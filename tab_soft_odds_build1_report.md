# Build 1 report — TAB soft-odds auto-fill

**Session:** S245, 20 Jul 2026. **Executor:** background Code session.
**Brief:** `tab_soft_odds_build1_brief.md`. **Spike ref:**
`tab_spike_result_s245.md`.

**Outcome: shipped, all phases.** Capture side is **live-proven** end to
end (transport + enable + endpoint, real TAB odds flowing); the tool-side
capture-read client is **live-proven** through the 8400 tunnel; the
frontend auto-fill column is **implemented-not-live** (exercised only on a
real race day). No stop condition hit. No money path touched.

---

## What landed, per side

### Capture side — `racing-data-capture` (VPS, deployed, uncommitted)

Left uncommitted per the brief (that repo runs from its working tree with
in-flight work). Changes are surgical — `git status` shows only these:

- **`bookmakers/tab.py`** — replaced the `requests`-based fetch with the
  proven **`curl_cffi` `impersonate="safari"` + Decodo residential
  country-targeted-AU (`gate.decodo.com:7000`, `user-…-country-au-session-
  <sid>-sessionduration-30`) + hunt-and-pin** transport. Module-level
  pinned session under a lock; re-hunts only on a block; polite backoff
  between hunt tries. `fetch_tab` / `discover_tab` signatures unchanged
  (the `proxies` kwarg is accepted for orchestrator compat but **ignored**
  — TAB does NOT use the generic `capture/proxy.py` path). Creds read from
  `.env` at runtime; no secrets in the repo.
- **`config/settings.py`** — one line: `DISABLED_BOOKMAKERS = {"palm"}`
  (removed `"tab"`). TAB re-enters the normal bookie cadence.
- **`api/routes/soft_odds.py`** (new) — `GET /racing/markets/{market_id}/
  soft-odds`. Returns per selection-id-joined runner: `betfair_selection_id`,
  `tab_win`, `tab_place`, `scratched`, `captured_at`, plus a top-level
  `captured_at`. **Resolves the most-complete DR-034 fragment server-side**
  (prefer the fragment carrying TAB data, else the one with the most
  selection-ids) — an important hardening found during live verify (see
  Runner-match section). Registered in `api/main.py`.
- **`tests/test_tab_transport.py`** (new) — `unittest` (the repo's style;
  no pytest in that venv). 5 tests, all green: block→block→200 pins the
  third; pinned session reused; 403-on-pinned → re-hunt + re-pin; hunt
  budget exhausted → `TabTransportError`; 200-non-JSON block page not
  pinned. `curl_cffi` mocked — no live TAB in tests.
- Backups left for rollback: `bookmakers/tab.py.pre-s245-bak`,
  `api/main.py.pre-s245-bak`.
- Both `racing-api` and `racing-capture` services restarted and **active**.

### Tool side — `bethub-v3` (Mac, committed + pushed)

- **`clients/vps_client/v1/soft_odds.py`** (new) — `tab_soft_odds(market_id)`
  HTTP capture-read surface mirroring the `_lookup_api` pattern: `get_json`
  over the 8400 tunnel, typed `TabSoftOdds` / `TabSoftOddsRunner` payload,
  `404 → GENUINE_ABSENCE`, transport failure/5xx →
  `VPS_UNREACHABLE(retry_after=60)`. DR-028 respected — no local
  `capture.db`, no cache. Exported from `v1/__init__.py`.
- **`ui/api/routers/racing.py`** — `GET /v1/racing/markets/{market_id}/
  soft-odds` thin adapter after the catalogue route. NOTE: could not reuse
  `_envelope_to_http` (it is typed to the **betfair_client** envelope
  classes; the vps_client envelopes are different classes and its
  `UnavailableEnvelope` has no `as_of`). Wrote a dedicated mapper following
  the `bets.py` precedent: fresh → 200; terminal absence
  (GENUINE_ABSENCE / NOT_YET_CAPTURED / NOT_IN_CAPTURE_WINDOW) → clean
  **fresh-empty 200** (blank column, no error/console noise); only genuine
  VPS transport failure → 503.
- **Frontend** (`ui/web/src`):
  - `api/racing.ts` — `fetchTabSoftOdds(marketId)` + `TabSoftOdds` types.
  - `hooks/usePriceMemory.ts` — `loadTabOddsEnabled()` / `saveTabOddsEnabled()`
    on the localStorage template, key `RACING_TAB_ODDS_ENABLED`, **default ON**.
  - `routes/Racing.tsx` — gated `useQuery(['racing','tab-odds',marketId])`
    (`enabled: !!selectedMarket && tabOddsEnabled`, `retry:false`, 60s
    staleTime) + a **seed-once-per-selection** effect: seeds `manualOdds`
    via `snapSoft(tab_win)`, skips scratched/unpriced, and **never clobbers**
    a selection already present (seeded earlier or operator-typed) — so the
    seed is fully typeable-over and background refetches don't stomp edits.
  - `components/OddsTable.tsx` (+ `.module.css`) — a small glanceable
    "TAB odds" toggle switch in the odds-table header meta row, wired to
    the persisted flag.

Commit: **`fdd6c0b`** (parent `2e9abd3`), pushed to `origin/main`
(`murra86/bethub-v3`).

---

## Live-integration status (S189 taxonomy — honest)

- **LIVE-PROVEN (today):**
  - Transport: live `discover_tab` → 27 venues; `fetch_tab` → Wagga R1,
    8/8 runners priced, through Decodo-AU + Safari, pinned after 2 tries.
  - TAB enabled + capturing: after the collector restart, **302 TAB
    snapshots across 11 races within ~15 min**, feed refreshing at the
    capture cadence (latest timestamps advancing 03:06 → 03:19).
  - VPS soft-odds endpoint: Blackall R2 returned 7/7 priced runners keyed
    by `betfair_selection_id`; 404 for an unknown market.
  - **Tool-side client end to end:** `tab_soft_odds('1.260136569')` over
    the live 8400 tunnel returned FRESH, 7 runners, real odds
    (`tab_win=16.0`, `captured_at` advancing between reads) — Mac tool →
    tunnel → VPS endpoint → real captured TAB odds, proven live.
- **IMPLEMENTED-NOT-LIVE:** the **frontend auto-fill column + toggle**.
  Built, unit-tested (ON seeds / OFF blank / typeable-over / toggle
  persists), and served from a fresh `npm run build` dist — but not yet
  exercised in a real open-race session by the operator. First racing day
  with a race open + toggle ON is the live-proof.
- **NOT-WIRED:** nothing outstanding for Build 1. (Build 2 — the dedicated
  live-refresh Decodo IP for the active race page — remains out of scope.)

---

## Runner-match degradation (Phase E) — behaviour observed

The TAB↔Betfair selection-id join is stamped at ingest and is not always
complete. Confirmed live on **Pakenham Synthetic** (market `1.260136594`):
the market fragments into multiple DB rows — one shell with **0**
selection-ids, another with **15**. This surfaced a real correctness point:
a naive `WHERE betfair_win_market_id=? LIMIT 1` could pick the shell and
blank a race that actually has odds on another fragment. The endpoint now
resolves the most-complete fragment server-side, so:

- Fragment with selection-ids **and** TAB data → full odds (Blackall: 7/7).
- Selection-ids present but TAB hasn't priced yet → runners returned with
  `tab_win=null`, `captured_at=null` → column simply stays blank for those.
- No selection-ids on any fragment → empty `runners` list → blank column.

All three degrade cleanly: blank column, **no error, no console noise**,
and distinguishable from toggle-off (toggle-off disables the query
entirely; degradation returns a fresh-empty 200). No read-time
name/cloth-number fallback was built (per brief — that is not Build 1).

---

## Suites (both beat baseline 1511 / 220 at `2e9abd3`)

- **bethub-v3 backend: 1520 passed** (+9: 6 client-surface + 3 router).
- **bethub-v3 frontend: 224 passed** (+4 toggle/seed/typeable-over), 26
  files; `npm run build` clean (the real typecheck gate); dist rebuilt.
- **Capture side: 5 passed** (`tests/test_tab_transport.py`, unittest).

## Commits / pushes (bethub-v3)

- `fdd6c0b` — "S245 Build 1: TAB soft-odds auto-fill (tool side)", pushed
  to `origin/main`. Green tree. (Capture-side changes deployed but left
  uncommitted per the brief's two-repo discipline.)

## Fences honoured

Zero money paths edited or imported (settlement / reconciliation /
bet-entry / lay / promo-credit / hedge / cash-flow untouched). DR-028
boundary held (tool reads TAB odds only over the HTTP capture API; no local
`capture.db`, no cache). TAB kept off the generic proxy path. No VPS API
schema change was needed (the `runners.betfair_selection_id` join already
existed — the endpoint reads it). No stop condition triggered.
