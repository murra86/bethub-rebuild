# Brief — Racing-page frontend pre-cutover fixes

**Type:** Surgical fix to known issues (single bounded Code
session). Read-write, named anchors only.
**Repo:** `bethub-v3` (local Mac), branch `main`. Working tree
**dirty by design** (~62 `git status --short` entries at the
S166 review). Dirty-tree discipline applies — see §4 / §9.
**Source report:** `interface_triage/racing_page_review_report.md`
(Session 166, read-only review; 12 findings). Every anchor below
traces to that report; the operator triaged it at S166.
**Commissioned:** Session 167.
**Test runner:** `uv run pytest` (the repo is a `uv` project on
Python 3.12; bare `python3 -m pytest` fails at collection — it
lacks `httpx`).

---

## §1 — What this brief is and is not

This brief commissions **four frontend fixes** to the racing
page and the Betfair hedge modal, all display / form-state, with
**no reach into the bet-placement path**. It is a single bounded
Code session.

- Code executes the four fixes against the named anchors, adds
  the named regression test, updates the fixtures the conversion
  change moves, and produces one report.
- Surprises become **findings in the report**, not mid-session
  pings to the operator and not chased fixes.
- Any remediation beyond the named fixes routes to the next
  operator-Claude triage session, **not** Code's report.
- `placement.py` and the bet-placement / lay POST path are **out
  of scope** and must not be touched (see §9).

## §2 — Why this work exists

The Session 166 triage of Code's read-only racing-page review
locked a pre-cutover fix set, split into three briefs by reach.
This is the **frontend brief** — the cluster that touches only
display and form-state, with zero bet-path reach, so it is the
cleanest to land and hand off first. The other two (cycle-capture,
launcher) are separate briefs.

The four fixes and their source findings:

- **Fix A** — bonus-winnings promo EV is silently broken (report
  **F1**, HIGH), plus a deliberate free-bet conversion drop from
  70% to 65% across the whole tool (folds in the misleading modal
  "70%" label **F2** and the triplicated `0.7` constant **F4**).
- **Fix B** — the double runner number (report **Q3**): drop the
  app's row-count index, show Betfair's saddlecloth number only.
- **Fix C** — soft-odds cell pre-fills with the Betfair back
  price (report **#7**): blank it so the real soft price is typed
  fresh.
- **Fix D** — log-bet panel doesn't clear on race switch (report
  **#8 / F7**): auto-clear on switch + a manual clear button.

## §3 — Pre-reads

Required, in order:

1. `interface_triage/racing_page_review_report.md` — the source
   review. §6 / Q1 (the EV engine), §7 / Q2 (the modal), Q3
   (runner number), §10b (soft odds), §10c (log-bet clear), and
   the Findings table (F1–F12) are the load-bearing sections.
2. The source files named per fix in §5 below.

Reference-only (read if an anchor is ambiguous, not required):

- `ui/web/src/promos/presets.ts` — promo config shape (promo
  types, `return_pct`, `return_type`, `insured_positions`).
- `ui/web/src/ev/evEngine.ts` — the EV engine (the bonus-winnings
  function, the conversion constant, the fixtures).

## §4 — System access

- **Mac filesystem, `bethub-v3` repo, READ-WRITE**, limited to
  the named anchors in §5. No edits outside them.
- **Dirty working tree (~62 entries) is the operator's in-flight
  work — NOT drift.** Read `git status --short` at session start
  to capture the baseline. Do **not** run any git mutation:
  no `git add`, `commit`, `stash`, `restore`, `checkout`
  (file-targeted), or `reset`.
- After each edit, run `git diff <file>` to confirm only the
  intended change landed. At session close, run `git status
  --short` and confirm the dirty-file list is unchanged in shape
  (only the files this brief edits should show new diff content;
  no files added to or dropped from the dirty set unexpectedly).
- If any named anchor's line numbers have shifted from the
  report's references (the tree is live), **confirm the anchor by
  symbol/function name before editing** — line numbers below are
  hints from the S166 review, not guarantees.
- **Tests:** `uv run pytest` only. Capture the pass/fail baseline
  before any edit and after all edits.
- All timestamps in the report: Adelaide local (ACST/ACDT) per
  DR-021 (timestamp anchoring, Adelaide local time).

## §5 — The four fixes

Each fix is independent; edit anchors do not overlap. Do them in
the order below (Fix A first — it is the consequential one and
the only one touching the test suite).

### §5.1 — Fix A: bonus-winnings EV wiring + 70→65 conversion drop

Three coupled changes (all share the free-bet conversion maths).

**A1 — wire the bonus % into the bonus-winnings EV (report F1).**

The defect: `evBonusWinnings` (`evEngine.ts` ~362-393) reads the
bonus basis from `promo.bonus_pct ?? promo.bonusPct ?? 0`, but
both call sites build the promo object with **`return_pct` only**
and never set `bonus_pct`/`basis`. So `bonusPct` resolves to 0,
the bonus adjustment vanishes, and bonus-winnings Promo EV
silently collapses to raw EV. (The engine's maths is correct —
it just never receives the bonus.)

Call sites (the anchors):
- `OddsTable.tsx` ~205-212 — the table-column `promoEV(...)`
  object.
- `Racing.tsx` ~150-154 — the log-panel snapshot `promoEV(...)`
  object.

Fix: at **both** call sites, add to the promo object passed to
`promoEV`:
- `bonus_pct: promoConfig.return_pct ?? 100` — for a
  bonus-winnings promo the operator's configured `return_pct` IS
  the bonus % (a 100%-winnings promo = `return_pct: 100`).
- `basis: 'winnings'` — the operator's agreed formula is the
  winnings basis: `effective odds = SoftOdds + bonus% ×
  (SoftOdds − 1)`, valued through the free-bet conversion and
  frozen at the promo's max-bonus cap. `evBonusWinnings` already
  implements this branch (`basis === 'winnings'`); pass it
  explicitly rather than relying on its default.

These two fields are inert for every other promo type (only
`evBonusWinnings` reads them), so adding them to the shared
object is safe. `return_type` already flows through both call
sites — keep it; it is what makes the free-bet conversion apply
(see A2). Do **not** alter `evInsurance`'s use of `return_pct`
(insurance reads it as the refund %, a different meaning on a
different promo type — leave untouched).

**A2 — drop the free-bet conversion 70% → 65%, single constant.**

Three hard-coded `0.7` sites today (report F4):
- `evEngine.ts:41` — `export const DEFAULT_FB_CONVERSION_RATE =
  0.7` (the canonical one; default param of `evInsurance`,
  `evFreeBet`, `evBonusWinnings`).
- `evEngine.ts:541` — a **second** local `const FB_CONVERSION =
  0.7` inside `bonusWinningsEffectiveOdds`.
- `HedgeModal.tsx:18` — a local `const FB_CONVERSION = 0.7`
  (display-only; see A3).

Fix: collapse to the single canonical constant and change its
value.
- Set `DEFAULT_FB_CONVERSION_RATE = 0.65` at `evEngine.ts:41`.
- In `bonusWinningsEffectiveOdds`, replace the local
  `FB_CONVERSION` with `DEFAULT_FB_CONVERSION_RATE` (reference
  the module constant; delete the local).
- In `HedgeModal.tsx`, replace the local `FB_CONVERSION` with the
  imported `DEFAULT_FB_CONVERSION_RATE` from `evEngine` (so the
  modal label, A3, reads the one true value).

After A2 there must be **no remaining literal `0.7` / `0.70`**
acting as a free-bet conversion rate anywhere in
`ui/web/src`. (The Harville exponents `0.77 / 0.62 / 0.48` are
unrelated — leave them.)

**A3 — fix the misleading modal label (report F2).**

`HedgeModal` displays *"v2 FB conversion 70% applied"* (~347-348)
but applies **no** conversion in its lay-sizing maths (the hedge
is sized to the full free-bet face value's winnings, correctly).
The label overstates what the modal does. Fix: make the label
accurate — either drop the "applied" claim, or render it as
context only (e.g. state the planning conversion rate without
implying the modal's lay size uses it), driven off
`DEFAULT_FB_CONVERSION_RATE` so the number can never again drift
from the engine. Wording is Claude/Code's call; the constraint
is that it must not claim a conversion the modal math doesn't
perform.

**A4 — regression test (REQUIRED — the bug is currently masked).**

The existing `evEngine` unit test passes `bonus_pct: 100`
directly, so it exercises the engine but **not** the UI wiring —
a green suite does not catch F1. Add a test that reproduces the
real call path: build the promo config the UI builds (with
`return_pct` set and `bonus_pct` ABSENT) and assert that
bonus-winnings Promo EV reflects the bonus (i.e. is **not** equal
to raw EV at the same price). This test must FAIL against the
pre-fix wiring and PASS after A1.

**A5 — update conversion-shifted fixtures.**

The 70→65 change moves any fixture whose expected value depends
on the free-bet conversion (the insurance free-bet fixtures, e.g.
`evInsuranceFB2nd3rdAt2_5`, and any bonus-winnings free-bet
fixture). Recompute and update the affected expected values to
the 0.65 basis. `evFreeBet` returns a % of face via the lay
hedge and does **not** apply the conversion constant — confirm
whether its fixture moves before editing it (it likely does
not). The report must list every fixture changed and its
old→new value.

### §5.2 — Fix B: runner number → Betfair saddlecloth only (Q3)

Today the runner cell renders two numbers — `{idx + 1}.
{runnerName}` (`OddsTable.tsx` ~226-229) — where `idx+1` is the
app's 1-based array position (market-book order) and the second
number is the saddlecloth number Betfair embeds at the front of
`runner_name`. They diverge after scratchings or when book order
≠ cloth order. Bets are unaffected (they key on the stable
`selection_id`), so this is a misread-the-runner hazard, not a
data/settlement risk.

Fix: drop the app's `idx+1`; show **Betfair's saddlecloth number
only**, so the displayed number matches what every other book
shows.

Anchor: `OddsTable.tsx` ~226-229 (render only).

Build-time call for Code (Claude-territory — make it, don't ask
the operator): source the saddlecloth number from the cleanest
available place. Order of preference:
1. A discrete catalogue field if one carries the cloth number
   cleanly (`sort_priority` exists on the catalogue but is an
   ordering hint, **not** guaranteed to equal the cloth number —
   do not assume it does).
2. Otherwise parse the leading number from the Betfair
   `runner_name` string (the convention for AU racing).

Fallback: if the number cannot be cleanly resolved for a runner,
render the name without a leading number rather than showing a
wrong or app-index number. Never fall back to `idx+1`.

**Display-only · frontend-only.** Does not touch the bet-record
key.

### §5.3 — Fix C: soft-odds blank default (#7)

Today the Soft Odds cell defaults to the Betfair back price:
`const soft = manualOdds[id] ?? back ?? 0` (`OddsTable.tsx`
~196), surfaced as `soft || ''` (~254), mirrored for the
panel/modal in `Racing.tsx` ~123-127 (`softOddsForSelected`).
The operator wants it **blank** so the real soft-book price is
typed fresh each time.

Fix: drop the `?? back` fallback from the **default** so the cell
starts blank (EV columns then render a dash until a price is
typed — the report confirms every downstream reader is guarded:
EV needs `soft > 1`, log-panel `canSubmit` blocks on `soft ≤ 1`,
the hedge modal returns `laySize = null` until set; nothing
silently miscalculates).

**Preserve** the stepper's own fallback `snapSoft(soft || back
|| 1.5)` (`OddsTable.tsx` ~244, ~270) so the +/- stepper still
works from a blank cell — that fallback is internal to stepping,
not the displayed default. Do not blank it.

Anchors: `OddsTable.tsx` ~196 (default) and ~254 (input value);
`Racing.tsx` ~123-127 (`softOddsForSelected`).
`ev/softOddsLadder.ts` is unaffected. **Frontend-only.**

### §5.4 — Fix D: log-bet clear + carry-over (#8 / F7)

Two real defects in the log-bet panel:
- On a race switch, `softOdds` and `snapshot` **don't clear** —
  `LogBetPanel`'s reset effect (~92-100) is keyed on
  `selectedRunner.selection_id` and guarded by `if
  (selectedRunner)`; on a race switch `selectedRunner → null`, so
  the guard is false and the old values persist into the new
  race.
- `stake` **never resets** on a runner or race switch at all (it
  only clears on successful submit / free-bet toggle-off).
- There is **no manual clear control**.

Fix, both halves:
1. **Auto-clear on race switch** — extend the reset so `softOdds`,
   `snapshot`, and `stake` all clear when the race (market)
   changes, not only when the runner's `selection_id` changes.
   Key the effect on the `marketId` prop (in addition to the
   existing runner key) and include `stake` in what it resets.
   `Racing.tsx` ~89-95 already clears the lifted state
   (`manualOdds`, `selectedRunner`) on race switch — this fix
   covers the panel-local state it doesn't reach.
2. **Manual clear button** — add a control that resets the
   panel-local form state (soft odds, snapshot, stake; leave
   account/book selection as-is unless trivially included).

Anchors: `LogBetPanel.tsx` ~78-100 (local state + reset effect;
add a clear handler) and `Racing.tsx` ~89-95 (already resets
lifted state — reference only, no change needed there unless the
marketId prop must be threaded to the panel). **Frontend
form-state only — the `POST /racing/bets` contract is
untouched.**

## §6 — Sequencing within session

The four fixes are independent (no shared edit anchors).
Suggested order:

1. **Fix A** first — it is the consequential one (real EV
   correctness) and the only one touching the EV engine + test
   suite. Land it, get the new test green, confirm fixtures.
2. **Fix C** (soft-odds default) — also in `OddsTable.tsx` /
   `Racing.tsx`, so naturally batched with A's files.
3. **Fix B** (runner number) — `OddsTable.tsx` render line.
4. **Fix D** (log-bet clear) — `LogBetPanel.tsx`.

Code may reorder if a different order is cleaner, but Fix A goes
first.

## §7 — Empirical verification

- **Test baseline:** run `uv run pytest` before any edit; capture
  pass/fail counts. Run again after all edits; the suite must be
  green (the pre-existing frontend-lint / vite-8 parking-lot
  items are not introduced by this brief — note them if they
  surface, don't fix them).
- **Fix A:** the new A4 test fails pre-fix, passes post-fix.
  List every fixture A5 changed with old→new value. Show one
  worked bonus-winnings example in the report: a configured
  bonus-winnings promo now yields a Promo EV strictly different
  from raw EV at the same soft price.
- **Fixes B / C / D:** these are UI-runtime behaviours. Code
  verifies by source reasoning + any component-level test that
  exists, and **describes** the expected on-screen behaviour in
  the report. Full live-UI confirmation (launch the app, switch
  races, watch the cells clear) is the **operator's** post-Code
  validation step, not Code's — name it as such in the report.
- **Dirty-tree integrity:** `git status --short` at close shows
  the same dirty-file set as at open, plus the diff content only
  in this brief's edited files.

## §8 — Output spec

Single report file: `interface_triage/frontend_fixes_report.md`.

Structure:
- Header — repo, branch, dirty-tree entry count at open and
  close, test baseline before/after, single-session confirmation.
- One section per fix (A / B / C / D) — what changed, the exact
  files + final line anchors, the `git diff` confirmation, and
  for A the new test + the fixture old→new table.
- A "what the operator must validate live" section — the UI
  behaviours Code could not runtime-confirm (B/C/D on-screen,
  and a live bonus-winnings EV spot-check).
- Self-assessment — coverage, confidence, anything deferred as a
  finding, scope-discipline confirmation.

Length: ~150-300 lines. Range, not a hard line.

The report does **not** contain: recommendations beyond the four
fixes; any cycle-capture or launcher work; any bet-path change;
any new promo-config UI input (the 65% stays a single constant
per the S166 decision, not a UI field).

## §9 — Hard limits (NOT in scope)

- **No bet-placement path changes.** `placement.py`, the
  `/racing/bets` and `/racing/lay` POST handlers, `place_bet` /
  `place_lay`, and the bet-record builder are **untouched**. Every
  fix here is display / form-state.
- **No schema or migration changes.** No DB columns, no
  `store/schema` edits.
- **No cycle-capture work** — the free-bet↔qualifier link, the
  `cycle_id` UI wiring, and the realised-conversion field are a
  **separate brief**. Do not touch them here even though Fix A is
  in the same EV engine.
- **No launcher / auth / throttle work** — separate brief.
- **No back-bet build in the modal** (mapped out-of-scope in the
  report; LAY-only stays).
- **No durability work** — the in-memory audit sink (F8) and the
  place-then-commit window (F11) stay parked.
- **No git operations** of any kind (§4).
- **Named anchors only** — no drift into adjacent code "while
  we're here". The Q1/§10 dead-code items (e.g.
  `calculateLayFieldProbabilities`) are **not** removed under
  this brief.
- **Named pieces of debt untouched** — no test-framework
  overhaul, no Alembic adoption, no orchestrator refactor.
- If the work doesn't fit one bounded session, that's a
  **finding**, not a continuation past budget.

## §10 — What happens after Code's session

The next operator-Claude session reads
`frontend_fixes_report.md`, confirms the four fixes landed clean
and the test went green, and surfaces anything Code flagged as a
finding. The **operator** then does the live-UI validation
(switch races, watch the panel clear, eyeball a bonus-winnings
EV). Code does **not** write the next brief.

Remaining pre-cutover briefs after this one: **cycle-capture**
(reaches bet storage; records-look already done at S167 —
`interface_triage/cycle_capture_records_look.md`) and
**launcher** (throttle-state-to-disk + port-override). Then W16
cutover scoping.

## §11 — Cross-references

- **Source report:** `interface_triage/racing_page_review_report.md`
  (S166) — findings F1, F2, F4, Q3 / #7 / #8 / F7.
- **Session record:** `sessions/SESSION_166.md` (the triage that
  locked this set) and SESSION_167 (this brief's drafting).
- **DRs invoked:** DR-019 (derived state on read — the EV /
  soft-odds display surface), DR-025 (hedge classification — the
  modal label), DR-030 (v3 module boundaries — the `ui/web/src`
  touch-lists), DR-021 (timestamp anchoring, Adelaide local).
- **Excluded / parked:** cycle-capture (separate brief), launcher
  (separate brief), audit-sink durability F8 + place-then-commit
  F11 (parked), modal back-bet build (out of scope), the filter
  "bug" F3 (dropped at S166 — did not reproduce), the streaming
  F-series and 200-market over-subscription (separate parking
  lot).

*End of brief.*
