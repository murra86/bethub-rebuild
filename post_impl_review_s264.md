# S264 post-implementation review — d5db700 (replace guards), 15edcd8 (cycle-audit confirmation), b53f091 (correct_matched_price)

Reviewed 2 Aug after live application of the Flemington R7 correction.
Suite 2138; live audit 306/306 · 466/466 · 100.0% · none ·
operator-confirmed 0; backup `bethub-pre-matched-price-20260802-124148.db`
verified: opens read-only, holds old 7.6 row, zero correction events —
genuine pre-change snapshot. Live proof the verb's real-diff event does
not confirm a pairing (audit still prints 0 confirmations with the
event present).

## Verdict: d5db700 CLEAN · b53f091 CLEAN · 15edcd8 FIX-NEEDED

- **P1 HIGH CONFIRMED — R1 filter narrowed but not closed.** The
  before==after discriminator is not unique to genuine cycle movers:
  `ops/correct_promo_chain.py:1334-1351` (account reassign) and
  `ops/correct_promo_selection.py:400-410` (promo re-point) both write
  operator bet_edited with before==after + cycle_id — in regular use
  (3 promo mis-picks to date; 4+ such events live). Under R1+R3 the
  latest such event would suppress C8/C2/timing flags on that bet.
  Latent masking channel, not a current mis-report (0 confirmations in
  play today; 42 events pass the filter, only 34 are real repair moves).
- **P2 MED CONFIRMED — a no-op generic edit confirms.** Empty-body /
  identical-value PATCH succeeds no-op and still emits an operator
  bet_edited with identical snapshots → passes the filter. 4-5
  empty-notes events of this shape already live (18-29 Jul).
- **FIX (commissioned same session):** positive move marker (notes
  shapes of cycle_move.py + repair_lay_cycles.py) instead of the
  identity heuristic; no-op edits emit no event; red tests for both
  masking shapes + regression pin for the 34 repair moves. Plus P3 LOW
  (recorded_at sorted as ISO text — breaks across ACST/ACDT; parse to
  datetime) and P5 INFO (verb's unsettled denylist → settled allowlist).
- **P4 LOW PLAUSIBLE (pre-existing):** `_translation.py:1283` — a
  present-but-null sizeCancelled raises in translation; absent defaults
  to 0.0 → false shortfall (fails loud in the safe direction).

## Checked out clean
F1 Decimal-safe, shortfall path updates everything the clean path does,
pre-guard makes stale-nonzero unreachable; F2 guard on both storages,
"not found" vs "terminal" distinguished, no silent-200 path; R2 single
BEGIN IMMEDIATE + rollback-on-refused-insert, before==after by
construction from the pre-UPDATE row; verb hand-reversible (re-run with
--price 7.6), all guards red-tested.
