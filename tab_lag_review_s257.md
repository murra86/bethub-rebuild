# TAB odds lag — full review (S257 v2, 28 Jul 2026)

> **AS BUILT (28 Jul afternoon, operator-confirmed "proceed"):** every
> measure below is BUILT, reviewed, DEPLOYED and live-proven. Two
> independent adversarial reviews + a revert-simulation verify pass ran
> over the changes; every confirmed finding was fixed (the biggest: an
> empty answer for a race TAB doesn't carry could silently disable the
> staleness marking — cured and regression-locked). Live proof against
> real racing (Swan Hill R3, 28 Jul): a fresh TAB price is now picked up
> every **3.5–3.7s** in the final window (was 8.3s Saturday), via two
> watcher sessions each politely at TAB's own ~7s rhythm; 22/22 screen
> reads served, zero failures. Expected on your screen: **~4–6s behind
> the app** in the final minutes, and the minute-plus moments are gone —
> the live feed now runs the whole time a race page is open. The one
> behavior change to know: "Fill odds from my bets" now keeps TAB
> updating the runners you did NOT bet. Nothing else you do changes.
> Detail: `sessions/SESSION_257.md`. The analysis below is the original
> review, kept for the record.

**Your report: the TAB column lags ~10s typically, but sometimes over a
minute. Both are real, and they have different causes.** The ~10s is the
live feed's designed pace. The minute-plus moments are almost certainly
NOT the live feed at all — they're the times the screen is quietly
showing the *slow background feed* instead, which only updates every
1¾–5 minutes. Fixing the average without fixing the switching would
leave the worst moments untouched, so the plan below treats consistency
as first-class.

All numbers measured from Saturday 25 Jul (4,792 screen reads, ~2,900
live TAB fetches, 1,062 real price changes). Nothing has been changed.

## Current state — what the screen is actually doing

The TAB column is fed by TWO feeds, switching silently:

**1. The live feed** (a dedicated watcher fetching TAB directly for the
race you have open). Saturday it was excellent and never faltered:
typically **4s** behind what TAB's feed offers, 99% of reads under 9s,
zero failures all day. Your ~10s-vs-the-app observation is this feed's
designed pace (details in the 28-Jul morning version of this note:
our 8.3s ask-rhythm + ~1s screen refresh + ~1.3s per fetch).

**2. The background feed** (the capture system's routine snapshots).
This is what the column shows whenever the live feed isn't running —
and it updates TAB odds only every **5 minutes** normally, every **~1¾
minutes** in the last 5 before the jump. Any moment you're on this feed,
"over a minute old" is normal and expected.

**When are you on the slow feed?** The live feed only runs while ALL of
these hold: the race page is open and visible, TAB is the selected
book, and the race is inside ~30 minutes of the jump (it correctly
keeps running through delayed jumps). So the minute-plus moments line
up with: looking at a race more than 30 min out, the first seconds
after opening/returning to a page, or any time the live feed quietly
drops out. The screen does show an age stamp, but outside the 30-min
window it doesn't mark TAB prices "stale" until they're **10 minutes**
old — so a 4-minute-old price looks current.

**3. A new trap shipped this morning (flagging before it bites):** the
"Fill odds from my bets" button marks EVERY runner on the card as
operator-owned — which permanently stops the feed from updating ANY
TAB price on that race, and also hides the staleness marker. One click
and the whole column is frozen until you change races. This wasn't
live on Saturday, but from the next sitting it would make lag look far
worse, at random — please treat this as part of the same problem.

**4. TAB's own publishing delay (background fact):** TAB's public feed
carries each price change ~30–40s after TAB's internal reprice stamp —
occasionally 90s+. Everyone reading the feed gets it that late,
almost certainly including the app (your ~10s comparison only adds up
if the app is on the same delayed feed). Nobody outside TAB can beat
this; it caps what any improvement can achieve.

## Proposed measures (ranked; nothing done yet)

**Consistency first — these kill the minute-plus moments:**

| # | Measure | What it buys | Cost / risk |
|---|---|---|---|
| 1 | **Live feed whenever the race page is open** — drop the 30-min gate (keep the gentler 15s rhythm far out, 7s near the jump) | The open race is never on the 5-minute feed; worst case goes from ~5 min to ~15s | Small change; traffic still tiny; same browser-like rhythm |
| 2 | **Fix the fill-odds freeze** — the button should own only the runners it actually fills (your bet runners), not the whole card; staleness marker stays visible | TAB prices keep flowing after you use the button | Small change to this morning's feature |
| 3 | **Honest staleness marking** — tighten the "stale" threshold on the background feed (e.g. 2 min, not 10) and keep the age stamp prominent | You always KNOW when a price is old, instead of discovering it | Trivial |

**Speed second — these sharpen the live feed itself:**

| # | Measure | What it buys | Cost / risk |
|---|---|---|---|
| 4 | Fix the ask-rhythm drift (8.3s → the designed 7s) | ~1s average | ~an hour; still matches TAB's own site rhythm |
| 5 | Screen reads our copy every 1s instead of 2s | ~0.5s average | Trivial |
| 6 | Second offset watcher session (the two take turns → fresh price picked up every ~4s) | ~2s average, worst case halved | Few hours + live check; TAB sees two normal-looking viewers; current Decodo plan covers it |

**Together:** typical lag vs the app roughly **10s → 4–6s**, and — the
bigger win — the over-a-minute moments disappear for the open race
except TAB's own publishing tail (which the app suffers equally).

**The Decodo answer is unchanged: a bigger subscription buys nothing.**
Our TAB traffic is megabytes against the plan; the lag lives in
publishing delay, ask-rhythm, and feed-switching — none of which a
bigger plan touches. Skip it.

**Not proposed:** polling one session faster than TAB's own site (~7s)
— account/IP-flagging risk (21-Jul lesson) for at most ~2s, and
measure 6 gets the same result while still looking like normal
browsers. Also not proposed: speeding up the whole capture system's
snapshot rhythm — measure 1 makes that unnecessary for the race you're
watching, and it would spend fingerprint budget across every book.

## Confidence

- **High**: the live feed's measurements, the background feed's
  cadences, the feed-switching conditions, and the fill-odds freeze
  (all read directly from code and Saturday's logs).
- **Medium**: that your minute-plus sightings were background-feed
  moments — it's the only mechanism found that produces them, and
  Saturday's live feed provably never stalled; but I can't replay what
  your eyes saw. If you can note the next minute-plus sighting (race +
  rough time + how far from the jump), one log pull will confirm it.
- **Medium**: the app rides the same delayed TAB feed (reasoned above).

## Next steps — your call

1. Confirm the consistency set (1–3) — biggest real-world change,
   modest work. Item 2 needs your view on how fill-odds should behave.
2. Confirm the speed set (4–6) — 4+5 are quick; 6 fits the Saturday
   sitting with a live side-by-side check against the app.
3. Skip the Decodo upgrade.

*Evidence: `bethub-analytical/race-price-pressure/cycle3_tab_leadlag/code/s257_lag_review/`
(analysis scripts); VPS `tab_live_log.db` + API journal (25 Jul);
`Racing.tsx` merge/gating, `live_soft_odds.py` refresher, capture
`config/settings.py` cadences. Morning v1 of this note is superseded by
this version.*
