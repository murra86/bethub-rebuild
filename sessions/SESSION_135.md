# Session 135 — W12 brief: drift triage and Batch 1 application

**Opened:** 2026-05-17 14:37 ACST
**Closed:** 2026-05-18 01:09 ACST
**Wall-clock:** ~10.5h (mostly operator-away time;
active session work much shorter)
**Tool routing:** Claude Chat (orchestration, drift
triage, brief edits via Desktop Commander)
**Governing DRs:** DR-019 + S124 amendment, DR-021,
DR-022, DR-029, DR-030 + S124 amendment, DR-032
**Skill fires:** `bethub-session-open` (clean fire),
`bethub-session-close` (clean fire)

---

## Anchor

- Open anchor: `TZ="Australia/Adelaide" date` returned
  `2026-05-17 14:37 ACST`.
- Close anchor: `TZ="Australia/Adelaide" date` returned
  `2026-05-18 01:09 ACST`.
- Calendar-calibrated gap to previous close (S134 at
  2026-05-17 13:49 ACST): same workday open, ~48
  minutes after prior close.

---

## Pre-flight checks

Open-side directory listing surfaced one anomaly: the
W12 brief on disk was 2,973 lines with a partial §1.4
inserted (header + Finding-H paragraph only). S134's
close-out recorded the brief at 2,949 lines, no §1.4 —
Batch 1 was drafted-not-applied per Path (b) split.

File mtimes pinned the brief modification at ~14:21
ACST, between S134 close (13:49 ACST) and S135 open
(14:37 ACST). No record of an editing session in that
gap. Drift surfaced before substantive work; operator
chose rollback to `.pre_s134_revision/` backup as the
recovery path.


## Session shape

Single-arc session focused on W12 brief Batch 1
revision application against the S134-drafted change
set. Drift triage absorbed the first action, then
clean rollback and Batch 1 application proceeded. No
pivots; no probe work; no governance edits. Closed
short of Batch 2 because (a) Batch 1 took 16 small
`edit_block` calls, (b) day-rollover and >3h
wall-clock fired split triggers, (c) the session had
already produced one unexplained drift episode and a
fresh chat was the safer ground for Batch 2.

The S128 hold-without-escalation pattern held — open
ritual rendered without step headers in
operator-facing text.

---

## What was delivered

### 1. Drift episode triaged and rolled back

W12 brief on disk was at 2,973 lines (vs S134-recorded
2,949) with a partial §1.4 — header + Finding-H
paragraph from Change 1, missing Findings C / M / G /
J-K / C-Gap-2 and the remaining-findings line.
Operator decision: roll back to
`.pre_s134_revision/w12_balances_brief.md` backup,
then apply Batch 1 cleanly. Rollback verified at
2,949 lines, no §1.4 header. Cause of partial
mutation between S134 close and S135 open remains
unexplained. Pre-revision backup retained on disk at
`dr029/w12_balances/.pre_s134_revision/w12_balances_brief.md`.

### 2. Batch 1 applied across 16 small edits

All six anchor changes from S134's
`.s134_revision_drafts/batch_1_drafts.md` landed:

- **Change 1 — §1.4 "Triage context from Session 134"
  inserted** (4 edits): six finding paragraphs
  (H, C, M, G, J/K, C-Gap-2) plus the
  remaining-findings line. §1.4 sits between §1.3 and
  §2.

- **Change 2 — §5.3 substrate + algorithm rewrite**
  (3 edits): substrate block replaced with the
  3-read shape (cash flow events, raw SQL against
  bets, `promo_cash_credited` events) per
  architecture.md §A.5; algorithm rewritten with the
  6-term cash-balance formula per §A.5 / §A.6;
  pending-stake separation paragraph replaces the
  prior in-cash-flow-events framing.

- **Change 3 — §5.4 full rewrite as
  Per-account-holder cash holding** (7 edits): title
  flipped from `Per-custodian cash holding`; body
  rewritten around `account_id` (the account-holder)
  rather than `book_id`; parked-pool formula with 6
  signed terms; per-account-at-book breakdown via
  §5.3 filter; total cash with holder = parked-pool
  + sum of breakdown; cumulative profit-share
  informational; Pydantic model swapped to
  `AccountHolderCashHolding`; edge cases rewritten;
  file anchor function renamed to
  `compute_account_holder_cash_holding`.

- **Change 4 — §5.6 algorithm step 2 + Pydantic
  model** (3 edits): payload-field names flipped to
  W13-shipped (`face_value_expiry`,
  `triggering_promo_instance_id`); credit-source
  enum corrected to W13 binary
  (`TRIGGERED`/`FREEBIE`); enriched
  `credit_source_label` derivation inserted (walks
  promo instance → template → `template.kind` to
  produce operationally-rich labels);
  `AvailableFreeBet` model field names aligned and
  `credit_source_label` added.

- **Change 5 — §5.7 algorithm rewrite + edge case**
  (4 edits): algorithm now walks raise-event-IDs
  (not warning-type tallies) per Finding-J/K;
  multi-raise-before-clear semantics rewritten —
  clear events reference specific raise event IDs,
  one clear cancels one raise; severity always from
  `severity_at_raise` (mandatory field, no
  catalogue-fallback path); edge case for
  catalogue-severity-drift replaced with the
  raise-event-as-source-of-truth framing.

- **Change 6 — §5.8 substrate bullet + algorithm
  step 2** (2 edits): bet-record substrate bullet
  rewritten — bet IDs walked backwards via
  `FreeBetCreditedPayload.triggering_bet_id` and
  `FreeBetDeployedPayload.deploying_bet_id`, then
  fetched by ID via `read_bet_record(bet_id)`;
  algorithm step 2 (`OBSERVED_NOT_TAKEN`) rewritten
  to walk the promo event log rather than a
  forward-only bet-record-with-`promo_template_id`
  filter (which doesn't exist on the substrate).

Post-Batch-1 state verified: 3,152 lines, all section
headers in order, §5.4 reads "Per-account-holder
cash holding," net delta +203 lines.

### 3. Batch 2 deferred to S136

Five mechanical changes plus architecture.md §A.5
add plus Code opening prompt draft remain
outstanding. Drafting partially in-flight during the
session (target areas read into context: §3.1, §5.1,
§5.2, §5.5, §7.3 CASH-2 / CASH-4 / CASH-5) but no
edits applied. S134's
`.s134_revision_drafts/batch_1_drafts.md` still
holds the full Batch 1 + Batch 2 specification — re-
read at S136 open for Batch 2 anchors.


---

## Standing-instruction adherence check

- **Cat 1 silent open-ritual discipline:** held. No
  step headers in operator-facing text at open. The
  drift surfaced through normal pre-flight, not
  through ritual narration.
- **Cat 1 calendar-calibrated open:** held. ~48 min
  gap to S134 close named explicitly.
- **Cat 1 v3 build picture render:** not rendered
  at open — no stream-state change since S134 (W12
  still active, brief still in revision).
- **Cat 2 session protocol:** held — anchor at
  open, anchor at close, session record written,
  current_state.md rotated, opening prompt
  generated.
- **Cat 2 minimal close on split trigger:** held —
  day-rollover and >3h wall-clock fired Step 3
  triggers; close runs minimal (record + state +
  opening prompt; no v3_build_picture update; no
  standing_instructions sweep).
- **Cat 3 filesystem discipline:** held — Desktop
  Commander used for all reads and writes; no
  `copy_file_user_to_claude` against bethub-rebuild
  files.
- **Cat 4 brief drafting style:** N/A — no new brief
  work, only revision application against drafted
  changes.
- **Cat 5 operator–Claude division of labour:**
  held — drift triage surfaced for operator
  decision (rollback vs forward-fix vs pause); Code
  did not run; rebuild folder edits all routed
  through Chat per the W12-revision arc shape.

---

## Open items in (new this session)

- **Drift episode unexplained.** The partial §1.4
  insert between S134 close (13:49 ACST) and S135
  open (14:37 ACST) has no traced cause. Not
  blocking forward work but flagged for awareness;
  if a similar pattern recurs, the operator may
  want to investigate AdsPower / Drive sync / other
  background processes touching the rebuild folder.
- **Batch 2 outstanding.** Five mechanical changes
  + architecture.md §A.5 add + Code opening prompt
  draft. S136 primary deliverable.

## Open items out (closed this session)

- **Batch 1 drafted-not-applied** (carried in from
  S134). Now applied. `batch_1_drafts.md` retained
  in `.s134_revision_drafts/` as historical
  reference; Batch 2 still references it.

---

## Session close state

- **Rebuild folder root:** clean, no phantoms.
  21 expected items (4 dirs visible at depth 1 plus
  artefact files listed in pre-flight).
- **`dr029/w12_balances/`:** brief at 3,152 lines
  (Batch 1 applied), pre-revision backup retained
  at `.pre_s134_revision/`, drafts retained at
  `.s134_revision_drafts/`.
- **`sessions/`:** SESSION_135.md present
  (this file).
- **`.close_out_backups/`:** stale
  `SESSION_135_opening_prompt.md` deleted at
  Step 9; new `SESSION_136_opening_prompt.md`
  written.
- **`v3_build_picture.md`:** untouched (no stream
  movement).
- **`standing_instructions.md`:** untouched (no
  edits this session).
- **Project knowledge base:** no operator-side
  re-uploads required.

---

## Forward routing — confirmed with operator

S136 primary deliverable: apply Batch 2 to W12 brief
from the now-known-good 3,152-line state. Five
mechanical changes per S134's
`batch_1_drafts.md` Batch 2 spec:

1. §3.1 read/write asymmetry framing add
2. §5.1 slug-flip target count clarification
   (Finding-N)
3. §5.2 seed mechanism field-name cleanup
4. §5.5 net-flow window framing (Finding-I) +
   external-payment classification (Finding-F)
5. §7.3 CASH-2 / CASH-4 / CASH-5 scenario
   alignment to the rewritten §5.3 algorithm
   (no bet-settlement cash flow event, refunds
   via DR-019 read-time derivation)

After Batch 2 lands:
- architecture.md §A.5 paragraph add (the design
  principle the brief now cites — write-side
  through adapter, read-side may drop to SQL)
- Code opening prompt draft for W12 commission

Operator-confirmed at S135 ~01:05 ACST in response
to "Yes — I think closing out now is the right
call" exchange.
