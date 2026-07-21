# Placings backfill + nightly results-sync fix — Code session report

**Executed:** 2026-06-25, ~21:54 → ~22:15 ACST (single bounded out-of-session Code run, per `placings_backfill_brief.md`).
**Mode:** READ-WRITE, capture-side only. Forward fix to one repo source anchor; recovery writes through the existing pipeline (`sync_day()`), reads `mode=ro`. No v3 / settlement / live-betting / money-path contact. No schema change. No capture.db hand-edit or copy.
**Outcome in one line:** forward fix landed and mechanism-verified; the real bug was deeper than the brief assumed (quota-starvation-by-ordering, not stamp-drop-out); **recovery is blocked by the Racing-API daily request quota** — 2 of 117 dates recovered, the rest is a clean leftover range for follow-up.

---

## 1. Run header

| Item | Value |
|---|---|
| SSH Step-0 gate | **PASS** — `ssh racing-vps 'echo ok'` (via operator ssh-agent), `-o ClearAllForwardings=yes`. |
| Repo | `/home/racing/racing-data-capture` (branch `master`, HEAD `5f71488` 2026-03-04). |
| capture.db | `/home/racing/racing-data-capture/data/capture.db` (~3.97 GB, live WAL). |
| Edit anchor | `scripts/backfill_race_metadata.py::get_unsynced_dates` (1 function). `subscription/racing_api.py` **not modified**. |
| VPS wall-clock | session start `2026-06-25T12:24:49Z` (21:54 ACST); close ~`12:43Z` (22:13 ACST). |
| Writes | forward fix (1 source file) + recovery via `sync_day()` upsert for 2 dates. No git state mutation. |
| Timestamps | capture.db stores UTC; all clock times below in ACST (UTC+9:30, no June DST). |

---

## 2. Working-tree state at session start (dirty-tree gate)

The VPS repo is dirty from the March rework — recorded at start, gate evaluated **before** editing:

```
## master
 M api/main.py            M bookmakers/sportsbet.py   M scripts/health_check.py
 M api/routes/results.py  M capture/orchestrator.py   M scripts/liveness_check.py
 M betfair/client.py      M config/settings.py        M storage/database.py
 M betfair/models.py      M matching/race_matcher.py
 M bookmakers/base.py     M bookmakers/pointsbet.py
 ?? api/__init__.py  api/db.py  api/routes/{__init__,health,races,snapshots}.py
 ?? bookmakers/tabtouch.py  scripts/liveness_check.py.bak
```

**Gate result: CLEAR.** Neither edit anchor — `scripts/backfill_race_metadata.py` nor `subscription/racing_api.py` — was in the dirty list (no modified/untracked collision). Safe to edit without touching anyone's uncommitted work. **Close-out `git status` confirms the dirty list is identical except `scripts/backfill_race_metadata.py` is now `M` (my anchor) — no other file changed, no git state mutated.**

---

## 3. Pre-backfill baseline (capture.db, `mode=ro`)

`finish_position` coverage by race month (runners with non-null `finish_position`):

| Month | Runners | finish_pos % | result_status % | margin % | sp_fixed % |
|---|---|---|---|---|---|
| 2025-11 | 26,833 | 76.9% | 96.5% | 61.3% | 59.4% |
| 2025-12 | 25,058 | 79.2% | 98.1% | 61.9% | 57.9% |
| 2026-01 | 24,611 | 79.5% | 98.0% | 62.5% | 57.8% |
| 2026-02 | 22,721 | 79.9% | 97.4% | 62.1% | 57.8% |
| 2026-03 | 67,297 | **21.2%** | 75.2% | 14.5% | 11.9% |
| 2026-04 | 56,964 | **6.4%** | 80.6% | 2.9% | 2.0% |
| 2026-05 | 53,849 | **0.1%** | 77.1% | 0.0% | 0.0% |
| 2026-06 | 45,366 | **0.1%** | 78.3% | 0.0% | 0.0% |

Reproduces the supply-review curve. Gap window 2026-03-01 → 2026-06-25 = **117 distinct race-dates**.

---

## 4. The forward fix

### 4.1 What I found before editing (the mechanism is not what the brief assumed)
The brief (following the supply review) framed the bug as: *"sync stamps each date on first touch, then never re-pulls it"* — i.e. dates **drop out** of `get_unsynced_dates` once `subscription_synced_at` is set. Grounding the anchors against the live data showed this is **not** what happens:

- `sync_day()` (line 284) does stamp `subscription_synced_at=now_iso` unconditionally on first touch — confirmed.
- **But dates do not drop out.** capture.db holds Betfair-matched greyhound/harness races that the thoroughbred-only Racing API never enriches, so those rows stay `subscription_synced_at IS NULL` **forever**. 116 of the 117 gap dates therefore remain in the `IS NULL` filter permanently (only 2026-03-01 is fully stamped). The nightly backfill **was** re-pulling recent dates.
- The real failure is in the **ordering + unboundedness**. `get_unsynced_dates` returned the whole (ever-growing) `IS NULL` set ordered **oldest-first**, and the Racing API has a **daily request quota**. Last night's run (`metadata_backfill.log`, 2026-06-24 14:00–14:05 UTC = 23:30 ACST) filled the **first 14 dates** (2026-03-02…03-14, already-complete March dates — pure waste) then returned **0 runners for all 101 remaining dates** — the recent dates that needed results were **starved at the tail**. Tally: `dates_with_runners=14, dates_with_zero=101`.

So the bug is **quota-starvation-by-ordering over an unbounded filter**, not stamp-drop-out.

### 4.2 Approach chosen (and why) — a deviation I'm flagging per the brief
The brief recommended *"a trailing N=14-day re-pull window … in addition to genuinely-unsynced dates"* (a **union** with the `IS NULL` set). I first implemented exactly that — and a read-only mechanism check showed it **adds 0 dates** (every recent date is already in the `IS NULL` set via its permanently-unsynceable non-thoroughbred rows) **and preserves oldest-first ordering**, so it would not fix the starvation at all.

I therefore chose the **alternative the brief explicitly permits** ("Code may choose a cleaner hook … and surface the choice as a finding"): **a bounded, recent-first trailing window** — drop the unbounded `IS NULL` union, order **recent-first**. This satisfies every behaviour requirement in §5.2 better than the literal union:
- **Bounded** — ≤ ~15 dates/run, never the whole history (the brief's "must not re-pull the entire history nightly").
- **Recent-first** — the freshest dates win the API quota before it can be exhausted on stale dates (directly fixes the observed starvation).
- **Self-limiting** — a resultless date falls out of the window after N days (the brief's "must not retry a resultless date forever").
- **Safe** — `sync_day()` upserts idempotently.
- Deliberate recovery of older gaps stays the operator's job via `--date`/`--days` (which bypass this function) — i.e. this session's recovery run.

### 4.3 The edit (anchor + bound + `git diff`)
One function, `get_unsynced_dates`. Applied via a guarded exact-replacement (aborts unless the anchor matches exactly once); `py_compile` passed.

```diff
-def get_unsynced_dates(conn) -> list[str]:
-    """Find distinct race_date values where metadata is missing."""
+def get_unsynced_dates(conn, trailing_days: int = 14) -> list[str]:
+    """Return the dates the nightly sync should (re-)pull — a *bounded,
+    recent-first* trailing window of the last ``trailing_days`` days.
+    [docstring explains: IS NULL set is unbounded via non-thoroughbred rows;
+     oldest-first + daily quota starved recent dates; recent-first + bound fixes it]
+    """
     rows = conn.execute(
         """
         SELECT DISTINCT race_date FROM races
-        WHERE subscription_synced_at IS NULL
+        WHERE date(race_date) >= date('now', ?)
           AND is_trial = 0 AND is_jump_out = 0
-        ORDER BY race_date
-        """
+        ORDER BY race_date DESC
+        """,
+        (f"-{trailing_days} day",),
     ).fetchall()
     return [r[0] for r in rows]
```

`git diff --stat`: `scripts/backfill_race_metadata.py | 38 ++++++-` — only this file, only this function. `main()`'s existing call `get_unsynced_dates(conn)` is unchanged (the new `trailing_days` param defaults to 14). **Bound = 14 days (≈15 calendar dates inclusive).**

---

## 5. The backfill recovery run

### 5.1 Controlled single-date test first (proof the pipeline fills)
Before any bulk run I tested one date through the real pipeline — `backfill_race_metadata.py --date 2026-06-20 --delay 1.5`:

| | runners | finish_position filled | races rows |
|---|---|---|---|
| PRE | 3,260 | **0** | 544 |
| POST | 3,260 | **1,384** | 544 (no duplicates) |

`sync_day` reported 139 races / 1,788 runners / 210 refined to PLACED in ~4s. **Confirmed: re-pull fills finish positions, idempotently, no row duplication.** This date's recovery is durable.

### 5.2 Window run — and the quota wall
Ran the gap window recent-first: `backfill_race_metadata.py --days 117 --delay 1.5` (detached, 20-min cap). `--days` builds dates `today − i`, i.e. **2026-06-25 → back to 2026-03-01, recent-first** — so the most valuable dates process first and any shortfall lands on the oldest end.

**Result — the Racing-API daily quota was already (near-)exhausted for 2026-06-25:**
- Of the dates processed before I stopped it (61 dates), **exactly 1 filled: 2026-06-25 (147 runners)**. Every other date returned **0 runners**.
- The smoking gun: **2026-06-20 returned 1,788 runners at 12:31Z (the single-date test) but 0 runners at 12:39Z** (8 minutes later, in the window run). Same date, same code — the data exists; the quota was spent in between (today's 11:30 UTC `sync_day(today)` cron + my test + the run's first date).
- I **stopped the run cleanly** once the wall was unmistakable (consecutive 0-runner dates) rather than burn the remaining rate budget — and to leave tonight's legitimate nightly run its allowance. Process confirmed terminated; transient VPS stdout (`/tmp/cc_backfill.out`) removed.

**Rate-limit adherence:** ran with `--delay 1.5` (above the script's 1.0s default), single-threaded, no new fast path — within the script's existing throttle, not exceeding it. The blocker is a **daily request quota**, a separate ceiling from the 5 req/sec rate limit.

### 5.3 Recovered vs leftover
- **Recovered this session (durable):** `2026-06-20` (1,384 finish positions) and `2026-06-25` (107 so far — today; most races not yet resulted).
- **Leftover (NOT recovered — quota-blocked):** the entire window **2026-03-01 → 2026-06-24 except 2026-06-20** (≈114 dates). The data is inside the Racing-API AU window and `sync_day` is proven to fill it — it is purely quota-gated, recoverable in future runs as quota allows (the API afforded only ~13–14 date-fills per day in observed runs).

---

## 6. Post-backfill coverage (before / after)

| Month | Runners | finish_pos % PRE | finish_pos % POST | Δ |
|---|---|---|---|---|
| 2025-11 | 26,833 | 76.9% | 76.9% | — |
| 2025-12 | 25,058 | 79.2% | 79.2% | — |
| 2026-01 | 24,611 | 79.5% | 79.5% | — |
| 2026-02 | 22,721 | 79.9% | 79.9% | — |
| 2026-03 | 67,297 | 21.2% | 21.2% | — |
| 2026-04 | 56,964 | 6.4% | 6.4% | — |
| 2026-05 | 53,849 | 0.1% | 0.1% | — |
| 2026-06 | 45,372 | 0.1% | **3.4%** | **+3.3pt** (06-20 + 06-25) |

Only June moved, reflecting the 2 recovered dates. The Mar–May gap is untouched (quota-blocked). The expected lift toward ~75–80% did **not** materialise — bounded entirely by the daily quota, a capability limit (§8), not a fix failure.

---

## 7. Forward-fix mechanism verification (+ carve-out)

**In-session mechanism proof (what the nightly job now does):**
- The nightly service runs `backfill_race_metadata.py` **argless** → `get_unsynced_dates()` (confirmed: `ExecStart=…/backfill_race_metadata.py`, timer `23:30 Australia/Adelaide`, `Persistent=true`).
- **Before:** `get_unsynced_dates()` returned **116 dates, oldest-first** (`2026-03-02 … 2026-06-25`).
- **After:** it returns **15 dates, recent-first** (`2026-06-25, 06-24, … 06-11`) — verified by importing and calling the patched function against the live DB read-only.
- Last night's log (14 filled oldest-first / 101 starved) demonstrates the failure the change inverts: the patched path spends the quota on the **most recent** dates first and is bounded so it cannot be exhausted on stale March dates.

**Carve-out (out-of-session, Session-36 precedent):** proving the fix catches a *future* late-publishing result requires the nightly run to fire against newly-published results with quota available — both out-of-session. In-session I proved the **mechanism** (the path now selects recent dates first, bounded) and that `sync_day` fills when quota is available (§5.1); I did not prove a live future catch. Tonight's 23:30 ACST run is the first live exercise.

---

## 8. Findings (surprises → findings, not mid-session escalations)

- **F1 — The bug is quota-starvation-by-ordering, not stamp-drop-out.** Dates do not leave `get_unsynced_dates`; the unbounded, oldest-first `IS NULL` set made the nightly run spend its Racing-API daily quota on already-complete March dates and starve recent dates (14 filled / 101 zeroed on 2026-06-24). The forward fix targets this directly; the supply-review/S174 framing was a partial proxy for it.
- **F2 — `subscription_synced_at IS NULL` is permanently unbounded.** Betfair-matched greyhound/harness rows are never enriched by the thoroughbred-only Racing API, so every date retains `IS NULL` rows forever. Any logic keyed on `IS NULL` (the original filter) grows without bound. *(The harness/greyhound enrichment mapping itself is excluded per §9 — flagged only as the cause of the unbounded set.)*
- **F3 — Recovery is gated by a Racing-API daily request quota, exhausted for 2026-06-25.** Demonstrated by 2026-06-20 returning 1,788 runners then 0 runners 8 minutes apart. Observed budget ≈ 13–14 date-fills/day, shared across the 11:30 UTC `sync_day(today)` cron, the nightly backfill timer, and any manual run. The full Mar–Jun recovery cannot complete in one session against this ceiling.
- **F4 — Two nightly Racing-API consumers share the quota.** The `30 11 * * *` UTC cron (`sync_day(today)` + `refine_placed_status`) and the 23:30-ACST backfill timer both draw on the same daily allowance; with the fix, the backfill timer now requests ≤15 recent dates rather than 116.
- **F5 — The fix's 14-day bound (~15 dates) sits near the observed daily quota (~13–14 fills).** Recent-first ordering means the freshest dates fill first within whatever budget exists, but the oldest 1–2 days of the window may starve on a given night and self-correct the next. Stated as fact; tuning is the operator's call.

---

## 9. Self-assessment — what could not be tested, and why

- **No live forward-fix catch.** Requires the nightly run + published results + available quota (all out-of-session). Mechanism proven; live catch deferred to tonight's 23:30 ACST run (carve-out, §7).
- **Bulk recovery not completed** — hard-blocked by the daily quota (F3), not by the fix or the pipeline. `sync_day` is proven to fill (§5.1); the leftover range (`2026-03-01 → 2026-06-24` minus `2026-06-20`, ≈114 dates) is recoverable in future quota-limited runs.
- **Exact quota size not pinned.** Inferred from two run profiles (14 fills last night; ~1 today after prior consumption). The precise daily ceiling / reset time was not probed (would itself consume quota).
- **`subscription/racing_api.py` left untouched** — the fix was achievable entirely within the one `get_unsynced_dates` anchor; `sync_day`'s unconditional stamp is harmless under the bounded recent-first window (re-pull happens regardless of the stamp), so no second-anchor edit was needed.
- **Scope held:** no auto-settle, no v3/settlement/money-path contact, no schema change, no capture.db hand-edit/copy, no git state mutation, no touch to scrapers/Betfair path or the harness/greyhound enrichment mapping. Recovery writes went only through `sync_day()`'s idempotent upsert.

*Routing (per §10) is the next operator-Claude session's job: confirm the forward fix, decide how the leftover range is recovered against the quota ceiling, and how the quota itself is handled. This report states what is; it proposes no remediation.*
