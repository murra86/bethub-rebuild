# SESSION 255 — 26 Jul (eve) → 28 Jul 2026

**Scope:** morning odds sweep (0k) build → daily operation; Monday deploy
window (panel review + commit + 6 queued fixes). Continuous-oversight
format: operator held a monitoring session open; hourly sweep-check loop
ran through Monday's card.

**Close:** S255 CLOSED 28 Jul. **S256 first action = 0j build** (other-code
bet row + goodwill/deposit credit rider — operator-directed at close).

## 1. Open (26 Jul eve)

- VPS health: all clear. RACING ALERT (25 Jul, Murtoa R1 no Betfair
  identity): self-resolved — Betfair listed the country meeting late;
  matched T−57m, 42 snapshots to jump, all 8 races SETTLED. No fix.
- Queue review delivered as exec summary; operator picked 0k first.

## 2. Morning odds sweep (0k) — BUILT, DAILY, NOT YET LIVE-PROVEN

Capture repo `8645e08`+`054c2e5`+`6dfa987`+`7ad7425`+`93b171e`, deployed
(push-to-origin `updateInstead`) + GitHub. Full record:
`morning_odds_sweep_report.md`. Headlines:

- `scripts/morning_sweep.py` + `racing-morning-sweep.{service,timer}` —
  hourly 06:00–17:00 Adelaide, **DAILY** (operator widened from
  Saturdays-only v1; wants regional/low-activity trends too). >T−75m
  only (re-checked per request), `snapshot_phase='MORNING'`, TAB on own
  `morning` pool, overround guard, no batch-summary writes, verified
  fill-if-null book-id stamping behind a runner-name identity guard.
- Adversarial review → 5 real bugs fixed pre-live: **writer-lock held
  across network waits** (the shared batch savers commit BEFORE their
  coverage UPDATEs — any new writer process must commit after calling
  them); JSON day-cache stringified race-number keys (retry-next-hour
  was dead from hour 2); S252 twin rows double-fetched (targets deduped
  by market id); TABtouch discovery carries dogs/harness links →
  identity guard; TAB 404 pacing/streak-reset. Plus: liveness freshness
  now EXCLUDES MORNING rows (sweep can't mask a wedged collector).
- First live morning (Mon 27): timer fired on schedule; oversight caught
  2 more real bugs, fixed + verified live by ~09:15 — (1) shared client
  `get_market_books_batch` split at 40 markets but its projection costs
  20 pts/market vs the 200-pt cap → every >10-market batch failed whole
  ("rate limit"); 10/request now (`7ad7425`). (2) Six books list
  synthetic-day meetings as "<venue> Synthetic" vs Betfair's plain name
  → surface-suffix aliases (`93b171e`); identity guard verified the
  aliased cards before stamping. **Side-lead for the data reset:** the
  synthetic-suffix class is a plausible S252 twin-row GENERATOR.
- Monday's later runs + Tuesday 06:00 run clean (8/8 books, 0 identity
  mismatches; neds Decodo-522 blip handled by the drop valve, recovered
  next hour). 186 capture tests green.
- **OPEN: §4 acceptance on Sat 1 Aug** (fold into race-day sitting) —
  per-source ≥90% pre-window coverage, TAB no-hunt-storm, collector
  non-interference, per-book publish-time table. Only then live-proven.

## 3. Monday window — PANEL SHIPPED (v3 `5c4b44e` on main, pushed)

Operator live-review with browser assist: bundle-hash, console, no-bets
invite, vacant-trap (Warrnambool R1: 7 active with box 5 empty), field
count (Ballarat R7: 12 active — verified independently against capture
DB: 17 declared / 5 TAB-scratched), free-bet visibility (liability shown)
all PASSED. Settled-race + no-promo card behaviours explained (see
decisions). **Promo-dependent checks PARKED for Sat 1 Aug:** $-at-risk
matches stake; additivity (panel EV rises by exactly the card's ΔEV);
steadies/concentrates wording.

Commits (branch `s253-race-panel`, merged `5c4b44e`):
- `613c68c` panel + confirm-card marginal, operator decisions baked in.
- `56f6d20` odds-table field filter === ACTIVE (three surfaces agree).
- `64bf938` operator-review UI fixes: stake input contained; activity
  board moved INTO the scrolling flow under the race box (was pinned
  below the viewport); settled races — poll stops on CLOSED, 30s backoff
  on stale-error, quiet grey "live prices have ended" note.
- `2a03a10` the six queued fixes: ONE guarded PromoSpec builder
  (`ev/promoSpec.ts`) for ALL EV surfaces incl. stamped promo_ev_at_log
  (bonus_pct NaN-guarded); over-cap stake called out in words (engine's
  capped-EV identity untouched — deliberate deviation from the queue
  line, reasoning in commit); scratched-runner bets report "normally
  voided and refunded" (they previously VANISHED inside the engine —
  worse than the reviewed mislabel); market_base_rate threaded to
  free-bet EV (was 8% default); shared RaceMarginalRead. 428 tests.
- Operator post-restart: "Looks good."

## 4. Operator decisions this session (standing — do not re-raise)

1. **`position_min_field` DROPPED tool-wide.** "Disregard from the tool
   — I'll monitor small fields myself. Maybe later, absolutely not a
   priority." Pinned null in the shared builder + test. The standing
   "enter terms on 12 templates" operator action is REMOVED.
2. Panel **"at risk" = pending bets only**.
3. **No-promo bets show no marginal line** on the confirm card — by
   design (outside the promo portfolio).
4. **Sweep daily**, not Saturdays-only.

## 5. Close: S256 queue

1. **0j build — FIRST ACTION** (operator-directed at close): other-code
   bet row + goodwill/deposit credit rider, spec in `worklist.md` 0j.
   Note: outside the formal Sun/Mon window — off the racing money path,
   deploy with operator present.
2. Quiet sitting: Saturday feedback batch + settled-bet stake-edit
   button.
3. **Sat 1 Aug sitting:** race-day live proofs + first live reassign +
   Take-SP stage 0 + sweep §4 acceptance + the 3 parked panel checks.
4. Operator anytime: BetRight ≥8 template (day next used); confirm
   Punting Form cancelled.
5. Small: 1-cent Betfair recon banner on Tim (likely rounding — 2 min in
   the next money-check sitting, not dismissed unexamined).
6. Parked list unchanged (+ new lead: synthetic-suffix as twin-row
   generator — for the data-reset thread).
