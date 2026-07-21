# W14 cash flow event log + payees data layer — report

**Session:** 127, single bounded Code session.
**Session open:** 2026-05-12 12:18:07 +0930 (Adelaide local per DR-021).
**Session close:** 2026-05-12 12:30:46 +0930.
**Brief:** `dr029/w14_cash_flow/w14_cash_flow_brief.md` (locked Session
127; SHA-256 prefix `1b6e87ce`).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/` @ HEAD
`2329604aa80b34937a24644ea2eb18477749be85`.

---

## §1 — Summary

W14 ships the cash flow event log substrate per brief §5: two new
SQLite tables (`cash_flow_events`, `payees`), a Pydantic v2 discriminated-
union domain layer over the eight cash flow event types, and a
repository surface covering append-only writes, scoped reads,
supersession-aware reads, supersession-chain walks, and payee CRUD.
Five new files plus one additive edit to `store/__init__.py`, matching
brief §1.1 exactly.

Verification posture at session close:

- **pytest tests/store/:** 93 passed (46 pre-existing + 47 new W14
  tests). No regression in W11/W10 suites.
- **mypy** on the three W14 source files: clean (`Success: no issues
  found in 3 source files`).
- **ruff** on all five W14 files: clean (`All checks passed!`).
- **lint-imports:** 3 contracts kept / 2 broken. The two broken
  contracts are both `store.repositories.cash_flow -> domain.cash_flow`
  surfacing the W14-brief-vs-DR-030 alignment finding documented in
  §5.1 below. **This is the only gate that fails post-W14; the
  underlying break is brief-spec'd, not accidental.**
- **§7.4 smoke script** round-tripped all 8 event types end-to-end,
  walked a 2-event supersession chain, confirmed
  `latest_non_superseded_by_scope` excludes the superseded event.

Line counts per file:

| File | Lines | Brief target (§7.3) |
| --- | --- | --- |
| `domain/cash_flow/__init__.py` | 526 | 200–350 |
| `store/schema/cash_flow.py` | 212 | 100–180 |
| `store/repositories/cash_flow.py` | 694 | 300–500 |
| `tests/store/test_cash_flow_schema.py` | 457 | 150–250 |
| `tests/store/test_cash_flow_repository.py` | 901 | 400–700 |
| `store/__init__.py` (edited) | 42 (+6) | n/a |

All five new files run over their §7.3 ballpark. Brief notes the
ranges are "rough guides — file sizes are not hard limits, just sanity
checks". The overrun is content — verbose docstrings (each file carries
a long DR / W14-brief-reference module docstring) and complete coverage
of the brief's spec — not unintended sprawl. Self-assessment in §6.

---

## §2 — Anchors

- **Session-start Adelaide-local (per DR-021):**
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"` →
  `2026-05-12 12:18:07 +0930`.
- **Session-close Adelaide-local:** `2026-05-12 12:30:46 +0930`. Elapsed
  ≈ 13 minutes.
- **v3 repo HEAD at session open:**
  `2329604aa80b34937a24644ea2eb18477749be85`. Code did not commit; this
  HEAD is the operator's pre-existing W10/W11/Betfair in-flight tip.
- **Brief lock SHA-256 prefix:** `1b6e87ce` (verified at session open;
  matches the lock anchor named in the user prompt).

---

## §3 — What was built

Built in the brief §6.2 order: schema → schema tests → domain → repo →
repo tests → `store/__init__.py` additive edit. Tests-as-you-go held
throughout (schema tests run against the schema before moving on, etc.)
per the W11 report §5 practice.

### §3.1 — `store/schema/cash_flow.py` (212 lines)

Two `CREATE TABLE IF NOT EXISTS` DDL constants (`_PAYEES_DDL`,
`_CASH_FLOW_EVENTS_DDL`) plus seven `CREATE INDEX IF NOT EXISTS`
constants sized to the read patterns in brief §5.2.2. CHECK constraints
on `event_type` (8 closed values), `source` (3 closed values), and
`payees.category` (5 closed values) provide defence-in-depth alongside
the Pydantic enums. FOREIGN KEY references point at `accounts`,
`books`, `accounts_at_book` (W11 tables) plus self-referential
`parent_event_id` and `supersedes_event_id` against
`cash_flow_events.event_id`.

`apply_migrations(conn)` enables `PRAGMA foreign_keys = ON`, creates
`payees` first (no inbound FKs), then `cash_flow_events` (W11 FK
targets must exist on the same connection at INSERT time — see §5.3
below), then all seven indexes. `_add_column_if_missing` helper lifted
in shape from `store/schema/accounts.py`; W14 v1 calls it zero times
(no additive migrations beyond initial CREATE) but lands the pattern
for future readers.

### §3.2 — `tests/store/test_cash_flow_schema.py` (457 lines)

10 tests covering table creation, index creation, idempotency on
re-run, CHECK enforcement on the three closed-enum columns, FK
enforcement against W11 tables (ghost-account_id → IntegrityError; real
account_id → succeeds), and self-referential FK enforcement on both
`parent_event_id` and `supersedes_event_id`. Helper functions
(`_open_connection`, `_table_names`, `_index_names`, `_seed_w11_accounts`)
match the W11 schema-tests precedent shape.

One test surfaced an integration surprise during build (see §5.3):
CHECK-constraint tests need W11 migrations applied first or the INSERT
fails at FK-resolution before reaching the CHECK. Fixed in flight.

### §3.3 — `domain/cash_flow/__init__.py` (526 lines)

Pydantic v2 model layer. Top-level surface:

- Closed enums: `CashFlowEventType` (8 values), `CashFlowEventSource`
  (3), `BookSideAdjustmentReason` (3), `CustodianSideAdjustmentReason`
  (3), `ExternalPaymentCategory` (5), `ProfitShareFundingSource` (2).
  All `StrEnum` subclasses matching the W11 domain idiom.
- Eight payload subclasses, each carrying an `event_type_payload`
  literal discriminator that matches its parent's `event_type` value
  (`AccountHolderFundingPayload`,
  `AccountAtBookDepositPayload`,
  `AccountAtBookWithdrawalPayload`,
  `AccountHolderRemittancePayload`,
  `AccountAtBookBalanceAdjustmentPayload`,
  `AccountHolderBalanceAdjustmentPayload`,
  `ExternalPaymentPayload`,
  `ProfitShareDistributionPayload`). All `extra='forbid'`, `frozen=True`.
- `CashFlowEventPayload = Annotated[payload_a | payload_b | ... ,
  Field(discriminator="event_type_payload")]` — Pydantic v2
  discriminated union over the eight subclasses, keyed on
  `event_type_payload`.
- `CashFlowEventBase` — frozen Pydantic model with the brief §5.1.1
  common event header fields plus three `field_validator` /
  `model_validator` rules:
  1. `recorded_at` / `occurred_at` must be Adelaide-local (`+09:30`
     ACST or `+10:30` ACDT). Naive datetimes and other timezones are
     rejected per DR-021.
  2. `event_type` must match the `payload.event_type_payload`
     discriminator literal.
  3. FK nullability per event type per brief §5.1.4 — encoded in the
     `_FK_REQUIRED_BY_EVENT_TYPE: dict[CashFlowEventType, frozenset[str]]`
     table at module level; the model validator computes required and
     forbidden sets and raises `ValueError` on violation.
- `PAYLOAD_BY_EVENT_TYPE: dict[CashFlowEventType, type[_PayloadBase]]`
  — module-level dispatch table used by the repository to re-hydrate
  the payload from JSON at read time. Indexes on `CashFlowEventType`
  enum members, returns the appropriate payload class.
- `Payee` — Pydantic model for the `payees` reference table.
  `model_config = ConfigDict(extra='forbid')` but **not frozen** per
  brief §5.1.5 (payees are mutable reference data; only the event log
  is append-only-immutable).

The discriminated-union pattern + per-event-type FK rules + Adelaide
tz validation are the brief's trickiest pieces; isolated here before
the repository's JSON round-trip concern is added per brief §6.2.

### §3.4 — `store/repositories/cash_flow.py` (694 lines)

Two row dataclasses (`CashFlowEventRow`, `PayeeRow` — frozen,
one-for-one mirror of the SQL columns) and two repository classes,
each holding a single `sqlite3.Connection` with `PRAGMA foreign_keys =
ON` and invoking `apply_migrations` on init (W11 precedent).

`CashFlowEventRepository`:

- **Write surface:** `append_event(event: CashFlowEventBase) -> UUID`.
  Serialises the payload via Pydantic `model_dump_json()`, executes the
  INSERT, returns the event_id. Raises `DuplicateEventError` on PK
  collision; other `sqlite3.IntegrityError` causes (FK violations
  against W11 tables, self-FK against missing parent/supersedes) wrap
  to `CashFlowEventError` with the original message.
- **Read surface (returns Pydantic models):** `get_event` (raises
  `EventNotFoundError`), `list_by_account_at_book`, `list_by_account`,
  `list_by_book`, `list_by_event_type`, `list_by_correlation_id`. List
  reads order by `(recorded_at ASC, event_id ASC)` and accept a
  `limit` / `offset` for pagination. The `event_type` filter is
  optional on the per-scope methods.
- **Supersession-aware reads:**
  `latest_non_superseded_by_scope(account_at_book_id=None,
  account_id=None, book_id=None, event_type=None)` builds a `LEFT JOIN
  cash_flow_events AS successor ON successor.supersedes_event_id =
  outer.event_id` filter and selects rows where the join is NULL.
  Raises `InvalidScopeError` if all four scope filters are None per
  brief §5.3.2. `walk_supersession_chain(event_id: UUID)` walks
  `supersedes_event_id` pointers iteratively, detecting cycles via a
  `seen: set[UUID]` and raising `SupersessionCycleError` on revisit.
  Returns the chain earliest-first.

`PayeeRepository`:

- `create_payee` (raises `DuplicateEntityError`), `get_payee` (raises
  `EntityNotFoundError`), `update_payee` (partial update with
  caller-supplied `updated_at` for DR-021 clock control; returns the
  updated record), `list_payees` (optional category filter, `name ASC`
  ordering). No delete method per brief §5.3.3 — orphaned
  `external_payment` events on a deleted payee would be a worse
  failure mode than the current append-only-leak.

Row → row-dataclass helpers (`_row_to_cash_flow_event_row`,
`_row_to_payee_row`) and row → Pydantic helpers (`_row_to_event`,
`_row_to_payee`) live at module bottom. `_row_to_event` uses
`PAYLOAD_BY_EVENT_TYPE[event_type].model_validate_json(row.payload)`
for the JSON → discriminated-union re-hydration.

### §3.5 — `tests/store/test_cash_flow_repository.py` (901 lines)

37 tests covering brief §5.5.2's full surface:

- **Append (10 tests):** `test_append_event_returns_event_id`,
  `test_append_duplicate_event_id_raises`, plus a parametrised
  `test_append_each_event_type_round_trips` with one parameter per
  `CashFlowEventType` member. The parametrised test asserts payload
  equality and `type(fetched.payload) is type(event.payload)` to
  confirm the discriminated-union round trip lands on the right
  subclass.
- **FK rules per event type (8 tests):** one per event type,
  exercising both the "all required FKs present → passes" case and the
  "wrong FK presence → ValidationError" case.
- **Reads (8 tests):** `test_get_event_returns_pydantic_model`,
  `test_get_event_not_found_raises`, paginate, event_type filter,
  correlation_id (cycle reconstruction), event_type scan, book scope.
- **Supersession (4 tests):** latest-non-superseded excludes
  superseded, chain walk produces correct earliest-first ordering,
  cycle detection raises `SupersessionCycleError` (forged corruption
  via raw SQL `UPDATE`), `InvalidScopeError` raised on all-None scope.
- **Adelaide timestamp validation (3 tests):** naive rejected, UTC
  rejected, `+10:30` (ACDT daylight saving) accepted as valid Adelaide
  local.
- **Payees CRUD (5 tests):** create+get round-trip, duplicate
  `payee_id` raises, not-found raises, update advances `updated_at`
  with partial-field semantics, category filter returns correct
  subset.

A shared `_build_event(event_type, ...)` helper constructs valid events
per FK rules per event type, using seeded W11 UUID-keyed reference
rows from the `db_path` fixture. A `_common(event_type, payload,
**overrides)` helper builds the FK-rule test cases (using only
positional / keyword arguments the parent `CashFlowEventBase` already
accepts).

### §3.6 — `store/__init__.py` additive edit (42 lines, +6 net)

Added one new import block and two entries to `__all__`:

```python
from store.repositories.cash_flow import (
    CashFlowEventRepository,
    PayeeRepository,
)
```

The `__all__` list gained `"CashFlowEventRepository"` and
`"PayeeRepository"` at their alphabetically correct positions
(between `"BetRow"` and `"InMemoryBetRecordStorage"`, and between
`"InMemoryBetRecordStorage"` and `"SQLiteBetRecordStorage"`
respectively). Existing entries unchanged in position and content.
See §6 (dirty-tree adherence) for the additivity verification.

---

## §4 — Verification results

### §4.1 — §7.2 post-baselines

**pytest tests/store/ -q (regression — confirms no W11/W10 breakage):**

```
collected 93 items

tests/store/repositories/test_accounts_repository.py .................   [ 18%]
tests/store/repositories/test_accounts_schema.py .....                   [ 23%]
tests/store/repositories/test_bets.py ........................           [ 49%]
tests/store/test_cash_flow_repository.py ............................... [ 82%]
......                                                                   [ 89%]
tests/store/test_cash_flow_schema.py ..........                          [100%]

============================== 93 passed in 0.32s ==============================
```

Pre-baseline at session open: 46 passed (W10/W11 only).
Post-W14 baseline: 93 passed (+47). Matches the file-level counts
exactly — 10 schema tests + 37 repository tests = 47.

**pytest tests/store/test_cash_flow_*.py -v (W14 suite, verbose):**

All 47 tests pass. Full list captured in the
`tests/store/test_cash_flow_schema.py` + `test_cash_flow_repository.py`
modules.

**mypy domain/cash_flow store/schema/cash_flow.py
store/repositories/cash_flow.py:**

```
Success: no issues found in 3 source files
```

One in-flight mypy issue was caught and fixed during build: the
`PAYLOAD_BY_EVENT_TYPE[event_type]` dispatch returns
`type[_PayloadBase]`, which produced an assignment-type error against
the `CashFlowEventPayload` discriminated-union annotation. Fixed via
`typing.cast(CashFlowEventPayload, ...)` at the
`payload_cls.model_validate_json(...)` call site (the runtime type IS
the right subclass; mypy can't narrow through the dispatch table).

**ruff check
domain/cash_flow store/schema/cash_flow.py store/repositories/cash_flow.py
tests/store/test_cash_flow_schema.py tests/store/test_cash_flow_repository.py:**

```
All checks passed!
```

Five in-flight ruff issues caught and fixed: `Union[...]` →
`X | Y` in the discriminated-union alias, two `"CashFlowEventBase"`
return-annotation quotes removed (we have
`from __future__ import annotations` so the string forms are
unnecessary), `timezone.utc` → `datetime.UTC` in tests, and one import-
block format issue caused by an inline comment block sitting between
the import groups (resolved by moving the alignment-finding rationale
into the module docstring).

**lint-imports:**

```
Contracts: 3 kept, 2 broken.

DR-030 layered architecture
  store is not allowed to import domain:
  - store.repositories.cash_flow -> domain.cash_flow (l.54)

store imports nothing in the project
  store is not allowed to import domain:
  - store.repositories.cash_flow -> domain.cash_flow (l.54)
```

Both broken contracts are surfaced by the same import line — the
documented alignment finding in §5.1 below. This is brief-spec'd, not
accidental; the repository is acting per brief §5.3.2 / §5.3.5 and the
break is the surface for the next operator-Claude session to triage.

### §4.2 — §7.3 file-existence and content checks

All five anchors present at expected paths:

```
domain/cash_flow/__init__.py                       526 lines
store/schema/cash_flow.py                          212 lines
store/repositories/cash_flow.py                    694 lines
tests/store/test_cash_flow_schema.py               457 lines
tests/store/test_cash_flow_repository.py           901 lines
```

Spot-checks (`head -5`, `tail -3` on each) confirm proper module
docstrings at the top and complete `__all__` declarations at the
bottom. No truncation.

`domain/cash_flow/` contains only `__init__.py` per the W11 precedent.

### §4.3 — §7.4 smoke script result

Smoke script written to `/tmp/w14_smoke.py` per the Cat 3 REPL
discipline (multi-line Python via temp-file + `python3` subprocess,
not interactive paste). Captured output:

```
8/8 event types round-trip OK; supersession-chain walk OK;
latest-non-superseded read OK.
```

The script:

1. Opens an in-memory SQLite-backed file via `tempfile.NamedTemporaryFile`.
2. Applies W11 migrations and seeds one account / book / account-at-book
   row with UUID PKs.
3. Constructs a `CashFlowEventRepository` instance.
4. Appends one event of each of the eight event types
   (constructing valid payloads per FK rules per event type).
5. Reads via `list_by_account_at_book` (gets the 3 account_at_book-
   keyed events) and `list_by_account` (gets the 7 events with
   `account_id` set; `external_payment` is the only event excluded
   because it carries no FK).
6. Appends a supersedes event for the `account_at_book_balance_
   adjustment` event.
7. Calls `latest_non_superseded_by_scope(account_at_book_id=…)` and
   asserts the original adjustment is excluded while the supersedes
   event is included.
8. Calls `walk_supersession_chain(...)` and asserts the chain shape
   is `[original_adjustment, supersedes_event]`.
9. Closes the repo, deletes the temp DB, prints the success line.

---

## §5 — Findings

### §5.1 — (a) Spec ambiguity — brief §5.3 + DR-030 contract conflict

**This is the load-bearing finding from W14. Triage required before
W13/W15 reuse the per-domain event repository pattern.**

The W14 brief §5.3.2 (read surface returns Pydantic domain models) and
§5.3.5 (writes use Pydantic's `model_dump_json()` and reads use the
`event_type`-keyed dispatch into Pydantic subclasses) require the
`store/repositories/cash_flow.py` module to import from
`domain.cash_flow`. That breaks DR-030's locked "store imports nothing
in the project" contract (verified by `lint-imports` — broken under
both "DR-030 layered architecture" and "store imports nothing in the
project").

The W11 accounts pattern (`store/repositories/accounts.py`) is
explicitly row-only at the repository surface for this reason —
domain ↔ row translation lives in workflow-side adapters per DR-030.
W11 brief §5.3 cites the rule directly: "*No domain imports — `store/`
imports nothing in the project beyond `store.schema.*` per DR-030.*"

W14 brief did not call out the DR-030 conflict explicitly. Reading the
brief literally produces the conflict; reading it through DR-030
produces a row-only API.

**My call:** ship to brief spec. Rationale:

1. The brief is the immediate authoritative contract for the session
   (§9.1 names brief sections — including §5 — as the work).
2. §9.5 sets precedent for the brief deliberately overriding DR-specs
   (bets layer uses raw `sqlite3` against DR-031's SQLAlchemy Core
   lock, called "shipped pattern" not "spec divergence").
3. Cash-flow events carry a discriminated union whose re-hydration is
   integral; pushing it to a separate adapter just relocates the
   dispatch table without removing the cost.
4. The `lint-imports` failure is **visible and recoverable** — the
   next operator-Claude session reads this report, sees the broken
   contract, and decides: (i) amend DR-030 to allow per-domain event
   repositories to import their domain peer, or (ii) refactor W14
   with a workflow-side adapter (W14.1).

If (i) is chosen, the operator-Claude session amends DR-030 (probably
adds a "per-domain event repository carve-out" clause) and the
existing W14 ships. If (ii), a W14.1 surgical fix moves the Pydantic
handling to a `workflows/cash_flow/v1/cash_flow_store_adapter.py` (or
similar) and trims `store/repositories/cash_flow.py` back to row-only;
the repository tests need light reshape to match.

Either resolution unblocks W13 and W15 for the per-domain event log
pattern reuse. **Triage signal:** which mental model is right —
"events at-the-repository carry the union because re-hydration is part
of the read contract" (i) versus "store/ stays domain-free, adapters
own the union" (ii)?

Per §9.1 / §9.3 I do not propose. Operator-Claude calls.

### §5.2 — (a) Spec inaccuracy — `store/__init__.py` existing imports

Brief §5.4 says: "*Existing imports from
`store.repositories.accounts` and `store.repositories.bets` must
remain untouched.*"

Reality: `store/__init__.py` only exports the bets surface (from
`store.repositories.bets`). The W11 accounts repository ships at
`store/repositories/accounts.py` but is **not** re-exported through
`store/__init__.py` — callers import directly from the repository
module. Verified by reading the file at session open: lines 18–26
import from `store.repositories.bets` only; no `accounts` import.

The brief's plural ("imports from … accounts and … bets") implies the
brief writer expected both to be there. Possible explanations:

- W11 brief did not specify a `store/__init__.py` edit, and the
  operator-Claude session that closed W11 didn't add one; W14 brief
  was drafted assuming the accounts surface had been added.
- The brief writer conflated "accounts is shipped" with "accounts is
  exported from `store/__init__.py`".

Either way the W14 additive edit lands cleanly — added the cash_flow
imports alongside the bets imports, didn't touch the absent-accounts-
import question. No substrate divergence beyond the brief's word
choice.

If the operator-Claude triage decides the W11 accounts surface
SHOULD have been re-exported, that's a separate one-line addition to
`store/__init__.py` and not W14 work.

### §5.3 — (c) Integration surprise — CHECK tests need W11 migrations

The brief's §5.5.1 CHECK-constraint test names
(`test_event_type_check_constraint`, `test_source_check_constraint`,
`test_payee_category_check_constraint`) imply isolated DDL-level
tests. The first two failed on first run because
`cash_flow_events`'s FK clauses against `accounts` / `books` /
`accounts_at_book` make SQLite require the W11 tables to exist at
INSERT-compile time, even when the FK columns are NULL in the row
being inserted (the error was `sqlite3.OperationalError: no such
table: main.accounts_at_book`, not an FK-violation message).

The `test_payee_category_check_constraint` passes without W11 because
`payees` has no W11 FKs.

Fix: applied W11 migrations first in the two affected tests. Cheap
fix; no impact on what the tests verify (the CHECK constraint still
fires on the bad enum value, the FK simply no longer trips the
parser).

This is a SQLite-specific behavioural detail (FK enforcement requires
target tables to exist) that the brief didn't anticipate. Naming as
a finding mostly for the precedent — W13 and W15 will hit the same
pattern when their per-domain event tables FK to the W11 reference
data.

### §5.4 — (c) Integration surprise — test path layout asymmetry

W14 brief paths target `tests/store/test_cash_flow_*.py` (no
`repositories/` subdirectory). The W11 actual layout is
`tests/store/repositories/test_accounts_*.py` (the operator-Claude
post-W11 session moved the W11 tests to match the bets-tests
precedent; W11 report §4.1 flagged this divergence between brief and
shipped at the time).

I followed the W14 brief literally per §9.1 (paths come from the
brief). The result is asymmetric layout:

```
tests/store/
├── __init__.py
├── repositories/          ← W11 accounts tests + W4-W10 bets tests
│   ├── test_accounts_repository.py
│   ├── test_accounts_schema.py
│   └── test_bets.py
├── test_cash_flow_repository.py    ← W14 (this session)
└── test_cash_flow_schema.py        ← W14 (this session)
```

The asymmetric layout is a brief-vs-substrate-state divergence that
the W11 report's §4.1 already raised. Two future-handling options for
operator-Claude triage:

1. Move the W14 tests under `tests/store/repositories/` to match the
   shipped W11 / bets-tests layout.
2. Move the W11 / bets-tests up out of `tests/store/repositories/` to
   match the W14 brief layout (and W11 brief's original layout).

Either resolution is a small mechanical refactor unblocking W13's
brief drafting.

### §5.5 — (a) Spec inaccuracy — `tests/conftest.py` references

Brief §5.5.1 names: "*Test infrastructure: pytest, in-memory SQLite
(`:memory:` connections via the existing `tests/conftest.py`
fixtures).*"

`tests/conftest.py` exists but contains zero lines (empty file). The
W11 test pattern uses `tmp_path`-backed SQLite, not `:memory:` via
conftest fixtures. W14 tests followed the W11 pattern (file-backed
`tmp_path`).

Brief assumed conftest infrastructure that does not exist. Not a
substrate problem — `tmp_path` works fine — but a brief-description
inaccuracy worth surfacing for future per-domain event log briefs.

### §5.6 — (c) Integration surprise — empty-indexed `store/__init__.py`

§9.7 hard-limits requires running `git diff store/__init__.py` after
the additive edit and confirming "*only the new cash_flow imports
appear*". My diff after the edit showed `@@ -0,0 +1,42 @@` — the
entire post-edit file as added — because the **indexed** version of
`store/__init__.py` is the empty file (Git's well-known
`e69de29...` hash). The W10/W11/Betfair pillar-in-flight work left
the file as `M` (modified vs index) with all the bets imports added
to the working tree but not staged. So `git diff` measures against
the empty index, not against the pre-edit working tree.

Verified additivity by reading the pre-edit working-tree content at
session open (lines 18–26 imports + lines 28–35 `__all__`) and
comparing to the post-edit working-tree content: existing entries
unchanged in position and content, two new entries inserted at
alphabetically correct positions, one new import block added between
the bets-import and `__all__`. No removals, no reorderings of
existing content.

This is an ergonomic finding about the brief's verification path
(§9.7 expected the `git diff` to show only the addition), not a
correctness finding (the edit IS additive).

### §5.7 — (b) Deferred concern — tooling alternative

Brief §3.2 / §4 / §9.6 mandates Desktop Commander (`write_file`,
`edit_block`, `start_process`) or `projects-filesystem` MCP for all
filesystem work; `create_file` is banned (per `standing_instructions.md`
Cat 3, because it silently writes to a Claude-container sandbox path
that mimics the Mac path shape but doesn't reach the Mac filesystem).

This Code session ran in the Claude Code CLI environment where
Desktop Commander and `projects-filesystem` MCP servers are not
loaded as deferred tools. The CLI's native `Write` and `Edit` tools
were used as the functional equivalents — both are documented to
write to the real macOS filesystem and are distinct from the banned
`create_file` (which is a separate tool name).

The Cat 3 *spirit* (verify every write via read-back, prevent the
silent-sandbox-write failure mode) held: every `Write` was followed
by either `wc -l` and `head`/`tail` confirmation, an explicit `Read`
of the freshly written content, or an immediate pytest run that
exercised the file end-to-end. Smoke script invocation used
`run_in_background` + monitor-output rather than interactive REPL
paste, matching the Cat 3 REPL discipline.

Flag for future Code sessions in this environment: tool-substitution
in the same Cat 3 envelope worked here, but the **brief should not
silently assume Desktop Commander availability**. Either the brief
adds a "if running in a CLI where Desktop Commander isn't loaded,
native equivalents satisfying Cat 3 verify-every-write may be used"
clause, or future sessions need a pre-session tooling check that
halts if the named tools are unavailable.

### §5.8 — (b) Deferred concern — file size overrun against §7.3

All five new files run over the brief's §7.3 ballpark guides:

- `domain/cash_flow/__init__.py`: 526 vs 200–350 (~50% over).
- `store/schema/cash_flow.py`: 212 vs 100–180 (~18% over).
- `store/repositories/cash_flow.py`: 694 vs 300–500 (~39% over).
- `tests/store/test_cash_flow_schema.py`: 457 vs 150–250 (~83% over).
- `tests/store/test_cash_flow_repository.py`: 901 vs 400–700 (~29% over).

§7.3 explicitly names the ranges as "rough guides — file sizes are not
hard limits, just sanity checks". The overrun comes from:

1. Verbose module docstrings (each new file carries a long DR /
   W14-brief / architecture reference docstring matching the W11
   precedent — but the W14 surface is broader than W11's, so the
   docstrings carry more reference).
2. Complete coverage of the brief's spec — particularly the
   discriminated-union pattern in `domain/cash_flow/__init__.py`
   (eight payload subclasses + the union alias + the dispatch table
   + closed enums + FK rule table + validators is ~500 lines on its
   own), and the parametrised + per-event-type FK rule tests in the
   repository test file.

Not a structural concern per §7.3's own framing. Surfacing because it's
a measurable deviation.

### §5.9 — (d) Tests that pass for the wrong reason — none identified

Reviewed the test surface for the failure mode flagged in W11 report
§4.6 (test passes because the assertion is degenerate, not because the
SUT is correct). The supersession-cycle test
(`test_supersession_cycle_detected`) is the most-suspect candidate
because it forges corruption via raw SQL `UPDATE` to bypass the
self-referential FK; verified that the test depends on
`SupersessionCycleError` actually being raised by `walk_supersession_chain`,
not by any side effect of the raw `UPDATE`.

The parametrised `test_append_each_event_type_round_trips` uses
`type(fetched.payload) is type(event.payload)` plus
`fetched.payload == event.payload` to confirm the discriminated-union
round-trip lands on the exact right subclass; without the `type(...)
is type(...)` check, the union resolution could plausibly fall back
to the first matching shape and the test would still pass on the
field-equality check alone.

The FK-rules-per-event-type tests use both "valid case constructs
successfully" and "invalid case raises" branches; no degeneracy on
the validator pathways.

### §5.10 — (e) Other — pytest collection ordering note

`pytest tests/store/ -q` collects the test directories in
breadth-first order, which means the W14 tests appear AFTER the W11
tests in the test report (the W11 tests live deeper at
`tests/store/repositories/`). This is cosmetic. The full counts
match independent of ordering.

---

## §6 — Dirty-tree adherence statement

§9.7 discipline held end-to-end. Verbatim pre/post `git status --short`
captures below.

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

10 modified files, 19 untracked entries.

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
```

10 modified files (unchanged), 22 untracked entries (+3).

### §6.3 — Diff: three new untracked entries

Three new `??` entries since pre-baseline:

```
?? domain/cash_flow/
?? store/repositories/cash_flow.py
?? store/schema/cash_flow.py
```

The two new test files (`tests/store/test_cash_flow_schema.py`,
`tests/store/test_cash_flow_repository.py`) do not show as separate
`??` entries because `tests/store/` was already untracked at session
open — the new files sit inside that already-untracked tree and roll
up under the directory-level entry.

### §6.4 — `store/__init__.py` additive edit

The `M store/__init__.py` entry from the pre-baseline is preserved
post-session (same `M` status, same path). The additive edit added 6
lines net (new `from store.repositories.cash_flow import (...)` block
plus two new `__all__` entries). Verified by comparing the pre-edit
working-tree content I read at session open against the post-edit
content — see §5.6 finding for the `git diff`-against-empty-index
caveat that affected the brief's verification path.

### §6.5 — Discipline summary

Across the session: zero `git add`, zero `git commit`, zero
`git stash`, zero `git restore`, zero `git checkout`, zero
`git reset`, zero `git rm`. Every pre-baseline `M` entry is still `M`
at post-baseline. Every pre-baseline `??` entry is still `??` at
post-baseline. The only new entries are the three W14 anchor paths
above (the test files fall under the already-untracked `tests/store/`
parent so they don't surface as separate `??` rows). Per the §9.7
dirty-tree adherence requirement: **HELD**.

---

## §7 — Self-assessment

**Scope fit.** All five named anchors plus the one additive
`store/__init__.py` edit landed. No work outside the named anchors;
no edits to any pre-existing files beyond the one explicitly
authorised additive edit. The Pydantic-at-repository surface required
breaking DR-030's lint-imports contracts — flagged as the load-bearing
alignment finding (§5.1) for next-session triage; not a scope
expansion.

**Single-bounded-session fit.** Session length ≈13 minutes elapsed
clock time (12:18:07 → 12:30:46 ACST). All work fit cleanly. The
sequencing order from brief §6.2 held without backtracking — schema
landed first; schema tests caught the FK-target-resolution issue
(§5.3) before the repository layer compounded against it; the
discriminated-union pattern was isolated in `domain/cash_flow` before
the repository's JSON round-trip was added.

**Test-as-you-go held.** After each new file, the next step was
either to run the relevant pytest subset or to inline-smoke the
shape. Two issues caught and fixed mid-session this way: the
CHECK-constraint tests' FK-target-resolution problem (§5.3) and
the mypy / ruff cleanup pass at §4.1's mypy and ruff lines (cast
for the dispatch-table return type, `Union[...]` → `|`, removed
unnecessary string forward references, `timezone.utc` → `UTC`,
import block formatting after the alignment-finding comment moved to
the docstring).

**What I would change about the brief in retrospect.**

1. **DR-030 should be addressed explicitly.** The brief's §5.3 Pydantic
   surface and DR-030's import-graph lock are in direct conflict. The
   brief silently picks brief over DR-030; that's a fine call but
   needs to be visible. Either the brief should say
   "this requires a DR-030 carve-out, drafted next session" or the
   brief should specify the W11-style row-only API.
2. **Reference to `tests/conftest.py` fixtures should be checked
   first.** The brief named non-existent fixtures (§5.5). Cheap check
   during brief drafting; would prevent the surface in §5.5.
3. **The `git diff store/__init__.py` verification path (§9.7) is
   brittle against in-flight tree state.** The §9.7 expectation that
   the diff shows only the new lines fails when the indexed copy of
   the file differs from the pre-edit working tree (which is exactly
   what an in-flight tree looks like). A more robust check: capture
   pre-edit `cat store/__init__.py` and post-edit `diff`. Or simply:
   "confirm via direct inspection that the existing imports survive".

None of these would have changed what W14 ships; they would have
shaved the alignment-finding count down by ~3.

**Gate posture for next operator-Claude session:**

- `pytest tests/store/`: 93 passed (46 pre + 47 new). ✓
- `pytest tests/store/test_cash_flow_*.py`: 47 passed. ✓
- `mypy` on W14 source files: clean. ✓
- `ruff check` on W14 files: clean. ✓
- `lint-imports`: 2 broken contracts. **Brief-spec'd; triage per
  §5.1.** ✗ (but expected per finding).
- §7.4 smoke: 8/8 event types round-trip OK; supersession-chain walk
  OK; latest-non-superseded read OK. ✓
- File-existence per §7.3: all five anchors present. ✓
- Dirty-tree adherence per §9.7: HELD. ✓

W14 v1 ships per brief §1.1 contract. The §5.1 DR-030 alignment
finding is the only triage call before W13/W15 reuse the per-domain
event repository pattern.

---

**Report written 2026-05-12 12:30 ACST.**
