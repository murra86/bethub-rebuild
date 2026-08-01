# Build 2 brief — TAB live-refresh for the active race page

**Session:** S245, 20 Jul 2026. **Author:** Chat (grounded on the live
code + the Build 1 transport). **Executor:** a background Code session.
**Priority:** HIGH — operator wants it for Saturday (odds move fast near
the off; he lays quickly and needs near-live prices).

Read this whole brief + `tab_spike_result_s245.md` (proven transport)
and confirm understanding **before editing any file**. This is a
data/display feature — **no money paths** (fence below).

## 0. What this is and why

Build 1 fills the Soft Odds column from the background capture feed —
fresh every ~5 min, tightening to ~2 min near jump. That's too slow for
the final minutes before the off, when TAB odds move fast and the
operator lays quickly. Build 2 adds a **dedicated live feed for the ONE
race the operator has open**: it fetches TAB odds straight from TAB
(bypassing the capture store) through a **second, dedicated Decodo AU
IP**, and refreshes fast as the race nears the jump.

Key property (operator-confirmed): the live fetch runs off the Decodo
residential IP — **never the operator's home line or TAB account** — so
aggressive polling carries **zero account-hygiene risk**; the only thing
at stake is scrape reliability.

## 1. Design

Three pieces. Reuse everything proven in Build 1.

### A. Transport — a dedicated "live" session (racing-data-capture)
`bookmakers/tab.py` today pins ONE module-level `_pinned_session` shared
by the collector's discovery + snapshots. The live feed must NOT share
it (fast live polling + collector polling on one IP invites blocks and
mutual re-hunts). **Refactor the pinned-session state into a small keyed
pool** — e.g. `_pinned_sessions: dict[str, str]` keyed by a pool name —
and give `fetch_tab` an optional `pool: str = "collector"` arg. The
collector keeps `"collector"`; the live endpoint uses `"live"`. Each
pool hunts-and-pins its own AU IP independently (same hunt-and-pin logic,
just per-pool). Keep the lock per-pool or a single lock guarding the
dict. Everything else in the transport (Safari, Decodo-AU, hunt-and-pin,
creds) is unchanged and LOAD-BEARING — do not alter it.

### B. Live endpoint (racing-data-capture)
New `GET /racing/markets/{market_id}/live-soft-odds`:
1. Resolve `market_id` (Betfair win market id) → the store's race row and
   its **TAB fetch identifiers** (date, TAB venue mnemonic, race number)
   AND the **runner_number → betfair_selection_id** map (the stamped
   join). Reuse the DR-034 most-complete-fragment resolution from
   `soft_odds.py` (and the same indexed, fast read — do NOT reintroduce a
   full scan; see the Build-1 perf fix + `test_soft_odds_route.py`).
   **Ground first:** confirm the race row actually carries what
   `fetch_tab` needs (venue mnemonic + race number + date) — if the
   stored `tab_race_id` / columns don't yield the TAB venue code, resolve
   it and say how in the report.
2. Call `fetch_tab(date, venue_code, race_number, pool="live")` → LIVE
   TAB odds by runner number.
3. Join live odds → `betfair_selection_id` via the store's runner map
   (by runner number within the race). Runners without a stamped
   selection id are omitted (same Phase E degradation as Build 1).
4. Return the SAME shape as `/soft-odds` (`betfair_selection_id`,
   `tab_win`, `tab_place`, `scratched`, `captured_at`=now), plus a
   `source: "live"` marker.
5. **Graceful failure:** if the live fetch blocks/erra (TabTransportError,
   timeout), return a clean "unavailable" (e.g. 503 or an empty
   `source:"live"` with a flag) — NEVER 500-noise. The tool falls back to
   the Build-1 background odds.

### C. Frontend — fast-poll the active race (bethub-v3)
- New `fetchTabLiveOdds(marketId)` in `api/racing.ts`.
- A second query in `Racing.tsx` that polls the LIVE endpoint, gated on:
  **page visible AND `tabOddsEnabled` AND the race is within ~30 min of
  jump** (outside that window, don't poll live — the background feed
  suffices). Adaptive cadence:
  - **~15 s** from T-30 min to T-5 min,
  - **~8 s** inside the final 5 min,
  - stop entirely on navigate-away / tab hidden / past jump.
  (These are named constants — the operator may tune them; they're off
  the Decodo IP so cadence is a reliability/politeness dial, not an
  account risk.)
- **Merge priority into the Soft Odds column:** when a live value is
  present for a selection, it **overrides** the background-capture value;
  when live is unavailable, fall back to the background value. In BOTH
  cases the operator-edit protection from the Build-1 fix stands — a
  selection in `operatorTouchedRef` is never overwritten by either feed.
  (Reuse/extend the existing seed effect + `operatorTouchedRef`; don't
  fork a parallel path that could clobber edits.)
- No new column, no new UI — same Soft Odds column, just faster underneath
  on the active race.

## 2. Fences (non-negotiable)
- **Bet-safety: zero money paths.** No settlement/reconciliation/stake/
  lay/hedge/promo-credit/cash-flow edits or imports. Display/data only.
- **Proven transport is LOAD-BEARING** — reuse it; the only change is the
  per-pool session split (A). Do not touch Safari/Decodo-AU/hunt-and-pin.
- **DR-028**: the tool reads live odds only over the HTTP capture API
  (the 8400 tunnel) — no local capture.db, no cache. New vps_client
  surface mirrors `soft_odds.py` client.
- **Two repos:** capture side (VPS working tree, surgical, uncommitted,
  leave a `.pre-*-bak`); bethub-v3 (commit + push GREEN only, co-author
  trailer, rebuild dist app-down).
- **Politeness:** the live poll is ONE race at a time, adaptive, stops on
  navigate-away. Do not poll live for races outside the ~30-min window or
  when the page is hidden.

## 3. Tests
- Transport: two pools hunt/pin independently; a block on the "live"
  pinned session re-hunts "live" WITHOUT disturbing "collector"'s pin.
- Live endpoint: join correctness (live odds keyed by selection id);
  unstamped runners omitted; a transport failure → clean unavailable (not
  500); the resolve query does NOT full-scan (extend the
  `test_soft_odds_route.py` plan-guard pattern).
- Frontend: live overrides background for the same selection; live
  unavailable → background shown; operator edit survives BOTH feeds; poll
  gated off outside the window / when hidden.
- `uv run pytest` + `npm run build` green. Beat baselines: bethub-v3
  1522 backend / 242 frontend at HEAD `8e49c97`; capture-side unittest
  (transport + soft-odds route) green.

## 4. Stop conditions
Stop and report if: the store can't yield the TAB fetch identifiers for a
market (blocks the live fetch — flag it, don't guess); a money module
would need touching; the transport per-pool split can't be done without
disturbing the collector's proven path; or the live fetch can't be made
to degrade cleanly to the background feed.

## 5. Report
`tab_live_refresh_build2_report.md` in bethub-rebuild: what landed each
side; live-integration status per S189 (the live endpoint can be
**live-proven** against real TAB today; the frontend fast-refresh is
**implemented-not-live** until the operator watches a race into the jump);
the merge/override + edit-protection behaviour; cadence constants;
suites; commits. Be honest about what's proven live vs fixture-tested.
