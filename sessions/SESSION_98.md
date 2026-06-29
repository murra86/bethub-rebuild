# Session 98

**Title:** W4 housekeeping report triaged end-to-end —
five items resolved (two operator-call items locked +
three no-call items confirmed); Code's report path-
target mismatch caught at open ritual and report moved
to canonical location; `bethub-brief-drafting` skill
updated with absolute-path discipline sub-section
preventing recurrence; sweep candidate (m) added; W4
housekeeping arc closed; Phase 2 (real `BetfairAdapter`
implementation brief drafting) sequenced as Session 99
primary deliverable with `INSUFFICIENT_FUNDS`
canonicalisation folded into Phase 2 brief scope per
§7.1 routing call.

**Opened:** 2026-05-07 12:43 ACST
**Closed:** 2026-05-07 13:34 ACST
**Wall-clock:** ~51 minutes active session work. Same-
workday open relative to Session 97 close (~2h 13m gap;
single-sitting workday continuation, no pause-and-
resume, no day-rollover).
**Tool routing:** Claude Chat exclusively (housekeeping
report triage, two operator calls, skill update via
Desktop Commander edit_block, sweep candidate authoring).
No Claude Code work this Chat session — Phase 2 brief
drafting deferred to Session 99 per Shape 2 close call.
**Governing DRs invoked:** DR-021 (Adelaide local time —
open and close anchors), DR-027 (two-database
architecture — context for cross-database boundary),
DR-028 (cross-DB integration boundary discipline —
same), DR-030 (v3 repo layout — frames §7.1 recovery-
key chain consistency as W4-internal namespace
discipline), DR-031 (v3 tech stack — pytest / ruff /
import-linter discipline confirmed clean post-
housekeeping), DR-032 (canonical reference layer —
informs §6.2 sibling-test ratification on test focus
grounds), DR-019 (derived state on read — informed §7.2
pre-flight namespace upper-snake preservation).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
`2026-05-07 12:43 ACST`.
Close: same command → `2026-05-07 13:34 ACST`.

Same-workday open relative to Session 97 close at 10:30
ACST (2h 13m gap). No pause-and-resume mid-session.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill. One
mandatory operator-facing surface at Step 3:

- **Path-target mismatch caught at pre-flight directory
  listing.** Code's housekeeping report was named at
  `dr029/w4_bet_entry/housekeeping_report.md` in the
  Session 97 housekeeping brief (relative path). Code's
  working directory when executing build briefs is the
  v3 repo (`/Users/tim/Desktop/Projects/bethub-v3/`) —
  where it runs pytest, ruff, import-linter, and module
  edits. The relative path resolved at the v3 repo root,
  not the rebuild folder where the brief itself lives.
  The mirrored `dr029/w4_bet_entry/` directory inside
  the v3 repo (created by Code as part of the path
  resolution) meant the path was *valid*, just pointing
  somewhere unexpected — silent mis-routing, no error
  message. Caught at pre-flight directory listing
  (rebuild folder showed brief but no report); report
  located via filesystem search at
  `bethub-v3/dr029/w4_bet_entry/housekeeping_report.md`
  (413 lines). Operator confirmed Option A (move to
  canonical path); report moved via `mv`; phantom
  `bethub-v3/dr029/w4_bet_entry/` and
  `bethub-v3/dr029/` directories cleaned via `rmdir`
  (both empty post-move).
- Rebuild root: 11 expected `.md` files present plus
  `openapi.json`, `external_api_resources.md`,
  `.DS_Store`, and `v3_build_picture.md`. All directories
  present (`agent_review`, `diagrams`, `dr029`,
  `orchestration_pack`, `sessions`, `skills`,
  `.close_out_backups`).
- `.close_out_backups/` contained `SESSION_98_opening_prompt.md`
  only (Session 97 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated
  `2026-05-07 10:30 ACST` matched Session 97 close;
  `sessions/SESSION_97.md` present at 921 lines (matches
  opening prompt's "~922 lines" estimate);
  `v3_build_picture.md` last-updated matched Session 97
  close (W4 stream `done` 1-session carry).
- Same-workday recap delivered at 2h 13m gap.
- V3 build picture: skip-silent at open (no stream
  movement in 2h 13m gap; W4 stream still `done`
  1-session carry from Session 97 close).
- Open-items delta at open: skip-silent at open (no
  meaningful delta in 2h 13m gap).
- Governing DRs named at open: DR-027, DR-028, DR-030,
  DR-031, DR-032, DR-019, DR-021. DR-029 named as
  closed.

## Session shape

Session 98 was a focused two-phase session that closed
its first phase cleanly and deferred its second phase
on operator's split-avoidance call. Three distinct
sub-phases:

**Sub-phase A — open-ritual anomaly recovery.** Pre-
flight directory listing surfaced the missing
`housekeeping_report.md` at the canonical rebuild-
folder path. Recovery was: (1) filesystem search to
locate the actual report position; (2) operator call
on Option A (move) vs Option B (read in place); (3)
move via `mv`; (4) phantom-directory cleanup via
`rmdir`; (5) two-route fix proposal (skill update +
sweep candidate); (6) operator approval; (7) skill
update via `Desktop Commander:edit_block` adding
"Output paths are absolute, anchored at the rebuild
folder root" sub-section to `bethub-brief-drafting`
skill at line 180. Total recovery time: ~5 minutes.
The catch happened exactly where the open-ritual is
designed to catch it; structural drift surfaced as
designed.

**Sub-phase B — Phase 1 housekeeping report triage.**
Read Code's 413-line housekeeping report end-to-end.
Operator-driven inventory-first cadence (sweep
candidate l from Session 97) applied: five items
inventoried in short form with operator-call /
no-call flags before walking. Three no-call items
acknowledged in one round (§6.1 test count delta;
§7.2 pre-flight namespace preservation; §9 length
flag). Two operator-call items walked one per round:

- **§7.1 — `INSUFFICIENT_FUNDS` casing.** Question
  was whether to canonicalise `INSUFFICIENT_FUNDS`
  (upper-snake) to `insufficient_funds` (lower-snake)
  in the same `_path_b_result` recovery-key chain
  that §5.3 just canonicalised, or defer it.
  Recommendation: Option A (same-sweep, fold into
  Phase 2 real adapter brief). Three reasons cited:
  standing principle direct hit (locked Session 97);
  casing-as-signal argument is weak (both keys
  originate from same Betfair API error layer);
  Phase 2 adapter brief is going to specify the
  boundary translation layer anyway. Operator:
  confirmed Option A.
- **§6.2 — sibling parametrised test vs mutating
  existing.** Code added a sibling test
  `test_sqlite_round_trip_price_source` rather than
  mutating `test_sqlite_round_trip` body, citing
  test focus + the brief's "1–4 new sub-assertions"
  hint. Recommendation: Option A (ratify the
  sibling-test shape). Three reasons: test focus is
  a real engineering value; the brief's §6
  sequencing note hint matches Code's interpretation;
  cost of rewriting is non-zero for no benefit.
  Operator: confirmed Option A.

W4 housekeeping arc closed. Codebase in clean post-
housekeeping state: 323 tests passing, ruff clean,
import-linter 5/5 contracts kept.

**Sub-phase C — Phase 2 sequencing call.** Three
shapes presented to operator: Shape 1 (proceed with
Phase 2 now end-to-end); Shape 2 (close clean now,
Phase 2 to Session 99); Shape 3 (start substrate
reads + scoping conversation today, draft Session 99).
Recommendation: Shape 2. Reasons cited: Phase 1
landed cleanly; Shape 1 would likely run into split-
trigger territory mid-Phase-2 (which is the worst
close-point for a long brief); Shape 2 preserves
Phase 1 close-out housekeeping without competing with
Phase 2 substrate work. Operator: confirmed Shape 2.

## What was delivered

Session 98 produced two skill-level governance edits
(one shipped, one routing-decision lock to encode at
sweep), one housekeeping-arc closure across five
report items, and three filesystem-state corrections
(report move + two phantom-directory removals):

**`bethub-brief-drafting` skill updated** —
`/Users/tim/Desktop/Projects/bethub-rebuild/skills/bethub-brief-drafting/SKILL.md`
gained 19-line sub-section "Output paths are absolute,
anchored at the rebuild folder root" under "Discipline
that travels with every brief" (line 180). Names the
failure mode (Code's working directory is the v3
repo, relative paths resolve there, not the rebuild
folder); names the substrate (Session 98 open ritual);
names the five path categories the discipline covers
(output report, pre-reads, anchor files, verification
queries, scratch/temporary); clarifies that absolute
paths into the v3 repo are fine when the file
genuinely lives there. File: 215 → 233 lines (+18 net,
trailing-newline normalised). Auto-syncs to all
future sessions because skill is loaded from rebuild-
folder canonical location; no operator-side re-upload
action required.

**Sweep candidate (m) — Code-bound brief output paths
are absolute, anchored at the rebuild folder root.**
Cat 3 (filesystem and tooling discipline) target.
Locked Session 98; sweep deferred to dedicated fresh-
mind sweep session. Carried alongside the existing
ten-or-eleven candidates. Skill update (above)
captures the discipline at the procedural layer;
sweep candidate captures it as canonical-truth
instruction at the upstream layer.

**Triage decisions locked across five housekeeping
report items:**

- §6.1 — test count delta +91 vs +12 brief estimate:
  no-call, awareness only. Brief estimate was wrong
  (assumed only 12 tests hidden, but 87 were);
  Code's wider delta is the better outcome
  semantically. Reinforces sweep candidate (h)
  brief-length-and-count calibration.
- §6.2 — sibling parametrised test ratified.
  `test_sqlite_round_trip_price_source` is the
  canonical home for `price_source` round-trip
  coverage going forward.
- §7.1 — `INSUFFICIENT_FUNDS` casing locked Option A:
  canonicalise `INSUFFICIENT_FUNDS` →
  `insufficient_funds` in Phase 2 real adapter brief
  scope. Standing principle (Session 97) exercised
  for the second time on this kind of decision.
- §7.2 — pre-flight namespace upper-snake convention
  correctly preserved by Code per brief's API-shape
  boundary guidance. Confirmatory only; carry-
  forward note for low-priority namespace-convention
  review.
- §9 length flag (410 vs 200–300): no-call,
  reinforces sweep candidate (h).

**Filesystem-state corrections:**

- Moved `housekeeping_report.md` (413 lines) from
  `bethub-v3/dr029/w4_bet_entry/` to
  `bethub-rebuild/dr029/w4_bet_entry/` via `mv`.
  Original mtime preserved (May 7 10:46, Code's
  actual write time).
- Removed phantom `bethub-v3/dr029/w4_bet_entry/`
  directory (empty post-move) via `rmdir`.
- Removed phantom `bethub-v3/dr029/` directory
  (empty after w4_bet_entry removal) via `rmdir`.
  v3 repo back to expected shape (governance lives
  in `bethub-rebuild/`, not `bethub-v3/`).

**No edits to canonical-truth files in this session.**
No edits to `decisions.md`, `architecture.md`,
`governance.md`, `standing_instructions.md` (sweep
candidate (m) accumulated; sweep deferred to dedicated
session), `vision.md`, `v3_data_requirements.md`,
`project_context.md`. Skill update is the substantive
write of the session at the procedural layer; all
other governance layers untouched.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028,
  DR-030, DR-031, DR-032, DR-019, DR-021 named at open.
  DR-029 named as closed gating arc.
- **Cat 1 (calendar-calibrated recap)** — same-workday
  tight recap delivered at 2h 13m gap.
- **Cat 1 (V3 build picture conditional render)** —
  skip-silent at open (no stream movement in 2h 13m
  gap). W4 stream's one-session `done` carry from
  Session 97 close drops at this close per Cat 1 done-
  stream-rotation discipline.
- **Cat 1 (open-items delta)** — skip-silent at open
  (no meaningful delta in 2h 13m gap).
- **Cat 1 (drift-check)** — done at open, all three
  checks matched Session 97 close timestamp.
- **Cat 1 (silent session-open ritual)** — held except
  for one mandatory operator-facing surface: path-
  target mismatch on housekeeping report. Handled per
  skill negative-scope rule: surface anomaly
  immediately rather than guess; operator confirmed
  routing; ritual resumed.
- **Cat 1 (silent session-close ritual)** — holding
  this close. Steps 1-10 silent except for the
  forward-routing question at Step 3 (Shape 1 vs
  Shape 2 vs Shape 3 Phase 2 sequencing call); Step 11
  produces brief verification line.
- **Cat 1 (call-driven surfacing during section-by-
  section)** — held with operator-driven cadence
  variant. Inventory-first cadence (sweep candidate l
  from Session 97) applied to housekeeping report
  triage; five items inventoried with operator-call /
  no-call flags before walking.
- **Cat 1 (short responses, plain language)** — held
  throughout. Three no-call items acknowledged in one
  round; two operator-call items walked one per round
  with plain-language + pros/cons + recommendation
  framing.
- **Cat 1 (decision-maker framing)** — held. Each
  operator-call item led with the situation, the
  options, and the recommendation; reasoning followed.
- **Cat 1 (don't drift to alternatives when operator
  clear)** — held. Operator's Shape 2 confirmation
  acted on without second-guessing; close-out
  proceeded directly.
- **Cat 1 (escalate to detail only when warranted)** —
  held. No-call items got short flag-only entries;
  operator-call items got full pros/cons/risks +
  recommendation detail.
- **Cat 1 (line-break rendering for review content)** —
  n/a this session; no fenced review content rendered
  for operator confirmation.
- **Cat 1 (default to luddite-analyst-gambler
  brevity)** — held throughout.
- **Cat 1 (plain-operator-language default for Code-
  report content surfacing)** — held throughout the
  five-item walk. No schema field name appeared
  without operational framing alongside; no DR cited
  without bracketed reminder when invoked mid-
  discussion.
- **Cat 2 (timestamp re-anchoring)** — open and close
  anchored. No pause-and-resume mid-session.
- **Cat 2 (pre-flight directory listing)** — done at
  open (caught the path-target mismatch). Done at
  close via list_directory and post-close
  verification.
- **Cat 2 (Desktop Commander default)** — held
  throughout. All file ops via `Desktop Commander`
  family. No `bash_tool` reflex this session (sweep
  candidate (a) gave no fresh data point this
  session).
- **Cat 2 (REPL discipline)** — n/a; no multi-line
  Python this session.
- **Cat 2 (`create_file` vs `write_file` namespace
  gotcha)** — n/a; skill update used
  `Desktop Commander:edit_block` (surgical edit), not
  fresh write.
- **Cat 2 (dry-run multi-target mechanical edits)** —
  n/a; skill update was a single surgical edit
  (one `old_string` → one `new_string`).
- **Cat 2 (persist drafted artefact content to
  scratch)** — n/a; this session's substantive write
  *is* the canonical artefact (skill update), not
  session-scratch deferred to a future session.
- **Cat 2 (surface structural-drift in session
  record)** — flagged this session: skill update is
  a procedural-layer governance edit (sub-section
  added to `bethub-brief-drafting` skill). Not
  schema-shifting on a canonical-truth file, but
  named explicitly here per Cat 2 discipline.
- **Cat 3 (`bash_tool` non-functional)** — held; no
  attempts this session.
- **Cat 3 (external API resources reach-for)** — n/a
  this session.
- **Cat 3 (NEW — Code-bound brief output paths
  absolute)** — sweep candidate (m) authored this
  session. Not yet in canonical truth; carries to
  fresh-mind sweep session.
- **Cat 4 (DR-027/028 invoked)** — named at open.
  Not load-bearing for this session's work (no cross-
  database topics surfaced).
- **Cat 4 (operational/analytical line discipline)** —
  held. Triage maintained operational-line framing
  throughout (W4 bet-entry workflow is operational-
  line by design).
- **Cat 4 (single-cycle analysis discipline)** — n/a
  this session.
- **Cat 4 (Betfair as canonical source)** — load-
  bearing for §7.1 routing call (Betfair-side error
  codes are canonical; W4 boundary translates to
  internal lower-snake convention).
- **Cat 4 (standing principle locked Session 97 — pay
  tooling-hygiene costs now)** — exercised twice this
  session: §7.1 (canonicalise `INSUFFICIENT_FUNDS`
  now); §6.2 (preserve cleaner sibling-test shape).
  The principle isn't "always change things" — it's
  "fix knowable-bad state, preserve knowable-good
  state."
- **Cat 5 (software questions are Claude's)** — held
  throughout. All Code-territory items (§6.2 test
  shape, §7.2 namespace preservation, §8.x
  confirmations) ratified or flagged-only — no
  operator-side decisioning solicited on technical-
  only matters. Operator calls limited to genuinely
  strategic / routing items (§7.1 same-sweep call,
  Phase 2 shape call).

## Session-98-specific reflections

- **Open-ritual catch validated.** The Cat 2 pre-
  flight directory listing caught the path-target
  mismatch exactly where the discipline is designed to
  catch it. The mismatch was silent (no error message
  from Code, no error at the rebuild-folder check) but
  surfaced immediately because the open ritual checks
  for what's expected to be there. Without the open-
  ritual check, this would have surfaced mid-triage
  ("where's the report?"). Reinforces that open-
  ritual silent-discipline exception ("surface
  immediately when something is wrong") earns its
  cost across sessions.

- **Two-route fix is structurally cleaner than
  one-route fix when failure mode is recurring.**
  Path-target mismatch is recurring-failure-mode
  shape: any future build brief could hit it. Skill
  update (Route 1) prevents recurrence at the
  procedural layer; sweep candidate (m) (Route 2)
  encodes the discipline as canonical-truth
  instruction at the upstream layer. Skill is faster
  to land (immediate); instruction is more durable
  (survives skill rewrites). Doing both costs little
  and protects against both kinds of drift. Pattern
  worth preserving: when a failure mode is recurring,
  fix it at both procedural (skill) and canonical-
  truth (instruction) layers.

- **Standing principle as routing default works
  cleanly across sessions.** Session 97's lock ("pay
  tooling-hygiene and structural-consistency costs
  now, while the project is in build, rather than
  carry them into live operations") was applied
  twice this session — once direct (§7.1
  canonicalisation) and once reverse (§6.2
  preserve-the-cleaner-shape). The principle's
  bidirectionality (don't introduce hygiene cost for
  literal-reading) emerged organically in §6.2's
  recommendation. Pattern: the principle reads as
  "fix knowable-bad state, preserve knowable-good
  state" — neither monotone "always change" nor
  monotone "always preserve."

- **Inventory-first cadence (sweep candidate l)
  reinforced again.** Five-item inventory in one
  short-form pass with call/no-call flags allowed
  the operator to see the session-budget shape
  upfront and confirm walking order. Three no-call
  items acknowledged in one round saved three
  operator round-trips. Pattern: inventory-first
  scales linearly with item count vs walk-blind's
  quadratic (each item's context cost compounds).
  Reinforces sweep candidate l for Cat 1 encoding.

- **Shape 2 close call protected Phase 2 from
  split-trigger pressure.** Operator's Shape 2 pick
  (close clean now, Phase 2 to Session 99) avoided
  the worst close-point for a long brief — mid-
  drafting close. Real adapter brief is similar in
  scope to W4's original brief (~2000 lines).
  Pattern: when a session has cleanly-closeable
  Phase 1 and uncertain-budget Phase 2, the
  cleanly-closeable phase wins on close-point
  optimisation. Reinforces governance.md split-
  trigger discipline (split rather than push
  through) at the *strategic* level (don't start
  Phase 2 if it'll need to be split mid-drafting),
  not just the tactical level (don't push past a
  trigger that already fired).

## Open items in (carried forward)

New from Session 98:

- **`INSUFFICIENT_FUNDS` canonicalisation folds into
  Phase 2 real adapter brief.** §7.1 routing call.
  Brief's §5 (substantive scope) carries an explicit
  anchor for the rename — orchestrator.py:~1050 `if`
  arm, plus any matching test fixture. Brief's §7
  (empirical verification) extends to confirm post-
  rename pytest-green. Brief's §11 (cross-references)
  cites Session 98 §7.1 as the routing decision that
  brought this in.
- **Pre-flight namespace upper-snake convention
  review (low-priority).** Carry-forward note from
  §7.2 confirmatory item. The `MARKET_OPEN` /
  `MARKET_SUSPENDED` / `MARKET_CLOSED` /
  `MARKET_STATUS_UNAVAILABLE` namespace is internally
  consistent; a separate sweep could revisit it but
  no impact on Phase 2 work. Parking-lot item.
- **Sweep candidate (m) — Code-bound brief output
  paths are absolute, anchored at the rebuild folder
  root.** Cat 3 routing target. Locked Session 98;
  sweep deferred. Skill update at
  `bethub-brief-drafting` captures the discipline at
  procedural layer.

**Carry-forward from Session 97 (status):**

- **Real `BetfairAdapter` implementation brief
  drafting (now Session 99 primary deliverable per
  Shape 2 close call).** Inherits clean post-
  housekeeping codebase + `INSUFFICIENT_FUNDS`
  canonicalisation in scope per §7.1. Substantively
  unblocked; Protocol extension and `price_source`
  field shapes inherited from W4 follow-up build.
- **Standing principle: pay tooling-hygiene and
  structural-consistency costs now (sweep candidate
  j).** Routing target Cat 4. Exercised twice this
  session.
- **Protocol-extension shape principle (sweep
  candidate k).** Cat 4 candidate. Not exercised
  this session; held.
- **Multi-item-triage inventory-first cadence (sweep
  candidate l).** Cat 1 candidate. Exercised again
  this session (five-item inventory). Held.
- **W7 brief drafting carry — `price_source`
  semantic on operator manual override.** Specific
  decision shape captured. Not exercised this session.
- **W7 brief drafting generic carry — modal copy
  distinguishing REST-also-failed from market-
  suspended.** Per-recovery-path copy decision. Not
  exercised this session.
- **Contract-cleanup-sweep candidate — explicit
  "REST-returns-fresh" contract assertion.** Held.
- **`bash_tool` standing-instruction softening
  reinforced (sweep candidate a).** No fresh data
  point this session — open ritual didn't reflexively
  reach for `bash_tool`. Watch in future sessions.
- **Housekeeping Code brief execution / report
  triage** — **closed this session.**

**Carry-forward from Session 96 (status):**

- **End-to-end-drafting cadence as Cat 1 explicit
  variant (sweep candidate c)** — not exercised this
  session (no brief drafting). Held.
- **Brief-length-estimate calibration as Cat 5
  candidate (h)** — reinforced again this session
  (housekeeping report 410 lines vs 200–300 estimate;
  brief estimate of "+12 tests" was 87-tests-too-
  low). Held.
- **"Review X" ambiguity-resolution pattern as Cat 1
  candidate (i)** — not exercised this session.
  Carry-forward.

**Carry-forward from Session 95 (status):**

- **Mid-session scratch writing as Cat 2 explicit
  pattern** — not exercised this session. Carry-
  forward.
- **Plain-operator-language default for Code-report
  content surfacing** — exercised cleanly throughout
  this session's five-item walk. Pattern held without
  drift. Carry-forward.
- **`bash_tool` Cat 3 rule sharpening (a)** — not
  reinforced this session (no fresh attempt). Carry-
  forward.
- **Brief-drafting pre-flight skill check** — not
  exercised this session (no fresh Code investigation
  needed). Carry-forward.
- **Structural drift between Cat 1 framing-and-
  internals match check** — not exercised this
  session. Carry-forward.
- **`str_replace` namespace gotcha substrate** —
  not exercised this session. Carry-forward.

**Carry-forward from earlier sessions (unchanged
unless noted):**

- **v3 composition-root structural decision** —
  sequenced Session 100+ (pushed back again; Session
  99 takes real adapter brief drafting). Genuinely
  next-after-real-adapter candidate.
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
- **v3 build-proper UI candidates** — three
  surfaces logged §5.2 of §2.10 brief.
- **Betfair SP-projection accuracy study** — post-
  DR-029 analytical capability candidate.
- **Racing EV model recalibration with §2.10
  bucket-1 captures** — post-DR-029 analytical work.
- **WIP §16** — VPS in-flight work. Unchanged.

Closed this session:

- **Housekeeping Code report triage** (Session 97
  carry) — **closed.** All five report items walked;
  two operator calls resolved; three awareness items
  addressed. W4 housekeeping arc complete.
- **Path-target mismatch on Code's housekeeping
  report** — closed at open ritual via report move +
  phantom-directory cleanup. Two-route fix shipped
  (skill update + sweep candidate (m)).

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
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC`
  betDelay confidence note. Partly addressed
  Session 76.

## Open items out (closed this session)

- **Housekeeping Code report triage** — closed. All
  five items resolved; W4 housekeeping arc complete;
  no remaining triage debt.
- **Path-target mismatch on Code's housekeeping
  report** — closed at open ritual.

## Session close state

- **Rebuild folder root:** unchanged this session in
  canonical-truth files. No edits to root-level
  governance docs.
- **`current_state.md`:** updated at close — "Last
  updated" → `2026-05-07 13:34 ACST`; "Where we are"
  → housekeeping arc closed, sweep candidate (m)
  added, skill update shipped, Phase 2 sequenced for
  Session 99; "What's next" → Session 99 real adapter
  brief drafting; required reads adjusted for
  Session 99.
- **`v3_build_picture.md`:** updated at close. **W4
  stream drops from picture per Cat 1 done-stream-
  rotation discipline (one-session carry expired).**
  "Last updated" bumped to this close timestamp.
- **`standing_instructions.md`:** unchanged this
  session in canonical-truth state. Sweep candidates
  now eleven-or-twelve (a, c, d, e, f, g, h, i, j,
  k, l, m):
  - (a) `bash_tool` softening — no fresh data point
    this session.
  - (c) End-to-end-drafting-after-§1-confirmation —
    not exercised this session.
  - (d) Mid-session scratch writing as Cat 2
    explicit.
  - (e) Plain-operator-language default for Code-
    report content surfacing — reinforced cleanly.
  - (f) Brief-drafting pre-flight skill check —
    parallel Code investigation as named option.
  - (g) Structural-drift framing-vs-internals match
    check.
  - (h) Brief-length-estimate calibration as Cat 5
    candidate — reinforced again (estimate vs reality
    twice this report).
  - (i) "Review X" ambiguity-resolution as Cat 1
    candidate.
  - (j) Pay tooling-hygiene and structural-
    consistency costs now (Cat 4 routing target) —
    exercised twice this session.
  - (k) Protocol-extension shape principle (Cat 4
    candidate) — held.
  - (l) Multi-item-triage inventory-first cadence
    (Cat 1 candidate) — exercised again this session.
  - (m) **Code-bound brief output paths are
    absolute, anchored at rebuild folder root (Cat 3
    candidate)** — new this session.

  Sweep deferred to fresh-mind dedicated session;
  eleven-or-twelve candidates is enough mass for a
  real sweep session. Sequenced for after real
  adapter brief lands cleanly.
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session.
- **`decisions.md`:** unchanged this session.
- **`skills/bethub-brief-drafting/SKILL.md`:** **new
  sub-section added this session** — "Output paths
  are absolute, anchored at the rebuild folder root"
  at line 180, under "Discipline that travels with
  every brief". File: 215 → 233 lines (+18 net).
  Auto-syncs to all future sessions; no operator-
  side re-upload required.
- **`skills/bethub-session-open/SKILL.md`:**
  unchanged this session.
- **`skills/bethub-session-close/SKILL.md`:**
  unchanged this session.
- **`dr029/w4_bet_entry/`:**
  - `housekeeping_brief.md` — unchanged.
  - **`housekeeping_report.md`** — **moved into this
    folder this session** from
    `bethub-v3/dr029/w4_bet_entry/`. 413 lines.
    Code's actual mtime preserved (May 7 10:46).
    Read end-to-end this session for Phase 1 triage.
  - All other artefacts unchanged.
- **`bethub-v3/dr029/`:** **directory removed this
  session** (phantom, created by Code's path
  resolution; empty post-housekeeping-report move).
- **`bethub-v3/dr029/w4_bet_entry/`:** **directory
  removed this session** (phantom, same).
- **`sessions/`:** Session 98 record written by
  close ritual (this file).
- **`.close_out_backups/`:** Session 98 opening
  prompt removed at close; Session 99 opening prompt
  written.
- **Project knowledge base:** unchanged. No re-
  upload required this session. Skill update
  auto-syncs from rebuild-folder canonical location.
- **VPS state:** unchanged this session. No VPS
  calls.
- **`bethub-v3/`:** unchanged in canonical state at
  session close (phantom dirs removed; no other
  edits this session — codebase is post-Session-97
  housekeeping state).
- **`/tmp/`:** no scratch scripts written this
  session.

## Forward routing

**Confirmed with operator at close (Shape 2):**
Session 99 opens fresh chat for real `BetfairAdapter`
implementation brief drafting Phase 2.

**Session 99 shape:**

Real `BetfairAdapter` implementation brief drafting.
Single bounded brief drafting session; end-to-end
drafting cadence likely suitable per sweep candidate
(c). Scope inheritance:

- Protocol extension shape from W4 follow-up brief.
- `price_source` field placement from W4 follow-up
  build (DR-032 canonical-reference-layer).
- Clean post-housekeeping codebase (323 tests, ruff
  clean, 5/5 import-linter contracts).
- `INSUFFICIENT_FUNDS` canonicalisation folded into
  brief scope per §7.1.
- W3/W4 import precedent (sweep candidate k held
  for explicit application).
- W4 mock-vs-real seam from W4 v1 brief.
- Betfair Streaming spec (DR-029 §2.4) and live-
  pricing surface (contract §9.1, post-v1.3
  amendment).
- External Betfair API documentation (Exchange REST
  + Streaming) per `external_api_resources.md`.

Pre-drafting operator calls anticipated: substrate-
driven (read W4 brief, W4 follow-up brief, W4
follow-up report for inherited shapes; identify
mock-vs-real seam; confirm scope boundary on
streaming-vs-REST).

Brief is similar in scope to W4's original brief
(2121 lines) — likely 1500–2000 lines, end-to-end
drafting cadence. If session-budget tightens mid-
drafting, prefer split-and-defer to Session 100
over push-through.

**Operator's between-session actions:** none
required. Skill update auto-syncs; no Code work
between sessions.

**Sequence after Session 99:**

- v3 composition-root structural decision drafting
  remains sequenced for Session 100+ (pushed back
  again; real adapter brief takes Session 99).
- Standing-instructions sweep — eleven-or-twelve
  sweep candidates accumulated; dedicated fresh-mind
  session whenever operator wants. No gating
  dependency.

**Out of scope for Session 99:**

- Standing-instructions sweep (deferred to dedicated
  session).
- v3 composition-root structural decision drafting
  (sequenced Session 100+).
- Any work outside real adapter brief drafting.

**Drafting shape for Session 99:**

1. Pre-flight grounding reads (W4 brief, W4 follow-up
   brief and report, contract §13/§9.1,
   `external_api_resources.md`).
2. Step 1 — name the job (real `BetfairAdapter`
   implementation brief; what Code builds; which
   scope-doc item it serves).
3. Step 2 — pre-flight grounding (file inventory at
   `clients/betfair_client/v1/` + `workflows/bet_entry/v1/`).
4. Step 3 — choose structural shape (likely build
   precedent from Session 87 W4 build brief +
   Session 33 source-review brief).
5. Step 4 — draft end-to-end in numbered sections.
6. Steps 5–7 — surface explicit calls + operator
   review + lock the brief.
7. Step 8 — forward routing for Session 100 (post-
   brief Code execution).

## Close-out notes

Session 98 was a clean two-phase session that closed
its first phase end-to-end and deferred its second
phase on operator's split-avoidance call. Wall-clock
51 minutes — under split-trigger thresholds.

Three patterns worth holding onto:

- **Open-ritual catch validates the discipline.** The
  pre-flight directory listing caught the path-
  target mismatch silently and immediately —
  exactly what the discipline is designed for. Worth
  reinforcing across sessions.

- **Two-route fix is the right shape for recurring-
  failure-mode catches.** Skill update (procedural
  layer) + sweep candidate (canonical-truth layer)
  protects against both kinds of drift. Pattern
  reinforced this session.

- **Standing principle is bidirectional.** "Pay
  tooling-hygiene costs now" reads as "fix knowable-
  bad state, preserve knowable-good state" — applied
  twice this session in opposite directions (§7.1
  fix, §6.2 preserve). Pattern worth preserving.

W4 housekeeping arc closed. Skill update shipped.
Sweep candidate (m) added. Phase 2 sequenced for
Session 99 real adapter brief drafting.
