# EV validation commission — earning full faith in the promo-EV numbers

**Commissioned:** Session 231, 2026-07-06. Operator-directed: the promo EVs are THE primary
execution metric; the operator currently has no independent grasp of their derivation and
needs validated numbers, not asserted ones.
**Status:** COMPLETE (S231, same session). Piece 1 delivered (`ev_derivation_paper.md`,
v1.1 after external reviews); piece 2 run twice (v1, then v2 end-to-end after the
adversarial review — script/output/CSVs at `dr029/ev_validation/`); piece 3 verdict in
`ev_validation_findings.md`; adversarial review filed verbatim and dispositioned. **Operator
signed off gate #10 on this evidence** with two standing rules (the $6–$10 haircut; flagged
EVs never firm). Refinement verdict accepted: fit-for-purpose for Strategies 1–2; reopen
triggers = Strategy 4 build, a 2-3-4 promo entering the catalogue, or proving-window drift.
**Relationship to B6:** gate #10 (EV eyeball) stays OPEN until this arc lands and the operator
signs off. Runs parallel to seeding/proving window; blocks nothing else.
**Governing DRs:** DR-027/028 (capture.db is the analytical store; read-only here),
DR-033 (source roles), DR-021 (Adelaide anchors).

---

## The three pieces

**Piece 1 — plain-language derivation paper** (`ev_derivation_paper.md`, delivered).
Operator-readable walk from Betfair prices to promo EV, every assumption named. The operator
reads and interrogates it; unclear = piece 1 gets revised until clear.

**Piece 2 — empirical calibration check** (the trust-earning evidence; spec below).

**Piece 3 — refinement verdict** (written from piece 2): is the held data enough, or would
ongoing/new capture materially sharpen the numbers? Names exactly what (if anything) to
collect and what cadence of recalibration is worth doing.

**Fresh-eyes adversarial review** (after pieces 1–3): one isolated reviewer over the method +
findings — same pattern that caught r11. Prompt+dossier only, no project context.

---

## Piece 2 spec — empirical calibration against capture.db

**Discipline:** capture.db on the VPS, strictly `mode=ro`. No writes anywhere on the VPS. No
Betfair contact. Output lands as `ev_validation_findings.md` (rebuild root) + a results CSV
per test under `dr029/ev_validation/` (created by the job).

**Grounded data inventory (verified S231, read-only):**
- `betfair_historical` — 163,809 runner rows, 12 months (2025-03-01 → 2026-02-28), 100%
  coverage of `win_bsp`, `win_result`, `place_result`; 163,317 with `best_back_at_off` +
  `best_lay_at_off`; `overround_at_off` present. Static Betfair CSV import.
- Join `betfair_historical.runner_id → runners.finish_position` — **137,917 rows carry the
  full ordinal finishing position** (Racing API side), enabling 2nd/3rd/4th validation.
- `betfair_snapshots` — 3.47M live snapshot rows (2026-03-02 → today), 3.14M with back+lay,
  81k with BSP stamped; `sp_near_price`/`sp_far_price` populating since Fix 3. Secondary
  dataset (validates the LIVE pipeline feeding the race screen, not just the historical CSV).

**Test 1 — win-probability calibration (the foundation).**
For every historical runner with back/lay at off: compute the engine's fair win probability
exactly as `evEngine.calculateFieldProbabilities` does — geometric midpoint
`sqrt(back × lay)`, implied probs field-normalised to sum to 1 (replicate in Python from the
paper's formulas; cross-check ~20 rows against the TS engine's output to prove the replica
before trusting it). Bucket into probability bands (e.g. 20 equal-count bins). Per bin:
predicted mean win% vs actual win rate (`win_result`), with binomial 95% CIs and N. Repeat
using BSP as the probability source (BSP is Betfair's own converged truth — if midpoint-at-off
calibrates worse than BSP, quantify the gap). Deliverable: calibration table + a
plain-language verdict per odds band, ESPECIALLY the operator's working band ($2–$10).

**Test 2 — Harville place-probability calibration (the promo load-bearer).**
For each race in the 137,917-row ordinal subset: field win probs per Test 1, then the
corrected-Harville 2nd/3rd/4th probabilities with the engine's exponents (γ=0.77, δ=0.62,
ε=0.48 — replicate `harvillePlaceProbs`). Per probability bin: predicted vs actual rate of
finishing exactly 2nd, exactly 3rd, exactly 4th, and cumulative (2nd, 2nd–3rd, 2nd–4th — the
shapes the insurance promos actually pay on). This directly answers: when the tool says "16%
to run 2nd", is that true? Also fit the exponents fresh on this dataset (simple 1-D
grid/optimise per exponent against log-loss or calibration error) and report fitted vs
current values — if materially different, that IS the refinement finding.

**Test 3 — insurance-EV end-to-end backtest (the money number).**
Simulate the Strategy-1 shape on history: for every historical runner in the $2–$10 band,
"place" a $25 insurance bet at the midpoint-at-off price with each seeded promo's terms
(FB-if-2nd, FB-if-2nd/3rd, cash-if-2nd; FB valued at 65%). Compare the engine's predicted
EV% against the realised average return over the sample. Slice by odds band. This is the
single most operator-meaningful output: "the tool predicted +X%, history delivered +Y% ± CI".

**Test 4 — live-pipeline spot-check (secondary).**
On the `betfair_snapshots` subset where BSP is stamped: near-jump midpoint vs BSP agreement,
and (where finish positions exist) a thin repeat of Test 1. Proves the LIVE feed the race
screen consumes behaves like the historical data the calibration ran on.

**Honesty rails:** state N per cell; no cell under N=200 gets a verdict; name selection
effects (the historical import is AU thoroughbred-weighted; snapshots are the operator's
followed races); dead-heats and scratchings excluded with counts reported; the FB-conversion
65% constant is TESTED (Test 3 sensitivity: rerun at 60/65/70/live-hedge) not assumed.

**Bound:** one job, read-only, no schema changes, no new capture. If a test can't run as
spec'd, report why rather than improvising a different test.

## Piece 3 — refinement verdict (written from piece 2)

Answers, in the operator's terms: (a) are the numbers on the race screen trustworthy enough
to execute on, where do they run hot/cold; (b) do we recalibrate the exponents/constants now,
and to what; (c) is any ongoing data collection worth it, or does the existing capture (which
runs anyway) accumulate everything needed; (d) recommended recalibration cadence, if any.

## Routing

Piece 2 runs as a bounded session against this spec (this session if budget allows, else the
next — the spec is self-contained on purpose). Findings triage per the inventory-first
cadence; operator-facing summary in plain gambling language. Adversarial review after piece 3.
Gate #10 sign-off is the operator's, on the evidence, at the end.
