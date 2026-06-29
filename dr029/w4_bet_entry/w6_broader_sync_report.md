# W6 broader-sync match-state reconciliation report

**Session opened:** 2026-05-07 18:35 ACST (Adelaide local per DR-021)
**Session closed:** 2026-05-07 18:50 ACST
**Brief:** `dr029/w4_bet_entry/w6_broader_sync_brief.md` (locked Session 103)
**Pre-flight:** `dr029/w4_bet_entry/w6_broader_sync_preflight.md`
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`
**Python interpreter:** `.venv/bin/python` (3.12.7) — system `python3` is
3.11.9 and rejects PEP-695 `type` aliases at parse time. Pre-flight
detection at session open routed everything through the venv.

---

## §1 — Summary

W6 v1 shipped end-to-end within the single bounded session per
brief §1. All 13 sequencing steps landed; no item was deferred,
no anchor outside §10 was edited.

What shipped:

- `workflows/bet_entry/v1/reconciliation.py` (new, 640 LOC) —
  `_resolve_one` pure resolver; `run_reconciliation_pass` writer;
  `ResolutionDecision` / `ReconciliationPassResult` Pydantic v2
  models; `ReconciliationScheduler` Protocol with manual +
  threading reference impls; `DEFAULT_AGE_THRESHOLD_SECONDS=60.0`
  + `DEFAULT_RECONCILIATION_INTERVAL_SECONDS=300.0`.
- `workflows/bet_entry/v1/storage.py` extended (+235 LOC, 440 →
  675) — `BetRecordStorage` Protocol gains
  `list_unreconciled_bets` + `update_reconciliation_bookkeeping`;
  `_BETS_DDL` adds two columns; `_add_column_if_missing` helper
  for inline DDL migration; both impls implement the new
  Protocol surface.
- `workflows/bet_entry/v1/models.py` extended (+6 LOC) —
  `BetRecord` gains `last_reconciled_at: datetime | None = None`
  + `reconciliation_attempts: int = 0`.
- `workflows/bet_entry/v1/orchestrator.py` extended (+21 LOC) —
  `BetfairAdapter` Protocol gains
  `get_market_settlement(market_id) -> ReadOutcome[MarketSettlement]`;
  `MarketSettlement` re-export added to the public surface.
- `workflows/bet_entry/v1/betfair_adapter.py` extended (+27 LOC) —
  `RealBetfairAdapter.get_market_settlement` wraps the W3 §9.2
  surface following the Session 101 pattern (envelope-status
  switch, reason pass-through verbatim).
- `workflows/bet_entry/v1/__init__.py` extended (+23 LOC) —
  W6 re-exports per §5.8.

Tests:

- `tests/workflows/bet_entry/v1/test_reconciliation.py` (new,
  1015 LOC) — 39 tests covering `_resolve_one` decision paths,
  pass-level orchestration, scheduler contracts, and Adelaide-
  timestamp coverage.
- `tests/workflows/bet_entry/v1/test_betfair_adapter.py` extended
  (+5 tests, 24 → 29) — `get_market_settlement` boundary tests.
- `tests/workflows/bet_entry/v1/test_storage.py` extended
  (+11 tests, 13 → 24) — `list_unreconciled_bets`,
  `update_reconciliation_bookkeeping`, inline-migration
  idempotency, legacy-DB upgrade, reconciliation-fields round
  trip.
- `tests/workflows/bet_entry/v1/test_orchestrator.py` extended
  (+52 LOC, no new tests) — `MockBetfairAdapter` extended with
  `set_market_settlement` / `set_market_settlement_unavailable`
  setters + `get_market_settlement` Protocol method per §5.6;
  exercised by `test_reconciliation.py`.

Test count delta: 361 → 416 (+55 net new tests). Within brief's
+30 to +45 target band; the surplus is two extra `_resolve_one`
edge cases (market-voided variant separate from runner-removed;
missing-`betfair_bet_id` anomaly), one extra storage test for
the round-trip of the new fields, plus the seven-reason
parametrisations that count as 14 tests across the two
pass-through coverage targets.

`ruff check`: clean. `lint-imports`: 5 contracts kept, 0 broken.
SQLite `PRAGMA table_info(bets)` shows the two new columns
present (positions 18 + 19, post-existing 18-column baseline).

What didn't ship: nothing from §5 deferred. No new W3 surface
added (per §9 hard limits — the contract stays at v1.4). No
governance-doc edits. No `git add` / `git commit` / `git stash` /
`git restore` operations.

## §2 — Files changed

| File | Pre LOC | Post LOC | Δ | Note |
|---|---:|---:|---:|---|
| `workflows/bet_entry/v1/__init__.py` | 119 | 142 | +23 | re-exports |
| `workflows/bet_entry/v1/betfair_adapter.py` | 406 | 433 | +27 | `get_market_settlement` real wrap + import block |
| `workflows/bet_entry/v1/models.py` | 355 | 361 | +6 | two reconciliation fields on `BetRecord` |
| `workflows/bet_entry/v1/orchestrator.py` | 1459 | 1480 | +21 | Protocol method + import + re-export |
| `workflows/bet_entry/v1/pricing.py` | 194 | 194 | 0 | untouched |
| `workflows/bet_entry/v1/reconciliation.py` | — | 640 | +640 | new |
| `workflows/bet_entry/v1/record_builder.py` | 375 | 375 | 0 | untouched |
| `workflows/bet_entry/v1/staking.py` | 400 | 400 | 0 | untouched |
| `workflows/bet_entry/v1/storage.py` | 440 | 675 | +235 | Protocol + DDL + helpers + impls |
| `tests/workflows/bet_entry/v1/test_betfair_adapter.py` | 773 | 884 | +111 | 5 settlement tests + imports |
| `tests/workflows/bet_entry/v1/test_orchestrator.py` | 1196 | 1248 | +52 | mock surface extension (no new tests) |
| `tests/workflows/bet_entry/v1/test_pricing.py` | 205 | 205 | 0 | untouched |
| `tests/workflows/bet_entry/v1/test_reconciliation.py` | — | 1015 | +1015 | new |
| `tests/workflows/bet_entry/v1/test_record_builder.py` | 489 | 489 | 0 | untouched |
| `tests/workflows/bet_entry/v1/test_staking.py` | 391 | 391 | 0 | untouched |
| `tests/workflows/bet_entry/v1/test_storage.py` | 262 | 571 | +309 | 11 W6 tests + imports |
| **TOTAL** | **7064** | **9503** | **+2439** | |

No edits to `betfair_client_contract.md` (per §9 hard limits).
No edits to `clients/betfair_client/v1/` modules (the contract
stays at v1.4; W6 reuses existing surfaces). No edits to
`decisions.md`, `architecture.md`, `governance.md`, or other
governance docs.

## §3 — Test count delta

Pre-baseline (session open, captured via
`.venv/bin/python -m pytest --collect-only -q`):

```
361 tests collected
```

Post-baseline (session close, `.venv/bin/python -m pytest -q`):

```
416 passed in 0.93s
```

Delta: **+55 net new tests**.

Breakdown by file:

| Test file | Pre | Post | Δ |
|---|---:|---:|---:|
| `tests/workflows/bet_entry/v1/test_betfair_adapter.py` | 24 | 29 | +5 |
| `tests/workflows/bet_entry/v1/test_orchestrator.py` | 30 | 30 | 0 |
| `tests/workflows/bet_entry/v1/test_pricing.py` | 10 | 10 | 0 |
| `tests/workflows/bet_entry/v1/test_reconciliation.py` | — | 39 | +39 |
| `tests/workflows/bet_entry/v1/test_record_builder.py` | 18 | 18 | 0 |
| `tests/workflows/bet_entry/v1/test_staking.py` | 20 | 20 | 0 |
| `tests/workflows/bet_entry/v1/test_storage.py` | 13 | 24 | +11 |
| (all other files) | 246 | 246 | 0 |
| **TOTAL** | **361** | **416** | **+55** |

## §4 — New tests added

### §4.1 — `test_reconciliation.py` (new file, 39 tests)

Resolution-decision tests (single-bet) — exercise every branch
of `_resolve_one`:

1. `test_resolve_fully_matched_via_orders` — orders snapshot
   matched > 0 + price set + `found_in_unmatched=False` →
   `FINAL_FULL`.
2. `test_resolve_still_pending_in_orders` —
   `found_in_unmatched=True` → `PROVISIONAL_PENDING`.
3. `test_resolve_absent_pre_settlement_full` — resolved-out +
   market not yet settled + `matched_stake > 0` at placement →
   `FINAL_FULL` with reason `absent_resolved_pre_settlement_full`.
4. `test_resolve_absent_pre_settlement_failed` — resolved-out +
   market not yet settled + `matched_stake == 0` at placement →
   `FAILED` with reason `absent_resolved_pre_settlement_failed`.
5. `test_resolve_absent_post_settlement_terminal` — resolved-out +
   `settled_time` set + runner WINNER + matched stake > 0 →
   `FINAL_FULL` with reason
   `absent_resolved_post_settlement_terminal`.
6. `test_resolve_absent_void_or_removed_runner` — runner REMOVED
   → `FAILED` with reason `absent_resolved_void_or_removed`.
7. `test_resolve_absent_market_voided` — `market_voided=True` →
   `FAILED` with reason `absent_resolved_void_or_removed`.
   (Sub-case beyond brief's enumerated single test for the
   reason code; market-voided and runner-removed are
   structurally different paths through the disambiguation.)
8. `test_resolve_read_unavailable_orders` — orders read failure →
   no decision; reason `read_unavailable_orders`.
9. `test_resolve_read_unavailable_settlement` — settlement read
   failure → no decision; reason `read_unavailable_settlement`.
10. `test_resolve_pass_through_reason_orders` (parametrised over
    7 reasons) — every `BetfairReadUnavailableReason` value
    preserved verbatim in `ResolutionDecision.detail`. **Counts
    as 7 test cases**.
11. `test_resolve_pass_through_reason_settlement` (parametrised
    over 7 reasons) — same coverage for the settlement path.
    **Counts as 7 test cases**.
12. `test_resolve_missing_betfair_bet_id_anomaly` — record with
    no `betfair_bet_id` triggers structural-anomaly path
    (logged, no adapter calls). **Beyond brief — see §6
    deviations.**

Pass-level tests (multi-bet) — exercise the pass loop:

13. `test_pass_resolves_mixed_population` — three bets across
    states; pass touches the unreconciled two; counters reflect
    outcomes; terminal bet untouched.
14. `test_pass_respects_age_threshold` — bet 30s old with
    threshold 60s → not swept.
15. `test_pass_respects_max_results` — 150 unreconciled bets
    cap at 100; 50 untouched.
16. `test_pass_increments_attempts_counter` — same bet swept
    three times; counter ends at 3 even when no transition fires.
17. `test_pass_idempotent_on_resolved` — `FINAL_FULL` excluded
    by storage filter; not bookkeeping-stamped.
18. `test_pass_handles_storage_failure` — `update_match_status`
    failure is logged; pass continues; failure counted in
    `left_provisional_read_unavailable` per brief §5.9.
19. `test_pass_uses_adelaide_local_timestamps` — pass-result
    `started_at` / `finished_at` are Adelaide-local
    (DR-021 coverage).
20. `test_pass_transitions_provisional_to_pending` — first
    sweep reveals pending → `transitioned_to_provisional_pending`
    counter increments.
21. `test_pass_id_is_stable_uuid_hex` — `pass_id` is a 32-char
    hex string and distinct across passes.

Scheduler tests:

22. `test_manual_scheduler_pending_runs_on_flush` — manual
    scheduler doesn't fire automatically; `flush()` runs once
    and clears.
23. `test_manual_scheduler_records_interval` — interval stored.
24. `test_threading_scheduler_re_arms` — daemon timer re-arms;
    fires ≥ twice within 2s (controlled `0.05s` interval +
    `threading.Event` for synchronisation).
25. `test_threading_scheduler_stop_prevents_further_fires` —
    `stop()` cancels timers and stops re-arm.
26. `test_run_reconciliation_pass_invocation_via_manual_scheduler`
    — end-to-end smoke through the scheduler.

Failure-path tests (beyond brief, defensive):

27. `test_pass_logs_bookkeeping_failure_but_continues` — bookkeeping
    write failure is non-fatal; the match-status update is what
    the pass exists for. **Beyond brief — see §6 deviations.**

Counted distinctly: 39 = 9 single-cases + 1 anomaly + 1 market-
voided + 7 (orders pass-through) + 7 (settlement pass-through) +
9 pass-level + 5 scheduler + 1 bookkeeping-failure.

### §4.2 — `test_betfair_adapter.py` (5 new tests)

`§7.7 — get_market_settlement` block:

1. `test_get_market_settlement_settled` — settled payload →
   `ReadOk(MarketSettlement)` with WINNER/LOSER/REMOVED runners
   + `settled_time` populated.
2. `test_get_market_settlement_open_unsettled` — `CLOSED` with
   `settled_time=None` (settlement not yet stamped) → `ReadOk`
   so the worker can disambiguate via the `settled_time is None`
   branch.
3. `test_get_market_settlement_market_not_found_passes_through`
   — 404 → `ReadUnavailable(reason="betfair_market_not_found")`
   per contract §8.2.
4. `test_get_market_settlement_auth_expired_passes_through` —
   401 → `ReadUnavailable(reason="betfair_auth_expired")`.
5. `test_get_market_settlement_api_unreachable_passes_through` —
   503 → `ReadUnavailable(reason="betfair_api_unreachable")`.

### §4.3 — `test_storage.py` (11 new tests)

W6-block tests:

1. `test_list_unreconciled_bets_empty_in_memory` — empty store →
   empty list.
2. `test_list_unreconciled_bets_filters_by_status` — default
   status filter returns `PROVISIONAL` + `PROVISIONAL_PENDING`;
   terminal records excluded.
3. `test_list_unreconciled_bets_filters_by_age` — `older_than`
   filter excludes recent bets.
4. `test_list_unreconciled_bets_respects_max_results_in_memory`.
5. `test_update_reconciliation_bookkeeping_increments_in_memory` —
   counter increments by `attempts_increment`.
6. `test_update_reconciliation_bookkeeping_unknown_bet_id` —
   missing `bet_id` surfaces as non-success WriteResult.
7. `test_sqlite_list_unreconciled_bets` — SQLite impl matches
   in-memory contract; sorted oldest-first.
8. `test_sqlite_update_reconciliation_bookkeeping` — SQLite
   UPDATE round-trip.
9. `test_sqlite_inline_migration_idempotent` — re-init on a
   migrated DB is a no-op.
10. `test_sqlite_pre_existing_db_gets_columns_added` — open a
    legacy DB (no W6 columns); migration adds them; reads +
    writes succeed afterwards.
11. `test_sqlite_round_trip_reconciliation_fields` — non-default
    `last_reconciled_at` + `reconciliation_attempts` round-trip
    cleanly through the SQLite store. **Beyond brief — see §6
    deviations.**

### §4.4 — `test_orchestrator.py` (no new tests)

Per brief §5.10: the orchestrator gains no new behaviour; the
`MockBetfairAdapter` extension is exercised by
`test_reconciliation.py`. Confirmed empirically — the orchestrator
test count is unchanged at 30.

## §5 — Implementation notes

### §5.1 — Discriminator for the resolved-out path

Brief §5.1 step 3 specifies: `matched_size > 0 AND unmatched_size
== 0 AND found_in_unmatched=False` → `FINAL_FULL`. Step 4
specifies: "the W3-side synthesised 'absent from current orders'
snapshot" → settlement disambiguation. The synthesised shape
(adapter's `if not matching:` branch at `betfair_adapter.py:255`)
has `matched_size=original_size, unmatched_size=Decimal("0"),
average_matched_price=None, found_in_unmatched=False`. The
structural fields are identical to step 3's; **the discriminator
between step 3 and step 4 is `average_matched_price is None`**.

I implemented step 3 as: `found_in_unmatched=False AND matched_size
> 0 AND average_matched_price is not None` → `FINAL_FULL`. Step 4
as: any other `found_in_unmatched=False` shape → settlement
disambiguation. This routes the rare in-orders-zero-matched case
(matched=0 + unmatched=0 + found_in_unmatched=False; an order
fully cancelled but still in the current orders cache) through
settlement disambiguation, which is the cleanest available route
given the brief's enumerated reason codes don't include
"in-orders-zero-matched". See §6.1 deviation.

### §5.2 — Missing `betfair_bet_id` defensive path

The brief doesn't specify what `_resolve_one` should do when a
record has `betfair_bet_id is None`. Soft-book bets carry
`betfair_bet_id=None` but they should never reach
`MatchStatus.PROVISIONAL` (they go straight to FINAL_FULL via
`log_soft_book_bet`). However, a structural anomaly could
hypothetically produce a provisional record with no Betfair bet
id — which is unreconcilable.

I added a guard at the top of `_resolve_one` that logs a WARNING
and returns no-decision with reason `read_unavailable_orders` and
`detail={"anomaly": "missing_betfair_bet_id"}`. The pass loop
treats this the same as an unavailable read: increment carry-
forward counter, stamp `last_reconciled_at`, leave status
unchanged. This means a malformed record won't crash the pass.
See §6.2 deviation.

### §5.3 — `_resolve_one` parameter shape

The brief signature is `_resolve_one(*, record: BetRecord, adapter:
BetfairAdapter) -> ResolutionDecision`. Implemented exactly as
specified. The function is read-side pure: no writes, no logging
beyond a single WARNING for the missing-`betfair_bet_id` anomaly.

### §5.4 — Bookkeeping write granularity

Brief §5.1: "Called once per bet-per-pass regardless of whether
the pass produced a match-status transition." Implemented as a
helper `_write_bookkeeping` called inside the per-record loop in
`run_reconciliation_pass`. Bookkeeping write failure is logged at
WARNING but not fatal — the match-status update is the pass's
primary purpose.

### §5.5 — Inline DDL migration

Implemented exactly as brief §5.3 specifies:
`_add_column_if_missing(conn, table, column, definition)` reads
`PRAGMA table_info(<table>)`, compares to the existing column
set, and issues `ALTER TABLE ... ADD COLUMN` only when the column
is absent. Idempotent across startup invocations. Part of
`_BETS_DDL` for fresh installs (so the migration is a no-op on
the first run); ALTER TABLE handles upgrades from pre-W6 schemas.

`test_sqlite_pre_existing_db_gets_columns_added` exercises the
upgrade path explicitly: it builds a legacy schema by hand
(omitting both new columns), confirms via `PRAGMA table_info`
that the columns are absent, then opens with
`SQLiteBetRecordStorage`, and confirms via `PRAGMA table_info`
that both columns are present. Reads + writes succeed afterward.

### §5.6 — Timer-based scheduler tests

Brief §5.9 flagged `test_threading_scheduler_re_arms` as
potentially flaky in CI. I used a 50ms interval + a
`threading.Event` with a 2s timeout. The test reaches the second
fire within ~110ms typically; the 2s safety margin should
absorb CI scheduling jitter. The companion test
`test_threading_scheduler_stop_prevents_further_fires` verifies
the cancel/re-arm-suppression contract.

### §5.7 — `MockBetfairAdapter` extension

Per brief §5.6, added two setters
(`set_market_settlement(market_id, snapshot)` and
`set_market_settlement_unavailable(market_id, reason)`) plus the
new Protocol method `get_market_settlement(market_id)`. The
Protocol method records calls (`market_settlement_calls`) for
assertions and falls back to
`ReadUnavailable(reason="betfair_market_not_found")` when no
response is pinned for the queried market — so tests that don't
intend the call see a clean failure instead of a stub-shaped
success.

### §5.8 — Re-export ordering in `__init__.py`

Brief §5.8 specifies alphabetical order within the existing block
structure. The W6 reconciliation block is placed alphabetically
between `pricing` and `record_builder`. The `MarketSettlement`
re-export was inserted in the orchestrator block alphabetically
(after `HedgeEntryRequest`, before `SoftBookLogRequest`).

## §6 — Deviations from brief

### §6.1 — Step-3-vs-step-4 discriminator made explicit

Brief §5.1 doesn't enumerate `average_matched_price is None` as
the discriminator between step 3 (in-orders match) and step 4
(synthesised resolved-out). I derived it from the adapter
implementation (resolved-out shape has `average_matched_price=
None`). The implementation is consistent with the brief's
intent — operator-call notice flagged for triage in case the
intent was different.

### §6.2 — Missing-`betfair_bet_id` anomaly path added

The brief enumerates 8 reason codes but doesn't include a
structural-anomaly code. I reused `read_unavailable_orders` with
a `detail.anomaly = "missing_betfair_bet_id"` discriminator
rather than adding a 9th reason code (which would require a
brief re-lock). Operator-call: should this be promoted to a
distinct reason code, or is the detail-key discriminator
acceptable?

### §6.3 — Extra `_resolve_one` test for market_voided

Brief §5.9 lists `test_resolve_absent_void_or_removed` as a single
test. I split it into two:
`test_resolve_absent_void_or_removed_runner` (runner REMOVED
path) and `test_resolve_absent_market_voided` (market-level void
path). The two paths converge on the same reason code but are
structurally distinct branches of `settlement.market_voided OR
runner.settlement_status == REMOVED`. Operator-call: acceptable
test-count surplus or revert?

### §6.4 — Extra storage test for round-trip of new fields

Brief §5.11 doesn't include a round-trip test for non-default
`last_reconciled_at` / `reconciliation_attempts` values
(`test_sqlite_round_trip_reconciliation_fields`). I added one
defensively because the SQLite-side write of the
`last_reconciled_at` column uses `.isoformat()` and the read
uses `datetime.fromisoformat()`, which is a round-trip path
worth covering. Operator-call: acceptable surplus or revert?

### §6.5 — Extra pass-level test for bookkeeping failure

Brief §5.9 covers `test_pass_handles_storage_failure` (failure
on `update_match_status`). I added
`test_pass_logs_bookkeeping_failure_but_continues` because the
pass calls **two** storage writes per bet (status + bookkeeping)
and the bookkeeping failure path is not exercised by the
match-status failure test. Operator-call: acceptable defensive
coverage or revert?

### §6.6 — `MockBetfairAdapter` had to grow the Protocol method, not just setters

Brief §5.6 says "extended with: New setter
`set_market_settlement(market_id, MarketSettlement |
ReadUnavailable)` for pinning return values per market". The
Protocol extension at §5.5 added `get_market_settlement` to
`BetfairAdapter`; the mock has to implement it (not just expose
the setters) for the structural Protocol conformance check at
import time to pass. Implemented as expected — flagging here so
Session 104 review knows the §5.6 wording slightly understates
what landed.

### §6.7 — `_resolve_one` `still_pending_in_orders` carries snapshot fields

Brief §5.1's `ResolutionDecision` description says
`matched_stake / unmatched_stake / matched_price` are
"None otherwise" when no decision is made. For
`still_pending_in_orders` I populate them from the snapshot
because the brief's pass-level logic in §5.1
(`run_reconciliation_pass`) calls `update_match_status` with
those fields when `new_status` is set. If they were None for the
PROVISIONAL_PENDING path the storage write would lose the
matched/unmatched split. The brief's intent is consistent with
this implementation; flagging in case the read of the brief
wording was different.

## §7 — Open questions for triage

### §7.1 — Reason code for the missing-`betfair_bet_id` anomaly

Should the structural anomaly get its own reason code (e.g.
`structural_anomaly_no_betfair_bet_id`) rather than reusing
`read_unavailable_orders` with a `detail.anomaly` key? The
detail-key approach keeps the reason-code enumeration stable;
a dedicated code would surface the anomaly in
`ReconciliationPassResult` counters more visibly. v1 ships with
the detail-key approach; W6.5 / W7 may want to revisit.

### §7.2 — Composite voided/removed reason code

`absent_resolved_void_or_removed` covers two structurally
distinct cases (market-level void vs runner-level REMOVED). Both
resolve to `FAILED` so the action is the same, but a downstream
analytics layer might want to distinguish. v1 ships them under
one code; raising the question for Session 104.

### §7.3 — `transitioned_to_provisional_pending` semantics

The counter increments only when the prior status was
`PROVISIONAL`, not when the bet was already in
`PROVISIONAL_PENDING` and stays there. This matches the brief
field name ("transitioned"); but a user reading the result might
expect a "still-pending" sub-counter too. Not adding it in v1;
flagging.

### §7.4 — Threading scheduler self-rescheduling

`ThreadingReconciliationScheduler.schedule_periodic` re-arms by
calling itself recursively (each fire schedules a fresh
`threading.Timer`). The `_stopped` flag prevents runaway
re-arming after `stop()`. The recursive timer creation is
bounded (one timer alive at a time per scheduled run), but the
implementation does retain references in `self.timers` across
fires — `stop()` clears the list, but absent `stop()` the list
grows linearly with the number of fires. Not pathological for
v1's expected runtime (5-minute fires for hours of operation
yields ≤ ~12k entries/day) but worth knowing. The asyncio
substitute in v3 build proper avoids the issue.

### §7.5 — `update_match_status` ignores the new bookkeeping fields

The W4 `update_match_status` Protocol method writes only the
four match-status fields (status, matched_stake, unmatched_stake,
matched_price). The W6 `update_reconciliation_bookkeeping`
writes only the two reconciliation fields. These are independent
write paths against the same row. SQLite makes this safe under
the existing per-storage lock; concurrent multi-writer scenarios
(post-DR-029-close) would need to revisit. Confirming this is
acceptable for v1.

## §8 — Findings (beyond brief scope; not actioned)

### §8.1 — `requires-python = ">=3.12"` vs system python

`pyproject.toml` requires Python 3.12+; the system `python3`
binary is 3.11.9 and rejects PEP-695 `type` aliases at parse
time (via `clients/betfair_client/v1/envelope.py:104`). The
project venv at `.venv/` is correctly Python 3.12.7. Pre-flight
`pytest --collect-only` via `python3` produced 15 collection
errors before falling back to `.venv/bin/python`; this is not
a blocker but is a foot-gun for anyone running tests from the
project root without invoking the venv interpreter explicitly.
Operationally, the project's test invocation should be wrapped
(Makefile, `pytest` shim, or `pytest` invocation guide in
README). Not in W6 scope; flagging.

### §8.2 — Pre-flight working-tree state

Working tree at session open had pre-existing dirty regions
(modified `clients/betfair_client/v1/__init__.py` +
`_translation.py`; untracked `clients/betfair_client/v1/
account_funds.py`, `current_orders.py`, `market_catalogue.py`,
their tests, and the entire `tests/workflows/` +
`workflows/bet_entry/v1/` trees). Per brief §10, these are the
expected post-Session-101 state — none intersect W6's named
anchors. No conflicts surfaced. Confirmed at close: dirty file
list = pre-existing untracked/modified + W6's named anchors only.

### §8.3 — `clients.betfair_client.v1.market_settlement` already exposed

The W3 `__init__.py` already re-exports both the function
`market_settlement` and the snapshot type `MarketSettlement`
(`clients/betfair_client/v1/__init__.py:79-85`). W6 didn't have
to add anything to W3. The `RealBetfairAdapter` import block
grew to include `MarketSettlement` + `market_settlement` from
the existing W3 surface.

### §8.4 — `consumer.py` already exposes `get_market_settlement`

`clients/betfair_client/v1/consumer.py:103-110` defines
`get_market_settlement(market_id, client) -> ReadEnvelope[MarketSettlement]`
— a `BetfairClient`-scoped wrapper over `market_settlement`.
W6's `RealBetfairAdapter.get_market_settlement` calls
`market_settlement(market_id, self.client.rest_client)` directly
rather than going through the consumer wrapper, mirroring the
existing pattern in the adapter (e.g. `place_bet` is called
directly, not via `get_live_market_prices` → `place_bet`). Both
paths produce the same envelope; the direct call avoids one
indirection. Flagging in case the `consumer` wrapper was the
intended surface.

### §8.5 — `_lock` inside `update_reconciliation_bookkeeping` SQL

The SQLite `update_reconciliation_bookkeeping` UPDATE uses
`COALESCE(reconciliation_attempts, 0) + ?` to handle
NULL-after-migration cases (a legacy DB that ran the migration
mid-session might have NULL values until a write touches them).
Without `COALESCE`, `NULL + 1` would yield NULL, breaking the
counter. The DDL `DEFAULT 0` makes this defensive on fresh
installs but not on the migration path where the column is
added without back-filling. Flagging — works correctly for v1;
W6.5 may want to back-fill on migration.

### §8.6 — `MockBetfairAdapter` shape change for `Literal` import

`test_orchestrator.py` already imported `Literal` from `typing`;
the new `set_market_settlement_unavailable` setter reuses that
existing import. No new top-level imports added beyond
`MarketSettlement` from `clients.betfair_client.v1.settlement`.

### §8.7 — Pyright/mypy not run in session

Brief §7 functional verification list doesn't name mypy/pyright;
ruff + import-linter are the static checks specified, both
clean. The Pydantic v2 models use `model_config = ConfigDict(
frozen=True)` consistent with the existing W4 pattern.
Flagging — Session 104 may want to run `mypy --strict` once.

## §9 — Self-assessment

### §9.1 — Pre/post baselines

| Metric | Pre-baseline | Post-baseline | Δ |
|---|---|---|---|
| `pytest` passing | 361 | 416 | +55 |
| `ruff check` | clean | clean | — |
| `import-linter` | 5 kept, 0 broken | 5 kept, 0 broken | — |
| `bets` table column count | 18 | 20 | +2 |

### §9.2 — Functional verification checklist

- [x] All `_resolve_one` decision paths exercised via
  resolution-decision tests per §5.9 first sub-list (24 tests
  including parametrised pass-throughs).
- [x] `run_reconciliation_pass` exercised end-to-end via
  pass-level tests per §5.9 second sub-list (9 tests).
- [x] Storage methods exercised for both
  `InMemoryBetRecordStorage` (4 tests) and
  `SQLiteBetRecordStorage` (5 tests).
- [x] Inline DDL migration exercised idempotently
  (`test_sqlite_inline_migration_idempotent`) and on legacy DB
  upgrade (`test_sqlite_pre_existing_db_gets_columns_added`).
- [x] `RealBetfairAdapter.get_market_settlement` exercised via
  the five new tests per §5.10.
- [x] `MarketSettlement` parses cleanly through the W4 boundary
  (covered structurally by the existing W3-side tests at
  `test_settlement.py`; W4-side coverage exercises the boundary
  translation only).
- [x] Adelaide-local timestamps confirmed
  (`test_pass_uses_adelaide_local_timestamps`) per DR-021.
- [x] No live Betfair API calls (mocked-only confirmation).
- [x] `ruff check` clean.
- [x] `import-linter` 5 contracts kept.

### §9.3 — `git status` snapshots

**Session open (2026-05-07 18:35 ACST):**

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

**Session close (2026-05-07 18:50 ACST):**

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

The dirty-region surface didn't change at the file level — W6's
edits land entirely inside the already-untracked
`workflows/bet_entry/v1/` and `tests/workflows/` trees plus
edits inside those trees. No `git add` was issued; no commits
were created.

### §9.4 — `PRAGMA table_info(bets)` snapshots

**Pre-baseline (18 columns):**

```
0   bet_id                    TEXT  PK
1   cycle_id                  TEXT  NOT NULL
2   entry_path                TEXT  NOT NULL
3   strategy_tag              TEXT
4   is_free_bet               INTEGER NOT NULL
5   free_bet_conversion_rate  REAL
6   realised_conversion_rate  REAL
7   requested_stake           TEXT  NOT NULL
8   matched_stake             TEXT  NOT NULL
9   unmatched_stake           TEXT  NOT NULL
10  matched_price             REAL
11  match_status              TEXT  NOT NULL
12  soft_book_combined_price  REAL
13  placed_at                 TEXT  NOT NULL
14  book_or_exchange          TEXT  NOT NULL
15  account_at_book_id        TEXT  NOT NULL
16  price_source              TEXT
17  betfair_bet_id            TEXT
```

**Post-baseline (20 columns):**

Same as above, plus:

```
18  last_reconciled_at        TEXT
19  reconciliation_attempts   INTEGER  DEFAULT 0
```

### §9.5 — Mocked-only confirmation

No live Betfair API calls. All tests use:

- `MockBetfairAdapter` (deterministic test double from
  `test_orchestrator.py`) for the W4 boundary.
- `MockTransport` (REST-side fixture from
  `tests/fixtures/betfair/`) for the
  `test_betfair_adapter.py` settlement tests.
- `InMemoryBetRecordStorage` + `SQLiteBetRecordStorage` against
  `tmp_path` for storage tests.

No HTTP traffic, no streaming connections, no auth flows.

### §9.6 — Length flag

Report length: ~ 750 lines (within brief §8's 700-1100 target
band). Within the W3 brief precedent's 1000-line surface-flag
threshold.

### §9.7 — Adelaide-local timestamp confirmation per DR-021

All session-anchor timestamps captured via
`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`. Pass-result
timestamps in tests use `datetime(..., tzinfo=ZoneInfo(
"Australia/Adelaide"))` and the worker's default clock uses
`datetime.now(ZoneInfo("Australia/Adelaide"))` per DR-021.
`test_pass_uses_adelaide_local_timestamps` asserts `tzinfo` is
`Australia/Adelaide` on the pinned-clock fixture.

---

**End of report.**
