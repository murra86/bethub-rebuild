# B3 — LAY money-path fix (build commission, cautious/verify-first)

**Session:** S225. Commissioned for a Claude Code **build** session in `bethub-v3`, on operator approval of `b3_lay_settlement_fix_design.md`.
**Type:** Build — but **gated**: a mandatory verify-and-challenge phase precedes any code. Treat the design as a **hypothesis to validate, not a spec to obey**.
**Codebase:** bethub-v3 @ HEAD `e2638fa`. An in-flight settlement-worker **dirty tree** is present and is a coordination precondition (Phase 0).
**Grounds (read first, in order):** `b3_lay_settlement_fix_design.md` (the proposal), `b3_lay_settlement_investigation_report.md` (evidence, incl. §10 closed gaps).
**Governing DRs:** DR-032/033 (Betfair settlement spine / data-source roles), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-019 (derived state on read), DR-021 (Adelaide anchors).

---

## 0. Prime directive — be cautious, and flag anything off

This design was authored by a governance session that got the **first** version of this fix wrong (it proposed "just wire the worker," which a review falsified). So: **do not assume the design is correct.** Your first job is to try to break it. If any assumption below does not hold in the code, or a simpler/safer approach exists, or the change is riskier than described — **STOP and write a findings report; do not build past the flaw.** Building the wrong money-path fix is worse than building nothing.

You have standing authority to deviate from this design where the code shows it's wrong — but surface the deviation and your reasoning in the report *before* implementing it. Silence-and-proceed is not acceptable on a money path.

---

## Phase 0 — VERIFY & CHALLENGE (no code yet; this is a hard gate)

Re-ground every load-bearing claim first-hand at HEAD `e2638fa`. For each, record CONFIRMED / WRONG / INCOMPLETE with file:line. **If any is WRONG or INCOMPLETE in a way that changes the fix, STOP and report before writing code.**

**A. Root-cause premises (must all hold or the design changes):**
1. `place_lay` (`ui/api/routers/racing.py:~1105-1109`) writes a not-fully-matched lay terminally as `FINAL_PARTIAL`; nothing revisits it. Confirm there is no other post-placement update path for Path-A lays.
2. `run_reconciliation_pass` sweeps only `PROVISIONAL`/`PROVISIONAL_PENDING` (`reconciliation.py:~416`); the live worker (`ui/api/settlement_worker.py`) runs no reconciliation pass.
3. `_resolve_one`'s absent-from-orders path trusts stored `matched_stake` (`reconciliation.py:~284-377`); `get_order_state` provides no live matched-size for a cleared order (`betfair_adapter.py:~262-267`).
4. `list_unsettled_bets` has no match-status predicate (`store/repositories/bets.py:~838`).

**B. Challenge the design's own risk points (this is where it most likely breaks):**
5. **P1 blast radius.** Grep every consumer of `MatchStatus.FINAL_PARTIAL` and `FINAL_FULL` for LAY bets — balance derivation, settlement, UI/provisional surfaces, any sweep or invariant. Does anything assume an unmatched lay is `FINAL_PARTIAL`, or that `PROVISIONAL_PENDING` never carries a `settlement_state=PENDING` lay? If re-labelling to `PROVISIONAL_PENDING` breaks or changes any of these, report it — this is the most likely place the design is wrong.
6. **P4 stall risk.** Confirm the settlement-gate design (exclude `PROVISIONAL*`) does not permanently strand any legitimately-settleable bet, and that a workable park/escalation signal exists (`reconciliation_attempts` / `last_reconciled_at` are populated and updated). If the "safety valve" can't be built cleanly from existing signals, say so.
7. **P3 feasibility.** Confirm a `listClearedOrders` surface exists (or can be added) in the Betfair client and returns real `sizeMatched`/`averagePriceMatched`; confirm the resolver can consume it without violating DR-030/032. If cleared-orders data isn't actually available, P3's approach must change.
8. **Coupling sanity.** Confirm the post-fix flow (§4 of the design) actually holds: reconciliation writes only match fields, settlement_state stays PENDING from placement, so a terminalised lay then settles with the true stake. If reconciliation or settlement touches state in a way that breaks this handoff, report it.

**C. Dirty-tree coordination (operator decision — do not resolve unilaterally):**
9. Report the uncommitted working-tree changes (`git status`, `git diff --stat`) — expected: the in-flight settlement-worker / post-settlement-void work touching `record_builder.py`, `settlement.py`, `betfair_adapter.py`, `clients/betfair_client/v1/settlement.py`, etc. State whether any of them **move the anchors** in A/B above (i.e. the dirty version differs from HEAD at your edit sites). **Do not commit, stash, or discard anything.** If B3's edits would collide with or depend on the dirty changes, STOP and report — the operator decides whether to land the in-flight work first.

**Phase-0 exit:** If A confirms, B raises nothing that changes the fix, and C shows no collision → you MAY proceed to Phase 1 in the same session, opening your report with the validation results. **If anything in A/B/C trips → STOP, write `b3_lay_settlement_fix_findings.md`, and do not build.** When in doubt, stop.

---

## Phase 1 — BUILD (only on a clean Phase 0), full P1–P4 together

Land the four parts as one coherent change (they are coupled — see design §5; do **not** ship P1+P2 without P4).

- **P1 — Placement re-label.** `racing.py:~1105-1109`: `remaining <= 0 → FINAL_FULL` (unchanged); `remaining > 0 → PROVISIONAL_PENDING` (was `FINAL_PARTIAL`). `matched_stake` stays the placement-instant matched size.
- **P2 — Wire the periodic reconciliation worker.** New `ui/api/reconciliation_worker.py` mirroring `settlement_worker.py` (gate → cycle → handle → loop → start), interval `DEFAULT_RECONCILIATION_INTERVAL_SECONDS`, `asyncio.to_thread`, one-bad-pass-logs-and-continues, cancel-and-await teardown. Expose `RealBetfairAdapter` via a cached `_betfair_adapter()` factory on `app.state` (client + audit_sink + operator_identity; note the streaming-client requirement). Lifespan: bring up reconciliation **before** the settlement worker. Config: `reconciliation_worker: bool = True` binding `BETHUB_RECONCILIATION_WORKER` (opt-out kill switch), gate `betfair_mode == "live" and settings.reconciliation_worker`; independent of `BETHUB_SETTLEMENT_WORKER`.
- **P3 — Cleared-order true-stake recovery.** Add a `listClearedOrders` read to the Betfair client + adapter; in `_resolve_one`'s absent-from-orders path (`reconciliation.py:~284-377`), consult it for the real matched size/price before the market-settlement disambiguation. Resolve cleared-won → `FINAL_FULL` with true stake; cleared-lapsed / never-matched → `FAILED`.
- **P4 — Settlement match-status gate + safety valve.** Add a match-status predicate to the settlement sweep (`list_unsettled_bets`, `bets.py:~838`) excluding `PROVISIONAL`/`PROVISIONAL_PENDING`. Add the park-not-settle escalation for un-reconcilable bets (threshold per design §6 decision 2 — propose the exact threshold in your report and implement it; fail closed). Compose with the existing winner-less-hold / park machinery in `settlement.py`.

**No backfill** — the mis-valued live row is being cleared at live-proof (operator direction).

---

## Phase 2 — PROVE

- **Unit/integration, green before you stop:** P1 status mapping (unmatched/partial/full lay); P2 lifespan start/teardown; P3 resolver branches (cleared-won / cleared-lapsed / never-matched) via the new cleared-orders read; P4 gate excludes `PROVISIONAL*` and the safety valve parks a no-`betfair_bet_id` bet. Existing `test_reconciliation.py` / settlement tests stay green (adjust only where P1/P4 legitimately change expected behaviour — call out every changed assertion in the report).
- **Live re-prove is the operator's step (S189), not yours** — do not start any worker or run the live app to settle. Leave a precise runbook in the report: place an unmatched lay → it matches on Betfair → the worker reconciles it to the true `matched_stake` before it settles → it settles with the true money; a lapsed lay resolves `FAILED`.

---

## Boundaries / disciplines (load-bearing)

- **Bet-safety (Cat 4).** This touches placement labelling, a new Betfair read, and settlement gating — all money-path. **`BETHUB_SETTLEMENT_WORKER` stays OFF**; do not run the app in a mode that auto-settles; do not place/settle/move money. `BETHUB_RECONCILIATION_WORKER` defaults on-in-live but you do not run it live — unit tests only.
- **Git.** HEAD stays `e2638fa` unless the operator (via Phase 0) directs otherwise. **No git write ops** (add/commit/stash/checkout/branch/discard) — including on the dirty tree. Your changes stay in the working tree for operator review.
- **DR-030** module boundaries; **DR-032/033** Betfair-only settlement spine (the cleared-orders read lives behind the client boundary); **DR-019** derived-on-read (don't add a stored P&L); **DR-021** Adelaide anchors on any new timestamps/log lines.
- **capture.db / operational DB** — reads `mode=ro` only; no writes.

---

## Reporting

Produce **`b3_lay_settlement_fix_report.md`** (or `..._findings.md` if you STOP in Phase 0):
- Phase-0 validation table (A/B/C, each CONFIRMED/WRONG/INCOMPLETE + evidence) — **lead with this**, including anything about the design that was off.
- Dirty-tree assessment + whether you proceeded or stopped, and why.
- Per-part: what changed, why, any deviation from the design and its rationale.
- Every changed test assertion, with justification.
- Suite result; the live re-prove runbook for the operator.
- Open risks / anything you were unsure about.

End the report's final line with the sentinel `<!-- B3 BUILD COMPLETE -->` (or `<!-- B3 STOPPED PHASE0 -->`) so the governance watcher can trigger triage.

---

## Ready-to-paste Code session prompt

> **Task (CAUTIOUS BUILD — verify first, flag anything off):** Implement the B3 LAY money-path fix in bethub-v3 @ HEAD `e2638fa`, per `b3_lay_settlement_fix_design.md` (read it + `b3_lay_settlement_investigation_report.md` first). **The design's author got the first version of this fix wrong — treat the design as a hypothesis to validate, not a spec. If any premise is wrong, a consumer breaks, or a safer approach exists, STOP and write a findings report before building. Silence-and-proceed is not acceptable on a money path.**
>
> **Phase 0 (hard gate, no code):** re-ground first-hand — (A) `place_lay` writes an unmatched lay terminally as `FINAL_PARTIAL` and nothing revisits it; reconciliation sweeps only `PROVISIONAL*`; the live worker runs no reconciliation pass; the resolver absent-path + adapter give no live matched-size for a cleared order; settlement has no match-status gate. (B) **Challenge the risk points:** grep every `FINAL_PARTIAL`/`FINAL_FULL` consumer for lays — does re-labelling to `PROVISIONAL_PENDING` break anything? Can the P4 settlement-gate strand a settleable bet? Does `listClearedOrders` actually return real matched size? Does the post-fix handoff (reconcile writes match fields only, settlement_state stays PENDING) hold? (C) **Dirty tree:** report `git status`/`diff --stat` (expected: in-flight settlement-worker work touching settlement.py/betfair_adapter.py/record_builder.py); state whether it collides with your edit sites; **do not commit/stash/discard.** If anything in A/B/C trips, STOP and report. Otherwise proceed, leading your report with the validation results.
>
> **Phase 1 (only if Phase 0 clean), full P1–P4 together (coupled — never P1+P2 without P4):** P1 — `racing.py:~1105-1109` write `PROVISIONAL_PENDING` when `remaining>0`. P2 — new `ui/api/reconciliation_worker.py` mirroring `settlement_worker.py`; cached `_betfair_adapter()` on `app.state`; lifespan brings reconciliation up before settlement; config `reconciliation_worker: bool = True` (`BETHUB_RECONCILIATION_WORKER` opt-out), independent of the settlement flag. P3 — add `listClearedOrders` to client+adapter; consult it in `_resolve_one`'s absent path for real matched size (cleared-won → FINAL_FULL true stake; lapsed/never-matched → FAILED). P4 — match-status predicate on `list_unsettled_bets` excluding `PROVISIONAL*`, plus a park-not-settle safety valve for un-reconcilable bets (propose+implement the threshold; fail closed).
>
> **Phase 2:** unit/integration green (P1 mapping, P2 lifespan, P3 cleared-orders branches, P4 gate + park); leave the live re-prove as an operator runbook — do NOT start a worker or auto-settle.
>
> **Boundaries:** HEAD `e2638fa`, no git write ops (incl. the dirty tree); `BETHUB_SETTLEMENT_WORKER` stays OFF; no place/settle/money-move; DB reads `mode=ro`; DR-030/032/019/021. Report to `b3_lay_settlement_fix_report.md` (or `..._findings.md` if stopped), leading with the Phase-0 validation, ending the final line with `<!-- B3 BUILD COMPLETE -->` (or `<!-- B3 STOPPED PHASE0 -->`).

---

*Read-only commission draft — no code touched; bethub-v3 byte-identical at `e2638fa`; dirty tree unchanged.*
