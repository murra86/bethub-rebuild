# Session 167

**Title:** Drafted, handed off, and triaged the frontend
pre-cutover fix brief — all four fixes (bonus-winnings EV wiring
+ 70→65 conversion drop, runner-number → saddlecloth, soft-odds
blank default, log-bet clear) landed clean in one bounded Code
session and passed triage green. Ran the cycle-capture
records-look (step zero) and locked the realised-conversion
storage call: manual entry now, auto-at-settlement later. Two of
three pre-cutover briefs still to draft (cycle-capture, launcher).
**Opened:** 2026-06-19 12:35 ACST
**Closed:** 2026-06-19 13:36 ACST
**Tool routing:** Claude Chat (records-look investigation, brief
drafting, Code-report triage). One Code commission handed off
and executed out-of-session this session — the frontend fixes
brief. Cycle-capture + launcher briefs still to draft (S168).
**Governing DRs:** DR-021 (timestamp anchoring), DR-019 (derived
state on read — the EV / soft-odds display surface), DR-025
(hedge classification — the modal label), DR-030 (v3 module
boundaries — the `ui/web/src` touch-lists), DR-032 (Betfair
canonical reference layer — the `cycle_id` / bet-record axis
behind the records-look). DR-027/028 remain the re-read trigger
pending at W16 cutover scoping (not this session).

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → 2026-06-19 12:35 ACST.
- Close: `TZ=Australia/Adelaide date` → 2026-06-19 13:36 ACST.

Same-workday open — S166 closed 12:21 ACST, S167 opened 12:35
ACST, 14 minutes later. Tight continuation; recap kept short per
the same-workday rule.

## Pre-flight checks

Open ritual ran clean and silent. Drift-check passed:
`current_state.md` last-updated, `SESSION_166.md` "Closed:", and
`v3_build_picture.md` "Last updated" all stamped 12:21 ACST at
the S166 close (streams moved S166, build picture correctly
updated). Root: 11 expected `.md` + `v3_build_picture` +
`external_api_resources` + `openapi.json`; all expected dirs
present incl. `interface_triage/`.

**One anomaly surfaced at open and fixed in-session.** The
S166 close record claimed it removed the stale
`SESSION_166_opening_prompt.md` from `.close_out_backups/`, but
the file was still present (alongside the correct
`SESSION_167_opening_prompt.md`). Removed it at open; backups
left holding only the S167 prompt. A missed close-sweep, caught
at the next open exactly as the drift-check is designed to.

## Session shape

A build session, single-threaded on the pre-cutover fix set.
Three phases: (1) the cycle-capture records-look (step zero,
operator-directed at S166) — a read-only investigation of v3's
bet-storage layer; (2) drafting the frontend fixes brief and
handing it to Code; (3) triaging Code's report when it came back
in-session. The frontend brief went the full round-trip —
drafted, executed out-of-session, triaged green — inside S167.

The operator handed Claude the routing call early ("whatever you
recommend") and stayed in a delegating posture; the records-look
storage question (manual vs auto realised-conversion) was the
one operator-call surfaced, and the operator resolved it
cleanly. Closed on a clean complete unit (one of three
pre-cutover briefs fully landed), with cycle-capture + launcher
deferred to S168 for fresh budget rather than squeezed in at the
tail.

## What was delivered

1. **Cycle-capture records-look** (`interface_triage/
   cycle_capture_records_look.md`, 111 lines). Read-only review
   of v3 bet-storage. Findings: (a) the link mechanism already
   exists — every bet carries a `cycle_id`, the log-bet API
   accepts one (`None` → fresh), so linking a free bet to its
   qualifier needs **no new schema**; (b) the UI never passes a
   parent `cycle_id` (`LogBetPanel.tsx` sets none), so today
   every bet starts a fresh cycle — the link is unbuilt at the
   UI layer; (c) `realised_conversion_rate` exists as a column
   but is never populated (settlement is an empty stub; the
   record builder always writes NULL). Net: cycle-capture is not
   a heavy schema job — it's a frontend link affordance + a
   manual realised-conversion entry, not new storage.

2. **Realised-conversion storage call — LOCKED (operator).**
   Manual entry now (operator types the realised figure when the
   free bet's cycle completes), auto-at-settlement later as an
   explicit known successor. The manual field must be designed
   forward-compatible with auto-population (must not block
   settlement from later computing the same field). A separate
   operator-facing **manual-process how-to** is a named
   follow-on deliverable, timed for after the cycle-capture UI
   shape locks.

3. **Frontend fixes brief** (`interface_triage/
   frontend_fixes_brief.md`, 419 lines). Surgical-fix brief
   (Sessions 35/36 shape), four fixes as one bounded Code
   session, all display/form-state, zero bet-path reach.
   Sections §1–§11 per the universal spine; dirty-tree
   discipline, bet-safety hard limits, `uv run pytest` gate,
   named anchors with confirm-before-edit. Drafted end-to-end,
   verified on disk (419 lines, all sections present).

4. **Frontend fixes — executed + triaged GREEN.** Code ran the
   brief out-of-session (read-and-confirm gate passed cleanly —
   Code restated all four fixes + hard limits accurately before
   touching a file). Report at `interface_triage/
   frontend_fixes_report.md` (352 lines). Outcome:
   - **Fix A (F1/F2/F4)** — bonus-winnings EV wiring fixed
     (`bonus_pct: return_pct`, `basis: 'winnings'` at both call
     sites); 70→65 conversion collapsed to one constant; modal
     label corrected. **Proven via test flip:** pre-fix Promo EV
     == Raw EV (−3.7% == −3.7%, the collapse) ❌ → post-fix
     +44.5% ≠ −3.7% ✅. Three conversion-shifted fixtures
     recomputed to 0.65, cross-checked to 6 dp; `evFreeBet`
     correctly unmoved.
   - **Fix B (Q3)** — render `{runnerName}` only (Betfair
     saddlecloth), `idx+1` dropped.
   - **Fix C (#7)** — soft-odds default blanked, stepper
     fallback preserved.
   - **Fix D (#8/F7)** — `clearForm()` extracted, reset re-keyed
     on `marketId`, manual Clear button added.
   - **Bet-path provably untouched:** Python suite 1028→1028
     identical. Dirty tree 62→62 same shape. Frontend vitest
     90→91 (+1 = the new A4 test). `tsc -b` clean.

## The three Code findings (triaged)

1. **Brief test-runner tension** — §4 said `uv run pytest` only,
   but Fix A's engine/test/fixtures are TypeScript (vitest).
   Code used pytest as the Python gate + vitest for the TS
   regression; both green. Claude-territory brief-quality lesson:
   **frontend-touching briefs must name vitest for TS tests +
   pytest as the Python backend gate.** Carry into the
   cycle-capture brief (it has a frontend piece). No operational
   impact.

2. **`v2_regression.ts` audit-guard override** — the fixtures
   carry a "do not update without a paired v2 audit" warning;
   A5's 70→65 recompute deliberately overrode it for the three
   conversion fixtures (intentional S166 business decision, each
   annotated inline). Surfaced to operator as a heads-up: v3's
   EV figures now intentionally differ from v2's old 70%-pinned
   ones (expected — v3 is the rebuild). Parked tidy-up option:
   split the v3-0.65 fixtures into their own block if strict
   v2-pin separation is ever wanted. Not actioned.

3. **Untracked frontend tree → empty `git diff`** — `ui/web/`
   is untracked, so the brief's per-file `git diff` check is
   structurally empty. Code substituted final-anchor greps +
   test verification; dirty-set shape provably unchanged (62→62).
   Claude-territory lesson: **for untracked frontend files, the
   dirty-tree per-file-diff check doesn't apply — specify
   grep + test verification instead.** Frontend-specific (the
   launcher brief touches tracked Python files, where git diff
   works). No operational impact.

## Standing-instruction adherence check

- **Cat 1 silent session-open ritual (S114-tightened)** —
  honoured. No step-narration headers in operator-facing text
  (the S166 partial-miss did not recur); steps ran silent, one
  combined orientation output, the one anomaly surfaced.
- **Cat 1 calendar-calibrated open (same-workday)** — honoured;
  tight 14-minute-reopen recap, no arc-state framing.
- **Cat 1 brevity / one-decision-at-a-time** — held; the
  records-look surfaced exactly one operator-call (manual vs
  auto), walked one at a time.
- **Cat 1 inventory-first on long reports** — honoured on the
  triage; the report's findings classified by operational
  impact, only finding 2 (the audit-guard override) surfaced to
  the operator, findings 1 + 3 handled as Claude-territory
  lessons.
- **Cat 1 don't-surface-dev-lead-calls (S163)** — honoured; the
  frontend brief hand-off was tight (what/where/next + the Code
  prompt), no enumerated dev-lead-call list.
- **Cat 1 escalate-to-detail-when-warranted** — used at the
  records-look result and the triage verdict, both proportionate.
- **Cat 2 timestamp anchors (DR-021)** — open + close anchored
  ACST (12:35 / 13:36).
- **Cat 2 always-provide-opening-prompt + Code-session prompt
  (S163)** — both provided: the ready-to-paste Code prompt at
  brief hand-off, and the S168 opening prompt at this close.
- **Cat 3 Desktop Commander exclusive; verify every write** —
  all file ops via DC; records-look note, brief, and this record
  written in chunks and verified.
- **Cat 3 brief-drafting skill read before drafting** — honoured
  (read the `bethub-brief-drafting` skill before the frontend
  brief).
- **Cat 5 make-the-call / operator-call split** — held; routing
  + brief-shape made as Claude calls; the realised-conversion
  storage call (operator workflow consequence) surfaced to the
  operator.
- **Fenced-content / artefact line-width** — records-look note,
  brief, and this record written at ~64-char wraps.
- **Silent close ritual (Cat 1)** — this close ran silent.

## Open items out (closed/actioned this session)

- **Cycle-capture records-look (step zero)** — done; storage
  link mechanism mapped, realised-conversion call locked
  (manual now / auto later). ✅
- **Frontend pre-cutover fix brief** — drafted, handed to Code,
  executed, triaged green. All four fixes landed; bet-path
  provably untouched. ✅
- **Stale `SESSION_166_opening_prompt.md`** in backups — removed
  at open (S166 close-sweep miss). ✅

## Open items (carried — pointer to current_state.md)

- **Draft the cycle-capture brief (S168)** — frontend link
  affordance (tag free bet to qualifier's cycle via existing
  `cycle_id` API) + manual realised-conversion entry
  (forward-compatible with auto-at-settlement). Reaches
  bet-record write. Records-look done — brief is unblocked.
- **Draft the launcher brief (S168)** — F9 throttle-state-to-
  disk + F10 port-override; consider folding F12 TEMPORARY_BAN
  port + shutdown-logout. Launcher + auth surface (tracked
  Python — git-diff discipline applies normally).
- **Operator live-UI validation of the frontend fixes** — the
  report's named checks (bonus-winnings EV above raw, single
  saddlecloth number, blank soft-odds cells, panel clears on
  race switch + Clear button). Operator-side, when next
  launching.
- **Manual-process how-to (cycle-capture)** — operator-facing
  walkthrough, timed for after the cycle-capture UI shape locks.
- **W16 v2→v3 cutover scoping** — downstream of all three
  pre-cutover briefs landing. 1 of 3 done. DR-027/028 re-read
  trigger when scoping begins.
- **Brief-quality lessons (carry into S168 drafting):** name
  vitest + pytest for frontend-touching briefs; use grep + test
  verification (not per-file git diff) for untracked frontend
  files.
- Parking-lot unchanged: quick-lay modal error-reason surfacing;
  streaming-path F1 transport gap; 200-market over-subscription;
  audit-sink durability (F8) + place-then-commit (F11) parked;
  streaming hardening (F3/F5/F4 series); the longer parking lot.

## Session close state

- **Rebuild folder root:** clean, no phantom files.
- **`interface_triage/`:** holds the S165 review brief, the S166
  review report, plus three S167 artefacts —
  `cycle_capture_records_look.md`, `frontend_fixes_brief.md`,
  `frontend_fixes_report.md`. The cycle-capture + launcher
  briefs land here at S168.
- **`bethub-v3`:** the frontend fixes landed (Code,
  out-of-session) across `evEngine.ts`, `OddsTable.tsx`,
  `Racing.tsx`, `HedgeModal.tsx`, `LogBetPanel.tsx`,
  `v2_regression.ts`, + new `OddsTable.test.tsx`. Tree remains
  dirty/in-flight by design; bet-path untouched (Python suite
  1028→1028). No git operations.
- **`.close_out_backups/`:** S168 opening prompt written; stale
  S167 prompt removed.
- **`v3_build_picture.md`:** updated at this close (Interface
  refinement stream moved — frontend brief drafted + executed +
  triaged).
- **`standing_instructions.md`:** no edits this session. The
  S163 edits still need the manual KB re-upload (operator-side;
  flagged below).
- **Project knowledge base:** unchanged this session.

## Forward routing — CONFIRMED WITH OPERATOR

The operator asked for the cutover-position read, then to close.
S168 drafts the remaining two pre-cutover briefs —
cycle-capture (records-look done, unblocked) and launcher — each
its own focused work, then hands them to Code. The operator's
live-UI validation of the frontend fixes runs operator-side
whenever they next launch. Once all three pre-cutover briefs
land and validation is done, W16 cutover scoping is the next
major routing decision (DR-027/028 re-read trigger). Operator
confirmed close.

## Pending operator-side action

- **Re-upload `standing_instructions.md`** to the bethub-rebuild
  Claude Project knowledge base if not already done since S163.
  Drive auto-syncs the local folder; the KB copy needs the
  manual refresh. (Carried from S165/S166 — still outstanding.)
- **Live-UI validation of the frontend fixes** — per the
  report's named checks.
- **Manage the three live unmatched lays (S164)** — real market
  exposure; pull or leave as desired.
