# DR-029 §2.1 follow-up — VPS analytical pipeline source-code review report

**Review date:** 2026-04-30 13:30 ACST.
**Source tree:** `/home/racing/racing-data-capture/` on `root@187.77.183.9`. Read-only file access via SSH; capture.db queries via `sqlite3 'file:.../capture.db?mode=ro'` only where needed to ground a code-reading observation.
**Brief discipline held:** read-only, observation-only, no remediation. Effort scale per brief §6 (trivial / small / medium / large / structural-rework). Risk-to-fix qualitative.
**Pre-reads done:** `source_review_brief.md`, `inspection_report.md` (full), `brief.md`, `dr029_scope.md` §1.2 + §2.1, `work_in_progress.md` open-questions section.

---

## §5.1 Calibration job's result-resolution wiring

### What was found

**The calibration job has two mutually-exclusive resolution sources.** `scripts/daily_calibration_summary.py:53-101` (`gather_runner_data`) executes two SELECTs in sequence, deduplicating by `race_id`:

- **Source 1 (live):** `betfair_snapshots` JOIN `races` JOIN `runners` filtered to `r.capture_status='SETTLED'` AND `bs.is_final_snapshot=1`. Reads `ru.result_status` and `ru.finish_position`. Determines `is_winner` by `(result_status == "WINNER") OR (finish_pos == 1)` (line 87).
- **Source 2 (CSV historical):** `betfair_historical` JOIN `runners` JOIN `races`. Reads `bh.win_result` and `ru.finish_position`. Source 2 only fires for races not covered by Source 1.

**The live-window winner-resolution path runs entirely off `runners.result_status`, not `finish_position`.** Source 1 evaluates `is_winner` from the OR clause; in the live-capture window `finish_position` is 0% (per inspection §C.1) but `result_status` IS being populated. Verified empirically against `capture.db` for 2026-04-20→2026-04-29: `result_status` distribution is WINNER=1286, LOSER=10597, REMOVED=1321, NULL=4439; `capture_status` is SETTLED=1310, PENDING=4334, TIMEOUT=34. The 1286 WINNERs are what `daily_calibration_summary.n_winners` sums to in §F.3.

**`result_status` is written by the orchestrator's settlement path, not by the Racing API path.** `capture/orchestrator.py:865-914` (`_check_settlement`) polls `client.get_market_results(market_id)` which returns `{selection_id: WINNER/LOSER/REMOVED}` from Betfair's settled market book, then calls `update_runner_result()` (in `storage/database.py:404-426`) passing `result_status` and `results_source='betfair_only'` **but NO `finish_position`**. Betfair's settled market book returns runner statuses, not race-rank — so this path can write WINNER but cannot supply finish positions 2/3/4/etc.

**The `finish_position` write path is `subscription/racing_api.py:_sync_single_runner` (lines 261-310).** It parses `runner.position` from The Racing API response, sets `finish_position`, and conditionally sets `result_status` to "WINNER" (pos=1), "LOSER" (other), or "REMOVED" (pos=109). This path is invoked only via `sync_day()`, called by:
1. `scripts/backfill_subscription.py` — bulk `--from / --to / --days` runner; manual one-off.
2. `scripts/backfill_race_metadata.py --days 1` — wired to `racing-metadata-backfill.service` daily at 23:30 Adelaide.

**Per-race matching for `sync_day` to merge into existing race rows.** `subscription/racing_api.py:209-223` calls `upsert_race(...)` keyed on `(race_date, venue_normalised, race_number)` with `venue_normalised = normalise_venue(course)`. `normalise_venue` lives in `matching/race_matcher.py:60-79` and applies the same alias table used during live discovery. **For runner-key matching** (`storage/database.py:218-227`, `compute_runner_key`) the rule is `"N:<runner_number>"` if a number is present, else `"S:<runner_name_normalised>"`. So a Racing-API runner with `runner.number=5` and a Betfair-discovered runner with `number=5` from `_ensure_betfair_runner` both produce key `"N:5"` and merge by upsert into the same row — `finish_position` would land on the same `runners.id` that already carries `betfair_selection_id`. The merge logic in `upsert_runner` (`database.py:330-352`) uses `COALESCE(excluded.X, X)` — non-null new value overwrites NULL existing, NULL new value preserves existing. Match should compose cleanly.

**Why the inspection observes 0% `finish_position` overlap is a path-not-taken issue, not a join-key collision.** Per Session 33 pre-flight, `racing-metadata-backfill.service` has been failing nightly since 2026-04-29 14:00 UTC (PermissionError on `logs/metadata_backfill.log`) — confirmed: see §"Anything surprising" below. But that's only ~14h. The 30-day 0% rate is a deeper failure: the service uses `--days 1`, so the 1-day-back call only enriches yesterday's races, never sweeping the 7-30-day backlog. Even if the service were running cleanly, `--days 1` would never converge for a race that doesn't have its Racing-API enrichment land on D+1; subsequent days don't retry. The `get_unsynced_dates()` helper (lines 56-66) DOES exist as the alternative path that finds all `subscription_synced_at IS NULL` dates — but the systemd unit hardcodes `--days 1`. Result: the daily service never catches up after a miss.

**Idempotency.** The calibration job is `INSERT OR REPLACE` keyed on `date` PRIMARY KEY (lines 188-208) — fully idempotent per-date. The Racing API path is upsert-with-COALESCE on `(race_date, venue_normalised, race_number)` and `(race_id, runner_key)` — also idempotent in the no-conflict path. Backfilling via `backfill_subscription.py --from 2026-03-02 --to 2026-04-29` would be a single bulk run with rate limiting (default 2.0s sleep between days) — observable, single-pass, and would write `finish_position` via the existing path with no new code.

**Other resolution paths in the codebase.** `storage/database.py` exposes `update_runner_result()` taking `finish_position` as a kwarg, but the only caller is the orchestrator's `_check_settlement` which never passes it. No other code attempts a `runners.finish_position` write. `subscription/racing_api.py:refine_placed_status()` (lines 343-388) computes PLACED status post-sync but reads, never writes, `finish_position`. `betfair_historical` is populated separately by `scripts/import_betfair_historical.py` (1,089 LOC, not read in detail) and joins to `runners` via runner_id from CSV-import-time matching.

### Effort to fix
**Small** for the read-only-canonical-source surgical fix. Three executables exist:

1. *Wire calibration's existing query path to write back* — modify `gather_runner_data` to UPDATE `runners.finish_position = 1` for is_winner rows. Trivial extension to existing query; one extra UPDATE per Source 2 row; idempotent. Does not give 2nd/3rd/4th places.
2. *Use `daily_calibration_summary` as canonical settlement-result source via `vps_client`* — no VPS-side change. Smallest change of all; bypasses `runners.finish_position` entirely.
3. *Backfill `subscription/racing_api.sync_day` over the 60-day live-capture window* — single bulk run via `backfill_subscription.py --from 2026-03-02`. Existing code; produces full positions and margins; ~60 days × 2s = 2 minutes of API calls per day per delay setting.

The *medium* path is also available: rework `racing-metadata-backfill.service` to call `get_unsynced_dates()` instead of `--days 1`, so the daily service backfills correctly. That fixes the failure mode (always running, never catching up) at the source.

### Risk to fix
**Low for path 2 (vps_client read-side adapter — no VPS write).** **Low-medium for path 3 (existing-code bulk backfill — Racing API rate limit is the only meaningful failure surface; idempotent so a partial run is safe to resume).** **Medium for path 1 (one-line addition in calibration job — but the calibration job's `is_winner` resolution is itself running on `result_status`, so a write-back would cement an incomplete winner-only signal as the canonical position).** No dual-running needed for paths 2-3; both compose with existing pipeline behaviour.

### What depends on it
This is the load-bearing finding. §5.3 (BSP write-back) is independent. §5.2 (intensive-cadence) is independent. §5.5's "wiring fix vs structural" verdict is anchored on §5.1.

---

## §5.2 Betfair scrape's intensive-mode trigger and market-discovery logic

### What was found

**Discovery cadence is 30 minutes flat** (`config/settings.py:7`, `DISCOVERY_INTERVAL=1800`). `capture/orchestrator.py:197-278` `_maybe_discover` runs `list_au_win_markets(now, now+12h)` and `list_au_place_markets(now, now+12h)`. The 12h forward window is wide; the discovery cadence is the constraint.

**Race-entry to CAPTURING is gated through `_register_race` (orchestrator.py:297-362) which silently returns if `scheduled_start` is missing.** Line 306-307: `if not scheduled_start: return`. This is the first plausible silent-drop path — any race emerging from `match_races` with no `_start_epoch` (no bookmaker contributed `start_epoch` AND no Betfair `start_time`) will not register, will never enter CAPTURING, will produce no snapshots. The `_register_race` function is also invoked only from inside `_maybe_discover`, so a race that was discovered but failed registration is not retried in the next discovery cycle — the in-memory `self._races` dict is the only registry.

**Phase machine cleanly defined** (`capture/scheduler.py:107-129`, `current_phase`): `mts > STANDARD_CAPTURE_WINDOW` → PENDING; `0 < mts <= INTENSIVE_WINDOW` → INTENSIVE; `INTENSIVE_WINDOW < mts <= STANDARD_CAPTURE_WINDOW` → STANDARD; `mts <= 0` → POST_START. With `STANDARD_CAPTURE_WINDOW=60`, `INTENSIVE_WINDOW=5`, the math is right.

**Most plausible root cause of the 56% no-pre-30min finding: discovery-cadence-too-coarse compounded by race-creation lag.** A race must be (a) in Betfair's catalogue with a `start_time` field set, (b) discovered by the orchestrator at the next ≤30-min cycle, (c) registered with `scheduled_start` populated, and (d) inside the `mts <= 60` STANDARD-capture window when its first per-race tick fires. Failure modes:

- **Late catalogue creation.** If Betfair adds the WIN market <30 min before jump (rare for normal races; common for late-added races, scratched-then-restored, jurisdiction edge cases), the next discovery may not run until <30 min before jump, by which point the pre-30min snapshot window is closed.
- **`scheduled_start` missing.** Bookmaker discoveries supply `start_epoch` from each platform's API; Betfair-only races take `snap.start_time.isoformat()` at `race_matcher.py:307`. If both are NULL the race silently drops at `_register_race`.
- **Filter on `event_type_ids=["7"]` + `market_countries=["AU"]`** (`betfair/client.py:103-128`). Confirmed AU-only and horse-racing-only — already known structural fact, not a candidate explanation for the AU-thoroughbred-only 56% gap.

**The 90-97s intensive p50 (vs documented 60s) is most plausibly a tick-granularity ceiling.** Three compounding factors visible in code:
- `MAIN_LOOP_TICK=30` (settings.py:6). The orchestrator only checks `should_take_betfair_snapshot` on each 30s tick, so after a 60s interval elapses, the next Betfair snapshot fires on the next tick — average extra wait ~15s, worst-case 30s. Effective cadence is ~75-90s mean.
- **Per-race serialised processing.** `_process_all_races` (orchestrator.py:392-418) loops over all tracked races and processes each one inline; a slow Betfair API call to one race delays all subsequent races' tick. With ~10-20 active races at peak and 1-3s per Betfair call, an additional 5-15s of slip per cycle is plausible.
- **Per-source serialised polling within `_take_bookie_snapshots`** (lines 689-776). Bookmakers are processed one at a time with `BOOKIE_STAGGER_MIN=2.0, MAX=5.0` (settings.py:31-32) sleep between each. Six active bookmakers × ~3.5s mean stagger = ~21s of sleep per race per cycle. This affects bookmaker cadence directly but also blocks the main loop tick from processing the next race quickly.

**Together these explain the 90-97s p50 cleanly without needing a separate diagnostic.** The 38% gap-rate at >120s is likely the tail of cycles where the bookmaker stagger plus a Betfair API slow-response stack on each other.

**Discovery is rerun for new-race-discovery only — no per-race Betfair re-fetch via `_maybe_discover`.** Once a race is in `self._races`, `_maybe_discover` calls `_update_race_ids` (lines 364-386) which only patches missing IDs. Per-race Betfair price polling is `_take_betfair_snapshot` driven by per-race phase/cadence, not by discovery. Smallest gap between Betfair-catalogue creation and orchestrator pickup is bounded above by `DISCOVERY_INTERVAL=1800s` = 30 min, plus the ~30s tick.

**Race-type / venue-type filters that systematically exclude.** None visible at the Betfair side beyond the AU-horse-racing filter. `is_trial=1` and `is_jump_out=1` flags are set by `subscription/racing_api.py` based on Racing API's `is_trial`/`is_jump_out` booleans but aren't used to gate Betfair capture. So trials and jump-outs that have a Betfair WIN market are captured the same as other races.

### Effort to fix
- *56% no-pre-30min*: **medium** to drop `DISCOVERY_INTERVAL` to e.g. 600s (10 min) — single constant change, but it raises Betfair API call volume 3×; rate-limit headroom is unknown from code. **Small** for the alternate fix of running an additional "fast-discovery" sweep when scheduled_start is within the next hour. **Trivial** for adding logging at `_register_race`'s silent-drop branch so the dropped-race rate becomes observable.
- *Intensive p50 90-97s slip*: **medium-large** for the structural fix (decouple per-race processing from main-loop tick — async or thread pool). **Small** for tightening `MAIN_LOOP_TICK` to 15s, but that doesn't fix the per-race serialisation; just the granularity ceiling.

### Risk to fix
**Medium.** Discovery-cadence and tick-granularity changes are load-bearing on a running system. A faster discovery interval risks Betfair rate limits (1 in N market_catalogue calls returns rate-limit error per `_handle_api_error`). Async/thread-pool rework of `_process_all_races` is large enough to merit dual-running; SQLite WAL allows it on a separate DB but the orchestrator owns the in-memory `_races` dict, which would need locking discipline.

### What depends on it
§5.5's overall read on whether the orchestrator can be evolved within its current shape rests partly on whether the cadence fixes need a structural rewrite or just config changes. The 56% finding root cause's small-vs-medium effort scale is the calibration question.

---

## §5.3 Snapshot writer for BSP / sp_near / sp_far

### What was found

**`bsp_price` is never written by any code path.** `betfair/models.py:42-58` defines `RunnerData` with fields `sp_near_price` and `sp_far_price`, but **no `bsp_price` field**. `betfair/client.py:_book_to_snapshot` (lines 264-340) reads `r.sp.near_price` and `r.sp.far_price` but never reads any equivalent for actual BSP. `capture/orchestrator.py:537-566` builds the snapshot row tuple with positions 19/20 = `runner.sp_near_price` / `runner.sp_far_price` and **no slot for `bsp_price`** — the column-positional INSERT in `save_betfair_snapshots_batch` (`storage/database.py:467-498`) accepts 21 values; column 19 is `bsp_price` per the SCHEMA (line 137); but the orchestrator's tuple at line 547-565 only writes 21 values where the 19th is `last_match_time`, the 20th is `matched_amount`, the 21st is `sp_near_price`... let me re-read carefully.

Re-checking column order in `save_betfair_snapshots_batch` INSERT statement (`database.py:471-481`): `(race_id, runner_id, snapshot_time, minutes_to_start, best_back_price, best_back_size, best_lay_price, best_lay_size, total_matched, market_status, runner_status, num_priced_runners, snapshot_phase, is_final_snapshot, back_depth_json, lay_depth_json, last_match_time, matched_amount, sp_near_price, sp_far_price, snapshot_batch_id)` — that's 21 columns; **`bsp_price` is not in the INSERT column list**. Therefore the INSERT never writes `bsp_price`. The schema (database.py:137) does declare `bsp_price REAL`, but only as an unused column. Inspection's 0.000% population is the necessary consequence of the column being orphan.

**`sp_near_price` and `sp_far_price` ARE wired through but the projection is wrong for pre-jump.** `betfair/client.py:228-234` (`get_market_book`) requests `price_projection=price_projection(price_data=["EX_ALL_OFFERS", "SP_TRADED"])`. Per Betfair's API: `SP_TRADED` returns SP traded prices that exist only **after** the market suspends and SP is reconciled. Pre-jump, `r.sp.near_price` and `r.sp.far_price` (which are the *projection* fields, not traded fields) are populated by the `SP_AVAILABLE` projection — which is not requested. So the code reads the right fields but Betfair returns nothing in them because the wrong projection was requested.

**Post-suspension settlement path doesn't fetch prices.** `_check_settlement` (orchestrator.py:865-914) calls `client.get_market_results(market_id)` which delegates to `betfair/client.py:_get_market_results` (lines 158-180) — `list_market_book(market_ids=[market_id])` **with no `price_projection`**. Betfair's default projection without `price_data` returns minimal info — runner statuses, market status. No SP, no BSP. So even after market closes, no SP fetch happens.

**The orchestrator stops snapshotting entirely once the market leaves OPEN.** `_take_betfair_snapshot` (orchestrator.py:502-517) detects `market_status != OPEN` and immediately calls `state.enter_settlement()` and `flag_final_betfair_snapshot()`. The remaining capture loop only runs settlement-status polling. There's no code path that fetches the `book.runners[*].sp.actual_sp` projection (the actual realised BSP) at any point post-suspension.

**For BSP specifically.** Betfair publishes BSP when the market suspends (jump). To capture BSP one would need: (a) request `price_projection=["SP_AVAILABLE"]` pre-jump for SP projections, (b) request `price_projection=["SP_TRADED"]` post-suspension for actual BSP and reconciled SP, (c) wire a post-suspension price fetch into `_check_settlement` or run a one-shot fetch when market transitions OPEN→SUSPENDED→CLOSED, and (d) extend `RunnerData` with a `bsp_price` field carried into the writer.

### Effort to fix
**Small.** Two changes in `betfair/client.py`: add `SP_AVAILABLE` to pre-jump price_data (or use it in place of `SP_TRADED` until suspension), and add a post-suspension fetch with `SP_TRADED` projection. One change in `betfair/models.py` to add `bsp_price`. One change in `capture/orchestrator.py:_take_betfair_snapshot` rows tuple. One change in `storage/database.py` INSERT column list. Schema's `bsp_price` column already exists; no DDL needed.

### Risk to fix
**Low.** Three new field-writes are additive — they don't change existing behaviour. The post-suspension fetch is a new code path that doesn't intersect existing settlement detection. Test coverage observation: there are no tests anywhere in the project tree (`find /home/racing/racing-data-capture -name "test_*.py"` returns only third-party venv hits). A change like this would land without a regression test. Worth considering as part of the fix but observation only.

### What depends on it
Independent of §5.1, §5.2. §5.5 weighs the cumulative shape.

---

## §5.4 Soft-book scrapers' shape

### What was found

**All seven active scrapers conform to the `bookmakers/base.py` contract.** `(BookmakerMeta, list[BookmakerRunner])` return tuple, `discover_<name>` returns `dict[str, dict]` keyed on normalised venue. The `discover` and `fetch` functions all accept `proxies: dict | None`. Module-level dispatch tables in `capture/orchestrator.py:78-88` and `_fetch_bookmaker:778-816` handle per-scraper invocation differences (e.g., TAB needs `(date, venue_code, race_num)`, others take `race_id_str`).

**Structural deviations — observation rather than judgement.** Per-scraper invocation signature differences (TAB and Palmerbet split path components; others pass an opaque race-id string) are handled at the orchestrator's dispatch site, not at the contract boundary. Adding an eighth scraper requires: a new module under `bookmakers/`, a new entry in `BOOKMAKER_KEYS`/`BOOKMAKER_LABELS`/`BOOKMAKER_DB_NAMES` (`base.py:38-58`), a new entry in `DISCOVER_FUNCTIONS` (orchestrator.py:78-88), a new branch in `_fetch_bookmaker`, a new `<name>_race_id` column on the `races` table plus an entry in `_register_race`'s `bk_id_fields` map. **Six touchpoints across four files for a new scraper.** Not zero-friction but not structural either.

**Scrapers are well-isolated.** Each module imports only from `bookmakers.base`, `matching.race_matcher` (for `normalise_venue`), `config.settings` (for `USER_AGENT_POOL`). No shared mutable state; orchestrator's circuit-breaker dict is keyed per-scraper. Removing one scraper would require touching the same six points but no other scraper's code. Module size is bounded (largest is entain at 357 LOC).

**Harness/greyhound 99% non-coverage is structural — every active scraper hard-codes thoroughbred filtering.** Confirmed:
- `bookmakers/entain.py:140-147` (`_is_horse_meeting`): `category_id == ENTAIN_HORSE_CATEGORY` (hardcoded UUID) AND rejects feed_id containing "greyhound" or "harness".
- `bookmakers/playup.py:22, 171-172`: `PLAYUP_GALLOP_TYPE_ID = 1` filter on `race_type.id`.
- `bookmakers/pointsbet.py:23, 131`: `PB_HORSE_RACING_TYPE = 1` filter on `meeting.racingType`.
- `bookmakers/sportsbet.py` (the Racing-API-based scraper): docstring "Coverage: thoroughbred AU only (no greyhounds, no harness, no NZ)" and Racing API's `/australia` endpoints are thoroughbred-only.
- `bookmakers/tab.py:150`: `if meeting.get("raceType") != "R": continue` (R = thoroughbred).
- `bookmakers/tabtouch.py`: HTML-scrapes the racing pages; URL pattern `/racing/{date}/{venue_code}/{race_num}` discovers via `/racing/races` index — thoroughbred-only by upstream filter on TABtouch's racing index.
- `bookmakers/unibet.py:254`: `"raceTypes": ["T"]` (T = thoroughbred) in the GraphQL discover variables.
- `bookmakers/palmerbet.py:47, 83, 156`: URL hardcoded `/HorseRacing/`. (Palmerbet currently disabled per `DISABLED_BOOKMAKERS={"tab","palm"}` in `config/settings.py:36`.)

**Extending to harness/greyhound** would require seven independent scraper changes, each platform exposing those codes via different endpoints (Entain has greyhound feeds, PlayUp has separate `race_type.id`, PointsBet has different `racingType`, Unibet has `raceTypes=["G"]` or `["H"]`, etc.). The structural cost is per-platform investigation and per-platform code, not a single-file lift.

**PointsBet 0.77 deviation — code-side diagnosis.** `bookmakers/pointsbet.py:34-62` is a straight `requests.get` to `api.au.pointsbet.com/api/racing/v3/races/{race_id}`. No retry, no backoff, no special handling. **PointsBet bypasses the Decodo proxy** (`config/settings.py:43`, `PROXY_BYPASS_BOOKMAKERS = {"pb", "uni", "play", "sb"}`). Routing is `proxies=None` always. No code-visible reason for the 23% drop in 30d-rate vs lifetime-rate. Possibilities the code does NOT rule out: PointsBet API response structure changed and `runners` array is parsed but missing some races; the discover endpoint `/v4/meetings` is filtering races more aggressively (the `country and country not in ("AUS", "NZL")` and `region != 2` checks at lines 138-142 would silently drop races that lose their `country` field on the upstream side); some races' `markets` list lost the `FixedWin` / `FixedPlc` types and now produce empty price maps. None of these can be confirmed from source-only inspection.

**`capture/proxy.py` is doing what its name suggests.** Builds a Decodo proxy URL from `DECODO_USERNAME` / `DECODO_PASSWORD` / `DECODO_ENDPOINT` / `DECODO_PORT` env vars (`proxy.py:24-58`). Returns `None` if disabled or credentials missing — orchestrator's `_get_proxies` (orchestrator.py:920-926) catches exceptions and returns None silently. Routing rules are cleanly stated in proxy.py docstring: bookmaker requests through Decodo, Betfair API direct, Racing API direct. Operationalised via `PROXY_BYPASS_BOOKMAKERS` for bookmakers with direct-routes-better characteristics (PointsBet, Unibet, PlayUp, sportsbet — sportsbet bypasses because it IS the Racing API path).

### Effort to fix
- *Add an 8th scraper*: **small** — six touchpoints across four files, no structural lifting.
- *Extend harness/greyhound coverage to existing scrapers*: **medium-to-large** — seven independent scraper revisions, each requiring upstream-platform investigation. Every platform has its own race-type taxonomy.
- *PointsBet 0.77 diagnosis*: cannot be diagnosed from source alone. Requires runtime probing of PointsBet's discover and fetch responses or comparing recent/historical capture logs. **Trivial** to add per-call diagnostic logging that would surface root cause in 1-2 days of running.

### Risk to fix
**Low for new-scraper add. Medium for harness/greyhound — adds 7× the scraping surface; rate-limit and circuit-breaker tuning would need extending.** No risk to existing pipeline behaviour from a PointsBet diagnostic-logging addition.

### What depends on it
§5.5's overall-shape read leans on "scrapers are tidy modules" being true. Confirmed.

---

## §5.5 Supervision config and code-health overall

### What was found

**Schema-management is ad-hoc.** Schema lives as a Python string constant `SCHEMA` in `storage/database.py:18-200`. `init_db` (lines 211-220) runs `executescript(SCHEMA)` on every collector start — relies on `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` to be idempotent. **Three migration scripts** (`scripts/migrate_*.py`):
- `migrate_depth_and_batch.py` (117 LOC): adds `back_depth_json`, `lay_depth_json`, `last_match_time`, `matched_amount`, `sp_near_price`, `sp_far_price`, `snapshot_batch_id` to `betfair_snapshots`; adds `snapshot_batch_id` to `bookmaker_snapshots`; creates `snapshot_batch_summary`.
- `migrate_race_metadata.py` (45 LOC): adds `race_group`, `track_type` to `races`.
- `migrate_s_to_n_runners.py` (149 LOC): one-shot data migration to fix S:-keyed runner rows created by Betfair number-prefixed names; merges them into N:-keyed rows.

**No `schema_version` table; no migration framework; no version tracking in code.** Migrations are detected-by-existence-check (`PRAGMA table_info` followed by ALTER TABLE conditional). The `SCHEMA` constant in `storage/database.py` already includes the fields each migration adds — so a fresh DB created by `init_db` produces the post-migration schema directly, and migrations are only relevant for existing DBs that pre-date the change. Pattern is internally consistent but discoverable only by reading the migrations.

**Code-cleanliness — middle of the road.** `capture/orchestrator.py` is 961 LOC and is genuinely several concerns interleaved — Betfair discovery, bookmaker discovery, race matching call-site, per-race phase processing, Betfair snapshotting, bookmaker snapshotting, settlement detection, runner-id resolution. Six method clusters with light coupling but shared state via `RaceState`. The docstring claim ("single main loop coordinating ... matching, settlement detection, coverage tracking") matches structurally — but the file is the orchestration layer in name and in fact, with no internal sub-module split. `subscription/racing_api.py` (466 LOC) is parser + sync logic in one file. `storage/database.py` (719 LOC) is schema + init + ~15 CRUD helpers; cleaner. Bookmaker scrapers (`bookmakers/*`) are 179-357 LOC each, single-responsibility. The pipeline is "monolithic orchestrator + clean per-source scrapers + thin storage layer" — not a monolith but the orchestrator carries the load.

**Test coverage: zero.** No `tests/` directory. No `test_*.py` or `*_test.py` files in the project tree (only third-party hits inside `venv/`). Pipeline is tested via observed live behaviour — and via `scripts/health_check.py` (766 LOC) and `scripts/liveness_check.py` (265 LOC) which monitor outputs rather than test code paths.

**Logging discipline: stdlib `logging` with freeform `%s`-style messages.** No structured (JSON, key=value) logging. Per-module loggers via `logger = logging.getLogger(__name__)` — centralised aggregation through root logger configured in `scripts/run_collector.py:37-71` (rotating file handler at `logs/collector.log`, 10MB × 5 backups). The metadata-backfill PermissionError (see "Anything surprising") is a path-permission issue, not a logging-fragility class.

**`scripts/health_check.py` (766 LOC) is monitoring + email + scrape-status decision logic.** SOURCES dict at lines 35-90 has 7 active sources (with `tabtouch` accidentally listed twice — second entry overwrites the first; harmless). Sportsbet, TAB, and Palmerbet are commented out as "Disabled until fixed" — but **sportsbet is currently operational** (confirmed by inspection §G.1: 281,567 snaps, 1,989 races last 30d). So `health_check.py`'s SOURCES inventory is stale relative to the running pipeline. The 766-LOC size is mostly per-source decision logic, HTML email templating, and CLI argument handling — not unreasonable for what it does, but it's a fair-sized concern parked in the scripts dir.

**`scripts/liveness_check.py` (265 LOC) is a concise "is the pipeline alive" check** every 15 minutes — runs `pgrep` for the collector PID, checks `betfair_snapshots` freshness within 240 minutes, hits the local `127.0.0.1:8400/health` endpoint. Sends email on failure with 30-min cooldown. Cleanly scoped.

**`run_collector.py` (120 LOC)** is a clean entry point: setup_logging → init_db → Betfair login → orchestrator.run(). Standard daemon shape.

**Supervision wiring** (per Session 33 pre-flight, confirmed):
- `racing-capture.service` — `Type=simple`, `Restart=on-failure`, `RestartSec=30`, runs as `User=racing`. Started by `racing-collector-start.timer` daily at 08:30 Adelaide. Stops itself via `_should_stop()` in orchestrator after `STOP_HOUR_LOCAL=19` (7 PM Adelaide) once no active races remain.
- `racing-calibration.service` — `Type=oneshot`, runs `daily_calibration_summary.py`. Daily 23:00 Adelaide.
- `racing-metadata-backfill.service` — `Type=oneshot`, runs `backfill_race_metadata.py --days 1`. Daily 23:30 Adelaide. **Currently failing** — see below.
- `racing-api.service` — long-running uvicorn for read API at `127.0.0.1:8400`.
- `racing-liveness.service` — every 15 min.
- `racing-health-check.service` — daily 06:00 Adelaide.
- `racing-backup.service` — daily 05:00 Adelaide.

**Schema management via the `SCHEMA` constant means the DB schema is "what the running code expects."** Drop or re-create the DB from a stale code checkout and the schema reverts to that checkout's state. No version-floor enforcement.

### Effort to fix (overall framing)
- *Surgical fixes against existing infrastructure for §5.1, §5.3, §5.4 PB diagnostic*: collectively **small-to-medium**. None require touching the orchestrator's main loop in load-bearing ways. Migrations could be one-shot data writes plus the existing-code Racing API backfill.
- *Cadence fixes for §5.2*: **medium** if discovery interval reduces (config) or fast-discovery sweep adds (orchestrator addition); **large** if intensive p50 slip is treated as a tick-granularity / async-per-race rework.
- *Schema-management discipline*: **medium-to-large** to introduce a migration framework retrospectively. Not load-bearing for any §5.1-§5.4 fix.
- *Test infra*: **medium** to add per-module pytest scaffolding; not in scope per brief but worth naming.

### Overall shape
**Targeted rework of specific components.** The pipeline IS a wiring fix at the §5.1, §5.3, §5.4-PB-diagnostic level — none of those fixes require touching the orchestrator's main loop or the storage layer in a load-bearing way. The §5.2 56% finding is a config + small-addition fix at the simplest level (drop `DISCOVERY_INTERVAL`); the intensive p50 slip is the only place where a structural-rework conversation seriously starts (per-race async). The orchestrator file is large but coherent; the storage layer is clean; the scrapers are tidy. There is real but bounded debt — no migration framework, no tests, monolithic orchestrator file — that doesn't block the §5.1-§5.4 fixes but would compound any larger evolution.

---

## Overall read

**Code's recommendation: Routing 1 (surgical fix) is concretely viable for §5.1, §5.3, and §5.4-diagnostic. The 56% finding (§5.2) admits a small surgical fix (config change + a fast-discovery sweep) that would close it materially without structural rework. The intensive-p50 slip (§5.5-adjacent §5.2 question) is the only place where a structural conversation arises, and even there a Reframe (Routing 2) is over-investment given that a `MAIN_LOOP_TICK=15s` change plus per-race-stagger reduction would mostly close the gap.**

Anchored evidence:

1. **§5.1 surgical fix is small and existing-code.** `daily_calibration_summary.py` already runs cleanly. Wiring `runners.finish_position` is a one-line addition (Source 1 path) to surface winner-only positions; full positions come from re-running `backfill_subscription.py --from 2026-03-02` over the live-capture window — a one-shot operator-side run using existing code. The runner-key match logic (`compute_runner_key("N:<num>")`) composes cleanly with the existing Betfair-write path. Effort: small. Risk: low. Backfill of `betfair_selection_id` onto pre-floor runners would require a separate scripted match against `betfair_historical` rows; out of `racing_api.sync_day` scope but a clean follow-up.

2. **§5.3 BSP write-back is small and additive.** Three field changes touching `betfair/client.py`, `betfair/models.py`, `capture/orchestrator.py:_take_betfair_snapshot`, and the INSERT column list in `storage/database.py`. Schema column `bsp_price` already exists. No new tables, no migration. Risk: low.

3. **§5.4 scrapers are well-shaped.** Adding harness/greyhound coverage IS structural at 7× per-platform — but DR-029 §3.x parks that scope explicitly. PointsBet 0.77 is a runtime-probing question, not a structural one. No reason to rebuild on §5.4 evidence.

4. **§5.2 56% no-pre-30min has a small-cost surgical fix path.** Lower DISCOVERY_INTERVAL plus a "fast-discovery if any race is within next-hour" check at the bottom of `_maybe_discover` would close most of the gap. The intensive-p50 slip is structural-leaning but not blocking — `_check_settlement` and `_take_betfair_snapshot` are well-scoped methods that admit refactoring without disturbing the rest of the file.

**The case for Routing 2 (reframe as replacement-design) requires evidence that the surgical path leaves load-bearing brokenness behind. The strongest such evidence would be:** (a) the orchestrator file is so entangled that any §5.2 cadence fix risks regression on §5.1/§5.3, (b) the schema-management approach is a recurring failure source. (a) is not borne out — the orchestrator's methods are coherent units. (b) is a real but slow-burning concern, not a hot-path break.

**The case for Routing 3 (full rebuild) requires evidence that the existing pipeline cannot be evolved.** No such evidence in the source. The code is built around a coherent set of contracts (`BookmakerMeta`/`BookmakerRunner`, `MarketSnapshot`/`RunnerData`, `RaceState`, `compute_runner_key`). The contracts compose cleanly. Tests are absent — but rebuild doesn't fix that unless the rebuild lands with tests, which is independent.

**Code's recommendation, restated:** Routing 1, with explicit acknowledgement that (a) the metadata-backfill service needs its `--days 1` to become `--days <unsynced-window>` or `get_unsynced_dates()`, (b) the orchestrator's `_register_race` silent-drop should grow a log line, (c) the test gap and migration-framework gap are real-but-deferrable debt that accompany any forward path.

---

## Anything surprising

**`racing-metadata-backfill.service` failure confirmed.** Service `Active: failed (Result: exit-code) since Wed 2026-04-29 14:00:05 UTC`. Root cause is `PermissionError: [Errno 13] Permission denied: '/home/racing/racing-data-capture/logs/metadata_backfill.log'`. The log file exists, owned `root:root`, mode 644, dated 2026-03-04 (i.e., created on initial deployment by root, never rotated). The service runs as `User=racing` per the unit file. The code at `scripts/backfill_race_metadata.py:32-49` mkdir's the parent and constructs a `logging.FileHandler(str(LOG_FILE))` — which fails when the file exists with non-writable ownership. The Racing API metadata backfill path has been silently not running since 2026-04-29 14:00 UTC. **Independent of the §5.1 issue:** the service was running via `--days 1` even when it worked; the 30-day window 0% `finish_position` finding cannot be explained by 14h of recent service failure alone. Both are real, both compound.

**`bsp_price` column is orphan in the writer's INSERT — schema declares it but the column isn't in any INSERT statement.** Cleanest source-exposes-but-pipeline-doesn't-write observation. Also: `betfair/models.RunnerData` doesn't have a `bsp_price` field; the orchestrator writes 21 columns but `bsp_price` isn't one of them. The schema column was added in `migrate_depth_and_batch.py` along with the `sp_near_price` / `sp_far_price` columns and the same migration's INSERT-statement update apparently extended to `sp_*` but not `bsp_price`. The 0% population is consistent with column-was-added-but-writer-was-not-extended.

**`health_check.py`'s SOURCES dict is stale — `sportsbet` is commented out as "Disabled until fixed" but is actively producing data.** Per inspection §G.1, sportsbet has 281,567 snapshots in 30d. Per `bookmakers/sportsbet.py` it's the Racing-API-based path (no proxy, no scraping). Per `config/settings.py:36`, `DISABLED_BOOKMAKERS = {"tab", "palm"}` — sportsbet is NOT in that set. So sportsbet runs but health_check doesn't monitor it. (TAB and Palmerbet are correctly disabled in both places.) Mild consistency drift, not load-bearing.

**`tabtouch` appears twice in `health_check.py:SOURCES` dict** (lines 75-83, 84-89). Python dict literal with duplicate key — second entry silently overwrites first. No functional effect (both entries are identical) but indicates the file accumulated a copy-paste artefact.

**`MAIN_LOOP_TICK=30` is the tick granularity ceiling for the documented `INTENSIVE_POLL_INTERVAL=60`.** A 60s interval can never be enforced cleanly by a 30s tick (mean wait ~75s, worst-case 90s). The documented 60s cadence was the design target; the running cadence ceiling is 75-90s by tick math alone, before any per-race serialisation. This is a configuration choice worth surfacing — a 15s tick would make the 60s cadence achievable.

---

## Self-assessment of review completeness

**Areas covered with grounded judgement:** §5.1 (full — calibration's resolution path mapped end-to-end, both write paths identified, runner-key matching mechanics verified, idempotency confirmed). §5.3 (full — three drop points identified across `betfair/client.py`, `betfair/models.py`, `orchestrator.py:_take_betfair_snapshot`, INSERT column list). §5.4 (full — all seven scrapers' race-type filters confirmed, contract-shape uniformity confirmed, PointsBet 0.77 sourced to runtime-only diagnosis). §5.5 (full — schema management, code modularity, test absence, logging shape, all systemd units and the metadata-backfill failure).

**Area covered with appropriate confidence:** §5.2 (56% root cause and intensive p50 slip diagnosed from code shape; would benefit from runtime-log validation but the code-shape diagnosis is internally consistent and the brief carved out runtime probing as out-of-scope).

**Files read in full:** `scripts/daily_calibration_summary.py`, `subscription/racing_api.py`, `scripts/backfill_subscription.py`, `scripts/backfill_race_metadata.py`, `storage/database.py`, `capture/orchestrator.py`, `capture/scheduler.py`, `betfair/client.py`, `betfair/models.py`, `config/settings.py`, `matching/race_matcher.py`, `bookmakers/base.py`, `bookmakers/pointsbet.py`, `bookmakers/entain.py` (full), `capture/proxy.py`, `scripts/run_collector.py`, three `scripts/migrate_*.py`, all four named systemd unit files. **Files read partially (head-only):** `scripts/health_check.py` (first 120 lines, SOURCES dict + failure hints), `scripts/liveness_check.py` (first 120 lines, structure), `bookmakers/{sportsbet,unibet,playup,tabtouch,tab,palmerbet}.py` (head + race-type filter via grep). Tail of each scraper not read in full but the contract conformance is verified at the head and via the grep over filter constants.

**Files NOT read:** `scripts/import_betfair_historical.py` (1,089 LOC) — historical-CSV import only, not on the live-capture write path, not implicated in any §5.1-§5.5 question. `api/main.py`, `api/db.py`, `api/models.py`, `api/routes/*` — the local read API, out-of-scope for write-path review. `scripts/extract_calibration_dataset.sql` — calibration dataset extract, ad-hoc.

**Time budget:** single Code session, roughly half the budget consumed on §5.1 + §5.2 (the load-bearing surgical-fix-viability questions). §5.3 and §5.4 came together more quickly because the code shapes are smaller. §5.5 was largely answered by orientation pre-flight + a few targeted reads.

**Where the review would benefit from additional depth:** (a) `_handle_api_error` in `betfair/client.py` is brief — Betfair rate-limit handling under a faster `DISCOVERY_INTERVAL` would benefit from runtime evidence rather than code-shape inference; (b) PointsBet 0.77 cannot be diagnosed from source alone, would benefit from a runtime probe (sample the discover/fetch responses for a recent day vs an early-window day); (c) the cross-source race-matching confidence distribution (`match_confidence` field on races) wasn't measured against the inspection-report's evidence — could illuminate whether some races are silently dropping due to low-confidence matches even after `_register_race` registration. None of these gaps materially shift the surgical-fix-vs-rebuild calibration; all are forward-routing follow-ups Session 34 may or may not commission.

*End of report.*
