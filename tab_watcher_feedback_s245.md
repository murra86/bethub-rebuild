# S245 operator feedback — TAB feed + watcher CALL

Captured 2026-07-20. Two items from the operator during the Build 2 launch.

## Feedback 1 — TAB auto-fill is book-driven, not a checkbox (ACTION: queued, post-Build-2)

**Change:** remove the "TAB odds" checkbox from the race page. The Soft
Odds column fills from TAB **only when the selected book is TAB**; on any
other book it stays blank (and **blanks when the operator switches from
TAB to another book**). Person/book selector changes must track correctly
(TAB fill/blank follows the currently-selected book across
person-and-book combinations).

**Applies to BOTH feeds:**
- Build 1 background fill (currently gated on the `tabOddsEnabled`
  toggle → change to "selected book == TAB").
- Build 2 live pull (brief gates on the toggle → same change: only pull
  live when the selected book is TAB, for the active race only).

**Disposition:** do as ONE clean follow-up change immediately after
Build 2 lands (avoids disrupting the running build; the toggle→book
swap is a trivial gate-source change). Removes the checkbox, gates both
feeds on book==TAB, preserves the Build-1 operator-edit protection.
Open detail to settle at build time: whether an operator edit persists
across a book switch away-and-back, or re-seeds — decide sensibly (lean:
edits are per-race and survive; a non-TAB book just hides the feed).

## Feedback 2 — FB-conversion CALL basis (FLAGGED for watcher calibration)

For **free-bet conversion** promos, the watcher's CALL should base its
recommendation on the **likelihood of securing the conversion target**
(convert the free bet to ~cash value), not raw promo EV.

**RESOLVED (operator, S245):** two figures for two purposes —
- **CALL free-bet-conversion recommendation → 70%** (operator's rule-of-
  thumb conversion target; the likelihood the CALL is graded against).
- **All EV *calculations* → stay 65%** (conservative): insurance-bet EV,
  free-bet valuation (`evFreeBet`), and any other money-valuing maths.
  Operator: value at 65% to stay conservative, but aim to convert at 70%.

**Disposition:** folds into the watcher Calls when we tune the grade
bands on data (the Calls are an explicit first cut). Not built now.
When built: keep the 65% EV constant untouched; the 70% is a SEPARATE
constant used only by the CALL's FB-conversion logic. Relates to
[[fb_lay_take_sp]] and the FB-conversion strategy work.
