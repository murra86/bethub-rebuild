# SESSION 222 — Settlement-correctness re-scope: investigated → deep Code design pass → three money-path decisions LOCKED (build commissioned)

**Opened:** 2026-07-03 (headless runner — settlement-correctness investigation)
**Closed:** 2026-07-03 19:24 ACST
**Tool routing:** headless runner (read-only investigation); Chat (verified the crux; commissioned + triaged a Code Plan-Mode design pass; locked the money-path decisions; close). Code ran two read-only passes (investigation-continuation + a design pass with 3 blast-radius sub-agents). **No code/test/flag/DB/Betfair writes anywhere; bethub-v3 byte-identical at `e2638fa`.**
**Governing DRs:** DR-021 (Adelaide anchors), DR-032 (Betfair settlement spine), DR-033 (settlement Betfair-only), DR-030 (module boundaries), DR-027/028 (two-DB boundary).

---

## Anchor
- Open: runner (investigation) 2026-07-03.
- Close: `TZ="Australia/Adelaide" date` → 2026-07-03 19:24 ACST.

## Session shape
Turned the S221 settlement finding into a fully-designed, decision-locked fix — without touching a line of code. Investigation → operator spot-verified the crux → a deeper Code design pass (operator's call, for codebase depth) → triage → three money-path decisions locked → build commissioned for next session.

## What was delivered

1. **Settlement-correctness investigation (headless runner) — `settlement_correctness_investigation.md`.** Confirmed read-only: (a) **nothing in the codebase ever writes `settlement_state="pending"`** — every live bet is born NULL and stays NULL, so the worker's `("pending",)` sweep is structurally empty for *every* live bet (not a reconciliation miss — that's a different axis); (b) the **LAY inversion traced to the money** — the resolver writes a market-objective state but `balance_derivation.py` reads it as the lay's own perspective, so a winning lay books as a full-liability loss (and vice-versa) — a silent ledger inversion. Left two calls to the operator (Option A vs B; lay dead-heat liability).

2. **Operator spot-verified the crux.** Chat independently confirmed the two load-bearing facts: `balance_derivation.py::_bet_cash_return` docstring explicitly interprets `settlement_state` as the **lay's own perspective**; grep confirmed **no `record.side` branch** in the resolver. High confidence — the gaps are real.

3. **Deep Code design pass (Plan Mode, read-only) — `settlement_correctness_fix_design.md` (26 KB).** On the operator's call (for codebase depth), a Code design pass with three blast-radius sub-agents pressure-tested the investigation and resolved the four calls, adding evidence the investigation lacked:
   - **Q1 (Option A vs B):** recommends **Option A** (stamp `PENDING` on the hedge/Betfair builder) + a **targeted one-row backfill** for the repro bet — reframing the investigation's own caveat (the backfill is a targeted, reversible single-row move, not the risky blanket UPDATE; so B is not load-bearing). Blast-radius traces show **B over-sweeps soft-book legs + legacy NULL rows** (a money-path behaviour change), which A avoids by construction; A also keeps the F2 spec/test honest and sidesteps the false-green trap. Offered a guarded-NULL defense-in-depth variant if self-healing is wanted.
   - **Q2 (LAY fix):** invert only the two clean terminals for `side==LAY` (WINNER→SETTLED_LOST, LOSER→SETTLED_WON); VOIDED + guard-park unchanged. **Two refinements over the investigation:** both resolvers need it (it missed `_resolve_provisional_for_bet` :947/:960), and the winner-guard needs **zero** change (its park triggers *are* a losing lay's liability-reduction conditions). Recommends **park-to-PROVISIONAL interim** over computing reduced lay liability.
   - **Q3:** the complete bounded fix — files/anchors, tests (create-path + SQLite-path regression + LAY tests both resolvers), ordering constraint (pending + resolver land together), re-prove plan.
   - **Q4:** invariant held; flag stays OFF until it re-proves.
   - Surfaced **two forward-looking items** (don't auto-settle soft-book — keep manual; a legacy-NULL floor) — neither blocks the re-prove.

4. **Three money-path decisions LOCKED (operator, S222 — all matching Code's recommendation):**
   - **(1) Pending-state fix = Option A** — stamp `PENDING` on the hedge/Betfair builder + a targeted one-row backfill for the repro lay. **Not** the guarded-NULL variant (the self-healing benefit is marginal; a create-path regression test covers the recurrence class).
   - **(2) LAY settlement** — invert the two clean terminals in **both** resolvers; **park lays with a dead-heat/material removed-runner reduction to PROVISIONAL** (manual settle), not compute reduced liability.
   - **(3) Soft-book stays manual** — the worker only auto-settles Betfair legs (Option A does this for free; matches DR-033).

## Standing-instruction adherence check
- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — the whole re-scope was designed **without touching code**; worker OFF throughout; no settlement/store/resolver edits; bethub-v3 byte-identical at `e2638fa`. The build stays gated (worker OFF until it lands + re-proves). ✅
- **Cat 5 (division of labour)** — the money-path decisions (Option A vs variant; lay liability; soft-book scope) surfaced to the operator with recommendations and **locked by the operator**, not taken unilaterally. Codebase-depth analysis correctly delegated to Code (Plan Mode, read-only) at the operator's suggestion. ✅
- **S178 / S189** — the earlier one-line brief's ungrounded premise (S221) is now fully remediated by design-before-brief; the LAY gap is the S189 "green-on-fixtures" lesson, now designed out. ✅
- **First-action gate (S200)** — S223 first action = triage the settlement-correctness build report (guarded); Code build commissioned via the prompt in the S223 opening prompt.
- No standing-instruction edits → no Cat-2 sweep.

## Open items
Pointer-only — full list in `current_state.md`.

**New / changed in S222:**
- Settlement fix **fully designed + three money-path decisions LOCKED** (`settlement_correctness_fix_design.md` is the execution spec). Build commissioned for S223. Worker OFF until it lands + re-proves.
- Two forward-looking items flagged: soft-book auto-settle scope (default: manual); legacy-NULL floor.

**Closed in S222:**
- Settlement-correctness investigation + Code design pass + the three decisions. ✅

**Carried to S223:**
- **Triage the settlement-correctness build report** (first action, guarded — Code builds out-of-session against `settlement_correctness_fix_design.md` with the 3 decisions locked; verify all edits landed together, the LAY re-prove against the repro bet, worker still OFF).
- **Placings health-by-hour sweep map** (companion, ready ~08:30 ACST 2026-07-04) → commission run re-timing.
- Cutover runway B1/B3/B4/B5/B6; promo-seed; re-confirm interim pieces.

## Session close state
Root clean; `settlement_correctness_fix_design.md` + `settlement_correctness_investigation.md` present; no phantom files. `.close_out_backups/` swept to the S223 prompt only. `current_state.md` rotated; `v3_build_picture.md` header updated. **Bet-safety CLEAN** — worker OFF, no code touched anywhere, bethub-v3 byte-identical at `e2638fa`; v2 untouched. The VPS carries the S219 FIX 1 + the read-only health sweep (completing ~08:30 ACST 2026-07-04). App stopped (relaunch worker-OFF when the tool is wanted).

## Forward routing
**Confirmed with operator.** S223 first action = **triage the settlement-correctness build report** (guarded). Code builds out-of-session against `settlement_correctness_fix_design.md` with the three locked decisions (Option A + backfill; both-resolver LAY inversion + park-interim; soft-book manual) — all edits landing together, ending in a re-prove against the repro LAY; the worker stays OFF until then. The ready-to-paste Code build prompt is in the S223 opening prompt. Companion (time-gated ~08:30 ACST 2026-07-04): read the placings health-by-hour sweep map and commission the run re-timing. **The runner was NOT fired at this close** — both first-action inputs are unavailable tonight (the operator runs the money-path build supervised; the placings map isn't ready until morning), so an auto-fire would only hold.
