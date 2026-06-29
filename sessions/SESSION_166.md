# Session 166

**Title:** Triaged Code's racing-page review report (12
findings). Locked the pre-cutover fix set — bonus-winnings EV
break, launcher lockout hardening, runner-number display,
soft-odds blank default, log-bet clear/carry-over, plus a
newly-promoted cycle-capture item. Dropped 70→65 free-bet
conversion across the whole tool. Confirmed insurance EV's
single-leg framing as correct. Dropped the filter "bug" (didn't
reproduce). No briefs drafted yet — S167 drafts the three.
**Opened:** 2026-06-19 10:54 ACST
**Closed:** 2026-06-19 12:21 ACST
**Tool routing:** Claude Chat (report triage + bucketing +
decision capture). No Code commission handed off this session;
three fix briefs to be drafted at S167, then handed to Code.
**Governing DRs:** DR-021 (timestamp anchoring), DR-032
(Betfair canonical reference layer + auto-login / throttle —
the F9 launcher surface), DR-025 (hedge classification — the
modal lay/back surface), DR-019 (derived state on read — the
EV / soft-odds display surface). DR-027/028 remain the re-read
trigger pending at W16 cutover scoping (not this session).

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → 2026-06-19 10:54 ACST.
- Close: `TZ=Australia/Adelaide date` → 2026-06-19 12:21 ACST.

Same-workday open — S165 closed 10:44 ACST, S166 opened 10:54
ACST, ten minutes later. Tight continuation; recap was kept
short per the same-workday rule.

## Pre-flight checks

Open ritual ran clean. Drift-check passed: `current_state.md`
last-updated, `SESSION_165.md` "Closed:", and
`v3_build_picture.md` "Last updated" all stamped 10:44 ACST at
the S165 close (streams moved S165, so the build picture was
correctly updated). Root: 11 expected `.md` + `v3_build_picture`
+ `external_api_resources` + `openapi.json`; all expected dirs
present incl. `interface_triage/`; no phantom files.

**One anomaly surfaced at open and resolved in-session.** The
S166 primary work (triage Code's report) needed
`interface_triage/racing_page_review_report.md`, which did not
exist at open — only the brief was present. Flagged to the
operator immediately rather than proceeding. The operator had
just finished the Code review run; the report landed moments
later and the triage proceeded.

## Session shape

A report-triage session, single-threaded. The operator ran the
read-only Claude Code racing-page review out-of-session
(commissioned at S165 close); this session read Code's 534-line
report and worked through it with the operator to finalise the
pre-/post-cutover buckets now that blast radius was known.

Inventory-first cadence (Cat 1): the report's 12 findings plus
the four verify answers were classified by operational impact,
then the operator-call items surfaced one at a time in plain
gambling language. The session closed on a fully-locked
pre-cutover set, with brief drafting deferred to S167 as its
own focused work.

## The report in one line

Read-only, working tree untouched (62 dirty entries at open and
close, no git ops), every finding grounded in `file:line`
reads. Test suite deliberately not run (judged unnecessary for
a bounded read; F1 is in fact *masked* by a passing unit test).
Code's own pre-cutover-critical candidates were F1 and F9.

## Decisions locked this session

1. **F1 — bonus-winnings EV break → FIX, pre-cutover.** The
   bonus-winnings promo EV silently collapses to raw EV: the UI
   passes `return_pct` but the engine reads `bonus_pct`, which
   the config never sets, so the bonus is treated as zero. Error
   direction *understates* the promo (risk is passing on a good
   play, not placing a bad one). Operator confirmed fix —
   bonus-winnings plays come up often enough to matter.
   **Agreed maths:** effective odds = SoftOdds + bonus% ×
   (SoftOdds − 1), with the free-bet portion valued at the
   free-bet conversion rate, and frozen once it hits the promo's
   max-bonus cap (e.g. $50). Bonus % stays configurable per
   promo (operator's formula was the 100% case; engine multiplies
   winnings by the promo's bonus % before conversion). Frontend-
   only, no bet-path reach.

2. **Free-bet conversion 70 → 65 across the whole tool.**
   Operator chose to drop the free-bet cash-return assumption
   from 70% to 65% everywhere (conservative). Lands on the
   engine's conversion default (feeds insurance EV today + the
   new bonus-winnings path), the second engine copy (point both
   at one constant — folds in F4), and the hedge modal's "70%
   applied" label (which is F2 — the label is decorative, the
   modal applies no conversion in its lay sizing; corrected for
   consistency). Net effect: tool gets slightly stricter on
   free-bet-heavy cycles. Folded into the same brief as F1 (same
   free-bet maths).

3. **F9 — launcher lockout re-hammer → FIX, pre-cutover.** The
   escalating login back-off (30m→1h→2h→4h cool-off, hard-kill
   at 5 failures) lives only in memory, so every force-quit-and-
   relaunch resets it to zero. Force-quitting and relaunching
   during a Betfair outage reproduces the request-hammering that
   locked the operator out ~48h on v2. Fix: persist the back-off
   state to disk so it survives a restart (cool-off resumes
   rather than resetting). The §11 risk the operator specifically
   flagged. Nowhere near the bet-placement path.

4. **F10 — `BETHUB_LAUNCH_PORT` two-copies path → close, same
   brief as F9.** A launch-port override lets a second instance
   run = two concurrent Betfair logins/streams. Same family as
   F9, cheap to close. Folded into the launcher brief.

5. **F5 — insurance EV single-leg framing → CONFIRMED correct,
   no fix.** The insurance EV models the qualifying bet + its
   triggered refund (refund valued as a free bet at the
   conversion rate); it does *not* model laying the qualifier
   off on the exchange. Walked through a worked example with the
   operator: laying the qualifier off is a different, low-
   variance strategy that sells the win to the exchange — not
   how Safety Net is run. The operator confirmed they rarely lay
   an insurance qualifier; they only ever lay the *triggered
   free bet*, which the conversion rate already models. So the
   on-screen EV is the true EV of the operator's actual play.
   Leave as-is.

6. **Q3 — runner number → FIX, pre-cutover.** The "1. 2. Heart
   N Power" double number: the first is the app's own row-count
   index (`idx+1`), the second is Betfair's saddlecloth number
   embedded in the runner name. They diverge after scratchings /
   when book order ≠ cloth order. Bets are unaffected — they key
   on the stable Betfair selection_id regardless — so this is a
   misread-the-runner hazard, not a data/settlement risk.
   Operator's call: drop the app's row-count, show Betfair's
   saddlecloth number only (matches the number every other book
   shows, so cross-checking is instant). Build-time verify
   whether the number is a clean field or must be parsed from
   the runner-name string (Claude-territory detail). Display-
   only, frontend-only.

7. **#7 — soft-odds blank default → FIX, pre-cutover.** The
   Soft Odds cell auto-fills with the Betfair back price;
   operator wants it blank so the real soft-book price is typed
   fresh. Report confirms blanking is behaviour-safe — EV
   columns show a dash until typed, and a blank cell can't be
   logged or hedged off (downstream guards exist). No silent
   miscalculation. Frontend-only.

8. **#8 / F7 — log-bet clear + carry-over → FIX, pre-cutover.**
   Confirmed real: on a race switch the soft odds + snapshot
   don't clear (the reset effect is guarded by `if
   (selectedRunner)`, false on switch-to-null), and stake never
   resets on a switch at all (only on successful submit). No
   manual clear control exists. Fix is both halves: auto-clear
   on race switch (soft odds, snapshot, stake) + a manual clear
   button. Frontend form-state only, no bet-path reach.

9. **Cycle-capture → PROMOTED to pre-cutover (new item).** The
   operator wants the *realised* value of a Safety Net cycle
   tracked: the qualifying bet plus, if a free bet triggers, the
   *actual* cash converted out of it (e.g. a real 72%, not the
   65% planning assumption), recorded as one linked unit. The
   65% stays a pre-race planning assumption only; the realised
   figure is pure record-of-fact. Operator's deciding argument
   for pre-cutover: if the qualifier→free-bet link isn't captured
   at go-live, every post-cutover cycle becomes a manual back-
   fill hole. **Scope boundary drawn:** the *capture* (linked
   record at real conversion) is pre-cutover; the *analytics on
   top* (true ROI, conversion-rate trends, re-checking the 65%
   assumption) stays post-cutover — the records sit waiting, the
   report runs later. **Step zero before briefing:** a look at
   what v3's bet records capture today — whether a free bet
   already links back to its originating qualifier or whether
   that link must be built (may surface a small storage-design
   call). Separate brief — reaches bet storage/settlement, not
   the racing-page frontend.

10. **#1 / F3 — filter "bug" → DROPPED.** The filters-clearing-
    each-other bug doesn't reproduce in code (`toggleCode`
    already toggles only the clicked code; filters live in
    `RaceListSidebar.tsx`, not `Racing.tsx`). Operator confirmed
    it's behaving live. Off the list entirely — nothing to brief.

## Handled silently (Claude's territory / parked)

Per Cat 1 inventory-first + Cat 5, the no-operator-call findings
were sorted without surfacing as decisions:

- **Q2 modal auto-calc — correct.** Lay sizing is live-price-
  driven (500ms poll until the operator edits, then sticks), the
  free-bet hedge is byte-identical to the EV engine's, liability
  soft-cap + fat-finger confirm guards present. Only issue was
  the F2 label, folded into the conversion pass.
- **Q4 TREND base — working as designed.** Base is the oldest
  `best_back` sample still inside the rolling ~5-min window
  (sliding, not anchored to market open); resets on market
  change, survives runner switch, blank for a few seconds after
  a page reload. No action.
- **F8 audit-sink durability (MEDIUM) — stays parked** per the
  brief's §16 (durability fix parked). Memory-only singleton
  audit sink loses placement audit entries on exit.
- **F11 kill-between-place-and-commit (MEDIUM) — parked with
  F8.** Narrow window; a `kill -9` between the Betfair ack and
  the local DB commit leaves an unrecorded live lay. Compounds
  F8.
- **F4 (0.7 hard-coded in 3 places) — folded** into the
  conversion-drop pass (point all at one constant).
- **F6 (table EV vs logged-snapshot EV normalise over different
  active-runner sets) — parked, LOW.** Coincide in a normal OPEN
  race; diverge only in edge states.
- **F12 (INFO) — dead code + v2 TEMPORARY_BAN backoff not ported
  + no Betfair logout on shutdown.** The TEMPORARY_BAN port and
  shutdown-logout are launcher-surface; flagged as candidates to
  fold into the launcher brief at drafting (Claude-territory
  call). Dead code ignorable.

## What was delivered

No artefacts written this session — a pure triage-and-decide
session. The output is the locked decision set above, rotated
into `current_state.md` and recorded here. Code's report
(`interface_triage/racing_page_review_report.md`, 534 lines)
landed from the out-of-session run and was read in full.

## The pre-cutover fix set (locked) → three briefs at S167

Split by where each reaches:

- **Frontend brief** — F1 bonus-winnings EV + 70→65 conversion
  drop (incl. F2 label + F4 consolidation), runner number →
  Betfair saddlecloth only, soft-odds blank default, log-bet
  clear (auto on race switch + manual button). All display /
  form-state, no bet-path reach. One bounded session.
- **Cycle-capture brief** — separate; reaches bet storage /
  settlement. Carries the records-look as step zero. Capture
  only (analytics post-cutover).
- **Launcher brief** — F9 throttle-state persistence + F10
  port-override two-copies path; consider folding F12's
  TEMPORARY_BAN port + shutdown-logout. Launcher + auth surface.

## Standing-instruction adherence check

- **Cat 1 inventory-first cadence on long reports** — honoured;
  12 findings + 4 verify answers classified by operational
  impact, operator-call items surfaced in plain language, no-call
  items handled silently.
- **Cat 1 brevity / one-decision-at-a-time** — held; findings
  walked one at a time, each with a single call.
- **Cat 1 escalate-to-detail-when-warranted** — used twice (the
  opening report-shape summary; the F5 worked-example walk-
  through), both flagged.
- **Cat 1 plain-language / no-jargon** — held; EV maths and
  launcher internals rendered in real-world gambling terms.
- **Cat 1 don't-surface-dev-lead-calls (S163)** — honoured; the
  build-time "is the runner number a clean field or parsed"
  detail was named as Claude-territory, not punted as a call.
- **Cat 1 silent open ritual** — partial miss: step-narration
  ("Step 1 — timestamp anchor", etc.) appeared in operator-facing
  text at this open, against the S114-tightened silent-ritual
  rule. Caught mid-session; the combined orientation output and
  the close ran clean. Flagged here so the next open watches for
  it. No skill-body change needed (the rule is already explicit).
- **Cat 2 timestamp anchors (DR-021)** — open + close anchored
  ACST (10:54 / 12:21).
- **Cat 2 always-provide-opening-prompt** — S167 prompt produced
  this close.
- **Cat 3 Desktop Commander exclusive; verify every write** —
  all file ops via DC; record written in chunks, verified at
  Step 11.
- **Cat 5 make-the-call / operator-call split** — held; software
  shape (brief split, constant consolidation) made as Claude
  calls; everything with operational/strategy/account-hygiene
  consequence surfaced to the operator.
- **Fenced-content line-width** — record written at ~64-char
  wraps.
- **Silent close ritual (Cat 1)** — this close ran silent.

## Open items out (closed/actioned this session)

- **Triage Code's racing-page review report (was S166
  primary)** — done; all 12 findings + 4 verify answers
  triaged, buckets finalised, operator-confirmed. ✅
- **The four verify-first items (promo EV soundness, modal lay
  auto-calc, runner-number canonical key, TREND base)** —
  resolved into their buckets: F1 fix + F5 confirm-as-is (EV
  soundness), modal correct (auto-calc), saddlecloth display fix
  (runner number), working-as-designed (TREND). ✅
- **Filter bug (#1)** — dropped, didn't reproduce, operator
  confirmed live. ✅

## Open items (carried — pointer to current_state.md)

- **Draft the three pre-cutover fix briefs (S167 primary)** —
  frontend brief, cycle-capture brief (records-look first),
  launcher brief.
- **W16 v2→v3 cutover scoping** — downstream of the pre-cutover
  fixes landing. DR-027/028 re-read trigger when it begins.
- **Live unmatched lays (S164)** — three test lays still real
  market exposure; operator-side, pull/manage as desired.
- Parking-lot unchanged: quick-lay modal error-reason surfacing;
  F1-uncaught-transport gap (the streaming-path F1, distinct
  from the EV F1 above); 200-market over-subscription; audit-
  sink durability (now also F8); streaming hardening (F3
  keepAlive / F5 INVALID_CLOCK / F4 on-screen warning — note
  these are the *streaming* F-numbers, a separate series from
  this report's findings); the longer parking lot.

## Session close state

- **Rebuild folder root:** clean, no phantom files.
- **`interface_triage/`:** holds `racing_page_review_brief.md`
  (locked, S165) + `racing_page_review_report.md` (534 lines,
  Code's report, read this session). The three fix briefs will
  land here at S167.
- **`bethub-v3`:** untouched this session (Chat-only triage).
  Tree remains dirty/in-flight by design; the completed Code
  review was read-only and did not mutate it (62 dirty entries
  at open and close).
- **`.close_out_backups/`:** S167 opening prompt written; stale
  S166 prompt removed.
- **`v3_build_picture.md`:** updated at this close (streams
  moved — Interface refinement stream advanced from
  awaiting-code-execution to brief-drafting).
- **`standing_instructions.md`:** no edits this session. The
  S163 edits still need the manual KB re-upload (operator-side;
  flagged below).
- **Project knowledge base:** unchanged this session.

## Forward routing — CONFIRMED WITH OPERATOR

The operator confirmed close after the triage was complete and
the full pre-cutover set was locked. S167 drafts the three fix
briefs (frontend, cycle-capture, launcher), each its own
focused work. The cycle-capture brief carries a records-look as
step zero before drafting. Brief drafting was deliberately
deferred from this session rather than pushed through — the
triage was a full session's work and briefs deserve their own
budget. Once the briefs are drafted and handed to Code, the
fixes execute out-of-session; W16 cutover scoping follows the
pre-cutover set landing. Operator confirmed close.

## Pending operator-side action

- **Re-upload `standing_instructions.md`** to the bethub-rebuild
  Claude Project knowledge base if not already done since S163
  (the S163 edits). Drive auto-syncs the local folder; the KB
  copy needs the manual refresh. (Carried from S165 — still
  outstanding.)
- **Manage the three live unmatched lays (S164)** — real market
  exposure; pull or leave as desired.
