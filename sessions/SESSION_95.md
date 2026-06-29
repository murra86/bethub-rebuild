# Session 95

**Title:** v1.2 contract addition Code report triaged end-to-end
(§7.1 deviation confirmed W3-pattern; Findings 1/2/4 no-action;
Finding 3 folded into Session 96+ adapter brief); operator-driven
scope expansion turned the small W4 follow-up brief into a
mini-build with paired §13 contract clarification (Option C —
REST fallback path for streaming-blocked placement, preserving
contract intent while keeping Strategy 1 entries alive); parallel
pre-flight grounding run document-side (operator-Claude) and
codebase-side (Claude Code investigation report at
`SESSION_95_code_preflight.md`); Code's investigation evaporated
the two-brief split rationale (REST surface already exists, no
contract amendment needed beyond optional paragraph); brief scope
locked Shape A, structural shape locked across 12 sections; brief
drafting deferred to Session 96 fresh-mind per operator's Option 2
choice; live triage substrate written to disk at
`dr029/w4_bet_entry/_drafts/SESSION_95_drafts.md` (461 lines).
**Opened:** 2026-05-07 08:49 ACST
**Closed:** 2026-05-07 09:16 ACST
**Wall-clock:** ~27 minutes active session work. Same-workday
open relative to Session 94 close (~23 min gap). No
day-rollover, no pause-and-resume.
**Tool routing:** Claude Chat (triage + scope discussion +
brief structural shape lock). Claude Code (parallel pre-flight
investigation, operator-commissioned out-of-session against the
investigation prompt drafted in this Chat session). No
brief-drafting work in this Chat session — drafting deferred
to Session 96.
**Governing DRs invoked:** DR-021 (Adelaide local time), DR-027
(two-database architecture — context for the operational-line
discipline of the W4 entry-flow), DR-028 (cross-DB boundary —
informs why streaming-disconnect rule lives in `betfair_client`
not in v3 modules), DR-030 (v3 repo layout — informs file
locations for the locked brief scope), DR-031 (v3 tech stack —
informs Pydantic v2 / pytest discipline for the new
`price_source` field), DR-032 (canonical reference layer — the
operational metadata block where `price_source` slots is
adjacent to DR-032's per-leg snapshot fields).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
`2026-05-07 08:49 ACST`.
Close: same command → `2026-05-07 09:16 ACST`.

Same-workday open relative to Session 94 close at 08:26 ACST
(23-min gap, single-sitting continuation). No pause-and-resume.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, calibrated
against Cat 1 silent-ritual instruction:

- Rebuild root: 12 expected `.md` files, `openapi.json`,
  `external_api_resources.md`, `.DS_Store`. All directories
  present.
- `.close_out_backups/` contained `SESSION_95_opening_prompt.md`
  only (Session 94 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated
  `2026-05-07 08:26 ACST` matched Session 94 close;
  `sessions/SESSION_94.md` present (607 lines);
  `v3_build_picture.md` last-updated `2026-05-07 08:26 ACST`
  matched Session 94 close.
- Same-workday recap delivered at 23-min gap.
- V3 build picture: skip-silent at open (no stream movement
  in 23-min gap).
- Open-items delta: skip-silent at open (no items
  closed/opened/overdue in 23-min gap).
- Governing DRs named at open: DR-029 (closed), DR-027,
  DR-028, DR-030, DR-031, DR-021.

Sandbox-vs-Mac filesystem confusion at the very start —
operator-Claude's first attempt at the open ritual used
generic `view` and `bash_tool` (sandbox container), got "no
such directory" responses, and surfaced a blocker question to
the operator. Operator clarified Desktop Commander was
available; subsequent calls via `Desktop Commander:list_directory`
and `Desktop Commander:read_file` worked cleanly. Logged as
substrate for the `bash_tool` standing-instruction softening
candidate carried from Session 94.

## Session shape

Session 95 had **two distinct phases**, the second emerging
from operator-driven scope expansion mid-session:

**Phase 1 — v1.2 Code report triage.** Followed the brief-
report-triage cadence established Session 93. Read Code's
report (440 lines) end-to-end. Walked the §7.1 deviation
(W3 path-style vs library-call internals) one round; operator
confirmed W3-pattern choice. Walked Findings 1/2/3/4 in turn:

- Finding 1 (brief-text mismatch at §3) — cosmetic, no call.
- Finding 2 (stale §2/§14.2 surface count) — operator deferred
  to next contract-housekeeping sweep.
- Finding 3 (translation-layer entries pending) — operator
  folded into Session 96+ real `BetfairAdapter` brief.
- Finding 4 (baseline test count off by 75) — informational, no
  call.

Operator surfaced context-loss concern partway through;
operator-Claude wrote live-triage substrate to scratch at
`dr029/w4_bet_entry/_drafts/SESSION_95_drafts.md` and
continued updating it through the rest of the session.

**Phase 2 — small W4 follow-up brief scope discussion.** Went
to commission the small W4 follow-up Code brief (§7.4 + §7.6
from W4 report). Operator pushed back on the framing:
"terminal-with-message" reclassification of streaming-blocked
errors would mean losing time-sensitive Strategy 1 entries
near the jump (95% of current profit). Operator-Claude laid
out three options (A terminal / B stale-cache fallback /
C REST fallback). Operator chose Option C.

This expanded the brief beyond the original "small follow-up"
framing. Re-reading W4 report §7.4 directly (rather than
working from memory) confirmed §7.4 was a question, not a
recommendation — Option C is a stronger answer than either
alternative the report reached toward. §7.6 likewise was a
question (NULL vs duplicate-leg-price); operator chose NULL.

**Phase 3 — parallel pre-flight grounding.** Operator
proposed parallel investigation: operator-Claude reads
documents (W4 report + contract §13); Claude Code investigates
codebase (REST surface existence, price_source field state,
streaming-blocked classification site). Investigation prompt
drafted in Chat, pasted to fresh Code session by operator.
Code's investigation report came back at 207 lines.

Code's findings evaporated the two-brief split rationale —
REST price-fetch already exists in `live_pricing.py`, no
contract amendment needed (or only paragraph-level §13
clarification), `streaming_blocked` Protocol slot is currently
unreachable so the change is greenfield wiring not refactor.
Operator confirmed Shape A (single combined brief, ~400-500
lines).

**Phase 4 — structural shape lock + Session 95 close.**
Operator-Claude offered three options for budget management
(push through drafting, lock shape and defer drafting,
close fully and re-open). Operator chose Option 2 — lock
shape, defer drafting to fresh-mind Session 96. Structural
shape locked across 12 sections to scratch.

## What was delivered

Session 95 produced one canonical artefact and two operational
substrates:

**Live triage scratch — `dr029/w4_bet_entry/_drafts/SESSION_95_drafts.md`**
(461 lines). Captures all locked decisions from this session:

- Triage decisions (§7.1 deviation, Findings 1/2/3/4
  resolutions).
- Brief-drafting carry-forward (Session 94 brief contradicted
  itself; lesson logged for next standing-instructions sweep).
- Forward routing locked (Session 96 brief drafting; Session
  96+ real `BetfairAdapter` brief unblocked once this brief
  ships).
- Out-of-scope items (composition-root structural decision,
  standing-instructions sweep).
- Brief-drafting Phase 1 (scope-at-session-start vs
  operator-driven scope expansion to Option C).
- Pre-flight grounding consolidated findings (document-side +
  Code-side).
- Shape A vs Shape B call (Shape A locked).
- Brief scope locked (six coordinated workflow-layer changes).
- Brief structural shape locked (12-section spine; anchor
  paths; anchored counts; open question on §5.5 contract
  clarification).

**Code preflight investigation report — `dr029/w4_bet_entry/_drafts/SESSION_95_code_preflight.md`**
(207 lines, written by Claude Code during the parallel
pre-flight phase). Covers:

- Q1 REST price-fetch surface — already exists in
  `live_pricing.py`; no new surface needed.
- Q2 `price_source` field — doesn't exist; slots into
  `models.py:212-215` BetRecord operational metadata block.
- Q3 streaming-blocked classification — centralised at
  `placement.py:155-186`; W4 Protocol slot currently
  unreachable; greenfield wiring change.

Plus §4 self-assessment with adjacent observations (path-b
modal recovery wiring may go unreachable; naming
inconsistency across W3/W4 boundary; per-record vs per-leg
`price_source` placement question; §7.6 not investigated per
scope).

**Code prompt rendered in chat** (not on disk, not load-
bearing post-session). Hard-wrapped ~70 chars per Cat 1.
Operator pasted into fresh Code session to commission the
investigation.

**No edits to canonical-truth files in this session.** No
edits to `decisions.md`, `architecture.md`, `governance.md`,
`standing_instructions.md`, `vision.md`,
`v3_data_requirements.md`, `project_context.md`. The two
artefacts are session-scratch, not knowledge-base files.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-030,
  DR-031, DR-021 named at open; DR-032 surfaced as substrate
  for `price_source` placement; DR-029 named as closed
  gating arc.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight
  recap delivered at 23-min gap.
- **Cat 1 (V3 build picture conditional render)** — skip-silent
  at open (no stream movement). Not updated at this close (no
  stream movement during session).
- **Cat 1 (open-items delta)** — skip-silent at open (no
  movement in 23-min gap).
- **Cat 1 (drift-check)** — done at open, all three checks
  matched.
- **Cat 1 (silent session-open ritual)** — held. Steps 1–5
  silent except for the sandbox-vs-Mac filesystem blocker
  surface that needed operator clarification. Steps 6–8
  combined into single brief output.
- **Cat 1 (silent session-close ritual)** — holding this
  close. Steps 1–10 silent; Step 11 produces brief
  verification line.
- **Cat 1 (call-driven surfacing during section-by-section)**
  — held. v1.2 report walked one Finding per round per
  operator's request. Brief-drafting structural shape walked
  one structural-element decision per round.
- **Cat 1 (short responses, plain language)** — mostly held.
  One drift event mid-session: operator-Claude responded with
  a technical explanation of W3 path-style vs library-call
  internals using terms like "translation layer", "REST
  transport", "Protocol abstraction" — operator surfaced
  ("explain in plain language, plain operator gambling style,
  it's in your standing instructions"); operator-Claude
  redrafted with luddite-analyst-gambler framing. The
  redrafted version landed cleanly. Drift cause: technical
  framing carried over from reading Code's report; should
  have unwound to plain-operator-language by default.
  Carry-forward: when explaining Code-report deviations, draft
  in plain-operator-language by default — not just when
  operator surfaces.
- **Cat 1 (decision-maker framing)** — held throughout. Each
  decision led with the call or recommendation; reasoning
  followed.
- **Cat 1 (don't drift to alternatives when operator clear)**
  — held. Operator's "happy with both" / "all good" responses
  acted on without re-litigating.
- **Cat 1 (escalate to detail only when warranted)** — held.
  Option-laying for §7.4 (A/B/C) was warranted detail;
  operator's "explain in plain English" surface was a sign
  the framing-detail balance was off; corrected.
- **Cat 1 (line-break rendering for review content)** — held.
  Code investigation prompt rendered hard-wrapped at ~70
  chars.
- **Cat 1 (default to luddite-analyst-gambler brevity)** —
  held throughout, with the one drift event noted above.
- **Cat 2 (timestamp re-anchoring)** — open and close
  anchored. No pause-and-resume mid-session.
- **Cat 2 (pre-flight directory listing)** — done at open and
  again at close.
- **Cat 2 (Desktop Commander default)** — held (after the
  sandbox/Mac confusion at session start). All file ops via
  `Desktop Commander:list_directory`,
  `Desktop Commander:read_file`,
  `Desktop Commander:start_process`,
  `Desktop Commander:write_file`,
  `Desktop Commander:edit_block`.
- **Cat 2 (REPL discipline)** — n/a; no multi-line Python
  this session.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)** —
  not exercised this session. The very-first attempts via
  generic `view` and `bash_tool` were sandbox-namespace, not
  the same gotcha — those tools are non-functional in this
  environment per Cat 3.
- **Cat 2 (dry-run multi-target mechanical edits)** — n/a;
  three single-target `edit_block` edits to scratch.
- **Cat 2 (persist drafted artefact content to scratch)** —
  held mid-session. Operator surfaced context-loss concern
  partway through Phase 1 triage; operator-Claude wrote
  scratch at `dr029/w4_bet_entry/_drafts/SESSION_95_drafts.md`
  and updated it across Phases 2–4. Pattern: scratch can be
  written *during* a session (live substrate), not only at
  close. Carry-forward: this is a valid pattern to encode
  more explicitly in Cat 2.
- **Cat 2 (surface structural-drift in session record)** —
  no governance artefact structure changed this session.
- **Cat 3 (`bash_tool` non-functional)** — confirmed at session
  open: first attempt at the timestamp anchor used generic
  `view` and `bash_tool` calls which failed with "no such
  directory" responses; Desktop Commander succeeded. Substrate
  reinforces the Session 94 carry-forward — the rule should
  read "non-functional in this Claude.ai web session
  environment" or similar; the rule may misread as universal.
- **Cat 3 (external API resources reach-for)** — n/a this
  session.
- **Cat 4 (DR-027/028 invoked)** — named at open. Surfaced
  during contract §13 reading (DR-028's "no second
  integration point" frames why streaming-disconnect-blocks-
  writes lives in `betfair_client` not in v3 modules).
- **Cat 4 (operational/analytical line discipline)** — held.
  Brief scope explicitly frames new `price_source` and
  REST-fetch-fallback as operational-line work.
- **Cat 4 (single-cycle analysis discipline)** — n/a this
  session.
- **Cat 4 (Betfair as canonical source)** — load-bearing for
  `price_source` placement decision (per-record vs per-leg).
- **Cat 5 (software questions are Claude's)** — held
  throughout. Pydantic shape design, Protocol extension,
  field placement, naming canonicalisation, brief structural
  shape — all Claude's calls. Operator surfaced operationally-
  shaped questions only (does this affect bet entry near the
  jump; what does this look like at the screen).

## Session-95-specific reflections

- **Operator pushback on §7.4 framing was load-bearing.** The
  initial pitch (terminal-with-message reclassification)
  reflected the W4 report's literal language but missed the
  operational consequence (losing Strategy 1 entries near the
  jump = real profit hit). Operator's question — "does that
  mean if Betfair goes down I have to leave the tool and try
  to fix it?" — was the catch. Pattern for future report-
  triage and brief-scope work: when the report frames
  something as "the right thing semantically," check the
  operational consequence before pitching as a recommendation.
  The W4 report itself was actually asking a question; treating
  it as a recommendation was the framing error.

- **Context-loss surfacing led to live substrate writing.** The
  operator's mid-session surface ("we've been losing context
  lately, document this for subsequent sessions") was the
  trigger to write `SESSION_95_drafts.md` to disk and update
  it live. Pre-existing Cat 2 already names "persist drafted
  artefact content to scratch" but framed it as a close-out
  action; this session demonstrated mid-session substrate
  writing as a valid pattern. Carry-forward: encode mid-session
  scratch writing in Cat 2 explicitly — surfacing trigger is
  any of (a) operator flags context concern, (b) substantive
  decisions accumulating that are not yet in artefact form,
  (c) session about to pivot mode (e.g. triage to brief-
  drafting) and the prior phase's locked decisions need to
  travel forward.

- **Parallel pre-flight (operator-Claude doc-side + Code
  codebase-side) is high-value.** Operator-Claude's solo
  pre-flight would have surfaced the document-side findings
  (W4 report wording, contract §13 rule) but not the Code-side
  findings (REST surface already exists, Protocol slot is
  unreachable). Code's investigation evaporated the two-brief
  split rationale entirely. Pattern for future complex briefs
  where codebase state matters and operator-Claude can't run
  read-only investigation directly: parallel pre-flight is
  fast, mode-coherent (operator-Claude runs documents, Code
  runs codebase), and produces a richer ground than either
  alone.

- **Operator-Claude pushback on "send it to Code" framing was
  warranted.** Operator initially said "these sound like
  questions for Claude Code" when offered three pre-flight
  questions. Operator-Claude held the line: "no — these are
  brief-drafting questions, where I have to make sure the
  brief commissions the right work; Code executes against
  the brief at run-time, but if I draft blind, the brief
  either commissions duplicate work or collides with existing
  code." Distinction held; operator approved the parallel
  approach. Pattern: brief-drafting pre-flight is operator-
  Claude's own discipline (per skill Step 2), not delegable
  to Code. Code's role is execution against the locked brief,
  not pre-execution scoping.

- **Plain-operator-language drift event was instructive.**
  When walking Deviation §7.1, operator-Claude defaulted to
  technical language (translation layer, REST transport,
  Protocol abstraction). Operator surfaced. The redraft
  ("library way" vs "in-house way", "wiring", "test pass /
  doesn't yet work against real Betfair API") landed cleanly.
  Pattern: when explaining Code-report content to operator,
  default to plain-operator-language — the technical content
  is for the brief and the artefacts, not the operator-
  facing surfacing. Cat 1 already says this; the drift event
  confirms the rule needs to fire even for "small technical
  details" that feel too small to unwind.

- **Option 2 (lock shape, defer drafting) was the right
  budget call.** Session 95's wall-clock at the budget check
  was already ~25 min plus full triage and scope discussion.
  Drafting a 400-500 line brief end-to-end would have added
  ~30-45 min more. Operator chose Option 2; structural shape
  locked to scratch in 5 minutes; clean close. Pattern:
  brief-drafting is mode-distinct enough from triage and
  scope discussion that splitting at the shape-lock boundary
  is the cheap insurance against drafting-fatigue drift.
  Session 11 lesson — split rather than push through —
  applied prophylactically rather than reactively.

## Open items in (carried forward)

New from Session 95:

- **W4 follow-up Code brief drafting (Session 96 primary
  deliverable).** Brief scope locked Shape A (single combined
  workflow-layer mini-build with optional §13 contract
  clarification); structural shape locked across 12 sections;
  pre-flight grounding consolidated; ~400-500 line target.
  Open question for Session 96 drafting: does §5.5 contract
  clarification land in this brief or defer? Argument for
  landing: paragraph-level, paired with behaviour change keeps
  governance clean. Argument for deferring: keeps brief
  workflow-only mode-coherent. Operator-Claude call at
  Session 96 open.
- **Mid-session scratch writing as Cat 2 explicit pattern.**
  Surfacing triggers: (a) operator flags context concern, (b)
  substantive decisions accumulating not yet in artefact form,
  (c) session about to pivot mode. Carry-forward to next
  standing-instructions sweep.
- **Plain-operator-language default for Code-report content
  surfacing.** Cat 1 substrate confirmed by drift event this
  session. Carry-forward: when explaining Code-report
  deviations or findings, draft in plain-operator-language
  by default; technical detail belongs in artefacts, not in
  operator-facing surfacing.
- **`bash_tool` Cat 3 rule sharpening.** Confirmed
  non-functional at this session's open (first-attempt
  generic `view` / `bash_tool` calls failed with "no such
  directory"). Rule reads "non-functional in this
  environment" — possibly should sharpen to "non-functional
  in the Claude.ai web/mobile environment" to make the scope
  explicit. Carry-forward.
- **Brief-drafting pre-flight skill check.** Code's
  investigation surfaced findings that materially changed
  brief scope (Shape A vs Shape B). Pattern: brief-drafting
  skill Step 2 (pre-flight grounding) should explicitly call
  out "consider parallel Code investigation when codebase
  state matters and operator-Claude can't run read-only
  investigation directly." Carry-forward to next
  bethub-brief-drafting skill review.
- **Structural drift between Cat 1 framing-and-internals
  match check.** Session 94 brief contradicted itself
  (§1/§3 named W3 v1.0 reference pattern; §6.1/§6.2 specified
  library-call internals). Substrate from §7.1 deviation in
  v1.2 report. Carry-forward to next standing-instructions
  sweep — candidate for Cat 5 (operator-Claude division of
  labour) or Cat 1 (call-driven surfacing).

Carry-forward from Session 94 (status):

- **`bash_tool` standing-instruction softening candidate** —
  reinforced this session (see above).
- **`str_replace` namespace gotcha** — not exercised this
  session.
- **End-to-end-drafting-cadence-after-§1 as Cat 1 candidate**
  — not exercised this session (this session's brief drafting
  deferred to Session 96).
- **v3 composition-root structural decision** — sequenced
  Session 96+ (was Session 96 per Session 94 close;
  operator-Claude noted Session 96 has W4 follow-up brief as
  primary deliverable, so composition-root pushes back to
  Session 97+).
- **Real `BetfairAdapter` implementation brief** — sequenced
  Session 96+. Session 96's W4 follow-up brief lands the
  Protocol extension and the `price_source` field, both of
  which the real adapter brief inherits.
- **W4 brief amendment sweep** — unchanged.
- **Math review §6 arithmetic-step explicit update** —
  unchanged.
- **W6 broader sync reconciliation (`listClearedOrders` or
  similar)** — unchanged.
- **Brief / contract `placeOrders` vs `place_bet` naming
  alignment** — unchanged.
- **W4 brief locked at 2121 lines** — unchanged.
- **Storage-interface stub spec carry to W6 brief drafting**
  — unchanged.
- **§12.2 four-modules-vs-support-files clarification** —
  unchanged.
- **Brief-length-estimate calibration** — unchanged.
- **Round 13 workflow-ordering-validation pattern** —
  unchanged.
- **DR-032 locked** — drove `price_source` placement decision
  this session.
- **`architecture.md` §A.10 written** — unchanged.
- **Cross-reference integrity gap** — unchanged.
- **Legacy `§D12` reference cleanup** — unchanged.
- **Cat 4 paragraph re: "pending architectural extension
  (Session 42)" stale** — unchanged.
- **Hedge-staking math review locked at 1942 lines** —
  unchanged.
- **All other carry-forward items from Session 94 unchanged.**

## Open items out (closed this session)

- **`betfair_client` v1.2 contract addition Code report
  triage** (Session 94 carry-forward) — **closed.** Triage
  walked end-to-end: §7.1 deviation (W3-pattern locked),
  Findings 1/2/4 (no action), Finding 3 (folded into Session
  96+ adapter brief). All routing decisions logged.

## Session close state

- **Rebuild folder root:** unchanged this session. No edits to
  root-level governance files.
- **`current_state.md`:** updated at close — "Last updated"
  → `2026-05-07 09:16 ACST`; "Where we are" → v1.2 triage
  closed, W4 follow-up brief scope locked Shape A,
  structural shape locked, drafting deferred to Session 96;
  "What's next" → Session 96 drafts W4 follow-up brief from
  locked structural shape; required reads adjusted for
  Session 96.
- **`v3_build_picture.md`:** unchanged this session. No stream
  movement (W4 work continues blocked-on-W4-follow-up; W4.1 /
  W5 / W6 / W7 all sequenced behind it).
- **`standing_instructions.md`:** unchanged this session. Five
  sweep candidates accumulated:
  - (a) `bash_tool` softening (carried from Session 94,
    reinforced this session).
  - (b) `str_replace` namespace gotcha as Cat 3 absorption
    (carried from Session 94).
  - (c) End-to-end-drafting-cadence-after-§1-confirmation as
    Cat 1 candidate (carried from Session 94).
  - (d) Mid-session scratch writing as Cat 2 explicit pattern
    (new this session).
  - (e) Plain-operator-language default for Code-report
    content surfacing (new this session — confirmed by drift
    event).
  - (f) Brief-drafting-pattern-fidelity check in
    bethub-brief-drafting skill Step 2 — parallel Code
    investigation as named option when codebase state matters
    (new this session).
  Plus existing carry-forward sweep candidates from earlier
  sessions. Sweep deferred to fresh-mind session.
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session.
- **`decisions.md`:** unchanged this session.
- **`dr029/w4_bet_entry/`:**
  - `hedge_staking_math.md` — unchanged.
  - `w4_bet_entry_brief.md` — unchanged.
  - `w4_bet_entry_report.md` — unchanged. Read this session
    for §7.4 + §7.6 substrate.
  - `_drafts/SESSION_91_substrate.md` — unchanged.
  - `_drafts/SESSION_95_drafts.md` — **new this session**,
    written live across the session at 461 lines. Holds all
    locked Session 95 decisions plus locked brief scope and
    structural shape for Session 96 drafting.
  - `_drafts/SESSION_95_code_preflight.md` — **new this
    session**, written by Claude Code during parallel
    pre-flight phase at 207 lines.
  - `v1_2_contract_addition_brief.md` — unchanged.
  - `v1_2_contract_addition_report.md` — unchanged. Read this
    session for triage.
- **`sessions/`:** Session 95 record written by close ritual
  (this file).
- **`.close_out_backups/`:** Session 95 opening prompt removed
  at close; Session 96 opening prompt written.
- **Project knowledge base:** unchanged. No re-upload required
  this session.
- **VPS state:** unchanged this session. No VPS calls.
- **`bethub-v3/`:** unchanged in canonical state at session
  close. Code's investigation was read-only per the prompt
  hard-limits; no edits.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 96 opens fresh
chat. Primary deliverable is **draft the W4 follow-up Code
brief from the locked structural shape**, sized ~400-500
lines, single combined Shape A brief.

The brief drafts six coordinated workflow-layer changes:

1. `BetfairAdapter` Protocol extension — new "fetch fresh
   price" read-side method exposing existing `live_pricing`
   REST capability.
2. `BetRecord.price_source` field addition at
   `models.py:212-215` BetRecord operational metadata block.
   Optional with default `None`; backward-compatible.
3. Orchestrator `_place_with_retry` REST-fetch branch when
   `streaming_blocked` outcome arrives.
4. `record_builder.py` NULL handling for single-leg
   `soft_book_combined_price`.
5. (Optional) §13 contract clarification paragraph.
6. Naming canonicalisation across W3/W4 boundary.

Plus tests (~+8 to +12), pytest baseline 232 → 240-244
expected.

**Open question for Session 96 open:** does the §5.5 contract
clarification land in this brief or defer? Operator-Claude
makes the call at Session 96 brief-drafting Step 1 (job
naming).

**Sequence after Session 96:**

- Session 97 — operator-Claude triage of Session 96 Code's
  W4 follow-up report.
- Session 96+ alt — real `BetfairAdapter` implementation
  brief drafting (substantively unblocked once W4 follow-up
  brief ships, since the Protocol extension lands here).
- Session 97+ — v3 composition-root structural decision
  (pushed back from Session 96 to accommodate W4 follow-up
  brief drafting).
- W5 brief drafting — can open whenever; parallelisable.

**Out of scope for Session 96:**

- v3 composition-root structural decision drafting —
  sequenced Session 97+.
- Real `BetfairAdapter` implementation brief drafting —
  sequenced Session 96+ (parallel option) or Session 97+
  (sequential option, depends on Session 96 budget).
- Standing-instructions sweep — deferred to fresh-mind
  session. Six sweep candidates accumulating (see Session
  close state above).

**Operator-side actions between sessions:**

- **(Optional)** read `SESSION_95_drafts.md` end-to-end before
  Session 96 to refresh on locked brief scope and structural
  shape.
- **(Optional)** read `SESSION_95_code_preflight.md` for
  Code's pre-flight findings (file paths, line numbers,
  current state of W3/W4 boundary).
- **(Optional)** review the v1.2 contract amendment for
  content fit (carried from Session 94 — operator-side
  review is between-session work per Cat 4).
- **(Optional)** review `bethub-v3/clients/betfair_client/v1/account_funds.py`
  and `market_catalogue.py` from v1.2 build if curious.
- **(Optional)** run a real `get_account_funds()` call against
  the live Betfair API at low risk (read-only, no exposure).
  Note: Finding 3 means this needs `_translation.py` entry
  first, which lands in the real `BetfairAdapter` brief
  Session 96+.
- **(Lower priority)** Betfair API membership tier
  investigation; BetWatch response awaiting; review
  `bethub-analytical/README.md` activation timing.

## Close-out notes

Session 95 was a high-leverage session despite short wall-
clock. The v1.2 triage closed cleanly. The W4 follow-up
brief scope expanded twice during the session — first by
operator-driven framing pushback (terminal-with-message →
Option C REST fallback), second by Code's pre-flight
investigation (Shape B two-brief split → Shape A single
combined brief). Both expansions made the brief better; both
arrived through cadence the standing instructions name.

Three patterns worth holding onto:

- **Operator-driven framing pushback during scope discussion
  is load-bearing.** The "does that mean if Betfair goes
  down I have to leave the tool" question reframed §7.4
  from a clean-semantic call to an operational-cost call.
  Pattern: when proposing scope, check operational
  consequence before pitching as recommendation. W4 report
  itself was asking a question, not making a recommendation;
  treating reports as recommendations is a framing error
  worth catching.

- **Parallel pre-flight (operator-Claude documents +
  Claude Code codebase) is high-value for complex briefs.**
  Solo pre-flight would have missed the codebase findings
  that evaporated the Shape B rationale. Pattern: when brief
  scope depends on codebase state operator-Claude can't read
  directly, parallel investigation is fast and mode-coherent.

- **Mid-session scratch writing is a valid Cat 2 pattern.**
  Operator surfaced context-loss concern; operator-Claude
  wrote `SESSION_95_drafts.md` live and updated it across
  phases. Pattern: scratch can be written *during* a session,
  not only at close, when (a) operator flags context, (b)
  decisions accumulating not yet in artefact form, (c)
  session about to pivot mode and prior phase's decisions
  need to travel forward.

W4 follow-up brief scope locked. Structural shape locked.
Session 96 opens fresh-mind on drafting from the locked
shape.
