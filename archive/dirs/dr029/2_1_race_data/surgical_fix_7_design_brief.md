# DR-029 §2.1 — surgical-fix Code session 7 brief (Fix 7: merge-mechanism design probe + runner-level convergence finding consolidation)

**Status:** locked at Session 48 close (2026-05-01 ACST).
**Brief author:** operator-Claude Session 48.
**Code session:** out-of-session, single bounded run, read-only.
**Pre-read precedent:** Session 33's source-review brief (per-area assessment shape, design-document output).

---

## §1. What this brief is and is not

**Is:** a single-bounded, read-only design probe of `capture.db`'s `races` table merge mechanism. Code runs four investigative areas (existing-merge mechanism inspection, runner-row dedup state, survivor-row convention, dependent-table re-pointing). Code produces a structured design report proposing the merge-execution pattern with reasoning, plus any anomalies that block write-readiness. This is a *design document*, not a write operation — no rows are modified, no functions are edited, no schema changes are proposed for this brief's scope.

**Is not:** the merge-execution brief. The merge-execution brief follows in a future session, drafted against this report's findings. Code does not write the merge-execution brief — that is operator-Claude's next-session job per Cat 5 (operator-Claude division of labour). Code does not execute any merges. Code does not fix Fix 5 §7b (the runner-level convergence finding) — Code investigates *why* it's the way it is, and proposes a structural answer.

**Surprises become findings, not blockers.** If Code discovers an architectural concern that wasn't anticipated in this brief's scope, surface it in the report's anomalies section. Do not chase surprises into adjacent investigation; do not propose fixes outside the brief's named scope. If a surprise genuinely blocks the brief's primary questions from being answerable, surface that explicitly and stop — partial-but-coherent report beats full-but-drift report.

**Hard limits §10 are non-negotiable.** Single bounded Code session. Read-only on capture.db. No edits to source code anywhere. No git operations beyond `status` / `diff` for context.

---

## §2. Why this work exists

DR-029 §2.1 (the race-side data fit-for-purpose verification) closed-with-known-debt-named at Session 34. The surgical-fix arc through Sessions 35–47 progressively:

- (Fix 1+2) wrote race-result write-back and reworked `racing-metadata-backfill.service`.
- (Fix 3) wired BSP / sp_near / sp_far write-back paths.
- (Fix 5) lifted sponsor-with-hyphen + locality-prefix harmonisation into `normalise_venue`, produced 186-record dry-run merge plan.
- (Fix 6) broadened `normalise_venue` (sponsor-park, sponsor-no-hyphen, suffix near-miss) plus alias extension (`pioneer → alice springs`), produced **784-record consolidated dry-run merge plan at `dr029/2_1_race_data/fix_6c_proposed_merge.json`** (zero ambiguous, 58.6% of normal-race orphans newly mergeable).

Two open architectural questions stand between Fix 6's dry-run plan and a write brief:

1. **Runner-level convergence finding (Fix 5 report §7b).** 2,081 race-rows have already merged via overnight `racing-metadata-backfill.service` runs. Yet the runner-level cross-tab `with_both` (runners with both `finish_position` AND `betfair_selection_id` populated) **remained at 0**. Race-level merged; runner-level didn't follow. The mechanism by which runner-rows are (or aren't) being consolidated when their parent race-rows merge is unknown.

2. **Survivor-row + dependent-table re-pointing.** The `races` table has a `UNIQUE(race_date, venue_normalised, race_number)` constraint. Five dependent tables carry `race_id INTEGER NOT NULL REFERENCES races(id)` — `runners`, `betfair_snapshots`, `bookmaker_snapshots`, `betfair_historical`, `snapshot_batch_summary`. A merge-execution brief that just `UPDATE`s Betfair-side fields onto the RA-side row would leave the original LC-side row intact (orphaning its dependent rows), and re-pointing dependent rows requires understanding what survivor-row convention the existing service uses (or whether it uses any).

This brief commissions Code to answer both questions empirically. The output is the structural foundation for the write brief.

---

## §3. Pre-reads

**Required:**

1. `dr029/2_1_race_data/surgical_fix_6_brief.md` — the brief that produced `fix_6c_proposed_merge.json`.
2. `dr029/2_1_race_data/surgical_fix_6_report.md` — Fix 6 outcomes, especially §6C totals and the 784-record plan structure.
3. `dr029/2_1_race_data/surgical_fix_5_report.md` — particularly §7b (the runner-level convergence finding).
4. `dr029/2_1_race_data/surgical_fix_3_report.md` — for the metadata-backfill service rework context (Fix 1+2 + Fix 3 reshaped this service).
5. `dr029/2_1_race_data/source_review_report.md` — for the original race-key match logic anchor.

**Reference-only (read on demand):**

- `dr029/2_1_race_data/fix_6c_proposed_merge.json` (1.6 MB, 3,249 records — the dry-run merge contract this design serves).
- `dr029/2_1_race_data/inspection_report.md` — original §2.1 inspection report from Session 28.
- `dr029/dr029_scope.md` — for §2.1 scope boundaries.
- `decisions.md` — DR-027 (two-database architecture) and DR-028 (cross-database integration discipline) for cross-DB context.

**Not required:** `architecture.md`, `vision.md`, `governance.md`, `standing_instructions.md`, `project_context.md`, `current_state.md`. Code does not need operator-facing planning context.

---

## §4. System access

**capture.db** at `/home/racing/racing-data-capture/data/capture.db` on VPS `root@187.77.183.9`. **Read-only access** — every SQL query opens via `sqlite3 file:...?mode=ro` URI or equivalent Python read-only connection. No `INSERT`, no `UPDATE`, no `DELETE`, no `CREATE`, no `DROP`, no `PRAGMA` that mutates state.

**Source tree** at `/home/racing/racing-data-capture/` on VPS. **Read-only access** — `git status` and `git diff` for context, `cat` / `grep` for source inspection. No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), `git reset`. No `vim` / `sed` / file edits.

**Adelaide local timestamps per DR-021** for every time-of-day reference in the report (open, close, key probe milestones).

**Tunnel** — if SSH access drops mid-session, restart via the existing pattern; do not chase tunnel diagnostics into adjacent investigation.

---

## §5. Substantive scope — four investigative areas

Code runs the four areas in the order named. Each area has anchored questions Code is asked to answer with empirical data and a proposed structural answer where the brief asks for one. **Areas are not collapsed** — keep findings separated even where Area B's findings inform Area C's reasoning.

### §5.1 — Area A: Existing-merge mechanism inspection

**Anchored question:** what does `racing-metadata-backfill.service` actually do when it consolidates a race-row that has both an RA-side orphan and a Betfair-side counterpart?

**Empirical probes:**

1. Read `racing-metadata-backfill.service` source on VPS. Identify the merge function(s) — likely in `matching/race_matcher.py` or `matching/metadata_backfill.py` (Code locates by inspection). Capture the merge function's logic in the report's §A.

2. Inspect the 2,081 already-merged races (`subscription_synced_at IS NOT NULL AND betfair_win_market_id IS NOT NULL`). Sample 5 representative merged races (vary venue, race_date, capture_status). For each, check:
   - Does the merged row carry a single consolidated set of fields, or are there still orphan rows that share the same `(race_date, venue_normalised, race_number)`?
   - What `match_method` value does the merged row carry? What `match_confidence`?
   - When was the merge written (`updated_at` timestamp)? Does it correlate with metadata-backfill service runs?

3. **Critical check:** are there any pairs of `races` rows that have different `id` values but the same `(race_date, venue_normalised, race_number)` post-Fix-6-`normalise_venue`? (i.e., has Fix 6's regex broadening created any rows that *would* now be UNIQUE-violating if a merge fired today?)

**Proposed structural answer:** describe the existing service's merge mechanism in 1-2 paragraphs. Name whether it `UPDATE`s an existing row, `INSERT`s a new row + cleans up the old, or operates differently.

### §5.2 — Area B: Runner-row dedup state (Fix 5 §7b consolidation)

**Anchored question:** why is runner-level `with_both` (runners with both `finish_position` AND `betfair_selection_id`) at 0 despite 2,081 race-level merges? Where are the runner rows pointing?

**Empirical probes:**

1. For each of the 5 sample merged races from §5.1, inspect the runner-row state:
   - How many `runners` rows point at the merged race's `id`?
   - Of those, how many carry `finish_position` populated? How many carry `betfair_selection_id` populated? How many carry both?
   - Are there orphan runner-rows pointing at *deleted* race-row IDs? (i.e., runner-rows whose `race_id` no longer matches any row in `races`)
   - Are there pairs of runner-rows pointing at the same merged race's `id` that represent the same physical horse but were captured by different sources (one via subscription, one via Betfair)?

2. **Cross-tab probe:** for the full population of `runners` rows whose `race_id` is in the 2,081 merged set, count:
   - Total runner-rows.
   - Runner-rows with `finish_position` populated only.
   - Runner-rows with `betfair_selection_id` populated only.
   - Runner-rows with both.
   - Runner-rows with neither.

3. **Side-source probe:** is there evidence that the existing metadata-backfill service is even *attempting* runner-row consolidation? Or does it consolidate at race-level only, leaving runner-rows un-touched? Read the merge function source from §5.1's findings to confirm.

**Proposed structural answer:** name the runner-row situation in 1-2 paragraphs. Is it that (a) runner-rows are duplicated and need dedup; (b) runner-rows aren't consolidated at all so the survivor-race has only one source's runners; (c) something else. Propose what runner-row handling the merge-execution brief would need to commission.

### §5.3 — Area C: Survivor-row convention

**Anchored question:** when two `races` rows merge (RA-side orphan with `subscription_synced_at` populated + LC-side counterpart with Betfair fields populated), which row should survive?

**Empirical probes:**

1. From §5.1's findings, identify what convention the existing service uses (if any). Does it preserve the LC-side row's `id`, the RA-side row's `id`, or create a new row?

2. Cross-check against the JSON merge plan. `fix_6c_proposed_merge.json` records carry `orphan_race_id` (RA-side) and `target_race_id` (LC-side). Which one is the survivor under the existing service's convention?

3. **Constraint conflict check:** for the 784 clean records in `fix_6c_proposed_merge.json`, would the existing service's convention produce any `UNIQUE(race_date, venue_normalised, race_number)` violations? Specifically:
   - For day-shift records (21), the survivor's `race_date` differs between sides — which side's `race_date` wins?
   - For alias-resolved records (52), the survivor's `venue_normalised` differs — which side's wins?
   - For exact-key records (711), `(race_date, venue_normalised, race_number)` should match post-Fix-6 — confirm empirically.

4. **Dependent-table impact:** for each survivor-row convention candidate (LC-side wins, RA-side wins, new-row created), enumerate which dependent tables have their `race_id` references invalidated and need re-pointing.

**Proposed structural answer:** propose a survivor-row convention with reasoning. Identify which side's `id` survives, which side's fields are copied where, which dependent rows need re-pointing, and how the UNIQUE constraint is handled for day-shift / alias-resolved records.

### §5.4 — Area D: Dependent-table re-pointing pattern

**Anchored question:** for the survivor-row convention proposed in §5.3, what's the safe pattern for re-pointing dependent rows in the five dependent tables (`runners`, `betfair_snapshots`, `bookmaker_snapshots`, `betfair_historical`, `snapshot_batch_summary`)?

**Empirical probes:**

1. For each of the five dependent tables, count the volume of rows that would need re-pointing across the 784 merge candidates. (Approximate counts from sampled merges, multiplied — Code does not run the full 784-record probe; sample sufficient to scale-estimate.)

2. Identify any dependent-table-level UNIQUE constraints that could be violated by re-pointing:
   - `runners` UNIQUE on `(race_id, runner_key)` — could two runners pointing at different race-rows now collide on the survivor?
   - `betfair_snapshots` UNIQUE on `(race_id, runner_id, snapshot_time)` — same risk.
   - `bookmaker_snapshots` UNIQUE on `(race_id, runner_id, snapshot_time, bookmaker)` — same risk.
   - `betfair_historical` UNIQUE on `(bf_win_market_id, bf_selection_id)` — independent of `race_id`, but `race_id` references would still need updating.
   - `snapshot_batch_summary` UNIQUE on `(batch_id, race_id, source)` — same risk.

3. **Transactional-safety probe:** is the existing service running its merges inside a SQLite transaction (single `BEGIN ... COMMIT`)? Or row-by-row? Or some hybrid? Read the merge function's transaction handling from §5.1's findings.

4. **Idempotency probe:** if the merge-execution script were re-run (after partial completion or operator-driven re-run), would it cleanly skip already-merged pairs, or would it double-process? Inspect for idempotency markers in the existing service.

**Proposed structural answer:** propose a re-pointing pattern with reasoning. Name the SQL pattern (`UPDATE <dep_table> SET race_id = :survivor WHERE race_id = :victim`), the transactional envelope (single transaction over all 784 merges, or batched, or per-merge), and the idempotency marker (e.g. check `survivor.match_method` for a sentinel value before re-processing).

---

## §6. Sequencing within session

A → B → C → D in order. The dependency:

- A grounds the existing service's behaviour. B and C both build on A's findings about the merge function.
- B (runner-row dedup) is logically downstream of A (race-row mechanism) but does not depend on C or D.
- C (survivor convention) depends on A and benefits from B's findings.
- D (dependent-table re-pointing) depends on C's proposed convention.

If A reveals that the existing service does **not** in fact merge race-rows at all (i.e., the 2,081 already-merged races got their state via some other mechanism — Betfair-side write to a row that already had subscription data, or vice versa, no actual row-consolidation step), then B / C / D's framing shifts. In that case:

- Proceed with B / C / D as **a fresh design proposal** rather than as inspection of an existing pattern.
- Surface this finding loud in §A's report — operator-Claude needs to know the architectural baseline is different than the brief assumed.

---

## §7. Empirical verification (success / failure criteria)

**Success criteria:**

- §5.1 / Area A: existing service's merge mechanism named in 1-2 paragraphs with code references. The 5-sample merged-race inspection produces a clear pattern (or names that there's no clear pattern, with reasoning).
- §5.2 / Area B: runner-level `with_both = 0` is mechanistically explained. Cross-tab numbers reported. Proposed runner-row handling for merge-execution brief named.
- §5.3 / Area C: survivor-row convention proposed with reasoning. UNIQUE constraint conflicts checked across all 784 clean records.
- §5.4 / Area D: re-pointing pattern proposed for all 5 dependent tables. Volume estimates produced. Transactional and idempotency calls named.

**Failure criteria (escalate as report findings, do not chase fixes):**

- A's source inspection reveals the merge function but the function's logic is opaque or doesn't match the empirical state of the 2,081 merged rows. Surface as anomaly; do not investigate further.
- B's runner-row probe reveals dedup state that contradicts §5.2's anchored question framing (e.g. `with_both` is actually nonzero). Surface as anomaly with corrected counts; reframe B's proposed answer accordingly.
- C's UNIQUE-constraint check reveals violations even under the proposed convention. Surface as a blocker; the merge-execution brief cannot proceed without resolution.
- D's re-pointing volume estimates indicate the merge-execution session would exceed reasonable Code-session budget (e.g. multi-million row updates). Surface as a sequencing concern; the merge-execution brief may need batching.

---

## §8. Output spec

**Single file** at `dr029/2_1_race_data/surgical_fix_7_design_report.md`.

**Section structure:**

1. Headline (3-5 sentences — what was found, what's proposed, what's blocked if anything).
2. §A — existing-merge mechanism inspection (findings + proposed structural answer).
3. §B — runner-row dedup state (findings + proposed structural answer).
4. §C — survivor-row convention (findings + proposal).
5. §D — dependent-table re-pointing pattern (findings + proposal).
6. §6 — anomalies (anything surfaced from the four areas that doesn't fit cleanly into the area's own findings).
7. §7 — self-assessment (brief scope adherence, hard limits held, what moved, what didn't).
8. §8 — proposed merge-execution brief shape (1-2 paragraphs naming what the next brief should cover, given §A-D findings).

**Length anticipation:** 350-500 lines. Heavier than a surgical-fix report because four investigative areas each carry findings + proposed structural answer. If Code's report would exceed ~600 lines, surface as a self-assessment finding (the design space may be larger than this brief anticipated).

**Output does NOT contain:**

- The merge-execution brief itself (operator-Claude's job, next session).
- Any source-code edits, even proposed ones (the report names *what* the merge-execution brief should commission, not *how* it should be implemented).
- Any data writes (read-only brief).
- Recommendations on whether to proceed with merge-execution at all (operator-Claude's call, against the report findings).

---

## §9. Hard limits

§9.1 **Single bounded Code session.** Estimated 60-90 minutes for the four investigative areas. If the work is larger, surface as a finding — partial-but-coherent report beats over-budget chase.

§9.2 **Read-only on capture.db.** Every connection opens read-only (`sqlite3 file:...?mode=ro&immutable=1` URI or `Connection(..., mode='ro')` Python). No `INSERT`/`UPDATE`/`DELETE`/`CREATE`/`DROP`. Verification snippets confined to `/tmp/`.

§9.3 **Read-only on source tree.** No `git add`, no `git commit`, no `git stash`, no `git restore`, no `git checkout`, no `git reset`. Only `git status`, `git diff`, `git log` for context. No file edits anywhere.

§9.4 **No edits to `matching/race_matcher.py` or `BETFAIR_VENUE_ALIASES`.** Fix 6 closed the venue-harmonisation arc; further venue work is out of scope.

§9.5 **No edits to `bookmakers/sportsbet.py` or any other source file.** Code does not propose source-level changes; the report names what a future brief would need to commission, not what to write.

§9.6 **No DR-029 named-debt remediation.** No test coverage, no migration framework, no monolithic-orchestrator refactoring.

§9.7 **No mid-session escalation.** Code runs end-to-end. If §5.1's findings reframe §5.2-§5.4's questions, Code reframes within the same session and continues. No pinging operator-Claude mid-flight.

§9.8 **No merge execution.** This brief produces a design document, not data writes.

§9.9 **No deletion of `fix_5c_proposed_merge.json` or `fix_6c_proposed_merge.json`.** Both remain in place as merge contracts (5C historical, 6C active).

§9.10 **No speculative scope expansion.** Code answers the four anchored questions in §5.1-§5.4. Adjacent investigations (e.g. Betfair Streaming, soft-book interface, sports-side merge mechanism) are out of scope. If a finding suggests a follow-up area, name it as a §8 brief-shape recommendation; do not investigate it.

§9.11 **No runner-key probing beyond §5.2's scope.** Fix 5 §7b's runner-level convergence is investigated mechanistically (why is `with_both = 0`?), not solved. The merge-execution brief or a future Fix 8 handles solution.

§9.12 **VPS dirty-tree state preserved.** `git status --short` at session end matches session start (11 modified, 7 untracked baseline from Fix 6). No new files outside `/tmp/`. No `.pyc` cleanup or any other tidiness drift.

---

## §10. What happens after Code's session

Operator-Claude reads `surgical_fix_7_design_report.md` at next session open. Triage shape:

- Read §A — existing service's merge mechanism. Confirm or update operator-Claude's mental model.
- Read §B — runner-row dedup state. Decide whether runner-row handling is in-scope for the merge-execution brief or needs its own brief (Fix 8).
- Read §C — survivor-row convention. Operator-Claude evaluates the proposal against architectural priorities (DR-027 / DR-028 cross-DB discipline, though this is intra-`capture.db` so discipline is lighter).
- Read §D — re-pointing pattern. Identify any volume / transactional concerns that affect the merge-execution brief shape.
- Read §6 — anomalies. Triage each: blocking, parking-lot, or fold into next brief.
- Read §8 — proposed merge-execution brief shape. Decide whether to commission directly or revise.

Default forward routing: **commission the merge-execution brief** (Fix 8) reading `fix_6c_proposed_merge.json` against the design from this report. Estimated brief size 350-500 lines. If §B reveals runner-row handling needs its own brief, sequence is: Fix 8 (merge-execution race-level) → Fix 9 (runner-row dedup). If §C / §D reveal blockers, the path branches.

**Operator-Claude does not commission Fix 8 within Session 49 if §6 surfaces architectural blockers.** In that case, Session 49 surfaces blockers and routes to operator decision before any further Code commissioning.

---

## §11. Cross-references

- **DR-029 §2.1** — race-side data fit-for-purpose verification (active arc).
- **DR-027 / DR-028** — cross-database integration discipline (intra-`capture.db` work, so DR-027/028 not directly invoked, but the survivor-row convention should respect the spirit: BetHub owns operational state, capture.db owns analytical/source data; merge work happens within capture.db, BetHub is not affected).
- **DR-021** — Adelaide local timestamps throughout report.
- **`dr029/2_1_race_data/surgical_fix_5_report.md` §7b** — runner-level convergence finding, folded into §5.2 (Area B) of this brief.
- **`dr029/2_1_race_data/surgical_fix_6_report.md` §6C** — 784-record dry-run merge plan that this design serves.
- **`dr029/2_1_race_data/source_review_report.md`** — original race-key match logic anchor.
- **Parking-lot items not in scope:** Saturday API observation probe (separate brief, runs tomorrow); Fix 4 cadence brief (waits on probe); §2.10 external analytics scan (separate scope-doc item); pending architectural extension "Betfair as canonical source extending to softbook bets" (post-DR-029 documentation pass).

---

## §12. Brief metadata

**Brief locked:** Session 48 close, 2026-05-01 ACST.
**Anticipated Code session timing:** out-of-session, operator's choice. ~60-90 min wall-clock estimate.
**Anticipated report size:** 350-500 lines.
**Estimated dependent-area sample sizes:** 5 representative merged races (§5.1, §5.2); 784-record full-population checks (§5.3, §5.4 light probes).
**This brief supersedes:** none. Replaces the verbal placeholder where "Fix 7" was tentatively reserved for the Fix 5 §7b runner-level finding alone — that finding now folds into Fix 7's broader scope, and the eventual merge-execution becomes Fix 8.
