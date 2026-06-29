# Session 35 — Surgical-fix Code brief drafted (fixes 1+2 combined)

**Open:** 2026-04-30 15:32 ACST
**Close:** 2026-04-30 15:41 ACST
**Duration:** ~9 min
**Shape:** brief-drafting; single substantive deliverable

## Required reads completed

- `work_in_progress.md` (project state through Session 34 close)
- `sessions/SESSION_34.md` (full Session 34 outcomes — routing call, three fixes commissioned)
- `dr029/2_1_race_data/source_review_report.md` (full read; §5.1 anchors load-bearing for the brief, §"Anything surprising" entry on `racing-metadata-backfill.service` for Fix 2 detail)
- `dr029/dr029_scope.md` §2.1 close entry plus §2.6 carry-in (the framing the brief executes under)
- Pre-flight directory listing of rebuild folder root — clean (seven canonical .md at root, dr029/2_1_race_data/ holds five existing artefacts; sessions log up through SESSION_34.md plus SESSION_35_OPENING_PROMPT.md)

## Substantive deliverable

`dr029/2_1_race_data/surgical_fix_1_2_brief.md` — 243 lines, 18,747 bytes, SHA256 prefix `9c0a24de`. Eleven numbered sections: what-this-is-and-isn't / why fixes combine / pre-reads / VPS access (read-write) / Fix 1 anchors / Fix 2 anchors / sequencing within session / empirical verification with three SQL baseline queries / output spec / hard limits / what-happens-after.

## Calls made in the brief

1. **Fixes 1 and 2 combined into single Code session.** Architectural argument: Fix 1's bulk backfill produces a snapshot that decays without Fix 2's daily-service rework — together they are the full Cluster 1 result-population resolution. Operational argument: each fix is small (existing-code execution / systemd unit edit), one Code session covers both with budget to spare. Counter-case (split for cleaner attribution if interactions surface) considered and not adopted — `get_unsynced_dates()` already exists as a helper, Code isn't writing new logic.

2. **Sequencing — Fix 2 first, Fix 1 second.** Counter to the brief's name-order. Fix 2 Change A (chown the log file) is the smallest, lowest-risk action, clears the recurring failure first; Change B (script + systemd edit) benefits from manual smoke-test before Fix 1 starts writing data; Fix 1 then runs against a healthy daily-service baseline. Brief notes Code can deviate if a different order is operationally cleaner.

3. **Live-capture-start determined empirically, not hard-coded.** Source-review report referenced `--from 2026-03-02` as an example; brief asks Code to query `MIN(snapshot_time)` from `betfair_snapshots` and use that date. Backfill is idempotent so over-running is safe. Protects against documentation/reality drift.

4. **Fix 2 split into Change A (chown) and Change B (rework).** Change A is a one-line root command, sequenced first. Change B has two implementation options (B1 default-behaviour edit vs B2 new flag); brief leaves the call to Code based on existing CLI shape.

5. **Output spec — full report, not just diff.** Seven-section structure including pre/post-fix baseline numbers side by side. Makes Session 36's read tractable.

6. **Hard limits explicit on what's NOT in scope.** Fixes 3 and 4 named-and-excluded; the three pieces of named debt (no test coverage, no migration framework, monolithic orchestrator file) named-and-excluded; schema changes named-and-excluded. Reduces drift risk.

7. **Version control hygiene silent.** Considered and not added — would be friction without payoff for a 30-min surgical fix on a single-developer pipeline. Existing pipeline appears to run off whatever the working tree contains; over-prescribing branching at this scale is over-engineering.

## Operator review

Operator's response: "Go with your recommendations. I don't know much about this stuff." All six review questions accepted as drafted. Brief locked.

## Standing instructions held

- Plain-language operational/gambling-framed framing (Session 31, extended Session 34 to session-shape work). Held throughout — orientation framed in plain language ("don't rebuild, fix what's wired wrong"); review questions surfaced in operator-decision-maker form.
- Operational/analytical line discipline drift watch (Session 32). No drift surfaced this session — brief's framing keeps the surgical fix entirely VPS-side, no operational-line surface invoked.
- Filesystem discipline (Session 34 lesson). Used Desktop Commander's `write_file` for the brief; verified post-write via `ls -la` + `wc -l` + `shasum` against the Mac filesystem path.
- REPL discipline (Session 30). Not invoked this session — no multi-line Python needed.
- Pre-flight directory listing (Session 14 standing). Held at orientation completion.
- DR-027 / DR-028 / DR-029 named in orientation. Held.

## Tool routing

Session 35 = Claude Chat (delivered).
Out-of-session post-35 = Claude Code, surgical fix 1+2 execution against the brief.
Session 36 = Claude Chat, read of `surgical_fix_1_2_report.md` and decision on next surgical-fix brief (BSP write-back or cadence — operator's call which next).

## Tenth consecutive non-early-close session

Sessions 26-35 inclusive. Each scope-completed-as-load-bearing — surgical-fix brief was this session's load-bearing work, completed in 9 minutes because the source-review report's anchors were unusually clean and the operator's "go with your recommendations" closed review without iteration.

## Close-out

Single new file (`surgical_fix_1_2_brief.md`) written via Desktop Commander, verified post-write. WIP table row updated (Session 35 promoted from anticipated to DELIVERED; Session 36 row added). WIP "Where we are" updated for Session 35 close, Session 34 entry pushed down. WIP §1 open-question updated to reference the locked brief. `SESSION_35_OPENING_PROMPT.md` moved to `.close_out_backups/` per established convention. This session log written. No silent failures encountered — Session 34 lesson on `create_file` vs `write_file` held by using `write_file` exclusively for the rebuild folder.
