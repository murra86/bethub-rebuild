# B3 — LAY money-path fix (build report)

**Session:** S226 build (CAUTIOUS — verify-first). Implements `b3_lay_settlement_fix_design.md` (P1–P4, coupled) after re-grounding its premises first-hand.
**Codebase:** bethub-v3 @ HEAD `e2638fa` (unchanged; **no git write ops**). Built **on top of** the in-flight settlement-worker dirty tree (§0.C) — no commit/stash/discard.
**Anchor:** 2026-07-05 ACST (DR-021). **Flags:** `BETHUB_SETTLEMENT_WORKER` left **OFF**; no place/settle/money-move; all DB reads that were needed were satisfied from source, not the operational DB.
**Result:** P1–P4 built + unit/integration green (`uv run pytest` → **1327 passed, 1 xfailed**, was 1289 at start → **+38 tests**). Live re-prove left as an operator runbook (§4). **Do NOT flip the settlement worker until §4 passes.**

---

## 0. Phase-0 validation (the hard gate) — result: **CLEAN, proceeded**

All three checks were run first-hand against the working-tree source at `e2638fa`. Nothing tripped; the design's premises hold. Details:

### 0.A — Re-ground the five mechanics (all CONFIRMED first-hand)

| # | Premise | Verdict | Evidence (working tree) |
|---|---------|---------|-------------------------|
| A1 | `place_lay` writes a not-fully-matched lay **terminally** as `FINAL_PARTIAL`; nothing revisits it | ✅ CONFIRMED | `racing.py:1105-1109` — `FINAL_FULL if remaining<=0 else FINAL_PARTIAL`; `matched_stake=matched_size` (placement-instant) |
| A2 | Reconciliation sweep takes **only** `PROVISIONAL`/`PROVISIONAL_PENDING` | ✅ CONFIRMED | `reconciliation.py:416-423` — `list_unreconciled_bets(statuses=(PROVISIONAL, PROVISIONAL_PENDING))` |
| A3 | The live worker runs **no** reconciliation pass | ✅ CONFIRMED | `settlement_worker.py:68-87` — cycle runs `run_settlement_pass` + `run_provisional_resolution_pass` only |
| A4 | Resolver absent-path + adapter give **no** live matched-size for a cleared order | ✅ CONFIRMED | `betfair_adapter.py:257-269` synthesises `matched_size=original_size, average_matched_price=None`; `reconciliation.py:284-377` then trusts stored `record.matched_stake` (L3) |
| A5 | Settlement has **no** match-status gate | ✅ CONFIRMED | `bets.py:list_unsettled_bets` WHERE keys on `settlement_state` only |

### 0.B — Challenge the four risk points (all resolved; none tripped a STOP)

- **B1 — Does re-labelling `FINAL_PARTIAL → PROVISIONAL_PENDING` break a consumer?** **No.** Grepped every `FINAL_PARTIAL`/`FINAL_FULL`/`match_status` consumer in `workflows/ store/ ui/ domain/ clients/`. The money/UI surfaces branch on **side**, not match_status: balance derivation (`balance_derivation._is_lay`), settlement lay detection (`settlement._is_lay_bet`), and the provisional-bets UI (`bets.py:283` keys on **settlement_state** `pending/provisional`, not match_status). No consumer assumes an unmatched lay is `FINAL_PARTIAL`. Re-labelling only (a) admits the lay to the reconciliation sweep (intended) and (b) surfaces it in `GET /bets/provisional` as pending (correct). `PROVISIONAL_PENDING` is already a persisted value the orchestrator writes (Trigger B), so no schema/enum surprise.
- **B2 — Can the P4 gate strand a settleable bet?** **No.** The gate excludes only `PROVISIONAL*` match state (untrustworthy). Terminal states (`FINAL_FULL`, genuine `FINAL_PARTIAL`, `FAILED`) pass through and settle exactly as before. Path-B PROVISIONAL bets that previously *could* have auto-settled unreconciled are now correctly held → reconciled (P2) or parked (valve). The park safety valve (§3.P4) removes the only permanent-strand path.
- **B3 — Does `listClearedOrders` actually return real matched size?** **Yes, by API contract** — Betfair `ClearedOrderSummary` carries `sizeSettled` (matched backer stake) + `priceMatched` + `betOutcome`. `_connection.py:50-51` already names `listClearedOrders` as an available endpoint. This is **contract-verified, not live-verified** — I cannot call live Betfair under the boundaries. Flagged as the one item the operator must confirm on the live re-prove (§4); fixtures cover cleared-won / cleared-lapsed / not-found / unavailable in the meantime.
- **B4 — Does the post-fix handoff hold (reconcile writes match fields only; settlement_state stays PENDING)?** **Yes, CONFIRMED.** `bets.py::update_match_status` writes only `match_status/matched_stake/unmatched_stake/matched_price`; reconciliation additionally calls `update_reconciliation_bookkeeping` (`last_reconciled_at/attempts`). Neither touches `settlement_state`. So a reconciled lay stays `PENDING` and becomes eligible for the (now gated) settle pass once terminal. Proven end-to-end by `test_gate_then_reconcile_then_settle_end_to_end`.

### 0.C — Dirty-tree collision (reported; **layered, not disturbed**)

`git status` at entry showed the expected in-flight settlement-worker work (S222–S224 chain): modified `settlement.py`, `betfair_adapter.py`, `record_builder.py`, `config.py`, `main.py`, `composition.py`, `clients/betfair_client/v1/{settlement.py,_translation.py}`, `workflows/bet_entry/v1/__init__.py`, `ui/api/routers/promos.py` + untracked `settlement_worker.py`, `post_settlement_void.py`, `credit_gap.py` and their tests.

**Collision with my edit sites: YES**, at `config.py`, `main.py`, `composition.py`, `betfair_adapter.py`, `settlement.py`, `_translation.py`, `__init__.py`, `settlement_worker.py`. **Handling:** every edit was made against the **working-tree (dirty) version** and is purely **additive** (new params with safe defaults, new functions, new branches, new imports) — it does not rewrite any dirty hunk. HEAD stays `e2638fa`; the dirty tree is byte-preserved except for my additive layers. No commit/stash/discard performed (DR boundary honoured). The baseline dirty suite was green before I started (52/52 on the two worker/reconciliation suites) and the full suite is green after.

**Conclusion:** Phase 0 clean → proceeded to the full coupled P1–P4 build.

---

## 1. What was built (P1–P4, coupled)

### P1 — Placement re-label (`ui/api/routers/racing.py:1105-1117`)
`place_lay` now writes `PROVISIONAL_PENDING` when `remaining > 0` (was `FINAL_PARTIAL`); keeps `FINAL_FULL` when `remaining <= 0`. Two lines + rationale comment. This is the source fix: a not-fully-matched lay is now reconcilable, and `FINAL_PARTIAL` regains its single meaning ("finished with a genuine partial").

### P2 — Reconciliation periodic worker (`ui/api/reconciliation_worker.py`, new)
Mirrors `settlement_worker.py` exactly (gate → cycle → handle → loop → start), driving `run_reconciliation_pass` at `DEFAULT_RECONCILIATION_INTERVAL_SECONDS` (300 s) off the loop via `asyncio.to_thread`, one-bad-pass-logs-and-continues, cancel-and-await teardown.
- **Config:** `reconciliation_worker: bool = True` binding `BETHUB_RECONCILIATION_WORKER` (opt-**out**). Reconciliation moves no money — it only corrects stored match state — so it is safe-on-in-live, **independent of** `BETHUB_SETTLEMENT_WORKER`. Gate: `betfair_mode == "live" and settings.reconciliation_worker`.
- **Composition:** new cached `_betfair_adapter()` factory exposed as `app.state.get_betfair_adapter` (builds `RealBetfairAdapter(client, audit_sink, operator_identity)`; inherits the streaming-client requirement, satisfied in live mode).
- **Lifespan (`main.py`):** reconciliation is brought up **before** the settlement worker and torn down in the `finally`, with the same fail-safe (a start error is logged, never aborts startup).

### P3 — Recover true matched size for a cleared order
- **Client (`clients/betfair_client/v1/cleared_orders.py`, new):** `list_cleared_orders(rest_client, bet_status="SETTLED", market_id=?, bet_id=?)` → `ClearedOrderList` of `ClearedOrderRecord` (carries `size_settled`, `price_matched`, `bet_outcome`). Mirrors `current_orders.py`.
- **Translation (`_translation.py`):** additive `_ORDERS_CLEARED_RE` + request branch (`listClearedOrders`, `betStatus` + `betIds`/`marketIds`) + response branch (`clearedOrders → orders`). New helpers `_build_list_cleared_orders_params` / `_translate_list_cleared_orders`. Exported from the client `__init__.py`.
- **Adapter (`betfair_adapter.py`):** `get_cleared_order_state(*, market_id, selection_id, bet_id) → ReadOutcome[ClearedOrderStateSnapshot]`. Not-found → `found=False` (caller falls through).
- **Protocol/type (`orchestrator.py`):** `ClearedOrderStateSnapshot` + `BetfairAdapter.get_cleared_order_state`.
- **Resolver (`reconciliation.py::_resolve_one`, new "Step 3.5"):** in the absent-from-current-orders path, **before** the market-settlement disambiguation, consult cleared orders. `found + sizeSettled>0 + price` → `FINAL_FULL` with the **true** stake (`cleared_order_fully_matched`); `found + sizeSettled==0` → `FAILED` (`cleared_order_lapsed`); **not-found or unavailable → fall through** to the existing Step 4-5 (P3 only ever *adds* recovery, never removes it). This is the direct fix for the incident bet (`434175139855`: placed 0-matched, matched 4.98, cleared — previously mis-resolved to stale-$0/`FAILED`).

### P4 — Gate settlement on a trustworthy match state + park safety valve
- **Query predicate (`bets.py`):** `list_unsettled_bets` gains `exclude_match_statuses: tuple[str,...] = ()` (Protocol + both impls; SQL `AND match_status NOT IN (...)`). Default `()` → every existing caller byte-identical. Both `run_settlement_pass` and `run_provisional_resolution_pass` pass `_UNTRUSTWORTHY_MATCH_STATUSES = (PROVISIONAL, PROVISIONAL_PENDING)` → neither pass ever derives money from an unreconciled row. Settlement-park bets (dead-heat / removed-runner / winner-less hold) are `FINAL_*` match state, so they are unaffected and still resolve.
- **Safety valve (`settlement.py::run_unreconciled_escalation_pass`, new):** a pure-DB pass that parks genuinely un-reconcilable bets to the manual `PROVISIONAL` queue (never auto-settle). Query: new `bets.list_stalled_unreconciled_bets` (`match_status IN PROVISIONAL* AND settlement_state=PENDING AND reconciliation_attempts >= N AND event started`). Threshold **`UNRECONCILED_PARK_MIN_ATTEMPTS = 3`** AND `event_start < now` (design decision 2 default; documented as calibratable). **Fails closed** — below threshold the bet stays PENDING and reconciliation keeps trying; at/above it it is parked, not settled. It is **self-healing**: reconciliation keeps sweeping the parked bet (the sweep ignores `settlement_state`), so if it later terminalises, the provisional-resolution pass settles it with the true stake. Wired into `settlement_worker_cycle` (runs only when `BETHUB_SETTLEMENT_WORKER` is on — exactly where the stale-settle risk it guards exists). New reason code `provisional_unreconciled_escalation`.

**End-to-end flow after the fix:** place lay (partly/unmatched) → `PROVISIONAL_PENDING`/`PENDING` (P1). Reconciliation worker (P2): still-in-orders → true stake via the in-orders branch; cleared → true stake via `listClearedOrders` (P3) → `FINAL_FULL` (or `FAILED` if never matched). Settlement acts only once terminal (P4 gate), deriving true money. A bet reconciliation can never terminalise is parked to manual (P4 valve), never mis-settled.

### Design deviations from the proposal (all documented, none reduce safety)
1. **The valve needed its own query.** The design recommended "gate at the query level (one predicate)." Honouring that literally makes the settle pass never *see* the untrustworthy rows, so the park valve — which must inspect them — required a **second, dedicated** read (`list_stalled_unreconciled_bets`) and a **separate pass** rather than an in-resolver branch. Both mechanisms are independently fail-closed. This is the cleanest way to satisfy "predicate on `list_unsettled_bets` excluding PROVISIONAL* **plus** a park valve" without coupling them.
2. **Valve lives in the settlement cycle, not the reconciliation cycle.** Parking writes `settlement_state` (a settlement concern) and only matters when auto-settlement is active, so it belongs with — and is gated by — the settlement worker. Keeps the B4 handoff invariant intact (reconciliation still writes match fields only).
3. **Backfill of `434175139855` deliberately omitted** — per the design (the test-bet log is cleared at live-proof). Not built.

---

## 2. Tests (Phase 2) — all green

`uv run pytest` → **1327 passed, 1 xfailed** (+38 over the 1289 baseline). New/added:

- **P1 mapping** (`tests/ui/api/test_racing.py`, +3): fully-matched → `FINAL_FULL`; unmatched (matched=0) → `PROVISIONAL_PENDING` (not `FINAL_PARTIAL`); partial → `PROVISIONAL_PENDING`.
- **P2 worker** (`tests/ui/api/test_reconciliation_worker.py`, new, 12): gate matrix (default-ON opt-out, independent of settlement flag), one real cycle reconciling `PROVISIONAL_PENDING`+stale-0 → `FINAL_FULL`+true stake, empty-store no-op, start/stop lifecycle, loop-survives-failure, lifespan doesn't-start-in-mock + start-failure-fail-safe.
- **P3 cleared orders**: client + JSON-RPC translation round trip (`tests/clients/betfair_client/v1/test_cleared_orders.py`, new, 7); adapter branches (`test_betfair_adapter.py`, +3: settled→true, absent→not-found, 503→unavailable); resolver branches (`test_reconciliation.py`, +4: cleared-won recovers true stake **without** consulting settlement, cleared-lapsed→FAILED, not-found falls through, unavailable falls through).
- **P4 gate + valve**: settlement gate excludes PROVISIONAL* / settles terminal; valve parks stalled / holds below-threshold / holds before-event-start / ignores terminal & non-PENDING (`test_settlement.py`, +6); SQLite storage predicates (`test_bets.py`, +2); **coupled integration** gate→reconcile→settle proving true-stake settlement + the PENDING handoff (`test_settlement.py`, +1).
- **Mock/harness**: `MockBetfairAdapter` gained `get_cleared_order_state` (default not-found) + setters; `settlement_worker_cycle` test updated for the 3-tuple return.

**Lint:** my new files (`cleared_orders.py`, `reconciliation_worker.py`, and the new tests) are **ruff-clean**. Pre-existing ruff findings on the dirty/HEAD code (e.g. the dirty tree's now-unused `RunnerSettlement` import in `settlement.py`; 35 pre-existing findings in `orchestrator.py` at HEAD including UP037/I001) were **left untouched** — the project does not gate on ruff, and disturbing the dirty tree is out of bounds. I introduced **no new** ruff errors.

---

## 3. Boundaries honoured

HEAD stays `e2638fa`; **no git write ops** (incl. the dirty tree — layered additively, nothing committed/stashed/discarded). `BETHUB_SETTLEMENT_WORKER` left **OFF**. No place/settle/money-move performed; no live Betfair call. No operational-DB write (the `mode=ro` triage from the investigation was already closed in §10 of the report; no new DB access was required for the build). DR-030 module boundaries, DR-032/033 Betfair settlement spine (the new read is a Betfair-only settlement-adjacent read via the client boundary), DR-019 derived-on-read, DR-021 Adelaide anchors respected.

---

## 4. Operator live-proof runbook (the real bar — NOT run here)

Do this **supervised**, then flip the flag only if it passes. Reconciliation can be turned on first (money-safe); auto-settlement last.

1. **Pre-flight (readers only, no settle):** deploy the build to the live host. Leave `BETHUB_SETTLEMENT_WORKER` **off**. Set `BETHUB_RECONCILIATION_WORKER` on (default) and `BETHUB_BETFAIR_MODE=live`. Confirm the log line `Reconciliation worker opted in ... starting periodic match-state reconciliation passes.` and that streaming reaches SUBSCRIBED.
2. **Reproduce the incident shape:** place a small **lay** that is **unmatched or partially matched** at placement (like `434175139855`). Confirm the store row is `match_status=provisional_pending`, `settlement_state=pending`, `matched_stake` = placement value.
3. **Let it match on Betfair**, then watch a reconciliation pass. **Confirm B3-B3:** `listClearedOrders` returns the real `sizeSettled`/`priceMatched` (this is the one contract-not-live-verified premise). Confirm the row converges to `final_full` with the **true** `matched_stake` — via the in-orders branch if still current, or the cleared-orders branch (`cleared_order_fully_matched`) if it cleared first.
4. **Only then** turn `BETHUB_SETTLEMENT_WORKER` on (supervised). Confirm: (a) while the lay was `provisional_pending` the settlement pass did **not** touch it (gate); (b) once `final_full`, it settles with the **true money** (not $0).
5. **Negative case:** place a lay left to **lapse** (never matches). Confirm it resolves to `FAILED`/void with the correct stake, never a wrong magnitude.
6. **Valve case (optional, forced):** simulate an un-reconcilable bet (e.g. a persistent read failure); confirm that after `reconciliation_attempts >= 3` and event start it is **parked to the manual `PROVISIONAL` queue** (`provisional_unreconciled_escalation`), never auto-settled.
7. **Close:** turn both workers **OFF** at the end of the supervised window. Record results back into governance. Backfill of any real mis-valued row (only `434175139855` known) remains a separate audited Cat-4 step.

**Do not leave either worker running unsupervised until step 4–5 have passed on real data.**

---

## 5. File manifest (all working-tree; HEAD unchanged)

**New:** `clients/betfair_client/v1/cleared_orders.py`, `ui/api/reconciliation_worker.py`, `tests/clients/betfair_client/v1/test_cleared_orders.py`, `tests/ui/api/test_reconciliation_worker.py`.
**Edited (additive):** `ui/api/routers/racing.py` (P1); `store/repositories/bets.py`, `workflows/bet_entry/v1/settlement.py`, `ui/api/settlement_worker.py` (P4); `clients/betfair_client/v1/{__init__.py,_translation.py}`, `workflows/bet_entry/v1/{orchestrator.py,betfair_adapter.py,reconciliation.py}` (P3); `ui/api/{config.py,main.py,dependencies/composition.py}` (P2). Plus the test files listed in §2. (Several of these were already in the dirty tree; my changes layer on top.)

<!-- B3 BUILD COMPLETE -->
