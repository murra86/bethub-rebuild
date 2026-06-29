# Session 9 — active log

**Session opened:** 2026-04-27 18:10 ACST

## Scope (planned, in order)

1. Resolve Q3 (inter-account-holder funding — Tim→Sarie debt tracked or not) and Q4 (friend payments — friends as account holders or pure external recipients) to close Slice 5.
2. Lock Slice 5 event-type catalogue (`account_at_book_deposit`, `account_at_book_withdrawal`, `account_at_book_balance_adjustment`, `account_settlement`, `external_payment` provisionally proposed in Session 8).
3. Slice 6 — hedge state. DR-025's six states reading against `lay_order_finalised` parent/child pattern from Session 6; `bet_settled` event type fully specified; cascade rule for status correction flagged in Session 8.
4. Reconciliation contract write-up.
5. Build strategy decision (strangler-fig vs clean break + slice strategy resolved together).
6. `diagrams/v3_target.svg`.

If context tightens: split before the diagram first, then before build strategy.

## Open questions carried in

- (Q3) Inter-account-holder funding — Does Tim funding Sarie's account-at-book create tracked Tim→Sarie debt in the system, or is inter-account-holder balance reconciled outside the system? Claude lean: track if regular bilateral settlement; skip if pure working-capital reconciled at operation level. Operator call.
- (Q4) Friend payments and account holder identity — Are hosting friends ever full account holders, or always purely external recipients? Claude lean: schema can distinguish (Scope C `account_settlement` vs Scope D `external_payment`); operator names which friends fall in which bucket. Operator call.
- Build strategy — interlocked, resolve together with slice strategy.

## Framing note

Workflow-first framing carries forward (reinforced by Sessions 6, 7, 8 success). Software questions are Claude's; ask only about betting/operational matters. Honour DR-021, DR-007, DR-022, DR-024. Use Desktop Commander for all rebuild folder file operations (bash sandbox can't reach it).

## Entries

### 2026-04-27 18:10 ACST — Session opened

Anchored on system clock per DR-021. Read `work_in_progress.md`, `sessions/SESSION_08.md` in full, `decisions.md` DR-001 through DR-026 in full. Confirmed framing, Slice 4 closed-state, Slice 5 carry-forward with Q3/Q4 parked, and the Slice 6 cascade rule flagged from Session 8. About to open Q3 to operator.

### 2026-04-27 18:44 ACST — Q3 + Q4 resolved; three-balance-location model locked

Initial Q3 framing was wrong on two counts. Operator corrected: the model is three balance locations, not two. (1) Tim's money — master pool. (2) Account-at-book balances — money at bookmakers in registrations, owned by Tim economically, held under different account-holder identities. (3) Cash holdings with account holders — money transferred to a custodian (Sarie, Kate, friend) that they're physically holding in their bank account awaiting deposit into one or more accounts-at-book over days/weeks. Still Tim's money. Account holders are custodians, not creditors. Tim never deposits into accounts that aren't his own — the account holder always executes the deposit themselves from cash they're holding on Tim's behalf.

Profit share is an outflow event, not a balance mechanic. When Tim transfers $1,500 to a custodian with $200 earmarked as profit share, the $200 leaves the operation immediately and the custodian is now holding $1,300 of Tim's money. No account-holder credit balance accrues over time.

Funds-flow structure on deposits: Tim → account holder (cash holding) → account-at-book (two distinct events with duration on the middle hop). Withdrawals mirror: account-at-book → account holder → Tim, possibly net of a separate profit-share outflow.

Q4 collapses inside this model: friends are *always* account holders (custodians who may also host registrations) — never pure external recipients of friend payments. Scope D `external_payment` remains in the catalogue but is reserved for non-account-holder operational expenses (tax, VPS, Racing API subscription), not friend payments.

Cash-holding-with-account-holder balance is tracked (DR-019 derived) with cash age — operator wants to know how much is sitting where and how long it's been there. This is working-capital surveillance, not just event recording. About to assemble the corrected Slice 5 event-type catalogue against this model.

### 2026-04-27 19:00 ACST — Slice 5 event-type catalogue locked

Seven event types and two reference data tables. Method fields dropped throughout (funding/deposit/withdrawal/remittance/distribution method) — operator confirmed transport mechanism is irrelevant; only the fact and quantum of cash movement matters. `withdrawal_landed_at` dropped; only `withdrawal_initiated_at` retained. `relationship_note` dropped from `account_holders`.

Profit share gets `funding_source` enum on `profit_share_distribution` (`tim_direct` | `account_holder_cash_holding`) which cleanly handles both the standalone-transfer-from-Tim shape and the deducted-from-cash-holding shape. The previously-considered `deducted_from_remittance` value folds into `account_holder_cash_holding` — same accounting outcome, simpler enum. A $1,500 transfer with $200 profit share is now: one `account_holder_funding` event ($1,500), one `profit_share_distribution` event ($200, `funding_source = account_holder_cash_holding`), leaving $1,300 in cash-holding for deposits. Same pattern works for the withdrawal-side variant.

Question (a) locked: `payees` reference data table for `external_payment.recipient`.
Question (b) locked: `is_self = true` on `account_holders` — Tim is a row, schema treats Tim → Tim cases as natural no-ops without special-casing.

**Final event types:**
1. `account_holder_funding` — Tim → custodian. Payload: `account_holder_id`, `amount`, `transferred_at`, `note` (opt), `recorded_at`.
2. `account_at_book_deposit` — custodian → account-at-book. Payload: `account_at_book_id`, `account_holder_id` (sourcing custodian), `amount`, `deposited_at`, `recorded_at`.
3. `account_at_book_withdrawal` — account-at-book → custodian. Payload: `account_at_book_id`, `account_holder_id` (receiver), `amount`, `withdrawal_initiated_at`, `recorded_at`.
4. `account_holder_remittance` — custodian → Tim. Payload: `account_holder_id`, `amount`, `remitted_at`, `note` (opt), `recorded_at`.
5. `account_at_book_balance_adjustment` — book-side non-bet/non-promo correction. Payload: `account_at_book_id`, `amount` (signed), `adjustment_reason` (enum: `bookmaker_error_correction` | `late_scratch_deduction` | `dormant_account_credit` | `regulatory_adjustment` | `other`), `note` (req if `other`), `recorded_at`.
6. `external_payment` — operational outflow. Payload: `payee_id` (FK), `amount`, `category` (enum: `tax` | `infrastructure` | `data_subscription` | `tooling` | `other`), `paid_at`, `note` (opt), `recorded_at`.
7. `profit_share_distribution` — distribution to account holder personally. Payload: `account_holder_id`, `amount`, `funding_source` (enum: `tim_direct` | `account_holder_cash_holding`), `distributed_at`, `relates_to_period_start` (opt), `relates_to_period_end` (opt), `note` (opt), `recorded_at`.

**Reference data:**
- `account_holders` — `account_holder_id`, `name`, `is_self` (bool), `active` (bool).
- `payees` — `payee_id`, `name`, `default_category` (opt), `active` (bool).

**DR-019 derived state for Slice 5:**
- Cash-holding-per-custodian = sum(funding in) + sum(withdrawals received) − sum(deposits sourced) − sum(remittances) − sum(`profit_share_distribution` where funding_source = `account_holder_cash_holding`).
- At-book balance = existing Slice 3/4 derivation + sum(deposits) − sum(withdrawals) ± sum(adjustments).
- Cash age per custodian: FIFO walk of funding events against drawdowns; oldest unconsumed funding gives maximum age.
- Tim's own bank balance not computed (system can't observe arbitrary external bank movements); Tim-as-custodian cash-holding gives the operationally-relevant slice.

**Burst Review surfaces:** stale cash holdings (operator-tunable age threshold), negative cash-holding balances (logging gap signal), periodic external_payment / profit_share totals.

Slice 5 closed. About to open Slice 6 — hedge state, `bet_settled`, cascade rule.

### 2026-04-27 19:26 ACST — `bet_settled` event type locked; Slice 6 piece 1 closed

`bet_settled` payload locked: `parent_event_id`, `outcome` (closed enum), `cash_returned_to_book`, `each_way_payload` (JSON, nullable; single event handles each-way), `sgm_leg_outcomes` (JSON array, nullable), `result_source` (enum: `betfair` | `racing_api` | `racing_australia` | `racenet` | `manual`), `result_observed_at`, `confidence_payload` (JSON), `status` (`provisional` | `finalised` | `rejected`), `recorded_at`, `occurred_at`, `note` (optional).

Outcome enum: `won | placed | lost | dead_heat_won | dead_heat_placed | voided | won_each_way | placed_each_way_only | lost_each_way | won_sport | lost_sport | pushed_sport`. Closed enum, extensible by new value when patterns emerge. UI principle locked alongside schema: execution-layer surfaces present `won | lost | voided` as primary with rest behind a "more outcomes" affordance — 99.9% case is one keystroke, 0.1% case is two. Burst Review and analytical surfaces show full granularity. UI principle, not schema change.

`scratched_protest_reversed` dropped from outcome enum — supersession path handles all post-settlement reversals. Original `bet_settled` records what was paid; superseding `bet_settled` records the correction; `note` field captures reversal context.

**Late-scratch dividend simplification (operator insight):** Case A (pre-settlement late scratch reducing dividend) collapses into Case B (post-settlement supersession) operationally — operator only notices dividend changes post-settlement. Therefore `dividend_deduction_pct` field dropped from `bet_settled` payload. Original settlement records actual cash returned (whether or not deduction-affected); supersession handles any subsequent correction. One mechanism, one mental model. Cleaner schema, less UI friction.

`result_source_confidence` deferred (per Q2 lean) — schema carries `confidence_payload` JSON only; dedicated field added when confidence model lands post-source-survey.

**Operator-confirmed architectural principle:** closed-schema-open-vocabulary promoted to architecture-level pattern when next we lift to `architecture.md`. Now appears in five places (annotation tags, AccountCare warning_type, promo terms_at_observation, Slice 5 enum extensibility, bet_settled outcome enum). Genuinely how this rebuild's schema thinks about structure-vs-flexibility.

Slice 6 piece 1 closed. Hedge state derivation, `hedge_state_classification` event, cascade rule (open items f/g/h) carry to Session 10. Operator chose to close here — Slice 5 reshape was substantial work, `bet_settled` is a clean handoff point, hedge state cascade interactions with FB deployment chains benefit from fresh attention.

**Closed:** 2026-04-27 19:30 ACST
**Summary:** Slice 5 fully closed against corrected three-balance-location model (Tim's money / account-at-book / cash-holding-with-account-holder). Q3 resolved: cash holdings with custodians are tracked balances with cash age, not bilateral debt. Q4 resolved: friends are always custodians, never pure external recipients. Seven Slice 5 event types locked: `account_holder_funding`, `account_at_book_deposit`, `account_at_book_withdrawal`, `account_holder_remittance`, `account_at_book_balance_adjustment`, `external_payment`, `profit_share_distribution` (with `funding_source` enum cleanly handling tim-direct vs deducted-from-cash-holding). Two reference data tables: `account_holders` (with `is_self`), `payees`. Slice 6 piece 1: `bet_settled` event type locked with late-scratch dividend simplification (Case A collapses to Case B via supersession; `dividend_deduction_pct` dropped). UI bias-to-common-path principle for outcomes surfaced. Closed-schema-open-vocabulary promoted to architectural principle (5 instances). Hedge state, cascade rule, reconciliation contract, build strategy, and diagram carry to Session 10.

---

## Session 14 amendment — `account_holder_balance_adjustment` event type

**Amendment date:** 2026-04-28 15:35 ACST. Source: Session 13 deliberation captured in delta-spec; Session 14 promotion. Closes a day-0 opening-balance gap on custodian holdings (Location 2 in the cash-flow model) surfaced during Session 13 cash-flow deliberation.

### Why

Day-0 opening balances on custodian holdings (~$12.5k of working capital across the operation at v3 launch) need an entry path. The existing `account_at_book_balance_adjustment` event handles day-0 openings on Location 1 (account-at-book balances) cleanly. Custodian holdings have no symmetric event: Location 2 derives purely from the four flow events (`account_holder_funding`, `account_at_book_deposit`, `account_at_book_withdrawal`, `account_holder_remittance`, `profit_share_distribution`). Without a balance-adjustment event for custodians, day-0 working capital sitting at custodians at v3 launch cannot be entered without resorting to backdated-funding-with-marker semantics — which would pollute `account_holder_funding`'s meaning. This amendment adds the symmetric event type.

### Event type: `account_holder_balance_adjustment`

Symmetric to existing `account_at_book_balance_adjustment`. Payload mirrors the at-book version:

- `account_holder_id` — FK to `account_holders`
- `signed_amount` — positive or negative dollar adjustment
- `adjustment_reason` — closed-schema-open-vocabulary enum; day-one values include `day_0_opening` plus operator-graded corrections (custodian counting corrections, etc.)
- `note` — free text, optional
- standard event header (`recorded_at`, `occurred_at`, `supersedes_event_id`, etc.)

### Day-0 opening pattern (both locations)

At v3 launch (day 0), the operator enters existing working capital via balance-adjustment events:

- `account_at_book_balance_adjustment` events with `adjustment_reason = 'day_0_opening'` for each account-at-book holding non-zero balance.
- `account_holder_balance_adjustment` events with `adjustment_reason = 'day_0_opening'` for each custodian holding non-zero cash.

After day 0, both adjustment event types are operator-graded corrections — same operational semantics as the existing at-book version.

### Cash-flow model interaction

Per the reconciliation contract A.5 (in `architecture.md`), `account_holder_balance_adjustment` is an **internal** cash-flow event — it does not touch Tim's bank. It does not appear in the operation-net-flow formula (which sums only the four bank-touching event types: `account_holder_funding`, `account_holder_remittance`, `external_payment`, and `profit_share_distribution where funding_source = 'tim_direct'`). Day-0 openings entered via balance-adjustment events represent capital already committed to the operation before v3 launch — they neither add to nor subtract from the running total of net cash pulled from Tim's bank since day 0.

### No v2 transaction backfill

v3 starts fresh from day 0. v2 keeps running until v3 displaces it; v3's transaction history begins at v3 launch. v2 historical data is not imported. Day-0 opening balances on both Location 1 and Location 2 enter via the `*_balance_adjustment` events with `adjustment_reason = 'day_0_opening'`.

### Rest of Slice 5 unchanged

All other Slice 5 schema and event-type definitions remain as previously locked. This amendment adds one new event type symmetric to an existing one; no existing field, payload, or derivation is modified.
