# Session 47 — Fix 5 triage + Fix 6 brief drafted (regex broadening + alias-table extension + consolidated dry-run merge)

**Opened:** 2026-05-01 16:57 ACST (Friday late afternoon, +16 min after Session 46 close).
**Closed:** 2026-05-01 17:12 ACST (~15 min, single calendar day, same workday as Session 46).
**Tool routing:** Claude Chat.
**Governing DRs invoked:** DR-029 (active arc — Fix 5 triage + Fix 6 brief drafting against §2.1 surgical-fix arc); DR-027/028 (named at open, not invoked substantively); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 16:57 ACST` at open and `2026-05-01 17:12 ACST` at close. Same workday as Session 46 close (16:41 ACST, +16 min) — calendar-calibrated short recap delivered.

## Pre-flight checks

- **Rebuild folder root at open:** 12 .md files plus expected directories. `.close_out_backups/` contained `SESSION_47_opening_prompt.md` only (per Session 46 close). No phantom files.
- **Drift-check Session 46 close-out:**
  - ✅ (a) `current_state.md` last-updated `2026-05-01 16:41 ACST` matches Session 46 close.
  - ✅ (b) `sessions/SESSION_46.md` exists, 136 lines, non-empty.
  - ✅ (c) `v3_build_picture.md` last-updated `2026-05-01 16:41 ACST` matches Session 46 close (session-ops stream notation rolled to "drop after Session 47").
- **`dr029/2_1_race_data/` at open:** confirmed `surgical_fix_5_report.md` (486 lines) and `fix_5c_proposed_merge.json` (1.7 MB / 3,249 records) had landed — Code finished out-of-session between Session 46 close and Session 47 open.
- **V3 build picture inline:** skipped at open — no stream state moved since Session 46 close. Conditional render condition not met.
- **Open-items delta:** Fix 5 Code execution moved from "pending" to "complete" but that's an in-session triage finding rather than a between-sessions delta. Skipped silently.

## Session shape

Session 47 opened ~16 minutes after Session 46 closed. Branch logic from `current_state.md`: Code's Fix 5 outputs landed on disk during the gap (Code session ran 16:42-17:25 ACST per the Code report's own anchor — wall-clock overlap with Session 46/47 boundary; Code finished before Session 47's substantive triage). Path = Fix 5 report triage primary, Saturday probe still scheduled for tomorrow morning.

Triage produced three forward-routing options (A: commission Fix 5 merge-execution brief now / B: commission Fix 6 regex-broadening brief first then merge-execute / C: pivot to runner-key probe per Fix 5 Finding §7b). Operator chose **Option B** with single-select tap. Fix 6 brief drafting fired naturally on the implicit trigger. Pre-flight grounding (Step 2 of brief-drafting skill) ran two empirical probes against `capture.db`: (a) LC-side counterpart inventory for the highest-volume unstripped-naming venues (confirmed real merge targets exist for ~426 records); (b) cross-tabulation of pattern broadenings against actual LC counterparts to size each Fix 6 stage's unlock potential.

Operator pivoted drafting cadence mid-skill from "section-by-section walkthrough" (chosen via tappable options) to "lock the calls — draft full brief, surface at hand-off" after §1 + §2 review. The pivot reasoning: technical detail in section-by-section walkthrough wasn't useful for operator review (operator is strategic decision-maker per Cat 5, not technical reviewer; sections were operating at appropriate detail for Code recipient but not for operator-Claude review). Brief drafted full-pass at 352 lines (within 280-360 anticipation, within Fix 5's 309-line precedent ballpark). Code hand-off prompt produced via `message_compose_v1`. Operator confirmed close at "Sounds good. Please draft brief, provide prompt for Claude Code, and close" — explicit close trigger.

## What was delivered

### Fix 5 report triage (consumed)

`dr029/2_1_race_data/surgical_fix_5_report.md` (486 lines) read in full. Three load-bearing findings surfaced:

1. **§5A landed cleanly** — sponsor-with-hyphen and locality-prefix harmonisation working as specified, but the strict lift's coverage is narrower than the brief's framing suggested (Finding §7e). Of 13 sample venues in the brief, only 3-4 were addressed by strict lift.
2. **§5B repointed the hypothesis** — warwick-farm-class residual is dominated by trials/jump-outs (1,910 of 3,249 orphans, 58.8%), not timezone day-drift. Day-drift is real but tiny (21 races across 4 non-DST QLD/border venues).
3. **§5C produced 186 clean merges (5.7% of total, 13.9% of normal-race orphans)** with 0 ambiguous and 1,153 normal-race no-matches split into unstripped-naming class (652) and no-LC-counterpart class (501).

Surfaced anomaly **Finding §7b — runner-level `with_both` is still 0 despite 2,081 race-level merges**. Race-level cross-tab moved overnight via `racing-metadata-backfill.service` runs but runner-level convergence didn't follow. Out of Fix 6 scope, parked as a future brief.

### Fix 6 brief locked (`dr029/2_1_race_data/surgical_fix_6_brief.md`, 352 lines)

Three substantive §-sections:

- **§6A — Regex broadening of `normalise_venue`.** Three sequenced stages: sponsor-park strip (`aquis park gold coast` → `gold coast`), sponsor-without-hyphen strip (`ladbrokes geelong` → `geelong`), suffix near-miss strip (`rosehill gardens` → `rosehill`, `morphettville parks` → `morphettville`). Stages held distinct, not collapsed. Vocabulary empirically anchored to Session 47 pre-flight, not transcribed from `_clean_venue` source.

- **§6B — `BETFAIR_VENUE_ALIASES` extension.** Empirical probe-and-decide for two renamed-venue classes (`ladbrokes pioneer`, 53 records; `ladbrokes cannon`, 44 records) where the Stage 2 regex strips correctly but the stripped name has no LC counterpart. Code probes `capture.db` to determine actual LC-side venue names; if probe produces clear dominant target, alias added; if ambiguous, no alias and finding surfaced.

- **§6C — Consolidated dry-run merge plan** at `fix_6c_proposed_merge.json` superseding `fix_5c_proposed_merge.json`. Estimated unlock: ~426 additional clean merges on top of Fix 5's 186 → ~612 total clean merges out of 1,339 normal-race orphans (45.7%). Day-shift broadening rule from Fix 5 carries forward unchanged.

Sequencing locked §6A → §6B → §6C with explicit reasoning. Hard limits §10 names: single bounded session, named anchors only (`matching/race_matcher.py:normalise_venue` + `BETFAIR_VENUE_ALIASES`), no schema changes, no DB writes, no commit/stash/restore, no DR-029 named-debt remediation, no mid-session escalation, no edits to `bookmakers/sportsbet.py`, no merge execution, no speculative regex broadening, no speculative alias additions, no deletion of `fix_5c_proposed_merge.json`. Dirty-tree handling §11 follows Fix 5 brief precedent — verify tree state pre-edit, edit only named anchors, post-edit `git status` confirmation, no `git add/commit/stash/restore`. VPS dirty-tree state captured at session pre-flight (11 modified, 7 untracked; +0 from Fix 5 close).

Output spec §12: report at `surgical_fix_6_report.md` (300-400 lines anticipated). Forward routing §13 names triage shape for next session: read §6A/§6B/§6C; default routing is to commission merge-execution brief reading `fix_6c_proposed_merge.json`.

### Calls made in brief, locked at hand-off

Nine drafting calls surfaced and held:

1. Combine all broadening + alias work + dry-run plan into one Code session (~60-90 min).
2. Code re-runs entire retroactive match producing ONE consolidated dry-run plan superseding Fix 5C.
3. Code probes live DB empirically to determine renamed-venue alias targets (not specified in brief).
4. No edits to `bookmakers/sportsbet.py` (Fix 5 boundary holds).
5. No merge execution.
6. Day-shift broadening rule carries forward unchanged (only sunshine coast / orange / ballina / rockhampton).
7. Three regex stages held distinct, not collapsed into one mega-regex.
8. Stage 2 sponsor vocabulary empirically anchored to Session 47 pre-flight (not transcribed from `_clean_venue`).
9. Suffix scope limited to ` gardens` and ` parks` only (other suffixes not empirically validated; no speculative additions).

### Code hand-off prompt produced

Via `message_compose_v1` widget: short prompt directing Code to the brief at the canonical path, naming pre-reads, key context (VPS, dirty tree state, three sub-fixes), outputs (report + JSON), Adelaide local timestamps per DR-021, 60-90 min single bounded session.

## Standing-instruction adherence check

- **Default to luddite-analyst-gambler brevity** — held. Triage handed back as short list of three options. Drafting cadence pivot accepted at operator pushback ("technical detail not useful for me — give me high-level"). One-paragraph plain-language framings on §1 / §2 review.
- **Escalate to detail only when warranted** — held. One escalation: Step 5 of brief-drafting skill surfaced nine drafting calls explicitly rather than burying them; operator chose lock-the-calls path after pushback.
- **Calendar-calibrated session open** — held. Same-workday case (+16 min after Session 46 close) → tight recap delivered.
- **V3 build picture rendered inline at session open — conditional** — held. Skipped silently (no stream state moved since Session 46 close).
- **Drift-check the previous session's close-out** — held. (a)/(b)/(c) all checked clean.
- **Open-items delta — conditional** — held. Skipped silently.
- **Cat 2 pointer (orientation summary delivers recap + drift-check + conditional renders)** — held.
- **Operator review of artefacts is between-session work** — held. Fix 5 report consumed at open; this session's Fix 6 brief is the artefact for next session's Code execution between sessions.
- **Operator-confirmed forward routing** — held. Option B confirmed via single-select; close confirmed via "Please draft brief, provide prompt for Claude Code, and close."

Other adherence:

- DR-021 timestamp anchor at open and close — clean.
- Required reads completed in order at open — clean.
- Pre-flight directory listing before substantive work — clean.
- DR-029 / DR-027 / DR-028 / DR-021 named in orientation — clean.
- Desktop Commander routing — clean. One namespace gotcha caught: bash_tool call returned "no such file" mid-pre-flight; resolved by re-loading Desktop Commander tools via tool_search per Cat 3.
- REPL discipline — held. Initial multi-line REPL paste mis-parsed (Cat 3 known failure mode); immediately switched to write-script-to-/tmp + start_process for both pre-flight probes.
- Operator-facing presentation discipline — held after operator pushback. §1 and §2 of brief drafted in technical detail (appropriate for Code recipient); operator review surfaced that section-by-section walkthrough wasn't useful for operator (technical detail vs strategic-decision-maker frame). Pivoted to lock-the-calls cadence, surfaced calls in plain language at hand-off.
- Don't-drift-to-alternatives — held. Operator said "draft brief, provide prompt, close" → drafted, produced prompt, closing.

## Open items in

- **Phase 2 validation** — skills + opening prompts in parallel; this session was second clean live run of all three skills (open + brief-drafting + close). Sessions 48-ish remaining for evaluation per `session_operations_proposal.md` §11.
- **WIP §1** — Fix 4 (cadence, needs probe) brief drafting still pending. Fix 5 brief done Session 46, executed pre-Session-47, triaged Session 47. Fix 6 brief locked this session — moves to Code execution.
- **WIP §13** — §2.10 carry, substantially fed by probe report §3.3 if probe runs clean Saturday.
- **WIP §16** — VPS in-flight work (11 modified, 7 untracked; +3 from `vps_drift_check.md` §3 baseline reflecting Fix 3 + Fix 5 landing between Sessions 36-47).
- **WIP §17** — Saturday API observation probe runs tomorrow 2026-05-02 morning ACST.
- **Pending architectural extension flagged Session 42** — "Betfair as canonical source" extending to all bet records. Lands in post-DR-029 documentation pass.
- **Fix 5 Code execution** — closed (executed during Session 46→47 gap, triaged Session 47).
- **NEW — Fix 6 Code execution pending** — operator runs Code out-of-session against locked brief; Session 48 (or wherever Fix 6 triage lands) reads report and JSON.
- **NEW — Runner-level convergence finding (Fix 5 §7b)** — race-level merges aren't unlocking runner-level `with_both` count. Out of Fix 6 scope; parked as future brief, possibly Fix 7.
- **NEW — Fix 5 merge execution brief** — consolidated into the post-Fix-6 merge execution brief. Single brief to execute Fix 6's `fix_6c_proposed_merge.json` (which includes Fix 5's 186 clean merges).

## Open items out

- **Fix 5 Code execution** — closed (executed and triaged this session).
- **Fix 5 report triage** — closed.
- **Fix 6 brief drafting** — closed. Brief locked at `dr029/2_1_race_data/surgical_fix_6_brief.md`.

## Forward routing — confirmed with operator

**Session 48 primary path:** triage Code's Fix 6 report (assuming Code execution lands before Session 48 opens). Branch logic depends on Saturday probe also landing.

Required reads:
1. `current_state.md`.
2. `standing_instructions.md` in full.
3. `project_context.md`.
4. `sessions/SESSION_47.md`.

**Branch-specific (Fix 6 report triage path):**
5. `dr029/2_1_race_data/surgical_fix_6_report.md` — Code's output.
6. `dr029/2_1_race_data/fix_6c_proposed_merge.json` — consolidated merge plan.
7. `dr029/2_1_race_data/surgical_fix_6_brief.md` — for cross-reference.

**Branch-specific (Saturday probe triage path, if probe ran first):**
5. `dr029/2_1_race_data/api_probe_report.md`.
6. `dr029/2_1_race_data/api_probe_brief.md`.

Triage shape (Fix 6 report path): read §6A functional verification (did the regex stages produce the named harmonisations cleanly?); read §6B alias probe results (were targets empirically clear or ambiguous?); read §6C consolidated plan totals (close to ~612 expected? unexpected ambiguity?). Decisions: commission merge-execution brief reading `fix_6c_proposed_merge.json` (default if §6C clean count healthy); refine match logic if §6B surfaced ambiguity; pivot to runner-level convergence finding (Fix 5 §7b) before any merge execution.

## Session close state

- Rebuild folder root: 12 .md (unchanged).
- `dr029/2_1_race_data/`: gained `surgical_fix_5_report.md`, `fix_5c_proposed_merge.json`, and `surgical_fix_6_brief.md` between Session 46 close and Session 47 close.
- `skills/`: unchanged (3 skill folders).
- WIP unchanged this session — open items rotate through `current_state.md` only.
- `.close_out_backups/`: contains `SESSION_48_opening_prompt.md` after this close (Session 47 opening prompt swept).
- Sessions: SESSION_47.md added.
- Standing instructions: unchanged (no new instructions surfaced this session).
- v3_build_picture: unchanged this close — Fix 5/Fix 6 movement is within the §2.1 stream which remains `in flight` with the same next-milestone shape (Code execution pending). No stream state moved.
- Claude Project `bethub-rebuild` operational.

Twenty-second consecutive non-early-close session.
