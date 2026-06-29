# Session 134 — W12 alignment triage + Batch 1 revision drafts

**Opened:** 2026-05-14 06:10 ACST
**Closed:** 2026-05-17 13:49 ACST
**Title:** Triage Code's S133 W12 alignment findings; lock six
operator decisions; draft Batch 1 brief revisions (drafted not
applied).
**Tool routing:** Claude Chat (planning, decisions, brief
drafting); Code dispatch deferred to S135.
**Governing DRs:** DR-019 (derived state on read), DR-021
(Adelaide local time), DR-022 (book/account/account-at-book
vocabulary), DR-030 (module-boundary discipline; the
read/write asymmetry sits inside this), DR-029 (rebuild scope).

---

## Anchor

**Open command + output:**
```
$ TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
2026-05-14 06:10 ACST
```

**Close command + output:**
```
$ TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
2026-05-17 13:49 ACST
```

Multi-day wall-clock (open Wed morning, close Sat afternoon
local time). Active session work was moderate — triage
conversation across ~four operator-decision rounds plus a
visual plus the Batch 1 drafting pass.

---

## Pre-flight checks (S134 open)

- `current_state.md`, `v3_build_picture.md`, `SESSION_133.md`
  all stamped 2026-05-14 05:55 ACST — no drift.
- `dr029/w12_balances/w12_balances_report.md` (1,187 lines)
  present on disk per S133 close.
- S134 opening prompt at
  `.close_out_backups/SESSION_134_opening_prompt.md` consumed.
- Cat 1 silent-open ritual broken — step headers ("Step 1 —
  Timestamp anchor", "Step 2 — Required reads") rendered to
  operator-facing text. Surfaced; not escalated (operator has
  declined revisit of hold-vs-escalate at S132 and S133).

---

## Session shape

S134 was a triage-and-revision session, no Code dispatch. Code
halted at the §6.1 alignment gate during the S133 W12 build
session and surfaced 15 findings — 7 brief-spec deviations, 7
load-bearing alignment misses, 1 standing observation. S134
worked through them as four operator-decision rounds:

1. **Severity ordering and inventory.** Plain-language pass
   over all 15 findings; classified as load-bearing,
   medium-impact, low-impact, cosmetic, or standing observation.
2. **Finding-H balance algorithm.** Locked: algorithm follows
   architecture.md §A.5/§A.6 verbatim. Cash returns derive
   from the bet row, not from settlement events. No
   `bet_won` / `bet_lost` event type added.
3. **Finding-C bet record substrate.** Locked: route (i) raw
   SQL workaround for the missing list-by-account-at-book
   method; promo→bet linkage walks backwards via promo
   events. Visibility discipline applied — the SQL-direct
   pattern surfaces in three places (brief per-section, brief
   §3.1 framing, architecture.md §A.5 paragraph) to prevent
   surprise in future related workstreams.
4. **Finding-G FB credit source labels.** Locked: option (ii)
   — derive rich `credit_source_label` field from the source
   promo's template kind. Binary enum stays untouched. Same
   visibility shape as Finding-C Gap 2.
5. **Finding-M Location 2 framing.** Pivoted through operator
   correction — first read (per-bookmaker aggregated across
   personas) rejected as not operationally meaningful. Locked:
   per account-holder with parked-pool balance + per-book
   breakdown + total + cumulative profit-share distributed.
   Added handling for `profit_share_distribution` two-flavour
   semantics (`tim_direct` vs `account_holder_cash_holding`
   funding sources). Visual produced mid-session to confirm
   the model.

The remaining nine findings (B, E, F, I, J, K, L, N, O) were
classified as silent Cat 5 mechanical applications — surfaced
in the triage summary for transparency, applied without
operator decision rounds.

Then drafted Batch 1 of the brief revision — six load-bearing
anchor changes covering the locked decisions. Operator
confirmed the Batch 1 summary at high level ("All good") and
elected Path (b) — split rather than push through to
application + Batch 2 + architecture edit + Code dispatch
within S134 budget. S11 lesson applied.

---

## What was delivered

1. **Triage of all 15 S133 findings.** Each classified by
   severity and impact; six load-bearing decisions locked
   with operator; nine mechanical Cat 5 applications named
   for transparency. Locked decisions recorded in the
   session-close artefact at
   `dr029/w12_balances/.s134_revision_drafts/batch_1_drafts.md`.

2. **Pre-revision backup of the W12 brief.** Frozen snapshot
   at `dr029/w12_balances/.pre_s134_revision/w12_balances_brief.md`
   (108,384 bytes; matches state at S134 open). Provides
   diff comparison source for S135 application work and any
   future review.

3. **Batch 1 drafts on disk.** Six anchor drafts (~280 lines
   of new prose) saved at
   `dr029/w12_balances/.s134_revision_drafts/batch_1_drafts.md`
   (589 lines including notes). Operator-confirmed at S134
   close. Ready for S135 `edit_block` application:
   - Change 1 — new §1.4 "Triage context from Session 134".
   - Change 2 — §5.3 substrate read + algorithm rewrite
     (Finding-H + Finding-C Gap 1).
   - Change 3 — §5.4 full rewrite, title and body
     (Finding-M; per-account-holder framing).
   - Change 4 — §5.6 algorithm step 2 + `AvailableFreeBet`
     model (Findings G + L; credit_source_label derivation
     and `face_value_expiry` field rename).
   - Change 5 — §5.7 algorithm rewrite (Findings J + K;
     raise-event-id-linked semantics, mandatory
     severity_at_raise).
   - Change 6 — §5.8 substrate read + algorithm step 2
     (Finding-C Gap 2; walk promo event log backwards for
     bet→promo linkage).

4. **Forward routing locked.** Path (b) — split. S135 applies
   Batch 1, drafts+applies Batch 2 (six mechanical changes),
   drafts+applies architecture.md §A.5 paragraph, drafts the
   Code opening prompt with review-before-build shape, then
   closes. Code dispatch happens out-of-session after S135.

---

## Standing-instruction adherence check

**Cat 1 — Silent open ritual:** broken. Step headers leaked
into operator-facing text at S134 open ("Step 1 — Timestamp
anchor", "Step 2 — Required reads"). Surfaced once; not
escalated per operator preference at S132 and S133. Pattern
is now 9-of-11 broken. Standing observation only.

**Cat 1 — V3 build picture render at session open:** skip
honoured. Same-workday + in-flow on W12 arc; operator just
saw the build picture at S133 close. Render would have been
ritual noise.

**Cat 1 — SQL-direct read pattern visibility:** introduced
this session as a discipline (Finding-C lock). Will land in
three places at S135: brief §3.1 framing, brief per-section
prose, architecture.md §A.5 paragraph. Not yet exercised — the
discipline is *spec'd* this session, *applied* next session.

**Cat 2 — Pre-execution risk advisory:** honoured. The split
decision at the Batch 1 → application boundary surfaced the
risk explicitly before pushing through.

**Cat 2 — Drift-check at session open:** honoured. S133 close
state matched expectations.

**Cat 3 — Filesystem discipline:** honoured. All writes via
Desktop Commander `write_file`. No `bash_tool` invocations
attempted. `start_process` used for read-only commands
(timestamp, `ls`, `wc`, `grep`).

**Cat 5 — Operator-Claude division:** honoured. Operator made
four load-bearing decisions (Findings H, C, G, M). Nine
mechanical applications classified as Cat 5 Claude territory
and named for transparency. No Cat 5 calls smuggled past the
operator.

---

## Open items in (carries forward to S135)

- **Apply Batch 1 to the brief** via six `edit_block` calls
  in order (Changes 1–6 per
  `dr029/w12_balances/.s134_revision_drafts/batch_1_drafts.md`).
  Pre-revision backup at
  `dr029/w12_balances/.pre_s134_revision/w12_balances_brief.md`
  is the diff source.
- **Draft and apply Batch 2.** Six mechanical changes:
  - §3.1 read/write asymmetry framing add (~10 lines).
  - §5.1 slug-flip count three → two (drop the
    `AccountCareWarningClearedPayload.warning_type_id`
    bullet; that field doesn't exist on the shipped payload).
  - §5.2 adapter method name fixes — replace
    `create_promo_template` → `create_template`,
    `create_warning_catalogue_entry` → `create_warning_type`,
    `list_promo_templates` → `list_templates`,
    `list_warning_catalogue_entries` → `list_warning_types`,
    plus `get_*` references.
  - §5.5 net-flow window clarification (~5 lines —
    clarify "net flow over the named window", not
    cumulative since day 0).
  - §7.3 scenarios — CASH-2 (remove bet-return cash flow
    event reference; final balance unchanged at $300),
    CASH-4 step 4 (remove lay-liability and commission cash
    flow event references; replace with bet-row-derived
    returns), CASH-5 (change `GOODWILL` → `FREEBIE`, add
    `credit_source_label: "goodwill"`).
- **Draft and apply architecture.md §A.5 paragraph** —
  ~15 lines. Names: (a) read/write asymmetry as a design
  principle; (b) Location 2 = per `account_holder_id` =
  `accounts.account_id` (resolving the prose ambiguity that
  Finding-M flagged); (c) `profit_share_distribution`
  two-flavour `funding_source` semantics and how each affects
  parked pool vs operation_net_flow.
- **Draft the Code opening prompt** with the review-before-
  build shape per operator's S134 instruction: Code reviews
  the revised brief and surfaces any remaining alignment
  concerns before implementing. Mirrors the §6.1 halt rule
  pattern that worked at S133.
- **Verify revised brief at S135 close** with end-to-end
  `wc -l` and section-header grep before Code dispatch.

---

## Open items out (closed this session)

- **W12 alignment triage** — closed. All 15 findings
  classified; six locked with operator; nine Cat 5 mechanical.
- **Forward-routing decision for S135** — closed. Path (b)
  split.
- **Pre-revision backup** — closed. Frozen at
  `.pre_s134_revision/w12_balances_brief.md`.

---

## Session close state

- **Rebuild folder root** (`/Users/tim/Desktop/Projects/bethub-rebuild/`):
  unchanged shape; same 22 entries as S134 open. No new
  top-level artefacts.
- **WIP** (`work_in_progress.md`): unchanged — no edits this
  session.
- **`.close_out_backups/`**: S134 opening prompt being deleted
  in close ritual; S135 opening prompt being written.
- **Sessions folder**: SESSION_134.md being added.
- **Project knowledge base**: no upload action needed.
  `standing_instructions.md` was not edited this session.
- **dr029/w12_balances/**: gained two close-out artefacts:
  - `.pre_s134_revision/w12_balances_brief.md` (frozen
    pre-revision snapshot).
  - `.s134_revision_drafts/batch_1_drafts.md` (drafted
    revisions awaiting S135 application).

---

## Forward routing

**S135 commission (operator-confirmed at S134 close):**

1. Open ritual per `bethub-session-open` skill.
2. Read `.s134_revision_drafts/batch_1_drafts.md` end-to-end.
3. Apply Changes 1–6 via `edit_block` calls in order against
   `dr029/w12_balances/w12_balances_brief.md`.
4. Sanity-check brief structure with `wc -l` and section
   header grep post-application.
5. Draft Batch 2 — six mechanical changes — and apply each
   on operator-confirm or batch-confirm.
6. Draft architecture.md §A.5 paragraph and apply on
   operator-confirm.
7. Draft Code opening prompt with the review-before-build
   shape; operator reviews; lock for dispatch.
8. Close S135.

**S135 is not commissioning Code.** Code dispatch is operator
copy-paste of the locked opening prompt into a fresh Claude
Code session after S135 closes. Code dispatch out-of-session
preserves the S134 lesson that brief-revision work belongs to
operator-Claude and not Code.

**Confirmed with operator at S134 close:** path (b) split
locked; S135 scope as above.

---

**Session close state verified at 2026-05-17 13:49 ACST.**
