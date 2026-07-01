# Session 212 — git baseline + empty-runners brief (locked → Code-executed → DB-write-contention finding)

**Opened:** 2026-07-01 12:28 ACST (headless runner)
**Closed:** 2026-07-01 14:44 ACST
**Tool routing:** Desktop Commander (filesystem/process); read-only `capture.db` verification via prior report.
**Governing DRs:** DR-021 (Adelaide timestamps), DR-033 (Betfair operational / Racing API analytical — this session analytical side). DR-032/DR-034 (canonical race identity) referenced only as *excluded* territory.

## Anchor
- Open: runner fast-path, 12:28 ACST (result stamp 12:28; S211 close was 12:22).
- Close: `TZ="Australia/Adelaide" date` → 2026-07-01 14:44 ACST.

## Pre-flight checks
- Runner opened on the fresh S212 result; the open was clean (drift-check passed, S211 record present).
- Root clean, no phantom files (`system_snapshot.md` / `context_index.md` / `STATUS.md` / `CLAUDE.md` absent — correct).
- `.close_out_backups/` held S210/S211/S212 prompts at open; S210/S211 confirmed stale and operator-deleted mid-session; only S212 remained pre-close.

## Session shape
An operator-directed housekeeping + brief-drafting + close session, with a Code execution landing mid-arc. Three strands: (1) git hygiene — closed a 13-session uncommitted-drift gap; (2) the empty-runners diagnosis brief drafted, locked, and (out-of-session) executed by Code; (3) advice on multi-agent review timing. The Code run completing mid-session turned the planned "auto-triage next session" into a report that already exists at close — S213 triages it on open.

## What was delivered
1. **Git baseline commit `c7f71ab`.** Sessions 198–211 governance docs, briefs, reports, and session records (46 files) put under version control; `.close_out_backups/` and `skills/*.zip` gitignored as transient/build artefacts. The repo previously had a single baseline commit with ~13 sessions of untracked/modified work sitting only in the working tree — that drift is now closed. The runner's open-flag (brief git-blob hash ≠ recorded `8880f78c`) was diagnosed as a **false alarm**: git-blob SHA-1 (`3f34…`) vs the recorded sha256 (`8880f78c…`) — different algorithms, identical content, verified twice. No content drift. Advice recorded (open item): the open-ritual drift-check should compute `shasum -a 256`, not `git hash-object`.
2. **Stale-file cleanup.** Verified `.close_out_backups/SESSION_210/211_opening_prompt.md` (closed sessions, not live reads) and the `~/.bethub-cycle` `SESSION_9001` test-watcher fixtures as stale; live watcher watches `.close_out_backups` and doesn't reference the fixtures. Permanent-delete boundary held — Claude verified staleness and handed the operator exact `rm` commands; **operator performed the deletes**. `.close_out_backups/` now holds only the current prompt.
3. **Throughput-fix report triaged** (`placings_throughput_fix_report.md`, carried from the open). Verdict: **partial success**. Pacing model corrected (`BACKLOG_MIN_DELAY` 1.5→0.2, ~3.15 req/sec clean, zero empty-200s); **ghost-row tripwire did NOT fire** (fault B not biting; net race-row delta 0); ~892 placings recovered (deficit 41,879 → 40,987). Nightly timer moved off the 23:30 contention slot to **05:30 ACST** (20:00 UTC, DST-safe) — this **answers the dated 1-Jul timer-shift check**. Surfaced the **empty-runners degradation mode** as the real remaining throughput gate.
4. **Empty-runners diagnosis brief drafted + LOCKED** — `placings_empty_runners_diagnosis_brief.md` (99 lines, 10,180 bytes, sha256 `6bae8914`). Diagnosis-first probe with a **conditional** fix: §5.1 instrument the empty-runners signature; §5.2 volume-vs-rate diagnostic; §5.3 fork (pacing / retry / neither); §5.4 abandoned-meet guard; §7 bounded verification burn + ghost-tripwire re-run. Hard limits: no `race_date`/identity, no schema, two named files only, no full-backlog burn, no git write-ops. Operator locked it ("lock it").
5. **Code executed the brief out-of-session** (~13:10–13:55 ACST) → `placings_empty_runners_diagnosis_report.md` (Status: EXECUTED; **fork resolved to §5.3 branch 3 — no behavioural change**, one instrumentation-only edit). **HEADLINE:** the empty-runners mode is real and reproduced, but is **NOT** triggered by request rate, cumulative volume, provider tier, or time-of-day — a fetch-only client is immune at **~9.8 req/sec** (≈2× the 5/sec ceiling) across 8 sustained dates. It is triggered **specifically by the `sync_day` write path contending with the live collector on the shared `capture.db`** (throwaway-DB write is immune; artificial latency is immune); intermittent (~5-min window), resets within ~2s of write-idle. **No pacing config defeats it (branch 1 rejected); retry-defeatability not verifiable (branch 2 unsupported).** Reframes the follow-up from a rate-tier/provider question to an **architecture/operational-contention question** for operator triage. **NOT yet triaged — that is S213's first action.**
6. **Multi-agent (Cowork sub-agent) review — timing advice.** Nothing scheduled in-docs; governance reserves it for high-reversal-cost / high-blind-spot decisions, not routine work. Advised the natural trigger is the **pre-W16-cutover go/no-go**. Flagged the Cowork caveat (all-Claude sub-agents undercut the deliberate cross-model-family diversity) and the prep cost (refresh the ~April doc suite + a collaborative `decision_under_review.md` session).

## Standing-instruction adherence
- Desktop Commander as default for all filesystem/process ops — honoured.
- DR-021 Adelaide timestamps throughout — honoured.
- Brief-drafting ritual (grounded anchors, universal spine, explicit-calls surfaced, operator lock before hand-off) — honoured.
- Permanent-delete boundary (Claude does not hard-delete; verify + hand commands to operator) — honoured.
- Code read-and-confirm gate provided in the hand-off prompt — honoured.

## Open items
Pointer to `current_state.md`. New this session:
- **Empty-runners = DB write-contention** (architecture/operational question). S213 triages the report → routes (accept intermittent write-degradation / serialise burn against the collector / other). The pacing-and-provider framing is retired by the finding.
- **sha256-not-git-blob** convention for the open-ritual drift-check — advice recorded, not yet actioned; future standing-instruction candidate.

Carried: full-backlog burn (still downstream of the empty-runners resolution, now reframed as contention not pacing); fault-B / `race_date` identity remediation (parked, tripwire clean); theracingapi.com rate-tier reply (pending — now largely moot given the finding); Cowork sub-agent review → pre-W16 cutover.

## Open items out
- Git uncommitted-drift (13 sessions) — CLOSED via `c7f71ab`.
- Stale `.close_out_backups/` prompts + `SESSION_9001` fixtures — CLOSED (operator-deleted).
- Brief git-blob "hash mismatch" — CLOSED (diagnosed benign, no content drift).
- Dated 1-Jul timer-shift check — CLOSED (timer at 05:30 ACST).

## Session close state
- Rebuild root clean; new artefacts `placings_empty_runners_diagnosis_brief.md` (LOCKED) + `_report.md` (EXECUTED, un-triaged), committed at close.
- `.close_out_backups/` → `SESSION_213_opening_prompt.md` only (after this close).
- `current_state.md` rotated to the S212 close; `v3_build_picture.md` untouched (no formal build stream moved — placings recovery is tracked in `current_state`); `standing_instructions.md` untouched (no instruction edits this session).

## Forward routing
**S213 first action = AUTO-TRIAGE `placings_empty_runners_diagnosis_report.md`** off the open ritual, **no confirmation gate** (HOLD only if somehow absent — it is present). Triage against the locked brief's §7/§8/§9; digest the DB-write-contention headline; route the architecture/contention question; then take stock with the operator on whether placings recovery stays worth chasing. **Confirmed with operator** ("close with auto triage in 213").
