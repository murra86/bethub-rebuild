# Morning odds sweep — build report (S255, 26 Jul 2026)

**Status: BUILT, DEPLOYED, REVIEWED, SMOKE-TESTED ×2. Runs DAILY
(operator-directed, widened from the brief's Saturdays-only v1). Not
yet live-proven** (S189 taxonomy) — first unattended live morning is
**Monday 27 Jul**; the full-card proof and formal §4 acceptance is
**Saturday 1 Aug**. Nothing more needs to be done before then.

## What this means for the betting day

From tomorrow morning, the system records what every bookmaker and
Betfair are quoting **from 6am**, hourly, every day, for the whole
thoroughbred card — the part of the day that until now was completely
invisible (the capture previously saw nothing earlier than one hour
before each race). After 2–3 Saturdays there is enough data for a
coarse answer to "does placing a promo bet calmly in the morning cost
me money or save it?"; 8–12 gives the full answer. Daily capture also
covers the operator's regional/low-activity-day trend question for
free — weekday country cards are in scope by construction — and feeds
the S252 morning-market accuracy question and the account-health
timing angle.

Cost: roughly doubles each day's scraping volume on the books (weekday
cards are smaller, so weekdays add less in absolute terms).
Protections: hourly-not-minutely, one-hour safety margin from the
collector's own window re-checked at every single request, TAB on its
own isolated connection identity, a failing book is dropped for the
rest of that hourly run automatically, and a permanent per-book kill
switch exists in the script config. Nothing about the existing
race-hour capture was touched; switch-off is one command (mask the
timer). Daily-vs-Saturday risk call: accepted because every failure
mode is per-book, per-run, and self-limiting, and the operator holds a
monitoring session open.

## What landed (capture repo `racing-data-capture`)

- `8645e08` — `scripts/morning_sweep.py` (standalone one-shot, identity-
  sweep pattern) + `deploy/systemd/racing-morning-sweep.{service,timer}`
  + `tests/test_morning_sweep.py` + a `pool` parameter on `discover_tab`.
- `054c2e5` — stale/incomplete day-map re-discovery valve (found via
  smoke test, below).
- `6dfa987` — timer widened to DAILY (operator-directed) + all fixes
  from the adversarial review (next section).
- All deployed to the VPS (push-to-origin `updateInstead`), timer
  installed + enabled. **Next fire: Mon 27 Jul 06:00–06:02 Adelaide**,
  then hourly through 17:00, every day.
- Tests: 184 pass (144 existing + 40 new); zero regressions.

## Adversarial review (operator-directed finalization pass)

An independent reviewer swept the finished script against the real
helpers it calls. Nine findings; the five real ones are fixed in
`6dfa987`, re-tested, and re-smoke-tested:

1. **CRITICAL — writer-lock held across network waits.** The shared
   batch savers commit *before* their coverage updates, leaving an open
   write transaction; the sweep would have held SQLite's single writer
   lock through staggers and HTTP fetches (a TAB hunt can run minutes),
   able to starve the live collector's writes mid-window. Fixed: the
   sweep commits immediately after every batch save and before close.
2. **Day cache died after hour 1.** JSON stringifies race-number keys;
   reloaded maps never matched sqlite's integer race numbers, so races
   not captured in hour 1 would never be retried — the exact late-
   appearing races the hourly cadence exists for. Fixed on load +
   round-trip test.
3. **Betfair-market twins (S252: ~63% of markets sit on TWO race
   rows).** Every twin would be fetched twice per book per hour and
   Betfair rows landed on an arbitrary twin. Fixed: targets deduped by
   market id (keep the row with more stamped book ids, then the older).
4. **Cross-code identity guard added.** TABtouch's schedule page
   carries dogs/harness links with no type filter — a colliding
   venue+number id could have stamped a greyhound race id onto a horse
   race permanently and written junk runners. Now every fetched card
   must share ≥50% of its runner names with the race's known (Betfair-
   stamped) runners before anything is written or stamped; stamping
   moved to after-verification.
5. **T−75m margin re-checked per request** (it was only checked at run
   start and eroded over a long pass), TAB 404s now pace like real
   requests and reset the failure streak, per-book crash containment so
   one book's failure can't kill the run, `Wants=network-online.target`
   on the service.
6. **Watchdog sharpened, not dulled:** liveness freshness now ignores
   MORNING rows (with a safe fallback), so the sweep can never mask a
   wedged collector during the morning. This is the one change outside
   the sweep itself — one WHERE clause in `liveness_check.py`, pinned
   by two new tests.

Accepted residual gaps (deliberate): the identity guard fails open on
thin evidence (<3 known or fetched names); snapshot tuple shapes vs the
savers are verified by review but not pinned by a test; the guard and
margin re-check live in network-path code exercised by the Saturday
acceptance rather than unit tests.

## Design as built (deviations from brief §2 flagged)

Per brief: races >T−75m only; `snapshot_phase='MORNING'` on the existing
snapshot tables; TAB on its own `"morning"` hunt-and-pin pool (404 =
not-served, no hunt); overround >150% guard replicated; NO
`snapshot_batch_summary` writes; own DB connection (timeout 30 /
busy_timeout 30000), chunked writes; no orchestrator/timer/watchdog
changes. §2.5 decision: **stamp discovered book race ids** — taken, but
via guarded fill-if-null UPDATE on the race row rather than
`upsert_race` (nothing else on the row can move). Bonus: the nightly TAB
history harvester keys off `tab_race_id`, so morning stamping widens its
coverage for free.

Deviations (all judged safe, listed per §7):
1. **"No odds yet" writes no rows** (brief implied write-what-comes):
   a race the book serves but hasn't priced is counted per book
   (`no_prices_yet`) and retried next hour. All-NULL odds rows carry no
   information; the per-book publish-time table derives from each race's
   first PRICED row, which is unaffected.
2. **Soft deadline 50 min/run**: with ~880 fetches at 2–3.5s pacing a
   full-card pass fits, but a pathological run stops starting new work
   at 50 min so hourly fires never pile up. Skips are counted
   (`deadline_skipped`).
3. **Same-book pacing 2–3.5s** (harvest_tab_history precedent) rather
   than the collector's 2–5s cross-book stagger — the same-book axis is
   the one that matters here; keeps a full pass ~40 min worst case.
4. **Per-book run-drop after 3 consecutive failures** (brief allowed
   "simple backoff"), plus `SWEEP_DISABLED_BOOKMAKERS` config set as the
   permanent per-book kill switch (§5 allow→flag→review).

## Live crontab/timer inventory (brief §5, report-don't-fix)

- **Crontabs: empty.** root and racing have none; `/etc/cron.d/
  racing-capture` exists but all three legacy lines were deleted at S238
  W4 (comment in the file records why).
- **Everything runs on systemd timers:** liveness (15-min),
  identity-sweep (05:50/10:20/15:20 Adelaide), collector-start,
  calibration, tab-history-harvest (22:45 ACST), metadata-backfill,
  backup, health-check — and now morning-sweep.
- **The 08:25-vs-9:00 collector-start question: resolved, live box wins.**
  `racing-collector-start.timer` starts the collector at **08:30
  Adelaide** daily. The repo's `deploy/cron.d/racing-capture` line 6
  (23:30 UTC = 9:00 ACST cron start) is stale history — that cron line
  no longer exists on the box. NOT fixed (separate concern); the repo
  deploy folder still doesn't carry all the live units. Sweep margin
  maths used T−75m and doesn't depend on collector start time anyway.

## Smoke test (26 Jul, on the box, as user `racing`)

1. **Today's date (Sunday evening):** 64 stamped thoroughbred races, 0
   still pre-window → clean no-op, exit 0. Correct.
2. **Monday's card (full path):** 10 pre-window races found. Betfair:
   10/10 markets returned, **149 MORNING rows at T−951m..T−1221m — the
   first pre-window prices the store has ever held**. TAB: pinned its
   own AU session on the `morning` pool (2 tries), discovery 5 venues,
   8/10 races priced (121 rows), 10 `tab_race_id`s stamped. TABtouch:
   same shape (121 rows, 10 ids). Overround guard rejected 4 genuinely
   junk night-before books (TAB/TABtouch Ballarat R8+R9 at 155–160%).
   Other six books: `no_id` — they don't list Monday's meetings on
   Sunday night; expected, and the case that motivated the map-staleness
   valve in `054c2e5` (an early map now re-discovers next hour).
   Runtime 120s. Log `logs/morning_sweep.log`, ownership `racing` ✓.
   Smoke residue: Monday MORNING rows kept (real data, phase-tagged);
   test day-cache file removed.
3. **Post-review double run (Monday's card again, final code):** two
   consecutive runs clean — second run reused the on-disk day cache
   (TAB + TABtouch fetched 8/8 with no re-discovery), the re-discovery
   valve correctly dropped the three books that don't list tomorrow
   yet, overround guard consistent (Ballarat R8/R9 at 155–160%),
   identity guard armed with zero false rejections, ~2 min runtime.

## First live morning (Mon 27 Jul) — two real defects caught and fixed

The timer fired on schedule from 06:01 Adelaide; all runs completed and
all 8 books swept. Oversight found two data gaps, both fixed and
verified live by ~09:15:

1. **Betfair morning prices were 0 for the first three runs** — a
   latent bug in the shared client, not the sweep: `get_market_books_
   batch` split requests at 40 markets against Betfair's 200-point
   weight cap, but its own price projection costs 20 points/market, so
   any batch over 10 markets failed whole ("rate limit"/TOO_MUCH_DATA).
   The 10-market smoke test had sat exactly at the cap. Nothing else
   ever called this helper with >10 markets. Fixed to 10/request
   (`7ad7425`); verified 17/17 markets, 229 rows. Cost of the gap:
   Betfair rows for 06:00–08:00 Adelaide today only (book side was
   unaffected, and the Betfair morning anchor is retrospectively
   backfillable from Data Portal per the brief).
2. **Six corporate books missed all 10 Ballarat races** — today's
   meeting runs on the synthetic track: those books list "Ballarat
   Synthetic" while Betfair (the race rows' naming authority) says
   "Ballarat", so the venue-keyed day map never matched. Fixed by
   aliasing surface suffixes (synthetic/poly/polytrack) in the day map
   (`93b171e`); verified all 8 books now fetch 17/17, and the identity
   guard confirmed the aliased cards are the right races before their
   ids were stamped. **Side-finding for the data reset / S252 twin
   investigation:** this same suffix class is a plausible generator of
   twin race rows (book-named row vs Betfair-named row) — logged here,
   not chased in this session.

Observation, no action: each hourly run is a fresh process, so TAB
hunts+pins a new session per run (~2–4 extra requests, a routine
"fingerprint rotated" WARNING each time). Harmless at this cadence;
persisting the pin in the day cache is a v2 nicety.

## Acceptance — OPEN until Sat 1 Aug (brief §4)

To run after the first swept Saturday (fits the Saturday race-day
sitting, S255 queue item 3): per-bucket coverage ≥90% of stamped
thoroughbred races per source; TAB morning odds present for
promo-relevant races, no hunt-storm signature, collector's own TAB
window unaffected; collector row counts + alert behaviour comparable to
prior Saturdays; the per-book morning publish-time table (§B.4
deliverable). Only after that does this become **live-proven**.

## Open items / notes

- **No alerting on the sweep itself** (v1): if a Saturday run fails, the
  evidence is `logs/morning_sweep.log` + `journalctl -u
  racing-morning-sweep`, not an email. Operator call whether to add a
  liveness line later.
- Sweep runs daily; manual runs any time:
  `venv/bin/python3 scripts/morning_sweep.py [YYYY-MM-DD]`.
- First unattended morning is Mon 27 Jul — worth a glance at
  `logs/morning_sweep.log` during the open monitoring session.
- Disable = `systemctl mask racing-morning-sweep.timer` (brief §2.7).
- Analysis explicitly out of scope; re-commission the early-placement
  study once ≥2–3 swept Saturdays exist.
