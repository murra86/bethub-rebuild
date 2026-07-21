# Report — Cash-lay back-stake pre-fill fix (HedgeModal)

_Session 210 · Code handoff against LOCKED brief `cash_lay_stake_prefill_fix_brief.md`_
_Written: 2026-07-01 09:34 ACST (Adelaide local, per DR-021)_
_Target codebase: `bethub-v3` · Working tree `main` @ `b0f05b0` — confirmed clean, matches brief §4_
_**Phase A outcome (first pass): NO-GO at the gate — recorded below in §§1–5.**_
_**Phase B outcome (after Addendum A triage): GO — fix + authorised test updates landed, all green, committed `e2638fa`. See §6.**_

---

## 0. Headline

The brief's core diagnosis is **fully confirmed** (A1–A3, A5 all hold; the fix as written
is correct and safe for the production data flow). However, the Phase A consumer scan (A4)
surfaced **an impact the brief did not name**: five existing tests in
`HedgeModal.test.tsx` seed the plain-cash back-stake box via `initialBackStake` and then
click **Place Lay**. Under the fix, the plain-cash box renders blank → `laySize` is `null`
→ the Place button is disabled → those five tests fail.

Repairing them (type a stake before each placement) is broader than the single change the
brief authorised (§9: adjust a test "to cover the cash-blank assertion") and contradicts
§7's "no new failures versus the pre-edit baseline". Per the §5 GO/NO-GO gate — "If … A4
surfaces a consumer this brief did not anticipate → STOP, do not edit, write the finding to
the report, end the session" — and the operator's explicit handoff instruction, this routes
to **operator-Claude triage**. I did not edit, did not improvise a test rewrite, and left
the tree clean and uncommitted.

---

## 1. Phase A review results and the GO/NO-GO call

### A1 — Re-derive the defect ✅ CONFIRMED

`ui/web/src/routes/Racing.tsx`, the `HedgeModal` `initialBackStake` ternary (lines 332–342):

```tsx
initialBackStake={
  promoConfig.promo_type === 'free_bet'
    ? (fbFaceValue ?? 0)                                    // FB branch
    : manualOdds[hedgeRunner.selection_id] != null          // cash branch ↓
      ? Number(manualOdds[hedgeRunner.selection_id])
      : 0
}
```

- The cash branch (taken whenever `promo_type !== 'free_bet'`) passes
  `Number(manualOdds[hedgeRunner.selection_id])` when a manual value exists, else `0`. ✅
- `manualOdds` is declared `useState<Record<string, number>>({})` (Racing.tsx:85) and is the
  operator's **soft odds** map — a *price*, not a *stake*. ✅

So a price is piped into a stake-named prop. Defect confirmed exactly as the brief states.

Nuance (not a contradiction): the cash branch also fires for a `bonus_winnings` cash promo,
but `HedgeModal` overrides that path to `$50` regardless of the prop (see A3), so the wrong
value only actually reaches the box in **plain cash** (no promo, or a non-BW cash promo).
Piping odds into the prop is nonetheless wrong in every cash case; the fix corrects all of them.

### A2 — Confirm the seed path ✅ CONFIRMED

`ui/web/src/components/HedgeModal.tsx`:

```tsx
const initialBackStakeForMode = useMemo(() => {
  if (initialMode === 'free_bet') {
    return roundDownToIncrement(initialBackStake, FB_STAKE_ROUNDING_INCREMENT)  // FB
  }
  if (activePromoType === 'bonus_winnings') {
    return BONUS_WINNINGS_CASH_DEFAULT_STAKE                                     // BW = 50
  }
  return initialBackStake                                                       // plain cash (170–178)
}, [activePromoType, initialBackStake, initialMode])

const [backStake, setBackStake] = useState<string>(
  initialBackStakeForMode > 0 ? initialBackStakeForMode.toFixed(2) : '0.00',    // 187–189
)
```

- The plain-cash branch returns `initialBackStake` unmodified. ✅
- `backStake` state is initialised from `initialBackStakeForMode`. ✅
- `backStake` populates the back-stake `<input value={backStake} …>` at line 427. ✅

### A3 — Confirm the two cash sub-paths are isolated ✅ CONFIRMED

- **Free-bet** branch: `roundDownToIncrement(initialBackStake, FB_STAKE_ROUNDING_INCREMENT)`
  (line 172) — separate `return`, reached only when `initialMode === 'free_bet'`.
- **Bonus-winnings** branch: `BONUS_WINNINGS_CASH_DEFAULT_STAKE` = `50` (line 59, returned at
  175) — separate `return`, reached only when `activePromoType === 'bonus_winnings'`.
- The planned edits touch only the plain-cash `return` (176→`return 0`) and the initialiser's
  `else` tail. Verified against the brief's proposed initialiser
  `initialBackStakeForMode > 0 ? …toFixed(2) : initialMode === 'cash' ? '' : '0.00'`:
  - BW cash → `initialBackStakeForMode = 50 > 0` → `'50.00'` (preserved ✅)
  - FB with face value → `> 0` → rounded value (preserved ✅)
  - FB skip (0) → not `'cash'` → `'0.00'` (preserved ✅)
  - plain cash (0) → `'cash'` → `''` (the intended new blank ✅)

Both sub-paths are independent of the plain-cash branch and are **not** touched by the edits.

### A4 — Enumerate every consumer ⚠️ CONFIRMED for production · **surfaced an unnamed test impact**

**(a) Readers of the `initialBackStake` prop inside `HedgeModal`:** only
`initialBackStakeForMode` (lines 172, 177) and, transitively, `fbSetFromTop`
(line 184, `initialMode === 'free_bet' && initialBackStakeForMode > 0`) and the `useMemo`
dependency array (178). `fbSetFromTop` is only meaningful in FB mode, which the edit does not
touch. No other reader. ✅ No production breakage.

**(b) Readers of the `backStake` state:** `backStakeNum = Number(backStake)` (253), which
feeds `laySize` (257–274), `fbStakeMissing` (282), `lockedProfit` (276–280), the confirmation
line (509–513), and `onPlaced`'s `faceValue` (361); plus the `<input>` value (427) and the
setters (onChange 430, FB quick-buttons 455). With a blank cash box, `backStakeNum = 0` →
`laySize = null` → placement blocked (the intended safety, see A5). No consumer misbehaves;
this is the designed effect. ✅

**(c) Readers of `manualOdds` in `Racing.tsx`:** declared (85); set via `handleSetManualOdds`
(276); read at 153 (`softOddsForSelected`, keyed on **`selectedRunner`**), 275 (passed to
`OddsTable`), and 339–340 (the call site being changed). Changing the cash branch to `0` does
**not** affect `softOddsForSelected` or `OddsTable`. Critically, `bookOdds={softOddsForSelected}`
(Racing.tsx:343) is the real lay-sizing input and is **untouched** — lay sizing still uses the
operator's soft odds. ✅ No production consumer breaks.

**⚠️ Unnamed impact — the test suite.** `HedgeModal.test.tsx` constructs the modal directly
with `initialBackStake` in **plain cash** mode and relies on the prop seeding the box so that
**Place Lay** is enabled. Under the fix the plain-cash box is blank, so `laySize` is `null`
and the Place button is disabled. The following **five** existing tests will newly fail:

| # | Test (line) | Why it breaks under the fix |
|---|-------------|------------------------------|
| 1 | `places a lay with explicit stake + price (the bet-safety rule)` (129) | Asserts `placeBtn` **not** disabled (134), then places — box now blank → disabled. |
| 2 | `forces a confirmation step when liability exceeds the soft cap` (192) | Clicks Place to reach the confirm dialog — button disabled, dialog never shows. |
| 3 | `respects a localStorage override of the liability cap` (220) | Clicks Place, expects `onPlaced` — never fires. |
| 4 | `§5.3(a) freezes — stops polling Betfair once the lay is placed` (256) | Clicks Place before checking the poll freeze — never places. |
| 5 | `§5.3(b) frozen result reads matched/unmatched straight from the response` (275) | Clicks Place, expects the matched/unmatched banner — never appears. |

All five pass `initialBackStake: 50` or `100` with **no promo** (→ plain cash) and depend on
the old seed. Each would need a stake typed (`fireEvent.change` on the back-stake input) before
clicking Place, or a promo set. That is a repair of five **pre-existing** placement tests —
broader than the brief's authorised "adding/adjusting a test … to cover the cash-blank
assertion" (§9) and in direct tension with §7's "no new failures versus the pre-edit baseline".
Tests 168 (BW `$50`), 178 (FB round-down), 152 (FB-missing), 239/298/308 (no placement click),
and every test in `Racing.flow.test.tsx` (does not open the modal) are **unaffected**.

### A5 — Confirm the empty-stake safety property ✅ CONFIRMED

With a blank box: `backStake = ''` → `backStakeNum = Number('') = 0`. The `laySize` memo
guards `backStakeNum <= 0` (261) → returns `null`. `attemptPlace()` bails on
`if (laySize == null || liability == null) return` (329); `runPlacement()` bails identically
(339); and the Place button is `disabled` on `laySize == null` (575). A blank box therefore
**cannot** place a zero-stake lay; it blocks until a real stake is entered, at which point
`laySize` becomes non-null and the button re-enables. ✅

_Note (informational, not a defect): in plain-cash mode `fbStakeMissing` is `false` (it gates on
`mode === 'free_bet'`), so a blank cash box shows no inline prompt — only the disabled button.
This matches the brief's assertion set (which asks only that placement be blocked) and is
pre-existing UI behaviour; flagged only for operator awareness._

### GO/NO-GO gate → **NO-GO**

A1, A2, A3, A5 confirm the diagnosis with no contradiction. A4 confirms **no production
consumer breaks** — but surfaces an impact the brief did not name: five existing placement
tests that encode the old plain-cash seed and will fail under the fix, whose repair exceeds
the authorised test-edit scope. The gate's second trigger ("A4 surfaces a consumer this brief
did not anticipate") fires. Per §5, §9, §10, and the operator's explicit handoff instruction,
I **STOP before editing**, record this finding, and hand back for operator-Claude triage. No
files were modified; no commit was made.

---

## 2. Pre-state capture (unchanged — no edits made)

**`Racing.tsx` cash-branch expression (lines 332–342):**

```tsx
initialBackStake={
  promoConfig.promo_type === 'free_bet'
    ? (fbFaceValue ?? 0)
    : manualOdds[hedgeRunner.selection_id] != null
      ? Number(manualOdds[hedgeRunner.selection_id])
      : 0
}
```

**`HedgeModal.tsx` `initialBackStakeForMode` plain-cash return (line 177):**

```tsx
return initialBackStake
```

**`HedgeModal.tsx` `backStake` initialiser (lines 187–189):**

```tsx
const [backStake, setBackStake] = useState<string>(
  initialBackStakeForMode > 0 ? initialBackStakeForMode.toFixed(2) : '0.00',
)
```

---

## 3. Edits made

**None.** The Phase A gate returned NO-GO, so Phase B was not entered. No `git diff` to show;
the working tree is unchanged from `b0f05b0`.

---

## 4. Verification results

Only the **pre-edit baseline** was captured (read-only; Phase A permits no edits). No
post-edit verification exists because no edit was made.

- **Working tree:** clean on `main` @ `b0f05b0` before and after the review
  (`git status --porcelain` empty; no stray `.tsbuildinfo`/`.vite` artifacts). ✅
- **Typecheck baseline (`npx tsc -b` in `ui/web`):** exit 0, clean. ✅
- **Targeted tests baseline (`HedgeModal.test.tsx` + `Racing.flow.test.tsx`):**
  **2 files, 13 tests, all passing.** ✅
- **Full `ui/web` suite baseline (`npx vitest run`):**
  **18 files, 124 tests, all passing.** ✅ (This is the baseline the brief's §7 "no new
  failures" bar would be measured against.)

**Behavioural assertions (§7) — analysed, not executed (no edit to test against):**

| Assertion | Predicted under the fix | Basis |
|-----------|------------------------|-------|
| Plain cash: box renders **empty** on open | ✅ would hold | A2 + proposed initialiser (`'' ` for cash) |
| Bonus-winnings cash: box renders **`50.00`** | ✅ would hold | A3 (`50 > 0` → `'50.00'`) |
| FB face value set up top: rounded value; FB-skip `0.00` + quick-buttons | ✅ would hold | A3 (FB branches untouched) |
| Empty cash box blocks placement; typing a stake re-enables | ✅ would hold | A5 |

The fix would deliver every named behaviour. The blocker is **not** the behaviour — it is the
five pre-existing tests (A4) whose repair the brief did not scope.

---

## 5. Self-assessment and items surfaced for operator-Claude

**Self-assessment.** The brief's diagnosis is correct and the two-anchor fix, as written,
would produce exactly the intended behaviour with no production-consumer regressions. I have
high confidence in A1–A3 and A5. The single reason for NO-GO is the test-suite blast radius in
A4, which the brief under-described: it anticipated *adding* one cash-blank test, but the fix
*breaks* five existing plain-cash placement tests that must also be updated. That gap is
precisely what the review-first gate exists to catch, so surfacing it (rather than silently
absorbing it by editing five tests beyond the authorised scope) is the designed-for outcome.

**Surfaced for operator-Claude triage (findings, not actions):**

1. **Five existing tests need adjustment, not just one addition.** Tests 1–5 in the A4 table
   each need a real stake typed into the back-stake input before clicking **Place Lay** (or a
   promo set) to survive the fix. This is mechanical and low-risk, but it is a *repair of
   pre-existing tests*, which exceeds the brief's §9 authorisation ("adjust a test … to cover
   the cash-blank assertion") and its §7 "no new failures" bar. Operator-Claude can resolve by
   either **(a)** widening the next brief's test-edit permission to cover these five plus the
   new cash-blank test, or **(b)** re-scoping.

2. **The production fix itself is ready.** If the test permission is widened, the two anchor
   edits are exactly as the brief specifies (Racing.tsx cash branch → `0`; HedgeModal
   plain-cash `return 0` + initialiser `… : initialMode === 'cash' ? '' : '0.00'`), and the
   §7 behavioural assertions would all pass. No change to the diagnosis or the fix shape is
   needed — only the test-scope authorisation.

3. **Informational (no action requested):** a blank cash box shows no inline prompt, only a
   disabled Place button (`fbStakeMissing` gates on FB mode only — A5 note). If operator wants
   parity with the FB-mode prompt, that is a separate, out-of-scope enhancement — flagged, not
   proposed.

**State handed back:** working tree clean at `b0f05b0`, nothing staged, no commit, no test
files touched. The next operator-Claude session decides whether to widen the test-edit scope
and re-issue, or re-scope. Code did not write the next brief.

---

## 6. Phase B — Edits, diffs, verification, and commit (post-Addendum A)

_Added 2026-07-01 09:46 ACST. Operator-Claude authorised the test-scope widening in
Addendum A; Phase A was not repeated. Tree re-confirmed clean at `b0f05b0` before editing._

### 6.1 Production edits (B1, B2)

**B1 — `ui/web/src/routes/Racing.tsx`** — cash branch of the `initialBackStake` ternary →
literal `0`. The now-stale comment ("Otherwise the existing table-carried value applies") was
corrected in the same edit so the data flow reads honestly (brief §6: "B1 makes the data flow
honest"). No other line touched; the FB branch and `bookOdds={softOddsForSelected}` are
unchanged.

```diff
           initialBackStake={
             // §5.7 — in free-bet mode the modal seeds its FB face value
             // from the amount set up top (0 when skipped, so the modal
-            // shows its own quick buttons). Otherwise the existing
-            // table-carried value applies.
+            // shows its own quick buttons). In cash mode the modal leaves
+            // the back-stake box blank (S210) for the operator to type the
+            // real stake, so pass 0 — never pipe the soft odds price into
+            // this stake-named prop.
             promoConfig.promo_type === 'free_bet'
               ? (fbFaceValue ?? 0)
-              : manualOdds[hedgeRunner.selection_id] != null
-                ? Number(manualOdds[hedgeRunner.selection_id])
-                : 0
+              : 0
           }
```

**B2 — `ui/web/src/components/HedgeModal.tsx`** — two coordinated edits confined to the
plain-cash path: `initialBackStakeForMode` plain-cash `return 0`, and the `backStake`
initialiser tail emitting `''` for cash and `'0.00'` otherwise. `initialBackStake` is still
referenced by the free-bet branch, so the `useMemo` dep array stays valid (no unused-var).

```diff
     if (activePromoType === 'bonus_winnings') {
       return BONUS_WINNINGS_CASH_DEFAULT_STAKE
     }
-    return initialBackStake
+    // S210 — plain cash: never seed the box from the incoming prop
+    // (the call site historically piped soft odds, a price, in here).
+    // The operator types the real stake into a blank box.
+    return 0
   }, [activePromoType, initialBackStake, initialMode])
```
```diff
   const [backStake, setBackStake] = useState<string>(
-    initialBackStakeForMode > 0 ? initialBackStakeForMode.toFixed(2) : '0.00',
+    initialBackStakeForMode > 0
+      ? initialBackStakeForMode.toFixed(2)
+      : initialMode === 'cash'
+        ? ''
+        : '0.00',
   )
```

### 6.2 Authorised test updates (Addendum A) — `HedgeModal.test.tsx`

The five named tests each received exactly one added step: type the stake the test already
passes as `initialBackStake` (50 or 100) into the `/back stake/i` input via `fireEvent.change`,
before the Place-Lay click. **No existing assertion was altered, loosened, removed, or
reordered; no `initialBackStake` prop removed; no other test or file touched.**

| # | Test (line) | Stake typed | Insertion point |
|---|-------------|-------------|-----------------|
| 1 | `places a lay with explicit stake + price (the bet-safety rule)` | `50` | see note ↓ |
| 2 | `forces a confirmation step when liability exceeds the soft cap` | `100` | immediately before the click |
| 3 | `respects a localStorage override of the liability cap` | `100` | immediately before the click |
| 4 | `§5.3(a) freezes — stops polling Betfair once the lay is placed` | `50` | immediately before the click |
| 5 | `§5.3(b) frozen result reads matched/unmatched straight from the response` | `50` | immediately before the click |

**Note on test 1 (the one deviation from "immediately before the click"):** test 1 has a
pre-existing assertion `expect(placeBtn).not.toBeDisabled()` *before* the click. Since the
cash box now opens blank, that assertion depends on the box being funded. Addendum A's binding
constraint — "every existing assertion stays unchanged … none loosened, deleted, skipped, or
reordered" — requires the stake to be typed *above* that assertion so it still passes with its
original meaning. Placing the stake there (rather than strictly between the assertion and the
click) is the only reading that satisfies the harder constraint; it adds only the stake step
and reorders nothing. Documented here for transparency, per the NO-GO discipline.

**Plus the one new cash-blank test** (§9-permitted), covering §7 behavioural assertions 1 and
4 in a single focused test: the plain-cash box renders empty on open, the Place button is
disabled while empty, and typing a stake re-enables it:

```tsx
it('renders a blank back-stake box on plain cash and blocks placement until a stake is typed (S210)', () => {
  renderModal({ initialBackStake: 200 })            // a soft-odds price the call site used to pipe in
  const stakeInput = screen.getByLabelText(/back stake/i) as HTMLInputElement
  expect(stakeInput.value).toBe('')
  const placeBtn = screen.getByRole('button', { name: /Place Lay/i })
  expect(placeBtn).toBeDisabled()
  fireEvent.change(stakeInput, { target: { value: '25' } })
  expect(placeBtn).not.toBeDisabled()
})
```

### 6.3 Verification results (Addendum A bar)

| Check | Baseline (pre-edit) | Post-edit | Verdict |
|-------|---------------------|-----------|---------|
| `npx tsc -b` (ui/web) | exit 0 | exit 0 | ✅ clean |
| Targeted: `HedgeModal.test.tsx` + `Racing.flow.test.tsx` | 13 pass / 2 files | **14 pass / 2 files** | ✅ (+1 new test) |
| Full `ui/web` suite (`npx vitest run`) | 124 pass / 18 files | **125 pass / 18 files** | ✅ (+1 new test) |

- The five modified tests pass with their original assertions intact.
- The new cash-blank test passes.
- No other test changed status from the 124-pass / 18-file baseline (124 → 125 is exactly the
  one added test).

**Behavioural assertions (§7) — now empirically confirmed by the suite:**

| Assertion | Result | Evidence |
|-----------|--------|----------|
| Plain cash: box renders **empty** on open | ✅ | new cash-blank test (`stakeInput.value === ''`) |
| Bonus-winnings cash: box renders **`50.00`** | ✅ | existing BW test still green (unchanged) |
| FB face value set up top: rounded value; FB-skip `0.00` + quick-buttons | ✅ | existing FB round-down / FB-missing tests still green |
| Empty cash box blocks placement; typing a stake re-enables | ✅ | new cash-blank test (`placeBtn` disabled → enabled) |

### 6.4 Observation (pre-existing, out of scope — not acted on)

`eslint` on the three files reports **3 pre-existing errors in `Racing.tsx` (lines 117–118)** —
a `react-hooks/set-state-in-effect` warning on the race-switch `setManualOdds({})` effect.
These sit far from the edited `initialBackStake` block (~line 332), predate this session, and
are **not** introduced by this change; `HedgeModal.tsx` and `HedgeModal.test.tsx` lint clean.
Lint is not part of Addendum A's verification bar. Flagged for awareness only — no action taken
(out of scope; surfaced as a finding, not a fix), consistent with the NO-GO discipline.

### 6.5 Commit

All-green, so committed per §10 / Addendum A:

```
e2638fa  ui: blank cash-mode back-stake pre-fill; stop piping soft odds into stake (S210)
         3 files changed, 50 insertions(+), 7 deletions(-)
         (Racing.tsx, HedgeModal.tsx, HedgeModal.test.tsx)
         parent b0f05b0
```

**Final state:** working tree clean on `main` @ `e2638fa`. No other files touched.
`Racing.flow.test.tsx` untouched. The next operator-Claude session confirms the behavioural
assertions and routes to close-out. Code did not write the next brief.
