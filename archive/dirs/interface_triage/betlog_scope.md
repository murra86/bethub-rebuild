# BetLog scope + manual-entry shape (locked S169)

**Status:** locked, Session 169 (2026-06-20 ACST).
**Amended S171 (2026-06-20 ACST):** promo display trimmed to
strategy-tag granularity (Option A) after the S171 BetLog
review found no bet→promo link in v3. See "Tucked into the
bet" below. No other scope change.
**Purpose:** the agreed scope the BetLog build brief (and,
after it, the after-the-fact manual-entry brief) is drafted
against. Not a build brief itself.
**Builds on:** S169 walk-through of v2's bet log
(`BetsPage.jsx` + `PendingSettlementTab.jsx` +
`SettledHistoryTab.jsx`), and v3 source grounding
(`store/schema/bets.py`, `ui/api/routers/racing.py`,
`workflows/bet_entry/v1/settlement.py`).

---

## Why BetLog comes before the free-bet work

The operator is cutting v3 over for live operational use and
must be able to **see his bets**. v3 has no bet-viewing
surface today — a settled-lost insurance qualifier vanishes
into the data with nowhere it shows up. So the free-bet
"placed?" confirm has no home until BetLog exists. Rather
than build a throwaway confirm-worklist now and the real
BetLog later, build BetLog properly and land the confirm
inside it. No rush to cutover; better ready than rushed.

---

## BetLog — the locked scope

### The frame

- **One page**, pending and settled bets **together**, with
  a state filter to flip between them or see all.
- **No manual-settle console.** v2's "Pending" tab is really
  a manual W/L/V settlement workspace; v3 settles itself off
  Betfair and routes ambiguous cases to the existing
  burst-review queue, so BetLog is a **viewing** surface, not
  a settlement console.

### Layout

- **Flat list, newest-first.** No race grouping (v2 grouped
  under each race and auto-opened all — busy to navigate for
  a log you read rather than settle).

### Filters (across the top)

- **Account** (persona — all that persona's bets)
- **Account-at-book** (that persona at one book)
- **Book** (all personas at one book — the account-health
  lens; recommended, operator to confirm at brief review)
- **Promo type**
- **Date range**
- **State toggle:** Pending / Settled / All

### On the row (always visible — one clean scannable line)

- Selection / runner
- Side (Back / Lay)
- "Free" marker — only when it's a free bet
- Stake @ odds
- State — Pending / Won / Lost / Void
- P&L — once settled
- Book + persona

### Tucked into the bet (visible on open)

- Bet id (a reference number, not something you scan)
- Exact timestamp (row keeps the date only)
- Commission detail
- Promo detail — strategy-tag granularity only (locked
  S171, Option A). Row shows the strategy tag (Safety Net
  / Price Booster / SGM / Synthetic Each-Way) as the short
  tag + the "Free" marker; the tuck-in shows the free-bet
  conversion rate. Full promo fine print (%, max stake,
  cash-vs-free-bet) is NOT shown — it isn't stored against
  the bet today (no bet→promo link in v3), revisited once
  the free-bet credit-in work lands a real promo record to
  hang it off.
- Cycle chain (insurance → free bet → deployed → net) —
  the busiest thing in v2; row shows a small "cycle"
  marker, the full chain opens up

### Actions on a bet

- **Edit** and **Delete** (you're looking at the bet, you
  fix a wrong stake or remove a mistake right there).
- The insurance **"placed?"** confirm lives here (feeds the
  free-bet credit-in work — replaces the throwaway worklist).

### Explicitly NOT in BetLog

- The manual W/L/V settle-event console (auto-settle +
  burst-review cover it).
- Manual "Add Bet" from scratch — that's a **bet-entry**
  capability, not a BetLog feature (it only lived on v2's
  bet log page by habit). See the manual-entry workstream
  below.

---

## Manual after-the-fact bet entry (separate workstream)

### Why it's a real cutover need

In a hectic Strategy 1 burst the operator sometimes fires a
bet and misses logging it, or has to leave and catch up
days later. Operationally he places first and logs later to
extract the EV. So v3 must let him log a bet **after the
race has run** — occasionally a couple of days after.

### The shape (locked)

A catch-up admin flow (never used mid-burst):
**date → venue → race number → runner** → the tool links it
through to the canonical Betfair stamp and writes the bet.

### The finding (S169 API-availability check)

The storage worry largely dissolves — **no new retention
build on our side:**

- **capture.db already holds it.** The VPS analytical store
  captures Betfair + the Racing API continuously and holds
  resulted races with the **Betfair Win market id, the
  selection id, and the finish position** — both the
  human-friendly picker fields and the canonical stamp that
  makes auto-settle + grouping work.
- **Live Betfair API is only a short window.** The S39
  Saturday probe saw a closed AU market readable for ~45 min
  unchanged, then it ages out; the market list favours
  upcoming races. Not a multi-day source.
- **The path was already designed.** The §2.8 bet-schema
  work already scoped "operator picks a resulted-race row,
  v3 lifts its `betfair_market_id` from that row" — so this
  is wiring an existing design in, not inventing one.
- **Clean boundary (DR-027/028).** Reading capture.db to
  fill the picker is the sanctioned reference pattern
  (vps_client reads by reference, no copy), not a violation.

### The one open question (opens the manual-entry brief)

**How many days back does capture.db actually keep resulted
races?** It runs continuously so likely well past a couple
of days, but the retention/pruning needs an empirical check.
This replaces the operator's original "how much storage /
what window" question — that no longer lands on us. This
check is the first step of the manual-entry brief (brief 2),
Claude-Chat-side, read-only against capture.db (VPS via SSH
tunnel, `start_process` Python, never copy).

### Auto-settle linkage — confirmed structurally safe

Every v3 bet (soft-book included) **must** carry a real
Betfair market id + selection id — the leg fields are
NOT NULL. Auto-settle reads exactly those off the bet
(`settlement.py:356-360`: `market_id = leg.betfair_market_id`
→ read the market → match `betfair_selection_id`). So a
logged bet can never float free of its event; if it's in
the system it's linked, settles, and groups. The trap the
operator flagged cannot happen in v3.

---

## Pre-cutover brief sequence (resequenced this session)

What began as a single free-bet brief is now **three briefs**
plus the still-pending launcher brief:

1. **BetLog** — the viewing surface above. Useful the moment
   it lands (you can see your book). S170 primary.
2. **After-the-fact manual entry** — date/venue/race-number/
   runner → capture.db → Betfair stamp. Opens with the
   capture.db retention check.
3. **Free-bet credit-in + cycle attribution** — the S168
   design, unchanged, EXCEPT its operator surface (the
   "placed?" confirm) now lands inside BetLog, so it depends
   on BetLog existing. Drafted third.

Plus the **launcher brief** (F9 throttle-to-disk + F10 port
override, consider F12) — still pending, independent.

Each is one bounded Code session; sequencing keeps Code from
drifting. No committed cutover date — ready beats rushed.
