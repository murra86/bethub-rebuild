# Session 137 — W12 brief verification + architecture.md §A.5 edit + Code opening prompt draft

**Opened:** 2026-05-17 22:44 PDT (Vancouver — temporary
timezone display window active until 2026-06-08;
canonical project zone remains Adelaide per DR-021;
ACST equivalent 2026-05-18 15:14 ACST).
**Closed:** 2026-05-17 23:58 PDT (ACST equivalent
2026-05-18 16:28 ACST).
**Wall-clock active session:** ~74 minutes.
**Tool routing:** Claude Chat (verification, architecture
edits, prompt drafting); no Claude Code dispatch this
session — Code prompt locked for out-of-session
dispatch by operator post-close.
**Governing DRs invoked:** DR-019 (read-time derivation
discipline — primary governor for W12), DR-021
(timestamp anchoring — Vancouver display override
active), DR-022 (book/account vocabulary), DR-027/028
(two-DB boundary), DR-030 + S124 amendment (module-
boundary contracts), DR-032 (canonical bet-record /
bet-leg shape).

## Anchor

```
# Session-open command (Vancouver per temporary
# instruction):
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-05-17 22:44 PDT

# Session-close command:
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-05-17 23:58 PDT
```

## Pre-flight checks

Session-open ritual ran per `bethub-session-open`
skill. Required reads completed (`current_state.md`,
`standing_instructions.md`, `project_context.md`,
`SESSION_136.md`). Pre-flight directory listing
confirmed clean rebuild folder root — 14 .md files
plus openapi.json at root, no phantoms.
`.close_out_backups/` contained
`SESSION_137_opening_prompt.md` as expected from
S136's close.

**Drift-check (Step 5 of open ritual):** clean.

- (a) `current_state.md` "Last updated" 2026-05-17
  22:36 PDT matched `SESSION_136.md` "Closed:"
  timestamp.
- (b) `SESSION_136.md` present, non-empty (394 lines).
- (c) `v3_build_picture.md` "Last updated" still
  2026-05-17 13:49 ACST (S134 close) — correct, no
  stream movement at S136 close.

**Open-side anomaly:** operator flagged two error
messages during S136, including one during close-out.
Drift-check covered the close-out artefacts
specifically (`current_state.md`, `SESSION_136.md`,
`.close_out_backups/SESSION_137_opening_prompt.md`) —
all three read clean and cross-referenced
consistently. Mid-session a DC channel-test
(`echo "DC channel test S137 <ts>"`) confirmed
underlying tool calls were landing despite the
operator's UI surfacing MCP errors — the pattern
matches the S136 episode (UI error, tool lands).
No silent corruption surfaced in either the close-
out artefacts or the brief verification that
followed.

## Session shape

S137 was the verification-and-finalisation session
for the W12 brief. The plan from S136 close-out had
three deliverables in sequence: (1) verify S136
brief edits end-to-end as load-bearing first action
given the UI-error concern; (2) complete the
architecture.md §A.5 edit deferred from S136
(additive read/write asymmetry principle plus
amendments reflecting the single-flavour profit-
share model); (3) draft the Code opening prompt
with review-before-build shape mirroring the §6.1
halt rule. All three landed cleanly. Plus the
S133-report rename to free the canonical report
path for the new Code session.

The verification was thorough — mechanical pass
(line count, section sequence, structural greps,
positive checks on renamed methods and enum
swaps) followed by coherence pass (§3.1 read/write
asymmetry framing against derivation sections;
§5.1b cleanup against §5.4 / §5.5 profit-share
treatment). All clean. Three follow-up items
surfaced and resolved: (a) the S136-record's
"51 numbered sections" count was a record-side
counting drift, actual is 49 with all sequence
groups complete; (b) `funding_source` 22 matches
all sat in allowed zones (§1.1 / §5.1b / §5.9 /
§6.2 / §9.2); (c) the `"insurance trigger"` label
is present at the §5.6 derivation and §7.3 test
scenario, an initial regex was line-wrap-blind.

The architecture edit landed in seven surgical
`edit_block` calls. Verification grep post-edit:
zero matches for `tim_direct` and
`account_holder_cash_holding`; one
`funding_source` match remained at L313 but in
§A.4 (promo and credit chains) — an unrelated
concept (the `promo_cash_credited` payload's
funding_source field), out of scope for §A.5
cleanup.

## What was delivered

**1. W12 brief verification — load-bearing first
action, clean.**

Brief at `dr029/w12_balances/w12_balances_brief.md`,
3,466 lines (within the expected 3,450-3,480 range).
Verification pass via two scripts written to `/tmp`
and executed via `Desktop Commander:start_process`:

- `/tmp/w12_brief_verify.py` — mechanical baseline
  (line count, §5.* sequence, structural greps for
  banned patterns, positive checks for renamed
  methods + enum swaps).
- `/tmp/w12_brief_verify2.py` — follow-up
  investigation (all-numbered-headers inventory,
  `funding_source` zone mapping, `"insurance
  trigger"` variant search).

Mechanical checks (all passed):

- Section sequence §5.1 → §5.1b → §5.2 → §5.3 →
  ... → §5.10 unbroken; §5.1b at L668-L777 = exactly
  110 lines as expected.
- Total numbered section headers: 49 (S136 record
  said "51" — counting drift in the session record,
  not a real drop; all sequence groups complete).
- Banned-pattern greps zero matches:
  `INSURANCE_TRIGGER`, `create_promo_template`,
  `create_warning_catalogue_entry`,
  `list_promo_templates`,
  `list_warning_catalogue_entries`,
  `get_warning_catalogue_entry`,
  `get_promo_template`.
- Renamed adapter methods all present:
  `create_template`, `create_warning_type`,
  `list_templates`, `list_warning_types`,
  `get_template`, `get_warning_type`.
- Enum swap: `FREEBIE` present (6 matches),
  `TRIGGERED` present (4 matches),
  `credit_source_label = "goodwill"` present.
- Zone-constrained: `funding_source` 22 matches
  all in allowed zones (§1.1 cross-ref ×4, §5.1b
  body ×9, §5.9 ×2, §6.2 ×3, §9.2 ×4);
  `tim_direct` and `account_holder_cash_holding`
  exclusively inside §5.1b cleanup discussion.
- `"insurance trigger"` label present at L1358
  (§5.6 derivation algorithm:
  `INSURANCE → "insurance trigger"`) and L2524
  (§7.3 test scenario verification).

Coherence pass (read-through of §3.1, §5.1b, §5.4,
§5.5):

- §3.1 read/write asymmetry sub-section reads
  coherently — three named obligations on SQL
  drops (name path inline, replicate adapter-side
  logic with DR-019 state-on-row semantics for
  entity tables / supersession discipline for
  event tables, surface verification in ship
  report). Forward-references architecture.md §A.5
  appropriately (the edit S137 then completed).
- §5.1b body well-formed — edit anchors tight
  (five files named), test impact specified (three
  test files plus parameterisation-collapse note,
  ±5 test count tolerance), hard limit explicit.
  Critical division-of-labour statement: "Code
  does not edit `architecture.md`. The
  architecture doc revision is already in effect
  when Code reads it as part of the §3.2 required
  reads" — locks the S137 architecture edit as
  prerequisite.
- §5.4 (Location 2 derivation) algorithm fully
  consistent with §5.1b single-flavour model —
  `profit_share_distribution` subtracts from
  parked-pool with explicit "holder's bank IS the
  parked pool" rationale, no `funding_source`
  conditional. Per-bookmaker softening present
  with W12.1+ flag.
- §5.5 (operation net-flow) bank-touching event
  list correctly excludes
  `profit_share_distribution`; algorithm iterates
  only over `account_holder_funding`,
  `account_holder_remittance`, `external_payment`.
  `external_payments_total` field present on
  output model per S136 COGS-equivalent framing.

**Outcome:** no silent corruption from the S136 UI
errors. Brief is verified clean and ready for Code
dispatch.

**2. Architecture.md §A.5 edit — seven surgical
`edit_block` calls, clean.**

§A.5 ran L334-L413 (80 lines) pre-edit; now L334-L424
(91 lines) post-edit. Net +12 lines (architecture.md
828 → 840 total lines). Each `edit_block` well under
the 30-line empirical ceiling per the S124-S125
lesson.

Edits in §A.5 order:

- **Edit 1 (NEW, ~14 lines):** Read/write asymmetry
  project-level design principle sub-section at top
  of §A.5. Three bullets: writes go through typed
  adapter; reads default to adapter and SQL drops
  are named exceptions, adapter-first is default
  for future workstreams; SQL drops replicate
  adapter-side business logic explicitly with
  comment at drop site and surface in ship report.
- **Edit 2 (AMEND):** Bank-touching event table
  row: `profit_share_distribution` "Conditional" →
  "No", explanation rewritten to internal ledger
  reallocation with explicit "holder's bank IS the
  parked pool" framing.
- **Edit 3 (AMEND):** Post-table prose paragraph:
  dropped the `funding_source` qualification
  language; restated as never-bank-touching under
  the clarified model.
- **Edit 4 (AMEND):** Location 2 formula bullet:
  `− Sum(profit_share_distribution where
  account_holder_id = X AND funding_source =
  account_holder_cash_holding)` → `− Sum(...
  where account_holder_id = X)`. Single conditional
  dropped.
- **Edit 5 (NEW, ~4 lines):** Per-account-holder
  Location 2 framing note inserted after the
  formula block — names the per-holder primitive
  and notes a per-bookmaker cross-account view is
  surfaceable as a separate informational read
  (W12.1+ refinement, not part of core
  derivation).
- **Edit 6 (AMEND):** Profit-share semantics
  paragraph + worked example rewritten to the
  ledger-reallocation framing. New opening
  paragraph explains the holder's-bank-IS-parked-
  pool model. Worked example ($1,500 + $200
  profit share) shows the $200 sitting in the
  holder's bank getting reallocated from
  operational capital to holder's own funds; no
  physical movement; net cash-holding $1,300 with
  the remaining $200 accruing to the holder
  personally.
- **Edit 7 (AMEND):** Operation-net-flow formula:
  dropped the `− sum(profit_share_distribution
  where funding_source = 'tim_direct')` term;
  "four bank-touching event types" → "three".

**Verification grep post-edit (architecture.md):**

- `tim_direct`: 0 matches ✓
- `account_holder_cash_holding`: 0 matches ✓
- `funding_source`: 1 match at L313 — in §A.4
  (promo and credit chains), referring to the
  `promo_cash_credited` payload's `funding_source`
  field (a different concept — always book-side
  credit). Out of scope for §A.5 cleanup;
  untouched by design.
- `profit_share_distribution`: 7 mentions, all in
  expected contexts (event-log inventory in §A.2
  at L99/L134, plus five edit sites in §A.5).

**3. Code session opening prompt drafted and
written.**

Path: `dr029/w12_balances/code_session_opening_prompt.md`.
116 lines on disk after three chunked writes (32 +
33 + 54). Per pre-execution risk advisory: each
chunk under the 50-line append threshold from S130;
the third chunk was 54 lines (slightly over the
conservative ceiling) but landed cleanly. Reviewed
inline with operator and confirmed before write.

Prompt shape (review-before-build, per S134
operator instruction):

- Required reads in order — brief, architecture.md
  §A.5 (with explicit one-paragraph reminder of
  the clarified profit-share model since that's
  the load-bearing context shift since S133),
  `current_state.md`, `standing_instructions.md`,
  `governance.md`, `decisions.md` (named DRs).
- Load-bearing first action: brief §6.1 alignment
  check (all seven checks A-G, plus operator-
  amplified judgement extension for H+). ANY
  alignment-finding halts substantive edits; Code
  reports, operator-Claude triages next session.
- Substantive build (only on clean alignment):
  §6.1 → step zeros §5.1 + §5.1b → derivation
  sections §5.3-§5.8 → §5.9 module structure +
  lint-imports → §5.10 tests.
- Hard limits enumerated (§9.2, §9.4, §9.5, §9.7,
  §9.8 highlighted as load-bearing).
- Output spec: ship report at `w12_balances_report.md`,
  test count baseline 753 with ±5 variance
  threshold for finding-surface.
- Tool routing, codebase paths, halt discipline.

**4. S133 report rename — preserved history, freed
canonical path.**

`dr029/w12_balances/w12_balances_report.md` (the
S133 alignment-halt report, 1,187 lines, 53 KB
content fully triaged into post-S134 brief
revisions) renamed to
`w12_balances_s133_alignment_report.md`. The new
Code session writes its ship report to the now-
free canonical `w12_balances_report.md` path.
Preserves the S133 historical record without
crowding the canonical path; aligns with the
standing rule that reports are governance/reference
material, not clutter (Cat 2).

## Standing-instruction adherence check

- **Cat 1 silent open-ritual ritual — VIOLATED.**
  Narrated "Step 1 — Timestamp anchor" and "Step 2 —
  Required reads in order" as headers during the
  S137 open. Cat 1 instruction is explicit on zero
  step-by-step narration; the same drift pattern
  held clean at S135 and S136 (the 2-of-11
  consecutive-clean streak). Self-flagged in the
  orientation summary; streak broken. Now 3-of-13
  broken instances (was 2-of-11 entering S137).
  Promotion-to-encoded-rule candidacy weakens.
- **Cat 1: Tool routing always stated** — honoured
  (Chat for verification + edits + prompt drafting,
  Code for the W12 build per the drafted prompt).
- **Cat 1: Plain-language operator-call framing** —
  honoured. Operator-direction calls (the three
  wording-mattering chunks for review; the S133-
  report rename) used plain language framing.
- **Cat 1: Brief drafting — strategic decisions
  only, autonomous on technical** — honoured.
  Architecture edit surfaced only the three
  wording-mattering chunks (read/write asymmetry
  sub-section, per-holder framing note, profit-
  share semantics + worked example rewrite); the
  four mechanical edits (table row, post-table
  prose, formula simplifications) handled
  autonomously. Code prompt drafted with
  structural shape surfaced for confirmation;
  technical detail (anchor specifics, lint-imports
  contract pointers, output format) handled
  autonomously.
- **Cat 1: Fenced block 60-70 char line wraps** —
  honoured throughout review blocks (architecture
  edit fenced display, Code prompt fenced
  display). Artefact-internal prose follows
  artefact-internal convention (architecture.md
  uses wider wraps; the Code prompt and brief use
  60-70 char wraps internally).
- **Cat 1: Drive sync auto-enabled — no prompt** —
  honoured.
- **Cat 1: Unwind shorthand with bracketed
  reminders** — honoured throughout operator-
  facing conversational text.
- **Cat 1: "No draft text unless it earns
  operator time" (S136 tightening)** — exercised
  positively. Showed three wording-mattering
  chunks (architecture edit) and the full Code
  prompt (substantial fresh artefact warranting
  full review); handled mechanical edits and
  follow-up verification investigation silently.
  Promotion candidate strengthens.
- **Cat 2: Session-close opening prompt produced**
  — honoured (Step 8 of close ritual).
- **Cat 2: Pre-execution risk advisory** — honoured.
  Pre-flagged chunking for the Code prompt write
  (~116 lines → three chunks); pre-flagged the
  30-line `edit_block` ceiling for the seven §A.5
  edits.
- **Cat 3: Empirical verification before editing
  governance artefacts** — honoured. Re-read §A.5
  live before drafting the seven `edit_block`
  calls; re-read the Code prompt from disk after
  write to confirm content for inline display.
- **Cat 3: `write_file` chunking discipline** —
  honoured. Six total file writes this session
  (SESSION_137.md chunks + Code prompt chunks +
  this session record); chunks ranged 32-92 lines.
  The 92-line append chunk landed cleanly,
  reinforcing the S130 empirical tolerance for
  append mode (60-180 lines reliable).
- **Cat 3: Live database queries via Desktop
  Commander start_process with Python** — N/A
  this session (no DB reads).
- **Cat 4: Divergence-capture-or-fix elevation** —
  exercised positively. Three follow-up
  divergences captured at first surfacing during
  brief verification (49-vs-51 section count,
  funding_source zone mapping, "insurance trigger"
  label false-negative); all investigated and
  resolved in-line before declaring verification
  complete. Sensitivity strengthens further.
- **Cat 5: Make software calls; don't punt them**
  — honoured. Two routing calls made autonomously:
  (a) whether to read a prior S133 Code-prompt
  artefact for shape reference (turned out none
  was committed to disk; drafted from scratch);
  (b) the S133-report rename vs overwrite call
  (chose rename to preserve history while freeing
  canonical path).

## Open items in

- **W12 dispatch to Claude Code (out-of-session).**
  Operator copy-pastes
  `dr029/w12_balances/code_session_opening_prompt.md`
  into a fresh Claude Code window after S137 close.
  Code executes against the locked brief in a
  single bounded session, halts on any alignment-
  finding, ships a report to
  `dr029/w12_balances/w12_balances_report.md`.
- **S138 triages Code's W12 report.** Loop closes
  on Code's ship-or-halt outcome. Three forward-
  routing branches per S136 plan:
  - Code reviews + ships clean → S139 drafts W15
    brief (operations log per-domain event log).
  - Code surfaces fresh alignment finding → S139
    returns to brief-revision pattern (W12
    additional iteration).
  - Code ships with W12.1 residual → S139 drafts
    W12.1 surgical-fix brief.
- **Vancouver timezone instruction.** Active
  through 2026-06-08; revert to Adelaide anchors
  at first session open on or after that date.
  Carried in `current_state.md` top.

## Open items out

- **Brief verification (S136 open item)** —
  resolved clean. Brief at 3,466 lines, all
  structural and coherence checks passed. No silent
  corruption from S136 UI errors.
- **Architecture.md §A.5 edit (S136 open item)** —
  resolved. Seven `edit_block` calls landed cleanly;
  verification grep clean for the §A.5 cleanup
  scope.
- **Code opening prompt draft (S136 open item)** —
  resolved. Prompt at canonical path; reviewed and
  approved by operator; ready for out-of-session
  Code dispatch.

## Carried forward

All sensitivity items from S136 carry. New
sensitivity:

- **Cat 1 silent open-ritual narration drift** —
  reset. Was 2-of-11 consecutive-clean (S135 + S136
  held); now 3-of-13 broken instances (S137 broke).
  Promotion-to-encoded-rule candidacy weakens.
  Re-establishing the streak is the next-session
  watch.
- **Cat 1 build-picture conditional render** — 17
  consecutive clean applications S120-S137. S137
  open skip was correct (no stream movement at
  S136 close). Strengthening.
- **Cat 1 "no draft text unless it earns operator
  time" (S136 addition)** — second positive
  instance. Exercised at the §A.5 edit (showed three
  wording-mattering chunks, handled mechanical
  edits autonomously). Promotion candidate
  strengthens.
- **Cat 3 pre-execution risk advisory** — exercised
  twice this session (chunking for Code prompt
  write, 30-line ceiling for `edit_block` sequencing
  on §A.5). Promotion candidate continues
  strengthening.
- **Cat 3 `write_file` mode='append' empirical
  tolerance refinement (S130 addition)** — heavily
  exercised this session. Append chunks of 33, 54,
  68, 92, 117, 123 lines all landed cleanly. The
  60-180 line empirical tolerance holds.
- **Cat 4 divergence-capture-or-fix elevation** —
  strengthening. Three captures-at-first-surfacing
  this session during brief verification, all
  resolved before declaring verification complete.

## Carry-forward operational (long-standing)

- Settings-area cadence follow-up brief — open;
  waits on operational experience.
- Greyhound operational constraint verification —
  open.
- `betfair_adapter.py` single-file mypy cleanup —
  low priority.
- `cascaded_at_settlement_state` closed-enum
  revisit — forward-tracked for W8 brief drafting.
- Hedge classification (DR-025, Finding #8 S123)
  — revisit scoped before W15; carries through W12
  shipped.
- §2.4 Fix 4 cadence design dependency (Finding
  #3 S123) — carries.
- Alembic adoption — sequenced after W12 + W15.
  Touched at S136 / S137 in the §5.1b orphan-
  column note (column-drop migration out of W12
  scope).
- (Optional) real `get_account_funds()` call
  against live Betfair API at low risk.
- (Lower priority) Betfair API membership tier
  investigation — awaiting BetWatch response.
- (W12.1 or later refinement) per-bookmaker
  cross-account spot-check view.

## Session close state

- **Rebuild folder root:** clean, 14 .md files
  plus openapi.json. No phantom files. Vancouver
  timezone instruction carried at top of
  `current_state.md`.
- **WIP:** None — all session deliverables
  committed. `w12_balances_brief.md` at 3,466
  lines (verified). `architecture.md` at 840
  lines (post §A.5 edit). Code prompt at 116
  lines on disk.
- **`.close_out_backups/`:** to contain
  `SESSION_138_opening_prompt.md` after sweep
  removes the now-stale
  `SESSION_137_opening_prompt.md`.
- **`sessions/`:** this file
  (`SESSION_137.md`) being written.
- **Project knowledge base:** no upload action
  required — `standing_instructions.md` unchanged
  this session (Drive auto-sync handles routine
  edits; no instruction-file changes here).

## Forward routing

**Confirmed with operator** — S138 triages Code's
W12 report after Code completes its out-of-session
single-bounded run against the locked brief. Three
branches per the routing table above.

S138 opening prompt (Step 8 of close) carries the
forward-routing branches explicitly so the next
operator-Claude session knows the expected outcome
shapes before reading the report.

## Close-out notes

S137 was a tightly-scoped, well-bounded session:
verification (load-bearing first action, clean),
architecture edit (seven surgical `edit_block`
calls, clean), Code prompt draft (committed at
canonical path), S133-report rename (preserves
history). ~74 minutes wall-clock — under the
3-hour split threshold by a comfortable margin.

Two operational notes worth carrying:

- The Cat 1 silent open-ritual broke at this open.
  Self-flagged in the orientation summary; not a
  governance event but worth noting for the
  promotion-candidate tracker.
- The S136 UI-error-during-edit concern is now
  resolved as a non-event at the brief level —
  verification surfaced no silent corruption. If
  a third instance surfaces in future sessions,
  the background-process investigation flagged at
  S136 close-out remains the right next step
  (AdsPower, Drive sync, editor processes touching
  the rebuild folder during active edits).
