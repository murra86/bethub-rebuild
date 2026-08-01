# Session 251 — Thu 23 Jul 2026

## Headline
Cycle-4 redirected to an own SP/finish-order model; entire data
foundation acquired, validated and joined in one day; SP baseline v0
beats the carry-the-price null 37%→13% median error out-of-time.

## 1. Opening (operator-set first action)
- Cycle-4 cloud judgement retrieved (Drive doc `CYCLE4_JUDGEMENT`) and
  delivered executive-level. Verdict: market-signals-only ≈10–15%
  edge odds; blend-with-ratings + exchange execution ≈25–35%;
  recommended kill test. My add: the agent's "third option" (tote
  place priced off exchange win) is Strategy 4, already at cycle-1 GO.
- Operator REDIRECTED the programme: build our own expected-SP +
  finishing-order model from historical + incoming data. Bar set
  later in session: promo-grade confidence first, market edge later.
- Standing checks after review: VPS all clear; RACING ALERTs 22 Jul =
  Pinjarra no-Betfair-identity (known category, self-cleared).

## 2. Research (3 parallel agents, notes in
`bethub-analytical/race-price-pressure/cycle4_predictive_signals/research/`)
- Data sources: free Betfair BSP files + Automation Hub archives;
  Punting Form = paid keystone; our capture DB unique (TAB/corporate
  time series).
- Public inputs: sectionals #1 post-price predictor; PF the licensed
  path; Racing Australia scraping ToU-banned.
- Literature: Benter two-stage blend; rank the race; benchmark =
  de-vigged market log-loss out-of-time; halve backtests.
- Synthesis: `research/SUMMARY_FOR_OPERATOR.md`.

## 3. Data acquisition (all validated — `data/VALIDATION.md`)
- Punting Form Pro subscribed (operator); API key stored
  `~/.config/puntingform/apikey`. $59 tier = form/results/ratings/
  speedmaps (live + ~1-month rolling window); sectionals/benchmarks
  403 (Professional/Modeller). Window backfilled same day: 34 days,
  1,041 files. Modeller quote requested (sales@), awaited.
- Betfair Data Portal access granted (whitelisted, operator's login):
  pulled 243 CSVs via Chrome session — Aus thoroughbred 2006→2026
  (BSP+preplay by market id), AU runner metadata 2022-11→, race info
  2022-08→, API snapshots 2025-09→ (official rating, forecast price).
  PRO stream TARs 2016→ (~100 GB) deferred/selective.
- Free Automation Hub: ANZ thoroughbred 2020→ + Kash + Top5 models.
- Daily BSP CSVs Oct 2012→ (8,766 files; AU coverage starts Oct 2012,
  NOT 2008 — notes corrected).

## 4. Join layer (`data/build_join_layer.py` → `model.db`, 1.56 GB)
3.26M runner rows 2006→Jun 2026. Four build iterations; quirks
absorbed and documented: 3 date formats; old Place files column-
shifted BY TWO; 2024 selection ids exported as floats (silently
killed a year of ID joins); W/L vs WINNER/LOSER. Final rates healthy
(place 86–98%, daily 86–89%, meta 100% in-era). PF joined via
persisted venue map (`pf_track_map`, Fannie Bay=Darwin etc.) —
93–100% on days with data.

## 5. SP baseline v0 (`data/sp_baseline.py`)
Predict BSP from morning state; train ≤2023, test 2024→Jun 2026
(353k rows): carry 37.4% median |%err| → linear shrink 17.1% → GBM
13.4%, robust across bands. Caveats: weak null (thin morning
markets); real fight = vs sp_near on capture data at decision times;
minor field-size leak to clean at capture join.

## 6. Allbets conditioning thread (side)
- New book Allbets (Tim): $200 deposit; $20 Cairns R9 in-tool; $40
  AFL Crows @1.38 NOT in-tool (no sports path — verified racing-only,
  bets.py); $100 deposit FB (winnings-only, expires 22 Aug 23:30).
- Tool gaps surfaced: no non-racing bet row; credits require a
  promo-carrying settled bet (BetLog.tsx:548) — no account-anchored
  credit.
- COMMISSIONED worklist 0j (Sun/Mon): other-code bet row + rider
  goodwill/deposit credit door (account-at-book anchored). Interim
  truth: `bethub-rebuild/conditioning_bets_log.md`; known $40 gap on
  Allbets until built (tool $180 vs real $140).

## 7. Standing schedule
- Fri: operator app restart + sanity pass (fault banner, watchdog,
  bankroll==UBank); TAB promo template terms as used.
- Sat: race day — NO deploys; optional Take-SP Stage 0 + multiplier
  probe.
- Sun/Mon deploy block: PF capture → VPS (+ near-jump second
  snapshot); capture-client SP-ladder/EX_TRADED/reductionFactor
  extension; 0j + credit door.
- Next work session: capture-DB extract (read-only) → sp_near
  benchmark at decision times; place-probability calibration.

## Awaiting externally
Punting Form Modeller quote (historical sectionals decision).
