# Session 249 — Tue 21 Jul 2026 (evening, ~20:12 → ~22:45)

**Opened** 20:12 (same evening as S248's close). **Focus:** AUTO
watchdog wiring → supervised first pass → two live catches fixed →
standing 3¢ fully decomposed → TAB source-freshness discovery +
head-to-head #1. **Closed:** yes, all repos pushed.

## Session-open checks

- VPS health: all clear (disk 37%, sweep ran 79 attempted / 25 walled).
- RACING ALERT: only the known Sun 20 Jul Pakenham storm (fixed S247);
  nothing new in 38+ h.
- **Bankroll standing check: PASSED** — UBank app $3,000.00 exactly ==
  Bankroll row (operator-confirmed at close).

## What was delivered

1. **Account watchdog WIRED THROUGH THE LIVE APP (`86594a8`)** — the
   S248 core now has its three surfaces, all riding the app's one
   composed Betfair client: daily trigger in the settlement worker
   (once per Adelaide date, first cycle of the day; skip-without-
   consuming when no client), on-demand
   `POST /api/v1/cash-flow/account-watchdog` (`?dry_run=true` fully
   read-only), fault banner via the money-health block, plus a
   dedicated BETFAIR ACCOUNT WATCHDOG section in the daily money check
   that says out loud when NO pass ran. Red-before proven on every
   surface. Suites 1721/303 at commit.
2. **Live catch #1 — funds read never worked (`22a2e94`).** First
   supervised pass flagged funds unavailable: `/v1/account/funds` had
   NO translation route and getAccountFunds lives on Betfair's
   SEPARATE account JSON-RPC endpoint. Transport now routes by method
   prefix (URL overridable via BETHUB_BETFAIR_ACCOUNT_JSONRPC_URL).
   Also silently repairs the bet-entry fundedness pre-flight, which
   had soft-warned "unchecked" since cutover. Suite 1724.
3. **Standing 3¢ FULLY DECOMPOSED (supervised pass + day sweeps
   18–20 Jul):**
   - **1¢ = the Gosford line** (account −713.31 vs derived −713.30,
     the input-precision case): auto-booked as the audited
     "exchange ledger rounding" event, R2-idempotent (re-sweeps
     proved no double-book).
   - **2¢ = commission rounding**, proven read-only: Betfair rounds
     each market's commission to the cent, ours keeps fractions
     (71.1728 vs 71.19 over 21 markets = −0.0172 ≈ the gap). NOT
     fixed tonight (operator conservatism rule; core-derivation
     change) → **worklist 0g, first in the S250 queue.** Until then
     the tool's Betfair row reads 2¢ high and the banner honestly
     carries one flag — known and accepted by the operator.
   - Daily trigger observed firing BY ITSELF at 20:42:39 (first
     worker cycle after restart) — the wiring works unattended.
4. **TAB source-freshness (transport brief item 5) — discovery DONE +
   head-to-head #1 RUN (capture `a2f4e50`, deployed VPS+GitHub):**
   via the operator's real Chrome (extension connected this session),
   the site's race page polls the SAME api.beta tab-info-service race
   endpoint as the collector, ~7s, differing only in params
   (jurisdiction=SA + returnPromo/returnOffers). No hidden host, no
   push channel ("shards.beta" = JS bundles). Probe script built +
   run live on VCY R2: feed-params vs site-params tick TOGETHER →
   **only remaining suspect for the Warren R3 lag = VPS vantage
   (Akamai serving the datacenter IP staler edge objects). Next:
   simultaneous Mac+VPS probe on one near-jump race — if VPS lags,
   the fix is residential egress for the live pool (the real Decodo
   case), not cadence.**
5. **Operator commission — worklist 0f:** account-at-book hide/soft-
   archive on Balances (all data retained, warning-not-block on
   discrepancies, un-hide path) + permissive bet entry (no-balance /
   hidden / missing pairing bets go straight through, auto-flagged to
   Burst review). Standing principle saved to memory: **remove
   friction at action time; safeguards monitor and correct later,
   never block** — plus the conservatism rider (S249): incomplete-
   but-safe beats complete-but-risky; additive only.
6. **Launcher opens BetHub in Chrome (`20f5611`)** — operator call;
   system default browser untouched, fallback if Chrome missing.
7. **Queue glances:** TAB transport day-1 telemetry — rotation fired
   twice (safari17_2_ios re-burned → safari15_5), zero frozen-book
   alarms; NOTE: burn list not persisted across collector restarts
   (each restart re-tries the burned fp once — harmless, listed).
   `racing-health-check.service` "failed" = cosmetic (email sends
   fine, script exits 1 after) — listed, no urgency.

## Decisions / lessons

- 2¢ commission fix deferred to a fresh sitting (operator rule stated
  mid-session: review enough to be sure nothing breaks; prefer
  incomplete-but-safe). It needs per-market share re-allocation so
  lines still sum — not a one-line rounding call.
- The watchdog's day window keys on SETTLED date — old diffs need a
  `?day=` sweep (18–20 Jul swept tonight; idempotent, safe).
- Chrome extension needed operator-side connect (sign-in) before
  list_connected_browsers saw it; once connected, discovery took
  minutes and burned zero fingerprints.
- Betfair streaming briefly hit SUBSCRIPTION_LIMIT_EXCEEDED during
  the restart overlap (old+new app) — recovered itself; expected
  shape, not a fault.

## State at close

- v3 HEAD `20f5611` (chain: `86594a8` watchdog wiring → `22a2e94`
  funds routing → `20f5611` launcher), pushed; suites 1724 / 303.
- Capture HEAD `a2f4e50`, pushed VPS + GitHub; no service restarts
  needed (probe is a standalone script).
- Money: Betfair derived 2,428.9772 vs real 2,428.96 (the known 2¢,
  banner-flagged); bankroll $3,000.00 == bank app (PASSED); watchdog
  ledger event booked −0.01 vs bet-69054a3f (audited).
- App left RUNNING in Chrome (operator's evening session).

## Forward routing (S250)

1. **Worklist 0g first: commission per-market cent-rounding** — after
   it, Betfair row must read 2,428.96 exactly, watchdog funds gap
   0.00, banner clear.
2. **Dual-vantage probe** on a near-jump race (Mac + VPS same race,
   same minutes; merge jsonl by timestamp) → decides
   residential-egress vs nothing.
3. Read day-2 transport telemetry + watchdog's first unattended daily
   pass (should book nothing, flag only the known 2¢ until 0g lands).
4. Standing: 0d transfer door, 0c hygiene (+ flag-detail display
   quantisation), 0f when commissioned, fp-burn-list persistence
   (small), health-check exit-code cosmetic.
