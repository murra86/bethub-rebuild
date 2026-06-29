# Report — Racing-page frontend pre-cutover fixes

**Type:** Surgical fix to known issues, single bounded Code session.
Read-write, named anchors only.
**Repo:** `bethub-v3` (local Mac), branch `main`. Working tree dirty
by design.
**Brief:** `interface_triage/frontend_fixes_brief.md` (Session 167).
**Source report:** `interface_triage/racing_page_review_report.md` (S166).
**Run:** single bounded session, 2026-06-19 (ACST).

> Note on doc location: the `interface_triage/` briefs live under
> `~/Desktop/Projects/bethub-rebuild/`, while the code repo is
> `~/Desktop/Projects/bethub-v3/`. All code edits landed in bethub-v3;
> this report is filed alongside the brief in bethub-rebuild.

---

## Header — at a glance

| | Open | Close |
|---|---|---|
| Branch | `main` | `main` |
| Dirty entries (`git status --short`) | **62** | **62** (unchanged) |
| Python suite (`uv run pytest -q`) | **1028 passed**, 4 warnings | **1028 passed**, 4 warnings |
| Frontend suite (`npx vitest run`) | 13 files / **90 passed** | 14 files / **91 passed** (+1 = the new A4 test) |
| Typecheck (`npx tsc -b`) | — | **exit 0 (clean)** |

- **Single session:** yes. All four fixes + the regression test + the
  fixture recompute fit one session. Nothing deferred as an
  out-of-budget continuation.
- **Bet-path safety:** `placement.py`, the `/racing/bets` + `/racing/lay`
  POST handlers, `place_bet`/`place_lay`, the bet-record builder, and
  all schema/migrations were **not touched**. Every edit is
  display / form-state, all inside `ui/web/src`. The Python suite is
  byte-for-byte unchanged (1028 → 1028) — no backend reach.
- **Test runner:** `uv run pytest` is the Python gate (used). The EV
  engine + Fix A's test/fixtures are **TypeScript/vitest** — the only
  runner that can execute a `.test.ts`. See *Finding 1* on this
  tension; both runners were used and both are green.

### Dirty-tree integrity

The entire `ui/web/` tree is **untracked** (`?? ui/web/`) in the baseline,
so it collapses to a single `git status` entry. Every file this brief
edits lives under `ui/web/`, so:

- The dirty-file **set is unchanged in shape** — 62 entries at open and
  close, no file added to or dropped from the set. The only entry
  covering this brief's edits is the pre-existing `?? ui/web/`.
- **Consequence for "`git diff` each file":** `git diff` shows nothing
  for untracked files, so a per-file diff is structurally empty here —
  not a sign the edits didn't land. In place of diffs, each fix below
  lists the **final line anchors** (re-grepped post-edit) and the edits
  were verified by the passing/failing tests and `tsc -b`. No git
  mutation of any kind was run (no add/commit/stash/restore/checkout/
  reset).

---

## Fix A — bonus-winnings EV wiring + 70→65 conversion drop

The consequential fix (report **F1** HIGH, plus **F2**, **F4**). Five
coupled parts; all green.

### A1 — wire the bonus % into bonus-winnings EV (F1)

`evBonusWinnings` reads `promo.bonus_pct`/`basis`, but both UI call sites
built the promo object with `return_pct` only — so `bonusPct` resolved to
0 and bonus-winnings Promo EV silently collapsed to raw EV. Added
`bonus_pct: promoConfig.return_pct ?? 100` and `basis: 'winnings'` to the
promo object at **both** call sites. The two fields are inert for every
other promo type (only `evBonusWinnings` reads them); `return_type` still
flows through unchanged.

- `ui/web/src/components/OddsTable.tsx:216-217` (table column object).
- `ui/web/src/routes/Racing.tsx:156-157` (log-panel snapshot object).

`evInsurance`'s use of `return_pct` (refund %) was left untouched.

### A2 — single canonical 0.65 conversion constant (F4)

Collapsed the three hard-coded `0.7` sites to one constant and dropped
its value to 0.65:

- `evEngine.ts:43` — `export const DEFAULT_FB_CONVERSION_RATE = 0.65`
  (was `0.7`).
- `evEngine.ts:549` — `bonusWinningsEffectiveOdds` now references
  `DEFAULT_FB_CONVERSION_RATE`; the local `const FB_CONVERSION = 0.7` was
  deleted.
- `HedgeModal.tsx:14` — imports `DEFAULT_FB_CONVERSION_RATE` from
  `evEngine`; the local `const FB_CONVERSION = 0.7` was deleted.

**Verified:** no literal `0.7` / `0.70` acting as a free-bet conversion
rate remains anywhere in `ui/web/src` (grep confirms the only `0.70`
matches are explanatory comments). The Harville exponents
`0.77 / 0.62 / 0.48` were left untouched. No `FB_CONVERSION` local
reference remains.

### A3 — accurate modal label (F2)

The free-bet scream-box previously read *"v2 FB conversion 70%
applied"*, but the modal applies **no** conversion in its lay-sizing math
(the hedge is sized to the full FB face value's winnings — correct). The
label now reads, driven off `DEFAULT_FB_CONVERSION_RATE` so it can never
drift from the engine:

> "Lay size hedges the full FB face value's winnings; the **65%** FB
> conversion is a planning figure (used in the EV columns) and is not
> applied to this lay size."

- `HedgeModal.tsx:343-350` (label), reading `DEFAULT_FB_CONVERSION_RATE`
  at `:348`.

### A4 — regression test (fails pre-fix, passes post-fix)

The existing `evEngine.test.ts` passes `bonus_pct: 100` directly, so it
exercises the engine but not the UI wiring — a green suite never caught
F1. A unit test on `promoEV` with a hard-coded config can't flip on a
**call-site** edit (it would fail to *compile* pre-fix, not assert-fail).
So the A4 test reproduces the **real table call path**: it renders the
actual `OddsTable` with a configured bonus-winnings promo and asserts the
Promo EV cell differs from the Raw EV cell.

- New file: `ui/web/src/components/OddsTable.test.tsx` (1 test).

**Demonstrated flip** (same test, against the live tree):

- **Pre-fix** (A1 reverted in OddsTable): `AssertionError: expected
  '-3.7%' not to be '-3.7%'` — Promo EV == Raw EV, the F1 collapse. ❌
- **Post-fix** (A1 restored): Promo EV `+44.5%` ≠ Raw EV `-3.7%`. ✅

### A5 — conversion-shifted fixtures (old → new at 0.65)

Three fixtures in `ui/web/src/ev/__fixtures__/v2_regression.ts` depend on
the FB conversion and were recomputed. The recompute is the exact linear
effect of the rate change — the conversion enters linearly, and the
non-conversion part of each value equals `evNoPromo`, so
`new = evNoPromo + (v2_0.70_value − evNoPromo) × (0.65/0.70)`. This was
cross-checked against the engine: all 22 `evEngine.test.ts` assertions
pass at 0.65 with the new fixtures (`toBeCloseTo`, 6 dp), confirming the
independent recompute matches the engine output.

`evFreeBet_r0_lay216` (48.65…) did **not** move — `evFreeBet` is a pure
lay hedge and never applies the conversion constant (confirmed: its test
passes unchanged).

**`evInsuranceFB2nd3rdAt2_5`** (insurance FB, 2nd_3rd, book 2.5):

| i | old (0.70) | new (0.65) |
|---|---|---|
| 0 | 26.83964821659959 | 25.004576971701347 |
| 1 | -23.393058324228384 | -25.244139611064373 |
| 2 | -47.032674595328615 | -48.58574563147687 |
| 3 | -57.67458021105498 | -59.02487279207173 |
| 4 | -66.73935842880067 | -67.88313109546196 |
| 5 | -75.62326136617438 | -76.53239528943016 |
| 6 | -80.78910367382122 | -81.54531683147894 |
| 7 | -85.58761161719133 | -86.18897572071727 |

**`evBonusWinningsFBAt2_5`** (bonus-winnings FB, book 2.5):

| i | old (0.70) | new (0.65) |
|---|---|---|
| 0 | 43.63108411899432 | 40.5966245953536 |
| 1 | -28.01763880270385 | -29.538392912505877 |
| 2 | -55.66145012399404 | -56.59818005095191 |
| 3 | -66.74172041031113 | -67.44436011995245 |
| 4 | -75.50808958212356 | -76.0255243092618 |
| 5 | -83.45861353429271 | -83.80807944554005 |
| 6 | -87.75404479106179 | -88.0127621546309 |
| 7 | -91.48952687450726 | -91.66932560251063 |

**`bweo`** (`bonusWinningsEffectiveOdds`, FB 25% cap $25):

| field | old (0.70) | new (0.65) |
|---|---|---|
| effectiveOdds | 2.7625 | 2.74375 |
| bonusValue | 13.125 | 12.1875 (= min(18.75,25) × 0.65) |
| isCapped | false | false (unchanged) |

> **Flagged (see Finding 2):** `v2_regression.ts` carries a header
> warning — *"do not 'update' the fixture without a paired v2 audit."*
> The 70→65 change is a deliberate S166 business decision, not port
> drift, so A5 intentionally overrides that warning for these three
> fixtures only. Each changed fixture is annotated inline as the
> "S166 0.65 basis" so a future reader knows it no longer pins to v2.

### Worked bonus-winnings example

Favourite at soft odds **2.0**, bonus-winnings **cash**, `return_pct 100`,
winnings basis. Effective odds = `2.0 + (2.0 − 1) × 1.0 = 3.0`. With
`pWin ≈ 0.4816`:

- Raw EV = `(0.4816 × 2.0 − 1) × 100` = **−3.7%** (displayed).
- Promo EV pre-fix = **−3.7%** (collapsed to raw — the bug).
- Promo EV post-fix = `(0.4816 × 3.0 − 1) × 100` = **+44.5%** (displayed)
  — strictly different from raw at the same soft price. ✔

---

## Fix B — runner number → Betfair saddlecloth only (Q3)

The runner cell rendered two numbers: `{idx + 1}. {runnerName}`, where
`idx+1` is the app's market-book array position and `runnerName` already
carries Betfair's embedded saddlecloth number at the front of the string.
They diverge after scratchings.

Fix: dropped `{idx + 1}. ` and render `{runnerName}` only — Betfair's
embedded saddlecloth number is what remains. Per the brief's build-time
call, the cleanest source is the number already embedded in
`runner_name` (Order-of-preference #2); `sort_priority` exists on the
catalogue but is an ordering hint, not guaranteed to equal the cloth
number, so it was not used. **Fallback is automatic and correct:** if
`runner_name` has no leading number the bare name shows — never the row
index. The now-unused `idx` map param was dropped to keep the build
clean.

- `OddsTable.tsx:186` (`prices.runners.map((runner) => {` — `idx` param
  removed).
- `OddsTable.tsx:237` (render: `{runnerName}` only).

Display-only, frontend-only. Does not touch the bet-record key
(`selection_id`).

---

## Fix C — soft-odds blank default (#7)

The Soft Odds cell defaulted to the Betfair back price
(`manualOdds[id] ?? back ?? 0`). Dropped the `?? back` fallback from the
**default** so the cell starts blank and the real soft-book price is typed
fresh.

- `OddsTable.tsx:197` — `const soft = manualOdds[runner.selection_id] ?? 0`.
- `Racing.tsx:124-127` — `softOddsForSelected` mirror, `?? best_back`
  dropped.

The input still surfaces `soft || ''` (blank when 0). Downstream readers
are all guarded (EV needs `soft > 1` → renders `–`; log-panel `canSubmit`
blocks on `soft ≤ 1`; hedge modal `laySize = null` until set) — nothing
silently miscalculates. The stepper's own internal fallback
`snapSoft(soft || back || 1.5)` (`OddsTable.tsx:245, 271`) was
**preserved** so +/- still works from a blank cell. `softOddsLadder.ts`
unaffected. Frontend-only.

---

## Fix D — log-bet clear + carry-over (#8 / F7)

Two defects: on a race switch the parent nulls `selectedRunner`, so
`LogBetPanel`'s reset effect (guarded by `if (selectedRunner)`, keyed on
`selection_id` only) never fired — `softOdds`/`snapshot` carried into the
new race; and `stake` never reset at all. There was also no manual clear.

Both halves landed in `LogBetPanel.tsx`:

1. **Auto-clear on race switch.** Extracted a `clearForm()` helper
   (clears soft odds, snapshot, stake, FB selection; preserves
   account/book), and re-keyed the reset effect on the **`marketId`**
   prop in addition to the runner key. When `selectedRunner` is null
   (the race-switch case) the effect now calls `clearForm()`, so the
   previous race's state can't carry over.
   - `LogBetPanel.tsx:93-101` (`clearForm`), `:103-118` (effect, deps
     `[selectedRunner?.selection_id, marketId]`, null branch clears).
   - `marketId` is already passed to the panel by `Racing.tsx:237` — no
     prop threading needed; `Racing.tsx:89-95` (lifted-state reset) was
     left unchanged (reference only, per brief).
2. **Manual clear button.** Added a "Clear" control in the submit row
   wired to the same `clearForm()`. Styled inline (idiomatic here — the
   file/area already uses inline styles) to avoid touching the CSS module
   outside the named anchor.
   - `LogBetPanel.tsx:454-468` (the Clear button), `:460`
     (`onClick={clearForm}`).

Frontend form-state only — the `POST /racing/bets` contract is untouched.

---

## What the operator must validate live

Fixes B / C / D are UI-runtime behaviours. Code verified them by source
reasoning + the full vitest suite (incl. the existing `LogBetPanel` /
`HedgeModal` component tests, all green) and `tsc -b`. The on-screen
confirmation is the operator's post-Code step:

1. **Fix A live spot-check** — pick a bonus-winnings promo, type a soft
   price, and confirm the Promo EV column now reads materially above Raw
   EV (the worked example shows +44.5% vs −3.7% at soft 2.0 / 100%). Also
   eyeball the FB scream-box label in the quick-lay modal — it should
   read "65% … planning figure … not applied to this lay size."
2. **Fix B** — open a race that has had a scratching and confirm each row
   shows a single number that matches the saddlecloth number every other
   book shows (not the app's row position).
3. **Fix C** — confirm the Soft Odds cells start **blank**; EV columns
   show `–` until a price is typed; the +/- stepper still works from a
   blank cell.
4. **Fix D** — select a runner, type soft odds + stake, then switch races
   and confirm the panel (soft odds, snapshot, stake) clears; then test
   the **Clear** button mid-entry (account/book selection should remain).

---

## Findings (surfaced, not chased)

1. **Brief test-runner tension (resolved, informational).** §4 mandates
   `uv run pytest` only, but Fix A's engine, test, and fixtures are
   TypeScript and run only under vitest. Interpretation taken: `uv run
   pytest` is the **Python backend gate** (guarding against the
   bare-`python3` collection failure on missing `httpx`); the A4 TS
   regression is verified under the frontend's own `vitest run`, the only
   runner that can execute it. Both were run, both green. No code impact.

2. **`v2_regression.ts` "do not update without a v2 audit" warning.**
   A5's 70→65 fixture recompute deliberately overrides that file's header
   warning for three fixtures (an intentional S166 decision, not port
   drift). Done within A5's named scope; each changed value is annotated
   inline. If the operator later wants strict v2-pin separation, the
   v3-0.65 fixtures could be split into their own block — noted, not
   actioned (out of this brief's scope).

3. **Untracked frontend tree → empty `git diff`.** Because `ui/web/` is
   untracked, the brief's "`git diff` each file" check is structurally
   empty. Substituted final-anchor greps + test-driven verification.
   Informational only; the dirty-set shape is provably unchanged (62→62).

No other surprises. No remediation beyond the four named fixes was
performed; anything else routes to the next operator-Claude triage.

---

## Self-assessment

- **Coverage:** all four fixes landed (A1–A5, B, C, D). A4 demonstrably
  fails pre-fix and passes post-fix. A5's three fixtures recomputed and
  cross-checked against the engine. Worked bonus-winnings example given.
- **Confidence:** high. Fix A is grep- and test-confirmed (the wiring gap
  reproduced and closed; fixtures match the engine to 6 dp). B/C/D are
  small, localised, source-reasoned, and covered by a green suite +
  clean typecheck; their on-screen behaviour is the operator's named
  validation step.
- **Scope discipline:** edits confined to the named anchors across
  `evEngine.ts`, `OddsTable.tsx`, `Racing.tsx`, `HedgeModal.tsx`,
  `LogBetPanel.tsx`, `v2_regression.ts`, plus the new `OddsTable.test.tsx`.
  No bet-placement path, no schema/migration, no cycle-capture, no
  launcher, no back-bet build, no durability work, no dead-code removal
  (`calculateLayFieldProbabilities` left in place), no new promo-config UI
  input (the 65% stays a single constant). No git operations. Python
  suite unchanged (1028→1028); dirty-tree shape unchanged (62→62).
- **Single session:** confirmed — everything fit; nothing deferred for
  budget.

*End of report.*
