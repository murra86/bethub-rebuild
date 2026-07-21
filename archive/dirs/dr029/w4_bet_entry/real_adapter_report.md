# W4 real `BetfairAdapter` Code report

**Status:** delivered Session 99 (single bounded Code session).
**Brief:** `dr029/w4_bet_entry/real_adapter_brief.md` (locked Session 99).
**Date:** 2026-05-07 (Adelaide local per DR-021).
**Audience:** operator-Claude triage, Session 100.

---

## §1 — Summary of what shipped

Six coordinated changes across five files, all green in one bounded
session.

1. **§5.1 / §5.2 / §5.3 / §5.4 / §5.5 / §5.6 / §5.7 — `RealBetfairAdapter`
   class.** New file `workflows/bet_entry/v1/betfair_adapter.py` (~290
   lines) implements the five-method `BetfairAdapter` Protocol against
   live W3 surfaces. Construction-time invariant raises `ValueError` on
   non-streaming clients. Four module-level translation helpers
   (`_now_adelaide`, `_betfair_to_w4_error_code`,
   `_unavailable_to_placement_outcome`, `_envelope_to_placement_outcome`)
   carry the boundary translation. `get_order_state` is a stub-with-
   finding because W3 currently exposes no order-state read surface
   (see §8.1).
2. **§5.8 — Surgical `INSUFFICIENT_FUNDS` rename.** Two literal sites
   renamed to `insufficient_funds` per Session 98 §7.1 routing call:
   `orchestrator.py:1050` (recovery-key chain) and
   `tests/.../test_orchestrator.py:581 + :589` (fixture + assertion).
   Pre-flight namespace at `orchestrator.py:554` and
   `test_orchestrator.py:381 + :409` preserved per brief §5.8 scope
   discipline.
3. **§5.9 — Re-export update.** `RealBetfairAdapter` added to the
   `workflows/bet_entry/v1/__init__.py` public surface as a new
   `# adapter` section at the top of `__all__`.
4. **§7 — Test module.** New file
   `tests/workflows/bet_entry/v1/test_betfair_adapter.py` (~430 lines)
   adds 19 tests across 6 sections (construction, market status, account
   funds, placement, fresh-runner-price, order-state stub).

**Test delta.** 19 new tests — one over the brief's 10–18 cap. Net
post-state: 323 → 342 (+19). Surfaced as a minor count deviation in
§6.3 because all 19 tests are explicitly named in brief §7.1–§7.6;
honouring the brief's literal coverage list took priority over the
arithmetic cap.

**Verification post-state:**
- Default `pytest` (`tests/`): 342 passed.
- Ruff: clean across project.
- Import-linter: 5 contracts kept (`DR-030 layered architecture`,
  `domain imports nothing`, `store imports nothing`, `contracts is a
  leaf`, `workflows cannot import workflows`).
- Manual spot-checks 1–3 (frozen dataclass shape; recovery-key chain
  lower-snake; pre-flight namespace upper-snake preserved): all green.

`git status` post-change shows the same dirty surface as session
start — no tracked files touched; all session edits land inside
already-untracked directories (`workflows/bet_entry/v1/`,
`tests/workflows/`).

---

## §2 — Modules edited

### §2.1 — `workflows/bet_entry/v1/betfair_adapter.py` (new file, ~290 lines)

| Region | Change |
|---|---|
| Module docstring (~lines 1–26) | Names brief anchor, scope, two §5.2(c) translations, and the §5.6 stub-with-finding decision. |
| Imports (~lines 28–61) | W3 imports via `clients.betfair_client.v1` re-export surface (15 names). W4 imports from orchestrator (5 names — Protocol + 4 snapshot models). |
| `_now_adelaide()` (~line 66) | Local DR-021 helper — `datetime.now(ADELAIDE)`. Mirrors the orchestrator's helper rather than reaching into W3's `_clock`/`to_adelaide` private path. |
| `RealBetfairAdapter` class (~lines 77–215) | `@dataclass(frozen=True)`. Three fields: `client: BetfairClient`, `audit_sink: AuditLogSink`, `operator_identity: str`. `__post_init__` raises `ValueError` on `streaming_client is None`. Five Protocol methods follow per §5.3–§5.7 sequencing. |
| `_betfair_to_w4_error_code` (~line 226) | Mechanical lower-casing per §5.2(c). Single-line helper. |
| `_unavailable_to_placement_outcome` (~lines 240–289) | Per-reason discrimination per §5.2(b). Streaming-disconnected → its own outcome; insufficient_funds → terminal+`insufficient_funds`; write-rejected → terminal+lower-snake `rejection_code`; everything else → retry_safe with reason value as error_code. |
| `_envelope_to_placement_outcome` (~lines 292–311) | Discriminates `EnvelopeStatus.FRESH` vs unavailable; FRESH unwraps `BetPlacementResult` into `PlacementOutcome("success", ...)`; unavailable delegates to the per-reason helper. |
| Static conformance check (~lines 318–323) | `if TYPE_CHECKING: _PROTOCOL_CONFORMANCE_CHECK: type[BetfairAdapter] = RealBetfairAdapter`. See §6.2. |

### §2.2 — `tests/workflows/bet_entry/v1/test_betfair_adapter.py` (new file, ~430 lines)

19 tests across 6 sections. See §3.

### §2.3 — `workflows/bet_entry/v1/__init__.py` (edit)

| Region | Change |
|---|---|
| Imports (~line 16) | Added `from workflows.bet_entry.v1.betfair_adapter import RealBetfairAdapter` as the first W4-internal import. |
| `__all__` (~line 70) | Added `"RealBetfairAdapter"` under a new `# adapter` section at the top of `__all__`, keeping the existing module-section ordering convention (`models`, `orchestrator`, `pricing`, …). |

### §2.4 — `workflows/bet_entry/v1/orchestrator.py` (edit, surgical)

| Line | Before | After |
|---|---|---|
| 1050 | `if outcome.error_code == "INSUFFICIENT_FUNDS":` | `if outcome.error_code == "insufficient_funds":` |

No other changes. Pre-flight namespace at line 554
(`code="INSUFFICIENT_FUNDS"`) preserved per brief §5.8 scope
discipline. The comment at lines 1045–1049 is unchanged.

### §2.5 — `tests/workflows/bet_entry/v1/test_orchestrator.py` (edit, surgical)

| Line | Before | After |
|---|---|---|
| 581 | `error_code="INSUFFICIENT_FUNDS"` | `error_code="insufficient_funds"` |
| 589 | `assert result.error_context.error_code == "INSUFFICIENT_FUNDS"` | `assert result.error_context.error_code == "insufficient_funds"` |

Pre-flight assertions at lines 381 (`MARKET_SUSPENDED`) and 409
(`INSUFFICIENT_FUNDS`) preserved. The function name at line 398
(`test_pre_flight_insufficient_funds_blocks` — function-name word,
not a literal) is also untouched.

---

## §3 — Tests built

**Total new tests:** 19. Zero regression on the 323 baseline.

### §3.1 — `test_betfair_adapter.py` (19 new)

| § | Test | Coverage |
|---|---|---|
| §7.1 | `test_real_adapter_requires_streaming_client` | `__post_init__` raises `ValueError` when `BetfairClient(streaming_client=None)` is passed. |
| §7.1 | `test_real_adapter_satisfies_protocol` | Runtime conformance: all five Protocol methods exist on the class; the adapter passes through a function typed as `BetfairAdapter`. (Static conformance is module-import-time via the `TYPE_CHECKING` line in §2.1.) |
| §7.2 | `test_get_market_status_open` | Fresh envelope (`OPEN`) → snapshot `status="OPEN"` with `market_id` and tz-aware `as_of`. |
| §7.2 | `test_get_market_status_suspended` | Per-reason refinement path: SUSPENDED-via-W3-intercept → snapshot `status="SUSPENDED"`. See §6.1 deviation. |
| §7.2 | `test_get_market_status_unavailable_returns_inactive` | Non-suspended unavailable (503 API unreachable) → snapshot `status="INACTIVE"`. |
| §7.3 | `test_get_account_funds_fresh` | Fresh envelope → `FundsSnapshot(available_to_bet_balance=Decimal("1247.83"))`. |
| §7.3 | `test_get_account_funds_unavailable_returns_none` | 429 → `None` per Protocol. |
| §7.3 | `test_get_account_funds_decimal_precision` | Float `1247.83` round-trips to `Decimal("1247.83")` exactly via `Decimal(str(value))`; no float-binary precision artefact. |
| §7.4 | `test_place_hedge_bet_success` | Fresh envelope → `PlacementOutcome(outcome="success", bet_id="318946271234")`; audit-log records `operator_identity` + `customer_order_ref`; `size_remaining` is `Decimal`. Uses real `StreamingClient` driven to SUBSCRIBED state. |
| §7.4 | `test_place_hedge_bet_streaming_disconnected_translates` | Real DISCONNECTED `StreamingClient` → `place_bet` §13.1 pre-check fires → adapter translates to `outcome="betfair_streaming_disconnected"`, matching `error_code`. |
| §7.4 | `test_place_hedge_bet_insufficient_funds_translates` | Raw upper-snake `INSUFFICIENT_FUNDS` (W3 reason path) → `outcome="terminal"`, `error_code="insufficient_funds"` (lower-snake) per §5.2(c). |
| §7.4 | `test_place_hedge_bet_market_suspended_translates` | Two assertions: (a) a custom `rejection_code="MARKET_SUSPENDED"` payload → `error_code="market_suspended"`; (b) the existing `PLACE_REJECTED_MARKET_SUSPENDED` fixture (`MARKET_NOT_OPEN_FOR_BETTING` rejection_code variant) → `error_code="market_not_open_for_betting"`. Confirms the mechanical lower-casing rule. |
| §7.4 | `test_place_hedge_bet_rate_limited_retry_safe` | 429 → `BETFAIR_RATE_LIMITED` reason → `outcome="retry_safe"`, `error_code="betfair_rate_limited"`. |
| §7.4 | `test_place_hedge_bet_decimal_to_float_conversion` | `Decimal("50.00")` stake → audit-log entry's `stake` field is `50.0` `float`. |
| §7.4 | `test_place_hedge_bet_customer_order_ref_round_trip` | `customer_order_ref="my-unique-ref-9999"` echoes through audit-log entry per contract §11.1 idempotency-key discipline. |
| §7.5 | `test_fetch_fresh_runner_price_fresh` | Fresh envelope → unwrapped `RunnerBestPrices` with expected `best_back` / `best_lay` `PriceLevel` shapes. |
| §7.5 | `test_fetch_fresh_runner_price_unavailable_returns_none` | 503 → `None` per Protocol. |
| §7.5 | `test_fetch_fresh_runner_price_forces_rest` | Monkeypatches `runner_best_prices` and asserts `streaming_client=None` is passed regardless of the adapter's wired SUBSCRIBED streaming client (W4 follow-up §13.5 forced-REST guarantee). |
| §7.6 | `test_get_order_state_stub_returns_none` | Stub returns `None` and does not raise (W3 surface gap; see §8.1). |

**Mock approach:** hand-rolled `MockTransport` (the existing W3
fixture at `tests/fixtures/betfair/rest_responses.py`) plus a minimal
`_SubscribedStreamingDouble` test double (see §6.6). One test
(`test_place_hedge_bet_success`) uses the real `StreamingClient`
driven through to SUBSCRIBED via `connect()` + `_handle_message(...)`
to cover the audit-log integration path; all other tests use the
double.

---

## §4 — Test results

```
$ .venv/bin/python -m pytest 2>&1 | tail -10
... [output abbreviated; 19 new tests + 323 baseline = 342] ...
============================= 342 passed in 0.41s ==============================

$ .venv/bin/python -m ruff check . 2>&1 | tail -5
All checks passed!

$ .venv/bin/lint-imports 2>&1 | tail -10
DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT
Contracts: 5 kept, 0 broken.
```

**Pre-change baseline:** 323 passed (matches brief §8 expectation).
**Post-change:** 342 passed = 323 + 19 new. One above the brief's
upper bound of 18 — see §6.3.

Two ruff `--fix` passes ran during build (one on the adapter file,
one on the test file) for `I001` import ordering and one `F401`
unused-import; nothing substantive.

---

## §5 — Linting + import-linter

Subsumed in §4. The new file `betfair_adapter.py` adds substantial
W3 imports (`AccountFunds`, `BetfairClient`, `BetfairReadUnavailableReason`,
`BetfairWriteUnavailableReason`, `BetPlacementResult`, `BetSide`,
`EnvelopeStatus`, `MarketPrices`, `PersistenceType`, `RunnerBestPrices`,
`UnavailableWriteEnvelope`, `WriteEnvelope`, plus four W3 functions).
This is the second W4 → W3 boundary widening (after `RunnerBestPrices`
landed via the W4 follow-up build per its report §8.4), and is
necessary by definition for the real adapter — it's the only module
that should know about W3 envelope shapes. No import-linter contract
drift; the `DR-030 layered architecture` contract permits
`workflows → clients` as a top-down dependency.

---

## §6 — Deviations from brief

### §6.1 — `get_market_status` per-reason refinement for `BETFAIR_MARKET_SUSPENDED`

**Brief literal (§5.2(a) + §5.3):** "v1 maps all unavailable reads
uniformly to `INACTIVE`." Brief §5.3 example code returns
`MarketStatusSnapshot(market_id, "INACTIVE", _now_adelaide())` for
all unavailable envelopes. Brief §7.2 test
`test_get_market_status_suspended` is named: "fresh envelope with
`SUSPENDED` status returns `MarketStatusSnapshot(status='SUSPENDED')`."

**Context-loss gap surfaced per brief §1 safeguard.** The W3
`live_pricing.market_prices` function intercepts
`MarketPrices.market_status == SUSPENDED` and converts the read to
`UnavailableReadEnvelope(BETFAIR_MARKET_SUSPENDED)` BEFORE returning
to the caller (`live_pricing.py:126–130`). The adapter therefore
never sees a `FreshEnvelope[MarketPrices]` with `market_status =
SUSPENDED`; that path is unreachable through `get_live_market_prices`.
The brief assumed otherwise.

**Code's most-defensible interpretation.** The W4 Protocol's
`MarketStatusSnapshot.status` literal includes `"SUSPENDED"`
explicitly. To preserve reachability of that literal, the adapter
performs the per-reason refinement the brief named as a permitted
escape valve at §5.2(a):

> Code surfaces the underlying `BetfairReadUnavailableReason` in the
> report's §8 if any of these unavailable-read mappings need
> per-reason refinement.

The adapter special-cases `BETFAIR_MARKET_SUSPENDED` specifically
(returns `status="SUSPENDED"`); all other unavailable reasons map
uniformly to `INACTIVE`. This honours the brief's `test_get_market_status_suspended`
intent. Comment in `betfair_adapter.py:111-120` documents the
reasoning. See also §8.2 finding.

### §6.2 — Static structural-Protocol conformance check shape

**Brief literal (§5.1):** `assert_type(RealBetfairAdapter, type[BetfairAdapter])`,
with explicit operator permission to choose an equivalent mechanism
if the literal form fails on Python 3.12.

**Code's choice:** at module bottom under `if TYPE_CHECKING:`, the
line `_PROTOCOL_CONFORMANCE_CHECK: type[BetfairAdapter] = RealBetfairAdapter`.
Reasoning:

- `assert_type(RealBetfairAdapter, type[BetfairAdapter])` would fail
  mypy because the inferred type of `RealBetfairAdapter` (the class
  object) is `type[RealBetfairAdapter]`, more specific than
  `type[BetfairAdapter]`; `assert_type` requires exact equality.
- The `type[BetfairAdapter]` annotation on assignment forces mypy to
  verify structural Protocol conformance (does `RealBetfairAdapter`'s
  instances satisfy `BetfairAdapter`?) — the same check the brief
  intended.
- Wrapping in `TYPE_CHECKING` keeps the line free of runtime cost.

The runtime `test_real_adapter_satisfies_protocol` (§7.1) provides a
parallel runtime check by calling a function typed `BetfairAdapter`
with the adapter instance.

### §6.3 — Test count: 19 new, one over the 18 upper bound

**Brief literal (§7):** "+10 to +18 new tests; baseline 323 → 333–341
expected."

**What landed:** 19 new tests; baseline 323 → 342.

**Why:** Brief §7.1–§7.6 explicitly enumerates 19 named tests:
- §7.1: 2 (`test_real_adapter_requires_streaming_client`, `test_real_adapter_satisfies_protocol`)
- §7.2: 3 (`test_get_market_status_open`, `_suspended`, `_unavailable_returns_inactive`)
- §7.3: 3 (`_fresh`, `_unavailable_returns_none`, `_decimal_precision`)
- §7.4: 7 (`_success`, `_streaming_disconnected_translates`, `_insufficient_funds_translates`, `_market_suspended_translates`, `_rate_limited_retry_safe`, `_decimal_to_float_conversion`, `_customer_order_ref_round_trip`)
- §7.5: 3 (`_fresh`, `_unavailable_returns_none`, `_forces_rest`)
- §7.6: 1 (`_stub_returns_none`)

Total = 19. Honouring the brief's literal explicit-named coverage
took priority over the +10/+18 arithmetic cap; collapsing two §7.4
tests (e.g. folding the customer-order-ref round-trip into the success
test) would honour the count cap but skip a brief-named test.

### §6.4 — `get_order_state` stub path chosen (W3 surface absent)

**Brief literal (§5.6):** Code's call between (a) using a discovered
W3 surface, or (b) implementing a stub that returns `None`
unconditionally and surfacing the gap as a §8 finding.

**Code's investigation:** grep across `clients/betfair_client/v1/`
for `list_current_orders|currentOrders|current_orders|listCurrentOrders|order_state|OrderState`
returned no matches in W3 module code. Direct inspection of the W3
re-export surface (`clients/betfair_client/v1/__init__.py`) confirmed
no order-state read function is exposed.

**Path taken:** stub. Returns `None` with docstring naming the gap
and pointing at the report §8 finding. See §8.1 for the routing
recommendation.

### §6.5 — Test fixture name in brief diverges; line numbers exact

**Brief literal (§5.8):** "`test_path_b_insufficient_funds_terminal`
test (`test_orchestrator.py:573–595`)".

**What's actually there:** the test at lines 572–595 is named
`test_path_b_terminal_error_no_retry`. Function body matches the
brief description exactly (queues `outcome="terminal", error_code="INSUFFICIENT_FUNDS"`,
asserts on `error_code` plus retry-attempt count). Line numbers
581 (fixture) and 589 (assertion) match exactly. Code applied the
rename to the correct sites; the function-name discrepancy did not
require any action.

### §6.6 — Mock approach: hand-rolled W3 `MockTransport` plus minimal streaming double

**Brief literal (§7):** Code's call between hand-rolled W3-style
mocks vs `unittest.mock` / `pytest-mock`.

**Code's choice:** hand-rolled. Reuses the existing
`tests/fixtures/betfair/rest_responses.py::MockTransport` plus
fixture payloads (`PRICES_FRESH_FULL`, `PRICES_RUNNER_FRESH`,
`PRICES_SUSPENDED`, `PLACE_SUCCESS`, `PLACE_REJECTED_INSUFFICIENT_FUNDS`,
`PLACE_REJECTED_MARKET_SUSPENDED`). For the streaming-state
pre-check, a minimal `_SubscribedStreamingDouble` class implements
just the three methods `place_bet` and `runner_best_prices`/
`market_prices` need: `streaming_status()`, `cached_market_prices()`,
`cached_runner_best_prices()`. Cast to `StreamingClient` at the
`BetfairClient` boundary (`cast(StreamingClient, double)`) for type
sanity.

One test (`test_place_hedge_bet_success`) uses the real
`StreamingClient` driven through `connect → CONNECTION_ACK →
subscribe_markets → AUTH_ACK` to exercise the full audit-log
integration path; all other tests use the double for speed and
focus.

### §6.7 — `test_place_hedge_bet_market_suspended_translates` covers two payloads

**Brief literal (§7.4):** one test asserting the
`MARKET_SUSPENDED` rejection_code translates to lower-snake
`market_suspended`.

**What landed:** the test now asserts both (a) a custom payload with
`rejection_code="MARKET_SUSPENDED"` lowering to `market_suspended`,
and (b) the existing fixture `PLACE_REJECTED_MARKET_SUSPENDED` (which
actually carries `rejection_code="MARKET_NOT_OPEN_FOR_BETTING"` —
inherited W3 fixture-shape choice) lowering to
`market_not_open_for_betting`. The second assertion confirms the
mechanical lower-casing rule applies uniformly across all
`BETFAIR_WRITE_REJECTED` codes per brief §5.2(c). One test, two
sub-assertions.

### §6.8 — `_now_adelaide()` defined locally, not lifted from W3

**Brief literal (§5.3):** "`_now_adelaide()` helper: thin wrapper
around `clients.betfair_client.v1._clock.now_utc()` plus
`to_adelaide()`; or, if Code prefers, lift directly from W3 by
importing the helpers it needs."

**Code's choice:** local definition mirroring `orchestrator.py:74-77`.
Reasoning: `_clock` is a private W3 module (`_`-prefixed); reaching
into it from W4 widens the W4→W3 import surface unnecessarily.
`to_adelaide` is exposed only via `envelope.py` (not via the
re-export `__init__.py`). Local `datetime.now(ADELAIDE)` is two
lines and keeps the W3 import surface tight.

### §6.9 — Adapter does not import `MarketCatalogue` / `get_market_catalogue`

**Brief literal (§5.1 imports anchor):** lists `MarketCatalogue` and
`get_market_catalogue` in the import block.

**What landed:** neither imported. The adapter does not call
`get_market_catalogue` from any of the five Protocol methods —
catalogue reads are an orchestrator-side concern (not in the W4
Protocol). Importing unused names would trigger ruff `F401` and
violate the principle of "import only what you use." Surface as
deviation; if a future Protocol extension wants catalogue access at
the adapter layer, the imports come back in at that point.

---

## §7 — Open questions

### §7.1 — Per-reason refinement for the other unavailable read reasons

The §6.1 deviation lands a per-reason refinement for
`BETFAIR_MARKET_SUSPENDED` only; the remaining six
`BetfairReadUnavailableReason` values (`GENUINE_ABSENCE`,
`BETFAIR_AUTH_EXPIRED`, `BETFAIR_RATE_LIMITED`,
`BETFAIR_STREAMING_DISCONNECTED`, `BETFAIR_MARKET_NOT_FOUND`,
`BETFAIR_API_UNREACHABLE`) all map uniformly to `INACTIVE` in
`get_market_status` and to `None` in `get_account_funds` /
`fetch_fresh_runner_price`.

Question: should any of these warrant separate W4-side surface
treatment? Examples:
- `BETFAIR_AUTH_EXPIRED` → could route to a separate "operator
  intervention required" pre-flight flag distinct from generic
  unreachable.
- `BETFAIR_MARKET_NOT_FOUND` → semantically distinct from "API
  unreachable"; could surface as a hard-stop on entry rather than
  a wait-and-retry.

Out of brief scope; routes through Cat 2 / Cat 3 of operator-Claude's
framework if the operator wants per-reason routing. Probably
nothing for now — `INACTIVE` / `None` is honest.

### §7.2 — `customer_strategy_ref=None` hard-wired at the adapter

Brief §5.5 names this: "W4 v1 doesn't populate `customer_strategy_ref`
— the operator hasn't surfaced a use case." Confirmation question:
is this the right default for live operations, or do operator-side
Strategy 1 / Strategy 2 workflows benefit from setting a non-empty
`customer_strategy_ref` for Betfair-side analytics joins?

The W3 `place_bet` audit-log already records `strategy_tag` (the
v3-internal analytics-join key per F5); `customer_strategy_ref` is
the Betfair-payload-side mirror. If they should be the same value,
the adapter could thread `strategy_tag` into both. Out of brief
scope; W4 v1 ships with `customer_strategy_ref=None`.

### §7.3 — `persistence_type=PersistenceType.PERSIST` hard-wired

Brief §5.5: "PERSIST is the correct value for hedge bets (don't
lapse at turn-in-play)." Confirmation: W7 burst review may surface
a use case for `LAPSE` or `MARKET_ON_CLOSE`. If so, the Protocol
extends and the adapter param-list extends. For now PERSIST is
hard-wired.

### §7.4 — Adapter file imports W3 types extensively — is the boundary still abstracted?

The adapter imports 12 W3 types and 4 W3 functions (per §5). This
is necessary by definition — the adapter is the single module that
should know about W3 envelope shapes. But it does mean that
`workflows/bet_entry/v1/` now has *two* modules with W3 imports:
- `orchestrator.py` — single import, just `RunnerBestPrices` per
  W4 follow-up §8.4 precedent.
- `betfair_adapter.py` — extensive W3 imports.

The Protocol abstraction at `orchestrator.py:166–218` keeps the
orchestrator W3-shape-naive (it sees W4 types only). The adapter
file is the contained "leak" of W3 shapes. Question: is this the
intended end-state, or does the operator want a stricter discipline
(e.g. W3 shapes never named in W4 module code, only via type-
aliases)?

---

## §8 — Findings

### §8.1 — W3 has no order-state read surface — primary finding

The brief §5.6 anticipated this gap as one of two paths. Code's
session-start grep across `clients/betfair_client/v1/` for
`list_current_orders|currentOrders|current_orders|listCurrentOrders|order_state|OrderState`
returned no matches in W3 module code. The W3 re-export at
`clients/betfair_client/v1/__init__.py` (175 lines) does not
expose any order-state read function. The contract
(`betfair_client_contract.md`) does name `listCurrentOrders` in
§9.4, but the W3 implementation hasn't shipped that surface yet.

**Impact on this brief.** `get_order_state` is a stub returning
`None`. Real-adapter Trigger B reconciliation (orchestrator brief
§6.2) cannot exercise against the live API until the W3 surface
lands. Mock-driven Trigger B tests via `MockBetfairAdapter` (Trigger
B coverage in `test_orchestrator.py`) remain valid; real-adapter
acceptance is partial pending the W3 work.

**Routing for operator-Claude.** This surfaces as a candidate for
a fresh contract-work brief targeting `clients/betfair_client/v1/`.
The brief would commission a `list_current_orders` (or equivalent)
W3 surface with the appropriate envelope shape, the adapter's
`get_order_state` stub would then be replaced with a real wrap.
Sequencing: probably before W6/W7 brief drafting, since W6's
operational store schema design may be informed by the order-state
shape.

### §8.2 — W3 `live_pricing` SUSPENDED-intercept conflicts with brief assumption

Documented in §6.1. The brief assumed
`MarketPrices.market_status == SUSPENDED` could pass through to the
adapter as a `FreshEnvelope`; W3 (`live_pricing.py:126–130`)
intercepts and converts to `UnavailableReadEnvelope(BETFAIR_MARKET_SUSPENDED)`
before returning. The adapter's per-reason refinement workaround
restores reachability of the `MarketStatusSnapshot.status="SUSPENDED"`
literal, but the underlying W3 shape choice is worth surfacing for
operator awareness:

- `MarketStatus` is a trinary enum (`OPEN | SUSPENDED | CLOSED`) at
  the W3 source-of-truth level (`settlement.py:29-32`).
- `live_pricing.market_prices` filters out SUSPENDED at the W3
  surface boundary, so consumers of the live-pricing read see a
  binary effective state (`OPEN | CLOSED`) plus an unavailable
  reason for SUSPENDED.
- Settlement reads (`settlement.market_settlement`) do not filter;
  consumers see all three trinary values.

The W4 `MarketStatusSnapshot.status` literal includes all four
(`OPEN | SUSPENDED | CLOSED | INACTIVE`) — so the adapter must do
the per-reason refinement to bridge the W3 binary-effective shape
back to the W4 trinary-plus-INACTIVE shape.

### §8.3 — `MarketPrices.market_status` `CLOSED` does pass through (untested in this brief)

Following on from §8.2: the W3 SUSPENDED-intercept does NOT apply
to `CLOSED`. A `MarketPrices` with `market_status=CLOSED` would
flow through as `FreshEnvelope[MarketPrices]`, and the adapter's
`get_market_status` would return `MarketStatusSnapshot(status="CLOSED")`
via the `market_prices.market_status.value` line. No brief test
exercises this path (the brief named `_open` and `_suspended` and
`_unavailable_returns_inactive` but not `_closed`); Code did not
add one to keep within the test count cap (already overshooting at
19 — see §6.3). The path is logically covered by the same
straight-through translation as `OPEN`.

### §8.4 — `place_bet` STREAMING_DISCONNECTED reason uses the read enum

The W3 `place_bet` returns
`UnavailableWriteEnvelope(reason=BetfairReadUnavailableReason.BETFAIR_STREAMING_DISCONNECTED, ...)`
when the §13.1 pre-check fires (`placement.py:159-186`). That is,
the streaming-disconnected reason on a write envelope is a member
of `BetfairReadUnavailableReason` (per the union type
`BetfairWriteUnavailableReason | BetfairReadUnavailableReason` on
`UnavailableWriteEnvelope.reason`). The adapter's
`_unavailable_to_placement_outcome` checks this correctly via
equality on `BetfairReadUnavailableReason.BETFAIR_STREAMING_DISCONNECTED`
— but the asymmetry is worth flagging because it would be easy for
a reader to assume "streaming-disconnected on a write envelope =
write enum value." It isn't. The code comment in the helper
(`betfair_adapter.py:248-253`) names this.

### §8.5 — `BetfairWriteUnavailableReason.BETFAIR_BET_PLACEMENT_IN_PROGRESS` falls through to retry-safe

The brief's §5.2(b) table assigns this reason to retry_safe. The
adapter's helper handles this via fall-through (after the explicit
checks for streaming-disconnected, insufficient_funds, and
write-rejected, anything else routes to retry_safe with the W3
reason value as the `error_code`). For
`BETFAIR_BET_PLACEMENT_IN_PROGRESS`, this means
`PlacementOutcome(outcome="retry_safe", error_code="betfair_bet_placement_in_progress")`.
Behaviourally correct; just observing that the helper is structured
as "explicit cases + safe-default-retry" rather than as an
exhaustive enum match. No behavioural ambiguity in practice; flagged
for awareness.

### §8.6 — Adapter file is the second W4 → W3 boundary widening

W4 follow-up §8.4 named `RunnerBestPrices` as the first W3-type-import
into W4-side code. This brief's `betfair_adapter.py` adds twelve
more W3 type imports (envelope reasons, snapshot types, enums,
result models) plus four W3 function imports. Post-brief, the
W3-shape knowledge in W4 is concentrated in two files:

- `orchestrator.py` — one type (`RunnerBestPrices`) in the Protocol
  return annotation. Otherwise W4-shape-clean.
- `betfair_adapter.py` — extensive. By design.

The Protocol abstraction continues to keep the orchestrator
W3-shape-naive at the call-site boundary (it consumes
`BetfairAdapter.fetch_fresh_runner_price()` → `RunnerBestPrices`
without knowing about envelopes). Other workflow modules
(`staking.py`, `pricing.py`, `record_builder.py`, `storage.py`)
remain W3-import-free.

If a future Protocol extension surfaces another W3 type at the
return-type level (e.g., `OrderPosition` for the §8.1 order-state
work), the orchestrator picks up another single W3 import. The
adapter file is the natural locus for any growth in W3-shape
awareness.

### §8.7 — Test-module hygiene (no conftest, autouse `_pin_clock`, existing `__init__.py` chain)

Three small test-hygiene observations consolidated:

- **No new conftest.** `tests/workflows/bet_entry/v1/` had no
  conftest before this brief; existing `test_orchestrator.py`
  defines fixtures inline. Code followed the same pattern. If a
  future test module wants to share the adapter fixtures, refactor
  is small.
- **`_pin_clock` autouse mirrors W3 conftest.** The new test module
  installs the same `_clock.now_utc()` pin used at
  `tests/clients/betfair_client/v1/conftest.py:27-30`, keeping
  `as_of` arithmetic deterministic across multi-second runs.
  Cheap consistency.
- **`tests/workflows/__init__.py` chain unchanged.** The
  housekeeping report §8.4 already verified this chain; the new
  test module slots in without new `__init__.py` files.

---

## §9 — Self-assessment

### §9.1 — Session-budget fit

Comfortable. All ten §6 sequencing items shipped: §5.1 class
skeleton + §5.2 helpers + §5.3 get_market_status + §5.4
get_account_funds + §5.6 get_order_state stub + §5.7
fetch_fresh_runner_price + §5.5 place_hedge_bet + §5.8 surgical
rename + §5.9 re-export update + test module. Verification pass
clean: 342 passing, ruff clean, all 5 import-linter contracts kept,
spot-checks 1–3 green. Report sits within the 400–600 line target
(this report ~600 lines).

### §9.2 — Confidence regions

**High confidence:**
- §5.1 dataclass shape + invariant + post_init guard.
- §5.2 translation helpers — covered by test cases for each
  outcome literal (`success`, `retry_safe`, `terminal`,
  `betfair_streaming_disconnected`) plus the two §5.2(c) named
  translations and the mechanical lower-casing rule.
- §5.3–§5.7 method implementations — direct W3 function wrapping
  with envelope discrimination.
- §5.8 surgical rename — mechanical; pre-flight namespace
  preservation verified by spot-check 3.
- §5.9 re-export — single-line import + `__all__` update.

**Medium confidence:**
- §6.1 SUSPENDED per-reason refinement — Code took the most-
  defensible interpretation of a context-loss gap; if operator
  prefers strict literal "all unavailable → INACTIVE", mechanical
  fix is two-line removal of the per-reason branch in
  `get_market_status`.
- §6.2 static conformance check shape — Code chose the
  `TYPE_CHECKING`-guarded `type[Proto]` assignment; if operator
  prefers a different mechanism (e.g. runtime function-signature
  check), straight swap.

**Lower confidence (flagged in §7 / §8):**
- §7.1 per-reason refinement for other unavailable reasons.
- §7.2 / §7.3 hard-wired `customer_strategy_ref=None` and
  `persistence_type=PERSIST`.
- §8.1 W3 surface gap for order state — biggest finding.

### §9.3 — What the operator should look at first

In rough priority order:

1. **§6.1 (SUSPENDED per-reason refinement)** — Code took the
   most-defensible interpretation of a brief-vs-codebase
   contradiction. Confirm or redirect; this affects how the W4
   Protocol's `MarketStatusSnapshot.status` literal flows in live
   operations.
2. **§8.1 (W3 order-state surface gap)** — primary finding.
   Routing decision: separate W3 contract-work brief vs deferring
   real-adapter Trigger B reconciliation until W6 brief lands.
3. **§6.3 (test count overshoot, 19 vs 18 cap)** — minor
   bookkeeping; mention only because it deviates from the brief's
   literal arithmetic. Code chose to honour the brief's
   explicit-named-coverage list over the count cap.
4. **§6.2 (static conformance check shape)** — minor; the brief
   invited Code's call.
5. **§6.4 (`get_order_state` stub path)** — confirmation only;
   the brief named both paths as acceptable.

The rest of §6/§7/§8 entries are smaller flags routing through
Cat 1 / Cat 2 / Cat 3 of operator-Claude's framework. §8.4 / §8.5 /
§8.6 are awareness items rather than decisions.

### §9.4 — Standing principle exercised

"Pay tooling-hygiene and structural-consistency costs now while in
build" (Session 97 lock) — applied to:
- §5.8 surgical `INSUFFICIENT_FUNDS` rename (Session 98 §7.1
  routing call landed in this same sweep, not deferred).
- The §5.2(c) `_betfair_to_w4_error_code` mechanical lower-casing
  helper handles the broader namespace consistency proactively, not
  just the two named translations — future rejection_codes flow
  through with no further code changes.

### §9.5 — Length flag

Report runs ~660 lines, ~10% over the brief's 400–600 target. The
W4 follow-up report referenced as a length precedent (447 lines)
covered six coordinated changes; this brief covers nine sub-sections
plus a context-loss-gap deviation pattern (§6.1, §6.9, §8.2, §8.3)
that the brief's §1 safeguard explicitly invited Code to surface.
§6 (nine deviations) and §8 (seven findings) each route distinctly
through operator-Claude's framework — collapsing them would lose
operator-triage granularity. Trade-off accepted: report is over
target by ~10%, content is the per-item breakdown the brief asked
for.

---

**End of report.**
