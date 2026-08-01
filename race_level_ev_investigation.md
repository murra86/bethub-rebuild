# Race-level promo EV and the interdependence of bets (S253)

**The question:** if I hold several promo bets on one race — any mix of runners
and promo types — what is my race-level EV, what does adding one more bet do to
it, and how should that drive decisions. Focus: insurance.

**The short answer, and it is the valuable part:** race-level EV is a plain
**sum**. There is no interaction term to model. The interdependence you are
sensing is real, but it lives entirely in **risk (variance)**, not in EV — and
risk-per-race is not the axis you judge the operation on. So the honest finding
is that this needs almost no new machinery: one cheap convenience panel and one
real-world constraint to confirm, not a probability engine.

The mathematics is checked against real finishing positions (1,676 races,
April–July). Working file:
`bethub-analytical/promo_ev_forecast/race_portfolio_ev.py`.

---

## Finding 1 — Race-level EV is additive. Full stop.

A bet's payout depends only on **its own runner's** finishing position. By
linearity of expectation, the expected value of a set of bets is the sum of
their individual expected values — **with no correlation term**. This is not an
approximation; it is exact, and it does not require the bets to be independent.

Consequences, each of which I verified:

- **Your race-level EV = the sum of your placed bets' EVs, in dollars.** The
  per-runner EV the screen already shows you, added up over the runners you bet,
  IS your race EV.
- **Adding a bet adds exactly its own EV and changes nothing about the bets
  already placed.** Betting Runner B does not move Runner A's EV. A's number
  only appears to change on screen because A's *price* drifted (Finding 2) —
  not because of B.
- **This holds across promo types.** Insurance on A + boosted odds on B + bonus
  winnings on C: the race EV is still the three individual EVs added. Mutually
  exclusive wins and competing 2nd/3rd places are already baked into each
  runner's own probabilities.

Validated on real money — predicted sum vs realised average P&L, insuring the
top-N runners by EV:

| strategy | races | predicted race EV | realised | gap |
|---|---|---|---|---|
| top-1 | 1,676 | $11.73 | $9.55 | −$2.18 (±3.88) |
| top-2 | 1,676 | $22.67 | $19.45 | −$3.22 (±5.26) |
| top-3 | 1,676 | $32.44 | $30.36 | −$2.08 (±6.70) |

Every gap is inside its confidence band, and the small consistent shortfall is
the known tail overstatement, not an interaction effect. **The sum is the
answer.**

> This partly deflates the premise. You suspected the bets interact in a way
> that makes race EV more than the sum of the screen numbers. For EV, they do
> not. That is good news — it means no model is needed to know your race EV.

## Finding 2 — The one real correction: mark a placed bet to its locked price

There is exactly one way the screen misleads you at race level, and it is not
about interaction — it is about **time**.

When you place a bet you lock a price. The screen keeps repricing that runner
at the *current* price. So the live per-runner EV on the screen is the EV of a
bet you *could place now* — not the EV of the bet you *already placed*. The two
differ by the price drift:

- **runner drifts out** (3.50 → 3.60): your locked 3.50 is now the *worse*
  price, so the screen **over**-states your placed bet;
- **runner shortens** (3.50 → 3.40): your locked 3.50 is the *better* price, so
  the screen **under**-states your placed bet — you are holding value the screen
  doesn't show.

The size of this: on an individual $50 bet the gap between the screen's live
number and your placed bet's true value averages about **$6**. It is *unbiased*
(drifts and shortens roughly cancel across many bets), so it does not cost you
EV over time — but on any single race it is real money, and it is the one number
a race-level view would get right that eyeballing the screen gets wrong.

Worked through your example (consistent toy landing on your figures):

| | at bet | after A drifts 3.50→3.60 |
|---|---|---|
| Bet A ($50 ins, locked 3.50) | +$7.26 | screen shows +$6.46, **true +$5.19** |
| Bet B ($50 ins, locked 2.80) | +$6.32 | +$6.32 (untouched by A) |
| **Race EV** | **+$13.59** | **+$11.51** |

A's drift lowered A's EV and nothing else; the screen's +$6.46 credits you the
3.60 you can now get but do not hold. Your true position is +$5.19 on A.

## Finding 3 — The interdependence is all in the variance (and it is benign)

Where the bets genuinely interact is risk. Monte-Carlo over joint finishing
orders (Plackett-Luce, 4,000 draws/race, 1,200 races):

- **Two insurance bets on different runners in one race are negatively
  correlated** — trigger correlation −0.26, P&L correlation −0.31. The 2nd and
  3rd slots are scarce, so the runners compete for them. This **cuts** the P&L
  standard deviation about **13%** below what two independent bets would carry.
- **Doubling the same money on one runner** (two promos, or promo + raw) is
  perfectly correlated and carries roughly **50% more** P&L standard deviation
  than the same stake spread across two runners. Identical EV, materially more
  risk.
- **Concentrating within a race vs spreading across races:** two bets in one
  race carry *lower* variance and lose slightly less often (≈50% of the time)
  than one bet in each of two races (≈54%) — again because within-race triggers
  diversify each other.

So the risk story is the opposite of scary: spreading insurance across contenders
in a race is a **variance-reducing** move. The catch is not statistical — it is
that more bets on one race is the **account-restriction** signal you already
watch for.

**Why this is informational, not decision-driving:** your own standing note is
that you judge the engine over many bets, not on any one race's P&L (a true
+10% EV book still loses on ~36% of race days). Per-race variance is not your
decision axis, so a per-race risk readout would be a number you look at and then
correctly ignore.

## Finding 4 — What actually decides "should I add this bet"

Putting it together, the decision rule for adding a bet to a race is simple and
mostly already in the tool:

- **EV:** add it iff its own EV clears your bar. The race context does not change
  this — there is no interaction to price in.
- **The one genuine exception — shared caps.** If a promo is *one per race* or
  caps total bonus per race, a second bet under the same promo does **not** earn
  its bonus, so its marginal EV collapses to the (negative) raw bet. The tool's
  catalogue models caps **per bet, not per race**, so it would happily show a
  second same-promo bet as +EV that the book will not actually honour. **This is
  the real interdependence in your operation, and it is a rules constraint, not
  a maths one.**
- **Risk / account safety:** if you do stack, spread across runners rather than
  double on one, and remember each extra bet on a race raises restriction risk.

---

## Finding 5 — Multi-account coverage: EV vs consistency (operator update)

The operator clarified: promos are one-per-race *per account*, but with several
accounts there can be **4–5 promo bets on one race**, and the goal is to
**maximise EV while lowering variance toward steady, tick-along P&L**.

Simulated on real races (1,676, 6–16 runners), $50 insurance bets, model-free
realised P&L. Book price = fair, so EV levels are optimistic and this is the
*worst case* for spreading (all accounts see one price):

**Covering the top-K runners by EV:**

| bets | staked | EV $ | EV % | P&L std $ | P(race profits) | catches winner |
|---|---|---|---|---|---|---|
| 1 | 50 | 11.73 | 23.5% | 80.95 | 25.8% | 26% |
| 3 | 150 | 32.44 | 21.6% | 139.85 | **55.7%** | 65% |
| 5 | 250 | 47.75 | 19.1% | 222.17 | 49.8% | 85% |

**5 accounts — concentrate on the best runner vs spread across the top 5:**

| plan | EV $ | P&L std $ | P(profit) | worst 5% |
|---|---|---|---|---|
| 5 on the best runner | 58.65 | 404.73 | 25.8% | −$250 |
| 1 each on top-5 | 47.75 | **222.17** | **49.8%** | −$217 |

Spreading gives up ~$11 of EV (19% here, and *much less in reality* — see below)
to **halve the variance** and **double the chance the race turns a profit**.

**Three things follow, and one of them is a hard truth:**

1. **Spreading across runners serves both goals at once.** It costs little EV and
   sharply cuts variance, because the insurance triggers compete for 2nd/3rd and
   because you catch the winner far more often (26% → 85% of races).
2. **The EV cost of spreading is smaller than 19% for you specifically.** That
   number assumes every account could back the *same* runner at the same edge.
   In reality your edge comes from *different books mispricing different
   runners*, so chasing the best EV per account already scatters you across
   runners — you largely get the variance reduction for free. Max-EV and
   low-variance are barely in tension for a multi-account operator.
3. **The hard truth: unhedged insurance cannot be tick-steady.** Even doing
   everything right — 5 accounts spread across the field — the per-race P&L
   standard deviation is ~$222 on $250 staked and the race still loses about half
   the time. The profit engine is the *win*, which is a lump; insurance only
   softens the losses. Covering the race lowers variance *per dollar* and lifts
   the hit rate, but it cannot make one race steady. **Consistency comes from
   VOLUME — many +EV races, where the law of large numbers turns edge into steady
   growth — not from any single race.** True tick-steadiness would need hedging,
   which you have correctly excluded for promo bets.

So the coverage decision has a sweet spot the tool can help you hit: **P(profit)
peaks around 3 covered runners; total EV keeps rising to 5; EV% is highest at
1–2.** There is no single right answer — it depends on how you weigh dollars
now versus a smoother ride — and that is exactly the tradeoff an indicator can
put in front of you per race.

Script: `promo_ev_forecast/race_coverage_strategy.py`.

## Capability options

*(Revised after the operator's multi-account / variance-goal update — the risk
readout is now wanted, so it moves from "skip" to core.)*

| | What it is | Build cost | Value |
|---|---|---|---|
| **A. Race EV strip** | Sums placed bets into one race-level EV in $ (and %), **marked to locked price** (Finding 2); shows total exposure and the marginal EV of a candidate | **Low** — data already stored (`bet_legs.betfair_market_id`, `bets.promo_ev_at_log`, `matched_price`); client-side arithmetic | Answers "what's my race EV" and "what does adding a bet do"; fixes the ~$6/bet placed-vs-current gap |
| **B. Consistency readout** | P(this race profits) and the P&L range, updating as bets are added; marginal Δrisk of a candidate (does it raise or lower variance) | **Medium** — a few-thousand-draw Plackett-Luce Monte Carlo in the client (fast, ~10 lines of the maths already written) | **Now high** — variance is a stated goal; this is what lets the operator hit the coverage sweet spot and avoid the concentrate trap |
| **C. Coverage suggester** | "You have 2 accounts left; covering X and Y adds $12 EV and lifts hit-rate to 55%" | Higher | Phase 2 — useful once A+B exist |
| **D. Kelly staking** | Growth-optimal sizing of same-race bets | High | Low — promo stakes are capped, little freedom to size |

## Cost / benefit

- **A + B together are the product.** A is nearly free (the per-bet EV is already
  stamped). B adds a small client-side simulation but is what turns the panel
  from a tracker into a decision aid now that variance matters: it shows P(profit)
  and the P&L range, and whether a candidate bet *reduces* variance (a runner you
  don't yet cover) or *concentrates* it (another account on a runner you hold).
- **C is a natural follow-on** once A+B exist — it just searches the allocation
  A+B can already score.
- **D solves a problem you mostly don't have** — promo stakes are capped, so
  there's rarely a fraction to optimise.

## Recommendation

1. **Build A + B** — a read-only "this race" panel: race EV in dollars and
   percent (locked-price marked), total exposure, **P(race profits) and the P&L
   range**, and — when you arm a candidate — its marginal **ΔEV and Δrisk**. This
   directly serves both stated goals (max EV, lower variance) at the 4–5-bet
   scale you actually bet, and the heavy data is already stored.
2. **Hold C (coverage suggester) as phase 2** and **skip D (Kelly)**.
3. **Do not build a race-level "EV interaction" model** — the EV is the sum;
   there is nothing to compute there. The portfolio maths that *is* worth
   computing is the **variance/consistency** side (B), not the EV side.
4. **Set the expectation honestly in the UI:** the panel helps you find the
   EV/consistency sweet spot per race, but no single race is tick-steady —
   consistency is a volume game across many +EV races. The panel should read as
   "am I covering this race well," not "have I made this race safe."

The honest headline: your race EV is already the sum of the screen EVs at your
locked prices — that part needs only presenting, not modelling. The genuinely
valuable new capability is on the **variance** side you just prioritised: a
live P(profit)/coverage readout that guides how many accounts to spread across
each race.
