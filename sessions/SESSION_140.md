# Session 140 — W12.1 lay-balance brief drafted and locked; commission-source conflict found and routed to its own item; W15 ops-log grounded but brief deferred after a full local-MCP outage

**Opened:** 2026-05-26 16:21 PDT (Vancouver — temporary timezone
display window active until 2026-06-08; canonical project zone
remains Adelaide per DR-021; ACST equivalent 2026-05-27 08:51
ACST).
**Closed:** 2026-05-27 08:34 PDT (ACST equivalent 2026-05-28 01:04
ACST — session spanned a stepped-away overnight gap; active work
was modest, concentrated either side of the gap).
**Tool routing:** Claude Chat (brief drafting + grounding).
Empirical grounding reads against the live v3 codebase at
`/Users/tim/Desktop/Projects/bethub-v3/`. No Claude Code dispatch.
W12.1 brief locked; W15 brief deferred to S141.
**Governing DRs invoked:** DR-025 (hedge classification — the
S139 amendment that locked the lay substrate), DR-019
(derive-on-read — liability never stored), DR-032 (canonical bet
record / bet_legs), DR-026 / architecture.md §A.10 (Betfair
canonical for market facts incl. commission), DR-030 (module
boundaries), DR-031 (tech stack; Python 3.12+; Alembic deferred),
DR-021 (timestamp anchoring; Vancouver display override active).

## Anchor

```
# Session-open (Vancouver per temporary instruction):
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-05-26 16:21 PDT

# Session-close (after the MCP bridge recovered):
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-05-27 08:34 PDT
```

## Pre-flight checks

Session-open ritual ran per `bethub-session-open` skill. Required
reads completed (`current_state.md`, `standing_instructions.md` in
full, `project_context.md`, `SESSION_139.md`). Pre-flight directory
listing: clean root, expected files plus openapi.json, no phantoms.

**Drift-check (Step 5):** clean.
- (a) `current_state.md` "Last updated" 2026-05-21 18:00 PDT matched
  `SESSION_139.md` "Closed:" timestamp.
- (b) `SESSION_139.md` present, non-empty (274 lines).
- (c) `v3_build_picture.md` "Last updated" 2026-05-21 18:00 PDT —
  correctly updated at S139 close (W12 dropped, W12.1 added). Render
  condition TRUE; build picture rendered at open.
- `.close_out_backups/` held `SESSION_140_opening_prompt.md` as
  expected from S139 close.

**Timezone re-anchor at open:** the open ritual's default Adelaide
anchor was corrected to the Vancouver display override per the live
`current_state.md` temporary instruction (active until 2026-06-08).

## Session shape

A brief-drafting session. Primary: draft the W12.1 lay-balance fix
brief (grounded at S139). Secondary: draft the W15 ops-log brief.
The W12.1 brief was drafted and locked. During W15 grounding, a
full local-MCP-bridge outage (both Desktop Commander and
projects-filesystem hung 4 minutes each) made disk writes
impossible; the operator stepped away and resumed next morning,
the bridge recovered, and the session closed. W15 brief drafting
deferred to S141 — split rather than push (Session 11 lesson),
forced this time by tooling rather than budget.

## What was delivered

**1. W12.1 lay-balance fix brief — LOCKED.** Written and verified
at `dr029/w12_balances/w12_1_lay_balance_brief.md` (459 lines,
SHA256 prefix `7a6d4dac`). Surgical-fix shape (Sessions 35/36
precedent), §1–§11 spine. Scope: add `side` + `commission` columns
to the `bets` table (DDL + idempotent `_add_column_if_missing`,
W6/W6.5/W9 pattern); add the fields to the `BetRecord` domain model
(backward-compatible defaults); persist + read them in the repo;
record `side` at bet entry from the construction the staking
calculator already computes; add the lay branch to the read-side
cash maths in `balance_derivation.py` (the four helpers
`_read_bet_rows_for_account_at_book`, `_bet_cash_return`,
`_bet_cash_stake_committed`, `_bet_pending_cash_stake`), liability
derived on read per DR-019. Net-effect checks built in: lay win =
+stake×(1−commission), lay loss = −liability, void = 0. NULL side
→ treated as back (preserves current behaviour). Commission read
with 8% fallback. Strict dirty-tree git discipline (the W12 build
is untracked). Focused tests. Cross-check the lay maths against
`domain/bets` construction definitions, mismatch as a finding.

**2. Scope correction surfaced during grounding.** S139 framed
W12.1 as "read-side only." Grounding revealed there is NO stored
signal today that a Betfair bet is a lay vs a back (the `BetRecord`
model and repo INSERT carry `book_or_exchange` but no `side`). So
the fix necessarily threads `side` through the write path
(domain model → repo INSERT → set at bet-entry construction) for
the lay branch to ever fire. This is the minimal write-side touch;
commission *population* stays deferred. Surfaced to the operator
before drafting; folded into the brief scope.

**3. Commission-source conflict found — routed to its own item.**
The v3 bet-entry staking calculator
(`workflows/bet_entry/v1/staking.py`, built in W4) sources
commission from a static `_COMMISSION_TABLE` (hard-coded:
AU thoroughbred 8%, Ipswich 4%, AFL/NRL 5%, other 6%) — the exact
track-table mechanism the S139 DR-025 amendment ruled against in
favour of Betfair's per-market `marketBaseRate`. So the built v3
code contradicts the S139 decision, and the conflict touches
staking (bet sizing), not just balances. Operator was presented
A/B/C (small read-side fix + park / fold write-side in / pause and
reconcile first); operator flagged the worry that parking creates
downstream rework but delegated the call. **Call made: Option A** —
build W12.1 now (it's forward-compatible; nothing built gets thrown
away when commission source later changes), defer the
commission-source reconciliation as its own brief. Reasoning: the
reconciliation is fixed-size work whether done now or later, v3
isn't live so no bad data accrues, and folding a W4-staging-reopen
into a balance fix is the scope-mixing briefs prevent. Honest
caveat recorded: lay balances run on the 8% fallback until the
reconciliation lands, but balances have no UI until W17+ so cannot
mislead in daily use.

**4. W15 ops-log grounded; brief deferred to S141.** Full grounding
captured to `dr029/w15_ops_log/_drafts/SESSION_140_drafts.md`
(183 lines): the per-domain event-table pattern (4 layers + tests +
linter), the common event-header shape, the `ops_events` design
(scope = bet_id/cycle_id; v1 single event type
`hedge_state_classification`; the six-state `HedgeState` enum to be
defined — not in code yet), the import-linter carve-out
(register `workflows.ops` in the `workflows-independent` contract;
inconsistency observed — promos/cash_flow/balances not listed —
surface as finding), the venv anchor fold, the three-way test
split, the home decision (per-domain pattern per the
`store/schema/cash_flow.py` docstring authority; top-level `ops/`
package is distinct and untouched). Brief NOT written (the outage).

**5. Local-MCP-bridge outage (environmental).** Mid-W15-grounding,
Desktop Commander hung 4 minutes; a follow-up probe of the
top-level `ops/` package, then a projects-filesystem read, both
hung identically — the whole Claude Desktop MCP bridge was
unresponsive, not one server. No disk writes possible during the
outage. Operator stepped away; on resume the bridge had recovered
and the close-out ran normally. This is the escalation of the
DC-flakiness watch-flag carried from S139 (one ~4-min timeout
there → full bridge outage here).

## Standing-instruction adherence check

- **Cat 1 silent open-ritual — PARTIAL (again).** No numbered step
  headers, but connective narration remained ("Starting the open
  ritual", "Continuing reads"). Same shape as S138/S139. Streak not
  re-established; S141 open is the next watch point.
- **Cat 1 calendar-calibrated recap** — honoured (new-workday recap
  at open: 5 days since S139).
- **Cat 1 build-picture conditional render** — honoured (rendered
  at open; streams moved at S139 close). 20 consecutive clean
  S120–S140.
- **Cat 1 plain-language operator framing** — honoured (lay maths,
  commission conflict framed in real gambling terms; A/B/C surfaced
  plainly).
- **Cat 1 escalate-to-detail-only-when-warranted** — honoured
  (flagged "this deserves a little detail" before the commission
  conflict and before the scope correction).
- **Cat 3 empirical-verification-before-asserting** — strong. Every
  W12.1 anchor re-verified live before drafting (line numbers
  matched S139); the commission conflict was confirmed by reading
  `staking.py` (not asserted from the grep alone); the no-stored-side
  finding confirmed against the repo INSERT + domain model.
- **Cat 5 make-software-calls-don't-punt** — honoured. The
  commission-source routing (Option A) was a delegated call;
  decomposition of the lay maths across the committed/return split
  was made, not punted.
- **Cat 2 timestamp anchors / required reads / pre-flight /
  drift-check** — honoured.
- **Cat 3 filesystem fallback** — exercised: on the DC outage,
  switched to projects-filesystem per Cat 3; when that also hung
  (whole-bridge outage), surfaced honestly rather than degrading
  silently.
- **Split-rather-than-push (Session 11)** — honoured: W15 deferred
  rather than pushed through a flaky/dead bridge.
- **Operator-confirmed forward routing (Session 42)** — honoured:
  operator said "bank it, close out" explicitly.
- **Minimal-close on split-trigger** — applied (tooling instability
  + operator wrap + Adelaide day-rollover all fired).

## Open items in (carry to S141)

- **W15 ops-log brief drafting — PRIMARY S141.** Fully grounded;
  read `dr029/w15_ops_log/_drafts/SESSION_140_drafts.md` first.
- **Commission-source reconciliation brief — NEW, tracked.** Port
  `staking.py` off the static `_COMMISSION_TABLE` onto Betfair's
  per-market `marketBaseRate`, and snapshot `commission` onto the
  bet record at entry — the full landing of the S139 DR-025
  decision. Reopens W4 staking + its tests. Own brief; sequence
  after W15, or per operator priority. This is the parked half of
  the W12.1 commission decision.
- **Vancouver timezone override** — active through 2026-06-08;
  revert to Adelaide anchors at first open on/after that date.

## Open items out (closed/advanced S140)

- **W12.1 lay-balance brief** — drafted and locked (was: brief
  drafting grounded S139). W12.1 now `awaiting-code-execution`.

## Session close state

- **`dr029/w12_balances/w12_1_lay_balance_brief.md`** — NEW, locked
  (459 lines, SHA `7a6d4dac`). Ready to hand to Code.
- **`dr029/w15_ops_log/_drafts/SESSION_140_drafts.md`** — NEW
  (183 lines). W15 grounding capture.
- **`current_state.md`** — rotated to S140 close.
- **`v3_build_picture.md`** — W12.1 → `awaiting-code-execution`
  (brief locked); commission-source reconciliation added as a new
  tracked sub-stream; W15 next-milestone updated (grounded, brief
  S141).
- **`.close_out_backups/`** — `SESSION_141_opening_prompt.md`
  written; stale `SESSION_140_opening_prompt.md` swept.
- **`sessions/`** — this file (`SESSION_140.md`).
- **v3 codebase** — unchanged this session (read-only grounding).
  W12 build remains dirty/untracked.
- **No governance-doc edits** — `decisions.md` /
  `standing_instructions.md` untouched this session. (S139's pending
  `decisions.md` re-upload still applies — see pending actions.)

## Pending operator-side actions

- **Re-upload `decisions.md` to the Project knowledge base** —
  carried from S139 (the DR-025 amendment). Still outstanding if not
  yet done; local-disk reads are current regardless.
- **Restart cleared:** the local MCP bridge recovered on its own /
  after the step-away; no action needed unless it recurs at S141.

## Forward routing

**Confirmed with operator** — S140 banked the W12.1 brief and
closed out at the operator's explicit instruction ("bank it, let's
close out") after the MCP outage made W15 drafting impossible.
**S141 drafts the W15 ops-log brief first** (fully grounded;
scratch file is the first read), then the operator decides whether
the **commission-source reconciliation brief** follows or is
re-prioritised. W12.1 is ready for out-of-session Code execution
whenever the operator chooses to run it.

## Carry-forward sensitivity

- **Cat 1 silent open-ritual** — partial again (connective
  narration); S141 watch point.
- **Cat 1 build-picture render** — 20 consecutive clean.
- **Cat 3 empirical verification** — strong (commission conflict +
  no-stored-side both confirmed against live source, not asserted).
- **Desktop Commander / local-MCP flakiness — ESCALATED.** S139 had
  one ~4-min timeout; S140 had a full-bridge outage (both MCP
  servers down ~4 min each). Recovered after the step-away. If this
  recurs at S141, consider it a pattern worth raising with the
  operator as an environment issue, not just a watch-flag.

## Close-out notes

A clean brief-drafting session bookended by an environment failure.
W12.1 landed well — the grounding caught two things S139's framing
missed (the unavoidable write-side `side` thread, and the
commission-source conflict with already-built W4 code), and both
were surfaced rather than silently absorbed. The commission-source
finding is the substantive governance catch: the v3 staking code
contradicts the S139 Betfair-rate decision, now tracked as its own
item. W15 was fully grounded but the brief deferred to S141 when
the whole local-MCP bridge went unresponsive mid-session — split
rather than push, forced by tooling. Close-out ran normally once
the bridge recovered. No structural drift; no governance-doc edits.
