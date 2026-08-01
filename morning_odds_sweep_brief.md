# Build brief — Morning odds sweep (capture-side)

**Authored:** planning-only Code session, 26 Jul 2026 (follow-up to the
early-placement gate stop — `bethub-analytical/analysis/early_placement/odds_drift_report.md`).
**Executor:** a formal bethub-v3 session (capture-side work on the VPS).
**Status:** PLANNED — nothing in this brief has been executed. No code,
config, or VPS state was touched in the planning session.

Read the whole brief before editing any file. The §1 facts were derived
from the current `racing-data-capture` checkout (clean tree at `e0e39a1`,
up to date with origin) and from read-only queries against the live
`capture.db`; paths:lines are cited so the executor can re-verify fast.

---

## 0. What we're building and why

Today the capture starts at T−60m — empirically, across 11.1M snapshot
rows since March, **not one price exists earlier than 60.0 minutes before
jump, from any source**. That made the early-placement study (does a
promo bet placed at 10am still pay?) unmeasurable, and it also blinds us
to the morning market S252 showed carries the single biggest accuracy
gain (7.8 pts at T−30m).

This build adds a **sparse morning sweep**: hourly captures of bookmaker
fixed odds (win + place) and Betfair prices for the day's thoroughbred
races, from 06:00 Adelaide until each race enters the collector's
existing T−60m window. Same database, same tables, new
`snapshot_phase='MORNING'`.

Operator context that shapes the design:
- **Most promo bets are currently placed at TAB** → TAB's morning odds
  are the primary "locked price" series. The other books matter as the
  ≥3-book consensus anchor (and as locked prices if promo placement
  widens later).
- The Betfair morning side gives the probability anchor; note it can
  also be backfilled retrospectively from Data Portal files (S252's
  `morning_wap`), so the *book* side is the calendar-critical half.
- Analysis is a separate later session. This build only makes the data
  exist. ~2–3 Saturdays of capture gives a coarse answer; ~8–12 gives
  the full stratified study.

## 1. What exists today (grounded facts — do not rediscover)

- **The T−60m gate is the phase machine, not the scrapers.**
  `RaceState.current_phase()` returns PENDING while
  `mts > STANDARD_CAPTURE_WINDOW (60)` (`capture/scheduler.py:101-122`,
  `config/settings.py:19`). The scrapers themselves are time-agnostic.
- **The collector process only starts at 9:00 Adelaide** (cron
  `30 23 * * *` UTC, `deploy/cron.d/racing-capture:6`). NOTE:
  `scripts/liveness_check.py:73` references an 08:25/08:30 start via a
  `racing-collector-start.timer` that is **not in the repo's deploy/
  folder** — the committed deploy config is not the full picture of the
  live box. **First task of the build session: inventory the live
  crontab + systemd timers before changing anything.**
- **Race rows already exist by ~05:50 Adelaide** with `scheduled_start`,
  `betfair_win/place_market_id` and runner `betfair_selection_id`: the
  identity sweep (`scripts/identity_sweep.py`, systemd timer at
  05:50/10:20/15:20 Adelaide, +26h lookahead window) INSERTs and stamps
  them. The Betfair half of a morning sweep is therefore ready-made.
- **Bookmaker race ids are NOT stamped in the morning** — only the
  collector's own 30-min discovery fills `ladbrokes_race_id` etc., and
  it can't run before the process starts. A morning sweep must run the
  per-book `discover_<bk>(date_str, proxies)` calls itself
  (`bookmakers/base.py:14-77` registry; per-race fetch signatures vary —
  TAB takes `(date_str, venue_code, race_number, pool=...)`, see the
  dispatch shapes in `capture/orchestrator.py:822-860`).
- **A second writer process is established practice.** identity_sweep
  opens its own connection with `timeout=30` + `PRAGMA
  busy_timeout=30000`, writes in 50-row chunks/short transactions
  (`scripts/identity_sweep.py:312-334,439-440`); all snapshot writers in
  `storage/database.py` are duplicate-safe (INSERT OR IGNORE /
  IntegrityError-swallow). WAL is on.
- **`snapshot_phase` is unconstrained TEXT** on both snapshot tables; the
  only values ever written are STANDARD / INTENSIVE / POST_START; no
  reader anywhere filters or validates phase, and nothing caps
  `minutes_to_start` (plain REAL, no CHECK; computed signed at
  `capture/scheduler.py:91-95`). `'MORNING'` collides with nothing.
- **`snapshot_batch_summary` has NO phase column**
  (`storage/database.py:190-201`) — morning batches would silently blend
  into completeness/overround aggregates. See design decision §2.6.
- **Watchdog/health checks don't mind early rows** (verified against
  `scripts/liveness_check.py` / `scripts/health_check.py`): staleness
  checks key off `MAX(snapshot_time)` (early rows can only help), the
  per-book NEAR-window check ignores anything outside ±60m, and stamped
  coverage only checks races jumping within 2h. No dashboards read
  phase or `minutes_to_start`.
- **TAB transport is special and hardened** (`bookmakers/tab.py:1-180`):
  Decodo AU residential + curl_cffi fingerprint rotation, hunt-and-pin
  per session **pool** (`"collector"` / `"live"`), 404 = race-not-served
  (never a block, never a hunt — the S250 fix), shared hunt breaker with
  120s cooldown. `scripts/harvest_tab_history.py` is the precedent for a
  standalone script using **its own sessions so it never touches the
  pinned pools** (`:16-18,32`).
- **Betfair REST is cheap in batch**: `get_market_books_batch()` splits
  at 40 markets/request against the 200-point weight cap
  (`betfair/client.py:29-30,315-339`). A whole Saturday card is ~3
  requests per sweep.
- **Data-quality guards live in the orchestrator, not the writers**: the
  overround >150% rejection and the Entain runner-count staleness guard
  are internal to `_take_bookie_snapshots`
  (`capture/orchestrator.py:748-771`) — a standalone script bypasses
  them unless it replicates them.

## 2. Design (proposed; deviations welcome if the executor finds better)

1. **Shape: standalone one-shot script + its own systemd timer**, on the
   identity-sweep pattern. `scripts/morning_sweep.py` +
   `deploy/systemd/racing-morning-sweep.{service,timer}`. Do NOT extend
   the orchestrator's phase machine — the collector isn't even running
   for most of the morning window, and the sweep must not add risk to
   the proven in-window capture.
2. **Schedule:** hourly, 06:00→17:00 `Australia/Adelaide` (timer
   `Timezone=`, DST-proof), **Saturdays only in v1**
   (`OnCalendar=Sat ...`). Each run captures only races with
   `minutes_to_start > 75` (margin so the sweep never overlaps the
   collector's window; the last pre-window point for every race
   therefore lands at T−75m..T−135m, and the T−2h→T−60m study bucket is
   fed by the collector's own T−60m start plus the last sweep pass).
   Races whose Betfair market is missing (outage-window races) are
   skipped and counted, not errored.
3. **Scope:** all AU thoroughbred races for the local racing day that
   carry a stamped Betfair win market id (identity sweep provides these
   by 05:50). Greyhounds/harness excluded. The study filters to metro
   later; capturing the full thoroughbred day costs little extra and
   TAB promos are not metro-only.
4. **Per run:**
   - Betfair: one `get_market_books_batch` over the day's pre-window
     market ids → `save_betfair_snapshots_batch` with
     `snapshot_phase='MORNING'` (prices, sizes, `total_matched`, sp_near
     /far, runner_status — runner_status gives us morning scratchings
     for free).
   - Books: on the first run of the day, call each enabled book's
     `discover_<bk>(today)` once and persist the venue/race→book-id map
     to a small on-disk day cache (JSON in `data/`, not the DB);
     subsequent runs reuse it (re-discover a book only if its fetches
     404 in bulk). Then per pre-window race per book:
     `fetch_<bk>` → `save_bookmaker_snapshots_batch`
     (`snapshot_phase='MORNING'`), honouring the existing 2–5s stagger
     and per-book circuit-breaker semantics (a simple per-book
     consecutive-failure backoff is acceptable in v1; do not silently
     hammer a blocked book for the whole card).
   - **TAB uses its own session pool** (`pool="morning"` or
     harvest-style own sessions) — never the collector's or live route's
     pinned sessions. 404 stays not-a-block.
   - Replicate the overround >150% guard from
     `_take_bookie_snapshots` before writing book rows (morning books
     are exactly where junk quotes are most likely).
   - Own DB connection: `timeout=30`, `busy_timeout=30000`, chunked
     short transactions (identity-sweep pattern).
5. **`races` writes:** none in v1 except optionally stamping the
   discovered bookmaker race ids via the existing `upsert_race` path so
   the 9am collector inherits them. This is the one v1 decision the
   executor should make on the ground: if `upsert_race` is cleanly
   reusable, stamp (it removes duplicate discovery work and makes the
   day cache recoverable from the DB); if it drags orchestrator coupling
   in, skip — the day cache alone suffices.
6. **`snapshot_batch_summary`: do NOT write morning batches in v1.** The
   table has no phase column, so morning rows would contaminate
   completeness/overround aggregates that existing checks read. Adding a
   phase column is a schema migration on a live 5GB DB — out of scope
   for v1; note it as a follow-up if batch-level morning bookkeeping is
   ever wanted. The snapshots themselves carry the phase.
7. **No changes to:** the orchestrator/phase machine, poll intervals,
   the identity sweep, the watchdog, or any existing timer/cron. The
   sweep is purely additive and can be disabled by masking its timer.

## 3. Sizing (from live-DB counts, 26 Jul)

A full AU Saturday thoroughbred card is ~90–110 races. Hourly sweeps
06:00→windows-open average ~6–8 passes/race:

| | fetches/Sat | new rows/Sat |
|---|---|---|
| Bookmakers (8 books) | ~5,000–6,500 | ~50–65k |
| Betfair (batched) | ~25–35 requests | ~8–10k |

Context: current bookmaker ingest is ~49k rows/day, so a Saturday with
the sweep roughly doubles book-row volume for that day only. Storage is
trivial against a 5GB DB. The real cost is **scraper exposure** (more
hits per book per day) — mitigated by hourly-not-minutely cadence,
existing stagger/backoff, TAB pool isolation, and Saturdays-only scope.

## 4. Verification & acceptance (first swept Saturday)

1. `MAX(minutes_to_start)` > 60 in both snapshot tables, phase
   `'MORNING'` present, and per-bucket row counts (T−8h+ … T−60m) non-
   zero for ≥90% of Betfair-stamped thoroughbred races — per book and
   for Betfair. (The gate queries from the odds-drift report §B.2 are
   the template.)
2. TAB specifically: morning odds present for the races the operator's
   promo screen would care about; no hunt-storm signature in the sweep
   log; collector's own TAB capture unaffected in its window.
3. Non-interference: collector in-window row counts and RACING ALERT
   behaviour comparable to prior Saturdays; no new alerts attributable
   to the sweep; backup size growth as sized above.
4. Honest classification per the S189 taxonomy: the sweep is
   **live-proven** only after (1)–(3) pass on a real Saturday.

## 5. Risks / open items

- **Deploy-folder vs live-box drift** (§1): verify the real crontab and
  timer set on the VPS before adding the new timer; reconcile the
  08:25-vs-9:00 collector-start question while there (report it, don't
  fix it — separate concern).
- **Morning book availability is unknown** — it's exactly what we've
  never observed. Some books may not publish fixed win+place odds at
  06:00. The sweep must treat "no market yet" as a normal per-race,
  per-book outcome (counted, reported in the log, retried next hour) —
  and the first Saturday's report should include the empirical
  publish-time table per book, which is itself a §B.4 deliverable the
  study needs.
- **Cloudflare/stealth:** doubled Saturday volume on the scraped books.
  If a book starts blocking under sweep load, drop it from the sweep
  (per-book disable set in the script config) rather than risking the
  in-window capture. Allow → flag → review later.
- **Scratchings/deductions:** morning Betfair `runner_status` improves
  the scratchings timeline, but Rule 4 deduction data still doesn't
  exist anywhere — the study's §8.2 stays unanswerable; nothing in this
  build pretends otherwise.
- **DST:** timer timezone-pinned; `minutes_to_start` is UTC-computed
  from `scheduled_start` and immune.

## 6. Explicitly out of scope

- The analysis itself (re-run of the early-placement commission once
  ≥2–3 swept Saturdays exist — separate session, separate brief).
- Betfair Data Portal retrospective joins (anchor-side backfill).
- The four uncaptured books (BetRight, Betr, PalmerBet, Dabble).
- Any schema migration (incl. batch-summary phase column).
- Collector refactor, cadence changes, or touching the placings
  backfill.

## 7. Report

Deliver `morning_odds_sweep_report.md` in bethub-rebuild: what landed,
the live crontab/timer inventory, first-Saturday acceptance numbers
(§4), the per-book morning publish-time table, per-book fetch/error
counts, and honest live-proof classification. Flag any deviation from
§2 with reasoning.
