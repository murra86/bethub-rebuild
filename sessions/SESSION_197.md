# Session 197 — auto-triaged the trickle-fix report (clean, but it
# exposed the real blocker); commissioned + triaged a diagnosis;
# the placings clock is STOPPED and the surgical fix is scoped

**Opened:** 2026-06-29 12:59 ACST
**Closed:** 2026-06-29 14:20 ACST
**Tool routing:** Claude Chat (open ritual; auto-triage of
`placings_trickle_fix_report.md`; diagnosis-brief drafting via the
brief-drafting skill; triage of Code's diagnosis report). Code
executed the diagnosis brief out-of-session. No v3 / sync code
touched in Chat.
**Governing DRs:** DR-021 (Adelaide time); DR-033 (placings
analytical, settlement Betfair-only — the bet-safety ground);
DR-027/028 (capture-side boundary).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-29 12:59 ACST (Mon).
- Close: `TZ="Australia/Adelaide" date` → 2026-06-29 14:20 ACST (Mon).
- New-workday open vs S196 (Sun 21:09); ~1h20m active, no
  day-rollover, no split trigger — full close.

## Pre-flight checks (open ritual)

Clean drift-check: `current_state.md` carried the matching
2026-06-28 21:09 S196-close stamp; `SESSION_196.md` present +
non-empty; `v3_build_picture.md` correctly untouched at S196 close
(no stream moved). `.close_out_backups/` held only the live
`SESSION_197_opening_prompt.md` — no stale artefacts. The
`placings_trickle_fix_report.md` was present on disk → auto-triage
target ready.

## Session shape

A triage → commission → triage arc on a single thread (the
placings backlog recovery), no pivot. Auto-triaged the
S196-commissioned trickle fix straight off the open (per S196
directive, no gate); the fix was clean but exposed the real
blocker; drafted + locked a diagnosis brief; Code ran it
out-of-session; triaged the diagnosis back. Ended with the clock
stopped and the surgical fix fully scoped — but the fix itself
deferred to S198 (sensitive write-path, no rush now the clock's
stopped).

## What was delivered

1. **Auto-triaged `placings_trickle_fix_report.md`.** The S196
   trickle fix was faithful — built to spec, bet-safe, scope held,
   unjam mechanism proven (9/9 unit + 1 live pass). **But it
   exposed F1:** the Racing API holds the placings, yet `sync_day()`
   isn't persisting them (589 positioned on 2026-03-15; DB held
   263; pass wrote 0). And **F2 (time-sensitive):** the unjammed
   strike-on-merit logic would retire *recoverable* dates that only
   *look* resultless — ~20 dates at strike 1, ~4 nights to
   retirement. Fill-rate readout (operator requirement): 20.0%
   thoroughbred filled window-total since 2026-03-01; March
   actually **54.4%** (the prior 21% was a blended all-runner
   figure); the big unfilled chunk is **recoverable-but-blocked**,
   not abandoned.

2. **Drafted + locked `placings_landing_diagnosis_brief.md`**
   (281 lines, sha `c099d707`, 13 sections §0–§12). One Code
   session, two halves: **Phase 0** a clock-stop (one guarded edit
   so no recoverable date retires while the bug is open) +
   **Phase 1** a read-only diagnosis (trace a recoverable race
   through the sync path, isolate where placings fail to land). Fix
   explicitly deferred to a later surgical brief. Ready-to-paste
   Code prompt provided at hand-off.

3. **Triaged `placings_landing_diagnosis_report.md`** (Code,
   out-of-session, clean + complete).
   - **Phase 0 landed + triple-verified — clock STOPPED.**
     `BACKLOG_FREEZE_RETIRE=True` (two-line guard in the named
     anchor only); a live pass logged `retired=[]`, selector held
     at 99, sidecar honest +1, zero exhausted flags. Self-clears on
     the first real fill. (Recorded drift, not a failure: the
     2026-06-28 23:30 timer fired between sessions, advancing
     strikes 1→2 exactly as F2 predicted — making Phase 0 more
     urgent, not less.)
   - **Phase 1 — the single "identity mismatch" is TWO bugs.**
     **RC-1 (dominant):** the oldest-first walk burns the daily
     Racing-API budget on the near-done early-March dates (stuck
     forever on genuine ~8% residue), so the recoverable tail
     (03-15→) is reached only after budget is spent — comes back as
     empty runner payloads, `upsert_runner` never reached, date
     mis-classed resultless (strikes). For the majority (Townsville,
     Swan Hill) the runner keys already match the API perfectly —
     the only thing missing is a budgeted fetch reaching the writer.
     **RC-2 (narrower, corrupting):** where the Betfair/live-capture
     path pre-populated a row with a *different* field under the
     same `N:<number>` keys (Dubbo: 6/8 different horses), a
     successful sync would COALESCE-overwrite the wrong horse —
     latent only because RC-1 starves the payload.
   - **Proposed fix:** sequence **RC-2 (reconcile by horse
     identity, not saddlecloth number) before RC-1 (pace
     `sync_day`'s per-meet calls + class empty "Results" payloads as
     transient/no-strike + fix the starvation so the tail gets
     budget).** Schema: none. Flip the freeze off after it proves
     out → struck dates self-clear.
   - **Findings:** F-a (two bugs, not one — prior "identity
     mismatch" undercounts the dominant fetch failure); F-b
     (duplicate meet_ids collapse to one row — noise, not the
     blocker); F-c (`venue_normalised` drift is live — a hazard for
     any name-based RC-2 fix); F-d (RC-1's empty payloads partly
     *manufacture* the F2 clock, not just expose it).

## Standing-instruction adherence check

- **Cat 1 new-workday calibration** — held (longer recap delivered;
  new-workday vs S196 Sun close).
- **Cat 1 silent open ritual** — **PARTIAL MISS AGAIN.** Step
  headers ("Step 1 — Timestamp anchor (DR-021)", "Step 2 — Required
  reads in order") leaked into operator-facing text at the open —
  the same drift the S114 tightening targets, last tripped
  S193/195/196. The close ran clean (no step-header narration). Flag
  carried; next open watches for it. (Recorded, not a new
  instruction.)
- **Cat 1 auto-triage no-gate** — held (triaged the trickle-fix
  report straight off the open per the S196 directive).
- **Cat 1 brevity / decision-maker framing** — held; the two-bug
  diagnosis turn was justified-detail (corruption risk + sequencing
  call), led with the call.
- **Cat 5 make-the-call** — held. Made the diagnosis-brief shape +
  the RC-2-before-RC-1 sequencing calls; surfaced only the
  operator-relevant ones (deferral, self-clearing freeze,
  bet-safety), not the dev-lead detail (S163).
- **Cat 2 always provide the Code prompt at hand-off** — held
  (ready-to-paste prompt given with the locked diagnosis brief).
- **Cat 2 auto-draft directive → opening prompt** — held (S198
  auto-drafts the surgical fix brief on open, operator-confirmed
  no-gate this session).
- **Cat 3 create_file banned / verify writes** — held. Brief +
  record via Desktop Commander; brief verified (`wc`/`shasum`,
  281 lines, sha `c099d707`).
- **Cat 3 live DB reads mode=ro, never copy** — N/A in Chat
  (SSH-from-Chat key not loaded → surfaced to operator; Code did its
  reads `mode=ro`, never copied capture.db).
- **Brief-drafting skill** — followed: job named, pre-flight
  grounding attempted (SSH blocked → fell back to the fresh report's
  precise anchors), surgical two-phase shape, surfaced calls,
  provided the prompt.
- **Bet-safety hard rule — CLEAN.** Analytical/capture-side only; no
  v3 / settlement / money-path / Betfair-scraper; no code touched in
  Chat (the brief commissions Code; the one VPS edit was Code's
  two-line Phase-0 guard).

## Open items

Pointer-only — full detail in `current_state.md`.

**New / changed this session:**
- **Diagnosis done → surgical fix scoped.** Two bugs (RC-1
  dominant, RC-2 corrupting); fix sequenced RC-2→RC-1; no schema
  change. The fix brief is S198's auto-draft deliverable.
- **Placings clock STOPPED** (Phase 0 `BACKLOG_FREEZE_RETIRE=True`
  landed + verified). Recoverable dates safe; freeze flips off after
  the fix proves out; struck dates self-clear.
- **Daily trickle check-up cadence → SUPERSEDED.** The daily
  fill-rate/backlog watch is moot until the fix lands (the report is
  explicit: no climb until RC-1 is fixed). Re-validate at S198 —
  don't kick off the daily watch; the fix is the path.

**Carried to S198:**
- **Surgical sync-path fix brief — auto-draft on open** (RC-2 then
  RC-1). Then **recovery kicks off once the fix proves out** (the
  "start data recovery" milestone).
- Launcher capture-data provisioning (queued, after the fix arc).
- Cash-modal back-stake blank — pre-cutover must-fix.
- Settlement-worker brief (IOU design + manual-match-to-lay).
- Promo-seed item (also unblocks the race-page promo buttons).
- W16 cutover scoping.
- Parking-lot items (unchanged).

**Closed / done this session:**
- Auto-triage of `placings_trickle_fix_report.md` — DONE. ✅
- Diagnosis commissioned + triaged; clock stopped. The diagnosis
  brief's job is complete. ✅

**Carry-forward sensitivity flags:**
- **Bet-safety — CLEAN** (this session). **But the next (fix) brief
  is the SENSITIVE one** — it edits the live capture write-path
  (`sync_day`, `_sync_single_runner`, `storage/database.py`) with a
  real data-corruption risk (RC-2 COALESCE-overwrite). Ground
  against live code (needs SSH key loaded) and walk section-by-
  section. Flagged in the opening prompt.
- **F-c `venue_normalised` drift is live** — the RC-2 name-based
  reconciliation must strip punctuation / handle venue drift or the
  "same horse" cases false-miss.
- **capture.db / DB reads read-only** (mode=ro, never copy).
- **v2 is never modified.**
- **Cat 1 silent-open-ritual leak recurred** at this open — next
  open watches.

## Session close state

- `sessions/SESSION_197.md` — this record.
- `current_state.md` — rotated to S197 outcomes; stamp
  2026-06-29 14:20.
- `v3_build_picture.md` — **untouched** (no v3 build stream moved;
  the placings work is capture-side analytical, not a tracked build
  stream — same reasoning as S196).
- `standing_instructions.md` — untouched (no new/edited standing
  instruction; the clock-stop + diagnosis are session-state). KB
  re-upload still pending (carryover).
- `decisions.md` — untouched. KB re-upload still pending (carryover).
- `placings_landing_diagnosis_brief.md` — NEW, locked (sha
  `c099d707`), released + consumed by Code.
- `placings_landing_diagnosis_report.md` — NEW (Code output),
  triaged this session.
- `.close_out_backups/` — consumed `SESSION_197` prompt swept;
  `SESSION_198_opening_prompt.md` written.

## Pending operator-side actions

**Between S197 → S198:**
- **`ssh-add` the VPS key next session** so Chat can ground the fix
  brief against the live sync code (`subscription/racing_api.py`,
  `storage/database.py`). SSH-from-Chat failed this session (key not
  loaded).
- **Run the Code session** against the surgical fix brief once S198
  drafts + locks it (prompt will be provided).
- **Re-upload `decisions.md`** to the Project KB (S191/S180
  amendments; carryover).
- **Re-upload `standing_instructions.md`** to the Project KB (S189
  §4; carryover).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** running; jump-start-only to retirement.

## Forward routing (CONFIRMED with operator)

**S198 AUTO-DRAFTS the surgical sync-path fix brief straight off the
open ritual — NO confirmation gate** (operator directive this
session: "get the next session to start auto-drafting on open. No
confirmation from me required").

Draft shape (from the diagnosis report §6):
- **RC-2 guard first** — reconcile API runners by **horse
  identity**, not saddlecloth number, so recovering the tail can't
  COALESCE-overwrite cross-sourced (Betfair-path) rows.
  Punctuation/venue-drift-robust per F-c.
- **RC-1 fetch fix** — pace `sync_day`'s per-meet calls; class
  empty "Results" payloads as transient (no strike); fix the
  starvation so the recoverable tail gets live budget.
- **Schema: none.** Flip `BACKLOG_FREEZE_RETIRE=False` after the fix
  proves out → struck dates self-clear.

Disciplines for the draft: **ground against live code first** (SSH
key) before naming anchors; **walk section-by-section** (sensitive
write-path + real corruption risk — not a lock-on-sight brief);
bet-safety framing explicit (write-path, but capture-side
analytical, DR-033). Begin drafting on open without waiting for a
go; surface operator-relevant calls only. After lock, provide the
Code prompt; Code executes; **then recovery kicks off once the fix
proves out** — the operator's "start the data recovery" milestone.
