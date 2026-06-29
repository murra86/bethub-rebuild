# Session 5 log

**Opened:** 2026-04-26 21:56 ACST
**Closed:** 2026-04-26 23:09 ACST
**Timezone:** Australia/Adelaide (locked default per Session 4)
**Governance:** DR-021 (system-date verify, per-entry timestamps anchored to real clock)

---

## Scope as planned

1. Accounting layer schema design — six slices (entity hierarchy → event log → bet record → promo + FB linkage → four-state cash flow → hedge state)
2. Reconciliation contract write-up
3. Build strategy decision (strangler-fig vs clean break + slice strategy, resolved together)
4. `diagrams/v3_target.svg`

If context tightens: split before diagram first, then before build strategy.

## Standing rules in force

- DR-007: vocabulary discipline (account / book / account-at-book)
- DR-021: system-date verify per governance write, Adelaide local
- DR-022: prior DRs read "persona" as "account"
- DR-024: reinforce operating/analytical separation if drift detected
- DR-026: load-bearing for Slice 3, locked Session 4

## Activity

### 21:56 ACST — Session opened
Timestamp anchored via `TZ="Australia/Adelaide" date`. Session log created.

### 21:58 ACST — Orientation complete
Read `work_in_progress.md`, `SESSION_04.md`, `decisions.md` (DR-001 through DR-026) in full. Confirmed Round 5 stars, DR-026's reasoning, six-slice plan, three open pushback questions for Slice 1.

### 22:41 ACST — Slice 1 closed (with one open item)
Slice 1 entity hierarchy locked: 8 entities (account, book, ownership_cluster, platform, account_at_book, promo_template, promo, bet) with cardinality map. Open questions resolved: (A) `promo_template` first-class, (B) free bets event-sourced [B2], (C) `account_arrangement` as history of intents with effective dates, settlement events on event log.

Operator additions captured: account holds full sign-up details (legal name, DOB, address, ID, email, password); password storage approach is open item Q1.5 (recommended B1: pointer to password manager entry, not raw password).

Two guardrails added: (1) hygiene rules table populated only with rules producing concrete weekly-plan output; (2) tier/phase fields stay at v2's tier 1/2/3 + phase 0–5 unless build forces expansion. One platform note: cluster > platform coupling severity; cluster-propagation events on event log carry axis tag.

### 22:51 ACST — Slice 1 final lock
Q1.5 resolved: B1 (password as pointer to manager entry) locked; operator currently uses memorised shared password across books per account, flagged as v3 build-time workflow improvement (unique password per book generated at registration, stored in manager) — not a schema decision.

C2 enriched on operator's "very fluid" feedback. Arrangement entity now has type field (`onboarding_sweetener` / `ad_hoc_performance_share` / `structured_share`), `effective_from`/`effective_to` dates, free-text notes, optional `terms_json` (populated only for `structured_share`). Payment events on event log carry their own free-text reasoning at time of payment. Move from ad-hoc to structured is a new arrangement row, not an edit. The reasoning field is load-bearing for eventually deriving fair structured splits from a year of operator-context-tagged payments.

### 23:00 ACST — Slice 2 presented; operator flagged uncertainty
Slice 2 presented in full: event shape (id, type, `occurred_at` vs `recorded_at`, source, related_entities, payload, `correlation_id`, `superseded_by`, notes), six event categories, ~25 event types catalogued, derived-state examples (FB inventory, weekly turnover, balance reconciliation), three open questions (D — auto-classify losses vs operator-confirm; E — single event log vs split per category; F — never delete, always supersede).

Operator added permanence note on C2 arrangements: `ad_hoc_performance_share` is a valid permanent arrangement type, not a transition state. Schema allows but does not force the move to `structured_share`. Folded into Slice 1's lock.

Operator flagged not fully understanding Slice 2 substance and asked whether to close out. Claude recommendation: close. Slice 2 is the foundation Slices 3–6 sit on; locking answers without full operator understanding would compound into every later slice. Slice 1 banks clean.

### 23:09 ACST — Session closed

---

## Summary

Slice 1 (entity hierarchy) fully locked across 8 entities with three open questions resolved (`promo_template` first-class, free bets event-sourced B2, `account_arrangement` as history of intents with optional `structured_share` type). Slice 2 (event log structure) presented but deferred to Session 6 on operator's flag of incomplete understanding — correct call given Slice 2's foundational role for Slices 3–6.

The "I don't fully understand" signal at Slice 2 is a process pattern worth marking. Schema design at this depth has structural-reasoning components that translate badly into software-jargon framings. Future presentations should lead with concrete operator-workflow walkthroughs and only introduce the underlying pattern after the workflow is clear.

The early-close pattern is now consistent across Sessions 3, 4, 5. Sessions 6+ may continue the pattern. This is correct given the cost-of-being-wrong asymmetry in schema design.

---

## Slice 1 schema lock — canonical record

(This section is the canonical record of Slice 1's outcome until lifted to `architecture.md` after the full schema design is complete in Session 6+.)

**Eight entities:**

1. **`account`** — real person whose identity is used for registrations. Holds: identity attributes, full sign-up details (legal name, DOB, residential address, ID details, email, password reference per B1), conditioning profile fields (interests, plausible bet topics, plausible browsing patterns per DR-013/DR-022), and is the locus of the account-level balance sheet (Slice 5 detail). Does not hold per-book money or per-book tier/phase. One account → many `account_at_book`.

2. **`book`** — bookmaker as a company. Holds: display name, short code, website URL, FK to `ownership_cluster`, FK to `platform`, hygiene reference data per DR-013 (subject to Slice 1 guardrail). Reference data; rarely changes.

3. **`ownership_cluster`** — corporate parent group. Holds: cluster name, notes on shared-data behaviour. One cluster → many books. Cluster > platform in coupling severity.

4. **`platform`** — technology platform a book runs on, distinct from corporate ownership. Holds: platform name, notes on platform-level shared-data behaviour. One platform → many books. Independent FK from `ownership_cluster` on `book`.

5. **`account_at_book`** — the specific registration of one account at one book. Composite uniqueness (one account never holds two registrations at the same book). Holds: registration metadata (date, account number/username at book, current status — active/restricted/banned/dormant), tier/phase per DR-013/DR-022 (subject to simplicity guardrail). Does not hold derived hygiene state (last-bet date, WTD turnover, etc.) — those are computed from the event log per DR-019.

6. **`promo_template`** — first-class entity (lock A). Holds: name, promo type (insurance / free bet / boost / cashback / EW cashback / etc.), structural parameters (refund mechanism, cap, eligible markets, eligible odds bands), mathematical model reference (Raw EV / Boosted Odds / Free Bet SNR / EW Cashback). One template → many `promo` instances over time and across books.

7. **`promo`** — specific instance of a promotional offer. Holds: FK to `book`, FK to `promo_template`, active window, scope (all-races / specific-race / specific-event / specific-market), per-instance overrides. One promo → many bets.

8. **`bet`** — central record of a back bet placed at a book. Holds: FK to `account_at_book`, nullable FK to `promo`, race/event/market identifiers (Slice 3 detail), stake/odds/bet type/runner, outcome fields (populated on settlement), DR-026 market-context snapshot (best Betfair lay price + size, best back price + size, total matched, snapshot timestamp, stale flag), hedge classification per DR-025 (Slice 6 detail), edit-history flag (actual edit history lives on event log per DR-017).

**Cardinality map:**

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

**Open question resolutions:**

- **(A) `promo_template` is first-class** — separate entity from `promo`. Reason: structural recurrence pattern is real (same structure across books and weeks), Q2/Q3 analytical queries want stable grouping key surviving operator name-typing variation, fuzzy grouping at planner-entry time is friction (against DR-023). Cost is one extra table and one join; trivial at this scale.

- **(B) Free bets are event-sourced (B2)** — no `free_bet` table. Events `free_bet_credited` / `free_bet_deployed` on the event log; FB inventory and realised cash value derived on read. Reason: aligns with DR-019; v2's $4,800 reconciliation gap partly traceable to FB state going out of sync with bet state when bets edited or anomalies occurred; B2 handles both face value and ~70% realised cash value as derived views (face value drives deployment decision, realised cash value drives operational-balance view); edits to insurance bet flow through naturally via event replay rather than cascade-update. Operator confirmed mental model fits — "70% of FB face value mentally added to balance" is the realised-cash-value view, which B2 produces cleanly.

- **(C) `account_arrangement` is a history of intents with effective dates** — type enum `onboarding_sweetener` / `ad_hoc_performance_share` / `structured_share`, free-text reasoning on each row, optional `terms_json` populated only for `structured_share`. Settlement payments are events on the event log (`friend_payment_made`) carrying their own at-time reasoning. Move from ad-hoc to structured is a new arrangement row, not an edit. `ad_hoc_performance_share` is a valid permanent state — schema allows but does not force the move to `structured_share`. Reason: operator's "very fluid, depends on operational environment, will change with time but may stay fluid even with good data" matches this shape; the at-time reasoning field is the dataset for eventually deriving fair structured splits if/when the operator wants to formalise.

**Build-time considerations (not schema decisions):**

- Operator currently uses memorised shared password across all books per account. v3 sign-up workflow should generate unique password per book at registration time and store in password manager (B1). Flagged for v3 build, not Slice 1. Recommendation made; not high priority per operator.

**Guardrails carried into Slices 2–6:**

- **Hygiene rules table populated only with rules producing concrete weekly-plan output.** Every rule must answer "what concrete weekly-plan output does this produce?" No "interesting observations," "things to watch," or untriggered free-text fields. Operator's slippery-slope concern made structurally explicit.
- **Tier/phase fields stay at v2's tier 1/2/3 + phase 0–5 unless build forces expansion.** Operator's simplicity guardrail.
- **Cluster > platform coupling severity.** Cluster-propagation events on event log carry axis tag (cluster vs platform); same-cluster-different-platform is still cluster-coupled; same-platform-different-cluster is the more common shared risk.

**Session 11 amendment — Q9 resolution (race-reference verification):**

Q9 (Slice 1 race-reference verification) was carried into Session 11 from Session 10. Verification confirmed Slice 1's locked entity hierarchy does **not** add a `race` entity. The race-reference question is resolved by external integration: race-side data (race classification, distance, surface, finish position, runner detail, BSP, Betfair time-series snapshots, bookmaker time-series snapshots) is owned by `capture.db` (the existing UK VPS racing-data capture system) and read by v3 on demand via the data API per DR-027.

The eight Slice 1 entities (account, book, ownership_cluster, platform, account_at_book, promo_template, promo, bet) are unchanged.

The `bet` entity carries race-side identifiers as references, not as denormalised race-data fields:

- `event_id` — Betfair `market_id` for the race-as-betting-market. Stable identifier.
- `bf_market_id` — same value as `event_id`, scoped to the Betfair-source meaning per DR-026 capture conventions. Retained as a separate field for source-clarity.
- `(race_date, venue_normalised, race_number)` — natural-key tuple, available as fallback resolution path when Betfair identifiers are missing or ambiguous (e.g. retrospective bet entry, Betfair market ambiguity).

No `race_id` foreign key. No race classification field. No race-distance field. No race-surface field. No finish-position field on the bet entity (finish position lives on `bet_settled` per the Session 10 amendment, captured at settlement time as a bet-context fact per the DR-026-extended cheap-capture principle, *not* as a denormalised race fact).

Session 10's "Option B" (race classification on the race reference) is preserved in spirit — race classification *is* on a race reference, just not one in v3. It's in `capture.db`, where it has been the whole time.

Australian thoroughbred / harness / greyhound is the in-scope universe per `capture.db` coverage. **NZ is excluded** day-one per operator decision in Session 11. NZ races logged in v3 will resolve race-side identifiers but will return null for race-classification context unless and until NZ coverage lands in `capture.db`. NZ inclusion is a question to be re-asked in the upcoming DR-029 data review (verify Racing API NZ coverage; if available, NZ enters scope; if not, NZ remains a day-one limitation).

**Why this is an amendment, not a Slice 1 reopen:** the eight entities are unchanged. The shape of the bet entity's race-side identifiers is unchanged at the field level (`event_id`, `bf_market_id` were already in the locked Slice 3 record). What this amendment adds is the architectural stance on what those identifiers *mean* — references into `capture.db` rather than identifiers awaiting a future v3 race entity. This documents an architectural fact that wasn't visible at Slice 1 lock time.

**Date:** 2026-04-28

---

## Carried forward to Session 6

### Originally Session 5 items that remain incomplete

- **Item 1 (Schema slices 2–6).** Slice 2 (event log) re-presented from scratch with concrete operator-workflow framing, then 3 (bet record), 4 (promo + FB linkage), 5 (cash flow), 6 (hedge state). Slice 2's three open questions (D — auto-classify losses vs operator-confirm; E — single event log vs split; F — never delete, always supersede) carry forward.
- **Item 2 — Reconciliation contract write-up.**
- **Item 3 — Build strategy decision (interlocked).**
- **Item 4 — `diagrams/v3_target.svg`.**

If Session 6 splits before completing all of these, that is fine. Sessions 7 and possibly 8 may be needed.

### Session 6 framing note (for next-session Claude)

Slice 2 was presented in Session 5 with abstract event-shape tables and software-jargon distinctions (`occurred_at` vs `recorded_at`, supersession, projections). Operator flagged not fully understanding it. Session 6 should re-present Slice 2 with concrete operator-side walkthroughs first — "when you log a bet at PointsBet, here's what happens; when you edit it later, here's what changes; when an insurance bet loses, here's how the FB credit gets created" — and only introduce the abstract event-shape after the concrete picture is solid. The point of Slice 2 is what the operator can do with the system, not the software pattern that makes it work.

If the operator can't follow the framing, the framing is wrong, not the operator. Software questions are Claude's; making the software intelligible to the operator is also Claude's job.

---

## Operator instructions carried forward (still in effect)

- DR-021: system-date verify per governance write, per-entry session log timestamps anchored to real clock not conversation pacing. Adelaide local time (ACST/ACDT) is the default zone.
- DR-007: vocabulary discipline — account/book/account-at-book.
- DR-022: read prior DRs' "persona" as "account."
- DR-024: reinforce operating/analytical separation if operator drifts.
- Software questions are Claude's; only ask the operator about betting/operational matters.

---

## Process notes

The "I don't fully understand" signal from operator at Slice 2 was the right stop signal and is worth marking as a process pattern. Schema design at this depth has structural-reasoning components that translate badly into software-jargon framings. Future presentations should lead with concrete operator-workflow walkthroughs and only introduce the underlying pattern after the workflow is clear.

Slice 1 was high-value because three of the eight entity decisions and all three open pushback questions had real operator content (account sign-up details, hygiene slippery slope, platform-vs-cluster severity, free-bet mental model, friend-payment fluidity, password situation). The pattern of presenting full structure with explicit pushback questions and resolving each with operator-side input continues to work — keep it for Slices 2–6 in Session 6.

The early-close pattern (Sessions 3, 4, 5 all deferring scope to preserve quality) is now consistent and structurally correct given the cost-of-being-wrong asymmetry in schema design.
