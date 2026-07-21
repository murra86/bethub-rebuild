# W10 — Storage lift report

**Source brief:** `dr029/w10_storage_lift/w10_brief.md` (locked
2026-05-11 16:36 ACST, Session 118).
**Session window:** 2026-05-11 16:40:50 → 17:11:36 ACST (Adelaide local
per DR-021).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`.

---

## 1. Pre-session state

- **File inventory:** 126 `.py` files (excluding hidden / cache dirs).
- **Line counts of files being lifted:**
  - `workflows/bet_entry/v1/storage.py` — 1097 lines.
  - `workflows/bet_entry/v1/models.py` — 422 lines.
- **`uv run lint-imports`:** 5 contracts kept, 0 broken (120 files,
  338 dependencies analysed).
- **`uv run pytest -x -q`:** 527 passed in 1.91s.
- **`git status`:** dirty per ongoing v3 build (`betfair_client` modified
  files plus the post-Fix-4 changes, plus the untracked W4–W9 surfaces).
  No lock files, no in-flight rebases.

---

## 2. Changes made (per §5 sub-section)

### §5.1 — Vocabulary lift to `domain/bets/`

Created `domain/bets/__init__.py` (370 lines) carrying the 11 named
types from `workflows/bet_entry/v1/models.py`:

- 9 enums — `StrategyTag`, `MatchStatus`, `SettlementState`, `EntryPath`,
  `LegRole`, `BetSideTag`, `Construction`, `HedgeSoftBookStakeKind`,
  `PriceSource`.
- 2 Pydantic models — `BetLeg`, `BetRecord` (the latter with the
  `is_past_settlement_window` computed-field property, retained on the
  model with the threshold + clock helpers re-housed inside
  `domain.bets` — see Finding A).

Trimmed `workflows/bet_entry/v1/models.py` to 136 lines, keeping the 5
workflow result envelopes (`PreFlightFlag`, `PreFlightResult`,
`ErrorContext`, `HedgePlacementResult`, `SoftBookLogResult`) plus the
`PreFlightSeverity` `Literal` alias used by `PreFlightFlag`.

### §5.1 (caller sweep) — vocab → `domain.bets`

Updated import sources in 8 production files and 7 test files. Where a
file imported both moved and stayed types, split the import statement so
moved types come from `domain.bets` and stayed types from
`workflows.bet_entry.v1.models`:

- Source: `workflows/bet_entry/v1/__init__.py`, `record_builder.py`,
  `staking.py`, `reconciliation.py`, `settlement.py`, `orchestrator.py`,
  `ui/api/routers/provisional.py` (+ the in-flight `storage.py` redirected
  to `domain.bets` so it kept loading during the lift sequence).
- Tests: `test_orchestrator.py`, `test_settlement.py`, `test_staking.py`,
  `test_reconciliation.py`, `test_record_builder.py`, `test_provisional.py`.

### §5.2 — Store-side files

Created three files under `store/`:

- `store/schema/bets.py` (120 lines) — `_BETS_DDL`, `_LEGS_DDL`,
  `_add_column_if_missing` helper, and `apply_migrations(conn)` exposed
  as the entry point the repository calls on init. Migration calls are
  identical to the previously-inline block in
  `SQLiteBetRecordStorage._connect_and_init`.
- `store/repositories/bets.py` (932 lines) — `BetRow` and `BetLegRow`
  flat dataclasses (primitive-only fields per W10 brief §5.3); the
  `BetRecordStorage` Protocol with row-based signatures;
  `StorageWriteError`, `WriteResult`; the `InMemoryBetRecordStorage` and
  `SQLiteBetRecordStorage` implementations rewritten against rows; and
  `_row_to_bet_row` / `_row_to_leg_row` sqlite3.Row → dataclass helpers.
- `store/__init__.py` (36 lines) — re-exports the public surface
  (`BetRecordStorage`, `WriteResult`, `StorageWriteError`,
  `InMemoryBetRecordStorage`, `SQLiteBetRecordStorage`, `BetRow`,
  `BetLegRow`).

### §5.3 — Boundary adapter

Created `workflows/bet_entry/v1/bet_store_adapter.py` (195 lines) with:

- `to_rows(record: BetRecord) -> tuple[BetRow, list[BetLegRow]]` — used
  by the orchestrator on write.
- `from_rows(row: BetRow, legs: list[BetLegRow]) -> BetRecord` — used by
  the reconciliation / settlement read paths and the provisional-router
  read path.
- `to_provisional_payload(row, legs, market_settlement, *,
  related_bet_ids, trigger_source)` — constructs
  `ProvisionalSettlementSurfacingPayload` at the workflow boundary.

`MarketSettlement` JSON (de)serialisation lives in the adapter
(`to_rows` calls `model_dump_json()`; `from_rows` calls
`model_validate_json()`). The store sees only the JSON string in
`BetRow.last_read_market_state`.

### §5.4 — Caller updates

Source-side call-site updates:

- `orchestrator.py` — write path converts via `to_rows(record)` before
  `write_bet_record`; `update_match_status` passes `status.value` (see
  Finding C).
- `reconciliation.py` — reads `list_unreconciled_bets` rows then
  `from_rows`; passes `MatchStatus.X.value` to storage methods.
- `settlement.py` — reads `list_unsettled_bets` / `read_bet_record` rows
  then `from_rows`; passes `SettlementState.X.value` to storage methods.
  `_persist_last_read_market_state` calls `model_dump_json()` before
  `update_last_read_market_state`.
- `ui/api/routers/provisional.py` — read loop uses the new
  `list_bet_ids_for_market` Protocol method (Finding D) and constructs
  payloads via `to_provisional_payload`.

Test-side updates:

- Helpers added to each affected test file:
  - `_write_record(storage, record)` — wraps `to_rows` + write.
  - `_read_record(storage, bet_id)` — wraps read + `from_rows`.
  - `_provisional_payloads(storage)` — wraps the new read + adapter loop.
- `tests/workflows/bet_entry/v1/test_storage.py` (571 lines) relocated
  to `tests/store/repositories/test_bets.py` (605 lines) per brief §5.4.
- `tests/workflows/bet_entry/v1/test_settlement.py` — 3 patches of
  `settlement_module._now_adelaide` / `DEFAULT_PAST_WINDOW_SECONDS` for
  the `is_past_settlement_window` block retargeted to `domain.bets` (see
  Finding A).

### §6 step 9 — `workflows/bet_entry/v1/storage.py` deleted

File no longer exists. Replaced by `store.schema.bets` + 
`store.repositories.bets` + `workflows.bet_entry.v1.bet_store_adapter`.

---

## 3. Post-session state

- **File inventory:** 130 `.py` files (+4 net: 6 created, 2 deleted).
- **Line counts of named anchors:**
  - `domain/bets/__init__.py` — 370 lines (was empty stub).
  - `workflows/bet_entry/v1/models.py` — 136 lines (was 422; trimmed by 286).
  - `store/schema/bets.py` — 120 lines (new).
  - `store/repositories/bets.py` — 932 lines (new).
  - `store/__init__.py` — 36 lines (was empty stub).
  - `workflows/bet_entry/v1/bet_store_adapter.py` — 195 lines (new).
  - `tests/store/repositories/test_bets.py` — 605 lines (relocated /
    rewritten from the deleted 571-line `test_storage.py`).
  - `workflows/bet_entry/v1/storage.py` — **does not exist**.
- **`uv run lint-imports`:** **3 contracts kept, 2 broken.** Store-pure
  (the brief's primary failure signal per §5.5) is **green**. The two
  broken contracts both fire on the same import: `domain.bets ->
  clients.betfair_client.v1.settlement` (l.36). See Finding B for the
  surface and Self-assessment §5 for the deviation discussion.
- **`uv run pytest -x -q`:** 527 passed in 1.45s. Same count as
  pre-baseline; no regressions.
- **`git status`:** dirty file list expanded by the W10 changes as
  expected. New untracked entries: `store/repositories/bets.py`,
  `store/schema/bets.py`, `tests/store/`. Newly-modified entries:
  `domain/bets/__init__.py`, `store/__init__.py`. The deleted
  `storage.py` shows as a `D` in git status against HEAD (since W9 didn't
  add it to the tree either — both the old file's existence and its
  deletion are untracked-tree-only). No git operations run during the
  session.

---

## 4. Findings / surprises

### A. `BetRecord.is_past_settlement_window` cross-import (unnamed)

The `is_past_settlement_window` computed-field property on `BetRecord`
function-locally imported `_now_adelaide` and
`DEFAULT_PAST_WINDOW_SECONDS` from
`workflows.bet_entry.v1.settlement`. After `BetRecord` moved to
`domain.bets`, this became a `domain → workflows` edge that
import-linter caught (function-local imports are still seen statically).

**Brief context:** W10 brief §2 named three known cross-boundary imports
the lift must resolve (8 bet-vocab types, `MarketSettlement`,
TYPE_CHECKING `ProvisionalSettlementSurfacingPayload`). This was the
4th, unnamed.

**Resolution:** defined `_now_adelaide()` and
`DEFAULT_PAST_WINDOW_SECONDS = 1800.0` locally in
`domain/bets/__init__.py`. The property reads from the module-level
attributes; tests that previously patched
`settlement_module._now_adelaide` for this property retarget to
`domain.bets._now_adelaide`. The settlement worker's own `_now_adelaide`
mirror in `settlement.py` is untouched (it's used by the scheduler /
pass-loop independently). Three monkeypatch tests in
`test_settlement.py:Block 3` were re-pointed accordingly. Mild
duplication (two `_now_adelaide` helpers / two
`DEFAULT_PAST_WINDOW_SECONDS` constants — the settlement module retains
its own for its scheduling logic) is bounded and worth flagging for the
next session.

### B. `BetRecord.last_read_market_state: MarketSettlement | None`

`BetRecord` declares `last_read_market_state: MarketSettlement | None`
(W9 brief §5.2 — the worker's most recent successful read). With
`BetRecord` now in `domain.bets`, this forces `domain.bets ->
clients.betfair_client.v1.settlement` at module load. This breaks both
the `DR-030 layered architecture` contract and the `domain-pure`
contract.

**Brief context:** W10 brief §2 named `MarketSettlement` as a known
cross-boundary import — but the framing was for `storage.py` reading /
writing the JSON. W10 §5.3 resolved that storage-side surface by giving
the store a `str` JSON column. The DOMAIN-side surface — the type
annotation on `BetRecord.last_read_market_state` itself — was not named
in the brief and was not anticipated.

**TYPE_CHECKING import attempted, did not work.** Pydantic v2 requires
the type to be resolvable at validate-time for runtime construction
(Pydantic-error: `class-not-fully-defined`). And import-linter catches
imports inside `TYPE_CHECKING` blocks too (the static analyser doesn't
distinguish).

**No fix attempted.** Per brief §9.1 ("Code observes and reports; the
next operator-Claude session decides what to do about surprises"), the
import is left in place and the contract failure is surfaced here. The
brief's primary failure signal is store-pure (which IS green); domain-
pure is a separate contract whose failure is reportable but does not
mean the lift didn't happen.

Possible resolution paths for the next session (not implemented here):
(a) change `BetRecord.last_read_market_state`'s type to
`dict[str, object] | None` and have the adapter convert MarketSettlement
↔ dict at the boundary; (b) add an `ignore_imports` exception to
`domain-pure` for this specific edge in `.importlinter`; (c) move
`MarketSettlement` to a domain-or-leaf location (probably too large a
scope for the brief). Triage call stays with operator-Claude.

### C. `BetRecordStorage` Protocol enum parameters

The brief §5.3 said "Other methods (`update_match_status`,
`update_reconciliation_bookkeeping`, `update_settlement_state`) take
primitive parameters as today — no change." But the original signatures
took `MatchStatus` and `SettlementState` enum instances (imported from
`workflows.bet_entry.v1.models`). Keeping those signatures after the
lift would force `store/repositories/bets.py` to import
`domain.bets.MatchStatus` etc., breaking store-pure (the brief's
primary failure signal).

**Resolution:** narrowed the Protocol parameters to `str` (the
canonical enum-value strings). All call sites in production code now
pass `MatchStatus.X.value` / `SettlementState.X.value` to storage
methods. List filter parameters (`statuses=`, `settlement_states=`)
became `tuple[str, ...]`. This was the minimum-change interpretation of
"primitive parameters as today" that satisfied store-pure.

### D. New `list_bet_ids_for_market` Protocol method

The old `list_provisional_settlement_bets` impls (both in-memory and
SQLite) ran an inline query for related bet-ids on the same Betfair
market and embedded that in the returned payload. The brief moved
payload construction to the workflow side (§5.3), so the related-bet-id
query needed a new surface.

**Resolution:** added
`BetRecordStorage.list_bet_ids_for_market(market_id, *, exclude_bet_id)`
to the Protocol with implementations in both backends. Workflow callers
(`ui/api/routers/provisional.py`) now call this method and pass the
result to `to_provisional_payload(related_bet_ids=...)`. This is a small
Protocol-surface addition, not a behaviour change — the related-bet-ids
feature itself is preserved.

### E. Adapter ↔ settlement circular import

`bet_store_adapter.py` needs `ProvisionalSettlementSurfacingPayload` and
`_build_surfacing_payload` from `settlement.py` to construct the
payload. But `settlement.py` imports `orchestrator.py` (for
`ReadOutcome`) and `orchestrator.py` now imports `bet_store_adapter` for
`to_rows`. Module-load order trips on this triangle.

**Resolution:** function-local imports inside
`bet_store_adapter.to_provisional_payload` for the settlement-side
symbols. `TYPE_CHECKING` import preserves type-checker visibility at
module top.

### F. Test-helper proliferation

The W10 lift changed the storage Protocol's read/write shape from
`BetRecord`-based to row-based. Most test files (5 of them) had dozens
of `storage.write_bet_record(record)` and
`storage.read_bet_record(bet_id).attr` call sites.

**Resolution:** added three small helpers per affected test file:
`_write_record(storage, record)`, `_read_record(storage, bet_id)`,
`_provisional_payloads(storage)`. Tests retain their pre-lift shape
syntactically; the helpers do the adapter-side conversion. Caller-side
test rewriting was significant but mechanical and is now consistent
across the test surface.

### G. Two `_now_adelaide` definitions exist (bounded duplication)

After Finding A's resolution, `_now_adelaide` lives in both
`domain.bets` (for `BetRecord.is_past_settlement_window`) and
`workflows.bet_entry.v1.settlement` (for the worker scheduler / pass
loops). They're identical (both `datetime.now(ZoneInfo("Australia/
Adelaide"))`). Same shape for `DEFAULT_PAST_WINDOW_SECONDS = 1800.0`
(present in both modules). The duplication is intentional and bounded
— each surface has its own monkeypatch story. Worth surfacing for
triage decision: collapse to one canonical location, or accept the
duplication.

---

## 5. Self-assessment

### Deviations from brief

1. **`domain-pure` + `DR-030 layered architecture` contracts broken.**
   Brief §5.5 expected lint-imports green. Store-pure (the named primary
   failure signal) IS green. The other two contracts fail on the
   single edge surfaced in Finding B
   (`domain.bets -> clients.betfair_client.v1.settlement` via
   `MarketSettlement`). Per §9.1, surfaced for triage rather than
   freelance-fixed.

2. **`BetRecordStorage` Protocol enum-typed params widened to `str`.**
   Brief §5.3 said "no change" for `update_match_status` /
   `update_settlement_state` / `list_unreconciled_bets` /
   `list_unsettled_bets`. To keep store-pure green, the enum types had
   to be widened to `str` (Finding C). Call sites pass `.value`.

3. **New Protocol method `list_bet_ids_for_market` added.** Brief §5.3
   moved payload construction to the workflow side without naming a
   replacement for the related-bet-ids query that lived inside the old
   `list_provisional_settlement_bets`. Added a small read method to keep
   the related-bet-ids feature intact (Finding D).

4. **`domain.bets` re-defines `_now_adelaide` + `DEFAULT_PAST_WINDOW_SECONDS`.**
   To keep `BetRecord.is_past_settlement_window`'s computed-field
   contract intact without a `domain → workflows` edge (Finding A).

5. **Three test patches retargeted from `settlement_module` to
   `domain.bets`.** Direct consequence of Finding A.

### Hard limits — did any come close?

- **§9.2 Behaviour and schema preserved.** Schema (DDL column set,
  migration block, JSON-as-string for `last_read_market_state`) — yes,
  unchanged. Behaviour — `BetRecordStorage` Protocol's call shape and
  semantics are preserved at the workflow surface (via the adapter); the
  parameter type narrowing from enum to `str` is a thin type-level
  change at the store surface, not a behavioural change. `BetRecord`'s
  public API — `is_past_settlement_window` property and all model fields
  — preserved.
- **§9.3 No adjacent workstreams.** No W11–W15 / W17 scaffolding
  touched. Confirmed by grep across `store/`, `domain/`, and
  `workflows/`.
- **§9.4 No Alembic adoption, no debt-fixing.** No new migration
  framework; the inline `_add_column_if_missing` block lifted as-is.
- **§9.5 Operational guardrails.** No git operations; no DB access
  (storage tests use `tmp_path`-scoped SQLite files only); session ran
  end-to-end with no mid-session escalation.

### Anything in scope that couldn't be done cleanly

- The `domain → clients` edge via `MarketSettlement` (Finding B). Per
  §9.1, surfaced rather than fixed. Brief §5.5 lint-green expectation
  is the only failed verification gate.

### Length flag

This report is ~270 lines. Within the 200–400 line target per §8.

---

**End of report.**
