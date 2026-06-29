# Session 76

**Title:** §2.10 (external analytics environmental scan inventory) brief drafted and locked end-to-end. Six sections written: §1 framing, §2 Betfair API field inventory, §3 Racing API field inventory, §4 combined disposition table, §5 forward-routing and carry-forward items, §6 what §2.10 closes. Brief at 957 lines. Eleven bucket-1 capture fields locked (9 Betfair + 2 Racing API), one routing-deferred Cluster C (breeding/connections/course analysis), five bucket-2 parked items with explicit re-evaluation triggers, plus the SP-pool composition pair (`backStakeTaken`/`layLiabilityTaken`) re-tiered from lower-value to high-value mid-session as Strategy 2 lead-indicator substrate after operator framing input. §2.10 closes the last unwritten DR-029 in-scope deliverable; DR-029 critical path now runs through contract documentation files drafting and close-out governance paragraph drafting before v3 build proper begins. Session 77 forward routing: contract documentation files drafting (`vps_client_contract.md` + `betfair_client_contract.md`) per §2.7 §5.4.
**Opened:** 2026-05-04 12:53 ACST
**Closed:** 2026-05-04 14:08 ACST
**Wall-clock:** ~75 min substantive single sitting. Same-workday open relative to Session 75's 12:34 ACST close (~19 minute gap).
**Tool routing:** Claude Chat. No Code routing. One web_fetch (Betfair Confluence Betting Type Definitions page for `bspReconciled` / `version` / `totalAvailable` canonical definitions). One Racing API openapi.json scan via Desktop Commander start_process for harness/greyhound endpoint coverage check.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 12:53 ACST`.
Close: same command → `2026-05-04 14:08 ACST`.

Same-workday open relative to Session 75's 12:34 ACST close. ~19 minute gap. Single sitting, immediate continuation. ~75 min wall-clock — moderate session, well under split-trigger thresholds.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_76_opening_prompt.md` only (Session 75 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 12:34 ACST` matched Session 75 close; `sessions/SESSION_75.md` present (258 lines); `v3_build_picture.md` last-updated `2026-05-04 12:34 ACST` matched Session 75's stream-state updates (§2.7 → done, §2.10 → in flight).
- Same-workday recap delivered (tight: Session 75 closed §2.7 brief end-to-end; Session 76 picks up §2.10 external analytics scan inventory writeup per Session 75 forward routing).
- V3 build picture: rendered at open since stream state moved at Session 75 close.
- Open-items delta: skipped silently (no movement in 19 min since Session 75 close).

## Session shape

Session 76 was a **brief-drafting session** — drafting §2.10 (external analytics environmental scan inventory) from scratch per Session 75 forward routing. Six sections landed across six drafting rounds (one round per section). The session's tempo was moderate (~75 min) — slightly longer than Session 75's §2.7 (~38 min) reflecting §2.10's more substantive empirical-substrate work (probe report integration, OpenAPI spec scan for harness/greyhound coverage, per-field disposition reasoning) but materially shorter than Sessions 73/74 (~87/~93 min) for design-from-first-principles work.

Two strategic framing decisions locked at session open shaped the drafting:

**Three-bucket capture-cheap classification (capture / park / already-covered) without a fourth cadence-conditional bucket.** Operator confirmed: keep §2.10 strictly capture/park/no-action; cadence is Fix 4's job. Cleaner separation between what §2.10 owns (field inventory + disposition) and what Fix 4 owns (cadence design). §4.3 cadence-dependence callout preserves the right cross-reference without tangling the two streams.

**Cluster C routing-deferred disposition.** Operator confirmed Option C (capture-routing-deferred) for Racing API breeding/connections/course-analysis surfaces — log availability without prejudging routing between `capture.db` (joint operational/analytical use) and `bethub-analytical/` (on-demand pulls). Routing decision deferred to whichever analytical project activates first against concrete deep-market-analysis requirement.

Round-by-round shape:

**Round 1 (open + §2.10 framing).** Operator confirmed a high-level framing of §2.10. API probe report pulled and analysed; eight-to-ten Betfair API capture candidates surfaced from probe report §3.3; Racing API thoroughbred-only structural product limit surfaced from probe report §3.5; cadence segmentation parked correctly to Fix 4; Racing API value assessment parked correctly to post-DR-029. Six-section structure proposed and confirmed. Strategic question on three-bucket vs four-bucket classification resolved (three-bucket; cadence is Fix 4's job).

**Round 2 (§1 framing drafted, written).** §1 written first (5 sub-sections, ~115 lines). What §2.10 is (per-field disposition list across two source APIs in three buckets), what §2.10 is not (no cadence, no analytics, no vendor value), the racing-only constraint (thoroughbred + harness + greyhound captured to capture.db; Racing API thoroughbred-only by product design), what feeds (probe report, openapi.json, current writer column set), what produces (bucket-1 list, bucket-2 list, forward-routing inputs).

**Round 3 (§2 Betfair API field inventory drafted).** Round walked through field-by-field with operator providing real-time framing input on multiple fields:
- `actualSP` clarified as same field as BSP (not two separate captures).
- `removalDate` — operator surfaced soft-book-bet-vs-Betfair-scratch edge case; resolution via existing burst-review workflow per architecture.md §D12 (Betfair as canonical runner identity).
- `adjustmentFactor` — operator confirmation on rule-same-but-numbers-can-drift framing.
- `inplay` — operator confirmation as direct UI value (race-jumped marker).
- `betDelay` — operator surfaced AU regulation context (call-in requirement prohibits live online betting); capture justified on cheap + v3.1+ PASSIVE bet-delay model historical signal.
- `version` — canonical definition retrieved (state-change signal, not tick-level skip-write).
- `totalAvailable` — operator confirmation on unmatched-liquidity reading.
- `backStakeTaken`/`layLiabilityTaken` — operator confirmed and surfaced strategic v3 UI candidate (where-the-price-is-going indicator); pair re-tiered to **high-value** mid-section after operator framing that lead-indicator price-direction signals carry direct Strategy 2 (Price Booster) profit-line value.
- `EX_LADDER` — operator confirmed park; agreed on operator-side Betfair contact action.
- `ex.tradedVolume` — operator surfaced same Betfair contact action; parked Fix-4-dependent.
- `bspReconciled` — operator chose Option A (canonical definition check); definition retrieved confirmed flag is mis-named relative to observable behaviour; park stands.

**Round 4 (§2 BSP-projection-pair clarification).** Operator surfaced memory of a Betfair-API "predicted SP" data point — clarified as `sp.nearPrice`/`sp.farPrice` (already captured per Fix 3, bucket-3). Operator confirmed dual-use forward-routing flags: operational use (headline farPrice projection on race/sports pages plus SP-pool interrogation panel) and analytical use (Option B — SP-projection accuracy study post-DR-029).

**Round 5 (§3 Racing API field inventory drafted).** §3 drafted with Cluster A (result enrichment — `winning_time_hundredths` + confirmed off-time, bucket-1), Cluster B (bundled-bookmaker breadth — operator confirmed flagged-but-not-parked, future operational soft-book DR substrate), Cluster C (breeding/connections/course analysis — Option C confirmed, capture-routing-deferred), §3.3 harness/greyhound structural park.

**Round 6 (§4 combined disposition table drafted).** Tier labels confirmed (high-value / lower-value / result-enrichment / capture-routing-deferred). Mid-round operator framing input — SP-pool composition pair re-tiered from lower-value to high-value as Strategy 2 lead-indicator substrate. §4.4 counts updated (7 high-value Betfair + 2 lower-value Betfair).

**Round 7 (§5 forward-routing and §6 closure drafted).** Six handoffs in §5 across three time horizons (Fix 4 / v3 build-proper / post-DR-029). §6 closes the brief end-to-end with what locks, what unblocks, what doesn't unblock.

**Round 8 (close confirmation).** Operator: "Yes, please close it up and prepare for next session." Forward routing for Session 77 confirmed by §6.2 sequencing — contract documentation files drafting per §2.7 §5.4.

## What was delivered

### 1. §2.10 brief drafted and locked end-to-end

Brief at `dr029/2_10_external_analytics_scan/2_10_external_analytics_scan.md`. 957 lines. Six sections, all locked.

**§1 Framing** (~115 lines, 5 sub-sections). What §2.10 is (per-field disposition across two source APIs in three buckets — capture / park / already-covered); what §2.10 is not (no cadence specification, no analytics design, no vendor-value assessment, no sports analytical capability); racing-only constraint per principle 1.3; thoroughbred-only Racing API as structural product limit (not gap); three named feeds (probe report, openapi.json, current writer column set); three named outputs (bucket-1 list, bucket-2 list, forward-routing matrix).

**§2 Betfair API field inventory** (~280 lines, 8 sub-sections). Inventory baseline against current snapshot-writer column set; high-value capture candidates (`sp.actualSP` = BSP, `removalDate`, `adjustmentFactor`, `inplay`, `betDelay`, plus the SP-pool composition pair `backStakeTaken`/`layLiabilityTaken` re-tiered to high-value mid-session as Strategy 2 lead-indicator substrate); lower-value but cheap candidates (`version` re-framed against canonical definition as state-change signal not tick-level skip-write, `totalAvailable`); three parked items with rationale (`EX_LADDER` credential gap, `ex.tradedVolume` extra-projection cost, `bspReconciled` mis-named no-consumer-identified); already-covered surfaces with `nearPrice`/`farPrice` dual-use UI + analytical flags.

**§3 Racing API field inventory** (~175 lines, 5 sub-sections). Inventory baseline against current orchestrator code path; Cluster A result enrichment (`winning_time_hundredths` + confirmed off-time, bucket-1); Cluster B bundled-bookmaker breadth flagged forward to future operational soft-book DR; Cluster C breeding/connections/course-analysis capture-routing-deferred (Option C); §3.3 harness/greyhound structural park (zero Racing API endpoints by product design); already-covered surfaces (meets-and-races thoroughbred path + bundled two-bookmaker odds).

**§4 Combined disposition table** (~110 lines, 4 sub-sections). Bucket-1 capture list combined across both APIs (11 fields + 1 routing-deferred cluster); bucket-2 park list with explicit parking rationale and re-evaluation triggers per item; cadence-dependence callout (capture-cheapness judged at orchestrator's current cadence; one explicit Fix-4-dependent re-evaluation trigger for `ex.tradedVolume`); combined-table summary with tier breakdowns (7 Betfair high-value + 2 lower-value + 2 Racing API result-enrichment + 1 routing-deferred cluster).

**§5 Forward-routing and carry-forward items** (~155 lines, 6 sub-sections). Six handoffs across three time horizons: Fix 4 cadence brief substrate (CLOSED-stop marker, INTENSIVE-tier segmentation candidates, greyhound POST_START code-specific cadence, `ex.tradedVolume` re-evaluation trigger); v3 build-proper UI candidates (headline `farPrice` projection on race/sports pages, SP-pool interrogation panel using `backStakeTaken`/`layLiabilityTaken`, race-jumped UI marker via authoritative `inplay`); post-DR-029 analytical capability candidates (Betfair SP-projection accuracy study, racing EV model recalibration with bucket-1 captures); post-DR-029 strategic decisions (Racing API value assessment with thoroughbred-only scope clarified, full-ladder credential upgrade question, future operational soft-book DR with bundled-bookmaker breadth substrate, Cluster C routing decision); operator-side parallel actions (Betfair contact for `EX_LADDER` and `EX_TRADED_VOLUME`); DR-029 close-out governance contribution (bucket-2 re-evaluation trigger discipline).

**§6 What §2.10 closes** (~115 lines, 4 sub-sections). What §2.10 locks (bucket-1 list + bucket-2 park list + bucket-3 surfaces + forward-routing matrix + bucket-2 re-evaluation trigger discipline); what §2.10 unblocks (DR-029 critical path now reduces to two items: contract documentation files + close-out governance paragraph); what §2.10 does not unblock (v3 build proper still gated, Fix 4 still waits, operational soft-book layer still deferred, sports analytical capability still asymmetric per principle 1.3, analytics layer formalisation still deferred, burst-review triage workflow still downstream, four post-DR-029 strategic decisions still need their triggers); brief close.

### 2. Strategic decisions locked

Approximately twelve strategic decisions confirmed by operator across the drafting:

1. **Three-bucket classification (capture / park / already-covered)** rather than four-bucket cadence-conditional.
2. **§2.10 strictly capture/park/no-action; cadence is Fix 4's job.** Clean separation.
3. **Racing API value assessment as post-DR-029 follow-on**, not §2.10 deliverable.
4. **CLOSED-stop marker** for Fix 4 substrate (operator-flagged); not §2.10 specification.
5. **Soft-book-bet-vs-Betfair-scratch edge case** handled by existing burst-review workflow per architecture.md §D12; `removalDate` capture provides authoritative timestamp for triage.
6. **`betDelay` capture justified** despite AU live-betting regulation gating operational use — cheap + historical signal substrate for v3.1+ PASSIVE bet-delay model handling.
7. **`bspReconciled` parked low-value** after canonical definition check confirmed flag is mis-named relative to observable behaviour.
8. **`sp.nearPrice`/`sp.farPrice` dual-use** — operational (headline projection + SP-pool interrogation panel) plus analytical (SP-projection accuracy study, Option B post-DR-029).
9. **Cluster C capture-routing-deferred** (Option C) — log availability, defer routing decision to whichever analytical project activates first against concrete deep-market-analysis requirement.
10. **Bundled-bookmaker breadth flagged-but-not-parked** as future operational soft-book DR substrate; not §2.10 capture decision.
11. **Tier labels in §4.1** (high-value / lower-value / result-enrichment / capture-routing-deferred) preserve §2/§3 framing context without imposing artificial cross-API numeric ordering.
12. **SP-pool composition pair (`backStakeTaken`/`layLiabilityTaken`) re-tiered to high-value** mid-§4 drafting after operator framing that lead-indicator price-direction signals carry direct Strategy 2 (Price Booster) profit-line value.

### 3. §2.10 brief now load-bearing input for DR-029 close

§2.10's bucket-2 re-evaluation trigger discipline is named in the DR-029 close-out governance paragraph as a standing piece alongside the three pieces of v3-carried debt, periodic data-fitness re-verification, operational/analytical line discipline, and §2.7's API contract versioning discipline. Survives DR-029 close into v3 build proper as one of the standing disciplines.

### 4. Working-style adherence

Memory edit #16 stance applied throughout per Session 75's pattern. Each round surfaced one to two strategic questions for operator decision; technical detail (sub-section structure, sub-section content, per-field disposition logic, three-bucket framing, tier labels, forward-routing organisation) handled inside the artefact rather than surfaced for operator review. Operator's framing inputs (mid-§2 SP-pool re-tier, AU regulation context for `betDelay`, soft-book-vs-Betfair-scratch edge case, BSP-projection-pair value memory, Cluster C and bundled-bookmaker future-state framing) integrated mid-drafting without breaking section cadence — pattern of operator surfacing strategic context that sharpens framing rather than redirecting scope.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (tight, ~19 minute gap from Session 75 close).
- **Cat 1 (V3 build picture conditional render)** — rendered at open since stream state moved at Session 75 close (§2.7 → done, §2.10 → in flight). To be updated at this close (§2.10 stream moves from `in flight` to `done`; §2.7 carry-rule one-session post-close drops; new "contract documentation files" stream surfaces as `in flight` for Session 77).
- **Cat 1 (open-items delta)** — skipped silently at open (no movement in 19 min). Will fire at next session open if movement.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Round-by-round cadence with one to two strategic questions per round. No paragraph-stacking.
- **Cat 1 (decision-maker framing)** — held. Each round led with the call or recommendation. Strategic questions explicitly framed as operator decisions with Claude's recommendation flagged for confirmation/pushback.
- **Cat 1 (don't drift to alternatives when operator clear)** — held.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders. `vps_client`, `betfair_client`, `capture.db`, `betfair_market_id`, `betfair_selection_id`, `actualSP`, `bspReconciled`, `nearPrice`, `farPrice`, `backStakeTaken`, `layLiabilityTaken`, `EX_LADDER`, `EX_TRADED_VOLUME`, `INTENSIVE`, `STANDARD`, `POST_START`, `SUSPENDED`, `CLOSED` unwound on use.
- **Cat 1 (escalate to detail only when warranted)** — held. Operator's framing inputs (BSP-projection-pair value memory, AU regulation context for `betDelay`) answered with precision-level detail without escalating beyond immediate scope.
- **Cat 1 (line-break rendering for review content)** — held. All §2.10 brief draft sections delivered in fenced markdown rendering inside the canonical artefact rather than chat preview blocks.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. No mid-session re-anchor needed; single sitting under 90 minutes.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held. Initial `mkdir` for `2_10_external_analytics_scan/` directory and OpenAPI spec scan via `Desktop Commander:start_process`. The bash_tool call attempted at the start of the openapi.json scan failed (correctly per Cat 3 — not functional in this environment); routed correctly through Desktop Commander on retry.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python REPL work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; all §2.10 draft content written directly to canonical artefact during the session. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — n/a; no structural drift this session. The §2 mid-section SP-pool tier upgrade was a tier label change within a section, not a structural change to the artefact's section layout. The change is captured in §4.1 cleanly.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — engaged. Betfair Confluence Betting Type Definitions page fetched via `web_fetch` for `bspReconciled`, `version`, `totalAvailable` canonical definitions (resolved §2.6 `bspReconciled` parking decision and refined §2.3 `version` framing to state-change signal). Racing API openapi.json scan via `jq` over Desktop Commander start_process for harness/greyhound endpoint coverage check (resolved §3.3 structural park framing).
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — n/a; all writes were single-target appends to the §2.10 brief.
- **Cat 3 (write-file vs create_file namespace gotcha)** — n/a; all writes via `Desktop Commander:write_file` directly.
- **Cat 4 (DR-027/028 invoked)** — named at open. DR-028 load-bearing for §1.1's three-bucket framing rationale (the contract is the integration boundary; §2.10 inventories what flows across it, not what happens inside the boundary). DR-027 anchoring the operational/analytical line separation throughout (Betfair API direct surfaces operational, Racing API surfaces analytical).
- **Cat 4 (operational/analytical line discipline)** — engaged throughout. §2 framed as Betfair API which serves both operational (`betfair_client` direct) and analytical (capture.db merged); §3 framed as Racing API which is purely analytical-line-only into capture.db.
- **Cat 4 (Betfair-as-canonical-source extension)** — load-bearing this session for the soft-book-bet-vs-Betfair-scratch edge case resolution per architecture.md §D12. Reaffirmed throughout §2 (Betfair identifiers as canonical join keys for runner identity).
- **Cat 5 (software questions are Claude's)** — held cleanly. Section structure, sub-section design, three-bucket framing logic, per-field disposition reasoning, tier label choice, forward-routing organisation — all Claude's calls (proposed for confirmation). Operator's strategic decisions (three-bucket vs four-bucket; Cluster C routing-deferred; SP-pool tier upgrade; bundled-bookmaker flagged-not-parked) involved scope and execution choices Claude proposed but operator confirmed. Cat 5 line held cleanly.
- **Cat 5 (operator working-style — memory edit #16)** — held throughout. Strategic questions one to two per round; technical detail in the artefact. Operator's framing inputs (memory of Betfair "predicted SP" data point clarified to `nearPrice`/`farPrice`; AU regulation context for `betDelay`; soft-book-vs-Betfair-scratch edge case; SP-pool re-tier as Strategy 2 lead-indicator) integrated mid-drafting as precision-shaped contributions rather than reframes.

## Open items in (carried forward + new)

New from Session 76:

- **§2.10 external analytics scan brief end-to-end** — **CLOSED Session 76.** All 6 sections locked. Brief at `dr029/2_10_external_analytics_scan/2_10_external_analytics_scan.md` (957 lines).
- **Betfair contact re: `EX_LADDER` entitlement and pricing** — operator-side parallel action. Not gating any DR-029 deliverable. Logged Session 76 §5.5; informs §5.4 full-ladder credential upgrade decision.
- **Betfair contact re: `EX_TRADED_VOLUME` projection cost and entitlement** — operator-side parallel action. Not gating; informs Fix 4 cadence-design substrate (§5.1) if purely payload-cost, treats analogously to `EX_LADDER` if entitlement-gated.
- **Bucket-2 re-evaluation trigger discipline** — substrate for DR-029 close-out governance paragraph. Each parked item carries an explicit re-evaluation trigger per §4.2 + §5.4.
- **Cluster C capture-routing decision** — deferred to whichever analytical project activates first against concrete deep-market-analysis requirement. Trigger: a strategy or analytical project surfaces concrete requirement for breeding/connections/course-analysis features.

Carry-forward (unchanged structure where applicable):

- **§2.6 settlement model — race path** — CLOSED Session 74.
- **§2.7 API contract versioning** — **CLOSED Session 75.** Carry post-close window expires this close.
- **§2.8 bet-schema reframing** — CLOSED Session 72.
- **§2.9 write-side bet-entry coherence** — CLOSED Session 73.
- **§2.10 external analytics scan** — **CLOSED Session 76.**
- **`vps_client_contract.md` documentation file** — required artefact before v3 build proper. Drafted as separate post-§2.7 artefact. **Session 77 primary candidate.** Likely Code-bound brief shape for developer-readable formal spec section against §2.6 / §2.9 locked shapes; operator-readable summary in Chat. **Part of DR-029 critical path.**
- **`betfair_client_contract.md` documentation file** — same shape as above. **Part of DR-029 critical path; pairs with `vps_client_contract.md` for Session 77 / 78 work.**
- **Post-DR-029-close contract documentation relocation** — both files move from `dr029/2_7_api_contract_versioning/` to permanent v3 location (likely `contracts/` folder at v3 project root) as part of DR-029 close-out documentation pass.
- **DR-029 close-out governance paragraph drafting** — covers three pieces of v3-carried debt, periodic data-fitness re-verification, operational/analytical line discipline, §2.7 versioning discipline, §2.10 bucket-2 re-evaluation trigger discipline. Substrate in place; drafting work consolidates framing. **Final DR-029 critical-path item before v3 build proper begins.**
- **90-day deprecation window revisit** — provisional v1.0 default; revisit triggered on first observed migration friction.
- **Auth flow implementation specification** — `betfair_client` v1.0 names auth handling as inside the boundary but does not specify flow shape. Lands inside `betfair_client_contract.md` developer-readable section.
- **Rate-limit budget allocation tuning** — `betfair_client` v1.0 implementation discipline; v3 build proper operational parameter tuning.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records. Reaffirmed throughout §2.10 (Betfair identifiers as canonical join keys; soft-book-vs-Betfair-scratch edge case resolution per architecture.md §D12). Continues as administrative cleanup post-DR-029.
- **Sports-side dead-heat capture in `architecture.md` §B.1.4** — administrative cleanup carry-forward (Session 74).
- **Past-settlement-window threshold calibration** — v3 operational parameter (30 minutes from race finish for v3 day-one); calibrate from operational experience.
- **Settlement worker periodic verification cadence** — v3 build proper operational tuning for §2.6 §3.4 condition 2.
- **Cluster 1 surgical-fix carry-in (analytical-layer prep)** — `runners.finish_position` backfill + `racing-metadata-backfill.service` rework. Non-gating analytical-layer prep work.
- **Complete cascade map** — parked. Best done post-DR-029.
- **CLV as analytical-layer signal** — built post-DR-029.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — operational design downstream.
- **`marketTime` mutability empirical question** — folded into Fix 4 cadence brief drafting per §2.9 §3.5.
- **§2.9 §4.4 six edge cases** — documented for burst-review reference, no mitigation built.
- **Fix 4 (Racing API and Betfair Streaming cadence design)** — non-gating quality work. Includes `marketTime` mutability empirical question + §2.10's CLOSED-stop marker substrate, INTENSIVE-tier segmentation candidates, greyhound POST_START code-specific cadence, `ex.tradedVolume` re-evaluation trigger.
- **Fix 5 (venue harmonisation)** — non-gating.
- **Fix 9 (Racing API re-fetch)** — non-gating.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — non-gating.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — Fix 8 report §8.5 recommendation.
- **Session numbering slip in probe brief** — cosmetic.
- **EX_LADDER entitlement question** — operator-side homework; **now also formally substrate for §5.4 post-DR-029 strategic decision** plus operator-side Betfair contact action (§5.5).
- **Drift-check methodology gap** — substrate from Session 64 carry-forward.
- **`bethub-analytical` project awaiting activation** — operator decision pending. **Now also substrate for §5.4 Cluster C routing decision** when activation surfaces concrete deep-market-analysis requirement.
- **Post-DR-029 monitoring layer (smaller scope)** — parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — non-gating.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — substrate input for analytical scan, **now resolved via §2.10 inventory**.
- **BetWatch contacted re: API service and book coverage** — awaiting response. No longer gating per Session 69. **Now also substrate for §5.4 future operational soft-book DR.**
- **Betfair API membership tiers — investigate.** Operator-side homework. **Now connects to §5.4 + §5.5 actions.**
- **PASSIVE bet-delay model handling** — flagged in §2.4 §15.4 as v3.1+ capability. **Now has explicit historical signal substrate via §2.10 bucket-1 `betDelay` capture.**
- **Three pieces of named debt being carried into v3 build** — substrate for DR-029 close-out governance paragraph.
- **Racing API value assessment** — post-DR-029 strategic decision per §5.4. Substrate: §3 inventory + thoroughbred-only scope clarified.
- **Future operational soft-book DR (post-DR-029)** — bundled-bookmaker breadth substrate from §3.2 + BetWatch response when received.
- **v3 build-proper UI candidates** — three surfaces logged §5.2 (headline `farPrice` projection, SP-pool interrogation panel, race-jumped UI marker).
- **Betfair SP-projection accuracy study** — post-DR-029 analytical capability candidate per §5.3. Substrate-already-present once `actualSP` capture lands.
- **Racing EV model recalibration with §2.10 bucket-1 captures** — post-DR-029 analytical work for `bethub-analytical/racing_ev_calibration/` activation.

Gaps from earlier reviews logged for awareness:

- **Claude-67 G1** — AU-specific session expiry not on disk.
- **Claude-67 G2** — `listCurrencyRates` API surface silent in captured reference.
- **Claude-67 G3** — Racing API ↔ Betfair market identity reconciliation implicit.
- **Claude-67 G4** — `listCurrentOrders` filter parameter list not in captured reference.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC` betDelay confidence note. **Partly addressed Session 76 — `betDelay` capture ensures historical signal substrate.**

## Open items out

Closed this session:

- **§2.10 §1 framing** — locked.
- **§2.10 §2 Betfair API field inventory** — locked.
- **§2.10 §3 Racing API field inventory** — locked.
- **§2.10 §4 combined disposition table** — locked.
- **§2.10 §5 forward-routing and carry-forward items** — locked.
- **§2.10 §6 what §2.10 closes** — locked.
- **§2.10 brief end-to-end** — CLOSED Session 76.
- **Three-bucket vs four-bucket classification strategic question** — locked three-bucket; cadence is Fix 4's job.
- **Cluster C routing strategic question** — locked Option C (capture-routing-deferred).
- **Bundled-bookmaker breadth strategic question** — locked flagged-but-not-parked, future operational soft-book DR substrate.
- **§2.10 tier-label scheme strategic question** — locked four-tier (high-value / lower-value / result-enrichment / capture-routing-deferred).
- **SP-pool composition pair tier strategic question** — locked high-value (Strategy 2 lead-indicator substrate; original draft was lower-value, re-tiered after operator framing).
- **`bspReconciled` capture decision** — locked park (canonical definition check confirmed flag is mis-named relative to observable behaviour).
- **`actualSP` vs BSP clarification** — same field, single capture populating existing `bsp_price` orphan column.
- **§2.7 carry-post-close window** — expires this close per `v3_build_picture.md` carry-rule.
- **§2.1 BSP-fix code finding (d) substrate input for analytical scan** — resolved via §2.10 inventory.

## Session close state

- **Rebuild folder root:** 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present. **One new directory created this session:** `dr029/2_10_external_analytics_scan/`.
- **`current_state.md`:** to be updated by close ritual to reflect Session 77 forward routing (contract documentation files drafting).
- **`v3_build_picture.md`:** **to be updated this close.** §2.10 stream moves from `in flight` to `done`. §2.7 (carry-rule one-session post-close from Session 75) drops. New `contract documentation files` stream surfaces as `in flight` for Session 77.
- **`standing_instructions.md`:** unchanged this session. No new instructions surfaced.
- **`dr029/2_10_external_analytics_scan/2_10_external_analytics_scan.md`:** **created this session.** 957 lines. Status: complete. All 6 sections locked.
- **`dr029/dr029_scope.md`:** unchanged this session. §2.10 scope per existing locked text unchanged; §2.10 brief assembled within scope.
- **`architecture.md`:** unchanged this session. Sports-side dead-heat capture amendment to §B.1.4 carry-forward from Session 74 still pending.
- **`decisions.md`:** unchanged this session. No new DRs surfaced.
- **`sessions/`:** Session 76 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 76 opening prompt to be removed at close; Session 77 opening prompt to be written.
- **Project knowledge base:** unchanged; no operator-side actions required for Session 77 open.
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 77 picks up **contract documentation files drafting** (`vps_client_contract.md` + `betfair_client_contract.md`) per §2.7 §5.4. This is the next DR-029 critical-path item before v3 build proper begins; alternative routing would be the close-out governance paragraph drafting (§6.2) which is the second remaining critical-path item.

Reasons contract documentation files first over close-out governance: contract documentation files are required artefacts before v3 build proper begins (per §2.7 §5.4), whereas close-out governance is the consolidation step that depends on having all DR-029 substrate complete (which includes the contract documentation files themselves). Sequencing contract documentation first means close-out governance has all its substrate when it drafts.

**Session 77 primary deliverable: contract documentation files drafting.**

Sequence:

1. **First work:** read `dr029/2_7_api_contract_versioning/2_7_api_contract_versioning.md` (§2.7 brief, the spec source for both contracts); read `dr029/2_6_settlement_model/` for §2.6 §5.1 settlement-read shape; read `dr029/2_9_write_side_coherence/` for §2.9 §6.1 contract surfaces.
2. **Routing decision early:** likely Code-bound brief shape for the developer-readable formal-spec section against §2.6 / §2.9 locked shapes (transcription work, not design-from-first-principles); operator-readable summary in Chat. Confirm shape with operator at session open before drafting either side.
3. **Section-by-section per Cat 1 default cadence** — both files together likely 2-session work (one per file, or one for vps_client_contract + brief drafting plus one for betfair_client_contract + brief drafting + Code routing handoff).

**Alternative routing if operator prefers:** close-out governance paragraph drafting per §6.2. Substrate is in place (§2.7 versioning discipline, §2.10 bucket-2 re-evaluation trigger discipline, three pieces of v3-carried debt, periodic data-fitness re-verification, operational/analytical line discipline). Drafting work is consolidating the framing.

**Out of scope for Session 77:** v3 build proper start (still gated on contract documentation files + close-out governance both landing); Fix 4 cadence brief drafting (post-DR-029-close non-gating); anything outside the chosen primary deliverable.

**Operator-side actions between sessions:**

1. **(Optional, low priority)** Investigate Betfair API membership tiers — informs §5.4 full-ladder credential upgrade decision + §5.5 EX_LADDER contact action.
2. **(Optional)** Awaiting BetWatch response — no longer gating; informs future operational soft-book DR.
3. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.
4. **(New, optional)** Contact Betfair re: `EX_LADDER` entitlement and pricing — informs §5.4.
5. **(New, optional)** Contact Betfair re: `EX_TRADED_VOLUME` projection cost and entitlement — informs Fix 4 cadence-design substrate.
6. **(Optional)** Review §2.10 brief end-to-end at leisure (between-session work; not a Session 77 blocker).
7. **(Optional)** Review §2.7 brief end-to-end at leisure.
8. **(Optional)** Review §2.6 brief end-to-end at leisure.
9. **(Optional)** Review §2.9 brief end-to-end at leisure.
10. **(Optional)** Review §2.8 brief end-to-end at leisure (carry-forward from Session 72).

## Close-out notes

Single sitting, ~75 min wall-clock — moderate session, well-aligned with brief-drafting cadence. The substrate-rich nature of §2.10 (probe report integration, OpenAPI spec scan, per-field disposition reasoning across two source APIs) made the section work somewhat heavier than §2.7's pure wrapper-shape framing (Session 75 ~38 min) but lighter than full design-from-first-principles work (Sessions 73/74 ~87/~93 min).

Three working-style moments worth holding onto:

- **Mid-section tier upgrade with operator framing input.** §2.3 SP-pool composition pair (`backStakeTaken`/`layLiabilityTaken`) was originally drafted as lower-value tier (analytical curiosity behind `farPrice` projection). Operator framing — that lead-indicator price-direction signals translate to direct Strategy 2 (Price Booster) profit-line value — re-tiered the pair to high-value mid-§4 drafting. Pattern: when operator surfaces strategic value framing that Claude's framing missed, the right response is to re-tier and re-frame the specific entries cleanly rather than dilute the whole section's tier scheme. The fix was three line edits: tier label upgrade in §4.1 table; value-summary re-framing as Strategy-2-substrate; §4.4 count update (5 → 7 high-value Betfair fields). Clean, surgical, no scope creep.

- **Canonical definition check resolves multiple parking decisions cleanly.** Operator chose Option A (canonical definition check) for `bspReconciled` mid-§2 drafting. The web_fetch against Betfair Confluence Betting Type Definitions resolved not just `bspReconciled` (definition + observable-behaviour mismatch confirms park decision) but also refined `version` framing (state-change signal not tick-level skip-write — this required walking back my earlier framing to operator about version's role in cadence design) and confirmed `totalAvailable` framing (operator's reading was right — unmatched-liquidity market-wide). Pattern: a single canonical-source check can resolve multiple adjacent framing decisions when the source is authoritative for related fields. The cost was one web_fetch, the benefit was three locked framings.

- **Operator framing memory as precision input.** Operator's surfaced memory of a Betfair-API "predicted SP" data point (Round 4) — initially uncertain whether they were thinking of `backStakeTaken`/`layLiabilityTaken` or something else — clarified to `nearPrice`/`farPrice` (already captured per Fix 3, bucket-3). The clarification reframed the operator-flagged v3 UI candidate (where-the-price-is-going indicator) from "build a composite indicator from raw SP-pool data" to "surface Betfair's own SP projection (`farPrice`) directly plus optional SP-pool interrogation panel for composition." Pattern: when operator surfaces uncertain framing, the right response is to enumerate what fields might match the framing and let the operator confirm — rather than picking one and running. Three candidates enumerated, one selected, cleaner result than guessing.

§2.10 brief is now locked. Session 77 picks up contract documentation files drafting (`vps_client_contract.md` + `betfair_client_contract.md`) as the next DR-029 critical-path item. After that lands, only the DR-029 close-out governance paragraph remains before v3 build proper begins.
