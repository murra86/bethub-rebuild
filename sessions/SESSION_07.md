# Session 7 — active log

**Session opened:** 2026-04-27 14:05 ACST

## Scope (planned, in order)

1. Resolve Slice 2 open questions D, E, F to close Slice 2.
2. Slice 3 — bet record (incl. Session 6 additions: market_id link, bet_placed_at + placement_time_source, SGM extension fields).
3. Slice 4 — promo + free-bet linkage (trigger-term variations, manual freebie path, FB revocation).
4. Slice 5 — four-state cash flow.
5. Slice 6 — hedge state (reads against `lay_order_finalised`).
6. Reconciliation contract write-up.
7. Build strategy decision (strangler-fig vs clean break + slice strategy, resolved together).
8. `diagrams/v3_target.svg`.

If context tightens: split before the diagram first, then before build strategy. Schema slices remain densest and most consequential.

## Open questions carried in

- (D) Trigger-position result-source reliability per code (thoroughbred / harness / greyhound). Operational call. Needs operator read.
- (E) Single event log table vs split per category. Software. Lock to single unless operator pushes back.
- (F) Never delete events, always supersede. Software. Lock to never-delete unless operator pushes back.
- Item 7 build strategy — interlocked, resolve together.

## Framing note

Workflow-first framing carries forward from Session 6. Lead with concrete operator walkthroughs; only introduce abstract patterns after the workflow ground is firm. If operator can't follow, framing is wrong, not operator. Software questions are mine; only ask the operator about betting/operational matters.

## Entries

### 2026-04-27 14:05 ACST — Session opened

Anchored on system clock per DR-021. Read `work_in_progress.md`, `sessions/SESSION_06.md` in full, `decisions.md` DR-001 through DR-026 in full. Confirmed framing instruction and Slice 2 carry-forward state. About to open D, E, F to close Slice 2.

### 2026-04-27 14:18 ACST — D, E, F resolved; Slice 2 closed

E locked: single event log table. F locked: never delete, always supersede. D locked to D1 (auto-classification with conservative default, two-source agreement where a second source exists, low-confidence cases flagged to Burst Review). Per-code result-source list deferred to auto-settlement build session — candidates flagged include Betfair Win, The Racing API, Racing Australia, RaceNet. Operator's stated aim is full D1 across all three codes; calibration during build determines which sources land where. About to open Slice 3 — bet record.

### 2026-04-27 14:52 ACST — Slice 3 closed; FB structure reshape lifted into Slice 4

Slice 3 walked through five workflows (live racing bet, retrospective entry, SGM, FB deployment, edited bet). Operator corrections absorbed across two rounds. Final Slice 3 shape: bet record is event-typed (`bet_placed` in single event log per E); first-class columns for common fields (event_type, recorded_at, occurred_at, account_id, book_id, account_at_book_id, supersedes_event_id, parent_event_id); JSON payload for type-specific fields. Bet payload carries: stake split into `cash_stake_amount` + `free_bet_stake_amount`; `runner_id` + `runner_name` (denormalised); `event_id` + `bet_type`; odds; `bet_placed_at` + `placement_time_source` + `recorded_at`; `promo_instance_id` + `promo_type_at_log`; full Betfair snapshot per DR-026 (`bf_market_id`, `bf_runner_id`, `bf_runner_name`, best back/lay + sizes, total matched, snapshot age, stale flag, `bf_snapshot_aligned_to_placement` for retrospective cases); `is_sgm` + `leg_count`; outcome + hedge state initially null; model fields (`model_estimated_odds`, `model_estimated_probability`, `model_version`, `model_estimated_at`) nullable until model built. SGM legs are `bet_leg` child events carrying Betfair market_id/selection_id as primary identifier (text description fallback only when Betfair lacks the market), per-leg Betfair snapshot, `leg_index`, `model_leg_probability` nullable. Sports-betting transferability confirmed: same schema for racing and sports. Live-mode lodgement: `bet_placed_at` = `recorded_at`, system-stamped, no operator picker. Retrospective entry: separate flow with coarse picker; `bf_snapshot_aligned_to_placement = false`. FB structural reshape (forced by operator's correction in Walkthrough 4) lifted into Slice 4: many-to-many credit-to-deployment junction, `book_treats_as` distinction dropped, uniform balance-pool treatment, FIFO-by-expiry as universal draw-down default with operator-override supported. About to open Slice 4 properly.

### 2026-04-27 15:05 ACST — Slice 4 walked through; two questions surfaced and parked

Slice 4 walked through eight workflows: promo observation (with `promo_template_id` reference data + `promo_observed` events carrying scope, account_at_book scoping, terms-at-observation snapshot); promo shrink as supersession-or-derived signal; taking a promo (the bet's `promo_instance_id` link); insurance trigger producing `free_bet_credited` with full traceability to triggering bet + promo; freebies as operator-entered credits with `credit_source = freebie`; FB deployment with many-to-many junction (`source_credit_event_ids` array + `draw_down_breakdown` payload); FB revocation (Session 6 addition); FB expiry (system-derived where possible, operator-entered fallback). Two open questions: Q1 — auto-diff promo terms changes vs compute-on-read shrink signal (Claude leaning compute-on-read); Q2 — provisional-vs-finalised state on auto-created FB credits vs no-credit-until-confirmed for low-confidence cases (Claude slight lean provisional for audit-trail reasons, both defensible).

### 2026-04-27 15:08 ACST — SGM pairwise joint probabilities locked in

Operator surfaced pairwise joint probabilities for SGM calibration. Worked through analytical value (decomposes joint-probability error into marginal vs correlation calibration questions) vs production tractability (model-architecture-dependent, but storage is trivial). Locked: `model_pairwise_probabilities` JSON array nullable on `bet_placed` for SGM bets. Populated when model exposes pairwise joints; null otherwise. Triple-and-higher joints not added day-one but extensible without migration via same JSON column. Slice 3 model-fields list now complete: parent carries `model_estimated_odds`, `model_estimated_probability`, `model_version`, `model_estimated_at`, `model_pairwise_probabilities`; each `bet_leg` carries `model_leg_probability`.

### 2026-04-27 15:23 ACST — Session closing

Natural close at end of Slice 3 (closed including SGM pairwise joints), Slice 2 closed (D, E, F resolved), Slice 4 walked through structurally with two open questions parked for Session 8 (Q1 promo-shrink auto-diff vs compute-on-read; Q2 provisional vs no-credit-until-confirmed for low-confidence FB auto-credits). Early-close pattern continues — schema decisions at this depth justify preserving quality over closing scope.

**Closed:** 2026-04-27 15:23 ACST
**Summary:** Slice 2 closed (E single table, F never-delete-supersede, D auto-classification with conservative default and per-code source list calibrated during build). Slice 3 closed in full including model-field structure for SGM calibration (joint odds, joint probability, per-leg probabilities, pairwise joint probabilities, model_version). Sports-betting transferability confirmed. FB structural reshape from operator correction (uniform balance-pool treatment, drop `book_treats_as`, FIFO-by-expiry universal default with operator override) lifted into Slice 4. Slice 4 walked through eight workflows establishing promo observation/template/shrink shape, FB credit lifecycle (triggered, freebie, revocation, expiry), and FB deployment with many-to-many junction. Two questions surfaced and parked for Session 8 opening.


---

## Session 11 amendment — race-side identifier integration semantics

**Added:** 2026-04-28 (Session 11)

The `bet` event payload's `event_id` and `bf_market_id` fields are references into `capture.db` (the existing UK VPS racing-data capture system), resolved at read time via `vps_client` per DR-027. No v3-side race table exists; per DR-028 these fields are not FK columns to a v3 race entity, and v3 does not store denormalised race-data alongside them.

The DR-026 market-context snapshot fields on `bet_placed` payloads (`bf_market_id`, `bf_runner_id`, `bf_runner_name`, best back/lay + sizes, total matched, snapshot age, stale flag, `bf_snapshot_aligned_to_placement`) are sourced from `capture.db` via `vps_client` per the DR-026 amendment dated 2026-04-28. The fields and semantics are unchanged. Per DR-029, the architecture is periodic-only with analytical bracketing; no on-demand fresh-now pattern is added unless cadence verification proves insufficient.

`bet_leg` events (SGM legs) carry their own per-leg Betfair `market_id` / `selection_id` references, sourced and resolved through the same integration path.

Slice 3's central design decisions (event-typed bet record, first-class columns plus JSON payload, sports-betting transferability, model fields including pairwise joint probabilities, retrospective entry flow with `bf_snapshot_aligned_to_placement = false`) are unchanged. This amendment documents only the architectural source-path for the race-side identifier and snapshot fields.

**Open question for Session 14 multi-agent review:** the v3 bet payload's snapshot fields (best_back/lay, sizes, total_matched, snapshot_timestamp, stale_flag, bf_snapshot_aligned_to_placement, bf_snapshot_unavailable) and the Slice 6 field_size captures (field_size_at_bet_placement, field_size_at_settlement) are reserved for review at Session 14's multi-agent governance review. Architectural simplification to drop these in favour of full cross-DB resolution from capture.db (bet stores only identifiers + placement_time; race-side context resolved via `vps_client` at read time) is plausible but has not been independently assessed. Slice 3 and Slice 6 schemas remain as previously locked until reviewed.
