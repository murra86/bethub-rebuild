# Launcher capture-data provisioning — investigation report

**Status:** READ-ONLY investigation complete. No files edited, no code changed,
no DB writes, no `capture.db` copy/mount. API access GET-only over the existing
8400 tunnel.
**Run:** 2026-06-29 ~19:45 ACST (DR-021 Adelaide anchor). Single bounded session.
**Grounding:** live read of the Mac launcher + v3 code at
`/Users/tim/Desktop/Projects/bethub-v3`, and live GET probes of the VPS racing
API at `http://127.0.0.1:8400` over `ssh -N -L 8400:localhost:8400
root@187.77.183.9` (PID 85200, confirmed listening).
**Governing DRs:** DR-033 (placings manual/analytical), DR-027/028 (two-DB
boundary, single integration point), DR-021 (Adelaide anchors).
**Bet-safety:** nothing in this pass touched settlement, money-movement,
lay-placement, or Betfair-auth WRITE paths. No stop condition tripped.

---

## 1. Understanding restatement (from the gate)

1. **Option B** gives `vps_client` an **API-backed read mode** — instead of
   opening `capture.db` as a local read-only SQLite file, it reads the canonical
   store via `http://localhost:8400/...` over the SSH tunnel, so the actual
   SQLite read happens *on the VPS* where the WAL is coherent. This is the
   DR-028 "single integration boundary, read by reference, no local copy" path.
2. **Log Past Bet needs from `capture.db`:** race discovery (date → venue →
   race number), a runner picker carrying `betfair_selection_id` + runner names,
   and win/lose result data. The §2c coverage table shows the lookup surface is
   supportable (selection IDs 63–100% across the recent window).
3. **Out of scope:** auto-confirming placings (2nd–4th) from `capture.db`
   (`finish_position` 0% on 8 of 15 recent dates) — deferred to the in-flight
   placings recovery; per DR-033 placings settle is a manual operator flag.

**One inconsistency carried in:** the brief and standing memory disagree on
which app is active (brief = v3; auto-memory = v2). The investigation prompt
names `bethub-v3` as app root and every anchor resolved there, so v3 is treated
as authoritative for this session. Not a code inconsistency — a doc-hygiene note
for the operator.

---

## 2. §A findings — link gap confirmed (with the exact 500 chain)

**Confirmed: the link is still missing and the 500 is real.** All §A anchors
resolve; the 500 mechanism is now traced end to end.

| Anchor (brief) | Resolves at | Status |
|---|---|---|
| `BetHub.command` exports Betfair mode + creds, no `BETHUB_CAPTURE_DB_PATH` | lines 75–78 | ✅ exact |
| `_connection.py` resolves a FILE path, opens `mode=ro` SQLite | logic spans 29–57 (brief said 29–45) | ✅ confirmed, minor drift |
| Race-lookup routes 500 with no path set | `bets.py` 925 / 938 / 952 | ✅ exact |
| `create_manual_bet` | `bets.py` 997–1014+ (`create_manual_bet_endpoint`) | ✅ confirmed |

**The launcher (`BetHub.command:75–78`)** exports only `BETHUB_BETFAIR_MODE` and
(in live mode) `BETHUB_BETFAIR_CREDENTIALS_PATH`. There is no
`BETHUB_CAPTURE_DB_PATH` anywhere in the script.

**The reader (`_connection.py`)** cannot speak HTTP as written. `_resolve_path`
(29–38) returns a `Path`; `_engine_for` (41–46) builds
`sqlite:///file:{path}?mode=ro&uri=true`. It is a file-only resolver — this is
precisely why Option B is a *code change*, not a config change.

**The exact 500 chain (newly traced this session):**
1. `bets.py:98 get_capture_db_path()` → `os.environ.get("BETHUB_CAPTURE_DB_PATH")`
   → returns **`None`** in the launched app.
2. The route (e.g. `lookup_meetings_endpoint:929`) calls
   `list_meetings(race_date, db_path=None)`.
3. `race_lookup.py:238 open_connection(None)` → `_resolve_path(None)` → env var
   also `None` → **raises `RuntimeError`** (`_connection.py:35–38`).
4. The surface's `try/except` catches only `OperationalError`
   (`race_lookup.py:240`). A bare `RuntimeError` is **not** caught → propagates
   out of the route → FastAPI returns **HTTP 500**.

So the 500 is unhandled-exception, not a mapped 503. This matters for §C item 5:
even the *current* failure mode is an ugly 500, and any API-backed rewrite must
deliberately map connection failure to the existing 503 envelope path, or it
will simply trade one silent 500 for another.

**No brief/code inconsistency at the Priority level in §A** — the diagnosis
holds. Only the `_connection.py` line range drifted (29–45 → logic actually runs
29–57).

---

## 3. §B findings — Option B feasibility, per-need endpoint mapping

**Headline: the 8400 API is live and healthy, but it is `race_id`-centric,
whereas the v3 client is human-field- and `event_id`-centric. Option B is *not*
a drop-in mode swap — every lookup surface needs re-mapping, and one core need
(past-date discovery) has no endpoint at all (see §C-1).**

`/health` returns `status:ok`, `db_path:/home/racing/.../capture.db`,
`betfair_last_snapshot:2026-06-29T10:12:06Z`, **`collector_active:false`**.

**The full live API surface (from `/openapi.json`) — 7 GET endpoints:**

```
GET /health
GET /racing/races/today
GET /racing/races/upcoming          (returned 0 items at probe time)
GET /racing/races/{race_id}
GET /racing/results/today
GET /racing/results/{race_id}
GET /racing/snapshots/{race_id}/latest
```

There is **no** meetings endpoint, **no** date-parameterised list, **no**
resolve-by-human-field, and **no** lookup-by-`betfair_win_market_id`.

### Per-need → endpoint mapping (verified against real JSON)

| Log Past Bet need | Current file/SQL surface | Nearest live API endpoint | Verdict |
|---|---|---|---|
| **Meetings for a date** (`list_meetings`) | SQL `GROUP BY venue WHERE date(race_date)=:d`, any date ≤365d | `/racing/races/today` only; must group client-side | ⚠️ **today only** — no date param (§C-1) |
| **Races for date+venue** (`list_races`) | SQL filter date+venue, any date | filter `/racing/races/today` by venue | ⚠️ today only |
| **Resolve date+venue+race# → identity+runners** (`resolve_race`) | single SQL row + runners, returns `betfair_win_market_id` + `selection_id`s | 2-step: `/racing/races/today` → find `id` → `/racing/races/{id}` | ⚠️ today only; needs 2 calls |
| **Runner picker** (`selection_id` + names) | `runners.betfair_selection_id` + `runner_name` | **`/racing/races/{id}`** `runners[]` carries both ✅ | ✅ available — but **NOT on `/snapshots/{id}/latest`** (see below) |
| **Win/lose results** (`race_results(event_id)`) | SQL keyed on `betfair_win_market_id` | `/racing/results/{race_id}` keyed on **`race_id`** | ⚠️ **re-keying needed** (§C-2) |

### Field-level confirmations (real responses)

- **`/racing/races/{id}`** carries: `id`, `venue`, `race_number`, `race_name`,
  `scheduled_start`, `betfair_win_market_id`, `capture_status`, and
  `runners[]` with `runner_name`, `runner_number`, `barrier`, `status`,
  `finish_position`, `margin_lengths`, `sp_fixed`, **`betfair_selection_id`**.
  → This single endpoint is a **superset** of what `resolve_race` returns. The
  picker should source from here.
- **`/racing/snapshots/{id}/latest`** carries `runner_id`, `runner_name`,
  `runner_number`, prices/ladders (`best_back/lay`, `back_depth`, `bsp_price`,
  `total_matched`…) — but **does NOT carry `betfair_selection_id`.**
  → **The brief's §B assumption is wrong:** "snapshots/{id}/latest MUST carry
  betfair_selection_id + runner names — CONFIRM IT DOES" → **it does not.** It is
  a price-ladder surface (the `bracketing`/`starting_price` analogue), not the
  picker source. The selection_id lives on race-detail and results instead. This
  is a **Priority correction to the brief** — but not a blocker, because the data
  is available on `/racing/races/{id}`.
- **`/racing/results/{race_id}`** and **`/racing/results/today`** carry
  `runners[]` with `finish_position`, **`result_status` (WINNER/LOSER/REMOVED)**,
  `margin_lengths`, `bf_bsp`, `sp_fixed`, `betfair_selection_id`, and the parent
  `betfair_win_market_id`. → win/lose is fully supportable.
  Observed on a SETTLED Betfair race (Maryborough, mkt `1.259538147`):
  `result_status` was `WINNER`/`LOSER` **while `finish_position` was `null`** —
  i.e. win/lose is knowable even when the ordinal hasn't landed. This is exactly
  the §2c placings gap, and it confirms manual win/lose is robust independent of
  the placings recovery.

### vps_client change surface (which methods move from file-read to API-call)

Every public surface in `clients/vps_client/v1/` opens `open_connection()` and
runs raw SQL. An API-backed Option B rewrites the **data-access layer of all of
them**, not just one:

| Module | Method(s) | Change |
|---|---|---|
| `race_lookup.py` | `list_meetings`, `list_races`, `resolve_race` | re-map to `/racing/races/today` + `/racing/races/{id}`; **lose arbitrary-date** (§C-1); resolve becomes a 2-call group-and-filter |
| `results.py` | `race_results` | re-map to `/racing/results/{race_id}`; **re-key event_id→race_id** (§C-2) |
| `runner_metadata.py`, `bracketing.py`, `starting_price.py`, `race_metadata.py`, `identifier_resolution.py` | various | not used by Log Past Bet, but share `open_connection`; an API mode must either cover them or be scoped to the lookup trio only — a DR-028 "single interface" decision the operator must make |
| `_connection.py` | `open_connection` | the integration seam — either gains an HTTP branch or a sibling transport is introduced |

**Return-shape mapping cost:** the API field names differ from the client's
internal column names (`bf_bsp` vs `sp_fixed`/`bsp`, `result_status` strings vs
the client's `WINNER`-counting dead-heat derivation, `runner_key` not present in
SQL, `betfair_win_market_id` returned in the results payload vs queried-by in
SQL). Each surface needs a translation layer from API JSON → the existing
pydantic return models (`MeetingSummary`, `RaceSummary`, `ResolvedRace`,
`RaceResults`). The envelope semantics (`FreshEnvelope` / `UnavailableEnvelope`
with `GENUINE_ABSENCE` / `NOT_IN_CAPTURE_WINDOW` / transport reasons) must be
re-derived from HTTP status + payload emptiness rather than SQL row presence.

**Net §B verdict:** Option B is feasible *for today's races* with moderate
mapping work, **but it cannot serve the feature's defining use case — logging a
bet that ran on a past date — without a VPS-API change** (a date parameter or
historical-meetings endpoint). That is a gap the brief's §3 deferred to "a small
read-only endpoint audit at lock time"; the audit is done, and the answer is
larger than a costing detail.

---

## 4. §C findings — gaps & limitations (the headline section)

### C-1. PAST-DATE DISCOVERY — the defining gap (Priority)

The feature is **"Log _Past_ Bet"**; `race_lookup.py:37–39` states the operator
"logs a race that already ran, **occasionally days ago**." The file/SQL path
supports this directly: `list_meetings`/`list_races`/`resolve_race` accept **any
`race_date`** and filter `WHERE date(race_date)=date(:race_date)` within a
365-day window (`CAPTURE_WINDOW_DAYS`).

**The API cannot do this:**
- `/racing/races/today` ignores a `?date=` parameter — `GET .../today` and
  `GET .../today?date=2026-06-20` both returned **identical 460-race lists**.
- `/racing/races?date=…`, `/racing/meetings`, `/racing/races/by-date/…`,
  `/racing/results?date=…` all returned **404**.
- `/racing/races/upcoming` returned **0** items at probe time.

→ Via the API, **past-date discovery is impossible unless the `race_id` is
already known** (only `/racing/races/{race_id}` accepts an arbitrary id). The
Log Past Bet flow *starts* from date+venue+race-number with no id in hand, so a
straight Option B swap reduces the feature to **today's races only** — a
functional regression against the current SQL design and against the feature's
stated purpose.

**Operator-relevant consequence for the A-vs-B lock** (stated, not decided):
Option A (SSHFS file) preserves arbitrary-date lookup because it runs the same
365-day SQL. Option B preserves it only if the VPS API gains a date-aware
discovery endpoint. So the past-date requirement is the single sharpest
discriminator between the two paths.

### C-2. event_id ↔ race_id re-keying (Medium)

The client's results contract is keyed on `event_id` (= `betfair_win_market_id`).
The API's results endpoint is keyed on the internal `race_id`. There is **no
endpoint to resolve a `betfair_win_market_id` → `race_id`.** Within a single Log
Past Bet flow this is bridgeable (resolve_race's underlying `/racing/races/{id}`
call already knows the `race_id` and could carry it forward), but it breaks the
current clean `race_results(event_id)` signature and any caller that holds only
the win-market stamp. A mapping/threading decision the rewrite must make
explicitly.

### C-3. Empty-runner edge (~12.5% of stamped races) — gracefully detectable

Both layers expose enough to handle this without a hard error:
- API: `/racing/races/today` carries `n_runners` (observed `0` on the first
  item, "Stratford On Avon"); `/racing/races/{id}` returns `runners: []`.
- Client: `resolve_race` filters `if row.betfair_selection_id is not None`, so a
  matched-but-unsnapshotted race yields `runners=[]` inside a `FreshEnvelope`.
→ The build can detect this (empty `runners`) and show "no runners captured for
this race" rather than an empty picker, as §4 of the brief wants. **The data
supports graceful handling; it's a UX requirement, not a blocker.**

### C-4. Harness/greyhound/intl mislabel-as-thoroughbred (Medium, pre-existing)

**Neither layer distinguishes race code.** The client **hardcodes**
`RaceCode.THOROUGHBRED` in all three lookup surfaces (`race_lookup.py:251, 289,
361`), and `bets.py:969` documents this as known (W1 Finding F2 — "capture.db
distinguishes no code today… always thoroughbred"). The API confirms it from the
other side: **no `code`/`race_type` field exists** on any races or results
payload, and `/racing/races/today` is visibly contaminated — it included UK
tracks ("Stratford On Avon") and AU "Jump Out"/trial races (Cranbourne) mixed
with real thoroughbred meetings. → Option B does **not** improve this; the API
exposes nothing to filter on. The mislabel is a pre-existing data-layer gap the
provisioning choice neither fixes nor worsens. Flag for the recovery/data side,
not this brief.

### C-5. Tunnel dependency & failure behaviour (Medium)

- **Today (file path):** missing path → `RuntimeError` → **unhandled 500**
  (§A). A down tunnel under Option A (SSHFS) would surface as a file/IO error;
  whether it maps cleanly is untested (SSHFS adds its own failure modes — the
  brief's §3 Option A fragility note).
- **Under Option B:** the route layer already has the right scaffolding —
  `_list_or_empty` (`bets.py:903`) and `_raise_for_lookup_failure` (`974`) map
  **transport-class** `UnavailableEnvelope` reasons to **503** (retryable),
  reserving 404 for genuine absence. **But** that only works if the new API
  client catches connection/timeout errors and returns a transport-flavoured
  `UnavailableEnvelope` — mirroring how `map_operational_error` wraps
  `OperationalError` today. If the rewrite lets `requests`/`httpx` exceptions
  propagate raw, it reintroduces the silent 500. → **Clean-failure requirement:
  map tunnel-down to 503, not 500.** During this session the tunnel was briefly
  unresponsive on first contact (curl exit 28 on `localhost`/IPv6) and answered
  on retry via `127.0.0.1` — a real reminder that the link is flaky enough to
  need explicit handling.

### C-6. `collector_active: false` confirmed (Observation only)

`/health` reports `collector_active:false` **now**, matching the S202 audit;
last Betfair snapshot `2026-06-29T10:12:06Z` (~19:42 ACST), bookmaker
`10:08:33Z`. **Impact on Log Past Bet: negligible** — the feature reads
*already-stamped past races*, and the snapshot data needed (selection_id, names,
win/lose) is written at/after the race, not by the live collector now. A dormant
collector affects *forward* freshness (and the placings recovery), not
retrospective lookup of races already in the store. Per the prompt, the
collector itself is out of scope; recorded as observation.

### C-7. Auth / error-handling assumptions introduced by the API path

- The 8400 API has **no authentication** and binds to `localhost` via the tunnel
  — security rests entirely on the SSH key forwarding. Option B introduces no
  new credential, but does make app correctness depend on the tunnel being up
  *and* on the operator's SSH session.
- New error taxonomy the client must own: HTTP timeouts, connection refused
  (tunnel down), 404 (unknown race_id) vs 200-with-empty (no runners), and
  partial/late JSON. None exist on the file path. These must be folded into the
  existing envelope mapping (C-5) or they become 500s.
- The launcher must guarantee the tunnel is up before the app needs it (brief
  §3 "Against" for Option B) — today nothing in `BetHub.command` starts or
  checks the tunnel.

---

## 5. §D findings — launcher-fix anchor check (read-only, not fixed)

| Fix | Anchor (brief) | Resolves at | Confirmed shape |
|---|---|---|---|
| **F9** login back-off resets on restart | `_auth_betfair.py:118–120, 54–56` | ✅ exact | in-memory → disk-persist is right |
| **F10** double-session via port override | `BetHub.command:16` | ✅ exact | single-session lock is right |
| **rebuild-if-source-newer** | `BetHub.command:67` | ✅ exact | rebuild-on-newer is right |

**F9 — confirmed and sound, with one nuance.** The throttle state
(`_consecutive_failures`, `_next_attempt_at`, `_killed`) is set in
`__init__` as plain instance attributes (`_auth_betfair.py:112–120`), guarded by
an in-memory lock — **wiped on every process restart**, exactly as the brief
says. The cool-off schedule is 30m/1h/2h/4h (`45–50`) with kill-at-5
(`MAX_LOGIN_ATTEMPTS`, `56`). Disk-persistence of the back-off timer is the right
shape. **Nuance for the operator:** lines 53–56 document that the *killed* state
is deliberately cleared by a restart ("No auto-recovery — only a fresh provider
(v3 restart) clears it"). If F9 persists `_killed` to disk too, it changes that
contract (a restart would no longer clear the kill). The operator should decide
whether F9 persists **only the back-off timer** (`_next_attempt_at` /
`_consecutive_failures`) or **also the kill-state** — the safe-against-lockout
goal argues for persisting the timer; persisting `_killed` is a separate policy
call. Worth an explicit line in the execution brief.

**F10 — confirmed.** `PORT="${BETHUB_LAUNCH_PORT:-8787}"` (`BetHub.command:16`)
lets a second instance bind a different port → two concurrent Betfair
sessions/streams. The launcher's shutdown logic (`OWNED_PORT_PIDS`, `39–44`,
`104–105`) is explicitly written to *not* reap a second BetHub, so the door is
genuinely open. A single-session lock is the right shape.

**rebuild-if-source-newer — confirmed.** `BetHub.command:67`
`if [ ! -f "$REPO_ROOT/ui/web/dist/index.html" ]` builds **only when the bundle
is absent**; a source-newer-than-dist case serves stale (the S172 BetLog trap).
Rebuild-when-source-newer is the right shape (e.g. a `find -newer` guard).

**F12** (TEMPORARY_BAN-port + shutdown-logout) — **not tripped over**; not
investigated per scope.

---

## 6. Open questions for operator-Claude triage

1. **(Priority) Past-date discovery (C-1).** Option B as currently scoped serves
   *today only*. Does the operator (a) require a VPS-API change to add a
   date-aware discovery endpoint before Option B can be locked, (b) accept
   Option A (SSHFS) specifically because it preserves 365-day lookup, or (c)
   narrow the feature to "today/recent" entry? This is now the central A-vs-B
   discriminator, beyond the WAL-correctness trade the brief framed.
2. **(Priority) Brief correction (§B):** the picker source is `/racing/races/{id}`,
   **not** `/racing/snapshots/{id}/latest` (snapshot carries no
   `betfair_selection_id`). Confirm the execution brief is updated.
3. **event_id↔race_id re-keying (C-2):** is the rewrite allowed to thread
   `race_id` through the Log Past Bet flow, or must `race_results(event_id)`
   keep its current signature (which would need a new VPS lookup endpoint)?
4. **DR-028 scope of the API mode:** does the API-backed transport cover *all*
   `vps_client` surfaces (one interface) or only the lookup trio + results
   (minimal)? The "single integration point" principle pulls toward all.
5. **Tunnel lifecycle (C-5/C-7):** should `BetHub.command` own starting/health-
   checking the 8400 tunnel, and must the API client map tunnel-down to 503 (not
   500) as an explicit acceptance criterion?
6. **F9 kill-state policy (§D):** persist back-off timer only, or also `_killed`
   (which changes the documented "restart clears kill" contract)?
7. **F12 in or out** of this launcher pass (carried from brief §6.3).

---

## 7. Self-assessment

- **Anchors that had drifted:** only one — `_connection.py` "29–45" understates
  the resolver+engine logic, which spans 29–57 (`_resolve_path` 29–38,
  `_engine_for` 41–46, `open_connection` 49–57). All `bets.py` route anchors
  (925/938/952), the launcher anchors (16/67/75–78), and the `_auth_betfair.py`
  anchors (54–56/118–120) resolved exactly.
- **One brief assumption corrected as a finding** (not just drift): §B's claim
  that `/racing/snapshots/{id}/latest` carries `betfair_selection_id` is false;
  it carries price-ladder data only. The picker data lives on
  `/racing/races/{id}`. Flagged Priority.
- **One discovery beyond the brief's framing:** the past-date gap (C-1) is a
  feature-level limitation of Option B, larger than the "small endpoint audit"
  the brief anticipated. Surfaced as the headline gap and Q1.
- **Tunnel flakiness:** first `/health` probe on `localhost` timed out (curl 28,
  likely IPv6/stale-channel); `127.0.0.1` answered on retry. Treated as a live
  signal for C-5, not a blocker.
- **`upcoming` returned 0** and **today is trial-heavy** (Cranbourne Jump Outs,
  UK tracks) — late-ACST/off-season effects. I located a genuine SETTLED
  Betfair-backed race (Maryborough, mkt `1.259538147`) to confirm the
  populated-field shapes, so the field-level confirmations rest on real data,
  not empty fixtures.
- **What didn't fit / not done (correctly out of scope):** did not enumerate the
  non-lookup `vps_client` surfaces' API mappings in detail; did not test Option
  A SSHFS behaviour (no mount permitted); did not probe write paths; did not pick
  A vs B or write the execution brief. The session fit comfortably within bounds.
