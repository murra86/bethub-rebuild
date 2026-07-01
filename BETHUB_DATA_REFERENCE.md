# BETHUB DATA REFERENCE

**Status:** LIVE — canonical. This is the single source of truth for
BetHub's data layer. As each section fills, the harvested source docs
are superseded (tracking table §H). Sections not yet filled are marked
**[SCAFFOLD — to fill]** with their harvest target named.
**Established:** 2026-06-30 (Session 205, Data Foundation arc, DR-021
Adelaide anchor).
**Frame:** `data_foundation_structure.md` (the approved structure spec).
**Governing DRs:** DR-027/028 (two-DB, single integration boundary),
DR-032 (Betfair canonical reference), DR-033 (data-source role split),
DR-021 (Adelaide anchors), DR-034 (race-identity model — LOCKED S206,
developed in §B).

---

## §0 — How this document works

**Purpose.** Answers, in one place: what each source contains, how the
sources reconcile to one physical race (identity), how that lands in
storage, how ingest behaves, and whether the whole serves what we use it
for. Built once, maintained, referred back to — across every BetHub
project, not just v3.

**Durable vs versioned.**
- §A (source contracts) and §B (identity) are **durable** —
  project-agnostic, carry forward indefinitely.
- §C (storage) and §D (ingest) are **v3-versioned** — they describe the
  current implementation; re-version when it changes.
- §E (fitness) spans both.

**Boundary test** (governs what belongs here):
> Does this **define or reconcile** the data, or **consume** it?
> Define/reconcile is IN. Consumers (EV model, strategies, settlement,
> UI, account-health) are documented as *needs* in §E, never
> re-architected here.

**Update protocol.** New data work updates THIS document rather than
spawning a new doc. That rule is what keeps it canonical. Detailed
one-off findings still live in their session reports; the durable
conclusion lands here. Bump the section's note line when changed.

---

## §A — Source contracts

### A.0 — Framing
Three sources feed BetHub: **Betfair** (operational backbone + analytical
snapshots), **The Racing API** (racing enrichment/analytics), and the
**bookmaker scrapers** (soft-book price capture). Per DR-033 each job has
one owner: Betfair operates + settles; the Racing API enriches; scrapers
supply comparative book prices. Capability overlap exists but duty does
not (e.g. Betfair holds BSP *and* the Racing API carries a BSP
cross-ref — Betfair owns it operationally).

### A.1 — Betfair (Exchange REST + Stream)

- **What/cost:** Betfair Exchange API. Free with the operator's Betfair
  account; session-token auth. The operational backbone — where bets are
  actually placed.
- **Surfaces:** polling **REST** + the **Exchange Stream API** (separate
  surface; real-time push).
- **Coverage:** racing AND sports; AU + global markets.
- **Contains:** live back/lay ladders + matched volume; market/selection
  identity (event / market / selection, venue, sport, start time);
  Betfair Starting Price (BSP, near/far + actual); win/lose market
  settlement (which selection won/lost the market); commission; account
  balance; order place/cancel/replace/state.
- **Does NOT contain:** full finishing order (knows winner + place-market
  outcome, not the 1-2-3-4 ordinal per runner); margins, form,
  jockey/trainer/weight, pedigree, stewards, career stats; results for
  unsubscribed markets. Not a deep historical store (a static 12-month
  import sits in capture.db `betfair_historical`, separate from the live
  API).
- **Role (DR-032/033):** operational — pricing, placement, settlement,
  balance, and the **canonical bet/event identity**. Also feeds the
  analytical line via VPS snapshots into capture.db `betfair_snapshots`
  (BSP, near/far SP), so it feeds BOTH lines but its assigned duty is
  operational.
- **Lands in:** v3 `betfair_client` (operational); capture.db
  `betfair_snapshots` + `betfair_historical` (analytical).
- **Cadence/reliability:** real-time (Stream) / on-demand (REST). REST
  data-weight budget capped (200-point ceiling — see
  `market_data_request_limits.md`).
- **Docs (on-disk canonical):**
  `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` (986L,
  Stream) + `dr029/2_4_betfair_streaming/reference_guide/` (placeOrders,
  cancelOrders, replaceOrders, best_practice,
  market_data_request_limits). Full REST Reference Guide is auth-walled
  Confluence — cited, partially captured. Public page tree fetchable
  (this session): Betting Type Definitions, Betting Enums,
  listMarketCatalogue, listMarketBook, Race Status API — **field-table
  harvest targets (A.4).**
- **Open viability:** **EX_LADDER entitlement** — full ladder depth may
  need an entitlement upgrade (§G).

### A.2 — The Racing API

- **What/cost:** theracingapi.com, spec **v1.4.3**. **Free plan +
  Australia Racing Data add-on (£49.99/mo).** HTTP Basic auth. Periodic,
  backward-looking enrichment — not real-time.
  *(Corrects stale `data_sources.md` figure of "~$100/mo Standard".)*
- **Rate limits:** rate-metered, **no monthly quota.** Free = 1 req/sec,
  paid = 5 req/sec, plus Cloudflare burst limits (>100 req/10s → 5-min
  cooldown). **OPEN:** whether the paid AU add-on lifts the rate to
  5/sec or stays free-tier 1/sec — operator emailed provider 2026-06-30
  (§G). Materially bounds capture/backfill cadence (relates to RC-1).
- **Coverage:** racing only (no sports). AU thoroughbred by state/course
  via the **Australia regional add-on** (`/v1/australia/meets`,
  `/v1/australia/meets/{id}/races`). Harness/greyhound enrichment limited
  or unavailable (DR-032).
- **Contains (per resulted runner):** finishing position, beaten
  margins, winning time, industry SP (fractional + decimal), a
  Betfair-SP cross-reference, stewards comments, tote returns; plus form,
  jockey/trainer/weight/barrier/rating, pedigree (sire/dam/damsire),
  career win/place %. Across ALL races, not just ones bet into.
- **Does NOT contain:** sports; live exchange prices; bet placement or
  settlement (read-only).
- **Update cadence:** today ~3 min, tomorrow ~15 min, future daily.
- **Role (DR-033):** racing enrichment + analytics.
- **Lands in:** pulled by the VPS (`subscription/racing_api.py`,
  `sync_day()`); capture.db `runners` (finish_position, result_status,
  margins, sp_fixed, form, pedigree, career; results_source=
  'subscription') + `races` (subscription metadata).
- **Docs (on-disk canonical):** `openapi.json` (640 KB, OpenAPI 3.1.0,
  v1.4.3) + the generated `racing_api_field_catalogue.md` (58 endpoints,
  124 schemas) — **field-table harvest source (A.4).**
- **Open viability:** ToS prohibits "betting operators and sportsbooks"
  (§G); the 1-vs-5/sec rate question above.

### A.3 — Bookmaker scrapers (soft books)

- **What:** in-house scrapers capturing comparative bookmaker prices.
  No external docs — grounded from our own code.
- **Working (proxy bypass):** Entain (Ladbrokes/Neds), PointsBet,
  Unibet, PlayUp.
- **Blocked (Cloudflare — need headless):** BetRight, Betr, Sportsbet,
  PalmerBet, Dabble. TAB API dead (needs TAB Studio registration).
- **Contains:** win/place odds per runner, per book, at snapshot time.
- **Role:** comparative book pricing (drift detection, Price Booster).
- **Lands in:** capture.db `bookmaker_snapshots`.
- **Cadence/reliability:** scraper health-check cron 6AM Adelaide;
  Cloudflare books are the standing fragility (§G).

### A.4 — Field tables  **[SCAFFOLD — to fill]**
Per-source, per-field rows (type, meaning, cadence, reliability, known
defects). **Harvest targets:** Racing API → `openapi.json` v1.4.3 +
`racing_api_field_catalogue.md`; Betfair → on-disk stream reference +
the fetchable Betting Type Definitions/Enums + listMarketCatalogue/Book;
scrapers → capture.db `bookmaker_snapshots` schema + scraper code. Known
defects to attach at field level: the 3 `scheduled_start` UTC encodings
(one breaks `fromisoformat`), the `race_date` ±1 skew. **Next unit.**

---

## §B — Identity & reconciliation model  **[LIVE — DR-034 locked S206]**

> **Status.** This section is the deep new work of the Data Foundation
> arc. Developed Session 206 from the Brief 1.1 duplication anatomy
> (`vps_endpoint_enrichment_report.md` §4, market `1.259530858`), the
> two ingest paths (`race_date_semantics_report.md`), and the capture
> store's identity anatomy (`vps_supply_review.md`). **DR-034 was
> locked S206 (after the placings-backfill cross-check) and is now the
> canonical record in `decisions.md`; the §B.8 copy below is the
> mirror.** Nothing here changes schema, ingest, or the live earning
> path; this is a *definition*, not a build (boundary test: it
> defines/reconciles, it does not consume).

### B.1 — The problem this fixes

BetHub reads three sources that each name a race their own way, and the
capture store then scatters a single real-world race across many rows.
There has never been a defined answer to "which physical race is this,
and what is its one canonical name." The 87% market-id duplication
(Brief 1.1) is the symptom; the absence of an identity model is the
disease. §B defines the model; DR-034 (§B.8) locks it.

### B.2 — The canonical entities and their keys

Four entities. The **Betfair WIN market is the spine** — the one
identifier that stayed invariant across every fragment of the worked
example, consistent with DR-032 (Betfair as the canonical reference).

| Entity | What it is | Canonical key | Notes |
|---|---|---|---|
| **Physical race** | one real-world race that ran (or will run) at a venue, on a day, at a start instant | **Betfair WIN `market_id`** (`1.2595…`) where a Betfair market exists | the spine. One physical race ⇒ exactly one Betfair WIN market. |
| **Runner** | one horse/dog in that race | **`(WIN market_id, selection_id)`** | `selection_id` is unique only *within* a market, so it is always scoped by the market. |
| **Market** | a Betfair betting market on the race (WIN, PLACE, …) | **Betfair `market_id`** | the WIN market is the spine; PLACE/other markets are siblings of the same race. |
| **Event** | the Betfair `event_id` parenting the race's markets | **Betfair `event_id`** | groups the race's WIN + PLACE (+ other) markets; the link tying a WIN market to its PLACE market for Strategy 4 (synthetic each-way). |

Clarification of a loose label: the Brief 1.1 by-market route docstring
wrote "`betfair_win_market_id` (event_id)". They are **not** the same
Betfair object — `market_id` (`1.259…`) names one market; `event_id`
names the parent event holding the WIN and PLACE markets together. The
**physical-race spine is the WIN `market_id`**, not the event id.

### B.3 — How each source's native keys map onto the spine

- **Betfair** — native hierarchy `event_id → market_id → selection_id`
  maps **directly** onto the canonical entities. No reconciliation
  needed; Betfair *is* the spine. This is why DR-032 makes Betfair the
  canonical reference for every bet record.
- **The Racing API** — native hierarchy `meet id → race id` (the
  `/australia/meets/{id}/races` path), each race carrying `off_time`
  (UTC), course, and race number. **Not currently persisted as a foreign
  id on the capture store** — the subscription ingest collapses the
  Racing-API race straight into the natural key
  `(race_date, venue_normalised, race_number)` via `upsert_race()` and
  keeps no Racing-API race id. So the Racing-API → spine link is
  *reconstructed by matching* (venue + date + race number + off_time),
  never stored. **Gap → §C/§D + roadmap:** persist the Racing-API race id
  so the link is recorded, not re-derived.
- **Bookmaker scrapers** — native book-specific venue/race refs in
  `bookmaker_snapshots`, carrying **no Betfair identifier of their own**.
  A scraper row reaches the spine only through the same
  venue+date+race-number match. Weakest link to the spine; relevant to
  Strategy 2 (Price Booster) drift detection, not to settlement.
- **capture.db store** — three identifiers coexist on `races`, and only
  one is a real race identity:
  - `races.id` — a synthetic per-row autoincrement. **NOT a physical-race
    identity** — it is a *per-fragment* row id. This is the trap the
    Brief 1.1 "first by id" tie-break fell into.
  - `(race_date, venue_normalised, race_number)` — the natural / upsert
    conflict key. **Fragments** one physical race into many rows (B.5).
  - `betfair_win_market_id` — the spine stamp; present on only ~20–27% of
    rows (Betfair capture began 2026-03-02; `vps_supply_review.md`). The
    strong identity, but a minority of rows carry it.
  - `runners.betfair_selection_id` — the runner-level spine key (95.9%
    coverage on snapshotted stamped races); the
    `(betfair_win_market_id, betfair_selection_id)` join is the working
    identity-resolution path today (`vps_supply_review` read #7).

### B.4 — The rule for races with no Betfair market

The spine is absent on the majority of rows (~73–80% unstamped; 34.8%
are start-less discovery shells). Identity for those falls back to a
**derived natural key**, explicitly **second-class**:

> **No-market identity = (real-world race date, canonical venue, race
> number)** — where *real-world race date* is `scheduled_start` converted
> UTC→Adelaide-local (per `race_date_semantics_report`, never the raw
> skew-prone `race_date`), and *canonical venue* is the harmonised venue
> ("Emerald" and "Emerald Downs" → one name).

Two hard boundaries on this fallback:
1. **Analytical-only.** Per DR-032 §6 a soft-book bet *must* have a
   Betfair market at logging time, and per DR-033 settlement runs off
   Betfair. So the operational/earning path **never** depends on the
   no-market identity — it serves only the analytical line (enriching and
   resulting races not bet into).
2. **Lower confidence by construction.** Without the spine, two rows can
   be recognised as the same race only by venue+date+number
   normalisation — the machinery that is currently imperfect (Fix 5
   territory). A start-less shell with no market id (B.6 case 3) is the
   weakest: keyable only by the stored skew-prone `race_date`, and
   analytically droppable.

### B.5 — The fragmentation mechanism (why one race becomes many rows)

Worked example — Betfair WIN market `1.259530858`, **one physical race**,
**three capture rows** (`vps_endpoint_enrichment_report.md` §4):

| id | race_date | venue | status | runners |
|---|---|---|---|---|
| 2652588 | 2026-06-28 | Emerald Downs | PENDING | 0 |
| 2674078 | 2026-06-28 | Emerald | SETTLED | 15 |
| 2677487 | 2026-06-29 | Emerald | SETTLED | 15 |

The upsert conflict key is `(race_date, venue_normalised, race_number)`
and `race_date` is **never updated on conflict** — so the *first*
inserter owns it. Both components drift across the two ingest paths:
- **`race_date` drift (±1 day)** — Path A (subscription) copies the
  Racing-API meeting date; Path B (live orchestrator) stamps the UTC
  clock date at discovery, up to 12 h ahead. The two skew opposite ways
  (`race_date_semantics_report`).
- **`venue_normalised` drift** — the same course arrives as "Emerald"
  from one path and "Emerald Downs" from the other.

Either drift alone splits the natural key; together they scatter one race
across several rows. The Betfair WIN market id was the **only** field
identical across all three — the empirical proof that it, not the natural
key, is the race's true identity.

### B.6 — The deterministic "which physical race is this" answer

Given **any** row from **any** source, resolve identity in this order:

1. **Spine path — row carries a Betfair WIN `market_id`.**
   → Canonical race = that market id. **Done.** All rows sharing the
   market id are fragments of this one physical race (B.7 picks the
   authoritative fragment).
2. **Derived path — no market id, but `scheduled_start` present.**
   → Canonical race = `(scheduled_start→Adelaide-local date, canonical
   venue, race number)`. Second-class, analytical-only (B.4).
3. **Weak path — no market id and no `scheduled_start`** (the 34.8%
   discovery shells).
   → Identity is only the stored `(race_date, venue_normalised, race
   number)`, flagged low-confidence; analytically droppable.

### B.7 — Fragment-collision rule (supersedes "first by id")

When several capture rows share one Betfair WIN market id (the 87%
case), they are fragments of one physical race. The Brief 1.1 route used
**`ORDER BY id`** (lowest id) — which returns the **earliest-created**
row, typically the live-orchestrator **PENDING 0-runner discovery
shell**. That is the wrong fragment: the result the caller wants lives on
a later, enriched sibling.

**The rule:** among fragments sharing a market id, select the
**most-complete fragment**, not the lowest id. Completeness order:

1. prefer a **resolved/SETTLED** status over PENDING;
2. then **most runners** (`n_runners` desc) — a 0-runner shell never wins
   over a populated sibling;
3. then **results present** (finish positions populated);
4. tie-break among equally-complete fragments by **highest id / most
   recently enriched** (the latest good write).

This is the immediate, deterministic correction for the by-market route.
**The deeper fix (→ roadmap, not executed here):** at read time *collapse*
all fragments of a market id into one canonical race — union runners and
results across siblings under the spine — so the answer never depends on
picking a single winning row; and enforce identity at **write** time (§D)
so fragments stop being created. Both are remediation items DR-034 points
to; neither is built by this section.

For the **no-market** fragmentation (the "Emerald" vs "Emerald Downs"
split where rows share no market id), fragments can be merged only by
venue-harmonisation + date-normalisation (Fix 5) — there is no spine to
collapse on. This is precisely why the no-market identity (B.4) is
second-class.

### B.8 — DR-034 (LOCKED S206 — canonical record in decisions.md)

> The text below is the DR-034 record, **locked Session 206** and
> copied into `decisions.md` as the canonical entry (with the
> placings-backfill dependency folded into stance 4). This §B.8 copy is
> the in-reference mirror; on any future amendment, `decisions.md` is
> the source of truth.

---

**## DR-034: Canonical race identity — the Betfair WIN market is
the spine; capture-store fragments resolve by completeness, not row id**

**Status:** LOCKED — Session 206 (2026-06-30). Canonical copy in
`decisions.md`.

**Why:** Brief 1.1 surfaced that 87% of market-bearing capture rows share
their `betfair_win_market_id` with ≥1 other row, because the capture
store's natural key `(race_date, venue_normalised, race_number)`
fragments one physical race into many rows (both components drift across
the two ingest paths). BetHub had no defined cross-source race identity,
so "which physical race is this" had no deterministic answer, and the
shipped by-market route's "first by id" tie-break returns an empty
discovery shell in the dominant case. This DR locks the identity model so
every future data consumer keys races the same way.

**Locked stance:**

1. **The Betfair WIN market id is the canonical identity of a physical
   race** wherever a Betfair market exists — the one field invariant
   across all fragments of a race; consistent with DR-032. Runner
   identity is `(WIN market_id, selection_id)`; the Betfair `event_id`
   parents a race's WIN + PLACE markets.
2. **The capture store's `races.id` is not a race identity** — it is a
   per-fragment row id and must never be used as one (the trap "first by
   id" fell into).
3. **Races with no Betfair market take a second-class, analytical-only
   identity:** `(scheduled_start→Adelaide-local date, canonical venue,
   race number)`. The operational/earning path never relies on it
   (DR-032 §6 requires a Betfair market at logging time; DR-033 settles
   off Betfair).
4. **Fragment-collision resolves by completeness, not row id.** Among
   capture rows sharing a WIN market id, the authoritative fragment is
   the most-complete one (resolved status → most runners → results
   present → most recent), superseding the Brief 1.1 `ORDER BY id`
   tie-break. Target end-state: collapse fragments under the market id at
   read time and enforce identity at write time (remediation, specified
   in §C/§D + roadmap, not executed by this DR).
5. **Per-source native keys map onto the spine** as in §B.3. The
   Racing-API race id is not currently persisted (the subscription path
   collapses it into the natural key); recording it is a named
   remediation item.

**Scope / what this is not:** A definition, not a build. This DR fixes
how races are identified and reconciled; it does **not** change any
schema, ingest path, or the live earning path, and commissions no code.
Schema/ingest remediation is specified separately (§C/§D + roadmap) and
executed under its own briefs. Bet-safe: analytical/governance only.

**Cross-references:** `BETHUB_DATA_REFERENCE.md` §B (the full model this
DR summarises); DR-032 (Betfair canonical reference — the spine builds on
it); DR-033 (source roles — keeps the no-market identity analytical);
DR-027/028 (two-DB boundary — identity by reference, no caching);
`vps_endpoint_enrichment_report.md` §4 (duplication anatomy);
`race_date_semantics_report.md` (fragmentation mechanism); Brief 2
(`vps_client_api_rewrite_brief.md`, re-locks against this identity).

**Date:** 2026-06-30 (Session 206 — locked from this draft after the
placings-backfill cross-check).

---

**Lock record (S206):** DR-034 written to `decisions.md`; §B header
flipped DRAFT→LIVE; stance 4 carries the placings-backfill dependency.
§H supersede of `race_date_semantics_report` stays pending (it also
harvests into §D, still scaffold — archive only once §D is filled).

---

## §C — Storage representation  **[SCAFFOLD — to fill]**
capture.db + bethub.db tables mapped to the §B canonical model; where
the natural key fails; correct keying. **Harvest:** `vps_supply_review.md`
(schema-truth + per-read fit tables) + live schema reads.

## §D — Ingest behaviour  **[SCAFFOLD — to fill]**
The two ingest paths (discovery vs enrichment/results), where they
diverge, how fragments get generated live, and the write-time identity
enforcement point. **Harvest:** `dr029/2_1_race_data/source_review_report.md`
+ ingest code (`subscription/`, `capture/`, `matching/race_matcher.py`).

## §E — Fitness matrix  **[SCAFFOLD — to fill]**
Per consumer — operational (bet logging, Betfair settlement,
account-health) and analytical (EV model, BSP↔finish, placings/backfill,
the four strategies) — what data it needs, from where, at what
reliability, served or gap. **Harvest:** `v3_data_requirements.md` +
`vps_supply_review` fit tables. Boundary test keeps this to *needs*.

---

## §F — Extensibility structure

Defined slots so future capability is a slot-fill, not a fresh dig:
- **New source** — copy the A.x contract shape (capability / role /
  access / cadence / reliability / docs / viability).
- **New sport** — §B spine is sport-agnostic; add a per-sport identity
  sub-section (Strategy 3's AFL/NRL → NBA/NFL data drops in here).
- **New analytical need** — add one §E consumer row + its data needs.
- **New store / migration** — re-version the relevant §C/§D sub-section.

---

## §G — Source-viability / dependency-risk register

| Risk | Detail | Status |
|---|---|---|
| Racing API rate tier | Free=1/s, paid=5/s; does the AU add-on lift to 5/s? Bounds backfill cadence (RC-1). | **Operator emailed provider 2026-06-30** — awaiting reply |
| Racing API ToS | Prohibits "betting operators and sportsbooks"; individual-analyst use likely fine. | Logged — monitor |
| Betfair EX_LADDER | Full ladder depth may need entitlement upgrade. | Open — confirm vs Reference Guide / account |
| Scraper fragility | Cloudflare books (BetRight, Betr, Sportsbet, PalmerBet, Dabble) need headless; TAB API dead. | Known — headless solution pending |

---

## §H — Supersede tracking

As each source doc is fully harvested into the section(s) above, it is
marked superseded (header pointer here) and moved to `_archive/`. The
reference then becomes the only live data doc.

| Source doc | Harvests into | Status |
|---|---|---|
| `data_sources.md` | §A.1–A.3, §B (roles) | **Harvested → §A** (supersede pending B/E) |
| `external_api_resources.md` | §A docs lines, §G | **Harvested → §A/§G** (supersede pending) |
| `racing_api_field_catalogue.md` | §A.4 | Pending (A.4 fill) |
| `betfair_stream_api_reference.md` | §A.1, §A.4 | Pending (A.4 fill) |
| `vps_supply_review.md` | §C, §E | Pending |
| `dr029/2_1_race_data/source_review_report.md` | §D | Pending |
| `v3_data_requirements.md` | §E | Pending |
| `race_date_semantics_report.md` | §B, §D | Partially (cited in §B) |

*No doc is archived until its target section is filled and the pointer
is in place — archiving early would lose detail mid-harvest.*

---

*LIVE canonical reference. §A source-contracts filled (S205); §B identity
& reconciliation model LIVE (S206) — DR-034 locked to `decisions.md`
after the placings-backfill cross-check (dependency in stance 4). §A.4
field tables + §C–§E scaffolded with harvest targets named. Next: §A.4
field harvest + §C/§D/§E (§D carries the write-time identity-enforcement
point + the fragment-floor deficit caveat).*
