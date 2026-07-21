# B3 — LAY money-path fix (design proposal)

**Session:** S225 design pass (operator-reviewed). Follows `b3_lay_settlement_investigation_report.md` (root cause CONFIRMED first-hand; all 4 gaps CLOSED in the S225 governance triage, §10 of that report).
**Type:** **Read-only design proposal** for operator review — no code touched, no test changed, no flag flipped, no design locked, no DB/Betfair write. A build commission follows on approval.
**Codebase:** bethub-v3 @ HEAD `e2638fa` (byte-identical; an in-flight settlement-worker **dirty tree** touches several of the files below — a coordination precondition, §8).
**Anchor:** 2026-07-05 ACST (DR-021).
**Governing DRs:** DR-032/033 (Betfair settlement spine / data-source roles), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-019 (derived state on read), DR-021 (Adelaide anchors).

---

## 1. The problem (fully grounded)

A Betfair **lay placed via the quick-lay route** (`place_lay`, `ui/api/routers/racing.py`, "Path A") can match *after* the placement HTTP call returns. Path A records only the placement-instant matched size as a **terminal** status and **nothing ever revisits it**, so the store's `matched_stake` stays frozen. Settlement then derives money from the stale value → **correct win/loss direction, wrong (often $0) magnitude.** Confirmed live: bet `434175139855` placed 0-matched, matched 4.98 on Betfair, won — v3 booked $0.

The investigation established the fix is **not** a single change. Four facts interlock:

- **F1 (primary).** `place_lay` writes a not-fully-matched lay as terminal `FINAL_PARTIAL` with frozen `matched_stake` (`racing.py:1105-1109`); the reconciliation sweep only takes `PROVISIONAL`/`PROVISIONAL_PENDING` (`reconciliation.py:416-423`) → the bet is never reconciled.
- **F2.** The live periodic worker runs settlement + provisional passes only — **no `run_reconciliation_pass`** (`settlement_worker.py:68-85`) → even reconcilable bets aren't swept in the live config.
- **F3.** The resolver's absent-from-orders path trusts the **stored** `matched_stake`, not a live value, and the adapter provides no live matched-size for an absent order (`betfair_adapter.py:262-267`) → naively feeding these bets into reconciliation can flip a real match to `FAILED`.
- **F4.** Settlement selects on `settlement_state` only, **no match-status gate** (`bets.py:838`) → it will settle a not-yet-trustworthy row, and it races any reconciliation worker.

**Design consequence:** a durable fix must (a) make Path-A lays reconcilable, (b) actually run reconciliation, (c) recover the *true* matched size even when the order has cleared, and (d) stop settlement from acting until the match state is trustworthy. Drop any one and you trade the $0 bug for a `FAILED` mislabel or a settle-vs-reconcile race. This is why the "obvious one-liner" (just broaden the sweep) is the most dangerous option in isolation.

---

## 2. What the fix must achieve (acceptance shape)

For any lay, before it settles, the store's `matched_stake`/`matched_price` must equal what actually matched on Betfair; and settlement must not run on a lay whose match state has not yet been reconciled to a trustworthy terminal value. Proven by re-running the S224 scenario live: an unmatched lay that matches on Betfair must settle with the **true money**, and a lay that genuinely never matches must resolve to `FAILED`/void — never to a wrong stake.

---

## 3. The coupled fix — four parts

*(A one-time backfill of the single mis-valued live row `434175139855` was considered and **dropped**: the test bet log will be cleared at live-proof, so correcting it now is wasted effort — operator direction, S225.)*

### P1 — Placement: stop writing a terminal label for a not-fully-matched lay `[maps R1]`
`place_lay` (`racing.py:1105-1109`): keep `FINAL_FULL` when `remaining <= 0` (genuinely fully matched at placement — terminal is correct); when `remaining > 0`, write **`PROVISIONAL_PENDING`** (not `FINAL_PARTIAL`). This puts unmatched/partially-open lays into the population reconciliation sweeps, and — critically — makes `FINAL_PARTIAL` mean only one thing again ("finished with a genuine partial match"), removing the ambiguity F3/P4 depend on.
- `matched_stake` at placement stays the placement-instant matched size (0 or the partial); reconciliation converges it.
- **Software call (recommended):** re-label at the source (P1) rather than broadening the reconciliation sweep to include `FINAL_PARTIAL`. Re-labelling keeps the terminal statuses terminal and avoids re-opening genuinely-finished partials.

### P2 — Run reconciliation: wire the periodic worker `[the original B3]`
G3 confirmed nothing reconciles in the live config. Wire `run_reconciliation_pass` as a periodic background worker, **mirroring `settlement_worker.py`** (gate → cycle → handle → loop → start), interval `DEFAULT_RECONCILIATION_INTERVAL_SECONDS` (300 s), off the event loop via `asyncio.to_thread`, one-bad-pass-logs-and-continues, cancel-and-await teardown. Expose the already-built `RealBetfairAdapter` on `app.state` via a cached `_betfair_adapter()` factory (needs client + audit_sink + operator_identity; note `RealBetfairAdapter` hard-requires a streaming-equipped client). Order the reconciliation bring-up **before** the settlement worker in the lifespan.
- **Posture (locked earlier):** on-in-live + kill switch — `reconciliation_worker: bool = True` binding `BETHUB_RECONCILIATION_WORKER` (opt-out), gate `betfair_mode == "live" and settings.reconciliation_worker`. Independent of `BETHUB_SETTLEMENT_WORKER`.

### P3 — Recover the true matched size for a cleared order `[maps R4 — the largest part]`
G2 confirmed: once a matched lay clears out of `listCurrentOrders`, `get_order_state` synthesises `matched_size=original_size, price=None` and the resolver falls back to the **stale stored stake**. To recover truth in that window, add a **`listClearedOrders` read** to the adapter and consult it in `_resolve_one`'s absent-from-orders path (before the market-settlement disambiguation), using the cleared order's real `sizeMatched`/`averagePriceMatched`.
- **Phasing note (see §5):** while a lay is still matched-and-current (the common pre-race case), reconciliation already recovers the true stake via the in-orders branch (`reconciliation.py:251-265`) with no cleared-orders read. P3 covers the narrower window where the order clears before any reconciliation pass runs (e.g. a lay placed close to off-time that matches and the market settles quickly).

### P4 — Gate settlement on a trustworthy match state `[maps R3]`
Settlement must not act on a lay until its match state is reconciled-terminal. Add a **match-status predicate** so settlement only takes bets whose `match_status` is a trustworthy terminal (`FINAL_FULL`, post-P1 genuine `FINAL_PARTIAL`, or `FAILED`) — i.e. **exclude `PROVISIONAL`/`PROVISIONAL_PENDING`** from the settlement sweep (`list_unsettled_bets`, `bets.py:838`).
- **Safety valve (required):** a bet that can never reconcile (no `betfair_bet_id`, or persistently `read_unavailable`) must not stall unsettled forever nor be settled at a stale stake. Use the existing `reconciliation_attempts` / `last_reconciled_at` columns to **escalate to operator-manual** (park, not auto-settle) after a bounded attempt count / age. Compose with the existing winner-less-hold / park machinery in `settlement.py`.
- **Software call (recommended):** gate at the query level (cleanest, one predicate) rather than inside the resolver.

---

## 4. The end-to-end flow after the fix

Place lay (partly/unmatched) → **`PROVISIONAL_PENDING` / `PENDING`** (P1). Periodic worker (P2) reconciles: still-matching-in-orders → recovers true stake via in-orders branch; cleared → recovers via cleared-orders read (P3) → **`FINAL_FULL` with the true `matched_stake`** (or `FAILED` if it genuinely never matched). Only once terminal-and-trustworthy does settlement act (P4), deriving the **true money**. A lay that never reconciles is parked to manual, never silently mis-settled.

---

## 5. Coupling & a phasing option (Cat-5 call surfaced)

**These parts are coupled.** P1 without P4 could let a still-`PROVISIONAL_PENDING` lay settle at a stale stake; P1 without P3 can flip a matched-then-cleared lay to `FAILED`; P2 without P1 sweeps nothing new. The safe target is **P1 + P2 + P3 + P4 together**.

**Phasing option (operator's call).** If you want the common case closed sooner, a defensible phase-1 is **P1 + P2 + P4** (re-label + wire worker + settlement gate): this makes Path-A lays reconcilable, actually reconciles them while they're in-orders (the common pre-race window), and *blocks settlement until they're terminalised* — so the worst case degrades to "a lay that clears before its first reconciliation pass gets parked to manual" (P4's safety valve), **not** a wrong settle. P3 (cleared-orders) then lands as phase-2 to remove that manual-park edge.
- **My recommendation:** build the full P1–P4 set. But if timeline pressure forces a split, phase-1 = P1+P2+P4 is safe *because P4 fails closed* (park, don't mis-settle). Do **not** ship P1+P2 without P4 — that's the combination that can mis-settle or `FAILED`-flip.

---

## 6. Open design decisions for the operator

1. **Full fix vs phase-1 (P1+P2+P4) first** — §5. Recommend full; phase-1 acceptable only with P4's park-not-settle valve.
2. **Settlement safety-valve thresholds** — after how many `reconciliation_attempts` / what age does an un-reconcilable bet escalate to manual rather than keep retrying? (Proposed default: park after the bet's event has started AND N≥3 attempts with no terminalisation — tune during build.)
3. **Reconciliation mechanism** — periodic worker (recommended, P2) vs consuming the live `orderSubscription` for real-time `matched_stake` updates. Stream-consumption removes the reconcile latency entirely but adds streaming-boundary plumbing (DR-030); recommend periodic now, stream as a later optimisation.

---

## 7. Blast radius & risks (per part — implementer must verify)

- **P1:** grep every consumer of `FINAL_PARTIAL` / `FINAL_FULL` for lays (balance derivation, UI provisional/《bets》surfaces, any sweep) — confirm none assumes an unmatched lay is `FINAL_PARTIAL`. Provisional UI (`GET /bets/provisional`) will now correctly show these lays as pending.
- **P2:** shared `SQLiteBetRecordStorage` is concurrency-safe under two worker threads (verified). Adapter factory is a heavier mirror than `_settlement_reader` (3 deps) and inherits the streaming-client requirement.
- **P3:** new Betfair client surface (`listClearedOrders`) — respect DR-032/033 (Betfair-only settlement spine) and the client boundary (DR-030). Risk of mis-classifying `FAILED` vs `FINAL_FULL` — cover with tests for cleared-won, cleared-lapsed, and never-matched.
- **P4:** risk of stalling settlement for un-reconcilable bets → the safety valve (decision 2) is load-bearing; must be tested (structural-anomaly bet with no `betfair_bet_id`).

---

## 8. Coordination precondition — the dirty tree

The investigation flagged uncommitted modifications in the working tree to `record_builder.py`, `settlement.py`, `betfair_adapter.py`, `clients/betfair_client/v1/settlement.py` and others — the **in-flight settlement-worker / post-settlement-void work** (the S222–S224 money-path fix chain, `BETHUB_SETTLEMENT_WORKER` still OFF). This design anchors to HEAD `e2638fa`, but P1–P4 will land **on top of** that dirty tree and P3/P4 touch some of the same files. **Before building:** confirm whether the dirty changes already moved any anchors here, and decide whether to commit/stash that in-flight work first so B3 lands on a clean base. This is an operator/Code-session coordination call, not resolved here.

---

## 9. Proof plan (S189 — fixtures ≠ live-proven)

1. **Unit/integration (green before ship):** P1 status mapping; P2 lifespan start/teardown; P3 resolver branches (cleared-won / cleared-lapsed / never-matched) using the adapter's cleared-orders read; P4 gate excludes PROVISIONAL* and the safety-valve parks an un-reconcilable bet.
2. **Live re-prove (the real bar), supervised:** place an unmatched lay, let it match on Betfair, confirm the worker reconciles it to the true `matched_stake` **before** it settles, and it settles with the **true money**. Then a lay left to lapse must resolve `FAILED`/void, not a wrong stake. Worker(s) supervised, OFF at close.

---

## 10. Boundaries / disciplines

Design proposal only — **no code, no tests, no flags, no DB/Betfair write, no git write ops.** HEAD stays `e2638fa`. Bet-safety (Cat 4): the eventual build touches placement-labelling, a new Betfair read, settlement gating, and a live-row backfill — all money-path; `BETHUB_SETTLEMENT_WORKER` stays OFF until the coupled fix + backfill are built and live-proven. DR-030 boundaries, DR-032/033 settlement spine, DR-019 derived-on-read, DR-021 anchors respected.

---

## 11. Recommended next step

On approval, convert this into a **build commission** (or a phased pair per §5), landed on a clean base per §8, with the proof plan §9 as the gate. Keep the worker OFF until the live re-prove passes.

*Read-only design proposal — no code touched; bethub-v3 byte-identical at `e2638fa`; dirty tree unchanged.*
