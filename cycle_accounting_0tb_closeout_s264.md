# 0t-B CYCLE ACCOUNTING — CLOSE-OUT (Phase 7, S264, 2 Aug 2026)

## The operator's number

**308 / 308 cycles accurately tracked (100.0%) · 470 / 470 bets in
coherent cycles (100.0%) · DEFECTS: none · operator-confirmed lines: 0.**
The daily money check (`ops.settlement_review`) carries the same number
in its CYCLE ACCOUNTING section. Per review note R5, acceptance is
stated as ZERO DEFECTS — the percentage alone is never the criterion
(C6/C7 carry no cycle_id; quantization can print 100.0% at scale).

## Programme trail

- Phases 1–3 (`a34a21b`+`ab05dc4`): classifier + acceptance command +
  repair-residue NIL + daily-check section. Adversarial review
  (`cycle_accounting_phases123_review_s264.md`): GO; R1/R2/R3 fixed
  same session (`15edcd8` + post-impl tightening `fa68f60` — only
  positive-marker cycle moves confirm; no-op edits emit nothing; live
  scan = exactly the 34 historical repair moves pass).
- Phase 4 (`c57172d`): derived open/closed state (expiry/revoked close
  with markers, auto-reopen on late pay — no writes), close-date proxy
  incl. F2 (attributed cash credit joins the close max), all-in cycle
  net on BOTH money surfaces via one shared derivation.
- Phase 4 re-trues (`f34155d` + LIVE APPLY 13:50): the four 2-Aug
  replacement-credit dates re-trued to 1 Aug 23:07 ($56.25/$25.50/
  $22.50/$10.63 = $114.88; banked promo cash 1 Aug now $149.88, no
  2-Aug line). Backup `bethub-pre-creditdates-20260802-135019.db`
  verified holding the old dates; full-store diff = exactly 4
  occurred_at fields + 4 audit events; idempotent re-run clean.
- Phase 5 (`2ab9ed7`): BetLog "Group by play" toggle, `/v1/bet-cycles`
  whole-play window rule, F9 reconciling footer, CycleChain summary.
- Phase 6 (`2288d51`): D2 (one commission-share helper across all 7
  echoes + corrections + reassign preview), D5 (rejected/superseded
  manual credits marked), D7 (pending lay shows liability, not backer
  stake), D10 (settled cash exchange backs join market netting;
  soft-book backs never), §6e self-check relabel, (g) S231 haircut
  CODIFIED in `evEngine.ts promoEV` only ($6–$10 band −3pts, FB
  lay-hedge exempt, flagged-EV shown as soft bands — never realised
  P&L, warnings never block).
- Post-impl review of 4–6 (`post_impl_review_46_s264.md`): **CLEAN** —
  no confirmed defects; backup + live state verified to the byte;
  suites 2184 pytest / 558 vitest / tsc clean.

## Low notes carried (from the CLEAN review — no fix required)

1. F9 footer wording attributes any card-vs-strip gap to "other days
   inside whole plays"; an unattributed (account-anchored) credit
   would also create a gap — wording-only, truthful today (all 17
   live credits attributed).
2. `retrue_credit_dates` copies one reference hop — a
   chained replacement-of-a-replacement would inherit the middle date
   (moot for the applied four).
3. D10 trim mismatch: python strips book_or_exchange, the sibling SQL
   read doesn't (no padded rows exist; write path uses literals).
4. Whole-play member fetch caps at 500 bets/page (store-wide today:
   470).

## Open ends

- **D3 — OPERATOR DECISION PENDING (plan §9.4):** `book_correction`
  ledger adjustments are currently excluded from the headline P&L
  (lumped with day_0_opening; −$0.01 today, unbounded in principle).
  Proposal: split by reason and include book_correction in the
  headline. Skipped in the build because the decision list never
  carried it — confirmed the right call by the post-impl review.
- R7 ratify (provisional credits close plays — shipped D4-lockstep
  deviation): **RATIFIED S265 (3 Aug), risk weighed on live data** —
  zero under-review credits in the whole history (109 finalised /
  7 rejected), the state is burst-lane-visible while it exists, and
  read-time derivation re-opens the play the moment a credit is
  rejected. Revisit trigger recorded: if promo style shifts to books
  that routinely dispute/slow-walk credits (under-review becomes
  common), reconsider the stricter reading.
- C8 future-flag caveat is now RESOLVED in principle: the assign-cycle
  button writes the audited move (R2 fix), so an underivable pairing
  has a sanctioned confirmation path.
