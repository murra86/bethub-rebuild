# Brief — empty-runners degradation: diagnosis + conditional fix

**Type:** Diagnosis-first probe with a **conditional** surgical fix (read-write, two named files only). Single bounded Code session.
**Status:** LOCKED — drafted and locked 2026-07-01 (Session 212).
**Anchored on:** `placings_throughput_fix_report.md` §3.1 / §4 / §7 (the throughput-fix burn that surfaced this mode).
**Bet-safety:** CLEAN by construction — analytical/capture side only (DR-033). No operational/betting DB, no Betfair operational path, no bet mutation touched.

---

## §1 — What this brief is and is not

Code characterises the **empty-runners degradation mode**, determines whether pacing or a retry-extension defeats it, and — **only if the diagnosis supports it** — makes a bounded surgical change to close it. Diagnosis comes first; the fix is contingent on what the diagnosis shows.

- Single bounded Code session. If it doesn't fit, that's a finding, not a continuation.
- Surprises become findings in the report, not mid-session escalations.
- Code does **not** touch the `race_date` identity key (fault B — §9). Ghost-row behaviour is measured and reported, never remediated.
- This is **not** the full-backlog burn. The verification burn here is a bounded ~20–40-date proof; the full clear stays a separate later brief (§10).

## §2 — Why this work exists

The throughput-fix session (`placings_throughput_fix_report.md`) proved pacing works (3.15 req/sec, zero empty-200s) and that placings flow at scale (872 on the one date that fetched cleanly), and its ghost-row tripwire did **not** fire. But it surfaced the real remaining throughput gate: under sustained multi-date load — even at 3.15 req/sec, well under the 5/sec ceiling — the API returns HTTP 200 with the **races** array populated but the nested **runner arrays empty**, from the second date of a run onward. The prior retry (§5.1 there) fires only on an empty *races list*, so this mode escapes it and walls the date un-retried. An isolated re-fetch of a walled date returned full runner data, so the mode is **transient**. Until it is characterised and defeated, any full-backlog burn walls after ~one date per run. This brief closes that gate.

## §3 — Pre-reads

Required, in order:

1. This brief.
2. `placings_throughput_fix_report.md` — especially §3.1 (the per-date wall sequence), §4 (achieved pace + empty-200 counts), §7 (the empty-runners key finding + the three candidate levers).
3. `subscription/racing_api.py` — `_fetch_meet_races()`, `sync_day()`, and the empty-200 instrumentation added last session (edit target).
4. `scripts/backfill_race_metadata.py` — `run_backlog_pass()` and the pacing/wall constants (edit target).

Reference-only (not required): `placings_throughput_fix_brief.md`; `BETHUB_DATA_REFERENCE.md` §G (rate tier — no daily quota, 5/sec ceiling).

## §4 — System access

- **VPS:** `root@187.77.183.9` : `/home/racing/racing-data-capture`. **Read-write on the two §3 source files only.** No timer this session (it was moved to 05:30 ACST last session — leave it). No other files edited.
- **capture.db:** opened `mode=ro` for all verification queries, at the canonical `DB_PATH`, via `start_process` Python. Never copied. The verification burn writes placings via the normal path (intended recovery), as last session.
- **Git:** working tree is dirty. Read `git status` at start; edit only named anchors; `git diff <file>` after each edit; `git status` at close to confirm the dirty set changed only by the named files. No `git add/commit/stash/restore/checkout/reset`.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every time reference; note UTC equivalents where relevant.

## §5 — Substantive scope

Diagnosis first (§5.1–§5.2), then a **fork** (§5.3) whose branch Code picks from the diagnosis, plus a guard (§5.4).

### §5.1 — Capture the empty-runners signature (instrumentation)
The prior instrumentation hooks only the empty-*races-list* case. Extend ground-truth capture so that on the **first** "races present, runners empty" response of a run, Code logs once the full status line, response headers, and a compact body shape (race count, runner count, any error/notice fields). This is the cheap replacement for guessing what the API emits under this mode — the prior session couldn't capture it because pacing at 0.2s avoided the empty-200 path entirely and the empty-runners path was uninstrumented.

### §5.2 — Volume-vs-rate diagnostic (the key question)
Determine whether the mode is triggered by **instantaneous rate** or **cumulative burst volume**. 3.15 req/sec was under the 5/sec ceiling yet still degraded from date 2, which points at volume — but that is a hypothesis to test, not assume. Run controlled bounded bursts varying the pacing levers independently: the current per-request delay, a larger inter-meet delay, and an inter-**date** pause between dates. For each configuration, record at which point (if any) date 2+ returns full runner arrays. The deliverable is a small table: pacing config → did the empty-runners mode appear, and from which date.

### §5.3 — Conditional remediation (fork — Code chooses, reasons it in the report)
- **If §5.2 shows a pacing config reliably avoids the mode** → set that pacing (the minimal slowdown that works) in `scripts/backfill_race_metadata.py`. Do **not** add a runners-empty retry in that case; report that pacing alone closes it.
- **If §5.2 shows the mode persists regardless of pacing but is retry-defeatable** (isolated re-fetch returns full data) → extend the meet-level retry in `_fetch_meet_races()` to treat "races present, runners empty" as degradation and re-fetch with the same escalating backoff, subject to the §5.4 guard.
- **If neither defeats it** → change nothing, report the characterisation, and route to operator triage (this becomes a rate-tier / provider question, not a code fix).

### §5.4 — Guard against genuinely runner-less meets
A legitimately abandoned/void meet can return races with no runners. The runners-empty retry (if taken in §5.3) must not spin on those. Define and implement the guard — e.g. bounded retry count, and a distinguishing signal (a meet that returns full data on isolated re-fetch was degraded; one that stays empty is genuinely runner-less). Report the observed distribution of the two.

## §6 — Sequencing within session

§5.1 (instrument) → §5.2 (pacing sweep, using the instrumentation to see the mode clearly) → §5.3 fork (decide + implement based on §5.2) → §5.4 guard (only if the retry branch is taken) → §7 verification. Rationale: the fork can't be resolved until the volume-vs-rate result is in, so diagnosis strictly precedes any edit.

## §7 — Empirical verification

- **Baseline (`mode=ro`):** recoverable deficit and filled-count across a bounded historical slice, as last session (deficit currently ~40,987).
- **Burn:** a bounded ~20–40-date deficit-ordered burn at the chosen config. Capture: dates attempted, dates that gained placings, total placings gained, achieved req/sec (confirm ≤5/sec), empty-runners occurrences before vs after remediation, and whether the pass still walls (and on what).
- **Ghost-row tripwire (`mode=ro`, fault-B guard):** re-run the prior session's race-row before/after comparison across the burn window. Report any positive (new-row) delta with `race_date` vs `scheduled_start` examples. Measured only — no remediation.
- **Success =** date 2+ returns full runner arrays across the burn (mode defeated), **or** a clear characterisation of why not with the pacing floor identified. Ghost-row creation is reported, not a pass/fail gate.

## §8 — Output spec

Single file: `placings_empty_runners_diagnosis_report.md` in the rebuild folder root.

Sections: (1) mode characterisation + the captured signature (§5.1); (2) volume-vs-rate results table (§5.2); (3) the fork decision + what was changed, if anything (§5.3–§5.4); (4) verification burn results (§7); (5) ghost-row tripwire result; (6) self-assessment incl. hard limits touched + dirty-set confirmation.

~250–400 lines. Contains **no** fault-B recommendation beyond the tripwire result, **no** full-backlog-burn attempt, and **no** overall "recovery is solved" verdict — that's operator-Claude's triage call.

## §9 — Hard limits (non-negotiable)

Code does **not**:
- Touch `race_date`, `upsert_race`'s conflict key, or any canonical race-identity logic (fault B — DR-032/034 territory; separate brief).
- Change any schema (no columns, tables, indexes).
- Edit any file other than `subscription/racing_api.py` and `scripts/backfill_race_metadata.py`.
- Touch the timer, the live-capture orchestrator, the Betfair path, or anything operational/betting.
- Attempt the full 41k backlog — the §7 burn is a bounded proof.
- Run any git write op; edit outside named anchors; escalate mid-session.
- Propose remediation for ghost rows or `race_date` (report the tripwire only).

## §10 — What happens after Code's session

Next operator-Claude session reads `placings_empty_runners_diagnosis_report.md` and triages:
- **Mode defeated (pacing or retry)** → commission the full-backlog burn brief (dedicated mode/timer to walk all deficit dates to zero), per the original throughput brief's §10.
- **Mode not defeated** → the finding reshapes recovery: accept the slower per-night trickle, and/or escalate the rate-tier question with theracingapi.com (the add-on reply is still pending). Code does not write either follow-up; that's the next session's work.

## §11 — Cross-references

- Governing DRs: DR-021 (timestamp anchoring), DR-033 (Betfair operational / Racing API analytical — this is analytical side). DR-032 / DR-034 (canonical race identity) are the *excluded* territory (§9).
- Prior artefacts: `placings_throughput_fix_report.md` (§7 empty-runners finding + candidate levers), `placings_throughput_fix_brief.md`, `BETHUB_DATA_REFERENCE.md` §G (rate tier).
- Excluded / parked: full-backlog burn mode, ghost-row / `race_date` identity fix, the theracingapi.com rate-tier reply.
