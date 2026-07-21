# DR-029 §2.1 — surgical-fix Code session 5 brief (Fix 5: venue harmonisation + retroactive merge + edge-case probe)

**Brief locked:** 2026-05-01 [time at lock] ACST.
**Authoring session:** Session 46 (operator-Claude).
**Target:** out-of-session Claude Code, single bounded session against `root@187.77.183.9` (`/home/racing/racing-data-capture/`).
**Estimated runtime:** 60-90 minutes.

---

## 1. What this brief is and is not

**Is.** A surgical fix to the venue-normalisation drift identified in `surgical_fix_1_2_report.md` §5. Three named §-sections, executed in a single Code session, in the order written:

- **§5A — lift `_clean_venue` into `matching/race_matcher.normalise_venue`** so future Racing API and bookmaker discoveries land on a single canonical venue string.
- **§5B — diagnostic probe of the `warwick farm`-style edge case** where venue_normalised aligns but rows still don't merge.
- **§5C — dry-run retroactive merge** of the 1,266 Racing-API-only orphan race rows into their matching live-capture rows. Dry-run only — Code produces a proposed-merge report, does not execute the merge.

**Is not.** Not a continuation of Fix 4 (cadence work, blocked on Saturday probe). Not a BSP / sp_near / sp_far follow-up (Fix 3, separate Code session). Not a remediation of named DR-029 debt (no test coverage, no migration framework, monolithic orchestrator file). Not a commit/stash of the operator's in-flight dirty-tree work.

Surprises become **findings in the report**, not blockers. If §5C dry-run surfaces edge cases beyond the warwick-farm class, Code names them and stops at dry-run — the actual merge execution is a separate session commissioned after operator-Claude triage.

---

## 2. Why this work exists

`surgical_fix_1_2_report.md` §5 surfaced the root cause of the unchanged `with_both` cross-tab (rows carrying both `finish_position` AND `betfair_selection_id`) post-Fix 1+2. The Racing API path (`subscription/racing_api.py:_sync_single_race`) and the live-capture path read identical Racing API responses but produce different `venue_normalised` values for the same race because Racing API path does not strip sponsor or locality prefixes that the bookmaker-side `bookmakers/sportsbet.py:_clean_venue` already strips.

Sample Racing-API-only orphan venues post-Fix 1+2:

```
southside cranbourne     : 213 races
southside pakenham       : 155 races
sportsbet-ballarat       :  66 races
royal randwick           :  42 races
sportsbet-wangaratta     :  33 races
aquis park gold coast    :  30 races
toowoomba inner track    :  27 races
sportsbet oakbank        :  26 races
ladbrokes geelong        :  21 races
bet365 park kilmore      :  22 races
sunshine coast@inner track: 15 races
devonport tapeta synthetic: 15 races
warwick farm (edge case) :  15 races
```

Race-level merge stats post-Fix 1+2:

```
has_subscription_sync | has_betfair_capture | count
0                     | 0                   | 17,377
0                     | 1                   |  8,327
1                     | 0                   |  1,266
1                     | 1                   |      0   ← zero merges
```

§5A closes the venue-prefix-drift cause forward. §5B characterises the residual `warwick farm` class (13-15 venues) where venue alignment doesn't trigger merge — likely race_date timezone or race_number drift, but unconfirmed. §5C produces a proposed-merge report grounded in §5A's harmonised normalisation, surfacing how many of the 1,266 orphan rows would merge cleanly and how many remain for follow-up.

---

## 3. Pre-reads

Required:

- `dr029/2_1_race_data/surgical_fix_1_2_report.md` — full. §5 is the load-bearing root-cause analysis; §6 names §5A and §5C as the next-session candidates.
- `dr029/2_1_race_data/source_review_report.md` — §5.1 anchor (race-key match logic in `subscription/racing_api.py:_sync_single_race`, `compute_runner_key` rules, `upsert_race` semantics).
- `dr029/2_1_race_data/vps_drift_check.md` — §3 (dirty file inventory), §7 (Fix 5 implications). The dirty-tree handling pattern is the same as Fix 3's brief — the discipline is the discipline.

Reference-only (read on demand):

- `dr029/2_1_race_data/surgical_fix_1_2_brief.md` — for hard-limits language and dirty-tree hard-limits precedent.
- `dr029/2_1_race_data/surgical_fix_3_brief.md` — for §10 dirty-tree conditional language precedent.
- `dr029/dr029_scope.md` §2.1 — for the wider Cluster 1 routing context.

---

## 4. System access

- **VPS shell access:** SSH `root@187.77.183.9`. All commands run from `/home/racing/racing-data-capture/`.
- **Filesystem:** read-write on `matching/race_matcher.py`. Read-only on `bookmakers/sportsbet.py` (the source for the lift). Read-only on `subscription/racing_api.py` (callsite verification only — no edit).
- **Database:** `data/capture.db` — read-only for §5B and §5C. The `sqlite3 'file:.../capture.db?mode=ro'` URI form is canonical. **No write to `data/capture.db` in this session.** §5C produces a proposed-merge report, not an executed merge.
- **Git:** read-only on the working tree. **No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), `git reset`.** See §9.
- **Adelaide local timestamps per DR-021** — every time-of-day reference in the report uses ACST/ACDT explicitly (e.g. `2026-05-01 17:30 ACST`).

---

## 5. Substantive scope

### §5A — Lift `_clean_venue` into `matching/race_matcher.normalise_venue`

**Anchors:**

- Source: `bookmakers/sportsbet.py:_clean_venue` (lines 52-66 per source-review report; verify line range pre-edit since the file is dirty).
- Target: `matching/race_matcher.py:normalise_venue` (lines 60-79 per source-review report; verify line range pre-edit).
- Callsite verification only: `subscription/racing_api.py:_sync_single_race` line 209-223 (calls `normalise_venue(course)` — confirm it receives the harmonised function automatically, no edit).

**The lift:**

1. Read `bookmakers/sportsbet.py` lines 52-66 (or the current `_clean_venue` location after dirty-tree verification). Capture the function's full body verbatim.
2. Open `matching/race_matcher.py`. Identify `normalise_venue` body. The current implementation strips a small fixed suffix list (`" park"`, `" racecourse"`, `" races"`, `" race club"`).
3. Modify `normalise_venue` to apply the `_clean_venue` logic **before** the existing suffix-stripping. Specifically:
   - Strip sponsor prefixes via `re.sub(r"^[A-Za-z]+-", "", raw)` (matching `Sportsbet-`, `Ladbrokes-`, `Bet365-`, etc.).
   - Strip locality prefixes via `re.sub(r"^(Northside|Southside|Eastside|Westside|South|North|East|West|New|Old|Upper|Lower)\s+", "", raw)`.
   - Strip naming-decoration suffixes — review what `sportsbet.py:_clean_venue` does for `@Inner Track`, `Tapeta Synthetic`, `Inner Track` and replicate. Code's discretion on whether these belong in `_clean_venue` (and thus get lifted) or whether they're already handled by the existing suffix strip.
   - Then apply the existing suffix-stripping as it stands today.
4. After the lift, `normalise_venue` is the canonical normaliser. Bookmaker-side `_clean_venue` may now be redundant — **do not delete it in this session.** Leave `bookmakers/sportsbet.py` untouched. Operator-Claude will route any consolidation in a later pass.

**Hard limits §5A:**

- No edits to `bookmakers/sportsbet.py` or any other bookmaker file.
- No edits to `subscription/racing_api.py`.
- No schema changes.
- No new modules, no new files.
- Edit only `matching/race_matcher.py:normalise_venue` and any helper imports it requires (e.g. `import re` if not already present at module top — check first).

**Verification §5A:**

- Pre-edit: `git diff matching/race_matcher.py` to confirm only the existing tabtouch one-line change is present (per `vps_drift_check.md` §3).
- Post-edit: `git diff matching/race_matcher.py` should show the existing tabtouch line PLUS the `normalise_venue` body change. No other lines.
- Functional: write a small inline test snippet (in a temp file under `/tmp/`, not in the project tree) that calls `normalise_venue` on the orphan-venue sample list from §2 above and confirms each one harmonises to its expected canonical form. Capture the input → output mapping in the report. Do not commit the test snippet.

### §5B — Edge-case diagnostic probe

**Question.** Why do `warwick farm` (and ~12 similar venues) appear in BOTH the Racing-API-only orphan list AND the live-capture orphan list, with venue_normalised aligned, yet still not merge?

**Probe queries** (read-only, against `data/capture.db`):

1. For each of the 13 edge-case venues identified in `surgical_fix_1_2_report.md` §5, list the `(race_date, venue_normalised, race_number)` tuples present on both sides:
   - Racing-API-only side: rows where `subscription_synced_at IS NOT NULL AND betfair_market_id IS NULL`.
   - Live-capture-only side: rows where `betfair_market_id IS NOT NULL AND subscription_synced_at IS NULL`.
2. For each candidate match (same venue_normalised, same race_number), inspect `race_date` UTC vs Adelaide-local. Hypothesis: Racing API uses `/australia/meets/{id}/races` returning UTC-date strings; the live-capture orchestrator records `race_date` from bookmaker-supplied fields which may be Adelaide-local. A race scheduled `2026-04-15 23:30 Adelaide` (`2026-04-15 13:30 UTC`) would appear under different `race_date` values.
3. Count the proportion of edge-case orphans that resolve via timezone-shift hypothesis (race_date differs by exactly one calendar day). Report:
   - Total edge-case orphan races inspected.
   - Resolved by timezone-shift hypothesis: count and percentage.
   - Resolved by race_number drift: count.
   - Unresolved (different cause): count, with a sample of 5 rows showing both sides verbatim.

**Hard limits §5B:**

- Read-only. No writes to `capture.db`. No code edits.
- Single Python script in `/tmp/` or inline `sqlite3` invocations. Do not commit.
- Time-box: 15 minutes of probe work. If the cause is unresolved at that point, report the partial findings and move to §5C.

### §5C — Dry-run retroactive merge

**Goal.** Produce a proposed-merge report for the 1,266 Racing-API-only orphan race rows, grounded in §5A's harmonised `normalise_venue`. **Do not execute the merge.** The execution is a separate Code session commissioned after operator-Claude triage of this dry-run report.

**Method:**

1. Re-run §5A's harmonised `normalise_venue` against every Racing-API-only orphan race row's `venue_normalised` value. (The orphans were upserted using the OLD `normalise_venue` — re-applying the new function gives the canonical key the row should now carry.)
2. For each orphan row, search the live-capture-only set for a candidate match on `(race_date, harmonised_venue, race_number)`.
3. Apply §5B's findings: if the timezone-shift hypothesis is confirmed for edge cases, broaden the race_date match to ±1 day for the affected venues.
4. Categorise outcomes:
   - **Clean merge:** orphan row matches exactly one live-capture row by harmonised key. Report orphan `race_id`, target `race_id`, and the runner-row transfer that would occur.
   - **Ambiguous:** orphan row matches multiple live-capture rows. Report all candidates; flag for operator-Claude review.
   - **No match:** orphan row matches no live-capture row. Report orphan `race_id`, harmonised venue, race_date, race_number; flag as "remains orphan post-harmonisation".
5. **Write the proposed-merge plan as a JSON file** at `dr029/2_1_race_data/fix_5c_proposed_merge.json`, with one record per orphan row carrying: `orphan_race_id`, `outcome` (clean / ambiguous / no_match), `target_race_id` (if clean), `candidate_race_ids` (if ambiguous), `reason` (if no_match). This file is the contract for the future merge-execution session.

**Hard limits §5C:**

- Read-only on `capture.db`. No INSERT, UPDATE, DELETE.
- Single output file at `dr029/2_1_race_data/fix_5c_proposed_merge.json`. Do not write any other artefact.
- The actual merge execution is **out of scope.** A future brief will commission it.

---

## 6. Sequencing within session

Order: §5A → §5B → §5C. Reasoning:

- §5A must land first because §5C re-applies the harmonised `normalise_venue` against the orphan set; §5C cannot run cleanly until §5A is in place.
- §5B can technically run before or after §5A (it's read-only), but running it second means §5C can fold §5B's findings into its match logic.
- §5C runs last and produces the outbound artefact.

If §5A lands but functional verification fails (the orphan-venue sample list doesn't harmonise as expected), **stop**. Do not run §5B or §5C against a broken normaliser. Surface the failure in the report; operator-Claude triages.

If §5B runs over its 15-minute time-box, **stop §5B at the partial point and proceed to §5C** with whatever findings are in hand.

---

## 7. Empirical verification — pre and post

**Pre-fix baseline (capture before any §5A edit):**

```sql
-- B1: race-level merge stats (compare to surgical_fix_1_2_report.md §5)
SELECT
  CASE WHEN subscription_synced_at IS NOT NULL THEN 1 ELSE 0 END AS has_subscription_sync,
  CASE WHEN betfair_market_id IS NOT NULL THEN 1 ELSE 0 END AS has_betfair_capture,
  COUNT(*) AS count
FROM races
WHERE race_date >= '2026-03-02'
GROUP BY 1, 2;

-- B2: with_both runners
SELECT COUNT(*) AS with_both
FROM runners r
JOIN races ra ON r.race_id = ra.race_id
WHERE ra.race_date >= '2026-03-02'
  AND r.finish_position IS NOT NULL
  AND r.betfair_selection_id IS NOT NULL;

-- B3: orphan-venue distribution (top 20)
SELECT venue_normalised, COUNT(*) AS races
FROM races
WHERE race_date >= '2026-03-02'
  AND subscription_synced_at IS NOT NULL
  AND betfair_market_id IS NULL
GROUP BY venue_normalised
ORDER BY races DESC
LIMIT 20;
```

**Post-§5A verification:**

- Functional verification snippet output (input → output mapping for the orphan-venue sample) included in the report.
- B1, B2, B3 re-run is **not expected to move** post-§5A — §5A only changes the function; existing rows still carry the old `venue_normalised` values until §5C's merge executes (which is out of scope for this session). Report this explicitly so the next operator-Claude session reads the unmoved cross-tab as expected, not as a Fix-5A failure.

**Post-§5C (dry-run report):**

- Total orphan races inspected: should equal 1,266 (or whatever the current count is — the orphan set will have grown since the Fix 1+2 report; capture the current number).
- Clean-merge count.
- Ambiguous-match count.
- No-match count.
- Sum of the three == total orphan races.

---

## 8. Output spec

**Single file:** `dr029/2_1_race_data/surgical_fix_5_report.md`.

**Plus one auxiliary artefact:** `dr029/2_1_race_data/fix_5c_proposed_merge.json` (the dry-run merge plan).

**Section structure for the report:**

1. Headline (1-2 sentences: did §5A land cleanly? did §5C produce a usable merge plan?).
2. What was done (per-§ summary).
3. Pre-fix baseline numbers (B1, B2, B3).
4. §5A execution log (diff of `matching/race_matcher.py`, functional verification snippet results, post-edit `git diff` confirmation).
5. §5B probe results (timezone-shift hypothesis confirmation, breakdown of edge-case orphans by cause).
6. §5C dry-run merge plan summary (clean / ambiguous / no_match counts; top-10 sample of each category; pointer to the JSON file).
7. Anything surprising.
8. Self-assessment (brief scope adherence, hard limits held, what moved, what didn't).

**Length anticipation:** 200-280 lines for the report. JSON file size will scale with orphan count (likely 200-400 KB at 1,266 rows).

**The report does NOT contain:**

- Recommendations for Fix 6 / future scope.
- A verdict on whether the Cluster 1 surgical-fix arc is "done" — that's operator-Claude's call in the next session.
- Edits or changes to any file beyond `matching/race_matcher.py`.
- Execution of the merge plan.

---

## 9. Hard limits — non-negotiable

1. **Single bounded Code session.** If the work doesn't fit, that's a finding, not a continuation. Partial-but-coherent beats complete-but-lost-coherence.
2. **Named anchors only.** Edit `matching/race_matcher.py:normalise_venue` and nothing else in the codebase. No drift into adjacent files "while we're here".
3. **No schema changes.** No `ALTER TABLE`, no new columns, no new indexes.
4. **No DB writes.** §5B and §5C are read-only. Any `INSERT`, `UPDATE`, `DELETE` against `capture.db` is out of scope.
5. **No commit / stash / restore.** The git working tree is dirty (per `vps_drift_check.md` §3). Operator's in-flight work stays untouched. No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), or `git reset`.
6. **No remediation of named DR-029 debt.** No test coverage added (a `/tmp/` verification snippet for §5A is fine; no `tests/` directory creation). No migration framework. No orchestrator file restructure.
7. **No mid-session escalation.** If §5B's hypothesis fails or §5C surfaces unexpected match shapes, capture the findings in the report and complete the session. Do not pause to ask operator-Claude for direction mid-flight.
8. **No edits to `bookmakers/sportsbet.py`.** It is the source for the lift, not a target. Even the redundant `_clean_venue` after the lift stays in place — operator-Claude routes any consolidation later.
9. **No execution of the proposed merge.** §5C produces a plan; the plan is the deliverable.

---

## 10. Dirty-tree handling

The VPS git working tree is dirty per `vps_drift_check.md` §3. Eight modified files plus untracked `api/` subtree and `bookmakers/tabtouch.py`. None of the dirty changes intersect §5A's edit anchors at the line level. The dirty handling discipline:

1. **Read working-tree state at session start.** Run `git status` and `git diff --stat`. Confirm the dirty file list matches `vps_drift_check.md` §3 (allowing for any newly-modified files since 2026-04-30; surface any unexpected dirty files in the report).
2. **`matching/race_matcher.py` is dirty** with a single tabtouch line addition. The §5A edit lands in the `normalise_venue` body; verify the tabtouch addition is in a different region of the file before editing. After §5A's edit, `git diff matching/race_matcher.py` should show the tabtouch line PLUS §5A's `normalise_venue` change — nothing else.
3. **`bookmakers/sportsbet.py` is dirty** (the 226-line rewrite that contains `_clean_venue`). Read the dirty version as the source of truth — the lift should reflect what's actually running, not any hypothetical clean-HEAD version. Do not edit this file.
4. **Post-edit, run `git status`** to confirm the dirty file list grew by zero (only `matching/race_matcher.py`'s diff grew). If any new file appears dirty or untracked, surface in the report.
5. **Do not commit, stash, or restore anything.** This includes any `/tmp/` verification snippet — leave it in `/tmp/`, do not move it into the project tree.

---

## 11. What happens after Code's session

The next operator-Claude session reads the report and:

- Triages §5A's functional verification: did the orphan-venue sample harmonise as expected?
- Triages §5B's findings: is the warwick-farm class explained? If so, does §5C's match logic need refinement before merge execution?
- Triages §5C's proposed-merge plan: clean-merge proportion, ambiguous-match handling, no-match reasons. Decides whether to commission a follow-up brief that executes the merge, or whether to refine the match logic first.

Code does NOT produce the next brief. The merge-execution brief is the next operator-Claude session's authoring work, informed by what this session's report surfaces.

If §5C's clean-merge count is high (>80% of orphans) and ambiguity is low (<5%), a single follow-up brief commissions execution. If ambiguity is high, a refinement pass is needed first — possibly a §5B-style probe on the ambiguous class.

---

## 12. Cross-references

- **Scope doc:** `dr029/dr029_scope.md` §2.1 (race-data fit-for-purpose). §5A closes the venue-normalisation drift cause forward; §5C addresses the historical orphan rows; §5B characterises a residual class.
- **Governing DRs:** DR-029 (data-layer fit-for-purpose review before v3 build — the gating arc); DR-021 (timestamp anchoring, Adelaide local time).
- **Prior reports:** `surgical_fix_1_2_report.md` (the source of the root-cause analysis and orphan-row stats); `source_review_report.md` (the canonical anchor for race-key match logic and `upsert_race` semantics); `vps_drift_check.md` (the canonical anchor for dirty-tree state).
- **Prior briefs:** `surgical_fix_1_2_brief.md` and `surgical_fix_3_brief.md` (precedent for hard-limits language and dirty-tree discipline).
- **Parking-lot items excluded:**
  - Fix 4 (cadence design, blocked on Saturday probe).
  - BSP / sp_near / sp_far follow-up (Fix 3, separate Code session).
  - Consolidation of `bookmakers/sportsbet.py:_clean_venue` after lift (operator-Claude routes later).
  - Execution of the §5C merge plan (separate Code session).
  - Test coverage, migration framework, orchestrator restructure (named DR-029 debt).

*End of brief.*
