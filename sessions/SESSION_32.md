# Session 32 — DR-029 §2.1 inspection-report triage (continued); rebuild question surfaced

**Open:** 2026-04-30 12:54 ACST
**Close:** 2026-04-30 13:10 ACST
**Duration:** ~16 min
**Shape:** triage of three remaining clusters; rebuild question surfaced mid-session and routed to a source-code review arc; §2.1 held open pending review

## Required reads completed

- `work_in_progress.md` (project state through Session 31)
- `sessions/SESSION_31.md` (triage outcomes for Clusters 6, 5, 3)
- `dr029/2_1_race_data/inspection_report.md` (822 lines, full)
- `dr029/dr029_scope.md` (§2.1 and §5 sequencing)
- `v3_data_requirements.md` §B.2 (especially B.2.4 — three named cadence responses)
- `agent_review/inputs/data_layer_current.md` §§4-5 (schema-defined view)
- Pre-flight directory listing of rebuild folder root — clean (seven canonical .md, expected directories)
</content>

## Triage outcomes — three clusters closed

### Cluster 2 — Betfair cadence (analytical line) → routes to §2.4 + small Code probe
</content>

**Operator-Claude framing drift surfaced and flagged.** First framing of Cluster 2 conflated the operational and analytical lines again — same drift Session 31 corrected mid-Cluster-3. Operator named it directly: when discussing Betfair cadence, name which line first (operational `betfair_client` direct ~1s near jump in v2 today / analytical VPS scrape periodic) before reasoning about impact. Standing watch-item folded into operator-instructions below.

**Findings (analytical line only).** Pre-jump intensive p50 90-97s vs documented 60s. Gap rate 22-39% in intensive window. **56% of AU thoroughbred 30d races have no pre-30min Betfair snapshot of any kind.**

**Operationally framed.** When placing a bet, the price the operator sees is fine — operational line, fast, untouched. Finding is about post-hoc analytical review: bracketing snapshots either side of a logged bet read from the analytical line, and for over half of AU thoroughbred bets they're either missing or spaced loosely. Strategy 1, 2, 4 affected on review/calibration; Strategy 3 not racing-analytical-driven.

**Routing.**
- **Cadence review of the VPS analytical line** — operator decision: not "is documented cadence being hit" but "is documented cadence the right cadence for what the analytical line needs." Routes forward to §2.4 (Betfair Streaming spec / analytical capture cadence) as a carry-in.
- **56% no-pre-30min coverage** — operator decision: not sufficient as it stands. Needs diagnostic to determine root cause (config gap vs measurement artefact vs structural market-discovery gap). Small Claude Code probe commissioned, low-cost, output is a finding not a fix.
- **§2.1 close implication:** §2.1 close now gated on the 56% probe finding returning, plus Cluster 1's rebuild-vs-surgical-fix call.

**Tool routing.** Probe = Claude Code, near-term. Cadence review = future Chat under §2.4.

### Cluster 4 — schema deltas + source-exposes-but-pipeline-doesn't-write → multi-routed

**Findings.** Two shapes bundled. Schema deltas: `data_layer_current.md` §§4-5 names fields not present as named in schema (`race_surface`, `race_code`, `actual_jump_time` on races, result `observed_at`, late_scratch flag, dead-heat flag, sectionals); some derivable, some not. Source-exposes-but-pipeline-doesn't-write: `betfair_snapshots.bsp_price` / `sp_near_price` / `sp_far_price` 0%-populated columns despite Betfair Streaming exposing the values; `betfair_historical` carries fields with no live-capture equivalent (in-play volume, at-off market state, runner-matching diagnostics).

**Operationally framed.** Largely measurement plumbing, not "v3 can't operate." Settlement-relevant lag can't be measured cleanly (no `actual_jump_time`, no first-party `observed_at`) — affects auto-settlement design under §2.6. BSP for live-capture races is absent (60-day window with no BSP from any source) — affects backtest and Harville calibration for Strategy 1 and Strategy 4. Other deltas are nice-to-have analytical fields.

**Routing.**
- Doc-only schema deltas (race surface naming, late-scratch derivability, race code via heuristic) → post-DR-029 documentation pass.
- Real capture gaps with settlement-lag implications (`actual_jump_time`, result `observed_at`) → carry forward as constraints into §2.6.
- BSP / sp_near / sp_far 0%-populated → §2.10 high-value candidate capture-cheap addition (source already exposes, schema columns already exist).
- Other `betfair_historical` fields with no live-capture equivalent → §2.10 lower priority candidates.
- Sectional times, dead-heat flag, stewards' boolean → §2.10 nice-to-haves contingent on clean source paths.

**§2.1 close implication.** Cluster 4 itself does not gate close; all items have clean homes downstream.

**Tool routing.** All routings above are Claude Chat work in their respective downstream sessions. Nothing for Code, nothing more for this session.

### Cluster 1 — result-population + identifier-overlap → architectural; rebuild question surfaced

**Findings.** Zero rows in 421,651 carry both `finish_position` AND `betfair_selection_id`. Two disjoint ingestion paths separated at live-capture-start floor (~60 days back). Pre-floor: Racing API subscription writes `finish_position`, never wrote `betfair_selection_id`. Post-floor: live VPS scraping writes `betfair_selection_id`, result-population pathway hasn't run. Load-bearing twist: **calibration job knows the winners daily** (n_winners, Brier scores, continuous through live-capture window with 4 missed days) — has working result-resolution path that doesn't write back to `runners.finish_position`. System knows who won; isn't writing it where v3 looks.

**Operationally framed.** All four strategies affected when v3 reads results back. v3's `vps_client.get_race_result(event_id)` reads from `runners`, returns nothing for any race in last 60 days. Auto-settlement (Strategy 1 Safety Net) and backtest/Harville (Strategy 4) most affected. Operational live pricing via `betfair_client` direct is unaffected — this isn't "bets won't place," it's "bets won't auto-settle and model can't learn."

**Triage classification.** Architectural insufficiency — discipline failure (two pipelines glued at a join, no overlap on keys downstream consumers need), not a tunable parameter.

**Three candidate routings surfaced.**
1. **Surgical fix** — wire calibration's resolution path back to `runners.finish_position`; expose `daily_calibration_summary` as canonical settlement-result source via `vps_client`; backfill `betfair_selection_id` onto pre-floor runners where tractable. Forward-routed across §2.4 / §2.6 / §2.10.
2. **Reframe remaining DR-029 scope as designing replacement analytical line** — middle ground; uses inspection findings to size the rebuild rather than committing sight-unseen.
3. **Full ground-up rebuild as own arc, separate from DR-029** — DR-029 closes with current state documented as known-insufficient; rebuild arc opens fresh.

### Rebuild question surfaced mid-session

**Operator instinct after Cluster 4 framing.** "Just need to scrap the whole VPS in current form and rebuild from the ground up. Proper thorough review of Betfair API and Racing API and re-look at soft-book scrapers. Use what we've done on current VPS to get a good start. Lot of stuff here, lot of work to get to where it should be — probably cleaner and just as efficient to rebuild."

**Operator-Claude pushback shape.** Pattern across six clusters is consistent (analytical line built incrementally over time, no one held the whole picture). Rebuild instinct well-founded but probably the right *eventual* call rather than the *next* call. Cluster 1 should land first to complete the picture before commit.

**After Cluster 1.** Operator returned the call to Claude: operator can't read the code, relies on Claude to make this call. Honest read from Claude: can't make the call well from `capture.db` schema and queries alone — needs a real source-code review of the VPS analytical pipeline. Specifically the calibration job's result-resolution code, the Betfair scrape's intensive-mode trigger and market-discovery logic, the snapshot writer (for the BSP / sp_near / sp_far question), the soft-book scrapers' shape, and supervision config. That review is bounded, probably a single Claude Code session.

**Routing decision.** Source-code review commissioned via a scope document (Claude Chat, separate session) → Claude Code executes review out-of-session → result feeds the surgical-fix-vs-rebuild call. Three sessions sized: scope document drafting, out-of-session Code review, then triage of review output and the call itself.

**Held open against this routing:** rebuild question itself (parked), Cluster 1's three routings (decision deferred to post-review), §2.1 close (held open, not closed, not failed — pending the review).

## §2.1 close assessment — held open

**Status: §2.1 held open pending source-code review.**

Six clusters complete on triage. Cluster 6 (Session 31), Cluster 5 (Session 31), Cluster 3 (Session 31), Cluster 2 (this session), Cluster 4 (this session), Cluster 1 (this session). Routings logged for all six. **§2.1 does not close yet** because:

- Cluster 2's 56% diagnostic probe needs to return.
- Cluster 1's surgical-fix-vs-rebuild call depends on the source-code review.
- Both feed into how remaining DR-029 scope items (§2.4, §2.5, §2.6, §2.10) get framed — surgical fix means forward-routing as currently scoped; rebuild means reframing or replacing those scope items.

**Sequencing forward:**
- Session 33 = scope document for VPS source-code review (Chat, ~30-45 min).
- Out-of-session = Claude Code executes the review against the bounded brief.
- Session 34 = read review output, make the surgical-fix-vs-rebuild call, decide §2.1 close shape.
- Then DR-029 §2.1 either closes (surgical-fix path) or reshapes the remaining scope (rebuild path).

The 56% probe Cluster 2 commissioned can run in parallel to the source-code review if they don't conflict; or it can be subsumed into the source-code review's questions. Operator-Claude's call when scoping Session 33's brief.

## New standing instruction

**Operational/analytical line discipline — drift watch.** When discussing any Betfair-related cadence finding or capability question, name which line (operational `betfair_client` direct, ~1s near jump in v2 today / analytical VPS scrape, periodic) before reasoning about impact. Without that anchor, framing slides toward conflating them, which Session 31 corrected once and Session 32 corrected again at top of Cluster 2. Pattern of error: reading a cadence number from `capture.db`-side measurement and reasoning about whether it's "tight enough near jump" — that framing only makes sense if same line serves both purposes, which it doesn't. Sit operator-instructions watch-item alongside the existing plain-language framing instruction.

## Tool routing summary

Two Code-session candidates surfaced this session:
- (a) 56% no-pre-30min coverage diagnostic probe (Cluster 2) — small, near-term, but possibly subsumed into (b).
- (b) VPS analytical pipeline source-code review (Cluster 1) — bounded single-session, scope drafted Session 33.

Plus the inherited Code candidates from Session 31 (Cluster 6 tunnel relocation; Cluster 3 harness/greyhound config probe). None gate the source-code review, all subordinate to it.

All scope-progress entries for the six cluster outcomes still TBD — operator's call on format (formal entries in `dr029_scope.md` §5 vs sibling progress log). Deferred to whenever §2.1 actually closes (post-review), since the framing of the entries depends on which routing won out.

## Session shape

Triage-completion with architectural pivot. Six clusters all triaged across Sessions 31 and 32; rebuild question surfaced as candidate routing for Cluster 1; bounded source-code review commissioned to inform the call. §2.1 held open rather than closed-with-known-insufficiency or closed-clean.

Seventh consecutive non-early-close session. Structural shape: triage-complete-with-decision-deferred — distinct from Session 31 (triage-partial-with-handoff), Session 30 (read-and-defer), and Sessions 26-29 (scope-completed-as-load-bearing).
