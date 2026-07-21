# Report — settlement read-path batched fix (F1–F4 + C-5/C-6, one function)

**Built:** Session 223, 2026-07-03 ACST (DR-021 Adelaide anchor).
**Author:** Claude Code (read-write; dirty-tree rules).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (unchanged — no git write ops; the working tree stays dirty as it was).
**Brief:** `settlement_readpath_batched_fix_brief.md`. **Grounding:** `settlement_readpath_reconciliation_report.md`.
**Worker flag:** `BETHUB_SETTLEMENT_WORKER` stayed **OFF** (not flipped). No bet placement, no DB writes, no live Betfair calls.

---

## 0. Result

**All four fixes (F1–F4) + both ride-alongs (C-5, C-6) built, entirely inside `clients/betfair_client/v1/_translate_market_settlement`.** No resolver edit, no enum edit. Full suite **1277 passed, 1 xfailed** (`uv run pytest`); `mypy` clean on the changed module; `ruff` clean on the changed code. The real Gossamer Glow shape (market `1.259636589`) still settles **SETTLED_WON (+$4.84)**, now proven through the *changed* translation from raw `listMarketBook` JSON.

**Two refinements beyond the literal brief — both flagged here for review, both surfaced by adversarial review, both still translation-only (no resolver/enum edit):**

1. **F1 uses `numberOfWinners`, not a bare `winner_count >= 2`.** The literal brief formula (`dead_heat_count = winner_count if winner_count >= 2 else None`) would have introduced a **liveness regression**: a Betfair "To Be Placed" market legitimately stamps `status = WINNER` on *every* placed runner (2/3/4 of them), which a market-type-blind count mis-reads as a dead heat → the winner-guard would park *every* place-market winner to PROVISIONAL forever. Fix: a dead heat is `winner_count > numberOfWinners` — `numberOfWinners` is a **real** REST `MarketBook` field (1 for a WIN market, N for an N-place market), so a normal N-place result (exactly N winners) settles while >N winners (a WIN dead heat, or a genuine tie for the last place) parks. Market-type-aware without a `marketType` field or a resolver edit.

2. **F4 gives a vacant/hidden non-runner a `0.0` reduction factor, not `None`.** The naive "map `REMOVED_VACANT`/`HIDDEN` to `REMOVED`" (the brief's literal F4) would make the winner-guard's Option-B "unreadable factor → park" fallback fire on the factor-less vacant box → park *every* winner in a race with a vacant box (contradicting the brief's own "a clean winner elsewhere still settles" requirement, and just relocating the freeze from PENDING to PROVISIONAL). Fix: a vacant box / hidden non-runner carrying no `adjustmentFactor` reads as `0.0` — honest, since it imposes **no** Rule-4 deduction — so a bet on it still VOIDs but winners elsewhere settle via the verified-sound `paid_full` path. A genuinely scratched `REMOVED` with a missing factor keeps `None` (→ park), so a real unreadable removal is never silently paid full.

Both refinements were adversarially verified as money-safe (see §3). Neither needed a resolver or enum edit; if the operator prefers the literal brief text over either refinement, that is a governance call — but the literal F1 regresses place markets and the literal F4 over-parks winners, so the refinements are recommended.

---

## 1. The fixes as built

All in `clients/betfair_client/v1/_translation.py::_translate_market_settlement` (the per-runner loop + return dict, now `~:569–678`).

### F1 — dead-heat winner (money-path) — `_translation.py:605–608, 644–676`
- **Built:** the loop tallies `winner_count` (runners whose resolved status is `WINNER`); the return dict sets `dead_heat_count = winner_count if winner_count > _expected_winners else None`, where `_expected_winners = market_book.get("numberOfWinners") or md.get("numberOfWinners") or 1` (`:644`). This makes the existing winner-guard dead-heat park (`workflows/bet_entry/v1/settlement.py:480–493`) reachable from a real read — a WIN dead heat (2 > 1) parks; a single winner (1 > 1 is false) settles; a normal N-place result (N > N is false) settles; a place dead heat (>N winners) parks.
- **Refinement vs brief:** see §0 item 1 (uses `numberOfWinners` instead of a bare `>= 2` to be place-safe).

### F2 — absent runner status defaults to a conservative sentinel (money-path, latent) — `_translation.py:605`
- **Built:** `status = r.get("status") or "ACTIVE"`. `"ACTIVE"` is outside `{WINNER, LOSER, REMOVED-like}`, so an absent/empty status collapses the runner to `LOSER` settlement_status **and** increments `unexpected_state_count` (`:614–617`) → the readiness gate (`settlement.py:737`/`:973`) holds the bet PENDING rather than auto-settling. Never defaults to WINNER.

### F3 — market-level void stays MANUAL; the dead field is retired — `_translation.py:664`
- **Built:** `"market_voided": False` (hardcoded, with a comment). The phantom `md.get("marketVoided")` read is gone (REST `listMarketBook` carries no `marketDefinition`/`marketVoided`, so it was always False anyway). No runner-signal auto-void derivation was built (operator decision: abandonments are settled manually). A real void therefore **holds** the bet in PENDING via the readiness gate (an ACTIVE-runner void) or VOIDs it via the runner-REMOVED branch — **never** auto-settles to a wrong WON/LOST state. The resolver's Step-5 `market_voided → VOIDED` branch is left intact (unreachable on the REST path, retained for a possible future streaming source).

### F4 — `REMOVED_VACANT` / `HIDDEN` no longer freeze the market (liveness) — `_translation.py:569–575, 611–613, 624–629`
- **Built:** `_REMOVED_LIKE_STATUSES = {"REMOVED", "REMOVED_VACANT", "HIDDEN"}` all map to settlement_status `REMOVED` and increment `removed_count`, **not** `unexpected_state_count` (`:611–613`) — so a stable non-participating status no longer sits in `unexpected_state_count` forever and freezes the readiness gate for every bet in the market. A bet on such a selection VOIDs via the runner-REMOVED branch.
- **Refinement vs brief:** see §0 item 2 (`_NON_DEDUCTING_REMOVED_STATUSES = {"REMOVED_VACANT", "HIDDEN"}` carrying no factor → `adjustment_factor = 0.0` at `:624–629`, so winners elsewhere settle instead of the guard over-parking them).

### C-5 (ride-along) — `bsp` audit field — `_translation.py:577–588, 632`
- **Built:** new `_settled_sp(runner)` helper reads the settled SP from `sp.actualSP` (real REST), falling back to a top-level `bsp` (streaming). The runner dict now uses `"bsp": _settled_sp(r)`. Audit-only; no decision consumes `bsp`.

### C-6 (ride-along) — fixtures fabricating `settledTime` — `tests/clients/betfair_client/v1/test_settlement.py`
- **Built (in-scope portion):** relabelled `test_translate_market_settlement_lifts_adjustment_factor`'s docstring to mark its `marketDefinition.settledTime` + top-level `bsp` as a **streaming-shape** payload (real REST carries neither), exercising the fallback branches rather than asserting the REST shape. The new raw-JSON translation tests (§2) all omit `settledTime` to reflect the real REST shape. (The shared `SETTLEMENT_FRESH_SETTLED` fixture lives in `tests/fixtures/betfair/rest_responses.py`, which is **not** a named anchor and was left untouched.)

---

## 2. Tests — driven from RAW `listMarketBook` JSON

The non-negotiable: the new tests drive `_translate_market_settlement` from raw Betfair JSON (the layer the prior resolver-only fixtures bypassed — the reason F1 hid). Added:

**Translation unit tests** (`tests/clients/betfair_client/v1/test_settlement.py`):
- `test_translate_dead_heat_two_winners_sets_dead_heat_count` — 2 WINNER (nOW defaulted 1) → `dead_heat_count == 2`.
- `test_translate_single_winner_no_dead_heat` — 1 WINNER → `None`.
- `test_translate_place_market_multiple_winners_not_dead_heat` — 3 WINNER on `numberOfWinners=3` → `None` (settles); 4 WINNER on a 3-place market → `4` (genuine place dead heat).
- `test_translate_win_dead_heat_with_number_of_winners_one` — explicit WIN `numberOfWinners=1`, 2 WINNER → `2`.
- `test_translate_absent_status_routes_to_unexpected_not_winner` — a status-less runner → `settlement_status != WINNER`, `unexpected_state_count == 1`.
- `test_translate_removed_vacant_and_hidden_treated_as_removed` — both map to `REMOVED`, `removed_runner_count == 2`, `unexpected_state_count is None` (not frozen), and their `adjustment_factor == 0.0`.
- `test_translate_market_void_never_signalled_on_rest` — `market_voided is False` even when a raw `marketDefinition.marketVoided=True` is present.
- `test_translate_bsp_prefers_sp_actual_sp_with_streaming_fallback` — `sp.actualSP` preferred, top-level `bsp` fallback, else `None`.

**End-to-end resolver tests, through translation + parse + resolver** (`tests/workflows/bet_entry/v1/test_settlement.py`, Block 9):
- `test_deadheat_winner_parks_via_translation_back` / `_lay` — a 2-WINNER raw market parks a BACK and a LAY on a dead-heater to PROVISIONAL (`provisional_dead_heat_or_reduction`), `dead_heat_count == 2`.
- `test_single_winner_via_translation_settles_won` — 1 WINNER → SETTLED_WON, no park.
- `test_place_market_winner_settles_not_parked_via_translation` — a 3-place market (`numberOfWinners=3`, 3 placed WINNERs) settles a placed-runner bet to SETTLED_WON, **not** parked (the regression guard).
- `test_status_less_runner_via_translation_holds_pending` — the bet's status-less runner → holds (`runner_not_yet_resolved`), never WON.
- `test_removed_vacant_bet_voids_and_market_not_frozen` — a bet on a `REMOVED_VACANT` selection VOIDs; a clean winner in the same market still settles WON.
- `test_market_void_shape_via_translation_holds_pending` — a CLOSED all-ACTIVE (void) shape holds PENDING, `market_voided is False`.
- `test_real_gossamer_glow_shape_via_translation_lay_settles_won` — the reconstructed real capture (1 WINNER `100232243`, laid `100232235`=LOSER, 8 REMOVED with the real factors `0.099…11.251`, `numberOfWinners=1`, no `marketDefinition`) → `dead_heat_count None`, `removed_runner_count 8`, `unexpected_state_count None`, `market_voided False`, and a LAY on the laid selection settles **SETTLED_WON**.

**Kept green (unchanged behaviour):** S222 LAY inversion (both resolvers), S223 settled-signal readiness, the pending-sweep tests, BACK mapping, and the full `paid_full` / Rule-4 materiality guard suite (`test_settlement_guard.py`, 15 tests). The winner-guard's removed-runner arm was verified undisturbed — a real material scratch still parks (see §3).

---

## 3. Adversarial review (pre-commit hardening)

Three independent skeptics probed the just-applied fix for money-path holes:

- **F4 `0.0` refinement — CLEAN (money-safe).** The `0.0` is doubly gated (`adjustment_factor is None` AND `status in {REMOVED_VACANT, HIDDEN}`), so it only stands in where no deduction exists. A present real factor is always honoured (→ park); a factor-less genuine `REMOVED` keeps `None` (→ park); the guard's `any_material`/`any_unreadable` are OR-folds, so a `0.0` sibling can never mask a coexisting material scratch; and the LOSER/lay-collect path never invokes the guard, so `0.0` cannot leak into a winning-lay collect. No silent-overpay path exists.
- **F1 winner-count — HOLE FOUND → FIXED.** The place-market multi-winner regression (§0 item 1). Resolved with `numberOfWinners`; sub-cases (dead-heat + material scratch still parks; a LOSER bet in a dead-heat market settles; a LAY on a dead-heater parks) all verified correct.
- **F2 / F3 / shape completeness — CLEAN (bet-safe).** No naturally-occurring raw shape mis-settles to a wrong terminal state. Every non-terminal/ambiguous status routes to the readiness-gate hold; a missing/type-mismatched `selection_id` yields runner `None` → PROVISIONAL (a hold, never a false match — translation coerces `str(selectionId)` and the resolver uses `==`); empty runners → hold.

**One residual the review surfaced but I did NOT build (operator's call — beyond the four fixes):** a *theoretical* void presented as a CLOSED market with ≥1 LOSER and **zero** WINNER runners would slip every gate and settle the LOSER bet (BACK→LOST / LAY→WON) instead of holding. The review notes Betfair does **not** emit a zero-WINNER settled market in practice, and this is the same low-confidence money-path tail the reconciliation already documented under F3. A cheap defensive hardening — *"CLOSED + runners present + `winner_count == 0` + `unexpected == 0` and ≥1 LOSER → force a hold"* — would close it at no money-path cost and would strengthen F3's "never auto-settle a void wrong" invariant to cover **all** winner-less shapes (not just the all-ACTIVE one). It must be scoped to exclude the all-`REMOVED` case (which should self-heal to VOIDED, not hold). **Recommendation:** authorise this as a small F3 follow-on if the operator wants the invariant airtight; otherwise it remains an accepted, documented, non-occurring residual. Not built here to honour "build exactly the four fixes."

---

## 4. Re-prove

- **Bench (primary):** the raw-JSON translation + end-to-end tests in §2 exercise the exact code that was broken (dead-heat, status-less, vacant, void, place-market, single-winner). Green.
- **Real anchor:** `test_real_gossamer_glow_shape_via_translation_lay_settles_won` reconstructs the captured market `1.259636589` shape and drives it through the **changed** translation → the laid selection still settles **SETTLED_WON** (the +$4.84 collect), field inventory intact. The pre-existing repro-style SQLite pass (`test_sqlite_pass_settles_repro_style_lay_without_settled_time`) also stays green.
- **Full suite:** `uv run pytest` → **1277 passed, 1 xfailed** (the xfail and 4 deprecation warnings are pre-existing, unrelated to this change).
- **Live (later, operator-supervised):** the real dead-heat / void / greyhound-vacant / place-market / lay-wins shapes are correct-by-construction after this fix; each to be confirmed the first time it occurs during the supervised window. Not part of this build.

---

## 5. Disciplines & scope

- **One function:** every fix is inside `_translate_market_settlement` (plus its module-local `_settled_sp` helper and two status-set constants). **No resolver edit, no enum edit.** The two refinements (F1 `numberOfWinners`, F4 `0.0`) stay translation-only precisely so no resolver/enum change was needed.
- **Named anchors only:** modified `clients/betfair_client/v1/_translation.py`, `tests/clients/betfair_client/v1/test_settlement.py`, `tests/workflows/bet_entry/v1/test_settlement.py`. Nothing else touched.
- **Dirty tree / git:** HEAD stays `e2638fa`; no git write ops. `git status`/`git diff` used read-only. (The diffstat vs HEAD is cumulative — it includes the pre-existing S222/S223 uncommitted work; this session's edits are the three anchors above.)
- **Bet-safety:** `BETHUB_SETTLEMENT_WORKER` OFF (operator flips it); no placement, no DB writes, no live Betfair calls (bench + reconstructed real capture only). The S222 backup `data/bethub.db.bak-S222-20260703T194225` is untouched.
- **Pre-existing lint (not introduced here):** `ruff` reports 4 findings in the two test files at lines outside this session's edits — an unsorted import block (I001) and an unused `settlement_module` import (F401) in the resolver test, an unsorted import block in the client test, and one E501 at `test_settlement.py:2714`. All are from prior-session dirty-tree work (confirmed: none appear as `+` lines in this session's diff). My added code is `ruff`-clean; left the pre-existing findings alone to avoid widening scope. Flagging them so they can be swept when that dirty-tree work is committed.
- **New consumed field:** `numberOfWinners` is now read from `listMarketBook` (a real REST `MarketBook` field, unlike the retired phantom `marketVoided`). Worth noting for the live window: confirm `numberOfWinners` is present on the first real settled read (it is a standard field; the code floors to 1 if ever absent).

---

## 6. Governing DRs

DR-032/033 (Betfair settlement source of truth; settlement Betfair-only) · DR-030 (module boundaries) · DR-027/028 (two-DB boundary) · DR-021 (Adelaide anchors). S189 (fixtures ≠ live-proven) is honoured: the fix's worth is the **raw-`listMarketBook` translation-layer tests**, and the adversarial pass that caught the place-market regression before it shipped — not more resolver fixtures.
