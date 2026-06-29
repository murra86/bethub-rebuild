# Session 94

**Title:** `betfair_client` v1.2 contract addition brief drafted
end-to-end and locked at 676 lines; brief commissions a single
Code session that amends `betfair_client_contract.md` in place
per §14.4 backward-compatible mechanism (adds §9.6
`get_account_funds` and §9.7 `get_market_catalogue`),
implements the corresponding methods in
`clients/betfair_client/v1/` with mocked-library tests, and
produces a short report; brief grounded empirically against
`betfairlightweight` v2.23.2 and the live W3 surface pattern;
Code commenced execution against the brief during this
session.
**Opened:** 2026-05-07 07:36 ACST
**Closed:** 2026-05-07 08:26 ACST
**Wall-clock:** ~50 minutes active session work. Same-workday
open relative to Session 93 close (~23 min gap). No day-
rollover, no split triggers.
**Tool routing:** Claude Chat (brief drafting end-to-end). No
Claude Code work in this Chat session — Code commissioned
out-of-session via the locked brief; execution running in
parallel chat as session closed.
**Governing DRs invoked:** DR-021 (Adelaide local time),
DR-027 (two-database architecture — context for why
`betfair_client` is operational-line-only), DR-028 (cross-DB
boundary discipline — frames the v3-side consumer pattern),
DR-030 (v3 repo layout — informs file locations and import-
linter contracts), DR-031 (v3 tech stack — Pydantic v2,
pytest, ruff, import-linter), DR-032 (canonical reference
layer for all bet records — load-bearing for §5.2 / §6.2 /
§7.2 of the brief).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
`2026-05-07 07:36 ACST`.
Close: same command → `2026-05-07 08:26 ACST`.

Same-workday open relative to Session 93 close at 07:13 ACST
(23-min gap, single-sitting continuation). No pause-and-resume.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, calibrated
against Cat 1 silent-ritual instruction:

- Rebuild root: 12 expected `.md` files, `openapi.json`,
  `external_api_resources.md`, `.DS_Store`. All directories
  present.
- `.close_out_backups/` contained `SESSION_94_opening_prompt.md`
  only (Session 93 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated
  `2026-05-07 07:13 ACST` matched Session 93 close;
  `sessions/SESSION_93.md` present (703 lines);
  `v3_build_picture.md` last-updated `2026-05-07 07:13 ACST`
  matched Session 93 close (W4 status `done`).
- Same-workday recap delivered at 23-min gap.
- V3 build picture: rendered at open (Session 93 close moved
  W4 stream to `done`).
- Open-items delta: skip-silent at open (no items
  closed/opened/overdue in 23-min gap).
- Governing DRs named at open: DR-029 (closed), DR-027,
  DR-028, DR-030, DR-031, DR-021.

## Session shape

Session 94 was a **brief-drafting session** — single
deliverable, single artefact, end-to-end through the
`bethub-brief-drafting` skill. The session ran the skill's
full eight-step ritual:

1. Job-naming round (Step 1) — surfaced two operator-driven
   refinements (artefact-relationship framing, scope-bundling
   call) that locked the brief's framing before any drafting.
2. Pre-flight grounding (Step 2) — verified v3 repo layout
   (`clients/betfair_client/v1/` one-file-per-surface
   pattern), confirmed `betfairlightweight` v2.23.2 surface
   for both endpoints, captured field-mapping from library
   resources to contract Pydantic shapes, verified
   `.importlinter` contracts.
3. Structural-shape lock (Step 3) — operator-confirmed
   surgical-fix-style for contract amendment + build-style
   for implementation; "mini-build with paired contract
   amendment" framing locked.
4. End-to-end drafting (Step 4) — brief drafted across 13
   sections in continuous flow per operator request after §1
   surfacing went well. ~676 lines.
5. Decisions surfaced for operator review (Step 5) — five
   operator-relevant calls plus two genuine open questions
   surfaced; all seven resolved cleanly.
6. Operator review (Step 6) — collapsed-into-Step-5 since
   the operator requested end-to-end drafting then review.
7. Lock (Step 7) — single edit applied (item 2:
   `event_timezone` → `event_time_zone` per library
   passthrough principle), brief locked at 676 lines, hash
   `510cbfbf...88054715` captured.
8. Forward-routing surfaced (Step 8) — Code prompt produced
   with hard-wraps; Code execution commenced before this
   session closed.

The session demonstrated three patterns:

1. **Pre-flight grounding paid off cleanly.** Three
   verification questions (does `clients/betfair_client/v1/`
   exist; `betfairlightweight` library mapping;
   import-linter constraints) all returned grounded answers
   that informed the brief without changing its shape. No
   surprises mid-drafting.

2. **Operator-driven framing refinement at job-statement
   stage was load-bearing.** Two refinements at Step 1
   (artefact-relationship — brief is the spec, not the
   amendment; scope-bundling — paper amendment + client
   implementation in one Code session, not split) shaped
   the entire brief. Catching these at job-statement stage
   rather than mid-drafting is exactly the discipline the
   skill's Step 1 is for.

3. **Call-driven surfacing held cleanly through end-to-end
   drafting.** Sections with no operator-relevant calls (§2,
   §3, §4, §6 implementation mapping, §7 test scope, §8
   sequencing, §9 verification, §10 output spec, §11 hard
   limits, §12 forward routing, §13 cross-references) were
   drafted silently. Operator-relevant calls surfaced at the
   end of drafting, batched for one-pass review.

## What was delivered

This session produced one canonical artefact and one
ephemeral artefact:

**Locked brief — `dr029/w4_bet_entry/v1_2_contract_addition_brief.md`**
(676 lines, SHA256 prefix `510cbfbf...88054715`). Single
artefact specifying:

- Contract amendment scope (§5.1–§5.5 of brief): new contract
  §9.6 `get_account_funds`; new contract §9.7
  `get_market_catalogue`; narrowed contract §15.4 (account
  management out of scope) to carve out `getAccountFunds`;
  appended contract §6 version history entry; cross-reference
  housekeeping.
- Implementation scope (§6.1–§6.4 of brief): new
  `account_funds.py`; new `market_catalogue.py`;
  `__init__.py` exports; library re-verification check.
- Test scope (§7.1–§7.2 of brief): new `test_account_funds.py`
  (8 cases minimum); new `test_market_catalogue.py` (12 cases
  minimum); 20-test floor confirmed.
- Sequencing (§8 of brief): two-phase, contract-first then
  implementation, with Phase 1 lock as canonical-truth
  boundary.
- Hard limits (§11 of brief): contract-as-canonical-mid-
  session enforced; no edits outside named anchors; no git
  operations; no real Betfair API calls; single bounded
  session.
- Output spec (§10 of brief): single report at
  `dr029/w4_bet_entry/v1_2_contract_addition_report.md`,
  300–500 line target.

**Code prompt** (rendered to chat, not on disk). Hard-wrapped
~70 chars per Cat 1. Contains job statement, working
environment, phase structure, key hard limits, output spec,
and what-not-to-do. Operator pasted into a fresh Claude Code
session to commission execution against the brief.

**No edits to canonical-truth files in this session.** No
edits to `decisions.md`, `architecture.md`, `governance.md`,
`standing_instructions.md`, `vision.md`,
`v3_data_requirements.md`, `project_context.md`. The brief is
new content in the `dr029/w4_bet_entry/` arc folder and does
not require Project knowledge base re-upload (knowledge base
holds canonical-truth files only).

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-030,
  DR-031, DR-021 named at open; DR-032 surfaced mid-session
  as load-bearing for §5.2 / §6.2 / §7.2 of the brief.
  DR-029 named as the closed gating arc.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight
  recap delivered at 23-min gap.
- **Cat 1 (V3 build picture conditional render)** — rendered
  at open (Session 93 close moved W4 to `done`). Not updated
  at this close (W4 still `done`, drops at Session 95 close
  per carry-rule). See Step 6 of close-ritual.
- **Cat 1 (open-items delta)** — skip-silent at open (23-min
  gap, no movement).
- **Cat 1 (drift-check)** — done at open, all three checks
  matched.
- **Cat 1 (silent session-open ritual)** — held. Steps 1–5
  silent; Steps 6–8 combined into single brief output.
- **Cat 1 (silent session-close ritual)** — holding this
  close. Steps 1–10 silent; Step 11 produces brief
  verification line.
- **Cat 1 (call-driven surfacing)** — held throughout.
  End-to-end drafting per operator request after §1 surfacing
  went well; operator-relevant calls batched for one-pass
  review at end. Sections with no operator-relevant call
  drafted silently.
- **Cat 1 (short responses, plain language)** — held
  throughout. DR numbers cited with bracketed reminders;
  technical terms unwound (`marketCatalogue`, `betfairlight-
  weight`, `RunnerCatalogue.metadata`, etc.).
- **Cat 1 (decision-maker framing)** — held. Each decision
  point led with the call or recommendation; reasoning
  followed.
- **Cat 1 (don't drift to alternatives when operator clear)**
  — held. Operator's "draft end-to-end" instruction at §2
  acted on cleanly without offering alternative cadences.
- **Cat 1 (escalate to detail only when warranted)** — held.
  Pre-flight grounding section escalated to library-shape
  detail only because the surface-mapping decisions are
  Claude's calls per Cat 5.
- **Cat 1 (line-break rendering for review content)** — held.
  Code prompt rendered hard-wrapped at ~70 chars per Cat 1.
- **Cat 1 (default to luddite-analyst-gambler brevity)** —
  held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close
  anchored. No pause-and-resume mid-session.
- **Cat 2 (pre-flight directory listing)** — done at open and
  again at close (Step 2 of close ritual).
- **Cat 2 (Desktop Commander default)** — held. All file ops
  via `Desktop Commander:read_file`,
  `Desktop Commander:list_directory`,
  `Desktop Commander:start_process` (date / wc / grep / shasum),
  `Desktop Commander:write_file` (brief drafted in chunks),
  `Desktop Commander:edit_block` (three single-target edits
  for the `event_time_zone` rename).
- **Cat 2 (REPL discipline)** — held. The library surface
  verification used single-line `python -c` invocations via
  `start_process`, not multi-line REPL.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)** —
  held and exercised. One incident: tried generic
  `str_replace` for the first `event_time_zone` edit; got
  "File not found" error; switched to
  `Desktop Commander:edit_block` per Cat 3 namespace rule.
  Operationally confirms the standing instruction at Cat 3.
- **Cat 2 (dry-run multi-target mechanical edits)** — n/a;
  three single-target `edit_block` edits, each with literal
  `old_string` / `new_string`.
- **Cat 2 (persist drafted artefact content to scratch)** —
  n/a; brief was drafted directly to canonical artefact and
  locked in-session, no scratch carry needed.
- **Cat 2 (surface structural-drift in session record)** —
  n/a; no governance artefact structure changed this session.
- **Cat 3 (`bash_tool` non-functional)** — held. Test at open
  showed `bash_tool` returned a result (against expectation);
  re-verified via Desktop Commander; subsequent ops all via
  Desktop Commander.
- **Cat 3 (external API resources reach-for)** — exercised
  via direct `betfairlightweight` library introspection in
  the v3 venv. Caught both endpoint signatures, return
  shapes, and the `selection_id: int` library convention.
- **Cat 4 (DR-027/028 invoked)** — named at open. DR-027/028
  framing surfaced in §13 cross-references of brief
  (operational-line-only framing).
- **Cat 4 (operational/analytical line discipline)** — held.
  Brief explicitly frames new surfaces as operational-line
  per §13 cross-references.
- **Cat 4 (single-cycle analysis discipline)** — n/a this
  session.
- **Cat 4 (Betfair as canonical source)** — load-bearing for
  §5.2 / §6.2 of the brief (Set B field requirements per
  DR-032 §4 — Betfair `marketCatalogue` is the canonical
  source for runner names, event identity, venue).
- **Cat 5 (software questions are Claude's)** — held
  throughout. Pydantic shape design, library mapping, test
  scope, sequencing — all Claude's calls. Operator surfaced
  only operationally-shaped questions (wallet behaviour,
  account-management framing, Strategy 4 metadata
  consideration).

## Session-94-specific reflections

- **Brief-drafting skill ran cleanly end-to-end.** All eight
  steps fired; pre-flight grounding (Step 2) returned
  grounded answers without surprises; structural-shape lock
  (Step 3) anchored on a documented hybrid (mini-build with
  paired contract amendment) rather than forcing a precedent
  fit. Pattern for future hybrid briefs: name the shape
  explicitly when no clean precedent applies, rather than
  pretending one of the existing precedents fits.

- **Operator-driven framing refinements at job-statement
  stage are high-leverage.** The two Step-1 refinements
  (artefact-relationship; scope-bundling) shaped the entire
  brief. Worth holding for future brief-drafting sessions:
  the job statement is a contract between operator and
  Claude before drafting begins, and the operator's
  refinements at that stage are cheap to apply and expensive
  to apply mid-drafting.

- **End-to-end drafting after §1 went well is a valid cadence
  variant.** Standing instruction's section-by-section default
  applies, but when the operator confirms the framing is
  right at §1 surfacing, end-to-end drafting with batched
  operator-relevant-call surfacing at the end is also valid.
  Pattern: operator opt-in to end-to-end after §1 confirms
  shape; otherwise default to section-by-section.

- **`bash_tool` returned a result at open.** Standing
  instruction Cat 3 says `bash_tool` is non-functional in
  this environment. At open, Step 1's timestamp anchor via
  `bash_tool` returned a valid timestamp. Re-verified via
  Desktop Commander as the canonical tool per Cat 3. Worth
  flagging: the `bash_tool` non-functional rule may be
  environment-specific or version-specific; standing
  instruction reads as universal. Not gating; Desktop
  Commander remains the canonical tool. Logged as a
  carry-forward item for next sweep — possibly the rule
  needs softening to "prefer Desktop Commander; `bash_tool`
  may work in some environments but is unreliable" rather
  than "non-functional".

- **Library introspection in v3 venv is high-signal pre-
  flight.** The `betfairlightweight` library shape was
  captured directly via `inspect.signature` and
  `inspect.getsource` calls, surfacing surface-API details
  (parameter defaults, return-shape attributes,
  `time_zone` rename) that grounded the brief's mapping
  table. Pattern for future contract-amendment briefs: when
  the contract surface maps to a Python library, introspect
  the library directly rather than assuming documentation.

- **`str_replace` namespace gotcha exercised.** First edit
  of `event_timezone` → `event_time_zone` used generic
  `str_replace` (the namespace-mismatched tool); got "File
  not found"; switched to `Desktop Commander:edit_block`.
  Confirms the existing Cat 3 standing instruction. The
  carry-forward to absorb this into Cat 3 alongside the
  `create_file` vs `write_file` note is now substrate-
  confirmed (Session 82 originally, exercised again here).

## Open items in (carried forward)

New from Session 94:

- **`betfair_client` v1.2 contract addition Code report
  awaiting triage.** Code execution commenced this session
  against `dr029/w4_bet_entry/v1_2_contract_addition_brief.md`
  (676 lines, SHA256 `510cbfbf...88054715`). Report expected
  at `dr029/w4_bet_entry/v1_2_contract_addition_report.md`
  (300–500 lines per brief §10). Session 95 reads the report
  and triages — same shape as Session 93's W4 report triage.
- **`bash_tool` standing-instruction softening candidate.**
  Cat 3 currently says `bash_tool` is non-functional;
  Session 94 open showed it returned a valid timestamp.
  Possible Cat 3 amendment at next standing-instructions
  sweep: change "non-functional" to "unreliable; prefer
  Desktop Commander". Not gating.
- **`str_replace` namespace gotcha substrate confirmed.**
  Exercised again this session (Session 82 originally).
  Cat 3 absorption candidate at next sweep — alongside
  `create_file` vs `write_file` note.

Carry-forward from Session 93 (status):

- **W4 follow-up Code brief — small.** Pairs §7.4
  (`streaming_blocked` reclassification) and §7.6
  (`soft_book_combined_price` NULL for single-leg). Did not
  draft this session; Session 95 if budget allows alongside
  v1.2 report triage, else Session 96.
- **v3 composition-root structural decision.** Sequenced
  Session 95 per Session 93 close. Session 95 may run this
  alongside v1.2 report triage if scope allows, else stays
  sequenced.
- **Real `BetfairAdapter` implementation brief.** Sequenced
  Session 96+. Substantively unblocked by v1.2 once Code's
  report locks the v1.2 surface.
- **W4 brief amendment sweep.** Cosmetic; deferred. Session
  93 close-out items unchanged.
- **Math review §6 arithmetic-step explicit update.**
  Cosmetic; deferred.
- **W6 broader sync reconciliation — `listClearedOrders` or
  similar.** §8.6 carry. Routes to W6 brief drafting.
- **Brief / contract `placeOrders` vs `place_bet` naming
  alignment.** §8.4 carry. Cosmetic.
- **W4 brief locked at 2121 lines** — unchanged.
- **Storage-interface stub spec carry to W6 brief drafting**
  — unchanged.
- **§12.2 four-modules-vs-support-files clarification as
  `standing_instructions.md` candidate** — unchanged.
- **Brief-length-estimate calibration as Cat-5 candidate** —
  unchanged.
- **Round 13 workflow-ordering-validation pattern as Cat 4
  candidate** — unchanged.
- **DR-032 locked.** Drove §5.2 / §6.2 / §7.2 of v1.2 brief.
- **`architecture.md` §A.10 written.** Unchanged.
- **Cross-reference integrity gap** — unchanged.
- **Legacy `§D12` reference cleanup** — unchanged.
- **Cat 4 paragraph re: "pending architectural extension
  (Session 42)" stale** — unchanged.
- **Hedge-staking math review locked at 1942 lines** —
  unchanged.
- **Substrate revision flag for W4 brief drafting** —
  unchanged.
- **Effective-odds synthesis as racing-screen → modal flow** —
  unchanged.
- **Default free-bet conversion rate 65%; operator-
  configurable** — unchanged.
- **Manual stake override as future refinement** — unchanged.
- **Multi-rung ladder hedge as future arc** — unchanged.
- **`EX_LADDER` operator-side homework parked** — unchanged.
- **W4 substrate decisions captured Session 87** — unchanged.
- **F5 strategy_tag carry forward** — unchanged.
- **Streaming envelope vocabulary carry-forward** —
  unchanged.
- **Manual free-bet ledger entry workflow** — unchanged.
- **Deployment-substrate items (F2, F3, F4)** — unchanged.
- **F6 carry-forward to Fix 4 brief + W3+ briefs** —
  unchanged.
- **§12 self-assessment item 3 — audit-log durable substrate
  selection** — unchanged.
- **W1 F2 sharpening (Thoroughbred / Harness label
  conflation)** — unchanged.
- **W1 F1 accepted as v1.0 conflation** — unchanged.
- **W0 F2 brief-language carry** — unchanged.
- **DR-030 "18 months" reference correction** — unchanged.
- **`governance.md` §4 deferred-capability reconciliation** —
  unchanged.
- **Jump-anchor design reframe** — unchanged.
- **Post-DR-029-close contract documentation relocation** —
  empty `bethub-v3/contracts/` folder confirmed; relocation
  remains deferred. Session 94 explicitly excluded relocation
  from v1.2 scope.
- **Sports-side dead-heat capture in `architecture.md`
  §B.1.4** — unchanged.
- **Past-settlement-window threshold calibration** —
  unchanged.
- **Settlement worker periodic verification cadence** —
  unchanged.
- **Cluster 1 surgical-fix carry-in** — unchanged.
- **Fix 9 / Fix 10 / three-row collision triage / low-
  confidence match review** — unchanged.
- **Complete cascade map** — unchanged.
- **CLV as analytical-layer signal** — unchanged.
- **Path-(iii) reconciliation-job scheduling** — unchanged.
- **§2.9 §4.4 six edge cases** — unchanged.
- **All other carry-forward items from Session 93
  unchanged.**

## Open items out (closed this session)

- **`betfair_client` v1.2 contract addition brief drafting**
  (Session 93 carry-forward) — **closed.** Brief drafted
  end-to-end and locked in-session at
  `dr029/w4_bet_entry/v1_2_contract_addition_brief.md` (676
  lines, SHA256 `510cbfbf...88054715`). Code execution
  commenced this session.
- **W4 stream — one-session `done` carry expired.** Stream
  drops from `v3_build_picture.md` at this close per
  `done` carry-rule.

## Session close state

- **Rebuild folder root:** unchanged this session. No edits
  to root-level governance files.
- **`current_state.md`:** updated at close — "Last updated"
  → `2026-05-07 08:26 ACST`; "Where we are" → v1.2 brief
  drafted and locked, Code execution commenced; "What's
  next" → Session 95 triages Code's v1.2 report; required
  reads adjusted for Session 95.
- **`v3_build_picture.md`:** updated at close — W4 stream
  drops per one-session `done` carry-rule expired this
  close. No other stream movement; "Last updated" stamp
  bumped to close timestamp.
- **`standing_instructions.md`:** unchanged this session.
  Three sweep candidates accumulated: (a) `bash_tool`
  softening; (b) `str_replace` namespace gotcha as Cat 3
  absorption alongside `create_file` vs `write_file` note;
  (c) end-to-end-drafting-cadence-after-§1-confirmation as
  Cat 1 candidate. Plus existing carry-forward sweep
  candidates from Sessions 91 / 92 / 93. Sweep deferred to
  fresh-mind session.
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session.
- **`decisions.md`:** unchanged this session.
- **`dr029/w4_bet_entry/`:**
  - `hedge_staking_math.md` — unchanged.
  - `w4_bet_entry_brief.md` — unchanged. Brief amendment
    sweep deferred.
  - `w4_bet_entry_report.md` — unchanged. Read this session
    for §8.1 + §8.2 substrate.
  - `_drafts/SESSION_91_substrate.md` — unchanged.
  - **`v1_2_contract_addition_brief.md` — new this session,
    locked at 676 lines.**
  - `v1_2_contract_addition_report.md` — expected from Code,
    not yet on disk at close (Code execution running in
    parallel chat).
- **`sessions/`:** Session 94 record written by close ritual
  (this file).
- **`.close_out_backups/`:** Session 94 opening prompt
  removed at close; Session 95 opening prompt written.
- **Project knowledge base:** unchanged. No re-upload
  required this session (no edits to knowledge-base files).
- **VPS state:** unchanged this session. No VPS calls.
- **`bethub-v3/`:** unchanged in canonical-state at session
  close. Code may have modified files during execution
  (running in parallel chat); state at next session open
  reflects whatever Code shipped. The seven expected
  modifications named in brief §9 final-state-check are the
  scope of any changes.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 95 opens fresh
chat. Primary deliverable is **read and triage the
`betfair_client` v1.2 contract addition Code report** at
`dr029/w4_bet_entry/v1_2_contract_addition_report.md`. Same
shape as Session 93's W4 report triage:

1. Read the report end-to-end.
2. Walk Open Questions one decision per round per Cat 1.
3. Walk Findings with operator-confirmed batching cadence.
4. Resolve forward routing.

**Pairs naturally same session if budget allows:** small W4
follow-up Code brief covering §7.4 (`streaming_blocked`
reclassification + new `ErrorContext.error_kind` value) and
§7.6 (`soft_book_combined_price` NULL for single-leg).
Narrow scope; <300-line brief expected. Carried from Session
93.

**Sequence after Session 95:**

- **Session 96:** real `BetfairAdapter` implementation brief
  drafting (substantively unblocked by v1.2). May absorb v3
  composition-root structural decision (fresh DR or DR-030
  addendum) if the adapter brief surfaces it as a load-
  bearing prerequisite.
- **Session 96 alt:** v3 composition-root structural
  decision drafted standalone before adapter brief. Either
  ordering works; depends on what Session 95 triage
  surfaces.
- **W5 brief drafting:** can open whenever. Could parallelise
  with adapter / composition-root work.

**Out of scope for Session 95:**

- Composition-root structural decision drafting — sequenced
  Session 96 unless Session 95 triage routes otherwise.
- Real `BetfairAdapter` implementation brief drafting —
  sequenced Session 96+.
- Standing-instructions sweep — deferred to fresh-mind
  session.

**Operator-side actions between sessions:**

- **(Required)** review the v1.2 contract amendment for
  content fit. The amendment is the canonical spec going
  forward; the operator's between-session read is the right
  time to catch anything that didn't land cleanly.
- **(Optional)** review the v1.2 implementation files at
  `bethub-v3/clients/betfair_client/v1/account_funds.py` and
  `bethub-v3/clients/betfair_client/v1/market_catalogue.py`
  if curious about the shipped code.
- **(Optional)** run a real `get_account_funds()` call
  against the live Betfair API at low risk — funds reads are
  read-only, no exposure. Validates library-mapping
  end-to-end. Operator's call.
- **(Optional)** review the v1.2 report end-to-end before
  the triage session.
- **(Lower priority)** Betfair API membership tier
  investigation; BetWatch response awaiting; review
  `bethub-analytical/README.md` activation timing.

## Close-out notes

Session 94 was a clean brief-drafting session. The brief-
drafting skill ran end-to-end with no surprises; pre-flight
grounding paid off; operator-driven framing refinements at
job-statement stage shaped the brief's framing cleanly;
end-to-end drafting after §1 confirmation worked as a valid
cadence variant.

Three patterns from Session 94 worth holding onto:

- **Hybrid brief shapes are valid when no clean precedent
  fits.** The "mini-build with paired contract amendment"
  shape was novel for this project; naming the hybrid
  explicitly rather than forcing a precedent fit was the
  right move. Pattern for future brief-drafting sessions:
  when the existing precedent shapes (inspection /
  source-review / surgical-fix / probe) don't fit cleanly,
  name the hybrid and proceed.

- **Library introspection is high-signal pre-flight for
  contract-amendment briefs.** When a contract surface maps
  to a Python library, direct introspection in the v3 venv
  via `inspect.signature` and `inspect.getsource` produces
  grounded mapping tables that documentation alone wouldn't.
  Pattern: pre-flight grounding for contract-amendment briefs
  always includes library introspection when applicable.

- **End-to-end drafting after §1 confirmation is valid when
  operator opts in.** Standing instruction's section-by-
  section default applies, but when the operator confirms
  framing is right at §1 surfacing and explicitly requests
  end-to-end drafting, that's a valid cadence with batched
  operator-relevant-call surfacing at the end. Pattern:
  operator opt-in to end-to-end after §1 confirms shape;
  otherwise default to section-by-section.

v1.2 brief locked. Code execution commenced. Session 95 opens
fresh on triage of Code's v1.2 contract addition report.
