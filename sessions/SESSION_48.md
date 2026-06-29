# Session 48 — Fix 6 triage + Fix 7 design brief drafted (merge-mechanism scoping probe + Fix 5 §7b consolidation)

**Opened:** 2026-05-01 17:21 ACST (Friday late afternoon, +9 min after Session 47 close).
**Closed:** 2026-05-01 17:44 ACST (~23 min, single calendar day, same workday as Session 47).
**Tool routing:** Claude Chat.
**Governing DRs invoked:** DR-029 (active arc — Fix 6 triage + Fix 7 design brief drafting against §2.1 surgical-fix arc); DR-027/028 (named at open, not invoked substantively — merge work is intra-`capture.db`); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 17:21 ACST` at open and `2026-05-01 17:44 ACST` at close. Same workday as Session 47 close (17:12 ACST, +9 min) — calendar-calibrated short recap delivered.

## Pre-flight checks

- **Rebuild folder root at open:** 12 .md files plus expected directories. `.close_out_backups/` contained `SESSION_48_opening_prompt.md` only (per Session 47 close). No phantom files.
- **Drift-check Session 47 close-out:**
  - ✅ (a) `current_state.md` last-updated `2026-05-01 17:12 ACST` matches Session 47 close.
  - ✅ (b) `sessions/SESSION_47.md` exists, 150 lines, non-empty.
  - ✅ (c) `v3_build_picture.md` last-updated `2026-05-01 17:12 ACST` matches Session 47 close.
- **`dr029/2_1_race_data/` at open:** confirmed `surgical_fix_6_report.md` (435 lines) and `fix_6c_proposed_merge.json` (1.6 MB / 3,249 records) had landed — Code finished out-of-session between Session 47 close and Session 48 open (Code wall-clock ~9 min, well inside brief's 60-90 min envelope).
- **V3 build picture inline:** skipped at open — no stream state moved since Session 47 close.
- **Open-items delta:** 9-minute gap; no items moved. Skipped silently.

## Session shape

Session 48 opened ~9 minutes after Session 47 closed. Fix 6 Code outputs landed during the gap. Triage produced four headline outcomes (§6A regex stages clean / §6B one alias added at 98.1%, one declined at 60.4% threshold-respecting / §6C 784 clean merges = 58.6% of normal-race orphans = +28% over brief's pre-flight estimate / hard limits all held). Operator chose recommendations route (Q1: commission merge-execution brief; Q2: decline Code's 24-hour scheduled-agent offer for 23:30 backfill verification — operator-Claude verifies cheaply at next session pre-flight).

Brief drafting fired naturally on operator's "draft brief and close" trigger. Step 2 pre-flight grounding via Desktop Commander surfaced **substantively bigger architectural complexity than anticipated** — the merge target is a single `races` table where two rows must consolidate into one (not a field-copy operation), with five dependent tables carrying `race_id` references that need re-pointing, plus the unresolved Fix 5 §7b runner-level convergence finding suggesting the existing service's merge mechanism doesn't consolidate runner rows.

Drafting paused with operator decision: full merge-execution brief now (Option 1, 500+ lines and write-risky) / smaller scoping brief first (Option 2, design-doc shape, source-review precedent) / defer entirely (Option 3). **Operator chose Option 2** — Fix 7 reframed as a design-document probe rather than a write operation. Scope expanded to fold the parked Fix 5 §7b runner-level finding into Area B of the same investigation (collapses two parked items into one).

Brief drafted full-pass at 283 lines (within 200-280 anticipation, slight overrun by 3 lines, comparable to Fix 6's 352-line precedent for a more substantively-scoped surgical brief). Code hand-off prompt produced via `message_compose_v1`. Operator confirmed close at "Please provide the very high level what this will do, and what it will fix (operator language), then draft the merge brief, and close" — explicit close trigger plus operator-language framing requirement.

## What was delivered

### Fix 6 report triage (consumed)

`dr029/2_1_race_data/surgical_fix_6_report.md` (435 lines) read in full. Four load-bearing findings:

1. **§6A regex broadening landed cleanly.** All 19 sample input → output pairs verified clean. Stages 1/2/3 held distinct, no collapse. Fix 5 lifts still firing.
2. **§6B alias probe disciplined.** `pioneer → alice springs` added at 98.1% confidence. `cannon` declined at 60.4% (below 80% threshold) — alias-discipline held per brief §6.4. Brief's RQ/Townsville hypotheses for both venues were guesses; probe overrode them.
3. **§6C exceeded brief's pre-flight estimate by 28%.** 784 clean merges (58.6% of normal-race orphans) vs ~612 anticipated. Zero ambiguous. Cause: Stage 2's vocabulary list catches `royal randwick → randwick` (106) and `bet365 camperdown → camperdown` (60) at 100% — under-counted in brief's pre-flight cross-tab.
4. **Hard limits all held.** §10.1–§10.12 clean. Dirty tree unchanged from brief baseline. Code stayed in lane.

Surfaced anomaly **§7b reclassification** — unstripped_naming residual collapsed from 271 expected to 7, no_lc_counterpart grew from 433 expected to 548. Net reclassification: -149 records moved from "Stage 2 didn't help" to "Stage 2 stripped cleanly but no LC row exists."

### Pre-flight grounding for merge-execution brief (surfaced architectural complexity)

Two empirical probes via Desktop Commander against live `capture.db`:
- (a) `fix_6c_proposed_merge.json` schema inspection — 5 top-level keys (`generated_at_acst`, `fix_session`, `method`, `totals`, `records`); 3,249 records each carrying `orphan_race_id` + `target_race_id` for clean records.
- (b) `races` table schema + dependent-table inventory — 49 columns, UNIQUE on `(race_date, venue_normalised, race_number)`, 5 dependent tables (`runners`, `betfair_snapshots`, `bookmaker_snapshots`, `betfair_historical`, `snapshot_batch_summary`) all carrying `race_id INTEGER NOT NULL REFERENCES races(id)`.

Sample clean-merge pair (id=43807 LC-side, id=47542 RA-side) inspected — confirmed two-row pattern where merge means consolidating two `races` rows into one with dependent-row re-pointing. Surfaced this complexity to operator before committing to brief shape (deferral-as-deliverable consideration).

### Fix 7 design brief locked (`dr029/2_1_race_data/surgical_fix_7_design_brief.md`, 283 lines)

Source-review brief shape (Session 33 precedent), four investigative areas:

- **§5.1 / Area A — Existing-merge mechanism inspection.** What does `racing-metadata-backfill.service` actually do when consolidating an RA-side orphan with its LC-side counterpart? Source code inspection + 5-sample merged-race empirical state probe + UNIQUE-violation pre-check.
- **§5.2 / Area B — Runner-row dedup state (Fix 5 §7b consolidation).** Why is runner-level `with_both = 0` despite 2,081 race-level merges? Per-sample runner-row state + cross-tab probe + side-source probe (does the existing service even attempt runner-row consolidation?).
- **§5.3 / Area C — Survivor-row convention.** When two `races` rows merge, which row's `id` should survive? Existing-service convention identification + 784-record cross-check + UNIQUE-conflict check across day-shift / alias-resolved / exact-key classes + dependent-table impact enumeration.
- **§5.4 / Area D — Dependent-table re-pointing pattern.** Volume estimates per dependent table + UNIQUE-constraint conflict checks + transactional-safety probe + idempotency probe.

Sequencing locked A → B → C → D with dependency reasoning. Hard limits §9.1–§9.12 named: single bounded session, read-only on capture.db (URI mode='ro'), read-only on source tree, no source edits, no merge execution, no runner-key probing beyond mechanistic explanation, dirty-tree state preserved, no speculative scope expansion, no deletion of Fix 5C/Fix 6C JSONs. Output spec §8: report at `surgical_fix_7_design_report.md` (350-500 lines anticipated). Forward routing §10 names triage shape for next session: read four-area findings → decide whether merge-execution becomes Fix 8 directly or branches.

### Calls made in brief, locked at hand-off

Nine drafting calls surfaced at hand-off:

1. Fix 7 = design brief, not write brief. Single read-only Code session, design-document output.
2. Fix 5 §7b runner-level finding folded into Fix 7's Area B (collapses two parked items).
3. Source-review brief shape (Session 33 precedent), not surgical-fix shape.
4. Four investigative areas (A → B → C → D), not three or five.
5. Five dependent tables enumerated explicitly.
6. Pre-reads list lean — five required, four reference-only.
7. Hard limits §9 carry 12 explicit items (most load-bearing: §9.2 read-only DB, §9.5 no source edits, §9.7 no mid-session escalation, §9.8 no merge execution, §9.11 no runner-key probing beyond mechanistic).
8. §6 sequencing protects against architectural-baseline surprise (if Area A reveals existing service doesn't actually merge race-rows, B/C/D reframe as fresh design proposal).
9. Output naming `surgical_fix_7_design_brief` / `surgical_fix_7_design_report` — "_design_" infix marks design-document output. Future merge-execution becomes Fix 8 with standard naming.

### Code hand-off prompt produced

Via `message_compose_v1` widget. Brief at canonical path, six pre-reads, key context (VPS, dirty-tree baseline, read-only design probe), four investigative areas A→B→C→D, output spec, ~60-90 min single bounded session, hard limits non-negotiable. Adelaide local timestamps per DR-021.

### Operator-language framing of merge-execution scope

Delivered before brief drafting per operator's explicit request. Two-paragraph plain-language framing covering: (a) the race-level join problem in operational terms (3,249 races never joined between Racing API and Betfair sides because of venue-name mismatches); (b) what Fix 6's dry-run produced (784 cleanly-resolvable cases); (c) what merge execution will fix operationally (better backward-looking analytics on last 60 days, Strategy 1 cycle analysis on those 784 races, Harville calibration data widening); (d) what it does NOT fix (548 no-counterpart, 1,910 trial/jump-out, 7 decoration-suffix, runner-level convergence, future races).

## Standing-instruction adherence check

- **Default to luddite-analyst-gambler brevity** — held. Triage handed back as four-headline framing. Q1/Q2 questions handed in tappable form. Operator-language framing on merge-execution scope delivered before brief drafting.
- **Escalate to detail only when warranted** — held. Two escalations: (a) the merge-mechanism architectural complexity surfaced after pre-flight grounding ("this deserves a little detail" framing not used explicitly but the spirit was — surfaced as three-option decision); (b) drafting calls list at hand-off.
- **Calendar-calibrated session open** — held. Same-workday case (+9 min after Session 47 close) → tight recap delivered.
- **V3 build picture rendered inline at session open — conditional** — held. Skipped silently (no stream state moved).
- **Drift-check the previous session's close-out** — held. (a)/(b)/(c) all clean.
- **Open-items delta — conditional** — held. Skipped silently.
- **Cat 2 pointer (orientation summary delivers recap + drift-check + conditional renders)** — held.
- **Operator review of artefacts is between-session work** — held. Fix 6 report consumed at open; Fix 7 design brief is the artefact for next session's Code execution between sessions.
- **Operator-confirmed forward routing** — held. Q1/Q2 confirmed via tappable; Option 2 (scoping brief) confirmed via tappable; close confirmed via "draft the merge brief, and close" → drafted, produced prompt, closing.
- **Don't drift to alternatives when the operator has been clear about today's work** — held. Operator said "draft brief, close" → drafted (after surfacing architectural complexity that genuinely warranted operator decision), produced prompt, closing.

Other adherence:

- DR-021 timestamp anchor at open and close — clean.
- Required reads completed in order at open — clean.
- Pre-flight directory listing before substantive work — clean.
- DR-029 / DR-027 / DR-028 / DR-021 named in orientation — clean.
- Desktop Commander routing — clean. One namespace gotcha caught: bash_tool call for `ls` returned non-functional error mid-pre-flight; resolved by re-loading Desktop Commander tools via tool_search per Cat 3.
- REPL discipline — held. All multi-line Python via write-script-to-`/tmp` + start_process pattern. No interactive REPL paste.
- Live database queries via Desktop Commander start_process with Python — held. SSH'd to VPS via subprocess, queried `capture.db` read-only via `sqlite3` heredoc. No file copies.
- Verify empirically — don't trust memory or first-pass assumption — held. Pre-flight grounding surfaced architectural complexity that pure inference would have missed; surfaced to operator as decision rather than worked around silently.
- Operator-Claude division of labour — held. Software architecture decision (scoping brief vs full brief) named as Claude's recommendation with reasoning, but operator was given the call because the trade-off involved scope-budget and urgency considerations beyond pure software judgement.

## Open items in

- **Phase 2 validation** — skills + opening prompts in parallel; Session 48 was third clean live run of all three skills (open + brief-drafting + close). One or two more sessions remaining for evaluation per `session_operations_proposal.md` §11.
- **WIP §1** — Fix 4 (cadence, needs probe) brief drafting still pending. Fix 6 brief done Session 47, executed pre-Session-48, triaged Session 48. Fix 7 design brief locked this session — moves to Code execution.
- **WIP §13** — §2.10 carry, substantially fed by probe report §3.3 if probe runs clean Saturday.
- **WIP §16** — VPS in-flight work (11 modified, 7 untracked; +0 from Session 47 baseline; Fix 6 added regex stages + alias to `matching/race_matcher.py` within existing modified file).
- **WIP §17** — Saturday API observation probe runs tomorrow 2026-05-02 morning ACST.
- **Pending architectural extension flagged Session 42** — "Betfair as canonical source" extending to all bet records. Lands in post-DR-029 documentation pass.
- **Fix 6 Code execution** — closed (executed during Session 47→48 gap, triaged Session 48).
- **Fix 5 §7b runner-level convergence finding** — folded into Fix 7 design brief Area B. No longer a standalone parked item.
- **NEW — Fix 7 Code execution pending** — operator runs Code out-of-session against locked design brief; Session 49 (or wherever Fix 7 triage lands) reads design report.
- **NEW — Fix 8 merge-execution brief drafting** — pending Fix 7 design report findings. Anticipated 350-500 lines; will commission actual race-row merges plus dependent-table re-pointing.
- **NEW — 23:30 ACST nightly metadata-backfill verification** — operator-Claude runs cheap read-only probe at next session pre-flight to confirm tonight's run was clean (first clean run under post-Fix-2 service config). Declined Code's scheduled-agent offer in favour of session-pre-flight verification.

## Open items out

- **Fix 6 Code execution** — closed.
- **Fix 6 report triage** — closed.
- **Fix 5 §7b runner-level convergence (as standalone item)** — closed by folding into Fix 7 Area B scope.
- **Fix 5 merge execution brief consolidation (verbal placeholder)** — closed; replaced by Fix 7 design brief → Fix 8 merge-execution brief two-step.

## Forward routing — confirmed with operator

**Session 49 primary path:** triage Code's Fix 7 design report (assuming Code execution lands before Session 49 opens). Branch logic depends on Saturday probe also landing.

Required reads:
1. `current_state.md`.
2. `standing_instructions.md` in full.
3. `project_context.md`.
4. `sessions/SESSION_48.md`.

**Branch-specific (Fix 7 design report triage path):**
5. `dr029/2_1_race_data/surgical_fix_7_design_report.md` — Code's design output.
6. `dr029/2_1_race_data/surgical_fix_7_design_brief.md` — for cross-reference.
7. `dr029/2_1_race_data/fix_6c_proposed_merge.json` — for merge contract reference.

**Branch-specific (Saturday probe triage path, if probe ran first):**
5. `dr029/2_1_race_data/api_probe_report.md`.
6. `dr029/2_1_race_data/api_probe_brief.md`.

**If both landed:** operator chooses primary at Session 49 open. Default: Fix 7 design triage first (smaller scope, unblocks Fix 8 merge-execution brief drafting); probe triage second (feeds Fix 4 brief drafting).

**Pre-flight verification at next session open:** read B1 cross-tab on `races` table to confirm 23:30 nightly metadata-backfill ran clean (first clean run under post-Fix-2 service config). Cheap read-only probe; ~10-second start_process call.

**Triage shape (Fix 7 design report path):** read §A existing-merge mechanism findings; read §B runner-row dedup state findings; read §C survivor-row convention proposal; read §D dependent-table re-pointing pattern proposal; read §6 anomalies; read §8 proposed merge-execution brief shape. Decisions: commission Fix 8 merge-execution brief (default if §A-D findings clean and no blocking anomalies); branch to Fix 8 + Fix 9 split if §B reveals runner-row handling needs separate brief; pivot to operator-decision if §6 surfaces architectural blockers.

## Session close state

- Rebuild folder root: 12 .md (unchanged).
- `dr029/2_1_race_data/`: gained `surgical_fix_6_report.md`, `fix_6c_proposed_merge.json`, and `surgical_fix_7_design_brief.md` between Session 47 close and Session 48 close.
- `skills/`: unchanged (3 skill folders).
- WIP unchanged this session — open items rotate through `current_state.md` only.
- `.close_out_backups/`: contains `SESSION_49_opening_prompt.md` after this close (Session 48 opening prompt swept).
- Sessions: SESSION_48.md added.
- Standing instructions: unchanged (no new instructions surfaced this session).
- v3_build_picture: unchanged this close — Fix 6 triage / Fix 7 design brief is within the §2.1 stream which remains `in flight` with the same next-milestone shape (Code execution pending, design probe). No stream state moved.
- Claude Project `bethub-rebuild` operational.

Twenty-third consecutive non-early-close session.
