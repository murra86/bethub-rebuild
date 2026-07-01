# BetHub Data Foundation — structure doc

**Status:** DRAFT structure spec — held for operator approval (S205).
This defines the *frame* of the canonical data reference and identity
model. Nothing is filled until the frame is approved.
**Drafted:** 2026-06-30 (Session 205, DR-021 Adelaide anchor).
**Why now:** the 87% market-id duplication finding (Brief 1.1 report)
exposed that BetHub has no defined cross-source *race identity*. Six
overlapping data docs exist; none reconcile the sources to one physical
race. This arc closes that — the data-layer question DR-029 was meant
to settle and didn't.

---

## 1. What this arc is, and its boundary

**Goal:** one canonical, living, reusable reference for BetHub's data
layer — sources, identity, storage, ingest, fitness — plus a locked
decision on race identity. Built once, maintained, referred back to.
Durable across every future BetHub project, not a v3-only snapshot.

**The boundary test** (apply whenever scope tempts mid-arc):
> *Does this thing **define or reconcile** the data, or **consume** it?*
> Define/reconcile is IN. Consume is OUT — a consumer is a requirement
> that feeds the fitness lens (§E), not a thing this arc redesigns.

So: the EV model, the strategies, settlement logic, the UI, account
health are all **consumers** — documented as needs, never re-architected
here. This is the foundation under them, not a rebuild of them.

**Durable vs versioned.** Layers A and B (source contracts, identity)
are project-agnostic and carry forward forever. Layers C and D (storage,
ingest) are v3-versioned — they describe the current implementation and
re-version when it changes. E (fitness) spans both.

---

## 2. What already exists (inventory + verdict)

The point of this section: prove we are **harvesting, not re-digging.**

| Existing doc | Holds | Verdict |
|---|---|---|
| `racing_api_field_catalogue.md` (1546L) | 58 endpoints, 124 schemas, generated | **Harvest** → A. Field work done. |
| `dr029/2_4…/betfair_stream_api_reference.md` (986L) | Stream protocol + message/field model | **Harvest** → A. |
| `external_api_resources.md` | Doc links, auth, EX_LADDER question | **Harvest** → A + viability notes. |
| `data_sources.md` | Capability + DR-locked roles | **Harvest** → A + B. |
| `vps_supply_review.md` | capture.db schema truth, per-read fit, finish-position gap | **Harvest** → C + E. |
| `dr029/2_1…/source_review_report.md` | Ingest source-code review | **Harvest** → D. |
| `v3_data_requirements.md` | v3 data-layer requirements, API contract | **Harvest** → E. |
| `race_date_semantics_report.md` | race_date skew, Candidate B | **Harvest** → B + D (the fragmentation mechanism). |

**Verdict:** field-level cataloguing is largely complete and good. The
**missing layer is identity/reconciliation (B)** — no existing doc maps
the sources to one physical race. That, plus unifying the above into one
maintained home, is the actual work. We do **not** regenerate the
catalogues.

---

## 3. Output artefacts

1. **`BETHUB_DATA_REFERENCE.md`** — the canonical living reference (the
   always-refer-back artefact). Single source of truth. Sections A–E
   below, plus the extensibility structure (§5) and viability notes
   (§6). Carries an update protocol so it stays current.
2. **A new decision record (provisionally DR-034)** — locks the
   canonical race-identity model (the §B conclusion). Short, governing,
   referenced by all future data work.
3. **Remediation roadmap** (a section in the reference, or a sibling
   doc) — what schema + ingest must change to *enforce* the identity
   model at write time. Feeds future Code briefs; this arc does not
   execute the remediation, only specifies it.

**Supersede plan:** once a source doc is harvested into the reference,
it is marked superseded (header pointer to the reference) and moved to
an `_archive/` folder. The reference becomes the only live data doc.
This is the mechanism that *keeps* the consolidation from re-scattering.

---

## 4. The reference skeleton (A–E)

Each section names: **covers / grounded by / complete-when.**

### A. Source contracts *(durable)*
- **Covers:** every field BetHub consumes from each source — Racing API,
  Betfair (Betting REST + Exchange Stream), bookmaker scrapers — with
  type, meaning, update cadence, reliability, and known defects.
- **Grounded by:** harvest the two big catalogues + `data_sources.md` +
  `external_api_resources.md`; reconcile against live payloads;
  scrapers grounded from our own code (no external docs).
- **Complete when:** every field we read has a row; every known defect
  (the 3 `scheduled_start` encodings, race_date skew, etc.) is recorded
  against its field, not in a separate report.

### B. Identity & reconciliation model *(durable — THE NEW WORK)*
- **Covers:** the canonical entities (physical race, runner, market,
  event); their canonical keys; how each source's native keys map onto
  them; the rule for races with no Betfair market; and the precise
  mechanism by which the two ingest paths currently fragment one race
  into many rows.
- **Grounded by:** the Brief 1.1 duplication finding (Betfair market id
  invariant across fragments → the spine), `race_date_semantics_report`,
  live capture.db anatomy, both source key schemes.
- **Complete when:** given any row from any source, the model
  deterministically answers "which physical race is this, and what is
  its canonical key" — including the no-market and the
  fragment-collision cases.

### C. Storage representation *(v3-versioned)*
- **Covers:** capture.db and bethub.db tables mapped to the canonical
  model; where the current natural key
  `(race_date, venue_normalised, race_number)` fails; what correct
  keying looks like.
- **Grounded by:** harvest `vps_supply_review.md`; live schema reads.
- **Complete when:** every store table is mapped to a canonical entity,
  and each identity gap is named with its fix-direction.

### D. Ingest behaviour *(v3-versioned)*
- **Covers:** the two ingest paths (discovery vs enrichment/results),
  where they diverge, how fragments get generated live, and what must
  change so identity is enforced at write time rather than patched after.
- **Grounded by:** harvest `source_review_report.md`; the ingest code
  (`subscription/`, `capture/`, `matching/race_matcher.py`).
- **Complete when:** the fragment-generation path is traced end to end
  and the write-time enforcement point is identified.

### E. Fitness matrix *(the use-lens — spans durable + versioned)*
- **Covers:** for each consumer — operational (bet logging, Betfair
  settlement, account-health) and analytical (EV model, BSP↔finish,
  placings/backfill, the four strategies) — what data it needs, from
  where, at what reliability, and whether the model serves it or what's
  missing.
- **Grounded by:** harvest `v3_data_requirements.md` + the
  `vps_supply_review` fit tables; the boundary test keeps this to
  *needs*, not consumer redesign.
- **Complete when:** every consumer has a row and every "missing/at-risk"
  cell routes to either a roadmap item or an accepted limitation.

---

## 5. Extensibility structure

The reference is built to be *added to*, so future capability is a
slot-fill, not a fresh dig. Defined empty slots from day one:

- **New sources** — a source-contract template (the §A row shape) ready
  for the next data provider or scraper.
- **New sports** — the identity model (§B) is sport-agnostic at the top;
  Strategy 3's AFL/NRL then NBA/NFL data drops into a per-sport
  sub-section without touching the spine.
- **New analytical needs** — the fitness matrix (§E) has an open
  consumer row shape; a new model becomes one row + its data needs.
- **New stores / migrations** — §C is versioned, so a schema change is a
  new version of that section, not a rewrite of the reference.

This is what makes "keep refining and adding capability for years"
cheap: the frame absorbs additions instead of fragmenting under them.

---

## 6. Source-viability notes (dependency-risk register)

A standing section — the risks that could break the foundation,
tracked so they don't surprise us:

- **Racing API plan/limits.** Free plan + Australia Racing Data add-on
  (£49.99/mo). No monthly quota — rate-metered: free = 1 req/sec,
  paid = 5/sec, plus Cloudflare burst limits. **Open:** does the paid
  add-on lift the rate to 5/sec or stay at free-tier 1/sec? Confirm with
  provider. Directly bounds capture/backfill cadence (relates to RC-1).
- **Racing API ToS.** Prohibits use by "betting operators and
  sportsbooks." Individual-analyst use likely fine; logged as a
  dependency risk on an income-critical source.
- **Betfair EX_LADDER entitlement** (carried from
  `external_api_resources.md`) — open question on full-depth ladder
  access.
- **Scraper fragility** — Cloudflare-blocked books (BetRight, Betr,
  Sportsbet, PalmerBet, Dabble) need headless solutions; TAB API dead.

---

## 7. Sequencing & magnitude

**Honest magnitude:** this is its own arc, several grounded sessions —
not one. But the shape is favourable because A/C/D/E are mostly
*consolidation* of existing docs; the deep new work is concentrated in
B (identity).

Provisional order:
1. **A — source contracts.** Harvest + reconcile. Fast-ish (docs exist).
2. **B — identity model.** The deep session(s). Grounded in the
   duplication anatomy. Ends in the DR-034 draft.
3. **C + D — storage + ingest.** Map to the locked identity; trace the
   fragment path; specify write-time enforcement.
4. **E — fitness matrix.** Tie consumers to the model; surface gaps.
5. **Roadmap + supersede.** Name the remediation; archive the old docs.

**Gating:** this arc gates Brief 2 and any further v3 build. Brief 2's
re-lock waits on the §B identity decision (it determines how the client
keys races/results). The shipped Brief 1.1 endpoint sits as-is with its
documented defect meanwhile — nothing live consumes it.

**Not at risk:** this is the racing/analytical identity layer. The live
v2 path that is actually earning is untouched throughout.

---

## 8. Governance

- Closes the DR-029 data-layer-fitness gap explicitly.
- Produces **DR-034** (provisional) — the canonical race-identity model.
- The reference carries an **update protocol** (who updates it, when,
  and the rule that new data work updates the reference rather than
  spawning a new doc) — the discipline that keeps it canonical.

---

## 9. Open calls for operator (approve the frame)

1. **Canonical reference name + home** — `BETHUB_DATA_REFERENCE.md` at
   rebuild root as the single living source of truth. Agree?
2. **Supersede plan** — harvested docs get marked superseded and moved
   to `_archive/`, leaving the reference as the only live data doc.
   Agree (vs keeping them live, which re-fragments)?
3. **Identity as a DR** — lock the §B conclusion as DR-034. Agree?
4. **Scope confirm** — we harvest the existing catalogues, we do **not**
   regenerate them; the new build is concentrated in identity (B) +
   unification + fitness completion. Agree?

On your answers I start filling — A first, then the deep B session.

---

*DRAFT structure spec. Frame only — no section filled. Held for the §9
approvals.*
