# W15 — Operations log (Code report)

## §1 — Session header

**Brief:** `dr029/w15_ops_log/w15_ops_log_brief.md`
(Locked Session 142; SHA-256 prefix `f0d54d6f`, verified at session
open against `shasum -a 256` — match).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/`.
**Session open:** 2026-06-10, 17:25 ACST (Adelaide local, DR-021).
**Session close:** 2026-06-10, 19:10 ACST.
**Interpreter:** `.venv/bin/python` → Python 3.12.7 (DR-031, ≥ 3.12 OK).
**Pre-reads consulted in order:** brief; `store/schema/cash_flow.py`;
`domain/cash_flow/__init__.py`;
`workflows/cash_flow/v1/cash_flow_store_adapter.py`; rebuild
`decisions.md` DR-025 including the 2026-05-22 Session 139 amendment.
Reference-only pre-reads (`store/repositories/cash_flow.py`,
`store/schema/bets.py` via the W12.1 read region, `domain/bets`) were
consulted on demand.

### §1.1 — §7.1 pre-baselines

- `git status --short` — dirty-tree snapshot captured (10 modified,
  29 untracked). The W12.1 surgical fix has landed before this
  session, exactly as §9 anticipated (additional modifications on
  `domain/bets/__init__.py`, `store/repositories/bets.py`,
  `workflows/balances/v1/balance_derivation.py`, etc., plus a new
  W12.1 test file under `tests/workflows/balances/v1/`).
- `.venv/bin/lint-imports` — **5 contracts kept, 0 broken** (162
  files, 410 dependencies analysed).
- `.venv/bin/pytest -q` — **820 passed, 2 failed**. The two failures
  (`tests/workflows/balances/v1/test_balance_derivation.py::test_balance_free_bet_inventory_surfaces`
  and
  `tests/workflows/promos/v1/test_promo_derivations.py::test_inventory_single_freebie_available`)
  pre-date W15; they concern `compute_free_bet_inventory`, an
  untouched module.
- §5 new-file paths confirmed absent: no `domain/ops/`, no
  `store/schema/ops.py`, no `store/repositories/ops.py`, no
  `workflows/ops/`.

---

## §2 — Pre-build alignment check

### §2.1 — Working-tree snapshot

Captured in §1.1. The dirty-tree state matches the brief §9
characterisation: the W12+ build region is untracked and the W12.1
surgical fix has already landed. W15's anchors are disjoint from
all of that.

### §2.2 — §5.7 naming-collision check

Per the brief:

```
$ .venv/bin/python -c "import ops; import domain.ops; import workflows.ops"
```

ran cleanly after the W15 modules existed; all three module paths
resolve to distinct locations:

- `ops` → `/Users/tim/Desktop/Projects/bethub-v3/ops/__init__.py`
  (root placeholder; untouched).
- `domain.ops` → `/Users/tim/Desktop/Projects/bethub-v3/domain/ops/__init__.py`
  (new — §5.1).
- `workflows.ops` → `/Users/tim/Desktop/Projects/bethub-v3/workflows/ops/__init__.py`
  (new — §5.4 package).

No shadowing, no resolution surprise. Root `ops/` retains its empty
`__init__.py` and is in no way modified.

### §2.3 — Pattern-file confirmation

The W14 / W14.1 shipped code is the authoritative template (the brief
makes this explicit). Confirmed by reading
`store/schema/cash_flow.py`, `domain/cash_flow/__init__.py`,
`workflows/cash_flow/v1/cash_flow_store_adapter.py`, and on demand
`store/repositories/cash_flow.py` (the W14.1-trimmed row-only shape).
W15 mirrors them field-for-field with the scope FKs swapped to the
bet axis (`bet_id` + `cycle_id`) and the closed event-type enum cut
to one member (`hedge_state_classification`).

---

## §3 — What was built, per §5 sub-section

Sequencing followed the brief's §6 order without deviation.

### §3.1 — `domain/ops/__init__.py` (§5.1)

New module. Surface:

- `OpsEventType(StrEnum)` — one member,
  `HEDGE_STATE_CLASSIFICATION = "hedge_state_classification"`.
- `OpsEventSource(StrEnum)` — `OPERATOR`, `SYSTEM`, `INTEGRATION`
  (verbatim mirror of `CashFlowEventSource`).
- `HedgeState(StrEnum)` — six DR-025 states, values verbatim:
  `hedged`, `hedge_partial`, `hedge_failed`, `unhedged_deliberate`,
  `unhedged_oversight`, `unhedged_unclassified`. Home decision per
  brief §5.1: lives in `domain/ops` with the payload that carries
  it; module docstring marks the future relocation candidacy
  (`domain/bets`) without pre-emptively placing it there.
- `ClassificationPath(StrEnum)` — `OPERATOR`, `AUTO_BETFAIR`,
  `AUTO_RESOLVE`, `SYSTEM_DEFAULT`. Each value carries the
  distinction the brief §5.1 / DR-025 amendment names.
- `_PayloadBase(BaseModel, frozen=True, extra='forbid')` — mirror
  of `domain.cash_flow._PayloadBase`.
- `HedgeStateClassificationPayload(_PayloadBase)` — fields
  `event_type_payload` (literal), `from_state` (optional;
  `None` on initial classification), `to_state` (required), `path`
  (required), `reason` (optional). Payload-level validator
  `_check_transition_is_a_transition` enforces
  `from_state != to_state` when `from_state is not None`.
- `OpsEventBase(BaseModel, frozen=True, extra='forbid')` — common
  event header: `event_id` (UUID), `event_type`, `recorded_at` /
  `occurred_at` (Adelaide-local-validated), `bet_id` (`str | None`),
  `cycle_id` (`str | None`), `parent_event_id` /
  `supersedes_event_id` (`UUID | None`), `payload` (the
  discriminated union), `source`, `correlation_id`, `notes`.
- Validators on `OpsEventBase`:
  - `_check_adelaide_local` (field validator) — rejects naive
    timestamps and non-Adelaide offsets.
  - `_check_event_type_matches_payload` (model_validator) — keeps
    the parent `event_type` and the payload discriminator aligned.
  - `_check_fk_rules` (model_validator) — for
    `hedge_state_classification`, both `bet_id` AND `cycle_id` are
    REQUIRED; pattern table (`_FK_REQUIRED_BY_EVENT_TYPE` +
    `_ALL_FK_FIELDS`) mirrors cash_flow.
  - `_check_path_source_consistency` (model_validator) — encoded
    via `_PATH_REQUIRES_SOURCE` lookup: `OPERATOR ⇔ OPERATOR`,
    `AUTO_BETFAIR / AUTO_RESOLVE / SYSTEM_DEFAULT ⇔ SYSTEM`.
- `OpsEventPayload` annotated discriminated union and
  `PAYLOAD_BY_EVENT_TYPE` dispatch table — mirror of cash_flow,
  used by the adapter to rehydrate payloads from JSON.

Imports: stdlib + pydantic only. DR-030 boundary intact.

### §3.2 — `store/schema/ops.py` (§5.2)

New module. DDL constant `_OPS_EVENTS_DDL` carries the header
columns with the scope swapped to the bet axis (`bet_id` TEXT,
`cycle_id` TEXT), the `event_type` CHECK constraint pinned to the
one v1 value, the `source` CHECK constraint pinned to the same
three values as cash_flow, self-FKs on `parent_event_id` /
`supersedes_event_id`, and an outward FK on `bet_id` to
`bets(bet_id)`. `cycle_id` carries no FK (cycles have no table per
DR-032). Four indexes match the brief §5.2 read patterns:
`idx_ops_events_bet`, `idx_ops_events_cycle`,
`idx_ops_events_event_type`, `idx_ops_events_correlation`.

`_add_column_if_missing` lifted in shape from
`store/schema/cash_flow.py`. `apply_migrations(conn)` enables
`PRAGMA foreign_keys = ON`, creates the table, creates the four
indexes; all DDL is `IF NOT EXISTS`, so idempotent on re-run. The
docstring documents the cross-schema dependency on `bets` exactly
as cash_flow documents its dependency on W11 — callers (and tests)
apply the bets-schema migrations on the same connection first.

Imports: stdlib only. DR-030 boundary intact.

### §3.3 — `store/repositories/ops.py` (§5.3)

New module. Surface:

- `OpsEventRow` (frozen dataclass) — flat mirror of the SQL
  columns, with `bet_id: str | None` and `cycle_id: str | None`
  per the brief's scope-typing note.
- Module-level errors mirroring cash_flow: `OpsEventError`,
  `DuplicateEventError`, `EventNotFoundError`,
  `SupersessionCycleError`, `InvalidScopeError`.
- `OpsEventRepository(conn)` — `__init__` sets `row_factory =
  sqlite3.Row`, enables FK enforcement, and invokes
  `apply_migrations` (idempotent).
- Write surface: `append_row(row)` — single INSERT; translates
  `UNIQUE constraint failed: ops_events.event_id` into
  `DuplicateEventError`, other `sqlite3.IntegrityError` into
  `OpsEventError`. Append-only at the SQL layer; no UPDATE / DELETE
  methods exposed.
- Single-row read: `get_row(event_id)` raising
  `EventNotFoundError` on miss.
- List reads: `list_rows_by_bet`, `list_rows_by_cycle`,
  `list_rows_by_event_type`, `list_rows_by_correlation_id`, each
  ordered `recorded_at ASC, event_id ASC` with cash_flow-style
  `limit` / `offset` (where applicable).
- Supersession-aware reads:
  `latest_non_superseded_rows_by_scope` with bet / cycle /
  event_type filters (at least one required, else
  `InvalidScopeError`) using the same LEFT JOIN pattern as
  cash_flow; `walk_supersession_chain_rows` returning the chain
  earliest-first with cycle detection.
- `_event_type_value(...)` helper accepting either a string or an
  enum-like with a `.value`, preserving the DR-030 "no
  `domain.ops` import here" boundary.

Imports: stdlib + `store.schema.ops` only. DR-030 boundary intact.

### §3.4 — `workflows/ops/v1/ops_store_adapter.py` (§5.4)

New module + the package files `workflows/ops/__init__.py` and
`workflows/ops/v1/__init__.py` (both empty, matching the
cash_flow package shape).

`OpsStoreAdapter(conn)` mirrors `CashFlowStoreAdapter`:

- Constructor takes a `sqlite3.Connection` and instantiates the
  underlying `OpsEventRepository`.
- `append_event(event)` → `UUID`; `get_event(event_id)` →
  `OpsEventBase`.
- `list_by_bet(bet_id, event_type=None, limit=1000, offset=0)`,
  `list_by_cycle(...)`, `list_by_event_type(event_type)`,
  `list_by_correlation_id(correlation_id)`.
- `latest_non_superseded_by_scope(bet_id=None, cycle_id=None,
  event_type=None)` — at least one filter required.
- `walk_supersession_chain(event_id)`.
- Module-level helpers `_row_to_event` and `_event_to_row`
  performing Pydantic ↔ row translation via
  `PAYLOAD_BY_EVENT_TYPE` dispatch and `model_validate_json` /
  `model_dump_json` exactly as the W14.1 adapter does.

Imports: stdlib + `domain.ops` + `store.repositories.ops`. DR-030
boundary intact.

### §3.5 — `store/__init__.py` (§5.5 additive edit)

Added the `from store.repositories.ops import (OpsEventRepository,)`
import block alongside the existing cash_flow and promos blocks,
and inserted `"OpsEventRepository",` into `__all__` in alphabetical
order. No reordering, removal, or reformatting of existing exports.
`git diff` confirms the change is additive.

### §3.6 — `.importlinter` (§5.6 additive edit)

Added the single line `    workflows.ops` to the
`workflows-independent` independence contract's `modules` list,
under `workflows.bet_entry` and `workflows.burst_review`. No other
contract was touched. The contract's continued under-population
(it does not list `workflows.cash_flow`, `workflows.promos`, or
`workflows.balances` despite those packages existing) is recorded
verbatim as Finding f#1 below.

### §3.7 — Tests (§5.8 — three files)

Three new test files plus the two test package `__init__.py`
files. Counts: 9 + 16 + 36 = **61 new tests, all green**.

`tests/store/repositories/test_ops_schema.py` (9 tests):

- Table + four indexes created.
- `apply_migrations` idempotent across two extra invocations.
- `event_type` CHECK rejects an unknown value.
- `source` CHECK rejects an unknown value.
- FK against `bets(bet_id)` — rejection (missing referent) and
  resolution (seeded referent). Confirms the `bets` + `ops`
  migrations layer cleanly and FK enforcement is alive
  end-to-end.
- Self-FK on `parent_event_id` rejects missing referent.
- Self-FK on `supersedes_event_id` rejects missing referent.

`tests/store/repositories/test_ops_repository.py` (16 tests):

- Insert + return event_id; round-trip via `get_row`.
- Duplicate PK → `DuplicateEventError`; bad FK → `OpsEventError`.
- `get_row` miss → `EventNotFoundError`.
- Each list path filters correctly: bet, cycle, event_type,
  correlation_id.
- Pagination / ordering: `recorded_at ASC`, `event_id ASC` for
  ties. Inserted out-of-order rows are returned in order.
- `latest_non_superseded_rows_by_scope` — no-scope call raises
  `InvalidScopeError`; replaced events are filtered; unsuperseded
  events surface.
- `walk_supersession_chain_rows` — earliest-first; unknown
  starting event raises; cycle detection (via direct SQL forced
  self-reference) raises `SupersessionCycleError`.
- Append-only invariant — `dir(OpsEventRepository)` contains
  none of `update_row`, `delete_row`, `remove_row`, `edit_row`.

`tests/workflows/ops/v1/test_ops_store_adapter.py` (36 tests):

- `append_event` + `get_event` round-trip preserves the
  payload subclass and optional fields (correlation_id, notes,
  reason, from_state).
- Each `list_by_*` filters correctly.
- Supersession surface end-to-end: `latest_non_superseded_by_scope`
  filters replaced events; `walk_supersession_chain` returns
  earliest-first across three events.
- Domain validators:
  - Naive `datetime` rejected.
  - UTC `datetime` rejected.
  - ACDT (+10:30) accepted (alternative Adelaide-local offset).
  - `event_type` ↔ payload discriminator mismatch rejected
    (exercised via `model_validate` on a wire-shaped dict with a
    forged `event_type` string).
  - `bet_id=None` and `cycle_id=None` each rejected separately for
    `hedge_state_classification`.
  - Payload-level `from_state == to_state` rejection (with
    `from_state` not None).
  - `from_state=None` accepted with any `to_state`.
- `path` ↔ `source` consistency rule, parametrised across **all
  four** `ClassificationPath` values and four corresponding bad
  pairings each (12 reject cases + 4 accept cases).
- All six `HedgeState` values accepted as `to_state` (parametrised),
  paired with the appropriate path/source so the cross-rules hold.

---

## §4 — §7.2 post-baselines + §7.3 spot-check transcript

### §4.1 — §7.2 post-baselines

- `.venv/bin/pytest -q` — **881 passed, 2 failed in 3.48 s**. The
  two failures are the same pre-existing FB-inventory failures
  carried in §1.1; W15 did not introduce them and did not touch
  the modules involved. Delta vs §1.1: `+61` passing tests
  (= 9 schema + 16 repository + 36 adapter), zero new failures.
- `.venv/bin/lint-imports` — **5 contracts kept, 0 broken**
  (173 files, 422 dependencies analysed). The previously kept
  `workflows cannot import workflows` contract continues to hold
  with `workflows.ops` now listed.
- `git status --short` — delta vs §1.1 is **exactly** the §5
  anchors plus the two named edits; no other working-tree change.
  Full output in §6.

### §4.2 — §7.3 end-to-end spot-check transcript

In a temporary `:memory:` SQLite DB with the bets schema applied
first and one stub bets row inserted (`bet-acme-1` /
`cycle-acme-1`), the canonical DR-025 lifecycle was run through
`OpsStoreAdapter`. Verbatim transcript:

```
[1] SYSTEM_DEFAULT  event_id=38db1e34-8cb9-4b81-b017-95bade59bd29
    -> unhedged_unclassified
[2] AUTO_RESOLVE    event_id=01bf971f-8fc6-4f8f-8b89-35e6ef491303
    -> unhedged_deliberate
[3] OPERATOR        event_id=c2bac5f2-3250-4aa3-ba04-db9cdbc60a2e
    -> unhedged_oversight
    (reason='I meant to hedge that and forgot.')

latest_non_superseded_by_scope(bet_id=...): [event_3.event_id]
walk_supersession_chain(event_3): [event_1, event_2, event_3]
list_by_bet(bet-acme-1): [event_1, event_2, event_3]

Payload round-trip: intact (==)

W15 §7.3 spot-check OK.
```

Per-assertion outcomes:

- Append event 1 (log-time `SYSTEM_DEFAULT`): `from_state=None`,
  `to_state=UNHEDGED_UNCLASSIFIED`, `path=SYSTEM_DEFAULT`,
  `source=SYSTEM`. ✅
- Append event 2 (`AUTO_RESOLVE`):
  `from_state=UNHEDGED_UNCLASSIFIED`,
  `to_state=UNHEDGED_DELIBERATE`, `path=AUTO_RESOLVE`,
  `source=SYSTEM`, `supersedes_event_id=event_1`. ✅
- Append event 3 (retrospective `OPERATOR` oversight flag):
  `from_state=UNHEDGED_DELIBERATE`,
  `to_state=UNHEDGED_OVERSIGHT`, `path=OPERATOR`,
  `source=OPERATOR`, `reason='I meant to hedge that and
  forgot.'`, `supersedes_event_id=event_2`. ✅
- `latest_non_superseded_by_scope(bet_id="bet-acme-1")` returns
  `[event_3]` only — events 1 and 2 are filtered out by the LEFT
  JOIN. ✅
- `walk_supersession_chain(event_3.event_id)` returns
  `[event_1, event_2, event_3]` (earliest-first). ✅
- `list_by_bet("bet-acme-1")` returns all three events in
  `recorded_at`-ASC order. ✅
- `get_event(event_3.event_id) == event_3` — payload JSON
  round-trip through the discriminated-union dispatch is
  byte-faithful (`recorded_at` / `occurred_at` retain the
  `+09:30` offset; `from_state`, `to_state`, `path`, `reason`
  all preserved). ✅

---

## §5 — Findings

### f#1 — `.importlinter` independence-contract under-population (recorded, not normalised)

**Observed.** `.importlinter` lists exactly three modules under the
`workflows-independent` independence contract:
`workflows.bet_entry`, `workflows.burst_review`, and (now)
`workflows.ops`. Three other workflow packages exist in the repo —
`workflows.cash_flow`, `workflows.promos`, `workflows.balances` —
and are not listed. The brief §5.6 directed Code to register
`workflows.ops` only, run `lint-imports`, and surface the omission
of the other three as a finding rather than silently normalising
it.

**Status.** `lint-imports` reports 5 contracts kept / 0 broken
after the W15 edit. The independence contract is alive on the
three listed modules and silent on the three unlisted modules.
The latter are therefore not enforced as mutually-independent by
the contract today.

**Why it matters.** Either the omission is deliberate (perhaps
`workflows.balances` legitimately depends on `workflows.cash_flow`
and `workflows.promos` for its derivation chains per the
DR-019 S124 "derivation-chain pattern" — see
`workflows/balances/v1/balance_derivation.py` docstring) or it is
under-population that should be closed. Either way it sits below
this brief's scope; the brief §5.6 hard limit is explicit that
W15 must not add the other three.

**Triage owner.** Operator-Claude — separate brief if normalisation
is desired, or a docstring note in `.importlinter` if the
under-population is intentional.

### f#2 — Cross-schema row-factory inconsistency between `store/schema/bets.py` and the cash_flow/ops pattern (observation, not a W15 surface)

**Observed.** During the §7.3 / §3.2 smoke checks, the
`apply_migrations` helper in `store/schema/bets.py` (last touched
by W12.1) accesses `PRAGMA table_info` rows by name
(`row["name"]`), which requires `conn.row_factory =
sqlite3.Row` on the connection. The cash_flow / promos / ops
schema helpers use positional access (`row[1]`) and work without
the row factory being set. The W15 schema tests therefore set
`row_factory = sqlite3.Row` on the test connection (matching the
W14 cash_flow-schema tests' precedent) which is sufficient — but
this asymmetry is visible to any caller bootstrapping
`apply_bets_migrations` without setting the row factory.

**Status.** No effect on W15: tests pass, lint-imports green, the
shipped `SQLiteBetRecordStorage` set its own connection's
`row_factory = sqlite3.Row` in its `_connect`. The asymmetry is
inherited from the W12.1 surgical fix and the prior
`store/schema/bets.py` shape; W15 did not touch this code.

**Why it matters.** Modest — it's a "where you need to set
`row_factory` to bootstrap depends on which schema migration you
call" inconsistency. Could surface in a future caller that lifts
the migration helpers in a non-test path.

**Triage owner.** Operator-Claude — either accept (the
SQLiteBetRecordStorage caller sets the factory; the test
fixtures set the factory; nobody else calls
`apply_bets_migrations` directly) or fold a one-line `row_factory =
sqlite3.Row` into `store/schema/bets.apply_migrations` in a
separate maintenance pass. Not a W15 surface.

### f#3 — `HedgeState` home: lives in `domain/ops` today, relocation trigger documented

**Observed.** Per brief §5.1 home decision, `HedgeState` lives in
`domain/ops/__init__.py` because the ops log is the only consumer
today. The DR-025 sequencing point (c) names the
`hedge_state` column on the `bets` row as later work; when that
lands `HedgeState` becomes domain vocabulary for both `domain.bets`
and `domain.ops`. The relocation candidacy is documented in the
`domain/ops` module docstring (third paragraph of the home
decision note).

**Status.** Informational; not a defect. Code did NOT pre-emptively
place `HedgeState` in `domain/bets`.

**Triage owner.** Whoever picks up DR-025 sequencing point (c).
The relocation, if made, is a single-file move plus an
update to the `domain.ops` re-export; no consumer code needs to
change beyond the import line.

### f#4 — Two pre-existing pytest failures carried (not introduced by W15)

**Observed.**
`tests/workflows/balances/v1/test_balance_derivation.py::test_balance_free_bet_inventory_surfaces`
and
`tests/workflows/promos/v1/test_promo_derivations.py::test_inventory_single_freebie_available`
failed both before and after the W15 build. Both concern
`compute_free_bet_inventory` (in `workflows/promos/v1/`), an
untouched module. Recorded for operator-Claude awareness; the
wiring issue is upstream of W15 (W12.1 reported the balances-side
failure too).

**Triage owner.** Operator-Claude — out of W15 scope; separate
follow-up against `compute_free_bet_inventory`.

---

## §6 — Self-assessment

### §6.1 — Length and pacing

The work fit one bounded session comfortably. No anchor ran larger
than expected; the W14 / W14.1 templates carried the structure
end-to-end. The single substantive judgement call was the §5.1
path↔source consistency model validator location — it sits on
`OpsEventBase` rather than `HedgeStateClassificationPayload`
because the payload alone cannot see the parent `source` header.
This matches the brief's wording ("model-level on `OpsEventBase`,
see below").

### §6.2 — Sequencing deviations

None. The §6 dependency order ran clean: domain → schema →
repository → adapter → `store/__init__.py` edit → `.importlinter`
edit + lint-imports → tests → §7.2 + §7.3 + report.

### §6.3 — Out-of-scope edges

- I did not touch the root `ops/` package (§9 hard limit).
- I did not add `workflows.cash_flow`, `workflows.promos`, or
  `workflows.balances` to the independence contract (§5.6 hard
  limit; recorded as f#1).
- I did not introduce a `hedge_state` column on `bets`, build any
  classifier-engine code, or touch settlement / Burst Review /
  bet-entry code (§9).
- I did not modify W12 / W12.1 territory (§9).
- I did not perform passing refactors anywhere (§9).

### §6.4 — Length note

Report length ~390 lines (target 200–400 per §8). Within target.

---

## §7 — Final `git status --short`

```
 M .importlinter
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
?? domain/ops/
?? domain/promos/
?? scripts/
?? store/repositories/accounts.py
?? store/repositories/bets.py
?? store/repositories/cash_flow.py
?? store/repositories/ops.py
?? store/repositories/promos.py
?? store/schema/accounts.py
?? store/schema/bets.py
?? store/schema/cash_flow.py
?? store/schema/ops.py
?? store/schema/promos.py
?? tests/clients/betfair_client/v1/test_account_funds.py
?? tests/clients/betfair_client/v1/test_current_orders.py
?? tests/clients/betfair_client/v1/test_market_catalogue.py
?? tests/scripts/
?? tests/store/
?? tests/ui/
?? tests/workflows/
?? ui/api/
?? ui/web/
?? workflows/balances/
?? workflows/bet_entry/v1/
?? workflows/cash_flow/
?? workflows/ops/
?? workflows/promos/
```

Delta vs §1.1 (the §7.1 baseline) is **exactly**:

- `.importlinter` moved from clean to **modified** (single-line
  addition of `    workflows.ops`).
- `store/__init__.py` remained **modified** with one extra import
  block + `__all__` entry (additive; the file's pre-session M
  flag is from the W10 lift content).
- New untracked top-level paths: `domain/ops/`,
  `store/schema/ops.py`, `store/repositories/ops.py`,
  `workflows/ops/`.
- New files inside the already-untracked `tests/store/` and
  `tests/workflows/` umbrellas:
  `tests/store/repositories/test_ops_schema.py`,
  `tests/store/repositories/test_ops_repository.py`,
  `tests/workflows/ops/__init__.py`,
  `tests/workflows/ops/v1/__init__.py`,
  `tests/workflows/ops/v1/test_ops_store_adapter.py`
  (these don't surface as new top-level `??` entries because the
  parent dirs were already untracked).

Nothing else moved. No `git add`, `commit`, `stash`, `restore`,
`checkout`, or `reset` was issued during the session.

**End of report.**
