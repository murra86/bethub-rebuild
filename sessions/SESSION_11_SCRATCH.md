# Session 11 scratch draft — cross-DB integration governance (REVISED v2)

**Drafted:** 2026-04-27 22:18 ACST
**Revised:** 2026-04-28 09:52 ACST (v1 → v2: DR demotion, renumbering, analytics dimension, multi-agent pattern)
**Revised:** 2026-04-28 11:06 ACST (v2 → v3: DR-028 lean structural protections; DR-029 bullet expansions including external analytics scan, periodic-only bet-log architecture with analytical bracketing, settlement model simplification, race results canonical for auto-settlement; multi-agent doc-suite ownership clarified; collaborative drafting parked)
**Status:** SCRATCH. Not promoted. Operator review before any of this lands in `decisions.md`, `sessions/SESSION_05.md`, `sessions/SESSION_07.md`, or `work_in_progress.md`.

This file holds the full set of governance changes from Session 11 around the cross-DB integration with `capture.db` (the existing UK VPS racing-data capture system at `/home/racing/racing-data-capture/data/capture.db`), plus the data-layer-first sequencing decision and the multi-agent governance review pattern.

**Revisions from v2:**
- DR-028 gets four lean structural protections (orientation citation, by-number citation when invoked, log discipline-rot watch, mid-session re-read trigger). Fires only when relevant — minimal orientation-reading overhead.
- DR-029 race-data bullet expanded: race results coverage canonical for v3 auto-settlement.
- DR-029 analytics bullet (bullet 4) reframed as **external environmental scan** — racing AND sports, source-by-source field inventory cross-referenced with analytics literature, time-boxed.
- DR-029 at-bet-placement-time API pattern bullet locked as **periodic-only with analytical bracketing**, reversing earlier hybrid lean. Cadence verification + late-scratching flag handling are data-review items.
- DR-029 settlement-model-simplification bullet added (book canonical for cash; VPS canonical for race result; divergences are reconciliation signals, not algorithmically resolved).
- Multi-agent governance review section: decision_under_review.md authoring updated to operator-Claude collaborative ("Claude asks, operator tells, Claude records") rather than solo operator drafting.
- `work_in_progress.md` parked items: collaborative decision-under-review drafting added for mid-Session-12 or Session-13.

**Final scope (unchanged from v2):**
- 3 new DRs (DR-027, DR-028, DR-029)
- 3 amendments (DR-020, DR-026, Slice 1 in SESSION_05.md, Slice 3 in SESSION_07.md)
- Multiple parked items added to `work_in_progress.md`
- Revised session sequencing (12: reconciliation contract; 13: build strategy; 14: first multi-agent review; 15+: data review scoping → execution → v3 build)
- Multi-agent governance review pattern documented for future use

Read end-to-end. We promote on confirmation, in one clean step.

---

## DR-027 (DRAFT) — Two-database architecture: v3 bet-data and capture.db race-data are separately owned, joined by reference

**One-line justification (DR-bloat watch):** Codifies a structural architectural fact (two databases, strict ownership per fact, integration by reference at read time) that affects every cross-DB integration decision in v3 and which has no natural home as an amendment to any existing DR. Earns its DR.

**Why:** Session 11 surfaced that the existing UK VPS racing-data capture system (`capture.db`, ~30k AU thoroughbred / harness / greyhound races, Betfair time-series snapshots, bookmaker time-series snapshots, BSP historical, calibration summaries) is the canonical source for race-side data and already serves Strategy 1, BetHub v2, the Racing EV model, and AFL Edge. v3 was about to design a `race` entity and duplicate this capture. Duplicating it would have produced two race-data sources drifting from each other — a v2-shaped failure mode at slow cadence.

The architectural fact locked here: **race-side data and bet-side data are owned by different systems, in different databases, joined at read time by stable identifier.** This is the DR-019 "compute on read" discipline extended across a database boundary.

**Locked stance:**

- v3's accounting-layer database (`bethub.db` or whatever the rebuild names it) owns **bet-data**: all entities and events from Slices 1–6 (account, book, ownership_cluster, platform, account_at_book, promo_template, promo, account_arrangement, the single event log carrying bet_placed / bet_correction / bet_settled / hedge_state_classification / cascade events / FB credit and deployment events / friend_payment_made / etc., plus operations log entries).
- `capture.db` (UK VPS, separate infrastructure, separate process) owns **race-data**: races, runners, finish positions, Betfair time-series snapshots, bookmaker time-series snapshots, BSP historical, batch summaries, daily calibration summaries.
- **No fact is owned by both.** No row exists in both databases. No table is written to by both systems.
- v3 references race-data by stable identifier — Betfair `market_id`, the natural key `(race_date, venue_normalised, race_number)`, or `capture.db`'s `race_id`. v3 reads race-side context on demand via the existing read-only data API on the VPS (`racing-api.service`, `127.0.0.1:8400` over SSH tunnel). v3 never writes to `capture.db`. v3 never stores a copy of race-data locally.
- The integration is implemented in a single module (`vps_client` or its v3 equivalent). All v3 access to `capture.db` flows through this one module.

**What this means concretely (the operator-facing shape):**

- When a bet is logged in v3, the bet event payload carries `event_id` (the Betfair market_id) and `bf_market_id` (the same identifier scoped to its source) plus the DR-026 market snapshot. Race classification, distance, surface, finish position, BSP — none of these live on the bet record. They live in `capture.db` and are read on demand when a query needs them.
- When the operator opens a Burst Review of last week's bets and wants to filter by race class or distance, v3 resolves each bet's race identifier through `vps_client` and returns the joined view. The join happens at query time in Python, not in SQL.
- When `capture.db` gets a race-data correction (a Racing API metadata update overnight, a finish-position revision after a stewards' inquiry), v3's next read sees the corrected value automatically. No sync, no cascade, no drift.

**Tradeoffs:**

- v3 is dependent on the VPS being reachable for any read that needs race-side context. Mitigations: the existing liveness-check infrastructure already monitors VPS health; bet-logging-time reads degrade gracefully via the `bf_snapshot_unavailable` flag pattern (DR-026 amendment below) when the VPS is unreachable; analytical-mode queries can tolerate brief unavailability.
- The data API contract becomes load-bearing for v3. If `capture.db`'s schema evolves and the API doesn't, v3 silently gets stale shape. Discipline against this is in DR-028.
- Cross-DB joins in SQL are not possible. Joins happen in Python at the integration boundary. For v3's scale (single user, tens of thousands of bets per year, hundreds of operator queries per day), this is structurally fine.

**Why this is the right pattern, not a v2-style mess:**

v2's coupling problems were caused by stored derived state going out of sync, mixed ownership of the same data within one database, and no clear boundaries. The pattern here is the opposite: strict ownership per fact, no stored derivations of cross-DB data, single integration boundary. The failure modes are *different* from v2's failure modes — contract drift across the boundary rather than ledger drift within the database. DR-028 codifies the discipline that prevents the contract-drift failure mode from compounding.

**Date:** 2026-04-27

---

## DR-028 (DRAFT) — Integration boundary discipline: no caching, no denormalisation, no second integration point

**One-line justification (DR-bloat watch):** Discipline-as-structure DR. The forbidden patterns codified here are what prevents DR-027 from drifting into a v2-shaped mess over time. Discipline that lives only in heads is unstable; structurally-named forbidden patterns are stable. Earns its DR — the discipline rules don't fit as an amendment to DR-027 because they describe *what is forbidden*, not *what is established*.

**Why:** DR-027 is only safe if its discipline holds. Discipline that lives only in the heads of session participants is unstable across years of build sessions, model upgrades, fresh-start sessions, and operator-Claude conversations where shortcuts feel locally reasonable. The protection against discipline rot is structural: name the forbidden patterns, make them visible, require a deliberate DR-write to bend them. This DR is the structure.

**Forbidden patterns:**

1. **No race-data caching in v3.** v3 does not store any race-data fact (race classification, distance, surface, finish position, BSP, runner detail, Betfair time-series snapshot, bookmaker time-series snapshot) in its own database. Reads happen on demand through the integration module. The DR-026 at-log-time market snapshot is the **single, narrow exception** explicitly justified in DR-026 itself by cross-system-durability concerns; no other captures may be added to that exception without a new DR.

2. **No race-data denormalisation onto v3 entities.** v3's `bet`, `bet_settled`, or any other v3 entity does not carry denormalised race fields. The Slice 6 fields `field_size_at_settlement` and `field_size_at_bet_placement` are *not* denormalisations — they are point-in-time captures of race state at specific bet-context moments, captured per the DR-026-extended cheap-capture principle. They survive on the bet record because they are bet-context facts, not race-context facts. If a future schema change proposes adding a v3-side field that duplicates a `capture.db` field, that is a denormalisation and is forbidden under this DR.

3. **No second integration point.** v3 talks to `capture.db` through exactly one module (`vps_client` or its named successor). No raw SQLite reads from `capture.db` in any other v3 module. No second HTTP client. No bypass. Schema drift, contract changes, and integration failures surface in one file, not scattered.

4. **No reflexive extension to additional external data sources.** Adding any third data source (a second VPS service, a third-party API, a new database) is a new architectural decision requiring its own DR. The pattern from DR-027 does not give standing permission to "and we'll add this too." Each new cross-system integration is a deliberate, named, documented architectural step.

**How the discipline is reinforced operationally:**

Four lean structural protections, each fires only when relevant — they do not blow out routine session-orientation reading:

1. **Orientation citation at session open.** When Claude reads `decisions.md` during session orientation and reaches DR-027 / DR-028, Claude names them explicitly in the orientation summary as a check that they have been registered for the session. One line, ~5 seconds of output. Fires every session (cost is constant, low).

2. **By-number citation when invoked.** When any in-session proposal touches the cross-DB boundary, Claude cites DR-028 by number and names which forbidden pattern applies before proposing implementation. This forces precision about which rule is in play and makes deviations visible. Fires only when cross-DB topics arise.

3. **Mid-session re-read trigger.** If a cross-DB topic surfaces mid-session (after orientation reading is past), Claude re-reads DR-028 explicitly before responding. Cost: a few seconds, only when relevant.

4. **Log discipline-rot watch.** Sessions where DR-028 is invoked, deferred, or even almost-bent get a log entry. This enables pattern-tracking across sessions: if DR-028 is invoked every session, that's signal; if never invoked, that's signal too. Fires only when DR-028 actively participates in a session.

**Additional structural protection:**

- **Multi-agent governance review for high-stakes cross-DB decisions.** High-reversal-cost or high-blind-spot decisions involving the cross-DB boundary are candidates for the multi-agent governance review pattern (see Multi-Agent Governance Review section below). The multi-agent review is a structural protection against Claude's anchoring on the v3 frame — distinct from these in-session protections.

- **Reversal as new DR.** A reversal of any forbidden pattern is itself a new DR. The bending becomes visible deliberately, never via session-by-session erosion.

**What this DR does *not* prohibit:**

- Reading from `capture.db` via the data API for any analytical or operational need. The whole point is that reads are cheap and unlimited.
- Storing references (Betfair market_id, race_id, natural-key tuples) on v3 entities. References are not denormalisation.
- Storing bet-context facts that happen to be informed by race state at a specific moment (the Slice 6 field_size captures, DR-026 market snapshots). Bet-context capture is owned by v3.
- Future changes to `capture.db`'s schema or the data API contract. Those are owned by the racing-data project, not v3, and v3's integration module absorbs the change in one place.

**Tradeoff:** Adds a discipline overhead — every cross-DB-related design decision passes through this DR. Acceptable: the alternative is the slow-cadence v2-shaped failure that the operator explicitly named as the meta-risk for this whole architecture.

**Date:** 2026-04-27

---

## DR-029 (DRAFT) — Data layer is reviewed and brought to v3 fit-for-purpose before v3 build begins

**One-line justification (DR-bloat watch):** Sequencing is structural. Codifying "data layer first, then v3 build" prevents discipline-rot via build-time temptation (adding ad-hoc captures during v3 build) and gives v3 a stable API contract to build against. Affects project trajectory across multiple sessions, doesn't fit as an amendment to any existing DR. Earns its DR.

**Why:** Session 11 surfaced two distinct risks for v3's cross-DB architecture: (1) discipline rot at build time, where the path of least resistance under bet-logging pressure could be to add an ad-hoc capture or denormalisation in v3 in violation of DR-028; (2) v3 building against a moving data-API contract while `capture.db` is itself being extended for v3's needs (sports markets, NZ, cadence tuning), producing integration bugs that compound. Both risks are eliminated by sequencing data-layer-first.

The operator also surfaced (Session 11) that the deep scoping work across Slices 1–6 has produced the truest sense of v3's data requirements yet — making this the right moment to review the data layer against those requirements, before build.

**Locked stance:**

The execution-layer (v3) build does not start until the data layer (`capture.db` + data API) has been reviewed against v3's scoped requirements and any required extensions are complete and stable.

**What "fit for purpose" means concretely:**

The data review produces a written audit covering at minimum:

- **Race-data coverage confirmed fit for purpose for v3's scoped needs.** All fields needed by v3 are captured at sufficient cadence with sufficient quality. Includes verification of race classification fields (race_class, distance_metres, race_group, track_type, track_condition_raw), finish position and margin capture, runner-level metadata, BSP / closing Betfair coverage. **Race results coverage is confirmed canonical for v3 auto-settlement** — v3's `bet_settled` settlement logic reads VPS race results via `vps_client` and resolves bet outcomes against them, inheriting Strategy 1 / BetHub v2's existing auto-settlement confidence pattern. NZ thoroughbred / harness / greyhound coverage is re-asked in the data review (operator decision: include if Racing API supports, exclude if not).

- **Sports market data layer added.** Betfair sports markets (AFL, NRL at minimum; other sports per scope) captured to support DR-026 at-log-time snapshots for sports bets in v3. Soft-book sports market coverage is a separate scope question to be decided in the data review (whether to extend existing scrapers to sports pages, accept day-one limitation, or defer).

- **At-bet-placement-time API pattern: periodic-only with analytical bracketing.** v3 calls VPS data API on bet log; VPS returns the most-recent-stored snapshot from `capture.db` with its timestamp and a freshness indication. v3 stores this inline on the bet record per DR-026. **No on-demand fresh-now snapshot pattern is added to the VPS** — the periodic capture (5 min standard, 60s pre-jump intensive, 60s in-running) is sufficient given the analytical model below.

  *Analytical justification (the bracketing model):* the bet record carries the snapshot at T-x with timestamp; analytical queries can read both the T-x snapshot and the T-x+cadence snapshot from `capture.db` at analysis time, observing the market movement *across* the bet timestamp. The bet's true market state at T is bracketed by the surrounding interval data. Cadence determines the tightness of the bracket; for typical pre-jump cadence (60s), the bracket is tight enough that timing-optimum, counterfactual-return, and promo-EV-calibration analyses are well-supported. This is a stronger analytical position than a single fresh on-demand snapshot, because the surrounding-interval data tells us about market movement *around* the bet, not just at a single point.

  *Freshness handling:* v3 marks `stale_flag = true` if the snapshot is older than a threshold (e.g. 90s) and `bf_snapshot_unavailable = true` if the snapshot is older than a larger threshold (e.g. 5 min) or the VPS is unreachable. Thresholds are tunable in v3 config.

  *Late-scratching handling:* a late scratching changes effective field size and can move Betfair prices substantially in seconds. The data review specifies that v3 reads scratching state from `capture.db` alongside the snapshot at bet-log time; if a scratching occurred between snapshot timestamp and bet-log time, v3 flags this on the bet record. This handles the edge case without requiring an on-demand snapshot pattern.

  *Cadence verification as data-review item:* the data review verifies empirically that pre-jump cadence is tight enough for v3's actual bet-log timing distribution. If a meaningful fraction of bets occur outside pre-jump cadence (e.g. operator places bets 8+ minutes before jump), resolution paths in priority order: (a) extend the pre-jump intensive window (e.g. 10 min instead of 5); (b) tune the standard-cadence interval; (c) accept the staleness with operator-visible indicator. On-demand snapshot is not introduced unless (a)/(b)/(c) prove insufficient.

  *VPS-unreachable handling:* per DR-026 amendment, v3 logs the bet with `bf_snapshot_unavailable = true`, surfaces in Burst Review.

- **Settlement model simplification (no confidence hierarchy).** The v3-with-VPS architecture removes the need for an algorithmic confidence hierarchy on bet settlement. Two sources, different facts: **VPS race result is canonical for "what happened in the race"** (auto-settlement reads from here); **book settlement (operator-recorded on `bet_settled`) is canonical for "what the operator's cash outcome was"**. Divergences between the two — voids per book rules, dead-heat handling differences, stewards' inquiry resolutions, late book corrections — are surfaced as **reconciliation signals in burst review or session reconciliation reports**, not algorithmically ranked. If divergence frequency turns out to warrant building structure around it, that is a future BetHub update, not a v3 day-one concern.

- **External analytics environmental scan (cheap-capture / expensive-to-reconstruct fields).** The data review explicitly conducts an external environmental scan to identify data fields v3 should capture now to preserve future analytical optionality, even though v3 is not building analytics in this phase. Scope:

  *Source-by-source field inventory.* What does Betfair API expose beyond what we currently capture? What does The Racing API expose beyond what we currently use? Are there other accessible sources (official racing body data, free historical archives, sectional times feeds, league data feeds for AFL/NRL, fitzRoy R package data, AFLTables, NRL-equivalent sources) that we don't currently consume? For each, what's the field list, what's the access cost, what's already in capture.db, what's not.

  *Analytics literature reconciliation.* Survey of racing AND sports analytics work — published research, public-domain models, betting-syndicate disclosures, Kaggle competitions, blog posts from quant-betting practitioners. What features do they use? What does the literature suggest matters predictively?

  *Cross-reference into capture decisions.* For each field the literature suggests is valuable, three buckets: (1) available + currently captured → no action; (2) available + not currently captured + cheap → capture in the data review; (3) available + not currently captured + expensive, *or* not available → parked for future consideration with a written rationale.

  *Cost test (the cheap-capture filter):* a candidate field is in-scope for capture only if capture cost is below threshold (e.g. "no new external API calls beyond what's already authorised; only fields already passing through existing API responses or trivially extractable from existing scrapers"). Expensive captures are parked, not adopted.

  *Multi-domain coverage.* Racing AND sports are treated as parallel work-streams with the same methodology. The existing AFL Edge work and racing-ev-model design notes feed in directly — the scan absorbs prior thinking rather than redoing it.

  *Time-box.* The scan is time-boxed to **two sessions of work** (covering racing + sports). If two sessions isn't enough for both, the operator decides whether to extend the box or split (racing scan first, sports scan second). The scan never opens-end. Whatever doesn't make the cut by the time-box closes is parked.

  *Capture-only constraint.* This is capture decisions only — **no analytics design happens here**. The analytics layer remains deferred and out of scope. Captured fields preserve future optionality; designing what to do with them is a later phase. The principle is the DR-026 cheap-capture principle applied at the race-data and sports-data layers: capture cheaply now, preserve analytical optionality for questions we haven't asked yet.

- **Data API contract versioned and documented.** v3's `vps_client` interface is specified against the locked contract. Schema-drift discipline (DR-028 forbidden pattern 3) is now operationally meaningful because there is a documented contract to drift from.

**Scope limits:**

This DR covers data-layer work scoped to v3's needs as locked across Slices 1–6 plus the cross-DB integration governance (DR-027 / DR-028 / DR-026 amendment). It does **not** cover:

- **Analytics layer formalisation.** Deferred. Out of scope for this phase. Cheap-capture fields per the data review are captured; analytics queries against them are not designed here.
- **Account-isolation layer formalisation.** Deferred (TP-Link MiFi + AdsPower + SOCKS5 remains operator-managed manual workflow). Out of scope.
- **Cloudflare-blocked book scraping** (Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble). Deferred — operator judgment that this is "an entire project in itself" and not a v3 prerequisite. Out of scope.
- **Any other umbrella-architecture work** beyond the v3 ↔ data layer integration.

These deferred scopes are intentional and operator-confirmed. They do not block v3 build. If they become binding during v3 operating life, they enter the work backlog as their own scoped pieces.

**Sequencing inside the data review (high-level, to be refined in Session 12+):**

1. Reconciliation contract write-up across Slices 1–6, including explicit v3 data-requirements statement (Session 12).
2. Build strategy decision — strangler-fig vs clean break + slice strategy (Session 13). Has data-layer implications because it determines whether v3's `vps_client` builds on top of `bethub-v2/vps_client.py` or designs from scratch.
3. First multi-agent governance review — assesses data-layer-first sequencing decision and v3 data requirements doc (Session 14). Decision-under-review document drafted collaboratively (operator + Claude) mid-Session-12 or Session-13.
4. Data review scoping — structured audit template covering the items above, checklist per data type, sub-questions per checklist item (Session 15).
5. Pre-execution governance review — operator go/no-go on data review scope before any execution begins.
6. Data review execution — extensions built, tested, documented, contract versioned. Per-extension governance check before each significant change. External analytics scan time-boxed to two sessions of work within this phase.
7. Final data layer lock review — confirms API contract is locked, `vps_client` interface is specified, data layer is fit-for-purpose. This is the gate.
8. v3 build begins.

**Tradeoffs:**

- **Cost:** v3 build is deferred by the duration of the data review and extensions. Measured in sessions, possibly several weeks. Operator accepts this cost as structural insurance against v2-shaped failure modes; explicitly prefers slow-and-solid over fast-and-fragile ("time spent now is time saved later, likely with dividends").
- **Risk:** Some v3 data requirements may only become visible during v3 build, not surfaced in the review. Mitigation: review is scoped to what's understood from Slices 1–6, not "perfect data layer." Gaps surfacing during build are bounded by DR-028 (extensions go through the integration module, no in-place caching, no second integration point), so build-time discoveries don't compound into v2-shaped messes.

**Date:** 2026-04-28

---

## DR-020 amendment — Standalone Betfair liquidity capture build superseded for AU racing

**Status:** Amendment to DR-020 (Standalone Betfair liquidity capture). The original DR specified a build task to capture Betfair market depth, total matched, and timing data for AU thoroughbred / harness / greyhound markets. Session 11 confirmed that `capture.db` (the existing UK VPS racing-data capture) already implements the substance of this spec.

**Amendment text (to be appended to DR-020 in `decisions.md`):**

> **Amendment 2026-04-28 (Session 11):** The standalone Betfair liquidity capture build originally targeted by this DR is **superseded for AU racing** by `capture.db` — the existing UK VPS racing-data capture system at `/home/racing/racing-data-capture/data/capture.db`. capture.db captures Betfair time-series snapshots for AU thoroughbred / harness / greyhound markets with 3-level depth on both back and lay, total matched, last_match_time, and snapshot batch tracking, on a tiered cadence (5 min standard → 60s intensive in the 5 min pre-jump window → 60s in-running → 2 min settlement checks). This implementation predates v3 and has been running successfully serving Strategy 1, BetHub v2, the Racing EV model, and AFL Edge.
>
> Per DR-027, v3 reads at-log-time market snapshots from capture.db via `vps_client` rather than running its own capture process. Per the DR-026 amendment (also dated 2026-04-28), the snapshot fields and capture principle are unchanged — only the source path is updated. Per DR-029, the architecture is periodic-only (no on-demand fresh-now pattern); analytical bracketing via surrounding-interval snapshots in capture.db provides stronger market-context visibility than a single fresh snapshot would.
>
> **Sports markets (AFL, NRL, etc.) are NOT covered by capture.db and remain genuinely uncaptured today.** The DR-020 capture principle (cheap to capture now, expensive to reconstruct retrospectively) still applies to sports markets and is the first item in the upcoming DR-029 data review. Day-one v3 sports bets will log with `bf_snapshot_unavailable = true` until the sports capture extension lands per DR-029.
>
> **For DR-014 (soft-book price context in burst-mode action queue):** existing VPS bookmaker scrape cadence (5 min standard / 90–120s intensive, 5 min pre-jump) may or may not be sufficient for DR-014's hot-path use case. Cadence verification is parked as a build-time question per DR-029's data review. Architectural shape (capture.db is the source) is unchanged regardless of cadence outcome.

---

## DR-026 amendment — at-log-time market-context snapshot is sourced via the data API

**Status:** Amendment to DR-026, dated 2026-04-26. The original DR-026 specified that the snapshot is sourced from "the standalone Betfair liquidity capture per DR-020." DR-020's build is now superseded for AU racing per the DR-020 amendment. This amendment records the corrected source path.

**Amendment text (to be appended to DR-026 in `decisions.md`):**

> **Amendment 2026-04-28 (Session 11):** The at-log-time market-context snapshot for AU racing bets is sourced from `capture.db` via `vps_client`, not from a standalone capture process. The fields captured on the bet record are unchanged (best Betfair lay price + size, best back price + size, total matched, snapshot timestamp, stale flag). The cross-system-durability justification for inline storage (rather than read-time derivation per DR-019) survives intact — the snapshot is captured external context, properly stored on the bet record, durable against later capture-side issues including VPS reachability changes and `capture.db` schema evolution.
>
> Per DR-029, the architecture is **periodic-only with analytical bracketing**: VPS returns the most-recent-stored snapshot from `capture.db` (typically 0–60s old in pre-jump windows; longer outside). v3 marks `stale_flag = true` above a tunable threshold (e.g. 90s) and `bf_snapshot_unavailable = true` above a larger threshold (e.g. 5 min) or when VPS is unreachable. Analytical queries can later bracket the bet's true market state by reading the surrounding-interval snapshots from capture.db, giving stronger market-context visibility than a single fresh snapshot would. **No on-demand fresh-now pattern** is introduced unless cadence verification in the data review proves insufficient.
>
> Late scratchings are handled via a separate flag: v3 reads scratching state from `capture.db` alongside the snapshot at bet-log time; if a scratching occurred between snapshot timestamp and bet-log time, v3 flags this on the bet record.
>
> For sports-market bets (AFL, NRL, and any non-racing market type), at-log-time snapshots are not available day-one per DR-029. v3 logs the bet with `bf_snapshot_unavailable = true` and surfaces the gap in Burst Review.
>
> The integration is implemented in a single module (`vps_client` or its named successor) per DR-027. The data API contract is load-bearing; per DR-028, no second integration point is permitted.

**Why this is an amendment, not a supersession:** DR-026's architectural stance (capture cheap, capture inline on the bet, capture durable across system boundaries) is unchanged. Only the source path is updated. The principle is what locks; the source path is implementation.

---

## Slice 1 amendment (canonical record in `sessions/SESSION_05.md`)

**Status:** Amendment to the canonical Slice 1 schema lock. Resolves Q9 (carried from Session 10) and the `race`-entity question that surfaced in Session 11's Q9 verification.

**Amendment text (to be inserted into the Slice 1 canonical record in `SESSION_05.md`, in the Q9 / race-reference section):**

> **Q9 resolution (Session 11):** Slice 1's locked entity hierarchy does **not** add a `race` entity. The race-reference question is resolved by external integration: race-side data (race classification, distance, surface, finish position, runner detail, BSP, Betfair time-series snapshots, bookmaker time-series snapshots) is owned by `capture.db` (the existing UK VPS racing-data capture system) and read by v3 on demand via the data API per DR-027.
>
> The eight Slice 1 entities (account, book, ownership_cluster, platform, account_at_book, promo_template, promo, bet) are unchanged.
>
> The `bet` entity carries race-side identifiers as references, not as denormalised race-data fields:
>
> - `event_id` — Betfair `market_id` for the race-as-betting-market. Stable identifier.
> - `bf_market_id` — same value as `event_id`, scoped to the Betfair-source meaning per DR-026 capture conventions. Retained as a separate field for source-clarity.
> - `(race_date, venue_normalised, race_number)` — natural-key tuple, available as fallback resolution path when Betfair identifiers are missing or ambiguous (e.g. retrospective bet entry, Betfair market ambiguity).
>
> No `race_id` foreign key. No race classification field. No race-distance field. No race-surface field. No finish-position field on the bet entity (finish position lives on `bet_settled` per the Session 10 amendment, captured at settlement time as a bet-context fact per the DR-026-extended cheap-capture principle, *not* as a denormalised race fact).
>
> Session 10's "Option B" (race classification on the race reference) is preserved in spirit — race classification *is* on a race reference, just not one in v3. It's in `capture.db`, where it has been the whole time.
>
> Australian thoroughbred / harness / greyhound is the in-scope universe per `capture.db` coverage. **NZ is excluded** day-one per operator decision in Session 11. NZ races logged in v3 will resolve race-side identifiers but will return null for race-classification context unless and until NZ coverage lands in `capture.db`. NZ inclusion is a question to be re-asked in the upcoming DR-029 data review (verify Racing API NZ coverage; if available, NZ enters scope; if not, NZ remains a day-one limitation).

**Why this is an amendment, not a Slice 1 reopen:** the eight entities are unchanged. The shape of the bet entity's race-side identifiers is unchanged at the field level (`event_id`, `bf_market_id` were already in the locked Slice 3 record). What this amendment adds is the architectural stance on what those identifiers *mean* — references into `capture.db` rather than identifiers awaiting a future v3 race entity. This documents an architectural fact that wasn't visible at Slice 1 lock time.

---

## Slice 3 amendment (canonical record in `sessions/SESSION_07.md`)

**Status:** Amendment to the canonical Slice 3 record. Documents the integration semantics of the bet payload's race-side identifier fields.

**Amendment text (to be inserted into the Slice 3 canonical record in `SESSION_07.md`):**

> **Session 11 amendment — race-side identifier integration semantics:** The `bet` event payload's `event_id` and `bf_market_id` fields are references into `capture.db` (the existing UK VPS racing-data capture system), resolved at read time via `vps_client` per DR-027. No v3-side race table exists; per DR-028 these fields are not FK columns to a v3 race entity, and v3 does not store denormalised race-data alongside them.
>
> The DR-026 market-context snapshot fields on `bet_placed` payloads (`bf_market_id`, `bf_runner_id`, `bf_runner_name`, best back/lay + sizes, total matched, snapshot age, stale flag, `bf_snapshot_aligned_to_placement`) are sourced from `capture.db` via `vps_client` per the DR-026 amendment dated 2026-04-28. The fields and semantics are unchanged. Per DR-029, the architecture is periodic-only with analytical bracketing; no on-demand fresh-now pattern is added unless cadence verification proves insufficient.
>
> `bet_leg` events (SGM legs) carry their own per-leg Betfair `market_id` / `selection_id` references, sourced and resolved through the same integration path.
>
> Slice 3's central design decisions (event-typed bet record, first-class columns plus JSON payload, sports-betting transferability, model fields including pairwise joint probabilities, retrospective entry flow with `bf_snapshot_aligned_to_placement = false`) are unchanged. This amendment documents only the architectural source-path for the race-side identifier and snapshot fields.

---

## Multi-agent governance review pattern (informational; not a DR)

**Status:** Process tool, not an architectural fact. Documented here for inclusion in `work_in_progress.md` (or a new `governance.md` if one is created) as an established review pattern for high-stakes decisions.

**Why this is not a DR:** It's a process for *making decisions*, not an architectural decision in its own right. DRs codify what v3 *is* or *does*; this pattern codifies *how high-stakes decisions get reviewed*. Distinct concerns. Belongs in process documentation, not architectural decisions.

**The pattern:**

For decisions with high reversal cost or high blind-spot risk (Claude is a single point of failure in the architecture review), assessment is structured across multiple independent agents to protect against Claude's anchoring on the v3 frame.

**Document suite (per review):**

| Document | Author | Purpose |
|---|---|---|
| `architecture_current.md` | Claude (this session, or successor) | Descriptive: what's locked, what entities exist, what DRs apply |
| `data_layer_current.md` | Claude (this session, or successor) | Descriptive: what `capture.db` does today, fields, cadence, gaps |
| `decision_under_review.md` | **Operator + Claude collaborative** ("Claude asks, operator tells, Claude records") | Frames the question being assessed, current direction, concerns, alternatives considered. Operator-context-in-the-frame is essential, but operator authoring solo would carry a writing-overhead Claude can absorb. The collaborative pattern keeps operator-context in the framing while Claude does the recording. |
| `open_questions.md` | Independent agent (fresh Claude session, ChatGPT, or Gemini) | Reads factual + decision documents, surfaces what hasn't been asked, what's been assumed without defence, what's been backgrounded that should be foregrounded |

**Assessment agents (three, independent):**

| Role | Agent | Brief |
|---|---|---|
| Software developer | Claude Opus, fresh session, no project context | Technical assessment: soundness of design, integration risks, alternatives |
| Project manager | GPT-5 / GPT-5.1 or Gemini | Sequencing, scope, dependency, risk-management framing |
| Skeptic | Whichever non-Claude model wasn't used for PM | Stress-test the decision; explicitly instructed to challenge rather than validate |

Each gets the same document suite. Each produces an independent assessment. **Mix model families** — three Claude sessions share architectural priors and converge; cross-family diversity protects against this.

**Judge:**

Claude Opus, fresh session, given all three assessments and the document suite. Instructed to *synthesise rather than choose* — surface where the three agents agree, where they disagree and why, what recommendations emerge from the synthesis.

**Cadence:**

Reserved for high-reversal-cost or high-blind-spot-risk decisions. Examples: data-layer-first sequencing (locked here in DR-029), build strategy (Session 13 deliverable), any DR that codifies discipline (DR-028 was a candidate; reviewed informally in Session 11 conversation but not via this full pattern).

**Heuristic:** If Claude says "you should defer to me, this is a software call," that's a signal the decision may warrant a multi-agent review. Software calls are exactly where Claude's anchoring is most likely to be both load-bearing and invisible to Claude.

**Not used for:** routine slice work, vocabulary calls, schema field decisions. Iteration with the operator is sufficient there.

**First scheduled use:** Session 14 — assessing the data-layer-first sequencing decision (DR-029) and the v3 data requirements doc (Session 12 sub-deliverable) before VPS data review begins. Decision-under-review document drafted collaboratively in mid-Session-12 or Session-13.

---

## `work_in_progress.md` — additions

**Add to the existing "Future-session tasks (parked)" section:**

> - **Soft-book scrape cadence verification for DR-014's hot-path use case.** Existing VPS bookmaker scrape cadence is 5 min standard / 90–120s intensive (5 min pre-jump). DR-014 expects "best soft price right now" during burst-mode bet decisions. Verify whether existing cadence is sufficient or whether DR-014's implementation needs a v3-side just-in-time poll layered on top. Resolution paths: tune VPS cadence higher in pre-jump window, build v3-side per-decision poll, or accept measured staleness with operator-visible indicator. Architecture stance is unchanged regardless of resolution: capture.db is the source per DR-027. **In scope for the DR-029 data review.**
>
> - **Sports Betfair capture gap.** The VPS Betfair collector covers racing markets only. v3 expects to log sports bets (AFL, NRL, etc.) and the DR-026 at-log-time market-context snapshot principle applies. Day-one v3 sports bets log with `bf_snapshot_unavailable = true` per DR-026 amendment. **First item in the DR-029 data review** — sports Betfair capture extension on the VPS.
>
> - **Cloudflare-blocked soft books (Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble).** Out of scope for the DR-029 data review per operator decision (Session 11) — "an entire project in itself" and not a v3 prerequisite. May enter scope as a separate piece of work after v3 is operating.
>
> - **Account-isolation layer formalisation.** TP-Link MiFi + AdsPower + SOCKS5 currently operator-managed manual workflow. Out of scope for the DR-029 data review per operator decision (Session 11). May become an architectural concern later.
>
> - **Analytics layer formalisation.** Deferred per DR-029 scope limits. Cheap-capture fields are added during the DR-029 data review (external environmental scan, racing + sports, time-boxed to two sessions) to preserve future analytical optionality, but no analytics layer is designed here.
>
> - **NZ racing inclusion.** Excluded day-one per operator decision (Session 11). Re-ask in DR-029 data review (verify Racing API NZ coverage).
>
> - **Decision-under-review collaborative drafting** for Session 14's first multi-agent governance review. Operator + Claude session, "Claude asks, operator tells, Claude records." Scheduled mid-Session-12 or Session-13. Frames the data-layer-first sequencing decision (DR-029) and v3 data requirements doc for assessment.

**Update the "Imminent build tasks" section:**

> The DR-020 build task ("Standalone Betfair liquidity capture") is **superseded for AU racing** by capture.db per DR-020 amendment. The build task is removed from imminent-build state. Sports Betfair capture extension is its successor and is the first item in the DR-029 data review.

**Update the "Open questions" / "Carrying into Session 12" section** (when work_in_progress.md is updated at session close):

> - Q9 (Slice 1 race-reference verification) — **resolved** in Session 11. No `race` entity in v3; references resolve into `capture.db`. NZ excluded day-one (re-ask in data review). See Slice 1 amendment in `sessions/SESSION_05.md` and DR-027.
> - Reconciliation contract write-up across Slices 1–6 — **carried to Session 12**. To include explicit v3 data-requirements statement as a sub-deliverable, supporting the upcoming DR-029 data review.
> - Build strategy decision (strangler-fig vs clean break + slice strategy) — **carried to Session 13**. Has data-layer implications via `vps_client` ancestry.
> - First multi-agent governance review — **scheduled Session 14**. Assesses DR-029 sequencing and v3 data requirements doc before data review execution begins. Decision-under-review document drafted collaboratively in mid-Session-12 or Session-13.

---

## Summary of what changes if the operator confirms this scratch

**`decisions.md`:**
- DR-027 appended (cross-DB architecture)
- DR-028 appended (integration boundary discipline, with four lean structural protections)
- DR-029 appended (data-layer-first sequencing, with periodic-only bet-log architecture, settlement model simplification, race results canonical for auto-settlement, external analytics environmental scan)
- DR-020 gets an "Amendment 2026-04-28 (Session 11)" subsection appended (supersession for AU racing; sports residual; periodic-only architecture lock)
- DR-026 gets an "Amendment 2026-04-28 (Session 11)" subsection appended (source-path correction; periodic-only architecture; late-scratching flag handling)

**`sessions/SESSION_05.md`:**
- Slice 1 canonical record gets a Session 11 Q9-resolution amendment appended

**`sessions/SESSION_07.md`:**
- Slice 3 canonical record gets a Session 11 race-side-identifier-integration-semantics amendment appended

**`work_in_progress.md`:**
- Seven new parked items added (cadence verification, sports capture gap, Cloudflare books, account-isolation layer, analytics layer, NZ, decision-under-review collaborative drafting)
- Imminent build tasks updated (DR-020 build task superseded for AU racing; sports capture gap is its successor in DR-029 data review)
- Open questions / carry section updated (Q9 resolved; Session 12/13/14 carries)
- Multi-agent governance review pattern documented (or added to a new `governance.md` if preferred)

**Nothing else changes.** Slices 2, 4, 5, 6 are unaffected. DR-001 through DR-019 and DR-021 through DR-025 are unaffected.

---

## What this scratch does *not* do

- Does not write the reconciliation contract. That's Session 12's deliverable, with the integration boundary baked in and a v3 data-requirements sub-deliverable.
- Does not resolve build strategy (strangler-fig vs clean break). Session 13 deliverable.
- Does not produce `diagrams/v3_target.svg`. Lower-priority; produced when the architectural picture is settled enough to draw cleanly. Likely Session 14 or post-data-review.
- Does not commit to operational behaviour around `vps_client` implementation details (retry policy, timeout values, contract versioning approach, error-surface design). Those are build-time decisions; architecture stance is what's locked here.
- Does not scope the DR-029 data review itself. That's Session 15's deliverable, after the multi-agent review at Session 14.

---

## Reading guidance

If anything below feels imprecise, vague, or like it could be bent under pressure in a future session — flag it. The whole point of writing this in scratch first is so you can challenge the language before it becomes binding.

**DR-028 in particular** is the discipline-as-structure piece. The four lean structural protections are designed to fire only when relevant — if they feel either too heavy (will blow out routine session orientation) or too light (won't actually protect against discipline rot), say so.

**DR-029's "fit for purpose" definition** has six bullets now (race-data + auto-settlement, sports market layer, periodic-only bet-log architecture with analytical bracketing, settlement model simplification, external analytics environmental scan, API contract versioning). If any of the six is too vague to be operationally actionable in Session 15's scoping work, say so.

**The periodic-only bet-log architecture** is a meaningful architectural lock-in. Reverses an earlier hybrid-pattern lean. If your gut says "no, I want to-the-second guaranteed for bets," push back — re-architecting to hybrid is straightforward and we lock that instead.

**The external analytics environmental scan** is a meaningful expansion of the data review's scope. Time-boxed to two sessions (covering racing + sports). If two sessions feels too aggressive or too generous, say so.

**The multi-agent governance review pattern** isn't binding (it's not a DR), but if the document-suite ownership structure or the role allocation feels off, say so — Session 14 is the first scheduled use and it's better to refine the pattern now than mid-execution.

**DR-bloat watch:** three new DRs (DR-027, DR-028, DR-029) plus three amendments. Each new DR has a one-line justification. If any feels like it could be demoted to an amendment of an existing DR, flag it.
