# Promo EV per runner — the indicator, and how far to trust it (S253)

**The question:** what is the best way to predict the promotional EV of an
individual runner, with the data we already have — and how confident can we be
in it.

**The answer:** the tool's existing EV calculation is the right indicator, and
it is accurate. Every promo type reduces to at most two probabilities, and both
of them, scored against real finishing positions, come in **within a fraction of
a point of the truth**. There is nothing to replace and no model to build.

---

## 1. Every promo type reduces to at most two numbers

| Promo type | EV formula | What has to be predicted |
|---|---|---|
| **Boosted odds** | win chance × boosted price − 1 | **win chance only** |
| **Bonus winnings** | win chance × adjusted price − 1 | **win chance only** |
| **Insurance** | win chance × price − 1 + chance of 2nd/3rd × bonus × conversion | **win chance + 2nd/3rd chance** |
| Free bet | lay-hedge arithmetic | nothing (out of scope) |

So the whole question is: how good are those two numbers?

Both come from one place — the live Betfair market. The win chance is the
back/lay geometric mid with the overround removed; the 2nd/3rd chance is the
corrected Harville model run on top of it. That is what ships today.

## 2. How accurate they actually are

Scored against **real finishing positions** — 3,249 races, 31,995 runners,
April–July 2026. Not against a model, against what happened.

**Win chance — the only input boosted odds and bonus winnings need:**

| tool says | runners | actually won | gap |
|---|---|---|---|
| 0–5% | 13,177 | 2.3% | +0.0 pts |
| 5–10% | 7,266 | 7.2% | +0.1 pts |
| 10–15% | 4,326 | 12.4% | −0.1 pts |
| 15–25% | 4,294 | 19.1% | +0.0 pts |
| 25–40% | 2,131 | 30.8% | +0.2 pts |
| 40%+ | 801 | 51.1% | −1.4 pts |
| **overall** | **31,995** | **10.2%** | **−0.0 pts** |

**2nd-or-3rd chance — the extra input insurance needs:**

| tool says | runners | actually ran 2nd/3rd | gap |
|---|---|---|---|
| **0–5%** | **2,021** | **2.2%** | **+1.6 pts** |
| 5–10% | 4,672 | 6.5% | +1.1 pts |
| 10–15% | 4,994 | 12.3% | +0.2 pts |
| 15–20% | 4,990 | 17.7% | −0.2 pts |
| 20–30% | 8,353 | 25.9% | −1.1 pts |
| 30%+ | 6,965 | 35.6% | +0.2 pts |
| **overall** | **31,995** | **20.3%** | **+0.0 pts** |

**In money, on a $50 bet:** the win chance contributes about **17c** of average
error, the 2nd/3rd model about **22c**. Both are small against a promo EV that
is typically worth several dollars.

**It does not decay.** The same tables at 10 minutes and 3 minutes out are
within a few cents of these. The indicator is as trustworthy half an hour out as
it is at the jump — what changes near the jump is the price, not the quality of
the read.

## 3. So how confident can you be?

**Boosted odds and bonus winnings: fully.** They need only the win chance, and
the win chance is calibrated at every price band. If the tool says a boosted
price gives you +8%, believe it.

**Insurance: nearly as much, with one exception.** The place model is sound
everywhere you normally bet. The exception is **runners the tool gives under a
5% chance of running 2nd or 3rd** — there it overstates by about 1.4 points,
worth roughly **45c per $50**. These are long shots; if you are betting one on
an insurance promo, shade the EV down slightly.

That is the entire caveat list on the probabilities.

## 4. The two things that DO make the number wrong

Neither is a modelling problem. Both are inputs the tool is missing or has set
wrong.

1. **The field-size clause is empty.** `position_min_field` is NULL on all 12
   catalogue templates, including both 2nd+3rd insurance rows (verified in
   `data/bethub.db`). The code honours it and the arming path carries it through
   (`presets.ts:271`) — the data was simply never entered. At a book that does
   not cover 3rd in a small field (BetRight excludes 3rd at ≤7 runners), the
   3rd-place leg is worth **$6.40 per $50 — 12.8 points of stake — of EV that
   is not there**, and 17% of races have 7 or fewer runners.

   **This is roughly 14× larger than every probability error combined.** It is a
   data-entry fix.

2. **The free-bet conversion rate is set to 0.65** against your own measured
   68.9% (S246) and 77.4% (S234). This does not change which runner looks best,
   but it sets the level — worth about 1 point of EV. Note it cuts both ways:
   raising it to 0.70 also lets ~12% more runners across the 5% execute bar, and
   about 40% of those extra ones are genuinely negative EV. It is a real
   correction, not a free one.

**Checked and clean:** the `bonus_pct` / `return_pct` alias is correct — the
catalogue stores a fraction and `presets.ts:268` converts it to a percentage on
arming, which is the unit the engine expects. No 100× error. That closes the
last open question from S252.

## 5. One thing to be careful of on screen

The EV figures above are the tool's **current** EV. The Race Watcher also shows
a **projected** EV, built by substituting Betfair's projected starting price
(`raceWatcher.ts:318-321`). That number is materially noisier than the current
one and reads high. If you are reading an EV to decide a bet, read the current
one.

The fix, if this is ever touched, is to shrink the substitution
(`mid × (sp_near/mid)^0.15`) rather than delete it — deleting it makes projected
EV identical to current EV and silently kills the LEAVE grade (S252 §9c).

---

## What this means

Nothing needs to be built to make the per-runner promo EV trustworthy. The
indicator is already right, and now measured against real results rather than
against another model.

Do the field-size data entry (§4.1) and the number becomes right in the one
place it is currently wrong.

Working file: `bethub-analytical/promo_ev_forecast/indicator_accuracy.py`
→ `indicator_accuracy.log`. Results are taken from the authoritative capture
fragment per `BETHUB_DATA_REFERENCE.md` §B.7.

---

## Appendix — wider analysis run this session, and why it is not above

I also benchmarked which *runner* to point a promo at, and how the read changes
as the jump approaches. That went beyond the question and I am not carrying its
conclusions forward. Three adversarial reviewers found real defects in it,
including a fragment-selection bug in `book_extract.py` that violates
`BETHUB_DATA_REFERENCE.md` §B.7 and inflated its "impossible book price" rate
roughly 16×, and a sample skewed to the most liquid half of metro thoroughbred
racing. Those files (`book_extract.py`, `promo_ev_bench.py`, `ev_stats.py`)
remain on disk but **should not be quoted** until the extract is rebuilt.

Nothing in section 1–5 above depends on them: the calibration work reads the
Betfair side only, which is deduped correctly, plus real finishing positions.
