# 0y build plan — race-page TAB refresh on race selection (S263, plan only)

**Status: PLAN ONLY — no code changed. Adversarial review next, build after
the International Phase 1 capture deploy settles (§6).**

**Operator complaint (1 Aug race day, worklist 0y):** selecting a new race
leaves TAB odds stale "up to a minute (at times more)". Wanted: every race
selection fires an immediate TAB refresh for that race — freshest odds
possible at decision time.

**For the operator (short version):** when you click a new race, the fast
TAB feed for the race you just LEFT keeps hogging both of our two polite
TAB lines for up to 45 seconds, and on Saturday the promo-pilot page was
also holding those same lines for its own races. Until your new race wins
a turn, the screen shows the slow background copy — which can genuinely be
one to five minutes old. The fix makes the race you clicked FIRST IN LINE
for the very next turn on those lines, retires the old race's feed within
seconds instead of 45, and — when TAB simply hasn't priced a race yet —
says so instead of showing nothing. It sends **no extra requests to TAB at
all** (same two lines, same ~7-second politeness rhythm TAB's own site
uses), so there is no new block risk and no proxy-cost change. Expected on
screen: fresh TAB odds ~2–4 seconds after clicking a race (worst case ~9),
instead of up to a minute-plus. Confidence: HIGH on the cause (read
directly from the code and the S257 measurements), MEDIUM-HIGH that the
worst sightings included promo-pilot contention (it polls the same fast
lane and ran that day; one log pull on build day will confirm).

---

## 1. Mechanism findings — where the switch-to staleness actually comes from

### The current path, end to end

1. **Rail click** → `Racing.tsx` `setSelectedMarket(m)` (line ~1116).
2. The live TAB query re-keys on the new market id
   (`queryKey ['racing','tab-live-odds', market_id]`, `staleTime: 0`) and —
   contrary to first suspicion — **does fire an immediate request** at
   `/api/v1/racing/markets/{id}/live-soft-odds` (v3 backend, thin adapter,
   `ui/api/routers/racing.py` ~line 824) → 8400 tunnel
   (`clients/vps_client/v1/live_soft_odds.py`, 5s connect / 10s read) →
   capture API `api/routes/live_soft_odds.py`.
3. Capture side: a market with no running refresher takes the **inline
   path** — resolve fragments, then `_claim_pool()` must win one of the two
   dedicated live Decodo sessions (`live` / `live-b`), each under the
   global **7s per-session floor** (S257 claim registry; the anti-scanner
   politeness rhythm — load-bearing).
4. If no session is claimable → **503 `live_pools_hot`**. The v3 tool has
   `retry: false`, so the query sits in error until its next interval tick
   — **1s / 5s / 15s** depending on the NEW race's distance to jump.
5. Until a live payload lands, the Soft Odds column shows the **background
   store snapshot** (`/soft-odds`), whose true age is honest
   (`bs.snapshot_time`) but whose cadence is **300s standard / 105s
   intensive** (`config/settings.py`: `STANDARD_POLL_INTERVAL`,
   `BOOKIE_INTENSIVE_POLL_INTERVAL`). The staleness banner does mark it
   (90s live-window threshold + live-query-error marking) — the numbers are
   honestly labelled, but they are still old numbers.

### The four contention sources that delay the first live fetch

**(a) The previous race's refresher lingers 45s and saturates the supply.**
`_IDLE_STOP_S = 45.0`: after a switch, the OLD race's refresher keeps
fetching at its last inferred cadence. In the final window that is
`_POLL_FINAL_S = 3.5s` across two pools — i.e. **exactly 100% of the claim
supply** (2 claims per 7s). Its 0.25s wake quantum claims each pool within
~0.25s of its floor expiring; the new race's UI-tick inline requests lose
almost every race for that pool. `_claim_pool` is fair/LRU — **the
selected race has no precedence over a dying refresher.**

**(b) NEW finding — the promo-pilot shares the same fast lane.**
`~/Desktop/Projects/promo-pilot/app.py` polls
`/api/v1/racing/markets/{id}/live-soft-odds` every **10s for EVERY promo
race inside T-30min** (`NEAR_POLL_S = 10`, `NEAR_WINDOW_MIN = 30`), via
the same v3 endpoint → same capture route → same two live pools → same
claim registry → same refresher registry. Saturday 1 Aug — the pilot's
first live day — is exactly the day of the complaint. Each pilot race
holds a refresher (10s touches → idle tier, one fetch/30s each: modest
claims, ~35% of supply at 3 races) **and a registry slot**.

**(c) The refresher registry has 3 slots and denies silently.**
`_MAX_REFRESHERS = 3`. Old-race refresher + two or three pilot races fill
it; the newly selected race then **cannot register a refresher at all**
(no eviction, no error) and runs cache-less inline fetches only — each one
a claim-race it usually loses while (a) persists.

**(d) Retry pacing amplifies every miss.** `retry: false` + interval tiers
mean a far-out race (>30min) re-asks only every **15s**; two hot-503s in a
row ≈ 30–45s before the first success even after supply frees.

### The resulting arithmetic (matches the complaint)

Typical mid-meeting switch: 5–45s of claim contention before the first
live fetch + a background snapshot aged 0–105s (intensive) or 0–300s
(standard) displayed meanwhile → perceived staleness routinely ~1 min,
"at times more" when the registry was full (race day, pilot running) or
the new race was far out (15s tier). Best case (quiet pools, warm pin)
is ~1.5s — which is why it doesn't ALWAYS happen.

**What is NOT the cause:** TAB's own ~15–40s anti-scanner publish delay is
a floor everyone shares (S257) but it is constant, not switch-correlated.
The transport itself never faltered on the measured day (S257: 22/22
serves). The v3 tunnel adapter adds no cache and no delay.

---

## 2. Design — selection priority, not more traffic

Principle: **do not add a single TAB request path.** The two live pools and
the 7s per-session floor stay exactly as S257 built them; the fix is
*re-ordering who gets the next turn* plus *retiring dead claimants faster*.
TAB-side request volume is bounded by the unchanged claim registry: ≤ 2
fetches per 7s globally, no matter what the UI does. That invariant is the
rapid-switching bound, and it already exists — every change below sits
inside it.

### 2.1 The selection signal — a `priority=selected` flag on the existing GET

No new endpoint, no second request per switch. The race page's live query
adds `?priority=selected` to the GET it already fires on selection
(`fetchTabLiveOdds`); the v3 router and vps_client pass it through; the
capture route treats a flagged request as "the operator is LOOKING at this
market now". The promo-pilot (unchanged, no flag) can never steal focus.
Rejected alternative: a separate `POST /live-focus` nudge — a second
request per switch, a second code path, and nothing the flag doesn't do.

Capture-side state: a single **focused market** (size-1, latest wins) with
a TTL (~20s, refreshed by each flagged request — i.e. focus follows the
UI's own polling and expires when the page goes quiet or moves on).

### 2.2 Focus-priority claims — ordering, never floor-breaking

`_claim_pool(now, market_id)` gains the rule: **when the focused market
has a fetch due** (flagged inline request waiting, or the focused
refresher's cadence elapsed), claims from other markets are denied for
that turn (they take the existing `live_pools_hot` roll-back path, which
`_refresh_once` already handles gracefully). Otherwise claims flow LRU as
today. Effects:

- On switch, the very next session to cross its 7s floor goes to the
  selected race → first fresh row within **0–7s** (typically ~2–4s, since
  the two pools' floors are staggered ~3.5s apart in the final window).
- Non-focused starvation is bounded: at most one focused fetch per focused
  cadence; in the focused race's final 5 minutes the focused feed consumes
  the full supply (1/3.5s = 2/7s) and pilot watchers ride their background
  fallback — accepted and stated (two polite sessions cannot serve two
  final-window races; the operator's decision screen wins). Outside the
  final window the focused race uses ≤ half the supply and the pilot is
  unaffected.
- The floor is NEVER shortened; a benched (blocked) session stays benched
  — focus cannot override transport health.

### 2.3 Fast-retire dead refreshers

Retire a refresher when its UI-touch age exceeds ~3× its inferred poll
tier, floored at 10s: final tier (1s polls) → retire at ~10s (was 45);
early tier (5s) → ~15s; idle tier (10–15s polls, incl. the pilot's) →
45s unchanged. Kills contention source (a) at the root and frees registry
slots in seconds. A wrongly-retired refresher (UI hiccup) costs one cheap
re-registration on the next poll.

### 2.4 Focused registration always succeeds

A flagged request for a market with no refresher registers one even when
the first build fails `live_pools_hot` (today registration happens only
after a successful build), evicting the stalest-touch NON-focused
refresher if the registry is full. `_MAX_REFRESHERS = 3` stays. Fixes (c);
the focused race always ends up with the cache + its own clock.

### 2.5 In-flight dedupe per market

A per-market latch: while an inline build for market X is in flight,
concurrent requests for X serve `_latest` (any age) or fail fast — never a
second concurrent build (today the claim floor happens to dedupe, but a
slow cold hunt can still stack API threads behind one market). Bounds
rapid same-race polling to one build at a time.

### 2.6 v3-side bounded retry burst (fixes (d))

`tabLiveQuery` changes `retry: false` → retry only 503-unavailable errors,
**max 3 attempts, ~2s apart**, then settle back to the interval tier.
These retries are tunnel reads (v3 → capture API cache), NOT TAB fetches —
the claim registry still owns all real TAB traffic. Worst-case
switch→fresh-display: ~7s floor + ≤2s retry gap ≈ **≤9s**; typical ~2–4s.
No UI debounce is added: a rail hop already costs one tunnel GET, focus is
size-1 latest-wins, and the claim floor makes TAB volume switch-count-
independent — a debounce would only delay the signal the feature exists to
send.

### 2.7 Honest "TAB hasn't priced this race yet"

The capture route's 200-empty today conflates three causes. Add an
additive `reason` field: `race_not_on_tab` (fresh 404 or the remembered
`_not_on_tab_until` answer) | `no_tab_identifiers` | `no_joined_runners`.
v3 passes it through (optional field — older VPS omits it harmlessly);
`Racing.tsx` shows a small note in the Soft Odds header — "TAB hasn't
priced this race yet" — when live says `race_not_on_tab` and the
background feed has no TAB prices either. Stale-but-real background
numbers keep showing with the EXISTING stale marking (90s/2min thresholds,
S257 measure 3) — no new blocking, no hidden data
(friction-vs-safeguards standing rule).

### Request-volume + budget delta (explicit)

- **TAB requests: zero added — slightly NEGATIVE overall.** Same two live
  sessions, same 7s floors, same global claim registry; fast-retire stops
  up-to-45s of fetches for races nobody is watching. No new pools, no new
  fingerprints, no cadence changes. Collector (`collector`) and morning
  sweep (`morning`) pools untouched.
- **Decodo: no new sessions, no plan change** (S257's "bigger subscription
  buys nothing" stands).
- **Tunnel/v3 API: + ≤3 retry GETs per switch for ~6s** (few KB each) and
  one query-param on existing GETs. Trivial.

---

## 3. Changes by repo, file level

### Capture side (`racing-data-capture` — build on POST-deploy master, §6)

All changes live in **one file plus its tests**; the transport is not
touched.

- `api/routes/live_soft_odds.py` — the whole feature:
  - focus state (`_focused_market: (market_id, deadline)`, guarded by the
    existing `_pool_lock`), set/refreshed by `priority=selected` requests;
  - `_claim_pool(now, market_id)` focus-ordering rule (§2.2) — deny turns
    to non-focused claimants only while a focused fetch is due;
  - fast-retire in `_Refresher.run()` (§2.3: idle threshold from the
    inferred tier instead of flat `_IDLE_STOP_S`);
  - focused registration-before-success + stalest-non-focused eviction
    (§2.4) in the route body;
  - per-market in-flight latch (§2.5);
  - `reason` on empty responses (§2.7), including the remembered-404
    answers; `LiveSoftOddsResponse` gains the optional field;
  - route signature: `priority: str | None = None` query param.
- `tests/test_live_soft_odds_route.py` — new cases (§5). Existing 404-
  memory / benching / claim-floor tests must stay green unmodified.
- **NOT touched:** `bookmakers/tab.py` (Safari/Decodo-AU/hunt-and-pin/
  breaker — LOAD-BEARING, S245/S247/S248), collector/orchestrator,
  `config/settings.py` cadences, liveness/coverage
  (`scripts/liveness_check.py` reads collector snapshots + heartbeat in
  `capture.db`; the live lane writes only the side DB
  `data/tab_live_log.db` via `api/live_fetch_log.py`, so the new fetch
  pattern is INVISIBLE to liveness/coverage by construction — the standing
  rule is satisfied by not creating a new write path at all),
  `api/routes/soft_odds.py`, morning sweep.

### v3 side (`bethub-v3`)

- `ui/web/src/api/racing.ts` — `fetchTabLiveOdds(marketId)` sends
  `?priority=selected` (the race page is the only selected-race caller).
- `ui/api/routers/racing.py` — pass the param through the adapter;
  forward `reason` (additive dict field, no envelope change).
- `clients/vps_client/v1/live_soft_odds.py` — optional `priority`
  argument on `tab_live_soft_odds`; optional `reason` on the model.
- `ui/web/src/routes/Racing.tsx` — retry burst on `tabLiveQuery` (§2.6);
  the "TAB hasn't priced this race yet" note off `reason` (§2.7). The
  seed/merge/edit-protection machinery (`operatorTouchedRef`,
  fresher-wins merge) is NOT touched.
- Tests: router + vps_client + `Racing.tablive` additions (§5).
- promo-pilot: **no change** (it simply never sends the flag). Do not
  edit that repo in this build.

---

## 4. Failure modes and how the design behaves

- **TAB 404 — race not served (overseas cards, non-TAB meetings):**
  unchanged path — `TabRaceNotFound` never burns a hunt or a bench
  (S250 `caffb78`), the per-market `_not_on_tab_until` memory answers
  empties for 120s without consuming claims; focus on such a market
  expires by TTL and, because its inline path returns before claiming,
  it never blocks other claimants. NEW: the empty now says WHY (§2.7).
- **Transport block mid-burst:** the blocked session is benched 900s and
  the rotation leans on the healthy one (S257 measure 6) — focus does not
  and must not unbench; with one healthy session the focused race gets
  every second turn (~7s cadence); with both benched the existing
  `live_tab_unavailable` 503 → the tool's background fallback + stale
  marking, and the v3 retry burst caps at 3 (no hammering the tunnel
  during an outage; interval ticks resume as today). The S248 shared hunt
  breaker semantics are untouched.
- **Collector collision:** none by construction — the nudge rides the
  existing `live`/`live-b` pools; the collector's own TAB snapshots run on
  its separate pinned `collector` session ("TAB on its OWN session pool",
  morning-sweep brief) and the only shared machinery, the hunt breaker,
  is unchanged. No change to snapshot cadence or the capture write path.
- **Pilot starvation in the focused race's final window:** accepted and
  bounded (§2.2). The pilot's page already degrades to the background feed
  by design ("use only near jump", its own runbook). If the pilot
  graduates to a standing tool, a THIRD live pool is the future answer —
  deliberately NOT in 0y (it would be the first real TAB-volume increase
  and deserves its own risk look).
- **Rapid switching (the bound):** N switches in any window produce ≤ 2
  real TAB fetches per 7s (claim-floor invariant, unchanged), ≤1 in-flight
  build per market (latch), focus size-1 latest-wins, ≤3 tunnel retries
  per switch. Proven red-green by the bound test (§5).
- **Refresher thrash from eviction:** eviction only targets non-focused,
  stalest-touch refreshers; a still-polled pilot market re-registers on
  its next 10s poll (cheap: one registration, its first fetch still
  claim-gated). Thread count stays ≤ `_MAX_REFRESHERS`.
- **VPS restart / deploy:** all new state is process-local (like the
  existing registries) — a `racing-api` restart drops it and the first
  flagged request rebuilds it; restart outside a race window as usual.
- **Multi-worker uvicorn would split the registries** (true TODAY for the
  S257 claim floor too): build-day check `systemctl cat racing-api`
  confirms single-worker before relying on it; if it ever isn't, stop and
  flag (pre-existing S257 assumption, not a 0y regression).
- **Phase 1 international races:** TAB itself lists some international
  meetings (they carry `tab_race_id`); post-deploy `race_date` semantics
  now include venue-local dates (0p commit `1b2b45e`). Build-day
  verification: the live route's `race_date` argument still matches TAB's
  card date for an international race with a `tab_race_id` (one fixture +
  one live check). If it doesn't, that is a PRE-EXISTING live-lane gap to
  flag separately — 0y must not silently widen or fix it.

---

## 5. Red-before tests

Capture side (`tests/test_live_soft_odds_route.py`, fake clock — red today
unless marked regression):

1. **Focus beats a lingering refresher:** market A's refresher saturating
   both pools at final cadence; flagged request for B arrives → the next
   floor-crossing claim goes to B; A's denied cycle rolls its clock back
   (no failure counted). Red: LRU gives A today.
2. **Fast-retire:** refresher at final tier untouched for >10s exits and
   frees its slot (idle-tier refresher at 20s does NOT). Red: flat 45s.
3. **Focused registration under a full registry:** 3 non-focused
   refreshers; flagged request registers B by evicting the stalest-touch;
   non-flagged request still refused. Red: silent denial today.
4. **Rapid-switching bound:** 10 flagged switches across distinct markets
   in a 3s burst → total `fetch_tab` calls in any rolling 7s window ≤ 2;
   focus holds only the newest market; every response is a clean shape
   (fresh, empty, or 503 — never 500). Claim-floor half is regression
   (green today); focus half red.
5. **In-flight latch:** two concurrent requests for one market run ONE
   build; the second serves `_latest` or fails fast. Red.
6. **Focus never overrides a bench:** focused market with both pools
   benched → `live_tab_unavailable` 503, benches untouched. Regression-
   shaped, red for the focus path.
7. **`reason` honesty:** fresh 404 and remembered-404 both say
   `race_not_on_tab`; missing identifiers say `no_tab_identifiers`;
   pre-existing empties keep shape (additive field only). Red.
8. **Focus TTL:** flag stops arriving → focus expires ≤20s → non-focused
   claims flow freely again. Red.

v3 side (pytest + vitest):

9. Router/vps_client pass `priority=selected` through and surface
   `reason`; omitted-by-old-VPS → None (contract tests). Red.
10. `Racing.tablive.test.tsx`: hot-503 → exactly 3 retries ~2s apart then
    settle to tier interval (mock timers); switch A→B fires an immediate
    flagged GET for B (regression: immediate GET exists; flag red); the
    "TAB hasn't priced this race yet" note renders on
    `reason=race_not_on_tab` + no background prices, absent otherwise;
    operator-typed odds survive the whole switch/retry cycle (regression).
11. Frontend rapid-switch bound: three rail hops in <2s → ≤1 immediate
    live GET per hop + ≤3 retries each, and no live GET for a market
    after navigating off it. Red (retry logic new).

Suites: capture `python -m unittest discover` green incl. existing
transport/claim tests unmodified; bethub-v3 `uv run pytest` +
`npm run build` (the typecheck gate) green; baselines from HEAD at build
time recorded in the report.

---

## 6. Effort + build timing

**Timing gate: build AFTER the International Phase 1 + resilience deploy
settles.** The capture repo is mid-deploy (pinned-SHA loop,
`scripts/deploy_phase1.py`; stack on `origin/master` up to `9d86480` plus
the local liveness commit `86a16b1`). This plan is written against that
post-deploy master — `live_soft_odds.py`'s latest substantive commits
remain `b7c282f` (S257) and `6566641` (0l), and Phase 1 did not touch the
live lane, so no rebase risk is expected; re-verify with a fresh
`git log origin/master -- api/routes/live_soft_odds.py` before the first
edit. Do NOT interleave 0y capture edits with the deploy loop: land as
normal commits on master once the loop is done and the S263 acceptance on
the deploy has passed, deploy via the established path, restart
`racing-api` between races (refreshers are process-local and rebuild on
first request).

Effort: capture side ~0.5–1 day (one file + tests; the module is small and
well-tested), v3 side ~0.5 day (param plumb + retry + note + tests),
adversarial review per standing practice, then a race-day live proof:
a deliberate switch drill (hop 3 races near a jump, note the seconds to a
moving TAB price) + one `tab_live_log.db`/journal pull to confirm the
claim ordering and — MEDIUM-confidence item — the pilot-contention share
of the 1-Aug sightings. Not a Saturday-morning deploy: land it on a quiet
day, prove it live the following race day.

---

## 7. Operator decisions

**None required.** All tuning numbers are engineering calls, decided here
with rationale, all operator-tunable later without redesign:

| Number | Value | Why |
|---|---|---|
| Focus TTL | ~20s | > the slowest live poll tier (15s) so focus follows the UI without flapping; expires within seconds of leaving the page |
| Fast-retire threshold | 3× inferred tier, min 10s | three missed UI polls = nobody is watching; keeps idle-tier (pilot) refreshers on today's 45s |
| v3 retry burst | 3 × ~2s, 503s only | covers one full 7s floor cycle; tunnel-only traffic; stops hammering during real outages |
| Per-session floor | 7s — UNCHANGED | TAB's own site rhythm; the S247/S257 anti-scanner line is not 0y's to move |
| Pool count | 2 — UNCHANGED | zero new TAB/Decodo exposure; a third pool is a future, separate call if the promo-pilot graduates |
| Empty-state wording | "TAB hasn't priced this race yet" | plain-language rule; shown only when there is genuinely nothing to show |

Flag for awareness only (no action needed): while your open race is inside
its final 5 minutes, the promo-pilot's fast TAB feed for OTHER races will
briefly ride its slower background copy — your screen wins the fast lane.

*Evidence read for this plan: `racing-data-capture/api/routes/
live_soft_odds.py` (S257 refresher/claims), `bookmakers/tab.py`
(transport, pools, breaker), `api/routes/soft_odds.py` +
`config/settings.py` (background cadences), `api/live_fetch_log.py` (side
DB), `bethub-v3/ui/web/src/routes/Racing.tsx` (queries, merge, banner),
`ui/api/routers/racing.py`, `clients/vps_client/v1/live_soft_odds.py`,
`promo-pilot/app.py` + `bethub_client.py` (shared live lane),
`tab_lag_review_s257.md`, `tab_live_refresh_build2_{brief,report}.md`,
`morning_odds_sweep_brief.md` (pool separation), capture git history to
`origin/master` @ `9d86480`.*
