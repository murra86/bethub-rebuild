# Bet-day feedback → workplan (S242 Sat 18 Jul + S243 Sun 19 Jul)

Every operator observation from the weekend, its status, and the plan.
Written S243 close. Sources: `bet_day_notes_s242.md` (items 1–12),
`money_read_truncation_review_report.md`, `fb_cross_account_fix_report.md`.

## 1. What you flagged, and where each item stands

| # | Observation (bet-day terms) | Status |
|---|---|---|
| 1 | Free-bet auto-select misbehaved when switching accounts | **FIXED + live-proven** (S243) — selection clears and re-derives on every switch; back end now refuses cross-account draws outright |
| 2 | BetLog rows: want P&L on the row + a gift icon on insurance-triggered bets | **To build** → UI pass #3 |
| 3 | Matched/unmatched status and settlement slow to update | **FIXED** (60s sweep, live at next restart); frontend refresh-cadence check remains → UI pass #3 |
| 4 | Scratched runner voided the FB — did it return to the pool? | **TRUE at the book, and now true in the tool** — restore door built; automatic void-return queued (build B2) |
| 5 | Race-page bottom bar shows "$0.00 @ $0.00" on unmatched lays | **To build** → UI pass #3 (show order price + requested stake) |
| 6 | Total-matched money stale in the race list, absent on the race page | **To build** → UI pass #3 (payload already carries it live) |
| 7 | Sarie's bonus-winnings FB never credited; 23 credit-gaps undismissed | **To triage** → sitting D |
| 8 | Sunday P&L looked $27.52 off | **RESOLVED — data clean to the cent**; the 50-row read trap spawned the honest-money-reads brief (build B1) |
| 9 | (Sun) BetRight showed an FB the real account didn't have | **RESOLVED** — revoked; root: BetRight excludes 3rd at ≤7 runners (confirmed, now a standing lesson) |
| 10 | Can't void/delete a bet in any state (BetRight phantom) | **To build** → B2 (audit-trailed void door) |

## 2. The workplan

### A. Monday (already committed — unchanged from S241 flags)
1. **TAB API build** per `tab_api_scoping_brief.md` (A1 Decodo spike first).
2. **Race watcher walkthrough** (design note §6 questions) → commission
   the Tier-1 build.

### B. Money-integrity builds (next build slots after A)

**B1 — "Honest money reads"** (truncation review report §4; one brief):
- The one with a fuse: **free-bet credit guard reads only the oldest
  1000 promo events** — after ~a season of Saturdays it stops preventing
  double-credits and re-lists paid bets as owed. Fix before data
  accumulates. (HIGH)
- Money-event list methods lose their silent default caps (root class).
- Ad-hoc bets-API reads: fetch-all form + standing len-vs-total rule.
- Balances movements fold-out: "showing latest 30 of N" or fetch-all.
- Post-settlement void detector: fix its 100-row cap BEFORE wiring.
- Sweep-slot hardening: terminal manual resolution clears match_status.

**B2 — "Promo + settlement doors"** (one brief):
- **Auto-restore-on-void**: settlement writes the corrective credit when
  it voids an FB bet (manual door covers it today; item 4's class).
- **Void/delete-bet door** (item 10): audit-trailed, any state, with
  re-classing (the BetRight phantom's "settled_won @ $0" row).
- **Small-field insurance honesty** (item 9 follow-on): catalogue can't
  express "no 3rd place under 8 runners" — decide catalogue extension
  vs picker warning at ≤7-runner fields for BetRight-variant promos.

### C. UI pass #3 — race-day display (mock-first per UX standing)
One brief, one build, per the S235 pattern:
- BetLog row: P&L impact on the collapsed row + gift icon on
  insurance-triggered bets (derive from the promo spine, DR-019). (item 2)
- Bottom bar: unmatched lay shows "unmatched $X @ price" from
  requested_stake + order price, never $0.00@$0.00. (item 5)
- Race page: CURRENT total-matched (and Δ since open) from the prices
  payload; fix/retire the stale left-bar figure. (item 6)
- Frontend status-refresh cadence review + the parked "amber unmatched
  recheck" item — now that the worker sweeps at 60s, make sure the
  screens keep up. (item 3 residual)
- Live walkthrough of the new FB auto-select-on-switch behaviour. (item 1)

### D. Triage sitting (read-only first, ~30 min)
- Sarie bonus-winnings FB (Roselyns Star, WON +$50, no credit): why the
  gap detector missed it (bonus-winnings variant vs settled-lost gate?),
  cross-check TAB's app before crediting. (item 7)
- Credit-gaps sweep: recount post-S243, dismiss the stale, keep the real.

### E. Operator actions (open)
- Log the $400 BetRight deposit's second hop (account_holder_funding via
  the movements door) — Sarie's $300 had both hops, this one only one.
- **New Saturday habit: check field size before BetRight safety-net
  bets** (≤7 runners = no 3rd-place protection; scratchings can shrink a
  field after placement).
- Restart the app when convenient — activates the 60s match-status sweep
  and the credit-revocation endpoint (data already corrected).

### F. Still parked (unchanged priority, good fits kept visible)
Results-retention build (weekend queue item) · take-SP brief v2
sign-off (Aged Care give-back case now quantified) · theme revision
verdict · spray-cost analysis · calendar diff / picker latency / W6
fault banner (deferred trio).

## 3. Suggested order

Mon = A (as committed). Then B1 (the fuse) → C (one UI brief while B1's
findings are fresh) → D triage in any spare sitting → B2. E items are
independent and immediate. F stays parked until A–C clear.
