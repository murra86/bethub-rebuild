# Promo-cycle analytics — canonical read rules + qualified baseline (S265, 3 Aug 2026)

**Purpose.** The operator asked for cycle-soundness numbers (TAB "Ins $50
FB 2+3" first), and the analysis went through one adversarial
verification and three attribution corrections before the numbers were
right. This file records the READ RULES any future analytics work must
honor — including the likely in-tool analytics page (parked idea, not
commissioned) — and the qualified baseline as of 3 Aug 2026. Every rule
below was learned by getting it wrong once against live data.

---

## 1. Read rules (each one bit us)

**R1 — `bets.commission` is a FRACTION, not a percent.** The column
holds 0.08 / 0.10 (distribution at 3 Aug: 72×0.08, 12×0.10 over lays).
Winning lay net = `stake × (1 − commission)`, NULL → 0.08 default
(`workflows/balances/v1/balance_derivation.py`, `_DEFAULT_COMMISSION`).
Dividing by 100 again charges 0.08% instead of 8% and flattered the
first conversion figure by $132.33. Caveat: this is the per-bet
identity; Betfair actually charges on per-market net (S247 item 2) —
identical for single-lay cycles, negligible here.

**R2 — P&L formulas by side/state.** Void → $0 always. BACK cash:
won `stake×(price−1)`, lost `−stake`. BACK free bet: won
`stake×(price−1)`, lost **$0** (face was never cash). LAY: won
`stake×(1−commission)`, lost `−stake×(price−1)`. Matches the app's own
derivation; validated against operator-verified figures (Arkansaw Kid
lay +$36.70 = 39.89×0.92; Velocity Miranda lay −$119.72 = 19.31×6.2).

**R3 — credit liveness has TWO supersession meanings.** A credit
superseded by another CREDIT-type event is dead (a correction). A
credit superseded by `free_bet_deployed` / `expired` / `revoked` is
CONSUMED lifecycle — still economically real. Filtering "unsuperseded
by anything" silently drops ~85% of real credits.

**R4 — void-and-restore = two credit events, ONE economic face.**
Live example `bet-f679f2a6…` (Fire Bomber, Doomben R3): FB deployed on
Inbestigator (Gold Coast R4), runner scratched → FB bet voided, TAB
returned the FB, restored credit re-deployed on Oscar Phoenix. Count
DISTINCT qualifiers for trigger rates and skip voided deploys' faces
(the face was returned, not consumed), or face totals overstate.

**R5 — lays attach to their back by SELECTION, not by cycle.** A cycle
can legitimately hold several backs + several lays (multi-deploy after
a restore; qualifier hedges). Cycle-wide lay lookup double-counted a
won lay ($35.60) into a voided chain. Match `bet_legs`
(selection_id, market_id) between lay and back.

**R6 — conversion's unit is the DEPLOYED BET, apportioned pro-rata.**
One FB bet can be funded by MULTIPLE credits (live example: $62.50 Neds
bet = $40 + $22.50 draws — per-credit accounting produced a 141%
"conversion"), and the credits can come from DIFFERENT templates/books.
Attribute the bet's net `× drawn/total_drawn` to each funding credit.
This is the only convention under which per-book numbers SUM to real
money (per-credit-full-net counted one co-funded bet's net in both TAB
and CrownBet at once).

**R7 — conversion excludes intentionally-unhedged; flags
unhedged-in-effect.** Intentional = `promo_journey_annotation` events
with tags `hedge_intentionally_skipped` + `bet:<bet_id>`. Separately,
a lay can exist but be $0-matched (failed exchange order — live
example `bet-52a3614f…`, Gilgandra, the 0z class): the FB converted at
0% with no annotation. Count these IN the average (they are real
outcomes) but surface them. `bets.realised_conversion_rate` is dormant
NULL by design (D1 fence) — never read it as truth.

**R8 — book attribution runs qualifier-side.** A funnel row's book is
the QUALIFIER's account-at-book (join `accounts_at_book`→`books`);
deploys/hedges may sit at other venues (Betfair). Template
`triggering_promo_instance_id` on credits == `promo_template_id`
(the promo instance layer is unused — 0 rows in `promo`).

---

## 2. Qualified baseline (all history to 3 Aug 2026, rules R1–R8)

Per template × qualifier book. N = settled qualifiers; TR% = triggers /
qualifying outcomes (losses for insurance, wins for bonus); CONV% =
apportioned net extraction / face consumed. Bet365 BW pays CASH at
settle (no FB face → no conversion row).

```
TEMPLATE                                 BOOK          N     W/L/V   WIN%     Q-P&L  TRIG    TR%     FACE  CONV%   EXTRACT    ALL-IN
Bet365 Bonus Winnings (Cash)             Bet365       11     5/6/0  45.5%    409.50     5 100.0%     0.00      —      0.00    409.50
Ins $25 FB 2nd                           PointsBet    13    2/11/0  15.4%   -202.50     6  54.5%    50.00  70.6%     35.31   -167.19
Ins $25 FB 2nd                           TAB           2     0/2/0   0.0%    -20.00     2 100.0%    10.00  72.5%      7.25    -12.75
Ins $50 FB 2+3                           BetRight     14    3/10/1  23.1%    -95.00     5  50.0%   200.00  71.8%    143.58     48.58
Ins $50 FB 2+3                           CrownBet     11     2/9/0  18.2%    -55.00     6  66.7%   350.00  56.6%    198.17    143.17
Ins $50 FB 2+3                           Ladbrokes     7     5/2/0  71.4%    398.00     1  50.0%    30.00  71.0%     21.30    419.30
Ins $50 FB 2+3                           Neds          8     2/6/0  25.0%   -120.00     2  33.3%    62.50  70.5%     44.06    -75.94
Ins $50 FB 2+3                           PointsBet    28    6/22/0  21.4%   -500.00     6  27.3%   280.00  73.2%    204.96   -295.04
Ins $50 FB 2+3                           TAB         151  46/105/0  30.5%   1087.50    46  43.8%  2300.00  70.2%   1613.62   2701.12
Ins $50 FB 2nd                           CrownBet      1     0/1/0   0.0%    -50.00     1 100.0%    50.00  75.4%     37.70    -12.30
Ins $50 FB 2nd                           UpYaGo        6     1/5/0  16.7%   -110.00     0   0.0%     0.00      —      0.00   -110.00
TAB Bonus Winnings 25% to $100 (FB)      TAB           3     2/1/0  66.7%    130.00     2 100.0%    46.00  63.3%     29.11    159.11
TAB Bonus Winnings 25% to $50 (FB)       TAB          30    8/21/1  27.6%   -194.20     7  87.5%   172.00  71.7%    123.26    -70.94

GRAND all-in across promo cycles: +$3,136.62
```

Headline reads:
- **TAB Ins $50 FB 2+3 is the workhorse and the edge**: 151 plays,
  +$2,701.12 all-in = **+$17.89/play** on $50 stakes (~36% ROI).
  Qualifier stage profitable alone (30.5% wins at avg 4.29 odds vs
  23.3% breakeven).
- **Every other template×book combination is small-sample**; most read
  negative at the qualifier stage with insufficient triggers to judge.
  PointsBet $50 2+3 (28 plays, −$295.04, 27.3% trigger) is the worst
  material cell.
- **vs S231/S246 benchmarks** (65% conversion / 24% win / 52%
  trigger): conversion ~70–73% BEATS 65% consistently across books;
  TAB win 30.5% beats 24%; **trigger 43.8% of losses is BELOW the 52%
  benchmark** (structural: 2nd/3rd-only; 59 of 105 TAB losses finished
  off the podium).

## 3. Data-quality census (3 Aug)

- 1 unhedged-in-effect FB (the $0-matched Gilgandra lay, 0z class) —
  in the averages, flagged.
- 6 triggered credits with face not yet deployed ($174.88 live FB
  inventory) — excluded from conversion until settled.
- 1 void-and-restore chain (R4 example) — coherent end to end.
- 0 orphan credits, 0 double-deploys, 0 duplicate-lay attributions
  under R5/R6.

## 4. Verification trail

S265: initial analysis → adversarial sub-agent verification (REFUTED
the commission units + benchmark framing; CONFIRMED census, formulas,
disjointness of the coincidental 46/46 win/trigger counts) → R5 and R6
discovered reconciling the sweep against the verified single-template
figures. The TAB $50 2+3 single-template number moved
76.7% → 70.97% → **70.2%** (final, conservation-safe convention).
Anyone reproducing these numbers should land on §2's table exactly;
a mismatch means a rule in §1 was skipped.
