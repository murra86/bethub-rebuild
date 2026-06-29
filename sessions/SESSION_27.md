# Session 27 log

**Date:** 2026-04-29 → 2026-04-30 (Adelaide local, ACST — session ran across local-midnight boundary)
**Open:** 16:56 ACST 2026-04-29
**Close:** 07:05 ACST 2026-04-30
**Duration:** ~14h wall-clock with overnight pause; substantive operator-Claude time materially less. First-of-arc DR-029 scoping work; second consecutive non-early-close session (broken streak Session 26, held broken).

---

## Scope going in

Per the Session 26 closing prompt, in order:

1. Strategy-calibration check-in (Finding 2c). Brief discussion at DR-029 scoping open: which of the four racing strategies actually need soft-book operational live pricing on day one. 10–15 minute opener.
2. DR-029 data review scoping. Open with scope recalibration (Finding 11). Frame versioned-not-feature-complete (Finding 7) explicitly. Output a scope document specifying what the data review will and will not address, structured to absorb Findings 2 (Betfair Streaming spec; soft-book direction post vendor-scan), 3 (bet-schema reframing), 4 (sports line-matching), 5 (write-side validation), plus the items already in DR-029's existing scope.
3. Reachability/continuous-fitness scoping placement (Finding 1). Decide: parallel to DR-029, after DR-029, or quick precursor before DR-029 execution.

Backup cleanup at session open: `.close_out_backups/SESSION_26_20260429T164200/` verify recoverable from canonical files, then remove.

## Scope completed

**(1) Strategy-calibration check-in — DELIVERED.** Walked the four racing strategies (Safety Net, Price Booster, Correlated Friction, Synthetic Each-Way) against the question of soft-book operational live pricing day-one need. Initial Claude framing: only Strategy 2 (Price Booster) structurally needs it; Strategies 1, 3, 4 less obvious. Operator pushback: even Safety Net (Strategy 1) is meaningfully degraded without live data because soft books move offered prices to near-zero or sub-zero EV after promo accounting quickly enough that 5-minute-stale data is materially misleading; Strategy 4 sits the same way. Re-rated Strategies 1 and 4 from "tolerable on stale data" to "meaningfully degraded without live." Operator's fallback is manual entry — not "skip the strategy." This made Position (2) the right architectural shape: interface contract on day one, source-flexible.

**(2) DR-029 data review scoping — DELIVERED.** Three substantive operator-driven architectural clarifications during scoping that materially reshaped the multi-agent-review-synthesis-derived starting point:

- **Position (2) locked for soft-book operational data.** Day-one *capability* via interface contract, not day-one *feature* with live source connected. Manual entry as day-one source feeding the `softbook_client` interface; vendor implementation (BetWatch et al per parallel operator-side scan) as backward-compatible v3.1 addition. Vendor scan moves off the DR-029 critical path and onto v3.1 milestone planning.

- **Sports analytical capture in `capture.db` dropped entirely.** Originally framed in `v3_data_requirements.md` §B.3 and treated by the multi-agent review as a settled scope item ("sports market addition"). Operator-surfaced Session 27 that the underlying purpose was weak: rich public archives (AFLTables, Squiggle, Fryzigg, NRL equivalents) obviate prospective capture for the SGM modelling use case; longer time-pressure windows reduce operational data's storage value; sports operational reads go via `betfair_client` direct anyway. Architecture asymmetric by design — racing has analytical store + operational direct; sports has operational direct only.

- **Two-direct-lines-into-Betfair architecture explicit.** Pre-Session-27 implicit model was "v3 reads `capture.db` for race-side, plus direct Betfair for operational." Operator clarified (and Claude had been confusing) that there are two genuinely independent connections to the Betfair API: VPS scrapes Betfair (and Racing API and other feeds) at periodic cadence into `capture.db` (analytical line); v3 itself talks Betfair direct via `betfair_client` for operational/burst-window pricing including bet entry (operational line). Both lines source same Betfair API at different cadences; reconcilable by construction modulo lag. v3's racing page sources from operational direct, not from `capture.db`. Racing API ↔ Betfair merging happens inside `capture.db` (`capture.db`-internal work).

These three clarifications dissolved several of the failure modes Claude had been carrying in the bet-entry-coherence framing. The "operator-vs-soft-book runner divergence" failure mode dissolves under "Betfair is canonical, soft-book is just placement venue." The "race not yet in `capture.db` at bet entry" failure mode dissolves because v3's racing page sources from operational direct, not from `capture.db`. Sports line-matching reframes from architectural-inference problem to capture-completeness-plus-operator-specification — but with capture-completeness no longer in `capture.db` because sports analytical is dropped, instead `betfair_client` queries Betfair direct at bet entry for all market variants.

Scope document `dr029_scope.md` written to rebuild root, 247 lines, 24,696 bytes, SHA256 prefix `da503a65d906de0f`. 10 in-scope items (race-data fit-for-purpose verification 2.1, sports operational layer Betfair-direct 2.2, periodic-only API pattern 2.3, Betfair Streaming spec 2.4, soft-book interface contract 2.5, settlement model 2.6, API contract versioning 2.7, bet-schema reframing 2.8, write-side bet-entry coherence 2.9, external analytics scan 2.10), 10 out-of-scope items (speculative analytics fields 3.1, full analytics layer 3.2, account-isolation 3.3, Cloudflare-blocked books 3.4, vendor selection 3.5, soft-book source connection day-one 3.6, sports analytical capture 3.7, reachability scoping arc 3.8, NZ racing 3.9, burst-review triage workflow design 3.10), 9-step execution sequencing in §5.

**(3) Reachability/continuous-fitness scoping placement — DELIVERED, but with reshape.** Operator-surfaced that the multi-agent review's Recommendation 3 was sized for an architecture where every operational path went through the VPS. Under the post-Session-27 architecture (operational paths direct to Betfair, VPS only on racing auto-settlement plus all analytical reads), the arc is overscoped. Decision: (D) reachability arc dissolved as separate scoping deliverable. Three remaining components distributed:

- Tunnel auto-restart and basic VPS monitoring → operator-side hygiene (parked, not gated on any scoping arc).
- Settlement-lag detection in v3 → part of v3 build's burst-review workflow design, downstream of DR-029.
- Periodic data-fitness re-verification → governance paragraph addition during DR-029 close.

Two residual concerns explicitly named as not-being-lost: silent capture-cadence degradation (lands in periodic re-verification follow-up); burst-review integration of integration-health (lands in v3-build burst-review design).

This is a substantive deviation from the multi-agent review's framing. The synthesis treated reachability and continuous-fitness as one of the cleanest convergence points across all four agents and recommended it as a first-class pre-build deliverable alongside the data review. The Session 27 architectural narrowing (operational paths off the VPS) genuinely changed the picture in a way the multi-agent review couldn't have anticipated because the architectural narrowing wasn't surfaced until Session 27 itself.

## Operator-discoveries / corrections during session

**Operator pushback on strategy-calibration framing (Item 1).** Claude's initial read had Strategies 1 and 4 as "mildly frictional without live"; operator corrected to "meaningfully degraded" because soft-book offered prices move to sub-zero EV quickly after promo accounting. Carried forward as the Position (2) justification.

**Operator pushback on draft 2.10 typo framing (Item 2).** Claude drafted write-side validation with a "typo creating ghost record" failure mode; operator noted v3 doesn't have a typo surface because bet entry is selection-from-known-options against Betfair-sourced data. Reframing carried into 2.10's revised three surfaces: sports line specification, placement-time sanity, identifier-resolution sanity.

**Operator clarification on direct-Betfair sourcing (Item 2).** Claude had been carrying confusion about whether v3's racing page sources from `capture.db` via `vps_client` or from Betfair direct via `betfair_client`. Operator clarified: direct from Betfair via `betfair_client` for operational (including bet entry); `capture.db` is analytical-only. This dissolved failure mode 1 (race not in `capture.db` at bet entry) and is now stated explicitly in `dr029_scope.md` §1.2.

**Operator-surfaced "do we even need sports capture?" (Item 2).** Most consequential single clarification of the session. Originally treated as settled in `v3_data_requirements.md` §B.3 and the multi-agent review. Operator argued: sports analytical needs are smaller (only SGM modelling), commercially-available historical data is rich, time-pressure windows are longer, operational sports needs go via `betfair_client` direct anyway. Decision: drop sports analytical capture entirely, accept architectural asymmetry. Captured in `dr029_scope.md` §1.3 and §3.7.

**Operator-surfaced reachability dissolution (Item 3).** Multi-agent review treated reachability and continuous-fitness as one of the cleanest convergence points; operator surfaced that the architectural narrowing in Session 27 has rendered most of it unnecessary — VPS isn't on operational paths anymore. Three components distributed to existing homes; two residual concerns named not-lost. Captured in `dr029_scope.md` §3.8 and WIP §11 of Session 28 open questions.

## Tools used

- `bash` (TZ command for Adelaide local time anchoring at session open and close).
- Desktop Commander: `read_multiple_files`, `list_directory`, `start_process`, `interact_with_process`, `write_file`, `edit_block` — all rebuild folder operations per filesystem note (bash sandbox cannot reach rebuild folder).
- `tool_search` twice mid-session to load Desktop Commander deferred tools (read_multiple_files set, then start_process set).
- No `ask_user_input_v0` calls this session — three substantive operator-question moments were handled in conversational text rather than tool widget, because each required substantive operator reasoning that buttons would have foreshortened.

## Files touched

**Created:**
- `sessions/SESSION_27.md` (this file).
- `dr029_scope.md` (rebuild root, 247 lines, 24,696 bytes, SHA256 prefix `da503a65d906de0f` post-write).

**Edited:**
- `work_in_progress.md` (Session 27 close update — header date 2026-04-30, Where-we-are section rewrite for Session 27 outcomes including the three substantive architectural clarifications, table row appended for Session 27 plus Session 28 placeholder, Open-questions section rewrite for Session 28 priorities, operator-instructions header updated to Session 28, close-out-fired list appended with Session 27, filesystem-discipline line updated to note `dr029_scope.md` at root and root now holds eight session-relevant `.md` files).

**Backups cleaned at session open:**
- `.close_out_backups/SESSION_26_20260429T164200/` (per Session 27 opening prompt directive; verified backup WIP differs from canonical WIP as expected — pre-Session-26-close vs post-Session-26-close — and the three input documents byte-identical against `agent_review/inputs/` pre-removal).

**Backups created at close:**
- `.close_out_backups/SESSION_27_20260430T070500/` containing pre-close copies of `work_in_progress.md` (SHA256 prefix `2be0afe0817fba45`, 35,021 bytes — Session 26 close state) and `dr029_scope.md` (SHA256 prefix `da503a65d906de0f`, 24,696 bytes — written this session). SESSION_27.md is new, no pre-state to back up.

**Pre-existed and not edited this session (no net change):**
- `v3_data_requirements.md`, `decisions.md`, `governance.md`, `vision.md`, `README.md`, `architecture.md`.
- `agent_review/Judge/` and all assessor outputs and synthesis.
- `agent_review/inputs/` and the three companion documents.
- `orchestration_pack/` and all contents.

## Lessons applied / discipline maintained

- **DR-021:** Adelaide local time anchored at session open (16:56 ACST 2026-04-29) and re-anchored at close (07:05 ACST 2026-04-30). Cross-midnight session noted in log.
- **DR-027 / DR-028 orientation discipline:** named DR-027, DR-028, and DR-029 explicitly in orientation summary at session open per the standing instruction; cited by-number throughout the scoping conversation; all three load-bearing for the scope document `dr029_scope.md` §6 cross-references.
- **Pre-flight directory listing:** ran at session open per standing instruction; surfaced the unchanged state of rebuild folder root plus `agent_review/inputs/` and the single `SESSION_26_20260429T164200/` backup awaiting cleanup.
- **Standing instruction on shorthand:** applied throughout operator-facing conversational text. The four strategies, the four soft-book options A/B/C/D, DR numbers, finding numbers, and recommendation numbers all unwound on use.
- **Silent-close-out-failure mitigation (Session 20 standing instruction):** state-snapshot reads after each Desktop Commander script call; pre-close and post-close state snapshots performed; integrity hashes recorded for all backed-up files and verified post-backup.
- **Open-and-close-out economy directive:** opening prompt for Session 28 to be produced as pointer document below; closing summary omitted; mid-session narration pulled tighter especially across the architecture-clarification turns where operator-pushback meant Claude had to reshape rather than acknowledge-and-continue.
- **Bias toward closing early:** held this session because the scope document delivery *is* the load-bearing work this session was opened to do, and Items 1 and 3 framed naturally around it. Second consecutive non-early-close, broken-streak-now-2.
- **Scripted-promotion pattern (governance.md §3):** four files modified or created (WIP edited, `dr029_scope.md` written, SESSION_27.md created, `.close_out_backups/SESSION_26_…/` removed). Past two-file threshold; scripted-promotion required. All-or-nothing close-out: backup directory created first with hash-verified pre-state, edits done with `edit_block` against verified pre-content, post-state verification at end (in next step).
- **Empirical-question discipline:** all `capture.db` state questions deferred to DR-029 execution session 2.1 rather than asserted from memory or first-pass assumption.
- **Tool-routing recommendation pattern (per userMemories):** Session 28 first-priority recommendation includes explicit tool-routing question (Claude Chat scoping pass first, then Claude Code for inspection) per the standing operator instruction to recommend tool routing on session handoffs.

## Open items going into Session 28

**Session 28 first priority:** DR-029 execution item 2.1 — race-side data fit-for-purpose verification. Empirical inspection of `capture.db` race-data population, cadence, and reliability. Tool-routing decision at session open: brief Claude Chat scoping pass to surface specific empirical questions (median pre-jump cadence in last 5 minutes, 95th percentile, gaps, etc.), then hand to Claude Code with tightly-scoped brief.

**Session 29+ provisional:** continued DR-029 execution. Per `dr029_scope.md` §5 sequencing: 2.4 Betfair Streaming spec, 2.5 soft-book interface contract, 2.2 sports operational direct, 2.8 bet-schema reframing, 2.9 write-side coherence, 2.6 settlement model, 2.3 periodic-only reaffirmation, 2.7 API contract versioning, 2.10 external analytics scan. Best-guess feel: 6–10 sessions for the 9-item sequencing. Each item's session count varies (2.1 may take 1–2 sessions; 2.4 + 2.5 may parallelise; 2.8 has dependencies on 2.4 and 2.5; etc.).

**Operator pre-decision-homework, separate from execution sessions:**
- VPS tunnel restart (immediate hygiene; tunnel down 9+ days; operator-side, not gated; folds with reachability arc tunnel-auto-restart component if hygiene work happens together).
- Soft-book operational vendor scan — BetWatch and alternatives — coverage of AU books, update frequency, cost. Not on DR-029 critical path; informs v3.1 milestone planning. Operator-side homework.

**Reachability arc — three distributed follow-ups (now tracked under WIP §11 of Session 28 open questions):**
- Tunnel auto-restart and basic VPS monitoring → operator-side ops hygiene; possibly Claude Code session.
- Settlement-lag detection in v3 → v3 build's burst-review workflow design, downstream of DR-029.
- Periodic data-fitness re-verification → governance paragraph addition during DR-029 close.
- Two residual concerns named not-lost: silent capture-cadence degradation (lands in periodic re-verification); burst-review integration of integration-health (lands in v3-build burst-review design).

**Parked separately (no change):**
- Operator-Claude context-retention concern from Session 17.
- Tote-pool capture extension (drafted Session 21, reverted; could be revived as future capture.db extension).

## Close-out notes

Close-out script ran clean — backup directory created with pre-close hashes captured and verified; WIP edited with five `edit_block` operations covering header date, Where-we-are rewrite, table row plus Session 28 placeholder, Open-questions section rewrite, operator-instructions section updates (header, close-out-fired list, filesystem-discipline line); `dr029_scope.md` written mid-session via `write_file`; SESSION_27.md created at close. Five files touched (2 created including this log, 1 edited, 1 created scope document, 1 backup directory cleaned at open + 1 backup directory created at close). Post-close state snapshot to verify in next step. Cross-midnight session noted; second consecutive non-early-close session held intentionally.