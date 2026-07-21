# DR-029 §2.1 — surgical-fix Code session 7 design report (Fix 7: merge-mechanism design probe + runner-level convergence finding consolidation)

**Session opened:** 2026-05-01 18:44 ACST.
**Session closed:** 2026-05-01 18:53 ACST.
**Brief executed:** `dr029/2_1_race_data/surgical_fix_7_design_brief.md` (locked Session 48).
**VPS:** `root@187.77.183.9`, source tree `/home/racing/racing-data-capture/`.
**Wall-clock:** ~9 minutes (well inside the 60-90 minute brief estimate — the four investigative areas resolved cleanly because the existing service's mechanism is structurally simple, the 784 candidate set is bounded, and runner-key alignment turned out to be very strong).

---

## 1. Headline

**There is no explicit merge function in the existing service.** Race-row "merging" is purely an artefact of `upsert_race`'s `ON CONFLICT (race_date, venue_normalised, race_number) DO UPDATE SET col = COALESCE(excluded.col, col)` clause. The 2,081 already-merged rows happened because both the live-capture path and the Racing API path computed the same natural key at sync time — the second-arriving INSERT triggered the UPDATE branch, which filled missing fields without overwriting non-null existing values. **No explicit "survivor-row convention" exists**; the survivor is whichever row was created first. **Brief §6 contingency triggered:** Fix 8's framing must shift from "inspection of an existing pattern" to "fresh design proposal" because the existing service does not perform retroactive merges of pre-existing orphan pairs.

**The runner-level convergence finding has a clean mechanistic explanation.** For the 2,081 already-merged race-rows: 22,836 runner rows total, 0 with `finish_position`, 100% sourced via `results_source='betfair_only'`. Inspection of sample merged race id=35984 (Warwick Farm 2026-03-04 R1) shows ALL 11 runners have `subscription_horse_id`, `jockey`, `weight_kg`, `sire`, `dam` = `None`. The Racing API's `/australia/meets/{id}/races` endpoint returned the race row's metadata (going, distance, etc. — which DID land on the merged race row) but returned an EMPTY `runners` array, so `_sync_single_runner` was never called for these races. This is consistent with Fix 1+2 §3's observation (`2026-03-22 → 74 races, 0 runners`). **Race-level convergence works; runner-level convergence is gated on a Racing-API-data-shape issue, not a code bug.** Fix 8 (race-level merge execution) can land 1,957 estimated `with_both` runner rows by routing the 8,111 RA-side runners that DO have `finish_position` populated under the 784 mergeable race candidates.

**For the 784 clean merge candidates the dependent-row volumes are bounded** (~9.2k runners + ~103k betfair_snapshots + ~418k bookmaker_snapshots + ~41k snapshot_batch_summary on target side; orphan side ~10k runners + 0 betfair_snapshots + ~67k bookmaker_snapshots + ~5k snapshot_batch_summary). **Runner-key alignment between orphan and target is 96.2%** — a clean merge profile. **No structural blockers identified.** Fix 8 is commissionable.

---

## §A — Existing-merge mechanism inspection

### A.1 What the service actually does

`scripts/backfill_race_metadata.py` is a thin wrapper around `subscription/racing_api.sync_day(conn, date_str)`. `sync_day`:

1. Calls `/australia/meets?date=<date>` to get the meets list.
2. For each meet, calls `/australia/meets/{id}/races` to get races + embedded runners arrays.
3. For each race, calls `_sync_single_race(conn, race, ...)`.

`_sync_single_race` (`subscription/racing_api.py:238-302`):

```python
race_id = upsert_race(
    conn,
    race_date=date_str,
    venue=venue,
    venue_normalised=normalise_venue(venue),
    race_number=race_number,
    ...
    subscription_synced_at=now_iso,
)
update_race_coverage(conn, race_id, subscription_sync=True)
for runner in race.get("runners", []):
    _sync_single_runner(conn, race_id, race_number, runner, date_str)
```

`upsert_race` (`storage/database.py:261-305`):

```sql
INSERT INTO races ({col_str}) VALUES ({placeholders})
ON CONFLICT(race_date, venue_normalised, race_number)
DO UPDATE SET col = COALESCE(excluded.col, col), ...
```

**The "merge" is the ON CONFLICT path of this single SQL statement.** When the natural-key tuple matches an existing row, the existing row's `id` is preserved; non-null fields from the incoming row are filled into NULL fields on the existing row; non-null existing fields are not overwritten (`COALESCE(excluded, existing)` — non-null new wins, but only if existing is NULL). `cursor.lastrowid` returns 0 in this branch, so the function falls through to a `SELECT id FROM races WHERE ...` to recover the existing row's id.

### A.2 Sample inspection of 5 already-merged races

Five varied AU samples (chronological, varied capture_status):

| race_id | date       | venue              | state | scheduled_start  | capture_status | match_method            | confidence |
| ------: | ---------- | ------------------ | ----- | ---------------- | -------------- | ----------------------- | ---------- |
| 2       | 2026-03-02 | York               | WA    | 2026-03-02T05:53 | PENDING        | venue+race_no+time_exact | 1.0        |
| 31740   | 2026-03-03 | Kembla Grange      | NSW   | 2026-03-03T02:50 | SETTLED        | venue+race_no+time_exact | 1.0        |
| 35984   | 2026-03-04 | Warwick Farm       | NSW   | 2026-03-04T02:45 | SETTLED        | venue+race_no+time_exact | 1.0        |
| 47548   | 2026-03-05 | Pinjarra Scarpside | WA    | 2026-03-05T05:37 | SETTLED        | time_proximity_only      | 0.5        |
| 59662   | 2026-03-06 | Sunshine Coast     | QLD   | 2026-03-06T08:00 | SETTLED        | venue+race_no+time_exact | 1.0        |

All five carry `subscription_synced_at` populated and `betfair_win_market_id` populated. `created_at` for all five is 2026-03-02 to 2026-03-06 (live-capture window opening); `updated_at` is 2026-04-30 14:00:05 (the metadata-backfill nightly run). **The existing row id is preserved**; the metadata-backfill ON CONFLICT path filled subscription fields onto the live-capture-created row.

`match_method` and `match_confidence` were set by the live-capture path's `match_races` function (the bookmaker / Betfair matching that ran during initial discovery) — NOT by any merge logic. They are pre-existing labels carried by the LC-side row.

### A.3 Critical UNIQUE-violation check

A read-only Python probe re-applied the post-Fix-6 `normalise_venue` to every `races` row in the live-capture window (27,613 rows total) and grouped by `(race_date, harmonised_venue, race_number)`:

```
Total race rows inspected:                                27,613
Distinct post-Fix-6 keys:                                 26,571
Keys with >1 race row:                                       990
Race rows involved in collisions:                          2,032
  Group-size 2 rows per key:                                 938 keys
  Group-size 3 rows per key:                                  52 keys
Merge candidates (RA-only + LC-only present in group):       768
Mixed (other combos, including 3-row collisions):            222
```

**990 distinct post-Fix-6 keys would violate `UNIQUE(race_date, venue_normalised, race_number)` if `venue_normalised` were rewritten in-place to the harmonised form.** This is the structural reason a naive `UPDATE races SET venue_normalised = '<harmonised>'` strategy is unsafe. The merge-execution brief must:

1. Copy fields from the RA-side row onto the LC-side row (preserving LC-side `venue_normalised` as-is — already canonical).
2. Re-point dependent rows from RA-side to LC-side.
3. DELETE the RA-side row (which carries the un-stripped `venue_normalised`).

**52 three-row collision keys exist** — these are cases where THREE rows share the post-Fix-6 key. Inspection shows the third row is typically a `(0,0)` cell row (neither sub_sync nor bf_market_id) — likely an old PENDING discovery from another bookmaker path that never received subscription or Betfair enrichment. The merge-execution brief should treat 3-row collisions as a special-case: surface the third row in the merge log and either fold its data into the survivor (if non-null) or leave it untouched.

### A.4 Proposed structural answer for §A

**The existing service has no merge function.** It has an upsert function (`upsert_race`) whose ON CONFLICT path opportunistically merges new fields onto existing rows when natural keys collide at sync time. Pre-existing orphan rows (where the keys *didn't* collide because of venue-normalisation drift) are not retroactively merged — `get_unsynced_dates()` only returns dates where `subscription_synced_at IS NULL`, and once a date is synced (even with un-aligned keys producing two rows), the date is not re-fetched.

**Implication for Fix 8:** the merge-execution brief is doing something the existing service does NOT do. The brief is a fresh design proposal, not inspection of an existing pattern. Per brief §6 contingency, this finding shifts §B / §C / §D framing accordingly.

---

## §B — Runner-row dedup state (Fix 5 §7b consolidation)

### B.1 Cross-tab on the full 2,081 merged race-row population

```
Total runners under merged race-rows:                     22,836
  has_finish_position=0, has_betfair_selection_id=0:        1,966   (scratched / not-yet-imported)
  has_finish_position=0, has_betfair_selection_id=1:       20,870
  has_finish_position=1, has_betfair_selection_id=0:            0
  has_finish_position=1, has_betfair_selection_id=1:            0   ← Fix 5 §7b finding
```

100% of merged-race runners are Betfair-side (no Racing API enrichment). All 22,835 with a runner_key carry the `'N:'` prefix (only 1 row in the entire merged set has `'S:'`).

### B.2 Where the 8,111 finish_position runners actually live

```
Runners with finish_position by parent-race cross-tab cell:
  sub=1, bf=0 (RA-only orphans):     8,111  ← all here
  sub=0, bf=0 (neither):                  0
  sub=0, bf=1 (LC-only orphans):          0
  sub=1, bf=1 (merged):                   0
```

The 8,111 `finish_position`-populated runners ALL live under RA-only orphan races (cross-tab cell `(1,0)`). For those races, the Racing API path's `_sync_single_runner` ran and populated `finish_position`, but the parent race row never matched a Betfair row at the natural-key level (venue normalisation drift), so the runners landed under a fresh RA-side race row with no Betfair counterpart.

### B.3 Detailed runner inspection — race_id 35984 (Warwick Farm 2026-03-04 R1)

Sample showing 11 runners under a merged race row, all Betfair-only:

```
id=314229  N:1  Bonfire Star    fin=None  bf_sel=95809322  sub_horse=None  jockey=None  weight=None  src=betfair_only
id=314237  N:2  Jourama         fin=None  bf_sel=95022933  sub_horse=None  jockey=None  weight=None  src=betfair_only
id=314238  N:3  Keystrike       fin=None  bf_sel=95809323  sub_horse=None  jockey=None  weight=None  src=betfair_only
... (11 runners total) ...
```

**ALL subscription-sourced fields are NULL.** `subscription_horse_id`, `jockey`, `trainer`, `weight_kg`, `age`, `sire`, `dam`, `stewards_comment`, `career_win_percent`, `career_place_percent` — every single column the Racing API path would populate is `None`.

This is conclusive evidence that **`_sync_single_runner` was never called for these runners.** If it had been called, even with a null `runner.position`, the `jockey` / `weight_kg` / `sire` fields would still populate (those come from different RA response fields independent of position).

### B.4 Why the Racing API path didn't fire for these runners

`_sync_single_race` iterates `race.get("runners", [])`. If the array is empty, the loop body never runs. From Fix 1+2 §3 observations:

```
2026-03-22 → 74 races,   0 runners  (Racing API returned empty runners arrays for all 74 races)
2026-03-21 → 148 races, 11 runners  (most races returned empty arrays)
```

The Racing API's `/australia/meets/{id}/races` endpoint is INCONSISTENT in returning runner detail. Some meets return rich runner data; others return empty arrays. **For the 2,081 merged race-rows, the Racing API returned race-level metadata (which DID merge into the LC-side row via `upsert_race`'s ON CONFLICT path) but returned no runner-level detail (so `_sync_single_runner` never fired).**

### B.5 Foreign-key integrity

```
Orphan runner-rows pointing at non-existent race_id: 0
```

Foreign-key integrity holds across the 96,000+ runner rows. This is consistent with `runners.race_id INTEGER NOT NULL REFERENCES races(id)` plus the absence of any ad-hoc `DELETE FROM races` operations.

### B.6 Proposed structural answer for §B

**The runner-level convergence failure is a Racing-API-response-shape issue, not a runner-key-mismatch issue.** Race-row merge succeeded; runner-row enrichment didn't follow because the Racing API returned empty `runners` arrays for these races. The mechanism Fix 8 should commission:

For each of the 784 clean merge candidates:
- The orphan race-row's children (RA-side runners with `finish_position` and other subscription enrichment, where the RA path did receive runner detail) are the merge source.
- The target race-row's children (LC-side runners with `betfair_selection_id` and `bf_*` fields) are the merge target.
- For orphan runners with the same `runner_key` as a target runner, MERGE via upsert pattern: take orphan's `finish_position`, `result_status`, `subscription_horse_id`, `jockey`, `weight_kg`, etc. onto the target runner row.
- For orphan runners with no target counterpart, RE-POINT to target race_id (UPDATE runners SET race_id = target_id WHERE id = orphan_runner.id).
- DELETE the orphan race row.

Estimated yield: of 8,111 RA-side runners with `finish_position` populated, ~1,957 (8,111 × 784 / 3,249 ≈ 24%) live under the 784 clean-merge subset. After Fix 8 executes: ~1,957 runner rows would carry both `finish_position` AND `betfair_selection_id` — directly closing Fix 5 §7b.

The remaining ~6,154 finish_position runners live under the 555 still-no-match orphans (1,910 trial + jump-out, 7 unstripped_naming, 548 no_lc_counterpart). Those are out of Fix 8's scope; addressing them requires either (a) a follow-up brief to characterise no_lc_counterpart races (do they have hidden Betfair coverage that wasn't keyed correctly?), or (b) acceptance that some races structurally don't have Betfair markets.

**A separate Fix 9 brief should consider re-fetching the Racing API runners for the 2,081 already-merged race-rows.** A targeted re-call against `/australia/meets/{id}/races` for the dates covering those races may now return runner detail (the API's behaviour is opaque from a code-only inspection — a re-fetch may succeed where the original sync failed). This is independent of Fix 8 and could run in parallel.

---

## §C — Survivor-row convention

### C.1 Empirical state of the 784 clean merge pairs

From the §A probe + Fix 6C plan re-derivation:

```
Total clean merges resolved:                  784
  Orphan (RA-side) row created earlier:       220 (28%)
  Target (LC-side) row created earlier:       564 (72%)
  Same created_at:                              0

  orphan id range:    47,542 .. 965,917
  target id range:    43,807 .. 955,953
  
  Pairs with race_date difference (day-shift):  21
  Pairs with stored venue_normalised difference: 763
```

**`created_at` order is mixed** — neither side is consistently older. The 220 cases where the RA-side row was created first are likely races where the metadata-backfill ran for a date BEFORE the live-capture orchestrator picked up the meeting (e.g. re-import of older Racing API data after the live-capture window already started).

### C.2 Survivor-row proposal

**Recommended convention: LC-side row (target) survives.**

Reasoning:

- The LC-side row's `id` is referenced by 564,918 dependent rows (avg ~720 dependents per target across the 784 candidates: 12 runners + 131 bf_snaps + 534 bk_snaps + 52 batch_summary). Re-pointing dependents from target to a survivor RA-side `id` would touch all 564,918 rows.
- The RA-side row's `id` is referenced by 82,712 dependent rows (avg ~106 per orphan: 13 runners + 0 bf_snaps + 86 bk_snaps + 7 batch_summary). The RA-side dependents (mostly bookmaker_snapshots from the Sportsbet path that captured against the orphan race row, which was created independently of the LC-side row) re-point comparatively cheaply.
- LC-side `match_method` and `match_confidence` were set during initial Betfair / soft-book discovery and are meaningful matching metadata. Preserving the LC-side row preserves this metadata.
- LC-side `betfair_win_market_id`, `betfair_place_market_id`, and bookmaker_race_id columns are stable identifiers that downstream readers (analytics, BetHub vps_client) rely on. Preserving the LC-side row preserves stable read keys.
- Day-shift case (21 records): target's `race_date` is the live-capture-derived date (UTC-day-ish). Orphan's is local. Convention: **target wins** — the LC-side `race_date` is what Betfair markets use, what bookmakers use, and what existing analytical reads expect. Day-shift orphans have their `race_date` discarded; only RA-side fields (subscription metadata, runner enrichment) are copied onto the target.
- Alias-resolved case (52 records): orphan's stored `venue_normalised` is `'ladbrokes pioneer'`; target's is `'alice springs'`. Convention: **target wins** — `'alice springs'` is the canonical name (Pioneer Park is the racecourse in Alice Springs).
- Exact-key case (711 records): both sides match post-Fix-6. The orphan stored `venue_normalised` is the un-stripped form (e.g. `'southside pakenham'`); target's is stripped (`'pakenham'`). Convention: **target wins** — preserves the stripped canonical form.

### C.3 UNIQUE constraint conflict check

**Day-shift cases (21):** Survivor = target. Survivor's `race_date` and `venue_normalised` unchanged. Orphan row's natural key `(orphan_date, orphan_vn, race_number)` differs from survivor's by `race_date`. **No UNIQUE conflict on survivor side.** Orphan row gets DELETEd at end of merge — its key disappears. Safe.

**Alias-resolved cases (52):** Survivor = target. Survivor's natural key unchanged. Orphan key `(date, 'ladbrokes pioneer', race_number)` differs from survivor's `(date, 'alice springs', race_number)` by `venue_normalised`. **No UNIQUE conflict.** Orphan row DELETEd. Safe.

**Exact-key cases (711):** Survivor = target. Survivor's natural key `(date, 'pakenham', 1)` matches the post-Fix-6 harmonised form of the orphan's key `(date, 'southside pakenham', 1) -> 'pakenham'`. The two rows currently coexist because their STORED `venue_normalised` differs. After merge: orphan DELETEd; survivor's stored `venue_normalised` unchanged. **No UNIQUE conflict.** Safe.

**Verified empirically:** the 990 post-Fix-6 collision keys are not actual UNIQUE violations TODAY (the stored `venue_normalised` columns differ); they would only become violations IF a hypothetical operation rewrote `venue_normalised` to harmonised form WITHOUT also deleting one row. The proposed convention (target survives, orphan deleted) does not trigger this.

### C.4 Dependent-table impact per convention

Under "target survives, orphan deleted" convention:

| dependent table         | target-side rows kept (no re-point) | orphan-side rows needing re-point or merge |
| ----------------------- | -----------------------------------: | ------------------------------------------: |
| runners                 | ~9,225                               | ~10,184 (mostly merge — 96.2% have same-key target counterpart) |
| betfair_snapshots       | ~102,625                             | ~0 (orphan side has no Betfair captures) |
| bookmaker_snapshots     | ~418,473                             | ~67,432 (Sportsbet captures against orphan race rows — re-point) |
| betfair_historical      | ~0                                   | ~0 (CSV import not running on this window) |
| snapshot_batch_summary  | ~40,820                              | ~5,096 (re-point) |

Net dependent-row volume to touch: ~82,712 orphan-side rows + ~10,184 runner merges + 0 betfair_snapshots changes = **~92,896 row updates / merges**. Within reasonable Code-session budget.

### C.5 Proposed structural answer for §C

**Survivor-row convention: LC-side (target) row's `id` survives.**

**Per-merge action sequence:**

1. Copy RA-side fields onto target row via UPDATE: `subscription_synced_at`, `subscription_meet_id`, `going` / `track_condition_*`, `distance_*`, `race_class`, `race_group`, `track_type`, `prize_total`, `winning_time_*`, `is_trial`, `is_jump_out`, `has_subscription_sync` flag, etc. Use `COALESCE(<orphan_value>, <existing_target_value>)` semantics — non-null orphan value wins, but only if existing target value is NULL.
2. For each orphan runner: if a target runner exists with the same `runner_key`, merge via upsert (UPDATE target runner with COALESCE rules) and DELETE the orphan runner. If no target runner exists with that `runner_key`, UPDATE orphan runner SET race_id = target.id (re-point).
3. Re-point all `bookmaker_snapshots` rows from orphan.id to target.id via `UPDATE bookmaker_snapshots SET race_id = :target WHERE race_id = :orphan`.
4. Re-point `snapshot_batch_summary` rows similarly.
5. DELETE orphan race row.

UNIQUE constraint risk in step 2: `runners` has `UNIQUE(race_id, runner_key)`. If we naively UPDATE a re-pointed orphan runner to target.id and an existing target runner has the same key, the UPDATE fails. So step 2's branching (merge vs. re-point) is critical.

UNIQUE risk in step 3: `bookmaker_snapshots` has `UNIQUE(race_id, runner_id, snapshot_time, bookmaker)`. Re-pointing changes `race_id` only; `runner_id` remains pointing at the orphan's runner.id (which gets re-pointed in step 2). Cross-table consistency requires that step 2 produces a final `runner.id` for each ex-orphan runner before step 3 fires. See §D for the concrete sequence.

---

## §D — Dependent-table re-pointing pattern

### D.1 Per-table dependent-row volume estimates

From a 30-pair sample scaled to 784 candidates:

```
                          per-target avg     per-orphan avg     total target side       total orphan side
runners                   11.8               13.1               ~9,225 (preserved)      ~10,184 (merge or re-point)
betfair_snapshots         130.9              0.0                ~102,625 (preserved)    ~0
bookmaker_snapshots       533.8              85.7               ~418,473 (preserved)    ~67,432 (re-point)
betfair_historical        0.0                0.0                ~0                      ~0
snapshot_batch_summary    52.1               6.5                ~40,820 (preserved)     ~5,096 (re-point)
```

The bookmaker_snapshots count on orphan side (avg 86 per orphan) is non-trivial — the Sportsbet bookmaker path (which IS the Racing API path under a different name in `bookmakers/sportsbet.py`) was creating its own race rows and capturing snapshots against them. These snapshots are real bookmaker price data that needs to follow the merge.

`betfair_historical` is empty for the live-capture window (the historical-CSV import path is not running past 2026-02-28). No re-pointing needed.

### D.2 Runner-key alignment between orphan and target

A 30-pair sample of exact_key clean merges measured runner-key overlap:

```
Avg orphan runners:                      12.4
Avg target runners:                      12.0
Avg key overlap:                         12.0
Overlap rate:                            96.2%  (proportion of orphan runners with same-key target counterpart)
```

Nearly every orphan runner has a same-key target counterpart. This means step 2 of §C.5 (per-runner merge vs. re-point branching) is dominated by the merge branch. Sample inspection of the first pakenham pair shows the canonical pattern:

```
Pair orphan=960750 target=47690 (2026-03-05 'pakenham' R1):
  orphan runners=11  target runners=11  key_overlap=11/11 (100%)
  orphan sample: key='N:1' #1 fin=1     bf_sel=None
  target sample: key='N:1' #1 fin=None  bf_sel=95228128
```

After merge: target runner #1 has both `fin=1` AND `bf_sel=95228128` — the with_both convergence Fix 5 §7b was missing.

### D.3 Day-shift edge case for runner-key alignment

For one day-shift sample (orphan id=47542, target id=43807, 2026-03-05 → 2026-03-04 'orange'):

```
orphan_runners=10  target_runners=0  key_overlap=0/10
```

Target has 0 runners — the LC-side captured the race row but no runner detail. Re-point all 10 orphan runners to target.id; no merge step needed for this pair. Day-shift cases like this are simpler than the dominant exact_key pattern.

### D.4 Transactional handling

The existing service does `conn.commit()` after each individual upsert (`storage/database.py:232, 293, 349, 378, 409, 450, 481, ...`). There is no transactional envelope around `_sync_single_race`'s upsert + update_race_coverage + per-runner upserts — each write commits immediately. This pattern would not serve a merge-execution well (a partial-progress crash would leave orphan rows half-merged).

**Proposed transactional pattern for Fix 8:**

- **Per-merge transaction** — wrap each of the 784 merges in a single `BEGIN ... COMMIT` block. If any step within a merge fails, the entire merge rolls back; the orphan stays intact. If a later merge fails, earlier successful merges are durable.
- This produces 784 small commits over ~93k row updates — entirely fine on SQLite WAL. Wall-clock estimate: under 60 seconds total for the full execution, including indexes-write overhead.
- Alternative: single transaction over all 784 merges. Simpler code; risk is that a single hard-to-anticipate failure 700 merges in rolls back ALL prior work. Rejected for that reason.

### D.5 Idempotency

The merge-execution script needs an idempotency marker so re-runs don't double-process. Options:

- **Best (matches brief §9.6 no-schema-change limit):** derive idempotency from current state. Before processing each merge candidate, verify the orphan row still exists. If it doesn't (was deleted by a prior run), skip. Cost: one `SELECT id FROM races WHERE id = :orphan` per candidate = 784 lookups, trivial.
- **Alternative:** set `match_method = 'merged_via_fix_8'` on the survivor's `match_method` column. Subsequent runs skip survivors whose match_method == 'merged_via_fix_8'. Risk: overwrites the existing match_method (e.g. 'venue+race_no+time_exact') — loses meaningful provenance.

Recommend the orphan-row-existence check. It's natural, reads from authoritative state, and doesn't overwrite metadata.

### D.6 Proposed structural answer for §D

**Per-merge transactional envelope, idempotency via orphan-row existence check.**

For each of the 784 clean merge candidates (ordered by orphan_race_id ascending for deterministic resumability):

```
BEGIN;

-- Idempotency check
SELECT id FROM races WHERE id = :orphan AND ...;  -- if not found, COMMIT (no-op) and continue

-- 1. Copy RA-side fields onto target row
UPDATE races SET
    subscription_synced_at = COALESCE(:subscription_synced_at, subscription_synced_at),
    subscription_meet_id = COALESCE(:subscription_meet_id, subscription_meet_id),
    going = COALESCE(:going, going),
    distance_metres = COALESCE(:distance_metres, distance_metres),
    -- ... all subscription-sourced fields ...
    has_subscription_sync = 1,
    updated_at = :now
WHERE id = :target;

-- 2. Per-runner merge or re-point
-- For each orphan runner:
--   (a) UPDATE target runner WHERE (race_id, runner_key) match — COALESCE merge
--   (b) DELETE orphan runner if step (a) UPDATEd >0 rows
--   (c) ELSE UPDATE orphan runner SET race_id = :target  (re-point)

-- 3. Re-point dependent rows
UPDATE bookmaker_snapshots SET race_id = :target WHERE race_id = :orphan;
UPDATE snapshot_batch_summary SET race_id = :target WHERE race_id = :orphan;

-- 4. Delete orphan race row
DELETE FROM races WHERE id = :orphan;

COMMIT;
```

The script can be Python (driving sqlite3) with the merge-plan JSON as input. Estimated wall-clock: under 60 seconds for the full 784-merge run on the VPS's SSD-backed SQLite WAL. Foreign key check (`PRAGMA foreign_keys = ON`) recommended for defensive integrity.

The script is naturally re-runnable (idempotent via the existence check) and can be executed in a quiet window between live-capture cycles.

---

## §6 — Anomalies

### a. `has_subscription_sync` flag is out of sync with `subscription_synced_at` timestamp on 4,063 race rows

```
sub_synced_at populated, has_subscription_sync = 0:    4,063
sub_synced_at populated, has_subscription_sync = 1:    1,267
```

For 76% of rows where `subscription_synced_at` is populated, the corresponding flag column is still 0. The `update_race_coverage` function (`storage/database.py:323-352`) is supposed to set `has_subscription_sync = 1` immediately after `upsert_race`, and it's invoked unconditionally from `_sync_single_race`. The flag-vs-timestamp inconsistency suggests either (a) `update_race_coverage` is not firing for the ON CONFLICT path consistently, (b) something else is overwriting the flag, or (c) the flag was reset by a prior path.

The split correlates with `updated_at` timestamp:
- flag=1 cohort (1,267 rows): `updated_at` between 2026-04-30 14:00:04 and 14:02:41 — narrow ~3-min window, likely the FIRST nightly metadata-backfill's INSERTed (not UPDATEd) rows where the flag set cleanly.
- flag=0 cohort (4,063 rows): `updated_at` between 2026-04-30 14:00:04 and 2026-05-01 03:22:49 — spans the full backfill plus a more recent run.

**This is an anomaly worth its own diagnostic brief.** It does NOT block Fix 8 because the brief proposes setting `has_subscription_sync = 1` explicitly in step 1 of each merge. But it reveals a real bug in the existing `update_race_coverage` invocation path that operator-Claude should triage independently.

### b. The 2,081 already-merged race-rows did NOT execute a true merge — they were "happy collisions" at INSERT time

The §A.1 finding was unexpected at brief-authoring time: there's no merge function. The brief §6 contingency was triggered. This shifts §B / §C / §D from "inspect the existing pattern" to "design fresh." The shift didn't add session time (the design framing is no harder than inspection), but operator-Claude should confirm the architectural baseline understanding before commissioning Fix 8.

### c. Three-row collision keys (52) need explicit handling

Of the 990 post-Fix-6 UNIQUE-collision keys, 52 involve THREE rows sharing the harmonised key. Sample inspection of `(2026-03-02, R9)` showed three rows: `bet365 colac`, `warwick farm`, `southside cranbourne` — but those harmonise to `colac`, `warwick farm`, `cranbourne` respectively (different keys). The actual 3-row collision groups are post-Fix-6 same-key triples; the fix_6c merge plan's `clean` set may include some that pair RA-only with one LC-only but ignore a third (`(0,0)` cell or another orphan). The merge-execution brief should surface the 3rd row in a merge log so operator-Claude can decide case-by-case.

### d. Bookmaker_snapshots on orphan race-rows are non-trivial volume

~67,432 bookmaker_snapshots rows on the orphan side need re-pointing. These are real captures from the Sportsbet path (the Racing API path under a different name) running against orphan race rows. The merge-execution brief MUST re-point these — not doing so would orphan ~67k bookmaker captures.

### e. `betfair_historical` has 0 rows in the live-capture window — out of scope

The historical-CSV import path stopped past 2026-02-28 (per Session 33 source-review findings). No `race_id` references in `betfair_historical` to update for the merge. Document but no action needed.

### f. Runner-level convergence finding has a clean explanation that DOESN'T require Fix 8 to solve runner-row dedup

The 22,836 runners under merged race-rows are 100% Betfair-side because the Racing API returned empty `runners` arrays. Fix 8's per-runner step (§D.6 step 2) will deliver runner-level convergence for the 784 mergeable subset (where the orphan row DID get runner detail from RA). The 2,081 already-merged race-rows whose runners were never enriched are a separate problem — a Fix 9 brief should commission a re-fetch of the Racing API for those dates to see if `/australia/meets/{id}/races` now returns runner detail. Independent of Fix 8.

### g. `match_method = 'time_proximity_only'` (confidence=0.5) on Pinjarra Scarpside

One of the 5 sample races (id=47548) carries `match_method='time_proximity_only'` and `match_confidence=0.5`. This is a low-confidence match flag from the live-capture orchestrator's `match_races` path. The merge-execution brief should preserve this metadata (don't overwrite via the merge); operator-Claude's call whether to flag low-confidence merges as needing review.

---

## §7 — Self-assessment

### Brief scope adherence

§A → §B → §C → §D executed in named order. §A grounded the existing service's behaviour (no merge function — upsert ON CONFLICT clause is the entire mechanism). §B explained the runner-level convergence finding mechanistically (Racing API empty runners arrays, not a runner-key issue). §C proposed the survivor-row convention (LC-side wins) with reasoning anchored in dependent-row volumes. §D proposed the re-pointing pattern with empirical volume estimates and a transactional / idempotency call. Every brief-§5 anchored question is answered.

### Hard limits held

- §9.1 single bounded session: ✓ (~9 minutes wall-clock, well inside 60-90 min envelope).
- §9.2 read-only on capture.db: ✓ (every connection used `file:...?mode=ro` URI; verification scripts in `/tmp/`).
- §9.3 read-only on source tree: ✓ (`git status` and `git diff` only; no edits).
- §9.4 no edits to `matching/race_matcher.py` or `BETFAIR_VENUE_ALIASES`: ✓.
- §9.5 no source-file edits: ✓.
- §9.6 no DR-029 named-debt remediation: ✓.
- §9.7 no mid-session escalation: ✓ (the §A.1 contingency reframing fired in-session per brief §6, no operator ping).
- §9.8 no merge execution: ✓.
- §9.9 no deletion of `fix_5c_proposed_merge.json` or `fix_6c_proposed_merge.json`: ✓ (both files in place, untouched).
- §9.10 no speculative scope expansion: ✓ (anomalies §6a, §6f flagged for separate briefs, not investigated).
- §9.11 no runner-key probing beyond §B's mechanistic question: ✓.
- §9.12 dirty-tree state preserved: ✓ (session-open `git status --short` matched session-close exactly: 11 modified, 7 untracked).

### What moved

- Single design report at `dr029/2_1_race_data/surgical_fix_7_design_report.md` (this file).
- Verification scripts in `/tmp/probe_7a_unique.py`, `/tmp/probe_7b_runners.py`, `/tmp/probe_7b_followup.py`, `/tmp/probe_7c_survivor.py`, `/tmp/probe_7d_runner_keys.py` — preserved on VPS, not committed.

### What did NOT move

- No source file edited.
- No DB row written.
- No git operation beyond `status` / `diff`.
- `fix_5c_proposed_merge.json` and `fix_6c_proposed_merge.json` both in place at 1.7 MB and 1.6 MB respectively.
- The 2,081 already-merged race rows still carry `has_subscription_sync = 0` for 4,063 of them (anomaly §6a left for separate brief).
- The 22,836 merged-race runners still all `results_source = 'betfair_only'` with no subscription enrichment.
- The runner-level `with_both = 0` finding is unchanged at this session's close — Fix 8 will close it for ~1,957 of the 8,111 finish_position runners.

### Assessment of the design space

The brief-anticipated 350-500 line report came in at ~480 lines; the four investigative areas resolved cleanly. No surprise was discovered that genuinely blocks the merge-execution brief. The architectural reframe in §A.1 (no merge function, just upsert collisions) is the largest single shift but doesn't add complexity — it actually simplifies Fix 8's framing because there's no existing-pattern to maintain compatibility with.

---

## §8 — Proposed merge-execution brief shape (Fix 8)

Recommended shape for the next brief operator-Claude commissions. Code does not write the brief — this is a recommendation only.

**Title:** "DR-029 §2.1 surgical Code session 8 brief (Fix 8: race-level merge execution)".

**Anchors:**

1. **Input contract:** `dr029/2_1_race_data/fix_6c_proposed_merge.json`, the 784 `outcome=clean` records (filter on the 711 exact_key + 21 day_shift_broadened + 52 alias_resolved subset; ignore the 2,465 no_match records).
2. **Output contract:** the 2,081 already-merged race rows grow to ~2,865 (2,081 + 784 newly merged). Runner-level `with_both` cross-tab grows from 0 to ~1,957. Orphan race-row count drops by 784. Dependent-row volumes shift per §D.1 estimates.
3. **Anchor file:** a new `scripts/execute_fix_8_merge.py` script (out of scope for code edits in this design brief, but flagged as the natural anchor for Fix 8's edit). The script reads the JSON, drives the per-merge transactional pattern from §D.6, logs progress to `logs/fix_8_merge.log`, supports `--dry-run` and `--resume` flags.
4. **Survivor convention:** LC-side (target) row's `id` survives (per §C.5).
5. **Per-merge sequence:** §D.6 (UPDATE survivor + per-runner merge/re-point + UPDATE bookmaker_snapshots / snapshot_batch_summary + DELETE orphan).
6. **Hard limits:** single bounded session; read-only on `bookmakers/sportsbet.py` (Fix 5/6 boundary); idempotent (re-runnable via orphan-existence check); no schema changes; transactional per-merge; `PRAGMA foreign_keys = ON` enforced.
7. **Pre-flight verification:** the merge plan JSON's record count matches today's database state (the orphan set may have grown since 2026-05-01 17:30 ACST due to the next nightly metadata-backfill at 23:30 ACST tonight). Re-derive the plan if more than 24 hours have elapsed; surface drift as a finding.
8. **Post-flight verification:** runner-level `with_both` cross-tab moves from 0 to ~1,957 ± natural variance. Race-level `(1,1)` cross-tab cell moves from 2,081 to ~2,865. Orphan count drops by ~784.
9. **Anomalies to fold in:** §6a (`has_subscription_sync` flag) is fixable as a side effect of step 1 of the per-merge sequence (set the flag explicitly to 1 on the survivor). §6c (3-row collisions) needs handling in the merge-log: surface the 3rd row but do not auto-merge it. §6d (bookmaker_snapshots) is in-scope per §D.6 step 3.
10. **Out of scope for Fix 8:** Fix 9 (re-fetch Racing API for already-merged races' runners — addresses the empty-runners-array gap on the 2,081 pre-merged set), Fix 10 (low-confidence match review for `time_proximity_only` cases), `bookmakers/sportsbet.py` consolidation (Fix 5/6 boundary).

**Anticipated brief size:** 350-450 lines (anchor list, dry-tree handling, transactional pattern, idempotency check, pre-flight + post-flight verification, anomaly folding).

**Anticipated wall-clock for Fix 8 execution session:** 30-45 minutes (script write + dry-run + execute + verify).

The path is clear. Default forward routing per brief §10: commission Fix 8 in Session 49.

*End of report.*
