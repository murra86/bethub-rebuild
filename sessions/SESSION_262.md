# SESSION 262 — Sat 1 Aug 2026 (race day, "bet-earlier" strategy day)

Operator verdict on the day: **successful.** This record covers the
race-day support work; the S260-armed capture deploy and the promo-pilot
first-race screen check have their own trails.

## Morning — Tim-TAB $10 free bet mis-booked as cash (FIXED)

Operator report: manual bet's $10 free bet "not showing — keeps
reverting to cash." Root cause: the bet (Shes Peakin, Parklands R5,
30 Jul, $10, `bet-53970cf4`) was logged under **Ins $25 Cash 2nd** when
the real TAB promo was **Ins $25 FB 2nd** — so the trigger banked $10
cash instead of a free bet. Third instance of the promo mis-pick class.
Fixed with `ops.correct_promo_selection --apply` (cash credit
superseded `a1a86071`, FB credit issued `ebb6fd1b`, bet re-pointed).
`ops.settlement_review` after: all coherence sweeps clean.
→ **Worklist 0x** (new): the two-click BetLog "change promo" button,
operator-flagged post-race-day.

## Midday — promo crunching: EW Cashback 4th/5th (Flemington R4)

Empirical answer from model.db (115k runners, 14+ fields, real finish
order): 4th/5th chance peaks ~19–21% for runners $4–$16; net EV on the
$100 EW promo bet ≈ +$13…$24 in the $4–$8 band, +$9…$19 at $8–$11,
negative past $16. Advice given: full $100, mid-priced runner, watch
the 14-runner minimum against scratchings. Confidence: HIGH on the
finish-position rates, MEDIUM on net dollars (TAB-vs-Betfair price
spread). Also flagged: no promo template exists for stake-back-4th/5th
— offered to add one before logging.

## Flag — "bet-earlier" strategy day

Operator employed deliberate early placement all day (well-before-race
through to jump). Recorded in
`bethub-analytical/analysis/early_placement/strategy_days.md` — any
timing/EV analysis must segment 1 Aug. First day with BOTH the morning
sweep live and spread placements.

## Evening — race-day notes batch (10 items)

**Corrections applied:**
- $10 Sarie-Ladbrokes FB credit `3343af97` **expired** (event
  `f94e8c3c`, sanctioned PromoStoreAdapter composition — no expiry door
  exists in UI/CLI; recorded as expiry, not revoke, so conversion stats
  stay honest).
- Doomben R4 $30 FB (Syrian Diamond): operator suspected the promo-bar
  selection was missed — **verified already correct** (deploy drew $30
  from a real Ladbrokes credit at placement; all 5 deploys map 1:1 to
  the five $30 split credits). No change.

**Open decision → S263:** Bet365 bonus-cash winnings are NOT tracked —
zero promo events for Bet365 ever, yet all 11 of today's Bet365 bets
carry "Bonus Winnings (Cash)". Today's 5 winners profit $599.50; the
uplift needs the actual % / cap from the operator before crediting.

**Investigated + queued (worklist 0y / 0z / 1a):**
- 0y — race-page TAB refresh on race selection (odds stale ≥1 min on switch).
- 0z — BetLog/modal batch: unmatched orders show 0.00@0.00 (Gilgandra
  Calmundi `bet-52a3614f`); reopen-modal/change-odds for unmatched; FB
  auto-select next credit after modal completes; matched-price truth
  (R7 Arkansaw Kid lay stored 7.6 asked vs 5.07 actual average — store
  the real matched average); modal lay stake from live best price (the
  R7 under-hedge, ~$20 light because stake was computed at asked 7.6).
- 1a — results log in-tool → auto-settlement + insurance triggering.

**Strategy flags recorded** (strategy_days.md): Sarie-TAB failed match
(first instance — never got on, price missed; a real cost of
bet-earlier); Townsville Tim-TAB $10 FB intentionally unmatched;
Doomben R4 intentionally unhedged.

**Shipped tonight (operator-directed, app closed for build):**
`dd7daec` — Burst Review shows event description for legless bets
(AFL H2H rows were rendering raw bet ids). 17/17 page tests, built,
pushed. Noted for 0z: quick-log sports bets carry no event date/time,
so unplayed games can't yet be hidden from the unsettled list.

## S263 OPENING (operator-directed)

1. Walk through today's feedback batch together.
2. Review the pending worklist overall (0u–1a + standing tail).
3. Carry-ins: Bet365 bonus % decision; 4th/5th promo template offer;
   Mango deploy still pending from S258 (port-forward + AdsPower
   profile + F19 cross button).
