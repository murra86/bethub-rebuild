# Placings not landing — diagnosis + clock-stop (Code brief)

**Status:** LOCKED 2026-06-29 (Session 197). Contract — Code
executes as written; surprises become findings, not edits.
**Drafted:** 2026-06-29 (Session 197), Adelaide local (DR-021).
**Routes to:** out-of-session Claude Code, single bounded session.
**Builds on:** `placings_trickle_fix_report.md` findings F1–F4.

---

## §0 — Baseline gate (hard STOP if not met)

Confirm BEFORE any edit. If any check fails, STOP and report —
do not proceed.

| Check | Required | |
|---|---|---|
| SSH | `ssh racing-vps -o ClearAllForwardings=yes` reaches host | |
| Repo / HEAD | `/home/racing/racing-data-capture`, `master`, HEAD `5f71488` | |
| Anchor state | `scripts/backfill_race_metadata.py` = `M` (dirty, trickle code present) | |
| Sidecar | `data/backlog_trickle_state.json` present; record its current strike counts verbatim before touching anything | |

Substrate must match what this brief is grounded on (the
2026-06-28 fix report). If HEAD moved or the anchor is clean,
STOP — the ground shifted.

---

## §1 — What this brief is and is not

**Is:** (a) a *clock-stop* — one small guarded edit so the
now-unjammed trickle cannot retire recoverable dates while the
real bug is open; (b) a *read-only diagnosis* that isolates why
recoverable placings the Racing API holds are not landing in
capture.db.

**Is not:** the fix. No edit to the sync/write path this session.
Code isolates the bug and writes the exact proposed fix into the
report; operator-Claude commissions that surgical fix next session.

Single bounded Code session. Surprises become findings in the
report, not chased and not escalated mid-session. Remediation
routes to operator-Claude triage, never into this report as an
applied change.

## §2 — Why this work exists

The 2026-06-28 trickle fix unjammed the backlog walk exactly to
spec — and in doing so exposed a bigger blocker (report F1): the
Racing API returns real finishing positions, but `sync_day()` is
not persisting them. On 2026-03-15 the API held 589 positioned
runners; capture.db held 263; the live pass wrote 0 new. The race
row's metadata is touched but the result-bearing runners never
reconcile onto it — an identity mismatch upstream of the
(correct) `upsert_runner`.

The clock (report F2): because blocked dates *look* resultless
(clean API, races answered, zero fills land), the new
strike-on-merit logic now strikes them. The live pass left
~20 dates at strike 1 of 5; at one strike per night they retire
in ~4 nights and drop from the selector — wrongly, since they are
recoverable. The nightly timer fires 23:30 ACST. Hence Phase 0
(clock-stop) runs first and is the time-critical half.

Bet-safety: analytical / capture-side only (DR-033 — placings
analytical, settlement Betfair-only). No v3, no settlement, no
money-path, no Betfair/scraper contact. Clean by construction.

## §3 — Pre-reads

Required, in order:
1. This brief.
2. `placings_trickle_fix_report.md` (F1–F4 + the §5 readout).

Reference-only (read on demand, not required):
- `placings_trickle_fix_brief.md` — the prior contract (anchors,
  no-touch list).
- `placings_trickle_report.md` — original trickle build history.

## §4 — System access

- **VPS** via `ssh racing-vps -o ClearAllForwardings=yes`
  (operator ssh-agent), repo `/home/racing/racing-data-capture`.
- **capture.db** `mode=ro` for all reads; never copy the file.
- **Racing API** read-only GETs only (re-probe the reproduction
  meets); respect existing delay/rate discipline (`>= 1.5s`,
  single-threaded).
- **Read-write: exactly ONE anchor** —
  `scripts/backfill_race_metadata.py` (already `M`), Phase-0 guard
  only (§5). Every other file is READ-ONLY this session, the sync
  path included.
- Adelaide local timestamps (ACST) in the report (DR-021).

---

## §5 — Phase 0: stop the clock (the one read-write change)

**Goal:** guarantee no recoverable date is retired / dropped from
the backlog selector while F1 is open. Minimal, named-anchor,
reversible.

**Anchor:** `scripts/backfill_race_metadata.py`, the
strike/retire region inside `run_backlog_pass()` (and the
`BACKLOG_EXHAUST_AFTER` constant region ~L106–108). Confirm exact
lines at the gate.

**The change — preferred shape (Code's call if a cleaner
named-anchor variant exists):** add a `BACKLOG_FREEZE_RETIRE`
guard (default ON for now) that makes the *retire / mark-exhausted*
step a no-op — dates may still accrue strike counts, but no date
is ever marked exhausted or removed from the selector while the
guard is on. This keeps the trickle otherwise running, so the
moment the F1 fix lands and placings start landing, struck dates
self-clear with no further deploy.

**Explicitly NOT this:** do not clear or rewrite the sidecar's
existing strike counts; do not disable the backlog pass wholesale;
do not touch `sync_day()` or the recent-window pass. Leave the
honest strike-1 signal intact — it is the F2 evidence.

**Phase-0 verification (capture both states in the report):**
- Show the guard's diff (`git diff scripts/backfill_race_metadata.py`
  for this region only).
- Run one backlog pass and show that for the struck dates the log
  now reads strike-accrued-but-not-retired, `retired=[]`, and the
  selector count does not fall by retirement.
- Confirm the sidecar's pre-existing strike counts are unchanged
  except for the honest +1 from the pass itself.

## §6 — Phase 1: isolate why placings don't land (read-only)

The question to answer with evidence, not inference: **for a
known-recoverable race, trace the API's positioned runners through
the sync path and identify the exact point they fail to reconcile
onto the DB race row.**

**§6.1 — Reproduction set (probe all three; read-only):**
- **Single-meet, recoverable** (the clean case — isolates the
  broad bug from meet-ID duplication): pick a 2026-03-15 venue the
  API returned exactly once, with positions present.
- **Dubbo 2026-03-15** — the report's worked case: API meet
  `met_aus_626943265490` (course "Dubbo"), R1 has number 1
  "I'm A Beaut" `position='1'`; DB "Dubbo R1" `race_id=179226`
  (same `subscription_meet_id`, synced 11:48) holds different
  runners (`N:2…N:10`, no `N:1`, all `finish_position` NULL).
- **Duplicate-meet** (isolates F3's contribution): a 2026-03-15
  venue the API returned twice (e.g. `bet365 Swan Hill`, `Grafton`)
  — one populated meet_id, one empty.

**§6.2 — The trace (per reproduction race):**
1. **Race identity** — how does the sync resolve an API meet +
   race number to a `race_id`? Capture the `subscription_meet_id`
   → `race_id` mapping for the reproduction race, and whether more
   than one DB race row shares that `subscription_meet_id`.
2. **Runner identity** — how is `runner_key` derived for an API
   runner? Compare the API payload's runner_keys for the positioned
   runners against the runner_keys actually present on the DB race
   row. Are they the same namespace? (Report shows API `N:1`
   present, DB row missing `N:1` and holding a different set.)
3. **Where it diverges** — is the DB race row populated from a
   *different* source/path (live-capture vs backfill) under keys
   that never collide with the API backfill payload's keys? This
   echoes the §2.1 Fix-5 venue/key normalisation drift — name it
   if it is the same class of bug.
4. **Does the write even attempt?** — does `_sync_single_race`
   reach `upsert_runner` for the positioned runners, or
   short-circuit earlier (0 matched, skip)? Report F4 notes
   per-runner exceptions are swallowed at `logger.debug` — so run
   the path under elevated logging OR a throwaway read-only probe
   harness (see §6.3) to see the per-runner matching outcome.

**§6.3 — Instrumentation rule.** To observe the matching, Code may
run a **standalone, read-only diagnostic harness** (a scratch
script under `/tmp`, not committed) that imports and exercises the
sync functions against the reproduction payloads with full logging,
OR run the existing path at DEBUG. Code must NOT modify
`subscription/racing_api.py`, `storage/database.py`, or any sync
function to add logging in place. Observe without altering
behaviour.

---

## §7 — Sequencing within session

1. **§0 baseline gate** — pass or STOP.
2. **Phase 0 (§5) FIRST** — stop the clock. It is time-critical
   (23:30 ACST timer). Land it, verify it, before any
   investigation. If Phase 0 cannot be landed cleanly, STOP and
   report — do not start Phase 1 with the clock still running.
3. **Phase 1 (§6)** — the read-only diagnosis.
4. **Write the report (§9).**

If the session runs short on budget, Phase 0 done + a partial but
coherent Phase 1 is the correct stop (clock is safe, diagnosis
continues next commission). Partial-but-coherent beats
complete-but-lost. Say so in the report self-assessment.

## §8 — Empirical verification

- **Phase 0:** the three checks in §5 (guard diff; one pass shows
  no retirement; sidecar counts honest).
- **Phase 1:** for each reproduction race, the report shows the
  API positioned-runner set, the DB race-row runner set, the
  `subscription_meet_id` → `race_id` mapping, and the precise
  point of divergence — with the evidence (payload excerpts, query
  outputs), not assertion.

## §9 — Output spec

Single file: `placings_landing_diagnosis_report.md` (rebuild root).

Sections:
1. Run header (SSH gate, HEAD, anchor state, capture.db size,
   sidecar before/after, VPS wall-clock, timestamps).
2. §0 baseline gate result.
3. Phase 0 — the guard: diff, verification, sidecar state.
4. Phase 1 — the trace, per reproduction race (the §6.2 four
   points each), with evidence.
5. **Root cause** — the single named mechanism (or the smallest
   set of candidates if not fully isolable read-only), stated
   plainly.
6. **Proposed fix** — the exact surgical change the next brief
   should commission: named file(s), named function(s)/region(s),
   the nature of the change, and any schema implication. This is
   the load-bearing deliverable — it is what lets the next session
   lock a surgical fix with no guesswork.
7. Findings (any further surprises; report-only).
8. Self-assessment (what was/wasn't isolable read-only, and why).

Length: ~120–200 lines. Range, not a hard line — overshoot if the
trace needs it, flag if so.

**Does NOT contain:** any applied sync-path fix; any recovery run;
any schema change; recommendations beyond the single §6 proposed
fix; an overall "verdict" beyond the root cause.

## §10 — Hard limits (non-negotiable)

- **One read-write anchor only:** the Phase-0 guard in
  `scripts/backfill_race_metadata.py`. Everything else READ-ONLY,
  the sync path included.
- **Do NOT edit** `sync_day`, `_sync_single_race`,
  `_sync_single_runner`, `upsert_runner`, `subscription/racing_api.py`,
  `storage/database.py`, the recent-window pass, the schema, or
  `main()` wiring. Diagnose them; do not change them.
- **Do NOT** run a recovery/backfill of placings this session, and
  do NOT clear or rewrite the sidecar's existing strikes.
- **Dirty-tree discipline:** no `git add/commit/stash/restore/
  checkout/reset`. Read working tree at start; edit only the named
  anchor; `git diff` after the edit; `git status` at close to
  confirm the dirty list is unchanged but for the (already-`M`)
  anchor.
- **Bet-safety:** analytical/capture-side only (DR-033). No v3,
  settlement, auto-settle, money-path, Betfair, or scraper contact.
- **No mid-session operator escalation.** Run end-to-end; surface
  in the report.
- **Single bounded session.** Doesn't fit → finding, not
  continuation.

## §11 — What happens after Code's session

Next operator-Claude (Chat) session triages
`placings_landing_diagnosis_report.md`: confirm Phase 0 holds the
clock; read the root cause + proposed fix; then **draft + lock the
surgical sync-path fix brief** against the now-known anchor. The
recovery (actually backfilling the recoverable placings) kicks off
the moment that fix lands and is proven — that is the "start the
data recovery" milestone. Code does not write that next brief.

## §12 — Cross-references

- **Prior report:** `placings_trickle_fix_report.md` (F1 the
  blocker, F2 the clock, F3 meet-ID duplication, F4 swallowed
  exceptions).
- **Prior contract:** `placings_trickle_fix_brief.md`.
- **DRs:** DR-033 (placings analytical, settlement Betfair-only —
  the bet-safety ground); DR-027/028 (capture-side boundary);
  DR-021 (Adelaide timestamps).
- **Lineage:** the §2.1 race-data fit-for-purpose arc; the Fix-5
  venue/key normalisation drift is the candidate sibling of this
  identity mismatch.
