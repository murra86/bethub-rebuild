# Adversarial review — EV validation (fresh-eyes, S231)

**Reviewer:** fresh isolated in-house agent, zero project context, instructed to refute.
**Inputs:** the commission, derivation paper, findings v1, calibration script v1 + raw output,
and the live engine source (which it independently diffed against the replica).
**Filed verbatim below.** Disposition of each finding is in `ev_validation_findings.md` §
"Review disposition" (v2). Headline dispositions: F1 fixed (Test 4 re-run inside the archived
v2 script); F3 CONFIRMED by the v2 band slice ($6–$10 runs ~3 pts hot); F4's mechanism
REFUTED empirically (clean-lay subset shows the same lean; fallback races are only 655 of
16,889) though its "not conservative for rivals" logic point stands; F2/F5/F6/F7/F8 accepted
— claims reworded and epsilon refit added; F9 largely defused by T1e/T1f (dropped races
calibrate identically); F10/F11 measured (dead-heats ~0.7% of races; fp↔winner disagreement
0.42%); F12 fixed (tie-break); F13 noted (clean-lay backtest now reported); F14/F15 accepted.

---

1. **FATAL — Test 4 has no evidence behind it.** The findings report specific Test 4 numbers (7,978 live races, 1.2-pt median midpoint-vs-BSP agreement, "1 in 100 readings off by 28+ points") — but the archived script contains no Test 4 code, the raw output ends at "TEST 3 … DONE", and the archive directory contains exactly two files (no Test 4 script, no output, and none of the per-test CSVs the commission mandates). Every Test 4 claim is unverifiable from the record. This matters more than it looks: Tests 1–3 validate a static historical CSV; Test 4 is the only piece that vouches for the LIVE feed the race screen actually consumes. The "execute on it" verdict is partly resting on numbers that, on the archived evidence, do not exist. The operator should withhold gate-#10 sign-off until the Test 4 script + raw output are produced and archived. **Decision-changing.**

2. **MATERIAL — Test 3 is not an independent "money number"; it is Tests 1+2 rearranged.** The backtest prices every bet at the engine's own midpoint odds and predicts with the engine's own midpoint probability. Algebraically, predicted-minus-realised on the base leg is exactly the odds-weighted Test 1 calibration error, and the promo layer reconciles "almost exactly" because it is exactly Test 2's numbers again. "History paid +21.1%" means: history would have paid +21.1% to a bettor who got Betfair-fair midpoint at a bookmaker with zero margin. No real book pays Betfair fair — soft books shade several points below it, and the shading directly erodes the base leg that carries the whole EV. The honesty-rails paragraph admits this, but the headline table presents an internal-consistency check as an achievable historical return. Operator should read Test 3 as "the arithmetic is self-consistent," not "this strategy historically earned 21%."

3. **MATERIAL — the "~1-point optimistic lean" is not uniform, and the spec-required odds-band slice of Test 3 was never run.** Reconstructing from the Test 1 band table: $2–$4 ≈0; $4–$6 model *pessimistic*; $6–$10 +0.41 pts on win% (≈1.9σ on N=24,344) → EV lean roughly ≈+3 pts optimistic at $6–$10. "A +12% on screen is a real +11-to-12%" is band-dependent and could be "+12% on screen is +9%" for a $8 runner. **Decision-relevant for which odds band to bet.**

4. **MATERIAL — the no-lay fallback is anti-conservative for the runner you bet, contradicting the paper's assumption ledger.** Ledger row 5 calls back+2-ticks "Conservative by construction." It is conservative only for the flagged runner itself; lengthening a *rival's* odds raises your runner's win probability and EV after normalisation. Predicted NOPROMO EV +0.52% implies implied sums average below 100%. The fallback (plus lay-rejection at >2× back) is pushing a phantom +1% into the field. Worst in thin markets — exactly where the operator is told the flags will protect him; the flags mark the fallback runner, not the runners whose EVs the fallback silently inflated.

5. **MATERIAL — "re-fitting the constants says the current values are already right" is not what the refit shows.** (a) Log-loss differences of 4e-5 — the objective is so flat the refit has essentially no power to distinguish exponents; a flat surface cannot "confirm" anything. (b) Epsilon was never refit at all despite the spec, and T2d is the worst table in the run. (c) The delta refit was conditioned on gamma=0.80, not the engine's 0.77. What actually constrains the exponents is the T2 calibration tables — say that, not "the refit confirms them."

6. **MATERIAL — "where it misses, it mostly UNDER-states your refund chance — errors sit in your favour" is contradicted by the raw output.** T2c's flagged bins: two of four significant misses are against the operator — and bin 10 is the highest-P(2nd/3rd) decile, short-priced runners in the $2–$4 heart of the working band, where the tool overstates the refund chance by ~0.8 pts. The sentence should be deleted or inverted for the short-price band.

7. **MATERIAL — "as close to perfectly calibrated as a 163k-runner sample can show" overstates, and part of Test 1 is true by construction.** Ten bins across T2a–T2d are starred — miscalibration above the noise floor in those cells. Pooled mean predicted equals pooled mean actual identically (per-race normalisation + exactly one winner), so headline-level agreement is an arithmetic identity; what Test 1 genuinely tests is the shape (favourite-longshot bias), which genuinely passes. Assumption 1 as written ("Betfair midpoint = true chance") was never and can never be tested this way — only the normalised field was.

8. **MATERIAL — the replica "proven identical … (cross-check to the decimal)" is overstated.** The actual crosscheck is one synthetic field, 4 numbers, tolerance ±0.15, against values that are the paper's own worked example — not the ~20 rows the spec required. Having independently diffed the Python against the TS source: the replica IS faithful (the only divergence is add_ticks arithmetic-stepping vs ladder-snap, which differs only for off-tick inputs that on-tick historical prices never hit). The conclusion survives — but by my inspection, not by the offered proof.

9. **MATERIAL — 18% of races silently vanish from Tests 2/3 with no bias analysis.** 16,889 kept races shrink to 13,866 full-ordinal. ~2,644 races with no finish positions (join failure — composition unreported) plus ~379 with partial order — plausibly fallers/DNFs, precisely the races where an insurance bet on the faller pays nothing. Also excluded and uncaveated: 141 fields under 5 — the live engine still prices ≤4-runner fields, and nothing in this validation covers them.

10. **MINOR — place dead-heats neither excluded nor counted.** A dead-heat for 2nd flows into T2/T3 as two "exactly 2nd" hits; real promos typically pay dead-heats by house rule. The spec's dead-heat count for places was never produced.

11. **MINOR — finish_position semantics never verified.** The obvious check (fp==1 ⟺ win_result=='WINNER') was never run. Indirectly defused — place actuals could not track predictions this tightly if fp meant something else — but that defense is the thing under test.

12. **MINOR — latent binning bug.** calib_table sorts (predicted, outcome) tuples, so ties straddling a bin boundary sort losers low / winners high. Negligible in this run; would bite any rerun on coarser probabilities.

13. **MINOR — validated population ≠ recommended execution population.** The backtest bets every $2–$10 runner including no-lay (⚠) fallback runners, while the findings instruct the operator to execute only on unflagged runners.

14. **MINOR — "the same ~0.8-point gap in every row" is one observation, not four.** All four Test 3 rows share the identical base leg on identical bets; the promo layers reconcile by construction.

15. **MINOR — smaller spec deviations:** no per-test CSVs; binomial CIs replaced by stars; "no better probability source" tested against exactly one alternative (BSP); "~70% general conversion" is operator recollection (labelled as such); delta grid never refined.

**Bottom line.** The core empirical content is real and mostly survives attack: Test 1's bin-level win calibration and Test 2's exact-2nd/exact-3rd calibration are genuine checks against actual finishing orders on large N, the Python replica is faithful (verified by my own diff), and no favourite-longshot pathology exists. But the headline verdict "The engine is validated. Execute on it." is broader than the evidence: (a) Test 4 has no archived evidence — that alone should block sign-off until produced; (b) the "money number" is an internal-consistency check dressed as a historical return; (c) the optimistic lean is plausibly ~3 EV points at $6–$10; (d) the fallback mechanism lives in the production engine and is mislabelled "conservative"; (e) the refit "confirms the constants" claim is hollow; (f) the "errors sit in your favour" sentence is false in the operator's own short-price band. An operator acting on this should: demand Test 4 artifacts, demand the band-sliced backtest, discount $6–$10 screen EVs by ~2–3 points pending that slice, and treat the +21% as arithmetic, not track record.
