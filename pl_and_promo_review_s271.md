# P&L and promo review — S271, Saturday 8 August 2026

Read-only. Every money figure is computed through the app's own
derivations (`bet_net_pnl`, `bet_is_settled`,
`free_bet_realised_conversion_rate`, `headline_book_corrections_total`)
rather than a second formula — the codebase explicitly warns that a
second money derivation becomes a second answer. Scripts:
`scratchpad/s271_figures.py`, `s271_ev_calibration.py`, `s271_verify.py`.

Store snapshot taken 8 Aug ~15:50 ACST, with one bet still pending.

---

## 1. The headline

| | Today (8 Aug) | All time |
|---|---|---|
| Bets settled | 144 | 711 |
| Won / Lost / Void | 49 / 94 / 1 | 245 / 461 / 5 |
| Still pending | 1 | 1 |
| Turnover (matched) | $6,686.52 | $30,775.61 |
| P&L from bets | +$728.62 | +$3,562.15 |
| Promo cash banked | +$16.25 | +$166.13 |
| Book corrections | $0.00 | −$0.01 |
| **P&L all-in** | **+$744.87** | **+$3,728.27** |
| Return on turnover | 11.14% | 12.11% |

Today put through **21.7% of all turnover to date** and produced
**20.0% of all profit** — a big day at very close to the standing rate,
not an outlier in either direction.

**The one pending bet** is `bet-9e977c10`, $50 @ $1.90, Leigh @ TAB.
⚠️ It is recorded as **"AFL: Sydney vs. Port — Port +48.5"**, not
+40.5 as described in conversation. Worth an eyeball: if the line is
wrong the record is wrong, and this is the bet whose account was moved
today. At $1.90 it settles to **+$45.00** or **−$50.00**.

---

## 2. Where the money actually comes from

All settled bets, to date:

| Component | n | Staked / face | Net P&L |
|---|---|---|---|
| Cash backs (the qualifiers) | 467 | $21,156.25 | **−$242.75** |
| Free bets | 123 | $5,477.50 | **+$6,832.00** |
| Lays (the hedges) | 121 | $4,141.86 | **−$3,027.10** |
| | | | **+$3,562.15** |

This is the single most important table in the review.

**The qualifying bets are not the business — they are the entry fee.**
$21,156 of cash turnover produced −$243, i.e. almost exactly break-even
(−1.1%). That is the machine working as designed: the qualifier is
bought at roughly fair value to unlock the promo.

**The free bets are the entire profit.** $6,832 gross, less $3,027 of
hedging cost, nets **+$3,805**. Against −$243 on qualifiers, that is the
whole +$3,562.

Practical consequence: **profit scales with the number of promos
harvested, not with turnover or with picking winners.** Anything that
increases promos worked per day is worth more than anything that
improves selection.

---

## 2b. By race type

Racing code joined from the capture database (`races.racing_code`) on
each bet's Betfair market id. Scored per complete cycle.

| Code | Cycles | Cash staked | Net P&L | ROI | Per cycle |
|---|---|---|---|---|---|
| **Thoroughbred** | 414 | $19,155.50 | **+$3,828.72** | **+20.0%** | +$9.25 |
| Harness | 10 | $405.00 | +$159.86 | +39.5% | +$15.99 |
| Greyhound | 40 | $1,257.75 | −$33.29 | −2.6% | −$0.83 |
| Non-racing (AFL etc.) | 7 | $185.00 | −$74.00 | −40.0% | −$10.57 |
| Betfair-outage bets | 3 | $153.00 | −$153.00 | −100.0% | −$51.00 |
| **All closed cycles** | **474** | **$21,156.25** | **+$3,728.29** | **+17.6%** | **+$7.87** |

**Today was 100% thoroughbred** — 144 bets, $6,686.52, +$728.62 at
10.9%. That is the normal shape of a Saturday.

**Take from it:** thoroughbreds are the engine — 414 of 474 cycles and
essentially all the profit. Everything else combined nets slightly
negative.

**Don't take from it:** that harness is the best code. Ten cycles at
~$40 average stake cannot support that; one result moves it ten points.
Greyhounds at −2.6% over 40 cycles are indistinguishable from
break-even. (Note this sits alongside S267's finding that greyhounds are
the best-*calibrated* code — calibration and profitability are different
questions, and 40 cycles settles neither.)

Conversion is deliberately **not** split by code (operator: "I just take
the 70% wherever I can get it — it may even be on sport"). It lands near
0.70 everywhere. What separates the codes is how often the promo triggers
and what the qualifier costs.

⚠️ The −$153 row is **not a betting result**: those are the three
6 August bets (Deebo, Bliss Bomb, Street Lyric, $51 each) that jumped
inside the Betfair maintenance window. No exchange market means they
could not be hedged and cannot be coded from capture. They are
thoroughbred races; they sit apart only because the data cannot see
them. Remember this when reading any code-level number.

---

## 3. Free-bet conversion

Operator definition (S268): after Betfair commission, counting only our
own money — numerator is the free bet plus **the lay on the free bet's
own selection**, denominator is the free bet's face value.

| Population | n | Mean | Median |
|---|---|---|---|
| **Headline — excludes intentional non-hedges** | **121** | **0.7018** | **0.7123** |
| Including the 2 intentional non-hedges | 123 | 0.6904 | 0.7121 |
| Money-weighted (the honest one) | — | **0.6998** | — |

Money-weighted: **$5,437.50 of face became $3,804.92**.

The 2 intentional non-hedges are the S263 operator-declared
acknowledgements (`promo_journey_annotation` tagged
`hedge_intentionally_skipped`); both lost, so both converted at 0.0000
and both are excluded from the headline as requested.

**This is the fourth independent ~70% reading** (S231, S268, S270, now
S271 on the full 121-bet population). The tool prices free bets at an
assumed **0.65**, which remains deliberate conservatism — recorded here
as measurement only, per the standing instruction not to propose
raising it.

### Unsuccessful hedge orders — a real and fixable cost

Included in the headline as requested. Splitting on whether the lay
actually filled:

| | n | Face | Converted |
|---|---|---|---|
| Hedge fully matched | 107 | $4,737.50 | **0.7313** |
| Hedge short-matched | 14 | $700.00 | **0.4862** |

**Value forgone: $171.60** — the 14 short-matched free bets converted
0.245 below the clean rate.

That is ~4.5% of all free-bet value, lost not to bad selection but to
lay orders that did not fill. It is the cheapest available improvement
in the whole operation: 2 of the 14 matched **nothing at all**.

### Do earlier hedges also CONVERT better, not just fill better? YES

Operator question, and the answer is clean.

| Lay placed | n | fully filled | money-wtd conversion |
|---|---|---|---|
| **3 min or more before jump** | 54 | 51/54 = 94% | **0.7335** |
| inside 3 min | 67 | 56/67 = 84% | **0.6744** |

**Early lays convert 0.734, late 0.674 — 6.1c in every free-bet dollar,
95% CI +2.0 … +10.1c. SIGNIFICANT.** Early clears the 0.70 bar; late
does not.

**Two separable effects, both real:**

- **Filling** — ~4 of the 6 cents.
- **Price** — comparing only FULLY-MATCHED lays, early still converts
  0.740 vs 0.721 (95% CI +0.2 … +3.8c, only just clear of zero). The lay
  sits **11.9%** above the back price inside 3 min vs **10.2%** earlier:
  the market tightens into the jump.

So placing earlier is worth **more** than the $171.60 fill-failure figure
alone implies — it also buys back part of the spread.

---

## 4. Promo performance — per whole cycle, grouped by mechanism

Amounts combined per operator instruction: "bonus winnings up to $100 /
$50 / $25" is one thing, not three. The mechanic (which positions pay) is
preserved because it is what drives the edge.

| Family | Pays when | Cycles | Cash staked | Net P&L | ROI | Per cycle | 95% CI |
|---|---|---|---|---|---|---|---|
| **Insurance — 2nd or 3rd** | 2nd *or* 3rd | 299 | $14,570.50 | **+$3,805.61** | +26.1% | **+$12.73** | **+2.75 … +22.71** |
| Price boost | enhanced odds on a win | 13 | $555.00 | +$97.20 | +17.5% | +$7.48 | −35.02 … +49.97 |
| Insurance — 2nd only | 2nd | 35 | $940.75 | +$28.81 | +3.1% | +$0.82 | −14.40 … +16.05 |
| Bonus winnings | a **win** — % of winnings | 88 | $4,160.00 | −$251.15 | −6.0% | −$2.85 | −19.40 … +13.69 |

**Combining the amounts changed the verdict.** Split by cap, "TAB Bonus
Winnings 25% to $50" read −21.1% and looked like a clear loser. As a
family, bonus winnings is −$2.85/cycle with a CI spanning zero —
**indistinguishable from break-even.** No evidence it loses; none that it
earns.

**Only insurance-2nd-or-3rd clears zero.** It is the only proven number
in this review.

### Rank on mechanics, not results

| Family | Bets | Avg odds | Wins expected | Wins actual | Edge at log |
|---|---|---|---|---|---|
| Insurance — 2nd or 3rd | 299 | 4.33 | 81.2 | **83** | 11.3% |
| Bonus winnings (to $50) | 64 | 4.19 | 17.7 | 14 | 6.0% |
| Insurance — 2nd only ($25) | 21 | 4.10 | 6.6 | 4 | 7.3% |

Insurance pays on 2nd/3rd (common); bonus winnings pays only on a **win**
(uncommon). That is the whole reason for 11.3% vs 6.0% — a fact about the
mechanics needing no sample size, unlike the realised results above.

## 5. EV at log versus real value — the check does not resolve

⚠️ **An earlier version of this section reported the indicator "running a
third hot". That was an analysis error, not a finding.**

`promo_ev_at_log` is stamped on **free bets too**, at ~70% — that is the
engine's estimate of *that free bet's conversion*, not a whole-play edge.
Summing those with the qualifiers' stamps roughly tripled the apparent
prediction ($1,980.64 → $5,853.05). The qualifier's stamp already prices
the credit it expects to earn; adding the free bet's own stamp counts the
same money twice.

**Corrected, on the 428 closed cycles carrying a stamped cash qualifier:**

| | |
|---|---|
| Predicted (qualifier stamps only) | **$1,980.64** |
| Realised (whole cycle + promo cash) | **$3,438.77** |
| Realised as a share of predicted | **173.6%** |
| Difference per cycle | **+$3.41** |
| 95% CI on that difference | **−$4.40 … +$11.21** |

The estimate came in **under** what arrived. But the CI crosses zero:
**no detectable bias in either direction.** Per-cycle sd is ~$82 against
a $3.41 effect.

### How much data each open question needs

| Question | Effect | sd | Cycles needed | Held | Status |
|---|---|---|---|---|---|
| Is the EV estimate biased? | $3.41 | $82.38 | 2,242 | 428 | open, far off |
| Do bonus-winnings promos lose? | −$2.85 | $79.20 | 2,967 | 88 | open, far off |
| Does insurance 2+3 make money? | +$12.73 | $87.90 | 183 | 299 | **answered: yes** |

**This table is the honest summary of the whole review.** One question is
settled; the others need an order of magnitude more data than exists.
Where a result cannot be measured, rank on mechanics instead.

**Recalibration is still worth scheduling** — not because the model is
provably wrong, but because what it models has moved: international
racing (S268), a shifted promo mix, and a trigger rate now measured at
28.4% of stake with nothing recent to check it against. Maintenance, not
a bug fix. (Operator noted the model has not been recalibrated for a
while; this is the reason to do it.)

## 6. Cycles

- **474 closed, 1 open.**
- Net across closed cycles: **+$3,562.15**
- Average per closed cycle: **+$7.52**
- Profitable cycles: **132 / 474 (27.8%)**

The low hit rate is expected and not a warning sign: the standard cycle
loses a little on the qualifier and only turns positive when the free
bet converts. Profit is concentrated, by design.

**Credit inventory: nothing idle.** All **$6,001.00** of credit earned
has been spent — the tool reports **zero in hand**, and there are no
open cycles holding a bonus. Exactly **$10.00** has ever expired unused:
**0.17%** of everything credited. For a promo operation that is very
tight turnover discipline, and it is worth protecting as volume grows.

⚠️ An earlier draft of this review claimed $523.50 sat in hand. That was
wrong — it came from subtracting free-bet stakes from credit face rather
than asking the tool. Credit face and the stake it funds are not the
same quantity, and superseded/replaced credits (the S270 $50→$51
correction, today's Sarie move) still carry a `finalised` status. **Ask
`ops.correct_promo_chain credits --pairing <aab>` or read the daily
money check; never subtract.**

---

## 7. Quiet days — worse, but not because they are quiet

| Date | Bets | Staked | P&L | ROI |
|---|---|---|---|---|
| 30 Jul | 18 | $358.06 | −$78.15 | −21.8% |
| 31 Jul | 8 | $201.36 | +$35.15 | +17.5% |
| 1 Aug | 121 | $5,254.58 | +$1,443.42 | +27.5% |
| 2 Aug | 22 | $730.01 | −$377.01 | −51.6% |
| 3 Aug | 18 | $925.07 | −$671.54 | −72.6% |
| 4 Aug | 9 | $415.58 | −$44.76 | −10.8% |
| 5 Aug | 38 | $1,217.68 | +$287.34 | +23.6% |
| 6 Aug | 5 | $233.00 | −$140.50 | −60.3% |
| 7 Aug | 9 | $253.24 | +$150.42 | +59.4% |
| **8 Aug** | **144** | **$6,686.52** | **+$728.62** | **+10.9%** |

⚠️ **An earlier version said "ignore thin days, they're noise." Too
glib — operator pushed back ("maybe they're not profitable") and was
right.** Measured per CYCLE:

| Day type | Cycles | Net P&L | Per cycle | Avg EV at log | Insurance share |
|---|---|---|---|---|---|
| Quiet (<40 bets) | 152 | −$563.24 | **−$3.71** | 7.24% | **32%** |
| Busy (100+ bets) | 316 | +$4,161.21 | **+$13.17** | 10.98% | **90%** |
| Difference | | | **−$16.87** | | |

95% CI on the gap: **−$30.89 … −$2.85 — SIGNIFICANT.**

**But the mechanism is the last two columns, not luck.** Busy days are
90% insurance promos; quiet days only 32%, and average EV falls 10.98% →
7.24%. **A quiet day is a day when the good promos are not on offer, so
the thin ones get worked.** Volume is a symptom of promo availability,
not a cause of returns.

Split further, no sub-cell survives: insurance on quiet days is 16
cycles; bonus winnings on quiet days is −$8.94/cycle with CI −$27.50 …
+$9.63. **The data cannot yet separate "quiet day" from "thin promo"** —
but the mechanism explains the gap far better than variance does.

**Revised advice:** on a quiet day, check what is actually on offer. If
it is only bonus-winnings promos, honest expectation is near zero and
**not betting is a legitimate call**. Still don't read a five-bet day's
*percentage* as a verdict on the system.

---

## 8. What this suggests

Ordered by value against effort. The top two recover money already
earned; the rest change how the numbers are read.

1. **Place hedges earlier.** Conversion 0.674 → 0.734 at 3+ min out — it
   fills more AND prices better. Worth 6.1c per free-bet dollar,
   recurring. Two lays went on *after* the jump.
2. **Alert on unmatched lays.** Two hedges matched nothing and nothing
   flagged it. An unhedged free bet is a naked position — risk, not just
   value.
3. **Recalibrate the model.** Not because it is provably wrong —
   corrected, it reads slightly conservative — but because international
   racing, the promo mix and the 28.4% trigger rate have all moved since
   it was tuned. Maintenance. **Operator flagged this is overdue.**
4. **Show promo ROI per cycle, grouped by family, in the tool.** Per-bet
   rates the best promo at +4.2% instead of +26.1%; per-template makes a
   break-even family look like a −21% disaster.
5. **Prefer insurance over bonus-winnings.** 11.3% vs 6.0% edge, from the
   mechanics. Ranking on *results* would need ~2,970 cycles.
6. **Stay on thoroughbreds by default.** 414 of 474 cycles, essentially
   all profit.
7. **Work more promos per day.** The only lever that compounds and the
   only proven number here: **+$12.73 per insurance cycle.**
8. **On a quiet day, check the offers** rather than assuming noise. If
   only thin promos are up, not betting is legitimate.

**Not on this list any more:** "deploy idle credit faster" (there is no
idle credit — §6) and "discount EV by a third" (that was built on the
free-bet-stamp error — §5).

---

## 9. Corrections log — what this review got wrong

Three, all found by operator challenge. Recorded because the *class* of
error matters more than the instances.

1. **$523.50 of credit "in hand"** — derived by subtracting free-bet
   stakes from credit face. Invalid: face ≠ stake funded, and superseded
   credits still read `finalised`. **Truth: zero in hand.** Ask the tool
   (`ops.correct_promo_chain credits --pairing`), never subtract.
2. **"EV runs a third hot"** — free bets carry their own ~70%
   `promo_ev_at_log` (their conversion estimate) and those were summed
   with the qualifiers'. **Truth: qualifier-only prediction $1,980.64 vs
   $3,438.77 realised — conservative, and inside the noise.**
3. **"Ignore thin days, they're noise"** — too glib. **Truth: quiet days
   are significantly worse (−$16.87/cycle) and the cause is promo mix,
   which is actionable.**

Common thread: **three separate populations got conflated with the
population that actually answers the question.** Define the population
before computing the statistic.
