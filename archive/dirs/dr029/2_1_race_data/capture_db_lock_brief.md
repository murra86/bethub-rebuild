# DR-029 §2.1 follow-up — `capture.db` lock contention fix

**Brief lock date:** 2026-05-03 (Session 53). **Operator:** Tim. **Tool routing:** Claude Code, single bounded session.
**Output:** `dr029/2_1_race_data/capture_db_lock_report.md`.
**Pre-flight diagnostic:** `dr029/2_1_race_data/capture_db_lock_vps_drift_check.md`.

---

## §1 What this brief is and is not

This is a **surgical fix brief** to remediate `database is locked` errors blocking the orchestrator's race-discovery persist path on the VPS. Single bounded Code session.

**What it is:** a four-anchor change to the FastAPI service layer to use per-request SQLite connections instead of a singleton, plus a one-shot manual WAL checkpoint and service-restart cycle, plus empirical verification that newly-discovered races persist correctly post-fix.

**What it is not:** a redesign of the API service surface (routes, response shapes, authentication — all unchanged), a schema change to `capture.db`, an addition of new endpoints, a fix to any other VPS-side issue, an upgrade of FastAPI / uvicorn / SQLite versions, or any work on the BSP write-back fix (which was the originally-scoped Session 53 work and is paused pending this fix).

**Surprises become findings, not blockers.** If Code observes anything unexpected during the fix or verification (e.g. WAL checkpoint fails, post-fix persists still error, lock contention re-emerges from a different source), Code reports it in the named output file and stops. Operator-Claude triages in the next session.

---

## §2 Why this work exists

The orchestrator (`racing-capture.service`, PID 686 at brief drafting) has been failing to persist newly-discovered races since approximately 2026-05-01. `capture.db` contains zero rows in `races` for race_date 2026-05-02 (Saturday) or 2026-05-03 (Sunday). Each discovery cycle logs hundreds of `database is locked` errors against the persist path; discovery itself completes cleanly but every `INSERT` fails.

The mechanism is documented in `capture_db_lock_vps_drift_check.md`: the API service (`racing-api.service`, PID 685) holds a single long-lived read-only SQLite connection across the uvicorn process lifetime (since 2026-04-30). In SQLite WAL mode, a long-held read connection prevents the WAL file from checkpointing past the connection's read snapshot. The WAL has grown to 426 MB, and at certain points the orchestrator's `BEGIN IMMEDIATE` write attempts hit `database is locked` instead of waiting for a checkpoint that cannot run.

This was originally surfaced during pre-flight grounding for the BSP write-back fix brief — the BSP brief's verification window depends on new races settling post-restart, and no new races were entering the DB. Investigation traced the symptom to the API service's connection-handling pattern. The BSP brief is paused until this fix lands.

The fix is a textbook FastAPI pattern: per-request connection lifecycle via dependency injection. The connection opens at the start of each request and closes when the request returns. Long-lived reader snapshots vanish; WAL checkpoints run normally; orchestrator writes succeed.

---

## §3 Pre-reads

**Required reads (in order):**

1. `dr029/2_1_race_data/capture_db_lock_vps_drift_check.md` — captures the operational symptom, the mechanism, the dirty-tree state, and the diff-intersection assessment.
2. This brief in full.

**Reference-only (read on demand):**

- `standing_instructions.md` Category 3 (filesystem and tooling discipline) — covers VPS access patterns, dirty-tree handling, and the no-DB-file-copy rule.
- `dr029/dr029_scope.md` — DR-029 scope; §2.1 is the active item.
- FastAPI dependency-injection documentation — the canonical pattern Code is implementing. Code reads on demand if needed.

**Code anchors named in this brief:**

- `api/db.py` (full file, 28 lines) — connection factory.
- `api/main.py` (full file, 31 lines) — lifespan handler and app construction.
- `api/routes/health.py` (full file, ~46 lines) — uses `request.app.state.db`.
- `api/routes/races.py` (~150 lines, uses `request.app.state.db` throughout).
- `api/routes/snapshots.py` (uses `request.app.state.db`).
- `api/routes/results.py` (uses `request.app.state.db`).

All six files are **untracked** in the VPS git working tree.

---

## §4 System access

**Mode:** read-write on the VPS source tree, read-write on the VPS-side `capture.db` for verification queries (one manual WAL checkpoint command included; otherwise read-only). No bookmaker scrapers touched, no Betfair API calls.

**Filesystem:**

- VPS at `root@187.77.183.9`. Repo at `/home/racing/racing-data-capture`. Edits via direct file write. After every edit, `git status --short` is run to confirm the file remains untracked (no accidental tracked-file modification).
- Local Mac at `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/` for the output report. Code writes the report directly to this path via Desktop Commander.

**Database:**

- VPS `capture.db` at `/home/racing/racing-data-capture/data/capture.db`. Read-only for verification queries from Code's side. One manual `wal_checkpoint(TRUNCATE)` command is run as part of the fix sequence — that's a maintenance operation, not a data write. Per `standing_instructions.md` Cat 3: never copy the DB file (WAL not copied → stale data). All queries via `sqlite3` CLI or Python `sqlite3` module against the live file at the canonical path.

**Service control:**

- `racing-api.service` and `racing-capture.service` both run continuously at brief drafting. Code stops the orchestrator first (to remove the writer that's failing), restarts the API service (to load the new code and release the long-held connection), runs the WAL checkpoint, then restarts the orchestrator. Single restart cycle each; full sequence in §6.
- `journalctl -u racing-capture -f` and `journalctl -u racing-api -f` for log inspection during verification.

**Timestamps:** Adelaide local time (ACST/ACDT) per DR-021 (timestamp anchoring, Adelaide local time) for every time-of-day reference in the report. UTC timestamps from logs are converted to Adelaide local before reporting.

**Hard limits on git operations** (working tree is dirty per `capture_db_lock_vps_drift_check.md`):

- No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), `git reset`.
- `git status` and `git diff` are read-only and used freely.
- Session close: `git status --short` output should match the pre-flight (11 modified + 7 untracked, same files). The fix edits only files already in the untracked list; if the post-edit count diverges, that's a finding.


---

## §5 Substantive scope sections

Five scope items. Code executes them in the order written (sequencing rationale in §6).

### §5.1 — Connection factory: support per-request lifecycle

**Anchor:** `api/db.py` (full file, currently 28 lines).

**Current shape:** single `get_connection()` function returning a fresh connection. Used today as a singleton via `app.state.db`.

**Change:** keep `get_connection()` for explicit single-shot use, and add a generator-style dependency `get_db()` that yields a connection per-request and closes it on completion. FastAPI's dependency-injection system uses generator dependencies natively — the cleanup runs after the response is sent, even on exceptions.

**Suggested shape (Code adapts to existing style):**

```python
"""Read-only SQLite database access layer."""

import sqlite3
from collections.abc import Generator
from pathlib import Path

DB_PATH = Path("/home/racing/racing-data-capture/data/capture.db")


def get_connection() -> sqlite3.Connection:
    """Open a fresh read-only connection to capture.db."""
    conn = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: yields a per-request read-only connection.

    Opens a fresh connection at the start of each request and closes
    it when the response is sent. This pattern releases WAL snapshots
    promptly and avoids long-lived read locks that block writers from
    checkpointing the WAL.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    """Convert sqlite3.Row objects to plain dicts."""
    return [dict(row) for row in rows]


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a single sqlite3.Row to a dict, or None."""
    return dict(row) if row else None
```

**Rationale:** the per-request connection is the canonical FastAPI pattern for short-lived database access. Each connection lives for the duration of one HTTP request and closes when the response returns. SQLite WAL snapshots are released as soon as the connection closes, which means the WAL can be checkpointed after the request completes.

### §5.2 — App lifespan: drop the singleton

**Anchor:** `api/main.py` (full file, currently 31 lines).

**Current shape:** lifespan handler opens `app.state.db = get_connection()` at startup, closes at shutdown.

**Change:** remove the singleton. The lifespan handler still exists (FastAPI 0.95+ pattern) but only carries the `db_path` reference, which is needed by the `/health` endpoint for diagnostic output. No long-lived connection is held.

**Suggested shape (Code adapts to existing style):**

```python
"""Racing Data API — read-only HTTP layer over capture.db."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.db import DB_PATH
from api.routes import health, races, snapshots, results


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: store DB path for diagnostic endpoints.
    # No long-lived connections — per-request via api.db.get_db dependency.
    app.state.db_path = DB_PATH
    yield
    # Shutdown: nothing to release.


app = FastAPI(
    title="Racing Data API",
    version="1.0.0",
    description="Read-only API over VPS racing data capture database.",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(races.router)
app.include_router(snapshots.router)
app.include_router(results.router)
```

**Rationale:** removing the singleton is the load-bearing change. The lifespan handler shape stays similar so existing deployment hooks (systemd, log capture) continue to work without modification.

### §5.3 — Routes: switch to dependency injection

**Anchors:** `api/routes/health.py`, `api/routes/races.py`, `api/routes/snapshots.py`, `api/routes/results.py`.

**Current pattern (every endpoint):**

```python
def some_endpoint(request: Request, ...):
    db = request.app.state.db
    ...
```

**Change to:**

```python
from fastapi import Depends
from api.db import get_db

def some_endpoint(db: sqlite3.Connection = Depends(get_db), ...):
    ...
```

**Per-file mechanics:**

1. Add `from fastapi import Depends` (and `import sqlite3` if not present) at the top.
2. Add `from api.db import get_db` to the imports.
3. For every endpoint that currently extracts `db = request.app.state.db`, replace the `request: Request` parameter (if no longer needed for anything else) with `db: sqlite3.Connection = Depends(get_db)` and remove the `db = request.app.state.db` line.
4. Where `request` is still needed (e.g. `request.app.state.db_path` in the health endpoint), keep `request: Request` alongside the new `db` parameter.

**Important detail for the health endpoint:** `request.app.state.db_path` is still used and should remain. Only the connection access changes.

**Verification (after each file's edit):**
- `python3 -c "import ast; ast.parse(open('api/routes/<filename>.py').read())"` — confirms the file still parses.
- `git status --short api/routes/<filename>.py` — confirms it remains untracked (`??` prefix), not promoted to modified.

### §5.4 — Service restart cycle and WAL checkpoint

This is an operational sequence, not a code edit. Run after §5.1, §5.2, and §5.3 are complete.

**Sequence (in order):**

1. **Stop the orchestrator** so it stops trying to write while we restart the API service:
   ```
   sudo systemctl stop racing-capture.service
   ```
   Verify with `sudo systemctl status racing-capture` → `inactive (dead)`.

2. **Restart the API service** to load the new code and release the long-held connection:
   ```
   sudo systemctl restart racing-api.service
   ```
   Wait 5 seconds. Verify with `sudo systemctl status racing-api` → `active (running)` with new start timestamp. Verify with `sudo lsof /home/racing/racing-data-capture/data/capture.db` → no `racing` user uvicorn entry should remain (or if one exists, it should have a fresh PID corresponding to the new process, with no active FD on the DB at idle — only present briefly during in-flight requests).

3. **Manually checkpoint the WAL** to reclaim the 426 MB. With no readers holding snapshots, this should run cleanly:
   ```
   sqlite3 /home/racing/racing-data-capture/data/capture.db "PRAGMA wal_checkpoint(TRUNCATE);"
   ```
   Capture the output. The expected return is `0|N|N` where N is the number of pages checkpointed (a non-zero number, possibly large). After the command, the WAL file should shrink to a few MB or zero bytes.

4. **Verify WAL state:**
   ```
   ls -la /home/racing/racing-data-capture/data/
   ```
   `capture.db-wal` should now be small (under 10 MB; ideally near zero).

5. **Restart the orchestrator:**
   ```
   sudo systemctl start racing-capture.service
   ```
   Verify with `sudo systemctl status racing-capture` → `active (running)` with new start timestamp.

6. **Watch the orchestrator's next discovery cycle:**
   ```
   sudo journalctl -u racing-capture -f
   ```
   Wait for the next `Discovery complete: N new races, M total active` log line. Expected: a non-zero `N new races` count, no `database is locked` errors anywhere in the cycle.

### §5.5 — Empirical verification

**Pre-fix baseline** (run before any edit, capture in report):

```sql
-- Most recent race_date persisted to capture.db
SELECT race_date, COUNT(*) AS n_races
FROM races
GROUP BY race_date
ORDER BY race_date DESC
LIMIT 7;

-- Counts of orphan-style errors in last 6 hours of orchestrator logs
-- (Code runs this via journalctl + grep, not SQL)
```

```bash
sudo journalctl -u racing-capture --since '6 hours ago' --no-pager | grep -c 'database is locked'
sudo journalctl -u racing-capture --since '6 hours ago' --no-pager | grep -c 'Discovery complete'
```

Expected pre-fix: most recent `race_date` is `2026-05-01` or earlier; non-zero `database is locked` count; non-zero `Discovery complete` count (discovery is firing but persists are failing).

**Post-fix verification** (after the §5.4 sequence completes):

```sql
-- Re-run the most-recent-race_date query
SELECT race_date, COUNT(*) AS n_races
FROM races
GROUP BY race_date
ORDER BY race_date DESC
LIMIT 7;
```

```bash
# Check the post-restart orchestrator log for clean discovery
sudo journalctl -u racing-capture --since '<orchestrator restart timestamp>' --no-pager | grep -E 'Discovery complete|database is locked'
```

Expected post-fix:
- `race_date` shows current Adelaide-local date (`2026-05-03`) and yesterday (`2026-05-02`) with non-zero `n_races` counts. May take one or two discovery cycles after the restart to fully populate the next two days' cards.
- Zero `database is locked` errors in the post-restart log.
- One or more clean `Discovery complete: N new races, M total active` lines with `N > 0`.

**Optional probe** (Code may run if budget allows, not required):

```bash
# Hit one or two API endpoints to confirm per-request connection lifecycle works
curl -s http://127.0.0.1:8400/health | head -c 500
curl -s 'http://127.0.0.1:8400/racing/races/upcoming?hours=4' | head -c 500
```

Expected: 200 OK with valid JSON. After each request, a `lsof` check on `capture.db` should show only PID 686 (the orchestrator) holding the file at idle — the uvicorn process should not show a sustained read FD against the DB outside of in-flight request handling.


---

## §6 Sequencing within session

Code executes the substantive scope items in this order:

1. **Pre-fix baseline first.** Capture the current symptom state (most recent `race_date` in `capture.db`, counts of `database is locked` errors and `Discovery complete` log lines in the last 6 hours, current WAL size). Establishes the counterfactual.

2. **Read-only inspection of all six files** (§5.1, §5.2, §5.3 anchors). Confirm structure matches the brief's expectations before editing. If any file is structurally different (e.g. routes already partially refactored, additional endpoints not listed in §3 pre-reads), surface as a finding before editing.

3. **§5.1 edit** — `api/db.py`. Smallest unit; gets the `get_db()` dependency landed first. Verify with file parse + `git status` post-edit.

4. **§5.2 edit** — `api/main.py`. Drops the singleton. Same verification.

5. **§5.3 edits** — four route files in order: `health.py`, `races.py`, `snapshots.py`, `results.py`. After each file, parse-check + `git status` check. Doing them in this order means the smallest file (`health.py`) lands first as a shape-check; if the dependency-injection pattern isn't quite right, it surfaces on the smallest-blast-radius file.

6. **§5.4 service-restart cycle and WAL checkpoint.** All six files complete and verified before this step.

7. **§5.5 post-fix verification.**

8. **Report write-up** per §8.

**Why this order:** the baseline must be captured before edits (loses counterfactual otherwise). Reading the six files before editing surfaces structural mismatches early. The edits land in size order so any pattern-shape problem surfaces on the smallest file first. The service-restart cycle waits until all code is in place — restarting the API service before all routes are converted would fail at runtime when a route still tries to access `request.app.state.db`.

**Code may deviate from this order if a different sequence is operationally cleaner**, with one constraint: the service-restart cycle must come after all six files are edited and verified, never partially.

---

## §7 Empirical verification (success/failure criteria)

**Success criteria (all must hold):**

1. **Pre-fix baseline captured.** Most recent `race_date` is May 1 or earlier; `database is locked` errors observed in the last-6-hours orchestrator log; current WAL size confirmed at ~400+ MB.
2. **All six files edited cleanly.** Each file remains untracked post-edit (`?? ` prefix in `git status --short`). No tracked file modified as a side effect. All six files parse via `ast.parse()`.
3. **Service-restart cycle completed.** API service restarted, orchestrator stopped and restarted, WAL checkpoint ran with non-zero pages reclaimed, both services show `active (running)` post-cycle.
4. **WAL reclaimed.** `capture.db-wal` post-checkpoint is small (under 10 MB; ideally near zero).
5. **New races persisting.** Post-restart `journalctl` shows at least one `Discovery complete: N new races, M total active` with `N > 0` and zero `database is locked` errors. Most-recent-race_date query shows today's date or yesterday's with non-zero `n_races`.

**Partial-success state (acceptable, reported):**

- Edits land cleanly, services restart, WAL reclaims — but the next discovery cycle hasn't fired yet within the session budget. Report the partial state with the orchestrator restart timestamp; operator-Claude verifies in a follow-up by re-running the post-fix queries.
- `N new races` count in first post-restart cycle is small (e.g. 5-20) rather than the expected hundreds — could indicate the upstream race-discovery source hasn't published Sunday's full card yet. Note in report; not a fix failure.

**Failure states (each gets its own finding):**

- Pre-fix baseline shows races persisting normally — the brief's premise is wrong. Stop without editing, surface to operator-Claude.
- Any of the six files structurally diverges from the brief's expectations during §6 step 2 inspection. Stop, surface, do not edit.
- Edit causes a tracked file to enter the modified-list (e.g. an import auto-formatter ran). Surface immediately, do not proceed to next file.
- API service restart fails (systemctl error, exception trace in startup log). Stop, do not run WAL checkpoint or restart orchestrator. Surface.
- WAL checkpoint command fails or returns busy state (would indicate a lingering reader). Stop, do not restart orchestrator. Surface — there's another reader Code didn't know about.
- Post-restart orchestrator continues to log `database is locked` errors. Indicates the fix didn't resolve the contention; there's another mechanism. Surface immediately.

**What the report captures regardless of outcome:**

- Pre-fix baseline (race_date query result, journalctl error counts, WAL size).
- File-by-file edit confirmation (`git status --short` per file, parse-check pass).
- Service-restart timestamps (Adelaide local + UTC) for both `racing-api.service` and `racing-capture.service`.
- WAL checkpoint command output and post-checkpoint WAL size.
- Post-restart `Discovery complete` and `database is locked` log line counts.
- Post-fix race_date query result.
- Final `git status --short` matching the pre-flight state (11 modified + 7 untracked, same files).

---

## §8 Output spec

**Single output file:** `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/capture_db_lock_report.md`

Code writes directly via Desktop Commander (`Desktop Commander:write_file` or equivalent). Verify post-write via `read_file` with line count + spot-check on the verification-results section.

**Section structure:**

1. **§1 Execution summary** — start/end Adelaide-local timestamps, Code session wall-clock, both service-restart timestamps, WAL pre/post sizes, summary of outcome (success / partial-success / failure with brief noun-phrase).
2. **§2 Pre-fix baseline** — race_date query result, journalctl error counts (last 6 hours), WAL size, full `lsof` output.
3. **§3 File inspection results** — for each of the six files, whether structure matched the brief's expectations. Flag any structural differences as findings (§7) without fixing them.
4. **§4 Edits** — for each file, the diff or final content (whichever Code judges more compact for the report), `git status --short` showing the file remains untracked, parse-check pass.
5. **§5 Service-restart cycle** — full sequence with timestamps and command outputs (systemctl status, lsof, WAL checkpoint result).
6. **§6 Post-fix verification** — race_date query post-restart, journalctl excerpt showing first `Discovery complete` line with `N > 0` and zero lock errors, post-restart WAL size, optional curl probe results if Code ran them.
7. **§7 Findings** — anything observed that wasn't anticipated by the brief. Lettered (a), (b), (c). Empty section is acceptable; named explicitly with "no surprises observed" if so.
8. **§8 Self-assessment** — did the five success criteria hold; what's uncertain / under-covered; dirty-tree discipline confirmation (final `git status --short` matching the pre-flight diff list).

**What the report does not contain:**

- No recommendations on follow-up work. The next steps are operator-Claude triaging; the BSP write-back fix re-activating; possibly a connection-health-check addition. None of those are this report's job.
- No fixes to anything beyond the named anchors.
- No commentary on Fix 4 cadence design, §2.10 field inventory, or BSP write-back. Out of scope.
- No retroactive backfill of missing race data for May 2 / May 3. Once persists are working again, the orchestrator's next discovery cycle picks up today's card; yesterday's (Saturday) is gone permanently. That's a finding for operator-Claude triage, not a fix.

**Length anticipation:** 200-350 lines. The report covers six file edits + a service-restart cycle + verification, but each unit is small. If heading toward 450+ lines, that's a signal of over-production — flag in self-assessment.

---

## §9 Hard limits

Non-negotiable list. Code does not do any of the following.

**Scope creep into other §2.1 / DR-029 work:**

- No work on the BSP write-back fix. That brief is paused pending this fix; Code does not touch `betfair/client.py` `get_market_book_sp_traded()`, `capture/orchestrator.py` settlement-handler, or `storage/database.py` `update_final_snapshot_bsp()`.
- No cadence work, no §2.10 field-inventory work, no §2.5 soft-book contract work.
- No retroactive backfill of any missing data.

**Schema and data:**

- No `ALTER TABLE`, `CREATE INDEX`, `CREATE TABLE`, or any DDL on `capture.db`.
- No `INSERT`, `UPDATE`, `DELETE` on any table. (The WAL checkpoint command is maintenance, not data.)
- No data migration, no row-level fixes, no re-import of missing race data.

**Service control:**

- Exactly one stop+start cycle on the orchestrator, exactly one restart on the API service. No additional service lifecycle commands beyond what §5.4 specifies.
- No changes to systemd unit files (`/etc/systemd/system/racing-*.service`).
- No `systemctl daemon-reload`, `enable`, `disable`, `mask`.
- No reboot of the VPS.

**Code drift:**

- Edit only the six files named in §5. No edits to other API files (e.g. `api/models.py`), no edits to scrapers, orchestrator, storage layer, betfair client, or anything else in the repo.
- No formatting passes (no `black`, `ruff format`, `isort`) on the edited files. Match the surrounding style by hand.
- No new dependencies. The fix uses only what's already in the project's `requirements.txt` / `venv` (FastAPI's `Depends`, `sqlite3` stdlib, `collections.abc.Generator` stdlib).

**Git operations** (working tree dirty per `capture_db_lock_vps_drift_check.md`):

- No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), `git reset`.
- `git status` and `git diff` are read-only and used freely.
- Final `git status --short` must match the pre-flight diff list (11 modified + 7 untracked, same files). Divergence is a finding.

**Mid-session operator escalation:**

- Code runs end-to-end without checking in. Findings, surprises, partial-success states all get reported in the output file at session close.
- Single bail-out exception: if pre-fix baseline shows races persisting normally (brief's premise is wrong) OR if any of the six files structurally diverges from the brief during inspection, Code stops without editing and writes a short report describing the unexpected state. No edits, no restart, no checkpoint. This is the one bail-out path.

**Single bounded session:**

- This is one Code session. If the post-restart verification window doesn't deliver a clean `Discovery complete: N > 0 new races` within the session budget, Code reports the partial-success state and stops. No "let's wait another hour" — partial result is reported and operator-Claude takes the next step in a fresh session.

---

## §10 What happens after Code's session

Code's session ends with the report at `dr029/2_1_race_data/capture_db_lock_report.md` written and verified. Operator hands the report to the next operator-Claude Chat session.

**Next operator-Claude session triage:**

1. Read the report in full.
2. Confirm the five success criteria hold (§7). If yes, the lock-contention fix is closed.
3. Re-activate the BSP write-back brief (paused mid-§9 of `bsp_writeback_brief` — needs to be lifted off pause and locked for execution).
4. Surface findings (§7 in the report) for routing — likely candidates: the missing-Saturday-data state (operator-side; data is gone, decide whether to note or move on), any unexpected behaviour observed during file inspection, any post-fix lock-contention re-emergence (would indicate a deeper issue).
5. Optional follow-up brief candidates (operator decides whether to scope):
   - Add a connection-health metric to the orchestrator's existing logging (early-warning if WAL grows past a threshold).
   - Add a periodic WAL-checkpoint cron (defensive against future similar bugs).
   - Add a smoke test for the API service that exercises a route and confirms the connection closes.

**Code does not produce the next brief.** The BSP write-back brief is mostly drafted in operator-Claude's working state from Session 53; lifting it off pause and locking it is operator-Claude's next-session work.

**The §2.1 surgical-fix arc close path** (visible after this fix lands, then the BSP fix lands):

- BSP write-back fix — lifts off pause once this fix verifies.
- Fix 4 cadence brief — drafted post-BSP-fix-close.
- §2.1 close-out governance paragraph — covers periodic data-fitness re-verification and the three named pieces of debt (no test coverage, no migration framework, monolithic orchestrator file).

---

## §11 Cross-references

**Scope doc item:** DR-029 §2.1 (race-side data fit-for-purpose verification). The lock contention is operationally upstream of the BSP write-back fix; resolving it unblocks BSP verification and unblocks the orchestrator's primary capture function.

**Decision Records invoked:**

- DR-029 (the data-layer fit-for-purpose review before v3 build) — active gating arc.
- DR-027 (the two-database architecture: BetHub owns operational state, capture.db owns analytical/source data) — `capture.db` is the analytical store this brief remediates.
- DR-028 (the cross-database integration boundary discipline: no caching, no denormalisation, no second integration point) — this brief touches only the analytical line; no cross-DB coupling introduced or modified.
- DR-021 (timestamp anchoring, Adelaide local time) — applies to all timestamps in the report.

**Prior reports / briefs / artefacts this builds on:**

- `dr029/2_1_race_data/capture_db_lock_vps_drift_check.md` (this session, pre-flight) — operational symptom, mechanism, dirty-tree state, files-touched assessment.
- `dr029/2_1_race_data/api_probe_report.md` (Session 52) — produced the Saturday probe data; the BSP write-back fix that surfaced this lock-contention issue grew out of the probe findings.
- `current_state.md` "Open items" §16 — names the WIP §16 in-flight VPS work; the API service code edited by this brief is part of that batch.

**Parking-lot items this brief excludes** (named so Code knows they're not its job):

- BSP write-back fix (paused).
- Fix 4 cadence design.
- §2.10 external analytics field inventory.
- §2.5 soft-book interface contract.
- Retroactive backfill of missing race data for May 2 / May 3.
- Connection-health metric, periodic WAL checkpoint cron, API smoke test (all optional follow-ups, operator-decided).
- EX_LADDER entitlement upgrade question.
- Any work on tracked code (committed files).

---

*End of brief.*
