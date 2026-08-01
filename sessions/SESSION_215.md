# SESSION 215 — Settlement-worker diligence triaged; backlog burndown checked

**Opened:** 2026-07-01 17:00 ACST (headless runner; held at gate)
**Resumed (operator, live):** 2026-07-02 ~08:00 ACST
**Closed:** 2026-07-02 08:40 ACST
**Tool routing:** Chat (triage + governance + read-only VPS/DB reads). Code executed the settlement-worker investigation out-of-session.
**Governing DRs:** DR-021 (Adelaide anchors), DR-027/028 (two-DB boundary), DR-032 (Betfair settlement spine), DR-033 (data-source roles; placings analytical, settlement Betfair-only).

---

## Anchor

- Open (runner): 2026-07-01 17:00 ACST — held on gate (settlement report absent).
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-07-02 08:40 ACST`.

## Pre-flight checks

Runner's S215 open drift-check was clean (current_state matched S214 close 16:54; SESSION_214.md present; no phantom files). On live resume, root re-listed clean — no `system_snapshot.md`/`context_index.md`/`STATUS.md`/`CLAUDE.md`; settlement investigation report now present.

## Session shape

Probe-triage + governance session across a day-gap. Runner opened S215 the prior evening and HELD (the settlement-worker investigation report wasn't present — Code hadn't run). Operator resumed next morning. Ran in three strands: (1) reviewed Code's confirmation-gate read-back and released the go-ahead with two guardrails; (2) once Code finished, triaged the investigation report against the brief §7/§8; (3) checked the overnight placings backfill burndown (the 1 Jul post-quota data point) via a read-only VPS/capture.db look.

## What was delivered

1. **Settlement-worker investigation — read-back reviewed, go-ahead released.** Code's confirmation-gate read-back (anchor `e2638fa` verified, all file/line anchors confirmed, three refinements flagged) was reviewed against the locked brief and accepted. Go-ahead released with two guardrails attached: (a) Code's internal adversarial pass is a *method*, not the parked pre-W16 Cowork governance panel; (b) per-finding evidence granularity (command/grep/line cite per §7/§8) must survive the multi-agent synthesis. Both guardrails were subsequently honoured in the report.

2. **Settlement-worker investigation report TRIAGED.** `settlement_worker_diligence_investigation_report.md` (121 lines) triaged against §7/§8. Read-only confirmed; `uv run pytest` the only execution (117/117 green). Verdicts accepted as evidenced:
   - **5A CONFIRMED (sharpened):** auto-worker not wired; the *production* scheduler is explicitly deferred to v3; only a never-started test stub (`ManualSettlementScheduler`) + reference impl (`ThreadingSettlementScheduler`) exist; not exported from the package `__init__`. Manual router wired at main.py:139.
   - **5B CONFIRMED:** 117 pass / 0 fail (111 across the four named files); `RealSettlementReader` absent repo-wide; fixture/in-memory only.
   - **5C CONFIRMED:** settlement commit and IOU credit are fully independent (different modules/endpoints/connections/spines), no atomic coupling, no reconciliation for a *missing* credit. Wider than framed — the credit is a **manual** operator action (`POST /credit-in`, gated on the bet already being `settled_lost`), so the loss-recorded/refund-omitted window opens if the operator simply never invokes it.
   - **5D CONFIRMED:** `reconciliation_attempts` non-idempotent (unbounded +1, no cap/reset); purely observational, feeds no resolver decision.
   - **5E CONFIRMED:** deferrals fully enumerated. Sharpest money-path carve-out: `POST_SETTLEMENT_VOID` defined but never fired → a terminal bet whose market later voids is never revisited. Also: no persisted settlement audit trail at v1; manual resolution only from PROVISIONAL; three `DEFAULT_*` thresholds are placeholders ("calibrate post-DR-029").
   - **5F REFUTED (the one map error):** PROVISIONAL is the safe default for the *truly unrecognised*, but exhaustiveness fails on **dead-heat** — a dead-heat winner force-settles to `SETTLED_WON` and is paid **full** winnings (`dead_heat_count`/`voided` never gate any branch or payout); removed-runner (Rule 4) reductions are not modelled anywhere. Root: settlement computes the win from price rather than reading Betfair's already-reduced settled amount.
   - **5G CONFIRMED:** two-DB boundary clean; no capture.db caching/denormalisation either direction.

3. **Triage outcome + operator decisions.** Report accepted as strong; guardrails held. Operator calls locked on the three real gaps — all handled with **lightweight detect/park guards, not sophisticated auto-fixes**:
   - **Dead-heat / removed-runner (5F):** rare; don't model the reduction maths. Cheap fix = detect dead-heat (`dead_heat_count` already carried, currently ignored) / removed-runner-with-deduction and **park to PROVISIONAL for manual settlement** rather than auto-settle full.
   - **Free-bet refund (5C):** confirmed this is the insured/Safety-Net promo (loss → free-bet back). Stays **manual** per standing decision — the report doesn't argue for automation. The only cheap improvement worth considering is a **detector** (flag `settled_lost` + qualifying insured promo + no `FREE_BET_CREDITED` event), not an embed. Operator's call whether even that's worth it.
   - **Post-settlement market void (5E):** outlined in detail from source (`ProvisionalTriggerSource.POST_SETTLEMENT_VOID` defined settlement.py:250, zero firing sites; both resolvers read only PENDING/PROVISIONAL, docstrings settlement.py:349-353 / 547-550 mark it not-implemented-at-v1). Cheap fix = a **detector** that flags "terminal bet whose Betfair market is now VOID" for manual correction, not the automatic re-settlement engine.
   - **Shape agreed:** the eventual settlement-worker build = wire up the worker + these three park/flag guards, not three new subsystems.

4. **Placings backfill burndown checked (1 Jul post-quota data point).** Read-only VPS look via the operator's ssh-agent (key loaded mid-session; agent socket bridged from launchd into the tool shell) + capture API on the live 8400 tunnel. Findings on the 05:30 ACST nightly (`racing-metadata-backfill` @ 2026-07-01 20:00 UTC):
   - **The S213 empty-runners (empty200) fix landed on its target** — 21 date-fetches all `empty200 pre=0 post-retry=0`; one transient EMPTY-RUNNERS warning that self-recovered.
   - **But the run still walls — on a different signature.** Backlog pass `attempted=6 filled=0 placings=0 walled=6 (post_retry_truncated=6)`; recent-window populated only today (07-01, 124 runners / 94 positions), all 14 older dates returned `0 runners (truncated)`. `oldest_remaining=2026-03-21`, `remaining_backlog_dates=100`.
   - **Burndown:** `recoverable_deficit` = **35,718**, down from ~41k; trend had drifted slightly up (41,340 → 41,633 → 41,861 across 29 Jun–1 Jul) then dropped to 35,718 this run. **Caveat:** that ~6.1k drop exceeds the run's visible fills (backlog 0; recent-window ~94 positions + a few hundred PLACED refinements) — confirm in triage whether it's real fills or a change in what the metric counts as recoverable before banking it.
   - **Diagnostic wrinkles:** the wall happened at 20:00 UTC, *before* the 23:00 UTC collector start (collector likely idle) — weakens "collector-load contention", leans toward the backfill's own inter-date pacing or API-side truncation. Recent dates (17-30 Jun, well inside retention) also truncated, so it's not purely aging; some old meets 404 outright (genuinely gone). Maps to current_state's "still walls → inter-date-pacing hypothesis (small pacing-constant bump, not a new architecture brief)" branch, plus a retire-vs-chase question on the oldest ~100 dates.

## Open items

Pointer-only — full list in `current_state.md`.

**New / changed in S215:**
- Settlement-worker diligence COMPLETE (6 confirmed / 1 refuted). Three build-time guards identified (dead-heat park; credit detector; post-settlement-void detector).
- Placings burndown: empty200 fix confirmed working; backlog still walls on `post_retry_truncated`; deficit 35,718 (verify the 6k drop).

## Open items out

- Settlement-worker investigation report triage (the S215 gated first action) — DONE.
- Placings burndown check (tonight's nightly run) — DONE.

## Session close state

Rebuild root clean (no phantom files; settlement report present). `.close_out_backups/` swept to the S216 opening prompt only. `v3_build_picture.md` updated (settlement-worker stream state moved). `standing_instructions.md` untouched (no instruction edits this session). No code touched in Chat; all VPS/capture reads `mode=ro`; bet-safety CLEAN.

## Forward routing

**Confirmed with operator.** S216 auto-action = **finalise the settlement worker** (draft the settlement-worker build brief — wire the worker + the three lightweight guards: dead-heat/removed-runner → park to PROVISIONAL; free-bet-credit missing-detector [manual stays manual]; post-settlement-void detector). **Then** address the placings backfill (the inter-date-pacing bump + the retire-vs-chase question on the oldest ~100 backlog dates, and confirm the 6k deficit drop was real). Data Foundation harvest remains parallel, not gating. Pre-W16 Cowork multi-agent panel stays parked until the worker is wired toward launch.
