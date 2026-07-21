# W14.1 cash flow store adapter — report

**Session:** 128 follow-on, single bounded Code session.
**Session open:** 2026-05-12 15:45:18 +0930 (Adelaide local per DR-021).
**Session close:** 2026-05-12 15:56:03 +0930.
**Brief:** `dr029/w14_cash_flow/w14_1_adapter_brief.md` (locked Session
128; SHA-256 prefix `21a59f1a`).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/` @ HEAD
`2329604aa80b34937a24644ea2eb18477749be85` (unchanged through session;
Code did not commit).

---

## §1 — Summary

W14.1 ships the surgical fix that closes the load-bearing W14 alignment
finding (W14 report §5.1) — domain ↔ row translation moves from
`store/repositories/cash_flow.py` to a new workflow-side adapter,
restoring DR-030's "store imports nothing in the project" lock.

Concretely:

- New file: `workflows/cash_flow/v1/cash_flow_store_adapter.py` (396
  lines) — owns the discriminated-union dispatch, JSON ↔ Pydantic
  re-hydration, and the public Pydantic-typed surface the W14
  repository previously exposed.
- Edited file: `store/repositories/cash_flow.py` (694 → 601 lines) —
  trimmed to row-only. All `domain.cash_flow` imports removed.
  Methods accept and return `CashFlowEventRow` / `PayeeRow`. Scope
  filters, ordering, pagination, the supersession LEFT JOIN, and all
  repository-level errors stay at the repository.
- Moved files: `tests/store/test_cash_flow_schema.py` →
  `tests/store/repositories/test_cash_flow_schema.py` (unchanged
  content); `tests/store/test_cash_flow_repository.py` →
  `tests/store/repositories/test_cash_flow_repository.py` (reshaped to
  row-level).
- New file: `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`
  (826 lines) — Pydantic-side behaviours that used to live in the
  W14 repository tests.
- Four new empty package-marker `__init__.py` files at
  `workflows/cash_flow/`, `workflows/cash_flow/v1/`,
  `tests/workflows/cash_flow/`, `tests/workflows/cash_flow/v1/`.

Verification posture at session close:

- **`lint-imports`:** **5 kept / 0 broken.** The load-bearing gate
  W14.1 exists to fix is clean.
- **pytest tests/:** 624 passed (was 596 pre-baseline; net +28 from
  the 27 row-level repository tests + 38 adapter tests minus the 37
  W14 repository tests that relocated and reshaped).
- **pytest tests/store/repositories/test_cash_flow_*.py:** 37 passed
  (10 schema, unchanged; 27 reshaped row-level repository).
- **pytest tests/workflows/cash_flow/v1/:** 38 passed (adapter).
- **mypy** on `workflows/cash_flow` plus `store/repositories/cash_flow.py`:
  `Success: no issues found in 4 source files`.
- **ruff check** on all touched files: `All checks passed!` (one
  in-flight `I001` import-ordering issue caught and auto-fixed mid-
  session; see §4.4).
- **§7.4 smoke script** round-tripped all 8 event types through the
  adapter, walked a 2-event supersession chain, confirmed
  `latest_non_superseded_by_scope` excludes the superseded event.

Line counts per file:

| File | Lines | Brief target (§7.3) |
| --- | --- | --- |
| `workflows/cash_flow/__init__.py` | 0 | empty marker |
| `workflows/cash_flow/v1/__init__.py` | 0 | empty marker |
| `workflows/cash_flow/v1/cash_flow_store_adapter.py` | 396 | 350–550 |
| `tests/workflows/cash_flow/__init__.py` | 0 | empty marker |
| `tests/workflows/cash_flow/v1/__init__.py` | 0 | empty marker |
| `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py` | 826 | 450–700 |
| `store/repositories/cash_flow.py` (post-trim) | 601 | 350–500 |
| `tests/store/repositories/test_cash_flow_repository.py` (reshaped) | 582 | 400–550 |
| `tests/store/repositories/test_cash_flow_schema.py` (relocated, unchanged) | 457 | ~450 |

The adapter test file (826) and the trimmed repository (601) overshoot
the brief's rough §7.3 guides; the repository test file (582) is
within or slightly over depending on which target line you read.
§7.3 explicitly frames the ranges as "rough sanity guides, not hard
limits". Findings §5.3 names this without expanding the brief.

Three findings surfaced — see §5. None are alignment-blocking.

---

## §2 — Anchors

- **Session-start Adelaide-local (per DR-021):**
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"` →
  `2026-05-12 15:45:18 +0930`.
- **Session-close Adelaide-local:** `2026-05-12 15:56:03 +0930`.
  Elapsed ≈ 11 minutes.
- **v3 repo HEAD at session open:**
  `2329604aa80b34937a24644ea2eb18477749be85`. Code did not commit;
  this HEAD is the operator's pre-existing in-flight tip carried
  forward from W14 close.
- **Brief lock SHA-256 prefix:** `21a59f1a` (verified at session
  open; matches the brief's lock anchor).

---

## §3 — What was built

Built per the brief §6.2 sequencing — package markers first, then the
adapter + repository trim together (allowed by brief §6.2's "free to
deviate when operationally cleaner"), then test moves, then test
reshape, then the new adapter test file, then regression and gate
check. Test-as-you-go held throughout — each phase ended with a
pytest run for the surface that phase touched.

### §3.1 — Package marker files (4 × empty `__init__.py`)

`workflows/cash_flow/__init__.py`, `workflows/cash_flow/v1/__init__.py`,
`tests/workflows/cash_flow/__init__.py`,
`tests/workflows/cash_flow/v1/__init__.py`.

All empty. Matches the shipped v3 precedent (`workflows/__init__.py`,
`workflows/bet_entry/__init__.py`, the test-side equivalents — all
empty; only the v1 package's own `__init__.py` carries content, and
even there only the `bet_entry` v1 `__init__.py` re-exports the
package's public surface).

### §3.2 — `workflows/cash_flow/v1/cash_flow_store_adapter.py` (396 lines)

The new adapter owns every Pydantic ↔ row translation the W14
repository was doing. Top-level shape:

- `CashFlowStoreAdapter` class with `__init__(conn: sqlite3.Connection)`.
  Both `CashFlowEventRepository` and `PayeeRepository` are
  instantiated with the same connection; the W14 repository pattern
  (PRAGMA `foreign_keys = ON`, `apply_migrations` invoked on init) is
  preserved — both repositories invoke `apply_migrations` on the
  shared connection (idempotent; the second call is a no-op).
- Event write surface: `append_event(event: CashFlowEventBase) -> UUID`
  — serialises via `_event_to_row` and delegates to
  `self._events.append_row`; returns `event.event_id` directly to
  preserve the brief-spec'd `UUID` return type.
- Event read surface: `get_event`, `list_by_account_at_book`,
  `list_by_account`, `list_by_book`, `list_by_event_type`,
  `list_by_correlation_id` — each delegates to the repository's
  `list_rows_by_*` counterpart and translates row → Pydantic via
  `_row_to_event`.
- Supersession-aware reads: `latest_non_superseded_by_scope` and
  `walk_supersession_chain` — delegate to the row-level repository
  methods; `InvalidScopeError`, `EventNotFoundError`, and
  `SupersessionCycleError` propagate unchanged.
- Payee write surface: `create_payee` (returns
  `payee.payee_id`), `update_payee` (adapter computes
  Adelaide-local now via `datetime.now(ZoneInfo("Australia/Adelaide"))`
  if caller did not supply an `updated_at`).
- Payee read surface: `get_payee`, `list_payees` — translate row →
  Pydantic.
- Module-level helpers `_row_to_event` / `_event_to_row` /
  `_row_to_payee` / `_payee_to_row` carry the translation logic.
  `_row_to_event` uses
  `PAYLOAD_BY_EVENT_TYPE[event_type].model_validate_json(row.payload)`
  with the same `typing.cast` workaround W14 used (the runtime type
  IS the right subclass; mypy can't narrow through the dispatch
  table).
- No errors defined at the adapter layer. Repository errors are
  canonical; the adapter is a thin translation surface. Pydantic
  `ValidationError` raises naturally on bad input.

### §3.3 — `store/repositories/cash_flow.py` (601 lines, was 694)

Trimmed to row-only per brief §5.2. Removed:

- All `from domain.cash_flow import (...)` lines (the entire
  domain-import block from the W14 repository).
- `typing.cast` import (no longer needed; cast moved to adapter).
- The `_row_to_event` / `_row_to_payee` Pydantic conversion helpers
  (moved to adapter).
- The `_PAYLOAD_BY_EVENT_TYPE` dispatch reference at the repository
  level (the dispatch table itself remains in `domain.cash_flow`; the
  adapter imports it now).

Kept (unchanged):

- `CashFlowEventRow`, `PayeeRow` dataclasses.
- All eight error classes (`CashFlowEventError`,
  `DuplicateEventError`, `EventNotFoundError`,
  `SupersessionCycleError`, `InvalidScopeError`, `PayeeError`,
  `DuplicateEntityError`, `EntityNotFoundError`).

Changed (renamed + retyped to row-level):

- `CashFlowEventRepository.__init__(db_path)` →
  `__init__(conn: sqlite3.Connection)`. The caller now owns the
  connection lifecycle (the adapter passes a connection in). PRAGMA
  `foreign_keys = ON` and `apply_migrations` still fire on init
  (idempotent). `close()` removed — the connection is the caller's,
  not the repository's. **This is a divergence from the shipped W14
  init pattern surfaced as finding §5.1.**
- `append_event(event: CashFlowEventBase) -> UUID` →
  `append_row(row: CashFlowEventRow) -> str` (returns
  `row.event_id`).
- `get_event(event_id: UUID) -> CashFlowEventBase` →
  `get_row(event_id: object) -> CashFlowEventRow`. The `object` type
  on the argument is deliberate — see finding §5.2.
- `list_by_X` → `list_rows_by_X` for all five list methods, each
  returning `list[CashFlowEventRow]`.
- `latest_non_superseded_by_scope` →
  `latest_non_superseded_rows_by_scope`. `InvalidScopeError` on
  all-None scope unchanged.
- `walk_supersession_chain` → `walk_supersession_chain_rows`.
  Returns `list[CashFlowEventRow]`. Cycle detection logic and
  `SupersessionCycleError` unchanged.

Same shape for `PayeeRepository`:

- `__init__(conn)`, no `close()`.
- `create_payee(Payee)` → `create_row(PayeeRow)`.
- `get_payee(payee_id)` → `get_row(payee_id)`.
- `update_payee` → `update_row(payee_id, *, name=None, category=None,
  notes=None, updated_at: str)`. `updated_at` is now an ISO string
  (adapter computes the `datetime` if its caller did not supply one,
  passes the ISO form to the repository).
- `list_payees` → `list_rows(category: str | None = None)`.

One new module-level helper, `_event_type_value(event_type: object) ->
str`, normalises either an enum or a string at the repository
boundary without forcing a `domain.cash_flow` import. Direct
row-level callers (e.g. the row-level repository tests) pass strings;
the adapter passes enums.

### §3.4 — `tests/store/repositories/test_cash_flow_schema.py` (457 lines, relocated, unchanged)

The W14 schema test file moved from `tests/store/test_cash_flow_schema.py`
to `tests/store/repositories/test_cash_flow_schema.py`. Content
unchanged — 10 tests covering table / index creation, idempotency,
CHECK enforcement, FK enforcement against W11 tables, and the two
self-referential FK tests for `parent_event_id` and
`supersedes_event_id`. All 10 pass at the new path on first run.

### §3.5 — `tests/store/repositories/test_cash_flow_repository.py` (582 lines, reshaped)

The W14 repository test file moved from
`tests/store/test_cash_flow_repository.py` to
`tests/store/repositories/test_cash_flow_repository.py` and reshaped
to row-level per brief §5.3. 27 tests:

- **Append (3 tests + 8 parametrised):** `test_append_row_returns_event_id`,
  `test_append_duplicate_event_id_raises`, parametrised
  `test_append_each_event_type_row_round_trips` (one per
  `CashFlowEventType` value) — asserts full row equality after
  append → get round-trip, including JSON `payload` string.
- **Read (1 test):** `test_get_row_not_found_raises`.
- **FK enforcement (1 test):** `test_fk_violation_against_w11_tables_raises`
  — append a row with a ghost `account_id` → expect
  `CashFlowEventError` wrapping the SQLite `IntegrityError`.
- **List reads (6 tests):** pagination, event_type filter,
  correlation_id-cycle reconstruction, event_type scan, book scope,
  account scope.
- **Supersession (4 tests):** latest-non-superseded excludes
  superseded, chain walk produces correct earliest-first ordering,
  cycle detection raises `SupersessionCycleError` (forged via raw
  SQL on the shared connection), `InvalidScopeError` on all-None
  scope.
- **Payee row-level CRUD (5 tests):** create+get row round-trip,
  duplicate row raises `DuplicateEntityError`, not-found raises
  `EntityNotFoundError`, partial-field update semantics, list by
  category.

Per-event-type FK rule tests, Adelaide-tz validation, the
discriminated-union Pydantic round-trip — all those move to the
adapter test file per brief §5.3.

### §3.6 — `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py` (826 lines)

38 tests covering adapter-level Pydantic behaviour:

- **Append / round-trip via adapter (1 + 8 parametrised):**
  `test_append_event_via_adapter_returns_event_id` plus parametrised
  `test_append_event_via_adapter_round_trips` (one per
  `CashFlowEventType` value, asserts payload subclass identity via
  `type(fetched.payload) is type(event.payload)`).
- **FK rules per event type (8 tests):**
  `test_fk_rules_account_holder_funding` through
  `test_fk_rules_profit_share_distribution` — each constructs a
  valid event and one or more invalid combinations, asserts
  `ValidationError` on the invalid cases.
- **Adelaide tz validation (3 tests):** naive rejected, UTC rejected,
  ACDT `+10:30` accepted.
- **Pydantic-returning read paths (7 tests):** `test_get_event_returns_pydantic_model`,
  `test_get_event_not_found_raises_via_adapter`, list-by-account-at-book,
  list-by-account, list-by-book, list-by-event-type, list-by-correlation-id.
- **Supersession via adapter (4 tests):** latest-non-superseded
  excludes superseded; chain walk returns Pydantic models
  earliest-first; `InvalidScopeError` propagates; `SupersessionCycleError`
  propagates from forged corruption.
- **Payees via adapter (7 tests):** create+get round-trip, get
  returns Pydantic, not-found raises `EntityNotFoundError`,
  `update_payee` advances `updated_at` and preserves
  unchanged fields, partial-field semantics
  (`category`-only update preserves `name` / `notes`), the
  adapter computes Adelaide-local `updated_at` when caller does not
  supply one, list-by-category.

Helper `_build_event(event_type, **overrides)` ports forward in shape
from the W14 repository tests; `_common(event_type, payload,
**overrides)` provides the FK-rule-test scaffold matching the W14
form.

### §3.7 — Files NOT touched (deliberately per brief §1.2 / §9.2)

- `domain/cash_flow/__init__.py` — read-only. Re-confirmed at
  session open: every artefact the adapter imports
  (`PAYLOAD_BY_EVENT_TYPE`, `CashFlowEventBase`,
  `CashFlowEventPayload`, `CashFlowEventSource`,
  `CashFlowEventType`, `ExternalPaymentCategory`, `Payee`) is
  present and unchanged.
- `store/schema/cash_flow.py` — read-only.
- `store/__init__.py` — read-only. 42 lines pre/post, no diff
  attributable to W14.1.

---

## §4 — Verification results

### §4.1 — Full pytest run (post-baselines)

`uv run pytest tests/ -q`:

```
============================= 624 passed in 1.99s ==============================
```

Pre-baseline at session open was 596 passed. Delta +28 = 38 new
adapter tests + 27 reshaped row-level repository tests + 10
relocated schema tests − 47 W14 tests that moved (10 schema +
37 repository). Net: 75 cash-flow tests across schema (10),
row-level repository (27), and adapter (38), up from 47 at W14
close.

### §4.2 — pytest on the touched suites (verbose)

`uv run pytest tests/store/repositories/test_cash_flow_*.py
tests/workflows/cash_flow/v1/ -v`:

```
tests/store/repositories/test_cash_flow_schema.py::
    test_apply_migrations_creates_tables PASSED
    test_apply_migrations_creates_indexes PASSED
    test_apply_migrations_idempotent PASSED
    test_event_type_check_constraint PASSED
    test_source_check_constraint PASSED
    test_payee_category_check_constraint PASSED
    test_fk_constraints_to_accounts_w11_tables PASSED
    test_fk_to_accounts_resolves_when_referent_seeded PASSED
    test_self_referential_fk_parent_event PASSED
    test_self_referential_fk_supersedes_event PASSED

tests/store/repositories/test_cash_flow_repository.py::
    test_append_row_returns_event_id PASSED
    test_append_duplicate_event_id_raises PASSED
    test_append_each_event_type_row_round_trips[account_holder_funding] PASSED
    test_append_each_event_type_row_round_trips[account_at_book_deposit] PASSED
    test_append_each_event_type_row_round_trips[account_at_book_withdrawal] PASSED
    test_append_each_event_type_row_round_trips[account_holder_remittance] PASSED
    test_append_each_event_type_row_round_trips[account_at_book_balance_adjustment] PASSED
    test_append_each_event_type_row_round_trips[account_holder_balance_adjustment] PASSED
    test_append_each_event_type_row_round_trips[external_payment] PASSED
    test_append_each_event_type_row_round_trips[profit_share_distribution] PASSED
    test_get_row_not_found_raises PASSED
    test_fk_violation_against_w11_tables_raises PASSED
    test_list_rows_by_account_at_book_paginates PASSED
    test_list_rows_by_account_at_book_filters_by_event_type PASSED
    test_list_rows_by_correlation_id_returns_full_cycle PASSED
    test_list_rows_by_event_type_scans_table PASSED
    test_list_rows_by_book PASSED
    test_list_rows_by_account PASSED
    test_latest_non_superseded_rows_excludes_superseded PASSED
    test_walk_supersession_chain_rows PASSED
    test_supersession_cycle_detected_at_row_level PASSED
    test_latest_non_superseded_requires_scope PASSED
    test_create_row_get_row_round_trip PASSED
    test_create_duplicate_row_raises_duplicate_entity_error PASSED
    test_get_row_payee_not_found_raises PASSED
    test_update_row_partial_fields PASSED
    test_list_rows_by_category PASSED

tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py::
    test_append_event_via_adapter_returns_event_id PASSED
    test_append_event_via_adapter_round_trips[account_holder_funding] PASSED
    test_append_event_via_adapter_round_trips[account_at_book_deposit] PASSED
    test_append_event_via_adapter_round_trips[account_at_book_withdrawal] PASSED
    test_append_event_via_adapter_round_trips[account_holder_remittance] PASSED
    test_append_event_via_adapter_round_trips[account_at_book_balance_adjustment] PASSED
    test_append_event_via_adapter_round_trips[account_holder_balance_adjustment] PASSED
    test_append_event_via_adapter_round_trips[external_payment] PASSED
    test_append_event_via_adapter_round_trips[profit_share_distribution] PASSED
    test_fk_rules_account_holder_funding PASSED
    test_fk_rules_account_at_book_deposit PASSED
    test_fk_rules_account_at_book_withdrawal PASSED
    test_fk_rules_account_holder_remittance PASSED
    test_fk_rules_account_at_book_balance_adjustment PASSED
    test_fk_rules_account_holder_balance_adjustment PASSED
    test_fk_rules_external_payment PASSED
    test_fk_rules_profit_share_distribution PASSED
    test_naive_datetime_rejected PASSED
    test_non_adelaide_tz_rejected PASSED
    test_acdt_daylight_saving_accepted PASSED
    test_get_event_returns_pydantic_model PASSED
    test_get_event_not_found_raises_via_adapter PASSED
    test_list_by_account_at_book_returns_pydantic_models PASSED
    test_list_by_account_returns_pydantic_models PASSED
    test_list_by_book_returns_pydantic_models PASSED
    test_list_by_event_type_returns_pydantic_models PASSED
    test_list_by_correlation_id_returns_full_cycle_in_pydantic PASSED
    test_latest_non_superseded_via_adapter_excludes_superseded PASSED
    test_walk_supersession_chain_returns_pydantic_models PASSED
    test_invalid_scope_raises_via_adapter PASSED
    test_supersession_cycle_raises_via_adapter PASSED
    test_create_payee_via_adapter_round_trips PASSED
    test_get_payee_returns_pydantic PASSED
    test_get_payee_not_found_raises_via_adapter PASSED
    test_update_payee_advances_updated_at PASSED
    test_update_payee_partial_field_semantics PASSED
    test_update_payee_computes_adelaide_local_if_not_supplied PASSED
    test_list_payees_filters_by_category PASSED

============================== 75 passed in 0.40s ==============================
```

### §4.3 — lint-imports (the load-bearing gate)

`uv run lint-imports`:

```
DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT

Contracts: 5 kept, 0 broken.
```

Pre-baseline at session open: 3 kept, 2 broken (the two W14
`store.repositories.cash_flow -> domain.cash_flow` contracts).
Post-W14.1: **5 kept, 0 broken.** The gate W14.1 was commissioned to
fix is clean. DR-030 holds.

### §4.4 — mypy and ruff

`uv run mypy workflows/cash_flow store/repositories/cash_flow.py`:

```
Success: no issues found in 4 source files
```

`uv run ruff check workflows/cash_flow store/repositories/cash_flow.py
tests/store/repositories/test_cash_flow_repository.py
tests/store/repositories/test_cash_flow_schema.py
tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`:

```
All checks passed!
```

One in-flight ruff issue (`I001 — import block is un-sorted or
un-formatted`) caught and auto-fixed on the adapter file with
`uv run ruff check --fix`. The fix was purely import-block ordering;
post-fix the full test suite still passed 624 / 624.

### §4.5 — File-existence and content checks (§7.3)

```
$ ls workflows/cash_flow/v1/
__init__.py        cash_flow_store_adapter.py    __pycache__

$ ls tests/workflows/cash_flow/v1/
__init__.py        test_cash_flow_store_adapter.py    __pycache__

$ ls tests/store/repositories/
__init__.py                       test_bets.py
test_accounts_repository.py       test_cash_flow_repository.py
test_accounts_schema.py           test_cash_flow_schema.py

$ ls tests/store/
__init__.py    __pycache__    repositories/
```

The W11 / bets-tests layout is now matched exactly:
`tests/store/repositories/` holds the five
`test_{accounts,bets,cash_flow}_*.py` files at one level; no stray
W14 test files at `tests/store/` root.

`grep "from domain" store/repositories/cash_flow.py` → 0 matches
(empirical confirmation that DR-030 is restored beyond the
`lint-imports` gate).

`grep "from store.repositories.cash_flow"
workflows/cash_flow/v1/cash_flow_store_adapter.py` → 1 match
(confirms the adapter reaches the repository correctly).

`ls tests/store/test_cash_flow_*.py` → `No such file or directory`
(confirms the originals are gone from the old location).

### §4.6 — §7.4 smoke script result

Script at `/tmp/w14_1_smoke.py` (per Cat 3 REPL discipline —
multi-line Python via `tempfile` + `python3` subprocess invocation
through the bash tool, not interactive paste). Output:

```
W14.1 adapter: 8/8 event types round-trip OK; supersession-chain walk OK;
latest-non-superseded read OK.
```

The script opens a `tempfile.NamedTemporaryFile`-backed SQLite
connection, applies W11 migrations, seeds an account / book /
account-at-book, constructs `CashFlowStoreAdapter(conn)`, appends one
event of each of the eight event types, calls
`list_by_account_at_book` (3 events) and `list_by_account` (7 events
— external_payment excluded because it carries no FK), appends a
supersedes event for the book-balance adjustment, calls
`latest_non_superseded_by_scope(account_at_book_id=..., event_type=
ACCOUNT_AT_BOOK_BALANCE_ADJUSTMENT)` and asserts the original is
excluded, calls `walk_supersession_chain` and asserts the chain is
[original, successor] in `CashFlowEventBase` Pydantic form. All
assertions hold.

---

## §5 — Findings

### §5.1 — (a) Spec ambiguity — brief assumed W14 `__init__(conn)` but ship was `__init__(db_path)`

**The minor spec divergence I bridged in flight, not as a halt.**

The W14.1 brief §5.1 specifies the adapter constructor as:

```python
class CashFlowStoreAdapter:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._events = CashFlowEventRepository(conn)
        self._payees = PayeeRepository(conn)
```

with the parenthetical "(W14 repository pattern)" claiming this
matches what W14 shipped. **It does not.** The shipped W14
`CashFlowEventRepository.__init__` (and `PayeeRepository.__init__`)
takes a `db_path: str | Path` and opens its own connection — matching
the W11 `SQLiteAccountsStorage` precedent the W14 brief explicitly
named as the constructor template.

Brief §6.1 alignment check item 1 ("W14 repository present and shape
matches") names only the methods in §5.2 to verify, and those match.
The constructor signature is not in §5.2's explicit list. So the
strict-§6.1 check passed, but the brief-vs-substrate inconsistency
needed a bridge to make the adapter work as written.

**My call:** changed both repositories' `__init__` to take a
`sqlite3.Connection`, matching the brief's adapter sample. The
caller (adapter or test fixture) now owns the connection lifecycle.
The `close()` method on both repositories went away with this
change — the connection isn't theirs to close.

This is technically outside §5.2's named scope (which lists method
changes, not constructor changes), but it is required by §5.1's
adapter sample code. Rejecting it would have either forced the
adapter to deviate from the brief's sample (taking a `db_path` and
opening its own connection — but then the two repositories would have
to open separate connections, breaking the "share one connection"
guarantee §5.1 calls out) or pushed the inconsistency back to triage
as a halt-finding.

The brief's §1.3 lists three Cat 5 software calls for visibility; the
unstated implicit call is "the adapter sample's `(conn)` shape
overrides §5.2's silence on the constructor". I surfaced as Cat 5 to
match the brief's pattern.

Triage signal: was the brief author aware of the discrepancy? If yes,
the constructor change was implicitly authorised. If no, the next
operator-Claude session may want to re-confirm the call.

### §5.2 — (c) Integration surprise — `object`-typed repository surface

The trimmed repository's row-level methods take `event_id: object`,
`account_at_book_id: object`, `event_type: object | None`, etc., not
`UUID` and `CashFlowEventType`. The reason: those types live in
`domain.cash_flow`, and after the trim `store/` is forbidden to
import from `domain/` per DR-030 (this is the exact contract W14.1
exists to restore).

Two practical approaches and the one I picked:

1. **Type with `str`** — strict row-level repository, callers convert
   UUIDs to strings before calling. Awkward for the adapter, which
   has UUIDs in hand and is now forced to `str()`-cast every call.
2. **Type with `object`** + accept anything `str()` renders — the
   adapter passes UUIDs directly, the row-level repository handles
   the conversion at its boundary. Row-level repository tests pass
   strings directly. Wider type erasure at the public surface; the
   trade is no boilerplate at the adapter / test sites.

I picked (2) for the IDs (`event_id`, `account_*`, etc.) and added a
small `_event_type_value` helper that accepts either a string or a
`.value`-carrying object (i.e., a `CashFlowEventType` enum, but the
helper does not name the enum type — it duck-types on `.value`). This
keeps the repository free of any `domain.cash_flow` import while
letting the adapter pass enums naturally.

The downside is loss of static type narrowness at the repository's
public surface. mypy and ruff are clean, but a caller passing
something silly (e.g. an int) would only fail at runtime with a
SQLite error.

Surfacing for the next session because W13 (`promo_events`) and W15
(`ops_events`) will face the same row-repository-vs-domain-types
question. Three plausible next-session decisions:

- **Accept as-is** — keep the `object`-typed row repository surface;
  document the pattern in the W13 / W15 briefs.
- **Tighten to `str`** — bear the adapter-side cast cost; gain static
  type safety at the row level.
- **Introduce a `store.types` module** with primitives like a
  `UuidStr` `NewType` or alias that lives in `store/` and avoids the
  `domain/` import — but then UUIDs everywhere look at the row level
  is a bigger refactor than W14.1 was scoped for.

Per §9.1 I do not propose; surfacing for operator-Claude triage.

### §5.3 — (b) Deferred concern — file size overrun against §7.3 guides

Three of the new / edited files run over the §7.3 ballpark guides:

- `workflows/cash_flow/v1/cash_flow_store_adapter.py`: 396 vs 350–550
  (in range).
- `store/repositories/cash_flow.py`: 601 vs 350–500 (~20% over).
- `tests/store/repositories/test_cash_flow_repository.py`: 582 vs
  400–550 (~6% over the top end).
- `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`:
  826 vs 450–700 (~18% over the top end).

§7.3 explicitly frames the ranges as "rough guides — not hard limits".
The overruns come from: each new / reshaped file carrying its own
module docstring matching the W14 docstring length (each is the file's
DR / W14 / W14.1 reference docstring); the parametrised + per-event-
type tests blowing up linear test count.

The trimmed repository (601 vs 350–500 target) is the one that
landed least-trimmed — W14 shipped at 694, the trim moved ~85 lines
of Pydantic-side code, and the resulting 601-line file is the
arithmetic outcome of that move. The added `_event_type_value`
helper and slightly more verbose docstring explaining the trim
account for the rest. Could have been trimmed further by removing
inline docstrings on every method, but that would have
operator-readability cost at fewer lines.

Not a structural concern per §7.3's framing. Surfacing because it's
a measurable deviation.

### §5.4 — (d) Tests that pass for the wrong reason — none identified

Reviewed the same way the W14 report §5.9 reviewed:

- `test_supersession_cycle_detected_at_row_level` (and the adapter
  equivalent) forges corruption via raw SQL `UPDATE` on the shared
  connection; verified that the test depends on
  `SupersessionCycleError` actually being raised by the row-level
  chain walk, not on side effects of the `UPDATE`.
- `test_append_each_event_type_round_trips` (row-level, 8
  parametrised) asserts full `CashFlowEventRow` equality after
  append → get. Row equality includes the JSON `payload` string, so
  this catches payload corruption regressions cleanly.
- `test_append_event_via_adapter_round_trips` (adapter, 8
  parametrised) asserts `type(fetched.payload) is type(event.payload)`
  plus `fetched.payload == event.payload`. The `type(...)` check is
  load-bearing — without it the discriminated-union could resolve
  to the first matching shape and pass field-equality alone.
- The FK-rules-per-event-type tests at the adapter level use both
  "valid case constructs successfully" and "invalid case raises
  `ValidationError`" branches.
- The `update_payee_partial_field_semantics` test (adapter-side)
  explicitly verifies that `name` and `notes` survive a
  category-only update; this is the partial-update assertion the
  W14 test had but reframed for the new adapter signature.
- The new `update_payee_computes_adelaide_local_if_not_supplied`
  test asserts the adapter computes Adelaide-local now when caller
  omits `updated_at`. The assertion checks `utcoffset()` ∈ {+9:30,
  +10:30} AND matches what `datetime.now(ZoneInfo("Australia/Adelaide"))`
  would produce at test time. This is robust against test running
  in either standard or daylight time.

### §5.5 — (e) Other — `store/__init__.py` did not need to be touched

Brief §1.2 lists `store/__init__.py` under "What this brief is not"
because the W14 additive edit already shipped at the alphabetically
correct positions per W14 brief §5.4. Verified at session open and
close: 42 lines, unchanged. The `git diff` against the empty index
shows `@@ -0,0 +1,42 @@` (the same artefact the W14 report §5.6
finding named — the indexed copy is empty because the in-flight
working tree hasn't been staged). Not a W14.1 concern; carrying
forward verbatim.

---

## §6 — Dirty-tree adherence statement

§9.7 discipline held end-to-end. Zero `git add`, zero `git commit`,
zero `git stash`, zero `git restore`, zero `git checkout`, zero
`git reset`, zero `git rm`, zero `git push`. The HEAD at session
close (`2329604aa80b34937a24644ea2eb18477749be85`) matches the HEAD
at session open exactly.

### §6.1 — Pre-baseline (`git -C bethub-v3 status --short` at session open)

```
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
?? contracts/betfair_client_contract.md
?? contracts/vps_client_contract.md
?? domain/accounts/
?? domain/cash_flow/
?? store/repositories/accounts.py
?? store/repositories/bets.py
?? store/repositories/cash_flow.py
?? store/schema/accounts.py
?? store/schema/bets.py
?? store/schema/cash_flow.py
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

10 modified entries, 22 untracked entries.

### §6.2 — Post-baseline (`git -C bethub-v3 status --short` at session close)

```
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
?? contracts/betfair_client_contract.md
?? contracts/vps_client_contract.md
?? domain/accounts/
?? domain/cash_flow/
?? store/repositories/accounts.py
?? store/repositories/bets.py
?? store/repositories/cash_flow.py
?? store/schema/accounts.py
?? store/schema/bets.py
?? store/schema/cash_flow.py
?? tests/clients/betfair_client/v1/test_account_funds.py
?? tests/clients/betfair_client/v1/test_current_orders.py
?? tests/clients/betfair_client/v1/test_market_catalogue.py
?? tests/store/
?? tests/ui/
?? tests/workflows/
?? ui/api/
?? ui/web/
?? workflows/bet_entry/v1/
?? workflows/cash_flow/
```

10 modified entries (unchanged), 23 untracked entries (+1).

### §6.3 — Diff: one new untracked top-level entry

Only one new `??` entry since pre-baseline:

```
?? workflows/cash_flow/
```

The new test files (the adapter test file and the relocated
schema / repository test files) and the four package marker files
do **not** show as separate `??` entries because their parent
directories (`tests/store/`, `tests/workflows/`) were already
untracked at session open and roll up under their existing
directory-level `??` entries. Same for the trimmed
`store/repositories/cash_flow.py` (the parent
`store/repositories/cash_flow.py` was already `??` at session open
per W14 close; the file is still there, content-trimmed).

The two original test files at `tests/store/test_cash_flow_*.py`
are gone from disk (verified by `ls`); they were under the
already-untracked `tests/store/` `??` entry pre-baseline, so the
deletion does not surface as a separate `??` entry change either.

### §6.4 — `store/__init__.py` not touched

The `M store/__init__.py` entry from the pre-baseline is preserved
post-session at the same `M` status, same path. 42 lines, no content
delta this session. The §5.5 finding names this — the W14 additive
edit landed at W14 close per §5.4 of the W14 brief and is intact.

### §6.5 — Discipline summary

Pre-baseline: 10 `M` + 22 `??` = 32 entries.
Post-baseline: 10 `M` (unchanged) + 23 `??` (+1) = 33 entries.

Every pre-baseline `M` entry is still `M` at post-baseline (same
path, same status). Every pre-baseline `??` entry is still `??` at
post-baseline. The one new entry is `workflows/cash_flow/` — the
brand-new W14.1 anchor that didn't exist pre-session. Per the §9.7
dirty-tree adherence requirement: **HELD.**

---

## §7 — Self-assessment

**Scope fit.** All four anchors plus the two test relocations landed
exactly as named. No work outside the named anchors; no edits to any
of the W11 / W4 / W6 / Betfair-pillar files; no edits to
`domain/cash_flow/__init__.py` or `store/schema/cash_flow.py` or
`store/__init__.py`. The one bridging change I made (the repository
constructor's `db_path` → `conn` shift, surfaced as finding §5.1) was
required by §5.1's adapter sample code; the alternative — adapter
mismatching the brief's sample — would have been a worse divergence.

**Single-bounded-session fit.** Session length ≈ 11 minutes elapsed
clock time (15:45:18 → 15:56:03 ACST). Sequenced cleanly: package
markers, adapter + repository together, schema test move, repository
test reshape, adapter test file, regression, gate. Two issues caught
mid-session via test-as-you-go:

1. The adapter's `append_event` initially returned the row's `str`
   event_id, not a `UUID`. The single failed test
   (`test_append_event_via_adapter_returns_event_id`) caught it in
   one verbose-pytest run; one-line fix to return `event.event_id`
   (which is the UUID the caller already holds).
2. The adapter's import block was `I001`-flagged by ruff. Auto-fix
   resolved it; ran full pytest after to confirm no behavioural
   regression.

Both were sub-minute fixes; neither involved scope expansion.

**Test-as-you-go held.** Phase-by-phase pytest runs caught both
in-flight issues at the right scope. The smoke script at §4.6
provided a final belt-and-braces end-to-end check that the eight
event types and the supersession flow all round-trip through the
public adapter surface in the way W14 originally exercised through
the repository.

**What I would change about the brief in retrospect.**

1. **Make the constructor change explicit in §5.2.** §5.1's adapter
   sample uses `CashFlowEventRepository(conn)`. The shipped W14
   takes `db_path`. §5.2 trim spec is silent on the constructor.
   Either §5.2 should call the constructor change out explicitly as
   part of the trim ("repositories now take a `sqlite3.Connection`,
   matching the adapter pattern; `close()` removed"), or §5.1 should
   match the shipped W14 substrate (the adapter takes a `db_path`).
   Either is fine; the silent assumption was the source of
   finding §5.1.
2. **Name the `event_type` / `id` type question at the row level.**
   Brief §5.2 names "rows in, rows out" but doesn't name the type of
   non-row arguments (the `event_id: UUID` on `get_event`, etc.).
   The post-trim repository can't accept `UUID` and
   `CashFlowEventType` directly because both live in `domain/`.
   Brief §5.3 mentions "passes scope filter arguments through to the
   repository" without naming whether the adapter unwraps enums
   first or the repository does it. I chose the `object` + helper
   path (finding §5.2); a brief amendment could lock the choice.
3. **The brief's §7.3 line-count guides may need to widen for the
   row-level + adapter split.** The W14.1 reshape produces three
   files (schema test, row-level repository test, adapter test)
   from the W14 single repository-test surface; the cumulative line
   count goes up because the helper / fixture scaffold duplicates
   across the row and adapter test files. Combined: 582 + 826 =
   1408 vs the W14 901-line single file. Some of the increase is
   structurally inherent in splitting one surface into two.

None of these would have changed what W14.1 ships; surfacing for
brief-drafting hygiene on W13 / W15 (which will face the same
row-vs-adapter split).

**Gate posture for next operator-Claude session:**

- **`lint-imports`:** 5 kept / 0 broken. ✓ — the load-bearing gate
  W14.1 was commissioned to fix is clean.
- **pytest tests/:** 624 passed. ✓
- **pytest tests/store/repositories/test_cash_flow_*.py:** 37
  passed. ✓
- **pytest tests/workflows/cash_flow/v1/:** 38 passed. ✓
- **mypy** on W14.1 source: clean. ✓
- **ruff check** on W14.1 source and tests: clean. ✓
- **§7.4 smoke:** 8/8 event types round-trip OK; supersession-chain
  walk OK; latest-non-superseded read OK. ✓
- **File-existence per §7.3:** all anchors present at expected
  paths. ✓
- **Dirty-tree adherence per §9.7:** HELD. ✓

W14.1 ships per brief §1.1 contract. Three findings (§5.1
constructor divergence — bridged; §5.2 row-level typing — design
choice for triage; §5.3 file size — informational) for triage. None
are alignment-blocking; W14 + W14.1 can transition to `done` if the
operator-Claude triage accepts the constructor bridge in §5.1.

---

**Report written 2026-05-12 15:56 ACST.**
