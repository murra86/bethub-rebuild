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

| Code | Cycles | Cash staked | Net P&L | ROI | Per cycle | FB conv. |
|---|---|---|---|---|---|---|
| **Thoroughbred** | 414 | $19,155.50 | **+$3,828.72** | **+20.0%** | +$9.25 | 0.69 |
| Harness | 10 | $405.00 | +$159.86 | +39.5% | +$15.99 | 0.69 |
| Greyhound | 40 | $1,257.75 | −$33.29 | −2.6% | −$0.83 | 0.71 |
| Non-racing (AFL etc.) | 7 | $185.00 | −$74.00 | −40.0% | −$10.57 | — |
| Betfair-outage bets | 3 | $153.00 | −$153.00 | −100.0% | −$51.00 | — |
| **All closed cycles** | **474** | **$21,156.25** | **+$3,728.29** | **+17.6%** | **+$7.87** | 0.70 |

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

**The interesting line is the last column:** free-bet conversion is flat
across every code — 0.69 thoroughbred, 0.71 greyhound, 0.69 harness.
Whatever separates the codes, it is not how well free bets cash out. It
is how often the promo triggers and what the qualifier costs.

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

---

## 4. Promo performance — per whole cycle

Judging a promo by the bets tagged with it is misleading: the tag sits
on the qualifier, while the value arrives as a credit that is spent
later. Scored per complete cycle (qualifier + hedge + free bet + promo
cash), single-template cycles only:

| Template | Cycles | Cash staked | Net P&L | ROI |
|---|---|---|---|---|
| Ins $50 FB 2+3 | 299 | $14,570.50 | **+$3,805.61** | **+26.1%** |
| Bet365 Bonus Winnings (Cash) | 20 | $820.00 | +$270.63 | +33.0% |
| TAB Bonus Winnings 25% to $100 (FB) | 4 | $160.00 | +$149.11 | +93.2% |
| Boosted Odds | 13 | $555.00 | +$97.20 | +17.5% |
| Ins $50 FB 2nd | 13 | $458.00 | +$35.20 | +7.7% |
| Ins $25 FB 2nd | 21 | $457.75 | −$68.89 | −15.0% |
| TAB Bonus Winnings 25% to $50 (FB) | 64 | $3,180.00 | **−$670.89** | **−21.1%** |

Compare the naive per-bet view, which scored *Ins $50 FB 2+3* at only
+4.18% ROI. Counting the credit it earns takes it to **+26.1%**. Always
read promos at cycle level.

**One promo carries the operation.** *Ins $50 FB 2+3* is 299 of 434
attributable cycles and delivers $3,806 of $3,618 net — more than the
whole book, because the rest nets negative.

### Are the two losing promos structurally bad, or unlucky?

| Template | n | Avg odds | Expected wins | Actual | Avg EV% at log |
|---|---|---|---|---|---|
| Ins $50 FB 2+3 | 299 | 4.33 | 81.2 | **83** | **11.3%** |
| TAB Bonus Winnings 25% to $50 | 64 | 4.19 | 17.7 | **14** | 6.0% |
| Ins $25 FB 2nd | 21 | 4.10 | 6.6 | **4** | 7.3% |

Both losers were **thin to begin with** (6.0% and 7.3% expected edge
versus 11.3% for the workhorse) **and** have run behind expectation
(3.7 and 2.6 wins short). At ~$50 a bet and ~4.2 average odds, being
3.7 wins light is roughly $590 — most of the $671 shortfall.

**Verdict: do not kill these promos on this evidence.** The sample is
small and the result is dominated by variance. The real finding is
structural: an insurance promo pays when the horse runs 2nd or 3rd,
which is common; a bonus-winnings promo pays only when it **wins**,
which is not. That is why one shows 11.3% expected edge and the other
6.0% — and why the thin ones have no cushion when luck turns.

---

## 5. EV at log versus real value

`promo_ev_at_log` is a **percentage of stake**, not dollars
(`ConfirmCard.tsx` renders it `{x}%`). The engine computes
`rawEv + pInsured × bonusValue × fbConversion`, all over stake — an
**unhedged** figure that ignores Betfair commission. Since qualifiers
are in fact never hedged (only 121 lays against 467 cash backs — laying
is free-bets-only per S252), that assumption matches practice.

Scored per closed cycle carrying an EV stamp (n=437):

| | |
|---|---|
| Predicted | **$5,853.05** (23.1% of stake) |
| Realised | **$3,638.78** |
| Gap | **−$2,214.27** — 62.2% of prediction delivered |
| Cycles meeting or beating their EV | 121 / 437 (27.7%) |

**The indicator is directionally right but materially optimistic.**

What the realised figure is actually made of — every line measured, not
attributed:

| Component | |
|---|---|
| Free bets, gross | +$6,832.00 |
| Hedges (commission + spread) | −$3,027.10 |
| Qualifiers in those cycles | −$332.25 |
| Promo cash banked | +$166.13 |
| **Realised** | **$3,638.78** |

Two contributors to the shortfall are measured directly: the qualifiers
came in at −$332 where fair odds imply about zero, and the unfilled
hedges cost $172 — together $504 of the $2,214 gap.

**The rest points at the insurance triggering less often than the model
assumes.** Working backwards through the engine's own arithmetic, a
23.1% predicted edge at the assumed 0.65 conversion implies it expected
about **35.6% of stake** back as credit face. Actual credit earned was
**$6,001 on $21,156** of qualifying stake — **28.4%**. That gap is worth
roughly **$1,000** more.

⚠️ The 35.6% is *inferred, not stored*: it assumes the raw punting edge
is near zero and the bonus equals the stake. Both hold for the insurance
promo that dominates the sample, not for every template. Right
explanation, roughly the right size — not a precise figure.

Note the direction of the remaining error: the EV uses a **0.65**
conversion assumption while actual conversion is **0.70** — so the
prediction is *conservative* on that term. The optimism sits entirely in
how often it thinks the horse will place.

**Do not treat the 23.1% EV number as a forecast of returns.** Realised
return on turnover is 12.1%. That is still an excellent business; it is
just about half of what the indicator advertises.

---

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

## 7. Day-by-day (last ten active days)

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

Daily ROI swings between −73% and +59%. **Volume is what stabilises
it**: the two 100+ bet days (1 Aug, 8 Aug) both landed near the
long-run rate, while every wild swing came on a day of fewer than 40
bets. Small days are noise, not signal — do not read a thin day's ROI
as information.

---

## 8. What this suggests

Ordered by value against effort. The top two recover money already
earned; the rest change how the numbers are read.

1. **Place hedges earlier.** Fill rate goes 85% → 96% when the lay is on
   5+ minutes out; two lays went on *after* the jump. Worth $171.60 so
   far and recurring. Pure execution.
2. **Alert on unmatched lays.** Two hedges matched nothing at all and
   nothing flagged it. An unhedged free bet is a naked position — this
   is risk, not just value.
3. **Recalibrate the place-rate in the EV engine.** It implies ~35.6% of
   stake returns as credit face; actual is 28.4%. Single biggest driver
   of the EV gap (~$1,000 of $2,214) and a one-number fix.
4. **Show promo ROI per cycle in the tool.** The per-bet view rates the
   best promo at +4.2% instead of +26.1%. Anyone reading it draws the
   wrong conclusion.
5. **Prefer insurance promos over bonus-winnings promos.** Insurance
   pays on 2nd/3rd (11.3% edge); bonus-winnings only on a win (6.0%).
   Not enough evidence to drop the thin ones — enough to rank them.
6. **Stay on thoroughbreds by default.** 414 of 474 cycles and
   essentially all profit. No reason to chase greyhounds at −2.6%.
7. **Discount the EV indicator by roughly a third when planning.**
   23.1% advertised, 12.1% delivered.
8. **Harvest more promos; stop trying to pick winners.** Qualifiers net
   −1.1% over 467 bets. Throughput is the only lever that compounds, at
   ~$9.25 per thoroughbred cycle.
9. **Ignore thin days.** Under 40 bets, daily ROI swings −100% to +59%
   on noise. Reacting to them invites unwarranted changes.

**Not on this list any more:** "deploy idle credit faster." There is no
idle credit — see §6.
