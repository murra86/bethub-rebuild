# W3 order-state read surface + read-side boundary pass-through brief

**Drafted:** 2026-05-07 (Session 101)
**Locked:** [pending operator review]
**Brief author:** Claude Chat (Session 101)
**Code execution:** out-of-session, single bounded run
**Output report:** `dr029/w4_bet_entry/w3_order_state_report.md`

---

## §1 — What this brief is and is not

This brief commissions a single bounded Claude Code
session to:

- **Add a new W3 read surface** — `current_orders.py`
  in `clients/betfair_client/v1/` exposing
  `list_current_orders` per a new contract §9.8 spec.
- **Update `betfair_client_contract.md`** — add §9.8
  authoritative spec; bump contract version to v1.3
  per §14.4 (backward-compatible addition).
- **Replace the `get_order_state` adapter stub** —
  swap the `None`-returning stub at
  `betfair_adapter.py:192-217` with a real wrap of
  the new W3 surface.
- **Extend the W4 `BetfairAdapter` Protocol** — grow
  the three read methods (`get_market_status`,
  `get_account_funds`, `get_order_state`) so they
  carry the unavailable-reason value through to the
  orchestrator (read-side pass-through routing per
  §7.1 fold-in).
- **Wire the orchestrator** to switch on the
  unavailable reason where it currently treats
  `None`/`INACTIVE` as the only failure shape.

This is **a single Code session**. If the work
doesn't fit, that's a finding to surface in the
report, not a continuation. Surprises become
findings, not blockers; remediation routes through
operator-Claude triage at Session 102, not through
ad-hoc Code-side decisions.

This brief is **not**:

- A composition-root structural decision (sequenced
  Session 102+).
- A W6 brief, a W7 brief, or any other workflow
  brief.
- A retrofit of v2 — v3 codebase only.
- A schema-changing brief — no DB migrations, no
  SQLAlchemy column additions.
- A test-coverage rework or a tooling-hygiene
  pass.
- A modal-layer copy spec (the modal-layer reads the
  pass-through reason values; this brief lands the
  pass-through, not the copy).
- An auth-refresh implementation. The W3 `_auth.py`
  refresh path exists per contract §9.6 failure
  modes; auth-expired routing surfaces the signal
  for the modal/operator layer to act on, not for
  automated refresh.

## §2 — Why this work exists

Session 100 triaged Code's report on the real
`BetfairAdapter` implementation (`real_adapter_report.md`,
~676 lines). Two open items routed to this brief:

**§8.1 — W3 order-state read surface gap.** The W4
`BetfairAdapter` Protocol method `get_order_state`
(orchestrator.py:189) supports Trigger B
reconciliation — the post-placement check that reads
back what actually matched at Betfair vs what we
intended. Code's report flagged that W3 currently
exposes no read surface for this; the real adapter
ships `get_order_state` as a stub returning `None`
unconditionally, which means real-adapter Trigger B
reconciliation cannot exercise against the live API.
Mock-driven Trigger B coverage in
`test_orchestrator.py` remains valid; what's missing
is the live path.

**§7.1 — `BETFAIR_AUTH_EXPIRED` distinct routing.**
The read-side adapter currently collapses every
`UnavailableReadEnvelope` outcome to a single signal
(`MarketStatusSnapshot.status="INACTIVE"` or `None`),
which means the operator-intervention case (Betfair
session token lapsed, operator must log back in)
looks identical to a transient rate-limit or a
genuinely-absent market. Operator's call Session
100: surface auth-expired distinctly so the modal
recovery layer can act on the operator-intervention
case. Brief drafting Session 101 sharpened the scope
to **read-side pass-through routing across all
three reads** — every read path surfaces the full
unavailable-reason value through to the orchestrator,
not just auth-expired, so the modal layer has full
discrimination available without a follow-up brief.

This matters because Trigger B reconciliation is the
mechanism that turns "we placed a bet and got a
response" into "we know what actually matched." When
auth lapses or the API goes unreachable mid-cycle,
the orchestrator currently treats the read failure
identically to "the bet just isn't there yet" —
which is wrong both ways (an auth-expired triggers
no recovery; a genuine race-condition with the
order cache triggers operator panic that isn't
warranted).

Cross-references: `dr029/w4_bet_entry/real_adapter_brief.md`
§5.6 (stub spec); `dr029/w4_bet_entry/real_adapter_report.md`
§8 (gap finding) + §7 (operator questions);
`sessions/SESSION_100.md` (triage and routing);
`dr029/w4_bet_entry/w3_order_state_preflight.md`
(this brief's pre-flight grounding).

## §3 — Pre-reads

Required:

1. `dr029/w4_bet_entry/w3_order_state_preflight.md`
   (pre-flight grounding, this session) — the
   empirical findings that anchor every spec
   decision in this brief.
2. `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
   §8 (typed envelope), §9.6 (account funds —
   closest shape precedent), §14.4 (backward-
   compatible additions), §15 (out of scope).
3. `dr029/w4_bet_entry/real_adapter_brief.md` §5.2
   (boundary translation), §5.6 (current stub
   spec), §12 (hard limits — what's the discipline
   precedent).

Reference-only — read on demand:

- `clients/betfair_client/v1/account_funds.py`
  (W3 module shape precedent).
- `clients/betfair_client/v1/envelope.py`
  (typed envelope, unavailable-reason enums).
- `workflows/bet_entry/v1/orchestrator.py` —
  `OrderStateSnapshot` (line 114),
  `BetfairAdapter` Protocol (line 166-218),
  `_read_order_state_with_retry` (line 932-967),
  Trigger B call sites.
- `workflows/bet_entry/v1/betfair_adapter.py`
  (current stub at line 192-217; read methods at
  line 105-217).
- `tests/clients/betfair_client/v1/test_account_funds.py`
  (test shape precedent).
- `tests/clients/betfair_client/v1/conftest.py`
  (existing fixtures).
- `tests/workflows/bet_entry/v1/test_betfair_adapter.py`
  (existing adapter tests, including current stub
  test at the `get_order_state` site).
- `decisions.md` DR-019 (derived state on read),
  DR-021 (timestamp anchoring, Adelaide local
  time), DR-027 / DR-028 (cross-DB boundary
  discipline), DR-030 (v3 repo layout), DR-031
  (v3 tech stack).

## §4 — System access

- **Mac filesystem read-write** at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Edit
  named anchors only per §10 hard limits.
- **Mac filesystem read-write** at
  `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  (single-file edit for §9.8 addition + §6 version
  history bump).
- **No VPS access.** This brief touches v3 codebase
  only; no `capture.db`, no VPS scrapers, no SSH
  paths.
- **No live Betfair API calls.** Test mocking only;
  no live REST or Streaming traffic. The new W3
  surface's correctness is verified via mocked
  `BetfairRestClient` per `test_account_funds.py`
  precedent.
- **Adelaide local timestamps per DR-021** — every
  timestamp in the report (open anchor, close
  anchor, any test fixtures generating
  `cache_as_of` values) uses
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
  via Desktop Commander or
  `datetime.now(tz=ZoneInfo("Australia/Adelaide"))`.

## §5 — Substantive scope sections

### §5.1 — New W3 module: `current_orders.py`

Create `clients/betfair_client/v1/current_orders.py`
mirroring `account_funds.py` shape (~90-110 lines
expected). Module structure:

```python
"""§9.8 Order-state reads.

Contract anchor: §9.8 (added v1.3 per §14.4 backward-
compatible additions). Source-spec anchor: W4
follow-up §6.4 — Trigger B reconciliation read.

Endpoint: ``/v1/orders/current`` (with optional
``?market_id=X&bet_id=Y`` query string filters).

Maps to Betfair's ``BettingAPING/v1.0/listCurrentOrders``
per §15.4 v1.3 carve-out. ``betfairlightweight.endpoints.betting.list_current_orders``
is the library-side counterpart; the W3 v1.0 surface
pattern continues to inject a path-style
``BetfairRestClient`` here, with translation between
v1 path-style endpoints and the Betfair JSON-RPC shape
held in ``_translation.py``.

Order-state reads are non-cached, non-streamed —
every call is direct REST. Returned envelope is
always ``fresh`` on success or ``unavailable`` on
failure; ``stale`` is not applicable per contract
§9.8.
"""
```

**Public function signature:**

```python
def list_current_orders(
    rest_client: BetfairRestClient,
    *,
    market_id: str | None = None,
    bet_id: str | None = None,
) -> ReadEnvelope[OrderStateList]: ...
```

**Filter semantics:**

- `market_id=None, bet_id=None` — returns all
  current orders for the operator's account.
- `market_id="1.234", bet_id=None` — returns all
  current orders within the named market. This is
  the Trigger B reconciliation call shape.
- `market_id=None, bet_id="abc"` — returns the
  named order if present in the operator's current
  orders. Useful for direct bet-id lookup.
- `market_id="1.234", bet_id="abc"` — both filters
  applied. Library-side scope of `listCurrentOrders`
  supports per-market filtering plus per-bet-id
  filtering; combining them is valid.

**Return shape:**

```python
class OrderRecord(BaseModel):
    """Single current-orders entry. Per Betfair
    `CurrentOrderSummary` shape."""

    bet_id: str
    market_id: str
    selection_id: str
    side: Literal["BACK", "LAY"]
    price_requested: float          # the price the bet was placed at
    price_matched_average: float | None  # None if nothing matched yet
    size_requested: Decimal
    size_matched: Decimal
    size_remaining: Decimal
    size_lapsed: Decimal             # for LAPSE persistence — what fell off
    size_cancelled: Decimal          # what got cancelled
    size_voided: Decimal             # what got voided post-settlement
    placed_date: datetime            # Betfair-side placement timestamp
    matched_date: datetime | None    # Betfair-side first-match timestamp
    persistence_type: Literal["LAPSE", "PERSIST", "MARKET_ON_CLOSE"]
    order_type: Literal["LIMIT", "LIMIT_ON_CLOSE", "MARKET_ON_CLOSE"]
    customer_order_ref: str | None
    customer_strategy_ref: str | None


class OrderStateList(BaseModel):
    """Per contract §9.8 return shape — the list
    wrapper carries the read's `cache_as_of`."""

    orders: list[OrderRecord]
    cache_as_of: datetime
```

**Internal `_parse` helper:** mirror
`account_funds._parse` shape — accept the raw
payload dict and the `cache_as_of` timestamp,
return `OrderStateList`. Defensive parsing per
account-funds precedent (`payload.get(...)` for
optional fields, type coercion at the boundary).

**Empty results valid.** `orders=[]` is a valid
fresh result and means "no current orders match the
filter" — not a failure. The orchestrator's Trigger
B logic interprets empty as "the bet has resolved
out of the order cache."

**Failure modes.** `BetfairReadUnavailableReason`
set applies. Common cases per contract §9.8:

- `betfair_auth_expired` — session token lapsed.
- `betfair_api_unreachable` — connectivity failure.
- `betfair_rate_limited` — endpoint shares
  Betfair's account-API rate budget.
- `betfair_market_not_found` — `market_id` filter
  passed but Betfair doesn't recognise the market.
- `genuine_absence` — the named bet doesn't exist
  in the operator's current-orders list (distinct
  from "API said no" — surfaces as a fresh
  envelope with `orders=[]`, not an unavailable
  envelope).

Module-internal: `_clock`, `_connection`,
`_errors.map_rest_error_read`, `envelope.to_adelaide`,
`envelope.now_adelaide` — all per
`account_funds.py` precedent.

### §5.2 — `__init__.py` re-export updates

Edit `clients/betfair_client/v1/__init__.py` to
re-export the new module's public names. Three
edit sites:

- Add to imports near line 25 (alphabetically
  ordered alongside `account_funds`,
  `cancellation`):

  ```python
  from .current_orders import (
      OrderRecord,
      OrderStateList,
      list_current_orders,
  )
  ```

- Add to `__all__` `read surfaces (§9)` block
  (around line 95):

  ```python
  # ... existing entries
  "OrderRecord",
  "OrderStateList",
  # ... and:
  "list_current_orders",
  ```

  Maintain alphabetical order within the section.

### §5.3 — Contract §9.8 spec

Add a new §9.8 to
`dr029/2_7_api_contract_versioning/betfair_client_contract.md`,
inserted between current §9.7 (Market catalogue
read) and current §10 (Streaming surface).

**Spec follows §9.6 / §9.7 precedent shape:**

- Header: `### §9.8 Order-state reads`
- Version note: `**Added v1.3 (2026-05-07).**
  Backward-compatible addition per §14.4. Closes
  W4 report §8.1 + Session 100 §7.1 fold-in.`
- Anchor: `Anchor: W4 follow-up §6.4 — Trigger B
  reconciliation read.`
- Endpoint path, call signature, parameter spec
  table, return shape (Pydantic models), filter
  semantics narrative, failure modes, example
  call and response (fresh + unavailable). Mirror
  the §9.6 example structure.

**Also bump §6 version history:**

- Add a v1.3 entry in §6 listing the §9.8
  addition.
- Adjust the §6 v1.2 entry's "current" or
  "latest" status if it carries one.

### §5.4 — `_translation.py` edit (if needed)

Inspect `_translation.py` to determine whether the
new endpoint `/v1/orders/current` already routes
via existing path-style → JSON-RPC translation, or
whether it needs an explicit translation entry.
Two possibilities:

- **Already covered** — the path-style routing is
  generic over endpoint paths. No `_translation.py`
  edit needed.
- **Not covered** — add a translation entry
  mapping `/v1/orders/current` to
  `BettingAPING/v1.0/listCurrentOrders`. Mirror
  the precedent for `/v1/account/funds` →
  `AccountAPING/v1.0/getAccountFunds`.

Code's call at execution time. If the answer is
"already covered," the report names that
explicitly so the brief-vs-implementation symmetry
is visible to triage.

### §5.5 — W4 Protocol extension: `ReadOutcome[T]`

Per the locked Session 101 architectural call
(read-side pass-through routing), the
`BetfairAdapter` Protocol's three read methods need
a return shape that carries the unavailable-reason
value through. Current shapes:

```python
def get_market_status(self, market_id: str) -> MarketStatusSnapshot: ...
def get_account_funds(self) -> FundsSnapshot | None: ...
def get_order_state(self, *, ...) -> OrderStateSnapshot | None: ...
```

New shape — introduce a generic discriminated union
in `orchestrator.py`:

```python
class ReadOk(BaseModel, Generic[T]):
    """Read returned a snapshot."""

    model_config = ConfigDict(frozen=True)
    outcome: Literal["ok"] = "ok"
    snapshot: T


class ReadUnavailable(BaseModel):
    """Read failed; reason carried through."""

    model_config = ConfigDict(frozen=True)
    outcome: Literal["unavailable"] = "unavailable"
    reason: Literal[
        "genuine_absence",
        "betfair_auth_expired",
        "betfair_rate_limited",
        "betfair_market_suspended",
        "betfair_streaming_disconnected",
        "betfair_market_not_found",
        "betfair_api_unreachable",
    ]


type ReadOutcome[T] = ReadOk[T] | ReadUnavailable
```

The Protocol methods become:

```python
def get_market_status(
    self, market_id: str
) -> ReadOutcome[MarketStatusSnapshot]: ...

def get_account_funds(
    self
) -> ReadOutcome[FundsSnapshot]: ...

def get_order_state(
    self, *, market_id: str, selection_id: str,
    bet_id: str, original_size: Decimal
) -> ReadOutcome[OrderStateSnapshot]: ...
```

**Reason value source.** The seven literal values
in `ReadUnavailable.reason` mirror the seven values
in `BetfairReadUnavailableReason` (envelope.py:38-46).
Stay in sync as values; deliberately decouple as
*types* per DR-030 layered architecture (W4
internals don't import from W3's enum directly —
the boundary translation lives in the adapter).

**Why a Pydantic discriminated union, not a
plain enum-or-snapshot tuple.** Three reasons:

- Pydantic-frozen pattern matches the existing
  W4 namespace (`OrderStateSnapshot`,
  `PlacementOutcome`, `MarketStatusSnapshot`).
- Discriminated union via `outcome` literal lets
  pattern matching (`match outcome:`) work
  cleanly at orchestrator call sites.
- Generic over T keeps the same shape across all
  three reads.

### §5.6 — Adapter changes: three read methods

Update three read methods in
`workflows/bet_entry/v1/betfair_adapter.py` to
return `ReadOutcome[T]` instead of
`MarketStatusSnapshot` / `FundsSnapshot | None` /
`OrderStateSnapshot | None`.

**Boundary translation pattern** (applies to all
three methods):

```python
def _envelope_to_read_outcome(
    envelope: ReadEnvelope[T_w3],
    snapshot_factory: Callable[[T_w3], T_w4],
) -> ReadOutcome[T_w4]:
    """Translate W3 ReadEnvelope to W4 ReadOutcome.

    Pass-through routing per §5.5: every
    UnavailableReadEnvelope.reason carries through
    to ReadUnavailable.reason verbatim (both are
    lower-snake `betfair_*` strings).
    """
    if envelope.status == EnvelopeStatus.UNAVAILABLE:
        return ReadUnavailable(reason=envelope.reason.value)
    snapshot = snapshot_factory(envelope.data)
    return ReadOk(snapshot=snapshot)
```

**Method-specific notes:**

- **`get_market_status`** — drop the SUSPENDED
  per-reason refinement at line 119-126. The
  pass-through now carries
  `betfair_market_suspended` through to the
  orchestrator directly; no need to convert it
  back to `MarketStatusSnapshot.status="SUSPENDED"`
  at the adapter boundary. The orchestrator-side
  logic (or the modal layer downstream) reads the
  reason and acts on it. **Behaviour-preserving
  rewire** — the SUSPENDED signal still reaches
  the operator, just via a different path. The
  W3-side `live_pricing` SUSPENDED-intercept
  (`live_pricing.py:126`) still does its job;
  what changes is the W4 boundary stops
  re-converting it back to a snapshot.
- **`get_account_funds`** — straightforward
  pass-through. Drop the `None` return.
- **`get_order_state`** — full body replacement of
  the stub at line 192-217. New body wraps
  `list_current_orders` per §5.1, parses the
  result (filter by `bet_id`, derive `matched_size`
  / `unmatched_size` / `average_matched_price` /
  `found_in_unmatched` per the
  `OrderStateSnapshot` shape).

**`OrderStateSnapshot` derivation** (the call
site Code wires inside the new
`get_order_state`):

```python
def get_order_state(
    self,
    *,
    market_id: str,
    selection_id: str,
    bet_id: str,
    original_size: Decimal,
) -> ReadOutcome[OrderStateSnapshot]:
    envelope = list_current_orders(
        self.client.rest_client,
        market_id=market_id,
        bet_id=bet_id,
    )
    if envelope.status == EnvelopeStatus.UNAVAILABLE:
        return ReadUnavailable(reason=envelope.reason.value)

    order_list: OrderStateList = envelope.data
    matching = [
        o for o in order_list.orders
        if o.bet_id == bet_id
    ]

    if not matching:
        # Bet has resolved out of the current-orders
        # cache — distinct from API-side failure.
        # Build a snapshot expressing "fully resolved,
        # not in unmatched."
        snapshot = OrderStateSnapshot(
            bet_id=bet_id,
            matched_size=original_size,  # assumption: fully matched on resolution
            unmatched_size=Decimal("0"),
            average_matched_price=None,  # unknown — bet has aged out
            found_in_unmatched=False,
        )
        return ReadOk(snapshot=snapshot)

    record = matching[0]
    # Sum size_matched + size_lapsed + size_cancelled +
    # size_voided to verify against original_size for
    # sanity (but the snapshot uses size_matched as the
    # canonical matched value).
    snapshot = OrderStateSnapshot(
        bet_id=record.bet_id,
        matched_size=record.size_matched,
        unmatched_size=record.size_remaining,
        average_matched_price=record.price_matched_average,
        found_in_unmatched=record.size_remaining > Decimal("0"),
    )
    return ReadOk(snapshot=snapshot)
```

**Sanity-check derivation note.** The above
treats "bet not in current orders" as "fully
resolved." That's the dominant case at Trigger B
read time (Trigger B fires 2-5s after placement;
fully matched bets fall out of current orders
within seconds of full match). The edge case
where the bet was cancelled, voided, or lapsed —
those would also fall out of current orders but
shouldn't be treated as "fully matched." Code's
report should flag this as a finding for Session
102 triage if the empirical behaviour differs;
real settlement-state reconciliation lives in the
post-settlement workflow (out of scope here).

### §5.7 — Orchestrator wiring update

Update orchestrator call sites that currently
treat `None`/`INACTIVE` as the only failure shape.
Three sites:

**Site 1: `_read_order_state_with_retry`**
(orchestrator.py:932-967). Current shape:

```python
try:
    snap = self._adapter.get_order_state(...)
    if snap is not None:
        return snap
except Exception as exc:
    LOG.warning(...)
# Single retry per §6.4
try:
    return self._adapter.get_order_state(...)
except Exception as exc:
    LOG.warning(...)
```

New shape:

```python
def _read_order_state_with_retry(
    self, ...
) -> ReadOutcome[OrderStateSnapshot]:
    """Brief §6.4 — single retry on Trigger B
    reconciliation read failure.

    Returns ReadOutcome[OrderStateSnapshot] —
    callers switch on outcome.
    """
    try:
        outcome = self._adapter.get_order_state(...)
        if isinstance(outcome, ReadOk):
            return outcome
        # ReadUnavailable — log and retry once
        LOG.warning(
            "Trigger B read unavailable (attempt 1): %s",
            outcome.reason,
        )
    except Exception as exc:
        LOG.warning("Trigger B read failed (attempt 1): %s", exc)
    # Single retry per §6.4
    try:
        return self._adapter.get_order_state(...)
    except Exception as exc:
        LOG.warning("Trigger B read failed (attempt 2): %s", exc)
        # Last-resort: synthesise a ReadUnavailable
        return ReadUnavailable(reason="betfair_api_unreachable")
```

The downstream Trigger B caller at orchestrator.py
~1287 (`snap: OrderStateSnapshot`) needs an unwrap
or pattern-match update to handle `ReadOutcome`.
Code's call on the cleanest unwrap shape — match
statement, isinstance ladder, or helper function.

**Site 2: `get_market_status` callers.** Search
`workflows/bet_entry/v1/orchestrator.py` for
`get_market_status` call sites. Each one currently
unpacks a `MarketStatusSnapshot`; new shape unwraps
`ReadOutcome[MarketStatusSnapshot]`. Code handles
each call site per the existing logic — usually
the question is "is this market actionable?" which
maps to "is this `ReadOk` AND `snapshot.status ==
'OPEN'`?" Pattern-match preferred where the
existing structure allows it.

**Site 3: `get_account_funds` callers.** Search
for call sites; current shape unwraps
`FundsSnapshot | None`; new shape unwraps
`ReadOutcome[FundsSnapshot]`. Same pattern.

For sites 2 and 3, **the orchestrator's behaviour
on `ReadUnavailable` is to fall through to the
existing failure path** — there's no new branching
logic at this brief's scope. The pass-through
preserves the reason value for downstream layers
(modal, logging, retry tracking) to read, but the
orchestrator's immediate response to "read failed"
is unchanged: log the reason, treat as the
existing "read failed" branch.

**Standing principle exercised here** (sweep
candidate j, locked Session 97): pay tooling-
hygiene costs now. The pass-through wires the
reason value through cleanly; downstream layers
can read it without a follow-up brief.

### §5.8 — `MockBetfairAdapter` updates

Update `MockBetfairAdapter` (in `test_orchestrator.py`
or wherever it lives) to return the new
`ReadOutcome[T]` shapes. Mock-driven tests need to:

- Build `ReadOk[T]` for success paths.
- Build `ReadUnavailable(reason="...")` for
  failure paths (preserving any existing
  test-driven failure-injection patterns).

Code's call on whether existing Trigger B test
fixtures need reshape vs whether wrapper helpers
on `MockBetfairAdapter` keep the test-shape stable.
Either is fine; the goal is `pytest` clean.

### §5.9 — New tests (W3 surface)

Add `tests/clients/betfair_client/v1/test_current_orders.py`
following `test_account_funds.py` precedent
(~200-300 lines expected). Coverage areas:

- **Fresh path: empty orders** — Betfair returns
  `[]`, returns `FreshEnvelope[OrderStateList]`
  with `orders=[]`.
- **Fresh path: single order** — single
  `CurrentOrderSummary` parses to
  `OrderRecord` correctly.
- **Fresh path: multiple orders** — list parsing.
- **Fresh path: filter combinations** — `market_id`
  only, `bet_id` only, both, neither.
- **Defensive parsing** — optional fields absent
  from payload (`size_lapsed`, `size_cancelled`,
  `size_voided`, `customer_strategy_ref`,
  `matched_date`).
- **Unavailable: each reason** — at least three of
  the seven failure modes (auth-expired,
  api-unreachable, rate-limited; coverage is
  exhaustive at the `_errors` level so spot-checks
  here suffice).
- **Filter validation** — invalid filter
  combinations rejected at the boundary if the
  spec calls for it.

Mirror `test_account_funds.py` for fixture shapes
and mocking patterns. Use existing `conftest.py`
fixtures where applicable.

### §5.10 — Adapter and orchestrator test updates

Update `test_betfair_adapter.py` (~430 lines, 19
tests):

- **Rename / restructure existing
  `get_order_state` stub test.** It currently
  asserts the stub returns `None`; new behaviour
  returns `ReadOk[OrderStateSnapshot]` or
  `ReadUnavailable`.
- **Add real-path tests for `get_order_state`** —
  fresh path with bet found in current orders
  (matched, partially matched, fully matched);
  fresh path with bet not found (resolved-out
  case); unavailable path with at least one
  reason value (auth-expired is the canonical
  case for this brief).
- **Update existing tests for `get_market_status`
  and `get_account_funds`** — they currently
  assert direct snapshot/None returns; new
  behaviour is `ReadOutcome[T]`. Test count may
  grow by 6-12 across the three methods (per
  Session 100 estimate).
- **`test_orchestrator.py` updates** — Trigger B
  test fixtures may need shape updates if they
  drove `MockBetfairAdapter.get_order_state` via
  `None` returns. Whether `Mock`-driven mocks
  need a `ReadOk` / `ReadUnavailable` builder
  depends on how the existing tests are
  structured — Code's call.

**Test count delta — overall expectation: +6 to
+12.** Real adapter brief shipped 19 new tests;
this brief adds ~6-12 additional (3-5 W3 surface
tests for `current_orders`, plus 3-7 adapter
tests covering the new `ReadOutcome` shape).
Final count is whatever Code lands; 6-12 is the
guide range, not a hard target.

### §5.11 — Static structural-Protocol conformance
   check

The existing
`_PROTOCOL_CONFORMANCE_CHECK: type[BetfairAdapter] = RealBetfairAdapter`
at `betfair_adapter.py:343-345` (TYPE_CHECKING
guarded) continues to apply unchanged. The
Protocol shape is updated per §5.5, the adapter
shape is updated per §5.6, and the conformance
check verifies they match. No new conformance
check needed at brief scope; the existing one
covers it.

### §5.12 — Import-linter contracts

The five existing import-linter contracts (per
Session 99 brief and Session 100 verification)
remain in force. New code lands within them:

- `clients/betfair_client/v1/current_orders.py`
  imports only from
  `clients/betfair_client/v1/` siblings (the `_*`
  privates and `envelope.py`). Mirrors
  `account_funds.py` precedent.
- `workflows/bet_entry/v1/betfair_adapter.py`
  imports adjusted for the new W3 module
  (add `OrderRecord`, `OrderStateList`,
  `list_current_orders` to the `clients.betfair_client.v1`
  import block; no other import surface widening).
- `workflows/bet_entry/v1/orchestrator.py` adds
  `ReadOk`, `ReadUnavailable`, `ReadOutcome` —
  these live in the orchestrator module itself;
  no new import surface.

If Code surfaces a contract violation during the
work, that's a finding to surface in the report,
not a blocker.

## §6 — Sequencing within session

Recommended execution order:

1. **Read pre-flight grounding doc + contract §9.6
   / §9.7 / §14.4** — orient on shape precedent.
2. **Read existing
   `account_funds.py`, `envelope.py`,
   `betfair_adapter.py` (current state)**.
3. **Build `current_orders.py`** end-to-end
   (§5.1) before touching the adapter or
   orchestrator. The W3 surface is a clean leaf;
   getting it right first means downstream wiring
   has a stable target.
4. **Build the W3 surface tests
   (`test_current_orders.py`)** — verify the
   surface in isolation before wiring across.
5. **Add the Pydantic models in `orchestrator.py`**
   for `ReadOk`, `ReadUnavailable`,
   `ReadOutcome` (§5.5). Update the Protocol
   method signatures.
6. **Update the adapter** — three read methods
   (§5.6). Drop the SUSPENDED special case in
   `get_market_status` (the pass-through carries
   the reason through directly).
7. **Update the orchestrator call sites** (§5.7)
   — the three call sites at
   `_read_order_state_with_retry`,
   `get_market_status` callers, and
   `get_account_funds` callers.
8. **Update `MockBetfairAdapter`** (§5.8).
9. **Update `test_betfair_adapter.py` and
   `test_orchestrator.py`** for the new shapes
   (§5.10).
10. **Update `__init__.py`** re-exports (§5.2).
11. **Inspect `_translation.py`** — confirm whether
    the new endpoint already routes or needs an
    edit (§5.4).
12. **Update contract spec** —
    `betfair_client_contract.md` §9.8 + §6 (§5.3).
13. **Final verification:** `pytest` clean,
    `ruff check` clean, import-linter clean. `git
    status` snapshot.

**Dependency reasoning:** the W3 surface (1) is the
sturdy base everything else wires off; building it
first (and testing it in isolation) means later
steps have a stable target. The Protocol changes
in `orchestrator.py` (5) need to land before the
adapter changes (6) so the adapter can match the
Protocol; tests (9) need both Protocol and adapter
in place. Contract spec (12) is paperwork that
documents the shipped surface; doing it last means
the spec describes what actually shipped, not what
was originally drafted.

If a different order would be cleaner during
execution, Code may deviate — naming the deviation
and reasoning in the report's self-assessment.

## §7 — Empirical verification

**Pre-baseline (capture at session start):**

- `pytest` count: report current passing count
  (expected: 342 per Session 100 close).
- `ruff check` clean: yes/no.
- Import-linter clean: yes/no (5 contracts).
- `git status` snapshot.

**Post-execution (capture at session end):**

- `pytest` count delta: expected +6 to +12 net
  new tests passing.
- `ruff check` clean: must be yes.
- Import-linter clean: must be yes (5 contracts
  preserved).
- `git status` snapshot — no unintended drift.

**Report includes both states.** The pre/post
diff is a section in the report's self-assessment.

**Functional verification** (run before reporting
clean):

- Pattern-match across all `get_market_status`,
  `get_account_funds`, `get_order_state` call
  sites — every one handles both `ReadOk` and
  `ReadUnavailable` paths.
- Confirm the SUSPENDED signal still reaches the
  orchestrator (it now arrives as
  `ReadUnavailable(reason="betfair_market_suspended")`
  instead of
  `MarketStatusSnapshot(status="SUSPENDED")`).
  Both paths are valid; the report names which
  ships.
- Confirm Trigger B reconciliation tests
  (mock-driven) cover both the resolved-out and
  the still-in-orders paths.

**Mocked REST integration only** — no live
Betfair calls. The report names the test approach
explicitly.

## §8 — Output spec

**Single output file:**
`dr029/w4_bet_entry/w3_order_state_report.md`

**Length anticipation:** 600-900 lines. Real
adapter report shipped at 676 lines; this brief is
slightly broader scope (W3 surface + boundary
pass-through + three adapter methods + contract
spec + tests) so the upper end is plausible. If it
exceeds 1000, that's a finding to flag in
self-assessment.

**Section structure:**

1. Summary — what shipped, what didn't.
2. Files changed — list with line-count deltas.
3. Test count delta — pre/post numbers.
4. New tests added — by file, with brief
   descriptions.
5. Implementation notes — anchor decisions Code
   made (e.g. the `_translation.py` answer; the
   resolved-out-of-orders treatment in
   `get_order_state` derivation; any divergence
   from brief's pseudocode).
6. Deviations from brief — explicit list with
   reasoning. None expected, but flag any.
7. Open questions for triage — anything Code
   surfaced as needing operator-Claude
   resolution.
8. Findings — anything beyond the brief's scope
   that Code observed and didn't action.
9. Self-assessment — pre/post baselines, ruff
   /import-linter status, git status snapshot,
   length flag if applicable.

**Output does not contain:**

- Recommendations on next briefs.
- Fixes to issues outside this brief's scope.
- Schema changes (none warranted).
- Mid-execution operator pings — surprises become
  findings, not blockers.

## §9 — Hard limits

**Out of scope — Code does not touch these:**

- v3 composition-root structural decision drafting
  (sequenced Session 102+).
- Any W6 or W7 brief-territory work.
- Modal-layer copy or UI changes (the modal-layer
  reads pass-through reason values; this brief
  delivers the pass-through, not the copy).
- Auth-refresh implementation. The W3 `_auth.py`
  refresh path exists; auth-expired routing
  surfaces the signal to the modal/operator layer;
  automated refresh is out of scope.
- Other adapter methods (`get_account_funds` and
  `get_market_status` are touched only to update
  return shape per §5.6; no other behaviour
  changes).
- Streaming surface changes (`StreamingClient`,
  message dispatch, etc.) — out of scope.
- Settlement, sports-line, scheduled-time, or
  market-catalogue read surfaces — out of scope.
- DR-027/028 boundary discipline interpretation —
  the W3 surface stays in `clients/betfair_client/v1/`,
  the adapter stays in `workflows/bet_entry/v1/`;
  no cross-DB work.
- Schema changes to operational DB (no SQLAlchemy
  Column additions, no Alembic migrations).
- Tooling-hygiene work outside the brief — no
  test-coverage rework, no monolithic-file split,
  no migration-framework introduction.
- Persona / account / account-at-book work — out
  of scope.
- VPS or `capture.db` work — none required, none
  permitted in this brief.
- No `git add`, `git commit`, `git push`,
  `git stash`, `git restore`, `git checkout`
  (file-targeted), or `git reset`. Code edits
  named anchors only; the operator commits.
- No mid-session escalation. If Code hits a
  surprise that would change scope, surface it as
  a finding in the report; do not ping operator-
  Claude mid-flight.

**Single bounded Code session.** If the work
doesn't fit, that's a finding, not a continuation.
Partial-but-coherent work plus a clear surfacing
beats complete-but-overbudget.

**Named anchors only.** Code edits the regions
this brief names: `current_orders.py` (new),
`__init__.py` (re-exports), `betfair_adapter.py`
(three read methods + boundary helper),
`orchestrator.py` (Protocol + new types +
call-site updates), `_translation.py` (only if
needed per §5.4), the test files named in §5.9 /
§5.10, and `betfair_client_contract.md` §9.8 +
§6. No drift into adjacent code.

**Read-write filesystem on Mac only.** No live
API calls, no VPS access.

**Adelaide local timestamps per DR-021.** Every
timestamp in the report is Adelaide local; every
timestamp in test fixtures is Adelaide local.

## §10 — Dirty-tree handling

Pre-flight grounding (Session 101) noted Code's
report Session 100 confirmed the working tree was
identical post-execution to session start — clean
state. Code captures `git status` at session start
and verifies no unintended file changes accumulated
at session end.

If `git status` at start surfaces unexpected dirty
regions, surface as a finding before commencing
edits.

## §11 — What happens after Code's session

Tim runs Code against this brief in a separate
out-of-session run. Code produces the report at
`dr029/w4_bet_entry/w3_order_state_report.md`.

Next operator-Claude session (Session 102) reads
the report end-to-end and triages. Triage shape
follows the Session 100 inventory-first cadence
(sweep candidate l):

- Walk the report's deviations, open questions,
  and findings in single-round inventory.
- Flag each item as no-call (Code's territory,
  ack only) or operator-call (warrants
  routing).
- Walk operator-call items one per round in
  priority order.

Possible Session 102+ outcomes:

- **All clean** — Trigger B reconciliation now
  exercisable against the live API; W4 stream
  remains dropped; route to next workflow brief
  (W6 or W7 per operator's call) or composition-
  root structural decision.
- **Findings to action** — Code surfaces
  something operator-Claude needs to resolve
  before forward routing. Specific items become
  inputs to Session 102 brief drafting.
- **Partial coverage with named-debt** — analogous
  to Session 99-100's stub-with-finding pattern;
  next brief picks up the named-debt.

**Code does not produce the next brief.** Each
brief follows from the prior report; speculative
chained briefs are scope drift.

## §12 — Cross-references

**Scope-doc anchors:**

- `dr029/dr029_scope.md` §2.7 (API contract
  versioning) — closes the v1.3 backward-
  compatible addition for §9.8.
- `dr029/dr029_scope.md` §2.9 (write-side bet-
  entry coherence) — Trigger B reconciliation
  via real adapter + real W3 surface is the
  mechanism this brief lands.

**Decision Records invoked:**

- DR-019 (derived state on read) — context for
  the adapter's no-cache discipline.
- DR-021 (timestamp anchoring, Adelaide local
  time) — applies to every timestamp in the
  report and in test fixtures.
- DR-027 / DR-028 (cross-DB boundary discipline)
  — the W3 surface stays in W3-locality; the
  adapter stays in W4-locality.
- DR-030 (v3 repo layout) — load-bearing for
  module placement: `current_orders.py` at
  `clients/betfair_client/v1/`, the new types
  in `orchestrator.py` at `workflows/bet_entry/v1/`.
- DR-031 (v3 tech stack) — Pydantic v2,
  `match`-statement preferred over isinstance
  ladder where it cleans up, pytest, ruff,
  import-linter.
- DR-032 (canonical reference layer for all bet
  records) — context: `OrderRecord` carries
  `bet_id`, `market_id`, `selection_id` — the
  canonical join keys at the Betfair side.

**Prior reports / briefs this brief builds on:**

- `dr029/w4_bet_entry/real_adapter_brief.md`
  (Session 99 lock — structural template).
- `dr029/w4_bet_entry/real_adapter_report.md`
  (Session 100 source of §8.1 + §7.1).
- `dr029/w4_bet_entry/w4_followup_brief.md`
  (Session 96 — closest contract-work brief
  precedent).
- `dr029/w4_bet_entry/w4_followup_report.md`
  (Session 97).
- `sessions/SESSION_99.md` (real adapter brief
  drafting).
- `sessions/SESSION_100.md` (real adapter report
  triage; routing decisions for this brief).

**Parking-lot items this brief excludes:**

- W6 broader-sync reconciliation (Session 100
  carry — separate brief later).
- W7 brief-drafting carry-forward
  (`persistence_type` settings + Greyhound
  constraint — Session 100 carry).
- Composition-root structural decision (Session
  102+).
- Modal-layer copy distinguishing read failure
  reasons.
- Auto-refresh on auth-expired (manual operator
  intervention is the v1 shape).

---

**Brief length:** [TBD at lock — line count
captured in session record at close.]
**SHA256 prefix:** [TBD at lock.]
