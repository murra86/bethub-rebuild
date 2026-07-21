# B3 — LAY money-path fix: adversarial verification report

**Verdict: DEFECTS FOUND — worst severity HIGH.**
The build's *core mechanisms are sound and well-tested* (P1 re-label, P4 gate + park valve, P2 worker wiring, and the settle-vs-reconcile race discipline all hold under attack). But there is **one CONFIRMED HIGH money-path hole** — the P3 cleared-orders fall-through re-creates the exact incident bug ($0 / FAILED) for the incident-class bet in a timing window, with **no self-heal** — and **one HIGH operator-coordination risk** (B3 is mechanically inseparable from the un-live-proven S222/S223 settlement-worker chain in the same dirty tree). Neither blocks turning the **reconciliation** worker on (money-safe), but both **must be closed before the `BETHUB_SETTLEMENT_WORKER` flag is flipped to real money**. Do not call this build SOUND: there is a proven path back to the target bug.

**Session:** independent adversarial verification (READ + run-tests only; no edits, no fixes, no git writes; `BETHUB_SETTLEMENT_WORKER` never set; no live Betfair; no money-move; DB not written). Method: full first-hand read of every P1–P4 site + a 5-agent adversarial fan-out (P3, P4, P1/mutation, P2/race, test-diff/dirty-tree), every returned finding re-verified against the code by the orchestrator.

---

## 0. Reproduce (not trust) — all confirmed

| Check | Report claim | Verified | Result |
|---|---|---|---|
| `git rev-parse HEAD` | `e2638fa` | ✅ | `e2638fac2c659783448bece9b1810294512068bf` |
| commits since HEAD | none | ✅ | `git log` top = `e2638fa` (S210); nothing committed since |
| stashes | none | ✅ | `git stash list` empty |
| working tree | dirty (S222 chain + B3 layered) | ✅ | 24 modified + 12 untracked, matches §5 manifest (see §5 below) |
| `uv run pytest` | 1327 passed, 1 xfailed | ✅ | **`1327 passed, 1 xfailed, 4 warnings in 6.23s`** — exact match |

The four §5-manifest new files exist (`clients/betfair_client/v1/cleared_orders.py`, `ui/api/reconciliation_worker.py`, and their tests); every "edited (additive)" file is present with a B3 hunk layered on the dirty tree. The 4 warnings are pre-existing `HTTP_422` deprecations, unrelated to B3. `racing.py` is a clean `+10 −1` pure-P1 change.

---

## 1. Findings (severity-ranked, file:line + concrete failure scenario)

### 🔴 HIGH-1 — P3 cleared-orders fall-through mis-FAILs the incident-class bet ($0 / void), no self-heal  ·  CONFIRMED (independently, twice)

**Where:** `workflows/bet_entry/v1/reconciliation.py` — Step 3.5 guard `:288`, fall-through Step 4-5 pre-settlement `matched_stake==0 → FAILED` at `:351-361` (and post-settlement equivalent `:416-431`), committed terminally at `:493`. Sweep exclusion `:470-476`. Real-REST `settled_time` is always `None` (`_translation.py:676-678`). Contributing mechanism: `run_reconciliation_pass:492` (see MEDIUM-4).

**Failure scenario (the incident bet, `434175139855`-shaped):** A quick-lay placed **0-matched** → P1 writes `PROVISIONAL_PENDING`, `matched_stake=0`, `requested_stake=4.98`. It matches in full (4.98) on Betfair, then the market settles and the order **clears out of `listCurrentOrders`**. On the reconciliation pass that first sees it absent:
1. `get_order_state` → synthesised absent snapshot (`matched_size=original_size`, `average_matched_price=None`) → Steps 2/3 skipped (price is `None`).
2. Step 3.5 `get_cleared_order_state` returns **either** `ReadUnavailable` (transient 500) **or** `found=False` (the bet has not yet propagated into `listClearedOrders` — a real Betfair current→cleared lag). The `isinstance(..., ReadOk) and .found` guard (`:288`) is False → the recovery block is skipped.
3. Step 4-5 `get_market_settlement` **succeeds**. On the real REST read path `settled_time` is `None` (S222/S223 established REST carries no `settledTime`; `_translation.py:676-678` reflects this), so the pre-settlement branch (`:338`) fires; `record.matched_stake == 0` → returns **`FAILED`, `matched_stake=0`** (`:351-361`).
4. `run_reconciliation_pass` writes it via `update_match_status` (`:493`). **`FAILED` is terminal and is excluded from the reconciliation sweep** (`statuses=(PROVISIONAL, PROVISIONAL_PENDING)`, `:470-476`) **and from the P4 park valve** (`list_stalled_unreconciled_bets` selects `PROVISIONAL*` only). The bet is now permanently marked `FAILED`/$0 with **no self-heal path** — neither reconciliation nor the valve will ever revisit it.

The lay **won**, but v3 books it as failed/void → **$0**. This is the *exact* symptom the whole fix was built to eliminate, reappearing inside **P3's own target window** (the design says P3 exists precisely for "a lay that clears before its first reconciliation pass"). It is CONFIRMED at the code level and reproducible by composing two currently-passing tests (`test_resolve_absent_pre_settlement_failed` + `test_resolve_absent_cleared_unavailable_falls_through`).

**Likelihood caveat (calibration, not exoneration):** the fall-through is only *reached* when the order is already absent from `listCurrentOrders`. For most bets an earlier 300 s pass catches the order in-orders (Step 3 → `FINAL_FULL`) first, so the exposed population is narrow — a lay placed close to off-time that matches and whose market settles inside one reconciliation window, on the one pass where the cleared read also misses. But the happy path (cleared read succeeds) is the *only* path tested, and when the conjunction hits, the loss is silent, terminal, and directional (a real winner booked at $0). Impact ⇒ HIGH.

**Fix direction (for the operator/next build, not applied here):** on the absent path, when `matched_stake == 0` **and** the cleared read was `ReadUnavailable`/`found=False`, return **no decision (carry-forward)** instead of `FAILED`, so the next pass retries once `listClearedOrders` populates — never terminalise the incident class off a missing signal. Add the missing negative test (MEDIUM-2). Persisting mid-flight `matched_size` (MEDIUM-4) further reduces the stale exposure.

### 🔴 HIGH-2 — B3 is mechanically inseparable from the un-live-proven S222/S223 settlement-worker chain in one dirty tree  ·  CONFIRMED

**Where:** shared files carrying **both** changesets: `workflows/bet_entry/v1/settlement.py`, `workflows/bet_entry/v1/betfair_adapter.py`, `clients/betfair_client/v1/_translation.py`, `ui/api/{config.py,main.py,dependencies/composition.py}`, `workflows/bet_entry/v1/__init__.py`, `ui/api/settlement_worker.py`. Whole P3/P2 surface is **untracked** (`clients/betfair_client/v1/cleared_orders.py`, `ui/api/reconciliation_worker.py`).

**Failure scenario (operator commit-time):** HEAD is `e2638fa` with nothing committed since; every production file is one unstaged modification. `settlement.py` alone interleaves the S223 settled-signal / winnerless-hold work (`market_winnerless_hold`, `settled_time`-gate removal) with the B3 P4 work (`exclude_match_statuses` gate `:1226/:1501`, `run_unreconciled_escalation_pass` `:1676`, `UNRECONCILED_PARK_MIN_ATTEMPTS` `:112`) in the same module and same `__all__`. Consequently: **committing B3 necessarily commits the S222/S223 chain, which has not had its operator-supervised live-worker run** (per governance, that is the sole open B2 step). Conversely, a whole-file `git stash` to isolate B3 tears the B3 hunks out of `settlement.py`/`betfair_adapter.py` — B3 will not build. And because the entire fix is uncommitted, any `git stash` / branch-switch / `git clean -fd` silently discards the whole money-path fix (untracked `cleared_orders.py` vanishes, leaving `reconciliation.py` importing a missing module). There is no clean way to land B3 alone. The operator must consciously accept this coupling (or do a careful interactive stage) before committing.

### 🟠 MEDIUM-1 — P3 recovery gate: `sizeSettled>0` with null `priceMatched` → FAILED/$0  ·  PLAUSIBLE

**Where:** `workflows/bet_entry/v1/reconciliation.py:290-293` — the cleared-won branch requires **both** `cleared.matched_size > 0` **AND** `cleared.average_matched_price is not None`; otherwise it drops to the lapsed branch (`:310-319`) → `FAILED, matched_stake=0`.

**Failure scenario:** `listClearedOrders` returns a SETTLED row with `sizeSettled=4.98` but `priceMatched` absent/null (an SP/BSP-persisted fill, or any response omitting `priceMatched`). `_translate_list_cleared_orders` → `price_matched=None`; adapter → `average_matched_price=None`, `matched_size=4.98`. Step 3.5: `matched_size>0` is True but the `AND` is False → **FAILED, $0** for a genuinely matched bet. No defensive fallback to `price_requested` or the stored price. PLAUSIBLE (LIMIT-PERSIST hedge orders normally carry `priceMatched`), but there is no guard. A live-proof / hardening item.

### 🟠 MEDIUM-2 — the incident-class fall-through (the HIGH-1 branch) is untested — green by omission  ·  CONFIRMED (test-quality)

**Where:** `tests/workflows/bet_entry/v1/test_reconciliation.py` — `test_resolve_absent_cleared_unavailable_falls_through` (`:533-555`) and `test_resolve_absent_cleared_not_found_falls_through` (`:499-530`) both build the record with `matched_stake=Decimal("50.00")` (>0), so the fall-through is only ever exercised where the stale stored stake is non-zero and Step 5 yields the *correct* `FINAL_FULL`. **No test drives `{matched_stake==0} + {cleared unavailable/found=False} + {settled_time=None}`** — the money-losing branch (HIGH-1). Compounding: the coupled acceptance test `test_gate_then_reconcile_then_settle_end_to_end` (`:3978`) **simulates** the reconciliation step with a manual `storage.update_match_status(FINAL_FULL, 4.98)` rather than driving `run_reconciliation_pass` through the cleared-orders path, so it structurally cannot catch a mis-FAIL either. This omission is *why* HIGH-1 is green in CI.

### 🟠 MEDIUM-3 — the PROVISIONAL-pass gate wiring has no pass-level test  ·  CONFIRMED (test-quality)

**Where:** `workflows/bet_entry/v1/settlement.py:1501` (`exclude_match_statuses` on `run_provisional_resolution_pass`). All provisional-pass tests build records with the `_make_record` default `match_status=FINAL_FULL` (`test_settlement.py:151`); none uses `PROVISIONAL_PENDING`. The PENDING-pass gate *is* covered (`test_settlement_pass_gate_excludes_provisional_pending:3796`), but the provisional pass is not.

**Failure scenario:** a regression dropping the `exclude_match_statuses` kwarg from line 1501 would let the provisional-resolution pass **auto-resolve a valve-parked bet** (`settlement_state=PROVISIONAL`, `match_status=PROVISIONAL_PENDING`) at its stale stake — defeating the load-bearing "parked, not auto-settled" invariant — and the full suite would stay green. A test asserting the provisional pass excludes a `PROVISIONAL_PENDING` row would close it.

### 🟠 MEDIUM-4 — reconciliation drops mid-flight `matched_size` while a lay stays `PROVISIONAL_PENDING`  ·  CONFIRMED (latent / contributes to HIGH-1)

**Where:** `workflows/bet_entry/v1/reconciliation.py:492` — `update_match_status` is called **only** `if decision.new_status != record.match_status`.

**Failure scenario:** a lay matching incrementally in-orders resolves to `still_pending_in_orders` → `new_status=PROVISIONAL_PENDING` each pass. Because that equals the current status, the `:492` guard **skips the write**, so the growing `snap.matched_size` (0 → 3 → 4.98) is **never persisted** — the DB `matched_stake` stays frozen at the placement value until a *terminal* transition. This is a pre-existing W6 guard, but P1 (which now routes these lays through the sweep as `PROVISIONAL_PENDING`) makes it live: it *guarantees* the stale `record.matched_stake` that Step 4-5 then trusts in the HIGH-1 fall-through. On its own it is masked by the P4 gate (the bet is held from settlement while `PROVISIONAL_PENDING`), so it only turns into money via HIGH-1 — hence MEDIUM. Persisting `matched_stake` on every pass (drop the status-equality guard around the stake write) would remove the stale-value amplifier.

### 🟡 LOW-1 — P3 multi-row-per-betId undercount  ·  PLAUSIBLE

`workflows/bet_entry/v1/betfair_adapter.py:337` takes `matching[0].size_settled` with **no summation**; `_build_list_cleared_orders_params` (`_translation.py:411-425`) never pins Betfair's `groupBy`. If `listClearedOrders` ever returns >1 `ClearedOrderSummary` for one `betId` (fragments 3.00 + 1.98), the resolver writes `matched_stake=3.00` and settles ~40% short. Betfair's default bet-level grouping normally yields one row per `betId` (hence LOW), but the code relies on that implicit default. Live-confirm item.

### 🟡 LOW-2 — "reconciliation never writes `settlement_state`" is not regression-locked  ·  CONFIRMED (test-quality)

No test asserts `run_reconciliation_pass` / `_resolve_one` leave `settlement_state` untouched. The money-safety invariant (reconciliation moves no money) is structurally true today but a future `update_settlement_state` call in the reconciliation path would ship green.

### 🟡 LOW-3 — valve threshold constant & SQLite event-start branch not pinned  ·  CONFIRMED (test-quality)

`UNRECONCILED_PARK_MIN_ATTEMPTS = 3` is not numerically locked — every escalation *pass* test references the symbol for both setup and expectation, so mutating the constant survives (only the SQLite query test pins a literal boundary). Separately, the production valve always calls `list_stalled_unreconciled_bets(older_than_event_start=started_at)`, but the only SQLite test (`test_bets.py:657`) omits that arg, so the SQLite `l.betfair_event_start_time < ?` isoformat-comparison branch (`bets.py:984-986`) runs unproven against SQLite (event-start hold is demonstrated only on the InMemory datetime path). Both LOW — the threshold is documented as calibratable, and the InMemory path exercises the logic.

### 🟡 LOW-4 — coupled acceptance assertion is loose  ·  CONFIRMED (test-quality)

`test_gate_then_reconcile_then_settle_end_to_end:4033` asserts `settlement_state in (SETTLED_WON, SETTLED_LOST)` where the deterministically-correct result for a lay-of-a-winner is `SETTLED_LOST`; a regressed lay inversion would pass this test. LOW because direction is separately locked by `test_resolve_lay_winner_settles_lost`.

### 🟡 LOW-5 — the operational-DB **backup** is stageable by `git add -A`  ·  CONFIRMED (operator hygiene)

The live DB is safe: `.gitignore` matches `*.db` / `*.db-shm` / `*.db-wal`, and `git check-ignore -v` confirms `data/bethub.db` (and sidecars) are ignored. **But** the untracked `data/bethub.db.bak-S222-20260703T194225` (225 KB of live bet rows) is **not** matched by any pattern — `git add -An data/` shows it *would* be staged. Operator: do **not** `git add -A` while committing B3; add a `*.db.bak-*` ignore. (No B3 write to the live DB: `bethub.db` mtime `16:18` predates the build window ~17:40–18:40; the `-shm` at `17:38` is a shared-memory touch from a read connection, with no change reaching the `.db` — consistent with the report's "no operational-DB write.")

---

## 2. What held under attack (positive confirmations)

- **P1 (re-label) — sound.** `racing.py:1114-1117`: `remaining<=0 → FINAL_FULL`, `remaining>0 → PROVISIONAL_PENDING`; `matched_stake` written unchanged. **Consumer sweep clean:** `balances/v1/balance_derivation.py` never reads `match_status` (branches on `side`); settlement lay detection is `side`-based; no money/UI figure changes wrongly when a not-fully-matched lay now surfaces as `PROVISIONAL_PENDING`. The provisional UI correctly shows these lays as pending. Report §0.B-B1 upheld.
- **P4 gate — sound, no bypass.** Only two settlement money-path callers of `list_unsettled_bets` (`settlement.py:1219` PENDING, `:1492` PROVISIONAL) and **both** pass `exclude_match_statuses=(PROVISIONAL, PROVISIONAL_PENDING)`. `list_provisional_settlement_bets` delegates *without* the exclude, but its only caller is the read-only `GET /v1/bets/provisional` UI endpoint (`provisional.py:281`) — reaches no settle path (and correctly surfaces parked bets to the operator queue). The SQLite `NOT IN` gate is **NULL-safe** because `match_status` is `TEXT NOT NULL` (`store/schema/bets.py:30`), so the SQLite-vs-InMemory NULL divergence is unreachable (REFUTED). The InMemory `reconciliation_attempts` `None`-crash is test-only (SQLite `COALESCE`s; the schema defaults 0) (REFUTED).
- **P4 valve — sound.** Parks `PENDING → PROVISIONAL` only (never auto-settles); `older_than_event_start=started_at` + `min_reconciliation_attempts=3` mean it **cannot fire on a healthy just-placed bet** (event not started, or <3 sweeps); it **self-heals** (reconciliation keeps sweeping the parked `PROVISIONAL*` bet; once terminal, the provisional pass settles it at the true stake); it **cannot permanently strand** (the only permanent-strand path is the un-caught HIGH-1 `FAILED`, which is a *reconciliation* defect, not a valve one). Runs only inside `settlement_worker_cycle`, i.e. only when `BETHUB_SETTLEMENT_WORKER` is on.
- **P2 (reconciliation worker) — sound.** Gate requires `betfair_mode=="live" AND reconciliation_worker` (opt-out, default ON), **independent of** `BETHUB_SETTLEMENT_WORKER`; mock mode never starts it; `BETHUB_RECONCILIATION_WORKER=false` disables it. **Startup cannot crash:** `_bring_up_reconciliation_worker` is wrapped in `try/except Exception` in `main.py`, and in live mode the streaming client is always non-None, so `RealBetfairAdapter.__post_init__` does not raise on a degraded stream (and the REST-based reconciliation reads don't need SUBSCRIBED). **Moves no money:** `run_reconciliation_pass` writes only match fields (`update_match_status`) + bookkeeping (`last_reconciled_at`/`attempts`) and **never** `settlement_state`; the sweep is `PROVISIONAL*` only, so it never touches a settled bet (no retroactive money change).
- **Race (settle vs reconcile) — the ordering guarantee holds.** The gate makes the two workers' populations **disjoint by `match_status`** (reconciliation sweeps `PROVISIONAL*`; settlement takes only terminal). `update_match_status` is a **single atomic row-write** coupling `match_status` + `matched_stake` + `matched_price` under `self._lock`, so settlement can never observe a torn "terminal status / stale stake" state: when it reads a bet as `FINAL_FULL`, the true stake is already committed in the same row. Terminal bets leave the sweep, so there is no concurrent modification of a settleable row and no retroactive change. The escalation valve and a reconciliation flip on the same bet self-heal in every interleaving. **The only hole in this otherwise-clean story is HIGH-1** (a mis-`FAILED` bet that no worker can recover).

---

## 3. Test-quality verdict

**Strong and non-vacuous on the happy paths, the gate, and the valve — weak precisely on the money-losing branch.**

- **Mutation-kills confirmed (by assertion inspection; no files edited, per boundary):**
  - P4 SQLite gate `NOT IN → IN` (`bets.py`): **killed** by `test_list_unsettled_bets_exclude_match_statuses_sqlite` — the gated set flips from `{"ff","fp"}` to `{"pp","pv"}`, failing `assert {...} == {"ff","fp"}`.
  - Valve query threshold `>=3 → >3`: **killed** by `test_list_stalled_unreconciled_bets_sqlite` (the `attempts=3` "stuck" row drops out, failing `== {"stuck"}`).
  - P1 boundary swap (`PROVISIONAL_PENDING`↔`FINAL_FULL`): **killed** by the `test_racing.py` mapping tests (unmatched→`PROVISIONAL_PENDING`, fully-matched→`FINAL_FULL`).
- **Genuinely exercises production (not mock setters):** `test_cleared_orders_translates_to_listClearedOrders` drives the real `TranslatingTransport` and verifies the JSON-RPC round-trip (request `betStatus`/`betIds`; response `betId/marketId/selectionId/sizeSettled/priceMatched/betOutcome` → snake_case → `ClearedOrderRecord`, `size_settled→matched_size`, `price_matched→average_matched_price`) — **field round-trip REFUTED as a defect.** `test_cycle_reconciles_provisional_pending_to_true_stake` drives the real worker cycle 0→4.98 `FINAL_FULL`.
- **The gaps that matter (all captured as findings above):** the incident-class fall-through (`matched_stake==0` + cleared-miss + `settled_time=None`) is untested (MEDIUM-2); the provisional-pass gate wiring is untested (MEDIUM-3); "reconciliation writes no `settlement_state`" is unlocked (LOW-2); the valve constant and the SQLite event-start branch are unpinned (LOW-3); one acceptance assertion is loose (LOW-4). **No silently-weakened assertion** was found in any *changed* test — the only diffs beyond pure additions are in `test_settlement.py`, and every changed assertion is a legitimate adaptation to the S222/S223/winnerless behaviour, not a hidden weakening. The five other changed test files are purely additive.

---

## 4. The P3 live-confirm — restated (the one contract-not-live-verified premise, now with sharper asks)

`listClearedOrders` is **contract-verified, not live-verified** — the fix trusts that Betfair's `ClearedOrderSummary` carries the true settled size/price. The supervised live-proof (report §4) **must** additionally confirm, beyond the report's existing steps:

1. **Field semantics:** for a real SETTLED lay, `sizeSettled` equals the true matched **backer stake** (what v3 stores as `matched_stake`) and `priceMatched` is populated — i.e. the recovered `matched_stake`/`matched_price` reproduce the v2-oracle values.
2. **One row per betId:** `listClearedOrders` filtered by a single `betId` returns exactly **one aggregated** `ClearedOrderSummary` (else `matching[0]` undercounts — LOW-1). If not, the adapter must sum `sizeSettled`.
3. **`priceMatched` present when `sizeSettled>0`** for every SETTLED fill shape you can produce (else MEDIUM-1 mis-FAILs a winner).
4. **★ The negative / lag case (HIGH-1) — the critical new ask:** deliberately reproduce the incident shape (a **0-matched** lay that matches then clears fast) and confirm that a reconciliation pass which catches it in the **absent-from-current-but-not-yet-in-cleared** window (or during a transient cleared-read failure) does **not** terminalise it to `FAILED`/$0. If it can (and the code says it can), harden the fall-through to carry-forward rather than `FAILED` **before** the settlement worker is ever flipped on. Verify by watching the row: it must converge to `final_full` with the **true** `matched_stake`, never `failed`.

Keep `BETHUB_SETTLEMENT_WORKER` **OFF** until step 4 passes. The **reconciliation** worker (money-safe) may be turned on first per the runbook — but note it is the reconciliation worker (on-by-default in live) that would commit the HIGH-1 mis-`FAILED`, so treat step 4 as gating for *it* too, not only for settlement.

---

## 5. Manifest cross-check & dirty-tree note

Working-tree file set matches report §5. New: `clients/betfair_client/v1/cleared_orders.py`, `ui/api/reconciliation_worker.py` + their tests (all **untracked**). Edited-additive B3 hunks confirmed in `racing.py` (P1), `bets.py`+`settlement.py`+`settlement_worker.py` (P4), `cleared_orders`/`_translation.py`/`__init__.py`/`orchestrator.py`/`betfair_adapter.py`/`reconciliation.py` (P3), `config.py`/`main.py`/`composition.py` (P2). Everything else in `git status` is the pre-existing S222/S223 settlement-worker chain (`record_builder.py`, `clients/betfair_client/v1/settlement.py`, `promos`, `post_settlement_void`, the settlement read-path F1–F4/C-5 in `_translation.py` and `settlement.py`) — **not B3**, and the coupling in HIGH-2 is that B3 and this chain share files and are uncommitted together.

---

## Bottom line

The engineering of P1/P2/P4 and the race discipline is careful and holds up; the gate and valve do exactly what they claim and are well-tested. **But the P3 recovery — the largest and hardest sub-part, and the one that directly targets the incident bet — has a confirmed fall-through that re-books the incident-class winner at $0/void when its cleared read misses, with no self-heal and no test.** Combined with the inseparable dirty tree, the honest verdict is **DEFECTS FOUND (worst: HIGH)**. The reconciliation worker is safe to trial per the runbook, but **do not flip `BETHUB_SETTLEMENT_WORKER` to real money until HIGH-1 is hardened (carry-forward, not FAILED) and its negative case is proven live (§4.4).**

<!-- B3 VERIFY COMPLETE -->
