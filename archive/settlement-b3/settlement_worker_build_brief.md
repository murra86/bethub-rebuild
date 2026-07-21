# Settlement-worker BUILD brief — LOCKED

> **STATUS: LOCKED — ready for Code.**
> Drafted Session 216 (2026-07-02, headless runner); reviewed and locked by the
> operator the same session. The one open money-path decision (§5.1a, removed-runner
> arm) is **resolved: Option C (precise, reduction-factor-gated) with Option B as a
> baked-in, pre-authorised fallback** — see §5.1a. An early-operation verification
> surface was added at operator request (§5.1b). Hand this to Code as-is. Anchors are
> at bethub-v3 @ `e2638fa`; Code re-confirms HEAD at session start per §3.

**Commissioned:** 2026-07-02 (Session 216), locked same session · Adelaide local timestamps (ACST/ACDT) throughout per DR-021.
**Codebase anchor:** bethub-v3 @ `e2638fa` (confirmed current HEAD at draft time, working tree clean, 0 commits ahead — matches the investigation report's anchor). Code confirms current HEAD at session start; if it has moved, note the new sha in the report header, re-verify the file/line anchors below, and proceed.
**Bet-safety:** This is a **money-path change brief.** It modifies settlement code that, once wired, marks real bets won/lost/void and reads live Betfair. Read-and-confirm gate is mandatory (§3). The build is **safe-by-default**: the auto-worker ships wired but **OFF unless the operator explicitly opts in** (§5.0), mirroring the existing `betfair_mode=mock` default. No live Betfair account is touched during the build or its tests — all verification is fixture-based.

---

## 1. What this brief is and is not

This is the **settlement-worker finalisation build.** It does two things:

1. **Wires the already-built auto-settlement worker into the running app** — the worker is code-complete and 117/117 green but is referenced nowhere outside `settlement.py` and its tests (investigation report 5A). Today nothing starts it, so no bet ever auto-settles and the manual PROVISIONAL queue is always empty.
2. **Adds three lightweight detect/park guards** — not three new subsystems, and not sophisticated auto-fixes. Each guard *detects and surfaces* a known money-path gap; none of them models reduction maths or auto-re-settles. Scope was locked with the operator at S215.

It is **not**: a re-settlement engine, an automation of the free-bet credit (that stays manual by standing decision), a calibration of the placeholder thresholds (deferred, §5.5), or the pre-W16 launch go/no-go (that is the parked Cowork multi-agent gate, unaffected by this build).

## 2. Why this work exists

Settlement is the first money-path build item in this stretch, ahead of the W16 cutover. The S214 diligence + S215 triage confirmed the chain is **code-complete, thoroughly tested against fake data, and not plugged into anything live** (investigation report §9). Wiring it is what turns green fixture tests into a live-proven settlement path (the S189 "classify done by live-integration status" discipline). The three guards close the three real gaps the diligence found (5C credit decoupling, 5E post-settlement void, 5F dead-heat/reduction) at the cheapest honest level — detect and hand to the operator, don't guess.

## 3. Pre-reads and READ-AND-CONFIRM gate (mandatory — money-path)

Code reads these in full **before writing any code**, then posts a short read-back confirming (a) the anchor sha, (b) that each file/line anchor below still resolves, and (c) Code's understanding of the one open decision in §5.1. **Wait for operator go-ahead on the read-back before editing.** This is the same money-path gate used for the diligence brief.

Pre-reads:
- `settlement_worker_diligence_investigation_report.md` — the grounded findings this build operationalises. Required, in full. Load-bearing sections: 5A (wiring), 5C (credit decoupling), 5E (post-settlement void), 5F (dead-heat/reduction).
- `settlement_worker_diligence_scope.md` — the map (§3 file map, §3E money-state write surfaces, §3F boundary).
- `workflows/bet_entry/v1/settlement.py` (1,354 lines) — the worker.
- `clients/betfair_client/v1/settlement.py` (118 lines) — the Betfair settlement read + models.
- `ui/api/main.py`, `ui/api/dependencies/composition.py` — the wiring targets.
- `workflows/bet_entry/v1/betfair_adapter.py` — the W6 `RealBetfairAdapter` reader-adapter pattern to mirror for the live settlement reader.
- `workflows/promos/v1/fb_credit.py` + `ui/api/routers/promos.py` — Guard 2 substrate.
- DR-032 (Betfair market = settlement spine), DR-033 (settlement is Betfair-only), DR-027/028 (two-DB boundary), DR-030 (module boundaries — where the worker and guards live).

## 4. System access

- Mac filesystem, bethub-v3 repo — **read-write** on the named files only (§5, §9). `git status`/`log`/`show`/`diff` for orientation; **no** `commit`/`stash`/`checkout`/`reset`/`add` unless the operator's Code prompt says otherwise (the rebuild convention is Code leaves the tree dirty and the report names what changed).
- Test suite — `uv run pytest` (the repo is a `uv` project; bare `python3 -m pytest` fails at collection — standing instruction). Add/extend tests freely; that writes only the test harness.
- **No live or staging Betfair.** No real settlement pass. Every new test uses `MockSettlementReader` / in-memory or `tmp_path` SQLite, exactly as the existing suite does.
- No VPS access — settlement is Mac/app-side, not the capture pipeline.

## 5. Substantive scope

Four parts: **5.0 wire the worker** (the core), then **5.1 / 5.2 / 5.3** the three guards. Anchors are at `e2638fa`.

### 5.0 — Wire the auto-settlement worker into the running app (the core build)

Today (5A): `run_settlement_pass` (settlement.py:698), `run_provisional_resolution_pass` (settlement.py:914) and the `SettlementScheduler` Protocol (settlement.py:1235) are referenced nowhere in `composition.py` or `main.py`, and are not exported from `workflows/bet_entry/v1/__init__.py`. The only live async bring-up in the app is the Betfair streaming socket (`main.py:88-113`, gated on `betfair_mode == "live"`). There is **no existing live periodic-worker pattern** in the app — this build establishes the first one.

Build:

1. **Live settlement reader.** Add a `RealSettlementReader` (satisfying the `SettlementReader` Protocol, settlement.py:96-114) that wraps the betfair client's `market_settlement()` (betfair/settlement.py:86-118) and translates its `ReadEnvelope[MarketSettlement]` into the `ReadOutcome[MarketSettlement]` the resolver expects — mirror the W6 `RealBetfairAdapter` in `betfair_adapter.py`. `RealSettlementReader` is currently absent repo-wide (report 5B). Place it per DR-030 (alongside the other bet-entry adapters).

2. **Compose it + start the passes.** In `composition.py` (mirror the streaming bring-up handoff at `composition.py:560-567`): build the settlement reader from the composed `BetfairClient` (reuse the cached `_betfair_client()` factory, composition.py:492), and expose a start handle to the lifespan hook. In `main.py`'s `lifespan` (main.py:88-113), start a periodic driver that runs `run_settlement_pass` **and** `run_provisional_resolution_pass` on `DEFAULT_SETTLEMENT_INTERVAL_SECONDS` (settlement.py:71, 60s), against the composed bet storage + live reader.
   - **Scheduler mechanism (Code's technical call, Cat 5):** prefer an `asyncio` background task consistent with the existing streaming lifespan pattern (start on entry, cancel-and-await on teardown in the `finally`), rather than the reference `ThreadingSettlementScheduler` (settlement.py:1285). Keep `ManualSettlementScheduler` / `ThreadingSettlementScheduler` as the test/reference impls. If Code judges the threading scheduler materially simpler and safe under FastAPI teardown, it may use it — say which and why in the report.
   - Export the worker entry points + the new reader from `workflows/bet_entry/v1/__init__.py` (currently unexported, report Refinement B).

3. **SAFE-BY-DEFAULT opt-in (money-path, load-bearing).** The pass driver starts **only** when **both** (a) `betfair_mode == "live"` **and** (b) a new explicit opt-in setting is on — default **OFF**. Proposed: `BETHUB_SETTLEMENT_WORKER=on` (settings field defaulting to off), mirroring the `betfair_mode=mock` safe default in `composition.py:8-21`. Rationale: deploying/importing the app, or flipping to live for streaming, must **not** silently begin auto-settling real bets. The operator flips the worker on deliberately once satisfied. In mock mode or with the flag off, the worker does not run and the manual provisional router (already wired, main.py:139) behaves exactly as today. Fail-safe: any error starting the worker is logged and never aborts app startup (mirror `main.py:98-105`).

4. **Idempotency + bounded sweep:** `run_settlement_pass` is already idempotent across calls and bounded by `max_results=100` + the age cutoff (settlement.py:702-735). No change needed; confirm the wiring passes those through and does not double-schedule.

### 5.1 — Guard 1: dead-heat / removed-runner-with-deduction → detect and park to PROVISIONAL

**The gap (5F, REFUTED map):** a dead-heat winner returns `RunnerSettlementStatus.WINNER` (the enum is closed WINNER/LOSER/REMOVED, betfair/settlement.py:35-38 — no DEAD_HEAT). It hits the unconditional `WINNER → SETTLED_WON` branch in **both** resolvers (settlement.py:449-459 PENDING, settlement.py:652-662 PROVISIONAL) and is paid **full** winnings downstream (`balance_derivation.py`, no dead-heat reduction). `dead_heat_count` / `removed_runner_count` are carried on `MarketSettlement` (betfair/settlement.py:55-56) and already threaded into the decision's `counts` (settlement.py:399-403 / 596-600) but **gate nothing**.

**Build — gate the WINNER branch in BOTH resolvers.** Before returning `SETTLED_WON`, if the winner is subject to a payout reduction the code doesn't model, return `PROVISIONAL` instead (new `reason_code`, e.g. `provisional_dead_heat_or_reduction`; surface via a `ProvisionalTriggerSource` — reuse `UNEXPECTED_STATE` or add a `DEAD_HEAT_OR_REDUCTION` member, settlement.py:240-251). This reuses the existing PENDING→PROVISIONAL plumbing end-to-end (the pass already counts `provisional_entered`, settlement.py:777) and the existing manual-resolution path clears it (`apply_manual_operator_resolution`, settlement.py:1128; already wired at main.py:139).

> **CRITICAL correctness point (why both resolvers):** if the guard is added only to the PENDING resolver, the very next `run_provisional_resolution_pass` will re-read the same market, hit its own unconditional `WINNER → SETTLED_WON` branch (settlement.py:652-662), and **un-park** the bet straight back to a full-payout settlement. The guard MUST gate the WINNER branch in **both** `_resolve_settlement_for_bet` and `_resolve_provisional_for_bet`. This is the load-bearing money-path requirement of Guard 1.

**Detection condition — two arms:**

- **Dead-heat arm (ships cleanly now):** park the WINNER when `settlement.dead_heat_count` is not None and `> 0`. A dead-heat divides the win payout; the code pays full, so parking is correct and dead-heats are rare (low manual-work cost).

- **Removed-runner-with-deduction arm — RESOLVED: Option C (precise), with Option B pre-authorised as fallback (§5.1a).** Park a WINNER only when its race had a removed runner whose reduction actually *bit* on this bet — a material deduction — not on every scratching. "Material" follows Betfair's own line, and it is **market-type-aware**:
  - **WIN markets:** the reduction is applied only when the removed runner's reduction factor is **≥ 2.5%**; below 2.5% Betfair applies nothing and the winner is paid at full original price — so there is nothing to park. Park when a removed runner's applied reduction factor ≥ 2.5%.
  - **PLACE markets:** the reduction factor is applied **even below 2.5%**. Park when any removed runner's applied reduction factor > 0. This matters for Strategy 4 (synthetic each-way / place value) — a WIN-only ≥2.5% rule would silently under-park genuinely-docked place winners.

  **Data gap + how Option C closes it.** The current `MarketSettlement` / `RunnerSettlement` model does **not** carry the reduction factor — only a market-level `removed_runner_count` (betfair/settlement.py:55) and a per-runner `voided: bool` (betfair/settlement.py:41-45). Betfair *does* expose the figure (the per-runner reduction/adjustment factor), but it lives on the market-book/catalogue data, **not** on the settlement read this contract currently models. So Option C requires: (i) extend `RunnerSettlement` + `_parse_settlement` (betfair/settlement.py:41-45, 60-83) to carry the per-runner reduction factor and whether it was applied; and (ii) source that figure — **Code determines at the read-and-confirm gate (§3) whether it arrives via an enriched settlement payload or requires a companion market-book read** per settled bet in a removed-runner race, and states which in the read-back. Because the settlement read is not yet live-proven (report 5B; fake transport in tests), the exact field/shape is **confirmed against the real payload as part of this build, not assumed**.

  **Fallback (Option B) — pre-authorised, no operator round-trip.** If, when wiring the live read, Code finds the reduction factor cannot be cleanly obtained (field absent from the real payload, or the companion read proves unavailable/unreliable at v1), Code ships the **dead-heat arm live** and, for removed-runner winners, auto-settles WON but emits the §5.1b verification record flagged "removed-runner, reduction not readable — needs manual review", deferring precise handling until the read is live-proven. Code states in the report which arm shipped (precise vs fallback) and why. Do **not** model the reduction maths and do **not** auto-settle full silently in any parked case (operator lock).

In every parked case (dead-heat or removed-runner), the bet lands in the manual PROVISIONAL queue with the count fields preserved (they already survive the manual write, settlement.py:1146-1151) — settlement never auto-pays full on a parked winner (operator lock).

#### 5.1a — RESOLVED (operator, Session 216): Option C with Option B fallback

The removed-runner arm is **Option C (precise), with Option B pre-authorised as the fallback** (build spec in the arm above). Recorded here for the decision trail. The three options weighed:

- **Option C — precise detector (CHOSEN).** Extend `RunnerSettlement` (betfair/settlement.py:41-45) + `_parse_settlement` (:60-83) to carry Betfair's per-runner reduction factor, then park a WINNER only when a removed runner's reduction was *material* (≥2.5% win / any on place). Detect-and-park, not maths-modelling — read the factor to decide whether to park; never compute the reduced payout. Confirmed at draft: Betfair exposes the factor, but on the market-book/catalogue data rather than the settlement read, and the read is not yet live-proven — so the exact source (enriched settlement payload vs companion market-book read) is Code's call at the §3 gate and the field is confirmed against the real payload during the build. Minimal extra manual work — only genuinely-docked winners park.
- **Option A — coarse detector (rejected).** Park any WINNER when `removed_runner_count > 0`. No model change, but **over-parks**: scratchings are common, so a large share of winning Strategy 1 (Safety Net) bets — ~95% of profit — would land in the manual queue even when no material deduction applied. Rejected for the manual-work load.
- **Option B — defer the removed-runner arm (retained as fallback).** Ship dead-heat now; for removed-runner winners, auto-settle but flag for review via §5.1b, and revisit when the read is live-proven. Pre-authorised so Code doesn't round-trip if C can't be cleanly sourced live.

#### 5.1b — Early-operation verification surface (operator confidence check, added Session 216)

Guard 1's removed-runner logic is proven by fixture tests against fake data, but is only *trusted* once it has decided correctly against **real** Betfair a few times (S189: implemented-and-wired ≠ live-proven). So the guard emits an operator-readable **verification record for every removed-runner decision it makes** — both when it parks and when it declines to park — capturing: bet ref, market id, market type (win/place), the removed runner(s) and their reduction factor(s), the materiality threshold applied (≥2.5% win / any place), and the resulting action (**parked** / **paid full** / **fallback-flagged**).

- **Detect-and-surface only.** A log line and/or a read-only list, mirroring the Guard 2/3 surfacing shape (a workflow function, optionally a `GET` endpoint so it shows in the app). It changes **no** settlement behaviour and re-settles nothing.
- **Purpose — the early-operation audit.** For the first stretch after the operator flips the worker ON in live mode, the operator reads these records and confirms each decision matches what actually happened on Betfair — including the *negative* decisions (removed-runner winners paid full because the reduction was immaterial), which otherwise settle silently and are the easy place for a wrong threshold to hide.
- **Deliberately lightweight and retirable.** It can be quietened once the guard is proven live. It is **not** a reconciliation engine and does **not** cross-check against a second source or re-settle (that stays out of scope per §5.5 and the Guard-3 detector boundary).

### 5.2 — Guard 2: missing free-bet-credit detector (credit stays MANUAL)

**The gap (5C):** settlement commits terminal state; the free-bet IOU credit is a **separate manual** operator action (`POST /api/v1/promos/credit-in`, promos.py:186) gated on the bet already being `settled_lost`. Nothing reconciles a `settled_lost` Safety-Net qualifier with a promo attached that never got its `FREE_BET_CREDITED` event — the loss is recorded, the refund owed is invisible.

**Build — a detector only. No automation of the credit; the credit stays manual (standing decision).** Add a read-only detector (per DR-030, in `workflows/promos/v1/`) that lists qualifiers owed a credit but not yet credited, reusing the exact gate the credit-in router already uses:
- `strategy_tag == 'safety_net'` (promos.py:46) ∧ `settlement_state == 'settled_lost'` (promos.py:47) ∧ `promo_template_id` present (the same `bets` columns queried at promos.py:173), **and**
- `find_existing_credit(adapter, qualifier_uuid) is None` (fb_credit.py:106-117 — the existing idempotency helper, reused as-is).

Surface it as a **read-only** list (a workflow function + optionally a `GET` endpoint so it shows in the app). It writes nothing and credits nothing — it only tells the operator "these lost Safety-Net bets are owed a free bet you haven't credited yet."

### 5.3 — Guard 3: post-settlement market-void detector (not a re-settlement engine)

**The gap (5E):** `ProvisionalTriggerSource.POST_SETTLEMENT_VOID` is defined (settlement.py:250) but has **zero firing sites** — both resolvers only read PENDING/PROVISIONAL (docstrings settlement.py:350-353 / 547-550), so a bet that already settled terminally and whose Betfair market **later voids** is never revisited.

**Build — a detector only. NOT an automatic re-settlement engine (operator lock).** Add a read-only sweep (mirror the settlement pass's read shape, using the same `RealSettlementReader`) over **terminal, non-VOIDED settled bets within a bounded recent lookback**, re-reading each bet's Betfair market; flag any whose market now reads `market_voided` (betfair/settlement.py:53) — or whose settled runner now reads `REMOVED` — as **"terminal bet, market now void — needs manual correction."**
- **Detector only:** it surfaces a list (using the `POST_SETTLEMENT_VOID` label for clarity); it does **not** transition the bet's state (terminal → PROVISIONAL re-parking is out of scope — the manual path only fires *from* PROVISIONAL at v1, settlement.py:1112-1116, and re-settlement is explicitly not this build).
- **Bounded, fail-safe:** only sweep bets settled within a recent window (markets age out — a 404 maps to `betfair_market_not_found`, betfair/settlement.py:98-111); treat any unavailable/404 read as "cannot check," never as "voided." Do not sweep the whole bet history each pass.

### 5.5 — Explicitly OUT of scope (do not build)

- Threshold calibration — `DEFAULT_AGE_THRESHOLD_SECONDS` / `DEFAULT_SETTLEMENT_INTERVAL_SECONDS` / `DEFAULT_PAST_WINDOW_SECONDS` stay at their v1 placeholders (settlement.py:56-88; "calibrate post-DR-029-close").
- Any automation of the free-bet credit itself (Guard 2 is detect-only).
- Any automatic re-settlement / terminal→PROVISIONAL transition (Guard 3 is detect-only).
- A persisted settlement audit-trail table (deferred, report 5E / W8 report §6).
- The `reconciliation_attempts` non-idempotency (5D) — confirmed observational, feeds no decision; leave it.
- Modelling the reduction maths for dead-heat/Rule-4 (operator lock — detect and park, never compute).

## 6. Sequencing within session

1. **Read-and-confirm gate first** (§3) — post the read-back, wait for go-ahead.
2. **5.0 wiring** — the core; establishes the reader + scheduler + safe-by-default flag. Land + test before the guards.
3. **5.1 Guard 1** — dead-heat arm always; removed-runner arm = Option C (park on a *material* reduction: ≥2.5% win / any on place) with the §5.1b verification record emitted on **every** removed-runner decision; Option B fallback (§5.1a) only if the live read can't source the factor. Both resolvers.
4. **5.2 Guard 2** and **5.3 Guard 3** — independent detectors, either order.
5. Full `uv run pytest`, then the report.

## 7. Empirical verification / success criteria

- **Baseline:** `uv run pytest` green before starting (report says 117/117; confirm).
- **5.0:** new tests prove (a) with the opt-in flag OFF (and/or mock mode) the worker does **not** run — no settlement transitions occur; (b) with live mode + flag ON, the driver invokes both passes against the reader on the configured interval; (c) `RealSettlementReader` translates a fresh envelope and an unavailable/404 envelope correctly into `ReadOutcome`; (d) app startup never aborts if the worker fails to start (fail-safe). No live Betfair — drive with a mock reader / injected settings.
- **5.1:** tests prove a dead-heat WINNER (`dead_heat_count > 0`) parks to PROVISIONAL in **both** the PENDING pass and the PROVISIONAL pass (i.e. it is not un-parked by the provisional pass) and is **not** paid full. Removed-runner arm (Option C): a WIN-market winner with a removed runner at reduction factor ≥2.5% **parks**; a WIN-market winner with a removed runner below 2.5% is **paid full** (not parked); a PLACE-market winner with any removed-runner reduction **parks**; and the §5.1b verification record is emitted for **each** of these decisions (park and paid-full alike) carrying the factor, threshold, and action. If the Option-B fallback path is exercised, a removed-runner winner auto-settles WON with the "reduction not readable" flag emitted. Preserve the existing clean-winner → SETTLED_WON path (regression).
- **5.2:** tests prove the detector lists a `settled_lost` safety-net + promo bet with no credit event, and excludes one that already has a `FREE_BET_CREDITED`/`PROMO_CASH_CREDITED` event; and that it writes nothing.
- **5.3:** tests prove the detector flags a terminal non-VOIDED bet whose mock market now reads `market_voided`, ignores one whose market is unchanged, treats a 404/unavailable as "cannot check," and writes no state.
- **Final:** full suite green; net new test count reported.

## 8. Output spec

Single file: `settlement_worker_build_report.md` at the bethub-rebuild root. Structure: one section per 5.0 / 5.1 / 5.2 / 5.3, each stating what was built, the files/lines touched, the tests added, and any deviation from this brief (with reason). The **5.1 section additionally states**: which removed-runner arm shipped (precise Option C vs Option-B fallback) and why; how the reduction factor is sourced (enriched settlement payload vs companion market-book read, resolved at the §3 gate); and the exact shape of the §5.1b verification records plus how the operator reads them and quietens them once the guard is proven live. Then **§ overall** (2-4 sentences, plain language: what is now live-wired vs still deferred, and the exact opt-in flag + how the operator turns the worker on) and **§ anything else noticed**. Per-finding evidence granularity (the same command/grep/line-cite discipline the diligence report held) survives into this report. Length bends to the detail the money-path warrants.

Report states clearly: the worker ships **wired but OFF by default**; it is not live-proven against real Betfair until the operator flips the flag in a live run (S189 taxonomy — this build makes it *implemented-and-wired*, not yet *live-proven*).

## 9. Hard limits

- Edit **only** under `workflows/bet_entry/v1/`, `workflows/promos/v1/`, `clients/betfair_client/v1/` (the settlement model + `_parse_settlement`; plus — **only** if Option C's factor sourcing requires a companion market-book read — the minimal market-book read surface, with Code naming exactly which files/methods it added), `ui/api/` (main, composition, config for the new flag, and a read-only detector route if added), and their test files. No other files.
- **No live or staging Betfair. No real settlement pass. No order placement.** Tests are fixture/in-memory only.
- **No auto-credit of free bets; no auto-re-settlement; no reduction maths.** The three guards detect/park/flag only, exactly as scoped.
- Safe-by-default is non-negotiable: the worker must not run unless the operator has explicitly opted in (§5.0.3).
- No `commit`/`stash`/`checkout`/`reset`/`add` unless the operator's Code prompt authorises it. Leave the tree dirty; the report names what changed.
- No scope creep into other DR-029 items, the placings/VPS workstream, or W16 cutover work.
- If the build needs more than one session to do properly, stop at whatever is coherent and green, and say so — partial-but-solid beats complete-but-rushed on money-path code.

## 10. What happens after Code's session

Next operator-Claude session triages the build report, confirms the worker wiring + guards behave as specified, and decides launch-readiness. The worker stays **OFF** until the operator deliberately opts in. The **pre-W16 Cowork multi-agent gate** (parked) is the adversarial cross-model review before real money flows through the wired worker — this build is what finally gives that gate a live design to shoot at.

## 11. Cross-references

- `settlement_worker_diligence_investigation_report.md` (S215) — the findings this build operationalises (5A/5C/5E/5F load-bearing).
- `settlement_worker_diligence_scope.md` (S214) — the map.
- DR-032 (Betfair market = settlement spine), DR-033 (settlement Betfair-only), DR-027/028 (two-DB boundary), DR-030 (module boundaries), DR-021 (Adelaide timestamps).
- Standing instructions: S189 (classify done by live-integration status — this build is the wiring that moves settlement toward live-proven), S178 (ground "already built" claims — done via the diligence report + this draft's direct code reads).
