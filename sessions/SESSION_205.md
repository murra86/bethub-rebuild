# SESSION 205

**Title:** Brief 1.1 executed + live (market-id enrichment); the 87%
market-id duplication finding exposed BetHub's missing race-identity
model → the **Data Foundation arc** stood up (structure doc + canonical
reference, §A filled). Brief 2 now gated behind the §B identity decision.
**Opened:** 2026-06-30 10:05 ACST (headless runner; fast-path open).
**Closed:** 2026-06-30 11:33 ACST.
**Tool routing:** Chat throughout (grounding, brief lock, scoping,
governance artefacts). Code executed Brief 1.1 out-of-session.
**Governing DRs:** DR-028 (single boundary), DR-027 (two-DB), DR-032
(Betfair canonical reference), DR-033 (source-role split), DR-021
(anchors), DR-034 *(pending — race-identity model, to be drafted S206)*.

---

## Anchor
- Open (runner): 2026-06-30 10:05 ACST. Close: `TZ="Australia/Adelaide"
  date` → 2026-06-30 11:33 ACST.

## Pre-flight checks
- Fast-path open: the S205 runner result was fresh (ran 10:04 > S204
  close 09:49); presented straight. Drift-check clean.
- Close pre-flight: rebuild root clean; `.close_out_backups/` held only
  the consumed S205 prompt; no phantom files.

## Session shape
A long, multi-pivot session. Began executing the staged S205 auto-action
(Brief 2 draft was held by the runner), but grounding Brief 1.1 first
collapsed its premise, then Code's Brief 1.1 report surfaced the 87%
market-id duplication — which the operator correctly read as a symptom
of a deeper structural gap (no defined cross-source race identity). The
session pivoted from interface-refinement execution into standing up a
**Data Foundation arc** to fix the foundation before building further on
it. Split triggers fired (duration + substantive scope change); closed
deliberately with §B (the deep identity work) deferred to S206.

## What was delivered
1. **Brief 1.1 grounded, re-scoped, locked, executed + live.** Live
   inspection showed the "thin endpoint" premise was 2/3 false
   (`RaceSummary` already returned `scheduled_start` + `state`; only
   `betfair_win_market_id` missing). Re-scoped tiny, locked
   (`vps_endpoint_enrichment_brief.md`, sha `ec70a2bd…`), Code executed
   (`vps_endpoint_enrichment_report.md`): the market-id field + a
   `/racing/results/by-market/{id}` route added, verified, no
   regression, dirty set unchanged (no git ops), bet-safe.
2. **The 87% duplication finding.** `betfair_win_market_id` is
   many-to-one — 16,033/18,418 market-bearing rows share a market id;
   the lowest-id sibling is typically a PENDING 0-runner shell, so the
   locked "first by id" tie-break returns the shell in the dominant
   case. Root: the natural key `(race_date, venue_normalised,
   race_number)` fragments one physical race (both race_date AND venue
   drift across the two ingest paths); the Betfair market id is the
   invariant.
3. **Data Foundation arc stood up.** `data_foundation_structure.md`
   (the approved frame) + `BETHUB_DATA_REFERENCE.md` (canonical living
   reference) — §A source contracts filled for all three sources
   (stale Racing-API cost/rate corrected), §G viability + §H supersede
   tracking filled, §A.4 + §B–§E scaffolded with named harvest targets,
   §B seeded with the identity spine. Confirmed the six existing data
   docs are harvest inputs (field-level work largely done), not rework.
4. **Source docs located/fetchable.** Betfair public page tree + on-disk
   captures; Racing API local `openapi.json` v1.4.3 (canonical) + the
   1546-line catalogue. Racing API plan/limits researched (no monthly
   quota; free=1/s, paid=5/s; AU-add-on tier question open).

## Open items
Pointer to `current_state.md`. New this session: the Data Foundation arc
(gates Brief 2); DR-034 pending (drafted S206); the Racing-API 1-vs-5/s
add-on rate (operator emailed provider 2026-06-30).

## Open items out
- Brief 1.1 drafted → locked → executed → triaged. ✅
- The "thin endpoint" premise — resolved (mostly false). ✅
- Structure-doc's four approval calls — all approved. ✅

## Session close state
- Rebuild root: `data_foundation_structure.md` +
  `BETHUB_DATA_REFERENCE.md` added; `vps_endpoint_enrichment_brief.md`
  (locked) + `..._report.md` present. `.close_out_backups/` holds the
  S206 opening prompt only.
- Project knowledge base: the two new docs + the reference may want
  uploading (operator-side, optional).

## Forward routing
**S206 first action = the deep §B identity session → DR-034 (canonical
race-identity model).** **Confirmed with operator** ("do B as auto-action
in s206"). Sequence after: §A.4 field harvest + §C/§D/§E → roadmap +
supersede → then Brief 2 re-locks against the locked identity →
cash-modal blank fix → settlement-worker → promo-seed → W16 cutover.
