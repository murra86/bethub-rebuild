# S245 Feedback 1 — TAB soft-odds auto-fill is book-driven (report)

Built 2026-07-20. Display-only UX change, zero money paths. Commit
`abd84e1` on `main` (from `09d0897`), pushed to `murra86/bethub-v3`.

## What changed

The "TAB odds" checkbox is gone. The Soft Odds column now auto-fills from
the TAB feeds **only while the book armed in the top bar is TAB**; on any
other book (or none) the auto-fill blanks. The operator no longer toggles
anything — arming the TAB book IS the switch.

Files:
- `ui/web/src/routes/Racing.tsx` — removed the `tabOddsEnabled` state and
  `handleToggleTabOdds`; added `selectedBookIsTab` (derived, below); both
  the background `tabOddsQuery` and the Build 2 `tabLiveQuery` now gate on
  `selectedBookIsTab` (the live query still ALSO keeps its visible +
  within-30m-of-jump gates); the seed/merge effect gates on
  `selectedBookIsTab`; a new blank-on-non-TAB effect; a per-runner
  `tabSeededRef` to know which values are TAB auto-seeds vs operator edits.
- `ui/web/src/components/OddsTable.tsx` — removed the `tabOddsEnabled` /
  `onToggleTabOdds` props and the checkbox JSX. The Soft Odds input is
  unchanged and stays freely typeable on every book.
- `ui/web/src/components/OddsTable.module.css` — removed the `.tabToggle`
  rules.
- `ui/web/src/hooks/usePriceMemory.ts` — removed the now-unused
  `loadTabOddsEnabled` / `saveTabOddsEnabled` helpers and the
  `RACING_TAB_ODDS_ENABLED` localStorage key.
- Tests: `Racing.tabodds.test.tsx` rewritten to the book-driven model;
  `Racing.tablive.test.tsx` updated to arm a TAB book before asserting the
  live feed fires.

## How "is the book TAB" is derived

From the currently-armed book in the top bar. Racing.tsx holds `bookId`;
the book's identity is its **name** in `accountListing.data.books` (the
`BookItem.name` field — the same string the chips render). Match is
case-insensitive on a whole word: `/\btab\b/i.test(book.name)`.

- Matches: `TAB`, `NSW TAB`, `TAB (SA)`, `tab`.
- Does NOT match: `Tabcorp`, `Stab` (no word boundary), and — deliberately
  — no book armed → not TAB (both feeds stay off, column blank).

Rationale for name-not-id: book_ids are opaque; the name is the stable,
human-meaningful identity already used across the top bar, and whole-word
matching avoids the substring traps.

## Edit-across-book-switch behaviour (the decided edge)

Chosen the lean the brief suggested: **operator-typed Soft Odds are
per-race and survive book switches; TAB auto-seeds follow the book.**

Mechanism: a runner the operator types/steps/clears is added to
`operatorTouchedRef` and removed from `tabSeededRef` (it is now operator-
owned, no longer a TAB auto-seed). The blank-on-non-TAB effect only clears
selections still in `tabSeededRef` and never those in `operatorTouchedRef`.
Concretely:

- TAB book: feed seeds the column (never overwriting operator-touched runners).
- Operator types over a runner → that value is theirs.
- Switch TAB → non-TAB: only the untouched auto-seeds blank; the typed
  value stays.
- Switch back to TAB: the seed effect re-runs off the cached feed and
  refills the auto-seed runners, still skipping operator-touched ones — the
  typed value is untouched.
- Typing on a non-TAB book works normally and that value also survives a
  later switch to/from TAB.

Person/book selector changes track correctly because `selectedBookIsTab`
is a `useMemo` over `bookId` + the listing; the top bar's existing
person-change logic (keeps the book when the pairing exists, else clears
it) drives `bookId`, and the fill/blank state follows whatever book is
current. Per-race reset also clears `tabSeededRef` alongside the existing
`operatorTouchedRef` reset.

Fences honoured: no money-path files touched; the existing merge/seed
effect and `operatorTouchedRef` are reused (no parallel fill path); the
`live ?? background` merge priority and operator-edit protection are
unchanged.

## Suites

- Frontend: `npm run build` (tsc -b + vite) GREEN; `vitest run` **249
  passed** (28 files) — baseline 247, +2 from the two added book-driven
  tests. `Racing.tabodds.test.tsx` (8) and `Racing.tablive.test.tsx` (5)
  both green.
- Backend: `uv run pytest` **1530 passed** (baseline 1530 — untouched, as
  expected for a frontend-only change).
- dist rebuilt via `npm run build` (dist is gitignored; only source
  committed).

## Commit

`abd84e1` — "S245 Feedback 1: TAB soft-odds auto-fill is book-driven, not
a checkbox" — pushed to `main`.

## Not done / notes

- Feedback 2 (FB-conversion CALL basis: 70% for the CALL, 65% for EV
  maths) is explicitly "not built now" in the spec — untouched.
- Implemented-not-live: like the rest of the race-page rework, this wants a
  next-racing-day live look (arm the real TAB book, confirm fill; arm a
  non-TAB book, confirm blank + typeable).
