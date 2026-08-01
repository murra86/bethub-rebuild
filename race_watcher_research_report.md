# Race Watcher — Deep Research Report (S241, 16 Jul 2026)

Deep-research run: 103 agents, 21 sources fetched, 94 claims extracted, top 25
adversarially verified (3-vote panels) — **25 confirmed, 0 refuted**. Sources span
peer-reviewed economics (Economica, J. Gambling Business & Economics, Big Data Research,
ICML, AAAI), Betfair's own data-science tutorials + official API docs, and practitioner
communities. Organized by the five questions; each ends with the design consequence.

## Q1 — Market formation & price reliability

- **Exchange prices are the least-biased probability anchor available — but only above a
  liquidity floor.** Smith/Paton/Vaughan Williams (Economica 2006, 700 UK races): Betfair
  bias 0.90% vs 1.19% best-bookmaker; bias falls strictly monotonically with matched
  volume (1.82%→0.38% across volume classes) — and in the LOWEST volume class the
  exchange's advantage over bookmakers **vanishes entirely** (statistically
  indistinguishable). [HIGH confidence, verified against the primary PDF]
- The same study applied a **hard liquidity gate** — races under £2,000 matched were
  excluded as unrepresentative. The pattern (hard floor below which prices aren't
  treated as informative) is the published precedent for our trust cap; the number is
  2002/UK/thoroughbred and NOT transferable — per-code AU thresholds must come from our
  own 98k races. [HIGH]
- **Volume alone is not enough**: on Betfair soccer, higher liquidity DECREASED
  efficiency on weekends (noise-bettor money) — liquidity *composition* matters, so the
  gate should combine volume with structural signals: spread, overround convergence,
  share of runners traded, near/far gap. [MEDIUM — soccer working paper]
- **Time-to-jump is a first-class trust input**: prices sharpen monotonically into the
  jump (Betfair's own AU thoroughbred logloss study: T-120s → T-0 → BSP strictly
  improving); most GB volume matches in the final 10 minutes, largest drifts start ~6
  minutes out; ~40% of US parimutuel pool money arrives in the final minute. Early
  prices structurally miss most informed flow. [HIGH]

**Design consequence:** the trust gate = matched-volume floor (per code, fitted on our
data) × structural formation (spread, overround, % runners traded) × time-to-jump ramp.
Below the floor, exchange and bookmaker prices are equally uninformative → grade capped
at the lowest tier regardless of computed EV. This is the operator's "no strong when
numbers might be off" requirement with published backing.

## Q2 — Projected BSP (nearPrice) accuracy — direct hits on our BF Close column

- **nearPrice is cached (~60s refresh) and goes stale during late moves.** Betfair's own
  tutorial shows best back moving 3.0→2.9 pre-jump while projected SP sat still (BSP
  came 2.79). [HIGH — against-interest source]
- **At the scheduled off (AU thoroughbreds, full year of data), the live BEST BACK is a
  strictly better BSP estimator than nearPrice**: mean abs relative error 0.0917 (best
  back) vs 0.1213 (nearPrice); farPrice is terrible (0.5784). [HIGH]
- **nearPrice = SP pool + unmatched exchange money** (official API docs); with thin
  unmatched money it degenerates toward raw pool skew — and the **near/far gap is a
  free per-runner reliability indicator** (they differ only by the exchange-money term).
  We already capture sp_far. [HIGH]
- **Final BSP is a well-calibrated benchmark** (Betfair Hub: 381,776 ANZ races, implied
  vs actual win rate within ~1pp) → the right calibration TARGET for our pipeline —
  though pooled/marketing data; per-code and longshot-tail calibration must be confirmed
  on our own data (a 1pp absolute error can be −30% relative on a $100 shot — exactly
  where insurance promos live). [MEDIUM]

**Design consequence (changes the current BF Close column too):** inside the final
minutes, project the close from the LIVE BOOK (best back / back-lay blend), demoting
nearPrice to a cross-check; nearPrice static while best back moves = staleness flag,
never a signal. Add |near−far|/near and book depth as per-runner trust inputs.
Re-measure the ~60s cache empirically on our own sp_near snapshot history.

## Q3 — Steamers/drifters (price-movement prediction)

- **Late money is smart money — AU evidence**: 14,854 AU thoroughbred races: late flow
  moves prices toward objective win probabilities; the direction of very-late flow
  significantly predicts returns (late steamers beat late drifters, z=9.79). BUT
  favourite-longshot bias survives even at final prices. [HIGH — tote, not exchange;
  effect size needs re-estimation on our exchange data]
- **The best-evidenced exchange-native move predictor is distance-weighted Weight of
  Money** (order-book imbalance over top ticks, tick-distance-weighted, Brunel/Big Data
  Research 2018) — genuinely predictive out-of-sample but statistically fragile (its
  edge sat exactly at the significance borderline; a 4.2% trade shift flips it to
  losing). [MEDIUM — single study]

**Design consequence:** movement signals (trend, WOM, book-vs-exchange divergence)
**adjust the projected EV modestly and are never allowed to RAISE the confidence tier**.
Firm-side movement = EV-supporting; drift against the runner = EV-eroding. The residual
longshot bias argues for extra caution exactly where insurance promos concentrate.

## Q4 — Calibration methodology (the recipe for our 98k races)

- **Isotonic regression beats/matches Platt scaling at ≥1,000 calibration samples;
  overfits below** (Niculescu-Mizil & Caruana, ICML 2005 — canonical). Platt's sigmoid
  "only rarely fits the true distribution"; isotonic breaks when score→outcome
  monotonicity fails — "quite frequent" with correlated composite scores (AAAI 2015).
  [HIGH]
- **Evaluation standard**: logloss (proper scoring rule) primary + ECE/MCE reliability
  tables (K=10 bins); BBQ (Bayesian binning) statistically beat Platt/isotonic on
  ECE/MCE across 30 datasets — run it as a third candidate. **MCE per tier is the
  natural acceptance test**: "a STRONG grade must never be badly miscalibrated." [HIGH]
- **Correlated signals (volume, spread, overround, near/far gap all proxy liquidity)
  must be collapsed into one liquidity factor before calibration** or the composite
  overstates confidence. [HIGH]

**Design consequence / concrete recipe:** segment per racing code × time-to-jump
bucket; isotonic where the bucket has ≥1,000 settled outcomes (our data clears this for
major buckets), Platt for thin buckets, BBQ alongside; target = BSP-settled outcomes;
grade-at-log stamped for a live decision-log validation loop.

## Q5 — Grading scheme design

**No external evidence survived adversarial verification on tier counts or grade UX** —
the weakest section, honestly reported. What the verified adjacent evidence implies:
- **Drop the CERTAIN tier.** Even the best prices retain measurable bias (FLB at final
  prices; exchange advantage vanishing in thin markets) — the top grade should be
  STRONG, and only trust can unlock it. [LOW — inference, not direct evidence]
- One promising unverified thread (Risk Analysis 2023, did not reach the verified set):
  experts systematically CONFLATE "how likely" with "how trustworthy" unless the UI
  separates them — supporting our two-dial display (EV figure + trust state shown
  separately, grade = the combination).
- Tier count and grade-vs-interval display: decide ourselves, validate against the
  operator's own decision log (did STRONGs realize better than MODERATEs?).

## The four open empirical questions (= the calibration backtest spec, analytical line)

1. Per-code, per-time-bucket matched-volume/spread thresholds at which AU exchange
   prices become as calibrated as BSP — answerable ONLY from our 3.6M snapshots.
2. Does bookmaker-vs-exchange divergence / cross-book consensus movement predict
   short-horizon exchange moves? (No surviving external evidence — our data can answer.)
3. Does nearPrice's staleness/inferiority-to-best-back replicate on our snapshot
   history, and where is the crossover per code?
4. Trust-capped tiers vs EV-plus-interval display: test on the operator's decision log.

## Caveats (verbatim-summarized from the run)

Transferability dominates: the one published threshold is 2002/UK; AU late-money
evidence is tote not exchange; BSP-calibration source is Betfair's own education page;
the ~60s cache is approximate; WOM is a single borderline study; liquidity-composition
is soccer; Q5 had no surviving evidence. Every number above is a STARTING POINT for
calibration on our own data, not a constant to hard-code.
