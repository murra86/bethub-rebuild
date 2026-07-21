# W6.5 — Settlement-state worker brief

**Drafted:** 2026-05-08 07:28 ACST (Adelaide local per DR-021)
**Source spec:** `dr029/2_6_settlement_race/2_6_settlement_race.md` (§2.6,
649 lines)
**Predecessors:** W6 broader-sync brief (1114 lines, shipped clean Session
103-104) + W6.1 surgical amendment (542 lines, shipped clean Session 105).
**Status at lock:** awaiting operator review.

---

## §1 What this brief is and is not

W6.5 commissions Code to build the **settlement-state worker** that
runs alongside W6's match-state reconciliation worker, sweeping
post-match bets and resolving them to terminal settlement states by
reading the Betfair Win market via the existing
`clients.betfair_client.v1.settlement` surface (already shipped at
v1.0).

This is a **single bounded Code session**. Code reads this brief
end-to-end, executes against named anchors only, and produces one
report at the named output path. Surprises become §6 deviations or §7
findings, not blockers. Remediation routes to operator-Claude triage in
the next session, never inside Code's report.

Specifically in scope:

- A new `settlement_state` field on `BetRecord` (Pydantic v2 enum, five
  values per §2.6 §3.1: `pending`, `settled_won`, `settled_lost`,
  `voided`, `provisional`).
- Three new count fields on `BetRecord` populated at settlement time
  from the existing `MarketSettlement` response: `dead_heat_count`,
  `removed_runner_count`, `unexpected_state_count`.
- A new derived property `is_past_settlement_window` on `BetRecord` —
  true when bet is `pending` and now exceeds 30 minutes past the leg's
  Betfair event start time. No stored column; no write path; computed
  at read time.
- A new module `workflows/bet_entry/v1/settlement.py` mirroring the
  shape of `reconciliation.py`: `_resolve_settlement_for_bet` pure
  read-side resolver, `run_settlement_pass` pass-loop entry point,
  `SettlementDecision` + `SettlementPassResult` Pydantic models,
  `SettlementScheduler` Protocol + `ManualSettlementScheduler` +
  `ThreadingSettlementScheduler`.
- Storage extensions on `BetRecordStorage` Protocol +
  `InMemoryBetRecordStorage` + `SQLiteBetRecordStorage`: four new
  columns via `_add_column_if_missing`, updated DDL, updated
  `_row_to_record` reader, updated `write_bet_record` INSERT, new
  `update_settlement_state` write method, new
  `list_unsettled_bets` query (mirrors `list_unreconciled_bets`
  shape but filters on `settlement_state` rather than
  `match_status`).
- A burst-review surfacing contract — a small immutable model
  (`ProvisionalSettlementSurfacingPayload`) capturing what gets
  surfaced to the burst-review queue when a bet enters
  `provisional`, plus a storage query `list_provisional_settlement_bets`
  that returns the data shape.
- Tests for all of the above — covers the state transitions, the
  worker pass loop, the burst-review surfacing payload, the
  derived past-window property, error paths, and an integration
  test against the SQLite reference store.

Specifically not in scope (see §9 hard limits for the full list):

- No changes to the `clients.betfair_client.v1.settlement` module.
  The surface is already shipped at v1.0; the worker calls it.
- No changes to W6's reconciliation worker. W6 and W6.5 are sibling
  workers, both reading the same Betfair settlement surface, neither
  invoking the other.
- No burst-review queue UI. §2.6 §3.5 specifies the data contract;
  the queue surface itself is v3 build proper UI work.
- No settlement worker cadence specification. §2.6 §2.4 leaves
  cadence to §2.4 (Streaming spec, parked) or v3 build proper. W6.5
  ships the pass-loop primitive; the trigger model wraps it later.
- No soft-book balance reconciliation. §2.6 §1.2 names this as the
  operational backstop; implementation is v3 build proper.
- No Alembic migration. W6.5 uses the same `_add_column_if_missing`
  inline DDL pattern W6 established. Alembic adoption is post-DR-029
  work per `decisions.md` DR-031 + governance.md.

This is a **substrate-plus-worker brief**, not a surgical-fix brief.
Closest precedent: W6 broader-sync brief (1114 lines, shipped Session
103-104). The §-section spine mirrors W6's; the substantive sections
are correspondingly larger than W6.1's surgical envelope.

## §2 Why this work exists

§2.6 of `dr029/2_6_settlement_race/2_6_settlement_race.md` specifies
v3's race-path settlement model: every racing bet settles against the
Betfair Win market identified by its `betfair_market_id`, regardless of
whether it was placed on Betfair or a soft book. The spec defines a
five-state state machine (`pending`, `settled_won`, `settled_lost`,
`voided`, `provisional`), three count fields capturing race-wide signals
from the same Betfair read, a past-settlement-window visibility flag,
two automated trigger conditions for the `provisional` state, and a
burst-review surfacing contract.

§2.6 §1.4 names §2.6's load-bearing inputs:

- §2.2 (Session 38) — sports-path settlement model (already shipped,
  out of scope here).
- §2.4 (parked) — Streaming spec / read cadence (out of scope per §1).
- §2.8 (Session 72) — bet record contract (DR-032). The spec assumes
  `settlement_state` already exists on the bet record per §2.8 §6.4.
  **Empirical pre-flight finding (Session 105):** the field does not
  exist on the live `BetRecord` model in `workflows/bet_entry/v1/
  models.py`. W4 explicitly left settlement fields out as "W5
  territory." W6.5 therefore creates the field as well as using it.
- §2.9 (Session 73) — write-side bet-entry coherence. Surface (c)
  identifier-resolution sanity check feeds §4.1 late-scratching cases.

§2.6 §1.5 names §2.6's load-bearing outputs:

- The `betfair_client` settlement-read contract — **already shipped
  at v1.0** in `clients/betfair_client/v1/settlement.py`. W6's
  reconciliation worker already calls `market_settlement(...)` and
  reads `MarketSettlement` / `RunnerSettlementStatus` / per-runner
  `voided` flag. No contract extension needed.
- The settlement state machine — W6.5 implements per §2.6 §3.
- The burst-review surfacing contract — W6.5 implements the data
  shape per §2.6 §3.5.

W6.5 is the load-bearing v3-side implementation that closes §2.6's
deliverable surface.

## §3 Pre-reads

Required reads (in order, before drafting any code):

1. `dr029/2_6_settlement_race/2_6_settlement_race.md` — the source
   spec. 649 lines. Read in full. §2 (canonical settlement source),
   §3 (state machine), §4 (edge cases), §5 (DR-029 closing
   contract) are all load-bearing. Section numbers in the spec are
   the canonical reference for §5 anchors below.
2. `dr029/w4_bet_entry/w6_broader_sync_brief.md` — W6 brief (1114
   lines). The structural template for W6.5. Read §5 (anchors),
   §7 (verification), §9 (hard limits), §10 (sequencing) for shape.
3. `dr029/w4_bet_entry/w6_1_anomaly_reason_code_brief.md` — W6.1
   brief (542 lines). Reference for the surgical amendment pattern
   that touched the same `reconciliation.py` substrate. Useful for
   understanding the existing reason-code Literal structure.
4. `workflows/bet_entry/v1/models.py` (361 lines) —
   `BetRecord` shape, the `MatchStatus` enum pattern for
   `SettlementState` to mirror, the `LegRole` / `EntryPath` /
   `PriceSource` enums for stylistic precedent.
5. `workflows/bet_entry/v1/reconciliation.py` (655 lines) — the
   structural template. `_resolve_one` shape, `ResolutionDecision`,
   `ReconciliationPassResult`, `run_reconciliation_pass`,
   `ManualReconciliationScheduler`, `ThreadingReconciliationScheduler`.
   W6.5 mirrors all of these.
6. `workflows/bet_entry/v1/storage.py` (675 lines) — the
   `BetRecordStorage` Protocol, the `_BETS_DDL`, the
   `_add_column_if_missing` migration helper, `_row_to_record`,
   `list_unreconciled_bets` (the shape `list_unsettled_bets`
   mirrors), `update_reconciliation_bookkeeping` (the shape
   `update_settlement_state` mirrors at the protocol level).
7. `clients/betfair_client/v1/settlement.py` (118 lines) —
   the existing settlement-read surface. `market_settlement(...)`
   function, `MarketSettlement` model, `RunnerSettlementStatus`
   enum, `RunnerSettlement` model, the count fields populated in
   `_parse_settlement`. W6.5 calls this without modification.
8. `tests/workflows/bet_entry/v1/test_reconciliation.py` —
   the test pattern to mirror for `test_settlement.py`. Look at
   the helper functions (`_make_record`, the `T0_PLUS_300S`
   Adelaide-local clock pin), the pass-level test structure,
   the storage-failure tests, the read-unavailable tests.

Reference-only (consult on demand, not required cover-to-cover):

- `decisions.md` — DR-021 (timestamp anchoring, Adelaide local),
  DR-027 (two-database architecture, the operational/analytical
  separation that puts settlement-read on the operational line),
  DR-028 (cross-database integration boundary discipline), DR-031
  (v3 tech stack: Pydantic v2, SQLite WAL, ruff, lint-imports,
  pytest), DR-032 (canonical-reference-layer for all bet records,
  the source of `betfair_market_id` / `betfair_selection_id` as
  canonical join keys).
- `architecture.md` §A.10 (canonical source identifiers), §B.1.4
  (sports-path settlement model — sibling reference; W6.5 is
  race-path only).
- `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  — `betfair_client` v1.0 contract spec (1486 lines). §9.2
  (settlement reads) is the anchor for the existing
  `market_settlement` surface; §15 (out-of-scope surfaces) is
  reference for what's absent at v1.0.
- `dr029/w4_bet_entry/w6_broader_sync_report.md` (756 lines) —
  W6 ship report. Reference for what shipped, what was left as
  carry-forward debt, and what the test structure looks like
  post-W6.

## §4 System access

- **Filesystem (read-write):** Mac local at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Edit anchors named in
  §5 only.
- **Working tree:** dirty per W6 + W6.1 ship pattern. Operator's
  in-flight work has not landed since W6.1; the dirty-tree state
  Code observed at W6.1 session open is the expected baseline.
- **Python interpreter:** `.venv/bin/python` (3.12.7) per W6.1
  precedent. `requires-python = ">=3.12"` in `pyproject.toml`;
  invoke via the venv interpreter explicitly to avoid the system
  `python3` foot-gun (W6 §8.1 finding).
- **Database (read-write):** in-process SQLite via the W6
  `SQLiteBetRecordStorage` reference implementation. No external
  database. No live Betfair API calls — all tests use mocked
  adapters per the W6 / W6.1 pattern.
- **Tests:** `pytest` from the venv. Pre-baseline run at session
  start to establish the count; post-baseline run at session end
  to verify net-new test delta.
- **No git operations.** No `git add`, `git commit`, `git stash`,
  `git restore`, `git checkout`, `git reset`. The brief's
  edit anchors land inside already-untracked files in the
  `workflows/bet_entry/v1/` namespace; the dirty-file list does
  not change.
- **Adelaide local timestamps per DR-021.** All session timestamps,
  all test fixtures, all log lines.

## §5 Substantive scope sections

§5 names every change W6.5 makes. Anchors are file + region. Code
edits only what's named here.

### §5.1 — `SettlementState` enum

**File:** `workflows/bet_entry/v1/models.py`

**Change:** Add a new enum class adjacent to `MatchStatus` (which
is the structural sibling).

```
class SettlementState(str, Enum):
    """§2.6 §3.1 — five-state settlement state machine for racing bets.

    `PENDING` is the default at bet entry. Terminal states are
    `SETTLED_WON`, `SETTLED_LOST`, `VOIDED`. `PROVISIONAL` is the
    non-terminal review state per §2.6 §3.4 — entered on
    settlement-read trigger conditions, exited on auto-resolution
    or manual operator action.
    """

    PENDING = "pending"
    SETTLED_WON = "settled_won"
    SETTLED_LOST = "settled_lost"
    VOIDED = "voided"
    PROVISIONAL = "provisional"
```

**Placement:** immediately after the existing `MatchStatus` enum
class block, preserving the ordering of unrelated enums after it.

### §5.2 — `BetRecord` field additions

**File:** `workflows/bet_entry/v1/models.py`

**Change A — `settlement_state` field.** Add to `BetRecord` after
the existing `last_reconciled_at` / `reconciliation_attempts` W6
bookkeeping fields, before the `legs` tuple. Default `None` for
backward compatibility with records constructed pre-W6.5; the
orchestrator will populate at write-time once W7 wires the trigger
to set `PENDING` at bet entry. **W6.5 does not modify the
orchestrator** — that's W7's territory. W6.5 only ensures records
constructed today work without the field, and that records with the
field set are read/written correctly.

```
# W6.5 — settlement-state field per §2.6 §3.1.
# Default None for backward compatibility with pre-W6.5 records.
# The orchestrator populates at write-time in W7 (out of scope here).
settlement_state: SettlementState | None = None
```

**Change B — three count fields.** Add immediately after
`settlement_state`, before `legs`. All optional; populated by the
settlement worker at terminal-state transition time (§5.5);
default `None` for pre-W6.5 records and for `pending` /
`provisional` records.

```
# W6.5 — three count fields per §2.6 §4.5.
# Populated from the same MarketSettlement read the worker performs
# at settlement transition; None outside terminal-state records.
dead_heat_count: int | None = None
removed_runner_count: int | None = None
unexpected_state_count: int | None = None
```

**Change C — `is_past_settlement_window` derived property.**
Pydantic v2 `@computed_field` on `BetRecord`, returning `bool`.
True iff `settlement_state == SettlementState.PENDING` AND now
(Adelaide local per DR-021) exceeds the leg's
`betfair_event_start_time` by `DEFAULT_PAST_WINDOW_SECONDS`. The
threshold lives as a module-level constant in `settlement.py` per
§5.4 below; the property reads it via import.

Per §2.6 §3.3, the threshold is 30 minutes (`1800` seconds) at v3
day-one and is operational tuning, not architectural. The
property uses `_now_adelaide()` from `settlement.py` for
testability — tests can monkeypatch the clock per the existing
W6 `_now_adelaide()` pattern.

```
@computed_field
@property
def is_past_settlement_window(self) -> bool:
    """§2.6 §3.3 — operational visibility flag for stuck-pending bets.

    Not a state — purely derived from `settlement_state`,
    `legs[0].betfair_event_start_time`, and the wall clock.
    Threshold defined in `settlement.py:DEFAULT_PAST_WINDOW_SECONDS`.
    """
    from workflows.bet_entry.v1.settlement import (
        DEFAULT_PAST_WINDOW_SECONDS,
        _now_adelaide,
    )
    if self.settlement_state != SettlementState.PENDING:
        return False
    if not self.legs:
        return False
    elapsed = (_now_adelaide() - self.legs[0].betfair_event_start_time)
    return elapsed.total_seconds() > DEFAULT_PAST_WINDOW_SECONDS
```

**Note on circular import.** `settlement.py` imports `BetRecord`
from `models.py`. The reverse import for the constant + clock is
done inside the `@computed_field` body (function-local) to avoid
circularity at module load. Same pattern as similar deferred-
import cases in the codebase.

### §5.3 — Storage schema migration + DDL + reader/writer extensions

**File:** `workflows/bet_entry/v1/storage.py`

**Change A — `_BETS_DDL` extension.** Add four columns to the
DDL:

```
settlement_state             TEXT,            -- W6.5 — nullable
dead_heat_count              INTEGER,         -- W6.5 — nullable
removed_runner_count         INTEGER,         -- W6.5 — nullable
unexpected_state_count       INTEGER,         -- W6.5 — nullable
```

Position: after `reconciliation_attempts` (the last existing W6
column), before the closing `)`.

**Change B — `_connect_and_init` migration.** Add four
`_add_column_if_missing` calls inside the existing migration block
(immediately after the W6 calls), idempotent and consistent with
W6's pattern:

```
_add_column_if_missing(conn, "bets", "settlement_state", "TEXT")
_add_column_if_missing(conn, "bets", "dead_heat_count", "INTEGER")
_add_column_if_missing(conn, "bets", "removed_runner_count", "INTEGER")
_add_column_if_missing(conn, "bets", "unexpected_state_count", "INTEGER")
```

**Change C — `write_bet_record` INSERT extension.** Add the four
columns to the INSERT column list and the values tuple. Position:
after `reconciliation_attempts`. Values for nullable enum / ints
follow the existing `price_source` / `betfair_bet_id` pattern
(value or None).

**Change D — `_row_to_record` extension.** Read the four columns
from the bet row and populate them on the `BetRecord` constructor.
Pattern follows the existing `price_source` reader:

```
settlement_state=(
    SettlementState(bet_row["settlement_state"])
    if bet_row["settlement_state"] is not None
    else None
),
dead_heat_count=bet_row["dead_heat_count"],
removed_runner_count=bet_row["removed_runner_count"],
unexpected_state_count=bet_row["unexpected_state_count"],
```

**Change E — `BetRecordStorage` Protocol method:
`update_settlement_state`.** Add to the Protocol (and to both
implementations). Signature:

```
def update_settlement_state(
    self,
    bet_id: str,
    *,
    settlement_state: SettlementState,
    dead_heat_count: int | None = None,
    removed_runner_count: int | None = None,
    unexpected_state_count: int | None = None,
) -> WriteResult:
    """W6.5 brief §5.3 — settlement-state write distinct from
    `update_match_status`. Writes the settlement state plus the
    three count fields atomically (single UPDATE statement).
    Counters default None — only populated on terminal-state
    transitions where the worker has the MarketSettlement read.
    """
    ...
```

Implementation in `SQLiteBetRecordStorage` mirrors
`update_match_status`'s shape: single UPDATE inside the lock, returns
`WriteResult` with `success=False` + `error_message="bet_id not
found"` if `cursor.rowcount == 0`. Implementation in
`InMemoryBetRecordStorage` mirrors the same pattern via
`model_copy(update={...})`.

**Change F — `BetRecordStorage` Protocol method:
`list_unsettled_bets`.** Add to the Protocol (and to both
implementations). Signature:

```
def list_unsettled_bets(
    self,
    *,
    settlement_states: tuple[SettlementState, ...] = (
        SettlementState.PENDING,
    ),
    older_than_event_start: datetime | None = None,
    max_results: int = 100,
) -> list[BetRecord]:
    """W6.5 brief §5.3 — return bets matching the settlement-state
    filter, optionally with leg event-start older than the given
    timestamp, capped at `max_results`.

    Default filter: `PENDING` only — the settlement-worker sweep
    population. Callers may override with `(PROVISIONAL,)` for
    burst-review queries or with multi-state filters for diagnostic
    dashboards.

    `older_than_event_start` filters on `legs[0].betfair_event_start_time`,
    not on `placed_at` (the §5.5 worker reads bets whose race has
    already started, not bets whose entry happened recently).

    `max_results` caps a single pass at 100 bets — same envelope
    as `list_unreconciled_bets`.
    """
    ...
```

Implementation in `SQLiteBetRecordStorage` extends the joined-query
pattern from `list_unreconciled_bets`: filters bets table on
`settlement_state IN (...)` and joins `bet_legs` for the leg-0
`betfair_event_start_time` filter. Stable ordering by leg event
start time ascending (oldest-first sweeps).

Implementation in `InMemoryBetRecordStorage` extends the
in-memory filter pattern.

**Change G — `BetRecordStorage` Protocol method:
`list_provisional_settlement_bets`.** Add to the Protocol (and to
both implementations). Returns the burst-review surfacing payload
shape (§5.6). This is a thin convenience over a `list_unsettled_bets`
call with `settlement_states=(SettlementState.PROVISIONAL,)`, plus
joining the surfacing payload data. Justification: the burst-review
queue UI calls one query, gets the shape it surfaces; keeping the
join inside storage means the queue UI doesn't need to know about
the bet-record-to-payload mapping.

Signature:

```
def list_provisional_settlement_bets(
    self,
    *,
    max_results: int = 100,
) -> list[ProvisionalSettlementSurfacingPayload]:
    """W6.5 brief §5.3 — return the burst-review surfacing
    payload for every bet currently in `PROVISIONAL` settlement
    state. Convenience over `list_unsettled_bets` plus the
    surfacing-payload mapping.
    """
    ...
```

Implementation: list bets via `list_unsettled_bets` with
`PROVISIONAL` filter, map each to the payload shape per §5.6, return
the list.

### §5.4 — `settlement.py` — module-level constants and helpers

**File:** `workflows/bet_entry/v1/settlement.py` (new module)

**Module docstring:** mirrors `reconciliation.py`'s shape — names
the brief, the source spec, the closed §2.6 contract.

```
"""Periodic settlement-state worker (W6.5 v1).

W6.5 brief: dr029/w4_bet_entry/w6_5_settlement_worker_brief.md §5.4.
Source spec: dr029/2_6_settlement_race/2_6_settlement_race.md.

Sweeps bets in `SettlementState.PENDING` whose Betfair event start
time has elapsed, reads Betfair via the existing v1.0
`market_settlement` surface (§9.2), and resolves to terminal
settlement states (`SETTLED_WON` / `SETTLED_LOST` / `VOIDED`) per the
state machine at `_resolve_settlement_for_bet`.

Closes §2.6's race-path settlement contract for v3 day-one.
"""
```

**Module-level constants:**

```
DEFAULT_AGE_THRESHOLD_SECONDS: float = 300.0
"""Bets whose Betfair event start time is younger than this are
not swept by the settlement worker. v1 default 5 minutes — the
worker reads after the race has run, not before.

Distinct from W6's reconciliation `DEFAULT_AGE_THRESHOLD_SECONDS`
(60s, applies to bet placement age). Calibrate post-DR-029-close.
"""


DEFAULT_SETTLEMENT_INTERVAL_SECONDS: float = 60.0
"""Worker pass interval — 1 minute by default.

Distinct from W6's reconciliation 5-minute pass interval —
settlement is more time-sensitive than match-status reconciliation
because operator visibility on settled bets drives downstream
cycle handling. v1 placeholder; calibrate post-DR-029-close.
"""


DEFAULT_PAST_WINDOW_SECONDS: float = 1800.0
"""§2.6 §3.3 — past-settlement-window threshold.

Bets in PENDING state whose leg event start time elapsed by more
than this are flagged via `BetRecord.is_past_settlement_window`
for operator visibility. Not a state — purely a visibility surface.
v1 default 30 minutes per §2.6 §3.3; calibrate post-DR-029-close.
"""


ADELAIDE = ZoneInfo("Australia/Adelaide")


def _now_adelaide() -> datetime:
    """DR-021 — Adelaide local for all worker timestamps.

    Mirror of the `_now_adelaide()` in `reconciliation.py`. Both
    workers use the same module-local helper for testability —
    monkeypatch this symbol per worker rather than reaching across
    modules.
    """
    return datetime.now(ADELAIDE)
```

### §5.5 — `settlement.py` — `_resolve_settlement_for_bet` and `run_settlement_pass`

**File:** `workflows/bet_entry/v1/settlement.py`

**Change A — `SettlementReasonCode` Literal.** Stable identifiers
for triage-visibility reasons, mirroring `ResolutionReasonCode`
in `reconciliation.py`. Six values:

```
SettlementReasonCode = Literal[
    "settled_won",                              # clean WINNER
    "settled_lost",                             # clean LOSER
    "voided_runner_removed",                    # per-runner REMOVED
    "voided_market_voided",                    # market_voided=True
    "provisional_unexpected_state",             # §2.6 §3.4 cond 1
    "provisional_post_settlement_void",         # §2.6 §3.4 cond 2
    "read_unavailable_settlement",              # API read failed
    "market_not_yet_settled",                   # CLOSED but no settled_time
    "market_not_yet_closed",                    # OPEN or SUSPENDED
]
```

`market_not_yet_settled` and `market_not_yet_closed` are
no-decision reason codes (no transition fires); the bet stays
`PENDING`. The worker still increments `reconciliation_attempts`
via the `update_settlement_bookkeeping` write below (§5.5 Change D).

**Change B — `SettlementDecision` Pydantic model.** Mirrors
`ResolutionDecision` in `reconciliation.py`:

```
class SettlementDecision(BaseModel):
    """Per-bet decision returned by `_resolve_settlement_for_bet`.

    `new_state` is None when the read returned a non-terminal
    market state (not yet closed / not yet settled) or when the
    read failed; otherwise it carries the resolved state.

    `dead_heat_count` / `removed_runner_count` /
    `unexpected_state_count` come from the same MarketSettlement
    response the worker reads. Populated only when `new_state`
    is set; None otherwise.

    `reason_code` is a stable identifier for triage; `detail`
    carries the source snapshot or unavailable reason for log
    visibility.
    """

    model_config = ConfigDict(frozen=True)

    new_state: SettlementState | None
    dead_heat_count: int | None
    removed_runner_count: int | None
    unexpected_state_count: int | None
    reason_code: SettlementReasonCode
    detail: dict[str, Any] = Field(default_factory=dict)
```

**Change C — `_resolve_settlement_for_bet` function.** Pure
read-side. Six-step logic mirroring `_resolve_one`:

```
def _resolve_settlement_for_bet(
    *,
    record: BetRecord,
    settlement_reader: SettlementReader,
) -> SettlementDecision:
    """W6.5 brief §5.5 — given a bet record and a settlement
    reader, decide what the bet's settlement_state should resolve
    to.

    Read steps (in order):

    1. Read the Betfair Win market via `settlement_reader.read(
       market_id=...)` using the leg's `betfair_market_id`.
    2. Read returned ReadUnavailable → no decision; reason
       `read_unavailable_settlement`.
    3. Market_status != CLOSED → no decision; reason
       `market_not_yet_closed`. Bet stays PENDING.
    4. settled_time is None (CLOSED but not yet settlement-stamped)
       → no decision; reason `market_not_yet_settled`. Bet stays
       PENDING.
    5. market_voided → SettlementState.VOIDED with reason
       `voided_market_voided`. Counts populated from the
       MarketSettlement response.
    6. Find the runner matching the leg's `betfair_selection_id`:
       - runner.settlement_status == REMOVED →
         SettlementState.VOIDED with reason `voided_runner_removed`.
       - runner.settlement_status == WINNER →
         SettlementState.SETTLED_WON with reason `settled_won`.
       - runner.settlement_status == LOSER →
         SettlementState.SETTLED_LOST with reason `settled_lost`.
       - runner is None (not in market) → unexpected; provisional
         with reason `provisional_unexpected_state`.
       - any other runner.settlement_status value →
         SettlementState.PROVISIONAL with reason
         `provisional_unexpected_state` (§2.6 §3.4 cond 1).

    All terminal-state and provisional decisions populate the
    three count fields from the MarketSettlement response.

    Pure read-side — does no writes. The pass-level worker
    (`run_settlement_pass`) takes the decision and applies it
    to storage.
    """
```

`SettlementReader` is a Protocol introduced in this module — see
§5.5 Change F.

**Note on §2.6 §3.4 condition 2 — post-settlement market voided.**
Condition 2 (a bet already in a terminal state transitions back to
PROVISIONAL because the market was subsequently voided) is the
exception to the "terminal states are terminal" rule. W6.5 v1
**does not implement condition 2.** The worker only reads bets in
`PENDING`. Condition 2 requires the worker to also re-read bets
already in terminal state (a periodic verification cadence per
§2.6 §5.4 carry-forward), which is out of scope per §1 (cadence
is §2.4 / build-proper territory). Manual operator escalation
from any non-PROVISIONAL state to PROVISIONAL is the
operator-side substitute at v1, per §2.6 §3.2.

**Recording the v1 limitation explicitly:** the post-settlement-void
edge case is a known gap at v1, called out in §2.6 §5.4
("Settlement worker periodic verification cadence") as
non-gating-for-DR-029. Operator-side balance reconciliation per
§2.6 §1.2 catches the concrete operational consequence
(divergence between Betfair settlement and soft-book
settlement) regardless of whether v3 itself notices.

**Change D — `SettlementPassResult` Pydantic model.** Mirrors
`ReconciliationPassResult`:

```
class SettlementPassResult(BaseModel):
    """Pass-level summary returned by `run_settlement_pass`.

    Counters are inclusive across the swept population. Six
    decision-class counters plus the no-decision carries plus
    swept_count and timestamps.
    """

    model_config = ConfigDict(frozen=True)

    swept_count: int
    settled_won: int
    settled_lost: int
    voided: int
    provisional_entered: int
    left_pending_market_not_closed: int
    left_pending_market_not_settled: int
    left_pending_read_unavailable: int
    started_at: datetime  # Adelaide local per DR-021
    finished_at: datetime
    pass_id: str  # uuid4 hex for log correlation
```

Eight counters total — covers six decision classes plus the two
no-decision-but-bet-stays-pending cases distinct from
read-unavailable.

**Change E — `run_settlement_pass` function.** Mirrors
`run_reconciliation_pass`. Single pass:

```
def run_settlement_pass(
    *,
    storage: BetRecordStorage,
    settlement_reader: SettlementReader,
    age_threshold_seconds: float = DEFAULT_AGE_THRESHOLD_SECONDS,
    max_results: int = 100,
    now: Callable[[], datetime] | None = None,
) -> SettlementPassResult:
    """W6.5 brief §5.5 — single pass.

    Queries unsettled bets whose leg event start time is older
    than `age_threshold_seconds` ago, resolves each via
    `_resolve_settlement_for_bet`, writes settlement-state updates
    via `storage.update_settlement_state` and bookkeeping via
    `storage.update_reconciliation_bookkeeping` (the same W6
    bookkeeping write — `last_reconciled_at` and
    `reconciliation_attempts` are shared substrate, not duplicated
    per-worker).

    Idempotent across calls. Returns a `SettlementPassResult`.
    """
```

The bookkeeping shared-substrate decision: rather than
introducing a separate `last_settled_at` / `settlement_attempts`
pair of fields, W6.5 reuses W6's `last_reconciled_at` /
`reconciliation_attempts`. Justification: a single
"last-touched-by-a-worker" timestamp + counter pair is sufficient
for operator visibility; both workers update it on every pass
they touch the bet. **Trade-off:** the operator can't distinguish
"last touched by reconciliation" from "last touched by
settlement" by reading these fields alone; the distinction comes
from the bet's `match_status` + `settlement_state` shape (a bet in
`PROVISIONAL` match-status was last touched by reconciliation; a
bet in `PENDING` settlement-state with `match_status=FINAL_FULL`
is settlement-worker territory).

Operator-Claude triage on this trade-off was held in pre-flight
this session and resolved as accept-the-shared-substrate.

**Change F — `SettlementReader` Protocol.** Adapter shape the
worker depends on. Mirrors `BetfairAdapter` in `reconciliation.py`
but narrower (settlement reads only):

```
class SettlementReader(Protocol):
    """Adapter shape for `_resolve_settlement_for_bet`.

    Production composition wraps the v1.0 `market_settlement`
    function in `clients.betfair_client.v1.settlement`; tests use
    in-memory stubs that return canned `MarketSettlement` payloads
    or `ReadUnavailable` instances.
    """

    def read(
        self,
        *,
        market_id: str,
    ) -> ReadOutcome[MarketSettlement]: ...
```

**Note on `ReadOutcome[MarketSettlement]`.** This is the existing
read-outcome envelope shape from `clients.betfair_client.v1.envelope`
(`ReadEnvelope[T]` with `FreshEnvelope` / `UnavailableReadEnvelope`
variants). W6.5 imports it from the existing module — no new
envelope type.

**Change G — `_write_settlement_bookkeeping` helper.** Reuses W6's
`update_reconciliation_bookkeeping` storage method per the
shared-substrate decision above. The helper is a one-line wrapper
inside `settlement.py` for naming clarity:

```
def _write_settlement_bookkeeping(
    *,
    storage: BetRecordStorage,
    bet_id: str,
    last_reconciled_at: datetime,
) -> None:
    """W6.5 brief §5.5 — reuses W6 bookkeeping per shared-substrate
    decision. Same write semantics as W6's `_write_bookkeeping`.
    """
    bk = storage.update_reconciliation_bookkeeping(
        bet_id, last_reconciled_at=last_reconciled_at,
    )
    if not bk.success:
        LOG.warning(
            "settlement bookkeeping write failed for bet_id=%s: %s",
            bet_id, bk.error_message,
        )
```

### §5.6 — Burst-review surfacing contract

**File:** `workflows/bet_entry/v1/settlement.py` (the surfacing
payload model lives in the same module as the worker that produces
it).

**Change A — `ProvisionalSettlementSurfacingPayload` Pydantic
model.** §2.6 §3.5 specifies five data items the queue receives;
the model captures them as a frozen Pydantic v2 model:

```
class ProvisionalSettlementSurfacingPayload(BaseModel):
    """§2.6 §3.5 — what the burst-review queue receives when a bet
    enters PROVISIONAL settlement state.

    The queue surface itself is v3 build proper UI work; W6.5
    locks the data contract. Five named items per §2.6 §3.5:

    1. The bet record (full).
    2. The trigger source — which §3.4 condition fired, or
       'manual_operator_escalation' with operator-supplied reason.
    3. The current Betfair Win market state as last read.
    4. Timestamps — `placement_time` plus `entered_provisional_at`.
    5. Pointer to related bets in the same race (by
       `betfair_market_id`).
    """

    model_config = ConfigDict(frozen=True)

    bet_record: BetRecord
    trigger_source: ProvisionalTriggerSource
    operator_escalation_reason: str | None = None  # only when manual
    last_read_market_state: MarketSettlement | None  # None if read failed
    placement_time: datetime
    entered_provisional_at: datetime
    related_bet_ids: tuple[str, ...]  # bets sharing the same betfair_market_id
```

**Change B — `ProvisionalTriggerSource` enum.** Closed set per
§2.6 §3.4:

```
class ProvisionalTriggerSource(str, Enum):
    """§2.6 §3.4 — what caused a bet to enter PROVISIONAL.

    `UNEXPECTED_STATE` is condition 1; `POST_SETTLEMENT_VOID` is
    condition 2 (W6.5 v1 doesn't fire this — see §5.5 Change C
    note); `MANUAL_OPERATOR_ESCALATION` is the operator-driven path
    per §2.6 §3.2.
    """

    UNEXPECTED_STATE = "unexpected_state"
    POST_SETTLEMENT_VOID = "post_settlement_void"
    MANUAL_OPERATOR_ESCALATION = "manual_operator_escalation"
```

**Change C — `entered_provisional_at` storage.** The payload
exposes when the bet entered `PROVISIONAL`. v1 uses
`last_reconciled_at` as the proxy — the timestamp of the
settlement-worker pass that wrote the `PROVISIONAL` transition.
This is approximate (pass cadence granularity) but sufficient for
v1 burst-review visibility. **Carry-forward note:** a dedicated
`entered_provisional_at` column on the bets table would give
exact transition time; deferred per scope as build-proper
refinement.

**Change D — Surfacing payload construction.** A helper function
`_build_surfacing_payload(record, last_read, trigger_source,
operator_reason=None)` lives in `settlement.py` and is called by
both the storage `list_provisional_settlement_bets` query and (in
build-proper) by the manual-escalation API surface.
`related_bet_ids` is computed via a storage query
`list_bet_ids_for_market(market_id)` that returns all bet IDs
sharing the market — see §5.3 Change F's filter pattern as
template. **Out of scope for W6.5:** if extending storage further
threatens the brief's envelope, defer the related-bets join to
build-proper and have the v1 surfacing payload return an empty
tuple for `related_bet_ids` with a §6 deviation flag. Code's call.

### §5.7 — `settlement.py` — schedulers

**File:** `workflows/bet_entry/v1/settlement.py`

**Change A — `SettlementScheduler` Protocol.** Mirrors
`ReconciliationScheduler` exactly — same shape, same docstring
modulo the worker name:

```
class SettlementScheduler(Protocol):
    """W6.5 brief §5.7 — periodic worker scheduler.

    Production scheduler uses an asyncio loop in v3 build proper;
    tests use a deterministic stub that runs on demand.
    """

    def schedule_periodic(
        self,
        *,
        run: Callable[[], None],
        interval_seconds: float,
    ) -> None: ...
```

**Change B — `ManualSettlementScheduler` dataclass.** Test
scheduler. Direct mirror of `ManualReconciliationScheduler` —
same fields, same `schedule_periodic`, same `flush()`, no
behavioural difference. Justification for the duplication:
keeping the worker modules independently composable means each
ships its own scheduler shapes. **Carry-forward note:** if v3
build proper adopts a single asyncio loop driving both workers,
these scheduler classes consolidate then.

**Change C — `ThreadingSettlementScheduler` dataclass.** Mirror of
`ThreadingReconciliationScheduler`. Same re-arm semantics, same
daemon-timer pattern, same `stop()`.

### §5.8 — Tests

**File:** `tests/workflows/bet_entry/v1/test_settlement.py` (new test
module)

The test module mirrors `test_reconciliation.py`'s structure. ~25-35
new tests organised into the following blocks:

**Block 1 — `_resolve_settlement_for_bet` (read-side decision logic):**

- `test_resolve_returns_settled_won_on_clean_winner`
- `test_resolve_returns_settled_lost_on_clean_loser`
- `test_resolve_returns_voided_on_runner_removed`
- `test_resolve_returns_voided_on_market_voided`
- `test_resolve_returns_provisional_on_runner_not_in_market`
- `test_resolve_returns_provisional_on_unexpected_runner_status`
  (synthetic — tests defensive handling for forward-compat)
- `test_resolve_returns_no_decision_on_market_not_yet_closed`
- `test_resolve_returns_no_decision_on_market_closed_no_settled_time`
- `test_resolve_returns_no_decision_on_settlement_read_unavailable`
- `test_resolve_populates_dead_heat_count_on_terminal_transition`
- `test_resolve_populates_removed_runner_count`
- `test_resolve_populates_unexpected_state_count`

**Block 2 — `run_settlement_pass` (pass-loop logic):**

- `test_pass_sweeps_only_pending_bets`
- `test_pass_filters_by_event_start_age_threshold`
- `test_pass_increments_settled_won_counter`
- `test_pass_increments_settled_lost_counter`
- `test_pass_increments_voided_counter`
- `test_pass_increments_provisional_entered_counter`
- `test_pass_increments_left_pending_counters_correctly`
- `test_pass_writes_bookkeeping_per_bet_per_pass`
- `test_pass_handles_storage_update_failure`
- `test_pass_writes_count_fields_on_terminal_transition`
- `test_pass_does_not_write_count_fields_on_no_decision`

**Block 3 — `is_past_settlement_window` derived property:**

- `test_past_window_false_when_not_pending`
- `test_past_window_false_when_within_threshold`
- `test_past_window_true_when_past_threshold`
- `test_past_window_uses_module_level_threshold` (monkeypatch
  `DEFAULT_PAST_WINDOW_SECONDS`)

**Block 4 — Burst-review surfacing payload:**

- `test_surfacing_payload_captures_full_bet_record`
- `test_surfacing_payload_carries_trigger_source`
- `test_surfacing_payload_includes_related_bets_in_same_market`
- `test_list_provisional_settlement_bets_returns_payloads`

**Block 5 — Storage layer:**

- `test_sqlite_settlement_state_round_trip`
- `test_sqlite_count_fields_round_trip`
- `test_sqlite_settlement_state_column_migration_idempotent`
- `test_sqlite_list_unsettled_bets_filters_correctly`
- `test_sqlite_update_settlement_state_returns_not_found`

**Block 6 — Integration test (single end-to-end pass):**

- `test_end_to_end_pass_with_sqlite_storage` — single pass against
  `SQLiteBetRecordStorage`, three bets in different states,
  verify final state on disk matches expected.

**Test count delta target: +25 net new tests** (417 → 442). Code
may produce 28-32 net new tests if natural test boundaries surface
additional cases during write; flag in §6 deviation if outside
the band.

### §5.9 — `__init__.py` exports

**File:** `workflows/bet_entry/v1/settlement.py` `__all__` list at
end of module.

Exports follow the `reconciliation.py` pattern:

```
__all__ = [
    "DEFAULT_AGE_THRESHOLD_SECONDS",
    "DEFAULT_PAST_WINDOW_SECONDS",
    "DEFAULT_SETTLEMENT_INTERVAL_SECONDS",
    "ManualSettlementScheduler",
    "ProvisionalSettlementSurfacingPayload",
    "ProvisionalTriggerSource",
    "SettlementDecision",
    "SettlementPassResult",
    "SettlementReader",
    "SettlementReasonCode",
    "SettlementScheduler",
    "SettlementState",
    "ThreadingSettlementScheduler",
    "_resolve_settlement_for_bet",
    "run_settlement_pass",
]
```

`SettlementState` is also exported from `models.py` per its
canonical module location; the re-export from `settlement.py` is
convenience-only for callers importing from the worker module.

## §6 Sequencing within session

Code's session walks in dependency order:

1. **Models first** (§5.1, §5.2) — `SettlementState` enum,
   `BetRecord` field additions, `is_past_settlement_window`
   property. The property's deferred import of
   `settlement.py:DEFAULT_PAST_WINDOW_SECONDS` and `_now_adelaide`
   means `settlement.py` doesn't have to exist yet when the
   property is added (the import is function-local).

2. **Storage substrate** (§5.3) — DDL, migration, `_row_to_record`
   update, `write_bet_record` INSERT update, `update_settlement_state`,
   `list_unsettled_bets`, `list_provisional_settlement_bets`.
   Both implementations (`SQLiteBetRecordStorage`,
   `InMemoryBetRecordStorage`) updated together so test plumbing
   keeps working.

3. **Worker module** (§5.4, §5.5, §5.6, §5.7, §5.9) — create
   `settlement.py` end-to-end. Constants, helpers, decision logic,
   pass loop, surfacing model, schedulers, exports.

4. **Tests** (§5.8) — `test_settlement.py` covering all blocks.
   Run targeted before full-suite: `pytest tests/workflows/bet_entry/
   v1/test_settlement.py -v` first, then full-suite.

5. **Verification** — see §7. Pre/post baselines on test count, ruff,
   lint-imports.

The order is intentional. Tests can't run before models + storage
+ worker exist; storage's `_row_to_record` needs the model fields;
worker's resolver needs the storage `update_settlement_state` method.
Reverse-ordering (tests-first / worker-first) introduces transient
import errors that don't reflect real progress.

If a different order surfaces during execution as cleaner, Code may
deviate; flag the deviation in §6 of the report with the reasoning.

## §7 Empirical verification

### §7.1 — Pre-baseline (session open)

Capture all of the following:

- `pytest --collect-only -q | tail -1` — pre-baseline test count.
  Expected: 417 (W6.1 ship state).
- `pytest -q` — full-suite pass/fail. Expected: 417 passed.
- `ruff check workflows/bet_entry/v1/ tests/workflows/bet_entry/v1/`
  — clean.
- `lint-imports` — 5 contracts kept, 0 broken.
- `git status` — capture the dirty-file list. No `git add` /
  `git commit` / `git stash` allowed; the snapshot is for the
  report's §9 self-assessment.

### §7.2 — Post-baseline (session close)

Re-run all of §7.1's commands.

Expected post-baseline:

- Test count: ~442 (+25 net new). Acceptable band: 442-447 (+25 to
  +30); flag in §6 if outside the band.
- Full-suite pass: all green.
- `ruff check` clean.
- `lint-imports` 5 kept, 0 broken.
- `git status` — same dirty-file list at the file-level. New
  untracked files: `workflows/bet_entry/v1/settlement.py` and
  `tests/workflows/bet_entry/v1/test_settlement.py`. No other new
  untracked files; no modifications outside the named anchors.

### §7.3 — Functional verification checklist

Code confirms in the report's §9 self-assessment:

- [ ] All `tests/workflows/bet_entry/v1/test_settlement.py` pass.
- [ ] `tests/workflows/bet_entry/v1/test_reconciliation.py` still
      passes (no regressions from W6 / W6.1 substrate).
- [ ] `tests/workflows/bet_entry/v1/test_storage.py` still passes
      (no regressions from §5.3 storage extensions).
- [ ] `tests/workflows/bet_entry/v1/test_models.py` still passes
      (no regressions from §5.1 / §5.2 model extensions).
- [ ] Full suite passes.
- [ ] `ruff check` clean on the W4 + tests scope.
- [ ] `lint-imports` 5 contracts kept, 0 broken.
- [ ] No live Betfair API calls (mocked-only tests).
- [ ] No edits outside the §5 named anchors.
- [ ] No new untracked files outside `settlement.py` +
      `test_settlement.py`.

### §7.4 — Sample model dumps

The report's §9 captures one clean settlement transition's
post-write state via a model dump (the SQLite row read back through
`_row_to_record`):

- A `BetRecord` after `SETTLED_WON` transition shows
  `settlement_state="settled_won"`, `dead_heat_count` /
  `removed_runner_count` / `unexpected_state_count` populated as
  expected from the `MarketSettlement` payload, and the W6
  `last_reconciled_at` / `reconciliation_attempts` fields stamped
  per pass.
- A `ProvisionalSettlementSurfacingPayload` for a bet in
  `PROVISIONAL` state shows the full payload shape — bet record,
  trigger source, last-read market state, timestamps, related bet
  IDs.

These confirm the wire shape Session 106's W6.5 triage will read
against.

## §8 Output spec

**Path:** `dr029/w4_bet_entry/w6_5_settlement_worker_report.md`
(absolute: `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/
w4_bet_entry/w6_5_settlement_worker_report.md`).

**Length range:** 600-900 lines. The brief is ~1100-1400 lines;
W6's report at 756 lines was inside W6's brief envelope (1114
lines), so a 600-900 line W6.5 report is the same proportion.
Flag in §9 self-assessment if outside the band.

**Required structure:**

- **§1 Summary** — what shipped end-to-end in one paragraph plus
  the named-anchor checklist (A-G across §5.1-§5.9). Test count
  delta. ruff / lint-imports state.
- **§2 Files changed** — table of pre/post LOC for every file
  touched. New files (settlement.py, test_settlement.py) listed.
- **§3 Test count delta** — exact pre and post numbers, the +N
  delta, any band-flag.
- **§4 New tests added** — listed by block (1-6 per §5.8) with
  one-line description per test. Total test count by block.
- **§5 Implementation notes** — one sub-section per §5.x anchor.
  What landed, any inline decisions taken. The §5.5 Change C
  note about §2.6 §3.4 condition 2 (post-settlement void
  not implemented at v1) is restated in this section's
  implementation note for visibility.
- **§6 Deviations from brief** — any deviation from the §5
  anchors or the §6 sequencing. Expected: none, given the brief's
  detail level.
- **§7 Open questions for triage** — anything Code surfaced that
  the next operator-Claude session needs to resolve. Expected:
  zero or one (the related-bets-tuple v1 stubbing call from §5.6
  Change D, if Code took it).
- **§8 Findings beyond brief scope** — anything Code noticed
  during execution that wasn't anchored in the brief but warrants
  surfacing. Expected: zero or one.
- **§9 Self-assessment** — pre/post baselines table per §7.1 /
  §7.2; functional verification checklist per §7.3 (8 items
  ticked); `git status` snapshots; length flag; DR-021 timestamp
  confirmation.

**What the report does not contain:**

- No recommendations for what to do next. Forward routing is
  Session 106's call.
- No proposals for fixes outside the brief's scope.
- No design changes from the §5 anchors. Anchor-level changes
  surface as §6 deviations.
- No `git` operations in the implementation notes.

## §9 Hard limits

Non-negotiable. Code does not, under any circumstances:

- **Modify `clients.betfair_client.v1.settlement`.** The
  surface is shipped at v1.0. W6.5 reads it without modification.
- **Modify `clients.betfair_client.v1.envelope`** or any other
  `clients/` module. The brief touches `workflows/` only.
- **Modify W6's reconciliation worker** (`reconciliation.py`).
  W6.5 sits beside it; cross-coupling is via the shared storage
  substrate (the W6 bookkeeping fields per §5.5 Change G), not
  via direct calls.
- **Modify the orchestrator** (`orchestrator.py`). The
  bet-entry write-time population of `settlement_state=PENDING`
  is W7's territory. W6.5's `BetRecord` field defaults to None;
  W6.5's tests construct records with `settlement_state` set
  explicitly via the model constructor for testing the worker.
- **Implement §2.6 §3.4 condition 2** (post-settlement market
  voided). Out of scope per §5.5 Change C note; carry-forward
  to build-proper.
- **Implement settlement worker cadence / trigger model.** Out
  of scope per §1; the pass-loop primitive is shipped; the
  trigger that wraps it is build-proper.
- **Implement burst-review queue UI surface.** Out of scope per
  §1; only the data contract is shipped here.
- **Implement Alembic migration.** Out of scope per §1; the
  inline DDL pattern from W6 (`_add_column_if_missing`) is
  reused.
- **Implement soft-book balance reconciliation.** Out of scope
  per §1; operational backstop lives in build-proper.
- **Edit `decisions.md`, `architecture.md`, `governance.md`,
  `standing_instructions.md`, or any rebuild-folder governance
  file.** Code-side governance touches are Chat-territory.
- **Run `git add` / `git commit` / `git stash` / `git restore` /
  `git checkout` (file-targeted) / `git reset`.** The dirty-tree
  state is preserved; `git status` is read-only.
- **Make live Betfair API calls.** All tests use mocked
  adapters. Code captures `git status` and the test count via
  `pytest`; nothing else hits a network.
- **Modify pre-W6 fields on `BetRecord` or in storage DDL.** The
  existing fields stay as they are; W6.5 adds new fields only.

If the brief's anchors and the live codebase diverge — for example,
a §5 anchor file has moved, an existing function shape has changed,
a test fixture is missing — Code surfaces the mismatch as a §6
deviation in the report and stops at the affected anchor; the
remaining anchors that don't depend on the affected one continue.
The next operator-Claude session resolves the mismatch.

## §10 What happens after Code's session

The next operator-Claude session (Session 106 by current sequencing)
runs W6.5 report triage via the inventory-first cadence pattern
(sweep candidate `(l)` — fifth concrete use likely):

1. Read the W6.5 report end-to-end.
2. Inventory pass — classify §6 deviations, §7 open questions,
   §8 findings as no-call (Code's territory, awareness only) or
   operator-call (warrants routing).
3. Walk operator-call items one-per-round. Resolve each.
4. Forward routing — sequence into W7 burst-review brief drafting
   if W6.5 ships clean and time permits, otherwise close-out and
   pick W7 up in 107.

Code does not produce the next brief. W7's brief drafting is
Chat's territory in the next session.

## §11 Cross-references

**Source spec:** `dr029/2_6_settlement_race/2_6_settlement_race.md`
(§2.6, 649 lines). Primary anchor.

**Predecessor briefs:**
- `dr029/w4_bet_entry/w6_broader_sync_brief.md` (1114 lines, W6).
- `dr029/w4_bet_entry/w6_1_anomaly_reason_code_brief.md` (542
  lines, W6.1).

**Predecessor reports:**
- `dr029/w4_bet_entry/w6_broader_sync_report.md` (756 lines).
- `dr029/w4_bet_entry/w6_1_anomaly_reason_code_report.md` (305
  lines).

**Active governing DRs:**
- DR-021 (timestamp anchoring, Adelaide local time) —
  load-bearing for every test fixture and log timestamp.
- DR-027 (two-database architecture: BetHub owns operational
  state, capture.db owns analytical/source data) — context for
  why settlement reads happen on the operational line via
  `betfair_client`, not from `capture.db`.
- DR-028 (cross-database integration boundary discipline: no
  caching, no denormalisation, no second integration point) —
  context. W6.5 reads only operational substrate plus the
  Betfair surface; no capture.db touch.
- DR-031 (v3 tech stack: Pydantic v2, SQLite WAL, ruff,
  lint-imports, pytest) — load-bearing for every code surface
  shipped here.
- DR-032 (canonical-reference-layer for all bet records:
  `betfair_market_id` + `betfair_selection_id` as canonical join
  keys) — load-bearing for the worker's `_resolve_settlement_for_bet`
  read of the bet's leg-0 identifiers.

**Source-spec items left out of scope (called out for clarity):**
- §2.6 §3.4 condition 2 (post-settlement market voided
  re-transition from terminal). Out per §5.5 Change C; ships
  build-proper.
- §2.6 §1.2 / §5.4 soft-book balance reconciliation. Out per
  §1; ships build-proper.
- §2.6 §5.4 settlement worker periodic verification cadence. Out
  per §1; ships build-proper.
- §2.6 §5.4 sports-side dead-heat capture (architecture.md
  §B.1.4 amendment). Out per §1; administrative cleanup,
  potentially folded into DR-029 close-out work.
- §2.6 §5.4 past-settlement-window threshold calibration. Out
  per §1; v3 operational tuning post-DR-029.

**Carry-forward items this brief logs:**
- W6 §8.1 finding — `requires-python = ">=3.12"` venv invocation
  foot-gun. W6.5 follows W6.1's mitigation (use the venv
  interpreter explicitly).
- W6 §8.5 finding — `COALESCE` defensive on bookkeeping UPDATE.
  Already shipped in W6 substrate; W6.5 does not modify.
- W6 §8.7 finding — mypy/pyright not run. W6.5 inherits the
  state; not a W6.5 amendment.
- §2.6 §5.4 entered_provisional_at column refinement (currently
  proxied via `last_reconciled_at` per §5.6 Change C). Ships
  build-proper.

---

**End of brief.**
