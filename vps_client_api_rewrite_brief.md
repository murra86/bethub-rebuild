# Mac `vps_client` API rewrite — brief (Brief 2)

**Status:** **LOCKED — re-drafted against DR-034 and locked by the
operator (S208).** Supersedes the S205 pre-DR-034 draft and the S208 held
draft in place. The §12 calls are resolved (operator accepted the
recommendations with two added requirements: the pinned VPS-completeness
dependency in §5.2 and the drop-counter in §5.2/§8). sha256 of the locked
file is recorded in the S208 session record at close. Drafted unattended
by the S208 headless runner; locked in-session after operator review.
**Drafted:** 2026-06-30 10:05 ACST (S205, original). **Re-drafted:**
2026-06-30 13:35 ACST (S208, headless runner, DR-021 Adelaide anchor) —
re-grounded on the now-live VPS enrichment + the locked DR-034 identity
model.
**Grounding:** live read-only of the Mac `vps_client` source at
`/Users/tim/Desktop/Projects/bethub-v3/clients/vps_client/v1/`
(anchors re-verified this session — `race_lookup.py` `_parse_iso:186`,
`list_meetings:222`, `list_races:259`, `resolve_race:297` all present
and current); the S204 live-endpoint report (`vps_date_endpoint_report.md`);
the S205 enrichment report (`vps_endpoint_enrichment_report.md` — the
live list payload + the by-market results route); the S202 investigation
report (`launcher_capture_provisioning_investigation_report.md`); and
DR-034 (`decisions.md` §DR-034). No fresh live VPS probe run this draft —
the S204/S205 reports' empirical payload samples are authoritative; a
re-probe at lock time is noted in §7.
**Governing DRs:** **DR-034 (canonical race identity — the Betfair WIN
market is the spine; capture `races.id` is a per-fragment row id, never
an identity; fragments resolve by completeness, not row id)**, DR-028
(single integration boundary — no caching, no denormalisation, one
defined interface), DR-027 (two-DB), DR-033 (placings analytical /
settlement Betfair-only), DR-032 (Betfair canonical reference — a
Betfair market is required at logging time), DR-021 (Adelaide anchors),
DR-031 (v3 stack — `uv`, httpx).
**Bet-safety:** analytical/read-path only. This brief re-points a
read-only race-lookup client and hardens the launcher. It does **not**
touch settlement, money movement, lay placement, or any live-betting
write path. The F9 launcher fix is *account-safety adjacent* (it
prevents a Betfair login lockout) but adds no betting write path.

---

## 0. What DR-034 changes for this brief (read first)

The S205 draft of this brief predates DR-034 and assumed the VPS list
endpoint was too thin (it proposed a "Brief 1.1" to enrich it). Two
things have moved since:

1. **The enrichment already landed (S205, `vps_endpoint_enrichment_
   report.md`).** The live `GET /racing/races?date=D` payload now carries
   13 fields per race — including `scheduled_start`,
   `betfair_win_market_id`, `state`, and `n_runners`. So the old §12
   call-1 ("insert Brief 1.1 or absorb the thinness?") is **resolved by
   facts on the ground** — the list is already rich enough for Candidate
   B and for the lookup trio. There is **no VPS dependency left** for
   Brief 2 on that axis.

2. **DR-034 is locked, and it reframes the whole lookup.** The capture
   store fragments one physical race into many rows — **87% of
   market-bearing rows share their `betfair_win_market_id` with ≥1 other
   row** (`vps_endpoint_enrichment_report.md` §4). DR-034 locks the
   identity model: the **Betfair WIN market id is the spine**; the
   capture `races.id` is a per-fragment row id and **must never be used
   as a race identity**; among fragments sharing a market id, the
   authoritative one is **the most-complete fragment** (resolved status →
   most runners → results present → most recent), **not the lowest row
   id**.

**The consequence for this brief is the load-bearing change.** Both the
shipped by-market results route (`ORDER BY id` → returns the empty
PENDING 0-runner shell in the dominant case, demo'd live at
`by-market/1.259530858` → id 2652588, 0 runners) **and** the current
file-path client SQL (one `RaceSummary` per row, no collapse) violate
DR-034: they would show duplicate races in the picker and resolve the
*wrong* (empty) fragment for runner detail. So **the rewrite must
collapse fragments by `betfair_win_market_id` and resolve by
completeness at read time** — this is DR-034 stance 4's "collapse
fragments under the market id at read time", applied to the Log-Past-Bet
lookup path.

**This is NOT the parked stance-4 remediation.** S207 parked the *write-
side / analytical-deficit* fragment-collapse (enforce identity at write
time; collapse the placings deficit) as downstream of restarting burn.
That stays parked. What this brief does is the **narrow read-time
collapse the lookup needs to return a non-empty runner set at all** —
without it, Log Past Bet returns an empty picker in ~87% of cases. The
two are different jobs; this one is a Brief-2 correctness requirement,
not the parked remediation.

---

## 1. What this brief is and is not

A **surgical rewrite + launcher-hardening** brief, single bounded Code
session. It rewrites the data-access layer of the Log-Past-Bet lookup
surfaces in `vps_client` to read the live VPS racing API over the 8400
tunnel instead of opening `capture.db` as a local file (which the
launched app never provisions — the standing HTTP-500 since S189),
**applies the DR-034 read-time fragment-collapse to the lookup**, and
closes three launcher items in the same pass.

- Surprises become **findings in the report**, not silent fixes or
  scope expansion.
- Remediation of anything outside the named anchors routes to
  operator-Claude triage, not Code's report.
- This is one Code session. If it does not fit, that is a finding —
  Code stops and reports, it does not continue past budget.

**It is NOT:** a settlement-worker change; a `capture.db` write or copy
or mount; a v2 change; a change to the recovery; a promo-seed or
cash-modal change; a rewrite of the non-lookup `vps_client` surfaces
(see §9); the parked DR-034 write-side / analytical-deficit fragment-
collapse remediation; a VPS-side change (the enrichment Brief 2 needs is
already live — Code invents no VPS endpoints).

---

## 2. Why this work exists

The "Log Past Bet" late-entry flow (race lookup → pick runner → log) is
the only v3 feature that reads the analytical store, and it is
**non-operational in the launched app**: every race lookup returns
HTTP 500 because the launcher never sets `BETHUB_CAPTURE_DB_PATH` and
the reader (`_connection.py`) can only open a local file — there is no
`capture.db` on the Mac and none coming. The locked provisioning path
(`launcher_capture_provisioning_brief.md`, S202) is **Option B**: read
the canonical store through the VPS API over the existing tunnel, where
the SQLite read happens on the VPS and the WAL is coherent — the DR-028
single-boundary path that survives W16 cutover. The S204 date endpoint
and the S205 enrichment built and enriched that API. This brief is the
Mac half: re-point the client at that API **and** make it key races by
the DR-034 spine.

The client date logic is the **locked Candidate B contract**
(`race_date_semantics_report.md` §4): `race_date` is not a clean
real-world-day key (two writers, opposite skews; ~27% off ±1, VIC
~50/50), so a naive single `?date=D` silently misses ~¼ of a day's
races. Candidate B fetches a ±1-day window and refines by the trustworthy
UTC `scheduled_start`. Layered on top of Candidate B is the DR-034
collapse: within the kept set, fold fragments sharing a
`betfair_win_market_id` into one logical race.

---

## 3. Pre-reads

**Required (read before editing):**
- `/Users/tim/Desktop/Projects/bethub-rebuild/vps_client_api_rewrite_brief.md`
  (this brief).
- `/Users/tim/Desktop/Projects/bethub-rebuild/decisions.md` §DR-034
  (the identity model — the load-bearing input; read it before §5).
- `/Users/tim/Desktop/Projects/bethub-v3/clients/vps_client/v1/race_lookup.py`
  (the lookup trio + current return models + `_parse_iso:186`).
- `/Users/tim/Desktop/Projects/bethub-v3/clients/vps_client/v1/results.py`
  (`race_results`).
- `/Users/tim/Desktop/Projects/bethub-v3/clients/vps_client/v1/_connection.py`
  (the transport seam being repurposed).
- `/Users/tim/Desktop/Projects/bethub-v3/clients/vps_client/v1/envelope.py`
  + `_errors.py` (envelope shapes + `VPS_UNREACHABLE` / `CAPTURE_DB_LOCKED`).
- `/Users/tim/Desktop/Projects/bethub-v3/ui/api/routers/bets.py` lines
  ~880–1040 (the route bridge: `_list_or_empty`, `_raise_for_lookup_
  failure`, `CaptureDbPathDep`, `create_manual_bet_endpoint`).
- `/Users/tim/Desktop/Projects/bethub-v3/launcher/BetHub.command`
  (launcher — F10 line 16, rebuild line 67, env exports 75–78).
- `/Users/tim/Desktop/Projects/bethub-v3/.../_auth_betfair.py` (F9 —
  back-off state ~112–120, schedule ~45–50, kill ~53–56; Code confirms
  the path at session start).

**Reference-only (read on demand, not required):**
- `/Users/tim/Desktop/Projects/bethub-rebuild/vps_endpoint_enrichment_report.md`
  — §1 the live list payload (13 keys incl. `betfair_win_market_id`),
  §2 the by-market route behaviour, §4 the 87% duplication anatomy.
- `/Users/tim/Desktop/Projects/bethub-rebuild/vps_date_endpoint_report.md`
  — the live `?date=` endpoint + the 3 `scheduled_start` encodings.
- `/Users/tim/Desktop/Projects/bethub-rebuild/race_date_semantics_report.md`
  — §4 Candidate B, §3 the 3 `scheduled_start` encodings.
- `/Users/tim/Desktop/Projects/bethub-rebuild/launcher_capture_provisioning_brief.md`
  + `..._investigation_report.md` — locked path, picker §B correction,
  F9/F10/rebuild anchors.
- `/Users/tim/Desktop/Projects/bethub-rebuild/BETHUB_DATA_REFERENCE.md`
  §B — the identity & reconciliation model.

---

## 4. System access

- **Mac filesystem, read-write**, scoped to the named anchors in §5 only
  (the `vps_client/v1/` lookup surfaces, the launcher, the auth back-off
  module). No edits outside named anchors.
- **`bethub-v3` git:** committer identity is set (S198); the repo is
  meant to be clean. Code commits the rewrite as one checkpoint **after**
  it lands and tests pass (per the S198 git-hygiene rule). If the tree is
  unexpectedly dirty at session start, that is a finding — surface it,
  do not commit over it.
- **VPS API, read-only GET over the tunnel** for the §7 live
  verification only (`ssh -N -L 8400:localhost:8400 root@187.77.183.9`,
  then `http://127.0.0.1:8400/...`). No VPS file edits, no service
  restart, no git ops on the VPS. `capture.db` is never opened, copied,
  or mounted from the Mac.
- **Tests:** `uv run pytest` (the repo is a `uv` project; bare `python3`
  lacks httpx — S160).
- All report timestamps Adelaide local (ACST/ACDT) per DR-021.

---

## 5. Substantive scope

> **No VPS dependency.** Unlike the S205 draft, §5 carries no "Brief 1.1"
> gate: the enriched list payload (`scheduled_start`,
> `betfair_win_market_id`, `state`, `n_runners` per race) is **already
> live** and is everything the client needs. The DR-034 collapse below is
> done **client-side**, from fields already on the list payload — no
> extra fetches for discovery, and the broken `by-market` results route
> is **not used** (see §5.6). This is the §12 call-1 recommendation,
> **resolved at S208 lock: client-side collapse, Brief 2 ships
> standalone.** (Had the operator chosen the VPS collapse instead,
> §5.2/§5.4/§5.6 would change — that path is flagged inline but is not
> the chosen one.)

### 5.1 — The transport seam (`_connection.py`)

Today `_connection.py` resolves a file path and builds a read-only
SQLite engine. Repurpose it into the **single HTTP transport** for the
lookup surfaces:

- Add a small API client (httpx) with base URL from
  `BETHUB_CAPTURE_API_URL`, defaulting to `http://127.0.0.1:8400`. Keep
  the existing `db_path`/path-resolution helpers callable by the
  non-migrated surfaces (§9) so they are untouched.
- One GET helper that: issues the request with a bounded timeout
  (~5 s connect / ~10 s read); on `httpx.HTTPError` / timeout / connect
  failure returns a transport signal that the calling surface converts
  to `UnavailableEnvelope(reason=VPS_UNREACHABLE, retry_after=60)`; on
  HTTP 5xx likewise; on HTTP 422 raises a programming-error finding (the
  client built a bad request — should not happen); on 200 returns parsed
  JSON.
- This is the DR-028 single boundary: one defined interface, by
  reference, no local copy, no cache.

### 5.2 — The DR-034 collapse helper (new — used by §5.3 / §5.4)

A shared client-internal helper that takes the Candidate-B kept set
(§5.5) of raw race rows and **folds fragments into logical races**:

1. Partition the kept rows by `betfair_win_market_id`.
2. Rows **with** a market id collapse to **one logical race per market
   id**. The authoritative fragment within a group is the
   **most-complete** one, by the DR-034 ordering: resolved/`state`
   precedence (settled > pending) → highest `n_runners` → results
   present → most recent (`scheduled_start`, then `id` only as a final
   tie-break). Carry that fragment's `id` forward as the
   **detail-fetch handle** (the `id` used for the one runner/results
   GET in §5.4 / §5.6) and its metadata (`venue`, `race_number`,
   `scheduled_start`) as the logical race's display fields.
3. Rows **with no market id** (DR-034 stance 3 — second-class,
   analytical-only) are **not loggable** (DR-032 §6 requires a Betfair
   market at logging time; DR-033 settles off Betfair). **Drop them from
   the lookup** (operator call 2, resolved — you cannot log a bet on
   them). **Instrument the drop (added S208).** Count, per lookup call,
   how many rows are dropped — both the no-market drops here and,
   separately, any market-bearing group that collapses to a still-empty
   logical race — and surface that count on the lookup's structured log
   line. The expected no-market floor tracks the known ghost/unfillable
   rate (~0.3–1.9%); a drop count materially above that floor is an early
   data-regression signal (enrichment gone stale, market ids dropping
   out), not a silent swallow. The counter is observability only — it
   changes no lookup behaviour.

This helper is the heart of the DR-034 alignment. It is pure
client-side reconciliation of one boundary's response (no cache, no
stored copy, no second integration point — DR-028 clean).

**Dependency (pinned — operator call 1, S208).** Doing the collapse
client-side means the completeness ordering leans entirely on the
VPS-supplied enrichment fields (`n_runners`, `state`, results-present)
staying present and accurate on the list payload. This is the accepted
trade for shipping Brief 2 standalone with no further VPS work. Failure
mode to record: if those fields are later dropped/renamed or go stale,
the "most-complete fragment" pick silently degrades back toward the
row-order bug this collapse exists to fix. The guards already in this
brief cover it — the §5.2 step-3 drop-counter (catches an empty-collapse
spike at runtime) and the mandatory §7 collapse test (asserts the
15-runner fragment wins over the 0-runner shell). No new behaviour here:
this is a recorded standing assumption of the lookup, surfaced so any
future VPS enrichment change is checked against it before it ships.

### 5.3 — `list_meetings(race_date)` / `list_races(race_date, venue)` → API

- `list_meetings`: drive from the Candidate-B union (§5.5), run the
  §5.2 collapse, then group the logical races by `venue`; emit one
  `MeetingSummary` per venue with `race_count` = count of **logical**
  races (post-collapse, so no duplicate inflation), `state` from the
  most-complete fragment, `code` = `RaceCode.THOROUGHBRED` (unchanged —
  capture.db distinguishes no code, W1 F2). Keep the existing
  `_outside_capture_window` pre-check (pure date math, no DB) →
  `NOT_IN_CAPTURE_WINDOW`. Empty union → `GENUINE_ABSENCE`.
- `list_races`: filter the collapsed logical races to `venue`; emit one
  `RaceSummary` (the **client-internal** model — `{race_number,
  jump_time, code, win_market_id}`) per **logical** race. `jump_time` =
  parsed `scheduled_start` (via the §5.5 parser) from the most-complete
  fragment; `win_market_id` = `betfair_win_market_id`. No more
  one-row-per-fragment duplication (the bug the pre-DR-034 SQL and the
  S205 draft both carried).

### 5.4 — `resolve_race(race_date, venue, race_number)` → API

Two-step. From the collapsed logical races (§5.2) find the one whose
`venue` + `race_number` match and whose `scheduled_start` lands on
Adelaide day D (§5.5 disambiguates the same venue+number on adjacent
days — the correctness-critical case). Then `GET /racing/races/{id}`
**using the most-complete fragment's `id`** (the §5.2 detail-fetch
handle — *not* the lowest id, *not* an arbitrary fragment) for the
runner set. Map `runners[]` (`betfair_selection_id`, `runner_name`,
`barrier`, `scratched`) → `ResolvedRunner`, dropping rows with null
`betfair_selection_id` (current behaviour). No win-market id →
`GENUINE_ABSENCE` (the no-market case is already dropped at §5.2, so
this path resolves only spine races). `event_id` = `win_market_id` =
`betfair_win_market_id` (W1 F1 echo, unchanged). The runner detail fetch
is the one intrinsic detail call (runners are never on the list
payload), and resolving it against the most-complete fragment is exactly
what stops the empty-picker failure.

### 5.5 — Candidate B date logic + the `scheduled_start` parser

Implement the locked contract as a shared helper feeding §5.2–§5.4:

1. For target Adelaide day **D**, call `GET /racing/races?date=` for
   **D−1, D, D+1** and union the rows.
2. **Keep** a row when its `scheduled_start` (UTC → Adelaide) falls on D.
3. For a row with **empty** `scheduled_start`, fall back to keeping it
   only if its stored `race_date == D`.

(The §5.2 collapse runs **after** this keep-filter, on the kept set.)

**Parser (load-bearing — replaces the current `_parse_iso:186`).** The
current `_parse_iso` does `replace("Z","+00:00")` → `fromisoformat`,
which **silently returns `None` on the 7-digit-fraction encoding**
(`…T13:00:00.0000000Z`) — a latent bug today (jump_time lost). The new
parser must accept all three live UTC encodings: `Z`+3-digit millis,
`Z`+7-digit fraction (**truncate the fraction to ≤6 digits before
`fromisoformat`**), and `+00:00` no-fraction. All are UTC; once parsed,
convert to Adelaide via `to_adelaide`. Centralise it (one parser, used
by both `race_lookup` and `results`).

**DST caveat (declared, carried from the report):** the UTC→Adelaide
conversion uses real Adelaide tz (ACST/ACDT via `zoneinfo`), so it is
DST-correct. Near-midnight summer edge rows remain the one imprecise
case; not fixed here.

### 5.6 — `race_results(event_id)` → API (re-keyed via the resolved fragment)

The client keys results on `event_id` (= `betfair_win_market_id`). The
VPS exposes two results routes: `/racing/results/{race_id}` (by internal
row id) and `/racing/results/by-market/{betfair_win_market_id}`. **The
by-market route is broken per DR-034** — it uses `ORDER BY id` and
returns the empty PENDING shell in the dominant duplicate case
(`vps_endpoint_enrichment_report.md` §2/§4). **Do not use it.**

RECOMMENDED path (no VPS change): within the Log-Past-Bet flow,
`race_results` is reached *after* `resolve_race` has already identified
the **most-complete fragment's `id`** (§5.2/§5.4). Call
`/racing/results/{that_id}` — the by-row-id route, which is correct.
Thread the resolved fragment id through the flow so `race_results`
consumes it rather than re-deriving from the market id. Map `runners[]`
(`finish_position`, `result_status` WINNER/LOSER/REMOVED,
`margin_lengths`, `betfair_selection_id`, `bf_bsp`/`sp_fixed`) →
`RunnerResult`; preserve the dead-heat derivation (count of WINNER
rows), `market_voided` (all REMOVED), and the `NOT_YET_CAPTURED`
heuristic (no settled rows).

*(If the operator chooses the VPS-side collapse instead — §12 call 1 —
the by-market route is fixed server-side to resolve-by-completeness and
`race_results(event_id)` keeps its market-id signature with no fragment
threading. Flagged as the alternative.)*

### 5.7 — Transport failure → 503 (correctness requirement)

The route bridge already maps transport-flavoured envelopes to 503
(`_list_or_empty` 503s on non-terminal reasons; `_raise_for_lookup_
failure` 503s on `VPS_UNREACHABLE`/`CAPTURE_DB_LOCKED`, 404 on terminal).
So **no route change is needed** — the entire requirement is that the
rewritten surfaces **never let a raw httpx exception escape**: every
transport/timeout/5xx becomes `UnavailableEnvelope(VPS_UNREACHABLE)`.
If a raw exception escapes, it propagates → 500, re-introducing exactly
the silent failure S189 flagged. Verify with a tunnel-down test (§7).

### 5.8 — Launcher fixes (same pass)

Per the locked provisioning brief §6 (policies already decided):

- **Tunnel env:** default base URL is `http://127.0.0.1:8400`, so no env
  is strictly required, but the launcher should export
  `BETHUB_CAPTURE_API_URL` explicitly for clarity (and drop the dead
  `BETHUB_CAPTURE_DB_PATH` expectation). **Tunnel auto-start/health-check
  is a §12 call — default is NOT in this pass.**
- **F9 (MED-HIGH) — login back-off survives restart.** Persist **only
  the back-off timer** (`_next_attempt_at` / `_consecutive_failures`) to
  disk, restored on init; **do NOT persist `_killed`** (a v3 restart must
  still clear a Betfair login kill — the documented contract, locked
  S202 §6.3). Atomic write; corrupt/missing file → treat as no back-off.
- **F10 (MEDIUM) — single-session lock.** `BETHUB_LAUNCH_PORT`
  (`BetHub.command:16`) lets a second instance start → two concurrent
  Betfair sessions. Add a single-instance lock (e.g. a pidfile/flock) so
  a second launch refuses rather than opening a parallel session.
- **rebuild-if-source-newer.** `BetHub.command:67` builds only when
  `dist/index.html` is absent → stale served bundle after every rebuild
  (the S172 BetLog trap). Rebuild when source is newer than `dist`
  (e.g. a `find -newer` guard).
- **F12 is OUT** (locked S202 §6.4).

---

## 6. Sequencing within session

1. §5.1 transport seam + §5.5 parser/date helper first (everything
   depends on them).
2. §5.2 collapse helper next (the lookup trio depends on it).
3. §5.3 → §5.4 lookup trio.
4. §5.6 results (consumes the §5.4 resolved fragment id).
5. §5.7 verify the 503 wrap holds across all four surfaces.
6. §5.8 launcher fixes (independent of the client work — may be done
   first or last; they share no anchors).
7. Tests, then the single checkpoint commit.

Code may deviate where a different order is cleaner, and says so in the
report.

---

## 7. Empirical verification

- **Unit/contract tests** (`uv run pytest`): the existing
  `tests/clients/vps_client/v1/` suite drove the file-path surfaces; it
  must be re-pointed/rewritten to drive the HTTP path (httpx mock or a
  fixture API). Capture before/after pass counts. New tests required:
  the 3-encoding parser (incl. the 7-digit-fraction case that currently
  returns `None`); the Candidate B window+refine (a VIC-style row filed
  under the wrong `race_date`); **the DR-034 collapse — a market id with
  ≥2 fragments (one PENDING 0-runner shell + one SETTLED 15-runner),
  asserting the lookup returns ONE logical race and resolves the
  15-runner fragment, not the shell**; and the transport-down →
  `VPS_UNREACHABLE` → 503 path.
- **Live smoke over the tunnel (read-only GET):** pick a recent populated
  date with a known duplicate market (e.g. `1.259530858`, Emerald,
  06-28/06-29 — the enrichment report's worked example), run one real
  Log-Past-Bet resolve end to end, and confirm it returns the
  **most-complete fragment** (runners present), not the empty shell.
  Also confirm a clean single-fragment race still resolves.
- **Tunnel-down test:** kill the tunnel, hit a lookup route, confirm
  **503** (not 500).
- **Re-verify the Mac source anchors at session start** (the §3 line
  numbers) before editing — they were grounded ~ this session but
  re-confirm per the brief-drafting discipline.
- Report records all states so the triage session sees what moved.

---

## 8. Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/vps_client_api_rewrite_report.md`.
Sections: (1) what changed per file; (2) before/after test counts +
the new tests (esp. the DR-034 collapse test); (3) live smoke results
(the duplicate-market resolve returning the most-complete fragment, one
clean resolve, the tunnel-down 503, **and the §5.2 drop-counter emitting
on a date with known no-market rows — confirm the count sits at/near the
~0.3–1.9% ghost floor, not above it**); (4) launcher-fix confirmations
(F9 persistence survives a simulated restart, F10 refuses a second
instance, rebuild fires on source-newer); (5) self-assessment (anchor
drift, scope adherence, anything odd, bet-safety statement). ~200–400
lines. **No** recommendations, **no** scope creep into the non-migrated
surfaces, **no** settlement/promo/cash-modal work, **no** VPS-side
change, **no** parked-remediation work.

---

## 9. Hard limits — what is NOT in scope

- **The other `vps_client` surfaces** — `race_metadata.py`,
  `runner_metadata.py`, `bracketing.py`, `starting_price.py`,
  `identifier_resolution.py`. They are not on the Log-Past-Bet path and
  not on any live path today. They stay on the (currently dead) file
  resolver. Name in the report that they remain non-operational in the
  launched app — a flagged follow-up, not this brief's job. (See §12
  call 3.)
- **No VPS-side work** — Code does not add or edit VPS endpoints. The
  enrichment Brief 2 needs is already live; the broken `by-market` route
  is sidestepped (§5.6), not fixed here.
- **No parked-remediation work** — the DR-034 stance-4 write-side /
  analytical-deficit fragment-collapse remediation stays parked (S207).
  This brief does the **read-time lookup collapse only**.
- **No `capture.db`** open/copy/mount on the Mac; no schema change; no
  write path; no migration framework; no settlement-worker work; no
  promo-seed; no cash-modal; no v2 change; no recovery change.
- **No new auth/credential** — the 8400 API is unauthenticated behind
  the SSH key; introduce none.
- **Single bounded session.** Over-budget → stop and report.

---

## 10. What happens after Code's session

Next operator-Claude session reads
`vps_client_api_rewrite_report.md`, triages (did the DR-034 collapse
return the most-complete fragment? did the 503 wrap hold? launcher fixes
verified?), and either routes a follow-up or marks Log Past Bet
**live-proven** (per the S189 live-integration taxonomy — green tests
alone are only *implemented-not-live*; live-proven needs the real
duplicate-market resolve end-to-end in the running app). Then the queue
moves to cash-modal → settlement-worker → promo-seed → W16. Code does
not write the next brief.

---

## 11. Cross-references

- Identity model: DR-034 (`decisions.md`) + `BETHUB_DATA_REFERENCE.md`
  §B; duplication anatomy `vps_endpoint_enrichment_report.md` §4.
- Locked path: `launcher_capture_provisioning_brief.md` §3/§6 (Option B,
  picker `/racing/races/{id}`, transport→503, F9 timer-only, F10 lock,
  rebuild, F12 out).
- Contract: `race_date_semantics_report.md` §4 (Candidate B) + §3 (3
  encodings).
- Live endpoints: `vps_date_endpoint_report.md` (`GET /racing/races?date=`)
  + `vps_endpoint_enrichment_report.md` (the enriched payload + the
  by-market route).
- DRs: DR-034 (identity), DR-028 (single boundary), DR-027 (two-DB),
  DR-033 (placings analytical / Betfair settlement), DR-032 (Betfair
  market required at logging), DR-021 (anchors), DR-031 (uv/httpx).
- Excluded parking-lot: the parked stance-4 write-side remediation; the
  34.8% start-less shells; the harness/greyhound mislabel-as-thoroughbred
  (C-4); the DST near-midnight edge; the broken `by-market` route (left
  in place, unused) — none fixed here.

---

## 12. Operator calls — RESOLVED (S208 lock)

All four calls resolved by the operator at S208 lock; the brief body
above already reflects them.

- **(1) Collapse location → client-side. Ship Brief 2 standalone, now.**
  No further VPS work. The broken `by-market` results route is left
  in place but unused (a tracked follow-up, not a blocker). The
  VPS-completeness dependency this creates is pinned explicitly in §5.2.
- **(2) No-Betfair-market races → drop from the picker.** Plus a
  drop-counter (§5.2 step 3 / §8 §3) so an abnormal drop rate surfaces
  as a data-regression signal instead of swallowing silently.
- **(3) Rewrite scope → lookup trio + results only.** The other four
  `vps_client` surfaces stay a flagged follow-up (§9).
- **(4) Tunnel → stays operator-managed.** Tunnel-down maps to 503
  gracefully (§5.7); auto-start/health-check remains a flagged
  follow-up, not this pass.

The original recommendation detail is retained below for the Code
session's context.

---

### Original call detail (reference — resolutions above are authoritative)

1. **(Priority) Where does the DR-034 fragment-collapse live — client or
   VPS?** **Recommend client-side** (as §5 is written): the enriched list
   payload already carries `n_runners` + `state` + `market_id`, so the
   client collapses cheaply with no extra fetches and **no further VPS
   work — Brief 2 ships standalone**, now. The broken `by-market` results
   route is sidestepped (results go by the resolved fragment's race id).
   *Operational consequence:* fastest path to a working Log Past Bet, and
   it leaves the by-market route broken-but-unused (a tracked follow-up).
   Alternative: a small VPS fix first (one more step) that makes the
   by-market route resolve-by-completeness server-side — cleaner
   long-term / more "on the spine" per DR-028, but defers shipping and
   adds a VPS brief. **This is the load-bearing call.**

2. **No-Betfair-market races in the picker — drop or show as
   un-loggable?** DR-034 stance 3 + DR-032 §6: a race with no Betfair
   market can't be logged (settlement is Betfair-only). **Recommend drop
   them** from the lookup (cleanest — you can't action them anyway).
   Alternative: show them greyed-out with a "no Betfair market — can't
   log" note, if you'd rather see that a race existed than have it vanish
   from the list. UX call, yours.

3. **Rewrite scope = lookup trio + results only?** Recommend yes — the
   other four `vps_client` surfaces aren't on any live path; migrating
   them is a flagged follow-up. (Software call; surfaced for visibility,
   not a decision unless you want them in.)

4. **Tunnel lifecycle.** Recommend the tunnel stays operator-managed (as
   today); Brief 2 maps tunnel-down → 503 gracefully; launcher
   auto-start/health-check of the 8400 tunnel is a flagged follow-up,
   **not** in this pass. (Carried from the S205 draft; confirm or fold
   auto-start in.)

*(Not calls — already locked S202 and unaffected by DR-034: F9
timer-only, F10 single-session lock, rebuild-on-newer, F12 out.)*

---

*LOCKED (S208, re-drafted against DR-034, operator-approved). Grounded
against live Mac source + the live VPS enrichment + DR-034. §12 resolved
(client-side collapse, drop no-market races + counter, lookup+results
scope, operator-managed tunnel); ready for the Code session. sha256
recorded in SESSION_208.*
