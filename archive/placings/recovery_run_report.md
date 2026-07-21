# Placings recovery run — Code report

**Executed:** 2026-06-29, ~18:30 → 18:40 ACST (single bounded Code session, per
`recovery_run_brief.md`, LOCKED S201).
**Host / mode:** racing-data-capture VPS (`root@187.77.183.9`), live. READ-WRITE on
**one** named anchor file (`scripts/backfill_race_metadata.py`, already `M` from S198).
`capture.db` `mode=ro` for verification reads; the proving pass writes through the
normal `sync_day()` path. All edits + the proving pass run as user **`racing`** (the
service user) so the new runtime artifacts are owned correctly. Capture-side analytical
only — no v3, settlement, money path, or Betfair pricing (DR-033).
**Outcome:** Wired + proven clean. Scope B (monitoring) and Scope A (budget split +
auto-revert) both verify. The recovery shape is live on the nightly timer. The full
clear builds over nights (F-2) — **not** completed in-session, as the brief anticipates.
The one honest surprise: the recoverable deficit (**41,340**) is far larger than the
fix report's per-date samples implied, so the realistic clear is **weeks, not the
brief's ~1–2** (Finding R-1).

---

## 1. What changed (one file, no schema, no S198 rework)

All edits are inside `scripts/backfill_race_metadata.py` — the file S198 already left
`M`. The proven S198 logic (Part A guard, B1 classifier, B2 ordering, per-meet pacing,
`sync_day`) is **byte-untouched**; verified intact post-edit (§5). The existing
`send_alert` SMTP path is **reused by import**, never duplicated; `liveness_check.py`
was **not** edited.

### Scope A — pacing / budget split (the recovery shape)

- **Raised per-night ceiling.** New constant `BACKLOG_RECOVERY_MAX_ATTEMPTS = 120`
  (vs base `BACKLOG_MAX_ATTEMPTS = 20`, unchanged). 120 > the 99 total backlog dates,
  so the ceiling **never artificially caps** the walk — `BACKLOG_WALL_THRESHOLD = 3`
  consecutive empties (the F-2 safety) is the real per-night stop, so a high ceiling
  can never hammer an exhausted quota.
- **`run_backlog_pass` parametrised.** Signature gains `max_attempts: int =
  BACKLOG_MAX_ATTEMPTS`; the two cap references inside it now use `max_attempts`. This
  is the *only* change to the proven function — purely the ceiling lever, classification
  untouched.
- **Automatic revert** (no manual flag, no code edit to trigger). New
  `run_recovery_pass()` orchestrator computes the recoverable deficit at the start of
  each night and picks the ceiling: deficit `>` threshold → recovery (120); else →
  steady (20). See §4.

### Scope B — low-touch monitoring (reuse, no new infra)

- **Deficit-burndown log** — `logs/backlog_recovery.log`, one glanceable line per
  nightly run (Adelaide local, DR-021). Append-only, **pulled not pushed**.
- **Stall alert (pushed once)** — fires the existing `send_alert` when
  `BACKLOG_STALL_NIGHTS = 3` consecutive recovery runs net `<=
  BACKLOG_STALL_EPSILON = 5` placings while deficit remains. Latched (fires once,
  re-arms when progress resumes).
- **Completion notify (pushed once)** — fires `send_alert` on the active→clear
  transition (the §4 revert). Latched.
- **Error alert (pushed)** — if the backlog pass raises, `run_recovery_pass` catches
  it, fires `send_alert`, and writes an `ERROR=…` burndown line (never crashes the
  capture pass).
- **`_notify()`** wraps `from scripts.liveness_check import send_alert` (lazy, guarded
  — a monitoring failure can never break the capture-side pass).

### New constants (all additive)

| Constant | Value | Role |
|---|---|---|
| `BACKLOG_RECOVERY_FLOOR` | `"2026-03-15"` | recovery-target start; pre-floor early-March residue excluded (F-3) |
| `BACKLOG_RECOVERY_MAX_ATTEMPTS` | `120` | elevated per-night ceiling (recovery mode) |
| `BACKLOG_RECOVERY_CLEAR_THRESHOLD` | `100` | recoverable deficit ≤ this ⇒ clear ⇒ revert + notify |
| `BACKLOG_STALL_NIGHTS` | `3` | consecutive ~zero nights ⇒ stall alert |
| `BACKLOG_STALL_EPSILON` | `5` | net placings ≤ this counts as ~zero |
| `BACKLOG_RECOVERY_STATE_PATH` | `data/backlog_recovery_state.json` | nights history + alert latches |
| `BACKLOG_RECOVERY_LOG` | `logs/backlog_recovery.log` | burndown log |

### Wiring

`main()` argless nightly path: `run_backlog_pass(...)` → `run_recovery_pass(...)` (one
line). Manual `--date` / `--days` recovery **bypasses** it entirely (unchanged).

### New runtime artifacts (gitignored, owned `racing`)

`logs/backlog_recovery.log`, `data/backlog_recovery_state.json` — created by the proving
pass, both `racing:racing` so the nightly service (User=`racing`) can write them. Neither
dirties the tree (`logs/`, `data/` are gitignored — same as the existing strike sidecar).

---

## 2. Deficit baseline (before)

Queried live from `capture.db` (`mode=ro`), mirroring the exact `get_backlog_dates`
predicate (`race_class IS NOT NULL`, non-trial/non-jump-out, `finish_position IS NULL`,
`scratched = 0`, exhausted-dates excluded). Backlog window `[2026-03-01, 2026-06-15)`;
recent window `[2026-06-15, 2026-06-29]`.

| Scope | Deficit | Dates |
|---|---|---|
| **Full backlog (≥ 2026-03-01)** | **42,103** | 99 |
| **Recoverable (≥ 2026-03-15)** — recovery target | **41,340** | 90 |
| Early residue (2026-03-01 … 03-14) — excluded (F-3) | 763 | 9 |
| Exhausted/retired | 0 | 0 |

**Top deficit dates** (B2 deficit-first ⇒ attempted first): 04-25 (1407), 04-04 (1391),
05-16 (1352), 06-13 (1319), 05-09 (1309), 05-23 (1294), 03-21 (1279), 04-18 (1264),
05-30 (1255), 04-11 (1230) … **residue tail at the back**: 03-04 (66), 03-05 (66),
03-02 (46), 03-01 (39), 03-06 (1).

> The fix report's §3 figures (e.g. 06-06 +1123) are a sanity anchor only; this is the
> live deficit. 06-06 is already cleared and absent from the list, as expected.

---

## 3. Verify results (§9)

### 3.1 Live proving pass — one real argless-equivalent run (18:31–18:35 ACST)

Ran the exact nightly path (`venv/bin/python3 scripts/backfill_race_metadata.py`, no
args) as `racing`. Today's Racing-API budget was **already exhausted** (the S198 fix
session hit HTTP 429 at ~15:28 ACST; quota resets 00:00 UTC), so fills are ~0 — F-2,
expected. What this proves is the **live integration**:

| §9 check | Observed | Verdict |
|---|---|---|
| Recent window served **first** | All 15 recent dates (06-29→06-15) processed before any backlog; "Backfill complete: … across 15 dates", 134 runners landed recent-side | ✅ never-starve held |
| Recovery engaged | `RECOVERY: mode=recovery recoverable_deficit=41340 ceiling=120 (clear_threshold=100)` | ✅ |
| Backlog deficit-first (B2) | attempted 04-25 (1407) → 04-04 → 05-16 — richest first | ✅ |
| B1 no false strike | 3 × `truncated → wall (no strike)`; `resultless=0 retired=[]`; sidecar entries for 04-25/04-04/05-16 still absent | ✅ |
| Wall is the stop | 3 consecutive walls → stopped (well before the 120 ceiling) | ✅ safety holds |
| Burndown line landed | see §3.2 | ✅ |
| Part A guard | `storage/database.py` untouched; 0 fills ⇒ no overwrite exercised; rides on the proven S198 guard unchanged | ✅ (inherited) |
| Deficit moved | 41,340 → 41,340 (0 fills, exhausted budget) | ⚠ F-2 / R-1 |

### 3.2 First burndown line + recovery state (live artifacts)

```
2026-06-29 18:35 ACST | mode=recovery ceiling=120 | deficit 41340 -> 41340 (net +0) | placings=0 | attempted=3 walled=3 resultless=0 retired=0 | avg_burn=0/night | nights_to_clear=n/a
```
`data/backlog_recovery_state.json`: one night entry (mode recovery, before/after 41340,
net 0), `stall_alerted=false`. Both files `racing:racing`. No false alarm (n/a, not
"stalled" — correct on a single walled night).

### 3.3 Monitoring + ceiling/revert — deterministic proof (no API, temp state/log)

Monkeypatched the API/DB callees and redirected state+log to `/tmp` (real state kept
clean). 12/12 checks **OK**:

| Scenario | Assertion | Verdict |
|---|---|---|
| A — high deficit | ceiling = 120; no notifies on healthy progress; burndown `mode=recovery ceiling=120`, `deficit 41340 -> 39000 (net +2340)` | ✅ |
| B — clear crossing | completion notify fires **exactly once**; ceiling 120 while clearing → **reverts to 20** once deficit ≤ 100; clear line shows `nights_to_clear=0 (clear)` | ✅ |
| C — stall | stall alert fires **exactly once** after 3 consecutive ≤ε nights; no completion notify while deficit remains | ✅ |
| D — error | error alert fires when the pass raises; burndown carries `ERROR=boom` | ✅ |

### 3.4 Budget-skew mechanism — deterministic proof

With the budget not walled (faked progress, 50 candidate dates):

| Ceiling | Dates attempted | Verdict |
|---|---|---|
| recovery (120) | **50** (all candidates; capped only by dates/wall, never the ceiling) | ✅ walks past 20 |
| base (20) | **20** | ✅ base still caps |

⇒ On a fresh-budget night the raised ceiling lets the backlog consume the bulk of the
leftover budget (the ~80/20 skew in practice); the live pass (§3.1) couldn't demonstrate
this empirically only because today's budget was exhausted.

---

## 4. Revert mechanism (chosen) + why

**Automatic deficit-threshold check** — chosen over a manual `BACKLOG_RECOVERY_MODE`
flag because the brief prefers "must not require a code edit to trigger."

`run_recovery_pass()` calls `_recoverable_deficit(conn)` — in-scope unfilled
thoroughbred runners with `race_date ≥ BACKLOG_RECOVERY_FLOOR (2026-03-15)`, mirroring
`get_backlog_dates` **including the exhausted-date exclusion**, so a genuinely-resultless
recoverable date that retires (freeze off, after `BACKLOG_EXHAUST_AFTER`) drops out and
the deficit can actually reach ~0.

- deficit `> 100` → **recovery**: ceiling 120.
- deficit `≤ 100` → **steady**: ceiling 20, and on the *first* such night the completion
  notify fires (latched, once).

**Why threshold = 100.** The recovery floor already excludes the genuine early-March
residue. 100 is below a single typical recoverable date's worth (live dates run
100–1,400), so once the recoverable deficit falls under 100 the few stragglers fit
comfortably under the base 20-date ceiling — recovery mode is no longer needed.
Conservative (won't revert while a real tail remains); the next session may tune it.

**Why ceiling = 120.** Greater than the 99 total backlog dates, so it never artificially
caps the walk; the F-2 wall-threshold remains the real per-night stop.

Both proven by logic/unit (§3.3, §3.4) — the real clear takes weeks, not provable
in-session.

---

## 5. Dirty-tree confirmation

- **No git operations of any kind** (no add/commit/stash/restore/checkout/reset).
  HEAD `5f71488` unchanged.
- `git status --short` at close = **identical** to baseline: **15 `M` + 8 `??`**. The
  one target (`scripts/backfill_race_metadata.py`) was already `M` from S198; no new
  tracked entry. The other 14 `M` + 8 `??` are byte-identical to baseline.
- Edits applied via an auditable patcher: 4 exact-match replacements (each asserting a
  single occurrence — signature, cap-check, cap-log-arg, `main` wiring) + 2 additive
  insertions (constants, helpers). Source validated in-memory **before** the live file
  was written; `py_compile` clean.
- **S198 logic verified intact post-edit:** B1's four branches present
  (`gained > 0` / `error or truncated` wall / `races_synced>0 and positions_seen==0`
  resultless / complete-noop); B2 `ORDER BY deficit DESC, ra.race_date ASC`; untouchable
  constants unchanged (`BACKLOG_FLOOR`, `BACKLOG_WALL_THRESHOLD`, `BACKLOG_MIN_DELAY=1.5`,
  `BACKLOG_EXHAUST_AFTER`, `BACKLOG_MAX_ATTEMPTS=20`, `BACKLOG_FREEZE_RETIRE=False`).
- No files written to the VPS source tree besides the one edited anchor; diagnostics ran
  via SSH stdin. Runtime artifacts (`logs/backlog_recovery.log`,
  `data/backlog_recovery_state.json`) are gitignored.

---

## 6. Findings (surprises → findings, not escalations)

- **R-1 (load-bearing) — the recoverable deficit is far larger than the fix report
  implied; the clear is weeks, not ~1–2.** Live recoverable deficit = **41,340** across
  90 dates (top dates ~1,300–1,400 each). The S198 fix session showed a fresh-budget
  window lands ~**1,123** placings (one rich date) before the quota walls. If a nightly
  run lands on the order of one-to-a-few rich dates before walling, the clear is roughly
  **4–6 weeks**, not the brief's ~1–2. The mechanism is correct and safe regardless; the
  burndown's `nights_to_clear` will report the true rate as real-budget nights accrue.
  No action taken (changing pacing/quota is out of scope) — flagged for the operator.
- **R-2 — the nightly timer fires at 23:30 ACST = 14:00 UTC, but the Racing-API quota
  appears to reset at 00:00 UTC.** So the nightly backlog pass runs ~14h into the UTC
  quota day, after recent-window + daytime consumption — it may receive limited budget
  per night, throttling the burn (compounding R-1). The S198 fix session's own
  fresh-budget fills happened at ~05:53 UTC. Out of scope to change the timer/threshold;
  flagged. If the budget genuinely never reaches the backlog, the **stall alert is the
  correct signal** (it will fire after 3 such nights).
- **R-3 — budget exhausted today ⇒ the live proving pass landed 0 fills.** Expected
  (F-2): the S198 verification spent today's quota (429 at ~15:28 ACST). The deterministic
  proofs (§3.3, §3.4) cover what the exhausted-budget live pass could not (ceiling skew,
  revert, completion/stall/error notifications). The first real burn begins with the
  fresh-budget nightly runs.
- **R-4 (disclosure) — the proving pass is recovery "night 1" in the burndown
  (net 0).** Tonight's 23:30 timer is night 2. The stall counter therefore starts now;
  if the next runs also wall while deficit remains, the stall alert will (correctly)
  fire — that is the monitoring working, not a false positive. "Nights" in the state =
  recovery runs (a same-day extra run counts); semantics noted for the operator.

---

## 7. Self-assessment

- **Proven:** Scope B monitoring (burndown line shape + Adelaide timestamp; stall /
  completion / error alerts each fire once via the reused `send_alert`); Scope A ceiling
  selection + **automatic revert** (recovery 120 ↔ steady 20 at the 100 threshold);
  budget-skew (raised ceiling walks past 20 when unwalled); live integration
  (recent-first held, recovery engaged, B2 deficit-first, B1 no-false-strike, wall is the
  stop, real artifacts owned `racing`).
- **Rides on the proven S198 fix unchanged:** guard / B1 / B2 / pacing all byte-intact;
  the recovery only added the ceiling lever + its revert + monitoring.
- **Not closed in-session (honest):** the actual backlog clear (F-2 — builds over
  nights); the empirical per-night burn rate and a firm nights-to-clear (today's budget
  was exhausted, so net 0 — R-3). The realistic estimate at the only available burn data
  point (~1,123/rich-date-night) is **~4–6 weeks** (R-1), materially longer than the
  brief's ~1–2 — to be confirmed by the burndown.
- **Scope held:** one named anchor file; no schema/migration; no S198 rework; reused the
  existing SMTP path (no new infra/creds); no git ops; capture-side analytical only
  (DR-033); ACST timestamps (DR-021); single bounded session; surprises booked as
  findings, no mid-session escalation. No follow-on brief written.
- **Stop-condition not triggered:** monitoring and the budget-split both verified clean,
  so the nightly timer is left running a **proven** recovery shape (per §8's gate).

---

## 8. Hand-off (§12)

The recovery now runs itself via `racing-metadata-backfill.timer` (enabled + active; next
fire Mon 2026-06-29 14:00 UTC / 23:30 ACST). Next operator-Claude (Chat) session:
confirm the budget split + monitoring wired clean (this report), glance
`logs/backlog_recovery.log` over the recovery, and act only on a **stall/error alert**.
Watch **R-1/R-2**: the true burn rate and nights-to-clear emerge in the burndown; the
clear is likely weeks. On backlog-clear the completion notify fires once and the ceiling
auto-reverts to steady (20) — confirm the revert and close the milestone. The genuine
pre-2026-03-15 early-March residue (763) is intentionally excluded and is **not** part of
this milestone.
