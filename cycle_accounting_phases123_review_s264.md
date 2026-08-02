# S264 adversarial review — cycle accounting 0t-B phases 1–3 (a34a21b, ab05dc4)

Reviewed 2 Aug. Every ship claim re-verified live: acceptance re-run
today = 306/306 cycles · 466/466 bets · 100.0% · zero defects · zero
operator-confirmed; pre-repair replay on
`bethub.db.pre-layrepair-20260802-095251` = 339 · 305 · 90.0% ·
C1×32 C2×2 (exact repair population); suite 2097; classifier consulted
by no placement/settle/credit path; D1 fence at the single winnings
site; D4 status filter correct with red tests.

## Findings

- **R1 HIGH CONFIRMED (repro'd): any plain operator edit
  "operator-confirms" a pairing.** `_operator_moves`
  (`workflows/bet_entry/v1/cycle_audit.py:288-317`) accepts EVERY
  `bet_edited` with source=operator + non-null cycle_id — and the
  generic BetLog edit endpoint stamps cycle_id on every edit, stake
  corrections included (49/49 live operator bet_edited events carry it;
  4 live bets latently "confirmed", one FB via an S254 stake edit).
  Repro: an underivable wrong-runner pairing flags C8, then a stake-edit
  event shape flips it to "coherent — operator-confirmed". Violates
  normative amendment F1; a route for 100.0%-while-wrong. FIX: accept
  only genuine move-shaped events (before==after snapshot or move-note
  marker) + the missing red test (stake edit must NOT confirm).
- **R2 HIGH CONFIRMED: the sanctioned fix writes no audit record.**
  The assign-cycle button calls `update_cycle_id` — raw UPDATE, no
  `bet_edited` event; the only writer of the confirmation shape is the
  34-move-hardcoded `ops/repair_lay_cycles.py`. So a future C8 fixed by
  button flags FOREVER (no sanctioned resolution) and button moves are
  un-audited. Exact inversion: deliberate placements leave no record;
  unrelated stake edits do. FIX: assign-cycle door writes the audited
  bet_edited move in the same transaction (forward-linker L2 pattern).
- **R3 MED CONFIRMED: stale confirmation wins** — an older move into
  the current cycle confirms even if a newer move placed the bet
  elsewhere. Subsumed by R1's tighter filter.
- **R4 MED PLAUSIBLE: bijection distortion** — confirmed pairings not
  removed from `_order_consistent_matching`'s pool; ≥2 lays on one
  (market, selection) with one manual pairing can false-flag a correct
  neighbour C8. Rare; informational-flag noise only.
- **R5 LOW-MED CONFIRMED: percentage blind spots** — C6/C7 (cycle_id
  None) never dent cycle_pct; ROUND_HALF_UP means ≥2000 cycles could
  print 100.0% at 1999/2000. Mitigated: both surfaces gate on
  `report.clean`. Write into Phase 7 close-out: acceptance = "zero
  defects", never "the percentage says 100.0".
- **R6 LOW: voided-lay-only cycle** reads silently coherent with a
  contradictory census label (zero live rows).
- **R7 LOW (ratify): provisional credits close plays** — disclosed
  D4-lockstep deviation from plan §1.3 letter; a qualifier-lost play
  with credit under review shows in no OPEN CYCLES list (backstop =
  burst-review lane). Operator-semantics call, unsigned.

## Verdict

**GO for phases 4–6.** R1+R2 are REQUIRED before Phase 7 sign-off AND
before the next manual pairing (neither touches money paths or phase
4–6 surfaces). Foundation verified sound.
