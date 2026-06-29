# Session 40 — Directory governance review + session operations proposal

**Opened:** 2026-05-01 08:06 ACST
**Closed:** 2026-05-01 ~09:00 ACST
**Tool routing:** Claude Chat
**Governing DRs invoked:** DR-029 (active arc — but no DR-029 substantive work this session); DR-027/028 (cross-DB discipline — not invoked, no boundary surface this session); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 08:06 ACST`. Friday morning — confirmed probe runs Saturday post-Session 40 (not before, as the opening prompt assumed).

## Session shape — pivot at orientation

Opening prompt assumed Saturday probe had already run; required reads structured around triaging probe outcomes (Branches A/B/C). Reality: probe runs *tomorrow*. Operator confirmed the routing pivot: Session 40 used for probe-independent meta-work today, with session-and-documentation updates to reflect the corrected probe-execution timeline.

## What was delivered

Three substantive deliverables, in order:

### 1. Directory governance review (clean state baseline)

Pre-flight surfaced phantom file `SESSION_11_SCRATCH.md` at rebuild root (not in Session 39 close inventory). Investigated; turned out it had been correctly placed in `sessions/` already — root listing was stale-cached. No action needed for it.

Full directory sweep produced consolidated findings list. Operator approved deletion of:
- 8 `.DS_Store` files (macOS Finder cosmetic noise) — deleted.
- 3 close-out backup opening prompts (`SESSION_34/35/36_OPENING_PROMPT.md` in `.close_out_backups/`) — reviewed for content first; both confirmed they carried no load-bearing content not already in WIP or session records, except one technical lesson on `create_file` vs `write_file` namespace gotcha that was folded into WIP standing instructions before deletion. Backups then deleted.

Operator surfaced concern mid-review about Claude losing context across sessions and accidentally deleting things needed later. Adopted standing rule for the rest of the review: don't propose deletion of anything referenced in WIP, session records, briefs, or scope documents without first showing the references. Default to "leave it" for ambiguous cases. Held throughout.

Items reviewed and **left in place**: `diagrams/` empty directory (placeholder for v3_target.svg per WIP); `orchestration_pack/` (multi-agent prompt drafts, ~70KB, named in WIP); `agent_review/` full tree (durable history); `dr029/2_1_race_data/notes.md` (Code's carry-over notes); `dr029/2_1_race_data/vps_drift_check.md` (Session 36 diagnostic referenced in WIP §16); `SESSION_11_SCRATCH.md` (Session 13 delta-spec workpaper). All have load-bearing references.

Final root state: 7 canonical .md, 6 subdirectories, no cosmetic noise.

### 2. WIP standing-instruction update — filesystem discipline

Strengthened the existing filesystem-discipline standing instruction in WIP per operator direction. New language:

- Desktop Commander is the **default** filesystem and process tool for all operations.
- This is a Claude.ai session running on the operator's local Mac via Desktop Commander — **there is no bash sandbox available, no separate Linux container, no other shell environment.**
- The bash_tool that may appear in Claude's tool list is **non-functional** — calls fail with "no such file" because it cannot reach the Mac filesystem.
- `projects-filesystem` MCP server is an acceptable alternative for rebuild folder file operations only.
- **Session 34 lesson** — `create_file` vs `write_file` namespace gotcha — folded in.

Single operator-driven correction surfaced mid-session: my first `mv` attempt used the bash_tool tool out of habit and got "no such file" — exactly the failure mode the standing instruction now warns against. Updated the standing instruction to make the rule more emphatic and explanatory rather than implicit.

### 3. Session operations proposal

Operator-surfaced concern: open and close sessions burn too much context (~50-65K tokens / 25-32% of 200K window before substantive work begins) and Claude loses fundamental agreements across sessions despite the heavy WIP read.

Web check completed (Claude Projects state, Custom Skills state, Claude 4.6/4.7 1M-token-context-window) to ground the proposal in current 2026 product capabilities.

Proposal written at `session_operations_proposal.md` (rebuild root, ~19KB, 195 lines). Twelve sections:

- §1-3 Problem diagnosis and core insight (split WIP's two jobs: durable canonical truth vs session journal).
- §4 Proposed structure — Project knowledge base + slim `current_state.md` + 3 custom skills + Memory.
- §5-6 Walkthroughs of session open and close under the new flow.
- §7 Migration plan — 4 phases, probe-work stays primary, dedicated meta-session in Session 42-43.
- §8 What does NOT change (DRs, sessions/, governance protocols, presentation discipline).
- §9 Risks and trade-offs (six items).
- §10 How this addresses context retention specifically (three structural protections — standing_instructions.md, DRs as agreement-of-record, skills for procedures).
- §11 Recommendation.
- §12 Open questions for operator.

**Section-by-section walkthrough with operator** (§1 through §12, single section per round, plain language, decision-shaped per Session 39 standing). Operator confirmed each section. Three operator-surfaced points worth recording:

(a) **Risk 3 mitigation** (Project RAG retrieval missing context): operator pushed for explicit mitigation language. Folded in: `current_state.md` and `standing_instructions.md` always read in full at session open (never via retrieval); DRs always read in full when invoked by number; everything else retrieval-OK with full-read as fallback.

(b) **`current_state.md` clarification** — operator asked whether it would be delta-based (current vs prior session). Confirmed: no, it's a single live file updated in place at close, not versioned snapshots. Rotation pattern: durable detail flows into `sessions/SESSION_N.md` at close; `current_state.md` itself stays slim and current.

(c) **`standing_instructions.md` is operator's control surface.** Operator surfaced that this file is where they want to dictate how Claude interacts with them — including the bit-by-bit walkthrough pattern that worked well today. Confirmed: operator-authored, organised by category (not chronology), forty-or-so existing instructions migrate over and get reorganised. Detailed review of `standing_instructions.md` shape deferred to a later session at operator's request.

**Three open-question answers locked:**
1. Operator has Claude Max (Pro-tier capacity, no constraint).
2. Operator OK with uploading rebuild folder docs to a Claude Project.
3. Diagnosis (context-loss as primary pain; token burn as secondary; WIP-as-single-file as structural driver) matches operator's felt experience. Operator added: open/close sessions take a long time — addressed by the proposal.

**Proposal accepted in principle.** Phase 1 (create empty Project in claude.ai) lands Session 41 if probe-triage time permits. Phase 2 (real migration: extract files, upload to Project, write skills) is dedicated meta-session, Session 42 or 43. Detailed `standing_instructions.md` review happens at end of Phase 2.

## Operator framing reinforced

Section-by-section walkthrough at one section per round held cleanly through the entire §1-§12 proposal review. Operator confirmed the pattern works well: "this approach you're doing right now of bit by bit of a report that's summarised in plain language. This has been a really useful thing for me. That's something I want to retain." Migrating to `standing_instructions.md` near the top under "how Claude communicates with operator."

Mid-session operator pull-back on `.DS_Store` deletion ("can you make sure that whatever you're deleting is not something we've needed for later on") prompted standing rule for rest of review (don't propose deletion of anything referenced in WIP/sessions/briefs without showing references). Held throughout.

## Standing-instruction adherence check

- DR-021 timestamp anchor — clean (08:06 ACST).
- Required reads completed in order — clean.
- Pre-flight directory listing before substantive work — clean (caught the `SESSION_11_SCRATCH.md` phantom).
- DR-027 / DR-028 / DR-029 named in orientation — clean.
- Desktop Commander / projects-filesystem routing — caught one bash_tool slip mid-session, corrected immediately, fed into the standing-instruction strengthening.
- write-script-to-/tmp + start_process discipline — n/a this session (no Python REPL needed).
- Operational/analytical line discipline — n/a (no DR-029 substantive work).
- Operator-facing presentation discipline (Session 39 standing) — held cleanly throughout. Section-by-section walkthrough was the proof of pattern.

## Open items

**No new substantive open items from this session.** The session operations proposal itself is parked under "what is next" as Phase 1/2/3/4 work, scheduled across Sessions 41-44+.

**Carrying forward:**
- WIP §16 (VPS in-flight work + metadata-backfill log-permission residual).
- WIP §17 (Saturday API observation probe — runs tomorrow).
- WIP §13 (§2.10 carry — to be substantially fed by probe report).

## Session close state

- Rebuild folder root: 7 canonical .md (unchanged) + new `session_operations_proposal.md` = **8 .md files at root**, plus 6 subdirectories. Note: `session_operations_proposal.md` is a discussion document, not a canonical file — slated to be archived or migrated as part of Phase 3 once the new flow is stable.
- WIP filesystem-discipline standing instruction strengthened.
- `.close_out_backups/` empty.
- All `.DS_Store` files removed.
- Probe brief unchanged.

## Forward to Session 41

Session 41 opens after Saturday's probe completes. Primary read: `dr029/2_1_race_data/api_probe_report.md` and the raw JSONL captures. Branches A/B/C from the original Session 40 opening prompt apply to Session 41 instead.

**Optional Phase 1 work** (if probe-triage time permits): create empty Claude Project named "bethub-rebuild" via claude.ai sidebar. No file uploads yet, no instructions yet — empty Project just creates the workspace.

Opening prompt for Session 41 generated alongside this record per standing instruction.
