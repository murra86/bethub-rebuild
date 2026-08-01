# Forecasting promo EV at jump — investigation (S252, 23 Jul 2026)

Commissioned: park the price research, priority is maximising promo EV.
Question: in the promo bar of the race page, how do we best forecast the EV
for each promo type — and does liquidity affect the price read?

Read-only throughout. No code changed.

## 1. What actually drives EV, per promo type

The EV engine is entirely in the browser (`ui/web/src/ev/evEngine.ts`); the
backend computes nothing, it only stores what the screen worked out.

| Promo type | EV formula in one line | The bit that needs forecasting |
|---|---|---|
| **Insurance** (your main type) | raw EV **+ chance it runs 2nd/3rd × bonus × 0.65** | the trigger chance |
| **Bonus winnings** | as if the odds were higher: `odds + bonus per dollar × 0.65` | the win chance and the cap |
| **Boosted odds / multiplier** | just win chance × the boosted price | nothing — the price is handed to you |
| **Free bet** | pure lay-hedge arithmetic, no probability at all | nothing — it's the lay price |
| **each-way cashback / other** | **no EV behaviour exists** | — |

So there is exactly **one forecastable quantity that matters for insurance:
the chance the runner finishes 2nd (or 2nd/3rd)**. Everything else is either
a price you are given or a fixed conversion rate.

That trigger chance comes from a corrected Harville place model over
de-vigged Betfair prices, with exponents 0.77 (2nd) and 0.62 (3rd).

## 2. Is that trigger chance actually right? — tested against real results

> **CORRECTED 23 Jul after adversarial review.** The finding is real but the
> numbers below were wrong by ~50%: my script hit the very duplicate-race
> problem described in §8 — its tie-break picked the copy of each race that
> holds prices but *not* results, silently discarding 833 recoverable races.

Replayed the tool's exact calculation and scored it against recorded
finishing positions — **2,683 races / 26,131 runners** after merging the
duplicate race records properly (originally 1,172 races).

| Trigger chance the tool shows | What actually happened | EV overstated by (per $50) |
|---|---|---|
| 0–5% | 3.47% → **2.14%** | **+$0.43** (originally reported +$0.65) |
| 5–10% | 7.5% → 7.4% | +$0.05 |
| 10–15% | 12.5% → 12.5% | +$0.01 |
| 15–20% | 17.5% → 18.0% | −$0.16 |
| 20–30% | 24.8% → 25.0% | −$0.06 (originally reported −$0.39) |
| 30%+ | 36.3% → 36.0% | +$0.11 |

**The place model is sound in the range you bet in.** Every band from 5% to
30% sits within 16c per $50. Stated honestly the sample can only resolve
about ±30c, so the defensible claim is *no detected bias above ~30c per $50
between 5% and 30%* — not "accurate to within a few cents", which claimed
more precision than the data supports.

**One real flaw: outsiders.** For runners the tool gives under a 5% trigger
chance, the true rate is **1.6× lower** than it says (not "less than half"),
overstating EV by about **43c per $50** (range 23c–63c). This was the *only*
band to survive multiple-comparisons correction (adjusted p = 0.0015), and it
holds across every liquidity band and binning choice. It is mechanically
clean: the underlying win probabilities are well calibrated even in the tail,
so the error is created by the place model itself. Published work supports
the direction — the model's exponents exist to correct a known bias, and at
the extreme tail they **over-correct**.

The −$0.39 gap previously reported in the 20–30% band was an artefact of the
same duplicate-race bug plus noise. It vanishes on corrected data and does
not survive multiple-comparisons correction.

## 3. Your liquidity question — tested, and the answer is no

Reasonable expectation: thin markets give a worse read of a runner's real
chance. Measured band-by-band on the trigger probability, at T-10m:

| Market liquidity | median matched | average error in the trigger chance |
|---|---|---|
| thin | $1,569 | **0.88 pts** |
| mid | $3,558 | 0.99 pts |
| deep | $9,996 | 1.17 pts |

> **CORRECTED 23 Jul after adversarial review — the conclusion below FAILED,
> and the operator's instinct was right.** The three numbers replicate
> exactly, but they cannot carry the inference. See §3b.

~~**Liquidity does not degrade it — if anything the deep markets are
marginally worse.** So no liquidity-based haircut on EV is justified by the
data.~~

## 3b. Why that failed, and what is true instead

Three independent problems with the test above:

1. **The metric has no power.** Simulating outcomes from the model's own
   probabilities — so the price is *perfect by construction* — still scores
   1.12 points on this metric. The observed spread (0.88–1.17) sits entirely
   inside the noise floor. Race-clustered bootstrap on deep-minus-thin:
   +0.26 pts, 95% CI [−0.94, +1.50]. It is a coin flip.
2. **The sample contained no thin markets.** Only races with backfilled
   results survive (1,172 of 16,549 markets), and those are systematically
   liquid — kept markets median $3,419 matched vs $730 for dropped. The
   "thin" band's median of $1,569 sits near the **60th percentile** of the
   real market universe. The claim was never tested where it matters.
3. **Field size and meeting class are confounded with liquidity** (thin =
   78% country, 9.9 runners; deep = 38% metro, 11.3 runners). Standardising
   for field size both inflates the errors (2.4 / 2.0 / 2.9 pts) and
   scrambles the ordering.

**What IS defensible on calibration** — from a properly powered test the
review ran on the broad dataset (52,101 runners, 4,340 races, including
genuinely illiquid markets down to $14 matched): there is **no detectable
relationship between liquidity and how well the Betfair price reads a
runner's WIN chance**. The liquidity interaction is −0.001 (SE 0.017) after
controlling for field size, and calibration error is flat across all ten
liquidity deciles. That is a real null, and better evidence than the original
test produced. It has **not** been established for the 2nd/3rd trigger
probability — the data to answer that doesn't exist yet.

**Where liquidity genuinely costs money — and this is the operator's point,
vindicated:** not calibration, but **execution**. Free-bet conversion lays on
Betfair, and you pay the lay side, not the midpoint:

| Market liquidity | median spread | lay price above mid | unusable price (lay > 2× back) | depth at best lay |
|---|---|---|---|---|
| thin | 5 ticks | **8.47%** | 8.3% | ~4× less |
| mid | 3 ticks | 4.88% | 2.3% | — |
| deep | 2 ticks | **3.59%** | 1.7% | — |

**Laying in a thin market costs roughly 2.4× more in slippage and is ~4.8×
more likely to hit an unusable price.** A calibration test can never see
this, so "no calibration effect" never licensed "no liquidity haircut". The
right adjustment is a slippage/fill term keyed on **spread in ticks and
available lay size** — not on cumulative matched volume.

Published work does not settle it either way, and one directly on-point study
([Tetlock 2008](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=929916))
finds liquidity can *worsen* prediction-market accuracy — a live warning
against assuming the relationship runs the obvious way.

**Still correct as built:** the two places liquidity is already handled — the
stale-price rejection (`evEngine.ts:195`) and the Race Watcher trust gate
capping the Call grade rather than shaving EV. Note the rejection fires **4.8×
more often in thin markets**, which silently switches the price estimator, so
thin and deep are not even scored by the same instrument.

## 4. Are the place-model settings right?

**Answer unchanged — leave them alone — but every number I originally gave in
support was invalid.** The measure I used to compare settings is one that a
deliberately useless model (predicting the same chance for every runner)
scores 19× better on, and the 0.664-vs-0.661 difference sits well inside
noise (59% of resamples say the tool's own setting is better).

Re-tested properly with a sound scoring measure on the corrected, larger
sample: the tool's settings are within 0.00002 of the best available, with a
confidence range spanning zero. The 2nd-place setting (0.77) matches the
published value (0.76) from the original literature.

So: **don't recalibrate — but because the surface is flat, not because the
current values are a located optimum.** One important qualifier: no setting
in this family fixes the outsider flaw in §2 — the gap is identical at the
tool's values and at the grid's best. That needs a different kind of fix (a
floor or shrinkage on very long shots), not a tuned exponent. The 3rd-place
setting (0.62) is more aggressive than anything published (0.65–0.80 is
typical), and the outsider overstatement grows as it falls — so it is the
suspect parameter if this is ever revisited.

## 5. ~~The one change that would genuinely improve the jump forecast~~ **[UNSAFE — DO NOT ACT ON THIS SECTION]**

> **CORRECTED 23 Jul after adversarial review.** The recommendation below —
> drop the `sp_near` substitution — is **unsafe** and must not be
> implemented. "Project off the live book" is the *identity*: current EV is
> already computed from the book mid, so removing the substitution makes
> projected EV equal current EV, deletes the `LEAVE` grade, and turns the
> project's own documented trap case from LEAVE into STRONG. Two reviewers
> established this independently, one by running the real fixture.
>
> **Replacement:** keep the substitution and shrink the input —
> `mid × (sp_near/mid)^β`, β ≈ 0.10 far out to ≈ 0.18 near the jump — which
> beats both the raw mid and raw sp_near at every horizon. Keep the
> direction gates (`isFirming`, `trendContradictsClose`) untouched.
> Full detail: `sp_bench_report.md` §9.

### Original text (superseded)

The Race Watcher builds its *projected* EV by substituting Betfair's
projected SP (`sp_near`) for the back price whenever the race is more than
2 minutes out (`raceWatcher.ts:318-321`).

This session's benchmark measured `sp_near` against 613,139 real decision
points: **it is worse than simply reading the current book at every single
horizon**, in every liquidity band, and recalibrating it does not help.

So the projected-EV path is currently built on the weakest available input.
**Recommendation: drop the `sp_near` substitution and project off the live
book.** That is a small, well-evidenced change to the number that most
directly answers "what will the EV be at jump".

Supporting fact for the same decision: the trigger probability is stable
across time — its calibration at T-30m, T-10m and T-3m is effectively
identical. The forecast does not decay as you move earlier, so an early EV
read is trustworthy *as a trigger estimate*; what moves is the price.

## 6. Gaps blocking "rank runners by promo EV"

Found while mapping the promo bar and catalogue:

1. **The promo bar shows no EV at all.** It renders shape labels only
   (`2nd/3rd → Bonus $50`). EV appears only after you arm a promo, in the
   odds-table columns. To rank runners across *all listed promos* the EV
   would have to be computed for every catalogue promo × every runner —
   that is the actual build, and it is cheap because EV is already
   client-side.
2. ~~**Bonus-winnings EV reads the wrong knob.**~~ **[DOWNGRADED — see §9]**
   The `bonus_pct`/`return_pct` alias is correct by design (it keeps screen
   EV and the credit engine on the same number). The `?? 100` fallback is
   real but **unreachable today** — every live bonus-winnings row has
   `return_pct = 0.25`. Fixing it is hygiene, not an EV correction, and it
   must touch **four** sites, not the two cited (`OddsTable.tsx:308` and
   `Racing.tsx:451` were missed, and they feed the *stamped* record).
3. **Your haircut rules do not exist in the code.** The "$6–$10 screen EVs
   are soft by ~3 points" and "flagged EVs are never firm" rules live only
   in your head — there is no discount applied anywhere. The nearest thing
   is a colour band (green at 5%+).
4. **No minimum-odds term** exists in the promo schema, and `cap` is
   overloaded (max stake for insurance, max credit for bonus winnings).
5. **Boosted odds only works if you type the boosted price** into the soft
   odds box — the engine has no separate boosted-price field.

## 7a. SCOPE LOCK (operator, 23 Jul)

**In scope:** highlighting high promo-EV runners on the race page. Promo bets
only. **Free bets are out of scope** — the laying/conversion workflow is a
separate thread and no work here depends on it.

One consequence worth stating plainly: the adversarial review's execution
finding (thin markets cost ~2.4× more in lay-side slippage) applies **only to
laying free bets**. Promo bets are never laid, so **that finding does not bear
on this build at all**. There is no liquidity adjustment to make here. The
only thing liquidity affects is how well the Betfair price reads a runner's
chance — and that was tested across genuinely thin markets and found clean.

The bonus conversion rate still matters, but as a *valuation* input, not as
workflow: an insurance promo refunds a bonus, and the EV has to say what that
bonus is worth. That is why the 0.65 figure is still on the fix list.

## 7. Recommended order of work **[REPLACED after adversarial review — see §9]**

The original order put a no-op first and an unsafe feature-deletion second.
Revised, ordered by real money impact:

**Live EV-honesty defects — fix before any ranking is built on the numbers:**

1. **Populate the field-size clause (`position_min_field`) on the two `[2,3]`
   insurance rows.** The capability shipped; the data was never entered. Your
   own standing lesson says BetRight excludes 3rd at ≤7 runners. Every 2+3
   insurance EV on a small field at such a book is overstated by roughly
   **8.5 points of stake** (~$4.23 on a $50 promo). This is the largest live
   EV error found, and it is a data-entry fix.
2. **Stop the promo-creation door defaulting the bonus percentage to 100**
   (`TopBar.tsx:898/938`). This has already written a wrong catalogue row
   once in production — the S244 correction note records it — and a wrong row
   poisons the credit engine, not just the screen.
3. **Raise the free-bet conversion rate off 0.65.** Your own measurements are
   68.9% (S246) and 77.4% (S234); 0.65 corresponds to converting at ~$3.60,
   below every practitioner benchmark. It systematically *understates*
   insurance EV by ~3 points, which is larger than the MOD margin — you are
   declining playable bets. Set it to the conservative 0.70 now; replace it
   with a function of the conversion odds later.

**Then, and only then, the ranking build:**

4. Build the strip as a **shortlist, not a winner** — every runner within ~2
   points of the top, ranked in **dollars not EV%**, with a hard interlock
   against pointing two books at the same runner in the same race, and
   per-book weekly promo budget visible. A single "best runner" ranking
   returns the favourite almost deterministically, which is both uninformative
   and the exact pattern that gets accounts restricted.

**Do not do:**

- ~~Drop the `sp_near` substitution~~ — unsafe, see §5 and §9.
- ~~Add a blanket "distrust outsiders" rule~~ — a no-op for 2nd/3rd insurance
  (the engine already rejects them) and actively wrong for loss-triggered and
  uncapped bonus-winnings promos, where the outsider is the correct pick.
- ~~Recalibrate the Harville exponents~~ — no measurable gain (pending the
  statistical review's verdict).

## 8. Data-quality finding (separate, needs a decision)

While extracting, found that **63% of Betfair markets since April are
attached to two different capture race rows** (6,790 of 10,771). The pattern
is always the same: one correctly-matched row, plus a second row dated one
day earlier with a truncated venue name and low match confidence
(`Pinjarra` vs `Pinjarra Park`, `Albion` vs `Albion Park`), created from
Betfair alone before the bookmaker data arrived.

**Both rows collect Betfair snapshots** (5,722 of 6,735 pairs), so the
capture is doing the work twice. This also looks related to the recurring
Pinjarra "no Betfair identity" RACING ALERTs — same venues, same
name-variant cause.

**Resolved — the app already handles this, so it is NOT a betting-day risk.**
`clients/vps_client/v1/_lookup_api.py:250-292` groups race rows by Betfair
market id, treats them explicitly as "fragments"/"twins" of one physical race
("Same market id ⇒ same physical race"), keeps the most complete fragment and
coalesces racing code and match confidence across the twins. So the duplicates
are collapsed before they ever reach the race list or the picker.

What remains is smaller but still real:
- **Capture does the work twice.** Both rows collect Betfair snapshots, so
  polling, storage and API calls are roughly doubled on affected races.
- **It is a trap for analysis.** Anything reading the capture database
  directly — as this session did — double-counts unless it dedupes by market
  id. That is exactly what produced an impossible intermediate result here
  (win rates above the de-vigged probabilities) before it was caught.
- The date on the low-confidence row is a day early relative to the real
  start time (it looks like a UTC-vs-local date assignment), which is likely
  the same root cause as the recurring Pinjarra "no Betfair identity" alerts.

Recommendation: fix at source when convenient (capture-side date assignment
and venue-name variants), not urgently. No action needed before race day.
