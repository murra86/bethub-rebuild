# DR-029 §2.1 follow-up — Saturday Betfair API observation probe brief

**Brief drafted:** Session 39, 2026-04-30 ACST.
**Probe runs:** Saturday morning ACST 2026-05-02 (operator opens Code session ~10:00–10:30 ACST).
**Tool routing:** Claude Code, single bounded session.
**Output:** `dr029/2_1_race_data/api_probe_data/` (raw JSONL + manifest) plus `dr029/2_1_race_data/api_probe_report.md` (field-availability matrix).
**Anchors:** `surgical_fix_3_report.md` §6 (the empirical "no `sp` field on closed runners" finding); `source_review_report.md` §5.3 (the inferred-but-empirically-wrong API-shape assumptions); `inspection_report.md` §F (BSP/SP 0% population).

---

## 1. What this is — and what it isn't

This is a **direct empirical observation probe** of Betfair's `MarketBook` API across a full race window, on real AU markets. Read-only. Standalone script. The probe captures raw `MarketBook` JSON every 1 second from race-discovery (T-60min) through CLOSED+45min, requesting every supported `priceProjection` in a single combined call per second, and writes the raw responses unchanged. Alongside it, a parallel Racing API capture stream runs at slower cadence to provide cross-source identity context. Session 40 reads the output and produces an analytical field-availability and join-feasibility report.

This is **NOT a fix**. No edits to `capture/orchestrator.py`, `betfair/client.py`, `storage/database.py`, or any other file in the analytical line. No service restart. No schema changes. No write-back path into `capture.db`. The orchestrator runs untouched alongside the probe.

This is **NOT a test**. No assertions, no pass/fail. The output is observed reality. Analysis is Session 40's job.

This is **NOT a fix-4 or fix-5 brief**. Cadence design (fix 4) and venue harmonisation (fix 5) wait on this probe's output before their briefs land.

---

## 2. Why the probe — short version

**The empirical surprise from Fix 3** (Session 37, `surgical_fix_3_report.md` §6): Betfair's `priceProjection=SP_TRADED` on closed AU thoroughbred WIN markets returns runner objects with `keys = ['selectionId', 'handicap', 'status', 'adjustmentFactor']` — **no `sp` field at all**. The Fix 3 brief inferred from `RunnerData.sp_near_price`/`sp_far_price` adjacency in the migration that `bsp_price` should follow the same projection mechanism. The inference was wrong; nobody knows what's actually right.

**Saturday timing**: chosen because it's the operator's preferred slot, not because the API behaviour requires Saturday. Betfair's API serves the same field structure regardless of meeting tier. Saturday metros do help marginally with question 4 (cadence of meaningful change) — thin Tuesday markets show no movement and conflate "no API change" with "no liquidity." But the BSP/SP write-back behaviour (questions 1, 2, 3) is API-internal and meeting-agnostic.

Three layers of inference (`inspection_report.md` → `source_review_report.md` → `surgical_fix_3_brief.md` → empirical test) is too many. Going direct: capture the raw API output across a real race, every second, with every projection requested in one call, then read what's actually there.

---

## 3. The five questions this probe answers

The probe is scoped to answer these five questions and no more. The output is structured to make each question's answer fall out cleanly.

1. **When (if ever) does `r.sp.actual_sp` populate?** Pre-jump? OPEN→SUSPENDED transition? SUSPENDED→CLOSED? Some time after CLOSED? Never via this API path? This is the BSP write-back question that Fix 3's inference got wrong. The probe will show the time-relative-to-jump curve of `sp.actual_sp` presence/absence across the race window.

2. **Cross-code response-shape parity.** Code's Fix 3 probe only tested AU thoroughbred WIN markets. Does harness behave the same? Does greyhound? If the SP fields populate differently (or at all) across codes, that's a Fix 4 design input.

3. **What fields does the API expose that the snapshot writer doesn't capture?** This is a substantial chunk of §2.10's API-field-inventory deliverable. The full key-list per response, observed across all projections, is the answer.

4. **What's the cadence of meaningful change at 1-second granularity?** Across `best_back_price`, `best_lay_price`, `total_matched`, market_status, runner_status. Informs Fix 4's cadence design. Specifically: how often does `best_back_price` actually move at 1s vs 5s vs 30s, and does the answer differ across phases (T-30min vs T-1min vs SUSPENDED)?

5. **Race and runner identity alignment across Betfair and Racing API.** At any given moment during the race window, how does Betfair's `marketId` / `selectionId` map to Racing API's race code / runner identity? Are runner name strings consistent? Do scratchings flow through both sources at similar latency? Do start times agree? Racing API also bundles Sportsbet and Ladbrokes odds against its own runner identity, so this question covers all three retail surfaces (Racing API native + Sportsbet via Racing API + Ladbrokes via Racing API) at once. Answers feed eventual cross-source join logic.

These are the five questions. The probe is not for "discover everything Betfair offers" beyond what the combined-projection call returns naturally. Anything beyond the five is observation-bonus, not target.

---

## 4. Probe scope (locked Sessions 37 and 39)

### 4.1 Markets

**Four markets, sequential capture.** Code picks at runtime from what's running on Saturday, prioritising metros with good liquidity:

- **2 thoroughbred WIN markets** from AU metro tracks (Randwick / Flemington / Eagle Farm / Caulfield / Rosehill / Moonee Valley etc., whichever is running). Pick races spaced roughly 2 hours apart so capture windows don't overlap.
- **1 harness WIN market** from a metro track if available (Gloucester Park, Tabcorp Park Menangle, etc.). If no metro harness available Saturday, pick best-liquidity provincial.
- **1 greyhound WIN market** from a metro track (Wentworth Park, The Meadows, Albion Park, etc.). Same liquidity-priority fallback if no metro.

Code chooses on the day. Selection criteria in priority order: (i) AU metro; (ii) market opened well in advance (Betfair has had time to populate fields); (iii) liquidity high enough that SP traded volume is meaningful (`total_matched` ideally >$50k by T-15min for thoroughbreds, less for harness/greyhound).

**No PLACE markets in this run.** WIN only. PLACE adds complexity without answering the five questions in this pass. However: the probe script's market-discovery filter MUST accept a `market_types` list as a parameter. This run passes `["WIN"]`. A future probe pass adding PLACE just changes that parameter — no rewrite. JSONL output is already keyed by `market_id`, so PLACE markets would land in their own files naturally. Note for §12.

**No NZ markets.** Per `dr029_scope.md` §3.9 NZ is backward-compatible-later. AU only.

**Brief constraint: at least one of the four races must be a thoroughbred.** Thoroughbred is what we have the most baseline data on; comparing harness/greyhound shape *to* a thoroughbred reference is question 2's whole point.

### 4.2 Time window per market

**T-60 min through CLOSED+45 min** (snapshot every 1 second).

Phase decomposition for analysis:
- **STANDARD** phase: T-60min → T-5min (per `capture/scheduler.py:107-129` thresholds).
- **INTENSIVE** phase: T-5min → T-0 (jump).
- **POST_START / SUSPENDED**: T-0 → market suspends. Variable; usually <2 min.
- **SETTLEMENT TRANSITION**: SUSPENDED → CLOSED. Variable; usually 5-30 min depending on protest/photo-finish.
- **CLOSED**: CLOSED → CLOSED+45min.

**Why CLOSED+45min** (not just CLOSED): the BSP gap finding needs to know if `actual_sp` shows up at any point post-CLOSED, not just at the moment of CLOSE. Fix 3 probed three markets between 5min and 1hr post-CLOSE — saw nothing. The probe gives the full 45min window so we can see if *any* time post-CLOSED yields SP data.

**Total wall-clock per market: ~105 min.** Four markets sequential, spaced naturally by Saturday's race-card timing.

### 4.3 Snapshot cadence

**1 call per second per race** during the active capture window. Hard ceiling — no parallel calls per race.

Each call carries every supported `priceProjection` value combined into a single `priceData` request. Result: each second in the data is a single MarketBook response containing the maximum-information shape Betfair will return. No rotation, no projection cycling.

### 4.4 Projection request shape

The probe issues one combined call per second per race. The `price_data` argument carries:

```python
price_data=["EX_BEST_OFFERS", "EX_ALL_OFFERS", "EX_LADDER", "SP_AVAILABLE", "SP_TRADED"]
```

Plus accompanying `priceProjection` flags as the `betfairlightweight` library supports (e.g., `virtualise=True` if it materially changes returned fields, `rolloverStakes=False`).

**Why combined rather than rotated:** the probe is a one-off observation pass. Rotation reserves bandwidth we don't need and risks a field appearing only when its projection is present, then being missed because the next second carried a different projection. Combined call gives every field every second. Single call per second keeps API load identical to rotation (1 call/sec either way).

**Fallback if `EX_LADDER` errors in the combined call:** Betfair's `TOO_MUCH_DATA` is the realistic risk on full-ladder requests for 20+ runner fields. Code's adaptation:

1. On combined-call success: continue at 1/sec with the full combined call.
2. On combined-call returning `TOO_MUCH_DATA` or similar 3+ times consecutively: drop `EX_LADDER` from the combined call. Continue at 1/sec with the reduced combined call.
3. To still capture `EX_LADDER` data: every 10 seconds, fire one extra single-projection call carrying `EX_LADDER` only. Captures ~10/min of `EX_LADDER` while preserving combined-call cadence on the other projections.
4. Log the fallback transition to manifest's `api_events` list with timestamp and triggering error.

**Hard rule: maximum 2 calls per second per race in any state** (the combined call plus at most one fallback `EX_LADDER` call). Across 4 sequential races this means peak ~2 calls/sec, well inside Betfair's 5 calls/sec hard cap. Sustained average across the day: well under 2/sec because of inter-race idle.

### 4.5 Rate-limit guard-rails

**Hard rule: 1 call per second per race, no parallel calls, no overlap between races.**

Code halves cadence to 1-per-2-seconds for the remainder of the current race if any of the following:
- Betfair returns rate-limit warning header.
- Betfair returns API error (`INVALID_INPUT_DATA`, `TOO_MUCH_DATA`, etc.) on more than 3 consecutive calls.
- Response time exceeds 2000ms on more than 5 consecutive calls.

Cadence restoration to 1-per-1 only on a fresh race (next market in sequence), not mid-race.

**Total expected API call volume:** 4 races × ~6,300 seconds × 1 call/sec = ~25,000 calls across the day. Spread across ~7 hours of wall-clock = ~1 call/sec sustained, mostly idle between race windows. Comfortably below Betfair's published rate limits for `listMarketBook` (5 calls/sec hard cap, 200 calls/min weighted limit per their docs).

### 4.6 Markets covered separately

The four races are captured **sequentially**, not in parallel. When race 1's window closes (CLOSED+45min) the script moves to race 2. Race 2's capture starts at race 2's T-60min, which may be hours after race 1 ended.

**Inter-race idle period:** the script sleeps or polls discovery until next selected race enters its T-60min window. No API calls during idle.

### 4.7 Parallel Racing API capture stream

Alongside the Betfair MarketBook capture, a **second parallel capture stream** queries Racing API for the same race window at slower cadence. Purpose: feed question 5 (cross-source identity alignment) plus capture Racing API's bundled Sportsbet and Ladbrokes odds against Racing API's own runner identity.

**Cadence: every 30 seconds per race** during the active capture window. Reasoning: Racing API's bundled sportsbook odds typically refresh every 30s–2min depending on the bookmaker's update cycle. 30s captures meaningful price movement without flooding; 60s would miss real movement; 1s would mostly capture identical responses. Roughly 210 captures per 105-min race window.

**Scope: capture everything Racing API returns for these races, no filtering.** Same one-off-probe reasoning as the Betfair greedy-capture choice: raw is cheaper to capture now than to re-probe for later. Racing API responses are smaller than Betfair `MarketBook` responses (no order books, no ladders) so storage is not a concern.

**Endpoints to capture per cycle:**
- Race entries / runners endpoint (whichever Racing API surface returns the canonical race + runner identity for the race in question).
- Bundled sportsbook odds endpoint(s) for Sportsbet and Ladbrokes against this race (Racing API documentation confirms both are provided).
- Any race-status / scratchings endpoint relevant to the race in question.

Code picks the exact endpoint set on the day based on what Racing API's auth and documentation support; the brief is loose on which calls; tight on "capture full responses, not selected fields."

**Output:** `/home/racing/probe_output/api_probe_data/race_{N}_{code}_{venue}_{race_number}_racingapi.jsonl` — separate JSONL file per race, parallel to the Betfair JSONL. Same wrapping-metadata schema (ts_utc, ts_acst, race identity, minutes_to_start, phase_inferred), with `source: "racing_api"`, `endpoint: "<name>"`, and the raw Racing API response in `response`.

**Auth and rate limits:** Racing API uses its own credentials (per the running orchestrator's existing config). Rate limits are Racing API's own; 30s cadence per race times max one race active = 1 call per 30 seconds sustained, well inside any sensible API limit.

**Failure isolation:** if Racing API auth fails or any endpoint returns errors persistently, Code logs the failure to manifest's `api_events` and continues the Betfair stream uninterrupted. Question 5 may be partially answered or unanswered as a result; questions 1–4 are unaffected. The Betfair stream is the load-bearing capture; Racing API is additive.

**No write-back to Racing API’s feed.** Probe is read-only against Racing API just as it is against Betfair.

---

## 5. Hard limits — the isolation envelope

These are non-negotiable. Probe runs as an isolated standalone script.

1. **Read-only API.** No `place_bet`, no `cancel_order`, no `update_order`. Only `list_market_book`, `list_market_catalogue`, `list_event_types` (if needed for picking races). The Betfair session is read-only by virtue of which methods are called.

2. **No edits to any analytical-line file.** Including but not limited to: `capture/orchestrator.py`, `betfair/client.py`, `betfair/models.py`, `storage/database.py`, `subscription/racing_api.py`, `scripts/*.py`, `config/settings.py`, anything under `bookmakers/`. The probe is a new standalone script, not a modification of existing code.

3. **No service restart.** `racing-capture.service` runs untouched. The probe shares the Betfair session via the same credentials but does not interfere with the running orchestrator. Per Fix 3 report §1: same `.env` credentials, same app key, Betfair allows shared session across multiple clients.

4. **Standalone script location:** `/home/racing/probe_output/probe.py` (or similar). NOT inside the source tree. NOT installed via the venv as a runnable module. Run directly via `python3 probe.py` from `/home/racing/probe_output/`.

5. **Output written to dedicated directory:** `/home/racing/probe_output/`. NOT `/home/racing/racing-data-capture/data/`, NOT anywhere `capture.db` lives. Probe never opens `capture.db` for any purpose.

6. **Honour the dirty git tree** (per Sessions 35/36/37 pattern). No `git add`, no `git commit`, no `git stash`, no `git restore`, no `git checkout` (file-targeted), no `git reset` of any kind. The eight pre-existing modified files plus seven untracked entries stay untouched. The probe lives outside the source tree so it cannot accidentally land in `git status`.

7. **No schema changes** — probe doesn't touch any SQLite database.

8. **No new Python dependencies.** Probe uses `betfairlightweight` (already installed), standard library `json`, `time`, `pathlib`, `os`. If Code wants to use `pandas` for the manifest, that's already installed via the venv.

9. **No tests written, no test infrastructure modified.**

10. **Single Code session, bounded.** Probe runs in one Saturday Code session, ~7 hours of mostly-idle wall-clock. Code session ends after race 4's CLOSED+45min window plus the report-writing pass.

---

## 6. Output structure

### 6.1 Raw data — Betfair JSONL per race

`/home/racing/probe_output/api_probe_data/race_{N}_{code}_{venue}_{race_number}_betfair.jsonl` — one file per race, append-only. (Racing API stream lands in a parallel `_racingapi.jsonl` file per race; see §4.7.)

Each line is a JSON object:

```json
{
  "ts_utc": "2026-05-02T05:42:13.124Z",
  "ts_acst": "2026-05-02T15:12:13.124+09:30",
  "source": "betfair",
  "race_code": "thoroughbred",
  "venue": "Randwick",
  "race_number": 5,
  "scheduled_start_utc": "2026-05-02T06:30:00Z",
  "minutes_to_start": -47.78,
  "phase_inferred": "STANDARD",
  "market_id": "1.234567890",
  "projection_requested": ["EX_BEST_OFFERS", "EX_ALL_OFFERS", "EX_LADDER", "SP_AVAILABLE", "SP_TRADED"],
  "projection_fallback_active": false,
  "request_duration_ms": 187,
  "api_error": null,
  "response": { ... raw MarketBook response, lightweight=True ... }
}
```

The wrapping object's metadata (timestamps, projection set requested, fallback state, phase, race identity) makes the output greppable / jq-able / pandas-loadable. The `response` field contains the raw Betfair `MarketBook` exactly as returned (no transformation, no field selection, no filtering).

**Append-only** — each second's call appends one line. If write fails partway, only the last second is lost.

When the `EX_LADDER`-fallback path is active (§4.4), each 10-second cycle adds one supplementary line with `projection_requested: ["EX_LADDER"]` and `projection_fallback_active: true`, distinguishable from the main combined-call lines via the boolean flag.

### 6.2 Manifest

`/home/racing/probe_output/api_probe_data/manifest.json` — written at probe-start, updated as each race completes:

```json
{
  "probe_run_id": "2026-05-02_saturday_metros",
  "started_at_utc": "2026-05-02T00:30:00Z",
  "completed_at_utc": null,
  "races": [
    {
      "race_index": 1,
      "race_code": "thoroughbred",
      "venue": "Randwick",
      "race_number": 5,
      "scheduled_start_utc": "2026-05-02T06:30:00Z",
      "market_id": "1.234567890",
      "betfair_captured": false,
      "betfair_snapshots_count": null,
      "betfair_data_file": "race_1_thoroughbred_Randwick_5_betfair.jsonl",
      "racingapi_captured": false,
      "racingapi_snapshots_count": null,
      "racingapi_data_file": "race_1_thoroughbred_Randwick_5_racingapi.jsonl",
      "first_snapshot_ts_utc": null,
      "last_snapshot_ts_utc": null
    }
  ],
  "projection_set_initial": ["EX_BEST_OFFERS", "EX_ALL_OFFERS", "EX_LADDER", "SP_AVAILABLE", "SP_TRADED"],
  "api_events": []
}
```

The `api_events` array logs any deviation from baseline cadence: `EX_LADDER` fallback transitions, rate-limit-driven slowdowns, Racing API auth failures, race scratchings mid-capture, etc. Each event carries `ts_utc`, `race_index`, `event_type`, and a free-form `note`.

### 6.3 Analytical report — `api_probe_report.md`

Written by Code at end of probe run, after all four races captured. Source-review-style report (loose narrative + observation tables, NOT a fix-shaped report).

Required sections:

- **§1 Probe execution summary.** Which four races captured, snapshot counts (Betfair + Racing API separately), any rate-limit events, any per-projection error patterns, any Racing API endpoint failures.
- **§2 Field-availability matrix.** From the Betfair stream: for each phase (STANDARD / INTENSIVE / POST_START / SUSPENDED / CLOSED), the list of fields seen on `runners[*]` and on the top-level `MarketBook` object, with non-null rates. Indexed by `(race_code × market_state × time-relative-to-jump)`. Where the `EX_LADDER`-fallback path was active, fields appearing only in fallback lines are noted separately.
- **§3 Direct answers to the five questions:**
  - §3.1 — `r.sp.actual_sp` time-relative-to-jump curve, per code.
  - §3.2 — Cross-code response-shape parity (any deltas between thoroughbred / harness / greyhound).
  - §3.3 — Field deltas vs current snapshot writer (the `data_layer_current.md` §4-5 fields, what the API exposes that the writer doesn't capture).
  - §3.4 — 1s cadence-of-meaningful-change observations on `best_back_price`, `best_lay_price`, `total_matched`, market_status.
  - §3.5 — Race and runner identity alignment between Betfair and Racing API. Includes: per-race mapping of Betfair `marketId` ↔ Racing API race code, Betfair `selectionId` ↔ Racing API runner identity (with name-string deltas noted), scratching latency between sources, start-time agreement, and observed structure of Racing API's bundled Sportsbet / Ladbrokes odds (field names, refresh cadence, runner-identity scheme).
- **§4 Anything surprising.** Same shape as Fix 3 report §6 — observations the brief didn't anticipate.
- **§5 Forward-routing notes.** Brief one-liners suggesting which observations feed Fix 4 (cadence), Fix 5 (venue harmonisation — unlikely from this probe but possible), §2.10 (API-field-inventory), and any future cross-source alignment work that question 5 surfaces.
- **§6 Self-assessment.** Did the five questions get answered? What's uncertain?

**Length target: 250-450 lines.** Slightly larger than original target to accommodate §3.5. Not a thesis; observation-grounded notes.

### 6.4 Disk space

Estimated storage:
- Betfair stream: 4 races × ~6,300 lines × ~6 KB per line (raw `MarketBook` with all projections combined is the upper bound) ≈ 150 MB.
- Racing API stream: 4 races × ~210 lines × ~3 KB per line ≈ 2.5 MB.
- Total: well under 200 MB. Comfortably under the 2 GB headroom check operator does pre-session.

---

## 7. Execution sequence

This is the Code-side narrative. Loose hand on exact commands; Code adapts.

1. **Pre-flight checks.** Verify VPS reachable, Betfair credentials valid (`/home/racing/racing-data-capture/.env` readable, login succeeds), `racing-capture.service` running, `/home/racing/` has ≥ 2GB free.

2. **Create probe workspace.** `mkdir -p /home/racing/probe_output/api_probe_data/`. Write `probe.py` to `/home/racing/probe_output/probe.py`.

3. **Discover Saturday's races.** Call Betfair `list_market_catalogue` filtered to AU horse/harness/greyhound (event_type_ids `[7, 4339]` — type IDs to confirm via `list_event_types`), market_countries `["AU"]`, market_type `WIN`, time window 06:00–21:00 UTC for Saturday (= ~16:00 ACST onwards). Inspect catalogue, pick four races meeting selection criteria (§4.1). Log selections to `manifest.json`.

4. **Per-race capture loop.** For each of the four selected markets in chronological order, run two parallel sub-loops covering the same T-60min through CLOSED+45min window:

   - **Betfair sub-loop (every 1 second):**
     - Open the race's `_betfair.jsonl` file in append mode.
     - Every second, call `list_market_book(market_ids=[market_id], price_projection=price_projection(price_data=["EX_BEST_OFFERS", "EX_ALL_OFFERS", "EX_LADDER", "SP_AVAILABLE", "SP_TRADED"]), lightweight=True)`. Wrap with metadata (§6.1 schema). Append line to JSONL.
     - If `EX_LADDER`-fallback triggers (§4.4), drop `EX_LADDER` from the combined call and add a 10s-cadence supplementary `EX_LADDER`-only call writing to the same JSONL with `projection_fallback_active: true`.
   - **Racing API sub-loop (every 30 seconds):**
     - Open the race's `_racingapi.jsonl` file in append mode.
     - Every 30 seconds, call the Racing API endpoints identified in §4.7 for this race. Wrap with metadata (same schema, `source: "racing_api"`). Append lines to JSONL.
     - Failures isolated to manifest `api_events`; do not interrupt the Betfair sub-loop.
   - Continue both sub-loops until T+45min past CLOSED detection (i.e., until 45 minutes after `market_status == "CLOSED"` first observed in the Betfair stream).
   - Close both JSONLs. Update manifest race entry with `betfair_captured`/`racingapi_captured` flags, snapshot counts, ts bounds.

5. **Inter-race idle.** Sleep / poll until next race's T-60min.

6. **Post-capture analysis.** After race 4 capture completes:
   - Load all eight JSONL files (Betfair + Racing API per race).
   - Compute field-availability matrix per (race_code × market_state) from Betfair stream.
   - Compute time-relative-to-jump curves for `r.sp.actual_sp` per code.
   - Compute 1s cadence-of-meaningful-change rates for the four observable Betfair fields.
   - Compute Betfair ↔ Racing API identity alignment per race.
   - Write `api_probe_report.md` per §6.3 structure.

7. **Hand off.** Update manifest `completed_at_utc`. Code session ends.

### 7.1 Adaptation latitude

**Code adapts mid-capture if a projection consistently errors** (e.g., `EX_LADDER` triggers `TOO_MUCH_DATA`). Drop the offending projection from the combined call per §4.4 fallback. Note in manifest's `api_events`.

**Code adapts if Racing API auth fails or any endpoint errors persistently.** Stop the Racing API sub-loop for the affected race (or for the whole run if auth is wholly broken). Continue the Betfair sub-loop. Note in manifest's `api_events`. Question 5 may be partially or fully unanswered as a result.

**Code adapts if a chosen race scratches mid-capture.** Two options: (a) continue capturing the suspended/scratched market through CLOSED+45min anyway (data is still useful for the no-runners-state observations); (b) skip ahead to a replacement race if one exists. Code's call.

**Code adapts if disk pressure shows up.** If `/home/racing/` drops below 500MB free at any point, halt remaining captures gracefully, write a partial-run manifest, exit cleanly. Better to have 2-3 complete races than 4 partials.

**Code adapts if Saturday's card is unexpectedly thin.** If only 2-3 metros are running with adequate liquidity, capture those plus 1-2 best-available provincials. Note the substitution in the manifest.

**Code does NOT adapt the five questions.** Output structure delivers answers to all five, even if some answers are "field never populated" or "Racing API endpoint unreachable" (negative results are valid answers).

---

## 8. Cross-references and pre-reads

Code's required pre-reads in this Saturday session, in order:

1. **This brief** — `dr029/2_1_race_data/api_probe_brief.md` — full read.
2. **`surgical_fix_3_report.md` §6** — the empirical surprise that motivates the probe; ~150 lines.
3. **`source_review_report.md` §5.3** — the inferred-but-empirically-wrong API-shape assumptions; ~30 lines.
4. **`inspection_report.md` §F** — BSP/SP 0% population baseline; ~80 lines.

Reference-only on demand:
- **`source_review_brief.md`** — for source-review-style brief shape reference.
- **`surgical_fix_3_brief.md`** — for hard-limits / dirty-tree-handling pattern reference.
- **VPS source tree:** `/home/racing/racing-data-capture/betfair/client.py` (lines 196-280) for `list_market_book` calling pattern Code can mirror in the standalone probe script.

---

## 9. What success looks like

The probe succeeds if the report at session-end answers all five questions clearly. "Clearly" here means: a Session 40 reader can pick up the report and immediately know:

- Whether `r.sp.actual_sp` is reachable at all via the live API on AU markets, and if so under which conditions / at which phase.
- Whether harness or greyhound markets behave differently from thoroughbred.
- Which fields the API exposes that the snapshot writer ignores (with the `data_layer_current.md` §4-5 list as comparison anchor).
- Whether 1-second cadence captures more meaningful change than 30-second cadence does, and at which phases.
- How Betfair race/runner identity maps to Racing API race/runner identity (and through Racing API, to Sportsbet and Ladbrokes), with name-string deltas, scratching-latency observations, and start-time agreement noted.

The probe **does not** need to design Fix 4. Fix 4's brief comes after Session 40's analysis. The probe just delivers grounded data.

The probe **does not** need to fix anything. Even if the report shows `actual_sp` is reachable via projection X at phase Y, the probe doesn't add that to the orchestrator. Fix 4 brief, separately, decides whether and how.

The probe **does not** need to design the cross-source join. Question 5 surfaces what the alignment surface looks like; deciding the join algorithm is downstream work.
---

## 10. What failure looks like

The probe fails (operator-side, not Code-side) if any of these:

- VPS unreachable Saturday morning. Operator opens Chat session first to diagnose, runs probe Sunday or following Saturday.
- Betfair credentials invalid. Operator updates `.env`, retries probe.
- `racing-capture.service` crashed and not restarted. Operator restarts service, ideally before Code session opens, otherwise Code can do it as a precondition (this is the one allowed deviation from "no service restart" — service restart of `racing-capture.service` is permitted IF the service is already in failed state at probe start, because the probe wants the orchestrator running for credential-session-sharing reasons).
- All Saturday metros cancelled (heavy weather etc.). Operator reschedules.

The probe **partially fails** but still produces useful output if:

- Only 2-3 of 4 races complete capture. Report explicitly notes which races, what's missing.
- A specific projection consistently errors. Report notes the projection as "unobservable" rather than concluding it returns no fields.
- Rate-limit events force cadence reduction. Report notes the slower cadence and any analytical impact.

Code's job in partial-failure cases: write the report against what was captured, name the gaps, deliver.

---

## 11. Discipline notes

- **Source-review-style not surgical-fix-style.** Loose hand on exact code structure of `probe.py`. Code knows how to write a Python script. The brief specifies what to capture, what shape to write it in, and what hard limits to honour. Implementation details are Code's call.
- **Tight hard limits on isolation.** No edits to analytical-line files, no service restart (with the one named exception in §10), dedicated output directory, dirty-tree honoured.
- **Output is observation, not interpretation.** The report's §4 ("anything surprising") is the place for Code's interpretive notes. §1, §2, §3 are observation tables and time-relative-to-jump curves — facts only.
- **Negative results are valid.** If `r.sp.actual_sp` never populates across any phase across all four races, that's the answer to question 1. Don't try to hunt for it in unrequested places. Likewise: if Racing API auth fails entirely, question 5 partially answered is fine — the probe doesn't attempt heroics to make the cross-source data appear.
- **Write the report even if probe runs short.** Saturday card thin? 2 races completed? Write the report against 2 races. Note the gap. Forward-route to "follow-up probe needed for harness/greyhound" if relevant.
- **No mid-probe operator escalation.** Code runs the probe end-to-end without checking in. Operator-side enablement (per WIP §17 "Saturday API probe — operator setup") is set Friday evening; Saturday morning Code has everything it needs. If something blocks, Code logs to manifest and exits cleanly.

---

## 12. What happens after

- **Saturday afternoon ACST 2026-05-02:** probe runs end-to-end. Code session ends. Output at `dr029/2_1_race_data/api_probe_data/` (raw JSONL + manifest, both Betfair and Racing API streams) and `dr029/2_1_race_data/api_probe_report.md`.
- **Session 40 (next operator-Claude session after Saturday):** opens with the probe report as primary read. Triages findings. Decides Fix 4 shape. Drafts Fix 4 brief if scope is clear, or commissions a follow-up probe if open questions remain.
- **Fix 5 (venue harmonisation):** independent of probe; brief drafted in Session 40 or 41 once Fix 4 is sequenced.
- **§2.10 API-field-inventory:** substantially fed by §3.3 of the probe report. The §2.10 work item shrinks correspondingly.
- **PLACE markets capture (future probe):** the probe script is parameterised on `market_types` (per §4.1). A future pass adds PLACE by changing the parameter; no rewrite. Likely Session 41+ once Fix 4 lands and the analytical line is settled enough that PLACE-side observations are useful.
- **Cross-source join work (future):** §3.5 of the probe report surfaces the Betfair ↔ Racing API ↔ Sportsbet/Ladbrokes alignment surface. Designing the join algorithm itself is downstream of this probe; likely scoped after Fix 4 + §2.10 land, possibly under DR-029 §2.x or a new sub-section.

---

*End of brief.*
