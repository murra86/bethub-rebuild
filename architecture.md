# Architecture

This document describes the v3 design at a high level. Diagrams referenced here live in `diagrams/`.

## Status

**Not yet designed.** This document will be filled out in Session 2.

What we know so far:

- The system breaks naturally into three layers (operational, execution, accounting) with strict boundaries between them — see DR-002 in `decisions.md`
- 15 functional concerns identified in Session 1 — see `diagrams/v2_current_state.svg` and `diagrams/v3_gap_analysis.svg`
- Not all 15 ship in v3 day one. Triage is a Session 2 task.

## Three layers (placeholder)

To be expanded in Session 2.

**Operational layer** — daily/weekly cadence. Profile switching, hygiene budgeting, AccountCare, promo allocation. The bedrock.

**Execution layer** — per-bet cadence. Bet logging, hedging, EV calculations, live odds. Fast, focused, narrow.

**Accounting layer** — quiet background. Ledger, reconciliation, reports. Invisible when working, impossible to break.

## Open architectural questions

- v3 build strategy — strangler-fig (new ledger alongside old) vs clean break (freeze v2, build v3 separately)
- Where does the operations log live (separate table, separate service, append-only file)
- Single canonical source of truth per number — what is the contract
- Three-layer boundaries — what is the interface between them

---

# Reconciliation contract — data flow across Slices 1–6

*Promoted from `SESSION_12_SCRATCH_v2.md` Session 14 (2026-04-28 15:35 ACST). Sits alongside, not replacing, the slice-by-slice locked records in `sessions/`.*

## Reconciliation contract


### A.0 What this contract is, and what it isn't

**Is:** a description of how data flows across the v3 accounting-layer database, from entity reference through event log through derived state, including the cross-DB boundary into `capture.db` (the existing UK VPS racing-data capture system) where race-side facts are owned. The goal is a single document that lets any reader understand "given a bet was placed, here is the full chain of events, references, and derived state that determines what the operator sees and what the analytical surfaces compute."

**Isn't:** a re-derivation of slice locks. Slices 1–6 are locked. Where this contract names a field, an event type, or a derivation rule, the locked slice record is the canonical source. Cross-references are included; restatement is avoided where possible.

**Isn't:** an architectural decision document. New architectural decisions are made via DRs in `decisions.md`. Where this contract surfaces a question that could affect architecture (notably the bet schema simplification question deferred to Session 15 multi-agent review), it flags the question and points at the existing review path; it does not pre-empt the review.

**Reading order:** the contract walks data flow forward from entity reference (A.1), through the bet-record and per-domain event-table spine (A.2), through the bets-row schema (A.3), through promo and credit chains (A.4), through cash flow (A.5), through settlement and hedge state (A.6), through cascade chains (A.7), through cross-DB integration (A.8), and closes with the derivation rules that compute everything visible in the system (A.9). Part B then extracts the v3 data requirements as a self-contained statement.

---

### A.1 Entity references — the stable identifiers everything else hangs off

Eight v3-side entities (Slice 1 lock per `sessions/SESSION_05.md`, Q9 amendment from Session 11):

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

**Plus the cash-flow reference data added in Slice 5:**

- `account_holders` — `account_holder_id`, `name`, `is_self` (bool, true for Tim), `active`. Custodian identity for the cash-flow model.
- `payees` — `payee_id`, `name`, `default_category`, `active`. Recipients for `external_payment` events (tax, infrastructure, data subscriptions, tooling).
- `warning_catalogue` — `warning_type`, severity baseline, descriptive metadata. Reference data for AccountCare warnings (Slice 4 addition; closed-schema-open-vocabulary pattern).

**Plus reference data implicit on entities above:**

- `account_arrangement` — history of intents with effective dates (Slice 1 lock C-resolution). Type enum `onboarding_sweetener` / `ad_hoc_performance_share` / `structured_share`. Optional `terms_json` for `structured_share` only. Free-text reasoning per row. Settlement payments are cash-flow events, not arrangement edits.

**No `race` entity exists in v3.** Race-side data lives in `capture.db` per DR-027. Where v3 needs race-side context (race classification, distance, surface, finish position, runner detail, BSP, time-series snapshots), v3 reads `capture.db` on demand via `vps_client` (the single integration module per DR-028).

**Race-side identifiers carried on `bet_placed` payloads:**

- `event_id` — Betfair `market_id` for the race-as-betting-market. Stable identifier; primary resolution path for race-side context.
- `bf_market_id` — same value as `event_id`, scoped to the Betfair-source meaning per DR-026. Retained as a separate field for source-clarity.
- `(race_date, venue_normalised, race_number)` — natural-key tuple available as fallback resolution path when Betfair identifiers are missing or ambiguous (retrospective entries, market ambiguity).

These are references, not foreign keys. v3 has no FK constraint to a race table. Resolution happens at read time through `vps_client`.

---

### A.2 Bet records and per-domain event log tables — the spine

v3's accounting-layer storage spine is **mutable bet records** (per DR-032 — the canonical-reference-layer schema, two-table shape: `bets` table + `bet_legs` table) plus **three per-domain event log tables** for events that do not sit on the bet record. The original single-event-log spine described in earlier versions of this section was superseded — bet lifecycle state (match status, settlement state, hedge state, reconciliation bookkeeping) sits as mutable columns directly on the `bets` row rather than as an event chain. See DR-027's Session 124 amendment for the architectural rationale; the locked schema commitment is DR-032.

**The shape, at a glance:**

- **`bets` table** — one row per bet. Owns bet-as-a-whole properties (stake, soft-book combined price, account context, promo metadata, strategy tag, timestamp, settlement state, match state, hedge state, reconciliation bookkeeping, DR-026 market snapshot). Mutable on settlement and reconciliation passes. Detailed schema in §A.3.
- **`bet_legs` table** — N rows per bet (one per leg). Owns per-leg Betfair identifiers (`betfair_market_id`, `betfair_selection_id`) and Set B denormalised display fields per DR-032. Immutable logging-time snapshots.
- **`cash_flow_events`** — append-only event log for cash flow (`account_holder_funding`, `account_at_book_deposit`, `account_at_book_withdrawal`, `account_holder_remittance`, `account_at_book_balance_adjustment`, `account_holder_balance_adjustment`, `external_payment`, `profit_share_distribution`). Owns balance derivation per §A.5. **W14 ships this table.**
- **`promo_events`** — append-only event log for promo lifecycle (`promo_observed`, `promo_journey_annotation`, `free_bet_credited`, `free_bet_deployed`, `free_bet_revoked`, `free_bet_expired`, `promo_cash_credited`, `accountcare_warning_raised`, `accountcare_warning_cleared`). Owns promo journey, FB inventory derivation, AccountCare warning derivation per §A.4. **W13 ships this table.**
- **`ops_events`** — append-only event log for ops-side observability (worker pass markers, retry events, scheduler triggers, reconciliation pass markers, hedge classification events, bet-correction audit entries). **W15 ships this table.**

**Why per-domain rather than a single event log:**

- **Aligns with operational shape.** Reads are mostly domain-scoped — balance derivation reads cash events; FB inventory reads promo events; ops debugging reads ops events. No cross-domain reporting requirement at v3's scale.
- **Cleaner workstream boundaries.** W14 / W13 / W15 each ship one event table and the surfaces that read from it.
- **Tighter indexes per table.** Each table carries its own indexes appropriate to its access patterns.
- **Schema flexibility per event type.** Each table carries its own payload-shape conventions without one-size-fits-all compromise.

**Common event header (all three per-domain event tables share the same structural shape):**

- `event_id` — primary key
- `event_type` — closed enum, scoped to the table's domain
- `recorded_at` — system clock at write time
- `occurred_at` — when the underlying real-world fact happened (operator-reported or system-derived; may equal `recorded_at` for live-mode events)
- `account_id` / `book_id` / `account_at_book_id` — first-class FKs where relevant; nullable per event type
- `parent_event_id` — nullable; points at a parent event in the same table (e.g., a `free_bet_deployed` chained from a `free_bet_credited`)
- `supersedes_event_id` — nullable; points at the event being replaced via per-domain supersession (see below)
- `payload` — JSON, type-specific fields per event_type
- `source` — where the event originated (operator, system, integration)
- `correlation_id` — links events in a single operational unit (a bet placement and its downstream promo credit, a settlement and its credit cascades)
- `notes` — free text, optional

**Per-domain event types (consolidated from Slices 2–6, distributed by domain):**

*`cash_flow_events` types (Slice 5 + Session 13 amendment):*
- `account_holder_funding` — Tim → custodian
- `account_at_book_deposit` — custodian → account-at-book
- `account_at_book_withdrawal` — account-at-book → custodian
- `account_holder_remittance` — custodian → Tim
- `account_at_book_balance_adjustment` — book-side non-bet/non-promo correction
- `account_holder_balance_adjustment` — **(Session 13 amendment)** custodian-side non-flow correction; symmetric to `account_at_book_balance_adjustment`. Day-one use: day-0 opening balances on custodian holdings via `adjustment_reason='day_0_opening'`. After day 0: operator-graded corrections (custodian counting corrections, etc.).
- `external_payment` — operational outflow to payee
- `profit_share_distribution` — distribution to account holder personally

*`promo_events` types (Slice 4):*
- `promo_observed` — point-in-time observation of a promo at a book
- `promo_journey_annotation` — operator interpretive context tagged to promo evolution (Slice 4 Q1)
- `free_bet_credited` — FB credit (triggered or freebie)
- `free_bet_deployed` — FB used on a bet (with `source_credit_event_ids` array)
- `free_bet_revoked` — book reclaims a pending FB
- `free_bet_expired` — system-derived where possible, operator fallback
- `promo_cash_credited` — cash bonus credit, symmetric with FB credit
- `accountcare_warning_raised` — warning surfaced for an account-at-book
- `accountcare_warning_cleared` — warning resolved

*`ops_events` types (Slice 6 amendments + W15):*
- Worker pass markers (`match_state_worker_pass`, `settlement_worker_pass`, `reconciliation_pass`) — observability for scheduled workers
- Retry events (`worker_retry_attempt`) — retry-with-backoff history for transient failures
- Scheduler triggers (`scheduler_trigger`) — when scheduled workers fired
- `hedge_state_classification` — operator-explicit or auto-set unhedged classification (per DR-025)
- `bet_correction` — operator edit to a bet record under DR-017, carrying old-value / new-value / operator-reason / timestamp
- `manual_operator_resolution` — operator action through W8 burst-review queue resolving a provisional bet

**Bet record mutation semantics (`bets` table — distinct from per-domain event tables):**

Bet records are mutable on settlement and reconciliation passes. The seven post-write-mutable columns (`match_status`, `settlement_state`, `dead_heat_count`, `removed_runner_count`, `unexpected_state_count`, `last_read_market_state`, `last_reconciled_at` / `reconciliation_attempts`) are updated in place by the W6 match-state worker, the W6.5 settlement worker, and the W8 manual operator resolution path. **Transitions are not historical — the previous value is overwritten when a transition fires.** This is acceptable per the operator's personal-operation scale and the absence of external audit obligation; if a future need for audit-trail history surfaces (operator takes on a partner, incorporates, regulatory shift), a transitions log can be added forward-only. The shipped pattern's reliability rests on three things: (1) worker logic is correct (substantial test coverage behind W6 / W6.5); (2) Betfair's `market_settlement` API returns truthful results; (3) misclassifications get caught operationally before they compound (W8 burst-review queue gives the surface to fix them). See DR-027 amendment for the full rationale.

**Bet-record edits via DR-017 fully-editable model:**

Operator edits to bet records (corrections caught during burst review or after-burst cleanup) update bet record columns in place. Each edit writes an `ops_events` row with `event_type='bet_correction'` carrying old-value / new-value / operator-reason / timestamp. Edit-audit trail is preserved at the ops-events layer; the bet record itself carries only current state.

**Supersession semantics (per-domain events only — DR-017 + Slice 2 F):**

Event corrections within a per-domain event table append a new event with `supersedes_event_id` set to the prior event. The prior event is **not deleted, not modified, not flagged-as-invalid in place** — it remains in the log permanently. Derived state per DR-019 walks the supersession chain at read time, treating only the most-recent non-superseded event as authoritative for that logical record. Chain depth is unbounded in principle, typically 0–2 in practice. Cascade rules (§A.7) determine when supersession of one event triggers recomputation of related events; cascades for bet-outcome corrections fire against the mutable `bets` row, not against an immutable settlement event.

---

### A.3 Bet record schema — the `bets` row and `bet_legs` rows

A bet is placed at a book. The operator triggers a log action through one of v3's entry surfaces — the racing screen's Log button or hedge modal (per Session 6 walkthrough), the sports screen's ladder action icons (per §B.1.2), or the soft-book entry path (per §B.2 — typed-price entry only). The system writes a row to the `bets` table plus one or more rows to the `bet_legs` table per DR-032. Mutable columns on the `bets` row are updated by downstream workers (W6 match-state, W6.5 settlement) and operator paths (W8 manual resolution per §C.1, DR-017 bet correction via `ops_events`).

**Identity and context columns:**

- `bet_id` — primary key
- `account_id`, `book_id`, `account_at_book_id` — context per active operating mode
- `entry_path` — closed enum: `racing_screen_log` | `racing_screen_hedge` | `sports_screen_log` | `sports_screen_hedge` | `softbook_entry` — names which entry surface wrote this bet (W4 / W4.1 / W7 surfaces)
- `strategy_tag` — closed enum: `safety_net` | `price_booster` | `correlated_friction` | `synthetic_each_way` | `unassigned` — names which of the four racing strategies this bet belongs to (per `project_context.md` §3)
- `cycle_id` — nullable; links bets that form one analytical cycle (insurance bet + triggered free bet, bonus-back original + bonus free bet, etc. — per the standing cycle-analysis convention in `governance.md`)
- `correlation_id` — links events in a single operational unit (a bet placement and its downstream promo credits, a settlement and its credit cascades)

**Stake and odds (bet-as-a-whole — per DR-032 rule 3, never on legs):**

- `cash_stake_amount`, `free_bet_stake_amount` — split per FB structural reshape; either or both can be non-zero
- `soft_book_combined_price` — the price the bookmaker quoted (single-leg price for non-multi bets; SGM combined price for multi-leg bets)
- `pending_fb_deployment` — boolean; true when FB stake recorded but no `free_bet_deployed` event yet (Slice 4 lock — the deployment event lives in `promo_events`)
- `bet_type` — e.g., win, place, each-way, SGM
- `is_free_bet` — boolean

**Time discipline:**

- `recorded_at` — system clock at write time
- `bet_placed_at` — when the bet was actually placed at the book
- `placement_time_source` — enum: `live_logged` (system-stamped, equals `recorded_at`) | `retrospective` (operator-entered)

**Price source provenance:**

- `price_source` — closed enum: `operator_typed` | `betfair_live` | `softbook_scrape_<book>` — names where the at-log soft-book price came from. Per §B.2, day-one is operator-typed only for soft-book bets; field exists for forward-compatibility with future scrape integrations.

**Promo linkage:**

- `promo_instance_id` — nullable; FK to a `promo` reference row (which links to `promo_template`)
- `promo_type_at_log` — denormalised promo kind for analytical convenience

**Betfair market-context snapshot (DR-026 + Session 11 amendment + Session 124 amendment):**

- `bf_market_id`, `bf_runner_id`, `bf_runner_name` — Betfair identifiers and denormalised display name (snapshot pattern, immutable)
- Best back price + size, best lay price + size, total matched at snapshot time
- `snapshot_timestamp` — when capture.db actually captured this snapshot
- `snapshot_age_seconds` — derived at log time (`recorded_at − snapshot_timestamp`)
- `stale_flag` — true if snapshot_age above threshold (tunable, e.g. 90s)
- `bf_snapshot_unavailable` — true if VPS unreachable or no recent snapshot
- `bf_snapshot_aligned_to_placement` — true for live-mode logging (snapshot is reasonably aligned to placement); false for retrospective entry
- `late_scratch_between_snapshot_and_log` — boolean; true if a scratching event occurred in capture.db between `snapshot_timestamp` and `bet_placed_at`

Beyond the fields above, no additional market-context snapshot fields live on the bet record. Deeper market context (depth beyond best price, time-series around placement) lives in `capture.db` and is reached via cross-reference (`betfair_market_id` + `bet_placed_at`) at analysis time per the DR-026 Session 124 amendment.

**Betfair hedge linkage (for bets hedged on Betfair):**

- `betfair_bet_id` — nullable; Betfair's identifier for the lay order placed against this bet. Populated when the hedge modal places a lay. NULL for unhedged bets.

**SGM extension:**

- `is_sgm` — boolean
- `leg_count` — integer

**Model fields (nullable until model built):**

- `model_estimated_odds`, `model_estimated_probability`, `model_version`, `model_estimated_at`
- `model_pairwise_probabilities` — JSON array, populated only when model exposes pairwise joints (SGM calibration)

**AccountCare context:**

- `active_warnings_at_log` — JSON array snapshot of warnings active at log time, for outcome-vs-warning analysis

**Mutable bet-lifecycle columns (Session 124 — written by W6 / W6.5 / W8 workers per §A.2 bet record mutation semantics):**

- `match_status` — `MatchStatus` enum: `PROVISIONAL` | `PROVISIONAL_PENDING` | `FINAL_FULL` | `FINAL_PARTIAL` | `FAILED`. Written by the W6 match-state worker as the Betfair market settles and resolution against the bet's selection completes. `PROVISIONAL_PENDING` is a transient state covering the window between settlement-event observation and match resolution.
- `settlement_state` — `SettlementState` enum: `PENDING` | `SETTLED_WON` | `SETTLED_LOST` | `VOIDED` | `PROVISIONAL`. Written by the W6.5 settlement worker once `match_status` is terminal. `PROVISIONAL` is the burst-review-surface state — settlement could not be resolved automatically and the operator needs to confirm via W8 (per §C.1 Burst Review).
- `dead_heat_count` — integer; how many dead-heat resolutions affected this bet. Drives proportional payout calculation per Betfair's dead-heat rules.
- `removed_runner_count` — integer; how many runners were removed from the race after this bet was placed. Drives Rule 4 deductions.
- `unexpected_state_count` — integer; counter for unhandled match-state transitions. Worth surfacing to ops debugging if non-zero.
- `last_read_market_state` — JSON; snapshot of the Betfair market state the worker last read (selection settlement status, market status, runner statuses). Used for forward debugging and for idempotent re-read on retry.
- `last_reconciled_at` — timestamp; latest worker pass that touched this bet.
- `reconciliation_attempts` — integer; how many worker passes have touched this bet.

**Retry-with-backoff timings (Session 124 — bet records carry retry state for transient failures):**

- `last_retry_at` — nullable timestamp; last retry attempt time.
- `next_retry_at` — nullable timestamp; scheduled next retry time. Worker scheduler reads this to pick up retry candidates.
- `retry_count` — integer; retry attempts since the last clean read.

**Bet legs (`bet_legs` table — per DR-032 two-table shape):**

Each leg of a bet writes a separate `bet_legs` row with `bet_id` foreign key:

- `bet_id` — FK to `bets`
- `leg_number` — integer ordering (1, 2, 3, ...)
- `betfair_market_id`, `betfair_selection_id` — the canonical join keys per DR-032
- Set B denormalised display fields per DR-032: `betfair_event_name`, `betfair_market_name`, `betfair_selection_name`, `betfair_event_venue`, `betfair_event_sport`, `betfair_event_start_time` — immutable logging-time snapshots
- `betfair_implied_probability_at_log_time` — nullable; per-leg Betfair-implied probability at logging time (used for SGM correlation analytics, per DR-032 point 8)
- `model_leg_probability` — nullable; per-leg model-estimated probability

**No stake or combined-price columns on `bet_legs`.** Stake and combined price live exclusively on the `bets` row per DR-032 rule 3. Single-selection bets are `bets` rows with one leg row. SGMs are `bets` rows with N leg rows. The schema is uniform across both shapes.

**At log time, the read into capture.db is:**

1. `vps_client.get_latest_snapshot(betfair_market_id, betfair_selection_id)` returns the most-recent stored snapshot with timestamp (for each leg).
2. `vps_client.get_scratch_state(betfair_market_id, as_of=bet_placed_at)` returns whether any scratchings occurred in the relevant interval.
3. v3 inlines the snapshot fields onto the `bets` row, sets stale/unavailable/aligned/late-scratch flags accordingly.

This is the **single integration boundary** per DR-028. No other v3 module reads `capture.db`; no v3 module writes to `capture.db`.

---

### A.4 Promo and credit chains

Promos are observed before they are taken. The data flow has three legs: observation, taking, and crediting.

**Leg 1 — Observation (Slice 4):**

The operator (or a future automated promo scanner) writes `promo_observed` events when a promo is seen at a book. Payload:
- `promo_template_id` — FK to reference data; templates capture kind-level mechanics (~10–30 rows; insurance / bonus / boost / EW cashback)
- `book_id`, `account_at_book_id` (if scoped per-account)
- `terms_at_observation` — JSON; carries the parametric variation (max_stake, min_odds, qualifying odds bands, eligible codes, expiry rules)
- `scope` — closed enum: all-races / specific-race / specific-event / specific-market
- `active_window_start`, `active_window_end`

**Promo journey is computed on read** (Q1 lock from Session 8):
- No `promo_terms_changed` event type exists.
- Successive `promo_observed` events on the same `(promo_template_id, book_id, account_at_book_id)` form a journey timeline.
- Promo shrink (e.g., insurance cap dropping from $50 to $10) is detected by comparing terms_at_observation between consecutive observations.
- `promo_journey_annotation` events capture operator interpretive context with tags (closed-schema-open-vocabulary), optional time_window, optional related_event_ids, confidence (hypothesis → confirmed/disproven).

**Leg 2 — Taking (Slice 3 + Slice 4):**

When the operator places a bet against a promo, the bet's `promo_instance_id` column links to a `promo` reference row, which links via FK to the `promo_template`. The `promo_observed` events are the journey context for that template-at-book at that time, but the bet does not directly link to a specific observation event — it links to the template via the promo instance.

`promo_type_at_log` is denormalised onto the bet payload for analytical convenience (avoids a join walk through promo → promo_template every time).

**Leg 3 — Crediting (Slice 4):**

Two crediting paths:

*3a — Triggered:* an insurance bet settles in a way that fires the trigger (e.g., 2nd-place finish on a "money back if 2nd" promo). The bet's `settlement_state` transition to a terminal state (typically `SETTLED_LOST` on insurance loss; per §A.6) causes a `free_bet_credited` event to be written in `promo_events` with:
- `triggering_bet_id` → the `bet_id` of the triggering bet (whose loss caused the credit)
- `triggering_promo_instance_id` → the promo the bet was taken against
- `credit_source = 'triggered'`
- `amount` — face value of the FB
- `status` — `provisional` initially if confidence is low; `finalised` for two-source-agreement or high-confidence single-source per Slice 2 D-resolution
- `confidence_payload` — JSON, shape per the deferred confidence model (Q2 from Session 8)

For `promo_cash_credited` (cash bonus promos like 25% boost on winnings): same structure, settlement_type=`cash` instead of `free_bet`. Payload mirrors `free_bet_credited` plus `funding_source` is implicit (always book-side credit).

*3b — Freebie:* manual FB credits (random goodwill from book, phone-call grants, non-bet-triggered promotions). Operator writes `free_bet_credited` directly with `credit_source = 'freebie'`. No triggering bet linkage.

**FB deployment chain (Slice 4 reshape from Session 7):**

When an FB is used on a subsequent bet, that bet's `free_bet_stake_amount` column is non-zero, and a separate `free_bet_deployed` event is written in `promo_events` with:
- `deploying_bet_id` → the `bet_id` consuming the FB
- `source_credit_event_ids` — JSON array; the credit events being drawn down (many-to-many junction)
- `draw_down_breakdown` — JSON; per-credit amount drawn (because one deployment can consume part of multiple credits)
- FIFO-by-expiry is the universal default; operator override supported

`pending_fb_deployment` flag on the bet handles the case where the FB stake is logged but the deployment event hasn't been written yet (e.g., credit is `provisional`, awaiting finalisation; or operator hasn't yet resolved which credits to draw from). Burst Review surfaces unaccounted FB deployments.

**FB lifecycle terminal events:**

- `free_bet_revoked` — book clawback. Status field on the `free_bet_credited` event is updated via supersession (writing a new credit event with status='rejected' and reason).
- `free_bet_expired` — system-derived where possible (expiry date in `terms_at_observation`); operator-entered fallback.

---

### A.5 Cash flow — two balance locations and operation-net-flow view

**Read/write asymmetry — project-level design principle.**

This principle applies across all v3 derivations, not just cash-flow:

- **Writes go through the typed workflow adapter** (`workflows/<domain>/v1/<domain>_store_adapter.py`). The adapter enforces payload contracts, supersession discipline on event tables, and DR-019 state-on-row semantics on entity tables.
- **Reads default to the adapter as well.** A derivation may drop directly to the SQL layer (`store/repositories/<domain>.py`) where the adapter exposes no matching read method, but each drop is a named exception, not the path of least resistance. Adapter-first is the default for future workstreams.
- **SQL drops replicate adapter-side business logic explicitly.** Bypassing the adapter does not bypass the need for the logic — supersession filtering and latest-event-per-scope selection on event tables; state-on-row semantics on entity tables. The replicated logic is named in a code comment at the drop site, and surfaced in the ship report alongside the drop.

The cash-flow model (Slice 5 + Session 13 amendment) has **two balance locations**, both derived per DR-019 from the cash-flow event types. **Tim's personal bank account is not in the model** — it is a personal bank account used for non-operation purposes too, so direct inclusion would conflate operation cash-flow with personal spending. v3 does not see the bank; it cannot and does not produce a "current bank balance" figure. Instead, an **operation-net-flow informational view** computes cumulative net impact on the bank from operation activity since day 0.

**Bank-touching vs internal cash-flow events.**

The cash-flow event types fall into two categories from Tim's-bank perspective:

| Event type | Touches Tim's bank? | Effect |
|---|---|---|
| `account_holder_funding` | Yes | Outflow (Tim → custodian) |
| `account_holder_remittance` | Yes | Inflow (custodian → Tim) |
| `account_at_book_deposit` | No | Internal: custodian → book |
| `account_at_book_withdrawal` | No | Internal: book → custodian |
| `account_at_book_balance_adjustment` | No | Internal: book-side correction |
| `account_holder_balance_adjustment` | No | Internal: custodian-side correction (incl. day-0 openings) |
| `external_payment` | Yes | Outflow (Tim → payee) |
| `profit_share_distribution` | No | Internal: pure ledger reallocation. Holder's bank IS the parked pool — profit-share marks dollars already in the holder's bank as the holder's own funds rather than operational capital. Reduces Location 2; never touches Tim's bank. |

The `account_at_book_deposit`/`withdrawal` pair is internal slosh between Locations 1 and 2 and cancels at the system-total level. The `*_balance_adjustment` events are model-side corrections (including day-0 opening entry path for both locations) and never touch Tim's bank. `profit_share_distribution` is never bank-touching under the clarified model — the holder's bank account is the parked pool, so a profit-share is pure ledger reallocation marking already-in-holder's-bank dollars as the holder's own funds rather than operational capital. No physical movement; no Tim's-bank touch.

**Location 1: Account-at-book balances.**

Per (account × book) registration, derived from:

- Sum(`account_at_book_deposit`) inflows
- − Sum(`account_at_book_withdrawal`) outflows
- ± Sum(`account_at_book_balance_adjustment`) signed adjustments
- − Sum(`bets.cash_stake_amount`) cash stakes placed
- + Sum(per-bet computed `cash_returned` per §A.6) cash returns
- + Sum(`promo_cash_credited` where status=`finalised`) bonus cash credits

The **at-book balance includes finalised promo_cash credits as positive contributions** but does **not** include FB face value (FBs sit in their own pool, not the cash balance, until deployed).

Day-0 opening balances at v3 launch enter via `account_at_book_balance_adjustment` events with `adjustment_reason='day_0_opening'`. After day 0, `account_at_book_balance_adjustment` is the operator-graded book-side correction event.

**Location 2: Cash holdings with custodians.**

Per account_holder, derived from:

- + Sum(`account_holder_funding` where account_holder_id = X) — Tim → custodian
- + Sum(`account_at_book_withdrawal` where account_holder_id = X) — book → custodian
- − Sum(`account_at_book_deposit` where account_holder_id = X) — custodian → book
- − Sum(`account_holder_remittance` where account_holder_id = X) — custodian → Tim
- − Sum(`profit_share_distribution` where account_holder_id = X)
- ± Sum(`account_holder_balance_adjustment` where account_holder_id = X) signed adjustments

The Location 2 primitive is per account-holder. A per-bookmaker cross-account view (cash with a single book aggregated across all holders' accounts at that book) is surfaceable as a separate informational read for spot-check of single-book concentration; it is not part of the core balance derivation. Refinement deferred until v3 reads run operationally.

Day-0 opening balances at v3 launch (~$12.5k of working capital across custodians) enter via `account_holder_balance_adjustment` events with `adjustment_reason='day_0_opening'`. After day 0, `account_holder_balance_adjustment` is the operator-graded custodian-side correction event (custodian counting corrections, etc.).

**Cash age per custodian:** FIFO walk of funding events (and day-0-opening balance adjustments treated as initial deposits for age purposes) against draw-downs; oldest unconsumed funding gives maximum age. Surfaced in Burst Review when above operator-tunable threshold (working-capital surveillance).

**Profit share semantics:**

The holder's bank account IS the parked pool — they are literally the same physical money. A `profit_share_distribution` event records a ledger reallocation: dollars already sitting in the holder's bank get marked as the holder's own funds rather than operational capital. No physical movement happens, and Tim's bank is never touched by a profit-share event.

A $1,500 transfer from Tim with $200 profit share recorded yields:
1. `account_holder_funding`: $1,500 (the $1,500 lands in the holder's bank)
2. `profit_share_distribution`: $200 (of the $1,500 sitting in the holder's bank, $200 is reallocated from operational capital to the holder's own funds)

Net cash-holding-with-custodian (operation's claim): $1,300. The remaining $200 is still physically in the holder's bank, but accrues to the holder personally, not the operation. No creditor balance, no separate transfer.

**External payments:** to non-custodian payees (tax, infrastructure, data subscriptions, tooling). `payees` reference data table holds recipient identity. Categorisation enum on event payload.

**Operation net flow — informational derived view (not a balance, not a reconciliation surface).**

Cumulative net impact on Tim's bank since day 0, derived from the three bank-touching event types:

```
operation_net_flow = + sum(account_holder_remittance)
                     − sum(account_holder_funding)
                     − sum(external_payment)
```

Surfaced informationally in Burst Review or Reports. Answers "since day 0, how much net cash has the operation pulled from / returned to my bank." Does **not** answer "what is my current bank balance" — Tim's bank includes personal spending v3 does not see, so v3 cannot and does not produce that figure. Operation-net-flow is **not** a reconciliation surface; it has no external check by design (Tim's actual bank statement isn't an apples-to-apples comparison because it includes personal activity).

The `*_balance_adjustment` events do not appear in the operation-net-flow formula because they are model-side adjustments, not flows. Day-0 openings entered via balance-adjustment events represent capital already committed to the operation before v3 launch — they neither add to nor subtract from the running total of "net cash pulled from Tim's bank since day 0."

**Money in transit not modelled.** A withdrawal-vs-remittance timing gap (book funds left the book but haven't yet hit Tim's bank) produces a brief understatement in operation-net-flow that clears when the remittance is logged. Acceptable noise; not worth modelling explicitly. No `account_holder_funding_pending` or transit-state event type is added.

---

### A.6 Settlement and hedge state

**Settlement state and hedge state both live as mutable columns on the `bets` row** per the §A.2 spine. Settlement state is written by the W6 (match-state) and W6.5 (settlement) workers; hedge state is operational scope deferred to post-W15 work (see "Hedge state — deferred" below).

**Settlement model — no algorithmic confidence hierarchy (DR-029):**

The DR-029 close-out lock dissolved the prior "confidence hierarchy" framing for bet settlement. The architecture is:

- **VPS race result is canonical for "what happened in the race."** Auto-settlement reads finish position and basic race result from `vps_client` per DR-027 / DR-028.
- **Book settlement (the at-book cash outcome) is canonical for "what the operator's cash outcome was."** Operators surface this through normal reconciliation review.
- **Divergences are reconciliation signals**, not algorithmic resolution. Surfaced in Burst Review (§C.1) or session reconciliation reports.

**Settlement state on the `bets` row (W6 / W6.5 workers, Session 124 — see §A.3 for column definitions):**

- `match_status` (`MatchStatus` enum: `PROVISIONAL` | `PROVISIONAL_PENDING` | `FINAL_FULL` | `FINAL_PARTIAL` | `FAILED`) — written by W6 as the Betfair market settles. `PROVISIONAL_PENDING` is transient between settlement-event observation and match resolution.
- `settlement_state` (`SettlementState` enum: `PENDING` | `SETTLED_WON` | `SETTLED_LOST` | `VOIDED` | `PROVISIONAL`) — written by W6.5 once `match_status` is terminal. `PROVISIONAL` surfaces to W8 burst-review queue when settlement could not be resolved automatically.
- `dead_heat_count`, `removed_runner_count`, `unexpected_state_count` — per-bet counters driving proportional payout (dead heat) and Rule 4 deductions (removed runners).

Auto-settlement that cannot resolve cleanly (Betfair market not yet settled past threshold, conflict between Betfair settlement and capture.db race result, partial-match ambiguity) surfaces as `settlement_state = PROVISIONAL` and routes to W8 burst-review queue for operator confirmation.

**Cash returned is computed on read per DR-019.** No `cash_returned_to_book` column is stored on the `bets` row. Cash return derives from `matched_stake × matched_price × dead_heat / removed_runner handling` against the bet's settlement state. If a worker re-read corrects any input (typo fix, dead-heat adjustment), the historical payout shifts retroactively — acceptable per the operator's personal-operation scale; no audit-trail history retained on the bet record (see DR-027 Session 124 amendment).

**Critical terminology distinction (Session 10, preserved):**

- `outcome` → cash-result. What happened to the bet's money. Derived from `settlement_state` plus matched-stake / matched-price / dead-heat handling.
- `finish_position` → physical-race fact. Where the horse came. Read at analysis time from `capture.db` via `vps_client`, not stored on the bet row.
- Promo trigger evaluation reads `finish_position` (e.g., insurance "money back if 2nd" reads `finish_position = 2` against capture.db).
- Cash-flow accounting reads `settlement_state` (e.g., `SETTLED_LOST` zeroes cash return).
- A win-only bet on a horse that places gets `settlement_state = SETTLED_LOST` and `finish_position = 2` (the latter read from capture.db).

**Settlement metadata still on spec, not yet shipped (post-W15 work):**

The following fields were originally specified in the `bet_settled` event payload (Slice 6 Session 10 amendments) and remain on spec but are not yet on the shipped bets row:

- `each_way_payload` — JSON, nullable; for each-way bets, separate win and place outcomes
- `sgm_leg_outcomes` — JSON array, nullable; per-leg outcomes for SGM (likely lives on `bet_legs` rather than `bets` once shipped)
- `field_size_at_settlement`, `field_size_at_bet_placement` — bet-context facts per DR-028 forbidden-pattern-2 rationale
- `result_source` — closed enum naming where the auto-settlement result came from (`betfair | racing_api | racing_australia | racenet | manual`)
- `result_observed_at` — when the source observed the result

These ship when downstream operational-layer work (W15+) hits a use case requiring them. The shape is not load-bearing for W14 / W13 / W12.

**Hedge state — deferred (DR-025, Finding #8 from S123 pre-W14 review):**

DR-025 specifies the five-terminal-states-plus-one-transient hedge classification model (`hedged` / `hedge_partial` / `hedge_failed` / `unhedged_deliberate` / `unhedged_oversight` / `unhedged_unclassified`). This model is **not yet shipped** as of the Session 123 codebase review — no `hedge_state` column on the `bets` row, no auto-classification flow, no operator surface.

The model is parked with tracking pointer and **revisit-before-W15-brief-drafting flag.** Strategy 2 (Price Booster) cycle measurement needs hedge classification to distinguish "deliberately didn't hedge because price moved against me" from "tried to hedge and it failed". The revisit before W15 decides whether the spec'd 5-state shape still fits operational reality or wants different states.

Once shipped, the model lands as:

- `hedge_state` column on the `bets` row (mutable; written by auto-classification flow and operator paths)
- `hedge_state_classification` events in `ops_events` table (audit trail of classification path: `operator_explicit` | `auto_resolved_timeout` | `auto_classified_promo_default`)
- Auto-classification flow: at log time for insurance bets (auto → `unhedged_deliberate`); on lay-order completion (auto → `hedged` / `hedge_partial` / `hedge_failed`); on `settled_at + 24h` timeout (auto → `unhedged_deliberate` from unclassified)
- Operator paths: W8 burst-review surface for manual classification; `unhedged_oversight` only ever set by operator retrospectively

Deferred. Spec carried for forward design; shipped surface lands post-W15.

---

### A.7 Cascade chains — what a change in bet settlement state does

(Slice 6 piece 3, reframed Session 124 for the mutable bets row spine)

**Cascade scope: closed list, day-one.**

Only `free_bet_credited` and `promo_cash_credited` events (in `promo_events` per §A.2) are in scope. These are the two event types whose existence is logically derived from a specific bet's outcome. Second-order cascade (FB inventory recompute, deployment orphans) is out of scope — DR-019 read-time recomputation handles inventory naturally; orphaned deployments surface in Burst Review.

**Cascade trigger: bet settlement state change on the `bets` row.**

In the shipped mutable-bets-row spine (§A.2), settlement is not an immutable event that gets superseded — it is a mutable column (`settlement_state`) on the `bets` row written by the W6.5 worker. When a bet's settlement state changes after credits have already been issued (e.g., outcome corrected from `SETTLED_LOST` to `SETTLED_WON`, or `PROVISIONAL` → `SETTLED_WON` via operator W8 resolution), affected credits are superseded by new credit events appended to `promo_events` with extended payload:

- `cascaded_from_bet_id` — the bet whose settlement state changed
- `cascaded_at_settlement_state` — the new settlement state that triggered the cascade
- `cascade_path` — closed enum: `auto | operator_explicit`
- `amount` — recomputed (typically $0 for full invalidation; non-zero for graded cases)

Cascade events use the per-domain supersession pattern from §A.2 — the prior `free_bet_credited` or `promo_cash_credited` event is not deleted; the new event has `supersedes_event_id` pointing at the prior event. Derived state (FB inventory, etc.) reads only the most-recent non-superseded event per DR-019.

**Auto-cascade scope (`cascade_path = auto`):**

Mechanically-clean full-invalidation only. Corrected outcome makes the credit categorically ineligible. Example: insurance bet outcome reverses from "2nd" to "won" → credit invalidated to $0, system writes the supersession.

**Manual cascade scope (`cascade_path = operator_explicit`):**

- Graded/partial cases (each-way leg flips, SGM single-leg flips, margin-graded promos)
- Non-cascade book-side clawbacks (PointsBet emails saying "we've clawed back this FB for [reason]" — `cascaded_from_bet_id = null`)
- Click-and-confirm UI flow; no SQL, no code for operator
- Novel cases route through Claude Chat/Code consultation; resolution recorded as `operator_explicit`

**Pattern automation over time:**

Manual resolutions accumulating evidence of consistent operator handling for a specific shape can be promoted to auto-cascade logic. New `cascade_path` values may emerge (`auto_pattern_X`). Closed-schema-open-vocabulary in action.

**Burst Review cascade events view (day-one):**

Shows every cascaded credit with: original event, triggering settlement (if any), recomputed event, path, net balance impact. Drill-down to full bet→settlement→credit chain. Cascades are rare-but-consequential; surfacing as primary view forces eyeball.

---

### A.8 Cross-DB integration — the boundary

(DR-027, DR-028, DR-026 amendment, DR-029 amendment)

**Two databases, separately owned:**

- **v3's accounting-layer database** (`bethub.db` or successor) owns bet-data: all entities, reference data, and events from Slices 1–6.
- **`capture.db`** (UK VPS racing-data capture, separate infrastructure, separate process) owns race-data: races, runners, finish positions, Betfair time-series snapshots, bookmaker time-series snapshots, BSP historical, batch summaries.
- **No fact owned by both. No row in both DBs. No table written by both systems.**

**Single integration module: `vps_client`.**

All v3 access to `capture.db` flows through one Python module (named `vps_client` in v2; the v3 successor may be named differently but the structural property holds). No raw SQLite reads from capture.db in any other v3 module. No second HTTP client. No bypass. The data API is the contract; `vps_client` is the implementation.

**Read-time, in v3's flow:**

| v3 event/query | Reads from capture.db (via vps_client) |
|---|---|
| `bet_placed` write (live mode) | Latest snapshot for `(bf_market_id, bf_runner_id)`; scratch state at `bet_placed_at` |
| `bet_placed` write (retrospective) | Same, but with `bf_snapshot_aligned_to_placement = false` |
| `bet_leg` write (SGM) | Per-leg snapshot for each leg's `(bf_market_id, bf_selection_id)` |
| `bet_settled` auto-settlement | Race result for `event_id` (finish positions, dead-heat status, scratch list) |
| Burst Review filter by race class | Race classification for each bet's `event_id` |
| Analytical queries (timing, counterfactual, EV calibration) | Full price-and-volume curve for `event_id` from capture.db time-series |

**v3 stores no race-data.** No race classification. No distance. No surface. No finish-position-derived-from-vps. The only field that approaches "stored race-data" is the DR-026 inline snapshot on `bet_placed`, and that is justified explicitly in DR-026 as a single, narrow, cross-system-durability exception. **It is also flagged for Session 15 multi-agent review** (whether even this exception should be removed in favour of full at-read-time resolution).

**Field_size captures (`field_size_at_bet_placement`, `field_size_at_settlement` on `bet_settled`)** are bet-context facts, not race-context facts, per DR-028 forbidden-pattern-2 rationale — they capture the state of the race at specific bet-context moments, not the race's identity. These are also reviewed in Session 15.

**Forbidden patterns (DR-028):**

1. No race-data caching in v3. (Single narrow exception: DR-026 inline snapshot, itself under review.)
2. No race-data denormalisation onto v3 entities.
3. No second integration point.
4. No reflexive extension to additional external data sources.

**Discipline reinforcement (DR-028 four lean structural protections):**

1. Orientation citation at session open — every session.
2. By-number citation when invoked — only when cross-DB topics arise.
3. Mid-session re-read trigger — only when relevant.
4. Log discipline-rot watch — only when DR-028 actively participates.

Plus: high-stakes cross-DB decisions go to multi-agent review per `governance.md`.

**Periodic-only API pattern with analytical bracketing (DR-029):**

- v3 calls `vps_client` on bet log; VPS returns most-recent-stored snapshot from capture.db with timestamp.
- v3 inlines per DR-026 (or, if Session 15 review removes inline storage, reads at analysis time via vps_client).
- **No on-demand fresh-now snapshot pattern is added** unless cadence verification in the DR-029 data review proves insufficient.
- Analytical queries can read both T-x and T-x+cadence snapshots from capture.db at analysis time, observing market movement *across* the bet timestamp. This bracketing is structurally stronger than a single fresh on-demand snapshot.

---

### A.9 Derivation rules — what's stored vs. what's computed

**Stored (source of truth):**

- All entity reference data (account, book, account_at_book, promo_template, promo, account_arrangement, account_holders, payees, warning_catalogue)
- All bet records (`bets` row + `bet_legs` rows per DR-032; mutable bet-lifecycle columns per §A.3)
- All events in the three per-domain event log tables (`cash_flow_events`, `promo_events`, `ops_events` per §A.2)
- v3 stores **no aggregates, no balances, no computed states** beyond the materialised-view-on-entity-row pattern for bet lifecycle state (DR-019 Session 124 amendment).

**Computed on read (per DR-019):**

| Display surface or query | Computed from |
|---|---|
| At-book balance per (account × book) — Location 1 | `cash_flow_events` (incl. `account_at_book_balance_adjustment`) + `bets.cash_stake_amount` + per-bet computed `cash_returned` (per §A.6) + finalised `promo_cash_credited` events from `promo_events` |
| FB inventory (face value) | `promo_events`: `free_bet_credited` finalised − `free_bet_deployed` amounts − `free_bet_revoked` − `free_bet_expired` |
| FB realised cash value (~70% of face) | FB inventory × operator-tuned conversion rate, OR derived from historical conversion data per book |
| Cash holding per custodian — Location 2 | Per §A.5 formula against `cash_flow_events` (incl. `account_holder_balance_adjustment`) |
| Cash age per custodian | FIFO walk of `account_holder_funding` events (and day-0-opening balance adjustments treated as initial deposits) vs draw-downs |
| Operation net flow (informational view, not a balance) | Per §A.5 formula; sum over four bank-touching event types from `cash_flow_events` since day 0 |
| Weekly turnover per account | Sum `bets.cash_stake_amount + bets.free_bet_stake_amount` where `bet_placed_at` in window |
| Cash returned per bet (settlement payout) | Computed from `bets.cash_stake_amount × matched_price × dead_heat_count / removed_runner_count handling` against `bets.settlement_state` (see §A.6) |
| Hedge state per bet | Once shipped (post-W15), reads `bets.hedge_state` directly; spec per §A.6 |
| Promo journey per (template × book × account_at_book) | Sequence of `promo_observed` events from `promo_events`; shrink detected by terms diff |
| Active warnings per account_at_book | `accountcare_warning_raised − accountcare_warning_cleared` from `promo_events`, walking supersession |
| Outcome-vs-warning analysis | Join `bets.active_warnings_at_log` against `bets.settlement_state` and computed `cash_returned` |
| Hygiene status per account | account_at_book.tier/phase + bookmaker rules + week-to-date turnover (computed) + last-bet date (computed) + cluster state |
| Reconciliation gap per book | Operator-reported book balance vs computed at-book balance |

**Cross-DB reads (computed from `vps_client`):**

| Query | Calls `vps_client` for |
|---|---|
| Race classification on a bet | `vps_client.get_race_metadata(betfair_market_id)` |
| Finish position on a bet | `vps_client.get_race_result(betfair_market_id)` (per §A.6 — never stored on bets row) |
| Field size on a bet (verification) | Cross-check against capture.db scratching events |
| Auto-settlement (W6.5 worker) | `vps_client.get_race_result(betfair_market_id)` |
| Counterfactual hedge return | `vps_client.get_market_curve(betfair_market_id, betfair_selection_id, from_ts, to_ts)` |
| Pre-jump movement before bet | `vps_client.get_market_curve(...)` bracketing `snapshot_timestamp` |
| Deeper market context for a bet (depth, time-series) | `vps_client` cross-reference by `betfair_market_id` + `bet_placed_at` per DR-026 Session 124 amendment |

**Performance note (DR-019):** SQLite handles full event-log replay queries trivially at v3's scale (single user, ~tens of thousands of bets per year). No pre-computation needed for performance. If a specific query becomes slow, in-memory caching at the read layer with explicit invalidation is an optimisation; default is always "compute fresh from events plus current bet records."

**Reconciliation as a first-class surface — six surfaces.**

Reconciliation is what the system is named for. The contract above produces reconciliation as the natural output of derived state vs. operator-observed reality. **Six reconciliation surfaces** day-one. **Operation-net-flow is a derived informational view, not a reconciliation surface** — Tim's bank is not in the model and there is no apples-to-apples external check.

- **Cash reconciliation:** computed at-book balance (Location 1) vs operator-entered actual book balance. Gap surfaced in Burst Review or dedicated reconciliation report.
- **FB reconciliation:** computed FB inventory vs operator-counted FB credits visible at book. Gap surfaces missing credit, missing deployment, or status discrepancy.
- **Settlement reconciliation:** v3 auto-settled bets vs operator's observation that the book paid X. Divergences are reconciliation signals (DR-029 model — not algorithmic resolution).
- **Race-result reconciliation:** capture.db race result vs book settlement. Divergences (voids per book rules, dead-heat differences, stewards' inquiry resolutions) are reconciliation signals, not algorithmic resolution.
- **Hedge reconciliation:** hedge state per A.6 vs operator's mental model of which bets are hedged.
- **Cash-holding-with-custodian reconciliation:** computed cash holding per custodian (Location 2) vs custodian's actual bank balance dedicated to operation. Cash age signals stale working capital.

Each reconciliation surface lives in its own view in v3. Each is a natural output of derived-state-on-read against an external check.

---

### A.10 Canonical source identifiers — Betfair as the reference layer

**The principle.** Betfair is the canonical source for anything Betfair owns. This applies in two directions.

For event-domain facts where Betfair is the authority — event identity, market identity, selection identity, venue, sport, commission rate at the bet's point in time — Betfair's record is the truth that v3 references. v3 does not store its own copy; it carries the Betfair-side identifier and, where a logging-time snapshot is justified, captures denormalised display fields as immutable historical facts (per DR-026's at-log-time market snapshot pattern).

For bet records — every bet logged in v3, whether placed on Betfair directly or on a soft book — Betfair's identifier scheme is the canonical join key. Every bet record carries `betfair_market_id` plus `betfair_selection_id` (for single-selection bets) or an array of `(betfair_market_id, betfair_selection_id)` pairs (for SGMs and other multi-leg bets). These identifiers are the join key into Betfair-sourced analytical data — price history, BSP, settlement events, traded volume — and into operational reads via `betfair_client`. Fuzzy-matching between bet records and the analytical layer is eliminated by construction.

**The rule for soft-book bets.** Soft-book bets (logged manually into v3 from the racing or sports screen) carry Betfair-side identifiers because the entry path inherits them. Both screens are Betfair-driven — the racing-screen runner row and the sports-screen selection row are both Betfair `(market_id, selection_id)`-keyed. Clicking "log soft-book bet" on a row passes the identifiers into the bet-log modal; the operator types account, book-at-account, and confirm. No resolution logic, no fuzzy-match at logging time. **Hard rule:** soft-book bets must have a Betfair market available at logging time. There is no fallback path for races or markets where Betfair has no coverage.

**The rule for Racing API context.** The Racing API is analytical-line only, not operational. Bet records carry only Betfair identifiers, never Racing API identifiers. When v3 needs Racing-API-sourced context for a bet (form, trainer history, track condition for thoroughbred bets), the join goes through `capture.db`'s internal Racing-API ↔ Betfair resolution layer — bet record (Betfair `market_id`) → resolution table → Racing API record. The fuzzy match between Racing API and Betfair is owned by capture.db's analytical layer, addressed code-driven and post-hoc, not at logging time. Racing API covers thoroughbreds only; harness and greyhound bets join only to Betfair-sourced analytics.

**Cross-DB boundary.** This canonical-source pattern sits cleanly under DR-027 (the two-database architecture) and DR-028 (the cross-DB integration boundary discipline). The Betfair-side denormalised display fields on bet records are immutable logging-time snapshots (historical fact, not refreshable cache); they do not breach DR-028's no-caching rule. The same Betfair identifier scheme keys both the operational and analytical lines, so no second integration point is introduced.

**The locked schema commitment** for bet records implementing this pattern is captured in DR-032. §A.10 names the architectural principle; DR-032 specifies the bet-record / bet-leg shape, ownership of fields between bet record and legs (stake and combined price live on the bet record only — never on legs), and the operator entry paths.

**Cross-references:** DR-032 (bet record canonical-source schema), DR-026 (at-log-time market snapshot pattern), DR-027 (two-database architecture), DR-028 (integration boundary discipline), DR-022 (account / book / account-at-book vocabulary).

**Note on legacy citations.** Earlier project documents and session records cite this section as `§D12`. The naming convention was a misalignment — `architecture.md` uses §A and §B as top-level section anchors, with no §D series. The principle's canonical home is §A.10 (this section). Legacy `§D12` references resolve to this content and will be updated at the next documentation sweep.

---

## Operational layer — Betfair direct

The operational layer is v3's path to live Betfair pricing for in-the-moment decision-making — distinct from the analytical-line reads that v3 performs against `capture.db` via `vps_client`. The operational layer connects v3 directly to the Betfair API via a dedicated module (`betfair_client`), without routing through `capture.db` or the VPS analytical pipeline.

This layer is the home for two surfaces: racing operational reads (live exchange pricing in the burst window before jump, post-jump in-running, and at bet entry — specified in detail in DR-029 §2.4) and sports operational reads (the entire sports surface — specified in §B.1 below). The two surfaces share the same `betfair_client` module and the same architectural shape; only the cadence pattern and the specific consumer surfaces differ.

### B.0 What this layer is, and what it isn't

**This layer is** v3's read path to Betfair for operational consumers. It sits parallel to `vps_client` in the consumer-facing v3 architecture: where `vps_client` reads the analytical surface (capture.db's polled-snapshot store), `betfair_client` reads Betfair direct for what's-happening-right-now.

**This layer is not** an analytical store. It writes nothing to disk. It does not snapshot, archive, or carry retention. Each call returns Betfair's current view of the world; v3 either uses that view to render a screen or to populate the at-placement operational snapshot on a new bet record. Once the call returns, v3 holds the response only as long as the UI surface or write operation needs it.

**This layer reconciles with the analytical line by construction modulo cadence lag.** Both `betfair_client` and the capture.db ingestion path source from the same Betfair API at different cadences. For Betfair-sourced data, the two surfaces are consistent up to the lag introduced by capture.db's polling cadence. The Racing API ↔ Betfair merging that capture.db performs internally is not visible to `betfair_client`.

**Cross-DB boundary discipline (DR-027 / DR-028) does not extend to this layer.** The two-database boundary is between v3's bet-data SQLite and capture.db. `betfair_client` sits on neither side of that boundary — it talks directly to a third party. The integration-discipline principles still apply (single integration point per source, no caching, no denormalisation across the boundary) but the cross-DB-by-reference-only rule is specifically about capture.db and does not constrain operational-layer design.

### B.1 Sports operational layer

v3's sports surface — fixture lists, market structure, live pricing, bet entry, auto-settlement — runs entirely against `betfair_client`. Sports has no analytical-line companion: there is no sports-specific capture.db schema, no sports scrapers, no sports time-series snapshots. The asymmetry between racing (analytical store + operational direct) and sports (operational direct only) is a deliberate architectural choice locked Session 27 and per DR-029 principle 1.3.

#### B.1.1 Sports page sources

When the operator opens v3's sports page, `betfair_client` makes calls to the Betfair API to populate the visible surface. The page is filtered by a pre-defined sports-and-leagues list (per `v3_data_requirements.md` §4): AFL, NRL, NBA, NBL, EPL, La Liga, Ligue 1, Serie A, MLS, International Cricket, Tennis majors, NHL, MLB, NFL, MMA. v3 surfaces fixtures from those leagues only — Betfair fixtures outside the day-one sports scope are not shown.

For each league the page shows the *core market types* relevant to that sport family:

- **AFL, NRL, NFL, NHL, MLB, NBA, NBL, MMA, Tennis (and similarly-shaped sports added later):** Match (head-to-head, two-way), Line (handicap), Total (over/under).
- **Soccer (EPL, La Liga, Ligue 1, Serie A, MLS):** Match (win / draw / win, three-way), Line (handicap), Total (over/under).
- **Cricket:** Match (two-way for limited-overs; tests handled separately or excluded day-one), Line (handicap), Total (over/under) where Betfair offers them.

The market-type set is intentionally narrow at day-one. SGM markets and individual / specialist markets (anytime tryscorer, first goalkicker, total disposals, individual run lines, etc.) are out-of-scope for v3 day-one but **architecturally provided for** — see B.1.6.

**Read pattern.** Each page render calls `betfair_client.list_events(sport, league)` to populate the fixture list, then `betfair_client.list_markets(event_id)` for any expanded fixture, then `betfair_client.get_market_book(market_id)` for live prices on visible markets. The pattern is read-on-demand — no background polling, no refresh loop until the page surfaces an explicit refresh moment (operator action, timed re-fetch in burst contexts, Streaming feed when §2.4 lands).

**Staleness and unavailability signalling.** If a `betfair_client` call fails or times out, the affected surface shows an explicit unavailability state ("Betfair unavailable — retry") rather than presenting stale data as current. Partial unavailability is allowed: if `list_events` succeeds but `get_market_book` fails for a specific market, the fixture lists render with that market shown as unpriced rather than the page failing entirely. Staleness signalling for streaming-vs-polled data is a §2.4 concern; at v3 day-one the simplest pattern (timestamp on each render, refresh-on-action) is sufficient.

#### B.1.2 Bet entry and the line ladder

Bet entry on Match markets is direct: operator picks a fixture, picks a market type (Match), picks a selection from the two (or three for soccer) priced rows shown, picks an action.

Bet entry on Line and Total markets uses the **line ladder** pattern:

1. Operator picks fixture and selects the Line or Total market-type tab.
2. Operator types a line value into the Line/Total input (e.g., `6.5` for handicap, `165.5` for total). Sign is unsigned in the input — for handicap, the favourite-side is inferred from the head-to-head market (see B.1.3).
3. v3 fetches Betfair's line-variant markets for the fixture and renders an **11-line ladder** centred on the operator's typed value. Five lines above and five below the centre. Each row shows back/lay prices and best-back size (liquidity) for both sides of the bet (Carlton-side / Collingwood-side for handicap; over / under for total).
4. Lines where Betfair has no live market render with "no market" placeholder rows so the operator gets immediate visual feedback on the boundary of available offerings.
5. Each priced row carries two trailing action icons:
    - **⚡ HedgeModal** — opens v3's hedging modal context (per v2 pattern), with the Betfair `market_id` plus selection plus current prices pre-populated. Operator works the modal as in v2.
    - **📝 LogBet** — opens v3's lighter bet-logging form for bets already placed at the soft book. Same Betfair `market_id` + selection + at-confirm operational snapshot pre-populated; operator enters stake and confirms.
6. Both action paths inherit the resolved Betfair `market_id` plus the operator-typed line value plus the operational snapshot from the ladder row context. No re-asking for line, no re-fetching prices.

The ladder pattern is sport-agnostic — the same ladder shape applies to AFL Line, NRL Line, NBA Total, soccer Line (Asian handicap variants), and any future sport whose Betfair markets follow the same line-variant structure. Cricket totals work identically.

**Failure mode.** If no Betfair market exists at the operator's typed line, the centred row renders as "no market" and the surrounding rows still populate where Betfair has variants. If no Betfair markets exist within ±5 of the typed line at all (essentially: typed line is far outside Betfair's current offering range), the ladder shows an empty-state with a "show all available lines" escape hatch. v3 does not silently write a bet record without a matching `market_id`.

**Auto-line-matching is a v3.1+ candidate, not v3 day-one.** A future improvement would auto-detect the right Betfair line by matching against the soft-book's listed line (since soft books and Betfair sit close around the consensus line). This depends on soft-book operational data being reliably available — itself a §2.5-locked source-flexible capability with manual entry day-one. Auto-line-matching lands in v3.1+ once §2.5's source path is materialised. Naming the dependency explicitly: auto-line-matching cannot ship before §2.5's source implementation lands.

#### B.1.3 Favourite inference for handicap markets

Line markets are signed by which side carries the minus handicap. The operator's typed line value is unsigned — typing `6.5` means "a 6.5-point handicap on this fixture." v3 derives the sign from the **head-to-head market** for the same fixture: the side with the shorter head-to-head price is the favourite and carries the minus handicap.

**Tolerance rule.** Shorter-priced side in the head-to-head market is the favourite, full stop. For the rare "pick'em" case where both sides price near-flat (e.g., both ~$1.95) and the line market exists at zero or near-zero, the ladder renders with both sides shown unsigned and the operator picks based on the row label rather than the inferred minus-side.

**Edge case: head-to-head temporarily unavailable.** If `betfair_client.get_market_book(head_to_head_market_id)` fails at the moment of ladder render, the ladder still renders but rows show selection labels neutrally ("Side A / Side B") rather than committing to favourite-inference. Operator picks by label. v3 logs the bet against the Betfair `market_id` it resolves at confirmation time, by which point head-to-head is typically reachable again.

#### B.1.4 Sports auto-settlement

Auto-settlement reads from `betfair_client` for each unsettled sports bet at scheduled-fixture-end-time-plus-margin. The fallback path uses public archives (AFLTables for AFL, equivalent sources for NRL and other sports) for cases where Betfair's settlement is delayed or incomplete.

**Decision logic:**

- Betfair returns market status `SETTLED` with a clear winning selection that matches the bet's selection → `settlement_state = SETTLED_WON`.
- Betfair returns market status `SETTLED` with a clear winning selection that does NOT match the bet's selection → `settlement_state = SETTLED_LOST`.
- Betfair returns market status `CANCELLED` or void-equivalent → `settlement_state = VOIDED` with refund discipline per the bet's terms.
- Betfair still `OPEN` or `SUSPENDED` more than **90 minutes** after scheduled fixture end → trigger public-archive fallback.
- Public-archive fallback resolves cleanly → `settlement_state = PROVISIONAL` (because the result came from a non-canonical source for v3's purposes), surface to Burst Review for operator confirmation.
- Both Betfair and public-archive resolve but disagree on the result → `settlement_state = PROVISIONAL`, surface to Burst Review.
- Neither Betfair nor public-archive resolves cleanly → `settlement_state = PROVISIONAL`, surface to Burst Review.

The 90-minute threshold is a starting value, intended to comfortably exceed full-time plus Betfair's typical settlement lag for AFL-shape fixtures. It can be tuned per-sport if a sport's settlement timing patterns warrant it (e.g., Tennis matches with multiple-set go-the-distance variability may need a longer threshold; NBA quarters running to schedule may allow shorter).

The `SETTLED_WON` / `SETTLED_LOST` / `VOIDED` / `PROVISIONAL` settlement discipline matches the racing settlement model specified in DR-029 §2.6 and the spine locked in §A.2 / §A.6. The architectural symmetry is intentional: regardless of canonical source (capture.db for racing, Betfair-direct for sports), the same enum vocabulary plus Burst-Review-confirmation pattern applies.

#### B.1.5 Sports bet record shape

Sports bet records store at placement time:

- **Betfair identifiers**: `betfair_event_id`, `betfair_market_id`, `betfair_selection_id`. Identifies the bet's canonical source unambiguously.
- **Operator-specified line value** (handicap and total markets only): the unsigned line the operator typed (e.g., `6.5`, `165.5`). Stored as a denormalised field for operator-readable display, separate from the Betfair `market_id` which already encodes the line implicitly.
- **At-placement operational snapshot**: price taken, best-back price, best-lay price, total matched (if available from Betfair at confirm time), snapshot timestamp from `betfair_client`. This is the bet's at-placement market-context fact, immutable on the record per DR-026.

**What's not stored on the bet record:** team or fixture metadata (resolved at read time via `betfair_client` from the stored identifiers), market-type metadata (encoded in `betfair_market_id`), per-bet `cash_returned` payout (computed on read per §A.6 — no `cash_returned` column on bets), result detail for analytical context (e.g., margin / first-goalscorer for sports — read via `betfair_client` at analysis time). Settlement state itself IS stored on the bets row (`settlement_state` column per §A.3 / §A.6, written by the auto-settlement path). These at-analysis-time facts are derivable from the stored facts plus current Betfair state, per the derivation discipline in §A.9.

**Betfair-unavailable-at-log-time fallback.** If `betfair_client` is unreachable at log time, the operator can still log the bet through a placeholder path: bet record is created with operator-typed line, stake, and soft-book details intact; Betfair `market_id` and at-placement operational snapshot fields are flagged `betfair_unresolved = true` and left blank. When Betfair reachability returns, a reconciliation step resolves the `market_id` from the stored fixture + market-type + line + selection metadata and backfills the operational snapshot from current Betfair state (with explicit `snapshot_resolved_late = true` flag so the bet record carries its provenance honestly). This is operationally smoother than blocking bet entry on Betfair reachability — and the failure mode has not been observed in v2 history, so the path exists as insurance not as a routine flow.

**Sports bet records are joined to the rest of the v3 data model at the bet-record level**, the same way racing bet records are. The `bets` table + `bet_legs` table (per §A.2) carry sports bets in the same shape as racing bets; the difference is the source of canonical truth for the bet-lifecycle data (Betfair-direct via `betfair_client` for sports auto-settlement; VPS-via-`vps_client` for racing finish-position context). Settlement transitions write to the same mutable `settlement_state` column regardless of source.

#### B.1.6 Same-game-multi (SGM) and specialist markets — architectural provision

SGM markets and individual/specialist markets are explicitly **out-of-scope for v3 day-one** but the architecture must not preclude their later addition. SGM requires:

- An expanded Betfair market vocabulary (anytime tryscorer, first goalkicker, total disposals, individual run lines, batting-partnership totals, etc.) — adds market types to the per-sport core-market list in B.1.1.
- Multi-leg bet records — a single SGM bet covers ≥3 legs at correlated odds; the bet record shape needs to accommodate multiple `betfair_selection_id` values (and possibly multiple `betfair_market_id` values, depending on whether SGM is implemented as a Betfair-side combined market or as separate-leg recording).
- Correlation modelling on the analytical side for EV calculation — this is sports analytical work, not currently in scope; lands as a separate sports-analytics arc when SGM goes live.

**Architectural provisions made now to keep SGM additive later:**

- The market-type tab strip in B.1.1 is extensible. Adding tabs for SGM, Individual, Specialist is a UI addition with no structural change.
- The bet record shape in B.1.5 stores `betfair_market_id` as a single field today but is designed to extend cleanly to a list-of-`market_id` if SGM lands as separate-leg recording. The single-field-vs-list shape is a v3.1+ implementation choice depending on Betfair's SGM API surface — the v3 day-one shape doesn't lock it.
- The line-ladder pattern (B.1.2) doesn't apply to SGM directly — SGM is multi-leg with discrete selections per leg rather than line-variant markets — but the same write-time-input philosophy applies: operator picks legs explicitly, v3 records the resolved Betfair `market_id`(s) without architectural inference.

SGM-specific concerns — three-leg-minimum constraints, correlation EV modelling, specialist-market discovery — are explicitly named as v3.1+ scope dependent on the sports analytical needs settling.

#### B.1.7 Cadence note (open, tracked)

v3's racing operational layer (DR-029 §2.4 — Betfair Streaming spec) and sports operational layer (this section) share the `betfair_client` module. v2 currently uses Betfair-direct polling for racing operational reads at a cadence that has worked well in practice. Whether that polling cadence is still appropriate for v3 — and whether v3 should move racing operational reads onto Betfair Streaming for sub-second updates near jump — is a §2.4 concern.

For sports, the polling-vs-streaming question matters less because sports markets move on a slower timescale than racing in-running. v3 day-one runs sports operational reads on the same polling pattern v2 uses for racing today; if §2.4 lands a Streaming connection that also serves sports, sports reads upgrade naturally without architectural change.

The specific cadence-appropriateness verification is gated on the Saturday API observation probe (per WIP §17), which surfaces what Betfair actually returns at what cadence on AU racing markets near jump. The probe's findings feed §2.4's design directly and inform whether sports operational reads need any cadence-specific tuning.

### B.2 Soft-book operational layer — deferred (Session 69)

**Architectural position.** v3 day-one has **no operational soft-book layer**. Soft-book bets enter v3 by typed-price entry only: the operator types the price they took at the soft book at bet-log time, and v3 stores it on the bet record. There is no `softbook_client` module, no live soft-book read anywhere in v3, no soft-book operational pricing displayed in the burst window or anywhere else.

This supersedes the original DR-029 §2.5 framing ("interface contract specified, source deferred"). The operational soft-book layer itself is deferred to a future DR — see DR-029 §3.11 for the formal deferral and rationale. In short: soft-book operational live pricing is several distinct consumer surfaces (best-promo-odds for racing insurance, multi-book scan for price boosters, SGM-correlated views, etc.), each tied to an operator strategy and bet type whose shape is still being discovered in operations. Specifying an interface contract before the consumer surfaces are known would mean guessing at structure — not a v3 day-one commitment.

**Soft-book bet records.** Soft-book bets carry the typed price plus the soft-book identity (which bookmaker), plus Betfair-side identifiers as the canonical join key per architecture.md §D12 (Betfair-as-canonical-source) and the Session 42 architectural extension. The Betfair-side identifiers are populated at bet-log time by a `betfair_client` lookup of the corresponding race/runner (racing) or fixture/market/selection (sports). The operational snapshot stored on the bet record is a Betfair-side snapshot, not a soft-book-side snapshot — there is no soft-book-side operational data flowing in v3 day-one.

The detailed bet-record shape (which fields, which optional, how reconciliation against Betfair-side fields handles edge cases) is specified in DR-029 §2.8 (bet-schema reframing) when that stream lands. §2.9 (write-side coherence) covers the bet-entry surface for soft-book bets — what the operator types, what v3 writes, what's flagged for Burst Review.

**Cross-DB boundary discipline.** Soft-book bets do not introduce a new integration surface. The Betfair-side lookup path runs through `betfair_client` (already specified) for the at-placement market-context snapshot; the analytical-side resolution at read time runs through `vps_client` (already specified) for race/fixture context. The DR-027 / DR-028 cross-DB discipline applies unchanged.

**When the operational soft-book layer returns to scope.** A future DR is expected when: (a) Strategy 2 (Price Booster) volume reaches a level where multi-book scan is operationally useful rather than aspirational; or (b) Strategy 3 (Correlated Friction) begins running and surfaces concrete same-game-multi pricing surface requirements; or (c) Strategy 4 (Synthetic Each-Way) execution begins and surfaces concrete value-betting price-comparison requirements; or (d) operator surfaces a different concrete requirement from running operations.

The future DR will likely re-introduce a `softbook_client` module shape with a specific consumer surface in mind (rather than the speculative source-flexible interface that the original §2.5 proposed). BetWatch parallel-track vendor research carries forward as discovery activity informing that future DR — no longer gating any DR-029 deliverable.

---


## Operator workflows

The Reconciliation contract (§A) and Operational layer (§B) describe how data flows and where it lives. The operator-facing workflows that read this data and surface decisions to the operator live here. Day-one v3 ships W8 Burst Review (§C.1); other workflows (after-burst cleanup, session reconciliation reports, AccountCare action queue, Promo Planner) land in subsequent workstreams.

### C.1 Burst Review — operator surface for provisional bet resolution

(W8 shipped surface, captured Session 124 per Finding #16 from S123 pre-W14 review)

**Purpose.** Burst Review is the operator surface for resolving bets that the W6 / W6.5 auto-settlement chain could not resolve cleanly. When `settlement_state` lands at `PROVISIONAL` (see §A.6), the bet routes to Burst Review for operator confirmation.

**Endpoint pair (W8 shipped surface):**

- **GET `/burst_review/provisional`** — returns a `ProvisionalSettlementSurfacingPayload` listing every bet currently in `settlement_state = PROVISIONAL`. Per-bet detail in the payload covers:
  - Bet identity (`bet_id`, `account_at_book_id`, `bet_placed_at`, `strategy_tag`)
  - Bet legs (per-leg Betfair identifiers, Set B display fields)
  - Current `match_status` and `settlement_state`
  - `last_read_market_state` (the Betfair market state the worker last read)
  - `unexpected_state_count` if non-zero (flag for ops debugging)
  - `dead_heat_count`, `removed_runner_count` if non-zero (drives operator's payout-calculation context)
  - VPS race result for the bet's Betfair market (read via `vps_client` at request time per §A.6)
  - Operator-typed soft-book price and stake context

- **POST `/burst_review/provisional/{bet_id}/resolve`** — the `apply_manual_operator_resolution` flow. Operator supplies:
  - Target `settlement_state` (`SETTLED_WON` | `SETTLED_LOST` | `VOIDED`)
  - Optional `operator_reason` (free text)
  - Optional `dead_heat_count` / `removed_runner_count` overrides if the operator needs to correct what the worker captured

  The handler writes the new `settlement_state` to the `bets` row (mutable per §A.2), writes an `ops_events` row with `event_type='manual_operator_resolution'` carrying old-state / new-state / operator-reason / timestamp, and triggers cascade rules per §A.7 (any `free_bet_credited` / `promo_cash_credited` events whose existence depends on this bet's outcome are recomputed and superseded in `promo_events`).

**Position in v3 repo layout (per DR-030):**

- Endpoint handlers: `workflows/burst_review/`
- Domain logic for cascade recomputation: `domain/bets/` plus settlement logic in `workflows/bet_entry/v1/` per DR-030 Session 124 amendment
- Store-layer writes: `store/repositories/` (bet record mutation + `ops_events` write + cascade event writes)

**What Burst Review does not handle (out of scope day-one):**

- Bet record edits via DR-017 fully-editable model (separate UI flow — operator clicks a bet row in normal bet history view and edits a field; writes `bet_correction` event to `ops_events` per §A.2).
- Hedge state classification (deferred per §A.6 — hedge classification surface lands post-W15 alongside DR-025 ship).
- Cash reconciliation and FB reconciliation surfaces (separate reconciliation reports per §A.9 — independent of Burst Review).
- Promo journey annotation (separate operator surface — writes `promo_journey_annotation` events to `promo_events`).

Burst Review's day-one scope is intentionally narrow: resolve provisional settlements to terminal states, trigger cascades, write audit trail. Adjacent operator surfaces ship in subsequent workstreams.
