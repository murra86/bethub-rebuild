# Session 207 — fragment-floor report triaged + accepted; both §10 decisions resolved; Brief 2 confirmed unblocked → next priority

**Opened:** 2026-06-30 12:17 ACST (runner fast-path open)
**Closed:** 2026-06-30 13:24 ACST
**Tool routing:** Chat throughout (triage, operator decisions, governance, data verification). No Code commissioned. Read-only VPS `capture.db` + source reads (`mode=ro`, never copied). Brief 2 drafting routed forward to S208 (Chat brief-drafting → Code execution).
**Governing DRs invoked:** DR-021 (Adelaide anchors), DR-033 (placings analytical / settlement Betfair-only), DR-034 (canonical race-identity model, locked S206).

---

## Anchor

- Open (runner): `2026-06-30 12:17 ACST` — fast-path, runner result `SESSION_207_opening_prompt_result.md` (ran 12:17:33).
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-06-30 13:24 ACST`.

Same-workday continuation of S206 (closed 12:10 ACST). ~1h active. No split trigger fired (well under 3h, no day-rollover, clean scope).

## Pre-flight checks

Runner fast-path presented a FRESH open result (run stamp 12:17 > S206 close 12:10, session number matched) and was surfaced straight per Step 0. Drift-check (in the runner result) was clean: `current_state.md` last-updated == 12:10; `SESSION_206.md` present + non-empty; `v3_build_picture.md` updated at the S206 close. `.close_out_backups/` held only `SESSION_207_opening_prompt.md`. No phantom files. Close-side pre-flight directory listing also clean — no `STATUS.md`/`CLAUDE.md`/`system_snapshot.md`.

## Session shape

A runner-opened HOLD that released in-session. The Step-12 runner opened S207 at 12:17 as a HOLD — its gated first action (triage the fragment-floor report) couldn't run because `placings_deficit_fragment_floor_report.md` wasn't on disk at 12:17 (Code hadn't finished). On the operator's "triage please", a disk re-check found the report HAD landed at 12:23 (six minutes after the runner's open), so the hold released and the triage ran. The rest of the session was operator-facing decision resolution off the triage, plus two read-only data checks (the VPS fetch-rate config and recent `capture.db` testability for the manual bet-log feature). No build, no Code commissioned, bet-safe throughout.

## What was delivered

1. **Fragment-floor report TRIAGED + ACCEPTED.** `placings_deficit_fragment_floor_report.md` (302 lines) triaged against the locked brief. Meets the contract: RECONCILES (market-stamped 104 ghost + 34,338 genuine = 34,442; no-market [7–707] ghost + [7,184–6,484] genuine = 7,191; grand total 41,633 = §5.2 baseline), stays in scope (read-only `mode=ro`, no copy/fix/schema/git), grounds schema before measuring, returns a clear §5.5 verdict. Arithmetic internally consistent throughout. No edits needed.

2. **Headline + the load-bearing caveat.** Of the 41,633 recoverable deficit: GHOST (un-fillable, resulted on a sibling fragment) = **111–811 runners (0.3–1.9%)**, market-stamped portion precise at 104; GENUINE (recoverable) = **40,822–41,522 (98.1–99.7%)**. So the recoverable target barely needs correcting now. CAVEAT: the floor is small only because burn ≈0 (quota wall) — as results land, each newly-resulted fragment whose date-drifted sibling stays NULL flips genuine→ghost, so 111–811 is a **floor at this moment, not a ceiling**; the slope once burn starts is the number that matters (first look: 1 Jul).

3. **Mechanism PINNED (and it's not what was hypothesised).** The ghost is a **±1-day `race_date`-drifted sibling** under the same Betfair WIN market id, with the result on the `subscription` fragment and the `betfair_only` sibling left NULL — a `results_source` split, NOT the `S:`/`N:` runner-key collision the brief hypothesised (both siblings use `N:` keys). Reshapes any future collapse brief: the merge key is date-drift-within-market-id, not key-form. The 9 market-stamped ghost groups are essentially two meetings (Swan Hill 06-06/-07, Gatton 06-02/-03).

4. **§10 decision (a) — stall-alert threshold: NO correction now. CONFIRMED.** The ghost correction is <0.3% precise / <1.9% worst-case — inside the noise. Hold the threshold; re-measure the floor after the first material burn and watch the slope. Paired with the 1 Jul daily check (run the burndown check + a ghost re-measure together).

5. **§10 decision (b) — DR-034 stance-4 collapse remediation: PARKED. CONFIRMED.** The live bottleneck is the quota wall (98%+ un-run), not ghosts (≤2%). Framing CORRECTED with the operator: the "proper" ghost-fix is **downstream of restarting burn, not a blocker to it** — the machine clears the fillable pile fine without it; the fix only earns its place because ghosts accumulate during burn and never self-clear. Sequence: confirm rate tier → let burn run → re-measure floor slope → then draft the stance-4 brief (Chat→Code) **if** the slope warrants. Mechanism is known (merge date-drifted siblings sharing a Betfair market id).

6. **Fetch-rate finding (read-only VPS source check).** Per-request pacing is already `BACKLOG_MIN_DELAY = 1.5`s in `scripts/backfill_race_metadata.py` — slower than the free-tier 1/sec — so the operator's "set it to 1/sec for now" is already satisfied; nothing to change there. The real throughput limiter is the **per-night attempt ceiling `BACKLOG_MAX_ATTEMPTS = 20`**: with ~90 backlog dates that's several nights minimum even running clean. Flagged to assess at the 1 Jul burn; if it's the choke, lifting it is a small Code job. Material note: even a 5/sec confirmation wouldn't fully open throughput without also lifting the nightly cap.

7. **Racing-API rate tier — operator already emailed.** Operator confirmed they had already emailed `support@theracingapi.com` to ask whether the AU add-on lifts the rate to 5/sec or leaves them at free-tier 1/sec. Awaiting reply; fold the answer into `BETHUB_DATA_REFERENCE.md` §G when it lands. (A drafted email was offered and then scrapped as redundant.)

8. **Brief 2 CONFIRMED UNBLOCKED → next priority.** `vps_client_api_rewrite_brief.md` (the Mac client lookup-trio + results rewrite + three launcher fixes — the launcher capture-data provisioning that makes Log Past Bet work for past races) was HELD + GATED behind the §B identity decision; that gate is DR-034, LOCKED at S206. So Brief 2 is unblocked, independent of the Racing-API reply and the overnight burn; it runs out-of-session (Chat drafts → Code executes). Confirmed as the next project-level priority. NOTE: a pre-DR-034 `vps_client_api_rewrite_brief.md` already exists at root — S208 re-drafts/re-locks it against the locked DR-034 identity model.

9. **Recent `capture.db` verified testable for the manual bet-log feature** (read-only `mode=ro`, last 12 days). Every recent day carries races with Betfair selection ids (the lookup's requirement). Best full-result test days (selection ids + finishing positions both present): **20 Jun** (1,378/1,399 fin), **27 Jun** (1,117/1,159 fin), **28 Jun** (625/633 fin). Finish-position gaps on 19/21/22/23/24 Jun are the deficit-in-recovery — those races are findable + linkable (win/lose-testable) but place results pending burn. CAVEAT surfaced to operator: the live-app test requires Brief 2 first (the app can't look up past races yet — that's exactly what Brief 2 builds), so the data being healthy means the test is real the moment Brief 2 ships.

## Standing-instruction adherence check

- **DR-021 anchors** — open 12:17 (runner) + close 13:24. ✓
- **Tool routing stated explicitly (Cat 1)** — Chat vs Code named on every routing point (triage = Chat; Brief 2 = Chat-draft→Code; floor re-measure = Code; rate-tier = operator-side; stance-4 brief if-needed = Chat→Code). ✓
- **DB reads (other instructions)** — `start_process` Python, `mode=ro`, never copied; both the VPS source grep and the `capture.db` testability query were read-only in place. ✓
- **Surface operator-relevant decisions only; handle technical detail autonomously** — the two §10 decisions framed for the operator's call; reconciliation arithmetic / mechanism detail handled inside the triage. ✓
- **Plain-language for operator** — delivered "dumb-person-speak" explanations on request without drift in the underlying facts. ✓
- **Brief drafting** — not exercised this session (Brief 2 deferred to S208); no brief drafted, so no brief-drafting-skill discipline invoked here.
- **Standing-instruction sweep** — no standing instruction authored or edited this session → close Step 7 skipped.

## Open items

Pointer-only — full list in `current_state.md`. New/changed this session:

- **Brief 2 — UNBLOCKED, now the next priority** (was: held + gated behind §B). S208 re-drafts/re-locks `vps_client_api_rewrite_brief.md` against DR-034.
- **Stall-alert threshold** — no ghost correction now; re-measure floor after first material burn (pair with 1 Jul daily check).
- **DR-034 stance-4 collapse remediation** — PARKED; downstream of burn, not a blocker. Revisit trigger: after first material burn, re-measure the floor (Code re-run of the fragment-floor measurement); if the slope is material, draft the stance-4 brief (Chat→Code). Mechanism known (merge date-drifted siblings sharing a Betfair market id).
- **Nightly throughput cap** — `BACKLOG_MAX_ATTEMPTS = 20` flagged as the likely real burn-rate limiter; assess at 1 Jul, lift via small Code job if it's the choke.

## Open items out (closed this session)

- Fragment-floor report triage (the S207 gated auto-action) — DONE + ACCEPTED. ✅
- §10 decision (a) stall-alert threshold — RESOLVED (no correction now). ✅
- §10 decision (b) fragment-collapse remediation — RESOLVED (parked, downstream-of-burn). ✅
- Brief 2 blocked-status — RESOLVED (unblocked; DR-034 locked). ✅
- Manual bet-log recent-data question — ANSWERED (recent data present + testable). ✅

## Session close state

- Rebuild folder root: clean, no phantom files. `SESSION_207.md` written. `current_state.md` rotated to the 13:24 close. `v3_build_picture.md` updated (W17 stream next-milestone advanced; "Last updated" → 13:24).
- WIP: none in flight.
- `.close_out_backups/`: `SESSION_208_opening_prompt.md` staged (S207's consumed prompt swept).
- `sessions/`: SESSION_207.md present.
- `standing_instructions.md`: untouched (no edits this session).
- Bet-safety: CLEAN — read-only analytical/governance only; no v3 / settlement / money-path / v2 touch.

## Forward routing — CONFIRMED WITH OPERATOR

**S208 first action (CONFIRMED): draft Brief 2** — re-draft/re-lock `vps_client_api_rewrite_brief.md` against the locked DR-034 identity model, via the brief-drafting skill, **held for operator review before lock** (not auto-committed). Operator confirmed "Yes" to closing S207 and opening S208 straight onto drafting Brief 2.

Then, in order: lock Brief 2 → Code executes out-of-session → test against recent `capture.db` (20/27/28 Jun) → cash-modal blank fix (small frontend, must-fix) → settlement-worker brief (IOU + manual-match-to-lay) → promo-seed → W16 cutover. The Data Foundation harvest (§A.4 → §C/§D/§E) sits parallel/ahead but does NOT gate Brief 2. Recovery monitoring continues (1 Jul first clean daily check + the 20/night-cap assessment); Racing-API rate-tier reply awaited.
