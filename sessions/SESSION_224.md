# SESSION 224 — Winner-less-hold triage CLEAN → settlement money-path fix chain COMPLETE → first supervised B2 live-proving window: lay-win settlement + full money-path proven live, and two real gaps surfaced (B3 match-reconciliation NOT-WIRED; Betfair entry lay-only)

**Opened:** 2026-07-05 15:00 ACST (headless/manual open; S224 guarded auto-first-action = triage the winner-less-hold hardening report).
**Closed:** 2026-07-05 16:26 ACST.
**Tool routing:** Claude Code session on the Mac (Bash + file tools) acting as the governance/Chat-equivalent session. The operator ran the live app supervised (worker ON) for a real B2 proving window during the session; three real Betfair lays were placed + settled live. **No bethub-v3 code touched in this session; HEAD byte-identical at `e2638fa` throughout.** Two rebuild-doc edits only (`cutover_readiness_map.md`).
**Governing DRs:** DR-032/033 (Betfair settlement spine / data-source roles), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-021 (Adelaide anchors), DR-019 (derived state on read). S189 (fixtures ≠ live-proven) was the operating discipline for the whole live window.

---

## Anchor
- Open ~15:00 ACST, close `TZ="Australia/Adelaide" date` → 2026-07-05 16:26 ACST. Same workday as S223 close was the prior evening (2026-07-03 22:42); this open is a new workday → but ran as a working session.

## Session shape
The guarded first action — triage the winner-less-hold hardening — passed **clean**, completing the settlement money-path fix chain. That unblocked the **first supervised live-proving window** for the auto-settlement worker (B2). The window did exactly what the S189 discipline promises: it proved the core engine **and** flushed out two real "built-but-not-live" gaps that green tests had hidden. Closed by turning the worker off and routing the next build (B3 match-reconciliation) as the S225 auto-action.

## What was delivered (in order)

1. **Triaged the winner-less-hold hardening report — CLEAN (S189 discipline: verified in code + ran tests).** Confirmed in `workflows/bet_entry/v1/settlement.py`: the `winner_count == 0 and loser_count >= 1` hold is present and correctly placed in **both** resolvers (after CLOSED / `market_voided` / `unexpected_state_count`, before runner-REMOVED self-void); reason code in the Literal; counter roll-ups fold the hold into the not-settled carry only. Ran the suite: **1289 passed / 1 xfailed**, settlement **115**, guard/void/worker **34**; Gossamer Glow re-proven SETTLED_WON. Verified the §2 material discovery (11 winner-less fixtures restored with spare-selection WINNER companions) weakened **no** assertions — the removed assertions in the dirty-tree diff belong to the S223 settled-signal cycle, not this task. Worker flag `settlement_worker: bool = False` (OFF by default). **→ settlement money-path fix chain COMPLETE.**

2. **Placings health-by-hour sweep — read, and the queued re-timing DROPPED.** The VPS sweep (`/tmp/health_by_hour_sweep.log`, 9 rounds every 3h) finished 2026-07-03 23:05 UTC. Finding: **Racing-API fetch health is flat across all 24 hours** — full fields, ~100–140ms, no gaps; the slot nearest the current 20:00-UTC backfill is among the *best*, not a bad patch. The only recurring blip (2 empty meets on 2026-05-30) is identical every round → a property of that date, not time-of-day. **No basis to re-time `racing-metadata-backfill.timer`** → dropped the queued re-timing task per re-validate-at-execution discipline.

3. **Opened the supervised B2 live-proving window (worker ON) — settlement engine PROVEN + gaps surfaced.**
   - **Gossamer Glow (stale backfilled lay) settled WON live.** The worker's first cycle (15:09) read the 2-day-old market live from Betfair (still served), settled the lay → SETTLED_WON. First real live settlement; the **lay-that-wins** watch-list case, ticked. Established that settlement writes **no DB audit event / no cash-flow row** — verified this is **by design** (DR-019 derived-state-on-read for balances; the settlement audit surface is the app log-line verification record), with a durable in-DB audit being the already-parked B7/F8 item.
   - **Hobart R9 lay (placed UNMATCHED intentionally) → surfaced B3.** Matched on Betfair but the store never reconciled (`matched_stake=0`, `reconciliation_attempts=0`), then settled → SETTLED_WON (correct *result*) with **$0 money** (wrong *value*). Root cause traced in code: **`run_reconciliation_pass` is built but NOT WIRED into the live app** (`ui/api/main.py` lifespan starts only streaming + the settlement worker; `settlement_worker_cycle` runs settlement + provisional passes, not reconciliation). **B2↔B3 dependency established:** the worker faithfully settles whatever stake the store holds → a stale stake yields a correct-direction / wrong-value settle. Bites any bet that **fills after placement**.
   - **Betfair entry modal is lay-only (`HedgeModal`).** Verified in the frontend — it's the Strategy-1 hedge tool (`postPlaceLay`, lay-liability caps, best-lay polling). Lay-only is **sufficient for the Scope-A cutover** (the Betfair leg IS the lay), so NOT a Strategy-1 blocker — but it **parks the BACK settlement live-proof** (worker's BACK mapping is built + unit-tested, unexercisable live until a back-entry path exists) and the operator wants a more flexible entry (future work).
   - **Casterton lay (MATCHED on entry, $3.08 @ 3.15) → FULL money-path PROVEN.** Store recorded the real matched stake at placement, settled → SETTLED_WON with the **money retained** ($3.08, not $0). The complete happy path proven end-to-end on a real bet: place → match → correct stake → settle with right result + right money. This race carried 1 removed runner naturally, but the lay-on-loser did **not** exercise the park/`paid_full` guard (that fires only on a bet ON the winner). **Bonus: B1 (lay placement) proven live** — three real lays placed + matched through a subscribed stream (B1 was flagged the single riskiest piece, never fired live).

4. **Updated `cutover_readiness_map.md`.** Added **B7** (live monitoring/observability: durable logs + heartbeat alarm + read-only review-pull; Claude as periodic reviewer, not the alarm). **Upgraded B3** with the not-wired match-reconciliation finding, the live evidence, and the B2-can't-be-fully-money-proven-until-B3 dependency. Added the **lay-only modal** to non-blockers (flexibility future work + parked BACK proof).

## Standing-instruction adherence check
- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — bethub-v3 byte-identical at `e2638fa`; no code touched in Chat. The worker was ON only for a **supervised** window (operator-launched, operator-watched) and is turned **OFF at close**. Three real small lays placed by the operator (real exposure, deliberate, low stakes). ✅
- **S189 (fixtures ≠ live-proven)** — the whole window operationalised it: green tests were proven *live*, and two "built-not-live" gaps (B3 not-wired, back-settle unexercisable) surfaced only under real placement. ✅
- **Cat 5 (division of labour)** — money-path/operational calls surfaced and made by the operator (leave-worker-on-then-off; force-vs-monitor rare shapes; next-build routing; modal-flexibility requirement). Technical calls (why $0, why not-wired, by-design audit) made as Claude calls in plain language. ✅
- **First-action gate (S200, hard)** — S225 first action **confirmed with operator**: draft the B3 match-reconciliation fix Code brief (auto-action).
- **Cat-2 sweep** — `cutover_readiness_map.md` materially updated (B3 upgrade, B7 add, modal note); `v3_build_picture.md` header + settlement stream updated; no `standing_instructions.md` change warranted (the force-vs-monitor principle is already covered by the live-proof plan §5).

## Open items
Pointer-only — full list in `current_state.md`.

**New / changed in S224:**
- Settlement money-path fix chain **COMPLETE** (winner-less-hold triaged clean).
- **B2 partially live-proven:** lay-win settlement + full money-path (matched-at-placement) proven live; guards + back + post-fill money still pending.
- **B1 (lay placement) proven live** (bonus).
- **B3 upgraded to NOT-WIRED** (match reconciliation) — blocks full money-proof; B2↔B3 dependency.
- **B7 added** (monitoring/observability).
- **Betfair modal lay-only** — flexibility future work; parks BACK live-proof.

**Closed in S224:**
- Winner-less-hold hardening triage (clean). ✅
- Placings health-by-hour sweep read → re-timing task dropped (no basis). ✅

**Carried to S225:**
- **Draft the B3 match-reconciliation fix Code brief** (first action, auto).
- Then B4 promo-seed (unlocks the full Safety-Net cycle proof); Betfair-entry flexibility scoping (back+lay).
- **Natural-monitoring watch-list** (needs B7 to be reliable): a lay that LOSES (SETTLED_LOST direction), the park/`paid_full` guards (winner-bet in a scratched-runner race / dead-heat), a void market.
- Cutover runway B5/B6.

## Session close state
Worker turned OFF at close (supervised window ended). `cutover_readiness_map.md` updated (B3/B7/modal). `current_state.md` rotated; `v3_build_picture.md` updated; `SESSION_224.md` written; S225 opening prompt generated with the confirmed auto-action; `.close_out_backups/` swept (holds only the S225 prompt). Three test bets left in the store by operator direction (remove once fully live-proven) — all settled/inert; the only real reconcile is the operator's own Betfair positions (account-side). **Bet-safety CLEAN** — worker OFF, no code in Chat, bethub-v3 at `e2638fa`; v2 untouched.

## Forward routing
**Confirmed with operator.** S225 first action = **draft the B3 match-reconciliation fix Code brief** (auto). Ground the "not-wired" premise by re-reading `ui/api/main.py` lifespan + `workflows/bet_entry/v1/reconciliation.py` before drafting; surface the **periodic-worker vs order-stream** design call. Then B4 promo-seed and the modal-flexibility scoping.
