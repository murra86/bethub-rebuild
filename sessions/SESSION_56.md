# Session 56

**Title:** BSP write-back report triage. Outcome partial-success — 3/5 §7.2 criteria hit cleanly; criteria #4 and #5 not exercised due to no AU thoroughbred CLOSED market in window. Finding (a) ("orchestrator silent loop") investigated empirically and dismissed — behaviour was correct for past-jump catalogue. Saturday data loss confirmed caused by lock-contention bug (since fixed), not by the API observation probe. §2.1 BSP-gap verification deferred to Session 57 once Devonport R1 settles.
**Opened:** 2026-05-03 10:10 ACST
**Closed:** 2026-05-03 11:00 ACST
**Wall-clock:** 50 min (single sitting, single workday — same-workday continuation of Session 55's 09:52 close).
**Tool routing:** Claude Chat. No Code routing this session — BSP write-back Code report consumed; verification Code routing deferred to Session 57.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-DB integration boundary discipline), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-03 10:10 ACST`.
Close: same command → `2026-05-03 11:00 ACST`.

Sunday morning, same-workday continuation of Session 55's 09:52 close (18 min gap; same-workday per Cat 1).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- 13 `.md` files at rebuild root + `openapi.json` (matched expected count at Session 55 close).
- All directories present.
- `.close_out_backups/` contained `SESSION_56_opening_prompt.md` only (Session 55 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-03 09:52 ACST` matched Session 55 close; `sessions/SESSION_55.md` present and non-empty; `v3_build_picture.md` last-updated `2026-05-03 07:20 ACST` matched (artefact didn't move at Session 55 close — correct).
- Governing DRs named in orientation summary.
- Same-workday calendar-calibrated recap delivered (tight).
- V3 build picture: skipped silently (no stream movement Session 55).
- Open-items delta: skipped silently (no meaningful between-session delta).
- Pre-flight check on `dr029/2_1_race_data/bsp_writeback_report.md` confirmed present at expected path. Code did execute.

## Session shape

Session 56 was a **single-deliverable triage session** that expanded into mechanism-investigation. Operator opened with the BSP write-back report landed and a flag that "no races available yet" — a signal that the report would surface a window-timing issue.

Three substantive threads ran in sequence:

1. **BSP write-back report triage.** Read the report in full. Surfaced as partial-success: edits land cleanly, services restarted cleanly, dirty-tree discipline preserved exactly, but criteria #4 and #5 ("at least one settled race shows BSP populated", "BSP values are sane") could not be exercised due to two distinct blockers — Code's Finding (a) (orchestrator's snapshot loop "silently inactive") and Finding (b) (no AU thoroughbred CLOSED market in window).

2. **Mechanism investigation — Finding (a).** Operator pushed back on the framing: "could this be because it was overnight?" Empirical check via direct VPS queries reframed Finding (a) entirely. The orchestrator wasn't silently broken — it was correctly transitioning Saturday's past-jump catalogue into POST_START phase (skipping STANDARD/INTENSIVE), which means the snapshot loop never engages. The "silent loop" was correct behaviour for the catalogue state, not a bug. Combined with the lock-contention bug (separately) clearing Saturday writes, this produced the appearance of a 13-hour blackout that wasn't actually one.

3. **Saturday data-loss attribution.** Operator surfaced a second hypothesis: "could the probe have caused Saturday's data loss?" Empirical check via journalctl logs ruled this out conclusively — `database is locked` errors began at 19:33 ACST Friday evening (well before the probe started Saturday morning), persisted through 36 hours of orchestrator log noise, and ended only with the lock-fix restart Sunday morning. Probe writes go to JSONL files in the rebuild folder, not capture.db; mechanism for interference does not exist. Saturday data loss is cleanly attributable to the (now-fixed) lock-contention bug.

Substantively closed: §2.1 BSP-gap verification deferred to Session 57, contingent on Devonport R1 settling with Betfair's `actualSP` reconciliation complete (~01:50 UTC = 11:20 ACST plus probe-validated 45-min reachable window = earliest verification ~11:50 ACST). Operator chose option 1 (verify directly via Desktop Commander next session, no Code re-run needed if direct-query verification is clean).

The session also surfaced an existing operational artefact worth capturing: the `liveness_check.py` cron at `/home/racing/racing-data-capture/scripts/liveness_check.py` has been firing 15-minutely emails through the Saturday gap, correctly detecting the snapshot staleness against its 4-hour threshold. Will go silent at the next 15-min run (10:45 ACST onwards) now that fresh snapshots are landing on Devonport R1.

## What was delivered

### 1. BSP write-back report triage — outcome documented

The fix itself is correctly applied (line 200 projection set is now `["SP_AVAILABLE", "SP_TRADED"]`; NaN-guard comment landed in `client.py`; stale comment in `orchestrator.py` updated). Three files parse cleanly. Service restart clean. Dirty-tree discipline preserved exactly (13 modified + 7 untracked, identical pre/post). No scope creep — brief's hard limits held.

Verification of criteria #4 and #5 deferred to Session 57.

### 2. Finding (a) reframed and dismissed

Code's report described "Betfair snapshot loop has been silently inactive since the lock-fix restart." Empirical investigation reframed this:

- Orchestrator log shows discovery cycles ran every 30 min Saturday returning "0 new races, 122 total active" (with 36 hours of `database is locked` errors).
- Saturday post-restart, all 147 race phase transitions went PENDING → POST_START (past-jump), not PENDING → STANDARD/INTENSIVE — by design, snapshot loop only engages on STANDARD/INTENSIVE phases.
- Sunday catalogue (post-BSP-fix restart at 09:46 ACST): first STANDARD transition at 10:08 ACST (tauherenikau R3), Devonport R1 transitioning STANDARD at 10:42 UTC, snapshot bursts at 10:42, 10:47, 10:53 (5-min STANDARD cadence). Loop is firing correctly.
- 18 snapshots written for Devonport R1 by 10:53 ACST.

**Resolution:** Finding (a) closed. Behaviour was correct, framing was wrong (Code's 17-min observation window was insufficient to distinguish "loop broken" from "loop waiting for in-window races"). Not a separate fix scope.

### 3. Saturday data-loss root cause confirmed

Empirical check of `racing-capture.service` journalctl logs:

- First `database is locked` error: **2026-05-01 10:03:02 UTC = 19:33 ACST Friday evening.**
- Last successful `betfair_snapshots` write before gap: **2026-05-01 10:41:56 UTC = 20:11 ACST Friday evening.**
- Probe started: **2026-05-02 00:35:30 UTC = 10:05 ACST Saturday morning** (14 hours into lock state).
- Probe finished: **2026-05-02 10:47:21 UTC = 20:17 ACST Saturday evening.**
- Lock state continued through to Sunday morning lock-fix restart at 21:24:59 UTC May 2 = 07:24 ACST Sunday.

Probe writes target JSONL files in `dr029/2_1_race_data/api_probe_data/`, not `capture.db`. No mechanism for interference. Saturday data loss caused entirely by the lock-contention bug, which is now fixed (zero `database is locked` errors in today's orchestrator log).

**Disposition:** accept the gap, do not backfill. Strategy 1 and Strategy 2 P&L unaffected (analytical-side loss only); Harville calibration sits on 12 months of clean BSP data, one Saturday is statistical noise; Betfair Historical Data backfill not worth the cost. Documented for incident reference.

### 4. Health-check liveness cron surfaced as existing infrastructure

The 15-min email alerts the operator was receiving traced to `scripts/liveness_check.py` on the VPS — a pre-existing operational artefact. Mechanism: 4-hour staleness threshold on `MAX(snapshot_time)` in `betfair_snapshots`, fires only during racing hours (-1h to +2h around any scheduled race), 30-min cooldown between alerts. Was correctly detecting the Saturday gap. Self-clears once snapshots resume — verified that next cron run at 10:45 ACST will read fresh data and exit silently.

**Implication:** the post-DR-029 monitoring scope I had loosely sketched (database-lock pattern check + snapshot-staleness check) is smaller than expected. **The snapshot-staleness check already exists.** Only the `database is locked` log-pattern check would be net-new. Adjusted the future-monitoring open item to reflect this.

### 5. Verified today's racing-data capture is healthy on AU thoroughbred path

Empirical confirmation:

- Zero `database is locked` errors in racing-capture log since midnight UTC today (10+ hours of clean operation).
- Zero `ERROR` lines in racing-capture log today.
- Devonport R1 snapshot capture firing on 5-min STANDARD cadence.
- Forbes R1 (next AU thoroughbred, 11:35 ACST jump) discovered with `betfair_win_market_id` populated; will engage when it transitions to STANDARD ~10 min before jump.
- NZ harness (Tauherenikau) and Tasmanian synthetic races discovered without Betfair WIN bindings — pre-existing architectural reality (not a regression). These are bookmaker-only retail markets, not Betfair-tradeable.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered (18 min between close and open).
- **Cat 1 (V3 build picture conditional render)** — skipped silently (no stream movement Session 55).
- **Cat 1 (open-items delta)** — skipped silently (no meaningful between-session delta).
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Triage of the BSP report was longer-form by design (single load-bearing artefact, structured triage). Mechanism-investigation responses kept tight; framed with "this deserves a little detail" implicitly via the empirical-check structure.
- **Cat 1 (decision-maker framing)** — held. Three operator decisions surfaced cleanly: accept Saturday data loss / scope backfill (operator: accept); routing on Finding (a) (operator: decided after empirical check that Finding (a) was overstated, no scope needed); wait-window use (operator: option 1, verify directly next session). Each was framed as a decision with options and reasoning.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. Operator said "go ahead" and "one at a time" — proceeded without offering alternatives.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders throughout; "Fix 4", "§2.4", "§7.2", "§2.10" all unwound on use.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open and at close.
- **Cat 2 (Desktop Commander default)** — held throughout. All filesystem and SSH operations via `Desktop Commander:start_process`. Multiple `tool_search` calls mid-session to load `start_process` parameter schema (deferred-tool pattern — expected) and `filesystem` tools.
- **Cat 2 (no-DB-file-copy)** — held. All capture.db queries via `ssh root@... sqlite3 ...` against the live VPS DB; no copy.
- **Cat 2 (operational/analytical line discipline)** — n/a; no Betfair-cadence-shaped discussions this session.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 2 (write_file vs create_file gotcha)** — held. This session record uses `Desktop Commander:write_file`.
- **Cat 3 (external API resources reach-for)** — instruction was authored Session 55. Not exercised this session — BSP triage was about the report's own contents and orchestrator behaviour, not API-shape questions. Will exercise from Fix 4 brief drafting onwards.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary held cleanly throughout — capture.db queries were read-only verification only, no integration-shape discussions.
- **Cat 4 (operator review of artefacts is between-session work)** — held. BSP report was the artefact-under-review this session; operator has now triaged.
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a this session; carries forward.
- **Cat 5 (software questions are Claude's)** — held. Ritual-level decisions (mechanism investigation order, accepting vs scoping Saturday backfill, recommending option 1 for the wait-window) framed with reasoning + recommendation, operator picked.

**No new standing instructions surfaced this session.** Cat 3 instruction from Session 55 noted but not exercised.

## Open items in (carried forward)

All non-closed items from Session 55 carry forward to Session 57. Status updates:

- **§2.1 BSP write-back fix verification (deferred to Session 57)** — fix is correctly applied; criteria #4 and #5 verification deferred until Devonport R1 settles with `actualSP` reconciliation complete (~11:50 ACST or later).
- **§2.4 Fix 4 cadence design** — unchanged. Brief drafting unblocked once §2.1 BSP-gap closes.
- **§2.5 soft-book interface contract** — unchanged.
- **§2.10 external analytics scan** — unchanged. Inventory write-up is the remaining work.
- **WIP §16** — VPS in-flight work (13 modified + 7 untracked post-BSP-fix). BSP fix landed inside the existing modified-files batch as planned.
- **Pending architectural extension (Session 42)** — unchanged. Post-DR-029 documentation pass.
- **Fix 9 (Racing API re-fetch)** — unchanged.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — unchanged.
- **Three-row collision per-row triage** — unchanged. Non-gating.
- **Low-confidence match review** — unchanged. Non-gating.
- **Durable Fix 8 merge tooling** — unchanged.
- **Session numbering slip in probe brief** — unchanged. Cosmetic.
- **EX_LADDER entitlement question** — unchanged. Operator-side homework.
- **Missing Saturday race data** — closed-with-disposition (this session). See "Open items out".
- **Drift-check methodology gap** — unchanged. Light-touch; folds into next pre-flight pattern naturally.
- **`bethub-analytical` project awaiting activation** — unchanged. Out-of-rebuild-project work.

**New (Session 56):**

- **Post-DR-029 monitoring layer (smaller scope)** — `liveness_check.py` cron already covers snapshot-staleness check (4-hour threshold, racing-hours-only, 30-min cooldown). Net-new addition: `database is locked` log-pattern detection. Single small brief, post-DR-029. Not gating. Parked.
- **§2.1 BSP-fix code finding (c) — stale docstring at `client.py:189`** — `"""Fetch realised BSP per runner via SP_TRADED projection."""` is stale post-fix (actual projection is `SP_AVAILABLE + SP_TRADED`). Trivially fixed in any future Fix 4 / §2.10 brief that touches the file. Not load-bearing for behaviour.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — gap is likely NZ + harness + greyhound that match via bookmaker-only with no Betfair binding. Out of scope for §2.1 fix. Materially affects the substrate Fix 4 / §2.5 will reach for. Surfaced for forward reference.

## Open items out

- **Missing Saturday race data — closed with disposition: accept the gap.** Strategy 1 and Strategy 2 P&L unaffected (analytical-side loss only); 12 months of clean Harville calibration data already imported, one Saturday is statistical noise; Betfair Historical Data backfill not worth the cost. Root cause: lock-contention bug at `racing-api.service` (now fixed via lock-fix landed Session 54). Probe ruled out as cause via empirical timeline check.
- **Finding (a) ("orchestrator silent loop")** — closed-as-not-a-bug. Behaviour was correct for past-jump catalogue. Code's framing was overstated due to short observation window post-restart; not a separate fix scope.

## Session close state

- **Rebuild folder root:** 13 `.md` files + `openapi.json` (unchanged from Session 55 close). No phantom files. All directories present.
- **`current_state.md`:** to be updated by close ritual.
- **`v3_build_picture.md`:** no stream state moved this session. §2.1 BSP-fix is in-flight pending verification — same status as at Session 55 close. Artefact untouched. Timestamp remains `2026-05-03 07:20 ACST`.
- **`standing_instructions.md`:** unchanged this session.
- **`sessions/`:** Session 56 record written by close ritual.
- **`.close_out_backups/`:** Session 56 opening prompt removed at close; Session 57 opening prompt to be written by close ritual.
- **Project knowledge base:** unchanged. (Session 55 noted `standing_instructions.md` re-upload pending — operator-side action carries forward, no new edits this session.)
- **VPS state:** healthy. Zero `database is locked` errors today. Snapshot loop firing on Sunday races. Devonport R1 capturing on 5-min STANDARD cadence. Liveness-check cron will go silent at 10:45 ACST onwards.
- **`bethub-analytical/`:** unchanged. Project remains scoped but not yet active.

## Forward routing

**Confirmed with operator at close:** "carry on in the next [session]" — operator has chosen option 1 (verify §2.1 BSP-gap directly via Desktop Commander next session, no Code re-run needed if direct-query verification is clean).

Session 57 primary deliverables (in order):

1. Pre-flight: confirm Devonport R1 has settled and Betfair `actualSP` reconciliation has completed (post-CLOSED+45min window). Earliest reasonable check: ~11:50 ACST. If §2.1 BSP-gap verification can run today.
2. Run §7.2 verification query (re-cast against `runners` join per Code's note in BSP report §2.3) — confirm `n_with_bsp = n_active_runners` for Devonport R1 and any other settled AU thoroughbred WIN markets.
3. Confirm `bsp_price` magnitudes are sane (`0 < bsp_price < 1000`; no NaN-encoded floats).
4. If clean → §2.1 BSP-gap closes, §2.1 surgical-fix arc moves to Fix 5 (venue harmonisation, brief drafting independent) and Fix 4 (cadence design, brief drafting unblocked).
5. If issues → root-cause triage; route to follow-up brief or Code re-run.

**Out of scope for Session 57:** Fix 4 cadence design Code execution; §2.6/§2.7/§2.8/§2.9 reframing; `bethub-analytical/` activation work; post-DR-029 monitoring brief drafting.

**Operator-side actions between sessions:**

1. Wait for Devonport R1 (and ideally one more AU thoroughbred WIN market) to settle and reconcile.
2. Re-upload `standing_instructions.md` to bethub-rebuild Claude Project knowledge base — carried over from Session 55, no new edits this session but operator-side action still pending.
3. Optionally: review `bethub-analytical/README.md` and decide on activation timing.
4. Open Session 57 with the standard "open session 57" trigger plus a note on whether Devonport R1 has settled and reconciled.
