# P&L logic audit — S260 (worklist 0t, audit half)

**Scope:** the money arithmetic behind every P&L figure the tool shows.
**Method:** read-only. Every number below was recomputed independently from the raw
stored fields and diffed against what the tool derives — nothing was accepted on
the strength of a comment or a passing test.
**Store:** `bethub-v3/data/bethub.db`, opened `mode=ro`, 30 Jul 2026. 336 bets
(332 settled), 54 Betfair markets, 68 promo credits, 54 cash-ledger events.
**Nothing was written to any database or to any code file.**

---

## FOR THE OPERATOR

**The core money arithmetic is right.** I recalculated the profit or loss on all
332 settled bets by hand, from scratch, and compared each one to what the tool
says. **Every single one matched — zero disagreements.** I did the same for
Betfair's commission across four real racing days and every one reconciled to the
cent. Cycle nets across dates also matched, hand-checked on twelve cycles.

**Your free-bet rule is being honoured.** A bonus's face value never appears in
any profit figure anywhere — not on the BetLog strip, not on the Balances
headline, not in the "where the money sits" totals. Bonuses show only as "Bonus
bets in hand", which is a separate box, correctly. When a bonus wins, the tool
counts the winnings only, at full value.

**The two-P&Ls problem you found is real, and it is bigger than a label.** The
BetLog period figure and the Balances headline answer genuinely different
questions. Right now they happen to be **identical ($2,225.99)** because you have
had almost no *cash* promo credits — your promos pay bonuses, and bonuses flow
into the bet figures naturally. The gap only opens when a book pays you cash. It
opened for about 74 minutes today (a $10 TAB cash credit, since corrected), and
it will open every time cash is credited from now on. My recommendation is at the
end of section 5 — you decide.

**Seven defects found. None of them is costing you money today.** The biggest is
a booby trap rather than a live error: there is a "conversion" box on the
log-a-past-bet screen with `0.65` shown as its example value, and anything you
type there **multiplies your real bonus winnings down** in every profit figure. On
a $50 bonus that wins at $10 you would see $292.50 instead of the $450 the book
actually paid you. No bet in the store has ever used it, so nothing is wrong
today — but it is one keystroke away.

**One thing the audit could not confirm.** The Balances "Self-check passed" tick
is weaker than it looks. I proved mathematically that it is *guaranteed* to pass
whenever the two sums run over the same rows — it is checking the tool against
itself, not against your accounts. It catches one real class of bug (the S259
lockstep problem, where one money read filters differently from the other) and it
is worth keeping for exactly that. It cannot detect a wrong price, a missing bet,
a missing deposit, or a correction booked with the wrong sign. Your Betfair
watchdog is the only check that compares against a real account, and it covers
Betfair only — the soft books are unchecked by anything but your eye.

**CONFIDENCE LEVEL: HIGH** on the per-bet arithmetic, the commission, the
free-bet treatment and the cycle nets — those are proven against real rows, not
argued. **MEDIUM** on the promo-credit reads, because there is so little cash-credit
history to test against (two events, ever). **HIGH** on the two-P&Ls analysis.
**LOW** on anything requiring a real Betfair statement — the store holds no
statement data, so the exact rounding rule Betfair applies is taken on the S249
evidence, not re-proven here.

**Recommended next steps, in order:**
1. **Kill the conversion box** on the log-a-past-bet screen (defect D1) — it is
   the only finding that can silently mis-state real money, and the fix is
   removing a field, not building anything.
2. **Decide the two-P&Ls question** (section 5). My recommendation: rename, do
   not unify, and add the cycle-complete figure as 0t's actual deliverable.
3. **Make the four "confirmation" screens use the same commission maths as
   BetLog** (defect D2) — a Betfair lay can currently show two different nets
   $3.26 apart depending on which screen you are looking at.
4. Leave the rest (D3–D7) on the 0t fix list; they are latent, sub-cent, or
   display-only today.

**SIGN-OFF: DEFECTS FOUND: 7** (0 arithmetic errors; 7 defects, all latent,
sub-cent, or display-only at today's data).

---

## AREA 1 — `bet_net_pnl`: BACK vs LAY, voids, part-matched

### VERDICT: **SOUND** — 0 mismatches in 332 settled bets

Every settled bet was recomputed from `matched_stake`, `matched_price`,
`settlement_state`, `side`, `is_free_bet` and the conversion-rate columns using an
independently written implementation of the §A.6 rules, then diffed row by row
against `bet_net_pnl`.

| | |
|---|---|
| settled bets recomputed | **332** (209 lost / 119 won / 4 void) |
| per-bet mismatches | **0** |
| independent total | **$2,225.99** |
| tool total | **$2,225.99** |
| difference | **$0.0000** |

**BACK vs LAY inversion — correct.** The identity is `gross cash return − cash
committed at placement`, and it collapses correctly on both sides:

- won cash back: `round2(S×P) − S` = winnings
- lost cash back: `0 − S` = −stake
- won lay: `(L + S(1−c)) − L` = `+S(1−c)` — the layer collects the backer's
  stake net of commission, **not** `S×P`
- lost lay: `0 − L` = −liability, with `L = round2(S×(P−1))`

The LAY branch correctly reads `settlement_state` as the *lay's own* perspective
and correctly treats the committed cash as the **liability**, not the matched
stake. Hand-verified live rows:

| bet | shape | stored | recomputed |
|---|---|---|---|
| `bet-86c45969…` | won LAY, part-matched S=28.25 @ 8.64, 8% | 25.99 | 28.25 − 2.26 = **25.99** ✓ |
| `bet-2a78ed58…` | won LAY, part-matched S=4.00 @ 6.6, 8% | 3.68 | 4.00 − 0.32 = **3.68** ✓ |
| `bet-21402f2e…` | won FB back, S=50 @ 10.0 | 450.00 | 50×(10−1) = **450.00** ✓ |
| `bet-8b3a1ce1…` | won FB back, S=100 @ 7.0 | 600.00 | 100×(7−1) = **600.00** ✓ |
| `bet-a5f3cfb2…` | voided FB back, S=50 @ 9.5 | 0 | **0** ✓ (face returns to inventory, not cash) |
| `bet-dfb09759…` | voided cash back, S=50 @ 4.8 | 0 | **0** ✓ (stake refund − stake committed) |
| `bet-60ce7b90…` | voided LAY, S=0, price NULL, `match_status=failed` | 0 | **0** ✓ |

**Voids — correct on both sides.** A voided cash bet nets exactly zero because the
stake refund cancels the committed stake; a voided free bet nets zero because the
face value was never cash. A voided lay returns the liability, netting zero. All
4 void rows verified.

**Part-matched — correct.** 5 rows carry non-zero `unmatched_stake` (4
`final_partial` won lays + 1 `failed`). All money derives from `matched_stake`
only; the unmatched remainder correctly contributes nothing, on both the
liability and the return side. `bet-2a78ed58` is the sharpest case: $4.00 matched
of a $38.34 request, and the P&L reflects the $4.00 only.

**Settled vs pending boundary — correct.** `_SETTLED_STATES` = {won, lost,
voided}; `_PENDING_SETTLEMENT_STATES` = {NULL, pending, provisional}. The 4
unsettled rows (2 `pending`, 2 NULL) contribute no P&L and $90.00 of committed
cash. The two sets are disjoint and jointly exhaustive over the vocabulary
actually present in the store.

### DEFECT D1 — the free-bet conversion rate haircuts *realised* winnings

`_bet_cash_return` multiplies a won free bet's winnings by
`realised_conversion_rate ?? free_bet_conversion_rate ?? 1`:

```python
winnings = matched_stake * (price - Decimal("1"))
return _cent(winnings * conversion)
```

A conversion rate is a **forward-looking EV assumption** (what a bonus is worth
before you hedge it). Multiplying *realised* winnings by it makes the P&L report
less money than the book actually credited.

- **Live exposure today: zero.** All 61 free-bet rows have both conversion columns
  NULL → conversion = 1 → FB winnings are exactly `(odds−1)×stake`, which is what
  the operator's rule requires. Verified by query.
- **But it is primed.** `ui/web/src/routes/LogPastBet.tsx` renders a `conversion`
  input for free bets with `placeholder="0.65"`, and posts it straight into
  `free_bet_conversion_rate`. Typing the placeholder value into a $50 bonus that
  wins at $10 would report **$292.50 instead of $450.00** — a $157.50 silent
  understatement, on a screen that gives no hint the number touches P&L.
- `realised_conversion_rate` is documented as "W5 populates at settlement" but is
  written nowhere in the codebase; it is NULL on every row.

**Where the fix belongs:** remove the field from the manual-entry form (the EV
engine already owns the 65% assumption — see area 8), or fence the multiplier so
it applies only to a *projected* figure and never to `bet_net_pnl`.

### CANNOT VERIFY — settlement-date attribution

The `bets` table has no `settled_at` column (only `last_reconciled_at`, which is
NULL-heavy). Every date-windowed P&L therefore attributes profit to **placement**
date. A bet placed 18 Jul and settled 19 Jul books its result to 18 Jul. I cannot
verify or correct settlement-date attribution from the store as it stands, and no
figure in the tool currently claims to do it. This is structural input for 0t: 6
cycles in the store span two calendar dates.

---

## AREA 2 — Betfair commission (S250 0g allocation + S247 mixed-market rebate)

### VERDICT: **SOUND** — reconciled to the cent on four real settlement days

Commission was recomputed independently per market from Betfair's stated rule
(*rate × the market's positive net, rounded to the cent, nothing on a net-loss
market*), then compared against the tool's allocated shares.

| day | settled cash lays | markets | independent | tool | diff |
|---|---|---|---|---|---|
| 2026-07-18 | 20 | 15 | **$52.18** | **$52.18** | $0.00 |
| 2026-07-22 | 6 | 6 | **$10.56** | **$10.56** | $0.00 |
| 2026-07-25 | 21 | 20 | **$59.47** | **$59.47** | $0.00 |
| 2026-07-29 | 3 | 3 | **$6.20** | **$6.20** | $0.00 |

**Per-market mismatches: 0. Per-bet share mismatches: 0 of 54.**

**The S247 mixed-market rebate is doing real work and doing it right.** On 18 Jul
the naive per-winning-bet charge would have been **$58.66**; Betfair's actual
charge on the positive market nets is **$52.18**. The rebate bridge returns
exactly the **$6.4792** difference — the Morphettville R3 class, reproduced from
the live rows. Two won lays on net-loss markets (`1.260299962` net −$165.40 and
`1.260319975` net −$264.93 on 25 Jul) correctly carry **$0.00** commission and
show their full gross.

**The 0g cent-rounding + largest-remainder allocation is structurally correct.** I
property-tested all 54 markets:

- every per-bet share is a whole-cent amount — **0 violations**
- every share is ≥ 0 — **0 violations**
- every share is within 1¢ of its unrounded raw value — **0 violations**
- **every market's shares sum exactly to that market's half-even rounded total** —
  **0 violations** (the S247 item-2 contract, verified not assumed)

**Mixed commission rates handled.** Two markets carry a 10% rate against the 8%
default (`1.260296443`, `1.260319975`); the allocation is rate-per-row, so a
mixed-rate market allocates correctly rather than applying one blended rate.

**Grouping is per (account, market)**, which matches how Betfair charges — a
second account laying the same race is a separate commission pot. Correct.

### CANNOT VERIFY — the rounding *mode*

The store holds no Betfair statement or commission-charge data. I can prove the
allocation is internally exact and that half-even is what the code applies; I
cannot re-prove from this store that half-even is what **Betfair** applies. That
rests on the S249 live read (71.1728 derived vs 71.19 charged over 21 markets)
recorded in governance. The daily watchdog's funds identity is the standing
re-proof; if the mode were wrong it would surface there as a funds gap, not as a
per-line flag (the watchdog's own R1 amendment says so explicitly).

### DEFECT D10 (latent) — a Betfair BACK bet would be left out of the market net

`_is_settled_cash_lay` restricts the netting population to `side='LAY'`. Betfair
nets commission across a market including any **back** bet's profit. Today: **0
Betfair back bets** in the store (all 61 Betfair rows are lays; the only 3 explicit
BACK rows are at TAB). The day a Betfair back bet wins on a market that also holds
a losing lay, the tool will under- or over-state that market's commission.

---

## AREA 3 — Free-bet treatment

### VERDICT: **SOUND** on all three arms

**(a) An FB stake never subtracts from cash.** `_bet_cash_stake_committed` returns
`Decimal("0")` for `is_free_bet=True` before any other branch. `_bet_pending_cash_stake`
likewise. Verified against the 61 FB rows: total FB matched stake is $2,828.00 and
none of it appears anywhere in `books_cash` or in the committed-cash total.

**(b) FB winnings = `(odds−1)×stake`.** Confirmed on all 6 won FB rows (see the
area-1 table). Rounded to the cent HALF_UP, which matches how a book credits.
Subject to defect D1 above if a conversion rate is ever entered.

**(c) Un-deployed FB face value appears in NO P&L figure.** Traced every consumer
of `total_face_value` / `free_bet_balance` in the codebase:

| surface | figure | FB face value present? |
|---|---|---|
| BetLog period strip | `period.pnl` | **No** — `bet_net_pnl` over settled rows only; no FB term exists in the fold |
| BetLog per-row P&L | `bet.pnl` | **No** — same derivation |
| BetLog cycle chain | `Net:` line | **No** — sums `bet.pnl` only |
| Balances headline | `pnl` = `settled_pnl + promo_cash` | **No** — no FB term in either component |
| Balances `cash_view` | movement-side identity | **No** |
| Balances `books_cash` / `operation_cash` | Location-1 cash | **No** — `cash_balance` and `free_bet_balance` are separate model fields |
| Balances "where the money sits" person total | `rows.cash + float` | **No** — verified in `Balances.tsx:349` |
| Balances "Bonus bets in hand" tile | `bonus_value` | **Yes, correctly** — its own tile, labelled as bonuses, never summed into money |
| Racing accounts context | `free_bet_balance` | **Yes, correctly** — a separate field for the placement screen |
| exports | — | **No export surface exists** (no CSV/download endpoint or client code in the repo) |

FB face value today is $0.00 across 0 credits in hand, so this is verified
structurally rather than numerically — but the structure is clean: there is no
code path that adds a face value into a P&L sum.

---

## AREA 4 — Promo credits: finalised + S259 supersession, in lockstep

### VERDICT: **SOUND** on the two money reads; **DEFECT** on two peripheral reads

Every consumer that touches promo credits was enumerated by grep and inspected.

| # | consumer | sums money into P&L? | `status = finalised`? | supersession-aware? | verdict |
|---|---|---|---|---|---|
| 1 | `balance_derivation.compute_account_at_book_balance` (cash credits) | **yes** | yes (`CreditStatus.FINALISED`) | yes (`supersedes_event_id` set) | **SOUND** |
| 2 | `cash_flow.pnl_dashboard` (`promo_cash`) | **yes** | yes | yes (`NOT IN (SELECT supersedes_event_id …)`) | **SOUND** |
| 3 | `promo_derivations.compute_free_bet_inventory` | no (bonus tile) | **NO** | yes (chain walk) | **DEFECT D4** |
| 4 | `bets._triggered_credits` (BetLog insurance marker) | no (display) | yes (skips `rejected`) | yes (skips revoked + rejected supersessions) | **SOUND** (S259 fix confirmed) |
| 5 | `settlement_review._manual_credits_for` | no (display) | **NO** | **NO** | **DEFECT D5** |
| 6 | `bets._reassign_closure` (`_promo_terminal_type`) | no (gate) | yes (rejected = dead terminal) | yes | **SOUND** |
| 7 | `settlement_review.ledger_coherence_lines` (6 sweeps) | no (gate) | n/a | yes (`superseded` set) | **SOUND** |
| 8 | `promos` router, `credit_gap`, `fb_credit`, `fb_correction`, `correct_promo_chain`, `correct_promo_selection` | no — write/detect side | n/a | yes | **SOUND** |

**The S259 lockstep holds where it matters.** Consumers 1 and 2 are the two sums
the Balances self-check compares for exact equality, and they apply *identical*
filters. Proven on the live corrected chain: the finalised $10.00 TAB cash credit
(`a4a92ee0…`, 13:11 today) is superseded by a `rejected` credit (`3f56c253…`,
14:25 today, notes: *"Wrong promo picked at log time: TAB paid a free bet, not
cash"*). Both money reads return **$0.00** promo cash. Without the filters the
figure would be $10.00 or $20.00. Correct.

**One asymmetry to note in the filter shapes.** Consumer 2 reads the raw JSON with
`payload.get("status", "finalised")` — a payload missing `status` defaults to
counted. Consumer 1 goes through the pydantic model, where `status: CreditStatus`
is **required**, so a payload missing `status` would raise rather than count. No
such row exists (all 68 credits carry an explicit status) and neither behaviour is
wrong on its own, but the two do not fail the same way, which is precisely the
class S259 was about.

### DEFECT D4 (latent) — FB inventory ignores credit `status`

`compute_free_bet_inventory` resolves availability purely by walking the
supersession chain to its terminal event; it never inspects
`FreeBetCreditedPayload.status`. A `free_bet_credited` written with
`status='provisional'` or `status='rejected'` (both valid `CreditStatus` values)
and nothing superseding it would count as **available bonus face value** in
"Bonus bets in hand" and in the placement screen's FB picker. Today: all 66 FB
credits are `finalised` ($2,985.00), so exposure is zero. Severity is limited by
the fact that FB face value never reaches P&L (area 3) — this is a bonus-inventory
overstatement risk, not a P&L one. It is nonetheless the exact lockstep asymmetry
S259 warned about: cash credits filter on status, bonus credits do not.

### DEFECT D5 (latent, display) — "MANUAL CREDITS TODAY" ignores status and supersession

`settlement_review._manual_credits_for` selects on
`credit_source='operator_manual_amount'` and `recorded_at LIKE '<date>%'` with no
status or supersession filter. A hand-typed credit later revoked or rejected would
still be listed as a credit that day, with no marker. Today's rejected credit has
`credit_source='triggered'`, so it does not surface — exposure zero. The daily
check's own contract ("hand-typed credits are money the doors did not compute;
list every one") makes an unmarked rejected credit actively misleading.

---

## AREA 5 — THE TWO P&Ls (operator-found gap — DOCUMENTED, NOT FIXED)

### VERDICT: **DEFECT — confirmed exactly as the operator described. Decision pending; no change made.**

### What each figure actually contains

| component | BetLog period strip (`period.pnl`) | Balances headline (`pnl`) |
|---|---|---|
| settled bet net P&L | **yes** | **yes** |
| — free-bet winnings (at full value) | yes | yes |
| — Betfair commission, per-market allocated | yes | yes |
| finalised promo **cash** credits | **NO** | **yes** |
| un-deployed bonus face value | no | no |
| `book_correction` / watchdog ledger adjustments | no | no (see D3) |
| deposits, withdrawals, funding, remittance, profit share | no | no |
| date scope | the filtered window, on **placement** date | **lifetime since day 0**, unscoped |
| pending money | separate field, `requested_stake`-based | separate field, matched-stake / lay-liability-based |
| source | `ui/api/routers/bets.py::_period_stats` | `ui/api/routers/cash_flow.py::pnl_dashboard` |

**The structural divergence is exactly one term: finalised promo cash.**
`dashboard_pnl − betlog_style_pnl ≡ Σ(finalised, non-superseded promo cash in scope)`.

### Quantified on real data — last 14 days, per day

| date | BetLog-style | promo cash | dashboard-style | gap |
|---|---|---|---|---|
| 2026-07-17 | 0.00 | 0.00 | 0.00 | **0.00** |
| 2026-07-18 | 1,010.56 | 0.00 | 1,010.56 | **0.00** |
| 2026-07-19 | 245.93 | 0.00 | 245.93 | **0.00** |
| 2026-07-20 | −6.54 | 0.00 | −6.54 | **0.00** |
| 2026-07-21 | −195.00 | 0.00 | −195.00 | **0.00** |
| 2026-07-22 | 122.20 | 0.00 | 122.20 | **0.00** |
| 2026-07-23 | −60.00 | 0.00 | −60.00 | **0.00** |
| 2026-07-24 | 0.00 | 0.00 | 0.00 | **0.00** |
| 2026-07-25 | 683.17 | 0.00 | 683.17 | **0.00** |
| 2026-07-26 | −30.00 | 0.00 | −30.00 | **0.00** |
| 2026-07-27 | −20.00 | 0.00 | −20.00 | **0.00** |
| 2026-07-28 | 118.19 | 0.00 | 118.19 | **0.00** |
| 2026-07-29 | 367.13 | 0.00 | 367.13 | **0.00** |
| 2026-07-30 | −9.65 | 0.00 | −9.65 | **0.00** |
| **TOTAL** | **2,225.99** | **0.00** | **2,225.99** | **$0.00** |

**Headline divergence: $0.00 across the last 14 days.** Peak divergence in the
store's whole history: **$10.00**, for the ~74 minutes on 30 Jul between the TAB
cash credit being finalised (13:11) and being rejected (14:25).

**Why the number is currently zero, and why that is not reassurance.** The
operation's promos pay **bonuses**, not cash: 66 free-bet credits ($2,985.00) vs 2
cash credits ($10.00, one of them since rejected). Bonus value reaches P&L
*naturally*, through the FB bet's own winnings, so no term is missing. The gap is
zero because the divergent term has barely been used — not because the two
figures are reconciled. Every future cash credit (goodwill payments, cash-back
promos, the Allbets-style cash arms) widens it one-for-one.

### The related complaint — "insurance days look artificially negative" — is a DIFFERENT gap

This one is not about promo cash and would not be fixed by adding the promo term.
Hand-verified on cycle `87957d21…` (2 dates, 5 bets):

| bet | shape | net |
|---|---|---|
| qualifier back, $50 @ 3.8, `safety_net` + promo | lost | **−50.00** |
| lay hedge | voided | 0.00 |
| FB $50 @ 9.5 (insurance payout, deployed) | voided | 0.00 |
| FB $50 @ 11.0 (re-deployed 19 Jul) | lost | 0.00 |
| lay $38.70 @ 13.0 | won | **+35.60** |
| | **cycle net** | **−14.40** |

That **−$14.40 is the true money** and the tool renders it correctly: $50 cash out,
a $50 bonus in (correctly worth nothing until converted), $35.60 captured on the
hedge. Nothing is missing. The figure *reads* artificially negative on the
qualifier's day because the conversion happened the next day — an **attribution**
problem, not an inclusion problem. This is exactly what 0t's cycle accounting is
for, and it is a stronger argument for a third figure than the promo-cash term is.

### RECOMMENDATION (operator decides)

**Do not unify. Rename, then add a third figure.** Reasoning:

1. **Unifying would destroy information.** The two numbers are not two attempts at
   the same quantity. BetLog's answers *"how did my betting decisions do in this
   window?"* — cash promo credits are not betting decisions and folding them in
   would corrupt a strategy-evaluation number with book generosity. The Balances
   headline answers *"how much better off is the operation since day 0?"* — that
   one must include every dollar received, cash promos included. Both questions
   are legitimate and the operator asks both.
2. **A label change alone is necessary but not sufficient.** It stops the "why do
   these disagree?" confusion, which is real, but it does not address the
   insurance-day attribution problem above — and that is the one that actually
   distorts your read of a strategy.
3. **The third figure is what 0t was commissioned to build.** A *cycle-complete*
   P&L: attribute a cycle's whole net to the date the cycle **closed**, with every
   member's bet P&L plus any in-cycle promo cash, and a cycle held open until its
   bonus is deployed-or-expired. That single figure answers "did insurance make
   money last week?" honestly, which neither existing number does.

**Concretely:**
- BetLog strip: relabel **"Bet results (this window)"** with a hover note *"bet
  outcomes only — cash promo credits are not included"*.
- Balances headline: relabel **"Total operation P&L (since <day 0>)"** with the
  breakdown already available on the response (`settled_pnl` + `promo_cash`)
  shown as a two-line subtitle, so the difference is visible rather than
  inferred.
- Then build the cycle-complete figure as 0t's deliverable, and make **that** the
  number the operator reads for strategy questions.
- Do **not** put the promo-cash term into the BetLog strip. It would make the two
  numbers agree and simultaneously make the strip answer a question nobody asked.

### DEFECT D7 (latent) — the two "money at risk" figures also differ

Not the same gap, but the same shape and worth folding into the same decision.
`pnl_dashboard.pending_at_risk` uses `pending_bet_stake_total` (matched stake for
a back, **derived liability** for a lay). `BetLog period.pending_stake` uses
`row.requested_stake` and applies no lay treatment at all. Today both read
**$90.00** (4 pending cash back bets, matched == requested). A single pending lay
would split them: the dashboard would show the liability, BetLog the requested
stake — for a $38 lay at 13.0 that is **$456.00 vs $38.00**.

---

## AREA 6 — the Balances exact-zero self-check

### VERDICT: **DEFECT — the check is an algebraic identity of the same inputs. It proves far less than "Self-check passed" implies.**

`self_check_ok` asserts `cash_view + pending_at_risk − pnl == 0.00`. It reads as
two independent ledgers agreeing. It is not.

### Proof that it cannot fail (given a shared row set)

Expanding the definitions:

```
books  = Σdeposits − Σwithdrawals + Σaab_adj + Σpromo_cash
         − Σstake_committed + Σcash_return + rebate
floats = Σfunding − Σremit − Σdeposits + Σwithdrawals
         − Σprofit_share + Σholder_adj

cash_view = books + floats + Σremit + Σprofit_share
            − Σfunding − Σaab_adj − Σholder_adj
          = Σpromo_cash + Σ(cash_return − stake_committed) + rebate
          = Σpromo_cash + settled_naive_net − pending + rebate
```

and `pnl = settled_net_with_shares + Σpromo_cash = settled_naive_net + rebate +
Σpromo_cash`. Therefore `cash_view + pending − pnl ≡ 0` **identically**. Every
cash-flow term cancels; the identity is the *same per-bet derivation and the same
promo filter* written on both sides of an equals sign.

**Verified numerically on the live store:**

| | |
|---|---|
| `cash_view` as coded | 2135.99000000000000000 |
| algebraic collapse prediction | 2135.9900 |
| difference | **0E-17** |
| settled naive net | 2219.5172 |
| rebate bridge | 6.4728 |
| naive + rebate | **2225.9900** = `settled_pnl` |
| self-check difference | **0E-17** → passes |

### What it DOES prove (keep it for these)

1. **Filter lockstep — the S259 class.** If `balance_derivation` and
   `pnl_dashboard` ever disagree about which credits count (finalised, superseded,
   status-missing), the identity breaks by exactly the disputed amount. This is
   real, and it is the one reason the check earns its place.
2. **Settlement-state vocabulary drift.** `pending` counts states in
   {NULL, pending, provisional}; committed-cash subtraction covers every
   non-settled row. A row appearing with a state in neither set (a new state
   string, a typo'd reclass) breaks the identity. Genuinely useful.
3. **That the two code paths' rounding still agrees to the cent.**

### What it does NOT prove — the tick means none of this

- **Nothing about reality.** It never touches a bookmaker or exchange. It cannot
  tell you a stake, price, or outcome is right. A wrong `matched_price` flows
  identically into both sides and the check still passes.
- **Compensating errors are invisible by construction.** Both sides are built from
  the *same* row values, so any error in a row is present on both sides and
  cancels. There is no arrangement of wrong bet data that this check can detect.
- **Missing events are undetectable.** An unrecorded credit, an unlogged bet, a
  deposit never entered — the check has no notion of absence. It sums what is
  there.
- **Wrong-signed corrections pass silently.** The watchdog module's own R3
  amendment states this: *"the pnl self-check is neutral to either sign — a
  wrong-signed booking would pass it silently and DOUBLE the gap."*
- **Soft-book balances are entirely unchecked** by this or anything else. The
  account watchdog compares against a real account for **Betfair only**; TAB,
  PointsBet, CrownBet, BetRight, Neds, Ladbrokes, AllBets, TABtouch, UpYaGo have
  no automated real-account comparison at all (10 of the 11 book lanes in the
  store, holding the majority of the $12,301.35 books cash).
- **Bonus inventory is outside the identity.** FB face value appears in neither
  side, so a wrong bonus balance cannot break the check (see D4).

**Recommended wording change (no build):** replace "Self-check passed" with
something that claims only what it proves, e.g. *"Both money reads agree ✓ (this
checks the tool against itself, not against your accounts)"*. The current label
invites the operator to treat an internal consistency check as account
verification — which is exactly the reliance the $29.67 S247 hand-catch showed to
be unsafe.

### DEFECT D3 — corrections are excluded from the P&L headline by construction

`cash_view` subtracts `Σaccount_at_book_balance_adjustment`, while `books` adds it
— so ledger adjustments cancel out of `cash_view` and appear in **no** P&L figure.
That is correct for `day_0_opening` (opening capital is not profit) but **wrong for
`book_correction`**: watchdog cent-truings are real money the exchange moved that
the derivation missed, and they are profit or loss. Both reasons share one event
type, and the dashboard excludes the type wholesale.

Live magnitude: the 5 `account_at_book_balance_adjustment` rows net **−$0.01**
(one −$0.01 truing, plus two +$0.004 truings each paired to a reversal by the S257
fix). Trivial today; unbounded in principle, since the same channel is where any
future book-side correction lands.

---

## AREA 7 — cycle netting across dates

### VERDICT: **SOUND** on the arithmetic — 0 mismatches in 12 hand-recomputed cycles; **DEFECT** on cycle *completeness*

Twelve cycles recomputed independently — all 6 multi-date cycles in the store plus
the 6 largest single-date cycles — against the `bet_net_pnl` sum
`ops/settlement_review.py` renders under "CYCLES TOUCHED TODAY" and
`BetLog.tsx:402` renders as the CycleChain `Net:` line.

| cycle | bets | dates | rendered net | hand-recomputed | diff | in-cycle promo cash |
|---|---|---|---|---|---|---|
| `87957d21` | 5 | 2 | −14.40 | **−14.40** | 0.00 | 0.00 |
| `15dee66c` | 3 | 2 | −11.30 | **−11.30** | 0.00 | 0.00 |
| `408baadd` | 3 | 2 (18→20 Jul) | 56.91 | **56.91** | 0.00 | 0.00 |
| `77999881` | 3 | 2 | −15.15 | **−15.15** | 0.00 | 0.00 |
| `c78b17ae` | 3 | 2 | −17.13 | **−17.13** | 0.00 | 0.00 |
| `d848dea5` | 3 | 2 | −15.42 | **−15.42** | 0.00 | 0.00 |
| `0040c769` | 3 | 1 | −24.01 | **−24.01** | 0.00 | 0.00 |
| `02f6668f` | 3 | 1 | −13.30 | **−13.30** | 0.00 | 0.00 |
| `033108e0` | 3 | 1 | −14.91 | **−14.91** | 0.00 | 0.00 |
| `03aff731` | 3 | 1 | −14.40 | **−14.40** | 0.00 | 0.00 |
| `065ef2f8` | 3 | 1 | −12.10 | **−12.10** | 0.00 | 0.00 |
| `0a60077d` | 3 | 1 | −9.21 | **−9.21** | 0.00 | 0.00 |

**Mismatches: 0.** Crossing a date boundary changes nothing about the arithmetic —
the cycle sum is over `cycle_id`, with no date term, so a two-date cycle nets
identically to a one-date one. `settlement_review` reads commission shares from a
**whole-store** query, so a market whose sibling lays sit outside today's cycles
still nets to Betfair's true commission; BetLog's CycleChain goes through the feed
route, which re-reads each touched market's siblings (`_lay_commission_shares`).
Both are correct.

**In-cycle promo cash: $0.00 across all 12** — there are no live finalised
promo-cash credits attached to any bet in the store, so the "plus in-cycle promo
cash" arm of the check evaluates to zero everywhere and the rendered net equals
the member sum trivially. **Note for 0t:** neither surface has *any* promo-cash
term. `settlement_review`'s net is `Σ bet_net_pnl` over settled members;
`BetLog.tsx:402` is `bets.reduce((s,b) => s + Number(b.pnl))`. When a cash credit
does land in a cycle, both cycle nets will understate it by the credit amount.
That is the same missing term as area 5, surfacing in a third place.

### DEFECT D8 — 32 cycles are not cycles

`cycle_id` groups are supposed to be a complete bet-and-hedge unit. In the live
store:

| cycle composition | count |
|---|---|
| 1 back, no lay | 154 |
| 1 back + 1 FB, no lay | 30 |
| 1 back + 1 FB + 1 lay | 27 |
| **1 lay only, no back at all** | **32** |
| 1 FB, no cash qualifier | 2 |
| 2 FB + 1 back + 2 lays | 1 |

The **32 lay-only cycles** (placed 18–30 Jul, e.g. `cycle-1ca6fcd7…` holding
`bet-df4dd0bb` LAY $22.65 @ 12.0 won) render a "cycle net" that is one leg of a
hedge with its back bet living in a different cycle. The net is arithmetically
correct for what it contains and **meaningless as a cycle**. The 2 orphan-FB
cycles are the mirror case: a converted bonus whose qualifier's loss sits
elsewhere, so the cycle shows a profit whose cost is booked to another cycle.

**The watchdog that should catch this sees only 24 hours.**
`cycle_pairing.list_unpaired_lays` filters on `CANDIDATE_LOOKBACK_SECONDS = 24*3600`,
so all 32 are already invisible to the daily check's "CYCLE PAIRING WATCH", which
currently reports *"Every recent lay is paired with its back."* That statement is
true and misleading in the same breath.

This is the single most important input this audit has for 0t: **cycle netting is
sound, cycle membership is not.** Building cycle-complete P&L on top of 32 broken
groups would produce a trustworthy-looking wrong number.

---

## AREA 8 — the S231 haircut rules: in governance, not in P&L code

### VERDICT: **CONFIRMED — the S252 finding stands, with one refinement**

| rule | in governance? | in code? |
|---|---|---|
| haircut $6–$10 screen EVs by ~3 pts | **yes** — `archive/b6-cutover/ev_validation_findings.md:66` ("Operational rule: haircut $6–$10…"), `sessions/SESSION_231.md:37`, `worklist.md:91`; S231 also parked "bake the $6–$10 haircut into the engine as a band correction" | **NO — absent from the entire codebase.** Grep for `haircut` across `domain/ workflows/ ui/ ops/ clients/ store/` returns nothing. |
| never treat a ~/⚠-flagged EV as firm | **yes** — `SESSION_231.md:37` | **NO** as an enforced rule — flags are rendered, but nothing downgrades or fences a flagged EV |
| FB conversion 65% | **yes** — locked S231 | **YES, and in the right place** (refinement to S252): `ui/web/src/ev/evEngine.ts:43` `DEFAULT_FB_CONVERSION_RATE = 0.65`, consumed by `racePortfolio.ts` for forward EV. The Python `pricing.py:51` `DEFAULT_FREE_BET_CONVERSION_RATE = 0.65` is **dead** — referenced only by its own test. |

So the accurate statement is: the **65% conversion is in code, in the forecast
engine, correctly** — it prices a bonus before you hedge it, which is exactly what
a conversion assumption is for. It correctly does **not** touch realised P&L
(that is defect D1's whole point: the one path where a conversion rate *can* reach
realised P&L is a bug, not this rule). The **$6–$10 band haircut** and the
**flagged-EV firmness rule** exist nowhere in code.

### Where they WOULD belong, if commissioned (one paragraph, no build)

Both are **forecast** corrections and belong on the EV side of the wall, never in
the P&L derivation — `bet_net_pnl` must keep reporting the money that actually
moved, or the tool loses its only honest record. Concretely: the $6–$10 band
haircut belongs in `ui/web/src/ev/evEngine.ts` as a band-conditional correction
applied at the same point `DEFAULT_FB_CONVERSION_RATE` is applied, so it lands on
every screen EV once and only once (the race panel, ConfirmCard, and the
portfolio optimiser all read through `racePortfolio.prepareBet`, so a single
correction there propagates without a second copy) — and it must be *carried into*
`promo_ev_at_log`, the column already written at placement, so an
after-the-fact accuracy review can compare haircut EV against realised outcome.
The flagged-EV firmness rule belongs one layer up as a *presentation and gate*
concern, not arithmetic: a flagged EV should surface as a non-firm band with no
single point value on the ConfirmCard, and — per the standing friction rule
(allow → flag → review later) — should warn without blocking. Neither rule should
alter `bet_net_pnl`, the Balances headline, or any cycle net; if the operator wants
haircut-vs-realised visibility, the right shape is a **comparison surface** (EV at
log vs realised, per band) rather than a haircut applied to realised money.

---

## DEFECT REGISTER

| id | area | defect | live exposure today | severity |
|---|---|---|---|---|
| **D1** | 1 | FB conversion rate multiplies **realised** winnings; manual-entry form offers the field with `0.65` as the placeholder | **$0.00** (all 61 FB rows NULL) — but one keystroke from a $157.50 understatement on a single $50 bonus | **HIGH (latent)** |
| **D2** | 2 | 4 surfaces call `bet_net_pnl` with no `commission_share`: `/v1/bet-corrections` `pnl_now`, reassign preview `pnl_delta`, and 7 single-bet `_to_feed_item` echoes (PATCH / settle / reclass / assign-cycle / provisional) | 50 of 54 won lays differ; 2 by **$3.26 / $3.23**, 48 sub-cent. Same bet shows two nets on two screens | **MEDIUM** |
| **D3** | 6 | `book_correction` ledger adjustments excluded from P&L along with `day_0_opening` (one event type, two meanings) | **−$0.01** | **LOW (structural)** |
| **D4** | 4 | FB inventory ignores credit `status`; a provisional/rejected FB credit would count as bonus in hand | **$0.00** (all 66 finalised) | **LOW (latent)** |
| **D5** | 4 | Daily check's "MANUAL CREDITS TODAY" applies no status/supersession filter | **$0.00** (today's rejected credit is `triggered`, not manual) | **LOW (latent)** |
| **D6** | 5 | Two P&L figures, one divergent term (finalised promo cash); plus placement-date vs cycle-close attribution | **$0.00** over 14 days; **$10.00** peak; widens with every cash credit | **MEDIUM — operator decision pending** |
| **D7** | 5 | Two incompatible "money at risk" definitions (matched/liability vs requested) | both **$90.00** today; a single pending lay would split them $456 vs $38 | **LOW (latent)** |
| **D8** | 7 | 32 lay-only + 2 orphan-FB cycles are incomplete units; the unpaired-lay watchdog only looks back 24h | 34 of 216 cycles | **MEDIUM — blocks 0t** |
| **D10** | 2 | Market commission netting excludes Betfair BACK bets | **0 rows** | **LOW (latent)** |

Also recorded, not counted as defects: **CANNOT VERIFY** the Betfair rounding mode
(no statement data in the store — rests on the S249 live read); **CANNOT VERIFY**
settlement-date attribution (no `settled_at` column exists).

---

## AUDIT SUMMARY

| area | verdict |
|---|---|
| 1 — `bet_net_pnl` (BACK/LAY, voids, part-matched) | **SOUND** — 0/332 mismatches · **D1** latent |
| 2 — Betfair commission (0g allocation + S247 rebate) | **SOUND** — 4 days reconciled to the cent, 0/54 share mismatches, 4 invariants clean · **D10** latent · rounding *mode* CANNOT VERIFY |
| 3 — free-bet treatment | **SOUND** — all three arms, every consumer traced |
| 4 — promo credits + S259 lockstep | **SOUND** on both money reads · **D4**, **D5** on peripheral reads |
| 5 — the two P&Ls | **DEFECT D6** — confirmed, quantified, recommendation given, **not fixed** |
| 6 — Balances self-check | **DEFECT** — algebraic identity, proven; useful for 2 narrow classes only · **D3** |
| 7 — cycle netting across dates | **SOUND** — 0/12 mismatches · **DEFECT D8** on cycle membership |
| 8 — S231 haircut rules | **CONFIRMED** absent from code (65% present, correctly, in the EV engine only) |

**Arithmetic errors found: 0** (332 bets, 54 markets, 12 cycles, 4 settlement
days, all independently recomputed and diffed).
**Defects found: 7** — none costing money at today's data; D1, D6 and D8 warrant
action.

*Read-only audit. No database was written. No code was changed.*
