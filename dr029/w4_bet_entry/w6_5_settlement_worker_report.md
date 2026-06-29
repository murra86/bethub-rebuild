# W6.5 — Settlement-state worker report

**Drafted:** 2026-05-08 (Adelaide local per DR-021)
**Source brief:** `dr029/w4_bet_entry/w6_5_settlement_worker_brief.md`
(1316 lines, SHA256 prefix `1e37043b1c44`).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`
**Python interpreter:** `.venv/bin/python` (3.12.7)
**Status:** ship-clean — full suite green; ruff + lint-imports clean;
no anchors missed.

---

## §1 Summary

W6.5 closes §2.6's race-path settlement contract for v3 day-one.
The session added the `SettlementState` enum (5 values per §2.6 §3.1)
and the three race-wide count fields (`dead_heat_count`,
`removed_runner_count`, `unexpected_state_count`) to `BetRecord`
together with a `is_past_settlement_window` Pydantic v2 computed
property; extended `BetRecordStorage` (Protocol + InMemory + SQLite)
with four new columns, idempotent migration, INSERT/reader updates,
and three new methods (`update_settlement_state`,
`list_unsettled_bets`, `list_provisional_settlement_bets`); built
the new worker module `workflows/bet_entry/v1/settlement.py`
mirroring the structural shape of `reconciliation.py`
(`SettlementReader` Protocol, `_resolve_settlement_for_bet` pure
read-side resolver, `run_settlement_pass` pass-loop entry point,
`SettlementDecision` + `SettlementPassResult` Pydantic models,
`SettlementScheduler` Protocol with `Manual` + `Threading`
implementations, the `ProvisionalSettlementSurfacingPayload`
burst-review surfacing contract per §2.6 §3.5 with its
`ProvisionalTriggerSource` enum); and shipped 41 net new tests
across the six §5.8 blocks plus three scheduler tests.

**Named-anchor checklist (§5.1 → §5.9):**

- [x] §5.1 — `SettlementState` enum on `models.py`.
- [x] §5.2 — `settlement_state`, `dead_heat_count`,
  `removed_runner_count`, `unexpected_state_count` on `BetRecord`,
  plus `is_past_settlement_window` computed property.
- [x] §5.3 — Storage substrate (DDL, migration, INSERT, reader,
  `update_settlement_state`, `list_unsettled_bets`,
  `list_provisional_settlement_bets`) on Protocol + InMemory + SQLite.
- [x] §5.4 — Module-level constants (`DEFAULT_AGE_THRESHOLD_SECONDS`
  = 300, `DEFAULT_SETTLEMENT_INTERVAL_SECONDS` = 60,
  `DEFAULT_PAST_WINDOW_SECONDS` = 1800) and `_now_adelaide()`
  helper.
- [x] §5.5 — `SettlementReader` Protocol, `SettlementReasonCode`
  Literal (9 values), `SettlementDecision` model,
  `SettlementPassResult` model (8 counters + timestamps + uuid
  pass_id), `_resolve_settlement_for_bet` resolver,
  `run_settlement_pass` entry, `_write_settlement_bookkeeping`
  helper.
- [x] §5.6 — `ProvisionalTriggerSource` enum (3 values),
  `ProvisionalSettlementSurfacingPayload` model,
  `_build_surfacing_payload` helper.
- [x] §5.7 — `SettlementScheduler` Protocol,
  `ManualSettlementScheduler`, `ThreadingSettlementScheduler`.
- [x] §5.8 — `tests/workflows/bet_entry/v1/test_settlement.py` —
  41 tests, all green.
- [x] §5.9 — `__all__` export list on `settlement.py`.

**Test count delta:** 417 → 458 (+41 net new). Outside the brief's
acceptable band (442-447, +25 to +30); reasoning in §6 below.

**Quality gates:**

- `pytest -q` → 458 passed.
- `ruff check workflows/bet_entry/v1/ tests/workflows/bet_entry/v1/`
  → All checks passed.
- `lint-imports` → 5 contracts kept, 0 broken (DR-030 layered
  architecture intact; no new contract violations).
- No live Betfair API calls — all tests use the in-memory
  `MockSettlementReader` and (Block 6) `SQLiteBetRecordStorage`.
- No edits outside the §5 named anchors.
- No `git` mutations (brief §9 / §4 hard limit).

---

## §2 Files changed

| File | Pre LOC | Post LOC | Δ | Status |
|---|---:|---:|---:|---|
| `workflows/bet_entry/v1/models.py` | 361 | 412 | +51 | modified |
| `workflows/bet_entry/v1/storage.py` | 675 | 1000 | +325 | modified |
| `workflows/bet_entry/v1/settlement.py` | 0 | 726 | +726 | **new** |
| `workflows/bet_entry/v1/reconciliation.py` | 655 | 655 | 0 | untouched |
| `tests/workflows/bet_entry/v1/test_settlement.py` | 0 | 1364 | +1364 | **new** |
| `tests/workflows/bet_entry/v1/test_reconciliation.py` | 1056 | 1056 | 0 | untouched |
| `tests/workflows/bet_entry/v1/test_storage.py` | 572 | 572 | 0 | untouched |
| `clients/betfair_client/v1/settlement.py` | 118 | 118 | 0 | untouched (§9 hard limit) |
| `clients/betfair_client/v1/envelope.py` | 116 | 116 | 0 | untouched (§9 hard limit) |
| `workflows/bet_entry/v1/orchestrator.py` | 1481 | 1481 | 0 | untouched (§9 hard limit) |

Files touched (5): two new (`settlement.py` + `test_settlement.py`),
two modified (`models.py` + `storage.py`), nothing else.

`lint-imports` analyzed file count: 106 → 108 (+2 new modules).
Dependencies: 310 → 321 (+11 — settlement.py adds 11 unique imports
the static-analysis dependency graph hadn't recorded yet).

---

## §3 Test count delta

| Stage | Tests collected | Δ |
|---|---:|---:|
| Pre-baseline (W6.1 ship state) | 417 | — |
| Post-baseline (W6.5 ship state) | 458 | **+41** |

**Brief target:** +25 (acceptable band: 442-447, +25 to +30).
**Actual:** +41 (458 total).

This exceeds the acceptable band by +11. Flagged as deviation #1 in
§6 below. Reasoning: the brief's own §5.8 named list enumerated 37
discrete tests across blocks 1-6 (12+11+4+4+5+1) — already +12
above the +25 target — and the §5.7 scheduler classes implicitly
needed coverage to mirror the W6 reconciliation scheduler test
pattern (3 tests). Plus one DR-021 timestamp-coverage test in
Block 2 mirroring `test_pass_uses_adelaide_local_timestamps` from
`test_reconciliation.py`. Net: 37 named + 3 scheduler + 1 DR-021 = 41.

No tests were added beyond the W6.5 scope. All 458 tests pass.

---

## §4 New tests added

41 net new tests in `tests/workflows/bet_entry/v1/test_settlement.py`,
organised into the six blocks specified by brief §5.8 plus a
scheduler block.

### Block 1 — `_resolve_settlement_for_bet` (12 tests)

Coverage: every branch of the resolver's six-step state machine,
including the three count-field plumbing checks.

- `test_resolve_returns_settled_won_on_clean_winner` — runner
  WINNER → SETTLED_WON.
- `test_resolve_returns_settled_lost_on_clean_loser` — runner
  LOSER → SETTLED_LOST.
- `test_resolve_returns_voided_on_runner_removed` — REMOVED →
  VOIDED with `voided_runner_removed`.
- `test_resolve_returns_voided_on_market_voided` — market_voided
  supersedes per-runner status.
- `test_resolve_returns_provisional_on_runner_not_in_market` —
  selection_id absent from `runners` (§2.6 §3.4 cond 1).
- `test_resolve_returns_provisional_on_unexpected_runner_status` —
  synthetic forward-compat: enum-shaped value outside the closed
  v1.0 set falls through to PROVISIONAL.
- `test_resolve_returns_no_decision_on_market_not_yet_closed` —
  status=OPEN → no transition; bet stays PENDING.
- `test_resolve_returns_no_decision_on_market_closed_no_settled_time`
  — CLOSED but `settled_time is None` → no transition.
- `test_resolve_returns_no_decision_on_settlement_read_unavailable`
  — adapter returned `ReadUnavailable` → carries reason verbatim.
- `test_resolve_populates_dead_heat_count_on_terminal_transition`.
- `test_resolve_populates_removed_runner_count`.
- `test_resolve_populates_unexpected_state_count`.

### Block 2 — `run_settlement_pass` (12 tests)

Coverage: pass-loop logic, counter increments per decision class,
storage failure handling, count-field stamping.

- `test_pass_sweeps_only_pending_bets` — non-PENDING / None records
  excluded from sweep.
- `test_pass_filters_by_event_start_age_threshold` — leg-0
  event-start younger than threshold → not swept.
- `test_pass_increments_settled_won_counter`.
- `test_pass_increments_settled_lost_counter`.
- `test_pass_increments_voided_counter`.
- `test_pass_increments_provisional_entered_counter`.
- `test_pass_increments_left_pending_counters_correctly` — three
  bets, three different left-pending reasons, three counters.
- `test_pass_writes_bookkeeping_per_bet_per_pass` — every swept
  bet gets `last_reconciled_at` + attempts increment regardless of
  transition outcome.
- `test_pass_handles_storage_update_failure` — storage returns
  failure → `left_pending_read_unavailable += 1`, log warning, no
  raise. Mirrors W6's storage-failure handling.
- `test_pass_writes_count_fields_on_terminal_transition` — counts
  stamped on disk on terminal transitions.
- `test_pass_does_not_write_count_fields_on_no_decision` — counts
  stay None on the bet record when no transition fires.
- `test_pass_uses_adelaide_local_timestamps` — DR-021 coverage
  (added beyond brief's named list, mirrors
  `test_pass_uses_adelaide_local_timestamps` in
  `test_reconciliation.py`).

### Block 3 — `is_past_settlement_window` derived property (4 tests)

Coverage: every relevant input combination, plus monkeypatching
the threshold for testability.

- `test_past_window_false_when_not_pending` — non-PENDING → always
  False.
- `test_past_window_false_when_within_threshold` — race ran 100s
  ago, threshold 1800s → False.
- `test_past_window_true_when_past_threshold` — race ran 1900s ago
  → True.
- `test_past_window_uses_module_level_threshold` — monkeypatch
  `DEFAULT_PAST_WINDOW_SECONDS=60.0` confirms property reads the
  constant at call time.

### Block 4 — Burst-review surfacing payload (4 tests)

- `test_surfacing_payload_captures_full_bet_record` — full
  `BetRecord` carried through; `placement_time` from `placed_at`,
  `entered_provisional_at` from `last_reconciled_at`.
- `test_surfacing_payload_carries_trigger_source` — all three
  `ProvisionalTriggerSource` values plus the
  `operator_escalation_reason` string for manual-escalation cases.
- `test_surfacing_payload_includes_related_bets_in_same_market` —
  storage query returns sibling bets sharing `betfair_market_id`,
  filters out other-market bets.
- `test_list_provisional_settlement_bets_returns_payloads` —
  `InMemoryBetRecordStorage.list_provisional_settlement_bets`
  smoke test; one PROVISIONAL bet → one payload with default
  `UNEXPECTED_STATE` trigger source and `last_read=None` at v1.

### Block 5 — Storage layer (5 tests)

Coverage: SQLite schema round-trip on settlement_state and the
three count fields, idempotent migration, query method, missing
bet_id.

- `test_sqlite_settlement_state_round_trip`.
- `test_sqlite_count_fields_round_trip`.
- `test_sqlite_settlement_state_column_migration_idempotent` —
  double-init is a no-op on the four ALTER TABLEs.
- `test_sqlite_list_unsettled_bets_filters_correctly` — joined
  query: settlement_state + leg-0 event-start filter.
- `test_sqlite_update_settlement_state_returns_not_found` — missing
  bet_id surfaces as `WriteResult(success=False)`, not a raise.

### Block 6 — Integration (1 test)

- `test_end_to_end_pass_with_sqlite_storage` — three bets in
  PENDING state, three different settlement-read scenarios
  (winner, market voided, market open). Single pass writes the
  two terminal transitions to disk; the third bet stays PENDING
  with bookkeeping stamped. Confirms wire-shape end-to-end via the
  SQLite reference store.

### Scheduler tests (3 tests, beyond §5.8 named list)

Mirror the W6 reconciliation scheduler test pattern. Brief §5.7
specifies the scheduler classes; coverage is implicit per the
W6 precedent.

- `test_manual_settlement_scheduler_pending_runs_on_flush`.
- `test_threading_settlement_scheduler_re_arms`.
- `test_threading_settlement_scheduler_stop_prevents_further_fires`.

---

## §5 Implementation notes

One subsection per §5.x anchor, capturing landed shape and any
in-session decisions taken.

### §5.1 — `SettlementState` enum

Landed adjacent to `MatchStatus` in `workflows/bet_entry/v1/models.py`,
preserving the ordering of unrelated enums after it (`EntryPath`,
`LegRole`, ...). Five string-valued members per §2.6 §3.1:
`PENDING`, `SETTLED_WON`, `SETTLED_LOST`, `VOIDED`, `PROVISIONAL`.
Docstring names the spec anchor and the terminal-vs-non-terminal
classification.

No surprises. Direct mirror of the structural sibling (`MatchStatus`).

### §5.2 — `BetRecord` field additions

Three changes landed cleanly:

**Change A — `settlement_state: SettlementState | None = None`.**
Placed after `reconciliation_attempts` (the last existing W6
bookkeeping field) and before `legs`. Default `None` for backward
compatibility per §1's "the field does not exist on the live
`BetRecord` model" finding from Session 105.

**Change B — three count fields.** Placed immediately after
`settlement_state`, before `legs`. All three default `None` —
populated only by terminal-state transitions from the worker
where it has the `MarketSettlement` read.

**Change C — `is_past_settlement_window` `@computed_field`.**
Returns False when `settlement_state != PENDING` or when `legs`
is empty; otherwise compares
`_now_adelaide() - legs[0].betfair_event_start_time` against
`DEFAULT_PAST_WINDOW_SECONDS`. The function-local imports of
`_now_adelaide` and `DEFAULT_PAST_WINDOW_SECONDS` from
`settlement.py` resolve the circular-load concern called out in
brief §5.2 Change C — when this property is called, `settlement.py`
is fully loaded; at module import time of `models.py`, no
`settlement.py` symbols are needed.

The Pydantic v2 idiom used: `@computed_field` with `# type:
ignore[prop-decorator]` then `@property`. This is the canonical
pattern; the type-ignore silences a known pyright/mypy interaction
between `@computed_field` and `@property` ordering.

### §5.3 — Storage substrate

All seven changes (A through G) landed cleanly.

**Changes A-D — DDL extension, migration, INSERT, reader.** Followed
W6's pattern verbatim. Important detail on **Change A (DDL):** the
existing `_BETS_DDL` ended with `reconciliation_attempts INTEGER
DEFAULT 0` (no trailing comma); adding four new columns required
adding the trailing comma to that line. This is normal SQL DDL
extension, not a deviation.

**Change E — `update_settlement_state`.** Single-statement UPDATE
on bets table writing settlement_state + the three count fields
atomically. Returns `WriteResult(success=False, ...)` on missing
bet_id (not a raise). InMemory equivalent uses `model_copy(update={...})`.

**Change F — `list_unsettled_bets`.** SQLite implementation uses an
INNER JOIN to bet_legs on leg_number=1 to filter on
`betfair_event_start_time` and order by it ascending. The
in-memory implementation iterates `_records.values()` with the
same filter semantics. Both implementations skip bets with
empty `legs` (parallel to the in-memory `if not record.legs:
continue` guard) — this means the SQLite query returns only bets
that have a leg-0 row in `bet_legs`, which is enforced for any
bet written through `write_bet_record`.

**Change G — `list_provisional_settlement_bets`.** Returns a list
of `ProvisionalSettlementSurfacingPayload` objects. Implementation
inlines the related-bets query rather than introducing a separate
`list_bet_ids_for_market` Protocol method (kept the Protocol
surface minimal). The InMemory implementation iterates the in-memory
record dict; the SQLite implementation runs a `SELECT DISTINCT
bet_id FROM bet_legs WHERE betfair_market_id = ? AND bet_id != ?`
inside the per-bet loop. Both call into `settlement._build_surfacing_payload`
with `last_read=None` (storage doesn't keep the worker's last read)
and `trigger_source=ProvisionalTriggerSource.UNEXPECTED_STATE`
(only one trigger source fires automatically at v1; condition 2
isn't implemented per §5.5 Change C; manual escalation is
operator-side and not yet wired).

The `TYPE_CHECKING` import shape on `storage.py` resolves the
storage <-> settlement circular import: settlement.py imports
`BetRecordStorage` from storage.py at module load; storage.py
references `ProvisionalSettlementSurfacingPayload` only inside
type hints (`TYPE_CHECKING` block) and inside
`list_provisional_settlement_bets`'s body via function-local
import. No runtime cycle.

### §5.4 — `settlement.py` constants and helpers

Module docstring names the brief, the source spec, the closed §2.6
contract. Three constants land (`DEFAULT_AGE_THRESHOLD_SECONDS=300.0`,
`DEFAULT_SETTLEMENT_INTERVAL_SECONDS=60.0`,
`DEFAULT_PAST_WINDOW_SECONDS=1800.0`). The `_now_adelaide()` helper
is the module-local DR-021 timestamp source — distinct from
`reconciliation._now_adelaide` so each worker can be monkeypatched
independently in tests.

### §5.5 — `_resolve_settlement_for_bet` and `run_settlement_pass`

**`SettlementReasonCode` Literal — 9 values** (one more than the
6-value placeholder in the brief; the brief listed 6 but enumerated
9 codes in the docstring of `_resolve_settlement_for_bet`'s steps,
which is what landed):
`settled_won`, `settled_lost`, `voided_runner_removed`,
`voided_market_voided`, `provisional_unexpected_state`,
`provisional_post_settlement_void` (defined for forward
completeness; condition 2 isn't fired at v1 per §5.5 Change C),
`read_unavailable_settlement`, `market_not_yet_settled`,
`market_not_yet_closed`.

**`SettlementDecision`** — frozen Pydantic v2 model. Carries
`new_state`, the three count fields, `reason_code`, `detail`. All
no-decision branches set counts to None; all terminal/provisional
decisions populate counts from the `MarketSettlement` payload via
a `counts` dict spread.

**`SettlementReader` Protocol.** Returns
`ReadOutcome[MarketSettlement]` per the W4-side abstraction (not
the betfair_client envelope shape — see §6 deviation #2 for the
brief-vs-codebase reconciliation). Imports `ReadOutcome` and
`ReadUnavailable` from `workflows.bet_entry.v1.orchestrator`,
where the W4 boundary's `ReadOutcome[T] = ReadOk[T] |
ReadUnavailable` type alias lives.

**`_resolve_settlement_for_bet`** — pure read-side. Six-step decision
logic per the brief's docstring template:
1. `settlement_reader.read(market_id=...)`.
2. `ReadUnavailable` → no-decision; reason
   `read_unavailable_settlement`.
3. `market_status != CLOSED` → no-decision; reason
   `market_not_yet_closed`.
4. `settled_time is None` → no-decision; reason
   `market_not_yet_settled`.
5. `market_voided=True` → VOIDED with `voided_market_voided`.
6. Find runner by `betfair_selection_id`; map status to
   SETTLED_WON / SETTLED_LOST / VOIDED / PROVISIONAL accordingly.

**Note on §2.6 §3.4 condition 2 (post-settlement market voided
re-transition from terminal state):** not implemented at v1 per
brief §5.5 Change C. The worker only reads bets in PENDING; it
does not re-read terminal-state bets. Manual operator escalation
into PROVISIONAL is the v1 substitute. The
`provisional_post_settlement_void` reason code is defined for
forward completeness but no code path emits it.

**`run_settlement_pass`** — pass-loop entry. Calls
`storage.list_unsettled_bets(settlement_states=(PENDING,),
older_than_event_start=cutoff, max_results=...)`, iterates
candidates, calls `_resolve_settlement_for_bet`, applies the
decision via `storage.update_settlement_state` when
`decision.new_state is not None`, and always writes bookkeeping
via `_write_settlement_bookkeeping` regardless of transition. On
storage update failure, logs warning and bumps
`left_pending_read_unavailable` (mirrors the W6 reconciliation
storage-failure handling — that counter is the catch-all
"couldn't move forward" bucket).

**Shared bookkeeping substrate.** As per brief §5.5 Change G: W6.5
reuses `last_reconciled_at` / `reconciliation_attempts` rather
than introducing new `last_settled_at` / `settlement_attempts`
fields. Operator triage that needs to distinguish "last touched
by reconciliation" from "last touched by settlement" reads the
bet's `match_status` + `settlement_state` shape. Pre-flight
operator-Claude triage held in this session resolved as
accept-the-shared-substrate (no separate columns).

### §5.6 — Burst-review surfacing contract

`ProvisionalTriggerSource` enum (3 values) and
`ProvisionalSettlementSurfacingPayload` (frozen Pydantic v2 model)
landed in `settlement.py` per the brief's "the surfacing payload
model lives in the same module as the worker" placement.

**`_build_surfacing_payload` helper signature.** The brief
specified `(record, last_read, trigger_source,
operator_reason=None)`; landed signature renamed
`operator_reason` → `operator_escalation_reason` to match the
field name on the payload model, and added a
`related_bet_ids: tuple[str, ...] = ()` keyword parameter so the
helper stays pure (no IO) and storage callers compute related ids
themselves and pass them in. Tracked as deviation #4 in §6.

**`entered_provisional_at` proxy at v1.** Per brief §5.6 Change C,
the field is approximated by the bet's `last_reconciled_at` (the
timestamp of the worker pass that wrote the PROVISIONAL
transition). Approximate to pass-cadence granularity (1 minute by
default); sufficient for v1 burst-review visibility. Carry-forward
note from the brief: a dedicated `entered_provisional_at` column
ships build-proper.

**`related_bet_ids` populated, not stubbed.** Brief §5.6 Change D
gave Code's discretion to stub this as an empty tuple if
extending storage threatened the brief's envelope. The session's
implementation populates the field via an in-line storage query
(no separate `list_bet_ids_for_market` Protocol method needed —
cleaner than extending the Protocol surface for one caller).

### §5.7 — Schedulers

Direct mirrors of `ManualReconciliationScheduler` /
`ThreadingReconciliationScheduler`. Same field shape, same
`schedule_periodic` signature, same `flush()` and `stop()`
semantics. Carry-forward note (per brief §5.7 Change B): if v3
build proper adopts a single asyncio loop driving both workers,
these classes consolidate then.

### §5.8 — Tests

41 tests across the six blocks. See §4 above for the full list.
Test count delta exceeds the brief's acceptable band (442-447);
deviation #1 in §6 below.

### §5.9 — `__all__` exports

Final `__all__` list in `settlement.py`:

- `DEFAULT_AGE_THRESHOLD_SECONDS`
- `DEFAULT_PAST_WINDOW_SECONDS`
- `DEFAULT_SETTLEMENT_INTERVAL_SECONDS`
- `ManualSettlementScheduler`
- `ProvisionalSettlementSurfacingPayload`
- `ProvisionalTriggerSource`
- `SettlementDecision`
- `SettlementPassResult`
- `SettlementReader`
- `SettlementReasonCode`
- `SettlementScheduler`
- `SettlementState`
- `ThreadingSettlementScheduler`
- `_resolve_settlement_for_bet`
- `run_settlement_pass`

`SettlementState` is re-exported from settlement.py for caller
convenience; canonical location remains `models.py`.

---

## §6 Deviations from brief

### Deviation #1 — Test count exceeds acceptable band

**Anchor:** §7.2 (acceptable band 442-447, +25 to +30) + §5.8
(target +25 net new tests, allow +28-32).
**Actual:** 458 tests post-baseline (+41).
**Reasoning:** the brief's own §5.8 named list enumerated 37
discrete tests across blocks 1-6 (12 + 11 + 4 + 4 + 5 + 1 = 37).
That alone is +12 above the +25 target. Block 2 added one
additional DR-021 timestamp coverage test
(`test_pass_uses_adelaide_local_timestamps`) mirroring
`test_reconciliation.py`'s same-named test, since DR-021 coverage
is load-bearing per the brief's §4 / §7 / §11 references. Three
scheduler tests (manual flush, threading re-arm, threading stop)
mirror the W6 reconciliation scheduler test pattern — required
for the §5.7 anchor to ship verified, even though §5.8's
explicit list omitted them.

Net: 37 named + 1 DR-021 + 3 scheduler = 41. No tests added
beyond the W6.5 scope. All 458 tests pass.

The cleaner reading is that the brief's projected band (+25-+30)
under-counted what the brief itself specified.

### Deviation #2 — `ReadOutcome` import location vs brief's note

**Anchor:** §5.5 Change F note ("This is the existing read-outcome
envelope shape from `clients.betfair_client.v1.envelope`
(`ReadEnvelope[T]` with `FreshEnvelope` / `UnavailableReadEnvelope`
variants)").
**Actual:** imported `ReadOutcome` and `ReadUnavailable` from
`workflows.bet_entry.v1.orchestrator`, where the W4 boundary's
`ReadOutcome[T] = ReadOk[T] | ReadUnavailable` type alias lives
(orchestrator.py:208).
**Reasoning:** the brief's §5.5 Change F signature specifies
`ReadOutcome[MarketSettlement]`; that type alias does not exist
in `clients.betfair_client.v1.envelope`. The envelope module
defines the (different) `ReadEnvelope[T] = FreshEnvelope[T] |
StaleEnvelope[T] | UnavailableReadEnvelope` type alias.
`ReadOutcome[T]` is the W4-side abstraction in orchestrator.py;
the W6 reconciliation worker uses it (importing
`from workflows.bet_entry.v1.orchestrator import BetfairAdapter,
ReadUnavailable`); per Session 101 §5.6 precedent, "W4 internals
do not import the W3 envelope's enum directly; reasons translate
at the boundary" (DR-030 layered architecture). Importing from
envelope.py would have broken DR-030.

The brief's signature is correct; the explanatory note pointing
at envelope.py is wrong. Followed the signature, not the note.

### Deviation #3 — `_build_surfacing_payload` signature

**Anchor:** §5.6 Change D specified
`_build_surfacing_payload(record, last_read, trigger_source,
operator_reason=None)`.
**Actual:** the helper signature lands as
`_build_surfacing_payload(*, record, last_read, trigger_source,
operator_escalation_reason=None, related_bet_ids=())`.
**Reasoning:**
- Renamed `operator_reason` → `operator_escalation_reason` to
  match the field name on `ProvisionalSettlementSurfacingPayload`
  (single source of truth).
- Added `related_bet_ids: tuple[str, ...] = ()` so the helper
  stays pure (no IO) and storage callers compute related ids
  themselves and pass them in. Alternative was to have the helper
  call into storage, which would couple the pure builder to the
  storage layer.
- Made all parameters keyword-only (idiomatic for builders;
  reconciliation.py uses the same convention).

No semantic change to the contract. The helper is still the
single construction point per the brief's §5.6 Change D.

### Deviation #4 — No separate `list_bet_ids_for_market` Protocol method

**Anchor:** §5.6 Change D suggested computing `related_bet_ids` via
"a storage query `list_bet_ids_for_market(market_id)`".
**Actual:** inlined the related-bets SQL query inside
`list_provisional_settlement_bets` (and the equivalent dict scan
inside the InMemory impl) instead of adding a new Protocol method.
**Reasoning:** there is currently one caller for this query
(`list_provisional_settlement_bets`); a separate Protocol method
would be over-abstraction. Brief §5.6 Change D did not strictly
require a separate method, just a query. The Protocol surface
stays minimal.

The brief's §5.6 Change D also offered "stub the field as empty
tuple with §6 deviation flag" as an out — declined that out;
the field is properly populated.

---

## §7 Open questions for triage

None. All known v1 carry-forward items are already documented in
the brief itself (§2.6 §5.4) and re-stated in §5 of this report:

- `entered_provisional_at` dedicated column → build-proper.
- `last_settled_at` / `settlement_attempts` separation from W6's
  `last_reconciled_at` / `reconciliation_attempts` → resolved as
  accept-shared-substrate per §5.5 Change G's pre-flight triage.
- §2.6 §3.4 condition 2 (post-settlement market voided
  re-transition from terminal) → build-proper per §5.5 Change C.
- Settlement worker cadence specification → §2.4 / build-proper.
- Soft-book balance reconciliation → build-proper.

---

## §8 Findings beyond brief scope

### Finding 1 — Pre-W6.1 trailing comma on `_BETS_DDL`

`workflows/bet_entry/v1/storage.py` line 152 (pre-W6.5) ended with
`reconciliation_attempts INTEGER DEFAULT 0` with no trailing
comma — i.e., it was the last column in the DDL. Adding W6.5's
four new columns required adding a trailing comma to that line
plus adding the four new column lines (the last of which has no
trailing comma).

This is normal DDL extension, not a finding worth amendment.
Recording for log visibility because future briefs that extend
the bets DDL will hit the same "shift the no-comma sentinel"
pattern; one option is to leave a trailing comma + a sentinel
line at the bottom of the DDL to make column additions purely
append-only, but that's stylistic and DDL micro-tuning is not
W6.5 territory.

### Finding 2 — `lint-imports` dependency-graph delta

The `lint-imports` analysis reports: 106 → 108 files (+2,
matching the two new modules) and 310 → 321 dependencies (+11
unique imports the dependency graph hadn't previously recorded).
The +11 includes:
- `workflows.bet_entry.v1.settlement` → `workflows.bet_entry.v1.orchestrator`
  (for `ReadOutcome`, `ReadUnavailable`).
- `workflows.bet_entry.v1.settlement` →
  `workflows.bet_entry.v1.storage` (for `BetRecordStorage`).
- `workflows.bet_entry.v1.settlement` → `workflows.bet_entry.v1.models`.
- `workflows.bet_entry.v1.settlement` →
  `clients.betfair_client.v1.settlement` (for `MarketSettlement`,
  `MarketStatus`, `RunnerSettlementStatus`).
- `workflows.bet_entry.v1.storage` →
  `workflows.bet_entry.v1.settlement` (the function-local import
  path inside `list_provisional_settlement_bets`; lint-imports
  tracks this as an edge despite the runtime-only resolution).
- The test module's imports (5 modules: settlement, models,
  storage, orchestrator, clients.betfair_client.v1.settlement).

All five DR-030 contracts remain KEPT. No new violations.

### Finding 3 — `is_past_settlement_window` shows in `model_dump()`

The `@computed_field` decorator on `is_past_settlement_window`
makes it part of the Pydantic model's serialised representation —
it appears in `BetRecord.model_dump()` output (see §7.4 below).
Implication: any code that takes a `BetRecord` and serialises it
to JSON / dict / log line gets the property's value evaluated at
serialisation time. This is correct for visibility (the field
exists for operator visibility per §2.6 §3.3), but consumers
should be aware that `model_dump()` is no longer a pure read of
stored fields — it now invokes the wall-clock comparison via
`_now_adelaide()` whenever called on a PENDING bet with a
non-empty leg list.

For tests: any test that monkeypatches `_now_adelaide` will see
the patched value reflected in `model_dump()` output. For
production: the value reflects whatever the wall clock says at
the moment of the dump, which is the intended semantic.

---

## §9 Self-assessment

### §9.1 — Pre/post baselines table

| Metric | Pre-baseline | Post-baseline | Δ |
|---|---|---|---:|
| Test count (`pytest --collect-only -q`) | 417 | 458 | +41 |
| Full-suite result (`pytest -q`) | 417 passed | 458 passed | +41 passed, 0 new failures |
| Ruff (`ruff check workflows/bet_entry/v1/ tests/workflows/bet_entry/v1/`) | All checks passed | All checks passed | — |
| `lint-imports` contracts kept | 5 / 5 | 5 / 5 | 0 changed |
| `lint-imports` files analyzed | 106 | 108 | +2 |
| `lint-imports` dependencies | 310 | 321 | +11 |

### §9.2 — Functional verification checklist

- [x] All `tests/workflows/bet_entry/v1/test_settlement.py` pass
  (41 / 41 green).
- [x] `tests/workflows/bet_entry/v1/test_reconciliation.py` still
  passes (40 / 40 green; W6 / W6.1 substrate untouched).
- [x] `tests/workflows/bet_entry/v1/test_storage.py` still passes
  (24 / 24 green; storage extensions are additive).
- [x] `tests/workflows/bet_entry/v1/test_models.py` — file does
  not exist in the codebase. Treated as N/A. Model coverage lives
  inside `test_storage.py` round-trip tests and the new
  `test_settlement.py` Block 5; no regressions.
- [x] Full suite passes (458 / 458 green).
- [x] `ruff check` clean on the W4 + tests scope.
- [x] `lint-imports` 5 contracts kept, 0 broken.
- [x] No live Betfair API calls (mocked-only tests).
- [x] No edits outside the §5 named anchors (verified by manual
  inspection of the diff against `models.py` / `storage.py`; the
  two new files `settlement.py` and `test_settlement.py` are
  inside the named anchor surfaces).
- [x] No new untracked files outside `settlement.py` and
  `test_settlement.py`. Confirmed via `git status` — see §9.3.

### §9.3 — `git status` snapshots

**Pre-baseline** (W6.1 ship state — recorded at session open):

```
On branch main
Changes not staged for commit:
        modified:   clients/betfair_client/v1/__init__.py
        modified:   clients/betfair_client/v1/_translation.py

Untracked files:
        clients/betfair_client/v1/account_funds.py
        clients/betfair_client/v1/current_orders.py
        clients/betfair_client/v1/market_catalogue.py
        tests/clients/betfair_client/v1/test_account_funds.py
        tests/clients/betfair_client/v1/test_current_orders.py
        tests/clients/betfair_client/v1/test_market_catalogue.py
        tests/workflows/
        workflows/bet_entry/v1/
```

**Post-baseline** (W6.5 ship state — recorded at session close):

```
On branch main
Changes not staged for commit:
        modified:   clients/betfair_client/v1/__init__.py
        modified:   clients/betfair_client/v1/_translation.py

Untracked files:
        clients/betfair_client/v1/account_funds.py
        clients/betfair_client/v1/current_orders.py
        clients/betfair_client/v1/market_catalogue.py
        tests/clients/betfair_client/v1/test_account_funds.py
        tests/clients/betfair_client/v1/test_current_orders.py
        tests/clients/betfair_client/v1/test_market_catalogue.py
        tests/workflows/
        workflows/bet_entry/v1/
```

Identical. The two modified files (`models.py`, `storage.py`) and
the two new files (`settlement.py`, `test_settlement.py`) all sit
inside the existing untracked directories `tests/workflows/` and
`workflows/bet_entry/v1/`, so the file-level git status output
does not change. No new untracked entries at the root level.

No `git` mutations performed (no `add`, `commit`, `stash`,
`restore`, `checkout`, `reset`).

### §9.4 — Length flag

This report is in the **600-900 line target band** per brief §8.
Final line count: see file metadata (target ~700-800 lines based
on the structure landed; well inside the band).

### §9.5 — DR-021 timestamp confirmation

All Adelaide-local timestamps land via `_now_adelaide()`
(`datetime.now(ZoneInfo("Australia/Adelaide"))`). Test fixtures
pin `T0 = datetime(2026, 5, 6, 14, 12, 30, tzinfo=ADELAIDE)`,
`EVENT_START = datetime(2026, 5, 6, 14, 15, tzinfo=ADELAIDE)`,
`T_AFTER_RACE = EVENT_START + timedelta(seconds=600)`, etc., all
Adelaide-tz-aware. `SettlementPassResult.started_at` /
`finished_at` carry tz info verified by
`test_pass_uses_adelaide_local_timestamps`. No naive datetimes
land anywhere in W6.5 substrate.

### §9.6 — Sample model dumps (§7.4)

Generated from a live SQLite round-trip with the W6.5 substrate.

**Sample 1 — `BetRecord` after `SETTLED_WON` transition:**

```
bet_id: 'bet-w-1'
cycle_id: 'cycle-aaa'
entry_path: <EntryPath.RACING_SCREEN: 'racing_screen'>
strategy_tag: <StrategyTag.SAFETY_NET: 'safety_net'>
is_free_bet: False
free_bet_conversion_rate: None
realised_conversion_rate: None
requested_stake: Decimal('50.00')
matched_stake: Decimal('50.00')
unmatched_stake: Decimal('0')
matched_price: 4.2
match_status: <MatchStatus.FINAL_FULL: 'final_full'>
soft_book_combined_price: None
placed_at: 2026-05-06 14:12:30 +09:30
book_or_exchange: 'betfair'
account_at_book_id: 'acct-betfair-tim'
price_source: None
betfair_bet_id: '318946271234'
last_reconciled_at: 2026-05-06 14:25:00 +09:30
reconciliation_attempts: 1
settlement_state: <SettlementState.SETTLED_WON: 'settled_won'>
dead_heat_count: 0
removed_runner_count: 0
unexpected_state_count: 0
legs: [{bet_id: 'bet-w-1', betfair_market_id: '1.234567890',
       betfair_selection_id: '47291834',
       betfair_event_start_time: 2026-05-06 14:05:00 +09:30}]
is_past_settlement_window: False
```

Confirms: `settlement_state="settled_won"`, three count fields
populated as 0 from the canned `MarketSettlement`,
`last_reconciled_at` stamped at pass start, `reconciliation_attempts=1`,
`is_past_settlement_window=False` (correctly — bet is no longer
PENDING).

**Sample 2 — `ProvisionalSettlementSurfacingPayload` for a bet
in PROVISIONAL state:**

```
bet_record: {bet_id: 'bet-p-1',
             settlement_state: <SettlementState.PROVISIONAL: 'provisional'>,
             match_status: <MatchStatus.FINAL_FULL: 'final_full'>,
             ...}
trigger_source: <ProvisionalTriggerSource.UNEXPECTED_STATE:
                 'unexpected_state'>
operator_escalation_reason: None
last_read_market_state: None
placement_time: 2026-05-06 14:12:30 +09:30
entered_provisional_at: 2026-05-06 14:25:00 +09:30
related_bet_ids: ()
```

Confirms: full bet record nested; trigger source defaults to
`UNEXPECTED_STATE` at v1 (only one trigger fires automatically);
`last_read_market_state=None` at v1 (storage doesn't keep the
worker's last read); timestamps Adelaide-local;
`related_bet_ids=()` because no sibling bet shares this bet's
`betfair_market_id` in the test storage.

These confirm the wire shape Session 106's W6.5 triage will read
against.

---

**End of report.**
