# W14 brief — Cash flow event log + payees reference data

**Status:** locked Session 127.
**Lock anchor:** 2026-05-12 ACST (Adelaide local per DR-021;
exact lock timestamp captured in `sessions/SESSION_127.md`
at close).
**Workstream:** W14 (transactions / cash-flow event log —
the third operational-store sub-stream after W11 accounts
and W10 storage lift; first per-domain event log table to
ship in v3).
**Recipient:** Claude Code, single bounded session.
**Brief location:**
`dr029/w14_cash_flow/w14_cash_flow_brief.md`.

---

## §1 — What this brief is and is not

### §1.1 — What this brief is

This brief commissions Code to build the **cash flow event
log + payees reference data layer** for v3 — the schema,
Pydantic v2 domain models, and repository surface for two
new entities:

- **`cash_flow_events`** — append-only event log for the
  eight cash flow event types specified in
  `architecture.md` §A.2 spine + §A.5:
  `account_holder_funding`, `account_at_book_deposit`,
  `account_at_book_withdrawal`, `account_holder_remittance`,
  `account_at_book_balance_adjustment`,
  `account_holder_balance_adjustment`, `external_payment`,
  `profit_share_distribution`. Owns the substrate for
  Location 1 (per-account-at-book balance) and Location 2
  (per-custodian cash holding) derivation that W12 ships,
  plus the operation-net-flow informational view.
- **`payees`** — reference data table holding recipient
  identity for `external_payment` events (tax,
  infrastructure vendors, data subscriptions, tooling).
  Bundled into W14 because `external_payment` events are
  awkward without it.

W14 is the **first per-domain event log table** in v3. The
schema choices made here — the common event header
(`event_id`, `event_type`, `recorded_at`, `occurred_at`,
FK columns, `parent_event_id`, `supersedes_event_id`,
`payload` JSON, `source`, `correlation_id`, `notes`) and
the per-domain supersession semantics — establish the
pattern that W13 (`promo_events`) and W15 (`ops_events`)
will reuse. Coherence across the three tables is a load-
bearing design constraint per DR-027 (the two-database
architecture decision, with Session 124 amendment locking
the per-domain event-table internal shape).

The work ships as exactly five files, matching the W11
single-file-per-domain envelope:

- `domain/cash_flow/__init__.py` — Pydantic v2 domain
  models (common event header base + 8 event-type payload
  schemas discriminated on `event_type` + payee model).
- `store/schema/cash_flow.py` — DDL + idempotent
  migration for both `cash_flow_events` and `payees`
  tables.
- `store/repositories/cash_flow.py` — row dataclasses +
  `CashFlowEventRepository` (append-only writes,
  account- and correlation-scoped reads, supersession-
  chain walk for derived-state reads) + `PayeeRepository`
  (CRUD).
- `tests/store/test_cash_flow_schema.py` — schema-level
  tests (DDL, indexes, CHECK constraints, FK nullability,
  idempotent migration round-trip).
- `tests/store/test_cash_flow_repository.py` —
  repository tests (append, modification rejection,
  supersession-chain walk, correlation-id read, account-
  scoped pagination, payee CRUD round-trip).

Plus one additive edit to `store/__init__.py` adding the
new repository imports alongside existing
`accounts`/`bets` imports (W11/W4 precedent — this file
already exports per-domain repositories).

### §1.2 — What this brief is not

W14 v1 explicitly does **not** ship:

- **Balances** (W12 territory). Per-account-at-book
  balance derivation, Location 1 / Location 2 formulas,
  operation-net-flow informational view, cash-age FIFO
  surveillance, profit-share semantics resolution — all
  W12. W14 ships the event substrate; W12 ships the read-
  side derivation against it.
- **Promo events** (W13 territory). `promo_events` table,
  promo journey, FB inventory, AccountCare warnings — all
  W13. W14 doesn't touch `promo_events` even though
  finalised `promo_cash_credited` events feed Location 1
  (that's W12's read-side concern reading both tables).
- **Operations log** (W15 territory). `ops_events` table
  — all W15. W14 establishes the common event header
  pattern; W15 reuses it.
- **Day-0 opening seeding tool / runbook.** W14 makes
  day-0 *possible* via the `account_at_book_balance_
  adjustment` and `account_holder_balance_adjustment`
  event types carrying `adjustment_reason='day_0_opening'`
  in their payload schemas. The actual day-0 seeding pass
  at cutover (~$12.5k of working capital across
  custodians at v3 launch per `architecture.md` §A.5)
  fires from W16 (cutover from v2). Schema and write
  paths in W14; seeding tool / runbook in W16.
- **Cascade events.** Cascade scope per §A.7 lands in
  `promo_events` only (`free_bet_credited` /
  `promo_cash_credited` supersession on bet settlement
  change). `cash_flow_events` is pure external-event
  append; no auto-cascade trigger path. The common event
  header carries `supersedes_event_id` for shape
  uniformity across the three per-domain tables and for
  rare manual corrections to historical cash flow
  entries (operator typo on a deposit amount, etc.).
- **Burst Review surfaces.** Cash-age threshold breaches,
  cash flow anomaly surfacing in Burst Review — operator-
  surface work, separate later sub-stream.
- **Cash reconciliation surfaces.** Reports comparing
  W14 event writes against book statements / custodian
  transaction lists — separate later sub-stream.
  **Sequencing note: vision lists reconciliation as a
  BetHub job. W14 ships the substrate that reconciliation
  surfaces will read; the surfaces themselves come in a
  later sub-stream once the substrate is in place. This
  is sequencing, not divergence from vision.**
- **Operator entry UI.** Web/API entry paths for cash
  flow events (deposit form, withdrawal form, etc.) are
  W17+ operator-facing work. W14 ships the repository
  surface that future UI will call into.
- **Tier and phase fields on cash flow events.** Out per
  W11 deferral; tier/phase context applies to operational
  decisions, not cash flow accounting.
- **Persona → account vocabulary sweep.** Out per W11
  deferral.
- **Alembic adoption.** Carried per W10 / W11 deferrals.
  W14 follows the existing pre-Alembic schema pattern
  (`store/schema/accounts.py` and `store/schema/bets.py`
  precedent — inline `CREATE TABLE IF NOT EXISTS` DDL +
  idempotent migration helper).
- **SQLAlchemy Core migration.** DR-031 specifies
  SQLAlchemy Core for v3 but shipped storage layer uses
  raw `sqlite3` (Finding #6 from S123 review, parked).
  W14 follows the shipped pattern, not the DR-031 spec —
  the migration is a separate concern out of scope.

### §1.3 — Why W14 v1 has the scope it does

Three calls were made during brief drafting (Session 127);
naming them here for visibility:

- **`payees` bundled into W14** rather than spun as a
  W14.1 follow-up. `external_payment` events carry a
  payee FK; splitting `payees` out would leave one of
  the eight event types incomplete in W14 v1, creating
  asymmetry across the table's event-type surface.
  Bundling keeps the workstream self-contained.
- **Day-0 opening balances ship as schema substrate
  only.** The `*_balance_adjustment` event types support
  `adjustment_reason='day_0_opening'` payloads from
  W14 day-one, but the actual seeding pass (writing the
  ~$12.5k opening balances across custodians) belongs
  to W16 cutover. W14 makes day-0 possible; W16 fires
  it.
- **Reconciliation surfaces deferred to a later sub-
  stream.** Vision treats reconciliation as a BetHub
  job; W14 ships the queryable substrate that
  reconciliation reports will read against book
  statements and custodian transaction lists. Substrate
  first, surface after — the surface needs the
  substrate.

These are Cat 5 software/scope calls (operator-Claude
division of labour per `standing_instructions.md` Cat 5).
Operator can override at any time before Code lock.

---

## §2 — Why this work exists

W14 closes one of three per-domain event log tables
specified in `architecture.md` §A.2 — the **mutable bet
records plus three per-domain event log tables** spine
locked at the pre-W14 governance update arc (Sessions
S124+S125+S126). `cash_flow_events` is the first to ship
in code, ahead of `promo_events` (W13) and `ops_events`
(W15), because the dependency chain runs W14 → W12
(balance derivation reads cash flow events) → W13 (promos
attach to bets and credit cash) → W15 (ops events
observe the whole pipeline).

The pre-W14 governance update arc closed end-to-end at
S126 confirming the spec is propagation-clean (zero stale
`bet_placed.*` / `bet_settled.*` / `bet_voided` /
`bet_logged` references in `architecture.md` and
`v3_data_requirements.md`; only correct DR-027 amendment-
citing references remain). W14 builds against locked,
verified substrate.

The architectural anchors W14 implements:

- `architecture.md` §A.2 spine (per-domain event log
  table pattern + common event header) — line 99
  explicitly states "**W14 ships this table**".
- `architecture.md` §A.5 cash flow model (eight event
  types, two balance locations, bank-touching vs
  internal categorisation, day-0 opening mechanics,
  profit-share semantics).
- `architecture.md` §A.6 settlement state (referenced
  for `cash_returned` derivation that W12 will join
  against cash flow events).
- `architecture.md` §A.9 derivation rules (what's stored
  vs computed).
- `architecture.md` §A.10 canonical-reference-layer
  (Betfair as canonical source — context for FK
  conventions on the bet-side that cash flow events
  cross to via correlation_id).

The spec is locked. W14's job is to faithfully implement
it in code with the same shape the spec describes, plus
the tests that exercise the shape.

---

## §3 — Pre-reads

### §3.1 — Required reads (read before starting)

Read in order. These define what Code is implementing.

1. **`architecture.md`** §A.2 (lines ~91–168, the per-
   domain event log spine + common event header + 8
   cash_flow_events types detail + supersession
   semantics) — the load-bearing substrate. Read in
   full. §A.5 (lines ~334–414, cash flow model with
   bank-touching/internal categorisation, two balance
   locations, day-0 mechanics, profit-share semantics)
   — also read in full. §A.6 (lines ~414–471), §A.9
   (lines ~567–610), §A.10 (lines ~624–645) — read in
   full; each is short.
2. **`decisions.md`** — specific DRs and their Session
   124 amendments:
   - DR-027 (two-database architecture + Session 124
     amendment locking per-domain event-table internal
     shape). Read body + amendment.
   - DR-019 (derived state on read + Session 124
     amendment for materialised-view-on-entity-row
     pattern). **Critical asymmetry:** the amendment
     applies to bet records (mutable columns on the
     `bets` row) but NOT to cash flow events — cash
     flow events are pure event-log writes, not entity-
     row updates. The brief schema reflects this.
   - DR-030 (v3 repo layout + Session 124 amendment).
     `cash_flow` lives under `domain/cash_flow/` and
     `store/{schema,repositories}/cash_flow.py` per the
     existing pattern.
   - DR-032 (canonical-reference-layer / two-table bet
     record). Reference for how cash flow events join
     to bet records via `correlation_id` and (where
     applicable) `bets.cash_stake_amount` / per-bet
     computed `cash_returned`.
   - DR-022 (book / account / account-at-book
     vocabulary). FKs on cash flow events use this
     vocabulary.
   - DR-021 (timestamp anchoring, Adelaide local
     time). Common event header `recorded_at` and
     `occurred_at` are Adelaide-local ISO 8601.
3. **`dr029/w11_accounts/w11_accounts_brief.md`** and
   **`dr029/w11_accounts/w11_accounts_report.md`** —
   precedent. W11 is the most-recent operational-store
   sub-stream and the template W14 follows. Read both
   end-to-end. File layout, schema migration pattern,
   repository pattern, test pattern all come from W11.

### §3.2 — Reference-only (read on demand)

- **`standing_instructions.md`** — Cat 3 filesystem and
  tooling discipline applies. Critical entries: `create_
  file` is banned for filesystem work (use only Desktop
  Commander or `projects-filesystem`); verify every
  write; REPL discipline (write-script-to-`/tmp` +
  `start_process` over interactive REPL paste); pre-
  execution risk advisory for tool-limit and context-
  window (flag inline before large operations).
- **`vision.md`** — context for non-negotiables
  (trust-without-manual-reconciliation, cycle-visibility-
  end-to-end, Adelaide local time, operator-tax-near-
  zero). W14's substrate directly serves the first and
  fourth.
- **`governance.md`** — DR-029 close-out named debt and
  deferred capabilities. W14 inherits the three pieces
  of named debt (no test coverage / no migration
  framework / monolithic orchestrator file) cleanly: W14
  ships its own tests, uses the pre-Alembic schema
  pattern, doesn't touch VPS-side orchestrator.
- **`project_context.md`** — orientation primer if
  needed (vocabulary, four strategies, active arc
  context).
- **`v3_build_picture.md`** — current stream state and
  next-milestone labels. W14 is `in flight`; W13 / W15
  blocked-on-W14.
- Existing v3 codebase files (read-only browse for
  pattern confirmation):
  - `bethub-v3/store/schema/accounts.py` — schema
    migration pattern.
  - `bethub-v3/store/schema/bets.py` — schema migration
    pattern (more complex table; closer in event-table
    spirit).
  - `bethub-v3/store/repositories/accounts.py` —
    repository pattern.
  - `bethub-v3/store/repositories/bets.py` — repository
    pattern.
  - `bethub-v3/domain/accounts/__init__.py` — Pydantic
    domain-model pattern.
  - `bethub-v3/domain/bets/__init__.py` — Pydantic
    domain-model pattern (more complex).
  - `bethub-v3/store/__init__.py` — current exports
    surface; W14 adds cash_flow imports additively.

---

## §4 — System access

- **Read-write** on the v3 codebase at
  `/Users/tim/Desktop/Projects/bethub-v3/` — limited to
  the five new files named in §1.1 plus the additive
  edit to `store/__init__.py`. No other paths under
  `bethub-v3/`.
- **Read-only** on the rebuild folder at
  `/Users/tim/Desktop/Projects/bethub-rebuild/` for all
  reference reads named in §3.
- **No VPS access** (no SSH to the racing data capture
  host). W14 is operational-store work; no
  `capture.db` interaction.
- **No Betfair API access.** W14 is internal schema and
  application code; no external API calls.
- **No live database access** beyond the test
  SQLite databases the test suite creates and tears
  down. v3's operational store does not exist on disk
  yet; W14's schema migration creates the tables from
  scratch.
- **Filesystem tool:** Desktop Commander (`write_file`,
  `read_file`, `edit_block`, `list_directory`,
  `start_process`) or `projects-filesystem` MCP server
  (`write_file`, `edit_file`). `create_file` is banned
  per `standing_instructions.md` Cat 3 — it writes to a
  Claude-container sandbox path that mimics the Mac path
  shape but doesn't reach the Mac filesystem.
- **Adelaide local timestamps per DR-021** for every
  time-of-day reference in the report and for every
  timestamp value persisted to `cash_flow_events`
  (`recorded_at`, `occurred_at`) and `payees`
  (`created_at`, `updated_at`). ISO 8601 with timezone
  offset (`+09:30` ACST / `+10:30` ACDT). Use
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  via `start_process` for session-start and session-
  close anchors in the report.
- **Single bounded Code session.** If the work doesn't
  fit, that's a finding, not a continuation. Partial-
  but-coherent ship beats complete-but-lost-coherence.

---

## §5 — Substantive scope

### §5.1 — Domain models (`domain/cash_flow/__init__.py`)

Pydantic v2 models defining the in-process shape of cash
flow events and payee reference records. Strict (`extra=
'forbid'`); type-checked at boundary; the schema is the
contract between writers and readers within v3.

**§5.1.1 — Common event header base class.**

```python
class CashFlowEventBase(BaseModel):
    event_id: UUID
    event_type: CashFlowEventType  # closed enum
    recorded_at: datetime  # Adelaide-local, tz-aware
    occurred_at: datetime  # Adelaide-local, tz-aware
    account_id: UUID | None = None
    book_id: UUID | None = None
    account_at_book_id: UUID | None = None
    parent_event_id: UUID | None = None
    supersedes_event_id: UUID | None = None
    payload: CashFlowEventPayload  # discriminated union
    source: CashFlowEventSource  # operator | system | integration
    correlation_id: UUID | None = None
    notes: str | None = None

    model_config = ConfigDict(extra='forbid', frozen=True)
```

Notes:
- `datetime` fields are tz-aware. Validate that the
  timezone is Adelaide (ACST/ACDT) at construction; reject
  naive datetimes or non-Adelaide tz.
- `frozen=True` enforces immutability at the Pydantic
  layer (events are append-only; the only way to "edit"
  is to write a new event with `supersedes_event_id`).
- The closed enums `CashFlowEventType` and
  `CashFlowEventSource` live in the same module as
  string-valued `StrEnum` subclasses.

**§5.1.2 — `CashFlowEventType` enum (closed, 8 values).**

```python
class CashFlowEventType(StrEnum):
    ACCOUNT_HOLDER_FUNDING = 'account_holder_funding'
    ACCOUNT_AT_BOOK_DEPOSIT = 'account_at_book_deposit'
    ACCOUNT_AT_BOOK_WITHDRAWAL = 'account_at_book_withdrawal'
    ACCOUNT_HOLDER_REMITTANCE = 'account_holder_remittance'
    ACCOUNT_AT_BOOK_BALANCE_ADJUSTMENT = (
        'account_at_book_balance_adjustment')
    ACCOUNT_HOLDER_BALANCE_ADJUSTMENT = (
        'account_holder_balance_adjustment')
    EXTERNAL_PAYMENT = 'external_payment'
    PROFIT_SHARE_DISTRIBUTION = 'profit_share_distribution'
```

`CashFlowEventSource`: `OPERATOR`, `SYSTEM`,
`INTEGRATION`.

**§5.1.3 — Per-event-type payload schemas.**

Each event type has its own payload subclass. The
`CashFlowEventPayload` field on `CashFlowEventBase` is a
discriminated `Annotated[Union[...], Field(discriminator
='event_type_payload')]` over these subclasses, keyed
off a `event_type_payload` literal discriminator that
matches the parent's `event_type`.

Eight payload schemas, one per event type:

- **`AccountHolderFundingPayload`** — Tim → custodian.
  Fields: `amount: Decimal` (positive); `reference:
  str | None` (bank-transfer reference or operator
  note). The custodian is identified by the parent
  event's `account_id` (the account-holder being
  funded).
- **`AccountAtBookDepositPayload`** — custodian →
  account-at-book. Fields: `amount: Decimal` (positive);
  `reference: str | None`. The (account, book,
  account-at-book) is identified by the parent event's
  FK fields.
- **`AccountAtBookWithdrawalPayload`** — book →
  custodian. Fields: `amount: Decimal` (positive);
  `reference: str | None`.
- **`AccountHolderRemittancePayload`** — custodian →
  Tim's bank. Fields: `amount: Decimal` (positive);
  `reference: str | None`.
- **`AccountAtBookBalanceAdjustmentPayload`** — book-
  side non-bet/non-promo correction. Fields: `amount:
  Decimal` (signed — can be positive or negative);
  `adjustment_reason: BookSideAdjustmentReason` (closed
  enum: `DAY_0_OPENING`, `BOOK_CORRECTION`, `OTHER`);
  `context: str | None` (operator note explaining the
  correction).
- **`AccountHolderBalanceAdjustmentPayload`** —
  custodian-side non-flow correction (Session 13
  amendment). Fields: `amount: Decimal` (signed);
  `adjustment_reason: CustodianSideAdjustmentReason`
  (closed enum: `DAY_0_OPENING`,
  `CUSTODIAN_COUNTING_CORRECTION`, `OTHER`); `context:
  str | None`. Day-one use: day-0 opening balances on
  custodian holdings via `DAY_0_OPENING`.
- **`ExternalPaymentPayload`** — operational outflow to
  a payee. Fields: `amount: Decimal` (positive);
  `payee_id: UUID` (FK to `payees`); `category:
  ExternalPaymentCategory` (closed enum: `TAX`,
  `INFRASTRUCTURE`, `DATA_SUBSCRIPTION`, `TOOLING`,
  `OTHER`); `reference: str | None`.
- **`ProfitShareDistributionPayload`** — distribution to
  the account holder personally. Fields: `amount:
  Decimal` (positive); `funding_source:
  ProfitShareFundingSource` (closed enum: `TIM_DIRECT`,
  `ACCOUNT_HOLDER_CASH_HOLDING`); `recipient_context:
  str | None`. The `TIM_DIRECT` variant is a bank
  outflow; the `ACCOUNT_HOLDER_CASH_HOLDING` variant
  reduces Location 2 directly without bank touch (per
  §A.5 profit-share semantics).

**§5.1.4 — FK field nullability rules per event type.**

The `account_id` / `book_id` / `account_at_book_id`
fields on the common event header are nullable
generically, but each event type has specific
expectations. Code enforces these via Pydantic
`model_validator` on the parent or on each payload
subclass:

- `account_holder_funding`: `account_id` REQUIRED
  (the custodian being funded); `book_id` and
  `account_at_book_id` MUST be None.
- `account_at_book_deposit`: `account_id`, `book_id`,
  `account_at_book_id` ALL REQUIRED.
- `account_at_book_withdrawal`: same as deposit — all
  three FK fields REQUIRED.
- `account_holder_remittance`: `account_id` REQUIRED;
  `book_id` and `account_at_book_id` MUST be None.
- `account_at_book_balance_adjustment`: all three FK
  fields REQUIRED.
- `account_holder_balance_adjustment`: `account_id`
  REQUIRED; `book_id` and `account_at_book_id` MUST be
  None.
- `external_payment`: all three FK fields MUST be None
  (payments to non-account-holder payees;
  recipient identity sits in payload via `payee_id`).
- `profit_share_distribution`: `account_id` REQUIRED;
  `book_id` and `account_at_book_id` MUST be None.

These rules are tested in
`test_cash_flow_repository.py` (invalid combinations
should fail validation at construction time).

**§5.1.5 — `Payee` reference model.**

```python
class Payee(BaseModel):
    payee_id: UUID
    name: str  # non-empty, max 200 chars
    category: ExternalPaymentCategory
    notes: str | None = None
    created_at: datetime  # Adelaide-local, tz-aware
    updated_at: datetime  # Adelaide-local, tz-aware

    model_config = ConfigDict(extra='forbid')
```

Note: `Payee` is NOT frozen — payee records are mutable
reference data (a vendor's notes can be updated, etc.).
Only the event log itself is append-only-immutable.

`ExternalPaymentCategory` is shared between
`ExternalPaymentPayload.category` and `Payee.category`
— a payee's default category is the category that
applies to most external_payment events written to it,
but each event independently carries its own category
(a payee can have payments in multiple categories
without conflict).

### §5.2 — Schema (`store/schema/cash_flow.py`)

SQLite DDL + idempotent migration helper. Pattern
follows `store/schema/accounts.py` and
`store/schema/bets.py` precedent — inline `CREATE TABLE
IF NOT EXISTS`, indexes after, idempotent migration
function callable from a future Alembic adoption.

**§5.2.1 — `cash_flow_events` table DDL.**

```sql
CREATE TABLE IF NOT EXISTS cash_flow_events (
    event_id            TEXT PRIMARY KEY NOT NULL,
    event_type          TEXT NOT NULL
        CHECK (event_type IN (
            'account_holder_funding',
            'account_at_book_deposit',
            'account_at_book_withdrawal',
            'account_holder_remittance',
            'account_at_book_balance_adjustment',
            'account_holder_balance_adjustment',
            'external_payment',
            'profit_share_distribution'
        )),
    recorded_at         TEXT NOT NULL,
    occurred_at         TEXT NOT NULL,
    account_id          TEXT,
    book_id             TEXT,
    account_at_book_id  TEXT,
    parent_event_id     TEXT
        REFERENCES cash_flow_events(event_id),
    supersedes_event_id TEXT
        REFERENCES cash_flow_events(event_id),
    payload             TEXT NOT NULL,
    source              TEXT NOT NULL
        CHECK (source IN (
            'operator', 'system', 'integration')),
    correlation_id      TEXT,
    notes               TEXT,
    FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),
    FOREIGN KEY (book_id)
        REFERENCES books(book_id),
    FOREIGN KEY (account_at_book_id)
        REFERENCES accounts_at_book(account_at_book_id)
);
```

Notes on DDL choices:

- All UUIDs stored as TEXT (W11 precedent — SQLite
  has no native UUID type; the application layer
  converts).
- Timestamps stored as TEXT (ISO 8601 with timezone
  offset). W11 precedent.
- `payload` stored as TEXT (JSON serialised at write,
  parsed at read). SQLite has a JSON1 extension but
  application-side JSON handling is simpler and
  matches the bets-row pattern for JSON columns.
- `parent_event_id` and `supersedes_event_id` are
  self-referential FKs (an event can be a child of
  another event in the same table; an event can
  supersede another event in the same table).
- The CHECK constraint on `event_type` enforces the
  closed enum at the database layer (defence-in-depth
  alongside the Pydantic enum).
- The CHECK constraint on `source` does the same.
- FK constraints to `accounts`, `books`,
  `accounts_at_book` (W11 tables) enforce referential
  integrity against the operational store's account
  vocabulary. FKs are nullable in the schema; per-
  event-type non-null rules are enforced at the
  Pydantic layer (per §5.1.4) rather than at SQL
  layer (SQLite CHECK constraints with conditional
  nullability are awkward; Pydantic handles it more
  cleanly).
- No `payees` FK at the schema layer for
  `external_payment` events — the FK is encoded in the
  `payload.payee_id` field. Per-event-type payload
  validation handles referential integrity at
  application layer. (Alternative: extract `payee_id`
  as a typed column on `cash_flow_events`. Rejected
  because it makes the cash flow events table carry a
  column relevant to only one of eight event types,
  bloating the schema. Application-layer enforcement
  via the repository is the cleaner pattern at this
  scale.)

**§5.2.2 — `cash_flow_events` indexes.**

Six indexes, sized to the read patterns:

```sql
CREATE INDEX IF NOT EXISTS
    idx_cash_flow_events_account_at_book
    ON cash_flow_events(account_at_book_id, recorded_at);

CREATE INDEX IF NOT EXISTS
    idx_cash_flow_events_account
    ON cash_flow_events(account_id, recorded_at);

CREATE INDEX IF NOT EXISTS
    idx_cash_flow_events_book
    ON cash_flow_events(book_id, recorded_at);

CREATE INDEX IF NOT EXISTS
    idx_cash_flow_events_event_type
    ON cash_flow_events(event_type, recorded_at);

CREATE INDEX IF NOT EXISTS
    idx_cash_flow_events_correlation
    ON cash_flow_events(correlation_id);

CREATE INDEX IF NOT EXISTS
    idx_cash_flow_events_supersedes
    ON cash_flow_events(supersedes_event_id);
```

Rationale: the four primary read access patterns (per
account-at-book for Location 1 balance, per account-
holder for Location 2 balance, per book for book-side
reporting, per event-type for analytics) all benefit
from a `(scope_col, recorded_at)` composite. The
`correlation_id` index supports cycle reconstruction
queries (find all events in a single operational unit).
The `supersedes_event_id` index supports supersession-
chain walks at read time per DR-019.

**§5.2.3 — `payees` table DDL.**

```sql
CREATE TABLE IF NOT EXISTS payees (
    payee_id    TEXT PRIMARY KEY NOT NULL,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL
        CHECK (category IN (
            'tax', 'infrastructure', 'data_subscription',
            'tooling', 'other')),
    notes       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payees_category
    ON payees(category);
```

Simple reference data shape. No FK constraints inbound
(events reference payees by id in payload JSON; no
outbound cascade concern at the DB layer).

**§5.2.4 — Migration helper.**

Single `apply_migrations(conn: sqlite3.Connection) ->
None` function callable from W11's existing migration
runner (or directly from tests). Pattern matches
`store/schema/accounts.py` precedent — sequential DDL
execution, idempotent on re-run.

The function:
1. Enables foreign keys (`PRAGMA foreign_keys = ON`)
   if not already set.
2. Creates `payees` table first (no inbound FK
   dependencies).
3. Creates `cash_flow_events` table second (depends on
   accounts/books/accounts_at_book from W11).
4. Creates all indexes.
5. Validates the schema by reading
   `sqlite_master` and confirming both tables and all
   indexes are present.

Re-run safety: every DDL statement uses `IF NOT
EXISTS`. Running `apply_migrations` on an already-
migrated DB is a no-op.

### §5.3 — Repository (`store/repositories/cash_flow.py`)

Row dataclasses plus two repository classes:
`CashFlowEventRepository` (append-only writes, scoped
reads, supersession-aware reads) and `PayeeRepository`
(CRUD). W11 precedent: each repository holds the
SQLite-side row conversion plus the methods consumers
call into.

**§5.3.1 — Row dataclasses.**

```python
@dataclass(frozen=True)
class CashFlowEventRow:
    event_id: str
    event_type: str
    recorded_at: str
    occurred_at: str
    account_id: str | None
    book_id: str | None
    account_at_book_id: str | None
    parent_event_id: str | None
    supersedes_event_id: str | None
    payload: str  # JSON-serialised
    source: str
    correlation_id: str | None
    notes: str | None

@dataclass(frozen=True)
class PayeeRow:
    payee_id: str
    name: str
    category: str
    notes: str | None
    created_at: str
    updated_at: str
```

Frozen — rows are read-side snapshots, not mutable
state. Conversion to/from Pydantic domain models
happens at the repository boundary.

**§5.3.2 — `CashFlowEventRepository` interface.**

Write surface:

- `append_event(event: CashFlowEventBase) -> UUID` —
  serialises to JSON, executes INSERT, returns the
  new event_id. Rejects any attempt to write an event
  whose `event_id` already exists in the table
  (PRIMARY KEY constraint catches this; repository
  surfaces a clear `DuplicateEventError`).
- No update methods. No delete methods. Events are
  immutable once written. The supersession mechanism
  (writing a new event with `supersedes_event_id` set
  to the prior event's id) is the only "correction"
  path.

Read surface (all reads return Pydantic domain models,
not raw rows):

- `get_event(event_id: UUID) -> CashFlowEventBase` —
  fetch by id; raises `EventNotFoundError` if absent.
- `list_by_account_at_book(account_at_book_id: UUID,
  event_type: CashFlowEventType | None = None, limit:
  int = 1000, offset: int = 0) -> list[
  CashFlowEventBase]` — paginated, optionally
  filtered by event type, ordered by `recorded_at
  ASC`.
- `list_by_account(account_id: UUID, event_type:
  CashFlowEventType | None = None, limit: int = 1000,
  offset: int = 0) -> list[CashFlowEventBase]` — same
  shape, scoped to account-holder.
- `list_by_book(book_id: UUID, event_type:
  CashFlowEventType | None = None, limit: int = 1000,
  offset: int = 0) -> list[CashFlowEventBase]` — same
  shape, scoped to book.
- `list_by_event_type(event_type: CashFlowEventType,
  limit: int = 1000, offset: int = 0) -> list[
  CashFlowEventBase]` — for analytics scans.
- `list_by_correlation_id(correlation_id: UUID) ->
  list[CashFlowEventBase]` — for cycle reconstruction;
  ordered by `recorded_at ASC`.

Supersession-aware reads (the DR-019 read-time
derivation surface):

- `latest_non_superseded_by_scope(account_at_book_id:
  UUID | None = None, account_id: UUID | None = None,
  book_id: UUID | None = None, event_type:
  CashFlowEventType | None = None) -> list[
  CashFlowEventBase]` — returns only events that have
  NOT been superseded by a later event. Implementation:
  LEFT JOIN against `cash_flow_events` self on
  `supersedes_event_id`, filter where the join is
  NULL. At least one scope filter must be provided
  (raises `ValueError` if all four are None — full-
  table superseded scans are not a supported read
  pattern; W12 derivations will always have a scope).
- `walk_supersession_chain(event_id: UUID) -> list[
  CashFlowEventBase]` — returns the full chain from
  the given event back to the original (i.e., walks
  `supersedes_event_id` pointers iteratively).
  Ordered earliest-first. Cycle detection raises
  `SupersessionCycleError` (should never occur with
  correct writes but defends against corruption).

**§5.3.3 — `PayeeRepository` interface.**

Standard CRUD shape, matching `AccountRepository`
precedent from W11:

- `create_payee(payee: Payee) -> UUID` — insert;
  `DuplicateEntityError` if `payee_id` already exists.
- `get_payee(payee_id: UUID) -> Payee` — fetch;
  `EntityNotFoundError` if absent.
- `update_payee(payee_id: UUID, name: str | None =
  None, category: ExternalPaymentCategory | None =
  None, notes: str | None = None) -> Payee` — partial
  update; updates `updated_at` to current Adelaide-
  local timestamp; returns updated record.
- `list_payees(category: ExternalPaymentCategory |
  None = None) -> list[Payee]` — optionally filtered
  by category; ordered by `name ASC`.
- No delete method. Payees are reference data and a
  deleted payee would orphan historical
  `external_payment` events. If a payee becomes
  inactive operationally, that's an operator-facing
  flag for future work (add an `is_active` column if
  the need surfaces).

**§5.3.4 — Error types.**

Define module-level exception classes consistent with
W11 patterns:

```python
class CashFlowEventError(Exception):
    """Base for cash flow event repository errors."""

class DuplicateEventError(CashFlowEventError):
    """Event with this event_id already exists."""

class EventNotFoundError(CashFlowEventError):
    """No event found for this event_id."""

class SupersessionCycleError(CashFlowEventError):
    """Cycle detected in supersession chain."""

class InvalidScopeError(CashFlowEventError):
    """At least one scope filter required."""
```

Plus the Payee equivalents (`PayeeError`,
`DuplicateEntityError`, `EntityNotFoundError`).
W11 precedent: errors live in the repository module,
not in a separate `errors.py`.

**§5.3.5 — JSON payload handling.**

The repository serialises Pydantic payload subclasses
to JSON at write time via Pydantic's
`model_dump_json()` and parses at read time via
`event_type`-keyed dispatch into the right subclass.
Pattern:

```python
def _row_to_event(row: CashFlowEventRow) -> CashFlowEventBase:
    payload_cls = _PAYLOAD_BY_EVENT_TYPE[row.event_type]
    payload = payload_cls.model_validate_json(row.payload)
    return CashFlowEventBase(
        event_id=UUID(row.event_id),
        event_type=CashFlowEventType(row.event_type),
        recorded_at=datetime.fromisoformat(row.recorded_at),
        occurred_at=datetime.fromisoformat(row.occurred_at),
        # ... etc
        payload=payload,
    )
```

Where `_PAYLOAD_BY_EVENT_TYPE` is a module-level dict
mapping each `CashFlowEventType` to its payload class.

Datetime parsing/formatting uses ISO 8601 with offset
(`fromisoformat` handles `+09:30`/`+10:30` cleanly in
Python 3.11+; project is on 3.12 per pyproject).

### §5.4 — `store/__init__.py` additive edit

The existing `store/__init__.py` (already modified in
W10/W11 in-flight work — see dirty-tree state in §9.7)
exports per-domain repositories. W14 adds:

```python
from store.repositories.cash_flow import (
    CashFlowEventRepository,
    PayeeRepository,
)
```

This edit is **additive only**. Existing imports from
`store.repositories.accounts` and
`store.repositories.bets` must remain untouched. See
§9.7 dirty-tree handling for the discipline.

### §5.5 — Tests

Two test files following the W11 precedent split
(schema-level tests separate from repository-level
tests). Test infrastructure: pytest, in-memory SQLite
(`:memory:` connections via the existing
`tests/conftest.py` fixtures).

**§5.5.1 — `tests/store/test_cash_flow_schema.py`.**

Tests:

- `test_apply_migrations_creates_tables` — runs
  `apply_migrations` on a fresh in-memory DB,
  confirms both `cash_flow_events` and `payees`
  tables exist via `sqlite_master` query.
- `test_apply_migrations_creates_indexes` — confirms
  all seven indexes (six on cash_flow_events, one on
  payees) exist.
- `test_apply_migrations_idempotent` — runs
  `apply_migrations` twice on the same connection;
  second run is a no-op.
- `test_event_type_check_constraint` — attempts a
  raw INSERT with an invalid `event_type` value;
  expects SQLite `IntegrityError`.
- `test_source_check_constraint` — same for invalid
  `source`.
- `test_payee_category_check_constraint` — same for
  invalid payee category.
- `test_fk_constraints_to_accounts_w11_tables` —
  apply both W11 (`accounts.apply_migrations`) and
  W14 schemas; insert an event referencing a non-
  existent `account_id`; expect FK violation when FK
  enforcement is enabled.
- `test_self_referential_fk_parent_event` — insert
  two events where the second's `parent_event_id`
  references the first; assert FK accepts it. Then
  insert with non-existent `parent_event_id`; expect
  FK violation.
- `test_self_referential_fk_supersedes_event` — same
  shape for `supersedes_event_id`.

**§5.5.2 — `tests/store/test_cash_flow_repository.py`.**

Tests grouped by surface:

*Append:*
- `test_append_event_returns_event_id` — append a
  valid event; assert event_id round-trips.
- `test_append_duplicate_event_id_raises` —
  attempting to append with an existing event_id
  raises `DuplicateEventError`.
- `test_append_each_event_type` — eight tests (one
  per event type) constructing a valid event of that
  type, appending it, fetching it back, asserting
  payload round-trips correctly. Critical for
  confirming the discriminated union pattern works
  end-to-end.

*FK rules per event type (per §5.1.4):*
- `test_fk_rules_account_holder_funding` — constructs
  with `account_id` only set; passes. Constructs with
  `book_id` set; Pydantic validation fails.
- `test_fk_rules_account_at_book_deposit` — requires
  all three FKs; missing any raises validation
  error.
- (One test per event type covering its FK
  expectations.)

*Reads:*
- `test_get_event_returns_pydantic_model` — append,
  get_event, assert returned value is correct
  payload subclass.
- `test_get_event_not_found_raises` — get_event with
  random UUID raises `EventNotFoundError`.
- `test_list_by_account_at_book_paginates` — append
  10 events to one account_at_book; list with limit=5
  returns 5; offset=5 returns next 5.
- `test_list_by_account_at_book_filters_by_event_type`
  — append events of multiple types to the same
  account_at_book; list with event_type filter
  returns only matching.
- `test_list_by_correlation_id_returns_full_cycle` —
  append three events with the same correlation_id
  (simulating a cycle: deposit → bet stake out →
  cash return in); list_by_correlation_id returns
  all three in `recorded_at` ASC order.
- `test_list_by_event_type_scans_table` — for
  analytics-style reads.
- `test_list_by_book` — book-scoped reads.

*Supersession:*
- `test_latest_non_superseded_excludes_superseded` —
  append event A; append event B with
  `supersedes_event_id=A`; query
  `latest_non_superseded_by_scope` for that
  account_at_book; assert only B returned, A
  excluded.
- `test_walk_supersession_chain` — append A → B
  (supersedes A) → C (supersedes B);
  walk_supersession_chain(C) returns [A, B, C].
- `test_supersession_cycle_detected` — synthetic
  corruption: insert two events A and B where
  A.supersedes=B and B.supersedes=A;
  walk_supersession_chain raises
  `SupersessionCycleError`.
- `test_latest_non_superseded_requires_scope` —
  calling with all-None scopes raises
  `InvalidScopeError`.

*Adelaide timestamp validation:*
- `test_naive_datetime_rejected` — Pydantic
  validation rejects events with naive (tz-unaware)
  datetimes for `recorded_at` or `occurred_at`.
- `test_non_adelaide_tz_rejected` — Pydantic
  validation rejects events with `recorded_at` in
  e.g. UTC.

*Payees:*
- `test_create_get_payee_round_trip` — create payee,
  get_payee, assert equal.
- `test_create_duplicate_payee_id_raises` —
  attempting to create with existing payee_id
  raises `DuplicateEntityError`.
- `test_update_payee_updates_timestamp` — update
  partial; assert `updated_at` advances.
- `test_list_payees_filters_by_category` — create
  payees of multiple categories; list with category
  filter returns only matching.

Target ~30–40 individual tests across the two files.
Test count is not a hard line — Code adds tests where
the surface warrants and drops where the test would be
redundant against a clearer earlier test.

---

## §6 — Sequencing within session

### §6.1 — Pre-build alignment check against shipped substrate

Before any new files are written, Code reads the existing
v3 storage layer and confirms the brief's assumptions
hold. Five checks, ~5 minutes of session budget; catches
a class of expensive rework cheaply.

1. **W11 schema present.** Read
   `store/schema/accounts.py`. Confirm `apply_migrations()`
   function exists; creates `accounts`, `books`,
   `accounts_at_book` tables with PKs `account_id`,
   `book_id`, `account_at_book_id` (UUIDs as TEXT); FKs
   enforced. W14's FK targets in §5.2.1 depend on this.
2. **W11 repositories present.** Read
   `store/repositories/accounts.py`. Confirm the pattern
   (row dataclasses + repository classes + error types in
   the same file). W14 follows the same shape in §5.3.
3. **W11 domain models present.** Read
   `domain/accounts/__init__.py`. Confirm Pydantic v2
   idiom (StrEnum closed enums, `model_config` with
   `extra='forbid'`, tz-aware datetime handling).
4. **W4/W6 bets JSON-column pattern.** Read
   `store/schema/bets.py` and
   `store/repositories/bets.py`. The bets layer has JSON
   columns (`last_read_market_state`,
   `active_warnings_at_log`, etc.). W14's `payload`
   column follows the same JSON serialisation/parsing
   convention. Confirm so W14 doesn't invent a different
   one.
5. **`store/__init__.py` snapshot.** Read the file.
   Snapshot the existing imports surface so the additive
   edit (§5.4) knows what to add alongside and what NOT
   to touch.

If any check reveals divergence between brief assumptions
and shipped substrate, Code: surfaces immediately under a
clear "Alignment finding" header in the report; halts
further work pending operator-Claude triage; does not
attempt to bridge the divergence unilaterally (that would
be scope creep per §9.1).

### §6.2 — Build order

Order matters because each layer reads against the
prior. Recommended sequence, with rationale:

1. **Schema first** (`store/schema/cash_flow.py`). The
   DDL is the substrate everything else exercises.
   Implement DDL, indexes, and `apply_migrations`.
2. **Schema tests** (`tests/store/test_cash_flow_
   schema.py`). Confirms substrate is correct before
   building on it. Catches DDL bugs cheaply (CHECK
   constraints, FK references, idempotency).
3. **Domain models** (`domain/cash_flow/__init__.py`).
   Pydantic shapes against the locked DDL. The
   discriminated-union pattern is the trickiest piece;
   isolate it here before the repository layer adds
   the JSON round-trip concern.
4. **Repository** (`store/repositories/cash_flow.py`).
   Both `CashFlowEventRepository` and
   `PayeeRepository`. Uses both schema and domain
   models.
5. **Repository tests** (`tests/store/test_cash_flow_
   repository.py`). Largest test surface; built last.
6. **Additive `store/__init__.py` edit.** Adds the
   new repository imports. Performed last so it
   doesn't break imports during incremental builds.

Code is free to deviate when a different order is
operationally cleaner — e.g., write a few domain
models first to clarify the schema's payload shape
expectations, then come back to finish the schema.
But the broad order (substrate → models → repository
→ tests-throughout) is the discipline.

**Test-as-you-go preferred over tests-at-end.** Each
new method tested before moving to the next. W11
report flagged this as the practice that caught
several mid-flight design issues before they
compounded.

---

## §7 — Empirical verification

Code captures pre- and post-baselines so the report
shows what moved.

### §7.1 — Pre-baselines (capture at session open)

Capture once at the start, before any edits:

- `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  — session-start Adelaide-local anchor.
- `git -C /Users/tim/Desktop/Projects/bethub-v3 status
  --short` — full working-tree snapshot. **This is the
  baseline the §9.7 dirty-tree discipline protects.**
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/domain/`
  — confirm `cash_flow/` does NOT exist yet.
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/store/
  schema/` — confirm `cash_flow.py` does NOT exist
  yet.
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/store/
  repositories/` — confirm `cash_flow.py` does NOT
  exist yet.
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/tests/
  store/` — confirm `test_cash_flow_*.py` files do
  NOT exist yet.
- `wc -l /Users/tim/Desktop/Projects/bethub-v3/store/
  __init__.py` — line count baseline for the additive
  edit.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/store/ -q 2>&1 | tail -20` — confirm
  existing W11/W10 tests pass on the dirty tree (this
  is the regression baseline; W14's edits should not
  break it).

### §7.2 — Post-baselines (capture at session close)

After all edits land:

- `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  — session-close Adelaide-local anchor.
- `git -C /Users/tim/Desktop/Projects/bethub-v3 status
  --short` — post-edit snapshot. Confirm: every entry
  from §7.1's snapshot still present (un-committed
  W10/W11/Betfair work untouched); new entries for
  W14's five files (`?? domain/cash_flow/`,
  `?? store/schema/cash_flow.py`,
  `?? store/repositories/cash_flow.py`,
  `?? tests/store/test_cash_flow_schema.py`,
  `?? tests/store/test_cash_flow_repository.py`); and
  one change to existing entry (`M store/__init__.py`
  if it was modified previously, else `?? `).
- `git -C /Users/tim/Desktop/Projects/bethub-v3 diff
  store/__init__.py` — confirm the additive edit
  adds only the cash_flow imports, removes nothing.
- `wc -l` on every new file — record line counts.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/store/test_cash_flow_schema.py
  tests/store/test_cash_flow_repository.py -v 2>&1` —
  full test run for the new suites. Capture in the
  report.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/store/ -q 2>&1 | tail -20` — full
  `tests/store/` run to confirm no regression in W11/
  W10 suites.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  mypy domain/cash_flow store/schema/cash_flow.py
  store/repositories/cash_flow.py 2>&1 | tail -20` —
  type-check the new code.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  ruff check domain/cash_flow store/schema/cash_flow.py
  store/repositories/cash_flow.py
  tests/store/test_cash_flow_schema.py
  tests/store/test_cash_flow_repository.py 2>&1` —
  lint the new code.

### §7.3 — File-existence and content checks

For each of the five new files:

- File present at expected path.
- Line count within ballpark (rough guides — file
  sizes are not hard limits, just sanity checks):
  - `domain/cash_flow/__init__.py`: ~200–350 lines.
  - `store/schema/cash_flow.py`: ~100–180 lines.
  - `store/repositories/cash_flow.py`: ~300–500 lines.
  - `tests/store/test_cash_flow_schema.py`: ~150–250
    lines.
  - `tests/store/test_cash_flow_repository.py`:
    ~400–700 lines.
- Spot-check via `head -20` and `tail -20` confirms
  expected module structure (imports at top, class
  definitions, no truncation at end).

### §7.4 — Spot-check: end-to-end round-trip

After all writes land, run a one-shot Python script
via `start_process` (write to `/tmp/w14_smoke.py`,
not interactive REPL — per Cat 3 REPL discipline) that:

1. Opens an in-memory SQLite connection.
2. Applies W11 migrations (accounts/books/
   accounts_at_book), then W14 migrations.
3. Inserts a test account, book, account-at-book.
4. Creates a `CashFlowEventRepository` instance.
5. Appends one event of each of the 8 event types
   (constructing valid payloads per §5.1.4 FK rules).
6. Reads them back via `list_by_account_at_book` (for
   the events that scope to account-at-book) and
   `list_by_account` (for the events that scope to
   account-holder only).
7. Writes a supersedes event for one of the
   adjustments; queries `latest_non_superseded_by_
   scope`; asserts the original is excluded.
8. Walks the supersession chain; asserts the chain
   shape.
9. Prints a one-line summary: "8/8 event types round-
   trip OK; supersession-chain walk OK; latest-non-
   superseded read OK." or surfaces the failure.

This is belt-and-braces alongside the pytest suite —
the smoke check exercises the integration shape end-
to-end in one pass, fast.

---

## §8 — Output spec

Single report at exactly this path:

`dr029/w14_cash_flow/w14_cash_flow_report.md`

Section structure (Code writes this; not a template):

1. **Summary** — one paragraph: what landed, line
   counts per file, test count and pass/fail status,
   any findings.
2. **Anchors** — session-start and session-close
   Adelaide-local timestamps; commit hash of the v3
   repo at session start (whatever it was — Code does
   not commit).
3. **What was built** — per-file walk-through (one
   short paragraph per file), naming the major
   classes/functions added and any design choices
   worth surfacing. Brief; the code is the
   substrate.
4. **Verification results** — outputs of §7.2 / §7.3
   / §7.4 checks. Include the full pytest output for
   the new suites; tail outputs for mypy and ruff;
   the smoke-script one-liner.
5. **Findings** — anything Code noticed during
   implementation that the operator-Claude next
   session should triage. Five categories:
   (a) spec ambiguities encountered (place where the
   brief or architecture spec was unclear and Code
   made a call);
   (b) deferred concerns (small items Code chose not
   to expand the brief for, with rationale);
   (c) integration surprises (interactions with W11
   code that weren't anticipated);
   (d) tests that pass for the wrong reason
   (anything Code can identify where a test passes
   but the underlying assertion is weak);
   (e) anything else.
6. **Dirty-tree adherence statement** — confirms §9.7
   discipline held end-to-end. Include the
   pre/post `git status --short` outputs verbatim so
   the operator-Claude next session can verify.
7. **Self-assessment** — one short paragraph: did the
   work fit the brief's scope; did it fit the single-
   bounded-session envelope; anything Code would
   change about the brief in retrospect.

Length anticipation: ~300–500 lines. Not a hard line.
Code reasonably over-runs when findings justify it.

The report contains **no recommendations for next
brief drafting** — that's operator-Claude triage
territory. Findings name what was observed; routing
of findings is post-session work.

The report contains **no scope-creep into W12/W13/W15
territory** — those are separate workstreams; W14's
report stays within W14's scope.

---

## §9 — Hard limits (non-negotiable)

### §9.1 — Operating principle

This brief is a contract. Code does what's named in
§§1, 4, 5, 6, 7, 8 and nothing else. Code does not
expand scope, fix adjacent bugs, refactor existing
code, change behaviour outside the named anchors, or
take on findings as in-scope work. Surprises become
findings (§8 item 5), not scope creep.

If the work doesn't fit a single bounded Code session,
Code surfaces that as a finding and ships what it
can coherently complete. Partial-but-coherent beats
complete-but-lost-coherence.

### §9.2 — Behaviour and schema preservation

- **No edits to W11 schema or repository.** `store/
  schema/accounts.py` and `store/repositories/
  accounts.py` are read-only for W14. If a need to
  modify them surfaces, that's a finding.
- **No edits to W10/W4/W6 storage layer.** `store/
  schema/bets.py`, `store/repositories/bets.py`,
  workflows code — all read-only.
- **No edits to clients/, contracts/, ui/, ops/.**
- **Additive-only edit to `store/__init__.py`** —
  add cash_flow imports alongside existing imports.
  Remove nothing. Reorder nothing.

### §9.3 — No adjacent workstreams or findings

- **No W12 work.** Do not implement balance
  derivation, Location 1 / Location 2 formulas, or
  any read-side that combines cash_flow_events with
  bets data. That's W12.
- **No W13 work.** Do not touch `promo_events` or
  create the table. Do not implement cascade events.
  That's W13.
- **No W15 work.** Do not touch `ops_events` or
  create the table. Common event header pattern lives
  in W14 but W15 implements its own table.
- **No day-0 seeding tool.** §1.2 + §1.3 named this
  explicitly; W14 ships the substrate, W16 fires the
  seeding.
- **No reconciliation reports.** Separate sub-stream.
- **No operator UI for entry.** W17+ work.
- **No analytical layer hooks.** P2 work.
- **No findings from the S123 pre-W14 review beyond
  what this brief addresses.** Findings #1–#9 from
  S123 either landed in S124/S125/S126 amendments or
  are parked. Do not revisit them.

### §9.4 — No Alembic, no debt-fixing

- **No Alembic adoption.** Carried per W10/W11
  deferrals (`apply_migrations` pattern continues).
  See `governance.md` "Debt 2 — No migration
  framework" for the return-to-scope trigger; W14
  does not fire it.
- **No test-coverage extension to W10/W11.** "Debt 1
  — No test coverage" applies to the VPS-side
  pipeline (capture.db, scrapers, orchestrator), NOT
  to the v3 storage layer. W14 ships its own tests
  per the W11 precedent. W10/W11 tests are out of
  scope.
- **No monolithic-orchestrator work.** "Debt 3" does
  not touch W14.

### §9.5 — No SQLAlchemy Core migration

DR-031 specifies SQLAlchemy Core for v3 but the
shipped storage layer uses raw `sqlite3` (Finding #6
from S123 review, parked). W14 follows the shipped
pattern, not the spec. The Core migration is a
separate concern out of scope for W14.

### §9.6 — Operational guardrails

- **Read-only on databases except in-memory test
  DBs.** v3's operational store doesn't exist yet
  on disk; the test suite creates and tears down
  in-memory SQLite connections. No production-shape
  DB file is written by W14.
- **No `create_file` tool.** Per
  `standing_instructions.md` Cat 3, banned for
  filesystem work. Use Desktop Commander or
  projects-filesystem MCP.
- **REPL discipline.** Multi-line Python via temp-
  file + `start_process` (e.g.,
  `write_file /tmp/script.py` then
  `start_process python3 /tmp/script.py`). Avoid
  pasting multi-line Python into an interactive REPL
  — line-continuation handling is unreliable.
- **Verify every write.** After each `write_file`
  to a v3 source file, read it back with `read_file`
  or `head`/`tail` to confirm content landed at the
  expected Mac path. Per Cat 3 — `create_file`'s
  silent-fail mode is the failure-mode this verify-
  every-write rule defends against. Surface any
  write that doesn't land cleanly as a finding.
- **Single bounded Code session.** Per §9.1. If
  scope doesn't fit, ship coherent partial and
  surface as a finding.

### §9.7 — Dirty-tree handling (load-bearing this session)

The v3 working tree is dirty at brief lock. `git
status --short` at lock shows uncommitted in-flight
work from W10 / W11 / Betfair pillar across multiple
files. This is the operator's expected state; the
dirty content is real work waiting for an eventual
commit pass.

W14's edit anchors mostly land in **greenfield
files** (the five new source/test files don't exist
yet — no collision). One anchor — `store/__init__.py`
— sits in dirty-tree territory and the discipline
below is non-negotiable.

**Forbidden git operations** for the duration of the
session:

- `git add`
- `git commit`
- `git stash` / `git stash pop`
- `git restore`
- `git checkout` (file-targeted)
- `git reset`
- `git rm`
- Any other operation that modifies the staging
  index or the working tree beyond the named edit
  anchors.

**Required discipline:**

1. **Read working-tree state at session start.** §7.1
   pre-baseline captures this via `git status --short`.
2. **Edit only the named anchors** — the five new
   files (greenfield writes; no collision) plus the
   one additive edit to `store/__init__.py`.
3. **After every edit to `store/__init__.py`**, run
   `git diff store/__init__.py` and confirm only the
   intended addition (the new cash_flow imports)
   appears. Any unexpected diff surfaces as a finding
   and Code halts the edit pass.
4. **For greenfield writes**, no `git diff` check is
   needed (new files appear in `git status` as `??`;
   the writes are visible there). But re-read the
   written file via `read_file` to confirm content
   landed.
5. **At session close**, run `git status --short`
   and confirm: every entry from the §7.1 baseline
   still present in the same status (modified entries
   still `M`, untracked entries still `??`, etc.);
   new entries only for the five W14 files and the
   `store/__init__.py` change. No entries disappear;
   no entries change status unexpectedly.

**If dirty regions intersect W14's edit anchors
beyond `store/__init__.py`** (e.g., Code finds an
existing partial `store/schema/cash_flow.py` from
some prior in-flight work that the operator forgot
about — unlikely, the §7.1 pre-baseline check should
catch this): Code halts, surfaces as a finding,
does not edit. The operator-Claude next session
triages.

**The `store/__init__.py` additive-only rule is the
load-bearing one.** Code's edit adds new import
lines. Existing import lines from W10/W11/etc. must
remain byte-for-byte identical. The `git diff`
post-each-edit check is the verification surface.

Substrate for this discipline: Session 36 (Fix 3 VPS
brief) — first instance of dirty-tree handling rules
in a brief; pattern has held across every brief
since. `standing_instructions.md` Cat 3 catalogues
the rules generally.

---

## §10 — What happens after Code's session

The next operator-Claude session reads
`dr029/w14_cash_flow/w14_cash_flow_report.md` and runs
a triage pass. Expected shape:

1. **Verification check.** Did the work land at the
   expected paths with the expected shape? Did the
   tests pass? Did mypy/ruff pass? Is the dirty-tree
   adherence statement clean (pre/post `git status`
   diffs as expected)?
2. **Findings triage.** For each finding in §8 item 5:
   - Spec ambiguity → routes to architecture/decisions
     amendment or a clarifying brief addendum.
   - Deferred concern → routes to a W14.1 follow-up
     brief if material, or to the parking lot if
     minor.
   - Integration surprise → routes to either a W11
     amendment (if the surprise reveals a W11 gap) or
     a W14.1 fix (if W14 needs to defend against it).
   - Weak test → routes to a test-tightening pass in
     W14.1 or as a follow-up in W13's brief.
   - Other → routed case-by-case.
3. **Forward routing.** Confirm W13 is the next
   active workstream (per the build picture). W13
   builds against the common event header pattern
   W14 established — W13's brief drafting reads
   W14's shipped code as substrate. If W14 needed a
   W14.1 follow-up, W14.1 runs before W13 brief
   drafting starts.
4. **Build-picture update.** W14 transitions from
   `in flight` to `done` (one-session carry); W13
   transitions from `blocked-on-W14` to `in flight`
   if no W14.1 needed; W15 stays `blocked-on-W14` if
   W13 sequencing puts it later, or moves to a
   different block label if sequencing shifts.

Code does **not** produce the next brief. Code
produces the report; the next operator-Claude session
produces W13's brief (or W14.1's brief if needed).

---

## §11 — Cross-references

### §11.1 — Architecture and decisions

- `architecture.md` §A.2 — per-domain event log
  spine, common event header, eight cash_flow_events
  types specified, supersession semantics. Line 99
  explicitly names "**W14 ships this table**".
- `architecture.md` §A.5 — cash flow model with two
  balance locations, bank-touching vs internal
  categorisation, day-0 opening mechanics, profit-
  share semantics, cash-age FIFO, external payment
  scope.
- `architecture.md` §A.6 — settlement state on bets
  row (referenced for `cash_returned` derivation
  that W12 joins to cash flow events).
- `architecture.md` §A.9 — derivation rules (what's
  stored vs computed).
- `architecture.md` §A.10 — canonical-reference-layer
  principle (Betfair as canonical source).
- `decisions.md` DR-027 + Session 124 amendment —
  two-database architecture + per-domain event-table
  internal shape.
- `decisions.md` DR-019 + Session 124 amendment —
  derived state on read; applies to bet records but
  NOT cash flow events (the asymmetry §1.1 and
  §5.1.1 call out).
- `decisions.md` DR-030 + Session 124 amendment —
  v3 repo layout.
- `decisions.md` DR-032 — canonical-reference-layer
  schema (referenced where cash flow events join to
  bet records via correlation_id and per-bet
  derivations).
- `decisions.md` DR-022 — account / book / account-
  at-book vocabulary.
- `decisions.md` DR-021 — Adelaide local timestamp
  anchoring.

### §11.2 — Prior briefs and reports (precedent)

- `dr029/w11_accounts/w11_accounts_brief.md` —
  primary precedent. File layout, schema migration
  pattern, repository pattern, test pattern, hard-
  limits structure.
- `dr029/w11_accounts/w11_accounts_report.md` —
  W11 Code report. Pattern for what W14's report
  looks like.
- `dr029/2_1_race_data/fix_3_brief.md` (Session 36)
  — original dirty-tree handling pattern. Substrate
  for §9.7.
- `sessions/SESSION_122.md` — W11 close session
  record. Operational context for what shipped in
  W11.
- `sessions/SESSION_124.md`, `SESSION_125.md`,
  `SESSION_126.md` — pre-W14 governance update arc
  records. Substrate for the locked spec state W14
  builds against.

### §11.3 — Standing instructions and governance

- `standing_instructions.md` Cat 1 — communication
  register (plain-language, decision-fronted).
- `standing_instructions.md` Cat 3 — filesystem and
  tooling discipline (`create_file` ban, verify-
  every-write, REPL discipline, dirty-tree handling
  generally, pre-execution risk advisory).
- `standing_instructions.md` Cat 5 — operator/Claude
  division of labour (software calls are Claude's).
- `governance.md` "Final data-layer lock review
  (DR-029 close-out)" — three pieces of named debt
  inherited; W14 carries them per §9.4.
- `vision.md` — non-negotiables (trust-without-
  manual-reconciliation, cycle-visibility, Adelaide
  local time, operator-tax-near-zero). W14's
  substrate directly serves these; alignment check
  ran in Session 127 brief-drafting pass.

### §11.4 — Parking-lot items the brief excludes

- DR-025 hedge classification (revisit-before-W15
  flag). Not relevant to W14.
- §2.4 Fix 4 cadence design (Finding #3 dependency
  for §2.10 P1). Not relevant to W14.
- Fix 5 venue harmonisation. Not relevant to W14.
- Operational soft-book layer (§2.5 deferred per
  Session 69). Not relevant to W14.
- §2.10 bucket-1 / bucket-2 (P1 / P2 — post-cutover
  + analytical layer). Not relevant to W14.
- Audit-trail surface for settlement transitions
  (Deferred capability 7 per `governance.md`). Not
  relevant to W14 — separate from the supersession
  pattern this table uses, which IS audit-shaped by
  design (immutable events, supersession chain
  walkable on read).

### §11.5 — Build-picture context

- `v3_build_picture.md` (Session 126 update) — W14
  is `in flight` post-S127 open; pre-W14 governance
  update sits one-session-carry `done` and drops at
  S127 close. W13 / W15 are `blocked-on-W14`. W12
  is `blocked-on-W13-and-W14`.

---

**Brief lock complete.** W14 is the contract; Code
executes against it in a single bounded session,
produces the report named in §8, and the operator-
Claude next session triages per §10.
