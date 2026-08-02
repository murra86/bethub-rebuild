# S264 adversarial review — `raceday-0x-0z` branch (56fa26b + 434685f, base 23ba696)

Reviewed 2 Aug in a linked worktree (live checkout/dist/DB untouched).
Suites at branch tip: pytest 2069 passed / 7 skipped, vitest 543, tsc
clean — all match the branch's claims. `npm ci` on a fresh checkout
needs `--legacy-peer-deps` (openapi-typescript@7.13.0 vs
typescript@6.0.3 peer conflict — pre-existing, note for fresh machines).

## Trial merge with main (cycle-accounting a34a21b + ab05dc4)

**Zero conflicts** — the feared `bets.py` feed-field collision
auto-merges (branch match_status/requested_price and main's
cycle_has_lay land in different regions, both survive in
`_to_feed_item`). Suites ON THE MERGED TREE: pytest 2113/7 skipped
(2069 + 44 cycle-audit), vitest 543, tsc clean. Resolution: plain
`git merge`.

## Findings

- **F1 HIGH CONFIRMED — replace route ignores `size_carried`.** The
  matched-stake refusal gates on the LOCAL row (lags exchange up to a
  sweep ~5 min). A partial match in the click window → replaceOrders
  cancels only the remainder; the matched fragment stays on the OLD id;
  the route re-points the row at the NEW id and the fragment's
  stake/liability never land in the row. Signal already in the response
  (`size_carried` < unmatched size) and unused. FIX BEFORE LIVE USE:
  on shortfall, refuse clean success + alarm with both ids. No test
  covers this shape.
- **F2 HIGH PLAUSIBLE — sweep can terminalize FAILED mid-replace.**
  Replace succeeds at Betfair → sweep reads old id as
  cleared_order_lapsed → writes FAILED conclusively →
  `update_exchange_order_reference` re-points betfair_bet_id WITHOUT
  checking/restoring match_status → row FAILED forever, new order live
  and unwatched (sweep selects PROVISIONAL* only). Seconds-wide window
  but live-money blind spot. FIX BEFORE LIVE USE: status-guard the
  UPDATE (`AND match_status IN ('provisional','provisional_pending')`)
  + refuse/surface if the sweep won.
- **F3 MED CONFIRMED — rejection can mean cancelled-not-replaced.**
  replaceOrders is cancel-then-place; place-leg failure = original
  order GONE, UI presents "row untouched". Timeout/503 may mean "it
  happened anyway" (new order, no row pointing at it — replace carries
  no customer ref). Not fully fixable client-side → live-use protocol.
- **F4 MED PLAUSIBLE — no tick-ladder validation on new_price** (0.01
  step allows off-tick e.g. 5.03 above 4.0; inherited exposure but
  replace raises the stakes per F3). Consider client-side snap via
  existing `tickLadder.ts` before first live use.
- **F5 LOW CONFIRMED — change-promo re-issue stamps occurred_at=now**
  (pre-existing engine behavior, 3× live-proven; 0x makes late
  corrections two-click-easy → tension with corrections-keep-original-
  economic-date grows). Operator awareness.
- **F6 LOW — cosmetic double asked-price label** on transient
  failed-not-yet-settled rows.
- **F7 LOW PLAUSIBLE — post-deploy FB re-arm ref survives FB-mode exit
  indefinitely** → much-later re-entry runs RELAXED auto-select.
  Operator-intent call.

## Verified clean
0x cross-kind refusal complete (both preview+apply, engine re-asserts
under BEGIN IMMEDIATE); 0z(d) touches unsettled bets only (no
retroactive re-true) and placement-verify demotes toward the sweep (safe
direction); requested_price display-only (no money-path reads); replace
refuses non-Betfair; FB re-issue = credit event, never P&L. Coverage
gaps: REPLACE_LOG_WRITE_FAILED, timeout/503, F1 shortfall shape untested.

## Verdict
**GO for the merge; FIX-FIRST F1+F2 (~15 lines total) before the
re-send button is used on live money.** F3/F4 = first-live-use protocol:

1. First use on a comfortably-unmatched order well before jump, at the
   prefilled asked price moved by whole ticks.
2. After clicking — and after ANY error/timeout — verify at Betfair
   directly that exactly one working order exists at the new price.
3. On a rejection, do NOT assume the old order still works — check
   Betfair (cancel-succeeded/place-failed leaves you off the market).
4. Confirm `size_carried` equals the full unmatched stake; shortfall =
   fragment matched on old id, reconcile by hand.
5. After the next sweep (~5 min), confirm matched figures track the
   NEW id.
