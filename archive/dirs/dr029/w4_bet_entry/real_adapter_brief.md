# W4 real `BetfairAdapter` implementation brief

**Status:** drafting Session 99.
**Audience:** Claude Code, single bounded session.
**Scope:** new `betfair_adapter.py` module at
`workflows/bet_entry/v1/` implementing the `BetfairAdapter`
Protocol against the live `clients.betfair_client.v1` surfaces;
boundary translation layer; new test module; surgical
`INSUFFICIENT_FUNDS` canonicalisation per Session 98 §7.1
routing call.
**Estimated size:** 800–1200 lines (brief). Adapter implementation
expected ~300–500 LOC; tests ~400–600 LOC.
**Estimated test delta:** +10 to +18 tests; pytest baseline 323
expected to land at 333–341.

---

## §1 — What this brief is and is not

This brief commissions Code to build the **real `BetfairAdapter`
implementation** for v3 — the production class that satisfies the
W4 `BetfairAdapter` Protocol by wrapping the existing
`clients.betfair_client.v1` surfaces and translating between
Betfair's raw API shape and W4's internal namespace.

**This brief is:**

- A single new module `betfair_adapter.py` at
  `workflows/bet_entry/v1/` implementing the five-method
  `BetfairAdapter` Protocol locked at `orchestrator.py:166`.
  Methods covered: `get_market_status`, `get_account_funds`,
  `place_hedge_bet`, `get_order_state`, and
  `fetch_fresh_runner_price` (the W4-follow-up REST-fallback
  method).
- A boundary translation layer between Betfair's raw API
  shape (upper-snake error codes, `WriteEnvelope` /
  `ReadEnvelope` envelopes from `clients.betfair_client.v1`,
  Betfair-specific failure-mode enums) and W4's internal
  namespace (lower-snake `error_code` strings on
  `PlacementOutcome`, the W4 snapshot models
  `MarketStatusSnapshot` / `FundsSnapshot` /
  `OrderStateSnapshot`, the W4 `PlacementOutcome` outcome
  literal). Two specific upper-to-lower translations land
  here: `MARKET_SUSPENDED` → `market_suspended` (housekeeping
  report §8.2 finding) and `INSUFFICIENT_FUNDS` →
  `insufficient_funds` (Session 98 §7.1 routing call).
- A new test module
  `tests/workflows/bet_entry/v1/test_betfair_adapter.py`
  exercising the adapter against a mocked
  `BetfairRestClient` — covers each Protocol method, each
  boundary translation, and the envelope failure-mode
  handling. Real-API acceptance testing is operator-side
  post-merge, not in this brief's scope.

**This brief is not:**

- A change to `clients.betfair_client.v1`. The W3 surface
  is read-only; the adapter composes existing surfaces
  without modifying them. The contract §11.1 `place_bet`,
  §9.1 `runner_best_prices`, §9.6 `get_account_funds`,
  §9.7 `get_market_catalogue` and the §10 streaming
  surfaces are wrapped, not changed.
- A change to the W4 `BetfairAdapter` Protocol. The
  Protocol is the contract this adapter satisfies; the
  Protocol stays as locked in W4 follow-up §5.1.
- A streaming-side integration. The Protocol surface is
  REST-only — the streaming-disconnect-blocks-writes rule
  (contract §13) is enforced inside `betfair_client.place_bet`,
  not at the W4 boundary. Live-pricing cache freshness
  behind streaming subscription is downstream concern
  (DR-029 §2.4 build).
- A change to `MockBetfairAdapter` at the W4 test
  fixture. The mock and the real adapter coexist; the
  mock continues to drive `test_orchestrator.py`'s
  scenario coverage; the real adapter has its own
  dedicated test module.
- A schema change. No edits to `models.py`, no edits to
  `record_builder.py`, no SQL DDL changes.
- An expansion of the contract surface. No new endpoints,
  no new typed shapes, no version bumps to
  `betfair_client_contract.md`.
- A change to `_path_b_result` modal recovery wiring at
  `orchestrator.py:1049–1058` beyond the §7.1 canonical-form
  rename. The branch logic, the comment, and the
  fall-through behaviour stay intact.

**Surprises become findings, not blockers.** Code runs the
brief end-to-end in a single bounded session; surfaces
findings in the report's §8; does not ping operator-Claude
mid-flight asking for direction.

**Contradictions and context-loss gaps surface as findings.**
This brief is drafted across multiple sessions of accumulated
context, parts of which are several weeks stale. If Code
encounters: a brief anchor that contradicts the live codebase
(file path moved, line number drifted, signature changed); a
brief reference that contradicts the contract or a prior
locked report; a brief instruction that contradicts another
part of this brief itself; or any apparent context-loss gap
where the brief assumes a fact that doesn't hold — flag it as
a finding in §8 of the report, proceed with the most-
defensible interpretation, and name the assumption made.
Don't pick arbitrarily, don't escalate mid-session, and
don't assume Claude Chat caught everything during drafting.
This is a named safeguard, not a blanket invitation to
question every anchor.

Single bounded Code session. Hard limits in §9.

---

## §2 — Why this work exists

W4 v1 shipped Session 90 with the `BetfairAdapter` Protocol
defined and a `MockBetfairAdapter` test fixture wired up.
W4 follow-up shipped Session 96, extending the Protocol with
`fetch_fresh_runner_price` and adding the `BetRecord.price_source`
field. The housekeeping arc closed Session 98, leaving the
codebase in a clean post-housekeeping state: 323 tests passing
under default `pytest`, ruff clean, import-linter 5/5 contracts
kept.

The Protocol is fully specified across five methods. The
`BetfairClient` v1 surface (W3) is fully assembled across
nine read surfaces, three write surfaces, and the streaming
layer per `betfair_client_contract.md` v1.3. **What's missing
is the production class that connects them.**

The W4 orchestrator currently runs only against
`MockBetfairAdapter` — every test in
`tests/workflows/bet_entry/v1/test_orchestrator.py`
queues canned scenarios via the mock's test hooks. To run W4
against the live Betfair API (operator-side acceptance testing,
eventual production cutover via W8), v3 needs a real adapter
that:

- Calls the existing W3 surfaces (`get_account_funds`,
  `runner_best_prices`, `place_bet`, `get_market_catalogue`,
  the `BetfairClient` consumer-side reading paths).
- Unwraps the `ReadEnvelope` / `WriteEnvelope` shapes into
  the W4 snapshot models (`MarketStatusSnapshot`,
  `FundsSnapshot`, `OrderStateSnapshot`) or the
  `PlacementOutcome` discriminated result.
- Translates Betfair's raw failure modes
  (`BetfairReadUnavailableReason`,
  `BetfairWriteUnavailableReason`, the `rejection_code`
  string set on write rejections) into W4's internal error
  vocabulary.

Two boundary translations specifically fold in here, both
identified in earlier sessions but not yet shipped:

- **`MARKET_SUSPENDED` → `market_suspended`** (housekeeping
  report §8.2 finding). The W4 internal `error_code`
  namespace is lower-snake post-Session-98 §5.3
  canonicalisation; the real adapter is the natural home
  for the upper-snake-to-lower-snake translation when
  reading raw Betfair `marketBook.status` or `placeOrders`
  rejection codes.
- **`INSUFFICIENT_FUNDS` → `insufficient_funds`**
  (Session 98 §7.1 routing call). Same translation pattern;
  the recovery-key chain at `orchestrator.py:1049–1058`
  checks `error_code == "INSUFFICIENT_FUNDS"` (upper-snake)
  separately from the `{"market_suspended",
  "betfair_streaming_disconnected"}` set (lower-snake).
  Standing principle (Session 97 lock — pay tooling-hygiene
  costs now while in build) routes this to be canonicalised
  in the same sweep as the real adapter ships, rather than
  carry the upper-snake outlier forward into live operations.

The Standing principle reads bidirectionally: fix
knowable-bad state, preserve knowable-good state. The
two translations fix knowable-bad state; the rest of W4's
behaviour and the Protocol shape are knowable-good and
preserved.

This brief commissions the real adapter plus the two
boundary translations.

---

## §3 — Pre-reads

In order:

1. **`dr029/w4_bet_entry/w4_followup_brief.md`** (762 lines)
   — locked Protocol extension shape (§5.1), `price_source`
   field (§5.2), REST-fetch fallback wiring (§5.3),
   naming canonicalisation precedent (§5.6). The Protocol
   this adapter implements was defined here. **Required.**

2. **`dr029/w4_bet_entry/w4_followup_report.md`** (447 lines)
   — Code's deviations and findings from the follow-up
   build. §6.1 names the canonicalisation choice (Option A,
   align on W3); §6.4 names the `OPERATOR_TYPED` placement
   call; §8.4 names the first W3-type-import precedent
   (`RunnerBestPrices` imported directly into orchestrator).
   §7.1 raises the implicit "REST returns means fresh"
   contract — confirmed in this brief's §5 wiring.
   **Required.**

3. **`dr029/w4_bet_entry/housekeeping_report.md`** (413 lines)
   — §8.2 names the `MARKET_SUSPENDED` translation pattern
   (W4-internal namespace is lower-snake post-§5.3
   canonicalisation; raw Betfair API `MARKET_SUSPENDED`
   needs translation at the W4 boundary). §7.1 raises the
   `INSUFFICIENT_FUNDS` parallel. Both fold into this
   brief's §5.2 boundary translation layer. **Required.**

4. **`dr029/2_7_api_contract_versioning/betfair_client_contract.md`**
   — required sections:
   - **§9.1 Operational live-pricing reads** (lines 284–381)
     — `runner_best_prices` call shape; `RunnerBestPrices`
     return type; `FreshEnvelope` / `StaleEnvelope` /
     `UnavailableReadEnvelope` discriminated return.
   - **§9.6 Account funds read** (lines 661–727) —
     `get_account_funds` call shape; `AccountFunds` return
     type; `available_to_bet_balance` field used by W4's
     `FundsSnapshot`.
   - **§9.7 Market catalogue read** (lines 728–) —
     `get_market_catalogue` call shape; used by W4's
     pre-flight via the `BetfairClient` consumer-side
     reading paths.
   - **§11.1 Bet placement** (lines 946–1047) —
     `place_bet` call shape; `BetPlacementResult` return
     type; the rejection-code set the adapter translates;
     `customer_order_ref` round-trip; `customer_strategy_ref`
     vs v3-internal `strategy_tag` distinction.
   - **§13 Streaming-disconnect-blocks-writes** (lines
     1244–1290) — the §13.5 v1.3 amendment names
     REST-fetch as the v3-side path that preserves the
     rule's intent. The adapter exposes
     `fetch_fresh_runner_price` per the Protocol; the
     orchestrator wires the fallback chain.

   Reference-only otherwise.

5. **`workflows/bet_entry/v1/orchestrator.py` lines 81–220**
   — the `BetfairAdapter` Protocol definition plus the four
   W4 snapshot models (`MarketStatusSnapshot`,
   `FundsSnapshot`, `OrderStateSnapshot`, `PlacementOutcome`)
   the adapter populates. **Required for signature
   anchoring.**

6. **`clients/betfair_client/v1/__init__.py`** (175 lines)
   — public re-export surface. Names every shape and
   function the adapter imports. **Required for import
   anchoring.**

**Reference-only — read on demand:**

- `decisions.md` DR-027 / DR-028 — cross-DB boundary
  context for why the streaming-disconnect rule lives in
  `betfair_client`.
- `decisions.md` DR-030 — v3 repo layout; informs
  `betfair_adapter.py` placement at
  `workflows/bet_entry/v1/`.
- `decisions.md` DR-031 — Pydantic v2, pytest, ruff,
  import-linter discipline.
- `decisions.md` DR-021 — Adelaide local timestamps for
  any time-of-day reference in the report.
- `clients/betfair_client/v1/account_funds.py` (92 lines),
  `live_pricing.py` (207 lines), `placement.py` (283
  lines), `market_catalogue.py` (135 lines), `consumer.py`
  (155 lines), `envelope.py` (115 lines), `_errors.py`
  (96 lines) — the W3 modules the adapter wraps. Read on
  demand during implementation, not as required pre-reads.
- `dr029/w4_bet_entry/w4_bet_entry_brief.md` (2121 lines)
  — W4 v1 brief. Reference-only; the substrate that drove
  the Protocol shape lives here. Read on demand.
- `dr029/w4_bet_entry/w4_bet_entry_report.md` (837 lines)
  — W4 v1 report. Reference-only.
- `external_api_resources.md` — pointer to Betfair
  Reference Guide and on-disk page captures (placement
  endpoint specs at `dr029/2_4_betfair_streaming/reference_guide/`).
  Read on demand if Betfair raw-API behaviour needs
  cross-checking against the adapter's translation logic.

---

## §4 — System access

- **Filesystem read-write** at the named anchors below.
  Read-only on all other paths in `bethub-v3/`.
  - New file:
    `workflows/bet_entry/v1/betfair_adapter.py`.
  - New file:
    `tests/workflows/bet_entry/v1/test_betfair_adapter.py`.
  - Edit: `workflows/bet_entry/v1/__init__.py` —
    add the new class to the public re-export surface.
  - Edit: `workflows/bet_entry/v1/orchestrator.py` —
    surgical rename only, at the `_path_b_result`
    recovery-key chain (~line 1050) per Session 98 §7.1
    routing call. No other edits to `orchestrator.py`.
  - Edit: `tests/workflows/bet_entry/v1/test_orchestrator.py`
    — surgical rename only, at the matching
    `INSUFFICIENT_FUNDS` test fixture. No other edits.

- **No edits to W3 modules.** `clients/betfair_client/v1/`
  is read-only. The adapter composes the existing W3
  surfaces; it does not modify them.

- **No edits to W4 core modules beyond the surgical
  renames named above.** `models.py`, `record_builder.py`,
  `staking.py`, `pricing.py`, `storage.py` — read-only.
  The Protocol stays as locked; the W4 snapshot models
  the adapter populates are read for signature reference
  but not modified.

- **No Betfair API calls.** All adapter tests run against
  a mocked `BetfairRestClient` (or equivalent W3-surface
  mocking — see §7 for test approach). Real-API
  acceptance testing is operator-side post-merge.

- **No git operations.** No `git add`, `git commit`,
  `git stash`, `git restore`, `git checkout`,
  `git reset`. Read working-tree state at session start
  via `git status`; edit only the named anchors above;
  run `git diff <file>` after each substantive edit to
  confirm only intended changes were added; run
  `git status` at session close to confirm dirty file
  list unchanged from start.

- **Live `bethub-v3/`** at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Tests run
  in-tree via `pytest` from project root.

- **Adelaide local timestamps per DR-021** for any
  time-of-day reference in the report.

---

## §5 — Substantive scope

Six coordinated changes. Sequencing in §6.

### §5.1 — `RealBetfairAdapter` class — construction and dependencies

**Anchor:** new file
`workflows/bet_entry/v1/betfair_adapter.py`.

**Class shape:**

```python
@dataclass(frozen=True)
class RealBetfairAdapter:
    """Production `BetfairAdapter` implementation.

    Wraps `clients.betfair_client.v1` surfaces (`BetfairClient`
    container plus auxiliary deps) and translates Betfair's raw
    API shape into W4's internal namespace per the Protocol at
    `orchestrator.py:166`.
    """

    client: BetfairClient            # REST + streaming bundle
    audit_sink: AuditLogSink         # write-side audit trail
    operator_identity: str           # write-side audit identity
```

**Construction-time invariant:** `client.streaming_client`
must be non-None. The W3 `place_bet` surface (contract §11.1)
requires a `StreamingClient` for the §13 streaming-disconnect
pre-check; an adapter constructed without streaming cannot
satisfy `place_hedge_bet`. Code asserts at `__post_init__` and
raises `ValueError` if `streaming_client` is None. The
adapter does not run REST-only.

**No retry logic at the adapter layer.** The W4 orchestrator
owns retry-with-backoff per `DEFAULT_BACKOFF_SCHEDULE_MS`
(50 / 200 / 500 ms across 3 attempts). The adapter exposes
single-call semantics on each Protocol method; orchestrator
wraps with retry where appropriate (per
`_place_with_retry`, `_place_via_rest_fetch`).

**No caching at the adapter layer.** Each call hits the W3
surface fresh. Streaming-cache routing (when applicable for
read-side calls) happens inside the W3 surface itself; the
adapter passes the `BetfairClient` container through.

**No state across calls.** The adapter is `frozen=True`;
each call is independent. Test scenarios that need stateful
behaviour wire it in at the `BetfairRestClient` mock layer,
not the adapter.

**Imports anchor:**

```python
from datetime import datetime
from decimal import Decimal
from typing import Literal

from clients.betfair_client.v1 import (
    AccountFunds,
    AuditLogSink,
    BetfairClient,
    BetfairReadUnavailableReason,
    BetfairWriteUnavailableReason,
    BetPlacementResult,
    BetSide,
    EnvelopeStatus,
    FreshEnvelope,
    MarketCatalogue,
    MarketPrices,
    MarketStatus,
    PriceLevel,
    PersistenceType,
    RunnerBestPrices,
    StaleEnvelope,
    UnavailableReadEnvelope,
    UnavailableWriteEnvelope,
    WriteEnvelope,
    get_account_funds,
    get_live_market_prices,
    get_market_catalogue,
    get_runner_best_prices,
    place_bet,
    runner_best_prices,
)

from workflows.bet_entry.v1.orchestrator import (
    BetfairAdapter,
    FundsSnapshot,
    MarketStatusSnapshot,
    OrderStateSnapshot,
    PlacementOutcome,
)
```

**Type-checking discipline:** Code declares
`RealBetfairAdapter` satisfies `BetfairAdapter` via Python's
structural Protocol matching (no explicit `class
RealBetfairAdapter(BetfairAdapter):` inheritance — the
Protocol is satisfied by shape). One `assert_type` line at
module bottom verifies static conformance:

```python
from typing import assert_type
assert_type(RealBetfairAdapter, type[BetfairAdapter])  # noqa: F821
```

If `assert_type` is not the right shape for this assertion
under Python 3.12, Code chooses the equivalent static-check
mechanism (e.g. a `_: BetfairAdapter = ...` line at module
scope) and names the choice in the report's §6 deviations.

### §5.2 — Boundary translation layer

**Anchor:** same file `betfair_adapter.py`. Translation
helpers sit as module-level functions below the class
definition, scoped to the adapter's needs.

Three translation concerns:

**(a) Read-envelope unwrapping.** W3 surfaces return
`ReadEnvelope[T]` discriminated union (`FreshEnvelope`,
`StaleEnvelope`, `UnavailableReadEnvelope`); W4 expects
either a populated snapshot model or `None`. The adapter:

- `FreshEnvelope` / `StaleEnvelope` → unwrap `.data` and
  populate the W4 snapshot. (Stale is acceptable — caller
  is the orchestrator which already handles staleness via
  the streaming-disconnect path.)
- `UnavailableReadEnvelope` → return `None` for the
  three methods that allow `None` return
  (`get_account_funds`, `get_order_state`,
  `fetch_fresh_runner_price`); for `get_market_status`
  (which returns `MarketStatusSnapshot` non-optionally),
  surface as `MarketStatusSnapshot(status="INACTIVE",
  ...)` per the Protocol's `Literal["OPEN", "SUSPENDED",
  "CLOSED", "INACTIVE"]` set — `INACTIVE` is the
  pre-existing W4-internal value covering "Betfair side
  not currently reachable for status". Code surfaces the
  underlying `BetfairReadUnavailableReason` in the report's
  §8 if any of these unavailable-read mappings need
  per-reason refinement (e.g. `BETFAIR_AUTH_EXPIRED`
  warranting a different W4-side surface than
  `BETFAIR_API_UNREACHABLE`); v1 maps all unavailable
  reads uniformly to `INACTIVE`.

**(b) Write-envelope discrimination.** The W3
`place_bet` returns `WriteEnvelope[BetPlacementResult]` —
either `FreshEnvelope` (placement landed, possibly with
matched stake) or `UnavailableWriteEnvelope` (placement
refused or rejected). The adapter translates to W4's
`PlacementOutcome` four-value `outcome` literal:

| W3 envelope | W3 reason / rejection | W4 `outcome` |
|---|---|---|
| `FreshEnvelope[BetPlacementResult]` | (success) | `"success"` |
| `UnavailableWriteEnvelope` | `BETFAIR_STREAMING_DISCONNECTED` | `"betfair_streaming_disconnected"` |
| `UnavailableWriteEnvelope` | `BETFAIR_RATE_LIMITED`, `BETFAIR_API_UNREACHABLE`, `BETFAIR_AUTH_EXPIRED`, `BETFAIR_BET_PLACEMENT_IN_PROGRESS` | `"retry_safe"` |
| `UnavailableWriteEnvelope` | `BETFAIR_INSUFFICIENT_FUNDS`, `BETFAIR_WRITE_REJECTED` (any rejection_code) | `"terminal"` |

The `error_code` field on the resulting `PlacementOutcome`:

- `"success"` outcome → `error_code=None`.
- `"betfair_streaming_disconnected"` outcome →
  `error_code="betfair_streaming_disconnected"` (lower-snake
  per W4 follow-up §6.1 canonicalisation).
- `"retry_safe"` outcome → `error_code` carries the W3
  reason as lower-snake string (e.g. `"betfair_rate_limited"`,
  `"betfair_api_unreachable"`).
- `"terminal"` outcome → `error_code` carries the
  W4-translated form (see (c) below).

**(c) Upper-snake to lower-snake translation table.**
Two specific Betfair raw codes translate at this layer:

| Betfair raw | W4 internal | Source | Carrier |
|---|---|---|---|
| `MARKET_SUSPENDED` | `market_suspended` | `placeOrders` `rejection_code` (contract §11.1) | `error_code` on `PlacementOutcome` (terminal) |
| `INSUFFICIENT_FUNDS` | `insufficient_funds` | `BETFAIR_INSUFFICIENT_FUNDS` envelope reason → terminal | `error_code` on `PlacementOutcome` (terminal) |

Both translations happen at the write-envelope discrimination
step — the adapter, never the orchestrator. After this brief
ships, the W4 orchestrator sees only lower-snake error codes
across the recovery-key chain (the §5.5 surgical rename
brings the orchestrator's recovery-key set into line).

Other Betfair `rejection_code` values (per contract §11.1:
`INVALID_BACK_LAY_COMBINATION`, `BET_TAKEN_OR_LAPSED`,
`RUNNER_REMOVED`, `MARKET_NOT_OPEN_FOR_BETTING`, lapse
codes) translate to lower-snake mechanically by the same
rule — Code applies a uniform `_betfair_to_w4_error_code`
helper per the table-driven translation. The two table
entries above are the ones that *also* surface in the W4
recovery-key chain at `_path_b_result`; the others are
informational `error_code` strings that flow through
without orchestrator-side branching today.

### §5.3 — `get_market_status` implementation

**Anchor:** method on `RealBetfairAdapter`.

```python
def get_market_status(self, market_id: str) -> MarketStatusSnapshot:
    envelope = get_live_market_prices(market_id, self.client)
    if envelope.status == EnvelopeStatus.UNAVAILABLE:
        return MarketStatusSnapshot(
            market_id=market_id,
            status="INACTIVE",
            as_of=_now_adelaide(),
        )
    market_prices: MarketPrices = envelope.data
    return MarketStatusSnapshot(
        market_id=market_id,
        status=market_prices.market_status.value,
        as_of=market_prices.cache_as_of,
    )
```

**`MarketPrices.market_status`** is a `MarketStatus` enum
with values `OPEN`, `SUSPENDED`, `CLOSED`. The W4
`MarketStatusSnapshot.status` literal includes
`"INACTIVE"` for the unavailable case. The three Betfair
values pass through unchanged (uppercase, matching the W4
Protocol literal exactly); `INACTIVE` is the W4-side value
for unreachable.

**`as_of` discipline:** when fresh/stale, use the W3
envelope's `cache_as_of` (the cache's last-known time);
when unavailable, use `_now_adelaide()` (the call time).
Adelaide-local per DR-021.

**`_now_adelaide()` helper:** thin wrapper around
`clients.betfair_client.v1._clock.now_utc()` plus
`to_adelaide()`; or, if Code prefers, lift directly from
W3 by importing the helpers it needs. Code's choice; named
in the report's §6 if any choice is non-obvious.

### §5.4 — `get_account_funds` implementation

**Anchor:** method on `RealBetfairAdapter`.

```python
def get_account_funds(self) -> FundsSnapshot | None:
    envelope = get_account_funds(self.client.rest_client)
    if envelope.status == EnvelopeStatus.UNAVAILABLE:
        return None
    funds: AccountFunds = envelope.data
    return FundsSnapshot(
        available_to_bet_balance=Decimal(
            str(funds.available_to_bet_balance)
        ),
        as_of=funds.cache_as_of,
    )
```

**Decimal conversion:** W3's `AccountFunds.available_to_bet_balance`
is `float`; W4's `FundsSnapshot.available_to_bet_balance` is
`Decimal`. Converting via `str()` avoids float-precision
artefacts in the Decimal representation. Code uses
`Decimal(str(value))`; if Code finds a cleaner pattern in
the existing codebase (e.g. a shared float-to-Decimal
helper in W3 or W4), it adopts that and names the choice
in §6.

**Unavailable-handling:** per Protocol, returns `None`.
The orchestrator's `pre_flight_check` already handles
`None` per W4 brief §4.3 (`funds_check_unavailable` warn
flag).

### §5.5 — `place_hedge_bet` implementation

**Anchor:** method on `RealBetfairAdapter`.

```python
def place_hedge_bet(
    self,
    *,
    market_id: str,
    selection_id: str,
    side: Literal["BACK", "LAY"],
    price: float,
    stake: Decimal,
    customer_order_ref: str,
    strategy_tag: str | None,
) -> PlacementOutcome:
    assert self.client.streaming_client is not None  # invariant per §5.1
    envelope = place_bet(
        market_id=market_id,
        selection_id=selection_id,
        side=BetSide(side),
        price=price,
        stake=float(stake),
        customer_order_ref=customer_order_ref,
        rest_client=self.client.rest_client,
        streaming_client=self.client.streaming_client,
        audit_sink=self.audit_sink,
        operator_identity=self.operator_identity,
        customer_strategy_ref=None,
        persistence_type=PersistenceType.PERSIST,
        strategy_tag=strategy_tag,
    )
    return _envelope_to_placement_outcome(envelope)
```

**Decimal-to-float conversion at the placement boundary.**
W3's `place_bet` takes `stake: float`; W4's
`place_hedge_bet` Protocol receives `stake: Decimal`.
`float(stake)` is the conversion. The fidelity loss is
acceptable because Betfair's API itself takes float; the
adapter sits on the boundary where Decimal precision stops
being meaningful.

**`customer_strategy_ref=None`:** per contract §11.1,
this is the Betfair-payload string distinct from
`strategy_tag` (which is v3-internal, audit-only). W4 v1
doesn't populate `customer_strategy_ref` — the operator
hasn't surfaced a use case. Code passes `None`; if W4 v1
later surfaces a `customer_strategy_ref` use case at the
orchestrator level, the Protocol gets extended at that
point. Out of this brief.

**`persistence_type=PersistenceType.PERSIST`:** per
contract §2.4 §9.6 day-one default, `PERSIST` is the
correct value for hedge bets (don't lapse at turn-in-play).
The Protocol doesn't expose `persistence_type` to the
caller — the adapter hard-wires `PERSIST` per the day-one
default. Future workflows that need `LAPSE` or
`MARKET_ON_CLOSE` (W7 burst review may surface a use case)
add it as a Protocol extension at that point.

**Return shape via `_envelope_to_placement_outcome`:**
helper function applying §5.2(b) and §5.2(c) tables to
produce the four-value `PlacementOutcome`. Helper signature:

```python
def _envelope_to_placement_outcome(
    envelope: WriteEnvelope[BetPlacementResult],
) -> PlacementOutcome:
    if envelope.status == EnvelopeStatus.FRESH:
        result: BetPlacementResult = envelope.data
        return PlacementOutcome(
            outcome="success",
            bet_id=result.bet_id,
            initial_size_matched=Decimal(str(result.initial_size_matched)),
            size_remaining=Decimal(str(result.size_remaining)),
            average_price_matched=result.average_price_matched,
            placed_at=result.placed_at,
            error_code=None,
            error_detail=None,
            raw={},
        )
    # UnavailableWriteEnvelope path
    return _unavailable_to_placement_outcome(envelope)
```

`_unavailable_to_placement_outcome` is the per-reason
discrimination table from §5.2(b), populating the four-
value `outcome` plus the lower-snake `error_code`. Code
implements as a small dispatch table or `match` statement.

### §5.6 — `get_order_state` implementation

**Anchor:** method on `RealBetfairAdapter`.

The `BetfairAdapter` Protocol (orchestrator.py:208–220)
specifies:

```python
def get_order_state(
    self,
    *,
    market_id: str,
    selection_id: str,
    bet_id: str,
    original_size: Decimal,
) -> OrderStateSnapshot | None:
    ...
```

**Implementation challenge:** the W3 surface for order-state
reads is `listCurrentOrders` (per contract §2.4 §9.4 + W4
brief §6.3). **The W3 v1 surface re-export at
`clients/betfair_client/v1/__init__.py` does not currently
expose `list_current_orders` or any order-state read
function.** This is an apparent context-loss gap per §1.

**Code's path forward:** at session start, Code grep for
order-state functions in `clients/betfair_client/v1/`
(both re-exported and module-local). If a function exists
at the module-local level (e.g. inside `consumer.py`,
`placement.py`, or a separate `orders.py`), Code uses it
directly via the appropriate import path and names the
discovery in §6 deviations. If no function exists at all,
Code:

(a) Implements `get_order_state` as a **stub** that returns
`None` unconditionally with a docstring naming the gap;
**does not** add a `list_current_orders` surface to W3
(out of scope per §9 hard limits).

(b) Adds the gap as the brief's primary §8 finding — the
real-adapter `get_order_state` cannot land cleanly until
W3 exposes the underlying surface, and that's contract
work that needs its own brief.

(c) Names the impact in §9 self-assessment: Trigger B
reconciliation (orchestrator brief §6.2) cannot exercise
against the real adapter until the W3 surface lands. The
mock-driven Trigger B tests remain valid; real-adapter
acceptance is partial pending the W3 work.

Either path (W3 surface exists, or stub-with-finding) is
acceptable. Code's call.

### §5.7 — `fetch_fresh_runner_price` implementation

**Anchor:** method on `RealBetfairAdapter`.

Per the W4 follow-up Protocol docstring (orchestrator.py:204):

> A real implementation wraps
> `clients.betfair_client.v1.live_pricing.runner_best_prices`
> with `streaming_client=None` to force the REST path.

```python
def fetch_fresh_runner_price(
    self,
    market_id: str,
    selection_id: str,
) -> RunnerBestPrices | None:
    envelope = runner_best_prices(
        market_id=market_id,
        selection_id=selection_id,
        rest_client=self.client.rest_client,
        streaming_client=None,  # force REST per W4 follow-up §13.5
    )
    if envelope.status == EnvelopeStatus.UNAVAILABLE:
        return None
    return envelope.data
```

**`streaming_client=None`** forces the REST path per
contract §10 routing (cache satisfies only when
`streaming_client is not None`). This is the structural
guarantee that `fetch_fresh_runner_price` returns a fresh
REST price, not a possibly-stale cached value — the
contract §13.5 amendment exists precisely because of this
guarantee.

**Stale envelope handling:** REST-only routing means stale
envelopes are not returned (the cache is bypassed
entirely). If a stale envelope ever does appear (W3
implementation choice), the adapter unwraps `.data` and
returns it; orchestrator's caller-side discrimination is
the same.

**Unavailable-handling:** per Protocol, returns `None`.
The orchestrator's REST-fetch-fallback chain (W4 follow-up
§5.3) handles `None` by falling through to the modal
recovery wiring.

### §5.8 — Orchestrator surgical rename — `INSUFFICIENT_FUNDS`

**Anchor:** `workflows/bet_entry/v1/orchestrator.py:1049`.

```python
if outcome.error_code == "INSUFFICIENT_FUNDS":
    recovery = (
        "Top up Betfair funds and retry",
        *recovery,
    )
```

**Change:** rename the literal `"INSUFFICIENT_FUNDS"` to
`"insufficient_funds"`. Mechanical surgical edit; no logic
change. Post-rename, the recovery-key chain reads
uniformly in lower-snake:

```python
if outcome.error_code == "insufficient_funds":
    ...
elif outcome.error_code in {
    "market_suspended",
    "betfair_streaming_disconnected",
}:
    ...
```

**Test fixture rename:**
`tests/workflows/bet_entry/v1/test_orchestrator.py:581`:

```python
adapter.queue_placement(
    PlacementOutcome(
        outcome="terminal",
        error_code="INSUFFICIENT_FUNDS",
        ...
    )
)
```

becomes:

```python
adapter.queue_placement(
    PlacementOutcome(
        outcome="terminal",
        error_code="insufficient_funds",
        ...
    )
)
```

Plus the matching assertion at `:589`:

```python
assert result.error_context.error_code == "INSUFFICIENT_FUNDS"
```

becomes:

```python
assert result.error_context.error_code == "insufficient_funds"
```

**Pre-flight namespace preserved.** The pre-flight
`PreFlightFlag.code` namespace at lines 396–411 (and the
test cases referencing it at `test_orchestrator.py:398`,
`:409`, and `orchestrator.py:554` for the warn-flag code
emission) is W4-internal and intentionally upper-snake per
housekeeping report §7.2 confirmatory item. **Code does
not rename pre-flight `INSUFFICIENT_FUNDS` references.**
The §5.8 rename is scoped exclusively to the recovery-key
chain branch and its associated test fixture.

If Code finds any other `"INSUFFICIENT_FUNDS"` literal in
the codebase outside the pre-flight namespace and outside
the recovery-key chain, surface as a §6 deviation with
the location and Code's call on whether it falls under the
canonicalisation scope.

### §5.9 — Re-export update at `__init__.py`

**Anchor:** `workflows/bet_entry/v1/__init__.py`.

Add `RealBetfairAdapter` to the public re-export surface
alongside the existing class re-exports. Maintain
alphabetical ordering of `__all__` per existing
convention.

---

## §6 — Sequencing within session

Build order, dependency-driven:

1. **§5.1 — `RealBetfairAdapter` class skeleton + imports +
   construction-time invariant.** Lands first; no methods
   implemented yet, just the dataclass shell, imports, and
   the `__post_init__` assertion. Confirms imports resolve
   cleanly against the live W3 surface.

2. **§5.2 — Boundary translation helpers** (`_betfair_to_w4_error_code`,
   `_unavailable_to_placement_outcome`,
   `_envelope_to_placement_outcome`, `_now_adelaide`). Pure
   functions; testable in isolation. Lands before the
   Protocol method implementations that consume them.

3. **§5.3 — `get_market_status`.** Smallest method;
   exercises read-envelope unwrapping on the simplest case
   (no Decimal handling, single field translation). Good
   first integration of the helpers from §5.2.

4. **§5.4 — `get_account_funds`.** Adds Decimal conversion
   to the unwrapping pattern. Builds on §5.3's shape.

5. **§5.6 — `get_order_state` (or stub-with-finding).**
   Sequenced before §5.5 because if W3 doesn't expose the
   underlying surface, Code lands the stub here and moves
   on. If W3 does expose the surface, Code implements it
   here. Either way, the call is named before placement
   work begins.

6. **§5.7 — `fetch_fresh_runner_price`.** Builds on §5.3's
   read-envelope-unwrapping pattern with the
   `streaming_client=None` forced-REST routing. Sequenced
   before placement so the helper that placement's REST-
   fallback uses is in place.

7. **§5.5 — `place_hedge_bet`.** Largest method;
   exercises write-envelope discrimination, the per-reason
   table, the upper-to-lower translation, plus
   `customer_order_ref` and `strategy_tag` round-trip.
   Lands after the helpers and the simpler methods are
   working.

8. **§5.8 — Orchestrator surgical rename.** Mechanical;
   small. Lands after the adapter's translation layer is
   in place so post-rename, the orchestrator's recovery-key
   chain reads only lower-snake codes (matching what the
   adapter produces). Run pytest to confirm green after
   this step before moving to test-module work.

9. **§5.9 — `__init__.py` re-export update.** Mechanical;
   small. Lands before the test module so test imports
   resolve cleanly.

10. **Test module — `test_betfair_adapter.py`.** Per §7
    structure. Lands last because it depends on every
    method being implemented.

11. **Final verification pass per §8.** pytest, ruff,
    import-linter, manual spot-checks.

---

## §7 — Test scope

**Expected pytest delta:** +10 to +18 new tests; baseline
323 → 333–341 expected. Zero regression on the existing
323.

All new tests live in
`tests/workflows/bet_entry/v1/test_betfair_adapter.py`.

**Test categories:**

### §7.1 — Construction and invariant tests

- `test_real_adapter_requires_streaming_client` —
  constructing with `BetfairClient(streaming_client=None)`
  raises `ValueError`.
- `test_real_adapter_satisfies_protocol` — static type
  check via `assert_type` or runtime conformance check;
  ensures the dataclass shape matches the Protocol.

### §7.2 — `get_market_status` tests

- `test_get_market_status_open` — fresh envelope with
  `OPEN` status returns `MarketStatusSnapshot(status="OPEN")`.
- `test_get_market_status_suspended` — fresh envelope with
  `SUSPENDED` status returns
  `MarketStatusSnapshot(status="SUSPENDED")`.
- `test_get_market_status_unavailable_returns_inactive`
  — unavailable envelope returns
  `MarketStatusSnapshot(status="INACTIVE")` with `as_of=now`.

### §7.3 — `get_account_funds` tests

- `test_get_account_funds_fresh` — fresh envelope returns
  `FundsSnapshot` with Decimal-converted balance.
- `test_get_account_funds_unavailable_returns_none` —
  unavailable envelope returns `None`.
- `test_get_account_funds_decimal_precision` — float
  `1247.83` from W3 round-trips to `Decimal("1247.83")`
  without precision artefact.

### §7.4 — `place_hedge_bet` tests

- `test_place_hedge_bet_success` — fresh envelope with
  matched stake returns
  `PlacementOutcome(outcome="success", bet_id=..., ...)`.
- `test_place_hedge_bet_streaming_disconnected_translates`
  — unavailable envelope with reason
  `BETFAIR_STREAMING_DISCONNECTED` returns
  `PlacementOutcome(outcome="betfair_streaming_disconnected",
  error_code="betfair_streaming_disconnected")`.
- `test_place_hedge_bet_insufficient_funds_translates`
  — unavailable envelope with reason
  `BETFAIR_INSUFFICIENT_FUNDS` returns
  `PlacementOutcome(outcome="terminal",
  error_code="insufficient_funds")` (lower-snake post-
  translation).
- `test_place_hedge_bet_market_suspended_translates`
  — unavailable envelope with `BETFAIR_WRITE_REJECTED` +
  `rejection_code="MARKET_SUSPENDED"` returns
  `PlacementOutcome(outcome="terminal",
  error_code="market_suspended")` (lower-snake post-
  translation).
- `test_place_hedge_bet_rate_limited_retry_safe` —
  unavailable envelope with reason `BETFAIR_RATE_LIMITED`
  returns `PlacementOutcome(outcome="retry_safe",
  error_code="betfair_rate_limited")`.
- `test_place_hedge_bet_decimal_to_float_conversion`
  — `stake=Decimal("50.00")` from W4 forwards as `50.0`
  float to `place_bet`.
- `test_place_hedge_bet_customer_order_ref_round_trip`
  — `customer_order_ref` echoes back through the result.

### §7.5 — `fetch_fresh_runner_price` tests

- `test_fetch_fresh_runner_price_fresh` — fresh envelope
  returns the unwrapped `RunnerBestPrices`.
- `test_fetch_fresh_runner_price_unavailable_returns_none`
  — unavailable envelope returns `None`.
- `test_fetch_fresh_runner_price_forces_rest` —
  asserts `streaming_client=None` is passed to
  `runner_best_prices` regardless of whether the adapter's
  client has a streaming client wired (the forced-REST
  guarantee per contract §13.5).

### §7.6 — `get_order_state` tests

If the W3 surface exists (per §5.6 path): tests covering
fresh envelope, unavailable envelope, and any matched-size
edge cases per the surface's actual behaviour.

If the W3 surface does not exist (stub path):
`test_get_order_state_stub_returns_none` — stub
implementation returns `None` and does not raise.

### §7.7 — Orchestrator surgical-rename regression

The existing
`test_path_b_insufficient_funds_terminal` test
(`test_orchestrator.py:573–595`) plus the rename at
§5.8 — Code confirms the test still passes post-rename.
No new test added; the existing test exercises the
recovery-key chain match against the renamed code.

**Mock approach for `BetfairRestClient`.** Code chooses
between (a) a hand-rolled mock class that implements the
`BetfairRestClient` interface (similar to the existing
`MockBetfairAdapter` pattern), or (b) `unittest.mock` /
`pytest-mock` / similar. Hand-rolled is the existing W4
pattern; Code's call on whether to follow it or adopt
`unittest.mock` for this test module. Named in §6 of the
report.

**`AuditLogSink` and streaming.** Tests use
`MemoryAuditLogSink` (already in the W3 public surface)
plus a minimal `StreamingClient` test double that returns
`SUBSCRIBED` state. Code may need to construct a small
test-double `StreamingClient` if one doesn't already
exist; it's a thin object whose only required method for
these tests is `streaming_status()` returning
`StreamingStatus(state=StreamingConnectionState.SUBSCRIBED)`.

---

## §8 — Empirical verification

**Pre-change baseline (capture at session start):**

```
$ cd /Users/tim/Desktop/Projects/bethub-v3
$ git status
$ python -m pytest --co -q 2>&1 | tail -5
$ python -m pytest 2>&1 | tail -10
```

Confirm: 323 tests collected, 323 passing, 0 failures, 0
xfails, 0 skips. If the baseline differs from 323, **stop
and surface as finding** — the brief's expected delta
arithmetic depends on this baseline.

Also confirm that `git status` shows no edits to the
named anchors above (clean tree at the brief's edit sites
even if other regions are dirty). Surface any conflict.

**Post-change verification (capture at session close):**

```
$ python -m pytest 2>&1 | tail -10
$ python -m ruff check . 2>&1 | tail -5
$ python -m lint_imports 2>&1 | tail -10
```

Confirm:

- pytest passes 333–341 tests (zero regression on baseline
  323 + 10–18 new). If outside this range, surface as
  finding.
- ruff clean across project.
- All 5 import-linter contracts kept (per W4 v1 baseline).

**Manual spot-check 1** — open `betfair_adapter.py` and
confirm:
- `RealBetfairAdapter` is `frozen=True` per §5.1.
- `__post_init__` raises on `streaming_client=None`.
- All five Protocol methods implemented with the signatures
  matching `orchestrator.py:166–220`.
- Translation helpers are module-level, not class methods.

**Manual spot-check 2** — open `orchestrator.py:1049–1058`
and confirm:
- Recovery-key chain reads `if outcome.error_code ==
  "insufficient_funds":` (lower-snake).
- The set immediately below reads
  `{"market_suspended", "betfair_streaming_disconnected"}`
  unchanged.
- The comment at lines 1044–1048 is unchanged.

**Manual spot-check 3** — open
`tests/workflows/bet_entry/v1/test_orchestrator.py` lines
398, 409, 554 (pre-flight namespace) and confirm those
references still read `"INSUFFICIENT_FUNDS"` (upper-snake,
preserved per §5.8 scope discipline).

---

## §9 — Hard limits

Non-negotiable list of what's NOT in scope.

- **No edits to `clients/betfair_client/v1/`.** The W3
  surface is read-only. The adapter composes existing
  surfaces; it does not modify them. If a needed surface
  is missing (per §5.6 `get_order_state`), Code reports
  the gap as a finding and does not add the surface.
- **No edits to `betfair_client_contract.md`.** The
  contract is locked at v1.3 from W4 follow-up §5.5. No
  amendments, no version bumps, no §6 history rows from
  this brief.
- **No edits to the `BetfairAdapter` Protocol** at
  `orchestrator.py:166–220`. The Protocol is the contract
  the adapter satisfies; it stays as locked.
- **No edits to W4 core modules beyond §5.8 surgical
  rename.** `models.py`, `record_builder.py`, `staking.py`,
  `pricing.py`, `storage.py`, the rest of `orchestrator.py`
  outside `:1049` — read-only.
- **No edits to `MockBetfairAdapter`** at
  `test_orchestrator.py:74`. The mock and the real adapter
  coexist; tests in `test_orchestrator.py` continue to use
  the mock.
- **No SQL schema changes.** No migrations, no Alembic, no
  DDL. The W4 SQLite stub stays as locked Session 98.
- **No new contract surfaces.** No new endpoints, no new
  typed shapes beyond what the adapter constructs from W3
  shapes, no new versioned surface.
- **No streaming-side integration.** The adapter is
  REST-only (per §1, §5.1). If `place_bet`'s streaming-state
  pre-check fires, that's W3's behaviour and the adapter
  passes the resulting envelope through unchanged. The
  adapter does not query streaming state directly.
- **No real Betfair API calls.** All adapter tests run
  against mocked `BetfairRestClient`. Real-API acceptance
  is operator-side post-merge.
- **No pre-flight namespace rename.** The
  `PreFlightFlag.code` upper-snake namespace
  (`MARKET_OPEN`, `MARKET_SUSPENDED`, `MARKET_CLOSED`,
  `MARKET_STATUS_UNAVAILABLE`, `INSUFFICIENT_FUNDS`) is
  preserved per housekeeping report §7.2.
- **No retry logic at the adapter layer.** Retry is the
  orchestrator's responsibility per W4 brief §5; the
  adapter exposes single-call semantics.
- **No caching at the adapter layer.** Each call hits the
  W3 surface fresh.
- **No git operations.** Per §4.
- **No operator escalation mid-session.** Code runs end-
  to-end; surfaces findings in the report; doesn't ping
  operator-Claude mid-flight asking for direction. If the
  brief has a gap, name it as a finding in §6 deviations
  or §8 of the report.
- **No DB-side coordination.** No writes to any DB; no
  reads either. The change is module-layer only.
- **Single bounded Code session.** If the work doesn't fit
  in one bounded session, that's a finding — don't
  continue past budget. Partial-but-coherent beats
  complete-but-lost-coherence.

**Contradictions and context-loss safeguard** (per §1):
if Code encounters a brief anchor that contradicts the
live codebase, the contract, a prior locked report, or
another part of this brief, flag as a finding in §8 of
the report, proceed with the most-defensible
interpretation, and name the assumption made. Don't pick
arbitrarily, don't escalate mid-session.

---

## §10 — Output spec

**Single output file:**
`dr029/w4_bet_entry/real_adapter_report.md`.

**Length target:** 400–600 lines. Comparable to the W4
follow-up report (447 lines) for a build of similar
scope.

**Section structure (anchored on the universal report
shape):**

1. Header / summary of what shipped.
2. Modules edited (per file, with line range and change
   summary).
3. Tests built (table per file with case count and
   highlights).
4. Test results (pytest, ruff, import-linter output).
5. Linting + import-linter results (already covered in
   §4 above; expand if any contract drift).
6. Deviations from brief (Code's calls when ambiguity
   surfaced — e.g. `assert_type` shape choice in §5.1,
   `get_order_state` path choice in §5.6, mock approach
   in §7).
7. Open questions (residual ambiguity for operator-Claude
   triage; one per question, scoped tightly).
8. Findings (operational observations and contract-shape
   items that aren't deviations or open questions but
   matter for next-stage work — including any
   contradictions or context-loss gaps surfaced per §1
   safeguard).
9. Self-assessment (session-budget fit, confidence
   regions, length-range overrun if any, what the
   operator should look at first).

**What the report does not contain:**

- No proposed remediations or follow-up briefs. Code
  reports findings and questions; operator-Claude triages.
- No scope creep into adjacent W4 items.
- No conclusions or overall verdict beyond the
  self-assessment's "did the build fit" framing.
- No real-API integration claims. All tests run against
  mocks; real-API behaviour is operator-side acceptance
  work post-merge.

---

## §11 — What happens after Code's session

**Session 100 (operator-Claude triage):**

1. Read the report end-to-end.
2. Walk deviations (§6) — confirm Code's calls.
3. Walk open questions (§7) one per round, plain-operator-
   language framing per Cat 1.
4. Walk findings (§8) — route each (no action / fold into
   existing carry / new brief / contract-housekeeping
   sweep). The §5.6 `get_order_state` path discovery is
   likely the largest finding to route — if the W3 surface
   doesn't exist, this surfaces as a fresh contract-work
   brief candidate.
5. Lock close-out: brief closed; W4 real-adapter arc
   complete (or partial-with-named-debt depending on
   §5.6 outcome); carry-forward items into
   `current_state.md`.

**Sequence after Session 100:**

- v3 composition-root structural decision drafting
  remains sequenced for whenever it next slots in —
  the real adapter is one of the W4 entry-point objects
  the composition root wires, so this is a natural
  follow-on.
- `bethub-v3/clients/betfair_client/v1/` `list_current_orders`
  surface (or equivalent) — if §5.6 surfaces a gap,
  this becomes a candidate brief for W3 contract work.
- W6 brief drafting — operational store schema. Real
  adapter stays in scope as the production
  `BetfairAdapter` for W6's Trigger B reconciliation
  consumer paths.
- W7 brief drafting — burst review workflow. Real
  adapter stays in scope as the production
  `BetfairAdapter` for W7's read-side calls (live
  pricing, market status).
- Standing-instructions sweep — eleven-or-twelve sweep
  candidates accumulated; dedicated fresh-mind session
  whenever operator wants. No gating dependency.

**Code does not produce the next brief.** That's
operator-Claude's work in Session 100 onward.

---

## §12 — Cross-references

- **W4 follow-up brief** at
  `dr029/w4_bet_entry/w4_followup_brief.md` — Protocol
  extension at §5.1; `price_source` field at §5.2;
  REST-fetch wiring at §5.3; canonicalisation precedent
  at §5.6.
- **W4 follow-up report** at
  `dr029/w4_bet_entry/w4_followup_report.md` — §6.1
  canonicalisation Option A; §8.4 first W3-type-import
  precedent (`RunnerBestPrices`); §7.1 implicit
  REST-returns-fresh contract.
- **Housekeeping report** at
  `dr029/w4_bet_entry/housekeeping_report.md` — §8.2
  `MARKET_SUSPENDED` translation pattern; §7.1
  `INSUFFICIENT_FUNDS` parallel; §7.2 pre-flight
  namespace preservation.
- **Betfair client contract** at
  `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  — §9.1 (`runner_best_prices`); §9.6
  (`get_account_funds`); §9.7 (`get_market_catalogue`);
  §11.1 (`place_bet`); §13 (streaming-disconnect-blocks-
  writes including §13.5 v1.3 amendment).
- **`BetfairAdapter` Protocol** at
  `workflows/bet_entry/v1/orchestrator.py:166–220` — the
  contract this brief implements.
- **W4 brief** at `dr029/w4_bet_entry/w4_bet_entry_brief.md`
  — original W4 v1 commission. Reference-only; the
  Protocol shape originated here.
- **DR-027** (the two-database architecture decision:
  BetHub owns operational state, capture.db owns
  analytical/source data) — context for why streaming-
  disconnect rule lives in `betfair_client` not in v3
  modules.
- **DR-028** (the cross-database integration boundary
  discipline decision: no caching, no denormalisation,
  no second integration point) — same.
- **DR-030** (v3 repo layout and module-boundary
  discipline) — informs `betfair_adapter.py` placement
  at `workflows/bet_entry/v1/`.
- **DR-031** (v3 tech stack: Python 3.12+, Pydantic v2,
  pytest, ruff, import-linter) — discipline for the new
  module.
- **DR-032** (canonical reference layer for all bet
  records) — informs the boundary-translation discipline
  (W4 internals stay clean of Betfair raw shape).
- **DR-021** (timestamp anchoring, Adelaide local time)
  — applies to the report's timestamps and any
  `as_of` field the adapter populates.
- **Standing principle (Session 97 lock)** — pay
  tooling-hygiene and structural-consistency costs now
  while the project is in build. Drives the §5.8
  `INSUFFICIENT_FUNDS` rename in the same sweep as
  the real adapter ships.
- **Session 98** at `sessions/SESSION_98.md` — W4
  housekeeping arc closed; §7.1 routing call folded
  `INSUFFICIENT_FUNDS` canonicalisation into this
  brief's scope.
- **Session 96** at `sessions/SESSION_96.md` —
  Protocol extension and `price_source` field shipped;
  precedent for the brief's structural shape.
- **Session 87** at `sessions/SESSION_87.md` — W4 v1
  brief drafting precedent.

**Parking-lot items excluded from this brief:**

- W3 `list_current_orders` surface addition (or
  equivalent for `get_order_state`) — out of scope per
  §5.6 / §9; surfaces as finding if the W3 surface
  doesn't currently exist.
- Streaming-side integration (DR-029 §2.4 build).
- `customer_strategy_ref` population at the
  orchestrator level — out of scope; no use case.
- `persistence_type` exposure at the Protocol level
  (LAPSE / MARKET_ON_CLOSE) — out of scope; no use
  case until W7 burst review surfaces one.
- Pre-flight namespace canonicalisation
  (`PreFlightFlag.code` upper-snake) — separate sweep
  candidate per housekeeping report §7.2.
- W7 brief drafting — sequenced after.
- W6 brief drafting — sequenced after.
- v3 composition-root structural decision drafting —
  sequenced after.
- Standing-instructions sweep — separate session.

---

**End of brief.**
