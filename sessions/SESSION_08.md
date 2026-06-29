# Session 8 — active log

**Session opened:** 2026-04-27 15:32 ACST

## Scope (planned, in order)

1. Resolve Q1 (auto-diff vs compute-on-read for promo terms changes) and Q2 (provisional-then-finalised vs no-credit-until-confirmed for low-confidence auto-derived FB credits) to close Slice 4.
2. Slice 5 — four-state cash flow.
3. Slice 6 — hedge state (six DR-025 states reading against `lay_order_finalised`).
4. Reconciliation contract write-up.
5. Build strategy decision (strangler-fig vs clean break + slice strategy, resolved together).
6. `diagrams/v3_target.svg`.

If context tightens: split before the diagram first, then before build strategy.

## Open questions carried in

- (Q1) Promo terms change capture — auto-diff vs compute-on-read shrink signal. Claude leaning compute-on-read.
- (Q2) Provisional FB credit state — provisional-then-finalised vs no-credit-until-confirmed for low-confidence auto-derived FB credits. Claude slight lean provisional.
- Item 5 build strategy — interlocked, resolve together.

## Framing note

Workflow-first framing carries forward from Sessions 6 and 7. Software questions are Claude's; ask only about betting/operational matters. Honour DR-021, DR-007, DR-022, DR-024. Use Desktop Commander for all rebuild folder file operations (bash sandbox can't reach it).

## Entries

### 2026-04-27 15:32 ACST — Session opened

Anchored on system clock per DR-021. Read `work_in_progress.md`, `sessions/SESSION_07.md` in full, `decisions.md` DR-001 through DR-026 in full. Confirmed framing instruction and Slice 4 carry-forward state with Q1, Q2 parked at Session 7 close. About to open Q1, Q2 to close Slice 4.

### 2026-04-27 16:14 ACST — Slice 4 closed

Q1 locked: compute-on-read for promo journey (no `promo_terms_changed` event); promo journey reconstructed from consecutive `promo_observed` events. Operator surfaced analytical use case for cross-stream reconciliation (promo terms timeline binding against AccountCare actions, conditioning, IP state, throttle history). To support operator interpretive context that isn't derivable from event streams, added `promo_journey_annotation` event with tags-based open vocabulary, optional `time_window_start/end`, optional `relates_to_event_ids`, `confidence` field tracking hypothesis → confirmed/disproven evolution. Closed-schema-open-vocabulary pattern matches the source reliability deferral.

AccountCare warning overlay surfaced as Slice 4 addition (operator's behavioural-analysis insight): bets placed during active warnings need queryable linkage for outcome analysis and warning recalibration. Locked: `accountcare_warning_raised` event with warning_type referencing `warning_catalogue` reference data, severity, condition_payload JSON, account_at_book scope; `accountcare_warning_cleared` event with raised_event_id link and clear_reason enum (condition_resolved | operator_dismissed | superseded_by_higher_severity); `active_warnings_at_log` snapshot on `bet_placed` payload. Warning catalogue extensibility via reference data inserts (closed schema, open vocabulary) — new warning types added without schema migration.

Q2 locked at deferred shape: confidence model and source reliability table both deferred to standalone post-source-survey work (operator correctly identified that confidence tier definition is premature without knowing source landscape, refresh latency, code coverage, quality characteristics). Schema carries `confidence_payload` JSON on `free_bet_credited` for whatever shape the eventual model produces, plus `status` field (provisional | finalised | rejected). Status field is a clean operational signal independent of the confidence model.

`credit_source` enum collapsed from four values to two on operator correction: `triggered` | `freebie`. Promo type variation (race insurance, bonus winnings FB and cash, SGM, BOB) carried by `promo_type_at_log` and the `promo_observed` template link, not by credit_source. Manual goodwill via phone confirmed as `freebie`. Bonus-cash-with-rollover dropped (US/UK pattern, not AU current market).

FB-used-before-credit-finalisation locked: `pending_fb_deployment` boolean flag on `bet_placed`, no separate event type; absence of matching `free_bet_deployed` event is the signal. Burst Review surfaces unaccounted FB deployments via query (FB stake recorded but no deployment event); operator resolution at review time creates the `free_bet_deployed` event with correct `source_credit_event_ids`. Negative FB balance and unaccounted FB additions surfaced as Burst Review sanity checks.

Slice 4 fully closed. About to open Slice 5 — four-state cash flow.

### 2026-04-27 17:42 ACST — Slice 4 reopened on operator pushback; promo template granularity and entry workflow worked through

Operator surfaced promo template granularity question after initial Slice 4 close — how the suite of promo variants (e.g. $50 vs $25 stake caps on same general 2nd/3rd insurance) gets represented and entered. Worked through two-layer model: `promo_template` carries kind-level structural mechanics (~10–30 rows; trigger condition, settlement type, name, kind enum); `promo_observed` event's `terms_at_observation` JSON carries parametric terms (max_stake, min_odds, qualifying odds, eligible codes, expiry rules). Trigger condition lives on template (structural, drives auto-credit logic); parametric terms live on observation. Combinatorial explosion avoided by not putting variants in template.

Promo entry workflow locked as Option A — autofill from observation history, scoped first to (book × template × account-at-book) then to (book × template) book-wide. No `promo_variant` reference data entity. Manual entry escape hatch retained in planner UI for genuinely novel promos; entry writes to observation event normally and becomes autofill candidate next time. UI concern primarily; schema-side decision is "no variant entity, terms live on observations."

Settlement type collapsed from three values to two on operator correction: `free_bet` | `cash`. Bonus cash dropped (US/UK pattern, not AU). Cash-boost-style promos (e.g. 25% on winnings) are `settlement_type = cash` with the boost percentage carried in `terms_at_observation`. New event type added: `promo_cash_credited`, symmetric with `free_bet_credited`. Payload: `account_at_book_id`, `amount`, `triggering_bet_event_id` (nullable for non-bet-triggered cash bonuses), `triggering_promo_instance_id`, `recorded_at`, `status` (provisional | finalised | rejected), `confidence_payload` JSON. Cash balance per DR-019 includes finalised `promo_cash_credited` events as positive contributions to at-book balance.

Operator surfaced cascade case for status correction: provisional bet outcome corrected from win to loss must propagate to dependent provisional credits (FB or cash), and may trigger different promo (e.g. 2nd-place insurance fires when initial-classification-as-1st gets rejected as 2nd). DR-019 compute-on-read handles this natively — no stored aggregates to invalidate. Cascade rule (auto-cascade for derivation-linked credits, Burst Review surfaces for visibility) flagged for Slice 6 specification when bet settlement events get fully locked.

Slice 4 fully closed (re-confirmed). Natural close — Slice 5 carries forward to Session 9 along with the two open Slice 5 operator questions and the Slice 6 cascade rule.

**Closed:** 2026-04-27 18:01 ACST
**Summary:** Slice 4 closed in full. Q1 locked compute-on-read for promo journey with `promo_journey_annotation` event added (tags-based open vocabulary). AccountCare warning capture added to Slice 4 (`accountcare_warning_raised`, `accountcare_warning_cleared` events; `active_warnings_at_log` snapshot on `bet_placed`; `warning_catalogue` reference data). Q2 deferred to post-source-survey work; schema carries `confidence_payload` JSON and `status` field. `credit_source` collapsed to `triggered` | `freebie`. `pending_fb_deployment` flag on `bet_placed` for FB used before credit finalisation. Two-layer promo template/observation model locked (template = kind, observation terms = variant); autofill-from-history entry workflow with manual escape hatch. Settlement type collapsed to `free_bet` | `cash`; new `promo_cash_credited` event symmetric with FB credit. Cascade rule for status correction flagged for Slice 6. Session 8 closed at end of Slice 4 — Slice 5 (cash flow), Slice 6 (hedge state + cascade rule), reconciliation contract write-up, build strategy, and `diagrams/v3_target.svg` carry to Session 9. Early-close pattern continues; consistent with Sessions 3–7.
