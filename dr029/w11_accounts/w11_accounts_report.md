# W11 accounts + account-at-book data layer — report

**Session:** 120, single bounded Code session.
**Session open:** 2026-05-11 20:15 ACST (Adelaide local per DR-021).
**Session close:** 2026-05-11 20:36 ACST.
**Brief:** `dr029/w11_accounts/w11_accounts_brief.md` (locked
2026-05-11 20:15 ACST).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`.

---

## §1 — Pre-session state

### §1.1 — Anchor file inventory

None of the W11 anchor paths existed at session open:

```
domain/accounts/                                 (absent)
store/schema/accounts.py                         (absent)
store/repositories/accounts.py                   (absent)
tests/store/test_accounts_schema.py              (absent)
tests/store/test_accounts_repository.py          (absent)
```

The `tests/store/` directory existed (with `__init__.py` and
`repositories/test_bets.py`); the `domain/`, `store/schema/`,
`store/repositories/` parent directories existed.

### §1.2 — Pre-baselines (per brief §7.1)

```
$ cd /Users/tim/Desktop/Projects/bethub-v3/
$ uv run lint-imports
Analyzed 124 files, 352 dependencies.
DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT
Contracts: 5 kept, 0 broken.

$ uv run pytest -x -q
............................... (elided) ...........................
============================= 527 passed in 1.76s ==============================

$ git status --short
 M clients/betfair_client/v1/__init__.py
 M clients/betfair_client/v1/_connection.py
 M clients/betfair_client/v1/_translation.py
 M clients/betfair_client/v1/live_pricing.py
 M clients/betfair_client/v1/streaming.py
 M domain/bets/__init__.py
 M pyproject.toml
 M store/__init__.py
 M tests/clients/betfair_client/v1/test_streaming.py
 M uv.lock
?? clients/betfair_client/v1/account_funds.py
?? clients/betfair_client/v1/current_orders.py
?? clients/betfair_client/v1/market_catalogue.py
?? store/repositories/bets.py
?? store/schema/bets.py
?? tests/clients/betfair_client/v1/test_account_funds.py
?? tests/clients/betfair_client/v1/test_current_orders.py
?? tests/clients/betfair_client/v1/test_market_catalogue.py
?? tests/store/
?? tests/ui/
?? tests/workflows/
?? ui/api/
?? ui/web/
?? workflows/bet_entry/v1/
```

Matches the W10.1 close baselines (5 contracts kept, 0 broken;
527 passed). The working tree was dirty at session open with
pre-existing modifications and untracked files — none touched by
this session.

---

## §2 — Changes made

Brief sequencing recommended schema → repository → domain → tests
(§6). Followed verbatim. Files in execution order below.

### §2.1 — `store/schema/accounts.py` (135 lines)

DDL for three tables in dependency order (`_ACCOUNTS_DDL`,
`_BOOKS_DDL`, `_ACCOUNTS_AT_BOOK_DDL`) plus two partial indexes
(`_INDEX_ACCOUNTS_AT_BOOK_BY_ACCOUNT`,
`_INDEX_ACCOUNTS_AT_BOOK_BY_BOOK`) filtered on `active = 1` per
brief §5.2. `_add_column_if_missing` helper included even though
W11 v1 calls it zero times — it lands the future-additive pattern
for tier / phase column work once those vocabularies lock.

`apply_migrations(conn)` runs the five `executescript` calls
followed by `conn.commit()` per the brief's specimen. Module-level
imports are `sqlite3` only (DR-030 — `store/schema/` is part of
`store/`, stdlib only).

The DDL bytes match the brief's specimen verbatim. The composite
`UNIQUE (account_id, book_id)` on `accounts_at_book` encodes
DR-022's "one account never holds two registrations at the same
book" rule structurally; the schema test
`test_composite_unique_constraint_on_accounts_at_book` exercises
the violation case directly.

### §2.2 — `store/repositories/accounts.py` (419 lines)

Three frozen-dataclass row types (`AccountRow`, `BookRow`,
`AccountAtBookRow`) defined at module top, plus `RegisterResult`
for the `register_account_at_book` structured-error envelope. All
shapes mirror their corresponding table columns one-for-one;
`is_self` and `active` are stored as `INTEGER` (0/1) and projected
back to `bool` in the row → dataclass helpers.

`SQLiteAccountsStorage`:

- `__init__(db_path)` opens the SQLite connection with
  `detect_types=sqlite3.PARSE_DECLTYPES`, sets
  `row_factory=sqlite3.Row`, enables FK enforcement via
  `PRAGMA foreign_keys = ON`, and invokes `apply_migrations`.
  Connection is held for the instance lifetime per brief §5.3
  (deliberate divergence from the per-call-connection pattern in
  `store/repositories/bets.py`).
- `close()` is the only addition beyond the brief's named method
  list — it lets tests release the underlying SQLite file
  cleanly. The bets-repository precedent doesn't ship `close`
  because its per-call pattern auto-closes inside each call;
  W11's held-connection pattern needs an explicit handle.

Accounts CRUD (`create_account`, `get_account`,
`list_active_accounts`, `archive_account`), books CRUD
(`register_book`, `get_book`, `list_active_books`, `archive_book`),
and accounts-at-book CRUD (`register_account_at_book`,
`get_account_at_book`, `get_account_at_book_by_composite_key`,
`list_active_accounts_at_book_for_account`,
`list_active_accounts_at_book_for_book`,
`close_account_at_book`) ship as named in the brief §5.3 method
list.

`register_account_at_book` catches `sqlite3.IntegrityError` and
dispatches to a `_classify_integrity_error` helper that inspects
the exception message:

- `"FOREIGN KEY constraint failed"` → `MISSING_REFERENT`.
- `"UNIQUE constraint failed: accounts_at_book.account_id, accounts_at_book.book_id"`
  → `ACCOUNT_ALREADY_REGISTERED_AT_BOOK`.
- Anything else (e.g. PK collision on `account_at_book_id`) →
  re-raised, matching the brief's note that PK collisions are
  treated like the `create_account` / `register_book` PK-collision
  raises.

`archive_account`, `archive_book`, and `close_account_at_book`
return `True` on a row-updated and `False` on a missing-row update
(per the cursor `rowcount` check). The brief specifies this only
for `archive_account` explicitly but the symmetry across the
archival surfaces is clearer than an asymmetric one-off.

### §2.3 — `domain/accounts/__init__.py` (114 lines)

Three Pydantic v2 models — `Account`, `Book`, `AccountAtBook` — in
the order the brief specifies. Each carries
`model_config = ConfigDict(frozen=True)` matching the existing
`domain/bets/` precedent (the brief's specimen doesn't include
this but the project pattern is consistent and frozen domain
models support equality testing in repository tests without
surprise).

Module-level imports are stdlib (`datetime`) + pydantic only.
`store/` does not import these models — the repository surface
uses its own row dataclasses per the W4 / W10 separation. Future
workflow consumers (W12 balances first) will land row ↔ domain
adapters when they need them.

The class docstrings name DR-022 / DR-021 / DR-030 / W11-brief
references for downstream readers.

### §2.4 — `tests/store/test_accounts_schema.py` (178 lines)

Five schema-level tests per brief §5.5:

- `test_apply_migrations_creates_all_three_tables` — asserts the
  three table names appear in `sqlite_master`.
- `test_apply_migrations_creates_indexes` — asserts the two
  partial-index names appear in `sqlite_master`.
- `test_apply_migrations_is_idempotent` — calls
  `apply_migrations` three times on the same connection; table /
  index sets unchanged.
- `test_apply_migrations_handles_pre_created_tables` —
  pre-creates the tables manually with seeded data, then calls
  `apply_migrations`; data survives.
- `test_composite_unique_constraint_on_accounts_at_book` —
  seeds FK referents (accounts / books), inserts one
  `accounts_at_book` row, asserts a duplicate composite raises
  `sqlite3.IntegrityError` with the expected UNIQUE-violation
  message.

Helpers (`_open_connection`, `_table_names`, `_index_names`) are
local to the file. Adelaide-local ISO8601 timestamps in seed data.

### §2.5 — `tests/store/test_accounts_repository.py` (417 lines)

Seventeen repository CRUD tests per brief §5.5:

*accounts:* `test_create_get_account`,
`test_create_account_duplicate_pk_raises`,
`test_list_active_accounts`,
`test_list_active_accounts_excludes_archived`,
`test_archive_account`,
`test_archive_account_not_found_returns_false` — 6 tests.

*books:* `test_register_get_book`,
`test_register_book_duplicate_pk_raises`,
`test_list_active_books`, `test_archive_book` — 4 tests.

*accounts-at-book:* `test_register_account_at_book`,
`test_register_account_at_book_duplicate_composite_returns_structured_error`,
`test_register_account_at_book_missing_referent_returns_structured_error`,
`test_get_account_at_book_by_composite_key`,
`test_list_active_accounts_at_book_for_account`,
`test_list_active_accounts_at_book_for_book`,
`test_close_account_at_book` — 7 tests.

The `missing_referent` test exercises both missing-account and
missing-book FK violations to confirm `MISSING_REFERENT` covers
both branches. The `duplicate_composite` test inserts a second
row with the same `(account_id, book_id)` pair but a fresh
`account_at_book_id` so the dispatcher routes through the
composite-UNIQUE branch (not the PK branch).

Fixture helpers (`_tim`, `_kate`, `_sportsbet`, `_ladbrokes`,
`_tim_at_sportsbet`, `_tim_at_ladbrokes`, `_kate_at_sportsbet`)
are local to the file. The `_seed_two_accounts_two_books` helper
seeds the FK-referent rows needed before any
`accounts_at_book` insert; the `_storage` helper returns a fresh
`SQLiteAccountsStorage` per-test backed by a `tmp_path` SQLite
file. Each test uses a try/finally to call `storage.close()`.

22 new tests total. Pytest baseline moves 527 → 549.

---

## §3 — Post-session state

### §3.1 — Post-baselines (per brief §7.2)

```
$ uv run lint-imports
Analyzed 129 files, 355 dependencies.
DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT
Contracts: 5 kept, 0 broken.

$ uv run pytest -x -q
... (elided)
============================= 549 passed in 1.49s ==============================

$ git status --short
 M clients/betfair_client/v1/__init__.py
 M clients/betfair_client/v1/_connection.py
 M clients/betfair_client/v1/_translation.py
 M clients/betfair_client/v1/live_pricing.py
 M clients/betfair_client/v1/streaming.py
 M domain/bets/__init__.py
 M pyproject.toml
 M store/__init__.py
 M tests/clients/betfair_client/v1/test_streaming.py
 M uv.lock
?? clients/betfair_client/v1/account_funds.py
?? clients/betfair_client/v1/current_orders.py
?? clients/betfair_client/v1/market_catalogue.py
?? domain/accounts/
?? store/repositories/accounts.py
?? store/repositories/bets.py
?? store/schema/accounts.py
?? store/schema/bets.py
?? tests/clients/betfair_client/v1/test_account_funds.py
?? tests/clients/betfair_client/v1/test_current_orders.py
?? tests/clients/betfair_client/v1/test_market_catalogue.py
?? tests/store/
?? tests/ui/
?? tests/workflows/
?? ui/api/
?? ui/web/
?? workflows/bet_entry/v1/
```

`lint-imports` files-count moved 124 → 129 (the five W11 files);
dependencies 352 → 355 (the three new internal imports —
schema-from-stdlib, repo-imports-schema, tests-import-repo).
Contracts: still 5 kept, 0 broken. Pytest: 527 → 549 (+22, the
exact W11 test count).

`git status --short` shows four new entries since pre-state — all
W11 anchors (`domain/accounts/`, `store/repositories/accounts.py`,
`store/schema/accounts.py`, plus the new tests folded under the
already-untracked `tests/store/` entry). Pre-existing dirty files
unchanged.

### §3.2 — File-existence check (per brief §7.3)

All five anchors present:

```
domain/accounts/__init__.py                       4044 bytes
store/schema/accounts.py                          4539 bytes
store/repositories/accounts.py                   14415 bytes
tests/store/test_accounts_schema.py               5887 bytes
tests/store/test_accounts_repository.py          12827 bytes
```

`domain/accounts/` contains only `__init__.py` per the brief's
"empty directory" instruction.

### §3.3 — Spot-check (per brief §7.4)

Manual round-trip against in-memory SQLite:

```python
$ uv run python -c "
import sqlite3
from store.schema.accounts import apply_migrations

conn = sqlite3.connect(':memory:')
apply_migrations(conn)
rows = conn.execute(
    \"SELECT name FROM sqlite_master \"
    \"WHERE type='table' ORDER BY name\"
).fetchall()
print('Tables:', [r[0] for r in rows])
assert [r[0] for r in rows] == ['accounts', 'accounts_at_book', 'books']
print('Spot-check passed.')
"
Tables: ['accounts', 'accounts_at_book', 'books']
Spot-check passed.
```

---

## §4 — Findings / surprises

### §4.1 — Brief-cited test path does not match the existing test layout

Brief §5.5 cites `tests/store/test_bets_*.py` as the test-pattern
precedent, but the actual file lives at
`tests/store/repositories/test_bets.py`. The brief also names the
W11 test paths explicitly in two places (§5.5 and §7.3 file-
existence check), both as `tests/store/test_accounts_*.py` (no
`repositories/` subdirectory).

W11 followed the brief's named paths — `tests/store/` directly,
matching §7.3's explicit file-existence list. This is a
divergence from the existing precedent's actual layout but not
from the brief.

Two future-handling options for the next operator-Claude session
to triage:

1. Treat the brief as the new canonical path and leave the W11
   tests at `tests/store/`. The bets tests remain at
   `tests/store/repositories/` indefinitely; the layout drifts
   asymmetric.
2. Move the W11 tests to `tests/store/repositories/` to match
   the bets-tests precedent. The §7.3 file-existence list in the
   brief becomes the obsolete reference and is amended in a
   follow-up.

No structural reason was visible from the brief or the existing
code to prefer one over the other; the divergence is a minor
inconsistency, not a correctness concern. Imports work from both
locations (the import-graph contract is `tests/` → anything).

### §4.2 — `executescript` vs `execute` divergence from `bets.py`

Brief §5.2 specifies `conn.executescript(_ACCOUNTS_DDL)` (five
calls) plus a final `conn.commit()` in `apply_migrations`. The
`bets.py` precedent uses `conn.execute(_BETS_DDL)` (note:
single-statement `execute`) instead.

`executescript` issues an implicit commit before executing — so
the explicit `conn.commit()` at the end of the brief's specimen
is partially redundant for the DDL/index path but not harmful. I
followed the brief's specimen verbatim. The behavioural result is
identical (tables and indexes created idempotently).

### §4.3 — `PRAGMA foreign_keys = ON` is real and tested

Brief §5.3 flags the FK-pragma divergence from `bets.py` as
intentional. The `test_register_account_at_book_missing_referent_returns_structured_error`
test exercises both missing-`account_id` and missing-`book_id`
branches; both surface as `sqlite3.IntegrityError("FOREIGN KEY
constraint failed")` and route through `_classify_integrity_error`
to `RegisterResult(success=False, reason="MISSING_REFERENT")`.

Note: `apply_migrations` is invoked inside `__init__` *after* the
pragma is enabled — but the pragma is connection-level and not
schema-level, so the connection's pragma state holds for all
subsequent queries on the same connection. If a future caller
opens its own `sqlite3.Connection` against an
accounts-tables-already-created database without enabling the
pragma, FK enforcement won't fire. The repository's contract is
that callers use `SQLiteAccountsStorage`, not the bare DB file.

### §4.4 — `_add_column_if_missing` lands but goes uncalled

W11 v1 has no additive migrations, so the helper has zero call
sites. Tested only by being reachable / parseable (no dedicated
test). Leaving it in the file is brief-specified (§5.2) and lands
the future-tier/phase pattern; the bets-schema precedent has the
same shape (W6 v1 brief).

A minor implementation note: my version uses `row[1]` (positional)
to read the column name from `PRAGMA table_info`, where `bets.py`
uses `row["name"]` (sqlite3.Row dict-access). Both work on the
project's connection-with-row-factory pattern; the positional form
also works on a raw connection with the default tuple row factory.
Not a divergence worth changing.

### §4.5 — `close` method beyond the brief's method list

Brief §5.3 lists the public methods (CRUD + register/archive) but
does not name `close`. The held-connection pattern in §5.3's
constructor specimen leaves the SQLite file handle open for the
instance lifetime — repository consumers (including tests) need a
way to release it.

I added `close()` to the repository. The alternative (relying on
GC + `__del__`) is more fragile for `tmp_path`-based tests; an
explicit `close` is the minimum-friction surface. The test
helpers wrap construction in try/finally to call it.

### §4.6 — One bug in the test file, caught and fixed before final run

A draft of `test_list_active_books` had a stray
`assert storage.archive_book("ladbrokes") is False or True` line
left over from an in-flight rewrite. The expression is operator-
precedence-degenerate (`is` binds tighter than `or`, so the whole
clause evaluates to `True` and the assert passes), but it
actually archives `ladbrokes` — breaking the subsequent ordering
assertion. Caught before the post-baseline pytest run; the
final-shipped version of the test inserts both books and asserts
the `ORDER BY name ASC` ordering without archiving either.

Mentioning the bug here rather than burying it because the
self-asserted-positive-degenerate pattern is the exact failure
mode that quiet test bugs cause (the test passes for the wrong
reason) — flagging for future test-review hygiene.

---

## §5 — Self-assessment

### §5.1 — Deviations from the brief

Three intentional deviations, all flagged in §4:

- **`close()` method on the repository** (§4.5). Beyond the
  brief's named method list but minimum-friction for held-
  connection lifecycle.
- **Symmetric `bool` return on `archive_book` and
  `close_account_at_book`** to match `archive_account`. The brief
  names the bool return only for `archive_account`; I extended to
  the symmetric archive surfaces for consistency.
- **`Pydantic ConfigDict(frozen=True)` on all three domain
  models**. Brief's specimen doesn't include it; the existing
  `domain/bets/` precedent does. Matching the project pattern.

One brief-vs-precedent divergence the brief itself created, not a
deviation:

- **Test files at `tests/store/`** instead of
  `tests/store/repositories/` (§4.1). The brief is the
  authoritative spec; followed.

### §5.2 — Hard-limit adherence (§9.1–§9.6)

- **§9.1 operating principle:** single bounded session. No
  mid-session escalation. Surprises captured as §4 findings.
- **§9.2 schema preservation:** `bets` schema unchanged. No FK
  added to `bets.account_at_book_id`. No existing test failed.
  No existing module modified.
- **§9.3 no adjacent workstreams:** no balances, no promos, no
  transactions, no ops log. No tier / phase columns on
  `accounts_at_book`. No isolation metadata. `ownership_cluster`
  stays a TEXT column on `books`, not a separate table. No
  books-list seeding.
- **§9.4 no Alembic, no debt-fixing:** raw inline DDL +
  idempotent `apply_migrations`, matching `bets.py`. No Alembic
  introduced.
- **§9.5 no SQLAlchemy Core migration:** raw `sqlite3` + frozen
  dataclass row types, matching the W4 / W10 pattern.
- **§9.6 operational guardrails:** no git ops, no DB access
  beyond `tmp_path`, no external API, no edits outside the named
  anchors. Adelaide-local timestamps in report and seed data.

### §5.3 — Length flag

This report runs ~520 lines, above the brief's 200–400 target.
The overshoot lives mostly in §2 (changes-made, per-file write-up
with the brief's per-method enumeration restated) and §3.1 (full
verbatim command outputs including the pre-existing-untracked
file list, kept verbatim because the brief §7 names verbatim
capture as the expectation).

Two tightening levers I declined: collapsing §3.1's untracked-
file list to "(unchanged from pre-state)" loses the verbatim
fidelity §7.1 / §7.2 specify; collapsing §2's method
enumeration to "matches brief §5.3 method list verbatim" loses
the structured paper-trail that the post-session triage uses to
verify gate posture against the brief without re-cross-
referencing. The overshoot is content the next operator-Claude
session will read; the alternative was synthesising it back from
the diff and the brief in flight, with worse fidelity. Calling it
flagged-and-accepted rather than re-shaping the report.

### §5.4 — Gate posture for next operator-Claude session

- `lint-imports`: 5 kept, 0 broken. ✓
- pytest: 549 passed (527 + 22). ✓
- File existence per §7.3: all five anchors present, plus the
  empty-but-for-`__init__.py` `domain/accounts/` directory. ✓
- Spot-check per §7.4: tables list matches expected. ✓
- All findings in §4 are commentary / minor; none are
  gate-breaking. The §4.1 path-divergence is the only one likely
  to recur as a real triage call.

W11 v1 is ready for the next operator-Claude session to triage
and unblock W12 (balances) per the brief §10 flow.

---

**Report written 2026-05-11 20:36 ACST.**
