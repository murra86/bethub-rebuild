# Placings backfill — deficit-drop verification + wall characterisation (read-only)

**Session:** 218 (headless runner, guarded fallback action). **Anchored:**
2026-07-02 12:42 ACST open; investigation ran ~12:44–12:47 ACST.
**Target:** `root@187.77.183.9` : `/home/racing/racing-data-capture`, live
`data/capture.db`.
**Mode:** READ-ONLY throughout — every DB read opened `mode=ro` / `sqlite3
-readonly`; no `capture.db` write; no Racing-API fetch probe run; no code
touched; no Betfair/settlement/money/live path near this work. Throwaway
decomposition script written to `/tmp` only.
**Why this action:** S218 first action was guarded on Code's settlement build
report, which is **not present** in the rebuild root — so the guard fell through
to the read-only placings backfill look carried from S215/S216. VPS access
re-verified first (ssh-agent holds `tim@racing-vps`; VPS reachable).

---

## Objectives (carried from S215/S216)

1. Verify the ~6.1k `recoverable_deficit` drop (41,633 → 35,718) is **real fills**
   vs a **metric-scope / 404-reclassification** artifact — the S215 caveat, since
   the drop exceeded the run's visible fills.
2. Characterise the `post_retry_truncated` wall.
3. Retire-vs-chase on the oldest ~100 backlog dates.

---

## Finding 1 — the ~6.1k drop is REAL FILLS. Bankable. (RESOLVES the S215 caveat.)

The burndown log shows the drop landed on the 2026-07-02 05:33 ACST pass logged
as `placings=0 retired=0 walled=6` — i.e. **not** the backlog pass's own work.
Decomposing the live window `[2026-03-15, now-14d)` (the exact
`_recoverable_deficit` predicate) shows where it came from:

- **`exhausted` dates in the strike sidecar = 0.** RAW deficit (no-exclusion) ==
  RECOVERABLE deficit == **36,033** now. The metric is hiding **nothing** behind
  exhaustion/retirement exclusions — so the drop is **not** metric-scope shrinkage
  and **not** 404-reclassification pulling dates out of the count.
- **Recent genuine fills, right size:** in-scope runners with `finish_position`
  set whose `races.updated_at` is within **2 days = 6,528**; within 3 days =
  **8,482** (of 9,537 total in-scope filled). That recent write batch matches the
  ~5,915 burndown drop (41,633 → 35,718) in magnitude.
- **Legitimate source:** those fills carry `results_source = subscription` (Racing
  API), not nulls/placeholder. `max(races.updated_at)` = 2026-07-02T03:17 UTC
  (~12:47 ACST) — writes are live and ongoing.
- **Mechanism:** the fills came via the **normal subscription sync** (which writes
  `finish_position` as Racing-API results mature), not the deep-backlog recovery
  pass — which is why the burndown showed a real drop with `placings=0` attributed
  to the pass. The S213/S214 empty-runners contention fix let the sync write
  cleanly through collector windows, and a batch matured in.

**Verdict:** bank the drop as real progress. Current metric ≈ **36,033** (drifts a
few hundred up/down as the moving 14-day upper edge ages fresh unfilled dates in;
floor fixed at 2026-03-15).

## Finding 2 — `post_retry_truncated` is the transient collector-contention wall, unchanged

- **What it is (code + S214):** the "soft wall / degraded" class — a fetch that
  stayed empty-200 *after* `sync_day`'s per-meet retries. It does **not** strike or
  retire the date (correctly — the date is recoverable). The pass stops the night
  after `BACKLOG_TRUNCATED_WALL_THRESHOLD = 6` consecutive such fetches.
- **Confirmed transient, not runner-less:** S214 re-fetched the 6 walled dates
  fetch-only and got FULL runners on every one (03-21: 1540 … 06-07: 970). The
  mode is triggered by our write path competing with a heavy live collector, not
  by the API having no data.
- **Why it walls now:** the recovery pass is scheduled `OnCalendar 05:30
  Australia/Adelaide` — one nightly run — and that window overlaps collector load.
  The 07-02 05:33 pass walled 6/6 immediately. The collector was writing ~15,006
  `bookmaker_snapshots` rows in the trailing minute at investigation time — exactly
  the heavy-burst condition the diagnosis named as the trigger.

## Finding 3 — retire-vs-chase: CHASE. The blocker is scheduling/contention, not data.

- The ~36k is **genuinely recoverable** (fetch-only proven) and `exhausted = 0`
  correctly reflects that nothing has been abandoned. Retiring the oldest dates
  would discard real analytical placings data that the API still serves.
- **Two-speed drain is already in play:** the newer half of the window is draining
  organically via the normal subscription sync as results mature (Finding 1). The
  genuinely stuck portion is the **old top-deficit dates the normal sync will never
  reach back to** — 2026-03-21 (1,279), 04-18 (1,264), 05-30 (1,255), 04-11
  (1,230), 03-28 (1,082); ~5 dates ≈ 6.1k runners. Those need the recovery pass (or
  a targeted low-contention refetch) — and that pass keeps walling on collector
  load at 05:30 ACST.
- **Lever (for a future fix-brief, NOT actioned here — read-only look):** re-time
  the recovery pass to a genuinely quiet collector window, and/or apply the
  inter-date-pacing bump flagged at S215, so the pass stops false-walling. No code
  or schedule was changed this session.

---

## Bet-safety / discipline

CLEAN. Read-only analytical-line work only (DR-033): capture.db `mode=ro`, no
writes, no file copy; no Racing-API fetch probe fired; systemd/sidecar reads only;
throwaway script in `/tmp`. No Betfair, settlement, money, or live-betting path
touched. `bethub-v3` not touched. v2 not touched.

## Recommended next action

1. **Bank Finding 1** — deficit metric is trustworthy; the drop is real; current
   recoverable ≈ 36,033, `exhausted = 0`.
2. **Backlog is chase-not-retire**, but the deep old dates are stuck behind the
   05:30-ACST collector-contention wall. Next backfill work item = a fix-brief to
   re-time the recovery pass (and/or add the S215 inter-date pacing bump) so it
   stops walling — scoped as capture-side analytical, no schema change.
3. Settlement build-report triage remains the primary first action **whenever Code
   ships the report** — this backfill look was the guarded fallback, not a
   re-route.
