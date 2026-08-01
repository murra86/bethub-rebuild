# Cycle linking backfill — insurance → FB → Betfair lay (S246, 20 Jul 2026)

**What changed for your betting day:** every insurance cycle now holds its
full story — the insurance bet, the free bet it triggered (where it
triggered), and the Betfair lay(s) hedging that free bet. Cycle nets in
the BetLog now read the true program result. The insurance program's
cycle-derived P&L is **+$686.16** (insurance legs −$210.00 + FB
conversion net of lays +$896.16 = 68.9% realized conversion on $1,300
face), matching the independent pairing analysis exactly.

## What was moved (32 rows, cycle_id only — no money fields touched)

- **3 FB conversion bets** re-homed to their true qualifier's cycle,
  resolved from the promo spine under the **effective-deploy rule**
  (only a deploy event not itself superseded counts as the real spend —
  superseded deploys are corrected/undone consumptions from the S243
  auto-select bug era and the void→restore→re-spend chain).
- **29 Betfair lays** joined the cycle of the back bet they hedge:
  23 by unique market+selection match; 6 by timestamp-nearest among
  same-runner candidates (three race-pairs where two books' FBs backed
  the same runner — five of the six pair to the exact minute the FB was
  placed, the sixth pairs by exclusion).
- One deliberate non-move: `bet-3b84ec36` consumed credits from TWO
  qualifiers at placement (the S243 bug, later corrected); under the
  effective-deploy rule its one real qualifier is the cycle it already
  sits in.

Full old→new map (reversible per row):
`cycle_linking_backfill_map.json` in this directory.
DB backup before the write:
`bethub-v3/data/bethub.db.bak-s246-pre-cyclelink-*`.

## Verification

- 29/29 lays now share a cycle with their back bet.
- 66 insurance cycles hold 120 bets (66 insurance + 27 FB conversions +
  27 lays); the 2 remaining lays hedge the 2 non-insurance FB bets.
- Cycle-derived program P&L equals the independent market+selection
  pairing analysis to the cent.

## Forward fix (commissioned same session)

B2 addendum item 10: the race-page quick-lay resolves its parent cycle
at placement (market+selection candidate shown in the confirm card) so
future lays land linked, not backfilled. FB→qualifier inheritance
already existed (Build 2 §5.5 Piece A) and needs no change.
