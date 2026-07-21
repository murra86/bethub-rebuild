# BSP write-back fix — VPS drift check

**Captured:** 2026-05-03 06:35 ACST (Session 53).
**Purpose:** Pre-flight diagnostic for the BSP write-back fix brief, per `bethub-brief-drafting` skill Step 2 precedent (Session 36's Fix 3 brief established the dirty-tree handling pattern). Captures VPS working-tree state so the brief's hard limits cover real, current dirty regions rather than hypothetical ones.

## Repo state

- **Repo:** `/home/racing/racing-data-capture` on VPS (`root@187.77.183.9`).
- **HEAD:** `5f71488006a1443021aefbc8a97e2a73d638c37c` ("Add /racing/results/today and /racing/results/{race_id} endpoints").
- **Working tree:** dirty. 11 modified files + 7 untracked files. Matches `current_state.md` "Open items" §16 baseline (WIP §16 — VPS in-flight work).

## Modified files

```
 M betfair/client.py
 M betfair/models.py
 M bookmakers/base.py
 M bookmakers/pointsbet.py
 M bookmakers/sportsbet.py
 M capture/orchestrator.py
 M config/settings.py
 M matching/race_matcher.py
 M scripts/health_check.py
 M scripts/liveness_check.py
 M storage/database.py
```

## Untracked files

```
?? api/__init__.py
?? api/db.py
?? api/routes/__init__.py
?? api/routes/health.py
?? api/routes/races.py
?? api/routes/snapshots.py
?? bookmakers/tabtouch.py
```

## Files this brief touches

The BSP write-back fix touches three files, all already in the modified-list:

1. **`betfair/client.py`** — uncommitted dirty work includes the entire `get_market_book_sp_traded()` method (lines 187-220) added by Fix 3 (Session 37). The brief's edit anchor is the projection set inside this method (line 200, currently `price_data=["SP_TRADED"]`). Editing it is a minor extension to the existing uncommitted batch.

2. **`capture/orchestrator.py`** — uncommitted dirty work includes the settlement-time BSP fetch block (lines 904-927) added by Fix 3. The brief's edit anchors are inside this same block. Same coherent batch.

3. **`storage/database.py`** — uncommitted dirty work includes the `update_final_snapshot_bsp()` function (lines 691-722) and the `bsp_price` parameter additions to `save_betfair_snapshot()` and `save_betfair_snapshots_batch()` (lines 508-570). The brief's edit anchors are inside `update_final_snapshot_bsp()`. Same coherent batch.

## Diff intersection assessment

**No conflict.** The three files this brief touches are dirty, but the dirty regions in those files **are** the Fix 3 BSP scaffolding — exactly the code we are fixing. We're not editing around someone else's in-flight work; we're refining work that's already part of a coherent uncommitted batch.

## Hard-limits implications for the brief

- Edit only named anchors per Session 36 pattern.
- Run `git diff <file>` after each edit to confirm only intended changes were added (validates against accidental drift into other dirty regions of the same files).
- `git status` at session close should show the same 11 modified + 7 untracked file list (no new files, no removed entries, no untracked → tracked transitions).
- No git mutation operations: no `add`, `commit`, `stash`, `restore`, `checkout` (file-targeted), `reset`.

## Untouched files note

None of the untracked files (`api/*`, `bookmakers/tabtouch.py`) are touched by this brief. The remaining modified files (`bookmakers/base.py`, `bookmakers/pointsbet.py`, `bookmakers/sportsbet.py`, `betfair/models.py`, `config/settings.py`, `matching/race_matcher.py`, `scripts/health_check.py`, `scripts/liveness_check.py`) are also untouched.
