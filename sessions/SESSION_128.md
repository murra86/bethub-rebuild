# Session 128 — W14 report triaged; (ii) DR-030-restoring W14.1 brief locked end-to-end after mid-session option-1 scope expansion; first per-domain event log workstream gets a row-only repository + workflow-side adapter pattern

**Opened:** 2026-05-12 13:53 ACST
**Closed:** 2026-05-12 14:18 ACST
**Wall-clock:** ~25m elapsed. Same-workday open relative
to S127 close (12:14 ACST same day, 99-minute gap).
Same-workday close — no day-rollover, no pause-and-resume.

**Tool routing:** Claude Chat for all work. Substantive
reads: `current_state.md`,
`standing_instructions.md` in full, `project_context.md`,
`sessions/SESSION_127.md`,
`dr029/w14_cash_flow/w14_cash_flow_brief.md` (1,665
lines), `dr029/w14_cash_flow/w14_cash_flow_report.md`
(864 lines), `v3_build_picture.md`, v3 codebase
listings (`workflows/`, `tests/workflows/`,
`tests/store/repositories/` for adapter location and
test layout grounding). Seven chunked `write_file`
calls drafting the W14.1 brief end-to-end (§1, §2+§3,
§4+§5.1+§5.2, §5.3+§5.4+§6, §7+§8, §9+§10, §11), plus
close-out paperwork. One single `start_process` call
to verify the W14.1 brief line count + byte count +
SHA256 prefix + section header order. No Code dispatch
this session beyond providing the operator with the
W14.1 prompt for hand-off; no VPS access, no Betfair
API, no live DB writes.

**Governing DRs invoked:** DR-021 (Adelaide local time
anchoring, open / close + every timestamp persisted
to cash_flow_events; W14.1 brief preserves the
substrate unchanged). DR-030 (v3 module-boundary
discipline + Session 124 amendment — **the load-bearing
reason W14.1 exists**; `store/` imports nothing else
in the project, restored after W14.1). DR-027
(two-database architecture + Session 124 amendment
— per-domain event-table internal shape unchanged).
DR-019 (derived state on read — the critical asymmetry
applies to bet records but NOT cash flow events,
carries through unchanged). DR-022 (book / account /
account-at-book vocabulary — FKs unchanged). DR-032
(canonical-reference-layer — reference only).
DR-028 (cross-database integration boundary
discipline — unchanged).

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
→ `2026-05-12 13:53 ACST`.
**Close:** same command → `2026-05-12 14:18 ACST`.

Same-workday open relative to S127 close (12:14 ACST
same day, 99-minute gap). No day-rollover this session.
No pause-and-resume.

## Pre-flight checks

Drift-check at open held clean. `current_state.md`
last-updated 2026-05-12 12:14 ACST matched S127 close
timestamp. `v3_build_picture.md` last-updated 12:14
ACST also matched. `sessions/SESSION_127.md` present
(693 lines).

**Pre-flight directory listing:** rebuild folder root
clean. Expected `.md` files at root plus
`v3_build_picture.md` plus `openapi.json` plus
`external_api_resources.md` plus expected directories
(`agent_review/`, `diagrams/`, `dr029/`,
`orchestration_pack/`, `sessions/`, `skills/`,
`.close_out_backups/`). `.close_out_backups/` held
only `SESSION_128_opening_prompt.md` (the active one,
correct state). No phantom files, no stale backups.

**Drift event surfaced at open:** Cat 1 silent
session-open ritual was BROKEN again at S128 open.
Step headers ("Step 1 — Timestamp anchor", "Step 2 —
Required reads", "Step 3 — Pre-flight directory
listing") appeared in operator-facing text — same
failure pattern as S125, S127. S126 held clean.
Three-out-of-four-session failure rate now visible.
Surfaced explicitly at open per Cat 1 drift-check
discipline. Operator response: "*I'm not too fussed
about that, so I think we can just leave it as is.
It's already working fairly well.*" Promotion-to-
encoded-rule consideration declined this session;
sweep candidate continues carrying.

## Session shape

Triage-then-brief-drafting session with operator-driven
mid-session scope expansion (option 1) at end of triage
phase. Five phases across the ~25-minute wall clock.

**Phase 1 — Open + orientation.** Anchor + required
reads (`current_state.md`, `standing_instructions.md`
in full, `project_context.md`,
`sessions/SESSION_127.md`,
`dr029/w14_cash_flow/w14_cash_flow_brief.md` in full,
`dr029/w14_cash_flow/w14_cash_flow_report.md` in full,
`v3_build_picture.md`) + pre-flight directory listing
+ drift-check + silent-ritual drift surfacing.
Calendar-calibrated tight recap delivered (3 sentences
on S127 substantive landings + objective for S128 +
inline naming of the load-bearing §5.1 finding).
Inline render of `v3_build_picture.md` (state moved
since previous open — S127 close updated the
artefact). Open-items delta rendered (W14 brief
drafting closed S127 / W14 report now on disk for
S128 triage / DR-030 alignment finding surfaced as
load-bearing routing decision).

**Phase 2 — W14 report triage (inventory-first
cadence per Cat 1 Session 113 instruction).** Ten
findings inventoried. Nine classified as Claude-
territory cleanups (test layout asymmetry, brief-spec
inaccuracies, `git diff` ergonomic notes, tooling-
alternative clause, pytest collection ordering,
file-size overrun against rough guides — none with
operational consequence on bet safety / account
hygiene / the four strategies / analytical layer).
One classified as load-bearing operator-call: §5.1
DR-030 alignment finding. Two routes named — (i)
amend DR-030 carving out per-domain event
repositories vs (ii) W14.1 surgical fix relocating
Pydantic handling to a workflow-side adapter.
Recommendation locked: (ii) — rationale being that
W4/W6/W11 already follow row-only repository pattern;
bending DR-030 on first per-domain event log table
would send a signal that module-boundary discipline
bends easily and W13/W15 would inherit the bent
version.

**Phase 3 — Plain-language re-explanation (per Cat 1
register).** Operator requested triage call in plain
terms. Reframed as: storage layer stays "dumb" (reads
and writes rows, doesn't know meaning); rule got bent
during W14 build; (ii) fixes W14 to obey the rule
vs (i) changes the rule. Operator: "*Yourcall.*"
Cat 5 software-call exercised, locked (ii).

**Phase 4 — Mid-session option-1 scope expansion.**
Operator asked for the Code dispatch prompt + close
after the (ii) call landed. Surfaced that the prompt
needs a locked W14.1 brief to point at, and current
routing has S129 drafting the brief. Surfaced two
options — (1) draft W14.1 within S128 collapsing the
arc by one session vs (2) close S128 cleanly with
W14.1 brief drafting locked as S129's primary
deliverable. Pre-execution risk advisory exercised
per Cat 3 (added S126): estimated ~700–1000 lines /
6–9 chunked write calls / context budget remaining
healthy / well-bounded but real scope expansion at
end-of-session. Operator: "*Option 1.*"

**Phase 5 — W14.1 brief drafting end-to-end.** Loaded
`bethub-brief-drafting` skill. Two empirical grounding
reads before drafting (`workflows/` listing confirmed
`bet_entry/v1/` and `burst_review/v1/` precedent for
`cash_flow/v1/` location; `tests/workflows/` listing
confirmed `bet_entry/` precedent for the new adapter
test file location; `tests/store/repositories/`
listing confirmed the W11 / bets-tests layout for
the W14 test relocation). Drafted the universal
section spine (§1, §2+§3, §4+§5.1+§5.2,
§5.3+§5.4+§6, §7+§8, §9+§10, §11) across seven
`write_file` calls — one rewrite establishing §1 plus
six appends. Per-chunk sizing ranged 113–314 lines;
performance-warning above ~30 lines on each but every
write landed cleanly. Brief landed at 1,586 lines /
64,872 bytes / SHA256 prefix `21a59f1a`. Ten Cat 5
software calls made and surfaced inline at brief
hand-off (operator-visible, not buried). Operator
delegated review depth ("Software development is
your realm" pattern from S127 carried implicitly via
the option-1 acceptance). Code dispatch prompt
provided. Close-out paperwork follows.

**Phase 6 — Close-out paperwork.** This file, plus
`current_state.md` rotation, plus `v3_build_picture.md`
update (W14.1 surfaces as new sub-stream tracked under
W14; W14 next-milestone updated to "Code's W14.1
report triage in S129"), plus S129 opening prompt
generation, plus `.close_out_backups/` sweep, plus
post-close verification.

## Structural drift surfaced this session

**One discipline gap caught: silent-ritual-at-open
broken again.** The Cat 1 rule (Session 83 / Session
114 tightening — "Zero step-by-step narration. No
'Step 1 — running timestamp anchor' or 'Step 3 —
pre-flight directory listing' or equivalent step
headers in operator-facing text") was broken at this
S128 open. Step headers appeared as visible operator-
facing markdown headers, same failure pattern as S127.
S126 held clean; S125, S127, S128 broke. Three-out-of-
four window now visible.

**Operator decision on the carry:** declined
promotion to encoded-rule. "*It's already working
fairly well.*" Sweep candidate continues carrying.
No standing-instruction edit this session.

**One mid-session scope expansion:** Phase 4's option-1
decision moved W14.1 brief drafting from S129's primary
deliverable into S128. Not drift — operator-driven
scope expansion under pre-execution risk advisory.
Recorded as a forward-routing change in §forward
routing below.

## What was delivered

Three on-disk artefacts plus the dispatch prompt:

**1. W14 report triage decision: (ii) — W14.1 surgical
fix locked at S128 triage.**

Rejected route (i) amend DR-030 carve-out. Rationale
in Phase 2 above + brief §1.1 / §1.3 / §2 fully.

**2. W14.1 brief at
`dr029/w14_cash_flow/w14_1_adapter_brief.md` —
1,586 lines / 64,872 bytes / SHA256 prefix
`21a59f1a`.**

Universal section spine: §1 (what this brief is /
is not / why W14.1 scope), §2 (why this work exists),
§3 (pre-reads — required + reference-only), §4
(system access), §5 (substantive scope — adapter /
repository trim / test reshape / test relocation),
§6 (sequencing — pre-build alignment check / build
order), §7 (empirical verification — pre + post
baselines / file checks / smoke script), §8 (output
spec — `dr029/w14_cash_flow/w14_1_adapter_report.md`,
target ~250–450 lines), §9 (hard limits — operating
principle / behaviour preservation / no adjacent
workstreams / no Alembic / no SQLAlchemy / operational
guardrails / dirty-tree handling), §10 (what happens
after Code's session), §11 (cross-references —
architecture and decisions / prior briefs / standing
instructions / parking lot / build picture).

Scope: relocates W14's Pydantic handling from
`store/repositories/cash_flow.py` to a new
`workflows/cash_flow/v1/cash_flow_store_adapter.py`,
trims the repository back to row-only (W11 accounts
precedent), moves the W14 test files from
`tests/store/test_cash_flow_*.py` to
`tests/store/repositories/test_cash_flow_*.py`
(matching the W11 / bets-tests layout that W14 report
§5.4 flagged), and splits Pydantic-side tests into a
new `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`.
Four new files (adapter + 3 package markers — counted
as one logical block of empty `__init__.py` files)
plus one edited file (`store/repositories/cash_flow.py`)
plus two moved files (the two W14 test files, with
reshape on the repository tests).

After W14.1: `lint-imports` passes on all five
contracts; DR-030 restored; W13 / W15 inherit a row-
only repository + workflow-side adapter pattern as
the v3 convention.

W14.1 is the **first surgical-fix brief in the v3
build proper arc** (Sessions 35/36 surgical-fix
precedent applied at v3 level).

**3. Claude Code dispatch prompt provided in chat.**

Copy-pasteable handover for the operator. Names the
brief path, the single-bounded-session reminder, the
eight-step procedure (read brief → run §3.1 required
reads → execute §6.1 alignment check → §7.1 pre-
baselines → §6.2 build → §9.7 dirty-tree discipline
→ §7.2–§7.4 verification → write report at §8 path),
Adelaide-local-timestamps directive, write-verify +
`create_file` ban directive (with CLI-tool fallback
clause per W14 report §5.7), and the SHA256 prefix
for cross-check (`21a59f1a`).

**4. Close-out paperwork landed in-session.**

This file (`sessions/SESSION_128.md`), `current_state.md`
rotation, `v3_build_picture.md` update (W14.1 sub-stream
surfaced under W14; W14 next-milestone updated to
"Code's W14.1 report triage in S129"),
`.close_out_backups/SESSION_129_opening_prompt.md`
written, stale `SESSION_128_opening_prompt.md`
deleted from backups.

## Standing-instruction adherence check

- **Cat 1 silent session-open ritual — BROKEN at this
  open.** Same failure pattern as S125 / S127. S126
  held clean. Three-out-of-four window now visible.
  Operator declined promotion-to-encoded-rule at
  surfacing. Sweep candidate continues carrying.
- **Cat 1 silent session-close ritual** — held this
  close. Step labels suppressed in operator-facing
  text; only this session record + the single brief
  one-line post-close output planned to surface.
- **Cat 1 V3 build picture conditional render at
  open — spirit-of-the-rule heuristic** — rendered at
  open this session (stream state had moved at S127
  close). Render shape matched the artefact + 1-2
  sentence detail on the current stream (W14).
  Eight consecutive clean applications (S121–S128).
  Pattern stable.
- **Cat 1 calendar-calibrated session open** — held.
  Same-workday recap delivered tight (3 sentences on
  S127 substantive landings + objective for S128 +
  the load-bearing §5.1 routing decision named
  upfront).
- **Cat 1 drift-check** — held at open
  (`current_state.md` + `v3_build_picture.md` +
  `SESSION_127.md` all anchored at 12:14 ACST
  matching S127 close).
- **Cat 1 open-items delta — conditional** —
  rendered at open (meaningful delta: S127 closed
  multiple items including W14 brief drafting, S128
  inherits Code's report on disk plus the §5.1
  finding).
- **Cat 1 tightened response register (Session 114)**
  — held. Triage-phase per-finding inventory stayed
  tight; recommendation framed in one paragraph;
  plain-language re-explanation when operator
  requested it; mid-session option surfacing for
  the scope-expansion decision kept to one round
  per option pair.
- **Cat 1 inventory-first cadence on long technical
  reports (added Session 114, surfaced Session 113)**
  — exercised in Phase 2. Ten W14 findings
  inventoried; nine classified as no-operational-
  impact (Claude territory per Cat 5); one classified
  as operator-call (§5.1). Plain-language framing
  used for the operator-call surfacing per Cat 1.
- **Cat 1 call-driven surfacing during section-by-
  section drafting (Session 84)** — held in
  brief drafting (Phase 5). Operator delegated the
  cadence via option-1 acceptance; call-driven
  surfacing collapsed into pre-drafting summary of
  the ten Cat 5 software calls made.
- **Cat 1 render review content with hard line wraps**
  — held. Brief drafted with ~60-65 character hard
  wraps throughout; dispatch prompt also wrapped.
- **Cat 2 timestamp anchor at session open + close**
  — held. Open 13:53 ACST; close 14:18 ACST.
- **Cat 2 required reads at session open** — held.
  Read `current_state.md`,
  `standing_instructions.md` in full,
  `project_context.md`, `sessions/SESSION_127.md`,
  `dr029/w14_cash_flow/w14_cash_flow_brief.md` in
  full, `dr029/w14_cash_flow/w14_cash_flow_report.md`
  in full, `v3_build_picture.md` in order.
- **Cat 2 pre-flight directory listing** — held at
  open. No phantom files; expected state.
- **Cat 2 governing DRs named in orientation** —
  held (DR-030 + DR-027 + DR-019 + DR-022 + DR-021
  all named with bracketed plain-language reminders
  in opening output and in the W14.1 brief).
- **Cat 2 persist-drafted-but-not-assembled artefact
  content to scratch** — N/A this session. All
  drafted content landed directly to canonical
  location (the W14.1 brief at its locked path);
  no in-chat-only locked drafts to persist.
- **Cat 2 surface structural-drift in session
  record** — held (the silent-ritual-at-open
  violation recorded explicitly above; the option-1
  mid-session scope expansion recorded under session
  shape and forward routing).
- **Cat 2 workstream-label / build-picture
  coherence at close (Session 115)** — held. W14.1
  is a new sub-stream entering the picture; added
  under the W14 row at close. W14 label use matches
  picture (was `in flight` at open; stays
  `in flight` at close with next-milestone updated
  to W14.1's report triage). No scope drift on
  existing labels.
- **Cat 2 re-validate queued work-items at execution
  time (Session 114)** — held. The S128 opening
  prompt's primary queue item ("triage W14 report")
  was re-validated in Phase 2 against the report
  itself (10 findings inventoried explicitly rather
  than trusted blindly). The forward-routing change
  to draft W14.1 in S128 was an operator-driven
  re-validation of the routing locked at S127
  close.
- **Cat 3 empirical-verification-before-editing** —
  held. The W14.1 brief's `workflows/cash_flow/v1/`
  location and test layout were grounded against
  the live v3 codebase (`workflows/` listing,
  `tests/workflows/` listing,
  `tests/store/repositories/` listing) before being
  written into the brief. Empirical, not assumed.
- **Cat 3 `create_file` banned** — held. All writes
  via `Desktop Commander:write_file` or
  `Desktop Commander:edit_block`. (No `edit_block`
  this session; only `write_file` calls and one
  verification `start_process`.)
- **Cat 3 verify-every-write** — held. Each
  `write_file` returned line count; final brief
  state verified via `wc -l` + `wc -c` + `shasum`
  + `grep` for section headers (count and order
  checked).
- **Cat 3 dry-run multi-target mechanical edits** —
  N/A this session. No multi-target scripted edits.
- **Cat 3 REPL discipline** — N/A this session (no
  multi-line Python invocations).
- **Cat 3 pre-execution risk advisory (added S126)**
  — exercised proactively in Phase 4 before
  committing to option 1 (estimated chunked write
  count + context budget + bounded-vs-unbounded
  read; named "real scope expansion at end-of-
  session" honestly). Third session of observation
  (S126 added → S127 exercised → S128 exercised).
  Pattern operationally visible; continue carrying
  as sweep candidate.
- **Cat 4 divergence-capture-or-fix** — N/A this
  session. The §5.1 finding is not a substrate
  divergence but a brief-spec vs DR-030 conflict
  surfaced in the W14 report itself; routing is
  fix-via-W14.1 (locked in Phase 2).
- **Cat 5 software-questions-are-Claude's** — held
  throughout. The ten Cat 5 software calls listed
  in Phase 5 were Claude's picks; operator confirmed
  the option-1 acceptance which implicitly delegated
  the technical detail.
- **Cat 5 make-software-calls-don't-punt (Session
  114)** — held. The (i) vs (ii) routing was framed
  as a recommendation with rationale, not as "A or
  B, your call?" — operator's "*Yourcall*" response
  exercised the locked recommendation.
- **Cat 5 cosmetic-calls-default-to-Claude's-pick**
  — N/A this session.
- **Cat 5 length targets bend to required detail
  (Session 120)** — exercised on the brief length.
  W14.1 landed at 1,586 lines (over the initial
  ~700–1000 estimate). Earned by §5's per-method
  change-mapping across two repository classes plus
  the test reshape breakdown plus §6 sequencing and
  §7 verification battery. Doesn't undermine the
  build — Code reads the brief once end-to-end; the
  detail is what protects against expensive mid-
  session ambiguity.

## Open items in / out

Pointer-only — full detail in `current_state.md`
post-rotation.

**Closed in Session 128:**

- **W14 report triage** — completed. Decision (ii)
  locked: W14.1 surgical fix relocating Pydantic
  handling to a workflow-side adapter; DR-030
  restored.
- **W14 brief drafting** — drops from
  `v3_build_picture.md` at this close per the one-
  session-carry rule. Was `done` at S127 close;
  carried one session through S128; drops now.

**New from Session 128 (PRIMARY for Session 129):**

- **Code's W14.1 report triage.** Expected at
  `dr029/w14_cash_flow/w14_1_adapter_report.md`
  once the out-of-session Code run finishes. S129's
  primary deliverable per the brief's §10. Triage
  shape: (a) verification of landed work (paths,
  tests, mypy, ruff, `lint-imports` — the load-
  bearing gate, dirty-tree adherence); (b) findings
  triage per the brief's §8 item 5; (c) forward
  routing — W14 + W14.1 → `done` if clean and
  W14.2 not needed; otherwise W14.2 follow-up brief
  drafting; afterwards W13 → `in flight`.
- **Operator-side action between S128 and S129:**
  dispatch the Claude Code session against the
  W14.1 brief; ensure Code writes the report at the
  named path before opening S129.

**Carry-forward dependencies (sensitivity flags
unchanged from S123 / S125 / S126 / S127):**

- **Hedge classification (DR-025, Finding #8 from
  S123).** Revisit before W15 brief drafting.
  Strategy 2 cycle measurement implications.
- **§2.4 Fix 4 cadence design dependency (Finding #3
  from S123).** Fix 4 must verify capture cadence
  brackets near-jump placements tightly.

**Tracked carry per operator instruction (carried
from S118 / S119 / S120 / S121 / S122 / S123 / S125 /
S126 / S127):**

- **Alembic adoption.** Locked migration tool per
  DR-031, deferred. Sequenced after W14 + W14.1 +
  W13 + W12 land. W14.1 brief §9.4 explicitly
  carries the deferral; W14.1 uses the existing
  pre-Alembic schema unchanged.

**Carried forward (sweep candidates):**

- **Cat 1 silent session-open ritual narration drift
  — sweep candidate, ACTIVE FAILURE for the third
  time in four sessions.** S125 / S127 / S128
  broke; S126 held. Operator declined promotion-to-
  encoded-rule at S128 ("*It's already working
  fairly well.*"). Sweep candidate continues
  carrying without escalation.
- **Cat 1 build-picture conditional render heuristic
  — formalisation candidate.** Eight consecutive
  clean applications (S121–S128). Pattern stable;
  promotion to encoded rule remains the next step
  if it holds 2-3 more sessions.
- **Cat 3 pre-execution risk advisory (added S126).**
  Third session of observation; exercised proactively
  this session for the option-1 scope expansion
  decision. Pattern stable. Promotion-to-encoded-
  rule candidate at S129/S130 if it holds.
- **Cat 4 divergence-capture-or-fix elevation
  candidate.** No fresh instance this session.
  Pattern held as sensitivity, not encoded. Review
  after a few sessions of W13 / W12 brief drafting
  where divergence is more likely to surface.

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
- **WIP:** no scratch writes this session. All
  writes direct to canonical files (W14.1 brief at
  its locked path; session record at
  `sessions/SESSION_128.md`).
- **`.close_out_backups/`:**
  `SESSION_128_opening_prompt.md` deleted at this
  close; `SESSION_129_opening_prompt.md` written.
  Post-close state: single file
  (`SESSION_129_opening_prompt.md`) only.
- **`sessions/` folder:** SESSION_124.md (587 lines)
  + SESSION_125.md (561 lines) + SESSION_126.md
  (643 lines) + SESSION_127.md (693 lines) +
  SESSION_128.md (this file) all present. Sessions
  journal complete through S128.
- **`dr029/w14_cash_flow/`:** holds W14 brief
  (`w14_cash_flow_brief.md`, 1,665 lines / 64.6KB),
  W14 report (`w14_cash_flow_report.md`, 864 lines),
  and W14.1 brief
  (`w14_1_adapter_brief.md`, 1,586 lines / 64.9KB)
  at this close. Will hold Code's W14.1 report
  next.
- **Project knowledge base:** unchanged this
  session (no `standing_instructions.md` edits).
  No operator-side re-upload action required.
- **`bethub-v3/contracts/`:** unchanged from S127
  close state.
- **`current_state.md`:** rotated this close;
  last-updated 2026-05-12 14:18 ACST.
- **`v3_build_picture.md`:** updated this close
  (W14 brief drafting row dropped per one-session-
  carry; W14.1 sub-stream added under W14; W14
  next-milestone updated to "Code's W14.1 report
  triage in S129"); last-updated 2026-05-12 14:18
  ACST.
- **`standing_instructions.md`:** unchanged this
  session. Cat 3 pre-execution risk advisory
  (added S126) exercised proactively but no
  further edits needed.

## Forward routing

**Confirmed forward routing for S129:** Code's W14.1
report triage.

**Operator's option-1 mid-session decision:** draft
W14.1 within S128 rather than defer to S129. This
collapses the W14 close-out arc by one session — the
original S128 routing (S128 triages W14 report only;
S129 drafts W14.1 brief; S130 triages W14.1 report)
becomes (S128 triages W14 report + drafts W14.1
brief; S129 triages W14.1 report).

**Operator-side action between sessions:** dispatch
the Claude Code session against the W14.1 brief at
`dr029/w14_cash_flow/w14_1_adapter_brief.md`. Code
writes the report at
`dr029/w14_cash_flow/w14_1_adapter_report.md`. The
gate condition for S129 open is the report being
present at that named path.

S129 shape per the W14.1 brief's §10:

1. **Verification check.** Did the work land at
   expected paths with expected shape? Tests pass
   (schema 10 + reshaped repository ~18–22 + new
   adapter ~25–30)? `lint-imports` passes all five
   contracts (the load-bearing gate W14.1 exists to
   fix)? mypy / ruff pass? Dirty-tree adherence
   statement clean (pre / post `git status --short`
   diffs as expected per §9.7)?
2. **Findings triage.** For each finding in §8 item
   5: spec ambiguity → architecture / decisions
   amendment or brief addendum; deferred concern →
   W14.2 follow-up brief or parking lot; integration
   surprise → W11 / W14 amendment or W14.2 defence;
   weak test → W14.2 or W13 follow-up; other →
   case-by-case.
3. **Forward routing.** W14 + W14.1 → `done` (one-
   session carry) if clean; W14.2 brief drafting
   if warranted; otherwise W13 brief drafting
   becomes the next active stream.

**Possible S129 pivots:**

- **Clean W14 + W14.1 close.** Most likely shape if
  `lint-imports` passes and regression is green.
  W14 + W14.1 → `done`; W13 → `in flight` (promo
  events / FB inventory / AccountCare warnings
  sub-stream); W15 stays `blocked-on-W14` (blocked
  on W13 sequencing).
- **W14.2 follow-up brief drafting.** If findings
  warrant — e.g. a regression introduced by the
  test reshape, or an integration surprise with the
  adapter pattern that W13 / W15 would also hit.
- **Partial-ship triage.** If Code surfaced
  scope-doesn't-fit-single-session as a finding —
  the brief explicitly authorised this via §9.1.
  S129 triages what landed, what didn't, routes
  the remainder.

**Out of scope for S129** (unless triage routes a
different direction):

- W13 / W12 / W15 brief drafting (sequenced after
  W14 + W14.1 close + any W14.2).
- DR-025 hedge revisit (parked for pre-W15).
- §2.4 Fix 4 cadence design (independent arc).
- W11 accounts adapter / re-export (separate
  concern, not W14.1's responsibility).

---

**Session 128 triages the W14 report and locks W14.1
end-to-end via a mid-session option-1 scope
expansion.** The (ii) DR-030-restoring route — move
Pydantic handling to a workflow-side adapter, trim
repository to row-only — is locked at the brief
contract level. W14's `lint-imports` failure is the
one gate that W14.1 fixes; everything else stays
intact. First per-domain event log workstream
inherits a row-only repository + workflow-side
adapter pattern as the v3 convention before W13 /
W15 reuse it.
