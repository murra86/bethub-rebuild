# `capture.db` schema reference (W1 introspection)

**Captured:** 2026-05-05 15:08 ACST.
**Source:** `root@187.77.183.9:/home/racing/racing-data-capture/data/capture.db` (2.05 GB).
**Method:** SSH + `python3` `PRAGMA table_info` per standing instructions Cat 3 (live database queries via start_process Python; never copy the file).

This document is governance reference — the bridge between `vps_client_contract.md`'s semantic field names and `capture.db`'s actual column names. The v3 SQL queries inside `clients/vps_client/v1/` are grounded against the schema captured here.

---

## §1 — Tables present

| Table | Row count | Used by surfaces |
|---|---|---|
| `races` | 60,264 | §9.1 race metadata, §9.4 bracketing (join), §9.5 BSP, §9.6 identity |
| `runners` | 435,251 | §9.2 runner metadata, §9.3 results, §9.5 BSP, §9.6 identity |
| `betfair_snapshots` | 1,740,185 | §9.4 bracketing, §9.5 BSP/sp_near/sp_far |
| `bookmaker_snapshots` | 2,964,813 | (not used by v1.0 surfaces) |
| `betfair_historical` | 163,809 | §9.5 BSP fallback (settled historical BSPs) |
| `snapshot_batch_summary` | 439,881 | (not used) |
| `daily_calibration_summary` | 64 | (not used) |

## §2 — `races` columns (relevant subset)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | capture.db internal race PK |
| `race_date` | TEXT | ISO date |
| `venue` | TEXT | maps to contract `RaceMetadata.venue` |
| `race_number` | INTEGER | maps to contract `RaceMetadata.race_number` |
| `distance_metres` | INTEGER | maps to contract `RaceMetadata.distance_metres` |
| `race_class` | TEXT | maps to contract `RaceMetadata.classification` (e.g. "Maiden Handicap", "BM58") |
| `track_condition` | TEXT | maps to contract `RaceMetadata.track_condition` |
| `meeting_type` | TEXT | METRO / COUNTRY / PROVINCIAL — does NOT map to `RaceCode` |
| `scheduled_start` | TEXT | ISO timestamp, UTC (`Z` suffix) — maps to contract `RaceMetadata.jump_time` (converted to Adelaide local) |
| `betfair_win_market_id` | TEXT | format `"1.254588168"` — Betfair Win market identifier |
| `betfair_place_market_id` | TEXT | parallel place market |
| `race_group` | TEXT | "Group 1" / "Group 2" / "Group 3" / "Listed" / "ungrouped" — maps to contract `RaceMetadata.group_or_tier` |
| `track_type` | TEXT | "turf" / "synthetic" — maps to contract `RaceMetadata.surface` |
| `betfair_last_snapshot_at` | TEXT | freshness anchor for race-level reads |
| `created_at` / `updated_at` | TEXT | row-level timestamps |
| `capture_status` | TEXT | "PENDING" default; informs availability classification |

**Mapping gaps surfaced as W1 findings:**
- No `event_id` column. Contract `event_id: str` parameter implemented as `betfair_win_market_id` lookup. See W1 Finding F1.
- No `code` discriminator (thoroughbred / harness / greyhound). capture.db is thoroughbred-only by data shape. Implementation defaults to `RaceCode.THOROUGHBRED`. See W1 Finding F2.

## §3 — `runners` columns (relevant subset)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | capture.db internal runner PK |
| `race_id` | INTEGER FK → races.id | join key |
| `runner_name` | TEXT | maps to `RunnerMetadata.name` |
| `barrier` | INTEGER | maps to `RunnerMetadata.barrier` |
| `weight_kg` | REAL | maps to `RunnerMetadata.weight_kg` |
| `jockey` | TEXT | maps to `RunnerMetadata.jockey` |
| `trainer` | TEXT | maps to `RunnerMetadata.trainer` |
| `form_string` | TEXT | maps to `RunnerMetadata.form_indicators` |
| `betfair_selection_id` | INTEGER | format like `69129132` — Betfair selection identifier |
| `scratched` | INTEGER (0/1) | maps to `RunnerMetadata.scratching_status` (`ACTIVE` if 0, `SCRATCHED` if 1) |
| `scratched_at` | TEXT | ISO timestamp; populated when scratched |
| `finish_position` | INTEGER | maps to `RunnerResult.finish_position` |
| `margin_lengths` | REAL | maps to `RunnerResult.beaten_margin_lengths` |
| `result_status` | TEXT | values: `WINNER` / `LOSER` / `PLACED` / `REMOVED` / NULL |
| `results_source` | TEXT | values: `betfair_only` / `betfair_and_subscription` / `subscription` / NULL |
| `sp_fixed` | REAL | settled SP (Betfair-side BSP at race close) |
| `stewards_comment` | TEXT | free-text; informs `RunnerResult.stewards_status` |

**Notes:**
- `RunnerResult.bsp` populated from `runners.sp_fixed` first, falling back to `betfair_snapshots.bsp_price` final-snapshot, then `betfair_historical.win_bsp`.
- `RunnerResult.stewards_status` maps to `OFFICIAL` by default; capture.db does not track stewards' status as a typed enum. See W1 Finding F4.
- `RunnerResult.sectional_times_seconds` not in capture.db — always `None`. See W1 Finding F5.
- `RunnerResult.dead_heat` derived: count of `result_status = 'WINNER'` rows for the race; ≥2 → dead heat.

## §4 — `betfair_snapshots` columns

| Column | Type | Notes |
|---|---|---|
| `race_id` | INTEGER FK | |
| `runner_id` | INTEGER FK | |
| `snapshot_time` | TEXT | ISO timestamp with timezone offset |
| `minutes_to_start` | REAL | negative = pre-jump, positive = post-jump |
| `best_back_price` / `best_back_size` | REAL | top-of-book back |
| `best_lay_price` / `best_lay_size` | REAL | top-of-book lay |
| `total_matched` | REAL | market-level matched volume |
| `market_status` | TEXT | OPEN / SUSPENDED / CLOSED |
| `runner_status` | TEXT | ACTIVE / WINNER / LOSER / REMOVED |
| `bsp_price` | REAL | reconciled BSP (post-close) |
| `sp_near_price` / `sp_far_price` | REAL | SP projections (pre-close) |
| `back_depth_json` / `lay_depth_json` | TEXT | JSON-encoded depth |
| `is_final_snapshot` | INTEGER | 0/1; identifies the last snapshot in a race |
| `snapshot_phase` | TEXT | bracketing label |

## §5 — `betfair_historical` columns

| Column | Type | Notes |
|---|---|---|
| `bf_win_market_id` | TEXT | join key parallel to races.betfair_win_market_id |
| `bf_selection_id` | INTEGER | join key |
| `win_bsp` | REAL | settled BSP (canonical) |
| `win_result` | TEXT | "WINNER" / "LOSER" / etc. |
| `place_bsp` | REAL | settled place BSP |
| `place_result` | TEXT | place result |

Used as a settlement-side fallback for §9.3 results and §9.5 BSP when the live `runners.sp_fixed` is null but historical reconciliation has landed.

## §6 — Indexes available for query planning

- `races`: `idx_races_date_status` (race_date, capture_status), `idx_races_start` (scheduled_start).
- `runners`: implied PK `id`; queries by `(race_id, betfair_selection_id)` are uncovered — full table scan or scan over race_id rows. Acceptable for v1.0 (single-race lookups).
- `betfair_snapshots`: `idx_bf_race_runner` (race_id, runner_id), `idx_bf_race_time` (race_id, snapshot_time). Both load-bearing for §9.4 bracketing.
- `betfair_historical`: `idx_bfh_market_selection` (bf_win_market_id, bf_selection_id) — the join used for BSP fallback.

## §7 — Schema observations and W1 implementation choices

1. **`event_id` ↔ `betfair_win_market_id`.** The contract's `event_id: str` parameter is implemented as a `betfair_win_market_id` lookup. capture.db has no Betfair event_id column. See W1 Finding F1.
2. **`RaceCode` always THOROUGHBRED.** capture.db is thoroughbred-only. Harness/greyhound capture is out of scope for the underlying pipeline. See W1 Finding F2.
3. **Timestamps converted to Adelaide local.** capture.db stores ISO strings — UTC for `scheduled_start` (Z suffix), timezone-offset for snapshot_time. Envelope `as_of` and any timestamp on returned models converts to Adelaide local per DR-021.
4. **Identifier-resolution surface joins races + runners.** Resolution succeeds when `(betfair_win_market_id, betfair_selection_id)` joins to a runner row. Lag indicator is the gap between `now` and the most recent snapshot covering that runner.
