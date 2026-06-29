# External API resources

Reference doc for external API documentation feeding rebuild work (DR-029 §2.4 Streaming spec, §2.10 external analytics scan, Fix 4 cadence brief drafting) and downstream analytical work in `bethub-analytical/`.

**Last updated:** 2026-05-03 (Session 59 — Streaming API doc captured locally)

---

## 1. Betfair

The Betfair developer documentation lives on Atlassian Confluence. Three load-bearing entry points captured here.

### 1.1 Reference Guide

https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687473/Reference+Guide

Authoritative reference for the Exchange API. Covers endpoint specs, request/response schemas, projection sets, error codes, rate limits.

**Most relevant for upcoming rebuild work:**
- §2.4 Streaming spec — Stream API is documented separately from polling REST; the Reference Guide is the entry into the Exchange REST surface that complements it.
- Fix 4 cadence brief drafting — projection-set semantics, rate limits, response shape detail.
- §2.10 external analytics scan — full field menu for what the API exposes vs what the snapshot writer captures (probe report §3.3 lifted 8–9 fields; Reference Guide is the canonical source for the full list).

**On-disk page captures (Path A on-demand fetch):** `dr029/2_4_betfair_streaming/reference_guide/` — five pages captured during §2.4 brief drafting:
- `placeOrders.md`, `cancelOrders.md`, `replaceOrders.md` — placement-side endpoint specs (instruction limits, customerOrderRef de-dup, atomicity semantics).
- `best_practice.md` — HTTP transport defaults, login rate floors, idle-keep-alive timing.
- `market_data_request_limits.md` — REST data-weight budget table (200-point ceiling).

Pages remaining as Path A on-demand fetches if §2.7 / §2.10 / future briefs need them: `Login & Session Management`, `Betting Enums`, `Betting Exceptions`, `updateOrders`.

### 1.2 Sample Code

https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687537/Sample+Code

Working code examples for common API operations across multiple languages. Useful for sanity-checking that v3 implementation patterns match Betfair's expected usage shape, particularly around session token handling, market subscription, and Streaming API integration.

### 1.3 API Tools Demo

https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687096/API+Demo+Tools

Live demo tools — useful for ad-hoc API calls without writing throwaway code. Worth knowing about for future probe-shaped work where targeted manual API calls are faster than scripting.

### 1.4 Streaming API (separate from polling REST)

Reminder: the Stream API is a separate surface from the polling REST API. The Saturday probe (`api_probe_report.md`) captured polling REST behaviour only — Streaming spec is in §2.4 and consumes the Stream API documentation, which is separate. No probe data on Streaming yet.

**On-disk canonical reference:** `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` (986 lines, captured Session 59 from operator's authenticated browser session — Confluence anonymous-access wall blocks `web_fetch`). Parallels `openapi.json` as the local canonical artefact for the corresponding API surface. Used by §2.4 Fix 4 brief drafting; expected forward-use by §2.7 (API contract versioning) and operational debugging post-v3-launch.

### 1.5 EX_LADDER entitlement question (open)

From rebuild work — full ladder access on Exchange data may require an entitlement upgrade. Open item flagged in `current_state.md`; possibly a DR. Worth confirming against the Reference Guide §1.1 and developer.betfair.com account documentation.

---

## 2. The Racing API

### 2.1 OpenAPI specification (local file)

`/Users/tim/Desktop/Projects/bethub-rebuild/openapi.json`

Full OpenAPI 3.1.0 spec for The Racing API v1.4.3. 640 KB, machine-readable. Includes:

- All endpoint paths, request parameters, response schemas.
- Per-endpoint rate limits (e.g. "1 request per second" for `/v1/courses/regions`).
- Plan tier annotations (Free / Basic / Standard / Pro Plan) — useful for understanding what's actually accessible at the current subscription level.
- Code samples in cURL, Python, PHP, JavaScript per endpoint.
- Component schemas for the data types the API returns (Region, Race, Runner, Dam, etc.).

**How to consume this in rebuild and analytical work:**
- For a quick endpoint reference, `grep` or `jq` over the JSON file directly. e.g. `jq '.paths | keys' openapi.json` lists every endpoint.
- For schema lookups (e.g. "what fields does a Runner record contain?") → `jq '.components.schemas.Runner' openapi.json`.
- For rate-limit auditing → search for `Rate Limit` in the description text (rate limits are embedded in the description HTML rather than as a separate field).

### 2.2 Documentation homepage

https://api.theracingapi.com/documentation#tag/Dams/operation/dam_progeny_distance_analysis_v1_dams__dam_id__analysis_distances_get

Browser-rendered version of the OpenAPI spec, with worked examples and a try-it-now interface. The deep-link above lands on the Dam progeny distance analysis endpoint specifically — useful given the analytical project's interest in dam/sire data for Strategy 4 modelling.

**Most relevant for upcoming work:**
- §2.5 soft-book interface contract — Racing API harness/greyhound coverage gap (probe Q5 input).
- Fix 5 venue harmonisation — Racing API is one side of the venue-name reconciliation; understanding what venue identifiers the Racing API uses is part of the harmonisation design.
- AFL SGM is unrelated, but for `bethub-analytical/`'s racing calibration piece (sequenced second), the Racing API exposes runner pedigree, dam/sire, and progeny analysis endpoints that are directly useful for Strategy 4 (synthetic each-way) place-market modelling — though Strategy 4 is currently out of scope for the analytical project.

### 2.3 Authentication

HTTP Basic auth with username/password. Credentials live in operator-side config; not captured here.

---

## 3. Cross-references

**Used by (rebuild):**
- `dr029/dr029_scope.md` — §2.4 Streaming, §2.5 soft-book, §2.10 external analytics.
- `dr029/2_1_race_data/api_probe_report.md` — Saturday probe; Reference Guide §1.1 was implicit in the probe design.
- Fix 4 cadence brief drafting (post-BSP-close work) — Reference Guide §1.1 is primary input.
- `current_state.md` "pending operator-side actions" — Betfair API documentation acquisition was flagged as operator-side homework; this doc captures the result.

**Used by (analytical):**
- `bethub-analytical/racing_ev_calibration/` — when activated (sequenced second after AFL SGM). Racing API for runner/race metadata; Betfair Reference Guide for BSP and market structure detail.

---

## 4. Update protocol

This is a slow-changing doc — external API references shift only when:
- A new API surface gets added (e.g. Betfair adds a new endpoint set, Racing API releases v2).
- An existing reference URL changes.
- A new local artefact lands (e.g. a downloaded API spec file).

When that happens, update the URL or path here and bump the "last updated" date. Don't accumulate version history in the doc itself — git history is the version history.

Detailed findings (e.g. specific rate limits for specific endpoints, projection-set behaviour quirks discovered through probing) live in the relevant DR-029 artefacts (probe reports, brief drafts) — not here. This doc is a pointer, not a compendium.
