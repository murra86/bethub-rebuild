# Hedge-staking math review

**Purpose:** Lock the staking formulas behind W4's
directional-drift handling before they embed in
the v3 bet-entry tool. v2 has a history of math
errors in this area; this review derives the
formulas from first principles, names every
assumption explicitly, and verifies via worked
numerical examples.

**Scope:** Two-leg hedge math where one leg sits
at a soft-book and one leg sits on Betfair
Exchange. Soft-book leg is back-only (soft-book
lay does not exist as a soft-book product). Betfair
leg can be lay (against soft-book back — common
case) or back (alternative construction in
two-outcome markets only). Cycle-equalisation
derivation; dynamic Betfair commission handling;
favourable vs unfavourable drift handling; worked
numerical examples for cash and free-bet hedges.

**Out of scope:** Strategy 3 (SGM correlated
friction) and Strategy 4 (synthetic each-way)
constructions. Multi-leg back-against-back
constructions in markets with three or more
outcomes (racing win markets, soccer with draw,
tennis with retirement) — back-against-Betfair-back
hedging is restricted to two-outcome markets only.
Pure-Betfair work with no soft-book leg.
Multi-rung ladder hedging across multiple Betfair
price levels — feasible extension flagged in §7;
routed to a future arc (matching-layer scope).

**Equalisation target (locked Session 88):**
Net dollars-in-pocket equalised across the two
Betfair-side outcomes (lay wins vs lay loses; or
back wins vs back loses) at whatever level the
current price-and-stake combination supports. No
EV assumptions baked in; no free-bet conversion
rate folded into placement-time formulas. The
equalised outcome may be positive, zero, or
negative — the hedge math is indifferent. Adjusts
to match current Betfair price on drift, not to
preserve original target.

---

## §1 — Variables and conventions

### Soft-book leg (placed first; back-only; parameters fixed at placement time)

- **S_soft** — soft-book stake (dollars). The
  amount the operator wagers at the soft-book.
- **P_soft** — soft-book decimal odds at placement.
  E.g. a $100 bet at 3.5 odds returns $350 gross
  ($250 profit + $100 stake) on a win.

Soft-book lay does not exist as a soft-book
product — Australian books offer back bets only.
Operators wanting lay exposure go to Betfair.

### Soft-book leg outcome shapes (back only)

For a cash soft-book back bet:

- **Win-state payout** (selection wins):
  W_soft_win = S_soft × (P_soft − 1)
  (profit only — stake returned but not counted as
  profit)
- **Loss-state payout** (selection loses):
  W_soft_lose = −S_soft

For a free-bet soft-book back, the stake is never
put up in cash — operator gains profit on a win
and loses nothing on a loss:

- **Win-state payout:** W_soft_win = S_soft × (P_soft − 1)
- **Loss-state payout:** W_soft_lose = 0

Refunds (insurance promo triggers, bonus winnings
free-bet legs) enter as separate downstream
cycles per §5 — placement-time math treats each
cycle independently.

### Betfair leg (placed to hedge — two alternative constructions)

The Betfair leg opposes the soft-book back. Two
mathematically distinct constructions exist:

**Construction A — Betfair lay on the same
selection.** Common case. Operator backs Crows at
soft-book, lays Crows at Betfair. Works in any
market regardless of number of outcomes. §2
covers this construction.

**Construction B — Betfair back on the opposing
selection.** Restricted to two-outcome markets
(head-to-head with no draw: AFL/NRL/NBA/NFL match
winner, two-way tennis). Operator backs Crows at
soft-book, backs Port at Betfair. Economically
equivalent to Construction A as a hedge — operator
is betting "Crows don't win" via either shape —
but the staking math differs because back-Port
stake and lay-Crows stake are not the same
number even when constructed at equivalent prices.
§3 covers this construction.

The W4 tool accepts either input shape; operator
chooses based on which Betfair price is better at
the moment.

### Betfair leg variables

- **S_bf** — Betfair stake (dollars). The decision
  variable — solved for, given the soft-book
  parameters and current Betfair price. Sizing
  convention: backer's-stake-equivalent (Betfair
  UI/API convention; the lay liability is derived
  rather than specified directly).
- **P_bf** — Betfair decimal odds at placement (or
  at the moment of drift recomputation).
- **bet_type_bf** — `lay` (Construction A) or
  `back` (Construction B).
- **c** — Betfair commission rate on net winnings,
  decimal form. **Resolved dynamically from a
  working lookup at placement time** — never
  hardcoded as a state default. Commission varies
  by sport (sports vs racing) and by venue (e.g.
  Ipswich 4% vs Queensland statewide 8% for racing).
  Hardcoding a state rate where a lower
  venue-specific rate applies eats profit silently
  on every cycle. **W4 v1 scope — port v2's
  commission-lookup mechanism.** Locked behaviour;
  operator does not type c. The §6 worked examples
  show the lookup result flowing through (default
  c = 0.08 for Queensland thoroughbred WIN, with
  one Ipswich c = 0.04 example to make the
  per-venue resolution visible).

### Betfair leg outcome shapes

For a Betfair **lay** at lay odds P_bf with
backer's-stake-equivalent S_bf:

- **Lay wins** (selection loses on Betfair):
  W_bf_laywin = S_bf × (1 − c)
- **Lay loses** (selection wins on Betfair):
  W_bf_layloss = −S_bf × (P_bf − 1)
  (the liability — operator pays out the backer's
  winnings)

For a Betfair **back** at back odds P_bf with
stake S_bf:

- **Back wins** (selection wins on Betfair):
  W_bf_backwin = S_bf × (P_bf − 1) × (1 − c)
- **Back loses** (selection loses on Betfair):
  W_bf_backloss = −S_bf

### Equalisation condition

Operator's net dollars-in-pocket equals the sum
of soft-book leg payoff and Betfair leg payoff in
each Betfair-side outcome state. The equalisation
condition is:

    Net (when Betfair leg wins) = Net (when
    Betfair leg loses)

§2 solves this for S_bf in Construction A.
§3 solves it for S_bf in Construction B.
§4 handles drift logic. §5 handles refund and
free-bet cycle-shape concerns. §6 worked examples.
§7 edge cases, ship-blocker items, and future
extensions.

### Sign and rounding conventions

- All payouts in operator-relative dollars: positive
  = operator gains, negative = operator pays.
- Commission applied only to positive Betfair
  winnings (lay-wins or back-wins net).
  Multi-bet-per-market commission interaction
  named in §7.
- Stake rounding: Betfair minimum stake is $5 AUD
  for most market types; round S_bf up to two
  decimals at minimum, round to whole dollar at
  operator preference. Worked examples use
  two-decimal precision unless noted.
- Decimal odds throughout; no fractional odds
  conversion needed.

---

## §2 — Construction A: lay-against-soft-book-back

The common case. Operator backs selection at
soft-book; operator lays the same selection at
Betfair. Works in any market regardless of number
of outcomes. Two formulas — one for cash
soft-book stakes, one for free-bet soft-book
stakes — because the loss-state payoff differs.

**Operational note:** Strategy 1 Safety Net cycles
are rarely hedged in practice (the refund layer
plus volume covers the EV). Strategy 2
bonus-winnings sub-shape is sometimes hedged.
Strategy 2 price-uplift sub-shape is rarely
hedged. The math review covers all cases for
completeness; §6 worked examples cover one cash
and one free-bet case.

### §2.1 — Outcome states

**Selection-wins state** (soft-book back wins;
Betfair lay loses):

    Net_win = W_soft_win + W_bf_layloss
           = W_soft_win − S_bf × (P_bf − 1)

**Selection-loses state** (soft-book back loses;
Betfair lay wins):

    Net_lose = W_soft_lose + W_bf_laywin
            = W_soft_lose + S_bf × (1 − c)

The two formulas split based on whether the
soft-book stake is cash (stake recoverable, loss
returns full negative-stake payout) or a free
bet (stake never staked in cash, loss returns
zero).

### §2.2 — Cash soft-book stake derivation

For a cash soft-book back:

    W_soft_win = S_soft × (P_soft − 1)
    W_soft_lose = −S_soft

Setting Net_win = Net_lose:

    S_soft × (P_soft − 1) − S_bf × (P_bf − 1)
        = −S_soft + S_bf × (1 − c)

Collecting:

    S_soft × (P_soft − 1) + S_soft
        = S_bf × (1 − c) + S_bf × (P_bf − 1)
    S_soft × P_soft = S_bf × (P_bf − c)

Solving for S_bf:

    **S_bf = (S_soft × P_soft) / (P_bf − c)**       (cash)

The numerator is the soft-book gross return on a
win (stake × decimal odds). The denominator is
Betfair lay odds minus commission rate.

### §2.3 — Free-bet soft-book stake derivation

For a free-bet soft-book back:

    W_soft_win = S_soft × (P_soft − 1)
    W_soft_lose = 0

Setting Net_win = Net_lose:

    S_soft × (P_soft − 1) − S_bf × (P_bf − 1)
        = 0 + S_bf × (1 − c)
    S_soft × (P_soft − 1)
        = S_bf × (P_bf − 1) + S_bf × (1 − c)
    S_soft × (P_soft − 1) = S_bf × (P_bf − c)

Solving for S_bf:

    **S_bf = [S_soft × (P_soft − 1)] / (P_bf − c)**  (free bet)

Same denominator (P_bf − c). Numerator is the
soft-book profit-only return on a win (stake ×
(odds − 1)) — drops the stake-recovery component
because there's no cash stake to recover.

### §2.4 — Equalised outcome value

Substituting S_bf back into Net_lose gives the
operator's per-cycle dollars-in-pocket.

**Cash:**

    Net = −S_soft + S_bf × (1 − c)
        = S_soft × [P_soft × (1 − c) / (P_bf − c) − 1]
        = S_soft × [P_soft × (1 − c) − (P_bf − c)]
                  / (P_bf − c)

**Free bet:**

    Net = 0 + S_bf × (1 − c)
        = S_soft × (P_soft − 1) × (1 − c) / (P_bf − c)

The free-bet Net is always positive (assuming
P_soft > 1 and P_bf > c, which always hold on
real Betfair markets with min tick 1.01) — free
bets cannot lose money on a hedged cycle, only
gain less or more depending on the hedge price.
The cash Net can be positive, zero, or negative
depending on the relationship between P_soft,
P_bf, and c.

### §2.5 — Cash Net = 0 condition (perfect arb)

Setting Net = 0 in the cash formula:

    P_soft × (1 − c) − (P_bf − c) = 0
    P_soft × (1 − c) = P_bf − c

    **P_bf = P_soft × (1 − c) + c**

This is the breakeven Betfair lay odds for given
soft-book back odds and commission rate. Three
regimes follow:

- **P_bf < P_soft × (1 − c) + c** — Net > 0. Cycle
  is profit-locked. Strategy 2 price-uplift
  sub-shape (soft-book offers a price boost
  pushing P_soft above the no-arb threshold).
- **P_bf = P_soft × (1 − c) + c** — Net = 0. Pure
  arbitrage. Rare; usually evaporates before the
  second leg lands.
- **P_bf > P_soft × (1 − c) + c** — Net < 0.
  Operator pays a cycle cost to construct the
  position. Strategy 1 Safety Net case (cycle
  cost is the "premium" paid for the chance the
  refund triggers); general-turnover case
  (cycle cost is the "fee" paid for account-health
  betting activity).

Sanity check at c = 0: P_bf = P_soft. Perfect arb
at equal prices with no commission — consistent
with §2.7 sanity check 1.

### §2.6 — Liability and balance impact

Lay liability at Betfair is the dollars at risk
in the lay-loses state (selection wins on
Betfair):

    Liability = S_bf × (P_bf − 1)

The liability is what Betfair holds against the
operator's account balance until the market
settles. It is **not** the same as the lay
stake — the lay stake (S_bf) is the backer's-
stake-equivalent the operator collects if the lay
wins; the liability is what the operator pays out
if the lay loses.

At high Betfair odds, the liability is much
larger than the stake. Worked example: free bet
$100 at $20 soft-book, hedge at $21 Betfair,
c = 0.08:

    S_bf = (100 × 19) / (21 − 0.08) = $90.82
    Liability = 90.82 × 20 = $1,816.40

So a $100 free-bet hedge ties up ~$1,816 of
Betfair balance until settlement. **The W4 tool
must surface liability prominently** alongside
the stake and Net values in the placement modal,
so the balance impact is visible before
confirmation.

**Soft warning threshold:** W4 surfaces a warning
when liability exceeds a configurable threshold.
**Default $1,000.** Operator-configurable per
deployment. Warning text names the dollar amount
and the equalised Net so the operator can weigh
the balance impact against the cycle's
expected profit.

### §2.7 — Sanity checks on the formulas

**Sanity check 1 — cash, zero commission, equal odds.**
c = 0, P_bf = P_soft:
    S_bf = S_soft × P_soft / P_soft = S_soft
    Net = S_soft × [P_soft − P_soft] / P_soft = 0
Hedge stake equals soft-book stake, perfect arb
at zero commission. Correct.

**Sanity check 2 — free bet, zero commission, equal odds.**
c = 0, P_bf = P_soft:
    S_bf = S_soft × (P_soft − 1) / P_soft
    Net = S_soft × (P_soft − 1) × 1 / P_soft
        = S_soft × (P_soft − 1) / P_soft
For S_soft = 100, P_soft = 3.0:
    S_bf = 100 × 2 / 3 = $66.67
    Net = 100 × 2 / 3 = $66.67
Free bet at $100 stake, $3 odds, hedged at $3
zero-commission produces a $66.67 equalised
return — consistent with the ~67% conversion rate
folklore for free bets at moderate odds.
Correct.

**Sanity check 3 — soft-book odds approach 1.**
P_soft → 1 (selection priced as a near-certainty
at soft-book):
- Cash: numerator → S_soft × 1 = S_soft;
  S_bf → S_soft / (P_bf − c).
- Free bet: numerator → 0; S_bf → 0.
Free-bet Sanity 3 is correct: a free bet at
near-certain odds returns near-zero profit, so
no hedge is needed. Cash Sanity 3 is correct: a
cash bet at near-certain odds still requires a
small hedge proportional to the Betfair liability.
Both correct.


---

## §3 — Construction B: back-against-Betfair-back

The two-outcome alternative. Operator backs Crows
at soft-book; operator backs Port at Betfair.
Restricted to two-outcome markets (head-to-head
with no draw: AFL/NRL/NBA/NFL match winner,
two-way tennis). Used when the Betfair back price
on the opposing selection is more attractive than
the Betfair lay price on the original selection.

**Operational note:** This construction is used
rarely (operator's word: "occasionally") relative
to Construction A. Math review covers it for
completeness; W4 tool needs both because operator
chooses based on which side of the Betfair book
shows the better price at placement time.

### §3.1 — Outcome states

In a two-outcome market, "Crows lose" and "Port
wins" are the same event. So the soft-book's
lose-state and the Betfair-back's win-state line
up.

**Original-selection-wins state** (Crows win;
soft-book back wins; Betfair back on Port loses):

    Net_win = W_soft_win + W_bf_backloss
           = W_soft_win − S_bf

**Original-selection-loses state** (Port wins;
soft-book back loses; Betfair back on Port wins):

    Net_lose = W_soft_lose + W_bf_backwin
            = W_soft_lose + S_bf × (P_bf − 1) × (1 − c)

Note the asymmetry vs Construction A — the
Betfair-back-loses case has no commission
applied (commission applies only to winnings),
while the Betfair-back-wins case applies
commission to the gross profit S_bf × (P_bf − 1).

### §3.2 — Cash soft-book stake derivation

For a cash soft-book back:

    W_soft_win = S_soft × (P_soft − 1)
    W_soft_lose = −S_soft

Setting Net_win = Net_lose:

    S_soft × (P_soft − 1) − S_bf
        = −S_soft + S_bf × (P_bf − 1) × (1 − c)

Collecting:

    S_soft × (P_soft − 1) + S_soft
        = S_bf × (P_bf − 1) × (1 − c) + S_bf
    S_soft × P_soft
        = S_bf × [(P_bf − 1) × (1 − c) + 1]

Solving for S_bf:

    **S_bf = (S_soft × P_soft) / [(P_bf − 1) × (1 − c) + 1]**       (cash)

The numerator matches Construction A cash. The
denominator differs — Construction A uses
(P_bf − c); Construction B uses
[(P_bf − 1) × (1 − c) + 1]. Algebraically these
are not equivalent except at the no-commission
limit (c = 0, both reduce to P_bf).

### §3.3 — Free-bet soft-book stake derivation

For a free-bet soft-book back:

    W_soft_win = S_soft × (P_soft − 1)
    W_soft_lose = 0

Setting Net_win = Net_lose:

    S_soft × (P_soft − 1) − S_bf
        = 0 + S_bf × (P_bf − 1) × (1 − c)
    S_soft × (P_soft − 1)
        = S_bf × [(P_bf − 1) × (1 − c) + 1]

Solving for S_bf:

    **S_bf = [S_soft × (P_soft − 1)] / [(P_bf − 1) × (1 − c) + 1]**  (free bet)

### §3.4 — Equalised outcome value

**Cash:**

    Net = −S_soft + S_bf × (P_bf − 1) × (1 − c)
        = S_soft × {[P_soft × (P_bf − 1) × (1 − c)]
                    / [(P_bf − 1) × (1 − c) + 1] − 1}

**Free bet:**

    Net = 0 + S_bf × (P_bf − 1) × (1 − c)
        = S_soft × (P_soft − 1) × (P_bf − 1) × (1 − c)
                  / [(P_bf − 1) × (1 − c) + 1]

### §3.5 — Liability and balance impact

For Construction B, Betfair holds the back stake
S_bf (not a separate liability — back bet stake
is the operator's at-risk amount). Balance impact
equals the back stake itself:

    Balance impact (Construction B) = S_bf

This is materially smaller than Construction A's
liability for the same hedge, because
S_bf < S_bf × (P_bf − 1) whenever P_bf > 2. At
P_bf < 2, the back stake exceeds what the
equivalent lay-side liability would be, but the
difference is small.

The W4 tool surfaces balance impact for both
constructions; the soft warning threshold (default
$1,000) applies to the Construction B back stake
the same way it applies to the Construction A
liability. The operationally meaningful quantity
is "dollars tied up in this hedge" regardless of
which side of the book the hedge sits on.

### §3.6 — Construction A vs Construction B equivalence

In a perfectly-priced two-outcome market with no
overround and zero commission, the lay-Crows
price and the back-Port price satisfy:

    P_lay_crows = P_back_port / (P_back_port − 1)

(or equivalently, 1/P_lay_crows + 1/P_back_port = 1.)

In real Betfair markets the two prices are not
identical because of overround (Betfair's spread
across the two sides). And even at "equivalent"
prices, the two constructions produce slightly
different Net values because their formulas use
different denominators — Construction A uses
(P_bf − c); Construction B uses
[(P_bf − 1) × (1 − c) + 1]. These coincide only
at c = 0.

Combined effect: operator looking at the same
Betfair market sees lay-Crows at one price and
back-Port at another, computes the hedge through
Construction A vs Construction B against the same
soft-book back, and gets two slightly different
Net values. Operator should pick the construction
with the better Net for that specific moment, not
assume they're interchangeable.

W4 tool can surface both Net values when both
sides of the Betfair book are visible — operator
picks the better-Net side. This is a §7 future-
extension item; v1 just executes whichever
construction the operator selects.

### §3.7 — Sanity check on Construction B

**Sanity check — cash, zero commission, equivalent prices.**
For Crows at P_soft = 2.0 (soft-book) and Port at
P_bf = 2.0 (Betfair back, equivalent two-outcome
mid-price), c = 0:

    S_bf = (S_soft × 2.0) / [(2.0 − 1) × 1 + 1]
         = 2 × S_soft / 2 = S_soft
    Net = S_soft × {[2.0 × 1 × 1] / 2 − 1}
        = S_soft × (1 − 1) = 0

Perfect arb at equivalent two-outcome prices with
no commission — operator stakes equal amounts on
both sides, breaks even. Correct.


---

## §4 — Modal mechanics: live price and custom price

The W4 placement modal exposes two simultaneous
ways for the operator to set the Betfair price
that drives stake computation. Both run in
tandem in the same modal — operator chooses which
to use at confirm-click. The math from §2 and §3
is unchanged; what changes is how the operator
arrives at P_bf.

### §4.1 — Live price mechanism

The modal subscribes to Betfair Streaming for the
target market (already-running subscription per
W3 substrate; no fresh API connection at modal
open). Live updates drive four displayed values
that recompute together:

- **P_bf_live** — current Betfair price at the
  best rung on the operator's chosen side (lay
  for Construction A, back for Construction B).
- **S_bf_live** — Betfair stake auto-computed
  against P_bf_live via the §2 / §3 formula
  matching the soft-book stake type (cash or free
  bet).
- **Liability_live** — derived from S_bf_live and
  P_bf_live per §2.6 (Construction A) or §3.5
  (Construction B).
- **Net_live** — equalised cycle outcome at the
  current price, per §2.4 / §3.4.

All four numbers update on every Streaming tick.
Operator watches them move and decides when to
place.

If operator confirms placement using the live
price, the placed order uses P_bf_live at
confirm-click as the requested price, with
Betfair's `priceLimit` parameter set to that
price (place at requested price or better; do
not match worse). Order fills immediately if
liquidity at that price-or-better exists; sits
unmatched as a limit order otherwise.

### §4.2 — Custom price mechanism

The modal exposes a custom-price input alongside
the live-price display. Operator types a target
price (e.g. 1.98 when live shows 2.00). The
custom price drives an independent set of four
values:

- **P_bf_custom** — operator-typed price.
- **S_bf_custom** — Betfair stake auto-computed
  against P_bf_custom.
- **Liability_custom** — derived from S_bf_custom
  and P_bf_custom.
- **Net_custom** — equalised cycle outcome at
  P_bf_custom.

These four update as the operator types or as
P_bf_custom is otherwise modified (e.g. clicking
+/- increment buttons against current value).

If operator confirms placement using the custom
price, the placed order uses P_bf_custom as the
requested price with `priceLimit` set to that
value. Same matching semantics as live-price
placement — fills immediately at requested-or-
better, sits unmatched otherwise.

### §4.3 — Match-availability surfacing

Whichever price the operator is about to confirm
(live or custom), the modal surfaces a
match-availability indicator computed from the
current Betfair ladder against the chosen stake
and price. Three states:

- **Fully matched at placement** — operator's
  S_bf at chosen price is ≤ available liquidity
  at that price-or-better. Order fills
  immediately at confirmation.
  Display: "Order will match immediately at $S_bf."

- **Partially matched at placement** — operator's
  S_bf exceeds available liquidity at that
  price-or-better. Indicator shows the split.
  Display: "$Y of $S_bf will match immediately;
  remaining $(S_bf − Y) sits unmatched at chosen
  price." Operator may also see this as a
  percentage. Operator confirms knowing the
  split.

- **Fully unmatched at placement** — operator's
  chosen price is past the current best price
  on the operator's side (e.g. lay at 1.98 when
  best lay is 2.00). No matching at placement.
  Display: "No matching at placement; full $S_bf
  sits as limit order awaiting market movement."
  Operator confirms knowing it's a parked order.

Match-availability is a Betfair ladder read
against the same Streaming subscription data
already in the modal. No extra API call.
Indicator updates live as ladder rungs and
liquidity move.

### §4.4 — Persistence type

Modal exposes three persistence-type options
on every placement, both Construction A and
Construction B, all market types:

- **PERSIST** (default) — order survives market
  suspension (e.g. in-play turn for sports;
  jump for racing); remains live until match or
  settlement.
- **LAPSE** — order cancels at suspension;
  does not survive in-play turn.
- **MARKET_ON_CLOSE (MOC)** — order converts to
  Betfair SP at suspension if unmatched.
  Available across all markets where Betfair
  exposes the option; operationally most common
  for greyhound markets where suspension at jump
  is total.

Default is PERSIST for both back and lay bet
types across all market types. Operator may
change per placement.

### §4.5 — Placement-latency and `priceLimit`

Between confirm-click and Betfair receiving the
order, the price may move. Betfair's `priceLimit`
parameter on `placeOrders` handles this:

- Order specifies "place at requested price or
  better, do not match worse."
- If market moves favourable in the latency
  window: order matches at the new better price.
- If market moves unfavourable in the latency
  window: order does not match worse than
  requested price; sits as an unmatched limit
  order at the requested price.

This collapses the favourable-vs-unfavourable
"drift" handling from earlier W4 design framings
(per Session 87 Round 9 substrate). The operator
chose a price (live or custom); `priceLimit`
ensures the placed order respects that choice
regardless of latency-window movement. There is
no envelope, no prompt, no two-route choice —
the limit-order semantics handle it.

The matched price is reported in the post-
placement result envelope. If `priceLimit`
allowed a better match (favourable movement),
the operator sees the better match. If
unfavourable movement left the order unmatched,
the operator sees the unmatched state and may
let it sit, modify it, or cancel it.

### §4.6 — Cancel / replace and `adjust_hedge`

The combined `adjust_hedge` workflow from Session
87 substrate executes cancel-then-place as two
sequential Betfair API calls. The same modal
mechanics apply to the place leg — operator
picks live-price or custom-price, modal recomputes
S_bf and shows match-availability, placement
uses `priceLimit`.

Drift between cancel response and place request
is handled by the same `priceLimit` mechanism on
the place leg — no separate drift-detection
logic needed. The ~50–200ms uncovered window
between cancel-success and place-request is a
liquidity-gap concern (the operator briefly has
no Betfair-side hedge during that window), not
a drift concern.

Named failure modes from Session 87 substrate
(`cancel_succeeded_place_failed`,
`cancel_failed_place_not_attempted`, etc.) surface
in the post-action result envelope.

### §4.7 — Sanity-checking from operator visibility

The math layer applies no sanity bounds on
P_bf_custom (operator may type any value). The
modal's live displays of liability and Net mean
nonsensical custom prices surface visually:

- A typed price below current market or with
  excessive liability shows an obviously-wrong
  liability number ("$100,000 liability on a
  $50 hedge" is operator-visible).
- A typed price producing an obviously-wrong Net
  ("equalised outcome: −$8,000 on a $20 free
  bet hedge") is operator-visible.

UI may emphasise these (visual highlight, color,
font weight) to draw operator attention without
blocking placement. Math layer trusts the
displayed numbers to do the sanity-checking work
through operator visibility. Hard math-layer
bounds checking is not in v1 scope.

### §4.8 — Substrate revision note

Session 87 Round 9 substrate captured a
"PriceDriftEnvelope" with two retry routes (hold
line / accept drift) as the unfavourable-drift
handling mechanism. This math review (Session 88)
supersedes that mechanism. The directional
thinking from Session 87 still holds — operator
controls which price they place at — but the
mechanism is simpler: live-price-and-custom-price
modal mechanics plus Betfair `priceLimit`
enforcement at the API. No envelope, no prompt,
no two-route choice. When W4 brief drafting
resumes, the §4 mechanics here are the locked
substrate; the Session 87 envelope shape does not
carry forward.


---

## §5 — Refund and free-bet cycle shapes

The math in §2 and §3 treats every hedged bet as
an independent placement-time problem — given a
soft-book stake and a Betfair price, compute the
hedge stake. This section names the cycle-shape
concerns that sit *around* the placement-time
math and the synthesis that produces the inputs
the math runs against.

The standing analysis convention from
`standing_instructions.md` Cat 4: any bet whose
outcome drives downstream behaviour (free bet
trigger, bonus-back, refund, cashback) is
analysed as a single cycle, never in isolation.
Placement-time math runs per leg; cycle-level
P&L tracking aggregates legs into one cycle.

### §5.1 — Strategy 1 (Safety Net) cycle shape

A Strategy 1 cycle has up to two legs:

1. **Original cash bet at soft-book** on an
   insurance-promo market. Three possible
   outcomes:
   - **Wins.** Profit S_soft × (P_soft − 1).
     Cycle ends.
   - **Loses without triggering refund.** Loss
     of S_soft. Cycle ends.
   - **Loses and triggers refund.** Refund
     typically issued as a free bet of original
     stake. Cycle continues to leg 2.

   Optionally hedged with Betfair (rare per
   operator's note) — hedge sits within leg 1,
   not as a separate leg.

2. **Refund free bet (only if leg 1 triggered
   it).** Free bet placed on a market of operator's
   choosing, optionally hedged with Betfair via
   the §2.3 free-bet formula. Cycle ends after
   the free bet's outcome regardless of result —
   no further promo triggers downstream.

Cycle membership ties leg 1 and leg 2 together
for analytics; placement-time math runs
independently on each.

### §5.2 — Strategy 2 sub-shape 1: boosted odds

Single-leg cash bet at soft-book at boosted odds.
Soft-book lists $2 but offers $2.30; operator
places at $2.30. Mathematically identical to a
regular cash bet at the boosted odds — no special
handling, no follow-on bet, no synthesis. The
§2.2 cash formula runs against P_soft = boosted
odds. Cycle is the single bet.

**v3 UX simplification:** operator enters the
boosted odds directly on the racing screen as
P_soft. No separate input for original-vs-boosted
delta. v2 captured the delta but the extra manual
step was operator-cumbersome with insufficient
analytical value; v3 drops the capture in favour
of streamlined entry.

### §5.3 — Strategy 2 sub-shape 2: bonus winnings as free bet

Two-leg cycle. Original cash bet at soft-book; if
it wins, a free bet matching winnings (up to a
cap) triggers. Free bet runs as a separate cycle
leg with its own potential Betfair hedge.

**Effective-odds synthesis.** The W4 tool
synthesises `P_soft_effective` automatically from
the promotional fields the operator entered on
the racing screen (promo type, free-bet cap,
conversion rate). The synthesis bakes the
expected free-bet bonus into the soft-book leg's
effective odds:

    P_soft_effective = P_soft_actual
                     + (free_bet_cap × conversion_rate) / S_soft

The placement-time math runs against
P_soft_effective, not P_soft_actual. The modal
displays both values for operator reference —
P_soft_actual is the soft-book's headline number;
P_soft_effective is the inflated odds used in
hedge-stake computation.

The synthesis allows hedging at an effective
arb when the soft-book's promotional structure
inflates the implied odds past the Betfair lay
breakeven. Without the synthesis, the
placement-time math would underprice the
soft-book leg and produce a worse equalised Net.

**Default conversion rate: 65%.** Operator-
configurable; downgraded from the historical 70%
folklore based on operator's observed
realisation rate. Conversion rate enters the
synthesis as a known parameter, not as an
assumption — operator has chosen a working value
that reflects how their cycles actually convert.
Analytics post-cycle measure the realised rate
and inform future tuning.

**Optimal stake to maximise promo.** Free-bet
caps mean over-staking produces no extra free
bet. Optimal stake is:

    S_optimal = free_bet_cap / (P_soft_actual − 1)
    rounded to nearest $5

The W4 tool surfaces S_optimal both on the racing
screen and in the modal. Operator may stake at
S_optimal or another amount; if stake exceeds
S_optimal the promo is under-utilised but the bet
is otherwise valid.

**Cycle continuation: triggered free bet =
Strategy 1 free-bet leg.** When the original bet
wins and triggers the free bet, the resulting
free bet is operationally and mathematically
identical to a Strategy 1 refund free bet. Both
are free bets placed on a chosen market with
optional Betfair hedging via the §2.3 free-bet
formula. Cycle membership ties the triggered
free bet to its originating bet; the math doesn't
care which strategy spawned it.

### §5.4 — Strategy 2 sub-shape 3: bonus winnings as cash

Single-leg cash bet at soft-book with cash bonus
on win. If original bet wins, win-state payout
becomes:

    W_soft_win = S_soft × (P_soft_actual − 1)
               + bonus_cash_cap

(capped at bonus_cash_cap; payout above the cap
is just the standard win profit).

**Effective-odds synthesis.** Same shape as
sub-shape 2 but no conversion rate (cash, not
free bet):

    P_soft_effective = P_soft_actual
                     + bonus_cash_cap / S_soft

Placement-time math runs against P_soft_effective.

**Optimal stake.** Same shape:

    S_optimal = bonus_cash_cap / (P_soft_actual − 1)
    rounded to nearest $5

**No follow-on bet.** Cash bonus is paid out
directly; cycle ends at the original bet's
settlement.

### §5.5 — Strategy 2 price-uplift

Top Fluc, Best of Best, Best Tote and similar
price-uplift promos. Single-leg cash bet at
soft-book; soft-book pays at the higher of
advertised / closing fluc / tote. Mathematically
straightforward (single-leg cash bet at the
uplift price), but the data sources for
identifying which markets show the best
uplift across sources need work outside DR-029
and W4 scope.

**Deferred to later refinement.** v3 build proper
ships W4 without explicit price-uplift handling;
operator places these as regular cash bets with
the soft-book's headline odds. Future refinement
extends the synthesis when data sources are
sorted.

### §5.6 — General turnover cycle shape

Single-leg cash bet placed for account-health
purposes. No promo trigger, no follow-on bet.
Placement-time math runs once (cash formula).
Net is typically negative (turnover bets are
expected to lose; the equalised hedge limits the
size of the loss).

Cycle membership tracks the turnover purpose
alongside P&L for analytics.

### §5.7 — Cycle-linkage at logging time

The W4 placement-time math is cycle-agnostic.
Cycle linkage — recording that placement X is
the hedge leg of cycle Y, or that placement Z is
the triggered free bet from cycle W — happens at
logging time, not at placement time.

This is the Session 87 architectural-extension
flag (Betfair as canonical source extending to
all bet records, including soft-book bets logged
manually). Soft-book bets log with Betfair-side
identifiers (`betfair_market_id`,
`betfair_selection_id`) as the canonical join key;
hedge legs reference the same identifiers; cycle
membership is recoverable by join.

Formalisation deferred to before W4.1 (when
soft-book entry establishes the cycle linkage at
logging time), not before W4. Math review flags
it for completeness; full architectural
specification belongs in `architecture.md` §D12
extension or new DR (DR-032 candidate).

### §5.8 — Free-bet conversion rate as both parameter and analytics

The 65% default conversion rate enters
placement-time math via the §5.3 synthesis. It
is a *parameter* the operator has chosen based
on observed realisation, not a baked-in
assumption. Operator-configurable in W4.

Post-cycle analytics measure the **realised**
free-bet conversion rate from actual outcomes:

    realised_rate = total_realised_free_bet_value
                  / total_face_value_of_hedge-attempted_free_bets

The denominator is intent-filtered: the
analytical layer excludes free bets where the
operator intentionally did not hedge, where
aggressive-price limit orders missed, or where
the free bet lapsed for operational reasons. The
intent-capture substrate from earlier sessions
provides the filter mechanism.

If realised_rate diverges from the configured
parameter over volume, operator updates the
parameter. This is a feedback loop, not a
static assumption.

**Analytics belongs to post-DR-029 work.** §5.8
flags the framing for completeness; the actual
analytics implementation lives in the analytical
layer build (post-cutover). v3 W4 ships with
the parameter; analytics layer adds the
realised-rate measurement later.


---

## §6 — Worked numerical examples

§6 demonstrates the §2 Construction A formulas
operationally with realistic numbers. Two
examples: §6.1 covers a cash hedge on a general
turnover bet; §6.2 covers a free-bet hedge as
the refund leg of a Strategy 1 Safety Net cycle.

The base-placement math, the live-price
recompute mechanism, and the custom-price input
mechanism (all locked in §4) are demonstrated in
§6.1. §6.2 uses the same mechanics with a free
bet to show the formula difference and the
liability behaviour at higher Betfair odds.

Numbers chosen to produce coherent operational
shapes: §6.1 lands in the cycle-cost regime (Net
negative, normal for general turnover under 8%
commission), §6.2 lands in the profit-locked
regime (Net positive, normal for Strategy 1
free-bet legs because the original stake is not
at risk).

### §6.1 — Cash hedge, general turnover

**Scenario.** The operator places a $50 win bet
on a Queensland thoroughbred at $3.00 with a
soft-book (no promo layer — clean turnover for
account health, Strategy 4-shaped). Betfair lay
on the same selection sits at $3.10 at modal
open. The operator decides to hedge.

**Inputs:**

    S_soft  = $50 (soft-book back stake)
    P_soft  = 3.00 (soft-book back odds)
    P_bf    = 3.10 (Betfair lay odds, opening price)
    c       = 0.08 (Queensland thoroughbred WIN
                    commission, resolved
                    dynamically per §1)
    bet_type_bf = lay (Construction A)

The 8% commission is **not typed by the
operator** — the W4 commission lookup resolves
it from the Betfair venue / sport at modal open.
For a Queensland WIN market on a thoroughbred
race, the lookup returns 8%. This is the same
mechanism v2 uses today; W4 ports it.

**Base placement math (P_bf = 3.10).**

Apply the Construction A cash formula from §2.2:

    S_bf = (S_soft × P_soft) / (P_bf − c)
         = (50 × 3.00) / (3.10 − 0.08)
         = 150 / 3.02
         = $49.67

The Betfair lay stake is $49.67 (backer's-stake-
equivalent). Liability follows from §2.6:

    Liability = S_bf × (P_bf − 1)
              = 49.67 × 2.10
              = $104.30

The operator's Betfair balance is reduced by
$104.30 until the market settles. Below the
$1,000 default soft warning threshold — no
warning surfaces.

**Outcome math.** Two outcomes, equalised:

*Outcome 1 — soft-book runner wins (Betfair lay
loses).*

    Soft-book net win   = S_soft × (P_soft − 1)
                        = 50 × 2.00
                        = +$100.00
    Betfair lay loss    = −Liability
                        = −$104.30
    Net                 = +100.00 − 104.30
                        = −$4.30

*Outcome 2 — soft-book runner loses (Betfair lay
wins).*

    Soft-book net loss  = −S_soft
                        = −$50.00
    Betfair lay win     = S_bf × (1 − c)
                        = 49.67 × 0.92
                        = +$45.70
    Net                 = −50.00 + 45.70
                        = −$4.30

**Both outcomes equalise at −$4.30.** This is
the cycle-cost regime per §2.4: P_soft × (1 − c)
= 2.76 is less than P_bf − c = 3.02, so the
hedge locks in a small certain loss across both
outcomes. Operator-facing reading: $4.30 of
turnover-cost-of-doing-business for a clean $50
bet that no longer carries risk.

For general turnover this is often acceptable —
the bet is shaped for account health, not edge.
For promo-driven cycles (Strategy 1 / Strategy
2), the math layer is the same but the soft-book
side carries the EV that justifies the cycle
cost. Math review §2 covers the formula; cycle-
shape decisions are operational territory.

**Net=0 break-even reference.** From §2.4:

    P_bf_breakeven = P_soft × (1 − c) + c
                   = 3.00 × 0.92 + 0.08
                   = 2.84

If Betfair tightened to lay at 2.84, the cash
hedge would equalise at exactly zero (free
hedge — a cost-neutral risk-strip). Below 2.84
flips the cycle into the profit-locked regime
(arb).

**Live-price recompute scenario.** Modal sits
open at base placement; operator has not
clicked confirm yet. Betfair Streaming pushes
a price update — the lay price tightens from
3.10 to 3.05 (favourable drift; tighter lay is
better for a Construction A hedge).

The §4 live-price mechanism recomputes on the
new price:

    P_bf_new = 3.05
    S_bf_new = (50 × 3.00) / (3.05 − 0.08)
             = 150 / 2.97
             = $50.51
    Liability_new = 50.51 × 2.05
                  = $103.54
    Net_new = +100.00 − 103.54  (Outcome 1)
            = −50.00 + 50.51 × 0.92  (Outcome 2)
            = −$3.54

The modal display updates: stake bumps from
$49.67 to $50.51; liability drops from $104.30
to $103.54; Net improves from −$4.30 to −$3.54
(a $0.77 improvement). Operator sees the new
numbers and can confirm or wait for further
movement.

**Critical detail — `priceLimit` protection.**
Per §4.4, the order is placed with a
`priceLimit` parameter equal to the price the
operator confirmed at. If the operator clicks
confirm at 3.05 and the matching price is 3.05
or better, Betfair fills. If the price has moved
back to 3.07 by the time the order arrives,
Betfair refuses to match (the lay would be
worse than the operator's intent). The
favourable-drift handling collapses cleanly:
the operator confirms at the displayed price,
and Betfair enforces no-worse-than at the API
layer.

**Custom-price scenario.** Same modal still
open. Operator decides to widen the lay target
to 3.15 (deliberately laying at a worse-for-
themselves price — sometimes done to maximise
fill probability when liquidity is thin and the
operator wants the hedge filled fast).

Operator types 3.15 in the custom-price input.
The modal recomputes off the typed price (the
live-price mechanism is suspended for the typed
input per §4.5):

    P_bf_custom = 3.15
    S_bf_custom = (50 × 3.00) / (3.15 − 0.08)
                = 150 / 3.07
                = $48.86
    Liability_custom = 48.86 × 2.15
                     = $105.05
    Net_custom = +100.00 − 105.05
               = −$5.05

Net worsens from −$4.30 to −$5.05 (a $0.75 cost
to widen). Operator sees the cost, decides
whether to confirm. If confirmed, the order
ships with `priceLimit=3.15` — Betfair will
match at 3.15 or better (i.e. anything ≤ 3.15
on the lay book).

**What §6.1 demonstrates.** The cash formula
runs cleanly across base placement, favourable
live-price drift, and operator-typed custom
price. All three scenarios use the same formula
(`S_bf = (S_soft × P_soft) / (P_bf − c)`) — the
modal mechanics swap which P_bf drives the
recompute. The cycle-cost regime is visible in
the math; the operator's interpretation
(acceptable cost for clean turnover) is
operational territory.

The §1 dynamic-commission framing is visible
here too — the 8% rate didn't appear because
the operator typed it; it appeared because the
W4 lookup resolved a Queensland thoroughbred
WIN market to 8% at modal open. If the same
$50 bet had been placed on an Ipswich
thoroughbred, the lookup would have returned
4% (per §1) and the math below would shift
favourably:

    S_bf @ Ipswich = (50 × 3.00) / (3.10 − 0.04)
                   = 150 / 3.06
                   = $49.02
    Liability      = 49.02 × 2.10 = $102.94
    Net            = +100 − 102.94 = −$2.94

**$1.36 better Net at Ipswich than Queensland**
on the same bet — a direct consequence of the
per-venue lookup. Hardcoding 8% across the
board would silently over-pay commission on
Ipswich cycles. The dynamic lookup is locked
v1 scope precisely because this gap compounds
across volume.


### §6.2 — Free-bet hedge, Strategy 1 Safety Net refund leg

**Scenario.** The operator placed a $100 cash
bet on a Queensland thoroughbred yesterday
under a Strategy 1 Safety Net promo (refund as
free bet if runner finishes 2nd, 3rd, or 4th).
Runner finished 3rd; the refund triggered as a
$100 free bet. Today, the operator places that
free bet on a different runner — $100 free bet
at $4.00 soft-book — and decides to hedge it on
Betfair to lock in the realised conversion. The
free-bet leg is the unit being analysed here;
the original cash bet that triggered the refund
sat in §5.1's cycle framing.

**Key difference from §6.1.** A free bet pays
**winnings only**, not stake-plus-winnings. The
soft-book "stake" of $100 is held by the book
and never reaches the operator's pocket. This
shifts the formula: substitute (P_soft − 1) for
P_soft in the Construction A cash formula
(derivation in §2.3).

**Inputs:**

    S_soft  = $100 (soft-book free-bet face value)
    P_soft  = 4.00 (soft-book back odds)
    P_bf    = 4.20 (Betfair lay odds at modal open)
    c       = 0.08 (Queensland thoroughbred WIN
                    commission, resolved
                    dynamically per §1)
    bet_type_bf = lay (Construction A)

**Base placement math.**

Apply the Construction A free-bet formula from
§2.3:

    S_bf = [S_soft × (P_soft − 1)] / (P_bf − c)
         = [100 × (4.00 − 1)] / (4.20 − 0.08)
         = (100 × 3) / 4.12
         = 300 / 4.12
         = $72.82

Liability:

    Liability = S_bf × (P_bf − 1)
              = 72.82 × 3.20
              = $233.01

The operator's Betfair balance is reduced by
$233.01 until settlement. Below the $1,000
default soft warning threshold — no warning
surfaces.

**Outcome math.**

*Outcome 1 — free-bet runner wins (Betfair lay
loses).*

    Free-bet net win    = S_soft × (P_soft − 1)
                        = 100 × 3
                        = +$300.00
                          (winnings only — no
                           stake returned)
    Betfair lay loss    = −Liability
                        = −$233.01
    Net                 = +300.00 − 233.01
                        = +$66.99

*Outcome 2 — free-bet runner loses (Betfair lay
wins).*

    Free-bet net loss   = $0
                          (no cash at risk —
                           the free bet's "stake"
                           was never the
                           operator's money)
    Betfair lay win     = S_bf × (1 − c)
                        = 72.82 × 0.92
                        = +$66.99
    Net                 = 0 + 66.99
                        = +$66.99

**Both outcomes equalise at +$66.99.** This is
the profit-locked regime per §2.4 — Net is
positive across both outcomes because the soft-
book side carries free-bet upside with no
downside exposure. The hedge converts the
all-or-nothing free bet into a guaranteed
$66.99 cash outcome.

**Realised conversion rate.** $66.99 locked
from $100 free-bet face value = **66.99%
realised conversion**. This is what Strategy 1's
post-settlement free-bet realisation actually
looks like at this price/commission combination.

The 65% default conversion rate parameter (§5.7)
is the operator's *expected* realisation across
volume — used in placement-time effective-odds
synthesis (§5.3) and EV reasoning. The 66.99%
*realised* rate from this specific cycle is one
data point that the analytical layer (post-DR-
029 work) will aggregate into a true realised-
rate measurement over volume. Realised drifts
above or below 65% by price, commission, and
hedge timing.

**Why no live-price / custom-price walk-
through here.** §6.1 demonstrated both modal
mechanisms cleanly. The same mechanisms apply
to free-bet placements without modification —
live-price drift recomputes S_bf via the §2.3
formula instead of §2.2; custom-price input
recomputes the same way. §4.7 covers the modal
behaviour in full. §6.2 focuses on what's
*different* about the free-bet case: the
formula numerator and the operational meaning
of the result.

**Liability behaviour at higher Betfair odds.**

The $233 liability above sits well below the
soft warning threshold. Free-bet hedges at
higher odds tie up substantially more Betfair
balance — same formula, larger numbers. Worked
example for contrast: the same $100 free bet at
$20 soft-book / $21 Betfair lay (a long-odds
free-bet leg, common when Strategy 1's
underlying runner had been priced as a longshot):

    S_bf = (100 × 19) / (21 − 0.08)
         = 1900 / 20.92
         = $90.82
    Liability = 90.82 × 20
              = $1,816.44
    Net (both outcomes) = $83.56
    Realised conversion = 83.56%

**The $1,816 liability triggers the soft warning
at the $1,000 default threshold.** The W4 modal
surfaces a warning before the operator confirms
— naming the liability dollar amount and the
equalised Net so the operator can decide whether
the cycle's expected conversion is worth tying
up that much Betfair balance.

Two operational observations from this contrast:

- Higher-odds free-bet hedges **convert better**
  (83.56% vs 66.99% at this commission), which
  is intuitive — the larger spread between
  P_soft and P_bf has more room to absorb
  commission.
- Higher-odds free-bet hedges **tie up
  substantially more balance** ($1,816 vs $233).
  Operator-facing reading: a $100 free-bet
  refund from a longshot losing leg wants ~$1.8k
  of free Betfair balance to hedge cleanly.
  Sizing across multiple concurrent free-bet
  refunds is operational territory; the warning
  threshold makes the per-cycle balance impact
  visible.

**What §6.2 demonstrates.** The free-bet formula
runs cleanly across moderate and high-odds
cases. Profit-locked regime is universal for
free-bet hedges (the soft-book side has no
downside). Realised conversion rate is the
locked cash outcome divided by free-bet face
value — a per-cycle measurement that aggregates
into the analytical layer's realised-rate
analytics. Liability scales with P_bf and
becomes the primary operational constraint at
long odds; the soft warning surfaces this at the
modal layer.


---

## §7 — Edge cases and future extensions

§7 consolidates items captured across §1–§6
into a single forward-looking list. Two
categories: **edge cases** that W4 v1 does not
fully resolve but accepts as known limitations,
and **future extensions** that sit outside W4
scope but flow naturally from the math review
substrate.

The dynamic commission lookup is **not in this
list** — per §1, it is locked W4 v1 scope (W4
ports v2's commission-lookup mechanism). §6.1's
Ipswich-vs-Queensland contrast demonstrates the
operational impact.

### §7.1 — Multi-bet-per-market commission interaction

**Status:** edge case; W4 v1 accepts the
limitation.

Betfair commission accrues at the market level,
not the bet level. If the operator places two
or more bets on the same Betfair market — for
example, hedging two different soft-book legs
against the same race — commission is computed
on the *net* market position, not on each bet
individually.

The §2 formulas assume commission applies to
each hedge in isolation (`c × winnings` per
bet). For single-hedge placements this is
exact. For multi-bet-per-market placements,
the formulas are slightly conservative — the
true post-commission Net is marginally better
than the formula predicts, because losses on
one bet offset commission base on the other.

**W4 v1 behaviour:** treat each hedge in
isolation. Acceptable because (a) most
operational placements are single-hedge, (b)
the conservative bias is in the operator's
favour (actual outcomes match or beat formula
predictions), (c) modelling the exact multi-bet
interaction adds complexity to the modal layer
without materially improving placement
decisions.

**Future extension:** if the analytical layer
identifies systematic multi-bet-per-market
placements (e.g. multiple soft-books on the
same race, hedged together), the formula could
be extended to account for net-market
commission. Not gating; analytical-layer work
post-DR-029.

### §7.2 — Multi-rung ladder hedge

**Status:** future arc; out of W4 v1 scope.

§3 (Construction B) and §6.1 (cash hedge) both
treat the Betfair lay as filling at a single
price. In practice, Betfair markets quote a
ladder — top three rungs visible under the
`EX_BEST_OFFERS` entitlement, top ten rungs
under `EX_LADDER` — and a large hedge may
need to fill across multiple rungs at
descending prices.

A multi-rung formula was derived in Session 88
conversation:

- For each rung, compute the marginal stake
  fillable at that rung's price (cheapest first
  on the lay side).
- Apply commission only on the *final* rung's
  partial fill (commission is market-level, so
  the cheaper rungs' winnings net against the
  final rung's loss in the equalisation).
- The single-rung formula is the collapse case
  (one rung fills all).

The multi-rung mechanism likely sits at the
matching layer rather than the math layer —
the math is a thin extension of §2, but the
operational shape (fill cheapest-first, partial
match handling, stale-rung detection) is
matching-layer territory. Routing locked Route
C in Session 88: defer to a future arc, likely
own math review and possibly own DR (candidate
DR-032 or later).

**W4 v1 behaviour:** single-rung placement at
the operator's chosen price (live or custom).
`priceLimit` protection means partial fills
are accepted only at prices ≤ operator's
intent — anything else refuses to match.
Operationally: large hedges that don't fill at
the top rung simply don't fill, and the
operator widens the price target manually.

**Four open policy questions** carried forward
to the future arc (operator-surfaced, Session
88):

- Commission rate source — same as W4 v1
  (dynamic lookup) or per-rung override?
- Rounding rule — round each rung's marginal
  stake or round the total?
- Partial-hedge tolerance — what fill
  percentage is "good enough" before flagging
  partial?
- Stale-price handling — what happens if a
  cheaper rung disappears between modal-open
  and confirm?

**Operator-side homework:** `EX_LADDER`
entitlement is parked operator-side. Current
`EX_BEST_OFFERS` (top three rungs) is
sufficient for W4 v1; `EX_LADDER` upgrade
becomes relevant when the multi-rung arc
opens.

### §7.3 — Cross-construction Net comparison

**Status:** edge case; W4 v1 is operator-
selects-construction.

Per §3.6, Construction A (lay-against-soft-book-
back) and Construction B (back-against-Betfair-
back) are not algebraically equivalent except
at c = 0. At positive commission rates, the
two constructions produce slightly different
Net values for "equivalent" prices, because:

- Construction A pays commission on the lay
  win (one outcome).
- Construction B pays commission on the back
  win at the opposing price (one outcome,
  different price).
- Real Betfair markets have overround across
  the two sides, so the "equivalent" prices
  are not identical.

**W4 v1 behaviour:** operator picks which
construction to use at modal open. Default
construction is A (works for any-outcome
markets); B is only available for two-outcome
markets per §3.

**Future extension:** the modal could surface
both Net values side-by-side when both
constructions are available, letting the
operator pick whichever produces the better
locked Net. Adds modal complexity (two stake
values, two liability values, two Nets) for
modest operational benefit (the difference is
small except at high commission and wide
overround). Not gating; UX call post-W4 v1.

### §7.4 — Strategy 2 price-uplift handling

**Status:** deferred to data-source work outside
DR-029.

Strategy 2 sub-shape 1 (boosted odds) was
simplified in Session 88 §5.4 — v3 takes the
boosted odds directly as P_soft, no separate
original-vs-boosted delta capture. This works
cleanly when the boosted odds are visible at
placement time (e.g. Top Fluc displayed before
race jump).

Some Strategy 2 sub-types involve **post-race
price uplift**: Best-of-Best, Best Tote,
closing-fluc-protection, where the final
payout odds are determined after the race
runs. Placement-time math uses the displayed
odds (best estimate at placement); the actual
realised P_soft may be higher.

The hedge math at placement time treats the
displayed odds as canonical — `S_bf` is sized
against displayed P_soft. If the realised
P_soft is higher, the cycle's actual Net is
better than the formula predicted; the hedge
is conservative.

**W4 v1 behaviour:** size hedges against
displayed P_soft. No placement-time accounting
for post-race uplift.

**Future extension:** the analytical layer
could measure realised vs displayed P_soft
across Strategy 2 cycles, producing a per-book
uplift distribution. This feeds back into
placement-time effective-odds synthesis —
similar shape to the free-bet realised-rate
parameter in §5.7. Outside DR-029 scope;
analytical-layer work.

### §7.5 — Manual stake override

**Status:** future refinement; not v1.

Session 88 Round 11: operator considered manual
stake override as a third axis of modal control
(alongside live-vs-custom price and persistence
type), then chose to defer.

**W4 v1 behaviour:** S_bf is computed by formula
from the operator's chosen P_bf (live or
custom). The operator does not type S_bf
directly. This keeps equalisation as canonical
behaviour; the modal always shows a hedge that
locks Net across both Betfair-side outcomes.

**Future extension:** allow the operator to
override S_bf manually — accepting a non-
equalised position deliberately. Operational
shapes that might justify this:

- Partial hedge — operator wants to hedge half
  the soft-book exposure, leave half running.
- Soft-book bias — operator has a directional
  view on the runner and wants to size the
  hedge against their conviction, not against
  pure equalisation.
- Liquidity constraint — operator knows the
  Betfair side won't fill at the equalised
  S_bf and pre-emptively shrinks the hedge.

When the override fires, the modal needs to
surface the **resulting Net for each outcome**
so the operator sees the directional exposure
they're accepting. The math is straightforward;
the UX shape is the design work.

**Carry-forward:** future W4 enhancement, post-
v3-ship.

### §7.6 — Placement-latency matched-price reporting

**Status:** `betfairlightweight` substrate;
deployment-time concern.

When W4 places a Betfair order, the order is
submitted with `priceLimit` protection per §4.4.
Betfair's matching engine fills at any price ≤
the limit (lay) or ≥ the limit (back). The
**actual matched price** may differ from the
operator's submitted price.

The §2 formulas assume P_bf is the matched
price. If the matched price differs, the
realised hedge math drifts from the displayed
math — usually favourably (matching at a
better price than submitted), occasionally
unfavourably-but-within-limit.

**W4 v1 behaviour:** capture the matched price
from the Betfair API placement response, store
it on the bet record, surface it in operational
review. Cycle reconciliation uses matched price,
not submitted price.

**Future extension:** post-placement modal
update showing matched-price-realised Net (vs
submitted-price-projected Net). Useful for
operator confidence-building over volume —
"actual hedge outcomes match my placement
intent". Not gating; UX add-on.

### §7.7 — Free-bet realised-rate analytics

**Status:** post-DR-029 analytical layer work.

§5.7 framed the free-bet conversion rate as
both **parameter** (placement-time, used in
effective-odds synthesis per §5.3) and
**analytics** (post-cycle, measured from actual
realised outcomes). §6.2's worked example
demonstrated one cycle's realised rate (66.99%
at moderate odds, 83.56% at long odds).

The analytical layer aggregates realised rates
across volume to:

- Validate the configured parameter (currently
  65% default, operator-configurable). If
  realised drifts above or below 65% over
  volume, operator updates the parameter.
- Surface per-bookmaker / per-promo realised-
  rate distributions. Some books pay free bets
  more cleanly than others; some promos
  produce free bets more amenable to clean
  hedging.
- Feed back into Strategy 1 EV reasoning. The
  Safety Net cycle's expected value depends on
  the realised free-bet rate; better
  measurement produces sharper EV estimates.

**Intent-aware filter required.** The realised-
rate denominator must exclude free bets the
operator deliberately did not hedge, free bets
where aggressive-price limits missed, and free
bets that lapsed for operational reasons. The
intent-capture substrate from earlier sessions
provides the filter mechanism (see §7.8).

**Carry-forward:** analytical-layer build,
post-DR-029, post-v3-ship.

### §7.8 — Intent-capture substrate for analytics filter

**Status:** post-DR-029 analytical layer
prerequisite.

Several future analytics surfaces (free-bet
realised-rate per §7.7, Strategy 2 price-
uplift measurement per §7.4) need an
**intent-aware filter** on the bet record set:
which bets were *meant* to be hedged-to-
equalisation, vs which were deliberately
asymmetric, vs which were operational misses.

Without the filter, realised-rate measurements
mix three populations:

- Cleanly-hedged cycles where the math worked
  as designed.
- Deliberately-unhedged cycles where the
  operator chose to ride the soft-book leg.
- Operationally-failed cycles where the hedge
  was attempted but missed (unfilled limit
  orders, lapsed free bets, late-placement
  shortfalls).

Mixing these produces noise in the realised-
rate signal that corrupts parameter-tuning
feedback.

The intent-capture substrate flags each bet at
logging time with its intended cycle role
(hedge-target, deliberate-asymmetric, no-hedge,
operational-fail). The analytical layer
filters on intent before computing realised
rates.

**Carry-forward:** the substrate work was
flagged in earlier-session conversation;
formalisation is post-DR-029 analytical-layer
prerequisite.

### §7.9 — Cycle-linkage at logging time

**Status:** Session 42 architectural extension;
formalises before W4.1.

Per §5 (cycle shapes) and the carry-forward
from Session 42, every bet record carries
Betfair-side identifiers (`betfair_market_id`,
`betfair_selection_id`, Betfair venue/sport/
event-name) as the canonical join key for
cycle linkage. This applies to *all* bet
records, including soft-book bets logged
manually.

The math review's equalisation logic operates
per-leg; cycle aggregation (linking the
original cash bet, the triggered free bet, and
the free bet's outcome into one analytical
unit) happens at the data-architecture layer,
not the placement-math layer.

**W4 v1 behaviour:** placement-time math is
per-leg per §2. Cycle-linkage at logging time
is W4.1 territory (soft-book bet entry path)
and feeds the operational store schema (W6).

**Carry-forward:** Session 42 architectural
extension formalises before W4.1 — either
extends `architecture.md` §D12 or new DR
(candidate DR-032). Three workstreams reference
it (W4 hedge-target input shape, W4.1 soft-book
entry path, W6 operational store schema).

### §7.10 — Sub-1.01 Betfair odds

**Status:** dissolved per Session 88 Round 6;
not a real concern.

The original §2.7 sanity-bound discussion
(Session 88) flagged a theoretical concern
about hedge math at extremely low Betfair odds
(P_bf approaching c). At c = 0.08 and P_bf
approaching 0.08, the cash formula's
denominator approaches zero and S_bf explodes.

In practice this is unreachable: Betfair's
minimum tick is 1.01. The math edge is purely
theoretical. Listed here for completeness and
because it surfaced in Session 88; no W4
behaviour required.

---

## §8 — Math review status

§1–§7 complete. The math review is locked
substrate for W4 brief drafting:

- **§1** — variables and conventions (dynamic
  commission lookup locked v1 scope).
- **§2** — Construction A: lay-against-soft-
  book-back (cash + free-bet formulas, Net=0
  condition, regimes, sanity checks, liability,
  warning threshold).
- **§3** — Construction B: back-against-
  Betfair-back (cash + free-bet formulas,
  two-outcome restriction, A-vs-B not-quite-
  equivalence).
- **§4** — modal mechanics (live + custom
  price tandem, `priceLimit` protection,
  PERSIST default, match-availability
  surfacing — supersedes Session 87
  PriceDriftEnvelope).
- **§5** — refund and free-bet cycle shapes
  (Strategy 1 two-leg, Strategy 2 three sub-
  shapes, effective-odds synthesis tool-
  calculated, default conversion 65%).
- **§6** — worked numerical examples (cash
  hedge general turnover, free-bet hedge
  Strategy 1 refund leg, Ipswich-vs-Queensland
  commission contrast, soft warning trigger
  demonstration).
- **§7** — edge cases and future extensions
  (multi-bet commission interaction, multi-
  rung ladder, cross-construction comparison,
  Strategy 2 price-uplift, manual stake
  override, placement-latency reporting,
  realised-rate analytics, intent-capture
  substrate, cycle-linkage at logging time).

**W4 brief drafting opens with §1–§7 as
substrate.** The four substrate decisions from
Session 87 (scope, module placement, placement
workflow input shape, cancel/replace + adjust)
are extended by §4 modal mechanics and §5
cycle-shape framing. The brief specifies the
W4 module against this locked substrate.
