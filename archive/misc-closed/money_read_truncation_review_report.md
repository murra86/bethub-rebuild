# Money-read silent-truncation review — S242/S243 (Sun 19 Jul 2026)

**Trigger:** Sunday review incident — an ad-hoc P&L scan over `GET /api/v1/bets`
read only the default 50-row page of Saturday's 107 bets and reported +651.56
against the true +679.08. The Balances page was right; the scan was wrong.
**Scope:** every money-relevant read in the codebase swept for silent bounds
(default limits, hardcoded LIMIT clauses, page caps, frontend slices) by 4
parallel finders → 55 raw findings → 40 money-relevant after dedup →
adversarial verify each → independent 3-way transactions reconcile.
**Run note:** the review workflow was interrupted at the synthesis stage on
19 Jul (session died mid-run, 41/45 agents complete); recovered same day from
the run journal — the 2 unfinished verifications were re-run fresh, nothing
re-used without a verdict.

## 1. Executive summary (plain language)

1. **Your money data is clean.** Three fully independent recounts of every
   dollar since the Thursday reset — bet-by-bet, cash-ledger fold, and the
   app's own figure — all land on **+679.08 to the cent**. Saturday's scare
   was a bad read, not bad data.
2. **The thing that lied on Saturday can lie again:** any quick question
   answered through the bets API without asking for *all* rows silently gets
   the newest 50 and produces a plausible-looking wrong day total. The app's
   own screens are honest (BetLog shows "1–50 of 107" and pages properly).
3. **The one that matters most is a time bomb, not a today-problem:** the
   free-bet crediting guard only ever looks at the **oldest 1000** promo
   events. At Saturday's rate that window fills in roughly one racing season.
   After that, already-credited bets reappear as "owed" on the credit-gaps
   list and the double-credit protection stops seeing new credits — the
   operator could pay the same free bet twice with no warning.
4. Two small screens will quietly go stale over weeks (movements fold-out
   caps at 30 rows ever-shown; an unwired void-sweep helper caps at 100), and
   two worker bounds were checked and are self-draining/acceptable today.
5. **Fix shape: one batched brief** (§4) — kill the promo-event window,
   make ad-hoc bet reads honest, and put "latest N" cues on the two capped
   screens — before more data accumulates on top of the traps.

## 2. Confirmed findings (adversarially verified, ranked)

### HIGH — Free-bet credit guard reads only the oldest 1000 promo events
`workflows/promos/v1/fb_credit.py:114` (guard) + `workflows/promos/v1/credit_gap.py:78` (detector that inherits it)

`find_existing_credit` calls `adapter.list_by_event_type(event_type)` with no
limit → adapter default `limit=1000` → SQL `ORDER BY recorded_at ASC …
LIMIT 1000` (`store/repositories/promos.py:317-332`). The window is the
**oldest** 1000 events, so the newest credits — exactly the retry/double-click
population the idempotency guard exists for — fall outside it first.

**Failure day-shape:** store holds 25 `free_bet_credited` events after one
real Saturday; append-only, no pruning → the window fills in ~10–16 weeks of
current operation. From event #1001: (a) every recently-credited safety-net
qualifier **reappears on the credit-gaps owed list** un-dismissed, dollar
amounts inflating what looks outstanding; (b) `POST /v1/promos/credit-in`'s
dedupe can't see the new credit → **a double-credit goes through silently**.
This is the only finding that can move real money the wrong way.

### MEDIUM — `GET /api/v1/bets` default 50-row page (the incident endpoint)
`ui/api/routers/bets.py:293-294, 694, 719, 754` (two finders converged on the same endpoint)

Default `limit=50`, hard max 500 (>500 is a 422, not a clamp). The response
carries honest `total/limit/offset` and the BetLog screen paginates correctly
with a visible "first–last of total" count — **the shipped UI is not
affected**. The trap is every consumer that omits `limit`: ad-hoc scripts,
session-assistant reads, future integrations get HTTP 200 + newest 50 and sum
a plausible wrong number (reproduced live: +651.56 vs +679.08, a 4%
understatement that survives a sanity glance). Re-arms every >50-bet day —
now routine.

### LOW — Balances "Money movements" fold-out shows latest 30 forever
`ui/web/src/routes/Balances.tsx:147` (sole caller, `fetchMovements(30)`; backend clamp 200)

Movements are manual and slow (17 rows after 2 days; ~3/day on a big bet day),
so no single day breaks this — but within ~2–4 operating weeks the fold-out
silently becomes "latest 30 only" with no count, no pagination, no cue,
contradicting the endpoint's own "honest history" design note. Slow fuse,
cosmetic-to-audit impact.

### LOW — Post-settlement void detector drops oldest rows over 100 (latent, unwired)
`workflows/bet_entry/v1/post_settlement_void.py:118, 139-143`

Zero production callers today, so nothing is currently wrong. Once wired as
the designed daily sweep (24h lookback, `limit=100`, newest-first): a
Saturday-shaped day (105 terminal bets, verified live) permanently skips the
5 oldest — they age out of the window before any later run reaches them, and
the report reads `swept=100/flagged=0` with no overflow signal. Must be fixed
**before** wiring, not after.

### Re-run after the interruption — both REFUTED

The two verifications lost in the session crash were re-run fresh:

- **Reconciliation worker sweep bound (100/pass) — REFUTED (LOW).**
  `workflows/bet_entry/v1/reconciliation.py:552` + worker at
  `ui/api/reconciliation_worker.py:86`. Self-draining work queue, ~1200
  rows/hour throughput vs a 107-bet day; nothing sums money over a single
  pass, and settlement fail-closes on unreconciled bets
  (`settlement.py:98-109`) so a deferred bet stays PENDING rather than
  settling at a stale stake. **One hardening note the adversarial check
  surfaced:** manual operator resolution writes `settlement_state` only and
  never clears `match_status` (`settlement.py:1893-1899`), and reconciliation
  deliberately keeps sweeping parked bets (`settlement.py:1697-1700`) — so a
  genuinely never-resolvable row occupies one of the 100 sweep slots
  *forever*. Years from mattering at observed park rates, but a one-line fix
  (clear/exclude `match_status` on terminal manual resolution) belongs in the
  batched brief.
- **Provisional/manual-queue 100-row cap — REFUTED (NONE).**
  `ui/api/routers/provisional.py:281`. No sum or count computed over the
  capped set; rows past 100 stay in the DB and surface as earlier rows
  resolve; the daily money check reads the queue uncapped
  (`ops/settlement_review.py:232-237`) and would report a >100 queue at true
  size same-day. Queue observed at 0–4 rows, currently 0.

## 3. Reconcile certificate (independent 3-way, read-only)

All three views computed from scratch, not through each other:

| View | Method | Result |
|---|---|---|
| Bets | Own per-bet derivation from raw rows (BACK/LAY/FB, commission, voids) | **+679.08** |
| Ledger | Own event-fold: per-account cash − day-0 seeds ($10,684.67 exact) − external funding ($700) | **+679.08** |
| API | `GET /api/v1/cash-flow/pnl`, `self_check_ok: true` | **+679.08** |

107/107 Saturday bets matched the app's canonical per-bet P&L to the cent.
No orphaned events, no duplicate bets, LAY commissions all populated, the
void→FB-return path correct. Cross-foot: BACK cash −60.00, FB wins +1,200.00,
LAY −460.92.

**Two operator-attention items surfaced (neither affects cash P&L):**

1. **Zeroed WON bet — confirm intended:** `bet-ac23aa98…` (Tim–BetRight,
   safety_net, won @8.0, requested $50) has `matched_stake=0` via an
   audit-trailed operator edit (18 Jul 13:26) and contributes $0. Saturday
   reconciles to the cent with it at 0, so real cash agrees — but a won
   50@8.0 would otherwise be +$350. One-line confirm that zeroing was
   deliberate.
2. **Free-bet inventory $50 light:** `bet-3b84ec36…` (single $50 FB,
   settled lost) has **two** `free_bet_deployed` events at the identical
   microsecond, drawing from two different credits — a double-write. The
   bonus board shows $150 / 3 FBs remaining; truth is $200 / 4. FB face value
   isn't cash, so P&L is untouched; needs a correction through the promo door
   (derive-on-read means fixing the event spine, not a balance).

Also re-confirmed (known, money-harmless): S227 finding S1 — 16 lay bets keep
placement-time snapshots in `bet_legs` while the `bets` row is truth.

## 4. Recommended fix — ONE batched brief ("honest money reads")

Per the sweep-the-class-then-one-fix discipline:

1. **`fb_credit.find_existing_credit`** (`fb_credit.py:113-114`): stop
   scanning a 1000-event page. Either query by qualifier directly (targeted
   SQL on the payload's qualifying-bet id) or page through all
   `free_bet_credited` events. This single change fixes both HIGHs (guard +
   credit-gaps detector inherit the same call).
2. **Adapter/store defaults** (`promo_store_adapter.py:213-224`,
   `store/repositories/promos.py:317-332`): a silent `limit=1000` default on
   an append-only money-event table is the root class — make money-event
   list methods explicit: caller passes a bound or asks for all; no silent
   default.
3. **`GET /api/v1/bets` ad-hoc honesty** (`ui/api/routers/bets.py`): keep the
   UI's 50-row pagination (it's honest), but close the omitted-limit trap —
   e.g. support an explicit fetch-all form for tooling and add the standing
   rule to ops docs: any P&L math over the bets API must reconcile
   `len(bets)` against `total` (one line of guard in any future script).
4. **Balances movements** (`Balances.tsx:147, 462-537`): fetch-all (backend
   clamp 200 permitting a paged loop) or render "showing latest 30 of N"
   with the unbounded count.
5. **`post_settlement_void.py:118`**: replace the `limit=100` single read
   with count-checked paging *in the same brief*, so it can never be wired
   in its current shape.
6. **Sweep-slot hardening** (`settlement.py:1893-1899`): clear or exclude
   `match_status` when a bet is terminally resolved through the manual door,
   so a dead row can't hold a reconciliation sweep slot forever.
7. **Promo-door correction** for the $50 double-deployment (reconcile item 2)
   and the one-line operator confirm on the zeroed bet (item 1).

## 5. What was not covered

- The 23 undismissed credit-gaps and the Sarie bonus-winnings FB no-credit
  flag (bet-day notes item 7) are a separate queued triage — not re-examined
  here beyond confirming the detector's mechanism.
- Betfair-side API pagination (listCurrentOrders/listClearedOrders page
  walking) was swept by the ops finder but only as far as code reading — no
  live Betfair calls were made on a Sunday.
- Frontend screens were verified against the current build (`ui/web/src`);
  the served `dist` bundle was assumed to match it (last build S241).
- The v2 legacy app and VPS capture side were out of scope.

## Appendix — verified-safe highlights (38 refuted + safe-by-construction)

- **`ops.settlement_review` daily money check: verified unbounded end-to-end**
  and empirically re-run against the 107-bet Saturday — all 107 bets, 86
  cycles processed, every summary count tied to independent SQL. The daily
  money check can be trusted on busy days.
- BetLog screen: honest pagination + total indicator; no sum computed over
  the page.
- `balance_derivation` list reads: explicit `limit=100_000` (orders of
  magnitude above realistic volume) — safe, monitored.
- Reconciliation/settlement worker batch bounds: self-draining loops, not
  subset computations (adversarial checks in §2, "Re-run after the
  interruption").
- Full refuted list with evidence retained in the run journal
  (session 89192e14, `wf_97aafee9`).
