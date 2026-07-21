# DR-029 data review — scope document

*Drafted Session 27 (2026-04-29 ACST). Locks the shape and boundaries of the DR-029 data review work. Subsequent execution sessions deliver against the scope items below. Operator-Claude can revise during execution as concrete dependencies surface; revisions are versioned-not-rewritten per the framing principle in section 1.*

## 1. Framing principles

### 1.1 Versioned contract, not feature-complete schema

The DR-029 data review's lock target is a **versioned and documented contract** for the data layer (`capture.db` schema and the data API exposed by `vps_client`), not a feature-complete schema. "Locked v1.0" means contract shape and versioning discipline are settled — the call signatures, the data shapes returned, the staleness and unavailability signals, the schema-evolution policy. It does not mean the field set is exhaustive or the schema is frozen against future additions.

What this enables: backward-compatible additions to the contract remain available as workflow validation surfaces new needs. v3 build can begin against v1.0 of the contract; subsequent versions add fields without breaking changes. This is the synthesis-derived position from Recommendation 7 of the multi-agent review — the data-layer-first sequencing is sound if "first" means "contract versioned and stable" rather than "contract feature-complete."

This framing is stated explicitly because it dissolves a disagreement the multi-agent review surfaced: the project manager's concern that locking the data layer before workflow validation produces v2-shaped over-engineering is addressed by the versioned-contract framing, not by abandoning the data-first sequencing. The skeptic's position that data-first sequencing protects against v2's data-coupling failures is preserved.

### 1.2 Two direct lines into Betfair

v3's data architecture rests on two independent connections to the Betfair API:

- **Analytical line.** VPS scrapes Betfair API (and Racing API, and other feeds where used) at periodic cadences into `capture.db`. The merging of Betfair and Racing API datasets happens inside `capture.db`. v3 reads the merged surface via `vps_client` for analytical purposes — bracketing, post-hoc review, model calibration, BSP archive, market-curve analysis, analytical fields on bet records at read time.

- **Operational line.** v3 itself talks to the Betfair API directly via `betfair_client` at operational cadence — streaming or fast polling appropriate to burst-window decision support. v3's racing page and sports page (operator-facing UI for bet entry and live decision support) source from this direct line. No path through `capture.db`.

The two lines query the same Betfair API at different cadences, so they are consistent by construction modulo cadence lag for Betfair-sourced data. The Racing API ↔ Betfair merging inside `capture.db` is `capture.db`-internal work, addressable when reconciliation surfaces become concrete.

### 1.3 Racing-only analytical store

`capture.db` captures **racing only**. Sports data is not captured analytically. Sports operational data flows via `betfair_client` direct. Sports historical data, when needed for the same-game-multi (SGM) modelling work or other future sports analytics, is sourced from public/commercial archives (AFLTables, Squiggle, Fryzigg, NRL equivalents) separately, not as a `capture.db` extension.

The asymmetry between racing (analytical store + operational direct) and sports (operational direct only) is a deliberate architectural choice. Racing has bespoke time-series data needs that public archives don't serve at the resolution the racing EV model requires, hence the analytical store. Sports has rich public archives that obviate prospective capture for the SGM use case, plus longer time-pressure windows that reduce operational data's storage value. The asymmetry is acknowledged here so subsequent design decisions don't drift toward symmetry-by-default.

### 1.4 Soft-book operational layer deferred — typed-price path only at v3 day-one

**Reframed Session 69 (2026-05-03 ACST).** Original framing (Session 27): the operational soft-book layer was a v3 day-one *capability* with `softbook_client` interface contract specified, source implementation deferred. Session 69 deferred the operational layer itself, not just the source.

The reframing came from the operator's strategic assessment that soft-book operational live pricing is not one feature but several — best-promo-odds for racing insurance, best-odds for general turnover, multi-book scan for price boosters, SGM-correlated views for Strategy 3, same-race-multi views for emerging strategies — each wanting a different aggregation, a different operator surface, a different consumer workflow. The strategies that would dictate those surfaces are still being discovered in operations. Specifying an interface contract now would mean guessing at consumer surfaces whose shape isn't known yet.

v3 day-one ships with **typed-price entry only**: when the operator logs a soft-book bet, they type the price they took at the soft book, and v3 stores it. There is no live soft-book read anywhere in v3, no `softbook_client` module, no day-one operational soft-book layer. The typed-price path is specified inside §2.8 (bet-schema) and §2.9 (write-side coherence) as part of those streams' natural scope — not as a separate §2.5 deliverable.

A future operational soft-book layer is a deferred capability returning to scope as a fresh DR (likely DR-031+) when the strategies that need it have matured into concrete requirements drawn from running operations. See §3.11 for the formal deferral.

## 2. In scope — items DR-029 will address

### 2.1 Race-side data fit-for-purpose verification

Empirical inspection of `capture.db`'s current race-data population, cadence, and reliability against v3's stated requirements (per `v3_data_requirements.md` §B.2). Specifically:

- Race metadata field coverage (classification, distance, surface, group/tier, track condition, jump times, code, venue, race number).
- Runner metadata field coverage (name, barrier, weight, jockey/driver/trainer, form indicators, finish position, beaten margin, BSP, scratching events).
- Results coverage (finish positions, dead-heat, stewards' status, margins, sectional times where available, source identifier).
- Pre-jump cadence sufficiency for v3's analytical bracketing needs — verification, not assumption.
- BSP and calibration data presence.
- Scratching event capture timing and completeness.

Carried forward from DR-029's existing scope. Empirical verification is the core deliverable; resolution paths for any insufficiency are documented but not pre-decided.

**§2.1 close addendum (Session 37, 2026-04-30 ACST).** Surgical-fix execution outcomes through Sessions 35–37: Fix 1+2 (result population + nightly-backfill rework) executed cleanly per brief but cross-tab `with_both` (`finish_position` AND `betfair_selection_id`) stayed 0→0 due to venue-normalisation drift between live-capture and Racing API paths — added Fix 5 (venue harmonisation + retroactive race-key merge) to the surgical-fix arc to close out Cluster 1 fully (Session 36). Fix 3 (BSP / sp_near / sp_far write-back) executed cleanly per brief Session 37: Change (b) — pre-jump projection `SP_TRADED`→`SP_AVAILABLE` — is the clean win with sp_near/sp_far populating 100% INTENSIVE / 95% STANDARD post-restart (was 0% across 1.6M baseline rows); Changes (a/d) extended `RunnerData` and writer paths cleanly. Change (c) — post-suspension SP_TRADED fetch — executed structurally per brief but Betfair's API empirically does not surface `r.sp.actual_sp` on closed AU thoroughbred WIN markets via `priceProjection=SP_TRADED` (Code probed three settled markets at varying post-settlement ages; runner objects returned only `selectionId`, `handicap`, `status`, `adjustmentFactor` with no `sp` field). The brief's underlying assumption about API-surface adjacency was wrong, not Code's execution. **BSP write-back gap routed to a direct API observation probe** scheduled for Saturday 2026-05-02 morning ACST — captures raw Betfair `MarketBook` JSON every 1 second across 4 markets (2 thoroughbred + 1 harness + 1 greyhound), full pre-jump → SUSPENDED → CLOSED+45min window, all projection combinations rotated. Probe answers: (i) when `r.sp.actual_sp` populates if ever, (ii) cross-code response-shape parity, (iii) full §2.10 API-field-inventory deliverable, (iv) cadence empirics for Fix 4 design. Surgical-fix sequencing: Fix 4 (cadence) and Fix 5 (venue harmonisation) brief drafting waits on probe results — Fix 4 specifically may want re-anchoring after observing actual API behaviour at state transitions. **The `bsp_price` column population gap is now narrowed from "wiring problem" to "Betfair-API-surface question" — outcome routed to probe, not another surgical fix without grounding.** Pre-flight verification residual logged Session 37: `racing-metadata-backfill.service` has been failing six consecutive scheduled nights since 2026-04-25 with `PermissionError` on the log file despite Fix 2's chown; manual run 2026-04-30 cleared 60 unsynced dates worth of accumulated metadata; tomorrow's scheduled run is the diagnostic for whether the chown actually held. Logged to WIP §16. Session 37 also surfaced `track_type=turf` for all races regardless of code (thoroughbred/harness/greyhound) — the discipline field doesn't appear cleanly carried in `races.track_type`; routed to §2.10 API-field-inventory.

**§2.1 close (Session 34, 2026-04-30 ACST).** Closed-with-known-debt-named after surgical-fix-vs-rebuild call. Cluster 1 (result-population + identifier-overlap) routed to **surgical fix** based on Code's source-review report at `dr029/2_1_race_data/source_review_report.md`. Evidence summary: zero rows in 421,651 carry both `finish_position` AND `betfair_selection_id` is path-not-taken, not join-key collision — system already produces what's needed (calibration job resolves winners daily; orchestrator settlement path writes `result_status`), wiring just doesn't run. Three small, low-risk, mostly-existing-code fixes close the gap: (1) backfill `finish_position` over the 60-day live-capture window via existing `backfill_subscription.py`, plus rework `racing-metadata-backfill.service` to use `get_unsynced_dates()` instead of `--days 1`; (2) add BSP write-back via three additive field changes across four files; (3) lower `DISCOVERY_INTERVAL` plus add fast-discovery sweep for late-listed Betfair markets, plus log the `_register_race` silent-drop branch. Routing 2 (reframe) and Routing 3 (rebuild) explicitly considered and not adopted — Code's evidence on evolvability holds (orchestrator file is large but coherent, contracts compose cleanly, scrapers tidy, storage layer clean). Three pieces of debt named as deferred-but-tracked: no test coverage, no migration framework, monolithic orchestrator file. None blocks surgical-fix execution. All three land in DR-029 close governance paragraph rather than blocking surgical-fix progress. **Surgical-fix execution forward-routed across §2.4 / §2.6 / §2.10 per the framings below.**

### 2.2 Sports operational layer — Betfair direct, no analytical capture

For sports markets (AFL, NRL day-one; other sports per execution-session decision), specify operational reads via `betfair_client` direct from Betfair. No corresponding `capture.db` schema or scraper work — sports is operational-only by architectural choice (per principle 1.3).

Specification deliverables:

- v3's sports page sources race/fixture lists, market structure, and live pricing direct from Betfair via `betfair_client`.
- For sports handicap and total markets: at bet entry, v3 queries Betfair direct for all market variants for the fixture (all line values offered), operator picks the line they bet at the soft book, v3 records the corresponding Betfair `market_id`. Pushes the line-matching problem from architectural-inference to operator-side specification at write time.
- Sports auto-settlement reads from Betfair direct via `betfair_client` for results, with public-archive fallback path specified (AFLTables, NRL equivalents) for cases where Betfair result data is incomplete or delayed.
- Bet record for sports stores Betfair identifiers (`event_id`, `market_id`, `selection_id`) plus the operator-specified line where applicable, plus the at-placement operational snapshot (price taken, best back/lay, total matched, timestamp).

This replaces the previous DR-029 framing of "sports market addition to `capture.db`" with the leaner direct-Betfair shape. Per Session 27 decision, the case for analytical sports capture in `capture.db` was found weak (rich public archives, longer time-pressure windows, SGM modelling sources from elsewhere), and DR-029 drops it accordingly.

**§2.2 close (Session 38, 2026-04-30 ACST).** Specified into `architecture.md` under the new `## Operational layer — Betfair direct` section (B.0 framing plus B.1.1–B.1.7 sports-specific subsections). The seven subsections cover: sports page sources from Betfair direct via `betfair_client` (B.1.1); bet entry via the operator-typed line + 11-line ladder pattern with HedgeModal/LogBet action icons per row (B.1.2); favourite inference for handicap markets via head-to-head price comparison — shorter-priced side is favourite, pick'em case falls through to label-pick (B.1.3); auto-settlement with Betfair-direct canonical, public-archive fallback at 90 minutes post scheduled fixture end, finalised/voided/provisional discipline matching the racing settlement model, past-90-min-no-result lands as `provisional` in Burst Review (B.1.4); sports bet record shape — Betfair identifiers + operator-specified line value + at-placement operational snapshot, with Betfair-unavailable-at-log-time fallback storing a placeholder record reconciled when reachability returns (B.1.5); SGM and specialist markets architecturally provided for but explicitly out-of-scope v3-day-one (B.1.6); cadence note tracked-and-open pending Saturday API probe findings (B.1.7). v3.1+ candidates named with explicit dependencies: auto-line-matching depends on §2.5's source implementation; SGM correlation modelling depends on a future sports-analytics arc. Operator UX shape adopts v2's HedgeModal/LogBet pattern with two action icons per ladder row — reuses an idiom that already works rather than introducing a new one. Operator confirmation came after sample mockup review (three states: empty, handicap-with-line-typed, total-with-line-typed) showing the line ladder layout with prices, liquidity, and the highlighted-row pattern. **The asymmetric architecture is now concrete in `architecture.md`** — racing has both analytical and operational lines; sports has operational-only — satisfying principle 1.3. **Next:** §2.4 (Betfair Streaming spec) extends the same operational-layer section when it lands, drawing on Saturday API probe findings; §2.5 (soft-book interface contract) is parallel work; §2.7 (API contract versioning) is downstream of all three at DR-029 close.

### 2.3 Periodic-only API pattern evaluation, on the analytical/operational axis

The periodic-only API pattern (no on-demand fresh-now endpoint, analytical bracketing as the rationale) is locked for the **analytical** consumer path — i.e., for `vps_client` against `capture.db`. The synthesis position is that the pattern is correct in scope but the scope was previously drawn wrong: it was being asked to do double duty for analytical and operational consumers.

DR-029 reaffirms periodic-only for analytical reads and explicitly carves out operational consumers as a separate concern (see 2.4 and 2.5). The bracketing argument (surrounding-interval snapshots from `capture.db` at analysis time are structurally stronger than a single fresh on-demand snapshot, because they tell us about market movement *around* the bet rather than at a single point) holds for analytical reads. It does not transfer to operational reads, which need a separate pattern entirely.

Reframed from existing DR-029 scope per Recommendations 1 and 5 of the multi-agent review.

### 2.4 Operational layer for Betfair pricing — Streaming spec

A direct connection to the Betfair Streaming API for sub-second exchange pricing in the burst window, routed through a dedicated `betfair_client` module. Extends the spirit of DR-028's one-integration-point discipline to operational feeds without forcing them through `vps_client`.

Specification deliverables:

- `betfair_client` module shape, parallel to `vps_client`, single integration point for the Betfair Streaming API.
- Connection management, authentication, subscription patterns, reconnection behaviour, message handling, rate-limit handling.
- Interface to v3's burst UI: what calls the burst UI makes, what shape returns, how staleness and unavailability are signalled.
- Reconciliation premise with `capture.db` analytical reads: same Betfair API at different cadences, consistent by construction modulo lag.

New scope item per Recommendation 2 of the multi-agent review — was previously implicit in v3 architecture, now named.

**Surgical-fix carry-in (Session 34).** §2.4 carries Cluster 2 cadence-fix scope (lower `DISCOVERY_INTERVAL`, add fast-discovery sweep for races within next hour, log `_register_race` silent-drop branch, consider tighter `MAIN_LOOP_TICK` for intensive-cadence ceiling) plus Cluster 4 BSP / sp_near / sp_far write-back from §5.3 of the source-review report. Both are small additive changes against existing infrastructure. The intensive p50 90-97s slip (vs documented 60s) is structural-leaning but bounded — `MAIN_LOOP_TICK=15s` plus per-race-stagger reduction would mostly close it; full async-per-race rework not adopted as part of surgical fix.

### 2.5 [Deferred Session 69] — Soft-book operational layer

**Deferred Session 69 (2026-05-03 ACST).** Originally scoped as `softbook_client` interface contract — source-flexible. Session 69 deferred the entire operational soft-book layer, not just its source implementation. See §1.4 for the reframing rationale and §3.11 for the formal deferral.

The typed-price path that v3 day-one supports for soft-book bet entry is specified inside §2.8 (bet-schema reframing) and §2.9 (write-side coherence) as part of those streams' natural scope. There is no separate §2.5 deliverable.

Section number retained for cross-reference stability across earlier session records and brief drafts; the in-scope item itself is closed.

### 2.6 Settlement model

Auto-settlement reads from the data layer, specified per consumer path:

- **Racing.** VPS race result via `vps_client` against `capture.db` is canonical. Two-source agreement (e.g., Betfair Win + Racing API) → `finalised`. Single high-confidence source → `finalised`. Low-confidence single-source or divergence → `provisional`, surfaced to Burst Review.
- **Sports.** Betfair result via `betfair_client` is canonical, with public-archive fallback (AFLTables, NRL equivalents) for delayed or incomplete cases. Same finalised / provisional discipline.

Carried forward from DR-029's existing scope, with the sports path re-specified per principle 1.3.

**Surgical-fix carry-in (Session 34).** §2.6 carries Cluster 1 result-population resolution as its centrepiece — (a) backfill `runners.finish_position` over the 60-day live-capture window via existing `backfill_subscription.py --from <live-capture-start>`; (b) rework `racing-metadata-backfill.service` to call `get_unsynced_dates()` instead of `--days 1` so the daily service catches up rather than only ever sweeping yesterday. Plus Cluster 4 capture-gap fixes for `actual_jump_time` and result `observed_at`. With these landed, the racing settlement path's two-source agreement discipline (Betfair Win + Racing API result, finalised vs provisional) operates against a populated data layer.

### 2.7 API contract versioning

Versioned endpoints, backward-compatible-additions discipline, breaking-changes-via-new-version-only policy, deprecation framework. Specification deliverables:

- Versioned endpoint pattern (e.g., `/v1/race/{event_id}/metadata`).
- Schema-change discipline: backward-compatible additions in-place; breaking changes only via new version.
- Deprecation policy with notice period.
- Contract documentation lives with the data layer, not v3.
- v3's `vps_client` interface is specified against the locked contract.
- Schema-drift surfaces in `vps_client` (one file), not scattered across v3 modules.
- Equivalent versioning discipline for `betfair_client` interface contract.

Carried forward from DR-029's existing scope; extended to cover the new operational module contract (`betfair_client`). `softbook_client` removed from §2.7 scope Session 69 following §2.5 deferral.

### 2.8 Bet-schema reframing on the operational/analytical axis

Reframe the bet-schema question (was: leaner-and-simpler vs more-data-rich) on the synthesis-derived axis: what is the minimal set of fields that must be captured at bet placement to make the bet record immutable as a *decision-context fact*, given that everything else is resolved at read time?

Synthesis-recommended shape: small, immutable, decision-context only — price taken, best back/lay at placement, total matched, snapshot timestamp from operational source. Race classification, runner detail, finish position, market curve, BSP, field size — all resolved at read time via `vps_client` against `capture.db`.

Specification deliverables:

- Final field list for the at-placement decision-context snapshot stored on the bet record, per bet type (Betfair exchange, soft-book racing, soft-book sports).
- Read-time resolution paths: which fields v3 resolves via `vps_client` analytical reads, which via `betfair_client` for current-market reference (e.g., live BSP for an unsettled bet's display).
- Sports bet records additionally store the operator-specified line for handicap/total markets (per 2.2).
- **Soft-book typed-price path (absorbed Session 69 from former §2.5).** Soft-book bet records store the operator-typed price taken at the soft book, plus the soft-book identity (which bookmaker), plus the at-placement Betfair-side reference snapshot for EV context. No live soft-book read; no `softbook_client` module. The operator types the price, v3 stores it.
- Immutability discipline: which fields on the bet record are append-only, which are read-time-derived and never stored, which are amendable via reconciliation events.

Downstream of 2.4 because "operational source" for exchange bets means the Betfair Streaming feed; soft-book bets do not have an operational source day-one (typed-price path only).

New scope item per Recommendation 1 of the multi-agent review. Soft-book typed-price path absorbed Session 69 (2026-05-03 ACST) following §2.5 deferral.

### 2.9 Write-side bet-entry coherence as integration-boundary contract addition

The leaner bet schema (2.8) means the bet record's identifiers must resolve cleanly at later read time. Three specific surfaces:

**(a) Sports line specification at bet entry.** For sports bets on handicap or total markets, the operator specifies the line they bet at the soft book. v3 queries Betfair direct via `betfair_client` for all market variants for the fixture, operator picks the line, v3 records the corresponding Betfair `market_id`. Burst UI behaviour when no Betfair market exists at the operator-specified line: surfaced for operator review (do not silently write a record without a matching `market_id`).

**(b) Placement-time sanity check.** `placement_time` is confirmed plausibly pre-jump (or pre-fixture-start for sports) given the scheduled start time from the operational source. Trivial check, specified explicitly to guard against backdating errors and clock-drift cases.

**(c) Identifier-resolution sanity check.** When the bet is logged, identifiers came from the operational direct line (`betfair_client` for racing-page or sports-page selections). Their later analytical resolution via `vps_client` against `capture.db` should always succeed because both lines source from the same Betfair API. If first analytical resolution fails after `capture.db`'s expected ingestion lag, surface as a `capture.db` ingestion fault rather than a write-time error. This is a passive sanity check on the integration boundary, not an active validation step.

The "operator-vs-soft-book runner divergence" failure mode is acknowledged as theoretically possible but operationally not a real concern, because Betfair is v3's canonical race-and-runner identity layer — any runner the operator can bet on at a soft book that doesn't exist in v3's Betfair-sourced view is a runner the bet won't actually happen on (the bet either doesn't get placed at the soft book because it's been scratched there too, or wouldn't be bet on because it's been scratched on Betfair).

New scope item per Recommendation 4 of the multi-agent review, narrowed per Session 27 architectural clarifications.

### 2.10 Time-boxed external analytics environmental scan

Time-boxed to two sessions of work, racing-focused given principle 1.3 drops sports analytical capture.

**Methodology:**

1. Source-by-source field inventory: what does Betfair API expose beyond current capture? Racing API beyond current use? Other accessible sources (official racing bodies, free historical archives, sectional times, Racing Australia)?
2. Analytics literature reconciliation: published research, public-domain models, betting-syndicate disclosures, Kaggle, blog posts. What features matter predictively for racing?
3. Cross-reference into capture decisions, three buckets:
   - Available + currently captured → no action.
   - Available + not currently captured + cheap → capture in the data review.
   - Available + not currently captured + expensive, OR not available → parked with rationale.
4. Cost test: capture-cheap filter only. No new external API calls beyond what's already authorised.
5. Capture-only constraint: no analytics design happens here. The analytics layer remains deferred.

**Sports analytical scan:** confirms the public/commercial archive landscape (AFLTables, Squiggle, Fryzigg, NRL equivalents) is as good as expected for SGM modelling and any other future sports analytics. Confirmation, not extension — sports analytical work is downstream of v3 build and sourced from public archives per principle 1.3.

Carried forward from DR-029's existing scope, narrowed per Recommendation 11 of the multi-agent review's scope-recalibration finding.

**Surgical-fix carry-in plus Session 34 touch-point.** §2.10 carries Cluster 4 source-exposes-but-pipeline-doesn't-write candidates (BSP / sp_near / sp_far now resolved via surgical fix §5.3, so §2.10's question on these becomes "any *other* SP-projection fields worth pulling alongside"). **Operator framing logged Session 34:** the API-field-inventory question (Betfair API + Racing API survey for fields-available-but-not-currently-captured) sits in §2.10, deliberately separate from the surgical fix. Different cognitive shape — surgical fix wires up what's already wired wrong; §2.10 surveys what the sources expose and decides what's worth pulling fresh. Better-quality decisions come from running §2.10 *after* the surgical fix has landed, against a cleaner data layer.

## 3. Out of scope — items DR-029 will explicitly not address

### 3.1 Speculative analytics fields

Fields whose value is "for analyses I haven't yet conceived of" — these are deferred until workflows actually surface the need, then added as backward-compatible contract additions per the versioned-contract framing (1.1). Per Recommendation 11 of the multi-agent review.

### 3.2 Full analytics layer

The analytics layer formalisation (separate analytical module, formal data warehouse, BI tooling) is deferred per the existing DR-029 scope and remains deferred. The capture-cheap analytics scan in 2.10 is a different and tighter activity.

### 3.3 Account-isolation layer formalisation

Deferred per existing DR-029 scope. Remains deferred.

### 3.4 Cloudflare-blocked soft-book scrapers

Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble. Out of scope per existing DR-029 scope — "an entire project in itself." Restated for clarity.

### 3.5 [Superseded Session 69] — Vendor selection for soft-book operational source

Originally: vendor scan (BetWatch and alternatives) parallel operator-side homework informing v3.1 milestone timing. Superseded by §3.11 — the operational soft-book layer itself is now deferred, so vendor selection is a downstream concern of that deferral, not a parallel pre-decision activity. Section number retained for cross-reference stability.

### 3.6 [Superseded Session 69] — Operational soft-book source connection on day one

Originally: v3 day-one ships with the operational soft-book interface but with manual entry as the source. Superseded by §3.11 — there is no operational soft-book interface day-one; soft-book bet entry is typed-price only inside §2.8. Section number retained for cross-reference stability.

### 3.7 Sports analytical capture in `capture.db`

Per principle 1.3 and Session 27 decision: sports data is not captured in `capture.db`. Sports operational reads via `betfair_client` direct (in scope, 2.2). Sports historical data sourced from public archives separately when needed.

### 3.8 Reachability and continuous-fitness infrastructure

Tunnel monitoring, auto-restart, alerting with thresholds, ongoing data-fitness checks, silent-degradation handling. Per Recommendation 3 of the multi-agent review, this is its own first-class scoping arc, parallel to or after DR-029. Out of scope for DR-029 specifically because it is its own arc, not because it is unimportant. Placement decision (parallel / after / precursor) made Session 27, recorded in `work_in_progress.md`.

### 3.9 NZ racing inclusion

Re-asked as a footnote in `v3_data_requirements.md` §B.2.1. Resolution path: verify Racing API NZ coverage during 2.1 (race-side data fit-for-purpose verification); if available, NZ enters scope as a backward-compatible later addition; if not, NZ remains a day-one limitation. Not a primary DR-029 deliverable.

### 3.10 Burst-review triage workflow design

Per Recommendation 5 of the multi-agent review, the burst-review triage is a load-bearing design pillar. Its detailed design is downstream of DR-029 — happens during v3 build phase when concrete reconciliation surfaces are flowing. DR-029 specifies what data the triage will read against (via the contracts above) but does not specify the triage workflow itself.

### 3.11 Soft-book operational layer (deferred Session 69)

**Deferred Session 69 (2026-05-03 ACST).** The operational soft-book layer — live soft-book pricing surfaced in v3 for burst-window decision support — is deferred from DR-029 entirely. This supersedes the original §2.5 in-scope framing.

**Why deferred.** Soft-book operational live pricing is not one feature. It is several distinct consumer surfaces, each tied to a different operator strategy and bet type:

- Best-promo-odds for racing insurance cycles (Strategy 1).
- Best-odds-with-promo for general turnover.
- Multi-book scan for price-booster identification (Strategy 2).
- SGM-correlated multi-leg views for Strategy 3 — and operator's own assessment is that this view may not be buildable from book odds alone, since correlation coefficients are not exposed at single-market granularity.
- Same-race-multi views for an emerging strategy.
- Other surfaces yet to be discovered as Strategy 3 and Strategy 4 mature.

Each surface wants a different aggregation, a different operator workflow, and potentially a different source. Specifying an interface contract before the consumer surfaces are known means guessing at shape — exactly the v2-shaped over-engineering the multi-agent review's project-manager seat warned against.

**Operator-side framing.** The strategies that would dictate the soft-book operational surfaces are still being discovered through running operations. Strategy 1 (Safety Net) is mature today and produces ~95% of profit; Strategy 2 (Price Booster) produces the remaining ~5%; Strategies 3 and 4 are aspirational growth directions, not income lines. The operational surfaces that would consume soft-book live pricing are mostly downstream of strategies that aren't yet running at scale. The honest position is: the operator does not yet know what soft-book operational views are needed, because the strategies that need them are pre-discovery.

**What v3 day-one ships with instead.** Typed-price entry only. The operator types the price they took at the soft book at bet-log time; v3 stores it. Specified inside §2.8 (bet-schema) and §2.9 (write-side coherence) as part of those streams' natural scope. No `softbook_client` module, no live read, no operational soft-book layer.

**When this returns to scope.** A future operational soft-book layer is a deferred capability. It returns to scope as a fresh DR when the strategies that need it have matured into concrete operational requirements. Trigger conditions: (a) Strategy 2 (Price Booster) volume reaches a level where multi-book scan is operationally useful rather than aspirational; or (b) Strategy 3 (Correlated Friction) begins running and surfaces concrete same-game-multi pricing surface requirements; or (c) Strategy 4 (Synthetic Each-Way) execution begins and surfaces concrete value-betting price-comparison requirements; or (d) operator surfaces a different concrete requirement from running operations.

**Cross-references for follow-on work.**

- BetWatch parallel-track vendor research (carried forward as operator-side homework) is no longer gating any DR-029 deliverable. Continues as discovery activity informing the future DR.
- The Betfair-as-canonical-source architectural extension (Session 42 flag) carries forward independently — soft-book bets in the typed-price path still carry Betfair-side identifiers as the canonical join key, per architecture.md §D12 and the Session 42 extension.
- §2.8 (bet-schema) and §2.9 (write-side) are now the load-bearing locations for soft-book bet record specification. Both inherit the Session 42 architectural extension.

## 4. Scope recalibration summary

Inherited DR-029 scope (existing, retained, possibly reframed): race-data fit-for-purpose (2.1), periodic-only API pattern (2.3 — reframed on operational/analytical axis), settlement model (2.6 — sports path re-specified), API contract versioning (2.7 — extended), external analytics scan (2.10 — narrowed).

Additions per Session 26 triage and this scoping session: Betfair Streaming spec (2.4), bet-schema reframing (2.8), write-side coherence (2.9).

Reshape per Session 27 architectural clarifications: sports analytical capture removed from scope (replaced by operational direct via `betfair_client`, 2.2). Sports analytical store dropped from `capture.db` per principle 1.3. Sports line-matching reframed from architectural problem to operator-side specification at bet entry (2.9a) supported by Betfair-direct query of all market variants.

**Reshape Session 69 (2026-05-03 ACST):** soft-book operational layer (originally §2.5) deferred from DR-029 entirely (§3.11). Original §2.5 framing was "interface contract specified, source deferred"; Session 69 deferred the operational layer itself, not just the source, on the basis that consumer surfaces are pre-discovery and contract shape cannot be specified meaningfully today. The typed-price path that v3 day-one supports for soft-book bet entry is absorbed into §2.8 (bet-schema) and §2.9 (write-side coherence). Section numbers §2.5, §3.5, §3.6 retained as superseded markers for cross-reference stability.

Narrowing per Recommendation 11: speculative analytics fields explicitly out (3.1), reaffirming existing out-of-scope decisions (3.2–3.4), the sports asymmetry (3.7), the reachability arc (3.8), NZ as backward-compatible-later (3.9), and burst-review workflow design (3.10).

## 5. Sequencing within DR-029 execution

Recommended order for the post-Session-27 execution sessions, reflecting dependency structure. Provisional — operator-Claude can revise during execution as concrete dependencies surface. Updated Session 69 (2026-05-03 ACST) to reflect §2.5 deferral.

1. Empirical `capture.db` inspection (covers 2.1 substantially, gates everything downstream that depends on `capture.db` state).
2. Operational layer spec — Betfair Streaming (2.4).
3. Sports operational direct (2.2) — depends on 2.4 (`betfair_client`) being settled.
4. Bet-schema reframing (2.8) — depends on 2.4 being settled. Includes the soft-book typed-price path absorbed from former §2.5.
5. Write-side coherence (2.9) — depends on 2.8 (and on 2.2 for the sports line specification surface).
6. Settlement model (2.6) — depends on 2.2 for the sports path and 2.4 for the Betfair-direct result reads.
7. Periodic-only API pattern reaffirmation (2.3) — synthesis activity drawing the analytical/operational boundary cleanly; mostly documentation work once 2.4 is in place.
8. API contract versioning (2.7) — final formalisation step before contract lock; covers `vps_client` and `betfair_client` contracts.
9. External analytics scan (2.10) — can run parallel to other items; output reads into 2.7 if it surfaces capture-cheap additions.

Final session: contract lock (v1.0 issued for both integration modules — `vps_client` and `betfair_client`) and pre-build governance review.

## 6. Cross-references

- `v3_data_requirements.md` — canonical living document for data-layer requirements; will be actively edited during DR-029 execution to reflect items 2.1–2.10.
- `decisions.md` — DR-027 (two-database architecture), DR-028 (integration boundary discipline), DR-029 (data layer fit-for-purpose before build) — load-bearing for everything in this scope document.
- `agent_review/Judge/judge_synthesis.md` — multi-agent review synthesis from which Recommendations 1–7 referenced above derive.
- `sessions/SESSION_26.md` — action triage from which the DR-029 scope additions originate.
- `sessions/SESSION_27.md` — this scoping session's log.
