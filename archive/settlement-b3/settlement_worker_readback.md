# Settlement-worker build — Code READ-AND-CONFIRM read-back (pre-edit gate)

> Captured Session 216 (2026-07-02 ACST). Code's mandatory §3 read-back on the
> LOCKED `settlement_worker_build_brief.md`. **Code is HELD at the gate — no edits
> made, tree clean — awaiting operator go-ahead AND a decision between options (1)
> and (2) in part (c) below.** S217 auto-action = triage this.

## (a) Anchor sha
- `git rev-parse HEAD` → `e2638fac2c659783448bece9b1810294512068bf` (e2638fa). `git status` clean, 0 ahead. HEAD unchanged from the brief's anchor; no report-header correction needed.
- Brief read in full + §3 pre-reads confirmed via direct file reads.

## (b) §5 anchors resolve
All 39 cited anchors across 8 files opened and confirmed to resolve. Six cosmetic drifts logged (none change the build):
- `settlement.py:777` — :777 is the `elif …PROVISIONAL:` guard; the `+= 1` on `provisional_entered` is :778. Impact: none.
- `settlement.py:1285` — :1285 is `@dataclass`; class on :1286. `ManualSettlementScheduler` at :1255, exported `__all__`:1337. Impact: none.
- `betfair/settlement.py` — file is 119 lines (trailing newline); brief said 118. Impact: none.
- `betfair/settlement.py:98-111` — :98-99 docstring; executable 404 map at :107-111; non-404 → `map_rest_error_read` :112. Impact: none.
- `promos.py:46/47` — constants `_GATE_STRATEGY_TAG`/`_GATE_SETTLEMENT_STATE`; the comparisons are at :209/210. Impact: none.
- `composition.py:8-21` mock default — docstring prose; the typed declaration is `config.py:58` `betfair_mode: Literal["live","mock"]="mock"`. Impact: relevant to (c)/the flag.

Two load-bearing confirmations for the build:
- **New opt-in flag** lives in `ui/api/config.py` — `Settings(BaseSettings)` with `env_prefix="BETHUB_"` (config.py:34-37). Declaring `settlement_worker: bool = False` there auto-binds env var `BETHUB_SETTLEMENT_WORKER`. Inside §9's `ui/api/` surface.
- **RealSettlementReader template** confirmed: `betfair_adapter.py`'s `RealBetfairAdapter` (:97-125) ReadEnvelope → ReadOutcome pattern; `get_market_settlement` (:305-324) the closest analogue to mirror. `bet_entry/v1/__init__.py` exports none of the settlement pass/scheduler/reader surface today (only W6 reconciliation) — Refinement B export is real.

## (c) §5.1a decision + reduction-factor sourcing
Code's understanding of the resolved decision **matches the brief**: Option C (precise, market-type-aware) with Option B pre-authorised fallback; gate `WINNER → SETTLED_WON` in both resolvers; dead-heat parks on `dead_heat_count > 0`; removed-runner parks on a material reduction (WIN ≥2.5%, PLACE any factor >0); §5.1b verification record on every removed-runner decision (park / paid-full / fallback-flagged); Option B flag if the factor can't be sourced live; never silently auto-pay full on a parked case; never model the maths.

**Sourcing — Code chose the ENRICHED SETTLEMENT PAYLOAD, not a companion market-book read.** Grounds:
- Reduction factor absent everywhere today (not on `RunnerSettlement`, not read by `_parse_settlement`; repo-wide grep for `adjustmentFactor|adjustment_factor|reduction*factor` returns zero hits).
- No companion market-book read surface carries it either (`live_pricing.py RunnerPrices`, `market_catalogue.py RunnerCatalogue`, stream parser all omit `adjustmentFactor`). A companion read = new surface + per-settled-bet fan-out reads with divergent freshness — strictly more invasive than enriching the payload.
- The settlement wire is owned end-to-end: `_translate_market_settlement` (`clients/betfair_client/v1/_translation.py:550-586`) already builds the settlement dict from a Betfair market book and already lifts per-runner `removalDate` (:567) off the same raw runner dict where Betfair's `adjustmentFactor` sits. The removed-runner signal already rides this payload, so the factor is its natural companion.

## ⚠️ The §9 edit-surface decision Code needs resolved before it starts
§9 authorises betfair-client edits to "the settlement model + `_parse_settlement`", plus a market-book read surface only if a companion read is required. The enriched-payload route splits:
- **Inside §9's named surface:** the model change (`RunnerSettlement` + `adjustment_factor`/applied flag) and the `_parse_settlement` lift — both in `clients/betfair_client/v1/settlement.py`. All §7 5.1 success criteria are satisfiable here (tests drive `MockSettlementReader` with domain `MarketSettlement` fixtures). Guard logic lives in `bet_entry/v1/settlement.py` (in-surface).
- **Outside §9's named surface:** populating the field from a real Betfair book needs one additive line in `_translate_market_settlement` (`_translation.py:561-570` — `r.get("adjustmentFactor")`). §9 names neither `_translation.py` nor this function; its only betfair-client carve-out is for a companion market-book read (which Code shows is unnecessary and more invasive).

**Code needs a pick before it edits:**
1. **Authorise the single additive line in `_translation.py`** under the same "name exactly what you added" discipline §9 applies to the companion-read carve-out. → Option C ships **live-effective**. *(Code's recommendation — minimal, additive, a read of an existing raw field, strictly cheaper than the carve-out §9 already blesses.)*
2. **Stay strictly inside the `settlement.py` named surface.** → Option C ships **plumbed-and-tested** (model + `_parse_settlement` + guard + full fixture tests), with `_translation.py` population logged as a required named follow-up. Interim live behaviour is safe: field unpopulated → every removed-runner winner reads `adjustment_factor = None` → the pre-authorised Option B park fires (never a silent full-payout). This is exactly the §5.1a "field absent from the real payload" fallback trigger.

Either path keeps the money-path invariant intact; the only difference is whether the precise arm is live-effective now or on a named follow-up. Code stopped per §3 — no edits, tree clean — awaiting go-ahead + the (1)/(2) call.

## Triage notes for S217 (operator-Claude)
- This is a **HOLD** first action: triage the read-back, recommend the (1)/(2) call + the go-ahead, then hold for the operator. Sending the go-ahead to Code and picking (1)/(2) is the operator's money-path call.
- The (1)/(2) question is narrow and low-risk: both keep the money-path invariant; (1) is one additive line reading an existing raw field, (2) defers that one line to a named follow-up and leans on the already-authorised Option B park in the interim. Code recommends (1).
