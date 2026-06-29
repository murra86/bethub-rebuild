# §2.8 — Bet-schema reframing on the operational/analytical axis

**Status:** Drafting.
**Authored:** Session 70 (2026-05-03 ACST onwards).
**Governing DRs:** DR-027 (two-database architecture: BetHub owns operational state, capture.db owns analytical/source data), DR-028 (cross-database integration boundary discipline), DR-019 (derived state on read), DR-026 (inline snapshot exception on bet records), DR-029 (data-layer fit-for-purpose review before v3 build).
**Source recommendations:** multi-agent review Recommendation 1 (`agent_review/Judge/judge_synthesis.md`).
**Cross-references:** `dr029/dr029_scope.md` §2.8 (scope), §1.4 (soft-book typed-price reframing), §3.11 (soft-book operational layer deferral); `architecture.md` §B.2 (soft-book deferral and typed-price position), §D12 (Betfair as canonical source); `dr029/2_3_periodic_api_pattern.md` (operational/analytical line discipline); `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` §14–§15 (at-placement snapshot precedent).

---

## 1. Framing

The pre-reframe question on bet schema was: leaner-and-simpler vs. more-data-rich. That framing was wrong. It treated the bet record as a single design surface to be optimised on a richness axis, when the underlying decision is about which fields are decision-context facts that must be captured immutably at placement, and which are derivable from the analytical line at read time.

§2.8 reframes the bet schema on the operational/analytical axis already locked by §2.3. The principle: a bet record is the immutable record of a decision the operator made at a moment in time, against a market state visible at that moment, on identifiers that anchor the bet to its canonical Betfair counterpart. Everything else — race classification, runner detail, finish position, market curve, BSP, field size, settlement payout — resolves at read time from the analytical line via `vps_client`, or from current-market reads via `betfair_client`.

This brief specifies the bet record across three bet types: Betfair exchange, soft-book racing, soft-book sports. Each carries the same backbone (decision-context snapshot + Betfair-side identifiers) with type-specific additions for the operator-supplied data that defines the bet's shape (typed price for soft-book, operator-specified line for sports handicap and total markets).

Three architectural commitments shape the brief:

**(a) Betfair-as-canonical-source applies to all bet records.** Per `architecture.md` §D12 and the Session 42 architectural extension, every bet record — Betfair-direct or soft-book — carries Betfair-side identifiers (`market_id`, `selection_id`, plus Betfair venue/sport/event-name) as the canonical join key. This eliminates fuzzy-matching between bet records and the analytical layer at read time. Position A (strict) is locked: a bet record without Betfair-side identifiers does not exist in the normal write path. Three operational paths support this without reducing operator flexibility — see §1.1 below.

**(b) Decision-context immutability holds.** The fields captured at placement that describe the decision the operator made are append-only. Price taken, stake, best back/lay at placement, total matched, snapshot timestamp from operational source — these never change after the placement record is written. Settlement fields (result, P&L, payout) are amendable via reconciliation events, not in-place edits.

**(c) Derived state on read is the default per DR-019.** Race classification, runner metadata, finish position, market curve, BSP, field size — all resolved at read time from `capture.db` via `vps_client`. Stored on the bet record only when the field is itself decision-context (e.g. the operator-specified line for handicap markets is decision-context; the total field size is not).

### 1.1 Three placement paths under Position A

Position A (strict Betfair-as-canonical-source) is supported by three write paths that together cover all real operator placement scenarios. The paths are distinguished by when Betfair-side identifier resolution happens, not by what gets stored:

**(i) Live placement.** Operator places a bet at the moment of the race (or fixture). Betfair is reachable. v3 resolves identifiers via `betfair_client` at click time, captures the at-placement snapshot, writes the bet record with all identifiers populated. The standard path; covers ~all volume.

**(ii) Retrospective placement.** Operator logs a bet after the event has resulted, typically because they forgot to log it at the time. v3 queries Betfair's historical market data via `betfair_client` (the `listMarketCatalogue` / `listMarketBook` surface returns settled markets within Betfair's retention window). Identifiers resolve, settlement state is already known, the record lands complete. `placement_time` is operator-typed (when they actually placed the bet at the soft book); `logged_time` is now.

**(iii) Betfair-unreachable-at-log-time fallback.** Operator logs a bet while Betfair is down, the operator is offline, or the historical market query fails for transient reasons. v3 stores a placeholder record with operator-typed fields and the bet's operator-supplied details. A reconciliation job retries identifier resolution on a schedule; on success, the placeholder is promoted to a full bet record with identifiers populated. The placeholder is operator-visible (in the bet log with a "pending Betfair resolution" indicator) so it doesn't disappear into a queue.

The only placement scenario Position A does not absorb into the normal write path is bets on markets Betfair does not carry at all — soft-book-only markets, novelty markets, exotic constructions. These route to a separate "non-Betfair-resolvable" surface that is operator-visible and operator-acknowledged. In current operations these are vanishingly rare (Strategy 1 and Strategy 2 volume is on standard Betfair-resolvable markets) and worth flagging as strategic outliers when they occur.

### 1.2 What this brief locks vs. defers

This brief locks the bet-record contract: the at-placement field list per bet type, the read-time resolution paths, the immutability discipline, the cycle record specification, and the free bet ledger specification. It does not lock the consumer-side UI behaviour (bet-entry form layouts, retrospective-entry workflow specifics, placeholder-indicator visual design, free-bet balance UI representation); those are downstream of v3 build proper. It does not lock the soft-book operational layer; that is deferred per §3.11 of the scope document.

### 1.3 What §2.8 closes for DR-029

Locks the bet-record contract for v3, plus the cycle record and free bet ledger specifications that the bet record depends on. Unblocks §2.9 (write-side coherence) which depends on §2.8 for the field list and resolution paths. Unblocks §2.7 (API contract versioning) on the bet-record shape. The Session 42 architectural extension lands as load-bearing contract here, satisfying the carry-forward.

---

## 2. Decision-context backbone

The fields below are common to every bet record regardless of type (Betfair exchange, soft-book racing, soft-book sports). They are the immutable record of the decision the operator made, captured at placement-commit and never amended thereafter. Type-specific additions are layered on top per §4, §5, §6.

### 2.1 Identity

- `bet_id` — v3-internal primary key, generated at placement-commit. Operator-invisible.
- `account_at_book_id` — which account-at-book placed the bet. Per DR-022 vocabulary; resolves to (account, book) pair.
- `bet_type` — Betfair exchange | soft-book racing | soft-book sports. Discriminator field for type-specific schema.
- `promo_cycle_id` — reference to the promo cycle this bet belongs to, if any. Set at staging time per §3; immutable post-commit. Null for non-promo bets (e.g. Strategy 4 Synthetic Each-Way value bets). Cycle record specification in §7.

Note: `parent_bet_id` is not a field on the bet record. Parent linkage for free-bet-funded bets is captured on the free bet ledger as consumption events — see §7.2 and §7.3. The relationship between parent (generation source) and child (consumer) is many-to-many: one generation can be consumed by many child bets (full or partial consumption events), and one child bet can consume from many generations on the same placement.

### 2.2 Betfair canonical identifiers

Per `architecture.md` §D12 and the Session 42 architectural extension, every bet record carries Betfair-side identifiers as the canonical join key into the analytical layer.

- `betfair_event_id` — Betfair's event identifier (race or fixture).
- `betfair_market_id` — Betfair's market identifier within the event.
- `betfair_selection_id` — Betfair's runner/selection identifier within the market.
- `betfair_event_name` — Betfair's canonical event name (used for display and audit; analytical joins use the IDs above).
- `betfair_venue` — Betfair's canonical venue/competition string.
- `betfair_sport` — racing | AFL | NRL | etc., per Betfair's taxonomy.

These six fields are populated by v3 at placement-commit via `betfair_client`. Population is mandatory for the normal write path per §1.1 paths (i) and (ii). Path (iii) (Betfair-unreachable fallback) leaves them null on the placeholder record; reconciliation populates them on promotion.

### 2.3 Operator-supplied parameters (staged at §3.1)

These fields come from the operator, not from market state. They are typically set during stage 1 (parameter staging) but can also be entered at placement-commit time if the operator skips staging.

- `stake` — the amount staked. AUD.
- `bet_side` — back | lay (Betfair exchange only; soft-book is back-only).
- `intended_strategy` — Strategy 1 | Strategy 2 | Strategy 3 | Strategy 4 | Other. Decision-context: which strategy the operator was running when they placed this bet. Used in analytical reads to filter bet history by strategy.
- `funding_source` — cash | free-bet-pool. Indicates whether the bet drew from the account-at-book's cash balance or from the pooled free bet balance. FIFO consumption logic applies when `funding_source = free-bet-pool`; consumption events are written to the free bet ledger per §7.3.
- `operator_notes` — free text. Optional. Captured immutably with the rest of the record.

`promo_cycle_id` (§2.1) is also operator-staged via the promo picker on the staging surface (operator picks the named promo, v3 resolves to the cycle ID). Promo specifics — promo type, placings covered, cap value, qualifying odds floor, refund mechanism, free-bet generation rules — live on the cycle record per §7.1, not on the bet record. The bet record only carries the cycle reference.

### 2.4 At-placement market snapshot

The state of the market at the moment of placement-commit. Per DR-026, this is the inline snapshot exception — these fields are stored on the bet record despite being derivable elsewhere, because the moment-of-placement state is the decision context and the analytical line cannot reconstruct sub-second precision retrospectively.

Three snapshot sources, distinguished by which placement path the bet came through:

- `snapshot_source = operational` — Betfair exchange bets via `betfair_client` operational read at click time. Path (i) live placement.
- `snapshot_source = typed` — soft-book bets (racing or sports) where the operator types the price taken at the soft book. Path (i) live placement, soft-book bet types.
- `snapshot_source = retrospective` — bets logged after the event (path ii), where Betfair-side state is queried from historical Betfair data via `listMarketCatalogue` / `listMarketBook`.

Common snapshot fields:

- `placement_time` — the moment of placement. Operator-typed for retrospective entries; v3-generated for live entries.
- `logged_time` — the moment the record was written to v3. Differs from `placement_time` only on retrospective entries.
- `price_taken` — the price at which the bet was placed. Operational source for Betfair exchange; operator-typed for soft-book; reconstructed from historical Betfair data for retrospective entries (with the caveat that retrospective price reconstruction is approximate to the closest-data-point Betfair retains).
- `snapshot_timestamp` — the timestamp of the snapshot itself, which may differ slightly from `placement_time` on operational reads (the snapshot reflects market state as-of its own timestamp, not as-of placement_time).

Type-specific snapshot fields (best back/lay, total matched, virtual ladder, soft-book reference Betfair price) are layered on per §4, §5, §6.

### 2.5 Settlement state

Settlement fields are amendable via reconciliation events (per §8), not in-place edits. They start unpopulated at placement-commit and fill in as the bet's lifecycle progresses.

- `settlement_state` — pending | finalised | provisional | voided.
- `result` — won | lost | placed (each-way) | partial | void. Null until settlement.
- `payout` — gross payout in AUD. Null until settlement.
- `pnl` — net profit/loss in AUD. Null until settlement.
- `settlement_time` — when the bet was settled. Null until settlement.

Settlement source is Betfair-canonical for all bet types — the racing settlement path reads from Betfair via `betfair_client` (with public-archive fallback paths inside the settlement layer for cases where Betfair result data is incomplete or delayed); the sports settlement path is locked to Betfair-direct per §2.2 (with public-archive fallback at 90 minutes post scheduled fixture end). Operator-overrides on settled records (rare, e.g. Betfair settled wrong) flow through reconciliation events with audit trail per §8, not as a different settlement source value on the bet record.

### 2.6 Reconciliation metadata (path-iii records only)

Path-(iii) placeholder records carry bookkeeping fields that track their pending-resolution lifecycle. On normal records (path i and path ii), all three fields are null and operator-invisible.

- `placeholder_state` — `null` (normal record, identifiers populated) | `pending-betfair-resolution` (placeholder, awaiting identifier resolution) | `non-betfair-resolvable` (operator confirmed the bet has no Betfair counterpart, e.g. novelty market).
- `reconciliation_attempts` — count of identifier-resolution retries for placeholder records. Useful for spotting placeholders that have been retrying without success.
- `last_reconciliation_attempt` — timestamp of the most recent resolution attempt for placeholder records.

Operator-facing experience: a path-(iii) placeholder appears in the bet log with a "pending Betfair resolution" indicator. v3 retries identifier resolution on a schedule. On success, the placeholder is promoted — the indicator clears, the bet becomes fully analytical-line-resolvable. The operator can also manually trigger resolution from the placeholder record if Betfair becomes reachable and they want immediate promotion.

---

## 3. Bet-entry flow — staging vs commit

Bet entry is a two-stage flow, not a single moment. Stage 1 (parameter staging) lets the operator pre-set deterministic parameters while market-watching. Stage 2 (placement-commit) captures the at-placement snapshot, resolves Betfair identifiers, and fuses staged parameters with captured ones into the immutable bet record.

This emulates and extends v2's promo-field picker on the race menu: in v2 the operator sets the promo cycle before lodging the bet; in v3 the staging surface covers promo cycle, account-at-book, intended strategy, stake, sports line value, funding source, and any other deterministic parameter.

### 3.1 Stage 1 — parameter staging

The operator opens a staging surface (UI-side; v3 build proper) for a specific market/selection. The staging surface is bound to a `betfair_event_id` + `betfair_market_id` + `betfair_selection_id` triple identified up-front (so the staging surface itself is Betfair-canonical from the outset; staged parameters cannot drift onto a different selection by accident).

The operator sets staged parameters (see §2.3 for the field list). Staged parameters are held in v3 working memory only. They are not a record. If the operator abandons the staging surface (closes it, navigates away, the market suspends, etc.), the staged parameters are discarded with no record-side consequence. New cycle definitions that referenced a not-yet-created cycle are not created if the bet is not committed.

### 3.2 Operational walkthrough — promo cycles and free bets

The operator-facing surface uses human-readable names; v3 manages cycle and bet IDs internally. The operator never sees, picks, or remembers an ID.

**Scenario A — first bet of a new Strategy 1 cycle (insurance promo, e.g. Sportsbet 4-place insurance, $50 cap, this Saturday).**

1. Operator opens the staging surface for a selection on the racing page.
2. Account-at-book picker — defaults to most-recently-used, one click.
3. Strategy picker — defaults to most-recently-used, one click.
4. Promo picker — opens a small modal showing **active promos for this account-at-book** (v3 already knows what promos are running; the operator has seeded them in a separate setup screen at the start of the day or week). Operator picks "Sportsbet 4-place insurance $50."
5. v3 detects this is the first bet of a new cycle today — auto-creates a new cycle ID under the hood, attaches it to the bet. Operator does not see or manage the cycle ID.
6. Operator types stake, hits place.

~3-4 clicks plus stake.

**Scenario B — second bet of the same cycle (another insurance bet under the same promo).**

1. Staging surface for a different selection.
2. Account-at-book picker.
3. Strategy picker.
4. Promo picker — v3 detects the active cycle for this promo today and surfaces it as the **default** (top of the list, pre-selected). Operator confirms or clicks through.
5. Type stake, place.

Same number of clicks. Cycle ID is reused under the hood.

**Scenario C — bet drawing from free bet balance.**

1. Operator opens the staging surface.
2. Account picker, strategy picker, promo picker (or "no promo" for naked use of free bet balance).
3. Funding source toggle: cash | free-bet-pool. Toggling to free-bet-pool surfaces the account-at-book's pooled free bet balance (e.g. "$100 free bet available"). Operator confirms the toggle.
4. Operator types stake, picks selection, hits place.

v3 at commit walks the free bet ledger's FIFO queue for this account-at-book, generates one or more consumption events to cover the stake (full consumption of older generations first, partial consumption of the next generation as needed), and links each consumption event to the parent generation's cycle. The operator does not pick a free bet, does not pick a parent, does not see consumption events. Parent and cycle attribution is fully automatic.

The many-to-many free bet linkage (§7.3) means a single child bet can have multiple parent linkages (a $100 free bet drawing from two $50 generations = two consumption events, two parent cycles), and a single parent generation can be linked to multiple child bets across time (a $50 free bet split across five $10 child bets = five consumption events of $10 each). Both shapes are first-class on the ledger.

### 3.3 Stage 2 — placement-commit

The operator clicks "place bet". v3 executes the commit sequence:

1. **At-placement snapshot capture** — operational source for Betfair exchange via `betfair_client`; operator-typed for soft-book; market state is captured as-of click time.
2. **Betfair identifier resolution** — already known from staging (the staging surface was bound to a Betfair-canonical triple at stage 1).
3. **Cycle creation if needed** — if `promo_cycle_id` referenced a new-cycle definition staged in §3.1, the cycle record is written first (per §7.1); the bet record carries the now-real cycle ID.
4. **Free bet consumption events** — if `funding_source = free-bet-pool`, v3 walks the FIFO queue and writes one or more consumption events on the free bet ledger (per §7.3). Parent linkages are established automatically.
5. **Bet record write** — the immutable record per §2 + type-specific §4/§5/§6 fields.
6. **Bet placement at the actual book** — for Betfair exchange this is the `placeOrders` REST call per §2.4 §14; for soft-book this is the operator placing the bet at the soft book, with v3's record as the canonical accounting view.

Failure modes during commit:

- Step 1 fails (operational source unreachable for Betfair exchange): bet placement aborts; staged parameters are preserved on the staging surface; operator can retry. No record is written.
- Step 2 fails (identifier resolution fails despite staging — should not happen normally because identifiers were known at stage 1, but could happen if the market suspended between stage 1 and stage 2): bet placement aborts; staged parameters are preserved; operator can retry or abandon.
- Step 6 fails for Betfair exchange (`placeOrders` rejection per §2.4 §15): bet record and any cycle/consumption events written in steps 3–5 are rolled back; staged parameters preserved on the staging surface; operator sees the rejection reason.
- Step 6 fails for soft-book (operator could not place the bet at the soft book, e.g. price gone, account limited): bet record and any cycle/consumption events are rolled back via operator action; staged parameters preserved.

The staging surface is preserved across commit failures so the operator can adjust and retry without re-entering parameters.

### 3.4 Retrospective entry (path ii)

Retrospective entries use the same two-stage flow with two adjustments:

- `placement_time` is operator-typed at staging (when they actually placed the bet at the soft book, hours or days ago).
- The at-placement snapshot at step 1 is a retrospective Betfair read (`listMarketCatalogue` / `listMarketBook` over the historical market). `snapshot_source = retrospective`. The snapshot reflects Betfair's state at the closest-to-placement-time data point Betfair retains; this is necessarily approximate and that approximation is captured in the `snapshot_timestamp` field.

Settlement state is already known for retrospective entries because the event has resulted; settlement fields populate from Betfair at the same commit step rather than waiting for a settlement reconciliation pass.

If the retrospective entry is free-bet-funded, the parent-generation events must already exist on the ledger (the parent insurance bet or bonus-winnings bet was logged earlier). For retrospective entries where the parent itself is also being entered retrospectively, the parent must be entered first; v3's free bet ledger does not auto-create generations from missing parents.

### 3.5 Path (iii) — Betfair-unreachable placeholder

Path (iii) bypasses stage 2's identifier resolution. The operator stages parameters as normal; on commit, identifier-resolution fails (Betfair unreachable, historical query fails, etc.). v3 writes a placeholder record carrying:

- All operator-supplied staged parameters from §2.3.
- `placeholder_state = pending-betfair-resolution`.
- Betfair canonical identifier fields (§2.2) all null.
- `placement_time` and `logged_time` as normal.
- `snapshot_source = typed` (the operator's typed information is the only snapshot available at commit time).

If the placeholder is free-bet-funded, free bet consumption events are written at commit normally — the parent linkage does not depend on Betfair-side identifier resolution. The placeholder's pool draw is committed against the free bet ledger immediately.

A reconciliation job retries identifier resolution on a schedule per §8.3. On success, the placeholder is promoted: identifier fields populate, `placeholder_state` is cleared, `snapshot_source` flips to `operational` or `retrospective` per the resolution path.

Placeholders are operator-visible in the bet log with a clear "pending Betfair resolution" indicator. The operator can also manually trigger resolution from the placeholder record if Betfair becomes reachable and they want immediate promotion.

---

## 4. Betfair exchange bet records

Betfair exchange bets are placed direct against `betfair_client` via `placeOrders`. The bet record extends the §2 backbone with exchange-specific identity (the round-trip key linking v3's local in-flight record to Betfair's bet record), exchange-specific snapshot fields (best back / best lay / total matched at placement), and an order-state lifecycle that tracks the bet from EXECUTABLE through EXECUTION_COMPLETE.

### 4.1 Exchange-specific identity

Two Betfair-side identifiers participate in placement; only one is stored permanently on the bet record.

- `customer_order_ref` — v3-generated UUID per placement instruction. Sent on `placeOrders` inside the `PlaceInstruction`. Echoed by Betfair on the placement response and on every subsequent order-state read (`listCurrentOrders`, `listClearedOrders`, order-stream `rfo` field). The load-bearing round-trip key matching v3's local in-flight record to Betfair's bet record before `betId` is known. **Stored permanently on the bet record.** Per `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` §14.2.
- `betfair_bet_id` — Betfair's order identifier, returned on the `placeOrders` response (`instructionReports[0].betId`) on `SUCCESS` status. Linked to the bet record after the placement response arrives. **Stored permanently on the bet record.** This is the canonical Betfair-side identifier for the bet across its full lifecycle.

A third identifier exists in the placement layer but is not stored on the bet record:

- `customer_ref` — v3-generated 32-character string sent on `placeOrders` request top-level. Used by Betfair for de-duplication inside a 60-second window (per §2.4 §14.2). Does NOT persist into the placement response or order-stream messages. Held in transient working state on the in-flight record for the 60-second retry window, discarded thereafter. **Not stored on the bet record** — no read-time consumer post-window.

### 4.2 At-placement snapshot — type-specific fields

`snapshot_source = operational` for live placement (the standard path). The snapshot fields below extend the §2.4 common backbone.

- `betfair_best_back_at_placement` — best available back price at the moment of placement-commit, captured from `betfair_client`'s in-process cache.
- `betfair_best_back_size_at_placement` — size available at the best back price.
- `betfair_best_lay_at_placement` — best available lay price at the moment of placement-commit.
- `betfair_best_lay_size_at_placement` — size available at the best lay price.
- `betfair_total_matched_at_placement` — total matched volume on the market at placement time.

Field-set rationale: this is the floor snapshot locked by `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` §17.2. Per DR-019 (derived state on read), the bet record stores only what cannot be reconstructed at read time. The full 3-deep ladder view (top 3 back / top 3 lay with prices and sizes) is captured periodically on the analytical line via VPS scrape into `capture.db` and is reconstructable from there if any audit surface ever needs depth context. Full per-price traded ladder (`EX_LADDER` projection) is not currently captured anywhere — Betfair returns DSC-0018 (authorisation-level rejection) on the current API credential, per the Saturday API observation probe (Session 37). See §10.

### 4.3 Retrospective entry adjustments

Path (ii) retrospective entries on Betfair exchange use `snapshot_source = retrospective`. The snapshot fields above are reconstructed from Betfair historical market data via `listMarketCatalogue` / `listMarketBook` over the closed market. The reconstruction is approximate — Betfair retains snapshots at its own cadence, not at the operator's actual placement time — and that approximation is captured in `snapshot_timestamp` (the timestamp of the historical snapshot Betfair returned, which differs from `placement_time`).

`customer_order_ref` and `customer_ref` are not generated for retrospective entries — there is no live `placeOrders` call. `betfair_bet_id` is populated from the historical record where Betfair retains it and where a clean match against the operator-supplied bet details is possible; otherwise null with `snapshot_source = retrospective` indicating the bet record came through the historical-reconstruction path.

### 4.4 Path (iii) Betfair-unreachable placeholder

Per §3.5, path (iii) placeholders carry no Betfair-side identifiers at commit time. For Betfair exchange placeholders, this means `customer_order_ref`, `customer_ref`, and `betfair_bet_id` are all null on the placeholder record (alongside the §2.2 canonical identifier fields). The placeholder is operationally rare on Betfair exchange — `betfair_client` unreachability blocks live placement upstream of bet-record write, so a Betfair-exchange placeholder typically represents an offline-then-logged-later bet rather than a transient API failure.

On reconciliation success (per §3.5), the placeholder is promoted: the §2.2 Betfair canonical identifiers populate via reconciliation, but `customer_order_ref` and `betfair_bet_id` cannot be retroactively constructed (the placement was offline; Betfair has no record). The promoted record carries `snapshot_source = retrospective` and `betfair_bet_id` populated where historical match succeeds, null where it does not.

### 4.5 Order-state lifecycle

Betfair-exchange bet records carry an order-state field that tracks the bet through Betfair's matching states. Per §2.4 §7 (order-stream lifecycle):

- `betfair_order_state` — `EXECUTABLE` | `EXECUTION_COMPLETE` | `EXPIRED` | `CANCELLED` | `LAPSED`. Populated via order-stream messages and `listCurrentOrders` / `listClearedOrders` reads.
- `betfair_size_matched` — the matched portion of the bet's stake. Updates from order-stream `OCM` messages.
- `betfair_size_remaining` — the unmatched portion still EXECUTABLE.
- `betfair_average_price_matched` — the average price across matched portions, where partial matches occur at varying prices.

These four fields are amendable as the bet's order state evolves between placement and full match (or lapse, or cancel). They are not append-only in the way decision-context fields are; they reflect Betfair-side state and update as Betfair-side state changes. Per §2.5 (settlement state) and §8 (reconciliation events), once the bet reaches `EXECUTION_COMPLETE` or terminal lapse / cancel, the order-state fields are frozen at their final values and settlement state takes over.

### 4.6 Order-state-to-settlement handoff

The handoff between order-state and settlement happens at terminal order state:

- `betfair_order_state = EXECUTION_COMPLETE` plus `betfair_size_matched > 0` → bet is fully matched; settlement layer takes over per §2.5. `settlement_state` transitions from `pending` to `finalised` (or `provisional` per the auto-settlement decision logic) when the market settles.
- `betfair_order_state = LAPSED` (full lapse) → bet did not match. Per §2.5, `settlement_state = voided`, `result = void`, `payout = 0`, `pnl = -0` (or stake refund if applicable to the lapse type per the lapse-status-reason codes).
- `betfair_order_state = CANCELLED` (full cancel by operator or system) → same as LAPSED in settlement terms.
- `betfair_order_state = EXECUTABLE` with partial match at market settlement → the unmatched remainder lapses; the matched portion settles per the market outcome. `betfair_size_matched` reflects the partial; settlement layer writes `payout` / `pnl` against the matched portion only.

### 4.7 Failure modes captured on the bet record

Per §3.3, placement-commit failures roll back the bet record (no record persists on commit-time failure). Two post-commit failure modes are captured on the bet record itself:

- **Placement timeout requiring single-retry** (§2.4 §14.3) — the in-flight record holds `customer_order_ref` and `customer_ref` across the retry. The bet record persists in two flavours: (a) retry succeeded cleanly → record carries the original `customer_order_ref` and the retry-returned `betfair_bet_id`; (b) retry hit `DUPLICATE_TRANSACTION` → record carries the original `customer_order_ref` and the `betfair_bet_id` recovered from the post-retry `listCurrentOrders` lookup.
- **Second-timeout in-flight-uncertain** (§2.4 §14.3) — if both the original and the retry timeout, the in-flight record is preserved as `placement_state = uncertain` and surfaced to the operator. No bet record is written until manual reconciliation via `listCurrentOrders` / `listClearedOrders` resolves the actual state. If reconciliation finds the bet, a normal record is written with `placement_state = recovered-from-uncertain` flag; if no bet exists at Betfair, the in-flight record is discarded.

The `placement_state` field is not part of the immutable decision-context backbone — it is operational metadata describing how the record came to exist. Default value is `clean` for the standard path; alternate values are `recovered-from-uncertain` (per above) and `placeholder-promoted` (per §4.4 reconciliation promotion).

---

## 5. Soft-book racing bet records

Soft-book racing bets are placed at a soft bookmaker (Sportsbet, Ladbrokes, etc.) and logged into v3 by the operator. v3 has no live read of soft-book state — per `architecture.md` §B.2, v3 day-one carries no `softbook_client` module and no soft-book operational pricing surface. The bet record extends the §2 backbone with the operator-typed price as the primary at-placement field, soft-book identity, and a Betfair-side reference snapshot captured for EV-context.

### 5.1 Soft-book identity

A single field captures soft-book identity:

- `soft_book_id` — which bookmaker the bet was placed at. Enumerated against v3's bookmaker reference list (`sportsbet`, `ladbrokes`, `pointsbet`, `neds`, `unibet`, etc., per the operator's active book set).

No bookmaker-side bet reference is captured. The operational reality is that typing per-book bet receipt numbers on every placement is high friction across Strategy 1 volume; the field would be inconsistently populated and the future CSV-import-from-bookmaker-transactions feature (parked) can fuzzy-match on amount + timestamp + selection where it lands. If a future DR re-introduces a reconciliation hook, it adds backward-compatibly.

### 5.2 Operator-typed price

`snapshot_source = typed` for live placement. The primary at-placement field on a soft-book racing record is the operator-typed price — what the operator actually took at the soft book at the moment of placement.

- `price_taken` (per §2.4 common backbone) — the price the operator typed at log time. Operator-supplied; immutable post-commit.

The price taken is the load-bearing decision-context fact for soft-book bets. Settlement payout calculations, EV reconstruction, and per-book price-comparison analyses all anchor on this field.

### 5.3 Betfair-side reference snapshot

At placement-commit, v3 captures the Betfair-side market state for the same race / runner via `betfair_client`. This is not the price the operator took (that came from the soft book) — it is the Betfair operational price visible at the moment of placement, captured for EV-context.

Snapshot fields (extending the §2.4 backbone):

- `betfair_best_back_at_placement` — best available back price on the corresponding Betfair market at placement time.
- `betfair_best_back_size_at_placement` — size available at the best back price.
- `betfair_best_lay_at_placement` — best available lay price.
- `betfair_best_lay_size_at_placement` — size available at the best lay price.
- `betfair_total_matched_at_placement` — total matched volume on the Betfair market.
- `snapshot_timestamp` — the timestamp of the Betfair-side snapshot.

The Betfair-side snapshot is the same field set as §4.2 (Betfair exchange snapshot) — the difference is operational role, not field shape. On a Betfair-exchange record the snapshot is the bet's own decision context (the price taken came from this snapshot); on a soft-book record the snapshot is the EV-context-comparison reference (the price taken came from the soft book; the Betfair price is stored to anchor EV calculation against the canonical line).

EV-context use cases:

- **Strategy 1 (Safety Net)** — the Betfair-side snapshot at placement gives the canonical line for EV calculation on the racing page. The promo cycle's EV is computed from the soft-book price taken plus the Betfair-side reference plus the cycle's `promo_terms` block (per §7.1).
- **Strategy 2 (Price Booster)** — the soft-book price uplift is measurable as `price_taken - betfair_best_back_at_placement` (subject to commission adjustments). Per-book uplift analytics anchor on the Betfair-side reference.
- **Strategy 4 (Synthetic Each-Way)** — value identification needs both the soft-book PLACE price and the Betfair-side reference; the latter is captured here.

### 5.4 At-placement field set summary

A soft-book racing bet record at placement-commit carries the §2 backbone plus:

- `soft_book_id`
- `price_taken` (operator-typed)
- `betfair_best_back_at_placement`
- `betfair_best_back_size_at_placement`
- `betfair_best_lay_at_placement`
- `betfair_best_lay_size_at_placement`
- `betfair_total_matched_at_placement`

`snapshot_source = typed`. The Betfair canonical identifiers from §2.2 (`betfair_event_id`, `betfair_market_id`, `betfair_selection_id`, plus venue / sport / event-name) are populated at commit by `betfair_client` resolution against the soft-book bet's race / runner. This is the load-bearing implementation of Position A (strict Betfair-as-canonical-source) for soft-book bets.

### 5.5 Retrospective entry adjustments

Path (ii) retrospective entries on soft-book racing follow the §3.4 pattern. `snapshot_source = retrospective`. The Betfair-side snapshot fields reconstruct from `listMarketCatalogue` / `listMarketBook` historical reads at the closest-to-placement-time data point Betfair retains. `price_taken` is operator-typed at staging — the operator types what they actually took at the soft book, hours or days ago.

`placement_time` is operator-typed (when they actually placed the bet at the soft book); `logged_time` is now.

### 5.6 Path (iii) Betfair-unreachable placeholder

Per §3.5, if `betfair_client` is unreachable at log time, v3 writes a placeholder soft-book record carrying:

- `soft_book_id` and `price_taken` populated normally (operator-supplied; not Betfair-dependent).
- All §2.2 Betfair canonical identifier fields null.
- All §5.3 Betfair-side reference snapshot fields null.
- `placeholder_state = pending-betfair-resolution`.
- `snapshot_source = typed`.

Free-bet-funded placeholders write consumption events at commit normally per §3.5 — pool-draw is independent of Betfair-side reachability.

On reconciliation success, the placeholder is promoted: §2.2 identifiers populate via `betfair_client` resolution; §5.3 snapshot fields populate from `listMarketBook` historical read at the closest-to-`placement_time` data point Betfair retains. `snapshot_source` flips from `typed` to `retrospective` to honestly indicate the Betfair-side snapshot is reconstructed rather than captured at placement-commit.

If the placeholder cannot resolve (the soft-book bet is on a market Betfair does not carry — rare per §1.1), the operator is prompted to confirm `placeholder_state = non-betfair-resolvable`. The record persists indefinitely as non-Betfair-resolvable; analytical-line joins skip it.

### 5.7 Settlement state

Soft-book racing bets settle Betfair-canonical per §2.5: the racing settlement path reads from Betfair via `betfair_client` against the §2.2 Betfair canonical identifiers, with public-archive fallback inside the settlement layer for cases where Betfair result data is incomplete or delayed. Settlement payout calculations apply the operator's `price_taken` (not the Betfair-side reference price) — the soft book paid the operator at the typed price, and the bet's actual P&L is computed against it.

Per §2.5, settlement-time operator-overrides (rare; e.g. soft book settled wrong, or Betfair settled wrong while the soft book settled right) flow through reconciliation events with audit trail per §8 — not as a different settlement source value on the bet record.

---

## 6. Soft-book sports bet records

Soft-book sports bets are placed at a soft bookmaker on a sports market (Match, Line, or Total — per `architecture.md` §B.1.1) and logged into v3 by the operator. The bet record extends the §5 (soft-book racing) shape with operator-supplied data specific to handicap and total markets, plus the line-resolution-to-Betfair-market-id pattern locked in §B.1.2 of the architecture.

§6 inherits the §5 backbone unchanged — soft-book identity (`soft_book_id` only), operator-typed `price_taken`, Betfair-side reference snapshot for EV-context, retrospective entry path, path (iii) placeholder behaviour, and Betfair-canonical settlement. This section specifies only what extends or differs.

### 6.1 Market-type discriminator

Sports bet records carry a market-type field in addition to the §2.1 `bet_type = soft-book sports` discriminator:

- `sports_market_type` — `match` | `line` | `total`. Distinguishes the three core market types per `architecture.md` §B.1.1. Drives type-specific schema validation (line and total records require an operator-specified line value; match records do not).

Match markets are direct: operator picks a fixture, picks a market type (Match), picks a selection from the two priced rows (or three for soccer including the draw selection). Line and total markets carry additional operator-supplied data per §6.2.

### 6.2 Operator-specified line value (line and total markets only)

Handicap and total markets require an operator-supplied line value at placement-commit. Two fields capture this:

- `operator_line_value` — the unsigned line the operator typed. Numeric, single-decimal precision typical (e.g. `6.5`, `165.5`, `2.5`). Mandatory for `sports_market_type ∈ {line, total}`; null for match markets.
- `operator_line_side` — `favourite` | `underdog` | `over` | `under`. Captures which side of the line the operator took at placement-commit time. Mandatory for `sports_market_type ∈ {line, total}`; null for match markets.

`operator_line_side` is decision-context per DR-026 (inline snapshot exception on bet records). Captured at placement-commit, not re-derived at read time. Reasons:

- For handicap markets, the favourite-side is determined per `architecture.md` §B.1.3 from the head-to-head market price at placement-commit — the side with the shorter head-to-head price is the favourite, carrying the minus handicap. Head-to-head prices shift between placement and event-start; re-deriving the side at read time may draw the inference toward a different team than was true at click time.
- For total markets, the over/under side is unambiguous from the operator's row pick at click time, but storing it explicitly keeps the field shape uniform across line and total markets.
- For pick'em handicap markets (per §B.1.3 — both head-to-head sides priced near-flat at placement, line near zero), favourite-inference does not apply. The operator's row pick at click time populates `operator_line_side` directly; no special schema accommodation needed.

Together, `operator_line_value` and `operator_line_side` are the operator-readable display fields for the line. The Betfair-side `betfair_market_id` already encodes the same information implicitly (Betfair's market structure is one market per signed line variant — "AFL Carlton vs Collingwood -6.5" is a different `market_id` from "AFL Carlton vs Collingwood -7.5"); the explicit fields are denormalised for read-time display without requiring a Betfair lookup.

### 6.3 Line-resolution to Betfair market-id pattern

Per `architecture.md` §B.1.2 (line ladder pattern) and §B.1.3 (favourite inference), v3 resolves the operator's typed line value to a specific Betfair `market_id` at staging time, before placement-commit. The resolution sequence:

1. Operator picks fixture, picks market-type tab (Line or Total), types the unsigned line value.
2. v3 fetches Betfair's line-variant markets for the fixture via `betfair_client.list_markets(event_id)` filtered to the relevant market-type set.
3. v3 renders the 11-line ladder centred on the operator's typed value (per §B.1.2).
4. Operator picks a row; v3 captures the `betfair_market_id` of that row, the operator's typed value, and the resolved side (`operator_line_side` derived from §B.1.3 favourite-inference for handicap, or the row pick directly for total).
5. v3 stages the parameters per §3.1 with the Betfair-canonical triple (`event_id`, `market_id`, `selection_id`) bound up-front.

At placement-commit, the `betfair_market_id` is already known from staging — it's not re-resolved. The bet record's §2.2 `betfair_market_id` and the operator-readable `operator_line_value` / `operator_line_side` fields are written together.

Failure mode at staging — no Betfair market exists at the operator's typed line — is handled per `architecture.md` §B.1.2: the centred row renders as "no market", surrounding rows still populate where Betfair has variants. If no markets exist within ±5 of the typed line, the ladder shows an empty-state with a "show all available lines" escape hatch. v3 does not silently write a bet record without a matching `market_id` — staging cannot complete without a resolved row.

### 6.4 At-placement field set summary

A soft-book sports bet record at placement-commit carries the §2 backbone plus the §5 soft-book backbone plus:

- `sports_market_type` (`match` | `line` | `total`)
- `operator_line_value` (mandatory for line and total; null for match)
- `operator_line_side` (mandatory for line and total; null for match)

`snapshot_source = typed`. The Betfair canonical identifiers from §2.2 are populated at commit from the staging-time resolution per §6.3. The Betfair-side reference snapshot fields (best back / best lay / total matched / snapshot timestamp per §5.3) capture the operational price visible on the resolved Betfair market at placement-commit.

### 6.5 Retrospective entry adjustments

Path (ii) retrospective entries on soft-book sports follow §3.4 plus §5.5 with one extension. The operator-typed line value plus side must be operator-supplied at staging — there is no automated reconstruction of which line the operator took, because soft-book line offerings drift between placement and now. The operator types `operator_line_value` and picks `operator_line_side` explicitly at staging.

v3 then resolves the corresponding Betfair `market_id` against Betfair's historical markets via `listMarketCatalogue` over the closed fixture, matching on the typed line plus side. If a clean match resolves, the §2.2 canonical identifiers and the Betfair-side reference snapshot populate. If no clean match resolves (rare; the soft-book line was not carried by Betfair), the entry routes to the path (iii) placeholder per §6.6.

### 6.6 Path (iii) Betfair-unreachable placeholder

Path (iii) for soft-book sports follows §5.6 unchanged: `soft_book_id`, `price_taken`, `sports_market_type`, `operator_line_value`, `operator_line_side` populate at commit (operator-supplied; not Betfair-dependent); §2.2 Betfair canonical identifier fields and §5.3 reference snapshot fields are null; `placeholder_state = pending-betfair-resolution`; `snapshot_source = typed`.

Reconciliation promotion follows §5.6: §2.2 identifiers populate via `betfair_client` resolution against the staged line-and-side; reference snapshot populates from `listMarketBook` historical read; `snapshot_source` flips to `retrospective`. If reconciliation cannot resolve a Betfair market for the staged line-and-side (the line existed at the soft book but not at Betfair — possible for niche line variants), the operator confirms `placeholder_state = non-betfair-resolvable` and the record persists as such.

### 6.7 Settlement state

Sports auto-settlement is locked Betfair-direct per `architecture.md` §B.1.4, with public-archive fallback at 90 minutes post scheduled fixture end (AFLTables for AFL, equivalents for NRL and other sports). Settlement payout calculations apply the operator's `price_taken` (not the Betfair-side reference price) — same discipline as §5.7.

The three-state outcome model (`finalised` | `voided` | `provisional`) plus Burst-Review-confirmation pattern applies per §B.1.4. Settlement-time operator-overrides flow through reconciliation events with audit trail per §8 — same as racing.

---

## 7. Cycle record and free bet ledger specifications

The bet record (§2) carries a `promo_cycle_id` reference. The cycle record holds the promo's parameters. The free bet ledger is the parent-linkage primitive for free-bet-funded bets.

### 7.1 Cycle record

A cycle record represents one instance of a promo running for one account-at-book over a defined period. Cycle records are written at placement-commit when the operator stages a bet against a new cycle (§3.3 step 3). Subsequent bets under the same promo on the same day attach to the existing cycle.

Cycle record fields:

- `cycle_id` — v3-internal primary key. Operator-invisible.
- `account_at_book_id` — which account-at-book this cycle runs for.
- `promo_name` — operator-facing display name (e.g. "Sportsbet 4-place insurance $50").
- `promo_type` — insurance | bonus-winnings | boosted-odds | cashback | other. Discriminator for promo-type-specific parameters.
- `promo_terms` — type-specific parameter block. For insurance: `placings_covered` (e.g. [2, 3, 4]), `cap_value` (e.g. $50), `qualifying_odds_floor` (e.g. 2.0), `refund_mechanism` (free-bet | cash). For bonus-winnings: `winnings_multiplier` (e.g. 1.0 = 100%), `cap_value`, `qualifying_odds_floor`, `bonus_mechanism` (free-bet | cash). For boosted-odds: `boost_amount` (per-leg or per-bet). For cashback: `cashback_percentage`, `cap_value`, `trigger_condition`. The block is structured so the promo EV calculation on the racing page can read every parameter it needs.
- `cycle_period` — start time, end time. Defines the window during which bets attach to this cycle.
- `created_time` — when the cycle was created at first-bet-of-cycle commit.

Promo EV calculation on the racing page (load-bearing per the operator's strategic decision-making) reads the cycle's `promo_terms` block plus the live Betfair operational price plus the operator-supplied stake, and computes expected value. The cycle's parameter block must be complete enough for this to work for any in-scope promo type — the type-specific discriminator and parameter sub-fields above cover Strategies 1 and 2 day-one. Strategies 3 and 4 cycle types can be added as `promo_terms` extensions backward-compatibly per §1.1 of the scope document (versioned contract, additive-only).

### 7.2 Free bet ledger — generation events

A generation event records one issuance of free bet credit to an account-at-book's pool, triggered by an upstream bet outcome.

Generation event fields:

- `generation_id` — v3-internal primary key.
- `account_at_book_id` — which account-at-book received the free bet.
- `source_bet_id` — the bet that triggered the free bet (the parent bet from the cycle that fired its trigger condition).
- `source_cycle_id` — the cycle the source bet belonged to. Cycle attribution flows to consumer bets through this field.
- `face_value` — the face value of the free bet at issuance. AUD.
- `remaining_balance` — the unspent portion of this generation. Mutable. Starts at face_value; decrements as consumption events draw from this generation.
- `generation_time` — when the free bet was issued.

A generation event's `remaining_balance` is the only mutable field on the free bet ledger; all other fields are immutable post-write. The pooled free bet balance for an account-at-book = sum of `remaining_balance` across all that account's generations.

### 7.3 Free bet ledger — consumption events

A consumption event records one drawdown from one generation by one consumer bet. Multiple consumption events can fire on a single placement commit (when the consumer's stake exceeds any single generation's remaining balance), and a single generation can have multiple consumption events across time.

Consumption event fields:

- `consumption_id` — v3-internal primary key.
- `consumer_bet_id` — the bet that drew from the pool.
- `source_generation_id` — the generation event drawn from.
- `consumed_amount` — how much was drawn from this generation by this consumer. AUD.
- `consumption_time` — when the consumption was committed.

The consumption event is the parent-linkage primitive. A consumer bet's parent linkages are exactly the set of consumption events with that bet as `consumer_bet_id`. The relationship is many-to-many in both directions:

- One generation → many consumption events (one full or many partial draws across time).
- One consumer bet → many consumption events (one placement drawing from multiple generations).

FIFO consumption logic at placement-commit: v3 sorts the account-at-book's generations by `generation_time` ascending, walks the list, and writes consumption events drawing from each generation's `remaining_balance` until the consumer's stake is fully covered. Each draw decrements the source generation's `remaining_balance`. Partial consumption is first-class — the last consumption event in a placement may draw less than its source generation's remaining balance, leaving residual balance for future consumers.

Cycle attribution at read time: a child bet's cycle membership is the set of cycles its consumption events resolve to via `source_generation_id → generation event → source_cycle_id`. Cycle-level P&L analysis (Strategy 1, Strategy 2 bonus-winnings) sums each cycle's share of each child bet's outcome proportional to consumed amounts.

### 7.4 Free bet ledger — operator-facing surface

The operator interacts with the ledger through two surfaces:

- **Free bet balance indicator** on staging surfaces — shows the pooled balance for the relevant account-at-book. Single number, e.g. "$100 free bet available."
- **Funding source toggle** on staging surfaces — cash | free-bet-pool. Toggling activates pool consumption at commit.

The operator never picks a generation, never sees consumption events, never picks a parent bet, never sees parent linkages. All bookkeeping is v3-internal. Cycle attribution is fully automatic.

Operator-facing exceptions are logged per §8 (reconciliation events) and surfaced in the bet log as audit-trail entries when the operator manually overrides automatic attribution (rare; e.g. a misallocated free bet that needs manual correction).

---

## 8. Read-time resolution paths

The bet record (§2 + §4 + §5 + §6) carries decision-context fields and Betfair canonical identifiers. Everything else needed for analytical reads — race detail, runner detail, finish position, market curve, BSP, field size, settlement payload, cycle membership, parent linkage, sports event metadata, sports result detail — resolves at read time per DR-019 (derived state on read). This section names the resolution path for each derivable field: which client, which join key, which fallback applies if the primary path returns nothing.

Two clients participate in read-time resolution:

- `vps_client` — reads against `capture.db` (the analytical-line database on the VPS, per DR-027). Carries periodic snapshots of Betfair API state, Racing API state, and soft-book scraper output. Backward-looking analytical reads anchor here.
- `betfair_client` — reads against the live Betfair API (operational line). Used for current-market reads where analytical-line coverage is insufficient or for historical reads via `listMarketCatalogue` / `listMarketBook` over closed markets within Betfair's retention window.

The default resolution path is `vps_client` against `capture.db`. `betfair_client` reads are reserved for cases where the analytical line does not carry the field or where a cross-check against Betfair canonical state is needed. Per DR-028 (cross-database integration boundary discipline), no caching, no denormalisation, no second integration point.

### 8.1 Race classification (racing bets)

Fields resolved: race type (thoroughbred | harness | greyhound), race-class metadata, prize money, race conditions, distance, surface.

- **Primary path:** `vps_client` reads `capture.db` Racing API tables, joining on `betfair_event_id` from §2.2. The Racing API record carries race type, class, prize money, distance, surface, conditions.
- **Fallback:** `betfair_client.list_market_catalogue` over the closed market — Betfair's catalogue carries event-level race detail at lower granularity (race type and event name reliably; class and prize money sometimes absent).
- **Failure mode:** if neither path returns the field, the bet record's display surface shows a "race classification unavailable" indicator on that field. Analytical queries filter such records out; the bet record itself remains valid and settled.

### 8.2 Runner metadata (racing bets)

Fields resolved: runner name, jockey, trainer, barrier, weight, age, sex, form summary.

- **Primary path:** `vps_client` reads `capture.db` Racing API runner tables, joining on `betfair_event_id` + `betfair_selection_id` from §2.2. Per-runner metadata captured at periodic Racing API scrape cadence (race-card cadence, not in-running).
- **Fallback:** `betfair_client.list_market_catalogue` with `MarketProjection.RUNNER_METADATA` returns runner names and selection IDs; jockey / trainer / barrier / weight are not on the Betfair surface and are Racing-API-only fields. Where the Racing API record is absent, runner name resolves from Betfair; the jockey / trainer / weight fields remain unresolvable for that bet.
- **Failure mode:** missing-runner-metadata indicator on the affected fields. Bet record remains valid.

### 8.3 Finish position (racing bets)

Fields resolved: finish position, beaten margin, sectional times where available.

- **Primary path:** `vps_client` reads `capture.db` Racing API result tables, joining on `betfair_event_id` + `betfair_selection_id`. Result data populates after the race completes; finish position and beaten margin are reliably present once the Racing API publishes results.
- **Fallback:** `betfair_client.list_market_book` with `MarketProjection.RUNNER_METADATA` over the settled market returns selection result via the `runners[].status` field (`WINNER` | `LOSER` | `REMOVED` | `PLACED` for each-way / place markets) but not the numeric finish position for losers. Where Racing API result is absent, win/lose binary resolves from Betfair; numeric position remains unresolvable.
- **Failure mode:** binary win/lose available; numeric finish position null for losers when Racing API path fails. Sectional times are always Racing-API-only and unresolvable from the Betfair fallback.

### 8.4 Market curve (racing bets and Betfair-exchange sports bets)

Fields resolved: pre-race / pre-event price movement on Betfair (best back time series, total matched time series, in-running price movement where applicable).

- **Primary path:** `vps_client` reads `capture.db` Betfair price-snapshot tables, joining on `betfair_event_id` + `betfair_market_id` + `betfair_selection_id`. Periodic capture cadence per the analytical-line scrape schedule (not sub-second; reconstruction of moment-of-placement market state is what `betfair_best_back_at_placement` and the rest of the §2.4 / §4.2 / §5.3 snapshot exists for, per DR-026).
- **Fallback:** Betfair Historical Data subscription where the operator has access; otherwise the curve is bounded by analytical-line capture cadence and gaps are present at sub-snapshot-interval resolution. The §2.4 placement snapshot fields cover the moment-of-placement decision context; the analytical line covers periodic sampling around it.
- **Failure mode:** sub-cadence resolution unavailable; curve renders at the cadence the analytical line captured. Decision-context price for the bet itself comes from the inline snapshot (§2.4 / §4.2 / §5.3), not from this path.

### 8.5 BSP — Betfair Starting Price (racing bets)

Fields resolved: actual BSP, near-jump SP projection, far-jump SP projection.

- **Primary path:** `vps_client` reads `capture.db` Betfair SP-snapshot tables, joining on `betfair_event_id` + `betfair_market_id` + `betfair_selection_id`. SP capture cadence per the §2.1 surgical-fix arc (sp_near and sp_far populating reliably at INTENSIVE / STANDARD cadence post the Sessions 36–37 fix per the §2.1 fix report).
- **Fallback:** `betfair_client.list_market_book` with `priceProjection=SP_AVAILABLE` over the closed market — returns `r.sp.actual_sp`, `r.sp.near_sp`, `r.sp.far_sp` where Betfair populates them. Per the Saturday API observation probe (Session 37), `actual_sp` is empirically not surfaced on closed AU thoroughbred WIN markets on the current credential; the entitlement question is carried forward as the EX_LADDER / SP-actual entitlement question per §10.
- **Failure mode:** where neither analytical nor live-API path returns BSP, the field is null on read.

### 8.6 Field size (racing bets)

Fields resolved: number of runners at jump (`active_runner_count`), number of withdrawals (`withdrawn_runner_count`).

- **Primary path:** `vps_client` reads `capture.db` Racing API runner tables filtered to the bet's `betfair_event_id`, counting `active` runners as of race-start time.
- **Fallback:** `betfair_client.list_market_catalogue` with `MarketProjection.RUNNER_METADATA` returns the runner list with status (`ACTIVE` | `REMOVED`); count from the live API.
- **Failure mode:** field size unavailable; analytical queries filtering by field size skip the bet. Bet record remains valid.

### 8.7 Settlement payout detail

Fields resolved: settlement payload from Betfair (commission applied, gross winnings, net payout components, voided portions, Rule 4 deductions where applicable).

- **Primary path:** the `payout` and `pnl` fields on the bet record (§2.5) carry the post-deduction realised values written at settlement. These are the load-bearing facts for accounting and EV reconstruction.
- **Auxiliary path (decomposition):** `vps_client` reads `capture.db` Betfair settlement-event tables, joining on `betfair_market_id` + `betfair_selection_id`. Where capture.db has captured the settlement event, the gross-vs-net decomposition (Betfair commission rate at settlement, Rule 4 deduction percentage, voided components) is available for analytical reconstruction.
- **Note on Rule 4 and commission:** Rule 4 deductions and Betfair commission rates are captured implicitly via the `payout` and `pnl` fields — Betfair's settlement payload applies them before returning the realised amounts. Decomposing into pre-deduction-vs-post-deduction is an analytical concern, not a bet-record-side capture concern. Per cheap-to-capture / expensive-to-reconstruct: the gross/net split lives in `capture.db`'s settlement event capture (analytical line) where available; reconstructing from a missing capture would require Betfair historical data and operator-typed commission rates per account, which is the expensive-side scenario. A `rule_4_affected` boolean on the bet record (derived at read time from the settlement event) is the analytical-side signal worth naming, not stored on the bet record.
- **Failure mode:** decomposition unavailable; `payout` and `pnl` remain reliable as the realised facts. Analytical queries needing pre-deduction reconstruction skip the bet where capture.db's settlement event is absent.

### 8.8 Cycle attribution

Fields resolved: cycle membership for the bet (which cycle, which promo, which promo terms).

- **Primary path:** join from the bet record's `promo_cycle_id` (§2.1) to the cycle record (§7.1). Cycle record holds `promo_name`, `promo_type`, `promo_terms`, `cycle_period`, `created_time`. All cycle-membership reads anchor here.
- **Failure mode:** `promo_cycle_id = null` indicates a non-promo bet (e.g. Strategy 4 Synthetic Each-Way value bet); cycle attribution is correctly absent. Where `promo_cycle_id` references a cycle ID that does not resolve, the bet record is in an invalid state and surfaces in the data integrity layer (DISC equivalent in v3) for operator review. This should not happen in normal operation — cycle records are written before the bet record per §3.3 step 3.

### 8.9 Parent linkage (free-bet-funded bets)

Fields resolved: parent generation events, parent cycles, consumed amounts per generation, parent bet (the source bet that triggered each parent generation).

- **Primary path:** join from the bet record's `bet_id` to the free bet ledger consumption events (§7.3) where `consumer_bet_id = bet_id`. Each consumption event carries `source_generation_id` linking to a generation event (§7.2); the generation event carries `source_cycle_id` linking to a parent cycle, and `source_bet_id` linking to the bet that triggered the generation.
- **Resolution shape:** many-to-many in both directions per §7.3. A child bet's parent linkages are the set of consumption events with that bet as `consumer_bet_id`; each consumption event resolves to one generation event, one parent cycle, and one parent bet. Cycle-level P&L analysis (Strategy 1 single-leg insurance cycles, Strategy 2 bonus-winnings cycles) sums each cycle's share of each child bet's outcome proportional to consumed amounts.
- **Failure mode:** for cash-funded bets, the bet record carries `funding_source = cash` and no consumption events resolve — parent linkage is correctly absent. For free-bet-funded bets where consumption events are absent, the bet record is invalid and surfaces in the data integrity layer. This should not happen in normal operation per §3.3 step 4.

### 8.10 Sports event metadata (soft-book sports bets)

Fields resolved: fixture detail, team / player names, kickoff time, venue, competition / season context.

- **Primary path:** `vps_client` reads `capture.db` Betfair event tables, joining on `betfair_event_id`. Event metadata captured at periodic Betfair API scrape cadence carries fixture name, kickoff time, competition, and venue.
- **Fallback:** `betfair_client.list_events` with the bet's `betfair_event_id` returns the canonical event record. Direct API read where the analytical-line capture is absent (rare; sports event capture cadence is daily-equivalent).
- **Failure mode:** event metadata unavailable; bet log displays Betfair canonical identifiers as fallback (the operator can navigate to Betfair via the `betfair_event_id` if needed).

### 8.11 Sports settlement detail (soft-book sports bets)

Fields resolved: fixture result (final score, period scores, overtime indicator), Betfair settlement payload, public-archive cross-check at 90-minute fallback per `architecture.md` §B.1.4.

- **Primary path:** `vps_client` reads `capture.db` Betfair settlement tables, joining on `betfair_market_id`. Settlement payload from Betfair carries selection-level outcome and the market's final state.
- **Fallback (operational):** `betfair_client.list_market_book` over the settled market returns the `runners[].status` per §8.3.
- **Fallback (public archive):** the 90-minute public-archive cross-check (AFLTables for AFL, equivalents for NRL and other sports) per `architecture.md` §B.1.4 lands as `provisional`-state settlement when Betfair settlement is delayed or absent. The cross-check source identifier is captured in the settlement reconciliation event (§9), not on the bet record.
- **Failure mode:** unsettled at 90 minutes with neither Betfair nor public-archive cross-check resolving routes to the operator-confirmation surface per §B.1.4. Bet record's settlement state remains `pending` until manual confirmation.

### 8.12 Resolution path summary

The §8 resolution paths above all anchor on Betfair canonical identifiers (`betfair_event_id`, `betfair_market_id`, `betfair_selection_id`) per §2.2 — the load-bearing implementation of the Session 42 architectural extension. No fuzzy-matching, no name-based joins, no soft-book ID translation at read time. Per DR-027 and DR-028, the bet record's canonical identifiers are the integration boundary into the analytical layer; the analytical layer joins back on the same identifiers. The boundary is one integration point, no caching, no denormalisation.

The §2 inline snapshot (§2.4 / §4.2 / §5.3) and the bet-record-side `payout` / `pnl` fields together cover everything that cannot be reliably reconstructed at read time. The §8 derived fields cover everything that can. The line between them is the cheap-to-capture / expensive-to-reconstruct principle applied per field.

---

## 9. Amendment discipline and reconciliation events

Operational reality across v2 was that any field captured at any stage might need amending later — odds typed wrong, bookmaker logged incorrectly, promo cycle attached to the wrong promo, account-at-book selected in error, stake mistyped, settlement state corrected after the fact. v3 acknowledges this directly: **every field on every record (bet record, cycle record, free bet ledger entries) is amendable**, with the reconciliation event log as the universal audit-trail primitive and explicit cascade rules so amendments flow through to dependent derivations correctly.

### 9.1 Amendment principle

Amendments happen via reconciliation events, not via in-place edits. Three properties hold:

- **Audit trail is preserved.** The original value is never lost. The reconciliation event log carries the full history of every amendment (who, when, what changed, why).
- **Cascade rules fire automatically.** Amendments to fields with downstream computational consequences (settlement amounts, free bet pool state, cycle attribution) trigger automatic re-derivation of the affected dependent state. Per §9.4 below.
- **Read-time consumers see the current value.** The bet record exposes the current (post-amendment) value of each field at read time; the reconciliation event log is the audit history, not the live state.

The bet record's stored fields are mutable in the sense that amendments can rewrite them. They are not append-only in a strict schema sense — but in normal operation, decision-context fields (price taken, stake, account-at-book, promo cycle, soft-book identity, sports line value/side) are not expected to change. Amendment is the exception, not the regular write path. The reconciliation event log surfaces the rate of amendments per field as an operator-visible signal — high amendment rates on a particular field indicate either an upstream UI issue or an operational pattern worth understanding.

### 9.2 Reconciliation event schema

A reconciliation event records one amendment to one record's one field.

Reconciliation event fields:

- `reconciliation_id` — v3-internal primary key.
- `event_type` — `bet-amendment` | `cycle-amendment` | `generation-amendment` | `consumption-amendment` | `settlement-correction` | `placeholder-promotion` | `placement-state-recovery` | `cascade-derived`. Discriminator naming what kind of amendment this is. `cascade-derived` flags reconciliation events that fired automatically as cascade consequences of another amendment per §9.4 (rather than direct operator action).
- `target_record_type` — `bet` | `cycle` | `generation` | `consumption`. Which record type was amended.
- `target_record_id` — the primary key of the amended record (e.g. `bet_id`, `cycle_id`, `generation_id`, `consumption_id`).
- `amended_field` — the name of the field amended.
- `old_value` — the value before amendment (serialised as text for audit purposes). Null where the field was previously unset.
- `new_value` — the value after amendment (serialised as text). Null where the amendment is a deletion.
- `reason` — operator-supplied free text describing why the amendment was made. Mandatory for operator-initiated amendments; auto-populated as `cascade from <parent reconciliation_id>` for cascade-derived events.
- `parent_reconciliation_id` — for `cascade-derived` events, references the reconciliation event that triggered this cascade. Null for direct operator-initiated amendments.
- `operator_initiated` — boolean. True for direct operator action; false for cascade-derived events and for system-initiated reconciliations (placeholder promotion, settlement-state automatic transitions).
- `audit_timestamp` — when the amendment was committed.

The reconciliation event log is append-only. Reconciliation events themselves are not amendable — corrections to a wrongly-applied amendment are made via a fresh reconciliation event reversing the prior change.

### 9.3 What gets a reconciliation event

Every change to a stored field on any of the four record types (bet, cycle, generation, consumption) generates a reconciliation event. This includes:

- Operator-initiated amendments to bet record fields (decision-context, settlement state, identity, identifiers).
- Operator-initiated amendments to cycle record fields (promo terms, period, name).
- Operator-initiated amendments to generation event fields (face value, source attribution).
- Operator-initiated amendments to consumption event fields (consumed amount, source generation).
- System-initiated settlement state transitions (`pending` → `provisional`, `provisional` → `finalised`, etc.) where settlement values are written or revised.
- Path-(iii) placeholder promotions (the transition from null Betfair-canonical identifiers to populated identifiers, and any associated `placeholder_state` and `snapshot_source` flips).
- Placement-state recovery transitions (path-(iii) placeholder promotion, `recovered-from-uncertain` flag setting per §4.7).
- Cascade-derived amendments triggered by §9.4 cascade rules.

The free bet ledger's `remaining_balance` field on generation events is the one mutable field on the ledger per §7.2. Each decrement of `remaining_balance` from a consumption-event write is itself a reconciliation event (`event_type = generation-amendment`, `cascade-derived`, parent is the consumption-event write or the consumption amendment that caused the rebalance). This keeps the ledger's mutable state fully audited without making `remaining_balance` a special case.

### 9.4 Cascade rules — flow-through for dependent derivations

Amendments to fields with downstream computational consequences fire cascade reconciliation events automatically. The rules below name the cascades explicitly — when an operator (or the system) amends a field on the left, the events on the right fire in sequence, each generating its own `cascade-derived` reconciliation event linked back to the originating amendment via `parent_reconciliation_id`.

**Bet record `price_taken` amendment** →
- Recalculate `payout` and `pnl` from the new price plus the existing settlement state (write `cascade-derived` reconciliation events on the bet record's settlement fields).
- If this bet triggered a free bet generation (i.e. a generation event exists with `source_bet_id = this bet_id`), recalculate the generation's `face_value` from the new price plus the cycle's `promo_terms` (cascade-derived `generation-amendment`).
- Generation `face_value` change does not automatically rewrite consumption events — `consumed_amount` is operator-committed at consumption time and remains valid. But if the new `face_value` is lower than the sum of consumption events drawn from this generation, the reconciliation surfaces an over-consumption flag for operator review (the cascade does not silently delete consumption events; the operator decides whether to amend specific consumptions).

**Bet record `stake` amendment** →
- Recalculate `payout` and `pnl` (cascade-derived settlement amendments).
- If `funding_source = free-bet-pool`, recalculate the consumption events for this bet — if new stake > old, write additional consumption events drawing from the FIFO queue (cascade-derived `consumption-amendment` writes). If new stake < old, partially reverse consumption events (cascade-derived consumption amendments reducing `consumed_amount` and incrementing `remaining_balance` on the source generations).
- If this bet triggered a generation event, recalculate generation `face_value` per the cycle's `promo_terms` (cascade-derived).

**Bet record `account_at_book_id` amendment** →
- Reverse all consumption events on the old account's pool (cascade-derived consumption amendments writing `consumed_amount = 0` and incrementing `remaining_balance` on the old account's source generations).
- Write fresh consumption events on the new account's pool via the FIFO walk against the new account's generations (cascade-derived consumption-event writes).
- If this bet triggered a generation event, the generation's `account_at_book_id` is also amended (cascade-derived), and consumption events drawn from that generation by other child bets are unaffected (those consumption events stay on the pool that received the credit, regardless of the source bet's new account attribution).
- If a settlement event has fired, the settlement transactions on the old account-at-book balance are reversed and rewritten on the new account-at-book balance (cascade-derived; balance-side bookkeeping is one integration point further down the operational data layer per the canonical balance-source convention).

**Bet record `bet_type` or `soft_book_id` amendment** →
- Bookmaker change implies account-at-book change (every account-at-book is bookmaker-specific). The cascade follows the `account_at_book_id` cascade above.
- Soft-book-specific fields (`price_taken` snapshot source, Betfair-side reference snapshot from §5.3) are unaffected — they remain captured at original placement-commit timing.

**Bet record `promo_cycle_id` amendment** →
- Cycle-level P&L recalculates for both the old and new cycles (cascade-derived; cycle-level P&L is derived at read time per §8.8 so this is automatic on next analytical read).
- If the amendment crosses promo types (e.g. insurance → bonus-winnings), generation-triggering rules differ. Any previously-triggered generation events from this bet are flagged for operator review — the cascade does not silently delete generation events because doing so would silently invalidate downstream consumption events that drew from those generations. The operator confirms whether to amend the generation events (via fresh reconciliation events) or accept the historical generations as standing.

**Bet record `betfair_event_id` / `betfair_market_id` / `betfair_selection_id` amendment** →
- Read-time resolution paths in §8 re-resolve against the new identifiers automatically (no stored field is affected; the bet record's stored canonical identifiers are the join key, and §8 derived fields refresh on next read).
- If the amendment changes the underlying race/event the bet was placed on, settlement state is invalidated — cascade-derived settlement amendments null out `result`, `payout`, `pnl`, and reset `settlement_state = pending` for the settlement layer to reprocess against the corrected identifiers.

**Settlement field amendments (`result`, `payout`, `pnl`, `settlement_state`, `settlement_time`)** →
- If this bet triggered a free bet generation under the old result, and the amended result no longer triggers (e.g. corrected from `placed` to `lost` on an insurance promo), the generation event is flagged for operator review — the cascade does not silently delete generation events for the same reason as the promo_cycle cascade above.
- If this bet did not trigger a generation under the old result, but does under the new result (e.g. corrected from `lost` to `placed`), the cascade surfaces a "missing generation" flag for operator review (the cascade does not silently create generation events because the operator is the source of truth for what the bookmaker actually issued).

**Cycle record `promo_terms` amendment** →
- Cycle-level P&L recalculates on next analytical read per §8.8.
- Generation-triggering rules for member bets are re-evaluated. Bets in the cycle that previously did/did not trigger generations under the old terms but should/should-not under the new terms surface flags for operator review.

**Generation event `face_value` amendment** →
- Existing consumption events drawn from this generation are unaffected (their `consumed_amount` is operator-committed). Over-consumption flag surfaces if `face_value` is lowered below the consumption sum.

**Consumption event amendments** →
- Source generation's `remaining_balance` recalculates via cascade-derived `generation-amendment` events.
- The consumer bet's `funding_source` and stake remain consistent — if a consumption is reversed entirely, the consumer bet's stake is no longer covered by the pool draw, and the reversal cascade either writes new consumption events from other generations (if pool balance allows) or surfaces an under-funded flag for operator review.

The cascade rules above are deterministic for the cases they cover. Where an amendment is ambiguous — would silently delete a downstream record, or implies a complex multi-record rewrite — the cascade surfaces a flag for operator review rather than auto-resolving. v3's data integrity layer (the v3 equivalent of v2's DISC) is responsible for surfacing these flags through to the operator.

### 9.5 Operator-facing surface

Operator-initiated amendments happen via the bet log's edit surface (UI-side; v3 build proper). The operator picks a record, picks a field, types the new value, types a reason. v3 writes the reconciliation event, fires the cascade, and surfaces any review flags from the cascade in the operator's flag queue.

The operator never composes a reconciliation event directly. The reconciliation event log is operator-readable as audit history — every record carries an "amendment history" view showing the full reconciliation event chain — but is not operator-writable.

System-initiated reconciliations (settlement transitions, placeholder promotions, cascade-derived events) happen automatically and surface in the bet log's amendment history without operator intervention.

### 9.6 What §9 does not cover

- **Free bet ledger consumption-event writes at placement-commit** are not reconciliation events. They are the primitive on the ledger per §7.3. Reconciliation events fire for *amendments* to consumption events, not for the original write.
- **Order-state lifecycle transitions on Betfair-exchange bets** (§4.5: `EXECUTABLE` → `EXECUTION_COMPLETE` etc., and the four amendable order-state fields) are tracked via the order-state field updates themselves, with the order-stream message being the source of truth. v3 does not generate a reconciliation event per order-state message — that would flood the log. The reconciliation event log fires once at order-state terminal transition, capturing the final state and any operator-initiated overrides thereafter.
- **Read-time derived fields** (§8) are not stored on the bet record and therefore have no reconciliation events. Amendments to upstream fields (Betfair canonical identifiers, settlement state) cascade through to the next read; the §8 fields refresh from the analytical line automatically.

---

## 10. What §2.8 closes for DR-029

§2.8 locks the bet-record contract for v3 across all three bet types (Betfair exchange, soft-book racing, soft-book sports), the cycle record, the free bet ledger (generation events + consumption events), the read-time resolution paths for derivable fields, and the amendment discipline (universal-amendable model with reconciliation event log + cascade rules).

### 10.1 What §2.8 unblocks

- **§2.9 (write-side bet-entry coherence)** — the bet record contract, staging-vs-commit flow (§3), and cascade rules (§9.4) are the load-bearing inputs §2.9 needs to specify atomicity guarantees, transaction boundaries, and the integrity-layer flagging surface. §2.9 is now writable.
- **§2.7 (API contract versioning)** — the bet-record shape, cycle-record shape, and free bet ledger shapes are the three contracts §2.7 versions across module boundaries (`vps_client`, `betfair_client`, the operational data layer). Bet-record-side §2.7 work is now writable.

### 10.2 What §2.8 lands as load-bearing contract

- **Session 42 architectural extension** — Betfair-as-canonical-source extending to all bet records lands here as load-bearing schema. §2.2, §4.1, §5.4, §6.3 implement it; §8 read-time resolution anchors on it. The pending architectural extension carry-forward from Session 42 is now a locked contract in §2.8 rather than a flagged future direction.
- **Universal-amendable model** — every field on every record (bet, cycle, generation, consumption) amendable via reconciliation events with cascade flow-through. Honest recognition of v2's operational reality: any field captured at any stage may need amending. The reconciliation event log is the universal audit-trail primitive.
- **Cheap-to-capture / expensive-to-reconstruct principle** applied per field — §2.4 / §4.2 / §5.3 inline snapshots and bet-record-side `payout` / `pnl` cover what cannot be reliably reconstructed at read time; §8 derived fields cover what can.

### 10.3 Carry-forward items (not gating)

These items are flagged but do not gate §2.8 close. They are post-§2.8 follow-through, sequenced ahead of v3 build proper but not blocking subsequent DR-029 sections.

- **EX_LADDER / SP-actual entitlement question.** Betfair returns DSC-0018 (authorisation-level rejection) on the current credential for `EX_LADDER` (full per-price traded ladder) and `actual_sp` is empirically not surfaced on closed AU thoroughbred WIN markets per the Saturday API observation probe. Entitlement-tier investigation is operator-side homework; possible DR depending on what tier access reveals. Not gating because the 3-deep periodic view captured by VPS scrape into `capture.db` is sufficient for currently-known audit needs (§4.2 lock).
- **Architecture.md §D12 sub-section update.** The Session 42 architectural extension is now load-bearing in §2.8, but the formal sub-section under `architecture.md` §D12 (Betfair as canonical source) has not yet been written to capture the schema-level commitment. Administrative cleanup; one-session edit at the appropriate post-DR-029 documentation pass.
- **Complete cascade map.** §9.4 names cascade rules for the fields where the cascade is well-understood (price_taken, stake, account_at_book_id, bet_type/soft_book_id, promo_cycle_id, Betfair canonical identifiers, settlement fields, cycle terms, generation face_value, consumption events). The complete map — every conceivable amendment path on every field on every record, with cascade behaviour and review-flag surfaces enumerated — is its own piece of work. Best done once v3 build is far enough along that the actual write paths exist to test the map against, rather than now from first principles. Parked as known follow-through; ties off post-DR-029 close before v3 build proper starts on bet entry.
- **CLV (closing line value) as analytical signal.** CLV is fully derivable at the analytical layer from the bet record's stored fields (Betfair canonical identifiers + `price_taken`) plus capture.db's BSP and pre-jump price-snapshot tables. It is not part of the operational read-time path v3 commits to in §2.8. Named here as a downstream analytical-layer signal that the operational data layer enables — built post-DR-029 alongside the wider analytical layer, not in v3 day-one.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — operational design downstream of v3 build proper. Not part of the bet-record contract.

### 10.4 What §2.8 does not do

§2.8 is the bet-record contract specification. It does not specify:

- **Consumer-side UI.** Bet-entry form layouts, retrospective-entry workflow specifics, placeholder-indicator visual design, free-bet balance UI representation, amendment-history audit-view display — all UI-side work downstream of v3 build proper.
- **Soft-book operational layer.** Per §3.11 of the scope document, deferred to a future DR. v3 day-one carries no `softbook_client` and no live soft-book pricing surface. §5 / §6 specify how soft-book bets are recorded; not how soft-book operational state is captured.
- **Atomicity / transaction boundaries on the cascade.** §9.4 specifies cascade behaviour; §2.9 specifies how the cascade is implemented atomically across the multi-record write paths.
- **Settlement source priority and 90-minute fallback machinery.** Per `architecture.md` §B.1.4. §2.5 / §5.7 / §6.7 reference it; the implementation lives in the settlement layer.
