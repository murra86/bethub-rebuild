# Data layer (current)

*Companion document for the multi-agent governance review. Drafted Session 19 (2026-04-28). Descriptive — what `capture.db` and its data API do today, what fields are captured, what cadence runs in practice, what gaps exist. Framed for assessors reading without prior project context. Sits alongside `architecture_current.md` in the doc suite; extends that document's §5.1 into data-layer-specific detail without re-stating it.*

---

## 1. What this document covers

`architecture_current.md` describes v3's bet-data side — entities, event log, reconciliation surfaces, the cross-DB integration boundary. This document describes the *other* database in the two-database architecture: `capture.db`, the existing UK VPS racing-data capture system that v3 reads from but does not write to.

The framing is descriptive: what `capture.db` does today, not what v3 needs from it. The needs side lives in `v3_data_requirements.md` (B.1–B.6). The ask of this document is to give assessors the factual ground — what's actually being captured, at what cadence, with what coverage, with what gaps — so that the four review questions in `v3_data_requirements.md` (B.7) can be assessed against the actual data layer, not against an idealised one.

A **v3-stakes question for assessors** is surfaced in §8 alongside (not folded into) the four B.7 questions.

---

## 2. What `capture.db` is and where it runs

`capture.db` is a SQLite database running on a UK Hostinger VPS as part of an existing racing-data capture system. The system predates v3 by months and runs continuously. It has its own service (`racing-api.service` on the VPS) exposing a read-only HTTP data API, reached from the operator's local environment over an SSH tunnel at `127.0.0.1:8400`.

The capture system itself comprises:

- A Betfair time-series capture process polling the Betfair API on a tiered cadence for AU thoroughbred / harness / greyhound markets.
- A set of bookmaker scrapers (Entain, PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API) running on the same VPS, writing time-series price snapshots into `capture.db`.
- A race-metadata and race-results population path drawing from Racing API and result-source feeds.
- BSP capture post-jump.
- Daily calibration summaries and batch summaries derived from the time-series data.

The system was originally built to serve a multi-consumer ecosystem (Strategy 1, BetHub v2, the Racing EV model, AFL Edge). The actual current consumer state is described in §3 — it differs materially from the original framing.

**v3 does not own `capture.db`.** v3 reads via the data API; v3 does not write; v3 does not duplicate any of its data on the bet-data side beyond the single narrow DR-026 inline-snapshot exception. The cross-DB boundary discipline is locked in DR-027 / DR-028.

---

## 3. Current operational reality

Empirically verified during Session 18 (2026-04-28) via v2 codebase inspection (`api/racing.py`, `betfair_sync.py`) and `bethub.log` review:

**capture.db has no real active consumer at present.** The originally-framed multi-consumer ecosystem is not the current state. Strategy 1 is not yet operational. AFL Edge has been mothballed for months. The Racing EV model is not a live execution-time consumer. BetHub v2 has code wired to capture.db's data API in two places — the racing page and the betfair_sync settlement path — but in practice the SSH tunnel that v2 depends on for VPS reach has been unreachable continuously for at least six days at the time of this writing, with v2 logs showing health-check failures every 30 seconds throughout that window.

**v2 has been operating normally throughout the tunnel-down period.** Settlement goes direct to Betfair API rather than via VPS; the racing page isn't a primary operator surface. The launchd plist `com.bethub.vps-tunnel.plist` exists at `~/Library/LaunchAgents/` but isn't currently running. Tunnel restart is a likely-easy fix, but the operational signal is what matters: VPS unreachable for a week, no one notices.

**v3 is the first execution-time consumer that will actually exercise the integration.** v3's design has v3 reading `capture.db` on every bet log, on every settlement, in burst review. The `bf_snapshot_unavailable = true` graceful-degrade flag in DR-026 is currently theoretical insurance against a failure mode v2 has demonstrated is the empirical default rather than the exception. v3 takes on a continuous-availability requirement that v2 has not enforced — monitoring, auto-restart, alerting — and that requirement is currently unspecified.

**Operator familiarity has decayed alongside consumer absence.** The operator does not currently have confident knowledge of which `capture.db` fields are reliably populated, what cadence holds in practice versus what was specified at build time, or where the rough edges sit. This is the same root cause as the reachability gap: a data layer with no real active consumer accumulates uncertainty about its own state. The DR-029 data review is the structural answer — sections 4–6 below frame each field set as schema-defined with empirical state requiring verification during that review, rather than asserting current population state.

**Why this matters for assessors.** The architectural elegance of the two-database split (DR-027) and the integration boundary discipline (DR-028) sits on top of an availability assumption that has not been operationally validated, and a population-state assumption that has not been recently re-verified. v3 building on top of an integration the operator has not had to keep alive — and whose contents the operator no longer holds in working memory — is a real risk worth naming explicitly. §8 carries this through as a v3-stakes question.

**Analytical-versus-operational distinction (operator-discovery, Session 19).** Re-encountering documented cadence during Session 19 review surfaced a structural distinction the existing documents have quietly conflated. `capture.db` is built as an *analytical* data layer — polled snapshots written to a database for post-hoc bracketing, modelling, and calibration, with retention indefinite and latency tolerance in minutes-to-hours. v3 also has an *operational* live-pricing need — sub-second prices in the burst window for in-the-moment decision-making, with retention zero and latency tolerance sub-second. These are different consumers with different requirements, not the same data path with a tunable cadence dial. For Betfair, the operational pattern is uncontroversial — Betfair offers a Streaming API designed exactly for this and a direct connection from v3 is the obvious shape. For soft-book operational live pricing, no equivalent pattern exists — see §5.4. Neither operational surface is currently designed in v3, and the distinction sharpens the v3-stakes question in §8.

---

## 4. Race-data fields captured (schema-defined)

Indexed primarily by Betfair `market_id` (event identifier) and resolvable by the natural-key tuple `(race_date, venue_normalised, race_number)`. Scope: AU thoroughbred, harness, and greyhound racing. NZ is not currently in scope.

The fields below are what the schema defines. Empirical population state — which fields are reliably populated, which are sparse, which are nominally present but unusable — is not currently held with confidence by the operator and will be re-verified in the DR-029 data review.

### 4.1 Race metadata

Schema-defined fields per `v3_data_requirements.md` B.2.1: `race_class`, `race_distance` (metres), `race_surface` (turf / synthetic / dirt), `race_group` (G1 / G2 / G3 / Listed / Stakes / Handicap), `track_condition` at jump, `track_type` (flat / circle / trotting / pace), `scheduled_jump_time`, `actual_jump_time` (post-jump), `race_code` (thoroughbred / harness / greyhound), `venue` (canonical), `race_number`.

### 4.2 Runner-level metadata

Schema-defined fields per `v3_data_requirements.md` B.2.2: indexed by Betfair `selection_id`. Runner name (canonical, with operator-friendly normalisation), barrier / box / draw, weight carried (where applicable), jockey / driver / trainer, form indicators where Racing API exposes them, finishing position (post-result), beaten margin (post-result), BSP, scratching events with timestamp (`scratched_at`, `late_scratch` flag).

### 4.3 Race results

Schema-defined fields per `v3_data_requirements.md` B.2.3: finish positions for all starters, dead-heat indication, stewards' inquiry status (where reported), margin between positions, race time / sectional times where source exposes them, result `observed_at` timestamp, source identifier (Betfair / Racing API / Racing Australia / Racenet).

Auto-settlement reads here: v3's `bet_settled` for racing bets uses VPS race result as canonical for "what happened in the race." Result-source-disagreement handling and lag-from-finish-to-population are empirical-state items for DR-029 verification.

### 4.4 Betfair time-series snapshots

Per runner per in-scope market, snapshot fields: best back price + size, best lay price + size, top-3 back depth, top-3 lay depth, total matched, snapshot timestamp.

DR-020 documented cadence (tiered): 5-minute standard outside the pre-jump window; 60-second pre-jump intensive in the 5-minute window before scheduled jump; 60-second in-running; 2-minute settlement checks. Whether this cadence still holds in practice is one of the central DR-029 verification items, given that the analytical-bracketing argument in DR-029 leans on pre-jump cadence being tight enough.

**Operator-flagged concern, surfaced during Session 19 review:** the documented 60-second cadence near jump and in-running prompted re-examination, and the primary realisation is structural rather than tuning-related. `capture.db` is an analytical capture layer; the operational live-pricing need v3 has near jump (per §3) is a separate concern that this layer was not built to serve and should not be tuned to serve. There is also a secondary, narrower analytical-bracketing concern — if the bracketing snapshots either side of a logged bet placed in the last 60 seconds before jump are 60 seconds apart in a fast-moving market, the bracket may be too wide to be analytically meaningful. The bracketing concern is real but secondary; whether it materially affects v3's analytical needs depends on how often racing bets are actually placed inside that window in operator workflow, which is a DR-029 verification item. The structural concern — that operational live pricing is a separate need requiring a separate design — is the load-bearing one and is carried through §3 and §8.

### 4.5 BSP and calibration data

BSP per runner per race (post-jump). Daily calibration summaries and batch summaries are produced as derived outputs of the time-series data. Coverage reliability across the three codes is a DR-029 verification item.

---

## 5. Bookmaker-data fields captured (schema-defined)

Soft-book time-series snapshots are captured via dedicated scrapers running on the same VPS, writing into `capture.db` alongside the Betfair time-series data. Same caveat as §4 applies: the field and scraper sets below are schema- and configuration-defined; current empirical state (which scrapers are actually running, which have died, which produce reliable data) is a DR-029 verification item.

### 5.1 Scrapers (configuration-defined)

Per `v3_data_requirements.md` B.2.5 and DR-014: Entain (Ladbrokes/Neds), PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API. TAB API was flagged as "needs TAB Studio registration" in earlier context and has not been confirmed live. Cloudflare-blocked books (BetRight, Betr, PalmerBet, Dabble, and Sportsbet non-racing) are out of scope and not captured.

The VPS scrapers route through a Decodo rotating residential proxy, which is what enables capture from books that would otherwise block standard datacenter IPs. The Cloudflare-blocked books listed above remain out of scope despite the proxy because they apply additional protections (browser fingerprinting, behavioural challenges) that Decodo alone does not bypass — they require headless-browser scraping infrastructure not currently in place.

### 5.2 Cadence (specified)

Documented cadence: 5-minute standard, 90–120-second intensive in the pre-jump window. Snapshot fields: best price per runner per market with timestamp, scrape source, race natural key. Cadence sufficiency for DR-014's hot-path use case (in-burst soft-book price context displayed alongside planned promo actions) is a central DR-029 verification item — the test is whether the cadence is empirically tight enough for the operator to trust the displayed price against what's actually on the book at decision time.

### 5.3 Sports markets

Sports markets (AFL, NRL, NBA, soccer leagues, others on the day-one v3 list per DUR §4) are **not captured** today. This is the largest known gap and is the first item in the upcoming DR-029 data review.

### 5.4 Operational soft-book live pricing (v3 need not currently designed)

v3's intended use case includes displaying soft-book prices alongside Betfair in the burst UI, both as a comparative tool and as a decision-support layer for identifying favourable EV bets at the moment of decision. This is an *operational* need (sub-second, in-the-moment, no retention requirement), distinct from the analytical soft-book capture in `capture.db` (which is the right tool for post-hoc analysis but the wrong tool for in-burst live pricing).

The operational soft-book live-pricing case is structurally harder than the operational Betfair case. Betfair offers a Streaming API designed for sub-second consumption; soft-books actively resist scraping and especially resist the high-cadence scraping operational decision-making would require. Frequency-blocking is the primary risk — current VPS scrapers work at 5-minute / 90–120-second cadence partly because that volume hides in normal-user traffic patterns; per-second cadence across multiple books simultaneously near every AU race jump is a different request-volume profile that residential proxies alone may not protect against. Proxy economics shift accordingly. The detection arms race is asymmetric — books iterate detection in days, operator finds out about a block when prices stop flowing during the burst window when the cost of degraded data is highest.

Four plausible architectural responses worth weighing:

- **Option A — in-scope, build operational soft-book layer.** Separate higher-cadence scraping infrastructure with appropriate proxy investment (likely a different proxy product than current Decodo rotating residential — sticky sessions, larger pool, or both). Maximum operational leverage, maximum engineering investment, real ongoing block-risk during burst windows.
- **Option B — out-of-scope, display last-known soft-book price from `capture.db` with explicit staleness indicator.** Burst UI shows Betfair live (sub-second from Streaming API) and soft-book prices flagged "as-of T-90s" or similar. Operator factors staleness into the decision. Lowest engineering cost, no block-risk, but degraded comparative decision-support — short-lived value windows on the soft-book side go unobserved.
- **Option C — on-demand fresh scrape per burst review.** When operator initiates a burst review on a specific race, v3 triggers a one-shot fresh scrape across in-scope books for that race only, at the moment of review. Lower request volume than continuous high-cadence (per-race-on-demand vs every-race-continuously) but still higher than current and still adversarial; middle-ground viability is uncertain.
- **Option D — third-party odds-feed vendor.** Subscribe to a commercial odds aggregator that already does the high-cadence soft-book scraping. Trade-offs: ongoing subscription cost vs one-off engineering cost, data-quality and book-coverage dependent on the vendor, lock-in risk if v3 builds operational features around their API and they raise prices or shut down, and whether available aggregators cover the specific books v3 needs (a vendor with 80% coverage of v3's day-one book list is meaningfully less useful than 100%). Operator pre-decision-homework worth doing: scan the market to identify whether a vendor exists that covers v3's specific book list at acceptable cost. If yes, the soft-book operational question shifts from "is it viable" to "build vs buy with known cost on both sides." If no, A/B/C are the only real options.

The choice among A/B/C/D is non-trivial and has downstream implications for v3's burst UI, decision-support story, ongoing operational risk profile, and the v3-stakes-question landscape in §8. The question is surfaced for the multi-agent review in §8 (sub-question 6b).

---

## 6. Known gaps

The named gaps below are operator-confirmed. The unnamed gaps — fields that look populated in the schema but aren't usable in practice, scrapers nominally running but producing garbage in specific conditions, edge cases worked around silently — are not currently held with confidence by the operator (per §3) and are themselves the substance of what the DR-029 data review verifies.

**Sports markets entirely absent from `capture.db`.** Day-one v3 sports bets log with `bf_snapshot_unavailable = true` until a sports-capture extension is built — first item in the upcoming DR-029 data review. The day-one v3 sport scope per DUR §4 (NBA, NBL, International Cricket, AFL, NRL, Tennis majors, NHL, MLB, NFL, MMA, plus EPL, La Liga, Ligue 1, Serie A, MLS) is the target of the extension.

**Soft-book cadence sufficiency for DR-014's hot-path is unverified.** The 5-minute standard / 90–120-second intensive cadence has not been empirically tested against the operator's actual in-burst decision-making latency. Verification is a DR-029 data-review item.

**Cloudflare-blocked books are out of scope.** Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble require headless-browser scraping infrastructure not currently in place. Operator-confirmed out of scope per DR-029 ("an entire project in itself").

**NZ thoroughbred / harness / greyhound is out of scope day-one.** Re-asked as a sub-question in the DR-029 data review per Session 13 revision 5; folded into B.7 #3 footnote in `v3_data_requirements.md`.

**Account-isolation layer formalisation is out of scope** for the DR-029 data review per operator decision. The TP-Link MiFi + AdsPower + SOCKS5 infrastructure remains operator-managed manual workflow.

**Empirical population-state visibility into `capture.db` itself is a gap.** As §3 notes, the operator does not currently hold confident knowledge of which fields are reliably populated, which are sparse, where the rough edges sit, or whether documented cadence still holds. The DR-029 data review is the structural answer; this document does not paper over the gap by asserting state the operator cannot confirm.

---

## 7. Data API contract surface today vs DR-029 requirements

The data API today is `racing-api.service` running on the VPS, reached at `127.0.0.1:8400` over SSH tunnel from the operator's local environment.

**What exists today.** A read-only HTTP API consumed by v2's `vps_client` module. v2's calls cover race metadata, latest snapshot lookup for `(market_id, runner_id)`, scratch state, and race result. The interface is implementation-coupled — schema lives in v2's client code rather than in formal contract documentation maintained alongside the data layer.

**What DR-029 requires.** A versioned contract (`/v1/race/{event_id}/metadata`, `/v1/race/{event_id}/snapshot/latest`, `/v1/race/{event_id}/result`, etc.), backward-compatible additions discipline, breaking changes only via new version, deprecation policy with notice period, contract documentation living with the data layer not with v3, schema-drift surfacing in `vps_client` (one file) per DR-028 forbidden pattern 3.

**Gap.** Today's interface is a working integration, not a versioned and documented contract. DR-029 calls for the lift to versioned-and-documented before v3 build begins. The lift is in scope for the post-multi-agent-review data review and is structurally important: DR-028's forbidden pattern 3 ("no second integration point") is operationally meaningful only when there *is* a documented contract for `vps_client` to be specified against.

**Periodic-only API pattern (DR-029).** Today's API returns most-recent stored snapshot from `capture.db` with timestamp. v3's design holds this pattern — no on-demand fresh-now endpoint, analytical bracketing via surrounding-interval snapshots read from `capture.db` at analysis time. The pattern is locked in DR-029 and is one of the four B.7 review questions.

---

## 8. v3-stakes questions for assessors

Two questions, surfaced separately from the four B.7 review questions in `v3_data_requirements.md`. Both operationally discovered during Sessions 18–19, framed here for the multi-agent review.

### Question 1 — Reachability and continuous-fitness discipline

v3's two-database architecture (DR-027) and integration boundary discipline (DR-028) place a continuous-availability requirement on `capture.db` and its data API. v3's design calls VPS on every bet log, on every settlement, in burst review. The graceful-degrade flag in DR-026 (`bf_snapshot_unavailable = true`) is the structural fallback when VPS is unreachable.

**The empirical context, two surfaces.** First, *reachability*: v2 has been operating normally for at least six continuous days with the SSH tunnel down and no successful VPS calls in that window. v2's wired code paths exist; v2 doesn't actually need them in execution-mode operation. Tunnel restart is a likely-easy fix that nobody has had to make, because nobody has noticed. Second, *population-state visibility*: the operator does not currently hold confident knowledge of which `capture.db` fields are reliably populated or whether documented cadence still holds in practice (§3 and §§4–6). Both surfaces share a root cause — the data layer has had no real active consumer, so neither its availability nor its contents have been operationally pressure-tested.

**What this means for v3.** v3 will be the first execution-time consumer that actually requires the tunnel to be up *and* requires the data inside `capture.db` to match what v3 thinks it's reading. v3's continuous-availability and continuous-fitness requirements are *new* operational requirements, not inherited ones. The infrastructure to enforce them — monitoring, auto-restart, alerting, escalation, and ongoing data-fitness verification past the one-off DR-029 review — is not currently specified.

**The ask of assessors.** Does v3's reachability-and-fitness discipline need to be specified before v3 build, alongside the data-layer fit-for-purpose review? Or are graceful-degrade and a one-off pre-build review sufficient — i.e., is the design genuinely robust to the same "VPS unreachable for a week, no one notices" pattern v2 has demonstrated, and to the slower drift of `capture.db` schema/cadence/coverage over v3's operational lifetime, or do these patterns indicate a structural gap in v3's design that the graceful-degrade flag and one-off review together paper over?

### Question 2 — Operational live pricing, Betfair and soft-book (analytical-versus-operational distinction)

Surfaced during Session 19 review. v3's design has not currently distinguished between *analytical* data needs (post-hoc bracketing, modelling, calibration — served by `capture.db`) and *operational* data needs (sub-second live pricing in the burst window for in-the-moment decision-making — not served by `capture.db`, and not currently designed). Per §3 and §§4.4 / 5.4, these are different consumers with different requirements; trying to serve both from the same polled-snapshot-into-SQLite path pulls the design in directions it wasn't built for. The operational layer is currently un-designed and splits cleanly into two different problems.

**6a. Operational Betfair live pricing.** v3 needs sub-second Betfair prices in the burst window for racing decisions near jump and for any in-running consideration. The pattern is uncontroversial — Betfair's Streaming API is designed for this — but the design move itself has not been made. Should v3's design specify a direct Streaming API connection from v3 (a third data surface alongside v3's own DB and `capture.db`)? How does that interact with DR-026 (which currently sources at-log-time `bf_snapshot` from `capture.db` — would the live feed be a better source when available?), DR-027 (the two-database split — does a non-database operational feed sit cleanly alongside it?), DR-028 (the one-integration-point discipline — does it extend to operational integrations or remain race-data-specific?), and B.7 #5 (periodic-only API pattern — does it become structurally cleaner if operational needs are served elsewhere)?

**6b. Operational soft-book live pricing.** v3's intended burst UI displays soft-book prices alongside Betfair as a comparative tool and EV decision-support layer. The operational pattern is structurally harder than the Betfair case — soft-books actively resist high-cadence scraping, frequency-blocking risk is real, and four plausible architectural responses exist (per §5.4): (A) in-scope, build operational soft-book layer with appropriate proxy investment; (B) out-of-scope, display last-known from `capture.db` with explicit staleness indicator; (C) on-demand per-burst-review fresh scrape; (D) third-party odds-feed vendor. The choice has meaningfully different downstream implications for engineering cost, ongoing block-risk, data quality, decision-support quality, and vendor lock-in. Assessor reasoning on the trade-offs — and on whether the question can or should be answered before v3 build vs deferred — would be valuable. Operator pre-decision-homework on whether suitable vendors exist for the specific v3 day-one book list is in flight separately and may inform the answer.

### Relationship to B.7

Both questions are independent of the four B.7 questions in `v3_data_requirements.md` but interact with them — Question 1 with all four (the data layer's continuous fitness underpins every B.7 answer); Question 2 particularly with #5 (the periodic-only API pattern argument depends on operational needs being served elsewhere; if they're not, periodic-only has to do double duty and the answer to #5 becomes harder). Assessors are invited to weigh both questions alongside the existing four.

---

## 9. Document scope notes

This document is descriptive of `capture.db`'s current state. It does not propose changes; it does not specify the data review's scope (that's the post-multi-agent-review work per DR-029); it does not enumerate v3's data needs (that's `v3_data_requirements.md`). The full DR-029 data review will produce a written audit covering race-data fit-for-purpose, sports-market layer addition, periodic-only API pattern, settlement model, external analytics environmental scan, and API contract versioning — informed by the multi-agent review's outputs and any direction adjustments those outputs prompt.
