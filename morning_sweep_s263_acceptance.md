# Morning odds sweep — first-Saturday acceptance report (brief §4)

**Saturday under test: 1 Aug 2026** (first swept Saturday).
**Authored:** S263 governance session, 2 Aug 2026, read-only against the
live capture box and DB. Companion to `morning_odds_sweep_brief.md` (§4
criteria) and `morning_odds_sweep_report.md` (build report, S255).

**Verdict: §4 acceptance PARTIALLY MET.** Everything the sweep controls
passed; the strict "every time-bucket covered for ≥90% of races, for
every bookmaker" bar is missed on the edge buckets by six of eight
books, for reasons that are now measured and understood (books that
publish later than 6am, one slow book running out of run time, and
safety checks correctly refusing suspicious prices). Formal S189
classification stays **live-operating, not yet live-proven** until the
operator either accepts the caveats below or one more Saturday passes
with the two small tune-ups.

---

## What Saturday's sweep means for the betting day (plain language)

- **The morning market is no longer invisible.** For all 104 AU
  thoroughbred races on Saturday's card, the system now holds hourly
  prices from 6:00am Adelaide — 78,745 price rows (69,600 bookmaker +
  9,145 Betfair) that simply did not exist on any earlier Saturday. The
  earliest prices sit at more than 14 hours before the jump.
- **TAB — the book the promo bets actually go to — delivered.** TAB
  morning prices exist for 100 of 104 races (all metro included);
  for 96 of them the first price was already captured on the 6:00am
  pass (median first capture 6:24am). This matches the promo-pilot's
  independent morning check on the day: 14/14 early races had
  full-field TAB prices by 7:20am.
- **The four TAB misses were a safety check working, not a failure:**
  all four are bet365 Hamilton races where TAB's own race id pointed at
  a card whose runners didn't match — the sweep refused to write
  rather than risk attaching the wrong race's prices (the exact error
  class the twin-row cleanup 0m is dealing with historically).
- **The race-hour capture was untouched.** Saturday's normal in-window
  capture volumes are level with (TAB: well above, thanks to the S257
  lag fix) the previous two Saturdays, no alerts fired, and the nightly
  backup grew by the predicted small amount.
- **One real payoff already banked:** Saturday was the operator-flagged
  "bet-earlier" day (recorded in
  `bethub-analytical/analysis/early_placement/strategy_days.md`). The
  morning prices behind those deliberately-early placements are now on
  record — the first strategy day that can ever be analysed against
  actual morning odds. Any future timing/EV analysis must segment
  1 Aug as a strategy day, not organic behaviour.
- **Confidence: HIGH** on everything above — every number below comes
  from the live database and the sweep's own logs, and the log-vs-
  database row counts reconcile exactly (69,600 = 69,600; 9,145 =
  9,145).

**Recommended next steps (operator call):**
1. Accept the report's caveats and treat the sweep as proven for TAB /
   Betfair / Ladbrokes purposes now — the promo-EV morning questions
   only need those — while the remaining books ripen; or hold the
   "live-proven" stamp for one more clean Saturday.
2. Two small tune-ups for a future code sitting (not urgent): rotate
   the book sweep order hour to hour (TABtouch is always last and lost
   ~9 races to the run's 50-minute time cap), and decide expectations
   for PlayUp (it simply doesn't list most races until late morning —
   57% coverage is the book, not the sweep).
3. Keep counting Saturdays: this is Saturday 1 of the 2–3 needed for a
   coarse early-placement answer, 8–12 for the full study.

---

## §4 criteria, one by one

### §4.1 — Phase present, pre-window depth, per-bucket coverage

- `snapshot_phase='MORNING'` present in both snapshot tables for the
  day: **yes** (69,600 bookmaker rows, 9,145 Betfair rows).
- `MAX(minutes_to_start)` > 60: **yes, by a wide margin** — Betfair
  T−860m, best book T−852m (previous all-history bound was exactly
  T−60.0m).
- Per-bucket row counts non-zero for ≥90% of Betfair-stamped
  thoroughbred races, per source: **met for Betfair and Ladbrokes on
  every bucket; met for all books except PlayUp/TABtouch on the middle
  buckets; missed on the edge buckets by six books.** Full table and
  the three structural causes in Appendix A2. Race-level coverage
  (≥1 morning row anywhere in the morning): Betfair, Ladbrokes, Neds,
  PointsBet, Unibet 104/104; Sportsbet 103/104; TAB 100/104; TABtouch
  95/104; PlayUp 59/104.

**Assessment: PARTIAL — pass in substance, miss on the strict letter.**

### §4.2 — TAB specifically

- Morning odds for the races the promo screen cares about: **pass** —
  100/104 races priced, every metro venue covered, median first
  capture 6:24am, corroborated independently by the promo-pilot's
  7:20am full-field check.
- No hunt-storm signature: **pass** — 24 "attempt blocked" lines
  across 12 runs = exactly the routine 2-try pin of a fresh hourly
  process (the build report's known observation), plus two transient
  proxy 5xx blips that self-recovered. TAB fetch errors for the whole
  day: 0.
- Collector's own TAB capture unaffected: **pass** — 27,861 in-window
  TAB rows vs 20,577 the previous Saturday (up 35%, the S257 lag fix;
  the sweep runs on its own isolated "morning" session pool).

**Assessment: PASS.**

### §4.3 — Non-interference

- In-window capture volumes level with prior Saturdays (Appendix A4).
- Alerts: zero alert lines in the liveness log for the window (and
  none elsewhere in the current log file); all 12 sweep service runs
  exited cleanly per the systemd journal; collector, identity-sweep,
  backup, health-check timers all fired normally on the day.
- Backup growth: 5.1 GB (31 Jul) → 5.3 GB (1 Aug), consistent with
  the brief's sizing of roughly-double book-row volume for the day;
  backup job reports OK.

**Assessment: PASS.**

### §4.4 — Honest classification (S189)

§4.1 does not pass on its strict wording, so the sweep remains
**live-operating, not yet live-proven**. Nothing observed on Saturday
was an unexplained failure; the machinery itself (12/12 runs, 8/8
books every run, guards live, zero unexplained gaps) behaved exactly
as designed. What flips it to MET: either operator sign-off accepting
Appendix A2's structural causes as out-of-scope for the sweep (they
are properties of the books and the deliberate T−75m margin), or a
repeat Saturday after the book-order/deadline tune-up clears the
TABtouch truncation — the only cause that is genuinely the sweep's own.

---

## The per-book morning publish-time table (§4 / study §B.4 deliverable)

First MORNING price captured per race, Adelaide time, Sat 1 Aug
(n = races with any morning price; "@6:00 pass" = priced on the first
sweep of the day). Capture time is an upper bound on true publish time
(hourly cadence + within-run book order shift books later; TABtouch
is always swept last).

| source | races | @6:00 pass | by 7am | by 8am | by 10am | earliest | median | latest |
|---|---|---|---|---|---|---|---|---|
| betfair | 104 | 97 | 97 | 97 | 104 | 06:00 | 06:00 | 09:01 |
| ladbrokes | 104 | 96 | 96 | 96 | 103 | 06:00 | 06:04 | 10:01 |
| neds | 104 | 96 | 96 | 96 | 104 | 06:07 | 06:12 | 09:15 |
| sportsbet | 103 | 95 | 95 | 95 | 103 | 06:15 | 06:18 | 09:20 |
| tab | 100 | 96 | 96 | 96 | 100 | 06:20 | 06:24 | 09:27 |
| pointsbet | 104 | 96 | 96 | 96 | 104 | 06:27 | 06:31 | 09:34 |
| unibet | 104 | 94 | 94 | 96 | 104 | 06:34 | 06:37 | 09:41 |
| tabtouch | 95 | 17 | 81 | 88 | 93 | 06:43 | 06:47 | 10:48 |
| playup | 59 | 36 | 36 | 36 | 52 | 06:40 | 06:42 | 11:38 |

Reading it: **by 6:45am on a Saturday, every book except PlayUp has
essentially its whole day priced.** The "latest" column is dominated by
seven races that only received their Betfair market ids between the
8:00 and 9:01 passes (see A1) — not late book publishing. TABtouch's
6:47 median is partly an artifact of being last in the run order.
PlayUp genuinely lists late and thinly. For the early-placement study:
a 10am placement is measurable against locked morning prices at every
book that matters; even a 6:30am placement is measurable at TAB,
Ladbrokes, Neds, Sportsbet.

---

## Appendix A — technical evidence

### A1. The day's card and targets

- `races` for 1 Aug: 104 AU thoroughbred (all 104 Betfair-stamped, 0
  trials/jump-outs) — the sweep-scope denominator; plus 86 AU
  greyhound and 56 AU harness (excluded by design) and 238 rows with
  no `racing_code`/market (internationals etc., out of scope).
- 13 venues: Rosehill 10, Townsville 9, Doomben 9, Flemington 9,
  Morphettville Parks 9, Newcastle 8, Aquis Park Gold Coast 8,
  Belmont 8, bet365 Hamilton 7, Darwin 7, Broome 7, Toowoomba 7,
  Gilgandra 6. First jump 10:55 ACST, last 20:20 ACST; every race was
  sweepable (≥1 pass before T−75m).
- Stamped-at-6am vs stamped-eventually: the first three runs saw 97
  races; 7 more (late Betfair-stamping, picked up around collector
  start 08:30) entered from the 09:01 run. These 7 depress the early
  bucket percentages for every source; the stated coverage numbers do
  not correct for this (conservative).

### A2. Run ledger and per-bucket coverage

12/12 hourly runs fired (06:00→17:01 ACST), all "Deactivated
successfully" in the journal, 8/8 books swept every run, zero ERROR
lines in the sweep log for the day:

| run (ACST) | targets | betfair rows | book rows | duration |
|---|---|---|---|---|
| 06:00 | 97 | 1,119 | 8,509 | 3001s |
| 07:00 | 97 | 1,119 | 8,601 | 3003s |
| 08:00 | 97 | 1,119 | 8,797 | 2926s |
| 09:01 | 104 | 1,184 | 8,881 | 3003s |
| 10:00 | 103 | 1,171 | 8,876 | 3001s |
| 11:00 | 93 | 1,059 | 8,022 | 2734s |
| 12:00 | 77 | 888 | 6,668 | 2234s |
| 13:01 | 58 | 669 | 5,086 | 1693s |
| 14:00 | 40 | 462 | 3,537 | 1131s |
| 15:00 | 19 | 204 | 1,657 | 587s |
| 16:01 | 10 | 100 | 575 | 235s |
| 17:01 | 5 | 51 | 391 | 144s |

Log-to-DB reconciliation exact: book rows 69,600 (log) = 69,600 (DB);
Betfair 9,145 = 9,145. Betfair batch: 800/800 markets returned across
the day, `login_failed=0, batch_failed=0` (the 27 Jul 10-market cap
fix holding at full-card scale).

Per-bucket coverage — races with ≥1 MORNING row in the bucket, over
races where the bucket was *feasible* (a pass existed in that bucket
before the race hit the T−75m margin; feasible n: T−8h+ 64, T−8h→−4h
104, T−4h→−2h 104, T−2h→−60m 77):

| source | T−8h+ | T−8h→−4h | T−4h→−2h | T−2h→−60m | ≥90% all buckets? |
|---|---|---|---|---|---|
| betfair | 94% | 99% | 100% | 99% | **yes** |
| ladbrokes | 92% | 99% | 100% | 94% | **yes** |
| neds | 88% | 99% | 100% | 88% | no (2pp short, edges) |
| pointsbet | 78% | 98% | 100% | 78% | no (edges) |
| sportsbet | 83% | 97% | 99% | 83% | no (edges) |
| tab | 83% | 96% | 96% | 79% | no (edges) |
| unibet | 75% | 98% | 100% | 82% | no (edges) |
| tabtouch | 70% | 89% | 91% | 79% | no |
| playup | 25% | 50% | 57% | 51% | no |

Three structural causes account for the edge-bucket misses; none is a
fetch failure:
1. **Publish/list timing** — a book that first prices a race at ~6:40
   (TABtouch median) or lists it mid-morning (PlayUp: 320 `no_id` +
   74 `no_prices_yet` outcomes on the day) cannot appear in the T−8h+
   bucket for early races, and the 7 late-stamped races (A1) were
   invisible to everyone before 09:01.
2. **T−2h→−60m is structurally narrow** — the sweep's deliberate
   T−75m margin leaves at most one pass in a ≤45-minute slice of that
   bucket, and races crossing T−75m mid-run are skipped by the
   per-request margin re-check (counted: `entered_window` 161 total,
   concentrated in late-order books: tabtouch 39, playup 36, unibet
   29, pointsbet 25). The collector itself owns T−60m onward; T−60..75m
   is a known, accepted by-design gap.
3. **The 50-minute soft deadline bit TABtouch** — the four full-card
   runs ran to the cap (3001s) and TABtouch, swept last, recorded all
   53 `deadline_skipped` outcomes on the day (its 9 missing races).
   This is the one cause that is the sweep's own; book-order rotation
   or a deadline bump is the v2 fix.

### A3. Guard activity (all writes-refused, none silent)

- **Overround >150% guard:** 16 rejections — Morphettville Parks R3
  rejected by four books across the first three passes (151–156%
  overround pre-open; priced sanely and captured from mid-morning),
  plus one-off early junk at Townsville R5 and Gilgandra R4–R6.
- **Cross-code identity guard:** 67 refusals covering 13
  race×book pairs, every one persistent across passes and none
  written: sportsbet→Gilgandra R1 (id `met_aus_432145597029/1`, wrong
  card all day); tab→bet365 Hamilton R1–R4 (TAB id `HPR/*` card
  mismatched Hamilton's runners); tabtouch→8 races (Flemington R1/R3/
  R6, Doomben R3, Morphettville R3, Rosehill R5/R7, Hamilton R1/R4 via
  `srm`/`mrx` ids). These fully explain the sportsbet/tab/tabtouch
  race-coverage gaps: **every non-PlayUp coverage miss on the day is a
  guard refusal, a late listing, or the deadline — zero unexplained.**
  (The Hamilton/HPR and venue-code collisions are live sightings of
  the same mis-label class the 0m twin review is cleaning up
  historically — the guard is doing for writes what 0m must do for
  history.)

### A4. Non-interference numbers

In-window (non-MORNING) snapshot rows, race_date = that Saturday:

| source | Sat 18 Jul | Sat 25 Jul | Sat 1 Aug |
|---|---|---|---|
| betfair | 27,938 | 34,896 | 39,861 |
| ladbrokes | 11,161 | 9,631 | 9,229 |
| neds | 10,983 | 9,620 | 9,243 |
| pointsbet | 11,161 | 9,714 | 9,339 |
| sportsbet | 11,024 | 9,219 | 9,266 |
| tab | n/a (started 20 Jul) | 20,577 | 27,861 |
| tabtouch | 10,267 | 23,855 | 24,561 |
| unibet | 9,589 | 8,332 | 8,245 |
| playup | 7,593 | 5,416 | 5,642 |

1 Aug is level with 25 Jul on every book (18 Jul predates the S257
TAB/tabtouch changes; Betfair growth is the S257/S260 pickup fixes).
No RACING ALERT signature in the liveness log for the window; sweep
runs consumed 2.2–31.8s CPU each (journal), trivial against the box.

### A5. Sources

All read-only: capture VPS `data/capture.db` (`snapshot_phase='MORNING'`
rows for `race_date='2026-08-01'`, thoroughbred, Betfair-stamped),
`logs/morning_sweep.log` (12 run blocks for sweep-date 2026-08-01),
`journalctl -u racing-morning-sweep.service` for the window,
`logs/backup.log`, `logs/liveness_check.log`, `systemctl list-timers`.
Bucket feasibility computed against each race's `scheduled_start` and
the actual run fire times. 1 Aug bet-earlier context:
`bethub-analytical/analysis/early_placement/strategy_days.md`.
