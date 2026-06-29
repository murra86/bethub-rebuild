# Session 165

**Title:** Interface-deficiency triage — operator's racing-page
run-through sorted into pre-/post-cutover buckets; a read-only
Claude Code codebase-review brief drafted and locked covering
the four verify questions, the three frontend fix-impact maps,
and (added at operator request) a launcher-lifecycle + backend
throttle/data-risk review. Brief handed to Code at close;
report triaged next session.
**Opened:** 2026-06-19 08:16 ACST
**Closed:** 2026-06-19 10:44 ACST
**Tool routing:** Claude Chat (interface triage + review-brief
drafting + governance). One Claude Code commission staged and
handed off at close (the read-only racing-page review brief);
Code executes out-of-session.
**Governing DRs:** DR-013 (DB read discipline), DR-021
(timestamp anchoring), DR-030 (v3 module boundaries), DR-032
(Betfair canonical reference layer + auto-login / throttle —
the §11 backend-risk surface). DR-027/028 named as the
re-read trigger pending at W16 cutover scoping (not this
session).

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → 2026-06-19 08:16 ACST.
- Close: `TZ=Australia/Adelaide date` → 2026-06-19 10:44 ACST.

New-workday open (prior close 2026-06-18 20:38). Full open
ritual ran clean — drift-check passed (current_state,
SESSION_164, v3_build_picture all stamped 20:38 at S164 close;
root clean, `.close_out_backups/` held the S165 prompt as
expected).

## Pre-flight checks

Open ritual clean. Drift-check passed: `current_state.md`
last-updated and `SESSION_164.md` "Closed:" both 20:38 ACST;
`v3_build_picture.md` updated at S164 close (streams moved).
Root: 11 expected `.md` + `v3_build_picture` +
`external_api_resources` + `openapi.json`; all expected dirs
present; no phantom files. (`interface_triage/` created later
this session.)

## Session shape

A triage-and-commission session. The operator brought a
first-pass deficiency list from a v3 racing-page run-through
(15 items spanning the race page and the Betfair hedge modal).
The session sorted each item into pre-cutover blocker vs
post-cutover refinement against the agreed bar — *does it cost
real speed or capability on Strategy 1's daily path?* — and
isolated four items that are really questions about current
behaviour (not yet bucketable without reading the code) plus
three confirmed pre-cutover frontend fixes with possible
backend reach.

The operator confirmed the bucketing and the codebase-review
instinct. The session then drafted a single read-only Claude
Code review brief: it answers the four verify questions (promo
EV soundness; modal hedge auto-calc; runner-number provenance
+ canonical key; TREND base price), and impact-maps the three
frontend fixes (filter clearing; soft-odds blank default;
log-bet clear + odds carry-over) so the eventual fix briefs are
written with full knowledge of blast radius.

Late in the session the operator added a fifth review area: the
`BetHub.command` launcher lifecycle and backend idle/shutdown
behaviour — driven by a real concern about Betfair throttling
and data risk (v2 had problems here) and a secondary annoyance
(terminal windows piling up). This landed as §11, with the
throttle/data questions risk-graded and flagged
pre-cutover-critical if a real risk surfaces.

The session closed on a clean hand-off: the brief is locked and
handed to Code; the operator closed v3 + the terminal (the
clean-shutdown path — confirmed correct); next session triages
Code's report.

## What was delivered

1. **Interface-deficiency triage (15 items).** The operator's
   racing-page + modal run-through was sorted: pre-cutover —
   filters clearing each other (#1), runner-number
   double/mismatch (#3), soft-odds blank default (#7), log-bet
   clear + odds carry-over (#8); verify-first — promo EV
   soundness (#2), modal lay auto-calc (#13), runner-number
   canonical key (#3), TREND base (#6); post-cutover —
   size-at-best-price (#4), table layout/alignment (#5), TREND
   line redesign (#6b), account hot buttons (#9), stake hot
   buttons (#10), modal cash/free-bet alignment (#11), modal
   back-bet support (#12). Operator confirmed the buckets.

2. **Read-only Code review brief drafted + locked.**
   `interface_triage/racing_page_review_brief.md` (482 lines,
   16 §-sections). Source-code review shape (Session 33
   precedent). File anchors grounded by a live pre-flight probe
   of the `bethub-v3` tree (frontend at `ui/web/src/`: route
   `routes/Racing.tsx`, `components/OddsTable.tsx`,
   `HedgeModal.tsx`, `LogBetPanel.tsx`, `PromoBar.tsx`, EV math
   `ev/evEngine.ts` + `commission.ts` + `softOddsLadder.ts`;
   backend `ui/api/routers/racing.py`). Covers §5 area map,
   §6–§9 the four verify questions, §10 the three frontend
   fix-impact maps, §11 launcher/backend risk, §12–§16
   sequencing/output/limits/after/cross-refs.

3. **§11 launcher lifecycle + backend risk (operator-added).**
   Grounded in a read of `BetHub.command`. Code answers, with
   evidence: close-pattern lifecycle map; idle-backend Betfair
   traffic (the throttle question — is it purely request-driven
   or is there a background refresh/keepalive/poll); orphan /
   multi-server risk; login-throttle state persistence (can
   relaunching defeat the back-off and re-create the ~48h v2
   lockout); shutdown cleanliness + data risk (clean logout?
   in-memory audit sink + unflushed WAL on abrupt kill);
   terminal-accumulation cause + lightest fix (map only). Each
   risk-graded; flagged pre-cutover-critical if real.

4. **Ready-to-paste Code session prompt provided** (Cat 2
   always-provide-Code-prompt). Names the read-and-confirm
   gate, read-only discipline (no edits, no git, placement.py
   untouched), `uv run pytest` if needed, the report path
   (`interface_triage/racing_page_review_report.md`), risk-
   grading of §11, and the stop-at-report condition.

5. **v3 + terminal clean-shutdown confirmed.** Operator closed
   both; confirmed correct — the terminal window-close fires
   the launcher's SIGHUP trap → SIGTERM the uvicorn group →
   port released. The orphan case (browser-only close) is what
   §11 investigates.

## Standing-instruction adherence check

- **Cat 1 brevity / decision-framing** — held; the triage led
  with the bucketing table and the call for the operator, detail
  deferred.
- **Cat 1 escalate-to-detail-when-warranted** — used once, on
  the 15-item triage ("this deserves the detail" before the
  table).
- **Cat 1 don't-surface-dev-lead-calls (S163)** — honoured; the
  brief's technical shape (section structure, anchor choices)
  was handled inside the artefact; only genuine calls surfaced
  (new folder, EV-no-fix stance, back-bet mapped-not-built,
  runner-number dual-handling).
- **Cat 2 timestamp anchors (DR-021)** — open + close anchored
  ACST.
- **Cat 2 always-provide-Code-prompt (S163)** — provided
  without being asked; updated when §11 was added.
- **Cat 2 always-provide-opening-prompt** — S166 prompt
  produced this close.
- **Cat 3 Desktop Commander exclusive; verify every write** —
  all file ops via DC; brief verified post-write (line count +
  header grep); launcher + tree read from disk, not assumed.
- **Cat 3 pre-flight grounding before brief drafting** — ran a
  live `bethub-v3` tree probe to ground file anchors rather than
  guessing filenames.
- **Cat 3 dry-run / single-target discipline on mechanical
  edits** — the §11 insertion required renumbering §11–§15 →
  §12–§16; done as individual single-target `edit_block` header
  edits (bottom-up, each header string unique — exempt from the
  dry-run rule), then internal cross-refs patched and verified
  by a header-sequence grep (clean §1–§16, no gaps/dupes). No
  cascade-renumber risk taken.
- **Cat 5 make-the-call / dev-lead territory** — folder
  location, brief structure, anchor selection all made as
  Claude calls; only the consequence-bearing ones surfaced.
- **Fenced-content line-width** — brief written with ~64-char
  wraps for mobile readability.
- **Silent close ritual (Cat 1)** — this close ran silent.

## Open items out (closed/actioned this session)

- **Interface-deficiency triage (was S165 primary)** — done;
  15 items bucketed, operator-confirmed. ✅
- **Codebase-review decision** — confirmed; brief drafted and
  locked. ✅

## Open items (carried — pointer to current_state.md)

- **Triage Code's racing-page review report (S166 primary).**
  Read `interface_triage/racing_page_review_report.md`, confirm
  the four verify verdicts + the §11 risk grades, finalise the
  pre-/post-cutover buckets now that blast radius is known, then
  commission the actual fix brief(s).
- **W16 v2→v3 cutover scoping** — still downstream of the
  interface triage; opens once the pre-cutover fix set is
  cleared. DR-027/028 re-read trigger when it begins.
- **Live unmatched lays (S164)** — three test lays still sit as
  real market exposure; operator-side, pull/manage as desired.
- All S162–S164 parking-lot items unchanged (quick-lay modal
  error-reason; F1 uncaught-transport gap; 200-market
  over-subscription; in-memory audit-sink durability — now also
  surfaced as a §11 risk-to-grade; streaming hardening
  F3/F4/F5; the longer parking lot).

## Session close state

- **Rebuild folder root:** clean, no phantom files. New
  `interface_triage/` directory created this session.
- **`interface_triage/`:** holds `racing_page_review_brief.md`
  (482 lines, locked). Report `racing_page_review_report.md`
  will land here from Code's out-of-session run.
- **`bethub-v3`:** unchanged this session (no code touched —
  Chat-only triage + brief drafting). Tree remains dirty/in-
  flight by design. The pending Code review is read-only and
  will not mutate it.
- **`.close_out_backups/`:** S166 opening prompt written; stale
  S165 prompt removed.
- **`v3_build_picture.md`:** updated at this close (streams
  moved — see below).
- **`standing_instructions.md`:** no edits this session. The
  S163 edits still need the manual KB re-upload (operator-side;
  flagged below).
- **Project knowledge base:** unchanged this session.

## Forward routing — CONFIRMED WITH OPERATOR

The operator handed the locked brief to Claude Code at close
and confirmed S166 will triage Code's report. S166 reads
`interface_triage/racing_page_review_report.md`, walks the four
verify verdicts and the §11 risk grades with the operator,
finalises the pre-/post-cutover buckets now that blast radius
is known (a verify item may move buckets on what's found), then
commissions the actual pre-cutover fix brief(s). W16 cutover
scoping follows once the pre-cutover set is cleared. Operator
confirmed close.

## Pending operator-side action

- **Run the Code review session** — paste the provided prompt
  into a Claude Code session pointed at `bethub-v3`; Code reads
  the brief, confirms back, then executes read-only and writes
  the report.
- **Re-upload `standing_instructions.md`** to the bethub-rebuild
  Claude Project knowledge base if not already done since S163
  (the S163 edits). Drive auto-syncs the local folder; the KB
  copy needs the manual refresh.
- **Manage the three live unmatched lays (S164)** — real market
  exposure; pull or leave as desired.
