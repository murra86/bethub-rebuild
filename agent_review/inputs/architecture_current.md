# Architecture (current)

*Companion document for the multi-agent governance review. Drafted Session 18 (2026-04-28). Descriptive — what is locked, what entities exist, what DRs apply. Framed for assessors reading without prior project context. Citations to DRs by number with a one-line gloss; the DR index at the end (§7) collects these for back-reference.*

---

## 1. What this document covers

v3 is the rebuild of an existing matched/promo betting tool (currently called BetHub v2). v2 has been running for months and continues to operate during the rebuild. v3 inherits the operational shape v2 produced — accounts at bookmakers, promotional bets, hedging on Betfair, free-bet ledger, AccountCare conditioning, a VPS-based racing-data capture system already in production — and rebuilds the software around that operational shape with v2's accumulated failure modes designed out.

This document describes the v3 architecture as it currently stands across Slices 1–6 of the rebuild design work (Sessions 5–10), with subsequent amendments through Session 14. It is descriptive, not persuasive: the goal is to give an assessor enough of v3's architectural shape to engage with the four review questions in `v3_data_requirements.md` (B.7) and the framing in `decision_under_review.md`. It does not re-derive design choices — those live in `decisions.md`.

---

## 2. High-level architectural shape

**Three layers (DR-002).** v3 separates into three layers with strict boundaries between them:

- **Operational layer** — daily and weekly cadence. Profile and account switching, AccountCare conditioning, promo allocation across accounts, the action queue surfacing what to do next.
- **Execution layer** — per-bet cadence. Bet logging, hedging on Betfair, EV calculations, live odds display, race-window navigation.
- **Accounting layer** — quiet background. Event log, derived balances, free-bet ledger, reconciliation surfaces, reports.

Each layer has one job and a defined interface to the others. v2's failure shape was that all three concerns mixed in every page, so a UX change to a promo-cap field touched the schema. v3's strict-boundary discipline is the structural fix.

**Two databases (DR-027).** Bet-data and race-data are owned by separate databases:

- **v3's accounting-layer database** (working name `bethub.db` or successor) owns bet-data: every entity and event involved in the bet lifecycle, settlement, hedging, promo cycles, free-bet ledger, cash flow, and the day-one AccountCare implementation.
- **`capture.db`** (existing UK VPS racing-data capture system) owns race-data: races, runners, finish positions, Betfair time-series snapshots, bookmaker time-series snapshots, BSP, daily calibration summaries.

No fact lives in both databases. v3 reads race-side context on demand at read time through a single integration module. The two-database stance is recognition, not invention — capture.db has been running on the VPS for months, but its current consumer situation is materially weaker than continuous use: BetHub v2 has code wired to it (racing page, result lookup during settlement), but the SSH tunnel that v2 depends on for VPS reach is frequently down, often for days at a stretch, with no operational impact on v2 because v2's actual bet-settlement path goes direct to Betfair API and the racing page isn't a primary operator surface. In effect, capture.db today is a quietly-running data layer without a real active consumer. v3 is the first consumer that will use the data layer at execution time, and that materially changes the operational stakes on tunnel reachability — §5 returns to this.

**Operating-mode and analytical-mode separation (DR-024).** A second separation cuts orthogonally to the three layers: operating-mode surfaces (action queue, bet logger, hedge modal, anything inside a burst) display only forward-looking, decision-relevant context; analytical-mode surfaces (reports, reconciliation views, P&L, EV-realised-vs-estimated dashboards) live behind dedicated entry points. The operator does not see "how am I doing today" while operating. This shapes which derivations get computed where, and it appears in the reconciliation-surface design (§6).

---

## 3. Entity model (v3 bet-data side)

Eight v3-side entities (Slice 1 lock):

```
account
  └── account_at_book ─── book ─── ownership_cluster
                                    └── platform
                              │
                              └── promo (when book runs an offer)
                                    └── promo_template
                              │
account_at_book
  └── bet ─── promo (nullable FK)
```

**Vocabulary (DR-022).** `account` is a real person (Tim, Kate, friends) whose identity is used for registrations. `book` is the betting company (Sportsbet, PointsBet, Ladbrokes, etc.). `account-at-book` is the specific registration of one account at one book — the unit at which money sits, promos arrive, and conditioning happens. One account never holds two registrations at the same book. Older DRs (DR-010, DR-013) use "persona" where the corrected reading is "account."

**Cash-flow reference data (Slice 5):**

- `account_holders` — custodian identity for the cash-flow model (Tim plus other people who hold operation cash on Tim's behalf).
- `payees` — recipients for non-bet outflows (tax, infrastructure, data subscriptions, tooling).
- `warning_catalogue` — closed-schema-open-vocabulary reference for AccountCare warnings.

**No `race` entity exists in v3.** Race-side data lives in capture.db. Bets carry race-side identifiers as references, not as foreign keys: Betfair `market_id` (primary), the natural-key tuple `(race_date, venue_normalised, race_number)` (fallback). Race classification, distance, surface, finish position, runner detail, BSP, time-series snapshots — none of these live on v3 entities. Where v3 needs them, it reads on demand through the integration module described in §5.

---

## 4. Event log — the spine

v3's accounting layer is event-sourced. A single append-only event log holds every event type. Derived state (balances, FB inventory, hedge state, reconciliation views) is computed at read time from the event log per DR-019 — v3 stores no aggregates and no balances.

**Common event header.** Every event carries: `event_id`, `event_type` (closed enum), `recorded_at` (system clock at write time), `occurred_at` (when the underlying real-world fact happened), context FKs (`account_id` / `book_id` / `account_at_book_id` where relevant), `supersedes_event_id` (nullable; for corrections), `parent_event_id` (nullable; e.g. `bet_settled.parent_event_id` → `bet_placed`), `payload` (JSON, type-specific), `source`, `correlation_id`, `notes`.

**Event categories.** Consolidated from Slices 2–6:

- *Bet lifecycle* — `bet_placed`, `bet_correction`, `bet_settled`, `bet_leg` (SGM legs), `lay_order_finalised`, `hedge_state_classification`.
- *Promo lifecycle* — `promo_observed`, `promo_journey_annotation`, `free_bet_credited`, `free_bet_deployed`, `free_bet_revoked`, `free_bet_expired`, `promo_cash_credited`.
- *AccountCare* — `accountcare_warning_raised`, `accountcare_warning_cleared`.
- *Cash flow (two-balance-location model)* — `account_holder_funding`, `account_at_book_deposit`, `account_at_book_withdrawal`, `account_holder_remittance`, `account_at_book_balance_adjustment`, `account_holder_balance_adjustment`, `external_payment`, `profit_share_distribution`.

**Supersession semantics.** Corrections never delete or modify the prior event. A correction writes a new event with `supersedes_event_id` pointing at the prior event; both remain in the log permanently. Derived state walks the supersession chain at read time, treating only the most-recent non-superseded event as authoritative. Cascade rules govern what other event types are auto-superseded when a `bet_settled` is superseded — closed list, day-one limited to `free_bet_credited` and `promo_cash_credited`, with auto-cascade for mechanically-clean full invalidation and manual cascade (operator-explicit) for graded cases.

**Two-balance-location cash-flow model (Slice 5 + Session 14 amendment).** v3 tracks two balance locations: account-at-book balances (Location 1, derived from cash-flow events touching specific account-at-books) and cash holdings with custodians (Location 2, derived per-custodian from funding, deposits, withdrawals, remittances, profit-share distributions, and balance adjustments). Tim's personal bank account is *not* in the model — Tim's bank includes personal activity v3 does not see, so v3 cannot produce a "current bank balance" figure. An informational *operation-net-flow* view computes cumulative net impact on Tim's bank since day 0 from the four bank-touching event types (funding out, remittance in, external payment out, profit-share distribution out where funded directly from Tim). It is informational, not a reconciliation surface (§6 distinguishes).

---

## 5. Cross-DB integration boundary

### 5.1 capture.db — what it is

capture.db is an existing SQLite database running on a UK VPS as part of the racing-data capture system. It captures Betfair time-series price-and-volume snapshots and bookmaker scrape data for Australian thoroughbred, harness, and greyhound racing on a tiered cadence (5 min standard / 60s pre-jump intensive in the 5-min window before scheduled jump / 60s in-running / 2-min settlement checks). It also stores race results, BSP, and daily calibration summaries. The system predates v3 by months and runs continuously on the VPS itself.

The consumer situation today, framed honestly: BetHub v2 has code wired to capture.db's data API — the racing page and the betfair_sync settlement path both call it — but in practice the SSH tunnel that v2 needs for VPS reach is frequently down for extended periods (at the moment of writing, the tunnel has been unreachable continuously for at least six days, with v2 logs showing health-check failures every 30 seconds throughout). v2 has been operating normally throughout this window because its actual settlement path is direct to Betfair API, not via VPS, and the racing page isn't a primary operator surface. So although capture.db has been collecting data the whole time, it has no real active consumer at the moment. v3 is the first consumer that will use the data layer at execution time — at every bet log, on every settlement, in burst review.

This materially changes the operational stakes on tunnel reachability. v2 demonstrates that "VPS unreachable for a week, no one notices" is the empirical default. v3's design has v3 reading capture.db on every bet log; the `bf_snapshot_unavailable = true` graceful-degrade flag in DR-026 is currently theoretical insurance against a failure mode v2 has demonstrated is actually common. v3 building on top of an integration the operator has not had to keep alive operationally is a real risk worth naming explicitly. v3 does not own capture.db, does not write to it, and does not duplicate any of its data — but v3 *does* take on a continuous-availability requirement that v2 has not enforced.

Sports markets (AFL, NRL, others) are *not* covered by capture.db today. Day-one v3 sports bets log with a `bf_snapshot_unavailable = true` flag until a sports-capture extension is built — first item in the upcoming DR-029 data review.

### 5.2 The boundary

Per DR-027 (two-database architecture):

- v3 references race-side data by stable identifier — primarily Betfair `market_id`, fallback the natural-key tuple `(race_date, venue_normalised, race_number)`.
- v3 reads race-side context on demand through the existing read-only data API on the VPS (currently `racing-api.service`, reached over SSH tunnel at `127.0.0.1:8400`).
- Cross-DB joins happen at read time in Python at the integration boundary — not in SQL.
- All v3 access flows through one Python module (working name `vps_client`). No raw SQLite reads from capture.db elsewhere in v3. No second HTTP client. No bypass.

Per DR-028 (integration boundary discipline), four patterns are forbidden:

1. **No race-data caching in v3.** v3's database stores no race-data fact. The single narrow exception is the DR-026 inline market-context snapshot on `bet_placed` (best back/lay price + size, total matched, snapshot timestamp), justified explicitly on cross-system-durability grounds — and itself flagged as one of the four review questions for this assessment.
2. **No race-data denormalisation onto v3 entities.** No race classification, no distance, no surface, no finish-position-derived-from-VPS on v3 rows. The Slice 6 `field_size_at_bet_placement` and `field_size_at_settlement` fields on `bet_settled` are bet-context captures (race state at specific bet-context moments), not race-context denormalisations — they are also under review alongside the DR-026 inline snapshot, as one paired question.
3. **No second integration point.** Schema drift, contract changes, and integration failures must surface in one file, not scattered.
4. **No reflexive extension to additional external sources.** Adding a third data source (a second VPS service, a third-party API, another database) requires its own architectural decision; the DR-027 pattern grants no standing permission.

### 5.3 Read-time uses

| v3 event or query | Reads from capture.db (via vps_client) |
|---|---|
| `bet_placed` write (live mode) | Latest snapshot for `(market_id, runner_id)`; scratch state at `bet_placed_at` |
| `bet_placed` write (retrospective) | Same, with snapshot-aligned-to-placement flag = false |
| `bet_leg` write (SGM) | Per-leg snapshot for each leg's `(market_id, selection_id)` |
| `bet_settled` auto-settlement | Race result for `event_id` (finish positions, dead-heat, scratch list) |
| Burst Review filter by race class | Race classification for each bet's `event_id` |
| Analytical queries (timing, counterfactual, EV calibration) | Full price-and-volume curve from time-series |

### 5.4 Periodic-only API pattern (DR-029)

The data API returns the most-recent stored snapshot from capture.db (typically 0–60 seconds old in pre-jump windows) with its timestamp, plus scratch state. v3 stores this inline on the bet record and marks staleness flags above tunable thresholds. **No on-demand fresh-now snapshot pattern is added to the API.** The analytical justification is bracketing: surrounding-interval snapshots (T-x and T-x+cadence) read from capture.db at analysis time bracket the bet's true market state across the bet timestamp, observing market movement *around* the bet rather than at a single point — structurally stronger than a single fresh on-demand snapshot. Cadence verification is a data-review item; if pre-jump cadence proves insufficient, resolution paths in priority order are: extend the pre-jump intensive window, tune standard-cadence interval, accept staleness with operator-visible indicator. On-demand is a last resort. This pattern is one of the four review questions.

---

## 6. Reconciliation surfaces

Reconciliation is what v3 is named for. Six reconciliation surfaces are produced as natural outputs of derived state vs. operator-observed reality. Each lives in its own view; each is a derived-on-read computation against an external check.

| Surface | Compares |
|---|---|
| **Cash reconciliation** | Computed at-book balance (Location 1) vs operator-entered actual book balance |
| **Free-bet reconciliation** | Computed FB inventory vs operator-counted FB credits visible at the book |
| **Settlement reconciliation** | v3 auto-settled bets vs operator's observation of book payout |
| **Race-result reconciliation** | capture.db race result vs book settlement |
| **Hedge reconciliation** | Hedge state per the derivation algorithm vs operator's mental model |
| **Cash-holding-with-custodian reconciliation** | Computed Location 2 per custodian vs custodian's actual bank balance dedicated to the operation |

**Operation-net-flow view (informational, not a reconciliation surface).** Cumulative net impact on Tim's bank since day 0, derived from the four bank-touching event types. It is *not* a reconciliation surface because Tim's actual bank statement isn't an apples-to-apples external check — it includes personal spending v3 does not see. Operation-net-flow answers "since day 0, how much net cash has the operation pulled from / returned to my bank." It does not answer "what is my current bank balance."

**Settlement-divergence philosophy (DR-029).** VPS race result is canonical for "what happened in the race." Operator-recorded book settlement is canonical for "what the operator's cash outcome was." Where the two diverge — voids per book rules, dead-heat handling differences, stewards' inquiry resolutions — the divergence is a reconciliation signal, not an algorithmically-resolved conflict. No confidence hierarchy is built; the architecture treats divergence as information.

**Burst Review — the operator-facing detection workflow.** Two terms first. *Burst* is v3's name for an unplanned span of opportunistic operating time, triggered by available promos — can last 20 minutes (a casual Tuesday afternoon) or 6+ hours (a Saturday spring-carnival day); within a burst the operator switches rapidly between accounts and books to take time-sensitive promos before race jumps. *Persona session* is the contrasting mode: an explicit, planned span operating as a single account for non-time-critical work (conditioning bets, browser activity, account upkeep), with profile and isolation infrastructure locked to that account for the duration. Bursts and persona sessions are the two operating-mode contexts; together they cover every operator-active moment, and DR-024's operating/analytical separation applies during both. (Vocabulary note: persona-session terminology is from DR-010, before DR-022 corrected "persona" to "account" — read it as a single-account session.)

Reconciliation surfaces feed a Claude-driven burst-review triage workflow designed in as a day-one capability. Claude extracts everything flagged across the six surfaces and other anomaly signals, investigates each, and presents the operator with a triaged list. Operator-initiated, Claude-driven. This is the v3 successor to v2's flagged-items page (which was a passive surface that didn't get traction). The cost of administrative overhead and detection time is the operator's named first concern in the DUR; the burst-review design is the structural answer.

---

## 7. DR index — short reference for back-cites in this document

- **DR-002** — three-layer separation (operational / execution / accounting) with strict boundaries.
- **DR-007** — vocabulary discipline: definitions of "concern," "decision," "principle," "metric" locked.
- **DR-019** — derived state computed on read, not stored. Bets and operations log entries are the source of truth; everything else is computed at read time.
- **DR-022** — vocabulary correction: `account` (person) / `book` (bookmaker) / `account-at-book` (registration).
- **DR-024** — operating-mode and analytical-mode surfaces are separated; operating-mode does not show "how am I doing" data.
- **DR-026** — at-log-time market-context snapshot captured on every bet (single narrow caching exception per DR-028 forbidden pattern 1; under review).
- **DR-027** — two-database architecture: v3 bet-data and capture.db race-data are separately owned, joined at read time by reference.
- **DR-028** — integration boundary discipline: four forbidden patterns (no race-data caching, no race-data denormalisation, no second integration point, no reflexive extension to additional external sources).
- **DR-029** — data layer reviewed and brought to v3 fit-for-purpose before v3 build begins; periodic-only API pattern with analytical bracketing locked; settlement-as-reconciliation-not-hierarchy locked.

Slice records (Slices 1–6) live as session logs in the rebuild folder; this document compresses what they collectively lock. The full reconciliation-contract walkthrough is in `architecture.md` §A.0–A.9; this document is the framed-for-outside-readers compression.
