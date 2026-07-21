# Capture.db lock contention — VPS pre-flight diagnostic

**Captured:** 2026-05-03 06:45 ACST (Session 53). Diagnostic ran in-session before drafting the remediation brief.
**Purpose:** Pre-flight diagnostic surfacing the operational symptoms, the mechanism, and the dirty-tree state for the `capture.db_lock_fix_brief.md`. Per `bethub-brief-drafting` skill Step 2 precedent.

## Operational symptom

The orchestrator service (`racing-capture.service`, PID 686) is failing to persist newly-discovered races. Last successful persist batch in `capture.db` is for `race_date = 2026-05-01`. Today (Sunday 2026-05-03) and yesterday (Saturday 2026-05-02) racing cards are missing entirely — zero rows in `races` for those dates.

Discovery cycles continue to fire (`journalctl -u racing-capture` shows "Discovery complete: 0 new races, 122 total active" repeating), but every persist attempt errors out with `database is locked`. The 122-race active set is the May 1 races; new races discovered are silently dropped.

The Saturday API observation probe (Session 52) wrote its data to a separate location (`api_probe_data/` JSONL files, not `capture.db`) so the probe was unaffected — but the orchestrator's normal capture path has been failing across two days.

## Filesystem state

```
/home/racing/racing-data-capture/data/
  capture.db       2,116,558,848  (2.1 GB)   May 1 10:42
  capture.db-shm     851,968                 May 2 14:03
  capture.db-wal   426,358,232    (426 MB)   May 2 14:03
```

The WAL file at 426 MB is the load-bearing anomaly. Normal SQLite WAL operation checkpoints back into the main DB file every few thousand pages (default ~1000 pages = ~4 MB). A 426 MB WAL means the checkpoint mechanism has been blocked from running for an extended period.

## Open file handles on capture.db

```
COMMAND   PID    USER    FD   TYPE   SIZE/OFF      NAME
uvicorn   685    racing  13rr REG    2116558848    capture.db
python    686    racing  4ur  REG    2116558848    capture.db
```

Two processes hold capture.db open:
- **PID 685** is `uvicorn api.main:app --host 127.0.0.1 --port 8400`, started Apr 30 from systemd as `racing-api.service`.
- **PID 686** is `scripts/run_collector.py`, started Apr 30 from systemd as `racing-capture.service` (the orchestrator).

The `r` modifier on uvicorn's FD13 indicates a read-locked file descriptor — held continuously since process start. This is the smoking gun.

## Mechanism

`api/main.py` lines 11-19:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open read-only DB connection
    app.state.db = get_connection()
    app.state.db_path = DB_PATH
    yield
    # Shutdown: close DB connection
    app.state.db.close()
```

`api/db.py` lines 9-17:

```python
def get_connection() -> sqlite3.Connection:
    """Open a read-only connection to capture.db."""
    conn = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    return conn
```

The API service opens **one read-only SQLite connection at process startup** (uvicorn lifespan startup hook on Apr 30) and stores it on `app.state.db`. Every route handler reuses that same connection via `request.app.state.db`. The connection lives for the entire uvicorn process lifetime.

In SQLite WAL mode, an open read connection holds an implicit "snapshot" of the WAL state at the time of its first read transaction (or each subsequent transaction boundary, depending on isolation mode). Until that connection closes or commits a new read transaction, the WAL cannot be checkpointed past the snapshot's read position. With `check_same_thread=False` and a long-lived connection serving requests across multiple async event-loop iterations, the connection effectively pins a read snapshot indefinitely.

Result: WAL grows monotonically. At the threshold where the WAL exceeds normal SQLite busy-timeout defaults during a `BEGIN IMMEDIATE` write (the orchestrator's persist path), the writer fails with `database is locked` instead of waiting for a checkpoint that cannot run.

This is a textbook pattern documented in SQLite WAL-mode notes: long-lived read connections must commit transactions periodically (or be closed and reopened) to release the WAL snapshot. The standard FastAPI pattern is per-request connection lifetime — open the connection at the start of the request, close at the end — exactly to avoid this class of bug.

## Repo state

- **Repo:** `/home/racing/racing-data-capture` on VPS (`root@187.77.183.9`).
- **HEAD:** `5f71488006a1443021aefbc8a97e2a73d638c37c` ("Add /racing/results/today and /racing/results/{race_id} endpoints").
- **Working tree:** dirty. 11 modified + 7 untracked files (matches `current_state.md` "Open items" §16 baseline).

The API service code (`api/main.py`, `api/db.py`, `api/routes/*.py`) is entirely **untracked** — it's the operator's in-flight WIP. The fix lands inside files that are already part of the WIP §16 batch, not on tracked code.

## Files this brief touches

- **`api/db.py`** (untracked) — connection factory; needs adjustment to support per-request lifecycle.
- **`api/main.py`** (untracked) — lifespan handler; remove the singleton, add a dependency that yields per-request connections.
- **`api/routes/health.py`** (untracked) — switch from `request.app.state.db` to dependency injection.
- **`api/routes/races.py`** (untracked) — same.
- **`api/routes/snapshots.py`** (untracked) — same.
- **`api/routes/results.py`** (untracked) — same.

All six files are untracked; the fix lands cleanly inside the WIP §16 batch with no dirty-tree intersection on tracked code.

## Diff intersection assessment

**No conflict.** All edited files are untracked. The fix is internal to the WIP §16 API service work. No tracked files modified; no committed code modified.

## Hard-limits implications for the brief

- Edit only the named files per Session 36 pattern.
- Run `git status --short` before and after each edit to confirm the same six untracked files remain untracked, and no tracked file enters the modified-list as a side effect.
- No git mutation operations: no `add`, `commit`, `stash`, `restore`, `checkout` (file-targeted), `reset`.
- One service-restart cycle: stop `racing-capture.service`, restart `racing-api.service` (picks up code changes), checkpoint the WAL manually, verify, then restart `racing-capture.service`.

## Untouched files

The remaining modified files in WIP §16 (`betfair/client.py`, `betfair/models.py`, `bookmakers/*.py`, `capture/orchestrator.py`, `config/settings.py`, `matching/race_matcher.py`, `scripts/health_check.py`, `scripts/liveness_check.py`, `storage/database.py`) are not touched by this brief. The remaining untracked file (`bookmakers/tabtouch.py`) is also untouched.

## Operational urgency

Two days of race data are missing from `capture.db` and counting. Each Sunday Australian racing day is ~120-150 races across thoroughbred / harness / greyhound metros and provincials; that's the volume currently being silently dropped per day. Until this is fixed, the orchestrator's primary function (analytical-line capture) is non-operational.

This means the fix is operationally higher-priority than the BSP write-back fix it blocked, and the BSP fix verification window (post-fix) is itself dependent on this fix landing first.
