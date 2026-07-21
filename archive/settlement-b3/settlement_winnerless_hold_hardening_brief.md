# Brief — settlement winner-less-market hold (the last money-path tail)

**Drafted:** Session 223, 2026-07-03 ACST (DR-021 Adelaide anchor).
**Author:** Chat (governance / operator-facing).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (dirty tree — worker build + S222 LAY + S223 settled-signal + S223 batched read-path fix).
**Routing:** Claude Code, read-write (dirty-tree rules).
**Grounding:** `settlement_readpath_batched_fix_report.md` §3 (the residual it surfaced but did not build).
**Worker flag:** `BETHUB_SETTLEMENT_WORKER` stays **OFF**; Code does not flip it.

---

## 0. Why this exists (plain English)

The batched read-path fix closed every found gap and left the money-path airtight **except one documented tail**: a theoretical closed market presented as *"has losers, but no winner at all"* would settle a **losing** bet to a wrong terminal state (a back bet → LOST, a lay → WON) instead of holding it. Betfair does **not** emit a winner-less settled racing market in practice — so this is insurance against a non-event — but the operator has elected to close it so the "no silent wrong-settle" invariant is genuinely complete.

This is a **defensive hold**, not a settlement: the failure direction is "park for manual," never "pay wrong." No downside.

---

## 1. The fix

A real settled racing market **always has at least one WINNER** (a dead heat has ≥2; a normal win/place market has 1..N). So a **CLOSED** market with **zero WINNER runners and ≥1 LOSER** is never a legitimately-settled market — it is either a mid-settlement read (losers stamped before the winner) or an anomalous/void shape. Either way: **hold, don't settle.**

**Where:** `workflows/bet_entry/v1/settlement.py`, **both** resolvers — `_resolve_settlement_for_bet` and `_resolve_provisional_for_bet` — as a readiness check, placed **after** the existing `market_status == CLOSED` and `market_voided` steps and the existing `unexpected_state_count` readiness gate, and **before** the leg-runner resolution (Step 6).

**The condition (tight and provably safe):**
```
winner_count = count of settlement.runners with status == WINNER
loser_count  = count of settlement.runners with status == LOSER
if winner_count == 0 and loser_count >= 1:
    → no decision; reason `market_winnerless_hold`; bet stays PENDING / PROVISIONAL
```

**Why this exact predicate — trace every case:**
- **Normal win market** (1 WINNER): `winner_count >= 1` → no hold → settles as today. ✅
- **Dead heat** (≥2 WINNER): `winner_count >= 1` → no hold → F1 dead-heat guard still parks it. ✅
- **Fully-removed / all-REMOVED market** (0 WINNER, 0 LOSER, all REMOVED): `loser_count == 0` → **no hold** → falls through to the leg's runner-REMOVED → **VOIDED** self-heal. ✅ (This is the case that must NOT be held — the predicate excludes it via `loser_count >= 1`.)
- **Winner-less with losers** (the tail; also a transient mid-settlement read): `winner_count == 0 and loser_count >= 1` → **hold** for manual / next cycle. ✅ (Bonus: a transient read where losers land before the winner now correctly waits instead of racing.)

No legitimate settled racing market lands in the hold branch — so this cannot suppress a correct settlement.

**Reason code:** add `market_winnerless_hold` to the `SettlementReasonCode` Literal; roll it into the same pending/provisional counters the existing `runner_not_yet_resolved` reason uses (a hold, not a terminal). No new state.

**No translation edit, no enum edit** — the resolver already holds `settlement.runners` with per-runner `settlement_status`; it counts from there. If the fix appears to need a translation or enum change, STOP and surface (it shouldn't).

---

## 2. Tests

Add to `tests/workflows/bet_entry/v1/test_settlement.py` (drive through the real path where practical):
- **The tail — both resolvers:** a CLOSED market with 0 WINNER and ≥1 LOSER → a bet on a LOSER selection **holds** (`market_winnerless_hold`), does **not** settle LOST (back) or WON (lay). One test each for `_resolve_settlement_for_bet` (PENDING) and `_resolve_provisional_for_bet` (PROVISIONAL).
- **Exclusion regression — all-REMOVED still voids:** a CLOSED market where every runner is REMOVED (0 WINNER, 0 LOSER) → a bet on a REMOVED selection still resolves **VOIDED** (not held). This is the guard against over-holding.
- **Normal-market regressions:** single WINNER → SETTLED_WON/SETTLED_LOST as today (no hold); a dead heat (≥2 WINNER) → still parks via the F1 guard (no hold pre-empting it).
- **Transient bonus (optional):** a read with losers present but the winner not yet stamped → holds, and a follow-up read with the winner present → settles.
- **Keep green:** all S222 LAY, S223 settled-signal + batched read-path tests, the `paid_full` guard suite, BACK mapping, F2 pending-sweep. `uv run pytest` green; `mypy` clean; no new `ruff`.

---

## 3. Re-prove

- Bench: the new hold tests + the all-REMOVED exclusion regression are the proof.
- Real anchor: confirm the Gossamer Glow capture (1 WINNER, laid selection LOSER) **still settles SETTLED_WON** — it has a winner, so the new hold branch does not touch it.

---

## 4. Disciplines

- **Read-and-confirm gate:** read this brief + `settlement.py` (both resolvers) end-to-end before editing.
- **Dirty-tree rules:** `git status` at start; edit **only** `workflows/bet_entry/v1/settlement.py` + `tests/workflows/bet_entry/v1/test_settlement.py`; `git diff` after each; **no git write ops**; HEAD stays `e2638fa`.
- **Bet-safety:** `BETHUB_SETTLEMENT_WORKER` stays **OFF** (operator flips it); no placement, no DB writes, no live Betfair calls. The failure direction of this change is a hold (manual), never a settlement — verify that holds for every case in §1.
- **Scope:** the two resolvers only; the predicate is exactly §1 — do not broaden it (e.g. don't hold on `loser_count == 0`, which would break the all-REMOVED self-void). If broader logic seems needed, STOP and surface.
- **Report:** produce `settlement_winnerless_hold_hardening_report.md` in the rebuild folder.

---

## 5. Governing DRs

DR-032/033 (Betfair settlement source of truth) · DR-030 (module boundaries) · DR-027/028 (two-DB boundary) · DR-021 (Adelaide anchors).
