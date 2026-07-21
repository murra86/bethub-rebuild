# UI pass #3 — build report (S245, 20 Jul 2026)

**Executor:** background Code session. **Base HEAD:** `abd84e1`.
**Brief:** `ui_pass3_build_brief.md`. **Mock:** `ui_pass3_betlog_row_mock.html`.
**Fence held:** display-only throughout; no placement / settlement /
reconciliation / money-calculation file was touched. Item 2's price fell
to the bounded stake-only fallback (see below), so even that one exception
never reached the money path.

All four items shipped. What each one means for your betting day is at the
top of each section; the mechanism is in the file.

---

## Item 1 — BetLog: P&L column + insurance shield

**What you see:** every bet row now shows its result as money on the far
right — green `+X` for a win, red `-X` for a loss, a dash while it's still
running, `0.00` on a void — so you read the outcome without tapping the row
open. And an insurance bet now carries a 🛡 in the Promo column, so you can
scan the list and instantly tell which bets are riding a safety-net promo,
distinct from a free bet (FB) or a plain promo.

**Shipped:**
- New 10th column **P&L appended on the far right, after State** —
  operator-locked position, nothing reordered. Grid widened by one column;
  reuses the pre-existing `.cellPnl` / `.cellPnlNeg` / `.cellPnlZero`
  classes. Value = `bet.pnl` via the existing `signedMoney()`, gated on
  `bet.is_settled`: win → green `cellPnl`, loss → red `cellPnlNeg`, pending
  → faint `—`, settled void → faint `0.00`. Same figure the expanded
  tuck-in already showed.
- **🛡 shield** in the Promo column when
  `strategy_tag === 'safety_net' && promo_template_id !== null` (the
  already-codified insurance rule, the same shape the credit-in gate uses).
  FB badge / plain-promo / `—` unchanged for the other cases.
- Files: `ui/web/src/routes/BetLog.tsx` (helpers `isInsuranceBet`,
  `pnlCell`; row cells), `BetLog.module.css` (grid + `.insuranceMarker`).
- **Note on `signedMoney`:** it renders `+120.00` / `-80.24` / `0.00`
  with no `$` sign and an ASCII hyphen — I reused it exactly as the
  existing tuck-in P/L does, for codebase consistency, rather than
  matching the mock's decorative `$` and unicode minus. The colour carries
  the win/loss meaning. Flag if you'd prefer the `$`/`−` styling.

## Item 2 — Unmatched-lay bar (activity board)

**What you see:** an unmatched Betfair lay on the race activity board now
reads **"Unmatched $40.00"** (your intended lay stake) instead of the
misleading **"$0.00"**. Matched and partial lays are unchanged.

**Item-2 grounding result — the lay price is NOT persisted → stake-only.**
I grounded the fence-sensitive bit before touching anything. The lay
*order* price is **not** stored at placement: the `bets` table
(`store/schema/bets.py`) has only `matched_price` (plus
`soft_book_combined_price`), no requested/order-price column; the record
builder (`workflows/bet_entry/v1/record_builder.py`) persists
`matched_price` only; the order price (`proposed_price`) lives solely in
the transient place-lay request / modal snapshot in the orchestrator. So
per the brief I took the **stake-only** path: show `Unmatched $<requested_
stake>` (dropping the "@ 0.00"), and did **not** modify the placement/money
path to capture the price.
- File: `ui/web/src/components/RaceActivityBoard.tsx` (helper
  `fmtMoneyCell`, applied to the BoardRow money span). A fully-unmatched
  lay (`matched <= 0` and `< requested`) renders `Unmatched $X`; everything
  else keeps `$matched @ matched_price`.
- **OPERATOR DECISION (parked):** if you want the lay *price* shown on the
  unmatched bar too, that needs a placement-path persistence change — a
  new stored order-price column, written when the lay is placed. That is a
  money-path change, deliberately out of this display-only pass. Say the
  word and it becomes its own scoped brief.

## Item 3 — Total-matched: live on the race page, de-staled in the list

**What you see:** the race page header now shows **"market matched $5k"** —
the live market total, updating ~1s with the rest of the prices, where
before it was fetched but never displayed. And the day-list figure in the
sidebar now carries a tooltip explaining it's the list-refresh figure, so a
slow-moving number there never reads as the live total.

**Shipped:**
- Race page: added the live `prices.total_market_traded_volume` to the
  OddsTable header meta row (`ui/web/src/components/OddsTable.tsx`), beside
  as-of and commission. Formatter is `fmtVol` — byte-identical to the
  sidebar's `formatMatched` (same abbreviation logic), so this reuses the
  existing formatter rather than adding new logic (the brief's "reuse
  `formatMatched`" intent; I did not cross-import to avoid a
  component→component dependency).
- Sidebar: the `total_matched` cell keeps its number but gains a `title`
  relabel — "Matched at the race-list refresh — the live market total is on
  the race page" (`ui/web/src/components/RaceListSidebar.tsx`). The sidebar
  status line already declares fresh/stale + lag for the whole list; this
  makes the per-cell meaning honest without dropping a useful liquidity
  glance.

## Item 4 — Refresh-cadence review — no change needed

**Finding: every surface already keeps up with the 60s settlement sweep.**
- Race-page prices: `OPEN_RACE_POLL_MS = 1_000` (1s) while the tab is
  visible — the new live total-matched inherits this, so it's genuinely
  live.
- Race activity board: `BOARD_POLL_MS = 5_000` (5s); current-orders
  persist/lapse join at 15s.
- BetLog feed: `refetchInterval` polls **10s while anything is pending or
  unsettled**, else one-shot — so matched-status changes and settlement
  results land within ~10s, well inside the 60s sweep window.
- The only slow surface is the sidebar day-list (by design — it's the
  whole-day catalogue), which is exactly what item 3's relabel addresses.

No refetch/invalidation was added — nothing was under-refreshing.

---

## Suites / gate

- Frontend `npm run build` (tsc typecheck + vite): **green**, dist rebuilt.
- Frontend vitest: **255 passed** (baseline 249; +6 new tests, +1 existing
  test updated). New: P&L per state (won/lost/pending/void), shield only on
  insurance bets (not FB / plain-promo / bare), unmatched-lay
  "Unmatched $X" (+ matched-lay unchanged), live total-matched on the race
  page, sidebar de-stale title.
- One existing test updated: `BetLog.test.tsx` previously asserted P&L was
  *absent* from the grid ("P&L left the grid, item 5"); item 1 deliberately
  re-adds it far-right, so that assertion was flipped to check the new grid
  cell (still present in the tuck-in too).
- Backend `uv run pytest`: **1530 passed** (unchanged — no backend file
  touched; grounding only).

## Files changed

- `ui/web/src/routes/BetLog.tsx`, `ui/web/src/routes/BetLog.module.css`
- `ui/web/src/components/RaceActivityBoard.tsx`
- `ui/web/src/components/OddsTable.tsx`
- `ui/web/src/components/RaceListSidebar.tsx`
- tests: `BetLog.test.tsx`, `RaceActivityBoard.test.tsx`,
  `OddsTable.test.tsx`, `RaceListSidebar.test.tsx`
- `ui/web/dist/*` (rebuilt)

## Needs an operator decision

1. **Item 2 lay price (parked):** showing the order price on the unmatched
   bar needs a placement-path persistence change (money path) — separate
   brief if wanted. Stake-only shipped for now.
2. **P&L styling (minor):** currently reuses `signedMoney` (`+120.00` /
   `-80.24`, no `$`, ASCII hyphen) for consistency with the tuck-in; the
   mock showed `$`/`−`. Change if you prefer the mock's look.

**S189 status:** all of this is implemented-not-live — display-only bits
get their first real confirmation at the next race-day look.
