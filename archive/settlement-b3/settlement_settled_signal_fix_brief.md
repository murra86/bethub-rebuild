# Brief — settlement worker: the "settled-signal" read gap (diagnosis → bounded fix → re-prove)

**Drafted:** Session 223, 2026-07-03 ACST (DR-021 Adelaide anchor).
**Author:** Chat (governance / operator-facing).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (dirty tree — the in-progress settlement-worker build + the S223 LAY-correctness change already landed on top of it).
**Routing:** Claude Code, out-of-session. **Phase 1 is read-only.** Phase 2 is read-write (dirty-tree rules). Phase 3 is a supervised live re-prove (real Betfair reads read-only; no bet placement; worker flip stays the operator's).
**Status of the worker:** OFF and must stay OFF except the supervised Phase-3 re-prove window.

---

## 0. Why this brief exists (plain English)

The S223 lay-settlement fix is correct and verified. But the **first real live run** of the auto-settlement worker (S223, worker switched on supervised) surfaced a **separate, pre-existing gap**: the worker reads the race result fine, but it never gets the one signal it waits for before it will settle anything — Betfair's *"this market is settled"* stamp. So it holds every bet in "pending" forever. Nothing crashes, nothing mis-pays — it just never **finishes**.

This blocks cutover **B2** (auto-settlement can't be called live-proven). It is not caused by the S223 change; it lives in the settlement worker's Betfair read path (built earlier, only ever tested against fabricated payloads that *included* the stamp — the exact S189 "green tests aren't proof" trap).

The fix is a code change to how the worker decides a market is ready to settle. Because it's a money-path change, this brief runs **diagnosis first** (confirm exactly what real Betfair returns — don't fix an assumption), then a bounded fix, then a re-prove against the same real bet.

---

## 1. The evidence (from the S223 live run)

Repro bet — the backfilled lay, sitting `pending`, read live by the worker several cycles with no settlement:

- **Bet:** `bet-df31ffcd-c841-4593-a3bd-506f4dd41de2` — side **LAY**, stake 5.26 @ 3.5.
- **Market:** `1.259636589`, laid selection **`100232235`** (Gossamer Glow).
- **Stored `last_read_market_state`** (real read, written during the live run): `market_status = "CLOSED"`, **`settled_time = null`**, the laid selection `100232235` carries `settlement_status = "LOSER"`, `market_voided = false`, `removed_runner_count = 8`.
- **`reconciliation_attempts = 4`**, `last_reconciled_at = 2026-07-03T19:59:46` — read repeatedly, `settled_time` null every time, for a race that closed ~3 hours earlier.

**Real outcome, already legible:** the laid horse **lost** → the lay **won** → this bet should settle **SETTLED_WON, +$4.84**. (This is the *safe* branch — old and new code both book it won. The *dangerous* inversion branch — laid horse wins → must book the loss — is not live-exercisable on this bet because it didn't run that way; it stays covered by the S223 bench re-prove.)

---

## 2. The mechanism (code trace — the confirmed blocker)

1. **Resolver readiness gate** — `workflows/bet_entry/v1/settlement.py`, **both** resolvers:
   - `_resolve_settlement_for_bet` **line 672**: `if settlement.settled_time is None:` → returns no-decision, reason `market_not_yet_settled`, **bet stays PENDING**.
   - `_resolve_provisional_for_bet` **line 895**: same gate → **bet stays PROVISIONAL**.
   - Note this gate sits **before** the market-void branch (Step 5) and the runner-resolution branch (Step 6), so it also blocks void settlement, not just win/lose.

2. **Where `settled_time` comes from** — `clients/betfair_client/v1/_translation.py`, `_translate_market_settlement` (~line 583):
   ```
   "settled_time": md.get("settledTime") or market_book.get("settledTime")
   ```
   The settlement path translates the request to Betfair **`listMarketBook`** (`_translate_request`, ~line 190, `priceData: ["SP_TRADED"]`, no `marketProjection`).

3. **The gap:** Betfair's REST **`listMarketBook` response carries neither a `marketDefinition` block nor a `settledTime` field** (that field lives only in the *streaming* MarketDefinition and, differently, in `listClearedOrders`). So `md` resolves to `{}`, `market_book.get("settledTime")` is `None`, and **`settled_time` is always `None`** — the resolver's line-672/895 gate can never pass against real Betfair. Every bet is held in pending indefinitely.

**Confidence:** high (code + Betfair REST contract). Phase 1 confirms it against a live response before any edit.

---

## 3. Phase 1 — DIAGNOSIS (read-only, supervised live)

**Goal:** confirm the exact shape of a real Betfair `listMarketBook` response for a closed, settled racing market, so the fix keys off something real. **No code edits. No bet placement.** One or a few read-only live calls, operator at the machine.

Capture, for market **`1.259636589`** (and one other recently-settled market if available), the **raw JSON-RPC `listMarketBook` result** the worker's transport receives, and answer:

- **(a) The blocker — settled signal.** Confirm there is **no `settledTime`** and **no `marketDefinition.settledTime`** in the REST response. Record what fields *do* indicate settlement: `status` (expect `CLOSED`), `complete`, `numberOfWinners`, and per-runner `status` (`WINNER`/`LOSER`/`REMOVED`/`ACTIVE`).
- **(b) Runner status mapping.** Confirm the per-runner `status` values map cleanly to the worker's `WINNER`/`LOSER`/`REMOVED` (`_parse_runner`), and that the laid selection `100232235` reads `LOSER` as expected.
- **(c) Reduction-factor units — money-path.** Confirm the units of Betfair's per-runner `adjustmentFactor` in this response. The guard (`_evaluate_winner_guard`) treats it as a **percentage** and compares `>= 2.5` (`REDUCTION_MATERIALITY_THRESHOLD_PCT = 2.5`). If Betfair actually sends a **fraction** (e.g. `0.025`) or a different basis, the materiality gate is off by ~100× and park-vs-pay decisions are wrong. State the real basis and whether the 2.5 threshold is correct as-is. (The stored blob showed factors like 11.2 / 27.8 on non-removed runners — clarify what those are and whether they should even be read on non-`REMOVED` runners.)
- **(d) Is there a settled-time-bearing call at all?** Note whether `listClearedOrders` (`settledDate` per cleared order) or the streaming `marketDefinition.settledTime` is available and cheap — as an alternative to (or cross-check on) keying readiness off `CLOSED` + resolved runner.

**Output:** a short diagnosis note (append to `settlement_settled_signal_fix_report.md` or inline) stating what real Betfair returns for (a)–(d), and which fix direction §4 the evidence supports. **If (b) or (c) reveal a second real defect, STOP and surface it before building** — don't silently widen scope.

---

## 4. Phase 2 — the bounded FIX (read-write; land after Phase 1 confirms)

**Recommended direction (confirm against Phase 1 before locking):**

**Option A — key readiness off "market CLOSED + runner resolved", not `settledTime`.** Real Betfair `listMarketBook` expresses "settled" as `status == CLOSED` with the runner carrying a terminal `status` (`WINNER`/`LOSER`/`REMOVED`) — that *is* the settled signal; `settledTime` is a streaming-only artefact the REST path will never supply. So:
- Remove / replace the hard `settled_time is None` gate (lines 672 and 895). Market-readiness rests on Step 3's existing `market_status == CLOSED` check.
- Add a **runner-level readiness guard**: at runner resolution, if the leg's runner status is still `ACTIVE`/unresolved on a CLOSED market, return no-decision (new reason e.g. `runner_not_yet_resolved`) so the bet stays pending — preserving the "don't guess" caution without depending on `settledTime`.
- Any decision `detail` that currently formats `settlement.settled_time.isoformat()` must tolerate `settled_time = None` (drop it, or fall back to the read timestamp).
- **Preserve unchanged:** the market-void branch (Step 5), runner-REMOVED → VOIDED, the winner-guard park (dead-heat / material reduction), the **S223 LAY inversion** (WINNER→SETTLED_LOST / LOSER→SETTLED_WON for lays; BACK unchanged), and Option A create-path PENDING stamp.

**Option B — source a real settled-time** from `listClearedOrders` (`settledDate`) or the streaming `marketDefinition`. More faithful to "settled_time" semantics but heavier (new endpoint/translation, cleared-orders paging). **Only take B if Phase 1 shows `CLOSED` + resolved-runner is not a reliable settled signal** (e.g. markets that sit CLOSED with resolved runners yet later re-void). Default to A.

**If Phase 1 (c) finds the reduction-factor units are wrong:** fix the units / threshold comparison in the same change (it's the same money-path read), with a test pinning the real basis.

**Tests (must land together, and must reflect the REAL shape):**
- **Fix the fixtures to match reality (the S189 fix):** the settlement mock/fixtures must represent a real closed market — `settled_time` absent, readiness carried by `CLOSED` + terminal runner status — not a fabricated `settledTime`. This is what let the gap hide.
- Create-path unchanged (hedge → PENDING; soft-book → None).
- Both resolvers settle a CLOSED market with a terminal runner and **no** `settled_time` (PENDING→terminal; PROVISIONAL→terminal).
- A CLOSED market with an **unresolved** runner stays pending (`runner_not_yet_resolved`).
- Market-void still → VOIDED without `settled_time`.
- **SQLite-path end-to-end**: the backfilled-style LAY, CLOSED + laid selection `LOSER`, no `settled_time`, swept from the real store → **SETTLED_WON**.
- Keep the S223 LAY tests (both resolvers), BACK mapping, and the **F2** pending-sweep test green.
- If units fixed: a test pinning Betfair's real `adjustmentFactor` basis against the 2.5% line.
- `uv run pytest` green; `mypy` clean on changed modules; no new `ruff`.

---

## 5. Phase 3 — RE-PROVE (supervised live; worker OFF outside the window)

Against the **same** repro bet (`bet-df31ffcd…`, market `1.259636589`, sel `100232235`), in the live app, supervised:
- The worker completes a cycle and settles the bet **end-to-end** to **SETTLED_WON** (laid selection lost → lay wins → **+$4.84** through the real balance-derivation), with the money-path invariant intact (nothing silently overpaid).
- Confirm a CLOSED-but-unresolved market (if one is in book) correctly stays pending — the caution still holds.
- The **dangerous inversion branch** (laid selection wins → SETTLED_LOST) is **not** live-exercisable on this bet; it stays covered by the S223 bench re-prove — state that explicitly rather than implying full-branch live coverage.

Then flip the worker **OFF** again (unless the operator elects to continue a broader live-proving window per `settlement_liveproof_plan.md`).

---

## 6. Disciplines (load-bearing)

- **Read-and-confirm gate:** read this brief + the two source files (`settlement.py`, `_translation.py`) end-to-end and confirm understanding **before** editing.
- **Phase 1 is READ-ONLY:** diagnosis only — no edits, no placement; live Betfair reads are read-only (`listMarketBook` / optional `listClearedOrders`).
- **Phase 2 dirty-tree rules:** `git status` at start; edit **only** the named anchors (`workflows/bet_entry/v1/settlement.py`, `clients/betfair_client/v1/_translation.py`, their tests); `git diff` after each; **no git write ops** (no add/commit/checkout/stash); HEAD stays `e2638fa`.
- **Bet-safety:** `BETHUB_SETTLEMENT_WORKER` stays **OFF** except the supervised Phase-3 window; **Code does not flip it** — the operator does, at the machine. No bet placement anywhere. The only permitted DB write is settlement of the repro bet during the supervised re-prove (reversible; the S222 backup `data/bethub.db.bak-S222-20260703T194225` stands).
- **Stop conditions:** stop and surface if Phase 1 shows the blocker is *not* the `settledTime` gap; if a second money-path defect appears (units, runner mapping); if the fix would touch surface beyond the named anchors; or if the re-prove settles to anything other than SETTLED_WON.
- **Report:** produce `settlement_settled_signal_fix_report.md` in the rebuild folder — diagnosis findings (a)–(d), the fix as built, test results, and the re-prove outcome.

---

## 7. Governing DRs

DR-032 (Betfair is the settlement source of truth) · DR-033 (settlement Betfair-only; placings analytical) · DR-030 (module boundaries) · DR-027/028 (two-DB boundary) · DR-021 (Adelaide anchors). S189 lesson (fixtures ≠ live-proven) is the direct substrate for the Phase-2 fixture fix.
