# Brief — settlement read-path batched fix (F1–F4 + C-5/C-6, one function)

**Drafted:** Session 223, 2026-07-03 ACST (DR-021 Adelaide anchor).
**Author:** Chat (governance / operator-facing).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (dirty tree — worker build + S222 LAY fix + S223 settled-signal fix).
**Routing:** Claude Code, read-write (dirty-tree rules).
**Grounding:** `settlement_readpath_reconciliation_report.md` (the read-only review that found these — read it first).
**Worker flag:** `BETHUB_SETTLEMENT_WORKER` stays **OFF**; Code does not flip it.

---

## 0. Why this exists (plain English)

The read-only reconciliation review found **four gaps** in how the auto-settlement worker reads a settled Betfair market — and, cleanly, **all four are in one function**: `clients/betfair_client/v1/_translation.py::_translate_market_settlement` (the thin layer that turns Betfair's raw data into the shape the settlement logic reads). The decision logic itself is sound; only this translation had gaps. So this is **one bounded fix in one place**, then re-prove.

The load-bearing one is a **silent money defect**: a dead-heat winner would settle at full instead of the split amount. The others are a wrong-way default, a never-auto-settle for voids (which the operator has chosen to keep **manual**), and a market-freeze on certain runner types. Two cosmetic tidy-ups ride along.

**Operator decision carried in (S223):** voided / abandoned races stay **manual** — do **not** build auto-void derivation. Those bets hold for the operator to settle by hand (they barely happen).

---

## 1. The single fix site

`clients/betfair_client/v1/_translation.py::_translate_market_settlement` (the per-runner status/count loop, ~`:559-591`) and its unit test `tests/clients/betfair_client/v1/test_settlement.py`. The end-to-end dead-heat-through-translation test lands in `tests/workflows/bet_entry/v1/test_settlement.py`.

**The resolver `workflows/bet_entry/v1/settlement.py` needs NO change** — F1 simply makes its existing dead-heat guard reachable; F4 restores a correct input to a gate that's already right. **No `RunnerSettlementStatus` enum change** (the conservative defaults route through the existing `unexpected_state_count` gate).

---

## 2. The fixes (build exactly these)

### F1 — dead-heat winner (MONEY-PATH, the load-bearing fix)
- **Now:** `dead_heat_count` is hardcoded `None` (`:588`); a real dead heat = **≥2 runners with `status == "WINNER"`**, which the loop keeps as WINNER but never tallies → the winner-guard dead-heat park (`settlement.py:480-483`) can never fire on a real read → a dead-heating selection settles at **full** winnings/liability.
- **Fix:** in the loop, count runners whose **resolved** status is WINNER; set `dead_heat_count = winner_count if winner_count >= 2 else None`. (A WIN market pays one winner; ≥2 WINNER ⇒ dead heat.) This makes the existing guard park a dead-heating **winner** to PROVISIONAL (manual). A dead-heat **loser** still routes through the LOSER branch and settles normally — correct.

### F2 — missing runner status defaults to WINNER (MONEY-PATH, latent)
- **Now:** `status = r.get("status", "WINNER")` (`:560`) — a runner dict lacking `status` becomes a clean WINNER, increments no counter, passes the readiness gate, and could auto-settle a BACK bet `SETTLED_WON` at full.
- **Fix:** default an absent/unknown status to the **conservative** side — a sentinel **not** in {WINNER,LOSER,REMOVED} so it hits the existing `else`-collapse and increments `unexpected_state_count` (the bet-safe park/hold direction). Never default to WINNER.

### F3 — market-level void: keep MANUAL (operator decision), retire the dead field
- **Now:** `market_voided = bool(md.get("marketVoided", False))` reads `marketDefinition.marketVoided` — a field REST `listMarketBook` never returns (no `marketDefinition` block at all), so it's **always False** and the Step-5 void→VOIDED branch is dead code on the real read path.
- **Fix (manual, per operator):** do **NOT** build runner-signal-derived auto-void. Stop reading the phantom `marketDefinition.marketVoided`; set `market_voided = False` explicitly **with a comment** stating REST cannot signal a market void and abandonments are handled manually by the operator (holds in PENDING via the readiness gate for manual resolution). **Requirement to preserve:** a real void must **never auto-settle to a wrong state** — it must hold PENDING (or void via the runner-REMOVED branch), never settle a bet WON/LOST. The review verified the expected void representations are money-safe; this fix keeps them so.

### F4 — `REMOVED_VACANT` / `HIDDEN` freezes the market (LIVENESS)
- **Now:** only exact `"REMOVED"` is recognised (`:565`); Betfair's `REMOVED_VACANT` (greyhound vacant trap) and `HIDDEN` collapse to LOSER + set `unexpected_state_count ≥ 1` permanently, and the market-wide readiness gate then holds **every** bet in that market PENDING/PROVISIONAL forever.
- **Fix:** map `REMOVED_VACANT` and `HIDDEN` to **terminal-non-participating** — treat like `REMOVED` (so a bet **on** that selection voids, and they add to `removed_count`, **not** `unexpected_state_count`). The readiness gate then counts only genuinely-pending ACTIVE runners.

### C-5 (ride-along, optional) — `bsp` audit field
- `r.get("bsp")` reads a non-existent top-level field (always None). No settle decision uses it; audit-only. **Fix:** read `r.get("sp", {}).get("actualSP")`, falling back to `r.get("bsp")` for streaming payloads.

### C-6 (ride-along, optional) — fixtures fabricate `settledTime`
- Test hygiene only (the resolver no longer gates on `settled_time` post-S223). **Fix:** default the translation test helper to `settled_time=None`; relabel the one `marketDefinition.settledTime` case as a streaming-shape parse test; keep one populated fixture to exercise the `_settled_time_iso` branch.

---

## 3. Tests — the non-negotiable (this is what let F1 hide)

**New tests must drive `_translate_market_settlement` from RAW `listMarketBook` JSON**, not from a hand-built `MarketSettlement` — the previous fixtures injected `dead_heat_count`/`market_voided` directly and bypassed the very code that was broken. Add, driven through the translation end-to-end:
- **Dead-heat:** raw market with **≥2 WINNER** runners → translation emits `dead_heat_count ≥ 2` → resolver **parks** a bet on a winning selection to PROVISIONAL (both a BACK and a LAY on a dead-heater).
- **Status-less runner:** raw runner dict with **no `status`** → routes to `unexpected_state_count > 0` (holds/park), **never** SETTLED_WON.
- **`REMOVED_VACANT`:** raw market with a vacant runner → does **not** inflate `unexpected_state_count`; a bet on it → VOIDED; a clean winner elsewhere in the market **still settles**.
- **Void shape:** the plausible real void representation → bet **holds PENDING** for manual (does not auto-settle to a wrong state).
- **Single winner (regression):** exactly 1 WINNER → `dead_heat_count = None` → normal settle, no park.

**Keep green:** the S222 LAY inversion (both resolvers), the S223 settled-signal readiness tests, the F2 pending-sweep test, BACK mapping, and the `paid_full` / Rule-4 materiality tests (verified sound — do not disturb). `uv run pytest` green; `mypy` clean on the changed module; no new `ruff`.

---

## 4. Re-prove

- **Bench:** the new raw-JSON translation tests above are the primary proof (they exercise the exact code that was broken).
- **Real anchor:** re-run the existing real-capture re-prove (the Gossamer Glow read, `market 1.259636589`) and confirm it **still** settles to SETTLED_WON (+$4.84) — the fix must not regress the one shape confirmed against real data.
- **Live (operator-supervised, later):** the real dead-heat / void / greyhound-vacant / lay-wins shapes remain the live-window watch-list — correct-by-construction after this fix, to be confirmed the first time each occurs. Not part of this build.

---

## 5. Disciplines (load-bearing)

- **Read-and-confirm gate:** read this brief + the review report + `_translation.py` and both test files end-to-end; confirm understanding before editing.
- **Dirty-tree rules:** `git status` at start; edit **only** the named anchors (`clients/betfair_client/v1/_translation.py`, `tests/clients/betfair_client/v1/test_settlement.py`, `tests/workflows/bet_entry/v1/test_settlement.py`); `git diff` after each; **no git write ops**; HEAD stays `e2638fa`. **No resolver edit, no enum edit** — if the fix seems to need one, STOP and surface (it shouldn't).
- **Bet-safety:** `BETHUB_SETTLEMENT_WORKER` stays **OFF** (operator flips it, at the machine); no bet placement; no DB writes; no live Betfair calls needed for this build (bench + existing real capture). The S222 backup `data/bethub.db.bak-S222-20260703T194225` stands.
- **Scope discipline:** all four fixes are in `_translate_market_settlement`. If a fix pulls in surface beyond the named anchors, STOP and surface rather than widen.
- **Stop conditions:** any test that must go green won't without disturbing a verified-sound path (LAY inversion, paid_full); the void fix would auto-settle a void to a terminal state (must hold manual); scope escapes the one function.
- **Report:** produce `settlement_readpath_batched_fix_report.md` in the rebuild folder — each fix as built, the raw-JSON tests, full-suite result, and the real-capture re-prove.

---

## 6. Governing DRs

DR-032/033 (Betfair settlement source of truth; settlement Betfair-only) · DR-030 (module boundaries) · DR-027/028 (two-DB boundary) · DR-021 (Adelaide anchors). S189 (fixtures ≠ live-proven) is the direct reason F1/F3 hid — the fix's worth is the **raw-`listMarketBook` translation-layer tests**, not more resolver fixtures.
