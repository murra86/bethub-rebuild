# Session 194 — consolidated frontend fix report auto-triaged CLEAN;
# cash-lay-modal stake-prefill must-fix + manual-match-to-lay
# requirement grounded and captured

**Opened:** 2026-06-26 13:37 ACST
**Closed:** 2026-06-26 15:06 ACST
**Tool routing:** Claude Chat (report triage + live-code grounding via
Desktop Commander reads against the bethub-v3 frontend + workflows). No
Code commissioned this session — the two items surfaced are captured for
future briefs, not executed.
**Governing DRs:** DR-021 (Adelaide time), DR-032 (the promo / free-bet
machinery the frontend brief used but did not modify), DR-033
(data-source roles — the deploy-before-settle / settlement-timing
context), DR-030 (module boundaries — frontend-only), DR-027/028
(operational/analytical boundary — untouched).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-26 13:37 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-26 15:06 ACST.
- ~1h29m wall-clock, same-workday. No split trigger (under ~3h, no
  day-rollover, no new DRs/amendments, no fatigue signal).

## Pre-flight checks (open ritual)

Clean open. `current_state.md`, `SESSION_193.md`, and
`v3_build_picture.md` all carried the matching 2026-06-26 00:50 ACST
S193-close stamp (no drift). Root folder clean (extra `.md` files all
live reference artefacts). `.close_out_backups/` held the expected
`SESSION_194_opening_prompt.md`. The `interface_triage/` listing settled
routing: `consolidated_frontend_fix_report.md` was present — the
operator ran the Code session between sessions — so the S194 primary
(auto-triage) was GO. Same-workday open (~13h after the past-midnight
S193 close); the build-picture table was rendered (overnight gap +
moved streams made it useful, not ritual noise).

## Session shape

A triage-then-grounding session, single clean arc. Auto-triaged Code's
`consolidated_frontend_fix_report.md` straight off the open (no gate,
per the standing pattern) — clean on every gate. The operator then
raised two questions off the triage notes, both grounded against the
live bethub-v3 code rather than answered from memory: (1) the
cash-lay-modal stake-prefill quirk, and (2) whether a free-bet leg
deployed-before-settle can be matched to its auto-captured Betfair lay.
Both resolved with the live code in hand; both captured into
`current_state.md` as forward items. No code touched in Chat; no Code
commissioned.

## What was delivered

1. **`consolidated_frontend_fix_report.md` — AUTO-TRIAGED CLEAN.** All
   seven S189-sweep fixes landed (sticky nav; odds-box "1"-acceptance +
   Delete-to-clear; the v2-mirrored Place Lay & Log rebuild; log-box
   drop-on-success; clean green success message; drop the redundant FB
   return-type selector; FB quick-amount buttons). The two load-bearing
   checks both pass: **§5.3(e) no-`cycle_id` rule HONOURED** — the
   free-bet handoff omits `cycle_id` entirely and a new regression test
   asserts `'cycle_id' in body === false`, so the server-side
   qualifier-cycle inheritance (`resolve_inherited_cycle`) is preserved;
   **§5.1 "freeze" = pinned, confirmed** — no lock-up in the nav (plain
   `<Link>`s, nothing that can hang), the symptom was a non-sticky
   header scrolling off, so the sticky fix is the right read. Bet-safety
   §9 preserved verbatim (liability soft-cap + tick-divergence confirm
   both still gate placement; their two tests pass). Frontend-only — no
   backend / schema / settlement touched. tsc clean; vitest 110→124
   (+14, 0 fail). Verdict: clean — but **implemented-not-live** until a
   build runs (Code did not rebuild the served `dist` bundle — same
   stale-bundle situation as S187), so the operator sees none of the
   seven fixes until `npm run build`.

2. **Cash-lay-modal stake-prefill quirk — GROUNDED + captured as a
   pre-cutover must-fix.** Report finding 3 flagged that the cash
   (non-free-bet) path passes the soft *price* into the modal's
   back-stake field. Grounded against `HedgeModal.tsx` + `Racing.tsx`:
   in cash mode `initialBackStake = manualOdds[selectionId]` (the soft
   price), which seeds the "back stake" box. Because the lay *size* is
   computed from the back stake, a cash lay placed without overwriting
   the box computes a wrong (too-small) lay size → under-hedge. **The
   lay *price* is NOT affected** — it is sourced live from Betfair best
   lay (`runner.best_lay[0].price`, polled ~500ms, operator-editable,
   tick-divergence fat-finger guard against the live price). So the
   feared "wrong lay price" is not the bug; the wrong *stake prefill*
   is. Free-bet mode (the operator's ~99%) is correct — the FB face
   value set on the race page carries through via `fbFaceValue` (§5.7).
   Fix: blank the cash-mode back-stake default (force entry). Small
   frontend brief; not the urgent "wrong price" risk, but make it before
   live cash lays.

3. **Deploy-before-settle manual-match-to-lay — GROUNDED + folded onto
   the settlement-worker piece.** Operator's scenario: deploy a free bet
   before it is credited in the tool (the tool auto-captures the Betfair
   lay), then log the soft-book free-bet leg via Log Past Bet once the
   FB is credited, and match it to that lay as one cycle. Grounded:
   `LogPastBet.tsx` + `createManualBet` carry NO `cycle_id` / link
   field, and the manual record-builder mints a standalone cycle when
   `cycle_id` is omitted. So there is **no one-operation match on the
   manual screen today** — confirming the S176 hedge-link gap is still
   open. The builder *does* accept a `cycle_id` (optional field) and the
   engine supports cycle-join (`resolve_inherited_cycle`), so this is a
   wiring/build item, not an architectural wall. Routing: the "match
   this logged leg to an existing Betfair lay" control belongs with the
   **settlement-worker brief** (same workflow as the IOU design).
   **Interim workaround, operator-agreed:** Claude hand-links the pair
   in burst review — read both records, confirm the match (account /
   book / runner / amounts), set the logged leg onto the lay's cycle,
   verify — fine at current free-bet volume.

4. **Both items captured in `current_state.md`.** The cash-modal fix is
   flagged as a must-fix above the pre-cutover queue (plain-English:
   cash path only, lay price unaffected). The manual-match requirement +
   burst-review interim are appended to the settlement-worker queue item.

## Standing-instruction adherence check

- **Cat 1 brevity / decision-maker framing** — held. Led with the call
  each turn; the triage digest led with the clean verdict; flagged the
  two groundings as deserving detail.
- **Cat 1 plain language / no jargon** — held. Both groundings explained
  in real-world terms (lay price vs stake prefill; "match the leg to the
  lay as one cycle"); code identifiers translated for the operator.
- **Cat 1 silent open/close ritual** — held at open (single combined
  brief, no step headers — the S193 drift did not recur). Close ran
  silent to this record + artefacts + opening prompt.
- **Cat 1 same-workday calibration** — held. Tight recap; build-picture
  table rendered (justified by the overnight gap + moved streams).
- **Cat 1 don't-surface-dev-lead-calls-by-default** — held. Surfaced the
  operationally-relevant items (must-build-before-live, the cash
  prefill, the manual-match capability, the empty-FB behaviour); held the
  lint / timing / input-refactor mechanics as Claude's.
- **Cat 3 empirical verification** — central this session. Both operator
  questions answered only after reading the live `HedgeModal.tsx`,
  `Racing.tsx`, `LogPastBet.tsx`, and `record_builder.py` — not from
  memory or the report's one-line findings.
- **Cat 3 create_file banned / verify writes** — held.
  `current_state.md` edits via Desktop Commander `edit_block`, both
  verified on the read-back; this record via `write_file`, verified at
  close.
- **Cat 5 make-the-call** — held. Made the software reads/calls; surfaced
  the operator-relevant decisions (fix priority, interim-workaround
  acceptance).
- **Bet-safety hard rule — CLEAN.** No code touched in Chat — report
  triage + read-only grounding only. The frontend brief was
  frontend-only by construction; the cash-modal and manual-match items
  are captured, not executed.

## Open items

Pointer-only — full detail in `current_state.md`.

**New / promoted for S195:**
- **Cash-modal back-stake blank** — pre-cutover must-fix (small
  frontend). Surfaced S194.
- **Manual-match-to-lay** — folded onto the settlement-worker brief;
  burst-review hand-link is the interim.

**Carried to S195:**
- Launcher capture-data provisioning (S195 primary).
- Settlement-worker brief (now carrying the IOU design + the
  manual-match-to-lay requirement).
- Promo-seed item.
- W16 cutover scoping.
- **Trickle progress check-up** — due `2026-06-28` (dated; surfaces on
  the open-items delta on/after that date).
- Parking-lot items (unchanged otherwise).

## Open items out (closed this session)

- **Triage `consolidated_frontend_fix_report.md` (S194 primary)** —
  DONE. Clean; seven fixes landed, both load-bearing checks pass
  (§5.3(e) no-`cycle_id`, §5.1 freeze = pinned), bet-safety preserved.
  Caveat: implemented-not-live until a build runs. ✅

## Session close state

- `sessions/SESSION_194.md` — this record.
- `current_state.md` — rotated to S194 outcomes; stamp 15:06. Cash-modal
  must-fix + manual-match requirement captured.
- `v3_build_picture.md` — interface-refinement row updated (frontend
  brief triaged clean; cash-modal must-fix + manual-match surfaced;
  must-build-before-live noted); header stamp 15:06.
- `standing_instructions.md` — untouched (no new instruction this
  session). KB re-upload still pending (carryover).
- `decisions.md` — untouched. KB re-upload still pending (carryover).
- `.close_out_backups/` — stale S194 prompt removed; S195 opening prompt
  written.

## Pending operator-side actions

- **Build the v3 frontend** (`npm run build`) so the seven fixes go
  live, then a quick live look: nav stays pinned scrolling BetLog /
  Accounts; on the next real partial-fill lay, confirm the "still
  unmatched" figure holds steady.
- **Re-upload `decisions.md`** to the bethub-rebuild Project KB (S191
  DR-029 + S180 DR-032 amendments; carryover).
- **Re-upload `standing_instructions.md`** to the Project KB (S189 §4
  live-integration rule; carryover).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** jump-start-only on request (to retirement).

## Forward routing (CONFIRMED with operator)

The operator said "Close up and let's continue next session," having
confirmed the launcher capture-data provisioning brief as the next pick.
S195 opens, then drafts the **launcher capture-data provisioning brief**
(the capture.db link + carried F9/F10/F12 + rebuild-if-source-newer).
The **cash-modal back-stake blank** is a flagged pre-cutover must-fix
(its own small frontend brief, sequenced at the operator's call). Queue
after: settlement-worker brief (carrying the IOU design + the
manual-match-to-lay requirement) → promo-seed item → W16 cutover. The
**trickle check-up (2026-06-28)** surfaces on whichever session opens
on/after that date. Between sessions the operator builds the frontend
and does the live look.
