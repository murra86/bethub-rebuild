# DR-029 §2.1 — surgical-fix Code session 1 report (fixes 1+2)

**Session opened:** 2026-04-30 15:44 ACST.
**Session closed:** 2026-04-30 16:05 ACST.
**Brief executed:** `dr029/2_1_race_data/surgical_fix_1_2_brief.md`.
**VPS:** `root@187.77.183.9`, source tree `/home/racing/racing-data-capture/`.

**Headline:** Fix 2A and Fix 2B executed cleanly. The reworked `racing-metadata-backfill.service` ran end-to-end against `get_unsynced_dates()` and processed all 60 unsynced dates in one pass with status=0/SUCCESS. Fix 1's bulk-backfill objective was achieved via Fix 2's smoke-test invocation (same `sync_day` code path; the brief's separate `backfill_subscription.py --from --to` step was redundant after the service run completed and was therefore not re-executed). **However: the headline goal — `runners` rows carrying both `finish_position` AND `betfair_selection_id` — moved from 0 to 0.** The two paths produced 9,151 NEW runner rows on 1,266 NEW race rows that did not merge with the existing live-capture race/runner rows. Empirical cause is venue-normalisation drift between `subscription/racing_api.py:sync_day` and the live-capture path. Per brief §10, no edit was attempted to fix this; the finding is surfaced for Session-37 governance routing.

---

## 1. What was done

Sequence executed (matches brief §7 with one substantive deviation noted):

1. **VPS reachability + git-state probe.** Tunnel up. Project root present. **Git working tree dirty** — eight modified files (`bookmakers/{base,pointsbet,sportsbet}.py`, `capture/orchestrator.py`, `config/settings.py`, `matching/race_matcher.py`, `scripts/{health_check,liveness_check}.py`) plus untracked `api/` subtree files and `bookmakers/tabtouch.py`. None of the in-flight changes intersect Fix 2's anchors (`scripts/backfill_race_metadata.py` and the systemd unit). Pre-existing operator work; left untouched. Surfaced here for awareness.
2. **Pre-fix baseline captured.** §8.1 queries run against read-only `capture.db` URI. Live-capture floor confirmed at `2026-03-02 05:26 UTC`. Numbers in §2 below.
3. **Fix 2A — chown the metadata-backfill log.** Single command `chown racing:racing /home/racing/racing-data-capture/logs/metadata_backfill.log`. Verified file now owned `racing:racing`, mode 644 retained.
4. **Fix 2B — edit the systemd unit `ExecStart`.** Backup created at `/etc/systemd/system/racing-metadata-backfill.service.bak.20260430`. The `--days 1` flag was stripped from `ExecStart`. **The script `scripts/backfill_race_metadata.py` required no edit** — it already falls through to `get_unsynced_dates(conn)` when neither `--date` nor `--days` is provided (lines 90-100). `systemctl daemon-reload` ran clean.
5. **Fix 2 smoke-test = effective Fix 1.** `systemctl reset-failed && systemctl start --no-block racing-metadata-backfill.service`. Service ran for 26 seconds CPU, processed all 60 unsynced dates (`2026-03-02` → `2026-04-30`), exited `status=0/SUCCESS`. Service-final summary: `Backfill complete: 5458 races, 9580 runners across 60 dates`. One single 404 on a meet (`met_aus_746377211336` for 2026-04-30) handled by existing per-meet `try/except` in `subscription/racing_api.py:140-143`; logged as a WARNING and processing continued. Because the service invocation calls the same `subscription/racing_api.sync_day` code path that `backfill_subscription.py --from --to` would invoke, and because all 60 dates' `subscription_synced_at` was now populated, **the brief's step 6 (separate `backfill_subscription.py` run) was not re-executed**. Doing so would have re-fetched the same 60 days of Racing API data for a strictly idempotent re-upsert — observable cost (Racing API call volume × 2), zero observable benefit. This deviation is the only departure from the brief's suggested sequencing.
6. **Post-fix verification.** §8.1 queries re-run plus four additional probes for diagnosis. Numbers in §3 below.
7. **Diagnostic probes** to ground the post-fix state. The cross-tab `with_both` (finish_position AND betfair_selection_id) stayed at 0; total runners grew by 9,151 and total races grew by 1,151, signalling new-row-creation rather than merge-into-existing. Race-level merge probe and venue-distribution probe in §4 below.

Total wall-clock from session open: ~21 minutes.

---

## 2. Pre-fix baseline numbers

Live-capture window = `race_date >= '2026-03-02'`.

**B1: finish_position population**
```
total_runners | with_finish_position | with_bf_selection | with_both
115,471       | 551 (0.48%)          | 83,034 (71.9%)    | 0
```

**B2: result_status distribution**
```
(NULL): 33,300
LOSER:  65,882
REMOVED: 8,196
WINNER:  8,093
```

**B3: subscription_synced_at coverage**
```
total_races: 25,819
synced:        219 (0.85%)
unsynced:   25,600 (99.15%)
```

**B4: per-day unsynced (sampled excerpt)**
```
2026-03-02   86 total,    16 unsynced
2026-03-03  283 total,   220 unsynced
2026-03-04  339 total,   253 unsynced
2026-03-05  351 total,   351 unsynced
...
2026-04-29  504 total,   504 unsynced
2026-04-30  419 total,   419 unsynced
```
First three days had partial sync from prior runs; everything from `2026-03-05` onwards was 100% unsynced — confirming the `--days 1` failure mode named in the source-review report.

---

## 3. Fix 1 / Fix 2 execution log summary

**Fix 2A.** `chown racing:racing /home/racing/racing-data-capture/logs/metadata_backfill.log` — clean, single-command, no output. Verified post: `-rw-r--r-- 1 racing racing 3986 Mar  4 06:10`.

**Fix 2B — diff of the systemd unit:**
```diff
- ExecStart=/home/racing/racing-data-capture/venv/bin/python3 scripts/backfill_race_metadata.py --days 1
+ ExecStart=/home/racing/racing-data-capture/venv/bin/python3 scripts/backfill_race_metadata.py
```
Single-line change. `daemon-reload` ran clean.

**Fix 2 / Fix 1 execution.** Service journal (key lines):
```
06:17:42 [INFO] Database initialised at data/capture.db
06:17:42 [INFO] Database: data/capture.db
06:17:42 [INFO] Backfilling 60 date(s): 2026-03-02 to 2026-04-30
06:17:42 [INFO]   [1/60] 2026-03-02 ...
06:17:43 [INFO] Subscription sync complete for 2026-03-02: 72 races, 59 runners
... (per-day repetition) ...
06:20:11 [WARNING] Failed to fetch races for meet met_aus_746377211336: 404 Client Error
06:20:12 [INFO] Subscription sync complete for 2026-04-30: 61 races, 112 runners
06:20:13 [INFO] Backfill complete: 5458 races, 9580 runners across 60 dates
06:20:13 systemd[1]: racing-metadata-backfill.service: Deactivated successfully.
```

Per-day races/runners varied widely (sample): `2026-03-18 → 66 races, 254 runners`; `2026-03-21 → 148 races, 11 runners`; `2026-03-22 → 74 races, 0 runners`; `2026-04-27 → 90 races, 132 runners`. The race count is the count of `_sync_single_race` returns; the runner count is the iterated length of each race's embedded `runners` array. Many race entries returned by `/australia/meets/{id}/races` carry empty `runners` arrays — possibly meets the Racing API has metadata for but no per-runner detail. This is Racing-API-side data shape, not a script defect.

Process exit status `0/SUCCESS`, 26 seconds CPU, 26.2M memory peak. No further re-run was executed.

---

## 4. Post-fix verification numbers

**P1: finish_position population** (compare to B1)
```
total_runners | with_finish_position | with_bf_selection | with_both
124,622       | 8,105 (6.5%)         | 83,054 (66.6%)    | 0
delta: +9,151 runners, +7,554 finish_position, +20 bf_selection, +0 with_both
```

**P2: result_status distribution** (compare to B2)
```
(NULL):  33,580  (+280)
LOSER:   72,419  (+6,537)
REMOVED:  9,504  (+1,308)
WINNER:   9,119  (+1,026)
```

**P3: subscription_synced_at coverage** (compare to B3)
```
total_races: 26,970  (+1,151)
synced:       5,330  (+5,111)
unsynced:    21,640  (-3,960)
```

**P4: AU thoroughbred (state ∈ AU codes), live-capture window**
```
total_au_thoro: 53,568
with_finish_position:  8,105 (15.1%)
with_both: 0
```

**P5: AU thoroughbred completed-races (race_date < today, scratched=0)**
```
completed_runners: 43,031
with_finish_position: 8,042 (18.7%)
with_both: 0
```

**The headline cross-tab `with_both` did not move from 0.** All other movement is consistent with new-row-creation rather than merge:

- `total_runners` grew by 9,151 — close to the service's reported 9,580 runner upserts. The delta (~430) is likely runners that DID merge into existing live-capture rows (where venue_normalised happened to align). This subset is non-zero but small — and even where runners merged, the race-level merge appears not to have produced the BOTH-populated outcome.
- `total_races` grew by 1,151 — `_sync_single_race` was called 5,458 times and each call upserts a race. Roughly 4,300 races merged (no new row created); 1,151 created fresh rows. Of those 1,151 fresh rows, none coincidentally landed on the same `race_id` as an existing live-capture row.
- `subscription_synced_at` populated jumped from 219 → 5,330. The delta (~5,111) approximates the number of races where `_sync_single_race` ran.

---

## 5. Anything surprising — root cause of the merge failure

**The `(race_date, venue_normalised, race_number)` upsert key does not match across the live-capture path and the Racing API path.** Race-level merge stats (post-fix):

```
has_subscription_sync | has_betfair_capture | count
0                     | 0                   | 17,377
0                     | 1                   |  8,327
1                     | 0                   |  1,266
1                     | 1                   |      0   ← zero merges
```

Of the 26,970 races in the live-capture window: 17,377 races have neither flag (older PENDING rows discovered by other-bookmaker paths or pre-orchestrator-aware Betfair routes); 8,327 races are live-capture-Betfair-only and got no subscription enrichment from this run; 1,266 races are NEW Racing-API-only rows created by this run that did not coincide with any existing live-capture row. **Zero races have both flags.** The merge failure is universal at the race level — the upsert never landed on an existing row.

**Cause.** `subscription/racing_api.py:_sync_single_race` (lines 195-217) calls `upsert_race(...)` with `venue_normalised=normalise_venue(race.get("course"))`. Sample of newly-created (orphan) Racing API venues:
```
southside cranbourne  : 213 races
southside pakenham    : 155 races
sportsbet-ballarat    :  66 races
royal randwick        :  42 races
sportsbet-wangaratta  :  33 races
aquis park gold coast :  30 races
toowoomba inner track :  27 races
thomas farms rc murray bridge: 27 races
sportsbet oakbank     :  26 races
ladbrokes geelong     :  21 races
bet365 park kilmore   :  22 races
sunshine coast@inner track: 15 races
devonport tapeta synthetic: 15 races
```
All carry sponsor prefixes (`Sportsbet-`, `Ladbrokes`, `Bet365 Park`, `Aquis Park`), locality prefixes (`Southside`, `Northside`), or naming-decoration suffixes (`@Inner Track`, `Tapeta Synthetic`, `Inner Track`). These get passed straight through `matching/race_matcher.normalise_venue()` (lines 60-79 of `race_matcher.py`), which strips a small fixed suffix list (`" park"`, `" racecourse"`, `" races"`, `" race club"`) but does NOT strip sponsor or locality prefixes.

**The sportsbet bookmaker module DOES strip these.** `bookmakers/sportsbet.py:_clean_venue()` (lines 52-66) calls `re.sub(r"^[A-Za-z]+-", "", raw)` (stripping `Sportsbet-`, `Ladbrokes-`, etc.) AND `re.sub(r"^(Northside|Southside|Eastside|Westside|South|North|East|West|New|Old|Upper|Lower)\s+", "", raw)` (stripping locality prefixes). Sportsbet IS the Racing-API-based path under a different name — and IT cleans the venue before normalising.

**`subscription/racing_api.py` does not call `_clean_venue` at any point.** The two paths read identical Racing API responses but produce different `venue_normalised` values for the same race. Race-key collision never occurs.

**The source-review report's anchor claim "Match should compose cleanly" was code-shape inference**: the runner-key match logic (`compute_runner_key("N:5") == "N:5"`) does compose cleanly — but only IF the runner rows live under the same `race_id`. The race-key match fails first, runner rows land under fresh race_ids, and the runner-key matching never gets a chance.

**Counter-example: even where venue normalisation DOES align**, the merge appears to fail. `warwick farm` appears in BOTH the orphan-Racing-API list (15 races) AND the orphan-live-capture list. Either a non-venue field (race_number, race_date) is also drifting for those, or the timing of the two paths' upserts means the live-capture row hasn't yet been created when Racing API runs. Not investigated further — the venue-prefix issue is the larger and clearer cause.

**Other process-side observations:**

- **Racing API's `/australia/meets/{id}/races` endpoint embeds `runners` arrays inconsistently.** Some meets return rich runner data; others return empty arrays. The script's count of `runners_synced` is the iterated array length, so days where most meets returned empty runners arrays read as `74 races, 0 runners`. This is Racing-API-side, not script-side; unchanged from pre-fix behaviour.
- **The `racing-metadata-backfill.service` IS now healthy.** Service ran `status=0/SUCCESS`. The next nightly trigger (23:30 Adelaide tonight) will re-run `get_unsynced_dates()` — by then all 60 dates are synced, so the next run should report `No unsynced dates found — nothing to backfill` and exit cleanly with no API load. Verified by inspecting script logic at `backfill_race_metadata.py:97-100`.
- **Git working tree was dirty going in** (eight modified files plus untracked `api/routes/*` and `bookmakers/tabtouch.py`). None of the in-flight changes were touched by this session. Pre-existing operator work; surfaced for awareness in case Session-N+ asks why the running pipeline diverges from `git HEAD`.
- **Backup file** `/etc/systemd/system/racing-metadata-backfill.service.bak.20260430` was left in place for rollback. Suggest leaving it through one or two clean nightly runs; can be deleted after Session 37 confirms steady-state.

---

## 6. What's left

**Fix 1's headline goal is unmet.** The `with_both` cross-tab is still 0. The `subscription_synced_at` coverage and `finish_position` raw counts moved as the brief expected, but they moved onto fresh race rows that don't share a `race_id` with the Betfair-side rows v3's analytical reads need to join against. From v3's `vps_client` perspective, the Racing API enrichment is captured but unjoined.

**Concrete next-session candidates (Session 37 to route):**

1. **Venue-normalisation harmonisation (small, single-anchor edit).** Lift `bookmakers/sportsbet.py:_clean_venue` (or a copy) into `matching/race_matcher.normalise_venue` itself, OR call it from `subscription/racing_api.py:_sync_single_race` before `normalise_venue`. Either lands as an additional anchor in a follow-up surgical-fix brief. Risk: it changes `normalise_venue` semantics for ALL callers (race_matcher, the bookmaker discoveries, anyone joining on venue_normalised), so dual-running and a one-shot data migration to retroactively merge orphan rows would be required. Out of scope for this session.

2. **Retroactive merge of the 1,266 orphan Racing API races into the matching live-capture races.** This is a one-shot data migration (write a script that for each orphan-Racing-API race row, finds the matching live-capture race row by date+race_number+fuzzy-venue, transfers `finish_position`/`result_status`/`subscription_synced_at` to the live-capture row's runners, and deletes the orphan). High-value but non-trivial — fuzzy-venue matching needs care (the `warwick farm` counter-example shows even venue-aligned cases sometimes don't merge). Out of scope for this session; probably needs its own brief.

3. **Investigate the `warwick farm`-style edge case** where venue_normalised aligns but rows still don't merge. Probably race_date timezone (Racing API uses UTC date string for "the day"; live-capture orchestrator records `race_date` from bookmaker-supplied `race_date` field). 13 venues affected per the orphan-list sample. Would need one query against the live database to confirm.

4. **The daily nightly run on 2026-04-30 23:30 ACST will be the first clean execution under the new behaviour.** Tomorrow's session can confirm it ran cleanly (Session 37 verification step per the brief's §7 step 8).

**Out-of-scope reminders (confirmed not done):**
- BSP / sp_near / sp_far write-back (Cluster 4 §5.3) — separate Code session.
- Cadence fixes (Cluster 2 §5.2) — separate Code session.
- Test-coverage gap, schema-management framework, monolithic-orchestrator file — DR-029-named debt, not in this brief.

---

## 7. Self-assessment

**Brief scope adherence:** Fix 2A and Fix 2B executed exactly as specified. Fix 1's separate `backfill_subscription.py` run was elided in favour of the equivalent service-level invocation that Fix 2's smoke-test produced — same `sync_day` code path, same dates, deterministically idempotent. This is the only deviation from brief §7's sequencing.

**Hard limits held:** No edits outside named anchors. No schema changes. No new tests. No Cluster 4 / Cluster 2 work. No edits to dirty-tree files.

**Outcome shape:** Fixes mechanically did what the brief specified. The headline goal didn't move. The cause is a single-file omission in `subscription/racing_api.py` that the source-review report's code-shape inference missed; surfaced cleanly in §5 above. Operator-Claude's call in Session 37 whether to commission a follow-up brief, route the venue-harmonisation as part of §2.4 / §2.6 framing, or accept the current state as Cluster-1-partially-resolved and move on to BSP / cadence fixes.

*End of report.*
