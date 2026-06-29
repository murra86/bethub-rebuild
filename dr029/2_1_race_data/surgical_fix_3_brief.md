# DR-029 §2.1 surgical fix — brief for Code session 2 (Fix 3, BSP write-back)

**Drafted:** Session 36 (2026-04-30 ACST), for hand-off to Claude Code.
**Source authority:** `dr029/2_1_race_data/source_review_report.md` §5.3 plus the §"Anything surprising" entry on the orphan `bsp_price` column.
**Working-tree context:** `dr029/2_1_race_data/vps_drift_check.md` (Session 36 diagnostic) — VPS git tree carries eight uncommitted operator-side changes plus an untracked `api/` subtree; one of Fix 3's anchor files (`capture/orchestrator.py`) is dirty. This brief carries explicit hard limits on dirty-tree handling.
**Governing decisions:** DR-029 (active arc, surgical-fix execution); DR-027 / DR-028 (cross-DB discipline — this fix is entirely VPS-side, no cross-DB boundary surface touched); DR-021 (timestamp discipline, ACST anchoring).

---

## 1. What this is, what this isn't

**This is** a single bounded Code session executing one surgical fix against the VPS analytical pipeline at `/home/racing/racing-data-capture/` on `root@187.77.183.9`. The fix resolves Cluster 4's BSP-write-back finding from the DR-029 §2.1 inspection report (zero rows of 1.6M `betfair_snapshots` carry `bsp_price`, `sp_near_price`, or `sp_far_price` data, despite the schema columns existing). Per the source-review report §5.3:

- The `bsp_price` schema column exists but is not in any INSERT statement — orphan column.
- `RunnerData` (`betfair/models.py`) has `sp_near_price` / `sp_far_price` fields but **no `bsp_price` field**.
- The pre-jump `betfair/client.py` price-projection request asks for `["EX_ALL_OFFERS", "SP_TRADED"]` — but `SP_TRADED` only returns reconciled SP after market suspension. Pre-jump SP projections need `SP_AVAILABLE` instead.
- The post-suspension settlement path (`_check_settlement` → `get_market_results`) doesn't fetch SP at all — `list_market_book` is called with no `price_projection`, so no SP / BSP comes back.
- Result: `sp_near_price` and `sp_far_price` writers are wired (orchestrator writes them, INSERT writes them) but the upstream Betfair calls don't return values for those fields. `bsp_price` isn't written even if Betfair returned it.

**Fix 3** lands four additive changes:

- **(a)** Extend `RunnerData` with a `bsp_price` field. Default None.
- **(b)** Switch the pre-jump price projection from `SP_TRADED` to `SP_AVAILABLE` (so `r.sp.near_price` / `r.sp.far_price` populate while market is OPEN).
- **(c)** Add a post-suspension SP fetch — when `_take_betfair_snapshot` detects market transition OPEN→SUSPENDED or SUSPENDED→CLOSED, fetch `list_market_book` with `price_projection=["SP_TRADED"]` once, capture the actual realised BSP from `r.sp.actual_sp`, and write it onto a final post-settlement snapshot row.
- **(d)** Extend the writer's INSERT column list to include `bsp_price` and add the `bsp_price` value to the per-snapshot tuple in `_take_betfair_snapshot`.

**This isn't** a rebuild, a refactor, or a fix for adjacent debt. The three pieces of named debt (no test coverage, no migration framework, monolithic orchestrator file) are explicitly out of scope. Fix 4 (cadence, Cluster 2 §5.2) is a separate Code session. Fix 5 (venue harmonisation + retroactive race-key merge — surfaced in Fix 1+2 report §5) is a separate Code session.

**This isn't** a fresh diagnosis either. The source-review report has done the file-and-line analysis; the surgical-fix-1+2 report further clarified that Cluster 1 is venue-merge-bound (separate from this fix entirely). Code's job here is execution against named anchors plus empirical verification — not re-investigation.

---

## 2. Why this fix is independent of Cluster 1's residual

The surgical-fix-1+2 report §5 found Cluster 1 partially resolved: `runners.finish_position` is now flowing in, but landing on orphan race rows that don't merge with the Betfair-side rows. Fix 5 will close that out separately.

**Fix 3 doesn't depend on Cluster 1's full resolution.** The BSP / sp_near / sp_far fields land on `betfair_snapshots` rows, which are keyed `(race_id, runner_id, snapshot_time)` against the Betfair-side race rows directly. These snapshot rows already have a clean `betfair_selection_id` join all the way through (`runners.betfair_selection_id` was the populated half pre-Fix-1). The Racing API merge problem doesn't touch Fix 3 at all.

In other words: when Fix 5 lands and the venue-merge gets harmonised, the BSP / sp_near / sp_far data Fix 3 writes will already be sitting on the right Betfair-side rows. Nothing replays.

---

## 3. Pre-reads (in order)

1. This brief.
2. `dr029/2_1_race_data/vps_drift_check.md` — full read. Characterises the dirty git working tree on the VPS. Critical for §10's hard limits.
3. `dr029/2_1_race_data/source_review_report.md` §5.3 in full (the load-bearing source-of-truth for the anchors below) plus the §"Anything surprising" entry on the orphan `bsp_price` column.
4. `dr029/2_1_race_data/surgical_fix_1_2_report.md` §1 + §5 (one-page read; ground for "what's just been done, what's been left for Fix 5").

That's the full required-read set. Reference-only:

- `dr029/2_1_race_data/inspection_report.md` §F (BSP / sp_near / sp_far 0% population is the empirical baseline this fix moves). Read on demand if a verification number needs grounding.
- `dr029/dr029_scope.md` §2.1 close entry plus §2.4 carry-in (the framing this brief executes under). Operator-Claude already has this; Code does not need it for the work.
- The Betfair Exchange API documentation for `priceProjection` and `MarketBook.runners.sp` is referenced inline in §5 below; Code may pull it as needed but the source-review report's analysis is the authoritative read.

---

## 4. VPS access — read-write

Distinct from Session 33's source-review (read-only), parallel to Session 35's Fix 1+2 brief (read-write). This session executes against the live VPS:

- **SSH:** `root@187.77.183.9`. Tunnel up per Fix 1+2 report § "What was done" #1; if it's not at session open, restart per the launchd unit (Cluster 6 fix, parked).
- **Project root:** `/home/racing/racing-data-capture/`.
- **Service user:** `racing`. Service restart for the orchestrator (`racing-capture.service`) is daily at 08:30 ACST; manual restart available via `systemctl restart racing-capture.service` if Code wants to verify Fix 3 behaviour against a running pipeline mid-session. Recommended: leave the service alone, let the next 08:30 restart pick up the changes naturally; verification queries against `capture.db` post-restart confirm the fix lands.
- **`capture.db`:** verification queries should use `sqlite3 'file:/home/racing/racing-data-capture/data/capture.db?mode=ro'` for read confirmation. Do not write to the DB directly; the changes flow through normal pipeline writes once the service picks up the new code.
- **No code-side staging:** edits land directly in the VPS source tree via SSH. There is no separate dev environment.

### 4.1 Working-tree state (load-bearing — read this carefully)

The VPS git working tree is **dirty** with eight modified files plus untracked `api/` subtree and `bookmakers/tabtouch.py`. Last commit is **2026-03-04**; the dirty changes range in mtime from 2026-03-11 to 2026-04-09. This is **legitimate operator-side in-flight work** (TABtouch scraper addition, FastAPI read-side build, Sportsbet venue-cleaner rewrite, defensive orchestrator additions, health-check expansion, Sportsbet re-enablement). It is NOT to be touched.

**Of Fix 3's four anchor files:**

- `betfair/client.py` — clean.
- `betfair/models.py` — clean.
- `capture/orchestrator.py` — **DIRTY with 14 lines of in-flight changes.** Diff lives at lines around 35, 84, 332-340, 370-378, 397-403, 748, 800-810. Fix 3's edit target (`_take_betfair_snapshot` around line 502-517 plus the snapshot tuple build at line 537-565) does **not** intersect with the dirty changes. Code must verify line numbers freshly before editing — the dirty changes shift positions slightly.
- `storage/database.py` — clean.

**Hard rule:** Code reads files in their working-tree state, edits the named-anchor regions only, and leaves all other dirty content as-is. No `git add`, no `git commit`, no `git stash`, no `git restore`. See §10 for the full hard-limits set.

---

## 5. Fix 3 — the four changes

### 5.1 What the existing code does

Per source-review report §5.3:

- `betfair/models.py:42-58` defines `RunnerData` with fields including `sp_near_price` and `sp_far_price` but **no `bsp_price`**.
- `betfair/client.py:_book_to_snapshot` (lines 264-340) constructs `RunnerData` instances from MarketBook responses; reads `r.sp.near_price` and `r.sp.far_price`.
- `betfair/client.py:228-234` `get_market_book` requests `price_projection(price_data=["EX_ALL_OFFERS", "SP_TRADED"])`. **`SP_TRADED` only returns post-suspension reconciled SP** — pre-jump it returns nothing in the `sp.near_price` / `sp.far_price` fields. The right pre-jump projection is `SP_AVAILABLE`.
- `capture/orchestrator.py:537-565` (`_take_betfair_snapshot`) builds the per-snapshot tuple. Position 19 = `runner.sp_near_price`, position 20 = `runner.sp_far_price`. **No slot for `bsp_price`.**
- `storage/database.py:467-498` `save_betfair_snapshots_batch` INSERT column list contains 21 columns. **`bsp_price` is not in the list** — orphan column.
- `_check_settlement` (`orchestrator.py:865-914`) calls `client.get_market_results(market_id)` which delegates to `betfair/client.py:_get_market_results` (lines 158-180) — `list_market_book` with no `price_projection`. **No post-suspension SP fetch happens.**

### 5.2 Change (a) — add `bsp_price` field to `RunnerData`

**File:** `betfair/models.py`.
**Anchor:** the `RunnerData` dataclass / model around lines 42-58.
**Change:** add field `bsp_price: float | None = None` (or the project's existing nullable-numeric idiom; check `sp_near_price` / `sp_far_price` field declarations and match the style).

### 5.3 Change (b) — switch pre-jump price projection from `SP_TRADED` to `SP_AVAILABLE`

**File:** `betfair/client.py`.
**Anchor:** `get_market_book` price_projection request, lines 228-234.
**Change:** replace `price_data=["EX_ALL_OFFERS", "SP_TRADED"]` with `price_data=["EX_ALL_OFFERS", "SP_AVAILABLE"]`.

**Rationale:** Betfair Exchange API behaviour:
- `SP_AVAILABLE` returns SP projections (`r.sp.near_price` / `r.sp.far_price`) while the market is OPEN. These are the projections that move with bet flow leading up to the off.
- `SP_TRADED` returns reconciled SP and matched amounts, populated only after the market suspends and SP is reconciled. Pre-jump it returns empty.

The downstream code (`_book_to_snapshot` reading `r.sp.near_price` / `r.sp.far_price`) is correct; the issue is only the request.

### 5.4 Change (c) — add post-suspension SP fetch

**Files:** `betfair/client.py` and `capture/orchestrator.py`.
**Anchors:**
- `betfair/client.py` — add a new method (e.g., `get_market_book_sp_traded(market_id)`) or extend `_get_market_results` to optionally accept a `price_projection` argument.
- `capture/orchestrator.py:_take_betfair_snapshot` (lines 502-517) — detect the OPEN→SUSPENDED transition (when `market_status` flips from OPEN to SUSPENDED on the current tick) and trigger a one-shot SP_TRADED fetch. Capture `r.sp.actual_sp` (or whichever field Betfair returns the realised BSP in — verify by inspecting the response object structure once the call lands).

**Constraint:** the post-suspension fetch must be one-shot per race per session — not polled, not retried, not repeated. Fire it once on the OPEN→SUSPENDED transition. If the call fails (rate-limit, network error), log and move on; do not block settlement processing.

**Result:** the realised BSP value lands on a final-snapshot row alongside the suspension-time best-back / best-lay / etc. Schema column `bsp_price` already exists; no DDL needed.

**Implementation note:** Code's call whether to add a new method on `BetfairClient` or to extend `_get_market_results`. The smaller change is a new method; the cleaner long-term shape is to consolidate. Either is acceptable — pick whichever fits the existing call-site idiom.

### 5.5 Change (d) — extend the writer's INSERT column list and snapshot tuple

**Files:** `storage/database.py` and `capture/orchestrator.py`.
**Anchors:**
- `storage/database.py:467-498` `save_betfair_snapshots_batch` INSERT column list — add `bsp_price` to the column list (preserve column order in the database; `bsp_price` already exists at the schema's column 19 per `database.py:137`). Match the column position in the placeholders / parameter tuple.
- `capture/orchestrator.py:537-565` `_take_betfair_snapshot` tuple build — add `runner.bsp_price` to the per-snapshot tuple at the position matching the INSERT's column list.

**Constraint:** preserve the existing column order in the schema. If `bsp_price` is at schema column 19 and the current INSERT goes through 21 columns, the new INSERT goes through 22 columns with `bsp_price` slotted in at the position consistent with the schema. Match `database.py`'s schema column order — that's the authoritative ordering reference.

### 5.6 Anchors summary (all four files)

- `betfair/client.py` — 1× projection-string change at lines 228-234, plus 1× new method or extended `_get_market_results` for SP_TRADED post-suspension fetch.
- `betfair/models.py` — 1× new field on `RunnerData` at lines 42-58.
- `capture/orchestrator.py` — 1× transition-detection branch in `_take_betfair_snapshot` (lines 502-517) calling the new SP_TRADED fetch on OPEN→SUSPENDED, plus 1× tuple addition at lines 537-565. **DIRTY FILE** — see §4.1.
- `storage/database.py` — 1× INSERT column-list addition at lines 467-498 plus matching parameter-tuple position.

---

## 6. Sequencing within the Code session

Suggested order — Code may deviate if a different sequencing is operationally cleaner:

1. **Verify VPS reachability and current state.** SSH in, confirm tunnel up, confirm project root contents match expected. **Run `git status` to confirm working tree matches the Session 36 drift-check snapshot** — eight modified files (`bookmakers/{base,pointsbet,sportsbet}.py`, `capture/orchestrator.py`, `config/settings.py`, `matching/race_matcher.py`, `scripts/{health_check,liveness_check}.py`) plus untracked `api/` subtree files and `bookmakers/tabtouch.py`. If the working tree differs from this snapshot, surface as a finding and stop — that means something has shifted between sessions.
2. **Pre-fix verification queries.** Capture baseline numbers for `bsp_price`, `sp_near_price`, `sp_far_price` population across `betfair_snapshots` over the live-capture window. These are the before-numbers Fix 3's verification compares against.
3. **Change (a)** — add `bsp_price` field to `RunnerData`. Smallest atomic change; doesn't break anything alone (default None means nothing writes a non-None value yet).
4. **Change (b)** — switch projection from `SP_TRADED` to `SP_AVAILABLE`. Pre-jump SP projections start populating immediately on next service tick.
5. **Change (d)** — extend INSERT column list and snapshot tuple. With (a) in place, `bsp_price` field exists on the dataclass; the writer can now reference it (default None until (c) lands).
6. **Change (c)** — post-suspension SP_TRADED fetch. Last because it's the most involved; lands cleanly when the rest is in place.
7. **Restart `racing-capture.service`** OR wait for the next 08:30 ACST natural restart. If restarting manually, do so during a quiet window (low active-race count); the orchestrator's start-up rebuilds the in-memory races dict from current Betfair catalogue, so no state is lost beyond the in-flight tick.
8. **Post-fix smoke verification.** Wait 5-10 minutes after restart, then re-run the §7 baseline queries against a recent snapshot window. Confirm `sp_near_price` / `sp_far_price` are populating non-NULL for races currently in INTENSIVE or STANDARD phase. (BSP write-back can only be confirmed after a market actually transitions OPEN→SUSPENDED — which depends on a race jumping during the session window. Code should not block on this; surface "BSP write-back path not yet exercised in-session, will populate from next race jump" as the verification status.)

If any change surfaces an unexpected interaction (a downstream consumer reading `RunnerData` that doesn't tolerate the new field; a Betfair API rate-limit response from the post-suspension fetch path; the column-position consistency between schema and INSERT statement breaks), surface as a finding and stop.

---

## 7. Empirical verification

### 7.1 Pre-fix baseline (captured before any edits)

```sql
-- Baseline: BSP / SP population across betfair_snapshots over live-capture window
SELECT
  COUNT(*) AS total_snapshots,
  SUM(CASE WHEN bsp_price IS NOT NULL THEN 1 ELSE 0 END) AS with_bsp,
  SUM(CASE WHEN sp_near_price IS NOT NULL THEN 1 ELSE 0 END) AS with_sp_near,
  SUM(CASE WHEN sp_far_price IS NOT NULL THEN 1 ELSE 0 END) AS with_sp_far
FROM betfair_snapshots
WHERE snapshot_time >= '<live_capture_start>';

-- Baseline: BSP populated on final-snapshot rows only (target population for BSP)
SELECT
  COUNT(*) AS final_snapshots,
  SUM(CASE WHEN bsp_price IS NOT NULL THEN 1 ELSE 0 END) AS final_with_bsp
FROM betfair_snapshots
WHERE is_final_snapshot = 1
  AND snapshot_time >= '<live_capture_start>';

-- Baseline: SP population in INTENSIVE phase (target for sp_near / sp_far)
SELECT
  COUNT(*) AS intensive_snapshots,
  SUM(CASE WHEN sp_near_price IS NOT NULL THEN 1 ELSE 0 END) AS intensive_with_sp_near,
  SUM(CASE WHEN sp_far_price IS NOT NULL THEN 1 ELSE 0 END) AS intensive_with_sp_far
FROM betfair_snapshots
WHERE snapshot_phase = 'INTENSIVE'
  AND snapshot_time >= '<live_capture_start>';
```

Use empirical `live_capture_start` = `MIN(snapshot_time) FROM betfair_snapshots` (per Session 35 brief §5.2 pattern) — confirmed `2026-03-02 05:26 UTC` per the surgical-fix-1+2 report.

### 7.2 Post-fix expected state

- **`sp_near_price` and `sp_far_price`** populated non-NULL for the majority of post-fix INTENSIVE-phase snapshots. Pre-fix rate was 0%; post-fix rate should be high (>80%) for INTENSIVE snapshots after the service restart, depending on Betfair's SP-projection-availability cadence per market.
- **`bsp_price`** populated on `is_final_snapshot=1` rows where the post-suspension fetch fired successfully. Cannot be quantified mid-session because it depends on races jumping during the session window. Verify by inspecting the journal for SP_TRADED fetch log lines and querying for one or two completed races' final snapshots post-jump.
- **Pre-fix rows unchanged.** Existing snapshots from before the fix retain their NULLs — Fix 3 doesn't backfill historical snapshots. Future snapshots from service restart onwards carry the new fields.

### 7.3 Verification rerun

Re-run the §7.1 queries post-fix for snapshots after the restart timestamp. Report side-by-side with pre-fix. Note that the volumes won't be comparable directly (post-fix window is hours, pre-fix is 60 days) — focus on the population RATE for INTENSIVE snapshots in the post-restart window vs the 0% baseline.

For BSP specifically, surface as a Session-37 verification step: query `is_final_snapshot=1 AND bsp_price IS NOT NULL` for races jumping post-restart, expect non-zero count after the next day of normal racing.

---

## 8. Output spec

Code produces a single deliverable: `dr029/2_1_race_data/surgical_fix_3_report.md`.

Anticipated 100-200 lines, covering:

1. **What was done** — short narrative of the actual sequence executed (which order, what was found mid-stream, any deviations from the brief's suggested sequencing). Working-tree state at session open vs at session close (confirm clean post-edit beyond the named anchors).
2. **Pre-fix baseline numbers** — output of the §7.1 queries.
3. **Changes applied** — exact diff of each of the four file changes. Include the `git diff` of each file post-edit so the actual change set is auditable.
4. **Service restart approach** — manual restart during quiet window OR wait for natural 08:30 restart; which was chosen and why.
5. **Post-fix verification numbers** — output of the §7.1 queries re-run for the post-restart window, side by side with pre-fix.
6. **Anything surprising** — any code-state mismatch between this brief's anchor descriptions and what was actually found. Any unexpected Betfair API response shape (the `r.sp.actual_sp` field name or path may differ from what the source-review report inferred; verify and report). Any interaction with the dirty-tree changes that surprised. Any other observation worth Operator-Claude awareness.
7. **What's left** — explicit named follow-ups. Specifically: confirm BSP write-back has fired against actual race jumps in the next session (Session 37 verification), since the OPEN→SUSPENDED path can only be exercised by real races jumping during a service uptime window.

If anything blocks completion, surface as a finding and stop — do not work around it. The brief is one bounded session; partial completion with clean reporting beats over-running into adjacent fixes.

---

## 9. The orphan column finding (informational, not action)

Per source-review report §"Anything surprising": `bsp_price` was added in `migrate_depth_and_batch.py` alongside `sp_near_price` / `sp_far_price` and similar columns, but the migration's INSERT-statement update extended to `sp_*` only — the writer was never extended to populate `bsp_price`. The 0% population is the necessary consequence.

Fix 3 closes that gap. There is no need to investigate why the original migration missed `bsp_price` — the historical write isn't recoverable, and the surgical-fix path is forward-only.

---

## 10. Hard limits

- **Single Code session.** If all four changes can't land cleanly in one session, complete whichever subset is further along, report state, stop. Changes (a), (b), (d) are the most independent and can land standalone; change (c) is the most involved.
- **No edits outside the anchors named in §5.** If a fix appears to require editing a file not in the anchor list, that's a finding — surface it, stop, do not proceed.
- **No schema changes.** No `ALTER TABLE`, no `CREATE`, no migration scripts. The `bsp_price` column already exists.
- **No new tests.** The test-coverage gap is named DR-029-deferred debt; this brief does not address it.
- **No fixes 4 or 5** (cadence, venue harmonisation) — those are separate Code sessions.
- **Honour the dirty git working tree.** Specifically:
  - Read files in their current working-tree state. The dirty changes are operator-side in-flight work and are NOT to be reverted, stashed, or committed.
  - **No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), or `git reset` (any form).**
  - Edit only within the named anchor regions. After each file edit, run `git diff <file>` and confirm only the brief's intended changes appear in addition to the pre-existing dirty changes (i.e., the diff grows; it does not change shape in unexpected ways).
  - At session close, run `git status` and confirm the file list is unchanged (no new files except the report; no fewer modified files than at session open).
- **No edits to untracked files.** The untracked `api/` subtree and `bookmakers/tabtouch.py` are NOT in scope. Do not import from them, do not modify them, do not delete them.

---

## 11. What happens after

Operator-Claude reads `surgical_fix_3_report.md` in Session 37 (or whichever session next opens after this Code run). Subsequent surgical-fix Code sessions:

- **Code session 3** — Fix 4 (cadence, Cluster 2 §5.2). Lower `DISCOVERY_INTERVAL`, add fast-discovery sweep when any race scheduled within next hour, log `_register_race` silent-drop branch. `config/settings.py` and `capture/orchestrator.py` anchors. **`config/settings.py` is dirty** per the Session 36 drift check (sportsbet re-enablement) — Fix 4 brief will carry the same dirty-tree handling rules as this brief.
- **Code session 4** — Fix 5 (venue harmonisation + retroactive race-key merge, surfaced in surgical-fix-1+2 report §5). Lift the existing `bookmakers/sportsbet.py:_clean_venue` logic into `matching/race_matcher.normalise_venue`, then run a one-shot data migration to merge orphan Racing-API race rows onto the matching live-capture race rows. **`bookmakers/sportsbet.py` and `matching/race_matcher.py` are both dirty** — Fix 5 brief will carry the same dirty-tree handling and will reference the operator's existing `_clean_venue` implementation as the source of the lift.

Subsequent surgical-fix briefs (for Fix 4 and Fix 5) get drafted in Operator-Claude sessions following each Code session's report. DR-029 §2.4 / §2.6 / §2.10 carry the surgical-fix carry-in framings these execute under.

---

*End of brief.*
