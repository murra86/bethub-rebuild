# DR-029 §2.1 — surgical Code session 8 brief (Fix 8: race-level merge execution)

**Brief locked:** 2026-05-01 19:14 ACST.
**Anchored against:** `dr029/2_1_race_data/surgical_fix_7_design_report.md` (locked Session 49 read; design probe complete).
**Input contract:** `dr029/2_1_race_data/fix_6c_proposed_merge.json` (3,249 records; the 784 `outcome=clean` subset is the merge target).
**System target:** VPS `root@187.77.183.9`, source tree `/home/racing/racing-data-capture/`, live `capture.db` at `/home/racing/racing-data-capture/data/capture.db`.

---

## §1. What this brief is and is not

**This is a surgical write-execution brief.** Single bounded Code session. Read-write on `capture.db`; read-only on the source tree. The brief commissions execution of the 784 race-level merges identified by Fix 6's dry-run, plus per-merge runner-row consolidation and dependent-table re-pointing per Fix 7's design report.

This brief does NOT perform: cadence design (Fix 4), Racing API re-fetch for the 2,081 already-merged race-rows (proposed Fix 9), low-confidence match review (proposed Fix 10), `has_subscription_sync` flag diagnostic (anomaly §6a — folded as side-effect only, not investigated as root-cause), or any other DR-029 §2.x scope item.

Surprises during execution become findings in the report, not blockers. If a single merge fails its UNIQUE-constraint pre-check or its transactional envelope rolls back, Code logs and continues with the remaining merges; the report's §6 anomalies surfaces what stalled. Multi-merge systemic failure is a different shape — Code halts, captures the failure mode, surfaces in the report. Operator-Claude triages in the next session.

---

## §2. Why this work exists

DR-029 §2.1 (race-side data fit-for-purpose verification) closed at Session 34 with known-debt-named. The surgical-fix arc (Fixes 1+2, 3, 5, 6, 7) has executed across Sessions 35-48. Fix 6 produced a 784-record merge plan (`fix_6c_proposed_merge.json`); Fix 7's design report (Session 49 read) confirmed:

- The existing `racing-metadata-backfill.service` has no merge function — race-row "merging" is purely an artefact of `upsert_race`'s `ON CONFLICT ... DO UPDATE SET col = COALESCE(excluded.col, col)` clause, which fires at sync time when natural keys collide. Pre-existing orphans (where keys didn't collide because of venue-normalisation drift) are not retroactively merged.
- The runner-level convergence finding (Fix 5 §7b) has a clean mechanistic explanation (Racing API returned empty `runners` arrays for the 2,081 already-merged race rows). For the 784 mergeable subset, runner-key alignment is 96.2% — clean merge profile.
- Survivor-row convention: LC-side (target) wins. Reasoning anchored in dependent-row volumes (~565k target-side vs ~83k orphan-side) and preservation of stable Betfair / bookmaker identifiers.
- No structural blockers identified.

This brief executes the merge. After Fix 8 lands: race-level `(1,1)` cross-tab cell grows from 2,081 to ~2,865; runner-level `with_both` cross-tab cell grows from 0 to ~1,957; orphan race-row count drops by 784. This unblocks Strategy 1 cycle analysis on the 784 affected races and widens the Harville calibration data by the equivalent runner volume.

---

## §3. Pre-reads

**Required, in order:**

1. `dr029/2_1_race_data/surgical_fix_7_design_report.md` — design anchor for every per-merge action sequence.
2. `dr029/2_1_race_data/surgical_fix_6_report.md` — merge-plan derivation, the 784-record composition (711 exact-key + 21 day-shift + 52 alias-resolved).
3. `dr029/2_1_race_data/fix_6c_proposed_merge.json` — the merge-plan input contract.
4. `dr029/2_1_race_data/vps_drift_check.md` — dirty-tree baseline.

**Reference-only — read on demand:**

- `dr029/2_1_race_data/source_review_report.md` — `upsert_race` ON CONFLICT semantics anchor.
- `dr029/2_1_race_data/surgical_fix_5_report.md` — Fix 5 §7b runner-level finding (now mechanistically explained).
- `dr029/2_1_race_data/surgical_fix_3_report.md` — metadata-backfill service rework context.

---

## §4. System access

- **VPS:** `ssh root@187.77.183.9`. Source tree at `/home/racing/racing-data-capture/`. Live database at `/home/racing/racing-data-capture/data/capture.db` (SQLite WAL mode).
- **Database access:** read-write on `capture.db` for the merge execution itself; read-only for all pre-flight and post-flight verification queries (use `file:...?mode=ro` URI for verification connections).
- **Source tree access:** read-only. The script being authored lives at `/root/fix_8_merge_execution.py` outside the source tree (NOT in `/home/racing/racing-data-capture/scripts/`); the source tree itself receives no edits in this brief.
- **Service access:** no service start / stop / restart. The `racing-metadata-backfill.service` and live-capture orchestrator continue running on their schedules. Execute the merge in a quiet window between live-capture cycles (post-jump quiet, pre-23:30 nightly backfill — Code's call on exact timing).
- **Adelaide local timestamps per DR-021** (timestamp anchoring, Adelaide local time) for every time-of-day reference in the report.

---

## §5. Pre-flight verification

Run before any write executes. All read-only.

### §5.1 Re-derive the merge plan against current DB state

The merge plan was generated 2026-05-01 17:25 ACST. Tonight's 23:30 ACST nightly metadata-backfill may have shifted the orphan set. Code's call on whether to execute pre- or post-23:30 backfill — but if executing after 23:30, **re-derive the merge plan freshly** and compare to the JSON.

Re-derivation procedure:
- Re-run the post-Fix-6 `normalise_venue` over every `races` row in the live-capture window.
- Group by `(race_date, harmonised_venue, race_number)`.
- Filter to clean RA-only ↔ LC-only pairs (matching Fix 6's `outcome=clean` criteria).
- Compare orphan_id / target_id pairs against `fix_6c_proposed_merge.json`.

Acceptable drift: new orphan races appearing in the plan (today's date may have produced fresh RA-side rows). Surface and add to the executed set if they meet `outcome=clean` criteria.

Unacceptable drift: orphan_id or target_id missing from the live DB (deleted), or the LC↔RA assignment swapping (target became RA-only). If unacceptable drift surfaces, halt execution, surface in the report, defer to operator-Claude.

### §5.2 Baseline cross-tabs

Capture the exact pre-state for the report. Read-only.

```sql
-- Race-level cross-tab on the live-capture window
SELECT
  CASE WHEN subscription_synced_at IS NOT NULL THEN 1 ELSE 0 END AS sub,
  CASE WHEN betfair_win_market_id IS NOT NULL THEN 1 ELSE 0 END AS bf,
  COUNT(*)
FROM races
WHERE race_date >= '2026-03-02'
GROUP BY sub, bf;

-- Runner-level cross-tab under merged race rows
SELECT
  CASE WHEN r.finish_position IS NOT NULL THEN 1 ELSE 0 END AS has_fin,
  CASE WHEN r.betfair_selection_id IS NOT NULL THEN 1 ELSE 0 END AS has_bf_sel,
  COUNT(*)
FROM runners r
INNER JOIN races ra ON r.race_id = ra.id
WHERE ra.race_date >= '2026-03-02'
  AND ra.subscription_synced_at IS NOT NULL
  AND ra.betfair_win_market_id IS NOT NULL
GROUP BY has_fin, has_bf_sel;

-- Orphan count
SELECT COUNT(*) FROM races
WHERE race_date >= '2026-03-02'
  AND subscription_synced_at IS NOT NULL
  AND betfair_win_market_id IS NULL;
```

Capture all three baselines into a `pre_state.json` artefact at `/root/fix_8_pre_state.json` (outside the source tree).

### §5.3 UNIQUE-constraint pre-check on the merge set

For each of the 784 merge candidates, verify:

1. Both `orphan_id` and `target_id` exist in `races` table.
2. Target's natural key `(race_date, venue_normalised, race_number)` is unique today.
3. Orphan's natural key differs from target's (otherwise they'd already be the same row).

If any candidate fails these checks, log to merge log and skip — do not execute that merge. Continue with remaining candidates.

### §5.4 Runner-key alignment spot-check

Sample 10 candidates from the 784 set. For each, count runner-key overlap between orphan and target. Per Fix 7 §D.2, expected overlap rate is 96.2%. If sample shows materially lower (<80%), surface as anomaly and proceed with caution — the per-runner merge branching may need different defaults.

### §5.5 Foreign-key integrity baseline

```sql
PRAGMA foreign_key_check;
```

Should return zero rows. If anything surfaces, halt and surface in report.

---

## §6. Substantive scope — per-merge execution

### §6.1 The script

Write a Python 3 script at `/root/fix_8_merge_execution.py` (NOT inside the source tree). The script:

- Reads `fix_6c_proposed_merge.json` (or freshly re-derived plan if §5.1 triggered re-derivation).
- Filters to `outcome=clean` records (the 784 set).
- For each merge candidate, executes the per-merge transactional sequence (§6.2 below).
- Logs progress to `/root/fix_8_merge.log` (one line per merge: timestamp, orphan_id, target_id, runner_merge_count, runner_repoint_count, bookmaker_snapshot_repoint_count, batch_summary_repoint_count, status).
- Supports `--dry-run` flag (executes the full sequence in a transaction that ROLLBACKs at the end — captures what would change without persisting).
- Supports `--resume` flag (skips merge candidates whose orphan_id no longer exists in `races` — relies on the orphan-row-existence idempotency check from Fix 7 §D.5).
- Enforces `PRAGMA foreign_keys = ON` on every connection.

Execute `--dry-run` first end-to-end, capture the output, verify the merge log shows expected per-merge counts, then execute the live run.

### §6.2 Per-merge transactional sequence

For each merge candidate `(orphan_id, target_id)` in the 784 set, execute inside a single `BEGIN ... COMMIT` block. Order: orphan_id ascending for deterministic resumability.

**Step (a) — Idempotency check.**

```sql
SELECT id FROM races WHERE id = :orphan;
```

If no row, COMMIT no-op, log as `idempotent_skip`, continue.

**Step (b) — Copy RA-side fields onto target row.**

```sql
UPDATE races SET
    subscription_synced_at = COALESCE((SELECT subscription_synced_at FROM races WHERE id = :orphan), subscription_synced_at),
    subscription_meet_id   = COALESCE((SELECT subscription_meet_id   FROM races WHERE id = :orphan), subscription_meet_id),
    going                  = COALESCE((SELECT going                  FROM races WHERE id = :orphan), going),
    track_condition_text   = COALESCE((SELECT track_condition_text   FROM races WHERE id = :orphan), track_condition_text),
    track_condition_number = COALESCE((SELECT track_condition_number FROM races WHERE id = :orphan), track_condition_number),
    distance_metres        = COALESCE((SELECT distance_metres        FROM races WHERE id = :orphan), distance_metres),
    distance_text          = COALESCE((SELECT distance_text          FROM races WHERE id = :orphan), distance_text),
    race_class             = COALESCE((SELECT race_class             FROM races WHERE id = :orphan), race_class),
    race_group             = COALESCE((SELECT race_group             FROM races WHERE id = :orphan), race_group),
    track_type             = COALESCE((SELECT track_type             FROM races WHERE id = :orphan), track_type),
    prize_total            = COALESCE((SELECT prize_total            FROM races WHERE id = :orphan), prize_total),
    winning_time_seconds   = COALESCE((SELECT winning_time_seconds   FROM races WHERE id = :orphan), winning_time_seconds),
    winning_time_text      = COALESCE((SELECT winning_time_text      FROM races WHERE id = :orphan), winning_time_text),
    is_trial               = COALESCE((SELECT is_trial               FROM races WHERE id = :orphan), is_trial),
    is_jump_out            = COALESCE((SELECT is_jump_out            FROM races WHERE id = :orphan), is_jump_out),
    has_subscription_sync  = 1,
    updated_at             = :now_iso
WHERE id = :target;
```

**Field list completeness:** Code authoritatively determines the full subscription-sourced field list by reading `subscription/racing_api.py:_sync_single_race` and `storage/database.py:upsert_race`. The list above is illustrative; the brief's authoritative requirement is **every field that the Racing API path populates and the live-capture path does not** gets carried via `COALESCE`. Schema-discovery first, then UPDATE construction.

Excluded fields (do not copy from orphan):
- `id`, `race_date`, `venue`, `venue_normalised`, `race_number` — natural-key + identity, target wins.
- `betfair_win_market_id`, `betfair_place_market_id`, `betfair_event_id` — Betfair identifiers, target wins.
- `match_method`, `match_confidence` — LC-side matching metadata, target wins.
- `created_at` — historical, target wins.
- All `bookmaker_*_id` columns — bookmaker-path identifiers, target wins.

The `has_subscription_sync = 1` write also closes anomaly §6a (the flag desync) for the merged subset as a side-effect.

**Step (c) — Per-runner merge or re-point.**

For each runner row where `race_id = :orphan`:

```sql
-- Try to find a target counterpart with same runner_key
SELECT id FROM runners WHERE race_id = :target AND runner_key = :orphan_runner_key;
```

**Branch (c.1) — target counterpart exists (merge):**

```sql
UPDATE runners SET
    finish_position           = COALESCE((SELECT finish_position           FROM runners WHERE id = :orphan_runner_id), finish_position),
    result_status             = COALESCE((SELECT result_status             FROM runners WHERE id = :orphan_runner_id), result_status),
    subscription_horse_id     = COALESCE((SELECT subscription_horse_id     FROM runners WHERE id = :orphan_runner_id), subscription_horse_id),
    jockey                    = COALESCE((SELECT jockey                    FROM runners WHERE id = :orphan_runner_id), jockey),
    trainer                   = COALESCE((SELECT trainer                   FROM runners WHERE id = :orphan_runner_id), trainer),
    weight_kg                 = COALESCE((SELECT weight_kg                 FROM runners WHERE id = :orphan_runner_id), weight_kg),
    age                       = COALESCE((SELECT age                       FROM runners WHERE id = :orphan_runner_id), age),
    sire                      = COALESCE((SELECT sire                      FROM runners WHERE id = :orphan_runner_id), sire),
    dam                       = COALESCE((SELECT dam                       FROM runners WHERE id = :orphan_runner_id), dam),
    stewards_comment          = COALESCE((SELECT stewards_comment          FROM runners WHERE id = :orphan_runner_id), stewards_comment),
    career_win_percent        = COALESCE((SELECT career_win_percent        FROM runners WHERE id = :orphan_runner_id), career_win_percent),
    career_place_percent      = COALESCE((SELECT career_place_percent      FROM runners WHERE id = :orphan_runner_id), career_place_percent),
    results_source            = CASE
                                  WHEN results_source = 'betfair_only'
                                       AND (SELECT finish_position FROM runners WHERE id = :orphan_runner_id) IS NOT NULL
                                  THEN 'betfair_and_subscription'
                                  ELSE results_source
                                END,
    updated_at                = :now_iso
WHERE id = :target_runner_id;

-- Re-point any dependent rows from orphan_runner_id to target_runner_id
UPDATE bookmaker_snapshots SET runner_id = :target_runner_id WHERE runner_id = :orphan_runner_id;
UPDATE betfair_snapshots SET runner_id = :target_runner_id WHERE runner_id = :orphan_runner_id;

-- Delete the orphan runner row
DELETE FROM runners WHERE id = :orphan_runner_id;
```

**Field-list discipline:** as per step (b), Code reads `subscription/racing_api.py:_sync_single_runner` and `storage/database.py:upsert_runner` to identify the authoritative full subscription-sourced runner-field list. All such fields get `COALESCE` carried.

**Branch (c.2) — no target counterpart (re-point):**

```sql
UPDATE runners SET race_id = :target, updated_at = :now_iso WHERE id = :orphan_runner_id;
```

UNIQUE constraint on `runners(race_id, runner_key)` is satisfied — Code's pre-check confirmed no target counterpart exists.

**Branch (c.3) — runner-level UNIQUE conflict on dependent re-point (merge branch):**

If the `UPDATE bookmaker_snapshots SET runner_id = :target_runner_id` step in branch (c.1) hits a UNIQUE constraint on `bookmaker_snapshots(race_id, runner_id, snapshot_time, bookmaker)` because the target already has a snapshot at that time for that bookmaker — log the conflict, skip the offending bookmaker_snapshots row's re-point (leave on orphan_runner, which then gets cascaded out via the DELETE), and continue. Surface aggregate count in the report's §6 anomalies.

**Step (d) — Re-point race-level dependent rows.**

```sql
UPDATE bookmaker_snapshots SET race_id = :target WHERE race_id = :orphan;
UPDATE snapshot_batch_summary SET race_id = :target WHERE race_id = :orphan;
-- betfair_snapshots: per Fix 7 §D.1, orphan side has 0 rows; sanity-check:
UPDATE betfair_snapshots SET race_id = :target WHERE race_id = :orphan;  -- expect 0 rows changed
-- betfair_historical: per Fix 7 §D.1, 0 rows in window; sanity-check:
UPDATE betfair_historical SET race_id = :target WHERE race_id = :orphan;  -- expect 0 rows changed
```

UNIQUE constraint risk on `bookmaker_snapshots(race_id, runner_id, snapshot_time, bookmaker)`: addressed by step (c.3) above — runner-id collisions are resolved before race-id re-point.

UNIQUE constraint risk on `snapshot_batch_summary(race_id, ...)`: depends on the table's actual UNIQUE constraint (Code reads schema). If conflict, log and skip the offending row, surface in §6 anomalies.

**Step (e) — Delete the orphan race row.**

```sql
DELETE FROM races WHERE id = :orphan;
```

If foreign-key check fails (some dependent row still points to orphan), the DELETE fails inside the transaction, the transaction ROLLBACKs, the merge logs as `failed_dependent_orphan`, and Code continues with the next merge.

**Step (f) — COMMIT.**

Per-merge transaction commits. Log entry written.

### §6.3 Three-row collision handling (anomaly §6c)

Per Fix 7 §6c, 52 of the 990 post-Fix-6 collision keys involve THREE rows. The merge plan's `outcome=clean` set may include some of these triples where the third row sits as a `(0,0)` cell (no sub_sync, no bf_market_id) — a pre-existing PENDING discovery row from another bookmaker path.

For each merge in the 784 set, before step (a), check:

```sql
SELECT id FROM races
WHERE race_date = :target_date
  AND venue_normalised = :target_venue_normalised
  AND race_number = :target_race_number
  AND id NOT IN (:orphan, :target);
```

If a third row exists, log to `/root/fix_8_three_row_log.json` with the third row's id, its `(sub, bf, has_subscription_sync)` flag state, dependent-row counts. **Do not auto-merge the third row.** Continue with the orphan↔target merge as planned.

The third-row log feeds operator-Claude triage in the next session — case-by-case decisions on whether to fold each into the survivor.

### §6.4 Logging discipline

Every merge writes one line to `/root/fix_8_merge.log`:

```
2026-05-XX HH:MM:SS ACST | orphan=NNNN | target=NNNN | runners_merged=N | runners_repointed=N | bk_snaps_repointed=N | batch_summaries_repointed=N | three_row_id=N_or_null | status=success|idempotent_skip|failed_unique|failed_dependent_orphan|failed_other
```

Aggregate counts written at end of execution to `/root/fix_8_aggregate_summary.json`.

---

## §7. Sequencing within session

1. **Pre-flight verification §5** — run all five sub-steps. Capture baselines. If §5.1 surfaces unacceptable drift, halt and surface in report; do not execute writes.
2. **Schema discovery for steps (b) and (c.1)** — read `subscription/racing_api.py` and `storage/database.py` to identify authoritative subscription-sourced field lists for `races` and `runners`. Capture in the report's §3 (or equivalent).
3. **Dry-run** — execute `/root/fix_8_merge_execution.py --dry-run` against the full 784 candidate set. Verify aggregate counts match Fix 7 §D.1 estimates within reasonable tolerance (±20%). If counts are wildly off, surface in report and halt.
4. **Live run** — execute `/root/fix_8_merge_execution.py` against the full 784 candidate set. Adelaide-quiet window (post-jump, pre-23:30). Code's call on exact timing.
5. **Post-flight verification §8** — re-run the §5.2 cross-tabs and capture the post-state. Compare pre vs. post; verify expected deltas. Run foreign-key integrity check.
6. **Report authoring** — see §8 below.

---

## §8. Empirical verification (post-flight)

Run all post-flight queries read-only.

### §8.1 Race-level cross-tab delta

Re-run the §5.2 race-level cross-tab. Verify:

- `(sub=1, bf=1)` cell: pre-state count + 784 ± natural variance (a small number of new orphans may have appeared during execution from other paths).
- `(sub=1, bf=0)` cell: pre-state count − 784 ± natural variance.
- Total race count: pre-state count − 784 (one orphan deleted per merge).

### §8.2 Runner-level cross-tab delta

Re-run the §5.2 runner-level cross-tab under merged race rows. Verify:

- `(has_fin=1, has_bf_sel=1)` cell: grows from 0 to ~1,957 ± natural variance.

If materially below ~1,500 or materially above ~2,500, surface as anomaly in §6 of the report.

### §8.3 Foreign-key integrity

```sql
PRAGMA foreign_key_check;
```

Should return zero rows. If anything surfaces, surface in report's §6 anomalies — these are post-Fix-8 broken references, the most serious failure mode.

### §8.4 Per-merge log audit

Aggregate `/root/fix_8_merge.log`:

- Total merges attempted: 784 (or freshly-derived count from §5.1).
- Successes: expected ~780+.
- Idempotent skips: expected 0 on first run.
- Failures: itemise by failure mode in report §6.

### §8.5 Three-row collision summary

Aggregate `/root/fix_8_three_row_log.json`. Surface count and per-row state distribution in report §7 (proposed Fix-9-or-similar follow-up).

### §8.6 Bookmaker_snapshots integrity

```sql
SELECT COUNT(*) FROM bookmaker_snapshots WHERE race_id NOT IN (SELECT id FROM races);
```

Should return 0. Any non-zero indicates a re-point that lost track of its target — surface in §6 anomalies.

### §8.7 Sample 5 merged races for visual confirmation

Pick 5 races from the merge set (one each from exact_key, day_shift, alias_resolved sub-categories — repeat as needed). For each, dump the post-merge state of the `races` row and 3 sample runner rows. Confirm:

- `subscription_synced_at` populated.
- `betfair_win_market_id` populated.
- `has_subscription_sync = 1`.
- Sample runners carry both `finish_position` AND `betfair_selection_id`.
- `results_source = 'betfair_and_subscription'` for runners that gained finish_position.

---

## §9. Output spec

Single report at `dr029/2_1_race_data/surgical_fix_8_report.md`. Length anticipation: 350-450 lines (matches Fix 6 / Fix 7 precedent).

**Required sections:**

1. **Headline** — what executed, what moved, top-line cross-tab deltas (race-level, runner-level), failure count, anomaly count.
2. **§A — Pre-flight verification outcomes** — §5.1 plan re-derivation result, §5.2 baseline cross-tabs, §5.3 UNIQUE pre-check result, §5.4 runner-key alignment spot-check, §5.5 FK integrity baseline.
3. **§B — Schema discovery** — authoritative subscription-sourced field lists for `races` and `runners` derived from source.
4. **§C — Dry-run outcomes** — aggregate counts, per-sub-category (exact_key / day_shift / alias_resolved), expected vs actual.
5. **§D — Live execution outcomes** — wall-clock, per-merge log summary, success / idempotent_skip / failure breakdown.
6. **§E — Post-flight verification deltas** — §8.1 race-level, §8.2 runner-level, §8.3 FK, §8.4 per-merge audit, §8.6 bookmaker_snapshots integrity, §8.7 sample races.
7. **§6 — Anomalies** — three-row collisions surfaced count, runner-level UNIQUE conflicts on dependent re-point count, FK violations (if any), unexpected aggregate volumes (if any), anything surprising the brief didn't anticipate.
8. **§7 — Self-assessment** — brief scope adherence, hard limits held, what moved, what did NOT move.
9. **§8 — Proposed follow-ups** — Fix 9 (Racing API re-fetch for 2,081 already-merged races' runners), three-row collision per-row triage, low-confidence match review, anomaly §6a (`has_subscription_sync` desync) root-cause diagnostic. **Recommendations only — no commissioning.**

**Report does NOT contain:**

- Recommendations on whether to commission proposed follow-ups (operator-Claude's call).
- Scope creep into other DR-029 §2.x items.
- Code edits to the source tree.
- Schema changes.

---

## §9. Hard limits — what is NOT in scope

Non-negotiable. Code does not do any of the following.

### §9.1 Single bounded session
One Code session. If the work doesn't fit, that's a finding, surface in the report. Partial-but-coherent execution beats complete-but-lost-coherence — if 600 of 784 merges land cleanly and the remaining 184 surface a systemic issue, halt, surface, defer to operator-Claude.

### §9.2 Source tree is read-only
No edits to anything under `/home/racing/racing-data-capture/`. No edits to `subscription/racing_api.py`, `storage/database.py`, `bookmakers/sportsbet.py`, `matching/race_matcher.py`, or any other source file. The merge script lives outside the source tree at `/root/fix_8_merge_execution.py`.

### §9.3 No service start/stop/restart
`racing-metadata-backfill.service` and the live-capture orchestrator continue running on their schedules. Code times the merge execution into a quiet window between cycles but does not modify service state.

### §9.4 No schema changes
No `ALTER TABLE`, no new tables, no new columns, no index changes. The merge operates within the existing schema.

### §9.5 No DR-029 named-debt remediation
No test coverage added. No migration framework introduced. No monolithic-orchestrator-file refactoring. Those are tracked in the DR-029 close-out governance paragraph and are not in scope.

### §9.6 No mid-session escalation
Code runs end-to-end. Surprises become findings in the report's §6 anomalies, not pings to operator-Claude. Multi-merge systemic failure (where the same failure mode hits 10+ merges in a row) is the exception — Code halts, captures the failure mode, surfaces in the report. Single-merge failures continue with logging.

### §9.7 No deletion of fix_5c_proposed_merge.json or fix_6c_proposed_merge.json
Both files preserved. They are governance artefacts and cross-references.

### §9.8 No execution of merges outside the 784 `outcome=clean` set
No execution against `outcome=no_match` records (2,465 records — venue/key mismatches Fix 6 couldn't resolve). No execution against the 1,910 trial/jump-out exclusions, 7 unstripped_naming residual, or 548 no_lc_counterpart records. These are out-of-scope for Fix 8.

### §9.9 No Racing API re-fetch
The 2,081 already-merged race rows whose runners are 100% Betfair-side (Fix 7 §B finding) are NOT re-fetched in this brief. That's proposed Fix 9, separate brief, separate Code session.

### §9.10 No `has_subscription_sync` flag root-cause diagnostic
The flag desync (anomaly §6a) is closed for the merged subset as a side-effect of step (b)'s explicit `has_subscription_sync = 1` write. The underlying bug — why `update_race_coverage` doesn't fire consistently on the ON CONFLICT path — is not investigated in this brief. Recommend as Fix 10 in §9 of the report.

### §9.11 No bookmaker_snapshots historical re-keying
Existing bookmaker_snapshots on the orphan side are re-pointed (race_id and runner_id updated to point at survivor). They are NOT re-keyed by `runner_key` or `runner_number` against the survivor's runner — only the foreign-key references move.

### §9.12 Dirty-tree state preserved
Pre-session `git status --short`: 11 modified, 7 untracked (per `vps_drift_check.md` Session 47-48 baseline). Post-session: identical. The merge script lives outside the source tree, so source-tree dirtiness is structurally protected. Verify via `git status --short` at session open and close.

### §9.13 No git operations on the source tree
No `git add`, `git commit`, `git stash`, `git restore`, `git checkout`, `git reset`. Read-only `git status --short` and `git diff` for verification only.

### §9.14 Single execution
The script is idempotent (orphan-row existence check) but is intended to be executed exactly once for the 784-merge run. Re-runs after the first successful run are no-ops (everything idempotent_skips). Do not re-run as a "let's see if anything moved" pattern — the next state-change is a new merge plan from a future Fix.

---

## §10. What happens after Code's session

Code's report lands at `dr029/2_1_race_data/surgical_fix_8_report.md`. The next operator-Claude session reads:

1. Headline (race-level + runner-level cross-tab deltas; failure count).
2. §D live execution outcomes.
3. §E post-flight verification — confirms expected deltas.
4. §6 anomalies — what stalled, what's unexpected.
5. §8 proposed follow-ups — recommendations on Fix 9 / 10 / three-row triage.

Triage shape: confirm expected deltas landed, confirm failures are bounded, decide which follow-ups to commission next. If everything clean, the §2.1 surgical-fix arc has only Fix 4 (cadence design, blocked on Saturday probe) remaining as gating work. Other follow-ups (Fix 9, Fix 10, low-confidence match review, three-row triage) are non-gating quality work.

If failure count is material (> ~30 failures or any FK violations), pivot to operator-decision before proceeding. The §8 cross-tab deltas not matching expectations is a different shape — needs root-cause diagnostic before further DR-029 closing work.

---

## §11. Cross-references

- **Scope doc anchor:** DR-029 §2.1 (race-side data fit-for-purpose verification).
- **Governing DRs:** DR-027 (the two-database architecture decision), DR-028 (the cross-database integration boundary discipline decision), DR-029 (the data-layer fit-for-purpose review before v3 build), DR-021 (timestamp anchoring, Adelaide local time).
- **Prior reports:** `surgical_fix_7_design_report.md` (design anchor), `surgical_fix_6_report.md` (merge-plan derivation), `surgical_fix_5_report.md` (Fix 5 §7b finding now mechanistically explained), `surgical_fix_3_report.md` (metadata-backfill service rework context), `source_review_report.md` (`upsert_race` ON CONFLICT semantics anchor).
- **Input contract:** `fix_6c_proposed_merge.json` (3,249 records; 784 `outcome=clean` subset is the merge target).
- **Parking-lot items excluded:** Fix 4 cadence design (waiting on Saturday probe), Fix 9 Racing API re-fetch (proposed in §8 of report), Fix 10 `has_subscription_sync` root-cause diagnostic (proposed in §8), three-row collision per-row triage (logged for operator-Claude review), low-confidence match review (`time_proximity_only` cases — proposed in §8).

---

*Brief locked. Hand off to Code.*
