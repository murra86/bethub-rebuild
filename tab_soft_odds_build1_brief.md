# Build 1 brief — TAB soft-odds auto-fill (background feed)

**Session:** S245, 20 Jul 2026. **Author:** Chat (grounded on a live
A1 spike + a full v3/capture code map). **Executor:** a background
Code session. **Priority:** HIGH (operator-flagged, TAB is the main
promo driver).

Read this whole brief and confirm understanding **before editing any
file**. Ask about anything ambiguous first. This is a data/display
feature — **no money paths anywhere in it** (see the fence below).

---

## 0. What we're building and why

Today the operator types TAB fixed odds into the "Soft Odds" column by
hand to get an EV read. Build 1 makes that column **auto-fill from the
background capture feed** for TAB races — still fully typeable-over —
and turns TAB capture back on (it was disabled only because TAB started
403ing our requests; the transport is now solved — see §1). The same
feed will later drive the race watcher.

**Explicitly OUT of scope (Build 2, separate brief):** the dedicated
second Decodo IP for fast live-refresh of the active race page. Build 1
serves odds at the background-capture cadence only (per-race: from
60 min before jump, every 5 min, tightening to ~2 min in the last 5,
plus a forced final snapshot T-10..T-30s). Do not build on-demand /
live-refresh fetching in Build 1.

## 1. The proven transport (LOAD-BEARING — do not substitute)

Full spike write-up: `tab_spike_result_s245.md` (read it). The block on
TAB is **geographic (Australia-only) + Akamai browser-fingerprint**,
not the datacenter-TLS story the old scoping brief assumed. The proven,
working transport is:

- **Proxy:** Decodo residential **country-targeted to AU**, endpoint
  **`gate.decodo.com:7000`**, username format
  **`user-<DECODO_USERNAME>-country-au-session-<sid>-sessionduration-<mins>`**.
  Creds already in the capture `.env` (`DECODO_USERNAME`,
  `DECODO_PASSWORD`). **Do NOT use** the bare username or the
  `au.decodo.com` endpoint (they return Netherlands IPs → geo-blocked),
  and the `-country-au` modifier without the `user-` prefix returns 407.
- **TLS:** `curl_cffi` with **`impersonate="safari"`** (installed on the
  VPS). **Chrome impersonation gets 403** — Safari is required.
- **Reliability = hunt-and-pin.** A *fresh random* AU IP passes TAB only
  ~1-in-several tries (most → 403 "Access Denied"); a *pinned working*
  IP holds (proven 8/8). So: cycle `session-<sid>` values until a
  200/JSON, then **pin that session** and reuse it for subsequent polls;
  **re-hunt only on a 403/block**, not every poll. Keep a module-level
  pinned session; back off politely (the existing bookie stagger of
  2–5s applies; don't hammer the hunt).

**Consequence for the code:** TAB is a *special-case* bookmaker with its
own fetch path — it must NOT go through the generic `capture/proxy.py`
(requests + rotating pool) path the other bookies use, because that path
can't do Safari impersonation, AU country-targeting, or hunt-and-pin.
Give `bookmakers/tab.py` its own `curl_cffi` transport that implements
hunt-and-pin, reading the same `.env` creds.

## 2. Governing disciplines (non-negotiable)

- **Two repos.** Capture side = `racing-data-capture` on the VPS
  (`root@187.77.183.9`, working dir `/home/racing/racing-data-capture`,
  venv at `venv/`). Tool side = `bethub-v3` (Mac,
  `~/Desktop/Projects/bethub-v3`, `uv run pytest`). The VPS repo has
  deliberately-uncommitted in-flight work — do not commit it wholesale;
  make your TAB changes surgically and leave the rest of its tree alone.
  The `bethub-v3` repo has full git autonomy: commit + push green trees
  with the co-author trailer.
- **DR-027 / DR-028 (two-database boundary).** BetHub owns operational
  state; capture.db owns analytical/source data. The tool reads TAB
  odds **only** over the HTTP capture API (the 8400 tunnel,
  `clients/vps_client` `get_json`) — **never open a local capture.db,
  never cache, never add a second integration point.** New capture-read
  surface follows `clients/vps_client/v1/_lookup_api.py` exactly.
- **BET-SAFETY FENCE.** This build touches **zero** money paths. Do not
  edit or import settlement, reconciliation, bet-entry, lay-placement,
  promo-credit, hedge, or cash-flow code. The only write the tool does
  is `setManualOdds` into frontend state (typeable-over display value).
  If you find yourself needing to touch a money module, STOP and report.
- **Static build.** After any frontend change, `npm run build` (vitest
  does not typecheck; `npm run build` is the real gate). Serve the dist;
  rebuild app-down per S232.
- **Read-write vs read-only:** capture repo — read-write but surgical.
  bethub-v3 — read-write. Live capture.db — read-only always.

## 3. Work, in phases

### Phase A — Capture side: transport + enable (racing-data-capture)
1. `bookmakers/tab.py`: replace the `requests`-based fetch with the
   proven `curl_cffi` Safari + Decodo-AU hunt-and-pin transport (§1).
   Keep the existing `fetch_tab` / `discover_tab` signatures and return
   shapes (`BookmakerMeta` / `BookmakerRunner`) so the orchestrator is
   unchanged. Module-level pinned session; re-hunt on 403.
2. `config/settings.py`: remove `"tab"` from `DISABLED_BOOKMAKERS`
   (leave `"palm"`). TAB then re-enters the collector's normal bookie
   cadence automatically.
3. **Expose TAB odds keyed by `betfair_selection_id`** on the VPS
   racing API (the tunneled 8400 service). The runners table already
   holds the TAB↔Betfair selection join stamped at ingest; add/extend a
   read endpoint (e.g. `/racing/markets/{betfair_win_market_id}/soft-odds`
   or extend the snapshots surface) that returns, per runner:
   `betfair_selection_id`, `tab_win`, `tab_place`, `scratched`, and a
   `captured_at` timestamp. Freshness/absence handled by the envelope
   contract on the tool side (§Phase C).
4. **Verify live** through the proven transport before moving on: TAB
   discovery + a racecard return real odds (the spike scripts are the
   reference; do not re-paste secrets into the repo).

### Phase B — DO NOT reuse the generic proxy path for TAB
Restate for safety: the generic `capture/proxy.py` rotating-requests
path is for the other bookies. TAB uses the dedicated transport from
Phase A.1. (No file work here — this is a guardrail.)

### Phase C — Tool side: capture read + route (bethub-v3)
1. New `clients/vps_client/v1/` surface (mirror `_lookup_api.py`): call
   `get_json(".../soft-odds", {id})` over the 8400 tunnel, apply the
   same id-resolution used elsewhere (Betfair `market_id` →
   `betfair_win_market_id`; see `identifier_resolution.py` /
   `race_lookup.py`), wrap results in an envelope, map
   `CaptureApiUnavailableError` → `UnavailableEnvelope(reason=
   VPS_UNREACHABLE, retry_after=60)`.
2. `ui/api/routers/racing.py`: add `GET /v1/racing/markets/{market_id}/soft-odds`
   in the §5.3 read block (after the catalogue route, ~line 725). Thin
   adapter only — delegate to the new client surface and reuse
   `_envelope_to_http`. No business logic in the router.

### Phase D — Frontend: fetch, seed, toggle (ui/web/src)
1. `api/racing.ts`: add `fetchTabSoftOdds(marketId)` next to
   `fetchMarketCatalogue`, returning the envelope type.
2. `routes/Racing.tsx`: add a `useQuery(['racing','tab-odds', market_id])`
   gated `enabled: !!selectedMarket && tabEnabled`. On success, seed
   `setManualOdds(selection_id, snapSoft(tabPrice))` per matched runner
   (snap through `ev/softOddsLadder` for ladder consistency). The
   existing `SoftOddsInput` external-pre-fill re-sync makes seeded
   values typeable-over — do not fight it. **Reverse** the current
   "start blank, never pre-fill" stance (OddsTable.tsx ~250-252,
   Racing.tsx ~195-199) — but only when the toggle is ON.
3. **Global TAB-odds on/off toggle.** Add
   `loadTabOddsEnabled()/saveTabOddsEnabled()` on the `usePriceMemory.ts`
   localStorage template, key `RACING_TAB_ODDS_ENABLED`, **default ON**.
   Gate both the `useQuery` `enabled` and the seeding on it. Surface the
   toggle in the race-page UI (a small labelled switch — you lead on
   placement; keep it glanceable, near the odds column/top bar). When
   OFF, the column behaves exactly as today (blank, operator types).

### Phase E — Runner-match honesty (important edge case)
The TAB↔Betfair `selection_id` join is stamped at capture ingest and is
**not always complete** — some meetings (e.g. Pakenham Synthetic seen
S245) have the market linked but runner selection-ids unstamped. When a
race's runners aren't selection-id-joined on the capture side, the
soft-odds surface returns no per-runner odds for them → the column stays
blank for that race → operator types as today. **This is acceptable
graceful degradation — do NOT build a read-time name/cloth-number
fallback matcher in Build 1.** Just ensure the empty/partial case
degrades cleanly (blank column, no error, no console noise) and is
distinguishable from "toggle off". Note it in the report.

## 4. Testing (fenced)
- Capture side: unit-test the hunt-and-pin transport logic (mock the
  proxy responses: block→block→200 sequence pins the third; a 403 on a
  pinned session triggers re-hunt). Do not hit live TAB in tests.
- Tool side: `uv run pytest` green. Cover the new client surface
  (unavailable → envelope; partial/empty selection join → blank), the
  route (envelope→http mapping), and id-resolution.
- Frontend: `npm run build` clean; tests for the toggle gating (ON
  seeds, OFF blank) and the seed-is-typeable-over behaviour.
- **No money-path tests touched.** Suite baselines to beat: bethub-v3
  1511/220 at HEAD `2e9abd3`.

## 5. Stop conditions / report
- Stop and report if: a money module would need touching; the capture
  selection-id join is more broken than the Pakenham class (i.e. widely
  empty, not occasional); the VPS API can't expose selection-id-keyed
  odds without a schema change (flag before doing any schema work — that
  is an operator/architecture call, not a build call); or the live TAB
  verify fails through the proven transport.
- Deliver a report `tab_soft_odds_build1_report.md` in bethub-rebuild:
  what landed on each side, live-integration status per the S189
  taxonomy (live-proven vs implemented-not-live vs not-wired — be
  honest; the frontend column is implemented-not-live until exercised on
  a real race day), the runner-match degradation behaviour observed,
  suite numbers, and commits/pushes on the bethub-v3 side.
- Classify "done" honestly: the transport + capture verify can be
  **live-proven** today; the frontend auto-fill is **implemented-not-
  live** until a race day.

## 6. What's already proven (don't re-litigate)
Transport works end-to-end (live Wagga R1 odds pulled through Decodo AU
+ Safari). Decodo plan covers AU free. No new spend. The two-build split
and the freshness model are locked (background feed → column now; live
IP → Build 2 later). Toggle is global, default ON.
