# DR-029 §2.1 surgical fix — brief for Code session 1 (fixes 1+2 combined)

**Drafted:** Session 35 (2026-04-30 ACST), for hand-off to Claude Code.
**Source authority:** `dr029/2_1_race_data/source_review_report.md` §5.1 plus the §"Anything surprising" entry on `racing-metadata-backfill.service`.
**Governing decisions:** DR-029 (active arc, §2.1 closed-with-known-debt-named Session 34, surgical-fix execution this session); DR-027 / DR-028 (cross-DB discipline — this fix is entirely VPS-side, no cross-DB boundary surface touched); DR-021 (timestamp discipline, ACST anchoring).

---

## 1. What this is, what this isn't

**This is** a single bounded Code session executing two combined surgical fixes against the VPS analytical pipeline at `/home/racing/racing-data-capture/` on `root@187.77.183.9`. The two fixes resolve Cluster 1 (result-population) of the DR-029 §2.1 inspection report, per the surgical-fix routing call landed Session 34. Both fixes use existing code paths — no new modules, no schema changes, no DDL.

- **Fix 1 — bulk backfill of `runners.finish_position` over the live-capture window.** Run existing `scripts/backfill_subscription.py` from live-capture-start to today via The Racing API path. Writes `finish_position`, `result_status`, and runner metadata into `runners` rows that currently have only the Betfair-written half (`betfair_selection_id`, `result_status` from settlement-book polling).
- **Fix 2 — rework `racing-metadata-backfill.service` from `--days 1` to `get_unsynced_dates()`.** Edit the systemd-invoked script wrapper (or the service's `ExecStart`) so the daily nightly run sweeps all unsynced dates rather than only yesterday. Fix the existing PermissionError on `/home/racing/racing-data-capture/logs/metadata_backfill.log` as part of the same change (file owned by root since 2026-03-04 deployment; service runs as `User=racing`, so the FileHandler open fails).

**This isn't** a rebuild, a refactor, or a chance to clean up adjacent code. The three pieces of debt named Session 34 (no test coverage, no migration framework, monolithic orchestrator file) are explicitly out of scope. Surfacing them in passing if encountered is fine; remediating them is not. Similarly, the BSP write-back (Cluster 4 §5.3) and the cadence fixes (Cluster 2 §5.2) are separate fixes for separate Code sessions — do not roll them in.

**This isn't** a fresh diagnosis either. The source-review report has done the file-and-line analysis. Code's job here is execution against named anchors plus empirical verification — not re-investigation.

---

## 2. Why fixes 1 and 2 combine

Fix 1 alone produces a snapshot of `finish_position` data that decays. The daily `racing-metadata-backfill.service` currently runs `--days 1`, which only enriches yesterday — there is no catch-up mechanism for any race whose Racing-API enrichment fails to land on D+1. Subsequent days don't retry. So a one-shot bulk backfill (Fix 1) catches up the existing 60-day window, but the daily service can't keep it healthy going forward.

Fix 2 makes the daily service catch up rather than only sweep yesterday. The `get_unsynced_dates()` helper already exists in `subscription/racing_api.py` (lines 56-66) — it returns all dates where `subscription_synced_at IS NULL`. Switching the service to use it converts the daily run from "enrich yesterday" to "enrich anything still unsynced," which is the behaviour the data layer needs.

Together they constitute the full Cluster 1 result-population resolution: Fix 1 produces the immediate state, Fix 2 keeps it that way.

---

## 3. Pre-reads (in order)

1. This brief.
2. `dr029/2_1_race_data/source_review_report.md` §5.1 in full (the load-bearing source-of-truth for the anchors below) plus the §"Anything surprising" entry on `racing-metadata-backfill.service` (for the PermissionError detail).
3. `dr029/2_1_race_data/source_review_report.md` §5.2 first paragraph and §5.5 — for awareness only, so Code knows what's adjacent and out of scope.

That's the full required-read set. Reference-only:

- `dr029/2_1_race_data/inspection_report.md` §C.1 / §D / §F — the empirical baseline this fix is moving (`finish_position` 0% in 30d; `result_status` distribution; the 1310 SETTLED vs 4334 PENDING split). Read on demand if a verification number needs grounding.
- `dr029/dr029_scope.md` §2.1 close entry plus §2.6 carry-in — the framing this brief executes under. Operator-Claude already has this; Code does not need it for the work.

---

## 4. VPS access — read-write

Distinct from Session 33's source-review (read-only). This session executes against the live VPS:

- **SSH:** `root@187.77.183.9`. Tunnel is up per Session 30 restoration; if it's not up at session open, restart per the launchd unit at `~/Library/Application Support/...` (per Session 30 / 31 routing — Cluster 6 fix lives there).
- **Project root:** `/home/racing/racing-data-capture/`.
- **Service user:** `racing` (the user that owns `racing-capture.service`, `racing-metadata-backfill.service`, etc.). For Fix 2's log-file ownership change, you'll need to act as root or use sudo — the service unit's `User=racing` is the constraint, not Code's session permissions.
- **`capture.db`:** verification queries should use `sqlite3 'file:/home/racing/racing-data-capture/data/capture.db?mode=ro'` for read confirmation. The bulk backfill writes via the existing `subscription/racing_api.sync_day` path; do not write to the DB directly via sqlite3.
- **No code Code-side staging**: edits land directly in the VPS source tree via SSH. There is no separate dev environment.

---

## 5. Fix 1 — backfill `finish_position` over the live-capture window

### 5.1 What the existing code does

`scripts/backfill_subscription.py` is the bulk-runner for Racing API enrichment. It accepts `--from`, `--to`, `--days` flags, calls `sync_day(target_date)` per day, with a configurable `--delay` sleep between days (default 2.0s) for rate-limit headroom.

`sync_day()` in `subscription/racing_api.py` calls `_sync_single_runner` (lines 261-310) per runner, which:

1. Parses `runner.position` from The Racing API response.
2. Sets `runners.finish_position` = parsed position.
3. Sets `runners.result_status` = "WINNER" (pos=1), "LOSER" (other), "REMOVED" (pos=109).
4. Calls `upsert_runner(...)` with `(race_id, runner_key)` keyed merge using COALESCE — non-null new value overwrites NULL existing, NULL new value preserves existing.

Match-by-runner-key uses `compute_runner_key`: `"N:<runner_number>"` if a number is present, else `"S:<runner_name_normalised>"`. A Racing-API runner with `runner.number=5` and a Betfair-discovered runner that produced `"N:5"` via `_ensure_betfair_runner` merge into the same `runners` row — `finish_position` lands on the row that already carries `betfair_selection_id`.

This is exactly the path-not-taken §5.1 of the source-review report identified. Code is not writing this logic; it's running it.

### 5.2 Determining the live-capture window

Source-review report §5.1 references "the 60-day live-capture window" and a `--from 2026-03-02` example. Verify the exact live-capture start date empirically before running rather than hard-coding 2026-03-02. The signal: earliest `betfair_snapshots.snapshot_time` per `capture.db`.

```sql
SELECT MIN(snapshot_time) AS live_capture_start
FROM betfair_snapshots;
```

Use the date portion of that result as `--from`. If the result lands before 2026-03-02, use the earlier date; the backfill is idempotent so over-running into pre-live-capture territory is safe (Racing API has the data either way; the Betfair-side rows it merges into may or may not exist). If the result lands after 2026-03-02, use the actual start.

### 5.3 The run

Single command, single bulk run:

```
python3 scripts/backfill_subscription.py --from <live_capture_start> --to <today_ACST>
```

(Substitute the actual ISO dates. The `--to` defaults to today if the script supports that, but pass it explicitly for log clarity.)

Anticipated runtime: ~60 days × 2.0s default delay = ~2 minutes of API-call wall-clock plus per-day Racing API response time. Script's existing rate-limit handling and per-day retry are sufficient — do not add new retry logic.

### 5.4 Anchors

- `scripts/backfill_subscription.py` — top-level CLI entrypoint, no changes needed.
- `subscription/racing_api.py:209-223` — `sync_day` upsert call, keyed `(race_date, venue_normalised, race_number)` via `normalise_venue` from `matching/race_matcher.py:60-79`.
- `subscription/racing_api.py:261-310` — `_sync_single_runner`, the actual write path for `finish_position`.
- `storage/database.py:218-227` — `compute_runner_key` (verify the rule mentioned above).
- `storage/database.py:330-352` — `upsert_runner` COALESCE merge logic (verify behaviour but no edit).

---

## 6. Fix 2 — rework `racing-metadata-backfill.service` to use `get_unsynced_dates()`

### 6.1 What's currently wired

- **Unit:** `racing-metadata-backfill.service`, `Type=oneshot`, runs daily at 23:30 Adelaide via a corresponding timer.
- **ExecStart:** invokes `scripts/backfill_race_metadata.py --days 1`.
- **Status:** `Active: failed (Result: exit-code) since Wed 2026-04-29 14:00:05 UTC`. Has been failing nightly since.
- **Failure root cause:** `PermissionError: [Errno 13] Permission denied: '/home/racing/racing-data-capture/logs/metadata_backfill.log'`. Log file exists, owned `root:root`, mode 644, dated 2026-03-04 (deployment-day creation by root, never rotated). Service runs as `User=racing`, so `logging.FileHandler(LOG_FILE)` fails on open.

### 6.2 The two changes

**Change A — log-file ownership.** Single command as root:

```
chown racing:racing /home/racing/racing-data-capture/logs/metadata_backfill.log
```

Verify with `ls -l` post-change. If the file is needed at all (the script may also write to stdout via the systemd journal), an alternative is to remove it and let the script recreate as the `racing` user — but the simpler path is the chown above.

**Change B — switch from `--days 1` to `get_unsynced_dates()`.** Two implementation options; Code's call which is cleaner:

- **Option B1 (preferred):** edit `scripts/backfill_race_metadata.py` so that when invoked with no `--days` and no `--from`/`--to`, it calls `get_unsynced_dates()` and iterates over the returned list. Then update the service unit's `ExecStart` to drop the `--days 1` flag. Keeps the CLI flexible — manual one-off `--days N` invocations still work for ad-hoc cases.
- **Option B2:** introduce a new flag `--unsynced` (or similar) that explicitly invokes the `get_unsynced_dates()` path, and update the service unit to use the new flag. More verbose but leaves the no-flag default behaviour unchanged.

Either is acceptable; B1 is the cleaner default. Pick the one that fits the existing CLI shape better — Code's call after reading the script's existing argparse setup.

`get_unsynced_dates()` lives at `subscription/racing_api.py` lines 56-66 per the source-review report. Verify the helper's return shape (list of date strings? list of date objects?) before wiring; iterate it the way `sync_day(target_date)` expects its arg.

### 6.3 Anchors

- `racing-metadata-backfill.service` unit file — locate via `systemctl cat racing-metadata-backfill.service` to find the unit-file path; edit there or via `systemctl edit` for an override drop-in.
- `scripts/backfill_race_metadata.py:32-49` — current `mkdir` + `FileHandler` setup that fails. The PermissionError fix is Change A; the script itself doesn't need editing for that.
- `scripts/backfill_race_metadata.py` argparse / main — for Change B's flag rework.
- `subscription/racing_api.py:56-66` — `get_unsynced_dates()` definition.

---

## 7. Sequencing within the Code session

Suggested order — do not strictly require Code follow this if a different order is operationally cleaner:

1. **Verify VPS reachability and current state.** SSH in, confirm tunnel up, confirm project root contents match expected (`scripts/`, `subscription/`, `storage/`, `capture/`, etc.). `git status` on the project to confirm clean working tree before edits.
2. **Pre-fix verification queries.** Capture baseline numbers from `capture.db` for `runners.finish_position` population and `result_status` distribution over the live-capture window. These are the before-numbers Fix 1's verification compares against.
3. **Fix 2 Change A first** (chown the log file). Smallest, lowest-risk change; clears the recurring failure independent of anything else.
4. **Fix 2 Change B** (switch to `get_unsynced_dates()`). Edit script + edit service unit. Reload systemd (`systemctl daemon-reload`).
5. **Manually invoke the reworked service** (`systemctl start racing-metadata-backfill.service`) as a smoke test before the next scheduled nightly run. Verify it processes more than one day. Watch logs.
6. **Fix 1.** Determine `live_capture_start` empirically per §5.2. Run `backfill_subscription.py --from <date> --to <today>`. Watch progress; expect ~2-5 min wall clock.
7. **Post-fix verification queries.** Re-run the baseline queries from step 2; confirm `finish_position` populated for live-capture-window rows; confirm `betfair_selection_id` overlap is now non-zero.
8. **Smoke-test the daily service** by leaving it to run at 23:30 Adelaide (or invoking it again manually) and checking logs the next session for clean execution.

If Fix 2 surfaces an unexpected interaction (e.g., `get_unsynced_dates()` returns an unexpectedly large list that would blow Racing API rate limits if processed in one run), surface as a finding before proceeding to Fix 1. The fixes are independent enough that Fix 1 can run cleanly even if Fix 2 needs a follow-up tweak.

---

## 8. Empirical verification

### 8.1 Pre-fix baseline (captured before any edits)

```sql
-- Baseline: finish_position population over the live-capture window
SELECT
  COUNT(*) AS total_runners,
  SUM(CASE WHEN finish_position IS NOT NULL THEN 1 ELSE 0 END) AS with_finish_position,
  SUM(CASE WHEN betfair_selection_id IS NOT NULL THEN 1 ELSE 0 END) AS with_bf_selection,
  SUM(CASE WHEN finish_position IS NOT NULL
            AND betfair_selection_id IS NOT NULL THEN 1 ELSE 0 END) AS with_both
FROM runners ru
JOIN races ra ON ra.id = ru.race_id
WHERE ra.race_date >= '<live_capture_start>';

-- Baseline: result_status distribution
SELECT result_status, COUNT(*) FROM runners ru
JOIN races ra ON ra.id = ru.race_id
WHERE ra.race_date >= '<live_capture_start>'
GROUP BY result_status;

-- Baseline: subscription_synced_at coverage
SELECT
  COUNT(*) AS total_races,
  SUM(CASE WHEN subscription_synced_at IS NOT NULL THEN 1 ELSE 0 END) AS synced
FROM races
WHERE race_date >= '<live_capture_start>';
```

### 8.2 Post-fix expected state

- `runners.finish_position` populated for the substantial majority of live-capture-window rows. Not 100% — some races never get Racing API enrichment (cancelled, edge-case venues, late additions). The expected rate is "high enough that it's no longer a Cluster 1 finding" — concretely, well over 90% for races whose `result_status` is settled.
- `with_both` (`finish_position` AND `betfair_selection_id`) shifts from the pre-fix 0 (per inspection report §C.2) to the same substantial majority. This is the headline number — the join semantics v3's analytical reads depend on are now functional.
- `subscription_synced_at` populated for nearly all live-capture-window races.
- `racing-metadata-backfill.service` runs cleanly (verify via `systemctl status` and journal logs).

### 8.3 Verification rerun

Re-run the §8.1 queries post-fix. Report before/after side by side in the output.

---

## 9. Output spec

Code produces a single deliverable: `dr029/2_1_race_data/surgical_fix_1_2_report.md`.

Anticipated 100-200 lines, covering:

1. **What was done** — a short narrative of the actual sequence executed (which order, what was found mid-stream, any deviations from the brief's suggested sequencing).
2. **Pre-fix baseline numbers** — output of the §8.1 queries.
3. **Fix 1 execution log summary** — `--from` / `--to` dates used, total runtime, any non-200 Racing API responses, any rows where `sync_day` raised before completion.
4. **Fix 2 changes applied** — exact diff of script and service unit changes (or the systemd `edit` override), output of `chown` and the manual smoke-test of the service.
5. **Post-fix verification numbers** — output of the §8.1 queries re-run, side by side with pre-fix.
6. **Anything surprising** — any code-state mismatch between the source-review report's anchors and what was actually found in the source tree (the report is dated 2026-04-30 13:30 ACST so drift is unlikely, but flag if anything has shifted). Any unexpected Racing API behaviour. Anything else worth Operator-Claude awareness.
7. **What's left** — explicit named follow-ups, if any. If the daily-service smoke-test will only conclusively verify on the next nightly run, name that as a Session-37+ verification step.

If anything blocks completion, surface as a finding and stop — do not work around it. The brief is one bounded session; partial completion with clean reporting beats over-running into adjacent fixes.

---

## 10. Hard limits

- **Single Code session.** If both fixes can't land cleanly in one session, finish whichever is further along, report state, stop.
- **No edits outside the anchors named in §5 and §6.** If a fix appears to require editing a file not in the anchor list, that's a finding — surface it, stop, do not proceed.
- **No schema changes.** No `ALTER TABLE`, no `CREATE`, no migration scripts. The schema column for everything this brief touches already exists.
- **No new tests.** The test-coverage gap is named debt; this brief does not address it.
- **No fixes 3 or 4** (BSP write-back, cadence) — those are separate Code sessions.

---

## 11. What happens after

Operator-Claude reads `surgical_fix_1_2_report.md` in Session 36 (or whichever session next opens after this Code run). Subsequent surgical-fix Code sessions:

- **Code session 2** — Fix 3 (BSP write-back, Cluster 4 §5.3). Three additive field changes across `betfair/client.py`, `betfair/models.py`, `capture/orchestrator.py`, `storage/database.py`. Schema column already exists.
- **Code session 3** — Fix 4 (cadence, Cluster 2 §5.2). Lower `DISCOVERY_INTERVAL`, add fast-discovery sweep, log `_register_race` silent-drop branch.

Subsequent surgical-fix briefs (for fixes 3 and 4) get drafted in Operator-Claude sessions following each Code session's report. DR-029 §2.4 / §2.6 / §2.10 carry the surgical-fix carry-in framings these execute under.

---

*End of brief.*
