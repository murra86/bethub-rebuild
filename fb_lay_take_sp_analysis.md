# FB lay "Take SP" backtest — should unmatched FB-hedge lays convert to BSP at the jump?

**Date:** 2026-07-14 (S240) · **Status:** research only, no code/money-path changes
**Commissioned:** operator, S240 — "take the SP route… but let's run the analysis first to confirm"
**Data:** all 19 FB back↔Betfair lay cycles in `bethub-v3/data/bethub.db` (8–14 Jul 2026), BSPs from
VPS capture (`runners.sp_fixed` / final-snapshot `bsp_price`) filled from Betfair's official BSP CSVs
(`promo.betfair.com/betfairsp/prices/dwbfpricesauswin*.csv`) for the 8–11 Jul capture-outage markets.
Wide sample: 13,798 runners, last 45 days of capture, last pre-jump (≤5 min) best-lay vs settled BSP.

## Verdict: take SP. On our own data it recovers ~$61 across the two real partial fills and costs ~nothing.

## Mechanism (confirmed against Betfair docs, S240 conversation)

- "Take SP" is a **pre-jump instruction**: persistence `MARKET_ON_CLOSE` at placement (already supported
  by `clients/betfair_client/v1/placement.py`), or flipped later on an unmatched bet via `updateOrders`
  (endpoint NOT in our client yet). At the in-play transition Betfair converts the unmatched remainder
  to an SP bet. No in-play action ever needed.
- **Liability is preserved, never increased.** The remainder's liability at the limit price is the
  ceiling; stake resizes to `V/(BSP−1)`. Consequence for an FB hedge: **win-side lock is identical to
  plan regardless of BSP; lose-side floats but can never go negative.**
- Floor: remainder liability must be ≥ ~$10 or the SP bet is cancelled at the off. Market must be BSP
  (`bspMarket` catalogue flag; AU thoroughbred WIN yes).

## Cycle-level results (19 paired cycles)

- **16 fully-matched cycles: unaffected.** SP conversion only ever touches an unmatched remainder.
- **Capital Asset (11 Jul):** lay 38.34 @ 6.60, only $5.00 matched, runner lost. Actual **$4.60**.
  Take-SP (BSP 6.00): **$38.95** — beats even the planned full-fill lock ($35.27) because BSP came in
  under the limit. Recovery: **+$34.35**.
- **Catch The Red Eye (11 Jul):** lay 38.91 @ 15.50, only $4.81 matched, runner lost. Actual **$4.43**.
  Take-SP (BSP 15.00): **$31.18** vs planned $35.80. Recovery: **+$26.75**.
- **Aged Care (14 Jul, SETTLED 14 Jul — checked 20:23 ACST, S241):** lay 41.21 @ 11.0. The $6.44
  jump-time partial went on to match **in full** (remainder matched under default PERSIST;
  reconciled final_full 15:15 ACST, Betfair bet 434950526068). Runner lost → lay won: actual
  **$37.91** (41.21 × 0.92 after 8% commission) = the full planned lock. Take-SP counterfactual
  **$35.62** → take-SP would have **cost $2.29** here — first live instance where the queue
  filled and persistence beat SP. This is the expected give-back case, not a counter-argument:
  take-SP trades a small haircut when the queue fills (this, −$2.29) against the stranding tail
  (Capital Asset +$34.35, Catch The Red Eye +$26.75). Note the selective-fill asymmetry
  (in-play matching tends to select winners) did not bite this time.
- **Paw Lonnie (14 Jul): $50 FB, NO lay ever placed, lost → $0.** Different failure mode — persistence
  can't fix a lay that was never placed, but *placing* the lay at target price with Take-SP set and
  walking away would have. Worth folding into the same build decision.

## Wide sample: the "cost" of SP is usually negative

Last pre-jump best-lay vs settled BSP, 13,798 runners, 45 days, all captured races:

| lay-price band | n | BSP ≤ pre-jump lay | median BSP/lay |
|---|---|---|---|
| 1.5–4 | 1,153 | 98% | 0.875 |
| 4–8 | 2,511 | 99% | 0.833 |
| 8–15 | 2,828 | 100% | 0.786 |
| 15–30 | 2,720 | 100% | 0.733 |

BSP almost never lands above the closing lay offer — the SP pool prices without the book spread. A
converted remainder therefore usually fills at odds **no worse than the last instant-lay price**, and
when BSP lands under the limit price the lose-side lock comes out *ahead* of plan (Capital Asset did
exactly this). Caveats: snapshot is 0–5 min out (spreads still narrowing); thin markets have small SP
pools; comparison is vs the *closing* lay offer, not vs the operator's limit.

## Strategy comparison ("keep bet" persist vs take SP)

Persist fails **selectively**: an in-play lay matches mostly when the horse travels well, so persist
covers the winners and strands the losers — precisely the $0-FB outcome. An unmatched winner does pay
more (full FB winnings, no lay), so persist has higher variance with occasional jackpots; take-SP
maximises conversion consistency, which is the S231-locked objective (65% FB conversion baseline).

## Recommended build (needs its own fenced brief + operator sign-off — placement money path)

1. Third at-jump option "Take SP" in the HedgeModal dropdown (client enum already exists), **default
   for free-bet lays** on BSP markets; guard: remainder-liability ≥ $10 note, `bspMarket` check.
2. Phase 2 (optional): `updateOrders` endpoint + T-minus-X flip sweep for sitting unmatched bets.
3. Settlement verification pass: SP fills return different price/stake via cleared orders; B3
   reconciliation paths need a red/green test with an SP-converted bet. Non-runner + SP conversion is
   a known API edge — include in tests.

Analysis artifacts: session scratchpad `fb_sp_extract.py` / `fb_sp_compute.py` / `cycles_computed.json`
(session-temporary; re-derivable from the two databases + Betfair CSVs).
