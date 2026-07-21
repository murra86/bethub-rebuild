# B3 — HIGH-1 hardening + test-gap fix (Code commission, cautious)

**Session:** S225 governance → commissioned for a Claude Code **fix** session in `bethub-v3`.
**Type:** Targeted fix + tests. Verify-first (the finding is adversarial — confirm it before fixing); no git write ops.
**Codebase:** bethub-v3 @ HEAD `e2638fa`, B3 (P1–P4) built additively on the in-flight settlement-worker dirty tree.
**Grounds (read first):** `b3_verification_report.md` (findings HIGH-1, MEDIUM-1/2/3/4, LOW-2), `b3_lay_settlement_fix_report.md` (the build), `b3_lay_settlement_fix_design.md`.
**Governing DRs:** DR-032/033, DR-030, DR-027/028, DR-019, DR-021.

---

## 0. Why this exists + the unifying principle

The max-effort adversarial verify passed everything **except** the P3 recovery path, where it found a confirmed HIGH money-path hole: the fix **re-books the incident-class winner at $0/`FAILED`** in P3's own target window (a 0-matched lay that matches, clears out of `listCurrentOrders`, and whose cleared-orders read misses on the pass that first sees it absent — then the market-settlement fall-through returns `FAILED` off the stale stored `matched_stake=0`, terminally, with no self-heal). Everything downstream of that (P1/P2/P4, the gate, the valve, the race discipline) is sound.

**The one principle that fixes the whole class:**
> **Never terminalise a bet to `FAILED`** (a permanent, unrecoverable, sweep-excluded, $0 state) **unless there is a CONCLUSIVE signal it never matched.** When the signal is missing or inconclusive — cleared-orders read `ReadUnavailable` or `found=False`, or a cleared row with `sizeSettled>0` but no `priceMatched` — **carry forward (return no decision)** so a later pass retries. The P4 park valve is the backstop for anything that genuinely never resolves (it parks to manual; it never mis-settles). A wrong `FAILED` is worse than a slow one.

---

## 1. Verify the diagnosis first (Phase 0 — hard gate, no fix yet)

The finding is adversarial and could be wrong. Confirm first-hand at HEAD `e2638fa` (working tree); if it does **not** hold, STOP and report rather than "fixing" a non-bug:
1. In `_resolve_one` (`workflows/bet_entry/v1/reconciliation.py`), confirm the absent-from-current-orders path, when the Step-3.5 cleared read returns `ReadUnavailable`/`found=False` **and** `record.matched_stake == 0` **and** `get_market_settlement` returns `settled_time is None`, resolves to **`FAILED`** (pre-settlement branch ~`:351-361`; post-settlement equivalent ~`:416-431`).
2. Confirm real Betfair REST yields `settled_time is None` (the S222/S223 fact; `_translation.py` ~`:676-678`).
3. Confirm `FAILED` is excluded from the reconciliation sweep (`statuses=(PROVISIONAL, PROVISIONAL_PENDING)`, ~`:470-476`) **and** the park valve (`list_stalled_unreconciled_bets` selects `PROVISIONAL*`) → no self-heal.
4. Confirm MEDIUM-4: `update_match_status` is called only `if decision.new_status != record.match_status` (~`:492`), so a lay matching incrementally **in-orders** (`still_pending_in_orders` → stays `PROVISIONAL_PENDING`) never persists its growing `matched_size` until a terminal transition.

If 1–4 confirm → proceed. If any is WRONG → STOP and write a findings report.

---

## 2. The fixes (land together)

### Fix A — HIGH-1: carry-forward, never mis-`FAILED` (the core)
In `_resolve_one`'s absent path, gate the `matched_stake==0 → FAILED` resolutions (both pre- and post-settlement) on a **conclusive negative**. Specifically: when `record.matched_stake == 0` and the Step-3.5 cleared read was **inconclusive** (`ReadUnavailable` or `found=False`), return **no decision** (carry-forward) with a distinct reason code (e.g. `absent_zero_stake_cleared_inconclusive`) — do **not** return `FAILED`. Only return `FAILED` for a 0-stake bet when there is a **conclusive** never-matched signal (a cleared row present with `sizeSettled==0` / `betOutcome` lapsed-or-void, or the existing market void/removed-runner branch). Preserve all current behaviour where `matched_stake>0` (those already resolve `FINAL_FULL`).

### Fix B — MEDIUM-1: `sizeSettled>0` with null `priceMatched` must not mis-`FAILED`
In the Step-3.5 cleared-won branch (~`:290-293`), a cleared row with `matched_size>0` but `average_matched_price is None` currently drops to lapsed → `FAILED/$0`. Apply the principle: a positive `sizeSettled` is evidence it matched, so **do not `FAILED`** — carry-forward (retry; price may populate) rather than terminalise. (Do not fabricate a price to force `FINAL_FULL`; carry-forward is the safe resolution, and the park valve backstops a never-priced fill.)

### Fix C — MEDIUM-4: persist mid-flight `matched_size` every pass
Persist the live `matched_stake`/`matched_price`/`unmatched_stake` whenever the reconciliation read shows they changed, **even if `match_status` is unchanged** (`still_pending_in_orders` staying `PROVISIONAL_PENDING`). Drop/loosen the `new_status != record.match_status`-only write guard (~`:492`) so the stake write fires on a stake delta. This keeps the stored stake tracking the true in-orders fill, which (a) directly shrinks the HIGH-1 exposure — a bet that clears after partial in-orders persistence resolves `FINAL_FULL` off a true stored stake, not 0 — and (b) is correct on its own. Keep the B4 invariant intact: **still write only match fields + bookkeeping, never `settlement_state`.**

*(These three are one coherent change: A stops the wrong terminalisation, B closes the sibling null-price path, C removes the stale-value amplifier that feeds A.)*

---

## 3. The test gaps (close all — green-by-omission is what hid HIGH-1)

- **MEDIUM-2 (the HIGH-1 branch):** add a `_resolve_one` test driving `{record.matched_stake==0} + {cleared read ReadUnavailable}` and again `{... + cleared found=False} + {settled_time=None}` → assert **carry-forward / no decision** (post-fix), NOT `FAILED`. AND make the coupled acceptance test (`test_gate_then_reconcile_then_settle_end_to_end`) drive `run_reconciliation_pass` **through the real cleared-orders path**, not a manual `storage.update_match_status(FINAL_FULL, 4.98)` simulation, so it can actually catch a mis-`FAILED`.
- **MEDIUM-3 (provisional-pass gate):** add a pass-level test asserting `run_provisional_resolution_pass` **excludes** a `PROVISIONAL_PENDING` row (regression-locks the `exclude_match_statuses` kwarg at `settlement.py:1501`; a dropped kwarg would let the provisional pass auto-resolve a valve-parked bet at its stale stake and stay green).
- **LOW-2 (money-safety invariant):** add a test asserting `run_reconciliation_pass` / `_resolve_one` **never write `settlement_state`** — locks "reconciliation moves no money" against future regression.
- **Add the Fix-B and Fix-C tests:** `sizeSettled>0 + null price → carry-forward`; and a stake-delta-persists-without-status-change test for Fix C.

**Recommended cheap adds (include if clean, else note):** LOW-1 — sum `sizeSettled` across multiple cleared rows per `betId` rather than `matching[0]` (`betfair_adapter.py:337`) + pin Betfair `groupBy`, so a fragmented fill can't undercount.

---

## 4. Prove

`uv run pytest` fully green (report the new count; expect > 1327). Every new test must **fail against the pre-fix code and pass after** (state this for the HIGH-1 test specifically — it must be red before Fix A). No existing assertion weakened. Then leave/point to the live-proof runbook — the §4.4 negative case (a 0-matched lay that clears fast must converge to `final_full`/true stake, never `failed`) is now the load-bearing live check.

## 5. Boundaries

HEAD stays `e2638fa`; **no git write ops** (incl. the dirty tree — layer additively, as the build did; do not commit/stash/discard). `BETHUB_SETTLEMENT_WORKER` OFF; no worker run live; no live Betfair; no place/settle/money-move; DB reads `mode=ro`. DR-030/032/019/021 respected. **Do not touch** the S222/S223 settlement-worker dirty hunks — only the B3 P3/reconciliation surface + its tests.

## 6. Deliverable — `b3_high1_fix_report.md`
Phase-0 confirmation (or STOP); what changed per Fix A/B/C with file:line; the new/updated tests and proof each is red-before/green-after; full-suite result; confirmation the B4 no-`settlement_state` invariant is intact; any deviation flagged. End the final line with the sentinel `<!-- B3 HIGH1 FIX COMPLETE -->` (or `<!-- B3 HIGH1 STOPPED -->` if Phase 0 refutes the finding).

---

## Ready-to-paste Code session prompt

> **Task (CAUTIOUS FIX — verify the finding first, then fix; no git writes):** An adversarial verify of the B3 LAY fix (bethub-v3 @ HEAD `e2638fa`) found a confirmed HIGH money-path hole (HIGH-1 in `b3_verification_report.md` — read it + `b3_lay_settlement_fix_report.md`). The P3 cleared-orders fall-through re-books the incident-class winner at $0/`FAILED`: a 0-matched lay that matches, clears out of `listCurrentOrders`, and whose cleared read misses → market-settlement fall-through returns `FAILED` off stale `matched_stake=0` (real REST `settled_time` is always None), terminally, excluded from sweep+valve, no self-heal. Guiding principle: **never terminalise a bet to `FAILED` without a CONCLUSIVE never-matched signal; when the cleared read is inconclusive, carry-forward (no decision) and let the park valve backstop.**
>
> **Phase 0 (hard gate, no fix):** confirm first-hand in `reconciliation.py::_resolve_one` that `{matched_stake==0} + {cleared read ReadUnavailable/found=False} + {settled_time=None}` → `FAILED` (~:351-361 / :416-431); that `FAILED` is excluded from the sweep (:470-476) and the valve; and that `update_match_status` only fires on status change (~:492) so in-orders `matched_size` never persists. If it doesn't hold, STOP and report.
>
> **Fix (land together):** (A/HIGH-1) when `matched_stake==0` and the cleared read was inconclusive, return **no decision** (new reason e.g. `absent_zero_stake_cleared_inconclusive`), not `FAILED`; only `FAILED` on a conclusive never-matched signal (cleared row `sizeSettled==0`/lapsed, or void/removed). (B/MEDIUM-1) cleared `sizeSettled>0` with null `priceMatched` → carry-forward, not `FAILED` (don't fabricate a price). (C/MEDIUM-4) persist `matched_stake`/`matched_price`/`unmatched_stake` on a stake delta even when `match_status` is unchanged (loosen the :492 status-only write guard) — never write `settlement_state`.
>
> **Tests (close the green-by-omission gaps):** MEDIUM-2 — drive `{matched_stake==0}+{cleared unavailable}` and `{...found=False}+{settled_time None}` → assert carry-forward not `FAILED`, AND make `test_gate_then_reconcile_then_settle_end_to_end` run the real `run_reconciliation_pass` cleared-orders path (not a manual update_match_status). MEDIUM-3 — assert `run_provisional_resolution_pass` excludes `PROVISIONAL_PENDING`. LOW-2 — assert reconciliation never writes `settlement_state`. Plus tests for Fix B and Fix C. Recommended: LOW-1 — sum `sizeSettled` across multiple cleared rows per betId.
>
> **Prove:** `uv run pytest` fully green; the HIGH-1 test must be **red before Fix A, green after**; no existing assertion weakened.
>
> **Boundaries:** HEAD `e2638fa`, no git write ops (incl. dirty tree — layer additively, don't touch the S222/S223 hunks); `BETHUB_SETTLEMENT_WORKER` OFF; no live Betfair; no money-move; DB reads mode=ro; DR-030/032/019/021. Report `b3_high1_fix_report.md` — Phase-0 result, per-fix file:line, red-before/green-after proof, suite count, B4 invariant intact; end the final line with `<!-- B3 HIGH1 FIX COMPLETE -->` (or `<!-- B3 HIGH1 STOPPED -->`).

---

*Read-only commission draft — no code touched; bethub-v3 byte-identical at `e2638fa`.*
