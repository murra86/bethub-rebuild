# SESSION 223 — Settlement money-path: correctness build triaged → live-proof surfaced the settled-signal gap → review-first reconciliation → batched read-path fix → last-tail hardening (worker OFF throughout)

**Opened:** 2026-07-03 19:31 ACST (manual open — operator ran the S222-commissioned build supervised, then opened S223).
**Closed:** 2026-07-03 22:42 ACST.
**Tool routing:** Claude Code background session on the Mac (Bash + file tools). Five out-of-session Code cycles this session (the S222-commissioned settlement-correctness build; the settled-signal fix; the read-only reconciliation review; the batched read-path fix; the winner-less-hold hardening) — each triaged in-session **except** the last (hardening), deferred to S224 open per operator. **No code touched in Chat. bethub-v3 HEAD byte-identical at `e2638fa` throughout; no git write ops. Settlement worker OFF the entire session.**
**Governing DRs:** DR-032 (Betfair settlement spine), DR-033 (settlement Betfair-only), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-021 (Adelaide anchors). S189 (fixtures ≠ live-proven) was the direct substrate for the whole arc.

---

## Anchor
- Open: 2026-07-03 19:31 ACST. Close: `TZ="Australia/Adelaide" date` → 2026-07-03 22:42 ACST. Same workday as S222 close (19:24).

## Session shape
The S222-designed settlement fix went from "built" to "money-path fully closed" in one session — but the road was the S189 lesson made vivid. The correctness build (Option A pending + LAY inversion) triaged clean, but the **first real live-worker run** surfaced that the worker could never *finish* a settlement (a settled-signal read gap). Rather than fix-and-relaunch serially (the operator explicitly flagged not wanting that rabbit hole), the arc pivoted to **review-first**: a read-only reconciliation of the whole settlement read path found four more gaps in one pass — including a **silent dead-heat over-settle** — and the batched fix's adversarial build caught **two regressions in Chat's own fix brief** before they shipped. Closed by hardening the last theoretical money-path tail.

## What was delivered (in order)

1. **Triaged the settlement-correctness build (S222-commissioned) — CLEAN.** `settlement_correctness_fix_report.md`: Option A PENDING stamp on the hedge builder only; the one-row backfill of the repro LAY (`bet-df31ffcd…`, Gossamer Glow); LAY inversion in **both** resolvers; soft-book left manual. Verified in code (gate/inversion present, worker flag False, HEAD unmoved) + ran the settlement tests (115 green). Bench re-prove settled the real captured read to SETTLED_WON (+$4.84).

2. **Supervised live-proof attempt → the settled-signal gap.** Operator launched the app live with `BETHUB_SETTLEMENT_WORKER=on`; the bet sat `pending` across 10+ worker cycles. Read-only diagnosis: the resolver's Step-4 `settled_time is None` gate (`settlement.py:672`/`:895`) can never pass, because the settlement read translates to Betfair `listMarketBook`, which returns **no** `settledTime` — so every bet is held pending forever. Confirmed the live app reads the same `data/bethub.db` (launcher sets no DB override) and Gossamer Glow was the only pending bet.

3. **Settled-signal fix — brief + report, triaged CLEAN.** `settlement_settled_signal_fix_brief.md` → `…report.md`: readiness re-keyed off `market_status == CLOSED` + a resolved runner (`runner_not_yet_resolved` guard), the `settled_time` gate removed from both resolvers, `_settled_time_iso` None-tolerant helper, fixtures fixed to the real (no-`settledTime`) shape. Verified in code + 119 tests green; real capture still settles SETTLED_WON.

4. **Review-first reconciliation (read-only) — the pivot that paid off.** On the operator's "will we just hit another snag" question, ran a read-only reconciliation of the whole settlement read path across all 9 settlement shapes: `settlement_readpath_reconciliation_review_brief.md` → `…report.md`. **Four findings, all in one function** (`_translate_market_settlement`): **F1 (money-path, HIGH)** a dead-heat winner silently over-settles (`dead_heat_count` hardcoded None; real dead-heat = ≥2 WINNER, never counted → the guard park is dead code on a real read); **F2** a status-less runner defaults to WINNER (unsafe direction); **F3** market-void never auto-VOIDs (phantom `marketDefinition.marketVoided`); **F4** `REMOVED_VACANT`/`HIDDEN` freeze the whole market. **Cleared:** the `paid_full` / Rule-4 materiality decision — verified sound (per-runner 2.5% test; `adjustmentFactor` is a percentage). Every dead-heat "park" test had injected the count directly, bypassing the translation — the S189 trap exactly.

5. **Batched read-path fix — brief + report, triaged CLEAN; adversarial pass caught two brief regressions.** `settlement_readpath_batched_fix_brief.md` → `…report.md`: F1–F4 + two cosmetic ride-alongs, all inside `_translate_market_settlement`, no resolver/enum edit. **Operator decision: F3 stays MANUAL** (no auto-void built; abandonments hold for manual). Code's adversarial review caught **two regressions in Chat's literal brief**: F1's bare `>= 2` would have frozen every place-market winner (fixed via Betfair's real `numberOfWinners` field); F4's naive REMOVED-map would have over-parked winners in a vacant-box race (fixed via a `0.0` non-deducting factor). Both money-safe, translation-only. Full suite 1277 passed; verified in code + ran 135 settlement tests green.

6. **Winner-less-hold hardening — the last tail (built, NOT triaged — S224 first action).** Code surfaced one residual: a theoretical CLOSED market with ≥1 LOSER and zero WINNER (a void shape Betfair doesn't actually emit) would settle a losing bet wrong. Operator chose to close it. `settlement_winnerless_hold_hardening_brief.md` → `…report.md`: both resolvers now hold (`market_winnerless_hold`) when `winner_count == 0 and loser_count >= 1`, with the all-REMOVED case excluded so real voids still self-VOID. Report claims full suite **1289 passed**. **Per operator: this report is NOT triaged in S223 — triage is the S224 guarded first action.**

## Standing-instruction adherence check
- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — worker OFF the entire session; no code touched in Chat; bethub-v3 byte-identical at `e2638fa`; the only DB write was the S222 one-row backfill (still `pending`, reversible, backup `data/bethub.db.bak-S222-20260703T194225` stands); a real Betfair session was opened **supervised** for the live-proof attempt then stopped. ✅
- **Cat 5 (division of labour)** — money-path calls surfaced and locked by the operator (F3 manual; the review-first-vs-go-live call; closing the last tail); technical shape (readiness predicate, `numberOfWinners`, the `0.0` factor) made as Claude/Code calls. ✅
- **S189 (fixtures ≠ live-proven)** — the whole arc is the S189 lesson; the batched fix's worth is the **raw-`listMarketBook` translation-layer tests**, not more resolver fixtures. New Cat-4 standing instruction added this close ("sweep the class in one pass before serial fixes"). ✅
- **First-action gate (S200)** — S224 first action confirmed with operator: **triage the winner-less-hold hardening report** (guarded/auto on open).
- **Cat-2 sweep** — one standing-instruction added (see above); `v3_build_picture.md` header updated (settlement money-path moved).

## Open items
Pointer-only — full list in `current_state.md`.

**New / changed in S223:**
- Settlement money-path **fully built** across four cycles; **triage of the final hardening is S224's first action** (worker stays OFF until that triage is clean).
- After a clean hardening triage: settlement money-path is closed → open the **supervised live-proving window** with the watch-list.

**Closed in S223:**
- Settlement-correctness build triage; the settled-signal gap (found + fixed); the read-path reconciliation (4 gaps found); the batched read-path fix; F3 decided manual. ✅

**Carried to S224:**
- **Triage the winner-less-hold hardening report** (first action, guarded/auto).
- **Live-proving watch-list** (only after the fix chain is triaged clean + worker turned on for a supervised window): a real dead-heat, a real void/abandonment, a greyhound vacant box, a place-market winner, a lay-that-wins — all correct-by-construction now, each to be confirmed the first time it occurs live. Plus: confirm `numberOfWinners` is present on the first real settled read.
- **Placings health-by-hour sweep map** (companion, ~08:30 ACST 2026-07-04) → commission run re-timing.
- Cutover runway B1/B3/B4/B5/B6; promo-seed; re-confirm interim pieces.
- **Optional maximum-certainty move** (operator-flagged, not scheduled): a one-pass reconciliation of the P&L / balance-derivation maths before leaning on the live window.

## Session close state
Root: five S223 brief/report pairs present; `settlement_winnerless_hold_hardening_report.md` present (untriaged by design). `current_state.md` rotated; `v3_build_picture.md` header updated; `standing_instructions.md` swept (one Cat-4 add); `SESSION_223.md` written; `.close_out_backups/` holds only the S224 opening prompt. **Bet-safety CLEAN** — worker OFF, no code in Chat, bethub-v3 byte-identical at `e2638fa`, operational DB carries only the reversible S222 backfill; v2 untouched. App was launched live (supervised) then stopped; relaunch worker-OFF unless a supervised proving window is intended.

## Forward routing
**Confirmed with operator.** S224 first action = **triage the winner-less-hold hardening report** (guarded — if present, which it is; auto on open). If clean → the settlement money-path fix chain is complete and the worker is unblocked for a supervised live-proving window (per `settlement_liveproof_plan.md`) with the S223 watch-list. Companion (time-gated ~08:30 ACST 2026-07-04): the placings health-by-hour sweep map → commission run re-timing.
