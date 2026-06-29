# Session 31 — DR-029 §2.1 inspection-report triage (partial)

**Open:** 2026-04-30 11:57 ACST
**Close:** 2026-04-30 12:42 ACST
**Duration:** ~45 min
**Shape:** triage of three of six clusters; remaining three deferred to Session 32 with revised plain-language framing instruction

## Required reads completed

- `work_in_progress.md` (project state through Session 30)
- `dr029/2_1_race_data/inspection_report.md` (822 lines, three chunks)
- Pre-flight directory listing of rebuild folder root — clean (seven canonical .md, expected directories, Session 30 close-out backup retained per immutable session-log principle)

Reference docs not pulled in this session — the three clusters triaged were resolvable from carry-forward in the Session 31 opening prompt. Clusters 2, 1, 4 remaining will want B.2.4, DR-014, DR-027/028, `dr029_scope.md` §2.1, and `data_layer_current.md` §§4-5 read fresh in Session 32.
</content>

## Triage outcomes — three clusters closed

### Cluster 6 — launchd/TCC tunnel observation → routed to WIP §11

**Finding.** The 9-day VPS tunnel outage was script-location-under-`~/Desktop/` triggering macOS TCC sandbox refusal — launchd-spawned bash couldn't read the script under TCC-protected directory. 11,992 retry firings all returned exit code 126. The `KeepAlive=false` setting was a separate, smaller observation (clean-exit reconnects wait 30s for next poll cycle).

**Routing.** Not a §2.1 data fit-for-purpose finding. Operator-side hygiene; goes to WIP §11 reachability arc, tunnel-auto-restart-and-monitoring component (already exists from Session 27, now has substantive root-cause). Two-component fix when actioned: (a) relocate `vps-tunnel.sh` outside TCC-protected directories (e.g. `~/Library/Application Support/bethub/`); (b) consider `KeepAlive=true` for clean-exit reconnect handling.

**Tool routing.** Claude Code session if/when actioned. Not Chat. Not gating DR-029.

### Cluster 5 — NZ pass-through → confirms §3.9, backward-compatible later addition

**Finding.** 464 NZ races present in 12m via Racing API. NZ has 100% race + runner metadata (jockey, trainer, weight, barrier, scratched_at). NZ has 0% Betfair coverage, 0% finish_position, 0% race_class / distance_metres / race_group, 0% BSP. ~69% NZ races have soft-book coverage from 5 of 7 scrapers.

**Decision.** Position (ii) — backward-compatible later addition. Day-one v3 limitation: NZ races visible and bet-loggable, not analytical-pipeline-eligible. v3 contracts written so `vps_client.get_race_result(event_id)` returns "no result available" for NZ event_ids today, and starts returning results the day the capture pipeline populates them. v3.1 milestone candidate (Betfair NZ scrape extension + result write-back + Racing API enrichment).

**Routing.** Confirms `dr029_scope.md` §3.9 empirically. Feeds WIP §7 — Racing API subscription kept (NZ comes through that path). v3.1 milestone planning alongside soft-book vendor scan parking-lot item.

### Cluster 3 — soft-book health and code-coverage → routed predominantly to §2.5

**Finding.** All 7 scrapers alive; cadence uniformly slightly looser than documented (~345s standard / ~145s intensive vs 300s / 90-120s) — fit-for-purpose for §2.1. Three sub-findings underneath:

1. **AU harness/greyhound 99% zero-coverage in pre-30min window** — soft-book scrapers do not capture these codes meaningfully. Inspection didn't diagnose root cause (config gap vs. books not exposing those codes on the URL pattern crawled).
2. **AU thoroughbred 32% zero-coverage** — books skip a lot of meetings; bimodal shape (25% all-7 / 32% none / 43% partial).
3. **PointsBet 0.77 30d/lifetime rate** — lone deviation from the 0.97-1.04 cluster across other six scrapers.

**Architecture clarification surfaced mid-cluster** (operator correction). VPS / `capture.db` is the *analytical* line — periodic, not time-sensitive, captures soft-book + Betfair API + Racing API for backward-looking analysis. Operational live pricing is Betfair API direct via `betfair_client` day-one (load-bearing); soft-book operational live pricing is nice-to-have, not essential — manual entry covers it day-one. Earlier framing in this cluster about Strategy 1 being "structurally a problem" without live soft-book on harness/greyhound was sloppy and corrected: harness/greyhound are operationally fine day-one (manual entry), analytically thin (no backtest data for those codes).

**Routing.**
- Harness/greyhound 99% zero-coverage → §2.5 (soft-book interface contract, source-flexible per Session 27 Position 2). Surfaces as known limitation via operator-visible indicator. Source-flexible filling lands in v3.1 milestone planning. Small Code-session probe of scraper config gap commissioned as low-cost insurance — if it's a config gap, easy fix; if not, locked in.
- AU thoroughbred 32% zero-coverage → same §2.5 with same operator-visible-indicator pattern. Structural-pattern probe (specific venues / times?) is §2.10 candidate sub-question.
- PointsBet 0.77 → folded into Decodo proxy review (WIP §14) as concrete data point. Not its own arc.

**Tool routing.** §2.5 spec note happens in future Chat session. Harness/greyhound config probe is Claude Code. PointsBet/Decodo is operator-side homework. None gate DR-029 §2.1 close.

## Three clusters remaining (Session 32)

- **Cluster 2 (Betfair cadence)** — bounded by `v3_data_requirements.md` B.2.4's three named responses (tune cadence / extend window / accept staleness with operator-visible indicator). Headline: pre-jump intensive p50 ~90-97s vs documented 60s; gap-rate 22-39% in intensive window; 56% of AU-thoroughbred 30d races have NO pre-30min Betfair snapshot of any kind.
- **Cluster 4 (schema deltas + source-exposes-but-pipeline-doesn't-write)** — mostly routes to §2.10 with light §2.1 acknowledgments. `betfair_snapshots.bsp_price`/`sp_near`/`sp_far` 0%-populated columns; multiple `data_layer_current.md` §§4-5 fields not present as named.
- **Cluster 1 (result-population + identifier-overlap)** — architectural. Zero rows in 421,651 carry both `finish_position` AND `betfair_selection_id`. `daily_calibration_summary` produces winners daily but doesn't write back to `runners`. Touches §2.1, §2.4, §2.6, possibly §2.10. Anticipated 30+ min; could expand to its own session.

## New standing instruction surfaced this session

**Plain-language operational/gambling-framed cluster summaries.** Operator is the strategic mind making routing decisions, not the data-detail consumer. Cluster summaries should lead with what's happening in operationally-grounded plain language (real-world racing/gambling vocabulary; what's happening, what's the impact, what are the avenues for remediation), then triage classification, then routing. Avoid dense technical detail in the opening framing — it sits in the inspection report itself if needed. Drift twice this session: once on Cluster 3 architecture split (corrected mid-cluster); once on overall cluster-summary density (corrected post-Cluster 3 with revised punchier version).

This applies to all DR-029 cluster triage going forward and to similar governance discussions where the operator's role is strategic-decision rather than detail-review.

## Tool routing summary for Session 31's outputs

Three Code-session candidates surfaced:
- (a) Cluster 6 tunnel-script relocation + plist update — small, low-priority.
- (b) Cluster 3 harness/greyhound scraper config probe — small, low-priority.
- All §2.5 spec notes and §2.10 sub-questions are Chat work.

None of (a) or (b) gate DR-029 §2.1 close.

## Session shape

Triage-with-revised-framing-instruction. Three clusters closed. Three deferred to Session 32 with the new plain-language standing instruction in force. Estimated context use at close: ~50% — within budget, but the deferral fork was the right call given Cluster 1's anticipated expansion plus the freshly-surfaced framing instruction that wants Session 32's full budget to apply consistently across the remaining clusters.

Sixth consecutive non-early-close session. Structural shape: triage-partial-with-handoff. Distinct from Session 30 (read-and-defer) and from Sessions 26-29 (scope-completed-as-load-bearing).
</content>