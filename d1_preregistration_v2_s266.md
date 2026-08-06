# D1 PRE-REGISTRATION v2 — Call reliability analysis sitting (RE-RUN)

**Written 4 Aug 2026, S266, after the v1 memo was REJECTED by adversarial
review.** Supersedes `d1_preregistration_s266.md` in full. v1 and its
memo (`d1_memo_s266.md`) are retained as the record of what failed and
why — they are not deleted, and they are not evidence for anything.

Normative inputs: amendments 1–16 (`call_reliability_program_plan_s265.md`)
and amendments 17–28 (statistician review, S266). Where v1 conflicts with
17–28, 17–28 win.

**Why v1 failed, in one line each — these are the failure modes this
protocol exists to prevent:**

1. The fit population was never characterised. It was ~50% greyhound and
   harness racing and 8% metro; the operator bets 93% thoroughbred and
   71% metro. The shipped constant was worse than no projection at all on
   the operator's own tracks.
2. The incumbent was an algebraic guess (`β = 1`), not the production
   code path (which applies `sqrt(back·lay)` on 62–97% of rows and then
   field-normalises).
3. Two "delete this" recommendations were made with no significance test,
   no interval, and no power calculation. Both inverted under one.
4. The free-bet conversion rate measured cash per dollar DEPLOYED; the
   engine constant multiplies expected face CREDITED. Different quantity.
5. Five pre-registered specifications were silently substituted
   mid-analysis, three of them load-bearing for a "drop it" call.
6. An exploratory result that contradicted the headline recommendation
   was filed as "a candidate for a later pass" instead of escalated.

---

## 0. STAGING — the protocol is gated, not a single pass

**Stage A — POPULATION (no hypothesis testing).** Deliverable A1 below.
**REVIEW GATE 1** on Stage A before any fit is run. If the population
cannot support the question, that is the answer and D1 reports it.

**Stage B — FITS.** Only after Gate 1 clears.

**Stage C — REVIEW GATE 2.** Full adversarial round on the completed
memo. Reviewer mandate includes independent RE-DERIVATION (§9).

Running a Stage B fit before Gate 1 clears is itself a protocol breach
and must be reported as one.

## 1. DELIVERABLE A1 — population characterisation (Stage A, blocking)

Before any model is fitted, produce and publish:

**A1.1 Composition of the analysis universe.** Every race carrying a
realised BSP, broken down by racing code and meeting grade, for the fit
window and the report window SEPARATELY. `races.racing_code` is null on
a large share; resolve by venue mapping, publish the mapping, and report
the unresolved remainder as a share with its effect on each figure. A
composition table accompanies every headline table in the final memo
(amendment 17).

**A1.2 Composition of the operator's decisions.** From `bet_legs`:
sport, venue, meeting grade, matched price distribution, hedge stake
distribution, and time-to-jump at placement (`bets.placed_at` vs
`bet_legs.betfair_event_start_time`). This defines the target
population. Current known values, to be re-derived not assumed: 264
Horse Racing / 19 Greyhound; 71% metro thoroughbred; matched price
median 4.40, p95 12.00, 99.6% ≤ 20; hedge median $7.21, p90 $38.72,
max $48.44.

**A1.3 The overlap.** How much analysis data exists inside the target
population, per horizon bucket, per meeting grade. **Declared in advance:
if a stratum holds fewer than 200 held-out decision points, no constant
is fitted for it and D1 says so.** Under-powered strata are reported as
bounds, never as estimates.

**A1.4 Selection mechanism.** WHY only ~9,000 of 63,000 captured races
carry a BSP. Name the mechanism. Determine whether the shortfall is a
capture artefact that can be repaired from another source (e.g. Betfair
Data Portal daily BSP files) — if metro thoroughbred coverage can be
materially widened, that is done BEFORE fitting, because the operator's
population is the thin one.

**A1.5 Effective data window.** Stated on the availability of the
OUTCOME variable, not of any column (amendment 25). v1 claimed "6 Apr –
3 Aug"; only 4 races in April carry a BSP.

## 2. UNIVERSE (amendment 17, blocking)

All headline fits, distributions and constants are defined over
**Australian thoroughbred racing, stratified METRO / PROVINCIAL /
COUNTRY**. Greyhound and harness appear only as a labelled robustness
appendix and never in a headline. No constant is proposed for D2 from a
universe whose thoroughbred share is below 90%.

## 3. THE INCUMBENT (amendment 19, blocking)

The incumbent is the **production code path, executed**, not described:
`raceWatcher.ts` `projectedPairs` → `evEngine.estimateTrueOdds`
(geometric mid when `lay ∈ (price, 2·price]`, else `addTicks(price, 2)`)
→ `oddsToProbabilities` field normalisation, with `LATE_WINDOW_MIN = 2`.

**Validation gate:** the port must reproduce `grade_at_log` on 100% of
the operator's stamped graded bets before any comparison is run. A port
that disagrees on even one bet is not the incumbent and is fixed first.

No bucket may straddle `LATE_WINDOW_MIN`; buckets are split so no bucket
mixes two incumbent regimes.

## 4. METRICS AND LOSSES (amendments 18, 20, 21)

**4.1 Fitting loss** for β: squared error in log price vs realised BSP.
Retained from v1 — but NOT sufficient for adoption.

**4.2 Adoption requires, in addition, out-of-time and decision-weighted:**
(i) error on the **field-normalised win probability** against
BSP-implied normalised probability — the quantity the EV engine actually
consumes; and (ii) a **decision-flip table**: distribution of EV-point
movement vs the incumbent, and the share of runners crossing
`EXECUTE_BAR_PCT` and `MOD_MARGIN_PCT`.
**A constant that moves EV by more than MOD_MARGIN on a majority of
runners may not ship on MSE evidence alone.**

**4.3 Decision weighting.** No improvement claim is stated unweighted.
Weights = the operator's realised placement-time distribution, re-derived
each sitting (A1.2). The decision-weighted figure is the headline.

**4.4 Clustering.** All SEs, CIs and bootstraps cluster at
**meeting-day**. Race-clustered figures may appear alongside, labelled.

**4.5 Every quantitative claim carries an interval.** No point estimate
stands alone. **Every null result is reported as a BOUND with its
minimum detectable effect at 80% power** — "no effect found" is never
written without the size of effect the test could have seen.

## 5. THE FITS

**5.1 β — shrunken tilt.** `projected = mid × (sp_near/mid)^β`, fitted
per horizon AND per meeting grade within thoroughbreds. Adopted only if
it beats the §3 incumbent out-of-time on §4.2's decision-scale metric.
Horizon buckets report their realised mean and IQR time-to-jump, and no
constant is applied outside the range where its bucket carries ≥5% of
its mass (amendment 24).

**5.2 Depth imbalance (amendment 22).** Amendment 1's veto-only
provision STANDS; v1's drop is refused. Re-run to the ORIGINAL spec:
(i) outcome = sign agreement with **realised drift direction**, as
registered — not with the post-β residual; (ii) **full-ladder** depth
from `back_depth_json` / `lay_depth_json`, top-of-book only as
comparison; (iii) meeting-day-clustered t and CI on the coefficient;
(iv) explicit **tail analysis by imbalance decile** — a veto is a tail
instrument; (v) stated MDE at 80% power. The v1 "base rate" comparator
is retired: it measured the projection's level bias, not direction.

**5.3 Lay usability (amendment 23).** Re-run on the **decision set**:
thoroughbred, back price 2.0–20.0, per horizon with §4.3 weights, using
**aggregated ladder depth** against the **armed stake** — referenced to
the realised hedge distribution (A1.2), not a round number. Fire-rate
figures name the exact predicate; a spread-only rate may not be labelled
"spread or depth". Only then may the click-time gate be pronounced on.

**5.4 Free-bet conversion — OPERATOR RULING 4 Aug 2026: the constant
STAYS AT 0.65.** The operator's stated reason: a slightly conservative
figure is preferred. This is a risk-posture decision, not a claim about
the true value, and is not re-litigated.
Consequences that are binding:
- **§1f fits the bar against 0.65**, the same value the screen uses. The
  threshold and the stamp it judges must be on one footing; a mismatch
  is worse than either value.
- Amendment 9's "correct the stamp before tuning" is satisfied by the
  constant being FIXED and KNOWN, not by it being moved.
- The measurement is still reported, correctly this time —
  **credit-conditional, not deploy-conditional** — with leakage
  (expired / revoked / never-deployed) in the denominator, per-book
  table, book-clustered AND day-clustered CIs, and the count of
  unconverted-but-live cycles. It is reported as evidence, not as a
  proposed change.
- The S265 reference table is NOT a clean yardstick: it double-counts a
  restored credit (CrownBet cell). Corrections are recorded there before
  it is cited again.

**5.5 EXECUTE_BAR (§1f).** Re-derived on the 0.65 stamp, re-banded
history, and the replay's EV distribution. **(β, bar) are fitted
JOINTLY, not sequentially** — they are one parameter pair, and the
current bar was implicitly set against the current projection. Per-kind
evidence reported; the one-global-bar decision (S245) stays
operator-owned.

**5.6 Small-field (§1b-ii).** Terms branch remains CLOSED by operator
ruling. The statistical branch — does Harville misprice the 2nd/3rd
trigger chance as a function of field size — is run as registered.
Additionally, the 10 BetRight bets with no recorded field size are
recovered by joining `bet_legs.betfair_market_id` to the capture store's
`active_field_size` (v1's extract dropped the market id; it will not
this time). Note for the record: `position_min_field` is populated on
exactly one template ("Stake back 4th/5th, 14+ runners") with zero bets
ever placed on it, and BetRight's `{"3": 8}` exists only as a code
comment, not in the database.

## 6. TREATMENT OF ROWS (amendment 27, mandatory — absent in v1)

No table enters the memo without: honesty-tier classification (a)
bet-time truth / (b) feed-approximated / (c) assumed-promo control; the
**scheduled-versus-actual jump caveat on every time bucket**, quantified
if actual jump times are recoverable and stated as an unbounded
assumption if not; the snapshot-staleness note; twin-row handling stated
as **union or drop with its justification** (v1 dropped where production
unions — DR-036); and every exclusion **counted**, not merely named.

## 7. PRE-REGISTRATION DISCIPLINE (amendment 28)

A registered outcome, comparator or threshold may **not** be substituted
mid-analysis. Where the registered spec looks wrong, run it **as
registered**, report it, and register the amended version as an
ADDITIONAL pre-specified test. Every deviation — declared or found by
review — is enumerated in the memo's own DEVIATIONS section.

## 8. CONTRADICTION ESCALATION (new, from v1's worst failure)

**Any subgroup, robustness or exploratory result that contradicts a
headline recommendation is escalated to a blocking finding in the memo,
not filed as future work.** v1's own metro estimate (0.05–0.10 against a
pooled 0.38) contradicted its shipping recommendation and was recorded
as "a candidate for a later pass". That single act is what took the
sitting from wrong-in-detail to wrong-in-conclusion.

## 9. REVIEW MANDATE (Stage C)

Reviewers are instructed that **re-running the analyst's scripts is not
verification** — it confirms only that code agrees with itself. Every
headline must be **independently re-derived from the raw tables** by a
reviewer who did not write the original implementation. The one v1
finding caught this way (the conversion-rate denominator) was the one
that inverted a recommendation.

Reviewers must also be given: this protocol, the v1 memo, and the v1
review findings, and asked explicitly whether each v1 failure mode
recurs.

## 10. STANDING FENCES (unchanged, not reopened)

Runner form permanently OUT (amendment 10). Place-market input DROPPED
(amendment 7). S252 market-edge / SP-modelling fence stands. Rule-gate
cascade stays; no ML layer (amendment 11). STRONG and MOD carry the same
stake — tiers collapse to FIRE/LEAVE for staking (operator, 4 Aug 2026).
LEAVE-override ≤ half stake (operator).
