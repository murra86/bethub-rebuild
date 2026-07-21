# Report — settlement winner-less-market hold (the last money-path tail)

**Session:** 223 (continuation), 2026-07-03 ACST (DR-021 Adelaide anchor).
**Author:** Claude Code (read-write, dirty-tree rules).
**Brief:** `settlement_winnerless_hold_hardening_brief.md`.
**Codebase:** bethub-v3 @ HEAD `e2638fa` (unchanged — dirty tree carries the accumulated
worker build + S222 LAY + S223 settled-signal + S223 batched read-path work).
**Worker flag:** `BETHUB_SETTLEMENT_WORKER` stays **OFF** — not flipped by this task.
**Files edited (only these two):** `workflows/bet_entry/v1/settlement.py`,
`tests/workflows/bet_entry/v1/test_settlement.py`. **No git write ops.**

---

## 0. Outcome

Built the one hardening the brief specifies, in **both** resolvers. A **CLOSED** market
with **0 WINNER runners and ≥1 LOSER** is never a legitimately-settled racing market, so
both resolvers now **hold** (bet stays PENDING / PROVISIONAL) instead of settling the leg's
LOSER selection to a wrong terminal (a BACK bet → LOST, a LAY bet → WON). The failure
direction is a **park for manual**, never a wrong settle — verified for every case.

- `uv run pytest`: **1289 passed, 1 xfailed** (full suite). Settlement suite **115 passed**.
- `paid_full` guard + post-settlement-void + settlement-worker suites: **34 passed**.
- Gossamer Glow real-capture anchor: **re-proven SETTLED_WON** (+$4.84 collect) — it has a
  winner, so the hold does not touch it.
- `mypy` on the production module `settlement.py`: **clean** (strict).
- **No new `ruff`** (proved against the HEAD blobs — see §6).
- HEAD stays `e2638fa`; predicate is **exactly** brief §1 (no broadening, no narrowing).
- **No translation edit, no enum edit** — none was needed.
- Independent **adversarial verification** (3 lenses): all **upheld**, high confidence,
  **zero blockers/majors** (see §7).

---

## 1. The fix (`settlement.py`)

Five surgical, additive edits — no import changes, no logic removal.

### 1a. Reason code added to the `SettlementReasonCode` Literal

```python
    "runner_not_yet_resolved",
    # Winner-less-market hold (winnerless-hold hardening) — a CLOSED market
    # with 0 WINNER runners and >=1 LOSER is never a legitimately-settled
    # racing market ... A hold, not a terminal — counted with
    # `runner_not_yet_resolved`.
    "market_winnerless_hold",
```

### 1b. The hold — in **both** resolvers

Placed **after** the `market_status == CLOSED` step (Step 3), **after** the `market_voided`
step (Step 5), and **after** the `unexpected_state_count` readiness gate (Step 6′), and
**before** the leg-runner REMOVED/WINNER/LOSER resolution — identically in
`_resolve_settlement_for_bet` (→ stays PENDING) and `_resolve_provisional_for_bet`
(→ stays PROVISIONAL):

```python
    winner_count = sum(
        1 for r in settlement.runners
        if r.settlement_status == RunnerSettlementStatus.WINNER
    )
    loser_count = sum(
        1 for r in settlement.runners
        if r.settlement_status == RunnerSettlementStatus.LOSER
    )
    if winner_count == 0 and loser_count >= 1:
        return SettlementDecision(
            new_state=None,                       # HOLD — bet stays PENDING / PROVISIONAL
            dead_heat_count=None,
            removed_runner_count=None,
            unexpected_state_count=None,
            reason_code="market_winnerless_hold",
            detail={
                "market_status": settlement.market_status.value,
                "winner_count": winner_count,
                "loser_count": loser_count,
            },
            source_market_settlement=settlement,  # read-persistence side effect preserved
        )
```

The predicate is **exactly** brief §1 — the case-by-case trace holds:

| Market shape | winner / loser | Outcome |
|---|---|---|
| Normal win market (1 WINNER) | ≥1 / n | no hold → settles as today |
| Dead heat (≥2 WINNER) | ≥1 / n | no hold → F1 dead-heat guard still parks it |
| All-REMOVED (0 WINNER, 0 LOSER) | 0 / **0** | **not held** (`loser_count == 0`) → self-heals to VOIDED via runner-REMOVED |
| Winner-less-with-losers (the tail) | **0 / ≥1** | **HOLD** — `market_winnerless_hold` |

No legitimately-settled racing market lands in the hold branch: a real settled market
always presents its winner runner, so `winner_count ≥ 1` and the predicate is false. The
hold therefore **cannot** suppress a correct settlement.

### 1c. Counter roll-up — a hold, not a terminal

`market_winnerless_hold` is folded into the **same** not-settled carry counter as
`runner_not_yet_resolved`, in **both** pass loops:

- `run_settlement_pass` → `left_pending_market_not_settled`
- `run_provisional_resolution_pass` → `stayed_provisional_market_not_settled`

The `settled_won` / `settled_lost` / `voided` counters live only inside the
`new_state is not None` transition arm, which a hold skips — so a hold can never
mis-increment a terminal counter.

**No other consumer needed updating.** A repo-wide sweep confirmed the only other
`reason_code` surface is `reconciliation.py`, which uses a **separate** `ResolutionReasonCode`
type on a different worker. No translation edit, no enum edit — the resolver already carries
`settlement.runners` with per-runner `settlement_status` and counts from there.

---

## 2. The material discovery — pre-existing winner-less fixtures (operator: read this)

Applying the exact predicate surfaced a non-obvious fact the brief did not anticipate:
**11 existing tests — including two S222 LAY tests and the S223 repro — used winner-less
fixtures.** They built a market containing only the leg's own `LOSER` runner (or a `LOSER`
plus count fields) and **no `WINNER`**, then expected the loser leg to settle. Under the new
(mandated) behavior, those markets are correctly **held**.

Those fixtures were winner-less only **by omission** — a minimal synthetic shape. A real
settled market always carries its winner runner (the real Gossamer Glow capture does, and it
still settles). The brief's own new requirement ("both resolvers hold a CLOSED 0-winner/≥1-loser
market — never settle the loser bet") **supersedes** the old settle-behavior for winner-less
markets, and narrowing the predicate to spare the fixtures is explicitly forbidden. The
faithful resolution — within the explicitly-editable `test_settlement.py`, preserving every
original assertion — was to **restore those fixtures to realistic winner-present markets** by
adding a documented companion WINNER runner (spare selection, never a bet leg):

```python
_WINNER_COMPANION   = RunnerSettlement(selection_id="99999999", settlement_status=WINNER, ...)
_WINNER_COMPANION_2 = RunnerSettlement(selection_id="99999998", settlement_status=WINNER, ...)
```

- Shared helpers touched: `_loser_settlement`, `_loser_for_runner`, `_closed_settlement`
  (companion added only when the leg is not itself the WINNER).
- Inline fixtures touched: the plain-loser, `dead_heat_count=2`, `removed_runner_count=1/8`,
  and three-count terminal-transition fixtures. The two `dead_heat_count=2` fixtures get
  **two** companions so `winner_count` matches the count they assert.
- **Every original assertion is unchanged** — the bet's own leg stays a LOSER/REMOVED, and the
  tests still assert SETTLED_LOST (back) / SETTLED_WON (lay) / VOIDED. The edits make the
  fixtures *more* realistic, not weaker. The adversarial "test-integrity" lens confirmed no
  assertion was weakened or removed.

The S222 LAY inversion and S223 settled-signal / repro behaviors are all still proven — now
against realistic markets.

---

## 3. Tests added — Block 10 (`test_settlement.py`), 12 new tests

Winner-less / all-REMOVED / regression shapes are driven through the **real translation**
(`_translate_market_settlement` + `_parse_settlement` via `_settlement_from_raw`, Block-9
rigor) so the counts come from production translation, not a hand-built payload.

- **The tail — both resolvers, both directions:** `test_winnerless_market_holds_pending_back`,
  `..._pending_lay`, `..._provisional_back`, `..._provisional_lay` — a 0-winner/≥1-loser CLOSED
  market **holds** (`market_winnerless_hold`, `new_state=None`); a BACK loser never becomes
  SETTLED_LOST, a LAY loser never becomes SETTLED_WON. The pending-back test also locks the
  fixture shape (0 winner, 3 losers, `unexpected_state_count is None`) so the readiness gate
  provably does **not** pre-empt — the hold is what fires.
- **Exclusion regression — both resolvers:** `test_all_removed_market_still_voids_pending`,
  `..._provisional` — an all-REMOVED market (0/0) is **not** held (`market_voided is False`
  on the read path) and self-heals to **VOIDED** via `voided_runner_removed`.
- **No pre-emption:** `test_winner_present_loser_leg_still_settles_lost` (winner present → a
  loser leg still SETTLED_LOST), `test_single_winner_leg_still_settles_won_not_held`,
  `test_dead_heat_not_pre_empted_by_winnerless_hold` (dead heat still parks via the F1 guard,
  not the hold).
- **Transient self-heal (bonus):** `test_winnerless_hold_self_heals_when_winner_lands` — a
  read with losers but no winner holds; a follow-up read once the winner lands settles the
  loser leg SETTLED_LOST.
- **Pass-loop counters:** `test_pass_counts_winnerless_hold_as_left_pending_not_settled` and
  `test_provisional_pass_counts_winnerless_hold_as_stayed_not_settled` — the hold rolls into
  the not-settled carry, `settled_won/lost/voided` stay 0, and the bet stays PENDING /
  PROVISIONAL at the storage level.

---

## 4. Re-prove

- **Bench:** the new hold tests + the all-REMOVED exclusion regression are the proof (all green).
- **Real anchor:** `test_real_gossamer_glow_shape_via_translation_lay_settles_won` — the
  captured market 1.259636589 (1 WINNER 100232243, laid selection 100232235 = LOSER, 10 LOSER,
  8 REMOVED with real reduction factors, no settledTime) **still settles SETTLED_WON**. It has
  a winner, so the hold branch does not touch it.

---

## 5. Money-path safety (the invariant)

The failure direction of this change is a **hold**, never a settlement — confirmed for every
path:

- Both hold branches return `new_state=None`, so the pass loops' `if decision.new_state is not
  None` write arm is skipped — **no `update_settlement_state` call**, no state transition.
- The read side effect is preserved (`source_market_settlement=settlement`), so
  `last_read_market_state` persistence still fires on a hold.
- The hold is only reachable when `market_voided` is False (checked first) and
  `unexpected_state_count` is falsy (readiness gate, checked first) — both take precedence.
- A LAY loser is held **before** the LOSER branch that would map it to SETTLED_WON, so a lay
  cannot be wrongly settled by this path.
- The winner-guard sits after the hold but is only reachable via the WINNER branch, which is
  impossible when `winner_count == 0` — no interaction flips a hold into a terminal.

---

## 6. Gates

| Gate | Result |
|---|---|
| `uv run pytest` (full) | **1289 passed, 1 xfailed** |
| settlement suite | **115 passed** |
| `paid_full` guard + post-settlement-void + settlement-worker | **34 passed** |
| Gossamer Glow re-prove | **SETTLED_WON** ✓ |
| `mypy workflows/bet_entry/v1/settlement.py` (strict) | **Success: no issues** |
| ruff — new violations | **0** (see below) |
| HEAD | **`e2638fa`** (unchanged) |

**No-new-ruff proof (against committed HEAD blobs):**

- `test_settlement.py`: **3 errors at HEAD → 3 now** — identical set (import-sort I001, an
  unused `settlement_module` import, one long line at an existing test). **Zero new.**
- `settlement.py`: **1 error at HEAD (I001) → 2 now.** The +1 is F401 (`RunnerSettlement`
  imported but unused). That import was added to the block by the **earlier dirty S222/S223
  work**, not this task — this task's edits are purely additive within function bodies, the
  Literal, and two counter tuples, and an additive edit cannot turn a used import into an
  unused one. This task introduced **zero** ruff violations.

Both remaining findings are pre-existing import-block/long-line issues outside this task's
surgical change set; fixing them would touch the import block (scope creep on a money-path
change), so they are left as-is and flagged here.

---

## 7. Adversarial verification (independent)

Three independent skeptics each read the code + brief directly and tried to **refute** a core
safety claim. Results:

| Lens | Verdict | Confidence | Defects |
|---|---|---|---|
| Predicate exactness / no-suppression / precedence | **UPHELD** | high | 0 |
| Counters + test integrity (no weakened assertions) | **UPHELD** | high | 0 |
| Money-path safety (no wrong settle, both resolvers, both sides) | **UPHELD** | high | 0 |

**Zero blockers/majors.** One minor nit (two tautological `assert new_state is not
SETTLED_LOST/WON` lines, vacuous when `new_state is None`) was **fixed** — folded into a
money-path comment on the meaningful `is None` assertion.

**One noted behavior nuance (not a defect — the safe direction).** A *mixed* anomalous shape —
the bet's **own** runner `REMOVED` while other runners are `LOSER` and there is no `WINNER`
(e.g. runners `[LOSER, LOSER, REMOVED(leg)]`; `winner_count=0`, `loser_count≥1`) — now **holds**
instead of the pre-hold VOID via the runner-REMOVED branch. This is the exact predicate applied
faithfully (it is winner-less **with losers**, distinct from the all-REMOVED 0-loser carve-out),
and it is strictly the conservative direction: a park-for-manual on a genuinely winner-less
(therefore not-legitimately-settled) market, never a wrong terminal — consistent with the
brief's stated failure direction ("hold, not pay wrong"). Surfaced here for operator awareness;
holding it is correct per §1's exact predicate.

---

## 8. Disciplines honored

- **Read-and-confirm gate:** brief + both resolvers read end-to-end before editing.
- **Scope:** predicate is exactly §1; only the two resolvers changed logic; no broadening
  (`loser_count == 0` all-REMOVED still self-voids). No translation edit, no enum edit.
- **Dirty-tree rules:** `git status` / `git diff` reviewed; edited **only** `settlement.py` +
  `test_settlement.py`; **no git write ops**; HEAD stays `e2638fa`.
- **Bet-safety:** `BETHUB_SETTLEMENT_WORKER` stays **OFF** (operator flips it); no placement,
  no DB writes, no live Betfair calls. The change's failure direction is a hold, never a settle.

---

## 9. What is left

The only remaining B2 step is the operator's **supervised live-worker run** with the flag
flipped ON. This change closes the last documented money-path tail; the "no silent
wrong-settle" invariant is now complete (the failure direction across every settlement branch
is either a correct terminal or a hold-for-manual).

---

## 10. Governing DRs

DR-032/033 (Betfair settlement source of truth) · DR-030 (module boundaries) ·
DR-027/028 (two-DB boundary) · DR-021 (Adelaide anchors).
