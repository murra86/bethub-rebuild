# Pre-W14 codebase review — bethub-v3 inventory and
# drift surfacing — report

**Brief:** `dr029/pre_w14_review/pre_w14_review_brief.md`
(locked 2026-05-11 22:31 ACST, Session 122).
**Execution opened:** 2026-05-11 22:32 ACST.
**Execution closed:** 2026-05-11 22:42 ACST.
**Author:** Claude Code, single bounded session.
**All timestamps:** Adelaide local per DR-021.

---

## §0 — Reading order and ground rules

This report is an empirical inventory pass over
`bethub-v3/` against `architecture.md`, the locked DRs
in `decisions.md` (DR-001 through DR-032), and the
`v3_data_requirements.md` / `dr029_scope.md` substrate.
Per brief §1 / §8, it does **not** propose fixes,
judge fitness, recommend remediation, or commission
follow-up work — triage is the next operator-Claude
session's job.

Sections §1–§10 below are 1:1 with brief §5.1–§5.10.
§11 ranks drift findings by operational severity; §12
is the self-assessment per the brief-drafting
convention.

**Citation discipline (brief §7):** every drift
finding cites both sides — the shipped file (absolute
path + line range) and the spec source it diverges
from (file + line / DR number).

**Deviations from sequencing (brief §6):** none. The
report follows §5.1 → §5.10 in the brief's order.

---

## §1 — Bet pillar inventory (brief §5.1)

### §1.1 — Module-by-module: what / persists / exposes

#### `domain/bets/__init__.py` (371 lines)

- **What:** Bet-vocabulary domain types per DR-032
  schema and W4 / W5 / W6 / W6.5 / W9 fields. Eleven
  types lifted from `workflows.bet_entry.v1.models`
  per W10 brief §5.1 — nine enums plus `BetLeg` and
  `BetRecord` Pydantic v2 models.
- **Persists:** Nothing. Pure domain layer (DR-030).
- **Exposes publicly** (`__all__`):
  `DEFAULT_PAST_WINDOW_SECONDS`, `BetLeg`, `BetRecord`,
  `BetSideTag`, `Construction`, `EntryPath`,
  `HedgeSoftBookStakeKind`, `LegRole`, `MatchStatus`,
  `PriceSource`, `SettlementState`, `StrategyTag`,
  plus `_now_adelaide()` (module-private helper
  reachable for monkey-patching).
- **Notable structural facts:**
  - `BetRecord.last_read_market_state` typed
    `dict[str, object] | None` (W10.1 — demoted from
    `MarketSettlement` to keep `domain` free of
    `clients` imports).
  - `BetRecord.is_past_settlement_window` is a
    `@computed_field` reading `_now_adelaide()`.
  - `SettlementState` enum has five values: `pending`,
    `settled_won`, `settled_lost`, `voided`,
    `provisional` (line 117–121).
  - `MatchStatus` enum has five values: `final_full`,
    `final_partial`, `provisional`, `provisional_pending`,
    `failed` (line 100–104).
  - `StrategyTag` enum has four values: `safety_net`,
    `price_booster`, `sgm_correlated`,
    `synthetic_each_way` (line 85–88). `sgm_correlated`
    is reserved but raises in `record_builder.py`
    (W4 v1 single-leg only).
  - `EntryPath` enum has four values: `racing_screen`,
    `sports_screen`, `manual_log`, `free_bet_ledger`
    (line 131–134). W4 v1 populates `RACING_SCREEN`
    only per the docstring.

#### `store/schema/bets.py` (120 lines)

- **What:** DDL + inline migrations for `bets` and
  `bet_legs` tables (W10 lift).
- **Persists:** Schema only — `apply_migrations()`
  runs `CREATE TABLE IF NOT EXISTS` plus
  `_add_column_if_missing` for W6 v1 / W6.5 / W9
  additive columns. No data writes.
- **Exposes:** `_BETS_DDL`, `_LEGS_DDL`,
  `_add_column_if_missing`, `apply_migrations`.

**`bets` table — verbatim column list (`store/schema/bets.py:17-45`):**

```
bet_id                       TEXT    PRIMARY KEY
cycle_id                     TEXT    NOT NULL
entry_path                   TEXT    NOT NULL
strategy_tag                 TEXT    -- nullable per W4 §3.2
is_free_bet                  INTEGER NOT NULL
free_bet_conversion_rate     REAL
realised_conversion_rate     REAL    -- W5 populates
requested_stake              TEXT    NOT NULL  -- Decimal-as-string
matched_stake                TEXT    NOT NULL
unmatched_stake              TEXT    NOT NULL
matched_price                REAL
match_status                 TEXT    NOT NULL
soft_book_combined_price     REAL
placed_at                    TEXT    NOT NULL  -- ISO8601 Adelaide local
book_or_exchange             TEXT    NOT NULL
account_at_book_id           TEXT    NOT NULL
price_source                 TEXT             -- W4 follow-up §5.2
betfair_bet_id               TEXT
last_reconciled_at           TEXT             -- W6 v1; nullable; ISO8601
reconciliation_attempts      INTEGER DEFAULT 0
settlement_state             TEXT             -- W6.5; nullable
dead_heat_count              INTEGER          -- W6.5; nullable
removed_runner_count         INTEGER          -- W6.5; nullable
unexpected_state_count       INTEGER          -- W6.5; nullable
last_read_market_state       TEXT             -- W9; nullable JSON
```

**`bet_legs` table — verbatim column list (`store/schema/bets.py:47-66`):**

```
bet_id                          TEXT    NOT NULL
leg_number                      INTEGER NOT NULL
leg_role                        TEXT    NOT NULL
betfair_market_id               TEXT    NOT NULL
betfair_selection_id            TEXT    NOT NULL
betfair_event_name              TEXT    NOT NULL
betfair_market_name             TEXT    NOT NULL
betfair_selection_name          TEXT    NOT NULL
betfair_event_venue             TEXT    NOT NULL
betfair_event_sport             TEXT    NOT NULL
betfair_event_start_time        TEXT    NOT NULL
betfair_implied_probability     REAL
matched_stake                   TEXT
matched_price                   REAL
PRIMARY KEY (bet_id, leg_number)
FOREIGN KEY (bet_id) REFERENCES bets(bet_id)
```

**Migrations callouts** (`store/schema/bets.py:107-117`):
columns added via `_add_column_if_missing` are
`last_reconciled_at`, `reconciliation_attempts`,
`settlement_state`, `dead_heat_count`,
`removed_runner_count`, `unexpected_state_count`,
`last_read_market_state`. The docstring at lines 80–84
flags: "v1 pattern. Replaced by Alembic revisions
post-DR-029-close (DR-031 locks Alembic … W10 brief
§10 / §1 explicitly defers Alembic adoption to a
separate later brief)."

#### `store/repositories/bets.py` (932 lines)

- **What:** Bet-record storage repository (W10 lift).
  Three top-level shapes — `BetRow` (frozen
  dataclass), `BetLegRow` (frozen dataclass),
  `WriteResult` — plus the `BetRecordStorage`
  `Protocol`, an `InMemoryBetRecordStorage`
  implementation, and an `SQLiteBetRecordStorage`
  reference implementation.
- **Persists:** `bets` and `bet_legs` rows. WAL mode +
  `PRAGMA foreign_keys = ON` (lines 469–470).
- **Exposes (`__all__`):** `BetLegRow`,
  `BetRecordStorage`, `BetRow`,
  `InMemoryBetRecordStorage`, `SQLiteBetRecordStorage`,
  `StorageWriteError`, `WriteResult`.

**`BetRecordStorage` Protocol — public method signatures
(`store/repositories/bets.py:120-207`):**

```python
write_bet_record(self, row: BetRow,
    leg_rows: list[BetLegRow]) -> WriteResult
update_match_status(self, bet_id: str, status: str,
    matched_stake: Decimal, unmatched_stake: Decimal,
    matched_price: float | None) -> WriteResult
read_bet_record(self, bet_id: str) ->
    tuple[BetRow, list[BetLegRow]] | None
list_unreconciled_bets(self, *,
    statuses: tuple[str, ...] =
        ("provisional", "provisional_pending"),
    older_than: datetime | None = None,
    max_results: int = 100) ->
        list[tuple[BetRow, list[BetLegRow]]]
update_reconciliation_bookkeeping(self, bet_id: str,
    *, last_reconciled_at: datetime,
    attempts_increment: int = 1) -> WriteResult
update_settlement_state(self, bet_id: str, *,
    settlement_state: str,
    dead_heat_count: int | None = None,
    removed_runner_count: int | None = None,
    unexpected_state_count: int | None = None)
        -> WriteResult
list_unsettled_bets(self, *,
    settlement_states: tuple[str, ...] = ("pending",),
    older_than_event_start: datetime | None = None,
    max_results: int = 100) ->
        list[tuple[BetRow, list[BetLegRow]]]
list_provisional_settlement_bets(self, *,
    max_results: int = 100) ->
        list[tuple[BetRow, list[BetLegRow]]]
list_bet_ids_for_market(self, market_id: str, *,
    exclude_bet_id: str | None = None) -> tuple[str, ...]
update_last_read_market_state(self, bet_id: str, *,
    last_read_market_state: str | None) -> WriteResult
```

**Storage uses raw `sqlite3`**, not SQLAlchemy Core
(`store/repositories/bets.py:16` imports `sqlite3`;
no `sqlalchemy` import anywhere in `store/`).

#### `workflows/bet_entry/v1/__init__.py` (144 lines)

- **What:** Package façade re-exporting eleven
  domain types from `domain.bets` plus the
  W4-shipped workflow surface (`BetEntryOrchestrator`,
  request shapes, four-path error model, staking
  math, pricing math, record builder helpers,
  reconciliation worker, soft-book log result).
- **Persists:** Nothing (pure re-exports).
- **Exposes:** 36 names in `__all__`
  (lines 84–144).

#### `workflows/bet_entry/v1/models.py` (136 lines)

- **What:** Five workflow result envelopes —
  `PreFlightFlag`, `PreFlightResult`, `ErrorContext`,
  `HedgePlacementResult`, `SoftBookLogResult`. Bet
  vocabulary lifted to `domain.bets` per W10.
- **Persists:** Nothing.
- **Exposes:** Five model classes plus the
  `PreFlightSeverity` `Literal["ok", "warn", "block"]`
  alias.

#### `workflows/bet_entry/v1/orchestrator.py` (1484 lines)

- **What:** The single impure composition module.
  Implements three public entry points —
  `pre_flight_check`, `place_hedge`, and
  `log_soft_book_bet` — plus the `BetfairAdapter`
  Protocol, Trigger B scheduling shapes, retry-
  with-backoff logic, the four-path error model
  (paths a/b/c/d), and the read-outcome
  discriminated-union (`ReadOk`, `ReadUnavailable`,
  `ReadOutcome[T]`).
- **Persists:** Via injected `BetRecordStorage` —
  `bets` and `bet_legs` rows on `place_hedge` and
  `log_soft_book_bet`; `update_match_status` on
  Trigger B reconciliation.
- **Exposes (`__all__`):** `BetEntryOrchestrator`,
  `BetfairAdapter`, `FundsSnapshot`,
  `HedgeEntryRequest`, `ManualTriggerBScheduler`,
  `MarketSettlement` (re-exported from
  `clients.betfair_client.v1.settlement`),
  `MarketStatusSnapshot`, `OrderStateSnapshot`,
  `PlacementOutcome`, `ReadOk`, `ReadOutcome`,
  `ReadUnavailable`, `SoftBookLogRequest`,
  `ThreadingTriggerBScheduler`, `TriggerBScheduler`.
- **Notable structural fact:** the orchestrator
  file is monolithic (~1500 lines). DR-029 close-out
  named "monolithic orchestrator file" as one of
  the three pieces of named debt (per `dr029_scope.md`
  §2.1 close addendum, Session 34); deferred-but-
  tracked at DR-029 close.

#### `workflows/bet_entry/v1/staking.py` (400 lines)

- **What:** Hedge stake math — pure module
  (no I/O). Implements Construction A
  (lay-against-back) and Construction B
  (back-against-back) per the math review
  (`dr029/w4_bet_entry/hedge_staking_math.md`).
  Cash and free-bet stake-kind discrimination.
  Commission table keyed on
  `(sport_family, country_code, venue_normalised)`
  with cascading fallback.
- **Persists:** Nothing.
- **Exposes:** `CommissionLookupKey`,
  `HedgeStakeInput`, `HedgeStakeResult`,
  `StakingError`, `breakeven_betfair_price`,
  `commission_lookup`, `compute_hedge_stake`,
  `resolve_commission`.

#### `workflows/bet_entry/v1/pricing.py` (194 lines)

- **What:** Effective-odds synthesis — pure
  module (no I/O). Implements bonus-winnings
  effective-odds synthesis for free-bet and
  cash flavours (math review §5).
- **Persists:** Nothing.
- **Exposes:** `DEFAULT_FREE_BET_CONVERSION_RATE`,
  `BonusFlavour`, `EffectiveOddsInput`,
  `EffectiveOddsResult`, `PricingError`,
  `optimal_promo_stake`, `synthesise_effective_odds`.

#### `workflows/bet_entry/v1/record_builder.py` (375 lines)

- **What:** DR-032 bet record + bet legs assembly —
  pure module (no I/O). Two builder entry points:
  `build_hedge_bet_record` (writes a hedge-leg
  record with `MatchStatus.PROVISIONAL` per
  Trigger A) and `build_soft_book_bet_record`.
  Validates strategy-tag (raises for
  `SGM_CORRELATED`) and free-bet invariants.
- **Persists:** Nothing.
- **Exposes:** `BetRecordBuilderError`,
  `HedgeRecordInputs`, `LegSnapshot`,
  `SoftBookRecordInputs`, `build_hedge_bet_record`,
  `build_soft_book_bet_record`.

#### `workflows/bet_entry/v1/bet_store_adapter.py` (202 lines)

- **What:** Boundary adapter between
  `domain.bets.BetRecord` and
  `store.repositories.bets.BetRow` /
  `BetLegRow`. Three functions: `to_rows`,
  `from_rows`, `to_provisional_payload`.
  Handles JSON serialisation for
  `last_read_market_state`.
- **Persists:** Nothing directly; called from the
  orchestrator + settlement worker + provisional
  router on writes/reads.
- **Exposes:** `from_rows`, `to_provisional_payload`,
  `to_rows`.

#### `workflows/bet_entry/v1/betfair_adapter.py` (433 lines)

- **What:** `RealBetfairAdapter` — production
  implementation of the `BetfairAdapter` Protocol.
  Wraps `clients.betfair_client.v1` surfaces
  (`get_live_market_prices`, `get_account_funds`,
  `place_bet`, `list_current_orders`,
  `runner_best_prices`, `market_settlement`) and
  translates between Betfair's API shape and W4's
  internal namespace. Requires a streaming-equipped
  `BetfairClient` (raises in `__post_init__` if
  `client.streaming_client is None`).
- **Persists:** Nothing directly; orchestrator
  drives writes via the storage interface.
- **Exposes:** `RealBetfairAdapter` (one frozen
  dataclass).

#### `workflows/bet_entry/v1/reconciliation.py` (660 lines)

- **What:** Periodic match-state reconciliation
  worker (W6 v1). Sweeps bets in
  `MatchStatus.PROVISIONAL` or
  `PROVISIONAL_PENDING`, reads
  `listCurrentOrders` and `market_settlement`,
  resolves to terminal states (`FINAL_FULL` /
  `FINAL_PARTIAL` / `FAILED`) or carries forward
  with reason codes.
- **Persists:** Via injected `BetRecordStorage` —
  `update_match_status` on transition;
  `update_reconciliation_bookkeeping` per swept
  bet per pass.
- **Exposes (`__all__`):**
  `DEFAULT_AGE_THRESHOLD_SECONDS` (60s),
  `DEFAULT_RECONCILIATION_INTERVAL_SECONDS` (300s),
  `ManualReconciliationScheduler`,
  `ReconciliationPassResult`,
  `ReconciliationScheduler`, `ResolutionDecision`,
  `ResolutionReasonCode`,
  `ThreadingReconciliationScheduler`,
  `run_reconciliation_pass`.

#### `workflows/bet_entry/v1/settlement.py` (1354 lines)

- **What:** Periodic settlement-state worker
  (W6.5 + W9). Two pass loops:
  `run_settlement_pass` (sweeps
  `SettlementState.PENDING` and reads
  `market_settlement`, transitions to
  `SETTLED_WON` / `SETTLED_LOST` / `VOIDED` /
  `PROVISIONAL`) and `run_provisional_resolution_pass`
  (W9 — sweeps `PROVISIONAL` and auto-resolves
  per §2.6 §3.2). Plus `apply_manual_operator_resolution`
  (§2.6 §3.2 manual operator path used by W8
  burst-review queue).
- **Persists:** Via injected `BetRecordStorage` —
  `update_settlement_state`,
  `update_reconciliation_bookkeeping`,
  `update_last_read_market_state`.
- **Exposes (`__all__`):**
  `DEFAULT_AGE_THRESHOLD_SECONDS` (300s),
  `DEFAULT_PAST_WINDOW_SECONDS` (1800s),
  `DEFAULT_SETTLEMENT_INTERVAL_SECONDS` (60s),
  `TERMINAL_SETTLEMENT_STATES`,
  `BetNotFoundError`,
  `InvalidSettlementTransitionError`,
  `InvalidTerminalStateError`,
  `ManualResolutionError`, `ManualSettlementScheduler`,
  `ProvisionalSettlementSurfacingPayload`,
  `ProvisionalTriggerSource`, `SettlementDecision`,
  `SettlementPassResult`,
  `SettlementProvisionalPassResult`,
  `SettlementReader`, `SettlementReasonCode`,
  `SettlementScheduler`, `SettlementState`
  (re-export), `SettlementStorageError`,
  `ThreadingSettlementScheduler`,
  `_resolve_provisional_for_bet`,
  `_resolve_settlement_for_bet`,
  `apply_manual_operator_resolution`,
  `run_provisional_resolution_pass`,
  `run_settlement_pass`.

#### `domain/pricing/__init__.py` (0 lines)

- **What:** Empty placeholder. DR-030 lists
  `domain/pricing/` as a target folder for "Live
  pricing cache" pure business logic.
- **Persists:** Nothing.
- **Exposes:** Nothing (empty `__init__.py`).
- **Note:** The live pricing implementation
  actually lives at
  `clients/betfair_client/v1/live_pricing.py`
  (REST + streaming) and the effective-odds
  synthesis lives at
  `workflows/bet_entry/v1/pricing.py`. The
  `domain/pricing/` folder is structurally
  reserved but unpopulated.

#### `domain/settlement/__init__.py` (0 lines)

- **What:** Empty placeholder. DR-030 lists
  `domain/settlement/` as a target folder for
  "Settlement worker" pure business logic.
- **Persists:** Nothing.
- **Exposes:** Nothing.
- **Note:** Settlement payout / state-machine
  logic actually lives at
  `workflows/bet_entry/v1/settlement.py` (1354
  lines) and the `MarketSettlement` Pydantic
  type lives at `clients/betfair_client/v1/settlement.py`.
  The `domain/settlement/` folder is structurally
  reserved but unpopulated.

### §1.2 — Brief §5.1 specific-question answers

**(a) Public path from `bets.settlement_state` →
cash returned per bet?**

Not shipped. The shipped surface populates
`bets.settlement_state` from
`SettlementDecision.new_state` via
`storage.update_settlement_state`
(`workflows/bet_entry/v1/settlement.py:751-759`)
and stores the three count fields
(`dead_heat_count`, `removed_runner_count`,
`unexpected_state_count`) alongside. There is
no "cash returned" function. There is no
`cash_returned_to_book` column on `bets`
(verbatim DDL above, `store/schema/bets.py:17-45`
— no such column). Balance-derivation read-side
has not shipped.

The closest call surface in the bet pillar is
`apply_manual_operator_resolution`
(`workflows/bet_entry/v1/settlement.py:1128-1227`),
which is called by the
`POST /api/v1/bets/provisional/{bet_id}/resolve`
endpoint (`ui/api/routers/provisional.py:316-383`)
— that endpoint sets the terminal settlement
state but does not compute a cash-flow figure.

**(b) Is `bets.realised_conversion_rate` populated
anywhere?**

No. The column exists on the `bets` table
(`store/schema/bets.py:25`) and the `BetRecord`
model (`domain/bets/__init__.py:278`). All shipped
writers pass `None`:
- `record_builder.py:279` —
  `realised_conversion_rate=None,  # W5 populates at settlement`
- `record_builder.py:352` — same for the soft-book
  record builder.

Tests assert it stays `None`
(`tests/workflows/bet_entry/v1/test_record_builder.py:92,219`).
W5 has not shipped — the field is a forward
placeholder.

**(c) Event-log scaffolding files anywhere?**

No. A repository-wide grep for `event_log`,
`events_log`, `append.only`, `supersedes_event`,
`bet_placed`, `bet_correction`, and the literal
`bet_settled` outside test files returns zero
production hits. The bet pillar persists into
mutable `bets` / `bet_legs` rows; the bet record
is updated in place on Trigger B, on
reconciliation, on settlement, and on operator
resolution. No `events` table, no `event_log`
module, no `supersedes_event_id` column, no
append-only persistence pattern.

**(d) Does `bet_legs` carry any mutable post-
placement state?**

Yes, two fields. The `bet_legs` table has
`matched_stake TEXT` and `matched_price REAL`
(`store/schema/bets.py:61-62`) — both nullable;
both are populated at log time on the hedge leg
from the `placeOrders` response. They are
written-once during the orchestrator's record-
builder pass (`record_builder.py:268-269,332-333`)
and the shipped storage layer does not update
them after insert — `update_match_status`
updates fields on the `bets` row only
(`store/repositories/bets.py:578-615`), and the
`bet_legs` table has no `UPDATE` SQL in the
shipped repository (verified by reading
`SQLiteBetRecordStorage` lines 452–846 — only
inserts).

So in practice `bet_legs` is write-once-from-
hedge-placement-flow; the columns are typed
nullable but the SQLite layer never rewrites
them.

**(e) Does the DR-026 market-context snapshot
land on `bets` columns as spec'd?**

No. DR-026 (`decisions.md:731-786`) names a
specific field set: best Betfair lay price + size,
best back price + size, total matched, snapshot
timestamp, stale flag, `bf_snapshot_unavailable`,
`bf_snapshot_aligned_to_placement`,
`late_scratch_between_snapshot_and_log` — all
captured on the bet record at log time
(`architecture.md §A.3`, lines 184–192).

A repo-wide grep for `bf_snapshot`,
`snapshot_timestamp`, `stale_flag`, `snapshot_age`,
`late_scratch_between`,
`bf_snapshot_aligned_to_placement`,
`bf_snapshot_unavailable` returns zero hits.
None of those columns exist on `bets` (verbatim
DDL above), nor on `bet_legs`.

The fields on `bet_legs` are Set B per DR-032 §4
(`betfair_event_name`, `betfair_market_name`,
`betfair_selection_name`, `betfair_event_venue`,
`betfair_event_sport`, `betfair_event_start_time`,
`betfair_implied_probability`) — those are
market-identity / display-name snapshots, not the
DR-026 price-and-volume snapshot. DR-026's
market-context snapshot is not implemented in the
shipped bet pillar.

Cross-reference: DR-026 has an "Open question for
Session 14 multi-agent review" (`decisions.md:786`)
about whether to drop inline snapshot storage
entirely. `v3_data_requirements.md §B.7 #1` and
`dr029_scope.md §2.8` reframe the bet schema along
the operational/analytical axis, naming this the
"bet-schema reframing" stream. The shipped code's
absence of DR-026 snapshot columns lines up with
the §2.8 reframing direction but DR-026 itself
remains the locked principle in `decisions.md`.

---

## §2 — Account pillar inventory (brief §5.2)

### §2.1 — Module-by-module

#### `domain/accounts/__init__.py` (114 lines)

- **What:** DR-022 vocabulary lock — three Pydantic
  v2 models (`Account`, `Book`, `AccountAtBook`).
  W11 v1 ships identity-only — no tier / phase,
  no isolation metadata, no ownership-cluster
  reference table (per W11 brief §1.2 / §1.3).
- **Persists:** Nothing (pure domain).
- **Exposes (`__all__`):** `Account`, `AccountAtBook`,
  `Book`.

**Model field lists (verbatim from source):**

`Account` (`domain/accounts/__init__.py:37-62`):
```
account_id: str
name: str
is_self: bool
active: bool = True
created_at: datetime
```

`Book` (`domain/accounts/__init__.py:65-83`):
```
book_id: str
name: str
ownership_cluster: str | None
platform: str | None
active: bool = True
```

`AccountAtBook` (`domain/accounts/__init__.py:86-111`):
```
account_at_book_id: str
account_id: str
book_id: str
active: bool = True
created_at: datetime
```

#### `store/schema/accounts.py` (135 lines)

- **What:** DDL + idempotent migration for three
  reference-data tables: `accounts`, `books`,
  `accounts_at_book`. Plus two partial indexes
  filtered on `active = 1`.
- **Persists:** Schema only.
- **Exposes:** `_ACCOUNTS_AT_BOOK_DDL`,
  `_ACCOUNTS_DDL`, `_BOOKS_DDL`,
  `_INDEX_ACCOUNTS_AT_BOOK_BY_ACCOUNT`,
  `_INDEX_ACCOUNTS_AT_BOOK_BY_BOOK`,
  `_add_column_if_missing`, `apply_migrations`.

**`accounts` table (`store/schema/accounts.py:35-43`):**
```
account_id   TEXT    PRIMARY KEY
name         TEXT    NOT NULL
is_self      INTEGER NOT NULL
active       INTEGER NOT NULL DEFAULT 1
created_at   TEXT    NOT NULL
```

**`books` table (`store/schema/accounts.py:45-53`):**
```
book_id            TEXT PRIMARY KEY
name               TEXT NOT NULL
ownership_cluster  TEXT
platform           TEXT
active             INTEGER NOT NULL DEFAULT 1
```

**`accounts_at_book` table (`store/schema/accounts.py:55-66`):**
```
account_at_book_id  TEXT    PRIMARY KEY
account_id          TEXT    NOT NULL
book_id             TEXT    NOT NULL
active              INTEGER NOT NULL DEFAULT 1
created_at          TEXT    NOT NULL
FOREIGN KEY (account_id) REFERENCES accounts(account_id)
FOREIGN KEY (book_id)    REFERENCES books(book_id)
UNIQUE (account_id, book_id)
```

Two indexes (`store/schema/accounts.py:68-80`):
```
idx_accounts_at_book__account_id (account_id) WHERE active = 1
idx_accounts_at_book__book_id    (book_id)    WHERE active = 1
```

#### `store/repositories/accounts.py` (419 lines)

- **What:** SQLite repository for the three
  reference tables. Three row dataclasses
  (`AccountRow`, `BookRow`, `AccountAtBookRow`),
  one `RegisterResult` structured envelope, and
  the `SQLiteAccountsStorage` class.
- **Persists:** `accounts`, `books`,
  `accounts_at_book` rows. Departs from the
  `bets.py` connection pattern by holding a
  single connection for the storage instance's
  lifetime; enforces `PRAGMA foreign_keys = ON`
  per-connection (lines 124–131).
- **Exposes (`__all__`):** `AccountAtBookRow`,
  `AccountRow`, `BookRow`, `RegisterResult`,
  `SQLiteAccountsStorage`.

**`SQLiteAccountsStorage` public methods
(`store/repositories/accounts.py:115-345`):**

```python
__init__(self, db_path: str | Path)
close(self) -> None
# accounts CRUD
create_account(self, row: AccountRow) -> None
get_account(self, account_id: str) -> AccountRow | None
list_active_accounts(self) -> list[AccountRow]
archive_account(self, account_id: str) -> bool
# books CRUD
register_book(self, row: BookRow) -> None
get_book(self, book_id: str) -> BookRow | None
list_active_books(self) -> list[BookRow]
archive_book(self, book_id: str) -> bool
# accounts_at_book CRUD
register_account_at_book(self,
    row: AccountAtBookRow) -> RegisterResult
get_account_at_book(self, account_at_book_id: str)
    -> AccountAtBookRow | None
get_account_at_book_by_composite_key(self,
    account_id: str, book_id: str)
        -> AccountAtBookRow | None
list_active_accounts_at_book_for_account(self,
    account_id: str) -> list[AccountAtBookRow]
list_active_accounts_at_book_for_book(self,
    book_id: str) -> list[AccountAtBookRow]
close_account_at_book(self,
    account_at_book_id: str) -> bool
```

### §2.2 — Brief §5.2 specific-question answers

**(a) Does the accounts pillar match DR-022?**

Yes for vocabulary. All three entities are tabled:
`accounts` (real people), `books` (bookmaker
organisations), `accounts_at_book` (registrations).
The composite `(account_id, book_id)` uniqueness
constraint is enforced at the schema level
(`store/schema/accounts.py:64`). The `is_self`
flag on `accounts` discriminates Tim's own
accounts from custodian accounts, matching the
DR-022 framing.

Forward-looking fields named in DR-022 framings
(tier, phase) — not shipped. Per the W11 brief
deferral (`domain/accounts/__init__.py:1-28`
docstring).

**(b) Does `bets.account_at_book_id` point at a
real `account_at_book` primary key?**

By column shape, yes — both are TEXT and the W11
brief explicitly aligned the new
`accounts_at_book.account_at_book_id` column to
match the existing `bets.account_at_book_id` shape
(`domain/accounts/__init__.py:89-95` docstring).
By FK enforcement, no — the `bets` schema declares
no `FOREIGN KEY (account_at_book_id) REFERENCES
accounts_at_book(account_at_book_id)` clause
(`store/schema/bets.py:17-45`, verbatim above).
The `bets` table has exactly one `FOREIGN KEY`
clause and it is the `bet_legs(bet_id) REFERENCES
bets(bet_id)` line on `bet_legs`
(`store/schema/bets.py:64`).

The W11 brief docstring at
`domain/accounts/__init__.py:89-95` says: "W11
closes the dangling-reference gap by giving the
value a real referent table; FK enforcement on
`bets.account_at_book_id` is deferred per W11
brief §1.2 (separate hygiene decision once the
new table is seeded)." So this is a known
deferred-FK-enforcement item.

Additionally, `bets.py` repository sets
`PRAGMA foreign_keys = ON` per-connection
(`store/repositories/bets.py:470`), but only the
`bet_legs(bet_id)` FK is present in the schema to
be enforced. The `accounts.py` repository sets
`PRAGMA foreign_keys = ON` too
(`store/repositories/accounts.py:130`).

**(c) Drift between shipped shape and architecture.md
§A.1?**

`architecture.md §A.1` (lines 53–88) names eight
v3-side entities — `account`, `account_at_book`,
`book`, `ownership_cluster`, `platform`, `promo`,
`promo_template` — plus `account_arrangement` and
three Slice-5 cash-flow reference tables
(`account_holders`, `payees`, `warning_catalogue`).

Shipped reality: three tables (`accounts`, `books`,
`accounts_at_book`). `ownership_cluster` is a TEXT
column on `books`, not a separate table; the W11
brief §1.2 names this as a deliberate
simplification. `platform` is a TEXT column on
`books`. Missing entirely from shipped state:
`promo`, `promo_template`, `account_arrangement`,
`account_holders`, `payees`, `warning_catalogue`.

Per the brief §5.2 framing this is a §5.9
missing-from-spec item; surfaced verbatim in §9
below.

---

## §3 — Clients inventory (brief §5.3)

### §3.1 — `clients/betfair_client/v1/`

#### Module list with line counts

```
__init__.py             183 lines  (public re-exports)
_audit.py               120 lines  (audit log shapes)
_auth.py                 54 lines  (auth provider Protocol)
_clock.py                14 lines  (Adelaide-local clock)
_connection.py          111 lines  (REST client + rate limit)
_errors.py               96 lines  (envelope-mapped errors)
_stream_parser.py       396 lines  (streaming-frame parser)
_translation.py         737 lines  (raw API ↔ Pydantic)
account_funds.py         92 lines  (§9.6 account funds)
cancellation.py         143 lines  (§11.2 bet cancellation)
consumer.py             155 lines  (consumer-side helpers)
current_orders.py       162 lines  (§9.8 order-state)
envelope.py             115 lines  (typed envelope §8)
identity.py              78 lines  (§9.5 identity check)
live_pricing.py         204 lines  (§9.1 live pricing)
market_catalogue.py     135 lines  (§9.7 marketCatalogue)
placement.py            283 lines  (§11.1 bet placement)
replacement.py          150 lines  (§11.3 bet replacement)
scheduled_time.py        72 lines  (§9.4 scheduled time)
settlement.py           118 lines  (§9.2 settlement reads)
sports_lines.py          91 lines  (§9.3 sports lines)
streaming.py            640 lines  (§10 streaming surface)
```

#### Public surface (re-exports from `__init__.py:103-183`)

**Envelope (§8):** `BetfairReadUnavailableReason`,
`BetfairWriteUnavailableReason`, `EnvelopeStatus`,
`FreshEnvelope`, `ReadEnvelope`, `StaleEnvelope`,
`UnavailableReadEnvelope`, `UnavailableWriteEnvelope`,
`WriteEnvelope`.

**Connection / auth / audit:** `AuditLogEntry`,
`AuditLogSink`, `AuthProvider`, `BetSideStr`,
`BetfairRestClient`, `BetfairRestError`,
`MemoryAuditLogSink`, `MockAuthProvider`,
`PersistenceTypeStr`, `RateLimitBudget`,
`StdoutAuditLogSink`, `Transport`, `WriteOperation`,
`WriteOutcome`.

**Read surfaces (§9):**
- §9.1 live pricing — `market_prices()`,
  `runner_best_prices()`, `MarketPrices`,
  `PriceLevel`, `RunnerBestPrices`, `RunnerPrices`.
- §9.2 settlement — `market_settlement()`,
  `MarketSettlement`, `MarketStatus`,
  `RunnerSettlement`, `RunnerSettlementStatus`.
- §9.3 sports lines — `sports_market_variants()`,
  `SportsMarketType`, `SportsMarketVariant`.
- §9.4 scheduled time — `market_scheduled_time()`,
  `MarketScheduledTime`.
- §9.5 identity — `identity_check()`, `IdentityCheck`.
- §9.6 account funds — `get_account_funds()`,
  `AccountFunds`.
- §9.7 market catalogue — `get_market_catalogue()`,
  `MarketCatalogue`, `RunnerCatalogue`.
- §9.8 order-state — `list_current_orders()`,
  `OrderRecord`, `OrderStateList`.

**Streaming (§10):** `MarketSubscriptionScope`,
`MarketUpdate`, `MatchedPositionLevel`,
`OrderPosition`, `OrderUpdate`, `StreamingClient`,
`StreamingConnectionState`, `StreamingStatus`,
`UnmatchedOrder`.

**Write surfaces (§11):**
- §11.1 placement — `place_bet()`,
  `BetPlacementResult`, `BetSide`, `PersistenceType`.
- §11.2 cancellation — `cancel_bet()`,
  `BetCancellationResult`.
- §11.3 replacement — `replace_bet()`,
  `BetReplacementResult`.

**Consumer-side reading paths (W3 §5.4):**
`BetfairClient`, `check_identity()`,
`get_live_market_prices()`,
`get_market_scheduled_time()`,
`get_market_settlement()`, `get_runner_best_prices()`,
`get_sports_market_variants()`.

### §3.2 — `clients/vps_client/v1/`

#### Module list with line counts

```
__init__.py                    70 lines  (public re-exports)
_clock.py                      14 lines  (Adelaide-local clock)
_connection.py                 57 lines  (SQLAlchemy engine)
_errors.py                     31 lines  (envelope error mapper)
bracketing.py                 256 lines  (§9.4 bracketing)
envelope.py                    78 lines  (typed envelope §8)
identifier_resolution.py      148 lines  (§9.6 identifier passive check)
race_metadata.py              163 lines  (§9.1 race metadata)
results.py                    193 lines  (§9.3 results)
runner_metadata.py            237 lines  (§9.2 runner metadata)
starting_price.py             197 lines  (§9.5 BSP)
```

#### Public surface (re-exports from `__init__.py:10-70`)

```
race_metadata()          — §9.1 race metadata reads
runner_metadata()        — §9.2 runner metadata reads
race_runners()           — §9.2 (race-level runner list)
race_results()           — §9.3 results reads
race_bracketing()        — §9.4 bracketing reads
runner_bsp()             — §9.5 BSP / sp_near / sp_far
identity_resolve()       — §9.6 identifier resolution
```

Plus the typed envelope: `Envelope`, `EnvelopeStatus`,
`FreshEnvelope`, `StaleEnvelope`,
`UnavailableEnvelope`, `UnavailableReason`.

Plus the payload Pydantic models: `BracketSnapshot`,
`BracketingSeries`, `BspReading`, `IdentityResolution`,
`PriceLadderLevel`, `RaceCode`, `RaceMetadata`,
`RaceResults`, `ResultSource`, `RunnerMetadata`,
`RunnerResult`, `RunnerSnapshot`, `ScratchingStatus`,
`StewardsStatus`.

### §3.3 — Brief §5.3 specific-question answers

**(a) Contract surface stable / locked? Drift between
contract spec and shipped surface?**

Both contracts at v1.0 per Sessions 76–80
(`vps_client_contract.md` §6 and `betfair_client_contract.md`
§6 version histories).

The contract section headers (`grep` from the
contract files, lines cited above) match the shipped
module organisation 1:1:

`betfair_client_contract.md` contract section → shipped
module mapping:
- §9.1 operational live-pricing → `live_pricing.py`
- §9.2 settlement → `settlement.py`
- §9.3 sports-line query → `sports_lines.py`
- §9.4 scheduled-time → `scheduled_time.py`
- §9.5 identifier-resolution → `identity.py`
- §9.6 account funds → `account_funds.py`
- §9.7 market catalogue → `market_catalogue.py`
- §9.8 order-state → `current_orders.py`
- §10 streaming → `streaming.py`
- §11.1 placement → `placement.py`
- §11.2 cancellation → `cancellation.py`
- §11.3 replacement → `replacement.py`
- §8 typed envelope → `envelope.py`

`vps_client_contract.md` contract section → shipped
module mapping:
- §9.1 race metadata → `race_metadata.py`
- §9.2 runner metadata → `runner_metadata.py`
- §9.3 results → `results.py`
- §9.4 bracketing → `bracketing.py`
- §9.5 BSP → `starting_price.py`
- §9.6 identifier-resolution → `identifier_resolution.py`
- §8 typed envelope → `envelope.py`

No drift found between contract surface and shipped
public surface at the section / file granularity.
Function-signature parity was not exhaustively
verified per individual surface (out of scope at the
inventory layer — would require contract-by-contract
signature audit), but the section/module mapping is
clean.

**Storage location of the contract files (carry-forward):**
both contracts still live at
`bethub-rebuild/dr029/2_7_api_contract_versioning/`.
DR-030 §Scope (`decisions.md:1022-1024`) explicitly
flags the relocation: "Contract files
(`vps_client_contract.md`, `betfair_client_contract.md`)
relocate from `dr029/2_7_api_contract_versioning/` to
v3's `contracts/` folder as part of v3 build proper
administrative cleanup." Surfaced in §7 below.

**(b) Client methods exposed beyond what the contract
documents?**

The `consumer.py` module at
`clients/betfair_client/v1/consumer.py` exposes
seven helper functions on top of the underlying
surface modules: `BetfairClient` (container),
`check_identity`, `get_live_market_prices`,
`get_market_scheduled_time`, `get_market_settlement`,
`get_runner_best_prices`, `get_sports_market_variants`.

The contract's §9 read-surface enumeration covers
the underlying calls (e.g., `market_prices`,
`market_settlement`). The `get_*` and
`check_identity` helpers in `consumer.py` are
described in the contract as "consumer-side
reading paths" — `__init__.py:175-182` re-exports
them under that label. The shipped `__init__.py`'s
re-export of those helpers is identified as
"W3 §5.4" in the `__init__.py` comment.

No additional uncatalogued client methods were
surfaced beyond the seven `consumer.py` helpers
plus the per-surface entry points. The `_*`
private modules (`_audit.py`, `_auth.py`,
`_clock.py`, `_connection.py`, `_errors.py`,
`_stream_parser.py`, `_translation.py`) are not
re-exported and are internal per contract §7 /
§14.

**(c) Cross-DB integration boundary — DR-028
respected?**

Yes. The shipped state matches DR-028's three
structural disciplines:
- **No race-data caching in v3** — verified by repo-
  wide grep for race-side field names (`race_class`,
  `track_condition`, `finish_position`, `bsp` outside
  the `vps_client` parser modules); no such columns
  exist on `bets`, `bet_legs`, `accounts`, `books`,
  or `accounts_at_book`. No `races` / `runners` table.
- **No race-data denormalisation onto v3 entities**
  — Set B fields on `bet_legs` are
  market-identity facts (event name, market name,
  selection name, venue, sport, start time) per
  DR-032 §4, not race-data facts.
- **No second integration point** — only one path
  reads capture.db: the `vps_client.v1` package
  (uses `sqlalchemy.text` against capture.db via
  `_connection.py`'s SQLAlchemy `Engine` / `Connection`).
  Repo-wide grep for `sqlalchemy` outside
  `vps_client.v1` and `tests/test_skeleton.py`
  returns zero hits — no other module talks to
  capture.db.

A subtle structural note: `vps_client` uses
SQLAlchemy Core (`from sqlalchemy import text`,
`create_engine`, `Connection`, `Engine`), reads
capture.db directly. The `bethub-v3` store/ side
uses raw `sqlite3` — see §6 below and the DR-031
drift row in §8.

---

## §4 — Reconciliation and settlement inventory (brief §5.4)

### §4.1 — Module-by-module

#### `workflows/bet_entry/v1/reconciliation.py` (660 lines)

Already inventoried in §1.1 — periodic
match-state reconciliation worker (W6 v1). Public
surface enumerated above.

Key internal entry points:
- `_resolve_one(*, record, adapter) -> ResolutionDecision`
  (lines 147–377) — pure read-side resolver.
- `run_reconciliation_pass(*, storage, adapter,
   age_threshold_seconds, max_results, now)
   -> ReconciliationPassResult` (lines 385–521).
- `_write_bookkeeping(*, storage, bet_id,
   last_reconciled_at)` (lines 524–547).

#### `workflows/bet_entry/v1/settlement.py` (1354 lines)

Already inventoried in §1.1 — periodic settlement-
state worker (W6.5 + W9) plus manual operator
path (W8). Public surface enumerated above.

Key internal entry points:
- `_resolve_settlement_for_bet(*, record,
   settlement_reader) -> SettlementDecision`
  (lines 319–486) — PENDING-pass resolver.
- `_resolve_provisional_for_bet(*, record,
   settlement_reader) -> SettlementDecision`
  (lines 494–690) — W9 PROVISIONAL-pass resolver.
- `run_settlement_pass(*, storage,
   settlement_reader, age_threshold_seconds,
   max_results, now) -> SettlementPassResult`
  (lines 698–849).
- `run_provisional_resolution_pass(*, storage,
   settlement_reader, max_results, now)
   -> SettlementProvisionalPassResult`
  (lines 914–1081).
- `apply_manual_operator_resolution(*, bet_id,
   new_state, operator_reason, storage, now)
   -> BetRecord` (lines 1128–1227).
- `_write_settlement_bookkeeping(...)` (lines 852–875).
- `_persist_last_read_market_state(...)` (lines 878–906).

#### `domain/settlement/__init__.py` (0 lines)

Empty placeholder. See §1.1 note above.

### §4.2 — Brief §5.4 specific-question answers

**(a) Reconciliation gap detection — function for
"expected book balance" vs "actual book balance"?**

Not shipped. `architecture.md §A.9` (line 534)
names "Reconciliation gap per book" as the
operator-reported book balance vs computed
at-book balance derivation; the six reconciliation
surfaces are enumerated at `architecture.md
§A.9` (lines 551–558). No shipped module computes
an at-book balance — no balance derivation at all
exists. The shipped `reconciliation.py` is
specifically *match-state* reconciliation (the
disambiguation pass that resolves
`PROVISIONAL` / `PROVISIONAL_PENDING` against
`listCurrentOrders` + `market_settlement`), not
cash-reconciliation.

The architecture.md surface for "reconciliation
gap per book" is not implemented. Surfaced in §9
below as a missing-from-spec item.

**(b) Settlement payout computation — name the
function the balance derivation will need to call.**

Not shipped. There is no "settlement payout"
function — no module computes `cash_returned_to_book`
from a settled bet. The shipped settlement worker
(`run_settlement_pass`, `_resolve_settlement_for_bet`)
transitions the `bets.settlement_state` field
from `PENDING` to one of `SETTLED_WON` /
`SETTLED_LOST` / `VOIDED` / `PROVISIONAL` and
populates three count fields (`dead_heat_count`,
`removed_runner_count`, `unexpected_state_count`)
— no dollar-amount payout is computed or stored.
Balance derivation would have nothing to read.

**(c) Settlement-state mutation path — when does
`bets.settlement_state` get written?**

Two paths in shipped code:

1. **Periodic settlement worker**
   (`workflows/bet_entry/v1/settlement.py:751-759`):
   `storage.update_settlement_state(bet_id,
   settlement_state=decision.new_state.value,
   dead_heat_count=..., removed_runner_count=...,
   unexpected_state_count=...)` called from inside
   `run_settlement_pass` (PENDING population) and
   `run_provisional_resolution_pass`
   (`workflows/bet_entry/v1/settlement.py:976-982`).
2. **Manual operator path** (W8) at
   `workflows/bet_entry/v1/settlement.py:1193-1199`
   — `apply_manual_operator_resolution` writes
   the operator-chosen terminal state from the
   `POST /api/v1/bets/provisional/{bet_id}/resolve`
   endpoint.

At bet entry time (W4 path: `place_hedge` and
`log_soft_book_bet`), `settlement_state` is not
populated — `record_builder.build_hedge_bet_record`
and `build_soft_book_bet_record` do not pass a
value, so the Pydantic default `None` is used
(`domain/bets/__init__.py:310`). On write, the
`bet_store_adapter.to_rows` function maps `None`
through to the SQLite column as NULL
(`workflows/bet_entry/v1/bet_store_adapter.py:68-72`).

The settlement worker then transitions a row from
NULL settlement_state to `PENDING` … wait, the
`run_settlement_pass` filter is
`SettlementState.PENDING.value`
(`workflows/bet_entry/v1/settlement.py:732`); a
record with NULL `settlement_state` would not be
swept by the PENDING pass. The orchestrator brief
notes (W4 brief §3.1) that bets land with NULL
`settlement_state` at v1; W7 was named as the
write-time setter ("The orchestrator populates at
write-time in W7 (out of scope here)" —
`domain/bets/__init__.py:308`). Whether W7 ships
this write-side population is not visible from the
shipped record-builder code (W7 lands the FastAPI
substrate and the burst-review queue — see §5
below — but does not appear to set
`settlement_state` at bet entry).

This is a structural observation, not a fitness
judgement.

**(d) Hedge state — is DR-025 hedge classification
shipped?**

No. DR-025 (`decisions.md:684-725`) names five
terminal states (`hedged`, `hedge_partial`,
`hedge_failed`, `unhedged_deliberate`,
`unhedged_oversight`) plus one transient
(`unhedged_unclassified`). It also names a
`hedge_state_classification` event type per
`architecture.md §A.6` (line 410) with
operator-explicit / auto-classified /
auto-resolved-timeout writing paths.

Repo-wide grep for `hedge_state` /
`unhedged_deliberate` / `unhedged_oversight` /
`unhedged_unclassified` / `hedge_failed` outside
the docstring of `bet_entry/v1/orchestrator.py`
returns zero hits in production code. No
`hedge_state` column on `bets`. No
`hedge_state_classification` events. No
classification worker. No auto-resolve-at-
settlement+24h logic.

`MatchStatus` (the five-value enum on `bets.match_status`)
is *match*-state — "did the placeOrders book the
hedge fully / partially / not at all" — not
*hedge*-classification — "did the operator
intend to hedge / did it succeed". DR-025's
states are not the same as match-states.

Surfaced in §9 below.

**(e) Were W6 / W6.5 / W9 shipped per their briefs?**

Apparently yes for all three, given:
- W6 (broader-sync reconciliation worker)
  shipped — see `workflows/bet_entry/v1/reconciliation.py`
  (660 lines, 28 tests passing per the brief
  baseline at W11.1 close).
- W6.5 (settlement-state worker) shipped — see
  `workflows/bet_entry/v1/settlement.py`'s
  `run_settlement_pass` (lines 698–849, sweeps
  PENDING) plus the `SettlementState` enum and
  the four count fields on `bets`.
- W9 (last-read market state) shipped — see
  `workflows/bet_entry/v1/settlement.py`'s
  `run_provisional_resolution_pass` (lines
  914–1081), the `_persist_last_read_market_state`
  helper (lines 878–906), and the
  `last_read_market_state` column on `bets`
  (`store/schema/bets.py:43`).

The brief's §1 / §9.5 directive "No tests run"
applies — these are structural reads, not
test-suite verifications.

---

## §5 — UI surface inventory (brief §5.5)

### §5.1 — Backend (`ui/api/`)

```
ui/api/__init__.py            (empty)
ui/api/config.py              52 lines  Settings (pydantic-settings)
ui/api/main.py                52 lines  create_app() + lifespan stub
ui/api/dependencies/          (empty __init__.py — 6 lines)
ui/api/middleware/            (empty __init__.py — 6 lines)
ui/api/routers/__init__.py    (re-exports)
ui/api/routers/health.py      41 lines  GET /api/health
ui/api/routers/provisional.py 395 lines  GET + POST /api/v1/bets/provisional[/.../resolve]
```

**Endpoints (verbatim from the router decorators):**
- `GET /api/health` (`ui/api/routers/health.py:34`)
  → `HealthResponse{status: "ok", timestamp,
  version}`.
- `GET /api/v1/bets/provisional`
  (`ui/api/routers/provisional.py:266-270`)
  → `list[ProvisionalBetItem]`.
- `POST /api/v1/bets/provisional/{bet_id}/resolve`
  (`ui/api/routers/provisional.py:316-320`)
  → `ResolveResponse`. Body validated against
  `ResolveRequest` (`new_state: Literal["settled_won",
  "settled_lost", "voided"]`, `operator_reason: str | None`).

**FastAPI app composition (`ui/api/main.py:30-49`):**
- `create_app()` instantiates `FastAPI` with
  `docs_url="/api/docs"`, `redoc_url="/api/redoc"`,
  `openapi_url="/api/openapi.json"`.
- `CORSMiddleware` added with
  `allow_origins=settings.cors_origins`
  (default: `["http://localhost:5173"]`).
- Includes `health_router` and `provisional_router`
  under prefix `/api`.
- `lifespan` (lines 25–27) yields with no setup /
  teardown — settlement-worker / reconciliation-worker
  scheduler wiring is named as future work in the
  module docstring (W8+).

**Settings (`ui/api/config.py:34-42`):**
```
app_name: str = "BetHub v3"
version: str = PROJECT_VERSION  # read from pyproject.toml
cors_origins: list[str] = ["http://localhost:5173"]
environment: Literal["dev", "prod"] = "dev"
```
Environment prefix is `BETHUB_`.

### §5.2 — Frontend (`ui/web/src/`)

```
ui/web/src/App.tsx                              50 lines  (router + nav)
ui/web/src/main.tsx                              ~6 lines (entrypoint)
ui/web/src/index.css, App.module.css            (styling)
ui/web/src/api/client.ts                        TanStack Query setup
ui/web/src/api/provisional.ts                   provisional API binding
ui/web/src/api/types.ts                         generated API types
ui/web/src/components/ProvisionalBetModal.tsx   (resolve modal)
ui/web/src/components/ProvisionalBetModal.test.tsx
ui/web/src/components/ProvisionalBetModal.module.css
ui/web/src/routes/Health.tsx                    /health page
ui/web/src/routes/Health.test.tsx
ui/web/src/routes/Health.module.css
ui/web/src/routes/Provisional.tsx               /provisional page
ui/web/src/routes/Provisional.test.tsx
ui/web/src/routes/Provisional.module.css
ui/web/src/test/setup.ts                        (vitest setup)
```

**Routes (`ui/web/src/App.tsx:39-43`):**
- `/` → `<Navigate to="/provisional" replace />`
- `/provisional` → `<Provisional />`
- `/health` → `<Health />`

**Nav (`ui/web/src/App.tsx:20-32`):** "Burst review"
link → `/provisional`; "Health" link → `/health`.

`QueryClient` (`ui/web/src/App.tsx:8-18`) configured
with `staleTime: 0, retry: false` and per-query
overrides on the Provisional page.

### §5.3 — `workflows/burst_review/__init__.py` (0 lines)

Empty placeholder. The actual burst-review surface
shipped via the W8 brief lives in
`workflows/bet_entry/v1/settlement.py`
(`ProvisionalSettlementSurfacingPayload`,
`apply_manual_operator_resolution`) and
`ui/api/routers/provisional.py` (GET + POST
endpoints) + `ui/web/src/routes/Provisional.tsx`
(operator-facing page). The `workflows/burst_review/`
folder itself is structurally reserved.

### §5.4 — Brief §5.5 specific-question answers

**(a) Balance-display surfaces shipped?**

No. Repo-wide grep of `ui/api/routers/` and
`ui/web/src/` for `balance`, `cash`, `flow`, `BSP`,
`turnover` returns zero hits. The shipped UI is
two pages: `/health` (substrate smoke-test from
W7) and `/provisional` (burst-review queue from
W8). Neither reads or displays balances; neither
joins to capture.db.

**(b) What state does the UI read from `bethub-v3`
vs from `capture.db`?**

The UI reads only from `bethub-v3` (the shipped
SQLite at `BETHUB_DB_PATH` or the `<repo>/data/bethub.db`
default — `ui/api/routers/provisional.py:62-80`).
The two endpoints query the
`SQLiteBetRecordStorage` via the `get_storage`
dependency
(`ui/api/routers/provisional.py:83-92`). No
`vps_client` invocation in any `ui/api/` module
(verified by repo-wide grep — no `vps_client`
import in `ui/` at all).

The shipped UI does not depend on capture.db.

**(c) Reconciliation gap surface — shipped or not?**

Not shipped. The only "reconciliation" surfaces
shipped relate to **match-state reconciliation**
(W6 reconciliation worker) and **settlement-state
reconciliation** (W6.5 / W9 settlement worker). No
"cash reconciliation" surface, no "FB reconciliation"
surface, no "settlement reconciliation" surface
that compares operator-observed vs computed
at-book balance. None of the six reconciliation
surfaces named in `architecture.md §A.9`
(lines 551–558) are implemented in the UI.

The `/provisional` endpoint surfaces bets that
the settlement worker has parked into
`SettlementState.PROVISIONAL` for operator
disambiguation — that is operator-driven
*settlement-state* triage, not balance
reconciliation.

**(d) Burst review scaffold — what's shipped vs what's
spec'd in `architecture.md`?**

Shipped:
- One endpoint
  (`GET /api/v1/bets/provisional`) returning bets
  in `SettlementState.PROVISIONAL`.
- One endpoint
  (`POST /api/v1/bets/provisional/{bet_id}/resolve`)
  to transition a bet to a terminal state.
- One React route (`/provisional`) with a
  resolve modal (`ProvisionalBetModal.tsx`).
- The `ProvisionalSettlementSurfacingPayload`
  data contract (`workflows/bet_entry/v1/settlement.py:254-285`).

Spec'd in `architecture.md` but not shipped:
- DR-017 (lines 388–390): "Burst Review is a
  first-class workflow … shows all bets logged
  during the burst, ordered by time, with quick-
  edit on every field. Includes a 'sanity check'
  pass that flags potential errors (multiple bets
  to same account in short window, stake outliers,
  etc.) for operator review."
- `architecture.md §A.7` (lines 450–453):
  "Burst Review cascade events view (day-one):
  Shows every cascaded credit with: original
  event, triggering settlement (if any),
  recomputed event, path, net balance impact."
- DR-025 (lines 711–713): "The Burst Review
  surfaces unclassified bets at two stages:
  'unclassified — pending settlement' … and
  'unclassified — ready to classify' …".
- DR-026 (line 768): "Reconciliation against
  future-captured data" view.
- Various reconciliation-surface views per
  `architecture.md §A.9` (lines 552–558).

What's shipped is one slice of one of the spec'd
burst-review surfaces (settlement-state
disambiguation only). The bulk of the
architecture.md / DR-017 / DR-025 / DR-026
burst-review surface is not on disk.

---

## §6 — Operations / contracts / config inventory (brief §5.6)

### §6.1 — `ops/`

```
ops/__init__.py    (empty, 0 lines)
```

Zero modules. No cron, no scripts, no deploy
configuration, no ops_log module, no rate-limit
monitoring. The folder is structurally reserved
per DR-030 (`decisions.md:976`).

### §6.2 — `contracts/`

```
contracts/__init__.py    (empty, 0 lines)
```

Zero modules. Per DR-030's §Scope amendment
(`decisions.md:1022-1024`): "Contract files
(`vps_client_contract.md`, `betfair_client_contract.md`)
relocate from `dr029/2_7_api_contract_versioning/`
to v3's `contracts/` folder as part of v3 build
proper administrative cleanup." Both contract
files still live at
`bethub-rebuild/dr029/2_7_api_contract_versioning/`
(verified by repo-wide find). The contracts folder
in v3 is empty.

### §6.3 — `pyproject.toml` (verbatim project section)

```toml
[project]
name = "bethub"
version = "0.1.0"
description = "BetHub v3 — Australian bookmaker
   account management platform"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "alembic",
    "betfairlightweight",
    "httpx",
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "ruff",
    "import-linter",
    "mypy",
]
```

Lint config (`pyproject.toml:26-35`): `ruff` with
`line-length = 100`, `target-version = "py312"`,
`select = ["E", "F", "I", "B", "UP", "N"]`,
`ignore = ["UP042", "UP046"]`.

mypy config (`pyproject.toml:37-43`): `strict = true`,
`plugins = ["pydantic.mypy"]`,
`betfairlightweight` import overridden to
`ignore_missing_imports = true`.

pytest config (`pyproject.toml:45-48`):
`testpaths = ["tests"]`, `asyncio_mode = "auto"`,
`addopts = "-v"`.

### §6.4 — `.importlinter` (verbatim)

Five contracts (`bethub-v3/.importlinter:12-67`):

1. `[importlinter:contract:layers]` — DR-030
   layered architecture. Layers:
   `ui | ops` → `workflows` → `domain | store | clients`
   → `contracts`.
2. `[importlinter:contract:domain-pure]` — `domain`
   forbidden from importing `clients`, `store`,
   `workflows`, `ui`, `ops`, `contracts`.
3. `[importlinter:contract:store-pure]` — `store`
   forbidden from importing `clients`, `domain`,
   `workflows`, `ui`, `ops`, `contracts`.
4. `[importlinter:contract:contracts-leaf]` —
   `contracts` forbidden from importing anything
   else.
5. `[importlinter:contract:workflows-independent]`
   — `workflows.bet_entry` and
   `workflows.burst_review` are independent.

`[importlinter]` root packages: `clients`, `store`,
`domain`, `workflows`, `ui`, `ops`, `contracts`,
`tests`.

Per the brief's reference to W11.1 close: 5 / 0
contracts kept.

### §6.5 — Brief §5.6 specific-question answers

**(a) DR-006 (operations log first-class) — is there
an `ops_log` table, an `ops_log` module, anything?**

No. `ops/__init__.py` is empty (0 lines). No
`ops_log` table in `store/schema/`. Repo-wide
grep for `ops_log` / `operations_log` returns
zero hits in production code. DR-006
(`decisions.md:67-75`) is not implemented.

**(b) DR-030 (repo layout / module-boundary
discipline) — do contracts in `.importlinter`
match boundaries on disk?**

Yes. The top-level folder layout matches DR-030's
locked stance exactly: `clients/` (with
`betfair_client/` and `vps_client/`), `store/`
(with `schema/` and `repositories/`), `domain/`
(with `bets/`, `pricing/`, `settlement/`,
`accounts/` — note `accounts/` is shipped per
W11 but is not in DR-030's original top-level
layout), `workflows/` (with `bet_entry/v1/` and
`burst_review/`), `ui/` (with `api/` and `web/`),
`ops/`, `contracts/`, `tests/`. The five
`.importlinter` contracts encode the layered
arrows in DR-030 (`decisions.md:982-993`)
directly.

Per W11.1 close, all five contracts kept (5 / 0)
— the brief's reference baseline.

One forward-looking note: DR-030's layout listing
includes `domain/pricing/` and `domain/settlement/`
as concrete folders for pure business logic, but
both are empty placeholders (see §1.1). The
pricing math and settlement state-machine live
in `workflows/bet_entry/v1/pricing.py` and
`workflows/bet_entry/v1/settlement.py` respectively.
This is a structural inversion of DR-030's intent
("`domain/` is pure. No DB access, no external API
calls. … This is where regression test coverage …
lands first because it's the cheapest place to
test" — `decisions.md:1000`) — those modules sit
under `workflows/` rather than `domain/`. Surfaced
in §8 below.

**(c) DR-031 (tech stack) — is SQLAlchemy Core in
use anywhere?**

Partial divergence with two distinct cases:

Case 1 — `clients/vps_client/v1/` USES SQLAlchemy
Core. Eight modules import `from sqlalchemy import
text` and `from sqlalchemy.exc import OperationalError`:
- `_connection.py` — `create_engine`, `Connection`,
  `Engine` for capture.db.
- `_errors.py` — `OperationalError`.
- `bracketing.py`, `identifier_resolution.py`,
  `race_metadata.py`, `results.py`,
  `runner_metadata.py`, `starting_price.py` — use
  `text()` for parameterised SQL against capture.db.

This matches DR-031's "SQLAlchemy Core (not ORM)"
lock for at least the capture.db read path.

Case 2 — `store/` (the v3 operational store)
uses raw `sqlite3`, not SQLAlchemy Core. Verified
by repo-wide grep — zero `sqlalchemy` imports in
`store/`. `store/schema/bets.py` uses raw DDL
strings; `store/schema/accounts.py` uses
`conn.executescript`; `store/repositories/bets.py`
and `store/repositories/accounts.py` use
`sqlite3.connect` directly and write parameterised
SQL with `?` placeholders.

The shipped state matches what W11 brief §5.3
flags explicitly in the
`store/repositories/accounts.py:10-13`
docstring: "raw `sqlite3` (not SQLAlchemy Core —
the brief carries the existing v3 raw-sqlite3
pattern forward and defers DR-031's SQLAlchemy
Core lock to a later store-layer migration)."
Similar deferral notes appear in
`store/schema/bets.py:80-84` for Alembic
adoption.

W11 brief §3.2's flag of this divergence
(referenced in the pre-W14 brief §5.6(c)) is
confirmed still divergent.

**(d) Pydantic v2 — load-bearing per DR-031;
confirm domain models use Pydantic v2 patterns.**

Confirmed. Every domain / workflow / client
model uses `from pydantic import BaseModel,
ConfigDict, Field, computed_field`, with
`model_config = ConfigDict(frozen=True)` as the
default pattern. Pydantic v2 specific patterns
observed:
- `model_config = ConfigDict(frozen=True)` —
  `domain/bets/__init__.py:228, 265`,
  `domain/accounts/__init__.py:56, 78, 105`,
  `workflows/bet_entry/v1/models.py:39, 63, 86,
  115, 132`, and many more.
- `model_validator(mode="after")` —
  `workflows/bet_entry/v1/pricing.py:73`,
  `workflows/bet_entry/v1/staking.py:215`.
- `@computed_field` decorator —
  `domain/bets/__init__.py:334-355`.
- `MarketSettlement.model_validate_json(...)`
  parsing — `ui/api/routers/provisional.py:289`.
- `model_dump_json()` /
  `model_dump(mode="json")` — used in
  `workflows/bet_entry/v1/settlement.py:897`,
  `workflows/bet_entry/v1/orchestrator.py:1385,
  1406`.
- `pydantic-settings` (`BaseSettings`) used at
  `ui/api/config.py:21, 34`.

The `tests/test_skeleton.py:49-54` asserts
`pydantic.VERSION.startswith("2.")` as a
substrate gate.

`pyproject.toml` declares `pydantic` and
`pydantic-settings` as dependencies. DR-031
amendment 2026-05-08 (Session 107) pinned
specific versions: pydantic 2.13.3,
pydantic-settings 2.14.0 — these aren't pinned in
`pyproject.toml` itself but the amendment names
the W7-shipped versions.

DR-031's Pydantic v2 lock is implemented.

---

## §7 — Tests inventory (brief §5.7)

### §7.1 — Per-pillar test-function counts

Counted by `^\s*(async )?def test_` in
`tests/`:

```
pillar bucket                       test fns
clients/betfair_client/             197
clients/vps_client/                  51
store/repositories/                  42
workflows/bet_entry/                218
ui/api/                              19
misc (test_skeleton.py)               6
TOTAL                               533
```

Note: pytest's collected-test count expands
`@pytest.mark.parametrize` entries, so the
collected-test count is higher than 533. The
brief's reference baseline ("549 tests passing
per W11.1 close") is the pytest collection
count, not the function-definition count; this
report does not run tests per §9.5.

### §7.2 — Test file paths (sample)

```
tests/__init__.py
tests/conftest.py                                     (empty)
tests/test_skeleton.py                                6 tests
tests/clients/betfair_client/v1/conftest.py
tests/clients/betfair_client/v1/test_account_funds.py      8
tests/clients/betfair_client/v1/test_audit.py              7
tests/clients/betfair_client/v1/test_cancellation.py       4
tests/clients/betfair_client/v1/test_consumer.py          10
tests/clients/betfair_client/v1/test_current_orders.py    14
tests/clients/betfair_client/v1/test_envelope.py          12
tests/clients/betfair_client/v1/test_error_mapping.py     10
tests/clients/betfair_client/v1/test_identity.py           3
tests/clients/betfair_client/v1/test_live_pricing.py       9
tests/clients/betfair_client/v1/test_market_catalogue.py  12
tests/clients/betfair_client/v1/test_placement.py          6
tests/clients/betfair_client/v1/test_replacement.py        3
tests/clients/betfair_client/v1/test_scheduled_time.py     3
tests/clients/betfair_client/v1/test_settlement.py         6
tests/clients/betfair_client/v1/test_sports_lines.py       4
tests/clients/betfair_client/v1/test_strategy_tag.py       5
tests/clients/betfair_client/v1/test_stream_parser.py     27
tests/clients/betfair_client/v1/test_streaming.py         34
tests/clients/betfair_client/v1/test_streaming_blocks_writes.py  8
tests/clients/betfair_client/v1/test_translation.py       12
tests/clients/vps_client/v1/conftest.py
tests/clients/vps_client/v1/test_bracketing.py             8
tests/clients/vps_client/v1/test_envelope.py               7
tests/clients/vps_client/v1/test_error_mapping.py          4
tests/clients/vps_client/v1/test_identifier_resolution.py  5
tests/clients/vps_client/v1/test_race_metadata.py          7
tests/clients/vps_client/v1/test_results.py                5
tests/clients/vps_client/v1/test_runner_metadata.py        9
tests/clients/vps_client/v1/test_starting_price.py         6
tests/store/repositories/test_accounts_repository.py      17
tests/store/repositories/test_accounts_schema.py           5
tests/store/repositories/test_bets.py                     20
tests/workflows/bet_entry/v1/test_betfair_adapter.py      29
tests/workflows/bet_entry/v1/test_orchestrator.py         30
tests/workflows/bet_entry/v1/test_pricing.py              10
tests/workflows/bet_entry/v1/test_reconciliation.py       28
tests/workflows/bet_entry/v1/test_record_builder.py       18
tests/workflows/bet_entry/v1/test_settlement.py           83
tests/workflows/bet_entry/v1/test_staking.py              20
tests/ui/api/test_health.py                                5
tests/ui/api/test_provisional.py                          14
tests/fixtures/betfair/__init__.py                    (fixture pkg)
tests/fixtures/betfair/raw_stream_frames.py
tests/fixtures/betfair/rest_responses.py
tests/fixtures/betfair/stream_messages.py
tests/fixtures/build_capture_fixture.py
```

### §7.3 — Brief §5.7 specific-question answers

**(a) Per-pillar test coverage — how many tests per
pillar?**

Counts in §7.1. Highlights:
- Workflow tests (218) and Betfair-client tests
  (197) dominate; together they are 78% of the
  total.
- `workflows/bet_entry/v1/test_settlement.py`
  alone has 83 test functions — the largest
  single test file, mirroring the largest
  production module (`settlement.py`, 1354 lines).
- UI tests are sparse (19) — health endpoint
  (5) + provisional endpoint (14). No frontend
  Python tests beyond the API surface; the
  React side has its own vitest suite (see
  `ui/web/src/**/*.test.tsx` — five test files,
  not counted in the Python total).

**(b) Test gaps in shipped pillars?**

Not assessed empirically — the brief explicitly
disallows running tests (`§9.5`). A structural
note: the bet pillar (W4 placement → W5
realised-conversion → W6 reconciliation → W6.5
settlement → W9 last-read) has reconciliation
tests (28) and settlement tests (83) but the
W5 stream is not present in production code
(see §1.2(b)), so no W5 settlement-payout
test path could exist. The `realised_conversion_rate`
column is asserted to remain `None` in the W4
record-builder tests
(`tests/workflows/bet_entry/v1/test_record_builder.py:92,219`).

**(c) Test scaffolding — fixtures, conftest patterns,
integration vs unit split.**

Fixtures live under `tests/fixtures/`:
- `tests/fixtures/betfair/raw_stream_frames.py`
- `tests/fixtures/betfair/rest_responses.py`
- `tests/fixtures/betfair/stream_messages.py`
- `tests/fixtures/build_capture_fixture.py`

Conftest files: `tests/conftest.py` (empty),
`tests/clients/betfair_client/v1/conftest.py`,
`tests/clients/vps_client/v1/conftest.py`. No
top-level / per-pillar conftests for the workflow
or store paths.

Integration vs unit split: not explicitly named
in the test directory structure. The unit-level
tests (record-builder, pricing, staking) live in
the same package as the integration-level tests
(orchestrator, betfair_adapter, settlement worker).
Test isolation pattern uses `InMemoryBetRecordStorage`
substitution (per W4 brief §10.2, referenced in
`store/repositories/bets.py:215-222`).

**(d) Are W11 / W11.1 tests at the correct paths
per the surgical rename?**

Yes:
- `tests/store/repositories/test_accounts_repository.py` ✓
- `tests/store/repositories/test_accounts_schema.py` ✓
- `tests/store/repositories/test_bets.py` ✓

Matches the W11.1 surgical-rename intent named
in the pre-W14 brief §3 reference-only files
("tests now live at `tests/store/repositories/`").

---

## §8 — DR drift inventory (brief §5.8)

For each locked DR in `decisions.md`, the table
below records: title, what it locks (one line),
shipped-reality status (**match** / **divergent**
/ **N/A**), and — for **divergent** — both-side
citations.

**Status legend:**
- **match** — shipped reality observably matches
  the DR's locked content at the inventory layer.
- **divergent** — shipped reality observably
  differs from the DR's locked content. Both
  sides cited.
- **N/A** — DR is a principle without a directly
  inspectable shipped surface, OR is forward-
  looking and not yet applicable at this inventory
  point.

| DR | Title (short) | What it locks (one line) | Status | Citations (if divergent) |
|---|---|---|---|---|
| DR-001 | Rebuild v2 from ground up | Decision to rebuild rather than extend | **match** | — (existence of `bethub-v3/` repo is the artefact) |
| DR-002 | Three-layer separation (operational / execution / accounting) | Strict boundaries between layers | **N/A** | — (DR-030 supersedes with concrete folder layout; see DR-030 row) |
| DR-003 | Six-file governance | README / vision / architecture / decisions / WIP / sessions; no anomaly/patch logs | **N/A** | — (governance discipline, not a shipped surface in `bethub-v3/`) |
| DR-004 | Session-open reads only WIP | Discipline for chat-side session open | **N/A** | — (session protocol, not in `bethub-v3/`) |
| DR-005 | Diagrams in `diagrams/` | Diagrams separated from `architecture.md` | **N/A** | — (governance) |
| DR-006 | Operations log first-class day-one | Append-only journal of operational actions | **divergent** | Spec: `decisions.md:67-75`. Shipped: `bethub-v3/ops/__init__.py` empty (0 lines); no `ops_log` table in `bethub-v3/store/schema/` (verified by directory listing); zero hits for `ops_log` / `operations_log` in repo-wide grep. |
| DR-007 | Vocabulary lock (concern / decision / principle / metric) | Definitions of the four terms | **N/A** | — (governance vocabulary) |
| DR-008 | Smart-Betfair principle | "Show only what Betfair native cannot" | **N/A** | — (UI principle; no execution-layer UI shipped yet) |
| DR-009 | Triage of 15 concerns | v3-day-one scope | **N/A** | — (roadmap; many concerns out of scope of inventory) |
| DR-010 | Two-mode session model (bursts + persona sessions) | Burst / race window / persona session entities; hierarchy | **divergent** | Spec: `decisions.md:158-191`. Shipped: no `burst`, `race_window`, `persona_session` entities. `bets.cycle_id` exists but is the W4 hedge-and-soft-book pair grouping per the orchestrator's `parent_cycle_id` handling (`workflows/bet_entry/v1/orchestrator.py:418`), not the DR-010 burst/race-window construct. No "burst start / end" workflow shipped. |
| DR-011 | Promo Planner day-one | Promo board + race-window scheduler + action surfacing | **divergent** | Spec: `decisions.md:195-214`. Shipped: no promo-planner module, no `promo`-anything tables, no race-window scheduler, no action queue. `workflows/burst_review/__init__.py` empty (0 lines). |
| DR-012 | Keyboard-first hot path | Principle | **N/A** | — (no execution-layer hot-path UI shipped) |
| DR-013 | Hygiene engine structure (persona profile, bookmaker rules, account state) | Three data sources + per-week plan output | **divergent** | Spec: `decisions.md:248-274`. Shipped: no `persona_profile`, `bookmaker_hygiene_rules`, `account_state` tables in `bethub-v3/store/schema/`. The shipped accounts pillar (`accounts`, `books`, `accounts_at_book` per `store/schema/accounts.py`) is identity-only — no tier / phase / rules columns. |
| DR-014 | Soft-book price context in burst action queue | Always-on best scraped + conditional promo-on-book highlight | **divergent** | Spec: `decisions.md:278-307`. Shipped: no action queue surface; no soft-book scraping infra; no operational soft-book layer (per `dr029_scope.md §3.11` — operational soft-book layer deferred Session 69). |
| DR-015 | Three-tier AccountCare alerts (red / amber / yellow) | Severity categories | **divergent** | Spec: `decisions.md:311-329`. Shipped: no AccountCare module, no warning tables, no alerts surface. |
| DR-016 | Hedge trigger model (two profiles, persist-after-jump, stake recalc) | Free-bet relaxed / cash strict trigger profiles | **divergent** | Spec: `decisions.md:333-367`. Shipped: `place_hedge` does single-shot placement with retry-on-retry-safe (`workflows/bet_entry/v1/orchestrator.py:680-782`); no "fire when conversion ≥ X%" trigger, no firming-fallback, no T=0 fallback, no persist-after-jump flag, no stake-recalculation-at-fire pattern. |
| DR-017 | Bet records fully editable + Burst Review + inline validation | Edit-anytime; hedge modal capture; six warning checks | **divergent** | Spec: `decisions.md:371-414`. Shipped: bets are written once (W4); the in-place updates are settlement-state, match-status, reconciliation bookkeeping, and last-read-market-state — not operator edits to any field. `update_match_status` / `update_settlement_state` / `update_reconciliation_bookkeeping` / `update_last_read_market_state` are the only update methods on `BetRecordStorage` Protocol (`store/repositories/bets.py:130-207`). No inline-editing UI shipped. No "sanity check" pass. None of the six inline validation warnings shipped. |
| DR-018 | Scraper architecture supports incremental scraper addition | Per-book interface + aggregator pattern | **N/A** | — (Cloudflare-blocked book scraping deferred per `dr029_scope.md §3.4`; soft-book operational layer deferred per `§3.11`. No scraper aggregator in `bethub-v3/`. Not yet applicable.) |
| DR-019 | Derived state computed on read | Source-of-truth = events; everything else computed | **divergent** | Spec: `decisions.md:443-468`. Shipped: `bets` table stores mutable state (`match_status`, `matched_stake`, `unmatched_stake`, `matched_price`, `settlement_state`, `last_reconciled_at`, `reconciliation_attempts`, `dead_heat_count`, `removed_runner_count`, `unexpected_state_count`, `last_read_market_state`) — see `store/schema/bets.py:17-45`. No event log; bet records mutate in place. (Bounded — derived aggregates aren't stored, only per-bet mutable state.) |
| DR-020 | Standalone Betfair liquidity capture, superseded by capture.db | VPS race-data capture is source | **match** | — (amendment 2026-04-28 supersedes for AU racing; `clients/vps_client/v1/bracketing.py` reads time-series from capture.db per the contract) |
| DR-021 | Session logging + Adelaide-local timestamps | All timestamps in Adelaide local | **match** | — (`ZoneInfo("Australia/Adelaide")` used in `domain/bets/__init__.py:46`, `workflows/bet_entry/v1/orchestrator.py:75`, `workflows/bet_entry/v1/settlement.py:41`, `workflows/bet_entry/v1/reconciliation.py:45`, `workflows/bet_entry/v1/betfair_adapter.py:82`, `clients/betfair_client/v1/envelope.py:28`, `ui/api/routers/health.py:21`, `ui/api/routers/provisional.py:52`) |
| DR-022 | account / book / account_at_book vocabulary | DR-022 vocab lock | **match** | — (`domain/accounts/__init__.py` ships `Account`, `Book`, `AccountAtBook`; `store/schema/accounts.py` ships three tables with composite uniqueness on `accounts_at_book`) |
| DR-023 | Operator focuses on betting; system handles admin | Principle — auto-settlement, auto-FB creation, auto-hedge-classification | **divergent** | Spec: `decisions.md:617-641`. Shipped: auto-settlement-state-transition is shipped (`run_settlement_pass` reads `market_settlement` and writes terminal states). NOT shipped: auto-FB-creation-from-insurance-trigger (no FB credit cascade); auto-hedge-classification (DR-025 not shipped); auto-late-scratch-deduction handling. Principle is partially implemented. |
| DR-024 | Operating-mode and analytical-mode separated | Principle | **N/A** | — (UI is one route surface — `/provisional` — insufficient to evaluate separation discipline) |
| DR-025 | Hedge classification model (5 terminal + 1 transient, auto-classified) | Five terminal hedge states + auto-resolve+24h | **divergent** | Spec: `decisions.md:684-725`. Shipped: zero hits for `hedge_state`, `unhedged_deliberate`, `unhedged_oversight`, `unhedged_unclassified`, `hedge_failed`, `hedge_partial` in production code. No `hedge_state` column on `bets` (see verbatim DDL in §1.1). No classification worker. No auto-resolve-at-settlement+24h logic. |
| DR-026 | Market-context snapshot principle (per-bet at log time) | Five-field snapshot inline on bet record | **divergent** | Spec: `decisions.md:731-786`. Shipped: zero hits for `bf_snapshot`, `snapshot_timestamp`, `stale_flag`, `snapshot_age`, `late_scratch_between`, `bf_snapshot_aligned_to_placement`, `bf_snapshot_unavailable` in production code. None of those columns exist on `bets` or `bet_legs` (verbatim DDL in §1.1). The Set B fields on `bet_legs` (event_name, market_name, etc.) are DR-032 §4 market-identity snapshots, not DR-026 price-and-volume snapshots. (Note: DR-026 has an open Session 14 multi-agent review item that may reframe; `dr029_scope.md §2.8` bet-schema reframing direction aligns with the absence, but DR-026 remains the locked principle in `decisions.md`.) |
| DR-027 | Two-database architecture (v3 bet-data + capture.db race-data) | Race-side via vps_client only | **match** | — (vps_client is the single integration point; no `races` / `runners` tables in `bethub-v3`; verified via grep) |
| DR-028 | Integration boundary discipline (no caching / denormalisation / second integration point) | Four forbidden patterns | **match** | — (only `vps_client` reads capture.db; only `betfair_client` talks to Betfair; no race-data caching observed; no second integration point) |
| DR-029 | Data-layer fit-for-purpose review gating v3 build | Locked stance: data-layer review before v3 build | **match** | — (multi-step gate; per `project_context.md §5` and the W11.1-close baseline, DR-029 is closed enough that W4–W11 have shipped; the three pieces of named debt are explicitly tracked) |
| DR-030 | V3 repo layout and module-boundary discipline (5 contracts) | Folder layout + .importlinter | **match (with carry-forward)** | Folder layout matches and 5/0 contracts kept (`bethub-v3/.importlinter`). Two structural carry-forwards: `domain/pricing/__init__.py` and `domain/settlement/__init__.py` are empty (0 lines each) — pricing math and settlement-state-machine live under `workflows/bet_entry/v1/`, not `domain/`. `bethub-v3/contracts/__init__.py` empty (0 lines) — contract files still live at `bethub-rebuild/dr029/2_7_api_contract_versioning/` per the DR-030 amendment explicitly tracking the future relocation (`decisions.md:1022-1024`). |
| DR-031 | Tech stack (Python 3.12+ / FastAPI / SQLite WAL / SQLAlchemy Core / Alembic / React+TS+Vite) | Locked stack | **divergent (bounded)** | Spec: `decisions.md:1032-1085`. Shipped: Python 3.12+ ✓ (verified by `tests/test_skeleton.py:14-17`); FastAPI ✓ (`ui/api/main.py:18`); SQLite WAL ✓ (`store/repositories/bets.py:469` `PRAGMA journal_mode = WAL`); React + TS + Vite ✓ (`ui/web/`); betfairlightweight ✓ (`pyproject.toml:13`); pytest + pytest-asyncio ✓ (`pyproject.toml:19-20`); ruff ✓ (`pyproject.toml:21`); import-linter ✓ (`pyproject.toml:22`). DIVERGENT: SQLAlchemy Core declared in `pyproject.toml` and used in `clients/vps_client/v1/` (8 modules) but NOT used in `bethub-v3/store/` (uses raw `sqlite3` — see `store/repositories/bets.py:16` and `store/repositories/accounts.py:40`). Alembic declared in `pyproject.toml:12` but no `alembic/`, no `migrations/`, no `alembic.ini`, no env.py — migration mechanism is inline `_add_column_if_missing` per `store/schema/bets.py:69-90`. Both divergences are documented as deferred per W10 brief §10 / §1 (`store/schema/bets.py:80-84` docstring) and W11 brief §5.3 (`store/repositories/accounts.py:10-13` docstring). The pre-W14 brief §5.6(c) explicitly flags both expected divergences. |
| DR-032 | Betfair as canonical reference + bet-record / bet-leg two-table schema | Stake on bets only; Betfair IDs on legs only; Set B immutable display | **match** | — (`store/schema/bets.py` has `bets` table with stake fields and zero Betfair identifiers; `bet_legs` has `betfair_market_id` / `betfair_selection_id` / six Set B display fields per DR-032 §4 / §5; `record_builder.py` enforces leg-count rules. Matches `decisions.md:1099-1156` description.) |

**Special three-way drift to call out explicitly
(brief §5.8 known starting drifts):**

DR-027 (the "single event log carrying bet_placed /
bet_correction / bet_settled / hedge_state_classification
/ cascade events / FB credit and deployment events
/ friend_payment_made / etc." per
`decisions.md:798`) **vs** DR-032 ("two-table shape:
bet record + bet legs" per `decisions.md:1099-1101`)
**vs** shipped reality (`bets` table with mutable
state columns `match_status`, `settlement_state`,
`matched_stake`, `unmatched_stake`, `matched_price`,
`last_reconciled_at`, `reconciliation_attempts`,
`dead_heat_count`, `removed_runner_count`,
`unexpected_state_count`, `last_read_market_state`
per `store/schema/bets.py:17-45`).

DR-027 (Session 19 lock) and `architecture.md §A.2`
(lines 91–149) describe a single append-only event
log with `bet_placed`, `bet_correction`,
`bet_settled` as separate events linked by
`supersedes_event_id` / `parent_event_id`. DR-032
(Session 90 lock) supersedes with a two-table
shape — `bets` row + N `bet_legs` rows — but
DR-032's framing assumes both rows are write-once
plus settlement-resolution fields. The shipped
state matches DR-032's two-table shape but adds
seven mutable-after-write columns on `bets` to
hold reconciliation / settlement / W9 read state,
diverging from DR-019's "no stored derived state /
no stored mutable state" principle.

Three locked positions, one shipped reality.

---

## §9 — Missing-from-spec inventory (brief §5.9)

What `architecture.md` (and the DR set + the
v3_data_requirements / dr029_scope substrate)
describes that is not on disk in `bethub-v3/`.
Each item below cites the spec source and tags
as **build pending** (known forward work — W12 /
W13 / W14 / W15 etc.) or **drift** (something
dropped through the cracks without a tracking
pointer).

### §9.1 — Event-log spine (`architecture.md §A.2`)

**Missing:** A single append-only event log table
holding every event type per `architecture.md`
lines 91–149.

**Includes (event types named):**
`bet_placed`, `bet_correction`, `bet_settled`,
`bet_leg`, `lay_order_finalised`,
`hedge_state_classification`, `promo_observed`,
`promo_journey_annotation`, `free_bet_credited`,
`free_bet_deployed`, `free_bet_revoked`,
`free_bet_expired`, `promo_cash_credited`,
`accountcare_warning_raised`,
`accountcare_warning_cleared`,
`account_holder_funding`,
`account_at_book_deposit`,
`account_at_book_withdrawal`,
`account_holder_remittance`,
`account_at_book_balance_adjustment`,
`account_holder_balance_adjustment`,
`external_payment`, `profit_share_distribution`.

**Tag:** Cross-cutting. **Build pending** (W14 is the
cash-flow event log per the brief preamble), but the
shape question is also under multi-agent-review-style
reframing (DR-027 vs DR-032 vs shipped reality —
see §8 three-way drift call-out).

### §9.2 — Promo lifecycle (`architecture.md §A.4`)

**Missing:** `promo_template`, `promo`,
`promo_observed`, `promo_journey_annotation`,
`free_bet_credited`, `free_bet_deployed`,
`free_bet_revoked`, `free_bet_expired`,
`promo_cash_credited`. Plus the `pending_fb_deployment`
flag, `source_credit_event_ids` array,
`draw_down_breakdown` JSON, FIFO-by-expiry logic.

**Spec:** `architecture.md §A.4` (lines 220–274).

**Tag:** **Build pending** — W13 is the promo-event
log per the brief preamble.

### §9.3 — Cash-flow event log (`architecture.md §A.5`)

**Missing:** Seven cash-flow event types
(`account_holder_funding`, `account_at_book_deposit`,
`account_at_book_withdrawal`,
`account_holder_remittance`,
`account_at_book_balance_adjustment`,
`account_holder_balance_adjustment`,
`external_payment`, `profit_share_distribution`)
plus the two-balance-location model (Location 1:
at-book; Location 2: custodian) plus
operation-net-flow derivation per the §A.5
formulas (lines 343–353).

**Reference data also missing:** `account_holders`,
`payees`, `account_arrangement`,
`warning_catalogue` tables per
`architecture.md §A.1` (lines 70–78).

**Tag:** **Build pending** — W14 is the cash-flow
event log per the brief preamble.

### §9.4 — AccountCare event log entries (`architecture.md §A.4`)

**Missing:** `accountcare_warning_raised` and
`accountcare_warning_cleared` events per
`architecture.md §A.4` (line 128–130) plus the
`warning_catalogue` reference table.

**Tag:** **Build pending** — part of the operational-
layer work that DR-029 close-out positions for
post-W14.

### §9.5 — Balance derivation (`architecture.md §A.5 / §A.9`)

**Missing:** Both Location 1 (per-account-at-book
at-book balance) and Location 2 (per-custodian
cash holding) derivation, plus the cash-age FIFO
walk and operation-net-flow informational view.

**Spec:** `architecture.md §A.5` (lines 298–353)
and `§A.9` (lines 522–527).

**Tag:** **Build pending** — depends on §9.3 (cash-
flow events) shipping first. Likely W14 then a
balance-derivation pass.

### §9.6 — Reconciliation gap per book (`architecture.md §A.9`)

**Missing:** Cash reconciliation surface (computed
at-book balance vs operator-entered actual book
balance) plus the other five reconciliation
surfaces per `architecture.md §A.9` (lines
552–558): FB reconciliation, settlement
reconciliation, race-result reconciliation, hedge
reconciliation, cash-holding-with-custodian
reconciliation.

**Tag:** **Build pending** for cash / FB
reconciliation (depend on balance derivation).
**Drift** for hedge reconciliation surface
(DR-025 + the hedge-state classification stream
hasn't shipped; no tracking pointer in
`current_state.md` per the brief reference).

### §9.7 — Ops log first-class storage (DR-006)

**Missing:** `ops_log` table and `ops/` module.

**Spec:** DR-006 (`decisions.md:67-75`). Explicit
"day one" commitment.

**Tag:** **Drift** — DR-006 is locked but the
shipped state is empty `ops/__init__.py` + no
`ops_log` table in `store/schema/`. No tracking
pointer in `current_state.md` (per the brief
reference set). The W11 / W11.1 reports name
this as deferred.

### §9.8 — Hedge state classification (DR-025)

**Missing:** Five terminal states + transient state
on `bets`; `hedge_state_classification` events;
auto-classification + auto-resolve-at-settlement+24h
logic.

**Spec:** DR-025 (`decisions.md:684-725`) and
`architecture.md §A.6` (lines 392–415).

**Tag:** **Build pending** — likely W15 or later;
named in `architecture.md §A.6` as a derived state
to compute from events.

### §9.9 — Cascade chains (`architecture.md §A.7`)

**Missing:** Auto-cascade of `bet_settled`
supersession through `free_bet_credited` and
`promo_cash_credited`. `cascaded_from_bet_settled_event_id`
and `cascade_path` payload fields.

**Spec:** `architecture.md §A.7` (lines 420–453).

**Tag:** **Build pending** — depends on §9.1
(event log) and §9.2 (promo events).

### §9.10 — Promo journey annotation (`architecture.md §A.4 Q1`)

**Missing:** `promo_journey_annotation` events
with closed-schema-open-vocabulary tags.

**Spec:** `architecture.md §A.4` (line 121 +
236–237).

**Tag:** **Build pending** — part of W13's
promo-event-log scope.

### §9.11 — Free-bet lifecycle terminal events

**Missing:** `free_bet_expired`, `free_bet_revoked`,
`free_bet_deployed` event types.

**Spec:** `architecture.md §A.4` (lines 270–273
plus 122–124).

**Tag:** **Build pending** — W13 scope.

### §9.12 — DR-013 hygiene engine (persona profile, bookmaker rules, account state)

**Missing:** The three data sources and the weekly
plan output.

**Spec:** DR-013 (`decisions.md:248-274`).

**Tag:** **Build pending** — likely post-W15
operational-layer work.

### §9.13 — Two-mode session model (DR-010 burst / race window / persona session)

**Missing:** Burst entity, race window entity,
persona session entity.

**Spec:** DR-010 (`decisions.md:158-191`).

**Tag:** **Build pending** — operational-layer
scope.

### §9.14 — Promo Planner (DR-011)

**Missing:** Promo board, race window scheduler,
action queue, outcome resolution.

**Spec:** DR-011 (`decisions.md:195-214`).

**Tag:** **Build pending** — operational-layer
scope.

### §9.15 — Soft-book scraping / operational soft-book layer

**Missing:** Soft-book scraping aggregator (DR-014
+ DR-018); `softbook_client` (deferred per
`dr029_scope.md §3.11`).

**Spec:** DR-014 (`decisions.md:278-307`);
DR-018 (`decisions.md:420-440`).

**Tag:** Operational soft-book layer is **explicitly
deferred** per `dr029_scope.md §3.11` Session 69.
Soft-book typed-price entry is absorbed into §2.8 /
§2.9; not yet shipped either. Cloudflare-blocked
book scrapers are out of scope per
`dr029_scope.md §3.4`.

### §9.16 — Hedge trigger model (DR-016)

**Missing:** Two trigger profiles (free-bet relaxed
+ cash strict), firming detection, persist-after-jump
default, T=0 fallback.

**Spec:** DR-016 (`decisions.md:333-367`).

**Tag:** **Build pending** — execution-layer work
likely post-W14.

### §9.17 — Burst Review first-class workflow + inline validation (DR-017)

**Missing:** Inline-edit-anywhere UI; six
operator-facing validation warnings; sanity-check
pass; "burst" surface.

**Spec:** DR-017 (`decisions.md:371-414`).

**Tag:** **Build pending** — partially shipped at
the settlement-state-disambiguation slice
(/provisional endpoint) but the bulk of the
DR-017 surface is open.

### §9.18 — DR-015 three-tier AccountCare alerts

**Missing:** Red / amber / yellow alerts surface.

**Spec:** DR-015 (`decisions.md:311-329`).

**Tag:** **Build pending** — operational-layer
scope.

### §9.19 — DR-026 market-context snapshot fields on bet record

**Missing:** Best back/lay price + size, total
matched, snapshot timestamp, stale flag,
`bf_snapshot_unavailable`,
`bf_snapshot_aligned_to_placement`,
`late_scratch_between_snapshot_and_log` on the bet
record.

**Spec:** DR-026 (`decisions.md:731-786`),
`architecture.md §A.3` (lines 184–192).

**Tag:** **Build pending OR resolved-by-§2.8**.
DR-026 is locked but `dr029_scope.md §2.8`
reframes the bet-schema along the operational/
analytical axis — see also `v3_data_requirements.md
§B.7 #1` ("Bet schema simplification" reserved for
multi-agent review). The shipped absence aligns
with the §2.8 direction but DR-026 itself remains
the locked principle in `decisions.md`. A locked
DR amendment would resolve the open framing
explicitly.

### §9.20 — Sports market data layer (`v3_data_requirements.md §B.3`)

**Missing:** Sports market data in capture.db
(currently absent per `v3_data_requirements.md
§B.3` line 109).

**Spec:** `v3_data_requirements.md §B.3`.

**Tag:** **Build pending** — first item in the
DR-029 data review per §B.3; affects sports bet
log path (`v3_data_requirements.md §B.3` line
120 — "v3 logs sports bets with
`bf_snapshot_unavailable = true`" until sports
capture lands).

### §9.21 — Contract relocation (DR-030 §Scope)

**Missing:** `vps_client_contract.md` and
`betfair_client_contract.md` at
`bethub-v3/contracts/`.

**Spec:** DR-030 §Scope amendment
(`decisions.md:1022-1024`): "Contract files
… relocate from `dr029/2_7_api_contract_versioning/`
to v3's `contracts/` folder as part of v3 build
proper administrative cleanup."

**Shipped reality:** Contracts live at
`bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`
(87,934 bytes) and `vps_client_contract.md`
(39,420 bytes). `bethub-v3/contracts/__init__.py`
is empty.

**Tag:** **Drift / tracking-pointer-aware** —
explicitly flagged in the DR-030 text but not yet
acted on.

---

## §10 — Missing-from-architecture inventory (brief §5.10)

What's on disk in `bethub-v3/` that isn't described
in `architecture.md`. For each: shipped file,
plain-language description, the spec section it
should plausibly belong to.

### §10.1 — `bets.cycle_id` column

**Shipped:** `store/schema/bets.py:19` —
`cycle_id TEXT NOT NULL` on the `bets` row.
Used to group a Strategy 2 hedge + soft-book
pair plus downstream free-bet inheritance per
the W4 brief §3.6 (`workflows/bet_entry/v1/orchestrator.py:418`
`parent_cycle_id: str | None`).

**Description:** A bet-cycle correlation key
linking the soft-book leg, the Betfair hedge,
and the downstream free-bet usage that cascades
from a triggered insurance bet. Generated as
`f"cycle-{uuid.uuid4()}"` when not inherited
(`workflows/bet_entry/v1/record_builder.py:244`).

**Plausibly belongs in:** A new architecture.md
sub-section, likely under §A.3 (bet placement)
or as a §A.7-adjacent ("cycle as the analytical
unit, per `project_context.md §3` 'Standing
analysis convention'"). The concept is described
operationally in `project_context.md §3` (line
63–65 — "Standing analysis convention") but not
in `architecture.md`.

### §10.2 — `bets.entry_path` column

**Shipped:** `store/schema/bets.py:21` —
`entry_path TEXT NOT NULL`. Enum:
`racing_screen`, `sports_screen`, `manual_log`,
`free_bet_ledger` (`domain/bets/__init__.py:124-134`).
W4 v1 populates `RACING_SCREEN` only.

**Description:** Discriminates the entry surface
that produced the bet record. Routes downstream
behaviour differences (e.g., validation rules,
display).

**Plausibly belongs in:** `architecture.md §A.3`
(bet placement) — would name the four entry paths
and their semantic differences. Currently absent.

### §10.3 — `bets.strategy_tag` column

**Shipped:** `store/schema/bets.py:22` —
`strategy_tag TEXT` (nullable). Enum:
`safety_net`, `price_booster`, `sgm_correlated`,
`synthetic_each_way` (`domain/bets/__init__.py:73-88`).

**Description:** Classification of the bet against
one of the four racing strategies. Sourced from
`project_context.md §3` ("The four racing
strategies"). `SGM_CORRELATED` is reserved but
raises in `record_builder.py:198-202`. NULL
means account-health turnover bet (no strategy).

**Plausibly belongs in:** `architecture.md §A.3`
or a new §A.x sub-section naming the strategy
classification. Currently absent from
`architecture.md`. (Project_context.md does
describe the strategies but is a session-orienting
primer, not the architectural spec.)

### §10.4 — `bets.is_free_bet` / `free_bet_conversion_rate` / `realised_conversion_rate` columns

**Shipped:** `store/schema/bets.py:23-25` — three
fields. `realised_conversion_rate` is unpopulated
(see §1.2(b) — W5 has not shipped).

**Description:** Free-bet flag plus the projected
conversion rate (default 65% — `DEFAULT_FREE_BET_CONVERSION_RATE`
in `workflows/bet_entry/v1/pricing.py:51`) plus
the placeholder for the realised rate at
settlement.

**Plausibly belongs in:** `architecture.md §A.4`
(Promo and credit chains) — the FB lifecycle is
described there but the specific bet-record
columns and the conversion-rate constants are
not. The `architecture.md §A.4` framing
references FB face value + 70% realised
conversion rate (`architecture.md §A.4` Q1 lock
+ `decisions.md` DR-009 line 162 "the free bet …
typically converts to roughly 70% of face value")
but no architecture surface names
`realised_conversion_rate` as a column.

### §10.5 — `bets.matched_stake`, `unmatched_stake`, `matched_price`, `match_status` columns

**Shipped:** `store/schema/bets.py:27-30`.
`match_status` enum has five values
(`final_full`, `final_partial`, `provisional`,
`provisional_pending`, `failed` —
`domain/bets/__init__.py:91-104`).

**Description:** Tracks the Betfair-side
placement outcome — how much of the hedge
matched, at what price, and the disambiguation
state of the bet record. Driven by the W4 Trigger
A + Trigger B + W6 reconciliation worker.

**Plausibly belongs in:** `architecture.md` has
no equivalent surface. `architecture.md §A.6`
(Settlement and hedge state) describes
**settlement** state and **hedge classification**
state, but not **match** state for a placed
hedge. The match-state machine (W4 brief §3.4 +
§6.2) is a W4 ship-detail that doesn't appear in
architecture.md. Plausibly belongs in §A.6 or
its own sub-section.

### §10.6 — `bets.soft_book_combined_price` column

**Shipped:** `store/schema/bets.py:31`.

**Description:** The SGM combined price the
bookmaker quoted (or the single-leg price for
non-multi bets). For single-leg soft-book bets,
written as NULL on the soft-book leg per W4
follow-up §5.4 (`workflows/bet_entry/v1/record_builder.py:336-358`).

**Plausibly belongs in:** `architecture.md §A.10`
(canonical source identifiers) names "bet records
… soft-book combined price (the SGM combined
price the bookmaker quoted, or the single-leg
price for non-multi bets)" in the bet-record
fields list (line 1106-1108 of `decisions.md`
DR-032 row), but `architecture.md §A.10` does
not enumerate it. Plausibly a §A.10-adjacent
addition.

### §10.7 — `bets.price_source` column

**Shipped:** `store/schema/bets.py:35` —
`price_source TEXT` (nullable). Enum:
`streaming_cache`, `rest_fetch`, `operator_typed`
(`domain/bets/__init__.py:189-200`).

**Description:** Names the source path that
produced the bet's price — the W4 follow-up §5.2
field added to flag whether the price came from
the streaming cache, a REST fallback, or operator
manual entry (soft-book leg).

**Plausibly belongs in:** `architecture.md §A.3`
(bet placement) — the snapshot-source-and-state
discipline is described but not the per-bet flag.
Also plausibly architecture.md §A.10 alongside
the canonical-source discussion.

### §10.8 — `bets.betfair_bet_id` column

**Shipped:** `store/schema/bets.py:36`.

**Description:** Betfair-side bet identifier
returned from `placeOrders`. Used by the W6
reconciliation worker to look up order state in
`listCurrentOrders`. Populated for hedge legs
only; NULL for soft-book legs.

**Plausibly belongs in:** `architecture.md §A.3`
or §A.10. The `architecture.md §A.10` text
discusses canonical Betfair identifiers but does
not enumerate `betfair_bet_id` as a per-bet
field.

### §10.9 — `bets.last_reconciled_at` + `reconciliation_attempts` columns

**Shipped:** `store/schema/bets.py:37-38`. W6 v1.

**Description:** Reconciliation bookkeeping. Set
per worker pass by
`update_reconciliation_bookkeeping`. Not used by
the production read path; intended for
operator-debugging and future cadence calibration.

**Plausibly belongs in:** `architecture.md §A.9`
(derivation rules / reconciliation surfaces) —
but the architecture.md text describes
**reconciliation** as the cash-side / FB-side /
settlement-side comparison, not the match-state
worker bookkeeping. Plausibly a different
sub-section ("worker bookkeeping fields") or a
DR-031-substrate-named convention.

### §10.10 — `bets.dead_heat_count`, `removed_runner_count`, `unexpected_state_count` columns

**Shipped:** `store/schema/bets.py:40-42`. W6.5.

**Description:** Bet-context fact captured from the
worker's MarketSettlement read — for race-state
visibility around the bet's settlement.

**Plausibly belongs in:** `architecture.md §A.6`
(Settlement). `architecture.md §A.6` (lines
371–373) names `field_size_at_settlement` and
`field_size_at_bet_placement` as bet-context
captures; the W6.5 three counts (dead-heat,
removed-runner, unexpected-state) are a different
set of bet-context facts but the same pattern.

### §10.11 — `bets.last_read_market_state` column

**Shipped:** `store/schema/bets.py:43`. W9.

**Description:** JSON-encoded MarketSettlement
snapshot from the most recent settlement-worker
read on this bet. Surfaced by the W8
`/provisional` endpoint for operator review.

**Plausibly belongs in:** `architecture.md` has
no surface that names a per-bet read-cache of
this kind. The DR-019 "compute on read" principle
would argue against persisting it; the W9 brief
§5.4 (referenced in `workflows/bet_entry/v1/settlement.py:81-88`)
justified it as the operator-visibility surface
substrate. Plausibly belongs in §A.6 as a
worker-side visibility helper, or as a separate
"worker substrate" section.

### §10.12 — `bets.settlement_state` enum value `PROVISIONAL`

**Shipped:** `domain/bets/__init__.py:121` —
`PROVISIONAL = "provisional"` as a fifth
SettlementState value alongside the four named
in `architecture.md §A.6`.

**Description:** Non-terminal review state per
§2.6 §3.4 (referenced in `workflows/bet_entry/v1/settlement.py:107-114`).
Bets enter PROVISIONAL when the settlement read
returns an unexpected runner status or runner
absence — operator-resolvable through the W8
burst-review queue.

**Plausibly belongs in:** `architecture.md §A.6`
naming the five-state machine (PENDING,
SETTLED_WON, SETTLED_LOST, VOIDED, PROVISIONAL).
`architecture.md §A.6` describes the
`bet_settled` event with `status` enum
`provisional | finalised | rejected` (line 370)
but the per-bet settlement-state machine (state
on the `bets` row) is a different surface.

### §10.13 — `bet_legs.leg_role` column

**Shipped:** `store/schema/bets.py:51` — enum
`HEDGE`, `SOFT_BOOK` (`domain/bets/__init__.py:137-146`).

**Description:** Per-leg tag distinguishing the
Betfair hedge leg from the soft-book back leg.
Bet records pair one of each per cycle, sharing
a `cycle_id`.

**Plausibly belongs in:** `architecture.md §A.10`
(canonical-source) or `DR-032 §5` — DR-032
specifies the two-table shape but does not name
the `leg_role` discriminator. The W4 brief and
the math review both rely on the hedge / soft-
book distinction; architecturally it sits in a
§A.10 amendment or DR-032 amendment.

### §10.14 — `MatchStatus.PROVISIONAL_PENDING`

**Shipped:** `domain/bets/__init__.py:103` — fifth
match-status value alongside the W4 brief §3.4
four-state machine. Surfaced by the W6
reconciliation worker (`run_reconciliation_pass`
in `workflows/bet_entry/v1/reconciliation.py:236-247`).

**Description:** Indicates a bet that has matched
partially but is still in Betfair's unmatched
list (operator-visible flag per W4 brief §6.5).
Not in any architecture.md text.

**Plausibly belongs in:** `architecture.md` would
need a "match-state-machine" surface
(see §10.5).

### §10.15 — W4 retry-with-backoff timing constants

**Shipped:** `workflows/bet_entry/v1/orchestrator.py:468`
— `DEFAULT_BACKOFF_SCHEDULE_MS: tuple[int, int, int]
= (50, 200, 500)` plus
`DEFAULT_TRIGGER_B_DELAY_SECONDS: float = 5.0`
(line 473).

**Description:** Per-attempt back-off for retry-safe
Betfair failures + Trigger B reconciliation delay.

**Plausibly belongs in:** `architecture.md` has no
surface for orchestrator retry policy. Could land
in §A.6 (settlement / hedge state) or a new
operational-discipline subsection. Documented in
the W4 brief but not in architecture.md.

### §10.16 — `clients/betfair_client/v1/streaming.py` (StreamingClient)

**Shipped:** Full streaming client with
`StreamingConnectionState`, `MarketSubscriptionScope`,
`StreamingClient` (lines 104, 112, 202 of
`clients/betfair_client/v1/streaming.py`) plus
the §13.1 streaming-disconnect block at
`placement.py:126`.

**Description:** The Betfair Streaming API client
per DR-029 §2.4 (Betfair Streaming spec). Sub-
second pricing in the burst window; provides the
SUBSCRIBED / NOT_SUBSCRIBED state that gates
`place_bet` per contract §13.

**Plausibly belongs in:** `architecture.md` has a
"## Operational layer — Betfair direct" section
(lines 585–719) that names the operational layer
sourced via `betfair_client` direct (§B.1.x).
The Streaming spec is named "tracked-and-open
pending Saturday API probe findings (B.1.7)" —
the shipped state has the Streaming client built
out. Could be an update to architecture.md §B
once §2.4 closes.

### §10.17 — Identity check surfaces

**Shipped:** `clients/betfair_client/v1/identity.py`
(78 lines, `identity_check()` →
`IdentityCheck`) plus
`clients/vps_client/v1/identifier_resolution.py`
(148 lines, `identity_resolve()` →
`IdentityResolution`).

**Description:** Both contract §9.5 surfaces.
Betfair `identity_check` is account auth-state
verification; vps_client `identity_resolve` is
the passive cross-DB identifier-resolution check
named in the W6 reconciliation flow.

**Plausibly belongs in:** Both are in the
contracts at `dr029/2_7_api_contract_versioning/`
— architecture.md has no equivalent text
surface but the cross-DB integration model is
described in §A.8. Could land in §A.8 as a
named "identity-check surface" sub-bullet.

### §10.18 — `clients/betfair_client/v1/_audit.py` AuditLogSink

**Shipped:** `_audit.py` with `AuditLogSink`
Protocol, `MemoryAuditLogSink`,
`StdoutAuditLogSink`, `AuditLogEntry`,
`WriteOperation`, `WriteOutcome`.

**Description:** Per-bet-write audit-trail
substrate. Used by `place_bet`, `cancel_bet`,
`replace_bet` to log every write to a sink
chosen at the composition root.

**Plausibly belongs in:** Contract §12 (Audit-
trail discipline) — already in
`betfair_client_contract.md`. Architecture.md
has no audit-trail section beyond what DR-006
implies for the ops_log (which isn't shipped).
Plausibly a §A-side audit-trail surface.

### §10.19 — `workflows/bet_entry/v1/staking.py` commission table

**Shipped:** `_COMMISSION_TABLE` literal in
`workflows/bet_entry/v1/staking.py:64-74`. Keyed
on `(sport_family, country_code,
venue_normalised)` with cascading fallback.
Hardcoded rates (0.08 / 0.04 / 0.05 / 0.06).

**Description:** Resolves the Betfair commission
rate per market. Hardcoded literal at v1 with a
config-driven path named as future work
(`workflows/bet_entry/v1/staking.py:58-63`).

**Plausibly belongs in:** `architecture.md` does
not name commission resolution. Could land in
§A.6 or §A.10 (canonical source — commission is
a Betfair-owned fact). Currently lives in the
math review at `dr029/w4_bet_entry/hedge_staking_math.md`.

### §10.20 — UI api `/provisional` endpoints

**Shipped:** Two endpoints (GET + POST) at
`ui/api/routers/provisional.py` plus the React
route at `ui/web/src/routes/Provisional.tsx`.

**Description:** Burst-review queue surface
showing bets in `SettlementState.PROVISIONAL`
plus the operator resolve action.

**Plausibly belongs in:** `architecture.md` has no
"Burst review" section — only the DR-017 mention
inside `decisions.md`. The W8-shipped slice is a
subset of the spec'd Burst Review (per §5.4(d)
above and §9.17). Architecture.md should plausibly
add a "Burst Review / operator-triage surface"
section.

---

## §11 — Summary of drift findings ranked by operational severity

Severity ranking below uses three tiers:

- **High** — drift that materially affects the
  shape of the next-pillar build (W14 cash-flow
  event log). If the operator builds W14 against
  the current assumed shape and this drift goes
  unaddressed, the W14 brief will land against a
  divergent baseline.
- **Medium** — drift that affects build sequencing
  or architectural coherence but does not block
  W14 specifically.
- **Low** — drift that is administrative,
  tracking-pointer-aware, or already named as
  deferred.

### High-severity drift

1. **Three-way drift: DR-027 event log vs DR-032 two-table schema vs shipped mutable-state bets row.** (§8 row "Special three-way drift"; §1.2(c).) The shipped bets table has seven mutable-after-write state columns. W14 (cash-flow event log) commissions an event-log pattern; whether it builds on DR-027's framing or DR-032's two-table framing or extends the shipped state-mutating pattern is the brief-shaping question.

2. **Event-log spine absent.** (§9.1; §8 DR-019 row; §1.2(c).) `architecture.md §A.2` (lines 91–149) describes a single append-only event log with 23 event types. Zero of those event types exist in the shipped store. W14 / W13 / future cash-flow / promo work would need to either build the event log from scratch or operate without it.

3. **DR-026 market-context snapshot fields absent on `bets`.** (§9.19; §8 DR-026 row.) Spec names a five-field snapshot + several flags; none implemented. The open Session 14 multi-agent review item (`v3_data_requirements.md §B.7 #1`) is relevant — the drift may already be the intended end-state, but DR-026 itself remains locked. Pending DR resolution one way or the other.

4. **DR-006 ops log first-class absent.** (§9.7; §8 DR-006 row.) `ops/__init__.py` is 0 lines; no `ops_log` table. DR-006 names "day one" but the shipped state has no scaffold.

5. **DR-019 derived-state-on-read partially divergent.** (§8 DR-019 row.) Bets table stores mutable state — `match_status`, `settlement_state`, three counts, last-read JSON, reconciliation bookkeeping. DR-019 spec stance is event-sourced; shipped reality stores per-bet mutable state. Bounded — aggregates aren't stored — but the principle is observably partial.

### Medium-severity drift

6. **DR-031 SQLAlchemy Core not used in `store/`.** (§8 DR-031 row; §6.5(c).) `store/` uses raw `sqlite3`. `clients/vps_client/v1/` uses SQLAlchemy Core. Explicitly deferred per W11 brief §5.3; confirmed still divergent.

7. **DR-031 Alembic not adopted.** (§8 DR-031 row.) Declared as a dependency in `pyproject.toml`; no `alembic/` directory; no migrations files; inline `_add_column_if_missing` is the migration mechanism. Explicitly deferred per W10 brief §10.2 / DR-029 close-out.

8. **DR-025 hedge classification absent.** (§9.8; §8 DR-025 row.) No `hedge_state` column on `bets`; no `hedge_state_classification` events; no classification worker. The DR-025 framing's distinction between "match" state (what shipped does) and "hedge" classification (what DR-025 names) is a substantive difference that affects downstream balance / reconciliation work.

9. **DR-013 hygiene engine absent.** (§9.12; §8 DR-013 row.) Three data sources (persona profile, bookmaker rules, account state) all absent. Operational-layer scope but named as load-bearing in `architecture.md` and DR-013.

10. **DR-017 burst-review + inline-validation partially divergent.** (§9.17; §8 DR-017 row.) The W8-shipped /provisional endpoint is one slice of the much larger DR-017 surface. Inline-edit-anywhere, six validation warnings, sanity-check pass — none shipped.

11. **`bets.account_at_book_id` not a foreign key.** (§2.2(b); §1.1 verbatim DDL.) `accounts_at_book` exists with the matching identifier shape, but the `bets` schema declares no FK clause to `accounts_at_book(account_at_book_id)`. W11 brief §1.2 explicitly defers FK enforcement.

12. **`domain/pricing/` and `domain/settlement/` empty.** (§1.1 ¶ `domain/pricing/__init__.py` and `domain/settlement/__init__.py`; §6.5(b).) DR-030 lists both as concrete folders for pure business logic; both are 0-line stubs. The actual code lives at `workflows/bet_entry/v1/pricing.py` and `workflows/bet_entry/v1/settlement.py`. The "domain is pure" intent of DR-030 is partially inverted — workflow modules host what DR-030 calls domain code.

### Low-severity drift

13. **Contract files not relocated to `bethub-v3/contracts/`.** (§9.21; §6.2.) DR-030 §Scope amendment names the relocation; contracts still in `dr029/2_7_api_contract_versioning/`. Tracking-pointer aware.

14. **`accounts/` not in DR-030's top-level folder layout.** (§1.1 ¶ inventory note; DR-030 listing at `decisions.md:962-979`.) DR-030's locked layout lists `domain/bets/`, `domain/settlement/`, `domain/pricing/` as the three sub-folders of `domain/`; W11 added `domain/accounts/` without a DR-030 amendment. No conflict in spirit (account vocab is pure domain), but absent from DR-030's locked listing.

15. **Bet-record fields not described in `architecture.md`.** (§10 entries §10.1 through §10.15.) Several W4 / W5 / W6 / W6.5 / W9-shipped fields and enum values lack architecture.md coverage — `cycle_id`, `entry_path`, `strategy_tag`, `price_source`, `betfair_bet_id`, match-state machine, `dead_heat_count` / `removed_runner_count` / `unexpected_state_count`, `last_read_market_state`, `MatchStatus.PROVISIONAL_PENDING`, `SettlementState.PROVISIONAL`, retry-with-backoff constants. None block W14 specifically; collectively they're a documentation drift the next operator-Claude session may want to surface for an architecture.md update sweep.

16. **`ProvisionalSettlementSurfacingPayload` and `apply_manual_operator_resolution` not in `architecture.md`.** (§10.20; §5.4 b/c.) W8-shipped surface for operator-driven PROVISIONAL → terminal-state transitions; not described in architecture.md. Burst-review-adjacent.

---

## §12 — Self-assessment (per brief-drafting convention)

### §12.1 — Coverage against brief

- §3 pre-reads — read fully: `architecture.md` (721
  lines), `decisions.md` (1194 lines, read in three
  chunks), `v3_data_requirements.md` (202 lines),
  `project_context.md` (209 lines),
  `dr029/dr029_scope.md` (287 lines). Total 2613
  lines of canonical-doc reading before the
  inventory pass.
- §5.1 bet pillar — covered (§1 of this report).
  All five named files inventoried (`domain/bets/`,
  `store/schema/bets.py`, `store/repositories/bets.py`,
  all six `workflows/bet_entry/v1/` files,
  `domain/pricing/`, `domain/settlement/`). All
  five (a)–(e) questions answered with file +
  line citations.
- §5.2 account pillar — covered (§2). Three named
  files inventoried. Three (a)–(c) questions
  answered.
- §5.3 clients — covered (§3). Both client packages
  inventoried module-by-module; line counts and
  public surface enumerated. Three (a)–(c)
  questions answered.
- §5.4 reconciliation / settlement — covered (§4).
  Module structure for `reconciliation.py` and
  `settlement.py` inventoried; key entry points
  cited. Five (a)–(e) questions answered.
- §5.5 UI — covered (§5). Backend routers
  enumerated; frontend route structure enumerated.
  Four (a)–(d) questions answered.
- §5.6 ops / contracts / config — covered (§6).
  `.importlinter` enumerated verbatim;
  `pyproject.toml` enumerated. Four (a)–(d)
  questions answered.
- §5.7 tests — covered (§7). Per-pillar counts;
  fixture / conftest structure. Four (a)–(d)
  questions answered.
- §5.8 DR drift inventory — covered (§8). One row
  per DR for all 32 DRs. Both-side citations for
  every **divergent** finding.
- §5.9 missing-from-spec — covered (§9). 21 items
  with spec-source citations.
- §5.10 missing-from-architecture — covered (§10).
  20 items, each cited with shipped-file location
  and the plausible architecture.md section.
- §11 ranked summary — covered.
- §12 self-assessment — this section.

### §12.2 — Hard limits adherence (brief §9)

- §9.1 single bounded session — observed; one
  Claude Code session.
- §9.2 no code changes anywhere — observed. Zero
  edits to `bethub-v3/`. Zero edits to any
  rebuild folder canonical doc.
- §9.3 no remediation / fixes / scope creep —
  observed. No "this should be fixed by …", no
  fitness verdict, no overall verdict on the
  codebase's health. The findings in §11 are
  surfaced in plain language with severity
  ranking; triage is the next session's job per
  brief §10.
- §9.4 no Alembic, no debt-fixing — observed.
  Findings 6 and 7 in §11 document the deferred
  state but do not propose Alembic adoption.
- §9.5 operational guardrails — observed. No git
  operations. No DB writes. No external API
  calls. No tests run. No log file inspection
  beyond what `ops/` directory listing required.
  All timestamps in this report in Adelaide
  local per DR-021.

### §12.3 — Confidence-and-limitation notes

- **Pillar coverage:** The bet pillar inventory
  is comprehensive — every file in the named
  list was read end-to-end. Schema columns were
  captured verbatim from the DDL constants in
  `store/schema/bets.py:17-66`. Account pillar
  similar. Client pillar inventoried by line-count
  + top-level def/class enumeration (`grep -nE
  '^(def|class)'`) plus the `__init__.py`
  re-export list, but per-function signature
  detail was not enumerated for every client
  function (would scale the report past the
  brief's 600–1000 line budget). The brief §7
  empirical-verification commitment to "every
  public function with full signature, captured
  from the source" was satisfied for the bet
  pillar `BetRecordStorage` Protocol (§1.1) but
  not exhaustively for the betfair_client / vps_client
  surfaces — those are summarised at the contract-
  section / module-file granularity. If a follow-
  up triage needs per-function signatures from
  the clients side, this is the substrate that
  would have to expand.
- **Tests verification limit:** Test counts in §7
  are from `^\s*(async )?def test_` regex —
  parametrize-expansion test counts (what pytest
  collects) were not produced because §9.5
  prohibits running pytest. The reference baseline
  (549) is plausibly the pytest-collected count;
  this report's 533 is the function-definition
  count. The discrepancy is not a finding.
- **Contract surface comparison limit:** The
  client contracts are 87,934 and 39,420 bytes of
  dense surface. The §3.3(a) comparison
  established that the section / file mapping is
  1:1 but did not exhaustively verify every
  function signature against the contract spec.
  A "per-method contract conformance audit" would
  be a separate workstream.
- **Architecture.md vs DR drift question:** Some
  rows in §8 marked **N/A** are principles
  (DR-008, DR-012, DR-024) where shipped state
  is too thin to evaluate the principle's
  application. The brief framing
  ("**N/A** — DR is a principle without a shipped
  surface to compare against") was applied per
  the legend in §8.
- **`current_state.md` not read:** The brief §3
  reference-only list does not name
  `current_state.md`, and time-since-snapshot for
  shipped state matters less for a read-only
  inventory than for an operational read. The
  pre-W14 brief itself is the authoritative
  starting point and is dated 2026-05-11 22:31
  ACST — same-day baseline as this report's
  execution.
- **Surprises:** the most surprising finding was
  finding #12 (§11) — `domain/pricing/` and
  `domain/settlement/` are empty 0-line stubs
  while DR-030 §Layout names both as concrete
  destinations. The pricing math and settlement
  state-machine live under `workflows/bet_entry/v1/`
  — a layered-architecture inversion that doesn't
  appear in any DR / brief I read. Surfaced
  explicitly as a medium-severity drift item;
  the next session may want to investigate
  whether this was deliberate (workflow-owning
  what's-effectively-domain) or whether the
  W4/W6.5 build placed the modules at the
  workflow layer for orchestration-coupling
  reasons.
- **Three-way drift on DR-027 / DR-032 / shipped:**
  this is the drift the pre-W14 brief explicitly
  anticipated as "one drift we know about"
  (brief §2). The report captures both sides
  per §7's discipline; the substantive resolution
  is next-session work per brief §10.

### §12.4 — Output discipline

- Output file: `dr029/pre_w14_review/codebase_review_report.md`
  (this file).
- Length: 2857 lines (file `wc -l`) / 13,055 words /
  118 KB. The line count is high because the file
  is wrapped narrow (~50 chars); effective content
  length is approximately the upper end of the
  brief §8 "600–1000 lines, likely closer to 1000"
  anticipation. Empirical fidelity (verbatim DDL,
  Protocol signatures, both-side citations) is
  the driver per brief §7 / §8.
- No remediation proposals.
- No fitness judgement.
- No scope creep beyond the §5.1–§5.10 inventory
  + §11 summary + §12 self-assessment commissioned.
- Both sides cited for every drift finding.
- All timestamps Adelaide local per DR-021.
- No tests run, no DB writes, no git operations,
  no external API calls.

— End of report.
