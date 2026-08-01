# Betfair reconciliation fixes + account watchdog (brief, S247)

**Status: COMMISSIONED S247 (Tue 21 Jul, midday) — operator caught a
$29.67 derived-vs-real Betfair gap by hand. Fixes 1–3 build TONIGHT;
item 4 (watchdog) right behind (tonight if time, else next session).**

**S248 (Tue eve): fixes 1–3 were live since S247's deploy. Item 4
CORE BUILT tonight — R4 client extension (`9e9dd0c`) + watchdog
module w/ all R1–R5 amendments (`f410a6c`), suite 1704 green, every
review rule red-before proven (incl. the R3 sign round-trip through
the real derivation). Remaining = S249 opener: wire on-demand route
+ daily trigger + fault banner through the LIVE app's composed
client (a standalone ops CLI would open a parallel Betfair login —
rejected), then the operator-supervised first pass books the
standing 3¢ as its opening act.**
Money-path throughout: red-before tests, operator walkthrough of the
data correction before write.

## The gap, fully attributed

Tool Tim@Betfair $2,399.29 vs real $2,428.96 = $29.67.
= $23.21 (Richmond R2 under-record) + $6.49 (Morphettville R3
commission model) − ~3¢ line rounding. All other lines reconcile
exactly (incl. Belmont R6 = two partial lays summing 74.52; Ballarat
R4 = 25.99 exact).

## 1. Premature FINAL_FULL (code fix)

`workflows/bet_entry/v1/reconciliation.py` Step 3
(`fully_matched_via_orders`, ~:276-289): concludes FINAL_FULL +
unmatched:=0 whenever the orders read shows matched_size>0 with an
average price — never compares matched vs requested. Three live rows
hit it (all stamped pre-jump, recon then stops on terminal status):

- `bet-b80c6f9c` Richmond R2 Oscar Phoenix: matched 13.47 / requested
  38.70; remainder FILLED post-stamp → account paid on 38.70, tool
  settled on 13.47. **MONEY WRONG −$23.21.**
- `bet-86c45969` Ballarat R4 Vesta Bale: 28.25/37.20, remainder
  lapsed → money right, label wrong.
- `bet-2a78ed58` Pakenham R9 Spirited Defence: 4.00/38.34, remainder
  lapsed → money right, label wrong.

Fix: Step 3 may write FINAL_FULL only when matched_size >=
requested_stake (tolerance 1c); otherwise stay PROVISIONAL_PENDING
carrying the true matched/unmatched from the read. Red-before test =
the Richmond shape (partial in orders → must NOT go terminal).
Settlement backstop: on settling an exchange bet whose match_status
was concluded from a pre-jump orders read, re-true matched from
cleared orders first (fields already parsed; S227 Case-A precedent).

## 2. Commission per race-net (code fix)

`workflows/balances/v1/balance_derivation.py` applies commission
per-winning-bet; Betfair charges on per-MARKET NET winnings (zero on
net-loss markets). Divergence only on mixed win/loss markets — one
live instance (Morphettville R3: Betfair charged $0, tool deducted
$6.49 from the winning legs of a net-loss market). All-win multi-leg
markets are arithmetically identical either way (verified on live
data: Belmont R1/R6, Morphettville R5).
Fix: balance derivation groups settled exchange bets by
betfair_market_id, commission on positive market net only. Per-bet
P&L display allocates the market's commission proportionally across
winning legs so lines sum to the market's true net. Red-before test =
Morphettville R3 shape. (Also covers operator's named case: multiple
FB lays same race.)

## 3. Data corrections (operator-present, audited, backup first)

- Richmond `bet-b80c6f9c`: matched_stake 13.47 → true figure from the
  account's cleared-order record (~38.70 @ 13.0; read it, don't
  assume), system-sourced audit event (supersede semantics), NEVER a
  hand verdict — same principle as the void re-true.
- The two lapsed rows: status-only correction FINAL_FULL →
  FINAL_PARTIAL w/ true unmatched restored; money untouched; audited.
- After 1+2+3: derived Tim@Betfair must equal the real balance to the
  cent (allowing the float-dust display rounding, itself on the
  hygiene list).

## 4. Betfair account watchdog (the missing independent check)

Why the operator caught this by hand: recon watches only non-terminal
bets (the bug made the row terminal), and NOTHING compares the tool
against the account — cleared-order profit/bet_outcome are fetched
and discarded by design ("account never sources verdicts"), so the
operator's eye was the only account-level reconcile.
Build: daily (and on-demand) account reconcile — pull the day's
cleared orders (profit per bet/market) + account funds, compare
line-by-line and in total vs derived; mismatches → daily check
section + fault banner. Hands-off rule intact for VERDICTS.

**Cent-truing addition (operator-commissioned S247 eve):** the
residual 3¢ (post-corrections: derived 2,428.99 vs real 2,428.96) is
input-precision — Betfair's ledger works from sub-cent matched sizes
(Gosford really 713.3105→713.31; our 2dp row says 713.30). Emulation
cannot close this; INGESTION does. The watchdog trues it: a per-line
difference ATTRIBUTABLE to a specific settled bet's cleared-order
figure is booked automatically as a system-sourced, audited
book-side balance adjustment ("exchange ledger rounding", named per
line). Anything UNATTRIBUTABLE is flagged for the operator, never
auto-booked — a reconciler that absorbs everything hides real
problems. Guarantee shape: after each daily pass the Betfair balance
either matches to the cent or carries a named flag saying exactly
which line disagrees and by how much. Verdicts untouched. First pass
books the standing 3¢ as its opening act. Edges (accepted): API
unreachable → trues on next successful pass (flagged meanwhile);
cleared-orders retention bounds catch-up after long tool outages.

### S248 review amendments (folded from `s248_build_plan_review.md` — binding)

- **R1 comparison basis.** Cleared-order `profit` is per-line and
  COMMISSION-FREE; our derived side is commission-netted per market.
  Compare lines on GROSS (+S won / −L lost); reconcile commission at
  MARKET level (expected = rate × max(0, market net) —
  `lay_commission_by_bet` already computes it). Naive line compare
  false-flags every winning lay by its commission share.
- **R2 idempotency.** Stored rows stay 2dp forever, so a line's cent
  diff is PERMANENT — every pass re-detects it. Booked adjustments
  carry an idempotency key per bet_id (existing-adjustment check);
  on-demand runs are no-ops on already-booked lines.
- **R3 sign convention.** Balance derivation ADDS book-side adjustment
  amounts (`balance_derivation.py:658`), so correct booking is
  `amount = real − derived` — the standing 3¢ books as **−0.03**.
  CRITICAL: the pnl self-check is neutral to adjustments of either
  sign — a wrong-signed implementation passes silently and DOUBLES the
  gap. Red-before test must assert post-booking derived == real.
- **R4 client prerequisite (build FIRST).** `list_cleared_orders` has
  no settledDateRange / paging, and the translation drops
  `moreAvailable` → an unfiltered daily pull silently truncates.
  Extend the client (date range + paging + more_available surfaced)
  before the watchdog consumes it.
- **R5 funds compare.** Betfair exposure is market-netted; derived
  subtracts each pending liability fully. Compare
  (available + exposure) vs (derived + Σ pending committed), or run
  the funds compare only when flat.
- **R6 (accepted as-is).** Daily cent rows are ledger noise in
  movements; per-line naming keeps them legible.
