# Session 173 — capture.db retention probe; finish-position gap uncovered

**Opened:** 2026-06-22 15:49 ACST (recommenced from a broken chat — see Session shape)
**Closed:** 2026-06-22 17:21 ACST
**Duration:** ~1.5h active, single workday, no day-rollover.
**Tool routing:** Claude Chat (planning / triage / probe) + Desktop Commander (governance reads, VPS access). No Code session — Chat-side governance + read-only data probe only.
**Governing DRs invoked:** DR-021 (anchoring), DR-027/028 (two-database boundary — re-read trigger fired), DR-013 read-discipline (mode=ro, never copy), DR-029 (data-layer fit-for-purpose), DR-032 (Betfair canonical reference).

---

## Anchor

- **Open:** `2026-06-22 15:49 ACST` (carried from the broken chat's open-ritual anchor).
- **Close:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-06-22 17:21 ACST`.
- S172 closed 15:42 ACST; S173 opened 7 min later — straight continuation.

## Pre-flight checks

- This session **recommenced a broken chat.** The original S173 chat ran the open-ritual (anchor 15:49, orientation reads, drift-check clean) and crossed off the `standing_instructions.md` re-upload item in `current_state.md`, then broke mid-probe. The operator pasted the broken transcript to resume.
- As a fresh instance, re-loaded live state from disk before any action: `current_state.md`, `external_api_resources.md`, `interface_triage/betlog_scope.md`, `decisions.md` (DR-013/027/028).
- Confirmed the S173-open cross-off persisted (standing_instructions item struck + ✅ in `current_state.md`).
- Pre-close directory listing: rebuild root clean, no phantom files.

## Session shape

A recommenced, single-thread session. The original S173 broke immediately after the operator asked whether `capture.db` has the right granularity for both auto-settled and days-late manual bets. This session re-oriented, re-registered the DR-027/028 cross-DB boundary (the brief-2 re-read trigger), and ran brief 2's opening step — the read-only `capture.db` retention + granularity probe — over the VPS tunnel.

What was scoped as a quick retention confirmation turned into a material finding: retention is ample, but the *outcome* granularity has a regime change that breaks finish-position (place) data for recent races — the exact data Safety Net and Synthetic Each-Way late-entry depend on. The session closed on that finding, with brief 2 reshaped and forward routing set to resolve the gap before brief 2 can be scoped.

## What was delivered

1. **Recommenced the broken session + re-registered the cross-DB boundary.** Re-read DR-027 (race-data in `capture.db`, bet-data in v3's store, joined by reference via `vps_client`) and DR-028 (no caching / no denormalisation / no second integration point). Logged the nuance: this Chat-side governance probe may read `capture.db` directly read-only (DR-028 blesses unlimited reads), but **brief 2 must spec v3's manual-entry reads to go through `vps_client` / the data API, never raw SQLite**.

2. **Tunnel diagnosis + operator brought it up.** The VPS SSH tunnel (`127.0.0.1:8400` → `racing-api.service`) was down (no listener, `PORT_8400_CLOSED`). Pointed the operator at the existing `bethub-v2/scripts/vps-tunnel.sh --bg` (auto-reconnect). Operator launched it; `/health` confirmed reachable, collector active, db at `/home/racing/racing-data-capture/data/capture.db`.

3. **Read-only `capture.db` probe (mode=ro, never copy).** Introspected the data API surface (today/upcoming + per-race-id only — no date-range endpoint), then SSH-exec read-only Python against the DB for schema + retention + fill-by-age.

4. **Findings — retention.** `races` spans **2025-03-03 → 2026-06-22** (86,613 races, 476 days, nothing pruned). Retention is ample; a bet logged days or months late always finds its race row. The question that opened brief 2 is answered.

5. **Findings — granularity (the material one).** Among bet-relevant races (those with a `betfair_win_market_id`):
   - **Win/lose solid:** `result_status` (WINNER/LOSER/REMOVED) ~95%, `betfair_selection_id` ~95%, win + place market ids present.
   - **BSP fine but relocated:** lives in `betfair_snapshots.bsp_price` (~82–85% May/Jun), **NOT** in `betfair_historical` (a static 12-month import that dead-ends **2026-02-28**). Any BSP read must target the snapshot table.
   - **`finish_position` BROKEN for recent races:** fill collapses after the Feb handover — ~13% Mar, **0 of 43,075** in May, 3 of 33,547 in Jun. Verified on a real settled race (Ballina R1, 21 Jun): winner shows `result_status=WINNER` but `finish_position=NULL`; placed runners are just `LOSER` with no ordinal.

6. **Reshaped brief 2 + reframed the Racing-API question.** For days-late manual entry: win/lose is resolvable from `capture.db`, but **Safety Net place refunds (2nd–4th) and Synthetic Each-Way are NOT** — `finish_position` is empty, no stored place result post-Feb, and the live Betfair place market is gone ~45 min after the race. Since manual entry exists mainly to catch up Strategy 1 (Safety Net) bursts, the gap hits its primary use case. Finish positions are the Racing API's output and they stopped landing ~Apr/May — which reframes the parked $100/mo cancellation question (the feed's key output already isn't landing: either a broken pipeline possibly already degrading *live* Safety Net auto-settle, or a non-delivering subscription). Noted `capture.db` holds `betfair_place_market_id` per race, so place outcome could instead be **derived from the Betfair place-market settlement** — a design option for brief 2.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open + close timestamps anchored in ACST. ✓
- **DB read discipline (mode=ro, never copy):** `capture.db` opened read-only via URI; only aggregates/samples returned over SSH; no copy to local disk. ✓
- **DR-027/028 re-read trigger (Cat 1 / sensitivity):** fired at brief-2 start; both DRs re-read and cited by number; the direct-read-vs-`vps_client` nuance logged. ✓
- **Cross-DB by-number citation:** DR-028 forbidden-pattern #3 named when distinguishing the probe (direct read OK) from v3's manual-entry path (must go through `vps_client`). ✓
- **Filesystem / REPL discipline:** read-only probe scripts run via `start_process`; no writes to `capture.db`; SSH `BatchMode` to fail fast. ✓
- No standing instruction authored or edited this session.

## Open items in (carried / new for S174)

- **NEW — finish-position gap (the session's headline).** `capture.db` `finish_position` collapsed to ~0 for recent bet-relevant races; breaks Safety Net place (2nd–4th) + Synthetic Each-Way late-entry settlement. **Blocks brief 2.** S174 primary.
- **NEW — BSP read targets `betfair_snapshots`, not `betfair_historical`** (the latter dead-ends 2026-02-28). Note for any brief touching BSP.
- **Brief 2 (manual entry)** — retention step DONE; now blocked-on a place-result source. Reshaped, not yet draftable. Still folds in the feed-robustness guard + write-path spot-check when it does.
- Carried: bet-mutation audit log (own brief, after brief 2); bets-feed robustness guard (into brief 2); launcher rebuild-if-source-newer (into F9/F10 brief); brief 3 free-bet credit-in; dark theme (parked); full parking lot per `current_state.md`.

## Open items out (closed / resolved S173)

- **`capture.db` retention question — ANSWERED.** 15.5 months retained, nothing pruned. The original brief-2 opening question is closed.
- **Broken-chat recovery** — recommenced cleanly; the S173-open `standing_instructions.md` cross-off confirmed persisted to disk.

## Session close state

- **Rebuild root:** clean, no phantom files.
- **`current_state.md`:** rotated to S173 close (17:21 ACST); Where-we-are = the probe finding; What's-next = resolve the gap.
- **`v3_build_picture.md`:** Interface-refinement stream moved (retention check done → blocked-on place-result source); updated + timestamp bumped.
- **`standing_instructions.md`:** untouched (no edits this session).
- **`.close_out_backups/`:** `SESSION_174_opening_prompt.md` written; stale `SESSION_173_opening_prompt.md` removed.
- **VPS tunnel:** left running (operator's `--bg` launch) for the next probe; operator can `./vps-tunnel.sh --stop`.

## Forward routing (confirmed with operator)

Operator closed after the finding with "I'll pick it up next session." The next session's shape follows directly from the session's outcome.

**S174 primary deliverable — resolve the place-result gap before brief 2 scopes.** Two strands:

1. **Read v3's `settlement.py`** to confirm whether live auto-settle reads `capture.db` `finish_position` or the Betfair place-market settlement — this decides whether the operator's *current* live Safety Net settlement is already exposed by the gap (urgent if so).
2. **VPS-side diagnostic** on why finish positions stopped landing ~Apr/May (Racing API status / a broken results-backfill job) — which also informs the parked Racing-API cancellation decision.

Then re-scope brief 2 with a real place-result source (fix the pipeline, or derive place from the Betfair place-market settlement). Racing-API cancellation stays parked pending strand 2.
