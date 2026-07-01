# Placings recovery run — Code brief

**Status:** LOCKED — 2026-06-29, Session 201, Adelaide local.
Operator signed off this session (80/20 split + low-touch monitoring
calls confirmed as drafted). Cleared for hand-off to Code. No edits
to scope after this point without a re-lock.
**Drafted:** 2026-06-29 (Session 201), Adelaide local.
**Commissions:** one bounded Claude Code session against the live
racing-data-capture VPS to provision and prove the systematic,
paced, deficit-ordered recovery of the recoverable placings backlog
— the operator's "start the data recovery" milestone.
**Serves:** the §8 hand-off of `placings_landing_fix_report.md` (the
verified RC-1/RC-2 fix). DR-033 (placings analytical; settlement
Betfair-only) — capture-side analytical only, no money/settlement
path.

---

## §1 — What this brief is and is not

**Is:** the provisioning + proving step that turns the now-fixed
nightly backlog walk into a monitored, budget-split recovery that
clears the recoverable placings backlog over ~1–2 weeks of nightly
runs. Code (a) sets the pacing/budget split so the backlog gets the
bulk of each night's Racing-API budget without starving the recent
window, (b) adds low-touch monitoring (a glanceable nightly
deficit-burndown log, a stall/error alert, a completion notify), and
(c) proves the mechanism on one controlled pass and reports. Single
bounded Code session.

**Is not:** a schema change, a refactor of the sync path, a rewrite
of the fix, or a re-litigation of the RC-1/RC-2 fix (that landed and
verified clean, S198 — `placings_landing_fix_report.md`). It is also
**not** a babysit of the full multi-night recovery: Code provisions
and proves the mechanism in one session; the recovery itself then
proceeds nightly via the existing systemd timer. The full clear
building over nights is expected, not a continuation. Surprises
become findings in the report, not mid-session escalations.

**Bet-safety:** analytical / capture-side only. Touches no v3 code,
no settlement, no money path, no Betfair operational pricing. The
data being recovered is backward-looking finishing positions used
for model calibration, never live bet placement (DR-033). The recent
window this brief protects is the same analytical capture stream —
both sides of the budget split are analytical.

---

## §2 — Why this work exists

The S198 surgical fix (`placings_landing_fix_report.md`) repaired the
two bugs that were stopping recoverable finishing positions from
landing in `capture.db`: RC-1 (fetch starvation + false strikes) and
RC-2 (cross-source overwrite). It proved the mechanism on two dates
(03-15 +83, 06-06 +1123 ≈ 1,206 placings landed), lifted the freeze
(`BACKLOG_FREEZE_RETIRE = False`), and explicitly deferred the
**systematic replay of the whole recoverable backlog** to the next
session (its §8 / §12 hand-off). This brief is that step.

The fix report's F-2 is the load-bearing constraint: even with the
fix correct, a single night's fetch does not complete the whole
backlog, because the Racing-API request budget exhausts within a day.
The recovery is therefore **paced over nights**, not a one-shot bulk
run — and the fix's B1 classifier guarantees this is safe: a
truncated / budget-exhausted fetch is classified transient (no
strike), so no recoverable date is ever wrongly retired while
completeness builds.

---

## §3 — Pre-reads

Required, in order:
1. `/Users/tim/Desktop/Projects/bethub-rebuild/placings_landing_fix_report.md`
   — the verified fix + the recovery mechanism (§4 B2 deficit
   ordering, §5 F-1 per-meet pacing, F-2 budget caveat, §8 hand-off).
   **Primary anchor.**
2. This brief.

Reference-only (read on demand):
- `/Users/tim/Desktop/Projects/bethub-rebuild/placings_landing_fix_brief.md`
  — the locked fix contract the report executed against.
- `/Users/tim/Desktop/Projects/bethub-rebuild/placings_landing_diagnosis_report.md`
  — RC-1/RC-2 root cause and the strike/freeze model.

## §4 — System access

- **Host:** racing-data-capture VPS (`root@187.77.183.9`), live.
- **Mode:** READ-WRITE, restricted to the named anchors in §6–§7.
  Everything else read-only.
- **Database:** `capture.db` at
  `/home/racing/racing-data-capture/data/capture.db`. Queried live
  for verification (§8), `mode=ro` for reads; the sync code writes
  through its normal connection. **Never copy the DB file.**
- **Repo / working tree:** `/home/racing/racing-data-capture`, HEAD
  `5f71488`. **Working tree is DIRTY** (the S198 fix left three files
  `M`) — see §9 hard limits. Edit only the named anchors; **no git
  operations of any kind.**
- **Scheduler (grounded this session):** the nightly run is
  `racing-metadata-backfill.service` (oneshot), fired by
  `racing-metadata-backfill.timer` at **23:30 Australia/Adelaide
  daily** (`Persistent=true`). ExecStart runs
  `scripts/backfill_race_metadata.py` **with no args** — the argless
  nightly path.
- **Timestamps:** Adelaide local (ACST/ACDT) for every time-of-day
  reference in the report (DR-021).

---

## §5 — Grounded current behaviour (where the recovery lives)

Confirmed against the live tree this session (S201, read-only).
Line numbers are anchors, not contracts — Code re-confirms by
function/constant name before editing.

**`scripts/backfill_race_metadata.py`:**

- **Constants (≈L104–110).** `BACKLOG_FLOOR = "2026-03-01"` (gap
  floor — never chase pre-gap history); `BACKLOG_WALL_THRESHOLD = 3`
  (consecutive empty/error dates → quota/connectivity wall → stop the
  night); `BACKLOG_EXHAUST_AFTER = 5` (clean-but-no-fill attempts →
  retire); `BACKLOG_MAX_ATTEMPTS = 20` (**per-night attempt ceiling —
  the budget proxy**); `BACKLOG_FREEZE_RETIRE = False` (freeze lifted,
  S198); `BACKLOG_MIN_DELAY = 1.5` (per-call pacing floor).
- **`main()` (≈L339–415), argless nightly path.** Order is
  **recent-first, then backlog**: it processes the recent window
  (`get_unsynced_dates`) first — unbounded over those dates, at
  `--delay` (default 1.0) — then, **only on the argless path**, calls
  `run_backlog_pass(conn, max(args.delay, BACKLOG_MIN_DELAY))` =
  1.5s pacing. Manual `--date` / `--days` recovery bypasses the
  backlog pass entirely (leave that untouched).
- **`run_backlog_pass()` (≈L194+).** Deficit-ordered walk (B2:
  richest-deficit dates first, residue to the back), per-meet paced,
  B1-classified (truncated/error → wall, no strike), capped at
  `BACKLOG_MAX_ATTEMPTS` dates/night, walls after
  `BACKLOG_WALL_THRESHOLD` consecutive empties. Strike sidecar at
  `data/backlog_trickle_state.json`.

**Existing notification path (reuse — do NOT build new):**
- `scripts/liveness_check.py:send_alert(subject, body)` — plain-text
  alert email via Gmail SMTP.
- `scripts/health_check.py` — HTML email via Gmail SMTP; SMTP creds
  loaded from the existing config file. Recovery monitoring reuses
  one of these paths; no new notification channel, no new creds.

**Existing log convention:** `logs/` holds `backup.log`,
`collector.log`, `health_check.log`, `liveness_check.log`. The
deficit-burndown log lands here as a sibling.

**The split, as it stands today.** Recent-first ordering already
guarantees the recent window is served before the backlog (the "never
starve recent" guarantee is structural). But the backlog pass stops
at `BACKLOG_MAX_ATTEMPTS = 20` dates/night even when budget remains —
so the backlog is currently *under-using* the leftover quota. That
ceiling is the lever for "moderate-aggressive, ~80% to backlog."

---

## §6 — Scope A: pacing + budget split (the recovery shape)

**Locked operator calls this implements (treat as decided inputs):**
1. **Pacing — moderate-aggressive, capped.** Deficit-ordered (B2,
   already built), per-meet paced (1.5s floor, already built),
   nightly. Most of each night's Racing-API budget on the backlog,
   **never starving the recent window.** Bulk clears over ~1–2 weeks
   under the daily cap (F-2).
3. **Budget split — ~80% backlog / ~20% recent window** until the
   backlog clears, then revert to recent-window-only.

**The mechanism (Code's build):**

- **Keep recent-first ordering.** It *is* the "never starve recent"
  guarantee — the recent window runs to completion before the backlog
  pass starts. Do not invert it. The recent window is small (a few
  unsynced days), so it consumes only a slice of the night's budget;
  the ~80/20 target is met structurally by letting the backlog
  consume the large remainder, not by enforcing a hard ratio.
- **Raise the backlog per-night ceiling** so the backlog pass uses the
  bulk of the leftover budget instead of stopping early at 20 dates.
  Code names the new value (a recovery-window ceiling materially
  above 20 — e.g. enough to walk the recoverable tail each night
  until the budget walls). The `BACKLOG_WALL_THRESHOLD = 3`
  consecutive-empty self-stop is the safety: the pass stops itself
  when the night's budget is exhausted (F-2), so a high ceiling can
  never hammer an exhausted quota — it just lets the walk go as far as
  the budget allows.
- **Revert condition.** When the recoverable backlog is cleared
  (total in-scope deficit across 2026-03-15→recent falls to ~0, i.e.
  only the genuine early-March residue remains), the elevated ceiling
  reverts to its pre-recovery value (recent-window-only steady
  state). Code implements this as a `BACKLOG_RECOVERY_MODE`-style flag
  or an automatic deficit-threshold check — Code's call; name it in
  the report. The revert must not require a code edit to trigger if an
  automatic check is cleaner, but a manual flag the next session can
  flip is acceptable.

**Do not** change `BACKLOG_FLOOR` (no pre-gap chasing), the per-meet
pacing floor (1.5s), the wall-threshold (the F-2 safety), or the
B1 classifier (already proven). The only pacing lever this brief
touches is the per-night ceiling + its revert condition.

## §7 — Scope B: low-touch monitoring

**Locked operator call this implements:**
2. **Monitoring — low-touch.** Alert on stall/error; notify on
   completion. Nightly deficit-burndown written to a log (glanceable),
   **no nightly push notification.**

**The build:**

- **Deficit-burndown log** — `logs/backlog_recovery.log` (or the
  cleanest sibling under `logs/`). One glanceable line per nightly
  run: date/time (Adelaide), total recoverable deficit before →
  after, placings landed this pass, dates attempted / walled /
  struck, and an estimate of nights-to-clear at the current burn
  rate. Append-only; this is the operator's at-a-glance progress
  view. **No push notification per night** — the log is pulled, not
  pushed.
- **Stall/error alert (pushed)** — fire the existing `send_alert`
  email path **only** on an exceptional condition: the nightly run
  errors out / fails to run, or the burndown stalls (e.g. N
  consecutive nights with ~zero net progress while deficit remains —
  Code names N, suggest 3). This is the "something is wrong" signal,
  not routine progress.
- **Completion notify (pushed, once)** — when the recoverable backlog
  clears (the §6 revert condition trips), fire a single completion
  email via the same path. One notify at the end, not nightly.

Reuse the existing SMTP/`send_alert` plumbing and recipient config.
**No new notification infrastructure, no new credentials, no new
service.** If a tiny shared helper is the clean way to call
`send_alert` from the backfill script, that is acceptable; prefer
import/reuse over duplication.

## §8 — Sequencing within the session

1. **Baseline the dirty tree.** `git status --short` and `git diff`
   on the target file(s). Record the pre-existing S198 modified
   regions so intended edits are distinguishable from prior fix work.
2. **Baseline the deficit (before).** Query `get_backlog_dates()` /
   `capture.db` for the total recoverable in-scope deficit (sum of
   unfilled in-scope runners over 2026-03-15→recent) and the per-date
   deficit list. This is the burndown's starting point.
3. **Scope B — monitoring first** (the burndown log + alert/notify
   wiring), so the proving pass in step 5 is observed.
4. **Scope A — pacing/budget split** (raised ceiling + revert
   condition).
5. **Proving pass.** Run **one** controlled argless-equivalent pass
   (accept it spends a real budget slice — the recovery runs nightly
   anyway). Capture: recent window served first (not starved), backlog
   consumed the bulk, deficit moved, a burndown line written, no false
   strikes, Part A guard intact (no overwrite). Verify the revert
   condition by logic/unit (the real clear takes ~1–2 weeks, not
   provable in-session).
6. **Report.**

If the monitoring wiring or the budget-split change does not verify
clean, **stop and report** — do not leave the nightly timer running an
unproven recovery shape.

## §9 — Empirical verification (capture before + after)

- **Deficit baseline (before/after).** Total recoverable in-scope
  deficit and per-date list before; after the proving pass, the same
  — showing the burn (`gained > 0` on the richest-deficit dates) and
  the residue unchanged at the back.
- **Recent-not-starved proof.** Confirm the recent window was
  processed before the backlog pass and received its full fetch (the
  "never starve recent" guarantee held).
- **Budget-skew proof.** Confirm the backlog pass consumed the bulk of
  the night's budget (walked materially more than the old 20-date
  ceiling, up to the wall) — the ~80/20 skew in practice.
- **No-false-strike / no-overwrite proof.** Confirm B1 still classes
  truncated fetches transient (no strike) and Part A's identity guard
  still routes results to the correctly-named horse (no Betfair-path
  incumbent overwritten) — i.e. the recovery rides on the proven fix
  unchanged.
- **Monitoring proof.** A burndown line landed in the log with the
  expected fields; a forced error path fires the alert email; the
  completion-notify path is exercised (e.g. dry-run / simulated
  deficit=0) without waiting the full clear.
- **Revert proof (logic).** Confirm the ceiling reverts to the
  pre-recovery value when the deficit-clear condition is met.

Prefer empirically-determined dates/deficits (query the DB) over
hard-coded ones (the fix report's §3 figures are a sanity anchor,
not a contract — the live deficit moves nightly).

## §10 — Output spec

- **Single file:**
  `/Users/tim/Desktop/Projects/bethub-rebuild/recovery_run_report.md`.
- **Sections:** what changed (Scope A pacing/budget split with the
  chosen ceiling + revert mechanism named; Scope B monitoring); the
  verify results (§9 before/after tables); the deficit baseline +
  first-pass burndown; the chosen revert mechanism and why; any
  findings; dirty-tree confirmation (`git status` unchanged except
  the intended edits); self-assessment including an honest
  nights-to-clear estimate at the observed burn rate.
- **Length:** ~200–350 lines. Tables over prose for the verify
  results and the deficit baseline.
- **Does not contain:** a schema proposal, a rewrite of the fix,
  scope into other backlog/cutover items, or a claim that the full
  backlog cleared in-session (it won't — the clear builds over
  nights; report the burn rate and the estimate instead).

## §11 — Hard limits (non-negotiable)

**Scope:**
- **No schema change / migration.** No new columns, no change to the
  stored `runner_key` derivation, no constraint changes.
- **No re-work of the S198 fix.** Part A guard, B1 classifier, B2
  ordering, per-meet pacing, `sync_day` fetch logic — all proven,
  all off-limits. This brief only touches the per-night ceiling + its
  revert, plus the monitoring wiring.
- **No new notification infrastructure.** Reuse the existing
  SMTP/`send_alert` path and recipient config.
- **No babysitting the full recovery.** Single bounded session: wire
  + prove + report. The nightly timer carries the multi-night
  recovery.
- **Named anchors only** (§5–§7). No drift into adjacent code.
- **No touch** to v3, settlement, money path, or Betfair operational
  pricing. Capture-side analytical only (DR-033).
- **Do not change** `BACKLOG_FLOOR`, the 1.5s pacing floor, the
  wall-threshold, or `BACKLOG_FREEZE_RETIRE` (stays `False`).

**Dirty-tree discipline (working tree is dirty):**
- **No git operations of any kind** — no `add`, `commit`, `stash`,
  `restore`, `checkout` (file-targeted), or `reset`.
- The S198 fix left `subscription/racing_api.py`,
  `storage/database.py`, `scripts/backfill_race_metadata.py` as `M`
  (plus other pre-existing in-flight `M`/`??`). Those regions are
  **not drift** — do not revert, tidy, or touch them. Edit only the
  recovery anchors.
- After each edit, run `git diff <file>` to confirm only the intended
  lines were added. `py_compile`-clean each edited file.
- At session close, `git status --short` confirms the dirty file list
  is unchanged except the intended recovery edits.

**Session shape:**
- Single bounded session. If the work doesn't fit, that's a finding,
  not a continuation.
- No mid-session operator escalation — surprises become findings.

## §12 — What happens after Code's session

The next operator-Claude (Chat) session reads
`recovery_run_report.md` and triages: confirm the budget split + the
monitoring wired clean, confirm the first burndown line and the
nights-to-clear estimate, then **monitor low-touch** — glance the
`logs/backlog_recovery.log` burndown over the ~1–2 week recovery, act
only on a stall/error alert. On backlog-clear (the completion notify
fires), the next session confirms the revert to recent-window-only
steady state and closes the recovery milestone. Code does **not**
write any follow-on brief; the recovery runs itself via the timer.

## §13 — Cross-references

- `placings_landing_fix_report.md` §4 (B2 deficit ordering), §5
  (F-1 pacing, F-2 budget caveat), §8 (the hand-off this brief
  executes) — primary anchor.
- `placings_landing_fix_brief.md` / `placings_landing_diagnosis_report.md`
  — the locked fix contract + RC-1/RC-2 root cause this recovery
  rides on, unchanged.
- **DR-033** (data-source roles) — placings analytical, settlement
  Betfair-only: the reason this whole recovery is bet-safe by
  construction.
- **DR-027 / DR-028** (two-database boundary) — capture.db is the
  analytical store; this work stays entirely capture-side.
- **DR-021** — Adelaide local timestamps in the report.

*End of brief (LOCKED — Session 201, cleared for Code).*
