# S268 — the country-stamping alarm after the Phase 1 deploy

Written 6 Aug 2026, ~07:20 ACST, immediately after the 04:40 Phase 1
deploy landed.

## What the alarm was saying

Two venues failed the F4 census (`same base venue under a qualified AND
an unqualified key`) every 45 minutes from the migration onward:
`newmarket (6 qualified / 6 bare)` and `sandown (6 qualified / 12 bare)`.

They were **two different problems wearing the same message.**

## 1. Sandown — the alarm was wrong. FIXED (`efcde0d`)

Sandown Park's greyhounds arrive stamped `country='AU'` with a **blank
state** — the AU dog and harness feeds simply do not supply one. The
census only excused a bare row if it carried an Australian *state*, so a
plainly-Australian row read as "bare" beside `sandown|gb`.

That is precisely the cry-wolf the clause's own comment exists to
prevent ("...teaches the operator to ignore the one tripwire that can
see an F1 escape"). The clause had the intent written down and the
implementation one condition short.

**Fix:** an explicit `AU` stamp is plainly Australian whether or not the
feed bothered with a state.

**Detection is unchanged, and this was checked rather than assumed:**
- The flap this census guards writes a row whose country could NOT be
  resolved — that lands `NULL`, not `'AU'`. Still fails.
  (`test_the_flap_still_fails_when_the_bare_row_is_not_australian`)
- A foreign state code still counts even under an AU stamp, so clause
  1's contradiction cannot be laundered through here.
  (`test_a_foreign_state_on_the_bare_side_still_fails`)

Suite 624/624 green. Pushed to the VPS and **confirmed live at 21:45
UTC** — sandown is gone from the check, newmarket remains.

## 2. Newmarket — the alarm was RIGHT. Open.

The six bare `newmarket` rows for 6 Aug are **empty shells**: 0 runners,
0 odds snapshots, no race name, no start time, `capture_status=PENDING`.
127 of the 128 bare newmarket rows ever written are empty.

The one field that identifies them:

    tabtouch_race_id = 2026-08-06/orb/1

**TABtouch.** This is verbatim the case the census comment describes —
"the venue survives the pass as a TABtouch-only blank-state row, country
cannot be resolved, the key comes out bare". The census found the thing
it was built to find, on its first day of really being able to.

### The class is much bigger than Newmarket

TABtouch-only rows with **no country at all**, last 30 days:

| venue | rows | actually |
|---|---|---|
| q1 lakeside | 231 | AU |
| northfield | 200 | **US** harness |
| hoosier | 198 | **US** harness |
| yonkers | 166 | **US** harness |
| mohawk | 151 | **US/CA** harness |
| mandurah | 149 | AU |
| monmore | 131 | **GB** dogs |
| sheffield | 123 | **GB** dogs |
| romford | 113 | **GB** dogs |
| sunderland | 98 | **GB** dogs |
| harlow | 72 | **GB** dogs |
| dunstall | 74 | **GB** dogs (Dunstall Park) |
| ascot | 83 | **ambiguous** — Ascot WA vs Ascot GB |
| cambridge | 78 | ambiguous |

So TABtouch carries international greyhound and harness coverage and
tags **none** of it with a country. Phase 1's rekey could not touch these
rows: it only rewrites rows whose country is already known and non-AU.

### Why a venue-name lookup will not fix it

`ascot` is Ascot (WA) *and* Ascot (GB). `sandown`, `newcastle`,
`cambridge`, `newmarket` are all live homonyms. The disambiguator has to
come from TABtouch's own meeting identity — the `orb`-style code in
`tabtouch_race_id`, or whatever jurisdiction field the feed exposes —
not from the venue string.

### Consequences, in order of how much they matter

1. **Cry-wolf returns.** The census will fail on every Newmarket race
   day (and Ascot, and Cambridge) until the country is resolved. Today's
   six age out of the 48-hour window around 14:15 UTC on 7 Aug.
2. **Twin risk.** These shells are empty *today*. The moment anything
   attaches to one, it is a twin of the properly-keyed `|gb` row — the
   DR-036 class, re-minted through a door Phase 1 did not close.
3. **Not a money problem right now.** 0 runners, 0 odds, PENDING. No bet
   can be placed against them and no price is being read from them.

### Recommendation

Resolve country from the TABtouch meeting identity, then let the
existing rekey migration key them properly. Scope it with the
international thoroughbred work (0p) rather than as a hotfix — the dogs
and harness are secondary to the operator's promo case, and the fix
needs the feed's own jurisdiction field rather than a guess.

**Do NOT silence the census for newmarket.** It is currently the only
thing watching this door.

---

# S268 — OPERATOR SCOPE CUT (6 Aug, same sitting)

> "We don't need international racing on the VPS, just USA, Hong Kong,
> and UK/Ireland races to show in the racing menu of the tool."

The wide international programme is OFF. The deliverable is narrow: five
countries in the racing menu.

## What the racing menu actually reads

The menu (`RaceListSidebar`) is **Betfair-catalogue-driven**, not
capture-driven. `country_code` on each meeting line comes from the
Betfair market catalogue. The VPS capture supplies the *bookmaker prices*
behind those races, and `race_lookup` matches them on
**date → venue → race number** — country is a display tag there, never a
match key.

So the menu is one config line, not a capture project.

**DONE:** `BetHub.command:322` → `AU,GB,IE,US,HK` (was pinned to `AU`).
No code change, no rebuild — this is the §3.5 lever, designed for exactly
this. Takes effect on the next app start. AU stays first because only the
home country's catalogue call is load-bearing (F13).

## Where the five stand, measured

| | in capture | rows | note |
|---|---|---|---|
| **USA** | yes | 2,323 | tagged `US` correctly |
| **UK** | yes | 2,455 | tagged `GB` correctly |
| **Ireland** | yes | 288 | tagged `IE` correctly |
| **Hong Kong** | yes | 381 | **tagged wrong — see below** |
| Australia | yes | — | home |

Nothing needed building. Four of the five were already captured and
correctly tagged; the deploy this morning is what made them usable.

## Hong Kong — captured, real, and mis-tagged

Happy Valley and Sha Tin, 381 races, **with genuine odds**: 84–153
runners a meeting and thousands of price snapshots from Ladbrokes, Neds
and TABtouch. This is not a shell class.

But every HK row carries `country = NULL` and `state = 'HK'` — the
country code is sitting in the state column. Cause is the same as the
Newmarket shells above: **0 of the 381 have a Betfair market id**, and
`race_matcher` is what stamps country. No Betfair match, no stamp.

Consequences, and they are small:
- The sidebar's country tag is gated on `country_code !== 'AU'`, so HK
  meetings would render **untagged**, looking like home racing.
- Phase 1's rekey left the keys bare (`happy valley`, `sha tin`). Harmless
  — neither has an Australian homonym.
- Odds still match, because the match key is the venue name.

**Not urgent: HK racing is out of season.** The season runs roughly
September to July; the last captured meeting was 15 July. There is
nothing live to get wrong before ~September.

Adding `HK` to the catalogue list may well populate the Betfair market
ids by itself, which would make `race_matcher` stamp the country and fix
this with no code at all. **Unproven, and unprovable until the season
resumes.**

## The bounded backfill, if it is ever wanted

Rows with `country IS NULL` and a country-bearing code sitting in
`state`:

| state | rows | resolves to |
|---|---|---|
| NZ / NZL | 1,040 | NZ |
| **HK** | **381** | **HK** |
| GBR | 99 | GB |
| JPN | 60 | JP |
| FRA | 53 | FR |
| IRL | 45 | IE |
| SAU | 44 | *deliberately unresolved (SA collides with South Australia)* |
| USA | 38 | US |
| KOR | 35 | KR |
| PAN | 31 | *not in the canon map* |
| SAF | 25 | ZA |

`canonical_country()` already maps every one of these. This is a
one-query backfill, not a project — but it is **not needed for the ask**,
so it stays parked.

## Explicitly NOT done

- Nothing was torn down on the VPS. The other eleven countries keep
  capturing. Turning capture off saves nothing (Australian books publish
  those meetings anyway) and the history has already paid for itself once
  — S267's Betfair import leaned on it.
- No TABtouch country-resolution work (the Newmarket/dogs class above).
  The census alarm for `newmarket` stays live and honest.

---

# S268 — CLOSE-OUT: Betfair-only is enough. Nothing left to build.

> "We don't need to capture data on the VPS though - just having BetFair
> odds in the tool is enough for now."

## Proven live in the running app, 6 Aug ~07:55 ACST

The operator had already restarted (app up 07:46:45, `live` mode,
`BETHUB_RACING_COUNTRIES=AU,GB,IE,US,HK` confirmed in the process env).

**Menu:** 110 markets on today's list — **38 AU, 50 GB, 22 US**.
Saratoga, Penn National, Presque Isle Downs, Louisiana Downs, Horseshoe
Indianapolis; Newmarket, Nottingham, Brighton, Dunstall Park, Sheffield.

**Betfair odds, end to end, on the overseas races:**
- Newmarket (GB) `1.260764296` — `fresh`, 7 runners, full three-deep back
  and lay ladder with sizes, last traded price.
- Louisiana Downs (US) `1.260759872` — `fresh`, `OPEN`, $3,739 traded,
  full ladder.
- Saratoga (US) `1.260757903` — `betfair_market_suspended`. **Normal**
  (race at the jump), not a defect; a second US market read fine.

**No country was dropped.** The F13 warning ("dropping country … from
today's race list") appears nowhere in the app log. All five catalogue
calls succeeded. Ireland returned zero because there is no Irish card in
today's Adelaide window; Hong Kong because the season ended 15 July.

## Therefore: the VPS work is OFF

- **No jurisdiction flip.** `jurisdiction_config` stays AU-only. GB and
  IE stay `enabled=0`; US and HK are not seeded and will not be.
- **No Gate B / Gate C sequence.** Both existed to make the *capture*
  side safe for GB. Not needed for a Betfair-only rail.
- **R-e does not arrive.** The overnight Betfair-freshness watchdog only
  arms once market-bearing GB rows exist overnight on the VPS. They will
  not. No louder first night.
- Gate B's three structural clauses were run anyway and all returned
  **0** — no non-AU row without its `|cc` qualifier, no venue key shared
  between AU and non-AU, no post-deploy international row missing
  `local_race_date`. The migration is sound; it is simply not being
  built on.

## The two things the operator lives with

1. **Empty soft-book columns on overseas races.** The bookmaker
   comparison is blank — Betfair only. The prices *are* being captured
   (Horseshoe Indianapolis 1,180 snapshots today, Saratoga 771, Penn
   National 458); they are just not linked to a Betfair market id,
   because linking is what the jurisdiction flip does. `soft-odds`
   returns `fresh` with an empty runner list, so nothing errors or
   blocks — the columns are simply empty.
2. **R-g — promo EV renders on overseas races using AUSTRALIAN
   calibration, with no warning marker.** This is the one that can cost
   money rather than just look bare. The indicator was validated on
   31,995 AU runners; nobody has checked it against a UK or US field.
   Named in the Phase 1 brief as operator-sequenced, deferred to Phase 3,
   still open.

## Backlog effect

- 0p international thoroughbreds — **descoped**, not cancelled. The
  capture half is what the operator does not want "for now".
- TABtouch country resolution (Newmarket shells, GB/US dogs and harness)
  — stays parked. The census alarm stays live and honest.
- The bounded `state`→`country` backfill (HK 381, NZ 1,040, GBR 99, …)
  — stays parked. Nothing reads it on a Betfair-only rail.
