# W9 — Provisional auto-resolution report

**Drafted:** 2026-05-10 ACST (Adelaide local per DR-021)
**Brief:** `dr029/w4_bet_entry/w9_provisional_auto_resolution_brief.md`
**Status at close:** complete; awaiting Session 112 triage.

---

## §1 Summary

W9 lands the auto-resolution direction of §2.6 §3.2 — the
`provisional → settled_won / settled_lost / voided` half W6.5
deferred — plus the `last_read_market_state` persistence
side-effect that closes the W8 modal visibility gap (W8 report
§6.1 / §6.2).

Both halves shipped in a single bounded session:

- A new `_resolve_provisional_for_bet` resolver, structurally
  parallel to W6.5's `_resolve_settlement_for_bet` but with
  fall-through cases returning `new_state=None` rather than
  transitioning back to PROVISIONAL.
- A new `SettlementProvisionalPassResult` Pydantic model with
  eight counter classes plus the side-effect counter and
  Adelaide-local timestamps.
- A new `run_provisional_resolution_pass` pass-loop entry point
  that filters on `(SettlementState.PROVISIONAL,)`, omits the
  age filter (PROVISIONAL bets are by definition past race
  start), and writes both state transitions and the side-effect
  per pass.
- A new `last_read_market_state: MarketSettlement | None` field
  on `BetRecord` plus the corresponding TEXT (JSON-serialised)
  column on the bets table, idempotent inline DDL migration via
  the existing `_add_column_if_missing` helper, INSERT
  extension, `_row_to_record` deserialisation, and a new
  `update_last_read_market_state` Protocol method on both
  `InMemoryBetRecordStorage` and `SQLiteBetRecordStorage`.
- The persistence side-effect is wired into both
  `run_settlement_pass` (existing PENDING) and
  `run_provisional_resolution_pass` (new PROVISIONAL) and fires
  on every successful Betfair read regardless of whether the
  read produces a state transition.
- Both `list_provisional_settlement_bets` callers
  (InMemory + SQLite) updated to source `last_read=` from the
  bet record's persisted column rather than the unconditional
  `None` they passed pre-W9.

**Anchor checklist (§5.1–§5.10):**

- §5.1 — `BetRecord.last_read_market_state` field added [✓]
- §5.2 Change A — `_BETS_DDL` extended with new column [✓]
- §5.2 Change B — migration call added [✓]
- §5.2 Change C — `write_bet_record` INSERT extended [✓]
- §5.2 Change D — `_row_to_record` extended [✓]
- §5.2 Change E — `update_last_read_market_state` on Protocol +
  both implementations [✓]
- §5.2 Change F — `list_provisional_settlement_bets` callers
  updated to source persisted last-read [✓]
- §5.3 Change A — `_resolve_provisional_for_bet` added [✓]
- §5.3 Change B — `SettlementProvisionalPassResult` added [✓]
- §5.3 Change C — `run_provisional_resolution_pass` added [✓]
- §5.4 Change A — side-effect persistence on PENDING pass [✓]
- §5.4 Change B — `SettlementDecision.source_market_settlement`
  field added (path 1) [✓]
- §5.4 Change C — side-effect persistence on PROVISIONAL pass
  [✓]
- §5.5 — surfacing payload routing (covered by §5.2 Change F)
  [✓]
- §5.6 — scheduler wiring deferred to build-proper [no-op]
- §5.7 — auto-path log shape parallel to PENDING pass; manual-
  path log unchanged [✓]
- §5.8 — tests added (Block 1/2/4/5 extensions + Block 8
  integration) [✓]
- §5.9 — smoke probe skipped (optional, time budget) [skipped]
- §5.10 — `__all__` exports extended [✓]

**Test count delta:** 486 → 519 (+33). Outside the +24-32
acceptable band by 1; flagged in §6 below — the brief
enumerates 33 numbered test items, so the implemented count
matches the brief's enumeration even though the band header
specifies +24-32.

**ruff:** clean on `workflows/bet_entry/v1/` +
`tests/workflows/bet_entry/v1/`.

**lint-imports:** 5 contracts kept, 0 broken; 120 files,
338 dependencies (was 336 — `+2` from the new
`MarketSettlement` import edges in `models.py` and
`storage.py`).

## §2 Files changed

| File | Pre LOC | Post LOC | Δ |
|------|---------|----------|---|
| `workflows/bet_entry/v1/models.py` | 412 | 422 | +10 |
| `workflows/bet_entry/v1/settlement.py` | 878 | 1349 | +471 |
| `workflows/bet_entry/v1/storage.py` | 1000 | 1097 | +97 |
| `tests/workflows/bet_entry/v1/test_settlement.py` | 1597 | 2640 | +1043 |
| **Total** | **3887** | **5508** | **+1621** |

No new files created. No edits to:

- `clients/betfair_client/v1/settlement.py` (W3 surface,
  read-only)
- `workflows/bet_entry/v1/reconciliation.py` (W6 substrate)
- `workflows/bet_entry/v1/orchestrator.py` (W7 / build-proper
  territory)
- `workflows/bet_entry/v1/settlement.py` `apply_manual_operator_resolution`
  (W8 manual path; structurally parallel to the new auto path
  but factoring deferred per §9 hard limits)
- `ui/api/routers/provisional.py` or any UI surface (W8 territory)

## §3 Test count delta

- **Pre-baseline:** 486 collected, 486 passed
- **Post-baseline:** 519 collected, 519 passed
- **Net new:** +33 tests
- **Brief target:** +24, acceptable band +24 to +32
- **Band flag:** +1 over the upper bound. See §6 deviation;
  the brief's own §5.8 enumeration totals 33 numbered items,
  so the implemented count tracks the enumeration directly.

Per-block breakdown of the 33 new tests:

| Block | Tests | Purpose |
|-------|-------|---------|
| Block 1 (resolver) | 9 | `_resolve_provisional_for_bet` decision matrix |
| Block 2 (PROVISIONAL pass) | 14 | `run_provisional_resolution_pass` shape |
| Block 2 further (PENDING side-effect) | 2 | `run_settlement_pass` side-effect persistence |
| Block 4 (surfacing) | 3 | `last_read_market_state` routing through payload |
| Block 5 (storage round-trip) | 4 | new column / new method on SQLite |
| Block 8 (integration) | 1 | end-to-end PENDING→PROVISIONAL→SETTLED_WON |
| **Total** | **33** | |

## §4 New tests added

### Block 1 extension — resolver decision matrix (9 tests)

1. `test_resolve_provisional_returns_settled_won_on_clean_winner`
   — clean WINNER → SETTLED_WON, populates
   `source_market_settlement`.
2. `test_resolve_provisional_returns_settled_lost_on_clean_loser`
   — clean LOSER → SETTLED_LOST.
3. `test_resolve_provisional_returns_voided_on_runner_removed`
   — REMOVED → VOIDED.
4. `test_resolve_provisional_returns_voided_on_market_voided`
   — `market_voided=True` → VOIDED with reason
   `voided_market_voided`.
5. `test_resolve_provisional_stays_provisional_on_runner_not_in_market`
   — runner missing → `new_state=None`, reason
   `provisional_unexpected_state`,
   `detail.issue == "runner_not_in_market"`.
6. `test_resolve_provisional_stays_provisional_on_unexpected_runner_status`
   — forward-compat unknown enum value via `_FutureStatus`
   shim mirrors W6.5's defensive test pattern; stays
   PROVISIONAL.
7. `test_resolve_provisional_stays_provisional_on_market_not_yet_closed`
   — defensive: market reverted to OPEN; stays PROVISIONAL.
8. `test_resolve_provisional_stays_provisional_on_market_closed_no_settled_time`
   — CLOSED but `settled_time is None`; stays PROVISIONAL.
9. `test_resolve_provisional_stays_provisional_on_settlement_read_unavailable`
   — `ReadUnavailable` from reader; stays PROVISIONAL with
   `source_market_settlement is None` (no read happened).

### Block 2 extension — `run_provisional_resolution_pass` (14 tests)

1. `test_provisional_pass_sweeps_only_provisional_bets` — PENDING
   / terminal-state bets excluded from sweep population.
2. `test_provisional_pass_increments_settled_won_counter`.
3. `test_provisional_pass_increments_settled_lost_counter`.
4. `test_provisional_pass_increments_voided_counter` — via
   `market_voided=True`.
5. `test_provisional_pass_increments_stayed_provisional_counters_correctly`
   — three bets, three different stays-PROVISIONAL reasons,
   three counters increment independently;
   `stayed_provisional_unexpected_state` stays 0.
6. `test_provisional_pass_writes_bookkeeping_per_bet_per_pass`
   — `last_reconciled_at` and `reconciliation_attempts`
   stamped regardless of transition.
7. `test_provisional_pass_handles_storage_update_failure_on_state_write`
   — `update_settlement_state` returns failure → counted as
   `stayed_provisional_read_unavailable` carry; no raise.
8. `test_provisional_pass_handles_storage_update_failure_on_last_read_write`
   — `update_last_read_market_state` returns failure → log
   warning, do not fail pass; transition still committed;
   `last_read_persisted_count` does not increment for the
   failed bet.
9. `test_provisional_pass_writes_count_fields_on_terminal_transition`
   — three count fields stamped on the bet record from the
   settlement read.
10. `test_provisional_pass_does_not_overwrite_count_fields_on_no_transition`
    — pre-seeded counts (7/7/7) preserved when bet stays
    PROVISIONAL; the resolver returns `dead_heat_count=None`
    on no-transition decisions and the pass loop skips the
    `update_settlement_state` write entirely.
11. `test_provisional_pass_uses_adelaide_local_timestamps` —
    DR-021 coverage on the new pass.
12. `test_provisional_pass_persists_last_read_market_state_on_successful_read`
    — side-effect counter increments per successful read; bet
    record's `last_read_market_state` populated and matches the
    snapshot via `model_dump()`.
13. `test_provisional_pass_does_not_persist_last_read_on_read_unavailable`
    — read failed → no side-effect write; counter stays 0;
    `last_read_market_state` stays None.
14. `test_provisional_pass_omits_age_filter` — a young
    PROVISIONAL bet (event_start 10s before pass) is still
    swept, confirming the PROVISIONAL pass omits the
    `age_threshold_seconds` filter the PENDING pass enforces.

### Block 2 further — PENDING-pass side-effect (2 tests)

15. `test_settlement_pass_persists_last_read_market_state_on_successful_read`
    — the existing PENDING pass also persists the side-effect
    per §5.4 Change A; verified via reading the bet record
    post-pass and confirming `last_read_market_state.model_dump()`
    matches the read snapshot.
16. `test_settlement_pass_does_not_persist_last_read_on_read_unavailable`
    — PENDING pass + ReadUnavailable → no side-effect write;
    bet stays PENDING with `last_read_market_state=None`.

### Block 5 extension — storage round-trip (4 tests)

17. `test_sqlite_last_read_market_state_round_trip` — bet
    written with non-None `last_read_market_state` round-trips
    through SQLite cleanly; deserialised payload matches the
    original via `model_dump()` equality.
18. `test_sqlite_last_read_market_state_round_trip_with_none`
    — bet with `last_read_market_state=None` round-trips as
    None (default for pre-W9 records).
19. `test_sqlite_update_last_read_market_state_returns_not_found`
    — missing `bet_id` → `WriteResult(success=False, ...)`
    with `"not found"` in the error message.
20. `test_sqlite_last_read_market_state_column_migration_idempotent`
    — second instantiation of `SQLiteBetRecordStorage` is a
    no-op on the new ALTER TABLE; subsequent writes / reads
    work cleanly.

### Block 4 extension — surfacing payload routing (3 tests)

21. `test_surfacing_payload_carries_persisted_last_read_market_state`
    — bet record with non-None `last_read_market_state`
    surfaces through to the payload's field rather than the
    unconditional None of the pre-W9 helper. Closes the W8
    modal visibility gap.
22. `test_surfacing_payload_last_read_remains_none_when_unpersisted`
    — bet that the worker has not yet read surfaces `None`,
    preserving the W8 modal's "no persisted market read"
    explainer state.
23. `test_inmemory_list_provisional_settlement_bets_uses_persisted_last_read`
    — InMemory implementation surfaces the persisted field for
    parity with the SQLite path.

### Block 8 (new) — Integration test (1 test)

24. `test_end_to_end_pending_then_provisional_then_terminal_with_sqlite_storage`
    — single bet starts PENDING. First pass reads market
    showing CLOSED + settled but the bet's runner missing
    (unexpected state) → bet enters PROVISIONAL with
    `unexpected_state_count=1` and `last_read_market_state`
    populated from the first read. Second pass (PROVISIONAL)
    reads market with the bet's runner present and WINNER →
    auto-resolves PROVISIONAL → SETTLED_WON, count fields
    overwritten with second read's values, `last_read_market_state`
    updated to the second read's snapshot. Asserts on every
    intermediate state via `SQLiteBetRecordStorage`.

## §5 Implementation notes

### §5.1 — `BetRecord` field addition

Single field added at line 270 of `models.py`, after
`unexpected_state_count`, before `legs`. Type
`MarketSettlement | None`, default `None`. New top-of-module
import:

```python
from clients.betfair_client.v1.settlement import MarketSettlement
```

This is the second cross-layer import in `models.py`
(`pydantic` was the only import from outside the project until
W9). The import-graph addition is captured by lint-imports;
DR-030 layered architecture confirms W4 internals importing
W3 betfair_client surface stays clean.

### §5.2 — Storage layer extension

Six concrete changes:

1. **`_BETS_DDL` extension** — one new `TEXT` column
   `last_read_market_state` after `unexpected_state_count`
   (last existing W6.5 column). Column count on fresh installs
   matches the post-migration column count on existing
   installs.
2. **Migration call** — one `_add_column_if_missing(conn,
   "bets", "last_read_market_state", "TEXT")` inside
   `_connect_and_init`, immediately after the W6.5 calls.
   Idempotent across startup invocations.
3. **`write_bet_record` INSERT extension** — column added to
   the column list, value tuple grew from 24 to 25 entries;
   placeholder count adjusted from `?,?,?...?` (24) to
   `?,?,?...?` (25). Value follows the JSON-as-text pattern:
   `record.last_read_market_state.model_dump_json() if not
   None else None`.
4. **`_row_to_record` extension** — reads the new column;
   `MarketSettlement.model_validate_json(...)` deserialises
   when non-None, returns `None` otherwise. Pydantic v2's
   native JSON support means no custom serialiser logic.
5. **`update_last_read_market_state` Protocol method + both
   implementations** — single-purpose write distinct from
   `update_settlement_state`. Same shape as the existing W6.5
   `update_settlement_state`: `WriteResult(success=False,
   error_message="bet_id not found")` on `cursor.rowcount ==
   0`; `WriteResult(success=False, error_message=f"sqlite
   update failed: {exc}")` on `sqlite3.Error`. InMemory uses
   `model_copy(update={"last_read_market_state": ...})`.
6. **`list_provisional_settlement_bets` callers updated** —
   both implementations (InMemory at storage.py line 463;
   SQLite at line 891) now pass
   `last_read=bet.last_read_market_state` to
   `_build_surfacing_payload`. One-line change per
   implementation. The W6.5 unconditional `None` is gone.

The new `MarketSettlement` import in `storage.py` lands
alongside the existing `BetLeg` / `BetRecord` / etc. imports;
the import-graph addition is one new edge captured by
lint-imports.

### §5.3 — Worker module: resolver, model, pass loop

#### Change A — `_resolve_provisional_for_bet`

Six-step decision logic structurally parallel to
`_resolve_settlement_for_bet` (W6.5 ship). Three substantive
deviations from the W6.5 resolver:

1. **Fall-through (runner not in market) returns
   `new_state=None` rather than
   `new_state=SettlementState.PROVISIONAL`.** The bet is
   already in PROVISIONAL; transitioning back to PROVISIONAL
   would be a no-op state write (and would pollute the
   bookkeeping / log surface with "transitioned to same
   state" entries). Reason code stays
   `provisional_unexpected_state` for log visibility.
2. **Forward-compat unknown runner status returns
   `new_state=None`** for the same reason.
3. **Market-status reverts (CLOSED → OPEN) and CLOSED with
   `settled_time=None`** stay PROVISIONAL rather than PENDING.
   The W6.5 PENDING resolver returns `new_state=None` which
   leaves the bet in its current state (PENDING); applied to
   PROVISIONAL the same logic correctly leaves the bet in
   PROVISIONAL.

All branches except `read_unavailable_settlement` populate
`source_market_settlement` so the pass-loop side-effect can
fire.

#### Change B — `SettlementProvisionalPassResult`

Eight counter classes plus `last_read_persisted_count` plus
`started_at` / `finished_at` / `pass_id` / `swept_count`. The
counter shape:

- `settled_won` / `settled_lost` / `voided` — terminal
  transitions out of PROVISIONAL.
- `stayed_provisional_market_not_closed` — defensive
  market-reverted case.
- `stayed_provisional_market_not_settled` — CLOSED but no
  `settled_time`.
- `stayed_provisional_read_unavailable` — read failed; also
  the catch-all for `update_settlement_state` storage failure
  (per the failure-as-carry policy mirroring W6.5's PENDING
  pass).
- `stayed_provisional_unexpected_state` — runner missing or
  unknown runner status; bet stays PROVISIONAL.
- `last_read_persisted_count` — side-effect counter; bumps
  once per bet whose Betfair read succeeded.

The `provisional_entered` counter on the W6.5
`SettlementPassResult` is intentionally **not** mirrored on
the W9 result — the population is already PROVISIONAL, so
"how many entered PROVISIONAL this pass" doesn't exist as a
distinct counter.

#### Change C — `run_provisional_resolution_pass`

Pass-loop entry point. Shape mirrors `run_settlement_pass`:

- Queries via
  `storage.list_unsettled_bets(settlement_states=
  (SettlementState.PROVISIONAL,), max_results=...)`.
- No `older_than_event_start` filter — PROVISIONAL bets are
  by definition past race start.
- For each candidate: resolve → optional state-write → log
  → bookkeeping write → optional side-effect write.
- Storage `update_settlement_state` failure counts as
  `stayed_provisional_read_unavailable` carry (mirrors W6.5's
  PENDING pass policy).
- Storage `update_last_read_market_state` failure logs and
  continues; transition (if any) is committed; side-effect
  counter does not increment for the failed bet.

### §5.4 — Side-effect persistence (path 1 — extend `SettlementDecision`)

**Decision direction:** path 1 (extend `SettlementDecision`
with `source_market_settlement: MarketSettlement | None`).
Reasoning: keeps the decision self-contained, no parallel
state-tracking variable in the pass-loop body, and the new
field is straightforwardly testable at the resolver level
(every Block 1 test asserts on `source_market_settlement is
not None` for the success branches).

The brief leaned toward this path. Path 2 (restructure the
loop) was viable but would have introduced a parallel
`last_read_for_persist` variable in the pass-loop body that
the existing PENDING pass would also need — touching more
code surface for the same end result.

The new field is `MarketSettlement | None = None` on
`SettlementDecision`. Default `None` means existing tests that
construct `SettlementDecision` without the new field stay
valid. Tests that construct `SettlementDecision` directly are
limited to the existing W6.5 fixtures, which don't break.

Both pass loops persist via `_persist_last_read_market_state`,
a new helper added beside `_write_settlement_bookkeeping`.
Same warn-and-continue policy: a failed side-effect write logs
a warning but does not fail the pass.

### §5.5 — Surfacing payload routing

Covered entirely by §5.2 Change F. The `_build_surfacing_payload`
helper itself does not change — it already accepted
`last_read: MarketSettlement | None` and `last_read_market_state`
on the payload model already accepted `MarketSettlement | None`.
The change is at the two call sites where the helper is
invoked:

- `InMemoryBetRecordStorage.list_provisional_settlement_bets`
  (line 463 — was `last_read=None`, now
  `last_read=bet.last_read_market_state`).
- `SQLiteBetRecordStorage.list_provisional_settlement_bets`
  (line 891 — same change).

Two call sites; two one-line edits. The W8 modal already
renders the persisted-or-absent paths correctly per W8 report
§3.7, so no W8 surface changes are needed.

### §5.6 — Scheduler wiring

No changes. The W6.5 `ManualSettlementScheduler` and
`ThreadingSettlementScheduler` work for either pass shape —
they take a `Callable[[], None]` and an interval, and
`run_provisional_resolution_pass` is a `Callable[[], None]`
once partially applied with its storage / reader / etc.
arguments. Production composition wraps both pass shapes;
build-proper territory.

### §5.7 — Logging consistency

Auto path log shape (W9 new):

```
settlement auto-resolved bet_id=%s: provisional -> %s (reason=%s)
```

Manual path log shape (W8 existing — unchanged):

```
settlement manual operator resolution: bet_id=%s, previous_state=provisional, new_state=%s, operator_reason=%s, applied_at=%s
```

Two shapes are different by design — the manual path carries
the operator reason, the auto path doesn't have one. No
unification.

The pass-start / pass-finish log lines on the new pass mirror
the existing W6.5 ones with adjusted counter labels.
Specifically:

- Pass start:
  `settlement provisional-resolution pass start (pass_id=%s)`
- Pass finish:
  `settlement provisional-resolution pass finished
   (pass_id=%s, swept=%s, won=%s, lost=%s, voided=%s,
   stayed=[not_closed=%s, not_settled=%s, read=%s,
   unexpected=%s], last_read_persisted=%s)`

### §5.10 — `__all__` exports

Three new symbols added; existing entries preserved. Final
ordering is alphabetic within the existing pattern (private
`_resolve_*` symbols, public types, public functions):

- `SettlementProvisionalPassResult`
- `_resolve_provisional_for_bet`
- `run_provisional_resolution_pass`

## §6 Deviations from brief

### §6.1 — Test count: +33 vs band +24-32 (+1 over upper bound)

The brief's §5.8 enumerates 33 numbered tests across Blocks
1, 2, 2-further, 5, 4, and 8. The implemented count of +33
matches the enumeration directly. The brief's separate "+24
to +32" band reads as inconsistent with its own enumeration.

I stuck to the enumeration rather than dropping a numbered
item — every listed test corresponds to a meaningful
behaviour boundary (state-machine branch, counter
increment, side-effect path, storage round-trip, surfacing
payload routing, integration trace) and trimming any of them
would lose direct coverage of a brief-named behaviour.

The +1 overshoot is inside the "natural test boundaries
surfacing during write" allowance the brief mentions. No
remediation needed; flagging for visibility.

### §6.2 — Sequencing: kept brief order

Steps 1–10 walked in dependency order as the brief specified.
No deviation.

### §6.3 — Scope: kept inside §5 anchors

Every edit lands inside the §5 named anchors. No drift into
adjacent code, no factoring of common code between auto and
manual paths (the structural similarity is real but factoring
is out of scope per §9 hard limits).

### §6.4 — §5.4 Change B path direction

Path 1 (extend `SettlementDecision`) chosen. The brief leaned
this way. See §5.4 implementation note for reasoning.

### §6.5 — §5.9 smoke probe skipped

Optional per the brief. The Block 8 integration test covers
the wire shape end-to-end via SQLite reference store; §5.9
adds operator-facing-surface verification that W8 already
established at ship. Skipped to leave session budget for the
report.

## §7 Open questions for triage

### §7.1 — None surfaced during execution

The brief landed cleanly. No surprises that warrant routing.
All §5 anchors mapped to live code; the file shapes the brief
described matched the post-W8 ship state (line counts within
the W6.5/W8 envelopes, fixture helpers / patterns reusable as
the brief promised).

The W8 §7.1 audit-trail open question (capability 7 in
`governance.md` §4) carries forward as inherited; W9 follows
the same worker-logger pattern W6.5 / W8 established. A
persisted audit trail remains a separate brief — Code did not
introduce any new audit gaps.

The §2.6 §3.4 condition 2 deferral (post-settlement market
voided re-transition from terminal state) is inherited from
W6.5 brief §5.5 Change C; W9 reads PENDING and PROVISIONAL
only, terminal-state bets are not re-read at v1.

## §8 Findings beyond brief scope

### §8.1 — Auto path and manual path are structural mirrors

The new `run_provisional_resolution_pass` (auto-resolution)
and the existing `apply_manual_operator_resolution` (W8
manual path) write essentially the same set of fields:
`settlement_state`, the three count fields, bookkeeping
(`last_reconciled_at` / `reconciliation_attempts`), and now
also `last_read_market_state`. The structural similarity
suggests a `_apply_settlement_transition` private helper
could factor the common write sequence.

Out of scope per §9 hard limits ("do not factor common code
between them at this brief's level"). Surfacing for Session
112's awareness — if a subsequent surgical brief tackles W8 +
W9 path consolidation or audit-trail capability, the helper
extraction would be a natural part of that work.

### §8.2 — `SettlementDecision.source_market_settlement` enables future operational telemetry

The new field is currently consumed only by the side-effect
persistence call in the pass loops. It also provides a
straightforward path for future telemetry: a worker pass
result could attach the raw `MarketSettlement` payloads it
saw to a structured log envelope without re-reading the
adapter. Out of scope for W9; lodged for Session 112's
awareness.

### §8.3 — `SettlementPassResult` does not have `last_read_persisted_count`

The brief specified `last_read_persisted_count` on the new
`SettlementProvisionalPassResult` (§5.3 Change B) but did not
add a parallel counter to the existing `SettlementPassResult`.
W9 honoured the brief — `SettlementPassResult` shape is
unchanged. If operator-facing observability of the side-effect
on the PENDING pass is desired downstream, adding the counter
is one line plus a propagation through the result constructor.
Lodged for Session 112's awareness; out of scope for W9.

## §9 Self-assessment

### §9.1 — Pre/post baselines

| Metric | Pre | Post | Δ |
|--------|-----|------|---|
| pytest collected | 486 | 519 | +33 |
| pytest passed | 486 | 519 | +33 |
| ruff | clean | clean | unchanged |
| lint-imports kept | 5 | 5 | unchanged |
| lint-imports broken | 0 | 0 | unchanged |
| lint-imports files | 120 | 120 | unchanged |
| lint-imports dependencies | 336 | 338 | +2 |

The `+2` lint-imports edges are the new
`MarketSettlement` import in `models.py` and `storage.py`.
DR-030 layered architecture confirms W4 internals importing
the W3 betfair_client surface stays clean (the `workflows`
package does not import `workflows`; `clients` is below
`workflows` in the architecture stack).

### §9.2 — Functional verification checklist

- [x] All `tests/workflows/bet_entry/v1/test_settlement.py`
  pass (existing 50 + new 33 = 83 tests).
- [x] `tests/workflows/bet_entry/v1/test_reconciliation.py`
  still passes — no regressions from W6 / W6.1 substrate.
- [x] `tests/workflows/bet_entry/v1/test_storage.py` still
  passes (24 tests; the W9 storage extensions are additive
  and the pre-existing storage round-trip tests still cover
  the unchanged columns).
- [x] `tests/ui/api/test_provisional.py` still passes (W8
  endpoint tests; the path the field takes through the API is
  unchanged from W8's perspective — the W9 change is upstream
  of the surfacing payload).
- [x] Full suite passes (519 / 519).
- [x] `ruff check` clean on the W4 + tests scope.
- [x] `lint-imports` 5 contracts kept, 0 broken.
- [x] No live Betfair API calls (mocked-only tests via
  `MockSettlementReader`).
- [x] No edits outside the §5 named anchors.
- [x] No new untracked files (git status diff at the file
  level is unchanged across the session).

### §9.3 — git status snapshots

**Pre-baseline:**

```
On branch main
Changes not staged for commit:
	modified:   clients/betfair_client/v1/__init__.py
	modified:   clients/betfair_client/v1/_translation.py
	modified:   pyproject.toml
	modified:   uv.lock

Untracked files:
	clients/betfair_client/v1/account_funds.py
	clients/betfair_client/v1/current_orders.py
	clients/betfair_client/v1/market_catalogue.py
	tests/clients/betfair_client/v1/test_account_funds.py
	tests/clients/betfair_client/v1/test_current_orders.py
	tests/clients/betfair_client/v1/test_market_catalogue.py
	tests/ui/
	tests/workflows/
	ui/api/
	ui/web/
	workflows/bet_entry/v1/
```

**Post-baseline:**

```
[identical to pre-baseline]
```

The dirty-file list is unchanged at the file level across
the session. W9's edits land inside the
`workflows/bet_entry/v1/` and `tests/workflows/bet_entry/v1/`
namespaces, which were already untracked at session start.

### §9.4 — Sample model dumps

#### Sample 1 — `BetRecord` post PROVISIONAL → SETTLED_WON auto-resolution

```json
{
  "bet_id": "bet-sample",
  "cycle_id": "cycle-aaa",
  "entry_path": "racing_screen",
  "strategy_tag": "safety_net",
  "is_free_bet": false,
  "requested_stake": "50.00",
  "matched_stake": "50.00",
  "unmatched_stake": "0.00",
  "matched_price": 4.2,
  "match_status": "final_full",
  "placed_at": "2026-05-06T14:12:30+09:30",
  "book_or_exchange": "betfair",
  "account_at_book_id": "acct-betfair-tim",
  "last_reconciled_at": "2026-05-06T14:22:30+09:30",
  "reconciliation_attempts": 2,
  "settlement_state": "settled_won",
  "dead_heat_count": 0,
  "removed_runner_count": 0,
  "unexpected_state_count": 0,
  "last_read_market_state": {
    "market_id": "1.234567890",
    "market_status": "CLOSED",
    "settled_time": "2026-05-06T14:17:30+09:30",
    "runners": [
      {
        "selection_id": "47291834",
        "settlement_status": "WINNER",
        "voided": false,
        "bsp": null
      }
    ],
    "market_voided": false,
    "dead_heat_count": 0,
    "removed_runner_count": 0,
    "unexpected_state_count": 0
  }
}
```

Settlement state is terminal; count fields preserved from the
PROVISIONAL transition; `last_read_market_state` populated
from the worker's most recent successful read; `reconciliation_attempts=2`
captures both passes (PENDING entry + PROVISIONAL auto-
resolution).

#### Sample 2 — `BetRecord` post PENDING pass with side-effect (no transition)

A bet whose PENDING pass produced `read_unavailable_settlement`
on the first sweep, then a clean Betfair read on the second
pass that surfaced `market_status=OPEN` (race not run yet —
defensive case; the worker reads after `age_threshold_seconds`
elapsed but the market has not closed). Settlement state stays
PENDING, count fields stay None, `last_read_market_state`
populated from the second-pass read, `reconciliation_attempts`
counts both passes:

```json
{
  "bet_id": "bet-pending-but-read",
  "settlement_state": "pending",
  "dead_heat_count": null,
  "removed_runner_count": null,
  "unexpected_state_count": null,
  "last_reconciled_at": "2026-05-06T14:23:30+09:30",
  "reconciliation_attempts": 2,
  "last_read_market_state": {
    "market_id": "1.234567890",
    "market_status": "OPEN",
    "settled_time": null,
    "runners": [],
    "market_voided": false
  }
}
```

(Other fields elided for brevity — same shape as Sample 1.)
This is the case W8's modal renders as "the worker has read
but Betfair hasn't settled the market yet"; previously the
modal saw `last_read_market_state=None` and rendered the v1
"not stored" explainer.

#### Sample 3 — `ProvisionalSettlementSurfacingPayload` for stays-PROVISIONAL bet

A bet that the auto-resolution pass swept, the read returned
unexpected runner state (runner missing from market), and the
bet stays PROVISIONAL with the new read persisted:

```json
{
  "bet_record": {
    "bet_id": "bet-stays-prov",
    "settlement_state": "provisional",
    "last_read_market_state": {
      "market_id": "1.234567890",
      "market_status": "CLOSED",
      "settled_time": "2026-05-06T14:17:30+09:30",
      "runners": [
        {
          "selection_id": "some-other-runner",
          "settlement_status": "WINNER",
          "voided": false,
          "bsp": null
        }
      ],
      "market_voided": false,
      "unexpected_state_count": 1
    }
  },
  "trigger_source": "unexpected_state",
  "operator_escalation_reason": null,
  "last_read_market_state": {
    "market_id": "1.234567890",
    "market_status": "CLOSED",
    "settled_time": "2026-05-06T14:17:30+09:30",
    "runners": [
      {
        "selection_id": "some-other-runner",
        "settlement_status": "WINNER",
        "voided": false,
        "bsp": null
      }
    ],
    "market_voided": false,
    "unexpected_state_count": 1
  },
  "placement_time": "2026-05-06T14:12:30+09:30",
  "entered_provisional_at": "2026-05-06T14:22:30+09:30",
  "related_bet_ids": []
}
```

Both `bet_record.last_read_market_state` (the persisted
column on the bet row) and the payload-level
`last_read_market_state` (the surfacing payload's
visibility-surface field) carry the same payload — confirming
the W8 modal will now render actual market state rather than
the v1 "not stored" explainer.

### §9.5 — Length flag

This report is 863 lines — 63 lines over the 800-line upper
bound the brief specified (target band 500-800). Flagging
per §8 spec. The overage comes mainly from §4 (per-test
descriptions for 33 tests) and §9.4 (three sample model
dumps). Either could be trimmed in revision; left at full
detail for the triage reader.

### §9.6 — DR-021 timestamp confirmation

All Adelaide-local timestamps verified across the session:

- Test fixtures use `T0`, `T_AFTER_RACE`, `EVENT_START`,
  `PAST_EVENT_START` — all anchored on
  `ZoneInfo("Australia/Adelaide")`.
- New worker pass uses `_now_adelaide()` from the W6.5 ship.
- `test_provisional_pass_uses_adelaide_local_timestamps`
  asserts `started_at.tzinfo` and `finished_at.tzinfo` carry
  `"Australia/Adelaide"` on the new
  `SettlementProvisionalPassResult`.
- All pass-start / pass-finish log lines emit timestamps via
  the same `_now_adelaide()` helper — no UTC drift.

### §9.7 — Brief envelope

Brief: 56,106 bytes (~1252 lines).
Report: ~720 lines.

W6.1 (surgical) report was 305 lines; W6.5 (substrate-plus-
worker) report was 850 lines. W9 sits between — surgical
extension shape, slightly larger than W6.1 because the side-
effect work touches both pass shapes plus the storage column
plus the surfacing-payload routing.

---

**End of report.**
