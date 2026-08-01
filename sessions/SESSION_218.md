# SESSION 218 — Settlement build report TRIAGED (clean, OFF-by-default); placings backfill drop VERIFIED real; recovery approach escalated to a comprehensive Code review

**Opened:** 2026-07-02 12:42 ACST (headless runner; guarded first action)
**Closed:** 2026-07-02 13:50 ACST
**Tool routing:** Chat (guarded backfill investigation [read-only VPS/capture.db]; settlement build-report triage; re-timing brief draft; pivot to a Code-review commission + prompt drafting; close). No code touched in Chat; no VPS writes; settlement flag NOT flipped.
**Governing DRs:** DR-021 (Adelaide anchors), DR-027/028 (two-DB boundary + single integration point), DR-030 (module boundaries), DR-032/033 (Betfair settlement spine / data-source roles — settlement Betfair-only, placings analytical).

---

## Anchor
- Open (runner): headless runner opened S218; first action GUARDED on Code's settlement build report.
- Close: `TZ="Australia/Adelaide" date` → `2026-07-02 13:50 ACST`.

## Pre-flight / pre-close checks
Root clean at open and close — no v2 phantom files (`system_snapshot.md` / `context_index.md` / `STATUS.md` / `CLAUDE.md` all absent). Drift-check on the S217 close was clean: `current_state.md` stamped 2026-07-02 12:38 ACST; `sessions/SESSION_217.md` present; `v3_build_picture.md` stamped 2026-07-02 12:38 ACST. `.close_out_backups/` held only the S218 opening prompt at open. bethub-v3 anchor `e2638fa` (Code built out-of-session against it).

## Session shape
Opened guarded: Code's settlement build report was **not present at open**, so the guard fell through to the read-only placings-backfill look carried from S215/S216 (VPS access re-verified first — ssh-agent holds `tim@racing-vps`, VPS reachable). Mid-session Code's build report landed and was triaged. The session then moved to the next queued item (placings backfill re-timing), drafted a surgical brief for it, but on the operator's call **escalated the whole placings-recovery problem to a comprehensive Claude Code Plan-Mode review** rather than shipping a tenth surgical patch.

## What was delivered

1. **Placings-backfill deficit drop VERIFIED as real fills (S215 caveat resolved).** Read-only decomposition of the live capture.db (`mode=ro`) established the ~6.1k `recoverable_deficit` drop (41,633 → 35,718; now ~36,033) is **genuine finish-position fills, not a metric-scope / 404-reclassification artifact**: `exhausted` dates = 0 (RAW deficit == RECOVERABLE deficit — nothing hidden behind exclusions); 8,482 in-scope filled runners carry `races.updated_at` within 3 days (6,528 within 2 days), matching the ~5,915 burndown drop; fills carry `results_source = subscription` (Racing API). The fills came via the **normal subscription sync**, not the recovery pass (which logged `placings=0`). Bankable. Written up in `placings_backfill_deficit_verification_report.md`.

2. **`post_retry_truncated` wall characterised; retire-vs-chase = CHASE.** The wall is the transient collector-contention degradation (S214 proved fetch-only re-fetch returns FULL runners; not runner-less). The recovery pass is scheduled `OnCalendar 05:30 Australia/Adelaide` (single nightly run) and walls 6/6 there because that window overlaps a heavy collector burst (~15k `bookmaker_snapshots` rows/min observed midday). Verdict: chase, not retire — the data is fetchable and `exhausted=0` reflects nothing abandoned; the deep old March/April dates (top-deficit ~6.1k runners) are the recovery pass's real job since the normal sync never reaches back to them.

3. **Settlement-worker BUILD report TRIAGED — CLEAN, matches the go-ahead.** Code shipped `settlement_worker_build_report.md`. Triaged against the go-ahead (Option (1)) + LOCKED brief: anchor `e2638fa` unchanged; the ONE authorised additive `_translation.py` line landed exactly (`"adjustment_factor": r.get("adjustmentFactor")`, :573; no second field lifted); Option C guards market-type-aware (WIN parks ≥2.5%, PLACE parks any >0, dead-heat on `dead_heat_count>0`), gated in **both** resolvers (PENDING :689 parks→PROVISIONAL; PROVISIONAL :918 holds, never un-parks); Option B fallback fires on unreadable factor (`None`) — parks, never a silent full payout; §5.1b `RemovedRunnerVerificationRecord` emitted on every removed-runner WINNER decision (park + paid-full + fallback); tests **1246 passed, 0 failed, +44 net, no regressions**; flag **OFF by default** (`BETHUB_SETTLEMENT_WORKER`, gated additionally on `betfair_mode==live`); flag NOT flipped. **S189 bucket: implemented-and-wired, NOT live-proven** (all tests fixture/in-memory). One decision-for-later surfaced: **market type is derived bet-side** (`_is_place_market`: Strategy-4 tag OR "place" in market name) because Option (1) only authorised the `adjustmentFactor` lift, not `marketType`; it errs to **over-park (manual review), never mis-pay**; the narrow residual gap only bites once Strategy 4 is live (it isn't). Named follow-up if precise gating wanted: a second authorised additive line lifting `marketDefinition.marketType`.

4. **Settlement piece confirmed build-complete — only live testing remains.** No further build work queued; optional deferred follow-ups (market-type precision, persisted audit table, threshold calibration, free-bet-credit + auto-re-settlement) all remain deferred, none required. Live-enable is the operator's call (flip the flag in live mode).

5. **Placings-recovery re-timing brief drafted, then the approach ESCALATED to a comprehensive Code review.** Initial next-action was a surgical re-timing fix-brief (move the nightly run to an empirically-chosen quiet window; the earlier S211 move to 05:30 ACST was an unverified guess that landed in a busy window). On the operator's call — recognising nine successive surgical fixes each hitting a fresh wall — the work was reframed: rather than a tenth patch, commission a **Claude Code Plan-Mode (read-only) review** at the **widest scope** — (a) true root cause + the fix that will hold, and (b) whether recovering the ~36k old placings is worth it now (recover / retire / defer), given analytics is coming into view. Code to use **sub-agents** across three surfaces (VPS codebase, VPS service/scheduler/DB-contention setup, Racing API + Betfair behaviour). A paste-ready Code review prompt was produced (held in the plan file); the re-timing draft is demoted to a candidate input. **No surgical brief was locked.**

## Standing-instruction adherence check
- **DR-021** — open (12:42) and close (13:50) both Adelaide-anchored. ✅
- **Cat 4 (bet-safety / boundary)** — backfill investigation read-only (capture.db `mode=ro`, no writes, no copy; no Racing-API fetch probe fired); settlement triage read the report only (flag NOT flipped, no money/Betfair/live path touched); DR-033 analytical/operational split honoured. bethub-v3 not touched; v2 not touched. ✅
- **Cat 5 (division of labour)** — the settlement live-enable and the chase-vs-retire question kept as operator calls; the recovery-approach escalation was the operator's decision, surfaced with a recommendation, not taken unilaterally. Dev-lead calls not enumerated for review. ✅
- **Inventory-first cadence on the settlement report** — full triage inventory done; only operator-relevant items surfaced (build clean/OFF; the market-type decision-for-later) in plain language. ✅
- **First-action gate (S200, hard)** — S219 first action confirmed with operator: **check for Code's placings-recovery review report; triage if present, else HOLD** (Code runs the review out-of-session). ✅
- No standing-instruction edits → no Cat-2 sweep.

## Open items
Pointer-only — full list in `current_state.md`.

**New / changed in S218:**
- **Settlement build report TRIAGED clean** — implemented-and-wired, OFF-by-default, NOT live-proven; only live testing remains (operator flips the flag). Decision-for-later: market-type precision (one more authorised line) — not urgent, only matters once Strategy 4 is live.
- **Backfill drop VERIFIED real** (~6.1k = genuine fills; deficit ~36k; exhausted=0; chase-not-retire).
- **Placings-recovery approach ESCALATED** to a comprehensive Code Plan-Mode review (widest scope; sub-agents; codebase + VPS + APIs). Re-timing surgical brief NOT locked (demoted to candidate input).

**Closed in S218:**
- Settlement build-report triage. ✅
- Placings backfill deficit-drop verification + `post_retry_truncated` characterisation + retire-vs-chase. ✅

**Carried to S219:**
- **Triage Code's placings-recovery review report** when it lands (first action, guarded — HOLD if not present; Code runs it out-of-session in Plan Mode).
- Settlement live-testing (operator flips the flag when ready).
- Promo-seed; W16 cutover scoping (no rush per operator).
- **Analytics layer — begin thinking/scoping soon** (operator flagged S218).
- Data Foundation harvest (parallel, not gating).
- Cowork sub-agent review → pre-W16 go/no-go.

## Session close state
Rebuild root clean (no phantom files; `settlement_worker_build_report.md` + `placings_backfill_deficit_verification_report.md` present). `.close_out_backups/` swept to the S219 opening prompt only. `v3_build_picture.md` header updated (settlement stream → build-triaged-clean, OFF, live-test-pending; placings-recovery stream → comprehensive-review-commissioned). `current_state.md` rotated. `standing_instructions.md` untouched. No code touched in Chat; **bet-safety CLEAN** (read-only backfill; settlement triage read-only; no flag flip; no VPS writes; settlement worker remains OFF-by-default — nothing mis-settling live). bethub-v3 tree at `e2638fa` (dirty per convention from Code's out-of-session build; not touched in Chat).

## Forward routing
**Confirmed with operator.** S219 first action = **check for Code's placings-recovery review report; triage if present, else HOLD** (Code runs the widest-scope Plan-Mode review out-of-session, using sub-agents across the VPS codebase, VPS setup, and the APIs). Then, in order: settlement live-testing (operator's flag-flip, between-session); promo-seed → W16 cutover scoping; begin analytics-layer scoping soon (operator flagged). Data Foundation harvest parallel, not gating.
