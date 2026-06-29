# Placings backlog-trickle — nightly results-sync standing change (brief)

**Drafted:** Session 192, 2026-06-25 22:36 ACST.
**For:** Claude Code, single bounded out-of-session session.
**Builds on:** `placings_backfill_report.md` (S192-triaged) — the forward
fix to `get_unsynced_dates` is LANDED (bounded, recent-first, 14-day
window) and is the substrate this brief extends.
**Mode:** READ-WRITE, capture-side / analytical only. One repo source
anchor on the VPS; recovery writes through the existing `sync_day()`
upsert; reads `mode=ro`. No v3 / settlement / live-betting / money-path
contact. No auto-settle.

---

## 1. What this brief is and is not

This is a **surgical standing change** to one VPS script: the nightly
racing-metadata sync. It adds a **backlog-trickle pass** that runs after
the existing recent-window pass and spends *leftover* Racing-API daily
quota filling the oldest still-missing finishing-position dates — bounded
so the recent window is never starved, idempotent, self-healing across
nights, and self-stopping once the backlog is filled.

It is a single bounded Code session. Surprises become **findings** in the
report, not mid-session escalations and not scope creep. Remediation and
any follow-on routing are the next operator-Claude session's job — this
brief commissions the change and its verification, nothing past it.

It is **not** a one-off recovery script (the manual `--date`/`--days`
recovery path already exists and is unchanged). It is **not** an
auto-settlement change, a schema migration, or anything touching live
betting.

## 2. Why this work exists

The S174/S191 finish-position gap (placings ~0.1% since May) is analytical
capture for future auto-settle readiness and racing analytics — placings
settle by the operator's manual flag today (DR-033, the data-source-roles
decision), so this is background investment, not a live-betting blocker.
The S192 forward fix stopped the nightly job starving recent dates, but
left ~114 historical dates (2026-03-01 → 2026-06-24, minus 2026-06-20)
unrecovered — purely Racing-API daily-quota-gated, not a fix failure.
The operator's routing call: recover the backlog automatically, in the
background, off leftover daily quota, with recent data always winning
first. Speed is explicitly not the priority — **reliability and
self-stopping are.**

## 3. Pre-reads

Required, in order:
1. `placings_backfill_report.md` (rebuild root) — the forward fix this
   extends; §4 (the landed `get_unsynced_dates` change), §5 (the proven
   `sync_day` fill + the quota wall), §8 findings (F1–F5, esp. F2 the
   permanently-unbounded `IS NULL` set and F3 the daily quota).
2. This brief.

Reference-only (read on demand, not required): `placings_backfill_brief.md`
(the prior contract), `vps_supply_review.md` (§4 the quantified gap).

## 4. System access

- **VPS** `/home/racing/racing-data-capture` (branch `master`, HEAD
  `5f71488`). SSH via the operator's unlocked ssh-agent (the VPS key is
  passphrase-protected — the operator runs this session from the
  logged-in Mac session). Step-0 gate: `ssh racing-vps 'echo ok'` with
  `-o ClearAllForwardings=yes` before any work.
- **capture.db** `/home/racing/racing-data-capture/data/capture.db`
  (~3.97 GB, live WAL). Reads `mode=ro`. Writes ONLY through the existing
  `sync_day()` idempotent upsert — never a hand-edit, never a copy.
- **READ-WRITE** to one source anchor (§5). Timestamps: capture.db stores
  UTC; every time-of-day reference in the report is Adelaide local
  (ACST/ACDT) per DR-021.

## 5. Substantive scope

### 5.0 Baseline gate (STOP condition)

Before editing, confirm the substrate is what this brief assumes:
- HEAD is `5f71488`.
- `get_unsynced_dates` in `scripts/backfill_race_metadata.py` is in its
  **post-S192-fix form** — bounded, recent-first (`date(race_date) >=
  date('now', ?)`, `ORDER BY race_date DESC`, `trailing_days` default 14).
- Working tree is dirty from the March rework AND the S192 forward fix:
  `scripts/backfill_race_metadata.py` is expected to show as `M` (the
  prior session's landed edit — **intended substrate, build on it, do not
  revert it**). The rest of the dirty list matches
  `placings_backfill_report.md` §2.

If the substrate is not this (fix absent, HEAD moved, anchor file clean),
**STOP and report** — do not build the backlog pass on an unknown base.

### 5.1 The backlog selector (new)

Add a selector that returns the **oldest-first** set of dates that are
backlog-incomplete — past dates inside the Racing-API window with
thoroughbred races still missing finishing positions. Bounded below by the
gap floor **2026-03-01** (do not chase already-complete pre-gap history).

Detection mechanism is **Code's call** — but it MUST NOT key on
`subscription_synced_at IS NULL` (F2: that set is permanently unbounded via
greyhound/harness rows the thoroughbred-only Racing API never enriches).
Key on actual finishing-position incompleteness for thoroughbred races
instead. Surface the chosen predicate as a finding.

### 5.2 The backlog pass (new, in the nightly entry)

In the argless nightly path (`main()`), after the existing recent-window
pass completes, run a backlog pass with these **behaviour requirements**:

- **Recent-first is a hard rule.** The backlog pass runs ONLY after the
  recent pass, and only on whatever quota is left. Recent/live-relevant
  data is never starved by backlog work — this is structural, not a
  preference.
- **Leftover-only, stop-on-wall.** Walk the backlog selector oldest-first,
  filling each date via `sync_day()`. Stop the pass for the night on the
  quota-wall signal (consecutive zero-runner dates — the same signal the
  S192 run used to stop cleanly). No need to know the exact quota number.
- **Idempotent** — `sync_day()` upsert, proven in `placings_backfill_report.md` §5.1.
- **Self-healing across nights** — a date left unfilled (quota-blocked
  this night) is simply still in the selector tomorrow; no manual nudge.
- **Don't retry genuinely-resultless dates forever.** A date that returns
  zero on repeated attempts *with quota available* is eventually
  classified "no results available" and dropped from the backlog set
  (logged). Mechanism is Code's call; if it needs lightweight persistence,
  a minimal capture-side tracking table/file is acceptable — but surface
  the choice as a finding. Do NOT alter the schema of any existing
  operational/capture table silently.
- **Self-stopping** — once no backlog-incomplete dates remain, the pass is
  a clean no-op and the nightly run is just the recent fill again.

### 5.3 Per-night logging (new)

The backlog pass appends one summary line per night to the existing
`metadata_backfill.log`, e.g.:

`BACKLOG PASS: attempted=N filled=M runners=R oldest_remaining=YYYY-MM-DD remaining_backlog_dates=K`

and on completion `BACKLOG COMPLETE`. This is the operator's window into
the true leftover-quota rate and the closing signal (`remaining_backlog_dates`
trending to 0) — it lets the next session confirm the trickle is closing,
not stalling, after 2–3 nights.

## 6. Sequencing within session

1. Step-0 SSH gate + §5.0 baseline gate.
2. Read working-tree state (`git status`) and record it.
3. Build the backlog selector (§5.1) — verify read-only what it returns
   against the live DB before wiring it in.
4. Wire the backlog pass into the nightly entry (§5.2) + logging (§5.3).
5. Verify (§7).

The recent-pass code is already correct (S192) — do not re-touch it beyond
calling it first in the nightly path.

## 7. Empirical verification

- **Pre:** finish-position coverage by month (reproduce
  `placings_backfill_report.md` §6); what the recent-window `get_unsynced_dates()`
  returns; what the new backlog selector returns (count + oldest/newest).
- **Mechanism proof:** show the nightly argless path now runs recent-pass
  → backlog-pass in that order; show the backlog pass consumes only
  leftover (stops on the consecutive-zero wall); show oldest-first; show
  the self-stop path when the selector is empty.
- **Post (bounded, in-session):** run one backlog increment with whatever
  quota is available and show the log line(s) emitted + any dates filled.
  If quota is already spent for the day (likely, per F3), that itself is a
  valid result — show the wall was hit and the pass stopped cleanly.
- **Carve-out (out-of-session, S36 precedent):** the true multi-night rate
  and full gap closure can only be proven by the nightly runs themselves.
  In-session, prove the **mechanism** and one increment; the live rate is
  read from the logs over the following nights.

## 8. Output spec

Single file: `placings_trickle_report.md` (rebuild root). ~150–220 lines.
Sections: run header; baseline-gate result; working-tree gate; the backlog
selector (predicate chosen + what it returns); the backlog pass (the edit,
`git diff`, behaviour); logging; pre/post coverage; mechanism verification
+ carve-out; findings (surprises as findings); self-assessment (what could
not be tested and why).

Does NOT contain: remediation proposals, a next brief, an overall
go/no-go verdict on cutover, or any scope past the backlog-trickle change.

## 9. Hard limits — NOT in scope

- **No auto-settlement, no v3, no settlement, no money-path, no
  live-betting contact.** Capture-side / analytical only.
- **No schema change to existing operational/capture tables.** A minimal
  dedicated tracking table/file for attempt-counts is permitted IF needed,
  surfaced as a finding — never a silent alter of existing tables.
- **Recent window is never starved** — backlog runs after, on leftover
  only. Non-negotiable.
- **No touch to** the scrapers, the Betfair path, `sync_day()`'s internals
  (call it, don't rewrite it), the harness/greyhound enrichment mapping
  (F2 names it only as the cause of the unbounded set), or the manual
  `--date`/`--days` recovery paths (leave them working and bypassing).
- **No new fast path / no rate-limit relaxation.** Keep `--delay >= 1.5`,
  single-threaded. The daily quota is a ceiling to respect, not beat.
- **Dirty-tree discipline:** no `git add/commit/stash/restore/checkout/reset`.
  Read tree at start; edit only the named anchor
  (`scripts/backfill_race_metadata.py`); `git diff` after each edit; `git
  status` at close to confirm the dirty list is unchanged except the
  anchor. The anchor already carries the S192 forward-fix edit — that is
  intended substrate, not drift to revert.
- **Single bounded session.** If the work doesn't fit, that's a finding,
  not a continuation.

## 10. What happens after Code's session

The next operator-Claude session reads `placings_trickle_report.md`,
confirms (a) the mechanism is sound — recent-first, leftover-only,
self-stopping — and (b) the first in-session increment behaved. From there
it's hands-off background: the operator lets the nightly runs trickle the
backlog closed over ~2 weeks, and a later session spot-checks the log rate
(`remaining_backlog_dates` trending to 0) to confirm it's closing, not
stalling. No follow-on Code brief is expected unless the rate stalls or a
finding surfaces one. Code does not write that next brief.

## 11. Cross-references

- **Serves:** the S174/S191 finish-position (placings) gap — analytical
  capture / future auto-settle readiness.
- **Builds on:** `placings_backfill_report.md` (the landed forward fix +
  F1–F5), `placings_backfill_brief.md` (the prior contract).
- **DRs:** DR-033 (data-source roles — placings settle manual, this is
  analytical; the reason speed isn't urgent); DR-021 (Adelaide
  timestamps); DR-027/028 (the v3↔capture boundary — untouched here; this
  is all capture-side).
- **Excludes (parking-lot):** the older months' pre-existing ~20%
  finish-position residual (Nov–Feb sit ~77–80%, never 100%) — a separate,
  smaller, pre-existing thing, NOT the Mar–Jun collapse this brief closes;
  the harness/greyhound mislabel + empty-runner resolve edge (S191
  usability gaps); auto-settle (deferred, DR-033).
