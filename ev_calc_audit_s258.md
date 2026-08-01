# EV calculation audit — S258 (29 Jul 2026)

Trigger: operator screenshot (Randwick R6, Rantan) — PROMO EV column
−2.4% while THIS RACE panel +$0.36 on the same standing bet. Operator
directive: full review of every EV calculation for soundness.

## Verdicts

### SOUND — verified by reading + external validation
| Surface | Verdict |
|---|---|
| `oddsToProbabilities` | Multiplicative overround removal; S253 validated the outputs against 31,995 real runners (win + place gaps ≈ 0.0 pts). |
| `estimateTrueOdds` | Geometric midpoint back/lay; lay rejected if >2× back; back+2-tick conservative fallback. |
| `harvillePlaceProbs` | Corrected Harville (γ/δ/ε exponents); externally calibrated (S253); the panel's MC sampler draws from the SAME generative process (S253 review fix). |
| `evNoPromo` / `rawEV` | (pWin×odds−1)×100 — textbook. |
| `evInsurance` | rawEV + P(insured)×bonus×conv as % of effective stake; field-size clause drops voided positions; S253 validated ~17c/$50 accuracy. Stake-safe: insurance presets set `max_stake`, and EV% is invariant above the cap. |
| `evFreeBet` | SNR lay-hedge: L=(o−1)F/(l−1+1−c), profit=L(1−c) — algebra checked, correct; % of face is face-invariant so the stake default cannot hurt it. |
| `evBoostedOdds` | Raw EV at boosted price — correct (note below). |
| Race panel (`racePortfolio`) | Headline EV is ANALYTIC (Σ per-bet EV built so E[pnl]≡EV exactly); only the risk band is Monte Carlo (CRN). Uses each bet's REAL stake → correct. ConfirmCard marginal rides this → correct. |

### DEFECT D1 — bonus-winnings hypothetical stake (CONFIRMED, exact reproduction)
`buildConfigFromPreset` (presets.ts:159-160) deliberately stores the
promo's $50 as `bonus_cap` and leaves `max_stake = null` for
bonus_winnings (right: the cap caps the CREDIT). But three consumers
compute EV at `promoConfig.max_stake ?? 100` — i.e. **always $100 for
every bonus-winnings promo**:
- OddsTable PROMO EV column (OddsTable.tsx:520)
- ConfirmCard EV readout (via `computeEvSnapshot`, Racing.tsx:178)
- **the STAMPED `promo_ev_at_log`** (same snapshot → BetLog analytics)

At $100 stake a $50 bonus cap binds whenever (odds−1)×25%×100 > 50 →
**odds > 3.0**; at the operator's universal $50 stakes it binds only
above 5.0. Result: bonus-winnings EV understated in the 3.0–5.0 odds
band — exactly where the operator bets.

Reproduction (harness, controlled inputs, Rantan case: pWin 0.23658,
book 3.80, 25%→FB cap $50, conv 0.65):
- stake $50 → **+0.664 %** ≡ panel's +$0.36 ✓
- stake $100 → **−2.411 %** ≡ column's −2.4% ✓
Delta fully explained; no residual.

Blast radius: display only + logged analytics. No money path touches
these numbers (settlement/credits use template terms + real results).
The 25 settled bonus-winnings bets' `promo_ev_at_log` are understated
(sum logged $86.73; true-at-$50 roughly $30–40 higher) → the S258
EV-vs-real "luck" on bonus_winnings is overstated by the same amount;
fortnight "running hot" ≈ +$405–415 rather than +$445 (raw), haircut
framing unchanged.

### Notes (not defects)
- Boosted-odds EV models no cap on boosted winnings — fine while the
  operator's boosts are uncapped; revisit if a capped boost appears.
- The standing ~3pt screen-EV haircut (S231) remains head-knowledge,
  not code — unchanged by this audit.

## Fix proposal (pending operator go)
1. Column + snapshot default stake for bonus-winnings → **$50** named
   constant (the house universal stake; insurance presets already
   encode the same scale via max_stake=50).
2. The at-log stamp uses the bet's ACTUAL typed stake from the
   ConfirmCard (it is known at stamp time) — the stamp describes THE
   bet, not a hypothetical.
3. Regression tests: the two reproduction cases + a stamp-stake test.
Optional/deferred: recompute historical bonus-winnings
`promo_ev_at_log` from stamped bf_back/lay_at_log (approximate — full
field not stored) or era-note the analytics.
