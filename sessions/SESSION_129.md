# Session 129 — W14.1 report triaged clean; W14 + W14.1 → `done`; loose-typing row repository surface locked as v3 convention for W13 / W15 reuse; W13 becomes next active stream

**Opened:** 2026-05-12 16:05 ACST
**Closed:** 2026-05-12 19:16 ACST
**Wall-clock:** ~3h11m elapsed. Same-workday open relative
to S128 close (14:18 ACST same day, 107-minute gap). No
day-rollover, no pause-and-resume. Triage-only session
with operator-facing surfacing of three findings; bulk
of the elapsed clock was between-message read/think time
on the operator side, not active Claude work.

**Tool routing:** Claude Chat for all work. Substantive
reads: `current_state.md`, `standing_instructions.md` in
full, `project_context.md`, `sessions/SESSION_128.md`,
`dr029/w14_cash_flow/w14_1_adapter_brief.md` (1,586
lines), `dr029/w14_cash_flow/w14_1_adapter_report.md`
(923 lines), `v3_build_picture.md`. Two `start_process`
calls for Adelaide-local timestamp anchors (open / close)
plus pre-flight + post-close directory listings. No Code
dispatch this session, no VPS access, no Betfair API,
no live DB writes, no v3 codebase edits. All deliverable
work is governance paperwork at close.

**Governing DRs invoked:** DR-021 (Adelaide local time
anchoring, open / close). DR-030 (v3 module-boundary
discipline + Session 124 amendment — **the load-bearing
reason W14.1 existed**; restored at W14.1 ship per
Code's `lint-imports` 5 kept / 0 broken). DR-027
(two-database architecture + Session 124 amendment —
per-domain event-table internal shape unchanged).
DR-019 (derived state on read — cash flow events
read-derived asymmetry carries through unchanged).
DR-022 (book / account / account-at-book vocabulary —
FKs unchanged).

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
→ `2026-05-12 16:05 ACST`.
**Close:** same command → `2026-05-12 19:16 ACST`.

Same-workday open relative to S128 close (14:18 ACST
same day, 107-minute gap). No day-rollover this session.
No pause-and-resume.

## Pre-flight checks

Drift-check at open held clean. `current_state.md`
last-updated 2026-05-12 14:18 ACST matched S128 close
timestamp. `v3_build_picture.md` last-updated 14:18
ACST also matched. `sessions/SESSION_128.md` present
(664 lines).

**Pre-flight directory listing:** rebuild folder root
clean. Expected `.md` files at root plus
`v3_build_picture.md` plus `openapi.json` plus
`external_api_resources.md` plus expected directories
(`agent_review/`, `diagrams/`, `dr029/`,
`orchestration_pack/`, `sessions/`, `skills/`,
`.close_out_backups/`). `.close_out_backups/` held
only `SESSION_129_opening_prompt.md` (the active one,
correct state). No phantom files, no stale backups.

**Gate condition for S129 open held:** Code's W14.1
report present at the named path
`dr029/w14_cash_flow/w14_1_adapter_report.md` (923
lines). The operator-side action between S128 and S129
(dispatch Code against the W14.1 brief; ensure Code
writes the report at the named path before opening
S129) closed cleanly.

**Drift event at open:** none. The Cat 1 silent
session-open ritual held this open — orientation
summary delivered as a single combined brief at the
end of the ritual, no step headers in operator-facing
text. S125 / S127 / S128 broke; S126 and S129 held.
Three-out-of-five window now. Pattern is fragile but
not stuck-broken; operator's S128 hold-without-
escalation call ("*It's already working fairly well.*")
remains current.

## Session shape

Triage-only session — Code's W14.1 report on disk at
session open, three plausible forward routes named in
the W14.1 brief §10 (clean close / W14.2 / partial-
ship). Four phases across the wall clock.

**Phase 1 — Open + orientation.** Anchor + required
reads + pre-flight directory listing + drift-check.
Calendar-calibrated tight recap delivered (3 sentences
on S128 substantive landings + objective for S129 +
inline naming of the load-bearing gate verification
outcome from Code's report summary). Inline render of
`v3_build_picture.md` (state moved since previous open
— S128 close updated the artefact, W14.1 sub-stream
added). Open-items delta rendered (closed: operator-
side dispatch of Code; new: three findings to triage).
Hand-off question on whether to start with verification
posture or jump straight to finding (a).

**Phase 2 — Findings walk-through at materiality-
weighted depth.** Operator requested findings walked
through "in the appropriate detail, depending on
materiality and significance" in plain language with
decisions and recommended next steps surfaced. Three
findings walked:

- **Finding (a) — brief §5.1 vs §5.2 inconsistency on
  repository constructor.** Brief's adapter sample
  used `CashFlowEventRepository(conn)`; shipped W14
  took `db_path`. Code bridged by changing both
  repository `__init__` signatures to take a
  `Connection`. Plain-language framing: drafting
  error on Claude's side at S128; Code spotted and
  fixed in flight; no operational consequence. Decision
  required: none — Code's bridge call endorsed.
  Materiality: low.
- **Finding (b) — `object`-typed row repository
  surface.** Repository can't import from `domain/`
  per DR-030, so its row-level methods take `object`
  rather than `UUID` / `CashFlowEventType`. Code added
  a small `.value`-duck-typed helper to handle event-
  type strings vs enums. Two alternative paths Code
  surfaced (tighten to `str` and bear adapter-side
  cast cost; introduce a dedicated `store/types`
  module). Plain-language framing: not a data-
  integrity concern (DB still enforces every
  constraint; adapter is the only real-world caller
  and is strict; mypy / ruff both clean); a code-
  shape choice between tidier code and one extra
  layer of static type-check protection that nothing
  in v3 will stress-test. Decision required: confirm
  or override the v3 pattern lock for W13 / W15.
  Materiality: moderate (locks a software convention
  for the next two operational data stores).
- **Finding (c) — file-size overruns above §7.3
  ballparks.** Three of the new / edited files run
  ~6–20% over the brief's rough size guides. The
  brief explicitly framed §7.3 as "rough guides —
  not hard limits". Per S120 standing rule
  (length-bends-to-required-detail). Decision
  required: none. Materiality: low (informational).

**Phase 3 — Operator request for plain-language
re-explanation of (b).** Operator surfaced unease
about the word "loose" — instinct that loose typing
might create data integrity problems down the line.
Re-explained in plain analogy terms: the database
itself enforces every constraint at write time
(rock solid in both options), and "loose" only
refers to how strict the data store's reception desk
is about checking inputs before passing them to the
strict betting window behind it. Three load-bearing
points named for the operator: (1) database
enforces every constraint at write time regardless;
(2) only one piece of code in production (the
adapter) calls the data store, and that adapter is
strict; (3) mypy / ruff both pass clean — no hidden
type problem. The only place looseness could bite
is if something *bypassed* the adapter — and v3's
architecture doesn't allow that. Operator confirmed
understanding and locked Claude's recommendation
("*Happy with your recommendation.*").

**Phase 4 — Close-out paperwork.** Session record
(this file) + `current_state.md` rotation +
`v3_build_picture.md` update (W14 row drops per one-
session-carry; W14.1 row drops per one-session-carry;
W13 transitions from `blocked-on-W14` to `in flight`;
W12 / W15 updated to `blocked-on-W13`) + S130 opening
prompt generation + `.close_out_backups/` sweep +
post-close verification.

## Structural drift surfaced this session

**None.** No standing-instruction edits, no governance-
artefact structural changes, no scope drift on any
labelled workstream. The session was clean triage with
one operator-confirmation decision.

**One pattern observation worth recording (not drift,
not a sweep candidate):** the W14.1 close arc validated
the option-1 mid-session scope expansion call at S128
— S128 + S129 collapsed the W14 close-out arc by one
session (original routing was S128 triage / S129 brief
draft / S130 triage; option-1 collapsed to S128 triage
+ brief draft / S129 triage). Pre-execution risk
advisory (added S126, Cat 3) exercised proactively
at S128 made the call cleanly. Pattern stable across
S126 → S127 → S128 → S129; remains a sweep candidate
for promotion-to-encoded-rule at S130 if it holds.

## What was delivered

Three substantive outcomes plus close-out paperwork:

**1. W14.1 report triage decision: clean close.**

All gate posture from Code's W14.1 report verified at
S129:

- **`lint-imports`:** 5 kept / 0 broken — the load-
  bearing gate W14.1 was commissioned to fix is
  clean. DR-030 restored.
- **pytest tests/:** 624 passed (was 596 pre-baseline).
  Net +28 from 38 new adapter tests + 27 reshaped
  row-level repository tests + 10 relocated schema
  tests minus 47 W14 tests that moved.
- **pytest tests/store/repositories/test_cash_flow_*.py:**
  37 passed (10 schema unchanged, 27 reshaped row-
  level repository).
- **pytest tests/workflows/cash_flow/v1/:** 38 passed
  (adapter).
- **mypy** on `workflows/cash_flow` plus
  `store/repositories/cash_flow.py`: clean.
- **ruff check** on all touched files: clean.
- **§7.4 smoke:** 8/8 event types round-trip through
  the adapter, supersession-chain walk and
  latest_non_superseded both work end-to-end.
- **Dirty-tree:** HELD. HEAD unchanged at
  `2329604aa80b34937a24644ea2eb18477749be85`. 10
  modified entries preserved; one new `??
  workflows/cash_flow/` entry. No git side-effects.

W14 + W14.1 → `done`.

**2. Three findings triaged.**

- **(a) Brief constructor inconsistency** — Code's
  bridge call (both repository `__init__` signatures
  changed from `db_path` to `Connection`) endorsed
  retroactively. Closed.
- **(b) `object`-typed row repository surface** —
  locked as the v3 convention for W13 / W15 per
  operator confirmation. The pattern: row-level
  repositories accept `object` for ID types that
  live in `domain/`, with a small per-repository
  helper (`_event_type_value` for W14 cash flow;
  W13 / W15 to draft their own equivalents) to
  normalise enum-vs-string at the boundary. Adapter
  layer remains strictly Pydantic-typed. The
  alternative paths Code surfaced (tighten to `str`;
  introduce `store/types` module) are rejected at
  this lock. Carry-forward to W13 / W15 brief
  drafting: brief drafts name the pattern
  explicitly so brief-vs-substrate alignment doesn't
  drift the way it did for W14.1's adapter
  constructor sample.
- **(c) File-size overruns above §7.3 ballparks** —
  acknowledged. No action. Per S120 standing rule.

**3. Forward routing locked: W13 becomes the next
active stream.**

W13 (promos / free-bet inventory — promo eligibility,
free-bet inventory event types per `architecture.md`
§A.4, promo cash credits, cycle linkage to bet
records per DR-032 canonical-reference-layer)
transitions from `blocked-on-W14` to `in flight`.
S130 shape: W13 brief drafting in a fresh session.
The W14.1 row-only-repository + workflow-side-
adapter pattern is the v3 convention W13 inherits.

W12 and W15 statuses updated:

- W12 (balances — read-side derivation): stays
  `blocked-on-W13-and-W14`, but the W14 dependency
  is now retired (W14 closed); rephrased
  `blocked-on-W13`.
- W15 (operations log): transitions from
  `blocked-on-W14` to `blocked-on-W13`.

W17 / W16 / W18 / P1 / P2 unchanged.

**4. Close-out paperwork landed in-session.**

This file (`sessions/SESSION_129.md`), `current_state.md`
rotation, `v3_build_picture.md` update (W14 + W14.1
both `done` and dropping per one-session-carry; W13 →
`in flight`; W12 / W15 dependency phrasing updated),
`.close_out_backups/SESSION_130_opening_prompt.md`
written, stale `SESSION_129_opening_prompt.md`
deleted from backups.

## Standing-instruction adherence check

- **Cat 1 silent session-open ritual — HELD this
  open.** No step headers in operator-facing text;
  orientation delivered as single combined brief.
  S125 / S127 / S128 broke; S126 / S129 held. Three-
  out-of-five window. Sweep candidate continues
  carrying without escalation per S128 operator call.
- **Cat 1 silent session-close ritual** — held this
  close. Step labels suppressed in operator-facing
  text; only this session record + a single brief
  one-line post-close output to surface.
- **Cat 1 V3 build picture conditional render at
  open — spirit-of-the-rule heuristic** — rendered
  at open this session (stream state had moved at
  S128 close — W14.1 sub-stream surfaced). Nine
  consecutive clean applications (S121–S129).
  Pattern stable; promotion-to-encoded-rule remains
  the next step.
- **Cat 1 calendar-calibrated session open** — held.
  Same-workday tight recap delivered.
- **Cat 1 drift-check** — held at open
  (`current_state.md` + `v3_build_picture.md` +
  `SESSION_128.md` all anchored at 14:18 ACST
  matching S128 close).
- **Cat 1 open-items delta — conditional** —
  rendered at open (meaningful delta: operator-side
  dispatch closed, three findings surfaced for
  triage).
- **Cat 1 tightened response register (Session
  114)** — held. Findings walked at materiality-
  weighted depth per operator's explicit request;
  plain-language re-explanation when operator
  surfaced unease about (b); no over-surfacing of
  software-call detail beyond what the operator's
  decision required.
- **Cat 1 inventory-first cadence on long technical
  reports (added Session 114, surfaced Session
  113)** — held in Phase 2. Three W14.1 findings
  inventoried; two classified as no-decision-
  required (a) and (c); one classified as operator-
  call (b). Plain-language framing for (b) per Cat 1
  register.
- **Cat 1 call-driven surfacing during section-by-
  section drafting (Session 84)** — N/A this session
  (no multi-section artefact drafting).
- **Cat 1 render review content with hard line wraps**
  — held. No fenced review content this session
  (no artefact drafts surfaced).
- **Cat 2 timestamp anchor at session open + close**
  — held. Open 16:05 ACST; close 19:16 ACST.
- **Cat 2 required reads at session open** — held.
  Read `current_state.md`, `standing_instructions.md`
  in full, `project_context.md`,
  `sessions/SESSION_128.md`,
  `dr029/w14_cash_flow/w14_1_adapter_brief.md` in
  full, `dr029/w14_cash_flow/w14_1_adapter_report.md`
  in full, `v3_build_picture.md` in order.
- **Cat 2 pre-flight directory listing** — held at
  open. No phantom files; expected state. Gate
  condition for S129 open (Code's W14.1 report on
  disk) verified at this check.
- **Cat 2 governing DRs named in orientation** —
  held (DR-030 + DR-027 + DR-019 + DR-021 all named
  with bracketed plain-language reminders).
- **Cat 2 persist-drafted-but-not-assembled artefact
  content to scratch** — N/A this session. No draft
  content produced.
- **Cat 2 surface structural-drift in session
  record** — held. No structural drift surfaced;
  recorded as none above.
- **Cat 2 workstream-label / build-picture
  coherence at close (Session 115)** — held. W14
  + W14.1 → `done` (matches brief contract);
  W13 → `in flight` (no scope drift on the W13
  label — what S130 brief-drafts against is what
  the picture has said about W13 since S117 re-cut);
  W12 / W15 dependency phrasing updated.
- **Cat 2 re-validate queued work-items at execution
  time (Session 114)** — held. The S129 opening
  prompt's primary queue item ("triage Code's
  W14.1 report") was re-validated at session open
  via the gate-condition check (report present at
  named path before substantive work began) and
  again in Phase 2 (findings inventoried explicitly
  against the brief's §10 triage shape, not
  trusted blindly).
- **Cat 3 empirical-verification-before-editing** —
  N/A this session. No governance-artefact edits
  beyond close-out paperwork.
- **Cat 3 `create_file` banned** — held. All writes
  via `Desktop Commander:write_file`.
- **Cat 3 verify-every-write** — held. Each
  `write_file` followed by a verification read or
  post-close directory listing.
- **Cat 3 dry-run multi-target mechanical edits** —
  N/A this session. No multi-target scripted edits.
- **Cat 3 REPL discipline** — N/A this session. No
  multi-line Python invocations.
- **Cat 3 pre-execution risk advisory (added S126)**
  — N/A this session (no high-risk operation).
  Fourth session of observation; pattern stable.
  Carry-forward sweep candidate.
- **Cat 4 divergence-capture-or-fix** — N/A this
  session. No substrate divergences. Finding (a)
  was a brief-spec internal inconsistency caught and
  bridged by Code; finding (b) was a row-vs-domain
  type question with no substrate divergence; finding
  (c) was a length-target overrun within explicitly-
  soft guides.
- **Cat 5 software-questions-are-Claude's** — held.
  All three findings were software-shaped; (a) and
  (c) handled in Claude's territory; (b) framed as
  operator-call only because it locks a v3
  convention with downstream cost, not because the
  technical detail was operator-shaped.
- **Cat 5 make-software-calls-don't-punt (Session
  114)** — held. (b) was framed as recommendation
  with rationale ("My call: accept Code's choice
  as-is"), not as "A or B, your call?". Operator's
  "*Happy with your recommendation.*" exercised the
  locked call.
- **Cat 5 cosmetic-calls-default-to-Claude's-pick**
  — N/A this session.
- **Cat 5 length targets bend to required detail
  (Session 120)** — referenced when surfacing
  finding (c). The standing rule held W14.1's file-
  size overruns as no-action.

## Open items in / out

Pointer-only — full detail in `current_state.md`
post-rotation.

**Closed in Session 129:**

- **W14 (transactions / cash-flow event log) →
  `done`.** Substrate shipped at S127, refactored to
  DR-030 compliance at W14.1 (S128 brief / Code
  execution between sessions / S129 triage). All
  load-bearing gates clean. Drops from
  `v3_build_picture.md` next session per one-
  session-carry rule.
- **W14.1 (DR-030 surgical fix — cash flow
  adapter) → `done`.** First surgical-fix sub-
  stream in the v3 build proper arc. Ships one new
  adapter file
  (`workflows/cash_flow/v1/cash_flow_store_adapter.py`),
  trims `store/repositories/cash_flow.py` to row-
  only, moves W14 test files to
  `tests/store/repositories/`, adds adapter test
  file at `tests/workflows/cash_flow/v1/`. Pattern
  becomes the v3 convention W13 / W15 inherit.
  Drops from `v3_build_picture.md` next session
  per one-session-carry rule.
- **W14.1 report triage** — completed. Three
  findings classified: (a) closed via Code's bridge;
  (b) locked as v3 convention; (c) acknowledged
  informational.
- **Operator-side action (dispatch Code against
  W14.1 brief)** — closed. Code session ran out-
  of-session between S128 close and S129 open;
  report written at the named path.
- **Stale `SESSION_129_opening_prompt.md` backup**
  — swept at S129 close.

**New from Session 129 (PRIMARY for Session 130):**

- **W13 brief drafting.** W13 (promos / free-bet
  inventory) is `in flight`; S130's primary
  deliverable is drafting the W13 brief for Claude
  Code dispatch. Brief drafts against:
  `architecture.md` §A.4 (promo event types:
  credited / deployed / revoked / expired), DR-032
  (canonical-reference-layer; bet records carry the
  cycle linkage), the row-only-repository +
  workflow-side-adapter pattern locked at W14.1
  (W13 brief explicitly names this pattern), and
  the per-domain event-table pattern established
  at W14. Target shape: similar architectural
  envelope to W14's brief but smaller surface
  (promo events do not carry the same supersession
  complexity as cash flow events).

**Carry-forward dependencies (sensitivity flags
unchanged from S123 / S125 / S126 / S127 / S128):**

- **Hedge classification (DR-025, Finding #8 from
  S123).** Revisit before W15 brief drafting.
  Strategy 2 cycle measurement implications. Not
  S130 territory.
- **§2.4 Fix 4 cadence design dependency (Finding
  #3 from S123).** Fix 4 must verify capture
  cadence brackets near-jump placements tightly.
  Not S130 territory.

**Tracked carry per operator instruction (carried
from S118 / S119 / S120 / S121 / S122 / S123 / S125
/ S126 / S127 / S128):**

- **Alembic adoption.** Locked migration tool per
  DR-031, deferred. Sequenced after W13 + W12 land.
  W13 brief carries the deferral; W13 uses the
  existing pre-Alembic schema unchanged.

**Carried forward (sweep candidates):**

- **Cat 1 silent session-open ritual narration
  drift — sweep candidate, FRAGILE BUT NOT STUCK-
  BROKEN.** S125 / S127 / S128 broke; S126 / S129
  held. Three-out-of-five window. Operator declined
  promotion-to-encoded-rule at S128. Sweep
  candidate continues carrying without escalation.
- **Cat 1 build-picture conditional render
  heuristic — formalisation candidate.** Nine
  consecutive clean applications (S121–S129).
  Pattern stable; promotion to encoded rule remains
  the next step.
- **Cat 3 pre-execution risk advisory (added
  S126).** Fourth session of observation. Pattern
  stable. Promotion-to-encoded-rule candidate at
  S130 / S131 if it holds. Validated at S129 in
  retrospect: option-1 call at S128 collapsed the
  W14 close-out arc by one session and shipped
  clean.
- **Cat 4 divergence-capture-or-fix elevation
  candidate.** No fresh instance S129. Pattern held
  as sensitivity, not encoded. Review after a few
  sessions of W13 / W12 brief drafting where
  divergence is more likely to surface.

**Carry-forward operational (Sessions 108 / 109
carry):**

- Settings-area cadence follow-up brief — open;
  waits on operational experience.
- Greyhound operational constraint verification —
  open.
- `betfair_adapter.py` single-file mypy cleanup —
  low priority.

## Session close state

- **rebuild folder root:** expected `.md` files
  present plus `v3_build_picture.md` plus
  `openapi.json` plus `external_api_resources.md`
  plus expected directories. No phantom files.
- **WIP:** no scratch writes this session. No draft
  content produced.
- **`.close_out_backups/`:**
  `SESSION_129_opening_prompt.md` deleted at this
  close; `SESSION_130_opening_prompt.md` written.
  Post-close state: single file
  (`SESSION_130_opening_prompt.md`) only.
- **`sessions/` folder:** Sessions journal complete
  through S129.
- **`dr029/w14_cash_flow/`:** holds W14 brief, W14
  report, W14.1 brief, and W14.1 report. Read-only
  reference material going forward; no further
  W14.x sub-streams expected.
- **Project knowledge base:** unchanged this
  session (no `standing_instructions.md` edits).
  No operator-side re-upload action required.
- **`bethub-v3/`:** unchanged this session beyond
  Code's W14.1 execution between sessions. HEAD at
  `2329604aa80b34937a24644ea2eb18477749be85`
  (carried forward from W14 close per Code's W14.1
  dirty-tree handling).
- **`current_state.md`:** rotated this close;
  last-updated 2026-05-12 19:16 ACST.
- **`v3_build_picture.md`:** updated this close
  (W14 + W14.1 both transition to `done`; W13 →
  `in flight`; W12 dependency rephrased
  `blocked-on-W13`; W15 dependency rephrased
  `blocked-on-W13`); last-updated 2026-05-12 19:16
  ACST.
- **`standing_instructions.md`:** unchanged this
  session. No edits.

## Forward routing

**Confirmed forward routing for S130:** W13 brief
drafting.

**S130 shape:** fresh session opens against W13 as
the active stream. Reads: `current_state.md`,
`standing_instructions.md` in full, `project_context.md`,
`sessions/SESSION_129.md`, `architecture.md` §A.4
(promo event spine), `decisions.md` DR-030 + DR-032
amendments, `dr029/w14_cash_flow/w14_1_adapter_brief.md`
(pattern precedent — W13 explicitly inherits the row-
only-repository + workflow-side-adapter shape).
Triggers `bethub-brief-drafting` skill. Drafts W13
brief end-to-end across chunked `write_file` calls
to `dr029/w13_promos/w13_promos_brief.md` (folder
fresh; needs creation). Brief target ~1,200–1,600
lines following the W14 / W14.1 envelope.

W13 brief substantive scope (provisional, locked at
S130 draft):

- Schema: `promo_events` table per per-domain event-
  table pattern (DR-027 amendment). Promo event
  types per `architecture.md` §A.4: credited
  (free-bet inventory in), deployed (free-bet used
  on a bet), revoked (free-bet withdrawn by book),
  expired (free-bet lapses), cash-credit (promo
  cash credited to account-at-book), cash-credit-
  used (cash credit consumed). Six event types
  provisional; final list locked at brief draft.
- Domain layer: Pydantic models for each event type,
  FK rules per type, Adelaide tz validation,
  `PAYLOAD_BY_EVENT_TYPE` dispatch following W14
  precedent.
- Repository: row-only per the W14.1 v3 convention.
  `object`-typed surface for IDs and event types
  per finding (b) lock. Small per-repository helper
  (`_promo_event_type_value` equivalent) for enum-vs-
  string normalisation at the boundary.
- Adapter: at `workflows/promos/v1/promo_events_store_adapter.py`
  per the W14.1 layout precedent.
- Tests: schema (W11 / W14 layout) +
  row-level repository + adapter-level Pydantic.
  Net test count target similar to W14.1 (~70–80
  tests across the three suites).
- Cycle linkage to bet records per DR-032
  canonical-reference-layer.

**Possible S130 pivots:**

- **Operator surfaces a W13 scope addition.** Most
  likely shape is operator wanting promo cycle
  analytics surfaced explicitly (e.g. linkage to
  Strategy 1 Safety Net cycles, free-bet realised-
  rate per S88 §5.8 carry). Drafted in brief if
  warranted.
- **Operator surfaces a W14.2 follow-up after re-
  reading the S129 triage.** Low probability given
  the operator's clean-close confirmation, but the
  W14.1 report's three findings remain on the
  record; reopening any of them is operator's call.
- **Standing-instruction sweep before W13 brief
  drafting.** Three sweep candidates carrying
  (silent-ritual-at-open / build-picture render
  heuristic / pre-execution risk advisory). S130 /
  S131 sit in the window where promotion-to-
  encoded-rule could fire. Operator's call;
  default is to keep carrying.

**Out of scope for S130** (unless triage routes a
different direction):

- W12 brief drafting (sequenced after W13).
- W15 brief drafting (sequenced after W13).
- DR-025 hedge revisit (parked for pre-W15).
- §2.4 Fix 4 cadence design (independent arc).
- Promotion of any sweep candidate to encoded
  standing instruction (operator's call at S130
  open if exercised).

---

**Session 129 closes W14 + W14.1 cleanly.** The first
per-domain event log workstream ships with the v3
convention W13 / W15 reuse: per-domain event table
internal shape (DR-027 amendment) + closed enum
domain layer + row-only repository (DR-030 +
loose-typing surface lock) + workflow-side adapter +
schema / row-level / adapter-level test split. W13
(promos / free-bet inventory) becomes the next
active stream; S130 drafts the brief.
