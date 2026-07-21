# B3 — HIGH-1 (+MEDIUM-1/-2/-3/-4, LOW-1/-2) money-path fix (build report)

**Session:** cautious fix — verify-first. Closes the HIGH-1 money-path hole (and the coupled MEDIUM/LOW findings) from `b3_verification_report.md`, per the guiding principle: **never terminalise a bet to FAILED without a CONCLUSIVE never-matched signal; when the cleared read is inconclusive, carry-forward (no decision) and let the P4 park valve backstop.**
**Codebase:** bethub-v3 @ HEAD `e2638fa` (unchanged — **no git write ops**; edits layered additively on the dirty tree, no S222/S223 hunk touched). **Flags:** `BETHUB_SETTLEMENT_WORKER` left **OFF**; no live Betfair; no money-move; DB not written.
**Result:** all fixes built; **`uv run pytest` → 1337 passed, 1 xfailed** (was 1327/1xfail → **+10 tests**). The HIGH-1 test is **red before Fix A, green after** (proven below). B4 handoff invariant preserved. **Do NOT flip the settlement worker until the live-proof (below) passes.**

---

## 0. Phase-0 gate (verify the finding first-hand — result: CONFIRMED, proceeded)

All three HIGH-1 mechanics confirmed first-hand at HEAD `e2638fa` before any edit:

| # | Premise | Verdict | Evidence (pre-fix working tree) |
|---|---------|---------|----------------------------------|
| 1 | `{matched_stake==0}` + `{cleared read ReadUnavailable/found=False}` + `{settled_time=None}` → **FAILED** | ✅ | Step 3.5 guard `reconciliation.py:288` skips on inconclusive cleared read → Step 4-5 pre-settlement `matched_stake==0` → FAILED `:351-361`; post-settlement equivalent `:416-431`; real-REST `settled_time` always None (`_translation.py:676-678`) |
| 2 | FAILED is terminal, excluded from the sweep **and** the valve → no self-heal | ✅ | sweep `list_unreconciled_bets(statuses=(PROVISIONAL, PROVISIONAL_PENDING))` `:470-476`; valve `list_stalled_unreconciled_bets` match_statuses default `PROVISIONAL*` — FAILED in neither |
| 3 | `update_match_status` fires **only** on status change → in-orders `matched_size` growth never persists | ✅ | `run_reconciliation_pass` write guard `if decision.new_status != record.match_status:` `:492` |

Gate PASSED → proceeded to the coupled fix.

---

## 1. What was built (per-fix, file:line)

All edits are in **B3 territory only** — `workflows/bet_entry/v1/reconciliation.py` and `…/betfair_adapter.py` (the B3 P3 `get_cleared_order_state`). No S222/S223 settlement-worker hunk was touched.

### Fix A — HIGH-1: carry-forward, never FAILED, on an inconclusive zero-stake absent path
`reconciliation.py::_resolve_one`. Two `matched_stake==0 → FAILED` returns in the Step 4-5 fall-through are replaced with **no-decision (carry-forward)**, reason `absent_zero_stake_cleared_inconclusive`:
- **Pre-settlement** branch (`settled_time is None`) — the branch a matched-then-cleared lay always lands in on real REST — now carries forward at **`:383-397`** (was `absent_resolved_pre_settlement_failed`/FAILED).
- **Post-settlement clean** (WINNER/LOSER, `matched_stake==0`) now carries forward at **`:452-470`** (was FAILED).
- **Unchanged (conclusive signals still FAILED):** a settled **void / removed-runner** market still returns FAILED (`absent_resolved_void_or_removed`, `:376-391`), so a genuine void is never stranded. The `matched_stake>0` paths (`FINAL_FULL`) are untouched.
- New reason code `absent_zero_stake_cleared_inconclusive` added to `ResolutionReasonCode` (`:98`). A carry-forward returns `new_status=None`, so `run_reconciliation_pass` leaves the bet `PROVISIONAL*` (retried next pass; parked by the valve if it never terminalises).

### Fix B — MEDIUM-1: cleared `sizeSettled>0` + null `priceMatched` → carry-forward (don't fabricate a price)
`reconciliation.py::_resolve_one` Step 3.5. The single "found-but-not-clean-recovery → FAILED" branch is split (`:317-343`):
- `cleared.matched_size <= 0` → **CONCLUSIVE lapse → FAILED** (`cleared_order_lapsed`, `:317-329`) — unchanged.
- `cleared.matched_size > 0` with `average_matched_price is None` → matched but price unreadable → **carry-forward** (`cleared_order_price_unreadable`, new reason `:101`, return `:333-343`) — never FAIL a real match or invent a price.

### Fix C — MEDIUM-4: persist a match-field delta even when `match_status` is unchanged
`reconciliation.py::run_reconciliation_pass`. The write guard is loosened from status-only to **status-or-field change** (`:567`), gated by a new pure helper `_match_fields_differ(decision, record)` (`:478-503`) that compares the exact values `update_match_status` would write (`matched_stake` / `unmatched_stake` / `matched_price`). A still-`PROVISIONAL_PENDING` lay whose `matched_size` grows now persists that growth. **Writes match fields ONLY** — `update_match_status` never touches `settlement_state`, so the B4 reconciliation/settlement handoff invariant holds (verified §3).

### Fix (LOW-1) — sum `sizeSettled` across multiple cleared rows per betId
`betfair_adapter.py::get_cleared_order_state` (`:337-365`). Replaces `matching[0]` with a **sum of `size_settled`** across all rows for the betId plus a **size-weighted average** of `price_matched` over priced rows. Single-row (the norm) reduces to the old behaviour; multi-fragment settlements no longer undercount the recovered stake.

### End-to-end flow after the fix
Place unmatched lay → `PROVISIONAL_PENDING`, `matched_stake=0` (P1). Reconciliation: in-orders growth persists (Fix C); once matched-and-cleared, Step 3.5 recovers the true stake (or, if the cleared read is unreadable/absent, **carries forward** — Fix A/B — never $0-FAILED). A lay that genuinely never matches is held `PROVISIONAL*` and **parked to manual by the P4 valve** (settlement-worker-gated), not auto-FAILED. Only a **conclusive** never-matched signal (cleared `sizeSettled==0`, or a settled void/removed runner) FAILs.

---

## 2. Red-before / green-after proof

Seven fix-targeting tests were written, then run against the **unfixed** source:

```
7 failed in 0.15s
  FAILED …::test_resolve_absent_pre_settlement_zero_stake_carries_forward        (returned FAILED)
  FAILED …::test_resolve_absent_zero_stake_cleared_unavailable_carries_forward   (returned FAILED)
  FAILED …::test_resolve_absent_zero_stake_cleared_not_found_carries_forward     (returned FAILED)
  FAILED …::test_resolve_absent_zero_stake_post_settlement_carries_forward       (returned FAILED)
  FAILED …::test_resolve_cleared_size_positive_null_price_carries_forward        (returned FAILED)
  FAILED …::test_pass_persists_growing_matched_stake_same_status                 (stake stayed 0)
  FAILED …::test_get_cleared_order_state_multi_row_sums_settled                  (matched_size 3.00 ≠ 5.00)
```

After applying the fixes, the full new/modified set (12 tests, incl. the boundary + lock tests) is **green**:

```
12 passed in 0.16s
```

**Tests added/changed (closing the report's green-by-omission gaps):**
- **MEDIUM-2** (`test_reconciliation.py`): the incident class is now driven directly — `{matched_stake==0}` × `{cleared unavailable}` / `{cleared found=False}` / `{post-settlement WINNER}` all assert **carry-forward, not FAILED**; plus boundary tests that a void/removed runner and a cleared `sizeSettled==0` **still FAIL** (Fix A/B don't over-carry). `test_gate_then_reconcile_then_settle_end_to_end` (`test_settlement.py`) now drives the **real `run_reconciliation_pass` cleared-orders (Step 3.5) path** — not a hand-forged `update_match_status` — and asserts `matched_stake` recovers to 4.98 with `settlement_state` staying PENDING through reconciliation.
- **MEDIUM-3** (`test_settlement.py`): `test_provisional_resolution_pass_gate_excludes_provisional_pending` — the provisional-pass gate wiring (`settlement.py:1501`) is now locked (a `PROVISIONAL_PENDING`+`settlement_state=PROVISIONAL` bet is not swept, `reader.calls == []`).
- **MEDIUM-4 / LOW-2** (`test_reconciliation.py`): `test_pass_persists_growing_matched_stake_same_status` (stake persists across a same-status pass); `test_pass_never_writes_settlement_state` (locks the B4 invariant — reconciliation leaves `settlement_state` untouched).
- **LOW-1** (`test_betfair_adapter.py`): `test_get_cleared_order_state_multi_row_sums_settled` (two rows → summed 5.00, size-weighted 4.40).

**No existing assertion weakened.** The only *changed* existing test is `test_resolve_absent_pre_settlement_failed`, renamed to `…_zero_stake_carries_forward` and re-asserted to the **corrected** behaviour (a deliberate behaviour change, strictly safer — carry-forward vs a wrong $0-FAILED — not a relaxation). The end-to-end test was **strengthened** (more assertions, real reconciliation path). Every other test change is purely additive.

---

## 3. Suite, B4 invariant, boundaries

- **Suite:** `uv run pytest` → **1337 passed, 1 xfailed, 4 warnings in 6.11s** (+10 over the 1327 baseline; same single pre-existing xfail; the 4 warnings are pre-existing `HTTP_422` deprecations).
- **B4 invariant intact:** `grep` confirms **no `update_settlement_state` call** anywhere in `reconciliation.py`; the only `settlement_state` tokens are detail-dict log strings and one explanatory comment. Fix C writes via `update_match_status` (match fields only). Locked by `test_pass_never_writes_settlement_state`.
- **Boundaries honoured:** HEAD stays `e2638fa`; **no git write ops** (no commit/stash/discard; dirty tree layered additively — S222/S223 hunks in shared files untouched; my source edits are confined to the two B3 files, `+276/−13`). `BETHUB_SETTLEMENT_WORKER` left OFF; no live Betfair; no money-move; no operational-DB write. DR-030 module boundaries, DR-032 Betfair settlement spine, DR-019 derived-on-read, DR-021 anchors respected.
- **Lint:** my new code is ruff-clean. The one remaining ruff `I001` (import-organize) is on `reconciliation.py`'s pre-existing B3 import block (lines 36–42), which I did not touch — a pre-existing finding on the dirty tree, left untouched per the build report; I introduced **no new** ruff errors.

---

## 4. Behaviour change the operator must know (deliberate, per the guiding principle)

A lay that **genuinely never matched** (fully lapsed) no longer auto-resolves to `FAILED` on the fall-through: its `betStatus=SETTLED` cleared read returns `found=False` (a lapse surfaces under `LAPSED`, not `SETTLED`), which is **inconclusive**, so it now **carries forward** and is **parked to the manual `PROVISIONAL` queue by the P4 valve** (after ≥3 sweeps + event start) instead of being auto-voided. This is the intended trade: we accept manual review of genuine lapses to **guarantee we never re-book a real winner at $0**. Two consequences:
1. With `BETHUB_SETTLEMENT_WORKER` **OFF** (current state), the valve does not run, so a never-matched 0-stake lay simply sits `PROVISIONAL_PENDING` — harmless (no money flows), visible in `GET /bets/provisional`.
2. The live-proof "lapse" negative case (fix-report §4.5 / runbook step 5) should now expect **parked-to-manual (valve)**, or a conclusive `cleared_order_lapsed` FAILED only if Betfair surfaces the order under `SETTLED` with `sizeSettled==0` — not an unconditional auto-FAILED.

---

## 5. Live-proof (still the real bar — NOT run here)

The HIGH-1 code path is now safe by construction and by test, but `listClearedOrders` remains **contract-verified, not live-verified**. Before flipping `BETHUB_SETTLEMENT_WORKER` on, the supervised live-proof must confirm (per `b3_verification_report.md` §4):
1. **The HIGH-1 negative/lag case:** reproduce the incident shape (0-matched lay that matches then clears fast); force a reconciliation pass to catch it **absent-but-not-yet-in-cleared** (or during a transient cleared-read failure) and confirm the row **carries forward and later converges to `final_full` with the true stake** (or is parked to manual) — **never `failed`/$0**.
2. `sizeSettled` == true matched backer stake, `priceMatched` populated, **one aggregated row per betId** (else the LOW-1 sum matters).
3. The lapse case resolves via the valve/manual path or conclusive `cleared_order_lapsed` — never a wrong magnitude.

Keep the reconciliation worker supervised and the settlement worker **OFF** until step 1 passes on real data.

<!-- B3 HIGH1 FIX COMPLETE -->
