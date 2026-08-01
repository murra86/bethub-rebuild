# Session 250 — Wed 22 Jul 2026 (morning, ~09:15 →)

**Opened** 09:15 on the staged `s250_open_brief.md`. **Focus:** 0g
commission cent-rounding (first action) → TAB overnight hunt-storm
diagnosed + fixed capture-side (standing authority) → 0c hygiene →
0d transfer door built → dual-vantage probe armed self-firing.

## Session-open checks

- VPS health: all clear (disk 37%, collector running, capture fresh,
  sweep ran 80 attempted / 25 walled).
- RACING ALERT: only the known Sun 20 Jul Pakenham storm; nothing new
  in ~2 days.
- Watchdog daily pass: correctly named as NOT run — the app hasn't
  been opened today (the trigger rides the settlement worker). Not a
  fault; the no-pass line is the built behaviour working.
- Bankroll check: needs the operator (app closed) — OPEN at close of
  this record.

## What was delivered

1. **0g DONE — per-market commission cent-rounding (`8b41ea3`,
   display rider `7f692c8`).** `lay_commission_by_bet` now quantizes
   each market's commission to the cent HALF-EVEN (the mode that
   matched the S249 live read) and allocates by largest remainder
   (bet_id tie-break): every share is a cent amount and a market's
   shares sum to exactly its rounded figure (S247 item 2 contract
   held). `market_commission_rebate_total` is now signed — a sub-cent
   top-up on fraction-carrying all-win markets. Red-before per shape:
   half-even discriminator (5% of 4.10 = 0.205 → 0.20, half-up would
   say 0.21), naive-per-share undershoot (2 × 0.444 → 0.89 not 0.88),
   mixed fractional factor, net-loss zero guard, singleton rounding,
   all-win end-to-end. Three old byte-identity assertions deliberately
   flipped to the new cent contract. Suite 1729.
   **Offline re-proof: the live store now derives the Betfair row
   2,428.96 EXACTLY (== the S249 real read; was 2,428.9772).**
   Remaining: the live watchdog re-proof fires by itself at next
   app-open — funds gap must read 0.00, banner clear.
   Rider: funds-gap flag totals display at 2dp (was raw Decimal tails).

2. **TAB overnight hunt storm diagnosed + fixed (capture `caffb78`,
   deployed + service restarted in the pre-racing window).** The
   standing-authority sweep found the collector had been cycling
   "every fingerprint worn / breaker OPEN" ALL NIGHT (from ~04:37
   ACST). Diagnosis from the attempt telemetry: the failing races
   (Gavea, Cambridge, Wolverhampton, Assiniboia…) return **HTTP 404 —
   TAB doesn't serve them**; the transport read any non-200 as a
   block, so each such race dropped the working pin, burned a 12-try
   hunt, opened the shared breaker — and the hunt volume itself
   provoked the scattered real 403 rate-limits. **Fingerprints were
   never burned** (hunts re-pinned in 1 try between storms all
   night). Fix: `TabRaceNotFound` (subclass of TabTransportError —
   live route's clean 503 and existing guards unchanged) raised
   straight from a 404: pin kept, no hunt, no breaker, one INFO line,
   `not_found_404s` telemetry counter; orchestrator skips the
   per-book circuit-breaker hit and retries at normal cadence.
   Red-before tests (pinned / no-pin / mid-rehunt shapes); capture
   suite 136. Post-restart: clean pins in 1–2 tries, zero storms, 324
   TAB snapshots captured this morning. Also downgrades the
   fingerprint-burn-list worklist item (real burns are rare).

3. **0c DONE (`22b51de`)** — `/holdings` serves cent-quantized
   `parked_pool` / `total_with_holder`; 2dp asserted by test.

4. **0d BUILT (`0b9b0af`) — bankroll → holder float transfer door.
   IMPLEMENTED-NOT-LIVE: operator walkthrough at next app-open before
   first real use.** New movement kind `transfer` (account_id = the
   RECEIVING holder): one door action books the remittance(bankroll,
   is_self) + funding(target) pair on one correlation (B2 item 4
   precedent; both models validated before either appends). Pair
   reversal rides the existing include_sibling door; the refuse
   message is generalized ("paired action" — it used to claim every
   pair was a bank-sourced deposit). Response carries
   `bankroll_parked_pool` beside the receiver's pool. UI: the
   bankroll row now LEADS with "Transfer to a holder's float"
   (receiver picker, outbound preview, bankroll-side success note);
   its own doors carry the operator-locked S248 wording ("Money in
   from personal bank" / "Money out of the operation"); non-self
   float doors unchanged. Suites 1734/307, tsc + vite green, dist
   rebuilt app-down. **Walkthrough flags: (a) transfer is the new
   DEFAULT door on the bankroll row (was funding); (b) first real
   transfer should be confirmed against the Balances figures.**

5. **Dual-vantage freshness probe ARMED self-firing** (queue item 2).
   A background runner polls the capture DB and fires
   `source_freshness_probe` on Mac + VPS simultaneously at the first
   race jumping in 5–10 min, then copies the VPS jsonl home
   (`probe_output/vps_freshness_…`). Lesson folded in: the first
   arming picked Gavea R7 — a race TAB 404s on (no prices, no
   verdict) — so the runner now requires a TAB bookmaker snapshot in
   the last 30 min (live coverage proof) before arming. Runner:
   scratchpad `dual_vantage_probe_runner.py` (session-scratch, not
   committed; probe script itself is deployed both ends at capture
   `caffb78`). Merge/verdict when it fires: VPS lags Mac ⇒
   residential egress for the live pool (real Decodo case); no lag ⇒
   drop the freshness thread.
   **First firing (Cambridge R1, 09:50): Mac side clean (7 CHANGE
   pairs; beta/site params ticking together again, consistent with
   S249), VPS side CRASHED on import — the VPS system python3 has no
   curl_cffi; the probe must run under the collector's
   `venv/bin/python`. Runner fixed + re-armed.**
   **Second firing (Assiniboia Downs R1, 10:21): both ends ran — and
   the "verdict" came back sharper than staler-edge: the VPS's 140
   direct-egress "200s" were ALL Akamai HTML block pages (empty
   prices), confirmed by a one-shot payload inspection. Datacenter
   egress isn't stale, it is BLOCKED-with-200 — the S249 vantage
   question only makes sense against the PRODUCTION path (Decodo AU
   exit). Probe upgraded (`5eea061`, both remotes): `--decodo` runs
   it through the collector's Decodo sticky session (creds from
   .env, reusing `_decodo_proxy_url`), and every jsonl sample now
   carries a `blocked` flag so a 200 block page can never read as a
   quiet race. Runner re-armed with VPS-side `--decodo`.**
   **Third firing (Gavea R8, 10:41–10:48) = THE VERDICT. Both ends
   real prices (bonus: TAB now serves the race it 404'd overnight —
   live-proves the 404-fix's retry-at-normal-cadence call). Merged
   jsonl, 18 shared price-states: Decodo-vantage first-seen minus
   Mac-home first-seen = mean +0.8s, median +1.3s, range −5.1..+5.7s
   — entirely inside the 6s sampling jitter, VPS AHEAD in 5/18.
   NO systematic vantage lag ⇒ per the S249 decision rule the
   FRESHNESS THREAD IS DROPPED: cadence, params, and now vantage all
   ruled out. No residential-egress build; no Decodo case for the
   live pool; Warren R3 stands as a transient edge anomaly, not a
   systematic lag. Logs: `probe_output/freshness_GEA_R8_101145.jsonl`
   (Mac) + `vps_freshness_GEA_R8_004149.jsonl` (Decodo).**

## Decisions / lessons

- Half-even is built on the S249 aggregate evidence; the distinction
  from half-up is only observable on an exact half-cent market. The
  watchdog re-proof at app-open is the live confirmation either way —
  a residual would surface as an honest funds-gap flag, never hidden.
- HTTP 404 from TAB is CONTENT-ABSENT, never a block — worth a
  standing rule for every bookmaker transport: hunting on a
  can't-succeed response converts one missing race into a nightly
  storm plus real rate-limits (cry-wolf family + fingerprint risk).
- Probe targeting: TAB-side probes must arm only on races with proven
  TAB coverage (snapshot-recency filter), or they measure nothing.

## State at close

- v3 HEAD `0b9b0af` (chain: `8b41ea3` 0g → `7f692c8` rider →
  `22b51de` 0c → `0b9b0af` 0d), pushed; suites 1734/307; dist
  rebuilt (app closed all session).
- Capture HEAD `caffb78`, pushed VPS + GitHub; racing-capture.service
  restarted 09:23 ACST and healthy.
- bethub-rebuild: worklist updated (0g DONE, 0c DONE, 0d BUILT,
  burn-list downgraded); this record.
- Probe runner live in background (6 h window).

## Late-morning live results (operator at the app, ~11:00)

- **0g LIVE RE-PROOF PASSED**: first watchdog pass of the day — 0
  flags, "matches the account". The standing 2¢ banner flag is gone.
- **0d LIVE-TESTED by the operator**: $20 bankroll→Sarie transfer
  (pair booked together, one correlation, "Test" note on both
  halves), then pair-reversed 48 s later — refuse-then-confirm door
  exercised, floats restored to the cent, net zero. 0d is LIVE.
- **Operator request built same sitting (`8c17381`)**: movement-card
  "when" field defaults to the current Adelaide minute (was blank);
  clearing it still books server-side now. Frontend-only — dist
  rebuilds app-down at next launch (app was running; not rebuilt
  live). Suites 306 vitest.

- **Stale-note upgrade built on request (`165d9aa`)**: the S247 Soft
  Odds stale marker now leads with a TICKING elapsed age ("stale 42s
  — as of 11:00:08"; rides the ~1s prices-poll re-render) and, inside
  the live window, a failing live refresh marks the column stale
  IMMEDIATELY (was: only once data aged past 90s). Recovery clears
  it on the next good poll — that's the "reconnected" signal, by
  absence. Red-before both shapes; vitest 308. Operator also briefed
  on the TAB column: ~8s polls in the final 5 min / 15s from T-30m /
  30s background; the TAB website's click-to-reveal quirk is their
  webpage redraw, not the feed — we read the feed directly.

- **Bankroll standing check: PASSED** — operator verified $3,000
  bankroll == UBank; all balances read correct.
- **Per-book promo rail BUILT (`5571597`, operator-commissioned live
  in-session):** arming TAB swaps the generic four insurance
  primaries for TAB's real menu — Ins 2nd/3rd $50 FB · Boost 25% →
  Bonus $50 · Boost 25% → Bonus $100 · Multiplier ×. Other books
  keep the default rail until their menus are defined (add an entry
  to `BOOK_PRIMARY_SHAPES`). Two catalogue rows seeded (idempotent
  one-off `scripts/seed_tab_promos_s250.py`, pre-write backup
  `bethub.db.bak-s250-pre-tabpromos-20260722`): the $50-cap TAB
  bonus-winnings sibling, and "TAB Odds Multiplier" riding the
  existing price_boost kind. NO promo domain / EV / money-path
  changes — both kinds were already first-class (the $100 boost was
  already live in the dropdown). Multiplier contract: revealed
  post-spin → log at the revealed final odds, no pre-spin EV;
  **operator to place one small live multiplier bet to confirm the
  mechanics (odds × multiplier, cash payout).** Red-before tests;
  vitest 310 / backend 1734.

- **TAB drift-since-open + latency decoupling BUILT + VPS-DEPLOYED
  (capture `824b047`, v3 `d640b72`; operator-commissioned via two
  AskUser calls, both recommended options taken):**
  - **Opening prices**: TAB serves `returnWinOpen`/`returnWinOpenDaily`
    on every poll — we were discarding them. Now parsed
    (BookmakerRunner optional fields), passed through the live route +
    vps_client + frontend; the Trend cell shows "4.60→3.60 ▼22%"
    (today's open → current; market-open on tooltip), falling back to
    the 5-min price-memory % where opens are absent. Race-watcher
    inputs deliberately untouched (0h research owns that).
  - **Latency decoupling**: live route now spins a per-market
    background refresher owning the TAB fetch (7s when the UI polls
    fast — the request gap IS the time-to-jump signal — 15s
    otherwise, never faster than the tab.com.au site; idle-stop 45s,
    failure-stop 5, cap 3 markets); requests serve the freshest
    cached copy. UI polls drop 8s→2s (final) / 15s→5s. Display age
    ~8–12s → ~4–5s avg (the ceiling; no TAB push channel exists).
  - **Deploy-order trap handled**: VPS restarted FIRST (operator-OK'd
    mid-day; ~3s blip, collector untouched) so the fast UI polls can
    never hit the old fetch-per-request route. **Live-proven
    end-to-end post-restart**: opens serving (18.00 open → 26.00 on a
    real runner), cache identity on rapid double-request (identical
    captured_at), and a refresher-fetched copy stamped 2.5s BEFORE
    the request that read it. v3 side live at next BetHub launch.
  - Suites: capture 141 / v3 1734 / vitest 312, tsc clean;
    red-before on route fields, cache, refresher, idle-stop, drift
    cell.

- **Soft-odds ownership investigated (worklist 0i, no changes —
  operator's instruction):** any touch (type/stepper/CLEAR) claims
  that runner from the feed permanently (race-switch is the only
  release); per-runner in code — "whole table stopped" = cumulative
  claims + the clear trap + 30s background cadence. Later build
  flagged: clear=hand-back + owned-box marker; auto-release
  rejected as worse-than-disease.

- **CYCLE-3 LEAD-LAG RESEARCH EXECUTED (operator: "begin, thorough,
  incl. web research" — /effort max):** 3 parallel research agents
  (methods / academic / industry — all landed, digests archived) + 
  own-data measurement on the VPS capture DB. **Findings: Betfair
  leads TAB by ~40s–2min** (Hayashi–Yoshida peak +40s; TAB reprices
  cluster 30–120s post-BF-move at ~2× null; TAB desk median
  inter-reprice 61s in final 2min, p10 7s); windows are FAST
  (persistence ≈0 between 2–5min snapshots) and fat when caught
  (arb margins p50 1–17%); favourites/mids are the clean end
  (longshot "value" is engineered margin). **Discovery:
  `returnHistory` = TAB's own ms-stamped complete reprice log per
  runner, same-day retention only, absent from all public
  documentation** — harvested 6 early races (evening re-run armed
  ~17:15, background). Industry triangulation independently matches
  our numbers. Report:
  `bethub-analytical/race-price-pressure/cycle3_tab_leadlag/`.
  Next: G1/G2 capture builds, N3 threshold-follower hazard signal
  → shadow mode; camouflage (jitter, round stakes, spread) is a
  first-class constraint — MBLs protect the win channel, flagging
  costs PROMO eligibility.

- **G1 + G2 BUILT AND LIVE same sitting (capture `da7fa2e`,
  operator-OK'd restart):** G1 = every real live-pool TAB fetch
  persists per-runner rows to side DB `data/tab_live_log.db` (price,
  opens, returnWinTime, percentageChange, differential, full flucs;
  never-raise layer; VERIFIED WRITING — 30 rows in the first 10s on
  the operator's open race). G2 = `scripts/harvest_tab_history.py`
  + systemd timer `tab-history-harvest.timer`, nightly 13:15 UTC
  (22:45 ACST), preserves returnHistory before TAB purges it; first
  run tonight. Suite 152. The proprietary reprice archive compounds
  from today.

- **Krasina rounding fix (operator-flagged, `2d44efa`):** TAB rounds
  bonus-winnings credits UP to the whole dollar, not half-up. The
  S244 rule was calibrated on two exact-HALF cases ($12.50→$13,
  $32.50→$33) where up==half-up, never actually distinguished;
  Krasina (Canterbury R3, $50 @ 1.90 won → $45 winnings → $11.25) is
  the first quarter-case → TAB $12, tool booked $11. Fixed
  ROUND_CEILING in BOTH the credit-in write (`fb_credit`) and the
  door preview (`credit_gap`); red-before test on the Krasina shape,
  S244 halves stay green; suite 1735. The one live credit trued
  $11→$12 via an audited superseding free_bet_credited event
  (append-only, original preserved; backup
  `bethub.db.bak-s250-pre-krasina-fix-20260722`; corrective event
  `70c547e0`); inventory verified $12, daily money check clean.
  Full audit only ran clean because I'd first computed **every**
  bonus-winnings credit ever booked — Krasina was the sole one
  affected. Correction script preserved in bethub-rebuild.
  (En route I mislabelled Krasina's price as 3.40 in a summary —
  operator caught it; the computation was always on 1.90, numbers
  unaffected.)

- **Adversarial review of cycle-3 (operator-commissioned) LANDED**
  (`cycle3_tab_leadlag/research/adversarial_review.md`): verdict
  "partially justified, headline premature". Mechanism sound + capture
  builds blessed; but the ~40s–2min magnitude was "the prior wearing
  the data's clothes" — the event-study null was a simplified strawman
  I mis-described as a rotation null (C1), the direction-agreement was
  null-consistent at n=6 and I'd OMITTED the contrary AFTER-control
  (C2), HY was unnormalized/floor-limited (C3), and exploitability
  rested on 13 uninspected arb events gross of costs (M1). 10-step
  refined plan; process critique (spec→code→report chain broke
  silently; confirmatory tasking; conclusion-grade interim headlines).
  All fair; folded into the report.
- **INTERIM-2 (evening re-run, 35 races, `code/*_full35.jsonl`):**
  more data STRENGTHENED the mechanism and resolved two review points
  — Part C desk-speed now clean/monotonic/well-powered (M2 anomaly
  gone; 34min→14.5→3.9→1.8→1.0min final-2m, p10 8s), and
  direction-agreement FLIPPED to support precedence (BEFORE clears the
  null in all 4 bands AND BEFORE≫AFTER — the C2 asymmetry the review
  demanded, now pro-lead). Still owed exactly as the review said:
  rotation null (C1), before-window=t0 re-check (C2a — flagged the
  single highest-value next fix), HY normalization (C3), cost/
  strikeability on arbs (M1). Conclusions remain gated; no
  self-certified re-implementation done unattended (would repeat the
  review's process critique).

- **G3 DONE — 4× finer near-jump Betfair capture (`e0e39a1`,
  operator-commissioned "proceed, check Betfair limits, don't
  break").** `INTENSIVE_POLL_INTERVAL` 60→15s (Betfair intensive,
  final 5 min) + `MAIN_LOOP_TICK` 30→5s (the 30s tick would have
  aliased a 15s interval back to 30s — caught before deploy).
  Betfair-ONLY: `_get_bookie_interval` keeps 105s, so the hardened
  TAB/Decodo path is untouched (verified). **Throttle-checked
  against Betfair docs: 5 listMarketBook/sec PER market is the limit;
  15s = 0.067/sec = ~1.3% of it, 50–75× headroom.** Suite 144;
  interval split asserted. Deployed to VPS; the restart hit the
  DESIGNED stop-hour clean exit (9:45pm Adelaide, no active races,
  status=0 — NOT a break) → `racing-collector-start.timer` starts it
  08:30 Adelaide tomorrow with the new config. Live 15s cadence
  unverifiable tonight (no races); verify tomorrow via capture-DB
  snapshot gaps in a final-5-min race.
  **Honest scope correction (told operator):** this is an ANALYTICAL
  win (sharpens the lead-lag resolution floor) — the LIVE betting
  view is unaffected because v3's `/prices` polls Betfair DIRECTLY at
  1s for the open race (`get_live_market_prices`, not via the
  collector). Operational benefit is downstream (better signal
  calibration), not a live-view speedup. Lesson: evening capture-
  config deploys need NO manual restart — the 08:30 timer picks up
  on-disk config; a manual restart past stop-hour just clean-exits.
  Follow-up option: widen the fine-Betfair window past T-5m (needs
  decoupling Betfair/bookie INTENSIVE_WINDOW — deferred, touches the
  shared phase logic) and/or tighten 15s→10s once it's run clean.

- **CYCLE-3 AUTONOMOUS MAX-EFFORT RUN (23 Jul, operator away, "lead
  this, use as many resources as needed, be honest"):** 4 research/
  adversarial agents + own money-sensitive data analysis on 154
  races. **Conclusion: the "front-run TAB" edge is NOT there in the
  data.** Two adversarial rounds progressively deflated it: corrected
  stats (proper rotation null, before-window=t0, normalized HY) then
  an independent check of THOSE showed no reliable lead (HY coin-flip,
  favourite tier leans against; the "weak" B1/B2 signals are
  co-concentration + within-runner-trend artifacts). A2: 0/3294 arbs
  survive commission. A3 base-rate-controlled: Betfair leads TAB 3.9×
  (real but weak); corporates lead more = shared-feed confirmation,
  not front-run. Strikeability research: adverse (locks at acceptance;
  MBL=latest-displayed not stale; sized bets referred 30-60s; repeated
  use flags accounts). Architecture research: human window generous IF
  strikeable, CLV/flumine eval. **Deliverable
  `cycle3_tab_leadlag/SUMMARY_FOR_OPERATOR.md`** (plan / feasibility /
  success=LOW / gated plan: Gate0 operator strikeability probe = the
  dealbreaker; Gate1 self-running CLV logger; Gate2 re-run on the new
  15s data; build only if it surprises positive — honest prior
  KILLS). All preserved in `code/`+`research/`. Health monitor left
  running (task, persistent). Value = stopped a build on a
  non-existent edge, honestly and rigorously.

## Forward routing (S251 / rest of today)

1. **Operator:** when-default + stale-note + TAB rail all go live at
   next BetHub launch (catalogue rows visible immediately).
2. **Multiplier mechanics test**: one small TAB multiplier bet — log
   at revealed final odds; confirm cash-at-final-odds and any stake
   cap; refine the template description after.
3. **Call/Trend + TAB-latency research commissioned (worklist 0h,
   brief `call_trend_tab_latency_research_brief.md`)** — operator
   flagged noisy Trend and confusing Calls off live screenshots;
   both traced (sp_near artifact / designed-but-opaque LEAVE / raw
   price-% trend). First sitting: grade backtest on logged
   grade_at_log + edge-TTL header probe. No engine changes made.
2. **Probe verdict LANDED in-session (Gavea R8): NO vantage lag —
   freshness thread DROPPED.** Nothing to build; T1 gate keeps its
   current transport evidence. If a Warren-R3-shape lag is ever
   OBSERVED live again, re-run the (now Decodo-capable) probe on that
   race in the moment — the tooling is deployed both ends.
3. Day-2 transport telemetry re-read tonight: expect `not_found_404s`
   counting, zero hunt storms overnight.
4. Standing queue: 0f (commissioned, conservatism rider) · 0e ·
   take-SP Stage 0 on next race day · next race day remains the big
   full-stack live-proof sitting.
