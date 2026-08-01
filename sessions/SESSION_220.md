# SESSION 220 — Settlement live-proving plan drafted (headless) + operator walkthrough; review-loop confirmation mechanism added; market-type precision gated on Strategy 4

**Opened:** 2026-07-02 17:25 ACST (headless runner — auto-executed the first action)
**Closed:** 2026-07-02 19:05 ACST
**Tool routing:** headless runner (open ritual + drafted the settlement live-proving plan); then Chat (interactive walkthrough of the plan with the operator; two plan edits; close). No code touched; no VPS access; settlement flag NOT flipped.
**Governing DRs:** DR-032 (Betfair settlement spine), DR-033 (settlement Betfair-only / placings analytical), DR-027/028 (two-DB boundary), DR-030 (module boundaries), DR-021 (Adelaide anchors).

---

## Anchor
- Open (runner): 2026-07-02 17:25 ACST — headless runner opened S220, drift-check clean, drafted the plan, saved result to `~/.bethub-cycle/results/SESSION_220_opening_prompt_result.md`.
- Close: `TZ="Australia/Adelaide" date` → 2026-07-02 19:05 ACST.

## Pre-flight / pre-close checks
Root clean; no v2 phantom files. Drift-check on the S219 close was clean (current_state / SESSION_219 / v3_build_picture all stamped 17:03). New artefact this session: `settlement_liveproof_plan.md`. `.close_out_backups/` held only the S220 prompt at open.

## Session shape
Auto-open (runner) drafted the settlement live-proving plan, then the operator engaged interactively for a section-by-section walkthrough, made one deferral decision, and asked to formalise a shared confirmation mechanism. No live action taken — the settlement flag stays OFF.

## What was delivered

1. **Settlement live-proving plan drafted (`settlement_liveproof_plan.md`) — headless.** The runner produced the operator run-book to take the settlement worker from *built-unproven* to *live-proven* (cutover blocker B2). Plain-language, tear-off checklist: preconditions (live mode, small exposure, supervised); the flip (`BETHUB_SETTLEMENT_WORKER=on` → restart → confirm bring-up); what to watch (clean self-settle; the §5.1b verification records — `parked` / `fallback_flagged` / `paid_full`, with `paid_full` the one to check hardest; the manual park queue; the no-silent-overpay invariant); success criteria (real window, N settlements incl. ≥1 awkward case, every `paid_full` checked — green fixture tests explicitly NOT sufficient per S189); rollback (flag OFF → manual, harmless); deferred follow-ups. Bet-safe: governance drafting only, flag not flipped.

2. **Operator walkthrough completed** (section-by-section, plain language). Operator now holds how the worker behaves (park-not-overpay), how to flip it, what to watch, and how to roll back.

3. **Decision — market-type precision gated on Strategy 4.** The one judgement call surfaced: the narrow place-market over-pay corner (§4d — a place-market winner with none of the usual "place" signals could be paid full when a small reduction should apply). Since it is a **place-market (Strategy 4)** risk and cutover proving is **Strategy 1 (win markets)**, the corner cannot arise in the proving window. **Operator agreed: do not hold up proving; prove live on Strategy 1 now; the market-type-precision fix (the "one more authorised line") is explicitly gated — required before Strategy 4 / place-market betting enters v3, not before Strategy-1 proving.** Recorded in the plan (§7).

4. **Review-loop confirmation mechanism added to the plan (§5b).** The operator asked whether they can review bet pathways/groupings with Chat to confirm the criteria. Yes — formalised as the confirmation mechanism: each review pass is **read-only** — Chat pulls the worker's verification records (app logs) + settled/parked states (operational store), groups them **by cycle** (insurance bet + free bet + conversion as one unit, per the standing analysis convention), confirms clean settles / deserved parks / every `paid_full` correct / no silent overpay, and keeps a running tally against the five criteria across days (flagging when a path hasn't been exercised, so it's never called proven early). **The read-only "review pull"** (one command → review-ready per-cycle summary) is built + validated on the **first real review pass** against real records, not guessed up front. Boundary: read-only throughout — Chat never touches a bet, a settlement, or the flag.

## Standing-instruction adherence check
- **DR-021** — open (17:25) + close (19:05) Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — governance/documentation only; settlement flag NOT flipped; no settlement/Betfair/money/live path touched; no VPS access; no code touched. ✅
- **Cat 1 (walkthrough cadence)** — section-by-section, plain gambling language, one decision surfaced (the place-market corner) with a recommendation, not punted. ✅
- **Cat 5 (division of labour)** — the deferral decision kept as the operator's call; the review loop fenced read-only. ✅
- **S189 taxonomy** — settlement worker classified built-unproven; the plan's success criteria enforce "proven not just green tests." ✅
- **First-action gate (S200, hard)** — S221 first action confirmed with operator: **execute the open process + provide a high-level dot-point summary of the agreed cutover plan** (self-contained, auto-executes). ✅
- No standing-instruction edits → no Cat-2 sweep.

## Open items
Pointer-only — full list in `current_state.md`.

**New / changed in S220:**
- **Settlement live-proving plan drafted** (`settlement_liveproof_plan.md`) + **review-loop confirmation mechanism** added. Worker still OFF — proving is the operator's between-session action.
- **Decision:** market-type precision **gated on Strategy 4** (not needed for Strategy-1 proving).

**Closed in S220:**
- Settlement live-proving plan draft + operator walkthrough. ✅

**Carried to S221:**
- **Execute the open process + high-level dot-point cutover-plan summary** (first action).
- **Placings 05:30 run-check** (companion, time-gated to 2026-07-03 ~05:30 ACST): read the outcome; if it still walls → commission the fetch-only health-by-hour sweep (weigh 2–3 healthy windows/day); if it drains → monitor.
- **Settlement live-proving** (operator flips the flag when ready; then the shared read-only review passes begin — build the review pull on the first pass).
- Cutover runway B2→B3→B1→B4→B5→B6; promo-seed; W16 mechanics; re-confirm interim-worked pieces.

## Session close state
Root clean (`settlement_liveproof_plan.md` present; no phantom files). `.close_out_backups/` swept to the S221 prompt only. `current_state.md` rotated; `v3_build_picture.md` header updated (settlement stream: live-proving plan drafted, B2 run-book ready, worker still OFF). `standing_instructions.md` untouched. **Bet-safety CLEAN** (governance only; flag not flipped; no code/VPS touched). bethub-v3 untouched; the racing-data-capture VPS repo still carries the S219 FIX 1 change (awaiting the 2026-07-03 05:30 run signal).

## Forward routing
**Confirmed with operator.** S221 first action = **execute the open process (open ritual) and provide a high-level dot-point summary of the agreed cutover plan** (the B1–B6 runway + Strategy-1-parity scope) — a self-contained governance quick-start, auto-executed by the runner. Companion (time-gated): check the 2026-07-03 05:30 ACST placings run and, if it still walls, commission the fetch-only health-by-hour sweep; else monitor. Then: settlement live-proving (operator flag-flip → shared read-only review passes), and the cutover runway B2→B3→B1→B4→B5→B6.
