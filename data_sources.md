# Data sources — capability and assigned role

**Status:** draft (Session 174). Role assignments here are mirrored in
`decisions.md` (DR — number assigned at lock).
**Last updated:** 2026-06-22 (Session 174).
**Purpose:** the single place that answers "what does each data source
contain, and what do we use it for." Pull-it-when-you-need-it reference —
NOT a session-open read. Pairs with `external_api_resources.md` (where the
API specs/URLs live); this doc is what's IN each source and what it's FOR.

**Two layers, kept deliberately separate:**
- **Capability** (Part 1) — what each source *can* provide. Slow-changing;
  shifts only when an API surface changes.
- **Assigned role** (Part 2) — what we *use* each for. Changing a role is a
  governance decision (a DR), made against the capability list — so we
  decide against what's possible, never rediscover it.

---

## Part 1 — Capability (what each source contains)

### Betfair Exchange API
- **What it is / cost:** Betfair Exchange API. Free with the operator's Betfair account (session-token auth). The operational backbone — where bets are actually placed.
- **Coverage:** Racing AND sports; AU + global markets.
- **Contains:** live real-time prices (back/lay ladders, matched volume); market + selection identity (event / market / selection names, venue, sport, start time); Betfair Starting Price (BSP); win/lose market settlement (which selection won or lost the market); commission; account balance; order placement / cancel / replace / order-state. Over both Streaming and REST.
- **Does NOT contain:** the full finishing order (it knows the winner and the place-market outcome, not the 1-2-3-4 ordinal for every runner); margins, form, jockey/trainer/weight, pedigree, stewards, career stats; results for races/events not subscribed to. Not a deep backward-looking store (a static 12-month import sits in capture.db `betfair_historical`, separate from the live API).
- **Access / where it lands:** v3's `betfair_client` (operational — pricing, placement, settlement, balance). The VPS also snapshots Betfair into capture.db `betfair_snapshots` (BSP, near/far SP) for the analytical line — so Betfair feeds BOTH lines, but its assigned role is operational (Part 2). Full API reference is auth-walled Confluence; key pages captured locally at `dr029/2_4_betfair_streaming/reference_guide/` (placement / cancel / replace, best-practice, data limits) + `betfair_stream_api_reference.md` (Streaming) — see `external_api_resources.md`. No local machine spec, so Betfair's field menu is cited, not transcribed.

### The Racing API
- **What it is / cost:** The Racing API (theracingapi.com), v1.4.3. Paid subscription (~$100/mo), HTTP Basic auth. Periodic, backward-looking enrichment — not real-time.
- **Coverage:** Racing only (no sports). AU via `/v1/australia/...` endpoints (also UK/IRE/NA elsewhere). Thoroughbred coverage confirmed; harness/greyhound enrichment limited or unavailable (per DR-032).
- **Contains (per resulted runner):** finishing position, beaten margins, winning time, industry SP (fractional + decimal), a Betfair-SP cross-reference, stewards comments, tote returns; plus form, jockey/trainer/weight/barrier/rating, pedigree (sire/dam/damsire), career win/place %. Across ALL races, not just ones bet into.
- **Does NOT contain:** any sports; live exchange prices for operational betting; bet placement or settlement (read-only data source).
- **Access / where it lands:** pulled by the VPS capture system (`subscription/racing_api.py`, `sync_day()`); lands in capture.db `runners` (finish_position, result_status, margins, sp_fixed, form, pedigree, career stats; results_source='subscription') and `races` (subscription metadata). Endpoints: `/v1/australia/meets`, `/v1/australia/meets/{id}/races`. The AU endpoints sit on the **Australia regional add-on** tier (the generic `/v1/results` path is Standard tier / 12-month window, UK-IRE-NA only); 5 req/sec. Full machine spec at `openapi.json`; **complete field-by-field catalogue at `racing_api_field_catalogue.md`** (generated — refresh with `python3 gen_racing_api_catalogue.py` when the API version bumps).

---

## Part 2 — Assigned role (what we use each for)  ← DR-locked

| Job | Source | Note |
|---|---|---|
| Live pricing | Betfair | real-time operational line |
| Bet placement | Betfair | operational line |
| Win/lose settlement | Betfair | confirmed S174 — `settlement.py` reads the leg's Betfair market + selection (WINNER→won, LOSER→lost); reads no analytical data, no finish position |
| Place/ordinal settlement (Safety Net 2nd–4th) | Manual (operator flag) | keeps the operational engine out of the analytical source; auto-settle deferred (needs free bets layable in-tool) |
| Bet / event identity | Betfair | canonical reference (DR-032) |
| Racing enrichment + analytics | Racing API | finishing positions, margins, form, pedigree, career stats, BSP cross-ref — all races, not just ours |
| Sports settlement | Betfair | Racing API carries no sports |
| Sports enrichment / analytics | (future separate subscription) | Racing API is racing-only |

**Overlap note:** both *could* do some jobs (the Racing API could settle a
place refund; Betfair holds BSP + price history). We still give each job one
owner, by the rule: **Betfair settles + operates; the Racing API enriches +
feeds analytics.** Overlap is capability, not shared duty.

---

## Part 3 — Deferred / open (named so they don't drift)

- **Auto-settle Safety Net place refunds** — wanted eventually (cuts manual
  effort). Depends on: free bets being layable in the tool (not built yet),
  and a decision on whether the operational settlement engine may read an
  analytical source for a placing. Manual flag until both resolve.
- **Sports enrichment subscription** — only if/when sports analytics wants the
  depth the Racing API gives racing. Not owed before sports lands.
- **Analytics spec** — can't be defined until the analytical project starts;
  the Racing API already appears to hold what it will need.
