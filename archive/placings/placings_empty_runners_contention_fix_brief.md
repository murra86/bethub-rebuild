# Brief — empty-runners degradation: contention fix (decouple fetch-from-write)

**Type:** Surgical fix, single named function, single named file. Single bounded Code session.
**Status:** LOCKED — 2026-07-01 (Session 213).
**Anchored on:** `placings_empty_runners_diagnosis_report.md` (Session 213, 2026-07-01) §2c, §3, §10.
**Bet-safety:** CLEAN by construction — analytical/capture side only (DR-033). No operational/betting DB, no Betfair operational path, no bet mutation touched.

---

## §1 — What this brief is and is not

Code restructures `sync_day()` so that, for a given date, **all meets are fetched from the Racing API before any write to `capture.db`** — closing the write-path contention trigger the diagnosis isolated. This is a structural fix to the fetch/write ordering, not a pacing tweak and not a retry extension (both were tested and rejected/unsupported last session).

- Single bounded Code session. If it doesn't fit, that's a finding, not a continuation.
- Surprises become findings in the report, not mid-session escalations.
- Code does **not** touch `race_date`, `upsert_race`'s conflict key, or any canonical race-identity logic (fault B — separate territory).
- This is **not** the full-backlog burn. Verification here is a bounded ~20–40-date proof; the full 41k-deficit clear is a separate later brief, contingent on this fix holding.
- Collector-idle-window scheduling (the diagnosis report's other candidate lever) is explicitly **out of scope** this session — parked, not pursued.

## §2 — Why this work exists

`placings_empty_runners_diagnosis_report.md` isolated the empty-runners mode to `sync_day`'s **write path contending with the live collector on the shared `capture.db`** — a fetch-only client is immune at up to ~9.8 req/sec (2× the rate ceiling), and writing identical data to a throwaway DB is immune, but writing to the real, collector-contended `capture.db` degrades from the second meet-write onward within a date. No pacing config defeats it (write-path delays up to 2.0 s inter-meet and 20 s inter-date all still degrade), and retry-defeatability under real degradation was unverified (the mode never fired during any retry-capable run). The diagnosis explicitly routed the fix to operator/architecture triage, naming fetch-then-write decoupling as the clean structural candidate. This brief takes that candidate and locks it in.

## §3 — Pre-reads

Required, in order:

1. This brief.
2. `placings_empty_runners_diagnosis_report.md` — full report, especially §2c (mechanism triangulation), §3 (fork decision + why branch 3 was taken), §10 (routing).
3. `placings_empty_runners_diagnosis_brief.md` — the prior locked brief, for the §5.1 instrumentation spec (must not be removed or altered by this fix).
4. `subscription/racing_api.py` — current `sync_day()` and `_fetch_meet_races()` in full, including the §5.1 empty-runners-signature instrumentation landed last session. This is the primary edit target.
5. `scripts/backfill_race_metadata.py` — `run_backlog_pass()`, to confirm it calls `sync_day()` per-date and doesn't assume per-meet incremental writes (i.e. that batching writes to date-end doesn't break its progress accounting or logging).

Reference-only (not required): `placings_throughput_fix_report.md`; `BETHUB_DATA_REFERENCE.md` §G.

## §4 — System access

- **VPS:** `root@187.77.183.9` : `/home/racing/racing-data-capture`. **Read-write on `subscription/racing_api.py` only.** `scripts/backfill_race_metadata.py` is read-only this session unless the pre-read (§3.5) surfaces a genuine incompatibility with batched writes — if so, that's a finding to report, not a silent edit; hold and note it rather than touching a second file without operator sign-off.
- **No timer change.** Nightly timer stays at 05:30 ACST.
- **capture.db:** opened `mode=ro` for all verification baseline/after queries, at the canonical `DB_PATH`, via `start_process` Python. Never copied. The verification burn writes placings via the normal (now-restructured) path — intended recovery.
- **Git:** working tree is dirty (expected — VPS repo, per standing discipline). Read `git status` at start. Edit only `subscription/racing_api.py`. Run `git diff subscription/racing_api.py` after the edit to confirm only the intended restructure landed. `git status` at close to confirm the dirty *set* (files touched) is unchanged except for this file's content. No `git add/commit/stash/restore/checkout/reset`.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every time reference; note UTC equivalents where relevant.

## §5 — Substantive scope

### §5.1 — Restructure `sync_day()`: fetch phase, then write phase

Split the current per-meet fetch-then-write loop into two sequential phases for the date:

- **Fetch phase:** iterate the date's meets, calling the existing `_fetch_meet_races()` (unchanged — including its existing retry/backoff and the §5.1 empty-runners-signature instrumentation from last session, which must survive this edit intact) for each meet, and **accumulate the parsed results in memory** (per-meet races + runners) without writing to `capture.db`. No behavioural change to the fetch call itself, its pacing, or its retry logic.
- **Write phase:** once all meets for the date have been fetched, write the accumulated results to `capture.db` via the existing upsert path (`init_db` / whatever `sync_day` currently calls per-meet), iterating the in-memory results. Wrap the date's writes in a single transaction if the current upsert path supports it cleanly — this further minimises the total time `capture.db` is held mid-write, but is a "do if clean, don't force it" call for Code, not a hard requirement.

**Memory footprint is a non-issue at this scale** (one date ≈ 150–200 races, low thousands of runners) — no streaming/chunking needed; hold the full date's fetch results in memory before writing.

**What does not change:** the meet-level fetch pacing/delay, the existing retry logic for genuine API failures, the existing empty-*races-list* retry (unrelated mode, already handled), the §5.1 signature-logging instrumentation, and the upsert semantics themselves (same conflict keys, same fields written). This is purely a reordering of *when* writes happen relative to fetches within a date — not a change to *what* gets written or how conflicts are resolved.

### §5.2 — Confirm `run_backlog_pass()` compatibility (read-only check)

Before or alongside §5.1, confirm `run_backlog_pass()` in `scripts/backfill_race_metadata.py` doesn't depend on `sync_day()` writing incrementally per-meet (e.g. for progress logging, partial-date resume behaviour, or a per-meet write count it surfaces). If it's compatible as-is, no edit needed there. If it isn't, report the incompatibility as a finding — do not edit the second file without it being named here.

## §6 — Sequencing within session

Read pre-reads (§3) → confirm current `sync_day()` structure and `run_backlog_pass()` compatibility (§5.2) → implement the fetch/write split (§5.1) → `py_compile`/import check → verification burn (§7). Rationale: the compatibility check is cheap and should happen before the restructure, not discovered after.

## §7 — Empirical verification

- **Baseline (`mode=ro`):** recoverable deficit (≥ 2026-03-15) and filled-count across the same class of bounded historical slice used last session, taken immediately before the burn.
- **Burn:** a bounded ~20–40-date deficit-ordered burn via `run_backlog_pass()` at the current production pacing config (unchanged — this fix targets the write-ordering, not the pacing). Capture: dates attempted, dates that gained placings, total placings gained, achieved req/sec (confirm ≤5/sec), empty-runners occurrences during the burn, and whether the pass walls (and on what).
- **Ghost-row tripwire (`mode=ro`, fault-B guard):** re-run the prior sessions' race-row before/after comparison across the burn window. Report any positive (new-row) delta with `race_date` vs `scheduled_start` examples. Measured only — no remediation.
- **Success =** the burn walks past date 1 without the empty-runners mode firing on subsequent dates within the window (mode defeated for this burn), **or** a clear report of partial improvement / continued failure with the mechanism note (the mode is intermittent and collector-load-linked, so a clean burn during a genuinely busy collector window is possible even with the fix working — note collector activity if observable, don't over-claim from one burn).

## §8 — Output spec

Single file: `placings_empty_runners_contention_fix_report.md` in the rebuild folder root.

Sections: (1) what changed in `sync_day()` (the restructure, with a short before/after description — not a full diff dump); (2) `run_backlog_pass()` compatibility check result (§5.2); (3) verification burn results (§7); (4) ghost-row tripwire result; (5) self-assessment incl. hard limits touched + dirty-set confirmation.

~150–300 lines. Contains **no** fault-B recommendation beyond the tripwire result, **no** full-backlog-burn attempt, and **no** overall "recovery is solved" verdict — that's operator-Claude's triage call, especially given the mode's known intermittency.

## §9 — Hard limits (non-negotiable)

Code does **not**:
- Touch `race_date`, `upsert_race`'s conflict key, or any canonical race-identity logic.
- Change any schema (no columns, tables, indexes).
- Edit any file other than `subscription/racing_api.py` (and `scripts/backfill_race_metadata.py` **only if** §5.2 surfaces a named, reported incompatibility — otherwise read-only).
- Change the meet-level fetch pacing/delay, the existing retry logic, or the empty-races-list retry.
- Remove or alter the §5.1 empty-runners-signature instrumentation from last session.
- Touch the timer, the live-capture orchestrator/collector, the Betfair path, or anything operational/betting.
- Attempt the full 41k backlog — the §7 burn is a bounded proof.
- Run any git write op; edit outside named anchors; escalate mid-session.
- Propose remediation for ghost rows or `race_date` (report the tripwire only).

## §10 — What happens after Code's session

Next operator-Claude session reads `placings_empty_runners_contention_fix_report.md` and triages:
- **Mode defeated (burn walks clean)** → commission the full-backlog burn brief (dedicated mode/timer to walk all deficit dates to zero).
- **Mode persists or result is ambiguous** (given intermittency, a single clean burn isn't full proof either way) → weigh a second, longer-window burn for confidence, or fall back to the collector-idle-window lever (B') as a complementary/alternative fix. Code does not write either follow-up; that's the next session's work.

## §11 — Cross-references

- Governing DRs: DR-021 (timestamp anchoring), DR-027/DR-028 (two-database architecture + cross-DB integration boundary — this fix operates entirely within the analytical side, but the contention mechanism is a live example of why that boundary discipline exists), DR-033 (Betfair operational / Racing API analytical split — analytical side).
- Prior artefacts: `placings_empty_runners_diagnosis_report.md` (the finding this brief acts on), `placings_empty_runners_diagnosis_brief.md` (the §5.1 instrumentation spec), `placings_throughput_fix_report.md`.
- Excluded / parked: collector-idle-window scheduling (B'), backfill DB-connection isolation (C), full-backlog burn, ghost-row / `race_date` identity fix.
