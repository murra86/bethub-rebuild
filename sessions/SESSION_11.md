# Session 11 — log

**Session opened:** 2026-04-27 21:10 ACST
**Session closed:** 2026-04-28 13:42 ACST (spans day-rollover at midnight ACST)

## Scope (planned, in order)

1. Reconciliation contract write-up across Slices 1–6, opening with Slice 1 race-reference verification (Q9 carried from Session 10).
2. Build strategy decision (strangler-fig vs clean break + slice strategy).
3. `diagrams/v3_target.svg`.

If context tightens: split before the diagram first, then before build strategy.

## Open items carried in

- **Q9** — Slice 1 race-reference verification. Provisional Slice 6 decision (Option B: race classification on race reference) pending this verification.

## Governing decisions (load-bearing for this session)

DR-006 (operations log), DR-019 (derived state on read), DR-021 (timestamp anchoring), DR-022 (vocabulary), DR-023 (operator-vs-system division of labour), DR-024 (operating/analytical separation), DR-026 (cheap-capture principle).

## Framing note

Workflow-first framing carries forward (eight consecutive early-close sessions). Software questions are Claude's; ask only about betting/operational matters. Honour DR-021, DR-007, DR-022, DR-024. Use Desktop Commander for all rebuild folder file operations (bash sandbox can't reach it).

## What this session actually became

The planned scope was reconciliation contract → build strategy → diagram. None of the three was delivered. The session instead produced a substantial architectural reframe — three new DRs, three amendments, a new governance file, and a multi-session sequencing plan — driven by operator-surfaced facts about existing infrastructure that the planned scope was implicitly going to ignore.

The reframe was correct and earned its place by displacing the planned work; it has been promoted via the scratch-then-promote pattern and the planned items (reconciliation contract, build strategy, diagram) carry forward to Sessions 12–14.

## Entries

### 2026-04-27 21:10 ACST — Session opened, Q9 verification underway

Anchored on system clock per DR-021. Read `work_in_progress.md`, `sessions/SESSION_10.md`, and `decisions.md` (DR-001 to DR-026) in full. Confirmed Slice 6 closed-state.

Q9 verification: read `sessions/SESSION_05.md` (Slice 1 lock) and `sessions/SESSION_07.md` (Slice 3 lock). **Found: Slice 1's locked entity hierarchy does not include a `race` entity at all.** Eight entities (account, book, ownership_cluster, platform, account_at_book, promo_template, promo, bet) — none of them race-side reference data. `bet.event_id` is a Betfair `market_id` text identifier, not an FK to any system-side `race` table. Session 10's "Option B" placement of race classification fields was provisional against an entity that doesn't exist. Q9 surfaces a real gap: Slice 1 needs a race entity added.

### 2026-04-27 21:22 ACST — `race` entity proposal drafted

Drafted an eleven-field `race` entity spec (race_id, bf_event_id, bf_market_id, venue, country, code, race_number, scheduled_jump_at, actual_jump_at, race_class, race_distance, race_surface, field_size_at_close, field_size_at_jump, recorded_at). Universe scope AU+NZ thoroughbred / harness / greyhound. Sourcing: Betfair liquidity capture per DR-020 for ids/timestamps; The Racing API (parked $100/month decision) for classification fields. Asked operator one betting-context question: confirm NZ inclusion in scope.

### 2026-04-27 21:27 ACST — VPS reframe surfaced by operator

**Operator surfaced existing infrastructure I had not adequately checked:** the UK VPS (`/home/racing/racing-data-capture/data/capture.db`) already captures races, runners, Betfair time-series snapshots, bookmaker time-series snapshots, BSP historical, batch summaries, and daily calibration summaries — and has been running successfully serving Strategy 1, BetHub v2, the Racing EV model, and AFL Edge.

Read `~/Desktop/Projects/racing/docs/system_snapshot.md`. Confirmed `capture.db` is rich: ~30k races, 3-level Betfair depth on both sides, 5-min standard / 60s pre-jump intensive cadence, BSP backfill, FastAPI read-only data layer (`racing-api.service`, 127.0.0.1:8400 over SSH tunnel) already wrapping it. BetHub v2 already consumes via `vps_client.py`.

**Reframing:** v3 was about to design a `race` entity and duplicate this capture. That would have produced two race-data sources drifting from each other — a v2-shaped failure mode at slow cadence. Architectural question now: how does v3's bet-data layer relate to the existing race-data layer.

### 2026-04-27 21:42 ACST — VPS-as-source partially right, partially wrong

Operator pushed back on "use the VPS" as a half-answer. Decomposed:

- **AU racing reference + AU racing Betfair snapshots:** capture.db genuinely sufficient; DR-020's standalone-capture build is satisfied by what already exists.
- **Bookmaker scrape cadence (5 min standard / 90–120s intensive):** may not be sufficient for DR-014's hot-path use case; cadence verification is a real build-time question.
- **Sports markets (AFL, NRL, etc.) on Betfair:** not captured today; this is genuinely v3's problem.
- **Cloudflare-blocked soft books:** operator-deferred ("an entire project in itself"), not a v3 prerequisite.
- **NZ:** out of scope for VPS today; operator confirmed NZ excluded day-one for v3, re-ask in data review.

### 2026-04-27 22:00 ACST — Discipline-rot meta-risk named; agreed to codify discipline as DRs

Operator named the meta-risk explicitly: cross-DB pattern can recreate v2-style failure mode through a different door if discipline rots over time. Confirmed: cross-DB pattern is structurally different from v2's failure mode (strict ownership per fact, no duplicated rows, no stored cross-DB derivations) but only stays clean if discipline is structural rather than trusted. Agreed to codify discipline as new DRs rather than rely on across-session memory.

### 2026-04-27 22:18 ACST — Scratch v1 written (option c chosen)

Operator chose option (c): scratch draft first, end-to-end review, then promote. Wrote `SESSION_11_SCRATCH.md` v1: DR-027 (cross-DB architecture), DR-028 (integration boundary discipline), DR-029 (DR-020 superseded for AU racing; sports gap parked), DR-030 (data-layer-first sequencing), DR-026 amendment (source-path), Slice 1 amendment (Q9 resolution), Slice 3 amendment (integration semantics).

### 2026-04-28 09:30 ACST — Day rollover; broader sequencing proposal from operator

Operator returned with a broader proposal: data-layer-first sequencing. Build out VPS to v3-fit-for-purpose *before* v3 build begins. This eliminates two risks: (1) discipline rot at build time via temptation to add ad-hoc captures or denormalisations under bet-logging pressure; (2) v3 building against a moving data-API contract while capture.db is itself being extended.

Operator surfaced two adjacent capabilities (analytics layer; account-isolation layer) and explicitly deferred both as out-of-scope for now. Cloudflare-blocked books also explicitly deferred. In-scope for the data review: race-data fit-for-purpose (cadence, fields, NZ re-ask), sports data layer (Betfair sports markets), at-bet-placement-time API pattern.

Discussed sequencing risk vs spec-on-paper failure. Agreed sequencing is right but with more upfront scoping: reconciliation contract first (Session 12), then build strategy (Session 13), then governance review (Session 14), then data review scoping/execution (Session 15+). Multi-session arc accepted: "time spent now is time saved later, with dividends."

### 2026-04-28 09:40 ACST — Multi-agent governance review pattern proposed

Discussed multi-agent governance review as structural protection against Claude's anchoring on the v3 frame. Document-suite ownership refined: Claude writes factual docs (`architecture_current.md`, `data_layer_current.md`); operator-Claude collaborative drafts `decision_under_review.md` ("Claude asks, operator tells, Claude records"); independent agent writes `open_questions.md`; three independent assessment agents (developer / PM / skeptic, mixed model families) produce assessments; independent judge synthesises. Reserved for high-reversal-cost or high-blind-spot decisions. First scheduled use: Session 14.

### 2026-04-28 09:45 ACST — DR-bloat concern surfaced; renumbering

Operator flagged DR-bloat as a real concern (four new DRs in one session is high). Reviewed: DR-029-as-DR-020-supersession demoted to a DR-020 amendment (supersession is a status note on an existing build task, not a new architectural decision). Old DR-030 (data-layer-first sequencing) renumbered to DR-029. **One-line justification discipline added per DR** going forward: every new DR carries a one-line justification for why it earns its DR rather than being demoted to amendment or parked item. Three new DRs net (DR-027, DR-028, DR-029) plus three amendments (DR-020, DR-026, plus the Slice 1 and Slice 3 record amendments).

### 2026-04-28 11:06 ACST — Scratch v3 written (after ~1hr operator review of v2)

Operator paused for an hour-long review of scratch v2. Returned with detailed feedback. Worked through each note. Key decisions:

- **DR-028 guardrails kept lean:** four structural protections (orientation citation at session open, by-number citation when invoked, mid-session re-read trigger, log discipline-rot watch). Each fires only when relevant — minimal orientation-reading overhead.
- **Bet-log freshness reversed from earlier hybrid lean to periodic-only with analytical bracketing.** Operator's reasoning that surrounding-interval data brackets the bet timestamp gave the architectural justification: the bet record carries placement_time + identifiers; analysis later reads both bracketing snapshots from capture.db, observing market movement *across* the bet timestamp. Stronger analytical position than a single fresh on-demand snapshot.
- **Confidence hierarchy dissolved.** Operator clarified: no soft-book auto-results data is captured today; settlement comes from operator-side observation of the book. Two sources, different facts: book canonical for cash; VPS canonical for race result. Divergences are reconciliation signals (burst review or session reconciliation), not algorithmic resolution. The "confidence hierarchy" was a v3-only idea proposed for scenarios that mostly don't arise.
- **VPS race results confirmed canonical for v3 auto-settlement.** Inherits Strategy 1 / BetHub v2 auto-settlement confidence pattern.
- **Analytics scan reframed as external environmental scan.** Not "what have we wished we had" (internal-looking), but "what does the world's data offer + what does the literature suggest is worth having" (external-looking). Racing AND sports parallel work-streams. Cost test: capture-cheap filter only (no new external API calls beyond what's already authorised). Time-boxed to two sessions of work.
- **NZ re-ask in data review** (verify Racing API NZ coverage; if available, NZ enters scope; if not, NZ remains day-one limitation).

### 2026-04-28 12:00 ACST — Further bet-schema simplification surfaced; deferred to Session 14

Operator surfaced a further simplification: if periodic-only is locked and analysis brackets via capture.db, does the bet record need to carry the snapshot inline at all? Stress-tested through six rationales (cross-system durability, analytical-self-containment, audit, late-scratching flag, retrospective-entry, DR-026 principle itself). All six found weak under the simplification. Same logic extends to Slice 6's `field_size_at_bet_placement` and `field_size_at_settlement` — derivable from capture.db scratching events.

Honest decomposition of "does this make BetHub development simpler": yes for v3 schema and bet-log path; no for analytical paths (richer `vps_client`); bigger for data review and capture.db audit. Net: cleaner architecture, comparable total complexity, simpler in most-frequently-exercised parts.

Operator deferred to Claude on the call. **Claude declined to take it as a unilateral software call:** blind-spot risk is real (anchoring on operator's prior correctness in this session is itself a signal), schema change reverses Slice 6 amendment from Session 10 (eight sessions of slice work overturned by one session's reasoning is high evidence threshold), multi-agent review pattern exists precisely for this. Recommended: defer to Session 14 multi-agent review; promote v3 of scratch with deferred-question markers in three places (DR-026 amendment, Slice 3 amendment, `work_in_progress.md` parked items).

This is the session's clearest application of the workflow-first / discipline-as-structure framing: catching a software-call lean and routing it to the multi-agent review process rather than acting on it.

### 2026-04-28 13:07 ACST — Scratch v4 written; operator confirmed promotion

Scratch revised to v4 with three deferred-question markers added. v3's locked architecture stays in force; the bet-schema-simplification question is explicitly tagged for Session 14 review. Operator confirmed proceed; chose option (b) — `governance.md` as its own file rather than embedded in `work_in_progress.md`.

### 2026-04-28 13:09 to 13:38 ACST — Promotion run

Promoted scratch v4 to canonical files. Files updated:

- `decisions.md`: DR-027, DR-028, DR-029 appended. DR-020 amendment ("Amendment 2026-04-28 (Session 11)") appended. DR-026 amendment ("Amendment 2026-04-28 (Session 11)") appended.
- `governance.md`: created (new file). Multi-agent governance review pattern documented.
- `work_in_progress.md`: parked items added (sports capture gap, Cloudflare books, account-isolation layer, analytics layer, NZ re-ask, decision-under-review collaborative drafting, bet schema simplification deferred to Session 14, soft-book cadence verification). Imminent build tasks updated (DR-020 build superseded for AU racing). Open questions / Session 12+ carries section updated.
- `sessions/SESSION_05.md`: Slice 1 Q9-resolution amendment appended.
- `sessions/SESSION_07.md`: Slice 3 race-side-identifier-integration-semantics amendment appended (with deferred-question marker for Session 14).

### 2026-04-28 13:42 ACST — Close-out gap discovered and resolved

Initial close-out left `sessions/SESSION_11.md` unwritten. Resolved by writing this file directly from the active session log narrative. Confirmed v3's deliberate governance scope is `vision.md`, `architecture.md`, `decisions.md`, `work_in_progress.md`, `sessions/`, `diagrams/`, plus the new `governance.md` — no `system_snapshot.md` or `context_index.md` (those were v2 conventions; v3 is deliberately leaner).

`SESSION_11_SCRATCH.md` retained in the rebuild folder root as historical artifact of the scratch-then-promote pattern; not deleted.

---

**Closed:** 2026-04-28 13:42 ACST

**Summary:** Three new DRs locked (DR-027 cross-DB architecture, DR-028 integration boundary discipline with four lean structural protections, DR-029 data-layer-first sequencing with periodic-only bet-log architecture / settlement model simplification / external analytics environmental scan). Three amendments locked (DR-020 superseded for AU racing; DR-026 source-path corrected; Slice 1 Q9 resolved with no v3-side `race` entity; Slice 3 documenting integration semantics). New governance file created (`governance.md`) documenting the multi-agent governance review pattern. Eight parked items added to `work_in_progress.md`.

**Architectural fact established:** v3's accounting-layer database and the existing UK VPS `capture.db` are separately owned, with strict per-fact ownership, joined by reference at read time via a single integration module. Race-side data lives in capture.db; bet-side data lives in v3.

**Sequencing established:** Session 12 reconciliation contract + v3 data-requirements sub-deliverable; Session 13 build strategy (strangler-fig vs clean break + slice strategy); Session 14 first multi-agent governance review (assesses DR-029 sequencing, v3 data requirements, and the deferred bet-schema-simplification question); Session 15+ data review scoping → execution → v3 build.

**Open items carrying to Session 12:**
- Reconciliation contract write-up across Slices 1–6, with explicit v3 data-requirements statement as a sub-deliverable.
- Decision-under-review collaborative drafting (operator + Claude) to be scheduled mid-Session-12 or in Session 13, supporting Session 14's multi-agent review.
- Build strategy decision deferred to Session 13.
- `diagrams/v3_target.svg` deferred to post-Session-14 (when architectural picture is settled enough to draw cleanly).

**Open question deferred to Session 14:** whether DR-026 inline snapshot storage and Slice 6 field_size captures should be removed in favour of full cross-DB resolution from capture.db.

**Streak:** ninth consecutive early-close session. Workflow-first framing held.
