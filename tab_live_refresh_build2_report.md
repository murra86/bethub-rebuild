# Build 2 report — TAB live-refresh for the active race page

**Session:** S245, 20 Jul 2026. **Executor:** background Code session.
**Status:** BUILT both sides, suites green, live endpoint **live-proven**
against real TAB; frontend fast-refresh **implemented-not-live** (needs a
watched race into the jump). No money paths touched.

---

## Grounding (done before any edit)

The store's race row **does** yield everything `fetch_tab` needs:

- `tab_race_id` carries `"<VENUE>/<race_no>"` — e.g. `WAG/8`, `PAK/10` —
  the exact `{venue_code}/{race_number}` shape `discover_tab` stamps. The
  first segment is the TAB **venue mnemonic**; split on `/`.
- `race_date` gives the fetch date (`YYYY-MM-DD`).
- `runner_number → betfair_selection_id` is the stamped join in `runners`.

So no guessing was needed. `_parse_tab_race_id()` splits `tab_race_id` and
falls back to the row's own `race_number` column if the id is odd-shaped.

---

## Capture side (VPS `racing-data-capture`, working tree, uncommitted)

Surgical edits, each modified file backed up `*.pre-s245-build2-bak`:

- **`bookmakers/tab.py` (A — transport, per-pool split, ONLY change):**
  the single module-level `_pinned_session` became `_pinned_sessions:
  dict[str, str]` keyed by pool, under one lock guarding the dict.
  `_tab_get(url, params, pool="collector")` and `fetch_tab(..., pool=
  "collector")` gained the arg; the collector keeps `"collector"`, the live
  endpoint passes `"live"`. Each pool hunts-and-pins its OWN AU IP; a block
  on one pool re-hunts only that pool. **Safari + Decodo-AU + hunt-and-pin
  logic, creds, headers, timeouts — all untouched.** Collector caller
  (`orchestrator.py`, positional `+ proxies=`) is unaffected by the new
  keyword default.

- **`api/routes/live_soft_odds.py` (B — new endpoint):**
  `GET /racing/markets/{market_id}/live-soft-odds`. Resolves the DR-034
  most-complete fragment (reusing `soft_odds.py`'s indexed correlated-
  subquery pattern — **no full scan**; extended completeness key to prefer a
  fragment carrying `tab_race_id`), reads the stamped runner→selection map
  (indexed by `race_id`), live-fetches via `fetch_tab(date, venue, n,
  pool="live")`, joins live odds→selection id by runner number, returns the
  `/soft-odds` shape **plus `source:"live"`**, `captured_at`=now.
  Degradation: unknown market → 404; no TAB ids / no joined runners → 200
  empty; `TabTransportError` or any fetch error → **clean 503, never 500**.

- **`api/main.py`:** registered the router **and** added `load_dotenv()` at
  startup (see finding below).

- **Tests:** `tests/test_tab_transport.py` rewritten to the pool model (6
  original cases + 2 new: pools pin independently; a live re-hunt leaves the
  collector pin intact). `tests/test_live_soft_odds_route.py` new (join by
  selection; unstamped/absent runners omitted; transport failure → 503 not
  500; unexpected error → 503; unknown market → 404; resolve + runner-map
  queries do **not** full-scan — EXPLAIN QUERY PLAN guard).

**Capture-side suite: 99 unittests green** (`python -m unittest discover`),
including the 15 in the three TAB/soft-odds files.

### Finding — API process didn't load `.env` (fixed)

The live endpoint fetches TAB, which needs `DECODO_*` creds from the env.
The collector loads `.env` via `python-dotenv` in its entrypoint, but the
**API (uvicorn) process did not** — so the first live calls returned an
instant (3ms) clean 503 (`fetch_tab` failing closed on missing creds). This
is *safe* (the tool just falls back to background), but the live feed would
never actually fetch. Fixed by mirroring the collector: `load_dotenv()` in
`api/main.py`. Restarted `racing-api.service`. Display/data only.

---

## S189 live-integration status

**Live endpoint — PROVEN against real TAB (today).** Restarted the API,
hit `/racing/markets/1.260136666/live-soft-odds` (Pakenham R10, 14 joined
runners, near jump):

- Cold hunt returned **HTTP 200, `source:"live"`**, runners joined to the
  same `betfair_selection_id`s as the background feed, in ~4.8s.
- Odds were genuinely fresher/moving vs the background snapshot:
  sel 100749631 `11.0 → 10.0`, sel 74901081 `7.0 → 7.5`, sel 97211330
  `2.4 → 2.4`.
- Subsequent calls **~1.1s** — the "live" pool pinned and holds, independent
  of the collector.
- The graceful path is real, not theoretical: an unlucky cold hunt returned
  a clean `503 {"reason":"live_tab_unavailable"}` (the hunt is ~1-in-several
  per the spike; a direct 12-session probe showed 3× `200 runners=14`).

**Frontend fast-refresh — implemented-not-live.** Fixture-tested (below) but
not yet watched into a real jump in the running app; that's the remaining
S189 step for the operator on a racing day.

---

## Tool side (`bethub-v3`, committed + pushed)

- **`clients/vps_client/v1/live_soft_odds.py`:** `tab_live_soft_odds`
  surface over the 8400 tunnel (DR-028 — no local `capture.db`). 200 →
  `FreshEnvelope[TabLiveSoftOdds]` (+`source`); live-blocked/5xx →
  `VPS_UNREACHABLE(retry 15s)`; 404 → `GENUINE_ABSENCE`. Exported from
  `v1/__init__.py`.
- **`ui/api/routers/racing.py`:** `GET /v1/racing/markets/{id}/live-soft-
  odds` thin adapter — terminal absence → fresh-empty (blank column);
  transport failure → 503 (tool falls back to background).
- **`ui/web/src/api/racing.ts`:** `fetchTabLiveOdds`.
- **`ui/web/src/routes/Racing.tsx`:** live poll query + merged seed effect.

### Merge / override + edit protection

One **merged** seed effect depends on BOTH feeds and recomputes desired =
`live ?? background` per selection each poll (so no flicker between them):

- a **live** value for a selection **overrides** the background value in the
  Soft Odds column;
- **live unavailable** (query disabled/failed, or that runner absent from
  the live card) → the background value stands;
- in **both** cases, any selection in `operatorTouchedRef` (the Build-1 edit
  guard) is never overwritten — the operator's typed/cleared price is
  sticky against both feeds. Scratched/unpriced entries are skipped.

### Cadence constants (named, operator-tunable — off the Decodo IP)

- `TAB_LIVE_WINDOW_MS = 30 * 60_000` — start live polling at T-30m.
- `TAB_LIVE_FINAL_WINDOW_MS = 5 * 60_000` — "final minutes" threshold.
- `TAB_LIVE_POLL_MS = 15_000` — cadence T-30m … T-5m.
- `TAB_LIVE_FINAL_POLL_MS = 8_000` — cadence inside the final 5 min.

Gate: `visible && tabOddsEnabled && msToJump>0 && msToJump<=30m`. The ~1s
prices poll re-renders continuously, so `msToJump` (gate + cadence) stays
current; the query stops on navigate-away / tab hidden / past jump.

### Tests

- vps_client surface (5): fresh-with-live-odds, Phase-E empty, 404, live-
  blocked 503 → VPS_UNREACHABLE, connect-down.
- router (3): fresh→200, genuine-absence→200-empty, VPS-unreachable→503.
- frontend (5, `Racing.tablive.test.tsx`): live overrides background; live
  unavailable → background; operator edit survives BOTH feeds; no live poll
  outside the ~30-min window; no live poll when the page is hidden.

---

## Suites

| Suite | Baseline (HEAD `8e49c97`) | After |
|---|---|---|
| bethub-v3 backend | 1522 | **1530** (+8) |
| bethub-v3 frontend | 242 | **247** (+5) |
| `npm run build` (typecheck gate) | — | **green, dist rebuilt** |
| capture-side unittest | green | **99 green** |

---

## Commits

- **bethub-v3:** `8e49c97 → 09d0897` (`S245 Build 2 (tool side): live TAB
  refresh…`, co-author trailer), **pushed** to `murra86/bethub-v3` main.
  dist is gitignored; rebuilt locally.
- **Capture side:** working tree, **uncommitted** by design; backups
  `bookmakers/tab.py.pre-s245-build2-bak`, `api/main.py.pre-s245-build2-bak`,
  `tests/test_tab_transport.py.pre-s245-build2-bak`.

## Fences honoured

Zero money-path edits/imports (racing display/data only). Proven transport
unchanged except the per-pool split. DR-028: tool reads live odds only over
the 8400 HTTP API. Two-repo discipline kept.

## Nothing stopped on

All §4 stop conditions clear: the store yields the TAB fetch ids; no money
module needed touching; the per-pool split didn't disturb the collector path
(proven by test + the collector still capturing during the live proof); the
live fetch degrades cleanly to the background feed (proven, both by the 503
path and the fixture tests). One config wiring addition (`load_dotenv()` in
the API) was required and is documented above.
