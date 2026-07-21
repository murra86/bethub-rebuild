# Free-bet conversion day — prep

**For:** the operator, before placing the $250 of TAB bonus bets.
**Written:** Session 234 (2026-07-08), grounded read-only against the live
code at `9de0609` and the store. Claude supports, watches, and records —
every bet today is yours.

**What's riding on the day (window scoreboard):** a real Betfair lay
settling through the automatic worker banks **tick 3**; a fully self-serve
day (you settle the TAB legs with the new buttons, no Claude scripts)
banks **tick 1**. Both are live shots, not guarantees — an honest miss
is fine, we just record it.

---

## 1. Logging a free-bet back (how the $250 draws down)

Your bonus inventory in the tool: **Tim $50 + $50, Sarie $50, Leigh $100**
— four separate bonus bets, each tied to the account that earned it.

- Place the bonus bet at TAB as usual. In the tool, log it the same way
  as any bet, but flip the **free bet** toggle on the log panel. Once
  you've picked the account and book, the panel shows that account's
  bonus-bet list — **tick the one you're using**. The tool may pre-tick
  it when there's only one candidate, but it never spends one without
  your tick.
- The moment the bet logs, that bonus disappears from the inventory and
  the account's bonus balance drops — that's the draw-down working.
  **No cash moves**: a free bet costs nothing to place, and if it loses
  there's nothing to lose. If it wins, TAB pays **winnings only** — the
  $50 stake itself never comes back. I've checked the money maths in the
  code: a won free bet credits the full winnings, exact against TAB.
- **Use the full face value as the stake** ($50 bets for the $50
  bonuses, $100 for Leigh's). Splitting a bonus across two bets isn't
  supported by the tool yet (parked item).
- "Conversion" in money: because the stake never comes back, a hedged
  free bet turns into roughly **65% of face value in locked cash** —
  that's the planning figure (~$160 out of the $250). Higher back odds
  convert better; the odds-aware version of that number is a parked
  item, so 65% is the working assumption today.
- **Right account matters**: the bonus only exists on the account that
  earned it — check the picker shows the account you're actually
  betting from before you submit.

## 2. The lay side — the hedge modal

The **⚡ hedge modal** on the race screen fires the Betfair lay. When a
free-bet promo is active it opens in free-bet mode and sizes the lay
with the free-bet formula (stake doesn't return, so the lay is smaller
than a normal hedge). It shows you the lay size, the liability (what
Betfair holds), and the locked profit before you confirm.

- **The safety catch (proven in Monday's drill):** if the live price
  feed isn't healthy, the tool refuses the lay **before anything
  reaches Betfair**. Known wart: the refusal currently shows as a raw
  "API 503" message — that IS the safety catch talking, not a broken
  tool. Wait for the feed to come back (usually seconds) and go again.
- Two confirm-gates you might hit, both deliberate: liability over
  **$500** asks you to confirm the dollar amount, and a lay price more
  than 10 ticks away from the live market asks you to confirm (catches
  a typo like 44 instead of 4.4).
- **The park valve:** at settlement time, if anything about the bet
  doesn't add up cleanly, the worker **parks it in the manual queue
  instead of guessing**. A parked bet is never money booked wrong —
  it's the tool asking for a human look. If something parks, tell
  Claude; don't try to fix it yourself.
- After the lay lands, the modal shows the result briefly, then hands
  you straight into the log panel in free-bet mode with the matched
  figure shown as a banner — log the TAB leg then and there.

## 3. The partial-fill watch (the one thing to watch closely)

A lay can **partially fill**: Betfair matches some of your money and
leaves the rest waiting. This has never happened to us live — today's
lays are the first realistic chance — and there's a known MEDIUM
watch-item on how the tool handles it, so eyes open.

- **What it looks like:** after placing, the modal (and the banner over
  the log panel) says something like *"Matched $12.40 — $7.60 still
  unmatched on the exchange."* Matched-in-full says "$0 unmatched".
- Note for greyhounds: any unmatched remainder dies at the jump (no
  in-play market). For gallops and harness it stays working by default.
- **If you see a partial fill:** carry on with your day — don't cancel
  or re-bet to "fix" it. Tell Claude: which race and runner, and the
  matched / unmatched dollar figures from the banner. Behind the
  scenes the tool should pick up the true matched amount on its own,
  and if settlement is at all unsure the park valve holds the bet for
  review rather than settling it wrong.
- **Either way, the outcome goes in the window log** — "partial fill
  handled cleanly" and "no partial fills occurred today" are both
  useful records.

## 4. How the day settles

- **Betfair legs (the lays): automatic.** The settlement worker stamps
  them when the race result lands — no buttons, no scripts. The first
  real lay it settles today is the **tick 3** evidence.
- **TAB legs (the free-bet backs): you settle them** with the new
  **Settle: Won / Lost / Void** buttons on the BetLog — first live use
  (they were built Monday evening and are proven in tests, but no one
  has pressed them on a real bet yet). They appear only on pending TAB
  bets, ask you to confirm, and every press is visible to the daily
  money check. A lost free bet still gets settled Lost — no cash moves,
  it just closes the bet out.
- **Nothing today should need a Claude-side script.** If you hit
  anything that seems to, stop and tell Claude — that's a window
  finding, not something to push through.
- **One honest gap, unlikely today:** if a free-bet back has to be
  **voided** (scratched runner, abandoned race), the void itself is
  fine — but the bonus does **not** automatically go back into your
  inventory in the tool. Tell Claude and it gets restored under
  supervision through the same door the credits came in by.
- Known niggle from day 1: pages don't always refresh themselves after
  logging — if a bet or balance looks missing, **refresh the page
  before worrying**. The data was right underneath both times this bit
  us on Monday.

## 5. How the day ends

1. All lays settled by the worker, all TAB legs settled by your
   buttons, nothing pending that shouldn't be.
2. Run the daily money check from the bethub-v3 folder:
   `uv run python -m ops.settlement_review` — your button-settles show
   up in it marked as operator settles (that visibility was built
   Monday precisely so this check sees your whole day).
3. Cross-check the tool's balances against **TAB and Betfair** the same
   way as day 1 — cash and bonus, account by account.
4. One-line sign-off for `b6_proving_window_log.md`, and the tick
   verdicts: did a real lay settle automatically (tick 3)? Was the day
   fully self-serve (tick 1)?

---

## Small print

- **Leigh's $100 template:** its credit maths in the catalogue is an
  approximation (exact only at cap-hit). That is **irrelevant to
  spending his $100 today** — it only matters if his winnings-style
  promo ever triggers a new credit-in. Nothing to do, just noted.
- The bonuses carry **no expiry inside the tool**, so they won't vanish
  from the picker — but TAB's own expiry clock still runs; that's yours
  to track.
- v3 is the app on **127.0.0.1:8787**; v2 (port 5000) is still
  system-of-record for everything else and doesn't know about today.
- First-live-use list for the window record: free-bet toggle +
  inventory picker, free-bet mode on the hedge modal, the settle
  buttons. Any friction with any of them is window evidence — say so
  even if it's small.
