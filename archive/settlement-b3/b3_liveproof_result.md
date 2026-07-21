# B3 / B2 live-proof — RESULT (S227) — PASSED

**Run:** 2026-07-06 (S227), Adelaide-anchored per DR-021. Operator-supervised live-proof on the launched v3 app against **live Betfair, real money**.
**Outcome:** **PASSED.** The full lay money-loop is proven end-to-end on real money; the **B2↔B3 dependency is CLEARED** (B2 auto-settlement fully money-proven, B3 reconciliation money-proven). Both workers turned **OFF** at the end of the supervised window (operator-confirmed).
**Code state:** bethub-v3 HEAD `e2638fac` unchanged; the only working-tree code change this session is the stream read-buffer fix (`_stream_transport.py`, additive, no git writes); suite 1346 green. `BETHUB_RECONCILIATION_WORKER` on + `BETHUB_SETTLEMENT_WORKER` on **only during the supervised window**, both OFF now.
**Governing DRs:** DR-019 (money derives on read from `matched_stake`), DR-021, DR-032/033.

---

## 1. What was proven (two real bets, real money)

### Case A — matched lay → true-stake reconcile → true-money settle (B3 + B2)
- **Bet `434257406420`** — LAY $3.15 on *2. Aston Valhalla*, Shepparton (market `1.259750980`).
- Placed **unmatched** → landed `provisional_pending` / `pending`, `matched_stake=0` (the **P1 re-label** — the old bug wrote a terminal `final_partial matched_stake=0`).
- Matched on Betfair → a reconciliation pass wrote the **TRUE** values: `matched_stake 0→3.15`, `matched_price 2.56`, converged `provisional_pending → final_full`. **(B3 core fix, live.)**
- Settlement gate held it `pending` while the race was open (**P4 gate**). On race close the settlement worker resolved it: market `CLOSED`, `settled_time=null` — resolved correctly anyway (**S223 settled-signal fix, live**). Layed selection was the **WINNER** → **LAY inversion** → `settled_lost`. Money derived on read = liability `3.15 × (2.56−1) = −$4.91` — **real magnitude, NOT $0**. **(B2 + inversion, live.)**

### Case B — never-matched lay → held → park valve (P4 / HIGH-1 principle)
- **Bet `434257942837`** — LAY $8.33 on *1. Frankys Lass*, Shepparton (market `1.259750983`), left to lapse on the jump.
- Landed `provisional_pending`, `matched_stake=0`, unmatched 8.33.
- Reconciliation swept it **3 times across ~10 min (10:52→11:02)** and **never got a conclusive "lapsed / sizeSettled==0" signal** from Betfair cleared-orders → correctly **refused to guess** (the HIGH-1 principle: never `FAILED` without a conclusive never-matched signal).
- At attempt 3 + race-started, the **P4 park valve** fired: `settlement_state pending → provisional` (manual queue). `matched_stake` stayed **0.0** throughout — **no fabricated magnitude, no mis-settle, no HIGH-1 $0/FAILED misbooking. NOT auto-settled.**
- **This is the most important safety behaviour, proven on real money: when the system can't conclusively determine an outcome, it escalates to the operator rather than guess money.**

**Summary:**

| Case | Bet | Path | Result | Verdict |
|---|---|---|---|---|
| Matched | `434257406420` $3.15 | placed→matched→reconciled→settled | `settled_lost`, −$4.91 true money | ✅ B3 + B2 |
| Lapsed | `434257942837` $8.33 | placed→held→parked | manual queue, $0, never auto-settled | ✅ P4 valve |

## 2. Also confirmed live (en route)
- **Stream read-buffer fix** (this session): the 64 KiB overflow reconnect loop is gone; the stream reached SUBSCRIBED and held through two full sessions of live use + a restart. See `stream_read_buffer_overflow_fix_report.md`.
- **P1 / P4 gate / S223 / LAY inversion** all exercised on real Betfair data (above).

## 3. Findings surfaced live

- **F-LIVE-1 (real, NOT money-path, was mis-parked): promo-catalogue cross-thread SQLite 500.** `GET /api/v1/promos/catalogue` threw `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread` (`store/repositories/promos.py:189`, `promos.py:140`) under the running app's concurrent polling. This is **Finding 1 from S187/S189** (the per-request `get_db_connection` cross-thread class) — assessed at S189 as "does not trip live → park post-cutover." **It tripped live.** That call is now falsified: **Finding 1 comes OFF "parked" and becomes a real pre-cutover fix** (same storage-layer per-method-connection pattern that fixed its siblings S187/S188). Money-harmless (read path; the catalogue is empty B4; `/bets` reads stayed 200; workers unaffected). Do not chase mid-proof; scope a follow-up fix.
- **F-LIVE-2 (tuning question, operator-raised): a lapsed lay parks rather than auto-`FAILED`.** Betfair cleared-orders did not surface the lapse within the 3-sweep / ~10-min window, so the bet parked to the manual queue instead of auto-resolving to `FAILED`. **Observed: once parked (`settlement_state → provisional`), reconciliation did NOT re-sweep it** — attempts stayed at 3, `last_reconciled_at` unchanged (11:02:06) through app shutdown ~5 min later. So the park is terminal-pending-manual, not a way-station to a later auto-`FAILED`. Safety outcome is correct; the open question is whether to raise the attempt threshold (`UNRECONCILED_PARK_MIN_ATTEMPTS = 3`), lengthen the reconciliation window (cadence observed ~5 min/sweep), switch to a time-based window, or — **the deeper unknown** — whether a purely never-matched order *ever* appears in cleared-orders at all (if not, a bigger window never auto-resolves it and the real fix is an infer-lapse-from-absence signal). **Resolve by MEASUREMENT first:** place several lapsing lays, log if/when each clears + how long, then choose. Money-safe regardless (valve holds pending; settlement gated off it). Scope a small observation exercise → then a tuning/design decision.
- **S1 (residual, money-harmless): reconciliation leaves `bet_legs.matched_stake` stale on a post-placement match.** Case A's bet reconciled to `bets.matched_stake=3.15` but its leg row stayed `0.0`. Verified money-harmless — money derives on read from `bets.matched_stake` (`balance_derivation.py:142-144, SELECT … FROM bets`), settlement writes only state (no money magnitude), and nothing on the money/display path reads `bet_legs.matched_stake`. Same family as S226's R3. Candidate to harden later (propagate to the leg for consistency).
- **Parking-lot (UX): BetLog shows no detail for unmatched/pending bets.** A `provisional_pending` lay renders as "$0 at $0" (it renders `matched_stake`/`matched_price`, legitimately 0 until matched). Wanted: show requested stake + intended price + runner for unmatched/pending bets. Display-only, money-harmless, BetLog surface (S171 build).

## 4. Open items after this run
- **Operator manual-queue housekeeping:** one parked bet `434257942837` ($8.33 lapsed, genuine no-bet, $0) to clear from the manual PROVISIONAL queue at leisure.
- **Commit-time — DONE post-close (S227):** the B3 + stream work committed as local checkpoint `ede5ef9` (HIGH-2/LOW-5 resolved; `*.db.bak*` ignored; clean snapshot of the live-proven code). **Remaining git item:** off-machine backup — no remote; push pending operator GitHub login.
- **Follow-ups scoped above:** F-LIVE-1 (Finding 1 off-park → fix), F-LIVE-2 (cleared-orders clear-time measurement → park-threshold/design decision), S1 (leg-stake harden), BetLog unmatched-detail, plus the parked stream subscription-trim (`stream_read_buffer_overflow_fix_report.md` §6).

## 5. Close decision
**B3 fix-side + B2 auto-settlement are LIVE-MONEY-PROVEN. The B2↔B3 gate is CLEARED.** No money-path code change remains on this arc. The remaining cutover money-path blocker is **B1** (a fresh lay's full loop — exercised in passing today via Case A's live placement, but its own line), plus B4 promo-seed, B5 tunnel, B6 cutover mechanics, B7 monitoring. Both workers OFF; flags stay off until the next supervised context.

<!-- B3/B2 LIVE-PROOF PASSED (S227) — B2↔B3 cleared; workers OFF; follow-ups F-LIVE-1 (Finding 1 off-park), F-LIVE-2 (park-threshold measurement), S1 (leg stake), BetLog detail -->
