# Session 198 — locked the placings-landing surgical fix brief
# (RC-2 guard then RC-1 fetch); captured two standing-instruction
# changes (opening-prompt auto-runner + bethub-v3 git hygiene);
# cleared the KB-reupload carryover. Code ran the brief
# out-of-session — report landed at close, freeze now OFF.

**Opened:** 2026-06-29 14:41 ACST
**Closed:** 2026-06-29 15:32 ACST
**Tool routing:** Claude Chat (open ritual; live-code grounding over
SSH; fix-brief drafting via the brief-drafting skill; two
standing-instruction edits; current_state KB-done marking; close
ritual). Code executed the locked brief out-of-session (15:01→15:31
ACST) — report triaged S199, not this session.
**Governing DRs:** DR-021 (Adelaide time); DR-033 (placings
analytical, settlement Betfair-only — the bet-safety ground);
DR-027/028 (capture-side boundary).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-29 14:41 ACST (Mon).
- Close: `TZ="Australia/Adelaide" date` → 2026-06-29 15:32 ACST (Mon).
- Same-workday open vs S197 (14:20 same day); ~51m active, no
  day-rollover, no split trigger — full close.

## Pre-flight checks (open ritual)

Clean drift-check: `current_state.md` carried the matching
2026-06-29 14:20 S197-close stamp; `SESSION_197.md` present +
non-empty; `v3_build_picture.md` correctly untouched at S197 close.
`.close_out_backups/` held only the live
`SESSION_198_opening_prompt.md`. SSH key WAS loaded this session
(unlike S197) → live-code grounding proceeded. Open ritual ran
clean — no Cat-1 step-header leak after the first two lines were
caught and corrected.

## Session shape

A single-thread drafting arc with two operator-initiated workflow
inserts. Auto-drafted the surgical fix brief straight off the open
(no gate, per S197 directive): grounded against the live VPS code,
surfaced the three-file scope finding, drafted section-by-section,
locked on operator OK, provided the Code prompt. Then the operator
delivered two out-of-session workflow changes (git housekeeping +
opening-prompt auto-runner) which were captured into
`standing_instructions.md`, and confirmed the KB re-uploads done.
Code ran the brief out-of-session during the session; its report
landed on disk by close.

## What was delivered

1. **Locked `placings_landing_fix_brief.md`** (330 lines, sha
   `c8c319b97a55`, §1–§13). Surgical two-part fix to the
   capture-side placings sync, grounded against the live VPS tree
   this session:
   - **Three-file scope finding** (grounding correction): the fix
     spans `subscription/racing_api.py` (the fetch path, clean
     tree), `storage/database.py` (the write path, dirty), and
     `scripts/backfill_race_metadata.py` (the oldest-first walk +
     strike logic + Phase-0 freeze flag, dirty) — not the two files
     the S197 close named. The walk/strike/freeze logic lives in a
     third file.
   - **Part A first (RC-2 guard):** match a result-write to the
     horse by identity (punctuation/whitespace-robust name), never
     the bare saddlecloth number; never overwrite a
     differently-named incumbent. Hard stop if the guard doesn't
     verify clean before Part B.
   - **Part B (RC-1 fetch):** classify quota-truncated/positionless
     fetches as transient (no strike); stop the early-March residue
     starving the per-night budget so the recoverable tail
     (2026-03-15→) gets a fetch. Flip `BACKLOG_FREEZE_RETIRE` to
     `False` as the last edit.
   - No schema change. Dirty-tree discipline (no git ops, named
     anchors only, `git diff` per edit). Ready-to-paste Code prompt
     provided at hand-off.

2. **Two standing-instruction changes captured into
   `standing_instructions.md`** (now 172 lines), from the operator's
   out-of-session report:
   - **Cat 2 amendment — opening prompts are now auto-consumed.**
     The opening prompt written to `.close_out_backups/` is
     auto-detected and executed by a headless `claude` runner
     (runs the open ritual + the defined first action, honouring a
     `hold` / no-gate marker, then notifies the operator). The close
     must now define the next session's first action explicitly,
     including auto-execute vs hold, and guard it if it depends on a
     maybe-absent artefact. Supersedes the manual-paste step.
   - **Cat 3 addition — bethub-v3 git hygiene.** The bethub-v3 Mac
     repo had no committer identity (commits silently failing; ~7
     weeks / 241 files uncommitted since 5 May). Now fixed: identity
     set, baseline checkpoint `7c4482b` on `main`, tree clean.
     Going forward: dirty-tree-clean check is meaningful again;
     commit after substantive work / after v3-targeting Code briefs;
     GitHub off-machine backup is the one open gap. Scope boundary
     written in: this is the bethub-v3 Mac repo, NOT the
     racing-data-capture VPS repo (whose dirty tree is expected).

3. **Cleared the KB-reupload carryover.** `standing_instructions.md`
   (incl. this session's edits) and `decisions.md` confirmed current
   in the Project KB by the operator; `current_state.md` pending
   actions marked done (✅) and the stale "re-upload pending" note
   removed from the required-reads list.

4. **Code executed the locked brief out-of-session (15:01→15:31
   ACST)** — `placings_landing_fix_report.md` (135 lines) landed on
   disk by close. NOT triaged this session (routed to S199 per
   operator). Headline (un-triaged, from the report header): both
   parts landed + verified, one in-scope finding (F-1), and
   `BACKLOG_FREEZE_RETIRE` flipped to `False` — **the placings clock
   is now running again.** Full triage is S199's job.

## Standing-instruction adherence check

- **Cat 1 silent open ritual** — held this time (the first two lines
  leaked step-framing language and were corrected immediately; the
  rest of the open and the whole close ran clean). Watch continues.
- **Cat 1 same-workday calibration** — held (tight recap; S197 close
  was same calendar day).
- **Cat 1 auto-draft no-gate** — held (drafted the fix brief straight
  off the open, no confirmation gate, per the S197 directive).
- **Cat 1 brevity / decision-maker framing** — held; surfaced the
  three-file scope finding and the prove-then-recover split as the
  operator-relevant calls, kept dev-lead detail in the brief.
- **Cat 5 make-the-call** — held (guard-before-fetch, the name-match
  rule, the additive sync-return signal — all made inside the brief,
  only the operational-consequence ones surfaced).
- **Cat 2 always provide the Code prompt at hand-off** — held.
- **Cat 3 empirical verification before governance edits** — held
  (re-read `standing_instructions.md` and `current_state.md` regions
  live before each edit).
- **Cat 3 create_file banned / verify writes** — held (brief +
  record + edits via Desktop Commander; brief verified
  `wc`/`shasum` = 330 lines, sha `c8c319b97a55`).
- **Cat 3 live code grounding (SSH) / DB read-only** — held (SSH key
  loaded; grounding reads only; no DB copy).
- **Brief-drafting skill** — followed end to end (job named,
  pre-flight grounding incl. dirty-tree check, surgical shape,
  surfaced calls, locked on OK, prompt provided).
- **Cat 2 NEW auto-runner rule (this session)** — exercised at this
  close: the S199 opening prompt defines the first action explicitly
  and guards it ("triage if present, else hold").
- **Bet-safety hard rule — CLEAN.** Analytical/capture-side only; no
  v3 / settlement / money path; no code touched in Chat (the brief
  commissions Code; Code's edits were capture-side, DR-033).

## Open items

Pointer-only — full detail in `current_state.md`.

**New / changed this session:**
- **Fix brief LOCKED and EXECUTED.** Code's
  `placings_landing_fix_report.md` is on disk, un-triaged → S199's
  first action.
- **Placings clock RUNNING again** — `BACKLOG_FREEZE_RETIRE=False`
  (flipped by Code as the fix's last edit). The S197 clock-stop is
  lifted.
- **Two standing instructions added** (Cat 2 auto-runner, Cat 3
  bethub-v3 git). Skill-review trigger: Cat 2 changed → review
  `bethub-session-open` / `bethub-session-close` at next open (the
  close skill's Step 8 still says "paste into a fresh chat").
- **NEW open item: GitHub off-machine backup of bethub-v3** (private
  push, pending operator login) — the one current backup gap.

**Carried to S199:**
- **Triage `placings_landing_fix_report.md`** (first action) → if
  clean, commission the **recovery run** (the "start data recovery"
  milestone). F-1 finding to read.
- Launcher capture-data provisioning.
- Cash-modal back-stake blank — pre-cutover must-fix.
- Settlement-worker brief (IOU + manual-match-to-lay).
- Promo-seed item (also unblocks race-page promo buttons).
- W16 cutover scoping.
- Parking-lot items (unchanged).

**Closed / done this session:**
- Surgical fix brief drafted + locked. ✅
- KB re-upload carryover (standing_instructions.md + decisions.md)
  — DONE. ✅
- Two workflow changes captured to standing_instructions.md. ✅

**Carry-forward sensitivity flags:**
- **Bet-safety — CLEAN** (this session and Code's run).
- **Placings clock is now LIVE** — S199 triage should confirm the
  freeze-flip was correct and that struck dates self-clear cleanly.
- **capture.db / DB reads read-only** (mode=ro, never copy).
- **v2 is never modified.**
- **`.git` / `.gitignore` now present at the rebuild folder root** —
  the governance folder appears to have been put under version
  control out-of-session (consistent with the git-housekeeping
  theme). Benign; noted for awareness, not drift.

## Session close state

- `sessions/SESSION_198.md` — this record.
- `current_state.md` — rotated to S198 outcomes; stamp
  2026-06-29 15:32.
- `v3_build_picture.md` — **untouched** (no v3 build stream moved;
  the placings work is capture-side analytical, not a tracked build
  stream — same reasoning as S196/S197).
- `standing_instructions.md` — **edited** (172 lines): Cat 2
  auto-runner amendment + Cat 3 bethub-v3 git-hygiene rule.
  KB copy is current (operator re-uploaded this session).
- `decisions.md` — untouched; KB copy current (operator re-uploaded
  this session).
- `placings_landing_fix_brief.md` — NEW, LOCKED (sha `c8c319b97a55`,
  330 lines); released + consumed by Code.
- `placings_landing_fix_report.md` — NEW (Code output, 135 lines);
  on disk, **un-triaged** → S199.
- `.close_out_backups/` — consumed `SESSION_198` prompt swept;
  `SESSION_199_opening_prompt.md` written.

## Pending operator-side actions

**Between S198 → S199:**
- **None blocking.** The S199 first action (triage) is auto-runner
  driven; the report is already present.
- **GitHub off-machine backup of bethub-v3** — private push, pending
  operator login (open gap).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** running; jump-start-only to retirement.

## Forward routing (CONFIRMED with operator)

**S199 first action: triage `placings_landing_fix_report.md`**
(operator: "First action is triage report"). The report is already
on disk (Code ran during S198), so the auto-runner will resolve the
guarded first action to triage immediately.

Triage shape: read the report + its F-1 finding; confirm both fixes
verified clean, confirm the freeze-flip
(`BACKLOG_FREEZE_RETIRE=False`) was correct and that struck dates
self-clear; then — **if clean — commission the recovery run** (the
operator's "start the data recovery" milestone), which is the next
brief. If the report shows the guard did not verify clean, re-scope
the guard before any recovery.

Skill-review note carried into the opening prompt: Cat 2 changed
this session (auto-runner), so `bethub-session-open` /
`bethub-session-close` get a review at S199 open.
