# Session 123 — Pre-W14 codebase review report triaged end-to-end; sixteen findings routed; coordinated pre-W14 governance update locked for S124

**Opened:** 2026-05-11 22:52 ACST
**Closed:** 2026-05-12 05:47 ACST
**Wall-clock:** ~6h 55m elapsed. Same-workday open relative
to Session 122 close (22:36 → 22:52; ~16m gap). Session
crossed local midnight ACST during execution — pause-and-
resume pattern implied (operator did not explicitly flag
pauses; the timestamp gap is the structural fact). Day-
rollover trigger fired at close per `governance.md` §close-
out protocol §2; close ran as minimal-close discipline (no
in-flight extra artefacts layered on top of close itself).
**Tool routing:** Claude Chat for the entire triage —
pre-W14 codebase review report read, 16 findings routed,
coordinated pre-W14 governance update planned, plus close-
out. All filesystem ops via Desktop Commander. No Code
dispatch this session.
**Governing DRs invoked:** DR-021 (Adelaide local time
anchoring, open / close). DR-019 (derived state on read —
load-bearing for Finding #5 routing; rolled into Finding
#1's resolution). DR-026 (market-context snapshot — load-
bearing for Finding #3 routing). DR-027 (two-database
architecture / single-event-log spine — load-bearing for
Finding #1 routing; amendment scoped for S124). DR-030
(v3 repo layout / module-boundary discipline — load-
bearing for Finding #12 routing). DR-032 (canonical-
reference-layer / two-table bet-record shape — referenced
across Finding #1's three-way drift surfacing).

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
→ `2026-05-11 22:52 ACST`.
**Close:** same command → `2026-05-12 05:47 ACST`.

Same-workday open relative to Session 122 close (16m gap,
22:52 minus 22:36). No pause-and-resume explicitly flagged
by operator, but the ~7-hour wall-clock spans a day-rollover
through 00:00 ACST. The structural fact: session crossed
midnight; close timestamp is 2026-05-12 not 2026-05-11.

## Pre-flight checks

Drift-check at open: **clean**. `current_state.md` last-
updated 2026-05-11 22:36 ACST matched Session 122 close.
`sessions/SESSION_122.md` present (201 lines).
`v3_build_picture.md` last-updated 2026-05-11 22:36 ACST
matched Session 122 close. `.close_out_backups/` held
`SESSION_123_opening_prompt.md` from S122 close (not
consumed at S123 open — operator opened with "Open session
123" + the Code execution summary paste, same pattern as
S119 / S120 / S121 / S122 — fifth consecutive session of
non-consumption).

Build picture render condition fired mechanically at S123
open (artefact moved at S122 close, later than previous
open). **S119 sweep-candidate heuristic applied this open
(third clean application):** same-workday open + 16m gap
(well within ~1hr threshold) + operator-supplied substantive
content (Code execution summary paste at open). All three
heuristic conditions fired; build picture render skipped at
open per heuristic spirit. Third clean application now;
heuristic continues to await formalisation.

**Pre-W14 codebase review report empirically on disk
pre-triage:** `Desktop Commander:list_directory` on
`dr029/pre_w14_review/` at open confirmed
`codebase_review_report.md` (2864 lines) and
`pre_w14_review_brief.md` (591 lines). Code's between-
session execution closed at 2026-05-11 22:51 ACST per the
report header — between S122 close (22:36) and S123 open
(22:52), report landed in a 15-minute window. Re-validation
discipline (Cat 2): queued triage item verified on disk
before substantive work began.

**Open ritual silent-ritual rule (Cat 1): held this open
(broke the carry).** No step-by-step narration appeared in
operator-facing text at S123 open — orientation summary
delivered as a single combined block per Cat 1, no "Step 1
— Timestamp anchor" headers. Carry-candidate run was at
nine consecutive sessions through S122 (114–122);
**broken at S123, sweep-candidate carry pauses.** Single-
session holds are noted but not declared resolved — the
pattern needs multi-session confirmation before sweep
candidate is dropped.

## Session shape

Single-arc session — triage of `dr029/pre_w14_review/
codebase_review_report.md` (Code's 2864-line empirical
inventory) end-to-end, surfacing 16 drift findings in
plain operator language and routing each to one of four
outcomes:

- Document the asymmetry (amend the spec to match
  shipped) — Findings #1, #2, #3, #5, #12.
- Fold into already-planned workstream — Finding #4
  (ops log → W15).
- Park with tracking pointer — Findings #6, #7, #8, #9,
  #10, #11 (already-deferred items or operational-layer
  scope).
- Coordinated governance update sweep — Findings #13,
  #14, #15, #16 (admin / documentation cleanup folded
  into the same S124 governance pass).

Session phases:

**Phase 1 — Open + approach pick.** Pre-flight clean.
Operator pasted Code's execution summary at open. I
proposed the triage approach: read §11 ranked summary +
§12 self-assessment first to anchor, then verify against
§8 (DR drift table for all 32 DRs), §9 (21 missing-from-
spec items), §10 (20 missing-from-architecture items),
then spot-check pillar inventories §1–§7 where ranked
findings cite them. Operator picked "1" — confirmed my
approach + single-sweep cadence.

**Phase 2 — Read.** Read the report end-to-end across
seven `Desktop Commander:read_file` calls (chunked due to
file size, not split). Key sections covered in context:
§1 bet pillar inventory + verbatim DDL for `bets` and
`bet_legs`; §2 account pillar; §3 clients; §4 reconciliation
+ settlement; §5 UI; §6 ops + contracts + config; §7
tests; §8 DR drift table for all 32 DRs; §9 21 missing-
from-spec items; §10 20 missing-from-architecture items;
§11 ranked summary (5 high / 7 medium / 4 low); §12 self-
assessment.

**Phase 3 — High-severity findings walkthrough (5 findings).**
Per Cat 1 section-by-section walkthrough — one finding
per round, my recommended routing + reasoning + operator
call. Finding #1 (three-way drift) went through three
operator-driven iterations before settling — see "Finding
#1 evolution" sub-section below; this was the load-
bearing decision of the session. Findings #2–#5 routed
cleanly with one round each (one pressure-test from
operator on each — same "is the logic sound, what are
the risks" framing applied consistently across all five
high-severity findings).

**Phase 4 — Medium-severity findings batched walkthrough
(7 findings).** Per the tighter-default discipline agreed
in Phase 3, medium-severity batched with default routing
"park with tracking pointer, fix later, unless concrete
W14/W13/W12 impact". I drifted to over-technical surface
on the batch (operator flagged: "I didn't understand a
lot of what you wrote"); pulled back to plain-language
framing immediately. Operator confirmed: medium-severity
items are not high-risk, can be addressed per planned
schedule, just need to be flagged at the right time. All
seven routed.

**Phase 5 — Low-severity findings batched walkthrough
(4 findings).** Quick admin-paperwork batch — all four
folded into the coordinated governance update. No new
work, all documentation cleanup.

**Phase 6 — Recap + close-out routing call.** Recapped
all 16 routings, surfaced the two-option close (close
here vs push into governance update this session).
Recommended close + dedicated S124 for the governance
update on fresh tank. Operator confirmed: "Happy to close
the session here. Please make sure that you update all
the Carry 4 documentation and context vigilantly. I'm
going to be more vigilant around what we're doing so I
can course correct if I notice something else. I really
need you to make sure that everything carries forward,
especially around the technical detail as I don't
understand it. Please do a very robust close."

Operator's close instruction is **load-bearing for this
session record's length and detail target** — operator
explicitly named context-preservation as the critical
output of this close, with technical detail flagged as
the at-risk material. Length-over-target per Cat 5 / S120
rule applied without hesitation.

## Finding #1 evolution — full decision trail

This is the load-bearing technical decision of the
session. Operator pressure-tested twice before locking
the final routing; the evolution itself is the durable
context worth preserving.

**Initial framing:** Code's report surfaces a three-way
architectural drift on bet record shape:

- **Position A — architecture.md §A.2 + DR-027 (Session 19
  lock).** v3's bet data is a single append-only event log
  table carrying 23 different event types (bet_placed,
  bet_settled, bet_correction, free_bet_credited, etc.).
  Every state transition gets its own immutable row,
  linked by parent_event_id.
- **Position B — DR-032 (Session 90 lock).** Supersedes
  with a two-table shape: a bets row + N bet_legs rows.
  Write-once-mostly except for settlement-resolution
  fields. No event stream.
- **Position C — shipped reality (Sessions 100–116).**
  Matches DR-032's two-table shape but extends it: seven
  post-write-mutable columns on the bets row hold
  match_status, settlement_state, three count fields
  (dead_heat_count, removed_runner_count,
  unexpected_state_count), last_read_market_state JSON,
  reconciliation bookkeeping (last_reconciled_at,
  reconciliation_attempts).

No two positions agree.

**First pick (my initial proposal):** Document the
asymmetry as a permanent design call. Clean architecture.md
§A.2 to describe what's shipped — mutable bet records per
DR-032 plus separate event log tables for cash-flow /
promo / ops events. DR-027 amendment alongside. Don't
fix shipped to match spec (months of rework on tested
code with no operational benefit). Don't pretend DR-032
already says this (it doesn't — the seven mutable
columns are a real extension).

**Operator pressure-test 1:** "Are you sure this is going
to stand up for the long term in terms of accuracy? For
the most part, this doesn't sound like operational
impact, but it may have the impact on accuracy of
records and reconciliation and things like that."

The pressure-test was load-bearing — the initial pick
underweighted the audit-trail concern. The shipped pattern
stores current-state on the bets row and lets it mutate
as the bet's lifecycle progresses. Three transitions get
overwritten with no history kept:

- match_status (PROVISIONAL → PROVISIONAL_PENDING →
  FINAL_FULL / FINAL_PARTIAL / FAILED) — W6 worker.
- settlement_state (NULL → PENDING → SETTLED_WON /
  SETTLED_LOST / VOIDED / PROVISIONAL) — W6.5 worker.
- settlement_state → terminal via the W8 manual
  operator path (operator resolving provisional bets
  from the burst-review queue).

Once a transition happens, the previous state is gone.
There's one timestamp on the bet row (last_reconciled_at)
which is the latest worker pass, not "when did this bet
become SETTLED_WON". The W8 manual path takes an
operator_reason argument but doesn't persist it on the
bet row — so "why was that called SETTLED_LOST six
months ago" has no answer.

Settlement payout dollar amounts are computed-on-read
per DR-019 (no cash_returned column on bets) from
matched_stake × matched_price × dead-heat handling. If
any input gets corrected post-settlement — typo fix,
worker re-read, dead-heat adjustment — the historical
payout shifts retroactively. For reconciling against
bank statements two years later, that's the audit
failure mode.

In practice the mutation window is bounded — once a bet
hits FINAL_FULL + SETTLED_WON via the worker, the columns
sit still. But the W8 manual path is the unbounded case:
if a bet sits PROVISIONAL for a week, operator resolves
SETTLED_LOST, then later realises it was a dead-heat and
re-resolves, the second resolution overwrites the first
with no record of either decision.

**Second pick (revised):** Hybrid — keep the mutable
bets row as the materialised view, add a transitions
event log alongside for audit history. Concretely: bets
row stays as today (current state reads fast, all shipped
workers continue to work unchanged). Add a small
bet_state_transitions table — append-only, captures
every match_status / settlement_state /
manual_resolution transition with timestamp + actor
(worker name or operator marker) + reason. Future cash-
flow events (W14) sit alongside as their own parallel
event log table. Update architecture.md §A.2 to describe
"materialised-view-on-events" rather than "pure event
log" (§A.2 as written) or "pure mutable state" (shipped
as built). DR-027 amendment for materialised-view
pattern. Cost: ~200-300 LOC plus tests — small pre-W14
cleanup workstream OR folded into W14 itself.

**Operator pressure-test 2:** "I'm just worried that
we'll keep finding these little deviations and keep
latching on to new things to fix them."

Legitimate scope-creep worry. I acknowledged the worry
honestly: the hybrid was a software-shaped answer, but
"is this the absolute best approach with no risk" is
two questions, and I had not given complete answers to
either. Surfaced three risks for the hybrid:

- Scope creep (the exact worry — adding the transitions
  log opens "should ops_log work the same way, should
  promo events, should we standardise across the
  codebase"). Mitigation: lock transitions log to
  bet-state transitions only, no expansion until after
  W14/W13/W12 land.
- Implementation risk: small. Pattern is straightforward.
- Sequencing risk: moderate. Folding into W14 vs separate
  pre-W14 work changes W14's shape.

Recommended: proceed with hybrid for this finding (load-
bearing for W14's shape, can't be deferred without
affecting W14 directly), adopt tighter triage discipline
for the remaining 15 findings — default routing "park,
fix later" unless concrete W14/W13/W12 impact.

**Operator's third move — load-bearing context shift:**
"In reality, I don't need a rigorous audit trail. I
don't have an accountant, but this is not going to the
ATO, so this might also be overkill. This is just a
personal gambling assistant that isn't going to be
audited. ... if we have full faith in the process and
the functionality of the tool, that things won't get
lost and any anomalies will be able to be addressed
accurately and consistently, then perhaps we do just
leave it as it's been built."

That changed the load-bearing constraint. The audit-
trail argument was pricing in (a) defensibility against
external review (now off the table) and (b) internal
debuggability when something looks wrong (still on the
table but smaller). (b) shows up as "this bet shows
SETTLED_LOST but I remember it was a dead-heat" — without
a transitions log, the recovery path is worker stdout
+ Betfair historical re-query. Annoying, not catastrophic.
On a personal-scale operation with manual oversight,
misclassifications get caught within days, not years.

The shipped pattern is sound if three things hold:

1. Worker logic is correct — settlement transitions
   resolve to the right terminal state given the inputs.
   83 settlement tests behind this. Solid.
2. Inputs are reliable — Betfair's market_settlement API
   returns truthful results. Outside our control but
   decades of operational track record.
3. Mistakes get caught operationally before they
   compound — operator spots misclassified bets in
   normal review flow within reasonable window, W8
   burst-review queue gives the surface to fix them.

Without external audit obligation, the concern shrinks
to "what if I want to retroactively figure out what
happened" — real but bounded.

**Final pick (locked):** Leave as built. Document the
asymmetry. No transitions log, no hybrid, no new
workstream. Update architecture.md §A.2 to describe
what shipped (mutable bet records per DR-032 + separate
event log tables for cash-flow / promo events that
W14 / W13 will introduce). DR-027 amendment. If a real
audit need ever surfaces later (operator takes on a
partner, incorporates, regulatory shift), revisit then.
Adding a transitions log retroactively is doable as a
forward-only operation — would lose history before the
change but capture everything after.

**My acknowledged miss:** the audit-trail concern should
have been pressure-tested in my initial pick before
pricing in the hybrid. Operator's first pressure-test
correctly surfaced the gap; I should have asked about
audit obligation directly rather than defaulting to the
"safer" engineering answer. Noted as an operator-facing
discipline drift (should-have-asked-the-operational-
constraint-first); not encoded as a standing instruction
since it's situational, but worth carrying as awareness.

## What was delivered

Sixteen findings routed end-to-end. Listed by severity
band with the final routing per finding.

### High-severity (5)

1. **Three-way drift (DR-027 / DR-032 / shipped, seven
   mutable columns on bets).** Routing: **document the
   asymmetry, leave shipped as built.** Update
   architecture.md §A.2 to match shipped (mutable bet
   records per DR-032 + separate event log tables for
   cash-flow / promo / ops events). DR-027 amendment
   acknowledging bet records are exception to "everything
   is events". Full decision trail above in "Finding #1
   evolution" sub-section.

2. **Event-log spine absent (zero of 23 event types
   shipped).** Routing: **clean architecture.md §A.2 to
   describe per-domain event tables** (cash_flow_events,
   promo_events, ops_events) rather than single unified
   event log. W14 / W13 / W15 build against the clean
   shape. Rationale: per-domain pattern aligns with
   Finding #1's resolution (mutable bets row + separate
   event logs per domain), cleaner workstream boundaries,
   tighter indexes per table, schema flexibility per
   event type. Operator-relevant pressure-test
   acknowledged: the unified-log pattern is also valid
   in the abstract, but per-domain fits the operational
   shape better — modest scale (~150k events / 5 years),
   reads are mostly domain-scoped (balance derivation
   reads cash events; FB inventory reads promo events),
   no cross-domain reporting requirement.

3. **DR-026 market-context snapshot fields absent on
   bets.** Routing: **lock DR-026 amendment saying
   snapshot data lives in capture.db (analytical line),
   cross-referenced by betfair_market_id + placed_at
   timestamp at analysis time.** No columns added to
   bets. No build work. **Carry-forward dependency:**
   §2.4 Fix 4 cadence design (Betfair Streaming spec)
   must verify capture cadence is tight enough to
   bracket near-jump placements — operator places close
   to jump, so capture cadence + placement time delta
   must be small for the cross-reference to work
   reliably. If Fix 4 surfaces cadence isn't tight
   enough near jump, Finding #3's resolution is
   revisited. Rationale: aligns with DR-027/028 two-
   database discipline (operational owns bets, analytical
   owns market data); capture.db captures time-series
   higher fidelity than single-point snapshots; real
   edge-measurement happens in analytical layer querying
   capture.db anyway, not on bets table.

4. **DR-006 ops log absent (ops/__init__.py empty, no
   ops_log table).** Routing: **fold into W15 as already
   planned.** No new workstream. W15's brief (whenever
   it gets drafted) ships ops_events table per per-domain
   event-table pattern locked in Finding #2. Plain-
   language framing operator-confirmed: ops log is a
   debugging aid (system's notebook about its own runs,
   worker passes, retries, scheduler triggers) — useful
   when something looks weird and you want to reconstruct
   what happened, not urgent in normal operation. Betfair
   audit log (already shipped) covers highest-stakes
   external-action audit; worker stdout covers internal-
   system observability at lower fidelity. The ops_log
   gap is real but bounded; W15 is the natural home.

5. **DR-019 derived-state-on-read partially divergent.**
   Routing: **roll into Finding #1's resolution.** DR-019
   amendment lands alongside DR-027 amendment and
   architecture.md §A.2 cleanup as one coordinated
   governance update. DR-019 amendment text: "Derived
   state is computed on read for aggregates (balances,
   turnover totals, summary views). Per-entity mutable
   state (e.g. bet lifecycle state) is stored on the
   entity row as a materialised view; transitions are
   not historical (acceptable per personal-operation
   scale, no audit obligation). Event log tables exist
   per domain (cash_flow, promo, ops) for events that
   don't belong on a single entity row." Same shipped
   reality, viewed from a different DR. No standalone
   work.

### Medium-severity (7)

6. **DR-031 SQLAlchemy Core not used in store/.** Park
   with tracking pointer. Already explicitly deferred
   per W11 brief §5.3. No new action.

7. **DR-031 Alembic not adopted.** Park with tracking
   pointer. Already explicitly deferred per W10 brief
   §10.2 and DR-029 close-out. Alembic adoption is a
   separate later brief sequenced after W14 / W13 / W12.

8. **DR-025 hedge classification absent.** Park with
   tracking pointer **+ flag for revisit before W15
   brief drafting.** Hedge classification is meaningful
   analytical surface — for Strategy 2 (Price Booster),
   distinguishing "deliberately didn't hedge because
   price moved against me" from "tried to hedge and it
   failed" matters for measuring strategy performance.
   Not load-bearing for W14 / W13 / W12; belongs
   alongside operational-layer work that surfaces
   post-W15. Worth deliberate review before W15 to
   decide if spec'd 5-state shape still fits or if
   operational reality wants different states.

9. **DR-013 hygiene engine absent.** Park with tracking
   pointer. Operational-layer scope, sequenced well
   after W14 / W13 / W12. Shipped W11 accounts pillar
   carries this deferral explicitly.

10. **DR-017 burst-review + inline-validation partially
    divergent.** Park with tracking pointer. Operational-
    layer scope. Shipped W8 /provisional slice covers
    highest-urgency use case (operator resolving
    provisional bets in burst-review queue). Inline-edit-
    anywhere surface is downstream of operational-layer
    build.

11. **bets.account_at_book_id not a foreign key.** Park
    with tracking pointer. Already explicitly deferred
    per W11 brief §1.2. Identifier shape matches; FK
    enforcement is separate hygiene call once
    accounts_at_book is seeded with real data. No
    operational impact today (only person logging bets
    is operator, not typing garbage IDs). Worth small
    cleanup later when convenient.

12. **domain/pricing/ and domain/settlement/ empty
    (DR-030 layout drift).** Routing: **lock the
    inversion as deliberate, amend DR-030 to match
    shipped.** Folds into the coordinated governance
    update with #1 / #2 / #5. DR-030 amendment names
    workflows/bet_entry/v1/ as canonical home for
    pricing.py and settlement.py; domain/bets/ retains
    pure-type role. Tiny amendment, zero build risk
    (amending spec to match shipped, not reverse).

### Low-severity (4)

13. **Contract files not relocated to bethub-v3/
    contracts/.** Fold into coordinated governance
    update. Five-minute file move (vps_client_contract.md
    and betfair_client_contract.md from
    dr029/2_7_api_contract_versioning/ to
    bethub-v3/contracts/). Closes the DR-030 §Scope
    tracking pointer.

14. **accounts/ folder not in DR-030's locked layout.**
    Fold into coordinated governance update. One-line
    DR-030 amendment adding domain/accounts/ alongside
    existing three (domain/bets/, domain/pricing/,
    domain/settlement/).

15. **Bet-record fields not described in architecture.md
    (15-ish W4/W5/W6/W6.5/W9 shipped fields and enum
    values).** Fold into coordinated governance update
    as "architecture.md §A.3 and §A.6 expansion to cover
    W4-W9 shipped fields". Shipped, working, tested —
    drift is purely documentary. Fields to describe:
    cycle_id, entry_path, strategy_tag, price_source,
    betfair_bet_id, the match-state machine,
    dead_heat_count / removed_runner_count /
    unexpected_state_count, last_read_market_state,
    retry-with-backoff timings, MatchStatus.
    PROVISIONAL_PENDING and SettlementState.PROVISIONAL
    enum values.

16. **ProvisionalSettlementSurfacingPayload +
    apply_manual_operator_resolution not in
    architecture.md.** Fold into coordinated governance
    update as "architecture.md adds Burst Review section
    describing W8 shipped surface". Small write-up.

### Coordinated pre-W14 governance update (S124 primary work)

Single S124 session covering all eight findings that
require governance edits (Findings #1, #2, #3, #5, #12,
#13, #14, #15, #16 — eight items folded into one
coordinated pass).

**Scope:**

- **architecture.md §A.2 cleanup** — describe what
  shipped (mutable bet records per DR-032 + per-domain
  event log tables). Covers Findings #1, #2, #5.
- **architecture.md §A.3 / §A.6 expansion** — add the
  W4-W9 shipped fields and enum values to the spec.
  Covers Finding #15.
- **architecture.md Burst Review section** — describe
  W8 shipped surface. Covers Finding #16.
- **DR-019 amendment** — derived-state-on-read framing
  updated for materialised-view-on-entity-row pattern.
  Covers Finding #5.
- **DR-026 amendment** — snapshot data lives in capture.db,
  cross-referenced by Betfair identifiers. Covers
  Finding #3.
- **DR-027 amendment** — bet records are the exception
  to "everything is events"; mutable bet row alongside
  per-domain event log tables. Covers Findings #1, #2.
- **DR-030 amendment** — workflows/bet_entry/v1/ canonical
  home for pricing.py and settlement.py; domain/accounts/
  added to layout. Covers Findings #12, #14.
- **Contract file relocation** — vps_client_contract.md
  and betfair_client_contract.md move from
  dr029/2_7_api_contract_versioning/ to
  bethub-v3/contracts/. Covers Finding #13.

**Discipline for S124:** per Cat 3 empirical-verification-
before-editing-governance-artefacts, S124 starts by re-
reading every DR's current locked text (DR-019, DR-026,
DR-027, DR-030) plus architecture.md (§A.2, §A.3, §A.6)
plus the §6 version-history rows on each DR. Amendments
land as additive notes per existing DR convention (DRs
are immutable once locked; amendments appended as
separate notes, not edits to existing text). One
coordinated pass; verify with `Desktop Commander:read_file`
post-write per Cat 3 verify-every-write rule.

**S124 brief target:** likely brief-drafting-and-execute
in-session rather than commissioning Code (the work is
governance edits, not codebase changes). Single session,
no Code dispatch.

**What this unlocks:** W14 brief drafting after S124 close
against a clean spec. W14 ships cash_flow_events table per
per-domain event-table pattern. W13 and W15 inherit same
pattern when sequenced.

## Standing-instruction adherence check

- **Cat 1 silent session-open ritual** — **held this open
  (broke the 9-session carry).** No step-by-step
  narration in operator-facing text at S123 open.
  Sweep-candidate carry paused but not declared resolved
  pending multi-session confirmation.
- **Cat 1 silent session-close ritual** — held this close
  (this is being executed silently; only the post-Step 11
  closing summary will surface).
- **Cat 1 V3 build picture conditional render at open —
  spirit-of-the-rule heuristic** — *third clean
  application.* Same-workday open + 16m gap + operator-
  supplied substantive content (Code summary paste). All
  three heuristic conditions fired. Build picture render
  skipped at open per heuristic spirit. Heuristic working
  in practice across three consecutive sessions
  (S121–S123); formalisation candidate.
- **Cat 1 open-items delta — conditional** — held
  implicitly (no full delta render; cross-offs handled
  inline as items closed during the session — the entire
  pre-W14 review triage closed in one session).
- **Cat 1 plain-language operational framing** — **held
  through high-severity walkthrough; drifted on medium-
  severity batch, caught by operator and corrected
  immediately.** Operator flagged at medium-severity
  batch: "I didn't understand a lot of what you wrote".
  Pulled back to plain-language framing within one
  response (the "is that more or less correct?"
  operator-facing recap). Low-severity batch then
  delivered in plain language throughout. Drift signal
  + recovery within the same session is the discipline
  working as intended.
- **Cat 1 tighten default response register further** —
  *held in spirit, breached in practice on several
  responses.* Several responses in Phase 3 (high-severity
  walkthrough) ran medium-to-long, particularly Finding
  #1's three rounds of pressure-test and resolution.
  Each was warranted per Cat 5 length-over-target
  preference given the operator's explicit pressure-test
  ("are you sure this is going to stand up", "I'm just
  worried we'll keep finding deviations") — operator
  needed the detailed reasoning to make an informed call.
  Operator did not signal cognitive overload. Drift
  signal: monitor whether the pattern reinforces or
  whether next session's brevity holds.
- **Cat 1 escalate to detail only when warranted** —
  held. The "this deserves a little detail" prefix used
  explicitly **three times** this session (Finding #1
  pressure-test 1, Finding #1 pressure-test 2, Finding
  #4 "what an ops_log actually provides"). Each
  warranted by operator pressure-test surface.
- **Cat 1 inventory-first cadence on long technical
  reports** — *held — load-bearing this session.* The
  triage approach picked at Phase 1 was textbook
  inventory-first: read §11 ranked summary + §12 self-
  assessment first to anchor, then verify against §8 /
  §9 / §10, then spot-check pillars where ranked findings
  cite them. Every finding classified by operational
  impact in the high-severity walkthrough; plain-language
  framing applied consistently after the medium-severity
  drift was caught.
- **Cat 1 call-driven surfacing during section-by-section
  drafting** — *held.* Each finding surfaced exactly one
  operator-call: my recommended routing + reasoning,
  operator confirms or overrides. No multi-call surfacing
  per finding.
- **Cat 1 don't drift to alternatives when operator
  clear** — held. Operator said "1" at Phase 1 → triage
  proceeded directly. Operator said "Confirm" on Finding
  #1's third pick → moved directly to Finding #2.
  Operator said "Happy to close the session here" at
  Phase 6 → close-out fired directly.
- **Cat 1 unwind internal shorthand** — *partial breach
  caught by operator in medium-severity batch.* High-
  severity walkthrough used plain-language framing with
  DR numbers bracketed (DR-026, DR-019, DR-027) on use.
  Medium-severity batch drifted to denser technical
  surface — "SQLAlchemy Core", "import-linter", "FK
  enforcement" — operator flagged not understanding.
  Recovery: plain-language synthesis offered + operator-
  facing "is that more or less correct" recap. Low-
  severity batch then unwrapped throughout.
- **Cat 1 render review content with hard line wraps** —
  held this close (session record being written with
  ~60-70 char wraps).
- **Cat 1 decision-maker framing** — *held.* Each
  finding led with the call (my recommended routing)
  before reasoning. The triage opener ("Code's report
  lands clean ... no new architectural shocks") led
  with the headline interpretation before the per-
  finding walkthrough.
- **Cat 2 timestamp anchor** — open 22:52 ACST, close
  05:47 ACST (day-rollover to 2026-05-12). Both anchored
  via Desktop Commander start_process. No bash_tool
  drift this session.
- **Cat 2 Desktop Commander default** — held. All file
  reads via Desktop Commander. Session record writing
  via Desktop Commander:write_file. No `bash_tool`
  reflexes caught. No `create_file` reflex caught.
- **Cat 2 re-validate queued work-items at execution
  time** — *held — load-bearing this session.* Queued
  item ("triage codebase_review_report.md") re-validated
  at S123 open by listing `dr029/pre_w14_review/` —
  empirically confirmed the report on disk (2864 lines)
  before substantive triage began.
- **Cat 2 workstream-label / build-picture coherence at
  session close (S115 rule)** — *held*. New sub-stream
  "Pre-W14 governance update" surfaced this session and
  added to v3_build_picture.md at this close. Pre-W14
  review rolls from `in flight` to `done` (one-session
  carry begins). W11.1 drops from picture (S122 carry
  expired). W14 / W13 / W12 / W15 update from
  `blocked-on-pre-W14-review` to `blocked-on-pre-W14-
  governance-update`.
- **Cat 2 persist-to-scratch (drafted-but-not-assembled
  artefact content)** — N/A this session. No artefacts
  drafted in chat for later assembly; triage decisions
  captured directly in this session record.
- **Cat 2 structural-drift surfacing** — held. No
  structural drift to canonical artefacts this session
  (no edits to architecture.md, decisions.md, governance.md,
  vision.md, v3_data_requirements.md, standing_instructions.md).
  All eight planned amendments are scoped to S124, not
  authored mid-session.
- **Cat 2 day-rollover split-trigger** — *fired at
  close.* Session crossed local midnight ACST.
  governance.md §close-out §2 day-rollover trigger
  observed. Close-out executed as minimal close — no
  extra in-flight work layered on; session record +
  current_state.md + v3_build_picture.md update +
  opening prompt only. Coordinated governance update
  itself deferred to S124 per the trigger response.
- **Cat 3 empirical verification before editing
  governance artefacts** — *held.* Re-read
  `current_state.md`, `standing_instructions.md`,
  `project_context.md`, `SESSION_122.md` at open;
  `v3_build_picture.md` re-read pre-close to verify
  state-to-update; pre-W14 codebase review report read
  end-to-end. No edits proposed against memory.
- **Cat 3 create_file ban; verify every write** — held.
  Session record written via Desktop Commander:write_file;
  will verify post-write via Desktop Commander:read_file
  at Step 11. Opening prompt written via Desktop
  Commander:write_file. No create_file reflexes.
- **Cat 5 software calls don't punt** — *held.* Triage
  approach pick was my call (read §11/§12 first, verify
  against §8/§9/§10). Per-finding routing picks were
  my calls with reasoning; operator confirms or
  overrides. Finding #1's evolution involved two
  operator-driven revisions — but each pick along the
  way was a software-shaped call I owned, not punted.
- **Cat 5 cosmetic calls default to Claude's pick** —
  held. S124 brief-drafting-in-session-vs-Code-dispatch
  shape was named with one-line reasoning (governance
  edits, not codebase changes); operator did not
  challenge. Session record structure picked silently
  per S122 / S121 precedent.
- **Cat 5 length-over-target preference (S120 close)**
  — *load-bearing this session.* Finding #1's three-
  iteration evolution warranted full operator-facing
  detail at each round. This session record itself is
  length-over-target (~18-20K target vs 6-12K skill
  ceiling) per the operator's explicit close instruction
  ("update all the Carry 4 documentation and context
  vigilantly ... I really need you to make sure that
  everything carries forward, especially around the
  technical detail as I don't understand it"). The
  length is the protective discipline.
- **Cat 5 should-have-asked-the-operational-constraint-
  first (new sensitivity, not encoded)** — *drift
  signal surfaced this session.* My initial Finding #1
  pick defaulted to the safer engineering answer
  (transitions log) without asking the operator about
  audit obligation first. Operator's "no accountant, no
  ATO" context shift collapsed the audit-trail argument
  in one turn — context I should have asked for at the
  start. Worth carrying as awareness for future
  technical-decision picks where operator's operational
  context could shift the load-bearing constraint. Not
  encoded as a standing instruction this close
  (situational; would over-specify); held as sensitivity.

## Open items in (carry-forward)

Pointer-only — full list lives in `current_state.md`
"Open items" section after rotation.

**New from Session 123 (PRIMARY for Session 124):**

- **Coordinated pre-W14 governance update.** One S124
  session covering eight findings: architecture.md §A.2
  cleanup + architecture.md §A.3 / §A.6 expansion +
  architecture.md Burst Review section + DR-019
  amendment + DR-026 amendment + DR-027 amendment +
  DR-030 amendment + contract file relocation. Per Cat
  3 empirical-verification: S124 starts by re-reading
  every DR's current locked text, the §6 version-
  history rows, and architecture.md sections in scope.
  Amendments land as additive notes per existing DR
  convention. Verify post-write per Cat 3.

- **Hedge classification (DR-025, Finding #8) — revisit
  before W15 brief drafting.** Strategy 2 cycle
  measurement implications. Worth deliberate review
  before W15 to decide if spec'd 5-state shape still
  fits.

- **§2.4 Fix 4 cadence design dependency (Finding #3
  carry).** Fix 4 cadence design must verify capture
  cadence is tight enough to bracket near-jump
  placements. If Fix 4 surfaces cadence isn't tight
  enough, Finding #3's resolution (snapshot data lives
  in capture.db, cross-referenced) is revisited.

**Carried (lower priority, parking-lot):**

- **(Optional)** review W3 + W4 + W4.1 + W6 + W6.1 +
  W6.5 + W7 + W8 + W9 Code-shipped state — substantially
  subsumed by the pre-W14 review's pillar-by-pillar
  inventory (now triaged).
- **(Optional)** run a real `get_account_funds()` call
  against the live Betfair API at low risk.
- **(Lower priority, parking-lot)** Betfair API
  membership tier investigation. Awaiting BetWatch
  response.

**Tracked carry per operator instruction (carried from
S118 / S119 / S120 / S121 / S122):**

- **Alembic adoption.** Locked migration tool per
  DR-031, deferred to a separate later brief. Sequencing
  after pre-W14 governance update + W14 + W13 + W12.
  Confirmed parked at Finding #7 routing this session.

**Carried forward (sweep candidates, lower priority):**

- **Cat 1: silent session-open ritual narration drift
  pattern — sweep-candidate carry PAUSED.** Nine
  consecutive sessions (114–122) violated; **S123 held
  the rule cleanly.** One-session hold; carry resumes
  if drift recurs. Drop sweep-candidate status only
  after multi-session confirmation (e.g. clean S124 +
  S125).
- **Cat 1: build-picture conditional render at open —
  spirit vs mechanical rule. S119 origination, S120
  reinforcement, *S121 first clean application*, *S122
  second clean application*, *S123 third clean
  application.* Heuristic working in practice across
  three consecutive sessions; formalisation candidate
  strengthened.
- **Cat 2: `.close_out_backups/` cleanup convention is
  informal** (S119 / S120 / S121 / S122 / S123
  reinforcement — fifth consecutive). Opening prompts
  not consumed at open in five consecutive sessions;
  close-side Step 9 has been the de facto canonical
  sweep. Either tighten open ritual or accept close-
  side Step 9 as canonical.
- **Cat 2 / Cat 3:** `str_replace` reflex extends the
  `create_file` failure mode pattern (carried from
  S115/S116; no new instances S119–S123).
- **Cat 2:** broaden persist-to-scratch rule to cover
  operator-provided source documents (carried from
  S116; reinforced S119 / S120 / S121 / S122 / S123 —
  operator pasted Code's end-of-session summaries at
  open in five consecutive sessions).
- **Cat 2 / Cat 3:** bash_tool reflex for non-
  filesystem-touching commands like `date` (carried
  from S121; no reproduction at S122 or S123 — all
  timestamp anchors used Desktop Commander
  start_process correctly).
- **Cat 4:** divergence-capture-or-fix in go-forward
  documentation (carried from S121). The pre-W14
  governance update at S124 embodies this priority
  concretely. Pattern may warrant elevation to standing
  instruction after S124 governance update lands.

**New from Session 123 (sensitivity not encoded):**

- **Cat 5 should-have-asked-the-operational-constraint-
  first** — surface operational context first on
  technical-decision picks where operator's situation
  could shift the load-bearing constraint. Substrate:
  Finding #1 evolution — defaulted to the safer
  engineering answer (transitions log) without asking
  about audit obligation; operator's "no accountant, no
  ATO" context collapsed the argument. Held as
  sensitivity for now; not encoded as standing
  instruction (would over-specify).

- **Codebase grounding before substantive briefs on
  long-running build arcs** (carried from S122,
  reinforced this session). The pre-W14 codebase review
  proved its worth — 16 findings surfaced, all triaged
  cleanly, no hidden landmines in shipped code, all
  drift either conscious deferral or already-known
  gaps. Worth considering as a periodic discipline.
  Held as sensitivity until S124 governance update
  lands; pattern then up for elevation.

**Carry-forward operational (Sessions 108 / 109 carry):**

- Settings-area cadence follow-up brief — open; waits
  on operational experience.
- Greyhound operational constraint verification — open.
- `betfair_adapter.py` single-file mypy cleanup — low
  priority.

## Open items out (closed Session 123)

- **Triage `dr029/pre_w14_review/codebase_review_report.md`**
  — closed. All 16 findings routed (5 high / 7 medium /
  4 low). One coordinated pre-W14 governance update
  scoped for S124 covering 8 of the 16 findings; 7
  medium-severity items parked with tracking pointers
  (already-deferred or operational-layer scope); 1
  finding (#4 ops log) folded into already-planned W15.

- **Pre-W14 codebase review sub-stream** — closed.
  Inventory and drift surfacing complete. One-session
  carry in build picture begins this close.

- **W12 architectural-drift unresolved (carried from
  S122)** — closed. Three-way drift (DR-027 vs DR-032
  vs shipped) routed to "document the asymmetry, leave
  shipped as built" per Finding #1 final pick. DR-027
  + DR-019 amendments + architecture.md §A.2 cleanup
  land at S124.

## Session close state

- **Rebuild folder root:** structurally unchanged. No
  new directories. No new governance files. No edits
  to architecture.md, decisions.md, governance.md,
  vision.md, v3_data_requirements.md,
  standing_instructions.md, project_context.md this
  session.
- **`current_state.md`:** rotated at this close. "Last
  updated" → 2026-05-12 05:47 ACST.
- **`sessions/SESSION_123.md`:** written (this file).
- **`sessions/SESSION_122.md`:** unchanged this session.
- **`v3_build_picture.md`:** updated at this close —
  pre-W14 review rolls from `in flight` to `done`
  (one-session carry begins); W11.1 drops from picture
  (S122 carry expired); new sub-stream "Pre-W14
  governance update" enters as `in flight` with
  next-milestone label naming the eight findings
  scoped; W14 / W13 / W12 / W15 update from
  `blocked-on-pre-W14-review` to `blocked-on-pre-W14-
  governance-update`. W16 / W17 / W18 / P1 / P2
  unchanged. "Last updated" stamp bumped to close
  timestamp.
- **`vision.md`:** not read this session; no edits.
- **`architecture.md`:** not read this session (all
  drift findings are surfaced in Code's report with
  spec citations; the actual architecture.md read for
  S124 amendment drafting happens at S124 open per Cat
  3 empirical-verification rule); no edits.
- **`decisions.md`:** not read this session; no edits.
- **`v3_data_requirements.md`:** not read this session;
  no edits.
- **`standing_instructions.md`:** not read in full this
  session (single read at open per Cat 2); no edits.
- **`.close_out_backups/`:** `SESSION_123_opening_prompt.md`
  deleted at this close (Step 9 sweep — was not consumed
  at S123 open). `SESSION_124_opening_prompt.md` written.
- **Project knowledge base:** no re-upload action
  required this close (no `standing_instructions.md`
  edits this session).

## Forward routing

**Confirmed with operator: close session here.** Operator
says: "Happy to close the session here. Please make sure
that you update all the Carry 4 documentation and context
vigilantly. I'm going to be more vigilant around what
we're doing so I can course correct if I notice something
else. I really need you to make sure that everything
carries forward, especially around the technical detail
as I don't understand it. Please do a very robust close."

**Session 124 primary work:** the coordinated pre-W14
governance update. Single session covering eight findings:

1. architecture.md §A.2 cleanup (mutable bet records
   per DR-032 + per-domain event log tables) — Findings
   #1, #2, #5.
2. architecture.md §A.3 / §A.6 expansion (W4-W9 shipped
   fields + enum values) — Finding #15.
3. architecture.md Burst Review section (W8 shipped
   surface description) — Finding #16.
4. DR-019 amendment (derived-state-on-read framing
   updated for materialised-view pattern) — Finding #5.
5. DR-026 amendment (snapshot data lives in capture.db,
   cross-referenced) — Finding #3.
6. DR-027 amendment (bet records exception to
   "everything is events") — Findings #1, #2.
7. DR-030 amendment (workflows/bet_entry/v1/ canonical
   for pricing.py and settlement.py; domain/accounts/
   in layout) — Findings #12, #14.
8. Contract file relocation (vps_client_contract.md and
   betfair_client_contract.md to bethub-v3/contracts/)
   — Finding #13.

**S124 discipline:** Cat 3 empirical-verification-before-
editing rules apply hard at S124 open — re-read every DR
and architecture.md section in scope, verify §6 version-
history rows on each DR, draft amendments as additive
notes per DR convention (not edits to locked text),
verify post-write per Cat 3 verify-every-write rule.

**Possible Session 124 shapes:**

- **Clean governance update → S124 ships all eight
  scope items → W14 brief drafting begins S125.** Most
  likely shape if S124 runs smoothly.
- **Heavy governance update → S124 ships partial scope
  → split remaining to S125 per Cat 2 deferral-as-
  deliverable.** Possible if any amendment surfaces
  scope ambiguity (e.g. DR-027 amendment text needs
  multi-round operator pressure-test like Finding #1
  did this session).
- **Pivot to operator-redline review of routings.**
  Operator explicitly flagged: "I'm going to be more
  vigilant around what we're doing so I can course
  correct if I notice something else." If operator
  revisits any of S123's 16 routings at S124 open, the
  session may pivot to re-triage before governance
  update drafting begins.

**Between-session operator actions:**

- None new. The codebase review report is on disk;
  triage outcomes are captured in this session record;
  S124 work is governance edits drafted in Claude Chat,
  not Code-dispatched.
- No `standing_instructions.md` re-upload action
  required this close (no edits this session).

**Sweep candidates at S124 open (carried from S123):**

- Cat 1 silent session-open ritual narration — carry
  paused (S123 held cleanly); monitor S124 + S125 for
  multi-session confirmation before dropping sweep
  candidate.
- Cat 1 build-picture conditional render heuristic —
  third clean application S123; formalisation
  candidate strengthened.
- Cat 2 `.close_out_backups/` cleanup convention — five
  consecutive sessions of close-side sweep; pattern
  established.
- Cat 4 divergence-capture-or-fix priority — S124's
  governance update is the concrete realisation of
  this priority.
- New from S123: Cat 5 should-have-asked-the-
  operational-constraint-first sensitivity (Finding #1
  evolution substrate).

## Length note

This session record runs long (~22K characters,
substantially over the 6-12K skill target) by deliberate
operator instruction. Operator's close direction explicitly
named context-preservation as the critical output, with
technical detail flagged as the at-risk material: "I
really need you to make sure that everything carries
forward, especially around the technical detail as I don't
understand it." Length-over-target preference per Cat 5
applied without hesitation. The Finding #1 evolution
sub-section + the per-finding routing sub-sections + the
coordinated governance update scope are the load-bearing
detail the operator needs preserved across the S123 → S124
gap; trimming any of those would defeat the close's
explicit purpose.
