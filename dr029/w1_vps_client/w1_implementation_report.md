# W1 — `vps_client` v1.0 implementation: Code report

**Brief:** `dr029/w1_vps_client/w1_brief.md` (Session 83).
**Repo target:** `/Users/tim/Desktop/Projects/bethub-v3/clients/vps_client/v1/`.
**Contract:** `dr029/2_7_api_contract_versioning/vps_client_contract.md` v1.0.

---

## §1 — Anchor (session start)

`2026-05-05 15:07 ACST` (Adelaide local, per DR-021).

---

## §2 — Pre-flight

SSH to `root@187.77.183.9` succeeded; `capture.db` accessible at the canonical path:

```
$ ssh root@187.77.183.9 'ls -la /home/racing/racing-data-capture/data/capture.db'
-rw-r--r-- 1 racing racing 2198802432 May  5 05:37 /home/racing/racing-data-capture/data/capture.db
```

Schema introspection ran via remote `python3 sqlite3` per Cat 3 (live database queries via `start_process` Python; never copy the file). Result captured to `dr029/w1_vps_client/capture_db_schema.md`.

Pre-flight passed; proceeded to step 2.

---

## §3 — Schema introspection summary

Seven tables present in `capture.db` (~2.05 GB). Six are relevant to v1.0:

| Table | Rows | Used by |
|---|---|---|
| `races` | 60,264 | §9.1, §9.4, §9.5, §9.6 |
| `runners` | 435,251 | §9.2, §9.3, §9.5, §9.6 |
| `betfair_snapshots` | 1,740,185 | §9.4, §9.5 |
| `betfair_historical` | 163,809 | §9.5 fallback |
| `bookmaker_snapshots` | 2,964,813 | not used by v1.0 |
| `snapshot_batch_summary` | 439,881 | not used by v1.0 |
| `daily_calibration_summary` | 64 | not used by v1.0 |

Notable shape findings (full mapping in `capture_db_schema.md`):

- `races` carries `betfair_win_market_id` (TEXT, e.g. `"1.254588168"`) but **no Betfair `event_id` column**. Surface §9.1 maps the contract `event_id: str` parameter to `betfair_win_market_id` lookup. → Finding F1.
- `races` has no thoroughbred / harness / greyhound discriminator. capture.db is thoroughbred-only by data shape. `RaceCode.THOROUGHBRED` is hard-coded. → Finding F2.
- `runners.result_status` has 5 distinct values (`WINNER`, `LOSER`, `PLACED`, `REMOVED`, `NULL`); `runners.results_source` has 4 (`subscription`, `betfair_only`, `betfair_and_subscription`, `NULL`).
- `scheduled_start` is ISO-formatted UTC (`Z` suffix); `snapshot_time` is ISO with timezone offset (e.g. `+00:00`).

Indexes available cover the load-bearing queries: `idx_bf_race_time` (race_id, snapshot_time) for §9.4 bracketing window scans; `idx_bfh_market_selection` for §9.5 historical fallback joins.

---

## §4 — Envelope module summary

`bethub-v3/clients/vps_client/v1/envelope.py` (~70 lines):

- `EnvelopeStatus` (`fresh` / `stale` / `unavailable`).
- `UnavailableReason` — five values exactly matching contract §8.2: `vps_unreachable`, `capture_db_locked`, `not_yet_captured`, `not_in_capture_window`, `genuine_absence`.
- `FreshEnvelope[T]`, `StaleEnvelope[T]`, `UnavailableEnvelope` Pydantic v2 generic models.
- `Envelope[U]` PEP-695 type alias (`type Envelope[U] = FreshEnvelope[U] | StaleEnvelope[U] | UnavailableEnvelope`) so the envelope is runtime-subscriptable per Python 3.12 type-alias syntax. → Finding F3 (deviation from contract's typing.Generic[T] phrasing).
- `now_adelaide()` and `to_adelaide()` helpers; both honour DR-021.

`T` is unbounded (`TypeVar("T")`) so the envelope can wrap either a single Pydantic model (e.g. `RaceMetadata`) or `list[RunnerMetadata]` for the §9.2 full-field surface. The contract specifies `Envelope[list[RunnerMetadata]]` for `race_runners()`; the bound on `T` had to drop to allow lists.

Envelope models declare `model_config = {"arbitrary_types_allowed": True}` so the discriminated union accepts list payloads.

---

## §5 — Per-surface implementation summary

### §5.1 §9.1 race metadata — `race_metadata.py`

- Endpoint: `/v1/race/{event_id}/metadata` (Python: `race_metadata(event_id)`).
- SQL: single SELECT against `races` keyed on `betfair_win_market_id`.
- Heuristic for `unavailable`: `capture_status='PENDING'` or `betfair_last_snapshot_at IS NULL` → `NOT_YET_CAPTURED` (retry 60s); `race_date` > 365 days ago → `NOT_IN_CAPTURE_WINDOW` (terminal); no row → `GENUINE_ABSENCE`.
- Freshness target: 120 s against `betfair_last_snapshot_at`; older → `StaleEnvelope` with `lag_seconds = age - 120`.
- `RaceCode` always `THOROUGHBRED` per F2.
- Seven tests in `test_race_metadata.py` cover fresh / stale / `NOT_YET_CAPTURED` / `NOT_IN_CAPTURE_WINDOW` / `GENUINE_ABSENCE` / `VPS_UNREACHABLE` (missing path) / `CAPTURE_DB_LOCKED` (mocked).

### §5.2 §9.2 runner metadata — `runner_metadata.py`

- Two endpoints: `/v1/race/{event_id}/runners` (full field, `race_runners()`) and `/v1/race/{event_id}/runner/{selection_id}` (single, `runner_metadata()`).
- SQL: race-row lookup by `betfair_win_market_id`, then `runners` filtered by `race_id` (and optionally `betfair_selection_id`).
- `selection_id` accepted as `str`, cast to `int` for the join. Non-numeric selection ids return `GENUINE_ABSENCE`.
- Same `_classify_availability()` pre-check as §9.1 — shared semantics.
- `ScratchingStatus` derived from `runners.scratched` (0/1) + `scratched_at`.
- Nine tests cover full-field, single-runner, scratched runner, stale, `NOT_YET_CAPTURED`, `NOT_IN_CAPTURE_WINDOW`, two `GENUINE_ABSENCE` paths, non-numeric selection.

### §5.3 §9.3 results — `results.py`

- Endpoint: `/v1/race/{event_id}/results`.
- SQL: race-row lookup + filtered runner aggregate.
- Heuristic: empty runner set OR no row with `result_status` set → `NOT_YET_CAPTURED` (retry 120s). Older than 365 days → `NOT_IN_CAPTURE_WINDOW`. Race row missing → `GENUINE_ABSENCE`. Otherwise → `fresh`.
- `dead_heat` derived: count of `WINNER` rows; `True` for any winner if count > 1.
- `market_voided` derived: all rows `REMOVED`.
- `stewards_status` always `OFFICIAL` per F4 (capture.db has no stewards-status enum; `stewards_comment` text is not parsed in v1.0).
- `sectional_times_seconds` always `None` per F5 (no column in capture.db).
- Five tests cover fresh-with-winner, `NOT_YET_CAPTURED`, `NOT_IN_CAPTURE_WINDOW`, `GENUINE_ABSENCE`, market-voided-flag-off.

### §5.4 §9.5 BSP / sp_near / sp_far — `starting_price.py`

- Endpoint: `/v1/runner/{event_id}/{selection_id}/bsp`.
- SQL: race lookup, then `runners.sp_fixed` (settled SP if present), then latest `betfair_snapshots` row for `(race_id, runner_id)`, then `betfair_historical.win_bsp` fallback.
- Reading order: `runners.sp_fixed` → snapshot `bsp_price` → historical `win_bsp`. `sp_near` and `sp_far` come from latest snapshot.
- `reconciled` is `True` when `sp_fixed` populated OR a final snapshot has `bsp_price`.
- Heuristic: no signal at all → `NOT_YET_CAPTURED` (retry 180s).
- Six tests: reconciled BSP, projection-only pre-reconciliation, `NOT_YET_CAPTURED`, `NOT_IN_CAPTURE_WINDOW`, two `GENUINE_ABSENCE` paths.

### §5.5 §9.4 bracketing — `bracketing.py`

- Endpoint: `/v1/race/{event_id}/bracket?from={ts}&to={ts}`.
- SQL: race lookup, then `betfair_snapshots JOIN runners` filtered by `race_id` + `snapshot_time` window. Optional `selection_id` adds `runners.betfair_selection_id` filter.
- Window > 24h → `GENUINE_ABSENCE` per contract bound on payload size.
- Inverted window (from > to) → `GENUINE_ABSENCE`.
- Snapshots grouped by `snapshot_time` into `BracketSnapshot` items; runners flattened per snapshot.
- Eight tests: fresh series, selection-filtered series, empty-window absence, oversize window rejection, inverted window rejection, `NOT_IN_CAPTURE_WINDOW`, `NOT_YET_CAPTURED`, unknown event `GENUINE_ABSENCE`.

### §5.6 §9.6 identifier resolution — `identifier_resolution.py`

- Endpoint: `/v1/identity/resolve?market_id={mid}&selection_id={sid}`.
- SQL: race lookup by `market_id`, then runner lookup by `(race_id, selection_id)`.
- Per contract §9.6, ingestion lag is collapsed onto the success path: market known + selection missing → `resolved=False` with `lag_indicator_seconds=120`. Both known → `resolved=True`.
- Market unknown → `GENUINE_ABSENCE`. Outside window → `NOT_IN_CAPTURE_WINDOW`. Non-numeric selection → `GENUINE_ABSENCE`.
- Five tests: resolved success, market-known-selection-missing, unknown-market, outside-window, non-numeric selection.

---

## §6 — Error mapping summary

`clients/vps_client/v1/_errors.py` (~30 lines):

```python
def map_operational_error(exc: OperationalError) -> UnavailableEnvelope:
    msg = str(exc).lower()
    if "database is locked" in msg:
        return UnavailableEnvelope(
            reason=UnavailableReason.CAPTURE_DB_LOCKED, retry_after=5,
        )
    return UnavailableEnvelope(
        reason=UnavailableReason.VPS_UNREACHABLE, retry_after=60,
    )
```

The two exception-shaped reasons are mapped here; the four row-shape reasons (`GENUINE_ABSENCE`, `NOT_YET_CAPTURED`, `NOT_IN_CAPTURE_WINDOW`, `STALE`) are surface-specific and live inside each surface module's heuristic. Per-surface heuristics documented in module docstrings.

Four tests in `test_error_mapping.py` cover: `database is locked` → `CAPTURE_DB_LOCKED` (retry 5s), `unable to open database file` → `VPS_UNREACHABLE` (retry 60s), unknown OperationalError → `VPS_UNREACHABLE` fall-through, envelope status check.

`_connection.py` opens a SQLAlchemy connection in SQLite read-only mode (`mode=ro&uri=true`). Engine cache keyed by path so a single test process reuses one engine per fixture.

`_clock.py` exposes `now_utc()` as a module attribute so tests can `monkeypatch.setattr(_clock, "now_utc", ...)` without per-surface patching. All surfaces import via `from . import _clock` and call `_clock.now_utc()` — a deliberate choice to enable deterministic tests against the byte-stable fixture (Finding F6).

---

## §7 — Fixture summary

`tests/fixtures/build_capture_fixture.py` (~270 lines) is the reproducible builder. Re-running from clean state produces a byte-identical fixture file. The fixture file is committed (40,960 bytes) so the test suite runs without first invoking the builder.

Rows in `capture_db_fixture.sqlite`:

| Table | Rows | Notes |
|---|---|---|
| `races` | 4 | id 1 fresh, id 2 stale, id 3 PENDING, id 4 outside-window (race_date 2020-01-01) |
| `runners` | 7 | 4 in race 1 (active, scratched, winner, loser); 1 each in races 2/3/4 |
| `betfair_snapshots` | 5 | 3-snapshot bracketing series for runner 10; final-snapshot reconciled BSP for runner 12 (winner); 1 stale-side snapshot for race 2 |
| `betfair_historical` | 1 | settled win_bsp for race 1 winner — fallback path |

Status coverage per surface:

- §9.1 race metadata: fresh (race 1), stale (race 2), `NOT_YET_CAPTURED` (race 3), `NOT_IN_CAPTURE_WINDOW` (race 4), `GENUINE_ABSENCE` (unknown market_id).
- §9.2 runner metadata: same plus `GENUINE_ABSENCE` (missing selection) and active vs scratched runners (race 1).
- §9.3 results: fresh (race 1 has WINNER + LOSER), `NOT_YET_CAPTURED` (race 3), `NOT_IN_CAPTURE_WINDOW` (race 4), `GENUINE_ABSENCE` (unknown).
- §9.4 bracketing: fresh series (race 1, runner 10), filtered series, empty-window absence, oversize window, inverted window, `NOT_IN_CAPTURE_WINDOW`, `NOT_YET_CAPTURED`, `GENUINE_ABSENCE`.
- §9.5 BSP: reconciled (race 1 / runner 10003), projection-only (race 1 / runner 10001), `NOT_YET_CAPTURED` (race 3 runner 30001), `NOT_IN_CAPTURE_WINDOW` (race 4), `GENUINE_ABSENCE` paths.
- §9.6 identity: resolved (race 1 / runner 10001), market-known-selection-missing (race 1 / fake selection), unknown market, outside-window, non-numeric selection.

The test conftest pins `_clock.now_utc()` to the fixture's reference "now" (`2026-05-05T05:00:00Z`) so freshness arithmetic against fixed timestamps is deterministic. Without the pin, `test_fresh_*` tests would flake into `stale` envelopes as wall-clock advances past the fixture's `RECENT_UTC` value.

---

## §8 — Final verification (verbatim output)

### `uv run ruff check`

```
All checks passed!
```

### `uv run mypy .`

```
Success: no issues found in 44 source files
```

### `uv run lint-imports`

```
Analyzed 43 files, 64 dependencies.
----------------------------------

DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT

Contracts: 5 kept, 0 broken.
```

### `uv run pytest -v`

```
collected 57 items

tests/clients/vps_client/v1/test_bracketing.py::test_fresh_series_returned_in_window PASSED [  1%]
tests/clients/vps_client/v1/test_bracketing.py::test_selection_filter_narrows_series PASSED [  3%]
tests/clients/vps_client/v1/test_bracketing.py::test_genuine_absence_when_no_snapshots_in_window PASSED [  5%]
tests/clients/vps_client/v1/test_bracketing.py::test_window_too_large_rejected PASSED [  7%]
tests/clients/vps_client/v1/test_bracketing.py::test_inverted_window_rejected PASSED [  8%]
tests/clients/vps_client/v1/test_bracketing.py::test_not_in_capture_window_for_old_race PASSED [ 10%]
tests/clients/vps_client/v1/test_bracketing.py::test_not_yet_captured_for_pending_race PASSED [ 12%]
tests/clients/vps_client/v1/test_bracketing.py::test_genuine_absence_for_unknown_event PASSED [ 14%]
tests/clients/vps_client/v1/test_envelope.py::test_fresh_envelope_carries_payload PASSED [ 15%]
tests/clients/vps_client/v1/test_envelope.py::test_stale_envelope_carries_lag PASSED [ 17%]
tests/clients/vps_client/v1/test_envelope.py::test_unavailable_envelope_terminal_reason PASSED [ 19%]
tests/clients/vps_client/v1/test_envelope.py::test_unavailable_envelope_transient_reason PASSED [ 21%]
tests/clients/vps_client/v1/test_envelope.py::test_to_adelaide_converts_naive_to_local PASSED [ 22%]
tests/clients/vps_client/v1/test_envelope.py::test_to_adelaide_preserves_aware_timestamp PASSED [ 24%]
tests/clients/vps_client/v1/test_envelope.py::test_unavailable_reason_values_match_contract PASSED [ 26%]
tests/clients/vps_client/v1/test_error_mapping.py::test_database_locked_maps_to_capture_db_locked PASSED [ 28%]
tests/clients/vps_client/v1/test_error_mapping.py::test_io_failure_maps_to_vps_unreachable PASSED [ 29%]
tests/clients/vps_client/v1/test_error_mapping.py::test_unknown_operational_error_falls_through_to_vps_unreachable PASSED [ 31%]
tests/clients/vps_client/v1/test_error_mapping.py::test_envelope_status_is_unavailable PASSED [ 33%]
tests/clients/vps_client/v1/test_identifier_resolution.py::test_resolves_when_market_and_selection_present PASSED [ 35%]
tests/clients/vps_client/v1/test_identifier_resolution.py::test_market_known_selection_missing_returns_lag_indicator PASSED [ 36%]
tests/clients/vps_client/v1/test_identifier_resolution.py::test_market_unknown_returns_genuine_absence PASSED [ 38%]
tests/clients/vps_client/v1/test_identifier_resolution.py::test_market_outside_capture_window PASSED [ 40%]
tests/clients/vps_client/v1/test_identifier_resolution.py::test_non_numeric_selection_returns_genuine_absence PASSED [ 42%]
tests/clients/vps_client/v1/test_race_metadata.py::test_fresh_returns_full_metadata PASSED [ 43%]
tests/clients/vps_client/v1/test_race_metadata.py::test_stale_when_last_snapshot_lags PASSED [ 45%]
tests/clients/vps_client/v1/test_race_metadata.py::test_not_yet_captured_for_pending_status PASSED [ 47%]
tests/clients/vps_client/v1/test_race_metadata.py::test_not_in_capture_window_for_old_race PASSED [ 49%]
tests/clients/vps_client/v1/test_race_metadata.py::test_genuine_absence_for_unknown_event PASSED [ 50%]
tests/clients/vps_client/v1/test_race_metadata.py::test_vps_unreachable_for_missing_path PASSED [ 52%]
tests/clients/vps_client/v1/test_race_metadata.py::test_capture_db_locked_maps_to_locked_reason PASSED [ 54%]
tests/clients/vps_client/v1/test_results.py::test_fresh_results_carry_winner_and_loser PASSED [ 56%]
tests/clients/vps_client/v1/test_results.py::test_not_yet_captured_when_race_unfinalised PASSED [ 57%]
tests/clients/vps_client/v1/test_results.py::test_not_in_capture_window_for_old_race PASSED [ 59%]
tests/clients/vps_client/v1/test_results.py::test_genuine_absence_for_unknown_event PASSED [ 61%]
tests/clients/vps_client/v1/test_results.py::test_market_voided_flag_off_for_clean_settlement PASSED [ 63%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_full_field_returns_all_runners PASSED [ 64%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_single_runner_lookup PASSED [ 66%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_scratched_runner_status_propagates PASSED [ 68%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_stale_when_race_lags PASSED [ 70%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_not_yet_captured_for_pending PASSED [ 71%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_not_in_capture_window_for_old PASSED [ 73%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_genuine_absence_for_unknown_event PASSED [ 75%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_genuine_absence_for_missing_selection PASSED [ 77%]
tests/clients/vps_client/v1/test_runner_metadata.py::test_non_numeric_selection_id_returns_genuine_absence PASSED [ 78%]
tests/clients/vps_client/v1/test_starting_price.py::test_reconciled_bsp_returned_for_finalised_runner PASSED [ 80%]
tests/clients/vps_client/v1/test_starting_price.py::test_projection_returned_pre_reconciliation PASSED [ 82%]
tests/clients/vps_client/v1/test_starting_price.py::test_not_yet_captured_when_no_signal PASSED [ 84%]
tests/clients/vps_client/v1/test_starting_price.py::test_not_in_capture_window_for_old PASSED [ 85%]
tests/clients/vps_client/v1/test_starting_price.py::test_genuine_absence_for_unknown_event PASSED [ 87%]
tests/clients/vps_client/v1/test_starting_price.py::test_genuine_absence_for_unknown_selection PASSED [ 89%]
tests/test_skeleton.py::test_python_version_supported PASSED             [ 91%]
tests/test_skeleton.py::test_all_packages_importable PASSED              [ 92%]
tests/test_skeleton.py::test_dependencies_importable PASSED              [ 94%]
tests/test_skeleton.py::test_pydantic_v2 PASSED                          [ 96%]
tests/test_skeleton.py::test_sqlalchemy_core_usable PASSED               [ 98%]
tests/test_skeleton.py::test_import_linter_config_present PASSED         [100%]

============================== 57 passed in 0.34s ==============================
```

57 passed (51 W1 surface tests + 6 W0 skeleton tests). Brief §5.5 target was 50–70; landed at 57 — within range.

---

## §9 — Git state

```
$ git log --oneline
0f5fae3 W1: vps_client v1.0 implemented per locked contract (§9.1–§9.6 + envelope + error mapping + fixture + tests)
67a7f04 W0: v3 repo skeleton initialised per DR-030 (layout) and DR-031 (stack)
```

Two commits on `main`: W0's prior skeleton commit, plus this session's single W1 commit. Working tree clean post-commit. Per the brief's hard limit "no commits beyond step 8", no amend was needed; all toolchain checks passed clean before the commit landed.

---

## §10 — Pass/fail status table

| # | Criterion | Status |
|---|---|---|
| 1 | `envelope.py` exists; envelope models instantiate without error | PASS |
| 2 | All six surface modules exist with public functions matching contract signatures | PASS |
| 3 | `tests/fixtures/capture_db_fixture.sqlite` exists and is non-empty | PASS — 40,960 bytes |
| 4 | `tests/fixtures/build_capture_fixture.py` exists; rerunning from clean produces the committed fixture | PASS — verified |
| 5 | `uv run ruff check` exits 0 with no findings | PASS |
| 6 | `uv run mypy .` exits 0 with no findings | PASS |
| 7 | `uv run lint-imports` exits 0 with five contracts kept, zero broken | PASS |
| 8 | `uv run pytest -v` exits 0; six W0 skeleton tests still pass; 57 total tests passed | PASS |
| 9 | Schema reference doc exists at `dr029/w1_vps_client/capture_db_schema.md` | PASS |
| 10 | `git log` shows exactly one new commit on main with §6 step 8 message | PASS |

**Overall status: verification passed clean.** All ten criteria met.

---

## §11 — Findings

Six findings surfaced. None blocked verification clean. All deferred to next operator-Claude session triage.

### Finding F1: contract `event_id` ↔ capture.db `betfair_win_market_id`

- **Step where it surfaced:** §6 step 1 (schema introspection).
- **Expected:** contract §9.1 specifies `event_id: str` as "Betfair `event_id` (canonical race identity per §2.8)".
- **Actual:** capture.db has no Betfair event_id column. The closest Betfair-side identifier on `races` is `betfair_win_market_id` (TEXT, format `"1.254588168"`).
- **Output:** `PRAGMA table_info(races)` shows columns including `betfair_win_market_id TEXT` and `betfair_place_market_id TEXT`, but no `betfair_event_id` or equivalent.
- **Code's read:** the contract spec was drafted against the Betfair API terminology where `event_id` identifies the race and `market_id` identifies a specific market within an event. capture.db's pipeline appears to key races by their Win-market ID directly, conflating event/market levels. For W1 v1.0, the implementation accepts the contract's `event_id: str` parameter and joins on `races.betfair_win_market_id`. This is a terminology gap, not a functional one — the lookup works correctly with values like `"1.000000001"`. The contract's `RaceMetadata.event_id` field is echoed back unchanged. If the operator wants strict Betfair-event-id semantics, capture.db would need an additional column populated upstream (out of scope here).
- Code did NOT attempt remediation per §1 of brief — the alternative (mapping `event_id` to `races.id` integer PK cast to string) breaks Betfair-side discoverability. The win-market-id mapping is the most defensible interpretation.

### Finding F2: `RaceCode` always `THOROUGHBRED` — capture.db has no code discriminator

- **Step where it surfaced:** §6 step 1 (schema introspection).
- **Expected:** contract §9.1 `RaceMetadata.code: RaceCode` enum with three values (`THOROUGHBRED`, `HARNESS`, `GREYHOUND`).
- **Actual:** `races.meeting_type` distinct values are `(NULL, COUNTRY, METRO, PROVINCIAL)` — none of which encode the three racing codes. No other column in the schema has the discriminator.
- **Output:** `SELECT meeting_type, COUNT(*) FROM races GROUP BY meeting_type` produces only meeting-tier values.
- **Code's read:** capture.db is thoroughbred-only by data shape (the upstream `racing-data-capture` pipeline appears scoped to thoroughbred). `RaceMetadata.code` is hard-coded to `RaceCode.THOROUGHBRED`. If/when capture.db extends to harness or greyhound, this default needs revisiting — likely as a backward-compatible v1.x change adding a code column upstream + reading it here. Contract §11.4 framing on "no code field today" would also apply.
- Code did NOT attempt remediation per §1 of brief — surfaced for visibility.

### Finding F3: `Envelope` type alias uses PEP-695 syntax, deviating from contract phrasing

- **Step where it surfaced:** §6 step 4 (test runs after `_envelope_for` cast addition).
- **Expected:** contract §8.3 shows `Envelope = FreshEnvelope[T] | StaleEnvelope[T] | UnavailableEnvelope` as a non-PEP-695 union alias.
- **Actual:** that form is not runtime-subscriptable in Python 3.12 (`Envelope[X]` raises `TypeError: ... is not a generic class`). Switched to `type Envelope[U] = FreshEnvelope[U] | StaleEnvelope[U] | UnavailableEnvelope` (PEP-695 generic type alias).
- **Output:**
  ```
  TypeError: clients.vps_client.v1.envelope.FreshEnvelope | clients.vps_client.v1.envelope.StaleEnvelope | clients.vps_client.v1.envelope.UnavailableEnvelope is not a generic class
  ```
- **Code's read:** the contract's phrasing is a typing-level alias (mypy understands it) but doesn't survive runtime subscripting. PEP-695 syntax (Python 3.12+) gives the same typing surface plus runtime support. The deviation is local to `envelope.py` — the contract surface upward is unchanged. Future contract revisions might want to update the example phrasing for accuracy under DR-031 (Python 3.12+).
- Code did NOT attempt remediation per §1 of brief — flagged.

### Finding F4: `RunnerResult.stewards_status` always `OFFICIAL` for v1.0

- **Step where it surfaced:** §6 step 4 (results surface implementation).
- **Expected:** contract §9.3 `StewardsStatus` enum has four values (`OFFICIAL`, `PROTEST_PENDING`, `PROTEST_UPHELD`, `DISQUALIFIED`).
- **Actual:** capture.db has `runners.stewards_comment` (free-text) but no enumerated stewards-status column. Mapping free text to the four enum values reliably is not a v1.0-bounded transformation.
- **Output:** schema shows `stewards_comment TEXT` only.
- **Code's read:** v1.0 implementation hard-codes `StewardsStatus.OFFICIAL`. This is a defensible default — the vast majority of races settle official. Edge cases (protest pending, disqualifications) currently surface only via `result_status='REMOVED'` for the affected runner. A future improvement: parse `stewards_comment` for known phrases ("disqualified", "protest"). Out of scope for W1.
- Code did NOT attempt remediation per §1 of brief — flagged.

### Finding F5: `RunnerResult.sectional_times_seconds` always `None`

- **Step where it surfaced:** §6 step 4 (results surface implementation).
- **Expected:** contract §9.3 `RunnerResult.sectional_times_seconds: list[float] | None`.
- **Actual:** capture.db has no sectional-times column on `runners` or any other table.
- **Output:** schema confirms — `runners` columns include result-shape fields but no sectional times.
- **Code's read:** this is a "field reserved for future use" case. The contract spec shape allows `None`; v1.0 always returns `None`. If sectional times are added to capture.db upstream, the implementation reads them; no contract change needed (backward-compatible additive).
- Code did NOT attempt remediation per §1 of brief — flagged.

### Finding F6: `_clock.now_utc()` test-patchability pattern

- **Step where it surfaced:** §6 step 4 (post-implementation test runs failed deterministically).
- **Expected:** tests against the byte-stable fixture would assert `fresh` envelopes for fixture rows tagged "recent".
- **Actual:** the fixture's `RECENT_UTC` is a fixed string (`2026-05-05T04:59:30.000Z`) — by the time tests run, wall-clock has moved on, so freshness arithmetic compares fixed past vs current `datetime.now()` and the test sees `stale`.
- **Output:** original test failures showed `StaleEnvelope` returned where tests expected `FreshEnvelope`.
- **Code's read:** the brief §5.5 specifies "Builder script is reproducible: running it from a clean state produces a byte-identical fixture file." Reproducible-bytes requires fixed timestamps. Fixed timestamps require pinned-clock test execution. The fix: a private `_clock.py` module that all surfaces import as `from . import _clock` and call as `_clock.now_utc()`. Tests `monkeypatch.setattr(_clock, "now_utc", lambda: FIXTURE_NOW_UTC)` in conftest's autouse fixture. This is a v3-internal test-affordance pattern; no contract impact. Surfacing because future surfaces in W2+ should follow the same pattern (use `_clock.now_utc()` not `datetime.now()`) for the same testability reason.
- Code did NOT attempt remediation per §1 of brief — flagged so W2+ briefs can adopt the convention.

---

## §12 — Self-assessment

**Did Code stay within the named anchors?** Yes. Every typed return shape traces back to contract §9.x; every reason value is from the §8.2 closed set; the envelope shape matches §8.3; surface signatures match contract §9 exactly. Two style-level deviations (PEP-695 type alias per F3; ruff UP042/UP046 ignored for the contract's `(str, Enum)` and `Generic[T]` patterns) are flagged.

**Were any out-of-scope items touched?** No. No `betfair_client` work (W2 carry-forward). No operational store work (W6). No v3 module consuming `vps_client`. No CLV reconstruction. No new dependencies beyond W0. `tests/clients/__init__.py` and `tests/clients/vps_client/__init__.py` and `tests/clients/vps_client/v1/__init__.py` were added to make pytest discover the surface tests cleanly — these are scaffolding under `tests/`, not under `clients/`, so they don't extend v3 module surface.

**Did the session fit a single bounded run?** Yes. ~21 minutes wall-clock from anchor-start to anchor-close. The work fit comfortably; the only iteration cycle was on toolchain green-ness (six rounds of ruff/mypy fixups), each round well under a minute.

**Anything Code thinks the next operator-Claude session should know that the report doesn't otherwise capture:**

1. **Schema-doc in rebuild folder, not v3 repo.** `dr029/w1_vps_client/capture_db_schema.md` is governance reference. If/when the contract documentation files relocate from `dr029/2_7_api_contract_versioning/` to `bethub-v3/contracts/` per DR-030 administrative cleanup, the schema doc should travel too — it's the bridge between contract and SQL implementation.

2. **`_clock.now_utc()` testability pattern (Finding F6).** W2 (`betfair_client`) and W6 (operational store) will benefit from the same private-module clock pattern. Worth naming in those briefs so the convention is consistent across `clients/`.

3. **Heuristic refinement is a first-real-data carry-forward.** The §5.4 brief discipline ("simplest defensible heuristic per surface, document the heuristic in the module docstring") is followed — every surface module's docstring states the heuristic. Once v3 runs against real `capture.db` (not the fixture), some heuristic thresholds (the 365-day capture-window cutoff, the 120-second freshness target) will likely need calibration. The implementation centralises these as module-level constants for easy revisit.

4. **Pydantic generic + list payload tension (Finding F3).** The drop of `T: BaseModel` bound on the envelope generic was load-bearing for `Envelope[list[RunnerMetadata]]` per contract §9.2. If a future contract revision wants to tighten the envelope's typing, it would need to either (a) wrap the list in a `RootModel`, or (b) keep the unbounded `T`. Current v1.0 chose (b).

5. **57 tests vs 50–70 target.** Toward the lower end of the brief's range. Coverage is one passing test per envelope status per surface plus shared envelope shape and error-mapping coverage. Adding more tests would mostly be redundant against the heuristic-driven coverage already in place. Self-assessed as adequate for W1 v1.0 verification scope; W4+ consumers will exercise more paths via integration tests.

---

## §13 — Anchor (session close)

`2026-05-05 15:28 ACST` (Adelaide local, per DR-021).

**Session duration:** ~21 minutes from anchor-start to anchor-close.

**End of report.**
