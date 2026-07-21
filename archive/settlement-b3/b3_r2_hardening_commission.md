# B3 — R2 price-null hardening + 3 LOW test-gap closure (Code commission, cautious)

**Session:** S226 governance → commissioned for a Claude Code **fix** session in `bethub-v3`.
**Type:** Targeted defensive fix + tests. Verify-first (reproduce R2 before fixing); no git write ops.
**Codebase:** bethub-v3 @ HEAD `e2638fa`, B3 (P1–P4 + HIGH-1 fix) built additively on the in-flight settlement-worker dirty tree.
**Grounds (read first):** `b3_high1_fix_report.md` (the HIGH-1 fix under hardening), `b3_verification_report.md`, `b3_high1_fix_commission.md` (guiding principle).
**Governing DRs:** DR-032/033, DR-030, DR-027/028, DR-019, DR-021.

---

## 0. Why this exists

The S226 focused adversarial re-verify of the HIGH-1 fix **confirmed HIGH-1 closed** (3 independent lenses, incl. an independent red-before reproduction). It surfaced two residuals on the same reconciliation write surface:
- **R2 (LOW, THIS COMMISSION):** Fix C's bundled all-fields write can **null a previously-good `matched_price`** when a `PROVISIONAL_PENDING` order is re-read with `sizeMatched>0` but `averagePriceMatched` absent. The nulled price zeroes the derived LAY liability (`balance_derivation.py::_lay_liability` returns 0 on `matched_price is None`) and, if the row later terminalises via the absent-path fall-through (`:366-376`/`:433-447`, which copy `record.matched_price` straight into a terminal FINAL_FULL), bakes in permanently → under-credits a settled-won lay. Self-healing on the next well-formed read; requires an off-nominal payload the live REST API does not emit. Empirically reproduced (scratchpad `probe_fixc.py`).
- **R1 (MEDIUM, NOT in scope — operator elected watch-at-live-proof):** the `matched_stake>0` absent-path fall-through books terminal FINAL_FULL at a possibly-stale-low stored stake. Below the never-$0 guarantee; has settlement-delay blast radius; logged as a live-proof watch-item. **DO NOT touch the `matched_stake>0` fall-through branches in this commission.**

**Guiding principle (unchanged):** never terminalise or mis-value a bet off an untrustworthy value; prefer preserving a known-good stored value over overwriting it with a null.

---

## 1. Verify R2 first (Phase 0 — hard gate, no fix yet)

Confirm first-hand at HEAD `e2638fa` (working tree):
1. In `run_reconciliation_pass` write block (`reconciliation.py:568-574`), `update_match_status` is called with `matched_price=decision.matched_price` **raw** (uncoerced) whenever `_match_fields_differ` is True.
2. The `still_pending_in_orders` decision (`:252-263`) carries `matched_price=snap.average_matched_price`, which can be `None` while `snap.matched_size>0` (model permits: `average_matched_price: float | None`).
3. `_match_fields_differ` (`:498-502`) returns True when `decision.matched_price (None) != record.matched_price (good)` even if stake is unchanged → triggers the write.
4. Reproduce: a `PROVISIONAL_PENDING` row with a good stored `matched_price`, re-read with `matched_size>0` + `average_matched_price=None`, has its stored price nulled after one pass.

If 1–4 confirm → proceed. If R2 does NOT reproduce → STOP and report (`<!-- B3 R2 STOPPED -->`).

---

## 2. The fix (two coupled edits, both in `reconciliation.py`, B3 territory only)

**F1 — `_match_fields_differ`:** a `None` decision price is not a real "change to persist". Change the price clause so it only signals a difference when the decision actually carries a price:
`decision.matched_price is not None and decision.matched_price != record.matched_price`.
(Stake/unmatched clauses unchanged.)

**F2 — the write call (`:568-574`), belt-and-suspenders:** never overwrite a non-None stored price with a null. Pass
`matched_price = decision.matched_price if decision.matched_price is not None else record.matched_price`.
This preserves the known-good stored price on a stake-only persist (and is a harmless no-op on a FAILED terminal, where stake is 0 and price is irrelevant). It does NOT fabricate a price and does NOT change any stake write.

Do not alter the carry-forward gate (`if decision.new_status is not None`), the absent-path resolutions, the settlement gate, or the valve. **No S222/S223 hunks.**

---

## 3. Close the 3 LOW test gaps (from the re-verify)

- **T1 (pass-level carry-forward self-heal):** drive `run_reconciliation_pass` with `{record.matched_stake==0}` + an inconclusive cleared read (unavailable / found=False), assert the bet is left `PROVISIONAL_PENDING`, **`update_match_status` NOT called** (no match-field write), and it remains re-sweepable. Locks the "carry-forward writes no money" property at the pass level (currently only transitively covered).
- **T2 (R2 regression — red-before/green-after REQUIRED):** a `PROVISIONAL_PENDING` row with a good stored `matched_price` re-read with `matched_size>0` + `average_matched_price=None` → assert the stored `matched_price` is **preserved** (not nulled), and stake growth (if any) still persists. Must fail against the pre-F1/F2 code and pass after.
- **T3 (LOW-1 mixed-price multi-row):** `get_cleared_order_state` with a `price_matched=None` row mixed with priced rows → assert summed stake is correct and the size-weighted average is computed over the **priced subset only** (no div-by-zero, no None pollution). File: `tests/workflows/bet_entry/v1/test_betfair_adapter.py`.

Optional cheap add if clean: a `_match_fields_differ` price-only unit test (None decision price ⇒ returns False on an otherwise-equal record).

---

## 4. Prove

`uv run pytest` fully green (report the new count; expect > 1337). **T2 must be red before F1/F2, green after** — state this explicitly. No existing assertion weakened.

## 5. Boundaries

HEAD stays `e2638fa`; **no git write ops** (layer additively; do not commit/stash/discard; do not touch the S222/S223 dirty hunks or the R1 `matched_stake>0` fall-through). `BETHUB_SETTLEMENT_WORKER` OFF; no worker run live; no live Betfair; no place/settle/money-move; DB reads `mode=ro`. DR-030/032/019/021 respected.

## 6. Deliverable — `b3_r2_hardening_report.md`

Phase-0 confirmation (or STOP); F1/F2 per-edit file:line; the 3 new tests + T2's red-before/green-after proof; full-suite count; confirmation the carry-forward gate + B4 no-`settlement_state` invariant are intact + R1 branch untouched. End the final line with the sentinel `<!-- B3 R2 HARDENING COMPLETE -->` (or `<!-- B3 R2 STOPPED -->`).

---

*Governance commission — no code touched here; bethub-v3 byte-identical at `e2638fa`.*
