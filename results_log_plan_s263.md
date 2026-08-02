# Results Log in-tool — build plan (worklist 1a)

**S263/S264 planning doc · 2 Aug 2026 · PLAN ONLY — no code changed.**
Commission (operator, 1 Aug race-day batch): *"Need to save time settling
bets and searching for results."* A results surface (finish order per
race) in the tool; feeds settle-assist + automatic insurance/promo
triggering (4th/5th cashback class included).
Adversarial review follows this plan before any build.

---

## Operator summary (plain language)

What the data says today: **the winner of every race you bet is already
in the system a few minutes after the race. The full finish order
(2nd/3rd/4th/5th) arrives automatically at 5:30 the next morning** for
94% of the horse races you bet. Dogs and trots only ever get the winner.

So the tool can already do this much without any new data work:
- show the finish order on the race page and next to every unsettled bet;
- propose Won/Lost/Void for every unsettled soft-book bet whose race has
  a result, and settle them all in one tap after you eyeball the list —
  each settle banks its own bonus credit exactly as it does today;
- one-tap the owed insurance credits (2nd/3rd, and 4th/5th at 14+
  runners) once positions are known.

The one gap: on race-day evening, positions (2nd/3rd/4th/5th) are not in
yet — only winners. Phase 4 tests whether our subscription can deliver
positions ~minutes after each race instead of next morning. Until then,
insurance one-taps happen next morning (same as your current workflow,
minus the hunting), and win/lose settling works same-day.

Confidence: HIGH on the coverage numbers (measured directly on the live
capture store, 660 races over 14 days + your own 202 bet races since
1 Jul). MEDIUM on same-day positions until the Phase-4 probe runs.

---

## 1. Scoping findings — what results data actually exists

All numbers measured 2 Aug 2026 against the live capture DB
(`/home/racing/racing-data-capture/data/capture.db`, read-only) and the
local store (`~/Desktop/Projects/bethub-v3/data/bethub.db`).

### 1.1 The two results writers (capture side)

**(a) Betfair settled states — same-day, winner-only order.**
`capture/orchestrator.py:1410` `_check_settlement()`: when a race's win
market suspends at the jump the race enters SETTLEMENT phase
(`orchestrator.py:931`; already-CLOSED markets settle immediately,
`:940`) and polls `get_market_results(win_market_id)` every
`SETTLEMENT_POLL_INTERVAL = 120s` up to `SAFETY_TIMEOUT = 3600s`
(`config/settings.py:31-33`). Writes per-runner
`result_status` = WINNER / LOSER / REMOVED, `results_source='betfair_only'`.
**No finish positions** — the win market only distinguishes the winner
(dead heat = multiple WINNERs). The same pass fetches realised BSP into
`betfair_snapshots.bsp_price` on the `is_final_snapshot=1` rows
(`storage/database.py:798` `update_final_snapshot_bsp`). Observed 1 Aug:
BSP written ~10s after close detection (collector log, Cannington R8
13:23:47 → 13:23:57). Net: **winner + BSP land ~2–6 min after the race.**
Only the WIN market is ever fetched — the captured
`betfair_place_market_id` is never queried for settled states.

**(b) Subscription full finish order — next morning, thoroughbred-only.**
`subscription/racing_api.py` (`sync_day`) pulls The Racing API
(`/australia/meets?date=` + `/australia/meets/{meet_id}/races` —
**Australia endpoints, thoroughbred product; no harness/greyhound, and
the 0p GB flip will need the separate GB endpoints later**). Writes
`finish_position` (full order, position 109 = scratched),
`margin_lengths`, `sp_fixed`, `prize_won`, `results_source='subscription'`,
then `refine_placed_status` derives PLACED from
`place_paying_positions`. Scheduled by
`racing-metadata-backfill.timer` **daily 05:30 Adelaide** ("pre-dawn, out
of the live-collector contention window"). Verified: all 104 of 1 Aug's
AU-card thoroughbred races carry `subscription_synced_at`
2026-08-01T20:xxZ = **05:30 ACST 2 Aug — one batch, next morning**. The
backfill retries truncated meetings nightly with an exhaust ceiling, so
a missed meeting can stay position-less forever (see Sandown 22 Jul
below).

**(c) `betfair_historical` (BSP/win_result CSV import) is STALE —
max `meeting_date` = 2026-02-28, zero rows since.** It was the S251
one-off Data Portal import. Anything reading it for current races gets
nothing (see 1.4).

### 1.2 Coverage — the authoritative-finish-order answer

**AU-card thoroughbreds** (has_bookies_capture=1, non-trial,
19 Jul–1 Aug, races already run): **660 races**

| class                                   | races | % |
|-----------------------------------------|------:|-----:|
| full finish order (every active runner) |  611  | 92.6 |
| partial positions                       |    8  |  1.2 |
| settled statuses only (winner known)    |   20  |  3.0 |
| no results at all                       |   21  |  3.2 |
| **winner known (any source)**           |  639  | 96.8 |
| margins present                         |  619  | 93.8 |
| SP present                              |  619  | 93.8 |

**The operator's own bet races** (202 distinct win markets across 466
bets since 1 Jul; all 202 resolve in capture, zero unresolved twins):

| code         | markets | full order | any status (winner) |
|--------------|--------:|-----------:|--------------------:|
| thoroughbred |    180  | 169 (94%)  | 176 (98%)           |
| greyhound    |     15  |   0        | 15 (100%)           |
| harness      |      7  |   1        | 7 (100%)            |

- The 4 thoroughbred markets with **zero** results (Sandown 29 Jul ×3,
  Devonport 26 Jul) are the 0m review-set class (adjacent-day duplicate
  labels / contaminated rows — frozen set, cure belongs to 0m, not
  here). The plan's read path returns an honest "no result captured"
  for them.
- Sandown 22 Jul ×4 have statuses but no positions — a subscription
  meeting miss that exhausted its retries. Expect a ~2–6% permanent
  position-less tail until/unless re-synced by hand.
- **Dogs/trots: winner-only, forever, on current sources.** The
  subscription is thoroughbred-only. ~11% of the operator's bet markets.

**BSP:** realised BSP present same-day on final snapshots for **101/104
(97%)** of 1 Aug AU-card thoroughbred races.

### 1.3 Timing (how soon after the race)

| datum                          | when available | source |
|--------------------------------|----------------|--------|
| winner / losers / removed      | ~2–6 min after race | Betfair settled poll (120s cadence) |
| realised BSP                   | same pass, ~2–6 min | `bsp_price` on final snapshots |
| full order, margins, SP, prize | **next morning 05:30 ACST** | subscription backfill timer |
| dead heat (winner)             | ~2–6 min (multiple WINNERs) | Betfair |
| track condition                | pre-race + subscription | already served |

So: **same-day = winner-only; positions for 2nd/3rd/4th/5th verdicts
land next morning.** This matches the lived workflow (S256: "11 gap rows
await overnight results"). Phase 4 attacks this gap.

### 1.4 What the racing-api already serves, and two defects found

`api/routes/results.py` (VPS):
- `GET /racing/results/{race_id}` — full runner detail for one race row.
  **Used today** by v3's `clients/vps_client/v1/results.py:race_results`.
- `GET /racing/results/by-market/{market_id}` — **rewritten by 0l
  Layer A**: `fetch_fragments` + `pick_primary` + cross-fragment union +
  name-dedupe. The v3 client docstring still says "that route is not
  used" because of the old DR-034 `ORDER BY id` bug — **stale comment;
  the union rewrite is the live-proven read** (market 1.260470533). This
  is the natural race-keyed read for the results log.
- `GET /racing/results/today` — whole settled card. Two wrinkles:
  `race_date = date('now')` is the **UTC** date (accidentally right for
  a 6–9am Adelaide settle-up, wrong after 09:30), and it N+1-loops every
  race. Fix: explicit `?date=` (pattern exists in `races_by_date`).
- **Defect (fix in Phase 0): BSP served is mostly wrong-source.**
  `_build_runner_results` reads BSP from `betfair_historical` (dead
  since Feb) and falls back to the final snapshot's `best_back_price` —
  it never reads the realised `betfair_snapshots.bsp_price` that IS
  captured same-day for 97% of races. Today's "SP" in the v3 settle
  strip is actually the closing back price.

v3 already has (must compose with, not duplicate):
- `GET /api/v1/bets/{bet_id}/race-result`
  (`ui/api/routers/bets.py:3244-3345`): leg → `resolve_race` (date,
  venue, R-number; verifies `win_market_id` matches the leg) →
  `race_results(row_id)`. Returns top-4 `placings` + the bet's own
  runner's `selection_position` / `selection_scratched`, dead-heat and
  void flags. **Consumers:** BetLog's `SettleDoorResult` strip
  (`BetLog.tsx:462`) and Burst Review's per-gap-row `gapVerdict`
  (`BurstReview.tsx:91,275-307`).
- The twin-repair census/"settled-count audits" used the same
  races/runners settled columns — no separate results store exists.

---

## 2. Read path (capture → racing-api → v3)

**Principle: one new race-keyed read; everything else reuses what runs
today. All reads cross the DR-028 tunnel (port 8400); nothing opens
capture.db locally.**

1. **VPS (Phase 0, small):**
   - `_build_runner_results` BSP precedence becomes: realised
     `betfair_snapshots.bsp_price` → `betfair_historical.win_bsp` →
     closing back (kept, but labelled: response gains
     `bsp_source: "settled" | "closing_proxy"` so v3 can render "SP
     3.40" vs "~3.40 (closing)"). Applies to all three results routes.
   - `/racing/results/today` gains optional `?date=YYYY-MM-DD`
     (explicit Adelaide race day from the caller; default unchanged).
2. **v3 vps_client:** new `race_results_by_market(market_id)` wrapping
   `/racing/results/by-market/{id}` with the same envelope heuristics as
   `race_results` (§9.3), returning the **full** ordered runner list +
   void/dead-heat/track fields. Update the stale DR-034 docstring in
   `clients/vps_client/v1/results.py` while touching the module; note in
   `contracts/vps_client_contract.md`.
3. **v3 API:** new `GET /v1/racing/race-result?market_id=...` in
   `ui/api/routers/racing.py` → `race_results_by_market`. Response:
   full finish order (position, name, selection_id, margin, SP+source,
   dead-heat), track condition, `market_voided`, `available/reason`
   (same graceful-absence shape as the per-bet endpoint). **Full order,
   not top-4** — the cap in the per-bet strip (`placed[:4]`) is that
   strip's display choice and stays.
4. **Unchanged:** `GET /v1/bets/{bet_id}/race-result` remains the
   bet-anchored read (BetLog strip, gap verdicts, and any bet whose leg
   lacks a market id). No duplication: both endpoints converge on the
   same VPS results rows.

Fan-out arithmetic that forces the race-keyed read: race-day soft-bet
volume is ~86–103 (1 Aug: 86; 25 Jul: 103). Settle-assist over per-BET
fetches would be ~100 tunnel round-trips; grouped by race it is ≤~30.
Per-bet stays for ≤20-row lanes where it already runs.

---

## 3. UI surface — where results live

Real-world language throughout ("Result", "Settle up", "bank" — never
"door"/mechanism words in copy).

**(a) Race page (Racing.tsx) — result strip.** When the selected race
has a result: one strip in the market panel — `1st Inside Job (SP 4.20)
· 2nd … · 3rd … · 4th …` expandable to full order, margins, track
condition, "MARKET VOIDED"/"=DH" flags, and a "result in — n bets on
this race" chip that links to the settle-up lane. Mirrors the existing
`SettleDoorResult` line visually → **trivial layout, no mock needed.**
Query keyed `['racing','race-result', market_id]`, retry:false,
staleTime 60s, enabled only once `scheduled_start_time` has passed.

**(b) Burst Review — "Settle up from results" lane (the
settlement-time surface).** New lane above the existing unsettled-soft
list: pending soft bets grouped by race, each race showing its finish
strip and each bet a **proposed outcome chip** (§4). This is a NEW
surface on an operator-critical screen → **mock-first per the UX
standing feedback: one local HTML mock (grouped-by-race list, chips,
preview modal) for approval before build.** Burst Review is the right
home — it is already the end-of-session screen with the settle,
credit-gap and pairing lanes; the race page strip links here.

**(c) BetLog** — unchanged (strip already present). The gap-lane
verdicts gain the field-size rule (§5).

**(d) Betfair bets** are never listed in the lane — they settle through
the worker (standing split). The lane's header says so in one line when
Betfair bets are pending: "n Betfair bets settling automatically."

---

## 4. Settle-assist flow

**Standing split respected: the results log ASSISTS operator settlement
of soft-book bets; it never silently auto-settles.** (Worker stays
Betfair-only: `settle_bet_endpoint` 422s Betfair; nothing here changes
that.)

**Proposal derivation** (pure function, per pending soft bet × its
race result, computed client-side from the race-keyed read):
- selection `result_status` WINNER (no dead heat) → **Won**
- LOSER / PLACED (win bet) → **Lost**
- REMOVED / `selection_scratched` → **Void**
- `market_voided` → **Void** (every bet on the race)
- **No proposal — "hand settle" row, excluded from one-tap:** dead-heat
  at the bet's position (soft rows carry no dead_heat_count; a Won
  settle would auto-bank the FULL bonus — the known 1b edge); no result
  yet; selection unresolvable (no `betfair_selection_id` leg match);
  multi-leg / LogOtherBet exotics; anything not a win-market single.

**One-tap shape — RECOMMENDED: "Settle all proposed" with per-bet
preview.** The lane lists every proposal (bet, book, stake, odds,
proposed outcome, and the P&L delta of the proposal); one tap opens a
confirm card ("Settle 14 bets: 3 Won · 10 Lost · 1 Void"), confirm runs
a **client-side sequential loop over the EXISTING
`POST /v1/bets/{bet_id}/settle`** — the Burst-Review sweep precedent
(`sweepMutation`, per-call-committed, no bulk endpoint at this scale).
Per-row single-settle chips also remain for cherry-picking.
- Each settle call fires the **existing auto-credit hook naturally**
  (`try_auto_bonus_credit` inside the settle endpoint) — a won bonus
  bet banks its own credit per bet, appears in the auto-credits lane,
  undo door unchanged. No new credit path.
- Failures: continue the loop, collect per-bet errors, honest summary
  ("12 settled · 2 failed: …"), refresh all surfaces
  (`invalidatePromoSurfaces` + bet feeds). Every settle is individually
  audited/logged exactly as a manual settle is today.
- Friction-vs-safeguards standing rule: the preview informs; nothing
  blocks. Hand-settle rows are flagged, never gated.

**The alternative — full-auto** (a worker pass that settles soft bets
from results with no tap) reverses the "soft books stay
operator-settled" standing decision. Recommendation: **ship
preview-first now; stage full-auto as a later explicit flip** if the
operator wants it after living with the assist (same staging pattern as
1b part (c) auto-bank, which posed the question and got the reversal
recorded). This is the single operator decision (§8).

---

## 5. Insurance / promo triggering

All through the EXISTING doors; results only make the verdicts
computable sooner and the taps fewer.

- **Insurance (settled-lost, 2nd/3rd, 4th/5th):** when a proposal is
  **Lost** and the bet's template has `refund_positions` and the
  selection's position is a **covered** insured position, the row's
  action becomes **"Settle lost + bank $X"** — the existing
  settle→`POST /v1/promos/credit-in` compose (`bonusLandedMutation`
  precedent, order matters: credit-in requires `settled_lost`). One tap,
  two audited events, idempotent (`find_existing_credit` guard).
- **Covered positions = the shared server rule.** Extend the client
  verdict to `covered_insured_positions(refund_positions,
  position_min_field, field_size)` parity (the server rule shared by the
  credit-in door and the gap detector, `credit_gap.py:99-121`) instead
  of raw `refund_positions`. The gap row / bet feed must expose
  `field_size_at_placement` and the catalogue already exposes
  `position_min_field` — this makes the **4th/5th cashback template
  (`{"4":14,"5":14}`, cap $100) ride the same rails**: 4th at a
  14+ field → owed; 4th at 13 → "outside (field 13 < 14)".
- **Field-degradation honesty (Cat-4 lesson: scratchings can degrade
  terms post-placement):** the race result gives the actual field
  (finishers + failed-to-finish). If `field_at_placement ≥ min_field`
  but actual field `< min_field`, the verdict is **check-book**, never
  auto-owed. BetRight-3rd-≤7 stays check-book (unchanged rule).
  Dead-heat at the position stays "?" (unchanged).
- **Timing honesty:** these one-taps light up when positions exist —
  next morning on current sources (or same-day once Phase 4 lands).
  Same-day, insurance rows settle Lost via §4 and land in the existing
  credit-gaps lane exactly as today; nothing double-credits because the
  door's idempotency guard is the single write path.
- Bonus-winnings on Won needs no new wiring — the settle loop's
  auto-credit hook covers it (including the dead-heat exclusion, which
  the hand-settle lane preserves).

---

## 6. Red-before test plan (per layer)

Every layer lands with its failing test written first (standing 1b
convention). Gates: `uv run pytest` + `npx vitest` + `tsc` +
`npm run build`; capture repo suite on the VPS side.

1. **VPS results routes:** (a) fixture race with `bsp_price` AND
   closing back → route must serve the realised BSP with
   `bsp_source='settled'` (**red today** — serves closing back);
   (b) `?date=` on /today returns that Adelaide date's card (**red** —
   param unknown today); (c) regression-pin: by-market twin union output
   unchanged by the BSP edit.
2. **Intraday sync guard (Phase 4):** running `sync_day(today)` while
   races are mid-card must not blank existing Betfair statuses or
   scratchings for unresulted races (upsert only sets result fields when
   present — pin it), and must be idempotent twice-over (0 duplicate
   runners, positions monotonic).
3. **vps_client:** `race_results_by_market` envelope tests
   (fresh / GENUINE_ABSENCE / NOT_YET_CAPTURED / window), mirroring the
   existing §9.3 suite (**red** — function absent).
4. **v3 endpoint:** `GET /v1/racing/race-result` — full order (>4
   runners served), voided flag, dead-heat flag, absence reason
   pass-through (**red** — 404 today).
5. **Proposal derivation:** unit matrix — WINNER→won, LOSER→lost,
   PLACED→lost, REMOVED→void, market_voided→void-all, dead-heat→none,
   no-result→none, unresolved-selection→none, multi-leg→none.
6. **Settle-all loop:** component test — preview counts, sequential
   door calls, mid-loop failure continues + error summary; integration:
   a won bonus bet in the loop yields the system credit event
   (source='system') and the settle response's credit marker renders.
7. **Insurance one-tap:** settle-lost→credit-in compose (assert order);
   `covered_insured_positions` client parity incl. 4th/5th at field
   14/13 and the degraded-actual-field → check-book case; BetRight-3rd
   unchanged; idempotency (second tap → "already credited").
8. **Race page strip:** vitest render with mocked query (pattern:
   `Racing.*.test.tsx`), incl. voided + dead-heat rendering and the
   pre-jump disabled state.
9. **Live proof (each phase):** first race day after deploy — strip vs
   the app's own result page for 3 races; one settle-all batch checked
   to the cent in the money check; first insurance one-tap re-verified
   against the book's ledger. Never claim "always" pre-live-proof.

---

## 7. Phases + effort

- **Phase 0 — VPS truth fixes (0.5 sitting).** BSP precedence +
  `bsp_source`; `?date=` on /today. Deploy window: any app-closed
  moment; no collector restart needed (API service only).
- **Phase 1 — race-keyed read + race page strip (1 sitting).**
  vps_client function + contract note + v3 endpoint + Racing strip.
  No mock (trivial layout, mirrors existing strip).
- **Phase 2 — Burst Review settle-up lane (1–1.5 sittings).** Mock
  first (one local HTML round); proposal derivation; grouped-by-race
  lane; preview + settle-all loop; hand-settle flags; Betfair header
  line. **This is the time-saving core.**
- **Phase 3 — insurance/promo one-taps (0.5–1 sitting).**
  Covered-positions verdict upgrade (+ expose
  `field_size_at_placement` on the gap/feed rows if absent), "Settle
  lost + bank $X", 4th/5th class, degradation flag.
- **Phase 4 — same-day positions probe → intraday sync (1 sitting +
  canary).** (a) One journaled probe on a race afternoon: manual
  `sync_day(today)` at ~14:30 + 17:30 ACST; measure positions gained
  and API behaviour for in-progress cards. (b) If the API serves
  same-day results: a systemd timer (pattern: morning-sweep unit,
  which already writes hourly 06:00–17:00 on race days post-0u
  indexes) running `sync_day(today)` + `refine_placed_status` every
  ~20 min, 12:00–19:30 ACST; deploy off-race-day, one canary Saturday
  before calling it live. (c) If the API does NOT serve same-day
  results: fall back to fetching **place-market settled states** in
  `_check_settlement` (client method already takes any market id) —
  same-day top-3 membership, which unlocks the [2,3]-template one-taps
  only (not [2]-only, not 4th/5th). Decide (b) vs (c) on probe
  evidence; (b) preferred (full order, margins, SP, no collector
  change).

Total ~4–5 sittings. Order is strict: 0→1→2 ship independently and each
is useful alone; 3 needs 1's read; 4 is independent of 2/3 and can slot
anywhere after 0. No dependency on 0p/0m; the 0m review-set tail
(~4 bet races) self-heals into honest "no result" lines meanwhile.

---

## 8. Operator decisions (aim: one)

**THE decision — settle-assist shape:** one-tap **"Settle all from
results" with per-bet preview** (recommended, §4) vs **full-auto**
soft-book settlement from results (reverses the standing
"soft books stay operator-settled" split; can be staged later after
living with the assist). Recommendation: preview-first now.

Engineering-decided (with rationale, not escalated):
1. Race-keyed read via the 0l by-market union route (twin-safe
   server-side; ≤30 calls vs ~100 per-bet on a Saturday); per-bet
   endpoint retained for bet-anchored strips. (§2)
2. Settle-all = client-side sequential loop over the existing settle
   door — per-bet audit + auto-credit hook untouched; no bulk write
   endpoint at this scale (Burst sweep precedent). (§4)
3. Proposals never cover dead-heats, scratch-ambiguity, unresolved
   selections, exotics — flagged hand-settle, never blocked. (§4)
4. Insurance one-tap = compose existing settle + credit-in doors,
   lost-before-credit order; covered-positions rule shared with the
   server. (§5)
5. BSP precedence realised-BSP-first with source labelling; /today
   gains explicit `?date=`; v3 passes explicit Adelaide dates. (§1.4/2)
6. Phase 4 same-day mechanism chosen by probe evidence (intraday
   subscription sync preferred over place-market fallback). (§7)
7. Mock-first applies to the Burst Review lane only; the race-page
   strip mirrors an existing pattern. (§3)
8. Dogs/trots stay winner-only (subscription is thoroughbred-only);
   their insurance verdicts remain check-book/manual. (§1.2)

---

## S264 ADVERSARIAL REVIEW — AMENDMENTS (NORMATIVE; the build must honor these)

Review (S264, 2 Aug, read-only against code + live DBs). Coverage
numbers reproduced TO THE ROW (660-race cohort: 92.6% full order /
96.8% winner; operator's 202 markets all resolve; 1 Aug: 104 races,
101 with realised BSP). Settle-assist plumbing claims all verified
(auto-credit fires inside every settled_won; dead-heat gate is
`(dead_heat_count or 0) > 0`; settle endpoint 409s non-pending rows;
place/each-way risk safe by construction — win-market singles only).
Verdict: AMEND-FIRST, an editing pass, then build starts immediately on
the preview shape (operator has since CONFIRMED preview — S264
decision 4).

**A1 (§1.4 + §6.1(a) — the BSP defect is real but misdescribed).**
CONFIRMED: realised `betfair_snapshots.bsp_price` is never read by any
results route, and `betfair_historical` is dead since 2026-02-28. WRONG
as written: nothing serves closing back "as BSP" — the route ships it
in its own `bf_closing_back` field and the v3 client maps
`bsp = bf_bsp` falling back to `sp_fixed`; the BetLog strip therefore
shows the official SP next morning and NOTHING same-day. The defect is
same-day BSP ABSENCE, not a mislabel. §6.1(a)'s red test is red by
absence; rewrite its description accordingly. The fix (realised-BSP-
first + `bsp_source`) is unchanged and right. Optional: when
`bsp_source` ships, fix `_source_for`'s BETFAIR_WIN inference off
closing prices.

**A2 (§2 volume).** "≤~30 grouped round-trips" → "≤~50" (measured: 37
distinct bet races on 1 Aug, 46 on 25 Jul). Still 2–3× better than
per-bet ~100; conclusion stands.

**A3 (§6.2 — the load-bearing pin is too weak).** Two corrections:
(a) The pin "upsert only sets result fields when present" does NOT
prevent WINNER demotion — `upsert_runner` COALESCE is
new-non-null-WINS. Extend the pin to: **subscription sync must never
demote an existing WINNER** (if the API numbers the second dead-heater
≠1, sync_day would flip its WINNER→LOSER, hide the dead-heat, and the
assist would propose Won-full-bonus — the exact 1b edge). Red-test it.
(b) Dead-heat detection (`winner_count>1`) is polluted by twin-row
contamination (53–78 multi-WINNER races/month since March vs a true
2–4). Failure direction is SAFE (excluded to hand-settle; zero in the
operator's own 202 markets) but: dual-source the detection
(`winner_count>1` OR duplicated `finish_position=1`) and word the lane
flag "conflicting result rows — hand settle", never asserting "dead
heat".

**A4 (honesty line, LOW).** A market voided AFTER a bet settles stays a
manual correction (endpoint 409s non-pending; the assist can never
re-open a settled bet). State it in §4.

**Decision closed:** settle-assist shape = one-tap-with-per-bet-preview,
operator-CONFIRMED S264 (no longer default-if-unanswered).
