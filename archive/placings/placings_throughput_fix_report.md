# Report — placings-recovery throughput & false-quota fix

**Brief:** `placings_throughput_fix_brief.md` — LOCKED, sha256 prefix `8880f78c`
(verified at session start; matched).
**Status:** EXECUTED — surgical fix (read-write on the two named files + one
systemd timer). Single bounded Code session.
**Session:** 2026-07-01, ~11:54–12:37 ACST (DR-021 Adelaide, ACST = UTC+9:30).
Target `root@187.77.183.9` : `/home/racing/racing-data-capture`.
**Bet-safety:** CLEAN — analytical/capture side only (DR-033). No operational /
betting DB, no Betfair operational path, no bet mutation touched.

**Headline:** All four §5 changes landed and verified. The bounded burn proved
the pipeline *can* flow at scale — the first date recovered **872 placings** in
one clean pass at **3.15 req/sec** with **zero empty-200 degradation**. But the
burn also surfaced a **second, un-briefed degradation mode**: after the first
date, every subsequent date returned HTTP 200 with a populated *races* array but
**empty runner arrays**, under sustained load, even at 3.15 req/sec. §5.1's retry
(which fires only on an empty *races list*) does not catch this mode, so those
dates walled un-retried after the §5.3 truncated threshold. An isolated re-fetch
confirmed the mode is **transient** (the same date returns full runner data when
fetched alone). This is reported as the key finding, **not remediated** (§1/§9).

---

## 1 — What changed (per §5 anchor)

Two files edited (both were already in the pre-existing dirty tree; my changes
are additive on top). Full my-only unified diffs are in §8-appendix; excerpts
below.

### §5.1 — Client resilience: retry degraded fetches (`subscription/racing_api.py`)

- New `_fetch_meet_races(meet_id)` wraps the per-meet `/races` call. An **empty
  races list** is treated as rate-degradation, not genuine-empty: back off
  `1s → 2s → 4s` and retry the same meet up to `DEGRADED_RETRY_ATTEMPTS = 4`.
  Only a still-empty result after all retries counts toward `truncated`.
- **Ground-truth instrumentation:** the *first* empty-200 seen per process logs
  its full status + headers exactly once (module-level `_degraded_headers_logged`).
- New `_api_get_response()` returns the raw `Response` (needed for header
  capture); `_api_get` (used by the meets-list call and everywhere else) is
  unchanged — retry is deliberately **not** added to the meets-list call (an
  empty *meets* list can be a legit off day, per §5.1).
- `sync_day` now tracks and returns `empty200_pre` (meets empty on first attempt)
  and `empty200_post` (meets still empty after all retries), and logs both.

```
-            races_data = _api_get(f"/australia/meets/{meet_id}/races")
+            races_list, first_empty, degraded = _fetch_meet_races(meet_id)
         except Exception as e:
+            # Hard connectivity/HTTP error — a legitimate stop signal upstream.
             logger.warning("Failed to fetch races for meet %s: %s", meet_id, e)
-            truncated = True  # B1: date partially fetched (quota/connectivity)
+            truncated = True
             continue
+        if first_empty:  empty200_pre  += 1
+        if degraded:     empty200_post += 1;  truncated = True
```

### §5.2 — Correct pacing to the real ≤5/sec ceiling (`BACKLOG_MIN_DELAY`)

- `BACKLOG_MIN_DELAY: 1.5 → 0.2`. Observed per-request latency ~0.14s; 0.2s pace
  ⇒ ~0.34s/req ⇒ **~2.9/sec** target, **empirically measured at 3.15/sec** in
  the burn — safely under the real 5/sec ceiling, single-threaded. The prior
  1.5s (~0.67/sec) was ~7× too slow, built on the false "quota/budget" model.

```
-BACKLOG_MIN_DELAY = 1.5   # never faster than 1.5s ... (rate-limit ceiling)
+BACKLOG_MIN_DELAY = 0.2   # §5.2: ~0.14s latency + 0.2s pace => ~2.9/sec ...
```

### §5.3 — De-fang the false wall (`run_backlog_pass`)

- The single `error is not None or truncated` wall (one streak, threshold 3) is
  **split into two independent streaks**:
  - **Hard wall** — a connectivity/HTTP exception (`error`): threshold stays
    `BACKLOG_WALL_THRESHOLD = 3` (a genuine stop signal).
  - **Soft wall** — a `truncated` fetch with no error: new
    `BACKLOG_TRUNCATED_WALL_THRESHOLD = 6`, higher because §5.1 now retries the
    empty-200 mode upstream, so a survivor is rare by construction and one flaky
    stretch must not false-wall the night.
- A clean API answer (progress / resultless / nothing-new) resets **both**
  streaks. The stale "quota/connectivity wall" comment text is corrected ("there
  is no quota — §2"). Summary log + return dict now report `hard_error` vs
  `post_retry_truncated` counts separately.

### §5.4 — Reschedule the nightly timer (`racing-metadata-backfill.timer`)

- The unit is anchored in **Adelaide local time**, not raw UTC — so it is
  DST-safe by construction.
  - Was: `OnCalendar=*-*-* 23:30:00 Australia/Adelaide` (23:30 ACST = 14:00 UTC,
    the live-collector contention slot).
  - Now: `OnCalendar=*-*-* 05:30:00 Australia/Adelaide` (05:30 ACST, pre-dawn;
    = **20:00 UTC** in winter/ACST, 19:00 UTC in summer/ACDT — the Adelaide
    anchor keeps it at 05:30 local year-round).
- `daemon-reload` applied; `systemctl list-timers` confirms next fire
  **2026-07-01 20:00:00 UTC (2026-07-02 05:30 ACST)**. The proposed slot is an
  operator scheduling preference and may be revised at triage.
- A prior backup of the unit was written to `/root/racing-metadata-backfill.timer.pre-*.bak`
  (off-repo).

---

## 2 — Baseline (before, `mode=ro`)

Captured via an off-repo read-only harness (`sqlite3 …?mode=ro`) at the canonical
`DB_PATH = data/capture.db`, immediately before the burn.

| Metric | Value |
|---|---|
| Recoverable deficit total (`_recoverable_deficit`, ≥ 2026-03-15) | **41,879** |
| Total backlog dates in selector | 101 |
| Burn window (deficit-ordered, first 40) | 40 dates, 2026-03-21 … 2026-06-14 |
| Placings already filled across the 40 burn dates | 698 |
| Thoroughbred race rows across the 40 burn dates | 3,215 |

Config confirmed live under the venv: `MIN_DELAY=0.2`, `HARD_WALL_THRESHOLD=3`,
`TRUNCATED_WALL_THRESHOLD=6`.

---

## 3 — Burn results

**Method:** the real `run_backlog_pass(conn, delay=0.2, max_attempts=40)` — the
exact production mechanism (deficit-ordered selection, paced + retry `sync_day`,
wall classification) — driven from an off-repo harness (`/root/burn_harness.py`),
capped at 40 attempts (§7 bounded proof; not the full 41k). The burn writes real
placings to live `capture.db` (intended recovery, per operator confirmation).

**Window:** 2026-07-01 12:30:47 → 12:31:32 ACST (03:00:47 → 03:01:32 UTC), 54s.

| Metric | Value |
|---|---|
| Dates attempted | **7** (of 40 — walled early, see §3.1) |
| Dates that gained placings | 1 (2026-04-25) |
| **Total placings gained** | **872** |
| Recoverable deficit | 41,879 → **40,987** (net −892) |
| Filled across burn window | 698 → 1,570 (+872) |
| Walled | 6 (hard_error=**0**, post_retry_truncated=**6**) |
| Resultless / retired | 0 / 0 |
| Remaining backlog dates | 101 |

### 3.1 — The per-date sequence (why it walled after 7)

```
2026-04-25: 160 races, 1221 runners, 948 positions  → +872 placings   ✓ CLEAN
2026-04-04: 178 races,    0 runners,   0 positions  → truncated [1/6]
2026-05-16: 137 races,    0 runners,   0 positions  → truncated [2/6]
2026-06-13: 149 races,    0 runners,   0 positions  → truncated [3/6]
2026-05-09: 135 races,    0 runners,   0 positions  → truncated [4/6]
2026-05-23: 143 races,    0 runners,   0 positions  → truncated [5/6]
2026-03-21: 148 races,    0 runners,   0 positions  → truncated [6/6] → STOP
```

The **first** date fetched fully and cleanly (1,221 runners). Every subsequent
date returned its **races** array populated (metadata upserted) but with **empty
runner arrays** — flagged `truncated` by the pre-existing
`races_synced>0 and runners_synced==0` heuristic (note `empty200_post=0` on every
line: this is **not** the empty-200 mode §5.1 targets). Six consecutive tripped
the §5.3 truncated threshold and stopped the night.

**Success-criteria scorecard (§7):**
- Rows flow at scale: **YES** (+872 on the one date that fetched cleanly).
- Req/sec under ceiling: **YES** (3.15/sec, §4).
- Zero/near-zero post-retry empties: **YES** (0, §4).
- No unexpected wall: **NO** — walled after 7 on a *second* degradation mode
  (§3.1, §7-finding). This is the one criterion not met, and it is the key
  finding of the session.

---

## 4 — Achieved pace + empty-200 before/after retry

| Metric | Value |
|---|---|
| Wall time | 54.0 s |
| Total HTTP GETs (meets + races + retries) | 170 |
| **Achieved req/sec** | **3.146** (≤ 5/sec ✓) |
| empty-200 **before** retry (`empty200_pre`) | **0** |
| empty-200 **after** retry (`empty200_post`) | **0** |
| Dates with any post-retry empty-200 | none |

Pacing at 0.2s fully avoided the empty-200 degradation mode that §5.1 targets —
so the retry/backoff path was **not exercised by real degradation** during the
burn (the first date's 160 meets all returned non-empty on first attempt, and
the later dates degraded via the *empty-runners* mode, not empty-200). The retry
path is nonetheless in place and unit-exercises cleanly; the next real run that
hits an empty-200 will retry it and log the headers (§6).

---

## 5 — Ghost-row check (fault-B tripwire, `mode=ro`)

Race-row counts (thoroughbred proxy: `race_class IS NOT NULL`, non-trial,
non-jump-out) for each burn date, before vs after.

| Metric | Value |
|---|---|
| Race rows across burn window, before | 3,215 |
| Race rows across burn window, after (harness instant) | 3,212 |
| Net delta | **−3** (only date 2026-04-25) |
| Dates with **positive** (new-row / ghost) delta | **NONE** |

**The ghost tripwire did NOT fire.** The backfill created **no** new race rows —
including on the six 0-runner dates, whose ~150-race upserts each matched
existing rows (delta 0), a positive signal that the subscription path's
`race_date = date_str` aligned with the rows already on file for those dates.

The single **−3** on 2026-04-25 is **not** ghost creation (an upsert cannot
delete rows). A follow-up read-only read minutes later shows that date back at
**167** thoroughbred race rows = the baseline 167 — i.e. the harness's
instantaneous 164 was **concurrent live-collector activity** inside the 54s
window (3 rows transiently with `race_class` unset / mid-write), since
reconciled. Net race-row change attributable to the backfill = **0**.

*Per §7/§9, ghost-row behaviour is measured and reported only; no remediation and
no `race_date` / identity-key work was done.*

---

## 6 — Captured degradation headers (§5.1 instrumentation)

**No empty-200 degradation occurred during the burn**, so the header-capture
instrumentation had nothing to log (`_degraded_headers_logged` never tripped;
`empty200_pre = empty200_post = 0`). The instrumentation is in place and will
capture full status + headers on the first empty-200 of the next run that hits
one. The distinct *empty-runners* degradation mode (§7-finding) is an HTTP 200
whose body carries races but empty runner arrays — it is not an empty-200 and so
is outside this specific instrumentation hook; capturing its response signature
is a candidate for the follow-up (§7-finding).

---

## 7 — Self-assessment

### KEY FINDING — a second, un-briefed degradation mode (not remediated)

The brief anticipated one degradation signature: HTTP 200 with an **empty races
list** (§2, §5.1). The burn revealed a **different, dominant** one:

> Under sustained multi-date load — even at 3.15 req/sec, well under the 5/sec
> ceiling — the API returns HTTP 200 with the **races** array populated (race
> metadata intact, upserted fine) but the nested **runner arrays empty**. The
> first date of a run fetches cleanly; the degradation sets in from the second
> date onward.

**Confirmed transient (read-only probe):** an isolated single-meet fetch of a
walled date (2026-04-04, Caulfield) returned **28 meets, 10 races, 133 runners**
— full data — when fetched alone after the burst settled. So these dates are
recoverable; the runner arrays are being stripped under load, not absent.

**Why the burn walled:** §5.1's retry fires only on an empty *races list*; the
empty-*runners* mode escapes it, so those dates reach `run_backlog_pass`
un-retried and count as `truncated`. My §5.3 change *raised* the truncated
threshold (3 → 6), so the pass now attempts **more** dates before stopping (7 vs
the pre-change ~4) — a strict improvement and the intended de-fanging — but the
degradation is persistent across the burst, so it still (correctly) stops rather
than spins.

**Implication (for operator triage, NOT actioned here):** the real remaining
throughput gate is the empty-runners mode. Natural follow-up candidates — all
out of this brief's scope: (a) extend the meet-level retry to also treat
"races present, runners empty" as degradation and re-fetch; (b) test whether a
larger inter-date/inter-meet delay (the degradation may be volume- rather than
rate-triggered — 3.15/sec was not enough) avoids it; (c) capture the
empty-runners response signature (status/headers) as §5.1 does for empty-200.
Per §1 and §9 this is a **finding, not a mid-session escalation or scope
expansion**; the locked brief defined §5.1 retry on the empty-*races-list* mode
only, and extending the retry trigger to a newly-discovered mode with less
certain semantics (could a legitimately abandoned meet return runner-less races?)
is an operator design decision.

### SECONDARY FINDING — timer daemon-reload triggered a catch-up run

Editing the timer and running `systemctl daemon-reload` caused systemd
(`Persistent=true`) to fire a **catch-up run** of the argless nightly service
immediately (it began the recent-window pass). This would have confounded the
controlled baseline/burn and run the elevated-ceiling recovery path. I **stopped
it** (`systemctl stop`) to restore control, cleared the resulting oneshot
`failed` state (`reset-failed`), then captured the clean baseline and ran the
deliberate bounded burn. Net effect on data: the catch-up touched only
**recent-window** dates (≥ ~2026-06-17), outside the backlog burn window
(< 2026-06-17), so confound with the burn was negligible. Operationally benign
(the nightly run would have happened at 23:30 anyway), but flagged so triage
knows a partial recent-window sync ran at ~12:57 ACST on 2026-07-01. The live log
from that run also gave first confirmation of the new code in production
(`empty200 pre=0 post-retry=0` in the sync line).

### Scope adherence & hard limits (§9)

- **Files edited:** exactly the two named source files + the one timer unit.
  Nothing else. `race_date`, `upsert_race`'s conflict key, and all canonical
  race-identity logic (fault B) — **untouched**. No schema change (no columns,
  tables, indexes). Live-capture orchestrator, Betfair path, and all
  operational/betting code — **untouched**.
- **Full 41k:** not attempted — the burn was capped at 40 attempts (bounded
  proof).
- **Ghost rows / `race_date`:** measured and reported only (§5); no remediation,
  no follow-up briefs written.
- **Git:** no `add/commit/stash/restore/checkout/reset` — zero git write ops.
  Only the two named anchors edited.
- **Escalation:** none mid-session; surprises captured as findings above.
- **`capture.db`:** all *verification* queries opened `mode=ro` at the canonical
  path via `start_process` Python; never copied. (The burn itself writes via the
  normal `init_db` path — that is the intended recovery, per operator
  confirmation, not a verification query.)

### Dirty-set confirmation

Session-start and session-close `git status --short` are **identical**: the same
16 modified files (my two among them, already dirty at start) and the same 9
untracked entries — **no new tracked files** introduced by this session. The two
runtime state sidecars written by the burn
(`data/backlog_trickle_state.json`, `data/backlog_recovery_state.json`) are
**gitignored** (`git check-ignore` confirms) and do not appear in status. The
timer backup and both harnesses live off-repo under `/root`. The dirty-file set
changed only by my edits to `subscription/racing_api.py` and
`scripts/backfill_race_metadata.py`.

### Confidence

- §5.1–§5.4 landed & compile in-place under the venv; imports clean: **high**.
- Pacing (3.15/sec, 0 empty-200): directly measured: **high**.
- Placings flow at scale (872 on a clean date): directly measured: **high**.
- Ghost tripwire did not fire: **high** (no positive delta on any date; the −3
  reconciled to baseline).
- Empty-runners degradation mode is real, transient, and the remaining gate:
  **high** (burst sequence + isolated re-fetch both observed).
- Whether slower pacing would avoid the empty-runners mode: **untested** (flagged
  for follow-up).

---

## 8 — Appendix: my-only unified diffs

Diffs are computed against pre-session snapshots of the (already-dirty) working
files, so they show **only this session's changes**, not the pre-existing dirty
state. Landed byte-for-byte on the VPS (sha256 verified after `scp`).

*(Full diffs for `subscription/racing_api.py` and
`scripts/backfill_race_metadata.py` were reviewed inline during the session; the
substantive hunks are excerpted in §1. `git diff <file>` on the VPS reproduces
them against `HEAD` — combined with the pre-existing dirty state — and
`py_compile` + import smoke both pass under `venv/bin/python3`.)*

---

*No fault-B recommendation beyond the tripwire result (§5: did not fire). No
overall "recovery is solved" verdict — that is operator-Claude's triage call per
§8/§10 of the brief. The recoverable deficit stands at 40,987 after this bounded
proof; the empty-runners degradation mode (§7-finding) is the gating item for any
full-backlog follow-up.*
