# International Thoroughbreds — Complexity & Risk Assessment (worklist 0p)

**Commissioned:** S259, 30 Jul 2026. **Assessment only — no code changed.**
**Operator intent (verbatim):** *"there should be no differentiation between
international thoroughbreds and Australian thoroughbreds and their treatment.
It's just another class of race that we have to bring in."*
**Driver:** more promos on international races than anticipated.

Evidence base: live capture DB read-only (`root@187.77.183.9`,
`data/capture.db`, 5.2 GB, read 30 Jul), both code repos, liveness and
collector logs.

---

## 1. Executive summary — what this means for your betting day

**The headline: international racing is already half-inside the system, and
nobody decided that.** This is not a greenfield build. It is a cleanup of
something that walked in the back door around 20 July, plus a decision about
how far to take it.

Right now, on any given night, the system is downloading odds for American,
British, French, Japanese and Turkish races. In the last two weeks it polled
**1,108 international races — slightly MORE than the 1,044 Australian races it
polled in the same period.** Those international races account for **29% of all
bookmaker odds traffic** and **44% of the traffic that goes through the paid
proxy**. That is the single biggest reason your 3 GB Decodo plan ran out on
30 July.

What you are getting for that money is close to nothing usable:

- **No Betfair prices at all.** Not one of the 1,925 international races in the
  last 30 days has a Betfair market attached. That means no true odds, no lay
  price, no EV number, and — critically — **you cannot log a bet on an
  international race in the tool at all.** The tool refuses it by design.
- **No results.** Zero of 1,515 finished international races have a single
  finishing position recorded. Not one. So even if you could log a bet, nothing
  would settle it, and no promo credit (insurance 2nd/3rd, bonus back) could be
  determined by the system.
- **Wrong dates.** Because there is no Betfair market to date the race from, the
  system stamps international races with the *Sydney* calendar date of the
  moment it noticed them. A Del Mar race that ran on 26 July American time is
  filed under 27 July. Twelve international meetings in the last month are
  smeared across up to eight different "race dates" each. This is exactly the
  twin-row disease you just spent S258/S259 killing — reinstated wholesale for
  every foreign race.
- **False alarms at 1am.** Your watchdog has sent **5 "book frozen" alert emails
  overnight** off the back of foreign races, and spends the whole night in a
  "grace period" that leaves it effectively blind. One of those fired at 01:30
  on 30 July naming TAB and TABtouch over 14 overnight foreign races.
- **A landmine with your name on it.** American "Canterbury Park" and Sydney's
  "Canterbury" collapse to the same internal name. They raced four days apart in
  July. When they eventually land on the same day at the same race number, the
  system will silently overwrite one meeting with the other — and the tool will
  hand you the wrong race when you go to log a bet. Same hazard for Ascot
  (Perth / UK), Newcastle (NSW / UK), Sandown (VIC / UK), Warwick (QLD / UK).

**So the honest complexity verdict: MEDIUM-LARGE.** Not because international
racing is exotic — it isn't, and the operator is right that it is "just another
class of race" — but because three foundations were built AU-shaped and all
three have to be widened before a single international bet can safely ride:

1. **Identity** — every race needs a country and a real local date, not a
   Sydney date and a bare venue name.
2. **Truth** — Betfair markets and results have to actually arrive for
   international races, or the entire settlement/EV/promo machinery is blind.
3. **Cost** — the proxy bill and the disk both need re-sizing before you turn
   the tap on, not after.

**The good news:** the two hardest-sounding worries turn out to be the smallest.
Turning on Betfair international discovery is close to a one-line change. And
the collector does not need a new schedule — it is *already* running through the
night; the 7pm stop rule stopped applying weeks ago and nobody noticed.

**The number that will decide the shape of this:** at full "treat it the same"
scope, the proxy bill goes to roughly **13 GB/month, possibly 20 GB**. The plan
you just upgraded to is 10 GB. **This will not fit.** That is a decision you
need to make before any build starts, not a footnote.

**Recommended sequencing (detail in §5):** stop the bleeding first (2–3 hours:
correct the dates, stop the false alarms, stop paying for races you can't use),
then prove the foundations on one jurisdiction (UK/IRE — Betfair-rich,
TAB-covered, sane timezone), then widen. Do **not** attempt a
turn-it-all-on-at-once build. The evidence below shows what happens when
international volume arrives without a decision behind it.

---

## 2. Verify or refute — worklist 0p's preliminary risk read

| 0p | Claim | Verdict | Evidence |
|----|-------|---------|----------|
| (a) | Betfair discovery is AU-country-filtered (`list_au_win_markets`) | **CONFIRMED** | `betfair/client.py:189` — `market_countries=["AU"]`, hardcoded in the only catalogue call. Confirmed empirically: **0 of 1,925** international race rows in 30 days carry a `betfair_win_market_id`. |
| (b) | `_TZ_STATE`/`state_from_timezone` AU-only; `local_racing_day` falls back to Sydney; would mis-stamp `race_date` and regenerate the twin class | **CONFIRMED, but the mechanism is different and worse than described** | The Sydney *fallback inside `local_racing_day`* is **not** the live failure path — Betfair carries `event_timezone` and would date foreign races correctly if it ever saw them. The live failure is that international races never reach Betfair at all, so `match_races` never runs the venue-local rule on them and the date comes from `orchestrator.py:222-223` — `local_racing_day(utc_now, "Australia/Sydney")`, i.e. **Sydney-today**, passed as the `race_date` for every bookmaker-discovered race. Proven live: Del Mar `scheduled_start 2026-07-26T22:38:00Z` (26 Jul 15:38 Pacific) stamped `race_date 2026-07-27`. `state_from_timezone` returning `"AU"` for unknown zones (`storage/racing_day.py:60-64`) is real but currently dormant — `state` on international rows comes from the bookmaker's own meta, which is why the DB already holds `GBR`/`USA`/`FRA`. **Highest-risk call is correct.** See R1. |
| (c) | Collector stops 19:00 Adelaide; international runs overnight, so operating hours + whole scheduler shape change | **REFUTED in practice — already solved by accident** | `STOP_HOUR_LOCAL = 19` (`config/settings.py:88`) only exits when **no races are active** (`orchestrator.py:165-181`). International races keep the tracker list non-empty, so the collector no longer exits: "Past stop hour … exiting" appears **once** in the current log (29 Jul 12:21). Snapshot histogram (Adelaide local, 14d) shows continuous capture 19:00→03:00, and 21:00–23:00 is **100% international**. The scheduler, phase machine and per-race trackers are jurisdiction-neutral (`capture/scheduler.py` uses UTC arithmetic throughout, `:91-99`). **The scheduler does not need reshaping. The VPS and DB do.** See R7, R8. |
| (d) | 10 GB Decodo plan sized on AU-only volume; international will move it again | **CONFIRMED and quantified — and the premise is wrong in your favour** | The 3 GB plan was **not** exhausted on AU-only volume. International is **43.7% of proxied requests already** (262,751 of 601,661 in 14 days). The 10 GB plan was therefore sized on a mix that was already 44% international. But it still does not survive full treatment: modelled at **~13 GB/month**, range 13–20 GB. See R9. |
| (e) | TAB 404s on unserved races (S250); overnight "book frozen" alerts are foreign-racing false alarms; liveness needs a per-book coverage model | **CONFIRMED and quantified** | TAB 404s: **8,621 (24 Jul), 11,124 (25 Jul), 5,749 (26 Jul), 4,918 (28 Jul)**. Liveness log (Mar→Jul): **17 overnight per-book FAILs, 5 "Book frozen" alert emails sent overnight, 232 overnight "staleness grace active" lines**. Live example 30 Jul 01:30 — "4 book(s) frozen mid-card … tab (14 NEAR races); tabtouch (14 NEAR races)", email sent. See R5, R6. |
| (f) | Racing-code classification + venue aliases are AU-centric | **CONFIRMED, with two additions 0p did not name** | `classify_code` (`storage/racing_day.py:67-80`) defaults everything non-greyhound to thoroughbred, so French *trot* meetings at Vincennes land as thoroughbred unless the market name happens to contain "trot"/"pace"; UK **jumps** racing has no code at all. Additions: (i) `normalise_venue`'s `re.sub(r"^[A-Za-z]+-", "", name)` (`matching/race_matcher.py:97`) eats the first hyphen segment of any foreign venue — "Saint-Cloud" → "cloud"; (ii) `METRO_VENUES`/`PROVINCIAL_VENUES` (`config/settings.py:96-108`) contain `ascot` and `newcastle`, so UK Ascot would be graded METRO and UK Newcastle PROVINCIAL by an Australian lookup. See R2, R10. |
| (g) | Results/BSP/settlement coverage must be proven before bets ride it | **CONFIRMED — and coverage is currently ZERO, not partial** | Of 1,515 international races 3+ days old, **0 have any finishing position**; all 12,744 international runners have `results_source = NULL`. `betfair_historical` contains **only the 8 AU states** — no international rows ever imported. Subscription sync: **0 of 1,925** international races have a `subscription_meet_id`; the Racing API client is country-locked in the URL path (`subscription/racing_api.py:285,360` — `/australia/meets`, and `bookmakers/sportsbet.py:31` `BASE_URL = ".../v1/australia"`). See R3. |
| (h) | DR-032 §6 (Betfair market must exist at logging time) is the gate; confirm international coverage | **CONFIRMED — and it is currently a hard block, not a risk** | The rule (`decisions.md:1223`) is enforced at four layers, hardest being the schema: `store/schema/bets.py:60` `betfair_market_id TEXT NOT NULL`. Upstream, `clients/vps_client/v1/_lookup_api.py:257-262` drops market-less rows from the picker **silently**. Net effect: **international races do not appear in the tool's race picker at all today, and cannot be logged.** The gate itself is jurisdiction-neutral — Betfair covers international racing well — so this unblocks the moment §3/R4 is done. |

**Net: 6 of 8 confirmed, 1 confirmed with a different (worse) mechanism, 1
refuted.** The read was good. The two things it missed are the two biggest:
**international is already running** (§3), and **there is no country field
anywhere in the data model** (R2).

---

## 3. The finding that reframes the job: international is already inside

International racing entered capture in volume on **20 July 2026** — a ~10×
step change with no decision behind it:

```
race rows/day, international states      captured (odds taken)
2026-07-15    16                          14
2026-07-18    15                          15
2026-07-19    10                          10
2026-07-20   136                          83     <-- step change
2026-07-23   175                         135
2026-07-25   213                         150
2026-07-29   152                          78
```

Monthly totals: Mar 271, Apr 410, May 399, Jun 375, **Jul 1,925.**

The step coincides with the TAB transport hardening run (S247/S248/S250,
`e215ba1`, `625c650`, `caffb78` — the last one explicitly titled *"TAB 404 =
race not served, never a block (kills the nightly hunt storm)"*). Making TAB
reliable overnight made TAB's overnight international card reliably capturable.
**The exact causal commit is not proven** (see §7) — but the correlation is
10 days ahead of the Decodo blowout and the direction is unambiguous.

**What the system currently does with international races:**

| Dimension | International today | AU today |
|---|---|---|
| Race rows, 30d | 1,925 | ~14,000 |
| Races actually polled, 14d | **1,108** | 1,044 |
| Bookmaker snapshots, 14d | **289,316 (28.7% of all)** | 720,148 |
| Snapshots per race | 261 | 690 |
| Books covering | 2–6 | 8 |
| Betfair market id | **0** | ~45% of rows |
| Betfair snapshots | **0** | ~32,000/day |
| Finishing positions | **0** | 2,171 races /30d |
| BSP (`betfair_historical`) | **0** | 163,809 rows |
| Subscription (Racing API) sync | **0** | 2,435 /30d |
| Racing code stamped | **0 of 1,925** | most |
| `meeting_type` | all `COUNTRY` (fallthrough) | graded |

**Read that table as: you are paying full freight for the least useful half of
the data.** Odds without prices, results, dates or identity.

### Per-book international coverage (races with ≥1 snapshot, 30 days)

| Jurisdiction | Books that actually serve it |
|---|---|
| **NZ** | pointsbet 177, neds 169, ladbrokes 163, playup 161, tabtouch 121, tab 8 |
| **HK** | tabtouch 49, neds 49, ladbrokes 49 — **TAB does not serve HK** |
| **GBR** | tab 100, tabtouch 97 |
| **USA** | tabtouch 156, tab 132 |
| **FRA** | tab 106, tabtouch 99 |
| **JPN** | tabtouch 123, tab 123 |
| **TUR** | tab 134, tabtouch 109 |
| **IRL** | tab 29, tabtouch 27 |
| CAN / BRA / ZAF / KOR / SAU / DEU / MYS | tab + tabtouch, 11–36 each |
| **Sportsbet, Unibet** | **zero international, anywhere** |

**Operator-relevant consequence:** outside NZ and HK, you have **two books** on
international racing — TAB and TABtouch. TAB is your main promo book, which is
consistent with "more promos on international than anticipated." But two books
means: no meaningful best-price comparison, no cross-book sanity check on a
price, and if the promo sits at Sportsbet or Unibet you have **no odds at all**
for that race.

---

## 4. Risk register

Severity: **CRITICAL** = money can be lost or a bet mis-recorded ·
**HIGH** = data corruption or blind operation · **MEDIUM** = cost/noise ·
**LOW** = cosmetic.

---

### R1 — Wrong race dates on every international race; the twin-row class is already regenerating · CRITICAL

**What breaks.** Every international race is date-stamped with the *Sydney*
calendar day on which the collector happened to discover it, not the day it ran
at the track. A meeting that straddles Sydney midnight is split across two
`race_date` values, minting exactly the duplicate-row class DR-036 was built to
eliminate. Because international races carry no Betfair market id, DR-036's
write-time enforcement (`storage/race_resolve.py`, adopt-by-market-id-first)
**cannot engage at all** — it falls straight through to the natural key
`(race_date, venue_normalised, race_number)`, which is the pre-DR-036 twin
generator.

**Evidence.**
- `capture/orchestrator.py:222-223` — `today_str = local_racing_day(utc_now, "Australia/Sydney")`, passed as the `race_date` for every bookmaker-discovered race (`:283`) and into TAB/Palmerbet URL paths.
- `matching/race_matcher.py:322-328` — the venue-local date rule is applied **only** on the Betfair branch. No Betfair market ⇒ the Sydney date stands.
- Live proof: Del Mar row, `scheduled_start = 2026-07-26T22:38:00+00:00` (26 Jul 15:38 Pacific), `race_date = 2026-07-27`.
- Meetings smeared across multiple `race_date` values, 30 days: `thistledown` 8, `vichy` 7, `delaware` 7, `finger lakes` 6, `gavea` 6, `tokyo city keiba` 5, `del mar` 5, `ankara` 5, `kawasaki` 4, `istanbul` 4, `kocaeli` 4, `sha tin` 3.
- DR-036 §2 (`decisions.md:1447-1454`) — write-time enforcement is explicitly market-id-first; there is no fallback identity spine.

**Fix.** Derive `race_date` per-race from the venue's own timezone rather than a
single global "today". Two routes: (i) turn on Betfair international discovery
so `event_timezone` supplies the authority (see R4) — this fixes it for free and
is the right answer; (ii) as a stopgap, map each book's country code to a
timezone and stamp locally. Also needs a historical repair pass over the ~1,900
existing mis-stamped rows.

**Sizing.** Route (i): small, rides R4. Historical repair: medium, and must use
`storage/twin_merge.py`'s journalled merge, never pick-and-drop (DR-036 §3).

---

### R2 — No country dimension anywhere; foreign and Australian venues silently collide · CRITICAL

**What breaks.** The system's race identity is `(date, venue name, race number)`
with **no country field at any layer**. Two same-named racecourses on the same
day at the same race number are, to this system, one race. The write path
resolves the collision by *updating the existing row* — silently overwriting one
meeting's data with the other's. The read path then hands the tool whichever
fragment has more runners, and the tool's own 409 cross-check cannot catch it
because the picker supplied the wrong id in the first place.

**Evidence.**
- `matching/race_matcher.py:127-131` — `normalise_venue` strips a trailing `" park"` suffix. **American "Canterbury Park" therefore normalises to `canterbury`, identical to Sydney's Canterbury.** Live in the DB: `canterbury` carries `NSW` rows on 22 Jul and `USA` rows on 23, 24, 26, 27 Jul — four days apart, no collision yet, pure luck.
- `matching/race_matcher.py:126-127` strips a trailing `(…)` — so Betfair's `(AUS)`, `(GB)`, `(FR)`, `(USA)` country tags are **deliberately discarded** during normalisation.
- `config/settings.py:96-108` — `METRO_VENUES` contains `ascot` (Perth) and `PROVINCIAL_VENUES` contains `newcastle`; UK Ascot and UK Newcastle would inherit those Australian gradings.
- `matching/race_matcher.py:541` — `_find_matching_venue` matches by **substring in both directions** (`venue_norm in grid_key or grid_key in venue_norm`), so a foreign venue will happily bind itself to an Australian one.
- `storage/racing_day.py:97-135` — the existing collision valve `collision_safe_venue_norm` diverts **only when the racing codes differ**. Two thoroughbred meetings never trigger it. This is not a gap in the valve; the valve was never scoped for it.
- `bookmakers/base.py:14-24` — `BookmakerMeta` carries `state: str` and no country.
- Tool side: `clients/vps_client/v1/race_lookup.py:448-452` — `best = max(candidates, key=_completeness_sort_key)`; the only disambiguator available is species code (`:438-446`), which is `T` for both. `ui/web/src/routes/LogPastBet.tsx:374-377` uses `key={m.venue}` on the venue dropdown — **duplicate React key, one option silently wins.**
- `storage/racing_day.py:60-64` — `state_from_timezone` returns the literal `"AU"` for any unknown timezone, so the moment Betfair international discovery is switched on, every foreign race is stamped Australian unless this is fixed first.

**Collision inventory (AU venues with a real international namesake):** Ascot
(Perth / UK / NZ "Ascot Park"), Newcastle (NSW / UK), Sandown (VIC / UK),
Warwick (QLD / UK), Canterbury (NSW / USA — **live in the data**), Wyong·Windsor
class, Kembla/Ripon-type near-misses via the substring matcher.

**Fix.** Add a `country` column to `races` and carry it end-to-end; include it in
the natural key and in venue normalisation (`venue_normalised` becomes
country-qualified, e.g. `gb:ascot`). This is a **schema change** and per DR-035
§7 the reset thread reserves natural-key changes — so this needs an explicit
decision (see §6, D3). Stop-gap available: an alias/deny table for the ~8 known
collisions, which buys time but does not generalise.

**Sizing.** Done properly: medium-large, and it touches the data reset thread.
Stop-gap: small.

---

### R3 — No results, no BSP, no settlement path for international · CRITICAL

**What breaks.** If an international bet could be logged today, nothing would
ever settle it, no insurance trigger (2nd/3rd) could be determined, no free-bet
credit could be verified, and no EV back-test could include it. The money
machinery would be running on operator hand-entry alone for that whole class.

**Evidence.**
- **0 of 1,515** international races 3+ days old carry a single `finish_position`. All 12,744 international runners have `results_source = NULL`. (AU comparator over the same window: 2,171 races with finishes; `betfair_only` 28,741 runners, `subscription` 24,292.)
- `betfair_historical` `state_code` distinct values: `NSW, VIC, QLD, WA, SA, TAS, NT, ACT` — **eight AU states, nothing else.** No international BSP has ever been imported.
- Subscription: **0 of 1,925** international rows have a `subscription_meet_id`. The client is country-locked in the URL path — `subscription/racing_api.py:285` `/australia/meets/{meet_id}/races`, `:360` `/australia/meets`; `bookmakers/sportsbet.py:31` `BASE_URL = "https://api.theracingapi.com/v1/australia"`, docstring `:12` *"thoroughbred AU only (no greyhounds, no harness, no NZ)"*.
- Settlement worker is Betfair-only by design and needs a market id; with none, international races are invisible to it.
- Tool-side result door: `ui/api/routers/bets.py:2988` parses `^\s*R(\d+)\b` from the Betfair market name. **UK/IRE Betfair market names carry no race number** (they are e.g. `"1m2f Hcap"`, `"Class 4 Stks"`), so `_extract_race_number` (`clients/betfair_client/v1/_translation.py:77`) returns `None` and the race-result door returns `available=False, reason="race number unresolvable from leg"` **permanently**.

**Fix.** Three independent supplies must be proven, in this order:
1. **Betfair market ids** (R4) — unlocks in-play settlement, BSP and the tool gate.
2. **The Racing API's non-AU products** — it does publish GB/IRE racecards and results under different endpoints; the client needs a second regional path, not a rewrite.
3. **The race-number convention** — international Betfair markets need a race number synthesised from off-time ordering, or the tool needs to stop requiring one.

**Sizing.** (1) small. (2) medium — new endpoint family, new response shape,
new venue harmonisation. (3) medium, tool-side, and it is a **hard blocker**
for the results door, not a nice-to-have.

---

### R4 — Betfair discovery is AU-locked in five places, capture *and* tool · HIGH (but the cheapest fix on this list)

**What breaks.** Everything downstream of "does a Betfair market exist" — dating,
identity, EV, lay, settlement, and the tool's ability to show the race at all.

**Evidence.**
- Capture: `betfair/client.py:189` — `market_countries=["AU"]`. One line. Method names `list_au_win_markets` / `_list_au_markets` (`:102`, `:126`) are cosmetic.
- Tool REST: `clients/betfair_client/v1/_translation.py:289` — `"marketCountries": ["AU"]`.
- Tool live stream: `clients/betfair_client/v1/_stream_transport.py:118-125` — `RACING_MARKET_FILTER = {"eventTypeIds": ["7","4339"], "countryCodes": ["AU"], "marketTypes": ["WIN","PLACE"]}`; scope enum literally named `MarketSubscriptionScope.RACING_AU` (`:142-145`). **Without this, international races get no live prices in the tool even if capture has them.**
- `clients/betfair_client/v1/racing_catalogue.py:8-9,121` — docstrings confirm AU-only.

**Non-obvious consequences of flipping it:**
- **Catalogue volume and the weight cap.** `PAGE_SIZE = 60` exists because Betfair's 200-point response-weight cap kills larger pages (`betfair/client.py:155-165`), and `MAX_PAGES = 50` (~3,000 markets) is the truncation alarm. AU today is 400–600 WIN markets/day across 3 codes. Global thoroughbred WIN+PLACE will multiply this several-fold; **the page cap and the 12-hour discovery window (`orchestrator.py:227`) both need re-sizing, and the truncation alarm at `betfair/client.py:141-145` will start firing if they are not.**
- `MAX_MARKETS_PER_BOOK_REQUEST = 10` (`betfair/client.py:35`) means price polling cost scales linearly with tracked markets — this is the Betfair API-weight budget, separate from the proxy budget.
- **The moment this flips, `state_from_timezone` stamps every foreign race `"AU"`** (`storage/racing_day.py:60-64`) unless R2 lands first. **Ordering matters: R2 before R4.**

**Fix.** Parameterise the country list in all five places; re-size page/window;
fix `state_from_timezone` first. **Sizing: small-medium** — the code change is
trivial, the volume tuning is the work.

---

### R5 — Wasted proxy spend on races that cannot be used; TAB 404 storms · HIGH

**What breaks.** You are paying residential-proxy bandwidth to fetch odds for
races that are un-loggable, un-settleable and invisible in the tool — plus a
large volume of pure-waste 404s for races TAB does not serve.

**Evidence.**
- TAB 404s/day from the collector log: **8,621 (24 Jul), 11,124 (25 Jul), 5,749 (26 Jul), 1,013 (27 Jul), 4,918 (28 Jul).**
- `bookmakers/tab.py:282-291` raises `TabRaceNotFound` on 404; `:177-186` documents *"overnight overseas races TAB doesn't cover 404 on EVERY fingerprint"*; orchestrator absorbs it without a breaker hit (`capture/orchestrator.py:884-892`) — correct behaviour (S250, `caffb78`), but it means the waste is now **silent and unbounded**.
- The 404 class is structural: TAB does not serve HK (0 of 51 HK races) and barely serves NZ (8 of 257), yet those meetings are discovered by other books and hunted at TAB anyway.
- On a non-404 block, `_HUNT_MAX_TRIES = 2 × 6 fingerprints = 12` attempts at 20 s timeout (`bookmakers/tab.py:111-116`) — worst case ~13 requests and ~4 minutes per race.

**Fix.** A per-book **coverage model**: record which jurisdictions each book
actually serves (the table in §3 is the seed data), and skip fetches for
book×jurisdiction pairs with no coverage. This is cheap, pays for itself
immediately in proxy bytes, and is the same data structure R6 needs.

**Sizing: small.** Highest value-per-hour item in this document.

---

### R6 — The watchdog is blind all night and cries wolf about foreign races · HIGH

**What breaks.** Your overnight safety net is simultaneously too loud (false
"book frozen" emails) and too quiet (its main checks are permanently graced off).
Both because it has no concept of jurisdiction.

**Evidence.**
- `scripts/liveness_check.py:93` — `AU_STATES = ("NSW","VIC","QLD","SA","WA","TAS","NT","ACT")`, used at `:232` `HAVING MAX(CASE WHEN state IN (…) THEN 1 ELSE 0 END) = 1`. **Check 7 (stamped coverage) therefore ignores international races entirely** — so international capture health is genuinely unmonitored. Correct today (they have no Betfair identity to check); becomes a hole the moment R4 lands.
- `check_per_book_staleness` (`:369+`) has **no state filter at all** and uses `_BOOK_ID_COLUMNS` for all 9 books. Overnight the only races in its window are foreign, so it evaluates books against races they were never going to cover.
- Measured over the full log (4 Mar → 30 Jul): **17 overnight (19:00–08:00) per-book FAILs, 5 "Book frozen" alert emails sent overnight, 232 overnight "staleness grace active" lines vs 5 in daytime.**
- Live sample, 30 Jul 01:30 — `Per-book: FAIL — 4 book(s) frozen mid-card … ladbrokes (6 NEAR races); neds (6 NEAR races); tab (14 NEAR races); tabtouch (14 NEAR races)` → `Alert sent: Book frozen`.
- The 232 overnight grace lines are `"No market-bearing races underway >60m — Betfair staleness grace active"` — because **no international race has a Betfair market**, the Betfair-freshness check never arms overnight. If capture wedged at midnight you would not hear about it until morning.
- `COLLECTOR_DAY_END = (19, 0)` (`:75`) still encodes the daily-session assumption that reality has already abandoned.

**Fix.** Feed the R5 coverage model into liveness: a book is only a staleness
candidate for jurisdictions it covers; extend check 7 past `AU_STATES` once
international races carry Betfair identity; retire or widen the 08:25–19:00
collector window.

**Sizing: small-medium**, and it should ship **with** R5 (same data).

---

### R7 — VPS disk will not absorb full international treatment for long · MEDIUM

**Evidence.** `capture.db` = **5.2 GB** (1,268,456 pages × 4,096). Disk: 48 GB
total, **24 GB free (50% used)** — and a 5.1 GB pre-twin-repair backup is sitting
on the same volume. Current growth ≈ **107,000 rows/day** (~75k bookmaker + ~32k
Betfair) ≈ **~48 MB/day**.

Full international treatment adds, per day: ~34,000 extra bookmaker rows (lifting
international races from 261 to AU-equivalent 690 snapshots each) plus ~11,500
Betfair rows (international currently has **zero**) ≈ **+45,500 rows/day, ~+43%**
→ **~68 MB/day ≈ 25 GB/year**. Against 24 GB free that is **roughly 12 months of
runway**, before the reset thread's own space needs. Liveness alerts at 85% disk
(`scripts/liveness_check.py:88`).

**Fix.** Decide retention/rollup before switching on (§6 D5), not after. Note
the 8-Jul disk-full incident is the standing substrate here.

---

### R8 — The collector's operating model needs no reshaping, but its *supervision* does · MEDIUM

The scheduler is genuinely jurisdiction-neutral: `RaceState.minutes_to_start`
uses `datetime.now(timezone.utc)` (`capture/scheduler.py:91-95`), every phase
threshold is minutes-to-jump, and the circuit breakers are per-book not per-day.
**Nothing about the phase machine or per-race trackers breaks on international.**

What does need attention:
- The collector now runs ~20 hours/day instead of ~11. Betfair session keep-alive is every 20 min (`config/settings.py:16`) and re-login on failure (`orchestrator.py:187-204`) — this has been exercised, but never *designed* for a 20-hour session.
- `DISCOVERY_INTERVAL = 1800` with a 12-hour lookahead (`orchestrator.py:227`) means every discovery pass downloads a full whole-day card from **every** book (`bookmakers/*.py` discover endpoints). Extending the lookahead for international multiplies those payloads.
- There is no longer a natural "quiet window" for backup, VACUUM or migration. `backup.log` and the twin-repair run both assumed one.

**Fix.** Small — mostly a decision (§6 D4) plus a maintenance window.

---

### R9 — The 10 GB Decodo plan does not survive this · MEDIUM (hard operational constraint)

**Today's proxied split (14 days, requests):**

| Book | Route | AU | International |
|---|---|---|---|
| tabtouch | Decodo | 91,617 | **125,251** |
| tab | Decodo (own gate, `country-au`) | 62,763 | **114,771** |
| ladbrokes | Decodo | 92,682 | 11,390 |
| neds | Decodo | 91,848 | 11,339 |
| **Proxied subtotal** | | **338,910** | **262,751 (43.7%)** |
| sportsbet, unibet, pointsbet, playup | **direct** (`config/settings.py:55`) | 381,430 | 26,565 |

**The model.** 601,661 proxied requests / 14 d = **42,976/day**. Against the
observed ~200–300 MB/day (SESSION_259 §12), that is **~5.8 KB/request**.

Bringing international to AU-equivalent intensity (261 → 690 snapshots/race)
takes international proxied requests to ~696,000/14 d. Total proxied →
**~1,035,000/14 d = 73,900/day × 5.8 KB ≈ 429 MB/day ≈ 12.9 GB/month.**

**Conclusion: ~13 GB/month at minimum scope, and 13–20 GB once Betfair-driven
discovery surfaces international meetings TAB never listed. The 10 GB plan
will be exhausted in roughly three weeks of a 30-day cycle.**

**Also note:** every proxied request currently exits from an **Australian**
residential IP (`capture/proxy.py:39-40` `au.decodo.com:10000`; `bookmakers/tab.py:213-217`
`country-au`). For AU books that is load-bearing. For UK/IRE/FR books — if you
ever add books that serve those markets directly — an AU exit is a geo-mismatch
and may be blocked or price-differentiated. **You could be shown different prices
than you can actually bet.**

**Fix.** Either upsize the plan, or run the traffic diet already filed as a
follow-up in SESSION_259 §12 (cadence and compression wins) **before** switching
international on. R5's coverage model is the cheapest lever: it removes the
404 waste at zero risk to S257's latency work.

---

### R10 — Racing-code and venue classification produce quietly wrong labels · MEDIUM

- `classify_code` (`storage/racing_day.py:67-80`): non-greyhound → harness if the market name contains "pace"/"trot"/"mobile" or the venue is in `_HARNESS_VENUES` (16 Australian tracks) → else **thoroughbred**. French *trot attelé* at Vincennes lands as thoroughbred; a UK flat race named "Pacemaker Stakes" lands as harness.
- **UK/IRE jumps racing has no code at all.** Cheltenham hurdles are indistinguishable from Flemington flat in this model, yet field size, place terms and attrition differ structurally — and the EV place model is trained on flat.
- `normalise_venue` damage on foreign names (`matching/race_matcher.py`): `:97` `^[A-Za-z]+-` strips hyphen prefixes (Saint-Cloud → `cloud`, Maisons-Laffitte → `laffitte`); `:100-106` strips leading `New|Old|South|North|…`; `:127` strips trailing parentheses, collapsing `Kempton (AW)` and Kempton turf into one venue; **no `unicodedata` normalisation anywhere in the file**, so accented French venue names will never match across sources.
- `bookmakers/tabtouch.py:226-229` — the discovery venue regex is `[A-Z][A-Z0-9 \-\']+?` terminated by an Australian **2–3 letter state suffix**. Cannot match accented characters; foreign venues fall back to the raw venue code (`:223`).
- `config/settings.py:96-124` — `METRO`/`PROVINCIAL`/`SYNTHETIC` venue sets are Australian; every international venue currently falls through to `COUNTRY` and `turf`. Wrong for Sha Tin, Meydan, and every US dirt/AW track.
- **Duplicate country codings already in the data**: `NZ`/`NZL`, `GB`/`GBR`, `ZAF`/`SAF`, `AUS` alongside the state codes — different books disagree and nothing reconciles them. This will fragment any country-based logic built on top.

---

### R11 — Tool-side: everything is filed by the Adelaide calendar day · HIGH

`Australia/Adelaide` is hardcoded in **22 non-test source locations** in
bethub-v3, with no configuration hook.

- `clients/vps_client/v1/_lookup_api.py:208-221` `_keep_on_day()` — *"refine the ±1-day union to Adelaide day D"*; `:86-107` converts every `scheduled_start` to Adelaide before bucketing.
- `ui/api/routers/racing.py:142,668` — `target_day = day or datetime.now(ADELAIDE_TZ).date()` **defines "today's races"**.
- `ui/api/routers/bets.py:134,952,957` — **P&L and BetLog period boundaries** are Adelaide midnight-to-midnight.
- `ui/web/src/components/RaceListSidebar.tsx:24-30` `adelaideTodayIso()`; `ui/web/src/routes/BetLog.tsx:174-201` date presets.
- `ui/api/settlement_worker.py:162,194` — once-per-Adelaide-day watchdog gate.

**What this means for your day.** A Santa Anita card you think of as "Sunday"
appears in the tool under **Monday**. A Hong Kong Wednesday night card files
under Thursday. A day's P&L slices a UK or US session in half. Jump-time
countdowns are safe (`RaceListSidebar.tsx:32-58` uses pure epoch arithmetic) —
it is only the *day bucketing* that is wrong, but the day bucket is what the
picker, BetLog and P&L all key on.

**Fix.** Either accept "Adelaide day is the operator's day" as an explicit,
documented convention (defensible — you bet from Adelaide), or introduce a
per-race local date. **Recommend the former** (§6 D6): it is far cheaper and
matches how the operator actually experiences a betting day, provided the race
picker *shows* the venue-local date so nothing is ambiguous.

---

### R12 — Promo model cannot express "international" at all · HIGH

`store/schema/promos.py:60-99` — `promo_template` has `kind`, `refund_positions`,
`return_type`, `return_pct`, `cap`, `fb_expiry_days`, `position_min_field`;
`promo` instance has `book_id`, `start_date`, `end_date`, `instance_label`.
**There is no jurisdiction, country, venue-list, meeting-scope or code
restriction field anywhere.** An operator cannot today express *"this promo is
AU metro thoroughbreds only"* or *"excludes international"*, except as free text
in `default_terms`/`notes` that nothing reads.

Given the driver for 0p is *more promos on international races*, this is not a
side issue — **it is the feature the operator is actually asking for**, and it
does not exist. Worse, promo terms are known to differ per account at the same
book (standing Cat-4 lesson), and international eligibility is exactly the kind
of clause that varies.

Compounding: `ui/web/src/ev/promoSpec.ts:16-19,48` hardcodes
`position_min_field: null` — the field-size clause was deliberately dropped
tool-wide (S255, operator decision, do not re-raise). International field sizes
are structurally different (UK handicaps 5–8, HK 12–14, FR up to 20), so the
clause the operator chose to monitor personally becomes materially harder to
monitor across four jurisdictions' conventions.

---

### R13 — EV and promo-EV are AU-calibrated; they will produce confident wrong numbers · HIGH

S253 validated the promo-EV indicator against **31,995 AU runners**. That
calibration does not transfer, and the code gives no signal when it is out of
domain.

**Merely miscalibrated (runs, silently biased):**
- `ui/web/src/ev/evEngine.ts:32-34` — `GAMMA=0.77, DELTA=0.62, EPSILON=0.48`, header comment `:21-24` *"Calibrated on AU racing 2025-2026 … load-bearing"*. Duplicated in `racePortfolio.ts:126-128`; validation corpus is *"1,676 real settled races"* (`racePortfolio.ts:434-441`) — all AU.
- `evEngine.ts:43` — `DEFAULT_FB_CONVERSION_RATE = 0.65`, *"Empirical AU matched-betting conversion via lay hedge"*. International lay liquidity is thinner outside UK/IRE, so 65% is optimistic where it matters most.
- `ui/web/src/ev/raceWatcher.ts:50-88` — the whole grade-threshold block is calibrated on named AU cases (Pinjarra, Kilmore, Albion Park R10); `CODE_VOLUME_FLOOR = {T:50_000,…}` is AUD against AU pool depths.
- `ui/web/src/ev/softOddsLadder.ts:2` — *"AU fixed-odds bookmaker price increments"*; will mis-quantise non-AU book prices.

**Structurally wrong, not just uncalibrated:**
- `ui/web/src/ev/commission.ts:12` — **8% commission fallback** is the AU Betfair MBR. UK/IRE markets are commonly 2–5%. Applied to a UK market this **over-charges EV by 3–6 points on every winning leg** — i.e. it will make genuinely good international promo bets look bad, in exactly the direction that costs you money by omission.
- `evEngine.ts:97-176` — the place model computes 2nd/3rd/4th only; `racePortfolio.ts:444-445` — *"Positions beyond 4th are filled in arbitrary order: no promo we model pays anything there."* **UK/IRE each-way terms routinely pay 5th and 6th** in 16+ runner handicaps. Those promos are **inexpressible**, not merely mis-valued. Note `promo_template.kind` already has an unused `'ew_cashback'` value.
- `clients/vps_client/v1/_lookup_api.py:46-59` — the `NO_MARKET_NORMAL_LOW = 0.40 / HIGH = 0.90` health band is calibrated on *"14 captured days (2026-06-16..06-29)"* of AU capture. International changes the denominator and this band will start firing for reasons unrelated to any regression.

**Does S253's calibration transfer?** Structurally, the *method* does — win
chance from de-overrounded Betfair mid, place chance from corrected Harville.
The *constants* do not, and there is no reason to assume they do: field-size
distributions, favourite-longshot bias and market formation timing all differ
by jurisdiction. **The S253 result should be treated as unproven outside AU
until re-run on international data — which requires R3 (results) first.**
Until then, an international EV number is a confident-looking guess.

---

### R14 — Currency · MEDIUM

`workflows/balances/v1/balance_derivation.py:74` `_CURRENCY = "AUD"`, and `:93-94`
defines `BalanceCurrencyMismatchError` — *"Raised if an event in the substrate
references a non-AUD currency"* — a **hard raise**. This is fine as long as you
bet international races through Australian accounts in AUD (which is the actual
situation). It becomes a blocker only if a foreign-domiciled account is ever
added. **Flagging it so it is a known boundary, not a surprise.**

---

## 5. Phased build proposal

Sizing is in operator sittings, not hours. Each phase is independently
shippable and independently valuable.

### Phase 0 — Stop the bleeding (½ sitting) · DO THIS REGARDLESS OF THE 0p DECISION

Even if the operator decides *not* to bring international in, these are
straight wins on the system as it stands today:

1. **Per-book jurisdiction coverage model** (R5) — seed from the §3 table; skip
   book×jurisdiction fetches with no coverage. Kills most of the 5,000–11,000
   daily TAB 404s and a slice of the proxy bill.
2. **Feed it to liveness** (R6) — a book is only a staleness candidate where it
   covers. Kills the overnight "book frozen" false alarms.
3. **Correct the international date stamp** (R1, stopgap) — country-code →
   timezone map so `race_date` is the venue-local day. Stops new date-twins
   accruing at ~150 rows/day.
4. **Retire the 08:25–19:00 collector-window assumption in liveness** (R6/R8) —
   reality has already moved.

**Deliverable:** less noise, lower bill, no new corrupt rows.
**Risk:** low. No new capability, no new surface.

### Phase 1 — Identity foundation (1–1.5 sittings) · PREREQUISITE FOR EVERYTHING

5. **Country dimension end-to-end** (R2) — `races.country`, carried from every
   book's meta and from Betfair `countryCode`; country-qualified
   `venue_normalised`; reconcile the `NZ/NZL`, `GB/GBR`, `ZAF/SAF` duplicates;
   fix `state_from_timezone` so unknown zones do not stamp `"AU"`.
6. **Venue normalisation made international-safe** (R10) — unicode
   normalisation, guard the hyphen-prefix and directional-prefix strips, keep
   the `(AW)`/country parenthetical instead of discarding it, replace
   `_find_matching_venue`'s bidirectional substring match with something that
   cannot bind Ascot to Ascot Vale.
7. **Historical repair** of the ~1,900 mis-dated/mis-keyed international rows,
   via `storage/twin_merge.py`'s journalled merge (DR-036 §3), never
   pick-and-drop.

**Gate before Phase 2:** a full day where every international race carries the
correct venue-local date and a country, and no AU/international venue key
collides. **Do not proceed without this gate.**

### Phase 2 — Truth supply, one jurisdiction (1–2 sittings)

Pick **UK + IRE** as the pilot: Betfair-rich, TAB-covered, no overnight
inversion, promo-relevant, and English-language venue names.

8. **Betfair international discovery** (R4) — parameterise the five `["AU"]`
   filters; re-size `PAGE_SIZE`/`MAX_PAGES`/lookahead; verify the truncation
   alarm behaves.
9. **Race-number synthesis** for markets whose names carry no `R\d` (R3) —
   order by off-time within meeting; both capture and tool.
10. **Results supply** — the Racing API's GB/IRE product, plus Betfair
    settlement as the primary. Prove finishing positions land before anything
    else.
11. **Betfair international BSP** into `betfair_historical`.

**Gate before Phase 3:** a UK/IRE race captured with a Betfair market, correct
date, correct country, a settled result, and a BSP — end to end, on real data,
verified by the operator. Per the standing end-to-end-chains rule, this is a
**chain** proof, not a per-surface one.

### Phase 3 — Tool side (1–1.5 sittings)

12. **Betfair country filters in the tool** (R4) — REST catalogue **and the live
    stream**, or international races have no live prices.
13. **Commission by market**, not the 8% AU fallback (R13) — this is a
    *money-correctness* fix, not a polish item.
14. **Country visible in the picker and race list** (R2/R11) — the venue
    dropdown must not have two "Ascot" options with the same React key; show the
    venue-local date alongside the Adelaide day.
15. **Promo jurisdiction scope** (R12) — the field the operator actually asked
    for: express *"applies to / excludes international"* on a promo template.

### Phase 4 — Widen, and re-validate the numbers (open-ended)

16. Add jurisdictions one at a time, each behind the Phase-1 gate.
17. **Re-run the S253 promo-EV calibration on international results** once
    Phase 2 has supplied them (R13). Until then, international EV carries an
    explicit "uncalibrated" marker in the UI.
18. Each-way 5th/6th place terms if UK/IRE promos need them (R13).

**Total rough sizing: 4–6 sittings to a trustworthy UK/IRE capability**, plus
open-ended widening. Phase 0 alone is half a sitting and pays for itself.

---

## 6. Decisions the operator must make

### D1 — The proxy bill. *(Blocking. Decide before any build starts.)*
Full treatment models at **~13 GB/month, range 13–20 GB**. The plan is 10 GB.
- **(a)** Upsize to 25 GB+ now and build freely.
- **(b)** Run the traffic-diet review (already filed, SESSION_259 §12) first, then re-model.
- **(c)** Cap international to the jurisdictions with real promo value and skip the rest.

**Recommendation: (b) then (c), with (a) held in reserve.** Phase 0's coverage
model is a diet measure that costs nothing and risks nothing — it should land
before you spend more money. Then decide from a clean number. Note S257's TAB
latency work must not be traded away for bytes.

### D2 — Scope: which jurisdictions?
Coverage today is **two books (TAB + TABtouch) outside NZ and HK**.
- **(a)** Everything Betfair lists.
- **(b)** UK, IRE, FR, HK, JPN, USA, NZ (the 0p list).
- **(c)** Where you actually get promos and ≥2 books: UK, IRE, FR, USA, JPN, plus NZ/HK which already have 3–6 books.

**Recommendation: (c), starting with UK+IRE as the pilot.** Turkey, Brazil,
Korea, Uruguay, Chile and Malaysia are currently consuming capture budget with
no promo case behind them — I would drop them explicitly rather than by
accident. **This is a question only you can answer: where are the promos?**

### D3 — The country dimension vs. the data reset. *(Architectural.)*
R2 wants `country` in the natural key. DR-035 §7 reserves natural-key changes
for the data reset.
- **(a)** Add `country` as a normal column now and fold the key change into the reset.
- **(b)** Do the key change now, ahead of the reset.
- **(c)** Alias table for the ~8 known collisions only.

**Recommendation: (a).** It captures the information immediately (so nothing is
lost and the reset has clean inputs), respects the reset thread's discipline,
and country-qualified `venue_normalised` gets most of the protection without
touching the index. **(c) alone is not enough** — the substring matcher at
`race_matcher.py:541` will find collisions an alias table never anticipated.

### D4 — What is a "racing day" now?
The collector already runs ~20 hours. There is no quiet window for backup,
VACUUM or migration.
- **(a)** Formalise continuous operation; carve an explicit maintenance window (e.g. 04:00–06:00 Adelaide, the current natural lull).
- **(b)** Keep a hard nightly stop and accept losing overnight international.

**Recommendation: (a) with an explicit 04:00–06:00 window.** The data already
shows that window is nearly empty (130 snapshots at 04:00 vs 128,460 at 14:00).

### D5 — Disk and retention.
~12 months runway at full international treatment, on a disk that is already
50% full and carrying a 5.1 GB backup.
- **(a)** Grow the VPS disk.
- **(b)** Rollup/prune old snapshot detail.
- **(c)** Defer to the data reset.

**Recommendation: (a) now (cheap, removes a class of 3am problem), (b) designed
into the reset.** The 8 Jul disk-full incident is the precedent.

### D6 — Whose day is "today"?
- **(a)** Adelaide day everywhere; show the venue-local date in the picker so nothing is ambiguous.
- **(b)** Per-race local date, with a timezone-aware picker and P&L.

**Recommendation: (a).** You bet from Adelaide; your P&L day is an Adelaide day.
(b) is a large tool-side change across 22 hardcoded locations, P&L boundaries and
the settlement worker's once-per-day gate, for a benefit you would not feel.
**But (a) is only safe if the picker shows the venue-local date** — otherwise
"Santa Anita 27 July" means two different things to you and to the tool.

### D7 — Do international EV numbers get shown before they are calibrated?
- **(a)** Show them, marked "uncalibrated".
- **(b)** Withhold the EV column on international until re-validated.

**Recommendation: (a) with a visible marker**, consistent with the standing
"allow → flag → review later" rule — warnings inform, they do not block. But
fix the commission fallback (R13) **first**: an 8% charge on a 2% market is not
an uncertainty, it is a wrong number, and it biases against taking good bets.

---

## 7. What I could NOT verify

1. **How many Betfair international markets there actually are per day.** No
   Betfair credentials were used in this assessment. All volume estimates for
   post-R4 discovery are reasoned from AU numbers and the observed TAB
   international card, not measured. **This directly affects the D1 cost
   decision and the `PAGE_SIZE`/`MAX_PAGES` sizing in Phase 2** — measure it
   with a single read-only catalogue call before committing to a plan tier.
2. **The exact commit that let international volume in on 20 July.** The
   correlation with the TAB transport hardening run (S247/S248/S250) is strong
   and the step change is unambiguous, but I did not bisect it. Worth 20 minutes
   before Phase 0, because if it was a *deliberate* change there may be a reason
   I have not accounted for.
3. **Whether the Racing API subscription actually covers GB/IRE/FR/US results
   under the current plan.** I confirmed the client is hard-scoped to
   `/v1/australia` and that other regional endpoints exist in that API family. I
   did **not** confirm your subscription tier includes them, or what their
   response shape is. **This is a hard prerequisite for Phase 2 item 10** —
   check the account before building.
4. **Real per-request byte sizes.** The ~5.8 KB/request figure is derived by
   dividing the reported ~200–300 MB/day by measured request counts. No adapter
   logs response sizes. The 13 GB/month figure inherits that uncertainty; the
   *direction* (10 GB is not enough) is robust, the precise number is not.
5. **Whether TAB/TABtouch international prices are actually bettable at the
   quoted price**, and whether TAB's promos apply to international races on your
   specific accounts. This is the commercial premise of the whole item and only
   you can confirm it. Promo terms are known to differ per account at the same
   book.
6. **Bookmaker responses to international requests.** No live requests were
   made. Claims about `region=domestic` (Entain), `countryCodes` (Unibet) and
   PointsBet's AU/NZ filter are read from code, not probed. In particular
   PointsBet's own code comment warns that international meetings *"have no
   fixed-odds markets and produce empty snapshots"* — if true across books, some
   international coverage may be tote-only and useless for fixed-odds promos.
   **Worth a probe before D2.**
7. **Whether any Australian/international venue-name collision has already
   corrupted a row.** I found the Canterbury near-miss (4 days apart) and
   confirmed no natural-key collision in the last 60 days. I did not sweep the
   full history.
8. **Betfair market-name conventions per jurisdiction.** The claim that UK/IRE
   market names carry no race number is from the code's own assumptions and
   general knowledge, not from live catalogue data. It drives Phase 2 item 9 and
   should be confirmed with the same read-only call as item 1.

---

*Assessment only. No code was changed in either repo. All capture-DB access was
read-only (`mode=ro` URIs).*
