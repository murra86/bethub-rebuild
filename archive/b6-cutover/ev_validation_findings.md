# EV validation findings — pieces 2 + 3 of the validation arc (v2)

**Executed:** Session 231, 2026-07-06, per `ev_validation_commission.md`. **v2** — reissued
after the fresh-eyes adversarial review (filed verbatim at
`dr029/ev_validation/adversarial_review.md`); the v1 run was extended and re-run end-to-end
with the reviewer's required slices and checks. Everything below is from the v2 run:
script, raw output, and per-test CSVs archived at `dr029/ev_validation/` (v1 retained).
Read-only against capture.db throughout.
**Sample:** 16,889 historical races (12 months to 2026-02-28), 162,985 runner-results;
13,866 races with full finishing order (134,805 runners); 45,656 simulated insurance bets.
Excluded and counted: 25 win-market dead-heats/voids, 141 fields under 5 (see caveat C4),
5 bad-price races. Place dead-heats measured: 44 races (2nd), 47 (3rd) — ~0.7%, kept in.
Finish-position semantics verified: fp==1 agrees with Betfair's WINNER on 99.58% of rows.

---

## Headline verdict

**The engine's probabilities are genuinely well calibrated, and the EVs are safe to execute
on with one band-specific correction: treat $6–$10 screen EVs as ~3 points generous.** In
the $2–$6 range — the heart of the working band — screen EVs are accurate to slightly
conservative (reality paid a touch MORE than predicted). The model's constants were re-fitted
from scratch and the current values held. No new data collection is needed.

## Test 1 — are the win chances true?

Across 20 probability bands on 162,985 runners, the largest predicted-vs-actual gap was
0.7 points; the engine's midpoint method matched Betfair's own starting price for accuracy.
What this honestly tests (reviewer point accepted): the *shape* of the probabilities — that
favourites and longshots are each priced true relative to the field. It passes cleanly:
no favourite-longshot bias worth naming, EXCEPT a small one inside $6–$10 (predicted 13.17%
win, actual 12.76% — the source of the band correction below).

## Test 2 — the place chances the insurance promos pay on

On 134,805 runners with known finishing order: chance-of-exactly-2nd within 0.8 points
everywhere; exactly-3rd within 0.6; the 2+3 insurance shape within 1.1. Ten of forty bins
miss by more than chance — real, small miscalibations, both directions. **Where they sit
matters (v1's "errors in your favour" claim was WRONG and is retracted):** in the
highest-refund-chance decile (short-priced runners, $2–$4), the tool OVERSTATES the 2+3
refund chance by ~0.8 points ≈ half an EV point on an FB promo. The 2nd-through-4th shape
is the weakest (±2.5 points) — no current promo uses it; treat any future 2-3-4 promo EV
as ±3 points.

**Constants (claim corrected):** the refit is low-powered — the fitting surface is nearly
flat, so it *loosely constrains* rather than confirms. For what it's worth: gamma re-fitted
to exactly 0.770 (current: 0.77), delta 0.60 (current 0.62), epsilon 0.55 (current 0.48,
small sample). What genuinely constrains the constants is the Test 2 tables above — and they
say the current values produce place chances true to within a point. **Keep all three.**

## Test 3 — the insurance backtest (read this honestly)

**This is an internal-consistency check, not an achievable return.** Bets are priced at
Betfair-fair midpoint; no real book pays that. It proves the promo arithmetic composes
correctly with the probabilities — it does NOT prove "+21% was historically available".
Your real edge on any bet depends on the actual book price vs fair, which the screen prices
per bet. With that frame, on 45,656 simulated $2–$10 insurance bets (FB at 65%):

| Band | Promo example (FB if 2nd/3rd) | Predicted | "Paid" | Read |
|---|---|---|---|---|
| $2–$4 | FB 2nd/3rd | +25.2% | +25.0% | accurate |
| $4–$6 | FB 2nd/3rd | +23.0% | +24.5% | ~1.5 pts conservative |
| $6–$10 | FB 2nd/3rd | +19.4% | +16.4% | **~3 pts generous** |

The same pattern holds for every promo shape (it comes from the base bet leg, one shared
observation — not four independent confirmations). **Operational rule: haircut $6–$10
screen EVs by ~3 points; take $2–$6 at face.** Statistically the $6–$10 gap is ~1.8σ —
borderline alone, but the win-calibration table shows the same signal independently.

**Free-bet valuation (operator-locked S231):** 65% stays (general realised ~70%; 74.8% was
the $5-specific case). Sensitivity: each 5c of real conversion ≈ +0.9 EV points on FB promos
— so realised results on free-bet refunds should run slightly ahead of screen.

**Suspected inflation mechanism — tested and CLEARED.** The reviewer hypothesised the
no-lay fallback (a rival with no lay price silently inflating your runner's EV) drove the
optimism. v2 tested it directly: races where every runner has a clean lay show the *same*
lean (+12.22 pred / +11.37 paid), and fallback races are only 655 of 16,889. The fallback
is not the cause; the $6–$10 signal is residual favourite-longshot bias in that band. The
reviewer's logic point stands, though: the ledger's "conservative by construction" applies
to the flagged runner only — a no-lay rival nudges YOUR number up, and the ⚠ flag sits on
the rival. Parked as a candidate engine-hardening item (low priority: fallback races are 4%
of the sample and showed no measurable lean).

## Test 4 — the live feed (now properly archived)

Re-run inside the archived v2 script (v1's numbers reproduced): across 7,978 live-captured
races, the typical runner's near-jump implied chance agrees with BSP within 1.1 points
(median). The tail is fat — p99 ≈ 29 points, thin markets. **The ~ and ⚠ confidence flags
are load-bearing; never execute on a flagged EV as a firm number.** Note honestly: the
backtest population included fallback runners, so the validated numbers cover the whole
board; the flags exist for per-runner reliability, not because flagged EVs were shown wrong
in aggregate.

## Piece 3 — the refinement verdict

- **(a) Trustworthy?** Yes, with the band rule: $2–$6 at face (if anything slightly
  conservative); $6–$10 minus ~3 points; flagged runners treated as rough guides.
- **(b) Recalibrate?** No. Current constants held under refit and calibrate within a point.
- **(c) More data?** No new collection. The running VPS capture accumulates everything used
  here. The one gap worth closing with time (not a project): more ordinal-finish races will
  sharpen the $6–$10 estimate and the 4th-place shape automatically.
- **(d) Cadence:** re-run the archived script (~1 hr, one command, read-only) every ~6
  months, after any engine change, or if live results drift from screen EVs during the
  proving window and beyond.

## Caveats register (v2)

- **C1** — Test 3 is internal-consistency; real returns depend on book price vs fair
  (assumption 7, operational, untestable from this data).
- **C2** — the $6–$10 haircut is ~1.8σ; two independent views agree but it's an estimate,
  not a constant. Watch it against real results during the proving window.
- **C3** — ~18% of races lack full finishing order and drop from Tests 2/3. v2 checked for
  bias: the dropped races' win calibration is indistinguishable from the kept ones (T1e vs
  T1f). Faller/DNF composition remains unquantified — noted, small.
- **C4** — fields under 5 runners (141 races) are excluded, and the live engine DOES price
  4-or-fewer-runner fields. Place probabilities there are unvalidated. Rare in practice;
  treat tiny-field insurance EVs with suspicion.
- **C5** — fp↔winner disagreement 0.42% (dead-heats + data noise); place dead-heats ~0.7%
  of races, kept in (promos pay dead-heats by house rule — check terms when one lands).
- **C6** — sample is the 12-month AU historical import; jurisdiction/code composition not
  broken out.

**Next:** operator's gate-#10 call on this evidence.
