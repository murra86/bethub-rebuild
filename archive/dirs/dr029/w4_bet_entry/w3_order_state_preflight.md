# W3 order-state brief — pre-flight grounding

**Captured:** 2026-05-07 16:18 ACST (Session 101 brief
drafting Step 2)
**Purpose:** Empirical grounding for
`w3_order_state_brief.md` per `bethub-brief-drafting`
skill Step 2. Anchors named in the brief reference the
state observed below.

---

## 1. W3 module inventory

`clients/betfair_client/v1/` line counts post-Session 100:

```
   14 _clock.py
   54 _auth.py
   72 scheduled_time.py
   78 identity.py
   91 sports_lines.py
   92 account_funds.py
   96 _errors.py
  104 _connection.py
  115 envelope.py
  118 settlement.py
  120 _audit.py
  135 market_catalogue.py
  143 cancellation.py
  150 replacement.py
  155 consumer.py
  175 __init__.py
  207 live_pricing.py
  283 placement.py
  396 _stream_parser.py
  595 streaming.py
  664 _translation.py
 3857 total
```

No `current_orders.py` present. Confirms the gap.

## 2. Closest shape precedent — `account_funds.py`

`account_funds.py` (92 lines) is the closest precedent
for the new module. Both characteristics align:

- Non-cached, non-streamed — every call is direct REST.
- `ReadEnvelope[T]` return shape (`fresh` on success,
  `unavailable` on failure; no `stale` path).
- Single endpoint, optional filter parameter.
- Library-side counterpart in betfairlightweight
  (`endpoints.account.get_account_funds` for funds;
  `endpoints.betting.list_current_orders` for orders).

Structure mirrored in the new module: docstring with
contract anchor + source-spec anchor; one or more
Pydantic models for the return shape; one `_parse`
helper; the public function injecting
`BetfairRestClient`; `_errors.map_rest_error_read`
for failure mapping.

## 3. Contract anchor — new §9.8

Operator's Session 100 reference to "§9.4" was
directional. Current §9.4 is **scheduled-time reads**.

Section ordering at insertion site:

- §9.5 Identifier-resolution checks
- §9.6 Account funds read (added v1.2 — closest
  precedent)
- §9.7 Market catalogue read (added v1.2)
- **NEW §9.8 — Order-state reads** (this brief)
- §10 Streaming surface

Brief is a backward-compatible v1.3 addition per §14.4
(no version bump on backward-compatible additions —
v1.3 because it adds a new public surface).

Closes Claude-67 G4 (`listCurrentOrders` filter
parameter list not in captured reference) — the new
§9.8 spec authoritatively replaces the captured-
reference gap.

## 4. Auth-expired finding — sharper than the §7.1
   triage suggested

`BetfairReadUnavailableReason.BETFAIR_AUTH_EXPIRED`
**already exists** in the enum (`envelope.py:42`):

```python
class BetfairReadUnavailableReason(str, Enum):
    GENUINE_ABSENCE = "genuine_absence"
    BETFAIR_AUTH_EXPIRED = "betfair_auth_expired"
    BETFAIR_RATE_LIMITED = "betfair_rate_limited"
    BETFAIR_MARKET_SUSPENDED = "betfair_market_suspended"
    BETFAIR_STREAMING_DISCONNECTED = ...
    BETFAIR_MARKET_NOT_FOUND = "betfair_market_not_found"
    BETFAIR_API_UNREACHABLE = "betfair_api_unreachable"
```

The §7.1 fold-in is **not** about adding a new enum
value — it's about **wiring auth-expired through to W4
so the orchestrator can route it distinctly from
other unavailable reasons**.

State of play across the W3-W4 boundary:

- **Write-side adapter:** already routes auth-expired
  distinctly. `betfair_adapter.py:295-308`
  `_unavailable_to_placement_outcome` falls through to
  the catch-all retry-safe branch returning
  `error_code=reason.value` (literal
  `"betfair_auth_expired"`). The orchestrator can
  switch on this string today.
- **Read-side adapter:** **collapses all UNAVAILABLE
  outcomes to a single signal.** `get_market_status`
  returns `MarketStatusSnapshot(status="INACTIVE", ...)`
  for everything except SUSPENDED.
  `get_account_funds` returns `None`. `get_order_state`
  returns `None` (stub). The auth-expired distinction
  is **lost at the boundary** on the read paths.

The §7.1 fold-in scope sharpens to: when the new
`get_order_state` real implementation lands, surface
auth-expired distinctly through to the orchestrator
so the operator-intervention signal reaches the
modal recovery layer.

## 5. W4 `OrderStateSnapshot` shape (orchestrator.py:114)

```python
class OrderStateSnapshot(BaseModel):
    """Reconciliation read for Trigger B."""

    model_config = ConfigDict(frozen=True)

    bet_id: str
    matched_size: Decimal
    unmatched_size: Decimal
    average_matched_price: float | None
    found_in_unmatched: bool
```

Trigger B reconciliation observes this snapshot.
`average_matched_price` is None when nothing matched;
`found_in_unmatched` is True when our `bet_id` is
still pending unmatched stake.

## 6. W4 Protocol method (orchestrator.py:189)

```python
def get_order_state(
    self,
    *,
    market_id: str,
    selection_id: str,
    bet_id: str,
    original_size: Decimal,
) -> OrderStateSnapshot | None: ...
```

`None` is the only failure shape today. Auth-expired
surfaced through this signature requires either
(a) a richer return type (snapshot OR retryable-
unavailable OR terminal-unavailable signal) or
(b) a side-channel (exception type, sentinel object,
adapter attribute the orchestrator polls).

Architectural call surfaces at brief drafting Step 5.

## 7. Adapter stub site (betfair_adapter.py:192-217)

Current shape — full method body:

```python
def get_order_state(
    self,
    *,
    market_id: str,
    selection_id: str,
    bet_id: str,
    original_size: Decimal,
) -> OrderStateSnapshot | None:
    """Brief §5.6 stub-with-finding path.

    W3 currently exposes no order-state read surface —
    neither `list_current_orders` nor any equivalent
    function in `clients/betfair_client/v1/`. Per brief
    §5.6 stub path: returns `None` unconditionally; the
    gap is named as the primary §8 finding in
    `real_adapter_report.md`. Real-adapter Trigger B
    reconciliation against the live API is partial
    pending the W3 surface work; mock-driven Trigger B
    tests via `MockBetfairAdapter` remain valid.
    """

    return None
```

Replacement target: full body replaces with real wrap
calling the new W3 surface, translating the
`ReadEnvelope[OrderState]` outcome into the
orchestrator-shape `OrderStateSnapshot | None` (or the
richer return shape per the §5 architectural call).

## 8. Orchestrator call site (orchestrator.py:932-967)

`_read_order_state_with_retry` (Trigger B
reconciliation) calls
`self._adapter.get_order_state(...)` twice (single
retry per brief §6.4); treats `None` as "read failed,
fall through." The auth-expired routing decision will
likely require this method to grow — it currently
treats `None` and exception identically.

## 9. Test precedents

- `test_account_funds.py` (204 lines) — closest
  shape precedent for non-cached read surface tests.
- `test_market_catalogue.py` (344 lines) — second
  precedent (also non-cached, single-call surface).
- `test_betfair_adapter.py` (~430 lines, 19 tests) —
  shipped Sessions 99-100; existing
  `get_order_state` stub test will need replacement
  / extension for the real path.
- `conftest.py` (45 lines) — existing fixtures;
  whether new fixtures are needed depends on the
  test scope brief drafting decides.

## 10. `__init__.py` re-exports (175 lines)

Public W3 surface flat — module-internal helpers not
re-exported. New function + new return type need to
be added to imports (line ~25), `__all__` (line ~95
read surfaces), and the read-surface comment block.

## 11. Cross-cutting findings

- `_translation.py` (664 lines) holds the v1
  path-style → Betfair JSON-RPC translation. New
  endpoint maps to Betfair's
  `SportsAPING/v1.0/listCurrentOrders` per the
  betfairlightweight library
  (`endpoints.betting.list_current_orders`). Whether
  the new endpoint requires a `_translation.py` edit
  depends on whether path-style routing already
  covers `/v1/orders/current` shape; brief §5 spec
  call.
- `_errors.py` (96 lines) `map_rest_error_read`
  already covers the read-side reasons; no edit
  expected for the new endpoint.
- `consumer.py` (155 lines) — pattern for the higher-
  level reading paths (`get_live_market_prices`,
  `get_market_settlement`, etc.). Whether the new
  W3 surface gets a consumer-side wrapper or stays
  module-direct is a brief §5 spec call (precedent:
  `get_account_funds` is module-direct, no
  consumer wrapper — same shape likely fits orders).

## 12. No dirty-tree intersection

Pre-flight `git status` not run yet (will be added at
brief §10 hard-limits if dirty regions need naming).
Code's report Session 100 noted post-execution `git
status` was identical to session start — clean
working tree on the bethub-v3 side.
