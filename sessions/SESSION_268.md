# SESSION 268 — Thursday 6 August 2026

Opened ~07:05 ACST, closed ~15:10. Working branch `s267-race-row`, which
is now identical to `main` and to GitHub.

---

## 1. Standing checks

VPS all clear (disk 45%, collector up, backups 2h, overnight sweep ran).
RACING ALERT mail: one live failure — country stamping — see §3.

## 2. Phase 1 international — LANDED

The 04:40 deploy fired at 19:10 UTC 5 Aug and **succeeded**: 11,751 rows
rekeyed across 15 countries (GB 2,468, US 2,316, TR 1,769, JP 1,220,
NZ 1,146 …), 23 merged, **0 refused, 0 collisions**. The 342 mis-stamped
rows that blocked S266 were gone.

Gate B's three structural clauses were run and all returned **0**: no
non-AU row without its `|cc` qualifier, no venue key shared between AU and
non-AU, no post-deploy international row missing `local_race_date`.

## 3. The country-stamping alarm — two problems, one message

Firing every 45 minutes since the migration.

**Sandown — the alarm was WRONG. Fixed (`efcde0d`).** The AU greyhound and
harness feeds supply `country='AU'` with a **blank state**, and the F4
census only excused a bare row carrying an Australian *state*. So Sandown's
dogs read as "bare" beside `sandown|gb`. The clause had its intent written
in its own comment ("teaches the operator to ignore the one tripwire that
can see an F1 escape") and was one condition short of it. Detection is
unchanged and was checked, not assumed: the flap case lands `country=NULL`,
not `'AU'`, and a foreign state code still counts. Suite 624 green,
confirmed live at 21:45 UTC.

**Newmarket — the alarm was RIGHT. Left ringing.** Six empty shells:
0 runners, 0 odds, `capture_status=PENDING`, identified by
`tabtouch_race_id = 2026-08-06/orb/1`. Verbatim the case the census comment
describes. The class is large — TABtouch carries international greyhound
and harness coverage and tags **none** of it with a country (Northfield,
Hoosier, Yonkers; Monmore, Sheffield, Romford, Sunderland, Harlow). A
venue-name lookup cannot fix it: `ascot` is Perth *and* Britain. Parked
under the scope cut below. Detail in `s268_country_stamp_residue.md`.

## 4. OPERATOR SCOPE CUT — international, twice

> "We don't need international racing on the VPS, just USA, Hong Kong, and
> UK/Ireland races to show in the racing menu of the tool."
> "We don't need to capture data on the VPS though - just having BetFair
> odds in the tool is enough for now."

The menu is **Betfair-catalogue-driven**, not capture-driven — so this was
one config line, not a capture project. `BetHub.command:322` →
`AU,GB,IE,US,HK` (`403e6c5`). AU stays first (F13: only the home country's
call is load-bearing).

**Proven live** in the running app: 110 markets (38 AU / 50 GB / 22 US),
full three-deep ladders on Newmarket and Louisiana Downs; one Saratoga
market suspended, which is a race at the jump, not a fault. **No country
dropped** — the F13 warning appears nowhere in the log. Ireland returned
nothing (no Irish card in the window); Hong Kong is out of season to ~Sept.

**Consequently OFF:** the jurisdiction flip (`jurisdiction_config` stays
AU-only, GB/IE `enabled=0`, US/HK never seeded), the Gate B → Gate C
sequence, and R-e's louder first night.

**Lived with:** soft-book columns stay blank on overseas races (the prices
ARE captured — Horseshoe Indianapolis 1,180 snapshots — just not linked to
a Betfair market, because linking is what the flip does); and **R-g**, EV
on overseas races running Australian calibration.

**Hong Kong is captured and mis-tagged** — Happy Valley + Sha Tin, 381
races with real odds, `country=NULL` and `state='HK'`, because 0 of 381
carry a Betfair market id and `race_matcher` is what stamps country.
Cosmetic on a Betfair-only rail. Bounded backfill sized and parked.

## 5. Frontend — two ships

**Stale-price warning fired 2.1s late (`7c294e6`).** S250 exists so a dead
live refresh near the jump cannot present as current. 0y later gave that
query `retry: 3, retryDelay: 700`, and the note was wired to `isError` —
which only turns true once the burst exhausts. For those two seconds, near
a jump, stale prices read as live. Now `failureCount > 0`: the note is up
on the first failure, the retries still run, and react-query zeroes the
count on success. **The red `Racing.softstale` test had been reporting this
all along** — it failed on `main` too, and the previous commit there had
tried to accommodate the delay in the test rather than remove it. **613/613
— the first fully green frontend run.** Verified by reverting.

**Overseas EV marker (`d54f03b`).** R-g brought forward: a banner naming
the country, in the same slot and voice as the small-field warning. An
absent country stays silent — a null reads as home racing everywhere else,
and a banner on every AU card is noise.

## 6. Two adversarial sub-agent reviews — both NO-GO, both dropped

**`s267-place-only`** — the review found it a **no-op for its stated
purpose**: `Results.tsx` gates every placings surface on
`position !== null`, and the Betfair place market yields the SET with no
order. Also: the restart step was a once-daily 04:25–06:05 recycle that
exits 0 mid-day having done nothing; no guard against over-marking places
when scratchings shrink a field, uncorrectable for the 79% of races the
subscription never reaches; and the acceptance test could not distinguish
the branch from `racing-intraday-results.timer`, which **already delivers
places on the day with positions**.

**0m** — two of the prior review's five blockers genuinely closed
(`--reverse`, `--report`; s3-only is 11 of 369 and the s3 objection is
empirically dead). But **`betfair_historical` is a permanent-damage trap**:
582 BSP rows point at the 369 loser races, and `INSERT OR IGNORE` against
`UNIQUE(bf_win_market_id, bf_selection_id)` means no future import can ever
correct the attachment. And **the s1 class (118 of 369) is near-worthless**
— 103 of 118 have overlapping envelopes, median 94%. Safe version: 8–10h
for **240** markets.

Operator dropped both. See `plan_s268_places_and_0m.md` and the memory
note. **Stage A is dead work too** — D1 v2's population report for a
question D1 v3 closed in S267.

## 7. Recording what actually happened — two gaps closed

**16 systemd units into git (`b9004a5`).** Chasing the intraday timer
turned up the real gap: the repo tracked **12** unit files while the box
ran **28**, missing `racing-capture.service` and `racing-api.service`
themselves. Captured verbatim off the live box; credential-scanned first.

**`bets.persistence_type` (`6d63702`).** The Take-SP setting was chosen on
the lay route, handed to Betfair, and dropped — so S267 could not
corroborate the operator's report, for every lay ever placed. Two tests:
one that it round-trips, one that a LAPSE lay stores LAPSE.

**Free-bet realised conversion (`f83bfa1`).** Derived on read; the dormant
column and the S260 D1 fence untouched. **The numerator is the free bet
plus the lay ON ITS OWN SELECTION** — a first cut summed the cycle and was
wrong, because 84 of 92 free-bet cycles also hold a qualifying cash back on
a different horse (cycle `58a6f299`: $50 @ 3.5 on "6. Clear Proof", then a
lay and a $32 free bet both on "14. Purr Sefanee" @ 21.0, one second
apart). Live median went from **−0.26 to +0.71**. Measured across all 93:
**hedged 0.7004, blended 0.6853** — the operator predicted "around 70%"
without seeing any of it. **65% stays: deliberate conservatism, do not
re-raise.**

## 8. Betfair scheduled outage — 13:30–17:00 ACST

Emailed maintenance, all channels globally. Session expired 13:43; **one**
failed auto-login armed the F9 cool-off (30m → 1h → 2h → 4h → self-disable
at 5). **Any login error counts equally — a network blip is
indistinguishable from a bad password, and the reason is never logged.**
Confirmed by a controlled login test outside the provider: HTTP **503**
from `identitysso.betfair.com`, Cloudflare, `retry-after: 1800`, while
betfair.com and the exchange API answered normally.

**Cost:** the afternoon's live proofs — Take-SP first fill, SP-pool near a
jump, first settle-up to the cent, first auto-banked bonus win. **All move
to Saturday.**

## 9. Built during the outage — `scripts/promo_insurance_ev.py` (`07714a1`)

An AllBets stake-back-if-2nd-or-3rd promo ran over seven races with the
exchange down. Tool reads the captured bookmaker board instead:

- **TOP-3 chance straight off the books' fixed PLACE odds**, not derived
  from win odds. Harville understated it enough to change answers (Moree R5
  best runner: −3.7% derived vs −1.2% off the place board).
- Favourite-longshot bias corrected by power normalisation.
- The book being bet into never informs the fair price.

**What the afternoon taught:**
1. **The edge is the PRICE, not the horse.** Six of seven races had nothing
   positive. Moree R5 turned +5.2% the moment AllBets moved one runner
   6.50 → 7.00 while eight books held.
2. **Short favourites in small fields are the best insurance bets** — Ahab
   at 2.70 (33% win / 38% place) came out **+14.0%**, double the card,
   because he only loses outright 29% of the time. Every longshot ran −30%
   to −50%.
3. **Field size drives it** — 13 runners can't clear a ~24% margin against
   a ~15% benefit. Scratchings improve the promo until they void it;
   Gosford R7 went 12 → 7 and stopped qualifying silently.

**Operator UX lesson, and it cost a bet.** A table sorted by EV put the
pick on the top line where the book puts runner 1; the operator backed
Deebo (−2.2%) instead of Big Short (+5.2%). **Always runner order, mark the
pick, never move it.** Now enforced in the script and documented in it.

Operator stood down for the day; focus moves to Saturday.

---

## HANDOFF — S269

1. **Do not open BetHub before 17:00 ACST 6 Aug.** The cool-off is armed at
   1 failure; opening during the outage escalates to 1h, then 2h, then 4h.
   After 17:00, open **once**.
2. **Saturday's live proofs**: Take-SP first fill (now checkable —
   `persistence_type` records it), SP-pool on a near-jump snapshot, first
   settle-up batch to the cent, first auto-banked bonus win.
3. **Known limit, carry into any Betfair-history analysis**: 582 settled
   BSP rows sit on the wrong race inside the S267 import.
4. Newmarket census alarm stays live and honest until TABtouch country
   resolution is wanted — parked, not forgotten.
5. Deploy-scheduler fix or retirement still open.
6. **The login failure reason is not logged anywhere.** Third instance
   today of "the tool did something and did not write down what happened".
   Small, and it would have answered the outage in one line.
