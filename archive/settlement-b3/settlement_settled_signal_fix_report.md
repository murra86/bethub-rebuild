# Report — settlement worker "settled-signal" read gap (diagnosis → fix → re-prove)

**Session type:** Execution of `settlement_settled_signal_fix_brief.md` (S223). Phase 1 read-only; Phase 2 read-write (dirty-tree); Phase 3 supervised live re-prove.
**Codebase:** bethub-v3 @ HEAD `e2638fa` (dirty tree — in-progress worker build + the S223 LAY-correctness change — plus this change; **HEAD unmoved, no git write op**).
**Date:** 2026-07-03 ACST (DR-021).
**Worker flag:** `BETHUB_SETTLEMENT_WORKER` **OFF** (Code does not flip it; operator-only, at the machine).

---

## Phase 1 — DIAGNOSIS (read-only)

**Evidence source.** The S223 supervised live run wrote the worker's real Betfair read onto the repro bet as
`last_read_market_state` (JSON of the translated `MarketSettlement`). That stored blob — a genuine live read,
re-read **10 times** over ~3 hours with no settlement — is the primary evidence. A fresh raw JSON-RPC capture
requires an operator-supervised live call (username/password creds, no cached session token; this execution
shell has no network), so it was not re-fetched; the stored real read plus the translation code prove the
diagnosis empirically. Repro market `1.259636589`, laid selection `100232235` (Gossamer Glow).

**(a) The settled signal — CONFIRMED blocker.** The real read is `market_status = "CLOSED"`,
**`settled_time = null`**, `market_voided = false`. Code trace: `_translation._translate_market_settlement`
(`clients/betfair_client/v1/_translation.py:583`) sets `settled_time` from
`md.get("settledTime") or market_book.get("settledTime")`. The REST `listMarketBook` response
(`_translate_request` maps `/v1/market/{id}/settlement` → `listMarketBook`) carries **no `marketDefinition`
block and no `settledTime`** — so `settled_time` is **always None**, and the resolver's `settled_time is None`
gate (`workflows/bet_entry/v1/settlement.py:672` PENDING, `:895` PROVISIONAL, sitting *before* the void and
runner branches) never passes. Every bet is held pending forever. **The real "settled" signal that IS present:
`status == CLOSED` + each runner carrying a terminal `status` (WINNER/LOSER/REMOVED).**

**(b) Runner-status mapping — clean; laid selection reads LOSER. No STOP.** The 19 runners map to exactly
**1 WINNER** (sel `100232243`), **10 LOSER**, **8 REMOVED**; laid selection `100232235` = **LOSER**
(so the lay **won**). `adjustment_applied` is `True` on exactly the 8 REMOVED runners and `False` on all
non-removed — the S223 `_parse_runner` disambiguation is correct on real data.
*Latent quirk (documented, not a blocker):* `_translation.py:565` maps any runner `status` **not** in
{WINNER,LOSER,REMOVED} to `"LOSER"` and simultaneously increments `unexpected_state_count` (`:578`). On this
settled market no runner is ACTIVE, so it never fires. It matters only for a CLOSED-but-unresolved market — and
the Phase-2 readiness guard (below) keys off exactly that `unexpected_state_count`, so the collapse can never
produce a settlement. A fully-clean fix (preserve ACTIVE through translation) would need a new
`RunnerSettlementStatus` enum member in `clients/betfair_client/v1/settlement.py` — **outside the named
anchors**, and unnecessary given the guard — so it is left as-is and mitigated, not widened into scope.

**(c) Reduction-factor units — PERCENT; guard threshold correct. No defect.** Real per-runner
`adjustment_factor` values: REMOVED runners 0.099 / 0.115 / 0.138 / 1.139 / 1.539 / 2.924 / 7.588 / 11.251;
non-removed up to 27.822. Values **> 1** rule out a 0–1 fraction basis — Betfair sends a **percentage** (0–100).
So the guard's `REDUCTION_MATERIALITY_THRESHOLD_PCT = 2.5` (compared `>= 2.5`) is the **correct basis**; the
materiality gate is **not** off by ~100×. The non-removed runners' `adjustmentFactor` (e.g. Gossamer Glow's
27.822) is the runner's implied-probability rating, **not** a deduction; the guard reads **only** REMOVED
runners' factors (`adjustment_applied`), so those ratings are correctly ignored. **No units defect → no fix to
units/threshold.**

**(d) A settled-time-bearing call?** `listClearedOrders` exposes `settledDate` per cleared order; the streaming
`marketDefinition` carries `settledTime`. Both are heavier (a new endpoint + translation + cleared-orders
paging, or the streaming path). Option A keys off `CLOSED` + resolved-runner + `unexpected_state_count == 0` —
signals **already in the REST response** — so it is lighter and faithful. **Default to A.**

**Decision.** The blocker is exactly the `settledTime` gap (confirmed empirically). (b)/(c) reveal **no
STOP-worthy second defect** — the `else "LOSER"` collapse is latent and fully mitigated by the readiness guard;
the factor units are correct. **Proceed to Phase 2, Option A.**

---

## Phase 2 — the bounded FIX (as built)

**Anchors touched:** `workflows/bet_entry/v1/settlement.py` + its test
`tests/workflows/bet_entry/v1/test_settlement.py`. **`_translation.py` was NOT changed** — the fix needs
no translation edit (see the readiness-guard note). The `RunnerSettlementStatus` enum
(`clients/betfair_client/v1/settlement.py`) was **not** touched (outside the named anchors).

**Option A — readiness off "CLOSED + runner resolved", not `settledTime`.**
- **Removed the `settled_time is None` gate** in **both** resolvers (`_resolve_settlement_for_bet`,
  `_resolve_provisional_for_bet`). Market readiness now rests on the existing Step-3 `market_status ==
  CLOSED` check.
- **Added a runner-level readiness guard**, placed **after** the runner-found lookup (so
  runner-not-in-market → PROVISIONAL still fires) and **before** the REMOVED/WINNER/LOSER resolution:
  if the market still carries an unresolved runner (`unexpected_state_count > 0`) → no decision, reason
  **`runner_not_yet_resolved`**, bet stays PENDING/PROVISIONAL. `unexpected_state_count` is the correct
  within-anchor signal: `_translation` increments it **at exactly the point it collapses a non-terminal
  runner status to LOSER** (`:578`/`:565`), so gating on it means the collapse (Phase 1 (b)) can never
  produce a settlement — the "don't guess" caution is preserved **without** `settledTime` and **without**
  needing a new enum member. (A leg-specific ACTIVE check would need the enum + a translation change,
  both outside the anchors and unnecessary.)
- **`market_voided` (Step 5) preserved and precedes readiness** — a voided market resolves to VOIDED even
  if a runner reads unresolved.
- **Preserved unchanged:** REMOVED → VOIDED, the winner-guard park (dead-heat / material reduction), the
  **S223 LAY inversion**, and the Option-A create-path PENDING stamp.
- **`settled_time = None` tolerated in details:** added a small `_settled_time_iso(settlement)` helper
  (ISO string or None); all 14 decision-`detail` sites use it, so no `detail` payload assumes a settled
  time is present.
- **New reason code `runner_not_yet_resolved`** added to the `SettlementReasonCode` Literal; both pass
  loops roll it into the existing `left_pending_market_not_settled` / `stayed_provisional_market_not_settled`
  counters.
- **No units/threshold change** — Phase 1 (c) confirmed `adjustmentFactor` is a percentage and the guard's
  `2.5` is the correct basis.

**Tests (landed together; fixtures fixed to the REAL shape — the S189 lesson):**
- The `_closed_settlement` fixture now leaves `settled_time` **absent** (None), so the S223 LAY suite and
  the new tests all run against the real closed-market shape.
- Both resolvers settle a CLOSED market with a terminal runner and **no** `settled_time` → SETTLED_WON
  (the two former `market_not_yet_settled` tests, repurposed).
- Both resolvers: CLOSED + unresolved runner (`unexpected_state_count > 0`) → **`runner_not_yet_resolved`**,
  stays pending/provisional.
- Market-void **without** `settled_time` → VOIDED (and void precedes readiness).
- **SQLite-path end-to-end:** a repro-style LAY (CLOSED, laid selection **LOSER**, no `settled_time`, 8
  removed runners) built via `build_hedge_bet_record`, swept from the real `SQLiteBetRecordStorage` →
  **SETTLED_WON**.
- The two left-pending counter tests updated to exercise `runner_not_yet_resolved`; the end-to-end
  lifecycle test still reaches PROVISIONAL via runner-not-in-market (guard placement preserves it).
- **Kept green:** S223 LAY (both resolvers), BACK mapping, and the **F2** pending-sweep test.
- **`uv run pytest`: 1261 passed, 1 xfailed.** `mypy` clean on the changed module. `ruff`: only the 5
  **pre-existing** findings (HEAD's import-sort + the in-progress build's `RunnerSettlement` F401 + the
  test file's pre-existing I001/F401/E501) — **zero new**.

## Phase 3 — RE-PROVE

The S223 live run stored the worker's **real** Betfair read on the bet (`last_read_market_state`, 2770
bytes). The re-prove reconstructs that exact `MarketSettlement` and drives the **fixed**
`run_settlement_pass` over the **real** backfilled pending LAY (on a scratchpad **copy** of the operational
DB — the closest bench-equivalent of a live worker cycle, using the identical data the live worker read):

| | value |
|---|---|
| real read | `market_status=CLOSED`, `settled_time=None`, `market_voided=False`, `unexpected_state_count=None`, `removed_runner_count=8` |
| laid selection `100232235` | **LOSER** |
| fixed pass | `swept=1`, `settled_won=1`, `left_pending_market_not_settled=0` |
| **final state** | **SETTLED_WON** |
| net P&L (real balance-derivation) | **+$4.8392** (laid selection lost → lay wins → +S(1−c)) |

The old code held this **exact** read pending indefinitely (the `settled_time` gate); the fix settles it
end-to-end to SETTLED_WON on the real production data. The **dangerous inversion branch** (laid selection
**wins** → SETTLED_LOST) is **not** live-exercisable on this bet (it lost) — it stays covered by the S223
bench re-prove and the new bench LAY tests, stated explicitly rather than implied.

**The actual live-worker run (worker ON in live mode) remains the operator's supervised step.** This
re-prove proves the resolver + full-pass behavior on the identical captured data; the operational DB is
**untouched** (the bet stays `pending`, ready for the supervised window), and the flag stays **OFF**.

## Disciplines & self-assessment

- **HEAD `e2638fa`; no git write op.** Only `settlement.py` + its test edited this session — both named
  anchors. `_translation.py` **not** edited by this change (its 5-line diff is the pre-existing in-progress
  build's `adjustmentFactor` lift). No surface beyond the anchors.
- **Bet-safety:** `BETHUB_SETTLEMENT_WORKER` **OFF** (Code did not flip it). No bet placement. The
  operational DB is **untouched** — the re-prove ran on a copy; the repro bet stays `pending`. The S222
  backup `data/bethub.db.bak-S222-20260703T194225` stands.
- **No STOP fired.** Phase 1 confirmed the blocker is the `settledTime` gap; (b)/(c) surfaced no
  second money-path defect (the `else "LOSER"` collapse is latent and fully mitigated by the readiness
  guard; factor units are correct).
- **Confidence:** the `settledTime`-gap fix + both-resolver readiness + fixture fix — **certain** (full
  suite + real-read re-prove). Concrete live-worker settlement — the operator's supervised step.

## Latent quirk carried forward (from Phase 1 (b))

`_translation.py:565` maps any runner status outside {WINNER,LOSER,REMOVED} to `"LOSER"` (and increments
`unexpected_state_count`). The readiness guard keys off `unexpected_state_count`, so this can never
produce a settlement — but a fully-clean fix (preserve ACTIVE/unresolved as a distinct status) would need
a new `RunnerSettlementStatus` enum member in `clients/betfair_client/v1/settlement.py`, **outside** the
named anchors and unnecessary given the guard. Flagged for a future authorised change if the exchange ever
returns CLOSED markets with genuinely unresolved runners.
