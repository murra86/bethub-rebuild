# Brief — VPS date-aware race discovery endpoint

**File:** `vps_date_endpoint_brief.md`
**Status:** LOCKED
**Version:** v2 — re-locked S204 post-review (supersedes v1)
**Supersedes:** v1 — sha256 prefix `4c291d52`, anchored
2026-06-30 08:41 ACST
**Anchored:** 2026-06-30 09:11 ACST (DR-021 Adelaide)
**Sequence:** Brief 1 of 2 (launcher capture-data provisioning execution)
**Bet-safety:** CLEAN — read-only racing data API (DR-033 analytical
layer). No Betfair, settlement, money-movement, lay-placement, or
live-betting path touched.

---

## §1 — What this brief is and is not

A surgical **additive** change: one new read-only endpoint on the VPS
racing API. Single bounded Code session. The endpoint shape is
**locked** below — no design exploration. Surprises become **findings**
in the report, not blockers, and not mid-session pings to
operator-Claude. Any remediation beyond the named change routes to
operator-Claude triage, never Code's report.

## §2 — Why this work exists

Log Past Bet is broken: the launcher never wires a capture-DB path and
the reader is file-only (investigation §A). The S202-locked fix path =
Option B (API-backed read) **plus** a date-aware discovery endpoint,
because the live `:8400` API is **today-only** and cannot serve
past-date lookup (investigation C-1). This is **Brief 1 of 2**. Brief 2
(the Mac `vps_client` rewrite) is dead without it — it would have no
past-date source to point at.

A read-only data check (2026-06-30, operator-Claude) confirmed the
endpoint lands on real data: `races` spans 2025-03-03 → 2026-06-29
(90,306 races); past dates carry Betfair selection IDs (62–89%) and
win/lose (`result_status`) at matching rates. `finish_position` is
sparse on past dates — **expected** (the placings recovery backfills it;
placings are manual per DR-033).

## §3 — Pre-reads (lean)

Required:
- this brief
- `api/routes/races.py` (the mirror target) — read the
  `APIRouter(prefix=...)` declaration and every route decorator (§5.2
  pre-condition depends on this)
- `api/db.py` (the `get_db` dependency)
- `api/models.py` (`RaceSummary` — the response model)

Reference-only (read on demand):
- `launcher_capture_provisioning_investigation_report.md` — §3 endpoint
  map, C-1 past-date gap
- `launcher_capture_provisioning_brief.md` — the locked path

## §4 — System access

VPS via SSH: `root@187.77.183.9`. Repo: `/home/racing/racing-data-capture`.
- **READ-WRITE to ONE file:** `api/routes/races.py`.
- **capture.db: READ-ONLY** (`mode=ro` via `get_db`). No schema change,
  no writes, no migration.
- **Service:** restart `racing-api.service` ONLY. Do **not** touch
  `racing-capture.service` (separate unit — the collector).
- All report timestamps Adelaide local (ACST/ACDT) per DR-021.

## §5 — The change (LOCKED)

**5.1 Endpoint:** `GET /racing/races?date=YYYY-MM-DD` → `list[RaceSummary]`
(same model as `/today`).

**5.2 Handler** — new function in `api/routes/races.py`, declared
**before** `@router.get("/{race_id}")` (line 74). Keep this ordering as
a positional convention, but note it is **belt-and-suspenders, not a
correctness requirement**: an empty-path route cannot satisfy a path
parameter, so it cannot collide with `/{race_id}` regardless of
declaration order. (v1 said the ordering made match-order
"unambiguous" — that imported the rejected path-param design's
collision risk into this design; corrected here.)

**PREFIX PRE-CONDITION — confirm before editing (review finding #1):**
the locked path `@router.get("")` is correct **only if** the router
prefix is exactly `/racing/races`. Confirm during the §3 pre-read of
`races.py`:
- If prefix is `/racing/races` with routes `@router.get("/today")`,
  `@router.get("/{race_id}")`, `@router.get("/upcoming")` → `""`
  resolves at `GET /racing/races`. **Proceed.**
- If the prefix is anything else (e.g. `/racing` with routes written as
  `@router.get("/races/today")`), then `""` resolves to the WRONG
  endpoint — and so would `@router.get("/")`. **This is a §1 surprise:
  STOP and report the actual prefix + route shape as a finding. Do NOT
  silently adapt the path.**

Path (locked, pending the pre-condition above):

    @router.get("", response_model=list[RaceSummary])
    def races_by_date(
        race_date: date = Query(..., alias="date"),
        db: sqlite3.Connection = Depends(get_db),
    ):

- Param named `race_date` (NOT `date`) to avoid shadowing the type;
  `alias="date"` keeps the query key `?date=`.
- FastAPI validates `YYYY-MM-DD` → malformed yields 422.
- Confirm the resolved path with the §7 curl. If `""` does not register
  at `GET /racing/races` **despite the correct prefix**, that too is a
  §1 surprise → report it; do **not** switch to `@router.get("/")` (the
  client probes without a trailing slash; `/` would force a 307).

**5.3 SQL** — copy the `/today` handler's query **verbatim** (lines
66–71), changing only the date binding (`date('now')` → bound param).
The skeleton below is **illustrative, not authoritative**: if the live
`/today` handler carries extra predicates, a status filter, or a JOIN,
copy them exactly. The live handler is the source of truth — past-date
results must match today's in shape and inclusion.

    SELECT * FROM races WHERE race_date = ? ORDER BY scheduled_start

param: `(race_date.isoformat(),)`. Reuse `_build_race_summaries(db,
race_rows)` (lines 13–48) **unchanged**. Reuse `Depends(get_db)`
**unchanged**.

**5.4 Empty result:** a date with no races returns `[]` + 200 (NOT 404)
— matches `/today` semantics; the client reads empty as "no meetings."

**5.5 Single permitted import addition:** `from datetime import date`
near the top of `races.py`. `Query` is already imported (line 5). No
other imports.

**5.6** NO `main.py` edit — `races.router` is already registered
(`main.py:28`). NO new model. NO `db.py` change. NO capture-window logic.

**5.7 Locate-the-change marker (untracked-file safety, finding #7):**
`races.py` is untracked (`??`), so `git diff` shows nothing for it. Add
one comment line immediately above the new handler so the operator can
find Code's addition inside the in-flight file:

    # [S204 Brief-1 v2] date-aware race discovery — added by Code

**Rejected alternative (do NOT build):** `/racing/races/by-date/{date}`
path-param form — collides with `/{race_id}` int coercion (422) unless
ordered carefully. Query-on-root is cleaner and is the shape the client
already probes.

## §6 — Sequencing within session

0. (Optional safety net, finding #7) Copy `races.py` to an **off-repo**
   scratch path before editing — e.g.
   `cp api/routes/races.py /tmp/races.py.s204-pre` — as a manual
   rollback source. This is NOT a repo edit and is within §9 limits.
   The Edit tool also forces a Read-first, an implicit in-session
   snapshot.
1. Read working-tree state (`git status`) — confirm the dirty set
   matches §9.
2. Confirm the §5.2 prefix pre-condition during the `races.py`
   pre-read. If it fails → STOP and report; do not edit.
3. Add the handler + the one import (§5.5) + the §5.7 marker.
4. `systemctl restart racing-api.service` — run in a **quiet window,
   not mid-race**. The restart drops the API for a few seconds;
   `/today`, `/results`, `/upcoming` consumers blink. Nothing on the
   money path consumes this API (DR-033), so it is safe — but avoid an
   active race window.
5. Run §7 verification.

One file, one restart. If the work doesn't fit one session, that's a
finding — stop and report, don't continue.

## §7 — Empirical verification (pre + post)

**PRE (before edit):**

    curl -s -o /dev/null -w "%{http_code}\n" \
      'http://127.0.0.1:8400/racing/races?date=2026-06-20'

→ expect 404 (no handler yet). Capture it.

**Pick a populated past date** (read-only, `mode=ro`):

    SELECT race_date, COUNT(*) FROM races
    WHERE race_date < date('now')
    GROUP BY race_date ORDER BY race_date DESC LIMIT 5;

**Timezone-basis probe** (read-only — finding #4, de-risks Brief 2):
sample raw `race_date` + `scheduled_start` together and report their
stored format verbatim —

    SELECT race_date, scheduled_start FROM races
    WHERE race_date < date('now')
    ORDER BY scheduled_start DESC LIMIT 5;

Report in §8: is `race_date` a bare `YYYY-MM-DD` or a datetime? Does
`scheduled_start` carry a timezone / look UTC or local? **Observation
only — do NOT normalise or fix anything.**

**POST (after restart):**
- curl the chosen past date → 200 + non-empty JSON list; spot-check one
  item carries `id`, `venue`, `race_number`, `race_date`, `n_runners`
  (`RaceSummary` shape).
- curl `?date=notadate` → 422.
- **Bare-root** `curl '.../racing/races'` (NO `date` param) → 422
  (required-param). This is a **behaviour change**: the bare root
  returned 404 pre-edit, returns 422 post-edit. Record both (finding
  #3).
- Regression smoke — still 200 and correct: `/racing/races/today`,
  `/racing/races/{a known id}`, `/racing/races/upcoming`.

Capture every curl + status code in the report table. **Note:**
near-zero `finish_position` on the chosen date is **expected** (placings
gap, deferred to the recovery) — do not flag it as a failure.

## §8 — Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/vps_date_endpoint_report.md`
Sections:
1. What changed (the added handler, verbatim, incl. the §5.7 marker)
2. Pre/post verification table (curl + codes + shapes), incl. the
   bare-root 404→422 line
3. Dirty-tree confirmation (`git status` before/after)
4. Self-assessment — must include:
   - the router prefix actually found (§5.2 pre-condition outcome)
   - the bare-root 404→422 behaviour shift, called out explicitly
   - the `race_date` / `scheduled_start` timezone basis (§7 probe) as a
     **Brief-2 watch item** — do NOT resolve it here
   - any anchors that drifted; anything else odd

Length ~150–300 lines. Does NOT contain: Brief-2 work, other endpoints,
recommendations beyond findings.

## §9 — Hard limits (non-negotiable)

- Edit **ONLY** `api/routes/races.py`, **ONLY** the new handler + the one
  import (§5.5) + the §5.7 marker. No drift into adjacent code.
- **NO other endpoints** (no results-by-date, no meetings, no resolve).
  The client groups/filters client-side; results come via existing
  `/racing/results/{race_id}`.
- **NO** capture.db schema change, **NO** writes, **NO** migration.
- **NO git operations whatsoever:** no `add` / `commit` / `stash` /
  `restore` / `checkout` / `reset`. The dirty tree is the operator's
  pre-existing in-flight VPS work, **not** drift:
  - Modified (M): `api/main.py`, `api/routes/results.py`, `betfair/*`,
    `bookmakers/*`, `capture/orchestrator.py`, `config/settings.py`,
    `matching/race_matcher.py`, `scripts/*`, `storage/database.py`,
    `subscription/racing_api.py` (15 files).
  - Untracked (??): the whole `api/` package incl. the edit target
    `api/routes/races.py`, plus `bookmakers/tabtouch.py`, a `.bak` file.
  - **NOTE:** `races.py` is UNTRACKED → `git diff` shows nothing for it.
    Verify the edit by **re-reading the file** and confirming
    `git status` still lists `races.py` as `??` and the rest of the
    dirty set is unchanged.
- The §6.0 off-repo scratch copy (`/tmp/...`) is **permitted** — it is
  not a repo file. Do **NOT** create any new `.bak` file inside the repo
  tree.
- **NO** touching `racing-capture.service`, the collector, the scrapers,
  or any service other than a `racing-api.service` restart.
- **NO** Brief-2 work (the Mac `vps_client` rewrite).
- Single bounded session.

## §10 — What happens after Code's session

Operator-Claude reads `vps_date_endpoint_report.md`, confirms the
endpoint is live + verified, then drafts **Brief 2** (Mac `vps_client`
API rewrite + the launcher fixes). Code does **not** write Brief 2.

**Carry into Brief 2 (finding #4):** before Brief 2's Mac client
computes "yesterday" in Adelaide local time (DR-021), it must resolve
how `race_date` is stored on the VPS (UTC / feed-local / Adelaide).
`/today` uses SQLite `date('now')` (UTC), which hints the stored basis
may not be Adelaide-aligned — a near-midnight off-by-one is the most
likely downstream integration failure. The §7 probe feeds this; Brief 2
owns the resolution.

## §11 — Cross-references

- **Path:** `launcher_capture_provisioning_brief.md` (LOCKED);
  investigation report §3 (endpoint map), C-1 (past-date gap), §B
  correction (picker = `/racing/races/{id}`).
- **Review (S204):** v2 folds in the pre-execution brief review —
  finding #1 (prefix contingency → §5.2 pre-condition), #2 (copy
  `/today`'s full predicate → §5.3), #3 (bare-root 404→422 → §7/§8),
  #4 (date-semantics carry → §7 probe + §10), #5 (ordering rationale
  corrected → §5.2), #7 (untracked-file safety → §5.7/§6.0), #8
  (restart timing → §6.4). Review finding #6 (report path
  bethub-rebuild vs bethub-v2) assessed as a **false positive** —
  `bethub-rebuild/` is the live project root.
- **DRs:** DR-033 (racing data = analytical/enrichment layer — this
  endpoint lives there), DR-028 (single integration boundary; API read
  by reference), DR-027 (two-DB), DR-021 (Adelaide anchors).
- **Excludes:** Brief 2; all parking-lot items.
