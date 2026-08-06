# D1 PRE-REGISTRATION — Call reliability analysis sitting

**Written 4 Aug 2026, S266, BEFORE any query is run.** Required by
amendment 16 of `call_reliability_program_plan_s265.md`. Amendments
1–16 are normative here; this page fixes the protocol so the retune is
not graded on the data that suggested it.

Any deviation from this page is recorded in the D1 memo as a
DEVIATION with its reason. The memo's adversarial review checks
conformance to this page first.

---

## 0. Order of work (precedence, amendment 9)

EV-honesty fixes land BEFORE any threshold or bar fitting, because
both move the stamped EV by more than MOD_MARGIN and tuning on a
biased stamp bakes the bias in:

1. `DEFAULT_FB_CONVERSION_RATE` 0.65 → measured value (0.702 subject
   to re-measurement in §1a below on the current record).
2. `position_min_field` — CLOSED by operator ruling 4 Aug 2026: it is
   a book-terms clause, the primary insurance books pay 2nd and 3rd
   at any field size, so it is not entered and the S255 decision
   stands. Superseded by §1b below, which splits the terms branch
   (closed, bounded once) from the statistical branch (open: Harville
   trigger chance by field size).
3. History re-banded on the corrected stamp. The n=49 / +16.0% band
   is RETIRED as evidence (amendment 15).

## 1. Fits, metrics, losses

Each fit below names its outcome, its loss, and its clustering unit
in advance. No fit is judged on a metric chosen after seeing results.

**1a. FB conversion rate (measurement, not a fit).** Outcome:
realised cash from converted free bets ÷ free-bet face value, on
settled cycles only. Unconverted-but-live cycles excluded and counted.
Reported with n, CI, and per-book breakdown. This is a
re-measurement of the 70.2% figure on the current record, not an
assumption.

**1b. Small-field insurance — SPLIT INTO TWO BRANCHES (operator
ruling, 4 Aug 2026, before any D1 query ran).**

The operator's ruling: if the small-field question is a BOOK TERMS
question, do not implement — the primary insurance books pay 2nd and
3rd regardless of field size. If it is a STATISTICAL question about
the EV calculation in small fields, embed it.

Determination: `position_min_field` is purely a terms clause
(`evEngine.ts:302-307` — "minimum ACTIVE field size at which the book
still covers it", BetRight `{"3": 8}`). It is NOT a Harville or
trigger-probability matter. **Therefore the terms branch is CLOSED:
the clause is not entered, the S255 decision stands, and the S265
BetRight per-book variant stays declined (do-not-re-raise).**

- **1b-i (terms branch — bounded, then closed).** Single bounded
  check only: count historical graded insurance bets placed with a
  book carrying a real small-field exclusion on fields at or below
  its threshold, and their dollar exposure. Purpose is to BOUND the
  residual stamp error for §1f, not to reopen the decision. If the
  count is zero or immaterial it is stated once and never raised
  again.
- **1b-ii (statistical branch — OPEN, operator-directed).** Does the
  Harville trigger-chance model misestimate 2nd/3rd probability as a
  function of FIELD SIZE? Amendment 7 measured place-BSP vs Harville
  in the 5–30% band overall (≤0.5pt) and found the <5% outsider tail
  overstated 1.36×, but never broke either out by field size — small
  fields are exactly where Harville's independence assumption is
  most strained. Outcome: Harville-implied 2nd/3rd trigger chance
  minus place-BSP-implied, by pre-registered field-size bucket
  (≤7, 8–10, 11–13, 14+), race-clustered. Materiality threshold
  declared in advance: **material if any bucket's median |delta| >
  1.0 percentage point of trigger chance, or > $0.50 per $50 promo.**
  If material, the correction is embedded in the EV engine per the
  operator's instruction. Data source: place BSP in the Data Portal
  daily files (jump-time truth — adequate for this question).

**1c. β — shrunken tilt projection (amendment 1).** Model:
`projected = mid × (sp_near/mid)^β`. Fit β per time-to-jump horizon
(pre-registered buckets: T−60→30m, T−30→10m, T−10→3m, T−3→0m).
Loss: **squared error in log price** against realised BSP. Clustering:
**by race** (errors within a race are correlated; all CIs use
race-clustered standard errors). Incumbent to beat: the current
constants. β is adopted per horizon only if it beats the incumbent
**out-of-time** (§2). Coverage constraint acknowledged: sp_near
capture begins Apr 2026; rows with `sp_near_price` = Infinity (44
known) excluded and counted.

**1d. Depth-imbalance — VETO ONLY (amendment 1).** Imbalance enters
as a trust/veto input: when the imbalance tercile's direction
contradicts the projection, the trust gate caps the tier. Signals
never raise a tier. Outcome for the fit: sign agreement between
imbalance direction and realised drift direction, race-clustered.
A magnitude adjustment is proposed ONLY if it beats the shrunken-tilt
incumbent out-of-time; if proposed, its cap units are stated
explicitly. Pre-registered: I expect this to fail the magnitude bar
(54% vs 52% base) and ship as veto-only.

**1e. Lay usability → EV FLOOR (amendment 3, rescoped).** Applies
ONLY to trades whose EV assumes a hedge leg (free-bet conversions).
Effect is an EV floor — recompute at unhedged-conversion economics —
never an automatic LEAVE. The execution path modelled is the ACTUAL
one: Take-SP / MARKET_ON_CLOSE default since S263, i.e. SP-lay
liability, not click-time depth alone. Deliverable: distributions of
lay/back spread ratio, best-lay depth vs armed stake, empty-ladder
frequency → proposed gate constants. For cash promos (never hedged)
these feed the TRUST gate only.

**1f. EXECUTE_BAR re-derivation (amendments 8, 15).** Run on the
CORRECTED stamp, re-banded history, and the replay's EV distribution.
Per-kind evidence reported (bonus vs insurance LEAVE rates differ:
24% vs 8%) but **the one-global-bar decision (S245) stands** — D1 may
only report per-kind evidence, never unilaterally split the bar.

## 2. Out-of-time split (fixed now)

**Fit window: capture data up to and including 30 Jun 2026.
Report window: 1 Jul 2026 → 4 Aug 2026.** Every headline number is
the out-of-time number. In-sample figures may be shown alongside,
always labelled.

If the report window yields fewer than **200 evaluable decision
points** for a given fit, that fit reports "insufficient out-of-time
sample" and its constant is NOT adopted. The split date does not
move to rescue a fit.

## 3. What tunes and what evaluates (amendment 16)

- **Tuning set:** capture-store replay + no-bet control samples.
- **Evaluation only:** the operator's bet record (279 graded bets).
  It is never used to fit a constant. It is the record the outcome
  claims are checked against, and it is small and self-selected.

## 4. Band boundaries — fixed in advance

Tier bands are declared before results are seen. Any boundary chosen
after seeing outcomes is labelled EXPLORATORY in the memo and cannot
enter D2.

Primary metric per tier (amendment 12): **CALIBRATION RESIDUAL** =
actual win rate − BSP-implied win rate. ROI is reported alongside
with CI and n, and is never the band test. Pre-registered band
statements:

- LEAVE: calibration residual significantly negative (one-sided,
  race-clustered).
- MOD: calibration residual within ±3 points of zero.
- STRONG: no separate band claimed in D1. **Operator locked 4 Aug
  2026: STRONG and MOD carry the SAME stake — tiers collapse to
  FIRE / LEAVE for staking purposes.** STRONG/MOD separation is not
  a D1 question and no stake rule depends on it.

Stake rules on record: LEAVE-override ≤ half stake (operator,
4 Aug 2026). No other stake rule exists.

## 5. Honesty tiers on every backtest row (amendment 4)

Each row classified (a) bet-time truth, (b) feed-approximated
series, (c) assumed-promo control. Non-feed books (Bet365, BetRight,
AllBets, CrownBet, UpYaGo) and typed boosted prices excluded from
series replay or flagged. Mandatory: twin-row dedupe by market id;
scheduled-vs-actual jump caveat on every time bucket; snapshot
staleness noted (~4.5min mid-window, ~20s inside T−3).

## 6. Coverage (amendment 5)

D1 characterises the 109 ungraded racing-screen cash backs and
reports the share of fired bets carrying a Call. The Call's EV basis
(qualifying stake = `max_stake ?? DEFAULT_HYPOTHETICAL_STAKE`) is
stated in the contract. NONE stamps distinctly from NULL.

## 7. Multiplicity

Every per-kind or per-code claim carries a multiplicity note stating
how many comparisons were run. No per-subgroup claim is promoted to a
constant without surviving correction.

## 8. Standing fences (not reopened by D1)

- Runner form: permanently OUT (amendment 10).
- Place-market input: DROPPED, materiality answered negative
  (amendment 7).
- Market-edge / SP modelling fence (S252) stands — the imbalance fit
  exists solely to serve the Call's LEAVE boundary.
- Architecture: rule-gate cascade stays; no ML layer (amendment 11).

## 9. Honesty line carried into the memo and the scorecard

A PERFECT jump-time Call is worth ≈2–3% of turnover **on the 59%
replayable share** — against the ~21% the promos themselves deliver.
The unreplayable remainder (outages, non-feed books) is NOT
established. The Call's three jobs are boundary discipline (LEAVE),
coverage, and stamp honesty — not alpha.

## 10. D3 is confirmatory

No mid-window changes. Per-tier n targets before any "calibrated"
claim: MOD ≥200, STRONG ≥100, LEAVE ≥50 via the counterfactual
ledger. Ledger settles at logged soft price + promo economics under
the live all-in convention (amendment 13), with CONSIDERED and
imbalance-VETOED subsets flagged separately. "~" lifts only when the
calibration CI excludes the neighbouring tier's point estimate.
D3 exit = "MOD calibrated, others accumulating".
