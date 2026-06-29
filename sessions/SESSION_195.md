# Session 195 — orientation + v2 jump-start; the `npm run build`
# confirmed LIVE (the S194 frontend caveat is CLEARED); launcher
# capture-data provisioning brief CARRIES to S196 unchanged (operator
# away for the weekend)

**Opened:** 2026-06-26 15:53 ACST
**Closed:** 2026-06-28 16:52 ACST
**Tool routing:** Claude Chat (orientation ritual + a v2 jump-start via
Desktop Commander `open` on `BetHub.app`). No Code commissioned; no
brief drafted; no v3 code touched.
**Governing DRs:** DR-021 (Adelaide time — re-anchored at close across a
multi-day span). No others invoked (no architectural work this session).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-26 15:53 ACST (Fri).
- Close: `TZ="Australia/Adelaide" date` → 2026-06-28 16:52 ACST (Sun).
- **Multi-day span** (~2 days wall-clock, Fri open → Sun close). Almost
  all of that is the operator being away for the weekend, not active
  session work — active work was ~minutes (orientation + the v2
  jump-start). Day-rollover split trigger technically fired, but there
  was no in-flight substantive work to defer (no brief was started), so
  a normal close applies; the span is noted here for the record.

## Pre-flight checks (open ritual)

Clean open, no drift. `current_state.md` carried the matching 2026-06-26
15:06 ACST S194-close stamp; `SESSION_194.md` present and non-empty;
`v3_build_picture.md` updated at S194 close (interface-refinement row).
Root folder clean (the extra `.md` files are all live reference
artefacts). `.close_out_backups/` held exactly the expected
`SESSION_195_opening_prompt.md`. Same-workday open (~47 min after the
S194 close), so a tight recap was delivered; the build-picture table was
NOT dumped (a 47-min same-workday gap = ritual noise, unlike the
overnight gap that justified rendering it at S194 open).

## Session shape

A near-orientation-only session with one operator action folded in. The
session opened Friday afternoon, ran the open ritual, surfaced the one
material between-sessions fact (the operator's `npm run build` had gone
through — see below), named the S195 objective (draft the launcher
capture-data provisioning brief) and the one open sequencing call
(cash-modal must-fix vs launcher brief first). Before any of that
substantive work began, the operator asked to jump-start v2 ("open v2
bethub asap"), which was done. The operator then went away for the
weekend and returned Sunday to close. No launcher brief was drafted; the
S195 primary carries to S196 unchanged.

## What was delivered

1. **The `npm run build` is CONFIRMED — the seven frontend fixes are now
   LIVE.** The operator ran `npm run build` in `bethub-v3/ui/web` between
   the S194 close and the S195 open; the terminal output pasted at open
   showed a clean build (`tsc -b && vite build`, 103 modules, new served
   bundle `index-DiScTfgm.js` 339.98 kB, built in 120ms). This **clears
   the S194 "implemented-not-live" caveat** on all seven S189-sweep
   fixes — they are now in the served bundle, not just on disk. The only
   remainder is a 30-second operator live-look (nav stays pinned
   scrolling BetLog/Accounts; on the next real partial-fill lay confirm
   the "still unmatched" figure holds steady) — a confirmation, not a
   blocker.

2. **v2 BetHub JUMP-STARTED (operator request).** On "open v2 bethub
   asap", launched `BetHub.app` via Desktop Commander `open`. Verified up:
   Flask listening on port 5000 (`.flaskenv` → `FLASK_RUN_PORT=5000`; a
   Python listener confirmed on `*:5000`), server responding (HTTP 404 on
   the bare `/` = alive, `/` simply isn't a route — not a connection
   failure). v2 is the live daily-driver per the jump-start-only-to-
   retirement standing rule; no v2 code was modified (launch only).

3. **No launcher brief drafted; S195 primary carries to S196.** The
   confirmed pick (draft the launcher capture-data provisioning brief)
   was not started — the operator jump-started v2 then was away for the
   weekend. It carries to S196 unchanged, alongside the same downstream
   queue.

## Standing-instruction adherence check

- **Cat 1 same-workday calibration** — held at open. Tight recap; the
  build-picture table was correctly NOT rendered (47-min same-workday
  gap = ritual noise).
- **Cat 1 silent open/close ritual** — PARTIAL MISS at open: step
  headers ("Step 1 — …", "Step 3 — …") leaked into operator-facing text
  during the open ritual, the same drift the S114 tightening targets and
  S193 last tripped. The single combined orientation brief at the end was
  clean. Close ran without step-header narration. Flag carried so the
  next open watches for it.
- **Cat 1 brevity / decision-maker framing** — held. Led with the
  build-is-live fact; one sequencing question, not a menu.
- **Cat 5 make-the-call** — held. The v2 jump-start was executed without
  punting; verification (port + HTTP) done before reporting up.
- **Cat 3 create_file banned / verify writes** — held. Records written
  via Desktop Commander; the close-out write-timeout (DC server hang) was
  surfaced immediately, not silently degraded, and re-verified on the
  server's return before re-writing (no partial file had landed).
- **Bet-safety hard rule — CLEAN.** No v3 code touched; no Code
  commissioned; v2 launch-only (no modification). The frontend fixes
  going live were the operator's own build, not a Chat action.

## Close-out note — DC server hang

First attempt to write this record (single ~120-line write) returned no
result after 4 min; a follow-up verification list also hung — the
Desktop Commander MCP server had gone unresponsive. Surfaced to the
operator with the project status they'd asked for (status does not depend
on the file tool). Operator restarted DC; on return, verified
`SESSION_195.md` had NOT landed (no partial), then re-wrote chunked.
No state corruption. Lesson reinforced: chunked writes + verify-on-return.

## Open items

Pointer-only — full detail in `current_state.md`.

**New / changed this session:**
- **Frontend fixes now LIVE** — the S194 implemented-not-live caveat is
  cleared (operator's `npm run build`). Only the operator live-look
  remains (confirmation, not a blocker).
- **v2 jump-started** — running on :5000 for the weekend's betting.

**Carried to S196 (unchanged):**
- Launcher capture-data provisioning brief (S196 primary — was S195's,
  not started).
- Cash-modal back-stake blank — pre-cutover must-fix (small frontend);
  sequencing still the operator's call.
- Settlement-worker brief (carrying the IOU design + manual-match-to-lay).
- Promo-seed item (also unblocks the race-page promo buttons).
- W16 cutover scoping.
- **Trickle progress check-up — NOW DUE** (`2026-06-28`, today). Claude-
  owned; reads the VPS log to confirm `remaining_backlog_dates` trending
  down. Surfaces first thing at the next open.
- Parking-lot items (unchanged).

## Open items out (closed this session)

- None formally closed. The S194 "build the frontend" pending
  operator-side action is effectively DONE (the fixes are live), leaving
  only the live-look.

## Session close state

- `sessions/SESSION_195.md` — this record.
- `current_state.md` — rotated to S195 outcomes; stamp 2026-06-28 16:52.
  Frontend-now-live + v2-jump-started reflected; launcher brief carried.
- `v3_build_picture.md` — interface-refinement row updated (frontend
  fixes now LIVE, caveat cleared); header stamp 2026-06-28 16:52.
- `standing_instructions.md` — untouched (no new instruction). KB
  re-upload still pending (carryover). The Cat 1 silent-ritual partial
  miss is noted in this record, not a new instruction.
- `decisions.md` — untouched. KB re-upload still pending (carryover).
- `.close_out_backups/` — stale S195 prompt removed; S196 opening prompt
  written.

## Pending operator-side actions

- **Frontend live-look** (quick): nav stays pinned scrolling
  BetLog/Accounts; on the next real partial-fill lay confirm the "still
  unmatched" figure holds steady. The fixes are live; this just eyeballs
  them.
- **Re-upload `decisions.md`** to the bethub-rebuild Project KB (S191
  DR-029 + S180 DR-032 amendments; carryover).
- **Re-upload `standing_instructions.md`** to the Project KB (S189 §4
  live-integration rule; carryover).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** now running (jump-started S195); jump-start-only to retirement.

## Forward routing (CONFIRMED with operator)

Routing was confirmed at the S194 close and is unchanged by this
near-orientation-only session: **S196 drafts the launcher capture-data
provisioning brief** (the capture.db link + carried F9/F10/F12 +
rebuild-if-source-newer) via the brief-drafting skill. The **cash-modal
back-stake blank** remains a flagged pre-cutover must-fix (its own small
frontend brief, sequenced at the operator's call). Queue after:
settlement-worker brief (IOU design + manual-match-to-lay) → promo-seed
item → W16 cutover. The **trickle check-up (now due, 2026-06-28)**
surfaces first thing at the S196 open.
