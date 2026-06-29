# Session 170

**Title:** BetLog build de-risked into a read-only codebase
review first — review brief locked + Code prompt staged.
Plus v2 jump-started for live betting (DB corruption found,
jump-start-only call to retirement).

**Opened:** 2026-06-20 09:51 ACST
**Closed:** 2026-06-20 10:41 ACST
**Tool routing:** Claude Chat (planning / scoping / brief
drafting) + Desktop Commander operational (v2 launch, v2 DB
diagnosis read-only, v3 source grounding read-only). No Code
commissioned in-session; the review brief is handed off for
out-of-session Code execution.
**Governing DRs:** DR-021 (timestamps), DR-030 (module
boundaries — endpoint placement), DR-032 (Betfair canonical
+ cycle axis), DR-019 (derived P&L on read), DR-022 (vocab).
DR-013 (DB read discipline — `start_process` Python, never
copy) for the v2 diagnosis. DR-027/028 named explicitly
out-of-scope for this review (BetLog is pure operational
store, no capture.db).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
  → `2026-06-20 09:51 ACST`
- Close: same command → `2026-06-20 10:41 ACST`

## Pre-flight checks (open ritual)

Drift-check clean: `current_state.md`, `SESSION_169.md`, and
`v3_build_picture.md` all stamped 2026-06-20 09:31 ACST (S169
close). `.close_out_backups/` held only
`SESSION_170_opening_prompt.md` — no stale prior prompt. No
phantom files at root (11 expected `.md` + `v3_build_picture.md`
+ `external_api_resources.md` + `openapi.json`, all
legitimate). Same-workday open (S169 closed 09:31, S170
opened 09:51 — a twenty-minute continuation).

## Session shape

Two distinct strands. **First, an operational interrupt:**
the operator needed to bet today and v2 was not running.
Launched v2 (Flask :5000 + Vite :5173 via the `start.sh`
basis, run as nohup processes), confirmed Betfair connected
(balance $2814.32, 231 markets, login OK), browser opened.
Caught a `database disk image is malformed` error at Flask
startup and ran a read-only integrity check on the live
`data/bethub.db` — corruption confined to two regenerable /
diagnostic tables (`data_integrity_warnings` and
`betfair_events_cache` + its index); the actual betting
tables (`bets` 1937, `accounts` 49, `transactions` 2418)
read clean. Operator cleared to bet. Operator's call:
**no repair — jump-start v2 each session until it's retired
at cutover.**

**Second, the session's planned work:** the BetLog brief.
The operator redirected the approach — rather than draft the
build brief, **get Code to validate the scope against the
real codebase first** (same de-risking move as the S165–166
racing-page review). So the planned build brief flipped to a
**read-only codebase-review brief**: Code inspects, reports
findings + a buildable verdict, builds nothing; S171 triages
the report and drafts the build brief off it. The operator's
two open calls were handled cleanly by the flip — the
delete-semantics question became a review *question* (area D
answers it) rather than a blind decision; the Book filter
rides into the build brief untouched. Drafted the full review
brief end-to-end and staged the ready-to-paste Code prompt.

## What was delivered

1. **v2 relaunched for live betting.** Flask + Vite up,
   Betfair connected, app open in Chrome. Done as a
   jump-start, not a fix — the operator confirmed v2 gets
   jump-started on request until cutover retires it, no
   repair work invested.

2. **v2 DB corruption diagnosed (read-only) + classified
   non-blocking.** `PRAGMA integrity_check` on the live
   `data/bethub.db`: corruption is confined to
   `data_integrity_warnings` (the integrity logger's own
   table — source of the startup "malformed" error) and
   `betfair_events_cache` + index `ix_bec_sport_start` (a
   cache that rebuilds from Betfair). Cross-linked-page
   corruption (the spreadable kind), but on regenerable
   tables only. Betting tables intact. Repair declined by
   operator (v2 retiring). **Carry note:** the corruption can
   spread under continued cache writes; if v2 misbehaves
   before cutover, the clean fix is stop → back up →
   drop-and-rebuild the two tables → restart.

3. **BetLog review brief — locked.** Written to
   `interface_triage/betlog_review_brief.md` (420 lines,
   18,555 bytes, sha256 `c092ccfeeebf0e55…`). Read-only
   codebase review of the v3 bets layer against
   `betlog_scope.md`. Seven anchored review areas + an
   overall read:
   - **A** bets read surface (row + tuck-in fields → real
     schema; P&L derivation; promo-terms gap; persona join).
   - **B** filter feasibility (account / account-at-book /
     book / promo / date / state — all queryable?).
   - **C** API surface (no bets-feed endpoint today; extend
     `racing.py` vs new bets router; DR-030 boundary read).
   - **D** edit/delete safety (maps downstream `bet_id` /
     `cycle_id` references; **answers the operator's
     delete-semantics call** — hard vs soft, orphan risk).
   - **E** settlement seam (pins the exact read interface
     `settlement.py` uses off a bet — the do-not-touch
     boundary; names the brief-3 confirm write seam).
   - **F** frontend scaffold (`ui/web/` routing, nav,
     data-fetch pattern, vitest).
   - **G** test baseline (`uv run pytest -q` + vitest counts).
   - **H** overall buildable / buildable-with-adjustments
     verdict.
   Output spec: `interface_triage/betlog_review_report.md`,
   findings only, ~300–550 lines. Hard limits: edits nothing,
   builds nothing, no git ops, no `.db` access, no settlement
   touch, no scope creep into briefs 2/3.

4. **v3 anchors grounded (read-only) during drafting.**
   Confirmed: `bets`/`bet_legs` schema (cycle_id, side,
   commission, settlement_state, free-bet fields; legs carry
   NOT NULL Betfair ids + event/venue/sport);
   `racing.py` hosts mixed GETs (list_races@614,
   get_log_context@707, list_accounts@753) + POSTs
   (log_bet@853, place_lay@994) but **no bets-list endpoint**;
   `ui/web/` is a thin Vite/React/TS scaffold with vitest
   present (`App.test.tsx`). v3 tree dirty as expected
   (streaming/placement modified; operational store + domain +
   `ui/web/` untracked).

5. **Ready-to-paste Code session prompt** provided for the
   review (read-and-confirm gate, read-only + no-git + no-db
   + no-settlement-touch rules, `uv run pytest -q` for the
   baseline, single output file, stop condition).

## Standing-instruction adherence check

- **Cat 1 (brevity, decision-maker framing, call-driven
  surfacing):** honoured. Led with the call at each turn (bet
  first → DB verdict → review-vs-build flip → the two operator
  calls → shape confirm). "This deserves a little detail"
  flagged before the DB-corruption explanation. Dev-lead calls
  (endpoint placement, sequencing, length range) not
  enumerated back per the S163 rule — only the two genuine
  operator calls (Book filter, delete semantics) surfaced, and
  both were absorbed by the review flip.
- **Cat 2 (session protocol):** timestamps anchored open +
  close (DR-021). Session record written. Opening prompt
  generated without being asked. Ready-to-paste Code prompt
  provided at hand-off without being asked (S163 rule).
  Forward routing operator-confirmed (review-first, then
  S171 triage → build brief).
- **Cat 3 (filesystem + tooling):** Desktop Commander used
  exclusively; `bash_tool` not touched. v2 + v3 source +
  v2 DB read read-only via `start_process`; DB queried at
  canonical path, never copied (DR-013). Brief written
  chunked + verified (line/byte/sha + header grep). Skills
  read before use (`bethub-session-open`,
  `bethub-brief-drafting`, `bethub-session-close`).
- **Cat 4 (governance framing):** cycle convention respected
  — the review brief treats `cycle_id` as the single-unit key
  (area A.4, D). Plain operational framing on the DB verdict
  (regenerable-tables-only, betting-data-intact).
- **Cat 5 (division of labour):** software/architecture calls
  made autonomously (review areas, anchors, endpoint-options
  framing, output spec). Operational calls put to the operator
  (bet readiness, v2 repair vs jump-start, the review-first
  redirect was operator-initiated). The delete call correctly
  reframed from a blind operator decision into a code-review
  question.
- **Google Drive auto-sync:** not prompted at close.

## Open items

Pointer-only — full detail in `current_state.md`.

**Promoted for Session 171:**
- **Triage the BetLog review report** (`betlog_review_report.md`,
  area H first), then **draft the BetLog build brief** off the
  confirmed anchors / any flagged adjustments.

**Carried:**
- **After-the-fact manual entry brief** (brief 2) — opens with
  the capture.db retention check.
- **Free-bet credit-in brief** (brief 3) — S168 design, surface
  in BetLog.
- **Launcher brief** — F9 throttle-to-disk + F10 port override
  (consider F12). Pending, independent.
- Governance: formalise the S168 credit-in design as a short DR
  or Session 70 amendment — operator's call, deferred.
- Parking-lot items (unchanged) — see `current_state.md`.

## Open items out

- **"Draft the BetLog build brief" as the S170 primary** —
  superseded by the operator's review-first call. Not dropped:
  it becomes the S171 deliverable, drafted *after* the review
  validates the scope. ✅
- **Delete-semantics operator call** — reframed from a blind
  decision into review area D (the code answers whether
  hard-delete orphans a cycle). No longer an open operator
  call. ✅
- **v2-not-running** — resolved (jump-started; jump-start-only
  to retirement is the standing call). ✅

## Session close state

- Rebuild folder root: clean, no phantom files.
- `interface_triage/`: one new file this session
  (`betlog_review_brief.md`, 420 lines). All prior files
  unchanged.
- `standing_instructions.md`: untouched this session (no new
  instructions surfaced). KB re-upload still pending
  operator-side (carried from S163 — unchanged).
- `v3_build_picture.md`: updated at this close (Interface
  refinement next-milestone moved — build brief → review brief
  locked + handed to Code; S171 triages).
- `.close_out_backups/`: holds `SESSION_171_opening_prompt.md`
  after this close (S170 prompt removed).

## Forward routing

**S171 triages the BetLog review report**
(`interface_triage/betlog_review_report.md`) — overall read
(area H) first — then **drafts the BetLog build brief** off
the confirmed anchors, folding in any adjustments the review
flagged (and updating `betlog_scope.md` first if any touch the
locked scope). Then brief 2 (manual entry) and brief 3
(free-bet credit-in). Launcher brief remains pending.
**Confirmed with operator** — the operator directed
"review first, then execute based on its feedback," and asked
for the review staged as the next concrete step (brief +
Code prompt delivered). No committed cutover date; ready beats
rushed.
