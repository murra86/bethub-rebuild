# F-LIVE-2 lapse-timing measurement — RESULT (S228) — CONCLUSIVE

**Run:** 2026-07-06 (S228), Adelaide-anchored per DR-021. Operator-supervised: four real lays placed to lapse across four venues; a read-only out-of-band watcher polled Betfair every 15s (`listCurrentOrders` + `listClearedOrders` under all four `betStatus` buckets). App running live throughout (reconciliation worker ON, settlement worker OFF). Watcher script: session scratchpad `lapse_watcher.py`; raw log `lapse_watch_s228.log` (scratchpad); the full timeline is reproduced in the table below and the app-side rows in the live store.
**Outcome:** the F-LIVE-2 "deeper unknown" is **ANSWERED, decisively — 5/5 data points.** A purely never-matched order **DOES** appear in Betfair cleared-orders, reliably within **~1–2 minutes of the jump** — but under **`betStatus=LAPSED`**, a bucket the app never queries.

---

## 1. The finding in one line

The app's 3-sweep/~10-minute reconciliation window was never too short — the resolver was asking the wrong question. `RealBetfairAdapter.get_cleared_order_state` (`workflows/bet_entry/v1/betfair_adapter.py`) calls `listClearedOrders` with **`betStatus="SETTLED"` only**; a never-matched lay is filed by Betfair under **`LAPSED`** and is therefore invisible to the resolver forever, no matter how long the window. S227's Case B park (bet `434257942837`) was this exact mechanism.

## 2. The measurement

| Bet (all LAY, all never-matched) | Venue | Lapse stamped by Betfair | Visible in cleared/LAPSED by | Latency (≤) |
|---|---|---|---|---|
| `434260117747` Bradford $5.21 | Pakenham | 12:05:43 | 12:07:32 | ~110s |
| `434260134513` Day To Remember $2.82 | Barcaldine | 12:15:03 | 12:17:05 | ~122s |
| `434260152246` Regal Spencer $7.04 | Shepparton | 12:18:11 | 12:19:18 | ~67s |
| `434260182977` Regal Vanguard $10.42 | Wangaratta | 12:22:41 | 12:24:22 | ~101s |
| `434257942837` Frankys Lass $8.33 (S227 Case B, checked retrospectively) | Shepparton | 2026-07-06 10:53:45 | present when first queried S228 | n/a (historical) |

Consistent shape across all five: the order leaves `listCurrentOrders` within seconds of the jump, then appears in `cleared/LAPSED` ~1–2 min later with `size_settled=0`, `size_cancelled=<full stake>`, and a `settled_date` stamping the lapse moment. It **never** appears under `SETTLED`, `CANCELLED`, or `VOIDED` (watched continuously; zero hits).

## 3. Recommended fix shape (design decision, not yet built)

Small, bounded resolver change — **money-path, so full brief + adversarial-verify discipline applies**:

1. In the reconciliation resolver's inconclusive branch (`matched_stake==0`, absent from current orders, no SETTLED hit), **also query `listClearedOrders` with `betStatus=LAPSED`** (bet-id filter). A LAPSED hit with `size_settled==0` is the **conclusive never-matched signal** HIGH-1 demands → resolve `FAILED` (genuine $0 no-bet) instead of parking.
2. **Keep the P4 park valve unchanged as the backstop** for the genuinely inconclusive residue (Betfair unavailable, neither bucket answers). The valve stays the safety floor; it just stops catching the common case.
3. Edit surface: `betfair_adapter.py` (add a LAPSED read or parameterise the existing one) + `reconciliation.py` `_resolve_one` inconclusive branch + tests. Both resolvers should be checked for the same SETTLED-only assumption per the S223 sweep-the-class rule.
4. Timing note: LAPSED filing lags the jump by ~2 min; reconciliation cadence (~5 min) already exceeds that — no cadence change needed. `UNRECONCILED_PARK_MIN_ATTEMPTS=3` can stay.

## 4. Housekeeping from this run

- The four measurement lays will hit the park valve (3 attempts) and land in the manual PROVISIONAL queue alongside S227's `434257942837` — **five** parked $0 no-bets for the operator to clear at leisure. (The LAPSED fix will not retro-resolve already-parked bets; parked rows are terminal-pending-manual by design.)
- Watcher was read-only (list calls only, own Betfair session, app session/stream undisturbed — confirmed: stream held SUBSCRIBED throughout).
- Also live-confirmed en route this launch: the F-LIVE-1 promo fix (catalogue 200s + nine promos in the picker — **F-LIVE-1 now live-proven**) and the B4 seed (operator-confirmed display; EV-accuracy eyeball deferred to a later check).

<!-- F-LIVE-2 MEASUREMENT CONCLUSIVE (S228) — lapsed orders file under betStatus=LAPSED within ~2min; resolver queries SETTLED only; fix = LAPSED read as conclusive never-matched signal, park valve stays backstop; NOT YET BUILT -->
