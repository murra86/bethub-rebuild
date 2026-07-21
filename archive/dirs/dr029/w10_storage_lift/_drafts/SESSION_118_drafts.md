# W10 storage lift brief — locked drafts (Session 118)

**Purpose:** Per Cat 2 "persist drafted-but-not-assembled
artefact content to scratch" — locked section drafts from
Session 118's W10 brief drafting, carried on disk so a fresh
session can resume mid-draft if needed.

**Final brief lands at:**
`dr029/w10_storage_lift/w10_brief.md` when locked.

**Anchor precedent:** Sessions 35/36 surgical-fix briefs (named
changes in dependency order, hard limits explicit, pre-and-post
empirical verification).

---

## §1 — What this brief is and is not

This brief commissions a structural lift: move bet-vocabulary
types from `workflows/bet_entry/v1/models.py` into
`domain/bets/`, move `storage.py` into `store/` (split across
`store/schema/` and `store/repositories/` per DR-030), redesign
the storage boundary so workflows convert between domain types
and store row types at the boundary, and update all caller
imports. No behaviour change — the `BetRecordStorage` Protocol
surface is functionally preserved, the `bets` + `bet_legs`
schema columns lift as-is, and the inline
`_add_column_if_missing` migration block stays as-is. Single
Code session. Surprises become findings in the report, not
blockers — the next operator-Claude session triages.

Out of scope for this brief: Alembic adoption (separate later
brief — flagged §10), schema changes to the W4 / W5 / W6 /
W6.5 / W9 columns, redesign of the Protocol surface, and the
workflow result envelopes (`PreFlightResult`,
`HedgePlacementResult`, `SoftBookLogResult`) which stay
workflow-internal.

---

## §2 — Why this work exists

Per `v3_build_picture.md` (Session 117 re-cut), W10 is the
storage lift to top-level `store/` per DR-030 (the v3 repo
layout decision locked Session 79). It is the first brief of
v3 build proper's operational-store band and unblocks W11–W15
(operational-store sub-streams: accounts + account-at-book per
DR-022, balances, promos with cycle linkage per DR-032,
transactions, operations log).

Session 118 pre-flight grounding surfaced that the lift cannot
be a simple file-move. `storage.py` currently imports:

- Eight bet-vocabulary types from `workflows.bet_entry.v1.models`
  (`BetRecord`, `BetLeg`, `MatchStatus`, `EntryPath`, `LegRole`,
  `PriceSource`, `SettlementState`, `StrategyTag`).
- `MarketSettlement` from `clients.betfair_client.v1.settlement`
  (read/write the `last_read_market_state` column as JSON).
- (TYPE_CHECKING) `ProvisionalSettlementSurfacingPayload` from
  `workflows.bet_entry.v1.settlement` (returned from
  `list_provisional_settlement_bets`).

All three import directions violate DR-030's `store-pure`
import-linter contract the moment `storage.py` lands in
`store/`. W10's scope is therefore the structural lift plus
the minimal boundary rework required to satisfy `store-pure`
without changing runtime behaviour.

---

## §3 — Pre-reads

**Required reads** (Code reads before starting):

- `decisions.md` §DR-030 (v3 repo layout and import-graph
  rules — the load-bearing contract this brief satisfies).
- `decisions.md` §DR-032 (canonical-reference-layer for all
  bet records — schema source for the `bets` + `bet_legs`
  tables being lifted).
- `.importlinter` at the v3 repo root (the actual layered
  architecture contract Code's edits must keep green).
- `workflows/bet_entry/v1/storage.py` (the file being lifted —
  1097 lines).
- `workflows/bet_entry/v1/models.py` (the file being split —
  422 lines; eleven of sixteen classes are bet vocabulary
  destined for `domain/bets/`).

**Reference-only** (read on demand):

- `decisions.md` §DR-031 (v3 tech stack — Alembic is locked as
  the migration tool but is out of scope for this brief).
- `decisions.md` §DR-022 (book/account/account-at-book
  vocabulary — background context for downstream W11–W15 but
  not load-bearing for this lift).
- `v3_build_picture.md` (W10 row + dependency graph context).
- `architecture.md` (orientation; not load-bearing for the
  edits themselves).

---

## §4 — System access

- **Mac filesystem, read-write** at
  `/Users/tim/Desktop/Projects/bethub-v3/` — the v3 codebase
  root. Edits to source files, test files, and the
  `.importlinter` config are in scope per §5.
- **No database access.** This brief does not read or write
  any SQLite database. The `bets.db` operational store is
  schema-only territory at this stage — no operational data
  to preserve.
- **No external API access** (no Betfair, no Racing API, no
  VPS).
- **Git operations:** the v3 repo working tree state is
  verified at session start per §9's dirty-tree handling.
  Code runs no `git add`, `git commit`, `git stash`,
  `git restore`, `git checkout` (file-targeted), or
  `git reset` during the session.
- **Timestamps:** Adelaide local time (ACST/ACDT) per DR-021
  for every time-of-day reference in the report.

---

## §5 — Substantive scope

### §5.1 — Split `models.py` (bet vocabulary to `domain/bets/`)

Move eleven types from
`workflows/bet_entry/v1/models.py` into a new module
`domain/bets/__init__.py`:

- *Enums (9):* `StrategyTag`, `MatchStatus`, `SettlementState`,
  `EntryPath`, `LegRole`, `BetSideTag`, `Construction`,
  `HedgeSoftBookStakeKind`, `PriceSource`.
- *Pydantic models (2):* `BetLeg`, `BetRecord`.

Five types stay in `workflows/bet_entry/v1/models.py`:
`PreFlightFlag`, `PreFlightResult`, `ErrorContext`,
`HedgePlacementResult`, `SoftBookLogResult`. These are workflow
result envelopes, not bet vocabulary.

The eleven moved types become importable as
`from domain.bets import BetRecord, BetLeg, MatchStatus, …` —
matches the package-root export pattern already used by
`clients/` and `store/`.

`ProvisionalSettlementSurfacingPayload` (currently in
`workflows/bet_entry/v1/settlement.py`) stays in workflows —
resolved at the boundary in §5.3.

### §5.2 — Move storage to `store/`

Source: `workflows/bet_entry/v1/storage.py` (1097 lines).
Final state: deleted.

Destinations:

- `store/schema/bets.py` — `_BETS_DDL`, `_LEGS_DDL`,
  `_add_column_if_missing` helper, and the migration block
  currently inline in `SQLiteBetRecordStorage._connect_and_init`.
  Migration block exposed as a module-level `apply_migrations(
  conn)` function the repository calls on init.
- `store/repositories/bets.py` — `BetRecordStorage` Protocol,
  `StorageWriteError`, `WriteResult`, `InMemoryBetRecordStorage`,
  `SQLiteBetRecordStorage`, and the `_row_to_record`,
  `_row_to_leg` helpers (renamed to `_row_to_bet_row`,
  `_row_to_leg_row` per §5.3's primitive-row shape).
- `store/__init__.py` — re-export the public surface
  (`BetRecordStorage`, `WriteResult`, `StorageWriteError`,
  `InMemoryBetRecordStorage`, `SQLiteBetRecordStorage`).

### §5.3 — Store row types and boundary conversion

Store declares two flat dataclass row types in
`store/repositories/bets.py`, fields-as-primitives only (str,
int, float, Decimal, datetime, None — plus JSON-as-string for
the `last_read_market_state` column):

- `BetRow` — mirrors the `bets` table columns one-for-one.
- `BetLegRow` — mirrors the `bet_legs` table columns
  one-for-one.

`BetRecordStorage` Protocol method signatures change to use
these row types:

- `write_bet_record(self, row: BetRow, leg_rows: list[BetLegRow])
  -> WriteResult` — replaces single-`BetRecord` parameter.
- `read_bet_record(self, bet_id: str) -> tuple[BetRow,
  list[BetLegRow]] | None` — replaces `BetRecord | None`.
- `list_unreconciled_bets(...)` returns `list[tuple[BetRow,
  list[BetLegRow]]]` — replaces `list[BetRecord]`.
- `list_unsettled_bets(...)` same shape.
- `list_provisional_settlement_bets(...)` returns
  `list[tuple[BetRow, list[BetLegRow]]]` — workflow callers
  construct `ProvisionalSettlementSurfacingPayload` themselves
  from the rows. This is the resolution for the TYPE_CHECKING
  circular: payload construction is workflow concern, not store
  concern.
- `update_last_read_market_state(..., last_read_market_state:
  str | None)` — takes the JSON string directly. Workflow
  serialises `MarketSettlement` to JSON before calling.
- Other methods (`update_match_status`,
  `update_reconciliation_bookkeeping`,
  `update_settlement_state`) take primitive parameters as today
  — no change.

Conversion module: new file
`workflows/bet_entry/v1/bet_store_adapter.py` housing two
functions plus the payload constructor:

- `to_rows(record: BetRecord) -> tuple[BetRow, list[BetLegRow]]`
  — used by orchestrator on write.
- `from_rows(row: BetRow, legs: list[BetLegRow]) -> BetRecord`
  — used by readers (reconciliation, settlement, provisional
  API router).
- `to_provisional_payload(row: BetRow, legs: list[BetLegRow],
  market_settlement: MarketSettlement | None)
  -> ProvisionalSettlementSurfacingPayload` — constructs the
  payload at the workflow side, with `MarketSettlement` resolved
  from the stored JSON string by the adapter.

`MarketSettlement` JSON (de)serialisation now lives in
`bet_store_adapter.py`, not in `store/repositories/bets.py`.
Store sees only the JSON string.

### §5.4 — Caller updates

Ten files update their imports:

- `workflows/bet_entry/v1/orchestrator.py` — import
  `BetRecordStorage`, `WriteResult` from
  `store.repositories.bets`; import `to_rows` from
  `workflows.bet_entry.v1.bet_store_adapter`; convert
  `BetRecord` to rows before `write_bet_record` calls.
- `workflows/bet_entry/v1/reconciliation.py` — import
  `BetRecordStorage` from `store.repositories.bets`; import
  `from_rows` from
  `workflows.bet_entry.v1.bet_store_adapter`; convert rows
  back to `BetRecord` after reads.
- `workflows/bet_entry/v1/settlement.py` — same shape as
  reconciliation; plus `to_provisional_payload` for the
  provisional-settlement query.
- `workflows/bet_entry/v1/__init__.py` — update re-export paths.
- `ui/api/routers/provisional.py` — import storage symbols from
  `store.repositories.bets`; use `from_rows` and
  `to_provisional_payload`.
- `tests/ui/api/test_provisional.py` — update import paths.
- `tests/workflows/bet_entry/v1/test_storage.py` — relocates to
  `tests/store/repositories/test_bets.py`. Update import paths.
- `tests/workflows/bet_entry/v1/test_orchestrator.py` — update
  storage import paths; add adapter usage where needed.
- `tests/workflows/bet_entry/v1/test_settlement.py` — same.
- `tests/workflows/bet_entry/v1/test_reconciliation.py` — same.

### §5.5 — Import-linter verification

After all edits, Code runs `uv run lint-imports` (or the
equivalent command per `pyproject.toml`). Output must be green:
all five contracts (DR-030 layered architecture, domain-pure,
store-pure, contracts-leaf, workflows-independent) pass.

Code reports any contract that fails. A failure here is the
brief's primary failure signal — the lift is incomplete if
`store-pure` does not hold.

---

## §6 — Sequencing within session

In dependency order:

1. Create `domain/bets/__init__.py` with the eleven moved
   types (copied from `models.py`).
2. Update `workflows/bet_entry/v1/models.py` to remove the
   eleven moved types; keep the five workflow result envelopes.
3. Sweep all callers (source + tests) updating
   `from workflows.bet_entry.v1.models import …` to
   `from domain.bets import …` where the imports were among
   the eleven moved types. Where a file imports both moved and
   stayed types, split the import statement.
4. Create `store/schema/bets.py` with the DDL constants,
   `_add_column_if_missing` helper, and `apply_migrations(conn)`
   function.
5. Create `store/repositories/bets.py` with the Protocol,
   row types, impls, and row-conversion helpers (primitive-only
   contents — no project imports).
6. Update `store/__init__.py` to re-export the public surface.
7. Create `workflows/bet_entry/v1/bet_store_adapter.py` with
   `to_rows`, `from_rows`, `to_provisional_payload`.
8. Update all callers of storage (per §5.4) — source files
   first, then test files.
9. Delete `workflows/bet_entry/v1/storage.py`.
10. Run `uv run lint-imports` — must be green.
11. Run `uv run pytest` — must be green.

Code may deviate from this order if a different sequence is
operationally cleaner; the dependency graph (domain types →
store types → adapter → callers → delete source) is the
load-bearing constraint, not the step numbering.

---

## §7 — Empirical verification

Pre-session baseline (captured at session start):

- File inventory: `find /Users/tim/Desktop/Projects/bethub-v3
  \( -path '*/.*' -prune \) -o -type f -name '*.py' -print
  | wc -l` — record count.
- `wc -l workflows/bet_entry/v1/storage.py
  workflows/bet_entry/v1/models.py` — record line counts.
- `uv run lint-imports` — record output (expected: green).
- `uv run pytest -x -q` — record output (expected: green).
- `git status` — record working tree state.

Post-session verification (must hold at session close):

- `workflows/bet_entry/v1/storage.py` does not exist.
- `domain/bets/__init__.py`, `store/schema/bets.py`,
  `store/repositories/bets.py`,
  `workflows/bet_entry/v1/bet_store_adapter.py` all exist with
  non-empty content.
- `wc -l workflows/bet_entry/v1/models.py` — reduced; the
  eleven moved types removed.
- `uv run lint-imports` — green.
- `uv run pytest -x -q` — green (same test count as pre, or
  higher if Code added tests for the adapter; not lower).
- `git status` — dirty file list is the expected set (files
  named in §5) and only that set.

---

## §8 — Output spec

Single file at `dr029/w10_storage_lift/w10_report.md`.

Section structure:

1. **Pre-session state** — file inventory, line counts, lint
   and test baselines, working tree state.
2. **Changes made** — per §5 sub-section: files created,
   modified, deleted, with line-count deltas.
3. **Post-session state** — file inventory, line counts, lint
   and test verification, working tree state.
4. **Findings / surprises** — anything Code surfaced during
   execution that wasn't in scope but is worth flagging
   (unexpected callers, type-hint complications, test
   failures resolved, etc.).
5. **Self-assessment** — deviations from the brief, anything
   in scope that couldn't be done cleanly, any §9 hard limits
   that came close to being touched.

Length anticipation: 200–400 lines. The report does not
contain recommendations beyond findings — next operator-Claude
session triages.

---

## §9 — Hard limits (non-negotiable)

### §9.1 Operating principle

Code observes and reports; the next operator-Claude session
decides what to do about surprises. Code runs the lift,
surfaces anomalies in its report, and walks away — operator-
Claude then triages each finding and routes it. Code does not
freelance fixes inside this session even when something looks
straightforwardly fixable; the routing call stays with the
operator. The hard limits below give Code the explicit scope-
protection to honour the principle.

### §9.2 Behaviour and schema preserved exactly as-is

No new functionality, no changes to the `bets` table or
`bet_legs` table column set, no renamed or removed fields, no
migration consolidation. The W4 / W5 / W6 / W6.5 / W9 column
additions lift across as-is. If Code spots something that
looks improvable while in there, it names the observation in
the report and walks away — does not fix.

### §9.3 No adjacent workstreams

W11–W15 (accounts, balances, promos, transactions, operations
log) and W17 (racing market pages) are downstream of this lift
and are off-limits this session. Code does not preview,
scaffold, or partially-start any of them.

### §9.4 No Alembic adoption, no debt-fixing

The locked migration tool (Alembic per DR-031) stays untouched
— the existing inline `_add_column_if_missing` migration block
relocates as-is. The three pieces of named debt from the
DR-029 close-out (no test coverage, no migration framework,
monolithic `orchestrator.py` file at ~1481 LOC) are tracked
separately and not touched in this session.

### §9.5 Operational guardrails

- **No git operations:** no `git add`, `git commit`,
  `git stash`, `git restore`, `git checkout` (file-targeted),
  or `git reset`. Working tree state is read at session start;
  if dirty unexpectedly, Code surfaces and stops.
- **No database access:** no reads or writes against any
  operational SQLite file. This brief is pure code
  rearrangement.
- **No mid-session escalation:** Code runs end-to-end and
  surfaces surprises in the report rather than pinging
  operator-Claude mid-flight.

---

## §10 — What happens after Code's session

The next operator-Claude session does three things:

1. **Read `w10_report.md` and triage findings.** Code's report
   lists what it changed (per §5 sub-section) plus any
   surprises observed during execution. Operator-Claude works
   through each surprise and routes it — fix it now in a
   follow-up brief, add to backlog, or close as known-and-
   tolerated. Per the §9.1 operating principle, the routing
   call stays with the operator; Code does not freelance
   fixes inside the W10 session.

2. **Carry forward Alembic adoption as a tracked open item.**
   The locked migration tool per DR-031 stays deferred to its
   own brief. Flagged here so it does not drift silently —
   lands in `current_state.md` open items at Session 118 close
   and in the Session 119 opening prompt. Sequencing: likely
   after W11–W15 are scoped, since the operational-store sub-
   streams will surface what schemas Alembic needs to manage
   from day one.

3. **Open the W11 brief drafting arc** (or pivot to a
   different sub-stream of the operational-store band if
   priorities shift). W11 is accounts + account-at-book per
   DR-022 — the foundation sub-stream the other four
   (balances, promos, transactions, operations log) depend
   on. If `w10_report.md` surfaces material findings that
   warrant their own follow-up brief, W11 drafting waits
   until those follow-ups are clean.

---

## §11 — Cross-references

- **DR-030** (v3 repo layout — the load-bearing contract this
  brief satisfies).
- **DR-031** (v3 tech stack — Alembic adoption deferred to
  separate brief, flagged §10).
- **DR-032** (canonical-reference-layer for all bet records —
  schema source for the lifted tables).
- **DR-022** (book/account/account-at-book vocabulary —
  context for downstream W11–W15).
- **`v3_build_picture.md`** W10 row (Session 117 re-cut).
- **Sessions 35/36** brief precedents (surgical-fix shape).
- **W3, W4, W6, W6.5, W9** brief precedents (the lift
  sources — schema columns introduced).
- **Parking-lot exclusions:** Alembic adoption (separate
  brief), W11–W15 sub-streams (downstream).
