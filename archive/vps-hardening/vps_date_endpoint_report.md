# Report — VPS date-aware race discovery endpoint

**Brief:** `vps_date_endpoint_brief.md` — LOCKED v2, sha256 prefix `55395a7d` (verified at session start; matched).
**Status:** EXECUTED — endpoint live + verified.
**Session window (DR-021 Adelaide local, ACST = UTC+9:30):**
2026-06-30 09:27 → 09:30 ACST.
**Target:** `root@187.77.183.9` : `/home/racing/racing-data-capture`.
**Bet-safety:** CLEAN — only the read-only racing data API touched
(DR-033 analytical layer). No Betfair / settlement / money-movement /
lay / live-betting path. `capture.db` opened read-only throughout.

---

## 1 — What changed

One file edited: `api/routes/races.py` (untracked `??`). One import
added + one handler added + one marker comment. No other change. The
`/today` handler was confirmed to be a plain single-predicate query
(no extra WHERE / JOIN / status filter), so the mirror swaps only
`date('now')` → a bound parameter, per §5.3.

**Import addition (§5.5)** — grouped with stdlib, immediately after
`import sqlite3`:

    import sqlite3
    from datetime import date

**Handler added (verbatim, incl. the §5.7 marker)** — inserted
immediately before `@router.get("/{race_id}", ...)`:

    # [S204 Brief-1 v2] date-aware race discovery — added by Code
    @router.get("", response_model=list[RaceSummary])
    def races_by_date(
        race_date: date = Query(..., alias="date"),
        db: sqlite3.Connection = Depends(get_db),
    ):
        race_rows = db.execute(
            "SELECT * FROM races WHERE race_date = ? ORDER BY scheduled_start",
            (race_date.isoformat(),),
        ).fetchall()
        return _build_race_summaries(db, race_rows)

Resolved route: `GET /racing/races` (router `prefix="/racing/races"` +
empty path). `_build_race_summaries` and `Depends(get_db)` reused
unchanged. No `main.py`, model, `db.py`, or schema change. The handler
was applied via an anchored, uniqueness-checked patch (each anchor
asserted to occur exactly once) and the result passed `py_compile`
clean before the service restart.

**Method note:** edit applied by piping a Python patch script to the
VPS over `ssh … python3 -` (stdin) — no `scp`, no new repo file. An
off-repo rollback copy was taken first (§6.0):
`/tmp/races.py.s204-pre` (4053 bytes). No `.bak` was created inside the
repo tree.

---

## 2 — Pre/post verification table

All curls against `http://127.0.0.1:8400` on the VPS.

| Phase | Request | HTTP | Body / shape |
|-------|---------|------|--------------|
| PRE  | `GET /racing/races?date=2026-06-20` | **404** | no handler yet (expected) |
| POST | `GET /racing/races?date=2026-06-28` | **200** | 560 items; first = `{"id":2652331,"venue":"Healesville","race_number":1,"race_date":"2026-06-28","n_runners":0}` — RaceSummary shape intact |
| POST | `GET /racing/races?date=notadate` | **422** | FastAPI date validation (expected) |
| POST | `GET /racing/races` (no `date`) | **422** | required-param; **404 pre-edit → 422 post-edit** (finding #3) |
| POST | `GET /racing/races?date=2026-01-01` | **200** | populated (New Year's Day) — full list, shape correct |
| POST | `GET /racing/races?date=2020-01-01` | **200** | `[]` — empty pre-data date → `[]`+200 (§5.4 confirmed) |
| POST | `GET /racing/races/today` (regression) | **200** | unchanged |
| POST | `GET /racing/races/2652331` (regression) | **200** | known id, unchanged |
| POST | `GET /racing/races/upcoming` (regression) | **200** | unchanged |

**Data-pick context (read-only `mode=ro`):** populated past dates,
most recent first — `2026-06-28` (560), `06-27` (477), `06-26` (591),
`06-25` (504), `06-24` (436). `2026-06-28` chosen for the POST test.
Note: SQLite `date('now')` is UTC; VPS clock at PRE was
`2026-06-29 23:57Z`, so DB "today" = `2026-06-29` and `06-28` is the
most recent complete past date.

**Spot-check note:** the first `2026-06-28` item carries `n_runners:0`.
Not a failure — runner-row counts are sparse on some past races
(observation only; see §4). Near-zero `finish_position` on past dates
is expected per the brief (placings recovery gap, DR-033) and was not
treated as a fault.

**Service restart:** `systemctl restart racing-api.service` in a
confirmed quiet window — nearest upcoming start `2026-06-30T02:10Z`
(~2h12m out), 0 races within 10 min, `collector_active:false` (last
snapshot ~13h prior). Post-restart `Active (running) since
2026-06-29 23:59:18 UTC` = **2026-06-30 09:29:18 ACST**, PID 407837
(uvicorn). `racing-capture.service` not touched.

---

## 3 — Dirty-tree confirmation

`git -C /home/racing/racing-data-capture status --porcelain` — no git
operations were run (read-only `status` only). Counts identical
before and after the edit:

| | Modified `M` | Untracked `??` | `races.py` |
|---|---|---|---|
| BEFORE | 15 | 8 | `?? api/routes/races.py` |
| AFTER  | 15 | 8 | `?? api/routes/races.py` |

The full `M` set matched §9 exactly (api/main.py, api/routes/results.py,
betfair/client.py, betfair/models.py, bookmakers/base.py,
bookmakers/pointsbet.py, bookmakers/sportsbet.py,
capture/orchestrator.py, config/settings.py, matching/race_matcher.py,
scripts/backfill_race_metadata.py, scripts/health_check.py,
scripts/liveness_check.py, storage/database.py,
subscription/racing_api.py). The `??` set matched §9 (whole `api/`
package incl. the edit target, `bookmakers/tabtouch.py`,
`scripts/liveness_check.py.bak`). `races.py` remained untracked, so
`git diff` shows nothing for it — the edit was verified by re-reading
the file (the §5.7 marker + handler + `from datetime import date` are
present) and by `py_compile`, per §9. No drift into adjacent code; the
operator's in-flight tree is unchanged.

---

## 4 — Self-assessment

**Prefix pre-condition (§5.2 HARD GATE) — PASS.** `races.py:10` is
`router = APIRouter(prefix="/racing/races")`, with sibling routes
`@router.get("/upcoming")`, `@router.get("/today")`,
`@router.get("/{race_id}")`. The locked `@router.get("")` therefore
resolves at `GET /racing/races`, empirically confirmed by the 200 on
`?date=2026-06-28`. No silent path adaptation was needed.

**Bare-root 404 → 422 behaviour shift (finding #3) — confirmed and
intended.** Adding a required `date` query param means the bare root
`GET /racing/races` now returns 422 (was 404 when no handler existed).
The POST 422 was captured empirically; the PRE bare-root 404 is
inferred from the same absent-route condition (the PRE curl that was
explicitly captured used the `?date=2026-06-20` form, which 404'd —
the bare path shared that missing route). Honest caveat: I did not
separately curl the bare path *before* the edit, so the pre-edit 404
on the bare path specifically is inferred, not independently captured.
Low risk — nothing is known to depend on `/racing/races` returning 404,
and the client probes with `?date=`.

**Timezone basis (§7 probe → Brief-2 watch item, NOT resolved here).**
Stored formats, sampled verbatim (`ORDER BY scheduled_start DESC LIMIT
5`, past dates):

- `race_date` — bare calendar date, `YYYY-MM-DD`, no time, no zone.
  Sample value: `2026-06-28`.
- `scheduled_start` — full datetime, UTC, but **string format varies by
  source/era**: late-June rows use `…T10:09:00+00:00` (explicit
  offset); `2026-01-01` rows use `…T01:51:00.000Z` (`Z` + millis), with
  at least one `…T06:50:00.0000000Z` (7-digit fraction). All UTC, but
  not a single canonical string.
- **Off-by-one surface:** the sampled `race_date=2026-06-28` rows carry
  `scheduled_start=2026-06-29T08:10–10:09Z`. So `race_date` is **not**
  the UTC calendar date of `scheduled_start` (that would be `06-29`),
  **nor** the Adelaide-local date of it (`+9:30` also lands on `06-29`).
  `race_date` appears to follow the source feed's own meeting-date
  convention, decoupled from `scheduled_start`'s UTC instant. A Mac
  client computing "yesterday" in Adelaide local (DR-021) and querying
  `?date=` could mismatch the stored `race_date` near day boundaries.
  This is exactly finding #4 / §10 — **Brief 2 owns the resolution.**
  No normalisation or fix attempted here (observation only, per §7).

**Anchors / line numbers.** All brief-cited anchors matched the live
file pre-edit: `prefix` at line 10, `_build_race_summaries` 13–48,
`/today` 66–71, `/{race_id}` at 74, `Query` imported at line 5. No
anchor drift. (Post-edit those shift downward by the inserted lines —
expected from an additive insertion; `/{race_id}` now begins at line
88. Not drift, just the consequence of the add.)

**Quiet-window / collector.** `collector_active` was `false` for the
entire session (last Betfair snapshot `2026-06-29T10:12Z`, ~13h stale),
so the restart blip touched no live capture. `racing-capture.service`
was not restarted or inspected beyond confirming it is a separate unit.

**Anything else odd.** (1) `n_runners:0` on some past races (e.g.
Healesville R1, 2026-06-28) — runner-row population is incomplete for a
subset of past races; consistent with the brief's note that past-date
enrichment is partial. Surfaced as an observation, not a fault, and not
acted on. (2) Mixed `scheduled_start` string encodings (above) — a
second facet of the same Brief-2 datetime-basis question; flagged, not
touched.

**Scope adherence.** One file edited (`api/routes/races.py`), one
import + one handler + one marker, one `racing-api.service` restart, no
git operations, no schema/write/migration, no other endpoint, no
Brief-2 work. Single bounded session. The off-repo `/tmp` rollback copy
remains on the VPS for the operator; it is not a repo file.

---

*Report landing complete — this unblocks operator-Claude to confirm
the endpoint and draft Brief 2.*
