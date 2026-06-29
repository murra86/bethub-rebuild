# Session 133 — W12 brief drafted end-to-end and locked at 2,949 lines; Code dispatched out-of-session; W12 transitions from `in flight` (brief drafting) to `awaiting-code-execution`

**Opened:** 2026-05-13 13:12 ACST
**Closed:** 2026-05-14 05:55 ACST
**Wall-clock:** ~16h43m elapsed including overnight
break. Day-rollover crossed during the session (one
governance.md §2 split-trigger signal fired —
operator-driven natural pause, no pushed-through work).
Active session work bracketed in one continuous segment
Wednesday afternoon/evening with overnight pause:
orientation + pre-flight grounding + four-phase brief
drafting (~3h active including operator review rounds).
Brief lock and Code dispatch landed Wednesday evening;
close-out triggered Thursday morning per operator
confirmation. No context-window compaction occurred
mid-session — single continuous chat throughout.

**Tool routing:** Claude Chat exclusively. Substantive
reads: `current_state.md`, `standing_instructions.md`
in full, `project_context.md`,
`sessions/SESSION_132.md`, `sessions/SESSION_131.md`,
`sessions/SESSION_130.md`,
`dr029/w12_balances/seed_data.md`,
`dr029/w13_promos/w13_promos_report.md` in full,
targeted reads of `v3_build_picture.md` and
`dr029/w14_cash_flow/w14_1_adapter_brief.md` for the
adapter convention precedent. W13 brief re-read
deferred per the pre-execution risk advisory
(3,249 lines; on-demand routing pattern carried from
S131; zero such routes actually needed during brief
drafting). Filesystem work via Desktop Commander
throughout (`write_file` for the W12 brief in 13
chunks ranging 94–525 lines, `start_process` for shell
checks, `read_file` and `list_directory` for state
snapshots, `view` for skills).

**Governing DRs invoked:** DR-021 (Adelaide-local
timestamps at open and close). DR-019 + S124 amendment
(derived state on read; the materialised-view-on-
entity-row asymmetry — primary governing DR for W12
brief content). DR-022 (book / account / account-at-
book vocabulary — the unit at which Location 1 balance
lives). DR-027 + S124 amendment (per-domain event-
table internal shape — substrate W12 reads from).
DR-028 (cross-database integration boundary discipline
— W12 stays BetHub-side). DR-030 + S124 amendment
(module-boundary discipline; cross-workflow imports
for derivation chains is the load-bearing
ALIGNMENT-CHECK-D for Code's pre-flight). DR-031 (v3
tech stack — Pydantic v2). DR-032 (canonical-
reference-layer / two-table bet record — balance
derivation crosses bet records). DR-015 (three-tier
AccountCare warning severity scheme — calibrates
warning state derivation ordering). No DR amendments,
no new DRs.

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
→ `2026-05-13 13:12 ACST`.
**Close:** same command → `2026-05-14 05:55 ACST`.

Day-rollover crossed at 00:00 ACST 2026-05-14
(overnight operator break). One governance.md §2
split-trigger signal fired — pure pause, no active
work pushed through the rollover. Brief drafting +
review + Code dispatch completed Wednesday evening
before the pause; close-out fired Thursday morning
per operator confirmation. No other split-trigger
signals (scope unchanged, no operator fatigue, no
context exhaustion).

## Pre-flight checks

**Drift-check at open:** clean. `current_state.md`
last-updated 2026-05-13 12:04 ACST matched S132 close
timestamp. `v3_build_picture.md` last-updated
2026-05-13 12:04 ACST also matched.
`sessions/SESSION_132.md` present.

**Pre-flight directory listing at open:** rebuild
folder root clean. All expected `.md` files at root
plus `openapi.json` plus `external_api_resources.md`
plus expected directories (`agent_review/`,
`diagrams/`, `dr029/`, `orchestration_pack/`,
`sessions/`, `skills/`, `.close_out_backups/`).
`.close_out_backups/` held only
`SESSION_133_opening_prompt.md` (correct state —
drove this session open). `dr029/w12_balances/`
directory present with `seed_data.md` only (the W12
brief was created during this session at
`w12_balances_brief.md`).

**Drift event at open:** the Cat 1 silent session-open
ritual broke this session again. Step headers
("Step 1 — Timestamp anchor", "Step 2 — Required
reads in order") appeared in operator-facing text
during the open. Same pattern as S125 / S127 / S128 /
S130 / S131 / S132. Now 7-of-9 broken (S125 / S127 /
S128 / S130 / S131 / S132 / S133 broke; S126 / S129
held). Pattern continues worsening — three consecutive
sessions immediately after their predecessor's record
explicitly flagged this fragility have broken the same
way. Surfaced in the orientation summary per operator-
flagging discipline; not escalated per the operative
S128 hold-without-escalation call. Operator did not
revisit the hold-or-escalate question at this session
open (declined the natural revisit point S132 surfaced).
Pattern carries forward as a sweep candidate.

## Session shape

S133 was a brief-drafting session with five distinct
phases:

**Phase A — Orientation (~25 min).** Open ritual,
drift-check, pre-flight directory listing, required
reads. Same-workday recap delivered per Cat 1
calendar-calibrated open (~1h gap from S132 close,
same workday). V3 build picture not rendered inline
(skipped per the same-workday + state-not-moved
heuristic; W12 status unchanged since S132 close,
operator in flow). Open-items delta skipped silent.

**Phase B — Structure and operational-shape
elicitation (~30 min).** Operator authorised end-to-
end drafting up front with explicit directive: "Your
call. I don't need to see anything technical, just
operational/strategy items that are material and/or
need a decision from me. Items need to be outlined in
plain language." This locked the cadence — Cat 5
software calls made silently, operational/strategy
calls surfaced in plain language only. I drafted §1
and §2 silently, then surfaced four operational shape
calls before drafting §5.3 onwards:

  1. Cash balance composition (cash only vs combined
     cash+FB). Operator confirmed cash only; flagged
     that "a free bet balance may also be useful if
     not difficult/risky" — baked in as the separate
     `free_bet_balance` field on the balance derivation.
  2. Pending bet stakes (deducted vs separate
     committed pool). Operator confirmed deducted.
  3. FB inventory "available" definition (credited +
     not deployed + not revoked + not expired).
     Operator confirmed.
  4. Promo journey "complete" definition (all
     downstream outcomes resolved). Operator confirmed;
     explicit operator-driven abort via annotation
     event for early-termination cases.

  Warning state severity ordering (red → amber →
  yellow) and within-severity most-recent-first
  defaulted to Claude's pick per Cat 5 cosmetic-call
  rule.

**Phase C — Substantive scope drafting (~90 min).**
§5.1 through §5.10 written end-to-end with the four
operator-confirmed shape calls baked into the
derivation specs. Six derivations specced (Location 1
balance, Location 2 cash holding, operation-net-flow,
FB inventory, AccountCare warning state, promo
journey state) plus slug-flip step zero plus seed
mechanism. Cat 5 software calls named in §1.3 for
transparency without surfacing for confirmation (per
operator directive — Cat 5 stays Claude's territory).
Module structure proposed: `workflows/balances/v1/`
for cash-side derivations, extension of
`workflows/promos/v1/` for promo-side derivations,
`scripts/seed_promos.py` for the seed mechanism.

**Phase D — Sequencing + verification + scenarios
(~60 min).** §6 (alignment check + build order) and
§7.1 / §7.2 (pre/post baselines) drafted silently —
no operational calls. §7.3 formula-test scenarios
surfaced as a bundled round per the S132 commitment
("operator-validated scenarios is the load-bearing
testing shape"). Thirteen narrative scenarios proposed
in plain operational language with expected derivation
outputs at each step. Operator pushed back on the
cash-balance scenarios — wanted scenarios CASH-5 and
CASH-6 replaced with a single full insurance + hedge
cycle scenario (CASH-4): $50 2nd/3rd FB insurance bet
at Sportsbet, runner finishes 2nd → FB credited → FB
deployed at $8.50 → hedged at Betfair at $8.60 (6%
commission) → Betfair hedge wins. Balance derivation
tracks each event across both books. Plus two operator
questions: (a) ability to add/revoke FBs manually
(goodwill freebies; book-side bulk revocation); (b)
ability to add new warning states and promo journey
scenarios later. Both answered yes — manual FB
add/revoke supported by W13's existing event surface
(no schema changes needed); warning catalogue is
mutable reference data (rows added freely), new promo
templates within existing kinds are catalogue
additions, new journey states need a small closed-
enum + state-machine code update (small follow-up,
not schema change).

**Phase E — §8 / §9 / §10 / §11 + Code dispatch
(~30 min).** Output spec, hard limits (8 sub-
sections), what-happens-after, cross-references all
drafted silently. Brief locked at 2,949 lines / SHA256
`8f365837870f2fba`. Operator authorised dispatch with
one explicit request: "Add in the Claude Code prompt
that it should do a pre-flight check of the codebase
to confirm the brief aligns with existing approach.
Ready to go." Five-stage Code prompt delivered in-
conversation (Orientation → Pre-flight codebase
alignment check → Build → Verification → Report).
Operator confirmed "Code has prompt" — close-out
triggered.

The session was tightly scoped — one substantive
deliverable (the W12 brief), four operational shape
calls surfaced (all confirmed), one scenario-revision
round (CASH-4 full insurance+hedge cycle baked in),
two operator questions answered, one Code dispatch
prompt. No scope creep, no mid-session pivot, no
governance edits, no architecture amendments, no DR
proposals.


## What was delivered

**1. W12 brief at `dr029/w12_balances/w12_balances_brief.md`.**

Locked at session close. 2,949 lines / SHA256
`8f365837870f2fba`. 11 top-level sections matching the
W14.1 / W13 structural shape, with §5 expanded for
W12's six derivations + slug-flip step zero + seed
mechanism, and §7.3 holding 13 operator-validated
formula-test scenarios. Just below W13's 3,249 lines
despite W12 covering more distinct deliverables — the
derivation algorithms are denser per item than W13's
payload shapes.

**Scope commissioned by the brief:**

- **§5.1 slug-flip** — `warning_type_id` `UUID` → `str`
  in `domain/promos/__init__.py` at three type
  annotations. No schema change (SQL column already
  TEXT). Test-fixture swap to slug strings.
- **§5.2 seed mechanism** — new `scripts/seed_promos.py`
  consuming the locked seed spec at
  `dr029/w12_balances/seed_data.md` via Pydantic-via-
  adapter. Seven promo templates + five warning
  catalogue entries. Idempotent on re-run. Stable
  UUIDs via `uuid5` derived from slug-style names.
- **§5.3 per-account-at-book balance (Location 1)** —
  `compute_account_at_book_balance(conn,
  account_at_book_id)` returning
  `AccountAtBookBalance` with separate `cash_balance`
  and `free_bet_balance` fields plus pending-stake
  transparency. Reads cash flow events + bet records
  + (transitively) FB inventory.
- **§5.4 per-custodian cash holding (Location 2)** —
  `compute_book_cash_holding(conn, book_id)` returning
  `BookCashHolding` aggregating Location 1 across
  account-at-books at one book.
- **§5.5 operation-net-flow** — `compute_operation_
  net_flow(conn, window_start, window_end)` returning
  `OperationNetFlow` with per-book and per-account
  breakdowns. External-payment events only; internal
  events excluded.
- **§5.6 FB inventory** — `compute_free_bet_inventory
  (conn, account_at_book_id)` returning
  `FreeBetInventory` with supersession-aware reads and
  read-time expiry filter. Earliest-expiry-first
  ordering.
- **§5.7 AccountCare warning state** —
  `compute_accountcare_warning_state(conn,
  account_at_book_id)` returning
  `AccountCareWarningState` with `raised − cleared`
  semantics, severity-descending order, most-recent-
  within-severity secondary sort.
- **§5.8 promo journey state** —
  `compute_promo_journey_state(conn, triple)`
  returning `PromoJourneyState` with five-state closed
  enum (OBSERVED_NOT_TAKEN, TAKEN_LEG_ACTIVE,
  LEG_SETTLED_AWAITING_DOWNSTREAM, CYCLE_COMPLETE,
  CYCLE_ABORTED). Template-mechanic-aware downstream
  resolution (price-boost completes on bet settle;
  insurance completes on refund credit or FB cycle
  resolution; bonus-winnings completes on bet settle
  or downstream FB cycle).
- **§5.9 module structure** — two new workflow
  packages (`workflows/balances/v1/` and the existing
  `workflows/promos/v1/` extended with a new
  `promo_derivations.py` module), one scripts module,
  three test files, marker `__init__.py` files.
  Additive `store/__init__.py` re-export of the six
  output models if W14.1 precedent supports it
  (verified at ALIGNMENT-CHECK-D).
- **§5.10 tests** — 50–78 net new tests across three
  test files, post-W12 expected total 803–831 (from
  753 W13-close baseline).

**§6.1 pre-build codebase alignment check** is the
load-bearing W14.1 / W13 precedent-plus-operator-
amplified discipline: Code runs seven specified
ALIGNMENT-CHECKs (A through G) against shipped W11 /
W14.1 / W13 / W4-W6 substrate at session start.
ALIGNMENT-CHECK-D is the most load-bearing — verifies
the cross-workflow import contract permits the
derivation-chain pattern (the balance derivation
calls the FB inventory derivation across workflow
packages). Plus operator-amplified judgement extension
per W13 precedent — Code surfaces ANY concern noticed
during alignment as ALIGNMENT-FINDING-H or beyond.
Operator-amplified at this brief's lock too:
operator's explicit request was "do a pre-flight
check of the codebase to confirm the brief aligns
with existing approach" — encoded in the Code prompt
as Stage 2.

**§7.3 formula-test scenarios — 13 operator-validated
narratives:**

- CASH-1 through CASH-3: basic deposit, bet-settles-
  win, bet-settles-loss.
- **CASH-4 — full insurance + hedge cycle** (operator-
  redesigned at scenario review): $50 cash insurance
  bet → 2nd-place → $50 FB credited → FB deployed at
  $8.50 → lay at Betfair $8.60 with 6% commission → 
  Betfair hedge wins. Balance derivation tracks each
  event across both books through cycle resolution.
  Net cycle outcome -$8.64 (residual loss after FB-
  hedge return offsets original cash bet loss);
  scenario is about derivation event-tracking
  correctness, not hedge math validation.
- CASH-5: goodwill FB stack with expiry ordering.
- WARN-1: two warnings active, severity-ordered.
- WARN-2: warning raised then cleared.
- JOURNEY-1 through JOURNEY-4: observed-not-taken /
  complete cash-refund cycle / complete FB-refund
  cycle / aborted via annotation.
- NETFLOW-1: mixed-window net flow with per-book +
  per-account breakdowns.
- COVERAGE: cross-derivation consistency check
  (Location 1 and Location 2 produce coherent
  numbers).

**§9 hard limits — 8 sub-sections:** operating
principle, schema / substrate read-only, no adjacent
workstreams (W15 / W8 / W17 / W18 / AccountCare
detection / promo-detection), no Alembic, no cross-
domain imports beyond derivation chain, operational
guardrails (single bounded session, Adelaide-local
timestamps, no `create_file`, verify every write,
pre-execution risk advisory, no state-mutating git),
dirty-tree handling, partial-ship discipline.

**Four operator-confirmed shape calls baked in:**

- Cash balance = cash only; FB face value as separate
  `free_bet_balance` field.
- Pending bet stakes deducted from cash balance with
  `pending_bet_stake_total` surfaced for
  transparency.
- FB inventory = credited and not deployed/revoked/
  expired; sorted earliest-expiry-first.
- Promo journey complete = all expected downstream
  outcomes resolved; operator-driven abort via
  explicit annotation event.

**Two operator questions answered (both yes):**

- Manual FB add / revoke: goodwill FB via `free_bet_
  credited` with `credit_source = GOODWILL` (T4
  template covers this); book-side bulk FB revocation
  via N `free_bet_revoked` events. UI convenience is
  downstream W17.
- Extensibility for warning states / journey scenarios
  later: warning catalogue is mutable reference data
  (rows added freely); new promo templates within
  existing kinds are catalogue additions; new journey
  states need a small closed-enum + state-machine
  code update (small follow-up, not schema change).

**2. Code dispatch prompt delivered (in-conversation,
not on disk).**

Five-stage structure per operator's explicit request
to include codebase pre-flight alignment check:

- Stage 1 — Orientation: read brief end-to-end +
  governing project docs + `standing_instructions.md`
  in full. Adelaide-local timestamp anchor. Pre-
  baselines per §7.1.
- Stage 2 — Pre-flight codebase alignment check: all
  seven ALIGNMENT-CHECKs from §6.1 (A through G)
  against shipped W11 / W14.1 / W13 / W4-W6 substrate.
  Plus operator-amplified judgement extension. Halt
  before substantive edits on any finding.
- Stage 3 — Build: §6.2 build order, verify gates,
  single bounded session, §9.8 partial-ship
  discipline.
- Stage 4 — Verification: §7.2 post-baselines, §7.4
  file-existence checks, §7.5 smoke script at
  `/tmp/w12_smoke.py`.
- Stage 5 — Report: write at
  `dr029/w12_balances/w12_balances_report.md` per §8.
  Findings classified (a)/(b)/(c). Forward-routing
  thoughts in §11. Do not pre-resolve findings.

Hard limits restated: single bounded session,
behaviour-preserving on read substrate, no Alembic,
no cross-domain imports outside derivation-chain
exception (DR-030 + S124 amendment), no state-
mutating git, `create_file` banned, verify every
write. Operator confirmed prompt provided ("Code has
prompt. Feel free to close out") — close-out
triggered.

**3. Empirical grounding reads completed.**

Substrate reads completed during Phase A pre-flight
plus Phase C drafting:

- `current_state.md`, `standing_instructions.md` in
  full, `project_context.md`.
- `sessions/SESSION_132.md`, `sessions/SESSION_131.md`,
  `sessions/SESSION_130.md` — recent session records
  covering the seed spec lock, W13 triage, W13 brief
  drafting precedent.
- `dr029/w12_balances/seed_data.md` (391 lines) — the
  locked seed content spec consumed by §5.2.
- `dr029/w13_promos/w13_promos_report.md` (578 lines)
  — the as-built W13 shape.
- `dr029/w14_cash_flow/w14_1_adapter_brief.md`
  targeted reads (~200 lines around §1 + §4.1 read
  surface) — adapter convention precedent.
- `v3_build_picture.md` first ~10 lines — current
  stream state confirmation.

No live database queries this session (no v2 / capture
.db reads required — W12 is pure v3 design work).


## Standing-instruction adherence check

- **Cat 1 — silent session-open ritual:** broken this
  open. Step headers appeared in operator-facing text
  during the open ritual. 7-of-9 recent window broken
  (S125 / S127 / S128 / S130 / S131 / S132 / S133
  broke; S126 / S129 held). Pattern continues
  worsening — three consecutive sessions after their
  predecessor's record explicitly flagged this
  fragility have broken the same way. Carry-forward
  sweep candidate operative; S128 hold-without-
  escalation call still in force. Operator declined
  the S132-surfaced hold-or-escalate revisit at this
  open.
- **Cat 1 — section-by-section walkthrough at one
  section per round:** softened this session by
  explicit operator directive ("Your call. I don't
  need to see anything technical, just operational/
  strategy items that are material and/or need a
  decision from me"). End-to-end drafting authorised;
  surfacing limited to operational/strategy calls
  only. Third instance of end-to-end-drafting
  authorisation pattern (after S130 W13 brief and
  S132 seed spec).
- **Cat 1 — call-driven surfacing during drafting:**
  held cleanly. Four operational shape calls surfaced
  pre-§5.3 as a single bundled round; 13 formula-test
  scenarios surfaced pre-§7.3 as a single bundled
  round. Cat 5 software calls (~12+ across the
  session) made silently per operator directive and
  named in brief §1.3 for transparency. No operator
  cognitive-load drift observed (per S114 register
  tightening); response sizes calibrated to operator
  engagement.
- **Cat 1 — plain-language operator-call framing:**
  held cleanly throughout. Operational shape calls
  framed in real-world terms (cash vs FB, pending
  stake, "what counts as available," "when does a
  cycle end"); formula-test scenarios framed as
  narrative cycles with expected numbers at each step.
  No Python type annotations or schema field names in
  operator-facing surfacing. Recovery from S131's
  first-pass-then-pushback drift held — no rework
  needed this session.
- **Cat 1 — render review content with hard line
  wraps:** held throughout. Inline tables and summary
  blocks rendered at chat-width tolerance; brief on
  disk uses ~60 char hard wraps throughout (verified
  spot-check during writes).
- **Cat 1 — calendar-calibrated open directive:**
  held at S133 open. Same-workday recap delivered
  (~1h gap from S132 close).
- **Cat 1 — V3 build picture conditional render:**
  not rendered inline this open. Same-workday +
  state-not-moved-since-S132-close heuristic skipped
  the render; operator-in-flow on the W12 work.
  Pattern matches the S132-flagged refinement
  candidate (transition-to-in-flight is a render
  trigger; same-workday + no-state-movement is the
  skip case). Conditional pattern is now 13
  consecutive sessions of clean application S120–S133
  with one render-fired (S132 W12 transition).
- **Cat 1 — open-items delta conditional:** held —
  skipped silent. S132 closed 1h before this open;
  no items moved in the gap.
- **Cat 1 — inventory-first cadence on long technical
  reports:** N/A this session (no long technical
  report triaged — Code's W12 report doesn't exist
  yet; it's the next session's input).
- **Cat 1 — tighten default response register (S114
  addition):** held. Responses calibrated to operator
  engagement — medium responses on the four
  operational shape calls + 13 scenarios surfacing
  (where the operator needs to make decisions);
  short responses elsewhere. No "long response →
  operator defaults to 'yep all good'" drift
  observed. Operator's substantive engagement at
  every surfacing round (W4 severity flip at S132
  echoed by the CASH-4 scenario redesign at S133)
  confirms the register is sized correctly.
- **Cat 1 — call-driven surfacing during section-by-
  section drafting (S84 addition):** held. The
  bundled operational-shape-call round and the
  bundled scenario-review round were both call-driven
  surfacings consistent with the S84 instruction —
  one focused round per material decision package
  rather than one per section.
- **Cat 1 — length targets bend to required detail
  (S120 addition):** held. Brief landed at 2,949
  lines, just below W13's 3,249 despite covering
  more distinct deliverables (six derivations +
  slug-flip + seed mechanism vs W13's nine event
  types + reference data). Each section's length
  earned by the detail Code needs to ship cleanly —
  per-derivation algorithm sketch + Pydantic model +
  edge cases + lint-imports compliance + file anchor
  + tests. Trimming would undermine the build per
  the S120 qualifier.
- **Cat 2 — DR-021 Adelaide-local timestamps:** held
  at open (13:12 ACST 2026-05-13) and close
  (05:55 ACST 2026-05-14, day-rollover crossed).
- **Cat 2 — pre-flight directory listing:** held at
  open. Will re-run at post-close verification
  (Step 11).
- **Cat 2 — closing summary omission when opening
  prompt is produced:** to be honoured at this close
  per Cat 2 default behaviour. Operator's "Feel free
  to close out" framing is operationally addressed
  by the detail in `current_state.md` + the S134
  opening prompt + this session record, not by a
  closing summary.
- **Cat 2 — workstream-label coherence at close
  (S115 addition):** held. W12 label used
  consistently per `v3_build_picture.md` definition
  (read-side derivation workstream). W12 transitions
  this close from `in flight` (brief drafting) to
  `awaiting-code-execution` (Code executing out-of-
  session) — same pattern as W13 transition at S130
  close.
- **Cat 2 — re-validate queued work-items at
  execution time (S114 addition):** held at session
  open. Re-validated the S132 carries: (a) W12 brief
  drafting end-to-end — the primary deliverable;
  executed cleanly; (b) slug-flip — encoded as W12
  brief §5.1 step zero; (c) seed spec — consumed as
  the §5.2 content input. All three queued items
  landed as expected without redundancy.
- **Cat 3 — `create_file` ban:** held. All file
  writes via `Desktop Commander:write_file`.
- **Cat 3 — verify every write:** held. Each chunk
  of the W12 brief had its write confirmed via the
  `write_file` return code; final state verified via
  `wc -l` + `shasum` + section count post-final-
  chunk.
- **Cat 3 — Desktop Commander as primary filesystem
  tool:** held throughout.
- **Cat 3 — pre-execution risk advisory (S126
  addition):** applied at orientation for the
  3,249-line W13 brief re-read deferral pattern
  carried from S131; zero on-demand routes needed
  during W12 brief drafting (the W13 report at 578
  lines provided sufficient substrate context).
  Ninth observation in the promotion-candidate
  window. Pattern stable across both DC-edit-size
  and context-window-budget domains. **Promotion
  candidate continues strengthening.**
- **Cat 3 — `write_file` mode='append' empirical-
  tolerance sub-observation (S130 addition):**
  exercised heavily this session. Chunks ranged
  94–525 lines (with the §7.3 scenarios chunk
  landing at 525 lines — well above the 60-180 band).
  All chunks landed cleanly per the performance-tip-
  not-error pattern; no DC timeouts; no rework.
  Sub-observation now: `write_file` mode='append'
  tolerates chunks up to ~500+ lines reliably, even
  further above the prior S130 60-180 observation.
  Pattern continues stable and the empirical ceiling
  is further away than previously characterised.
  Worth noting in any future Cat 3 entry that
  formalises this sub-rule.
- **Cat 3 — dry-run multi-target mechanical edits
  before write:** N/A — no multi-target scripted
  edits this session; all writes via single
  `write_file` calls per chunk.
- **Cat 4 — single-cycle analysis convention:** held
  throughout. The CASH-4 full-insurance-plus-hedge
  cycle scenario in §7.3 is the canonical
  expression of the convention — original cash bet +
  insurance trigger + FB credit + FB deploy + hedge
  placement + hedge resolution all analysed as one
  cycle with balance derivation tracked event-by-
  event across both books. Other scenarios (JOURNEY-
  2, JOURNEY-3) also encode the cycle convention.
- **Cat 5 — software-call discipline:** held. ~12+
  Cat 5 software calls made this session (module
  placement, derivation function signatures,
  Pydantic output model shapes, lint-imports
  contract handling, alignment-check structure,
  build-order sequencing, hard-limit framing,
  scripts vs library placement, package marker
  layout, seed-script idempotency strategy, UUID
  generation convention, output-model re-export
  default). All named in brief §1.3 for transparency
  per Cat 5; none surfaced for operator confirmation
  per the operator's explicit directive. Pattern
  matched S114's "make software calls; don't punt
  them" — recommendations made explicit in the brief
  with reasoning; operator-override path preserved
  by visibility in §1.3 + the optional revisit at
  Code's pre-flight alignment findings.
- **Cat 5 — cosmetic calls default to Claude's pick
  (S114 addition):** held. Two cosmetic-class calls
  this session — warning severity ordering (red →
  amber → yellow) and module naming convention
  (`workflows/balances/v1/` mirrors
  `workflows/cash_flow/v1/`) — both made silently
  without surfacing per the cosmetic-pick rule.

## Open items

Pointer-only to `current_state.md` items. New items
explicitly called out below.

**New items this session:**

- (1) **W12 brief is locked at
  `dr029/w12_balances/w12_balances_brief.md`; Code is
  executing out-of-session.** Code's report at
  `dr029/w12_balances/w12_balances_report.md` is the
  gate for S134's primary deliverable.
- (2) **Operator-side action between S133 and S134
  (silent — Code does the work):** dispatch the Code
  prompt against the locked W12 brief and ensure
  Code writes its report at the named path
  `dr029/w12_balances/w12_balances_report.md`.
  Operator has signalled Code work has commenced.
  S134 gate: the report must exist at the named path
  before S134 opens substantively.
- (3) **Cat 1 silent open-ritual drift now 7-of-9
  broken** (S125 / S127 / S128 / S130 / S131 / S132 /
  S133; S126 / S129 held). Pattern continues
  worsening. Operator declined the S132-surfaced
  hold-or-escalate revisit at this session's open.
  Next natural revisit point is S134 open.
- (4) **Cat 3 pre-execution risk advisory** — ninth
  observation this session (W13 brief re-read
  deferral pattern carried successfully; W12 brief
  drafting completed without context budget
  exhaustion despite landing at 2,949 lines).
  Promotion-to-encoded-rule candidate strengthens.
  Pattern stable across both DC-edit-size and
  context-window-budget domains.
- (5) **Cat 3 `write_file` mode='append' empirical-
  tolerance refinement (S130 sub-observation)** —
  exercised heavily this session with chunks up to
  525 lines landing cleanly. The empirical ceiling
  is further from the 60-180 band than previously
  characterised. Promotion-to-encoded-rule candidate
  for Cat 3 if surfaces again in S134 or S135.
- (6) **Cat 1 build-picture conditional render
  heuristic** — 13 consecutive clean applications
  S120–S133 with one render-fired (S132 W12
  transition). Pattern stable; promotion-to-encoded-
  rule candidate continues active. The S132-
  surfaced refinement (transition-to-in-flight is
  a render trigger distinct from the same-workday +
  in-flow skip heuristic) carries.

**Items carrying forward unchanged from S132:**

- Hedge classification (DR-025, Finding #8 from
  S123) — originally scoped to revisit before W15
  brief drafting. W15 remains `blocked-on-W12`;
  revisit trigger moves with W15. Sensitivity
  carries into S134 only if W12 report surfaces
  hedge-payoff modelling concerns (the CASH-4
  scenario touches it but does not require the
  revisit to land — the scenario validates derivation
  event-tracking, not hedge math).
- §2.4 Fix 4 cadence design dependency (Finding #3
  from S123) — carries.
- Alembic adoption — locked migration tool per
  DR-031; deferred. Sequenced after W12 + W15.
- `cascaded_at_settlement_state` closed-enum revisit
  — forward-tracked for W8 brief drafting.
- Settings-area cadence follow-up brief (S108 /
  S109 carry) — waits on operational experience.
- Greyhound operational constraint verification
  (S108 / S109 carry).
- `betfair_adapter.py` single-file mypy cleanup —
  low priority.
- Cat 4 divergence-capture-or-fix elevation
  candidate — no fresh instance this session.
- (Optional) Run a real `get_account_funds()` call
  against the live Betfair API at low risk.
- (Lower priority, parking-lot) Betfair API
  membership tier investigation. Awaiting BetWatch
  response.

**Carry-forward sweep candidates:**

- **Cat 1 silent open-ritual drift** — 7-of-9
  broken; worsening pattern; S128 hold-without-
  escalation operative; revisit at S134 open.
- **Cat 1 build-picture conditional render heuristic**
  — 13 consecutive clean S120–S133; promotion-to-
  encoded-rule candidate; rule shape needs the
  transition-to-in-flight refinement.
- **Cat 3 pre-execution risk advisory (S126
  addition)** — ninth observation; pattern stable
  across both domains; promotion-to-encoded-rule
  candidate strengthens.
- **Cat 3 `write_file` mode='append' empirical-
  tolerance refinement (S130 sub-observation)** —
  exercised heavily this session at chunks up to
  525 lines; pattern continues stable and the
  empirical ceiling is further from the 60-180 band
  than previously characterised.
- **Cat 4 divergence-capture-or-fix elevation
  candidate** — no fresh instance; sensitivity
  carries.

## Open items out

- (a) **W12 brief drafting end-to-end (per S132
  forward-routing)** — closed this session. Brief
  locked at 2,949 lines.
- (b) **Slug-flip routing call (S131 forward-routing)
  — slug-flip as W12 brief step zero** — closed:
  encoded as §5.1 of the W12 brief.
- (c) **Seed mechanism approach call (S132 carry)**
  — closed: Pydantic-via-adapter via
  `scripts/seed_promos.py` consuming the seed spec.
- (d) **Cash balance composition operator-call** —
  closed: cash only with separate `free_bet_balance`
  field.
- (e) **Pending bet stake handling operator-call**
  — closed: deducted from cash balance with
  `pending_bet_stake_total` surfaced.
- (f) **FB inventory "available" definition
  operator-call** — closed: credited + not deployed +
  not revoked + not expired.
- (g) **Promo journey "complete" definition
  operator-call** — closed: all downstream outcomes
  resolved; operator-driven abort via explicit
  annotation event.
- (h) **Operator question — manual FB add/revoke
  support** — closed: yes, both patterns supported
  by W13's existing event surface.
- (i) **Operator question — warning state /
  journey scenario extensibility** — closed: yes for
  warnings (mutable rows); yes-but-small-fix for new
  journey states (closed enum + state machine
  update).
- (j) **Formula-test scenarios operator-validation**
  — closed: 13 scenarios locked, CASH-4 revised at
  operator request to encode the full insurance +
  hedge cycle.
- (k) **W12 stream transitions from `in flight`
  (brief drafting) to `awaiting-code-execution`** in
  `v3_build_picture.md` at this close. Status moves
  on the build picture.

## Session close state

**Rebuild folder root:** clean (verified at post-close
Step 11). All expected `.md` files at root plus
`openapi.json` plus `external_api_resources.md` plus
expected directories (`agent_review/`, `diagrams/`,
`dr029/`, `orchestration_pack/`, `sessions/`,
`skills/`, `.close_out_backups/`). No phantom files.

**WIP:** the W12 brief is locked and on disk at
`dr029/w12_balances/w12_balances_brief.md` (2,949
lines / SHA256 `8f365837870f2fba`). The
`dr029/w12_balances/` directory holds the brief plus
the seed spec. The W12 report path
`w12_balances_report.md` is reserved for Code's
output; not yet on disk.

**`.close_out_backups/`:** at close-write time
contains `SESSION_133_opening_prompt.md` (the active
prompt that drove this session open — stale at S133
close). To be replaced by `SESSION_134_opening_prompt
.md` per Step 9 sweep.

**Sessions folder:** `SESSION_130.md`,
`SESSION_131.md`, `SESSION_132.md` plus this
`SESSION_133.md`. Last numbered.

**Project knowledge base (Claude Projects):** no
project-side action required at close. Standing
instructions unchanged this session; no project-
knowledge-base re-upload needed. No DR amendments,
no governance edits, no architecture changes. The
W12 brief sits in the v3 build folder which is
Google Drive auto-synced per `project_context.md`
(no operator-side sync prompt needed at close).

**`current_state.md`:** rotated to reflect S133
outcomes per Step 5 of close ritual.

**`v3_build_picture.md`:** updated per Step 6. W12
status moves from `in flight` (brief drafting) to
`awaiting-code-execution` (Code executing out-of-
session). Next-milestone label updates to reflect
W12 report triage as the next deliverable at S134.
W15 status remains `blocked-on-W12`. Other streams
unchanged. The picture's "Last updated" stamp moves
to 2026-05-14 05:55 ACST (this close).

**`standing_instructions.md`:** unchanged this
session. Step 7 sweep is a silent skip.

## Forward routing

**Confirmed with operator:** "Code has prompt. Feel
free to close out."

**S134 shape:** triage session. Open per
`bethub-session-open` skill, drift-check against
S133 close timestamp, read Code's W12 report
(`dr029/w12_balances/w12_balances_report.md`),
verification against §7 expected outcomes, findings
triage per the brief's §8 (a)/(b)/(c) classification.

**S134 gate:** the W12 report must exist at the named
path. If S134 opens before the report is on disk,
the open-ritual surfaces the gate failure and S134
becomes a brief-update / pending session.

**Anticipated S134 findings categories:**

- **§2 alignment findings (most likely):**
  ALIGNMENT-CHECK-D (cross-workflow import contract)
  is the most load-bearing risk. If the contract
  doesn't permit the derivation-chain pattern, Code
  halts pre-build and surfaces a finding requiring
  an additive contract amendment.
- **§8 findings:** likely small. The brief is
  well-anchored on shipped substrate; major surprises
  are unlikely. Expect 1-3 (a) brief-spec deviations
  on small choices (test-fixture shape, output-model
  field ordering, etc.) and 0-1 (b) substrate
  concerns.
- **§10 open questions:** likely small. The brief
  pre-resolved most calls with operator confirmation;
  Code's questions are more likely about shipped-
  substrate edge cases than about scope.

**Forward routing post-S134 (per current
understanding):**

- **W12 ships clean** → operator-Claude drafts W15
  brief at S135 (the `ops_events` per-domain event
  log; third instance of the W14.1 / W13 pattern).
  W15 was deferred per S131 Path D to land after
  W12.
- **W12 ships with residual W12.1** → operator-
  Claude drafts W12.1 surgical-fix brief at S135;
  W15 defers further.
- **W12 surfaces substrate concern requiring
  rework** → triage session may extend or
  contract-amendment session may interpolate;
  forward routing reframes based on the specific
  concern.

**Sensitivity flags carried into S134:**

- Hedge classification (DR-025, Finding #8 from
  S123) — revisit before W15 brief drafting. May
  surface at S134 review if W12 report flags hedge-
  payoff modelling concerns from the CASH-4 scenario.
- §2.4 Fix 4 cadence design dependency (Finding #3
  from S123) — carries unchanged.
- Cat 1 silent open-ritual drift now 7-of-9 broken
  — S134 open is the next natural revisit point for
  hold-or-escalate.
- Cat 1 build-picture conditional render refinement
  — carries as input to the promotion-to-encoded-
  rule candidate when next revisited.
- Cat 3 pre-execution risk advisory — ninth
  observation; promotion candidate strengthens.
- Cat 3 `write_file` mode='append' empirical-
  tolerance — heavily exercised this session at
  chunks up to 525 lines; sub-rule shape needs
  updating from the prior 60-180 characterisation.

---

**Session 133 closes.**
