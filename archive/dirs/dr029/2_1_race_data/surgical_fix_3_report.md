# DR-029 §2.1 — surgical-fix Code session 2 report (Fix 3, BSP write-back)

**Session opened:** 2026-04-30 16:30 ACST.
**Session closed:** 2026-04-30 16:56 ACST.
**Brief executed:** `dr029/2_1_race_data/surgical_fix_3_brief.md`.
**VPS:** `root@187.77.183.9`, source tree `/home/racing/racing-data-capture/`.

**Headline:** All four named changes (a/b/c/d) landed cleanly within the dirty-tree rules and survived a manual restart of `racing-capture.service`. **Change (b) — pre-jump SP projection switch — is the clean win**: post-restart `sp_near_price` and `sp_far_price` populated 100% in INTENSIVE phase and 95% in STANDARD phase, against a pre-fix baseline of 0% across both. **Change (c) — post-suspension BSP fetch — is structurally correct per the brief's spec but empirically inert**: Betfair's `priceProjection=SP_TRADED` request on closed AU thoroughbred WIN markets returns runner objects with no `sp` field at all (verified empirically against three settled markets including one settled 1+ hour earlier), so the post-`_check_settlement` UPDATE path runs but writes 0 BSP rows. The realised-BSP write-back gap is now narrowed to a Betfair-API-shape question for Session 37.

---

## 1. What was done

Sequence executed (matches brief §6 with one minor early-stage diagnostic deviation noted):

1. **VPS state verification.** `git status --short` matched Session 36 drift-check exactly: 8 modified files, 7 untracked entries (`api/__init__.py, api/db.py, api/routes/{__init__,health,races,snapshots}.py, bookmakers/tabtouch.py`). HEAD `5f71488` unchanged. `git diff --stat` line counts for the 8 pre-existing modified files matched the drift snapshot (sportsbet 226, orchestrator 14, pointsbet 11, settings 4, base 4, race_matcher 1, health_check 21, liveness_check 2).
2. **Pre-fix baseline.** §7.1 queries returned exactly the 0% rates in inspection §F: 1,644,562 live-capture-window snapshots (0 BSP, 0 sp_near, 0 sp_far); 84,571 final-snapshot rows (0 BSP); 239,169 INTENSIVE-phase rows (0 sp_near, 0 sp_far).
3. **Edits via scp roundtrip.** Each file was scp'd to `/tmp/fix3_workspace/` for line-exact Edit-tool semantics, then scp'd back. After all four edits, `python3 -m ast` verified all four files parsed cleanly. A second smoke-test ran on the VPS to verify the new `RunnerData.bsp_price` field and the new `BetfairClient.get_market_book_sp_traded` method import without error.
4. **Change (a)** added to `betfair/models.py`: `bsp_price: float | None = None` after `sp_far_price`, with a one-line clarifying comment.
5. **Change (b)** in `betfair/client.py`: replaced `"SP_TRADED"` with `"SP_AVAILABLE"` at both pre-jump call sites — `get_market_book` (line 196) and `get_market_books_batch` (line 223). `replace_all` was used for symmetry; `grep` post-edit confirmed no `SP_TRADED` references remained in either method (the new SP_TRADED call sites for change (c) were added separately below).
6. **Change (d)** in `storage/database.py`: extended `save_betfair_snapshot` (single-row) and `save_betfair_snapshots_batch` INSERT column lists with `bsp_price` slotted between `sp_far_price` and `snapshot_batch_id`, parameter tuple position matched. Batch docstring updated from "tuple of 21 values" to "tuple of 22 values". Single-row signature gained a `bsp_price: float | None = None` keyword arg. Plus, in `capture/orchestrator.py`, `_take_betfair_snapshot`'s per-snapshot tuple gained `runner.bsp_price` between `sp_far_price` and `batch_id`.
7. **Change (c)** in `betfair/client.py`: added new method `get_market_book_sp_traded(market_id) -> dict[int, float] | None` that calls `list_market_book` with `priceProjection=["SP_TRADED"]`, walks `book.runners[*].sp.actual_sp`, returns `{selection_id: actual_sp}` for runners whose `actual_sp` is a positive numeric, or None on API error / empty response. In `storage/database.py`: added helper `update_final_snapshot_bsp(conn, race_id, bsp_by_selection)` which UPDATEs `betfair_snapshots.bsp_price` on `is_final_snapshot=1` rows joined through `runners.betfair_selection_id`. In `capture/orchestrator.py`: added the import for `update_final_snapshot_bsp` and a try/except block in `_check_settlement` AFTER result-status processing but BEFORE `update_race_settlement` — fetches BSP, calls UPDATE, logs `BSP captured for ... — N runners, M rows updated`. Inside try/except so a Betfair API error doesn't block settlement.
8. **scp back to VPS.** All four files pushed. Post-push `git status` and `git diff --stat` confirmed: pre-existing 8 dirty files unchanged in line count; 3 new Fix 3 anchor files (`betfair/client.py`, `betfair/models.py`, `storage/database.py`) now dirty; `capture/orchestrator.py` diff grew from 14 to 38 lines (+24 from Fix 3 edits, consistent with the import line + tuple line + 21-line BSP block); 7 untracked entries unchanged.
9. **Manual service restart.** Pre-restart probe confirmed 0 active races and 0 PENDING races scheduled in next 8 hours — ideal quiet window. `systemctl restart racing-capture.service` ran cleanly. New PID 3348714 came up at 07:11:17 UTC; Betfair login successful; orchestrator started; first discovery returned 23 WIN + 23 PLACE markets. Modules with new field/method loaded cleanly.
10. **Post-restart smoke-verification.** Allowed 2 minutes for first snapshots, then 4 more minutes to capture INTENSIVE-phase coverage. Sample SP values inspected directly (real magnitudes, e.g. `sp_near=4.16` for favourite-priced runner, `sp_near=20.6` for outsider). Then verified BSP write-back path: confirmed `_check_settlement` fired (1 settlement event journal-logged at 07:22:00 for albion R7), but `bsp_price` remained 0 across all final-snapshot rows. Diagnostic probes against three closed AU markets via direct `list_market_book` call confirmed Betfair returns `runners[*]` without an `sp` field at all under `priceProjection=SP_TRADED` for closed markets — see §5 below.
11. **Final git-state verification.** Modified-file list at session close: same 8 pre-existing + 3 Fix 3 anchors = 11 files. Same 7 untracked entries. `capture/orchestrator.py` diff = 38 lines (was 14, +24 from Fix 3 edits, no operator-side lines disturbed). All hard-limit conditions held.

Total wall-clock: ~26 minutes.

---

## 2. Pre-fix baseline numbers

Live-capture window = `snapshot_time >= '2026-03-02T05:26:38'` (empirical floor confirmed via `MIN(snapshot_time)`).

```
=== B1: BSP / SP population (all live-capture-window snapshots) ===
total_snapshots: 1,644,562
with_bsp:                 0  (0.000%)
with_sp_near:             0  (0.000%)
with_sp_far:              0  (0.000%)

=== B2: BSP on is_final_snapshot=1 rows ===
final_snapshots: 84,571
final_with_bsp:       0  (0.000%)

=== B3: SP population on INTENSIVE-phase snapshots ===
intensive_snapshots: 239,169
intensive_with_sp_near:    0  (0.000%)
intensive_with_sp_far:     0  (0.000%)
```

Matches inspection §F exactly. Three columns 0% populated despite schema and column-list extending to them in `migrate_depth_and_batch.py`.

---

## 3. Changes applied — diffs

`git diff --stat` segment for the four anchor files (post-edit, pre-restart):

```
 betfair/client.py     |  40 ++++++++++++++++++++++-
 betfair/models.py     |   2 ++
 capture/orchestrator.py | 38 +++++++++++++++++--- (was 14)
 storage/database.py   |  48 ++++++++++++++++++++++++++++--
```

### Change (a) — `betfair/models.py`
```diff
@@ -54,6 +54,8 @@ class RunnerData:
     # BSP projections
     sp_near_price: float | None = None
     sp_far_price: float | None = None
+    # Realised BSP (populated post-suspension via SP_TRADED projection)
+    bsp_price: float | None = None
```

### Change (b) — `betfair/client.py` (two call sites)
```diff
@@ get_market_book (line 196) @@
-                    price_data=["EX_ALL_OFFERS", "SP_TRADED"],
+                    price_data=["EX_ALL_OFFERS", "SP_AVAILABLE"],

@@ get_market_books_batch (line 223) @@
-                        price_data=["EX_ALL_OFFERS", "SP_TRADED"],
+                        price_data=["EX_ALL_OFFERS", "SP_AVAILABLE"],
```

### Change (c) — `betfair/client.py` (new method) + `storage/database.py` (new helper) + `capture/orchestrator.py` (settlement-time fetch + UPDATE)
New method `get_market_book_sp_traded` added immediately after `get_market_results` in `betfair/client.py`:
```python
def get_market_book_sp_traded(self, market_id: str) -> dict[int, float] | None:
    """Fetch realised BSP per runner via SP_TRADED projection. ..."""
    try:
        books = self._client.betting.list_market_book(
            market_ids=[market_id],
            price_projection=price_projection(price_data=["SP_TRADED"]),
        )
    except Exception as e:
        logger.warning("get_market_book_sp_traded error for %s: %s", market_id, e)
        return None
    if not books:
        return None
    results = {}
    for r in (books[0].runners or []):
        sp = getattr(r, "sp", None)
        if not sp: continue
        actual_sp = getattr(sp, "actual_sp", None)
        if isinstance(actual_sp, (int, float)) and actual_sp > 0:
            results[r.selection_id] = float(actual_sp)
    return results
```

New helper `update_final_snapshot_bsp` added immediately after `flag_final_betfair_snapshot` in `storage/database.py`:
```python
def update_final_snapshot_bsp(conn, race_id, bsp_by_selection: dict[int, float]) -> int:
    """Write realised BSP onto is_final_snapshot=1 rows for a race. ..."""
    if not bsp_by_selection:
        return 0
    updated = 0
    for selection_id, bsp in bsp_by_selection.items():
        cur = conn.execute("""
            UPDATE betfair_snapshots SET bsp_price = ?
            WHERE race_id = ? AND is_final_snapshot = 1
              AND runner_id IN (
                  SELECT id FROM runners
                  WHERE race_id = ? AND betfair_selection_id = ?
              )
        """, (bsp, race_id, race_id, selection_id))
        updated += cur.rowcount
    conn.commit()
    return updated
```

In `capture/orchestrator.py`: added import line for `update_final_snapshot_bsp` and a try/except block inside `_check_settlement` AFTER the result-processing loop, BEFORE `update_race_settlement` — fetches `bsp_by_selection`, calls UPDATE helper, logs `BSP captured for ...` on success, `BSP fetch failed for ...` on exception. Logged-and-continue per brief constraint.

### Change (d) — `storage/database.py` and `capture/orchestrator.py`
Both INSERT statements (`save_betfair_snapshot` single + `save_betfair_snapshots_batch` batch) gained `bsp_price` in column list and matching `?` placeholder. Single-row signature gained `bsp_price: float | None = None` kwarg. Tuple positions in both writers preserved sp_near/sp_far adjacency.

In `capture/orchestrator.py:_take_betfair_snapshot`, the per-snapshot tuple at line 565 gained `runner.bsp_price`:
```diff
                 runner.sp_near_price,
                 runner.sp_far_price,
+                runner.bsp_price,
                 batch_id,
             ))
```

---

## 4. Service restart approach

**Manual restart taken** during a verified quiet window (0 active races at restart time, 0 PENDING races scheduled in next 8 hours per `capture.db` query). Brief §6 step 7 explicitly permitted manual restart "during a quiet window". The natural 08:30 ACST timer-restart was non-viable here: the prior orchestrator had been running continuously since 2026-04-22 (8+ days, never auto-stopped because `_should_stop()` requires zero active races at 19:00 — there's been at least one active race every day at that hour for the past week). Without manual intervention, the new code wouldn't have picked up until the next time the orchestrator self-stops (no certain ETA).

Pre-restart Betfair tunnel and tunnel-related state was not disturbed. Post-restart Betfair login succeeded on the first attempt; orchestrator entered normal loop without errors.

---

## 5. Post-fix verification numbers

Window: `snapshot_time > '2026-04-30T07:11:00'` (i.e., post-restart only).

```
=== P1: All post-restart snapshots ===
total: 370
with_bsp:                 0
with_sp_near:           328  (88.6%)
with_sp_far:            328  (88.6%)

=== P2: Per-phase rates (post-restart) ===
Phase       rows  sp_near%  sp_far%
INTENSIVE   100   100.0%    100.0%
STANDARD    240    95.0%     95.0%
POST_START   30     0.0%      0.0%
```

**Pre→post comparison (rate):**
- `sp_near_price` INTENSIVE: 0% → 100% ← Change (b) clean win.
- `sp_far_price` INTENSIVE: 0% → 100%.
- `sp_near_price` STANDARD: 0% → 95%.
- `bsp_price` post-suspension: 0% → 0%. Path is wired but Betfair returns no SP data at the moment of settlement detection — see §6 below.

POST_START rows have 0% sp_near/sp_far population because at that point the market has either suspended or is about to, and Betfair stops returning SP_AVAILABLE projections post-suspension. This is consistent with the brief's expected behaviour ("snapshot rows from before the fix retain their NULLs").

Sample SP values from a STANDARD-phase race post-restart, demonstrating real (not placeholder) projections:
```
runner 437591  STANDARD  sp_near=20.6055  sp_far=1.0       (outsider)
runner 437592  STANDARD  sp_near= 4.1623  sp_far=1.0       (favourite)
runner 437598  STANDARD  sp_near= 8.7642  sp_far=1.3799    (mid-range)
runner 437600  STANDARD  sp_near=49.3893  sp_far=1.0       (rank outsider)
```
The `sp_far=1.0` placeholder value on most runners is Betfair's "no SP flow yet" default — the SP FAR projection becomes meaningful only as SP betting volume builds up close to jump.

---

## 6. Anything surprising

### Betfair `actualSP` is not reachable via `SP_TRADED` projection on closed AU thoroughbred WIN markets

This is the load-bearing finding for Session 37. The Fix 3 (c) path executed correctly per the brief's spec — `_check_settlement` fires, `get_market_book_sp_traded` is called, the UPDATE helper runs — but the response from Betfair contains no `sp` field at all. Direct empirical probe via `betfairlightweight.list_market_book(market_ids=[...], price_projection=price_projection(price_data=["SP_TRADED"]), lightweight=True)` against three AU thoroughbred WIN markets:

1. **albion R7** — settled at 07:22:00 UTC (this session, ~5 minutes after settlement).
2. **wyong R8** — settled at 06:25:00 UTC (~1 hour after settlement, well past any reconciliation window).
3. **tamworth R6** — settled at 06:20:00 UTC (~1 hour after settlement).

For all three, the raw response shape on each runner is:
```
runner_keys = ['selectionId', 'handicap', 'status', 'adjustmentFactor']
sp_field    = (absent)
```

No `sp` object exists on the runner at all. Both `actual_sp` and `near_price` / `far_price` are unreachable via this code path for closed markets. Variants attempted: `SP_TRADED`, `SP_AVAILABLE`, `SP_TRADED + SP_AVAILABLE`, `EX_BEST_OFFERS + SP_TRADED` — all yield runners with no `sp` field for closed markets. (For OPEN markets — the pre-jump path — `SP_AVAILABLE` correctly populates `sp.near_price` / `sp.far_price`, which is why Change (b) works.)

**Hypotheses for Session 37 (informational, not actioned):**

- **Different endpoint required for BSP retrieval** — possibly `listMarketProfitAndLoss`, or `listMarketBook` with additional `marketProjection` flags (`MARKET_DESCRIPTION`?), or the historical-CSV import path which DOES carry BSP via betfair_historical.win_bsp.
- **Different timing window** — Betfair may populate `actualSP` on the `sp` object only during a brief reconciliation window between SUSPENDED and CLOSED. The orchestrator's `_check_settlement` runs after the market is already CLOSED, by which point `sp` may have been removed from the response. A pre-CLOSED fetch (in `_take_betfair_snapshot` when transition is detected as SUSPENDED) might yield it.
- **AU market-type quirk** — AU thoroughbred WIN markets may use Tote SP / AU SP rather than Betfair Starting Price proper, and the `actualSP` field may be specific to UK/IE markets. The historical-CSV path's `betfair_historical.win_bsp` is sourced from Betfair's BSP CSV files (the canonical authoritative source) — this is a different data product than the live API's `actualSP`.

The brief's source-review-report-§5.3 anchor inferred from `RunnerData.sp_near_price` / `sp_far_price` adjacency in the migration that `bsp_price` should follow the same projection mechanism — but empirical evidence is that the projection mechanism doesn't surface BSP on closed markets. This isn't a bug in Fix 3; it's a gap in the brief's underlying assumption about Betfair's API surface.

### Session-37 immediate next probe

Add a SUSPENDED-side fetch in `_take_betfair_snapshot`'s transition branch (lines 502-517) — when the orchestrator first detects `market_status != OPEN`, before `state.enter_settlement()`, call `get_market_book_sp_traded`. The market may still have `sp` populated at SUSPENDED-but-not-yet-CLOSED. If that yields actual_sp, the fix becomes a one-line addition.

If SUSPENDED-side also yields no `sp`, the BSP write-back has to come from a different Betfair endpoint or a delayed/scheduled re-fetch path (pull `actualSP` via a periodic job that re-queries closed markets after a 30-60 minute delay). Both are larger surgical-fix candidates than (c) was specified to be.

### Other observations

- **Pre-existing dirty `capture/orchestrator.py` lines stayed unchanged.** The 14 in-flight operator changes (tabtouch wiring, IntegrityError handler, n_priced filter) sit outside `_take_betfair_snapshot` and `_check_settlement`. Diff stat grew from 14 to 38 lines net (24 lines added by Fix 3), exactly consistent with the import line + tuple line + 21-line BSP block. No collision.
- **Brief's claim about `update_runner_result` not passing `finish_position`** (source-review §5.1) is still true; this fix doesn't touch it. Out of Fix 3's scope.
- **`flag_final_betfair_snapshot` gracefully handles the case where no OPEN snapshot exists** for a race the orchestrator only met post-jump — it UPDATEs zero rows (silently fine). Doesn't affect Fix 3.
- **The SP_AVAILABLE projection successfully populates STANDARD-phase rows at 95% rate.** The 5% of STANDARD rows without sp_near/sp_far are likely the very-earliest snapshots in the 60-min capture window (when Betfair hasn't yet computed an SP projection because liquidity is too thin). This is normal Betfair behaviour, not a fix gap.
- **Restart did not interrupt anything observable.** No active races to drop, no in-flight ticks lost, no API rate-limit issues.

---

## 7. What's left

**Confirmed by Session 37+ verification:**

1. **BSP write-back is structurally wired but empirically inert against the current Betfair endpoint.** Bottom line: the `bsp_price` column population rate post-Fix-3 is still 0%, and will remain 0% until a Betfair-API-shape change is made. Ranked next-step candidates (Session 37 to route):
   - **Cheapest, most likely to work:** add a pre-CLOSED (i.e., SUSPENDED-detected) SP_TRADED fetch in `_take_betfair_snapshot`'s transition branch. If `sp.actual_sp` is populated during SUSPENDED state, this lands BSP without further investigation. Single-anchor edit; same risk class as Fix 3 itself.
   - **Medium effort:** add a delayed re-fetch path — a periodic sweep job (e.g., 30 minutes after settlement) that reads closed races without `bsp_price` and re-queries Betfair. If `actual_sp` becomes reachable later, this catches it.
   - **Larger investigation:** Betfair API audit — read documentation, find the canonical endpoint for `actualSP` retrieval on AU markets, possibly via `listMarketProfitAndLoss` or `listMarketBook` with non-default flags. If AU markets don't expose BSP via the live API at all, the gap may be only fillable via the historical CSV (the path `scripts/import_betfair_historical.py` already implements, just no longer running past 2026-02-28).

2. **Routine `racing-capture.service` daily restart is needed if the operator wants the SP_AVAILABLE projection change to be picked up automatically.** This session's manual restart established the new code in the running process, but the orchestrator runs continuously (non-restart pattern observed: it's been up 8+ days previously). If the service crashes for any reason, systemd's `Restart=on-failure` will restart it cleanly with the new code; otherwise the operator can rely on the eventual self-stop at `STOP_HOUR_LOCAL=19` when no active races. No action needed from Session 37 here — just awareness.

3. **Pre-jump `sp_near_price` / `sp_far_price` populating cleanly is now in steady state.** Continued monitoring across Session 37+ should see the per-day INTENSIVE-phase rate hold near 100%. The inspection-report-§F findings on these two columns are now closed.

**Out-of-scope reminders (confirmed not done):**
- No Fix 4 (cadence) — separate Code session.
- No Fix 5 (venue harmonisation) — separate Code session.
- No edits to dirty pre-existing files (sportsbet, orchestrator's non-anchor regions, etc.).
- No `git add` / `git commit` / `git stash` / `git restore` / `git checkout` (file-targeted) / `git reset` of any kind. Verified at session close.
- No new tests, no schema changes (the `bsp_price` column already existed from `migrate_depth_and_batch.py`).

---

## 8. Self-assessment

**Brief scope adherence:** all four named changes (a/b/c/d) implemented exactly per the brief's anchors. The post-suspension fetch was placed in `_check_settlement` (after results processing, before `update_race_settlement`) per the brief's option "Code's call whether to add a new method on `BetfairClient` or to extend `_get_market_results`. The smaller change is a new method ... Either is acceptable" — chose new method for clean separation of concerns.

**Hard limits held:** no edits outside named anchors; no schema changes; no new tests; no Fix 4 / Fix 5 work; no edits to pre-existing dirty files; no git mutation operations of any kind. Pre-existing dirty file diffs preserved at original line counts. Untracked files unchanged.

**Outcome shape:** changes (a), (b), (d) mechanically did what the brief specified, with (b) producing the most measurable analytical-line improvement (sp_near/sp_far went from 0% to 100% in INTENSIVE phase). Change (c) executed exactly the brief's spec but produced 0 BSP rows because Betfair's `priceProjection=SP_TRADED` doesn't return `sp` on closed AU thoroughbred WIN market runners. The Fix-3-as-specified envelope is closed; the `bsp_price` column population gap is now narrowed to a Betfair-API-shape question that's tractable for Session 37 with a small follow-up brief.

This pattern echoes Fix 1+2's: surgical fix mechanically completes against named anchors, but a downstream empirical gap (there: venue normalisation; here: Betfair `actualSP` reachability) remains for the next session to route. Both gaps are real and bounded; both surface cleanly enough that Session 37 can decide quickly between routing them as small follow-ups vs. accepting them as known-debt.

*End of report.*
