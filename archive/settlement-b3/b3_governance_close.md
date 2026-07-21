# B3 — Governance close (fix-side)

**Closed:** 2026-07-05 (S226), Adelaide-anchored per DR-021.
**Scope of this close:** the B3 lay money-path **fix-side** — root cause, the 4-part coupled fix (P1–P4), the HIGH-1 fix, and the R2/R3 hardening — is **complete, adversarially verified, and suite-green** on bethub-v3 @ HEAD `e2638fac2c659783448bece9b1810294512068bf`. This close does **not** clear B3 for money: the final gate is the operator's supervised **live-proof** (§4 runbook, `b3_lay_settlement_fix_report.md`), deferred to the next session by operator decision.
**Bet-safety:** bethub-v3 HEAD **byte-identical at `e2638fa`** throughout the whole B3 arc; all code built additively on the in-flight dirty tree with **no git write ops**; `BETHUB_SETTLEMENT_WORKER` **OFF**; the `BETHUB_RECONCILIATION_WORKER` opt-out defaults on-in-live but **no worker was run live**; **no place/settle/money-move**; the one known mis-valued live row (`434175139855`) left as-is (clears at live-proof).
**Governing DRs:** DR-032/033, DR-030, DR-027/028, DR-019, DR-021.

---

## 1. What B3 was

A live Betfair **LAY** placed UNMATCHED, later matched, settled with the **correct direction but $0 money** (stored `matched_stake` stayed 0). Root cause (CONFIRMED first-hand + corroborated by live logs): the quick-lay route `place_lay` (`ui/api/routers/racing.py:1105`) wrote a not-fully-matched lay as **terminal `FINAL_PARTIAL matched_stake=0`**, while `run_reconciliation_pass` sweeps `PROVISIONAL*` only → the bet was **never reconciled**, so a post-placement match never updated the store; settlement then valued the stale 0 → correct direction, $0 magnitude. Money derives on read from `matched_stake` (DR-019), so fixing the stake fixes the money. Full arc: `b3_lay_settlement_investigation_report.md`.

## 2. What was built (all on `e2638fa`, additive, no git writes)

- **4-part coupled fix** (`b3_lay_settlement_fix_design.md` → `b3_lay_settlement_fix_report.md`): **P1** re-label placement (`remaining>0 → PROVISIONAL_PENDING`); **P2** periodic reconciliation worker (`ui/api/reconciliation_worker.py`, `BETHUB_RECONCILIATION_WORKER` kill switch, independent of the settlement flag); **P3** recover the true matched size for a cleared order via a new `listClearedOrders` read (`clients/betfair_client/v1/cleared_orders.py` + adapter `get_cleared_order_state` + resolver Step 3.5); **P4** gate settlement to exclude `PROVISIONAL*` + a park-not-settle safety valve. Coupled; fails closed.
- **HIGH-1 fix** (`b3_high1_fix_commission.md` → `b3_high1_fix_report.md`): P3's cleared-orders fall-through could re-book the incident-class winner at `$0/FAILED` on a cleared-read miss. Principle installed: **never terminalise to `FAILED` without a conclusive never-matched signal; carry-forward (no decision) when the cleared read is inconclusive; the P4 park valve backstops.** Fix A (HIGH-1 carry-forward) + B (null-price → carry-forward) + C (persist mid-flight stake).
- **R2 + R3 hardening** (`b3_r2_hardening_commission.md` → `b3_r2_hardening_report.md`, THIS session): **R2** — the reconciliation write could **null a known-good `matched_price`** when a still-pending order re-read omitted the average price (F1 in `_match_fields_differ` + F2 in the write call). **R3** (surfaced by the R2 re-verify) — F2's fallback left a stale non-None price on FAILED zero-stake rows; F2 refined so terminals write `decision.matched_price` verbatim (None on FAILED clears it), preserving the stored price **only** on the still-pending case.

## 3. Verification standard met

- **Suite:** `uv run pytest` → **1343 passed, 1 xfailed** on `e2638fa`. Grew 1289 → 1327 (P1–P4) → 1337 (HIGH-1) → 1342 (R2) → 1343 (R3), every increment red-before/green-after on its money-path test.
- **HIGH-1:** confirmed CLOSED by an S226 focused 4-lens adversarial re-verify (incl. an independent red-before reproduction of the carry-forward tests).
- **R2/R3:** confirmed by an S226 focused 3-lens read-only refute pass (correctness, test-integrity, blast-radius) — all UPHELD; the pass itself surfaced R3, which was then hardened and proven red-before/green-after. **R2 surface residual: none.**
- **Invariants held throughout:** the carry-forward gate (`if decision.new_status is not None`), the **B4 no-`settlement_state`-write** reconciliation/settlement handoff, the P4 settlement gate + park valve, and the settle-vs-reconcile race discipline.

## 4. Residuals carried past this close (none re-open the $0 path)

- **R1 (MEDIUM — live-proof watch-item, operator-elected):** the `matched_stake>0` absent-path fall-through books terminal `FINAL_FULL` at a possibly **stale-low** stored stake on a cleared-miss → *under*-settle (never $0, never stuck). Blast radius is settlement-delay. **Watch at live-proof:** a partially-then-fully-matched lay must converge to the TRUE stake, never a stored-low `FINAL_FULL`. Not fixed here by operator election.
- **HIGH-2 (operator commit-time item):** B3 is mechanically inseparable from the un-live-proven S222/S223 chain in one uncommitted tree — committing B3 commits that chain; a blind `git stash`/`clean` discards the untracked P3 files. Decide staging at commit time.
- **LOW-5 (operator commit-time item):** untracked `data/*.db.bak-S222-*` not gitignored → don't `git add -A`; add a `*.db.bak-*` ignore.
- **Cosmetic:** none open on the R2 surface after R3.

## 5. Close decision

**B3 fix-side is GOVERNANCE-CLOSED.** The engineering is done, verified, and green; no code change remains on the fix-side. The one thing that clears B3 for money is the operator's supervised live-proof, which requires live Betfair + real money-move and cannot be done by a Claude session.

**The single gate remaining to clear B2↔B3:** operator supervised live-proof per `b3_lay_settlement_fix_report.md` §4 —
1. `BETHUB_RECONCILIATION_WORKER` on, `BETHUB_SETTLEMENT_WORKER` **off** first (money-safe): reproduce the unmatched-lay incident, confirm the stake reconciles to the TRUE matched size.
2. The **HIGH-1 negative case**: a fast-clearing 0-matched lay must converge `final_full`/true stake, **never `failed`**.
3. The **R1 watch**: a partial→full lay must converge to the true stake, never a stored-low `FINAL_FULL`.
4. The **R2 watch**: a still-pending lay whose price momentarily reads absent must keep its stored price.
5. Only then turn `BETHUB_SETTLEMENT_WORKER` on. Both flags stay OFF until the run passes.

On a clean live-proof: B2 is fully money-proven and B2↔B3 clears; then handle the HIGH-2 / LOW-5 commit-time items.

---

## 6. LIVE-PROOF PASSED (S227, 2026-07-06) — gate CLEARED

The operator-supervised live-proof ran on real Betfair with real money and **PASSED**. Both money-loop paths proven: a matched lay reconciled to its **true stake** and settled with **true money** (`434257406420` → `settled_lost` −$4.91, not $0 — B3 + B2 + S223 + LAY inversion), and a never-matched lay was **held then parked to the manual queue by the P4 valve** (`434257942837`, `matched_stake` stayed 0, never auto-settled — the HIGH-1 principle live). **B2↔B3 is CLEARED; B2 auto-settlement is fully money-proven.** Both workers turned OFF at close. Full record + the live findings (F-LIVE-1 promo cross-thread 500 = Finding 1 off-"parked"; F-LIVE-2 lapse-parks-not-FAILED measurement item; S1 leg-stake residual) in **`b3_liveproof_result.md`**. A live prerequisite also fixed this session: the stream 64 KiB read-buffer overflow (`stream_read_buffer_overflow_fix_report.md`).

<!-- B3 GOVERNANCE CLOSE (fix-side) — LIVE-PROOF PASSED S227; B2↔B3 CLEARED; workers OFF -->
