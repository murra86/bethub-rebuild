# SESSION 229 — settlement window PASSED (B2 side complete); B1 formally ticked; B5 built + live-tested; B7 built COMPLETE (all three pieces) — runway reduced to B6 only

**Opened:** 2026-07-06 14:27 ACST (cold manual open — no runner result; drift-check clean). Same workday as S228's 14:22 close, five minutes after it.
**Closed:** 2026-07-06 17:06 ACST, Adelaide-anchored per DR-021. Same workday.
**Tool routing:** Single access-having governance Claude Code session on the Mac. Ran all four builds first-hand (Bash + file tools); watched the supervised settlement window by reading the live store `mode=ro`; all app test-drives in **mock mode** against scratch DBs/log dirs (zero Betfair contact, zero live-store writes from this session).
**Bet-safety:** No new bets. The only live-store writes were made by **the operator's own launched app** during the supervised settlement window (settlement worker ON for the window, operator-launched with `BETHUB_SETTLEMENT_WORKER=1`): the four S228 $0 measurement lays stamped `settled_won`/$0 (ledger confirmed untouched) and S227's parked `434257942837` auto-resolved `failed`/$0/`voided` under the S228 LAPSED fix. Both workers OFF when the operator closed the app. Suite never left green; all five commits pushed on green trees.
**Governing DRs:** DR-021, DR-019 (money derives on read — the $0 stamps), DR-027/028, DR-032/033.

---

## Session shape

Opened holding for the supervised settlement window (S228's confirmed first action); the operator said proceed. The window's first attempt surfaced an env-flag miss (the app launched without the settlement switch — caught by reading the process environment, relaunched correctly); the second launch stamped all four lays terminal on its first pass. The operator then said "proceed with whatever is next" and the session ran the remaining runway: B1 governance tick, B5 build, then — after a scope conversation — all three B7 pieces. Two operator calls reshaped B7 mid-flight: permanent log retention, and the phone alarm replaced by an in-tool banner.

## What was delivered (in order)

1. **Supervised settlement window PASSED — settlement side of the LAPSED-fix loop live-proven.** First launch had the flag unset (`ps eww` showed no `BETHUB_SETTLEMENT_WORKER`; operator had double-clicked the launcher) — relaunched with the one-line command; the first settlement pass (14:55) stamped all four S228 lays `pending → settled_won` / $0; `cash_flow_events` confirmed zero money rows for them. Promo catalogue re-confirmed clean under the launch (8/8 concurrent 200s). BetLog "Pending" badges resolved. **En-route live finding: the badges read "Won"/$0** (market outcome favoured the lays; money $0 per DR-019) — joins the BetLog failed/no-bet badge parking-lot item, display-only.

2. **B1 formally ticked** (status refresh prepended to `cutover_readiness_map.md`). Evidence: six real lays through the tool across S227/S228, all via a genuinely SUBSCRIBED stream (§13.1 interlock live), full loop closed in every direction (matched→true money; never-matched→no-bet; settlement stamps S229). Residuals named: F8 audit-sink durability (closed later this same session by B7 piece 1) and the interlock's refusal path (unit-tested only; money-safe direction). **Money path B1–B4 all live-proven.**

3. **B5 BUILT + LIVE-TESTED** (`b5_tunnel_hardening_report.md`, commit `eef2fc2`): launcher auto-starts the 8400 VPS tunnel and a **health-gated** reconnect watchdog redials only when the port is actually dead. Discovery that reshaped the design: v2's `vps-tunnel.sh --bg` supervisor has held the tunnel since 22 June and v2 needs it until cutover — so v3 shares politely (reuses healthy tunnels, never kills what it didn't start; shutdown reaps only our BatchMode-fingerprinted ssh, covering the watchdog-dies-first window-close ordering found in testing). 4-case live matrix passed (cold start / drop-respawn ~15s / worst-case teardown / v2 coexistence + handback). Residuals R-T1 (v2 supervisor churn while v3 owns the port — dissolves at cutover, add v2-supervisor retirement to B6's list), R-T2 (boot gap — LaunchAgent deferred), R-T3 (~30s half-open window).

4. **B7 piece 1 — durable logs + placement audit** (`b7_piece1_durable_logs_report.md`, commits `d0ef5d2` + `a4fb928`): app-wide namespaces to a daily-rotating `~/.bethub/logs/bethub-app.log` — **retained permanently (operator call)**; `FileAuditLogSink` JSONL gives contract §12.2 its durable substrate (**F8 CLOSED**), no-silent-loss fallback into the app log; live composition rewired off the vanishing memory sink. Test infra: conftest log-dir isolation (test runs can never pollute the real diary) + suite-wide caplog bridge (fixed the two pre-existing caplog tests the namespace widening broke). Behavioural red-before proven; suite 1358→1367; mock-proven end-to-end (real-default-path boot; scratch-path mock placement wrote a full audit line).

5. **B7 piece 2 — in-tool fault banner** (`b7_piece2_fault_banner_report.md`, commit `59dfcf1`): **operator call — phone alarm replaced by in-tool alert** (faults only matter in use; money path degrades hold-not-overpay; catch-up sweeps live-proven; caveat named: a dead unattended app can't self-report — accepted, phone alarm PARKED for unattended/30-account scale). Worker health registry (both workers report cycles/errors; monotonic 3×-interval staleness), `GET /api/health/workers` (never-started workers absent — OFF-by-design is not a fault; stream state degrades, never 500s), `HealthBanner` on every route (silent when healthy; plain-words on stall/error/feed-drop; lost-contact after two failed polls). 12 backend + 5 frontend tests; suites 1379/130; dist rebuilt.

6. **B7 piece 3 — daily money check** (`b7_piece3_review_pull_report.md`, commit `a4cdab3`): `uv run python -m ops.settlement_review [--date]` — read-only pull of a day's settlement/reconciliation decisions + §5.1b verification records from the durable log, joined `mode=ro` to the store for cycle grouping, DR-019 money, and the manual queue; every `paid_full` flagged for eyes. 4 tests; suite **1383**. **Live-run clean — and surfaced that S227's parked bet self-cleared** (`failed`/$0/`voided`) during the window: the S228 fix chain gave reconciliation its conclusive lapse signal and settlement stamped it. **Manual queue is empty; the operator's last housekeeping chore dissolved.** One-off: today's stamps predate the diary's 15:48 birth, so today's pull reads empty; full coverage from tomorrow.

## Findings / calls of note

- **Env-flag miss at the first window launch** — the flag only takes via the command-line launch; caught in-session by process-env inspection. Candidate future nicety: launcher prints worker flags at startup (parking-lot, cosmetic).
- **Cat 5 design calls made:** health-gated tunnel watchdog over blind respawn (coexistence-safe); permanent log retention (operator ratified); caplog bridge in conftest over per-test patches; worker-health staleness on the monotonic clock; never-started workers absent from the health feed.
- **Two operator scope calls recorded:** permanent diary retention; phone alarm → in-tool banner (parked, revisit trigger named).

## Standing-instruction adherence check

- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 2 first-action gate (hard)** — S230 first action CONFIRMED with operator via explicit options: **prep the go/no-go panel pack** (drafting only, nothing sent externally). ✅
- **Cat 3 git (S227 autonomy)** — five commits (`eef2fc2`, `d0ef5d2`, `a4fb928`, `59dfcf1`, `a4cdab3`), all green-tree, pushed, reported. ✅
- **Cat 4 live-integration classification** — settlement side upgraded to live-proven; B5 live-tested; B7 pieces classified implemented/mock-proven with passive live confirms named. ✅
- **Cat 5** — technical calls made without punting; operational calls (retention, alarm scope, S230 routing) surfaced as operator decisions. ✅

## Open items

**Closed in S229:** supervised settlement window ✅; B1 formal tick ✅; B5 ✅; B7 (all three pieces; F8 closed en route) ✅; S227 manual-queue chore (self-cleared) ✅.

**Carried to S230+** (full detail `current_state.md`): B6 cutover mechanics via the go/no-go panel (S230 preps the pack); BetLog badge items (now incl. "Won"/$0 on no-bets); phone alarm parked (revisit at unattended/scale); launcher worker-flag echo (cosmetic); B5 residuals R-T1..R-T3; B7 residuals (R-L1..R-L3, R-B1..R-B3, R-P1..R-P3); R-B partial-lapse `sizeCancelled` (confirm opportunistically); S1 leg-stake harden; stream subscription-trim; passive live confirms of the S229 builds at the next real launch (tunnel + diary + banner ride-along).

## Session close state

bethub-v3 at `a4cdab3` (= origin/main; tree clean; suite **1383** green; frontend 130 green, dist rebuilt). Both workers OFF (operator closed the app after the window). Live store: four S228 lays terminal `settled_won`/$0; S227 park terminal `voided`/$0; manual queue EMPTY. Machine state: v2's tunnel supervisor running and holding 8400 (as before the session). New artefacts: `b5_tunnel_hardening_report.md`, `b7_piece1_durable_logs_report.md`, `b7_piece2_fault_banner_report.md`, `b7_piece3_review_pull_report.md`; `cutover_readiness_map.md` status-refreshed (S229 header). `current_state.md` rotated; `v3_build_picture.md` updated; `.close_out_backups/SESSION_230_opening_prompt.md` generated (S229 prompt swept).

## Forward routing

**S230 first action (CONFIRMED with operator): draft the go/no-go panel pack** — the multi-agent cutover-readiness review commission (reviewer briefs, evidence pack, run mechanics for the operator). Drafting only; nothing sent to any external service; the operator reviews the pack before any panel runs. B6 scoping follows the panel per the agreed order.
