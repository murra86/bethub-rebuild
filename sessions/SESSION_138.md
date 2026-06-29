# Session 138 — W12 ship-report triage: clean ship; lay-side gap routed to DR-025 / before-W15; forward to W15

**Opened:** 2026-05-21 16:06 PDT (Vancouver — temporary
timezone display window active until 2026-06-08;
canonical project zone remains Adelaide per DR-021;
ACST equivalent 2026-05-22 08:36 ACST).
**Closed:** 2026-05-21 16:34 PDT (ACST equivalent
2026-05-22 09:04 ACST).
**Wall-clock active session:** ~30 minutes.
**Tool routing:** Claude Chat (report triage; empirical
verification reads against the v3 codebase at
`/Users/tim/Desktop/Projects/bethub-v3/`). No Claude Code
dispatch this session — W12 already shipped out-of-session
before this open.
**Governing DRs invoked:** DR-019 (read-time derivation
discipline — W12 governor), DR-021 (timestamp anchoring —
Vancouver display override active), DR-025 (hedge
classification — lay-side routing target), DR-032
(canonical bet-record / bet-leg shape), DR-030 + S124
amendment (module-boundary contracts), DR-027/028 (two-DB
boundary).

## Anchor

```
# Session-open command (Vancouver per temporary
# instruction):
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-05-21 16:06 PDT

# Session-close command:
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-05-21 16:34 PDT
```

## Pre-flight checks

Session-open ritual ran per `bethub-session-open` skill.
Required reads completed (`current_state.md`,
`standing_instructions.md` in full, `project_context.md`,
`SESSION_137.md`, plus the load-bearing W12 report).
Pre-flight directory listing confirmed clean rebuild
folder root — 13 .md files plus openapi.json, no
phantoms. `.close_out_backups/` held
`SESSION_138_opening_prompt.md` as expected from S137's
close.

**Drift-check (Step 5 of open ritual):** clean.

- (a) `current_state.md` "Last updated" 2026-05-17 23:58
  PDT matched `SESSION_137.md` "Closed:" timestamp.
- (b) `SESSION_137.md` present, non-empty (577 lines).
- (c) `v3_build_picture.md` "Last updated" 2026-05-17
  23:58 PDT — correctly updated at S137 close (W12
  transitioned `in flight` → `awaiting-code-execution`).
  Render condition therefore TRUE; build picture rendered
  inline at open.

**Code ran between sessions.** Operator dispatched the
locked W12 Code prompt almost immediately after S137
close; Code's ship report landed 2026-05-18 00:47 PDT
(861 lines). The report was the load-bearing read for
S138 triage.

## Session shape

S138 was the W12 report-triage session, matching the
"Code ships clean" forward branch pre-agreed at S136/S137.
Code's report self-declared **shipped clean**: 809 tests
passing (753 baseline + 56 new W12 tests, within the
50–78 expected band), all three code-quality gates green
(import-linter 5/5 contracts kept, mypy clean, ruff
clean). The §6.1 alignment pass passed all seven specified
checks and surfaced two additional Cat 5 mechanical
findings (H, I), both scope-reductions, both applied
during the build — no halt fired.

Triage ran the inventory-first cadence (Cat 1): all eight
of Code's findings inventoried and classified by
operational impact. Exactly one had operational
consequence — the §7.3 CASH-4 lay-side gap (Finding b#4).
That one was investigated at length against the live v3
codebase (not taken on the report's word), discussed with
the operator in plain gambling terms, and routed. The
other seven were code-shape or tooling matters with no
operational consequence — handled as Claude-territory
software calls per Cat 5.


## What was delivered

**1. W12 confirmed a clean ship.** Code's report verified
against its own gates: 809 tests passing (+56 net), 5/5
import contracts kept, mypy and ruff clean. All six
read-side derivations in place (Location 1 at-book
balance, Location 2 holder cash holding, operation
net-flow, free-bet inventory, AccountCare warning state,
promo journey), the 7-template + 5-warning reference seed
populating idempotently, and both substrate step-zeros
(§5.1 slug-flip, §5.1b funding_source removal) landed.
No W12 halt; no W12.1 residual blocking the ship.

**2. Lay-side finding (b#4) investigated and routed.**
The report flagged that the Location 1 balance derivation
handles the Betfair lay side of a hedge on a back-bet
basis. Verified empirically against the v3 codebase
rather than trusting the report:

- `workflows/balances/v1/balance_derivation.py` —
  `_read_bet_rows_for_account_at_book` selects only from
  the `bets` header table (matched_stake, matched_price,
  settlement_state); it does not join `bet_legs`, so it
  never sees a leg's role (HEDGE vs SOFT_BOOK) or side
  (LAY vs BACK). `_bet_cash_return` applies back-bet maths
  (matched_stake × matched_price on a win; full
  matched_stake refund on void) with no liability and no
  commission branch.
- `architecture.md` §A.6 — the section the derivation
  cites — specifies cash_returned = matched_stake ×
  matched_price against settlement state. It does not
  fold in a Betfair lay, and it **explicitly defers hedge
  state to post-W15** (DR-025 hedge-classification model;
  no `hedge_state` column on the bets row yet, no
  auto-classification flow, revisit-before-W15 flag
  already on the books).
- `domain/bets/__init__.py` — the lay/hedge maths the
  operator developed (LegRole.HEDGE, BetSideTag LAY/BACK,
  Construction A `LAY_AGAINST_BACK` vs B
  `BACK_AGAINST_BACK`, HedgeSoftBookStakeKind CASH vs
  FREE_BET driving the formula numerator, "math review
  §1/§2/§3") is intact in the domain model. It is
  entry-side construction maths, not what W12's read-side
  balance derivation touched.

**Conclusion:** not a regression or lost logic. The
lay-side cash-folding was deliberately parked (hedge state
is post-W15 per §A.6 + DR-025); W12 faithfully implemented
§A.6 as written. Code's "finding" re-surfaces the known
DR-025 deferral from the balance angle.

**Operator clarification noted.** Operator's instinct that
the impact is confined to the free-bet-conversion side may
hold *operationally* (if Betfair lays are only ever placed
to convert a triggered free bet, letting the qualifying
insurance bet ride for the win). The code itself does not
restrict the gap to free bets — any lay leg is mis-handled
— but the operator's actual lay usage is the ground truth.
Operator did not need to settle this to route; flagged for
the DR-025 revisit.

**Routing (operator-confirmed):** no action now. The fix
rides on the **DR-025 hedge-classification revisit, which
is the standing "before W15 brief drafting" flag** — that
revisit decides the lay substrate (liability + commission
fields the bet row doesn't yet carry). The balance fix
itself is then a small follow-on (anticipated W12.1) once
that substrate lands. Flag recorded so it ties to the
existing carry-forward item rather than a loose thread.

**Clarification carried for the flag:** W12 derives cash
*balances*, not a P&L figure (no profit/loss function
among the six). The gap surfaces as a wrong cash balance
on the Betfair-side account, not a wrong P&L line. Open
operational sub-question for the DR-025 revisit: whether a
Betfair lay is logged as its own `bets` row (entry_path
`racing_screen_hedge` → read and mis-mathed as back) or
only as a `HEDGE` leg under the soft-book bet (never read
by this derivation → Betfair-side cash simply unreflected).
Both are wrong, differently; which applies depends on the
operator's hedge-recording shape.

**3. Hedge / Betfair modal — confirmed unaffected.** The
modal is a bet-entry surface (computes the offset lay
stake at entry). W12 built no UI and is purely read-side;
the two share no code. The modal's offset maths is the
entry-side logic preserved in the domain model. Caveat
carried: the v3 hedge modal is not built yet (racing
screens are W17+), so the modal in use today is v2's,
untouched by the rebuild and not inspected this session.
Optional follow-up if ever wanted: verify v2's hedge-stake
maths separately.


**4. Remaining seven findings — Claude-territory software
calls made (no operator action).**

- **§5.1b scope reduction (Finding-H).** The adapter /
  repository / schema edits the brief enumerated were
  no-ops in the shipped substrate (`funding_source` lived
  only in the JSON payload inside `domain/cash_flow`).
  Code applied the actual edits needed (domain + tests).
  Accepted as shipped — same operational outcome.
- **§5.9 store re-export skipped (Finding-I).** The brief's
  optional re-export step would have broken the shipped
  `store-pure` import contract. Step was explicitly
  optional; correctly skipped. Accepted.
- **§7.4 slug-flip count drift.** Brief expected ≥3
  `warning_type_id: str` anchors; substrate has 2. Code
  aligned mechanically. Accepted — count drift only.
- **`_ensure_adelaide_local` duplication (Finding-5).**
  Known since S134; no new duplication. No action.
- **Cross-workflow lint carve-out (Finding-D / §10 q1).**
  The `workflows-independent` import contract names only
  `bet_entry` and `burst_review`, so W12's
  balances→promos derivation import passes by omission
  rather than explicit carve-out. Call: make it explicit
  for maintainability — **folded into the W15 Code brief
  as a one-line housekeeping item** (not commissioned
  separately; no operational impact).
- **Smoke script deferred (Finding-7 / §10 q3).** Accepted
  Code's recommendation — the 56 parametrised tests are a
  higher-signal surface than a standalone smoke script
  that exercises each function once. No action.
- **Python 3.11→3.12 tooling (Finding-8 / §10 q4).** The
  repo requires 3.12+; running `python3 -m pytest` on a
  system 3.11 interpreter throws collection errors.
  Call: **add a one-line venv anchor to future Code
  opening prompts** ("run `.venv/bin/python -m pytest`;
  project requires 3.12"). Folded into the W15 Code brief
  prep.

**5. Forward route confirmed.** Clean ship → S139 revisits
DR-025 hedge classification (the before-W15 flag; where
the lay substrate is decided), then drafts the W15 brief
(operations log — the `ops_events` per-domain event-table
workstream, structurally a third instance of the
W14/W13 pattern). W12.1 lay-balance fix is downstream of
the DR-025 substrate decision.

## Standing-instruction adherence check

- **Cat 1 silent open-ritual ritual — PARTIAL.** No
  numbered "Step N" headers this open (improvement over
  S137's explicit step headers). But brief connective
  step-narration still present between reads ("Now the
  required reads", "Now the pre-flight directory listing",
  "Now the most recent session record") — the rule is
  zero operator-facing ritual text, only the combined
  orientation at the end plus anomalies. Self-flagged.
  Better than S137 but not clean; streak not yet
  re-established. S139 open is the next watch point.
- **Cat 1 inventory-first cadence on long reports** —
  honoured. Eight findings inventoried, classified by
  operational impact; only the operationally-relevant one
  (lay-side) surfaced in plain gambling language; the
  seven code/tooling findings handled silently as Claude
  territory.
- **Cat 1 plain-language operator-call framing** —
  honoured. Lay-side gap explained in real-world hedge/
  insurance terms; "back bets fine, Betfair lay side
  wrong" framing.
- **Cat 1 escalate-to-detail only when warranted** —
  honoured. Flagged "this deserves a little detail" before
  the deep lay-side answer; tightened hard to two
  sentences when the operator asked for a summary.
- **Cat 1 build-picture conditional render** — honoured.
  Rendered at open (correct — stream moved at S137 close);
  18 consecutive clean applications S120–S138.
- **Cat 1 tool routing always stated** — honoured (Chat
  triage; W15 named for Code; W12.1 named as downstream).
- **Cat 1 "no draft text unless it earns operator time"** —
  honoured. No draft artefacts surfaced; triage delivered
  as conversation.
- **Cat 3 empirical verification before asserting** —
  honoured strongly. The lay-side claim was verified
  against the live v3 codebase (balance_derivation.py,
  architecture.md §A.6, domain/bets) rather than trusting
  Code's report summary. Surfaced a sharper picture than
  the report (header-only read vs leg ignorance; §A.6
  deferral lineage).
- **Cat 5 make software calls; don't punt** — honoured.
  All seven minor findings resolved as Claude-side calls
  (accept-as-shipped × 4; two folds into the W15 brief;
  one accept-Code-recommendation). None punted to the
  operator.
- **Cat 3 write_file chunking** — honoured (session record
  in append chunks within tolerance).
- **Cat 2 session-close opening prompt produced** —
  honoured (Step 8).


## Open items in

- **S139: DR-025 hedge-classification revisit, then W15
  brief drafting.** DR-025 (the five-terminal-plus-one-
  transient hedge classification model) is the standing
  before-W15 flag. The revisit decides whether the spec'd
  state shape still fits and — load-bearing for the
  lay-side gap — defines the lay substrate (liability +
  commission fields on the bet row). W15 (operations log /
  `ops_events`) brief drafting follows, since `ops_events`
  ships the `hedge_state_classification` audit events.
- **W12.1 lay-balance fix (anticipated, downstream).**
  Once the DR-025 revisit lands the lay substrate, a small
  surgical brief patches `_bet_cash_return` /
  `_read_bet_rows_for_account_at_book` to handle lay legs
  (liability release + winnings net of commission). Not
  commissioned yet; tracked.
- **Two housekeeping folds for the W15 Code brief:**
  (a) make the `workflows-independent` import carve-out
  explicit in `.importlinter`; (b) add a `.venv/bin/python`
  (Python 3.12) anchor line to the Code opening prompt.
- **Vancouver timezone instruction.** Active through
  2026-06-08; revert to Adelaide anchors at first session
  open on or after that date. Carried at top of
  `current_state.md`.

## Open items out

- **W12 dispatch to Claude Code** — done. Code executed
  the locked brief out-of-session, shipped clean.
- **W12 report triage (S138 primary)** — done. Clean ship
  confirmed; eight findings classified; one operational
  finding routed; seven handled as software calls.
- **Lay-side finding (b#4)** — triaged and routed to the
  DR-025 revisit / before-W15; no action this session.

## Carried forward

Sensitivity items from S137 carry. Updates:

- **Cat 1 silent open-ritual narration** — partial
  improvement at S138 (no numbered step headers; brief
  connective narration remained). Was 3-of-13 broken
  entering S138. Streak still not re-established; S139
  open is the watch point. Promotion-to-encoded-rule
  candidacy still weakened.
- **Cat 1 build-picture conditional render** — 18
  consecutive clean (S120–S138). Strengthening.
- **Cat 3 empirical-verification-before-asserting** —
  strong positive instance this session (verified the
  lay-side claim against live v3 code, surfaced a sharper
  picture than the report). Strengthening.
- **Cat 5 make-software-calls-don't-punt** — seven clean
  applications this session. Strengthening.

## Carry-forward operational (long-standing)

- **DR-025 hedge classification revisit** — now PRIMARY
  for S139 (was parking-lot; promoted by the W12 lay-side
  routing + the standing before-W15 flag).
- Settings-area cadence follow-up brief — open.
- Greyhound operational constraint verification — open.
- `betfair_adapter.py` single-file mypy cleanup — low
  priority.
- `cascaded_at_settlement_state` closed-enum revisit —
  forward-tracked for W8 brief drafting.
- Hedge classification (DR-025, Finding #8 S123) —
  promoted to PRIMARY S139 per above.
- §2.4 Fix 4 cadence design dependency (Finding #3 S123)
  — carries.
- Alembic adoption — sequenced after W12 + W15.
- (Optional) real `get_account_funds()` call against live
  Betfair API at low risk.
- (Lower priority) Betfair API membership tier
  investigation — awaiting BetWatch response.
- (W12.1) per-bookmaker cross-account spot-check view —
  carries alongside the lay-balance fix.

## Session close state

- **Rebuild folder root:** clean, 13 .md files plus
  openapi.json. No phantom files. Vancouver timezone
  instruction carried at top of `current_state.md`.
- **WIP:** None — triage was conversational; no in-session
  artefacts pending assembly. No scratch-draft persistence
  required (no draft content produced this session).
- **v3 codebase:** unchanged by this session (read-only
  verification reads against
  `/Users/tim/Desktop/Projects/bethub-v3/`). W12's shipped
  state stands as Code left it.
- **`.close_out_backups/`:** contains
  `SESSION_139_opening_prompt.md` after sweep removed the
  stale `SESSION_138_opening_prompt.md`.
- **`sessions/`:** this file (`SESSION_138.md`).
- **Project knowledge base:** no upload action required —
  `standing_instructions.md` unchanged this session.

## Forward routing

**Confirmed with operator** — S138 triaged Code's clean
W12 ship report; W12 ships as built. S139 revisits DR-025
hedge classification (the before-W15 flag, and where the
lay substrate is decided), then drafts the W15 brief
(operations log / `ops_events`). The W12.1 lay-balance fix
is downstream of the DR-025 substrate decision. Operator
instruction at close: "no action required... close out the
session and prep the next session for our next workphase."

## Close-out notes

S138 was a tight, well-bounded triage session (~30 min
wall-clock). The standout was the empirical lay-side
investigation: rather than accept Code's report summary,
the v3 code was read directly, which reframed the finding
from "a bug" to "a known deferral surfacing from a new
angle" and tied it cleanly to the existing DR-025
before-W15 flag. The Cat 1 silent-open-ritual remains the
one self-flagged drift — improved but not clean. No
governance events; no structural drift; no standing-
instruction edits.
