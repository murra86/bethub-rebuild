# Report — empty-runners degradation: contention fix (decouple fetch-from-write)

**Brief:** `placings_empty_runners_contention_fix_brief.md` — LOCKED (Session 213, 2026-07-01, sha256 `3666d66c…`). Read end-to-end at session start; all §3 pre-reads consumed in order (this brief → diagnosis report → diagnosis brief → `subscription/racing_api.py` → `scripts/backfill_race_metadata.py`). Brief integrity confirmed (sha256 matched the locked value).
**Status:** EXECUTED — the §5.1 restructure landed in `subscription/racing_api.py` (fetch-phase then write-phase). One file edited, byte-exact isolated. Verification burn run; the empty-runners mode **still fired** during a heavy collector window — reported as a finding, no "solved" verdict (that is operator-Claude's call).
**Session:** 2026-07-01, verification window ~15:21–15:27 ACST (DR-021 Adelaide, ACST = UTC+9:30; ≈ 05:51–05:57 UTC). Target `root@187.77.183.9` : `/home/racing/racing-data-capture`.
**Bet-safety:** CLEAN by construction — analytical/capture side only (DR-033). No operational/betting DB, no Betfair operational path, no bet mutation, no `race_date`/identity logic, no timer, no collector touch.

---

## 1 — What changed in `sync_day()` (§5.1)

`sync_day()` in `subscription/racing_api.py` was restructured from a single **interleaved per-meet fetch-then-write loop** into two **sequential phases for the date**. Nothing else in the file changed — proven byte-exact (below).

**Before** (one loop): for each meet → `_fetch_meet_races(meet_id)` → *immediately* write that meet's races/runners via `_sync_single_race()` (which calls `upsert_race`/`upsert_runner`, each self-committing). Fetches and `capture.db` writes were interleaved: the paced, multi-second fetch loop held/released the `capture.db` write lock repeatedly, co-timed with the live collector — the write-path contention trigger the diagnosis isolated (report §2c/§2d).

**After** (two phases):
- **Fetch phase** — iterate the date's meets, call the unchanged `_fetch_meet_races()` for each, and accumulate `(meet_id, races_list)` in a `fetched_meets` list **in memory**, writing nothing to `capture.db`. Pacing (`delay`, `meet_idx > 0`), the retry/backoff, the empty-*races-list* retry, and the §5.1 empty-runners instrumentation inside `_fetch_meet_races` are all untouched. The `truncated` / `empty200_pre` / `empty200_post` counters are computed here exactly as before.
- **Write phase** — once every meet is fetched, iterate `fetched_meets` and write via the unchanged `_sync_single_race()` upsert path. Upsert semantics, conflict keys, `race_date`, per-upsert commits, and the return-dict shape are byte-for-byte identical to the prior loop.

This is purely a reordering of **when** writes happen relative to fetches within a date — not a change to **what** is written or how conflicts are resolved. During the (long, paced) fetch phase the process now holds no `capture.db` write lock at all; the date's writes are compressed into one tight burst afterward.

**Transaction wrap (§5.1 "do if clean, don't force it") — NOT taken, deliberately.** The upsert path self-commits inside **each** `upsert_race`, `update_race_coverage`, and `upsert_runner` (`storage/database.py` lines 348, 404/433, 464). A single date-level transaction is therefore **not cleanly achievable from within `racing_api.py` alone** — any `BEGIN` opened in `sync_day` would be terminated by the first internal `conn.commit()`. Forcing it would require editing `storage/database.py`, which is out of scope (§9). Per the brief's explicit "don't force it," no wrap was added; commit semantics are unchanged. This means the write phase is a burst of many small commits (as before), just relocated to after all fetches. Noted as a candidate for a future, in-scope-for-that-brief change (would require the second file).

**Memory footprint:** a non-issue as the brief anticipated — one date ≈ 77–152 race rows / low-thousands of runners held as already-parsed dicts before the write burst.

**Edit isolation (proven byte-exact):** reversing *exactly* the two-phase hunk on the post-edit file reproduces the session-start sha256 `6abc0303f1f3e96c…` — i.e. the fetch/write split is the **only** change to the file. The pushed VPS file round-trips identically to the local edit. Owner preserved (`racing:racing`). `py_compile` + import clean under the VPS venv for both anchor files; `sync_day` signature intact (`(conn, date_str, delay=0.0) -> dict`).

## 2 — `run_backlog_pass()` compatibility check (§5.2) — COMPATIBLE, no second-file edit

`run_backlog_pass()` in `scripts/backfill_race_metadata.py` does **not** depend on `sync_day()` writing incrementally per-meet:

- **Progress accounting** is `_count_filled(conn, date_str)` taken **before and after the entire `sync_day()` call returns** (lines 273, 286) — a direct DB read of `finish_position` counts, never a per-meet signal. Batching all writes to date-end is invisible to it (the "after" read runs once `sync_day` has fully returned, by which point every write is on the connection).
- It otherwise consumes **only** the returned dict fields `error`, `races_synced`, `truncated`, `positions_seen` — all still populated identically by the restructured `sync_day`.
- No per-meet write count is surfaced or logged; no partial-date resume; no assumption that meet N's row is visible before `sync_day` returns.

Conclusion: **compatible as-is.** No incompatibility surfaced, so — per §4/§5.2/§9 — the second file was **not edited**. Confirmed byte-identical at close (sha256 `cc99a2ee…`, unchanged from session start).

## 3 — Verification burn results (§7)

**Baseline (`mode=ro`, immediately before the burn; 15:21 ACST / 05:51 UTC):**

| Metric | Value |
|---|---|
| Recoverable deficit (≥ 2026-03-15) | **36,650** (consistent with the diagnosis report's close) |
| Backlog dates (total, deficit-ordered) | 100 |
| Burn window (fixed = top-40 deficit-ordered dates) | 2026-05-23 … 2026-03-27 |
| Filled across window | 3,505 |
| Thoroughbred race-rows across window | 3,013 |

**Burn** — `run_backlog_pass(delay=0.2, max_attempts=40)`, the **unchanged production pacing config** (the exact mechanism the diagnosis §7 used), writing placings via the normal restructured path. Start 15:22:25 → end 15:23:15 ACST (05:52:25 → 05:53:15 UTC).

| Metric | Value |
|---|---|
| Wall time | 49.9 s |
| Dates attempted | **7** (of 40 — walled early) |
| Dates that gained placings | 1 (2026-05-23) |
| Total placings gained (this burn) | **931** |
| Achieved req/sec | **3.06** (153 requests / 49.9 s; ≤ 5/sec ✓) |
| Walled | 6 (hard_error = **0**, post_retry_truncated = **6**) |
| empty-runners occurrences (this burn) | **6 dates** (dates 2–7, mode fired) |
| Still walls? | **Yes** — on 6 consecutive post-retry-truncated (the empty-runners mode) |

Per-date (attempt order): `2026-05-23` full (143 races, `runners_synced`=1179, positions=955, **+931 placings**, refined 134 → PLACED); then `2026-03-21 / 04-18 / 05-30 / 04-11 / 03-28 / 06-07` each returned **races present, 0 runners** (empty-runners mode) and walled at `truncated_streak 6/6`. The captured §5.1 signature during the burn is identical to the diagnosis: clean HTTP **200**, populated `races`, all-empty `runners`, `notices=None`, `cf-cache-status: DYNAMIC`, `via: 2.0 heroku-router` (meet `met_aus_949899694074`, 1 race / 0 runners). This reproduces the pre-fix burn almost exactly (diagnosis §7: attempted 7, filled 1, +963, 6 truncated).

**Transience confirmed (fetch-only probe, `mode=ro` for verification / no `capture.db` write; 15:24:29–15:25:07 ACST):** re-fetching the 6 walled dates fetch-only returned **FULL runners on every one** — 2026-03-21: 1540, 04-18: 1647, 05-30: 1742, 04-11: 1613, 03-28: 1267, 06-07: 970 — matching the diagnosis's fetch-only baselines. The walled dates are the **transient degradation mode, not genuinely runner-less**; the mode reset once our write path went idle.

**Collector window — genuinely busy (observed).** During the burn the live collector was writing `bookmaker_snapshots` at extreme rate: **39,279 rows in the trailing 1 minute** (max snapshot_time current, `capture.db-wal` ≈ 6.0 MB) at 15:26 ACST. The 15:22–15:23 ACST burn ran squarely inside a heavy live-odds capture burst — exactly the collector-load condition the diagnosis named as the mode's trigger. Per §7, a burn during a genuinely busy collector window can fire the mode even with the fix working; this one did.

**Mechanism observation (a finding, not a verdict — for operator triage, not actioned here).** The restructure decouples fetch from write **within** a date, and here **date 1 fetched-and-wrote and recovered (+931 placings)** while **dates 2–7 degraded on their fetch phase** — i.e. *after* date 1's write burst, during a stretch when our process itself was not writing. Two observations bear on why the within-date decoupling did not defeat the mode in this burn, offered for the next session to weigh:
1. `run_backlog_pass` pauses only `delay` = **0.2 s between dates**, whereas the diagnosis measured the mode **resets within ~2 s of write-idle** (report headline / §2b). Date N's fetch therefore begins ≈0.2 s after date N-1's write burst — **inside the ~2 s degraded window that burst induces**. Within-date fetch/write separation does not, on its own, insert a write-idle gap between one date's writes and the next date's fetch.
2. The collector's continuous writes are an independent contention source our fetch-order cannot quiet (diagnosis §3), and the window here was demonstrably heavy.
Both candidate levers this points at — an inter-date write-idle gap ≥ the reset time, and collector-idle-window scheduling (B') — are **explicitly out of scope / parked** for this session (brief §1, §9, §11). Reported only.

**Aggregate recovery this session (intended, normal-path upserts):** recoverable deficit (≥ 2026-03-15) **36,650 → 35,718 (Δ −932)**; filled across the fixed window **3,505 → 4,436 (Δ +931)** — the whole delta is date 1's fill. Reported as intended recovery from the one clean date, **not** as evidence the mode is defeated.

## 4 — Ghost-row tripwire result (fault-B guard, `mode=ro`)

Thoroughbred race-row counts (`race_class IS NOT NULL`, non-trial, non-jump-out) across the fixed 40-date window, before vs after the burn.

| Metric | Value |
|---|---|
| Race rows across window, before | 3,013 |
| Race rows across window, after | 3,013 |
| Net delta | **0** |
| Dates with **positive** (new-row / ghost) delta | **NONE** (all 40 per-date deltas = 0) |

**The ghost tripwire did NOT fire.** Despite +931 placings written on a fully re-synced date (~135 race upserts), zero new race rows were created — every upsert matched an existing row, so the subscription path's `race_date` alignment held across this window. Measured only; **no remediation, no `race_date`/identity work** (§9).

## 5 — Self-assessment

### Scope adherence & hard limits (§9)
- **Files edited:** exactly **one** — `subscription/racing_api.py` (the §5.1 fetch/write split). Reversing the hunk reproduces the session-start sha256 (`6abc0303…`), so the restructure is the *only* change. `scripts/backfill_race_metadata.py` byte-identical at close (`cc99a2ee…`); §5.2 came back compatible, so it was not touched. No file outside the named anchor edited.
- **`race_date` / identity:** `race_date`, `upsert_race`'s conflict key, and all canonical race-identity logic — **untouched**. No schema change (no columns/tables/indexes).
- **Pacing / retry / instrumentation:** meet-level `delay`, the degraded-empty-200 retry/backoff, the empty-*races-list* retry, and the §5.1 empty-runners instrumentation — all **unchanged** (verified in-diff and by the burn logging the same signature).
- **Transaction wrap:** not taken — the upsert path self-commits per row, so a clean single transaction is unreachable without editing `storage/database.py` (out of scope). "Don't force it" honoured.
- **Operational/betting:** timer (05:30 ACST), live-capture orchestrator/collector, Betfair path — **untouched**. The collector was only *observed* read-only (`mode=ro` snapshot counts) to characterise the window; never edited.
- **Full 41k:** not attempted; the §7 burn was capped at `max_attempts=40` and walled at 7 (bounded proof).
- **`capture.db`:** all baseline/after/probe/collector verification queries opened `mode=ro` at the canonical `DB_PATH` (`data/capture.db`) via venv Python; never copied. The burn wrote placings via the normal restructured upsert path — the intended recovery.
- **Git:** no `add/commit/stash/restore/checkout/reset` — zero git write ops.
- **Escalation:** none mid-session. The surprise — the mode firing during a busy collector window despite the within-date decoupling, and the 0.2 s-inter-date-vs-~2 s-reset observation — is captured as a finding (§3), not a mid-session escalation and not a follow-up brief.
- **Output:** this single file; **no** fault-B recommendation beyond the tripwire result, **no** full-backlog-burn attempt, **no** "recovery is solved" verdict.

### Dirty-set confirmation (§4)
Session-start and session-close `git status --short` are **identical in composition**: the same **16 modified** files (incl. `subscription/racing_api.py` and the already-dirty `scripts/backfill_race_metadata.py`) and the same **9 untracked** entries — no new tracked or untracked files. The dirty *set* changed only in the *content* of `subscription/racing_api.py` (the restructure); `scripts/backfill_race_metadata.py` content is unchanged from session start (sha256 match). Both anchor files `py_compile` clean under the venv.

### Confidence
- **Restructure is correct, isolated, and behaviour-preserving on the write side:** HIGH (byte-exact reversal to session-start sha; `py_compile`/import clean; `run_backlog_pass` compatibility verified; identical return-dict/counters).
- **Restructure defeats the empty-runners mode:** **NOT DEMONSTRATED** by this burn — the mode fired on 6/7 dates during a heavy collector window; the burn walled at the same point as the pre-fix burn. Given the mode's known intermittency and this window's demonstrable busyness, a single burn cannot settle it either way (as §7/§8 anticipate).
- **Walled dates are the transient mode, not genuine-empty:** HIGH (fetch-only probe recovered all 6 to full runners, counts matching the diagnosis baselines).
- **Within-date decoupling does not, alone, break write→fetch contention across the date boundary at 0.2 s inter-date pacing:** MEDIUM (one busy-window burn; grounded in the diagnosis's ~2 s reset measurement, but not independently instrumented against collector write-rate this session).

### Routing note (§10 — operator-Claude's call, not decided here)
The mode is **not shown defeated**; the fetch/write decoupling landed cleanly and is bet-safe, but this burn provides no evidence it closes the mode, and one clean date's recovery (+931) flowed only because date 1 ran clean. The next operator-Claude triage session owns the decision — a second, longer-window burn during a quieter collector window for confidence, and/or weighing the parked levers (inter-date write-idle gap; collector-idle-window scheduling B'). This session writes no follow-up brief.
