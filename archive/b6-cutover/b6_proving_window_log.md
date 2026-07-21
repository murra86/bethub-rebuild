# Gate 9 — proving-window log

Running tally for the three ticks + per-day operator sign-offs.
Guide: `b6_proving_window_guide.md`. Gate table: `b6_scope.md`.

## Tick status

| Tick | Status | Evidence |
|---|---|---|
| 1. Clean AU racing day | **OPEN** | Day 2 not counted either (see below) — settlement was fully self-serve this time, but the day needed supervised store corrections (promo variant, credit re-book, duplicate, cycle joins). The S235 race-page/promo redesign targets exactly the friction that caused them |
| 2. Live interlock-refusal trip | **DONE — Day 1 (2026-07-08)** | Deliberate drill 11:43–11:45 ACST: two lay attempts refused pre-send (`streaming_disconnected`), both in `placement-audit.jsonl`; feed self-reconnected 0.4 s after Wi-Fi restored |
| 3. Real settlement beyond −$4.91 | **DONE — Day 2 (2026-07-08)** | FIVE automatic worker settlements of real lays, all correct-money: −$364.71 (Sesh), +$39.41 (Bettors Hope, after a live partial→full fill), +$79.91 (Exquisite Taste), +$6.79 (Miss Bay King Cole), +$7.92 (Vermont). Every figure verified on the live read path to the cent |

Gate-3 rider: **CLOSED — Day 1** (all 14 bets found their account-at-book in the picker first go; seeded balances held exact in live use).

**R1 (MEDIUM) partial-match watch: SEEN LIVE AND CLOSED — Day 2.** The Bettors Hope lay filled $4.57 of $42.84 at placement; the operator held (no re-fire), the remainder matched on Betfair, the reconciliation sweep updated the stored stake to the full fill, and the worker settled the right money. The park valve was never needed.

---

## Day 1 — Tuesday 2026-07-08 (Sandown / Canterbury / Ipswich)

**Operator sign-off (verbatim):**
> "Day 1: 14 bets placed and reconciled with TAB exactly, bonuses landed as
> expected. Not a clean day — settlement needed Claude's scripts and my promo
> terms were wrong at logging. One new promo discovered that were different
> across different accounts (but same book) - new promo has been added to the
> tool. Sign off."

**Day shape:** 14 promo bets (Tim ×6, Sarie ×4, Leigh ×4), all TAB, across 6
races. Cash −$582 (Silent Thinker won +$125; 13 losers −$707). Bonus bets
banked **$250**: Tim $50+$50, Sarie $50, Leigh $100 — all four credits
verified on the live read path against TAB, linked to their qualifiers.

**Why not counted as tick 1:** live-logged soft-book bets had no self-serve
settlement path — all 14 were settled via supervised store-adapter scripts
(backed up, read-back verified, balances derived exact). The gap was built
away same-day: BetLog settle door (won/lost/void, soft-book + pending only,
visible to the daily money check as `reason=operator_manual`) — bethub-v3
`9de0609`, suites 1399/134.

**Interlock drill (tick 2 evidence):** see tick table. Two side-notes from
the drill, both cosmetic/known: the bet modal surfaced the refusal as a raw
"API 503" (parking lot: plain-language label) and the health banner can't
update while the Mac itself is fully offline (browser pauses polling;
irrelevant to the real feed-drop failure mode, which the banner catches
within 20 s).

**Findings / lessons:**
1. **Promo terms differ per account at the same book.** TAB ran two versions
   of the run-2nd insurance on the same races: stake-back-in-bonus cap $50
   (Tim, Sarie) vs winnings-as-bonus cap $100 (Leigh). Bets were logged
   against the wrong template and corrected post-day (both variants now in
   the catalogue; Leigh's template carries an engine-approximation note —
   `return_pct=2.0` computes right only at cap-hit; winnings-based credit
   support is parked). **Standing habit adopted: before the first bet on any
   new promo, capture the terms as EACH account's betslip shows them.**
2. **Results feeds lag on finishing positions.** Betfair marks winner/loser
   immediately but who-ran-2nd needed The Racing API meets route (queried
   from the VPS); capture-side placings backfill hadn't landed hours later.
   Matters whenever a promo pays on exact position.
3. Stale pages misled twice (Leigh's balance, BetLog) — data was right
   underneath both times. Parking lot: refetch after bet logging.
4. Account-switching friction (two missed bets, Canterbury R1) was the
   Pi/SIM/router gateway build-out, NOT BetHub — being fixed in a separate
   session. Off BetHub's ledger.
5. Daily money check (`ops.settlement_review`) was blind to script-side
   settlements (it dates from worker log lines). The settle door closes this
   for operator settles going forward.

**Store writes this day (all supervised, backed up first
`bethub-20260708-preclose-day1.db`, read-back verified):** 1 new promo
template + 14 bet re-points + 14 strategy tags (store adapter / designed
edit path), 14 settlements (designed settlement write), 4 free-bet credits
(via the app's credit-in endpoint, amounts $50/$50/$50/$100).

**Free bets outstanding ($250):** first use of each will live-prove the
free-bet modal flow — treat as a window observation item.

---

## Day 2 — Tuesday 2026-07-08 evening (conversion day: Belmont / Bathurst / Redcliffe / others)

**Operator sign-off:** closing instruction "Do the close and drafts on open"
after confirming the cycle groupings table ("All correct") and the day's
balances; day run and closed in-session with Claude verifying every leg live.

**Day shape:** the $250 bonus conversion day (the S233 plan) plus an
operator-initiated Kate @ PointsBet insurance strand (10 qualifiers). Four
conversions completed: **$210 of bonuses → $162.53 cash (77.4%**, vs the 65%
working assumption): Sesh +$35.29 (70.6%), Bettors Hope +$39.41 (78.8%),
Exquisite Taste +$79.91 (79.9%), Vermont +$7.92 (~79%). Kate's strand: 10
qualifiers, 2 winners (+$225, +$34), 2 triggers (Solar Flare, Velocity
Miranda — both $10 bonuses credited and the first one converted same day).
Sarie's $50 bonus carries. End-of-day: zero unsettled bets, manual queue
EMPTY, `ops.settlement_review` clean, all five active account-at-book
balances derived exact.

**Why not counted as tick 1:** settlement WAS self-serve end-to-end (operator
settle buttons + five automatic worker settlements) — but the day needed
supervised store corrections: a wrong promo variant picked at logging (dense
near-identical picker labels; the trigger credited $10 cash instead of a $10
bonus before the re-point — deleted and re-credited through the proper door),
a Log Past Bet double-entry (form saved silently; duplicate deleted), manual
cycle joins (the modal never links its lay), and safety-net labels set after
the fact (the logging flow never sets the tag the credit gate requires).
None were money-path failures; all were promo/logging UX. The S235 redesign
(locked this close) targets each one.

**Findings / lessons:**
1. **Shape beats cap.** With stake ≤ cap, the credit amount is independent of
   the template's cap — what must be right at logging is the SHAPE (refund
   positions × return type). Anchors the promo-picker redesign (shape-first,
   cap off the slip).
2. **The credit gate and the logging flow disagree:** credit-in requires
   `strategy_tag=safety_net` + promo attached, but race-page logging sets
   only the promo. Every qualifier today needed a post-hoc tag before the
   watchdog could see it.
3. **R1 closed** (see tick table) — partial fills reconcile correctly.
4. Stale-page class bit twice more (silent Log Past Bet save → duplicate;
   race pages not refetching). Upgraded from niggle to redesign input.
5. The `credit-gaps` watchdog over-lists by design (it can't know finishing
   positions) — dismiss affordance queued.
6. Results self-serve: from S235 Claude calls win/lose + trigger status
   itself (Betfair result + place-market derivation); greyhound/harness
   place coverage is the honest gap to confirm.

**Store writes this day (all supervised, backed up first — four backups in
`~/.bethub/backups/`):** 1 promo re-point + 1 wrong-currency credit event
deleted + 1 replacement credit via the app's credit-in door; 1 manual FB back
via the Log Past Bet API + 1 deploy event via the app's own
`record_free_bet_deployment`; 1 duplicate bet deleted; 3 cycle joins; 12
strategy tags via the designed PATCH; 1 selection-name normalisation.
No code changes; bethub-v3 stayed at `9de0609`.

**Window state after day 2: ticks 2 + 3 DONE, rider CLOSED, R1 CLOSED —
tick 1 (one clean self-serve day) is the only evidence still open.**
