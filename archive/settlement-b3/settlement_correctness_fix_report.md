# Report — settlement-correctness fix: BUILT, tested, backfilled, re-proven (worker stays OFF)

**Session type:** Execution of the LOCKED design `settlement_correctness_fix_design.md` (S222).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (dirty tree — the in-progress settlement-worker build — plus this change; **HEAD unmoved, no git write op**).
**Date:** 2026-07-03 ACST (DR-021).
**Outcome:** All operator-locked decisions built exactly. Full suite **1257 passed, 1 xfailed**. The repro LAY backfilled to `pending` (one row, backup taken). Re-proven against the real bet: the fixed resolvers settle it to the **correctly inverted** LAY state for every possible Gossamer Glow outcome, and the money-path invariant holds (the pre-fix silent overpay is closed). `BETHUB_SETTLEMENT_WORKER` remains **OFF**. The one step not auto-executed — the concrete *live* Betfair read of which way Gossamer Glow ran — is deferred to the operator's supervised live-proving window (reasons in §5).

---

## 0. TL;DR

- **Pending-state = Option A, exactly as locked.** `build_hedge_bet_record` now stamps
  `settlement_state=SettlementState.PENDING` at create (Betfair/hedge leg only). `build_soft_book_bet_record`
  and `build_manual_bet_record` untouched — soft-book stays NULL / manual. Then a **targeted one-row backfill**
  moved the existing repro LAY from NULL → `pending` (backup first; `changes()=1`; reversible).
- **LAY inversion in BOTH resolvers, as locked.** `side==LAY` inverts only the clean terminal states —
  WINNER→SETTLED_LOST, LOSER→SETTLED_WON — in `_resolve_settlement_for_bet` **and**
  `_resolve_provisional_for_bet`. VOIDED, the winner-guard park, and BACK mapping are byte-unchanged.
- **Dead-heat / material-reduction lays PARK**, reusing the existing guard (no reduced-liability maths), as locked.
- **Tests land together and pass:** create-path (hedge→PENDING, soft-book→None), a SQLite-path end-to-end sweep
  (builder-created LAY → swept from the real SQLite store → SETTLED_LOST), LAY tests for both resolvers, and the
  pre-existing BACK + F2 tests stay green.
- **Re-proven** against the real backfilled bet through the real code + store; **money-path invariant confirmed**
  (dangerous case now books −L, not +collect).
- **Worker OFF** throughout; **bethub-v3 HEAD unmoved**; no git write.

---

## 1. What was built (the locked decisions, 1:1)

### 1.1 Option A — create-path PENDING stamp (hedge builder only)

`workflows/bet_entry/v1/record_builder.py` — `build_hedge_bet_record`'s `BetRecord(...)` return now carries
`settlement_state=SettlementState.PENDING` (+ a design-referencing comment). `SettlementState` was already
imported. `build_soft_book_bet_record` (stays NULL) and `build_manual_bet_record` (terminal-only) untouched.

### 1.2 LAY inversion in both resolvers

`workflows/bet_entry/v1/settlement.py`:
- Added `BetSideTag` to the `domain.bets` import.
- Added three pure helpers (side-aware terminal mapping, design §2):
  - `_is_lay_bet(record)` — `record.side == BetSideTag.LAY` (NULL side ⇒ BACK, matching `balance_derivation._is_lay`).
  - `_winner_terminal_state(record)` — LAY→SETTLED_LOST, else SETTLED_WON.
  - `_loser_terminal_state(record)` — LAY→SETTLED_WON, else SETTLED_LOST.
- Applied at all **four** sites (both resolvers): the clean-WINNER return uses `_winner_terminal_state(record)`
  and the LOSER return uses `_loser_terminal_state(record)`; `reason_code` follows the resolved state
  (`.value`) so state/reason stay consistent. For a BACK bet the mapping is byte-identical to before
  (WINNER→"settled_won", LOSER→"settled_lost"). The winner-guard park, REMOVED→VOIDED, and market-voided
  branches are unchanged (side-independent).

### 1.3 Guard unchanged — lays park on dead-heat / material reduction

No change to `_evaluate_winner_guard`. Its park triggers (dead-heat, material/unreadable removed-runner
reduction) are exactly the conditions under which a losing lay's liability is reduced, so a losing lay routes
through the (objective-)WINNER branch, hits the guard, and parks to PROVISIONAL for manual settlement — rather
than auto-booking a knowingly-wrong full −L. No reduced-liability maths added (as locked).

---

## 2. Tests (all land together; full suite green)

Added:
- `tests/workflows/bet_entry/v1/test_record_builder.py` — `test_hedge_record_stamps_pending_settlement_state`
  (hedge builder, LAY construction → `settlement_state==PENDING`, `side==LAY`);
  `test_soft_book_record_leaves_settlement_state_null` (soft-book → `settlement_state is None`).
- `tests/workflows/bet_entry/v1/test_settlement.py` — `_make_record` gained a `side` param; new Block 7:
  LAY WINNER→SETTLED_LOST, LAY LOSER→SETTLED_WON (PENDING resolver); the same two for the PROVISIONAL resolver;
  LAY dead-heat→PROVISIONAL (parked); LAY market-void→VOIDED; explicit-BACK WINNER→SETTLED_WON regression; and
  **`test_sqlite_pass_settles_builder_created_lay_to_inverted_state`** — the SQLite-path regression: a LAY bet
  built by `build_hedge_bet_record` (PENDING at create) is swept end-to-end by `run_settlement_pass` against the
  **real** `SQLiteBetRecordStorage` and settles to SETTLED_LOST on a laid-selection WINNER.

Results:
- Targeted files: **115 passed** (`test_settlement.py` + `test_record_builder.py`).
- **Full suite: 1257 passed, 1 xfailed** (`uv run pytest`). The pre-existing F2 test
  `test_pass_sweeps_only_pending_bets` and the BACK mapping tests stay green (Option A keeps NULL out-of-scope
  for the PENDING sweep, so the F2 contract is unchanged, as designed).
- `mypy` clean on the two changed production modules. `ruff` on the changed files reports only **pre-existing**
  findings — the `settlement.py:15` import-sort and the `RunnerSettlement` F401 (introduced by the in-progress
  worker build; absent at HEAD), plus three pre-existing findings in `test_settlement.py` present at HEAD. My
  additions introduced **zero** new ruff findings; per dirty-tree rules the pre-existing debt is left untouched.

---

## 3. The backfill (targeted, reversible, verified)

With the LAY fix landed and the worker OFF:
- Backup: `data/bethub.db.bak-S222-20260703T194225` (full copy before the write).
- `UPDATE bets SET settlement_state='pending' WHERE bet_id='bet-df31ffcd-c841-4593-a3bd-506f4dd41de2'
  AND settlement_state IS NULL;` → **`changes()=1`** (exactly one row, guarded by `IS NULL`).
- After: the repro LAY is `settlement_state='pending'` — a PENDING sweep candidate. It settles **nothing**; the
  actual won/lost still flows through the (fixed) worker under the operator's supervised proving run.
- Reversible: restore the backup, or `UPDATE … SET settlement_state=NULL WHERE bet_id=… AND settlement_state='pending'`.

---

## 4. Re-prove — against the REAL backfilled bet

A harness loaded the **actual** repro bet from the operational DB through the production load path
(`SQLiteBetRecordStorage` + `from_rows`, run on a scratchpad **copy** so the operational DB is untouched) and
ran it through the **real** fixed resolvers for every possible Gossamer Glow outcome. Derived
`L = 5.26×(3.5−1) = 13.150`; winning-lay collect `S(1−c) = 5.26×0.92 = 4.8392`.

| Actual outcome | PENDING resolver | PROVISIONAL resolver | Net P&L (real balance-derivation) |
|---|---|---|---|
| Gossamer Glow **WINS** (laid sel WINNER → lay loses) | **SETTLED_LOST** | **SETTLED_LOST** | **−13.150** (full liability) |
| Gossamer Glow **LOSES** (laid sel LOSER → lay wins) | **SETTLED_WON** | **SETTLED_WON** | **+4.8392** (collect) |
| Dead-heat WIN (reduced liability) | **PROVISIONAL** (parked) | stays PROVISIONAL | manual settle (no auto P&L) |
| Market VOIDED | **VOIDED** | **VOIDED** | **0.000** |

All correct. **Money-path invariant, made vivid on the dangerous case (laid selection wins):**
- pre-fix (BUG: WINNER→SETTLED_WON) would have booked **+4.8392** — a silent overpay (a phantom collect on a
  bet that actually lost).
- post-fix (FIX: WINNER→SETTLED_LOST) books **−13.150** — the correct full-liability loss.

So whichever way Gossamer Glow actually ran, the worker now resolves the repro LAY to the correct bet-relative
state, and nothing is silently overpaid.

---

## 5. The one deferred step — the concrete live Betfair read (operator-supervised)

The design's re-prove step 2 ("read the actual Betfair result for Gossamer Glow") was **not** auto-executed, by
design and for safety:
- The stored Betfair credential (`bethub-secrets/betfair.json`) is **username/password with no cached
  session token** — a live read requires a full interactive login against the operator's **real-money** Betfair
  account. The live-proving plan itself frames the live read as an **operator-supervised** step
  (`settlement_liveproof_plan.md` §4/§5b: "you're at the machine… supervised proving run").
- The execution shell is sandboxed (no outbound network).

I therefore did **not** log into the Betfair account from this session. The re-prove above proves the fix is
correct for **every** possible outcome, so the only thing the live read adds is *which* correct branch actually
fired. **Operator step to close it:** in live mode, with the worker still OFF, read the settlement for market
`1.259636589` / selection `100232235` (or turn the worker on for the supervised window per liveproof §3–§5) and
confirm the repro LAY settles to SETTLED_LOST if Gossamer Glow won, SETTLED_WON if it lost — matching this
table.

---

## 6. Bet-safety, dirty-tree, and self-assessment

- **`BETHUB_SETTLEMENT_WORKER` stays OFF.** `ui/api/config.py` default is `settlement_worker: bool = False`;
  not set in env; not touched. No launcher/flag change.
- **HEAD `e2638fa`, no git write op** (no add/commit/checkout/stash). The in-progress settlement-worker build in
  the dirty tree is untouched except for the four files this change edits:
  `workflows/bet_entry/v1/settlement.py`, `workflows/bet_entry/v1/record_builder.py`, and the two matching test
  files. No unrelated file touched.
- **Operational DB:** the only write is the one-row backfill above (backed up, reversible). No schema change, no
  other row touched. No live Betfair call. Capture side untouched.
- **Confidence:** LAY inversion + both-resolver coverage + create-path stamp + backfill — **certain** (code +
  full suite + real-bet re-prove). Money-path invariant — **certain** (real balance-derivation on the real bet).
  Concrete which-way result — **pending the operator's supervised live read** (§5).

## 7. Follow-ups (from the design, not blockers)

Carried forward from `settlement_correctness_fix_design.md` §4, to decide before the worker is left **on** for
normal running (neither blocks this fix or the re-prove):
1. **Soft-book auto-settle scope** — kept manual here (soft-book builder unstamped); confirm that is the intended
   end-state, or authorise a separate soft-book settlement path.
2. **Legacy NULL rows** — none in the current DB; Option A ignores NULL, so no churn. Revisit only if a
   legacy/imported DB ever carries pre-W6.5 NULL rows.
3. Optional tidy: add `side` to `RemovedRunnerVerificationRecord` so a parked-lay `paid_full` audit line reads
   bet-relatively (design §2.4). Cosmetic; not done.

Settlement live-proving (cutover **B2**) now turns on the operator's supervised window (§5) — the code, tests,
backfill, and logic re-prove are done.
