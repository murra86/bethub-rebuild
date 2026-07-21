# Brief — Cash-lay back-stake pre-fill fix (HedgeModal)

_Drafted: 2026-07-01 09:23 ACST (Session 210) · Status: LOCKED — approved for Code handoff_
_Target codebase: `bethub-v3` · Governing feature: W17.1 §5.4 quick-lay tool (HedgeModal)_

## 1. What this brief is and is not

This is a **surgical fix** to a single known defect: in cash mode the quick-lay modal pre-fills the back-stake box from the runner's soft *odds* (a price) instead of a dollar *stake*, so a cash lay placed without the operator overtyping the box is sized off the price and comes out under-sized.

It is a single bounded Code session with a **review-first gate**: Code independently re-derives the defect and scans for other impacts BEFORE editing anything (§5 Phase A). If the review confirms the diagnosis and finds no impacts beyond the two named anchors, Code proceeds to the edits (§5 Phase B). If the review contradicts the diagnosis, or surfaces any consumer/impact not named in this brief, Code STOPS before editing, records the finding in the report, and ends the session for operator-Claude triage.

It is not a refactor, not a redesign of the modal, not a change to lay sizing, lay pricing, the liability guard, or the free-bet/bonus-winnings seeding paths. Surprises become findings, not improvised fixes.

## 2. Why this work exists

The quick-lay modal (`HedgeModal`, W17.1 §5.4) is the panel where a lay is placed and logged. It runs ~99% in free-bet mode (correct) and rarely in cash mode. Session 210 operator-Claude diligence traced an under-sizing defect on the cash path to its root cause: the call site in `Racing.tsx` passes the operator's manual soft odds into the modal's `initialBackStake` prop, and the modal seeds the cash back-stake box from that prop. The lay *price* is independent (live-polled from Betfair) and is unaffected; only the pre-filled back-stake figure is wrong, and only in plain cash mode. This brief commissions the fix the operator signed off on: **blank the cash-mode back-stake box** so the operator types the real stake, mirroring the free-bet path's correct behaviour, while preserving the bonus-winnings $50 default and the free-bet face-value seeding.

## 3. Pre-reads

Code reads these before starting, in order:

1. `ui/web/src/components/HedgeModal.tsx` — the modal carrying both edit-relevant anchors and the seeding/guard logic.
2. `ui/web/src/routes/Racing.tsx` — the call site that supplies `initialBackStake`.
3. `ui/web/src/components/HedgeModal.test.tsx` — existing coverage (reference-only; informs the verification step).
4. `ui/web/src/routes/Racing.flow.test.tsx` — existing coverage (reference-only).

This brief itself is the spec. No other reads are required.

## 4. System access

- **Mac filesystem, read-write**, scoped to the two named anchor files only.
- Working tree confirmed **clean** on `main` at HEAD `b0f05b0` (S209) as of 2026-07-01 09:23 ACST. No dirty regions intersect the edits.
- No database access. No VPS. No Betfair API calls.
- All timestamps in the report in Adelaide local time (ACST/ACDT) per DR-021.

## 5. Scope

### Phase A — Independent review and impact scan (NO edits in this phase)

Code performs its own verification before touching any file. The goal is to confirm this brief's diagnosis from first principles and to rule out impacts beyond the two anchors. Record each result in the report.

A1. **Re-derive the defect.** In `Racing.tsx`, confirm the `HedgeModal` `initialBackStake` ternary: the cash branch passes `Number(manualOdds[hedgeRunner.selection_id])` (a price) when a manual odds value exists, else `0`. Confirm `manualOdds` is the operator's soft odds map (`Record<string, number>`), i.e. a price, not a stake.

A2. **Confirm the seed path.** In `HedgeModal.tsx`, confirm `initialBackStakeForMode` returns `initialBackStake` unmodified on the plain-cash branch (the branch that is neither free-bet nor bonus-winnings), and that the `backStake` state is initialised from it. Confirm this is what populates the back-stake `<input>`.

A3. **Confirm the two cash sub-paths are isolated.** Confirm the free-bet branch (`roundDownToIncrement(initialBackStake, FB_STAKE_ROUNDING_INCREMENT)`) and the bonus-winnings branch (`BONUS_WINNINGS_CASH_DEFAULT_STAKE`, currently $50) are independent of the plain-cash branch and will not be touched by the planned edits.

A4. **Enumerate every consumer.** Find every reader of: (a) the `initialBackStake` prop inside `HedgeModal`, (b) the `backStake` state, (c) `manualOdds` in `Racing.tsx`. Confirm that blanking the plain-cash seed and changing the call-site cash branch to `0` does not break any other consumer (e.g. lay sizing, `onPlaced` face-value handoff, FB quick-buttons, the §5.7 FB-skip fallback display).

A5. **Confirm the empty-stake safety property.** Confirm that with an empty back-stake box, `laySize` is `null` (the `backStakeNum <= 0` guard) and both `attemptPlace()` and `runPlacement()` bail on `laySize == null` — i.e. a blank box cannot place a zero-stake lay; it blocks until a real stake is entered.

**GO/NO-GO gate.** If A1–A5 all confirm as above and no additional impact surfaces → proceed to Phase B. If any check contradicts the diagnosis, or A4 surfaces a consumer this brief did not anticipate → STOP, do not edit, write the finding to the report, end the session.

### Phase B — The edits (two anchors, dependency order)

B1. **`Racing.tsx` — stop piping odds into the stake prop.** In the `HedgeModal` `initialBackStake` ternary (cash branch, ~lines 339–341), replace the `manualOdds`-derived value with a literal `0`. The free-bet branch (`fbFaceValue ?? 0`) is unchanged. Net effect: the cash path no longer hands a price to a stake-named prop.

B2. **`HedgeModal.tsx` — blank the plain-cash seed.** Two coordinated edits, both confined to the plain-cash path:
  - In `initialBackStakeForMode` (~line 176), change the plain-cash branch from `return initialBackStake` to `return 0`, so the modal never seeds the plain-cash box from the incoming prop regardless of caller. The free-bet and bonus-winnings branches are untouched.
  - In the `backStake` state initialiser (~lines 186–188), when `initialBackStakeForMode` is not greater than 0, emit `''` (blank) for cash mode and keep `'0.00'` for free-bet mode. Concretely: `initialBackStakeForMode > 0 ? initialBackStakeForMode.toFixed(2) : initialMode === 'cash' ? '' : '0.00'`. This blanks plain cash, preserves the bonus-winnings `$50` (which is `> 0`, so it renders `'50.00'`), preserves free-bet face-value seeding, and leaves the free-bet-skip fallback at `'0.00'`.

After each edit, run `git diff <file>` to confirm only the intended lines changed.

## 6. Sequencing within session

1. Phase A in full, record results, evaluate the GO/NO-GO gate.
2. On GO: B1 (`Racing.tsx`) then B2 (`HedgeModal.tsx`). Order is for clarity, not a hard dependency — B2 makes the modal self-protecting even if the call site still passed a value, and B1 makes the data flow honest; either order leaves the same end state. If Code judges a different order cleaner, it may deviate and note it.
3. Verification (§7).
4. Output (§8).

If the work does not fit one session, that is a finding — Code reports partial-but-coherent state rather than continuing past budget.

## 7. Empirical verification

**Pre-state (capture before editing, in the report):**
- The current cash-branch expression in `Racing.tsx`.
- The current `initialBackStakeForMode` plain-cash return and the `backStake` initialiser in `HedgeModal.tsx`.

**Post-state (capture after editing):**
- `git diff` for both files showing only the intended lines changed.
- **Typecheck:** run the project's TypeScript check over `ui/web`; must pass clean.
- **Targeted tests:** run `HedgeModal.test.tsx` and `Racing.flow.test.tsx`; both green.
- **Full UI suite:** run the `ui/web` test suite; no new failures versus the pre-edit baseline (capture the baseline pass/fail count first).

**Behavioural assertions to confirm (state in the report, add a focused test if not already covered):**
- Cash mode (no active promo / plain cash): back-stake box renders **empty** on open.
- Bonus-winnings cash: back-stake box still renders **`50.00`**.
- Free-bet mode with face value set up top: box still renders the rounded face value; FB-skip still renders `0.00` with quick-buttons.
- An empty cash back-stake box blocks placement (no lay fires); typing a real stake re-enables it.

## 8. Output spec

Single report at `/Users/tim/Desktop/Projects/bethub-rebuild/cash_lay_stake_prefill_fix_report.md`. Sections: (1) Phase A review results and the GO/NO-GO call; (2) pre-state capture; (3) edits made with `git diff`; (4) verification results (typecheck, targeted tests, full-suite delta, behavioural assertions); (5) self-assessment and anything surfaced for operator-Claude. Expected length ~120–250 lines. The report contains no recommendations beyond the named fix and no scope-creep proposals; additional impacts, if any, are surfaced as findings, not acted on.

## 9. Hard limits — what is NOT in scope

- **No change to lay sizing, lay price, persistence, commission, or the liability guard.** The `laySize` formula and the `MAX_LIABILITY_SOFT_CAP` / tick-divergence guard are untouched.
- **No change to the free-bet path** (`roundDownToIncrement` seeding, FB quick-buttons, §5.7 FB-skip fallback, FB-mode submit blocking).
- **No change to the bonus-winnings `$50` default** (`BONUS_WINNINGS_CASH_DEFAULT_STAKE`) — it is a preserved v2 safety behaviour and stays.
- **No edits outside `Racing.tsx` and `HedgeModal.tsx`**, beyond optionally adding/adjusting a test in `HedgeModal.test.tsx` to cover the cash-blank assertion.
- **No schema changes, no API/route changes, no backend changes.** This is screen-only.
- **No git history rewriting.** Working tree is clean; do not `git stash`/`reset`/`restore`/`checkout` files. A commit on green is permitted (see §10); nothing else.
- **No improvising a different fix** if Phase A contradicts the diagnosis — that routes to operator-Claude.

## 10. What happens after Code's session

On green verification, Code commits both files (plus any added test) with the session-tagged message `ui: blank cash-mode back-stake pre-fill; stop piping soft odds into stake (S210)`. If any verification step is red, Code leaves the changes **uncommitted** and reports. Either way, the next operator-Claude session reads the report, confirms the behavioural assertions, and routes to close-out or follow-up. Code does not write the next brief.

## 11. Cross-references

- **Feature:** W17 §5.11 / W17.1 §5.4 quick-lay tool (HedgeModal).
- **DRs:** DR-021 (timestamp anchoring, Adelaide local time).
- **Origin:** Session 210 operator-Claude diligence (this session) — root cause traced to the `Racing.tsx` `initialBackStake` cash branch and the `HedgeModal` plain-cash seed.
- **Precedent briefs:** Sessions 35 / 36 (surgical-fix shape: named anchors, pre/post verification, explicit hard limits).
- **Excluded / parking lot:** none surfaced; the `manualOdds`-as-stake call-site smell is fixed here rather than parked.

---

## Addendum A — Test-scope authorisation (Session 210 triage)

_Added 2026-07-01 09:34 ACST, after Code's Phase A returned NO-GO. The locked brief above is unchanged; this addendum widens one hard limit, updates the verification bar, and re-issues. Origin: `cash_lay_stake_prefill_fix_report.md` §5._

**Triage outcome.** Phase A confirmed the diagnosis in full and confirmed the two-anchor production fix breaks no production consumer. The sole blocker was A4: five existing plain-cash placement tests in `HedgeModal.test.tsx` encode the old pre-fill (they seed the box via `initialBackStake` and click Place Lay) and fail once the box blanks. These tests are **updated to match the corrected behaviour, not worked around.** The production fix is unchanged.

**Authorised additional edits — this supersedes the §9 test hard-limit and the §7 "no new failures vs baseline" bar, and nothing else:**

- Edit exactly these five tests in `ui/web/src/components/HedgeModal.test.tsx`:
  1. `places a lay with explicit stake + price (the bet-safety rule)` (~line 129)
  2. `forces a confirmation step when liability exceeds the soft cap` (~line 192)
  3. `respects a localStorage override of the liability cap` (~line 220)
  4. `§5.3(a) freezes — stops polling Betfair once the lay is placed` (~line 256)
  5. `§5.3(b) frozen result reads matched/unmatched straight from the response` (~line 275)
- **The only permitted change to each:** enter a stake into the back-stake input (`fireEvent.change` on the `/back stake/i` field) using the **same numeric value the test currently passes as `initialBackStake`** (50 or 100), inserted immediately before the existing Place-Lay click. This reproduces the exact stake the test previously relied on, so all downstream maths (lay size, liability, matched/unmatched figures) is identical.
- **Every existing assertion in those five tests stays unchanged.** No assertion is loosened, deleted, skipped, or reordered. No `initialBackStake` prop is removed (leaving it is harmless — plain cash now ignores it). The change is purely the added stake-entry step.
- Plus the single new cash-blank assertion test already permitted by §9 (asserts the plain-cash box renders empty on open).
- **No other test file or test may be edited.** `Racing.flow.test.tsx` stays untouched. The BW-$50, FB-round-down, FB-missing, persistence, and `onPlaced` tests are not touched (they already pass under the fix).

**Updated verification bar (replaces §7's baseline clause):** after the edits, the full `ui/web` suite is green — the five modified tests pass with their original assertions intact, the new cash-blank test passes, and no other test changes status from the captured 124-pass / 18-file baseline. `HedgeModal.test.tsx` and `Racing.flow.test.tsx` green. `tsc -b` clean.

**Everything else in the locked brief stands unchanged:** the two production anchors B1 (`Racing.tsx` cash branch → `0`) and B2 (`HedgeModal.tsx` plain-cash `return 0` + initialiser `… : initialMode === 'cash' ? '' : '0.00'`) exactly as specified; all other §9 hard limits; commit-on-green with the S210 message from §10; and the NO-GO handback discipline if anything **beyond these five named tests** surfaces.

**Re-issue.** Phase A is complete and recorded in the report — Code does not repeat it. Code re-confirms the tree is still clean at `b0f05b0`, then proceeds in order: B1 → B2 → the five authorised test updates → the new cash-blank test → the updated verification bar above → commit on green. If any check is red, leave everything uncommitted and report.
