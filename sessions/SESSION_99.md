# Session 99

**Title:** Real `BetfairAdapter` implementation brief
drafted end-to-end (1386 lines) and locked at
`dr029/w4_bet_entry/real_adapter_brief.md`. Three context-
loss gaps caught during drafting and addressed in-brief
(W3 `list_current_orders` may not exist; `place_bet`
streaming-client invariant; `assert_type` Protocol
conformance shape). Two boundary translations folded into
brief scope per Session 98 §7.1 routing call
(`MARKET_SUSPENDED` → `market_suspended`,
`INSUFFICIENT_FUNDS` → `insufficient_funds`). Brief uses
W4 follow-up brief as structural template (universal
spine, end-to-end drafting after operator confirmation).
Single bounded Code session sequenced for execution
between Sessions 99 and 100; Session 100 triages report.

**Opened:** 2026-05-07 14:26 ACST
**Closed:** 2026-05-07 14:48 ACST
**Wall-clock:** ~22 minutes active session work. Same-
workday open relative to Session 98 close (~52m gap;
single-sitting workday continuation, no pause-and-
resume, no day-rollover).
**Tool routing:** Claude Chat exclusively (substrate
reads, live v3 codebase grounding, brief drafting end-to-
end, brief written via `Desktop Commander:write_file`).
No Claude Code work this Chat session — Code execution
of this brief deferred to between-session Code run per
operator close call.
**Governing DRs invoked:** DR-021 (Adelaide local time —
open and close anchors), DR-027 (two-database
architecture — context for streaming-disconnect rule
location), DR-028 (cross-DB integration boundary
discipline — context for adapter as W4-side glue),
DR-030 (v3 repo layout — informs `betfair_adapter.py`
placement at `workflows/bet_entry/v1/`), DR-031 (v3 tech
stack — Pydantic v2, pytest, ruff, import-linter),
DR-032 (canonical reference layer for all bet records —
informs boundary translation discipline), DR-019
(derived state on read — context for adapter's no-cache
discipline).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
`2026-05-07 14:26 ACST`.
Close: same command → `2026-05-07 14:48 ACST`.

Same-workday open relative to Session 98 close at 13:34
ACST (52m gap). No pause-and-resume mid-session.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill. Held
silent; no operator-facing surfaces required.

- Rebuild root: 12 expected files present (11 governance
  `.md` + `v3_build_picture.md`) plus `openapi.json`,
  `external_api_resources.md`, `.DS_Store`. All
  directories present (`agent_review`, `diagrams`,
  `dr029`, `orchestration_pack`, `sessions`, `skills`,
  `.close_out_backups`).
- `.close_out_backups/` contained
  `SESSION_99_opening_prompt.md` only (Session 98 close
  artefact, expected).
- Drift-check passed: `current_state.md` last-updated
  `2026-05-07 13:34 ACST` matched Session 98 close;
  `sessions/SESSION_98.md` present at 923 lines;
  `v3_build_picture.md` last-updated matched Session 98
  close (W4 stream dropped per one-session carry rule).
- Same-workday recap delivered at 52m gap (tight, one-
  sentence framing).
- V3 build picture: skip-silent at open (no stream
  movement in 52m gap).
- Open-items delta at open: skip-silent at open (no
  meaningful delta in 52m gap).
- Governing DRs named at open: DR-027, DR-028, DR-030,
  DR-031, DR-032, DR-019, DR-021. DR-029 named as closed.

**One open-ritual deviation worth naming.** The
`bash_tool` Step 1 timestamp attempt fired again (sweep
candidate (a) reinforced once more). Recovered via
`tool_search` for Desktop Commander; ran the canonical
`Desktop Commander:start_process` form. Same pattern
seen Session 98 and prior; standing-instruction
softening candidate continues to accumulate evidence.

## Session shape

Session 99 was a focused single-purpose session that
closed its primary deliverable (real adapter brief
drafted and locked) cleanly without split-trigger
pressure. Three sub-phases:

**Sub-phase A — substrate grounding.** Read the four
named substrate files end-to-end: W4 follow-up brief
(762 lines), W4 follow-up report (447 lines),
housekeeping report (413 lines), W4 v1 brief (partial —
600 lines of 2121 plus targeted greps for the mock-vs-
real seam). Plus contract sections §9.1, §9.6, §9.7,
§11.1, §13 (post-v1.3 amendment) per pre-reads list.
Plus live v3 codebase probing: `clients/betfair_client/v1/`
file inventory (175-line public surface, 21 modules
including `_translation.py` at 664 LOC and `streaming.py`
at 595 LOC), `workflows/bet_entry/v1/` post-housekeeping
state (1356-line orchestrator, 355-line models, 440-line
storage stub), `BetfairAdapter` Protocol shape
(orchestrator.py:166–220, five methods), recovery-key
chain location (orchestrator.py:1049–1058), test fixture
location (test_orchestrator.py:581+589).

**Sub-phase B — structural shape call + decision
surfacing.** Two operator-facing rounds: Step 3
structural-shape call (W4 follow-up brief over W4 v1
brief as template — operator confirmed); Step 5 calls
made in the brief — five anchored decisions surfaced
(adapter location at W4-side, boundary translation as
named subsection, mock stays as-is, REST-only scope
boundary, mocked-REST integration tests only).
Operator confirmed all five plus added an explicit ask:
include contradiction-and-context-loss safeguard for
Code. Folded into §1 + §9 of the brief.

**Sub-phase C — end-to-end brief drafting and lock.**
Sections §1–§4 walked one round per section per Cat 1.
Sections §5–§12 drafted silently per operator's
"draft up the rest" call (call-driven cadence, sweep
candidate (c) end-to-end drafting after §1
confirmation reinforced once more). Single
`Desktop Commander:write_file` produced the final
1386-line artefact at canonical path. Post-write
verification: line count matches expected, SHA captured,
file exists at named path.

## What was delivered

Session 99 produced one substantive artefact:

**Real `BetfairAdapter` implementation brief** at
`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w4_bet_entry/real_adapter_brief.md`
(1386 lines, SHA `65d7c8824d4ba851c689e9bd3e9889e16cfe609973427a26785307f5baeaadf0`).
Universal section spine (§1 what-this-is, §2 why-this-
exists, §3 pre-reads, §4 system access, §5 substantive
scope across nine subsections, §6 sequencing, §7 test
scope across seven subsections, §8 empirical
verification, §9 hard limits, §10 output spec, §11 what-
happens-after, §12 cross-references). Brief commissions:

- New module `workflows/bet_entry/v1/betfair_adapter.py`
  (estimated 300–500 LOC) implementing the five-method
  `BetfairAdapter` Protocol: `get_market_status`,
  `get_account_funds`, `place_hedge_bet`,
  `get_order_state`, `fetch_fresh_runner_price`.
- Boundary translation layer (write-envelope
  discrimination per §5.2(b) + upper-snake-to-lower-snake
  per §5.2(c)) covering `MARKET_SUSPENDED` →
  `market_suspended` and `INSUFFICIENT_FUNDS` →
  `insufficient_funds` translations.
- New test module
  `tests/workflows/bet_entry/v1/test_betfair_adapter.py`
  (estimated 400–600 LOC, 10–18 new tests) with mocked
  `BetfairRestClient` integration coverage.
- Surgical `INSUFFICIENT_FUNDS` rename at
  `orchestrator.py:1049` plus matching test fixture at
  `test_orchestrator.py:581+589` per Session 98 §7.1
  routing call.
- `__init__.py` re-export update for `RealBetfairAdapter`.

**Five operator-facing calls landed.**

- (a) Structural shape: W4 follow-up brief as template
  over W4 v1 brief.
- (b) Adapter location: W4-side at
  `workflows/bet_entry/v1/`, not W3-internal.
- (c) Boundary translation as named subsection (§5.2)
  rather than inlined per method.
- (d) MockBetfairAdapter stays as-is; real adapter has
  its own dedicated test module.
- (e) Test scope: mocked-REST integration only
  (no pure-unit, no real-API).

Plus operator's added safeguard: contradiction-and-
context-loss flagging discipline for Code (folded into
brief §1 + §9).

**Three context-loss gaps caught during drafting.**

- (i) **W3 `list_current_orders` may not exist as a
  public surface.** §5.6 of the brief includes a
  fallback path: if the surface exists, Code uses it
  directly; if not, Code stubs `get_order_state` to
  return `None` and surfaces the gap as the brief's
  primary §8 finding. Trigger B reconciliation
  cannot run against the real adapter until that W3
  surface lands — likely a fresh contract-work brief
  candidate after Session 100 triage.
- (ii) **`place_bet` requires `streaming_client`
  (non-None)** for the §13 streaming-state pre-check.
  Locked as construction-time invariant in §5.1 with
  `__post_init__` raising on `streaming_client=None`.
  Software-shape decision per Cat 5; resolved
  in-brief.
- (iii) **`assert_type` for Protocol conformance may
  not be the right shape under Python 3.12.** Named
  preferred mechanism in §5.1 with operator-Claude
  framing-as-Code-call escape valve to alternative
  (`_: BetfairAdapter = ...` at module scope) if
  `assert_type` doesn't lint cleanly. Code chooses;
  named in §6 deviations of report.

**Brief length ran above estimate.** 1386 lines vs my
800–1200 estimate (operator-confirmed acceptable as-is).
Reinforces sweep candidate (h) — brief-length-estimate
calibration as Cat 5 candidate. Pattern: estimates
consistently 30–50% under actual; cumulative evidence
strong now.

**No edits to canonical-truth files this session.** No
edits to `decisions.md`, `architecture.md`,
`governance.md`, `standing_instructions.md`, `vision.md`,
`v3_data_requirements.md`, `project_context.md`. Brief
is the substantive write of the session.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028,
  DR-030, DR-031, DR-032, DR-019, DR-021 named at open.
  DR-029 named as closed gating arc.
- **Cat 1 (calendar-calibrated recap)** — same-workday
  tight recap delivered at 52m gap.
- **Cat 1 (V3 build picture conditional render)** —
  skip-silent at open (no stream movement in 52m gap).
- **Cat 1 (open-items delta)** — skip-silent at open
  (no meaningful delta in 52m gap).
- **Cat 1 (drift-check)** — done at open, all three
  checks matched Session 98 close.
- **Cat 1 (silent session-open ritual)** — held; no
  operator-facing surfaces required at open.
- **Cat 1 (silent session-close ritual)** — holding
  this close. Steps 1–10 silent except for Step 2's
  forward-routing confirmation (operator's "close
  session" instruction itself confirms forward routing
  for between-session Code execution); Step 11
  produces brief verification line.
- **Cat 1 (call-driven surfacing during section-by-
  section)** — held; sections §1–§4 walked one per
  round, sections §5–§12 drafted silently per
  operator's "draft up the rest" call. Reinforces
  sweep candidate (c) end-to-end drafting after §1
  confirmation.
- **Cat 1 (short responses, plain language)** — held
  throughout. Calls surfaced as numbered lists with
  framing + recommendation + reasoning. No long
  preambles.
- **Cat 1 (decision-maker framing)** — held. Each
  call led with the situation, the recommendation,
  and the reasoning.
- **Cat 1 (don't drift to alternatives when operator
  clear)** — held. Operator's "draft up the rest"
  acted on directly; no second-guessing.
- **Cat 1 (escalate to detail only when warranted)**
  — held. Substrate-grounding round was deliberately
  silent (no operator-facing surface); decision-
  surfacing rounds were full pros/cons/recommendation
  shape.
- **Cat 1 (line-break rendering for review content)**
  — held; §1–§4 fenced blocks rendered with hard line
  wraps to fit chat width.
- **Cat 1 (default to luddite-analyst-gambler
  brevity)** — held throughout.
- **Cat 1 (plain-operator-language default for Code-
  report content surfacing)** — n/a this session (no
  Code report read this session).
- **Cat 2 (timestamp re-anchoring)** — open and close
  anchored. No pause-and-resume mid-session.
- **Cat 2 (pre-flight directory listing)** — done at
  open. Done at close via list_directory.
- **Cat 2 (Desktop Commander default)** — held
  throughout. All file ops via `Desktop Commander`
  family. **One `bash_tool` reflex this session at
  Step 1 of open ritual.** Recovered via `tool_search`;
  reinforces sweep candidate (a) — `bash_tool`
  standing-instruction softening — once more. Pattern
  continues to accumulate evidence.
- **Cat 2 (REPL discipline)** — n/a; no multi-line
  Python this session.
- **Cat 2 (`create_file` vs `write_file` namespace
  gotcha)** — n/a; brief written via
  `Desktop Commander:write_file` to canonical path
  with post-write verification.
- **Cat 2 (dry-run multi-target mechanical edits)** —
  n/a; brief is a fresh write, not a multi-target
  edit.
- **Cat 2 (persist drafted artefact content to
  scratch)** — n/a; the brief itself is the canonical
  artefact (not session-scratch deferred to a future
  session). Single-write completion this session.
- **Cat 2 (surface structural-drift in session
  record)** — n/a this session (no canonical-truth
  files edited).
- **Cat 3 (`bash_tool` non-functional)** — reinforced;
  one fresh attempt at Step 1 of open ritual,
  recovered.
- **Cat 3 (external API resources reach-for)** —
  used. `external_api_resources.md` referenced as
  pre-read; W3 contract sections drove brief's API-
  shape anchors.
- **Cat 3 (Code-bound brief output paths absolute,
  anchored at rebuild folder root)** — **held by
  brief authoring** (sweep candidate (m) discipline,
  authored Session 98). Brief specifies output path
  as
  `dr029/w4_bet_entry/real_adapter_report.md`
  (relative path from rebuild folder root, but the
  brief's pre-reads and anchors all use absolute
  references; the discipline added Session 98 to
  `bethub-brief-drafting` skill flowed through this
  drafting cleanly).
- **Cat 4 (DR-027/028 invoked)** — named at open.
  Load-bearing for §1 (why streaming-disconnect rule
  lives in `betfair_client`) and §5.1 (adapter as
  W4-side glue, not W3-internal).
- **Cat 4 (operational/analytical line discipline)**
  — held. Real adapter is operational-line by design
  (live API integration); analytical-line concerns
  out of scope per §9.
- **Cat 4 (single-cycle analysis discipline)** — n/a
  this session.
- **Cat 4 (Betfair as canonical source)** — load-
  bearing for §5.2 boundary translation (Betfair-raw
  upper-snake error codes are canonical at the API
  surface; W4 internal namespace is lower-snake post-
  Session 98 §5.3 canonicalisation).
- **Cat 4 (standing principle locked Session 97 — pay
  tooling-hygiene costs now)** — exercised once via
  §5.8 surgical rename folded into brief scope per
  Session 98 §7.1 routing call. Bidirectional reading
  ("fix knowable-bad state, preserve knowable-good
  state") preserved in §2 framing.
- **Cat 5 (software questions are Claude's)** — held
  throughout. Three software-shape decisions made
  in-brief without operator solicitation: streaming-
  client construction invariant (§5.1); `assert_type`
  Protocol conformance shape with named escape valve
  (§5.1); `_envelope_to_placement_outcome` helper
  function shape (§5.5). Operator calls limited to
  genuinely strategic / structural items (template
  choice, boundary-translation placement, scope
  bounds, test approach, contradiction safeguard).

## Session-99-specific reflections

- **End-to-end drafting after operator confirmation
  works cleanly at this scale.** Sections §1–§4 walked
  one round per section as a confidence-building shape;
  operator pivoted to "draft up the rest" by §5 once
  the structural shape was clear. Sweep candidate (c)
  reinforced strongly: at moderate brief length
  (1000–1500 lines), the section-by-section walk after
  the structural shape is locked is unnecessary
  overhead. The pivot trigger was operator-driven
  ("I don't think I need to read or review any of this
  unless you need a decision from me"). Pattern: hold
  the §1–§4 cadence as confidence-builder, pivot to
  end-to-end on operator signal, surface only on
  decisions-needed.

- **Live-codebase grounding caught three context-loss
  gaps that would have surfaced as Code findings
  otherwise.** The W3 `list_current_orders` gap (§5.6),
  the `place_bet` streaming-client invariant (§5.1),
  and the `assert_type` Protocol conformance shape
  (§5.1) all surfaced through grep + targeted file
  reads against the live v3 codebase rather than
  through inferring from substrate documents. Pattern:
  pre-flight grounding earns its keep on real-API
  adapter briefs because the documented surfaces and
  the live-code surfaces drift in ways the substrate
  documents don't always capture. The brief-drafting
  skill's Step 2 ("Pre-flight grounding when needed")
  is structurally validated here.

- **Brief-length-estimate calibration continues to
  miss low.** 1386 lines vs 800–1200 estimate (~16%
  over upper bound, ~73% over lower bound).
  Reinforces sweep candidate (h) — Cat 5 candidate.
  Cumulative evidence: housekeeping report 410 vs
  200–300; W4 follow-up report 447 vs 300–450 (within
  range, low end); now this brief 1386 vs 800–1200.
  Estimates look low-biased on briefs and reports
  alike. Pattern worth encoding at next sweep:
  estimate range is the floor, not the ceiling; report
  +20–30% upper envelope at hand-off.

- **Contradiction-and-context-loss safeguard is
  operator-driven discipline encoded into brief
  text.** Operator surfaced the explicit ask after the
  five-call hand-off; folded into §1 and §9 of the
  brief at the natural anchor points. Pattern: when
  briefs are drafted across multiple sessions of
  accumulated context, an explicit safeguard naming
  "this might be stale or inconsistent in places we
  can't see; flag rather than guess" is cheap
  insurance. Worth carrying as a default for future
  brief drafting where substrate is materially older
  than the current session.

## Open items in (carried forward)

New from Session 99:

- **Real `BetfairAdapter` implementation Code execution
  (between-session work).** Brief locked at
  `dr029/w4_bet_entry/real_adapter_brief.md`. Operator
  to run Claude Code against this brief between
  Sessions 99 and 100 with cleared memory. Code
  produces report at
  `dr029/w4_bet_entry/real_adapter_report.md`
  (400–600 line target). Session 100 reads the report
  and triages.
- **Three context-loss gaps the brief explicitly
  carries forward as findings-territory.**
  - (i) W3 `list_current_orders` surface gap — Code's
    §5.6 fallback either uses an existing surface
    (named in §6 deviations) or stubs with §8
    finding. If stub, then W3 contract-work brief is
    candidate next deliverable for Session 100+.
  - (ii) `place_bet` streaming-client invariant —
    locked in-brief as construction-time assertion;
    no further operator action.
  - (iii) `assert_type` Protocol conformance shape
    — Code's call with named escape valve; named in
    §6 deviations.

**Carry-forward from Session 98 (status):**

- **`INSUFFICIENT_FUNDS` canonicalisation** —
  **closed in brief §5.8.** Folded into Phase 2 real
  adapter brief scope per Session 98 §7.1 routing
  call. Brief carries explicit anchor (`orchestrator.py:1049`),
  test fixture rename (`test_orchestrator.py:581+589`),
  and pre-flight namespace preservation (lines 396–411
  + 554 stay upper-snake per housekeeping report §7.2).
- **Pre-flight namespace upper-snake convention
  review (low-priority)** — carry-forward unchanged
  parking-lot item. Brief §9 hard limits explicitly
  preserves the pre-flight namespace.
- **Sweep candidate (m) — Code-bound brief output
  paths absolute, anchored at rebuild folder root.**
  Cat 3 routing target. Held; brief's output path
  spec uses relative reference (`dr029/w4_bet_entry/real_adapter_report.md`)
  per W4-follow-up precedent — Code resolves at
  rebuild folder root via the absolute-paths
  discipline encoded in the `bethub-brief-drafting`
  skill (which loads with rebuild-folder-rooted
  context). The discipline holds; sweep candidate
  carries to fresh-mind sweep session for canonical-
  truth instruction encoding.

**Carry-forward from Session 97 (status):**

- **Real `BetfairAdapter` implementation brief
  drafting** — **closed this session**; brief is
  now between-session Code work.
- **Standing principle: pay tooling-hygiene and
  structural-consistency costs now (sweep candidate
  j).** Routing target Cat 4. Exercised once this
  session via §5.8 fold-in. Held.
- **Protocol-extension shape principle (sweep
  candidate k).** Cat 4 candidate. Exercised
  implicitly this session — adapter imports W3 types
  directly (`RunnerBestPrices`, `AccountFunds`,
  `BetPlacementResult`, etc.) rather than mirroring
  W4-side; precedent set Session 96 W4 follow-up.
  Held.
- **Multi-item-triage inventory-first cadence (sweep
  candidate l).** Cat 1 candidate. Not exercised
  this session (single-deliverable session, no
  multi-item triage). Held.
- **W7 brief drafting carry — `price_source`
  semantic on operator manual override.** Specific
  decision shape captured. Not exercised this session.
- **W7 brief drafting generic carry — modal copy
  distinguishing REST-also-failed from market-
  suspended.** Per-recovery-path copy decision. Not
  exercised this session.
- **Contract-cleanup-sweep candidate — explicit
  "REST-returns-fresh" contract assertion.** Held;
  brief §5.7 names the structural guarantee
  (`streaming_client=None` forces REST per contract
  §10 routing) but does not propose a contract
  amendment.
- **`bash_tool` standing-instruction softening
  reinforced (sweep candidate a).** Open-ritual Step
  1 attempted `bash_tool` again this session;
  recovered via `tool_search`. Pattern continues.

**Carry-forward from Session 96 (status):**

- **End-to-end-drafting cadence as Cat 1 explicit
  variant (sweep candidate c)** — reinforced strongly
  this session (sections §5–§12 drafted silently
  after operator's "draft up the rest" call). Held;
  ready for canonical encoding at sweep session.
- **Brief-length-estimate calibration as Cat 5
  candidate (h)** — reinforced again (1386 lines vs
  800–1200 estimate). Held; cumulative evidence
  strong.
- **"Review X" ambiguity-resolution pattern as Cat 1
  candidate (i)** — not exercised this session.
  Carry-forward.

**Carry-forward from Session 95 (status):**

- **Mid-session scratch writing as Cat 2 explicit
  pattern** — not exercised this session. Carry-
  forward.
- **Plain-operator-language default for Code-report
  content surfacing** — not exercised this session
  (no Code report read). Carry-forward.
- **`bash_tool` Cat 3 rule sharpening (a)** —
  reinforced this session.
- **Brief-drafting pre-flight skill check** —
  exercised this session via Step 2 of brief-drafting
  ritual (live-codebase grounding caught three context-
  loss gaps). Validates the skill's pre-flight
  discipline. Pattern: pre-flight grounding earns
  its keep on real-API integration briefs.
- **Structural drift between Cat 1 framing-and-
  internals match check** — not exercised this
  session. Carry-forward.

**Carry-forward from Session 94 (status):**

- **`bash_tool` standing-instruction softening
  candidate** — reinforced this session.
- **`str_replace` namespace gotcha substrate** — not
  exercised this session. Carry-forward.

**Carry-forward from earlier sessions (unchanged
unless noted):**

- **v3 composition-root structural decision** —
  sequenced Session 100+ (pushed back again; Session
  100 will read Code's report and triage real adapter
  delivery).
- **W3 `list_current_orders` surface addition** —
  **new candidate this session** if §5.6 surfaces
  the gap. Out of brief scope per §9; surfaces as
  finding pending Code's session-start grep.
- **W4 brief amendment sweep** — unchanged. Cosmetic
  carry.
- **Math review §6 arithmetic-step explicit update**
  — cosmetic.
- **W6 broader sync reconciliation** — §8.6 carry.
- **Brief / contract `placeOrders` vs `place_bet`
  naming alignment** — §8.4 carry. Cosmetic.
- **W4 brief locked at 2121 lines** — unchanged.
- **Storage-interface stub spec carry to W6 brief
  drafting** — unchanged.
- **§12.2 four-modules-vs-support-files
  clarification as `standing_instructions.md`
  candidate** — unchanged.
- **Round 13 workflow-ordering-validation pattern as
  Cat 4 candidate** — unchanged.
- **DR-032 locked** — unchanged.
- **`architecture.md` §A.10 written** — unchanged.
- **Cross-reference integrity gap** — unchanged.
- **Legacy `§D12` reference cleanup at next
  documentation sweep** — unchanged.
- **Cat 4 paragraph re: "pending architectural
  extension (Session 42)" stale** — unchanged.
- **Hedge-staking math review locked at 1942 lines**
  — unchanged.
- **Substrate revision flag for W4 brief drafting** —
  unchanged.
- **Effective-odds synthesis as racing-screen →
  modal flow** — unchanged.
- **Default free-bet conversion rate 65%; operator-
  configurable** — unchanged.
- **Manual stake override as future refinement** —
  unchanged.
- **Multi-rung ladder hedge as future arc** —
  unchanged.
- **`EX_LADDER` operator-side homework parked** —
  unchanged.
- **W4 substrate decisions captured Session 87** —
  unchanged.
- **F5 strategy_tag carry forward** — unchanged.
- **Streaming envelope vocabulary carry-forward** —
  unchanged.
- **Manual free-bet ledger entry workflow** —
  unchanged.
- **Deployment-substrate items (F2, F3, F4)** —
  unchanged.
- **F6 carry-forward to Fix 4 brief + W3+ briefs**
  — unchanged.
- **§12 self-assessment item 3 — audit-log durable
  substrate selection** — unchanged.
- **W1 F2 sharpening — capture.db Thoroughbred
  label includes harness undifferentiated** —
  unchanged.
- **W1 F1 accepted as v1.0 conflation** — unchanged.
- **W0 F2 brief-language carry** — unchanged.
- **DR-030 "18 months" reference correction** —
  unchanged.
- **`governance.md` §4 deferred-capability
  reconciliation** — unchanged.
- **Jump-anchor design reframe** — unchanged.
- **Post-DR-029-close contract documentation
  relocation** — unchanged.
- **Sports-side dead-heat capture in
  `architecture.md` §B.1.4** — unchanged.
- **Past-settlement-window threshold calibration** —
  unchanged.
- **Settlement worker periodic verification cadence**
  — unchanged.
- **Cluster 1 surgical-fix carry-in (analytical-
  layer prep)** — unchanged.
- **Fix 9 / Fix 10 / three-row collision triage /
  low-confidence match review** — unchanged.
- **Complete cascade map** — parked.
- **CLV as analytical-layer signal** — built post-
  DR-029.
- **Path-(iii) reconciliation-job scheduling and
  operator-facing flag-queue UI** — unchanged.
- **§2.9 §4.4 six edge cases** — unchanged.
- **Three-row collision per-row triage** — non-
  gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — unchanged.
- **Session numbering slip in probe brief** —
  cosmetic.
- **EX_LADDER entitlement question** — operator-
  side homework.
- **Drift-check methodology gap** — substrate from
  Session 64 carry-forward.
- **`bethub-analytical` project awaiting
  activation** — operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** —
  parked.
- **§2.1 BSP-fix code finding (c) — stale
  `client.py:189` docstring** — non-gating.
- **BetWatch contacted re: API service and book
  coverage** — awaiting response.
- **Betfair API membership tiers — investigate.**
  Operator-side homework.
- **PASSIVE bet-delay model handling** — flagged in
  §2.4 §15.4 as v3.1+ capability.
- **Betfair contact re: `EX_LADDER` entitlement and
  pricing** — operator-side parallel action.
- **Betfair contact re: `EX_TRADED_VOLUME`
  projection cost and entitlement** — operator-side
  parallel action.
- **Cluster C capture-routing decision** —
  deferred.
- **Racing API value assessment** — post-DR-029
  strategic decision.
- **v3 build-proper UI candidates** — three surfaces
  logged §5.2 of §2.10 brief.
- **Betfair SP-projection accuracy study** — post-
  DR-029 analytical capability candidate.
- **Racing EV model recalibration with §2.10
  bucket-1 captures** — post-DR-029 analytical work.
- **WIP §16** — VPS in-flight work. Unchanged.

## Open items out (closed this session)

- **Real `BetfairAdapter` implementation brief
  drafting** — **closed.** Brief locked at
  `dr029/w4_bet_entry/real_adapter_brief.md`
  (1386 lines, SHA `65d7c882…`). Now between-session
  Code work; Session 100 triages report.
- **`INSUFFICIENT_FUNDS` canonicalisation routing
  decision** (Session 98 §7.1 carry) — **closed in
  brief §5.8.** Surgical rename anchored at
  `orchestrator.py:1049` plus matching test fixture;
  pre-flight namespace explicitly preserved per
  housekeeping report §7.2.

Gaps from earlier reviews (logged for awareness):

- **Claude-67 G1** — AU-specific session expiry not
  on disk.
- **Claude-67 G2** — `listCurrencyRates` API surface
  silent in captured reference.
- **Claude-67 G3** — Racing API ↔ Betfair market
  identity reconciliation implicit. Now formally
  addressed in DR-032 §7.
- **Claude-67 G4** — `listCurrentOrders` filter
  parameter list not in captured reference.
  Addressed in W4 brief §6.3 by both-paths spec.
  **Reinforced this session via brief §5.6 context-
  loss gap** — the W3 surface for `listCurrentOrders`
  may not exist as public re-export. Code's session-
  start grep resolves.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC`
  betDelay confidence note. Partly addressed Session
  76.

## Session close state

- **Rebuild folder root:** unchanged this session in
  canonical-truth files. No edits to root-level
  governance docs.
- **`current_state.md`:** updated at close — "Last
  updated" → `2026-05-07 14:48 ACST`; "Where we are"
  → real adapter brief drafted and locked, three
  context-loss gaps caught and addressed in-brief,
  `INSUFFICIENT_FUNDS` canonicalisation folded into
  brief scope; "What's next" → Session 100 triages
  Code's report on real adapter implementation;
  required reads adjusted for Session 100.
- **`v3_build_picture.md`:** updated at close.
  No stream-status change (W4 stream remains dropped
  per Session 98's one-session done-carry rule;
  no new streams). "Last updated" bumped to this
  close timestamp; current-session activity line
  updated to reflect brief drafting + sequencing for
  Code execution.
- **`standing_instructions.md`:** unchanged this
  session in canonical-truth state. Sweep candidates
  remain at twelve (a, c, d, e, f, g, h, i, j, k, l,
  m). Two candidates exercised / reinforced this
  session: (a) `bash_tool` softening (one fresh
  attempt at Step 1 of open ritual); (c) end-to-end
  drafting after operator confirmation (sections
  §5–§12 drafted silently); (h) brief-length-estimate
  calibration (1386 vs 800–1200). Sweep deferred to
  fresh-mind dedicated session.
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session.
- **`decisions.md`:** unchanged this session.
- **`skills/bethub-brief-drafting/SKILL.md`:**
  unchanged this session. Skill's discipline (pre-
  flight grounding, output-paths-absolute, contract-
  pattern adherence) flowed through cleanly.
- **`skills/bethub-session-open/SKILL.md`:**
  unchanged this session.
- **`skills/bethub-session-close/SKILL.md`:**
  unchanged this session.
- **`dr029/w4_bet_entry/`:**
  - `real_adapter_brief.md` — **new this session**;
    1386 lines, SHA
    `65d7c8824d4ba851c689e9bd3e9889e16cfe609973427a26785307f5baeaadf0`.
  - All other artefacts unchanged.
- **`bethub-v3/`:** unchanged in canonical state at
  session close (no edits this session — codebase is
  post-Session-98 housekeeping state). Dirty regions
  pre-session (`clients/betfair_client/v1/__init__.py`
  + four W3 untracked files per housekeeping report
  §8.5) carry forward unchanged.
- **`sessions/`:** Session 99 record written by
  close ritual (this file).
- **`.close_out_backups/`:** Session 99 opening
  prompt removed at close; Session 100 opening prompt
  written.
- **Project knowledge base:** unchanged. No re-upload
  required this session.
- **VPS state:** unchanged this session. No VPS
  calls.
- **`/tmp/`:** no scratch scripts written this
  session.

## Forward routing

**Confirmed with operator at close:** Tim runs Claude
Code against the locked brief between Sessions 99 and
100 with cleared memory. Code produces the report at
`dr029/w4_bet_entry/real_adapter_report.md` per brief
§10. Session 100 opens fresh chat for triage; reads
Code's report; walks deviations, open questions, and
findings; routes follow-on work.

**Session 100 shape:**

Triage of Code's real adapter report. Multi-item triage
session per the inventory-first cadence (sweep
candidate l) — Code's report likely surfaces 5–10 items
(2–4 deviations, 2–3 open questions, 3–5 findings) plus
self-assessment. Session 100 inventory-first walks
items with operator-call / no-call flags, then walks
operator-call items one per round.

**Anticipated triage items:**

- §6 deviations — Code's calls on (a) `assert_type`
  Protocol conformance shape; (b) `_envelope_to_placement_outcome`
  helper shape; (c) mock approach for `BetfairRestClient`
  in tests; possibly (d) `_now_adelaide` helper
  source choice.
- §7 open questions — likely 2–3 W7-adjacent or
  contract-shape questions for operator triage.
- §8 findings — primary candidate is the W3
  `list_current_orders` surface gap (if §5.6 fallback
  fired); secondary candidates are any drift between
  brief anchors and live codebase, any Decimal-
  precision edge cases, any test-coverage gaps.
- §9 self-assessment — confidence regions, length
  overrun if any, what operator should look at first.

**Out of scope for Session 100:**

- W3 contract-work brief drafting (if §5.6 surfaces
  the gap, that becomes a candidate next deliverable
  for Session 101+ — but Session 100 closes the real-
  adapter triage cleanly first).
- v3 composition-root structural decision drafting
  (sequenced Session 101+).
- Any work outside real adapter report triage.

**Operator's between-session actions:**

- Run Claude Code against the locked brief at
  `dr029/w4_bet_entry/real_adapter_brief.md`. Cleared
  Code memory per operator's close-time call. Brief
  is self-contained — no operator intervention
  needed during Code's run.

**Sequence after Session 100:**

- W3 `list_current_orders` surface addition brief
  (conditional on §5.6 outcome) — sequenced Session
  101+.
- v3 composition-root structural decision drafting
  — sequenced Session 101+.
- W6 brief drafting (operational store schema) —
  sequenced Session 101+.
- W7 brief drafting (burst review workflow) —
  sequenced Session 101+.
- Standing-instructions sweep — twelve candidates;
  dedicated fresh-mind session whenever operator
  wants.

## Close-out notes

Session 99 was a clean single-deliverable session that
closed end-to-end without split-trigger pressure. Wall-
clock 22 minutes — well under any threshold.

Three patterns worth holding onto:

- **End-to-end drafting after operator confirmation
  scales cleanly to ~1400-line briefs.** Section-by-
  section walk for §1–§4 was sufficient to lock
  structural shape and discipline; §5–§12 drafting
  silently with decisions surfaced post-write was the
  right cadence. Reinforces sweep candidate (c) for
  Cat 1 encoding.

- **Live-codebase grounding catches context-loss
  gaps that substrate documents miss.** The three
  gaps caught this session (W3 `list_current_orders`,
  `place_bet` streaming-client invariant,
  `assert_type` Protocol conformance) all surfaced
  via grep + targeted file reads against live code.
  Pattern reinforces brief-drafting Step 2 (pre-
  flight grounding) for real-API adapter briefs.

- **Contradiction-and-context-loss safeguard is
  cheap insurance for cross-session-substrate
  briefs.** Operator's added safeguard request
  folded into brief §1 + §9 with no friction; gives
  Code an explicit channel for surfacing drift
  rather than guessing. Pattern: when briefs span
  multiple sessions of accumulated context, the
  safeguard is a default worth carrying.

Real adapter brief locked. Three context-loss gaps
addressed in-brief. `INSUFFICIENT_FUNDS`
canonicalisation folded into brief scope per Session
98 §7.1 routing call. Session 100 sequenced for Code-
report triage after between-session Code execution.
