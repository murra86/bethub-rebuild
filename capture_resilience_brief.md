# Capture Resilience Brief — S260 live-incident fixes (A, B, C)

Base: racing-data-capture @ `f2fa921` (498 tests green). VPS runs `f50d4b2`.
Every change here is cherry-pickable onto `f50d4b2` and deployable WITHOUT
International Phase 1. See §6.

Timer status verified on the box:
* `twin-repair-n2/n3` — **do not exist**. Transient `systemd-run` units; both
  stopped and their `/run/systemd/transient/` files are gone. Nothing to re-arm;
  §9 creates permanent units instead.
* `racing-collector-restart.timer` — `inactive` but still **`enabled`**. It would
  re-arm itself unchanged at the next reboot. §9 settles it.

---

## 0. Corrections to the S260 incident write-up (measured, not argued)

The incident narrative in SESSION_260.md was wrong in five ways. Recorded here
because two of them changed the fix:

1. **The root cause is a MISSING INDEX, not lock policy.** See E1/E2.
2. **There IS a busy timeout** — Python's implicit 5.0 s `sqlite3.connect`
   default, implemented as `sqlite3_busy_timeout`. Writes waited 5 s and *then*
   failed; they did not "fail hard immediately".
3. **18:45–20:00 UTC is the EMPTIEST capture window of the day, not "peak UK/US
   racing".** Races are scheduled there; no book we poll serves them (E5).
4. **The card roll is 14:00 UTC**, not 14:30 — the code uses `Australia/Sydney`.
5. **`collector_restart.near_races()` already wraps `datetime()` on both sides**
   — it was never the source of the false all-clear. That was an ad-hoc operator
   query only.

New finding the write-up missed entirely: **the B6 self-heal inside the identity
sweep has the same defect and runs at peak AU racing** (E8).

---

## 1. Evidence base

Read-only from the live DB (5.2 GB, 105,283 races, 4,109,006 betfair snapshots,
7,570,933 bookmaker snapshots) and the repair journal.

**E1 — the merge's real cost.** `logs/twin_repair_full_s259_n2.log`:
```
14:15:02  progress 200/6244 (361.5 markets/s) {'skipped_gate': 200}
14:39:52  progress 400/6244 (0.3 markets/s)   {'skipped_gate': 205, 'merged': 188}
```
Markets 1–200 were pure reads (gate skips) at **2.8 ms each** — so the whole read
phase of `merge_market` is 2.8 ms. Markets 201–400 took **1,490 s / 200 = 7.5 s
each**. `systemd` reports **31 min 20 s CPU in 34 min wall** — CPU-bound, not
I/O-bound, not lock-waiting. Therefore the entire 7.5 s is inside the `with conn:`
write transaction.

**E2 — where the 7.5 s goes.**
```
betfair_snapshots.runner_id   INTEGER REFERENCES runners(id)
bookmaker_snapshots.runner_id INTEGER REFERENCES runners(id)
```
Indexes present: `idx_bf_race_runner(race_id, runner_id)`,
`idx_bk_race_runner(race_id, runner_id)`. **`runner_id` is never leftmost.** With
`PRAGMA foreign_keys=ON`, `DELETE FROM runners WHERE race_id = ?`
(`twin_merge.py:576`) must prove no child references each deleted row — with no
usable index, SQLite scans. Measured live:
```
SELECT EXISTS(SELECT 1 FROM betfair_snapshots   WHERE runner_id = 999999999);  -- 0.198 s
SELECT EXISTS(SELECT 1 FROM bookmaker_snapshots WHERE runner_id = 999999999);  -- 0.353 s
```
**0.55 s per deleted runner row**, warm cache; ~10 donor runners per merge ⇒
5.5–7.5 s. **This is the whole defect.** Every other query in the write path is
index-served (verified by EXPLAIN QUERY PLAN). The donor runners have just had
their children re-pointed away, so the FK probe is guaranteed to find nothing and
scan to the end — worst case by construction.

**E3 — the collector's existing timeout.** `storage/database.py:229`
`sqlite3.connect(str(path), check_same_thread=False)` → implicit 5.0 s. WAL is on
and persists in the file, so readers never blocked; this was purely
writer-vs-writer. Sample errors 9/14/11 s apart, consistent with 5 s waits.

**E4 — the collector's timing budget.** `config/settings.py`: `MAIN_LOOP_TICK=5`,
`INTENSIVE_POLL_INTERVAL=15`, `BOOKIE_INTENSIVE_POLL_INTERVAL=105`,
`POST_START_POLL_INTERVAL=60`, `FINAL_BOOKIE_SNAPSHOT_WINDOW=(10,30)` — a
**20-second-wide** one-shot irrecoverable window per race. The loop is **single
threaded and serial**, so a stall of T seconds delays *every* race by T. A wait
longer than 20 s can cost a race its only irrecoverable snapshot. **A busy_timeout
tuned to "survive a 7.5 s merge" is strictly worse than failing** — it converts
one lost write into a whole-card stall.

**E5 — capture activity by UTC hour** (snapshots written, 7 full days 23–29 Jul):
```
h   betfair  bookies      h   betfair  bookies
09   36252    11871       17       0     5595
14     133    16535       18       0     1263
15       0    18456       19       0       70   <-- global minimum
16       0    11447       20    1014     9180
```
Per-day for hour 19 over 10 days: 0,0,0,70,0,0,0,0,0,24.

**E6 — restart harm by 5-minute slot**, defined as races whose `scheduled_start`
falls in `[T−20min, T+10min]` **and which actually got captured**, averaged over
14 days:
```
UTC    ACST    avg captured races harmed   days with ZERO harm
18:45  04:15   0.64                        8 / 14
18:50  04:20   0.64                        8 / 14
18:55  04:25   0.00                       14 / 14
19:00-20:45    0.00 (0.07 at 19:15-19:45) 13-14 / 14
20:50  06:20   0.43                        9 / 14
21:15  06:45   1.36                        7 / 14
```
**18:55–20:45 UTC (04:25–06:15 ACST) is a measured zero-harm window on 14/14 days.**

**E7 — no gap exists on the raw definition.** 294 races in the next 20 hours;
**zero** inter-race gaps ≥ 20 min. `near_races()` counts all races, so it is
non-zero at essentially every minute. A zero-harm restart is impossible on that
definition; the harm-weighted definition in §A4 is achievable.

**E8 — the B6 self-heal has the same defect, in the money hours.**
`scripts/identity_sweep.py:527` calls `merge_recent_twins(conn, window_days=14)`
with **no `max_markets`**, under `PRAGMA foreign_keys=ON`, on the same
`merge_market`. The 29 Jul 20:20 UTC sweep merged 47 twins in **9 min 45 s**
(~12.4 s/merge — matches E1/E2). The sweep also runs at **00:50 and 05:50 UTC** =
10:20 and 15:20 AEST — peak AU racing. It has caused no storm yet only because
those runs found `twin_merged=0`. Live, undiagnosed instance of Defect A.

**E9 — restart duration.** 30 Jul: SIGTERM 15:00:07 → stopped 15:00:12 → new
process 15:00:13. **~6 s down**, plus Betfair login and first discovery (9 books
× 2–5 s stagger): **~90 s to first snapshot**.

**E10 — rehydration validated against the incident.** As of 14:46 UTC 30 Jul,
`scheduled_start in [now−2h, now+12h]` grouped by `race_date`:
```
2026-07-30 :  81 races (12:47 -> 18:54 UTC)   <-- the abandoned card
2026-07-31 : 123 races (14:00 -> 02:44 UTC)   <-- what discovery already finds
```
The §3 fix recovers exactly the abandoned set and is a no-op for the rest.

---

## 2. DEFECT A — the twin repair starves the collector

### A1 (THE fix) — two indexes

`storage/database.py`, appended to `SCHEMA` after `idx_bk_race_runner`:
```sql
-- S260 incident: betfair_snapshots.runner_id and bookmaker_snapshots.runner_id
-- are FKs to runners(id), but runner_id is not the leftmost column of any
-- index, so `DELETE FROM runners` FK-checks by full scan of 4.1M + 7.6M rows
-- (measured 0.55s per deleted row). That is the entire 7.5s write-lock hold
-- per twin merge, and it starved the collector for 34 minutes on 30 Jul 2026.
CREATE INDEX IF NOT EXISTS idx_bf_snap_runner ON betfair_snapshots(runner_id);
CREATE INDEX IF NOT EXISTS idx_bk_snap_runner ON bookmaker_snapshots(runner_id);
```
Cost: ~11.7M entries, ~180–250 MB (DB 5.2 GB, 24 GB free). Insert path gains one
index maintenance per snapshot row (~5–10% on a non-bottleneck). Build time takes
an exclusive lock: **build it in deploy step 4, inside the zero-capture window,
BEFORE restarting anything** — do not let `init_db()` build it on startup.

New `scripts/migrate_fk_indexes.py`, idempotent, ~40 lines: connect with
`timeout=120` and `PRAGMA busy_timeout = 120000`, run both `CREATE INDEX IF NOT
EXISTS` with timing, `PRAGMA wal_checkpoint(TRUNCATE)`, then print
`EXPLAIN QUERY PLAN SELECT 1 FROM bookmaker_snapshots WHERE runner_id=1`.

**Acceptance:** the EXPLAIN must read `SEARCH ... USING COVERING INDEX
idx_bk_snap_runner (runner_id=?)`, not `SCAN`.

### A2 — explicit `busy_timeout`. **Value: 4000 ms.**

`storage/database.py:229-231` in `init_db`:
```python
conn = sqlite3.connect(str(path), check_same_thread=False, timeout=BUSY_TIMEOUT_S)
conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
```
with module constants and this rationale as a comment:

> NOT a "wait it out" number. The main loop is single-threaded and serial, so a
> T-second wait delays EVERY tracked race by T. The binding deadlines are the
> 20 s-wide forced final bookmaker snapshot (T−30s..T−10s, irrecoverable) and the
> 15 s INTENSIVE Betfair tick. 4 s absorbs every legitimate concurrent writer by
> >20× (post-A1 a twin merge commits in ~50 ms; identity sweep, morning sweep and
> coverage recompute all commit in milliseconds) while leaving ≥16 s of the
> final-snapshot window intact even if a write stalls to the full timeout. A
> longer value would convert one lost row into a whole-card stall, which is
> strictly worse. Before S260 this was Python's IMPLICIT 5.0 s default.

Also: `api/live_fetch_log.py:62` (a second live WRITER into capture.db from the
API process) → `timeout=4.0` + `PRAGMA busy_timeout = 4000`. `api/db.py:12`
read-only → `PRAGMA busy_timeout = 2000` (a checkpoint RESTART can return BUSY).
Leave batch jobs as they are (identity_sweep 30 s, morning_sweep 30 s,
coverage_recompute 60 s, merge_market_twins 60 s) — those SHOULD wait.

### A3 — make lock loss visible

`capture/orchestrator.py`: add `self._lock_errors: int = 0`; increment in the
`except` blocks of `_take_bookie_snapshots` and `_persist_race` when
`"database is locked" in str(e)`; append `db-lock errors: %d` to the discovery
summary line and reset per pass. In `scripts/liveness_check.py`, extend the
capture-silent check to name the lock when ≥20 lock errors appear in the last
15 min of the collector journal.

### A4 — repair pacing (defence in depth; keep even after A1)

New `storage/pacing.py` — ONE definition of "capture would be harmed", shared by
the repair and the recycle wrapper. Deliberately **harm-weighted, not
race-weighted**: 294 races in 20 hours with zero ≥20 min gaps means a
race-counting definition can never be satisfied; a race we are not capturing
costs nothing to interrupt.

```python
NEAR_FORWARD_MIN = 10       # jumps within the next 10 min
RECOVERABLE_BACK_MIN = 20   # ... or jumped within the last 20 min
FRESH_CAPTURE_MIN = 15      # ... and we wrote a snapshot for it this recently

def hot_races(conn, back_min=20, fwd_min=10, fresh_min=15) -> int
def stale_card_in_flight(conn, today_card: str) -> int
```
`hot_races` counts races inside the irrecoverable window that we are **actively
capturing** (`bookies_last_snapshot_at` or `betfair_last_snapshot_at` fresh
within `fresh_min`). `stale_card_in_flight` counts actively-captured races whose
`race_date < today_card` and whose jump is within [−60 min, +90 min] — the Defect
B safety net, kept even after rehydration lands.

Timestamp discipline in both: `datetime()` applied to BOTH sides, plus a bare
date-prefix lower bound as a sargable prefilter so `idx_races_start` still bounds
the scan (a date prefix sorts before any `YYYY-MM-DDT...` value of the same day,
so it is a safe lower bound).

`scripts/merge_market_twins.py` — **pacing only, no merge semantics**:
1. New args `--sleep-between` (default **0.25** s), `--yield-to-capture` (default
   on), `--max-lock-ms` (default **2000**), `--checkpoint-every` (default 200).
2. Connection: `busy_timeout = 60000`, `foreign_keys = ON`, and
   **`wal_autocheckpoint = 0`** — the 75 MB WAL was autocheckpoint retrying (and
   fsyncing a 5.2 GB main file) after every commit while live readers held
   snapshots.
3. Before each merge: while `hot_races(conn)` and waited < 120 s, sleep 5 s; log
   the yield.
4. Per-merge lock-hold watchdog: time the merge; if it exceeds `--max-lock-ms`,
   WARN with the market id and back off; **after 10 consecutive slow merges,
   ERROR and STOP** ("the runner_id FK indexes are missing or the DB has
   regressed"). This makes a repeat of 30 Jul self-limiting even if A1 is reverted.
5. Checkpoints: `PASSIVE` every `--checkpoint-every` markets (never blocks a
   writer, never waits for readers); `TRUNCATE` exactly once after the loop. The
   current code TRUNCATEs every 200 markets, which takes the writer lock and waits
   for readers up to the 60 s timeout — itself a pathological-hold generator.

`storage/twin_merge.py` — **one change only**: `merge_recent_twins(...,
max_markets: int | None = 25)` (was `None`). Rationale E8: the sweep runs at
00:50 and 05:50 UTC inside peak AU racing, and an uncapped self-heal is a
47-merge / 9m45s write-lock train through the money card. Post-A1 that is
25 × ~50 ms, but the cap makes the guarantee structural rather than incidental.
`merge_market` itself is untouched.

### A5 — STRATEGIC: keep a bounded bulk job; do NOT trickle it through the sweep

**Recommendation: keep the bulk repair, move it into the measured zero-capture
window, pace it, finish the backlog in one night.** Reasoning by weight:

1. **The backlog is now ~30 minutes, not 5 hours.** 5,800 × (~0.05 s merge
   post-A1 + 0.25 s yield) ≈ 29 min, plus ~60 s orphan scan — inside the
   110-minute zero-harm window with room. The premise that motivated a trickle
   ("this takes all night, and there is no all-night") is dissolved by A1.
2. **The trickle destination is worse than the source.** The obvious host is the
   identity sweep, but two of its three daily runs are at peak AU racing (E8).
   A low-priority daemon has the same problem in a more complicated shape: under
   continuous operation it must yield constantly, and a yielding daemon that only
   progresses in the zero-capture window *is* the nightly job with an extra
   process and an extra failure mode.
3. **A bounded job has a deadline, a journal and a visible end.** The repair is
   resumable by construction. A trickle has no completion event, so "is the
   backlog gone?" becomes a standing question.
4. **Both shapes need A1 and A4 anyway.**

So: one permanent nightly unit (§9), `--all --deadline 05:45 --sleep-between 0.25
--yield-to-capture`, fired **05:05 ACST** (V5 — after the 05:00 backup, which
`sqlite3 .backup` would otherwise never finish against a committing repair) and
gated on `hot_races()` rather than on the clock (V1). Expected to clear all 5,800 the
first night; thereafter a no-op, and disableable once two consecutive nights
report the same remaining count.

### A6 — `collector_restart.py` references a dead unit

`scripts/collector_restart.py:62` `REPAIR_UNIT = "twin-repair-n2.service"` — that
unit no longer exists, so the guard is inert. Change to
`REPAIR_UNITS = ("racing-twin-repair.service", "racing-identity-sweep.service")`
and refuse if any is active (the sweep is now a merge writer too).

---

## 3. DEFECT B — restarting the collector drops the in-flight card

### B1 — how the tracked set is actually built (settled from code)

`Orchestrator.__init__` starts with `self._races = {}`. The **only** population
path is `_maybe_discover` → `match_races(...)` → `_persist_race` →
`_register_race`. **There is no startup load from the database at all.**

`match_races` builds its grid **exclusively from `bookmaker_discoveries`**
(`race_matcher.py:225-232`), each fetched as `discover_fn(today_str)` where
`today_str = local_racing_day(utc_now, "Australia/Sydney")`
(`orchestrator.py:305`). Betfair markets are matched *onto* that grid; Betfair
discovery is AU-only today, so an overseas race has no Betfair market to rescue it.

Consequence: **a race is trackable only if it appears on the bookmaker card for
the current AU racing day.** The UK/IE evening card of 30 Jul was filed by TAB
under its 30 Jul card; once `today_str` rolled to 31 Jul (at **14:00 UTC** —
Sydney midnight), those races were absent from every discovery response and could
not be re-registered. Before the restart they survived only because their
`RaceState` objects were already in memory. That is exactly why a restart — and
only a restart — drops them, and why the liveness self-heal did the same damage.

### B2 — the fix: rehydrate by `scheduled_start`, never by `race_date`

Right for three independent reasons: (a) it is the only predicate true of a race
running *now* regardless of which card filed it; (b) it survives Phase 1
unchanged, because Phase 1 keeps `race_date` as the AU card/join date and adds
`local_race_date` — a rehydration keyed on either date column would have to move
with that decision, one keyed on `scheduled_start` does not; (c) it repairs the
liveness self-heal restart, which no wrapper script can gate.

`capture/orchestrator.py`: constants `REHYDRATE_BACK_HOURS = 2`,
`REHYDRATE_FORWARD_HOURS = 12`; new `_rehydrate_tracked_races(bf_win, bf_place)`
placed immediately after `_register_race` (~line 563). It selects id + all book
ids + market ids from `races` where `scheduled_start` is in the window (with the
sargable date prefix and `datetime()` on both sides) and
`COALESCE(capture_status,'PENDING') NOT IN ('SETTLED','TIMEOUT')`, skips anything
already in `self._races` or `self._retired`, skips any row whose WIN market is
already tracked (0l B5 guard), and calls `_register_race`. Logs one
`AUDIT rehydrated N in-flight race(s) ... by card date: {...}` warning.

Supporting edits:
* `__init__`: `self._retired: set[int] = set()` (place with `self._au_venue_cache`,
  **after** the Phase 1 hunk at `@@185`).
* `_process_all_races`: on the `COMPLETE`/`TIMEOUT` cleanup path,
  `self._retired.add(race_id)`. **Do NOT** add on the `sqlite3.IntegrityError`
  path — that one deliberately forces re-discovery. Without `_retired` the
  rehydration would re-register every finished race until it aged out: an infinite
  re-registration loop and a repeated settlement poll.
* `_maybe_discover`: call it **at the end**, immediately before
  `self._coverage = CoverageIndex.load(...)` (~line 422). End-of-pass placement
  means the Betfair catalogue is in hand and it cannot mask a discovery failure.
  The first pass runs within one `MAIN_LOOP_TICK` of startup, so recovery after a
  restart is ~5 s, not 30 min.
* `_register_race` needs no change: it reads `race_data.get(...)` for every field
  the DB row supplies, and `book_query_date` correctly falls back to `race_date`
  via `RaceState.fetch_date()` — exactly the "a race belongs to the card it was
  discovered on" rule (`scheduler.py:76-82`).

Cost: one indexed query per 30-minute pass; 204 rows at 14:46 UTC on 30 Jul, of
which 123 were already tracked.

### B3 — `collector_restart.py` must also refuse on a previous card in flight

Replace `near_races()` with the shared `storage.pacing` predicates: refuse when
`hot_races(conn)` is non-zero, and separately when `stale_card_in_flight(conn,
today_card)` is non-zero, each with its own log line. Prefer deleting
`near_races()` and updating `tests/test_continuous_operation.py`.

Note: `near_races()` was **already correct** on the datetime question
(`collector_restart.py:109-116` wraps both sides). Its real defect is the one the
S259 review predicted — it counts races we are not capturing, so under continuous
operation it can never be satisfied (E7).

### B4 — the recycle window, and whether the recycle is still needed

**Keep the recycle. Move the window from 04:15–05:30 to 04:25–06:05 ACST
(18:55–20:35 UTC), and redefine "gap" as harm-weighted (§A4).**

* The write-up's premise is wrong and the data says so: 18:45–20:00 UTC is the
  emptiest capture window of the day (E5 — hour 19 produced 70 snapshot rows
  across 7 days against 18,456 at hour 15). On the harm-weighted measure it is
  **zero on 14/14 days from 18:55 UTC onward** (E6). Only 04:15 and 04:20 ACST
  carry any harm at all, at 0.64 races.
* `config/settings.py`: `COLLECTOR_RESTART_AT = (4, 25)`,
  `COLLECTOR_RESTART_GIVE_UP_AT = (6, 5)`. The give-up stays at 06:05 so the
  restart remains inside `MAINTENANCE_WINDOW_END`, which
  `liveness_check.collector_expected_running()` uses to avoid alerting on the ~6 s
  outage. **Do not push past 06:05 without changing both copies of that constant
  (`config/settings.py:135` AND `liveness_check.py:83` — they are duplicated).**
* **Still needed?** Yes, weakly, and now nearly free. The collector ran 7h52m at
  80 MB RSS with no growth signal, and the Betfair session is maintained by
  `_maybe_keep_alive` with a re-login fallback — so the recycle is insurance
  against slow leaks and session rot, not a functional requirement. Its cost is
  ~90 s in a window where we capture nothing, on 14/14 days. Insurance at that
  price is worth buying. What is not worth buying is a recycle that can never fire
  (today's) or one that fires blind.
* The recycle now also refuses while the repair or identity sweep is active (§A6).

---

## 4. DEFECT C — the SQL datetime comparison trap

`'2026-07-31T18:55:00+00:00' > '2026-07-30 22:51:23'` is true because `'T'`(0x54)
> `' '`(0x20), so **every** stored value sorts after any `datetime('now')` string
of the same or earlier date. Full sweep of `scripts/`, `capture/`, `storage/`,
`api/`:

| Site | Verdict |
|---|---|
| `scripts/collector_restart.py:109-116` | **SAFE** — both sides wrapped; the date-prefix lower bound is correct and sargable. Contradicts the write-up. |
| `scripts/deploy_phase1.py:151-157` | **SAFE** — identical shape |
| `scripts/liveness_check.py` (10 sites) | **SAFE**, and the reference implementation — its docstring documents the trap |
| `scripts/health_check.py:247-248` | **SAFE** |
| `scripts/morning_sweep.py` (4 sites) | **SAFE** — parsed Python-side via `fromisoformat` |
| `storage/racing_day.py:301`, `storage/twin_merge.py:184-194`, `capture/orchestrator.py:506` | **SAFE** — Python side / both sides same format |
| **`api/routes/races.py:74-75`** | **REAL FINDING, currently benign.** String-compares a format-matched literal (`strftime('%Y-%m-%dT%H:%M:%S+00:00','now')`). Works only because the collector writes exactly that format; the DB already holds a second format (`...T13:00:00.0000000Z`) for which `'.'`(0x2E) > `'+'`(0x2B) mis-orders same-second rows — benign only because every such row is dated 2025. One writer-format change silently empties the endpoint. **FIX**: wrap both sides in `datetime()`, keep a date-prefix prefilter. |
| `api/routes/races.py:85`, `api/routes/results.py:98` | **ADJACENT REAL BUG, different trap**: `race_date = date('now')` compares the **UTC** date against the **AU card** date, so for the ~10 hours from 14:00 UTC these endpoints return the wrong card. Flagged; fix optional, out of this brief's blast radius. |

---

## 5. Test plan — red before green

New file `tests/test_capture_resilience.py` except where noted. Baseline 498.

**A1 (3):** indexes exist after `init_db`; `EXPLAIN QUERY PLAN` shows
`USING COVERING INDEX idx_bk_snap_runner` not `SCAN` (red on HEAD); migration
idempotent.
**A2 (3):** `PRAGMA busy_timeout` is 4000 (red: HEAD returns 5000); a write
succeeds behind a 0.5 s holder; a write **fails in <5 s** behind a pathological
holder (monkeypatched timeout, proving it does not stall the loop).
**A3 (1):** lock errors counted and surfaced in the discovery summary.
**A4 (5):** `hot_races` ignores uncaptured races (red: old `near_races` returns 2);
`hot_races` correct against ISO-with-offset stamps (the defect-C regression fence);
repair yields while capture is hot; repair aborts after 10 slow merges;
`merge_recent_twins` defaults to a cap of 25 (red: HEAD merges all 31) — in
`tests/test_twin_merge.py`.
**B (6):** **the incident test** — a 30 Jul race in flight while discovery returns
only 31 Jul must land in `_races` (red on HEAD); idempotent; never resurrects a
retired race (**the infinite-loop fence**); respects the market-twin guard; skips
SETTLED/TIMEOUT; window bounds (−3 h and +13 h out, −1 h and +11 h in).
**B3 (3):** defers on an actively-captured near race; **proceeds when near races
are not being captured** (red: HEAD defers — the case the old predicate could
never reach); defers on a previous card in flight.
**C (2):** `/races/upcoming` returns a legacy-format row dated today (red on HEAD);
excludes past and far-future.

Expected total: **498 → 548** as built (the v2 review adds the aggregate-rate
abort, the WAL fence, the `_retired`/IntegrityError split, the yield bounds and
the scripted lock guard).

---

## 6. Phase 1 independence — BUILT AND VERIFIED (rewritten, F2)

**The v1 text of this section was wrong in a way that could have shipped Phase 1
by accident.** It named two shared files and promised "zero conflicts". There are
**three**, and the third **does** conflict — exactly as review item V6 predicted.
What follows is the build as actually performed, not a claim.

### 6.1 Which commits go on the branch

| Commit | On `s260-resilience`? | Why |
|---|---|---|
| `fed12c6` "S260 capture resilience: …" | **YES — this is the whole deploy** | A/B/C |
| `52b4382` "S260 resilience review round 2: six fixes" | **YES** | F1/F3/F4/F5/F6 |
| `7669997` "S260 deploy_phase1: the VPS has no git remote" | **NO — DO NOT PICK** | it touches `scripts/deploy_phase1.py` and `tests/test_intl_rekey.py`, which are **Phase 1 files that do not exist on `f50d4b2`**. Cherry-picking it produces two "deleted by us" conflicts and nothing useful. It is a Phase 1 fix and ships with Phase 1. |

### 6.2 The three shared files

* `api/routes/races.py` — Phase 1 adds `country=`/`local_race_date=` inside
  `_build_race_summaries` (~59-62). Our edit is the `/upcoming` query at 72-79.
  **No overlap; auto-merges.**
* `capture/orchestrator.py` — Phase 1 has 7 hunks (`@@81 @@166 @@185 @@303 @@361
  @@456 @@477`). Our edits sit between them. **No overlap; auto-merges** (git
  reports `Auto-merging capture/orchestrator.py`, which is normal, not a warning).
* **`scripts/liveness_check.py` — CONFLICTS. EXPECT IT. It is not a mistake and
  it does not mean the branch is wrong.** Phase 1 rewrote this file heavily
  (+170 lines) and A3 adds its `db_lock_errors()` block immediately above where
  Phase 1 inserted its country-census block, so the A3 hunk's trailing context is
  Phase 1 code that does not exist on the base.

### 6.3 THE liveness_check.py CONFLICT — exact resolution

**Read this before touching anything.** The conflict is deceptive by shape:

```
<<<<<<< HEAD
=======            <-- the HEAD side is EMPTY. There is nothing of yours here.
... 172 incoming lines ...
>>>>>>> fed12c6
```

An empty HEAD side makes "take theirs" look obviously right. **It is not.** Only
the **first ~30** of those 172 lines are the A3 change. The remaining ~142 are
Phase 1's country-census block, dragged in as diff context. Accepting the whole
incoming side **silently imports Phase 1 code onto a non-Phase-1 base** — it will
even pass tests, because nothing on this base calls it, and you will have shipped
half of international Phase 1 without meaning to.

**Resolution, exactly:**

1. **KEEP** everything from the comment line
   `# S260 A3 — name the write lock when capture goes silent.`
   down to and including the final line of `db_lock_errors()`:
   `               if "database is locked" in line.lower())`
   — i.e. the comment block, `DB_LOCK_ALERT_THRESHOLD = 20`,
   `DB_LOCK_WINDOW_MINUTES = 15`, and the whole `def db_lock_errors(...)`.
2. **DELETE** everything from the line `COUNTRY_WINDOW_HOURS = 24` onward, down to
   and including the `>>>>>>>` marker. That is all Phase 1.
3. **DELETE** the `<<<<<<< HEAD` and `=======` markers.
4. Leave exactly two blank lines before the next `def check_api_responsive():`.

**The one-line test that you resolved it right** (run before `--continue`):
```bash
grep -c COUNTRY_WINDOW_HOURS scripts/liveness_check.py   # MUST print 0
grep -c "def db_lock_errors"  scripts/liveness_check.py   # MUST print 1
grep -c "<<<<<<<\|>>>>>>>"    scripts/liveness_check.py   # MUST print 0
```
If the first one prints anything but `0`, you took Phase 1. Redo it.

The second A3 hunk in the same file (the `n_locks` block in `main()`, ~line 1118)
applies **cleanly**. There is only ever one conflict in this file.

### 6.4 The build, as performed

```bash
git worktree add -b s260-resilience /tmp/s260wt f50d4b2
cd /tmp/s260wt
git cherry-pick fed12c6          # CONFLICT in scripts/liveness_check.py — expected
#   ... resolve per 6.3, run the three greps ...
git add scripts/liveness_check.py && git cherry-pick --continue
git cherry-pick 52b4382          # clean
uv run pytest
```
**Result: green.** `f50d4b2` alone is **396** tests; with both commits it is
**451**. (On `master`/`f2fa921` the same commits give **555**; the 104-test gap is
Phase 1's own suites, which do not exist on this base.)

Forward-compatibility: rehydration keys on `scheduled_start` only. **If Phase 2
ever makes `race_date` venue-local for foreign rows, rehydration must read a
persisted `book_query_date`, which does not exist as a column today.** Recorded as
a Phase 2 precondition. The F5 identity guard inherits the same caveat: its
`race_date` clause is a card-date comparison, and its `scheduled_start` clause is
the one that survives the Phase 2 decision unchanged.

Forward-compatibility: rehydration keys on `scheduled_start` only. **If Phase 2
ever makes `race_date` venue-local for foreign rows, rehydration must read a
persisted `book_query_date`, which does not exist as a column today.** Recorded as
a Phase 2 precondition.

---

## 7. Deploy runbook — CORRECTED (supersedes the v1 sequence; V2/V3/V4/V5/V8/V10)

**Target window: 18:55–20:15 UTC (04:25–05:45 ACST).** V2: hour 20 is NOT
zero-capture (9,180 bookie snapshots per 7 days, more than hour 17 — STANDARD
polls for 21:00+ jumps), so the window ends 20:15, not 20:35.

**This is the LEAST-HARMFUL hour today, not a quiet window.** V1: ~10 races/day
are scheduled in it and die at a 404 in our own fetch path. Treat it as a
one-off convenience for this deploy only; the permanent units gate on STATE
(`hot_races()`), never on this clock.

**Order changed (V3): STOP THE COLLECTOR BEFORE BUILDING THE INDEXES.** The
indexes live in `SCHEMA`, so any collector start during the build runs
`executescript(SCHEMA)`, blocks on the EXCLUSIVE lock, dies at the 4 s
busy_timeout, and crash-loops (`Restart=on-failure`, `RestartSec=30`) for the
whole build. Stopping first is strictly safer and costs nothing in this window.

**Push first (V4): the VPS has NO git remote** (`origin` on the dev machine
points AT the VPS — it is a push-to-VPS model), so `git fetch/pull` on the box
is a no-op or a hard failure. `git push origin <branch>` from the dev machine
BEFORE step 0.

```
0. Local: uv run pytest -> 555 green on master (baseline was 498).
   Local: build s260-resilience off f50d4b2 (§6) -> ONE EXPECTED conflict in
   scripts/liveness_check.py, resolved per §6.3 (run the three greps), then
   451 green on that base. Do NOT cherry-pick 7669997 (§6.1).
   Local: git push origin s260-resilience     <-- V4. Without this, step 4 fails.
1. Confirm no unit is mid-run:
     systemctl is-active racing-identity-sweep racing-morning-sweep \
                         racing-coverage-recompute racing-backup \
                         racing-twin-repair
   All inactive. Confirm the window: date -u  (must be 18:55-20:15).
2. Verify today's backup exists:
     ls -la /home/racing/racing-data-capture/data/backups/ | tail -3
   V10: backups live at data/backups/ (capture_YYYYMMDD.db, 5.2 GB), NOT
   /home/racing/backups/. The day's backup runs at 19:30 UTC, so before then
   "today's" legitimately does not exist -- empty output is NOT a pass, it is a
   "check yesterday's and decide".
3. STOP the collector (V3):
     sudo systemctl stop racing-capture
   Confirm it is down before continuing: systemctl is-active racing-capture
4. Build the indexes (EXCLUSIVE lock, 60-180 s; ~134 MB, measured):
     sudo -u racing venv/bin/python3 scripts/migrate_fk_indexes.py data/capture.db
   ACCEPTANCE: it must print PASS on both probes and
   "SEARCH ... USING COVERING INDEX". If it says SCAN, STOP and roll back --
   the rest of Defect A is inert. The script exits non-zero on failure.
5. Check out the code (collector still DOWN):
     sudo -u racing git -C /home/racing/racing-data-capture checkout s260-resilience
     sudo -u racing git -C /home/racing/racing-data-capture rev-parse HEAD
   Assert the SHA matches what was pushed in step 0.
6. START the collector (~90 s to first snapshot):
     sudo systemctl start racing-capture
   ACCEPTANCE within 2 min: "Orchestrator started"; "Running discovery for <date>";
   "Discovery complete: ... db-lock errors: 0"; an "AUDIT rehydrated" line IF any
   previous-card race is in flight (expect N=0 in this window -- absence here is a
   pass, and step 9 is what actually proves the rehydration).
7. Install the permanent units (§9) and re-arm both timers.
8. Run the repair ONCE by hand, GUARDED (V8 -- not an eyeball step).
   The guard goes FIRST, deliberately: it must be watching from the first
   merge. F6: it now waits up to 30s for the repair to appear, so this
   ordering is safe and so is the reverse -- neither can make it exit
   thinking there is nothing to guard.
     sudo -u racing venv/bin/python3 scripts/repair_lock_guard.py \
          > logs/repair_lock_guard.log 2>&1 &
     sudo -u racing venv/bin/python3 scripts/merge_market_twins.py --all \
          --deadline 05:38 --sleep-between 0.1 --yield-to-capture \
          --max-lock-ms 2000 > logs/twin_repair_s260_indexed.log 2>&1 &
   F3: the deadline is 05:38 and the sleep is 0.1 -- NOT 05:45/0.25, which
   left the post-loop orphan scan finishing 05:47-05:49 against the 05:50
   identity sweep, a SECOND merge writer into the same tables. Arithmetic
   in §9.
   The guard stops the repair on the FIRST 'database is locked' line in the
   collector journal, and stops it if it cannot read the journal at all.
   The repair also self-limits: 10 consecutive merges over 2000 ms, any
   200-market block under 1 market/s, or a WAL over 1 GB all abort it.
   ACCEPTANCE at the first "progress 200/..." line: rate >= 3 markets/s
   (pre-index it was 0.13). Expect ~5,800 in ~15 min, then the orphan scan,
   then the remaining count (a non-zero remainder is expected -- see §10).
   READ THE LAST LINE, not the remaining count: "DONE in ..." (exit 0) means
   the scope was walked; "INCOMPLETE ..." (exit 75) means the deadline
   stopped it early -- normal and resumable, but it is NOT finished, and
   §10's pre-authorised remainder is not the explanation. F4.
9. DEFECT B ACCEPTANCE (the real one, NEXT DAY, 14:00-19:00 UTC): after the
   Sydney-midnight roll, with the overseas card in flight, restart the collector
   and confirm the "AUDIT rehydrated ... by card date: {'<yesterday>': N}" line,
   fetch attempts for those venues, and fresh snapshot rows for them.
   This is the test 30 Jul failed. Do it deliberately.
```

**Expected capture cost: ~90 s of downtime plus 60–180 s of index-build
contention, in the least-harmful hour of the day.** On the (circular, V1)
harm-weighted measure that is 0 captured races; the honest figure is "up to a
handful of the ~10/day GB/US races we are already failing to capture in this
hour anyway". If the window slips past 20:15 UTC the at-risk figure rises with
the 21:00 jumps.

---

## 8. Rollback

* **A1 indexes** — additive, semantics-free. `DROP INDEX idx_bf_snap_runner;
  DROP INDEX idx_bk_snap_runner;` (seconds). No scenario needs this except disk
  pressure.
* **A2/A3/A4/B/C** — code only. `git checkout f50d4b2 && sudo systemctl restart
  racing-capture` (~90 s). **Leave the indexes in place** — they are independently
  correct and are what makes the un-paced code survivable.
* **Twin repair** — merge semantics untouched, so the S259/S260 rollback story is
  unchanged: `race_row_merges` holds donor pre-images and the child-move manifest
  per market; reversal is a hand restore from the journal. The pacing changes add
  no new rollback surface. If it misbehaves, `systemctl stop
  racing-twin-repair.service` — progress is banked per market.
* **Timers (V9 — this was wrong in v1).** Step 7 installs units into
  `/etc/systemd/system/`, so `git checkout f50d4b2` reverts the CODE and leaves
  them ARMED — firing an unpaced repair, or one whose new flags no longer parse.
  **Rollback MUST include:**
  `sudo systemctl disable --now racing-twin-repair.timer racing-collector-restart.timer`
* **Point of no return: none** for the code. The only irreversible artefacts are
  the merges, governed by the pre-existing S259 journal procedure.

---

## 9. Re-arming the two timers

Both units go in `deploy/systemd/` **in the repo** — the previous repair units
were `systemd-run` transients that vanished on stop, which is why nothing is left
to re-arm and why it must not be done that way again.

**`racing-twin-repair.service`** — `Type=oneshot`, `User=racing`,
`WorkingDirectory=/home/racing/racing-data-capture`, ExecStart
`venv/bin/python3 scripts/merge_market_twins.py --all --deadline 05:38
--sleep-between 0.1 --yield-to-capture --max-lock-ms 2000`, output appended to
`logs/twin_repair.log`, `TimeoutStartSec=5400`, **`SuccessExitStatus=75`**.

**THE TIMING BUDGET (F3 — this was too thin at 05:45/0.25).** The envelope is
05:05 start → 05:50 identity sweep = **45 minutes**, and *everything* must fit,
including the work that happens **after** the deadline break:

| | old (05:45, 0.25 s) | new (05:38, 0.1 s) |
|---|---|---|
| loop, 5,800 × (0.05 s merge + sleep) | 29.0 min → ends 05:34 | **14.5 min → ends 05:19.5** |
| slack left for yields before the deadline | **4 min** | **18.5 min** |
| post-loop `TRUNCATE` + `verify_no_orphans` + 2nd `find_twin_markets` (all AFTER the break) | 2–3 min → **05:47–05:49** | 2–3 min → **~05:41** |
| clear of the 05:50 sweep by | **1–3 min** | **≥ 9 min** |

Yields are not free: `hot_races()` is **5** right now and each yield costs up to
120 s, so the old 4-minute slack was two yields wide. The new budget absorbs
nine.

**`SuccessExitStatus=75` (F4).** Exit 75 = `INCOMPLETE`: the deadline stopped the
run with markets still in scope. That is a normal, resumable outcome — every
merged market is committed and drops out of scope — so systemd must not mark the
unit failed. The script still exits non-zero and logs `INCOMPLETE`, never `DONE`,
so a human reading the morning log can tell "ran out of time" from "finished".
Exit 1 (orphans, or a self-limiting abort) remains a real failure. `Type=oneshot`
with no `Restart=`, fired only by the timer, so **no exit code can produce a
restart loop**.

**`racing-twin-repair.timer`** — `OnCalendar=*-*-* 05:05:00 Australia/Adelaide`,
**`Persistent=false`** (a missed night must NOT fire a catch-up run into racing).
**05:05, not 04:30 (V5):** `racing-backup.timer` fires at 05:00 and
`scripts/backup_db.sh` uses `sqlite3 .backup`, whose API **restarts from page 1
on every source write** — a repair committing every ~0.15 s for a quarter of an
hour means a 5.2 GB backup that never converges, or fails locked (`set -euo
pipefail` ⇒ unit fails). `--deadline 05:38` then stops well before the 05:50
identity sweep, which is a second merge writer.

**The clock is NOT the safety property (V1).** The unit's actual gate is
`--yield-to-capture` → `storage.pacing.hot_races()`: it pauses whenever a race
is being actively captured inside its irrecoverable window, at any hour. That is
deliberate — there is no quiet clock window, only a quiet state, and Phase 1
will fill this hour with GB racing.

**`racing-collector-restart.timer`** — OnCalendar every 5 minutes from
`04:25` to `06:05 Australia/Adelaide`, `Persistent=false`; plus the
`config/settings.py` constants from §B4. Same rule: the clock is only the retry
envelope, `hot_races()` and `stale_card_in_flight()` decide.

Arming (deploy step 7): copy both to `/etc/systemd/system/`, `daemon-reload`,
`rm -f data/.collector_restart_day` (clears the give-up stamp), then
`systemctl enable --now` both timers and confirm each shows a concrete NEXT.
**`racing-collector-restart.timer` is currently `inactive` but still `enabled`, so
it would have re-armed itself unchanged at the next reboot** — `enable --now` with
the new OnCalendar is the fix, not merely a convenience.

**Morning-after verification (mandatory):** repair log shows **`DONE in ...`** —
if it shows **`INCOMPLETE`** the run was truncated by the deadline (exit 75) and
is *not* finished: it will resume tonight, but two `INCOMPLETE` nights in a row
means the budget above is wrong, so read the yield lines (F4) — plus an
all-zero orphan scan, a remaining count, and progress lines at ≥3 markets/s;
`grep -c "database is locked"` over the collector journal **must be 0**; the
restart log shows either a completed restart or a deferral reason. Per S260's own
standing rule: **absence of output is not a pass.**

---

## 10. What this brief could not settle from code

**One item.** The ~200–205 markets that skip at the identity gate on every pass
(`overlap 0/N below 50%`) will never clear, and will make every future nightly run
report a non-zero remainder. **F4 note: because this remainder is pre-authorised
here, the remaining count can never be read as "did the run finish?" — that is
what the `DONE` / `INCOMPLETE` line is for.** Whether that remainder is correct (two genuinely
different races sharing one market id, which must never merge) or a gate
mis-calibration is a **merge-semantics** question, explicitly out of scope. It
needs its own read-only census. It blocks nothing here: it is why §A5 says the
nightly unit can be disabled once two consecutive nights report the same count.

---

# v2 — Adversarial review round 1: integrated fixes (NORMATIVE)

Two reviewers: correctness **SAFE WITH FIXES**, ops **NOT SAFE** (the deploy as
written cannot execute). This section overrides §0–§9 wherever they conflict.

**ROOT CAUSE INDEPENDENTLY CONFIRMED.** Reviewer 1 reproduced the timings
(betfair probe 0.199 s + bookmaker 0.347 s = **0.546 s/runner** vs the plan's
0.55) and ran a **controlled experiment** on a 2 M-row replica: without the index
`SCAN` at 28 ms/row; with `(runner_id)` `SEARCH ... USING COVERING INDEX` at
0 ms/row — SQLite's FK enforcement really does use it. A1 works. Real index size
~**134 MB** (plan's 180–250 MB was conservative); build well under 180 s.

## V1 — THE "ZERO-CAPTURE WINDOW" DOES NOT EXIST (SEVERE; kills §B4's premise)
E5/E6 measure **the defect, not the absence of racing**. `races` holds **144
races scheduled in 18:55–20:35 UTC over 14 days (~10.3/day)** — 33 GB/IRE
(Salisbury, Lingfield, Leicester, Wolverhampton), 50 US/CAN — all present in our
DB **with `tab_race_id` set**, discovered by our own TAB poll, dying at the
per-race fetch (journal: `2026-07-24T19:37 TAB attempt 404 … saratoga extra R6`).
Captured per UTC hour over 14 days: h19 **1/99**, h20 **0/66**, versus 98% at
h00–12. **§0 correction #3 is REFUTED — and so is what I told the operator: it is
not that "no book serves them", it is that our fetches 404.** E6 is circular: it
counts only races that *were* captured, so it is blind by construction to exactly
the ~10/day this brief exists to protect.

Consequences, all binding:
1. The **one-off deploy** may still use the window — it is genuinely the
   least-harmful hour *today*.
2. The **permanent units must NOT be pinned to that clock.** Gate the nightly
   repair on `hot_races()` (A4 already builds the predicate) and let it run
   whenever capture is actually idle, rather than trusting an hour that is only
   quiet because of a bug.
3. **Precondition, recorded:** re-derive E5/E6 **after** Phase 1 lands. Phase 1
   puts ~4 GB races/day into exactly 18:55–20:35 UTC, so today's numbers expire
   the moment the GB flip happens.
4. This is the same lesson as E7 in a different costume: there is no quiet clock
   window, only a quiet *state*. Gate on state.

## V2 — hour 20 is NOT zero-capture, on the plan's own data (MAJOR)
E5 reproduces exactly (h19 = 70) but **h20 = 9,180 bookie snapshots/7 d** — more
than h17. Those are STANDARD polls for 21:00+ jumps. Therefore: **deploy window
ends 20:15 UTC**, and step 7's `--deadline` must not reach into it.

## V3 — STOP THE COLLECTOR FOR THE INDEX BUILD (both reviewers, independently)
The index lives in `SCHEMA`, so any collector start during the build runs
`executescript(SCHEMA)` → blocks on the EXCLUSIVE lock → dies at the 4 s
busy_timeout → **crash-loops** for the whole build (`Restart=on-failure`,
`RestartSec=30`). Reorder to: **stop collector → build indexes → checkout code →
start collector.** Stopping first is strictly safer and costs nothing.

## V4 — THE DEPLOY CANNOT EXECUTE AS WRITTEN, AND SUNDAY IS WORSE (SEVERE)
The VPS has **no git remote and no upstream** (`git remote -v` empty;
`master@{upstream}` fatal). Local `origin` = `ssh://root@…/home/racing/…` — this
is a **push-to-VPS** model. So `git fetch --all` is a no-op and
`git checkout s260-resilience` fails `pathspec did not match`.
**The same defect is latent in `scripts/deploy_phase1.py:326`, which runs
`git pull --ff-only`** — it would fail, and the script's own order (stop → pull →
migrate → start) means the abort at `:317` **leaves the collector DOWN**, on a
Sunday, unattended. This survived two prior reviews.
**Fixes:** tonight = local `git push origin s260-resilience`, then VPS
`git checkout s260-resilience`. Sunday = merge `s260-resilience` into `master`
locally **first** (master must contain both sets of SHAs, or Sunday silently
reverts tonight), `git push origin master`, and replace `deploy_phase1.py`'s pull
step with `git checkout master` + an explicit SHA assertion. **Add a
restart-on-every-failure-path guard to `deploy_phase1.py` as well** — the same
class the S260 implementation review already fixed once.

## V5 — THE NIGHTLY BACKUP COLLIDES WITH THE REPAIR, EVERY NIGHT (SEVERE)
`racing-backup.timer` = 05:00 ACST (19:30 UTC) — dead centre of both the §9 repair
window and the deploy window. `scripts/backup_db.sh` uses `sqlite3 ".backup"`,
and **SQLite's backup API restarts from page 1 on every source write**. A repair
committing every ~0.3 s for 30 min means the 5.2 GB backup never converges, or
fails locked (`set -euo pipefail` → unit fails). Step 1's `is-active
racing-backup` check passes only because the backup has not started yet.
**Fix:** repair timer to **05:05 ACST with `--deadline 05:45`**, and add
`racing-backup.service` to the A6 refusal set.

## V6 — a third shared file with Phase 1 — **CONFIRMED, and now resolved in §6.3**
`scripts/liveness_check.py` is **not** in §6's two-file list, and Phase 1 rewrites
it heavily (+170 lines). A3 edits its capture-silent check. Cherry-pick A3's
liveness hunk separately and **expect a conflict**. §6's independence claim must
be proven **by build, not assertion**.
**Round 2 (F2): V6 was right.** The conflict is real, it presents with an EMPTY
HEAD side and 172 incoming lines of which only ~30 are A3, and "take theirs"
imports Phase 1's country-census block onto a non-Phase-1 base. §6 has been
rewritten with the exact keep/drop and a three-`grep` check. The build has now
been performed: **451 green on `f50d4b2`.**

## V7 — a moderately-slow repair slips both gates (confirmed attack)
`--max-lock-ms 2000` means 1.5 s/merge never trips the 10-consecutive abort; with
`--sleep-between 0.25`, 5,800 × 1.75 s ≈ **2.8 h**, so the deadline truncates at
~3,200 markets *after* starving capture past window close.
**Fix:** add an **aggregate-rate abort — stop if throughput falls below 1
market/s averaged over any 200-market block** — in addition to the per-merge
watchdog.

## V8 — liveness is blind for the whole operation
`liveness_check.py:1045-1049` skips **all** capture-side checks inside 03:55–06:05
ACST. A collector wedge at 04:30 is invisible until 06:05, then needs two
consecutive runs → first restart ~06:30. **Fix:** step 7's concurrent
`journalctl | grep locked` must be a **scripted hard abort**, not an eyeball.

## V9 — rollback leaves the timers armed
§8's "point of no return: none" is wrong: step 6 installs units into
`/etc/systemd/system/`, and `git checkout f50d4b2` reverts the code while leaving
them armed — firing an unpaced repair, or one whose new flags no longer parse.
**Rollback MUST include `systemctl disable --now racing-twin-repair.timer
racing-collector-restart.timer`.**

## V10 — smaller corrections
- **§4 evidence is wrong, urgency higher:** the Zulu format is **44,632 rows
  spanning 2025-03-02 → 2026-07-30**, not "every such row is dated 2025". The
  `api/routes/races.py:74-75` fix is more than hygiene.
- **§A2 rationale is per-write, not per-tick:** `_process_all_races` is serial, so
  k stalled writes cost k×4 s and can exceed the 20 s final-snapshot window. Say
  "per stalled write" in the comment; the A4.4 watchdog is the real backstop.
- **`_retired` needs a code split:** `orchestrator.py:628-655` pushes
  COMPLETE/TIMEOUT **and** `sqlite3.IntegrityError` into one `completed` list.
  §B2's "do not add on the IntegrityError path" requires splitting it, or either
  the infinite-loop fence or the forced re-discovery breaks.
- **Backup path in step 2 is wrong:** backups live at
  `data/backups/` (`capture_20260730.db`, 5.2 GB), not `/home/racing/backups/`.
  Also the day's backup runs at 19:30 UTC, so before then "today's backup"
  legitimately does not exist — an agent must not read empty output as a pass.
- **Step 7 deadline** must be 05:45, not 06:00 (05:50 identity sweep is a second
  merge writer). **SUPERSEDED by F3: it is 05:38 with `--sleep-between 0.1`.
  05:45 was still too late — the post-loop orphan scan runs AFTER the deadline
  break.**
- **WAL:** `wal_autocheckpoint = 0` + PASSIVE-only cannot reclaim frames while the
  collector holds a read snapshot, so the WAL grows monotonically across 5,800
  merges. Disk survives (24 G free) but **add a WAL-size abort**.
- **Check on the side:** `local_race_date` already exists on live — confirm that
  is Phase 0 and not a partly-run Phase 1 migration.

## Confirmed-correct by review (do not re-litigate)
`near_races()` datetime handling is safe and the write-up's claim against it is
refuted; `_register_race` really does accept the DB-row subset and
`fetch_date()` falls back correctly for stale cards; `merge_recent_twins` cap=25
is safe (4,548 twin groups since 1 May, 3 sweeps/day = 75/day clears steady
state); `MAINTENANCE_WINDOW_END` is consistent in both copies; disk is adequate
and `backup_db.sh` prunes before writing; `api/routes/races.py` genuinely does not
overlap Phase 1; the liveness self-heal cannot fire during the index build;
collector write failures log-and-continue rather than wedge.

---

# v3 — Adversarial review round 2: six fixes (NORMATIVE over v2 where they conflict)

Round 2 attacked the *implementation*, not the plan, and found the deploy gate
itself broken. Fixed in `racing-data-capture` `52b4382` (548 → 555 tests) and in
this document.

## F1 (BLOCKER) — the deploy branch could not be proven green
`tests/test_capture_resilience.py` patched
`capture.orchestrator.learned_venue_countries` — an **international Phase 1**
symbol. `mock.patch.object` raises `AttributeError` on a missing attribute, so on
the `f50d4b2` base the VPS actually runs, the test **errored**. The single gate
§6 calls "buildable proof, not a claim" could not be executed. Fixed with
`create=True` (patches the real symbol where it exists, inert where it does not;
the assertions are unchanged and meaningful on both bases). The whole new test
file was swept: this was the only Phase-1-only symbol, proven by building the
branch rather than by reading.

## F2 (BLOCKER) — §6 was dishonest and its resolution was dangerous
Rewritten in place. Three shared files, not two; `scripts/liveness_check.py`
conflicts and that is EXPECTED; the exact keep/drop is recorded with a
three-`grep` check; and `7669997` is named as a Phase-1-only commit that must
**not** be cherry-picked. See §6.

## F3 (MAJOR) — the repair deadline budget was too thin
`--deadline 05:45 --sleep-between 0.25` spent 29 of a 40-minute window in the
loop and then ran `TRUNCATE` + `verify_no_orphans` + a second `find_twin_markets`
**after** the deadline break, landing 05:47–05:49 against the 05:50 identity
sweep. Now **`--deadline 05:38 --sleep-between 0.1`**: loop 14.5 min, 18.5 min of
slack for yields (`hot_races()` is 5, and a yield costs up to 120 s), post-loop
done by ~05:41, ≥9 min clear. Full table in §9; the arithmetic is also a comment
block in the service unit, where the operator will actually meet it.

## F4 (MAJOR) — a deadline-truncated run exited 0 and logged DONE
The deadline `break` set no flag, so a run that yielded away 39 of its 40 minutes
logged `DONE` and a remaining count — and §10 pre-authorises a non-zero
remainder, so nothing in the morning log distinguished "finished" from "ran out
of time". Now: `INCOMPLETE` in the log and **exit 75**. `SuccessExitStatus=75` in
the unit keeps it a normal resumable outcome for systemd (and `Type=oneshot` with
no `Restart=`, timer-fired, cannot loop on any exit code); exit 1 stays a real
failure. Two `INCOMPLETE` nights in a row = the F3 budget is wrong.

## F5 (MODERATE, live) — rehydration could double-track a physical race
The only duplicate guard was `_find_tracked_market(betfair_win_market_id)`, and
`_find_tracked_market(None)` is `None` **by construction** — so a twin pair in
which one row never got a market registered **twice**, two trackers writing
bookmaker snapshots to two race rows for one race. With ~5,800 twins unrepaired
this was live. New `_find_tracked_race` guard.

**One deviation from the review, recorded.** The review specified the key
`(venue_normalised, race_number, race_date)`. That key alone is **vacuous**:
`races` carries `UNIQUE(race_date, venue_normalised, race_number)`, so two ROWS
can never collide on it — it is exactly why the pre-reset collision valve
(`'mount gambier|greyhound'`) exists. Real twin rows must therefore differ on
venue **or** on card date. The guard implements the specified key as a fence
against duplicate registration from any other source, **and** adds
`(venue, race_number, scheduled_start)` across differing card dates — which is
the live DR-036 twin shape (one race, two `race_date` stamps from the venue
timezone mis-stamp) and the class the market guard actually misses. A venue
cannot run two different races with the same race number at the same instant, so
false-collapse risk is nil; two genuinely different races at one venue on two
cards differ in `scheduled_start` and both keep tracking (tested).

## F6 (MINOR) — the lock-guard start race
Runbook step 8 backgrounds `repair_lock_guard.py` on the line **before** the
repair, and `watch()`'s first act was `repair_is_running()` — False for the second
or two before the repair's process exists. The guard logged "nothing to guard",
exited 0, and the repair ran unwatched all night. Fixed **in the script**, so no
ordering can bite: `wait_for_repair()` waits a bounded 30 s (`--startup-grace`)
for a repair to appear. Step 8 now says why the guard goes first.

## Verification actually performed (this is the gate that failed last round)
* `uv run pytest` on `master` → **555 passed**.
* Scratch worktree at `f50d4b2`, cherry-pick `fed12c6` (one expected conflict in
  `scripts/liveness_check.py`, resolved per §6.3) + `52b4382` (clean),
  `uv run pytest` → **451 passed, green**. Worktree and branch removed afterwards.
* Nothing pushed. Nothing deployed. The VPS was not touched.
