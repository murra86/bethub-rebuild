# Session 10 — active log

**Session opened:** 2026-04-27 19:32 ACST

## Scope (planned, in order)

1. Slice 6 piece 2 — hedge state derivation logic (computed on read against `lay_order_finalised` chain) plus `hedge_state_classification` event for operator-explicit and auto-resolved unhedged classifications. DR-025's six states drive the derivation.
2. Slice 6 piece 3 — cascade rule for `bet_settled` supersession. Resolve open items f, g, h from Session 9 close.
3. Reconciliation contract write-up across Slices 2–6.
4. Build strategy decision (strangler-fig vs clean break + slice strategy resolved together).
5. `diagrams/v3_target.svg`.

If context tightens: split before the diagram first, then before build strategy.

## Open items carried in (Claude leans, operator call)

- **(f)** One `hedge_state_classification` event per bet with `classification_path` enum (`operator_explicit` | `auto_resolved`). Lean: yes on both — clean queryable record of every classification including auto-path ones, matches DR-025's "operations log captures the path to terminal state" intent.
- **(g)** Cascade scope only `free_bet_credited` and `promo_cash_credited`. Lean: yes — these are the only event types whose existence is logically derived from a specific bet's outcome.
- **(h)** Burst Review "cascade events" view day-one. Lean: yes — cascades are rare-but-consequential, missing them risks unnoticed balance corrections.

## Framing note

Workflow-first framing carries forward (reinforced by Sessions 6, 7, 8, 9 success — seven consecutive early-close sessions). Software questions are Claude's; ask only about betting/operational matters. Honour DR-021, DR-007, DR-022, DR-024. Use Desktop Commander for all rebuild folder file operations (bash sandbox can't reach it).

## Entries

### 2026-04-27 19:32 ACST — Session opened

Anchored on system clock per DR-021. Read `work_in_progress.md` in full, `sessions/SESSION_09.md` in full, `decisions.md` DR-001 through DR-026 in full. Confirmed framing, Slice 5 closed-state, Slice 6 piece 1 (`bet_settled`) locked, three architectural-load-bearing DRs for this session (DR-016, DR-019, DR-025) plus DR-023, DR-026 confirmed. About to open Slice 6 piece 2 — hedge state derivation.

### 2026-04-27 19:54 ACST — Slice 6 piece 2 locked

Hedge state derivation algorithm locked: read-time, given bet_id, walk lay_order_finalised chain first (returns hedged | hedge_partial | hedge_failed), then hedge_state_classification (returns operator-set or auto-set unhedged state), else unhedged_unclassified. hedge_failed confirmed terminal-from-lay-chain, never reclassifiable. Pre-settlement operator classification permitted. `hedge_state_classification` event payload locked: parent_event_id, target_state (closed enum: unhedged_deliberate | unhedged_oversight), classification_path (closed enum: operator_explicit | auto_resolved_timeout | auto_classified_promo_default), oversight_reason (closed enum, extensible: operator_distraction | tool_failure | external_disruption | other — required when oversight target, null otherwise), note (optional, required when oversight_reason=other), recorded_at, occurred_at, supersession fields. Three event-writing paths: operator-explicit from Burst Review (with pre-settlement permission), auto-classified at log time for insurance bets only (insurance is structurally-let-ride; empirical EV-vs-commission validation deferred to v4 analytics against DR-020/DR-026 captured data), auto-resolved timeout via sweeper at settled_at + configurable window (default 24h per DR-025). 24h timer configurable. Closed-schema-open-vocabulary pattern instance count now six. About to open Slice 6 piece 3 — cascade rule for `bet_settled` supersession.

### 2026-04-27 20:14 ACST — Slice 6 piece 3 locked (pending Q6 field name)

Terminology check confirmed `placed` (bet_settled outcome enum value, finishing-position) and `triggered` (verb describing promo eligibility evaluation, not a schema noun) are clean and not conflated in the locked schema. Cascade scope (item g): closed list — only `free_bet_credited` and `promo_cash_credited`, day one. Second-order cascade out of scope (DR-019 handles via read-time recomputation; orphan deployments surface in Burst Review). Cascade mechanism (item f): supersession pattern. Superseding credit event payload: parent_event_id, cascaded_from_bet_settled_event_id (null for non-cascade clawbacks), cascade_path (closed enum: auto | operator_explicit), amount (recomputed; typically $0 for full invalidation, non-zero for operator-graded), note, standard supersession fields. Auto-cascade scope narrowed to mechanically-clean full-invalidation case only (corrected outcome categorically ineligible). Graded/partial cases and book-side clawbacks unrelated to outcome reversal handled via operator_explicit path through UI affordance (click-confirm-note, no SQL/code for operator). Operator-explicit execution clarified — execution-layer build will surface a UI affordance writing the supersession event behind the scenes. Burst Review cascade events view (item h): day-one. Shows original event, triggering settlement, recomputed event, path, net impact, drill-down. Closed-schema-open-vocabulary pattern instance count now seven. Q6 outstanding: keep `triggering_bet_event_id` field name on credit events, or rename. About to move to reconciliation contract write-up across Slices 2–6.

### 2026-04-27 20:30 ACST — Q7 locked; Slice 6 piece 1 amendment

`finish_position` (integer, nullable) added to `bet_settled` payload. Required for racing bets (thoroughbred/harness/greyhound); null for sports/SGM. Sourced from result_source at settlement time. Resolves the outcome-vs-physical-finish terminology concern cleanly: `outcome` carries cash-result (won/placed/lost/etc — what happened to the bet's money); `finish_position` carries physical-race fact (where the horse came); promo eligibility evaluation reads finish_position for racing-position-dependent promos (insurance "money back if 2nd" reads finish_position = 2, not outcome = placed). Operator's intuition that this opens analytical doors confirmed — runner-finish-position-by-promo-type is the kind of analysis schema captures naturally once the field exists. Late-scratch and dead-heat handled naturally (null for scratched-voided; same finish_position for dead-heat tied positions). SGM null day-one; per-leg outcomes carry relevant info via sgm_leg_outcomes JSON. Slice 6 piece 1 amendment captured for lift-to-architecture.md propagation. Q6 still outstanding pending operator call. About to either close Q6 and move to reconciliation contract write-up, or close Q6 and move on.

### 2026-04-27 20:42 ACST — Q6 locked; Q8 surfaced

Q6 locked: `triggering_bet_event_id` confirmed as field name on `free_bet_credited` and `promo_cash_credited` events (no rename). Q8 surfaced (operator-prompted): field size capture on `bet_settled`. Same DR-026 cheap-to-capture-expensive-to-reconstruct logic as `finish_position`. Each-way EV evaluation depends on field size structurally (book terms vary by field size). Insurance-promo conversion analysis by field size is high-analytical-value. Two candidate fields: `field_size_at_settlement` (actual starters, excludes late scratches) and `field_size_at_bet_placement` (field at log time). Lean is capture both. Race-level metadata (class, distance, surface) flagged for verification during Slice 1 review at reconciliation contract write-up — likely lives on race reference record, not bet_settled. About to lock Q8 and close Slice 6.

### 2026-04-27 20:55 ACST — Q8 locked; race classification provisionally placed on race reference; Slice 6 closing

Q8 locked: both `field_size_at_settlement` (actual starters, excludes late scratches) and `field_size_at_bet_placement` (field at log time) added to `bet_settled` payload. Both integer, nullable, racing-only, sourced automatically. Operator example use case: high-odds-runner finish-pattern analysis by field size, materially relevant to profitability. Race classification fields (`race_class`, `race_distance`, `race_surface`) provisionally placed on race reference record (Option B) per DR-019 reference-data principle and to avoid per-bet denormalisation. Verification deferred to Slice 1 review during reconciliation contract write-up — if Slice 1 race reference is missing any of these, surface as Slice 1 amendment. `bet_settled` does NOT duplicate race classification. Racing API likely source given operator notes its richness. Q9 surfaced as soft choice: verify-during-reconciliation-review (lean) vs verify-now-before-moving-on. About to take operator call on Q9 and close Slice 6 fully.

### 2026-04-27 21:03 ACST — Q9 resolved (soft path); Slice 6 fully closed; session closing

Q9 resolved on soft path — race classification placement verification deferred to Slice 1 review during reconciliation contract write-up in Session 11. Operator confirmed Option B for race classification with sharp additional argument: capturing race data on the race table for ALL observed races (not just bet-on races) unlocks pilot/hypothetical-bet analysis where bet criteria can be modelled across the full universe of races. Australian + NZ racing scope (operator's actual betting universe) makes the missing-race-reference edge case non-binding. Slice 6 fully closes here: piece 1 (`bet_settled` with finish_position, field_size_at_settlement, field_size_at_bet_placement amendments), piece 2 (hedge state derivation + `hedge_state_classification` event), piece 3 (cascade rule with full operator-explicit / auto-cascade / Burst Review surfacing model). Eight operator questions worked through Q1–Q8 locked; Q9 noted for reconciliation review. Closed-schema-open-vocabulary pattern instance count finishes at seven for Slice 6.

**Closed:** 2026-04-27 21:03 ACST
**Summary:** Slice 6 fully closed. Hedge state model locked: six states per DR-025, derived on read against `lay_order_finalised` chain then `hedge_state_classification` event then default `unhedged_unclassified`. `hedge_state_classification` event payload locked with three writing paths (operator_explicit / auto_resolved_timeout / auto_classified_promo_default for insurance bets only) and oversight_reason enum (operator_distraction | tool_failure | external_disruption | other). Cascade rule for `bet_settled` supersession locked: scope is `free_bet_credited` and `promo_cash_credited` only; supersession-pattern mechanism with cascade_path enum (auto for clean full-invalidation, operator_explicit for graded/manual cases); Burst Review cascade events view day-one. Slice 6 piece 1 amended with `finish_position` (resolves outcome-vs-physical-finish terminology cleanly), `field_size_at_settlement`, `field_size_at_bet_placement`. Race classification (`race_class`, `race_distance`, `race_surface`) provisionally placed on race reference record (Option B), pending Slice 1 verification during reconciliation contract review. Reconciliation contract, build strategy, and `diagrams/v3_target.svg` carry to Session 11.
