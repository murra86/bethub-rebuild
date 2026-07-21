# Build brief — UI pass #3 (race-day display tweaks)

**Session:** S245, 20 Jul 2026. **Author:** Chat (grounded on a live code
map + an operator-approved mock). **Executor:** background Code session.
**Locked mock (BetLog row):** `ui_pass3_betlog_row_mock.html`. **Fence:**
display-only, **no money paths** — with ONE carefully-bounded exception
(item 2's lay price) that must stay safe (see its rule).

Read this whole brief + open the mock and confirm understanding before
editing. This is polish on existing reads — small, low-risk, reversible.

## Scope (four items). All in `bethub-v3` frontend unless noted.

### 1. BetLog row — P&L column + insurance shield (display-only)
`ui/web/src/routes/BetLog.tsx` `BetRow` (collapsed grid `:543-609`) +
`BetLog.module.css` (grid `:129-135`).
- **Add a 10th column, P&L, on the FAR RIGHT (after State)** — operator
  locked this position. Reuse the already-present-but-unreferenced
  `.cellPnl` CSS class (`:257`); widen the grid template by one column.
  Value = `bet.pnl` via `signedMoney()`, gated on `bet.is_settled`
  (mirror the expanded tuck-in `:626-627`): green `+$X`, red `−$X`, `—`
  while pending, `$0.00` on a settled void. Right-aligned, tabular nums.
- **Insurance shield 🛡** in the existing Promo column (`cellPromo`
  `:597-605`) when the bet is insurance-triggered — reuse the codified
  rule `strategy_tag === 'safety_net' && promo_template_id !== null`
  (already used at `:501-504`). Keep FB badge / plain-promo / `—` for the
  other cases. **Icon = 🛡 shield** (operator pick), not a gift.
- All data already on the payload — no backend change.

### 2. Unmatched-lay bar — real values, not "$0.00 @ 0.00"
`ui/web/src/components/RaceActivityBoard.tsx` `BoardRow` money cell
(`:195-198`). It reads `matched_stake`/`matched_price`, both `0` for an
unmatched lay → shows "$0.00 @ 0.00". The board already derives the right
label via `stateLabel` (`:60-67`, comparing `requested_stake` vs
`matched_stake`).
- For an **unmatched / partial** lay, show **"Unmatched $X @ price"**
  where $X = `requested_stake` (already on the feed) and price = the lay
  order price.
- **THE ONE FENCE-SENSITIVE BIT — the lay price:** the order price is
  NOT on the bets feed today (only `matched_price`). **Ground first:** is
  the requested/lay price already PERSISTED at placement (a column on the
  bet / bet_legs / a placement record)?
  - **If YES** → echo it onto `BetFeedItem` (`ui/api/routers/bets.py`) as
    a read-only field and render it. This is a display/data-surfacing
    change — fine.
  - **If NO** (the price is only in the transient `PlaceLayRequest`) →
    do the **stake-only** fix: show **"Unmatched $X"** (drop the
    "@ 0.00"), and **STOP + flag** that surfacing the price needs a
    persistence change on the placement path — do NOT modify placement /
    money logic to capture it. That's a separate operator decision.
  - Either way: matched/partial-matched rows keep showing matched
    stake @ matched price as today.

### 3. Total-matched — live on the race page + de-stale the list
- **Race page:** render the LIVE market total —
  `prices.total_market_traded_volume` (`MarketPrices`, already fetched
  ~1s in `Racing.tsx`, currently only stamped into log snapshots, never
  shown). Put it in a race-page header/status area near where `prices`
  is in scope (~`Racing.tsx:586-607`); reuse `formatMatched` from the
  sidebar. Optionally show Δ since race-open if cheap; skip if it adds
  state complexity.
- **Race list sidebar** (`RaceListSidebar.tsx:198-200`,
  `total_matched`): this is the day-list figure, refreshed at the list
  cadence (hence stale-looking). Either relabel it so it doesn't read as
  live, or retire it in favour of the race-page live figure — your call;
  keep it honest (don't show a stale number as if it's current).
- Display-only — both fields already exist on their payloads.

### 4. Refresh-cadence review (item 3 residual)
Review that the race-page + BetLog surfaces refresh to keep up with the
60s settlement sweep and matched-status changes (the "amber unmatched
recheck" concern). This is a **review**: if a query is under-refreshing
(e.g. a bet feed / activity board that only refetches on mount), add a
sensible refetch/invalidation; if they're already fine, say so and change
nothing. Don't over-poll. Report what you found.

**OUT of scope:** the FB auto-select-on-switch walkthrough (item 1) — a
live operator walkthrough, not a build.

## Fences
- **Bet-safety:** display-only except item 2's price, which is bounded
  above — never modify placement / settlement / reconciliation / money
  calculation. If surfacing the price would touch the money path, do the
  stake-only fallback and flag. No money-path files otherwise.
- Frontend gate is `npm run build` (vitest doesn't typecheck); rebuild
  dist app-down. `bethub-v3` git: commit + push GREEN only, co-author
  trailer.
- Keep the operator-locked BetLog column ORDER — P&L appends at the end,
  nothing reorders.

## Tests
- BetLog row: P&L renders per state (won/lost/pending/void), 🛡 shows on
  `safety_net`+promo bets and NOT on FB / plain-promo / bare bets.
- Activity board: unmatched lay shows "Unmatched $X…" not "$0.00 @ 0.00";
  matched rows unchanged.
- Total-matched: race page renders the live figure; sidebar no longer
  reads as live-when-stale.
- `uv run pytest` + `npm run build` green. Beat baselines: backend 1530 /
  frontend 249 at HEAD `abd84e1`.

## Report
`ui_pass3_report.md` in bethub-rebuild: what shipped per item; the item-2
grounding result (was the lay price persisted? → echoed, or stake-only +
flagged); the refresh-cadence findings; suites; commit. Flag anything
that needs an operator decision (esp. the item-2 price if it fell to
stake-only). S189 status: all display-only bits are implemented-not-live
until the next race-day look.
