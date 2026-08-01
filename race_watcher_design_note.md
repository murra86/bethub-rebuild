# Race Watcher — Design Note (S241, 16 Jul 2026) — for operator walkthrough

> **v2 amendments (16 Jul eve, from the deep-research run —
> `race_watcher_research_report.md`, 25/25 claims verified):**
> 1. **Trust CAPS the grade** (operator requirement, now research-backed): below a
>    per-code matched-volume floor the exchange loses its informational advantage
>    entirely (Economica 2006) — an unformed market structurally cannot emit STRONG,
>    whatever the EV maths says. Gate = volume floor × structure (spread, overround,
>    % runners traded, |near−far| gap) × time-to-jump ramp, collapsed into ONE liquidity
>    factor before calibration (correlated-signal overconfidence, AAAI 2015).
> 2. **CERTAIN tier dropped** — top grade is STRONG (residual bias survives even in the
>    best prices; longshot bias worst exactly where insurance promos live).
> 3. **Close projection ≠ nearPrice alone**: nearPrice is ~60s-cached and beaten by live
>    best back as a BSP estimator near the off (Betfair's own study) → late-window
>    projection uses the live book, nearPrice demoted to cross-check + staleness flag.
>    Affects the existing BF Close column as well.
> 4. **Movement signals (trend/WOM) may adjust projected EV but NEVER raise the tier**
>    (the one rigorous order-flow study sits at the significance borderline).
> 5. **Calibration recipe pinned**: per code × time-bucket, isotonic ≥1,000
>    samples/bucket (Platt below, BBQ as third candidate), target = BSP-settled
>    outcomes, evaluated logloss + ECE/MCE(K=10), acceptance = per-tier MCE bound.
>    Four open empirical questions in the report = the analytical-line backtest spec.

Operator intent (16 Jul, verbatim shape): on individual race screens, active only while
the race is open, crunch typed soft-book odds × Betfair data × the armed promo into
conditional recommendations — **weak / moderate / strong / certain** — on whether to take
the bet. Anchor example: 2nd/3rd $50 bonus insurance armed; runner shows +2.3% promo EV
(below the execute bar) but Betfair indicators say the runner will shorten → the soft
price is actually rich vs jump-time truth → the tool should say so.

Strategy context (operator-stated): insurance bets are NEVER layed. Targeting = positive
promo EV + expected shortening, to maximise unlayed EV at jump time.

## 1. Core engine — "EV at jump", not just "EV now"

Per runner with typed soft odds:
- **EV_now**: exactly today's promo EV column (unchanged).
- **Projected close**: BF Close (sp_near), admitted only through a TRUST GATE built from
  the 16 Jul live lessons:
  - **Pool coherence**: Σ(1/sp_near) across active runners near 100% → trust; far off →
    distrust (observed live: Pinjarra back-heavy ≈107% → all-▼ artifact; Kilmore
    lay-heavy ≈88% → all-▲ artifact).
  - **Market formation**: overround band (~≤106%), spread tightness, share of runners
    with matched volume (Albion Park R10: 6/10 runners $0 matched, 115% overround,
    sp_near merely echoing the back price → no independent information).
  - **Time-to-jump ramp**: weight rises inside ~15 min (thin harness: later).
  - **Trend agreement**: price-memory trend (matched money) agreeing with close direction
    → boost; contradiction → prefer trend, flag the conflict (Rays Redemption: fresh
    steam vs stale lay-heavy pool).
- **EV_projected**: rerun the SAME promo EV maths substituting the projected close for
  current Betfair prices, soft price held fixed (the operator's position locks the soft
  price; the moving part is market truth). Reuses evEngine verbatim — no new maths.

## 2. Grading

| Grade | Condition (first cut — tune from logged outcomes) |
|---|---|
| CERTAIN | EV_now ≥ bar AND EV_projected ≥ bar AND high confidence (coherent pool, formed market, ≤15m, trend agrees) |
| STRONG | EV_projected comfortably ≥ bar at decent confidence (the +2.3%→+9% case), OR EV_now ≥ bar and holding/firming |
| MODERATE | EV_projected ≥ bar at LOW confidence (thin/early/conflicted), OR EV_now marginal + firming |
| WEAK | Marginal on every read |
| (no grade) | Drifting / projected below bar / no soft odds typed |

Every grade renders WITH its reasons, compact: `+2.3% now → ~+8.5% @ 2.70 proj · pool
coherent · trend agrees · 8m`. The execute bar and band edges are operator-tunable
constants; **grade-at-log is stamped alongside EV-at-log** so bands are calibrated from
realized results after a few weeks (analytics-line follow-up).

## 3. Throttle / activity model

- **Phase 1 costs ZERO extra Betfair calls**: the race page already polls prices for the
  open market only; the grader is client-side arithmetic on data already fetched.
  "Active only on the race screen" holds automatically.
- **Phase 2 watchlist**: races with an armed promo + typed soft odds get background
  grading at ~30s cadence inside T-20min only; a banner (fault-banner surface) surfaces
  grade transitions ("Kilmore R3 #5 → STRONG, 6m out"). Bounded: promo-armed races only,
  auto-expires at jump.

## 4. Phasing

1. **Phase 1 — grade chip + EV_projected on the race screen.** Display-only, fenced,
   client-side. Test fixtures = the four 16 Jul live case studies (Pinjarra all-▼,
   Kilmore all-▲, Albion R10 unformed-book echo, Rays Redemption trend-vs-pool
   conflict). Candidate: Fri 17 pm post-reset if clean; else with Monday's builds.
2. **Phase 2 — watchlist + banner.**
3. **Phase 3 — TAB auto soft odds** (separate build, Mon 20 Jul,
   `tab_api_scoping_brief.md`): TAB races grade hands-free.
4. **Phase 4 — Claude watcher layer** (paid service, operator sign-off): cross-race
   triage + plain-language narration on top of the deterministic grades. ADVISORY-ONLY
   hard fence.

## 5. Fences + governance

Display-only throughout: no placement, no logging, no settlement, no money-path files.
The grade is decoration on existing reads. Normal process: this note → operator
walkthrough (bands, bar, banner behaviour, chip placement) → fenced build brief.

## 6. Open questions for the walkthrough

1. The execute bar: one global promo-EV threshold, or per-promo-shape?
2. Banner interruption level: passive strip vs toast vs (later) phone push via W1 email?
3. Should CERTAIN exist at all, or is STRONG the top (avoiding overconfidence)?
4. Grade visibility for negative-EV runners: hide entirely vs show "avoid" reasons?
5. Watchlist cadence + window (30s / T-20m proposed).

## 7. Walkthrough outcomes (S245, 20 Jul 2026 — operator-locked)

Locked via an illustrated mock (`race_watcher_execute_bar_mock.html` —
take 2, the row-level version = the approved visual reference).

**Phase 1 — active-race grade, fully specified:**
- **Q1 execute bar → ONE GLOBAL dial.** Not per-promo-shape (simpler to
  tune, calibrates faster on pooled results). The bar is invisible on
  screen; it only sets where a Call flips.
- **Presentation: ONE new "Call" column** folded into the existing
  OddsTable row — no other column moves (operator: the current screen is
  right; the watcher rides data already on the row). Grade pills
  STRONG / MOD / LEAVE; **reasons on hover/tap**, not on the row.
- **Q3 grade ceiling → STRONG, no CERTAIN** (research-backed; residual
  bias survives even the sharpest prices).
- **Q4 non-play visibility → faint dot for dead runners, explicit LEAVE
  only for tempting-but-trap runners** (positive-looking yet drifting
  under the bar, e.g. the Coldstream case).
- **Grade-at-log stamping confirmed** as the calibration substrate; the
  capture store already banks the raw ingredients (pending-money
  imbalance, BSP/sp_near moves, odds drift/steam, time-to-jump). Honing
  the Calls is the analytical-line backtest (§6 report's four open
  questions).
- **Promo source (Phase 1) = the top-bar armed promo** — so the Call and
  the existing Promo EV column always agree; zero new input.

**Deferred to the cross-card watcher (Phase 2) design:**
- **Q2 banner** and **Q5 cadence/window** — both are watchlist concerns.
- **Promo-assignment model** — pre-assigned per-race promos + standing/
  floating promos usable on any race. Unlocks hands-free multi-race
  grading and the "watcher finds the single best race to spend your one
  daily floating promo on" capability (operator-flagged as high value).

Rapid Vision mechanism clarified for the record: shortening = weight of
money coming to **back** it (lay-side weight is what drifts a price);
STRONG = positive EV now + fixed soft price turning rich as the true
price shortens + a trustworthy market confirming it.
