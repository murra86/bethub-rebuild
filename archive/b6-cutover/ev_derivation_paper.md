# How your promo EVs are calculated — the derivation, in plain language

**Written:** Session 231, 2026-07-06, for the operator. Piece 1 of the EV validation arc
(`ev_validation_commission.md`). This describes what the race screen actually computes —
the code lives in `ui/web/src/ev/evEngine.ts` and this paper was written from that code,
not from memory. Anything here that doesn't survive your interrogation gets fixed —
in the paper or in the engine, whichever is wrong.
**v1.1** — revised same session after the v2 empirical run (`ev_validation_findings.md`)
and three external reviews (operator-run ChatGPT/Grok/Gemini): claim language tightened,
one factual figure corrected (the overround), assumption ledger updated with the measured
verdicts.

The pipeline at a glance:

```
Betfair back/lay prices
        │
        ▼
Midpoint odds (geometric)      ← no lay? back + 2 ticks, flagged ⚠
        │
        ▼
Implied win chances, scaled to sum to 100%
        │
        ▼
Harville step-down (corrected)
        │
        ▼
Chances of exactly 2nd / 3rd / 4th
        │
        ▼
Promo payout mechanics ($ through each outcome)
        │
        ▼
EV% on the race screen
```

---

## The one-paragraph version

For every runner, the tool asks three questions. **One:** what is this runner's true chance
of winning? (Answer: read it off Betfair — the most liquid, least-margin-loaded public
probability estimate available for AU racing, and the v2 validation confirmed it calibrates
as well as Betfair's own starting price.) **Two:** what is its chance of running exactly
2nd, 3rd or 4th? (Answer: a standard racing formula that converts win chances into place
chances — this is the "Harville" piece.) **Three:** given those chances, what does this
specific promo pay across every possible outcome? (Answer: multiply each outcome's chance
by its dollar result, add them up, and express it as cents-per-dollar-staked. That's the
EV% you see.)

---

## Step 1 — the runner's true winning chance

**Where it comes from.** Betfair shows two prices per runner: the **back** price (what you
can take right now) and the **lay** price (what layers are asking). The engine's estimate of
the fair price sits between them — that's a modelling assumption, and it's the one Test 1 of
the validation checked (it passed). The engine uses the *geometric midpoint* — multiply the
two prices together and take the square root. Back $5.00 / lay $5.20 → √(5.00 × 5.20) =
$5.10. Geometric rather than the simple average because odds move proportionally: $2 → $4 is
the same size move as $20 → $40, and the geometric midpoint respects that at every price
level (it's also near-identical to averaging the implied chances, which stops longshot
chances inflating the way a simple average of big odds would).

**When half the picture is missing.** If a runner has no lay price (thin market), the engine
takes the back price and moves it two ticks worse as a safety margin, and flags the number
as low-confidence. On the screen: a tilde (~) means wide back-lay gap — trust it less; the
warning triangle means no lay at all — the number is a guess with a safety margin.

**Squeezing the water out (removing the overround).** Convert every runner's midpoint price
into an implied chance (1 divided by the odds), then scale the whole field so the chances add
to exactly 100%. Measured across all 16,889 validation races: midpoint implied chances
average **99.5%** — a whisker *below* 100%, so the scaling is a light touch (and corrects
v1 of this paper, which guessed ~100.5% the other side). Either way the step guarantees no
phantom margin leaks into the EVs.

**What this step assumes.** (a) Betfair's midpoint is an unbiased estimate of the true
chance; (b) commission does NOT belong here (it's a cost of hedging, not a fact about the
horse — it's charged where you actually pay it, in the free-bet hedge maths); (c) the price
you can actually get at the book is entered separately — the Betfair side only supplies the
probability. Assumption (a) is exactly what Test 1 of the empirical check validates.

## Step 2 — chance of running 2nd, 3rd, 4th (the Harville piece)

Your insurance promos pay on placings, so the tool needs "chance of finishing exactly 2nd",
not just "chance of winning". No market quotes that directly, so it's derived.

**The core idea (Harville, 1973).** Chance runner B runs 2nd = chance someone else (say A)
wins × chance B "wins" the race that's left after removing A — where B's chance among the
leftovers is just its win chance re-shared over the remaining field. Sum over every possible
winner A, and you have B's chance of running 2nd. Same trick again, one layer deeper, for
3rd; again for 4th.

**The known flaw, and the correction.** Two separate ideas here, worth keeping apart:
*Harville provides the structure* (the remove-and-re-share arithmetic above); *the exponents
are an empirical correction layered on top of it*. Raw Harville has a documented bias: it
makes favourites too likely to fill the minor placings (a horse that fails to win often
failed for a reason — it flattens out worse than raw arithmetic assumes). The standard
correction (Lo / Bacon-Shone / Stern): at each step-down layer, before re-sharing the
remaining field, raise each survivor's win chance to a power slightly below 1, which
squashes the favourite's edge in the fight for that placing. The exponents apply layer by
layer — **0.77 when re-sharing for 2nd, 0.62 for 3rd, 0.48 for 4th** — each layer flattening
more, matching the real-world pattern that the further down the finishing order you go, the
more random it gets.

**Where 0.77 / 0.62 / 0.48 came from — and where they stand now.** Originally calibrated on
AU racing 2025–26 in the earlier racing EV model project, with a 5% safety margin. They are
the single most load-bearing constants in your insurance EVs. The v2 validation re-fitted
them from scratch on ~135,000 runner-results: gamma came back **exactly 0.77**, delta 0.60
(vs 0.62), epsilon 0.55 (vs 0.48, small sample) — differences too small to act on, and the
fitting surface is flat, so the stronger evidence is the calibration tables themselves
(place chances true to within ~1 point). **All three held.**

**Worked example** (numbers produced by this exact calibrated model — the same run archived
with the validation). A $5.00 runner in a realistic 10-horse field: ~19.9% to win, ~17.0% to
run exactly 2nd, ~14.1% exactly 3rd, ~11.4% exactly 4th. Note the gentle stepdown — win
chance and 2nd chance are close for a mid-priced runner; that pattern is what Test 2
verified against reality.

## Step 3 — pushing dollars through the promo

All EVs are per dollar staked, shown as a percentage. A worked example each; all use the
$5.00 runner above (19.9% win / 17.0% 2nd / 14.1% 3rd), $25 stake.

**No promo (the baseline).** Chance × payout − stake: 0.199 × $5.00 = $0.995 back per $1,
i.e. **−0.5%**. A fair-priced bet loses you nothing but wins you nothing — the promos are
where your edge lives.

**Insurance (Strategy 1).** You get the no-promo result PLUS: chance-of-refund × refund
value. Cash refund: full face value. Free-bet refund: face × 65% (the standing conversion
assumption — see the ledger below). Free bet if 2nd: −0.5% + (17.0% × $25 × 0.65)/$25 =
−0.5% + 11.1% = **+10.6%**. Add 3rd-place cover and the refund chance nearly doubles →
**+19.8%**. Cash-if-2nd swaps the 0.65 for 1.0 → **+16.5%**. The caps ($25/$50) don't change
the percentage while your stake is under the cap — they cap how much stake qualifies.

**Bonus winnings (Strategy 2b).** Winning pays odds PLUS a bonus on the winnings. The engine
folds the bonus into an effective price. At $25 on the $5.00 runner your winnings would be
$100, so the 100%-of-winnings free bet hits its $50 cap: bonus = $50 face = $2 per dollar
staked, worth 65% → effective odds $5.00 + $2 × 0.65 = $6.30 → EV 0.199 × 6.30 − 1 =
**+25.4%**. (Uncapped it would be far higher — the cap is doing real work at this stake;
halve the stake and the percentage improves. On a short-priced favourite the winnings might
never reach the cap at all. The engine computes the cap's bite from the actual stake and
odds of each bet — the worked number here is one point on that curve, not a flat rule.) The
25%-cash version, uncapped: bonus $1 per dollar staked at full value → effective odds $6.00
→ **+19.4%**.

**Boosted odds (Strategy 2a).** No mechanics — just EV at the boosted price. $5.00 → $5.50
on a 19.9% chance: 0.199 × 5.5 − 1 = **+9.5%**. The entire edge is the price difference.

**Free-bet conversion (the downstream leg of every cycle).** When you turn a free bet into
cash by backing at the book and laying on Betfair: lay-stake = face × (book odds − 1) ÷
(lay odds − commission); locked profit = lay-stake × (1 − commission). Back $5.00, lay
$5.00, 8% commission: $50 face → 50 × 4 × 0.92 / 4.92 = **$37.40 = 74.8%** — the number you
quoted for the $5/$5 case, reproduced by the engine to the decimal. This formula is verified
against operator ground truth (S231). **To head off an apparent contradiction:** the 74.8%
is what the live hedge maths yields at ideal $5/$5 prices; the 65% used *inside the promo
EVs* (below) is a deliberately lower flat planning value for future free bets whose lay
prices are unknown — a conservative assumption, not a mathematical result, and
operator-locked at S231 (general realised conversion runs ~70%).

## The assumption ledger — every number that isn't derived

Statuses updated with the v2 measured verdicts (impact column per external review).

| # | Assumption | Value | EV impact | Verdict (v2 run) |
|---|---|---|---|---|
| 1 | Betfair midpoint field = true chances | — | High | **PASSED** — calibrated to ≤0.7 pts across 20 bands; one residual: $6–$10 runs ~3 EV pts hot (haircut rule) |
| 2 | Harville correction exponents | 0.77 / 0.62 / 0.48 | High | **HELD** — refit landed on 0.77 exactly; delta/epsilon differences immaterial; place chances true within ~1 pt |
| 3 | Free-bet conversion (flat, inside promo EVs) | 65% | Medium | **Operator-locked** (general ~70% realised; 65% deliberately conservative); sensitivity measured ≈ +0.9 EV pts per +5c |
| 4 | Betfair commission | 8% | Medium | Matches your account; config constant |
| 5 | No-lay fallback | back + 2 ticks, flagged ⚠ | Low | Conservative for the flagged runner; nudges *rivals'* EVs up slightly — tested at field level: no measurable lean (fallback races 4% of sample). Parked hardening candidate |
| 6 | Field normalisation to 100% | multiplicative | Low | Standard; measured light-touch (midpoint books average 99.5%) |
| 7 | Book price entered = price you'll be paid | — | High | Operational — your judgement at bet time; NOT testable from this data. Screen EV is only as real as the price you actually get |

## What stands validated (v2, 2026-07-06)

**Measured and passed:** win-chance calibration (163k runners); place-chance calibration
(135k runners with full finishing order); the promo arithmetic end-to-end (internal-
consistency backtest, 45,656 simulated bets); the free-bet hedge formula (your ground truth,
to the decimal); the live-feed agreement with BSP (median 1.1 pts; fat tail in thin markets —
hence the flags).

**The two standing operational rules the validation produced:** haircut $6–$10 screen EVs by
~3 points; never execute on a ~/⚠-flagged EV as a firm number. Full detail, caveats register
included, in `ev_validation_findings.md`; the hostile second opinion is filed verbatim at
`dr029/ev_validation/adversarial_review.md`.

One scope note: everything here is calibrated on AU racing. If the operation ever extends
to other jurisdictions, the constants need re-checking there (the archived script makes that
cheap).

Read this paper hard. Anything that doesn't convince you, say so — the whole point is that
these numbers stop being mine and start being yours.
