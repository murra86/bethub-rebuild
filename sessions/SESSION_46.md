# Session 46 — Fix 5 brief drafted (venue harmonisation + retroactive merge + edge-case probe)

**Opened:** 2026-05-01 16:17 ACST (Friday afternoon, +4 min after Session 45 close).
**Closed:** 2026-05-01 16:41 ACST (~24 min, single calendar day).
**Tool routing:** Claude Chat.
**Governing DRs invoked:** DR-029 (active arc — Fix 5 brief drafting against §2.1 surgical-fix arc); DR-027/028 (cross-DB discipline — not invoked); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 16:17 ACST` at open and `2026-05-01 16:41 ACST` at close. Same workday as Session 45 close (16:13 ACST, +4 min) — calendar-calibrated short recap delivered.

## Pre-flight checks

- **Rebuild folder root at open:** 12 .md files plus expected directories. `.close_out_backups/` contained `SESSION_46_opening_prompt.md` only (per Session 45 close). No phantom files. Clean.
- **Drift-check Session 45 close-out:**
  - ✅ (a) `current_state.md` last-updated `2026-05-01 16:13 ACST` matches Session 45 close.
  - ✅ (b) `sessions/SESSION_45.md` exists, 125 lines, non-empty.
  - ✅ (c) `v3_build_picture.md` carries authoring stamp `2026-05-01 14:21 ACST` correctly — no stream state moved at Session 45 close so artefact wasn't updated. Expected.
- **V3 build picture inline:** skipped at open — no stream state moved since Session 45 close (+4 min, Phase 2 deliverable authoring with no stream movement). Conditional render condition not met.
- **Open-items delta:** none meaningful since Session 45 close. Skipped silently.

## Session shape

Session 46 opened ~4 minutes after Session 45 closed. Per `current_state.md` Session 46 branch logic: pre-probe afternoon path → Fix 5 (venue harmonisation) brief drafting. Operator confirmed objective at open with one short clarifying question ("what's the objective"); Claude responded with two-paragraph plain-English framing of the venue-mismatch problem and the two-part fix shape.

Session was the first live exercise of the `bethub-brief-drafting` skill on a real brief. Skill fired naturally on the implicit trigger ("Fix 5 brief drafting" from `current_state.md`) without operator needing to invoke it. Pre-flight grounding (Step 2 of the skill) read three named anchors in order: `source_review_report.md`, `vps_drift_check.md`, `surgical_fix_1_2_report.md`. Three routing calls surfaced as a short list with brief detail and recommendations (per operator request "short list of options, brief detail, recommendation please"); operator delegated all three with "your call on these. I'm not technical." Brief drafted full-pass at 309 lines (within 200-280 target range slightly exceeded due to three §-sections rather than precedent's one or two). Nine calls-made surfaced at hand-off; operator locked all as drafted ("As per documentation, all your calls").

## What was delivered

### `surgical_fix_5_brief.md` (309 lines, at `dr029/2_1_race_data/surgical_fix_5_brief.md`)

21,247 bytes. Three substantive §-sections:

- **§5A** — Lift `bookmakers/sportsbet.py:_clean_venue` logic into `matching/race_matcher.normalise_venue` so all callers share canonical venue normalisation. Single-file edit; sportsbet.py left untouched (redundant `_clean_venue` stays in place, operator-Claude routes consolidation later).
- **§5B** — Diagnostic probe of the `warwick farm`-class edge case (13 venues where venue_normalised aligns but rows still don't merge). Time-boxed 15 minutes; hypothesis is race_date timezone drift.
- **§5C** — Dry-run retroactive merge of the 1,266 Racing-API-only orphan race rows. Produces `dr029/2_1_race_data/fix_5c_proposed_merge.json` as the contract for the future merge-execution session. Does not execute the merge.

Sequencing locked §5A → §5B → §5C with explicit stop conditions. Hard limits §9 names: single bounded session, named anchors only, no schema changes, no DB writes, no commit/stash/restore, no DR-029 debt remediation, no mid-session escalation, no edits to `bookmakers/sportsbet.py`, no merge execution. Dirty-tree handling §10 follows the Fix 3 brief precedent — verify tree state pre-edit, edit only named anchors, post-edit `git status` confirmation, no `git add/commit/stash/restore`.

Output spec: single report at `surgical_fix_5_report.md` (200-280 lines anticipated) plus auxiliary JSON file. Forward routing §11 names triage shape for next operator-Claude session: read clean-merge proportion, ambiguous-match handling, no-match reasons; decide whether to commission merge-execution brief or refine match logic first.

### Operator-confirmed routing calls (locked)

Three operator decisions delegated to Claude:

1. **Scope shape** — three §-sections in one Code session (option c).
2. **`_clean_venue` lift target** — into `matching/race_matcher.normalise_venue` itself (option a — canonical normaliser, all callers benefit).
3. **Retroactive-merge mechanics** — dry-run only; operator-Claude reviews proposed merges before commissioning real execution (option b — cheap insurance against silent miss-merge).

### Calls made in brief, locked at hand-off

Nine drafting calls surfaced and held:
1. Three §-sections in one Code session, strict ordering.
2. Lift into `normalise_venue` itself, not per-caller wrapper.
3. §5C dry-run only, JSON output.
4. `bookmakers/sportsbet.py:_clean_venue` left in place after lift.
5. §5B time-boxed 15 minutes with stop-and-proceed-to-§5C rule.
6. §5A functional verification via `/tmp/` snippet (no `tests/` directory).
7. B1/B2/B3 cross-tab post-§5A re-run is NOT EXPECTED to move (named in brief).
8. §5C output is JSON (not Markdown) — machine-readable for future merge-execution brief.
9. Length anticipation 200-280 lines for report.

## Phase 2 validation status

Session 46 was the first live exercise of all three Phase 2 skills:
- ✅ `bethub-session-open` — fired automatically; ritual ran clean (Steps 1-8 all held).
- ✅ `bethub-brief-drafting` — fired implicitly on `current_state.md` Fix-5-drafting context; Steps 1-7 all ran; Step 6 (operator review) held to operator's "your call on these / all your calls" mode rather than section-by-section walkthrough (precedent allowed per skill body).
- ✅ `bethub-session-close` — firing now.

Validation period continues through Sessions 47-48-ish. After two more sessions running both skills + opening prompts, evaluate per `session_operations_proposal.md` §11 whether to drop the opening prompt artefact.

## Standing-instruction adherence check

- **Default to luddite-analyst-gambler brevity** — held. Two-paragraph framing on objective question; short-list routing options; two-line confirmations; no over-explanation.
- **Escalate to detail only when warranted** — held. One escalation: Step 5 of brief-drafting skill surfaced nine drafting calls explicitly rather than burying them; operator chose "as per documentation" path, all locked.
- **Calendar-calibrated session open** — held. Same-workday case (+4 min after Session 45 close) → tight recap delivered.
- **V3 build picture rendered inline at session open — conditional** — held. Skipped silently (no stream state moved since Session 45 close).
- **Drift-check the previous session's close-out** — held. (a)/(b)/(c) all checked clean.
- **Open-items delta — conditional** — held. Skipped silently.
- **Cat 2 pointer (orientation summary delivers recap + drift-check + conditional renders)** — held.

Other adherence:

- DR-021 timestamp anchor at open and close — clean.
- Required reads completed in order at open — clean.
- Pre-flight directory listing before substantive work — clean.
- DR-029 / DR-027 / DR-028 / DR-021 named in orientation — clean.
- Desktop Commander routing — clean. One namespace gotcha caught: bash_tool call returned "no such file" mid-session (write_file path mid-process); resolved by re-loading Desktop Commander tools via tool_search per Cat 3.
- Operator-facing presentation discipline — held. Plain-language framing on the objective question; brief drafting kept technical content in the brief itself (artefact deliverable, exempt from brevity defaults per Cat 1).
- Don't-drift-to-alternatives — held. Operator said "go ahead" → drafted; said "all your calls" → locked.
- Operator-confirmed forward routing — held. Confirmed close at operator's "close it up I reckon" with explicit ask-back ("unless you recommend otherwise").

## Open items in

- **Phase 2 validation** — skills + opening prompts in parallel; Sessions 47-48-ish then evaluate.
- **WIP §1** — Fix 4 (cadence, needs probe) brief drafting. Fix 5 brief locked this session — moves to Code execution.
- **WIP §13** — §2.10 carry, substantially fed by probe report §3.3.
- **WIP §16** — VPS in-flight work; metadata-backfill log-permission residual closed empirically Session 43.
- **WIP §17** — Saturday API observation probe runs tomorrow 2026-05-02. Triage Session 48 (or whichever session it lands in after Fix 5 Code execution + Session 47 triage).
- **Pending architectural extension flagged Session 42** — "Betfair as canonical source" extending to all bet records.
- **NEW — Fix 5 Code execution pending** — operator runs Code out-of-session against locked brief; Session 47 triages report and JSON merge plan.

## Open items out

- **Fix 5 brief drafting** — closed. Brief locked at `dr029/2_1_race_data/surgical_fix_5_brief.md`.

## Forward routing — confirmed with operator

**Session 47:** triage Code's Fix 5 report.

Required reads:
1. `current_state.md`.
2. `standing_instructions.md` in full.
3. `project_context.md`.
4. `sessions/SESSION_46.md`.
5. `dr029/2_1_race_data/surgical_fix_5_report.md` — Code's output.
6. `dr029/2_1_race_data/fix_5c_proposed_merge.json` — auxiliary merge plan.
7. `dr029/2_1_race_data/surgical_fix_5_brief.md` — for cross-reference if scope questions arise.

Triage shape: read §5A functional verification (did the orphan-venue sample harmonise?); read §5B findings (timezone-shift hypothesis confirmed?); read §5C dry-run summary (clean / ambiguous / no_match counts). Decide:
- **High clean-merge / low ambiguity:** commission single follow-up brief that executes the merge.
- **High ambiguity or unexpected match shapes:** refine match logic first; possibly a §5B-style probe on the ambiguous class.
- **Saturday probe priority shifts in:** if probe ran cleanly Saturday morning, Session 47 may pivot to probe triage and defer Fix 5 report triage to Session 48.

## Session close state

- Rebuild folder root: 12 .md (unchanged).
- `dr029/2_1_race_data/`: gained `surgical_fix_5_brief.md` this session.
- `skills/`: unchanged (3 skill folders).
- WIP unchanged this session — open items rotate through `current_state.md` only.
- `.close_out_backups/`: contains `SESSION_47_opening_prompt.md` after this close (Session 46 opening prompt swept).
- Sessions: SESSION_46.md added.
- Standing instructions: unchanged (no new instructions surfaced this session).
- Claude Project `bethub-rebuild` operational.

Twenty-first consecutive non-early-close session.
