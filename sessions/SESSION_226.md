# SESSION 226 — B3 lay money-path: TCC access restored → R2 price-null hardening built + proven → 3-lens re-verify (R2 upheld, R3 surfaced) → R3 hardened → **B3 fix-side GOVERNANCE-CLOSED** (live-proof opens S227)

**Opened:** 2026-07-05 (fresh session after operator granted Full Disk Access; S226 planned auto-first-action = run `b3_r2_hardening_commission.md`, which S225→S226 had STOPPED on a mid-session macOS TCC revocation).
**Closed:** 2026-07-05, Adelaide-anchored per DR-021.
**Tool routing:** Single access-having governance Claude Code session on the Mac. Unlike S225 (which routed all code to commissioned Code sessions), this session held Full Disk Access to `~/Desktop/Projects/bethub-v3`, so it **ran the R2/R3 fix first-hand** (Bash + file tools) and spawned **read-only** sub-agents for the adversarial re-verify. All fix work additive on the dirty tree; **HEAD byte-identical at `e2638fa` throughout; no git write ops; `BETHUB_SETTLEMENT_WORKER` OFF; no money moved.**
**Governing DRs:** DR-032/033, DR-030, DR-027/028, DR-019, DR-021.

---

## Session shape

The env blocker that STOPPED the R2 hardening at the S225→S226 boundary (macOS TCC / Full Disk Access revoked mid-session) was cleared by the operator granting access + relaunching a fresh session. This session then executed the pending R2 commission cleanly, hardened one residual the re-verify surfaced (R3), and **governance-closed the B3 fix-side**. The only remaining B3 gate — the operator's supervised live-proof — is deferred to S227 by operator decision ("I'll do the live proof tomorrow; we'll open with that").

## What was delivered (in order)

1. **Env unblocked + re-grounded.** Confirmed read/write to `~/Desktop/Projects/bethub-v3` (note: path is `Projects/bethub-v3`, not `~/Desktop/bethub-v3` as an earlier memory said — corrected). HEAD `e2638fac`, dirty tree intact, flag OFF.

2. **R2 hardening — Phase-0 verified first-hand, then fixed** (`b3_r2_hardening_report.md`, rewritten from the prior STOP record). Reproduced R2 via `scratchpad/probe_r2.py`: a `PROVISIONAL_PENDING` row with good stored `matched_price=4.20`, re-read `matched_size=25 + average_matched_price=None` (still pending), had its price **nulled 4.20→None** after one `run_reconciliation_pass` (stake growth persisted). **Fix (2 edits, `reconciliation.py` only): F1** `_match_fields_differ` price clause now `decision.matched_price is not None and …`; **F2** the write passes `decision.matched_price if not None else record.matched_price`. **5 new tests** (T1 pass-level carry-forward-writes-no-money; T2 R2 regression **red-before/green-after PROVEN**; T3 mixed-null-price + all-null cleared-order rows; a `_match_fields_differ` price-only unit). Suite **1342 passed / 1 xfailed**.

3. **Focused adversarial re-verify — 3 read-only refute-lenses (operator-elected).** Because the author (this session) wrote the fix, independent refuters were run: **correctness**, **test-integrity**, **blast-radius**. **All UPHELD** (all three independently reported suite 1342/1xfail — no concurrent-revert race corruption). Correctness probed liability held at 128.0 where pre-fix understated to 0; test-integrity independently reproduced T2's red-before and restored `reconciliation.py` byte-identical; blast-radius confirmed F1/F2 the only product change with carry-forward gate + B4 invariant + R1 branches intact.

4. **R3 surfaced + hardened.** The correctness lens found **R3 (LOW/cosmetic):** F2's belt-and-suspenders fallback left a **stale non-None `matched_price` on FAILED zero-stake rows** — traced **money-harmless** (every `balance_derivation` formula linear in `matched_stake`, always 0 on FAILED; `settlement.py` never reads `matched_price`), only a UI echo, but resting entirely on the multiply-by-zero invariant with no defensive gate. **Operator elected to HARDEN** (semantically correct — a FAILED bet has no matched price — and removes the caveat). **F2 refined** (`reconciliation.py:588-602`): preserve the stored price **only** on the still-pending case (`decision.matched_price is None and decision.new_status == PROVISIONAL_PENDING`); every terminal writes `decision.matched_price` verbatim (None on FAILED clears the leftover). **New test** `test_pass_clears_price_on_failed_terminal`, **red-before/green-after PROVEN** (against the prior F2: `assert 4.2 is None` failed **while T2 still passed** — the two behaviors are independent). Suite **1343 passed / 1 xfailed**.

5. **B3 fix-side GOVERNANCE-CLOSED** (`b3_governance_close.md`). The engineering is complete, adversarially verified, and green; no fix-side code remains. The sole gate to clear B2↔B3 is the operator's supervised live-proof.

## Standing-instruction adherence check

- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — bethub-v3 HEAD byte-identical at `e2638fa`; all edits additive on the dirty tree with **no git write ops**; the two red-before checks reverted `reconciliation.py` in-place and restored it **byte-identical** (md5-confirmed). `BETHUB_SETTLEMENT_WORKER` OFF; reconciliation worker never run live; no place/settle/money-move; the known mis-valued live row left as-is. ✅
- **Cat 5 (division of labour)** — code fix run first-hand by the access-having governance session (legitimate: it held the access the S225 Code sessions lacked); adversarial verify routed to independent read-only sub-agents to counter author bias. Money-path scope calls (re-verify vs skip; harden R3 vs watch) surfaced to + made by the operator. ✅
- **S178/S189 discipline** — every premise re-grounded first-hand before acting (Phase-0 R2 reproduction; independent red-before); "green ≠ correct" operationalised — the re-verify caught R3 on an already-green surface. ✅
- **First-action gate (S200, hard)** — **S227 first action confirmed with operator: the supervised live-proof** (report §4 runbook + HIGH-1 negative case + R1/R2 watches). "We will open with that."
- **Cat-2 sweep** — `current_state.md`, `cutover_readiness_map.md`, `v3_build_picture.md` updated this close; no `standing_instructions.md` change warranted.

## Open items

**Closed in S226:**
- R2 price-null hardening — built + 3-lens re-verified. ✅
- R3 (FAILED-row stale price) — hardened + proven. ✅
- **B3 fix-side — GOVERNANCE-CLOSED** (`b3_governance_close.md`). ✅

**Carried to S227:**
- **Operator supervised live-proof** (first action, confirmed) — `b3_lay_settlement_fix_report.md` §4: reconciliation-on first (money-safe) → reproduce the unmatched-lay incident, confirm true-stake convergence → **HIGH-1 negative case** (fast-clearing 0-matched lay → `final_full`, never `failed`) → **R1 watch** (partial→full lay converges to TRUE stake, never stored-low `FINAL_FULL`) → **R2 watch** (still-pending lay keeps its price) → then settlement-on. Clears **B2↔B3**. Flags OFF until it passes.
- **Operator commit-time:** HIGH-2 (stage/commit B3 vs the shared S222/S223 uncommitted tree); LOW-5 (`*.db.bak-*` gitignore, don't `git add -A`).
- B4 promo-seed; Betfair-entry flexibility scoping; natural-monitoring watch-list (post-B7); cutover B5/B6.

## Session close state

bethub-v3 at `e2638fac`, both workers OFF, no git writes, v2 untouched. Artifacts in `bethub-rebuild/`: `b3_r2_hardening_report.md` (COMPLETE), `b3_governance_close.md` (fix-side close). `current_state.md` rotated; `cutover_readiness_map.md` + `v3_build_picture.md` updated; `SESSION_226.md` written; **S227 opens with the operator's supervised live-proof**. **Bet-safety CLEAN.**
