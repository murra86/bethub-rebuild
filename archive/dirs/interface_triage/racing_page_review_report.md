# Report — Racing-page + Betfair-modal codebase review

**Type:** Read-only source review (no edits made).
**Repo:** `bethub-v3` (local Mac), branch `main`, working tree dirty by
design — **untouched** (62 `git status --short` entries at start and at
close; no git operations performed).
**Brief:** `interface_triage/racing_page_review_brief.md` (Session 165).
**Run:** single bounded session, 2026-06-19 (ACST).
**Method:** source reads + targeted greps. Test suite **not** run — every
answer below is grounded in `file:line` reads; running `uv run pytest`
would not change a verdict (see self-assessment). No DB read was needed.
No network / Betfair calls.

---

## §5 — Area map

| Area | Owning file | Data source |
|---|---|---|
| Race-list sidebar + **T/H/G filters** | `RaceListSidebar.tsx` | `GET /racing/races` → `racing.py:list_races` → `get_racing_markets` (Betfair) |
| Race selection / page shell / lifted form state | `routes/Racing.tsx` | local state; `selectedMarket` from sidebar |
| Runner column (name + number) | `OddsTable.tsx:226-229` | `idx+1` (tool) + `runner_name` from catalogue (`racing.py:get_market_catalogue_endpoint`) |
| BF Back / BF Lay / Matched | `OddsTable.tsx:230-232` | `GET /racing/markets/{id}/prices` → `get_live_market_prices` (streaming cache → REST fallback) |
| Raw EV / Promo EV columns | `OddsTable.tsx:197-216` | frontend-derived (`ev/evEngine.ts`) |
| Soft Odds column (+ stepper) | `OddsTable.tsx:235-279` | frontend (`manualOdds` ?? BF back); ladder `ev/softOddsLadder.ts` |
| TREND column | `OddsTable.tsx:280-306` | frontend (`hooks/usePriceMemory.ts`) |
| Promo selection + per-promo EV inputs | `PromoBar.tsx` + `promos/presets.ts` | frontend |
| Log-bet panel | `LogBetPanel.tsx` | `GET /racing/accounts`, `/racing/log-context`; `POST /racing/bets` |
| Hedge / quick-lay modal | `HedgeModal.tsx` | live prices poll; `POST /racing/lay` (`place_bet`, side=LAY) |
| Commission | `ev/commission.ts` | `market_base_rate` (catalogue, `description.marketBaseRate ÷100`) |

Two files the §3 pre-reads under-pointed: **the T/H/G filters live in
`RaceListSidebar.tsx`, not `Racing.tsx`** (see §10a); and the displayed
runner "second number" originates in the Betfair `runner_name` string,
not a discrete field (see Q3).

---

## Q1 — Are the promo EV estimates sound? (§6)

**Display path:** `PromoBar` writes `promoConfig` → `OddsTable.tsx:198-216`
(table column) and `Racing.tsx:134-165` (log-panel snapshot) both call
`promoEV()` (`evEngine.ts:467-521`), which branches by promo type.

**Probability base (shared by raw + promo EV):** geometric midpoint of the
BF back/lay spread, `√(back·lay)`, with lay rejected as stale when
`lay > 2×back` → fallback `back + 2 ticks` (`estimateTrueOdds`,
`evEngine.ts:188-197`). Field-normalised to sum 1 (`oddsToProbabilities`,
52-58). Place probabilities via corrected Harville with load-bearing
exponents `GAMMA=0.77 / DELTA=0.62 / EPSILON=0.48` (`evEngine.ts:32-34,
95-170`). Commission excluded from probability (correct — it's a cost).

**Per promo type:**

- **Insurance** — `evInsurance` (`evEngine.ts:309-338`). Plain terms:
  `EV% = [P_win·odds·S − S + P_insured·bonus·fbConv] / S × 100`, where
  `bonus = effectiveStake·(return_pct/100)`, `P_insured` = sum of the
  configured place probs (`any_non_win` / `2nd` / `2nd_3rd` /
  `2nd_3rd_4th`), `fbConv = 0.70` when `return_type='free_bet'` else
  `1.0`. Inputs all wired correctly from config: `return_pct`,
  `insured_positions`, `return_type` (`OddsTable.tsx:207-211`). **Sound;
  fixture-pinned** (`v2_regression.ts:66-70`, `evInsuranceFB2nd3rdAt2_5`).
- **Free Bet / Bonus Bet** — `evFreeBet` (`evEngine.ts:411-424`), reached
  via `promoEV` (486-491). Pure lay-hedge, returns **% of face value**:
  `layStake = (odds−1)·face / (lay−1+(1−c))`, `lockedProfit =
  layStake·(1−c)`. Models free-bet **stake-not-returned** correctly. Uses
  **live** `best_lay` + commission(`mbr`); returns `null` if no lay.
  **Sound; fixture-pinned** (`evFreeBet_r0_lay216 = 48.65…`).
- **Boosted Odds** — `evBoostedOdds` = raw EV at `bookOdds`
  (`evEngine.ts:400-403`). There is **no separate boosted-price input** —
  the operator must enter the boosted price into the Soft Odds cell; the
  column then reads as raw EV at that price. Behaviour is correct given
  that, but the "boost" is operator-typed, not promo-driven (note).
- **Bonus Winnings** — `evBonusWinnings` (`evEngine.ts:362-393`).
  **DEFECT (see Finding F1).** The function reads `promo.bonus_pct` /
  `promo.bonusPct` (line 370), but the config object the UI builds carries
  only **`return_pct`** — `bonus_pct` is never set on either call site
  (`OddsTable.tsx:205-212`, `Racing.tsx:150-154`; confirmed by grep —
  `bonus_pct` appears nowhere outside `evEngine.ts` and its unit test).
  Result: `bonusPct = 0` → `bonusPerDollar = 0` → `adjustedOdds = bookOdds`
  → **the Bonus-Winnings Promo EV silently collapses to the raw EV**,
  ignoring the configured bonus % entirely. The regression test passes
  because it calls the engine with `bonus_pct: 100` directly
  (`evEngine.test.ts:99-100`), masking the UI wiring gap.

**Free-bet conversion (~70%):** hard-coded `DEFAULT_FB_CONVERSION_RATE =
0.7` (`evEngine.ts:41`), **not surfaced in the UI** (PromoBar has no
conversion input). Duplicated as the literal `0.7` in two more places
(`HedgeModal.tsx:18`, `bonusWinningsEffectiveOdds` `evEngine.ts:541`) — a
consistency risk if ever changed (Finding F4).

**Strategy-1 insurance cycle:** `evInsurance` models a **single qualifying
bet + its triggered refund** (refund valued at 70% when it returns as a
free bet). It does **not** model laying the qualifying bet on the exchange,
nor the onward deployment+hedge of the triggered free bet (the "free-bet
outcome" leg of the whole cycle). Whether that single-leg framing matches
the operator's whole-cycle EV definition is a judgment call → flagged, not
"corrected" (Finding F5).

**Probability-set inconsistency:** the table normalises over
`status ≠ REMOVED ∧ ≠ WITHDRAWN` (`OddsTable.tsx:102-108`), but the
log-panel snapshot normalises over `status === 'ACTIVE'`
(`Racing.tsx:104-106`). In a normal OPEN race these coincide; in edge
states they diverge, so the EV shown in the table can differ slightly from
the EV stored against the logged bet (Finding F6).

**Dead code:** `calculateLayFieldProbabilities` (`evEngine.ts:256-270`) is
defined but never called (grep-confirmed). Low risk, noted.

**Verdict:** insurance, free-bet, and boosted paths are sound and
fixture-pinned; **bonus-winnings EV is broken in the UI path (F1)** and is
the load-bearing finding here.

---

## Q2 — Does the modal hedge amount auto-calc correctly? (§7)

**Lay sizing** (`HedgeModal.tsx:193-210`), per hedge type:
- **Cash:** `laySize = bookOdds·backStake / (layPrice − c)`;
  `lockedProfit = laySize·(1−c) − backStake` (212-216).
- **Free bet:** `laySize = (bookOdds−1)·backStake / (layPrice − 1 +
  (1−c))`; `lockedProfit = laySize·(1−c)`. This is the **stake-not-returned**
  free-bet hedge and is **byte-identical to `evFreeBet`'s `layStake`**
  (`evEngine.ts:419-422`) — the modal and the EV engine agree. ✔

**Live price:** lay price initialises from `runner.best_lay[0]`
(150-152), then a **500 ms poll** (`HEDGE_MODAL_POLL_MS`, 163-168) updates
the input via `useEffect` (180-184) **until the operator edits it**
(`userEditedLayPrice` ref) — then it sticks. `laySize` is a `useMemo` over
`layPriceNum`, so it **recalculates on every price change** (193-210). ✔

**Commission:** from `catalogue.market_base_rate` via `getCommission`
(186-187), 8% fallback. The catalogue is fetched once per market
(`Racing.tsx:81-86`, `staleTime: Infinity`), so commission is effectively
**constant per market** — it will not re-derive intra-race (note, not a
bug).

**Free-bet stake-not-returned:** modelled (free-bet denominator). ✔

**Guards present (good):** liability soft-cap (`$500`, localStorage-tunable,
non-disable-able), and a fat-finger check when the entered lay diverges
>10 ticks from live best lay — both force a confirm screen
(`HedgeModal.tsx:242-262, 428-443`).

**`FB_CONVERSION` (0.7) in the modal is display-only (Finding F2).** The
scream-box claims *"v2 FB conversion 70% applied"* (347-348), but the
constant is **used nowhere in the modal's math** — lay sizing and locked
profit apply no 0.7 (correctly; hedge sizing matches the full FB face
value's winnings). The message overstates what the modal does and could
mislead an operator who "works to ~70%."

**Back-bet support:** **LAY only.** `postPlaceLay` → `/racing/lay` →
`place_bet(side=BetSide.LAY)` is hard-coded (`racing.py:1029`);
`PlaceLayRequest` has no `side` field. Adding a back would touch:
`HedgeModal.tsx` (side toggle + sizing sign), `api/racing.ts`
(`PlaceLayRequest`/`postPlaceLay`), `racing.py:place_lay` (side param,
persistence semantics, `Construction`), and `build_hedge_bet_record`
(`Construction.LAY_AGAINST_BACK`). **Reaches backend + bet-record layer.**
Mapped only, per brief.

**Verdict:** auto-calc is **correct and live-price-driven**; the only
issue is the **misleading 70% label (F2)**, which is cosmetic to the math.

---

## Q3 — Runner-number provenance + canonical key (§8)

**The two numbers in "1. 2. Heart N Power":**
- **First number ("1.") — tool-applied.** `OddsTable.tsx:227` renders
  `{idx + 1}. {runnerName}`, where `idx` is the position in the
  `prices.runners` array (market-book order from `get_live_market_prices`).
  It is a **1-based array index**, not any racing number.
- **Second number ("2.") — Betfair's, embedded in the name string.**
  `runnerName` is `runner_name` from the catalogue, taken **verbatim** from
  Betfair (`market_catalogue.py:91`, `runner_name=str(raw["runner_name"])`).
  For AU racing, Betfair's `runnerName` conventionally prefixes the
  **saddlecloth/runner number** ("2. Heart N Power").

**Why they diverge:** `idx+1` follows the market-book array order;
Betfair's embedded number follows the saddlecloth number. They disagree
whenever the prices array is not saddlecloth-sorted — most visibly after a
**scratching** shifts array positions, or when book order ≠ cloth order.
A separate Betfair ordering field, `sort_priority`, exists on the
catalogue (`market_catalogue.py:50, 92`) but the UI uses neither it nor
the embedded number for the rendered index.

**Canonical key for downstream historical analysis — recommendation:**
**`selection_id`** (the Betfair selection id) is the stable, canonical
join key, and it is already what bet records key on — both the log path
and the lay path send `betfair_selection_id` / `selection_id`
(`LogBetPanel.tsx:201`, `HedgeModal.tsx:282`), persisted as Set-B
DR-032 reference. Trade-offs:
- `selection_id` — globally stable, immune to scratchings/array reorder,
  already the bet-record key. **Use this as the join key.**
- saddlecloth number (parsed from `runner_name`) or `sort_priority` —
  human-meaningful and Betfair-canonical, fine as a **display/label**, but
  **not** a join key (cloth numbers repeat across races; `sort_priority`
  can shift).
- `idx+1` — **must never be used as a key**: it is array position, unstable
  across scratchings and poll updates.

So the financial/keying risk is low: **mis-reading the on-screen number is
an operator hazard, not a data-key hazard** — the bet is keyed on
`selection_id` regardless of what number is shown.

**Fix touch-list (collapse to one number):** `OddsTable.tsx:226-229` only
(drop `idx+1`, or render the saddlecloth number parsed from `runner_name`
/ `sort_priority`). **Display-only · frontend-only** — does not reach the
bet-record key.

---

## Q4 — What base price is TREND % calculated on? (§9)

**Base:** the **first (oldest) `best_back` sample still inside the rolling
window** — `trendFor` (`usePriceMemory.ts:54-77`):
`pctChange = (lastBack − firstBack) / firstBack × 100`, `firstBack =
samples[0].bestBack`, `lastBack = samples[last].bestBack`. It is **not**
the opening price, **not** BSP, **not** the previous tick.

**Window / memory model:** samples accumulate from the ~1 s price poll and
are **pruned to the window on every tick** (`usePriceMemory.ts:125-141`),
so the base is a **sliding** "earliest price within the last N minutes."
Window default **5 min**, tunable via `localStorage` key
`RACING_PRICE_WINDOW_MS` (min 30 s; `loadWindowMs`, 34-44). Consequence:
after the window fills, the `%` is measured against a ~5-min-ago price that
keeps advancing — it is **not** anchored to session/market open. Direction
arrow thresholds are ±0.5% (75-77); a `$$` matched-spike flag fires on a
>25%-or-$1k volume jump (82-89).

**Survival across race switch / reload:** memory resets on **market
change** (`useEffect`, 117-123) and **survives a runner switch within the
same race** (keyed on `marketId` only) — intended per the §5.9 comment. It
is **not persisted** (`useRef` + `useState`), so a **page reload clears
it**; TREND shows `·` until ≥2 samples re-accumulate (`trendFor`, 58-66).
This is consistent with an "in-session" design but means TREND is blank for
the first few seconds after any reload (note, not a defect).

---

## §10 — Impact maps: the three frontend pre-cutover fixes

### (a) Filters clear each other

**The described bug does not reproduce in current code (Finding F3).** The
T/H/G filters live in **`RaceListSidebar.tsx`** (not `Racing.tsx` as the
brief states). `toggleCode` (`RaceListSidebar.tsx:89-98`) already toggles
**only the clicked code** (delete-if-present / add-if-absent) with a
floor-of-one guard. Clicking one of three active filters removes just that
one; the other two remain. There is no code path that clears the
unclicked filters.

- **Blast radius:** `codes` (state, 72-74) feeds the races query key (78)
  and `enabled` (83). Purely local.
- **Touch-list:** `RaceListSidebar.tsx:72-98`. **Frontend-only.**
- **Action for next session:** re-verify against the *running* build — the
  defect may already be fixed, or the operator may have observed a
  different control. Brief a fix only if it still reproduces live.

### (b) SOFT ODDS pre-filled with BF back

**Where set (frontend default, not server-driven):** `OddsTable.tsx:196`
`const soft = manualOdds[id] ?? back ?? 0`, surfaced in the input as
`soft || ''` (254); mirrored for the panel/modal in
`Racing.tsx:123-127` (`softOddsForSelected`).

**Who reads soft odds (so a blank default doesn't silently break a calc):**
- Raw EV / Promo EV columns (`OddsTable.tsx:197-216`) — already guarded
  (`back ?` and `soft > 1`); blank → EV renders `–`, not a wrong number. ✔
- Log panel `initialSoftOdds` → snapshot (`Racing.tsx:241-243`,
  `LogBetPanel.tsx:95`); `canSubmit` blocks on `soft ≤ 1`
  (`LogBetPanel.tsx:169`). Blank is safe (submit refused until typed). ✔
- Hedge modal `bookOdds` (`Racing.tsx:260`); blank → `laySize = null`
  until set (`HedgeModal.tsx:193-201`). Safe (no placement). ✔
- Stepper fallback uses `snapSoft(soft || back || 1.5)` (`OddsTable.tsx:244,
  270`) — keep this `|| back` so stepping still works from a blank cell.

So blanking the default is **behaviour-safe** (downstream guards exist) but
**not behaviour-neutral**: EV columns and hedge book-odds go blank until
the operator types. No silent miscalculation.
- **Touch-list:** `OddsTable.tsx:196` (+ input `value` 254),
  `Racing.tsx:123-127`. `ev/softOddsLadder.ts` unaffected. **Frontend-only.**

### (c) Log-bet clear + odds carry-over

**State map:**
- Lifted to `Racing.tsx`: `selectedRunner`, `manualOdds`, `selectedMarket`.
- Local to `LogBetPanel.tsx:78-88`: `accountId`, `bookId`, `stake`,
  `softOdds`, `isFreeBet`, `selectedFb`, `snapshot`, `idempotencyKey`.

**What resets, what doesn't:**
- On **race switch**, `Racing.tsx:89-95` clears `manualOdds` and
  `selectedRunner`. ✔
- But `LogBetPanel` only resyncs on **`selectedRunner.selection_id`
  change** (`LogBetPanel.tsx:92-100`), and that effect is guarded by
  `if (selectedRunner)`. On a race switch `selectedRunner → null`, so the
  guard is false and **`softOdds` / `snapshot` are not cleared** — they
  persist into the new race until a runner is picked there. **This is the
  observed carry-over.**
- `stake` is **never reset on runner change at all** (the effect sets
  `softOdds` + `snapshot`, not `stake`); it only clears on successful
  submit (217) or FB-toggle-off (312-315). So stake carries across both
  runner and race switches.
- There is **no clear control** anywhere in the panel.

- **Touch-list:** `LogBetPanel.tsx` (local state 78-88; reset effect
  92-100 — extend to key on the `marketId` prop and to include `stake`;
  add a clear handler) + `Racing.tsx:89-95` (already resets the lifted
  state). **Frontend form-state only — no backend reach** (clearing/reset
  is pure UI; the `POST /racing/bets` contract is untouched).

---

## §11 — Launcher lifecycle + backend idle/shutdown risk

Files read: `BetHub.command`, `ui/api/main.py`,
`clients/betfair_client/v1/_auth_betfair.py`, `streaming.py`,
`_stream_transport.py`, `dependencies/composition.py`, `_audit.py`.

### (a) Close-pattern lifecycle map — **risk: informational**

| Pattern | uvicorn | Betfair auth session | Streaming connection |
|---|---|---|---|
| (i) both open | running | token cached, refresh at 3 h (`_auth_betfair.py:32`) | socket up, inbound heartbeat 5 s; reads request-driven (1 s poll) |
| (ii) browser closed, terminal open | **keeps running** | persists/refreshes lazily | **keeps running autonomously** (background task) — see (b) |
| (iii) browser + terminal closed | SIGHUP→trap→SIGTERM→stop | abandoned (no logout) | torn down cleanly via lifespan (see (e)) |

Terminal close → `trap '_shutdown 0' INT TERM HUP` (`BetHub.command:55`) →
`kill -TERM` to the process group (`set -m`, line 80) → uvicorn lifespan
shutdown → 3 s grace then `kill -9` fallback (33-37) → port freed.

### (b) Idle-backend behaviour — the throttle question — **risk: LOW**

- **Auth provider:** **no background timer.** `session_token()` is purely
  on-demand (`_auth_betfair.py:125-182`); nothing schedules a refresh.
- **Streaming transport:** **yes, one autonomous `asyncio` task** —
  `run()` (`_stream_transport.py:320-345`), started by the lifespan hook
  (`main.py:62`) and running until `stop_streaming`, **independent of the
  UI.** Behaviour with the browser closed:
  - one persistent socket; **inbound** heartbeats every 5 s
    (`HEARTBEAT_MS`, `_stream_transport.py:86`); **outbound** traffic only
    on (re)connect / auth / subscribe.
  - on a drop → reconnect with back-off **1/2/4/8/16/30 s capped**
    (`_next_backoff_delay`, 608-618) — i.e. ≤ one connection attempt per
    30 s in sustained failure, deliberately below Betfair's connection-rate
    ceiling (`streaming.py:73-77`).
  - each (re)connect's auth send calls `session_token()`
    (`_stream_transport.py:514`) — **cached**, so it does **not** trigger a
    REST login unless the token has aged out (3 h) or an INVALID_SESSION
    forced one re-login (466-497, one per episode).
- **No scheduled REST polling loop.** `live_pricing` prefers the streaming
  cache and falls through to one-shot REST only on a request
  (`streaming.py:14-19`); browser closed → no requests → no REST market
  reads.

**So:** with the browser closed the backend is **not** silent — the
streaming task keeps a single socket alive and will autonomously reconnect
on drops — **but** the traffic is bounded (one socket, reconnect ≤ 30 s,
login cached 3 h + throttled). No unbounded polling, no idle REST-login
storm. **This is the safe shape the operator was hoping for**, with the
one caveat in (d).

### (c) Multiple-server / orphan risk — **risk: LOW (same-port) / MEDIUM (port override)**

- Pinned port 8787; stale-port `kill -9` before start
  (`BetHub.command:59-64`); `set -m` process group; shutdown reaps the
  group + only the PIDs it recorded post-healthcheck (`OWNED_PORT_PIDS`,
  39-44, 105) and explicitly **will not kill a newer BetHub** (45-49).
  Same-port relaunch SIGKILLs the **old** uvicorn → OS closes its sockets →
  old Betfair stream/session dropped; **no orphan still connected.** ✔
- **`BETHUB_LAUNCH_PORT` override (line 16):** a second instance on a
  different port runs a **second uvicorn → second streaming socket +
  second auth provider → two concurrent Betfair sessions/streams in
  parallel** (two order subscriptions, double login). The single-port pin
  guarantees one server *per port*, not one server total. **Flag this** as
  the one path to two concurrent Betfair clients.

### (d) Throttle-state persistence — the lockout question — **risk: MEDIUM–HIGH**

- The escalating login throttle (cool-off 30 m→1 h→2 h→4 h, hard-kill at 5
  consecutive failures) is **in-memory instance state** on
  `BetfairAuthProvider` — `_consecutive_failures`, `_next_attempt_at`,
  `_killed` (`_auth_betfair.py:118-120`). **Not persisted.**
- **Within a process the protection is solid:** the cool-off gate raises
  **without** calling `_login()` (no network) for the duration of the
  window (`_auth_betfair.py:158-169`), so only **one real login network
  attempt fires per cool-off window** even though the streaming supervisor
  keeps retrying every ≤30 s.
- **Across restarts it resets to zero.** A fresh provider clears all
  throttle state — the code says so explicitly (*"only a fresh provider
  (v3 restart) clears it"*, comment 54-56). So **rapid relaunching DOES
  defeat the back-off**: each restart permits one immediate login attempt
  (streaming auth, plus any REST read). Repeated force-quit/relaunch during
  a Betfair outage **reproduces the request pattern that caused the ~48 h
  v2 lockout.** State plainly: it is *"re-hammer if you keep relaunching"*
  (≈1 attempt per relaunch), not an automatic tight loop — but the path is
  real and undefended across process boundaries.
- Secondary: v2's dedicated **TEMPORARY_BAN** backoff was **not ported**
  (`_auth_betfair.py:14-15, 239-246`); a ban now flows through the generic
  30 m first-failure cool-off instead. Roughly equivalent first step, but
  the explicit ban handling is gone.

### (e) Shutdown cleanliness + data risk — **risk: NONE (WAL) / MEDIUM (audit + place-then-commit)**

- **Clean stop (SIGTERM trap):** lifespan `finally` → `stop_streaming` →
  `transport.stop()` cancels the task, closes the writer, marks the client
  disconnected (`main.py:104-111`, `_stream_transport.py:282-297`). The
  **socket is torn down cleanly.** However there is **no Betfair REST
  logout** — the session token is simply abandoned and expires on its own
  (~token max age); `keepAlive` scheduling is a self-named finding
  (`_stream_transport.py:475`). Not a request-limit problem in practice,
  worth noting.
- **Abrupt `kill -9`** (stale-port clear line 62; trap fallback line 37):
  lifespan `finally` does **not** run → no graceful socket close (the OS
  closes the TCP socket on process death; Betfair sees a peer disconnect —
  fine).
- **Data risk:**
  - **SQLite/WAL — NONE.** Bet rows are written synchronously in-request
    before the response returns (`racing.py:1102-1103`, and `log_bet`
    913-947). WAL is crash-safe: committed txns are durable, an in-flight
    txn rolls back on next open, no corruption. Nothing relies on a
    graceful flush. **Confirmed safe.**
  - **In-memory audit sink — MEDIUM (known gap).** Production wires a
    **singleton `MemoryAuditLogSink`** even in live mode
    (`composition.py:529-534`) — memory-only, never written to disk, so
    **every placement audit entry is lost on any process exit** (clean or
    kill). A durable `StdoutAuditLogSink` exists (`_audit.py:97-104`) but
    is not wired. (Per brief §16: surfaced + risk-graded only; the
    durability **fix stays parked**.)
  - **Kill between place and commit — MEDIUM.** `place_lay` places on
    Betfair **first** (`racing.py:1025`) then writes the local row
    (1102). A `kill -9` in the sub-second between Betfair's ack and the DB
    commit leaves a **real-money lay live on Betfair with no local
    record**, and the audit entry that would have captured the attempt is
    in-memory → also lost. Narrow window, but the consequence (an
    unrecorded live bet) is material, and it compounds with the in-memory
    audit sink above. (The existing `LAY_LOG_WRITE_FAILED` path,
    1104-1121, covers a *failed* write but not a *killed* process.)

### (f) Terminal accumulation — cause + lightest fix (map only) — **risk: NONE (cosmetic)**

- **Cause:** the trap deliberately exits **0** on a clean stop
  (`BetHub.command:52-56`) so a tidy Terminal *can* auto-close — but
  whether it does depends on the **Terminal.app profile setting "When the
  shell exits"** (default: *Don't close the window*). On a non-zero exit
  (a real failure) the window is intentionally kept so the error stays
  visible. Windows pile up because the profile isn't set to
  close-on-clean-exit (plus failure windows persist by design).
- **Lightest fix (map only):** set the Terminal.app profile **"Shell →
  When the shell exits → Close if the shell exited cleanly."** This is a
  pure Terminal.app preference — **touches no code** and goes nowhere near
  the shutdown/port logic. (An `osascript` window-close on clean exit is
  the alternative but edits the script and is heavier.)

### §11 overall verdict

Mostly the clean shape the operator wanted: REST is request-driven, WAL is
crash-safe, the socket tears down cleanly on a graceful stop, and same-port
relaunch leaves no orphan. **Three risks to carry into fix-scoping:**
(d) cross-restart throttle reset (re-hammer path — the closest thing to the
v2 lockout), (e) in-memory audit sink + the narrow place-then-commit loss
window, and (c) the `BETHUB_LAUNCH_PORT` parallel-session path. The
autonomous streaming reconnect (b) is by design and rate-bounded — not a
throttle risk on its own.

---

## Findings (consolidated)

| # | Severity | Finding | Evidence |
|---|---|---|---|
| **F1** | **HIGH** | Bonus-Winnings Promo EV silently collapses to raw EV — UI passes `return_pct`, engine reads `bonus_pct`/`basis` which the config never sets. | `evEngine.ts:362-393` vs `OddsTable.tsx:205-212`, `Racing.tsx:150-154`; grep |
| **F2** | MEDIUM | Hedge modal advertises "v2 FB conversion 70% applied" but `FB_CONVERSION` is used only in the label, not in the lay math (math is correct without it). | `HedgeModal.tsx:18, 347-348, 193-210` |
| F3 | LOW | §10a filter bug does not reproduce; `toggleCode` already toggles only the clicked code; filters live in `RaceListSidebar.tsx`, not `Racing.tsx`. Re-verify live. | `RaceListSidebar.tsx:89-98` |
| F4 | LOW | `0.7` FB-conversion hard-coded in 3 places, not UI-configurable. | `evEngine.ts:41, 541`; `HedgeModal.tsx:18` |
| F5 | INFO | Insurance EV models a single qualifying bet + refund (FB@70%), not the full lay-off / free-bet-deployment cycle — confirm against the operator's whole-cycle definition. | `evEngine.ts:309-338` |
| F6 | LOW | Table EV and logged-snapshot EV normalise over different active-runner sets (`≠REMOVED∧≠WITHDRAWN` vs `===ACTIVE`). | `OddsTable.tsx:102-108` vs `Racing.tsx:104-106` |
| F7 | LOW | Log-panel `stake` never resets on runner/race switch; `softOdds` carries over on race switch (effect guarded by `if(selectedRunner)`). | `LogBetPanel.tsx:92-100` |
| F8 | MEDIUM | Production wires a memory-only singleton audit sink in live mode → all placement audit entries lost on any exit (durable `StdoutAuditLogSink` exists, unwired). | `composition.py:529-534`; `_audit.py:97-104` |
| F9 | MED-HIGH | Login-throttle state is in-memory; a process restart resets it → rapid relaunch can defeat the back-off (the v2-lockout re-hammer path). | `_auth_betfair.py:118-120, 54-56` |
| F10 | MEDIUM | `BETHUB_LAUNCH_PORT` allows a second instance → two concurrent Betfair sessions/streams. | `BetHub.command:16` |
| F11 | LOW | `kill -9` between Betfair placement and DB commit → unrecorded live lay (compounds F8). | `racing.py:1025, 1102` |
| F12 | INFO | `calculateLayFieldProbabilities` is dead code; v2 TEMPORARY_BAN backoff not ported; no Betfair logout on shutdown. | `evEngine.ts:256`; `_auth_betfair.py:239-246`; `main.py:104-111` |

**Pre-cutover-critical candidates** (operator's call): **F1** (bets placed
off wrong bonus-winnings EV) and **F9** (Betfair lockout re-hammer). F8/F11
(audit/data durability) are MEDIUM but the durability fix is parked per
brief §16.

---

## Touch-list summary (for fast bucketing)

| Item | Touch-list | Reach |
|---|---|---|
| Q3 collapse runner number | `OddsTable.tsx:226-229` | **frontend-only** |
| §10a filters | `RaceListSidebar.tsx:72-98` (verify first) | **frontend-only** |
| §10b SOFT ODDS blank default | `OddsTable.tsx:196,254`; `Racing.tsx:123-127` | **frontend-only** |
| §10c clear + carry-over | `LogBetPanel.tsx:78-100`; `Racing.tsx:89-95` | **frontend-only** |
| F1 bonus-winnings EV (if briefed) | `OddsTable.tsx:205-212`, `Racing.tsx:150-154` (pass `bonus_pct`/`basis`) or `presets.ts` config shape | **frontend-only** |
| Q2 add back-bet (out of scope) | `HedgeModal.tsx`, `api/racing.ts`, `racing.py:place_lay`, `record_builder` | **reaches backend** |

---

## Self-assessment

- **Coverage:** all four verify questions (Q1–Q4) answered with `file:line`
  evidence; all three §10 impact maps produced with touch-lists + reach
  tags; §11 (a)–(f) each answered and risk-graded; Q3 canonical-key
  recommendation given.
- **Confidence:** high on F1 (grep-confirmed the config never sets
  `bonus_pct`), the Q2 formulas (byte-matched to `evEngine`), Q4, and the
  §11 lifecycle/throttle/WAL reads. Medium on the exact AU-racing semantics
  of the Betfair `runner_name` prefix in Q3 — the *mechanism* (idx+1 +
  embedded Betfair number) is certain from the code; the claim that the
  embedded number is specifically the saddlecloth is from AU-racing
  convention, not a live data sample (no network/DB read was needed to
  establish the provenance).
- **Tests:** `uv run pytest` was **not** run. Every finding is grounded in
  source; the suite would not change a verdict, and F1 specifically is
  *masked* by the unit test (which passes `bonus_pct` directly), so a green
  suite would not surface it. Running it was judged unnecessary spend for a
  bounded session.
- **Scope discipline:** read-only throughout; no source/test/git changes;
  `placement.py` not modified; working tree unchanged (62 dirty entries at
  open and close). Out-of-scope items (back-bet build, layout/sparkline
  redesign, hot buttons, durability fix) mapped where the brief asked,
  built nowhere.
- **Length:** ~430 lines — within the 300–550 target; no padding.
- **Surprises surfaced as findings, not chased:** F3 (filter bug absent),
  F8 (singleton memory audit sink), F2 (decorative 70% label), F10
  (`BETHUB_LAUNCH_PORT`).

*End of report.*
