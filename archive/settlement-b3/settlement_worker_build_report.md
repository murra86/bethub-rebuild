# Settlement-worker BUILD report

**Brief:** `settlement_worker_build_brief.md` (LOCKED, S216) + operator go-ahead
`settlement_worker_code_goahead.md` (S217) — **§9 edit-surface pick = Option (1),
live-effective**.
**Built:** Session 217 (2026-07-02 ACST, DR-021 Adelaide throughout).
**Codebase anchor:** bethub-v3 @ `e2638fac2c659783448bece9b1810294512068bf`
(`e2638fa`) — **HEAD unchanged** from the brief/read-back anchor; confirmed at
session start (`git rev-parse HEAD`). All §5 file/line anchors resolved as the
read-back logged (the six cosmetic drifts noted there hold; none affected the
build).
**Bet-safety / ship state:** worker lands **wired but OFF by default**. No live or
staging Betfair was touched; every test is fixture / in-memory / `tmp_path`
SQLite. Tree left **dirty** per the rebuild convention — no
`commit`/`stash`/`checkout`/`reset`/`add` run. **The flag was NOT flipped** —
live-enable is the operator's call.

> One doc-location note for the triage session: the code lives in
> `~/Desktop/Projects/bethub-v3/`; these briefs/reports live in
> `~/Desktop/Projects/bethub-rebuild/`. The anchor `e2638fa` is bethub-v3's HEAD
> (bethub-rebuild has its own unrelated git history).

## Files touched (all within §9 surfaces)

Production (non-test):

| File | Change |
|---|---|
| `clients/betfair_client/v1/settlement.py` | `RunnerSettlement` gains `adjustment_factor` + `adjustment_applied` (:66-67); new `_parse_runner` lifts + derives them (:82-106); `_parse_settlement` uses it (:109). §9 named surface. |
| `clients/betfair_client/v1/_translation.py` | **The one authorised additive line** — `"adjustment_factor": r.get("adjustmentFactor")` in `_translate_market_settlement` (:573). Named exactly per go-ahead Option (1). |
| `workflows/bet_entry/v1/settlement.py` | Guard 1: new reason code `provisional_dead_heat_or_reduction` (:134), trigger `DEAD_HEAT_OR_REDUCTION` (:359), `REDUCTION_MATERIALITY_THRESHOLD_PCT=2.5` (:146), `RemovedRunnerFactor`/`RemovedRunnerVerificationRecord`/`_WinnerGuardOutcome` (:158/:176/:210), `_is_place_market` (:422) + `_evaluate_winner_guard` (:451); WINNER branch gated in **both** resolvers (:689 PENDING, :918 PROVISIONAL); §5.1b `_emit_verification_record` (:1157) + pass emission/counters. |
| `workflows/bet_entry/v1/betfair_adapter.py` | `RealSettlementReader` (:333) — the live `SettlementReader`. |
| `workflows/bet_entry/v1/post_settlement_void.py` | **NEW** — Guard 3 read-only detector. |
| `workflows/bet_entry/v1/__init__.py` | Refinement B exports: reader + worker entry points + Guard 3 detector. |
| `workflows/promos/v1/credit_gap.py` | **NEW** — Guard 2 read-only detector. |
| `ui/api/config.py` | `settlement_worker: bool = False` (:70) → binds `BETHUB_SETTLEMENT_WORKER`. |
| `ui/api/dependencies/composition.py` | `_settlement_reader()` factory (:550) + `app.state.get_bet_storage`/`get_settlement_reader` bring-up handles (:588-589). |
| `ui/api/main.py` | lifespan starts/stops the worker gated on the safe-by-default check; `_bring_up_settlement_worker` (:93); fail-safe try/except. |
| `ui/api/routers/promos.py` | read-only `GET /v1/promos/credit-gaps` (:307). |

Tests: `tests/clients/betfair_client/v1/test_settlement.py` (+3), and new files
`test_settlement_guard.py` (15), `test_post_settlement_void.py` (7),
`test_credit_gap.py` (6), `test_promos_credit_gaps.py` (2),
`test_settlement_worker.py` (12); plus 3 pre-existing tests in
`tests/workflows/bet_entry/v1/test_settlement.py` **updated** (see 5.1
deviations). No file outside §9 was edited (`store/repositories/bets.py`,
`domain/bets.py`, `bet_store_adapter.py` untouched).

**The `_translation.py` line as landed** (`_translate_market_settlement`, :573,
inside the per-runner dict built alongside `removalDate`/`bsp`):

```python
"adjustment_factor": r.get("adjustmentFactor"),
```

That is the **only** edit outside §9's named `settlement.py` surface, exactly as
Option (1) authorised. No `marketType` (or any second field) was lifted from the
raw book — see the market-type note in 5.1.

## Test results

- **Baseline before starting:** the five brief-named files = **117 passed**
  (`uv run pytest` — matches report 5B); full suite **1202 passed, 1 xfailed**.
- **After the build:** full suite **1247 passed, 1 xfailed, 0 failed**
  (`uv run pytest`). **Net new = 45 tests** — `test_settlement_guard.py` 15,
  `test_post_settlement_void.py` 7, `test_credit_gap.py` 6,
  `test_promos_credit_gaps.py` 2, `test_settlement_worker.py` 12, and 3 added to
  `tests/clients/betfair_client/v1/test_settlement.py` — plus 3 pre-existing tests
  updated. No regressions.

---

## 5.0 — Wire the auto-settlement worker (the core)

**What was built.** The app's **first live periodic worker** (report 5A: there
was no live periodic-worker pattern — only the streaming socket), established
consistent with the streaming lifespan shape.

1. **Live settlement reader** — `RealSettlementReader` (`betfair_adapter.py:333`)
   satisfies the `SettlementReader` Protocol (`settlement.py:96-114`), wrapping
   the betfair-client `market_settlement` (§9.2) and translating
   `ReadEnvelope[MarketSettlement]` → `ReadOutcome[MarketSettlement]` — the same
   translation `RealBetfairAdapter.get_market_settlement` performs
   (`betfair_adapter.py:305-324`). It is **deliberately distinct** from
   `RealBetfairAdapter`: settlement reads use only the REST client and never
   place an order, so it carries **no** streaming precondition (RealBetfairAdapter
   requires a streaming-equipped client for the §13.1 placement interlock; forcing
   that on a settlement reader would wrongly refuse to build on a REST-only
   client). A `TYPE_CHECKING` structural-conformance assertion pins it to the
   Protocol.

2. **Composed + started.** `composition.py` adds a cached `_settlement_reader()`
   built from the same `_betfair_client()` factory (`:550`), and exposes
   `app.state.get_bet_storage` / `app.state.get_settlement_reader` bring-up
   handles (`:588-589`) — factories, not built objects, so app import stays
   side-effect-free (mirrors the streaming `get_streaming_client` handoff). The
   driver lives in a dedicated `ui/api/settlement_worker.py`:
   `settlement_worker_cycle` runs **both** `run_settlement_pass` and
   `run_provisional_resolution_pass`; `start_settlement_worker` launches an
   `asyncio` background task (`_settlement_worker_loop`) that, each
   `DEFAULT_SETTLEMENT_INTERVAL_SECONDS` (60s), runs the cycle **off the event
   loop** via `asyncio.to_thread` (the passes are blocking SQLite+REST;
   `SQLiteBetRecordStorage` opens a fresh connection per call under a lock, so
   cross-thread use is safe). `main.py`'s lifespan starts it and cancel-and-awaits
   it on teardown, mirroring the streaming bring-up/teardown.
   - **Scheduler mechanism (Cat-5 call):** `asyncio` background task, per the
     brief's preference and to match the streaming lifespan shape — **not** the
     reference `ThreadingSettlementScheduler`, which stays (with
     `ManualSettlementScheduler`) as the test/reference impl.
   - **Refinement B exports** landed in `workflows/bet_entry/v1/__init__.py`
     (`RealSettlementReader`, `run_settlement_pass`,
     `run_provisional_resolution_pass`, `DEFAULT_SETTLEMENT_INTERVAL_SECONDS`,
     the scheduler/reader types, and the Guard 3 detector). The colliding
     `DEFAULT_AGE_THRESHOLD_SECONDS` (settlement vs the already-exported
     reconciliation one) was deliberately **not** re-exported to avoid shadowing.

3. **SAFE-BY-DEFAULT opt-in (load-bearing).** `should_start_settlement_worker`
   returns True **only** when `betfair_mode == "live"` **AND**
   `settlement_worker` is on — default **OFF**
   (`config.py:70` → `BETHUB_SETTLEMENT_WORKER`). Any error starting the worker is
   logged and **never aborts app startup** (lifespan try/except, mirroring the
   streaming fail-safe `main.py:98-105`). In mock mode or with the flag off the
   worker never runs and the manual provisional router behaves exactly as before.

4. **Idempotency + bounded sweep** — unchanged. `run_settlement_pass` stays
   idempotent + bounded by `max_results=100` + the age cutoff; the wiring passes
   those through and does not double-schedule.

**Tests (§7 5.0):** `test_settlement_worker.py` (12) —
(c) `RealSettlementReader` translates a fresh envelope → `ReadOk` and a 404 →
`ReadUnavailable(reason="betfair_market_not_found")`; (a) the gate returns False
for `{mock,*}` and `{live,flag-off}`, and the lifespan **does not** invoke the
bring-up in default mock mode; (b) the gate returns True only for `{live,on}`, one
`settlement_worker_cycle` settles both a PENDING and a PROVISIONAL winner (proving
both passes run), and the periodic loop fires the cycle repeatedly on a short
interval; (d) a bring-up that raises does **not** abort startup (`/api/health`
still 200), and a failing cycle does not kill the loop.

---

## 5.1 — Guard 1: dead-heat / removed-runner-reduction → detect and park

**Which arm shipped: Option C (precise), LIVE-EFFECTIVE — not the Option-B
fallback.** Per go-ahead pick (1), the precise removed-runner arm is live now: the
model carries Betfair's per-runner reduction factor, `_translation.py` populates
it from the real book via the one authorised line, and the guard gates on it. The
Option-B fallback is retained and fires **per-runner at runtime** whenever a
removed runner's factor comes back unreadable (see below).

**How the reduction factor is sourced: the ENRICHED SETTLEMENT PAYLOAD** (not a
companion market-book read), as the read-back resolved at the §3 gate.
`_translate_market_settlement` already builds the settlement dict from a Betfair
market book and already lifts each runner's `removalDate`; the one authorised line
lifts `adjustmentFactor` off that **same raw runner dict** (`_translation.py:573`).
`_parse_runner` (`clients/.../settlement.py:82`) carries it onto
`RunnerSettlement.adjustment_factor` and derives `adjustment_applied` = True
**only** for a REMOVED runner with a positive factor (a genuine Rule-4 deduction),
so a non-removed runner's rating `adjustmentFactor` is never mistaken for a
reduction. No companion read, no new betfair-client surface beyond the model +
`_parse_settlement` + the one line.

**The gate (both resolvers).** `_evaluate_winner_guard` (`settlement.py:451`)
decides, for a WINNER, whether to park:
- **Dead-heat arm:** `dead_heat_count > 0` → park.
- **Removed-runner arm (Option C, market-type-aware):** for each REMOVED runner,
  read its factor — park when it is *material* for the market type
  (**WIN ≥ 2.5%**, **PLACE any > 0**; `REDUCTION_MATERIALITY_THRESHOLD_PCT = 2.5`).
  A WIN winner whose only removed-runner reduction is < 2.5% is **paid full**
  (Betfair applies nothing there), which is correct.
- **Option-B fallback (runtime, per-runner):** if a removed runner's factor is
  **unreadable (None)**, the winner **parks anyway** (`action="fallback_flagged"`,
  `reduction_readable=False`) — honouring the go-ahead invariant "Option B (park
  on any removal) must fire when `adjustment_factor` is None — never a silent full
  payout." (This is the go-ahead's tightening of the brief's original Option-B
  wording, which said "auto-settle WON but flag"; the go-ahead's "park on any
  removal / never a silent full payout" is the safer rule and the one that
  governs — see Deviations.)

The gate is wired into **both** resolvers — `_resolve_settlement_for_bet`
(PENDING, `:689`) parks to PROVISIONAL; `_resolve_provisional_for_bet`
(PROVISIONAL, `:918`) returns `new_state=None` so a parked winner **stays**
PROVISIONAL and is **never un-parked** to SETTLED_WON. This is the load-bearing
§5.1 requirement: without gating the provisional resolver too, the very next
provisional pass would re-settle the parked bet to full winnings. Clean
winner/loser/void paths are unchanged; count fields still ride the park
(`**counts`).

**Market-type sourcing — a resolved sub-detail with ONE residual money-path
exposure, flagged prominently for the triage / launch-readiness call.** The
settlement read carries no Betfair `marketType`, and Option (1) authorised **only**
the `adjustmentFactor` lift in `_translation.py` — lifting `marketType` too would
be a *second* out-of-§9 edit the go-ahead did not authorise (and unilaterally
adding it would break the very "wait for operator authorisation on out-of-surface
edits" discipline this gate exists to enforce). So market type is derived
**bet-side** by `_is_place_market` (`settlement.py:422`) from two grounded signals,
**defaulting to WIN**: `strategy_tag == SYNTHETIC_EACH_WAY` (Strategy 4 — the
each-way/place strategy the brief itself flags as the PLACE case) **or** the leg
market name containing "place" (which catches Betfair's standard "To Be Placed",
since "placed" contains "place"); otherwise WIN.

The two misclassification directions are **asymmetric**, and — corrected from an
earlier overclaim, per the adversarial review below — the bet-safe framing holds in
only one of them:
- **WIN-treated-as-PLACE:** cannot arise in practice (WIN is the default; it would
  need a false place-signal on a win market), and if it did it would only
  *over-park* into manual review — safe.
- **PLACE-treated-as-WIN (the real residual):** a genuine PLACE-market winner
  carrying **neither** signal is scored on the WIN ≥2.5% threshold, so a PLACE
  Rule-4 reduction **below 2.5%** is judged immaterial and the winner is **paid
  full** — a genuine **over-payment**, because Betfair applies any positive
  reduction on a PLACE market. This is **rare** (it needs a PLACE market that is
  neither Strategy-4-tagged nor "place"/"placed"-named — unusual given Betfair
  names place markets "To Be Placed" — AND a winning bet AND a sub-2.5% removed
  runner), and every such decision emits a §5.1b `paid_full` verification record
  for the operator's early-operation audit — but it is an **after-the-fact audit,
  not a bet-safe park**, so it is a real (narrow) exposure the launch-readiness call
  should weigh, not a guaranteed-safe path.

The build ships the precise Option-C arm the brief/go-ahead asked for and does
**not** silently widen it: defaulting unknown→WIN matches the dominant market
(Strategy 1 Safety-Net WIN betting is ~95% of profit) and honours the operator's
explicit rejection of Option A over-parking. **Named follow-up that closes the
exposure:** a second *operator-authorised* additive line in
`_translate_market_settlement` lifting `marketDefinition.marketType` onto a new
optional `MarketSettlement.market_type` field, gated in `_is_place_market` ahead of
the heuristic — one-line, additive, parallel to the adjustmentFactor lift. It was
**not** taken now because the go-ahead authorised only the one line; it is the
recommended pre-live hardening for this guard.

**§5.1b verification records — shape, how to read, how to quieten.**
`RemovedRunnerVerificationRecord` (`settlement.py:176`) is emitted for **every**
removed-runner WINNER decision — park **and** paid-full **and** fallback-flagged.
Fields: `bet_id`, `market_id`, `selection_id` (the winner), `market_type`
(win/place), `materiality_threshold_pct` (2.5 win / 0.0 place), `removed_runners`
(each carrying `selection_id`, `adjustment_factor`, `adjustment_applied`,
`readable`), `reduction_readable`, `action` (`parked`/`paid_full`/
`fallback_flagged`), `dead_heat_count`, and a human `detail` string.
- **Surface (how the operator reads them):** the resolver attaches the record to
  the `SettlementDecision`; each pass emits it as a **structured INFO log line**
  (`_emit_verification_record`, `settlement.py:1157`) and counts it
  (`removed_runner_verifications` on both pass results). Parked bets *also* appear
  in the manual PROVISIONAL queue with the `provisional_dead_heat_or_reduction`
  reason. During the first live stretch the operator reads these log lines (and
  the queue) and confirms each decision — **crucially including the negative
  `paid_full` decisions**, which otherwise settle silently and are where a wrong
  threshold or a market-type misclassification would hide.
- **How to quieten once proven:** the records are deliberately lightweight and
  retirable — raise the `_emit_verification_record` log level (or gate it behind a
  verbosity flag) once the guard has decided correctly against real Betfair enough
  times. It is not a reconciliation engine and re-settles nothing.
- **No GET endpoint for §5.1b:** a persisted read-only list would need a
  settlement audit table, which is explicitly out of scope (§5.5 / report 5E). The
  log-line + provisional-queue surface satisfies the brief's "a log line and/or a
  read-only list"; a persisted list is a named follow-up gated on that table.

**Tests (§7 5.1):** `test_settlement_guard.py` (15) — dead-heat WINNER parks in
the PENDING resolver **and** is held (not un-parked) in the PROVISIONAL resolver
and end-to-end across both passes (settled_won stays 0); WIN winner with a ≥2.5%
removed-runner reduction parks; WIN winner < 2.5% is paid full; PLACE winner (via
strategy **and** via market name) with any reduction parks; the §5.1b record is
emitted with correct factor/threshold/action for park **and** paid-full; the
Option-B fallback (unreadable factor) parks with `reduction_readable=False`;
clean-winner → SETTLED_WON regression holds with no record; boundary factor
(exactly 2.5%) is material. Plus 3 betfair-client tests: `_translate` lifts
`adjustmentFactor`; `_parse_settlement` derives `adjustment_applied` across
removed/non-removed/zero/None; backward-compat without the field.

---

## 5.2 — Guard 2: missing free-bet-credit detector (credit stays MANUAL)

**What was built.** `workflows/promos/v1/credit_gap.py` (new) —
`list_uncredited_qualifiers(conn)` lists settled-lost Safety-Net qualifiers with a
promo attached that have **no** credit event yet, reusing the **exact** credit-in
gate (`strategy_tag == 'safety_net'` ∧ `settlement_state == 'settled_lost'` ∧
`promo_template_id` present — the same `bets` columns `promos.py` queries, sourced
here from the canonical `StrategyTag`/`SettlementState` enum values so they cannot
drift from the router's `_GATE_*` literals) **and** the existing idempotency helper
`find_existing_credit` (`fb_credit.py:106`) reused verbatim — so it and the
credit-in write agree exactly on what is outstanding. It **writes nothing and
credits nothing**; the credit itself stays the manual `POST /credit-in` action
(standing decision). Surfaced read-only via `GET /api/v1/promos/credit-gaps`
(`promos.py:307`). An unparseable qualifier id (O5) is skipped with a warning, not
silently dropped.

**Tests (§7 5.2):** `test_credit_gap.py` (5) + `test_promos_credit_gaps.py` (2) —
lists an uncredited qualifier; excludes an already free-bet-credited one and an
already cash-credited one; excludes non-qualifiers (wrong strategy / state / no
promo); writes nothing (event + bet row counts unchanged); the endpoint returns
only the uncredited qualifier and 200-with-`[]` when none.

---

## 5.3 — Guard 3: post-settlement market-void detector (NOT re-settlement)

**What was built.** `workflows/bet_entry/v1/post_settlement_void.py` (new) —
`run_post_settlement_void_detection(...)` sweeps terminal **non-VOIDED** settled
bets (`settled_won`/`settled_lost`) within a bounded recent lookback, re-reads each
bet's Betfair market via the same `RealSettlementReader`, and flags any whose
market now reads `market_voided` — or whose settled runner now reads `REMOVED` —
using the `POST_SETTLEMENT_VOID` label. It **transitions nothing** (detector only;
terminal→PROVISIONAL re-parking and re-settlement are out of scope). **Bounded +
fail-safe:** candidates come from `list_bets(settlement_states=(won,lost),
placed_from=now-lookback, limit=max_results)` — the only existing read that gives a
recent-window, bounded terminal batch (`store/repositories/bets.py` is outside the
§9 edit surface, so no new storage method was added); any unavailable / 404 read
is counted as **"cannot check," never "voided"**; the bounded batch is reported so
nothing is silently dropped.

**Tests (§7 5.3):** `test_post_settlement_void.py` (7) — flags a terminal bet whose
market now reads `market_voided`; flags one whose settled runner now reads
`REMOVED`; ignores an unchanged market; treats a 404/unavailable as "cannot check"
(never flagged); writes no state (bet stays terminal); an already-VOIDED bet is not
a candidate; a bet outside the lookback window is not swept.

---

## § overall

The auto-settlement worker chain is now **implemented-and-wired** (S189 taxonomy)
— a live REST settlement reader, an asyncio periodic driver running both passes,
and three detect/park guards — but it is **not yet live-proven** against real
Betfair. It ships **wired but OFF by default**: it runs only when the operator
sets **`BETHUB_SETTLEMENT_WORKER=on` (or `=true`/`=1`)** *and* the app is already
in live mode (`BETHUB_BETFAIR_MODE=live`); in any other configuration no bet
auto-settles and the manual PROVISIONAL router behaves exactly as before. Still
deferred (unchanged): threshold calibration, the free-bet-credit automation and
any auto-re-settlement (Guards 2/3 detect only), a persisted settlement audit
table, and the marketType-precise gating follow-up. The money-path invariants hold
end to end: a payout the code cannot model (dead-heat, material or unreadable
removed-runner reduction) parks to manual review and is never silently auto-paid
full, in either resolver.

## § adversarial review (internal verification method — not the Cowork gate)

Before finalising, the money-path guarantees were adversarially reviewed by 5
independent skeptic agents (each told to REFUTE, reading the actual working-tree
code). **This is an internal verification method, not the parked pre-W16 Cowork
governance panel** — that cross-model gate remains the pre-live adversarial review
before real money flows, and nothing here substitutes for it. Outcome: **4 upheld,
1 refuted**.

| Claim | Verdict | Handling |
|---|---|---|
| Guard 1 gates BOTH resolvers; PROVISIONAL pass never un-parks; a parked case is never silently paid full (dead-heat / material reduction / unreadable factor all park) | **upheld** | The load-bearing invariant holds (verified: the only `SETTLED_WON` in the provisional resolver sits under the `else` of `if guard.park:`). No change. |
| Removed-runner materiality is market-type-aware and bet-safe; "any misclassification biases toward PARK, never mis-pay" | **refuted (major)** | Correct: the PLACE-treated-as-WIN default can over-pay a sub-2.5% PLACE reduction. Report claim corrected (§5.1 above); behaviour kept (defaulting WIN is brief-aligned); marketType follow-up recommended pre-live. |
| Worker safe-by-default; start failure never aborts startup; teardown cancel-and-awaits; passes off the event loop | **upheld** | Confirmed (gate at `settlement_worker.py:65`, sole caller `main.py:145`, fail-safe `main.py:150-157`). Nit re teardown thread — see below. |
| Guards 2 & 3 strictly read-only; Guard 3 treats 404 as cannot-check + is bounded | **upheld** | Confirmed. Nit re credit_gap gate fidelity — **fixed** (empty-string `promo_template_id` now excluded to match the credit-in gate exactly; test added). |
| Model change backward-compatible; no unintended change to existing settle paths | **upheld** | Confirmed (new fields default to pre-build shape; stored JSON still validates). The added §5.1b log line + counter on immaterial winners is intended, not a regression. |

## § anything else noticed

- **Go-ahead vs brief on Option B (reconciled toward safety):** the brief's §5.1
  wording for the Option-B fallback was "auto-settle WON but flag"; the go-ahead's
  non-negotiable invariant is "Option B (park on any removal) … never a silent
  full payout." These conflict, and the build follows the **go-ahead** (park on an
  unreadable removed-runner factor). It is the later governing document and the
  strictly safer money-path rule.
- **3 pre-existing tests updated (not a regression):** `test_settlement.py`'s
  `test_resolve_populates_dead_heat_count_on_terminal_transition`,
  `test_pass_writes_count_fields_on_terminal_transition`, and
  `test_provisional_pass_writes_count_fields_on_terminal_transition` asserted the
  **old 5F behaviour** — a dead-heat WINNER force-settling to SETTLED_WON (the very
  bug Guard 1 fixes). Their real purpose is "count fields stamped on a terminal
  transition," so the vehicle was repointed to a **LOSER** (a genuine terminal
  transition unaffected by Guard 1, legitimately carrying a market-level
  `dead_heat_count`); dead-heat-winner parking is now covered explicitly by the new
  Guard 1 tests.
- **`adjustment_applied` is a parse-time removal flag, not the materiality
  verdict:** it marks "this REMOVED runner carries a positive Rule-4 factor," and
  is carried into the §5.1b record for operator visibility. It deliberately does
  **not** encode Betfair's sub-2.5% WIN suppression — that market-type-aware
  materiality lives in the guard, which knows the bet's market type. This avoids a
  second source of truth for the park decision.
- **Backward-compat of the model change:** the two new `RunnerSettlement` fields
  default to the pre-build shape (`None` / `False`), so previously-persisted
  `last_read_market_state` JSON still validates via `MarketSettlement.model_validate_json`
  (provisional router, `provisional.py:289`) and the `bet_store_adapter`
  dict↔JSON path is untouched. No `store`/`domain`/adapter edits were needed.
- **Worker teardown finishes the in-flight pass (benign):** on lifespan teardown
  `SettlementWorkerHandle.stop()` cancels the loop coroutine and awaits its unwind,
  but a pass already running inside `asyncio.to_thread` completes in its worker
  thread rather than being interrupted mid-flight. This is safe: each pass is
  idempotent and bounded (`max_results=100` + age cutoff) and its writes are
  per-bet committed, so a pass finishing just after a shutdown signal only completes
  work it would have done anyway. Making the synchronous pass cancellable mid-flight
  was judged not worth the complexity for v1.
- **Guard 2 gate fidelity (fixed post-review):** the detector's SQL now excludes
  both `NULL` and empty-string `promo_template_id`
  (`IS NOT NULL AND != ''`), matching the credit-in router's Python-falsiness gate
  (`not promo_template_id`) exactly, so the detector and the write never disagree on
  whether a promo is attached.
