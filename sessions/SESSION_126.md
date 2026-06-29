# Session 126 — Pre-W14 governance update propagation tail closed; eight propagation fixes + one cosmetic landed mechanically; retroactive SESSION_124.md written; pre-execution risk-advisory added to standing instructions; close-out paperwork landed in-session

**Opened:** 2026-05-12 10:42 ACST
**Closed:** 2026-05-12 11:18 ACST
**Wall-clock:** ~36m elapsed. Same-workday open relative
to S125 close (07:58 ACST same day, 2h44m gap). Same-
workday close-out — no day-rollover, no pause-and-resume.

**Tool routing:** Claude Chat for all work — eleven
`edit_block` calls across `architecture.md` (8) +
`decisions.md` (2) + `v3_data_requirements.md` (1), one
fresh-file write of `sessions/SESSION_124.md` (retroactive
record, 587 lines via twelve chunked `write_file` calls),
plus close-out paperwork. All filesystem operations via
Desktop Commander. No Code dispatch this session.

**Governing DRs invoked:** DR-021 (Adelaide local time
anchoring, open / close). DR-027 (two-database
architecture / bet-data internal shape — Session 124
amendment is the architectural substrate for every
propagation fix this session). DR-019 (derived state on
read — Session 124 amendment referenced by F7).
DR-030 (v3 repo layout — Session 124 amendment
referenced by C1). DR-026 (market-context snapshot —
reference only; unchanged). DR-028 (cross-DB integration
boundary discipline — unchanged; applies to all cross-DB
references in fix text). DR-032 (canonical-reference-
layer / two-table bet record — context for §A.2 / §A.3
spine).

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
→ `2026-05-12 10:42 ACST`.
**Close:** same command → `2026-05-12 11:18 ACST`.

Same-workday open. No day-rollover this session. No
pause-and-resume.

## Pre-flight checks

Drift-check at open held clean per the S125 close's
expectations. `current_state.md` last-updated 2026-05-12
07:58 ACST matched S125 close timestamp. `v3_build_
picture.md` last-updated 07:58 ACST also matched.
`sessions/SESSION_125.md` present (561 lines).
`sessions/SESSION_124.md` correctly absent at open (to
be written retroactively this session).

**Anomaly surfaced at open: stale
`.close_out_backups/SESSION_124_opening_prompt.md`** —
11KB, dated May 12 05:54 ACST. The S125 close-out
flagged this stale artefact (never swept because S124
closed under DC timeout); operator instructed delete
as first move of S126. Cleaned at 10:48 ACST via single
`rm` operation. Post-clean `.close_out_backups/` held
only `SESSION_126_opening_prompt.md` (the active one).

**Pre-flight directory listing:** rebuild folder root
clean. 11 expected `.md` files at root plus
`v3_build_picture.md` plus `openapi.json` (12 total
`.md`-shaped artefacts) plus expected directories
(`agent_review/`, `diagrams/`, `dr029/`,
`orchestration_pack/`, `sessions/`, `skills/`,
`.close_out_backups/`).

**Pre-flight verification (scope item #1):** four
`Amendment 2026-05-12` anchors confirmed at decisions.md
lines 470 (DR-019), 794 (DR-026), 836 (DR-027), 1071
(DR-030) — all unchanged since S125 close. Contract
files confirmed at `bethub-v3/contracts/` (87934-byte
`betfair_client_contract.md` + 39420-byte
`vps_client_contract.md` + empty `__init__.py`).
`sessions/SESSION_125.md` confirmed at 25137 bytes
(modified 08:01 ACST after S125 close).

## Session shape

Single-arc session with four phases plus a mid-session
standing-instruction surfacing.

**Phase 1 — Open + stale backup sweep.** Pre-flight
clean. Stale `SESSION_124_opening_prompt.md` flagged by
operator at S125 close, deleted at S126 first-move.
Pre-flight re-grep + directory state verification all
clean. Operator green-lit Phase 2 entry.

**Phase 2 — Eight propagation fixes + one cosmetic
(F1–F8 + C1).** Eleven `edit_block` calls in sequence
(F2 split into three sub-edits per the opening prompt's
specification). Order: F1 (warm-up, one line) → F2a /
F2b / F2c (§A.4 promo chain) → F3 (§A.5 cash flow
formula) → F4 (§B.1.4 sports auto-settlement, ~30 lines
— the largest single edit, DC-timeout watch flagged
proactively) → F5 (§B.1.5 not-stored paragraph) → F6
(§B.1.5 bet event log reference) → F7 (decisions.md
DR-023 body) → F8 (v3_data_requirements.md
auto-settlement paragraph) → C1 (decisions.md DR-030
§Scope cosmetic). All eleven edits landed cleanly in
one pass. F4 did not trigger a DC timeout — the
~30-line edit_block ran in a single shot. No partial-
write damage.

**Mid-session — operator-surfaced standing instruction
candidate (Cat 3).** Between Phase 2 and Phase 3, the
operator surfaced a recurring failure mode: "if I give
you a task to do and you think it might exceed your
tools limit/context window, please advise PRIOR to
execution. This has happened a couple of times and
it's been a time-drain." Flagged for the S126 close
standing-instruction sweep; queued as a Cat 3
(filesystem and tooling discipline) entry pairing with
the existing DC-timeout discipline. Discussed
substrate inline: S124's DR-027 amendment (~50 lines)
triggered the DC timeout that ended S124; S125
recovered via two ~25-line halves; the empirical
threshold sits between ~30 and ~50 lines per single
edit_block call.

**Phase 3 — Final re-grep verification (Phase 2 of the
opening prompt).** Comprehensive `grep` across
`architecture.md`, `decisions.md`,
`v3_data_requirements.md` for stale patterns. Results
matched the opening prompt's expected zeros and
expected hits exactly:

- `bet_placed.*` in architecture.md + v3_data_
  requirements.md: zero hits.
- `bet_settled.*` in architecture.md +
  v3_data_requirements.md: zero hits.
- `bet_settled.*` in decisions.md: only the two
  expected DR-027 hits at line 812 (body) + line 841
  (amendment citing the framing it supersedes) — both
  correct per amendment convention.
- `the bet event log` / `single event log` /
  `unified event log` in architecture.md: one expected
  hit at line 103 (the §A.2 header
  `**Why per-domain rather than a single event log:**`
  — that's the explanatory contrast, not stale
  framing).
- Same phrases in decisions.md: two expected hits at
  lines 812 + 841 (DR-027 body + amendment).
- `bet_voided` / `bet_logged`: zero hits across all
  three files.
- `Amendment 2026-05-12` count in decisions.md: 4
  unchanged.

Propagation tail confirmed closed.

**Phase 4 — Retroactive SESSION_124.md write.**
Standard session-record structure (header, anchor,
pre-flight checks, session shape, structural drift,
what was delivered, standing-instruction adherence,
open items, session close state, forward routing,
record-honesty footnote). Target ~250–400 lines per
opening prompt; final 587 lines / 24KB matching the
recent-session register. Twelve chunked `write_file`
calls (~25–60 lines each) in rewrite + append mode.
Substrate: S125 opening prompt's Phase 3 narrative
beats, `SESSION_125.md` references back to S124, the
S126 opening prompt's specification, the eight S124
edits visible on disk. No conversational substrate
preserved (S124 transcript did not persist across
Claude.ai sessions); record-honesty footnote at the
tail makes the reconstruction provenance explicit.

**Phase 5 — Close-out paperwork.** This file, plus
`current_state.md` rotation, plus `v3_build_picture.md`
update (pre-W14 governance update → `done`, W14 →
`in flight`, W13 / W15 → `blocked-on-W14`), plus
`standing_instructions.md` Cat 3 edit adding the
pre-execution risk-advisory entry, plus S127 opening
prompt generation, plus `.close_out_backups/` sweep
(delete S126 prompt, write S127 prompt), plus post-close
verification.

## Structural drift surfaced this session

None substantive. The pre-W14 governance update stream
closed end-to-end as the S125 + S126 trajectory
projected; no scope expansion mid-session; no unexpected
findings surfaced during the Phase 2 re-grep. The
session executed cleanly against the S126 opening
prompt's mechanical specification.

**One discipline gap caught and converted to standing
instruction:** the pre-execution risk-advisory pattern
surfaced by the operator mid-session is a new Cat 3
entry, not structural drift in the session itself. The
gap was in S118+ accumulated behaviour (Claude biting
off large single tasks that hit tool limits without
pre-flight flagging), not in S126's execution. Adding
the standing instruction at this close prevents the
pattern recurring.

## What was delivered

Three substantive on-disk artefact updates plus one
fresh session record plus close-out paperwork:

**1. architecture.md — eight propagation fixes (F1–F6
across six sections):**

- **F1 (§A.0 line 49):** reading-order line updated to
  reference the post-S124 section descriptions
  ("bet-record and per-domain event-table spine (A.2),
  bets-row schema (A.3)").
- **F2a (§A.4 line 297):** promo-instance linkage
  reframed from `bet_placed.payload.promo_instance_id`
  to the bet's `promo_instance_id` column.
- **F2b (§A.4 lines 303–306):** triggered FB credit
  reframed — `bet_settled` event → bet's
  `settlement_state` transition to a terminal state
  (typically `SETTLED_LOST` on insurance loss),
  `free_bet_credited` event written in `promo_events`
  with `triggering_bet_id` (column reference, not event
  reference).
- **F2c (§A.4 lines 319–320):** FB deployment chain
  reframed — `bet_placed.payload.free_bet_stake_amount`
  → bet's `free_bet_stake_amount` column;
  `free_bet_deployed` event written in `promo_events`
  with `deploying_bet_id`.
- **F3 (§A.5 lines 362–363):** Location 1 cash flow
  formula reframed — `bet_placed.cash_stake_amount` →
  `bets.cash_stake_amount`; `bet_settled.cash_returned_
  to_book` → per-bet computed `cash_returned` per §A.6.
  Brings §A.5 into alignment with §A.9's derivation.
- **F4 (§B.1.4 lines 715–730):** sports auto-settlement
  decision logic reframed from old three-state
  `finalised` / `voided` / `provisional` to the four
  shipped enums `SETTLED_WON` / `SETTLED_LOST` /
  `VOIDED` / `PROVISIONAL`. The largest single edit
  this session (~30 lines including replacement). Ran
  cleanly in one shot — no DC timeout.
- **F5 (§B.1.5 line ~735):** "What's not stored on the
  bet record" paragraph reframed — settlement_state
  removed from the not-stored list (it IS stored per
  §A.6), with cash_returned added as the genuinely-
  derived-on-read field.

- **F6 (§B.1.5 line ~740):** "bet event log" paragraph
  reframed — `bets` + `bet_legs` tables carry sports
  bets in the same shape as racing bets; settlement
  transitions write to the mutable `settlement_state`
  column regardless of source. Removes the
  non-existent `bet_logged` / `bet_settled` / `bet_
  voided` event type references.

**2. decisions.md — one fix plus one cosmetic:**

- **F7 (DR-023 body line 635):** stale "computed on
  read from the event log" reframed to "computed on
  read from bet records and the per-domain event log
  tables (`cash_flow_events`, `promo_events`,
  `ops_events` per architecture.md §A.2 — see DR-019
  Session 124 amendment for the materialised-view-on-
  entity-row refinement and DR-027 Session 124
  amendment for the per-domain event-table spine)."
- **C1 (DR-030 §Scope ~line 1066):** parenthetical
  added noting contract relocation completed at S125
  ("relocation completed Session 125 — files now at
  `bethub-v3/contracts/`").

**3. v3_data_requirements.md — one fix:**

- **F8 (line 74):** auto-settlement paragraph reframed
  — `bet_settled` event framing → settlement worker
  (W6.5); finalised/provisional vocabulary →
  `SETTLED_WON` / `SETTLED_LOST` / `PROVISIONAL`.

**4. sessions/SESSION_124.md — retroactive write
(587 lines / 24KB).**

Standard session-record format. Five-phase reconstruction
of S124's work (open, six architecture.md edits, two
decisions.md amendments, DR-027 timeout, ungraceful
close) plus structural-drift documentation of the DC-
timeout threshold discovery, plus a record-honesty
footnote making the reconstruction provenance explicit.
Captures the eight items that landed at S124, the
ninth item (DR-027 amendment) that timed out
mid-write, the items that did not start (DR-030
amendment, contract relocation, verify pass, close-out
paperwork), and the items that surfaced retroactively
at S125 (F1–F8 + C1).

**5. standing_instructions.md — Cat 3 entry added:**
pre-execution risk-advisory for tool-limit / context-
window risk. Substrate: S124's DR-027 amendment
edit_block (~50 lines) triggered the DC timeout that
ended S124; S125 recovered via two ~25-line halves.
Operator-flagged at S126 as a recurring failure mode
worth encoding. Pairs with the existing DC-timeout
discipline (post-failure split via
`interact_with_process`); the new entry is the
pre-failure equivalent.

**6. .close_out_backups/ swept:** stale
`SESSION_124_opening_prompt.md` deleted at S126 first-
move (operator instruction); `SESSION_127_opening_
prompt.md` written at close.

## Standing-instruction adherence check

- **Cat 1 silent session-open ritual** — held this open.
  Anchor + required reads + pre-flight + drift-check
  executed silently; the operator-facing orientation
  was a single combined output (recap, anomaly carry,
  v3 build picture, open-items delta, hand-off line).
  Zero step labels in operator-facing text. S125 had
  partially broken this rule; S126 held. One session
  of the multi-session reset complete; S127 needs to
  hold for full reset.
- **Cat 1 silent session-close ritual** — held this
  close. Step labels suppressed; only this session
  record + the single brief one-line post-close output
  surface to the operator. Two sessions clean of the
  recent narration-drift sweep candidate.
- **Cat 1 V3 build picture conditional render at open
  — spirit-of-the-rule heuristic** — rendered at open
  this session (stream state had moved at S125 close).
  Render shape matched the artefact + 1–2 sentence
  detail on the current stream. Six consecutive clean
  applications (S121–S126).

- **Cat 1 calendar-calibrated session open** — held.
  Same-workday recap delivered tight (1 sentence on
  S125's substantive landings + propagation deferral,
  1 sentence on S126's mechanical-fix scope).
- **Cat 1 drift-check** — held at open
  (`current_state.md` + `v3_build_picture.md` +
  `SESSION_125.md` all anchored at 07:58 ACST).
- **Cat 1 open-items delta — conditional** — rendered
  at open (meaningful delta: S125 closed five items,
  S126 carried nine + retroactive write).
- **Cat 1 tightened response register (Session 114)** —
  held. Per-fix briefings stayed short; "plain English"
  framings used on each fix the operator gated. F2–C1
  ran as a single pass after operator broadened
  latitude.
- **Cat 1 call-driven surfacing during section-by-
  section drafting** — held. SESSION_124.md retroactive
  draft proceeded without per-section surfacing (no
  operator-relevant calls within section boundaries;
  substrate was specified in the opening prompt).
- **Cat 2 timestamp anchor at session open + close** —
  held. Open 10:42 ACST; close 11:18 ACST.
- **Cat 2 required reads at session open** — held.
  Read `current_state.md`, `standing_instructions.md`
  (full), `project_context.md`,
  `sessions/SESSION_125.md` in order.
- **Cat 2 pre-flight directory listing** — held at
  open. Stale `SESSION_124_opening_prompt.md` surfaced
  as anomaly, deleted at first-move.
- **Cat 2 governing DRs named in orientation** — held
  (DR-027 + DR-019 + DR-030 + DR-021 named in opening
  output; DR-028 + DR-026 + DR-032 named as
  reference-only).
- **Cat 2 deferral-as-deliverable** — exercised
  proactively (the pre-execution risk-advisory itself
  is structurally about preventing unintended deferral
  via DC timeout).
- **Cat 2 workstream-label / build-picture coherence
  at close (Session 115)** — held. Pre-W14 governance
  update stream closes `done`; W14 enters `in flight`;
  W13 / W15 transition from `blocked-on-pre-W14-
  governance-update` to `blocked-on-W14` (sequenced
  after W14 for event-shape settling). v3_build_
  picture.md updated this close.

- **Cat 3 empirical-verification-before-editing** —
  partially held. For F1 the operator-gated pre-edit
  re-read fired explicitly; for F2–C1 the operator
  broadened latitude (substrate validated via the
  opening prompt's verbatim text) and pre-reads were
  skipped in favour of edit_block's failure-mode
  verification. Zero edits failed; no stale-state
  surprises.
- **Cat 3 `create_file` banned** — held. All writes via
  `Desktop Commander:write_file` or
  `Desktop Commander:edit_block`.
- **Cat 3 verify-every-write** — held throughout. Each
  edit_block's return surface acted as inline verify
  for small edits; the Phase 2 re-grep was the global
  verify for the Phase 1 fix pass.
- **Cat 3 dry-run multi-target mechanical edits** —
  N/A (each fix was single-target via edit_block with
  verbatim `old_string`).
- **Cat 3 REPL discipline** — N/A this session (no
  multi-line Python invocations).
- **Cat 3 pre-execution risk advisory (NEW this
  session)** — surfaced and exercised before adoption.
  F4 risk-flagged proactively before execution; the
  retroactive SESSION_124.md write also risk-flagged
  before execution (tool-call count noted, no
  individual-write timeout risk).
- **Cat 4 divergence-capture-or-fix** — N/A this
  session (no divergence surfaced).
- **Cat 5 software-questions-are-Claude's** — held
  throughout. Build-picture status calls for W13 / W15
  (`blocked-on-W14` rather than `unfinished` given the
  event-shape-settling sequencing intent) were
  Claude's pick.
- **Cat 5 length targets bend to required detail** —
  exercised on the retroactive SESSION_124.md write
  (587 lines vs ~250–400 target). Length earned;
  substrate around what landed vs what didn't vs what
  surfaced retroactively warranted the detail per the
  "doesn't undermine the build" test.

## Open items in / out

Pointer-only — full items live in `current_state.md`
post-rotation.

**Closed in Session 126:**

- **F1–F8 propagation fixes + C1 cosmetic** — all
  landed in Phase 2. Phase 3 re-grep confirmed
  propagation tail closed (zero stale `bet_placed.*` /
  `bet_settled.*` / `bet_voided` / `bet_logged`
  references in architecture.md +
  v3_data_requirements.md).
- **Retroactive SESSION_124.md write** — 587 lines on
  disk at `sessions/SESSION_124.md`. Closes the
  S124-paperwork-gap carried since 2026-05-12 ~07:02
  ACST.
- **Pre-W14 governance update stream** — closed
  end-to-end across S124 + S125 + S126. Stream goes
  `done` at this close; one-session carry begins;
  drops from v3_build_picture.md at S127 close.

**Closed transitively at this close:**

- The Session 42 lesson re-applied successfully: S125's
  operator-pivot pivot from "execute-all-scope-items"
  to "comprehensive-check-then-close-then-defer" was
  the right call; S126 confirmed the bounded scope and
  closed cleanly. No premature close-out risk at S126
  itself — forward routing for S127 (W14 brief
  drafting) is operator-known via the standing arc
  reference chain.

**Opened in Session 126 (NEW for S127):**

- **Cat 3 pre-execution risk-advisory entry** in
  `standing_instructions.md` — operator-flagged this
  session, drafted + added at close. Carries forward
  as standing discipline.

**Operator-side action between sessions:**

- **`standing_instructions.md` needs re-uploading to
  the `bethub-rebuild` Claude Project knowledge base.**
  Cat 3 entry added this close (pre-execution risk-
  advisory). The Project-side cached copy is stale
  until the operator re-uploads. Cheap to do at any
  point before S127 open.

**Primary stream queued for S127:**

- **W14 — Transactions / cash-flow event log.**
  Operational store sub-stream — cash-flow event types
  per `architecture.md` Slice 5 (deposits, withdrawals,
  balance adjustments, funding events, remittances,
  profit-share distributions, external payments).
  Builds against the clean per-domain event-table
  pattern locked at S124's §A.2 spine + DR-027
  amendment. First-deliverable shape: W14 brief
  drafting against the now-clean spec (architecture.md
  + decisions.md + v3_data_requirements.md all
  propagation-clean as of this close).

**Carry-forward dependencies (sensitivity flags
unchanged from S123 / S125):**

- **Hedge classification (DR-025, Finding #8 from
  S123).** Revisit before W15 brief drafting. Strategy
  2 cycle measurement implications.
- **§2.4 Fix 4 cadence design dependency (Finding #3
  from S123).** Fix 4 must verify capture cadence
  brackets near-jump placements tightly.

**Tracked carry per operator instruction (carried
through S118 / S119 / S120 / S121 / S122 / S123 / S125
/ S126):**

- **Alembic adoption** — locked migration tool per
  DR-031, deferred. Sequenced after pre-W14 governance
  update (now `done`) + W14 + W13 + W12 land.

**Carried forward (sweep candidates):**

- **Cat 1 silent session-open and session-close ritual
  narration drift — sweep candidate.** S125 partially
  broke at open (step labels in operator-facing text);
  S125 close also partially broke (per operator's S125
  close summary); S126 open + close both held clean.
  One session of the two-session reset complete; S127
  needs to hold clean for multi-session reset.
- **Cat 1 build-picture conditional render heuristic
  — formalisation candidate.** Six consecutive clean
  applications (S121–S126). Pattern stable; promotion
  to encoded rule is the next step if it holds another
  2–3 sessions.
- **Cat 3 pre-execution risk advisory (NEW Session
  126).** Just-added entry; not yet a sweep candidate;
  observe across S127 / S128 for any drift before
  declaring stable.
- **Cat 4 divergence-capture-or-fix elevation
  candidate.** S125's integrity check exercised the
  pattern; S126 didn't surface a fresh instance.
  Pattern held as sensitivity, not encoded; review
  after a few sessions of W14 / W13 / W12 brief
  drafting where divergence is more likely to surface.

**Carry-forward operational (Sessions 108 / 109
carry):**

- Settings-area cadence follow-up brief — open; waits
  on operational experience.
- Greyhound operational constraint verification —
  open.
- `betfair_adapter.py` single-file mypy cleanup — low
  priority.

## Session close state

- **rebuild folder root:** 11 expected `.md` files
  present plus `v3_build_picture.md` plus `openapi.json`
  plus expected directories. No phantom files.
- **WIP:** no scratch writes this session (all writes
  direct to canonical files; no drafted-but-not-
  assembled artefact content).
- **`.close_out_backups/`:** stale
  `SESSION_124_opening_prompt.md` deleted at S126
  first-move. `SESSION_127_opening_prompt.md` written
  this close. Post-close state: single file
  (`SESSION_127_opening_prompt.md`) only.
- **`sessions/` folder:** `SESSION_124.md` (587 lines /
  24KB, retroactive) + `SESSION_125.md` (561 lines /
  25KB) + `SESSION_126.md` (this file) all present.
  Sessions journal complete through S126.
- **Project knowledge base:** `standing_instructions.md`
  edited this session (Cat 3 entry added).
  **Operator-side action required:** re-upload
  `standing_instructions.md` to the `bethub-rebuild`
  Claude Project knowledge base before S127 open.
- **`bethub-v3/contracts/`:** unchanged from S125 close
  state (`__init__.py` + `vps_client_contract.md` +
  `betfair_client_contract.md`).
- **`dr029/2_7_api_contract_versioning/`:** unchanged
  from S125 close state (contracts relocated; remaining
  files are governance substrate).
- **`current_state.md`:** rotated this close; last-
  updated 2026-05-12 11:18 ACST.
- **`v3_build_picture.md`:** updated this close
  (pre-W14 governance update → `done`; W14 →
  `in flight`; W13 + W15 → `blocked-on-W14`); last-
  updated 2026-05-12 11:18 ACST.

## Forward routing

**Confirmed forward routing for S127:** W14 brief
drafting against the now-clean spec.

W14 is the transactions / cash-flow event log
operational store sub-stream. Brief drafting against
`architecture.md` Slice 5 (cash flow event types) +
the per-domain event-table pattern locked at S124's
§A.2 spine + the DR-027 amendment locking the bet-data
internal shape. The spec is propagation-clean as of
this close (Phase 2 re-grep confirmed zero stale
references across architecture.md +
v3_data_requirements.md; decisions.md amendment
references are correct per DR amendment convention).

Operator confirmation chain for W14 as the S127 entry
point: signposted at S122 (W14 sequenced ahead of
W13 + W12), S123 (W14 brief drafting flagged as the
next substantive arc after pre-W14 governance update
closes), S124 (eight-item scope assumed W14-readiness
at close), S125 close (W14 flagged as `blocked-on-pre-
W14-governance-update`), S126 opening prompt (W14
brief drafting opportunistic-extension flagged if
budget remained after propagation tail closed),
S126 current_state.md rotation (W14 named as primary
S127 stream). Forward routing operator-known via the
standing arc reference chain; no fresh confirmation
required at S126 close.

**Possible S127 pivots:**

- **Clean W14 brief drafting session.** Most likely
  shape — propagation tail closed, spec clean, brief
  drafting is the standard next move.
- **Section-by-section call-driven walk.** Per Cat 1
  (Session 84) — surface only operator-relevant calls
  at each section; mechanical structural choices flow
  from earlier locked decisions.
- **Pre-flight reads of cash flow + balance sections.**
  Architecture.md §A.5 (cash flow), §A.6 (settlement
  state implications for cash returns), DR-008 (Smart
  Betfair view context) are reference reads on
  demand.

**Carry-forward dependencies for W14 brief drafting:**

- W14 brief drafting should explicitly cite the per-
  domain event-table pattern (`cash_flow_events` as
  the dedicated table; no unified events log).
- §A.5 Location 1 balance formula (now propagation-
  clean at this close) is the load-bearing derivation
  W14 builds against — the brief should reference it
  rather than restating.
- DR-019 Session 124 amendment (per-entity mutable
  state stored as columns) applies to bet records but
  NOT to cash flow events — cash flow events are pure
  event-log writes, not entity-row updates. The brief
  should clarify this asymmetry to prevent cross-
  contamination.

**Out of scope for S127** (unless brief drafting ships
fast and there's residual budget):

- W13 / W12 / W15 brief drafting (sequenced after W14).
- DR-025 hedge revisit (parked for pre-W15).
- §2.4 Fix 4 cadence design (independent arc).

---

**Session 126 closes the pre-W14 governance update
stream after a 3-session arc** (S124 attempt under DC
timeout, S125 substantive remediation + integrity
check, S126 propagation tail + retroactive S124
paperwork). The stream's effective scope expanded from
8 items at S123 lock to 17 items closed across the
three sessions. v3 build proper enters its next active
phase at S127 with W14 — first operational store sub-
stream since the W11 accounts/account-at-book closure
at S122.
