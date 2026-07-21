# B3 — R2 price-null hardening + 3 LOW test-gap closure — REPORT (COMPLETE)

**Session:** S226 (continued) — cautious Claude Code fix session, commissioned per `b3_r2_hardening_commission.md`.
**Codebase:** bethub-v3 @ HEAD `e2638fac2c659783448bece9b1810294512068bf` (unchanged), B3 (P1–P4 + HIGH-1 fix) built additively on the in-flight settlement-worker dirty tree.
**Outcome:** **COMPLETE.** R2 reproduced first-hand at HEAD, then closed with two coupled edits (F1+F2) in `reconciliation.py`; the 3 LOW test gaps closed (5 new tests). T2 red-before/green-after proven. Full suite **1342 passed, 1 xfailed** (prior 1337 + 5 new). `BETHUB_SETTLEMENT_WORKER` OFF; no git write ops; no live Betfair; no money-move.
**Env note:** the mid-S226 macOS TCC block that STOPPED the prior attempt was cleared by the operator granting Full Disk Access + relaunching a fresh session. The prior STOP record (env, not a code verdict) is superseded by this report.

---

## 1. Phase 0 — R2 confirmed first-hand at HEAD `e2638fa` (hard gate PASSED)

All four commission points confirmed against the working tree, corroborated by a direct probe (`scratchpad/probe_r2.py`, run via `uv run python`):

1. **Raw price write** — `run_reconciliation_pass` write block (`reconciliation.py:568-574` pre-fix) calls `update_match_status(..., matched_price=decision.matched_price)` **uncoerced** whenever `_match_fields_differ` is True. ✓ (read)
2. **None price on a matched-size decision** — the `still_pending_in_orders` decision (`:252-263`) carries `matched_price=snap.average_matched_price`, which the model permits to be `None` while `snap.matched_size > 0`. Probe POINT2: decision built from a `matched_size=25, average_matched_price=None, found_in_unmatched=True` snapshot → `decision.matched_price is None`, `new_status=PROVISIONAL_PENDING`. ✓
3. **`_match_fields_differ` fires on None** — (`:498-502` pre-fix) returns True because `None != 4.20` even though stake is otherwise the differentiator. Probe POINT3: `_match_fields_differ(decision, record) == True`. ✓
4. **Reproduction — good stored price nulled after one pass** — a `PROVISIONAL_PENDING` row (`matched_stake=20`, **`matched_price=4.20`**) re-read with `matched_size=25 + average_matched_price=None` (found_in_unmatched=True): after one `run_reconciliation_pass`, probe POINT4 pre-fix showed **stored `matched_price` 4.20 → None** (`R2 REPRODUCED: True`), while stake growth 20→25 persisted. ✓

→ Gate passed. Proceeded to fix.

---

## 2. The fix — two coupled edits, both in `workflows/bet_entry/v1/reconciliation.py`, B3 territory only

**F1 — `_match_fields_differ` price clause (`reconciliation.py:498-508`):** a `None` decision price is no longer treated as a change to persist. The price clause is now:
```python
or (
    decision.matched_price is not None
    and decision.matched_price != record.matched_price
)
```
Stake / unmatched clauses unchanged. (Comment added citing the R2 rationale.)

**F2 — the write call (`reconciliation.py:568-581`), belt-and-suspenders:** never overwrite a non-None stored price with a null. The `matched_price` argument is now:
```python
matched_price=(
    decision.matched_price
    if decision.matched_price is not None
    else record.matched_price
),
```
Preserves the known-good stored price on a stake-only persist; harmless no-op on a `FAILED` terminal (stake 0, price irrelevant). Does **not** fabricate a price and does **not** change any stake write.

**Untouched (per commission boundaries):** the carry-forward gate (`if decision.new_status is not None`, `:566`), the absent-path resolutions, the R1 `matched_stake>0` fall-through branches (`absent_resolved_pre_settlement_full` `:371`, `absent_resolved_post_settlement_terminal` `:438`), the settlement gate, the park valve. No S222/S223 hunks.

**Post-fix probe (POINT4, green):** stored `matched_price` preserved at **4.2** after the pass; stake growth 20→25 still persisted; `R2 REPRODUCED: False`.

---

## 3. The 3 LOW test gaps — closed (5 new tests)

**T1 — pass-level carry-forward self-heal** (`tests/workflows/bet_entry/v1/test_reconciliation.py::test_pass_carry_forward_writes_no_match_fields`): drives `run_reconciliation_pass` on a `matched_stake==0` `PROVISIONAL_PENDING` bet with a resolved-out absent orders read + inconclusive cleared read (found=False) + `settled_time=None` → HIGH-1 carry-forward (`absent_zero_stake_cleared_inconclusive`, `new_status=None`). Asserts **`update_match_status` never called** (spy counter stays empty → no match-field/money write), bet left `PROVISIONAL_PENDING` with `matched_stake==0`, and re-sweepable (`reconciliation_attempts==1`, still in `list_unreconciled_bets()`). Locks "carry-forward writes no money" at the pass level.

**T2 — R2 regression (red-before/green-after REQUIRED)** (`..::test_pass_preserves_good_price_on_null_price_reread`): a `PROVISIONAL_PENDING` row with a good stored `matched_price=4.20` re-read with `matched_size=25 + average_matched_price=None` → asserts stored `matched_price` **preserved at 4.20** (not nulled) and stake growth (20→25, unmatched 25) still persists.

**T3 — LOW-1 mixed-price multi-row** (`tests/workflows/bet_entry/v1/test_betfair_adapter.py::test_get_cleared_order_state_mixed_null_price_rows`): `get_cleared_order_state` with a `price_matched`-absent row (2.00) mixed with a priced row (4.00 @ 3.00) → asserts summed `matched_size==5.00` (over ALL rows) and size-weighted `average_matched_price==4.00` computed over the **priced subset only** (the None-priced fragment excluded from the mean, not counted as zero, no div-by-zero, no None pollution). Plus a companion **all-null-price** case (`..::test_get_cleared_order_state_all_null_price_rows`): stake still sums to 5.00, average is `None` (→ MEDIUM-1 carry-forward, never $0/FAILED).

**Optional add (done, clean)** — a `_match_fields_differ` price-only unit (`..::test_match_fields_differ_ignores_none_decision_price`): a None decision price on an otherwise-equal record returns False; a genuine stake delta still returns True.

---

## 4. Proof

- **T2 red-before/green-after (explicit):** with F1+F2 reverted in-place (comments left; logic restored to the raw `decision.matched_price != record.matched_price` clause and raw `matched_price=decision.matched_price` write), **T2 and the `_match_fields_differ` unit FAILED** — `test_pass_preserves_good_price_on_null_price_reread` (price nulled) and `test_match_fields_differ_ignores_none_decision_price` (`assert True is False`). Restoring the fix (byte-identical to the F1+F2 version) → both **PASS**. So the tests genuinely bind the fix, not theatre.
- **New tests alone:** 5 passed.
- **Full suite:** `uv run pytest` → **1342 passed, 1 xfailed** (the pre-existing xfail reproduced; prior count 1337 + 5 new). No existing assertion weakened.
- **Lint:** my added lines introduce **zero** new ruff findings. Three pre-existing dirty-tree lint items remain untouched (two `I001` import-ordering on `reconciliation.py:17` / `test_reconciliation.py:20` and one `E501` at `test_reconciliation.py:988`); `ruff check --diff` shows the fixes would only reorder pre-existing import blocks / touch an existing `fetched_terminal` line — **none of my added lines appear**. Reordering imports is outside commission scope and would disturb the dirty tree, so left as-is.

---

## 5. Invariants / boundaries — all intact

- HEAD stays `e2638fac2c659783448bece9b1810294512068bf`; **no git write op** (no commit/stash/discard). Fix layered additively on the dirty tree.
- **Carry-forward gate** (`if decision.new_status is not None`, `:566`) untouched — verified present.
- **B4 no-`settlement_state` invariant** intact: F2 changes only the `matched_price` argument to `update_match_status`, which writes match fields only (never `settlement_state`); the P4 reconciliation/settlement handoff is unaffected.
- **R1 `matched_stake>0` fall-through** branches untouched (`absent_resolved_pre_settlement_full` `:371`, `absent_resolved_post_settlement_terminal` `:438`) — R1 remains the operator's live-proof watch-item, not modified here.
- `BETHUB_SETTLEMENT_WORKER` OFF (`config.py:70 settlement_worker: bool = False`); no worker run live; no live Betfair; no place/settle/money-move; DB reads only.

---

## 6. What's next (for governance)

1. Focused re-verify of the R2 hunk (F1+F2 + the 5 tests) if the operator wants an adversarial pass on the changed surface.
2. Governance-close B3 (R2 was the last authorised fix; R1 stays a watch-item, HIGH-2 dirty-tree commit coupling + LOW-5 `.db.bak` gitignore stay operator commit-time items).
3. Operator supervised live-proof (§4 runbook in `b3_lay_settlement_fix_report.md`), with the R1 watch: a partially-then-fully-matched lay must converge to the TRUE stake, never a stored-low FINAL_FULL — and now also the R2 watch: a still-pending lay whose price momentarily reads absent must keep its stored price.

---

## 7. S226 focused adversarial re-verify (3 read-only refute-lenses) — R2 UPHELD; R3 surfaced + closed

Per operator election, a focused adversarial fan-out ran on the changed F1+F2 surface — three independent read-only refute agents (correctness, test-integrity, blast-radius), each instructed to REFUTE. All reported the full suite at the then-count (1342 passed / 1 xfailed — no concurrent-revert race corruption).

- **Correctness lens — UPHELD (all 4 targets).** F2 is the only reconciliation price-write and cannot emit None over a good stored value (probed: liability stayed 128.0 where pre-fix understated to 0). F1 still fires on genuine price/stake deltas; F2 is a provable no-op on the absent-path FINAL_FULL branches. **Surfaced R3 (LOW/cosmetic):** F2's belt-and-suspenders fallback left a **stale non-None `matched_price` on FAILED zero-stake rows**. Traced money-harmless end-to-end — every `balance_derivation` formula is linear in `matched_stake` (always 0 on FAILED → leftover price × 0 = 0); `settlement.py` never reads `matched_price`. Only visible effect: a UI serializer echoing the stale price on a failed row. Caveat raised: the safety rested entirely on the multiply-by-zero invariant with no defensive price↔stake gate.
- **Test-integrity lens — UPHELD.** Independently reproduced T2's red-before (`assert None == 4.2`; unit `assert True is False`), restored `reconciliation.py` byte-identical (md5 unchanged). No vacuous assertions; T1's spy proven to fail on any write; T1 confirmed on the `absent_zero_stake_cleared_inconclusive` branch. Flagged (transparency, not a defect) the HIGH-1 test rename as correct co-evolution.
- **Blast-radius lens — UPHELD (all 6 checks).** F1 (`:505-512`) + F2 the only product-source change; carry-forward gate (`:566`), B4 no-`settlement_state` invariant (both `update_match_status` impls), and R1 fall-through branches (`:366-376`/`:432-447`) intact and unmasked (F2 probed as a definitional R1 no-op); HEAD unchanged. Sole caveat: the dirty uncommitted tree makes git hunk-attribution impossible, so containment rests on direct code reading (consistent with this report).

### R3 fix (F2 refinement) — applied + proven

Operator elected to harden rather than carry R3 as a watch-item (it's the semantically correct behavior — a FAILED bet has no matched price — and it removes the invariant-dependence caveat). **F2 refined** (`reconciliation.py:588-602`): preserve the stored price **only** on a still-pending re-read that omits the price (`decision.matched_price is None and decision.new_status == MatchStatus.PROVISIONAL_PENDING`); every terminal resolution now writes `decision.matched_price` verbatim — including `None` on a FAILED bet, clearing the leftover. F1 unchanged.

**New test** `test_pass_clears_price_on_failed_terminal` (a PROVISIONAL_PENDING lay with a leftover stored price, cleared read reports `sizeSettled=0` → `cleared_order_lapsed` → FAILED): asserts the stored `matched_price` is **None** (cleared) on the terminal. **Red-before/green-after proven** — against the prior belt-and-suspenders F2 the test failed `assert 4.2 is None` **while T2 still passed** (the two behaviors are independent; the harden fixes R3 without regressing R2). `reconciliation.py` restored byte-identical to the R3-hardened version after the red-before check.

**Suite after R3 harden:** `uv run pytest` → **1343 passed, 1 xfailed** (1342 + 1 new). HEAD `e2638fac` unchanged; no git write ops; flag OFF; carry-forward gate, B4 invariant, and R1 branches still intact.

**R2 surface residual after this pass: none.** R1 remains the sole open money-adjacent watch-item, deferred to operator live-proof.

<!-- B3 R2 HARDENING COMPLETE -->
