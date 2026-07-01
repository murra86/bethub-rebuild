# Report — VPS racing-API enrichment (Brief 1.1)

**Brief:** `vps_endpoint_enrichment_brief.md` — LOCKED, sha256
`ec70a2bd…227d6d` (verified full-hash at session start; matched).
**Status:** EXECUTED — both changes live + verified.
**Session:** 2026-06-30, ~10:34–10:50 ACST (DR-021 Adelaide, ACST =
UTC+9:30). Target `root@187.77.183.9` : `/home/racing/racing-data-capture`.
**Bet-safety:** CLEAN — read/analytical path only (DR-033). Added two
read fields/lookups to the racing API. No settlement, money-movement,
lay, or live-betting write path touched. `capture.db` opened read-only
for verification only. `racing-capture.service` not touched.

**Headline finding (see §4):** the locked "first by id" tie-break for
the new by-market route is materially affected by a **dominant**
market-id duplication in the data — 87% of market-bearing rows share
their `betfair_win_market_id` with ≥1 other row, and the lowest-id
sibling is frequently a PENDING 0-runner discovery shell. The route was
built exactly as locked; this is surfaced as a finding for
operator-Claude / the Brief 2 re-lock, not silently changed.

---

## 1 — What changed (three named anchors only)

**A1 — `api/models.py` → `RaceSummary`** (one field added, after
`scheduled_start`):

    scheduled_start: str | None
    betfair_win_market_id: str | None      # ← added
    n_runners: int

**A2 — `api/routes/races.py` → `_build_race_summaries`** (one kwarg in
the `RaceSummary(...)` construction; row is `SELECT *`, column already
in hand):

    scheduled_start=race["scheduled_start"],
    betfair_win_market_id=race["betfair_win_market_id"],   # ← added
    n_runners=counts["total"],

**B — `api/routes/results.py` → new route** inserted immediately before
`@router.get("/{race_id}", …)` (verbatim):

    @router.get("/by-market/{betfair_win_market_id}", response_model=RaceResultDetail)
    def race_result_by_market(
        betfair_win_market_id: str, db: sqlite3.Connection = Depends(get_db)
    ):
        """Single race result resolved by Betfair win market id (event_id). …
        … the lowest race id wins (ORDER BY id)."""
        race = row_to_dict(db.execute(
            "SELECT * FROM races WHERE betfair_win_market_id = ? ORDER BY id",
            (betfair_win_market_id,),
        ).fetchone())

        if not race:
            raise HTTPException(status_code=404, detail="Race not found for market id")

        runner_results = _build_runner_results(
            db, race["id"], race["betfair_win_market_id"]
        )
        return RaceResultDetail( … same shape as /{race_id} … )

`_build_runner_results` and `Depends(get_db)` reused unchanged. No
schema change, no `main.py` change, no new model. Each edit applied via
an anchored, uniqueness-asserted patch; all three files passed
`py_compile`. Deployed with `systemctl restart racing-api.service`
(active since 2026-06-30 01:15:04 UTC = 10:45:04 ACST).

**Method / safety:** off-repo backups taken first
(`/tmp/{models,races,results}.py.b11-pre`); each edit verified by
`diff` against its backup (clean isolation even for the modified
`results.py`). No `.bak` written inside the repo.

---

## 2 — Curl verification (post-restart, over the :8400 tunnel)

**Change A — list key-set before → after:**

| | keys |
|---|---|
| before (this session) | 12: id, race_date, venue, state, race_number, race_name, distance_metres, track_condition, scheduled_start, n_runners, n_scratched, sources_with_data |
| after | **13** (above + `betfair_win_market_id`) |

`GET /racing/races?date=2026-06-28` → 200; each object now carries
`betfair_win_market_id`; non-null on 149 / 560 rows (null where no
Betfair market), correct semantics.

**Change B — results routes:**

| Check | Request | Result |
|---|---|---|
| Identical sets | `results/2652720` vs `results/by-market/1.259477316` | both 200; both id 2652720, 15 runners; **top-id + (finish_position, bf_bsp, selection_id, result_status) sets IDENTICAL** |
| Dup-guard demo | `results/by-market/1.259530858` | 200; returns lowest id 2652588 → `PENDING`, **0 runners** (the shell — see §4) |
| 404 path | `results/by-market/0.000000` | **404** "Race not found for market id" (not 500) |

Test market `1.259477316` (Broome 2026-06-28) was chosen because its
lowest-id row (2652720) is itself a settled race with finish positions,
making the identical-set check meaningful rather than trivially empty.

**No-regression sweep — all 200:**

    racing/races/2652720            HTTP 200
    racing/races?date=2026-06-28    HTTP 200
    racing/results/2652720          HTTP 200
    racing/results/today            HTTP 200
    racing/races/today              HTTP 200
    racing/races/upcoming           HTTP 200

---

## 3 — Git-state record (no git write ops were run)

`git status --porcelain`, HEAD `5f71488` (unchanged across session).

**Start vs close — the only differences:**

| file | start | close | note |
|---|---|---|---|
| `api/models.py` | (tracked, clean — unlisted) | **` M`** | named anchor A1 — expected new M |
| `api/routes/results.py` | ` M` | ` M` | named anchor B — content changed, status same |
| `api/routes/races.py` | `??` | `??` | named anchor A2 — content changed, status same |

Every other path is **byte-for-status identical** start→close: the 14
other ` M` files (api/main.py, betfair/*, bookmakers/*,
capture/orchestrator.py, config/settings.py, matching/race_matcher.py,
scripts/*, storage/database.py, subscription/racing_api.py) and the
untracked set (api/__init__.py, api/db.py, api/routes/__init__.py,
api/routes/health.py, api/routes/snapshots.py, bookmakers/tabtouch.py,
scripts/liveness_check.py.bak). **Confirmed: only the three named files
moved.** No `add`/`commit`/`stash`/`restore`/`checkout`/`reset` was run.

**Pre-existing oddity (not mine):** a stray untracked file literally
named `['DB_PATH` was present at session **start** (it is not in the
§12 dirty-set listing) and is still present, unchanged, at close. I did
not create, read, or touch it — flagged for operator-Claude as a
pre-existing artifact.

---

## 4 — Self-assessment

**Duplicate-market guard — FIRED, and it is the dominant case, not an
edge.** The brief (§5.2) assumed `betfair_win_market_id` is "the unique
Betfair market" and duplicates "should not happen." Empirically (read-
only):

- **7,996** distinct market ids are shared by >1 race, spanning
  **16,033 of 18,418 (87%)** market-bearing rows. Only ~2,385 rows have
  a market id unique to one row.
- Anatomy of one set (market `1.259530858`, 3 rows, all race_number 7,
  all `scheduled_start = 2026-06-29T06:43Z`, same market):

  | id | race_date | venue | capture_status | n_runners |
  |---|---|---|---|---|
  | 2652588 | 2026-06-28 | Emerald Downs | PENDING | 0 |
  | 2674078 | 2026-06-28 | Emerald | SETTLED | 15 |
  | 2677487 | 2026-06-29 | Emerald | SETTLED | 15 |

  One physical race, three rows — split because the `races` natural key
  is `(race_date, venue_normalised, race_number)` and **both** differ
  across siblings: `race_date` (06-28 vs 06-29, the two ingest paths per
  `race_date_semantics_report.md`) and `venue` ("Emerald Downs" vs
  "Emerald", a normalisation mismatch). The Betfair market id is the
  same across all three.

**Consequence for the route as locked:** `ORDER BY id` returns the
**lowest** id, which is typically the earliest-created row — the live-
orchestrator **discovery shell** (PENDING, 0 runners), as demonstrated
in §2 B2 (`by-market/1.259530858` → id 2652588, 0 runners). So a Brief 2
client keying results on `event_id` (= win_market_id) via this route
will, in the duplicate-dominant case, receive an **empty shell** rather
than the settled 15-runner result that lives on a higher-id sibling.
The route is correct *to the locked spec*; the spec's tie-break is the
wrong one for this data. **Routed to operator-Claude triage (brief §1);
not changed here, and no fix prescribed (brief §8 "no recommendations").**
This should be resolved before Brief 2 relies on `by-market` for
results — it directly affects the Log-Past-Bet lookup the chain exists
to fix.

**Anchor drift:** none. All three anchors matched the live files as the
brief described (`RaceSummary` field list, `_build_race_summaries`
construction, the `/{race_id}` results route). Change A2's column was
already read by the `/{race_id}` detail route the same way (no new
query). Models/route shapes unchanged otherwise.

**Restart timing (transparency):** unlike the Brief-1 restart, this one
ran during **active capture** — `collector_active: true`, snapshots
seconds old, and 1 race starting within 10 min (it was ~10:45 ACST, peak
AU racing). `racing-api.service` is a separate systemd unit from
`racing-capture.service`; the restart drops only the read endpoint on
:8400 for ~2 s and does not touch the collector or `capture.db` writes.
`racing-capture.service` confirmed still `active` immediately after.
Bet-safety/data risk: nil (read/analytical path, DR-033). A truly idle
window does not occur during the racing day, so the required deploy was
not deferred. Recorded rather than treated as a blocker.

**Scope adherence:** edited only the three named files at the named
anchors; no schema change; the 14 unrelated dirty modules were neither
read nor touched; **zero git write operations**; one `racing-api`
restart, no other service change; single bounded session. The
duplicate-market discovery was surfaced as a finding, not actioned —
staying inside the locked scope per the operator's instruction.

**Bet-safety statement:** CLEAN — this session added two read fields/
lookups to the analytical racing API (DR-033) and restarted only the
read API. No Betfair, settlement, money-movement, lay-placement, or
live-betting path was read or written.

*Report landing complete — operator-Claude can confirm the enrichment
is live (list carries `betfair_win_market_id`; results-by-market
returns) and must weigh the §4 duplicate-market finding before Brief 2
re-locks against `by-market`.*
