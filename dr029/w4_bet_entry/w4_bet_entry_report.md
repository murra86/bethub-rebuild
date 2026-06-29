# W4 — Betfair hedge-entry workflow v1: Code session report

**Brief:** `dr029/w4_bet_entry/w4_bet_entry_brief.md` (locked,
2121 lines).
**Session model:** single bounded Code session per brief §12.1.
**Session open:** 2026-05-06 ~13:30 Adelaide local (ACST/ACDT,
UTC+09:30) per DR-021.
**Session close:** 2026-05-06 ~16:50 Adelaide local.
**Wall-clock:** ~3 hours 20 minutes (read pre-reads, build,
test, lint, write report).
**Build location:** `/Users/tim/Desktop/Projects/bethub-v3/workflows/bet_entry/v1/`.

## §1 — Header / summary of what shipped

The four locked W4 v1 workflow modules, the support files
(`models.py`, `storage.py`, `__init__.py`, `tests/`), full pytest
test set across all four modules, and this report. All module-
boundary discipline (DR-030 import-linter contracts) and
formatting discipline (`ruff`) clean. 287 tests pass — 212 v3
tests already in the suite plus 75 new W4 tests.

What this session shipped:

- **Module set**: `orchestrator.py` (impure), `staking.py`
  (pure), `pricing.py` (pure), `record_builder.py` (pure) — the
  four locked modules per brief §2 / §12.2.
- **Support files**: `models.py` (Pydantic v2 contracts shared
  across modules), `storage.py` (`BetRecordStorage` Protocol +
  SQLite reference impl per brief §9.4), `__init__.py` (public
  re-exports).
- **Test set**: pure-module unit tests (`test_staking.py`,
  `test_pricing.py`, `test_record_builder.py`), the
  storage-stub roundtrip tests (`test_storage.py`), the
  mocked-API orchestrator tests (`test_orchestrator.py`).
- **Report**: this file.

What this session did **not** ship:

- W4.1 / W5 / W6 / W7 work (out of W4 v1 scope per brief §1.2).
- Strategy 3 SGM mechanics (reserved enum value; raises in
  `record_builder.py`).
- Real-API integration tests (operator-side acceptance per
  brief §10.3 / §12.8).

## §2 — Modules built

### §2.1 — `models.py` (340 lines)

**Path:** `workflows/bet_entry/v1/models.py`.

**Public surface:**
- Enums: `StrategyTag`, `MatchStatus`, `EntryPath`, `LegRole`,
  `BetSideTag`, `Construction`, `HedgeSoftBookStakeKind`.
- DR-032 schema: `BetLeg`, `BetRecord`.
- Pre-flight: `PreFlightSeverity`, `PreFlightFlag`,
  `PreFlightResult`.
- Result envelopes: `ErrorContext`, `HedgePlacementResult`,
  `SoftBookLogResult`.

**Dependencies:** Pydantic v2 (per DR-031), stdlib `datetime` /
`decimal` / `enum` / `typing`. No imports from other workflow
modules; this is the canonical contract.

**Implementation choices:**
- `BetRecord.legs` is a `tuple[BetLeg, ...]` not `list` —
  `model_config = ConfigDict(frozen=True)` requires hashable
  contents. Records are immutable post-construction, matching
  DR-032 §4 (Set B is "historical fact, not live mirror").
- Stake fields (`requested_stake`, `matched_stake`,
  `unmatched_stake`) typed as `Decimal` rather than `float`.
  Math review §1 names two-decimal stake rounding; SQLite
  storage uses Decimal-as-string. Float would introduce
  rounding error on round-trip.
- `BetLeg.betfair_implied_probability` typed `float | None`
  per DR-032 §2 last bullet ("Optionally: the leg's individual
  Betfair-implied probability at logging time").

### §2.2 — `storage.py` (431 lines)

**Path:** `workflows/bet_entry/v1/storage.py`.

**Public surface:**
- `BetRecordStorage` Protocol — three methods
  (`write_bet_record`, `update_match_status`, `read_bet_record`)
  per brief §9.4.
- `WriteResult` dataclass.
- `InMemoryBetRecordStorage` — volatile, used by tests.
- `SQLiteBetRecordStorage` — file-backed reference implementation.

**Dependencies:** stdlib `sqlite3`, `threading`, `pathlib`. The
Pydantic models from `models.py`. No SQLAlchemy yet — the v1
stub is small enough that SQLAlchemy Core's value adds
indirection without payoff at this scale; W6's production
implementation will move to SQLAlchemy Core + Alembic per
DR-031.

**Implementation choices:**
- `bets` table primary key is `bet_id`; `bet_legs` table
  composite PK is `(bet_id, leg_number)` with FK to `bets`. The
  `bets` row carries the stake fields per DR-032 §3 (no stake
  on legs).
- WAL mode + `PRAGMA foreign_keys = ON` per DR-031.
- Decimal stakes stored as canonical string text to avoid the
  binary float drift sqlite would otherwise produce.
- Process-local lock + `BEGIN IMMEDIATE` transaction wraps
  writes — sufficient for the single-operator scale; W6's
  schema build will own a real concurrency story.
- `force_fail_next_write(count=N)` test hook on
  `InMemoryBetRecordStorage` queues `N` consecutive failures so
  the orchestrator's 3-attempt retry path can be exercised
  cleanly.

### §2.3 — `record_builder.py` (361 lines)

**Path:** `workflows/bet_entry/v1/record_builder.py`.

**Public surface:**
- `BetRecordBuilderError` exception.
- `LegSnapshot`, `HedgeRecordInputs`, `SoftBookRecordInputs`
  Pydantic v2 input shapes.
- `build_hedge_bet_record`, `build_soft_book_bet_record`
  functions.

**Dependencies:** stdlib `uuid` / `datetime` / `decimal`,
Pydantic v2, `models.py`. Pure — no I/O, no other workflow
imports.

**Implementation choices:**
- `cycle_id` and `bet_id` auto-generate as
  `cycle-<uuid4>` / `bet-<uuid4>` when not supplied (brief
  §3.6: builder generates fresh for cycle's first bet;
  inherits parent cycle when supplied).
- Strategy-tag validation enforces DR-032 closed enum +
  raises on `SGM_CORRELATED` per brief §3.2 ("the value
  exists in the enum so the schema doesn't change when W4.1 /
  W7 ships SGM entry, but W4 v1's `record_builder.py` raises
  if asked to build a record with `strategy_tag =
  'sgm_correlated'`").
- `is_free_bet` / `free_bet_conversion_rate` invariants per
  brief §3.3: rate must be NULL when not free-bet; rate in
  (0, 1] when free-bet.
- `realised_conversion_rate` always set to NULL by W4 (W5
  populates at settlement per brief §3.3).

### §2.4 — `staking.py` (400 lines)

**Path:** `workflows/bet_entry/v1/staking.py`.

**Public surface:**
- `StakingError` exception.
- `CommissionLookupKey`, `HedgeStakeInput`, `HedgeStakeResult`
  Pydantic v2 shapes.
- `commission_lookup`, `resolve_commission` (the v2-style
  dynamic lookup per math review §1).
- `compute_hedge_stake` (the four formulas — cash and free-bet
  × Construction A and B, per math review §2 / §3).
- `breakeven_betfair_price` helper (math review §2.5).

**Dependencies:** stdlib `decimal` / `enum`, Pydantic v2,
`models.py` enums. No imports from `pricing.py` or other
workflow modules.

**Implementation choices:**
- All math runs on `Decimal` internally (float inputs converted
  via `Decimal(str(value))` to avoid float-precision drift).
  Display rounding happens at the end via
  `quantize(0.01, ROUND_HALF_UP)`.
- Liability and Net are computed from the **unrounded** s_bf
  raw value, then the result is rounded — this matches the math
  review §6 worked examples (which carry the unrounded value
  through downstream cents). Originally I had Liability
  computing from the rounded s_bf, which produced $104.31 vs
  the math review's $104.30 in §6.1 and $233.02 vs $233.01 in
  §6.2. Switching to unrounded raw value lands all four §6.1 +
  §6.2 worked examples cent-accurate.
- Construction-specific denominators: A uses `(P_bf − c)`; B
  uses `[(P_bf − 1) × (1 − c) + 1]`. Both raise `StakingError`
  if the denominator is non-positive (math review §7.10
  "theoretically unreachable on real Betfair markets" but
  surfaced defensively).
- Commission table is a Python literal in-module —
  config-driven storage and tuning is a separate forward
  concern; the table ships locked v1 with the math review
  §1 / §6.1 values (Queensland 8%, Ipswich 4%, family
  fallbacks).
- The `_classify_sport` helper maps Betfair-style sport
  strings ("Horse Racing", "Australian Rules", etc.) to the
  internal `_SportFamily` enum; unknown sports fall back to
  `OTHER_SPORT` (6%) rather than raising.

### §2.5 — `pricing.py` (194 lines)

**Path:** `workflows/bet_entry/v1/pricing.py`.

**Public surface:**
- `PricingError` exception.
- `BonusFlavour` enum (`FREE_BET_BONUS` / `CASH_BONUS`).
- `DEFAULT_FREE_BET_CONVERSION_RATE = 0.65` (per math review
  §6.2 / brief §3.3).
- `EffectiveOddsInput`, `EffectiveOddsResult` Pydantic v2
  shapes.
- `synthesise_effective_odds`, `optimal_promo_stake` functions.

**Dependencies:** stdlib `decimal` / `enum`, Pydantic v2. No
imports from `staking.py` or other workflow modules.

**Implementation choices:**
- Cash and free-bet flavours are discriminated by the
  `BonusFlavour` enum on the input rather than by separate
  functions. The model_validator catches misconfigurations
  (e.g. FREE_BET_BONUS without conversion rate) at construction
  time per brief §5.6 (programmer errors raise; operational
  errors flow through result types).
- `optimal_promo_stake` rounds to nearest $5 per math review
  §5.3 / §5.4; configurable rounding step (test exercised at
  $5 default).

### §2.6 — `orchestrator.py` (1240 lines)

**Path:** `workflows/bet_entry/v1/orchestrator.py`.

**Public surface:**
- `BetEntryOrchestrator` class with three entry points:
  `pre_flight_check`, `place_hedge`, `log_soft_book_bet` per
  brief §2.3.
- `BetfairAdapter` Protocol — abstracts the Betfair surface
  W4 needs.
- `MarketStatusSnapshot`, `FundsSnapshot`, `OrderStateSnapshot`,
  `PlacementOutcome` — adapter-side data shapes.
- `HedgeEntryRequest`, `SoftBookLogRequest` — orchestrator
  input shapes.
- `TriggerBScheduler` Protocol; `ManualTriggerBScheduler`
  (test); `ThreadingTriggerBScheduler` (reference).

**Dependencies:** stdlib `logging` / `threading` / `time` /
`uuid` / `zoneinfo` / `decimal` / `datetime`, Pydantic v2,
`models.py`, `record_builder.py`, `storage.py`. Note: the
production `BetfairAdapter` implementation that wraps
`clients.betfair_client.v1` lives in v3-build-proper composition
(outside W4 v1's module set per brief §12.4 — see Open
Questions §7.3).

**Implementation choices:**
- **`BetfairAdapter` Protocol abstraction**: instead of
  importing `clients.betfair_client.v1` directly, the
  orchestrator depends on a small Protocol that exposes only
  what W4 needs (`get_market_status`, `get_account_funds`,
  `place_hedge_bet`, `get_order_state`). This keeps:
  - The orchestrator unit-testable with a deterministic mock
    (per brief §10.2).
  - Contract gaps (no `getAccountFunds`, no `marketCatalogue`
    for runner names — see Findings) visible at exactly one
    boundary.
  - The "real-Betfair adapter" deferrable to v3 build proper
    composition — outside W4 v1's locked module set (brief
    §12.2).
- **Trigger B execution model** (brief §6.4 names asyncio):
  `TriggerBScheduler` Protocol with two implementations
  (`ManualTriggerBScheduler` for tests, `ThreadingTriggerBScheduler`
  for unblocked v1 use). v3 build proper composition can swap
  either for an asyncio-driven version. Tests bypass the 5s
  wait by calling `scheduler.flush()`.
- **Retry policy encoded as constants**:
  `DEFAULT_BACKOFF_SCHEDULE_MS = (50, 200, 500)` and
  `DEFAULT_TRIGGER_B_DELAY_SECONDS = 5.0`. Test orchestrators
  override `sleep_fn=lambda _: None` for zero-wall-clock test
  runs.
- **Result-type pattern throughout**: only `Exception` raises
  are programmer errors (invalid Pydantic input, schema
  violations). All operational errors — Betfair rejection,
  storage failure, schema-build issue post-placement — flow
  through `HedgePlacementResult.error_context` /
  `SoftBookLogResult.error_context` per brief §5.6.
- **Path (a) note**: in production, `staking.py` is called
  upstream of `place_hedge` (the modal computes the proposed
  stake before the operator confirms). The orchestrator's
  guard against zero / negative stakes is preserved as a
  defence; a real `StakingError` lands at the modal layer per
  brief §1.4 / §3.7. See §7 Open Questions.

## §3 — Tests built

Total: **75 W4 tests** plus 287 across the full v3 suite (W4
adds 75 to the 212 already shipped).

**Pure-module unit tests:**

| Module | Tests | Highlights |
|---|---|---|
| `test_staking.py` | 20 | All math review §6.1 / §6.2 worked examples land cent-accurate; §2.7 sanity 1/2/3 + §3.7 Construction B sanity; §6.1 Queensland-vs-Ipswich contrast; §2.5 break-even reference; commission lookup precedence; invalid input handling. |
| `test_pricing.py` | 10 | Free-bet vs cash flavour synthesis; default 65% rate; operator-overridable rate; Pydantic validator rejects FREE_BET_BONUS without rate; rate out-of-range rejected; optimal stake helper rounds to $5. |
| `test_record_builder.py` | 13 | DR-032 schema validation; strategy_tag closed enum + nullable; Strategy 3 raise-path; free-bet invariants; cycle-id generation + inheritance; Set B six fields population; matched > requested raise-path. |
| `test_storage.py` | 9 | In-memory + SQLite roundtrip; Decimal preservation; NULL strategy_tag schema handling; duplicate-write integrity; unknown-bet update returns non-success result rather than raise. |

**Mocked-API orchestrator tests (`test_orchestrator.py`,
23 tests):**

Brief §10.2 minimum case set, all exercised:

| Case | Test | Coverage |
|---|---|---|
| Happy path | `test_happy_path_full_match`, `test_happy_path_then_log_soft_book` | Trigger A + Trigger B `final_full` + soft-book log |
| Path (a) | `test_path_a_invalid_stake_zero` | Pydantic validator rejection upstream |
| Path (b) retry-safe → succeeds | `test_path_b_retry_safe_then_succeeds` | 1 retry-safe failure, attempt 2 succeeds |
| Path (b) retries exhausted | `test_path_b_retry_safe_exhausted` | 3 retry-safe → escalated terminal |
| Path (b) terminal | `test_path_b_terminal_error_no_retry`, `test_path_b_market_suspended_terminal` | Insufficient funds + market suspended |
| Path (c) | `test_path_c_storage_write_fails_persistently` | 3 forced storage failures; placement detail preserved |
| Path (d) | `test_path_d_soft_book_log_fails` | 3 forced storage failures on soft-book log |
| Trigger B `final_partial` | `test_trigger_b_final_partial` | Half-matched at placement; remainder lapsed |
| Trigger B `provisional_pending` | `test_trigger_b_provisional_pending` | Half-matched; rest still in unmatched |
| Trigger B fail twice | `test_trigger_b_read_fails_twice_stays_provisional` | Single retry exhausted; record stays PROVISIONAL |
| Trigger B `failed` | `test_trigger_b_failed_status_when_no_match` | Bet vanished without matching |
| Strategy tag plumb-through | `test_strategy_tag_plumbed_to_betfair_call` | `strategy_tag.value` reaches placement call |
| `customer_order_ref` round-trip | `test_customer_order_ref_round_trip`, `..._auto_generated` | Round-trip on caller-supplied; auto-gen otherwise |
| Cycle linkage | `test_cycle_id_inherits_when_supplied`, `..._generated_when_none` | Brief §3.6 generation + inheritance |
| Pre-flight | 5 tests | OPEN/SUSPENDED/CLOSED + funds OK/insufficient/unavailable |

**Mock shapes:** `MockBetfairAdapter` records every call and
exposes `queue_placement(...)` / `queue_order_state(...)` /
`set_market_status(...)` / `set_account_funds(...)` to drive
scenarios deterministically. No real Betfair API calls.

## §4 — Test results

```
============================= test session starts ==============================
collected 287 items

tests/                                       212 passed
workflows/bet_entry/v1/tests/                 75 passed

============================= 287 passed in 0.41s ==============================
```

W4 sub-totals: 75/75 passing. No skips, no failures, no xfails.

## §5 — Linting + import-linter results

**`ruff check .`**: All checks passed (project-wide).

**`lint-imports`**: 5 contracts kept, 0 broken. Per the
DR-030 contracts:

```
DR-030 layered architecture                       KEPT
domain imports nothing in the project             KEPT
store imports nothing in the project              KEPT
contracts is a leaf package                       KEPT
workflows cannot import workflows                 KEPT
```

W4's `workflows/bet_entry/v1/` imports only from stdlib,
Pydantic v2, and W4's own modules. No imports from
`workflows.burst_review` (forbidden by the
`workflows-cannot-import-workflows` contract); no imports past
`clients/` boundary (the orchestrator uses an in-package
`BetfairAdapter` Protocol, not a direct `clients.betfair_client`
import — see §7.3 Open Question and Findings).

Pure modules (`staking.py`, `pricing.py`, `record_builder.py`)
do not import from `orchestrator.py` or each other.

## §6 — Deviations from brief

**Order deviations are normal per brief §9.3; scope deviations
are flagged.** Below: zero scope deviations, four named
order/structural deviations.

### §6.1 — Module location is `workflows/bet_entry/v1/`, not `workflow/...`

The brief says `workflow/bet_entry/v1/` (singular) at §1.1 /
§2.1 / §8.1 / §9.4 etc. The actual v3 repo (per DR-030
locked-stance + the on-disk layout) uses `workflows/` (plural).
Code built at `workflows/bet_entry/v1/` to match the existing
repo, the `import-linter` configuration that already names
`workflows.bet_entry`, and the empty `workflows/bet_entry/`
package marker that already exists.

This is a brief-text deviation; not a scope or behaviour
deviation. The brief should be amended at next pass to read
`workflows/`.

### §6.2 — Storage stub built right after `models.py`

Brief §9.1 names the build order:

1. `models.py`
2. Storage-interface stub
3. `record_builder.py`
4. `staking.py` + `pricing.py` (parallel)
5. `orchestrator.py`
6. Tests alongside each module.

Code's actual build order:

1. `models.py`
2. `storage.py` (stub)
3. `staking.py`
4. `pricing.py`
5. `record_builder.py`
6. `orchestrator.py`
7. Tests written after each module group (one or two at a
   time, not strictly alongside).

Brief §9.3 lists "Building `staking.py` before
`record_builder.py`" as a permitted deviation. The reason here:
the math review §6 worked examples are concrete enough that
implementing them up-front locked the staking interface
cleanly. `record_builder.py` followed naturally from the
shape `staking.py` + `pricing.py` settled.

### §6.3 — `BetLeg` field names follow DR-032, not brief §3.5

Brief §3.5 lists Set B as six fields:

```
runner_name, event_name, venue_name, market_name,
scheduled_start_time, betfair_implied_probability
```

DR-032 §2 (the schema substrate the brief says is
load-bearing) lists six different fields:

```
betfair_event_name, betfair_market_name, betfair_selection_name,
betfair_event_venue, betfair_event_sport, betfair_event_start_time
```

with `betfair_implied_probability_at_log_time` as an optional
seventh per DR-032 §2's last bullet ("Optionally: the leg's
individual Betfair-implied probability at logging time").

Code followed DR-032 (the locked schema contract per brief
§12.3 + §3.8) plus the optional implied-probability field.
Brief §3.5 should be reconciled at next pass.

This affects test field names but not the schema's substantive
behaviour — Set B is still six immutable logging-time
snapshots, populated from a `marketCatalogue`-style source at
modal open, never refreshed.

### §6.4 — Skipped a unit-test-shape note

Brief §9.3 lists "Skipping mocked-orchestrator tests if
`orchestrator.py`'s composition is straightforward enough" as a
permitted deviation. Code did **not** take this option — the
`test_orchestrator.py` 23-case mocked-API set is shipped per
brief §10.2 minimum case list. (Mentioned for completeness; not
a deviation, just a non-skip.)

## §7 — Open questions

### §7.1 — Path-(a) routing across the modal/orchestrator boundary

Brief §5.2 names path (a) as "`place_hedge` calls `staking.py`
(or `pricing.py`...) and the pure-module function returns an
error result instead of a stake". In v3 architecture as built,
`staking.py` is called **upstream** of `place_hedge` — the
modal computes the proposed stake before the operator confirms,
and `place_hedge` accepts `(proposed_stake, proposed_price)` as
inputs. A `StakingError` would surface in the modal (W7
territory) before reaching the orchestrator at all.

The `_path_a_result` envelope is preserved in `orchestrator.py`
so the framework holds, but the on-call site for path-(a) is
W7's modal logic rather than the orchestrator. Triage:
clarify whether path (a) belongs primarily at the W7 modal
layer (Code's interpretation) or at the orchestrator boundary
(brief's literal reading).

### §7.2 — `provisional_pending` follow-up at +30s?

Brief §6.5 says: "**Final fallback if reconciliation can't
establish final state:** if the order's final state is
unresolvable within a reasonable window (e.g. 30 seconds —
beyond Trigger B's execution), the bet record stays
`provisional_pending`. Operator-side review is the terminal
recovery path."

Code's implementation has Trigger B firing once at +5s and
retrying the read once at the same call (per §6.4 single
retry); after that it stops. There's no scheduled +30s
follow-up. Triage: is the 30s reference a passing comment
(operator-side review window) or a second scheduled trigger
W4 should run? Lit reading suggests the former — Code's
implementation reflects that — but the brief's wording leaves
room for the latter.

### §7.3 — Real `BetfairAdapter` implementation lives where?

The orchestrator depends on a `BetfairAdapter` Protocol
defined inside `workflows/bet_entry/v1/orchestrator.py`. A real
implementation that wraps `clients.betfair_client.v1` (the
W3-shipped surface) needs to live somewhere; brief §12.4
forbids edits outside `workflows/bet_entry/v1/`.

Code's interpretation: the real adapter is W4 module set
territory and lives **inside** `workflows/bet_entry/v1/` (a
support file alongside the protocol). Code did not ship this
adapter — it wasn't named in the brief's deliverable list,
and integration tests against `clients.betfair_client.v1`'s
surface would push beyond the mocked-API scope per brief
§10.2 / §12.8.

Alternative: the adapter lives at the v3 composition root
(outside `workflows/bet_entry/v1/`) — operator-Claude triage
locks the location.

### §7.4 — Streaming-disconnect-blocks-writes interaction with retry

Per `betfair_client_contract.md` v1.0 §13, `place_bet` returns
`BETFAIR_STREAMING_DISCONNECTED` when the streaming connection
is not `SUBSCRIBED`. Brief §5.3 lists "service busy" /
"network transient" / etc. as retry-safe; doesn't name
streaming-disconnect explicitly.

Code's orchestrator treats `streaming_blocked` outcomes as
retry-safe — three attempts, 50/200/500ms backoff. If the
streaming connection is sustainedly disconnected, this burns
~750ms before escalating to terminal. That's tolerable but
arguably wasteful — the retry won't help if the streaming
connection isn't reconnecting in the meantime.

Triage: should `streaming_blocked` route directly to a `wait
for reconnect, do not retry` UX flow (per the contract §13
"resumes on reconnect" framing)? Code preserved retry
semantics for consistency; behaviour can be changed without
a brief amendment.

### §7.5 — `customer_strategy_ref` vs `strategy_tag`

`betfair_client_contract.md` v1.1 distinguishes two strings:

- `customer_strategy_ref` — Betfair payload, forwarded to
  exchange ("1"–"4" per the contract example).
- `strategy_tag` — v3-internal, never sent to Betfair, lands
  on audit log only (the four enum string values per
  contract §12.1 example: `safety_net`, `price_booster`,
  `sgm_correlated`, `synthetic_each_way`).

Brief §3.2 names `strategy_tag` only. Code's `HedgeEntryRequest`
exposes both fields — `strategy_tag` (W4-side enum) and
`customer_strategy_ref` (Betfair payload, optional). The
orchestrator passes both through to `place_hedge_bet`.

Triage: should W7 default `customer_strategy_ref` to a numeric
"1"–"4" mapping (Betfair-side), or leave it empty? The
contract example's "2" maps to `price_booster`. Code defaults
both to None on the request; W7 can populate per its own
logic.

### §7.6 — Soft-book combined price for single-leg bets

Brief §3.4 / §3.7 has `soft_book_combined_price` on the bet
record. DR-032 §2 names it as a bet-record field for
combined-price SGMs. For single-leg soft-book bets, what's the
value?

Code's implementation: optional `float | None`. For single-leg
hedge bets, the orchestrator passes whatever the request
supplied (typically the hedge's own price isn't relevant; the
soft-book leg's odds drive the field). Triage: should
single-leg bets always store the soft-book leg's back odds
here, even though it duplicates the leg-level `matched_price`?

## §8 — Findings

Operational observations and contract-shape items that aren't
deviations or open questions but matter for next-stage work.

### §8.1 — Contract gap: no `getAccountFunds` exposed in `betfair_client` v1.0

`betfair_client_contract.md` v1.0 §15.4 explicitly excludes
account management. Brief §4.3 specifies a fundedness check via
Betfair `getAccountFunds`. Code's orchestrator surfaces a
`WARN funds_check_unavailable` flag rather than a
`BLOCK INSUFFICIENT_FUNDS` flag when `BetfairAdapter.get_account_funds()`
returns None — preserving brief §4.3's "API failure handling"
discipline ("don't block the operator on a check that's itself
failing"). Per brief §4.6 ("pre-flight is advisory, not
gating"), the operator can still proceed and the exchange will
reject at `placeOrders` time per §5.3.

**Implication for W3 / W6 / next contract review:** if W4 is to
ship with a working fundedness check, either the contract needs
a backward-compatible addition (`get_account_funds`) — likely
lands as v1.2 per the §14.4 "new endpoints alongside existing
ones" mechanism — or W4 v1 ships permanently with the
`WARN funds_check_unavailable` shape.

### §8.2 — Contract gap: no `marketCatalogue` exposed for runner / event names

DR-032 §4 / brief §3.5 / §A.10 specify Set B six fields per leg
populated from Betfair `marketCatalogue` — `runner.runnerName`,
`event.name`, `event.venue`, etc. The v1.0 contract's
`MarketPrices` (§9.1) and `RunnerPrices` shapes do not expose
these; `RunnerPrices` has `selection_id` and a runner status
but no `runner_name`. Sports markets get a `SportsMarketVariant`
shape, but racing markets need an analogue.

Code's `LegSnapshot` accepts the six Set B fields as opaque
inputs — the orchestrator's `BetfairAdapter` is responsible
for resolving them. The mock adapter pre-populates them.

**Implication:** the v3 production wiring needs a
`get_market_catalogue(market_id) -> MarketCatalogue` surface
on the contract. Likely also a v1.2 backward-compatible
addition. The same surface is needed by W4.1 (soft-book entry)
and W7 (modal pre-population), so it's not unique to W4.

### §8.3 — Math review §6 worked examples land cent-accurate (after liability fix)

First-pass implementation rounded `s_bf` to two decimals and
then computed liability from the rounded value, producing
$104.31 vs $104.30 in §6.1 and $233.02 vs $233.01 in §6.2. The
math review's worked examples implicitly carry the unrounded
`s_bf` through to liability and Net computation, then round
once at display.

Switching `staking.py` to compute liability and Net from the
unrounded raw `s_bf` value lands all four §6.1 + §6.2 worked
examples cent-accurate. The display rounding still happens at
the end (the operator-facing values are two-decimal stake plus
two-decimal liability plus two-decimal Net).

**Implication:** W4 v1's stake / liability / Net values will
match the math review's worked examples exactly. The math
review itself can be updated at next pass to show the
arithmetic step explicitly.

### §8.4 — `place_bet` not `placeOrders`

Brief §5.3 / §6 / §10.2 says `placeOrders`; the contract names
the Betfair-side surface as `place_bet` (§11.1). They map to
the same operation; no functional impact. Brief and contract
should align on naming at next pass.

### §8.5 — `priceLimit` mechanism is implicit at v1.0 contract

Math review §4.5 specifies that Betfair's `priceLimit` parameter
prevents matching at worse-than-requested prices. The v1.0
`place_bet` signature has `price` as the limit price (per the
implicit limit-order semantics of any price submitted to
`placeOrders`); there is no separate `priceLimit` parameter.

Code's `BetfairAdapter.place_hedge_bet` exposes only `price` —
the `priceLimit` semantics are inherited from the contract's
limit-order behaviour. **No action needed.** Flagged because
the brief leans on the math review §4.5 framing; the contract
satisfies it implicitly.

### §8.6 — `OrderPosition` reconciliation by `bet_id`

Brief §6.3 names `listCurrentOrders` as the polling-fallback
read; the v1.0 contract exposes `streaming_client.order_cache_snapshot(market_id, selection_id)`
which returns an `OrderPosition` containing `unmatched: list[UnmatchedOrder]`
keyed by `bet_id`. Matched levels are aggregated by price
(`matched_backs` / `matched_lays`) without per-bet
attribution.

Code's reconciliation logic: search `unmatched` for our
`bet_id`. If found with `size_remaining > 0` → `provisional_pending`;
if found with `size_remaining == 0` → `final_full`; if not
found → infer from placement-time data (assume final_full
unless the placement reported zero matched, in which case
`failed`).

**Implication for W6:** broader sync reconciliation may need
to disambiguate "fully matched and aged out of unmatched
cache" from "cancelled or lapsed" using a separate Betfair
surface (e.g. `listClearedOrders`, currently out of W4 scope).

### §8.7 — Streaming-disconnect interaction with placement is automatic

Per contract §13, `place_bet` itself blocks placement when the
streaming connection isn't `SUBSCRIBED`. Code's adapter
abstraction routes this through `PlacementOutcome.outcome=streaming_blocked`,
which the orchestrator treats as retry-safe. v3 build proper
composition will likely surface a "streaming reconnecting"
banner from `streaming_status()` independently — W4 can leave
this UX to W7.

### §8.8 — Strategy 3 raise visible at runtime

`BetRecordBuilderError` raises if `strategy_tag = SGM_CORRELATED`
is supplied. The enum value exists in `models.py` so the schema
doesn't change when W4.1 / W7 ship SGM mechanics, but any
caller passing it today gets a clear error message. **Brief
§3.2 satisfied.**

### §8.9 — Backoff sleep is synchronous via `time.sleep`

Brief §5.3 / §5.6 says retries run synchronously inside the
entry-point function; modal blocks during retry. Code uses
`time.sleep` (injectable as `sleep_fn` for tests). When the
v3 production wiring moves to FastAPI's async context, this
becomes `asyncio.sleep` — the orchestrator's `sleep_fn` hook
makes that swap easy at the composition root.

## §9 — Self-assessment

### §9.1 — Did the build fit within the session budget?

Yes, comfortably. Wall-clock ~3h20m. Pre-reads consumed ~45
minutes (math review + DR-032 + contract + the four DRs);
build consumed ~1h45m; tests + lint + this report consumed
~50 minutes.

The session budget had room — Code could have shipped a real
`BetfairAdapter` adapter wrapping `clients.betfair_client.v1`
(see §7.3) but held off because the brief §10.2 mocked-API
test set is the locked deliverable, and a real adapter
without integration tests against it would be untested code.

### §9.2 — Where am I less confident?

**(a) Trigger B reconciliation logic when our `bet_id` is
not in `unmatched` and `matched_size == 0`** — I treat this as
`failed` per brief §6.5's table ("Order cancelled / lapsed
entirely → failed (rare)"). The contract's order-cache shape
doesn't surface a definitive "this bet was cancelled" signal;
my interpretation infers from absence + zero matched. If a
race condition produces "fully matched and the cache rolled
over" before our read, we'd misclassify as `failed`. Brief
§6.5 acknowledges the rarity; I've left the simpler logic in
place but the operator-side acceptance run in §10.3 should
watch this case.

**(b) `customer_order_ref` round-trip discipline**: per
contract §11.1 / §2.4 §9.8, retried placements should reuse
the same `customer_order_ref` so Betfair recognises them as
the same intended placement. Code's `_place_with_retry` uses
the same `customer_order_ref` across all 3 attempts (good).
But the duplicate-submit guard (`betfair_bet_placement_in_progress`)
is **also** keyed by `customerRef` — if the first attempt's
network-transient failure happened *after* Betfair received
the placement, the second attempt would either succeed-as-no-op
(idempotency) or be rejected with `bet_placement_in_progress`.
The current orchestrator treats this as retry-safe and would
retry again. Triage might want to mark `bet_placement_in_progress`
as terminal-with-special-message ("placement already in
flight").

**(c) Async sleep at production composition**: see Finding
§8.9. The injection point is clean but I haven't proven the
asyncio path under FastAPI; it should work but is unexercised.

### §9.3 — What should the operator look at first when reviewing?

In priority order:

1. **`staking.py` arithmetic against the math review §6
   worked examples** — Code's pytest cases match the math
   review cent-by-cent, but operator-side acceptance with a
   real bet at low stake against the operator's actual
   commission would confirm the lookup. The brief §6.1 /
   §6.2 numbers are reproducible.

2. **`record_builder.py` field names against DR-032** —
   Set B field names follow DR-032 (not brief §3.5). Operator
   should confirm this is the intended schema before W6
   inherits the same shape.

3. **`orchestrator.py`'s `BetfairAdapter` Protocol** — the
   abstraction boundary. The Protocol exposes 4 methods; the
   real adapter wraps `clients.betfair_client.v1`. Operator
   should confirm:
   - The Protocol covers all the Betfair surfaces W4 needs.
   - The contract gaps named in Findings §8.1 / §8.2 are
     accepted as v1.2 follow-ups (or remediated some other
     way).
   - The Protocol's location (inside `workflows/bet_entry/v1/`
     or moved to v3 composition root) is right.

4. **Path (a) routing** — see §7.1 Open Question. The
   orchestrator's path-(a) envelope is preserved but the
   on-call site is W7's modal logic, not the orchestrator
   boundary the brief literally names. This affects W7's
   error-handling design, not W4's behaviour.

5. **Trigger B `provisional_pending` 30-second follow-up
   question** — see §7.2. Lit reading on the brief suggests
   no scheduled +30s follow-up; if operator-Claude wants one,
   it's a small orchestrator addition.

### §9.4 — Length-range overrun?

This report runs ~810 lines, over the brief §11.2 range of
400–700 lines (~16% overrun). Per brief §11.4, naming the
sections that drove the overrun:

- **§2 Modules built** (~200 lines) — the per-module
  implementation-choices write-ups are substantive because
  this is first-of-workstream work and the choices land
  contracts that W6 / W7 inherit. I judged this content
  worth the extra space.
- **§3 Tests built** (~70 lines) — the case-by-case mocked-
  API table is detailed because brief §10.2 names a minimum
  case list and the report is the artefact that confirms each
  case is exercised.
- **§7 Open questions** (~110 lines) — six substantive
  questions, all needing operator-Claude triage answers
  before next-stage work routes cleanly.
- **§8 Findings** (~150 lines) — nine findings, dominated by
  contract-shape items (no `getAccountFunds`, no
  `marketCatalogue`) that push toward a `betfair_client` v1.2
  surface. Material for the next operator-Claude session.

I have not padded sections; the overrun reflects real
first-of-workstream content (deviations, contract-gap
findings, scheduling-protocol open questions). Brief §11.4
permits overrun "when the work warrants it"; this overrun is
named here per the discipline.

### §9.5 — Acceptance work the operator runs next

Brief §10.3 / §13.2 sequence:

1. Operator-Claude triage session reads this report; works
   through Open Questions and Findings.
2. Operator runs a small real-money test bet through the full
   workflow (Strategy 1 or Strategy 2 cycle, low stake). Two
   gaps to keep in mind: (a) the funds-check is a permanent
   `WARN` until contract surfaces add `getAccountFunds`; (b)
   Set B population needs a `get_market_catalogue` adapter
   method that's currently mock-only.

3. Findings from operator acceptance route through a small
   targeted Code brief if material.

---

**End of report.** All 287 v3 + W4 tests pass; 5/5 import-linter
contracts kept; ruff clean across the project. W4 v1 module
set is locked, schema follows DR-032, the four-error-path
framework + Trigger A/B reconciliation per brief §5/§6 land in
`orchestrator.py` exactly as specified.
