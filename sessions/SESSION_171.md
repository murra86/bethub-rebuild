# Session 171

**Title:** BetLog triaged → built → triaged in one arc. The
S171 review report came back "buildable with adjustments";
three operator calls locked (hard delete, strategy-tag promo
only, structured Book key); the build brief was drafted +
locked (491 lines); Code executed the full build (§5.1–§5.8)
in one session, both suites green, settlement seam untouched;
build report triaged clean. BetLog is built and ready for live
validation.

**Opened:** 2026-06-20 10:50 ACST
**Closed:** 2026-06-20 16:27 ACST
**Tool routing:** Claude Chat (review triage, scope amendment,
build-brief drafting, build-report triage) + Desktop Commander
(filesystem, scope edit, brief write). Code commissioned
out-of-session for the BetLog build; the build report is the
triage target.
**Governing DRs:** DR-019 (derived P&L on read), DR-021
(timestamps), DR-022 (account/book vocab — filters), DR-030
(module boundaries — new bets router), DR-031 (`uv run pytest`
gate), DR-032 (Betfair canonical — leg ids + cycle axis).
DR-027/028 named explicitly out-of-scope (BetLog is pure
operational store, no capture.db).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
  → `2026-06-20 10:50 ACST`
- Close: same command → `2026-06-20 16:27 ACST`

## Pre-flight checks (open ritual)

Drift-check clean: `current_state.md`, `SESSION_170.md`, and
`v3_build_picture.md` all stamped 2026-06-20 10:41 ACST (S170
close). `.close_out_backups/` held only
`SESSION_171_opening_prompt.md` — no stale prior prompt. No
phantom files at root. Same-workday open (S170 closed 10:41,
S171 opened 10:50 — a nine-minute continuation). The BetLog
review report was present (operator ran it out-of-session
between S170 and S171), so the S171 gate was cleared.

## Session shape

A full triage → build → triage arc in one session, spanning
two out-of-session Code-adjacent gaps (the operator ran the
codebase review before the session, and ran the build during
it). Three strands:

**First, triage the BetLog review report.** Code's read-only
review (`betlog_review_report.md`, 568 lines) came back
**buildable with adjustments — no blocker.** Walked the
operator through the three adjustment points that carried a
call (the other three were Claude's dev-lead territory): the
review answered the S169 delete-semantics question cleanly
(hard-delete only when unsettled AND un-cycled), and surfaced
two more — how much promo detail the log shows, and which key
the Book filter uses.

**Second, lock the three calls + amend the scope.** Operator
locked: (1) **hard delete** for the clean deletable case
(pending + standalone); (2) **strategy-tag promo display
only** (Option A) — no bet→promo join, since v3 has no FK from
a bet to its promo terms; (3) **structured Book key**
(`account_at_book_id → books.book_id`), not the free-text
`book_or_exchange`, because an account-health lens that
silently misses bets is worse than useless. The promo call
touched the locked scope, so `betlog_scope.md` was amended
(S171 note + the trimmed "promo detail" line).

**Third, draft + lock the build brief, then triage the
build.** Drafted `betlog_build_brief.md` (491 lines, 12
sections) end-to-end off the review's file+line anchors — the
full BetLog build contract (read + edit/delete, the "Placed?"
confirm scaffolded inert, the settlement seam ringed off).
Provided the ready-to-paste Code prompt. Code executed the
**full build §5.1–§5.8 in one session** (no split), came back
green, and the report triaged clean.

## What was delivered

1. **BetLog review report triaged — "buildable with
   adjustments."** Overall read (area H) is a go; nothing in
   the locked scope is contradicted by the v3 code. Six
   adjustments, three Claude-side (feed/filter build, P&L
   reuse, frontend wiring) and three operator calls (below).

2. **Three operator calls locked.**
   - **Delete:** hard-delete only when the bet is BOTH
     unsettled AND un-cycled; everything else is edit-not-
     delete. Hard (no trace), since it only ever fires on a
     standalone mistake bet.
   - **Promo display:** strategy-tag granularity only (Option
     A). Row shows the strategy tag + "Free" marker; tuck-in
     shows the free-bet conversion rate. No fine print — not
     stored against the bet in v3; revisit when free-bet
     credit-in lands a real promo record.
   - **Book filter:** structured `account_at_book_id →
     books.book_id` key, not free-text `book_or_exchange`.

3. **`betlog_scope.md` amended (S171).** Status line carries
   an S171 amendment note; the "Full promo terms" tuck-in line
   trimmed to strategy-tag granularity. No other scope change.

4. **BetLog build brief — locked.** Written to
   `interface_triage/betlog_build_brief.md` (491 lines, 21,586
   bytes, sha256 `0558fb6f1afa713b…`). 12 numbered sections:
   what-it-is, why, pre-reads, system access, the eight build
   pieces (§5.1–§5.8), sequencing, test baselines, the
   settlement-seam do-not-touch boundary, output spec, hard
   limits + dirty-tree, what-happens-after, cross-refs. Read-
   write on named v3 anchors only; backend-complete-and-tested
   named as the sanctioned stop-point if Code ran long.

5. **Ready-to-paste Code prompt** provided at hand-off (read-
   and-confirm gate, settlement seam, dirty-tree rules, test
   gate, single output file, stop condition).

6. **BetLog build — executed by Code, triaged clean.** Full
   §5.1–§5.8 in one session, no split. Python 1028 → 1092
   (+64), frontend 91 → 99 (+8), 0 regressions, `tsc -b`
   clean. Settlement/placement seam byte-identical by hash
   (`settlement.py` / `reconciliation.py` / `orchestrator.py`
   / `placement.py`). New router `ui/api/routers/bets.py`;
   store-pure read/edit/delete methods; P&L reused (no
   recompute, no third commission constant); frontend BetLog
   page with inert "Placed?" scaffold. Report at
   `betlog_build_report.md` (453 lines).

## Build-report triage — flagged decisions

Code flagged four build decisions (none touched the locked
scope; none required a scope amendment):

1. **`cycle_id` filter added** to `list_bets` + GET param +
   `count_bets_by_cycle` — in direct support of the §5.8 /
   §A.4 cycle-chain tuck-in. Claude-side software call; clean.
2. **"Pending" toggle includes `provisional`** (in-settlement-
   review), alongside NULL + pending. Surfaced to operator as
   the one thing they'll *see* differently — flagging it as
   redirectable if they'd rather in-review bets sat separately.
   The delete fence stays stricter (never deletes provisional)
   — correct.
3. **Date-range lexicographic compare** on ISO `placed_at` —
   follows existing precedent; DST-straddle edge only. No new
   behaviour. Silent (no operator angle).
4. **Labels joined from active reference maps** — an archived
   account-at-book shows null persona/book name (falls back to
   `book_or_exchange` for the book label). Display nicety,
   rare at day-0. Filter keys drift-free regardless.

**Carried (not resolved):** the `promo_events` delete pre-check
keys on the `correlation_id` candidate-forms of `cycle_id`;
the exact stored form wasn't traceable without `.db` access
(out of scope). Built conservatively (raw + prefix-stripped +
normalised-UUID candidates + a `foreign_keys=ON` backstop),
and a promo referent on an un-cycled+unsettled deletable bet
is near-impossible by construction. Parking-lot: confirm-and-
tighten next time a live-DB look is open. Surfaced to operator;
no action now.

## Standing-instruction adherence check

- **Cat 1 (brevity, decision-maker framing, call-driven
  surfacing, inventory-first triage):** honoured. Led with the
  call at each turn. The build-report triage ran inventory-
  first — four flagged decisions classified, only the two with
  an operator angle surfaced (provisional-in-Pending; the
  promo-events caveat), the rest named as clean software
  adaptations per the S163 don't-enumerate-dev-lead-calls rule.
  Three triage calls surfaced one at a time, each with plain-
  language stakes.
- **Cat 2 (session protocol):** timestamps anchored open +
  close (DR-021). Session record written. Opening prompt
  generated without being asked. Ready-to-paste Code prompt
  provided at hand-off without being asked (S163). Forward
  routing operator-confirmed (BetLog built → live validation →
  brief 2).
- **Cat 3 (filesystem + tooling):** Desktop Commander used
  exclusively; `bash_tool` not touched. Scope re-read live
  before the amendment (empirical-verification rule). Brief
  written chunked + verified (line/byte/sha + section grep).
  Single-target `edit_block`s for the scope amendment (dry-run-
  exempt). Skills read before use (open, brief-drafting,
  close).
- **Cat 4 (governance framing):** cycle convention respected —
  the build treats `cycle_id` as the single-unit key. Plain
  operational framing on the triage (account-health lens, what
  you'll see on the Pending filter).
- **Cat 5 (division of labour):** software/architecture calls
  made autonomously (new router vs extend, repository method
  vs raw SQL, P&L reuse, the backend stop-point split).
  Operational/usability calls put to the operator (the three
  locked calls; provisional-in-Pending). The delete call
  correctly stayed as an operator call (hard vs soft) even
  though the code answered the safety boundary.
- **Google Drive auto-sync:** not prompted at close.

## Open items

Pointer-only — full detail in `current_state.md`.

**Promoted for Session 172:**
- **Draft the manual-entry brief (brief 2)** — opens with the
  capture.db retention check (read-only, VPS via SSH tunnel,
  `start_process` Python, never copy; DR-027/028 re-read
  trigger).

**Carried:**
- **Free-bet credit-in brief (brief 3)** — S168 design, lands
  the "Placed?" write into the scaffold BetLog left.
- **Launcher brief** — F9 throttle-to-disk + F10 port override
  (consider F12). Pending, independent.
- Governance: formalise the S168 credit-in design as a short
  DR or Session 70 amendment — operator's call, deferred.
- **BetLog promo-events delete-check** — confirm-and-tighten
  the `correlation_id` form next time a live-DB look is open.
- Parking-lot items (unchanged) — see `current_state.md`.

## Open items out

- **Triage the BetLog review report** — done; "buildable with
  adjustments," three calls locked. ✅
- **Draft the BetLog build brief** — done; locked at 491 lines,
  handed to Code, executed, triaged clean. ✅
- **The three triage calls** (delete / promo / book) — locked. ✅
- **BetLog build itself** — Code built §5.1–§5.8 in one
  session, both suites green, seam untouched, triaged clean.
  BetLog now exists in v3 as a built page (pending live
  validation). ✅

## Session close state

- Rebuild folder root: clean, no phantom files.
- `interface_triage/`: two new files this session
  (`betlog_build_brief.md` 491 lines, `betlog_build_report.md`
  453 lines); `betlog_scope.md` amended (S171 note + promo
  trim). All prior files unchanged.
- `standing_instructions.md`: untouched this session (no new
  instructions surfaced). KB re-upload still pending operator-
  side (carried from S163 — unchanged).
- `v3_build_picture.md`: updated at this close (Interface
  refinement next-milestone moved — BetLog built; next is live
  validation + brief 2).
- `.close_out_backups/`: holds `SESSION_172_opening_prompt.md`
  after this close (S171 prompt removed).

## Forward routing

**S172 drafts the manual-entry brief (brief 2)** —
date/venue/race-number/runner → capture.db → Betfair stamp →
write. Opens with the capture.db retention check (how many days
back resulted races are kept), read-only against capture.db
(VPS via SSH tunnel, `start_process` Python, never copy;
DR-027/028 re-read trigger). Then brief 3 (free-bet credit-in,
the "Placed?" write) and the launcher brief.
**Between sessions:** operator validates BetLog live — launch
v3, open the BetLog tab, eyeball real bets. **Confirmed with
operator** — the locked three-brief sequence + launcher, with
BetLog now built and ready to look at. No committed cutover
date; ready beats rushed.
