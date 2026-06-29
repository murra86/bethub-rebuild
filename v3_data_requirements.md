# v3 data requirements

*Promoted from `SESSION_12_SCRATCH_v2.md` Part B Session 14 (2026-04-28 15:35 ACST). Self-contained. Reserved as input for Session 15 multi-agent governance review.*

---

**Audience:** Session 15 multi-agent governance review. Document is self-contained and intended for extraction as `v3_data_requirements.md`. Read order does not depend on Part A; cross-references to Part A are stated where useful, but the reader can absorb this section alone.

**Purpose:** Statement of what v3's accounting layer needs from the data layer (`capture.db` + data API) to operate, organised so the upcoming DR-029 data review can audit `capture.db` against this requirement set.

### B.1 Scope of the data layer for v3

**In scope for the data layer:**

- All race-side data v3 reads on demand: race metadata, runner detail, results, time-series snapshots, scratching state, BSP, calibration data
- Sports market data (AFL, NRL at minimum): currently absent from capture.db, must be added per DR-029
- Soft-book scrape data: cadence verification per DR-014's hot-path use case
- Periodic-only API contract per DR-029 (no on-demand fresh-now)
- API versioning and contract documentation (per DR-028 forbidden pattern 3)

**Out of scope:**

- Analytics layer formalisation (deferred per DR-029)
- Account-isolation layer (deferred per DR-029)
- Cloudflare-blocked book scraping (deferred per DR-029, "an entire project in itself")
- v3-side caching, mirroring, or denormalisation of any of the above (forbidden per DR-028)

### B.2 Race-side data requirements

#### B.2.1 Race metadata

For every AU thoroughbred / harness / greyhound race v3 might log a bet against, the data layer must expose, indexed by `event_id` (Betfair market_id) and resolvable by `(race_date, venue_normalised, race_number)`:

- Race classification (`race_class`)
- Race distance (`race_distance` in metres)
- Race surface (`race_surface`: turf / synthetic / dirt or applicable code-equivalent)
- Race group / tier (e.g., G1 / G2 / G3 / Listed / Stakes / Handicap)
- Track condition at jump
- Track type (e.g., flat / circle / trotting / pace)
- Scheduled jump time
- Actual jump time (post-jump)
- Race code (thoroughbred / harness / greyhound)
- Venue (canonical name)
- Race number

**NZ thoroughbred / harness / greyhound:** out of scope day-one; re-asked as a sub-question under B.7 #3 (DR-029 scope rightness) — see footnote there.

#### B.2.2 Runner-level metadata

Per runner per race, indexed by Betfair selection_id and race natural key:

- Runner name (canonical, with operator-friendly normalisation for display)
- Barrier / box / draw
- Weight carried (where applicable)
- Jockey / driver / trainer
- Form indicators where Racing API exposes them (last-start, days since last run, distance change, code change)
- Finishing position (post-result)
- Beaten margin (post-result)
- BSP (Betfair Starting Price) where available
- Scratching events with timestamp (scratched_at, late_scratch flag)

#### B.2.3 Race results

For settled races:

- Finish positions for all starters
- Dead-heat indication
- Stewards' inquiry status (where reported)
- Margin between positions
- Race time / sectional times where source exposes them
- Result observed_at timestamp from source
- Source identifier (Betfair / Racing API / Racing Australia / Racenet)

**Auto-settlement reads from the data layer.** v3's settlement worker (W6.5) for racing bets uses VPS race result as canonical for "what happened in the race." Two-source agreement (e.g., Betfair Win + Racing API) → `settlement_state = SETTLED_WON` or `SETTLED_LOST` (depending on whether the bet's selection won). Single high-confidence source → same. Low-confidence single-source or divergence → `settlement_state = PROVISIONAL`, surfaced to Burst Review.

#### B.2.4 Betfair time-series snapshots

For each runner in each in-scope market, the data layer captures and exposes:

- Best back price + size available
- Best lay price + size available
- Top 3 back prices + sizes (market depth)
- Top 3 lay prices + sizes (market depth)
- Total matched on the market
- Snapshot timestamp

**Cadence:** existing capture.db tiered cadence (5 min standard → 60s pre-jump intensive in 5 min window → 60s in-running → 2 min settlement checks).

**Cadence verification is a DR-029 data-review item.** Empirical check that pre-jump cadence is tight enough for v3's actual bet-log timing distribution. Resolution paths in priority order if insufficient: (a) extend pre-jump intensive window; (b) tune standard-cadence interval; (c) accept staleness with operator-visible indicator. On-demand pattern is not introduced unless (a)/(b)/(c) fail.

#### B.2.5 Bookmaker time-series snapshots

For DR-014's burst-mode soft-book price context:

- Existing scrapers (Entain, PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API) produce time-series snapshots at 5 min standard / 90–120s intensive cadence
- Cadence sufficiency for DR-014's hot-path use case is **a DR-029 data-review item** — verification, not assumption
- Cloudflare-blocked books (Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble) deferred per DR-029

#### B.2.6 BSP and calibration data

- BSP per runner per race (post-jump)
- Daily calibration summaries (existing capture.db output)
- Batch summaries (existing capture.db output)

These support the Racing EV model and any future racing analytics. Already in capture.db; v3 reads via data API on demand.

### B.3 Sports market data requirements

**Currently absent from capture.db. First item in the DR-029 data review.**

For Betfair sports markets (AFL, NRL day-one; other sports via review scope decision):

- Market identifiers (event_id, market_id, selection_id) per match
- Match metadata (teams, scheduled start time, league, round, season)
- Match results (post-event)
- Time-series snapshots equivalent to B.2.4 — best back/lay + sizes, depth, total matched, timestamp
- BSP equivalent where available
- SGM market structure where Betfair exposes joint markets (drives Slice 3 SGM model fields)

**Day-one v3 sports-bet behaviour without sports capture:** v3 logs sports bets with `bf_snapshot_unavailable = true`. Surfaced in Burst Review. Auto-settlement for sports bets falls back to operator-confirmation path until sports capture lands.

**Soft-book sports market coverage:** separate scope question for the data review.

### B.4 Data API contract

The data API (`racing-api.service` on UK VPS, `127.0.0.1:8400` over SSH tunnel; v3 `vps_client` is the integration module) exposes the data above through a versioned contract.

**Contract requirements per DR-028 forbidden pattern 3:**

- Versioned endpoints (e.g., `/v1/race/{event_id}/metadata`, `/v1/race/{event_id}/snapshot/latest`, `/v1/race/{event_id}/result`)
- Schema change discipline: backward-compatible additions in-place; breaking changes only via new version
- Deprecation policy with notice period
- Contract documentation lives with the data layer, not v3
- v3's `vps_client` interface is specified against the locked contract
- Schema-drift surfaces in `vps_client` (one file), not scattered across v3 modules

**Periodic-only API pattern (DR-029):**

- `vps_client.get_latest_snapshot(event_id, runner_id)` returns most-recent stored snapshot with its timestamp; v3 derives staleness
- `vps_client.get_market_curve(event_id, runner_id, from_ts, to_ts)` returns time-series for analytical queries
- `vps_client.get_race_result(event_id)` returns settled race result
- `vps_client.get_scratch_state(event_id, as_of)` returns scratching events up to a timestamp
- `vps_client.get_race_metadata(event_id)` returns race classification and runner detail

**No on-demand fresh-now endpoint.** Periodic capture is sufficient given analytical bracketing.

**VPS-unreachable handling:** v3 logs the bet with `bf_snapshot_unavailable = true`, surfaces in Burst Review.

### B.5 External analytics environmental scan (data-review item)

**Time-boxed to two sessions of work** in the DR-029 data review (covering racing AND sports as parallel work-streams).

**Methodology:**

1. Source-by-source field inventory: what does Betfair API expose beyond current capture? Racing API beyond current use? Other accessible sources (official racing bodies, free historical archives, sectional times, league data feeds, fitzRoy, AFLTables, NRL-equivalents)?
2. Analytics literature reconciliation: published research, public-domain models, betting-syndicate disclosures, Kaggle, blog posts. What features matter predictively?
3. Cross-reference into capture decisions, three buckets:
   - Available + currently captured → no action
   - Available + not currently captured + cheap → capture in the data review
   - Available + not currently captured + expensive, OR not available → parked with rationale
4. Cost test: capture-cheap filter only. No new external API calls beyond what's already authorised.
5. Capture-only constraint: no analytics design happens here. The analytics layer remains deferred and out of scope.

### B.6 Data review sequencing (DR-029)

The pre-build sequencing (already documented in DR-029):

1. Reconciliation contract write-up across Slices 1–6 — **Session 12 produced v1; Session 13 produced delta-spec; Session 14 produces v2 (this document) and promotes.**
2. Build strategy decision — likely Session 15+ now after multi-agent review reframes the question.
3. First multi-agent governance review — Session 15, assesses DR-029 sequencing, this v3 data requirements doc, the deferred bet-schema-simplification question, the periodic-only API pattern, and DR-029 scope rightness (with NZ folded in).
4. Data review scoping — post-multi-agent-review.
5. Pre-execution governance review — operator go/no-go on data review scope.
6. Data review execution — extensions built, tested, documented, contract versioned. Per-extension governance check.
7. Final data layer lock review — confirms API contract is locked, `vps_client` interface is specified, data layer is fit-for-purpose.
8. v3 build begins.

### B.7 Open questions reserved for Session 15 multi-agent review

These are reserved for the review and **must not be pre-empted** in the data review scoping.

1. **Bet schema simplification.** Whether DR-026 inline snapshot storage and Slice 6 `field_size_at_bet_placement` / `field_size_at_settlement` should be removed in favour of full cross-DB resolution from capture.db (bet stores only identifiers + placement_time; race-side context resolved via `vps_client` at read time). If adopted, simplifies bet_placed payload, revises the Slice 6 amendment, cleans DR-028 forbidden pattern 1 by removing its single narrow exception. **Until reviewed, current schemas remain in force.**

2. **DR-029 sequencing soundness.** Whether the data-layer-first sequencing (review → extend → lock → then v3 build) is the right structural protection given v3's actual risk profile.

3. **DR-029 scope rightness.** Whether the in-scope items (race-data fit-for-purpose, sports market layer, periodic-only API pattern, settlement model, external analytics environmental scan, API contract versioning) and out-of-scope items (analytics layer, account-isolation layer, Cloudflare-blocked books) are correctly drawn. **Footnote:** NZ inclusion is re-asked here as a sub-question — verify Racing API NZ coverage; if available, NZ enters scope; if not, NZ remains day-one limitation.

4. ~~**NZ inclusion.**~~ Folded into #3 as a footnote.

5. **Periodic-only API pattern with analytical bracketing.** Whether the periodic-only architecture (no on-demand fresh-now, cadence verification as fallback path) is the right structural commitment for the VPS data API contract and `vps_client` interface. Independently assessed alongside #1 because they share a data-shape concern but address different parts of the architecture (#1 is bet-record storage; #5 is the API contract itself). The DR-029 deliberation in Session 11 reasoned through this with the bracketing argument (surrounding-interval snapshots from `capture.db` at analysis time are structurally stronger than a single fresh on-demand snapshot, because they tell us about market movement *around* the bet rather than at a single point) — Session 15's review is independent assessment of this deliberated decision.





### B.8 What this document does NOT contain

- It is not the data review scoping. That's post-Session-15 work, after the multi-agent review approves direction.
- It does not specify new data fields to capture. The environmental scan in B.5 is the methodology for surfacing those during the data review.
- It does not pre-empt the deferred bet-schema-simplification question. The current schema is documented; the simplification is flagged but not adopted.
- It is not exhaustive of v3's queries against the data layer. It captures the structural shape of v3's data dependence; specific query patterns surface during build.

---
