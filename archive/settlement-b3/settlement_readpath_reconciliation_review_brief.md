# Brief — settlement read-path reconciliation review (read-only; find-all, fix-none)

**Drafted:** Session 223, 2026-07-03 ACST (DR-021 Adelaide anchor).
**Author:** Chat (governance / operator-facing).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (dirty tree — worker build + S223 LAY fix + settled-signal fix).
**Routing:** Claude Code, Plan Mode / read-only. **This is a REVIEW, not a build.**
**Worker flag:** stays **OFF** throughout. No edits, no placement, no DB writes, no flag flip.

---

## 0. Why this exists (plain English)

Two live gaps have now bitten us in a row (the lay inversion; the settled-signal gate) — and both had the same root cause: **the bench test fixtures didn't match what real Betfair actually returns**, so the code looked proven when it wasn't. We've now verified exactly **one** real market shape (Gossamer Glow — a losing lay in a heavily-reduced race). Every *other* settlement shape is still only bench-tested against fixtures we haven't checked against reality.

The operator does not want to discover these one-at-a-time during live betting. **This review's single job: reconcile the whole settlement read-and-resolve path against real Betfair, across every shape Strategy-1 win-market betting can produce, and surface ALL remaining gaps in one pass** — so any fixes are batched into one bounded change and the live-proving window is fix-free. **Find everything; fix nothing inline.**

---

## 1. Scope — the read/resolve path only

- **Translation:** `clients/betfair_client/v1/_translation.py` — `_translate_market_settlement`, `_parse_runner`, and the `/v1/market/{id}/settlement` → `listMarketBook` request mapping.
- **Reader:** `clients/betfair_client/v1/settlement.py` — `_parse_settlement`, `market_settlement`, the `MarketSettlement`/`RunnerSettlement` shapes, `RunnerSettlementStatus`.
- **Resolvers + guard:** `workflows/bet_entry/v1/settlement.py` — `_resolve_settlement_for_bet`, `_resolve_provisional_for_bet`, `_evaluate_winner_guard`, `_is_place_market`, the readiness guard, the LAY terminal helpers.
- **Fixtures:** `tests/workflows/bet_entry/v1/test_settlement.py` — every settlement fixture, checked field-by-field against the real Betfair shape.
- **Out of scope:** placement, streaming, pricing, matching/reconciliation, the promos path, anything not on the settle-a-bet path.

**Betfair source of truth for this review:** the real REST `listMarketBook` response for a settled racing market (the settlement path uses it). The one real capture we hold: `last_read_market_state` on bet `bet-df31ffcd-c841-4593-a3bd-506f4dd41de2` (market `1.259636589`).

---

## 2. The reconciliation — shape by shape

For **each** settlement shape below, produce three things: **(i)** the resolver decision the code produces (trace it), **(ii)** the full list of Betfair fields the path consumes to get there, and **(iii)** a verdict on whether each consumed field, and the matching test fixture, reflects the **real** `listMarketBook` shape (present? correct basis/units? not fabricated?).

Shapes (Strategy-1 win markets — BACK and LAY):
1. **BACK winner** → SETTLED_WON.
2. **BACK loser** → SETTLED_LOST.
3. **LAY, laid selection wins** → SETTLED_LOST (the dangerous inversion — confirm both resolvers).
4. **LAY, laid selection loses** → SETTLED_WON (the Gossamer Glow shape — the one real anchor).
5. **Selection REMOVED** (backed or laid) → VOIDED.
6. **Market-level void** → VOIDED (and that it precedes the readiness guard).
7. **Dead-heat winner** → PARK (PROVISIONAL) — and confirm how a dead-heat is *actually represented* in real `listMarketBook` (is `dead_heat_count` even derivable from it? where from?).
8. **Material Rule-4 reduction on a winner (≥2.5%)** → PARK; **immaterial (<2.5%)** → `paid_full` (settle full) — confirm the `adjustmentFactor` basis end-to-end and that `paid_full` only fires when the real reduction is genuinely trivial.
9. **CLOSED but a runner unresolved** → stay pending (`runner_not_yet_resolved`) — confirm real Betfair can even present this, and that the `else "LOSER"` collapse + `unexpected_state_count` gate behaves.

**The specific question that has bitten us twice, asked of every field:** *does real Betfair `listMarketBook` actually return this field, in this shape, with this basis — or is the fixture asserting something Betfair never sends?* (The settled-signal gap was exactly a fixture asserting a `settledTime` that `listMarketBook` never returns. Hunt that class everywhere.)

Pay special attention to: **dead-heat representation** (shape 7 — where does `dead_heat_count` come from in a real REST response?), and the **`paid_full` decision** (shape 8 — the one place a real over-payment could settle silently).

---

## 3. Empirical grounding (don't audit against assumptions alone)

- **Calibrate against the real capture** we hold (`last_read_market_state`, market `1.259636589`) — every field in it is ground truth for shape 4 / 5 / 8.
- **Where a supervised live window is available:** capture, **read-only**, the real `listMarketBook` settlement response for 2–3 additional recently-settled AU racing markets of *different* shapes (ideally a clean single winner, a straightforward market with no removals, and one with a dead-heat or material reduction if findable). Diff each against the §2 assumptions and the fixtures. (Note the aging-out constraint: fully-settled markets 404 out of the API window, so capture near settlement.)
- **If live capture isn't available**, complete the review against the real capture + Betfair's documented `listMarketBook` response schema, and **explicitly mark which shapes remain confirmed-by-schema-only vs confirmed-against-real-data** — so the live window knows which settlements to watch hardest. Do not present schema-only confirmation as live-proven.

---

## 4. Output — a coverage matrix + batched findings

Produce `settlement_readpath_reconciliation_report.md` with:
- **A coverage matrix:** rows = the 9 shapes; columns = resolver-decision-correct? · every-consumed-field-real? · fixture-matches-reality? · confirmed-against (real-capture / live-capture / schema-only).
- **A findings list**, each classified:
  - **money-path** (settles to the wrong state / silently overpays),
  - **liveness** (never settles — stuck pending, the settled-signal class),
  - **cosmetic** (audit-line / naming only).
- **A verdict:** either "path reconciled — the live window can open fix-free" (with the caveat of any schema-only shapes), OR "N findings — batch into one bounded fix before the live window."

**Do NOT fix anything inline.** If findings exist, they go into **one** follow-up bounded fix brief (batched), not serial edits. The point of this pass is to make the *next* code change the *last* one.

---

## 5. Disciplines (load-bearing)

- **READ-ONLY, entire review.** No production or test edits; no bet placement; no DB writes; `BETHUB_SETTLEMENT_WORKER` stays OFF and is not flipped by Code. Real Betfair reads are read-only (`listMarketBook`); no `placeOrders` anywhere.
- **Dirty tree untouched:** `git status` at start; **no** edits, **no** git write ops; HEAD stays `e2638fa`.
- **Read-and-confirm gate:** read this brief + the four scoped source files end-to-end before analysing.
- **Stop/scope:** the deliverable is findings, not fixes. If a finding is money-path (a bet could settle wrong or silently overpay), flag it **first** and unmistakably — that is the one class that must not reach the live window unseen.
- **Report:** `settlement_readpath_reconciliation_report.md` in the rebuild folder.

---

## 6. Governing DRs

DR-032 (Betfair is the settlement source of truth) · DR-033 (settlement Betfair-only) · DR-030 (module boundaries) · DR-027/028 (two-DB boundary) · DR-021 (Adelaide anchors). S189 (fixtures ≠ live-proven) is the direct reason this review exists.
