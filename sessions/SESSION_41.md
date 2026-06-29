# Session 41 — Phase 2 governance work: standing_instructions.md + current_state.md

**Opened:** 2026-05-01 09:15 ACST
**Closed:** 2026-05-01 09:30 ACST
**Tool routing:** Claude Chat
**Governing DRs invoked:** DR-029 (active arc — but no DR-029 substantive work this session); DR-027/028 (cross-DB discipline — not invoked, no boundary surface this session); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 09:15 ACST` at open and `2026-05-01 09:30 ACST` at close. Friday morning — probe runs Saturday 2026-05-02. **Branch X confirmed at open.**

## Session shape

Probe-independent governance work per Session 40 close. Operator's stated priority for the day was completing the documentation parts of Phase 2 of the session operations proposal (extract `standing_instructions.md` from WIP, build slim `current_state.md`). Both delivered with section-by-section walkthrough cadence, one category per round.

## What was delivered

### 1. `standing_instructions.md` at rebuild root

Created at `/Users/tim/Desktop/Projects/bethub-rebuild/standing_instructions.md`. Five categories covering the ~forty-or-so existing standing instructions migrated out of WIP and reorganised by what they govern (not chronologically):

1. **How Claude communicates with the operator** (8 instructions) — short responses / plain operational-gambling-and-non-technical language / decision-maker framing / section-by-section walkthrough / unwind shorthand with bracketed reminders / drift signals / scope clause / don't drift to alternatives.
2. **Session protocol** (10 instructions including close-out actions) — timestamp anchor + Adelaide local time / pre-flight directory listing / required reads / name governing DRs / opening prompts as pointers / copy-paste opening prompts (current workflow) / "Open session N" / "Close session N" as future state pending Phase 2 evaluation / close-out actions checklist / closing summary discipline / deferral-as-deliverable.
3. **Filesystem and tooling discipline** (7 instructions) — Desktop Commander default / bash_tool non-functional / projects-filesystem alternative / create_file vs write_file gotcha / REPL discipline / live DB queries / verify empirically.
4. **Governance discipline** (6 instructions) — DR-027/028 cross-DB / operational-vs-analytical line discipline / plain-language cluster summaries / operator review as between-session work / insurance + free bets analysed as cycle / Betfair canonical for Betfair-owned data.
5. **Operator-Claude division of labour** (4 instructions) — software questions Claude's / betting and operational questions operator's / operator as strategic decision-maker (not technical decision-maker) / propose software-shaped answers first for ambiguous cases.

**Three operator-driven shape changes during review**, all to Category 1:

- (a) Plain operational language extended to cover technical/coding/data-architecture jargon — operator explicitly noted "I'm not technical."
- (b) Shorthand unwinding now requires a brief bracketed description on every reference (not just first mention) to spur memory — e.g. "DR-027 (the two-database architecture decision)".
- (c) Operator-as-strategic-decision-maker re-framing in Category 5: operator makes strategic/routing decisions, Claude makes software/technical decisions (proposed for confirmation, not punted back).

### 2. `current_state.md` at rebuild root

Created at `/Users/tim/Desktop/Projects/bethub-rebuild/current_state.md`. 60 lines, five sections: where we are / what's next (with branch logic A/B/C/X carrying forward to Session 42) / required reads for next session / open items as WIP-section pointers / active governing DRs with bracketed reminders. Drafted post-walkthrough and reviewed in full; no operator changes requested.

### 3. "Open session N" / "Close session N" decision

Operator surfaced the question of whether the operator workflow could be simplified to typing only "Open session N" / "Close session N" with Claude reading `current_state.md` as the orientation source. Three rounds of discussion landed on: keep copy-paste opening prompts as the current workflow (load-bearing handoff with 41-session habit); produce `current_state.md` alongside the opening prompt at every close starting now; evaluate after two or three sessions whether `current_state.md` is reliable enough on its own to drop the opening prompt artefact. No commitment to switch — switch only on evidence. Captured in Category 2 of `standing_instructions.md`.

## Standing-instruction adherence check

- DR-021 timestamp anchor — clean (09:15 ACST open, 09:30 ACST close).
- Required reads completed in order — clean.
- Pre-flight directory listing before substantive work — clean.
- DR-027 / DR-028 / DR-029 named in orientation — clean.
- Desktop Commander / projects-filesystem routing — clean (one tool_search reload mid-close for start_process; recovered cleanly).
- Operator-facing presentation discipline (Session 39 standing) — held cleanly throughout. Section-by-section walkthrough was the proof of pattern.
- Don't-drift-to-alternatives — held cleanly. Operator stated governance work was today's priority; session executed against that without proposing alternatives.

## Open items

**No new substantive open items.** Carrying forward:

- WIP §16 (VPS in-flight work + metadata-backfill log-permission residual).
- WIP §17 (Saturday API observation probe — runs tomorrow).
- WIP §13 (§2.10 carry — to be substantially fed by probe report).
- Phase 1 of session operations proposal (create empty Claude Project) — Session 42 if probe-triage time permits.
- Phase 2 detailed `standing_instructions.md` review — operator may want a fresh pass at it once they've used it for a session or two.

## Session close state

- Rebuild folder root: 7 canonical .md + `current_state.md` + `standing_instructions.md` + `session_operations_proposal.md` = **10 .md files at root**, plus 6 subdirectories.
- WIP unchanged this session — stays in place during Phase 2 transition as fallback per Session 40 plan.
- `.close_out_backups/` empty.
- All `.DS_Store` files swept again at close (one had reappeared since Session 40).
- Probe brief unchanged.

## Forward to Session 42

Session 42 opens after Saturday's probe completes. Branches A/B/C apply per `current_state.md` and the Session 42 opening prompt below. Sixteenth consecutive non-early-close session.
