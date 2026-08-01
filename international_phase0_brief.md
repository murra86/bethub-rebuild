# International thoroughbreds — Phase 0 build brief (worklist 0p)

**Status:** PLANNING ONLY. No code written. Adversarial self-review at §11.
**Commissioned:** S259/S260, 30 Jul 2026, from
`international_thoroughbreds_assessment.md` §5 "Phase 0 — stop the bleeding".
**Repo:** `racing-data-capture` only. **bethub-v3 is untouched by Phase 0**
(one optional additive field on a racing-api response; no v3 build required).
**Evidence base:** live capture DB read-only (`mode=ro`, 30 Jul), collector +
liveness logs on the VPS, both repos at capture `c0abb2b`.

Operator decisions already locked and planned to: **D1** diet first, no plan
upsize · **D2** UK pilot, jurisdiction set is configurable data · **D3**
`country` as a plain column now · **D4** continuous operation + 04:00–06:00
Adelaide maintenance window · **D5** grow disk now · **D6** Adelaide stays "the
day", picker shows venue-local date · **D7** international EV marked
uncalibrated, only after the commission fallback is fixed.

> **D2 note, as requested.** The jurisdiction set lands as a config table, not
> a literal. Adding Ireland is one row. My recommendation remains **UK + IRE
> together**: they share a timezone, a Betfair market-name convention, a
> results supply and a book-coverage profile, so the second one is nearly free
> and validates the "configurable, not hardcoded" claim the first time rather
> than the second.

---

## 1. What changed between the assessment and this brief

The assessment was written from aggregates. Planning it forced eight
row-level checks. Five held, **three did not**, and two of the three change
the shape of the build. They are stated up front because the brief is built
on the corrected picture, not the assessment's.

| # | Assessment claim | Measured | Consequence |
|---|---|---|---|
| A | R1: mis-dating is "the twin-row disease reinstated wholesale", ~150 corrupt rows/day | **REFUTED as a duplication claim, on two independent censuses.** (i) Grouping market-less races by `(venue, race_number, scheduled_start)` over 21 days gives exactly **one** date-twin group (`randwick` R16, an AU row). (ii) The stricter census, which also catches `scheduled_start IS NULL` rows: of **1,452** market-less rows sharing `(venue, race_number)` with a row on the adjacent `race_date`, only **1 pair shares a single runner name**. The other 1,451 are simply venues racing on consecutive days. International races are mis-*dated* but not *duplicated* — TAB files each race on exactly one of its own dates, so each physical race gets exactly one row. | The urgency behind Phase 0 item 3 collapses. What is real is **card fragmentation**: 63 meetings in 21 days (36 USA, 16 GBR, 8 IRL, 3 CAN) have their races split across two `race_date` values at Sydney midnight — e.g. Windsor (GBR) 20 Jul, races 1–5 on `2026-07-20` and races 6–7 on `2026-07-21`, all seven with a venue-local date of 20 Jul. That is a *display and query* defect, not data loss. **This is why §5 does not flip `race_date` in Phase 0.** |
| B | (c) The 19:00 stop hour is "REFUTED in practice — already solved by accident"; "Past stop hour … exiting" appears **once** in the log | **REFUTED.** It appears **10 times** across log rotations, including **22 Jul 12:15 UTC** and **29 Jul 12:21 UTC**. On 29 Jul the collector shut down at 12:21 UTC and did not restart until the 23:00 UTC timer — **10 hours 39 minutes down, i.e. 21:52–08:30 Adelaide, the entire overnight international card of 29–30 Jul lost.** (Log gap verified: zero collector lines between those timestamps; `systemctl` `NRestarts=0`, `ActiveEnterTimestamp=Wed 2026-07-29 23:00:19 UTC`.) | Item 4 is **not** documentation work. It is a live, intermittent, ~10-hour capability hole firing roughly weekly. It is also an **interlock on item 1** — see §4 and §7. |
| C | R6: the 30 Jul 01:30 "Book frozen" email is the live example of a foreign-racing false alarm | **REFUTED — that one was a TRUE POSITIVE.** The same alert names `ladbrokes` and `neds` frozen since 00:40:54 alongside tab/tabtouch since 00:41:28, and the collector log shows `TAB attempt error … CONNECT tunnel failed, response 407` starting **00:42:01** — the Decodo quota outage that produced capture commit `c0abb2b`. | The false-alarm class is real but the headline example was misattributed. Corrected evidence in §4. Designing to "silence the 01:30 alert" would have been designing to silence a genuine outage. |

Five that held, with numbers now attached: TAB does 404 at scale
(3,843 / 5,787 / 5,535 / 2,874 / 2,459 per day 23–28 Jul; 29 Jul reads 102
only because of the outage in row B); international races are polled in
volume; `races` carries no country; `state_from_timezone` returns `"AU"` for
unknown zones; the AU/international venue collision is live (`canterbury`
carries NSW and USA rows within 60 days — the only cross-jurisdiction
collision in the window, alongside `q2 parklands` AUS/QLD).

**Two findings the assessment did not have at all**, both cheap and both
folded into this build:

- **The venue-code bug.** 275 international races in 14 days carry a
  `tab_race_id` of the shape `"/6"` — venue mnemonic missing. `fetch_tab`
  builds `…/meetings/R//races/6`, which 404s **every single poll, forever, by
  construction**. Distribution: USA 158, GBR 51, CAN 31, IRL 17, GB 12, NZ 3.
  Zero AU. This is a straight bug and a meaningful slice of the 404 count.
- **The Entain circuit-breaker leak.** Unlike TAB's 404 path (which is
  breaker-exempt since `caffb78`), `ladbrokes`/`neds` fetch failures call
  `cb.record_failure()`. The top two failing venues across the whole retained
  log are **`happy valley` (100) and `sha tin` (69)** — Hong Kong. So
  international races are actively consuming AU books' circuit-breaker budget.
  1,653 neds and 1,117 ladbrokes failures total.

---

## 2. Scope

**In:**

1. Per-book coverage model, learned from snapshot success, enforced at fetch
   dispatch (§3).
2. Coverage fed to the liveness checker, plus a replacement check so the
   watchdog gets *louder* about real overnight failure while getting quieter
   about non-coverage (§4).
3. `races.country` — plain nullable column, canonicalised, populated forward
   and backfilled; jurisdiction set as config data (§5).
4. `races.local_race_date` — venue-local date as a **new column**, and the
   `race_date`/`book_query_date` decoupling refactor that makes Phase 1's key
   change safe. **`race_date` itself is not flipped in Phase 0** (§5, §6, and
   the operator decision **D8** at §10).
5. Continuous operation: `STOP_HOUR_LOCAL` retired, explicit 04:00–06:00
   Adelaide maintenance window, liveness window assumptions replaced (§7).
6. Ordering enforcement making R4-before-R2 structurally impossible (§8).
7. The two §1 bug fixes: empty TAB venue mnemonic, Entain breaker leak.

**Explicit non-goals** (named so they are not smuggled in):

- No change to `races.race_date` values, to `venue_normalised`, or to
  `UNIQUE(race_date, venue_normalised, race_number)`. DR-035/DR-036 §7
  reserves stand.
- No Betfair international discovery (that is R4/Phase 2). Phase 0 *forbids*
  it, mechanically (§8).
- No historical repair of mis-dated international rows (Phase 1 item 7).
- No results, BSP, subscription, settlement, EV, commission, promo-scope or
  tool-side work. No `evEngine`, no `commission.ts`, no picker.
- No `normalise_venue` change, no `_find_matching_venue` change, no alias
  additions. **These are frozen while the twin repair runs** (§6).
- No proxy plan change, no cadence change, no compression work. S257's TAB
  latency work is not traded for bytes.
- No `position_min_field` anything (operator-dropped, S255).
- No greyhound/harness reclassification. `INCLUDE_GREYHOUNDS` stays as it is.

---

## 3. Item 1 — per-book coverage model

### 3.1 Why not "per-book jurisdiction", as originally scoped

Per-jurisdiction is the wrong grain, and the live data says so plainly.
TAB serves **132 of 429** USA races and **100 of 288** GBR races — so
suppressing TAB on USA or GBR throws away real coverage, and permitting it
keeps most of the waste. The variance is almost entirely **per venue**:

| GBR venue | races w/ TAB id | ever served |
|---|---|---|
| york uk | 11 | **11** |
| great yarmouth | 11 | **11** |
| ayr | 8 | **8** |
| doncaster / cartmel | 7 / 7 | **7 / 7** |
| uttoxeter | 16 | **0** |
| ascot uk | 14 | **0** |
| lingfield | 13 | **0** |
| leicester | 12 | **0** |
| thirsk / pontefract / chester / chepstow / redcar / catterick | 6–7 each | **0** |

Same shape in USA (`saratoga extra` 0/23, `charles town` 16/24) and the
28 Jul 01:30 false alarm resolves to `gavea` (BRA) R8/R9: TAB id assigned,
**0 TAB snapshots, 160 and 208 TABtouch snapshots**. TAB does not serve
Gávea; TABtouch does.

**Design grain: `(book, venue_normalised)` primary, `(book, country)` only as
the prior for a venue with no history.** This also sidesteps a trap that would
have broken a jurisdiction-keyed model outright: **8,913 race rows in the last
30 days have `state = ''`** — TABtouch and PointsBet hardcode `state=""` in
both discovery and fetch (`bookmakers/tabtouch.py:136,238`,
`bookmakers/pointsbet.py:56,152`), and TABtouch is the single largest
international discoverer. A jurisdiction-keyed model would have a
40–50%-of-rows "unknown" bucket on day one. A venue-keyed one does not care.

### 3.2 Data model

New table, additive, no index or key change:

```
book_venue_coverage(
  bookmaker            TEXT NOT NULL,      -- db name: 'tab', 'tabtouch', …
  venue_normalised     TEXT NOT NULL,
  country              TEXT,               -- canonical, nullable (§5)
  races_with_book_id   INTEGER NOT NULL,   -- trailing window
  races_served         INTEGER NOT NULL,   -- >=1 snapshot from this book
  last_served_at       TEXT,
  last_probe_at        TEXT,
  status               TEXT NOT NULL,      -- SERVED | UNSERVED | UNKNOWN
  computed_at          TEXT NOT NULL,
  PRIMARY KEY (bookmaker, venue_normalised)
)
```

Plus `book_country_coverage(bookmaker, country, …)` with the same columns,
computed by rollup — used only as the prior for an unseen venue.

### 3.3 Learning rule (recompute, never hand-maintained)

Nightly, in the 04:00–06:00 window (§7), over a **trailing 21 days**:

- `races_with_book_id` = races where `<book>_race_id IS NOT NULL`.
- `races_served` = of those, how many have ≥1 `bookmaker_snapshots` row for
  that book.
- `status = SERVED` if `races_served >= 1`.
- `status = UNSERVED` if `races_with_book_id >= 8` **and** `races_served = 0`.
- `status = UNKNOWN` otherwise.

The 21-day window and the `>= 8` floor are chosen so a venue that races
weekly needs three clean weeks of total non-service before it is suppressed.
Seeded from history on first run; no hand-written table, so it cannot rot.

### 3.4 Enforcement — and where it must *not* go

Enforcement lives in **exactly one place**: the per-book fetch loop in
`capture/orchestrator._process_race`, immediately before
`self._fetch_bookmaker(...)`. If `(book, venue)` is `UNSERVED`, skip the
fetch, increment a counter, do not touch the circuit breaker, do not log at
WARNING.

**It must not be applied at discovery, at `match_races`, at `_persist_race`,
or at `_register_race`.** Two hard reasons:

1. A race that no book serves must still be discovered and tracked, because
   the *other* books still serve it and because Phase 2's Betfair discovery
   will attach to those rows.
2. **The stop-hour interlock.** `_should_stop()` (`orchestrator.py:165-181`)
   exits the collector past 19:00 Adelaide when `active == 0`. Suppressing at
   registration would shrink the tracked-race set, which makes `active == 0`
   *more* likely overnight, which fires the exact 10.6-hour outage measured on
   29 Jul (§1 row B). Fetch-level suppression leaves tracker counts
   bit-identical. **Item 4 ships before item 1 regardless** (§7).

### 3.5 Safety valves

- **Fail open.** `UNKNOWN` always fetches. A venue never seen before is
  always tried.
- **Never suppress AU.** Hard guard: if the venue has any row with `state IN
  (8 AU states)` in the trailing window, or `country = 'AU'`, it can never be
  `UNSERVED`. Belt and braces against a learning bug taking out a real
  Australian meeting.
- **Re-probe.** For every `UNSERVED (book, venue)`, the **first race of each
  meeting** is fetched anyway, once per day. If it succeeds, the next
  recompute flips the status back to `SERVED` and full coverage resumes within
  24h. Cost: ~1 request per suppressed meeting per day. This is what stops
  suppression from becoming permanent blindness when a book adds coverage.
- **Kill switch.** `COVERAGE_SUPPRESSION_ENABLED` env flag, default on;
  flipping it off and restarting restores today's behaviour exactly.
- **Audit line** per suppressed race, at INFO, with the counters in the
  discovery summary — so the log proves what was skipped.

### 3.6 Companion bug fixes (same deploy)

- **Empty TAB mnemonic.** `discover_tab` must not emit a race id when
  `venueMnemonic` is empty (`bookmakers/tab.py:570`); `_fetch_bookmaker` must
  refuse a `tab_race_id` whose venue-code segment is empty
  (`orchestrator.py:923-925`). Kills 275 races' worth of guaranteed 404s per
  14 days at source. Same treatment for `palmerbet`'s `Venue/Num` shape.
- **Entain breaker leak.** A fetch failure on a `(book, venue)` that is
  `UNSERVED` or `UNKNOWN` must not call `cb.record_failure()`. Circuit
  breakers exist to protect against *this book being down*, not against *this
  book not carrying Hong Kong*. Failures on `SERVED` venues still count.

---

## 4. Item 2 — liveness

### 4.1 Corrected noise baseline

Per-book FAIL lines in the retained liveness log, classified by hand:

| When | Books named | Verdict |
|---|---|---|
| 28 Jul 00:30 → 02:00 (7 lines, 1 email) | tab ("last snapshot **never**", 2–4 NEAR races), tabtouch | **False alarm — the target class.** The NEAR races were `gavea` (BRA) R8/R9: TAB id present, 0 TAB snapshots ever, TABtouch fine. |
| 28 Jul 23:00 (1 line) | tab, 6 NEAR races | Same class, overnight international. |
| 27 Jul 01:00 (1 line) | ladbrokes, neds, pointsbet | Ambiguous — NZ window; not claimed as a win. |
| 30 Jul 01:15 → 01:45 (3 lines, 1 email) | ladbrokes, neds, tab, tabtouch | **TRUE POSITIVE — Decodo 407 quota outage at 00:42.** Must still fire after this build. |
| 29 Jul 08:00–09:15, 22/23/26 Jul 09:00 | playup, then 5 books | Daytime, out of scope. |

So the honest claim is: **~8 of ~12 overnight per-book FAIL lines and 1 of 2
overnight emails in the retained window are the coverage class.** Not "5 false
alarm emails". The separate 29 Jul overnight storm (24 `Stamped coverage` FAIL
lines, 9 emails) was the `kensington`/`randwick kensington` twin — **already
fixed by 0l**, and must not be double-counted as an international win.

The other half of R6 is real and worse: **237 "staleness grace active" lines**
in the log. Overnight, `staleness_applies(require_market=True)` finds no
market-bearing race in the window (no international race has a Betfair
market), so the Betfair-freshness check never arms. Between ~19:00 and ~08:00
Adelaide the watchdog's main freshness check is off.

### 4.2 Changes

**(a) Coverage filter on `check_per_book_staleness`.** In the per-book NEAR
query, exclude races whose `(book, venue_normalised)` coverage status is
`UNSERVED`. A book that cannot serve a race is not a candidate for being
frozen on it. Books with no remaining candidate races drop out entirely
(existing behaviour). *Verified against the 30 Jul true positive: tab,
tabtouch, ladbrokes and neds all hold `SERVED` status on the NEAR venues in
that window, so that alert still fires unchanged.*

**(b) New check — `check_capture_heartbeat`, replacing the overnight silence.**
This is the load-bearing half. Independent of Betfair, independent of state:

> If ≥1 tracked race has `scheduled_start` within `-STALE_MINUTES … +60m`,
> and ≥1 book holds `SERVED` coverage on that race's venue, then **at least
> one snapshot from any book must exist across those races in the last 20
> minutes.** Zero ⇒ FAIL "capture silent".

This fires on the 29 Jul collector-exit hole (nothing running at all), on a
proxy outage, and on any wedge — at any hour, including 01:00. It is the check
that makes the watchdog *net louder*, and it is why (a) is safe to ship.

**(c) `check_stamped_coverage` untouched in Phase 0.** It filters to
`state IN AU_STATES` at `:232`, which is correct *today* — international races
genuinely have no Betfair identity to check, so widening it would produce a
guaranteed nightly FAIL on every international race. It is widened in **Phase
2**, gated on the same flag as R4 (§8). Recorded here so nobody "fixes" it.

**(d) Operating-window replacement** — see §7.

### 4.3 What the watchdog must not go quiet on

Stated as explicit invariants, each with a test:

| Real failure | Still caught by |
|---|---|
| Collector dead / stopped | `check_collector_alive` + new heartbeat (b) |
| Proxy 407 / quota | `check_proxy_auth` (always-on) + heartbeat (b) + per-book (a) on SERVED venues |
| One book burned mid-card on AU racing | per-book (a) — AU venues are never `UNSERVED` (§3.5) |
| One book burned mid-card on international it *does* serve | per-book (a) — `SERVED` venues keep candidacy |
| Whole overnight card uncaptured | heartbeat (b) — **new; not caught today** |
| Betfair feed stalled during AU racing | unchanged |
| Book silently *drops* a jurisdiction it used to serve | recompute flips it to `UNSERVED` after 3 weeks — **accepted blind spot**, logged as a status transition in the sweep summary so it is visible |

---

## 5. Items 3 and 5 — country, and the date

### 5.1 `races.country` (D3)

Plain nullable `TEXT` column via the existing idempotent-migration pattern
(`ensure_racing_code_schema` in `storage/racing_day.py`). **No index, no
natural-key participation, no `venue_normalised` change.** DR-036 §7 reserves
respected exactly.

Canonical values: **ISO-3166 alpha-2** (`AU`, `GB`, `IE`, `US`, `FR`, `JP`,
`NZ`, `HK`, `TR`, …). Resolution order, first hit wins, `NULL` if none:

1. **Betfair `countryCode`** when a market matched (Phase 2 onward; wiring
   added now, unreachable while the country list is `["AU"]`).
2. **Bookmaker meta `state`**, through a canonicalisation map that fixes the
   duplicate codings already in the data: `NZ`/`NZL`→`NZ`, `GB`/`GBR`→`GB`,
   `ZAF`/`SAF`→`ZA`, `IRL`→`IE`, `USA`→`US`, `FRA`→`FR`, `JPN`→`JP`,
   `TUR`→`TR`, `CAN`→`CA`, `BRA`→`BR`, `KOR`→`KR`, `DEU`→`DE`, `SAU`→`SA`,
   `MYS`→`MY`, `URY`→`UY`, `ARG`→`AR`, `CHL`→`CL`, `SAM`→ audit (unmapped;
   probably South America mis-tag), `AUS` + the 8 AU state codes → `AU`.
3. **TAB's venue display country tag.** TAB writes `"Windsor (Gbr)"`,
   `"Saratoga (Usa)"`, `"Naas (Irl)"` — and `normalise_venue` throws the
   parenthetical away at `race_matcher.py:126-127`. Phase 0 *reads* the tag
   off the raw display string before normalisation and uses it as a country
   source. **It does not change `normalise_venue`** (§6).
4. **`venue_country` learned table** for the ~250/day blank-state
   TABtouch-only rows: a venue's country, learned from any row of that venue
   that did resolve. Recomputed with the coverage model.

Write discipline: **fill-if-null**, never overwrite a non-null `country`
(`upsert_race`'s `COALESCE(excluded.col, col)` is new-value-wins, so `country`
goes through the guarded path, not the generic upsert). A row whose country
resolves two different ways lands on an audit list rather than flapping.

**Jurisdiction set as configuration.** One table, `jurisdiction_config(country
TEXT PK, enabled INTEGER, tz TEXT, label TEXT, betfair_country_code TEXT)`,
seeded `AU` enabled and `GB` disabled-pending-Phase-2. Ireland is `INSERT INTO
jurisdiction_config VALUES ('IE', 0, 'Europe/Dublin', 'Ireland', 'IE')` — one
row, no code change, exactly as D2 requires.

### 5.2 The date — and why `race_date` is not flipped in Phase 0

**`race_date` is not just an identity stamp. It is a live URL parameter.**
Three call sites read the stored value and put it in a bookmaker request path:

- `capture/orchestrator.py:925` — `fetch_tab(state.race_date, vc, rn)` →
  `/dates/{race_date}/meetings/R/{code}/races/{n}`
- `capture/orchestrator.py:932` — `fetch_palmerbet(state.race_date, …)`
- `scripts/morning_sweep.py:496,501` — both again, off `race["race_date"]`

TAB files an overseas meeting under **TAB's own Australian card date**, not
the venue-local date. Windsor (GBR) on 20 Jul local is TAB's 20 Jul *and*
21 Jul card. If `race_date` becomes venue-local, every international TAB fetch
asks the wrong date. Best case that is a 404 and international TAB capture —
the **main promo book** — dies silently, because 404s are deliberately
swallowed since `caffb78`. Worst case, at a track running consecutive days
(Del Mar, Saratoga, Thistledown all do), TAB returns **the previous day's race
N** and we write another day's prices onto this race's row. Silent
wrong-price corruption on the promo book.

`twin_row_fix_brief.md` §5 B1 anticipated half of this — *"`today_str` REMAINS
the bookmaker-discovery query date; only the row stamp changes"* — but B1 was
**dropped before build** ("Build deltas", §8), and it addressed the discovery
query only, not these three fetch sites. The coupling is live and unguarded.

Second reason, and the one the operator asked me to work out: **the cutover
would create a twin class that nothing in the system can repair.**

- Changing `race_date` changes the natural key
  `(race_date, venue_normalised, race_number)` for every row it touches.
- For rows in flight at cutover, the next discovery pass resolves the natural
  key, misses the old row, and **inserts a new one**. Bookmaker discovery
  re-persists the whole current card every 30 minutes, so this is not a
  handful of races — it is one new row per international race on the card,
  plus AU rows that cross Sydney midnight (late WA/NT, and every
  greyhound/harness row that never matched Betfair).
- **`storage/race_resolve.resolve_by_market` cannot help**: it keys on
  `betfair_win_market_id`, and **0 of 1,925 international rows have one**. It
  falls straight through to the natural key — the pre-DR-036 twin generator,
  exactly as R1 says.
- **`storage/twin_merge.py` cannot help either.** Its scope is *"markets with
  >1 same-code rows"*; `twin_row_fix_brief.md` §5 Layer C says in terms
  *"No-market-id shells: OUT (data-reset thread; no spine)"*. The nightly
  self-heal in `scripts/identity_sweep.py` uses the same core and the same
  scope. So a cutover twin on a market-less international race is **invisible
  to the write-time enforcement, invisible to the nightly self-heal, and
  invisible to the historical repair.** It is permanent until the data reset.
- And `_register_race` would then track both rows — the S258 double-tracking
  data-loss mechanism, on the class where B5's market-id tracker dedup
  (`_find_tracked_market`) has no market id to dedup on.

Third reason: **the repair is still running.** `twin-repair-n2.timer` is armed
for 2026-07-30 14:15 UTC (23:45 Adelaide); last night's pass merged 2,530 of
8,821 markets before its 04:30 deadline and reported **"Twin markets remaining
in scope: 6,291"**. Several more nights to go. Changing key semantics
underneath a running merge is not a risk worth taking for a defect that is
costing us a display bug.

Fourth: **Phase 1 changes the other half of the same key** —
country-qualified `venue_normalised` (`gb:ascot`). Flipping `race_date` in
Phase 0 and `venue_normalised` in Phase 1 means **two cutover waves** instead
of one, on a class with no merge machinery, for no benefit.

Fifth, and decisive: **§1 row A**. The measured harm today is card
fragmentation, not duplication — **one** true twin in 21 days on each of two
independent censuses (the second one specifically built to catch what the
first would miss), and it is Australian. There is no ~150-rows/day corruption
to stop.

### 5.3 What Phase 0 does about the date instead

**(i) New column `races.local_race_date`** — venue-local calendar date of the
jump, derived from `scheduled_start` and the venue's timezone
(`jurisdiction_config.tz` via `country`, else the Betfair event timezone once
available, else `NULL`). Populated forward by the collector and backfilled
over history. **Purely additive. Nothing keys on it. Nothing routes on it.**

This delivers everything Phase 0 actually needs from item 3:
- A meeting can be queried as one meeting (`GROUP BY venue, local_race_date`),
  which is what "12 meetings smeared across 8 dates" was really asking for.
- The racing-api race payload gains `local_race_date`, which is the field D6
  requires the picker to show. Optional, additive, no v3 build needed to ship
  Phase 0.
- Phase 1's key change becomes mechanical: the target value is already
  computed, already backfilled, and already verifiable **before** anything is
  rewritten. The Phase 1 cutover can be dry-run against a column that already
  exists.

**(ii) The decoupling refactor.** `RaceState` gains `book_query_date`, set
from the discovery `today_str`; the three fetch sites switch from
`race_date`/`race["race_date"]` to it. **Today this is a provable no-op** —
`book_query_date == race_date` for every bookmaker-discovered row — so it
ships behind a test asserting equality on current data, and it removes the
landmine that would otherwise detonate in Phase 1. `morning_sweep.py` gets the
same treatment via a persisted `book_query_date` column (or, simpler, it keeps
reading `race_date` until Phase 1 adds the column — decided at build time
against whichever reads cleaner; both are safe while `race_date` is unchanged).

**(iii) `state_from_timezone` de-fanged now.** `storage/racing_day.py:60-64`
returns the literal `"AU"` for any unknown timezone. Phase 0 changes the
unknown branch to return `None`, and extends `_TZ_STATE` with the enabled
jurisdictions' zones mapping to their country codes. **This is a no-op today**
— the function is only reachable from the Betfair branch, and Betfair
discovery is `["AU"]`-only, so no unknown zone ever reaches it. A red-before
test proves the current behaviour, then proves the new one. It costs nothing
now and removes the single worst landmine in the R4 path.

---

## 6. Interaction with the S259 twin fix — what Phase 0 must not touch

The 0l gains are (DR-036): read-time union under the horse-identity guard;
write-time market-id-first adoption; one tracker per market; journalled merge
repair. Phase 0 preserves all four by **not going near any of them**:

| 0l surface | Phase 0 |
|---|---|
| `storage/race_resolve.py` | untouched |
| `storage/twin_merge.py` | untouched |
| `api/market_resolution.py` | untouched |
| `matching/race_matcher.normalise_venue` / `_find_matching_venue` / `BETFAIR_VENUE_ALIASES` | **frozen.** Any change alters `venue_normalised`, which alters the merge set of a repair that is mid-run with 6,291 markets outstanding. Phase 1 owns it, after the repair reports zero. |
| `UNIQUE(race_date, venue_normalised, race_number)` | untouched — no key change, no value change |
| `_register_race` / `_find_tracked_market` | untouched (§3.4) |
| `scripts/identity_sweep.py` merge pass | untouched; the coverage recompute is a **separate** job on its own timer, not bolted into the sweep |
| `races` schema | two additive nullable columns + two new tables. No index change. |

**Deploy is fenced against the repair window.** The nightly repair runs
23:45–04:30 Adelaide. Phase 0's collector restart and its backfill both happen
**outside** that window, and the deploy is refused if `twin-repair-n2.service`
is active (a preflight check, not a convention).

---

## 7. Item 4 — continuous operation and the maintenance window (D4)

**Evidence (§1 row B):** the stop hour is live, fires roughly weekly, and
costs ~10.5 hours of overnight capture when it does.

- `config/settings.py:88` — `STOP_HOUR_LOCAL = 19` replaced by
  `CONTINUOUS_OPERATION = True` (env-overridable). `_should_stop()` returns
  `False` unless continuous operation is off. The dead branch is deleted, not
  commented.
- **Managed restart instead of self-exit.** Continuous operation with no
  restart at all means a Betfair session and a process that never recycle
  (`orchestrator.py:187-204` re-login has been exercised but never designed
  for indefinite uptime). A `racing-collector-restart.timer` at **04:15
  Adelaide** performs a graceful restart inside the maintenance window —
  bounded, scheduled, and in the emptiest slot in the data (130 snapshots at
  04:00 vs 128,460 at 14:00).
- **Maintenance window 04:00–06:00 Adelaide, documented and now real.** It is
  already crowded: twin-repair deadline 04:30, backup 05:00, metadata backfill
  05:30, identity sweep 05:50, health check 06:00. The coverage recompute and
  the `local_race_date` backfill slot in at **04:05** — before the repair
  deadline, and short. The window is written into
  `vps_health` / the ops runbook, not just this brief.
- **Liveness window replacement.** `COLLECTOR_DAY_START/END = (8,25)/(19,0)`
  are replaced by `MAINTENANCE_WINDOW = (03:55, 06:05)` Adelaide.
  `collector_expected_running()` returns `True` at every hour except inside
  that window. The `collector_last_exit_clean()` escape hatch is **deleted** —
  under continuous operation there is no such thing as a clean designed exit,
  and leaving it in would keep the 29 Jul hole silent.

**Ordering:** item 4 ships **first**, before item 1. §3.4 argues the coverage
model cannot shrink the tracker set, but the argument is a code-reading, and
the failure mode if it is wrong is a silent 10-hour overnight hole. Retiring
the stop hour first makes that failure mode structurally impossible rather
than argued.

---

## 8. Ordering enforcement — making R4-before-R2 impossible

The rule: **country identity (R2) before Betfair international discovery
(R4)**, because `state_from_timezone` would stamp every foreign race `"AU"`.
Four independent locks, so no single lapse can breach it:

1. **Single choke point.** All five hardcoded `["AU"]` filters
   (`betfair/client.py:189`; v3 `_translation.py:289`;
   `_stream_transport.py:118-125`) are replaced — *in Phase 2, not now* — by
   reads from one function, `betfair_market_countries()`, which derives from
   `jurisdiction_config WHERE enabled = 1`. Phase 0 introduces the function
   and points `betfair/client.py` at it; the config seeds `AU` only, so the
   behaviour is byte-identical today.
2. **Startup assertion.** `assert_identity_ready(countries)` raises at
   collector startup unless, for every enabled non-`AU` country: `races.country`
   exists, `jurisdiction_config.tz` is populated, that tz is in `_TZ_STATE`,
   and `INTL_IDENTITY_VERSION >= 2` (a constant Phase 1 bumps). **Enabling a
   country before Phase 1 stops the collector booting.** Loud, immediate,
   unmissable — the opposite of silent corruption.
3. **Red test, permanently.** `test_no_intl_discovery_without_identity` asserts
   that `betfair_market_countries()` returning anything beyond `["AU"]` while
   `INTL_IDENTITY_VERSION < 2` raises. Anyone who widens the list without
   doing Phase 1 gets a failing suite before they get a deploy.
4. **Runtime tripwire.** A liveness check that FAILs if any race row exists
   with a `betfair_win_market_id` and a `country` that is `NULL` or `'AU'`
   while its `state` is a non-AU code. Catches the case where discovery is
   widened through some path nobody predicted.

Phase 0 also fixes the `"AU"` fallback itself (§5.3 iii), so even a total
failure of all four locks degrades to `NULL` rather than a wrong country.

---

## 9. Build, test, deploy, rollback, acceptance

### 9.1 Order of work (four independently revertible commits)

| # | Commit | Contents | Gate before next |
|---|---|---|---|
| 1 | **Continuous operation** | `CONTINUOUS_OPERATION`, `_should_stop`, restart timer, liveness maintenance-window replacement, `collector_last_exit_clean` deletion | 48h with zero unplanned collector exits; one clean 04:15 restart observed |
| 2 | **Identity groundwork (no behaviour change)** | `races.country`, `races.local_race_date`, `jurisdiction_config`, `venue_country`, country canonicalisation, `state_from_timezone` unknown→`None`, `betfair_market_countries()` + the four locks (§8), `book_query_date` decoupling refactor | Full suite green; live spot-check that `betfair/client.py` still requests `["AU"]`; `country` populated on ≥95% of new rows |
| 3 | **Coverage model** | tables, recompute job, fetch-dispatch suppression, re-probe, kill switch, TAB-mnemonic fix, Entain breaker fix | 24h of counters; 404 delta measured; **zero** AU venue suppressed |
| 4 | **Liveness** | per-book coverage filter, `check_capture_heartbeat` | overnight observation; heartbeat proven to fire on an induced silence |

### 9.2 Test plan (red before green at every layer)

- **Coverage learning:** fixture with `gavea`/tab at 0-served-of-12 → `UNSERVED`;
  `york uk`/tab at 11-of-11 → `SERVED`; 3-of-3 → `UNKNOWN` (below the floor);
  a venue carrying an AU state and 0 served → **`SERVED`, never suppressed**
  (the §3.5 guard, red first).
- **Enforcement:** `UNSERVED` skips the fetch and does not touch the breaker;
  `UNKNOWN` fetches; the meeting's first race fetches even when `UNSERVED`
  (re-probe); kill switch off ⇒ every fetch attempted.
- **Tracker invariance (the §3.4 interlock):** a fixture day where every book
  is `UNSERVED` on every international venue must produce an **identical
  tracked-race set** to the same day with suppression off. Red-first.
- **Stop hour:** `_should_stop()` returns `False` at 23:00 Adelaide with zero
  active races under continuous operation; returns `True` with the flag off
  (so the old path is still provably intact).
- **Liveness:** replay of the **28 Jul 01:30** Gávea state ⇒ no FAIL; replay of
  the **30 Jul 01:30** Decodo state ⇒ **FAIL, unchanged** (this test is the
  single most important one in the build); zero snapshots across all books with
  SERVED NEAR races ⇒ heartbeat FAIL; maintenance-window hour ⇒ collector not
  expected up.
- **Country:** each duplicate coding canonicalises (`NZL`→`NZ`, `GBR`→`GB`,
  `SAF`→`ZA`, …); `"Windsor (Gbr)"` yields `GB` **without** changing
  `normalise_venue("Windsor (Gbr)")`, asserted directly; unknown code ⇒ `NULL`
  + audit; existing non-null `country` never overwritten.
- **Date decoupling:** `book_query_date == race_date` for every row in a
  current-data fixture (proves the no-op); `fetch_tab` receives
  `book_query_date`, asserted by call-arg spy; `local_race_date` correct for
  a Windsor GBR straddle case (races 1–7 all `2026-07-20` despite `race_date`
  20 and 21), a Del Mar Pacific case, and a `scheduled_start IS NULL` case
  (⇒ `NULL`, never a guess).
- **Ordering locks:** enabling `GB` in `jurisdiction_config` while
  `INTL_IDENTITY_VERSION < 2` raises at startup; `betfair_market_countries()`
  returns exactly `["AU"]` on seeded config.
- **Regression:** existing capture suite green (198+ tests). No v3 test run
  required — v3 is untouched.

### 9.3 Deploy

Standing capture-fix authority. Per commit: local build + full suite → push
VPS + GitHub → restart `racing-capture` in a no-NEAR-races gap (graceful ~13s,
practised S250/S257) → restart `racing-api` only if the payload field landed.

**Preflight refusals** (hard, scripted): `twin-repair-n2.service` active;
inside 23:45–04:30 Adelaide; any Decodo bench cooldown active; `df` below the
standing floor.

Backfills (`country`, `local_race_date`, first coverage compute) run **read
mostly, write in bounded batches with `wal_checkpoint(TRUNCATE)` between
batches**, at 04:05 Adelaide, resumable, and are `UPDATE … WHERE col IS NULL`
only — they can never overwrite anything and can never change a key column.

### 9.4 Rollback

- Commit 1: revert + restart. Collector returns to self-exit.
- Commit 2: revert. **The columns and tables stay** (additive, nullable,
  nothing reads them after revert). Nothing to un-write.
- Commit 3: `COVERAGE_SUPPRESSION_ENABLED=0` + restart — **no deploy needed**,
  seconds, and provably restores prior behaviour because suppression is a
  single early-`continue`.
- Commit 4: revert `liveness_check.py`; it is a standalone script on a timer,
  no restart needed.

No rollback requires touching data. That is a deliberate property of this
build and the main reason `race_date` is not flipped.

### 9.5 Acceptance criteria (all measurable, baselines from 30 Jul)

| # | Metric | Baseline | Target | How |
|---|---|---|---|---|
| A1 | TAB 404s/day (`not on TAB this cycle`) | 3,843 / 5,787 / 5,535 / 2,874 / 2,459 (23–28 Jul); ~4,100 mean of full-uptime days | **≤ 1,000/day**, i.e. ≥75% reduction, measured over 3 full-uptime days | `grep -c` on collector.log by date |
| A2 | Races carrying a `tab_race_id` that TAB never serves | 800 of 2,113 in 14d (AU: 13 of 471) | ≤ 150 in 14d, and the suppressed ones no longer fetched at all | DB query, same SQL as the baseline |
| A3 | Malformed `tab_race_id` (`'/%'`) written | 275 in 14d | **0** new | DB query on rows created post-deploy |
| A4 | Overnight (19:00–08:00 Adel) per-book FAIL lines | ~12 in the retained window, ~8 of them coverage-class | Coverage-class → **0**; true-positive class → **unchanged** | liveness log, classified |
| A5 | The 30 Jul Decodo scenario still alerts | true positive | **Must still FAIL** — asserted by unit test and by the next real outage | test + observation |
| A6 | Overnight blindness | 237 "grace active" lines; no check armed | `check_capture_heartbeat` armed and passing every overnight run; proven to FAIL on induced silence | liveness log |
| A7 | Unplanned collector exits | 2 in 8 days (22, 29 Jul), 10.6h each | **0** in 14 days; exactly one scheduled 04:15 restart per day | collector.log + `systemctl` |
| A8 | Date correctness spot check | Windsor GBR 20 Jul: 7 races across `race_date` 20 and 21 | All 7 carry `local_race_date = 2026-07-20`; ≥98% of international rows with a `scheduled_start` carry a non-null `local_race_date`; **`race_date` values bit-identical to pre-deploy** (checksum) | DB queries + a pre/post `race_date` checksum over all rows |
| A9 | `country` populated | 0% (column absent) | ≥95% of new rows with a non-blank `state`; ≥80% of blank-state rows via the venue table; the rest `NULL` + audit list ≤ 5% | DB query |
| A10 | New twin rows | 1 no-market date-twin group / 21d | **≤ 1** — unchanged. Any increase is a build failure | the §1 row A query, re-run |
| A11 | Traffic delta | ~43,000 proxied requests/day | −3,000 to −4,000 requests/day (~8%); **bytes −1 to −2% only** (see the honesty note below) | request counters + Decodo dashboard |
| A12 | Entain breaker pressure | 1,653 neds + 1,117 ladbrokes failures, top venues Happy Valley + Sha Tin | ≥40% fewer breaker-recorded failures | collector.log |

> **Honesty note on A11, correcting the assessment's framing.** A 404 response
> body is on the order of 1 KB against a ~5.8 KB average request. Removing
> ~4,000 404s/day is roughly **4 MB of a ~250 MB day — 1 to 2%**, not a
> meaningful dent in the Decodo bill. Item 1's real value is **noise, alert
> quality, latency, breaker headroom and hunt pressure**, not bytes. The
> worklist line "kills 5,000–11,000 daily TAB 404s" is true; the implied
> proxy-bill saving is not. **D1's traffic diet needs a different lever** —
> and the honest one is cadence, or D2 dropping jurisdictions outright.

---

## 10. Operator decisions this brief needs

**D8 — the date stamp. The one place this brief departs from the literal
Phase 0 scope, and it needs a yes.**

Phase 0 as commissioned says "fix the race_date stamp". This brief instead
**adds `local_race_date` and leaves `race_date` alone**, deferring the flip to
Phase 1 where it lands together with country-qualified `venue_normalised` and
the historical repair, in one cutover, with the merge machinery available.

Reasons, in order of weight: (1) `race_date` is a live TAB/Palmerbet URL
parameter in three places — flipping it either kills international TAB capture
silently or writes the wrong day's prices onto a race (§5.2); (2) the cutover
would mint twins on the one class where `race_resolve`, `twin_merge` and the
nightly self-heal are **all** inoperative for want of a market id — permanent
damage until the data reset; (3) the historical repair is mid-flight with
6,291 markets outstanding; (4) Phase 1 changes the other half of the same key,
so doing it now means two waves instead of one; (5) **the measured harm is one
true twin in 21 days on two independent censuses, and it is Australian** —
there is no 150-rows/day fire to put out.

What is lost by waiting: international meetings stay split across two
`race_date` values in raw queries. What is gained immediately: `local_race_date`
makes the meeting queryable as one meeting and gives D6's picker its field.
**No capability is deferred; only the key rewrite is.**

*If the operator says flip it now anyway*, the build grows by roughly a full
sitting: `book_query_date` becomes load-bearing rather than a no-op refactor
and needs live proof against TAB before cutover; a market-less twin-merge core
must be written (identity-guarded on runner names only, since there is no
spine); a canary + journalled migration is required; and the repair must be
paused. That is a Phase 1 shape, not a Phase 0 shape — which is the argument.

**D9 — jurisdiction seed.** Phase 0 seeds `jurisdiction_config` with `AU`
enabled and `GB` present-but-disabled. Confirm `IE` should be seeded
disabled-but-present at the same time (my recommendation; costs one row).

---

## 11. Adversarial review

Written against my own brief, deliberately hunting for what breaks it.
Verdict at the end.

### 11.1 Data corruption at the date cutover

**There is no date cutover.** §5.2/§10 removed it, which removes the whole
corruption class the commission asked me to design against. That is a real
answer, but it is also the answer that makes me most suspicious of myself, so:

**Attack: am I deferring the hard thing and calling it design?** Partly, yes —
and the operator should read D8 with that in mind. Defence: the deferral is
not free-floating, it is *conditioned on measurement* (one twin group in
21 days), and it does not defer any capability, only a key rewrite. If the
measurement is wrong the argument collapses. So how confident am I in the
measurement? The first query grouped market-less races by
`(venue_normalised, race_number, scheduled_start)` and counted groups with >1
row. **Weakness: it requires `scheduled_start` to be identical across twins,**
and rows with `scheduled_start IS NULL` — all TABtouch-only rows — are
invisible to it entirely. So on its own that figure was a floor, not a
ceiling.

**I ran the second census rather than leaving it as a build gate, and it
holds — decisively.** Market-less rows sharing `(venue_normalised,
race_number)` with a row on the adjacent `race_date`, over 21 days, ignoring
`scheduled_start` entirely: **1,452 rows**. Of those, pairs sharing **at least
one normalised runner name** — the only definition of a twin that survives
RC-2: **1**. The other 1,451 are venues that simply raced on consecutive days.
**The duplication claim in R1 is refuted on the evidence that matters, and D8's
fifth reason is now measured twice by two different methods.** The pre-build
gate is closed; it is recorded here as evidence, not as outstanding work.

**Attack: `local_race_date` backfill writes to ~1.9M rows.** It is
`UPDATE … WHERE local_race_date IS NULL`, batched, checkpointed, on a column
nothing reads. Worst case is wasted IO. But it runs at 04:05, inside the same
window as the twin repair's deadline and the 05:00 backup, on a DB where the
repair holds long transactions. **Real risk: lock contention with the repair,
or bloating the WAL that the 05:00 backup then copies.** *Fix accepted:* the
backfill is **refused entirely while the repair has markets outstanding**;
`local_race_date` is populated forward-only until the repair reports zero,
then backfilled. Slower, but it removes an interaction I cannot fully model.

### 11.2 Interaction with the ongoing twin repair

**Attack: does the coverage model change the repair's inputs?** It suppresses
*fetches*, so fewer `bookmaker_snapshots` rows are written for suppressed
races. `twin_merge` moves snapshot children between fragments; fewer children
is not wrong, but a market that would have merged with N snapshots now merges
with fewer. Since suppressed races are exactly those with **zero** snapshots
from that book, the delta is zero rows. **Holds.**

**Attack: does the recompute job contend with the repair?** It reads
`bookmaker_snapshots` over 21 days — a large read against a DB under long
write transactions. *Fix accepted:* recompute at **04:05 only if the repair is
not running**, else skip that day (coverage is a 21-day rolling statistic;
missing a day is immaterial). Never fall back to hand-maintained data.

**Attack: could the repair change `venue_normalised` under the coverage
model's feet?** Yes — merge canonicalisation re-normalises the canonical
venue (`twin_row_fix_brief.md` §5 Layer C). A `(book, venue)` coverage row
could be keyed on a spelling the repair retires. Consequence is benign
(the old key goes `UNKNOWN` by absence and fails open), but it means coverage
must be **keyed on live data at recompute time, never cached across the
change** — which the recompute design already guarantees, and I am recording
it so nobody "optimises" it into a persistent hand-curated table later.

### 11.3 Anything that could regenerate the twin class

- Phase 0 writes **no identity column**. `race_date`, `venue_normalised`,
  `race_number`, `betfair_win_market_id`, `racing_code` are untouched by every
  commit. A9's `country` and A8's `local_race_date` are non-key.
- **A10 exists precisely as the tripwire** — the twin census is re-run
  post-deploy and any increase is a build failure.
- **Residual I could not eliminate:** `upsert_race`'s
  `COALESCE(excluded.col, col)` is new-value-wins, so if `country` went
  through the generic upsert two books disagreeing (`GB` vs `GBR` before
  canonicalisation) would flap the column on every discovery pass. Not a twin,
  but a churn bug and a source of `updated_at` noise. §5.1's guarded
  fill-if-null write is the fix; it must not be shortcut into "just add
  country to the kwargs dict", which is the obvious lazy implementation.

### 11.4 Liveness going quiet on something real

This is the review lens I trust least in my own work, because §4(a) is a
*suppression*.

- **The 30 Jul Decodo outage is a unit test (A5), not a hope.** I checked the
  four books named in that alert against their venue coverage: all `SERVED` on
  the NEAR venues. It fires unchanged.
- **New coverage from the heartbeat (b)** catches the 29 Jul 10.6-hour hole,
  which **nothing catches today** — the collector was down, and `is_racing_hours`
  → `collector_expected_running()` returned `False` because the exit was clean.
  Net, the watchdog gets louder.
- **Attack: the re-probe hides a book going dark.** If TAB stops serving York,
  York flips `SERVED`→`UNSERVED` after 3 weeks and per-book staleness stops
  watching it. Three weeks of degraded coverage before the watchdog stops
  caring — and it never *tells* anyone. *Fix accepted:* every
  `SERVED`→`UNSERVED` transition emits an audit line **and** a liveness note;
  a book losing a venue it used to serve is exactly the kind of quiet
  regression this system has been bitten by before.
- **Attack: the heartbeat is too weak.** "≥1 snapshot from any book in 20
  minutes" passes if eight books are dead and one is alive. True. It is a
  *floor*, deliberately — the per-book check is the ceiling. But I should be
  honest that between them there is a middle band (most books dead overnight,
  one alive, all on `SERVED` venues) where per-book catches it and heartbeat
  does not — which is fine, because per-book still runs. The gap that
  genuinely remains: **most books dead overnight on venues that are all
  `UNSERVED` for them.** By construction those books were never going to
  produce data, so there is nothing to lose. **Holds, narrowly.**
- **Attack: `check_stamped_coverage` still filters `state IN AU_STATES`, and
  `state` is blank on 8,913 rows.** So it already ignores every TABtouch-only
  race, international *and Australian*. That is a pre-existing hole this brief
  does not close (§2 non-goals). I am flagging it rather than fixing it,
  because widening it needs the country column to be populated first — which
  is why it is Phase 2 work gated on the same flag. **Named, not solved.**

### 11.5 Assumptions I did not verify against live data

Listed honestly, worst first.

1. **That TAB serves overseas meetings under the AU card date, not the
   venue-local date.** This is the load-bearing premise of §5.2. It is
   inferred from code (`fetch_tab` builds the URL from `race_date`;
   `discover_tab(today_str)` queries the AU date) plus the observation that
   TAB-discovered international rows carry Sydney dates and *do* get served.
   **I made no live TAB request to confirm it.** If it were wrong, the flip
   would be safe and D8's first reason evaporates (reasons 2–5 would still
   stand). *Gate:* one read-only `fetch_tab` probe against a known overseas
   meeting on both candidate dates, **before** the build starts. Cheap,
   decisive.
2. **That suppressed fetches carry no second-order value.** A 404 from TAB
   is still evidence the race exists. Nothing consumes it today — but
   `has_bookies_capture` and the coverage flags are written on success only,
   so I believe nothing regresses. **Not proven by test against the derived
   stores** (`model.db`, the analytical extracts). *Gate:* grep the analytical
   repo for any consumer of "book id present but zero snapshots" before
   shipping commit 3.
3. **That the 8-race floor and 21-day window are right.** Chosen by judgement
   from the venue table, not by tuning. A venue racing fortnightly needs
   ~12 weeks to be suppressed. That is conservative in the safe direction, but
   it also means A1's ≥75% target may be missed on the first pass. *Accepted:*
   A1 is measured over 3 days and the floor is a config constant, tunable
   without a deploy.
4. **That `country` resolves for ≥80% of blank-state rows via the venue
   table.** Asserted, not measured. The blank-state population is dominated by
   greyhound/harness venues (`romford`, `monmore`, `yonkers`, `mohawk`,
   `hoosier`, `addington`, `northfield`) which may never appear on a
   state-bearing row. **A9's 80% could well miss.** *Accepted:* A9 is
   informational for the blank-state slice; only the non-blank 95% is a gate.
5. **That the 04:15 restart is safe.** The collector has never been restarted
   on a daily schedule. Graceful shutdown is ~13s and practised, but always
   operator-initiated in a chosen gap. A scheduled restart will eventually
   land while an international race is mid-INTENSIVE. *Fix accepted:* the
   restart timer runs a **gap-aware wrapper** — the same no-NEAR-races check
   used for manual restarts, retrying every 5 minutes until 05:30, then
   skipping the day. It must not be a bare `systemctl restart`.
6. **That v3 is genuinely untouched.** `clients/vps_client/v1/_lookup_api.py`
   reads `race_date` and falls back to it when `scheduled_start` is empty
   (`:218-219`). Phase 0 does not change `race_date` values, so this is safe —
   **but it is a direct dependency of v3's day bucketing on a capture column
   Phase 1 will rewrite.** Recording it here so Phase 1 plans a v3 change it
   would otherwise miss.
7. **That the assessment's traffic figures are usable.** They rest on
   ~5.8 KB/request derived by dividing a reported daily total by a request
   count. I inherited that number for A11 and then argued it downward. The
   *direction* of A11 is robust; the magnitude is not, and A11 should be read
   as "prove it is small" rather than "hit this number".

### 11.6 What I would still change if I could

- The brief spends its risk budget on not-breaking rather than on delivering.
  Phase 0's actual delivered value is: fewer 404s, quieter nights, a louder
  watchdog, no more 10-hour holes, and two new columns. **None of that gets a
  single international bet logged.** That is correct for Phase 0 and it is
  what "stop the bleeding" means, but the operator should not expect to *feel*
  this build except as silence.
- The single highest-value line in it is arguably not in the original scope at
  all: **A7, the collector exits.** Losing the whole overnight card roughly
  weekly is a bigger operational fact than the 404s, and it was mis-read as
  solved.

### 11.7 Verdict

**SAFE WITH FIXES** — where "the fixes" are the five accepted in this review,
all of which are now written into the brief above:

1. `local_race_date` backfill forward-only until the twin repair reports zero.
2. Coverage recompute skipped on days the repair is running.
3. `SERVED`→`UNSERVED` transitions raise an audit + liveness note.
4. `country` written through a guarded fill-if-null path, never the generic
   upsert.
5. The 04:15 restart is a gap-aware wrapper, never a bare `systemctl restart`.

A sixth accepted fix — the second twin census — was **executed during this
review rather than deferred**, and it cleared (§11.1).

Plus **two pre-build probes that must return before code is written**: the TAB
overseas-card-date probe (§11.5 #1) and the analytical-consumer grep
(§11.5 #2).

And **one operator decision — D8** — which is not mine to make.

---

*Planning document. No production code written. All capture-DB access
read-only (`mode=ro`).*
