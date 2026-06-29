# Session 39 — Saturday API observation probe brief drafted

**Opened:** 2026-04-30 18:52 ACST
**Closed:** 2026-05-01 ~07:55 ACST (session ran across local-midnight boundary)
**Tool routing:** Claude Chat
**Governing DRs invoked:** DR-029 (active arc, §2.1 Saturday probe brief drafted), DR-027/028 (cross-DB discipline — confirmed not extending; probe is read-only against Betfair API direct, doesn't touch `capture.db` boundary surface), DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-04-30 18:52 ACST`. Anchored 52 min after Session 38 close.

## Pre-flight

Rebuild folder root state matches Session 38 close exactly: 7 canonical .md, dr029/ with scope + 10 artefacts in 2_1_race_data/. No drift.

## What was delivered

`dr029/2_1_race_data/api_probe_brief.md` drafted in two passes (Pass A structural, Pass B wording). Locked at 403 lines / ~28 KB. Saturday-execution-ready.

Brief structure:
- **§1-2** What this is, why the probe (Saturday timing called out as operator preference, not data requirement).
- **§3** Five questions the probe answers — `actual_sp` write-back behaviour, cross-code parity, field deltas vs current writer, 1s cadence of meaningful change, identity alignment between Betfair and Racing API.
- **§4** Probe scope in seven sub-sections — markets (4 sequential, AU metros prioritised), time window (T-60 → CLOSED+45), cadence (1/sec per race), projection request shape (combined call + EX_LADDER fallback), rate-limit guard-rails, sequential not parallel, parallel Racing API capture stream at 30s cadence.
- **§5** Hard limits — 10 isolation rules, including read-only API, no analytical-line edits, dirty-tree honoured, dedicated output directory.
- **§6** Output structure — Betfair JSONL per race, Racing API JSONL per race, manifest with `api_events` log, analytical report (~250-450 lines target).
- **§7** Execution sequence with parallel sub-loops + adaptation latitude.
- **§8-12** Pre-reads, success/failure criteria, discipline notes, forward routing.

## Mid-session pivots (operator-driven)

Three substantive shape changes during the session, each driven by operator challenging the draft:

**Pivot 1 — Saturday timing reframed.** First-cut brief overweighted Saturday-as-data-requirement. Operator pulled back: Betfair's API serves the same field structure regardless of meeting tier, the BSP/SP write-back behaviour is API-internal, and Saturday only marginally helps question 4 (cadence of meaningful change benefits from real liquidity). Operator chose to keep Saturday as the run day for operator-preference reasons, not data reasons. Brief reframed accordingly across §1, §2.

**Pivot 2 — combined call replaces projection rotation.** First-cut had 12-projection cyclic rotation through the run. Operator pushed for greedy capture given this is a one-off probe. Locked: single combined call per second carrying every supported `priceProjection`. Same API load (1 call/sec), every field every second. `EX_LADDER` fallback path specified for the realistic `TOO_MUCH_DATA` risk: drop from combined call, capture every 10s as supplementary single-projection call.

**Pivot 3 — Racing API parallel capture stream added.** First-cut was Betfair-only. Operator surfaced the cross-source join question and noted Racing API ships with bundled Sportsbet and Ladbrokes odds normalised against Racing API's own runner identity. Locked: parallel Racing API capture stream at 30s cadence per race, full responses captured, failure-isolated from Betfair stream. Resolves three retail surfaces (Racing API native + Sportsbet via Racing API + Ladbrokes via Racing API) at once. Q5 added to the questions list, §3.5 added to the report structure, §4.7 added to probe scope, §6 schemas updated, §7 execution sequence updated to two parallel sub-loops per race.

## Operator framing reinforced

Plain-language operational/gambling-framed framing held throughout. Short responses, baby-steps section-by-section walkthrough through the brief review (§1 through §12, single section per round). Operator confirmed this rhythm worked well — load-bearing for the §11 discipline note in the brief itself ("no mid-probe operator escalation").

## Standing-instruction adherence check

- DR-021 timestamp anchor — clean (18:52 ACST).
- Required reads completed in order — clean.
- Pre-flight directory listing before substantive work — clean.
- DR-027 / DR-028 / DR-029 named in orientation — clean.
- Desktop Commander / projects-filesystem routing for rebuild folder, no bash sandbox attempts — clean.
- write-script-to-/tmp + start_process discipline — n/a this session (no Python REPL needed).
- Operational/analytical line discipline — clean (probe is operational-read-only, doesn't touch capture.db boundary).

## Open items

**No new open items.** The brief itself is the deliverable. Session 39 closes with the brief locked and Saturday-ready.

**Carrying forward unchanged from Session 38:** WIP §16 (VPS in-flight work + metadata-backfill log-permission residual), §13 (§2.10 carry — substantially fed by probe report §3.3).

## Session close state

- Rebuild folder root: 7 canonical .md, dr029/ with scope + 11 artefacts in 2_1_race_data/ (api_probe_brief.md added).
- WIP needs Session 39 close addendum (§17 reflects locked details, opening Session 39 markers cleared, Session 40 markers seeded).
- Saturday probe execution: operator opens Code session ~10:00–10:30 ACST 2026-05-02; pre-reads listed in brief §8; output lands at `dr029/2_1_race_data/api_probe_data/` (raw streams) and `api_probe_report.md` (analytical).

## Forward to Session 40

Session 40 opens after Saturday's probe completes — earliest 2026-05-02 evening ACST, more likely Sunday or following weekday. Primary read: `api_probe_report.md`. Deliverables: triage probe findings; draft Fix 4 brief if probe data is clear; commission follow-up probe if open questions remain; sequence Fix 5 brief and §2.10 work item.

Opening prompt for Session 40 generated alongside this record per standing instruction.
