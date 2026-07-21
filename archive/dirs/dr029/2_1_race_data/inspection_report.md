# DR-029 §2.1 — race-side data fit-for-purpose: inspection report

**Inspection date:** 2026-04-30 (Adelaide local; ACST, UTC+9:30). Queries run 2026-04-30 11:05–12:00 ACST against the live VPS `capture.db`. All timestamps in this report are Adelaide local unless explicitly marked UTC; the underlying DB stores ISO-8601 with `+00:00` (UTC).

**Pre-reads confirmed.**
- `dr029/dr029_scope.md` §1.2 (two-direct-lines architecture; analytical line is VPS→`capture.db`→`vps_client`) and §2.1 (this scope item).
- `v3_data_requirements.md` §B.2 (B.2.1–B.2.6 mapped onto §B–§F below).
- `agent_review/inputs/data_layer_current.md` §3 (operator-familiarity-decay framing) and §§4–5 (schema-defined view).

**Brief discipline held.** Numbers, distributions, and gaps only. No thresholds, no pass/fail, no remediation proposals. Surprises documented in §H and named-as-findings rather than acted on.

**VPS tunnel restart outcome:** restored manually. The launchd plist `~/Library/LaunchAgents/com.bethub.vps-tunnel.plist` had been firing `StartInterval=30s` for an extended period and accumulating exit-code-126 failures in `/tmp/bethub-tunnel.log` ("Operation not permitted" reading the script under `~/Desktop/`). Direct invocation of `scripts/vps-tunnel.sh --bg` (foreground shell, with TCC permissions) brought the tunnel up; `localhost:8400/health` returns `collector_active=true` with Betfair last-snapshot timestamps fresh to the minute. Direct SSH to `root@187.77.183.9` worked throughout (key auth, distinct from the launchd-tunnel surface) and was used for all measurement queries below via `sqlite3 'file:/home/racing/racing-data-capture/data/capture.db?mode=ro'`.

**Code-stratification heuristic.** `capture.db` has no `race_code` column. The schema-defined `meeting_type` (METRO/PROVINCIAL/COUNTRY/blank) and `track_type` (turf/synthetic/blank) do not cleanly split codes — same venues appear in both. Inference rules used throughout this report:

- **AU thoroughbred** = `state IN ('VIC','NSW','QLD','WA','SA','TAS','NT','ACT')`.
- **NZ (any code)** = `state = 'NZ'`.
- **AU harness (heur)** = `state IS NULL/blank` AND `LOWER(race_name) LIKE '%pace%' OR '%trot%' OR '%mobile%' OR '%stand%'`.
- **AU greyhound (heur, residual)** = `state IS NULL/blank` AND not harness keyword.
- **foreign / other** = any other non-AU `state` value (HK, SAF, ARG, NZL, AUS, UAE, etc.).

The greyhound bucket is residual — some unkeyed harness races may land there. Operator-Claude can refine if needed; the tables below carry the heuristic transparently as a column.

**Scope reminder.** Seven measurement sections (§A–§G) plus an anomalies section (§H). Two windows reported side-by-side (last-30-days; last-12-months). Per-code stratification with all-codes row where useful. NZ pass-through detected: 464 races present (12m); §B / §C numbers reported for the NZ subset. §E / §F / §G use the discovered live-capture-start floor (2026-03-02) instead of the full 12-month window — soft-book and live Betfair sources do not backfill.

### §0.1 Operator-side hygiene observation (non-blocking, parking-lot for tunnel-auto-restart arc)

Captured during tunnel restoration; flagged for the reachability-arc tunnel-auto-restart hygiene component (`work_in_progress.md` §11). Observation only — no action taken.

`com.bethub.vps-tunnel.plist` settings observed:

| Key | Value |
| :-- | :-- |
| `RunAtLoad` | `true` |
| `KeepAlive` | `false` |
| `StartInterval` | `30` (seconds) |
| `Label` | `com.bethub.vps-tunnel` |
| `ProgramArguments` | `/bin/bash /Users/tim/Desktop/Projects/bethub-v2/scripts/vps-tunnel.sh --bg` |
| `StandardOutPath` / `StandardErrorPath` | `/tmp/bethub-tunnel.log` |

`launchctl print gui/501/com.bethub.vps-tunnel` reports `runs = 11992` and `last exit code = 126` at the moment of inspection. The 30-second `StartInterval` re-fires the script on schedule, but every fire returns 126 because launchd-spawned `/bin/bash` cannot read the script under `~/Desktop/` — a macOS TCC (Transparency, Consent and Control) sandbox: launchd-spawned binaries do not inherit the user's Full Disk Access permission. The 9+ day outage is therefore not a `KeepAlive=false` symptom: even with `KeepAlive=true`, the launchd-side script invocation would still fail with `Operation not permitted`. The outage cause is the script-location-under-`~/Desktop/` constraint, not the supervision policy.

Two observations follow naturally (operator-Claude's call whether to act):

- The launchd plist is currently mis-aligned with macOS TCC — fixable by relocating the script outside `~/Desktop/` (e.g. `~/Library/Application Support/`, or a path outside the TCC-protected directories).
- `KeepAlive=false` plus 30-second `StartInterval` is a periodic-poll supervision pattern, not a crash-restart one. If a tunnel SSH process exits cleanly mid-run (server-side disconnection), launchd does not relaunch it within the same 30-second cycle — it waits for the next interval. This is independent of the TCC issue.

---

## §A — Schema discovery

Database file: `/home/racing/racing-data-capture/data/capture.db` (2.0 GB; WAL active at 4.5 MB; SQLite 3.45.1). Opened read-only via `mode=ro` URI for all queries.

### A.1 Table inventory (rows total / 30d / 12m / oldest / newest)

| Table | Rows total | 30-day rows | 12-month rows | Oldest ts | Newest ts |
| :-- | --: | --: | --: | :-- | :-- |
| `races` | 56,306 | 17,307 | 51,153 | 2025-03-03 | 2026-04-30 |
| `runners` | 421,651 | 56,730 (via race_date) | 370,152 | 2025-03-03 | 2026-04-30 |
| `betfair_snapshots` | 1,629,309 | 838,670 | 1,629,309 | 2026-03-02T05:26 UTC | 2026-04-30T01:52 UTC |
| `bookmaker_snapshots` | 2,727,085 | 1,487,956 | 2,727,085 | 2026-03-02T05:26 UTC | 2026-04-30T01:55 UTC |
| `betfair_historical` | 163,809 | 0 | 137,037 | 2025-03-01 | **2026-02-28** |
| `daily_calibration_summary` | 60 | 26 | 60 | 2026-01-15 | 2026-04-28 |
| `snapshot_batch_summary` | 409,175 | 215,518 | 409,175 | 2026-03-03T01:16 UTC | 2026-04-30T01:55 UTC |

Two structural floors emerge that frame everything below:

- **Live-capture floor:** `betfair_snapshots`, `bookmaker_snapshots`, and `snapshot_batch_summary` all begin at **2026-03-02 05:26 UTC** (= 2026-03-02 ~14:56 ACST). 60 days of data at the time of inspection. Older races have no time-series.
- **Historical-CSV ceiling:** `betfair_historical` runs **2025-03-01 to 2026-02-28** and stops there. The CSV import pipeline appears to have not run for ~60 days. There is a 2-day gap between the historical ceiling (2026-02-28) and the live-capture floor (2026-03-02).

### A.2 CREATE TABLE statements (verbatim)

```sql
CREATE TABLE races (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_date TEXT NOT NULL,
    venue TEXT NOT NULL,
    venue_normalised TEXT NOT NULL,
    state TEXT,
    race_number INTEGER NOT NULL,
    race_name TEXT,
    distance_raw TEXT,
    distance_metres INTEGER,
    race_class TEXT,
    track_condition_raw TEXT,
    track_condition TEXT,
    track_condition_rating INTEGER,
    meeting_type TEXT,
    scheduled_start TEXT,
    prize_total REAL,
    field_size INTEGER,
    active_field_size INTEGER,
    place_paying_positions INTEGER,
    is_trial INTEGER DEFAULT 0,
    is_jump_out INTEGER DEFAULT 0,
    winning_time_seconds REAL,
    winning_time_raw TEXT,
    betfair_win_market_id TEXT,
    betfair_place_market_id TEXT,
    ladbrokes_race_id TEXT,
    neds_race_id TEXT,
    sportsbet_race_id TEXT,
    tab_race_id TEXT,
    pointsbet_race_id TEXT,
    palmerbet_race_id TEXT,
    subscription_meet_id TEXT,
    subscription_synced_at TEXT,
    match_confidence REAL,
    match_method TEXT,
    match_evidence TEXT,
    has_betfair_capture INTEGER DEFAULT 0,
    has_bookies_capture INTEGER DEFAULT 0,
    has_subscription_sync INTEGER DEFAULT 0,
    betfair_last_snapshot_at TEXT,
    bookies_last_snapshot_at TEXT,
    capture_status TEXT DEFAULT 'PENDING',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    unibet_race_id TEXT,
    playup_race_id TEXT,
    race_group TEXT,
    track_type TEXT,
    tabtouch_race_id TEXT,
    UNIQUE(race_date, venue_normalised, race_number)
)
```

```sql
CREATE TABLE runners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL REFERENCES races(id),
    runner_name TEXT NOT NULL,
    runner_name_normalised TEXT NOT NULL,
    runner_number INTEGER,
    runner_key TEXT NOT NULL,
    barrier INTEGER,
    jockey TEXT,
    trainer TEXT,
    weight_raw TEXT,
    weight_kg REAL,
    age TEXT,
    sex TEXT,
    rating INTEGER,
    form_string TEXT,
    betfair_selection_id INTEGER,
    betfair_sort_priority INTEGER,
    subscription_horse_id TEXT,
    scratched INTEGER DEFAULT 0,
    scratched_at TEXT,
    scratch_source TEXT,
    finish_position INTEGER,
    margin_raw TEXT,
    margin_lengths REAL,
    result_status TEXT,
    results_source TEXT,
    sp_fixed REAL,
    prize_won REAL,
    sire TEXT,
    dam TEXT,
    stewards_comment TEXT,
    career_win_percent REAL,
    career_place_percent REAL,
    match_confidence REAL,
    match_method TEXT,
    UNIQUE(race_id, runner_key)
)
```

```sql
CREATE TABLE betfair_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL REFERENCES races(id),
    runner_id INTEGER REFERENCES runners(id),
    snapshot_time TEXT NOT NULL,
    minutes_to_start REAL,
    best_back_price REAL,
    best_back_size REAL,
    best_lay_price REAL,
    best_lay_size REAL,
    total_matched REAL,
    market_status TEXT,
    runner_status TEXT,
    num_priced_runners INTEGER,
    snapshot_phase TEXT,
    is_final_snapshot INTEGER DEFAULT 0,
    bsp_price REAL,
    source TEXT DEFAULT 'live',
    back_depth_json TEXT,
    lay_depth_json TEXT,
    last_match_time TEXT,
    matched_amount REAL,
    sp_near_price REAL,
    sp_far_price REAL,
    snapshot_batch_id TEXT,
    UNIQUE(race_id, runner_id, snapshot_time)
)
```

```sql
CREATE TABLE bookmaker_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL REFERENCES races(id),
    runner_id INTEGER REFERENCES runners(id),
    bookmaker TEXT NOT NULL,
    snapshot_time TEXT NOT NULL,
    minutes_to_start REAL,
    win_odds REAL,
    place_odds REAL,
    snapshot_phase TEXT,
    snapshot_batch_id TEXT,
    UNIQUE(race_id, runner_id, snapshot_time, bookmaker)
)
```

```sql
CREATE TABLE betfair_historical (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER,
    runner_id INTEGER,
    bf_win_market_id TEXT,
    bf_place_market_id TEXT,
    bf_selection_id INTEGER,
    meeting_date TEXT,
    track TEXT,
    state_code TEXT,
    race_no INTEGER,
    distance INTEGER,
    race_type TEXT,
    scheduled_time TEXT,
    actual_off_time TEXT,
    tab_number INTEGER,
    selection_name TEXT,
    selection_name_normalised TEXT,
    win_bsp REAL,
    place_bsp REAL,
    win_result TEXT,
    place_result TEXT,
    win_ppwap REAL,
    win_ppmax REAL,
    win_ppmin REAL,
    win_pp_traded_vol REAL,
    win_ipwap REAL,
    win_ipmax REAL,
    win_ipmin REAL,
    win_ip_traded_vol REAL,
    best_back_at_off REAL,
    best_lay_at_off REAL,
    overround_at_off REAL,
    match_method TEXT,
    match_confidence REAL,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bf_win_market_id, bf_selection_id)
)
```

```sql
CREATE TABLE daily_calibration_summary (
    date TEXT PRIMARY KEY,
    n_races INTEGER,
    n_runners INTEGER,
    n_winners INTEGER,
    betfair_brier_score REAL,
    betfair_mean_bias_pp REAL,
    fav_strike_rate REAL,
    avg_overround_bookmakers REAL,
    n_sources_active INTEGER,
    created_at TEXT
)
```

```sql
CREATE TABLE snapshot_batch_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    race_id INTEGER NOT NULL REFERENCES races(id),
    source TEXT NOT NULL,
    snapshot_time TEXT NOT NULL,
    n_runners_captured INTEGER NOT NULL DEFAULT 0,
    n_runners_expected INTEGER,
    overround REAL,
    is_complete INTEGER DEFAULT 0,
    UNIQUE(batch_id, race_id, source)
)
```

### A.3 Indexes

| Table | Index | Definition |
| :-- | :-- | :-- |
| `races` | `idx_races_date_status` | `(race_date, capture_status)` |
| `races` | `idx_races_start` | `(scheduled_start)` |
| `runners` | (autoindex on `UNIQUE(race_id, runner_key)`) | — |
| `betfair_snapshots` | `idx_bf_race_runner` | `(race_id, runner_id)` |
| `betfair_snapshots` | `idx_bf_race_time` | `(race_id, snapshot_time)` |
| `betfair_snapshots` | `idx_bf_batch` | `(snapshot_batch_id)` |
| `bookmaker_snapshots` | `idx_bk_race_runner` | `(race_id, runner_id)` |
| `bookmaker_snapshots` | `idx_bk_race_bk_time` | `(race_id, bookmaker, snapshot_time)` |
| `bookmaker_snapshots` | `idx_bk_batch` | `(snapshot_batch_id)` |
| `betfair_historical` | `idx_bfh_market_selection` | `(bf_win_market_id, bf_selection_id)` |
| `betfair_historical` | `idx_bfh_meeting` | `(meeting_date, track, race_no)` |
| `betfair_historical` | `idx_bfh_race_runner` | `(race_id, runner_id)` |
| `betfair_historical` | `idx_bfh_bsp` | `(win_bsp) WHERE win_bsp IS NOT NULL` |
| `snapshot_batch_summary` | `idx_batch_summary_batch` | `(batch_id)` |
| `snapshot_batch_summary` | `idx_batch_summary_race` | `(race_id, source)` |

Plus auto-indexes on every `UNIQUE` constraint.

### A.4 Schema-vs-documentation deltas

`agent_review/inputs/data_layer_current.md` §§4–5 names the following fields as the schema-defined view. Verified against the actual `CREATE TABLE`:

- **`race_class`** — present (`races.race_class`).
- **`race_distance`** — different name: `races.distance_metres` (and `distance_raw`).
- **`race_surface`** — **NOT IN SCHEMA.** No surface column on `races`. Closest analogue is `track_type` (turf/synthetic/blank), which conflates surface with course-shape; nothing distinguishes turf-surface from dirt-surface for the few foreign races where dirt would apply.
- **`race_group`** — present (`races.race_group`), positioned at end of `CREATE TABLE` indicating recent column addition.
- **`track_condition`** — present (plus `track_condition_raw` and `track_condition_rating`).
- **`track_type`** — present, positioned at end indicating recent column addition.
- **`scheduled_jump_time`** — different name: `races.scheduled_start`.
- **`actual_jump_time`** — **NOT ON `races` TABLE.** Available only via `betfair_historical.actual_off_time`, which exists for the 2025-03-01 → 2026-02-28 historical-CSV window and not for the live-capture window.
- **`race_code`** — **NOT IN SCHEMA.** No code column. Stratification by code requires the heuristic documented in the header.
- **`venue`** / **`race_number`** — present.
- **`scratched_at`** — present.
- **`late_scratch` flag** — **NOT IN SCHEMA.** Late-scratch can only be derived by computing `scratched_at` minus `scheduled_start`.
- **Result `observed_at` timestamp** — **NOT IN SCHEMA explicitly.** `races.updated_at` exists as a generic update timestamp; `runners.scratched_at` covers scratch events; nothing names result-observation time.
- **Dead-heat indication** — **NO EXPLICIT FLAG.** Derivable from multiple `runners.finish_position = 1` for one race.
- **Stewards' inquiry status** — text only (`runners.stewards_comment`); no boolean status flag.
- **Sectional times** — race-level winning time only (`races.winning_time_seconds`); per-runner sectionals not in schema.
- **Top-3 back/lay depth** — stored as JSON: `betfair_snapshots.back_depth_json`, `lay_depth_json`.
- **BSP per runner** — split: `betfair_historical.win_bsp` / `place_bsp` for the historical-CSV window; `betfair_snapshots.bsp_price` exists as a column but is **0% populated** (see §F).

Tables present in `capture.db` but not named in `data_layer_current.md` §§4–5: `snapshot_batch_summary` (batch tracking; rows present and active). Documented tables that are absent: none — all schema-defined tables exist.

---

## §B — Race metadata coverage (cross-ref `v3_data_requirements.md` B.2.1)

### Measurement summary

Race-metadata population is sharply non-uniform across codes and across the 30d-vs-12m windows. The headline shape: thoroughbred has the deepest schema-field set populated; harness and greyhound mostly do not carry the thoroughbred schema fields at all. Within thoroughbred, **`race_class` and `distance_metres` are 0% in the 30-day window and 83% in the 12-month window** — recent races sit in `capture_status='PENDING'` until a backfill enriches them ~30+ days later. Conversely, **`track_type` is 100% in the 30-day window and 19% in the 12-month window** — a recently-added column that the live capture pipeline now writes but pre-existing rows do not. `race_group` is universally rare (≤2% across all windows), consistent with black-type tier being a small fraction of races. `scheduled_start`, `venue`, and `race_number` are at-or-near 100% across all codes and windows.

### B.1 Per-code population, side-by-side 30d / 12m

| Code (heuristic) | Races 30d | Races 12m | `race_class` 30d / 12m | `distance_metres` 30d / 12m | `race_group` 30d / 12m | `track_condition` 30d / 12m | `track_type` 30d / 12m | `scheduled_start` 30d / 12m | `venue` 30d / 12m | `race_number` 30d / 12m |
| :-- | --: | --: | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| AU thoroughbred | 3,255 | 30,730 | 0.0% / 83.2% | 0.0% / 83.2% | 0.0% / 1.7% | 50.8% / 89.4% | 100.0% / 18.6% | 97.9% / 99.8% | 100% / 100% | 100% / 100% |
| AU harness (heur) | 749 | 2,569 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 100.0% / 97.5% | 100% / 100% | 100% / 100% | 100% / 100% |
| AU greyhound (heur, residual) | 12,842 | 17,055 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 100.0% / 99.0% | 20.3% / 35.1% | 100% / 100% | 100% / 100% |
| NZ | 281 | 464 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 81.9% / 89.0% | 100% / 100% | 81.9% / 89.0% | 100% / 100% | 100% / 100% |
| Foreign | 180 | 335 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 88.3% / 93.7% | 100.0% / 97.0% | 88.3% / 93.7% | 100% / 100% | 100% / 100% |
| **All codes** | **17,307** | **51,153** | — | — | — | — | — | — | — | — |

### B.2 Time-decay diagnostic (AU thoroughbred only)

Splits the 12-month window into recent (30d), middle (31d-365d), and old (>365d) to surface the structural backfill lag and the recent-column-addition pattern.

| Bucket | n races | `race_class` | `distance_metres` | `track_type` | `track_condition` | `race_group` |
| :-- | --: | :-- | :-- | :-- | :-- | :-- |
| 0–30d | 3,255 | 0.0% | 0.0% | 100.0% | 50.8% | 0.0% |
| 31–365d | 27,475 | 93.0% | 93.0% | 8.9% | 94.0% | 2.0% |
| >365d | 5,136 | 100.0% | 100.0% | 0.0% | 97.1% | 0.0% |

Two distinct lag patterns visible: (a) **race_class / distance_metres / track_condition / race_group** populate via a backfill that arrives after ~30 days and is in steady state by 31–365d (race_class settles at 93% / 100%); (b) **track_type** is a recent column whose write path is wired into current capture but never backfilled to older rows, so it inverts (100% / 9% / 0%). The race_group rate maxes at 2% even in the well-populated 31-365d slice — operator interpretation work for §H whether that is structural sparsity (most races aren't G1/G2/Listed) or population-pipeline gap.

### B.3 `actual_jump_time` derived from `betfair_historical.actual_off_time`

`races` does not carry `actual_jump_time`. Closest source is `betfair_historical.actual_off_time` (joined on `race_id`).

| Window | Completed races (race_date ≤ today-1d, ≥1 finish_position populated) | Joined `actual_off_time` populated | Coverage |
| :-- | --: | --: | --: |
| 30d (2026-03-31 to 2026-04-29) | 0 | 0 | n/a |
| 12m (2025-04-30 to 2026-04-29) | 23,647 | 12,119 | 51.2% |

The 30d denominator is 0 because `finish_position` is itself 0% populated in the 30-day window (see §D — results capture has not run for the live-capture-window races). The 12m number is bounded above by `betfair_historical`'s 2026-02-28 ceiling: races after that date have no historical row regardless of whether they're complete.

Sanity check on `actual_off_time` quality where it does exist: jump-vs-scheduled offset for thoroughbred 90-365d races has p50 = 1.0 min, p95 = 3.7 min, p99 = 6.2 min, max = 20.3 min, min = -40.8 min (some rows show jumps materially before scheduled — likely scheduling-data refresh skew rather than real early jumps).

### B.4 Distance distribution for AU thoroughbred (12m, where populated)

`distance_metres` is populated only for the AU-thoroughbred slice (other codes 0% as above). The parser in the capture pipeline does not extract metres from harness `race_name` patterns like `R5 1720m Pace M` even though metres is literally embedded.

| Code | n with distance | min | p50 | p95 | max |
| :-- | --: | --: | --: | --: | --: |
| AU thoroughbred | 25,553 | 10 m | 1,100 m | 1,968 m | 5,500 m |

Out-of-range tally:
- distance < 800 m: 1,219 races (likely barrier trials / jump-outs / 600m sprints — `is_trial=1` and `is_jump_out=1` flags exist on races but were not cross-tabulated).
- distance > 4,000 m: 5 races.
- distance NULL on AU-thoroughbred 12m: 5,177 races (mostly the 30d-PENDING subset).

### B.5 NZ subset — population state for the pass-through detection

464 NZ races present in 12m (281 in 30d). Per the table in B.1: NZ races have `track_type` 100% populated, `track_condition` ~89%, `scheduled_start` ~89%, `venue`/`race_number` 100%. NZ races have **0% `race_class` / `distance_metres` / `race_group`** — NZ is not enriched by the same Racing API path that backfills AU thoroughbred. Runner-level NZ population is reported in §C.1; jurisdiction handling oddity noted in §H.

### Anomalies in §B

- `state` field has 10 rows with value `'AUS'` (rather than `NSW`) — all at Wentworth Park, all with `race_name` blank; per the heuristic these get bucketed as foreign rather than AU-greyhound. Likely upstream data-quality issue in the source feed.
- `state` carries international codes mixed with AU-state codes: HK (168), SAF (26), TX (24), PAN (23), PA (20), ARG (12), NZL (11), AUS (10), WV (9), UAE (9), LA (9), NE (7), FL (7) — total 333 foreign races. Some are US-state two-letter codes (TX, PA, WV, LA, NE, FL) which collide-by-design with AU two-letter state codes; in this DB the AU codes are unambiguous because they don't overlap with the US-state set.

---

## §C — Runner metadata coverage (cross-ref `v3_data_requirements.md` B.2.2)

### Measurement summary

Runner-name coverage is 100% across all codes and windows (no row exists without a name). Beyond name, the picture is sharply asymmetric. **AU thoroughbred runners** carry the Racing-API-sourced fields (jockey, trainer, weight, form) at 70-86% in the 12m window but those fields are mostly absent in the 30-day window — same backfill lag as §B. **AU harness and AU greyhound** have less than 25% population on jockey/trainer/weight/barrier across both windows, with form_string 0% and finish_position / margin 0% — the schema fields exist but the capture pipeline writes very little for these codes. **NZ and foreign** runners have 100% on jockey / trainer / weight / barrier but 0% finish_position / margin / `betfair_selection_id`. The most consequential structural fact in this section: **zero runners across the entire database have BOTH `finish_position` and `betfair_selection_id` populated** — the two come from disjoint ingestion paths separated at the live-capture-start floor.

### C.1 Per-code per-window field population

| Code | Runners 30d | Runners 12m | `runner_name` | `barrier` 30d / 12m | `weight_kg` 30d / 12m | `jockey` 30d / 12m | `trainer` 30d / 12m | `form_string` 30d / 12m | `finish_position` 30d / 12m | `margin_lengths` 30d / 12m | `betfair_selection_id` 30d / 12m |
| :-- | --: | --: | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| AU thoroughbred | 25,215 | 299,234 | 100% | 27.9% / 63.7% | 10.6% / 67.6% | 35.9% / 83.5% | 0.0% / 85.7% | 0.0% / 77.6% | 0.0% / 66.8% | 0.0% / 52.4% | 60.9% / 9.5% |
| AU harness (heur) | 4,838 | 19,747 | 100% | 0.9% / 0.7% | 0.9% / 0.7% | 0.9% / 0.7% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 99.1% / 99.3% |
| AU greyhound (heur) | 22,490 | 44,016 | 100% | 2.4% / 22.4% | 2.2% / 22.3% | 2.5% / 22.5% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 97.4% / 77.4% |
| NZ | 2,871 | 4,823 | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% |
| Foreign | 1,316 | 2,332 | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% |

### C.2 The two-population structural finding (`finish_position` vs `betfair_selection_id`)

Cross-tab over the entire `runners` table:

| `finish_position` | `betfair_selection_id` | Rows |
| :-- | :-- | --: |
| NULL | NULL | 101,289 |
| NULL | populated | 82,090 |
| populated | NULL | 238,272 |
| populated | populated | **0** |

**No row in the entire database carries both `finish_position` AND `betfair_selection_id`.** The two come from disjoint ingestion paths that do not overlap. By race_date bucket:

| Bucket | Runners | `finish_position` populated | `betfair_selection_id` populated | Both |
| :-- | --: | :-- | :-- | --: |
| 0–30d | 56,730 | 0.0% | 74.1% | 0 |
| 30–60d | 58,327 | 1.6% | 68.6% | 0 |
| 60–90d | 24,845 | 79.7% | 0.0% | 0 |
| 90–180d | 74,378 | 78.5% | 0.0% | 0 |
| 180–365d | 155,872 | 77.4% | 0.0% | 0 |
| >365d | 51,499 | 74.7% | 0.0% | 0 |

There is a hard break at the live-capture-start floor (~60 days ago, the period where `betfair_historical` import last ran). Runners before the break carry `finish_position` (from Racing API subscription) but no `betfair_selection_id` (Betfair-side identifiers were not joined back to `runners`). Runners after the break carry `betfair_selection_id` (live capture writes it from the Betfair Streaming feed) but no `finish_position` (results aren't being populated for live-capture-window races).

### C.3 Scratching-event capture timing and completeness

Of all runners with `scratched=1` in the 12m window, by code:

| Code | Scratched runners (12m) | With `scratched_at` | Pct | With `scratch_source` | Pct |
| :-- | --: | --: | :-- | --: | :-- |
| AU thoroughbred | 57,441 | 8,512 | **14.8%** | 8,512 | 14.8% |
| AU harness (heur) | 378 | 378 | 100.0% | 378 | 100.0% |
| AU greyhound (heur) | 4,955 | 4,955 | 100.0% | 4,955 | 100.0% |
| NZ | 1,045 | 1,045 | 100.0% | 1,045 | 100.0% |
| Foreign | 24 | 24 | 100.0% | 24 | 100.0% |

The asymmetry is striking — AU thoroughbred has the worst coverage of `scratched_at` (15%); every other code is at 100%. Likely-explanatory hypotheses (operator's call to confirm in §H or follow-up): scratch events for AU thoroughbred flow from multiple sources (Racing API, individual scrapers, Betfair) and only some of those sources record a timestamp; harness/greyhound/NZ/foreign flow through a single source path that always records `scratched_at`.

### C.4 `late_scratch` derivation (no flag in schema)

Computing `scratched_at` minus `scheduled_start` for the 14,744 scratched runners with both timestamps available in the 12m window:

| Bucket | Runners |
| :-- | --: |
| > 3h before scheduled jump | 211 |
| 30 min – 3h before | 10,311 |
| 0 – 30 min before (LATE per brief's definition) | 272 |
| 0 – 30 min after scheduled jump | 3,848 |
| 30 min – 3h after | 92 |
| > 3h after | 10 |

Note the 3,848 with `scratched_at` 0–30 min *after* `scheduled_start`. These are not "late scratchings" in the operational sense; they're scratched-runner records whose write timestamp is later than the scheduled-jump field. Without an explicit `late_scratch` flag, deriving the flag is a definitional question: late-relative-to-scheduled-jump (272 in 12m thoroughbred, plus the 3,848 between 0-30 min after if those count as the inclusive form of "within 30 min of jump") versus late-relative-to-actual-jump (which requires `actual_jump_time`, which itself only exists for 51.2% of completed races per §B.3).

### C.5 BSP per-runner coverage

Reported as a separate query in §F (the canonical BSP section). Headline numbers:

- Live-capture window (race_date ≥ 2026-03-02): 99,377 completed runners, **0 with BSP from any source** — `betfair_historical` has no rows past 2026-02-28; `betfair_snapshots.bsp_price` is 0.0% populated.
- Historical-CSV window (2025-03-01 to 2026-02-28), AU thoroughbred 12m: 1,537,822 runner-rows, 92.9% have `betfair_historical.win_bsp` populated for any join row; 49% of races in that window have any `betfair_historical` row at all (14,420 / 29,601).

### Anomalies in §C

- The complete absence of `finish_position`+`betfair_selection_id` overlap across the database is the single largest structural fact in this report; carried forward to §H.
- `betfair_selection_id` 30d / 12m for AU thoroughbred is 60.9% / 9.5%, an inversion identical in shape to the `track_type` inversion in §B (recent-column-write versus older-row-no-backfill).
- The 99% `betfair_selection_id` rate for AU harness (heur) is striking — harness has very few other fields populated but is consistently linked to Betfair.

---

## §D — Results coverage (cross-ref `v3_data_requirements.md` B.2.3)

### Measurement summary

Results are populated in the historical-CSV window and are essentially absent in the live-capture window. **`finish_position` is 0% across all codes in the 30-day window**, then steps up at ~60 days ago to ~78% (the historical-CSV ceiling). This is the same hard break as §C.2. AU thoroughbred 12m has 82.6% `finish_position`, 64.9% `margin_lengths`, 92.4% `results_source`, 45.4% `stewards_comment`, 77.1% `winning_time_seconds`. Every other code has 0% `finish_position` / `margin` / `winning_time` in the 12m window — even though the schema fields exist. `results_source` distribution is two-source ('subscription' and 'betfair_only') with **zero overlap**: no race has runner records carrying both sources, so the two-source-agreement settlement path described in `v3_data_requirements.md` B.2.3 cannot be evaluated against this DB as it stands.

### D.1 Per-code per-window completed-races population

Denominator: runners on completed races (`race_date ≤ today-1d`, `scratched=0`).

| Code | Completed runners 30d | Completed runners 12m | `finish_position` 30d / 12m | `margin_lengths` 30d / 12m | `results_source` 30d / 12m | `stewards_comment` 30d / 12m |
| :-- | --: | --: | :-- | :-- | :-- | :-- |
| AU thoroughbred | 20,033 | 241,734 | 0.0% / 82.6% | 0.0% / 64.9% | 64.3% / 92.4% | 0.0% / 45.4% |
| AU harness (heur) | 4,766 | 19,369 | 0.0% / 0.0% | 0.0% / 0.0% | 99.0% / 97.8% | 0.0% / 0.0% |
| AU greyhound (heur) | 19,884 | 39,061 | 0.0% / 0.0% | 0.0% / 0.0% | 96.4% / 75.0% | 0.0% / 0.0% |
| NZ | 2,155 | 3,735 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% |
| Foreign | 1,301 | 2,308 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% |

### D.2 Race-level coverage: `winning_time_seconds`, dead-heat, race count

Same denominator at race level.

| Code | Races 30d | Races 12m | `winning_time_seconds` 30d / 12m | Dead-heat 12m | Dead-heat 30d |
| :-- | --: | --: | :-- | --: | --: |
| AU thoroughbred | 3,194 | 30,669 | 0.0% / 77.1% | 29 | 0 |
| AU harness (heur) | 724 | 2,544 | 0.0% / 0.0% | 0 | 0 |
| AU greyhound (heur) | 12,517 | 16,730 | 0.0% / 0.0% | 0 | 0 |
| NZ | 273 | 456 | 0.0% / 0.0% | 0 | 0 |
| Foreign | 180 | 335 | 0.0% / 0.0% | 0 | 0 |

Dead-heat detection is by counting races with multiple `runners.finish_position = 1`. 29 instances in 12m AU thoroughbred is on order with the natural rate (a handful per year), and 0 in 30d is consistent with the 0% finish_position population in the 30d window (no dead-heats can be detected if no positions are populated).

### D.3 Time-decay of `finish_position` (any code, completed races)

| Bucket | Races completed | Races with any `finish_position` | Pct |
| :-- | --: | --: | :-- |
| 0–7 d | 4,042 | 0 | 0.0% |
| 7–14 d | 3,968 | 0 | 0.0% |
| 14–30 d | 8,878 | 0 | 0.0% |
| 30–60 d | 8,564 | 122 | 1.4% |
| 60–90 d | 2,556 | 2,389 | 93.5% |
| 90–180 d | 7,444 | 6,933 | 93.1% |
| 180–365 d | 15,282 | 14,203 | 92.9% |
| >365 d | 5,153 | 4,669 | 90.6% |

The hard break occurs at ~60 days, which aligns with the `betfair_historical` ceiling (2026-02-28). Pre-break, 90-95% of completed races have ≥1 `finish_position` populated. Post-break, near-zero.

### D.4 Source-identifier distribution

`results_source` distinct values across the entire `runners` table:

| `results_source` | Runner rows | Distinct races |
| :-- | --: | --: |
| `subscription` | 296,769 | 29,019 |
| `betfair_only` | 80,824 | 7,969 |
| (blank / NULL) | 44,069 | 5,662 |

Distinct races with `subscription` source: 29,019. Distinct races with `betfair_only` source: 7,969. Distinct races with **both** runner-records at `subscription` AND `betfair_only` sources (set intersection): **0**. The two source values are mutually exclusive at the runner record level — no race has one runner from `subscription` and another from `betfair_only` simultaneously.

The brief named four expected sources (Betfair / Racing API / Racing Australia / Racenet). The actual capture writes only two distinct values in `results_source`. `subscription` likely corresponds to the Racing API subscription path; `betfair_only` to the Betfair-data-only path. Racing Australia and Racenet do not appear as `results_source` values.

### D.5 Settlement-relevant lag

Brief asks for distribution of (result `observed_at`) minus (`actual_jump_time`). Both inputs are structurally absent for the 30-day window:

- `actual_jump_time` is unavailable for the live-capture window (no `betfair_historical` row past 2026-02-28; no equivalent column on `races`).
- `observed_at` is not stored explicitly. `races.updated_at` is a generic update marker — a race's `updated_at` is updated by every snapshot-batch write, so it tracks last-snapshot rather than first-result-observation.

For races in the 90–365d window where both `actual_off_time` (via `betfair_historical`) and `races.updated_at` exist (105,306 thoroughbred AU rows), the difference is implausibly large (p50 ≈ 9,556 days) — the column-format mismatch confirms `updated_at` is not a useful proxy for result-observation lag. **A clean settlement-lag distribution cannot be computed from the schema as-is.** The structural finding for the wider scope: result-observation timestamps are not first-class data; deriving them requires additional capture (e.g., a dedicated `results.observed_at` field or an event-log of result-population events).

### Anomalies in §D

- `subscription` and `betfair_only` are mutually exclusive at the race level. No two-source-agreement signal is computable from this schema as-is — the two-source agreement framing in `v3_data_requirements.md` B.2.3 (`Betfair Win + Racing API → finalised`) cannot be exercised with current `results_source` semantics.
- 5,662 races have NULL `results_source` (i.e., neither `subscription` nor `betfair_only`).
- Sectional times are entirely absent (no per-runner sectionals column; only `races.winning_time_seconds`).

---

## §E — Betfair time-series cadence (cross-ref `v3_data_requirements.md` B.2.4)

**Window note.** Betfair time-series live-capture-start floor is **2026-03-02 05:26 UTC** = 2026-03-02 14:56 ACST. All §E numbers below are bounded by that floor. The 30-day window (last 30 days from inspection) is fully within the live-capture period. The 12-month window is reduced to "live-capture-start to now" = ~60 days.

### Measurement summary

`betfair_snapshots` has 1,629,309 rows across 8,328 distinct races, averaging 195.6 snapshots per race. Snapshot-field coverage is high for prices (best back ~92%, best lay ~92%, total_matched 100%, top-3 depth ~92%) but `bsp_price` is 0.0% populated despite the column existing in the schema. Cadence is materially looser than the documented tier — measured pre-5min-intensive p50 is ~90-100s versus documented 60s, and the 95th percentile gap in the same window is 7-11 minutes for thoroughbred and greyhound. Foreign and NZ races have 0% Betfair coverage. Only 44% of AU-thoroughbred 30d races have any pre-30min snapshot at all; greyhound (heur) has 81% and harness (heur) 65%.

### E.1 Snapshot inventory

| Metric | Value |
| :-- | --: |
| Total snapshots | 1,629,309 |
| Distinct races covered | 8,328 |
| Average snapshots per race | 195.6 |
| Live-capture-start floor (UTC) | 2026-03-02T05:26:38 |
| Latest snapshot (UTC) | 2026-04-30T01:52:04 |

### E.2 Field population (entire snapshot table)

| Field | Pct |
| :-- | --: |
| `best_back_price` | 92.35% |
| `best_back_size` | 92.35% |
| `best_lay_price` | 91.67% |
| `best_lay_size` | 91.67% |
| `total_matched` | 100.00% |
| `back_depth_json` | 92.15% |
| `lay_depth_json` | 91.48% |
| `minutes_to_start` | 100.00% |
| `snapshot_phase` | 100.00% |
| `runner_id` | 73.02% |
| `bsp_price` | **0.000%** |
| `sp_near_price` | 0.000% |
| `sp_far_price` | 0.000% |

The 27% of rows without `runner_id` are market-level rather than runner-level snapshots. By `snapshot_phase`: STANDARD (47.6%) and INTENSIVE (14.5%) are 100% runner-level; POST_START (37.9%) is 28.7% runner-level — the post-jump phase mostly writes market-level rows (status, total_matched, etc.) without per-runner detail.

### E.3 Per-race snapshot counts in the three windows (last 30 days, completed races)

Counts are total snapshots per race (across all runners and market-level rows), not per-runner-per-race.

| Code | Races 30d | Avg snapshots in [-30, 0] min | Avg in [-5, 0] min (intensive) | Avg in [0, 30] min post | Pct races with ≥1 pre-30min snap |
| :-- | --: | --: | --: | --: | --: |
| AU thoroughbred | 3,125 | 28.5 | 10.0 | 5.4 | **43.8%** |
| AU harness (heur) | 724 | 48.0 | 21.1 | 14.4 | 64.6% |
| AU greyhound (heur) | 2,602 | 55.2 | 21.7 | 14.0 | 80.9% |
| NZ | 222 | 0.0 | 0.0 | 0.0 | 0.0% |
| Foreign | 159 | 0.0 | 0.0 | 0.0 | 0.0% |

**56% of AU-thoroughbred 30d races have no pre-30min Betfair snapshot of any kind.** This is the single largest cadence-related fact in §E. Greyhound (81% covered) and harness (65% covered) have markedly better coverage than thoroughbred. NZ and foreign Betfair markets are not covered at all.

### E.4 Inter-snapshot interval distribution per (race, runner) per code

Sampled across 60-day live-capture window, per-(race, runner) intervals broken down by phase.

| Code | Window | n gaps | p50 (s) | p95 (s) | p99 (s) | max (s) | Pct gaps > 2× documented cadence |
| :-- | :-- | --: | --: | --: | --: | --: | --: |
| AU thoroughbred | pre-30 outside 5min | 111,416 | 334.2 | 667.7 | 795.9 | 1,009 | 7.9% (>600s) |
| AU thoroughbred | pre-5 intensive | 63,350 | 97.4 | 461.1 | 711.1 | 977 | **38.6% (>120s)** |
| AU thoroughbred | in-running 0-10 min post | 33,400 | 90.0 | 487.8 | 735.9 | 900 | 28.9% (>120s) |
| AU harness (heur) | pre-30 outside 5min | 87,485 | 311.9 | 392.9 | 472.9 | 774 | 0.1% |
| AU harness (heur) | pre-5 intensive | 69,087 | 89.9 | 270.0 | 361.7 | 774 | 21.8% |
| AU harness (heur) | in-running 0-10 min post | 47,599 | 80.4 | 134.6 | 211.4 | 555 | 7.4% |
| AU greyhound (heur) | pre-30 outside 5min | 134,642 | 330.9 | 625.9 | 771.3 | 1,034 | 5.8% |
| AU greyhound (heur) | pre-5 intensive | 86,238 | 90.3 | 418.4 | 684.2 | 1,034 | 33.7% |
| AU greyhound (heur) | in-running 0-10 min post | 51,366 | 90.0 | 348.3 | 684.4 | 864 | 20.3% |

### E.5 Documented vs measured cadence

| Window | Documented (`data_layer_current.md` §4.4) | Measured p50 | Measured p95 | Gap-rate (>2× documented) |
| :-- | :-- | :-- | :-- | :-- |
| Standard (outside pre-jump 5min) | 5 min (300 s) | 311–334 s | 393–668 s | 0.1–7.9% |
| Pre-jump intensive (0–5 min before jump) | 60 s | **90–97 s** | **270–461 s** | **22–39%** |
| In-running | 60 s | 80–90 s | 135–488 s | 7–29% |

p50 cadence is broadly in line with documentation outside the intensive window. **Inside the intensive 5-min-pre-jump window, p50 is ~50% looser than documented (90s vs 60s) and the tail is significantly worse: 1 in 3 intervals exceeds 2× documented cadence.** The harness (heur) tail is markedly tighter than thoroughbred or greyhound (p95 = 270s vs 418-461s).

### E.6 Snapshot-phase distribution

| Phase | Snaps | Pct |
| :-- | --: | :-- |
| STANDARD | 776,130 | 47.6% |
| POST_START | 616,795 | 37.9% |
| INTENSIVE | 236,384 | 14.5% |

If the documented model were holding precisely (5min STANDARD outside last 5min, then 60s INTENSIVE in last 5min, then 60s POST_START in-running): per-race expectation depends on race duration. INTENSIVE would write 5 cycles × ~8 runners ≈ 40 snaps per race; with 8,328 races covered, expected ≈ 333,120 INTENSIVE snaps. Measured 236,384 = 71% of expected — consistent with the gap-rate findings above.

### Anomalies in §E

- `bsp_price`, `sp_near_price`, `sp_far_price` columns: 0 rows populated — schema-defined-but-unused. Source-exposes-but-pipeline-doesn't-write observation noted in §H.
- 0% Betfair coverage on NZ (464 races in 12m) and foreign (335). Confirms Betfair scrape config is AU-only.
- 56% of AU-thoroughbred 30d races have no pre-30min snapshot — meaningful given AU thoroughbred is the codified primary code.

---

## §F — BSP and calibration (cross-ref `v3_data_requirements.md` B.2.6)

**Window note.** §F is bounded by both the historical-CSV ceiling (BSP via `betfair_historical`, ends 2026-02-28) and the live-capture floor (`betfair_snapshots`, starts 2026-03-02). Daily and batch summaries use the entire 12m window where they exist.

### Measurement summary

BSP is structurally split. For the historical-CSV window (2025-03-01 to 2026-02-28), AU-thoroughbred runners have 92.9% BSP coverage via `betfair_historical.win_bsp`. For the live-capture window (2026-03-02 onward), **0 runners have BSP from any source** — `betfair_historical` was not extended past 2026-02-28, and the `betfair_snapshots.bsp_price` column has 0 rows populated. Daily calibration summaries are present and continuous from 2026-01-15 to 2026-04-28 with four missing days in the last 60 (Mar 1, Apr 1, Apr 10, Apr 16) — a roughly weekly miss-rate.

### F.1 BSP via `betfair_historical` (window 2025-03-01 to 2026-02-28)

| Code | Runners (in CSV window) | Distinct races | Races with any `betfair_historical` row | Runner-rows with `win_bsp` populated | Pct |
| :-- | --: | --: | --: | --: | :-- |
| AU thoroughbred | 1,537,822 | 29,601 | 14,420 | 1,429,071 | 92.9% |
| AU greyhound (heur, residual) | 340 | 17 | 2 | 269 | 79.1% |

(AU harness, NZ, foreign all have 0 matches via `betfair_historical` join in this window — the historical CSV import covers AU thoroughbred almost exclusively, with sparse coverage of greyhound and zero coverage of harness/NZ/foreign.)

Note the 14,420 / 29,601 = 49% race-level coverage even in the AU-thoroughbred CSV window. Half the AU-thoroughbred races inside the historical-CSV window have no `betfair_historical` row at all.

### F.2 BSP in the live-capture window (race_date ≥ 2026-03-02)

| Source | Live-capture-window completed runners | With BSP populated |
| :-- | --: | --: |
| `betfair_historical.win_bsp` | 99,377 | 0 |
| `betfair_snapshots.bsp_price` | (any timestamp) | 0 |
| `betfair_snapshots.sp_near_price` / `sp_far_price` | (any timestamp) | 0 |

The complete absence of BSP for the live-capture window is the central §F finding. Three named sources, none populated.

### F.3 Daily calibration summary continuity (last 60 days)

`daily_calibration_summary` is being produced; days present versus expected for the last 60 days (one row per day expected; the row for date D is created at ~12:30–13:30 UTC on day D+1):

| Date | Status | n_races | n_winners |
| :-- | :-- | --: | --: |
| 2026-03-01 | **missing** | — | — |
| 2026-03-02 → 2026-03-31 | present (30 / 30 expected) | varies 8–219 | varies 7–212 |
| 2026-04-01 | **missing** | — | — |
| 2026-04-02 → 2026-04-09 | present (8 / 8) | — | — |
| 2026-04-10 | **missing** | — | — |
| 2026-04-11 → 2026-04-15 | present (5 / 5) | — | — |
| 2026-04-16 | **missing** | — | — |
| 2026-04-17 → 2026-04-28 | present (12 / 12) | varies 75–238 | varies 69–234 |
| 2026-04-29 | not yet produced (run is scheduled for 2026-04-30 ~13:30 UTC = ~23:00 ACST) | — | — |

Four missed days in the last 60 (Mar 1, Apr 1, Apr 10, Apr 16). Mar 1 missing aligns with the live-capture-start floor of Mar 2 (no data to summarise on Mar 1). The other three (Apr 1, 10, 16) are unexplained from the data — could be calibration-job execution failures.

`n_winners` in the daily summary table is populated daily despite `runners.finish_position` being 0% in the same window (§D). The calibration job evidently has a separate result-resolution path (likely Betfair market-status / runner_status) that does not write back to `runners.finish_position`. Consequence: `daily_calibration_summary` works but `runners.finish_position` does not.

### F.4 Snapshot batch summary

`snapshot_batch_summary` is producing rows continuously across all 7 active sources (betfair plus 6 bookmakers). Last 30 days show daily activity for each source on every day with racing:

| Date sample | betfair | ladbrokes | neds | playup | pointsbet | sportsbet | tabtouch | unibet |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: |
| 2026-04-26 | 4,074 | 782 | 768 | 568 | 710 | 622 | 791 | (not present this date — scraper?) |
| 2026-04-27 | 2,255 | 676 | 656 | 680 | 680 | 531 | 584 | 489 |
| 2026-04-28 | 2,797 | 418 | 402 | 420 | 420 | 424 | 419 | 420 |
| 2026-04-29 | 3,184 | 670 | 653 | 566 | 566 | 480 | 659 | 480 |
| 2026-04-30 (partial) | 214 | 57 | 55 | 57 | 57 | 63 | 12 | 14 |

Batch counts roughly track racing volume per day. Per-race average completeness (`is_complete=1` rate) was not computed in this section but the recent samples show is_complete=1 on all observed batches in the snapshot.

### Anomalies in §F

- `betfair_snapshots.bsp_price`, `sp_near_price`, `sp_far_price`: 0 rows — schema fields exist for live-capture BSP but the pipeline writes nothing.
- The 49% race-level coverage in `betfair_historical` (within its CSV window) is well below the per-runner 92.9% rate — inconsistent on its face, but explainable by the historical CSV import targeting only a subset of races (specific market types? specific source files?). Operator interpretation in §H.

---

## §G — Soft-book scrapers — health and cadence (cross-ref `v3_data_requirements.md` B.2.5; `data_layer_current.md` §§5.1–5.2)

**Window note.** §G uses live-capture-start (2026-03-02) to now. Soft-book scrapers do not backfill.

### Measurement summary

All seven documented scrapers are active and writing recent data. None are dead. Two scrapers came online later than the live-capture-start floor: sportsbet started 2026-03-21 (19 days late) and tabtouch started 2026-03-30 (28 days late). Cadence per scraper is uniform — all scrapers cluster at p50 ~345s in the standard window and ~140-150s in the intensive window, against a documented 90-120s intensive cadence (slightly looser). Cross-scraper coverage is sharply asymmetric: AU thoroughbred 30d has 25.2% of races covered by all 7 scrapers in the pre-30min window, but **32.1% have zero coverage**. AU harness (heur) and AU greyhound (heur) have 99% zero-coverage rates — soft-book scrapers do not meaningfully cover these codes.

### G.1 Per-scraper inventory (all 30d / 12m = live-capture-window)

| Scraper | Snaps total | Snaps 30d | Races total | Races 30d | First seen (UTC) | Last seen (UTC) | 30d-rate / lifetime-rate |
| :-- | --: | --: | --: | --: | :-- | :-- | --: |
| pointsbet | 574,313 | 225,034 | 4,424 | 1,831 | 2026-03-03T01:16:44 | 2026-04-30T01:54:55 | 0.77 |
| ladbrokes | 440,719 | 227,821 | 3,578 | 1,896 | 2026-03-02T05:26:38 | 2026-04-30T01:55:32 | 1.03 |
| neds | 429,383 | 223,643 | 3,575 | 1,895 | 2026-03-02T05:26:38 | 2026-04-30T01:55:32 | 1.04 |
| unibet | 398,663 | 195,709 | 3,193 | 1,623 | 2026-03-03T02:14:47 | 2026-04-30T01:54:55 | 0.97 |
| playup | 388,266 | 194,931 | 2,963 | 1,511 | 2026-03-03T02:27:28 | 2026-04-30T01:54:55 | 0.99 |
| sportsbet | 281,567 | 211,821 | 2,673 | 1,989 | **2026-03-21T00:08:13** | 2026-04-30T01:55:32 | 1.03 |
| tabtouch | 215,050 | 209,873 | 1,800 | 1,766 | **2026-03-30T01:29:56** | 2026-04-30T01:54:55 | 1.04 |

`30d-rate / lifetime-rate` is `(snaps_30d / 30) / (snaps_total / lifetime_days)` — values near 1.0 indicate steady-state production; values < 1 indicate the 30d rate is below the lifetime average. **pointsbet at 0.77 is the lone deviation** — its 30-day production rate is 23% below its lifetime average. Possible mechanisms (operator's call): scrape volume was higher in the early weeks and tapered, or pointsbet has degraded in the last 30 days, or the formula is sensitive to the timing of scrape events. Other scrapers cluster 0.97–1.04 (near steady state).

Scrapers that the brief named as expected per `data_layer_current.md` §5.1 ("Entain (Ladbrokes/Neds), PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API") are all present. `palmerbet_race_id` exists in the `races` schema but `bookmaker_snapshots` has zero rows with `bookmaker = 'palmerbet'` — consistent with PalmerBet being Cloudflare-blocked and out-of-scope per `data_layer_current.md` §5.1. No scrapers exist in the data that aren't named in the documentation.

### G.2 Cadence per scraper (AU thoroughbred 30d, two pre-jump windows)

| Scraper | Window | n gaps | p50 (s) | p95 (s) | p99 (s) | max (s) | Pct gaps > 2× documented (300s/120s) |
| :-- | :-- | --: | --: | --: | --: | --: | --: |
| ladbrokes | pre-30 outside 5min | 61,417 | 347.6 | 752.5 | 992.9 | 2,245 | 13.5% |
| ladbrokes | pre-5 intensive | 26,953 | 150.1 | 600.4 | 819.9 | 2,283 | 26.7% |
| neds | pre-30 outside 5min | 60,355 | 348.4 | 772.2 | 1,211.6 | 2,245 | 14.6% |
| neds | pre-5 intensive | 26,491 | 150.9 | 638.9 | 846.3 | 2,283 | 27.2% |
| playup | pre-30 outside 5min | 52,222 | 342.4 | 694.3 | 805.8 | 1,146 | 8.0% |
| playup | pre-5 intensive | 23,413 | 142.2 | 492.6 | 756.4 | 977 | 24.5% |
| pointsbet | pre-30 outside 5min | 64,402 | 344.7 | 726.3 | 826.2 | 1,146 | 11.3% |
| pointsbet | pre-5 intensive | 28,201 | 148.1 | 565.9 | 782.8 | 977 | 25.9% |
| sportsbet | pre-30 outside 5min | 72,731 | 345.5 | 744.4 | 842.6 | 1,636 | 13.8% |
| sportsbet | pre-5 intensive | 32,870 | 140.7 | 613.8 | 797.9 | 977 | 25.4% |
| tabtouch | pre-30 outside 5min | 58,482 | 348.4 | 758.9 | 1,005.1 | 2,216 | 13.8% |
| tabtouch | pre-5 intensive | 25,519 | 150.9 | 607.4 | 833.5 | 1,629 | 27.0% |
| unibet | pre-30 outside 5min | 63,613 | 344.6 | 728.0 | 826.7 | 1,146 | 11.4% |
| unibet | pre-5 intensive | 27,892 | 148.1 | 568.4 | 784.3 | 977 | 26.0% |

All seven scrapers cluster tightly around the same cadence shape: standard p50 ≈ 345s (vs documented 5 min = 300s — 15% looser at median), intensive p50 ≈ 140–151s (vs documented 90–120s — at the upper end of documented range or slightly past it). Pre-5 intensive gap-rate (>2× documented = >240s) is uniform across scrapers at 24–27%.

### G.3 Cross-scraper coverage at races (30d, races covered by N scrapers in pre-30min window)

| Code | Total races | 0 scrapers | 1 | 2 | 3 | 4 | 5 | 6 | 7+ |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| AU thoroughbred | 3,194 | 1,024 (32.1%) | 708 (22.2%) | 7 | 73 | 34 | 92 | 450 (14.1%) | 806 (25.2%) |
| AU harness (heur) | 724 | 716 (98.9%) | 0 | 0 | 0 | 0 | 0 | 8 | 0 |
| AU greyhound (heur) | 12,517 | 12,397 (99.0%) | 3 | 20 | 8 | 2 | 2 | 85 | 0 |
| NZ | 273 | 69 (25.3%) | 2 | 7 | 7 | 0 | 188 (68.9%) | 0 | 0 |
| Foreign | 180 | 68 (37.8%) | 2 | 21 | 89 (49.4%) | 0 | 0 | 0 | 0 |

Two structural facts:

- AU thoroughbred is bimodal: 25.2% of races are covered by all 7 scrapers, 32.1% are covered by none. The middle (1-6 scrapers) accounts for the remaining 42.7% with no clean cadence shape — likely reflects per-scraper venue coverage gaps.
- **AU harness and AU greyhound have 99% zero-coverage** for soft-book scrapers in the pre-30min window. The DR-014 hot-path use case (in-burst soft-book price comparison) does not have soft-book data for harness or greyhound at decision time as the data stands.
- NZ has a curious cluster at exactly 5-scraper coverage (69%). Some scrapers cover NZ (likely the international-friendly ones); operator's call which.

### Anomalies in §G

- pointsbet 30d-rate / lifetime-rate at 0.77 — material degradation versus all other scrapers at 0.97-1.04. Could be statistical artifact or real drift.
- 99% zero-coverage for harness/greyhound by soft-book scrapers — DR-014's hot-path multi-book context essentially does not exist for these codes.
- Maximum inter-snapshot gaps are large (up to 2,245s = 37 min) — more than 7× the documented standard cadence in extreme cases.

---

## §H — Cross-section anomalies and surprises

Free-form section. The following surfaced during the inspection and are worth naming. Up to four non-source-survey items per the brief; source-exposes-but-schema-stores-but-pipeline-doesn't-write observations are appended.

**H.1 The two-population structural finding: `finish_position` and `betfair_selection_id` are mutually exclusive across the entire database.** Zero runners across all 421,651 rows carry both `finish_position` AND `betfair_selection_id` populated (§C.2). The two come from disjoint ingestion paths separated at the live-capture-start floor (~60 days before the inspection). Pre-floor: Racing API subscription writes `finish_position` but does not write `betfair_selection_id`. Post-floor: Betfair Streaming live capture writes `betfair_selection_id` but the result-population pathway does not run. v3's analytical path (vps_client / `bf_snapshot` join with race result) requires both, and currently has zero overlap available. This is the load-bearing observation in this report.

**H.2 The 60-day hard break around the live-capture-start floor.** Live capture began 2026-03-02; `betfair_historical` import runs through 2026-02-28; the gap is 2 days but the consequence is wider. Everything that was previously sourced via the historical CSV (BSP, `actual_off_time`, win/place results, traded-volume metrics) is missing for the entire live-capture window. Everything that depends on live capture (Betfair `selection_id`, time-series snapshots, soft-book snapshots) is absent before the floor. The two halves of the database are joined only by `race_id` and don't overlap on substantive fields.

**H.3 Code-coverage asymmetry across capture pathways.** AU thoroughbred is the well-covered code on most fields (race metadata, runner form, results in CSV window). AU harness and AU greyhound have very low coverage on race_class / distance_metres / jockey / trainer / form / scratching-with-timestamp under the AU-thoroughbred frame, but have 100% scratched_at population (vs thoroughbred 15%) — a different scratching-source pipeline. NZ races (464) are present and have 100% jockey / trainer / weight / barrier / scratched_at but 0% finish_position / Betfair coverage. Foreign races (335) are similar. These coverage shapes are structural — different feeds per code, with the merging logic underspecified in `data_layer_current.md` §§4–5.

**H.4 `daily_calibration_summary` is producing winners daily but `runners.finish_position` is not being written.** The calibration job (n_winners daily with brier scores) clearly has a result-resolution path that runs and works in the live-capture window (Apr 28 brier 0.0729, 110 winners from 990 runners, n_sources_active = 8). That path does not write back to `runners.finish_position`. Two consequence patterns: (a) v3's planned `vps_client.get_race_result(event_id)` would not find results in `runners` even though the calibration pipeline knows them; (b) the calibration job is itself a known-good upstream source the auto-settlement path could consume directly, bypassing the broken `runners.finish_position` write-back.

### Source-exposes-but-schema-stores-but-pipeline-doesn't-write observations

These were apparent during schema discovery; observation only, no probing of upstream sources. Per brief's hard limit, no API documentation was read.

- `betfair_snapshots.bsp_price`, `sp_near_price`, `sp_far_price` columns: 0 rows populated across 1,629,309 snapshots. The schema accommodates Betfair's BSP / SP-near / SP-far data fields (which the Streaming API exposes near jump and post-jump), but the live capture pipeline writes nothing. This is the cleanest source-exposes-but-pipeline-doesn't-write case in the inspection.
- `betfair_historical` carries `win_ipwap` / `win_ipmax` / `win_ipmin` / `win_ip_traded_vol` (in-play volume metrics) and `best_back_at_off` / `best_lay_at_off` / `overround_at_off` (at-off market state) and `match_method` / `match_confidence` (the import's runner-matching diagnostics). These are present in the historical CSV import but no equivalent live-capture-time columns exist on `betfair_snapshots`. The schema asymmetry between historical and live capture is itself worth naming.

(Per brief, the systematic Betfair / Racing API field-inventory survey is §2.10 of the wider scope and is not pursued here.)

---

*End of report.*
