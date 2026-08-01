# Session 213 — empty-runners contention fix commissioned + triaged (not yet defeated); settlement-worker up next with an outsourcing steer

**Opened:** 2026-07-01 14:55 ACST (headless runner, fast-path)
**Closed:** 2026-07-01 15:36 ACST
**Tool routing:** Desktop Commander (filesystem/process) for brief drafting, locking, and triage; no Code executed inside this chat session — Code ran out-of-session against the locked brief, operator relayed the confirmation-gate read-back and the final report into chat for review.
**Governing DRs:** DR-021 (Adelaide timestamps, every anchor), DR-027/DR-028 (referenced — two-database architecture, cited as the reason the contention finding matters), DR-033 (Betfair operational / Racing API analytical — this session analytical side throughout).

## Anchor
- Open: runner fast-path, 14:55 ACST (result stamp 14:53:23; S212 close was 14:44 — fresh, session-number match).
- Close: `TZ="Australia/Adelaide" date` → 2026-07-01 15:36 ACST.

## Pre-flight checks
- Runner opened on the fresh S213 result; presented straight per the Step 0 fast-path (no re-verify) — Code's triage of `placings_empty_runners_diagnosis_report.md` was already complete and correct at open.
- `.close_out_backups/` held only `SESSION_213_opening_prompt.md` at open (S212's stale prompt had already been deleted at S212 close).
- Root clean at open; no phantom files.

## Session shape
A single-arc session: pick up the carried empty-runners diagnosis triage, decide against a multi-agent review for this fix, commission and lock a surgical contention-fix brief, walk the operator through Code's confirmation gate, triage the resulting report, and — when the operator lost the technical thread mid-triage — recalibrate into a plain-language leadership mode for the rest of the arc. Closed on a forward-routing conversation that set S214's first action (settlement-worker diligence) with an explicit new steer to weigh Code/Cowork outsourcing given the money-path stakes.

## What was delivered

1. **Empty-runners diagnosis triage (carried from S212) — confirmed sound.** The runner's fast-path result held up: fork resolved correctly to §5.3 branch 3 (pacing rejected empirically, retry unsupported), the edit stayed in scope (one file, +46 lines, pure logging), and the ghost-row tripwire stayed clean (net race-row delta 0 across ~4,441 placings written). ~4,300 placings recovered as a side effect (deficit 40,987 → 36,650).

2. **Stale-file cleanup closed.** `.close_out_backups/SESSION_212_opening_prompt.md` verified stale and handed to the operator as an exact `rm` command (permanent-delete boundary held); operator confirmed deletion.

3. **Multi-agent Cowork review — declined for this fix, reasoning recorded.** Checked `governance.md`'s multi-agent review pattern against this specific decision: the documented trigger is the pre-W16 cutover go/no-go, not a routine surgical fix; the fix itself (decouple fetch-from-write, single file, cleanly reversible, no schema touch) doesn't meet the "high reversal cost / high blind-spot risk" heuristic. Recommended a normal locked brief instead; operator agreed ("proceed with your rec").

4. **Contention-fix brief drafted + LOCKED.** `placings_empty_runners_contention_fix_brief.md` (103 lines, 11,572 bytes, sha256 `3666d66c…`) — restructures `sync_day()` in `subscription/racing_api.py` to fetch a full date's meets before writing any of them, closing the fetch/write interleaving the diagnosis isolated as the contention trigger. Scoped deliberately narrow: decoupling only (parked the collector-idle-window alternative), transaction-wrap left as a "do if clean" call for Code, second file (`backfill_race_metadata.py`) read-only unless a named incompatibility surfaced. Five explicit drafting calls surfaced to the operator at hand-off; operator locked as-drafted ("go").

5. **Ready-to-paste Code commissioning prompt produced** — the wrapper distinct from the brief itself (per this project's standing pattern), naming the read-and-confirm gate, scope, and hard limits. Operator ran it against Code out-of-session.

6. **Code's confirmation-gate read-back reviewed and approved.** Anchor/drift check clean, §5.2 (`run_backlog_pass()` compatibility) correctly found compatible with no second-file edit needed, and the no-transaction-wrap decision was the right call for the right reason (would have required editing `storage/database.py`, outside the §9 authorized anchors). Gave the go-ahead to proceed.

7. **Fix executed + triaged — landed clean, mode NOT shown defeated.** `placings_empty_runners_contention_fix_report.md`: the restructure is correct, isolated (byte-exact reversal to session-start sha), and behaviour-preserving (identical return-dict/counters, `run_backlog_pass()` unaffected, second file byte-identical at close). Ghost tripwire stayed clean (0 delta). But the verification burn still walled 6 of 7 dates on the empty-runners mode — same shape as the pre-fix burn — because it ran inside a genuinely heavy collector window (39,279 snapshots/min). Code's own finding: `run_backlog_pass` only pauses 0.2s between dates, while the mode resets in ~2s of write-idle, so date N's fetch can start inside the degraded window date N−1's write burst induces — a specific, cheap-to-test hypothesis about the residual cause, not more architecture.

8. **Routing decided: let tonight's nightly run be the next data point.** Rather than forcing a second manual burn into another possibly-busy window, the 05:30 ACST nightly run gives a free, unforced test under normal collector load. Clean → fix likely works, today was unlucky timing. Still walls → real evidence for the 0.2s inter-date-pacing hypothesis, pointing at a small follow-up (bump the inter-date pause) rather than more architecture.

9. **Operator clarification: rate limit vs contention mode are unrelated.** The operator questioned whether the 5 req/sec ceiling was really unlimited as previously discussed. Confirmed: yes, the rate ceiling is settled and unrelated to this mode — fetch-only traffic is immune at nearly double that rate. The empty-runners mode is our own two local processes (backfill + live collector) contending over the same `capture.db` file, not a provider-side throttle. This was a genuine confusion point, now resolved.

10. **Operator requested a shift in working mode.** The operator lost the technical thread mid-triage and asked Claude to lead fully on architecture/technical calls going forward on this arc, surfacing only operator-relevant decisions (money, risk, priorities, timing) rather than technical detail. Acknowledged and will be honoured — no standing_instructions.md edit made (this reinforces existing Cat 5 division-of-labour practice rather than introducing a new rule; flagged here for visibility, not codified as a new instruction this session).

11. **S214 first action set: settlement-worker diligence, with an outsourcing evaluation folded in.** Settlement-worker (IOU + manual-match-to-lay) is next on the build path to W16 cutover — the first money-path build item in this stretch, so standing practice is diligence-first before any Code brief. The operator added a new instruction for this pass specifically: because it's money-path and "has to be really, really solid," S214 should explicitly weigh whether portions of the diligence can be outsourced to Code (better positioned to review the codebase directly) and/or a Cowork multi-agent review (parallel granular checks across the application) rather than Claude Chat doing all of it solo. Confirmed with operator explicitly ("Please proceed").

## Standing-instruction adherence
- Desktop Commander as default for all filesystem/process ops — honoured.
- DR-021 Adelaide timestamps throughout — honoured.
- Brief-drafting ritual (grounded anchors from the diagnosis report + brief, universal spine, explicit-calls surfaced, operator lock before hand-off) — honoured.
- Permanent-delete boundary (Claude does not hard-delete; verify + hand commands to operator) — honoured.
- Code read-and-confirm gate reviewed before go-ahead — honoured.
- Multi-agent review governance heuristic — honoured; reasoned explicitly against `governance.md`'s stated trigger rather than a gut call.
- Money-path diligence-first discipline — carried forward into S214's first action as confirmed.

## Open items
Pointer to `current_state.md`. New this session:
- **Placings burndown — check tonight's 05:30 ACST nightly run.** Not gating S214's first action; check at next natural opportunity. Clean run → fix works, no further brief. Still walls → weigh bumping the inter-date pause in `backfill_race_metadata.py` (small pacing-constant change, not a new architecture brief).
- **Settlement-worker diligence (S214 first action, CONFIRMED)** — money-path, diligence-first; explicitly weigh Code/Cowork outsourcing for parts of the review given the stakes.
- **Operator working-mode steer** — lead fully on technical/architecture calls, surface only operator-relevant decisions. Carried as working practice, not a standing_instructions.md edit this session.

Carried unchanged: promo-seed → W16 cutover; Data Foundation harvest (parallel, not gating); full-backlog burn (still downstream of the contention resolution — now further gated on tonight's data point); fault-B / `race_date` identity (parked, tripwire clean); Cowork sub-agent review → pre-W16 cutover go/no-go (unchanged — this session's declined-review decision was about the placings fix specifically, not the cutover review itself).

## Open items out
- Empty-runners diagnosis triage (S213's carried first action) — CLOSED, routed through to a fix brief, execution, and triage.
- Stale `.close_out_backups/SESSION_212_opening_prompt.md` — CLOSED (operator-deleted).
- Multi-agent review timing question for the contention fix — CLOSED (declined, reasoning recorded against `governance.md`).
- Operator's rate-limit-vs-contention confusion — CLOSED (clarified).

## Session close state
- Rebuild root clean; new artefacts `placings_empty_runners_contention_fix_brief.md` (LOCKED) + `_report.md` (EXECUTED, triaged) present.
- `.close_out_backups/` → `SESSION_214_opening_prompt.md` only, after this close.
- `current_state.md` rotated to the S213 close.
- `v3_build_picture.md` untouched — no formal build stream moved this session (settlement-worker diligence hasn't started; its next-milestone label is unchanged from S210's close). Placings recovery continues to be tracked in `current_state.md`, not the build picture, per the S212 precedent.
- `standing_instructions.md` untouched — no instruction edits this session (the operator's working-mode steer is carried as practice, not codified).

## Forward routing
**S214 first action (CONFIRMED with operator — "Please proceed") = settlement-worker diligence pass.** Diligence-first per money-path standing discipline: ground in the real, current codebase before drafting any brief. New this session — explicitly weigh, as part of that diligence, whether portions of the review can be outsourced to Code (out-of-session codebase review, better positioned than Chat to inspect the app directly) and/or a Cowork multi-agent review (parallel granular checks across the application), given this is the first money-path build item and needs to be maximally solid before it reaches Code. No hold expected — this is scoping/diligence work Claude leads directly.
