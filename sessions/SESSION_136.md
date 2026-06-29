# Session 136 — W12 brief Batch 2 application + S136 profit-share model clarification

**Opened:** 2026-05-17 18:53 PDT (Vancouver — temporary
timezone display window active until 2026-06-08;
canonical project zone remains Adelaide per DR-021).
**Closed:** 2026-05-17 22:36 PDT.
**Tool routing:** Claude Chat (planning, decisions,
brief revisions, architecture-level decisions);
no Claude Code dispatch this session.
**Governing DRs invoked:** DR-019 (read-time derivation
discipline), DR-021 (timestamp anchoring — Vancouver
temporary override recorded), DR-027/DR-028 (data-flow
boundaries — orthogonal context), DR-029 (close-out
arc baseline), DR-030 (module-boundary contracts —
clarified preservation under §3.1 read/write
asymmetry framing), DR-032 (bet-record / bet-leg
shape — referenced for §7.3 settlement-from-bet-row
discipline).

## Anchor

```
# Session-open command (Vancouver per S136 temporary
# instruction):
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-05-17 18:53 PDT

# Session-close command:
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-05-17 22:36 PDT
```

ACST equivalent of close (for cross-reference against
historical project timestamps): 2026-05-18 15:06 ACST.

## Pre-flight checks

Session-open ritual ran cleanly per the
`bethub-session-open` skill. Required reads completed
(current_state.md, standing_instructions.md,
project_context.md, SESSION_135.md, SESSION_134.md,
batch_1_drafts.md). Pre-flight directory listing
confirmed clean rebuild folder root, only
`SESSION_136_opening_prompt.md` in
`.close_out_backups/` as expected from S135's close.

Brief line count at session open: 3,152 lines (post-
S135 Batch 1 application).

Test baseline at session open: 753 passing (W13 close
baseline, unchanged since S131).

## Session shape

S136 was a brief-revision session that started as a
mechanical Batch 2 application pass (five spec'd
change areas from S134) and **expanded substantively**
when the operator's clarification of the profit-share
model surfaced a structural inconsistency between the
brief, the architecture.md doc, and the shipped W14
substrate. The session pivoted from "apply Batch 2 as
spec'd" to "apply Batch 2 plus a clarified
profit-share model that rolls up into a new substrate
step (§5.1b) and pending architecture.md edits."

The pivot was operator-driven and well-formed — Tim's
plain-language framing ("the holder's bank IS the
parked pool; profit-share is just bookkeeping") was a
genuinely cleaner model than what the existing
architecture doc carried. Claude (tech-lead position)
agreed with the simplification and folded the cleanup
into the W12 commission rather than spinning off a
separate W14.x amendment session, preserving forward
velocity.

**Pause-and-close trigger near end of session.** An
error message surfaced in the operator's UI during a
Batch 2 edit late in the session. Claude's tool calls
appeared to complete successfully and the response
landed clean, but the operator flagged that prior
occurrences of similar UI errors have correlated with
silent edit corruption. **The architecture.md §A.5
edit and the Code opening prompt were both deferred
to S137 in light of this concern.** S137's load-
bearing first action is verification of S136's brief
edits before any forward work.

## What was delivered

**1. Vancouver temporary timezone display
instruction.** Recorded in `current_state.md` at top
under "Temporary operator instruction" — active until
2026-06-08, reverts automatically. Display override
only; DR-021 unchanged (Adelaide remains the
canonical project zone, historical timestamps
preserved as written).

**2. Batch 2 mechanical application (all five spec'd
change areas from S134).**

- **§3.1 — new read/write asymmetry framing
  paragraph.** Hardened from the initial S134 draft
  per S136 risk-averse direction: each SQL-drop must
  name the path inline, replicate adapter-side
  business logic explicitly (supersession discipline
  on event tables, DR-019 state-on-row semantics on
  entity tables), and surface verification in the
  ship report. Recorded as a project-level principle
  to be carried into architecture.md §A.5
  (architecture edit deferred to S137).
- **§5.1 — slug-flip count three → two.** Dropped
  the `AccountCareWarningClearedPayload.warning_type_id`
  bullet (the field doesn't exist on the shipped
  payload — `Cleared` payloads carry
  `cleared_warning_event_id` instead).
- **§5.2 — adapter method names aligned with W13
  ship.** Six renames: `create_promo_template` →
  `create_template`, `create_warning_catalogue_entry`
  → `create_warning_type`, `list_promo_templates` →
  `list_templates`,
  `list_warning_catalogue_entries` →
  `list_warning_types`, plus the `get_*_by_id` →
  `get_template` / `get_warning_type` calls in the
  seed script's idempotency check. Also threaded
  through the §6 alignment-check reference-data read
  list and the §5.7 substrate-read references.
- **§5.5 — net-flow view rewrite.** Explicit window-
  scoping at the top, concrete external-payment
  event type list replacing the prior "confirm at
  §6.1" hedging language. Per the S136 model
  clarification: external-payment events are
  `account_holder_funding` (inflow),
  `account_holder_remittance` and `external_payment`
  (outflow). `profit_share_distribution` is NOT
  bank-touching under the clarified model.
  Added `external_payments_total` field to the
  output model per the operator's COGS-equivalent
  framing.
- **§7.3 — three CASH scenarios re-aligned.** CASH-2
  removes the bet-settlement cash flow event;
  return derives on read from the bet row per
  architecture.md §A.6. CASH-4 step 3 and step 4
  same shape — lay liability and lay settlement
  derive on read; no settlement cash flow events
  written. CASH-5 swaps `GOODWILL` → `FREEBIE` enum
  and adds the `credit_source_label = "goodwill"`
  derivation note. Also caught and fixed in CASH-4
  step 2: `INSURANCE_TRIGGER` → `TRIGGERED` with
  derived `credit_source_label = "insurance
  trigger"`.

**3. Profit-share model clarification (S136
substantive call).** Operator clarified that the
holder's bank account IS the parked pool — they are
literally the same physical money. A
`profit_share_distribution` event records a ledger
reallocation marking dollars already in the holder's
bank as the holder's own funds rather than
operational capital; no physical movement happens.
This collapses the prior two-flavour model
(`tim_direct` vs `account_holder_cash_holding`) into
a single-flavour model and resolves a structural
inconsistency between the brief, the architecture
doc, and the shipped W14 substrate.

Under the clarified model:

- **Cash with holder (Location 2):** profit-share
  always subtracts (operation's claim moves to
  holder).
- **Operation net-flow:** profit-share never appears
  (Tim's bank doesn't move).
- **No conjugate-split problem** (the prior model
  had profit-share appearing inconsistently across
  both views).

**4. New substrate step §5.1b.** Drops the now-
vestigial `funding_source` field from
`ProfitShareDistributionPayload`. Folded into W12 as
a second step zero alongside the §5.1 slug-flip,
rather than spun off as a separate W14.x amendment
session. Build order (§6.2) updated with new steps
5a and 5b sequenced after the §5.1 fallout. §1.1
opening updated from "two non-derivation pieces" to
"three non-derivation pieces." §9.2 hard limits
carved out specific exceptions for the
`cash_flow`-side cleanup. §5.9 edited-files list
extended to cover the three additional touchpoints
(`domain/cash_flow/__init__.py`,
`workflows/cash_flow/v1/cash_flow_store_adapter.py`,
`store/repositories/cash_flow.py`). Lint-imports
contract #2 and #3 narrative updated.

Schema-side: the orphan `funding_source` column in
the `cash_flow_events` table is tolerated (no Alembic
column-drop migration — out of scope per §9.4). The
column is ignored by all read and write paths after
§5.1b lands.

**5. Per-bookmaker cross-account view softening.**
Per operator framing — the view is useful for
occasional spot-checks of single-book concentration
across personas but isn't the core Location 2
derivation. §1.4 Finding-M paragraph and §5.4 body
softened. Parking-lot note added to
`current_state.md` under "Lower priority, parking-
lot" — revisit when W12 reads are live and the
operator can see what view shapes they actually
want.

**6. Brief verification snapshot.** Final brief line
count: 3,465 lines (+313 from session open). Section
numbering intact — 51 named sections, all
sequentially numbered (§1.1 through §11.5 with
§5.1b as the only sub-letter insertion). No
references to dropped enum values (`INSURANCE_TRIGGER`,
`GOODWILL`) or dropped enum flavours
(`tim_direct`, `account_holder_cash_holding`) outside
the §5.1b cleanup context.

## Standing-instruction adherence check

- **Cat 1: Tool routing always stated** — honoured.
- **Cat 1: BetHub DB reads via Desktop Commander
  start_process** — N/A this session (no DB reads).
- **Cat 2: Session-close opening prompt produced** —
  honoured (Step 8 below).
- **Cat 1: Brief drafting — surface strategic
  decisions only, autonomous on technical detail** —
  honoured. Tim's three direction calls were
  strategic (risk posture on read/write asymmetry,
  fix-now vs defer on funding_source, fold-into-W12
  vs separate W14.x). All sub-technical detail
  (anchor renumber, lint-imports contract narrative,
  build-order step sequencing) handled autonomously.
- **Cat 1: Fenced block 60-70 char line wraps** —
  honoured throughout brief edits.
- **Cat 1: Drive sync auto-enabled — no prompt** —
  honoured.
- **Cat 1: Unwind shorthand in operator-facing
  conversational text** — honoured.
- **Cat 1 sweep candidate authored this session:**
  the "no draft text unless I judge it earns your
  time; otherwise plain summary + direction needed"
  tightening of the existing operator-facing-
  language rule. Not promoted to encoded standing
  instruction this session; flagged for S137 review.

## Open items in

- **S137 reviews S136 brief edits for correctness
  before any forward work.** Load-bearing in light
  of the UI-error-during-edit episode. Specific
  spots to re-verify:
  - §3.1 framing paragraph — applied as new section
    with §3.2/§3.3 renumber.
  - §5.1 slug-flip — three → two anchors, opening
    paragraph adjusted to match.
  - §5.2 — six adapter method renames.
  - §5.5 — full substrate-read paragraph and
    algorithm rewrite plus output model
    `external_payments_total` field addition.
  - §5.1b — entire new section ~110 lines.
  - §1.1 — "two non-derivation pieces" → "three";
    file count narrative updated.
  - §1.4 + §5.4 — per-bookmaker view softening.
  - §6.2 — build order steps 5a and 5b inserted.
  - §9.2 hard limits — three bullets carved out
    exceptions.
  - §5.9 edited-files list — three new entries;
    lint-imports narrative contracts #2 and #3
    updated.
  - §6 alignment-check reference-data read list —
    adapter method name renames.
  - §5.7 substrate-read — `list_warning_types`
    rename.
  - CASH-2, CASH-4 steps 2/3/4, CASH-5 — settlement-
    from-bet-row updates and enum corrections.
- **Architecture.md §A.5 edit — deferred to S137.**
  Originally planned for S136; deferred when the
  profit-share model clarification expanded scope
  beyond the original ~15-line additive paragraph.
  The edit now needs to cover:
  - Read/write asymmetry as a project-level design
    principle (additive — three sub-points).
  - Location 2 framing — per account-holder, not
    per bookmaker (additive — short paragraph,
    softens to allow per-bookmaker as separate
    informational view).
  - Profit-share semantics rewrite (amends existing
    §A.5 content):
    - Bank-touching event table:
      `profit_share_distribution` moves from
      "Conditional" to non-bank-touching always.
    - Location 2 formula: simplify (no
      `funding_source` conditional).
    - Operation-net-flow formula: drop the
      `profit_share_distribution where
      funding_source = 'tim_direct'` term.
    - Profit-share semantics paragraph: rewrite to
      reflect the holder's-bank-IS-parked-pool
      model.
  - Probable size: 30–50 lines of net change across
    additions and amendments. Apply via multiple
    surgical `edit_block` calls rather than a single
    large rewrite.
- **Code opening prompt — deferred to S137.**
  Drafted after the brief and architecture.md edits
  are confirmed correct. Shape: review-before-build
  per the §6.1 halt rule that worked at S133. The
  artefact lives as `dr029/w12_balances/
  code_session_opening_prompt.md` or similar (path
  to confirm at S137).
- **S137 verification rigour.** Per the operator's
  S136-close concern about silent edit corruption
  from UI errors, S137 should:
  1. Read the brief end-to-end at session open,
     not just spot-check sections.
  2. Cross-reference §6.2 build order against §5
     section bodies for consistency.
  3. Verify the section numbering is unbroken (§5.1,
     §5.1b, §5.2, ..., §5.10 in sequence; no
     §5.1.5 or similar drift).
  4. Verify no orphan references to removed enum
     values or removed funding_source language
     outside the §5.1b cleanup context.
  5. Run a structural grep for known-fragile
     patterns: `INSURANCE_TRIGGER` should return
     zero matches; `funding_source` should return
     matches only inside §5.1b lines (~lines 668-
     772) and the cross-reference notes in §6.2 /
     §9.2 / §5.9 / §1.1.

## Open items out

- **Batch 2 application** — applied, complete in
  brief. Subject to S137 verification.
- **Profit-share model clarification** — captured in
  brief (§5.4, §5.5, §5.1b). Subject to S137
  verification and architecture.md §A.5 alignment.
- **Per-bookmaker view scope decision** — parked as
  W12.1+ refinement, captured in `current_state.md`.

## Carried forward

- All carried items from S135 plus the three new
  S137 priorities above. Live list in
  `current_state.md`.

## Forward routing

**Confirmed with operator** — S137 reviews S136
brief edits for correctness, completes architecture.md
§A.5 edit, drafts the Code opening prompt, then
closes. Code dispatch stays out-of-session per the
standing pattern.

S137 opening prompt (Step 8) carries the verification
rigour requirements explicitly so they don't drift.

## Session close state

- **Rebuild folder root:** clean. No phantom files.
  Vancouver timezone instruction recorded in
  `current_state.md` top.
- **WIP:** `dr029/w12_balances/w12_balances_brief.md`
  at 3,465 lines (post-Batch 2 + S136 substrate-step
  + per-bookmaker softening). Subject to S137
  verification.
- **`.close_out_backups/`:** to contain
  `SESSION_137_opening_prompt.md` after this close.
- **`sessions/`:** this file (SESSION_136.md) being
  written.
- **Project knowledge base:** no upload action
  required (Drive auto-sync per Cat 1).

## Close-out notes

S136 was a long, substantive session with one
expanded scope shift (profit-share model
clarification). The expansion was operator-driven,
well-formed, and Claude judges the resulting model
to be genuinely cleaner than what the architecture
doc previously carried. The cost was velocity:
architecture.md §A.5 edit and the Code opening
prompt both pushed to S137.

The operator flagged a UI error during a Batch 2
edit late in the session and the close was triggered
in part by concern about silent edit corruption.
S137's load-bearing first action is verification
before any forward work. This session record's "Open
items in" section names the specific spots to
re-verify and a structural-grep checklist.
