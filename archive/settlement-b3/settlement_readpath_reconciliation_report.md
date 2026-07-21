# Report — settlement read-path reconciliation (read-only; find-all, fix-none)

**Run:** Session 223, 2026-07-03 ACST (DR-021 Adelaide anchor).
**Author:** Claude Code (Plan Mode / read-only).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (unchanged — no edits, no test edits, no DB writes, no bet placement, no flag flip; `BETHUB_SETTLEMENT_WORKER` stayed **OFF** throughout).
**Brief:** `settlement_readpath_reconciliation_review_brief.md`.
**Deliverable:** this report only. **Nothing was fixed inline.**

---

## 0. Verdict (money-path first, unmistakable)

**The path is NOT reconciled fix-free.** Four actionable findings — and, cleanly, **all four land in the single function `clients/betfair_client/v1/_translation.py::_translate_market_settlement`**, so they batch into **one bounded fix** in one place.

Two are genuine silent-money-path defects that must not reach the live window unseen:

- **F1 (money-path, HIGH) — a dead-heat winner silently over-settles.** `_translate_market_settlement` hardcodes `dead_heat_count = None` (`_translation.py:588`). A real dead heat is represented by Betfair as **≥2 runners with `status == "WINNER"`** — which the translation keeps as WINNER but never counts. So `dead_heat_count` is **always None from a real read**, the winner-guard dead-heat park (`workflows/bet_entry/v1/settlement.py:480-483`) **can never fire in production**, and a dead-heating selection auto-settles at **full** winnings/liability. This is the exact shape the brief said to watch hardest, and it is broken. Its 3 green "dead-heat park" tests all inject `dead_heat_count=2` **directly onto a hand-built `MarketSettlement`**, bypassing the translation — so they prove the resolver, never the read.

- **F2 (money-path, LOW/latent — NEW, surfaced by the completeness pass) — a status-less runner defaults to WINNER, the bet-*unsafe* direction.** `_translation.py:560` does `status = r.get("status", "WINNER")`. A runner dict missing its `status` key is treated as a clean WINNER, increments **neither** the removed nor the unexpected counter, and so **passes the readiness gate unguarded** → a BACK bet on that selection auto-settles `SETTLED_WON` at full. Every *other* unrecognised status collapses to LOSER + `unexpected_state_count++` (the bet-safe park direction); only a *missing* status points the wrong way. Latent (real Betfair populates `status` on CLOSED markets), but it is a wrong-direction default on the money path and belongs in the same one-line-per-field fix.

Two more are non-silent (they hold or stick a bet rather than mis-pay), but still need the same batched fix:

- **F3 (liveness + low-confidence money-path tail) — a market-level void never auto-VOIDs.** `market_voided` is derived from `marketDefinition.marketVoided` (`_translation.py:587`), a field REST `listMarketBook` **never returns** (no `marketDefinition` block at all — confirmed empirically on the real capture). So `market_voided` is **always False** and the Step-5 void→VOIDED branch is **dead code** on the real read path. Verified outcome across the plausible real void representations is **money-safe** (the bet self-catches into held PENDING via the readiness gate, or self-heals via the runner-REMOVED→VOIDED branch); the residual money-path tail is low-confidence and only fires if a real void ever presents the bet's own runner as a clean LOSER (not expected for an abandonment, which has no winner and refunds all stakes). Primary live impact: **voided-market bets accumulate in PENDING and require manual resolution** — there is no automatic void settlement.

- **F4 (liveness) — a `REMOVED_VACANT` / `HIDDEN` runner freezes the whole market's settlement.** Betfair's runner-status enum is `{ACTIVE, WINNER, LOSER, REMOVED_VACANT, REMOVED, HIDDEN}`; the translation recognises only exact `"REMOVED"` (`:565`). A vacant trap (greyhounds) or a hidden runner therefore collapses to LOSER + sets `unexpected_state_count > 0` **permanently**, and the market-wide readiness gate (`settlement.py:737` / `:973`) returns `runner_not_yet_resolved` on every pass → **every bet in that market stays stuck PENDING/PROVISIONAL forever** (no mis-pay, but never settles; only the 30-min `is_past_settlement_window` visibility flag surfaces it).

Plus two cosmetic fixture-hygiene items that can ride along in the same change (C-5 `bsp`, C-6 fabricated `settledTime`) — neither affects a settlement decision.

**What the review CLEARED (and it matters):** the brief's *other* watch-hardest item — the `paid_full` decision — is **verified sound**. Betfair applies the Rule-4 2.5% materiality test **per withdrawn runner, not cumulatively** (high-confidence, sourced), `adjustmentFactor` is a percentage (real-capture-confirmed values 0.099…11.251), and the guard's per-runner gate mirrors Betfair's own rule exactly. `paid_full` fires only when every removed factor is genuinely <2.5%, which is precisely a Betfair zero-deduction settlement. **No silent over-payment exists on the removed-runner reduction arm.** The LAY inversion (S222), the REMOVED→VOIDED path, `selection_id` matching, and `market_status` sourcing are all reconciled against the real capture.

**Recommendation:** open **one** batched fix brief against `_translate_market_settlement` (F1–F4 + C-5/C-6), re-prove, and keep the worker OFF until then. Do **not** open the live-proving window on the dead-heat (shape 7) or market-void (shape 6) shapes before the fix.

---

## 1. Coverage matrix — the 9 shapes

Columns: **Decision correct?** (resolver logic) · **Every consumed field real?** (does real `listMarketBook` supply it, in this basis) · **Fixture matches reality?** · **Confirmed against** (real-capture / schema-only) · **Finding**.

| # | Shape | Decision correct? | Consumed fields real? | Fixture = reality? | Confirmed against | Finding |
|---|-------|:---:|:---:|:---:|---|---|
| 1 | **BACK winner** → SETTLED_WON | ✅ | ✅ `status=WINNER` | ✅ | **real-capture** (1 WINNER, sel `100232243`) | — reconciled |
| 2 | **BACK loser** → SETTLED_LOST | ✅ | ✅ `status=LOSER` | ✅ | **real-capture** (10 LOSER) | — reconciled |
| 3 | **LAY, laid wins** → SETTLED_LOST | ✅ (inversion) | ✅ `side`+`status=WINNER` | ✅ | schema/logic (S222; not live-seen) | — reconciled |
| 4 | **LAY, laid loses** → SETTLED_WON | ✅ (inversion) | ✅ `side`+`status=LOSER` | ✅ | **real-capture** (Gossamer Glow, +4.84 collect) | — reconciled *(the one real anchor)* |
| 5 | **Selection REMOVED** → VOIDED | ✅ (`status=REMOVED`) | ✅ `status`/`adjustmentFactor`/`removalDate` | ✅ | **real-capture** (8 REMOVED) | reconciled for exact `REMOVED`; gap for `REMOVED_VACANT` → **F4** |
| 6 | **Market-level void** → VOIDED | logic ✅, **input dead** | ❌ `marketDefinition.marketVoided` never sent | ❌ injects `market_voided=True` | **real-capture** (no `marketDefinition`) | **F3** |
| 7 | **Dead-heat park** → PROVISIONAL | logic ✅, **input dead** | ❌ `dead_heat_count` hardcoded None; real dead-heat = ≥2 WINNER, uncounted | ❌ injects `dead_heat_count=2` | schema-only | **F1** (money-path) |
| 8 | **Material / immaterial Rule-4** → PARK / paid_full | ✅ | ✅ `adjustmentFactor` (percentage, lifted) | ✅ realistic (factors flow through translation) | **real-capture** + HIGH-confidence Betfair rule | — reconciled; **`paid_full` verified sound** |
| 9 | **CLOSED, runner unresolved** → stay pending | ✅ (readiness gate) | ✅ `status`/`unexpected_state_count` | ✅ | **real-capture** (`unexpected=None`, all clean) | reconciled for transient ACTIVE; gap for permanent `REMOVED_VACANT`/`HIDDEN` (**F4**) and status-default (**F2**) |

**Confirmed-against-real-data:** shapes 1, 2, 4, 5, 8. **Schema/logic-only (watch in the live window):** 3, 6, 7, 9 — with shapes 6 and 7 **broken** (do not open the window on them un-fixed) and 3 simply not-yet-seen-live.

---

## 2. Findings

Each finding: what · where · real-world outcome (BACK/LAY) · classification · confidence · confirmed-against · fix direction (for the batched brief — **not applied**).

### MONEY-PATH

#### F1 — Dead-heat winner silently over-settles *(HIGH confidence; schema/logic-confirmed)*
- **What.** `_translate_market_settlement` hardcodes `"dead_heat_count": None` (`_translation.py:588`); the runner loop counts REMOVED and non-terminal statuses but **never tallies WINNER occurrences**. The client `_parse_settlement` passes the value through verbatim (`clients/betfair_client/v1/settlement.py:121`). The winner-guard dead-heat trigger is solely `settlement.dead_heat_count is not None and > 0` (`workflows/bet_entry/v1/settlement.py:480-483`), so it is **always False on a real read**. A real dead heat = ≥2 runners with `status == "WINNER"` (Betfair schema), which the translation keeps as WINNER and never counts.
- **Outcome.** **BACK** on a dead-heating selection: runner is WINNER → guard `park=False` → `SETTLED_WON` at **full** winnings, but a real dead heat divides the stake by the number of dead-heaters → **silent over-pay of profit**. **LAY** on the dead-heating laid selection: `_winner_terminal_state(LAY) = SETTLED_LOST` at **full** liability, but real dead-heat liability is proportionally reduced → **silent over-book of liability against the operator**.
- **Why the tests miss it.** Every green dead-heat test (`test_settlement.py:507-540`, `:2855`; `test_settlement_guard.py:130-192`) injects `dead_heat_count=2` **directly onto a hand-built `MarketSettlement`**, never through `_translate_market_settlement`. `test_consumer.py:157` even asserts the translation emits `dead_heat_count=None`. No test feeds ≥2 raw WINNER runners through the translation and expects a count. The guard *looks* fully proven (11 green tests) while half of it is unreachable in production.
- **Confirmed against.** Schema-only — the real capture (market `1.259636589`) had a single WINNER, so it did not exercise a dead heat, but it *did* confirm the parse yields `dead_heat_count=None`.
- **Fix direction.** In `_translate_market_settlement`, count runners whose resolved status is WINNER and set `dead_heat_count = winner_count` when `winner_count >= 2` (else `None`), so the existing guard park fires on a real read. (WIN markets pay one winner; ≥2 WINNER ⇒ dead heat.)

#### F2 — Missing runner status defaults to WINNER, the bet-unsafe direction *(LOW/latent confidence; NEW)*
- **What.** `_translation.py:560`: `status = r.get("status", "WINNER")`. A runner dict lacking a `status` key is silently a clean WINNER (in the valid set at `:565`), and increments **neither** `removed_count` **nor** `unexpected` (`:576-579`). So it yields `unexpected_state_count = None`, **passes the readiness gate**, and — if it is the bet's own selection on a BACK bet — auto-settles `SETTLED_WON` at full (`settlement.py:761-797`).
- **Outcome.** A wrong-direction default: every *known* unrecognised status collapses to LOSER + `unexpected++` (bet-safe park), but a *missing* status collapses to WINNER + nothing (bet-**unsafe** pay), with no guard and no readiness catch.
- **Confirmed against.** Schema/logic — Betfair normally always populates `Runner.status` for a CLOSED market, so this is a **latent landmine**, not an observed live misfire.
- **Fix direction.** Default an absent/unknown status to the conservative side (e.g. treat as ACTIVE/unknown → `unexpected++`, or park), never WINNER.

#### F3 — Market-level void never auto-VOIDs (dead branch); money-safe, low-confidence money-path tail *(liveness-primary)*
- **What.** `market_voided = bool(md.get("marketVoided", False))` with `md = market_book.get("marketDefinition") or {}` (`_translation.py:554,587`). REST `listMarketBook` returns **no `marketDefinition` block** (confirmed empirically: the real capture had none) and there is **no `marketVoided` field anywhere in Betfair's API** (the only void-adjacent field is streaming-only `runnersVoidable`, and even the field *name* here is wrong). So `market_voided` is **provably always False on real reads** and the Step-5 `voided_market_voided` → VOIDED branch (`settlement.py:701` / `:932`) is **unreachable dead code**.
- **Outcome (verified money-safe across plausible representations).** A genuine abandonment/void presents (per Betfair refund rules + historical-data behaviour, medium confidence) as `status=CLOSED`, runners **retaining ACTIVE**, **no WINNER**, all stakes refunded. Traced through BetHub: ACTIVE collapses to LOSER + `unexpected_state_count>0` → readiness gate holds the bet **PENDING indefinitely** (safe, not a mis-pay). Alternatively, if the leg runner is marked REMOVED, the runner-REMOVED→VOIDED branch fires and the bet **correctly voids**. The **only** mis-settle path — leg returns a clean LOSER with `unexpected==0` — cannot occur for a void, because a void has no winner and does not forfeit backer stakes by marking runners LOSER. Hence: **no wrong payout in the expected representations**; residual money-path tail is low-confidence.
- **Live impact.** Voided-market bets **never auto-settle to VOIDED** — they pile up in PENDING/PROVISIONAL and rely entirely on the operator + the 30-min visibility flag. Fixtures (`test_settlement.py:356`, `:3047`) inject `market_voided=True` directly — a field reality never sends.
- **Confirmed against.** Real-capture (absence of `marketDefinition`) + schema. No real *voided-market* capture exists → the void representation itself is unobserved (watch hardest for a void in the live window).
- **Fix direction.** Derive void from real runner-level signals (e.g. CLOSED with no WINNER and every runner non-terminal/REMOVED), not from `marketDefinition.marketVoided`; keep the streaming field as a fallback only. At minimum, document the branch as dead on REST and route abandonments to explicit operator handling.

### LIVENESS

#### F4 — `REMOVED_VACANT` / `HIDDEN` runner freezes the whole market's settlement *(MEDIUM confidence; schema-confirmed)*
- **What.** The readiness gate exists to wait out a *transient* ACTIVE runner in a CLOSED market (settlement not yet propagated) — which self-heals when the runner flips to WINNER/LOSER. It does **not** cover `REMOVED_VACANT` (greyhound vacant trap) or `HIDDEN`, which are **stable** Betfair statuses that persist unchanged in a settled market book. The exact-match on `"REMOVED"` (`:565`) collapses them to LOSER and sets `unexpected_state_count ≥ 1` **permanently**; the market-wide gate (`settlement.py:737` / `:973`, keyed off the market's `unexpected_state_count`, not the bet's own runner) then returns `runner_not_yet_resolved` on every pass and **never opens**. Nothing downstream clears the count.
- **Outcome.** Any bet whose market contains ≥1 `REMOVED_VACANT`/`HIDDEN` runner **never auto-settles, regardless of side** — a cleanly-won BACK and a cleanly-lost-laid LAY both stick PENDING (or PROVISIONAL) forever. No wrong-state payout (not money-path), but no settlement either; after 30 min only `is_past_settlement_window` flags it for manual resolution. Live incidence depends on whether BetHub reads greyhound markets (`REMOVED_VACANT`) or HIDDEN-carrying horse markets.
- **Confirmed against.** Schema-only — the real capture's 8 removed runners were exact `"REMOVED"` (clean, `unexpected=None`), silent on the vacant/hidden case rather than disproving it.
- **Fix direction.** In `_translate_market_settlement`, treat `REMOVED_VACANT`/`HIDDEN` as terminal-non-participating (map like REMOVED, or exclude from `unexpected_state_count`) so the readiness gate counts only genuinely-pending ACTIVE runners.

### COSMETIC (no decision impact — fixture / audit hygiene)

#### C-5 — `bsp` misread from a non-existent top-level field *(HIGH; real-capture-confirmed; inert)*
- `_translate_market_settlement` reads `r.get("bsp")` (`:568`), but REST `Runner` has **no top-level `bsp`** — the settled SP is `sp.actualSP`. So `bsp` is **always None on a real read** (the Gossamer Glow runners carried none). No settle-path decision reads `bsp` (verified: zero references in the resolver; state comes from `status`, amount from the bet's own matched price), so it never mis-settles or mis-pays. Effect is purely that the persisted `last_read_market_state` audit JSON always records `bsp=null` instead of the settled SP. **Fix (optional):** read `r.get("sp", {}).get("actualSP")` (fall back to `r.get("bsp")` for streaming payloads).

#### C-6 — Fixtures fabricate `settledTime` / `marketDefinition.settledTime` *(HIGH; real-capture-confirmed; hygiene)*
- Many resolver fixtures set a concrete `settled_time`, and the translation unit test (`tests/clients/betfair_client/v1/test_settlement.py:117`) fabricates `marketDefinition.settledTime` — fields real `listMarketBook` never sends. **Post-S223 the resolver no longer gates on `settled_time`**; it is read only via `_settled_time_iso()` into an audit-only `detail` string, so these fixtures cause **no decision distortion**, and the real None-shape is independently covered by dedicated tests (`:473`, `:1900`, `:3047`, `:3070`). Pure test-realism imperfection. **Fix (optional):** default the `_settlement()` helper to `settled_time=None`; relabel the `:117` case as a streaming-shape parse test; keep one non-None fixture to exercise the populated `_settled_time_iso` branch.

---

## 3. Verified SOUND (refuted candidates + assurance)

These were checked adversarially (each verifier tried to *refute* soundness) and stand:

- **`paid_full` / Rule-4 materiality — SOUND (HIGH).** Betfair applies the 2.5% test **per withdrawn runner, not cumulatively** (each sub-2.5% removal produces *zero* deduction on the win market; the "cumulative" wording in Betfair's docs refers to recomputing *remaining* runners' factors upward, which are then themselves reported ≥2.5% and caught per-runner). `adjustmentFactor` is a percentage (real-capture values 0.099…11.251; a non-removed runner's 27.822 is a rating, correctly ignored). The guard's WIN ≥2.5% / PLACE any>0 gate mirrors Betfair's own rule. **paid_full at full odds is the correct settlement — no silent over-payment.** *(Was the brief's second watch-hardest item; cleared.)*
- **LAY inversion — SOUND.** `_winner_terminal_state`/`_loser_terminal_state` invert correctly in both resolvers; real capture booked laid-loses → SETTLED_WON (+4.84). The LOSER branch is correctly **unguarded** for a winning lay (Rule-4 does not reduce a lay collect).
- **`voided` runner flag unused — NOT a defect (HIGH).** `voided = bool(removalDate) and status=="REMOVED"` is a strict **subset** of `settlement_status=="REMOVED"`, which is what the resolver voids on — the safe/correct key. Reading `voided` could only void *less*, never more. Retained for audit only.
- **`selection_id` matching — SOUND.** `str == str` throughout (`_translation.py:563` stringifies; the leg field is typed `str`); real capture matched.
- **`SP_TRADED` projection — SOUND.** `Runner.status` and `adjustmentFactor` are returned regardless of `priceData`; confirmed by the 19-runner real capture.
- **`market_status` — real source.** Read from the genuine top-level `market_book.get("status")` (listMarketBook does return `status=CLOSED`), not a fabricated field.

---

## 4. The batched fix (outline only — do NOT apply here)

Every actionable finding is in **one function**, `clients/betfair_client/v1/_translation.py::_translate_market_settlement`. A single bounded change:

1. **F1** — count WINNER-status runners; set `dead_heat_count = winner_count if winner_count >= 2 else None`.
2. **F2** — change the status default from `"WINNER"` to a conservative unknown that increments `unexpected_state_count` (never auto-wins).
3. **F4** — map `REMOVED_VACANT`/`HIDDEN` to terminal-non-participating so they don't inflate `unexpected_state_count`.
4. **F3** — derive `market_voided` from runner-level signals (or document the branch dead on REST + route abandonments to operator handling); stop reading `marketDefinition.marketVoided`.
5. **C-5** (optional ride-along) — read settled SP from `sp.actualSP`.
6. **C-6** (optional ride-along) — scrub fabricated `settledTime` from fixtures.

The resolver (`workflows/bet_entry/v1/settlement.py`) needs **no change** — F1 simply makes the existing dead-heat guard reachable; F3/F4 restore correct inputs to gates that are already right. **New tests must drive `_translate_market_settlement` from raw `listMarketBook` JSON** (≥2 WINNER runners; a status-less runner; a `REMOVED_VACANT` runner; a void shape) — the missing translation-layer coverage that let F1/F3 hide behind resolver-only fixtures.

---

## 5. Live-window guidance

- **Do not open the live-proving window on shape 6 (market void) or shape 7 (dead-heat) before the fix** — both are broken against real reads.
- **Confirmed against real data (safe to trust now):** BACK win/lose, LAY laid-loses (the Gossamer Glow anchor), REMOVED (exact), material/immaterial Rule-4 incl. `paid_full`.
- **Schema/logic-only — watch these specific settlements during the supervised window:** a clean single-winner **dead heat** (F1), any **abandoned/voided** race (F3 — capture how a real void presents its runners; this is the one unobserved shape that matters most), a **greyhound market with a vacant box** (F4), and a **LAY whose laid selection wins** (shape 3, correct but not yet seen live).
- The optional live-capture step (reading a couple more real settled markets of different shapes) was **not** performed — this run was unattended static reconciliation against the one real capture we hold, plus Betfair's documented schema and rules. The confirmed-vs-schema-only split above marks exactly what remains to be seen against real data.

---

## 6. Method & disciplines

- **Read-and-confirm gate honoured:** the brief and all four scoped files were read end-to-end (`_translation.py`, `clients/.../settlement.py`, `workflows/.../settlement.py`, `tests/workflows/bet_entry/v1/test_settlement.py`), plus the adjacent `test_settlement_guard.py` and `tests/clients/betfair_client/v1/test_settlement.py` (they carry the shape-7/8 and translation fixtures).
- **Empirical grounding:** calibrated against the one real capture (`last_read_market_state` on `bet-df31ffcd…`, market `1.259636589`) and its provenance in `settlement_settled_signal_fix_report.md` / `settlement_correctness_fix_report.md`; corroborated against Betfair's published `listMarketBook`/Runner schema, the runner-status enum, and the Exchange non-runner/Rule-4 rules.
- **Adversarial verification:** each candidate finding was independently refuted-tested; the two open Betfair-behaviour questions (void representation; cumulative vs per-runner Rule-4) were researched to source; a completeness pass swept for a missed shape/field (which surfaced **F2**). Two schema-confirmation sub-agents failed on an output-format cap; their content (runner-status enum incl. `REMOVED_VACANT`/`HIDDEN`; no top-level `bsp`; `adjustmentFactor` percentage; no `marketDefinition` in REST) is independently corroborated above and does not change any verdict.
- **Read-only throughout:** `git status` unchanged; HEAD stays `e2638fa`; no production or test edits; no bet placement; no DB writes; `BETHUB_SETTLEMENT_WORKER` untouched. Real Betfair was not called in this run (static reconciliation).

**Governing DRs:** DR-032/033 (Betfair settlement source of truth), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-021 (Adelaide anchor). S189 (fixtures ≠ live-proven) is the direct reason F1 and F3 existed undetected — the fix must add translation-layer coverage against raw `listMarketBook`, not more resolver fixtures.
