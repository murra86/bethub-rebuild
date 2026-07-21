# §2.7 — API contract versioning

**Locked:** Session 75 (in progress, drafting from 2026-05-04 11:56 ACST).
**Scope reference:** `dr029/dr029_scope.md` §2.7.
**Load-bearing inputs:** §2.6 §5.1 (`betfair_client` settlement-read contract specification), §2.9 §6.1 (`vps_client` and `betfair_client` v1.0 contracts substantially specified), §2.4 (Betfair Streaming connection shape; cadence parameters pending Fix 4).
**Load-bearing outputs:** locked v1.0 contracts for `vps_client` and `betfair_client`; schema-evolution policy; deprecation framework; named contract documentation location per module; substrate for DR-029 close-out governance paragraph.
**Governing decision records:** DR-027 (two-database architecture: BetHub owns operational state, capture.db owns analytical/source data, no shared tables, integration by reference only), DR-028 (cross-database integration boundary discipline: no caching, no denormalisation, no second integration point, four lean structural protections), DR-029 (data-layer fit-for-purpose review before v3 build — active arc).

---

## §1 — Framing

### §1.1 What §2.7 specifies

API contract versioning across two integration-module contracts:

- **`vps_client`** — v3's read interface against `capture.db` analytical-line data on the VPS. Owned by v3; sole consumer of `capture.db` per DR-027 / DR-028.
- **`betfair_client`** — v3's interface against the Betfair Exchange and Streaming APIs. Covers operational-line live pricing, sports market structure reads, settlement reads, and identity-resolution checks per §2.6, §2.9, §2.4.

§2.7 locks the **versioning discipline** for both contracts at v1.0 — what "versioned" means here, how schema evolves over time, how breaking changes are handled, where the contract documentation lives. §2.7 does **not** re-specify the contract shapes themselves; the shapes are already locked across §2.6 and §2.9. §2.7's job is the wrapper that turns the specified shapes into durable contracts that v3 build proper can consume safely and that survive schema evolution without forcing v3 churn.

### §1.2 Why versioning matters here

v3 build proper begins once DR-029 closes. Once v3 is running against v1.0 of both contracts, contract changes have downstream cost — every breaking change forces v3 code adjustment. The versioning discipline locked here protects v3 from that churn:

- **Backward-compatible additions stay free.** Fields can be added to a contract response without v3 ever needing to know — v3 reads what it knows, ignores what it doesn't.
- **Breaking changes are explicit.** A breaking change forces a new version of the affected contract, parallel running of v1 and v2 for a defined window, then retirement.

The discipline matters in different ways for the two contracts:

- **`vps_client` discipline matters more locally.** `capture.db`'s schema is BetHub-controlled and will evolve with operational discovery — new fields surfaced by §2.10 inventory writeup, new analytics signals identified post-build, new soft-book sources when the operational soft-book layer eventually returns to scope. The versioning discipline shields v3 from `capture.db` schema churn that BetHub itself drives.
- **`betfair_client` discipline matters as an external buffer.** Betfair's API shape is Betfair-controlled — they change their own API on their schedule. The versioning discipline isolates Betfair-driven changes inside `betfair_client` so v3's racing page, sports page, and settlement worker don't have to track Betfair API version churn.

### §1.3 Two contracts, two failure modes guarded against

**`vps_client` failure mode without versioning discipline.** Schema drift propagates into v3 — v3 reads start breaking silently when `capture.db`'s schema shifts (a renamed field, a moved type, a removed column). Guarded by: versioned endpoint pattern + schema-drift surface localised to `vps_client` (one file owns the boundary; v3 modules don't see the schema directly).

**`betfair_client` failure mode without versioning discipline.** Betfair changes their API, v3 starts crashing or misreading. Guarded by: the same one-file boundary + explicit handling of Betfair-side breaking changes via new `betfair_client` version + parallel running window during transition.

Both failure modes are real — `capture.db` schema will evolve as operational discovery runs through v3 build proper, and Betfair has historically released breaking API changes (e.g. Streaming API auth-pattern revisions, new market-status fields). The versioning discipline doesn't prevent the changes; it contains their blast radius.

### §1.4 Load-bearing inputs

- **§2.6 §5.1** — `betfair_client` settlement-read contract specification. Five fields named: market state (`OPEN`/`SUSPENDED`/`CLOSED`), market settlement state (`settledTime`), per-runner settlement status (`WINNER`/`LOSER`/`REMOVED`), market void status, per-runner void status. §2.7 wraps this shape in versioning policy.
- **§2.9 §6.1** — `vps_client` and `betfair_client` v1.0 contracts substantially specified. Three `betfair_client` surfaces: (a) sports-line query at bet entry, (b) `marketTime` read, (c) passive identifier-resolution check. `vps_client` shape against locked `capture.db` data contract. §2.7 wraps these in versioning policy.
- **§2.4** — Betfair Streaming connection shape. The subscribe / stream-message-handle pattern is part of `betfair_client` v1.0 contract. Cadence parameters (subscribe interval, reconnect backoff, heartbeat threshold) are pending Fix 4 brief drafting; cadence is operational tuning, not contract shape, so §2.7 can lock `betfair_client` v1.0 today.
- **DR-027 / DR-028** — the cross-database integration boundary discipline that §2.7's versioning wraps. DR-027 establishes that v3 reads `capture.db` only via `vps_client` (no shared tables, integration by reference only); DR-028 establishes the four lean structural protections (no caching, no denormalisation, no second integration point, one-file boundary). §2.7's versioning discipline operates inside that boundary.

### §1.5 Load-bearing outputs

- **Locked v1.0 contracts for `vps_client` and `betfair_client`** — ready for v3 build proper to consume. The contracts are immutable at v1.0; subsequent versions are issued explicitly under the schema-evolution policy.
- **Schema-evolution policy applicable to both contracts** — backward-compatible additions in-place, breaking changes via new version only, deprecation framework with notice period.
- **Deprecation framework** — what triggers a new version, what the parallel-running window looks like, how v3 transitions from v1 to v2 of a contract.
- **One named documentation location per contract** — single source of truth for each contract's shape and version history. Lives with the data layer (in the rebuild folder), not scattered across v3 code.
- **Substrate for the DR-029 close-out governance paragraph** — DR-029 closes by naming the discipline that survives the close into v3 build proper. §2.7's versioning discipline is one of the named pieces (alongside the three pieces of debt, the periodic data-fitness re-verification, the operational/analytical line discipline).

---

## §2 — `vps_client` v1.0 contract

### §2.1 What the contract exposes

`vps_client` is v3's read interface against `capture.db` analytical-line data on the VPS. Per DR-027, v3 does not read `capture.db` directly; per DR-028, `vps_client` is the only file in v3 that knows `capture.db`'s schema. The contract exposes a small set of named call surfaces, each returning typed data plus a freshness envelope (per §2.3 below).

Named call surfaces at v1.0:

- **Race metadata reads** — race-level fields (classification, distance, surface, group/tier, track condition, jump times, code, venue, race number) keyed on Betfair event identifier. Resolves the canonical race identity at read time.
- **Runner metadata reads** — runner-level fields (name, barrier, weight, jockey/driver/trainer, form indicators, scratching status) keyed on Betfair selection identifier within a race.
- **Results reads** — finish positions, beaten margins, BSP, dead-heat indicator, stewards' status, sectional times where available. Source identifier carried with each result row so v3 can distinguish Racing API result from Betfair Win settlement.
- **Bracketing reads** — pre-jump market snapshots over a parameterised window (e.g. 10 minutes pre-jump through 30 seconds post-suspension). Returns the time-series of price snapshots for analytical work — bet-card market curve display, post-hoc EV review, model calibration.
- **BSP / sp_near / sp_far reads** — Betfair starting price and projection-derived near/far estimates. Single-point reads keyed on race + selection.
- **Identifier-resolution reads (passive sanity check)** — per §2.9 surface (c). Given a Betfair `market_id` + `selection_id` recorded at bet placement, confirm the analytical-line resolution succeeds. Returns presence/absence + lag indicator if absent (so v3 can distinguish "ingestion lag" from "genuine join failure").

The actual call signatures, parameter types, and return shapes live in the contract documentation (per §1.5 and the documentation-location note in §4 below) — not in this brief. The brief names the surfaces; the contract specifies them.

### §2.2 Versioned endpoint pattern

Path-based versioning. Concrete shape: every call surface lives under a `/v1/` prefix. Examples:

- `/v1/race/{event_id}/metadata`
- `/v1/race/{event_id}/runners`
- `/v1/race/{event_id}/results`
- `/v1/race/{event_id}/bracket?from={ts}&to={ts}`
- `/v1/runner/{event_id}/{selection_id}/bsp`
- `/v1/identity/resolve?market_id={mid}&selection_id={sid}`

Rationale for path-based versioning over header-based:

- **Visible at the call site.** v3 code reads `vps_client.v1.race_metadata(event_id)` — the version is in the call shape, not buried in headers. Easier to grep, easier to migrate explicitly when v2 of the contract issues.
- **Parallel running is mechanically simple.** When v2 of a call surface issues, the v1 endpoint stays available unchanged. v3 modules migrate one call site at a time from `vps_client.v1.X` to `vps_client.v2.X` over the deprecation window. No conditional header logic, no fallback branches.
- **Documentation tracks paths cleanly.** One section of contract documentation per `/v1/` surface; v2 documentation appends without rewriting v1 history.

Header-based versioning was the obvious alternative (`Accept: application/vnd.bethub.v1+json`) but rejected — the visibility-at-call-site benefit outweighs the small protocol elegance loss. v3 is BetHub-internal; we own both ends of the call; we don't need the HTTP-purist versioning shape.

### §2.3 Staleness and unavailability signals — typed envelope on every return

Every `vps_client` call returns a typed envelope wrapping the data. Three top-level statuses:

- **`fresh`** — data is current to within the analytical-line's expected ingestion lag (per Fix 4 cadence design once it lands; provisionally ~60–120 seconds for live-capture-window data, ~24h for retrospective backfill data). Envelope shape: `{status: "fresh", as_of: <timestamp>, data: <typed-payload>}`.
- **`stale`** — data is present but lags expected freshness. Envelope: `{status: "stale", as_of: <timestamp>, lag_seconds: N, data: <typed-payload>}`. v3 receives the data and the lag indicator; UI surfaces (bet card, racing page) can render with a freshness badge.
- **`unavailable`** — data cannot be returned. Envelope: `{status: "unavailable", reason: <enum>, retry_after: <seconds-or-null>}`. Reasons enumerate: `vps_unreachable` (VPS down or network partition), `capture_db_locked` (write-side ingestion holding a lock), `not_yet_captured` (the requested data is within the ingestion-lag window — try again later), `not_in_capture_window` (the requested data falls outside `capture.db`'s captured range — e.g. pre-go-live race or post-retirement window), `genuine_absence` (the request resolved but no matching record exists — e.g. an event_id that doesn't correspond to any captured race).

The five `unavailable` reasons matter because v3 acts differently per reason:

- `vps_unreachable` → operational alarm, retry with backoff, surface "VPS connectivity lost" banner.
- `capture_db_locked` → short retry, no operator surfacing.
- `not_yet_captured` → pending state, retry on schedule.
- `not_in_capture_window` → terminal for this read, surface "outside captured range" if v3 cared.
- `genuine_absence` → terminal, surface "no record" cleanly.

The discipline: v3 modules never see raw `capture.db` query exceptions. Every exceptional case is mapped to a typed envelope status by `vps_client`, so v3 modules write exhaustive switch-on-status logic against a closed set of states.

### §2.4 Schema-drift surface localised to one file (DR-028 protection)

`vps_client` is the **only** file in v3 that knows `capture.db`'s schema. v3 modules consume `vps_client`'s typed return shapes, never raw `capture.db` rows.

Concretely:

- The SQL queries against `capture.db` live inside `vps_client`. v3 modules call typed Python functions; they never write SQL or see column names from `capture.db`.
- The typed return shapes (Pydantic models or equivalent) are defined inside `vps_client`. v3 modules import the types from `vps_client`, but the field-to-column mapping is `vps_client`-internal.
- When `capture.db`'s schema shifts (a column rename, a type change, a new field), the change touches `vps_client` only. v3 modules see no change unless the typed return shape itself changes — and a typed return shape change is a versioning event (§4 schema-evolution policy).

This is the DR-028 "no second integration point" protection in concrete form. The cost-benefit: a single boundary file becomes large and dense, but the alternative — `capture.db` schema knowledge scattered across v3 modules — is the v2 failure mode the rebuild exists to fix.

### §2.5 What's deliberately not in `vps_client` v1.0

Five categories explicitly out of scope:

- **Operational reads** — live pricing, real-time market state, current burst-window snapshots. These go through `betfair_client` direct per the operational/analytical line discipline (Cat 4 of `standing_instructions.md`). `vps_client` reads the analytical store; live reads bypass it.
- **Writes to `capture.db`** — v3 does not write to the analytical layer per DR-027. `capture.db` is owned by the analytical-line capture pipeline on the VPS; v3 is read-only against it.
- **Soft-book operational reads** — deferred per `dr029_scope.md` §2.5 / §3.11. The operational soft-book layer is not part of v3 day-one; no `softbook_client` analogue exists. When the operational soft-book layer eventually returns to scope as a fresh DR, it specifies its own interface contract — not part of `vps_client`.
- **Analytics-derived fields** — fields that are computed at read time from `capture.db` raw data per the §2.8 bet-schema discipline (resolved-at-read, not stored on the bet record). These computations live in v3's analytical-derivation layer, not in `vps_client`. `vps_client` returns the raw inputs; v3's derivation layer composes them.
- **Sports analytical reads** — sports has no `capture.db` analytical store per `dr029_scope.md` principle 1.3 (racing-only analytical store; sports is operational-only). `vps_client` exposes no sports surfaces in v1.0. Sports historical data, when needed, sources from public/commercial archives separately (AFLTables, Squiggle, Fryzigg, NRL equivalents) — not part of `vps_client`.

---

## §3 — `betfair_client` v1.0 contract

### §3.1 What the contract exposes

`betfair_client` is v3's interface against the Betfair Exchange and Streaming APIs. Per DR-028, `betfair_client` is the only file in v3 that knows Betfair's API shape; v3 modules consume `betfair_client`'s typed return shapes, never Betfair's raw responses. The contract covers six categories of surface — five read categories plus one write category — at v1.0.

**Read surfaces:**

- **Operational live-pricing reads** — racing page and sports page burst-window reads. Per-market price ladders, total matched, market state. Sub-second cadence in burst windows; polling cadence outside burst windows. Cadence parameters are Fix 4 (pending); the contract shape is locked here.
- **Settlement reads (per §2.6 §5.1).** Five fields: market state (`OPEN`/`SUSPENDED`/`CLOSED`), market settlement state (`settledTime`), per-runner settlement status (`WINNER`/`LOSER`/`REMOVED`), market void status, per-runner void status. Plus the three count fields generalised from the same full-market-book read (`dead_heat_count`, `removed_runner_count`, `unexpected_state_count`).
- **Sports-line query (per §2.9 surface (a)).** At sports bet entry, given a fixture, return all market variants offered (handicap/total line values) so the operator can pick the line they bet at the soft book and v3 records the corresponding Betfair `market_id`.
- **Scheduled-time reads (per §2.9 surface (b)).** `marketTime` read for individual markets — used at bet placement-time to confirm scheduled start is plausibly in the future given placement timestamp (the §2.9 surface (b) sanity check).
- **Identifier-resolution checks (per §2.9 surface (c)).** Passive sanity check at bet logging time — confirm the Betfair `market_id` + `selection_id` exists in the live API state. Distinct from the `vps_client` analytical-side identifier resolution; this one runs against Betfair direct.

**Streaming surface:**

- **Streaming connection (per §2.4).** Subscribe / stream-message-handle pattern for sub-second exchange pricing in burst windows. Connection management, authentication, subscription lifecycle, reconnection behaviour, message dispatch. Cadence parameters (subscribe interval, reconnect backoff, heartbeat threshold) deferred to Fix 4 — the contract specifies the connection *shape*, not the timing.

**Write surfaces (tagged distinctly per §3.5):**

- **Bet placement** — `placeOrders` equivalent. Place a bet at Betfair given market identity, selection identity, side (back/lay), price, stake.
- **Bet cancellation** — `cancelOrders` equivalent. Cancel an unmatched or partially-matched bet.
- **Bet replacement** — `replaceOrders` equivalent. Modify an unmatched bet's price (used in hedge-modal workflows).

### §3.2 Versioned endpoint pattern

Path-based versioning identical to `vps_client` (per §2.2 rationale). Every call surface lives under a `/v1/` prefix. Examples:

- `/v1/market/{market_id}/prices` (operational live pricing read)
- `/v1/market/{market_id}/settlement` (settlement read, full-market-book)
- `/v1/event/{event_id}/markets?market_type={MATCH_ODDS|HANDICAP|TOTAL}` (sports-line query)
- `/v1/market/{market_id}/scheduled_time` (`marketTime` read)
- `/v1/identity/check?market_id={mid}&selection_id={sid}` (live-side identifier resolution)
- `/v1/streaming/subscribe` (Streaming connection lifecycle)
- `/v1/orders/place` (bet placement)
- `/v1/orders/cancel` (bet cancellation)
- `/v1/orders/replace` (bet replacement)

Critical decoupling: **`betfair_client`'s versioning is independent of Betfair's own API versioning.** Betfair versions their API on their schedule; `betfair_client` v1.0 wraps whatever current Betfair API surfaces are needed today. When Betfair issues a breaking change to one of their surfaces, `betfair_client` absorbs that change internally without necessarily issuing a new `betfair_client` version — the wrapper's typed return shape can stay stable across Betfair internal churn. A `betfair_client` v2.0 is issued only when the v3-facing typed return shape itself changes (new field added in a way that's not backward-compatible, behaviour change in error semantics, etc.).

This decoupling is the core protection: v3 builds against `betfair_client` v1.0, and Betfair API churn is contained inside `betfair_client` for as long as the wrapper can absorb it. Forced Betfair-driven `betfair_client` version bumps happen, but they happen at the rhythm of v3-facing change, not Betfair-facing change.

### §3.3 Staleness, unavailability, and Betfair-specific signals

Same typed envelope as `vps_client` (per §2.3) — `fresh` / `stale` / `unavailable` plus typed reason enumeration. Three differences from `vps_client`:

**Difference 1: `stale` is rare on `betfair_client`.** The Betfair API responds with current state by definition (live API, not an analytical store). The `stale` status surfaces only in two cases — Streaming connection lag (heartbeat past expected interval but connection not yet failed) and rate-limit-induced delay where `betfair_client` had to back off and the response data may be a few hundred milliseconds older than ideal. Most `betfair_client` reads return either `fresh` or `unavailable`.

**Difference 2: Expanded `unavailable` reason enumeration.** `betfair_client` adds Betfair-specific reasons:

- `betfair_auth_expired` — session token expired, requires re-auth. v3 surfaces auth-recovery flow.
- `betfair_rate_limited` — Betfair-side rate limiting. `betfair_client` honours retry-after; v3 sees the back-off.
- `betfair_market_suspended` — market is in `SUSPENDED` state. Read succeeded, but the market isn't taking action. v3 distinguishes from `OPEN`/`CLOSED`.
- `betfair_streaming_disconnected` — Streaming connection lost. Reads can fall through to polling; bet placement and writes block until reconnected (per §3.4 below).
- `betfair_market_not_found` — `market_id` doesn't exist in current Betfair state. Distinct from `genuine_absence` because it can mean "market closed and aged out of the API window" rather than "never existed".
- `betfair_api_unreachable` — network partition or Betfair API down. Operational alarm.

Plus the shared reasons that apply to both contracts where relevant.

**Difference 3: Write-side reasons (tagged distinctly per §3.5).** Write surfaces have their own reason enumeration overlay:

- `betfair_write_rejected` — Betfair rejected the order at submission. Reason payload carries Betfair's rejection code (e.g. `INVALID_BACK_LAY_COMBINATION`, `BET_TAKEN_OR_LAPSED`, `RUNNER_REMOVED`, `MARKET_NOT_OPEN_FOR_BETTING`).
- `betfair_insufficient_funds` — placement failed due to account balance.
- `betfair_bet_placement_in_progress` — duplicate-submit guard. Concurrent placement attempts on the same market+selection within a debounce window are rejected.

Write-side reasons live in the same envelope but trigger different v3 handling — operational alarm for unexpected rejections, audit-trail entry for every placement outcome regardless of success/failure (for the "every bet whose outcome drives downstream behaviour is analysed as a single cycle" Cat 4 discipline).

### §3.4 One-file boundary against Betfair API churn (DR-028 protection)

`betfair_client` is the **only** file in v3 that knows Betfair's API shape. Same DR-028 protection as `vps_client` §2.4, applied to the operational-line side.

Concretely:

- The HTTP calls against the Betfair Exchange API live inside `betfair_client`. v3 modules call typed Python functions; they never see Betfair's raw JSON or construct Betfair's URL paths.
- The Streaming subscription and message dispatch live inside `betfair_client`. v3 modules subscribe via typed registration calls and receive typed price-update events; they never parse Betfair's Streaming protocol directly.
- The typed return shapes are defined inside `betfair_client`. When Betfair adds a field, removes a field, renames a field, or changes a field's semantics, the change touches `betfair_client` only. v3 modules see no change unless the typed return shape itself changes (which is a versioning event per §4).
- Auth handling — login flow, session token management, token refresh, session expiry — lives inside `betfair_client`. v3 modules never see auth state directly.

Read-write coupling at the boundary: per the operator confirmation that bet placement and reads share the same connection (one auth context, one connection pool, one rate-limit budget), `betfair_client` is one module covering both. The DR-028 "no second integration point" protection requires it — splitting reads and writes into two modules would create two boundaries against the same external API.

**Streaming-disconnect blocks writes.** When the Streaming connection is lost (`betfair_streaming_disconnected` status), `betfair_client` blocks bet placement attempts until the connection re-establishes. Rationale: bet placement during a streaming gap means v3 doesn't have current price visibility, and placing into stale prices is a money-risk failure mode. v3 surfaces "Streaming reconnecting — placements paused" to the operator; placement queue resumes on reconnect. This is a `betfair_client` v1.0 contract behaviour, not a v3-side decision.

### §3.5 What's deliberately not in `betfair_client` v1.0

Five categories explicitly out of scope:

- **Analytical reads** — historical price curves, BSP archives, post-jump market analysis. These go through `vps_client` against `capture.db` per the operational/analytical line discipline. `betfair_client` reads live state only.
- **Soft-book reads** — deferred per `dr029_scope.md` §2.5 / §3.11. No `softbook_client` analogue exists in v3 day-one.
- **Sports analytical capture** — `betfair_client` does not write to `capture.db` or any analytical store. Sports operational reads land in v3's session-local state (UI display, bet placement context) and are persisted only via the bet record's at-placement snapshot per §2.8.
- **Account management** — fund transfers, deposits/withdrawals, account settings, statement queries. Betfair's API exposes these but v3 day-one doesn't use them; account hygiene work is operator-side via Betfair's web UI. Returns to scope only if a future workflow surfaces a concrete need.
- **Market discovery beyond v3 day-one workflows** — Betfair's API exposes broad market discovery (`listMarketCatalogue` across all sports, all events). `betfair_client` v1.0 exposes only the discovery surfaces v3 day-one needs (sports-line query, racing page market list, sports page fixture list). Generic catalogue browsing is out of scope.

**Write-side tagging in contract documentation.** Per the operator confirmation that bet placement, cancellation, and replacement are part of `betfair_client` v1.0 but their failure-mode and audit-trail discipline differs from reads, the contract documentation tags these surfaces as the **write-side sub-category** of `betfair_client` v1.0:

- Distinct section in contract documentation covering placement / cancellation / replacement with their own failure-mode catalogue and audit-trail requirements.
- Distinct reason enumeration prefix (`betfair_write_*`) in the typed envelope so v3 modules can switch on read-vs-write outcomes without parsing reason names.
- Audit-trail requirement: every write-surface call produces a structured log entry (operator identity, timestamp, market+selection, side+price+stake, outcome+reason) regardless of success/failure. Failure outcomes are the substrate for the "single-cycle analysis" Cat 4 discipline (e.g. a placement rejection that's followed by a successful retry is one cycle, not two independent events).

The tagging is a documentation and discipline overlay; the module boundary stays at one file per DR-028.

---

## §4 — Schema-evolution policy

The policy applies identically to both `vps_client` v1.0 and `betfair_client` v1.0. One discipline, two contracts.

### §4.1 Backward-compatible additions in-place

The following changes are backward-compatible and require **no version bump**. They land on the existing version (`/v1/...`) directly:

- **New fields added to a typed return shape** — provided the field is optional (i.e. v3 modules ignoring it continue to function correctly). v3 build proper modules consume the fields they know; new fields are invisible to them until a deliberate refactor uses the new field.
- **New optional parameters on existing endpoints** — provided defaults preserve existing behaviour when the parameter is absent.
- **New enum values in returned status / reason fields** — provided v3 modules have an explicit fall-through case (e.g. a `default:` branch in a switch). The §2.3 / §3.3 reason enumerations are designed with fall-through expectation; new reasons land as additions.
- **New endpoints alongside existing ones** — entirely additive surfaces (e.g. a new `/v1/runner/{event_id}/{selection_id}/sectional_times` if sectional times surface as worth pulling). Existing endpoints stay unchanged.
- **Behaviour refinements that strictly relax existing constraints** — e.g. an endpoint that previously returned `genuine_absence` for some boundary case now returns valid data because the underlying coverage improved.

What this enables: post-v3-build operational discovery surfaces new fields, new Betfair API surfaces become useful, new sources land in `capture.db`. None of them force a version-bump dance. The contracts grow without breaking.

**Deferred capabilities — where they fit.** The capabilities flagged across DR-029 as "make space for later" land mostly as backward-compatible additions when they arrive:

- **§2.10 inventory writeup outcomes** — Betfair API fields currently uncaptured that prove worth capturing post-scan. Land as backward-compatible additions to `betfair_client` (live-side surfaces) and/or `vps_client` (analytical-side surfaces, after the capture pipeline is extended).
- **PASSIVE bet-delay model handling** (flagged §2.4 §15.4) — when v3.1+ surfaces it, lands as additions to `betfair_client`'s Streaming surface and reason enumeration.
- **CLV as analytical-layer signal** (post-DR-029) — lands as additions to `vps_client`'s analytical-derivation reads.
- **Operational soft-book layer** — does *not* land as `vps_client` or `betfair_client` extensions. Returns as a fresh DR with its own contract module (`softbook_client` or equivalent). Different shape; different policy applies to it independently.

The §2.7 policy is what makes these capacity rather than v1.0 content — the contracts can grow without re-versioning whenever the additions are backward-compatible. They are content of *future versions* only when the addition forces a breaking change (per §4.2).

### §4.2 Breaking changes via new version only

The following changes are breaking and require a **new version of the affected surface**. The policy is strict — no in-place breaking changes regardless of how minor they appear:

- **Removed fields** from a typed return shape.
- **Renamed fields** — even if the new name is "obviously the same thing".
- **Type changes** to existing fields (e.g. integer → float, single value → list, nullable → non-nullable, string → enum).
- **Semantic changes** to existing fields — same name, same type, different meaning (e.g. `placement_time` shifting from "wall-clock at placement" to "Betfair-acknowledged time").
- **Removed enum values** that v3 modules might have been switching on.
- **Removed endpoints** — even if the endpoint is "obviously redundant" with another.
- **Removed parameters** from existing endpoints.
- **Parameter type changes** on existing endpoints.
- **Behaviour changes that tighten existing constraints** — e.g. an endpoint that previously accepted some input now rejects it.

The discipline: when in doubt, treat as breaking. The cost of an unnecessary version bump is a documentation entry and a 90-day deprecation window; the cost of an in-place breaking change misclassified as backward-compatible is silent v3 module breakage.

When a breaking change is needed, the affected surface gets a new version — `/v2/...` alongside `/v1/...`. The v1 surface stays operational and unchanged during the deprecation window (§4.3). v2 introduces the breaking change. v3 modules migrate from v1 to v2 over the window (§4.5).

**Granularity:** versioning is per-surface, not per-contract. `betfair_client` can have `/v1/orders/place` and `/v2/market/{market_id}/settlement` simultaneously — bumping the settlement-read surface to v2 doesn't force a bump on the orders surface. This keeps the version churn proportional to actual change. The contract as a whole is "v1.0 with surface-level v2 additions"; only when the majority of surfaces have moved to v2 does it make sense to retire v1 contract documentation entirely (a documentation event, not a version event).

### §4.3 Deprecation framework

When v2 of a surface issues, v1 of that surface enters **deprecation**.

**Fixed deprecation window: 90 days from v2 issuance to v1 retirement.** Provisional length, set today on a one-operator project basis — long enough to avoid pressure-driven migration, short enough that parallel-version overhead doesn't accumulate. Revisit once v3 has been running long enough to know how often surface-level version bumps actually happen and what migration friction looks like in practice.

**During the deprecation window:**

- v1 of the surface stays fully operational. No behaviour changes; no error injection; no degradation. v3 modules running against v1 continue to function correctly.
- v2 is fully operational from issuance day one.
- v3 modules migrate per call site over the window (per §4.5).
- Contract documentation marks v1 as `deprecated, retires <date>` in the v1 section header.
- Operational logs emit a deprecation warning when v1 is called — surfaces in v3's log stream so unmigrated call sites are visible without forcing a runtime failure.

**At window end:**

- v1 of the surface is retired. The endpoint stops responding (or responds with `unavailable` reason `endpoint_retired`).
- Contract documentation moves the v1 section to a "retired surfaces" appendix (kept for historical reference; not removed entirely).
- Any remaining v3 calls to v1 fail explicitly. Operational alarm.

The 90-day window is a soft contract — if migration friction is higher than expected, the window extends by explicit operator decision. The policy is the default rhythm; the operator's call overrides per case.

### §4.4 Contract documentation location and discipline

**v1.0 location:** under `dr029/2_7_api_contract_versioning/`. Two files:

- `vps_client_contract.md` — `vps_client` v1.0 contract documentation.
- `betfair_client_contract.md` — `betfair_client` v1.0 contract documentation.

Each file is single source of truth for its contract.

**Post-DR-029-close relocation.** When DR-029 closes and v3 build proper begins, the contract documentation moves to a permanent v3-build location — likely a `contracts/` folder at the v3 project root, or equivalent. The relocation is part of the DR-029 close-out documentation pass. The §2.7 brief governs the documents during DR-029; the relocation is a documentation-housekeeping event, not a version event.

**Document shape — both audiences.** Each contract documentation file contains two sections:

- **Operator-readable summary at the top.** Plain language describing what each surface does, what data it returns at high level, what failure modes it has, what's deliberately not in v1.0. The section the operator reads at version bumps to confirm the change is what was intended. Cat 1 / Cat 4 plain-language discipline applies.
- **Developer-readable specification below.** Formal type signatures (Pydantic models or equivalent), OpenAPI-style endpoint definitions, full parameter and return-shape specs, full reason-enumeration definitions, error semantics. The section v3 build proper (and any future Code session) reads when implementing against the contract.

The two sections coexist in one file — the file is the contract; both sections describe it.

**Edit discipline.** Contract documentation edits are **governance events**, not casual changes:

- Backward-compatible additions land as in-place edits with a dated note in the version history section ("2026-MM-DD: added field `X` to `/v1/race/{event_id}/metadata` return shape").
- Breaking changes land as new version sections appended to the file, with v1 marked deprecated and retirement date set.
- Version history is **append-only**. Old version sections are never rewritten or removed (retired surfaces move to a "retired surfaces" appendix at retirement).
- Every edit is timestamped, attributed to the originating session or DR, and recorded in the version history section at the top of the file.

The discipline matches `decisions.md` — locked artefacts grow by amendment, not by rewrite.

### §4.5 Migration discipline

When v2 of a surface issues, v3 modules migrate per call site over the deprecation window. **Per-call-site, not all-at-once.**

**Migration sequence:**

1. v2 of the surface issues. Contract documentation updated; deprecation date set 90 days out.
2. v3 modules continue calling v1; v1 stays fully operational.
3. As v3 modules are touched for unrelated reasons (feature work, bug fix, refactor), call sites against the deprecated surface are migrated to v2 opportunistically. The deprecation warning in operational logs makes unmigrated sites visible.
4. At ~60 days into the window (one-third of the window remaining), audit remaining v1 call sites. If migration is on track, no action; if some call sites remain, schedule explicit migration work.
5. At ~80 days, all v1 call sites are migrated. Final v1 calls are removed from v3 code.
6. At 90 days, v1 retires per §4.3.

**Why per-call-site migration:** an all-at-once migration on v2 issuance creates a single high-risk change touching multiple v3 modules simultaneously. Per-call-site migration spreads the risk over the window, lets each migration land with its own testing context, and means a problem with one migration doesn't block others.

**Migration testing:** every migrated call site is exercised against v2 before the v1 call site is removed. The opportunistic-migration pattern means migrations land alongside other work that exercises the affected module — natural testing rather than dedicated migration test passes.

**Rollback:** if a v2 surface turns out to have a defect that v1 doesn't, the migration pauses. v3 modules already migrated stay on v2; unmigrated stay on v1; v2 fix issues; migration resumes. The 90-day window absorbs reasonable rollback time. If the defect is severe enough to force unmigrating, that's an operator decision, not a default policy step.

---

## §5 — What §2.7 closes for DR-029, what's deferred

### §5.1 What §2.7 locks as load-bearing contract

**v1.0 of both integration-module contracts:**

- **`vps_client` v1.0** — path-based versioning under `/v1/...`, six call-surface categories named (race metadata, runner metadata, results, bracketing, BSP / sp_near / sp_far, identifier-resolution), typed envelope on every return with three statuses (`fresh` / `stale` / `unavailable`) and five enumerated unavailability reasons, one-file boundary against `capture.db` schema (DR-028 protection), five out-of-scope categories.
- **`betfair_client` v1.0** — path-based versioning under `/v1/...` decoupled from Betfair's own API versioning, six surface categories named (operational live pricing, settlement reads, sports-line query, scheduled-time reads, identifier-resolution checks, Streaming connection) plus three write surfaces (placement, cancellation, replacement) tagged distinctly, typed envelope identical in shape to `vps_client`'s with expanded Betfair-specific reason enumeration, one-file boundary against Betfair API churn, streaming-disconnect-blocks-writes behaviour, five out-of-scope categories plus write-side documentation tagging.

**Shared schema-evolution policy:**

- Backward-compatible additions in-place (new optional fields, new optional parameters, new enum values with fall-through, new endpoints, behaviour relaxations) — no version bump required.
- Breaking changes via new version only (per-surface granularity — e.g. `/v2/market/{market_id}/settlement` issues independently of other `betfair_client` surfaces).
- 90-day deprecation window from v2 issuance to v1 retirement, provisional pending operational experience.
- Per-call-site opportunistic migration over the deprecation window.
- Contract documentation location and discipline — single source of truth file per contract, both-audiences shape (operator-readable summary + developer-readable specification), append-only version history, edits as governance events.

**Capacity for deferred capabilities:** the §4.1 backward-compatible additions policy is what makes deferred capabilities (§2.10 inventory writeup outcomes, PASSIVE bet-delay handling, CLV analytical signal, post-DR-029 monitoring, and others surfaced through DR-029) capacity in v1.0 rather than v1.0 content. Deferred capabilities land as additions when they arrive without re-versioning, except where the addition itself forces a breaking change.

### §5.2 What §2.7 explicitly does not specify

**Cadence parameters.** Subscribe interval, reconnect backoff, heartbeat threshold, polling-cadence-outside-burst-windows, settlement worker periodic verification cadence — these are operational tuning, set as parameters against `betfair_client` v1.0's contract shape rather than as part of the contract shape itself. Fix 4 (Racing API cadence design brief) covers the cadence design discipline; per-surface cadence parameters land as v3 build proper operational tuning.

**The actual call signatures, parameter types, return shapes, and field-level type definitions.** These live in the contract documentation files (`vps_client_contract.md` and `betfair_client_contract.md` — to be drafted as separate artefacts post-§2.7 per §5.4 below), not in this brief. §2.7 names the surfaces and locks the wrapper discipline; the documentation files specify the surfaces.

**Migration friction tolerance.** The 90-day deprecation window is provisional — set today on a one-operator project basis, revisited once v3 has been running long enough to know how often surface-level version bumps actually happen and what migration friction looks like in practice. §2.7 does not commit to 90 days as the long-run policy; it commits to 90 days as the v1.0 default with explicit revisit.

**Auth flow specifics.** Betfair session token management, refresh discipline, expiry handling — `betfair_client` v1.0 contract names auth handling as inside the boundary (per §3.4) but does not specify the auth flow shape. Auth flow lives in `betfair_client` implementation, not in the contract.

**Rate-limit budget allocation.** How `betfair_client`'s shared rate-limit pool divides across read surfaces, Streaming subscriptions, and write surfaces is implementation discipline, not contract shape. v3 build proper tunes the allocation against operational reality.

**Operational-soft-book contract shape.** Out of scope per §3.5 / `dr029_scope.md` §3.11. When the operational soft-book layer eventually returns to scope as a fresh DR, that DR specifies its own contract module (`softbook_client` or equivalent) with its own §2.7-style versioning policy applied independently.

### §5.3 What §2.7 unblocks

**v3 build proper can build against locked v1.0 contracts.** The wrapper discipline is locked; the contract shapes are locked across §2.6 / §2.9; the contract documentation files are the remaining writable specification work. Once those land (per §5.4), v3 build proper has a complete spec to build against.

**DR-029 close-out governance paragraph has a named discipline to point at.** §2.7's versioning discipline survives DR-029 close into v3 build proper. The close-out governance paragraph references §2.7 as one of the named pieces of discipline carrying forward — alongside the three pieces of debt (no test coverage, no migration framework, monolithic orchestrator file), the periodic data-fitness re-verification, and the operational/analytical line discipline.

**Future deferred-capability DRs have a versioning policy template to reuse.** When the operational soft-book layer returns as a fresh DR, when sports analytical capability is eventually built, when the analytics layer formalisation lands — each of these will need its own contract module with versioning discipline. §2.7's policy is the template; new DRs apply the same shape (path-based versioning, typed envelope, one-file boundary, backward-compat additions in-place, breaking-via-new-version, 90-day deprecation, both-audiences documentation, append-only history).

### §5.4 What §2.7 carries forward (non-gating)

**Contract documentation files themselves.** `vps_client_contract.md` and `betfair_client_contract.md` are the substantive specification work that §2.7 governs but does not draft. Carry-forward: drafted as separate artefacts post-§2.7. Likely shape — a Code-bound brief commissions Code to draft the developer-readable formal specification section against the §2.6 / §2.9 locked shapes; the operator-readable summary section drafts in Chat. The documentation files are required to land before v3 build proper begins; they are part of the DR-029 critical path even though §2.7 does not draft them.

**Post-DR-029 relocation of contract documentation to v3 project root.** Once DR-029 closes and v3 build proper begins, the documentation files move from `dr029/2_7_api_contract_versioning/` to a permanent v3 location (likely a `contracts/` folder at v3 project root). Documentation-housekeeping event, not a version event. Carry-forward: relocation lands as part of DR-029 close-out documentation pass, not as a separate work item.

**Revisit of 90-day deprecation window.** Set provisionally today; revisit once v3 has been running long enough to know how often surface-level version bumps actually happen. Trigger: first time the operator notices the deprecation window producing real friction (either too short — pressure-driven migration — or too long — parallel-version overhead accumulating). v3 operational parameter, not §2.7 amendment trigger.

**Auth flow implementation specification.** §2.7 names auth handling as inside the `betfair_client` boundary but does not specify the flow shape. Carry-forward: auth flow specification lands inside the `betfair_client_contract.md` developer-readable section when that file drafts, not as part of §2.7.

**Rate-limit budget allocation tuning.** Same shape — implementation discipline tuned against operational reality, not contract shape. Carry-forward: lands during v3 build proper as operational parameter tuning.

**Operational experience surfacing new edge cases.** As v3 runs, new contract-shape questions will surface — surface-level version bumps that arise from real Betfair API churn, deprecation-window friction patterns, undocumented Betfair behaviour discovered in production. Each lands as a §2.7-policy application or amendment, not as §2.7 spec drift.

### §5.5 What §2.7 does not unblock

**§2.10 (external analytics environmental scan inventory writeup).** Independent of §2.7. §2.10's deliverable is the inventory of Betfair API and Racing API fields available but not currently captured, with capture-cheap classification. §2.10 is the only remaining writable DR-029 stream after §2.7 closes.

**DR-029 close itself.** DR-029 closes when §2.10 has landed plus the contract documentation files (per §5.4) have landed plus the close-out governance paragraph has been written. §2.7 closes one of the four remaining DR-029 streams; it does not close DR-029.

**v3 build proper start.** Gated on DR-029 close (per `project_context.md` §1 and `dr029/dr029_scope.md` framing). §2.7 unblocks v3 build proper *at the contract level*, but v3 build proper does not start until DR-029 closes. The contract documentation files are part of that close.

**Operational soft-book layer.** Deferred per `dr029_scope.md` §3.11. Returns as a fresh DR (likely DR-031+) when strategy work surfaces concrete consumer surface requirements. §2.7's versioning policy will apply to that future DR's contract module independently when it lands; §2.7 does not unblock soft-book work.

**Sports analytical capability.** Out of scope per `dr029_scope.md` principle 1.3 and §3.7. Sourced from public archives when needed; not a `vps_client` or `betfair_client` extension. §2.7's versioning policy does not apply to sports analytical work because there is no v3 sports analytical contract.

**Burst-review triage workflow design.** Out of scope per `dr029_scope.md` §3.10. Downstream of DR-029 close — happens during v3 build proper when concrete reconciliation surfaces are flowing. §2.7 specifies the contracts the burst-review reads against; it does not specify the triage workflow itself.
