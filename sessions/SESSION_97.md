# Session 97

**Title:** W4 follow-up Code report triaged end-to-end —
eleven items walked (five operator calls + six awareness/
routing-only items); standing principle locked
("pay tooling-hygiene and structural-consistency costs now,
while the project is in build, rather than carry them into
live operations"); housekeeping brief drafted at 450 lines
covering three findings (§8.1 testpaths reorganisation,
§8.2 SQLite stub `price_source` round-trip, §8.3 recovery-
key set canonicalisation); W4 follow-up arc closed; W4
stream moves to `done` in v3 build picture; Session 98
sequenced for real `BetfairAdapter` implementation brief
drafting against post-housekeeping-clean codebase.
**Opened:** 2026-05-07 10:11 ACST
**Closed:** 2026-05-07 10:30 ACST
**Wall-clock:** ~19 minutes active session work. Same-
workday open relative to Session 96 close (~24 min gap;
well under the 4am same-workday cutoff). No day-rollover,
no pause-and-resume.
**Tool routing:** Claude Chat exclusively (triage, operator
calls, housekeeping brief drafting). No Claude Code work
this Chat session — Code committed via the housekeeping
brief produced at close for fresh out-of-session execution
between Session 97 and Session 98.
**Governing DRs invoked:** DR-021 (Adelaide local time),
DR-027 (two-database architecture — context for §13
contract paragraph rationale), DR-028 (cross-DB
integration boundary discipline — same), DR-030 (v3 repo
layout — frames §8.1 testpaths reorganisation as
consistent-shape work), DR-031 (v3 tech stack — pytest /
ruff / import-linter discipline encoded in housekeeping
brief), DR-032 (canonical reference layer for all bet
records — drove §5.2 `price_source` placement reinforced
in §6.4 ratification), DR-019 (derived state on read —
informed §5.4 NULL handling ratification).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
`2026-05-07 10:11 ACST`.
Close: same command → `2026-05-07 10:30 ACST`.

Same-workday open relative to Session 96 close at 09:47
ACST (24-min gap, single-sitting continuation). No
pause-and-resume.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, with one
operator-surfaced clarification at Step 2:

- **Session-number slip caught at open.** Operator's first
  message said "Open session 98" but `current_state.md`,
  `.close_out_backups/`, and `sessions/` all named Session
  97 as the next-up session (gated on Code shipping the
  W4 follow-up report). Operator-Claude paused the ritual
  at Step 2 mid-reads, surfaced the discrepancy with
  diagnostic detail (latest session record on disk =
  SESSION_96.md; staged opening prompt =
  SESSION_97_opening_prompt.md; gate-condition Code report
  now on disk so the gate is cleared). Operator confirmed
  Session 97. Ritual resumed cleanly.
- Rebuild root: 11 expected `.md` files present plus
  `openapi.json`, `external_api_resources.md`, `.DS_Store`,
  and `v3_build_picture.md` (12th expected per skill).
  All directories present (`agent_review`, `diagrams`,
  `dr029`, `orchestration_pack`, `sessions`, `skills`,
  `.close_out_backups`).
- `.close_out_backups/` contained `SESSION_97_opening_prompt.md`
  only (Session 96 close artefact, expected, dated
  2026-05-07 09:55).
- Drift-check passed: `current_state.md` last-updated
  `2026-05-07 09:47 ACST` matched Session 96 close;
  `sessions/SESSION_96.md` present at 800 lines;
  `v3_build_picture.md` last-updated matched Session 94
  close (no movement at Session 95 or 96 close — both
  brief-drafting-shaped, no stream movement).
- Same-workday recap delivered at 24-min gap.
- V3 build picture: skip-silent at open (no stream
  movement in 24-min gap; W4 stream still
  `blocked-on-W4-follow-up` at open).
- Open-items delta at open: one item closed (W4 follow-up
  Code execution gate — Code shipped, report on disk).
  Surfaced as one-line note.
- Governing DRs named at open: DR-027, DR-028, DR-030,
  DR-031, DR-032, DR-019, DR-021. DR-029 named as closed.

## Session shape

Session 97 was a focused triage session running end-to-end
on Code's W4 follow-up report (447 lines, structure per
brief §10). Three distinct phases:

**Phase 1 — full-surface inventory.** Operator requested
all eleven items presented in short form first with the
operator call (or no-call) called out per item, before
digging into any one item. This shape — "lay out the whole
surface, then walk in priority order" — was operator-
driven and worked cleanly: eleven items took one inventory
message; six were marked no-operator-call (awareness or
routed elsewhere); five were marked as needing operator
calls. Inventory framing made the session-budget
arithmetic visible to the operator before commitment to
the walking cadence.

**Phase 2 — operator-call walking, four rounds.** Plain-
language + pros/cons/risks + recommendation framing per
operator request. Items walked one per round:

- §6.1 — naming canonicalisation. Code chose Option A
  (W3-aligned `betfair_streaming_disconnected`).
  Recommendation: ratify Code's choice (line-ball-leaning-
  A on grounds that Option A makes the next adapter brief
  cheaper to draft; Option B's case is cosmetic, Option
  A's is structural). Operator: ratified Option A.
- §6.2 — modal recovery comment wording. Recommendation:
  ratify as-is (line-ball-leaning-ratify; comment runs
  four lines vs brief's "one-line" target but earns the
  extra lines by naming four reference points). Operator:
  ratified as-is.
- §6.3 — contract status header rolled v1.1 → v1.3 with
  v1.2 also rolled in. After §6.2, operator delegated
  remaining low-risk/non-material items to operator-
  Claude recommendation. Recommendation: ratify (real
  bug-fix; alternative would have left header more wrong
  than before).
- §6.4 — `OPERATOR_TYPED` populated at orchestrator
  boundary. Recommendation: ratify (Code-territory call;
  one-site placement at `_soft_book_inputs_from`).
- §6.5 — `_place_with_retry` tuple-return shape change.
  Recommendation: ratify (right answer; rejected
  alternatives for sound reasons).
- §7.1 — implicit "REST returns means fresh" contract.
  Recommendation: park (REST guarantees freshness per W3
  contract §4; explicit assertion is contract-housekeeping
  nicety).

**Phase 3 — standing principle locked + remaining-items
recommendations.** Operator surfaced standing principle at
§8.1 walk: "I would rather spend extra time now closing
potential gaps in the future (once operations are live)
and having to locate key context to make fixes. This
should be a standing principle." Operator-Claude landed
the principle as **"Pay tooling-hygiene and structural-
consistency costs now, while the project is in build,
rather than carry them into live operations."** Routing
target: Cat 4 (governance discipline) of
`standing_instructions.md`. Sweep candidate (j) carried
forward.

The principle changed the routing default for §8.x
findings — without it, "carry as-is" was the cheapest
this-session option; with it, the evaluation shifts to
whole-of-project cost.

Remaining items walked under operator-delegated-
recommendation discipline:

- §8.1 — testpaths reorganisation. Recommendation: Option
  1 (move W4 tests under `tests/workflows/bet_entry/v1/`).
  Operator: confirmed Option 1.
- §8.2 — SQLite stub round-trip `price_source`.
  Recommendation: Option 1 (add column now, fold into same
  Code brief as §8.1). Operator: confirmed.
- §8.3 — recovery-key set canonicalisation on lower-snake.
  Recommendation: fold into same Code brief (third item).
  Operator: pre-delegated; confirmed by absence of
  pushback.
- §8.4 — first W4 → W3 import. Recommendation: flag-and-
  park (permitted under DR-030; precedent-setting only).
  Carry-forward as standing-instructions sweep candidate
  (k) — Protocol-extension shape principle.
- §7.2 — operator manual price override case.
  Recommendation: named carry-forward to W7 brief
  drafting (specific decision named: either flip
  `price_source` to `OPERATOR_TYPED` on override path or
  introduce fourth `PriceSource` value
  `OPERATOR_OVERRIDE`).
- §7.3 — modal copy after REST-fetch failure.
  Recommendation: generic W7 brief carry, no special
  weight.

**Phase 4 — sequencing call (between-Session-97-and-98).**
Operator headed out for a bit; confirmed that Claude Code
should execute the housekeeping brief between sessions
(sequence 1: clean codebase before Session 98 drafts the
real adapter brief). Operator-Claude proceeded with close-
out drafting the housekeeping brief and the Session 98
opening prompt with a pre-flight check that housekeeping
has shipped clean.

## What was delivered

Session 97 produced two canonical artefacts (one routing
decision lock, one Code-bound brief) plus one standing-
principle lock:

**Standing principle locked — "Pay tooling-hygiene and
structural-consistency costs now, while the project is in
build, rather than carry them into live operations."**
Routing target: Cat 4 (governance discipline) of
`standing_instructions.md`. Carried as sweep candidate
(j) for the deferred fresh-mind sweep session. Principle
changes routing default for findings of "knowable-bad
state in tooling/structure" — fix-now becomes the default,
carry-forward becomes the exception requiring justifying
case. Driver: operator's explicit framing during §8.1
walk on the cost of locating context once operations are
live.

**Triage decisions locked across eleven W4 follow-up
report items:**

- §6.1 — Code's Option A (W3-aligned canonicalisation)
  ratified. Locks
  `betfair_streaming_disconnected` as the canonical
  string across W3 reason value, W4 outcome literal, and
  recovery-key set wherever it now appears.
- §6.2 — modal recovery comment wording ratified as-is.
- §6.3 — contract status header rollup v1.1 → v1.3 with
  v1.2 folded ratified.
- §6.4 — `OPERATOR_TYPED` orchestrator-boundary
  population ratified.
- §6.5 — `_place_with_retry` tuple-return shape change
  ratified.
- §7.1 — implicit REST-returns-fresh contract parked
  (contract-cleanup-sweep candidate).
- §7.2 — operator manual price override case routed as
  named carry-forward to W7 brief drafting with explicit
  decision shape captured.
- §7.3 — modal copy generic W7 brief carry.
- §8.1 / §8.2 / §8.3 — folded into combined housekeeping
  brief (see below).
- §8.4 — flagged as standing-instructions sweep
  candidate (k) — Protocol-extension shape principle.

**Housekeeping Code brief drafted —**
`dr029/w4_bet_entry/housekeeping_brief.md` (450 lines).
Surgical-fix shape covering three coordinated changes:

- §5.1 — move W4 module-local tests from
  `workflows/bet_entry/v1/tests/` to
  `tests/workflows/bet_entry/v1/`. Resolves §8.1
  testpaths exclusion permanently.
- §5.2 — extend `workflows/bet_entry/v1/storage.py` SQLite
  stub to round-trip `price_source` (DDL + INSERT +
  SELECT + round-trip test). Resolves §8.2 silent-data-
  loss gap.
- §5.3 — canonicalise recovery-key set on lower-snake
  (`MARKET_SUSPENDED` → `market_suspended`). Resolves
  §8.3 mixed-conventions cosmetic gap.

Brief carries hard limits (no test-body edits beyond
import-path repairs and the new round-trip assertion; no
SQL schema changes beyond the named column; no W3 edits;
no git operations; no mid-session escalation), sequencing
(§5.1 first because it moves test files that §5.2 / §5.3
exercise), pre-and-post baseline verification, output
spec at `dr029/w4_bet_entry/housekeeping_report.md`
(200–300 line target, structure named), and what-happens-
after (Session 98 triage when report ships, then real
adapter brief drafting against the cleaned codebase).

**No edits to canonical-truth files in this session.** No
edits to `decisions.md`, `architecture.md`, `governance.md`,
`standing_instructions.md` (sweep candidates accumulated
but the sweep itself is deferred), `vision.md`,
`v3_data_requirements.md`, `project_context.md`. Brief is
session-substrate per `bethub-brief-drafting` skill —
becomes locked artefact at hand-off but doesn't modify
canonical truth.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-030,
  DR-031, DR-032, DR-019, DR-021 named at open. DR-029
  named as closed gating arc.
- **Cat 1 (calendar-calibrated recap)** — same-workday
  tight recap delivered at 24-min gap.
- **Cat 1 (V3 build picture conditional render)** —
  skip-silent at open (no stream movement in 24-min gap).
  Updated at this close (W4 stream moves
  `blocked-on-W4-follow-up` → `done`).
- **Cat 1 (open-items delta)** — surfaced one-line at
  open: ✅ W4 follow-up Code execution gate closed.
- **Cat 1 (drift-check)** — done at open, all three checks
  matched.
- **Cat 1 (silent session-open ritual)** — held except for
  one mandatory operator-facing surface: session-number
  slip discrepancy (operator said "Session 98",
  filesystem said Session 97 was next-up). Handled per
  skill negative-scope rule: surface anomaly immediately
  rather than guess; operator confirmed; ritual resumed.
- **Cat 1 (silent session-close ritual)** — holding this
  close. Steps 1-10 silent except for the operator-
  facing forward-routing question at Step 2 (sequence-1-
  vs-sequence-2 housekeeping-between-sessions choice);
  Step 11 produces brief verification line.
- **Cat 1 (call-driven surfacing during section-by-section)**
  — held with operator-driven cadence variant. Operator
  asked for full inventory first then walking by priority;
  inventory message marked which items needed calls vs
  awareness. Walking cadence honoured plain-language +
  pros/cons + recommendation discipline per operator
  request.
- **Cat 1 (short responses, plain language)** — held
  throughout. Inventory message ran longer than typical
  (eleven items) but each item kept to short-form
  framing; subsequent walking-rounds held to the
  standard cadence.
- **Cat 1 (decision-maker framing)** — held. Each operator-
  call item led with the call, the choice, or the
  recommendation; reasoning followed.
- **Cat 1 (don't drift to alternatives when operator
  clear)** — held. Operator's "happy for you to make
  remaining recommendations based on standing principle"
  acted on without second-guessing; six items walked
  end-to-end with operator-Claude recommendations
  applied.
- **Cat 1 (escalate to detail only when warranted)** —
  held. Inventory items pre-classified as "no operator
  call" got short flag-only entries; operator-call items
  got plain-language + pros/cons/risks + recommendation
  detail per request.
- **Cat 1 (line-break rendering for review content)** —
  held. Code commission prompt for housekeeping brief
  rendered hard-wrapped during close-out (see Step 8 of
  close ritual).
- **Cat 1 (default to luddite-analyst-gambler brevity)**
  — held throughout.
- **Cat 1 (plain-operator-language default for Code-report
  content surfacing)** — held throughout the eleven-item
  walk. No schema field name appeared without operational
  framing alongside; no DR cited without bracketed
  reminder when invoked mid-discussion.
- **Cat 2 (timestamp re-anchoring)** — open and close
  anchored. No pause-and-resume mid-session.
- **Cat 2 (pre-flight directory listing)** — done at open
  (with phantom-file scan including `openapi.json` flag).
  Done at close via list_directory and post-close
  verification.
- **Cat 2 (Desktop Commander default)** — held throughout.
  All file ops via `Desktop Commander:read_file`,
  `Desktop Commander:list_directory`,
  `Desktop Commander:start_process`,
  `Desktop Commander:write_file`. One `bash_tool` attempt
  on the open-ritual timestamp call (failed correctly per
  Cat 3); recovered by tool_search then standard
  Desktop Commander invocation.
- **Cat 2 (REPL discipline)** — n/a; no multi-line Python
  this session.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)**
  — held. Housekeeping brief written via
  `Desktop Commander:write_file` to canonical Mac path;
  verified post-write via `Desktop Commander:start_process`
  `wc -l` (450 lines on disk matching tool output).
- **Cat 2 (dry-run multi-target mechanical edits)** —
  n/a; brief was a single fresh-write, not a multi-target
  edit.
- **Cat 2 (persist drafted artefact content to scratch)**
  — n/a; this session's draft *is* the canonical artefact
  (locked housekeeping brief), not session-scratch
  deferred to a future session.
- **Cat 2 (surface structural-drift in session record)**
  — no governance artefact structure changed this
  session. Brief is a fresh artefact; doesn't modify any
  existing governance file's structure.
- **Cat 3 (`bash_tool` non-functional)** — held by
  correction. Open-ritual Step 1 attempted `bash_tool`,
  failed, recovered via tool_search → Desktop Commander.
  This is the standing-instruction-softening candidate
  (a) reinforced again — `bash_tool` continues to be
  reflexively reached for at the standard Adelaide-
  timestamp invocation despite the standing instruction.
  Sweep candidate (a) holds.
- **Cat 3 (external API resources reach-for)** — n/a this
  session.
- **Cat 4 (DR-027/028 invoked)** — named at open.
  Referenced in §6.1 walk (canonicalisation downstream of
  the W3/W4 boundary discipline).
- **Cat 4 (operational/analytical line discipline)** —
  held. Triage maintained operational-line framing for
  all W4 work (live-pricing path, modal recovery, REST
  fallback); no analytical-line cross-contamination.
- **Cat 4 (single-cycle analysis discipline)** — n/a
  this session.
- **Cat 4 (Betfair as canonical source)** — load-bearing
  for §6.4 ratification (`OPERATOR_TYPED` at soft-book
  boundary because Betfair is canonical for non-soft-book
  bets).
- **Cat 4 (standing principle locked this session — pay
  tooling-hygiene costs now)** — sweep candidate (j) for
  the deferred sweep.
- **Cat 5 (software questions are Claude's)** — held
  throughout. All Code-territory items (§6.4 placement,
  §6.5 tuple-return, §8.4 import precedent) were
  ratified or flagged-only — no operator-side
  decisioning solicited on technical-only matters.
  Operator calls were limited to genuinely strategic
  / routing items.

## Session-97-specific reflections

- **Operator-driven inventory-first cadence works for
  multi-item triage.** Eleven items in one short-form
  inventory before walking allowed the operator to see
  the session-budget shape upfront and confirm the
  walking order. Without the inventory step, walking
  blind through eleven items would have surfaced
  "wait, how much more is there?" mid-flight. Pattern:
  for triage sessions with high item count (~6+),
  inventory-first-then-walk is operator-budget-cheaper
  than walk-blind. Carry-forward as Cat 1 candidate
  (l) — multi-item-triage inventory-first cadence.

- **Operator delegation after first two operator calls
  triggered cleanly.** Operator's "happy for you to make
  remaining recommendations based on standing principle"
  at item 4 of 11 was a structural delegation: the
  standing principle just locked (item 3 of 11) gave
  operator-Claude enough framework to walk remaining
  items without bouncing each one back. Pattern: when
  the operator surfaces a routing-decision-substrate
  mid-session, subsequent items in the same session
  inherit it. Standing principle becomes
  decision-multiplier rather than one-off lock.

- **Standing principle landing mid-triage is a
  governance event worth preserving.** The principle
  emerged organically from the §8.1 walk — operator's
  framing of "extra time now closing potential gaps
  before live ops" became a generalisable principle
  applicable beyond §8.1. Operator-Claude named it,
  scoped it (Cat 4 routing target), distinguished it
  from existing instructions (orthogonal to Cat 4 / 5),
  added it to sweep candidates (j), and reapplied it
  to remaining items in same session. Pattern worth
  preserving: when an operator framing crystallises into
  a principle, name-and-lock-and-apply mid-session
  rather than carrying as fuzzy "operator preference."

- **Housekeeping-brief-drafting after triage is mode-
  coherent.** Triage closed; housekeeping brief drafted
  during close-out as direct continuation. End-to-end
  drafting cadence held cleanly (per Cat 1 candidate
  (c) end-to-end-drafting-after-§1-confirmation).
  Brief landed at 450 lines (above 200–300 estimate but
  small register; brief-length-estimate calibration as
  Cat 5 candidate (h) reinforced again). Pattern: when
  triage routes findings to a follow-up brief, drafting
  the brief during close-out keeps everything in the
  same context and produces tighter cross-references
  than deferring to a fresh session.

- **Session-number slip caught at open is a real
  detection win.** Operator said "Open session 98";
  filesystem named Session 97. Open-ritual paused at
  Step 2 with diagnostic detail; operator confirmed.
  This is exactly the failure mode Cat 1 silent-ritual
  + drift-check exception are designed to catch. Worth
  reinforcing: silent-ritual exception is "surface
  immediately when something is wrong," and this kind
  of mismatch is the canonical thing.

## Open items in (carried forward)

New from Session 97:

- **Housekeeping Code brief execution (Session 97+
  out-of-session).** Brief locked at 450 lines; Code
  commission prompt rendered at close. Operator's
  between-session action: paste prompt into fresh Code
  session; let Code execute end-to-end; report lands at
  `dr029/w4_bet_entry/housekeeping_report.md`.
- **Housekeeping Code report triage (Session 98 first
  task).** Read Code's report end-to-end; walk
  deviations / open questions / findings; close
  housekeeping arc. Likely shorter triage shape than W4
  follow-up (smaller brief, smaller report expected).
- **Real `BetfairAdapter` implementation brief drafting
  (Session 98 primary deliverable post-housekeeping
  triage).** Inherits clean codebase post-housekeeping;
  draws Protocol-extension and `price_source` field
  shapes from W4 follow-up; W3/W4 import precedent
  established §8.4. Drafting against locked W4 follow-up
  build + housekeeping fixes.
- **Standing principle: pay tooling-hygiene and
  structural-consistency costs now (sweep candidate j).**
  Routing target Cat 4 of `standing_instructions.md`.
  Locked Session 97; sweep deferred to dedicated
  session.
- **Protocol-extension shape principle (sweep candidate
  k).** When a future Protocol extension on the W4
  adapter boundary needs to surface a W3-side type,
  prefer importing the W3 type directly over inventing
  a W4-side mirror. Carry-forward Cat 4 candidate.
- **Multi-item-triage inventory-first cadence (sweep
  candidate l).** When triage covers 6+ items, present
  short-form inventory with operator-call / no-call
  flags before walking. Cat 1 candidate.
- **W7 brief drafting carry-forward — `price_source`
  semantic when operator manually overrides at modal-
  confirm.** Specific decision shape captured: either
  (a) flip to `OPERATOR_TYPED` on override path or (b)
  introduce fourth `PriceSource` value
  `OPERATOR_OVERRIDE`. Operator-Claude call at W7 brief
  drafting.
- **W7 brief drafting generic carry — modal copy
  distinguishing REST-also-failed from market-
  suspended.** Per-recovery-path copy decision; expected
  per-path call set in W7 anyway.
- **Contract-cleanup-sweep candidate — explicit
  "REST-returns-fresh" contract assertion.** Make
  implicit assumption explicit if/when contract-
  housekeeping sweep happens. No standalone work.
- **`bash_tool` standing-instruction softening
  reinforced (sweep candidate a).** Open-ritual Step 1
  attempted `bash_tool` again this session; recovered
  via tool_search. Pattern continues. Sweep target
  could be either explicit guidance ("call
  Desktop Commander directly without tool_search for
  the Adelaide timestamp") or auto-discovery hint.

**Carry-forward from Session 96 (status):**

- **End-to-end-drafting cadence as Cat 1 explicit
  variant (sweep candidate c)** — reinforced this
  session in housekeeping-brief drafting. Held.
- **Brief-length-estimate calibration as Cat 5
  candidate (h)** — reinforced again (450 lines vs
  200–300 estimate, ~50% over). Pattern: surgical-fix
  briefs tend to land 30–50% over their content-only
  estimate due to per-section anchor density. Held.
- **"Review X" ambiguity-resolution pattern as Cat 1
  candidate (i)** — not exercised this session;
  operator's first message was unambiguous (despite
  session-number slip). Carry-forward.

**Carry-forward from Session 95 (status):**

- **Mid-session scratch writing as Cat 2 explicit
  pattern** — not exercised this session. Carry-forward.
- **Plain-operator-language default for Code-report
  content surfacing** — exercised cleanly throughout
  this session's eleven-item walk. Pattern held without
  drift. Carry-forward to next sweep for explicit
  encoding.
- **`bash_tool` Cat 3 rule sharpening (a)** —
  reinforced again this session. Carry-forward.
- **Brief-drafting pre-flight skill check** — not
  exercised this session (no fresh Code investigation
  needed). Carry-forward.
- **Structural drift between Cat 1 framing-and-
  internals match check** — not exercised this session.
  Carry-forward.
- **`str_replace` namespace gotcha substrate** — not
  exercised this session. Carry-forward.

**Carry-forward from earlier sessions (unchanged unless
noted):**

- **v3 composition-root structural decision** —
  sequenced Session 99+ (pushed back again; Session 98
  consumed by housekeeping triage + real adapter brief
  drafting). Genuinely next-after-real-adapter
  candidate.
- **Real `BetfairAdapter` implementation brief** —
  **Session 98 primary deliverable post-housekeeping
  triage.** Substantively unblocked: Protocol extension
  + `price_source` field both landed in W4 follow-up
  build; W3/W4 import precedent established Session 96
  build / Session 97 triage; housekeeping arc closes
  the operational loose ends.
- **W4 brief amendment sweep** — unchanged. Cosmetic
  carry.
- **Math review §6 arithmetic-step explicit update** —
  cosmetic.
- **W6 broader sync reconciliation** — §8.6 carry.
  Routes to W6 brief drafting.
- **Brief / contract `placeOrders` vs `place_bet`
  naming alignment** — §8.4 carry. Cosmetic.
- **W4 brief locked at 2121 lines** — unchanged.
- **Storage-interface stub spec carry to W6 brief
  drafting** — unchanged.
- **§12.2 four-modules-vs-support-files clarification
  as `standing_instructions.md` candidate** —
  unchanged.
- **Round 13 workflow-ordering-validation pattern as
  Cat 4 candidate** — unchanged.
- **DR-032 locked** — drove `price_source` placement
  and reinforced this session via §6.4 ratification.
- **`architecture.md` §A.10 written** — unchanged.
- **Cross-reference integrity gap** — unchanged. Cat 2
  candidate.
- **Legacy `§D12` reference cleanup at next
  documentation sweep** — unchanged.
- **Cat 4 paragraph re: "pending architectural
  extension (Session 42)" stale** — unchanged. Flag
  for next sweep.
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
- **CLV as analytical-layer signal** — built post-
  DR-029.
- **Path-(iii) reconciliation-job scheduling and
  operator-facing flag-queue UI** — unchanged.
- **§2.9 §4.4 six edge cases** — unchanged.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — unchanged.
- **Session numbering slip in probe brief** —
  cosmetic.
- **EX_LADDER entitlement question** — operator-side
  homework.
- **Drift-check methodology gap** — substrate from
  Session 64 carry-forward.
- **`bethub-analytical` project awaiting activation**
  — operator decision pending.
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
- **Betfair contact re: `EX_TRADED_VOLUME` projection
  cost and entitlement** — operator-side parallel
  action.
- **Cluster C capture-routing decision** — deferred.
- **Racing API value assessment** — post-DR-029
  strategic decision.
- **v3 build-proper UI candidates** — three surfaces
  logged §5.2 of §2.10 brief.
- **Betfair SP-projection accuracy study** — post-
  DR-029 analytical capability candidate.
- **Racing EV model recalibration with §2.10 bucket-1
  captures** — post-DR-029 analytical work.
- **WIP §16** — VPS in-flight work. Unchanged.

Closed this session:

- **W4 follow-up Code report triage** (Session 96
  primary-deliverable carry) — **closed.** All eleven
  items walked end-to-end; five operator calls
  resolved; six awareness/routing-only items addressed.
  W4 follow-up arc complete.
- **W4 follow-up Code execution gate** — closed at
  open (Code shipped report between sessions).

Gaps from earlier reviews (logged for awareness):

- **Claude-67 G1** — AU-specific session expiry not on
  disk.
- **Claude-67 G2** — `listCurrencyRates` API surface
  silent in captured reference.
- **Claude-67 G3** — Racing API ↔ Betfair market
  identity reconciliation implicit. Now formally
  addressed in DR-032 §7.
- **Claude-67 G4** — `listCurrentOrders` filter
  parameter list not in captured reference. Addressed
  in W4 brief §6.3 by both-paths spec.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC`
  betDelay confidence note. Partly addressed Session
  76.

## Open items out (closed this session)

- **W4 follow-up Code report triage** (Session 96
  primary-deliverable carry) — **closed.** All eleven
  items resolved; W4 follow-up arc complete; no
  remaining triage debt.
- **W4 follow-up Code execution gate** — closed at
  open ritual.

## Session close state

- **Rebuild folder root:** unchanged this session. No
  edits to root-level governance files.
- **`current_state.md`:** updated at close — "Last
  updated" → `2026-05-07 10:30 ACST`; "Where we are"
  → W4 follow-up arc closed, housekeeping brief
  locked, real adapter brief sequenced for Session
  98; "What's next" → Session 98 housekeeping triage
  + real adapter brief drafting; required reads
  adjusted for Session 98.
- **`v3_build_picture.md`:** updated at close. **W4
  stream moves `blocked-on-W4-follow-up` → `done`.**
  W4 follow-up arc closed; the next session inherits
  W4 as `done` (carries one session post-close per
  Cat 1 done-stream-rotation discipline; drops at
  Session 98 close if not re-touched). "Last updated"
  bumped to this close timestamp.
- **`standing_instructions.md`:** unchanged this
  session in canonical-truth state. Sweep candidates
  accumulated to ten now (a, c, d, e, f, g, h, i, j,
  k, l):
  - (a) `bash_tool` softening — reinforced again.
  - (c) End-to-end-drafting-after-§1-confirmation —
    reinforced.
  - (d) Mid-session scratch writing as Cat 2 explicit.
  - (e) Plain-operator-language default for Code-
    report content surfacing — reinforced cleanly.
  - (f) Brief-drafting pre-flight skill check —
    parallel Code investigation as named option.
  - (g) Structural-drift framing-vs-internals match
    check.
  - (h) Brief-length-estimate calibration as Cat 5
    candidate — reinforced again.
  - (i) "Review X" ambiguity-resolution as Cat 1
    candidate.
  - (j) **Pay tooling-hygiene and structural-
    consistency costs now (Cat 4 routing target)** —
    new this session.
  - (k) **Protocol-extension shape principle (Cat 4
    candidate)** — new this session.
  - (l) **Multi-item-triage inventory-first cadence
    (Cat 1 candidate)** — new this session.

  Sweep deferred to fresh-mind dedicated session;
  ten-or-eleven candidates is enough mass for a real
  sweep session. Sequenced for after housekeeping
  arc + real adapter brief land cleanly.
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session.
- **`decisions.md`:** unchanged this session.
- **`dr029/w4_bet_entry/`:**
  - `hedge_staking_math.md` — unchanged.
  - `w4_bet_entry_brief.md` — unchanged.
  - `w4_bet_entry_report.md` — unchanged.
  - `_drafts/SESSION_91_substrate.md` — unchanged.
  - `_drafts/SESSION_95_drafts.md` — unchanged.
  - `_drafts/SESSION_95_code_preflight.md` —
    unchanged.
  - `v1_2_contract_addition_brief.md` — unchanged.
  - `v1_2_contract_addition_report.md` — unchanged.
  - `w4_followup_brief.md` — unchanged. Read this
    session for triage cross-reference.
  - `w4_followup_report.md` — unchanged. **Read end-
    to-end this session for triage.**
  - **`housekeeping_brief.md`** — **new this
    session**, written at 450 lines via
    `Desktop Commander:write_file`. Locked Code-bound
    brief; Session 97 secondary deliverable.
- **`sessions/`:** Session 97 record written by close
  ritual (this file).
- **`.close_out_backups/`:** Session 97 opening
  prompt removed at close; Session 98 opening prompt
  written.
- **Project knowledge base:** unchanged. No re-upload
  required this session.
- **VPS state:** unchanged this session. No VPS
  calls.
- **`bethub-v3/`:** unchanged in canonical state at
  session close. No edits this session — Code's W4
  follow-up build state is the post-Session-96 reality
  on disk; this session triaged, didn't modify.
- **`/tmp/`:** no scratch scripts written this
  session.

## Forward routing

**Confirmed with operator at close:** Session 98 opens
fresh chat after Code executes the housekeeping brief
out-of-session.

**Session 98 shape (two phases):**

1. **Phase 1 — housekeeping report triage** (smaller
   triage than W4 follow-up; brief is 450 lines vs
   762, three coordinated changes vs six). Read
   `dr029/w4_bet_entry/housekeeping_report.md`
   end-to-end; walk deviations / open questions /
   findings; close housekeeping arc.
2. **Phase 2 — real `BetfairAdapter` implementation
   brief drafting.** Substantively unblocked once
   housekeeping closes clean. Drafts against W4 follow-
   up's locked Protocol extension + `price_source`
   field + post-housekeeping clean codebase. Single
   bounded brief; end-to-end drafting cadence likely
   suitable per c. Pre-drafting operator calls
   anticipated: substrate-driven (read W4 brief, W4
   follow-up brief, W4 follow-up report for inherited
   shapes).

**Operator's between-session actions:**

1. **Paste housekeeping commission prompt into a fresh
   Claude Code session.** Prompt produced at session
   close, hard-wrapped ~70 chars per Cat 1.
2. **Let Code execute end-to-end.** Single bounded
   session per brief §9 hard limits. No operator
   escalation mid-session per brief instructions.
3. **Review Code's report when it ships.** Optional —
   Session 98 triage walks the report end-to-end
   regardless.
4. **(Optional) Review the housekeeping brief itself
   between sessions.** Brief locked at 450 lines;
   readable for operator confirmation if desired
   before Code runs.

**Sequence after Session 98:**

- v3 composition-root structural decision drafting
  remains sequenced for Session 99+ (pushed back
  again; real adapter brief takes Session 98).
- Standing-instructions sweep — ten-or-eleven sweep
  candidates accumulated; dedicated fresh-mind
  session whenever operator wants. No gating
  dependency. Could go ahead of Session 98 if
  operator prefers a clean instructions surface
  before drafting the real adapter brief; or after.

**Out of scope for Session 98:**

- New brief drafting beyond the real adapter brief.
- Standing-instructions sweep (deferred to dedicated
  session).
- v3 composition-root structural decision drafting
  (sequenced Session 99+).

**Triage shape for Session 98 Phase 1
(housekeeping):**

1. Read Code's report end-to-end.
2. Walk §6 deviations.
3. Walk §7 open questions one per round, plain-
   operator-language framing per Cat 1.
4. Walk §8 findings — route each (no action / fold
   into existing carry / new brief / contract-
   housekeeping sweep / standing-instructions sweep).
5. Lock close-out: housekeeping arc closed; carry-
   forward items into `current_state.md`.

## Close-out notes

Session 97 was a clean, focused triage session that
landed one principle-level governance event (the
standing principle on tooling-hygiene timing) and
closed the W4 follow-up arc cleanly. Wall-clock 19
minutes — well under split-trigger thresholds.

Three patterns worth holding onto:

- **Inventory-first-then-walk for high-item-count
  triage.** Eleven items in one short-form inventory
  saved walk-blind context cost. Cat 1 candidate (l).

- **Operator-driven principle landing mid-session is
  decision-multiplier shape.** When operator framing
  crystallises into a generalisable principle, name-
  scope-apply same session rather than carrying as
  fuzzy preference. Standing principle becomes
  routing default for subsequent items in same
  session. Pattern reinforces "ground principles in
  the substrate that surfaced them" discipline.

- **Housekeeping-brief-during-close-out is mode-
  coherent when triage routed to Code.** Drafting
  immediately while triage substrate is fresh
  produces tighter cross-references than deferring.
  Reinforces Cat 1 candidate (c) end-to-end-drafting
  cadence.

W4 follow-up arc closed. Housekeeping brief locked.
Standing principle locked. Session 98 sequenced for
housekeeping triage + real adapter brief drafting.
