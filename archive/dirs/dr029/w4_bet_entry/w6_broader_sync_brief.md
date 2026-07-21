# W6 broader-sync match-state reconciliation brief

**Drafted:** 2026-05-07 (Session 103)
**Locked:** [pending operator review]
**Brief author:** Claude Chat (Session 103)
**Code execution:** out-of-session, single bounded run
**Output report:** `dr029/w4_bet_entry/w6_broader_sync_report.md`

---

## §1 — What this brief is and is not

This brief commissions a single bounded Claude Code session to:

- **Add a periodic match-state reconciliation worker** — a new W4
  module `workflows/bet_entry/v1/reconciliation.py` that sweeps
  bets in `MatchStatus.PROVISIONAL` or
  `MatchStatus.PROVISIONAL_PENDING` state, queries Betfair via the
  existing W3 surfaces (`listCurrentOrders` §9.8 +
  `market_settlement` §9.2), and resolves to terminal states
  (`FINAL_FULL` / `FINAL_PARTIAL` / `FAILED`).
- **Extend the `BetRecordStorage` Protocol** — add query methods for
  unreconciled bets plus a bookkeeping-write for reconciliation
  attempt counters.
- **Extend the SQLite reference impl** — add two new columns
  (`last_reconciled_at`, `reconciliation_attempts`) plus inline
  idempotent DDL migration on storage init.
- **Extend the W4 `BetfairAdapter` Protocol** — no new read methods
  (W6 reuses `get_order_state` from W3 and `market_settlement`
  via a thin new wrapper) but extend the adapter to expose
  `get_market_settlement(market_id) -> ReadOutcome[MarketSettlement]`
  bridging the W3 `settlement.py` surface to the W4 boundary
  pattern locked Session 101.
- **Add a worker scheduler Protocol** — mirror
  `TriggerBScheduler` shape; ship reference threading impl plus
  manual stub for tests.
- **Wire the worker** to a composition entry point that v3 build
  proper will hook to a real periodic trigger; v1 ships the
  worker as a callable surface that tests exercise via the
  manual scheduler stub.

This brief closes the **§7.2 settlement-state ambiguity** locked
Option A in Session 102 — W6 is now the architectural home for
differentiating cancelled / voided / lapsed bets from fully matched
ones, exercised end-to-end through the periodic sweep.

This is **a single Code session**. If the work doesn't fit, that's
a finding to surface in the report, not a continuation. Surprises
become findings, not blockers; remediation routes through
operator-Claude triage at Session 104, not through ad-hoc Code-side
decisions.

This brief is **not**:

- A composition-root structural decision (sequenced post-W7).
- A W7 brief (sequenced after W6).
- The settlement-state reconciliation worker per §2.6 (the
  five-state `pending` / `settled_won` / `settled_lost` /
  `voided` / `provisional` machine on the `settlement_state`
  field). That's a separate W6.5 brief sequenced after W6 lands.
  See §1 carry-forward in §2 below for how the two relate.
- A retrofit of v2 — v3 codebase only.
- A bet-record schema reframing — only the two narrow
  reconciliation-bookkeeping columns are added (`last_reconciled_at`,
  `reconciliation_attempts`); no new bet-substance columns.
- A test-coverage rework or a tooling-hygiene pass beyond the
  worker and storage extensions.
- An audit-trail substrate selection. The named-debt audit-trail
  question (`governance.md` §4) is not blocked by W6 because the
  worker's auto-resolution writes use `update_match_status` which
  doesn't currently emit audit entries; W6 ships consistent with
  v1's no-audit-trail substrate posture and the broader durable-
  substrate decision happens post-DR-029-close.
- An Alembic adoption brief. Inline idempotent DDL migration is
  the v1 pattern; Alembic adoption is sequenced post-DR-029-close
  with the other named debt items.
- A modal-layer copy spec. The W7 modal layer reads
  `last_reconciled_at` and reconciliation-derived match status
  values as substrate; this brief lands the worker, not the
  display.

## §2 — Why this work exists

Session 102 triaged Code's W3 order-state report
(`w3_order_state_report.md`, 677 lines). Four operator-call items
resolved cleanly. The headline architectural call — §7.2
resolved-out-of-orders settlement-state ambiguity — locked Option
A: W6 broader-sync reconciliation is the architectural home for
differentiating cancelled / voided / lapsed bets from fully matched
ones, with Trigger B's "fully matched" assumption acceptable as a
v1.4 contract approximation.

The orchestrator's own contract names W6's job. From
`orchestrator.py:962-985` (`_run_trigger_b` docstring):

> Failure handling per §6.4: single retry at +10s if the read
> fails, then leave `provisional` for W6's broader sync
> reconciliation to pick up later (out of W4 scope).

And the failure log message:

> "Trigger B read unavailable for bet_id=%s (reason=%s); record
> stays provisional (W6 sync reconciliation will pick up)."

This is the orchestrator's own contract for what W6 is for: pick
up `MatchStatus.PROVISIONAL` and resolve to terminal. W6 is the
periodic sweep that turns "we don't know what happened" into "we
know what happened" without requiring operator intervention on
the recoverable cases.

Why this matters operationally: Trigger B is a 5-second
post-placement read. When it fails (auth lapse, transient
unreachable, rate-limit hit), the bet sits at
`MatchStatus.PROVISIONAL` indefinitely. Without W6, the operator
sees stale match-state data and must triage manually. With W6,
the worker re-reads on a periodic cadence (every few minutes) and
auto-resolves the recoverable cases — the operator only sees
provisional state for genuinely stuck bets that need attention.

Plus the §7.2 lock: the same worker that recovers
read-failure provisionals also resolves the cancelled / voided /
lapsed cases that Trigger B's "fully matched" approximation can't
distinguish. Same query path (`listCurrentOrders` returning
absence-from-orders-list); different resolution logic depending on
why the bet is absent (settlement-resolved vs cancelled-out vs
lapsed). The worker reads `market_settlement` to disambiguate when
the answer isn't visible from `listCurrentOrders` alone.

**Relation to §2.6 (race-path settlement model).** §2.6 specifies a
**different** reconciliation worker — the one that drives racing
bet P&L by transitioning `settlement_state` (a field not yet on the
schema) through the five-state `pending` / `settled_won` /
`settled_lost` / `voided` / `provisional` machine when the Betfair
Win market settles. That worker is sequenced as a follow-up brief
(W6.5 or v3-build-proper-equivalent). W6 (this brief) operates on
`match_status`, not `settlement_state`. The two are operationally
independent and structurally distinct: W6 reconciles bets in a
seconds-to-minutes window post-placement; the §2.6 worker
reconciles bets in a minutes-to-hours window post-race-jump. A
bet typically passes through W6 first (match state resolves) and
then through the §2.6 worker (settlement state resolves), but the
two state machines are independent.

Cross-references: `sessions/SESSION_102.md` (§7.2 locked Option
A); `dr029/w4_bet_entry/w3_order_state_report.md` §7.2 finding;
`dr029/w4_bet_entry/w6_broader_sync_preflight.md` (this session's
pre-flight grounding); `dr029/2_6_settlement_race/2_6_settlement_race.md`
(the locked source spec for the deferred §2.6 worker —
informational reference, not in scope here);
`workflows/bet_entry/v1/orchestrator.py:962-985` (the W6 contract
in the orchestrator).

## §3 — Pre-reads

Required:

1. `dr029/w4_bet_entry/w6_broader_sync_preflight.md` (pre-flight
   grounding, this session) — the empirical findings that anchor
   every spec decision in this brief.
2. `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
   §9.2 (settlement reads — the `market_settlement` surface),
   §9.8 (order-state reads — the `list_current_orders` surface
   shipped Session 101), §6 version-history (the brief assumes
   v1.4 latest with no version bump anticipated for W6 because no
   new W3 surfaces are added), §14.4 (backward-compatible-
   additions discipline; W6 does not exercise it).
3. `dr029/w4_bet_entry/w3_order_state_brief.md` §5 substantive
   scope sub-sections (the per-section discipline precedent W6
   mirrors), §10 hard limits (the brief-time discipline shape),
   §12 cross-references.

Reference-only — read on demand:

- `workflows/bet_entry/v1/orchestrator.py` — `MatchStatus`
  references; `_run_trigger_b` (line 957-1019);
  `_read_order_state_with_retry` (line 1021-1067); `ReadOk` /
  `ReadUnavailable` / `ReadOutcome[T]` discriminated union (line
  169-207); `BetfairAdapter` Protocol (line 210-269);
  `TriggerBScheduler` Protocol (line 282-385).
- `workflows/bet_entry/v1/models.py` — `MatchStatus` (line 42-56);
  `BetRecord` (line 191-225); `BetLeg` (line 142-189).
- `workflows/bet_entry/v1/storage.py` — `BetRecordStorage`
  Protocol (line 60-78); `_BETS_DDL` (line 92-112); `_LEGS_DDL`
  (line 114-127); `InMemoryBetRecordStorage` (line 134-205);
  `SQLiteBetRecordStorage` (line 213-360); `_row_to_record` (line
  363-389).
- `workflows/bet_entry/v1/betfair_adapter.py` — pre-existing
  adapter wraps for the three reads + `get_order_state` real
  wrap shipped Session 101 (line 192-217 region pre-Session-101;
  the adapter has grown post-ship).
- `clients/betfair_client/v1/current_orders.py` —
  `list_current_orders` surface shape (162 lines).
- `clients/betfair_client/v1/settlement.py` —
  `market_settlement` surface shape (118 lines).
- `clients/betfair_client/v1/envelope.py` — `ReadEnvelope[T]` /
  `FreshEnvelope` / `UnavailableReadEnvelope` /
  `BetfairReadUnavailableReason` enum.
- `tests/workflows/bet_entry/v1/test_orchestrator.py` —
  `MockBetfairAdapter` shape (line 1-160 region) for mock-impl
  precedent.
- `tests/workflows/bet_entry/v1/test_betfair_adapter.py` —
  adapter test patterns (773 lines; W6 tests mirror the pass-
  through coverage shape from Session 101 §4.2).
- `tests/workflows/bet_entry/v1/test_storage.py` — storage tests
  (262 lines) for the test pattern around DDL migrations.
- `decisions.md` — DR-019 (derived state on read), DR-021
  (timestamp anchoring, Adelaide local time), DR-027 / DR-028
  (cross-DB boundary discipline — W6 stays operational-line-only,
  no analytical-line reads), DR-030 (v3 repo layout), DR-031 (v3
  tech stack — Pydantic v2, pytest, ruff, import-linter, no
  Alembic at v1 per inline-DDL discipline below), DR-032
  (canonical reference layer for all bet records — `bet_legs`
  carries `betfair_market_id` + `betfair_selection_id` as
  canonical join keys for the W6 query strategy).

## §4 — System access

- **Mac filesystem read-write** at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Edit named anchors
  only per §10 hard limits.
- **No `betfair_client_contract.md` edits** — W6 does not add
  any new W3 read surface; the contract stays at v1.4. (If
  pre-flight inspection during Code execution surfaces a need
  for a new surface, that's a finding for the report, not an
  in-session contract edit.)
- **No VPS access.** This brief touches v3 codebase only; no
  `capture.db`, no VPS scrapers, no SSH paths.
- **No live Betfair API calls.** Test mocking only; no live REST
  or Streaming traffic. The new W6 module's correctness is
  verified via the existing mock infrastructure
  (`MockBetfairAdapter` plus the new mock-storage test patterns).
- **Read-write SQLite access** for the reference impl tests —
  the test storage uses `sqlite3` against a tmp-dir path per the
  existing `test_storage.py` precedent.
- **Adelaide local timestamps per DR-021** — every timestamp in
  the report (open anchor, close anchor, any test fixtures
  generating `last_reconciled_at` values) uses
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` via
  Desktop Commander or
  `datetime.now(tz=ZoneInfo("Australia/Adelaide"))`.

## §5 — Substantive scope sections

### §5.1 — New W4 module: `reconciliation.py`

Create `workflows/bet_entry/v1/reconciliation.py` (~200-280 lines
expected). Module exposes the worker entry point plus the
resolution-decision pure function.

**Public function signatures:**

```python
def run_reconciliation_pass(
    *,
    storage: BetRecordStorage,
    adapter: BetfairAdapter,
    age_threshold_seconds: float = DEFAULT_AGE_THRESHOLD_SECONDS,
    now: Callable[[], datetime] | None = None,
) -> ReconciliationPassResult:
    """Single sweep: query unreconciled bets, resolve each via
    `_resolve_one`, write updates. Idempotent across calls — the
    `last_reconciled_at` column gates re-reads within the
    age-threshold window.

    Returns a result envelope summarising the pass: total
    unreconciled bets seen, count resolved to each terminal
    status, count left provisional with reason, count of read
    failures.
    """
```

```python
def _resolve_one(
    *,
    record: BetRecord,
    adapter: BetfairAdapter,
) -> ResolutionDecision:
    """Pure function — given a bet record and an adapter,
    decide what the bet's match-state should resolve to.

    Reads (in order):
    1. `adapter.get_order_state(market_id, selection_id, bet_id,
       original_size)` — the W3 §9.8 surface via the adapter
       boundary.
    2. If `ReadOk` returns a snapshot showing the bet is still
       in unmatched (`found_in_unmatched=True`): keep
       `PROVISIONAL_PENDING` (or transition to it from
       `PROVISIONAL`); return ResolutionDecision with
       `new_status=PROVISIONAL_PENDING`.
    3. If `ReadOk` returns a snapshot showing matched_size > 0
       and unmatched_size == 0 and bet absent from unmatched
       (`found_in_unmatched=False`): bet is fully matched;
       return ResolutionDecision with
       `new_status=FINAL_FULL`.
    4. If `ReadOk` returns the resolved-out shape (the W3-side
       synthesised "absent from current orders" snapshot):
       fall through to step 5 (the §7.2 disambiguation path).
    5. Disambiguate absent-from-orders by reading
       `adapter.get_market_settlement(market_id)`:
       - Market not yet `settled_time`-stamped: bet is in the
         placement → settlement gap; if matched_size > 0 at
         placement, treat as `FINAL_FULL`; if matched_size == 0
         at placement, treat as `FAILED` (cancelled / voided /
         lapsed before any match took effect).
       - Market settled and runner `WINNER` / `LOSER` with the
         bet's matched_size > 0: terminal `FINAL_FULL`.
       - Market settled but runner `REMOVED` or market voided:
         terminal `FAILED`.
       - Read fails (`ReadUnavailable`): no decision; carry
         forward as `PROVISIONAL` with the unavailable-reason
         logged for triage visibility.
    6. If `ReadUnavailable` from step 1: no decision; carry
       forward as current status, increment
       `reconciliation_attempts`, set `last_reconciled_at`.
    """
```

**`ResolutionDecision` model (Pydantic v2 frozen):**

```python
class ResolutionDecision(BaseModel):
    """Output of `_resolve_one` — what the worker decided plus
    the reasoning trail for triage visibility.

    `new_status` is None when the read failed and no decision
    could be made; otherwise it carries the resolved status.
    `reason_code` is a stable identifier
    (`fully_matched_via_orders`, `still_pending_in_orders`,
    `absent_resolved_pre_settlement_full`,
    `absent_resolved_pre_settlement_failed`,
    `absent_resolved_post_settlement_terminal`,
    `absent_resolved_void_or_removed`,
    `read_unavailable_orders`,
    `read_unavailable_settlement`).
    `detail` carries the source snapshot or unavailable reason
    for log visibility.
    """

    model_config = ConfigDict(frozen=True)

    new_status: MatchStatus | None
    matched_stake: Decimal | None
    unmatched_stake: Decimal | None
    matched_price: float | None
    reason_code: Literal[
        "fully_matched_via_orders",
        "still_pending_in_orders",
        "absent_resolved_pre_settlement_full",
        "absent_resolved_pre_settlement_failed",
        "absent_resolved_post_settlement_terminal",
        "absent_resolved_void_or_removed",
        "read_unavailable_orders",
        "read_unavailable_settlement",
    ]
    detail: dict[str, Any] = Field(default_factory=dict)
```

**`ReconciliationPassResult` model (Pydantic v2 frozen):**

```python
class ReconciliationPassResult(BaseModel):
    """Per-pass summary returned by `run_reconciliation_pass`.

    Counters are inclusive of the pass itself (totals across the
    swept population, not deltas). For pass-over-pass deltas, a
    caller compares two `ReconciliationPassResult` instances.
    """

    model_config = ConfigDict(frozen=True)

    swept_count: int
    resolved_final_full: int
    resolved_final_partial: int
    resolved_failed: int
    transitioned_to_provisional_pending: int
    left_provisional_read_unavailable: int
    started_at: datetime  # Adelaide local
    finished_at: datetime
    pass_id: str  # uuid4 for log correlation
```

**Default cadence constant:**

```python
DEFAULT_AGE_THRESHOLD_SECONDS: float = 60.0
"""W6 v1 — bets younger than 60 seconds are not swept (Trigger
B's window). Calibrate from operational experience per the
post-DR-029 monitoring layer.
"""
```

**Logging:** the worker logs at `INFO` for the pass start /
finish, at `INFO` for each resolution decision, at `WARNING` for
`read_unavailable_*` outcomes. The log substrate is the existing
`logging.getLogger("workflows.bet_entry.v1.reconciliation")`
pattern. No structured-logging framework adoption at v1.

**Idempotency posture.** `_resolve_one` is read-side pure (no
writes). `run_reconciliation_pass` writes `update_match_status`
per the orchestrator's existing call path plus
`update_reconciliation_bookkeeping` for the
`last_reconciled_at` / `reconciliation_attempts` writes. The
storage Protocol calls are idempotent at the database level —
re-running the same pass twice produces the same final state
(same status, incremented attempt counter).

### §5.2 — `BetRecordStorage` Protocol extensions

`storage.py` Protocol gets two new methods:

```python
class BetRecordStorage(Protocol):
    # ... existing three methods unchanged ...

    def list_unreconciled_bets(
        self,
        *,
        statuses: tuple[MatchStatus, ...] = (
            MatchStatus.PROVISIONAL,
            MatchStatus.PROVISIONAL_PENDING,
        ),
        older_than: datetime | None = None,
        max_results: int = 100,
    ) -> list[BetRecord]:
        """Brief §5.2 — return bets matching the status filter,
        optionally older than the given timestamp (placement
        time), capped at `max_results` per call.

        Default `statuses` covers the W6 sweep population.
        Future callers (e.g. burst-review queries) may override
        with a different filter.

        `older_than` filters on `placed_at`, not
        `last_reconciled_at` — the worker uses
        `age_threshold_seconds` to compute this from the pass's
        start time.

        `max_results` caps a single pass at 100 bets to keep the
        worker's memory + Betfair-call budget bounded; the
        caller iterates passes if the population exceeds the
        cap.
        """
        ...

    def update_reconciliation_bookkeeping(
        self,
        bet_id: str,
        *,
        last_reconciled_at: datetime,
        attempts_increment: int = 1,
    ) -> WriteResult:
        """Brief §5.2 — bookkeeping write distinct from
        `update_match_status`. Increments
        `reconciliation_attempts` and stamps
        `last_reconciled_at`. Called once per
        bet-per-pass regardless of whether the pass produced a
        match-status transition.
        """
        ...
```

The two methods are added to both impls (`InMemoryBetRecordStorage`
and `SQLiteBetRecordStorage`).

### §5.3 — SQLite reference impl: schema additions + inline DDL migration

`storage.py` `_BETS_DDL` is updated with two new columns:

```sql
CREATE TABLE IF NOT EXISTS bets (
    -- ... existing columns unchanged ...
    last_reconciled_at           TEXT,           -- nullable; ISO8601 Adelaide
    reconciliation_attempts      INTEGER DEFAULT 0
);
```

Plus an inline idempotent migration in `_connect_and_init`:

```python
def _connect_and_init(self) -> None:
    with self._lock, self._connect() as conn:
        conn.execute(_BETS_DDL)
        conn.execute(_LEGS_DDL)
        # W6 v1 — inline DDL migration. Idempotent at startup.
        # When v3 adopts Alembic post-DR-029-close, this block
        # is replaced by an Alembic revision; the columns
        # themselves are part of `_BETS_DDL` so fresh installs
        # already have them.
        _add_column_if_missing(
            conn, "bets", "last_reconciled_at", "TEXT"
        )
        _add_column_if_missing(
            conn, "bets", "reconciliation_attempts",
            "INTEGER DEFAULT 0"
        )
```

`_add_column_if_missing` helper:

```python
def _add_column_if_missing(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    """Inline DDL migration helper — idempotent ALTER TABLE.

    SQLite's `PRAGMA table_info(<table>)` returns the existing
    column list; the helper adds the column if absent and is a
    no-op if present. Idempotent across startup invocations.

    v1 pattern (W6 brief §5.3). Replaced by Alembic revisions
    post-DR-029-close.
    """

    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {row["name"] for row in rows}
    if column in existing:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
```

`_row_to_record` updated to read the new columns and surface
them to `BetRecord` (per §5.4).

### §5.4 — `BetRecord` model: optional reconciliation fields

`models.py` `BetRecord` gets two new optional fields:

```python
class BetRecord(BaseModel):
    # ... existing fields unchanged ...

    # W6 v1 — reconciliation bookkeeping (brief §5.4)
    last_reconciled_at: datetime | None = None
    reconciliation_attempts: int = 0
```

Both default to None / 0 for backward compatibility with existing
records. Pydantic optional default handles parse-back from the
schema cleanly.

### §5.5 — `BetfairAdapter` Protocol extension: `get_market_settlement`

`orchestrator.py` `BetfairAdapter` Protocol grows one new read
method:

```python
class BetfairAdapter(Protocol):
    # ... existing methods unchanged ...

    def get_market_settlement(
        self, market_id: str
    ) -> ReadOutcome[MarketSettlement]:
        """W6 boundary read — bridges
        `clients.betfair_client.v1.settlement.market_settlement`
        (W3 §9.2 surface) to the W4 read-side discriminated
        union shape. Used by `_resolve_one` step 5 to
        disambiguate absent-from-orders bets via market-level
        settlement state.

        `MarketSettlement` is imported from
        `clients.betfair_client.v1.settlement`; the W4
        boundary translation lives in the adapter
        (`RealBetfairAdapter`) per the Session 101 §5.6
        precedent (W4 internals do not import the W3
        envelope's enum directly; reasons translate at the
        boundary).
        """
        ...
```

`RealBetfairAdapter.get_market_settlement` wraps the W3 surface
following the Session-101 pattern: catch
`UnavailableReadEnvelope` from the W3 surface; translate the
reason value to the literal-string set on `ReadUnavailable`;
wrap success as `ReadOk(snapshot=...)`.

### §5.6 — `MockBetfairAdapter` extension

`test_orchestrator.py` `MockBetfairAdapter` extended with:

- New setter `set_market_settlement(market_id, MarketSettlement
  | ReadUnavailable)` for pinning return values per market.
- New setter `set_market_settlement_unavailable(market_id,
  reason)` for pinning `ReadUnavailable` outcomes per market
  with a specific reason value.
- The mock keeps existing `set_*` API stable; W6 tests use the
  new setters for market-settlement scenarios.

### §5.7 — Worker scheduler Protocol

`reconciliation.py` defines:

```python
class ReconciliationScheduler(Protocol):
    """Worker scheduler — same shape pattern as
    `TriggerBScheduler`. Production scheduler uses a periodic
    timer or an asyncio loop in v3 build proper; tests use a
    deterministic stub that runs on demand.

    The scheduler is responsible for invoking
    `run_reconciliation_pass` at the configured cadence. The
    worker module itself stays cadence-agnostic.
    """

    def schedule_periodic(
        self,
        *,
        run: Callable[[], None],
        interval_seconds: float,
    ) -> None: ...
```

Plus reference impls:

- `ManualReconciliationScheduler` — never fires; tests call
  `flush()` to run all pending passes immediately. Mirrors
  `ManualTriggerBScheduler` shape.
- `ThreadingReconciliationScheduler` — daemon
  `threading.Timer` with `interval_seconds` re-scheduling
  itself after each call. Mirrors
  `ThreadingTriggerBScheduler` shape with the periodic-loop
  extension.

`DEFAULT_RECONCILIATION_INTERVAL_SECONDS: float = 300.0` (5
minutes — v1 placeholder; calibrate post-DR-029-close).

### §5.8 — `__init__.py` re-exports

`workflows/bet_entry/v1/__init__.py` updated to add re-exports
for the new public surfaces:

- From `reconciliation`: `run_reconciliation_pass`,
  `ResolutionDecision`, `ReconciliationPassResult`,
  `ReconciliationScheduler`, `ManualReconciliationScheduler`,
  `ThreadingReconciliationScheduler`,
  `DEFAULT_AGE_THRESHOLD_SECONDS`,
  `DEFAULT_RECONCILIATION_INTERVAL_SECONDS`.
- From `orchestrator`: `MarketSettlement` re-export added (the
  imported type from `clients.betfair_client.v1.settlement`
  surfaces at the W4 boundary now via `get_market_settlement`).
- From `storage`: no new re-exports — the new Protocol methods
  attach to existing exports.

Alphabetical order within the existing block structure.

### §5.9 — New tests (W6 worker surface)

`tests/workflows/bet_entry/v1/test_reconciliation.py` (new file).
Estimated 350-450 lines covering:

**Resolution-decision tests** (single-bet, mock-driven, ~10
tests):

- `test_resolve_fully_matched_via_orders` — adapter returns
  `ReadOk` with matched_size > 0 and `found_in_unmatched=False`;
  decision is `FINAL_FULL`.
- `test_resolve_still_pending_in_orders` — adapter returns
  `ReadOk` with `found_in_unmatched=True`; decision is
  `PROVISIONAL_PENDING`.
- `test_resolve_absent_pre_settlement_full` — adapter returns
  the resolved-out snapshot; market settlement read returns
  `ReadOk` with market not yet `settled_time`-stamped; record's
  `matched_size > 0` at placement; decision is `FINAL_FULL`.
- `test_resolve_absent_pre_settlement_failed` — adapter returns
  the resolved-out snapshot; market settlement read returns
  `ReadOk` with market not yet `settled_time`-stamped; record's
  `matched_size == 0` at placement; decision is `FAILED`.
- `test_resolve_absent_post_settlement_terminal` — adapter
  returns the resolved-out snapshot; market settlement read
  returns `ReadOk` with `settled_time` stamped and runner
  `WINNER`; decision is `FINAL_FULL`.
- `test_resolve_absent_void_or_removed` — adapter returns the
  resolved-out snapshot; market settlement read returns
  `ReadOk` with runner `REMOVED` or `market_voided=True`;
  decision is `FAILED`.
- `test_resolve_read_unavailable_orders` — adapter returns
  `ReadUnavailable` on `get_order_state`; decision is None
  (carry-forward), reason `read_unavailable_orders`.
- `test_resolve_read_unavailable_settlement` — adapter returns
  resolved-out from `get_order_state`, then `ReadUnavailable`
  on `get_market_settlement`; decision is None (carry-forward),
  reason `read_unavailable_settlement`.
- `test_resolve_pass_through_reason_orders` — for each of the
  seven `BetfairReadUnavailableReason` values, the orders-read
  unavailable path preserves the reason verbatim in
  `ResolutionDecision.detail`.
- `test_resolve_pass_through_reason_settlement` — same coverage
  for the settlement-read unavailable path.

**Pass-level tests** (multi-bet, mock-driven, ~6 tests):

- `test_pass_resolves_mixed_population` — three bets each in a
  different state (`PROVISIONAL`, `PROVISIONAL_PENDING`,
  `FINAL_FULL`); pass touches the first two only;
  pass-result counters reflect the resolutions.
- `test_pass_respects_age_threshold` — bet placed 30 seconds
  ago at pass start; `age_threshold_seconds=60`; bet is not
  swept.
- `test_pass_respects_max_results` — 150 unreconciled bets in
  storage; `max_results=100`; pass touches 100, leaves 50.
- `test_pass_increments_attempts_counter` — same bet swept
  three times across three passes; `reconciliation_attempts`
  ends at 3 even when no transition fires.
- `test_pass_idempotent_on_resolved` — bet in `FINAL_FULL`
  passed through `_resolve_one`-equivalent path is unchanged
  (the storage filter excludes terminal states); pass
  result's `swept_count` doesn't include it.
- `test_pass_handles_storage_failure` — storage.update_match_status
  returns failure; pass logs a warning, continues with the
  remaining bets, surfaces the failure count in
  `ReconciliationPassResult.left_provisional_read_unavailable`
  (the closest existing counter; W6.5 may add a dedicated
  storage-failure counter when the audit-trail substrate
  lands).

**Adelaide-local timestamp coverage** (1 test):

- `test_pass_uses_adelaide_local_timestamps` — pass-result
  `started_at` and `finished_at` are Adelaide-local on the
  pinned-clock fixture.

**Scheduler tests** (~3 tests):

- `test_manual_scheduler_pending_runs_on_flush`.
- `test_threading_scheduler_re_arms` — daemon timer fires
  twice within a controlled interval. (May skip if flaky in
  CI; the manual scheduler covers the contract surface.)
- `test_scheduler_passes_invocation_to_run_callback`.

### §5.10 — Adapter and orchestrator test updates

`test_betfair_adapter.py` adds tests for the new
`get_market_settlement` method (~5 tests):

- `test_get_market_settlement_open_unsettled` — market
  `CLOSED` but no `settled_time`; adapter returns `ReadOk`.
- `test_get_market_settlement_settled` — market `CLOSED` with
  `settled_time`; adapter returns `ReadOk` with settlement
  snapshot.
- `test_get_market_settlement_market_not_found_passes_through`
  — 404 on the W3 surface; adapter returns
  `ReadUnavailable(reason="betfair_market_not_found")`.
- `test_get_market_settlement_auth_expired_passes_through`.
- `test_get_market_settlement_api_unreachable_passes_through`.

`test_orchestrator.py` adds no new tests (the orchestrator
itself doesn't gain new behaviour — W6 is parallel substrate);
the mock setter additions per §5.6 are exercised by the new
`test_reconciliation.py`.

### §5.11 — Storage test updates

`test_storage.py` adds (~6 tests):

- `test_list_unreconciled_bets_empty` — empty store; returns
  empty list.
- `test_list_unreconciled_bets_filters_by_status` — three
  bets across `PROVISIONAL` / `FINAL_FULL` / `FAILED`; default
  status filter returns only `PROVISIONAL`.
- `test_list_unreconciled_bets_filters_by_age` — two bets, one
  placed before the threshold one after; older_than filter
  correctly partitions.
- `test_list_unreconciled_bets_respects_max_results`.
- `test_update_reconciliation_bookkeeping_increments`.
- `test_update_reconciliation_bookkeeping_stamps_timestamp`.

Plus migration coverage (~2 tests):

- `test_inline_migration_idempotent` — instantiating the SQLite
  storage twice doesn't raise on the duplicate
  `ALTER TABLE`.
- `test_pre_existing_db_gets_columns_added` — open a DB built
  by an old version of `_BETS_DDL` (without the W6 columns);
  the migration adds them on init; reads + writes succeed.

### §5.12 — Static structural-Protocol conformance unchanged

`BetRecordStorage` and `BetfairAdapter` Protocols remain
structural (PEP 544 protocols, `runtime_checkable=False`).
`InMemoryBetRecordStorage` / `SQLiteBetRecordStorage` and
`MockBetfairAdapter` / `RealBetfairAdapter` implement the
extended Protocols by virtue of method presence. No
`@runtime_checkable` decoration added; no `assert isinstance(x,
SomeProtocol)` checks added; existing import-linter contracts
remain kept.

## §6 — Sequencing within session

13 ordered steps with dependency reasoning. Code may deviate when
a different order is operationally cleaner; the brief specifies
the dependencies, not the literal step ordering.

1. Read `models.py`; add the two new optional fields to
   `BetRecord` per §5.4.
2. Read `storage.py`; extend `BetRecordStorage` Protocol per §5.2;
   add `_add_column_if_missing` helper per §5.3.
3. Update `_BETS_DDL` per §5.3.
4. Update `_connect_and_init` per §5.3 to call the migration
   helper for the two new columns.
5. Implement the two new methods on `InMemoryBetRecordStorage`
   per §5.2 (in-memory storage's filter / age / sort operations
   work on the existing in-memory record dict; bookkeeping
   write updates a model-copy of the record).
6. Implement the two new methods on `SQLiteBetRecordStorage`
   per §5.2 (parameterised SQL for the filter; UPDATE for the
   bookkeeping write).
7. Update `_row_to_record` per §5.4 to populate the two new
   fields from the SQLite row.
8. Read `orchestrator.py`; extend `BetfairAdapter` Protocol per
   §5.5; implement `get_market_settlement` on
   `RealBetfairAdapter`.
9. Read `tests/workflows/bet_entry/v1/test_orchestrator.py`;
   extend `MockBetfairAdapter` per §5.6.
10. Create `workflows/bet_entry/v1/reconciliation.py` with the
    Pydantic models per §5.1 + the worker functions per §5.1
    + the scheduler Protocol and impls per §5.7.
11. Update `workflows/bet_entry/v1/__init__.py` per §5.8.
12. Create
    `tests/workflows/bet_entry/v1/test_reconciliation.py` per
    §5.9. Run the test suite to a clean baseline.
13. Update `tests/workflows/bet_entry/v1/test_betfair_adapter.py`
    per §5.10 + `test_storage.py` per §5.11. Run full test
    suite again; ruff; import-linter.

The ordering minimises rework: schema and storage land before
the worker that depends on them; the adapter and mock land
before the worker tests that use them; the worker itself comes
together in one file; tests close out the session.

A sound deviation: implementing
`SQLiteBetRecordStorage.list_unreconciled_bets` and
`update_reconciliation_bookkeeping` (steps 6-7) before extending
the Protocol (step 2) is fine if Code finds it cleaner to write
the impl test-first. The Protocol extension in step 2 is the
contract; the impl satisfies it.

## §7 — Empirical verification

**Pre-baseline (Code captures at session open):**

- `pytest` count passing.
- `ruff check` clean / not clean.
- `import-linter` contracts kept.
- `git status` snapshot.
- `PRAGMA table_info(bets)` against a freshly-init storage
  instance — column count + names.

**Functional verification at close:**

- All `_resolve_one` decision paths exercised via the
  resolution-decision tests per §5.9 first sub-list.
- `run_reconciliation_pass` exercised end-to-end via the
  pass-level tests per §5.9 second sub-list.
- Storage-impl methods exercised for both
  `InMemoryBetRecordStorage` and `SQLiteBetRecordStorage` via
  the `test_storage.py` additions per §5.11.
- Inline DDL migration exercised idempotently per the migration
  coverage tests.
- `RealBetfairAdapter.get_market_settlement` exercised via the
  five new tests per §5.10.
- `MarketSettlement` returned from `clients.betfair_client.v1.settlement`
  parses cleanly through the W4 boundary on a synthetic Betfair
  payload (covered by the existing W3-side tests at
  `test_settlement.py`; W4-side coverage exercises the boundary
  translation only).

**Post-baseline (Code captures at session close):**

- `pytest` count passing — should be pre-count + ~30 to ~45
  net new tests.
- `ruff check` clean.
- `import-linter` contracts kept (5 contracts; no new ones
  added).
- `git status` snapshot.
- `PRAGMA table_info(bets)` shows the two new columns present.

## §8 — Output spec

**Single named output report** at
`dr029/w4_bet_entry/w6_broader_sync_report.md`.

**Section structure (12-section spine):**

1. Summary — what shipped, what didn't, test count delta, ruff
   / import-linter status.
2. Files changed — table with pre/post line counts and deltas.
3. Test count delta — pre-baseline + post-baseline + breakdown
   by test file.
4. New tests added — detailed list per §5.9 / §5.10 / §5.11
   with one-line descriptions.
5. Implementation notes — judgement calls Code made during
   execution (mock-shape choices, in-memory storage filter
   implementation, inline DDL migration nuances, etc.).
6. Deviations from brief — items where Code's empirical state
   diverged from brief specification, with operator-call
   notice (per the W3 report §6 precedent — version-history
   verification, namespace conventions, signature sub-features).
7. Open questions for triage — items needing operator input
   for routing in Session 104.
8. Findings (beyond brief scope; not actioned) — items
   surfaced during execution that aren't in the brief but
   warrant Session 104 triage visibility.
9. Self-assessment — pre/post baselines table, `git status`
   snapshots open and close, functional-verification check
   list, mocked-only confirmation, length flag, Adelaide-local
   timestamp confirmation per DR-021.

**Length anticipation:** 700-1100 lines. Within the 1000-line
surface-flag threshold per the W3 brief precedent (W3 report
shipped at 677 lines; W6 expected to land slightly higher
because the migration + scheduler substrate adds reportable
surface area).

**What the report does not contain:**

- No recommendations on next-brief direction (Session 104
  triage decides).
- No editorial on §2.6 (the deferred settlement-state worker
  brief is sequenced after W6; W6's report stays in W6's
  scope).
- No commentary on Alembic adoption timing (post-DR-029-close
  decision; outside W6's scope).
- No analytical-line capability commentary
  (`capture.db`-side concerns).

## §9 — Hard limits

Out of scope. Code does not, under any circumstance:

- Edit `betfair_client_contract.md` — W6 adds no new W3
  surface; the contract stays at v1.4.
- Edit `decisions.md`, `architecture.md`, `governance.md`,
  `vision.md`, `v3_data_requirements.md`, `project_context.md`,
  `standing_instructions.md` — governance docs are operator-
  Claude territory, not Code.
- Add a new W3 read surface — the brief's resolution strategy
  uses the existing v1.4 surfaces (`list_current_orders` §9.8 +
  `market_settlement` §9.2). If pre-flight inspection during
  Code execution surfaces a need for `listClearedOrders` or
  any other new W3 surface, the brief's design fails forward as
  a finding for Session 104, not an in-session contract bump.
- Implement the §2.6 settlement-state reconciliation worker.
  That's a separate brief sequenced after W6 lands.
- Add a `settlement_state` field to `BetRecord`. §2.8 §6.4
  named it; W4 didn't ship it; W6 doesn't either. The §2.6
  worker brief adds it.
- Adopt Alembic. The inline DDL migration helper per §5.3 is
  the v1 pattern; Alembic adoption is sequenced post-DR-029-
  close.
- Add an audit-log substrate. The named-debt audit-trail
  question stays parked.
- Modify the modal-layer copy or any W7-territory display
  logic. The reconciliation-derived match status values are
  read by W7 as substrate; W6 doesn't render them.
- Run live Betfair API calls. Test fixtures only.
- Touch the v2 codebase or v2's `bethub.db`.
- Edit the analytical-line side (`capture.db`, the VPS
  scrapers, `vps_client_contract.md`).
- Run `git add`, `git commit`, `git stash`, `git restore`,
  `git checkout` (file-targeted), or `git reset`. Working
  tree management is operator territory.
- Drift outside named anchors. The substrate edits are
  precisely the files named in §5; any related change ("while
  we're here, this also needed updating") surfaces as a
  finding in the report, not an in-session edit.
- Continue past the single bounded session. If the work
  doesn't fit, that's a finding in §6 / §7 of the report, not
  a continuation.

## §10 — Dirty-tree handling

Working tree at session open is expected to match the
post-Session-101 state. The brief's named anchors are:

- `workflows/bet_entry/v1/models.py` (existing; modified at
  step 1).
- `workflows/bet_entry/v1/storage.py` (existing; modified at
  steps 2-7).
- `workflows/bet_entry/v1/orchestrator.py` (existing;
  modified at step 8).
- `workflows/bet_entry/v1/betfair_adapter.py` (existing;
  modified at step 8).
- `workflows/bet_entry/v1/reconciliation.py` (new file;
  created at step 10).
- `workflows/bet_entry/v1/__init__.py` (existing; modified at
  step 11).
- `tests/workflows/bet_entry/v1/test_orchestrator.py`
  (existing; modified at step 9).
- `tests/workflows/bet_entry/v1/test_reconciliation.py` (new
  file; created at step 12).
- `tests/workflows/bet_entry/v1/test_betfair_adapter.py`
  (existing; modified at step 13).
- `tests/workflows/bet_entry/v1/test_storage.py` (existing;
  modified at step 13).

No `git add`, no commits, no stash, no restore, no checkout.
Read working-tree state at session start. Edit only named
anchors. After each edit, `git diff <file>` to confirm only
intended changes were added. At session close, `git status` to
confirm dirty file list = pre-existing untracked/modified +
named anchors only.

If dirty regions intersect named anchors at session start,
surface the conflict as a finding before commencing edits.

## §11 — What happens after Code's session

Session 104 reads the W6 report end-to-end via the inventory-
first cadence (sweep candidate l, third concrete use). Walk
the report's deviations / open questions / findings in single-
round inventory. Flag each as no-call (Code's territory, ack
only) or operator-call (warrants routing).

Possible Session 104 outcomes:

- **All clean** — W6 shipped end-to-end; route to next workflow
  brief (W7 per the locked sequence) or to the W6.5 settlement-
  state worker brief if operator wants to interleave.
- **Findings to action** — Code surfaces something needing
  operator-Claude routing before forward sequencing. Specific
  items become inputs to Session 105 brief drafting.
- **Partial coverage with named-debt** — analogous to Sessions
  99-100's stub-with-finding pattern; next brief picks up the
  named-debt.

Sequence after Session 104:

- Session 105+ — depending on Session 104 outcome.
- W7 brief drafting — sequenced after W6 lands cleanly.
- W6.5 settlement-state worker brief drafting — sequenced
  after W7 unless operator chooses to interleave with W6's
  triage.
- Composition-root structural decision drafting — sequenced
  after W7.
- v3 build proper — sequenced after composition-root locks.

## §12 — Cross-references

**Scope-doc anchors:**

- `dr029/dr029_scope.md` §2.9 (write-side bet-entry coherence —
  closes this brief's downstream connection).
- `dr029/2_6_settlement_race/2_6_settlement_race.md` (the
  load-bearing source spec for the deferred §2.6 / W6.5
  settlement-state worker brief).

**DRs invoked:**

- DR-019 (derived state on read) — context for the
  reconciliation read pattern (W6's reads are derivative of
  Betfair's authoritative state; v3 doesn't cache the result
  beyond the bet-record fields).
- DR-021 (timestamp anchoring, Adelaide local time) — applies
  to all timestamps in the worker, the report, and the test
  fixtures.
- DR-027 / DR-028 (cross-DB boundary discipline) — load-bearing.
  W6 reads only operational-line surfaces (Betfair direct via
  `betfair_client`); no `capture.db` reads. The
  by-reference-only rule is preserved structurally — bet
  records carry `betfair_market_id` / `betfair_selection_id`
  per DR-032 §1; W6 uses these as canonical join keys for the
  Betfair-side queries.
- DR-030 (v3 repo layout and module-boundary discipline) — W6
  module placement at `workflows/bet_entry/v1/reconciliation.py`
  follows the existing W4 module layout. W4 internals do not
  import the W3 envelope's enum directly per the Session 101
  precedent.
- DR-031 (v3 tech stack) — Pydantic v2, pytest, ruff,
  import-linter discipline. SQLite WAL per existing
  `SQLiteBetRecordStorage`. No Alembic at v1 (sequenced
  post-DR-029-close).
- DR-032 (canonical reference layer for all bet records) —
  `bet_legs` carries `betfair_market_id` / `betfair_selection_id`;
  W6 queries Betfair using these as canonical join keys.

**Prior reports / briefs / sessions:**

- `dr029/w4_bet_entry/w3_order_state_brief.md` (Session 101
  brief) — twelve-section spine precedent; the universal shape
  W6 mirrors.
- `dr029/w4_bet_entry/w3_order_state_report.md` (Session 102
  triage source) — Code's report on the W3 surface ship; the
  §7.2 finding that W6 closes is in this report.
- `dr029/w4_bet_entry/w3_order_state_preflight.md` (Session
  101) — pre-flight precedent for the brief discipline.
- `dr029/w4_bet_entry/real_adapter_brief.md` /
  `real_adapter_report.md` (Sessions 99-100) — earlier
  contract-work brief precedent.
- `dr029/w4_bet_entry/w4_bet_entry_brief.md` (Sessions 87+) —
  W4 substrate brief; §8.6 broader-sync reconciliation carry
  source.
- `sessions/SESSION_102.md` — Option A locked at §7.2; W6
  sequenced.
- `sessions/SESSION_101.md` — W3 brief drafting precedent.

**Parking-lot exclusions referenced inline:**

- §2.6 settlement-state worker (sequenced as W6.5; references
  inline in §1, §2, §9, §11).
- Alembic adoption (sequenced post-DR-029-close; referenced
  inline in §1, §5.3, §9).
- Audit-trail durable substrate (sequenced post-DR-029-close;
  referenced inline in §1, §5.1).
- Past-settlement-window threshold calibration (§2.6 §3.3; v3
  operational parameter, not W6).
- §2.9 §4.4 six edge cases (analytical-line side; awareness
  not mitigation; referenced for completeness).
- F5 `strategy_tag` carry — W6 reads `strategy_tag` from
  `BetRecord` for log visibility but does not branch on it;
  the carry is informational, closed by virtue of the carry
  being read (not actively mitigated as a separate concern).
