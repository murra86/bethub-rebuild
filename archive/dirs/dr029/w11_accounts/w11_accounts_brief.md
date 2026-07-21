# W11 brief — Accounts + account-at-book data layer

**Status:** locked Session 120.
**Lock anchor:** 2026-05-11 20:15 ACST (Adelaide local per DR-021).
**Workstream:** W11 (accounts + account-at-book, the first
operational-store sub-stream).
**Recipient:** Claude Code, single bounded session.
**Brief location:**
`dr029/w11_accounts/w11_accounts_brief.md`.

---

## §1 — What this brief is and is not

### §1.1 — What this brief is

This brief commissions Code to build the **accounts data
layer** for v3 — the schema, Pydantic domain models, and
repository surface for three new entities:

- **`accounts`** — the real people who hold registrations at
  bookmakers (Tim, Kate, Sarie, friends).
- **`books`** — the bookmaker organisations (Sportsbet,
  Ladbrokes, PointsBet, etc.) with reference attributes.
- **`accounts_at_book`** — the registration of one account at
  one book; the unit at which money sits, promos are received,
  and operational state lives downstream.

W11 is the first of five operational-store sub-streams
(W11–W15). It is the substrate every later sub-stream depends
on: balances (W12), promos (W13), transactions (W14), and
operations log (W15) all attach to `account_at_book_id`. The
existing `bets.account_at_book_id` column in the storage layer
(written W4–W6, shipped W10 lift) gains a real referent table.

The work ships as exactly three production source files plus
two test files:

- `domain/accounts/__init__.py` — Pydantic v2 models.
- `store/schema/accounts.py` — DDL + idempotent migration.
- `store/repositories/accounts.py` — row dataclasses +
  repository surface.
- `tests/store/test_accounts_schema.py` — schema-level tests.
- `tests/store/test_accounts_repository.py` — repository
  CRUD tests.

### §1.2 — What this brief is not

W11 v1 explicitly does **not** ship:

- **Balances** (W12 territory). Per-account-at-book balance
  state, cash-flow event handling, and cash-flow custodian
  surfaces all live in W12.
- **Promos** (W13 territory). Promo eligibility, free-bet
  inventory, cycle linkage to bet records all live in W13.
- **Transactions** (W14 territory). Deposit / withdrawal /
  settlement transaction log and the cash-flow event-type
  surfaces (`account_holder_funding`,
  `account_at_book_deposit`, etc., per `architecture.md`
  Slice 5) live in W14.
- **Operations log** (W15 territory). The append-only
  operational events log lives in W15.
- **Tier and phase fields on account-at-book.** DR-022 names
  tier and phase as account-at-book properties ("tier and
  phase are tracked, and conditioning happens"), but the
  vocabularies are not yet locked. Deferred to a small later
  sub-stream once the vocabulary work is done. Operator
  decision Session 120 — W11 ships identity-only.
- **Account isolation infrastructure metadata.** MiFi router
  / SIM / AdsPower profile linkage to account-at-book is a
  future concern; the data shape will be decided in a
  separate DR or amendment. Not in W11 scope.
- **Persona → account vocabulary sweep across the codebase.**
  DR-022 supersedes the term "persona" in older DRs; any
  documentation or code references to "persona" elsewhere
  are separate housekeeping.
- **Alembic adoption.** Carried as deferred per W10 brief
  §10.2 and W10.1 brief §9.4. W11 follows the existing v3
  pre-Alembic schema pattern (`store/schema/bets.py`
  precedent — inline `CREATE TABLE IF NOT EXISTS` DDL +
  idempotent column-add helper + module-level
  `apply_migrations(conn)` invoked by the repository on
  init).
- **Schema changes to the `bets` table.** The existing
  `bets.account_at_book_id TEXT NOT NULL` column stays
  unchanged. W11 does **not** add a `FOREIGN KEY` constraint
  to `bets.account_at_book_id` referencing the new
  `accounts_at_book` table — that's a separate hygiene
  decision once the new table is real.
- **Operator-facing UI for managing accounts / books /
  registrations.** UI is W17+ territory.
- **`ownership_cluster` as a separate reference table.**
  `architecture.md` lines 56–80 names the entity chain
  `account_at_book → book → ownership_cluster`. W11 carries
  `ownership_cluster` as a TEXT field on the `books` row,
  not a separate normalised table. A future amendment can
  promote to a reference table once clusters acquire their
  own attributes; day-0 the string is sufficient.

### §1.3 — Why W11 v1 is identity-only

The operator's strategic call at Session 120: W11 v1 ships
**identity + basic active/inactive status only**. Tier and
phase fields on account-at-book are deferred because:

- The tier vocabulary (limiting-state values: clean /
  restricted / closed / etc.) is not yet locked.
- The phase vocabulary (lifecycle stages: onboarding /
  conditioning / mature / etc.) is not yet locked.
- The state-transition rules (what moves an account-at-book
  between values, who or what writes the transition) are not
  yet locked.
- W12–W15 do not depend on tier / phase to land — they
  depend only on identity (`account_at_book_id` as a foreign
  key target).

Adding tier and phase later is a small additive migration
(`_add_column_if_missing` pattern, which W11's schema module
provisions for); deferring does not lock W11 out of those
columns when they're ready.

---

## §2 — Why this work exists

W10's storage lift shipped at Session 119 with one DR-030
contract break (Finding B). W10.1 closed the break at the top
of Session 120. With W10 closed, W11–W15 (the five
operational-store sub-streams) come off the block. W11 is
the substrate they all reference.

DR-022 (the vocabulary correction decision — account / book /
account-at-book supersedes earlier "persona" usage) is the
operative governance for entity names and shape. W11 turns
DR-022's locked vocabulary into code: three tables, three
Pydantic models, repository methods that use the locked
nouns.

The existing `bets.account_at_book_id` column has been a
dangling reference since W4 shipped — the bets schema names
the column, values get written at bet entry, but no table
exists to give the value a meaningful referent. W11 closes
that gap (though FK enforcement on `bets.account_at_book_id`
is deferred per §1.2).

DR-027/028 (the two-database boundary discipline) places
account data unambiguously on the BetHub side. Account-at-
book identity is operational state — never read from
`capture.db`, never written to `capture.db`, never joined
across the boundary.

DR-030 (v3 repo layout + module-boundary discipline) governs
where W11 code lives: `domain/accounts/` for pure Pydantic
models, `store/schema/accounts.py` for DDL,
`store/repositories/accounts.py` for the repository surface.
Import-graph rules apply unchanged.


---

## §3 — Pre-reads

### §3.1 — Required reads (read before starting)

1. **`decisions.md` §DR-022** (vocabulary lock: account /
   book / account-at-book noun definitions; "one account
   never holds two registrations at the same book"
   constraint).
2. **`decisions.md` §DR-027** (two-database architecture:
   accounts data lives on BetHub side).
3. **`decisions.md` §DR-028** (boundary discipline: no
   caching, no denormalisation, no second integration
   point).
4. **`decisions.md` §DR-030** (v3 repo layout +
   import-graph rules: the directory placement and
   import-graph constraints govern §5 scope below).
5. **`store/schema/bets.py`** — the pattern precedent for
   v3 schema modules. DDL constants,
   `_add_column_if_missing` helper, `apply_migrations(conn)`
   function. W11 follows the same shape.
6. **`store/repositories/bets.py`** — the pattern precedent
   for v3 repository modules. Raw `sqlite3` (not SQLAlchemy
   Core), frozen `@dataclass` row types, `apply_migrations`
   call on init, query shape. W11 follows the same shape.

### §3.2 — Reference-only (read on demand)

- `architecture.md` lines 56–80 — the entity diagram and
  reference-data section. **Vocabulary note:**
  `architecture.md` uses `account_holders` in some sections
  as a legacy term for the cash-flow custodian; per DR-022,
  read as `accounts`. W11 uses DR-022 vocabulary
  (`accounts`).
- `decisions.md` §DR-031 — v3 tech stack. **Divergence
  note:** DR-031 names SQLAlchemy Core as the v3 ORM/query
  layer, but the existing v3 bets store uses raw `sqlite3`.
  W11 matches the existing v3 pattern (raw sqlite3) rather
  than DR-031's locked spec. Migration of the store layer
  to SQLAlchemy Core is a separate later concern, not W11.
- `decisions.md` §DR-032 — canonical reference layer for
  bet records. Context for why `bets.account_at_book_id`
  exists and what W11's `accounts_at_book` table closes.
- `dr029/w10_storage_lift/w10_brief.md` and
  `w10_1_brief.md` — schema-pattern precedent (W10) and
  surgical-fix shape precedent (W10.1).
- `dr029/w4_bet_entry/w4_bet_entry_brief.md` — "build new"
  brief-shape precedent.

---

## §4 — System access

- **Mac filesystem read-write** on
  `/Users/tim/Desktop/Projects/bethub-v3/`. Code creates
  new files at the named locations in §5 and modifies no
  existing source files outside those locations.
- **No database access.** No queries against `bethub.db`
  (v2) or `capture.db` (VPS). Tests use ephemeral SQLite
  via `tmp_path` per the existing v3 test pattern.
- **No Betfair API calls. No HTTP calls. No external
  service access of any kind.**
- **No git operations.** No `git add`, `git commit`,
  `git stash`, `git restore`, `git reset`. The working
  tree state is whatever Code finds at session open;
  W11's new files are untracked at session close.
- **Adelaide local timestamps** (ACST / ACDT) per DR-021
  for every time-of-day reference in the report.

---

## §5 — Substantive scope

### §5.1 — Domain models (`domain/accounts/__init__.py`)

Single new module at `domain/accounts/__init__.py`. Pydantic
v2 models per DR-031. Module-level imports: stdlib +
Pydantic only (DR-030 — `domain/` imports nothing in the
project).

**Module docstring** names: the entity set (accounts, books,
accounts-at-book), DR-022 as the vocabulary source, and
DR-030 placement (`domain/` is pure; importers will be
`workflows/` and `tests/` once they exist; `store/` does
**not** import these models — store-side uses its own row
dataclasses per §5.3).

**Three Pydantic models, in this order in the file:**

```python
class Account(BaseModel):
    account_id: str          # TEXT primary key, v3 ID
                             # convention (TEXT not INTEGER)
    name: str                # human-readable: "Tim", "Kate"
    is_self: bool            # True for Tim; False for Kate,
                             # Sarie, friends. Distinguishes
                             # the operator's own account
                             # from custodian accounts.
    active: bool = True      # False = archived / retired.
    created_at: datetime     # Adelaide local timestamp at
                             # row creation, per DR-021.

class Book(BaseModel):
    book_id: str             # TEXT primary key, stable
                             # canonical ID
                             # (e.g. "sportsbet").
    name: str                # display name ("Sportsbet").
    ownership_cluster: str | None  # cluster name as TEXT;
                             # not normalised to a separate
                             # table day-0. Nullable.
    platform: str | None     # softbook platform name
                             # ("Entain", "BetMakers") where
                             # known. Nullable.
    active: bool = True

class AccountAtBook(BaseModel):
    account_at_book_id: str  # TEXT primary key, matching the
                             # bets.account_at_book_id column
                             # shape already in the schema.
    account_id: str          # FK to accounts.account_id.
    book_id: str             # FK to books.book_id.
    active: bool = True
    created_at: datetime     # Adelaide local timestamp at
                             # registration, per DR-021.
```

**Field-by-field rationale:**

- `account_id`, `book_id`, `account_at_book_id` are TEXT,
  not INTEGER. Matches the existing v3 ID convention
  (`bets.account_at_book_id TEXT NOT NULL`). TEXT values
  can be human-readable slugs (e.g. `"tim"`, `"sportsbet"`,
  `"tim_sportsbet"`) or UUIDs; the brief is agnostic about
  generation strategy — Code's call on whether to provide a
  generator helper or expect callers to supply IDs.
- `is_self` on `Account` distinguishes the operator from
  custodian accounts. Useful for UI filtering and
  reporting; W12+ cash-flow events that distinguish
  Tim-personal flows from custodian-internal flows rely on
  this flag.
- `ownership_cluster` on `Book` is TEXT not a foreign key.
  Day-0 simplification per §1.2.
- `active` is a boolean on all three entities. Simplest
  viable status field. Status enums (limiting tier,
  lifecycle phase, etc.) deferred per §1.2 / §1.3.
- `created_at` is `datetime` (Pydantic v2 native handling);
  at storage time it serialises to ISO8601 Adelaide local
  TEXT.

**No additional models in this brief.** No `BookCluster`,
no `AccountStatus` enum, no `AccountAtBookTier` /
`AccountAtBookPhase`. Future additions are future briefs.

### §5.2 — Schema (`store/schema/accounts.py`)

Single new module at `store/schema/accounts.py`. Module-level
imports: stdlib only (`sqlite3`).

**Module docstring** names: DDL for three tables, DR-030
placement (`store/schema/` part of `store/`, no project
imports beyond stdlib), and `apply_migrations(conn)` as the
public surface invoked by the repository on init.

**Three DDL constants, in dependency order in the file:**

```python
_ACCOUNTS_DDL = """
CREATE TABLE IF NOT EXISTS accounts (
    account_id   TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL,
    is_self      INTEGER NOT NULL,   -- bool as 0/1
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT    NOT NULL    -- ISO8601 Adelaide local
);
"""

_BOOKS_DDL = """
CREATE TABLE IF NOT EXISTS books (
    book_id            TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    ownership_cluster  TEXT,
    platform           TEXT,
    active             INTEGER NOT NULL DEFAULT 1
);
"""

_ACCOUNTS_AT_BOOK_DDL = """
CREATE TABLE IF NOT EXISTS accounts_at_book (
    account_at_book_id  TEXT    PRIMARY KEY,
    account_id          TEXT    NOT NULL,
    book_id             TEXT    NOT NULL,
    active              INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT    NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (book_id)    REFERENCES books(book_id),
    UNIQUE (account_id, book_id)
);
"""
```

**Indexes (two partial indexes, filtered on `active = 1`):**

```python
_INDEX_ACCOUNTS_AT_BOOK_BY_ACCOUNT = """
CREATE INDEX IF NOT EXISTS
  idx_accounts_at_book__account_id
  ON accounts_at_book (account_id)
  WHERE active = 1;
"""

_INDEX_ACCOUNTS_AT_BOOK_BY_BOOK = """
CREATE INDEX IF NOT EXISTS
  idx_accounts_at_book__book_id
  ON accounts_at_book (book_id)
  WHERE active = 1;
"""
```

Partial indexes support the "list active registrations for
an account / for a book" queries named in §5.3. SQLite
supports partial indexes natively.

**Migration helper:** include the `_add_column_if_missing`
helper in the file (lifted in shape from `bets.py`), even
though W11 v1 has no migrations to apply beyond initial
CREATE TABLE statements. Defining it here provisions for
future additive changes (e.g. when tier / phase land) and
matches the `bets.py` precedent so future readers find the
same pattern.

**`apply_migrations(conn)` function:**

```python
def apply_migrations(conn: sqlite3.Connection) -> None:
    """Idempotent schema setup for accounts / books /
    accounts_at_book.

    Called by the repository on connect. Safe to invoke on
    every connection; CREATE TABLE IF NOT EXISTS and CREATE
    INDEX IF NOT EXISTS handle the idempotency.

    Future tier / phase columns land here as
    _add_column_if_missing calls.
    """
    conn.executescript(_ACCOUNTS_DDL)
    conn.executescript(_BOOKS_DDL)
    conn.executescript(_ACCOUNTS_AT_BOOK_DDL)
    conn.executescript(_INDEX_ACCOUNTS_AT_BOOK_BY_ACCOUNT)
    conn.executescript(_INDEX_ACCOUNTS_AT_BOOK_BY_BOOK)
    conn.commit()
```

**Constraint named explicitly:** `UNIQUE (account_id,
book_id)` on `accounts_at_book` enforces DR-022's "one
account never holds two registrations at the same book"
rule at the schema level. Violations surface as
`sqlite3.IntegrityError`; the repository's
`register_account_at_book` method catches and returns a
structured error result rather than raising (see §5.3).


### §5.3 — Repository (`store/repositories/accounts.py`)

Single new module at `store/repositories/accounts.py`.
Imports stdlib + the schema module
(`from store.schema.accounts import apply_migrations`). No
domain imports — `store/` imports nothing in the project
beyond `store.schema.*` per DR-030.

**Pattern match:** matches `store/repositories/bets.py`
shape exactly — frozen dataclass row types defined at module
top, repository class encapsulating a sqlite3 connection,
`apply_migrations` invoked in `__init__`, methods take /
return the row dataclasses.

**Row dataclasses (defined at top of file, before the
repository class):**

```python
@dataclass(frozen=True)
class AccountRow:
    account_id: str
    name: str
    is_self: bool
    active: bool
    created_at: datetime

@dataclass(frozen=True)
class BookRow:
    book_id: str
    name: str
    ownership_cluster: str | None
    platform: str | None
    active: bool

@dataclass(frozen=True)
class AccountAtBookRow:
    account_at_book_id: str
    account_id: str
    book_id: str
    active: bool
    created_at: datetime
```

**Domain ↔ row translation:** not in W11 scope. The W4 +
W10 pattern is that workflow-side adapter modules (e.g.
`workflows/bet_entry/v1/bet_store_adapter.py`) handle
translation between row dataclasses and Pydantic domain
models. For W11 there is no consumer workflow yet (W12+
will be the first consumers), so no adapter ships in this
brief. Future workflow briefs will land the adapter when
they need it.

**`RegisterResult` shape** (defined at module top, before
the class, alongside the row dataclasses):

```python
@dataclass(frozen=True)
class RegisterResult:
    success: bool
    reason: str | None = None
    # reason values when success=False:
    #   "ACCOUNT_ALREADY_REGISTERED_AT_BOOK"
    #   "MISSING_REFERENT"
```

The result-type pattern matches v3 convention (structured
errors over exceptions for operational paths; exceptions
reserved for programmer errors).

**Repository class shape:**

```python
class SQLiteAccountsStorage:
    """v1 repository for accounts / books /
    accounts_at_book.

    Connection lifecycle matches SQLiteBetRecordStorage:
    constructor opens connection, calls apply_migrations,
    holds the connection for the storage instance's
    lifetime.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(
            str(db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row
        # Enable FK enforcement at the connection level.
        self._conn.execute("PRAGMA foreign_keys = ON;")
        apply_migrations(self._conn)
```

**Note on `PRAGMA foreign_keys = ON`:** SQLite does not
enforce declared FOREIGN KEY constraints unless the pragma
is on per-connection. W11's repository turns it on so that
attempting to register an account-at-book with a missing
`account_id` or `book_id` actually surfaces as an
`IntegrityError` rather than silently succeeding. The
`bets.py` repository does **not** currently set this
pragma; the divergence is intentional — W11's tighter FK
discipline is the right v3-day-0 stance for the new
reference layer.

**Methods to ship:**

*Accounts:*

- `create_account(row: AccountRow) -> None` — insert row;
  raises on PK collision (`sqlite3.IntegrityError`).
- `get_account(account_id: str) -> AccountRow | None` —
  return row or None.
- `list_active_accounts() -> list[AccountRow]` — return all
  rows with `active = 1`, ordered by `created_at`.
- `archive_account(account_id: str) -> bool` — set
  `active = 0`; return True on success, False if account_id
  not found.

*Books:*

- `register_book(row: BookRow) -> None` — insert row;
  raises on PK collision.
- `get_book(book_id: str) -> BookRow | None`.
- `list_active_books() -> list[BookRow]` — ordered by
  `name`.
- `archive_book(book_id: str) -> bool` — set `active = 0`.

*Accounts-at-book:*

- `register_account_at_book(row: AccountAtBookRow) ->
  RegisterResult` — insert row; on composite-key
  uniqueness violation, returns
  `RegisterResult(success=False,
  reason="ACCOUNT_ALREADY_REGISTERED_AT_BOOK")`. On FK
  violation (missing `account_id` or `book_id`), returns
  `RegisterResult(success=False,
  reason="MISSING_REFERENT")`. Programmer errors (e.g.
  passing a non-`AccountAtBookRow`) raise normally.
- `get_account_at_book(account_at_book_id: str) ->
  AccountAtBookRow | None`.
- `get_account_at_book_by_composite_key(account_id: str,
  book_id: str) -> AccountAtBookRow | None` — returns the
  registration if it exists (active or not); caller filters
  if needed.
- `list_active_accounts_at_book_for_account(account_id:
  str) -> list[AccountAtBookRow]`.
- `list_active_accounts_at_book_for_book(book_id: str) ->
  list[AccountAtBookRow]`.
- `close_account_at_book(account_at_book_id: str) -> bool`
  — set `active = 0`.

**No batch / bulk methods in W11 v1.** Per-record CRUD
only. Future briefs can add batch helpers when callers
need them.

**No transaction-management methods.** v3-day-0 pattern is
auto-commit per statement at the SQLite layer; explicit
transaction wrappers come later if needed. (Matches
`bets.py` precedent.)

### §5.4 — Books seeding (substrate decision, not code)

W11 v1 does **not** ship books-list seeding (a populated
`books` table with rows for Sportsbet, Ladbrokes,
PointsBet, etc.). Seeding is a separate concern from
schema construction; the operator's actual books-of-record
list lives outside this brief.

**Reason:** the brief is a Code-bound spec for building the
data layer. Seeding the canonical books list is an
operator-driven decision (which books are in scope, what
their IDs / display names / ownership clusters / platforms
are). Encoding that list into `store/schema/accounts.py`
ties operator-data to schema-code, the wrong coupling for
v3-day-0.

**What W11 v1 delivers instead:**

- Tests that exercise the repository with synthetic
  fixture data (a small fixture set of accounts and books
  used for round-trip tests; see §5.5). Fixture data does
  not become production seed data.
- The repository surface (`register_book`) that whatever
  seeding mechanism eventually lands (operator-managed via
  UI; separate ops script; static YAML; whatever) will
  call into.

**Out of scope for W11:** the actual seeding mechanism and
the operator-curated books list. That is a later brief —
likely folded into the W17 racing-pages work or a separate
ops brief, operator's call when the time comes.

### §5.5 — Tests

Two new test files matching the existing v3 test pattern
(see `tests/store/test_bets_*.py` for the precedent —
fixture handling, `tmp_path` usage, conftest scope).

**`tests/store/test_accounts_schema.py` — schema-level
tests:**

- `test_apply_migrations_creates_all_three_tables` — call
  `apply_migrations` on a fresh in-memory connection;
  assert the three tables appear in `sqlite_master`.
- `test_apply_migrations_creates_indexes` — assert the two
  partial indexes appear in `sqlite_master` (type =
  'index').
- `test_apply_migrations_is_idempotent` — call
  `apply_migrations` three times on the same connection;
  no errors, table / index set unchanged.
- `test_apply_migrations_handles_pre_created_tables` —
  pre-create tables manually, then call
  `apply_migrations`; confirm `CREATE TABLE IF NOT EXISTS`
  doesn't raise and existing data survives.
- `test_composite_unique_constraint_on_accounts_at_book` —
  insert two `accounts_at_book` rows with the same
  `(account_id, book_id)`; assert `sqlite3.IntegrityError`.

**`tests/store/test_accounts_repository.py` — repository
CRUD tests:**

Cover round-trip for each entity:

*Accounts:*

- `test_create_get_account` — round-trip a single row.
- `test_create_account_duplicate_pk_raises` —
  `sqlite3.IntegrityError` on PK collision.
- `test_list_active_accounts` — multiple rows, active +
  inactive mix.
- `test_list_active_accounts_excludes_archived`.
- `test_archive_account`.
- `test_archive_account_not_found_returns_false`.

*Books:*

- `test_register_get_book`.
- `test_register_book_duplicate_pk_raises`.
- `test_list_active_books`.
- `test_archive_book`.

*Accounts-at-book:*

- `test_register_account_at_book` — happy path.
- `test_register_account_at_book_duplicate_composite_returns_structured_error`
  — assert
  `RegisterResult(success=False,
  reason="ACCOUNT_ALREADY_REGISTERED_AT_BOOK")`.
- `test_register_account_at_book_missing_referent_returns_structured_error`
  — assert `MISSING_REFERENT` on a row with a non-existent
  `account_id` or `book_id`.
- `test_get_account_at_book_by_composite_key`.
- `test_list_active_accounts_at_book_for_account`.
- `test_list_active_accounts_at_book_for_book`.
- `test_close_account_at_book`.

**Approximate test count:** ~22 new tests. Pytest baseline
should move from 527 to ~549. Report the exact count.

**Fixture data:** minimal — two synthetic accounts (one
self, one custodian), two synthetic books, two or three
synthetic registrations. Fixture data is local to each
test file's `conftest.py` or in-test setup, not a shared
global fixture.

---

## §6 — Sequencing within session

Recommended order:

1. **Schema first** (`store/schema/accounts.py`) — the
   foundational artefact; everything else references the
   shapes it locks.
2. **Repository** (`store/repositories/accounts.py`) —
   second. Row dataclasses + the repository class.
3. **Domain models** (`domain/accounts/__init__.py`) —
   third. (Could equally be first; domain models don't
   depend on schema. Placing third is purely
   convenience.)
4. **Tests** (both test files) — fourth.

Code may deviate from this order with a cleaner dependency
story; if it does, the rationale lands in the report.


---

## §7 — Empirical verification

### §7.1 — Pre-baselines (capture at session open)

Run before any edits, capture output verbatim in the report:

```
$ cd /Users/tim/Desktop/Projects/bethub-v3/
$ uv run lint-imports
$ uv run pytest -x -q
$ git status --short
```

Expected pre-state:

- `lint-imports` — **5 contracts kept, 0 broken** (W10.1
  close baseline).
- `pytest -x -q` — **`527 passed`** (W10.1 close baseline).
- `git status --short` — whatever Code finds at session open
  (unmodified working tree expected; if dirty, list the
  files in the report's pre-state section).

### §7.2 — Post-baselines (capture at session close)

After all edits land:

- `lint-imports` — **still 5 contracts kept, 0 broken**.
  W11 adds files under `domain/accounts/`,
  `store/schema/`, `store/repositories/`, `tests/store/`,
  all within existing import-graph allowances. No new
  contracts; no broken contracts.
- `pytest -x -q` — **`527 + N passed`** where N is the
  new-test count from §5.5 (expected ~22; report the exact
  number).
- `git status --short` — five new untracked files plus any
  pre-existing dirty files unchanged at the path level.

### §7.3 — File-existence check

At session close, confirm presence of:

```
/Users/tim/Desktop/Projects/bethub-v3/
  domain/accounts/__init__.py
  store/schema/accounts.py
  store/repositories/accounts.py
  tests/store/test_accounts_schema.py
  tests/store/test_accounts_repository.py
```

Plus an empty
`/Users/tim/Desktop/Projects/bethub-v3/domain/accounts/`
directory (the `__init__.py` is the only file in it for
W11 v1).

### §7.4 — Spot-check: `apply_migrations` round-trip

Manual round-trip on a fresh in-memory SQLite, ideally via
a brief Python REPL session:

```python
import sqlite3
from store.schema.accounts import apply_migrations

conn = sqlite3.connect(":memory:")
apply_migrations(conn)
rows = conn.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' ORDER BY name"
).fetchall()
assert [r[0] for r in rows] == [
    "accounts", "accounts_at_book", "books"
]
```

Result captured in the report's §7.4 section.

---

## §8 — Output spec

**Single report at:**
`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w11_accounts/w11_accounts_report.md`

**Length target:** 200–400 lines. Code's call within range;
over / under acceptable when work warrants it, flagged in
self-assessment.

**Section structure (parallel to W10 / W10.1 reports):**

1. Pre-session state (anchor file inventory; pre-baseline
   command outputs).
2. Changes made (per §5 sub-section: §5.1 schema, §5.2
   domain models, §5.3 repository, §5.5 tests).
3. Post-session state (post-baseline command outputs;
   file-existence check; spot-check result).
4. Findings / surprises (anything Code surfaced during
   execution that wasn't predicted by the brief — file
   shape choices, test coverage edge cases, dependency
   surprises).
5. Self-assessment (deviations from brief; hard-limit
   adherence; length flag).

**What the report does not contain:**

- No recommendations for W12+ scope.
- No proposals for tier / phase / isolation work.
- No edits to anything outside named anchors in §5.
- No "I noticed X could be cleaner" beyond what's strictly
  a finding affecting the W11 deliverable.

---

## §9 — Hard limits (non-negotiable)

### §9.1 — Operating principle

W11 is a single bounded Code session. Surprises become
**findings**, not blockers. Remediation routes to the next
operator-Claude session, not to mid-session escalation. If
Code finds a structural problem the brief didn't
anticipate (e.g. an existing module surface conflicts with
the proposed shape; the test pattern doesn't compose
cleanly with the new files), the finding lands in §4 of
the report and Code keeps moving.

**Verbatim from W10.1 §9.1:** *Code does not edit the
brief. Code does not commission follow-on work. Code does
not escalate mid-session for operator input. Findings land
in the report and the next operator-Claude session
triages.*

### §9.2 — Behaviour and schema preservation

W11 adds new tables and new code. It does **not** modify
any existing schema (`bets`, `bet_legs`, or any column
thereon). The `bets.account_at_book_id` column stays as
`TEXT NOT NULL` with no new `FOREIGN KEY` constraint —
adding the FK is a separate hygiene decision once the new
table is real and seeded.

No existing tests should fail. No existing modules should
be modified. No behaviour change to any shipped surface.

### §9.3 — No adjacent workstreams or findings

- **No W12 (balances)** — no `balances` table, no
  per-account-at-book balance state, no cash-flow
  event-type schema.
- **No W13 (promos)** — no `promos` / `promo_observed` /
  `free_bet_credited` schema.
- **No W14 (transactions)** — no transaction event types,
  no cash-flow plumbing.
- **No W15 (operations log)** — no append-only ops log
  schema.
- **No W4 (bet entry) modifications** — no schema changes
  to `bets`; no domain or workflow changes to bet entry.
- **No tier / phase fields on `accounts_at_book`** —
  deferred per §1.2 and §1.3.
- **No isolation infrastructure metadata** — deferred.
- **No `ownership_cluster` as a separate reference
  table** — TEXT field on `books` only.
- **No books-list seeding** — §5.4.

### §9.4 — No Alembic, no debt-fixing

W11 uses the existing v3 pre-Alembic schema pattern
(matching `store/schema/bets.py` precedent — inline DDL +
idempotent `apply_migrations`). The Alembic adoption carry
from W10.1 §9.4 still holds; W11 does not introduce
Alembic.

W11 also does not address any of the three named pieces of
DR-029 close-out debt (no migration framework, monolithic
orchestrator, no test coverage at scale). Test coverage
for the W11 deliverable itself is part of §5.5; the
broader debt is deferred.

### §9.5 — No SQLAlchemy Core migration

DR-031 names SQLAlchemy Core as the v3 ORM/query layer,
but the existing v3 bets store uses raw `sqlite3`. W11
matches the existing pattern (raw sqlite3 + frozen
dataclass row types). Migration of the store layer to
SQLAlchemy Core is a separate concern, not W11.

### §9.6 — Operational guardrails

- **No git operations.** No add, commit, stash, restore,
  reset.
- **No DB access** beyond ephemeral SQLite via `tmp_path`
  in tests.
- **No external API calls.** No Betfair API. No HTTP. No
  network.
- **No mid-session escalation.** Single end-to-end Code
  session. Report is the only artefact.
- **No edits outside named anchors in §5.** New files at
  named paths only; no modifications to any existing
  source file.
- **Adelaide local timestamps** per DR-021 throughout the
  report.

---

## §10 — What happens after Code's session

The next operator-Claude session (Session 121 or later)
triages `w11_accounts_report.md`. Triage shape:

- **Read the report** in full per the Cat 1 inventory-first
  cadence.
- **Run gate verification:** lint-imports still 5 / 0;
  pytest count = 527 + N (where N matches the report);
  file-existence as named in §7.3; spot-check as named in
  §7.4.
- **If clean** (gates pass, no material findings): close
  W11, mark `done` in `v3_build_picture.md` (one-session
  carry rule), unblock W12 (balances) as the default next
  stream.
- **If findings surface** (gates fail or material report
  findings): route per triage call — follow-up surgical
  brief, escalate to broader re-shape, or accept residual
  state with operator confirmation.

Code does not produce the next brief. The next brief is
the next operator-Claude session's work.

---

## §11 — Cross-references

- **DR-022** (vocabulary lock: account / book /
  account-at-book supersedes "persona") — primary
  governance.
- **DR-027** (two-database architecture: BetHub owns
  operational state) — placement justification.
- **DR-028** (cross-database boundary discipline) —
  context only; W11 does not cross the boundary.
- **DR-030** (v3 repo layout + import-graph rules) —
  module placement and import-graph constraints.
- **DR-031** (v3 tech stack) — Pydantic v2 for domain;
  divergence noted in §3.2 (raw sqlite3 in store layer
  rather than SQLAlchemy Core, matching existing pattern).
- **DR-032** (canonical reference layer for bet records)
  — context for why `bets.account_at_book_id` exists and
  what W11's `accounts_at_book` table closes.
- **W10 / W10.1 briefs** (`dr029/w10_storage_lift/`) —
  schema-pattern precedent.
- **W4 brief**
  (`dr029/w4_bet_entry/w4_bet_entry_brief.md`) — "build
  new" brief-shape precedent.
- **Architecture** (`architecture.md` lines 56–80) —
  reference-data entity diagram. Vocabulary drift
  between `account_holders` (legacy) and `accounts`
  (DR-022 locked) noted in §3.2; W11 uses DR-022.

---

**Brief locked Session 120, 2026-05-11 20:15 ACST.**
