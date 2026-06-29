# W4 brief — Betfair hedge-entry workflow (v1)

**Status:** drafting (Session 91 onward).
**Workstream:** W4 (bet entry + write surfaces, Betfair-side orchestration).
**Recipient:** Claude Code, single bounded session.
**Brief location:** `dr029/w4_bet_entry/w4_bet_entry_brief.md`.
**Substrate:** math review §1–§7 (1942 lines, locked at
`dr029/w4_bet_entry/hedge_staking_math.md`); DR-032 schema
commitment (110 lines, locked at `decisions.md` line 1081);
`architecture.md` §A.10 (22 lines, the architectural-principle home
that DR-032 cites).
**Drafting state:** sections §1 (scope) and §2 (module shape) drafted
Session 91. Remaining sections drafted Session 92 onward.

---

## §1 — Scope

### §1.1 — What this brief is

This brief commissions Code to build the **Betfair hedge-entry
workflow** for v3 — the engine that sits behind BetHub's hedge-entry
modal and orchestrates: pre-flight checks against current Betfair
state, hedge-stake calculation, Betfair API order placement, bet
record assembly per DR-032 (the canonical-reference-layer-for-all-
bet-records decision), and per-order reconciliation against
post-`placeOrders` matching activity.

The workflow ships as four modules at `workflow/bet_entry/v1/` per
DR-030 (the v3 repo layout decision — workflow/ is the orchestration
layer). Three of the four modules are pure (testable in isolation);
one is impure (BetfairClient reads, Betfair API order calls, bet
record writes).

W4 is the first v3 build workstream after the W0–W3 substrate work.
It is the workflow engine; W7 ships the modal UI that consumes it.

### §1.2 — What this brief is not

W4 v1 explicitly does **not** ship:

- **Modal UI rendering.** Per DR-030 module boundaries, UI is W7's
  territory. W4 specifies the data contract W7 consumes; W4 does not
  write Vue / React / template / styling code.
- **Modal mechanics behavioural spec** — math review §4 covers live-
  pricing behaviour, price drift envelope, what happens when the
  modal sits open. Carried forward to W7 as locked-but-not-yet-
  shipped substrate.
- **Soft-book typed-price entry path (W4.1).** Separate brief,
  downstream. W4 v1 handles the Betfair-side hedge entry only; the
  soft-book bet log entry is invoked through W4's orchestrator but
  the soft-book entry path itself (the racing-screen → modal flow
  for the original soft-book bet) is W4.1 territory.
- **Burst review workflow (W7).** Sequenced behind W4.
- **Settlement worker (W5).** W4 leaves `realised_conversion_rate`
  NULL at logging; W5 populates at settlement.
- **Operational store schema build (W6).** W4 specifies the bet
  record / bet leg schema per DR-032 plus W4-specific operational
  fields, but the table creation, migration framework, and broader
  operational store schema live in W6.
- **Strategy 3 (SGM) implementation.** The `sgm_correlated`
  strategy tag is reserved in the enum but not populated by W4 v1.
  Multi-leg bet entry workflow surfaces in W4.1 / W7.
- **Manual free-bet ledger entry workflow.** Free bets from
  promotional / random / unsolicited sources need manual ledger
  entry; that workflow lives in W6+ / future workflow brief, not W4.
- **Multi-rung ladder hedge.** Future arc per math review §7.2.
- **Page-level Betfair balance threshold flag.** Dropped at scope
  simplification (Session 91); pre-flight checks live at modal level
  only.
- **Broader sync-based reconciliation safety net.** W4 ships per-
  order reconciliation only (5-second window post-`placeOrders`).
  Sync-based reconciliation across the whole bet history is W6
  territory.
- **Streaming subscription dependency for reconciliation.** If
  Betfair streaming subscription is available at W4-shipping time
  (W2/W3 dependency), W4's reconciliation pass uses it; if not,
  polling fallback. Brief specifies both paths; does not require
  streaming to ship W4.

### §1.3 — Strategy coverage in W4 v1

W4 v1 actively serves three of the four racing strategies:

- **Strategy 1 (safety net / insurance promos).** Bet record
  populated; hedging is rare in operational practice (per Session
  91 operator clarification — Strategy 1's EV comes from the refund
  cycle, hedging would forfeit it). Workflow handles the rare case
  cleanly.
- **Strategy 2 sub-shape (a) (price-uplift / top fluc / BOB).** Bet
  record populated; hedging meaningful (locks in the price-uplift
  edge as guaranteed profit).
- **Strategy 2 sub-shape (b) (bonus-winnings).** Two flavours, both
  served:
  - **Free-bet bonus-winnings** — `pricing.py` synthesises
    effective odds using free-bet conversion rate (default 65%).
  - **Cash bonus-winnings** — `pricing.py` synthesises effective
    odds using cash bonus rate (no conversion-rate input).
- **Strategy 4 (synthetic each-way / clean turnover with EV
  thesis).** Bet record populated; no hedge typically (Strategy 4
  is value-betting, not promo-extraction). Workflow tags the bet
  but the hedge path may be skipped depending on the bet shape.

Plus a **fifth bet class without a strategy tag**:

- **Account-health turnover (NULL `strategy_tag`).** Deliberate
  non-EV bets placed for account-pattern hygiene. Distinct from
  Strategy 4 (Strategy 4 has an EV thesis; account-health turnover
  does not). Bet record populated with `strategy_tag = NULL`.

**Strategy 3 (SGM correlated friction)** is reserved in the tag
enum but not populated by W4 v1. SGMs need multi-leg entry and
modal mechanics that ship in W4.1 / W7.

### §1.4 — Operational workflow that W4 supports

The operator's actual workflow that W4 sits inside (corrected
Session 91 against earlier misunderstanding):

1. Operator selects soft-book bet on the racing page, picks promo
   type, enters soft-book odds, waits for EV trigger.
2. EV triggers. Operator places the bet **at the soft book**
   (real-money exposure on the soft-book side happens here).
3. Operator opens the **Betfair hedge modal in BetHub**. Modal pre-
   populates from racing-page data. Modal calculates and surfaces
   hedge stake using current Betfair prices.
4. Operator confirms hedge → **Betfair API order placed** (real-
   money exposure on the exchange side happens here). Hedge bet
   record written automatically on API success (Trigger A) plus
   reconciliation pass (Trigger B) within 5 seconds.
5. **Log-bet screen comes up.** Operator enters details of what
   bet was actually placed at the soft book. Soft-book bet record
   logged in BetHub.

W4 v1 supplies the engine for steps 3, 4, and 5. The racing-page UI
(step 1) and the EV trigger surfacing (step 2) are out of W4 scope
(W7 / racing-page territory). The modal UI rendering across all
steps is W7. W4 is the workflow logic plus the data contract W7
consumes.

### §1.5 — Why this ordering matters

The ordering is **time-sensitive and operationally locked**: soft-
book bet placed before Betfair hedge; hedge placed before soft-book
log; soft-book log is record-keeping after both real-money positions
are closed. Failure semantics in §[error semantics, drafting
Session 92+] follow this ordering — financial-risk failures (paths
where the operator is exposed without a hedge) are weighted higher
than record-keeping failures (paths where both legs are real but
BetHub didn't log them).

---

## §2 — Module shape

### §2.1 — Four modules at `workflow/bet_entry/v1/`

W4 v1 ships exactly four modules. Module count and split are locked
Session 91 — Code does not introduce additional modules, does not
split any of the four into sub-modules, and does not merge into a
flatter shape.

| Module | Purity | Responsibility |
|---|---|---|
| `orchestrator.py` | impure | Workflow entry point. BetfairClient reads, Betfair API order calls, bet record writes, reconciliation pass. |
| `staking.py` | pure | Stake math: standard cash hedge, free-bet hedge (per math review §2), combined-stake math (per math review §3). |
| `pricing.py` | pure | Effective-odds synthesis. Two paths: free-bet bonus-winnings (uses conversion rate), cash bonus-winnings (uses cash bonus rate). |
| `record_builder.py` | pure | DR-032-compliant bet record + bet legs assembly. Single source of truth for "given entry-path inputs, build a valid bet record". |

The split rationale (each module has one clear responsibility):

- **`orchestrator.py` is the only module with side effects.** All
  Betfair I/O, all database writes, all API calls flow through here.
  Pure modules are called as functions; impure work is centralised.
  This makes `orchestrator.py` the right place for retry-with-
  backoff logic, reconciliation pass orchestration, and error-path
  routing.
- **`staking.py` and `pricing.py` are split despite both being
  math.** They answer different questions. Staking: "given the
  prices, how much do I stake?". Pricing: "given a soft-book promo,
  what's the effective odds I'm pricing the hedge against?". They
  consume different math review sections and have different inputs;
  splitting prevents accidental coupling.
- **`record_builder.py` is its own module** because DR-032's schema
  is the contract W4 implements. One module whose only job is "build
  a DR-032-compliant bet record + bet legs from entry-path inputs"
  is the cleanest implementation of that contract. Future readers go
  to one place to understand schema population.
- **No `commission.py`.** Dynamic commission lookup is W4 v1 scope
  (W4 ports v2's mechanism), but it's a thin lookup, not enough to
  justify its own module. Lives inside `staking.py` or
  `orchestrator.py` per Code's call.

### §2.2 — Module boundaries (what crosses, what doesn't)

- **Pure modules import only from the standard library, Pydantic,
  and other pure modules.** No I/O, no Betfair API, no database.
- **`orchestrator.py` imports from all three pure modules** plus the
  BetfairClient (W3), Betfair API surface, and the v3 operational
  store interface (W6 dependency — see §[dependencies, drafting
  Session 92+]).
- **No circular imports.** `staking.py`, `pricing.py`, and
  `record_builder.py` do not import from each other. Each is self-
  contained. Composition happens in `orchestrator.py`.
- **Pydantic models for cross-module data.** Inputs and outputs of
  pure-module functions are Pydantic v2 models per DR-031 (the v3
  tech stack decision — Python 3.12+, Pydantic v2). No tuples or
  dicts as cross-module data shapes.

### §2.3 — Return contract

`orchestrator.py` exposes three main entry-point functions, each
returning a Pydantic model:

- **`pre_flight_check(market_id, selection_id, proposed_stake) ->
  PreFlightResult`** — modal-open-time check. Returns market status
  (closed / suspended / open), proposed-stake fundedness against
  current Betfair balance, and any operator-actionable flags.
- **`place_hedge(...) -> HedgePlacementResult`** — places the
  Betfair hedge order. Returns the placement outcome (matched /
  partial / failed), the populated bet record, the reconciliation
  pass status, and operational error context if applicable.
- **`log_soft_book_bet(...) -> SoftBookLogResult`** — logs the
  soft-book bet record after both legs are placed. Returns the
  populated bet record and operational error context if applicable.

**Error handling pattern: result-type, not exceptions.** Operational
errors (Betfair API failures, market closed, insufficient funds,
write failures) flow through the result type with explicit error
fields (`error_path` ∈ {a, b, c, d}, `severity` ∈ {critical,
standard}, `recovery_options`, `error_detail`). Exceptions are
reserved for **programmer errors** — invalid input types, schema
violations, bugs. Caller code (W7) checks `result.success` and
renders accordingly; doesn't wrap in try/except for normal
operational paths.

This pattern carries the four-error-path framework (drafted Session
91, lands in §[error semantics, drafting Session 92+]) explicitly in
the return type rather than reconstructing it from exception classes
at the caller.

### §2.4 — Module file structure

```
workflow/
  bet_entry/
    v1/
      __init__.py
      orchestrator.py
      staking.py
      pricing.py
      record_builder.py
      models.py            # Pydantic models for cross-module data
      tests/
        __init__.py
        test_staking.py
        test_pricing.py
        test_record_builder.py
        test_orchestrator.py  # mocked Betfair API
```

`models.py` is a fifth file but not a fifth module — it's the
shared Pydantic model definitions used across the four modules.
This is conventional Python project structure; not a scope addition.

`tests/` follows W0's pytest scaffolding pattern. Test scope per
§[test coverage, drafting Session 92+] is unit-tests for pure
modules + mocked-orchestrator tests for the impure module. Real
Betfair test-account integration testing is operator-side acceptance
work after the brief lands.

---

## §3 — Contract substrate mapping

This section maps W4's bet record + bet legs schema against DR-032
(the canonical-reference-layer-for-all-bet-records decision). DR-032
locks the principle (Betfair-side identifiers as canonical join
keys; bet record + bet legs schema; immutable logging-time snapshots
on legs; entry-path inheritance from racing screens); §3 names the
W4-specific fields, their population sources, and their consumer
modules.

§3 is the contract `record_builder.py` implements. `staking.py` and
`pricing.py` consume parts of it for math; `orchestrator.py` owns
the assembly and the writes.

### §3.1 — Bet record schema (W4-relevant fields)

A bet record represents one bet as a unit of operational state. For
single-leg bets (most cases), the record carries the leg inline. For
multi-leg bets (SGM in W4.1+), the record carries summary fields and
the legs live in a separate `bet_legs` table joined by `bet_id`.

W4 v1 populates the following fields per DR-032:

**Identity and lineage:**

- `bet_id` — primary key, generated at logging time.
- `cycle_id` — links bets within a single analysis cycle (per
  standing analysis convention; see §3.6 below). Generated at logging
  time for the cycle's first bet; inherited by downstream legs.
- `entry_path` — `'racing_screen'` for W4 v1 (the only path W4
  serves). Reserved values for future paths (`'sports_screen'`,
  `'manual_log'`, `'free_bet_ledger'`) not populated by W4 v1.

**Strategy classification:**

- `strategy_tag` — closed enum + nullable. See §3.2 below.

**Promo / free-bet context:**

- `is_free_bet` — boolean. Inherited from racing-screen promo
  selection (Option 2, Round 9). Modal allows override.
- `free_bet_conversion_rate` — float; populated only when
  `is_free_bet = TRUE`. Default 65% (config-driven; see §3.3 below).
  Operator-overridable at modal.
- `realised_conversion_rate` — float; **left NULL by W4 at logging
  time.** W5 (settlement worker) populates at settlement based on
  whichever leg actually won (see §3.3 below).

**Stake and matching (see §3.4 for full semantics):**

- `requested_stake` — what the operator submitted.
- `matched_stake` — what actually matched at the exchange / book.
- `unmatched_stake` — what didn't match (lapsed at race start /
  market close).
- `matched_price` — the price at which the matched portion filled.
  For non-hedge bets, the requested price.
- `match_status` — five-value enum. See §3.4 below.

**Operational metadata:**

- `placed_at` — Adelaide local timestamp (ACST/ACDT) per DR-021
  (timestamp anchoring, Adelaide local time). Populated at logging
  time.
- `book_or_exchange` — `'betfair'` for hedge legs; soft-book name
  (e.g. `'sportsbet'`, `'ladbrokes'`) for soft-book legs. Closed
  enum; values defined in W6's operational store schema.
- `account_at_book_id` — foreign key to W6's account-at-book table
  per DR-022 (the account / book / account-at-book vocabulary
  decision).

**Settlement context (W5 territory; W4 leaves NULL at logging):**

- `settled_at`, `settlement_outcome`, `payout_amount`,
  `realised_conversion_rate` — all populated by W5 at settlement.
  W4's record-builder leaves these fields NULL.

W4 v1 does **not** define the table itself. Table creation,
constraints, indexes, and migration framework are W6 territory
(operational store schema build). W4 specifies the field-level
contract; W6 implements the storage layer.

### §3.2 — `strategy_tag` enum and inference

**Enum (closed, four values + nullable):**

- `safety_net` — Strategy 1 (insurance / refund promos).
- `price_booster` — Strategy 2 (top fluc, BOB, bonus winnings).
- `sgm_correlated` — Strategy 3 (SGM correlated friction).
  *Reserved; not populated by W4 v1.*
- `synthetic_each_way` — Strategy 4 (clean turnover with EV thesis).
- `NULL` — account-health turnover (deliberate non-EV bets placed
  for account-pattern hygiene; distinct from Strategy 4).

**Inference rules (racing-screen → modal, per Round 8):**

| Racing-screen promo selection | `strategy_tag` |
|---|---|
| Insurance | `safety_net` |
| Bonus-winnings (free-bet flavour) | `price_booster` |
| Bonus-winnings (cash flavour) | `price_booster` |
| Top fluc / BOB / price-uplift | `price_booster` |
| Synthetic each-way | `synthetic_each_way` |
| No promo selected | `NULL` |

**Modal override:** racing-screen inference is a default; operator
can change `strategy_tag` at the modal before confirming. Override is
a normal operation (no audit trail at v1).

**Tag set is closed.** `record_builder.py` validates that
`strategy_tag` is one of the four values or `NULL`. Any other value
is a programmer error (Pydantic raises). New strategies require a DR
amendment + enum extension; W4 does not silently accept new tags.

**Strategy 3 (`sgm_correlated`) handling:** the value exists in the
enum so the schema doesn't change when W4.1 / W7 ships SGM entry,
but W4 v1's `record_builder.py` raises if asked to build a record
with `strategy_tag = 'sgm_correlated'`. SGM bets need multi-leg
mechanics that W4 v1 doesn't ship.

### §3.3 — Free-bet field semantics

**`is_free_bet`** — boolean, inherited from racing-screen promo
selection (Option 2, Round 9). Modal allows override. Operator's
reasoning at Round 9: free-bet hedging is time-sensitive; parameters
must be locked before the modal opens; the racing-screen → modal
flow already inherits Betfair identifiers and `strategy_tag`, so
`is_free_bet` riding the same flow is consistent.

**`free_bet_conversion_rate`** — float; populated only when
`is_free_bet = TRUE`.

- **Default 65%.** Per math review §6.2 (66.99% realised at moderate
  odds, 83.56% at long odds; 65% is the conservative working
  default).
- **Default lives in a config constant**, not hardcoded into
  `staking.py` or `pricing.py`. Future tuning is a config edit.
- **Operator-overridable at modal.**
- **Stored on the bet record at logging time** — the rate used at
  the time of bet entry, immutable thereafter.

**Conversion rate consumed only by `pricing.py`'s free-bet bonus-
winnings path.** Walking the strategies (Round 9 / Round 10):

| Strategy / sub-shape | Uses `free_bet_conversion_rate`? |
|---|---|
| Strategy 1 (safety net) | No |
| Strategy 2(a) price-uplift | No |
| Strategy 2(b) free-bet bonus-winnings | **Yes** |
| Strategy 2(b) cash bonus-winnings | No |
| Strategy 4 (synthetic each-way) | No |
| Account-health turnover (NULL) | No |

**`realised_conversion_rate`** — float; left NULL by W4 at logging.
W5 populates at settlement. Calculation rule (Round 9, operator-
specified): based on **whichever leg actually won**, not theoretical
equalised outcome. Handles the Betfair-price-drift edge case where
the hedge stake doesn't precisely equalise outcomes and one leg pays
slightly more than the other.

W4's contribution to `realised_conversion_rate`: ensures the bet
record carries the fields W5 needs at settlement (`is_free_bet`,
`free_bet_conversion_rate`, leg-level matched stake / matched price)
to compute the realised rate. W5 reads these and writes
`realised_conversion_rate` back.

### §3.4 — Generalised stake fields and `match_status` enum

Per Round 15, every bet record carries the same five stake / match
fields, regardless of bet type. Schema uniformity (Option A) chosen
over hedge-only fields (Option B) per Round 15's rationale: DR-032
favours uniformity, soft-book bets can also partially match in
unusual cases, and analytical queries are simpler when the field set
is constant.

**Fields:**

- `requested_stake` — what the operator submitted at the modal
  (Betfair side) or what the operator entered as having staked at
  the soft-book log (soft-book side).
- `matched_stake` — what actually matched. For Betfair hedge bets,
  populated from `placeOrders` response + reconciliation pass. For
  soft-book bets, defaults equal to `requested_stake` unless operator
  notes a partial match at the log.
- `unmatched_stake` — `requested_stake - matched_stake`. Stored
  explicitly for analytical clarity (avoids derivation in queries).
- `matched_price` — the price at which the matched portion filled.
  For Betfair hedge bets, populated from `placeOrders` response. For
  soft-book bets, the operator-entered odds.
- `match_status` — five-value enum (see below).

**For non-hedge soft-book bets:** `requested_stake = matched_stake`
in the common case; `unmatched_stake = 0`; `match_status =
'final_full'`. The fields exist uniformly but degenerate cleanly.

**`match_status` five-value enum:**

| Value | Meaning |
|---|---|
| `final_full` | Order fully matched at requested or better price. Terminal state. |
| `final_partial` | Order partially matched; remainder lapsed at race start / market close. Terminal state. |
| `provisional` | Order placed; reconciliation pass not yet completed. Transient state, normally exists for ~5 seconds. |
| `provisional_pending` | Order partially matched; reconciliation pass completed but unmatched portion still pending in market. Rare; flagged for operator review. |
| `failed` | Order rejected by exchange; no matching occurred. Terminal state. |

**State transitions (W4-managed):**

- Trigger A (`placeOrders` API success) → write record with
  `match_status = 'provisional'`.
- Trigger B (reconciliation pass, ~5 seconds later) → update record
  to `'final_full'`, `'final_partial'`, or `'provisional_pending'`
  based on `listCurrentOrders` data.
- Trigger A (`placeOrders` API rejection — terminal error) → write
  record with `match_status = 'failed'` directly. No Trigger B.

Full reconciliation pass design lives in §6.

**DR-032 compatibility:** `match_status` and the generalised stake
fields fit within DR-032 as **operational state**, not principle
change. **No DR-032 amendment needed.** DR-032 locked the canonical
identifiers and the bet record + bet legs structure; the stake /
match field set is W4's contribution to the operational layer that
sits on top of DR-032's identity layer.

### §3.5 — Set B (immutable logging-time snapshot fields per leg)

Per DR-032 §2 / §4 + Round 7, each bet leg carries six immutable
logging-time snapshot fields. These are populated once at logging
time by `record_builder.py` and never refreshed. Their purpose is to
make bet display readable without ever joining to capture.db (per
DR-028, the cross-database integration boundary discipline decision
— no caching, no denormalisation, no second integration point).

**Set B fields (per leg):**

| Field | Source at logging | Purpose |
|---|---|---|
| `runner_name` | Betfair `marketCatalogue` / `runner.runnerName` | Human-readable runner identity (e.g. "Winx"). |
| `event_name` | Betfair `marketCatalogue` / `event.name` | Race / event name (e.g. "Race 5 Randwick"). |
| `venue_name` | Betfair `marketCatalogue` / `event.venue` (Betfair-canonical) | Venue (e.g. "Randwick"). |
| `market_name` | Betfair `marketCatalogue` / `marketName` | Market type (e.g. "WIN", "PLACE", specific SGM). |
| `scheduled_start_time` | Betfair `marketCatalogue` / `marketStartTime` | Race / event start time at logging. |
| `betfair_implied_probability` | `1 / Betfair_back_price` at logging | Per-leg Betfair-implied probability. |

**All six are immutable snapshots.** Never refreshed. Not cache.

**Rationale recap (Round 7):**

- `betfair_implied_probability` as snapshot vs derived: DR-019
  (derived state on read) wants derivation done at read, not at
  store, *unless* the derivation depends on time-of-logging context
  that won't be reproducible later. Betfair-implied probability at
  logging *is* time-of-logging context — the price moves;
  reconstructing it later means going to capture.db. Snapshot is
  correct.
- `scheduled_start_time` as snapshot: the time at logging matters
  for "did I bet 30 seconds before jump or 30 minutes before"
  analytics. The race could be rescheduled; the original scheduled
  time is the operationally relevant one.
- Six fields total (not fewer): Set B's purpose is to make bet
  display readable without ever joining to capture.db. Cutting the
  set down breaks that property.

**Population source: Betfair `marketCatalogue` API.** `orchestrator.
py` reads `marketCatalogue` once at modal open (already needed for
pricing display) and caches in-memory for the duration of the modal
session. `record_builder.py` reads from this in-memory cache when
assembling the bet record at confirm time. **No second Betfair API
call** for Set B population — DR-028's "no second integration point"
discipline.

### §3.6 — Cycle linkage (`cycle_id`)

Per the standing analysis convention (any bet whose outcome drives
downstream behaviour is analysed as a single cycle, never in
isolation), bets within a cycle share a `cycle_id`.

W4 v1's role in cycle linkage:

- **First bet of a cycle:** `record_builder.py` generates a fresh
  `cycle_id` at logging time. The hedge leg and soft-book leg of a
  Strategy 2 hedge entry share the same `cycle_id` (they're one
  cycle by definition — placed-together-as-a-pair).
- **Downstream bets in a cycle (free-bet trigger from prior bet):**
  inherited `cycle_id` from the triggering bet. **W4 v1 does not
  populate the inheritance** — the racing-screen → modal flow for
  free-bet hedging carries the parent `cycle_id` as input;
  `record_builder.py` reads it from the entry-path inputs.

**Source of inherited `cycle_id` at modal:** the racing screen knows
when a bet about to be placed is a free-bet trigger from a prior
cycle (Strategy 1's triggered free bet, Strategy 2(b)'s free-bet
payout running through its own cycle). The racing screen passes the
parent `cycle_id` into the modal as part of the entry-path inputs.
W4's contract: accept `parent_cycle_id` as an optional modal input;
when present, use it; when absent, generate fresh.

**Manual free-bet ledger** (Round 9 — out of W4 scope) is the future
path for cycle-linking unsolicited / promotional free bets. W4 v1
doesn't handle this; the racing-screen-driven path is the only entry
point W4 v1 supports.

### §3.7 — Field population summary by module

Quick reference for which module owns the population of which field
group:

| Field group | Populating module | Source |
|---|---|---|
| Identity (`bet_id`, `cycle_id`, `entry_path`) | `record_builder.py` | Generated / inherited at logging |
| Strategy (`strategy_tag`) | `record_builder.py` | Racing-screen inferred + modal override |
| Free-bet (`is_free_bet`, `free_bet_conversion_rate`) | `record_builder.py` | Racing-screen inferred + modal override |
| Stake / match (Betfair hedge leg) | `orchestrator.py` (passes data to `record_builder.py`) | `placeOrders` response + reconciliation pass |
| Stake / match (soft-book leg) | `orchestrator.py` (passes data to `record_builder.py`) | Operator entry at log-bet screen |
| `matched_price` (Betfair hedge leg) | `orchestrator.py` (passes data to `record_builder.py`) | `placeOrders` response |
| `match_status` | `orchestrator.py` (initially Trigger A, updated by Trigger B) | API responses |
| Set B (six fields per leg) | `record_builder.py` | Betfair `marketCatalogue` (in-memory at modal session) |
| `placed_at`, `book_or_exchange`, `account_at_book_id` | `record_builder.py` | Logging context (timestamp, modal context, account selection) |
| Settlement fields | None in W4 | W5 populates at settlement |

`staking.py` and `pricing.py` are **pure consumers** of bet record
inputs (they compute stake / effective odds and return values to
`orchestrator.py`); they do not populate fields directly.

### §3.8 — DR-032 compliance check

W4's schema implementation per §3.1–§3.7 satisfies DR-032's
principles:

- **Betfair-side identifiers as canonical join keys** — W4 records
  carry `betfair_market_id` and `betfair_selection_id` per leg
  (inherited from racing-screen entry path).
- **Bet record + bet legs schema** — W4 implements both. Single-leg
  bets carry the leg inline (`bet_legs` table has one row per leg).
- **Stake on bet record only** — `requested_stake`, `matched_stake`,
  `unmatched_stake` live on the bet record. Per-leg matched stake
  for hedge-leg + soft-book-leg pairing lives on the legs.
- **Immutable logging-time snapshots on legs** — Set B six fields
  per leg per §3.5.
- **Entry-path inheritance from racing screens** — `entry_path =
  'racing_screen'`; `strategy_tag`, `is_free_bet`,
  `free_bet_conversion_rate`, parent `cycle_id` (when present) all
  inherited from racing-screen → modal flow per §3.2 / §3.3 / §3.6.
- **Hard rule on Betfair-market availability** — W4 only logs bets
  where Betfair has the market. (Soft-book bets without a Betfair
  hedge market are rejected by the racing screen before reaching W4
  — out of W4 scope; racing-screen contract enforces this.)
- **Racing API joins via capture.db's resolution layer post-hoc** —
  W4 doesn't read Racing API. Any post-hoc Racing API joins (for
  analytics) happen in capture.db's resolution layer per DR-027
  (the two-database architecture decision); W4's bet records have
  the Betfair identifiers needed for those joins to work.



## §4 — Pre-flight checks

Pre-flight checks run at modal-open time before the operator confirms
the hedge. Their job is to surface conditions that would cause the
hedge to fail (or behave unexpectedly) so the operator can react
*before* committing real money to the exchange — not as automatic
prevention, but as informed-decision support.

§4 is scoped tighter than the initial substrate (Round 15
simplification): two checks at modal level only, no page-level
Betfair state-reading. The dropped page-level Betfair balance flag
is named in §1.2 (out of scope) and §12 (hard limits).

### §4.1 — Pre-flight check entry point

`orchestrator.py` exposes:

```python
def pre_flight_check(
    market_id: str,
    selection_id: int,
    proposed_stake: Decimal,
) -> PreFlightResult:
    ...
```

**Inputs:**

- `market_id` — Betfair `marketId` for the hedge market (passed in
  from the modal, inherited from the racing-screen entry path per
  DR-032's canonical-identifier flow).
- `selection_id` — Betfair `selectionId` for the runner being
  hedged. Same provenance.
- `proposed_stake` — the hedge stake `staking.py` has already
  calculated for this modal session, in Decimal.

**Output:** `PreFlightResult` Pydantic model carrying market status,
fundedness check, and operator-actionable flags (see §4.4).

**Call site:** the modal calls `pre_flight_check` once at modal-open
time, after `staking.py` has computed the proposed hedge stake from
the racing-page inputs and Betfair pricing. The result feeds modal
display state (W7 territory).

### §4.2 — Market status check

**What it checks:** whether the Betfair hedge market is currently
open for bet placement.

**Source data:** Betfair `marketBook` API response. `orchestrator.py`
already calls `marketBook` for live pricing display at modal open;
the market status is in the same response (`status` field). **No
second API call** for the market status check — DR-028's "no second
integration point" discipline.

**Statuses surfaced:**

| Betfair `status` | Pre-flight flag | Operator-facing message |
|---|---|---|
| `OPEN` | OK | (nothing surfaced; check passes silently) |
| `SUSPENDED` | Warn | "Market currently suspended — wait for resumption before placing." |
| `CLOSED` | Block | "Market closed — hedge cannot be placed." |
| `INACTIVE` | Block | "Market not active — hedge cannot be placed." |

**Block vs warn distinction:** `SUSPENDED` is transient (markets
suspend and resume during normal trading, particularly near jump);
operator may reasonably wait it out. `CLOSED` and `INACTIVE` are
terminal for the hedge attempt; operator needs to handle the soft-
book exposure manually.

**No system-side prevention.** Even on `block` status, `pre_flight_
check` returns the flag but does not block the hedge from being
attempted. Operator's choice. (The exchange will reject the order
at `placeOrders` time anyway — see §5 path (b) terminal-error
handling.)

### §4.3 — Proposed-stake fundedness check

**What it checks:** whether the operator's Betfair account has
enough cleared funds to cover the proposed hedge stake.

**Source data:** Betfair `getAccountFunds` API response. Read once
at modal open. Returns `availableToBetBalance` (the funds available
for new bets after open exposures).

**Comparison:** `proposed_stake <= availableToBetBalance` →
fundedness check passes. Otherwise it fails.

**Statuses surfaced:**

| Condition | Pre-flight flag | Operator-facing message |
|---|---|---|
| `proposed_stake <= availableToBetBalance` | OK | (nothing surfaced; check passes silently) |
| `proposed_stake > availableToBetBalance` | Block | "Insufficient Betfair funds for proposed hedge of $X. Available: $Y." |
| `getAccountFunds` API call fails | Warn | "Could not verify Betfair balance — fundedness unchecked." |

**Block-but-not-prevention:** same pattern as §4.2 — flag surfaced,
but no system-side prevention. The exchange will reject the order at
`placeOrders` time with an `INSUFFICIENT_FUNDS` terminal error
anyway.

**API failure handling:** if `getAccountFunds` errors, pre-flight
returns a `warn` flag rather than a `block`. Operator can choose to
proceed (the hedge attempt itself is the next opportunity to learn
fund state). Don't block the operator on a check that's itself
failing.

### §4.4 — `PreFlightResult` model shape

Pydantic v2 model per DR-031 (the v3 tech stack decision):

```python
class PreFlightFlag(BaseModel):
    severity: Literal["ok", "warn", "block"]
    code: str  # e.g. "MARKET_SUSPENDED", "INSUFFICIENT_FUNDS"
    message: str  # operator-facing display text
    detail: dict  # structured context (e.g. balance values)

class PreFlightResult(BaseModel):
    market_status: PreFlightFlag
    fundedness: PreFlightFlag
    overall_severity: Literal["ok", "warn", "block"]  # max of the two
    checked_at: datetime  # Adelaide local per DR-021
```

**`overall_severity`:** computed by `pre_flight_check` as the max
severity across the two checks (`block` > `warn` > `ok`). W7 uses
this to decide modal-level display state (e.g. confirm button
enabled / warning banner / block banner).

**`checked_at`:** Adelaide local timestamp (ACST/ACDT) per DR-021.
W7 may surface "checked X seconds ago" alongside the status.

**Detail dict examples:**

- Market status: `{"betfair_status": "SUSPENDED"}`.
- Fundedness OK: `{"available_balance": 1247.50, "proposed_stake":
  73.20}`.
- Fundedness fail: `{"available_balance": 50.00, "proposed_stake":
  73.20, "shortfall": 23.20}`.

### §4.5 — Out of scope at pre-flight (named explicitly)

To prevent drift during Code's session:

- **Page-level Betfair balance threshold flag.** Dropped at Round
  15 simplification. Pre-flight is modal-only; the racing page does
  not read Betfair state.
- **Soft-book account state.** W4 does not read soft-book account
  balance, promo eligibility, or limiting status at pre-flight. The
  soft-book bet has already been placed by the time the modal opens
  (per the §1.4 workflow).
- **Promo eligibility checks.** Whether the soft-book promo is
  actually active / eligible / triggered correctly is the operator's
  judgement at the racing page; W4 does not re-verify.
- **Cross-account checks.** W4 does not verify that the Betfair
  account selected at the modal matches any particular account-at-
  book pairing or persona. That's modal / W7 / W6 territory.
- **Stale-price check at pre-flight.** Stale-price detection is a
  modal-rendering concern (W7), not a pre-flight gate. The price
  data passed into `staking.py` for stake calculation is whatever
  the modal has at confirm time; staleness is surfaced visually by
  W7 per Round 11 (modal opens with last-known prices, stale
  flagged, 2-second configurable threshold).
- **Hedge-stake recalculation.** `pre_flight_check` does not
  recalculate the hedge stake — it takes the stake as input.
  Recalculation between modal-open and confirm is W7's UI behaviour
  (modal updates as prices move, per math review §4 carried to W7).

### §4.6 — Pre-flight is advisory, not gating

`pre_flight_check` returns flags; it does not prevent `place_hedge`
from being called. The operator (via W7) makes the decision based
on the flags. W7 may choose to disable the confirm button on
`block` severity, but that's a W7 UI choice, not a W4 enforcement.

**Why advisory:** §1.5's financial-risk-weighted error semantics
make the operator the strategic decision-maker. Pre-flight surfaces
information; operator decides. Same pattern as Round 11's stale-
price handling — flag, don't block.



## §5 — Error semantics

§5 specifies how W4 handles failures across the hedge-entry workflow.
The framework is **severity-weighted by financial risk**, not by
code-path complexity (Round 14 reframe). Failures where the operator
is exposed without a hedge are critical; failures where both legs
are placed but BetHub didn't log them cleanly are standard.

The four-error-path framework was locked Session 91 (Rounds 13 / 14
against the corrected workflow ordering from Round 13). §5 maps the
four paths to specific error sources, retry policies, surface
messages, and modal data preservation rules.

### §5.1 — The four error paths

Mapped to the §1.4 workflow ordering:

| Path | Workflow step | Failure | Severity |
|---|---|---|---|
| (a) | Step 3 prep — hedge stake calculation | `staking.py` / `pricing.py` returns error | **Critical** |
| (b) | Step 4 — Betfair API order placement | `placeOrders` API call fails | **Critical** |
| (c) | Step 4 success path — hedge log write | BetHub local DB write fails | Standard |
| (d) | Step 5 — soft-book log write | BetHub local DB write fails | Standard |

**Critical = operator has unhedged real-money exposure on the
soft-book side.** The soft-book bet was placed at step 2; until the
Betfair hedge confirms (step 4), the operator carries directional
risk. Paths (a) and (b) leave the operator in this state.

**Standard = both real-money positions are closed; record-keeping
failure only.** By the time paths (c) or (d) fire, both books have
matched the bets. The position is closed; only BetHub's local
journal is incomplete.

This split shapes everything below: critical paths surface
prominently, fail loud and fast (or retry tightly), and preserve
modal data indefinitely. Standard paths surface non-urgently,
retry quietly, and fall back to manual entry without operator
escalation.

### §5.2 — Path (a): hedge stake calculation failure

**When this fires:** `place_hedge` calls `staking.py` (or
`pricing.py` for Strategy 2 sub-shape (b)), and the pure-module
function returns an error result instead of a stake.

**Likely causes:**

- Invalid input shape (Betfair price missing, soft-book odds
  missing, conversion rate out of range).
- Math edge case (negative stake, division by zero, NaN result —
  protected against in pure-module logic but surfaced if encountered).
- Pricing path mis-routed (e.g. free-bet path called without
  `free_bet_conversion_rate` populated).

**Severity: critical.** Soft-book bet already placed at step 2; no
Betfair exposure yet. Operator is exposed.

**Retry policy: no retry.** Pure-module errors are deterministic; a
second call with the same inputs returns the same error. Fail loud
and fast.

**Surface message:**

> Soft-book bet placed at book; Betfair hedge calculation failed.
> You are exposed on the soft-book side.
>
> Recovery options:
> 1. Retry calculation (if input data is fixable from the modal).
> 2. Manually hedge through Betfair directly (using the
>    market / runner already loaded in the modal).
> 3. Accept the unhedged position.
>
> Error detail: [specific error code + message from staking.py /
> pricing.py].

**Modal data preservation:** modal preserves entry data
**indefinitely** until operator dismisses. Operator's decision —
retry, manual hedge, or accept exposure — depends on having the
modal context (market, runner, prices, soft-book bet detail).

**Logging:** `place_hedge` returns a `HedgePlacementResult` with
`success = False`, `error_path = 'a'`, `severity = 'critical'`,
`recovery_options = [...]`. No bet record written for the hedge
leg (the hedge didn't happen). The soft-book bet record is still
written by `log_soft_book_bet` in step 5 if the operator chooses to
log it.

### §5.3 — Path (b): Betfair API order placement failure

**When this fires:** `place_hedge` calls Betfair's `placeOrders`
API and the API call fails or returns a non-success status.

**Severity: critical.** Soft-book bet placed; Betfair order
rejected by exchange. Operator is exposed on the soft-book side.

**Sub-classification: retry-safe vs terminal.**

**Retry-safe errors** (transient, likely to succeed on retry):

| Error category | Source | Examples |
|---|---|---|
| Network transient | HTTP layer | Connection reset, DNS failure, timeout |
| Rate limit | Betfair `TOO_MANY_REQUESTS` | Brief throttle by exchange |
| Service busy | Betfair `SERVICE_BUSY` | Exchange-side temporary load |
| Server error | HTTP 5xx | Transient exchange-side fault |

**Terminal errors** (deterministic; retry will produce the same
failure):

| Error category | Source | Examples |
|---|---|---|
| Insufficient funds | Betfair `INSUFFICIENT_FUNDS` | Surfaced by §4.3 fundedness pre-flight, but exchange-side check is authoritative |
| Market state | Betfair `MARKET_NOT_OPEN_FOR_BETTING`, `EVENT_CLOSED`, `MARKET_SUSPENDED` | Market state changed between pre-flight and `placeOrders` |
| Invalid stake | Betfair `INVALID_BET_SIZE`, `BET_SIZE_TOO_LOW` | Stake below exchange minimum or above exposure limit |
| Account state | Betfair `INVALID_ACCOUNT_STATE`, `ACCOUNT_LOCKED` | Account-side issue requiring operator action outside W4 |

**Categorisation source:** the `betfair_client_contract.md` v1.0
already names retry-safe vs terminal categorisation for `placeOrders`.
W4 reads from that contract. If new error codes surface in
operational use that aren't in the contract, Code surfaces them as
findings rather than silently categorising.

**Retry policy (retry-safe errors only):**

- 3 attempts maximum.
- Exponential backoff: **50ms, 200ms, 500ms** between attempts.
- Retry runs synchronously inside `place_hedge`; modal blocks until
  retry completes or terminal-fails.
- After 3 retry-safe failures, escalate to fail-loud-fast (treat as
  if terminal).

**Retry policy (terminal errors):** no retry. Fail loud and fast.

**Surface message (terminal or retries-exhausted):**

> Betfair hedge failed: [specific exchange error]. You are exposed
> on the soft-book side.
>
> Recovery options:
> 1. Retry [shown only when manual retry is sensible — e.g. for
>    `MARKET_SUSPENDED` if it might resume].
> 2. Manually hedge through Betfair directly.
> 3. [Specific error-code-keyed action — e.g. "Top up Betfair
>    funds" for `INSUFFICIENT_FUNDS`; "Wait for market resumption"
>    for `MARKET_SUSPENDED`].
> 4. Accept the unhedged position.
>
> Error detail: [Betfair error code + message].

**Modal data preservation:** indefinitely until operator dismisses.
Same rationale as path (a).

**Logging:** `place_hedge` returns `HedgePlacementResult` with
`success = False`, `error_path = 'b'`, `severity = 'critical'`,
`error_detail` carrying the Betfair error code. Hedge bet record
written with `match_status = 'failed'` per §3.4 — captures the
attempt for analytics even though the order didn't match.

**Pre-flight relationship:** §4's pre-flight checks substantially
*reduce* terminal-error frequency at `placeOrders` time (market
status caught at §4.2, fundedness caught at §4.3) but don't
eliminate it. Race conditions exist (market status changes between
pre-flight and `placeOrders`; balance changes if other bets settle
in the gap). Terminal errors at `placeOrders` are exceptions in
operational practice but not impossible.

### §5.4 — Path (c): Betfair hedge log write failure

**When this fires:** `placeOrders` succeeded; Betfair confirmed the
order; `record_builder.py` assembled the bet record;
`orchestrator.py` calls the v3 operational store to write — and
the write fails.

**Severity: standard.** Hedge is placed; both real-money positions
are closed. BetHub's local journal is incomplete; no monetary
risk.

**Likely causes:**

- v3 operational store transient failure (lock contention, brief
  unavailability).
- Schema validation failure (programmer error — should have been
  caught by `record_builder.py` Pydantic validation; surfaces here
  if it slipped through).
- Disk / filesystem error.

**Retry policy:**

- 3 attempts.
- Exponential backoff: **50ms, 200ms, 500ms.**
- Retry runs synchronously inside `place_hedge`.
- After 3 failures, treat as persistent and surface non-urgently.

**Surface message (persistent failure):**

> Hedge placed successfully on Betfair, but BetHub failed to log
> the hedge record. The position is closed (no monetary risk).
>
> Recovery options:
> 1. Retry log write (if transient cause is suspected).
> 2. Manually enter the hedge record from the Betfair confirmation
>    detail. The modal preserves the placement detail below.

**Modal data preservation:** indefinitely until operator dismisses.
Even though severity is standard, the data must not be lost — the
operator may need it for manual entry.

**Logging:** `place_hedge` returns `HedgePlacementResult` with
`success = False` (from BetHub's perspective the workflow didn't
complete), `error_path = 'c'`, `severity = 'standard'`,
`betfair_placement_detail` populated (so the operator / W7 can
display what happened on the exchange even though local logging
failed). The Betfair side is fact; only the local record is
missing.

### §5.5 — Path (d): soft-book log write failure

**When this fires:** both legs placed at books / exchange; hedge
record written successfully; operator submits the soft-book log
form (step 5); BetHub local DB write fails.

**Severity: standard.** Same rationale as path (c) — both
positions closed; record-keeping only.

**Operator-confirmed pattern** (Session 91 substrate): path (d)
"very occasionally happens" in v2 today. Lower severity is
acceptable because the position is closed; manual recovery works.

**Retry policy:** same as path (c). 3 attempts; 50ms / 200ms /
500ms backoff.

**Surface message (persistent failure):**

> Soft-book bet record failed to log. Both legs are placed (no
> monetary risk).
>
> Recovery options:
> 1. Retry log write.
> 2. Manually enter the soft-book bet record from the entry data
>    below.

**Modal data preservation:** indefinitely until operator dismisses.

**Logging:** `log_soft_book_bet` returns `SoftBookLogResult` with
`success = False`, `error_path = 'd'`, `severity = 'standard'`.

### §5.6 — Cross-cutting policies

**Result-type pattern, not exceptions** (Round 16, locked).
Operational errors flow through Pydantic result models. Exceptions
reserved for programmer errors (invalid input types, schema
violations, bugs).

**Backoff schedule is consistent across all retry-safe paths:**
50ms, 200ms, 500ms across 3 attempts. One schedule for the four
paths simplifies reasoning and matches v2's existing pattern.

**Retry runs synchronously inside the entry-point function.** Modal
blocks during retry; W7 may render a "retrying..." state. No
async retry queues; no fire-and-forget; no operator-invisible
recovery loops. Visibility is the priority.

**Modal data preservation rule (uniform across all four paths):**
on any error, modal preserves entry data **indefinitely** until
operator dismisses. Critical-path data preserved because operator
needs it for recovery decisions. Standard-path data preserved
because operator may need it for manual entry. Uniform rule
simplifies W7's UI logic.

**No mid-session escalation to operator.** `orchestrator.py` does
not pause and ask the operator a question mid-call. It runs end-to-
end, returns a result, and lets the modal / W7 handle operator
interaction. Per the brief-drafting skill's "no-mid-probe-
escalation" discipline.

### §5.7 — Error context carried in result models

Each result model carries enough context for W7 to render a useful
operator-facing message without re-querying:

```python
class ErrorContext(BaseModel):
    error_path: Literal["a", "b", "c", "d"]
    severity: Literal["critical", "standard"]
    error_code: str  # e.g. "STAKING_INVALID_INPUT", "BETFAIR_INSUFFICIENT_FUNDS"
    message: str  # operator-facing display text
    detail: dict  # structured context (Betfair error response, validation detail, etc.)
    retry_attempts: int  # how many retries were attempted before giving up
    recovery_options: list[str]  # operator-actionable next steps
    modal_data_snapshot: dict  # entry data preserved for manual recovery
```

**`recovery_options`** is a list of operator-facing strings. W7
renders these as buttons / options. Examples:

- Path (a): `["Retry calculation", "Manual hedge at Betfair",
  "Accept unhedged position"]`.
- Path (b) with `INSUFFICIENT_FUNDS`: `["Top up Betfair funds and
  retry", "Manual hedge at Betfair", "Accept unhedged position"]`.
- Path (c): `["Retry log write", "Manual entry from placement
  detail"]`.
- Path (d): `["Retry log write", "Manual entry from form data"]`.

**`modal_data_snapshot`** carries the entry data that the modal
should preserve. W7 renders this alongside recovery options so
operator has full context for the recovery decision.

### §5.8 — Logging and observability (out of scope at v1)

Persistent error logging to a durable audit log is **out of scope
for W4 v1**. v3's audit-log durable substrate is a deployment-time
decision (carried in `current_state.md` as §12 self-assessment item
3 — audit-log durable substrate selection).

W4 v1 ships with **transient logging only** — Python `logging`
module to stderr / app log. Errors are visible at runtime but not
persisted to a structured store. When the audit-log substrate
lands, W4's error paths will write to it; that's a follow-up
integration, not a W4 v1 deliverable.



## §6 — Reconciliation pass design

§6 specifies how W4 reconciles the per-order matching state for a
hedge after `placeOrders` returns. The pattern is **Trigger A + B
hybrid** (Round 15): an immediate write at `placeOrders` success
(Trigger A) followed by a reconciliation pass ~5 seconds later
(Trigger B) that updates the record with finalised match data.

The reconciliation pass is **per-order only** — W4 reconciles the
order it just placed. Broader sync-based reconciliation across the
whole bet history (catching missed Trigger A writes, sweeping
provisional records, reconciling against Betfair's order history)
is **W6 territory** and explicitly out of W4 scope.

### §6.1 — Trigger A — immediate write at placement success

**When this fires:** `placeOrders` returns successfully (HTTP 200 +
non-error result code).

**What it does:** `record_builder.py` assembles the bet record
using the `placeOrders` response data; `orchestrator.py` writes the
record to the v3 operational store with `match_status =
'provisional'`.

**Data populated from `placeOrders` response:**

- `requested_stake` — operator's submitted stake.
- `matched_stake` — `placeOrders` `sizeMatched` (what filled
  immediately at placement; often equals `requested_stake` for
  liquid markets).
- `unmatched_stake` — `requested_stake - matched_stake`.
- `matched_price` — `placeOrders` `averagePriceMatched` for the
  matched portion. Null when nothing matched immediately.
- `match_status` — `'provisional'` (until Trigger B confirms).
- Per-leg Betfair identifiers (`betfair_market_id`,
  `betfair_selection_id`), bet identifier (`betfair_bet_id` from
  `placeOrders` response), Set B six fields (from `marketCatalogue`
  cached in-memory at modal session per §3.5).

**Why immediate write matters:** if the operator's session ends
between Trigger A and Trigger B (browser close, network drop,
process crash), the bet record exists. The hedge happened on the
exchange regardless of BetHub's subsequent journal state; capturing
the placement at Trigger A makes BetHub's journal robust to
session-level interruption.

**Failure handling:** Trigger A failure is path (c) per §5.4 —
hedge log write failure. Standard severity, retry-with-backoff,
operator-facing recovery message. No Trigger B if Trigger A's write
never succeeds.

### §6.2 — Trigger B — reconciliation pass ~5 seconds after placement

**When this fires:** **5 seconds** after Trigger A's write
(configurable; v1 ships at 5).

**What it does:** `orchestrator.py` reads the order's current state
from Betfair (via streaming subscription if available, polling
fallback otherwise — see §6.3) and updates the bet record with
finalised match data.

**State transitions Trigger B may produce:**

| Pre-Trigger-B `match_status` | Betfair state | Post-Trigger-B `match_status` |
|---|---|---|
| `provisional` | Order fully matched | `final_full` |
| `provisional` | Order partially matched, remainder lapsed | `final_partial` |
| `provisional` | Order partially matched, remainder still pending | `provisional_pending` |
| `provisional` | Order placed but still fully unmatched | `provisional_pending` |
| `provisional` | Order cancelled / lapsed entirely | `failed` (rare; see §6.5) |

**Update fields:**

- `matched_stake`, `unmatched_stake`, `matched_price` — refreshed
  from current order state.
- `match_status` — transitioned per the table above.

**Why 5 seconds:** matches the operational rhythm of Betfair near-
jump matching (orders typically fill or lapse within a few seconds)
without holding the modal blocked. 5 seconds is the working default
from v2's pattern; configurable for tuning during W4 operational
use.

**Modal behaviour during Trigger B:** the modal does **not** block
on Trigger B. Trigger A's write is what BetHub considers "logged";
the modal can close after Trigger A completes. Trigger B runs in
the background (see §6.4 for execution model) and updates the
record in-place when complete.

### §6.3 — Streaming vs polling for Trigger B

W4 v1 specifies **two paths**, both implemented; runtime selection
based on whether a streaming subscription is available at W4-
shipping time.

**Streaming path (preferred when available):**

- Subscribes to Betfair Exchange Streaming API order subscription
  for the placed `betfair_bet_id`.
- Receives `OCM` (order change message) frames as the order's match
  state changes.
- Trigger B reads the latest `OCM` frame at the 5-second mark and
  uses its data for the update.
- Subscription cancels after Trigger B completes.

**Polling fallback (when streaming subscription not available):**

- Calls `listCurrentOrders` with the `betfair_bet_id` filter at the
  5-second mark.
- Reads order state from the response.
- Single call; no repeated polling.

**Why streaming preferred:** the streaming subscription captures
intermediate order-state changes (partial matches landing in
sequence), which a single polling call misses. Both paths produce
the same final `match_status` at the 5-second mark, but streaming
gives richer mid-flight observability for future analytics. v1's
analytics layer doesn't consume mid-flight data (Trigger B's
single read is what writes to the record), so polling is
operationally equivalent for W4 v1's purposes — streaming becomes
preferred as analytics layer (P2 territory) builds out.

**Streaming subscription dependency:** W4 v1's streaming path
**depends on W2 / W3** having shipped streaming subscription
infrastructure. Status check before W4 ships is carry-forward from
Session 91 (current `current_state.md` open items). If W2 / W3
streaming subscription is operational at W4-shipping time, Code
implements both paths and selects streaming at runtime; if not,
Code implements polling-only and notes streaming as a follow-up.

**Code's call:** Code's session reads the `betfair_client_contract.md`
v1.0 to confirm what's currently shipped and selects the
implementation accordingly. **If only one path is implementable at
Code's session time, Code surfaces that as a finding** rather than
implementing speculatively against unbuilt streaming infrastructure.

**Brief framing:** §6 specifies both paths; W4 implementation is
flexible to ship either or both. The streaming path is not a
gating dependency for W4 to ship.

### §6.4 — Trigger B execution model

**Asynchronous, in-process.** `orchestrator.py` schedules Trigger B
using Python's `asyncio` (per DR-031, the v3 tech stack decision).
A coroutine runs at `placeOrders + 5s`, performs the reconciliation
read, and updates the bet record.

**No background workers, no separate process, no queue.** Trigger
B runs inside the same Python process that handled the modal call.
Process lifetime: until Trigger B completes (typically <100ms after
the 5-second wait). If the process exits between Trigger A and
Trigger B, the bet record stays in `provisional` state; W6's
broader sync reconciliation (out of W4 scope) is the eventual catch.

**Modal returns to operator immediately after Trigger A.** The
operator does not wait 5 seconds for the modal to close; W7 dismisses
the modal on Trigger A success. Trigger B's work is operator-
invisible unless it surfaces a `provisional_pending` flag (see
§6.5).

**Failure handling:** if Trigger B's reconciliation read fails
(streaming or polling errors), the bet record stays in
`provisional`. **Trigger B retries once** at +10 seconds (single
retry, not the 3-attempt pattern from §5 — Trigger B is operator-
invisible and a transient failure is acceptable). After two
failures, the record stays `provisional` and is flagged for W6's
sync reconciliation to pick up later.

### §6.5 — Stuck-pending handling

**`provisional_pending` state:** rare; used when reconciliation
completes but the order has unmatched stake still pending in the
market (operator placed a bet that's only partially matched and the
unmatched portion is still working).

**When this happens in W4 v1:** the operator placed a hedge that
didn't fully match within the 5-second reconciliation window. The
matched portion is fact; the unmatched portion is in limbo until
the market closes (race start) or the operator cancels.

**W4 v1 surfaces `provisional_pending` to the operator** via a
flag W7 can render alongside the bet record (operator-facing:
"Hedge partially matched; unmatched stake of $X is still pending
on Betfair. Review and cancel manually if desired.").

**Final fallback if reconciliation can't establish final state:**
if the order's final state is unresolvable within a reasonable
window (e.g. 30 seconds — beyond Trigger B's execution), the bet
record stays `provisional_pending`. Operator-side review is the
terminal recovery path.

**No automatic cancellation.** W4 does not call Betfair's cancel
API on stuck-pending orders. Operator decides whether to let the
unmatched portion lapse at race start or cancel it manually
through Betfair directly. (Cancellation as a W4 capability is out
of scope for v1; surfaces as a future workflow extension.)

### §6.6 — Reconciliation pass scope (out of W4)

To prevent drift in Code's session:

- **Broader sync reconciliation** — sweeping all `provisional`
  records, reconciling against Betfair's full order history,
  catching missed Trigger A writes from path (c) failures. **W6
  territory.** W4 v1 ships per-order reconciliation only.
- **Settlement reconciliation** — populating `realised_conversion_
  rate`, `payout_amount`, `settlement_outcome`. **W5 territory.**
  Trigger B does not touch settlement fields.
- **Cross-leg reconciliation** — verifying that the hedge leg and
  soft-book leg of a single cycle were both logged correctly.
  **W6 / future workflow territory.** W4 v1 trusts that
  `place_hedge` and `log_soft_book_bet` each succeed independently
  and writes them as independent records linked by `cycle_id`.
- **Cancel-and-replace reconciliation** — handling cases where the
  operator cancels a hedge and replaces it. **Out of W4 v1 scope.**
  Cancellation is not a W4 v1 capability.
- **Streaming subscription lifecycle** — subscription pooling,
  reconnection, heartbeat handling. **W2 / W3 territory.** W4 v1
  consumes whatever subscription interface W2 / W3 ships.



## §7 — Pre-reads

Files Code reads before starting. Required-reads are loaded into
context at session open; reference-only docs are pulled on demand.

### §7.1 — Required reads

In order:

1. **This brief in full** — `dr029/w4_bet_entry/w4_bet_entry_brief.md`.
2. **Math review §1, §2, §3, §5, §6, §7** — `dr029/w4_bet_entry/
   hedge_staking_math.md`. **§4 (modal mechanics) is W7 territory;
   skip.** §1 is foundational framing; §2 is the free-bet hedge
   math (consumed by `staking.py`); §3 is combined-stake math; §5
   is bonus-winnings effective-odds synthesis (consumed by
   `pricing.py`); §6 is conversion-rate calibration (informs
   default 65%); §7 is edge cases.
3. **DR-032** — `decisions.md` line 1081. The canonical-reference-
   layer-for-all-bet-records decision; W4's schema contract.
4. **`architecture.md` §A.10** — line 563. The architectural-
   principle home that DR-032 cites; canonical source identifiers.
5. **DR-027** — `decisions.md`. Two-database architecture (BetHub
   owns operational state, capture.db owns analytical/source data).
   Frames W4's "no capture.db reads" stance.
6. **DR-028** — `decisions.md`. Cross-DB integration boundary
   discipline (no caching, no denormalisation, no second integration
   point). Frames Set B's in-memory-cache-only population.
7. **DR-030** — `decisions.md`. v3 repo layout; specifies
   `workflow/bet_entry/v1/` as W4's home and module-boundary
   discipline.
8. **DR-031** — `decisions.md`. v3 tech stack (Python 3.12+,
   FastAPI, SQLite WAL, SQLAlchemy Core, Pydantic v2, pytest, ruff,
   import-linter).
9. **`betfair_client_contract.md` v1.0** — rebuild folder root.
   Locked contract for the v3 Betfair client (`placeOrders` shape,
   error categorisation, streaming subscription interface,
   `marketBook` / `marketCatalogue` / `getAccountFunds` /
   `listCurrentOrders` shapes). **Required, not reference** — Code
   builds against this contract throughout.

### §7.2 — Reference-only

Read on demand if a question surfaces during the session:

- **DR-019** — derived state on read. Informed Set B's snapshot
  reasoning per §3.5.
- **DR-022** — account / book / account-at-book vocabulary. Frames
  `account_at_book_id` foreign-key field in §3.1.
- **DR-026** — at-log-time market snapshot pattern. DR-032's Set B
  follows this principle at the per-leg level.
- **DR-021** — Adelaide local timestamp anchoring. Applied to
  `placed_at` and all time-of-day references in W4 output.
- **`dr029/2_8_bet_schema/2_8_bet_schema.md`** — bet-schema
  reframing brief. Background context for DR-032; not required.
- **W4 substrate session records** — `sessions/SESSION_87.md` (W4
  substrate decisions), `SESSION_88.md` (math review §4 carried to
  W7), `SESSION_89.md` (math review §6/§7 lock), `SESSION_90.md`
  (DR-032 + §A.10 lock), `SESSION_91.md` (full design substrate).
  Reference if rationale for a specific design decision is
  unclear.

### §7.3 — Not pre-reads

Explicitly **not** required:

- **`vps_client_contract.md`** — VPS / capture.db scope; W4 doesn't
  touch capture.db.
- **DR-029 scope doc** — closed; W4 is post-DR-029 build work.
- **v2 codebase** — W4 is greenfield v3 build; v2 is reference for
  operational behaviour only and not authoritative for v3 design.
- **`v3_data_requirements.md`** — older artefact; superseded by
  workstream briefs for v3 build proper.



## §8 — System access

W4 is greenfield v3 build work running locally on the operator's
Mac. No VPS access, no capture.db access, no v2 modifications.

### §8.1 — Filesystem

**Read-write:**

- `/Users/tim/Desktop/Projects/bethub-v3/workflow/bet_entry/v1/` —
  the W4 module home. Code creates this directory tree and all
  files within it.
- `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w4_bet_entry/
  w4_bet_entry_report.md` — the report file (single output per
  §11).

**Read-only:**

- `/Users/tim/Desktop/Projects/bethub-rebuild/` — all named pre-
  reads per §7.
- `/Users/tim/Desktop/Projects/bethub-v3/` — v3 codebase. Code
  reads existing v3 modules (W0 / W1 / W2 / W3 if shipped) to align
  imports and patterns. **No edits outside `workflow/bet_entry/v1/`.**

**Out of bounds:**

- `/Users/tim/Desktop/Projects/bethub-v2/` — v2 codebase. Not modified.
- VPS at `root@187.77.183.9` — not accessed.

### §8.2 — Databases

- **v3 operational store** — read-write, only via the v3 storage
  interface (whatever W6 ships, or a stub if W6 not yet built; see
  §9.4). No direct SQL against the operational store from W4
  modules.
- **capture.db** — no access. W4 does not read or write capture.db.
- **v2 bethub.db** — no access.

### §8.3 — Betfair API

**Read-write** for orders. W4 calls Betfair via the v3 BetfairClient
shipped by W3 (per `betfair_client_contract.md` v1.0):

- `marketBook` — read live pricing + market status.
- `marketCatalogue` — read runner / event / venue metadata for Set B.
- `getAccountFunds` — read available balance for §4.3 fundedness.
- `placeOrders` — write hedge order.
- `listCurrentOrders` — read for Trigger B polling fallback.
- Streaming subscription (order subscription) — read for Trigger B
  streaming path.

**No direct HTTP calls.** All Betfair access routes through the v3
BetfairClient.

**Test mode:** mocked-API integration tests for `orchestrator.py`
use a mocked BetfairClient that returns fixture responses
conforming to the contract. **No real Betfair API calls in tests.**

### §8.4 — Tooling

- **Python 3.12+** per DR-031.
- **Pydantic v2** for all cross-module data shapes.
- **SQLAlchemy Core** for v3 storage interface (consumed; not
  defined by W4).
- **pytest** for unit + mocked-integration tests.
- **ruff** for linting; **import-linter** for module-boundary
  enforcement (`workflow/bet_entry/v1/` cannot import from forbidden
  layers per DR-030).

### §8.5 — Timestamps

All timestamps in code, tests, log output, and the report use
**Adelaide local time (ACST/ACDT)** per DR-021. Python's
`datetime.now(ZoneInfo("Australia/Adelaide"))` is the canonical call.



## §9 — Sequencing within session

W4's session is one bounded Code execution. §9 names the build
order Code follows and explains why. Code may deviate if a cleaner
order surfaces during the session — name the deviation in the
report's deviations section per §11.3.

### §9.1 — Build order

In dependency order:

1. **`models.py`** — Pydantic v2 models for cross-module data
   (bet record, bet leg, stake / match fields, `match_status`
   enum, `strategy_tag` enum, `PreFlightResult`,
   `HedgePlacementResult`, `SoftBookLogResult`, `ErrorContext`).
   Defines the contracts §3 / §4 / §5 specify.
2. **Storage-interface stub** — `storage.py` (or equivalent) at
   `workflow/bet_entry/v1/`. Thin protocol + reference
   implementation. See §9.4.
3. **`record_builder.py`** — pure module. Implements the DR-032
   contract (§3.1, §3.5, §3.6, §3.7, §3.8). Pure function: given
   entry-path inputs, return a validated bet record + bet legs
   structure.
4. **`staking.py` and `pricing.py`** — pure modules; build in
   parallel. `staking.py` implements math review §2 (free-bet
   hedge), §3 (combined-stake math). `pricing.py` implements math
   review §5 (bonus-winnings effective-odds synthesis) for both
   free-bet and cash flavours per §1.3.
5. **`orchestrator.py`** — impure module. Composes the three pure
   modules + BetfairClient + storage interface. Implements
   `pre_flight_check`, `place_hedge`, `log_soft_book_bet` per §2.3.
   Implements retry-with-backoff per §5, Trigger A + B
   reconciliation per §6.
6. **Tests alongside each module.** Pytest unit tests for pure
   modules build alongside the modules themselves. Mocked-API
   integration tests for `orchestrator.py` build last.

### §9.2 — Why this order

- **Models first.** Every other module imports from `models.py`.
  Building models first locks the contracts that the rest of the
  session implements against.
- **Storage interface stub second.** `record_builder.py` returns
  data structures; `orchestrator.py` writes them via the storage
  interface. Defining the interface shape early lets
  `orchestrator.py` integrate cleanly without speculating about
  W6's eventual API.
- **`record_builder.py` third.** It's the schema-shaping module;
  pure; tests cleanly in isolation. Builds confidence that the
  DR-032 contract is correctly implemented before staking /
  pricing math layers on top.
- **Staking and pricing in parallel.** No interdependency
  (`staking.py` and `pricing.py` do not import from each other per
  §2.2). Either can be built first; building in parallel is fine
  if Code's session shape supports it.
- **Orchestrator last.** Composition layer; depends on all four
  other modules. Building last means every dependency is in place
  with passing tests.
- **Tests alongside, not after.** Pure-module tests are quick to
  write and catch contract-shape errors immediately. Don't defer
  them to end-of-session.

### §9.3 — Permitted deviations

Code may reorder if a cleaner sequence surfaces during the session.
Common acceptable deviations:

- Building `staking.py` before `record_builder.py` if the staking
  math is more familiar to Code's working context and `record_
  builder.py`'s schema details surface questions that benefit from
  staking-side thinking first.
- Building `pricing.py` ahead of `staking.py` if Strategy 2 sub-
  shape (b) effective-odds synthesis is the more complex path and
  benefits from being tackled first.
- Skipping mocked-orchestrator tests if `orchestrator.py`'s
  composition is straightforward enough that unit tests on the
  pure modules cover the meaningful cases.

Code names the deviation and the reason in the report. **Order
deviations are normal; scope deviations are not.**

### §9.4 — Storage interface stub

W6 (operational store + session ops) ships the canonical v3
operational store schema later in the build sequence. **W4 ships
ahead of W6**, so W4 can't write to the W6 storage layer directly —
it doesn't exist yet.

**W4's solution:** ship a thin **storage-interface stub** at
`workflow/bet_entry/v1/storage.py` (or equivalent path). The stub
is two pieces:

1. **A protocol** (Python `Protocol` class or abstract base class)
   defining the interface that `orchestrator.py` writes against:

   ```python
   class BetRecordStorage(Protocol):
       def write_bet_record(self, record: BetRecord) -> WriteResult: ...
       def update_match_status(
           self, bet_id: str, status: MatchStatus,
           matched_stake: Decimal, unmatched_stake: Decimal,
           matched_price: Decimal | None,
       ) -> WriteResult: ...
       def read_bet_record(self, bet_id: str) -> BetRecord | None: ...
   ```

   (Exact signature is Code's call within the §3 schema contract.)

2. **A reference implementation** — SQLite-backed (per DR-031),
   single-file at a configurable path, schema migration via Alembic
   (per W0's scaffolding). The reference implementation is what W4
   actually writes to until W6 ships.

**Hand-off to W6:** when W6 ships the v3 operational store, W6
implements the same `BetRecordStorage` protocol. Swapping the
reference implementation for W6's implementation is a single
configuration change at `orchestrator.py`'s composition root.
**The protocol signature is the contract** — W6 conforms to it; W4
does not change.

**Why a stub vs waiting for W6:** building W4 against an
unimplemented W6 forces W4 to either guess at W6's API (drift risk)
or block on W6 (sequence break). Shipping a stub with a locked
protocol gives W4 something concrete to write against, gives W6 a
contract to implement, and lets the two workstreams ship in either
order without coupling.

**Stub limitations (operator-facing):** the SQLite reference
implementation is **operationally usable** for early v3 testing but
is not the production operational store. W6's implementation
supersedes it. Test data accumulated in the stub's SQLite file is
**not migrated automatically** to W6 when W6 ships — operator
decides at W6 cutover whether to migrate, replay, or discard.



## §10 — Empirical verification and acceptance

§10 names what "done" looks like for Code's session.

### §10.1 — Pure-module unit tests

Pytest unit tests for `staking.py`, `pricing.py`, and
`record_builder.py`. All tests pass before Code closes the session.

**Coverage targets:**

- `staking.py` — math review §2 (free-bet hedge) + §3 (combined
  stake) worked examples are pytest cases. Edge cases from math
  review §7 are pytest cases. Invalid input handling per §5.2
  exercised.
- `pricing.py` — math review §5 (bonus-winnings effective-odds
  synthesis) worked examples are pytest cases for both free-bet
  and cash flavours. Strategy-routing per §3.3 exercised
  (free-bet vs cash flavour selection).
- `record_builder.py` — DR-032 schema validation exercised.
  `strategy_tag` enum (closed-set + nullable) exercised.
  `is_free_bet` inheritance + override exercised. Set B
  population from `marketCatalogue` fixture exercised. Cycle-id
  generation + inheritance exercised. Strategy 3 raise-path
  exercised.

**No coverage minimum.** Code judges what counts as adequate
coverage; the goal is operational confidence, not a percentage
target. Code names test count + key cases covered in the report.

### §10.2 — Mocked-API integration tests for `orchestrator.py`

Pytest integration tests using a mocked BetfairClient that returns
fixture responses conforming to `betfair_client_contract.md` v1.0.
All tests pass before close.

**Cases exercised (minimum):**

- Happy path: `pre_flight_check` clean → `place_hedge` clean
  (Trigger A + Trigger B `final_full`) → `log_soft_book_bet` clean.
- Path (a) — staking math returns error.
- Path (b) — `placeOrders` returns retry-safe error, retries
  succeed.
- Path (b) — `placeOrders` returns retry-safe error, retries
  exhausted.
- Path (b) — `placeOrders` returns terminal error.
- Path (c) — Trigger A succeeds, storage write fails.
- Path (d) — `log_soft_book_bet` storage write fails.
- Trigger B — `final_partial` outcome.
- Trigger B — `provisional_pending` outcome.
- Trigger B — reconciliation read fails twice; record stays
  `provisional`.

**No real Betfair API calls in tests.** Mocked responses only.

### §10.3 — Acceptance is operator-side, post-brief

Manual operator acceptance happens **after** Code closes the
session. Shape:

1. Operator reads the report.
2. Operator runs a small real-money test bet through the full
   workflow (single Strategy 1 or Strategy 2 cycle at small stake)
   against the operator's actual Betfair account in a test market
   (e.g. low-stakes daily race).
3. Operator confirms the bet record landed correctly in the
   storage stub, the hedge matched on Betfair, and the four error
   paths haven't surfaced unexpectedly.

**This step is out of W4's brief.** It's operator-Claude triage
work in the next session after Code's report lands.

**No real-API integration tests in W4's session.** Per Round 17
test-coverage scope decision: operational use is the strongest
integration test signal; the mocked-API tests cover protocol
correctness against the locked contract.

### §10.4 — Linting and module-boundary checks

- `ruff` clean (no errors, no warnings) across all W4 files.
- `import-linter` passes — `workflow/bet_entry/v1/` does not import
  from forbidden layers per DR-030.
- Pure modules (`staking.py`, `pricing.py`, `record_builder.py`)
  do not import from `orchestrator.py` or each other.
- Pure modules import only from stdlib + Pydantic + (where
  applicable) other pure modules' `models.py` types.



## §11 — Output spec

Code produces **one report file** at the end of the session.

### §11.1 — File path and format

**Path:** `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/
w4_bet_entry/w4_bet_entry_report.md`.

**Format:** markdown, hard line wraps at ~70 characters per
`standing_instructions.md` Cat 1 (line-break rendering for review
content). Adelaide local timestamps per DR-021.

**Length range:** 400–700 lines. Range, not hard line. Code may
reasonably exceed when the work warrants it (e.g. unexpected
findings, multi-deviation scope detail) but flags the overrun in
the report's self-assessment section per §11.4.

### §11.2 — Section structure

In order:

1. **Header** — session timestamp (open + close, Adelaide local),
   total wall-clock, brief reference, summary of what shipped.
2. **Modules built** — one sub-section per module
   (`models.py`, `storage.py` stub, `record_builder.py`,
   `staking.py`, `pricing.py`, `orchestrator.py`). Each sub-section
   names: file path, line count, key public surface (classes /
   functions), key dependencies, brief notes on implementation
   choices.
3. **Tests built** — pytest test count by module, summary of
   cases exercised, fixtures used, mock shapes for `orchestrator.
   py` integration tests. Confirms §10.1 + §10.2 cases all
   exercised.
4. **Test results** — full pytest output summary (pass / fail /
   skip count). All tests pass at close per §10.1 / §10.2; if any
   skip or fail, named and explained.
5. **Linting + import-linter results** — `ruff` and `import-
   linter` final-state output. All clean per §10.4; if not, named.
6. **Deviations from brief** — every place Code deviated from §1–
   §10 spec. Each deviation: what the brief said, what Code did,
   why. **Order deviations are normal and expected** (per §9.3);
   scope deviations are flagged for triage.
7. **Open questions** — every place Code had to make a call that
   wasn't explicitly covered by the brief. Includes contract
   ambiguities (`betfair_client_contract.md` shape), edge cases not
   in math review §7, schema field semantics not nailed in §3.
   Operator-Claude triage works through these in the next session.
8. **Findings** — observations that aren't deviations or open
   questions but matter for next-stage work. Examples: stub
   storage performance characteristics, retry timing observed in
   mocked tests, behavioural surprises from the contract, things
   W6 / W7 will need to know.
9. **Self-assessment** — Code's confidence in the build.
   Specifically:
   - Did the build fit within the session budget? If not, where
     did the budget run tight?
   - Are there parts of the build Code is less confident about
     (math edge cases, error-path behaviour, async timing)?
   - What would Code recommend the operator look at first when
     reviewing?

### §11.3 — What the report does not contain

- **No proposed next briefs.** The next brief is operator-Claude's
  call after reading the report; Code does not draft follow-on
  briefs.
- **No scope expansion.** If Code thought "this would also need
  X", X goes in **Open questions** or **Findings** — not as
  speculative implementation.
- **No real-API test results.** §10.3 acceptance is operator-side;
  Code's report covers mocked-API tests only.
- **No strategic recommendations.** Code reports what was built,
  what surprised Code, what's open. Operator-Claude decides what
  to do about it.

### §11.4 — Length-range overrun handling

If the report runs longer than 700 lines:

- Code names the overrun in §11.2's self-assessment sub-section.
- Code names which sub-section drove the overrun (typically
  Deviations or Open questions on first-of-workstream work).
- Code does not pad sections to hit a length target; under-running
  the range is fine if the work was crisp.



## §12 — Hard limits

The eight hard limits Code must not exceed. These are non-
negotiable. Surprises become **findings** (in §11's report
section), not silent scope additions.

### §12.1 — Single bounded session

W4 is one Code session. If the work doesn't fit, that's a finding,
not a continuation. Partial-but-coherent ships beat
complete-but-budget-exhausted scrambles.

### §12.2 — Module set fixed at four workflow modules

The four workflow modules locked at Round 2:

1. `orchestrator.py` (impure)
2. `staking.py` (pure)
3. `pricing.py` (pure)
4. `record_builder.py` (pure)

**No additional workflow modules. No splits. No merges.**

**Support files are not workflow modules** — these are permitted
and do not violate this limit:

- `models.py` — Pydantic v2 model definitions shared across the
  four workflow modules. Named in §2.4.
- `storage.py` (or equivalent) — `BetRecordStorage` protocol +
  SQLite-backed reference implementation. Named in §9.4.
- `__init__.py` — Python package marker.
- `tests/` — pytest test files, one per workflow module plus
  `test_orchestrator.py` for mocked-API integration tests.

The four-module limit governs **workflow architecture**, not
filesystem layout. Support files exist to make the four workflow
modules work; they're not workflow modules themselves.

If Code finds it needs a fifth workflow module to ship the brief,
**that's a finding**, not a silent expansion. Code stops, names
the gap in the report, and operator-Claude triages in the next
session.

### §12.3 — DR-032 schema is the bet-record contract

§3 maps the schema; Code implements against it. **No schema changes
mid-session.** If a schema gap surfaces during implementation,
that's a finding for the next operator-Claude triage session, not
a silent addition.

W4 v1 specifies the **field-level contract**; W6 implements the
**storage layer** (table creation, constraints, indexes, migration
framework). Code's storage stub at §9.4 is the interim
implementation — its schema follows §3, not a Code-invented variant.

### §12.4 — No edits outside `workflow/bet_entry/v1/`

Code may **read** other v3 modules (W0 / W1 / W2 / W3 if shipped)
to align imports and patterns. Code may **not edit** any file
outside `workflow/bet_entry/v1/` and the named report path
(`dr029/w4_bet_entry/w4_bet_entry_report.md`).

If Code finds an issue in another v3 module that affects W4,
that's a finding — not a quick fix.

### §12.5 — Pre-flight stays modal-only

§4's pre-flight checks are scoped to two checks at modal level
(market status + proposed-stake fundedness). **No page-level
state-reading.** No pre-flight checks at other layers (racing
page, soft-book log screen, settlement). The dropped page-level
Betfair balance threshold flag is explicitly out of scope.

### §12.6 — No UI rendering work

W4 is the workflow engine + data contract. **All UI rendering is
W7's territory.** Code does not write Vue / React / template /
styling code. Code does not design modal layouts. Code does not
make rendering decisions.

If §3 / §4 / §5 / §6 specify a data shape that W7 will render,
Code ships the data shape — not the rendering.

### §12.7 — Reconciliation pass is per-order only

§6's reconciliation pass reconciles the order Code just placed.
**No broader sync reconciliation.** Sweeping all `provisional`
records, reconciling against Betfair's full order history, catching
missed Trigger A writes from path (c) failures — all W6 territory.

§6.6 names the out-of-scope reconciliation paths explicitly. Code
must not implement any of them.

### §12.8 — Test coverage scope is fixed

Per Round 17:

- **Unit tests** for pure modules (`staking.py`, `pricing.py`,
  `record_builder.py`). Required.
- **Mocked-API integration tests** for `orchestrator.py`. Required.
- **No real-API integration tests.** Real-API acceptance is
  operator-side post-brief work per §10.3.

If Code thinks real-API tests are warranted, that's a finding —
not a silent addition.

### §12.9 — Other named exclusions

Carried forward from §1.2 for emphasis. Code does not ship:

- W4.1 (soft-book typed-price entry path).
- W6 (operational store schema).
- W7 (UI / modal rendering).
- Strategy 3 SGM implementation.
- Manual free-bet ledger entry workflow.
- Modal mechanics from math review §4 (W7 territory).
- Multi-rung ladder hedge.
- Page-level Betfair balance threshold flag.
- W5 settlement worker logic.
- Broader sync-based reconciliation safety net.
- Cancel-and-replace workflow.
- Streaming subscription lifecycle (W2 / W3 territory).
- Persistent error-log substrate (audit-log durable substrate is a
  separate deployment-time decision per §5.8).



## §13 — What happens after Code's session

§13 names the next operator-Claude session's job after Code's
report lands.

### §13.1 — Triage session reads the report

A fresh operator-Claude session opens, reads
`w4_bet_entry_report.md` in full, and works through the report's
Open questions and Findings sections. Operator-Claude triage is the
shape; Code does not write the next brief.

The triage session names what each Open question / Finding implies
and routes accordingly:

- **Implementation gaps Code couldn't close** — schema-shape
  questions, contract ambiguities, math edge cases. Operator-Claude
  triage decides whether the gap closes in a follow-up Code session
  (small targeted brief), in operator-Claude design work (governance
  layer), or in W7 / W6 / W5 (downstream workstream).
- **Findings on stub limitations** — storage-stub characteristics
  W6 will need to know. Routes to W6 brief-drafting context.
- **Findings on contract ambiguities** — places where
  `betfair_client_contract.md` v1.0 didn't fully specify a shape
  Code needed. Routes to a contract-update follow-up if material.
- **Deviations Code flagged** — operator-Claude reviews each, locks
  in (and updates relevant briefs / contracts) or surfaces back as
  a follow-up.
- **Self-assessment items** — anywhere Code expressed lower
  confidence routes to operator-side acceptance review per §10.3
  with extra attention.

### §13.2 — Operator-side acceptance

Per §10.3, operator runs a small real-money test bet through the
full workflow. This happens **after** the triage session has worked
through the report — operator goes into the test bet with a clear
view of which paths to watch carefully.

Acceptance findings (anything that surfaces during real-bet
operation that the mocked-API tests didn't catch) get logged as
follow-up items for a small targeted Code brief.

### §13.3 — Forward routing

Once W4 has shipped clean (mocked-API tests pass + operator
acceptance landed), the next workstream opens. Per the v3 build
picture (Session 91 close):

- **W4.1** (soft-book typed-price entry path) — `blocked-on-W4`,
  unblocks here. Small follow-up brief.
- **W7** (Burst Review workflow) — `unblocked` (sequenced behind
  W4), can open in parallel with W4.1 or sequenced after.
- **W5** (settlement worker) — `blocked-on-W4`, unblocks here.
- **W6** (operational store + session ops) — currently `blocked-on-
  W1`; remains blocked on W1 regardless of W4. W6 implements the
  `BetRecordStorage` protocol that W4's stub defined, swapping the
  stub at composition time.

Triage session decides which next workstream to open and drafts the
next brief.

### §13.4 — Stub retirement timing

W4's storage stub is operationally usable but not the production
store. **The stub remains in place until W6 ships W6's
implementation** of `BetRecordStorage`. At W6 cutover:

- Operator-Claude session reviews any data accumulated in the stub
  during W4's operational use period.
- Operator decides: migrate to W6 (if data is operationally
  meaningful), replay test workflows against W6 (if data was test-
  only), or discard (clean start).
- W4's `orchestrator.py` composition root is updated to point at
  W6's implementation. No W4 module changes.

The stub's existence is an explicit interim state — not a
permanent fixture.



## §14 — Cross-references

### §14.1 — Decision Records

- **DR-019** — derived state on read. Informed Set B snapshot
  reasoning (§3.5).
- **DR-021** — timestamp anchoring, Adelaide local time. Applied
  to `placed_at` field (§3.1) and all time-of-day references in
  W4 output (§8.5).
- **DR-022** — account / book / account-at-book vocabulary.
  Frames `account_at_book_id` foreign-key field (§3.1).
- **DR-026** — at-log-time market snapshot pattern. Set B six-
  field per-leg pattern follows DR-026's principle (§3.5).
- **DR-027** — two-database architecture (BetHub owns operational
  state, capture.db owns analytical/source data). Frames W4's "no
  capture.db reads" stance throughout.
- **DR-028** — cross-DB integration boundary discipline (no
  caching, no denormalisation, no second integration point).
  Frames Set B in-memory `marketCatalogue` cache (§3.5) and "no
  second API call" pre-flight design (§4.2).
- **DR-030** — v3 repo layout + module-boundary discipline.
  Specifies `workflow/bet_entry/v1/` as W4's home; enforced by
  import-linter checks (§10.4).
- **DR-031** — v3 tech stack (Python 3.12+, FastAPI, SQLite WAL,
  SQLAlchemy Core, Pydantic v2, pytest, ruff, import-linter).
  Applied across §2, §6.4, §8.4, §10.
- **DR-032** — canonical-reference-layer-for-all-bet-records.
  Load-bearing for W4 schema; §3 maps DR-032 fields to W4
  population sources.

### §14.2 — Substrate documents

- **`hedge_staking_math.md`** — math review §1, §2, §3, §5, §6,
  §7. Required-read for Code per §7.1. §4 (modal mechanics)
  carried to W7.
- **`architecture.md` §A.10** — canonical source identifiers.
  Architectural-principle home that DR-032 cites. Required-read
  per §7.1.
- **`betfair_client_contract.md` v1.0** — locked v3 BetfairClient
  contract. Required-read per §7.1.
- **`dr029/2_8_bet_schema/2_8_bet_schema.md`** — bet-schema
  reframing brief. Background context for DR-032; reference-only.

### §14.3 — Session records

W4 design substrate decisions:

- **`sessions/SESSION_87.md`** — initial W4 substrate (four
  decisions logged).
- **`sessions/SESSION_88.md`** — math review §4 (modal mechanics)
  carried to W7.
- **`sessions/SESSION_89.md`** — math review §6 (worked examples)
  + §7 (edge cases) lock.
- **`sessions/SESSION_90.md`** — DR-032 + `architecture.md` §A.10
  landed; governance-gap closure.
- **`sessions/SESSION_91.md`** — full W4 brief design substrate
  (17 operator-facing rounds); brief skeleton + §1 / §2 drafted.
- **`sessions/SESSION_92.md`** — §3–§14 drafted; brief locked.

Substrate file: **`dr029/w4_bet_entry/_drafts/SESSION_91_substrate.
md`** — rationale-preserving 17-round design log. Reference for
"why was this decision made" questions during Code's session.

### §14.4 — Workstream cross-references

- **W4.1** (soft-book typed-price entry path) — sequenced
  behind W4; out of W4 v1 scope per §1.2.
- **W5** (settlement worker) — populates `realised_conversion_
  rate`, `payout_amount`, `settlement_outcome` per §3.1 / §3.3;
  sequenced behind W4.
- **W6** (operational store + session ops) — implements the
  `BetRecordStorage` protocol W4 defines (§9.4); replaces W4's
  stub at composition time per §13.4.
- **W7** (Burst Review workflow) — consumes W4's data contracts
  for modal rendering; ships modal mechanics from math review §4
  carried forward Session 91.
- **W2 / W3** — streaming subscription dependency for Trigger B
  streaming path per §6.3; flagged-but-not-gating.

### §14.5 — Excluded parking-lot items

Named here so Code can recognise them and not chase them:

- Manual free-bet ledger entry workflow.
- Multi-rung ladder hedge (math review §7.2 future arc).
- Page-level Betfair balance threshold flag.
- Cancel-and-replace workflow.
- Persistent error-log substrate (audit-log durable substrate is
  a deployment-time decision).
- Strategy 3 SGM implementation.
- Real-API integration tests.


