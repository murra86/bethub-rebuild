# VPS drift check — Session 36

**Run:** 2026-04-30 16:08 ACST.
**Purpose:** characterise the dirty git working tree on `/home/racing/racing-data-capture/` (VPS) before drafting Fix 3 brief.
**Outcome:** drift is benign for Fix 3 purposes — last commit is 2026-03-04, all dirty changes since are in-flight legitimate work, oldest mtime 2026-03-11, newest 2026-04-09. None of the dirty files block Fix 3's anchors at the line level. Fix 3 brief carries explicit hard limits to leave dirty state untouched.

---

## 1. Reachability

VPS up. Tunnel up. `uptime` reports 59 days continuous since reboot. Load average ~0.

## 2. Tracked tree last moved

**Last commit: `5f71488` on 2026-03-04.** Branch `master`. Nine commits total, all dated 2026-03-03 / 2026-03-04 — initial deployment burst. **Nothing has been committed since 2026-03-04.** All eight modified-file changes since then live as uncommitted working-tree edits.

## 3. Dirty file inventory

```
bookmakers/base.py            +/-   4 lines   (mtime 2026-03-20)
bookmakers/pointsbet.py       +     11 lines  (mtime 2026-03-11)
bookmakers/sportsbet.py       +/-  226 lines  (mtime 2026-03-20)
capture/orchestrator.py       +/-   14 lines  (mtime 2026-04-09)
config/settings.py            +/-    4 lines  (mtime 2026-03-20)
matching/race_matcher.py      +     1 line    (mtime 2026-03-30)
scripts/health_check.py       +    21 lines   (mtime 2026-03-20)
scripts/liveness_check.py     +/-   2 lines   (mtime 2026-03-29)
```

Plus untracked subtree (all dated similar window):

```
api/                          ← FastAPI service: __init__.py, main.py, db.py, models.py
api/routes/                   ← health.py, races.py, snapshots.py, results.py
bookmakers/tabtouch.py        ← new TABtouch scraper module
```

(Plus `__pycache__/` dirs — compiled bytecode, ignore.)

## 4. What the changes are, plain language

The diffs tell a coherent story:

- **`bookmakers/tabtouch.py` (new).** TABtouch added as a new scraper. Source-review report Session 33 listed eight bookmaker scrapers; this would make nine.
- **`capture/orchestrator.py`.** Wiring tabtouch into the orchestrator's discover/fetch dispatch. Plus two non-tabtouch additions: a `sqlite3.IntegrityError` handler that logs and removes the offending race rather than re-trying (defensive); and a fix to `n_priced` count to filter scratched runners.
- **`config/settings.py`.** Re-enables Sportsbet (`"sb"` removed from `DISABLED_BOOKMAKERS`, added to `PROXY_BYPASS_BOOKMAKERS`). Probably accompanies the substantial Sportsbet rewrite below.
- **`bookmakers/sportsbet.py`.** 226-line rewrite. Likely the work that produced the venue-cleaning logic the surgical-fix-1+2 report's §5 identified — strips sponsor prefixes etc. Predates this session's discovery.
- **`bookmakers/pointsbet.py`, `bookmakers/base.py`.** Smaller scraper-side adjustments.
- **`matching/race_matcher.py`.** Single line — `tabtouch_race_id` added to the bookmaker-id field map. Pure tabtouch wiring.
- **`scripts/health_check.py`, `scripts/liveness_check.py`.** Health/liveness tweaks. Health check gained 21 lines; liveness one-line touch.
- **`api/` subtree (untracked).** A FastAPI service with routes for `health`, `races`, `snapshots`, `results`. Possibly a read-side API for v3 to call instead of (or alongside) direct sqlite3 reads. Adjacent to but not yet integrated with `vps_client` design.

## 5. Whose work is this?

**Operator's, almost certainly.** This is in-flight VPS-side build work that pre-dates the v3 rebuild governance arc and was never folded into the rebuild folder's session log. The mtime spread (2026-03-11 → 2026-04-09) is consistent with month-of-March-and-early-April operator-side work; the rebuild project itself only started mid-April.

The work is real and substantial — TABtouch scraper, FastAPI read-side, Sportsbet venue cleaner. Not noise, not a security concern, not a Code-side accident.

## 6. Implications for Fix 3

**Fix 3 anchors per source-review report §5.3 (BSP write-back) are:**

- `betfair/client.py` — add BSP / sp_near / sp_far field reads from MarketBook responses.
- `betfair/models.py` — extend the snapshot model dataclass with the three new fields.
- `capture/orchestrator.py` — pass the three fields through `save_snapshot` calls.
- `storage/database.py` — extend `save_betfair_snapshot()` insert/update to include the three fields.

**Cross-check against dirty list:**

- `betfair/client.py` — clean. Not in dirty list.
- `betfair/models.py` — clean. Not in dirty list.
- `capture/orchestrator.py` — **DIRTY** with 14 lines of in-flight changes. Fix 3 must edit this file. Risk: Fix 3 edits could collide with operator's in-flight changes if line numbers have shifted.
- `storage/database.py` — clean. Not in dirty list.

**Single point of risk: `capture/orchestrator.py`.** Examining the diff: the in-flight changes touch the bookmaker dispatch tables (lines 35, 84, 332-340, 370-378), the per-race exception handler (line 397+), the snapshot summary call (line 748+), and the bookmaker fetch dispatcher (line 800+). **None of these lines touch the `save_snapshot` write path that Fix 3 needs to extend.**

The Betfair write path passes through `_capture_betfair_snapshot` (per source-review report) which is at a different position in the file. Fix 3 should be able to land its edits without collision, but the brief MUST instruct Code to:

1. Verify pre-edit that the dirty changes are still in place and not yet committed.
2. Treat the dirty file as the working source — read with `git diff` mental-overlay applied, edit the actual file in its current state.
3. After Fix 3 edits land, NOT run `git add .` or `git commit` — leave the working tree dirty as found.
4. After Fix 3, re-run `git status` to confirm only Fix 3's intended files are additionally dirty (or that orchestrator.py's diff has grown, not shrunk).

## 7. Implications for Fix 5 (venue harmonisation)

**`bookmakers/sportsbet.py` is the file that already implements the venue cleaner Fix 5 needs to lift into `matching/race_matcher.normalise_venue`.**

The 226-line sportsbet.py rewrite is the source. `matching/race_matcher.py` is also dirty — but only with a single-line tabtouch addition unrelated to venue normalisation. So Fix 5 still has a clean line surface in `race_matcher.py` for the venue-harmonisation edit.

When Fix 5 lands, the source for the lift is the dirty (uncommitted) sportsbet.py. The brief should reference this explicitly so Code reads from the working tree, not from any hypothetical clean HEAD version.

## 8. Implications for Fix 4 (cadence)

Fix 4 anchors per source-review report §5.2 are `config/settings.py` (lower `DISCOVERY_INTERVAL`), `capture/orchestrator.py` (fast-discovery sweep, `_register_race` silent-drop log).

Both files are dirty. Same handling pattern as Fix 3 — verify dirty state preserved through and after the fix.

## 9. Recommendation for the surgical-fix arc

**Do not commit or stash the operator's in-flight work as part of any surgical fix brief.** That's the operator's call to make in their own time — possibly never, possibly via a separate session that reviews and commits or reverts each change. Treating committing as "tidy housekeeping" inside a Code session would discard work the operator may want to review first.

**Each subsequent surgical-fix brief carries an "honour the dirty tree" hard limit:** read files in their current working-tree state, edit them as such, do not run `git add`, `git commit`, `git stash`, or `git restore`. Verify post-edit that no accidental tree changes were made beyond the fix's named anchors.

**Add a parking-lot item to WIP §15** alongside Decodo and digest-review: "VPS in-flight work review — eight modified files plus untracked `api/` subtree and `bookmakers/tabtouch.py` on `/home/racing/racing-data-capture/`, dating from 2026-03-11 to 2026-04-09. Substantial real work (TABtouch scraper, FastAPI read-side, Sportsbet venue cleaner). Operator-side review needed to commit/revert/integrate. Not gating DR-029."

---

*End of drift check.*
