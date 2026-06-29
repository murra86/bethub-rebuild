# Session 144 — W12.2 triaged and closed clean; FB-inventory failures diagnosed (test wiring, not a bug); W17 unblocked

**Opened:** 2026-06-10 13:41 ACST.
**Closed:** 2026-06-10 14:04 ACST.
**Tool routing:** Claude Chat (W12.2 report triage; FB-inventory
failure diagnosis via live test runs + code reads). No code
edits; no governance edits beyond close-out rotation.
**Governing DRs invoked:** DR-025 (hedge classification — six
states; S139 amendment: commission = Betfair per-market
`marketBaseRate`, 8% fallback, table retired), DR-026/§A.10
(Betfair canonical for market facts), DR-019 (derive-on-read),
DR-030 (module boundaries), DR-031 (tech stack), DR-021
(Adelaide anchors; no overrides).

## Anchor

```
# Session-open:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-06-10 13:41 ACST

# Session-close:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-06-10 14:04 ACST
```

## Pre-flight checks

Open ritual ran per `bethub-session-open`, silent (fourth
consecutive clean). Required reads completed
(`current_state.md`, `standing_instructions.md` in full,
`project_context.md`, `SESSION_143.md`, the W12.2 report read
from disk, the locked W12.2 brief). Pre-flight directory
listing: clean root, expected files, no phantoms.
`.close_out_backups/` held `SESSION_144_opening_prompt.md` as
expected (operator opened with "Open session 144").

**Drift-check (Step 5): clean.**
- (a) `current_state.md` "Last updated" matched
  `SESSION_143.md` "Closed:" (2026-06-10 13:22 ACST).
- (b) `SESSION_143.md` present, non-empty (282 lines).
- (c) `v3_build_picture.md` updated at S143 close (streams
  moved); render condition TRUE — build picture rendered.

**Same-workday open** (~19 min after S143 close) — tight recap
delivered per Cat 1.

**W12.2 report existence verified on disk at open**
(`dr029/w12_balances/w12_2_commission_construction_report.md`,
393 lines) and read as a required read. Brief SHA `2928122d` /
487 lines re-verified on disk before triage. The operator's
in-chat Code summary arrived in the open message and matched
the report — no discrepancy.

## Session shape

A short, clean session (~23 min wall-clock). Item 1: W12.2
report triage — closed clean in the first exchange. Item 2:
the carried FB-inventory failure check, executed as the
spare-budget item per the S143 routing — diagnosed in three
tool rounds (live test run + derivation read + test-constant
greps). Operator delegated routing to Claude's recommendation
("Go with your recommended action"); close with W17 brief
drafting as S145 primary.

## What was delivered

**1. W12.2 triaged — CLOSED CLEAN, no W12.2.x follow-up.**
Code's report (393 lines) verified against the locked brief
(487 lines, SHA `2928122d`, re-verified on disk). Headline:
both pieces landed — (a) commission sourced from Betfair's
per-market base rate (static table retired;
`commission_from_market_base_rate` + `DEFAULT_COMMISSION_RATE`
shipped; §9.7 catalogue read extended backward-compatibly with
`market_base_rate`; ÷100 normalisation at the translation
boundary only), (b) construction plumbing wired
(`HedgeEntryRequest.commission_rate` + `construction` with
side⇔construction validator; `_hedge_inputs_from` forwards
both, construction total-derived from `side`;
`_modal_data_snapshot` extended; record builder populates
`commission`). Post-baselines: pytest 894/2 (+13 net vs 881/2;
both failures the pre-existing FB-inventory pair),
lint-imports 5 kept / 0 broken, `git status` 45 lines
character-identical pre/post. §7.3 spot-check verified the
load-bearing chain end-to-end: LAY hedge with c=0.05 valued on
the W12.1 lay branch with the stored rate; BACK hedge with
None → NULL → 8% read-side fallback. **W12.1 F§5.2 is closed
operationally — every new hedge stores true per-market
commission and its back/lay tag; the lay-balance maths is live
on new bets.** Existing rows untouched per §9.

Findings inventory (5), none with operational consequence:

- **f#1 contract version label** — brief named v1.3; running
  contract was already at v1.4, Code landed v1.5 preserving
  monotonic ordering. Correct call; brief-drafting lesson
  (verify the running contract version at grounding time). No
  action.
- **f#2 missing §9.7 translation entry** — the catalogue path
  had no `_translation.py` wiring pre-session; without it the
  new field was unreachable end-to-end. Code added the minimal
  equivalent (~90 lines: regex, five projections, ÷100
  boundary) within the brief's explicit permission. Other
  surfaces verified wired; no wider sweep needed.
- **f#3 / f#4 stale docstrings** — two references to the
  retired `_COMMISSION_TABLE`
  (`workflows/balances/v1/balance_derivation.py` L159;
  `tests/workflows/balances/v1/test_balance_lay_branch.py`
  L291). Behaviour correct; one-line tidy-ups → maintenance
  list.
- **f#5 diff co-mingling** — `_translation.py`'s diff includes
  pre-existing W3 §9.8 work; W12.2 footprint recorded
  precisely. Informational only.

One trivial report discrepancy: 393 lines vs the 200–350
target; content load-bearing; accepted per the
length-bends-to-detail rule.

**2. FB-inventory pre-existing failures DIAGNOSED — test
wiring, NOT a production bug.** Carried open item executed
with spare budget. Empirical chain: ran the two failing tests
live (`test_balance_free_bet_inventory_surfaces`,
`test_inventory_single_freebie_available` — both assert a
just-credited free bet appears in inventory; both get an empty
inventory back); read `compute_free_bet_inventory` in
`workflows/promos/v1/promo_derivations.py` (the read-time
expiry filter compares `face_value_expiry` against real
wall-clock `_now()` — by design, per the W12 brief §5.6, to
accommodate background-job lag); grepped both test files'
time constants. **Root cause: both test files freeze
`REF_TIME = datetime(2026, 5, 18, 12:00, ADL)` and credit a
free bet expiring `REF_TIME + 86400s` (= 2026-05-19 12:00),
but the derivation checks expiry against the real clock — so
the tests passed when written and became time-bombs on
2026-05-19.** The production filter behaviour is correct
(expired free bets must not surface as available — Strategy 1
inventory accuracy depends on it). Fix shape: freeze the clock
inside the tests (monkeypatch `_now` / inject a clock) or make
test expiries relative to real now; the former is the proper
fix. Routed to the maintenance list with this diagnosis; no
standalone brief. **Baseline note for future briefs: expected
pytest baseline remains 894 passed / 2 failed until the test
fix lands; after it lands the baseline goes fully green
(896/0).**

**3. Forward routing settled — W17 unblocked.** With W12.2
closed, the W11–W15 band is complete; W17 (racing market
pages) is no longer blocked and its brief drafting is S145's
primary (Claude Chat work — planning + brief; Code executes
later). The Alembic sequencing gate ("after W12 + W15") is
also now open — surfaced as a W17-adjacent consideration, not
auto-actioned (DR-031 deferred it; whether to adopt before or
after W17 is a brief-drafting-time call).

## Standing-instruction adherence check

- **Cat 1 silent open-ritual — CLEAN.** Zero step narration;
  single combined output. Fourth consecutive clean
  (S141–S144).
- **Cat 1 calendar-calibrated recap** — honoured
  (same-workday, tight recap).
- **Cat 1 build-picture conditional render** — honoured
  (rendered; streams moved at S143 close). 24 consecutive
  clean S120–S144.
- **Cat 1 open-items delta** — honoured (rendered; delta
  existed).
- **Cat 1 inventory-first cadence on Code's report** —
  honoured (five findings inventoried + classified; none
  operator-consequential; routing surfaced for visibility).
- **Cat 1 plain-language framing** — honoured (triage verdict
  and FB-inventory diagnosis both delivered in operational
  language; technical detail kept to this record).
- **Cat 2 timestamp anchors / required reads / pre-flight /
  drift-check** — honoured.
- **Cat 3 empirical verification** — honoured: report read
  from disk over trusting the in-chat summary; brief SHA +
  line count re-verified pre-triage; FB-inventory diagnosis
  ran the failing tests live and read the derivation + test
  constants from disk rather than reasoning from memory.
- **Cat 3 Desktop Commander discipline** — honoured; no
  `create_file`; chunked session-record writes; live test
  runs via `start_process`.
- **Cat 5 make-software-calls-don't-punt** — honoured: triage
  verdict, FB-inventory root-cause call and fix shape, and
  maintenance-list routing all made and surfaced, not punted.
  The one operator call surfaced (close now vs spare-budget
  check) was answered with "go with your recommendation" —
  executed the check then closed.
- **Operator-confirmed forward routing (Session 42)** —
  honoured: operator delegated to the stated recommendation
  (W17 brief drafting as S145 primary) in their close-message.

## Open items in (carry to S145)

- **W17 brief drafting — PRIMARY S145.** Racing market pages:
  port v2's true-EV + promotional-EV display; Betfair
  price-movement indicators on selections; redesign where new
  features need to land, retain v2 structure where it works.
  Expect a grounding pass (v2 racing-page code + v3 UI
  scaffold state) before drafting. Alembic-adoption timing is
  a named consideration during drafting (gate now open).
- **Maintenance list (one new entry):** FB-inventory test
  time-bomb fix — freeze the clock in
  `tests/workflows/promos/v1/test_promo_derivations.py` and
  `tests/workflows/balances/v1/test_balance_derivation.py`
  (REF_TIME 2026-05-18; real-clock expiry filter). Sits
  alongside: W12.2 f#3/f#4 stale `_COMMISSION_TABLE`
  docstrings; `store/schema/bets.py` row-factory asymmetry
  (W15 f#2); `.importlinter` documentation note (W15 f#1);
  `betfair_adapter.py` mypy cleanup. The list is now five
  small items — a bundled micro maintenance brief is becoming
  worthwhile; surface as an option during W17 drafting or any
  light session.

## Open items out (closed/advanced S144)

- **W12.2 report triage** — CLOSED (clean; no W12.2.x;
  commission sourcing + construction plumbing live).
- **W12.2 workstream** — DONE (one-session carry; drops at
  S145 close). W12 band complete.
- **FB-inventory failure check** — CLOSED as an investigation
  (diagnosis recorded; fix is a maintenance-list item, not an
  open question).
- **W15 workstream** — dropped from the picture at this close
  per the one-session carry rule.

## Session close state

- **`dr029/w12_balances/`** — brief + report both final; no
  further W12.2 artefacts expected.
- **v3 codebase** — untouched this session (Chat-only).
- **`current_state.md`** — rotated to S144 close.
- **`v3_build_picture.md`** — updated (W12.2 → done; W15
  dropped; W17 → in flight; W17 milestone updated).
- **`.close_out_backups/`** — `SESSION_145_opening_prompt.md`
  written; stale `SESSION_144_opening_prompt.md` swept.
- **No edits** to `decisions.md`, `standing_instructions.md`,
  or any other canonical truth.

## Forward routing

**Confirmed with operator** ("Go with your recommended
action" — the stated recommendation being W17 brief drafting
as S145 primary, with the FB-inventory check executed first
on spare budget). S145 opens on W17 (racing market pages)
brief-drafting work: grounding reads of v2's racing pages and
the v3 UI scaffold, then scope settlement with the operator
(what ports, what redesigns), then the brief. Claude Chat
work throughout; Code executes the locked brief
out-of-session later.

## Close-out notes

Shortest session of the arc (~23 min) and a clean one: W12.2
closed the W11–W15 band, and the FB-inventory mystery carried
since pre-W12.1 resolved to a benign test time-bomb in three
tool rounds. The W12 representation precedent held (single
row through brief → execution → triage; surgical sub-streams
W12.1/W12.2 carried and dropped per the one-session rule).
The maintenance list crossing five items is the only
emerging-shape note — bundling them is cheap and keeps the
list from silently growing.
