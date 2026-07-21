# Consolidated frontend fix report — pre-cutover interface polish

**Session:** Code, executing `consolidated_frontend_fix_brief.md` (S193).
**Date:** 2026-06-26 ACST.
**Target repo:** `bethub-v3` — frontend only (`ui/web/src`).

---

## Run header

- **HEAD:** `2329604`, branch `main` — unchanged at session end.
- **Working tree:** 69 dirty entries at start and end; `ui/web/src/` is
  `?? ui/web/src/` (UNTRACKED) throughout. **No git operation was run**
  (no add/commit/stash/restore/checkout/reset). Changes verified by file
  read + the test suite, never `git diff`.
- **Scope held:** every edit is under `ui/web/src` (+ named `.module.css`).
  No backend file (`ui/api`, `workflows`, `domain`, `store`, `clients`,
  `migrations`), no schema, no migration, no API contract. The free-bet
  consume + qualifier-cycle inheritance is read/relied-on, never modified.

### Files touched

Source (9):
- `src/App.module.css` — §5.1
- `src/components/OddsTable.tsx` — §5.2
- `src/components/PromoBar.tsx` — §5.6, §5.7
- `src/components/PromoBar.module.css` — §5.7
- `src/components/HedgeModal.tsx` — §5.3, §5.7
- `src/components/HedgeModal.module.css` — §5.7
- `src/components/LogBetPanel.tsx` — §5.5, §5.4, §5.3(e)
- `src/routes/Racing.tsx` — §5.7, §5.3(d), §5.4
- `src/routes/Racing.module.css` — §5.3(d)

Tests (5 — 4 extended, 1 new):
- `src/components/OddsTable.test.tsx`, `HedgeModal.test.tsx`,
  `PromoBar.test.tsx`, `LogBetPanel.test.tsx` (extended)
- `src/routes/Racing.flow.test.tsx` (new — §5.4 integration)

Sequencing followed §6: small isolated fixes first (§5.1/§5.2/§5.5/§5.6),
then §5.7, then the interconnected §5.3/§5.4 last.

---

## Per-fix outcome

### §5.1 — Sticky top nav — DONE
**Anchor:** `App.module.css .nav`. Added `position: sticky; top: 0;
z-index: 50`. Sticky (not fixed) keeps the nav in normal flow, so it
occupies its own height and never overlaps the first page row — no
compensating top padding required. z-index 50 sits under the modals
(z-index 100+) and above page content. On the Racing page (which already
sizes itself `calc(100vh - 50px)` and scrolls `.main` internally) the
nav was already on-screen; the fix bites on the taller body-scrolling
pages (BetLog, Accounts, Log Past Bet). See the freeze-vs-pinned finding.

### §5.2 — Odds column accepts "1" + Delete-to-clear — DONE
**Anchor:** `OddsTable.tsx` soft-odds input (+ no CSS change needed).
The inline `type="number"` input committed straight through a `n > 1`
guard, so the leading `1` of `1.50` was rejected and dropped. Extracted a
small `SoftOddsInput` component that holds the raw keystrokes in local
state: intermediate values (`1`, `1.`) now display, and the value commits
to `setManualOdds` only when the parsed price is `> 1`. The `> 1` rule
governs what is *committed*, never what can be *typed*. Switched the field
to `type="text" inputMode="decimal"` because a number input silently
coerces `"1."` to `""` mid-edit. Added `onKeyDown` so the keyboard Delete
clears the box (commits `0`); Backspace-to-empty clears via the empty
`onChange` (also commits `0`). The ▾/▴ steppers and race-switch resets
flow back into the box through a `committed`-keyed sync effect.

### §5.3 — Place Lay & Log flow (the v2 rebuild) — DONE
**Anchors:** `HedgeModal.tsx`, `Racing.tsx`, `LogBetPanel.tsx`.

**(a) Freeze on placement.** `livePricesQuery.refetchInterval` is now
`response != null ? false : HEDGE_MODAL_POLL_MS` — once the lay is placed
the modal stops polling Betfair, so the result line can't drift off a
moving price.

**(b) Honest frozen result.** The result line reads ONLY from the frozen
placement `response` (`matched_size` / `size_remaining`), never the live
`laySize` denominator. Full match (`size_remaining ≤ FILL_REMAINDER_
THRESHOLD`, 0.01) → green "Matched in full — $0 unmatched". Partial →
"Matched $X — **$Y** still unmatched on Betfair" with `$Y` (the real
exposure) held still and called out in a `<strong>` against the amber
`.partial` style. The moving percentage (which divided by `laySize`) is
gone.

**(c) Persistence auto-set by race code.** `defaultPersistenceForRace`
derives the default from `catalogue.event_type_name`: greyhound → LAPSE
(no Betfair in-play, the remainder can't persist), thoroughbred + harness
→ PERSIST; indeterminate → the safe pre-existing default (PERSIST). Seeded
via `useState` initialiser and re-applied by an effect if the catalogue
arrives after mount, gated by a `userEditedPersistence` ref so a late load
never clobbers the operator's manual override (mirrors the lay-price
pattern).

**(d) Hand into the soft-book log + lifted banner.** On placement the
modal freezes the result, shows it, then auto-closes after
`HEDGE_AUTO_CLOSE_MS` (1500 ms), landing the operator in `LogBetPanel`
(runner already set via the existing `onPlaced → setSelectedRunner`). The
matched/unmatched result is lifted to `Racing.tsx` (`hedgeHandoff` state,
carried out of the modal via an extended `onPlaced(response, meta)`) and
rendered as a banner ABOVE the log panel — green for full, amber for
partial — that stays for the whole soft-book log. The banner clears on the
next lay (`handleQuickLay`) or the next successful log (`handleLogged`).

**(e) Free-bet handoff — cycle link preserved, empty inventory graceful.**
When the lay was placed in `mode === 'free_bet'`, the handoff lands the
log panel in free-bet mode (`isFreeBet = true`) via a per-placement
`handoffNonce` so the FB inventory picker shows. The three hard rules:
1. **No `cycle_id` on the soft-book FB log.** `postLogBet`'s body still
   omits `cycle_id` entirely — untouched, and a regression test now
   asserts `'cycle_id' in body === false`. The qualifier-cycle inheritance
   (`log_bet → resolve_inherited_cycle` on `consumed_credit_event_ids`) is
   left to the server.
2. **Pre-select only on an unambiguous match.** Once the operator picks
   the account+book and the inventory loads, if exactly ONE free bet
   matches the deployed face value (passed through as `handoffFaceValue`)
   it is pre-ticked; otherwise the selection is left to the operator. This
   only ticks the box — nothing is auto-consumed (the operator still
   confirms the log). A `handoffPreselectApplied` ref makes it one-shot.
3. **Empty inventory is graceful.** The empty-FB message now reads
   "No free bet booked in at this account-at-book yet — settle the
   qualifier first, or untick 'free bet' above to log this as a plain cash
   bet deliberately." Submit stays blocked in FB mode (the existing
   "Pick a free bet to deploy" guard), so a free-bet deployment cannot be
   silently logged as cash — the operator must deliberately untick. No
   trap, no silent mislink. Deploy-before-settle / IOU credit stays OUT.

### §5.4 — Log box drops and closes on successful log — DONE
**Anchor:** `Racing.tsx handleLogged` + `LogBetPanel`. On a successful
log, `handleLogged` keeps invalidating the log-context query, clears the
lay-result banner, and schedules `setSelectedRunner(null)` after
`LOG_SUCCESS_CLOSE_MS` (1200 ms) so the green success message shows for a
beat, then the panel nulls back to "Select a runner." **`manualOdds` and
`selectedMarket` are not touched** — the race stays and the operator's
typed soft odds persist in the column (`manualOdds` still resets only on a
market change). In `LogBetPanel` the inline `canSubmit()` warning is gated
behind `!success` so the just-cleared stake doesn't flash "Stake required"
during the close beat.

### §5.5 — Clean success message — DONE
**Anchor:** `LogBetPanel.tsx submit()`. Replaced
``Logged ${result.bet_id} ✓`` with the plain "Bet logged successfully";
the now-unused `result` binding was dropped (the `await` stays). It renders
through the existing `.successMsg` style, which is already green
(`#80ffaa`) — no CSS change needed.

### §5.6 — Drop the Free Bet return-type selector — DONE
**Anchor:** `PromoBar.tsx`. The return-type `<select>` is now gated behind
`config.promo_type !== 'free_bet'`. A free bet always returns cash, so the
choice was redundant there; it stays visible for insurance /
bonus-winnings, where return type is a real choice.

### §5.7 — Free-bet quick-amount buttons (top-primary, modal-fallback) — DONE
**Anchors:** `PromoBar.tsx` (primary), `HedgeModal.tsx` (fallback), wired
through `Racing.tsx`. When the Free Bet pick is active, the PromoBar shows
`$25 / $50 / $100` quick buttons + a free-entry box that set a
parent-owned `fbFaceValue` (Racing state; cleared whenever the active
promo leaves free-bet mode). Racing carries it into the modal via the
existing `initialBackStake` path in free-bet mode. The modal shows the
same quick buttons ONLY when no amount was set up top (`fbSetFromTop`
false); when an amount was set up top the FB face-value field is
pre-filled and the buttons are hidden. Set once — up top by default, in
the modal only if skipped. The shared `FB_QUICK_AMOUNTS` const lives in
`PromoBar` and is imported by the modal so both surfaces show the same set.

---

## Bet-safety preservation (§9)

The `HedgeModal` lay-placement safety rules are preserved verbatim — none
were weakened by the freeze/flow changes:
- Placement still posts explicit `price` + `stake` (`laySize.toFixed(2)`),
  never a profit-target order type.
- The liability soft-cap (localStorage-tunable, guard not disableable) and
  the tick-divergence fat-finger confirm both still gate placement
  (`attemptPlace → checkGuardReasons → pendingConfirm`), unchanged. Their
  two existing tests still pass.
The freeze only changes what the modal *displays and polls* after a
placement that has already passed those guards.

---

## Test delta

| Gate | Before | After |
|------|--------|-------|
| `npx tsc -b` | clean (exit 0) | clean (exit 0) |
| `npx vitest run` | 17 files, 110 passed | 18 files, 124 passed |

Net **+14 tests, 0 failures, 0 removed**. New/extended coverage:
- **OddsTable** — a typed "1.x" displays the leading "1" and commits at
  `> 1`; backspace-to-empty and keyboard Delete each clear the box
  (commit 0).
- **HedgeModal** — §5.3(a) polling stops after placement (no further
  `fetchMarketPrices` calls once frozen); §5.3(b) the result line shows
  the response's matched/unmatched figures; §5.3(c) greyhound → LAPSE,
  thoroughbred → PERSIST; §5.3(d/e) `onPlaced` reports `mode` + `faceValue`.
- **PromoBar** — §5.6 return-type hidden under Free Bet, kept for
  insurance; §5.7 quick amounts + free entry emit the chosen face value,
  and the FB-amount row is absent for standalone callers (no setter).
- **LogBetPanel** — §5.3(e) free-bet handoff lands FB mode, pre-ticks the
  one matching FB, logs **without** a `cycle_id`; empty inventory shows the
  graceful message and keeps submit blocked (no silent cash log).
- **Racing.flow (new)** — §5.4 end-to-end: after a successful log the
  panel drops to "Select a runner" while the typed soft odds and the open
  race both persist.

No Python suite change expected or made — confirmed by construction (no
backend file edited).

---

## Findings (surprises / decisions — for the next triage session)

1. **§5.1 "freeze" reading = pinned, confirmed.** Code inspection found no
   lock-up / unresponsive fault in the nav (it is plain `<Link>`s, no
   state that could hang). The symptom matches a non-sticky header
   scrolling off a body-scrolling page, so the sticky fix is the right
   read. The nav lives outside the per-page scroll container, so the
   layout assumption (`calc(100vh - 50px)` on the Racing page) is
   unaffected. No lock-up to report.

2. **Empty-FB-inventory UX decision.** The brief left the exact path
   open. The decision taken: keep submit blocked in free-bet mode (so a
   free bet can never be silently logged as cash) and make the inline
   message name the deliberate alternative — untick "free bet" to log a
   plain cash bet. This makes "log as plain" a conscious operator action,
   not a silent fallthrough, and never traps (there is always the untick
   path). Nothing is consumed or cycle-linked in this state.

3. **Pre-existing `initialBackStake` semantics in the cash path.** In
   non-free-bet mode `Racing` still passes `manualOdds[selectionId]` as
   the modal's `initialBackStake` (the value is the soft *price*, not a
   stake). This predates the brief and is outside the named anchors'
   intent for §5.7 (which only governs the free-bet face value), so it was
   left exactly as found. Noted only for visibility.

4. **Auto-close timing is fixed, not adaptive.** The modal auto-closes
   1500 ms after a placement regardless of full vs partial fill; the
   partial exposure is carried by the persistent banner above the log
   panel, so closing does not lose the figure. If the operator wants
   longer to read a partial in-modal, that timing is the lever — flagged,
   not changed.

5. **Lint (not part of the §7 gate) is pre-existing red.** `eslint .` was
   already failing at baseline on untouched code — e.g.
   `react-hooks/set-state-in-effect` on the existing race-switch effect
   (`Racing.tsx:117`) and `react-refresh/only-export-components` on
   component files that export consts (the established repo convention,
   e.g. `HedgeModal`'s exported constants). The new code follows those
   same existing patterns (the `committed`/persistence sync effects mirror
   the existing lay-price sync effect; `FB_QUICK_AMOUNTS` is exported like
   `HEDGE_MODAL_POLL_MS`). tsc + vitest — the §7 gate — are both green.

---

## Self-assessment — what could not be verified in-session

- **Live Betfair partial-fill behaviour.** The freeze (a/b) and the
  partial banner were verified against mocked `postPlaceLay` responses
  (full and partial). The real shape of a near-jump partial fill — and
  that the frozen `matched_size`/`size_remaining` are the values the
  operator should trust — can only be confirmed against the live exchange,
  which is out of frontend scope (no Betfair API access this session).
- **Sticky nav across real page heights.** Confirmed by CSS reasoning and
  the App nav tests still passing; not visually verified in a browser at
  the operator's 1366-laptop viewport against each page's real content
  height (no dev-server run — the app serves a static `dist` build and
  this session made no build).
- **The 1200 ms / 1500 ms beats** were chosen for a readable-then-close
  feel; they are verified to fire and sequence correctly in tests but were
  not tuned against live operator rhythm.
- **Server-side qualifier-cycle inheritance** is asserted only at the
  frontend boundary (the log body carries no `cycle_id` and the correct
  `consumed_credit_event_ids`). That the server then inherits the
  qualifier's cycle is existing backend behaviour, exercised by its own
  suite, not re-checked here.
