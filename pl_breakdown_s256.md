# P&L breakdown — S256 (28 Jul 2026, all activity since 18 Jul)

Requested by operator: "basic breakdown of PL using the cycles we have
established — by account, account-at-book, and by promotion type."

**Method (technical note):** read-only over the live money store using
the app's OWN derivations — `bet_net_pnl` per settled bet with the
market-netted lay-commission allocation (`lay_commission_by_bet`,
whole-store, the pnl-dashboard pattern). Promo-type figures are
CYCLE-level: each cycle's member bets (soft-book back + Betfair hedge +
FB conversion spends, linked per the S246 backfill) are netted together
and the cycle is labelled by its qualifier's template kind. Account and
account-at-book tables are BET-level (each bet's P&L at the account
that carried it), which is why Betfair hedging losses sit on
Tim @ BetFair while the promo table nets them into their cycles. All
three views reconcile to the cent with each other AND with the Money
page (`/v1/cash-flow/pnl` = 1750.32, self-check passing) at the time of
the read. Window: first bet row 2026-07-18 → 28 Jul morning.

## Total

**+$1,750.32** across 293 settled bets. Plus $100.00 unspent bonus-bet
face value in hand (Allbets deposit bonus — not counted until it
converts).

## By account (bet-level)

| Account | P&L | Settled | Won |
|---|---:|---:|---:|
| Leigh | +$897.50 | 49 | 12 |
| Tim | +$890.32 | 176 | 80 |
| Sarie | +$227.50 | 59 | 12 |
| Kate | −$265.00 | 9 | 0 |

## By account-at-book (bet-level)

| Account @ book | P&L | Settled | Won |
|---|---:|---:|---:|
| Tim @ TAB | +$1,020.00 | 56 | 17 |
| Leigh @ TAB | +$897.50 | 49 | 12 |
| Tim @ BetRight | +$305.00 | 19 | 4 |
| Sarie @ TAB | +$167.50 | 47 | 10 |
| Sarie @ CrownBet | +$160.00 | 10 | 2 |
| Tim @ UpYaGo | +$5.00 | 7 | 2 |
| Tim @ BetFair | −$29.68 | 56 | 50 |
| Sarie @ TABTouch | −$100.00 | 2 | 0 |
| Tim @ AllBets | −$110.00 | 4 | 0 |
| Kate @ CrownBet | −$265.00 | 9 | 0 |
| Tim @ PointsBet | −$300.00 | 34 | 7 |

Notes: Tim @ BetFair is the hedging book — 50 small wins netting
−$29.68 is the cost of laying, not a betting problem; its true value
shows inside the promo cycles below. Tim @ AllBets −$110 is the
conditioning spend (deliberate). Kate @ CrownBet 0-from-9 is the only
genuinely cold line.

## By promotion type (cycle-level — the whole play netted)

| Type | P&L | Cycles | Settled bets |
|---|---:|---:|---:|
| Insurance (2nd/3rd refund) | +$1,425.84 | 157 | 233 |
| Bonus winnings (boosted) | +$304.11 | 15 | 23 |
| No promo | +$20.37 | 37 | 37 |

Insurance is ~81% of all profit at ~$9.08 per cycle. Bonus-winnings
runs ~$20.27 per cycle on a small sample (15). Non-promo bets are
break-even — consistent with the S252/S253 finding that the edge is
the PROMO, not the price.

## Review-surface sweep (same sitting)

Pending bets 0 · manual queue 0 · source-pending spends 0 · unpaired
lays 0. Credit-gaps watchdog: 35 rows → 24 dismissed through the
tool's own confident-ran-outside sweep (placings verdicts, tool rules:
dead-heats, BetRight-3rd and unknowns never auto-classed); **11 remain
with genuinely-absent race results** — expected to fill from tonight's
post-trial-fix results re-pull, re-sweep after (likely most are also
ran-outside; any that finished 2nd/3rd are owed a credit → check the
book, credit-in).
