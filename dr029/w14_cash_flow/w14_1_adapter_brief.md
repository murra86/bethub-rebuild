# W14.1 brief — Cash flow store adapter (move domain translation out of store/)

**Status:** locked Session 128.
**Lock anchor:** 2026-05-12 ACST (Adelaide local per DR-021;
exact lock timestamp captured in `sessions/SESSION_128.md`
at close).
**Workstream:** W14.1 (surgical fix against W14's
`lint-imports` break — moves domain ↔ row translation from
`store/repositories/cash_flow.py` to a new
`workflows/cash_flow/v1/cash_flow_store_adapter.py`,
restoring DR-030's module-boundary discipline).
**Recipient:** Claude Code, single bounded session.
**Brief location:**
`dr029/w14_cash_flow/w14_1_adapter_brief.md`.
**Triages:** W14 report §5.1 (the load-bearing
DR-030 alignment finding) plus W14 report §5.4 (test
layout asymmetry — folded in because the move is
cheap and the W11 layout is the locked convention).

---

## §1 — What this brief is and is not

### §1.1 — What this brief is

This brief commissions Code to **refactor W14's cash flow
store layer into the W11 row-only pattern** by adding a
workflow-side adapter that owns all Pydantic ↔ row
translation. The work restores DR-030's locked
module-boundary discipline (`store/` imports nothing else
in the project) while keeping every behaviour W14 shipped
intact.

The fix has four anchors:

- **New file:** `workflows/cash_flow/v1/cash_flow_store_adapter.py`
  — owns the discriminated-union dispatch (using
  `PAYLOAD_BY_EVENT_TYPE` imported from
  `domain/cash_flow`), the JSON serialisation / parsing,
  the row ↔ Pydantic translation for both event and payee
  surfaces, and the public surface that workflow callers
  use. This is where W14's eight read methods, two
  supersession-aware reads, and payee CRUD now live at
  Pydantic level. The adapter takes a `sqlite3.Connection`
  on construction (W14 repository pattern) and instantiates
  both `CashFlowEventRepository` and `PayeeRepository`
  internally; delegates row-level operations to them and
  translates at the boundary.
- **Edited file:** `store/repositories/cash_flow.py` —
  trimmed back to row-only. Methods accept `CashFlowEventRow`
  / `PayeeRow` (not Pydantic models), return rows (not
  Pydantic models). All `domain.cash_flow` imports removed.
  Repository errors stay at the repository (the adapter
  re-raises). All scope-filter logic, ordering,
  pagination, and the supersession LEFT JOIN stay at the
  repository — these are SQL-shape concerns, not domain
  concerns.
- **Moved files:** `tests/store/test_cash_flow_schema.py`
  → `tests/store/repositories/test_cash_flow_schema.py`,
  and `tests/store/test_cash_flow_repository.py` →
  `tests/store/repositories/test_cash_flow_repository.py`.
  Matches the W11 / bets-tests layout that the
  post-W11 operator-Claude session locked. Schema tests
  carry over unchanged. Repository tests reshape to
  row-level (no Pydantic, just rows + scope filters +
  SQL-shape invariants).
- **New file:** `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`
  — adapter-level tests covering the Pydantic-side
  behaviour: discriminated-union round-trip per event
  type, per-event-type FK rules raise `ValidationError`,
  Adelaide tz validation, supersession-aware reads
  returning correct Pydantic types, payee CRUD round-trip.

Plus two new package marker files
(`workflows/cash_flow/__init__.py`,
`workflows/cash_flow/v1/__init__.py`) and two test
package markers
(`tests/workflows/cash_flow/__init__.py`,
`tests/workflows/cash_flow/v1/__init__.py`). All empty
or one-line per existing v3 convention.

The work ships as **four new files** (the adapter, the
adapter test file, and four package markers — counted as
one logical block of empty `__init__.py` files) plus
**one edited file** (`store/repositories/cash_flow.py`)
plus **two moved files** (the two W14 test files).

### §1.2 — What this brief is not

W14.1 explicitly does **not**:

- **Touch `domain/cash_flow/__init__.py`.** W14's domain
  layer is correct as shipped — closed enums, eight
  payload subclasses with `event_type_payload`
  discriminator, `CashFlowEventBase` with FK-nullability-
  per-event-type model validator, Adelaide tz validators,
  `PAYLOAD_BY_EVENT_TYPE` dispatch table, `Payee` model.
  Read-only file for W14.1.
- **Touch `store/schema/cash_flow.py`.** Schema is
  correct as shipped — eight CHECK-constrained event
  types, seven indexes, FK constraints to W11 tables,
  self-referential FKs on `parent_event_id` /
  `supersedes_event_id`, idempotent migration. Read-only.
- **Touch `store/__init__.py`.** W14's additive edit
  landed correctly (cash_flow repository imports added at
  alphabetical positions; existing entries preserved).
  The adapter is consumed from `workflows.cash_flow.v1`,
  not re-exported through `store/`. Read-only for W14.1.
- **Amend DR-030.** The route considered in the W14
  report §5.1 was "amend DR-030 to carve out per-domain
  event repositories." Rejected at S128 triage — the
  cleaner route is fixing W14 to obey the rule rather
  than bending the rule for W14. No `decisions.md` edit
  this brief.
- **Build W11 / W4 / W6 adapters.** Whether the W11
  accounts repository or the bets repositories ship with
  workflow-side adapters is W11 / W4 / W6 territory.
  W14.1 establishes the cash_flow adapter pattern; other
  domains follow their own briefs if and when they need
  adapters. The brief's hard limits exclude touching W11 /
  W4 / W6 anchors.
- **Re-export accounts from `store/__init__.py`.** The
  W14 report §5.2 surfaced that `store/__init__.py`
  exports the bets surface but not accounts. Separate
  concern; not W14.1.
- **Touch any other v3 module.** No `clients/`, no
  `contracts/`, no `ui/`, no `ops/`, no other workflows
  / their tests, no scripts / build config / pyproject.
- **Address minor W14 findings beyond §5.4.** W14 report
  §5.2 (accounts re-export), §5.3 (W11-migrations-needed-
  for-CHECK-tests — informational precedent for W13 /
  W15 briefs, not a fix), §5.5 (empty
  `tests/conftest.py` — brief inaccuracy, not a fix),
  §5.6 (`git diff` against empty index — ergonomic note),
  §5.7 (tooling-alternative clause — standing-instruction
  sweep candidate, not a fix), §5.8 (file-size overrun
  within §7.3 rough-guides framing — not a fix), §5.10
  (pytest collection ordering — cosmetic): all out of
  scope.
- **Add or change tests beyond the named reshape /
  relocation / new adapter file.** The same 47 W14 tests
  exist at the end of W14.1 — some at the row level
  (under `tests/store/repositories/`), some at the
  adapter level (under `tests/workflows/cash_flow/v1/`).
  Net new tests are only what the reshape requires
  (adapter coverage of behaviours that were repository-
  level in W14 and are adapter-level after W14.1).
- **Change behaviour, contract, or semantics.** Every
  W14 read pattern returns the same data shape from the
  adapter that the W14 repository returned. Every W14
  write pattern accepts the same Pydantic input at the
  adapter that the W14 repository accepted. Errors and
  edge cases preserved one-for-one.

### §1.3 — Why W14.1 has the scope it does

Three software calls were made during brief drafting
(Session 128); naming them for visibility per
`standing_instructions.md` Cat 5:

- **Adapter takes a connection, constructs repositories
  internally.** Alternative considered: constructor
  injection of pre-built `CashFlowEventRepository` and
  `PayeeRepository` instances. Rejected — would force
  every caller to construct three objects instead of one
  and offers no testability benefit at this scale (the
  adapter's own tests can pass an in-memory connection
  exactly the same way W14's repository tests did).
  Matches the W14 repository constructor pattern.
- **`PAYLOAD_BY_EVENT_TYPE` dispatch table stays at
  `domain/cash_flow`.** It is a pure data structure
  mapping enum → class; nothing about it is store-side
  or workflow-side. The adapter imports it as a domain
  artefact, the same way it imports the model classes.
  No move required.
- **Row-level pagination, ordering, and the supersession
  LEFT JOIN stay at the repository.** These are SQL-shape
  concerns. The adapter passes through `limit` / `offset`
  / scope arguments to the repository and translates the
  resulting rows. The W14 brief locked the SQL surface
  shape; W14.1 keeps it.

These are Cat 5 software/scope calls. Operator can
override at any time before Code lock.

---
## §2 — Why this work exists

W14 shipped per its brief specification at Session 127.
Code's W14 report §5.1 flagged that brief §5.3 (Pydantic
domain models at the repository surface) directly
conflicts with DR-030 (the v3 module-boundary discipline,
the "store/ imports nothing in the project" contract).
Code shipped to brief spec and surfaced the conflict as
the load-bearing finding. The `lint-imports` gate shows
two broken contracts post-W14, both from the same import
line in `store/repositories/cash_flow.py`:

```
DR-030 layered architecture
  store is not allowed to import domain:
  - store.repositories.cash_flow -> domain.cash_flow (l.54)

store imports nothing in the project
  store is not allowed to import domain:
  - store.repositories.cash_flow -> domain.cash_flow (l.54)
```

S128 triage routed this between two options:

- **(i)** Amend DR-030 — carve out per-domain event
  repositories, W14 ships as-is, W13 / W15 inherit the
  same Pydantic-at-repository pattern.
- **(ii)** W14.1 surgical fix — move Pydantic handling to
  a workflow-side adapter, repository trims to row-only,
  DR-030 holds.

(ii) locked at S128 triage. Rationale: the W4 / W6 bet
records and the W11 accounts repository ship row-only at
the storage layer per the established v3 convention.
Carving out DR-030 on the first per-domain event log
workstream would signal that module-boundary discipline
bends easily, and the next two event log tables (W13
promos, W15 ops log) would inherit the bent version.
W14.1 fixes W14 to the established convention before
W13 / W15 reuse the pattern.

The W14 brief also surfaced a second finding folded in
here for cost reasons: W14 tests landed at
`tests/store/test_cash_flow_*.py` per brief §5.5, but
the shipped W11 layout sits at
`tests/store/repositories/test_accounts_*.py` (the
post-W11 operator-Claude session moved W11 tests to that
location to match the bets-tests precedent). W14.1
already touches the test suite to reshape repository
tests vs adapter tests; the relocation lands in the same
pass at near-zero marginal cost.

Two governance anchors W14.1 honours:

- **DR-030** (the v3 module-boundary discipline, with
  Session 124 amendment) is the load-bearing reason this
  brief exists. After W14.1, `lint-imports` passes on all
  five contracts.
- **DR-027** (the two-database architecture decision, with
  Session 124 amendment locking per-domain event-table
  internal shape) — unchanged by W14.1. The per-domain
  event log shape stays correct; only the layer that owns
  Pydantic translation moves.

The pattern W14.1 establishes — repository owns rows /
SQL; adapter owns Pydantic / domain translation — is the
template W13 (`promo_events`) and W15 (`ops_events`)
reuse when their per-domain event log workstreams land.

---

## §3 — Pre-reads

### §3.1 — Required reads (read before starting)

Read in order. These define what Code is implementing
and what it must not break.

1. **W14 brief at
   `dr029/w14_cash_flow/w14_cash_flow_brief.md`** —
   read end-to-end. The brief locks the substrate W14.1
   refactors. Particularly load-bearing for W14.1:
   §5.1 (domain models — unchanged by W14.1),
   §5.2 (schema DDL — unchanged), §5.3 (current
   repository surface — the thing W14.1 trims), §5.4
   (the `store/__init__.py` additive edit — already
   landed, unchanged), §5.5 (the test surface — reshaped
   and relocated), §6.2 (build order — W14.1 follows a
   similar order applied to the refactor: adapter and
   repository changes, then test reshape, then test
   relocation), §9.7 (dirty-tree handling — carries
   forward verbatim).

2. **W14 report at
   `dr029/w14_cash_flow/w14_cash_flow_report.md`** —
   read end-to-end. Particularly load-bearing:
   §3 (what was built — names every method, helper, and
   dispatch table that needs to move or stay), §4.1
   (the `lint-imports` failure surface — confirms which
   contract breaks need to clear after W14.1), §5.1
   (the load-bearing finding and the two options),
   §5.4 (the test layout asymmetry being folded in),
   §6 (the dirty-tree adherence statement — confirms
   the working-tree state W14.1 builds against).

3. **`decisions.md` DR-030** (the v3 module-boundary
   discipline + Session 124 amendment) — read body +
   amendment. The contract W14.1 restores.
   **`decisions.md` DR-027** (Session 124 amendment) —
   read body + amendment. Confirms the per-domain
   event-table internal shape is unchanged by W14.1.

4. **`dr029/w11_accounts/w11_accounts_brief.md`** —
   precedent for the row-only repository pattern.
   Particularly §5.3 ("No domain imports —
   `store/` imports nothing in the project beyond
   `store.schema.*` per DR-030"). Skim end-to-end if not
   already in working memory.

5. **`bethub-v3/store/repositories/accounts.py`** —
   the row-only repository in the wild. W14.1's trimmed
   `store/repositories/cash_flow.py` mirrors this shape:
   row dataclasses, repository class accepting and
   returning rows, errors in-module, no domain imports.

6. **`bethub-v3/workflows/bet_entry/v1/`** — the
   workflow-side pattern in the wild. The directory's
   in-flight state confirms the
   `workflows/<domain>/v1/<role>_<artefact>.py` naming
   convention W14.1 follows for the adapter file. Read
   the v1 directory listing plus any one shipped file
   inside it to confirm the package-marker pattern
   (`__init__.py` empty or one-line) and module-level
   docstring convention.

### §3.2 — Reference-only (read on demand)

- **`standing_instructions.md`** Cat 3 (filesystem and
  tooling discipline — `create_file` ban, verify-every-
  write, REPL discipline, pre-execution risk advisory,
  dirty-tree handling generally) and Cat 5 (operator /
  Claude division of labour).
- **`vision.md`** — non-negotiables. W14.1's substrate
  doesn't change the operational picture; the Pydantic
  surface the adapter exposes is identical to what W14's
  repository exposed.
- **`governance.md`** — DR-029 close-out named debt and
  deferred capabilities. W14.1 inherits the three pieces
  of named debt cleanly (W14.1 ships its own adapter
  tests, uses the existing pre-Alembic schema as-is,
  doesn't touch VPS orchestrator).
- **`v3_build_picture.md`** — current stream state and
  next-milestone labels.
- **`dr029/w14_cash_flow/w14_cash_flow_brief.md`** §9.7
  — dirty-tree handling. Same discipline applies to
  W14.1.

Existing v3 codebase files (read-only browse for pattern
confirmation):

- `bethub-v3/store/repositories/cash_flow.py` (W14
  shipped) — the file W14.1 trims.
- `bethub-v3/store/repositories/accounts.py` (W11
  shipped) — the row-only template W14.1's trimmed
  cash_flow repository mirrors.
- `bethub-v3/domain/cash_flow/__init__.py` (W14
  shipped) — read-only for W14.1; informs adapter
  imports.
- `bethub-v3/store/schema/cash_flow.py` (W14 shipped) —
  read-only.
- `bethub-v3/tests/store/test_cash_flow_schema.py`,
  `tests/store/test_cash_flow_repository.py` (W14
  shipped) — the files being moved and (for the
  repository tests) reshaped.
- `bethub-v3/tests/store/repositories/test_accounts_repository.py`,
  `test_bets.py` — layout precedent for the relocated
  W14 tests.
- `bethub-v3/tests/workflows/bet_entry/v1/` (whatever
  test files exist) — layout precedent for the new
  adapter test file.

---
## §4 — System access

- **Read-write** on the v3 codebase at
  `/Users/tim/Desktop/Projects/bethub-v3/` — limited to
  the named anchors:
  - **New files (greenfield writes):**
    - `workflows/cash_flow/__init__.py`
    - `workflows/cash_flow/v1/__init__.py`
    - `workflows/cash_flow/v1/cash_flow_store_adapter.py`
    - `tests/workflows/cash_flow/__init__.py`
    - `tests/workflows/cash_flow/v1/__init__.py`
    - `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`
  - **Edit (W14 file, trimmed to row-only):**
    - `store/repositories/cash_flow.py`
  - **Moves (W14 test files relocated; if Code's
    `Move` / `mv` is awkward, equivalent is
    `write_file new-path` + verify + delete original
    via `start_process rm <old-path>`):**
    - `tests/store/test_cash_flow_schema.py`
      → `tests/store/repositories/test_cash_flow_schema.py`
      (with light reshape per §5.3)
    - `tests/store/test_cash_flow_repository.py`
      → `tests/store/repositories/test_cash_flow_repository.py`
      (with reshape per §5.3 — repository tests
      become row-level; Pydantic-side tests relocate
      to the new adapter test file)

  No other paths under `bethub-v3/` are touched.

- **Read-only** on the rebuild folder at
  `/Users/tim/Desktop/Projects/bethub-rebuild/` for all
  reference reads named in §3.

- **No VPS access.** W14.1 is operational-store refactor
  work; no `capture.db` interaction.

- **No Betfair API access.** W14.1 is internal
  application code; no external API calls.

- **No live database access** beyond the in-memory /
  `tmp_path`-backed SQLite databases the test suite
  creates and tears down. The W14 schema is unchanged;
  no migration writes against any on-disk DB.

- **Filesystem tool:** Desktop Commander (`write_file`,
  `read_file`, `edit_block`, `list_directory`,
  `start_process`) or `projects-filesystem` MCP server
  (`write_file`, `edit_file`). `create_file` is banned
  per `standing_instructions.md` Cat 3 — writes to a
  Claude-container sandbox path that mimics the Mac
  path shape but does not reach the Mac filesystem. If
  Code is operating in a Claude Code CLI environment
  where the named Desktop Commander tools are not
  loaded (per W14 report §5.7), the CLI's native
  `Write` / `Edit` tools are acceptable substitutes
  **provided the Cat 3 spirit holds**: every write
  followed by a read-back or test-exercise that
  confirms the file landed at the real Mac path.

- **Adelaide local timestamps per DR-021** for every
  time-of-day reference in the report and any timestamp
  literals in test fixtures. ISO 8601 with timezone
  offset (`+09:30` ACST). Use
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  via `start_process` for session-start and session-
  close anchors.

- **Single bounded Code session.** If the work doesn't
  fit, that's a finding, not a continuation. Partial-
  but-coherent ship beats complete-but-lost-coherence.

---

## §5 — Substantive scope

### §5.1 — Adapter (`workflows/cash_flow/v1/cash_flow_store_adapter.py`)

The new adapter owns every Pydantic ↔ row translation
the W14 repository was doing. Top-level shape:

**Imports the adapter needs:**

- `from domain.cash_flow import (CashFlowEventBase,
  CashFlowEventType, PAYLOAD_BY_EVENT_TYPE, Payee, ...)`
  — every domain artefact the W14 repository was
  importing.
- `from store.repositories.cash_flow import
  (CashFlowEventRepository, PayeeRepository,
  CashFlowEventRow, PayeeRow, DuplicateEventError,
  EventNotFoundError, SupersessionCycleError,
  InvalidScopeError, DuplicateEntityError,
  EntityNotFoundError, ...)` — row dataclasses,
  repository classes, error types.
- Standard library: `sqlite3`, `uuid.UUID`,
  `datetime.datetime`, `typing.cast`.

**Adapter class:**

```python
class CashFlowStoreAdapter:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._events = CashFlowEventRepository(conn)
        self._payees = PayeeRepository(conn)
```

Construction takes a connection and instantiates both
underlying repositories. The W14 repository pattern (one
connection, `PRAGMA foreign_keys = ON`,
`apply_migrations` invoked on init) is preserved — both
repositories share the same connection and the migration
runs once at first construction.

**Public write surface (events):**

- `append_event(event: CashFlowEventBase) -> UUID` —
  takes a Pydantic event, serialises the payload via
  `event.payload.model_dump_json()`, converts the
  event's typed fields to row primitives (UUID → str,
  datetime → ISO string, etc.), builds a
  `CashFlowEventRow`, calls `self._events.append_row(row)`,
  returns the event_id. Errors from the repository
  (`DuplicateEventError`, FK / CHECK / self-FK
  `IntegrityError` wrapped to `CashFlowEventError`)
  propagate unchanged.

**Public read surface (events — returns Pydantic models):**

- `get_event(event_id: UUID) -> CashFlowEventBase` —
  calls `self._events.get_row(event_id)`, translates row
  via `_row_to_event` (see helpers), returns the
  Pydantic model. Raises `EventNotFoundError`.
- `list_by_account_at_book(account_at_book_id: UUID,
  event_type: CashFlowEventType | None = None,
  limit: int = 1000, offset: int = 0)
  -> list[CashFlowEventBase]` — passes scope args
  through to `self._events.list_rows_by_account_at_book(...)`,
  translates row list via `_row_to_event`, returns
  Pydantic list.
- `list_by_account(...)`, `list_by_book(...)`,
  `list_by_event_type(...)`, `list_by_correlation_id(...)`
  — same shape, each delegates to its repository
  counterpart and translates rows to models.
- `latest_non_superseded_by_scope(account_at_book_id=None,
  account_id=None, book_id=None, event_type=None)
  -> list[CashFlowEventBase]` — delegates to
  `self._events.latest_non_superseded_rows_by_scope(...)`,
  translates, returns. The `InvalidScopeError`
  (all-None scope) propagates from the repository.
- `walk_supersession_chain(event_id: UUID)
  -> list[CashFlowEventBase]` — delegates to
  `self._events.walk_supersession_chain_rows(event_id)`,
  translates, returns. `SupersessionCycleError`
  propagates.

**Public write surface (payees):**

- `create_payee(payee: Payee) -> UUID` — Pydantic in,
  translates to `PayeeRow`, delegates to
  `self._payees.create_row(row)`, returns
  `payee_id`. `DuplicateEntityError` propagates.

**Public read surface (payees — returns Pydantic models):**

- `get_payee(payee_id: UUID) -> Payee` — delegates,
  translates row → Pydantic, returns. Raises
  `EntityNotFoundError`.
- `update_payee(payee_id: UUID, name: str | None = None,
  category: ExternalPaymentCategory | None = None,
  notes: str | None = None,
  updated_at: datetime | None = None) -> Payee` — the
  adapter computes the `updated_at` value if not
  supplied (Adelaide-local now), delegates to
  `self._payees.update_row(...)`, translates row →
  Pydantic, returns the updated record.
- `list_payees(category: ExternalPaymentCategory | None
  = None) -> list[Payee]` — delegates, translates,
  returns.

**Module-level helper functions:**

- `_row_to_event(row: CashFlowEventRow)
  -> CashFlowEventBase` — uses
  `PAYLOAD_BY_EVENT_TYPE[CashFlowEventType(row.event_type)]`
  to find the payload class, calls
  `payload_cls.model_validate_json(row.payload)` to
  parse, constructs the `CashFlowEventBase` with the
  typed fields (UUIDs via `UUID(...)`, datetimes via
  `datetime.fromisoformat(...)`, etc.) and the parsed
  payload, returns it. This is the function that owned
  the `typing.cast` workaround in W14 (per W14 report
  §4.1); same cast applies here.
- `_event_to_row(event: CashFlowEventBase)
  -> CashFlowEventRow` — inverse direction. Serialises
  payload via `event.payload.model_dump_json()`, formats
  UUIDs and datetimes to strings, builds the row.
- `_row_to_payee(row: PayeeRow) -> Payee` — straight
  field translation.
- `_payee_to_row(payee: Payee) -> PayeeRow` — inverse.

**No errors defined at the adapter layer.** Repository
errors are the canonical errors; the adapter is a thin
translation surface. Pydantic `ValidationError` raises
naturally on bad input (e.g. constructing a
`CashFlowEventBase` with a naive datetime).

**Module docstring** at top names the W14 → W14.1
relocation explicitly (one paragraph), names DR-030
as the load-bearing reason, and points at the W14
brief / W14 report for substrate context.

### §5.2 — Repository trim (`store/repositories/cash_flow.py`)

The W14 repository becomes row-only. Every change is
mechanical:

**Removed imports:**

- Every `from domain.cash_flow import ...` line.
- Pydantic-related imports
  (`from pydantic import ...`) — keep only what raw
  dataclass / sqlite3 work needs.
- `typing.cast` is no longer needed for the dispatch-
  table return type (the dispatch table moves to the
  adapter).

**Removed module-level state:**

- The `PAYLOAD_BY_EVENT_TYPE` reference (still imported
  from domain, but the repository module no longer
  needs it).
- The `_row_to_event` / `_row_to_payee` Pydantic
  conversion helpers move to the adapter.

**Kept module-level state:**

- `CashFlowEventRow` and `PayeeRow` dataclasses
  (unchanged).
- All error classes
  (`CashFlowEventError`, `DuplicateEventError`,
  `EventNotFoundError`, `SupersessionCycleError`,
  `InvalidScopeError`, `PayeeError`,
  `DuplicateEntityError`, `EntityNotFoundError`).

**Method-by-method changes to `CashFlowEventRepository`:**

- `append_event(event: CashFlowEventBase) -> UUID` is
  **removed**. Replaced by:
  `append_row(row: CashFlowEventRow) -> UUID` —
  raw INSERT against the row's fields, returns
  `UUID(row.event_id)`. `DuplicateEventError` on PK
  collision; other `sqlite3.IntegrityError` wrapped to
  `CashFlowEventError`.
- `get_event(event_id: UUID) -> CashFlowEventBase`
  becomes `get_row(event_id: UUID) -> CashFlowEventRow`
  — returns the row, raises `EventNotFoundError` on
  absence.
- Every list method (`list_by_account_at_book`,
  `list_by_account`, `list_by_book`,
  `list_by_event_type`, `list_by_correlation_id`)
  becomes `list_rows_by_<scope>(...)`, returning
  `list[CashFlowEventRow]`. Scope filters, ordering by
  `(recorded_at ASC, event_id ASC)`, pagination via
  `limit` / `offset` — all unchanged from W14.
- `latest_non_superseded_by_scope(...)` becomes
  `latest_non_superseded_rows_by_scope(...)` returning
  `list[CashFlowEventRow]`. The LEFT JOIN SQL is
  unchanged; the `InvalidScopeError` on all-None
  scope is unchanged.
- `walk_supersession_chain(event_id: UUID)` becomes
  `walk_supersession_chain_rows(event_id: UUID)`
  returning `list[CashFlowEventRow]`. Iteration logic
  and `SupersessionCycleError` raising unchanged.

**Method-by-method changes to `PayeeRepository`:**

- `create_payee(payee: Payee) -> UUID` →
  `create_row(row: PayeeRow) -> UUID`.
- `get_payee(payee_id: UUID) -> Payee` →
  `get_row(payee_id: UUID) -> PayeeRow`.
- `update_payee(payee_id, name=None, category=None,
  notes=None)` → `update_row(payee_id, name=None,
  category=None, notes=None, updated_at: str)` —
  the adapter computes the timestamp (Adelaide-local
  now) and passes the ISO string; repository writes
  it verbatim.
- `list_payees(category=None)` → `list_rows(category=None)`
  returning `list[PayeeRow]`.

**No method signatures, ordering, scope filter SQL,
pagination, or error semantics change in net behaviour.**
The only thing that changes is the type at the
boundary: rows in, rows out.

**Module docstring** at top notes the W14.1 trim
(one paragraph) — domain ↔ row translation moved to
`workflows/cash_flow/v1/cash_flow_store_adapter.py`
per DR-030.

---
### §5.3 — Test reshape

W14 shipped 47 tests across two files. W14.1 distributes
them across three files post-refactor:

**Repository tests (row-level) at
`tests/store/repositories/test_cash_flow_repository.py`:**

These are the W14 tests that exercise SQL shape — scope
filtering, ordering, pagination, supersession LEFT JOIN
SQL, raw row round-trip. They move to the relocated test
file and reshape to use rows instead of Pydantic models.
Estimated 18–22 tests:

- `test_append_row_returns_event_id` — append a
  `CashFlowEventRow`, assert event_id round-trips.
- `test_append_duplicate_event_id_raises` — raises
  `DuplicateEventError`.
- `test_append_each_event_type_row_round_trips`
  (parametrised, eight cases) — constructs a row with a
  representative payload JSON string for each event
  type, appends, fetches the row back, asserts row
  equality (including `payload` string round-trip).
  This replaces W14's parametrised
  `test_append_each_event_type_round_trips` —
  the eight-event-type coverage stays at repository
  level; per-event-type Pydantic round-trip moves to
  the adapter test file.
- `test_get_row_not_found_raises` —
  `EventNotFoundError`.
- `test_list_rows_by_account_at_book_paginates`,
  `test_list_rows_by_account_at_book_filters_by_event_type`,
  `test_list_rows_by_correlation_id_returns_full_cycle`,
  `test_list_rows_by_event_type_scans_table`,
  `test_list_rows_by_book` — the W14 list tests, but
  operating on rows rather than Pydantic models.
- `test_latest_non_superseded_rows_excludes_superseded`,
  `test_walk_supersession_chain_rows`,
  `test_supersession_cycle_detected_at_row_level`,
  `test_latest_non_superseded_requires_scope`
  (`InvalidScopeError`).
- `test_fk_violation_against_w11_tables_raises` — keep
  the FK enforcement test (insert a row with a ghost
  `account_id`; expect `CashFlowEventError` wrapping
  the `IntegrityError`).
- Payee row-level CRUD: `test_create_row_get_row_round_trip`,
  `test_create_duplicate_row_raises_duplicate_entity_error`,
  `test_update_row_partial_fields`,
  `test_list_rows_by_category`.

**Tests dropped at this layer (moving to adapter
tests):** the per-event-type FK rule tests
(`test_fk_rules_account_holder_funding`,
`test_fk_rules_account_at_book_deposit`, etc. — these
are Pydantic validation tests, not SQL tests), the
Adelaide tz validation tests, the
`test_append_each_event_type_round_trips` Pydantic-
identity assertions.

**Adapter tests (Pydantic-level) at
`tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`:**

These are the W14 tests that exercise Pydantic
construction, FK-nullability-per-event-type validation,
Adelaide tz validation, and the discriminated-union
round-trip with type identity. Estimated 25–30 tests:

- `test_append_event_via_adapter_round_trips`
  (parametrised, eight cases) — for each event type,
  construct a valid `CashFlowEventBase` with the
  appropriate payload subclass, call
  `adapter.append_event(event)`, call
  `adapter.get_event(event_id)`, assert
  `type(fetched.payload) is type(event.payload)` and
  `fetched.payload == event.payload`. The W14
  discriminated-union round-trip moves here.
- FK rules per event type (eight tests, one per type)
  — each constructs an event with the wrong combination
  of FK fields, asserts `ValidationError` on the
  Pydantic construction. The valid-case half also fires
  via `test_append_event_via_adapter_round_trips`.
- `test_naive_datetime_rejected`,
  `test_non_adelaide_tz_rejected`,
  `test_acdt_daylight_saving_accepted` — Adelaide tz
  validation per W14 §5.1.1.
- Read paths returning Pydantic types:
  `test_get_event_returns_pydantic_model`,
  `test_list_by_account_at_book_returns_pydantic_models`,
  `test_list_by_account`, `test_list_by_book`,
  `test_list_by_event_type`,
  `test_list_by_correlation_id_returns_full_cycle_in_pydantic`.
- Supersession-aware at Pydantic level:
  `test_latest_non_superseded_via_adapter_excludes_superseded`,
  `test_walk_supersession_chain_returns_pydantic_models`,
  `test_invalid_scope_raises_via_adapter`.
- Payees at Pydantic level: `test_create_payee_via_adapter_round_trips`,
  `test_get_payee_returns_pydantic`,
  `test_update_payee_advances_updated_at`,
  `test_update_payee_partial_field_semantics`,
  `test_list_payees_filters_by_category`.

**Schema tests at
`tests/store/repositories/test_cash_flow_schema.py`:**

The W14 schema tests carry over unchanged. Ten tests:
`test_apply_migrations_creates_tables`,
`test_apply_migrations_creates_indexes`,
`test_apply_migrations_idempotent`,
`test_event_type_check_constraint`,
`test_source_check_constraint`,
`test_payee_category_check_constraint`,
`test_fk_constraints_to_accounts_w11_tables`,
`test_self_referential_fk_parent_event`,
`test_self_referential_fk_supersedes_event`. These tests
exercise DDL / SQL — they don't care whether the layer
above is row-only or Pydantic. Relocation only, no
reshape.

**Net test count target:** W14 shipped 47 tests; W14.1
ships ~53–62 (each per-event-type FK rule test now has
two assertions splitting into one repository-level row
test + one adapter-level Pydantic test; some W14 tests
collapse into parametrised cases). Approximate is fine —
Code adds or drops where the surface warrants and
surfaces the count in the report.

**Shared test fixtures:**

- Repository tests use `tmp_path`-backed SQLite via
  fixtures equivalent to W14's repository test setup.
  No `tests/conftest.py` changes (it stays empty per
  W14 report §5.5 finding).
- Adapter tests use the same `tmp_path`-backed SQLite
  pattern — the adapter takes the same connection the
  repository tests would have built. Helper functions
  (`_build_event(event_type, ...)`,
  `_common(event_type, payload, **overrides)`,
  `_seed_w11_accounts(...)`) port across as needed; if
  they end up shared between repository and adapter
  test files, place them in a per-test-file private
  helper rather than a shared conftest (keep
  `tests/conftest.py` untouched).

### §5.4 — Test relocation mechanics

The two W14 test files are untracked in git
(per W14 report §6 — `tests/store/` was already
untracked at W14 session open; W14's new test files
roll up under the parent directory's `??` entry).
Moving them is filesystem-level — no git operations
needed.

Procedure for each move:

1. Read original file content via `Desktop Commander:read_file`.
2. Apply the reshape edits per §5.3 (for the repository
   test file) or keep content unchanged (for the schema
   test file).
3. Write to the new destination via
   `Desktop Commander:write_file`.
4. Verify by reading the new file.
5. Delete the original via
   `Desktop Commander:start_process rm
   /Users/tim/Desktop/Projects/bethub-v3/tests/store/test_cash_flow_<schema|repository>.py`.
6. Verify deletion via
   `Desktop Commander:list_directory tests/store/`.
7. Run the relocated tests immediately to confirm
   imports and fixtures resolve under the new path.

The post-W14.1 `tests/store/` listing should match the
W11 / bets-tests layout:

```
tests/store/
├── __init__.py
└── repositories/
    ├── __init__.py
    ├── test_accounts_repository.py
    ├── test_accounts_schema.py
    ├── test_bets.py
    ├── test_cash_flow_repository.py   ← W14.1 (relocated + reshaped)
    └── test_cash_flow_schema.py        ← W14.1 (relocated, unchanged)
```

No stray empty `test_cash_flow_*.py` files at
`tests/store/` root post-relocation.

---

## §6 — Sequencing within session

### §6.1 — Pre-build alignment check against shipped W14 substrate

Before any edits land, Code reads the shipped W14
substrate and confirms the brief's assumptions hold.
Five checks, ~5 minutes of session budget; catches a
class of expensive rework cheaply.

1. **W14 repository present and shape matches.** Read
   `store/repositories/cash_flow.py`. Confirm the
   classes / methods named in §5.2 exist with their
   current Pydantic signatures (`append_event(event:
   CashFlowEventBase)`, `get_event(event_id: UUID)
   -> CashFlowEventBase`, etc.). W14.1's repository
   trim assumes these are present to convert.
2. **W14 domain layer present and intact.** Read
   `domain/cash_flow/__init__.py`. Confirm
   `CashFlowEventBase`, `CashFlowEventType`,
   `PAYLOAD_BY_EVENT_TYPE`, `Payee`, the eight payload
   subclasses, and the FK-nullability-per-event-type
   model validator all exist. W14.1's adapter imports
   them; if any are missing or renamed, W14.1's import
   block is wrong.
3. **W14 schema layer present and intact.** Read
   `store/schema/cash_flow.py`. Confirm
   `apply_migrations(conn)` is callable. W14.1 doesn't
   touch this file but the adapter / repository need
   the schema to migrate cleanly during tests.
4. **`workflows/bet_entry/v1/` directory shape.** Read
   `workflows/bet_entry/v1/` and (at least one) shipped
   file inside. Confirm the package-marker pattern
   (`__init__.py` empty or one-line docstring) and the
   adapter file naming convention. W14.1's new
   `workflows/cash_flow/v1/cash_flow_store_adapter.py`
   follows whatever convention the bet_entry adapter
   uses.
5. **`tests/store/repositories/` layout.** Read the
   directory listing. Confirm `__init__.py` exists
   and the W11 / bets test files are at the expected
   paths. W14.1's relocated cash_flow tests land
   alongside.

If any check reveals divergence between brief
assumptions and shipped substrate, Code surfaces
immediately under a clear "Alignment finding" header
in the report; halts further work pending operator-
Claude triage; does not attempt to bridge the
divergence unilaterally (per §9.1 hard limit).

### §6.2 — Build order

Order matters because the test suite is the
verification surface and each step needs to leave
the suite in a runnable state. Recommended sequence:

1. **Add the four new package marker `__init__.py`
   files first.** Empty or one-line docstring.
   `workflows/cash_flow/__init__.py`,
   `workflows/cash_flow/v1/__init__.py`,
   `tests/workflows/cash_flow/__init__.py`,
   `tests/workflows/cash_flow/v1/__init__.py`. This
   prepares the package structure before the modules
   that live inside it.
2. **Write the adapter** at
   `workflows/cash_flow/v1/cash_flow_store_adapter.py`.
   Import block, helper functions
   (`_row_to_event`, `_event_to_row`, `_row_to_payee`,
   `_payee_to_row`), `CashFlowStoreAdapter` class
   with all public methods. The adapter calls the W14
   repository's existing Pydantic-typed methods at
   this point — temporarily acceptable; trim
   happens next.
3. **Trim `store/repositories/cash_flow.py`** to
   row-only per §5.2. Remove domain imports, remove
   the dispatch table reference, remove the Pydantic
   conversion helpers, rename and re-type every
   method per §5.2.
4. **Update the adapter** to call the now-row-only
   repository (replace `self._events.append_event(event)`
   with `self._events.append_row(self._event_to_row(event))`,
   etc.). The adapter now owns the translation.
5. **Run existing tests** (`uv run pytest tests/store/
   -q`) — most will fail because they construct Pydantic
   events and call methods that no longer exist or
   return the wrong type. Expected; the failures are
   the reshape signal.
6. **Move the schema test file** to its new path
   under `tests/store/repositories/`. Re-run the schema
   tests via `uv run pytest
   tests/store/repositories/test_cash_flow_schema.py
   -v`; all 10 should pass unchanged.
7. **Move and reshape the repository test file** to
   its new path; reshape per §5.3 (row-level
   assertions, drop Pydantic-side tests). Re-run via
   `uv run pytest
   tests/store/repositories/test_cash_flow_repository.py
   -v`.
8. **Write the new adapter test file** at
   `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`.
   Pydantic-side tests per §5.3. Run via
   `uv run pytest
   tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py
   -v`.
9. **Full regression run** — `uv run pytest tests/ -q`.
   Confirm W11 / W10 / W4 / W6 suites still pass.
10. **Run `lint-imports`, `mypy`, `ruff`** —
    confirm DR-030 contracts now pass; confirm
    type-check and lint clean on the new and edited
    files.

Code is free to deviate when a different order is
operationally cleaner — e.g., write the adapter and
repository together to keep both in mind. The broad
order (package markers → adapter scaffold → repository
trim → adapter-repo wiring → test moves → test reshape
→ new adapter tests → regression → gate check) is the
discipline.

**Test-as-you-go preferred over tests-at-end.** Each
phase ends with a pytest run for the surface that
phase touched. Catches integration issues cheaply.

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
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/workflows/`
  — confirm `cash_flow/` does NOT exist yet (but
  `bet_entry/` and `burst_review/` do).
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/tests/workflows/`
  — confirm `cash_flow/` does NOT exist yet (but
  `bet_entry/` does).
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/tests/store/`
  — confirm the two W14 test files
  (`test_cash_flow_schema.py`,
  `test_cash_flow_repository.py`) ARE present at the
  store root, and `repositories/` directory exists.
- `wc -l /Users/tim/Desktop/Projects/bethub-v3/store/repositories/cash_flow.py`
  — line count baseline for the trim (W14 shipped at
  694 lines; W14.1 post-trim target ~350–500).
- `wc -l /Users/tim/Desktop/Projects/bethub-v3/store/__init__.py`
  — line count baseline. W14.1 does NOT touch this
  file; baseline confirms no drift.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/store/ -q 2>&1 | tail -20` — confirm
  existing W14 + W11/W10 tests pass on the dirty tree
  (93 tests passed per W14 report §4.1; this is the
  regression baseline).
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  lint-imports 2>&1 | tail -20` — confirm the 2 broken
  contracts surface from the W14 import line as
  documented in W14 report §4.1. This is the failure
  W14.1 fixes; the post-baseline must show "all
  contracts kept".

### §7.2 — Post-baselines (capture at session close)

After all edits land:

- `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  — session-close Adelaide-local anchor.
- `git -C /Users/tim/Desktop/Projects/bethub-v3 status
  --short` — post-edit snapshot. Confirm: every entry
  from §7.1's snapshot still present (un-committed
  W10/W11/Betfair/W14 work untouched); new entries for
  `workflows/cash_flow/`, `tests/workflows/cash_flow/`
  as `??`; `store/repositories/cash_flow.py` shows as
  `??` (was untracked at W14 close per the report
  §6.2), with content trimmed; the two W14 test files
  at `tests/store/test_cash_flow_*.py` no longer
  exist (they moved into `tests/store/repositories/`).
- `wc -l` on every new and edited file — record line
  counts. Confirm the repository trim landed (W14
  shipped 694 lines; W14.1 target ~350–500 — the cut
  is roughly the Pydantic helpers, the dispatch table,
  the per-method Pydantic translation).
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/store/repositories/test_cash_flow_*.py
  -v 2>&1` — schema tests (10) + reshaped repository
  tests (~18–22) pass.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/workflows/cash_flow/v1/ -v 2>&1` —
  new adapter test file passes (~25–30 tests).
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/ -q 2>&1 | tail -20` — full suite
  regression. Confirm no W11 / W10 / W4 / W6 / clients
  tests broke. Test count: W14 left tests/store/ at 93
  (46 pre + 47 W14); W14.1 lands tests/store/ at ~30
  + tests/workflows/cash_flow/v1/ at ~25–30 — net
  total across all suites should be ≥ 93 (no test
  count regression; small expansion expected).
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  lint-imports 2>&1` — **the gate W14.1 exists to
  fix.** Confirm all five contracts pass (5 kept, 0
  broken). If any contract still fails, that is the
  load-bearing finding to surface.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  mypy workflows/cash_flow store/repositories/cash_flow.py
  2>&1 | tail -20` — type-check the changed and new
  code.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  ruff check workflows/cash_flow store/repositories/cash_flow.py
  tests/store/repositories/test_cash_flow_*.py
  tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py
  2>&1` — lint the changed and new code.

### §7.3 — File-existence and content checks

For each named anchor:

- **New files exist:**
  `workflows/cash_flow/__init__.py`,
  `workflows/cash_flow/v1/__init__.py`,
  `workflows/cash_flow/v1/cash_flow_store_adapter.py`,
  `tests/workflows/cash_flow/__init__.py`,
  `tests/workflows/cash_flow/v1/__init__.py`,
  `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`.
- **Edited file at expected path:**
  `store/repositories/cash_flow.py` — content trimmed,
  no `domain.cash_flow` imports remain (grep
  confirms).
- **Relocated files at new paths:**
  `tests/store/repositories/test_cash_flow_schema.py`,
  `tests/store/repositories/test_cash_flow_repository.py`.
- **Original test paths are gone:**
  `tests/store/test_cash_flow_schema.py` does NOT
  exist; `tests/store/test_cash_flow_repository.py`
  does NOT exist.
- **Line counts within ballpark:** Code names actuals
  in the report. Rough sanity guides (not hard limits):
  - `workflows/cash_flow/v1/cash_flow_store_adapter.py`:
    ~350–550 lines.
  - `store/repositories/cash_flow.py` (post-trim):
    ~350–500 lines.
  - `tests/store/repositories/test_cash_flow_schema.py`:
    ~450 lines (unchanged from W14 ship).
  - `tests/store/repositories/test_cash_flow_repository.py`
    (reshaped): ~400–550 lines.
  - `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`:
    ~450–700 lines.
- **`grep "from domain" store/repositories/cash_flow.py`**
  returns no matches — confirms the domain imports were
  removed cleanly. (This is the empirical test for
  "DR-030 restored" beyond the `lint-imports` gate.)
- **`grep "from store.repositories.cash_flow"
  workflows/cash_flow/v1/cash_flow_store_adapter.py`**
  returns at least one match — confirms the adapter
  reaches the repository correctly.

### §7.4 — Spot-check: end-to-end round-trip via adapter

After all writes land, run a one-shot Python script
via `start_process` (write to `/tmp/w14_1_smoke.py`,
not interactive REPL — per Cat 3 REPL discipline) that
mirrors W14's smoke script but exercises the public
adapter surface:

1. Opens a `tempfile.NamedTemporaryFile`-backed SQLite
   connection.
2. Applies W11 migrations (accounts / books /
   accounts_at_book), then W14 migrations.
3. Seeds one account, book, account-at-book.
4. Constructs a `CashFlowStoreAdapter` instance.
5. Calls `adapter.append_event(...)` once for each of
   the 8 event types (constructing valid Pydantic
   events per FK rules per event type).
6. Calls `adapter.list_by_account_at_book(...)` and
   `adapter.list_by_account(...)`; asserts the
   correct subset returns per FK rules.
7. Calls `adapter.append_event(...)` with a
   supersedes event for one of the adjustments.
8. Calls `adapter.latest_non_superseded_by_scope(
   account_at_book_id=…)`; asserts the original
   adjustment is excluded.
9. Calls `adapter.walk_supersession_chain(...)`;
   asserts the chain shape (Pydantic models,
   earliest-first).
10. Closes the adapter, deletes the temp DB, prints
    `"W14.1 adapter: 8/8 event types round-trip OK;
    supersession-chain walk OK; latest-non-superseded
    read OK."` or surfaces the failure.

This is belt-and-braces alongside the pytest suite —
the smoke check exercises the full integration shape
end-to-end through the public adapter surface, fast.

---

## §8 — Output spec

Single report at exactly this path:

`dr029/w14_cash_flow/w14_1_adapter_report.md`

Section structure (Code writes this; not a template):

1. **Summary** — one paragraph: what landed, line
   counts per file, test count and pass / fail status,
   `lint-imports` outcome (the load-bearing gate),
   any findings.
2. **Anchors** — session-start and session-close
   Adelaide-local timestamps; commit hash of the v3
   repo at session start (whatever it was — Code does
   not commit).
3. **What was built** — per-file walk-through (one
   short paragraph per file), naming the major
   classes / functions added or moved or removed and
   any design choices worth surfacing. Brief; the
   code is the substrate.
4. **Verification results** — outputs of §7.2 / §7.3
   / §7.4 checks. Include the full pytest output for
   the new and relocated suites; tail outputs for
   `lint-imports`, mypy, and ruff; the smoke-script
   one-liner.
5. **Findings** — anything Code noticed during the
   refactor that the operator-Claude next session
   should triage. Five categories same as W14 (spec
   ambiguity / deferred concern / integration
   surprise / weak test / other).
6. **Dirty-tree adherence statement** — confirms §9.7
   discipline held end-to-end. Include the
   pre / post `git status --short` outputs verbatim
   so the operator-Claude next session can verify.
7. **Self-assessment** — one short paragraph: did the
   work fit the brief's scope; did it fit the
   single-bounded-session envelope; anything Code
   would change about the brief in retrospect.

Length anticipation: ~250–450 lines (smaller than
W14's 864 because the surface is smaller and the
report can lean on the W14 report for context). Not
a hard line. Code reasonably over-runs when findings
justify it.

The report contains **no recommendations for next
brief drafting** — that's operator-Claude triage
territory. Findings name what was observed; routing
of findings is post-session work.

The report contains **no scope-creep into W12/W13/W15
or W11/W4/W6 territory** — those are separate
workstreams; W14.1's report stays within W14.1's
scope.

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

### §9.2 — Behaviour and contract preservation

- **No behaviour change at the adapter's public
  surface.** Every public method on
  `CashFlowStoreAdapter` has the same name, signature,
  return type, error semantics, and observable
  behaviour as the equivalent W14 repository method.
  Callers swapping
  `CashFlowEventRepository(conn).append_event(...)`
  for
  `CashFlowStoreAdapter(conn).append_event(...)`
  should see identical results (excepting the
  `payee.update_payee`'s `updated_at` plumbing — the
  adapter computes Adelaide-local now if the caller
  doesn't supply one, matching W14 behaviour).
- **No schema change.** The W14 DDL is unchanged.
  No new tables, no new columns, no index changes,
  no migration changes. `store/schema/cash_flow.py`
  is read-only for W14.1.
- **No domain model change.**
  `domain/cash_flow/__init__.py` is unchanged. Enums,
  payload subclasses, `CashFlowEventBase`, validators,
  `PAYLOAD_BY_EVENT_TYPE`, `Payee` — all read-only.
- **No `store/__init__.py` change.** The W14 additive
  edit stays as it landed. The adapter is not
  re-exported through `store/`; callers import from
  `workflows.cash_flow.v1`.
- **Error class preservation.** Every W14 error class
  (`CashFlowEventError`, `DuplicateEventError`,
  `EventNotFoundError`, `SupersessionCycleError`,
  `InvalidScopeError`, `PayeeError`,
  `DuplicateEntityError`, `EntityNotFoundError`) stays
  at the repository module and propagates through the
  adapter unchanged. No new error classes at the
  adapter layer.

### §9.3 — No adjacent workstreams or findings

- **No W11 work.** `store/repositories/accounts.py`
  and `domain/accounts/__init__.py` are read-only.
  Whether the W11 accounts surface needs its own
  workflow-side adapter is W11's concern; W14.1 does
  not propose it, does not draft it, does not build
  it.
- **No W4 / W6 work.** `store/repositories/bets.py`,
  `domain/bets/__init__.py`, and the in-flight
  `workflows/bet_entry/v1/` content are all read-only
  beyond reading for pattern reference.
- **No W12 work.** Do not implement balance
  derivation, Location 1 / Location 2 formulas, or
  any read-side that combines cash_flow_events with
  bets data.
- **No W13 work.** Do not touch `promo_events` or
  create the table.
- **No W15 work.** Do not touch `ops_events` or
  create the table.
- **No day-0 seeding tool.** W14 ships the substrate,
  W16 fires the seeding.
- **No reconciliation reports.** Separate sub-stream.
- **No operator UI for entry.** W17+ work.
- **No analytical layer hooks.** P2 work.
- **No fixing of W14 findings beyond §5.1 (this
  brief's reason for existing) and §5.4 (test layout
  folded in).** Findings §5.2, §5.3, §5.5, §5.6,
  §5.7, §5.8, §5.10 are not addressed.

### §9.4 — No Alembic, no debt-fixing

- **No Alembic adoption.** Carried per W10 / W11 / W14
  deferrals (`apply_migrations` pattern continues).
  W14.1 does not touch migrations.
- **No test-coverage extension to other suites.** Debt
  1 ("No test coverage" — applies to the VPS-side
  pipeline) is not in scope. W14.1 ships its own
  adapter tests and reshaped repository tests per
  §5.3; other test suites are read-only.
- **No monolithic-orchestrator work.** Debt 3 does
  not touch W14.1.

### §9.5 — No SQLAlchemy Core migration

DR-031 specifies SQLAlchemy Core for v3 but the
shipped storage layer uses raw `sqlite3` (Finding #6
from S123 review, parked). W14.1 follows the shipped
pattern, not the spec. The Core migration is a
separate concern out of scope.

### §9.6 — Operational guardrails

- **Read-only on databases except in-memory / temp
  test DBs.** No production-shape DB file is written
  by W14.1; test suite creates and tears down
  `tmp_path`-backed SQLite connections.
- **No `create_file` tool.** Per
  `standing_instructions.md` Cat 3, banned for
  filesystem work. Use Desktop Commander or
  `projects-filesystem` MCP. If operating in a
  Claude Code CLI environment where these are not
  loaded, native `Write` / `Edit` are acceptable
  substitutes provided the Cat 3 spirit holds
  (verify every write).
- **REPL discipline.** Multi-line Python via
  temp-file + `start_process` (e.g.,
  `write_file /tmp/script.py` then
  `start_process python3 /tmp/script.py`). Avoid
  pasting multi-line Python into an interactive
  REPL.
- **Verify every write.** After each `write_file`
  to a v3 source file, read it back with
  `read_file` or `head` / `tail` to confirm content
  landed at the expected Mac path. Surface any
  write that doesn't land cleanly as a finding.
- **Single bounded Code session.** Per §9.1.

### §9.7 — Dirty-tree handling (load-bearing this session)

The v3 working tree was dirty at W14 close (per W14
report §6) and will still be dirty at W14.1 open.
`git status --short` will show 10 modified entries
plus a number of untracked entries including the W14
anchor paths (`workflows/bet_entry/v1/`,
`store/repositories/cash_flow.py`,
`store/repositories/accounts.py`,
`store/repositories/bets.py`, `domain/accounts/`,
`domain/cash_flow/`, the test directories, etc.). This
is the operator's expected state.

**The §9.7 dirty-tree handling from W14 carries forward
verbatim.** Forbidden git operations for the duration
of the session:

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
2. **Edit only the named anchors.**
3. **For greenfield writes** (the four new package
   marker files, the adapter, the new adapter test
   file), the writes appear in `git status` as `??`
   under their parent directories. No `git diff`
   check is needed but re-read the written file via
   `read_file` to confirm content landed.
4. **For the `store/repositories/cash_flow.py` trim**,
   the file was untracked (`??`) at session open per
   W14 close. After the trim, it remains `??` (or
   shows as untracked under a parent if the parent
   path is `??`). No `git diff` against a baseline is
   meaningful here — verify content by direct read of
   the file post-trim and grep for the absence of
   `from domain` imports.
5. **For the two test file moves**, the originals at
   `tests/store/test_cash_flow_*.py` were untracked
   under the parent `tests/store/` `??` entry. After
   the moves, the new locations
   (`tests/store/repositories/test_cash_flow_*.py`)
   surface naturally and the originals are gone from
   disk (verify via `list_directory`).
6. **At session close**, run `git status --short` and
   confirm: every entry from the §7.1 baseline still
   present in the same status (modified entries
   still `M`, untracked entries still `??`, etc.);
   no entries disappear unexpectedly; no entries
   change status unexpectedly. The new W14.1 paths
   surface as additions; the moves leave no orphan
   `??` entries.

**If dirty regions intersect W14.1's edit anchors
unexpectedly** (e.g., the `store/repositories/cash_flow.py`
file has been modified between W14 close and W14.1
open by some other in-flight work — unlikely, but
the §7.1 pre-baseline diff against W14 report §6.2
should catch any drift): Code halts, surfaces as a
finding, does not edit. The operator-Claude next
session triages.

**The behaviour-preservation discipline (§9.2) is the
load-bearing one alongside dirty-tree.** Every
adapter method must produce the same observable
behaviour as the W14 repository method it replaces;
any divergence in error semantics, return shape, or
edge-case handling is a finding, not in-scope work.

Substrate: W14 brief §9.7 (which inherited from
Session 36 Fix 3 — the original dirty-tree handling
pattern). `standing_instructions.md` Cat 3 catalogues
the rules generally.

---

## §10 — What happens after Code's session

The next operator-Claude session reads
`dr029/w14_cash_flow/w14_1_adapter_report.md` and
runs a triage pass. Expected shape:

1. **Verification check.** Did the work land at the
   expected paths with the expected shape? Did the
   tests pass? Did `lint-imports` come up clean (the
   load-bearing gate W14.1 exists to fix)? Did mypy /
   ruff pass? Is the dirty-tree adherence statement
   clean (pre / post `git status` diffs as expected)?
2. **Findings triage.** For each finding in §8 item
   5: spec ambiguity → architecture / decisions
   amendment or brief addendum; deferred concern →
   W14.2 follow-up brief or parking lot; integration
   surprise → W11 / W14 amendment or W14.2 defence;
   weak test → W14.2 or W13 follow-up; other →
   case-by-case.
3. **Forward routing.** Three plausible shapes:
   - **Clean W14 close.** Most likely if `lint-imports`
     passes, regression is green, and no material
     findings surface. W14 → `done` (one-session
     carry); W14.1 → `done`; W13 → `in flight`
     (brief drafting becomes next active stream).
   - **W14.2 follow-up.** If findings warrant — e.g.
     a regression that the test reshape introduced,
     or an integration surprise with the adapter
     pattern that W13 / W15 would also hit.
   - **Partial-ship triage.** If Code surfaced
     scope-doesn't-fit as a finding (the brief
     authorised this via §9.1). The next session
     triages what landed, what didn't, routes the
     remainder.
4. **Build-picture update.** W14.1 transitions from
   `in flight` to `done` (one-session carry) if
   clean; W14 → `done` at the same time; W13 →
   `in flight` if no W14.2 needed.

Code does **not** produce the next brief. Code
produces the report; the next operator-Claude
session produces W13's brief (or W14.2's brief if
needed).

---
## §11 — Cross-references

### §11.1 — Architecture and decisions

- `architecture.md` §A.2 — per-domain event log spine
  + common event header (unchanged by W14.1; the
  shape lives in `domain/cash_flow` and persists
  through schema + adapter unchanged).
- `architecture.md` §A.5 — cash flow model (unchanged
  by W14.1; W14 ships the substrate, W14.1 keeps it
  intact).
- `decisions.md` DR-030 + Session 124 amendment — v3
  module-boundary discipline. **The load-bearing
  reason W14.1 exists.** After W14.1, `lint-imports`
  passes on all five contracts.
- `decisions.md` DR-027 + Session 124 amendment —
  two-database architecture + per-domain event-table
  internal shape. Unchanged by W14.1.
- `decisions.md` DR-019 + Session 124 amendment —
  derived state on read. The critical asymmetry
  (applies to bet records but NOT cash flow events)
  carries through unchanged.
- `decisions.md` DR-032 — canonical-reference-layer.
  Reference only.
- `decisions.md` DR-022 — book / account /
  account-at-book vocabulary. FKs on cash flow
  events still use this vocabulary; unchanged by
  W14.1.
- `decisions.md` DR-021 — Adelaide local timestamp
  anchoring. Adapter helper computes Adelaide-local
  `updated_at` on `update_payee` when not supplied;
  rest of the timestamp surface is unchanged.

### §11.2 — Prior briefs and reports

- `dr029/w14_cash_flow/w14_cash_flow_brief.md` — W14
  brief. The substrate W14.1 refactors. §5.1, §5.2,
  §5.3, §5.4, §5.5, §6.2, §9.7 all referenced inline.
- `dr029/w14_cash_flow/w14_cash_flow_report.md` —
  W14 report. §5.1 (the load-bearing finding driving
  W14.1), §5.4 (the test layout folded in), §4.1
  (the `lint-imports` failure W14.1 fixes), §6 (the
  dirty-tree state W14.1 inherits).
- `dr029/w11_accounts/w11_accounts_brief.md` —
  precedent for the row-only repository pattern.
  Particularly §5.3 ("No domain imports — `store/`
  imports nothing in the project").
- `dr029/2_1_race_data/fix_3_brief.md` (Session 36) —
  original dirty-tree handling pattern. Substrate
  for §9.7 via W14 brief.
- `sessions/SESSION_127.md` — W14 brief drafting and
  dispatch record.
- `sessions/SESSION_128.md` — W14 report triage
  record (this session). Records the (i) vs (ii)
  routing decision and the operator's option-1 call
  to draft W14.1 within S128 rather than defer to
  S129.

### §11.3 — Standing instructions and governance

- `standing_instructions.md` Cat 1 — communication
  register, silent-ritual rules, hard line wraps.
- `standing_instructions.md` Cat 3 — filesystem and
  tooling discipline (`create_file` ban, verify-
  every-write, REPL discipline, dirty-tree handling
  generally, pre-execution risk advisory).
- `standing_instructions.md` Cat 5 — operator /
  Claude division of labour. The eight Cat 5
  software calls made in §5 (W14 brief drafting)
  carry forward unchanged into W14.1; the three
  additional W14.1 calls are surfaced in §1.3.
- `governance.md` "Final data-layer lock review
  (DR-029 close-out)" — three pieces of named debt
  inherited; W14.1 carries them per §9.4.
- `vision.md` — non-negotiables. W14.1 doesn't
  change the operational picture; the adapter's
  public surface preserves W14's behaviour.

### §11.4 — Parking-lot items the brief excludes

- DR-025 hedge classification (revisit-before-W15
  flag). Not relevant to W14.1.
- §2.4 Fix 4 cadence design (Finding #3 dependency
  for §2.10 P1). Not relevant.
- Fix 5 venue harmonisation. Not relevant.
- Operational soft-book layer (§2.5 deferred per
  Session 69). Not relevant.
- §2.10 bucket-1 / bucket-2 (P1 / P2 — post-cutover
  + analytical layer). Not relevant.
- W11 accounts adapter / re-export — separate
  concern, not W14.1.
- Audit-trail surface for settlement transitions
  (Deferred capability 7 per `governance.md`).
  Separate.
- W14 minor findings §5.2 / §5.3 / §5.5 / §5.6 /
  §5.7 / §5.8 / §5.10. Out of W14.1 scope.

### §11.5 — Build-picture context

- `v3_build_picture.md` (Session 127 update) — W14 is
  `in flight`; W14.1 inserts as an active sub-stream
  under W14 at S128 close. W13 / W15 stay
  `blocked-on-W14` (now meaning blocked on W14 +
  W14.1 closing). W12 stays
  `blocked-on-W13-and-W14`.

---

**Brief lock complete.** W14.1 is the contract; Code
executes against it in a single bounded session,
produces the report named in §8, and the operator-
Claude next session triages per §10.
