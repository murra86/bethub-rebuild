# Session 130 — W13 brief drafted end-to-end and locked at 3,249 lines; Code dispatched out-of-session; W13 transitions from `blocked-on-W14` to `in flight`

**Opened:** 2026-05-12 19:25 ACST
**Closed:** 2026-05-13 08:47 ACST
**Wall-clock:** ~13h22m elapsed including overnight
break. Day-rollover crossed during the session (one
governance.md §2 split-trigger signal fired —
operator-driven natural pause, no pushed-through work).
Active session work bracketed in two segments: opening
ritual + pre-flight grounding (~25 min, S130 open
through structure proposal Tuesday evening), then full
brief drafting + operator review + Code dispatch
(~3.5h active, Wednesday morning). Context-window
compaction occurred between the two segments; the
mid-session compaction is captured in
`/mnt/transcripts/2026-05-12-22-57-41-w13-promos-brief-drafting.txt`
and was handled cleanly via context-load on resume.

**Tool routing:** Claude Chat for orchestration and
brief drafting. Substantive reads:
`current_state.md`, `standing_instructions.md` in full,
`project_context.md`, `sessions/SESSION_129.md`,
`dr029/w14_cash_flow/w14_1_adapter_brief.md` (substrate
template), W14 / W14.1 shipped code (`workflows/cash_flow/v1/cash_flow_store_adapter.py`
end-to-end, `store/repositories/cash_flow.py`
substantial pass, `domain/cash_flow/__init__.py`
through the payload subclasses, `store/schema/cash_flow.py`
head), decisions.md DR-030 + S124 amendment plus
DR-032 in full, architecture §A.4 by reference,
`workflows/burst_review/` live state (confirmed
empty), tests/workflows/cash_flow/v1/ + tests/store/repositories/
layouts. Filesystem work via Desktop Commander
exclusively (`write_file` for the brief in 31 chunks
ranging 60–180 lines, `start_process` for shell
checks, `read_file` for substrate reads,
`list_directory` for state snapshots). No Code
dispatch from Claude Chat — the dispatch prompt was
delivered to operator at close for out-of-session Code
execution; Code commenced work between brief lock and
session close.

**Governing DRs invoked:** DR-021 (Adelaide local time
anchoring throughout). DR-027 + S124 amendment
(per-domain event-table internal shape — `promo_events`
is the second instance W13 will ship). DR-030 + S124
amendment (v3 module-boundary discipline + the
locked `workflows/bet_entry/v1/` inversion and
`domain/accounts/` addition — W13 brief specs
compliance from session one). DR-019 + S124
amendment (derived state on read; the critical
asymmetry that `promo_events` is pure event-log
writes, materialised-view-on-entity-row applies to
bet records but NOT to `promo_events`). DR-022
(book / account / account-at-book vocabulary — FKs
on `promo_events` follow identically). DR-032
(canonical-reference-layer; `promo_events` payload
references to `bet_id` target the locked
`bets.bet_id` shape; SQL-level FK NOT enforced on
payload-JSON values per SQLite limitation).

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
→ `2026-05-12 19:25 ACST`.
**Close:** same command → `2026-05-13 08:47 ACST`.

Day-rollover crossed at 00:00 ACST 2026-05-13
(overnight operator break). One governance.md §2
split-trigger signal fired. No active work pushed
through the rollover — natural pause; resume happened
Wednesday morning. No other split-trigger signals
(scope unchanged, no operator fatigue, no context
exhaustion).

## Pre-flight checks

Drift-check at open held clean. `current_state.md`
last-updated 2026-05-12 19:16 ACST matched S129 close
timestamp. `v3_build_picture.md` last-updated 19:16
ACST also matched. `sessions/SESSION_129.md` present
(658 lines).

**Pre-flight directory listing:** rebuild folder root
clean. Expected files plus `.close_out_backups/`
holding only `SESSION_130_opening_prompt.md` (correct
state — that prompt drove this session open).

**Drift event at open:** the Cat 1 silent
session-open ritual broke this session. Step headers
appeared in operator-facing text during the open. Not
escalated per S128 operator hold-without-escalation
call; recorded here as a carry-forward sweep candidate
for the open-ritual pattern. Four-out-of-six window
across S125 / S126 / S127 / S128 / S129 / S130 (S126
and S129 held; S125, S127, S128, S130 broke). Pattern
is fragile.


**Compaction event mid-session:** context-window
compaction fired between Tuesday evening (pre-flight
grounding + structure proposal + first three §1
chunks of the brief written) and Wednesday morning
(brief completion + operator review + Code dispatch).
Transcript at
`/mnt/transcripts/2026-05-12-22-57-41-w13-promos-brief-drafting.txt`.
Compaction summary captured the in-flight state
cleanly and the morning resume read it accurately
before continuing. The brief was already partially on
disk before compaction (sections §1.1 through partway
through §7 of the brief); resume continued from §8
without rework.

**Apparent operator-message duplication after
compaction:** the operator's instruction message
"(i) is good. If you have the tools/context, draft
end-to-end and produce a short plain summary…" was
received twice — once before the compaction (acted on
as the original drafting instruction) and once after
the compaction (treated as a UI/retry artefact, not as
a restart-from-scratch directive). Continued drafting
from §8 rather than re-opening the brief. Worth
flagging here as a pattern observation; not escalated.

## Session shape

S130 was a brief-drafting session with three distinct
phases:

**Phase A — Pre-flight grounding (Tuesday evening,
~25 min).** Empirical reads against the W14.1
substrate (the v3 convention W13 inherits) plus the
W14 schema CHECK pattern plus the W14.1 test layout
plus the live state of `workflows/burst_review/`.
Surfaced two findings worth flagging at operator
proposal time: (1) W13's surface is materially bigger
than W14 — 9 event types vs 8, 3 reference tables vs
1; (2) `workflows/burst_review/` is empty (only
`__init__.py`), so cascade-trigger logic is genuinely
future work and W13 ships the write surface only.

**Phase B — Structure proposal + reference-table call
(Tuesday evening, single round).** Proposed the
W14.1-mirroring 11-section brief structure with
operator-requested §6.1 codebase-alignment check
embedded. Surfaced one operator-call: reference-table
approach — (i) ship all three reference tables fully,
(ii) DDL-only with SQL seeding deferred, (iii) pre-
split into W13a/W13b. Recommended (i). Operator
confirmed (i).

**Phase C — End-to-end brief drafting + operator
review + Code dispatch (Wednesday morning, ~3.5h).**
Drafted the W13 brief end-to-end across 31 chunked
`write_file` calls (compaction occurred mid-Phase-C,
between §6.2 close and §7.1 open; resume continued
cleanly). Final brief at 3,249 lines / 124,465 bytes
/ SHA256 7a0a3814deeadac4343d4f30644f911cbfa8b9fac0d9fb4ad055ed007e98fb41.
Operator review surfaced three operator-decisions
held; operator confirmed all three with implicit
trust in Claude's judgement on calls that align with
vision and don't constrain future builds. Code
dispatch prompt delivered; operator signalled Code
work had commenced; close-out triggered.

The session was tightly scoped — one substantive
deliverable (the W13 brief), one operator-call
surfaced (reference-table approach), one Code-dispatch
artefact (the dispatch prompt). No scope creep, no
mid-session pivot, no governance edits, no
architecture amendments, no DR proposals.


## What was delivered

**1. W13 brief at `dr029/w13_promos/w13_promos_brief.md`.**

Locked at session close. 3,249 lines / 124,465 bytes /
SHA256
`7a0a3814deeadac4343d4f30644f911cbfa8b9fac0d9fb4ad055ed007e98fb41`.
11 top-level sections (§1–§11), 24 sub-sections.
Structural shape mirrors W14.1's 1,586-line brief
template with §5 expanded for W13's larger surface
(9 event types, 3 reference tables, complex cascade
and FB deployment payloads).

**Scope commissioned by the brief:**

- New `store/schema/promos.py` — DDL for
  `promo_events` + 3 reference tables
  (`promo_template`, `promo`, `warning_catalogue`),
  9 indexes, CHECK constraints on closed-enum
  columns, `apply_migrations(conn)` idempotent
  migration. Mirrors `store/schema/cash_flow.py`.
- New `domain/promos/__init__.py` — Pydantic v2
  models per the 9 event types from architecture §A.4
  (`promo_observed` / `promo_journey_annotation` /
  `free_bet_credited` / `free_bet_deployed` /
  `free_bet_revoked` / `free_bet_expired` /
  `promo_cash_credited` / `accountcare_warning_raised` /
  `accountcare_warning_cleared`), reference data
  models (`PromoTemplate`, `Promo`,
  `WarningCatalogueEntry`), FK-nullability-per-event-
  type model validator,
  Adelaide-local tz validator, `PAYLOAD_BY_EVENT_TYPE`
  dispatch table. Mirrors `domain/cash_flow/__init__.py`.
- New `store/repositories/promos.py` — four row-only
  repository classes (`PromoEventRepository`,
  `PromoTemplateRepository`, `PromoRepository`,
  `WarningCatalogueRepository`) per the W14.1 v3
  convention. `object`-typed surface plus
  `_promo_event_type_value` helper for
  enum-vs-string normalisation. DR-030 compliant
  from session one (no `domain.promos` imports).
- New `workflows/promos/v1/promo_store_adapter.py` —
  Pydantic ↔ row translation surface, adapter-side
  payload reference validation (`promo_template_id` /
  `warning_type_id` / referenced-credit-event
  existence checks). Mirrors W14.1's
  `cash_flow_store_adapter.py`.
- Additive edit to `store/__init__.py` — adds
  `Promo*Repository` and error classes at
  alphabetical positions.
- Three new test files at the W14.1-locked layout
  (schema / repository / adapter) covering ~90–115
  net new tests.
- Five package marker `__init__.py` files
  (`workflows/promos/`, `workflows/promos/v1/`,
  `tests/workflows/promos/`, `tests/workflows/promos/v1/`,
  plus `domain/promos/__init__.py` is the
  substantive module not a marker).

**§6.1 pre-build codebase alignment check** is the
load-bearing W14.1-precedent-plus-operator-amplified
discipline: Code runs seven specified reads against
shipped W14.1 / W11 / burst_review substrate at
session start, surfaces any divergence as
ALIGNMENT-FINDING-A through G, halts substantive
edits on any finding. Operator amplified at close:
Code applies its own judgement beyond the seven
specified checks — surfaces ANY concern (spec
mismatch, future-builds risk, pattern drift) as a
finding rather than just executing the named seven.
This carries into the dispatch prompt's Stage 2.

**§9.1 partial-ship discipline** is the safety net
for W13's larger-than-W14 surface. If Code reaches
session-budget wall mid-build, halt at next coherent
boundary; S131 triages partial ship and decides
forward routing.

**Six Cat 5 software calls** named in brief §1.3:

- (1) Reference tables ship via option (i) — full
  schema + Pydantic + repo + adapter CRUD.
  **Operator-confirmed at structure proposal.**
- (2) Revocation and expiry as separate event types
  (not status-updates-via-supersession-of-credits).
  **Operator-confirmed at structure proposal** ("just
  leave it in. No use messing with the architecture
  for such little things now").
- (3) Cash credit revocation via supersession of new
  `promo_cash_credited` events with `status='rejected'`
  (no `promo_cash_revoked` event type — asymmetric
  with FB pattern, matches §A.4 verbatim).
  **Operator held — implicit trust in Claude's
  judgement.**
- (4) Cascade payload fields as optional fields on
  `FreeBetCreditedPayload` /
  `PromoCashCreditedPayload` base classes (not
  separate subclasses). **Operator-confirmed at
  structure proposal.**
- (5) `promo_observed` payload-side
  `promo_template_id` (no SQL FK to `promo_template`,
  adapter-side existence check). Same pattern as
  W14's `external_payment.payee_id`.
  **Operator held — implicit trust in Claude's
  judgement.**
- (6) `accountcare_warning_raised.warning_type_id`
  validated at adapter, not at SQL FK.
  **Operator held — implicit trust in Claude's
  judgement.**

**Three operator-decisions surfaced for brief lock, all
held with implicit trust:**

- Cat 5 calls (3) / (5) / (6) above — operator
  signalled "I trust that your decisions will be good
  for this as long as they align with the vision and
  building on top of what we've already developed and
  not limiting our builds in the future for the other
  areas."
- Reference-table mutation surface — no `delete_*`
  methods on any reference repository, remediation via
  status update or partial field update.
  **Operator held.**
- Confidence payload deferral — `FreeBetCreditedPayload.confidence_payload`
  as free-form `dict[str, object] | None` pending
  Slice 2 Q2 confidence-model lock.
  **Operator held.**

Two non-blocking items surfaced for S131 triage:

- Reference-data seed-script approach (§5.5.2):
  operator-side SQL vs Pydantic-via-adapter. Affects
  post-W13 operator work only.
- Forward-routing preference (§10 paths A/B/C —
  W15 / W12 / W8 ordering). Frames S131's "what
  should land next" question.


**2. Code dispatch prompt delivered (in-conversation,
not on disk).**

Stage-1-through-5 structure: read brief end-to-end +
governing project docs; run §6.1 alignment check +
operator-amplified judgement extension; execute §6.2
build order; run §7 empirical verification; write
report at `dr029/w13_promos/w13_promos_report.md` per
§8 output spec. Hard limits restated explicitly (single
bounded session, behaviour preservation, no Alembic,
no cross-domain imports, no state-mutating git
commands, `create_file` banned). Tools: Desktop
Commander preferred, CLI native tools acceptable
substitutes if DC isn't loaded, Cat 3 spirit applies
either way. Operator confirmed prompt provided and Code
work has commenced; close-out triggered immediately
after.

**3. Empirical grounding reads completed.**

Substrate reads completed during Phase A pre-flight
plus Phase C drafting:

- `workflows/cash_flow/v1/cash_flow_store_adapter.py`
  (396 lines, end-to-end) — adapter pattern W13
  inherits literally.
- `store/repositories/cash_flow.py` (601 lines, ~half
  read substantively) — row-only repository pattern
  with `_event_type_value` helper and `object`-typed
  surface.
- `domain/cash_flow/__init__.py` (526 lines, first
  300 lines plus structural skim) — closed enums,
  `_PayloadBase`, per-event-type `_Payload` subclasses
  with `event_type_payload` literal discriminator,
  FK-nullability `@model_validator`,
  `PAYLOAD_BY_EVENT_TYPE` dispatch.
- `store/schema/cash_flow.py` (212 lines, first 150
  lines) — DDL constants + CHECK constraint pattern
  + `apply_migrations`.
- `decisions.md` DR-030 + S124 amendment plus
  DR-032 substantively.
- `workflows/burst_review/` directory listing —
  confirmed empty (only `__init__.py`).
- `tests/workflows/cash_flow/v1/` +
  `tests/store/repositories/` directory listings —
  confirmed the three-way test split pattern W13
  inherits.

## Standing-instruction adherence check

- **Cat 1 — silent session-open ritual:** broken this
  open. Step headers appeared in operator-facing text
  during the open ritual. Recorded as carry-forward
  sweep candidate; pattern is 4-broken-out-of-6 in
  the recent window. Not escalated.
- **Cat 1 — section-by-section walkthrough at one
  section per round:** softened this session by
  explicit operator directive. Operator authorised
  end-to-end draft of the W13 brief in one go ("If
  you have the tools/context, draft end-to-end and
  produce a short plain summary…"). Discipline still
  applied at the structure-proposal stage (proposed,
  awaited confirmation, proceeded). Brief itself was
  drafted in a single planned sweep rather than
  section-by-section. Pattern Tracking: this is the
  second session where operator has authorised
  end-to-end drafting for a substantive artefact —
  watch for any quality drift on subsequent reviews.
- **Cat 1 — render review content with hard line
  wraps:** held. Code dispatch prompt and brief
  structure proposal rendered with ~60–70 char hard
  wraps. The brief itself uses ~60-char hard wraps
  throughout (confirmed via spot-check of brief tail
  during verification).
- **Cat 1 — calendar-calibrated open directive:**
  held at S130 open. "Same-workday open relative to
  S129 close, ~9 min gap" noted.
- **Cat 1 — V3 build picture conditional render:**
  not rendered this session (no operator request, no
  cross-stream surfacing event). Held. Conditional
  pattern is now 11 consecutive clean applications
  S120–S130.
- **Cat 2 — DR-021 Adelaide-local timestamps:** held
  at open and close.
- **Cat 2 — pre-flight directory listing:** held at
  open.
- **Cat 2 — closing summary omission when opening
  prompt is produced:** will be honoured at this
  close per Cat 2 default behaviour.
- **Cat 3 — `create_file` ban:** held. All file
  writes via `write_file` (or via heredoc-piped
  `cat >>` for the session record).
- **Cat 3 — verify every write:** held. Each chunk
  of the W13 brief had its write confirmed via the
  `write_file` return code; mid-draft and final
  state verified via `wc -l` + `shasum` + section
  count.
- **Cat 3 — Desktop Commander as primary filesystem
  tool:** held throughout.
- **Cat 3 — pre-execution risk advisory (S126
  addition):** the brief was drafted in chunks of
  60–180 lines via `write_file` rather than
  30-line chunks per the empirical-DC-edit_block
  threshold. All chunks landed cleanly with the
  "performance tip" advisory only; no timeouts.
  Sixth session of observation; pattern is stable.
  Promotion-to-encoded-rule candidate: `write_file`
  with `mode='append'` tolerates 60–180-line chunks
  reliably, distinct from `edit_block`'s
  30-line empirical ceiling. Worth a Cat 3 entry
  formalising this if it surfaces again.
- **Cat 5 — operator-call surfacing during drafting:**
  held. Six Cat 5 calls named in brief §1.3 plus
  three operator-decisions surfaced at brief-lock
  review. Operator-confirmed three; operator-held
  three with implicit trust. Pattern matched the
  drafting-skill's call-driven surfacing discipline.

## Open items

Pointer-only to `current_state.md` items. New items
explicitly called out below.

**New items this session:**

- (1) **W13 brief is locked; Code is executing
  out-of-session.** Code's report is the gate for
  S131's primary deliverable.
- (2) **Operator-side action between S130 and S131
  (silent — Code does the work):** dispatch the
  Code prompt against the locked W13 brief and
  ensure Code writes its report at the named path
  `dr029/w13_promos/w13_promos_report.md`. Operator
  has signalled Code work has commenced. S131 gate:
  the report must exist at the named path before
  S131 opens substantively.
- (3) **Reference-data seed-script approach** —
  non-blocking; affects post-W13 operator work.
  S131 triage frames the path (operator-side SQL vs
  Pydantic-via-adapter).
- (4) **Forward-routing preference** — W15 vs W12
  vs W8 ordering. Non-blocking; S131 triage decides
  after W13 report assessment.
- (5) **`write_file` append-chunk size empirical
  ceiling** — sixth session observation of clean
  60–180-line chunks via `write_file` mode='append'.
  Promotion-to-encoded-rule candidate for Cat 3 if
  surfaces again in S131 or S132.
- (6) **Cat 1 silent open-ritual pattern** —
  4-broken-out-of-6 recent window. Carry-forward
  sweep candidate; not escalated.

**Items that carry forward unchanged from S129:**

- The S128 hold-without-escalation call on the
  silent open-ritual drift remains the operative
  stance.
- Cat 1 build-picture conditional render heuristic
  continues clean (now 11 consecutive applications
  S120–S130).
- Cat 3 pre-execution risk advisory (S126
  promotion-candidate from S124 / S125 / S126 /
  S128 / S129 / S130 observation window) — six
  sessions of stable pattern, ready for promotion
  on a seventh observation if S131 or S132 holds.

## Open items out

- (a) **W14 / W14.1 close-out is now fully behind
  us.** All five `lint-imports` contracts clean as
  of W14.1 close; no W13 work touches W14 files;
  pattern reference only. The substrate is locked
  and serves as the W13 inheritance template.
- (b) **Brief structure proposal call** — operator
  confirmed (i) full reference-table shipping;
  closed at S130 Phase B.
- (c) **Reference-table approach call** — operator
  confirmed option (i); closed at S130 Phase B.
- (d) **Cascade payload field shape call** —
  operator confirmed optional fields on base
  payload classes (not separate subclasses); closed
  pre-Phase-C.
- (e) **Revoked-vs-expired event-type structure call**
  — operator confirmed leave §A.4 verbatim; closed
  pre-Phase-C.


## Session close state

**Rebuild folder root:** clean. All expected `.md`
files at root plus `openapi.json` plus
`external_api_resources.md` plus expected directories
(`agent_review/`, `diagrams/`, `dr029/`,
`orchestration_pack/`, `sessions/`, `skills/`,
`.close_out_backups/`). No phantom files.

**WIP:** the W13 brief is locked and on disk at
`dr029/w13_promos/w13_promos_brief.md`. The
`dr029/w13_promos/` directory exists with the brief
as its sole file (the W13 report path
`w13_promos_report.md` is reserved for Code's
output; not yet on disk).

**`.close_out_backups/`:** at close-write time
contains `SESSION_130_opening_prompt.md` (the active
prompt that drove this session open — stale at S130
close). To be replaced by
`SESSION_131_opening_prompt.md` per Step 9 sweep.

**Sessions folder:** `SESSION_129.md` (658 lines)
plus this `SESSION_130.md`. Last numbered.

**Project knowledge base (Claude Projects):** no
project-side action required at close. Standing
instructions unchanged this session; no
project-knowledge-base re-upload needed. The W13
brief sits in the v3 build folder which is Google
Drive auto-synced per project_context.md (no
operator-side sync prompt needed at close).

**`current_state.md`:** to be rotated to reflect
S130 outcomes per Step 5 of close ritual.

**`v3_build_picture.md`:** to be updated per Step 6
— W13 stream moves from `blocked-on-W14` to `in
flight` (Code executing); no other stream movement.

**`standing_instructions.md`:** unchanged this
session. Step 7 sweep is a silent skip.

## Forward routing

**Confirmed with operator:** "Claude code prompt has
been provided and work has commenced. Happy for you
to close out."

**S131 shape:** triage session. Open per
`bethub-session-open` skill, drift-check against
S130 close timestamp, read Code's W13 report
(`dr029/w13_promos/w13_promos_report.md`),
verification against §7 expected outcomes, findings
triage per the brief's §10 classification
((a) brief-spec deviation / (b) spec-implied
substrate concern / (c) pre-existing codebase shape).

**S131 forward-routing call from three plausible
paths post-clean-W13-ship:**

- Path A: operator seeds reference data, proceed to
  W15 (ops_events) brief drafting.
- Path B: skip W15, proceed to W12 (read-side
  balances / FB inventory / AccountCare warning
  derivation).
- Path C: build W8 burst-review surface next so
  cascade triggering logic lands and `free_bet_credited`
  cascade fields move from "write surface only" to
  "fully exercisable end-to-end."

**Operator picks at S131 after Code report
assessment.** Brief drafting for the chosen path
lands at S132 or S133.

**Operator-side action between S130 close and S131
open:**

- Ensure Code's W13 report is on disk at
  `dr029/w13_promos/w13_promos_report.md` before
  opening S131 substantively. Code is the actor;
  operator dispatches and monitors.

**S131 gate:** the report must exist at the named
path. If S131 opens before the report is on disk,
the open-ritual surfaces the gate failure and S131
becomes a brief-update/triage session pending
report.

---

**Session 130 closes.**

