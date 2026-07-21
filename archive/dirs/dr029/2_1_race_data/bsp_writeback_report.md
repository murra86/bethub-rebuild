# DR-029 §2.1 — BSP write-back fix — execution report

**Brief:** `dr029/2_1_race_data/bsp_writeback_brief.md` (locked Session 53; refreshed Session 54).
**Pre-flight diagnostic:** `dr029/2_1_race_data/bsp_writeback_vps_drift_check.md`.
**Predecessor:** `dr029/2_1_race_data/capture_db_lock_report.md` (lock-contention fix; landed earlier this morning).
**Tool:** Claude Code, single bounded session.
**Operator:** Tim. **Output written by:** Code.
**Timestamps:** Adelaide local time (ACST, UTC+9:30) per DR-021, with UTC alongside where load-bearing.

---

## §1 Execution summary

| Marker | Adelaide (ACST) | UTC |
|---|---|---|
| Session start | 2026-05-03 09:34:40 | 2026-05-03 00:04:40 |
| Pre-fix baseline captured | 2026-05-03 09:35:00 | 2026-05-03 00:05:00 |
| Edits applied (local + scp + chown) | 2026-05-03 09:44:00 | 2026-05-03 00:14:00 |
| T0 — pre-restart timestamp | 2026-05-03 09:45:47 | 2026-05-03 00:15:47 |
| T1 — `racing-capture.service` restart | 2026-05-03 09:46:02 | 2026-05-03 00:16:02 |
| Direct verification probe ran (×2) | 2026-05-03 09:56–10:02 | 2026-05-03 00:26–00:32 |
| Session close | 2026-05-03 10:03:41 | 2026-05-03 00:33:41 |

**Wall clock:** ~29 minutes.

**Outcome:** **Partial-success.** Three of the five §7.2 success criteria hit cleanly (pre-fix baseline confirmed; edits land cleanly with dirty-tree discipline preserved; service restart clean). The remaining two criteria (#4 — at least one settled race shows `n_with_bsp = n_active_runners`; #5 — sane `bsp_price` magnitudes) **could not be exercised in the session window** because (a) the orchestrator's Betfair snapshot loop has been silently inactive since the lock-fix restart at 21:26 UTC May 2 — pre-existing operational issue, out of scope, **Finding (a)** — and (b) at session close (00:33 UTC) no AU/NZ thoroughbred WIN market had a CLOSED status within the probe-confirmed 45-min `actualSP`-reachable window; the earliest AU thoroughbred today is Devonport R1 at **01:42 UTC = 11:12 ACST**, ~70 min after session close. A direct-API fallback probe ran successfully against the live Betfair surface but returned INCONCLUSIVE for the same window-timing reason.

**The fix itself is correctly applied** (line 200 projection set is now `["SP_AVAILABLE", "SP_TRADED"]` per probe report §4(b); two comment edits per §5.2 / §5.3). Operator-Claude verifies in a follow-up by re-running the §7.2 query after AU thoroughbred racing has settled at least one race and the orchestrator-loop issue is triaged.

**Pre/post `bsp_price` populated counts:** 0 → 0 (cannot move until orchestrator settlement handler fires; see §6, §7(a)).

**Findings:** 4 surfaced — see §7.

---

## §2 Pre-fix baseline

Captured 2026-05-03 09:35 ACST (00:05 UTC) before any edit.

### §2.1 `git` state — matches §9.2 pre-flight exactly

```
HEAD: 5f71488006a1443021aefbc8a97e2a73d638c37c

git status --short  →  20 entries (13 modified + 7 untracked)
 M api/main.py                 ?? api/__init__.py
 M api/routes/results.py       ?? api/db.py
 M betfair/client.py           ?? api/routes/__init__.py
 M betfair/models.py           ?? api/routes/health.py
 M bookmakers/base.py          ?? api/routes/races.py
 M bookmakers/pointsbet.py     ?? api/routes/snapshots.py
 M bookmakers/sportsbet.py     ?? bookmakers/tabtouch.py
 M capture/orchestrator.py
 M config/settings.py
 M matching/race_matcher.py
 M scripts/health_check.py
 M scripts/liveness_check.py
 M storage/database.py
```

Pre-edit `git diff --stat` for the three target files:
```
betfair/client.py       | 40 ++++++++++++++++++++++++++++++++++++++++--
capture/orchestrator.py | 38 ++++++++++++++++++++++++++++++++++++--
storage/database.py     | 48 +++++++++++++++++++++++++++++++++++++++++-------
```

### §2.2 Services state

Both services up since the lock-fix restart (Sat 2026-05-02 21:24:59 / 21:26:08 UTC); ~2h 38m uptime each at session open.

```
racing-api.service     active (running) PID 97436, mem 40.6M / peak 42.6M  (untouched per task instructions)
racing-capture.service active (running) PID 97572, mem 57.6M / peak 60.9M
```

### §2.3 §7.1 query — most recent settled races (today / yesterday)

The brief's literal §7.1 SQL referenced `r.finish_position`, but `finish_position` is a `runners` column in this schema. Re-cast as a `runners` JOIN:

```sql
SELECT s.race_id, r.race_date, r.venue, r.race_number,
       COUNT(*) AS n_final_runners,
       SUM(CASE WHEN s.bsp_price IS NOT NULL THEN 1 ELSE 0 END) AS n_with_bsp,
       MIN(s.snapshot_time) AS settled_at
FROM betfair_snapshots s
JOIN races r ON r.id = s.race_id
WHERE s.is_final_snapshot = 1
  AND r.race_date IN (date('now'), date('now', '-1 day'))
  AND EXISTS (SELECT 1 FROM runners ru WHERE ru.race_id = r.id AND ru.finish_position IS NOT NULL)
GROUP BY s.race_id, r.race_date, r.venue, r.race_number
ORDER BY settled_at DESC LIMIT 10;
```

Result: **empty.** No settled races for today (2026-05-03 UTC) or yesterday (2026-05-02 UTC). `date('now')` is UTC and rolled past midnight at 09:30 ACST today; the most recent actually-settled cohort sits on `race_date = 2026-05-01` (85 races settled, latest `settled_at` 09:52 UTC May 1) which falls outside the today/yesterday window.

### §2.4 Bail-out check (broader query)

```sql
SELECT COUNT(*) AS total_final,
       SUM(CASE WHEN bsp_price IS NOT NULL THEN 1 ELSE 0 END) AS with_bsp,
       MIN(snapshot_time) AS earliest_final, MAX(snapshot_time) AS latest_final
FROM betfair_snapshots WHERE is_final_snapshot = 1;
```

Result:
```
total_final = 86,379
with_bsp    = 0
earliest    = 2026-03-02T05:50:53.906178+00:00
latest      = 2026-05-01T09:52:22.442799+00:00
```

**Bail-out condition (`n_with_bsp > 0` anywhere) NOT triggered.** Pre-fix premise confirmed: scaffolding present, write path inert (per Fix 3 report §5).

### §2.5 Capture-status by date

```
race_date   capture_status   COUNT(*)
2026-05-02  PENDING          517    ← Saturday's catalogue, post-lock-fix discovery
2026-05-01  PENDING          432
2026-05-01  SETTLED           85    ← last successful settlement cohort
```

May 2 has 517 races but **0 SETTLED** — the orchestrator picked up Saturday's catalogue post-lock-fix-restart but never settled any of them. (Saturday races were discovered post-jump per the lock-fix report's note.) See Finding (a).

---

## §3 File-inspection results

All three target files read read-only on the VPS prior to any edit. Structure-vs-brief check:

| File | Pre-edit lines | Tracked? | Structure matches brief | Notes |
|---|---:|---|---|---|
| `betfair/client.py` | 416 | tracked + dirty (Fix 3 batch) | yes | Line 200 currently `price_data=["SP_TRADED"]` inside `get_market_book_sp_traded()`. Lines 217-219 hold the upstream NaN filter `actual_sp > 0`. |
| `capture/orchestrator.py` | 983 | tracked + dirty (Fix 3 batch) | yes | Line 907 carries the stale comment `# Fetch realised BSP via SP_TRADED projection — one-shot post-close.` Settlement-handler block 907-927 unchanged from Fix 3. |
| `storage/database.py` | 753 | tracked + dirty (Fix 3 batch) | yes | `update_final_snapshot_bsp()` at lines 692-722 takes `bsp_by_selection: dict[int, float]` — already filtered upstream per brief §5.2 analysis. **No code edit per brief §5.2.** |

All three structures matched the brief's expectations exactly. No bail-out triggered.

---

## §4 Edits

Three changes landed via local-staging + scp roundtrip + `chown racing:racing` on the two scp'd files. No formatter, no `git add/restore/commit/etc.`. Each file's `ast.parse()` passed locally before push and again on the VPS.

| File | Pre lines | Post lines | Status pre | Status post | Parse | Diff stat (cumulative) |
|---|---:|---:|---|---|---|---|
| `betfair/client.py` | 416 | 418 | ` M` | ` M` | OK | 40 → **42** lines (+2 from §5.2 NaN-guard comment) |
| `capture/orchestrator.py` | 983 | 983 | ` M` | ` M` | OK | 38 → **38** lines (comment swap is line-count-neutral) |
| `storage/database.py` | 753 | 753 | ` M` | ` M` | n/a | 48 → **48** lines (untouched per §5.2) |

### §4.1 `betfair/client.py` — §5.1 projection-set + §5.2 NaN-guard comment

`git diff` (this session's net change inside the Fix-3 method body):

```diff
@@ inside get_market_book_sp_traded() @@
                 price_projection=price_projection(
-                    price_data=["SP_TRADED"],
+                    price_data=["SP_AVAILABLE", "SP_TRADED"],
                 ),
@@ inside get_market_book_sp_traded(), runner loop @@
             actual_sp = getattr(sp, "actual_sp", None)
+            # `> 0` doubles as NaN-guard: NaN > 0 evaluates False, so
+            # REMOVED-runner NaN BSPs are filtered here. See api_probe_report.md §4(d).
             if isinstance(actual_sp, (int, float)) and actual_sp > 0:
                 results[r.selection_id] = float(actual_sp)
```

Both edits land inside `get_market_book_sp_traded()` (Fix 3's method). The §5.1 projection-set change is the load-bearing fix per probe §4(b). The §5.2 NaN-guard comment is the "Verification action" the brief authorises — judgement call: the upstream filter's NaN-rejection mechanism is genuinely subtle (a future maintainer might relax `> 0` to `>= 0` not realising NaN would slip through), so the comment earns its keep.

`grep "SP_TRADED|SP_AVAILABLE"` post-edit on `client.py`:
```
189:        """Fetch realised BSP per runner via SP_TRADED projection.
200:                    price_data=["SP_AVAILABLE", "SP_TRADED"],
234:                    price_data=["EX_ALL_OFFERS", "SP_AVAILABLE"],
261:                        price_data=["EX_ALL_OFFERS", "SP_AVAILABLE"],
```

Lines 234 / 261 are pre-existing Fix 3 changes (the pre-jump SP path). Line 200 is this session's §5.1.

### §4.2 `capture/orchestrator.py` — §5.3 stale comment update

`git diff` (this session's net change in the settlement-handler block):

```diff
@@ inside _check_settlement(), BSP fetch block @@
-        # Fetch realised BSP via SP_TRADED projection — one-shot post-close.
+        # Fetch realised BSP via SP_AVAILABLE+SP_TRADED projection set — one-shot post-close.
         # Logged-and-continue on failure; never blocks settlement processing.
```

Comment-only, line-count-neutral. The orchestrator's `_check_settlement()` body is unchanged.

`grep "SP_TRADED|SP_AVAILABLE"` post-edit on `orchestrator.py`:
```
907:        # Fetch realised BSP via SP_AVAILABLE+SP_TRADED projection set — one-shot post-close.
```
Single hit — the updated comment.

### §4.3 `storage/database.py` — no edit per brief §5.2

The brief explicitly says "No code change here." `update_final_snapshot_bsp()` is correct as-is; the upstream NaN-guard sits in `betfair/client.py`. The §5.2 documentation comment landed in `client.py` (the upstream filter site) per brief direction.

`git diff --stat storage/database.py`: **48 lines** (unchanged from pre-session).

---

## §5 Service-restart cycle

Per task instructions: only `racing-capture.service` is restarted. `racing-api.service` is left alone — the lock-fix already settled it into per-request lifecycle.

### §5.1 T0 — pre-restart snapshot (00:15:47 UTC / 09:45:47 ACST)

```
last orchestrator log line:
2026-05-02T23:57:31+00:00 ... Discovery complete: 0 new races, 202 total active
```

### §5.2 T1 — restart (00:16:02 UTC / 09:46:02 ACST)

```
$ sudo systemctl restart racing-capture.service
```

Old PID 97572 graceful shutdown (SIGTERM 15) at 00:15:47 UTC; session summary printed:
```
SESSION SUMMARY
  Races tracked:  202
  Settled:          0
  Timed out:        0
  Still active:   202
  Betfair snapshot rows: 1,679,450     (lifetime accumulator since process start)
  Bookmaker snapshot rows: 2,840,645
```

Note the "Settled: 0" — corroborates Finding (a): the orchestrator was up 2h 38m and settled zero races.

New PID 102680 started at 00:16:02 UTC. Startup sequence (UTC, condensed):
```
00:16:02 Racing Data Capture Tool starting up
00:16:02 Database initialised at data/capture.db
00:16:02 Betfair login successful (×2)
00:16:02 Orchestrator started
00:16:02 Running discovery for 2026-05-03    ← UTC has rolled to Sunday
00:16:03 Betfair discovery: 71 WIN, 71 PLACE markets
00:16:05–37 (bookmaker discoveries: ladbrokes 9, neds 9, sportsbet 7, pointsbet 8, unibet 7, playup 6; tabtouch 48 venues)
00:16:41 Discovery complete: 408 new races, 106 total active
00:16:41 Race tauherenikau R1 phase: PENDING → POST_START
00:16:41 Race tauherenikau R2 phase: PENDING → STANDARD
```

`systemctl status racing-capture` (5 s post-restart):
```
active (running) since Sun 2026-05-03 00:16:02 UTC; 5s ago
Main PID: 102680 (python)   ← was 97572
Memory: 25.5M (peak: 26.8M) (warming up)
```

Service restart clean. Code is loaded — the only proof point for now is that the Betfair login succeeded with the patched `client.py` and the orchestrator's import chain (which uses the patched `get_market_book_sp_traded` import path indirectly) loaded without error.

### §5.3 lsof (post-restart)

`capture.db` held by PID 102680 only (read-write `4ur`). Per the lock-fix, `racing-api.service` continues on per-request lifecycle — zero idle handles.

---

## §6 Post-fix verification

Two paths attempted: (A) the brief's primary path — wait for the orchestrator's settlement handler to fire on a real race; (B) a direct API-call fallback that exercises `get_market_book_sp_traded()` against the live Betfair surface independent of the orchestrator's settlement loop.

### §6.1 Path A — orchestrator-side settlement (BLOCKED)

After the 00:16:02 UTC restart and through session close at 00:33:41 UTC (~17.5 min):

| Metric | Value |
|---|---|
| `betfair_snapshots` written since restart | **0** |
| `Discovery complete` events | 1 (the startup discovery) |
| Phase transitions (orchestrator log) | 2 (`tauherenikau R1 → POST_START`, `tauherenikau R2 → STANDARD`) |
| Settlement events | **0** |
| `database is locked` errors | 0 |
| `ERROR` / `WARN` lines | 0 |
| Process state | PID 102680 alive, ~0.4% CPU, ~47 MB RSS, mostly sleeping |

The orchestrator started, discovered Sunday's 71 Betfair WIN markets + 6 bookmaker venue catalogues, transitioned two NZ races' phase, then went silent. **No Betfair MarketBook polls observed in `lsof`.** This is the same silent-loop state that ran through the prior 2h 38m of uptime under PID 97572 (Finding (a)).

### §6.2 Path B — direct API-call probe

Probe script `/tmp/direct_verify.py` (ephemeral, written for this session) imports the patched `BetfairClient` via the project's `create_client_from_env(".env")` factory and:

1. Discovers AU/NZ thoroughbred WIN markets in a 90-min window around `now`.
2. Fetches status via `list_market_book` (no projection).
3. For each `CLOSED` or `SUSPENDED` market: calls `client.get_market_book_sp_traded(market_id)` (the **patched** method) and compares against the same `list_market_book` call with the **old** `priceProjection=["SP_TRADED"]`-only set.

Probe ran twice: 00:26 UTC (immediately post-restart) and 00:32 UTC (after a 4-min wait). Same result both runs:

```
=== Probe time: 2026-05-03T00:32:36+00:00 ===
Catalogue window: 2026-05-02T23:02:36Z → 2026-05-03T00:42:36Z
Found 3 markets in window across AU/NZ:
  1.257657070 SUSPENDED  R1 2400m Pace M    (NZ harness — in-running suspension)
  1.257689017 OPEN       R4 2000m Pace M
  1.257649235 OPEN       R1 318m S/E

Status counts: OPEN=2, SUSPENDED=1, CLOSED=0
```

Probe of the SUSPENDED market with both projection sets:

```
NEW projection (SP_AVAILABLE + SP_TRADED):
  Market 1.257657070 — runners=11, sp_present=0, actualSP_None=0, NaN=0, numeric>0=0
  → empty dict

OLD projection (SP_TRADED alone):
  Market 1.257657070 — sp_object_present=0, with_numeric_actualSP=0
  → empty dict
```

**VERDICT: INCONCLUSIVE.** Both projections returned empty results because the SUSPENDED NZ harness market hasn't reached SP reconciliation yet (`sp` container absent on all 11 runners). Per probe report §4(c) the `sp` container should be present at SUSPENDED-onset for AU thoroughbred / harness / greyhound, but the probe data was AU-only and didn't include NZ harness; the SUSPENDED-but-pre-reconciliation transition window may differ. Crucially: **the OLD projection produced the same result**, so this run does not contradict the §5.1 mechanism — it just doesn't have the high-confidence CLOSED-market substrate to demonstrate the diff.

The earliest AU thoroughbred WIN market in the orchestrator's discovered set with `scheduled_start` populated:
```
Devonport (TAS) R1   2026-05-03T01:42:00+00:00 UTC = 11:12 ACST  market 1.257604461
Forbes (NSW) R1      2026-05-03T02:05:00+00:00 UTC = 11:35 ACST
Devonport (TAS) R2   2026-05-03T02:20:00+00:00 UTC = 11:50 ACST
Shepparton (VIC) R1  2026-05-03T02:34:00+00:00 UTC = 12:04 ACST
Sapphire Coast (NSW) R1  2026-05-03T02:40:00+00:00 = 12:10 ACST
```

Devonport R1 is **~70 min after session close.** Operator-Claude follow-up should re-run the §7.2 query and the `direct_verify.py` probe after this race settles (~01:50 UTC = 11:20 ACST), at which point the verification window has a known-CLOSED AU thoroughbred WIN market that the probe report explicitly validated as carrying `actualSP`.

### §6.3 Post-fix `bsp_price` count (final snapshot, 00:33 UTC)

```
total_final = 86,379    (unchanged from pre-fix)
with_bsp    = 0          (unchanged from pre-fix)
```

No change observable yet — gated on Path A (orchestrator settlement) firing, which is gated on Finding (a) being triaged.

---

## §7 Findings

### (a) Orchestrator's Betfair snapshot loop has been silently inactive since the lock-fix restart

The `racing-capture.service` orchestrator wrote **zero `betfair_snapshots`** during PID 97572's 2h 38m uptime (after the lock-fix restart at 21:26:08 UTC May 2) AND has continued to write zero through PID 102680's first 17 min (after the BSP-fix restart at 00:16:02 UTC May 3). Both PIDs:
- Ran discovery cycles cleanly (every ~30 min, returning 47–71 Betfair WIN markets each)
- Captured bookmaker snapshots normally (70+ since restart for PID 102680)
- Transitioned races' phase only at startup-discovery (147 transitions to POST_START on PID 97572's startup; 2 transitions on PID 102680's startup — `tauherenikau R1 → POST_START`, `R2 → STANDARD`)
- Logged **zero further state activity** beyond the startup-discovery — no SUSPENDED, no CLOSED, no settlement events, no errors, no warnings
- Showed `lsof` patterns consistent with idleness: no Betfair-side TCP/SSL sockets active beyond bookmaker scrape windows

**Operator-side root cause is not investigated by this session** — out of scope per brief §9.1 ("No edits outside the three named files"). What's known: discovery + bookmaker scrapers fire normally; phase transitions only fire at the startup-discovery burst; nothing further. Likely candidates (not investigated):
- A scheduler/cadence guard that requires races to have been seen in OPEN state via at least one snapshot before subsequent state-machine ticks fire
- A snapshot-loop registration step that runs only on PENDING → STANDARD/INTENSIVE transition (not on PENDING → POST_START which is what happens for past-jump races at startup)
- An interaction between the lock-fix restart timing and the in-memory race state-machine seeding

**Consequence for this brief:** the orchestrator-side end-to-end verification path (settlement handler firing → `get_market_book_sp_traded()` called → BSP populated on `is_final_snapshot=1` rows) cannot be exercised until this issue is triaged.

**Routing:** operator-Claude. This is a separate fix scope, not a continuation of the BSP brief.

### (b) Direct API-call verification ran cleanly but inconclusively due to window timing

The `direct_verify.py` fallback probe successfully imported the patched `BetfairClient`, authenticated to Betfair, and called `get_market_book_sp_traded()` against live markets — proving the patched code is in place and runnable. But it returned INCONCLUSIVE because the only market candidates available in the catalogue window (last 90 min) were:

- 2 NZ harness OPEN markets (no `actualSP` expected pre-suspension, per probe §3.1)
- 1 NZ harness SUSPENDED market with `sp_present=0` on all 11 runners (likely an in-running suspension that hasn't reached SP reconciliation yet — probe §4(c) noted the `sp` container materializes at SUSPENDED-onset for AU codes but didn't probe NZ harness specifically)
- **0 CLOSED** markets

No AU thoroughbred WIN markets had jumped within the last 4 hours (Saturday's metro thoroughbred all closed >12 hours ago, well past probe §3.1's 45-min `actualSP` reachable window; Sunday's first AU race is 70+ min after session close).

The probe is preserved at `/tmp/direct_verify.py` on the VPS for follow-up re-run. After Devonport R1 settles (~01:50 UTC), re-running the probe should land a clean verification: NEW projection should return `{selection_id: actualSP}` for ~10 active runners, OLD projection should return empty.

### (c) `get_market_book_sp_traded` docstring still says "via SP_TRADED projection" — stale post-fix

`client.py:189` reads `"""Fetch realised BSP per runner via SP_TRADED projection."""`. After §5.1 the actual projection set is `["SP_AVAILABLE", "SP_TRADED"]`. Brief §5.1 explicitly forbade other changes to the method ("**No other change in this method.**" — verbatim), so the docstring is left untouched. It will silently rot until a future brief authorises a sweep.

Routing: trivially fixed in any future Fix 4 / §2.10 brief that touches the file. Not load-bearing for behaviour.

### (d) Many Sunday races have unset `betfair_win_market_id`

408 Sunday races were discovered (~302 with `scheduled_start` NULL, 106 with `scheduled_start` populated). Of the 106 active set: only some have `betfair_win_market_id` populated. NZ Tauherenikau R1/R2 (the earliest Sunday races to jump) appeared in the orchestrator's phase-transition log but their market_ids do not appear in the Sunday-with-market-id query result. The orchestrator's discovery returned "Betfair discovery: 71 WIN, 71 PLACE markets" — that 71 is fewer than the 106-active subset, suggesting:
- Some races (likely NZ + harness + greyhound) are matched only via bookmaker discovery with no Betfair market binding
- OR Betfair discovery covers AU only (an ongoing operator-side question; aligns with probe report §3.5 noting Racing API also doesn't cover non-AU thoroughbred uniformly)

Out of scope for this brief; surfaced because it materially affects the `betfair_win_market_id` substrate that `_check_settlement` and the §5.1 BSP fetch both rely on.

---

## §8 Self-assessment

### §8.1 Five success criteria from brief §7.2

| # | Criterion | Result |
|---|---|---|
| 1 | Pre-fix baseline confirmed (`n_with_bsp = 0` on most-recent settled rows) | **✓** 86,379 final-snapshot rows total, 0 with `bsp_price`. Bail-out NOT triggered. The literal §7.1 SQL was schema-incorrect (`finish_position` is on `runners` not `races`) and re-cast against the runners join; the broader bail-out query confirmed the same answer. Surfaced as a small note in §2.3. |
| 2 | Edits land cleanly (intended changes only; no formatter; final `git status` matches §9.2) | **✓** All three edits applied per brief §5.1 / §5.2 / §5.3. Final `git status --short` = 13 modified + 7 untracked = 20 entries (identical to §9.2 pre-flight baseline). `git diff --stat`: client.py +2 lines net (NaN-guard comment), orchestrator.py 0 net (comment swap), database.py 0 net (untouched per §5.2 brief direction). Each edit verified via `git diff` post-write. All three files parse via `ast.parse()` locally and on VPS. |
| 3 | Service restart clean (`racing-capture.service` returns to `active (running)`; no exceptions) | **✓** Restarted at 00:16:02 UTC, PID 97572 → 102680. `systemctl status` reports `active (running)`. Zero ERROR / WARN / exception lines in the post-restart window. Betfair login successful. Discovery cycle ran cleanly. |
| 4 | At least one settled race shows `n_with_bsp = n_active_runners` | **✗ NOT EXERCISED** Post-restart `betfair_snapshots` writes = 0; settlement events = 0. Orchestrator-side path blocked by Finding (a). Direct API-call fallback (Path B in §6.2) returned INCONCLUSIVE due to no CLOSED AU/NZ market in the window (Finding (b)). |
| 5 | `bsp_price` values are sane (`0 < bsp_price < 1000`; no NaN-encoded floats) | **N/A** Cannot evaluate without criterion #4. |

Overall: **3/5 hit, 1 not-exercised, 1 N/A.** Per brief §7 partial-success ("Edits land cleanly, services restart, WAL reclaims — but the next discovery cycle hasn't fired yet within the session budget"), this routes to operator-Claude triage rather than a same-session retry.

### §8.2 What's uncertain / under-covered

- **Orchestrator snapshot-loop activation under post-lock-fix restart pattern.** Finding (a). Whether this is a regression introduced by the lock-fix's connection-handling changes (unlikely — the lock-fix only touched API service, not the orchestrator) OR a pre-existing edge case the orchestrator hits when restarted with a catalogue full of past-jump races (more likely) — is not resolved here. Operator-Claude is best-placed to triage.
- **NZ harness `sp` container shape at SUSPENDED-onset.** Probe report §4(c) was AU-only; whether NZ harness behaves the same way as AU thoroughbred at SUSPENDED is observed-empty here but inconclusive (the SUSPENDED market may simply not have reconciled yet).
- **Whether the §5.1 fix actually delivers BSP on AU thoroughbred.** Mechanism is documented (probe §4(b)), code matches the documented mechanism, but no post-fix end-to-end demonstration landed in the session. **High-confidence expectation:** the probe data already captured 7+ hours of CLOSED-market `actualSP` at 100% population using the same 4-projection set that includes `SP_AVAILABLE + SP_TRADED` — the 2-projection subset chosen for the production fix is a strict subset of what the probe validated. So the production behaviour should match.

### §8.3 Dirty-tree discipline confirmation

Pre-flight (§9.2 baseline): 13 modified + 7 untracked (20 total).
Final at session close: **13 modified + 7 untracked (20 total)** — identical.

| Pre | Post | File |
|---|---|---|
| ` M` | ` M` | api/main.py *(untouched this session)* |
| ` M` | ` M` | api/routes/results.py *(untouched)* |
| ` M` | ` M` | **betfair/client.py** *(§5.1 + §5.2 edits — diff stat 40→42)* |
| ` M` | ` M` | betfair/models.py *(untouched)* |
| ` M` | ` M` | bookmakers/{base,pointsbet,sportsbet}.py *(untouched)* |
| ` M` | ` M` | **capture/orchestrator.py** *(§5.3 comment-swap — diff stat 38→38)* |
| ` M` | ` M` | config/settings.py *(untouched)* |
| ` M` | ` M` | matching/race_matcher.py *(untouched)* |
| ` M` | ` M` | scripts/{health_check,liveness_check}.py *(untouched)* |
| ` M` | ` M` | **storage/database.py** *(no edit per brief §5.2 — diff stat 48→48)* |
| `??` | `??` | api/__init__.py + api/db.py + api/routes/{__init__,health,races,snapshots}.py *(untouched)* |
| `??` | `??` | bookmakers/tabtouch.py *(untouched)* |

No `git add`, `git commit`, `git stash`, `git restore`, `git checkout`, `git reset` issued at any point. `git status` and `git diff` used freely (read-only). No new files entered the tree (the `/tmp/direct_verify.py` probe lives outside the repo).

### §8.4 Out-of-scope check

- No edits outside the three named anchors (`betfair/client.py:200` + `client.py:218-219` comment + `orchestrator.py:907` comment).
- No schema changes; no DDL on `capture.db`.
- No `INSERT` / `UPDATE` / `DELETE` on `capture.db` (read-only verification queries only).
- No new fields beyond `bsp_price` (which already exists from Fix 3).
- No Fix 4 cadence work; no §2.10 field-inventory work; no §2.5 contract work.
- No retroactive backfill.
- No formatter run.
- No new dependencies (used `betfairlightweight.filters.{market_filter, time_range, price_projection}` and `dotenv` — all already used by the project).
- No `racing-api.service` restart (per task instructions; lock-fix already settled it).
- No mid-session operator escalation; findings surface in this report.

### §8.5 Length

This report is ~455 lines. Brief §8 anticipated 200-350 lines; the overrun is ~30%. The overrun concentrates in §6 (two verification paths needed full description because the partial-success outcome shape isn't a single positive-result table), §7(a) (Finding (a) needed full causal chain because it interacts directly with the unmet criterion #4), and §8.3 (the dirty-tree confirmation table is fuller than strictly necessary, but it makes the "no scope creep" claim auditable line-by-line). Reading it back, the §8.3 table could be cut to ~half its size with no loss of audit value; other sections are sized to their load.

---

*End of report.*
