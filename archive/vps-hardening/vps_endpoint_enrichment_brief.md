# VPS racing-API enrichment — brief (Brief 1.1)

**Status:** LOCKED — 2026-06-30 10:34 ACST (Session 205). Contract;
Code executes against it as written. §12 resolved: operator delegated
the call ("go with what you think best") — proceeding surgically now,
VPS git hygiene carried as tracked debt (§4 no-git limits apply).
**Drafted:** 2026-06-30 10:19 ACST (Session 205, DR-021 Adelaide anchor).
**Grounding:** live read-only inspection of the VPS API source at
`/home/racing/racing-data-capture/api/` (routes + models), the live
`GET /racing/races?date=` payload, and `git status` of the
`racing-data-capture` repo. All findings empirical, this session.
**Governing DRs:** DR-028 (single integration boundary — one defined
interface, no caching/denormalisation), DR-027 (two-DB), DR-033
(placings analytical / settlement Betfair-only), DR-021 (Adelaide
anchors).
**Bet-safety:** analytical / read-path only. Adds read fields and a
read lookup to the racing API. No settlement, money-movement, lay, or
live-betting write path is touched.

---

## 1. What this brief is and is not

A **surgical VPS-side addition**, single bounded Code session. It closes
the two real gaps between what the Mac `vps_client` (Brief 2) needs and
what the racing API returns today:

1. the race-list summary omits `betfair_win_market_id`;
2. there is no results lookup keyed on `betfair_win_market_id`.

- Surprises become **findings in the report**, not silent fixes.
- This is one Code session. Over-budget → stop and report, do not
  continue.

**It is NOT:** a Mac-client change (that is Brief 2); a schema change;
any change to the capture/scraper, betfair, bookmaker, orchestrator,
storage, or scripts modules (all of which are carrying unrelated
uncommitted work — see §4 and §12); a new capture endpoint beyond the
two named; an auth change.

**Grounding correction (material).** The premise that the date endpoint
was "too thin" is mostly false. The live `RaceSummary` already returns
`scheduled_start` (Candidate B's refine field) and `state`. Only
`betfair_win_market_id` is genuinely absent from the list. The results
*payload* is already complete; only a market-id *lookup key* is missing.
This brief is therefore far smaller than the Brief 2 draft anticipated,
and Brief 2's "no-Brief-1.1 fallback" fan-out logic largely dissolves
when it re-locks.

---

## 2. Why this work exists

Brief 2 re-points the Mac Log-Past-Bet lookup surfaces at this API. Two
things it needs that the API does not yet give:

- **`betfair_win_market_id` on the list summary** — the loggability
  stamp / `event_id`, so the picker carries it without an N-call
  per-race detail fan-out. (`scheduled_start` + `state`, the other two
  fields the draft thought were missing, are already present — confirmed
  on the wire this session.)
- **Results keyed on `betfair_win_market_id`** — the client keys results
  on `event_id` (= win_market_id); the live results route is keyed only
  on internal `race_id`, and nothing maps win_market_id → race_id.

Closing both on the VPS keeps the Mac client lean and is the DR-028
single-boundary shape (the interface carries what the consumer needs).

---

## 3. Pre-reads

**Required (read before editing):**
- `/Users/tim/Desktop/Projects/bethub-rebuild/vps_endpoint_enrichment_brief.md`
  (this brief).
- `/home/racing/racing-data-capture/api/models.py`
  (`RaceSummary`, `RaceResultDetail`, `RunnerResult`).
- `/home/racing/racing-data-capture/api/routes/races.py`
  (`_build_race_summaries` ~L14–49; `races_by_date` ~L76–85).
- `/home/racing/racing-data-capture/api/routes/results.py`
  (`_build_runner_results` ~L13–71; `race_result` /{race_id} ~L108+).

**Reference-only (read on demand):**
- `/Users/tim/Desktop/Projects/bethub-rebuild/vps_client_api_rewrite_brief.md`
  §5/§12 (the consumer — Brief 2).
- `/Users/tim/Desktop/Projects/bethub-rebuild/race_date_semantics_report.md`
  §4 (Candidate B — for why `scheduled_start` matters).

---

## 4. System access

- **VPS filesystem, read-write**, scoped to the three named files in §5
  **only** (`api/models.py`, `api/routes/races.py`,
  `api/routes/results.py`). No edits to any other file.
- **DIRTY TREE — explicit git limits.** The `racing-data-capture` repo
  is broadly dirty (see §12): `api/routes/races.py` is **untracked**,
  `api/routes/results.py` is **modified**, plus a large unrelated
  in-flight set across betfair/bookmakers/capture/storage/scripts.
  Therefore:
  - **No** `git add`, `git commit`, `git stash`, `git restore`,
    `git checkout` (file-targeted), `git reset` — none, at all.
  - Read `git status` at session **start** and record it.
  - After **each** edit, run `git diff <file>` (or, for the untracked
    `races.py`, re-read the changed region) to confirm only the intended
    change landed.
  - At session **close**, run `git status` and confirm the dirty-file
    set is unchanged except for the content of the three named files.
    Any other file moving is a finding.
- **Deploy:** `systemctl restart racing-api.service` after both changes
  land (the running uvicorn must reload to serve new code). This briefly
  drops the 8400 endpoint; the tunnel reconnects. No other service
  touched (`racing-capture.service` is left alone).
- **`capture.db`:** read-only, for the §7 verification curls only. Never
  copied or mounted.
- All report timestamps Adelaide local (ACST/ACDT) per DR-021.

---

## 5. Substantive scope

### 5.1 — Change A: `betfair_win_market_id` on the race-list summary

- **`api/models.py` → `RaceSummary`:** add one field,
  `betfair_win_market_id: str | None`. Placement is Code's call
  (alongside `scheduled_start` reads cleanly).
- **`api/routes/races.py` → `_build_race_summaries`:** in the
  `RaceSummary(...)` construction (~L35–48), add
  `betfair_win_market_id=race["betfair_win_market_id"]`. The row is a
  `SELECT *` so the column is already in hand; the `/{race_id}` detail
  route already reads it the same way (L133).

Confirmed this session: the column exists on `races` and is populated on
~29% of recent rows (1153 / 3981, last 7d) — non-null where a Betfair
market exists, null otherwise, which is the correct semantics. No
back-fill, no new query.

### 5.2 — Change B: results lookup keyed on `betfair_win_market_id`

Add one route to `api/routes/results.py` that mirrors the existing
`/{race_id}` route but resolves by market id first:

- `GET /racing/results/by-market/{betfair_win_market_id}` →
  `SELECT * FROM races WHERE betfair_win_market_id = ?`.
- Not found → `HTTPException(404, "Race not found for market id")`.
- Found → `_build_runner_results(db, race["id"], betfair_win_market_id)`
  (the existing builder, reused verbatim) → return `RaceResultDetail`
  in exactly the same shape as the `/{race_id}` route.

**Route-ordering note:** the existing `/{race_id}` route is typed
`race_id: int`, so a string market-id path will not be captured by it;
the literal `/by-market/` prefix is unambiguous. Code confirms FastAPI
registration order does not shadow either route. Market ids are strings
(e.g. `1.234567890`) — the path param is `str`, no coercion.

**Duplicate-market guard:** if more than one race row shares a
`betfair_win_market_id` (should not happen — it is the unique Betfair
market), Code takes the first by `id` and notes the collision as a
finding rather than failing.

---

## 6. Sequencing within session

1. Change A (`models.py` field, then `races.py` builder line).
2. Change B (the `by-market` route).
3. `systemctl restart racing-api.service`.
4. §7 verification curls.
5. Record the start/close `git status` pair.

A and B are independent; order is for tidiness, Code may swap and says
so.

---

## 7. Empirical verification

After the restart, all read-only GET over the tunnel
(`http://127.0.0.1:8400`):

- **Change A:** `GET /racing/races?date=<recent populated date>` →
  confirm the `betfair_win_market_id` key is now present in each race
  object, non-null on races that carry a market, null otherwise. Record
  one before/after key-set diff (before = the 12-key set captured this
  session; after = 13 keys).
- **Change B:** pick a known settled race that has a
  `betfair_win_market_id`; call both
  `GET /racing/results/{race_id}` and
  `GET /racing/results/by-market/{that_market_id}` and confirm the
  runner sets are identical (same finish positions, same BSP).
- **404 path:** `GET /racing/results/by-market/0.000000` (bogus id) →
  404, not 500.
- **No regression:** `GET /racing/races/{race_id}`,
  `/racing/races?date=`, `/racing/results/{race_id}`,
  `/racing/results/today`, `/racing/races/today`, `/racing/races/upcoming`
  all still return 200.

Report records the before/after states.

---

## 8. Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/vps_endpoint_enrichment_report.md`.
Sections: (1) what changed per file (the three named anchors only);
(2) curl verification — list key-set before/after, the two results
routes returning identical runner sets, the 404 case, the no-regression
sweep; (3) git-state record — the start `git status`, the close
`git status`, explicit confirmation only the three named files moved;
(4) self-assessment — anchor drift, scope adherence, the duplicate-market
guard if it fired, bet-safety statement (read/analytical path only).
~120–200 lines. **No** recommendations, **no** Mac-client work, **no**
touching the unrelated uncommitted modules.

---

## 9. Hard limits — what is NOT in scope

- **No Mac / `vps_client` changes** — that is Brief 2, after this lands.
- **No schema change** — both fields/columns already exist; this is
  response-model + route surface only.
- **No touching the unrelated dirty set** — betfair, bookmakers, capture
  orchestrator, storage, config, scripts, subscription all carry
  uncommitted work; none of it is read, edited, committed, or reverted.
- **No git write operations** of any kind (§4).
- **No second capture endpoint**, no back-fill job, no new auth, no VPS
  service change beyond the one `racing-api` restart.
- **Single bounded session.** Over-budget → stop and report.

---

## 10. What happens after Code's session

Next operator-Claude session reads
`vps_endpoint_enrichment_report.md`, confirms the enrichment is live
(list carries `betfair_win_market_id`; results-by-market returns), then
**Brief 2 re-locks against the now-real contract** — and Brief 2 sheds
its no-Brief-1.1 fallback machinery (the per-race fan-out in its
§5.2/§5.3 was guarding against a missing `scheduled_start`/`state` that
was never missing; the results path drops the `race_id`-threading
fallback). Code does not write Brief 2.

The VPS git-hygiene debt (§12) is carried as a tracked open item
regardless of the call made.

---

## 11. Cross-references

- Consumer: `vps_client_api_rewrite_brief.md` (Brief 2) §5, §12.
- S204 Brief-1 endpoint: `races_by_date` in `api/routes/races.py`
  (untracked on the VPS — see §12).
- Contract: `race_date_semantics_report.md` §4 (Candidate B), §3
  (the 3 `scheduled_start` encodings).
- DRs: DR-028 (single boundary), DR-027 (two-DB), DR-033 (placings
  analytical), DR-021 (anchors).

---

## 12. Operator call — RESOLVED at lock

**VPS git hygiene. Resolved: proceed surgically (option 1).** Operator
delegated the call at lock ("go with what you think best"). The
`racing-data-capture` repo working tree is
broadly dirty. Last commit (`5f71488`) predates the S204 work; since
then `api/routes/races.py` (the Brief-1 date endpoint) is **untracked**
and `api/routes/results.py` is **modified**, alongside a large unrelated
in-flight set (betfair client/models, bookmakers, capture orchestrator,
storage, config, scripts, subscription). Two of this brief's three edit
anchors sit inside that dirty region.

- **(Recommended) Proceed surgically now.** Code edits the three named
  anchors only, runs no git operations, deploys via the one service
  restart, and the VPS hygiene is logged as tracked debt. A ~20-line
  read-path change should not wait on a repo-cleanup detour. Risk is
  contained by the §4 no-git limits and the start/close `git status`
  check.
- **Alternative: sort the VPS tree first.** Pause Brief 1.1, commit/
  organise the in-flight VPS work in a separate dedicated pass, then run
  1.1 against a clean tree. Cleaner, but blocks Brief 2 behind a larger
  hygiene job.

Either way, the fact that S204's endpoint exists *only* as an untracked
working-tree file is real latent risk and is now on the books.

---

*DRAFT. Grounded against live VPS source + live payload + `git status`,
S205. Holds for the §12 call; nothing handed to Code until then.*
