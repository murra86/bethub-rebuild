# Session 96

**Title:** W4 follow-up Code brief drafted end-to-end from
the Session-95-locked structural shape; three pre-drafting
operator calls confirmed (§5.5 contract clarification lands
as v1.3; `BetRecord.price_source` placement bet-record-level
not per-leg; modal recovery wiring at `_path_b_result:942-946`
left intact as cheap insurance for Betfair-fully-down edge
case); brief locked at 762 lines (50% over Session 95's
400-500 estimate; locked as-is per operator call); five
post-drafting calls surfaced and locked (length-overrun
no-tighten, §5.6 naming canonicalisation as Code's call,
§5.5 stamps v1.3, test target 8-12 with overflow allowed,
soft-no-touch on modal recovery wiring with one-line
comment); Code commission prompt produced and surfaced
hard-wrapped ~70 chars per Cat 1; brief drafting cadence
held end-to-end without operator-side surfacing during
sections per Cat 1 call-driven discipline (operator
confirmed end-to-end at Step 4 entry).
**Opened:** 2026-05-07 09:27 ACST
**Closed:** 2026-05-07 09:47 ACST
**Wall-clock:** ~20 minutes active session work. Same-workday
open relative to Session 95 close (~11 min gap; well under
the 4am same-workday cutoff). No day-rollover, no
pause-and-resume.
**Tool routing:** Claude Chat exclusively (brief drafting,
operator calls, Code prompt rendering). No Claude Code work
in this Chat session — Code commissioned via the prompt
produced at close for fresh out-of-session execution.
**Governing DRs invoked:** DR-021 (Adelaide local time),
DR-027 (two-database architecture — context for why
streaming-disconnect rule lives in `betfair_client` not v3),
DR-028 (cross-DB integration boundary discipline — same),
DR-030 (v3 repo layout — informs file locations in brief
§5.x), DR-031 (v3 tech stack — Pydantic v2 / pytest /
ruff / import-linter discipline encoded in brief),
DR-032 (canonical reference layer for all bet records —
drives bet-record-level `price_source` placement per §5.2),
DR-019 (derived state on read — informs single-leg-first
discipline for `price_source`).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
`2026-05-07 09:27 ACST`.
Close: same command → `2026-05-07 09:47 ACST`.

Same-workday open relative to Session 95 close at 09:16
ACST (11-min gap, single-sitting continuation). No
pause-and-resume.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, calibrated
against Cat 1 silent-ritual instruction:

- Rebuild root: 12 expected `.md` files present plus
  `openapi.json`, `external_api_resources.md`, `.DS_Store`.
  All directories present (`agent_review`, `diagrams`,
  `dr029`, `orchestration_pack`, `sessions`, `skills`,
  `.close_out_backups`).
- `.close_out_backups/` contained `SESSION_96_opening_prompt.md`
  only (Session 95 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated
  `2026-05-07 09:16 ACST` matched Session 95 close;
  `sessions/SESSION_95.md` present at 679 lines;
  `v3_build_picture.md` last-updated matched Session 94
  close (Session 95 made no stream movement, artefact
  untouched per close-out discipline).
- Same-workday recap delivered at 11-min gap.
- V3 build picture: skip-silent at open (no stream movement
  in 11-min gap).
- Open-items delta: skip-silent at open (no items
  closed/opened/overdue in 11-min gap).
- Governing DRs named at open: DR-027, DR-028, DR-030,
  DR-031, DR-032, DR-021. DR-029 named as closed.

Two operator-surfaced clarifications during open:

1. Operator's first message read "review new draft and
   provide operator calls or important decisions" —
   ambiguous between "review a draft I've produced
   between sessions" (no draft on disk) and "review the
   locked Session-95 substrate before drafting begins."
   Operator-Claude surfaced the ambiguity rather than
   guessing; operator clarified via paste of Session 95's
   close-out summary, which named the SESSION_95_drafts.md
   substrate explicitly. Substrate confirmed: read
   `SESSION_95_drafts.md` end-to-end, surface operator
   calls before drafting commences. Logged as Cat 1
   substrate — when "review draft" is ambiguous between
   between-session-product and locked-substrate, ask
   rather than guess.

## Session shape

Session 96 was a focused brief-drafting session running
the `bethub-brief-drafting` skill end-to-end against
Session 95's locked structural shape and scope. Three
distinct phases:

**Phase 1 — pre-drafting operator calls.** Operator-Claude
read `SESSION_95_drafts.md`, `SESSION_95_code_preflight.md`,
relevant W4 report sections, and contract §13/§9.1.
Surfaced three operator calls explicitly named in the
locked substrate as "operator-Claude call at Session 96
open":

- §5.5 contract clarification — land in this brief or
  defer? Operator: land. Reasoning: paragraph-level
  cost trivial; cleanup cost later if deferred is
  non-trivial; rule-vs-code drift is exactly what §13
  was built to prevent.
- `price_source` placement — `BetRecord` or `BetLeg`?
  Operator: BetRecord. Reasoning: W4 v1 single-leg only;
  per-leg is future-proofing for SGM (Strategy 3) which
  isn't built; one model-shape edit when SGM lands.
  DR-019 (derived state on read) discipline — don't
  model what isn't needed yet.
- `_path_b_result` modal recovery wiring — prune or
  leave? Operator: leave intact. Reasoning: cheap
  insurance for Betfair-fully-down edge case where REST
  also fails; pruning saves nothing and removes a
  fallback.

**Phase 2 — end-to-end drafting.** Operator confirmed
end-to-end over section-by-section (per the Session 35 /
Session 36 surgical-fix brief precedent). Brief drafted
in one pass against the 12-section locked spine. Anchored
edits validated against live `bethub-v3` filesystem
(BetRecord at lines 177-222 confirmed; orchestrator.py
1240 lines confirmed; live_pricing.py 207 lines confirmed;
placement.py 283 lines confirmed). Pydantic v2 / DR-032 /
DR-031 contract discipline encoded throughout.

Brief written to disk via `Desktop Commander:write_file`
at `dr029/w4_bet_entry/w4_followup_brief.md` — 762 lines,
~50% over Session 95's 400-500 estimate.

**Phase 3 — post-drafting operator calls + Code prompt.**
Surfaced five post-drafting calls:

- Length overrun — lock as-is or tighten? Operator: lock
  as-is (recommendation accepted). Locks brief at 762
  lines; carries "brief-length-estimate calibration" as
  Cat 5 sweep candidate.
- §5.6 naming canonicalisation — operator-call or
  Code's-call? Operator: Code's call (recommendation
  accepted). Brief leaves choice between W3-aligned
  (`betfair_streaming_disconnected`) and W4-aligned
  (`streaming_blocked`) with surfacing in Code's report
  deviations section.
- §5.5 contract version stamp — v1.3 or footnote on
  v1.2? Operator: v1.3 (recommendation accepted). Follows
  the v1.1 (F5 strategy_tag) precedent of recording
  running version even when not strictly required by
  §14.4.
- Test count target — 8-12 acceptable? Operator: yes
  (recommendation accepted). Overflow above 12 fine if
  Code surfaces additional cases worth covering.
- Modal recovery wiring touch — strict-no-touch or
  soft-no-touch with one-line comment? Operator:
  soft-no-touch (recommendation accepted). One-line
  comment naming why retained as rare-path fallback.

Code commission prompt produced hard-wrapped ~70 chars
per Cat 1 line-break rendering instruction. Surfaced in
chat for operator paste into fresh Code session.

## What was delivered

Session 96 produced one canonical artefact and one
session-substrate:

**W4 follow-up Code brief — `dr029/w4_bet_entry/w4_followup_brief.md`**
(762 lines, written end-to-end via `Desktop Commander:write_file`).
Single combined Shape A workflow-layer mini-build covering
six coordinated changes plus paragraph-level §13 contract
clarification:

- §5.1 — `BetfairAdapter` Protocol extension. New
  `fetch_fresh_runner_price(market_id, selection_id) ->
  RunnerBestPrices | None` read-side method exposing the
  existing W3 `live_pricing` REST capability.
  `MockBetfairAdapter` test hook lands in same edit.
- §5.2 — `BetRecord.price_source` field addition at
  `models.py:212-215` operational metadata block. New
  `PriceSource` enum (`STREAMING_CACHE` / `REST_FETCH` /
  `OPERATOR_TYPED`); optional default `None`;
  backward-compatible (BetRecord.frozen=True plus optional
  default).
- §5.3 — Orchestrator REST-fetch branch in
  `_place_with_retry` at lines 645-685. Three-step fallback
  chain: streaming cache → REST fetch → modal recovery
  (existing wiring at `:942-946` preserved as rare-path
  fallback).
- §5.4 — `record_builder.py` NULL handling for single-leg
  `soft_book_combined_price`. Logic change only; model
  field already `float | None` per Code preflight finding.
- §5.5 — §13 contract clarification paragraph naming the
  rule's intent post-REST-fetch. v1.3 backward-compatible
  addition per §14.4; status header + §6 history-row +
  §13 paragraph itself.
- §5.6 — Naming canonicalisation across W3/W4 boundary.
  Code's call between W3-aligned and W4-aligned canonical
  forms; surfaces in report deviations section.

Brief carries hard limits, sequencing, test scope (+8 to
+12 expected), empirical verification (pre-and-post
pytest baseline 232 → 240-244), output spec
(`w4_followup_report.md` 300-450 line target), what-
happens-after (Session 97 operator-Claude triage,
real adapter brief unblocked post-triage), cross-references
to W4 report / contract sections / DRs / Session 95
substrate.

**Code commission prompt rendered in chat** (not written
to disk; not load-bearing post-session). Hard-wrapped
~70 chars per Cat 1 line-break-rendering discipline. Names:
brief path; required pre-reads; system access (no API
calls, no git, MockBetfairAdapter); pre-change baseline
capture commands; build sequence per brief §6; modal
recovery wiring soft-no-touch directive; test target
overflow tolerance; post-change verification commands;
output path and section structure.

**No edits to canonical-truth files in this session.** No
edits to `decisions.md`, `architecture.md`, `governance.md`,
`standing_instructions.md`, `vision.md`,
`v3_data_requirements.md`, `project_context.md`. Brief is
session-substrate per `bethub-brief-drafting` skill —
becomes locked artefact at hand-off but doesn't modify
canonical truth.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-030,
  DR-031, DR-032, DR-021 named at open; DR-019 surfaced as
  substrate during `price_source` placement discussion.
  DR-029 named as closed gating arc.
- **Cat 1 (calendar-calibrated recap)** — same-workday
  tight recap delivered at 11-min gap.
- **Cat 1 (V3 build picture conditional render)** —
  skip-silent at open (no stream movement). Not updated at
  this close (no stream movement during session).
- **Cat 1 (open-items delta)** — skip-silent at open (no
  movement in 11-min gap).
- **Cat 1 (drift-check)** — done at open, all three checks
  matched.
- **Cat 1 (silent session-open ritual)** — held. Steps 1-5
  silent except for the "review new draft" ambiguity
  surface (operator clarification required, surfaced
  appropriately rather than guessed).
- **Cat 1 (silent session-close ritual)** — holding this
  close. Steps 1-10 silent; Step 11 produces brief
  verification line.
- **Cat 1 (call-driven surfacing during section-by-section)**
  — held with mode variant. Operator confirmed end-to-end
  over section-by-section at brief-drafting Step 4 entry;
  no in-flight section surfacing during draft execution
  (call-driven discipline applied at brief-as-a-whole
  granularity rather than per-section). Post-drafting
  surfacing held to five operator-relevant calls.
- **Cat 1 (short responses, plain language)** — held
  throughout. No drift events this session.
- **Cat 1 (decision-maker framing)** — held. Three
  pre-drafting calls and five post-drafting calls each led
  with the call or recommendation; reasoning followed.
- **Cat 1 (don't drift to alternatives when operator
  clear)** — held. Operator's "happy with your
  recommendations" acted on without re-litigating any
  individual call.
- **Cat 1 (escalate to detail only when warranted)** —
  held. Pre-drafting calls warranted detail (load-bearing
  for SGM-future, contract-vs-code drift, fallback
  insurance). Post-drafting calls were tighter — length
  overrun, naming canonical form, version stamp, test
  range, soft-vs-strict touch — and surfaced as such.
- **Cat 1 (line-break rendering for review content)** —
  held. Code prompt rendered hard-wrapped ~70 chars in
  fenced block.
- **Cat 1 (default to luddite-analyst-gambler brevity)**
  — held throughout.
- **Cat 1 (plain-operator-language default for Code-report
  content surfacing)** — n/a this session (no Code-report
  content surfaced; this was brief-drafting, not triage).
- **Cat 2 (timestamp re-anchoring)** — open and close
  anchored. No pause-and-resume mid-session.
- **Cat 2 (pre-flight directory listing)** — done at open.
  Done implicitly at close via list_directory checks for
  Step 9 and Step 11.
- **Cat 2 (Desktop Commander default)** — held throughout.
  All file ops via `Desktop Commander:list_directory`,
  `Desktop Commander:read_file`,
  `Desktop Commander:start_process`,
  `Desktop Commander:write_file`. No `bash_tool` attempts
  this session (compared to Session 95 where the open
  ritual hit it).
- **Cat 2 (REPL discipline)** — n/a; no multi-line Python
  this session.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)**
  — held. Brief written via `Desktop Commander:write_file`
  to canonical Mac path; verified post-write via
  `Desktop Commander:start_process` `wc -l` (762 lines on
  disk matching tool output count).
- **Cat 2 (dry-run multi-target mechanical edits)** —
  n/a; brief was a single fresh-write, not a multi-target
  edit.
- **Cat 2 (persist drafted artefact content to scratch)**
  — n/a; this session's draft *is* the canonical artefact
  (locked brief), not session-scratch deferred to a
  future session. Session 95's substrate was the scratch;
  Session 96 promoted it to the locked brief.
- **Cat 2 (surface structural-drift in session record)**
  — no governance artefact structure changed this session.
  Brief is a fresh artefact; doesn't modify any existing
  governance file's structure.
- **Cat 3 (`bash_tool` non-functional)** — held by absence;
  no `bash_tool` calls attempted this session.
- **Cat 3 (external API resources reach-for)** — n/a this
  session.
- **Cat 4 (DR-027/028 invoked)** — named at open.
  Referenced during §13 contract clarification discussion
  (DR-028's "no second integration point" frames why
  streaming-disconnect rule lives in `betfair_client` not
  v3 modules — encoded in brief §5.5 reasoning).
- **Cat 4 (operational/analytical line discipline)** —
  held. Brief frames new `price_source` and REST-fetch
  branch as operational-line work; no analytical-line
  cross-contamination.
- **Cat 4 (single-cycle analysis discipline)** — n/a this
  session.
- **Cat 4 (Betfair as canonical source)** — load-bearing
  for `price_source` placement decision (DR-032's
  per-leg snapshot fields adjacent on BetRecord
  operational metadata block).
- **Cat 5 (software questions are Claude's)** — held
  throughout. Brief structural shape, anchor verification,
  Pydantic field signatures, fallback chain design —
  all Claude's calls. Operator surfaced strategic
  questions only (does this affect strategy 1, future-
  proof for SGM, contract drift risk).

## Session-96-specific reflections

- **End-to-end drafting cadence held cleanly.** Operator
  confirmed end-to-end at Step 4 entry; brief drafted in
  one pass against the locked spine; no in-flight
  operator-side surfacing required during draft execution.
  Post-drafting surfacing held to five operator-relevant
  calls, all locked in one round. Pattern: when
  pre-drafting calls are settled and the structural shape
  is locked, end-to-end drafting is mode-coherent and
  operator-budget-cheap. Cat 1 candidate: encode
  end-to-end-after-§1 cadence as explicit option
  alongside section-by-section default. Carry-forward to
  next standing-instructions sweep (already named
  Session 94 carry-forward).

- **Brief-length estimate gap of ~50% locks calibration
  problem.** Session 95's structural shape was 12
  sections, ~400-500 line estimate. Brief landed at 762
  lines with no padding. The same gap surfaced on the
  W4 v1 brief (target 1500-1800; landed 2121, ~20%
  over) and was less acute on the v1.2 contract addition
  brief (target ~400; landed ~440, ~10% over). Pattern:
  workflow-layer mini-builds estimate low because
  per-section anchor density compounds across sections.
  Carry-forward as Cat 5 candidate: brief-length
  estimates should add per-section overhead (~30-40 lines)
  beyond the "what each section covers" content.

- **Pre-drafting operator calls were genuinely
  load-bearing.** All three calls (§5.5 land, BetRecord
  placement, modal recovery intact) materially shaped the
  brief structure. §5.5 added §5.5 + §6 (sequencing
  position) + §12 (cross-references). BetRecord
  placement vs BetLeg changed the field's semantic and
  the SGM-future rationale. Modal recovery intact
  changed the fallback chain wording in §5.3 (rare-path
  fallback) and added a hard-limit constraint in §9. Had
  these been deferred to Code's report deviations, the
  brief would have committed to choices Code would have
  flagged back. Pattern: pre-drafting calls on locked
  substrate items named "operator-Claude call at next
  open" are high-leverage; settling them at session open
  rather than during drafting keeps the brief
  mode-coherent.

- **Post-drafting calls surfaced cheap secondary
  decisions.** Five post-drafting calls each took
  one-or-two-sentence operator-side framing and one-line
  decisions. None required re-drafting any section; all
  fit in the brief's existing structure. Pattern:
  post-drafting surfacing is the right place for cheap
  calibration calls (length tolerance, naming-as-Code's-
  call, version-stamp convention, test-range tolerance,
  soft-vs-strict touch wording) — they don't earn their
  way into the brief's substantive scope but matter for
  brief-as-locked-contract clarity.

- **Substrate for "review new draft" ambiguity-resolution
  pattern.** Operator's first message was ambiguous
  between two readings; operator-Claude surfaced rather
  than guessed; operator's clarification (Session 95
  close-out paste) made the substrate clear. Pattern:
  when "review X" is ambiguous between between-session-
  product and locked-substrate, ask before reading.
  Carry-forward to next standing-instructions sweep —
  candidate for Cat 1 (call-driven surfacing).

## Open items in (carried forward)

New from Session 96:

- **W4 follow-up brief Code execution (Session 96+
  out-of-session).** Brief locked at 762 lines; Code
  commission prompt rendered. Operator's between-session
  action: paste prompt into fresh Code session; let Code
  execute end-to-end; report lands at
  `dr029/w4_bet_entry/w4_followup_report.md`.
- **W4 follow-up Code report triage (Session 97 primary
  deliverable).** Read Code's report; walk deviations
  (especially §5.6 canonical name choice + modal recovery
  comment wording); walk open questions; route findings.
- **End-to-end-drafting cadence as Cat 1 explicit
  variant.** Reinforced this session (operator confirmed
  end-to-end at Step 4 entry; brief drafted clean in one
  pass). Originally surfaced Session 94. Carry-forward to
  next sweep.
- **Brief-length-estimate calibration as Cat 5
  candidate.** This session's gap (50% over) plus
  precedent gaps (W4 v1 20% over; v1.2 contract addition
  10% over) confirm pattern. Carry-forward to next sweep.
- **"Review X" ambiguity-resolution as Cat 1
  candidate.** Substrate from this session's open
  ambiguity. Carry-forward.

**Carry-forward from Session 95 (status):**

- **Mid-session scratch writing as Cat 2 explicit
  pattern** — not exercised this session (no mid-session
  pivot triggers). Carry-forward.
- **Plain-operator-language default for Code-report
  content surfacing** — n/a this session. Carry-forward.
- **`bash_tool` Cat 3 rule sharpening** — not exercised
  this session (no `bash_tool` attempts). Carry-forward.
- **Brief-drafting pre-flight skill check — parallel
  Code investigation as named option** — not exercised
  this session (pre-flight grounding from Session 95
  consolidated; no fresh Code investigation needed).
  Carry-forward.
- **Structural drift between Cat 1 framing-and-internals
  match check** — not exercised this session (brief was
  fresh, no prior reference pattern to drift from).
  Carry-forward.
- **`bash_tool` standing-instruction softening
  candidate** — not reinforced this session (no calls
  attempted). Carry-forward.
- **`str_replace` namespace gotcha substrate** — not
  exercised this session (only `write_file` used).
  Carry-forward.

**Carry-forward from earlier sessions (unchanged unless
noted):**

- **v3 composition-root structural decision** —
  sequenced Session 97+ (pushed back twice already;
  Session 95 deferred for v1.2 triage; Session 96
  deferred for W4 follow-up brief drafting). Genuinely
  next deliverable candidate post-Session-97 triage.
- **Real `BetfairAdapter` implementation brief** —
  sequenced Session 97+. **Substantively unblocked once
  Code's W4 follow-up report ships clean** — the
  Protocol extension and `price_source` field both land
  in this brief; the real adapter brief inherits both
  shapes.
- **W4 brief amendment sweep** — unchanged. Cosmetic
  carry.
- **Math review §6 arithmetic-step explicit update** —
  cosmetic.
- **W6 broader sync reconciliation —
  `listClearedOrders` or similar** — §8.6 carry. Routes
  to W6 brief drafting.
- **Brief / contract `placeOrders` vs `place_bet`
  naming alignment** — §8.4 carry. Cosmetic.
- **W4 brief locked at 2121 lines** — unchanged.
- **Storage-interface stub spec carry to W6 brief
  drafting** — unchanged.
- **§12.2 four-modules-vs-support-files clarification as
  `standing_instructions.md` candidate** — unchanged.
- **Round 13 workflow-ordering-validation pattern as
  Cat 4 candidate** — unchanged.
- **DR-032 locked** — drove `price_source` placement
  decision Session 95; reinforced this session.
- **`architecture.md` §A.10 written** — unchanged.
- **Cross-reference integrity gap** — unchanged. Cat 2
  candidate.
- **Legacy `§D12` reference cleanup at next
  documentation sweep** — unchanged.
- **Cat 4 paragraph re: "pending architectural extension
  (Session 42)" stale** — unchanged. Flag for next
  sweep.
- **Hedge-staking math review locked at 1942 lines** —
  unchanged.
- **Substrate revision flag for W4 brief drafting** —
  unchanged.
- **Effective-odds synthesis as racing-screen → modal
  flow** — unchanged.
- **Default free-bet conversion rate 65%; operator-
  configurable** — unchanged.
- **Manual stake override as future refinement** —
  unchanged.
- **Multi-rung ladder hedge as future arc** — unchanged.
- **`EX_LADDER` operator-side homework parked** —
  unchanged.
- **W4 substrate decisions captured Session 87** —
  unchanged.
- **F5 strategy_tag carry forward** — unchanged.
- **Streaming envelope vocabulary carry-forward** —
  unchanged.
- **Manual free-bet ledger entry workflow** — unchanged.
- **Deployment-substrate items (F2, F3, F4)** —
  unchanged.
- **F6 carry-forward to Fix 4 brief + W3+ briefs** —
  unchanged.
- **§12 self-assessment item 3 — audit-log durable
  substrate selection** — unchanged.
- **W1 F2 sharpening — capture.db Thoroughbred label
  includes harness undifferentiated** — unchanged.
- **W1 F1 accepted as v1.0 conflation** — unchanged.
- **W0 F2 brief-language carry** — unchanged.
- **DR-030 "18 months" reference correction** —
  unchanged.
- **`governance.md` §4 deferred-capability
  reconciliation** — unchanged.
- **Jump-anchor design reframe** — unchanged.
- **Post-DR-029-close contract documentation
  relocation** — empty `bethub-v3/contracts/` folder
  confirmed Session 94; relocation remains deferred.
- **Sports-side dead-heat capture in `architecture.md`
  §B.1.4** — unchanged.
- **Past-settlement-window threshold calibration** —
  unchanged.
- **Settlement worker periodic verification cadence** —
  unchanged.
- **Cluster 1 surgical-fix carry-in (analytical-layer
  prep)** — unchanged.
- **Fix 9 / Fix 10 / three-row collision triage / low-
  confidence match review** — unchanged.
- **Complete cascade map** — parked.
- **CLV as analytical-layer signal** — built post-DR-029.
- **Path-(iii) reconciliation-job scheduling and
  operator-facing flag-queue UI** — unchanged.
- **§2.9 §4.4 six edge cases** — unchanged.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — unchanged.
- **Session numbering slip in probe brief** — cosmetic.
- **EX_LADDER entitlement question** — operator-side
  homework.
- **Drift-check methodology gap** — substrate from
  Session 64 carry-forward.
- **`bethub-analytical` project awaiting activation** —
  operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** —
  parked.
- **§2.1 BSP-fix code finding (c) — stale
  `client.py:189` docstring** — non-gating.
- **BetWatch contacted re: API service and book
  coverage** — awaiting response.
- **Betfair API membership tiers — investigate.**
  Operator-side homework. Now relevant to ladder
  reconstruction future arc per §7.5 nuance discussion.
- **PASSIVE bet-delay model handling** — flagged in
  §2.4 §15.4 as v3.1+ capability.
- **Betfair contact re: `EX_LADDER` entitlement and
  pricing** — operator-side parallel action.
- **Betfair contact re: `EX_TRADED_VOLUME` projection
  cost and entitlement** — operator-side parallel
  action.
- **Cluster C capture-routing decision** — deferred.
- **Racing API value assessment** — post-DR-029
  strategic decision.
- **v3 build-proper UI candidates** — three surfaces
  logged §5.2 of §2.10 brief.
- **Betfair SP-projection accuracy study** — post-DR-029
  analytical capability candidate.
- **Racing EV model recalibration with §2.10 bucket-1
  captures** — post-DR-029 analytical work.
- **WIP §16** — VPS in-flight work. Unchanged.

Closed this session:

- **W4 follow-up Code brief drafting** (Session 95
  primary-deliverable carry) — **closed.** Brief locked
  at `dr029/w4_bet_entry/w4_followup_brief.md`, 762
  lines, ready for Code commission via prompt rendered
  in chat at session close. All five locked Session 95
  decisions encoded; all three pre-drafting operator
  calls applied; all five post-drafting operator calls
  resolved.

Gaps from earlier reviews (logged for awareness):

- **Claude-67 G1** — AU-specific session expiry not on
  disk.
- **Claude-67 G2** — `listCurrencyRates` API surface
  silent in captured reference.
- **Claude-67 G3** — Racing API ↔ Betfair market identity
  reconciliation implicit. Now formally addressed in
  DR-032 §7 — Racing API joins go via capture.db's
  internal resolution layer, code-driven post-hoc, never
  at logging time.
- **Claude-67 G4** — `listCurrentOrders` filter parameter
  list not in captured reference. Addressed in W4 brief
  §6.3 by both-paths spec.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC` betDelay
  confidence note. Partly addressed Session 76.

## Open items out (closed this session)

- **W4 follow-up Code brief drafting** (Session 95 primary
  deliverable carry) — **closed.** Brief locked at 762
  lines on disk; Code commission prompt produced and
  surfaced.

## Session close state

- **Rebuild folder root:** unchanged this session. No
  edits to root-level governance files.
- **`current_state.md`:** updated at close — "Last
  updated" → `2026-05-07 09:47 ACST`; "Where we are" →
  W4 follow-up brief locked, Code commission prompt
  produced, ready for out-of-session execution; "What's
  next" → Session 97 triage of Code's report (when it
  ships); required reads adjusted for Session 97.
- **`v3_build_picture.md`:** unchanged this session. No
  stream movement (W4 follow-up brief locks the
  Protocol extension and `price_source` field but Code
  hasn't executed yet; W4 stream stays
  blocked-on-W4-follow-up until Code's report ships and
  triage closes).
- **`standing_instructions.md`:** unchanged this session.
  Eight sweep candidates accumulating now:
  - (a) `bash_tool` softening (carried from Session 94,
    reinforced Session 95).
  - (b) `str_replace` namespace gotcha as Cat 3
    absorption (carried from Session 94).
  - (c) End-to-end-drafting-cadence-after-§1-confirmation
    as Cat 1 candidate (reinforced this session).
  - (d) Mid-session scratch writing as Cat 2 explicit
    pattern (Session 95 carry).
  - (e) Plain-operator-language default for Code-report
    content surfacing (Session 95 carry).
  - (f) Brief-drafting-pattern-fidelity check in
    bethub-brief-drafting skill Step 2 — parallel Code
    investigation as named option (Session 95 carry).
  - (g) Structural-drift framing-vs-internals match
    check (Session 95 carry).
  - (h) Brief-length-estimate calibration as Cat 5
    candidate (new this session).
  - (i) "Review X" ambiguity-resolution pattern as Cat 1
    candidate (new this session).
  Sweep deferred to fresh-mind session. Eight-or-nine
  candidates is enough mass for a dedicated
  standing-instructions sweep session post-Session-97
  triage.
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session.
- **`decisions.md`:** unchanged this session.
- **`dr029/w4_bet_entry/`:**
  - `hedge_staking_math.md` — unchanged.
  - `w4_bet_entry_brief.md` — unchanged.
  - `w4_bet_entry_report.md` — unchanged. Read this
    session for §7.4 + §7.6 anchors.
  - `_drafts/SESSION_91_substrate.md` — unchanged.
  - `_drafts/SESSION_95_drafts.md` — unchanged. Read
    this session for locked scope and structural shape.
  - `_drafts/SESSION_95_code_preflight.md` — unchanged.
    Read this session for anchor verification.
  - `v1_2_contract_addition_brief.md` — unchanged.
  - `v1_2_contract_addition_report.md` — unchanged.
  - **`w4_followup_brief.md`** — **new this session**,
    written at 762 lines via
    `Desktop Commander:write_file`. Locked Code-bound
    brief; Session 96 primary deliverable.
- **`sessions/`:** Session 96 record written by close
  ritual (this file).
- **`.close_out_backups/`:** Session 96 opening prompt
  removed at close; Session 97 opening prompt written.
- **Project knowledge base:** unchanged. No re-upload
  required this session.
- **VPS state:** unchanged this session. No VPS calls.
- **`bethub-v3/`:** unchanged in canonical state at
  session close. Read-only verification queries via
  `Desktop Commander` (line counts and BetRecord field
  ranges) for brief anchor confirmation; no edits.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 97 opens
fresh chat after Code executes the W4 follow-up brief
out-of-session. Primary deliverable is **triage Code's
report** at `dr029/w4_bet_entry/w4_followup_report.md`.

**Operator's between-session actions:**

1. **Paste Code commission prompt into a fresh Claude
   Code session.** Prompt produced at session close,
   hard-wrapped ~70 chars per Cat 1.
2. **Let Code execute end-to-end.** Single bounded
   session per brief §9 hard limits. No operator
   escalation mid-session per Code's brief instructions.
3. **Review Code's report when it ships.** Optional —
   Session 97 triage walks the report end-to-end with
   operator-Claude.
4. **(Optional) Review the brief itself between
   sessions.** Brief locked at 762 lines; readable for
   operator confirmation if desired before Code runs.

**Sequence after Session 97:**

- Real `BetfairAdapter` implementation brief drafting
  becomes the natural next deliverable once Session 97
  closes clean (Protocol extension and `price_source`
  field both land in the W4 follow-up build, so the
  real adapter brief inherits both shapes).
- v3 composition-root structural decision drafting
  remains sequenced for whenever it next slots in
  (Session 98+ depending on real adapter brief
  sequencing).
- Standing-instructions sweep — eight to nine candidates
  accumulated; dedicated fresh-mind session whenever
  operator wants. No gating dependency.

**Out of scope for Session 97:**

- New brief drafting (Session 97 is triage, not new
  scope work).
- Standing-instructions sweep (deferred to dedicated
  session).
- v3 composition-root structural decision drafting
  (sequenced Session 98+).

**Triage shape for Session 97:**

1. Read Code's report end-to-end.
2. Walk §6 deviations — confirm Code's calls (§5.6
   canonical name choice; modal recovery comment
   wording; any other deviations).
3. Walk §7 open questions one per round, plain-operator-
   language framing per Cat 1.
4. Walk §8 findings — route each (no action / fold
   into existing carry / new brief / contract-
   housekeeping sweep).
5. Lock close-out: brief closed; W4 follow-up arc
   complete; carry-forward items into `current_state.md`.

## Close-out notes

Session 96 was a clean, focused brief-drafting session.
Wall-clock 20 minutes — well under split-trigger
thresholds. Three pre-drafting calls landed cleanly;
end-to-end drafting cadence held; five post-drafting
calls resolved in one round; Code commission prompt
produced.

Three patterns worth holding onto:

- **End-to-end drafting after pre-drafting calls settle
  is mode-coherent and operator-budget-cheap.** When the
  structural shape is locked from prior session and
  pre-drafting calls clear, drafting in one pass against
  the spine is faster, less interruption-shaped, and
  produces tighter cross-section coherence than
  section-by-section. Cat 1 candidate.

- **Brief-length estimates locked at session-prior
  systematically under-call by 20-50%.** Per-section
  anchor density compounds; pre-drafting estimates
  capture content but not the structural overhead.
  Cat 5 candidate; brief-length estimates should add
  ~30-40 lines per section beyond content.

- **Pre-drafting operator calls earn their session-budget
  cost.** All three calls this session materially shaped
  the brief; deferring to Code's report deviations would
  have meant Code committing and then operator-Claude
  unwinding. Pattern: when a locked substrate names
  "operator-Claude call at next open," settle the call
  pre-drafting rather than letting the brief commit
  blind.

W4 follow-up brief locked. Code commission prompt
produced. Session 97 ready to triage Code's report
whenever it ships.
