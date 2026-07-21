# DR-029 §2.1 — BSP write-back fix — brief

**Status:** locked, ready for Code.
**Drafted:** Session 53 (§1–§9 paused mid-draft); §9 hard-limits refresh, §10, §11 completed Session 54 after the lock-contention fix landed (`capture_db_lock_report.md`, 2026-05-03).
**Anchored on:** `dr029/2_1_race_data/api_probe_report.md` (Session 52 deliverable). The probe directly determined the fix's mechanism.
**Pre-flight diagnostic:** `dr029/2_1_race_data/bsp_writeback_vps_drift_check.md` (refreshed at Session 54 open — see §9.2 below for the post-lock-fix dirty-tree state).
**Tool:** Claude Code, single bounded session.
**Output:** `dr029/2_1_race_data/bsp_writeback_report.md`.
**Timestamps:** Adelaide local time (ACST/ACDT) per DR-021 (timestamp anchoring, Adelaide local time).

---

## §1 What this brief is and is not

This is a **surgical fix** — a single-line projection-set change in `betfair/client.py` plus an isnan-guard confirmation in `storage/database.py`, plus an empirical verification window. It activates the `bsp_price` write path that Fix 3 (Session 37) wired correctly but couldn't verify because the upstream API call was using the wrong projection set.

**Single bounded Code session.** End-to-end in one run. If the work doesn't fit, that's a finding, not a continuation.

**Surprises become findings, not blockers.** Code reports anomalies in the report; remediation routes to operator-Claude triage. Code does not chase findings mid-session.

**Code does not propose follow-up work.** The next brief (if any is needed) is the operator-Claude session's job after reading this brief's report.

This is **not** a redesign of the BSP fetch path, **not** a change to the snapshot writer's column set, **not** an addition of new fields beyond `bsp_price`, **not** a Fix 4 cadence change, **not** a fix for the missing Saturday/Sunday race data, and **not** a credential-upgrade pursuit for `EX_LADDER`.

---

## §2 Why this work exists

Fix 3 (Session 37) added `bsp_price` write-back scaffolding: the column on `betfair_snapshots`, the `update_final_snapshot_bsp()` function, the orchestrator settlement-time call to `get_market_book_sp_traded()`. Empirical verification at Fix 3 close found `bsp_price` was never populated — the function was being called, but `runner.sp.actual_sp` came back missing on every closed-market read. Fix 3 routed this to a direct API observation probe (Session 39 brief, Session 52 execution, Session 53 triage).

The probe (`api_probe_report.md` §4(b)) found the mechanism: **Betfair's `sp` object shape-shifts at the SUSPENDED transition.** Pre-suspension, `sp = {nearPrice, farPrice, backStakeTaken, layLiabilityTaken}`. Post-suspension, `sp = {actualSP, backStakeTaken, layLiabilityTaken}` — `nearPrice`/`farPrice` removed, `actualSP` added. Requesting `priceProjection=SP_TRADED` *alone* fails to materialise the `sp` container on closed runners because nothing in `SP_TRADED` lives there post-SUSPENDED. **Adding `SP_AVAILABLE` to the projection set keeps the container present** so `actualSP` is reachable.

Empirically: `actualSP` is 100% populated for active runners from SUSPENDED-onset across thoroughbred, harness, and greyhound; persists through the full 45-minute CLOSED tail; is `NaN` (Python float) for REMOVED runners and must be NaN-guarded.

The fix is a one-line projection-set extension plus a confirmation that the existing isnan-guard in `update_final_snapshot_bsp()`'s caller path is sufficient.

DR-029 (the data-layer fit-for-purpose review before v3 build) §2.1 (race-side data fit-for-purpose verification) close path runs through this fix and Fix 4 (cadence design). This brief lifts §2.1's BSP gap; Fix 4 follows.

---

## §3 Pre-reads

In order:

1. `dr029/2_1_race_data/api_probe_report.md` — §4(b), §4(c), §4(d), §3.1, §3.3, §5. The probe report is the design source.
2. `dr029/2_1_race_data/surgical_fix_3_brief.md` and `dr029/2_1_race_data/surgical_fix_3_report.md` — Fix 3 wired the scaffolding this brief activates; the report's "BSP write-back wired correctly per brief but empirically inert" finding is the gap this brief closes.
3. `dr029/2_1_race_data/bsp_writeback_vps_drift_check.md` — the dirty-tree pre-flight (Session 53; refreshed Session 54 — see §9.2).

Reference-only — read on demand:

- `dr029/2_1_race_data/capture_db_lock_brief.md` and `dr029/2_1_race_data/capture_db_lock_report.md` — the lock-contention fix that landed immediately before this one. Same dirty tree, no overlap with this brief's edit anchors.
- `dr029/dr029_scope.md` — DR-029 scope; §2.1 close path.
- `decisions.md` DR-021 (timestamp anchoring), DR-027 (the two-database architecture: BetHub owns operational state, capture.db owns analytical/source data), DR-028 (the cross-database integration boundary discipline: no caching, no denormalisation, no second integration point).

---

## §4 System access

**VPS:** `root@187.77.183.9`, repo at `/home/racing/racing-data-capture`. Read-write on the three named files (§5). Read-only on `capture.db` (`/home/racing/racing-data-capture/data/capture.db`) for verification queries.

**Mac filesystem:** read-only. Reports write to `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/`.

**Betfair API:** read-only. The fix triggers exactly the same call path as today (orchestrator's settlement-time BSP fetch); no new code paths, no new credentials.

**Service restart:** `sudo systemctl restart racing-capture.service` once edits are in place. The lock-contention fix has already settled the API service into per-request lifecycle, so no API service restart is needed for this fix.

**Adelaide local timestamps per DR-021** for every time-of-day reference in the report.

---

## §5 Substantive scope

Three named edits, in dependency order.

### §5.1 — `betfair/client.py:200` projection-set change

**Current shape** (lines 187–220, `get_market_book_sp_traded()`):

```python
books = self._client.betting.list_market_book(
    market_ids=[market_id],
    price_projection=price_projection(
        price_data=["SP_TRADED"],
    ),
)
```

**Change:**

```python
books = self._client.betting.list_market_book(
    market_ids=[market_id],
    price_projection=price_projection(
        price_data=["SP_AVAILABLE", "SP_TRADED"],
    ),
)
```

**Why:** per probe §4(b), `SP_AVAILABLE` is required for the `sp` container to materialise on closed runners. `SP_TRADED` alone yields no `sp` object on closed AU thoroughbred WIN markets. Both projections together cost the same single API call.

**No other change in this method.** The downstream `getattr(r, "sp", None)`, `getattr(sp, "actual_sp", None)`, and `isinstance(actual_sp, (int, float)) and actual_sp > 0` guards are correct and stay as-is.

**Note on `actual_sp` attribute name:** the `betfairlightweight` library converts Betfair's camelCase `actualSP` API field to snake_case `actual_sp` on the runner's `sp` object. Fix 3's existing code uses `actual_sp` correctly. No change.

### §5.2 — `storage/database.py:691-722` isnan-guard confirmation

**Current shape** (`update_final_snapshot_bsp()`):

```python
def update_final_snapshot_bsp(
    conn: sqlite3.Connection,
    race_id: int,
    bsp_by_selection: dict[int, float],
) -> int:
    """Write realised BSP onto is_final_snapshot=1 rows for a race."""
    if not bsp_by_selection:
        return 0
    updated = 0
    for selection_id, bsp in bsp_by_selection.items():
        cur = conn.execute(
            """
            UPDATE betfair_snapshots
            SET bsp_price = ?
            WHERE race_id = ?
              AND is_final_snapshot = 1
              AND runner_id IN (
                  SELECT id FROM runners
                  WHERE race_id = ? AND betfair_selection_id = ?
              )
            """,
            (bsp, race_id, race_id, selection_id),
        )
        updated += cur.rowcount
    conn.commit()
    return updated
```

**No code change here.** The function receives `bsp_by_selection: dict[int, float]` — a dict already filtered upstream in `betfair/client.py`'s `get_market_book_sp_traded()`. The upstream filter is `isinstance(actual_sp, (int, float)) and actual_sp > 0`, which **is** sufficient: `math.isnan(NaN) is True` AND `NaN > 0 is False`, so NaN values fail the comparison and never reach the dict.

**Verification action:** Code adds a one-line comment to the upstream filter to document why the `> 0` guard is load-bearing for NaN-rejection, citing probe report §4(d). Comment, not code change. If Code judges the existing code self-explanatory enough that a comment is noise, skip — surface as a finding either way.

### §5.3 — `capture/orchestrator.py:904-927` no change required

**Current shape** (settlement handler's BSP fetch block):

```python
# Fetch realised BSP via SP_TRADED projection — one-shot post-close.
# Logged-and-continue on failure; never blocks settlement processing.
try:
    bsp_by_selection = self._client.get_market_book_sp_traded(
        state.betfair_win_market_id
    )
    if bsp_by_selection:
        n_updated = update_final_snapshot_bsp(
            self._conn, state.race_id, bsp_by_selection
        )
        logger.info(
            "BSP captured for %s R%d — %d runners, %d final-snapshot rows updated",
            state.venue_normalised, state.race_number,
            len(bsp_by_selection), n_updated,
        )
except Exception as e:
    logger.warning(
        "BSP fetch failed for %s R%d: %s",
        state.venue_normalised, state.race_number, e,
    )
```

**No code change.** The orchestrator's settlement handler is correct. The comment line `# Fetch realised BSP via SP_TRADED projection` is now slightly stale (the fix uses `SP_AVAILABLE + SP_TRADED`); Code may update the comment to `# Fetch realised BSP via SP_AVAILABLE+SP_TRADED projection set —` if judged useful, or skip. Comment-only change, not load-bearing.

---

## §6 Sequencing within session

1. Read pre-reads (§3) in order.
2. Capture pre-fix baseline (§7.1).
3. Make the §5.1 projection-set edit. Run `git diff betfair/client.py` — confirm only the one-line projection-set change.
4. Optionally make the §5.2 comment addition. Run `git diff storage/database.py` — confirm comment-only or empty diff.
5. Optionally update the §5.3 stale comment in `capture/orchestrator.py`. Run `git diff capture/orchestrator.py` — confirm comment-only or empty diff.
6. Local `ast.parse()` on each edited file.
7. SCP edits to VPS, chown back to `racing:racing` if needed.
8. `sudo systemctl restart racing-capture.service`.
9. Wait for the next AU thoroughbred race to enter SUSPENDED → CLOSED state with the orchestrator running. Capture verification queries (§7.2).
10. Write the report.

The verification window (step 9) is the longest part of the session — settlement happens at race end and Code waits for it. Code may run §7.2's queries in a polling loop or wait for one full settlement cycle to land. Choose whichever fits the session budget; surface the chosen approach in the report.

---

## §7 Empirical verification

### §7.1 — Pre-fix baseline

Run before any edit:

```sql
-- Most recent settled race(s) with final snapshots
SELECT s.race_id,
       COUNT(*) AS n_final_runners,
       SUM(CASE WHEN s.bsp_price IS NOT NULL THEN 1 ELSE 0 END) AS n_with_bsp,
       MIN(s.snapshot_time) AS settled_at
FROM betfair_snapshots s
JOIN races r ON r.id = s.race_id
WHERE s.is_final_snapshot = 1
  AND r.race_date IN (date('now'), date('now', '-1 day'))
  AND r.finish_position IS NOT NULL
GROUP BY s.race_id
ORDER BY settled_at DESC
LIMIT 5;
```

Expected: `n_with_bsp = 0` for all rows. The pre-fix state is "scaffolding present, write path inert."

If `n_with_bsp > 0` on any pre-fix row: that's a finding — something else is writing `bsp_price` and the brief's premise needs operator-Claude triage before Code proceeds. Bail out, write the finding to the report, end session.

### §7.2 — Post-fix baseline

After the service restart, wait for at least one AU thoroughbred race to settle. Then run:

```sql
-- Same query as §7.1 but bounded to post-restart races
SELECT s.race_id,
       COUNT(*) AS n_final_runners,
       SUM(CASE WHEN s.bsp_price IS NOT NULL THEN 1 ELSE 0 END) AS n_with_bsp,
       AVG(CASE WHEN s.bsp_price IS NOT NULL THEN s.bsp_price END) AS avg_bsp,
       MIN(s.snapshot_time) AS settled_at
FROM betfair_snapshots s
JOIN races r ON r.id = s.race_id
WHERE s.is_final_snapshot = 1
  AND r.race_date = date('now')
  AND r.finish_position IS NOT NULL
  AND s.snapshot_time > '<service-restart timestamp>'
GROUP BY s.race_id
ORDER BY settled_at DESC
LIMIT 5;
```

**Five success criteria:**

1. **Pre-fix baseline confirmed** — `n_with_bsp = 0` on the most recent pre-fix settled races.
2. **Edits land cleanly** — `git diff` after each edit shows only the named one-line change (or comment-only changes for §5.2/§5.3); no formatter, no drift; final `git status` shows the same 13 modified + 7 untracked file list as §9.2 (no new files, no removed entries).
3. **Service restart is clean** — `racing-capture.service` returns to `active (running)` state; orchestrator log shows no exceptions in the post-restart window.
4. **At least one settled race shows `n_with_bsp = n_active_runners`** — `bsp_price` populates for all active (non-REMOVED) runners on at least one settled race in the verification window. Confirm by joining `betfair_snapshots` to `runners` and counting `runner_status != 'REMOVED'`.
5. **`bsp_price` values are sane** — `0 < bsp_price < 1000` for all populated rows; no NaN-encoded floats (which would surface as `NULL` in SQL, but should also be checked with the SQL identity `bsp_price = bsp_price` which fails on NaN); average BSP looks like a plausible mid-pack price (typically $2–$50 for AU thoroughbred WIN).

Partial-success (e.g. criterion 4 met for some but not all runners on a race, or criteria 1–3 met but no race settled in the verification window) routes to operator-Claude triage rather than retry within the same session.

### §7.3 — Verification window assumption

The fix needs **a settled AU thoroughbred WIN market with the post-fix code running.** AU thoroughbred metro racing typically runs from late morning ACST through evening; the verification window opens at the first settled race after the service restart. If Code starts the session outside racing hours, the report should note this and the session may need to span racing hours, OR Code may end the session and queue the verification for an operator-Claude follow-up read.

Per probe §3.1, `actualSP` is 100% populated for active thoroughbred runners from SUSPENDED-onset and persists through the 45-minute CLOSED tail — so a verification race that's been settled for at least 5 minutes is reliable.

---

## §8 Output spec

Single file: `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/bsp_writeback_report.md`.

Section structure:

1. **§1 Execution summary** — anchor table with Adelaide-local + UTC timestamps (T0 service stop / T1 edits applied / T2 service start / T3 first verification race settled / T4 session close); outcome line; pre/post `bsp_price` populated counts.
2. **§2 Pre-fix baseline** — §7.1 query results.
3. **§3 File-inspection results** — confirm structures match brief §5; report current line counts and any structural divergence.
4. **§4 Edits** — `git diff` of each edited file.
5. **§5 Service-restart cycle** — systemctl output, post-restart `lsof` confirmation.
6. **§6 Post-fix verification** — §7.2 query results plus orchestrator log excerpts showing the BSP-captured log line firing.
7. **§7 Findings** — anything surprising, anomalous, or worth surfacing for operator-Claude triage. Empty section if nothing surfaces.
8. **§8 Self-assessment** — five success criteria checked, dirty-tree discipline confirmed, out-of-scope check, length.

**Length anticipation:** 200–350 lines. Smaller than the lock-contention report because the fix is one line; larger than a trivial report because the verification window produces real data tables.

**Output does not contain:**

- Recommendations for Fix 4 cadence design.
- Proposals for additional snapshot writer fields (`adjustmentFactor`, `removalDate`, etc. — those route to §2.10).
- Schema change suggestions.
- Operator-facing strategy or scope commentary.

---

## §9 Hard limits

### §9.1 — What is NOT in scope

- **No edits outside the three named files** (`betfair/client.py`, `storage/database.py`, `capture/orchestrator.py`), and within those files, no edits outside the three named anchors (§5.1, §5.2, §5.3).
- **No schema changes.** No `ALTER TABLE`, no new columns, no migrations.
- **No DDL on `capture.db`.** Read-only verification queries only.
- **No new fields beyond `bsp_price`.** The probe report names eight other writer gaps (`adjustmentFactor`, `removalDate`, `bspReconciled`, `inplay`, `betDelay`, `version`, `totalAvailable`, `sp.backStakeTaken`/`sp.layLiabilityTaken`); all of these are §2.10 work, not this brief.
- **No Fix 4 cadence work.** Even if the session has spare budget after verification, do not extend into cadence-tier edits.
- **No retroactive backfill.** The missing Saturday 2026-05-02 race data and any pre-fix settled races without `bsp_price` are out of scope; backfill is operator-decided as a separate brief if at all.
- **No `EX_LADDER` credential pursuit.** Out of scope per probe §4(a).
- **No mid-session operator escalation.** Findings surface in the report.
- **No formatter run.** No `black`, `ruff format`, `isort`, etc.
- **No new dependencies.** The fix uses what's already imported.

### §9.2 — Dirty-tree discipline (post-lock-fix baseline)

Working tree on VPS as of Session 54 open (2026-05-03 07:05 ACST), HEAD `5f71488006a1443021aefbc8a97e2a73d638c37c`:

**Modified (13):**

```
 M api/main.py
 M api/routes/results.py
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

**Untracked (7):**

```
?? api/__init__.py
?? api/db.py
?? api/routes/__init__.py
?? api/routes/health.py
?? api/routes/races.py
?? api/routes/snapshots.py
?? bookmakers/tabtouch.py
```

**Hard limits on git mutation:**

- No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), `git reset`.
- `git status` and `git diff` are read-only and used freely.
- After each edit, run `git diff <file>` to confirm only intended changes were added.
- At session close, `git status --short` must match the 13 modified + 7 untracked file list above. Divergence is a finding.

The three target files (`betfair/client.py`, `storage/database.py`, `capture/orchestrator.py`) are already in the modified-list — the dirty regions in those files **are** Fix 3's BSP scaffolding. Editing the projection-set line and (optionally) two comments is a minor extension to the existing uncommitted batch, not a fresh dirty region.

### §9.3 — Single bounded session

If verification can't be completed in the session (e.g. no AU racing in the window, or service won't restart cleanly), Code surfaces as a finding and ends the session. Do not extend past budget; do not attempt restart cycles or workarounds beyond what §6 names.

---

## §10 What happens after Code's session

Code produces `bsp_writeback_report.md`. The next operator-Claude session reads the report and:

1. **Triages findings against the five success criteria (§7.2).**
2. **If success → §2.1's BSP gap closes.** §2.1 surgical-fix arc moves to its remaining work: Fix 5 (venue harmonisation, brief drafting independent), and Fix 4 (cadence design, brief drafting unblocked once probe outputs are fully digested for §2.10).
3. **If partial-success → operator-Claude routes specifics.** Common routes: missing settled-race-in-window → re-verify in a follow-up read; some-runners-not-populated → triage whether REMOVED-runner NaN-guard works as expected, possible follow-up brief; service-restart hiccup → triage with VPS state.
4. **If failure → root-cause triage.** The most likely failure mode given the probe's findings is a code path the probe didn't hit; triage routes to a follow-up brief.

**Out of scope for the next session:** Fix 4 cadence design (queued separately; brief drafting follows BSP close); retroactive `bsp_price` backfill of pre-fix races (operator-decided whether to scope at all); §2.10 field-inventory write-up (separate work stream).

The next session does **not** open with a fresh Code commission. The triage session writes the next brief if and only if a follow-up is needed.

---

## §11 Cross-references

- **DR-029** (the data-layer fit-for-purpose review before v3 build) §2.1 (race-side data fit-for-purpose verification). This brief lifts §2.1's BSP write-back gap; Fix 4 (cadence) is the remaining §2.1 work after this and Fix 5 (venue harmonisation).
- **DR-027** (the two-database architecture) — the fix touches `capture.db` (analytical line) only; no v2 `bethub.db` interaction. BetHub-side operational state is unaffected.
- **DR-028** (the cross-database integration boundary discipline) — no caching, no denormalisation, no second integration point. The fix writes one column to one analytical-line table; integration boundary unchanged.
- **DR-021** (timestamp anchoring, Adelaide local time) — applies to all timestamps in the report.

**Source documents:**

- `dr029/2_1_race_data/api_probe_report.md` — design source. §4(b) names the projection-set mechanism; §3.1 names the population rate; §4(d) names the NaN-guard requirement.
- `dr029/2_1_race_data/surgical_fix_3_brief.md` and `dr029/2_1_race_data/surgical_fix_3_report.md` — the wiring this brief activates. Fix 3's "wired correctly per brief but empirically inert" finding is what this brief closes.
- `dr029/2_1_race_data/bsp_writeback_vps_drift_check.md` — the dirty-tree pre-flight (Session 53; refreshed at Session 54 open).
- `dr029/2_1_race_data/capture_db_lock_brief.md` and `dr029/2_1_race_data/capture_db_lock_report.md` — the upstream fix that landed immediately before this one. No edit overlap; same dirty tree.

**Parking-lot items (excluded by §9.1):**

- §2.10 external analytics scan (eight-plus other API-exposed fields not captured by the writer).
- Fix 4 cadence design.
- Fix 5 venue harmonisation.
- Retroactive `bsp_price` backfill.
- `EX_LADDER` credential upgrade pursuit.
- Schema-level write-side coherence work (§2.9).

---

*End of brief.*
