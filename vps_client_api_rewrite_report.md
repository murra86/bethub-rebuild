# Report — Mac `vps_client` API rewrite (Log Past Bet) + launcher hardening (Brief 2)

**Brief:** `vps_client_api_rewrite_brief.md` — LOCKED (S208), sha256
`f7f5e7e3d1287c3975dc7d015ebabb6a672ddb094fe030d5f7fc040386c5ae28`
(verified full-hash at session start; matched).
**Status:** EXECUTED — client re-pointed to the VPS racing API, DR-034
read-time collapse applied, launcher hardened. All tests green; live
smoke over the 8400 tunnel confirms the most-complete fragment resolves.
**Session:** 2026-06-30, ~14:03 → 14:31 ACST (DR-021 Adelaide, ACST =
UTC+9:30). Single bounded Code session.
**Bet-safety:** CLEAN — analytical/read-path + launcher only. No
settlement, money-movement, lay-placement, capture-db open/copy/mount, or
VPS-side change. The F9 launcher fix is account-safety *adjacent* (it
prevents a Betfair login lockout across restarts) and adds no betting
write path.

---

## 0. Pre-flight (anchors re-verified before any edit)

Per §7 / brief-drafting discipline, the four §3 Mac source anchors were
re-confirmed at session start — **no drift**:

| Anchor | §3 line | Actual line | State |
|---|---|---|---|
| `race_lookup._parse_iso` | 186 | 186 | ✅ present |
| `race_lookup.list_meetings` | 222 | 222 | ✅ present |
| `race_lookup.list_races` | 259 | 259 | ✅ present |
| `race_lookup.resolve_race` | 297 | 297 | ✅ present |

F9 auth anchors (`_auth_betfair.py`): throttle state 112–120, schedule
45–50, kill 53–56 — all present. Launcher anchors (F10 `BETHUB_LAUNCH_PORT`
line 16, rebuild line 67, env exports 75–78) — all present.

**One path drift (finding, not a blocker):** §3 cites the launcher at
`launcher/BetHub.command`; the live file is at repo-root
`/Users/tim/Desktop/Projects/bethub-v3/BetHub.command`. Same file, same
internal anchors — edited in place.

---

## 1. What changed, per file

### Production (within the §5 named anchors)

**`clients/vps_client/v1/_connection.py` (§5.1 transport seam) — repurposed.**
Now carries **two** transports. New: an httpx HTTP client for the
migrated lookup surfaces — `api_base_url()` (`BETHUB_CAPTURE_API_URL`,
default `http://127.0.0.1:8400`), `_build_client()` (isolated for test
injection), and `get_json()` with bounded timeouts (5 s connect / 10 s
read). `get_json` maps: connect/timeout/`httpx.HTTPError` and HTTP 5xx →
`CaptureApiUnavailableError`; HTTP 422 → `CaptureApiBadRequestError`
(programming-error, raised loudly); HTTP 404 → `None`; HTTP 200 → parsed
JSON; any other status → unavailable (never lets a raw exception escape,
§5.7). The original read-only SQLite file helpers (`_resolve_path`,
`_engine_for`, `open_connection`) are **kept unchanged** for the
non-migrated §9 surfaces.

**`clients/vps_client/v1/_lookup_api.py` (§5.2 + §5.5) — NEW shared helper.**
Holds the three load-bearing pieces:
- `parse_scheduled_start()` — the centralised parser, replacing the old
  `_parse_iso`. Accepts all three live UTC encodings, **including the
  7-digit fraction** (`…T06:50:00.0000000Z`, truncated to 6 digits) the
  old parser silently dropped to `None`; converts UTC → Adelaide via
  `to_adelaide` (DST-correct `zoneinfo`).
- `logical_races_for_day()` — Candidate B: fetch `?date=` for D-1/D/D+1,
  union, keep rows whose `scheduled_start` lands on Adelaide D (empty
  `scheduled_start` → fall back to stored `race_date == D`), then run the
  collapse.
- `collapse_fragments()` — the DR-034 read-time fold by
  `betfair_win_market_id`, resolving the most-complete fragment; drops
  no-market rows and still-empty market groups; returns `DropStats`.
- `DropStats` — the §5.2 drop-counter (observability only), with a
  structured `.log()` line per lookup call.

**`clients/vps_client/v1/race_lookup.py` (§5.3 / §5.4) — rewritten.**
The trio now drives off `logical_races_for_day` + the collapse:
- `list_meetings` groups logical races by the most-complete fragment's
  canonical venue; `race_count` counts **logical** races (no fragment
  inflation).
- `list_races` emits one `RaceSummary` per logical race; no-market races
  are gone (dropped at the collapse), so `win_market_id` is always set.
- `resolve_race` finds the matching logical race, fetches
  `GET /racing/races/{id}` **using the most-complete fragment's id** (the
  detail-fetch handle), and maps `runners[]` → `ResolvedRunner` (drops
  null-`betfair_selection_id` rows; derives `scratched` from the detail
  route's `status == "Scratched"`).
- Return models (`MeetingSummary`/`RaceSummary`/`ResolvedRunner`/
  `ResolvedRace`) are **unchanged in shape**, so the (untouched) route
  bridge keeps working. `db_path` is retained on every signature for
  call-site compat but ignored on the HTTP path. Every transport failure
  becomes `UnavailableEnvelope(VPS_UNREACHABLE, retry_after=60)`; a 422
  raises (programming error).

**`clients/vps_client/v1/results.py` (§5.6) — rewritten.**
`race_results(event_id, *, race_id, …)` now reads
`GET /racing/results/{race_id}` by **row id** — the resolved fragment's id
threaded in from `resolve_race`. The broken `by-market` route is **not
used**. Heuristics preserved (404 → GENUINE_ABSENCE; no settled runners →
NOT_YET_CAPTURED; >365 d → NOT_IN_CAPTURE_WINDOW; dead-heat from WINNER
count; `market_voided` = all REMOVED). `event_id` (market id) is echoed
onto the result.

**`clients/betfair_client/v1/_auth_betfair.py` (F9) — back-off persistence.**
Added opt-in persistence of **only** the back-off timer
(`_consecutive_failures` + `_next_attempt_at`); the kill flag is **never**
persisted (a restart still clears a login kill, locked S202 §6.3). New
`backoff_state_path` ctor param, falling back to the `BETHUB_BETFAIR_BACKOFF_PATH`
env (exported by the launcher — both in-scope anchors, so the composition
root is untouched). `_restore_backoff()` runs on init; `_persist_backoff()`
writes atomically (`tmp` + `os.replace`) after each failure/success.
Missing/corrupt file → treated as no back-off (never blocks start-up).
When neither path nor env is set, persistence is off — the prior
in-memory-only behaviour (preserved for tests + the mock path).

**`BetHub.command` (§5.8 launcher) — three fixes + env.**
- **Env:** exports `BETHUB_CAPTURE_API_URL` (default `http://127.0.0.1:8400`)
  and `BETHUB_BETFAIR_BACKOFF_PATH` (default `$HOME/.bethub/…`). The dead
  `BETHUB_CAPTURE_DB_PATH` expectation is confirmed gone (it was never
  exported; the reader now ignores it).
- **F10 single-session lock:** a PID lockfile (`$TMPDIR/bethub-v3-launch.lock`,
  not keyed on the port) — a second launch with a live owner refuses; a
  stale lock (dead owner) is reclaimed. Released on clean shutdown only if
  we own it. (No `flock` on stock macOS — a PID-liveness check via
  `kill -0` is used.)
- **rebuild-if-source-newer:** rebuilds when `dist/index.html` is missing
  **or** any of `ui/web/{src,index.html,package.json,vite.config.ts}` is
  newer than it (`find -newer`) — fixing the stale-bundle trap (S172).

### Tests

- **`tests/_capture_api_fake.py` — NEW** shared `httpx.MockTransport`
  double for the racing API (serves `?date=`, race detail, results;
  `fail_mode` for connect-down / 5xx / 422), usable by both test trees.
- **`tests/clients/vps_client/v1/test_race_lookup.py`** — re-pointed to
  HTTP + new behaviour tests (see §2).
- **`tests/clients/vps_client/v1/test_results.py`** — re-pointed to the
  by-row-id HTTP path.
- **`tests/clients/betfair_client/v1/test_auth_betfair.py`** — F9
  simulated-restart tests appended.
- **`tests/ui/api/test_bets_manual_create.py`** + **`…/test_bet_mutation_audit.py`**
  — collateral re-point: their capture-`db` sqlite fixtures became
  `FakeCaptureApi` fakes (the resolve path is HTTP now). Test *bodies*
  unchanged; only the fixture transport changed.

---

## 2. Before / after test counts + new tests

| Suite | Before | After | Δ |
|---|---|---|---|
| `test_race_lookup.py` | 11 | **18** | +7 |
| `test_results.py` | 5 | **7** | +2 |
| `test_auth_betfair.py` | 22 | **28** | +6 |
| `test_bets_manual_create.py` | 17 | 17 | re-pointed |
| `test_bet_mutation_audit.py` | 6 | 6 | re-pointed |
| `tests/clients/vps_client/` (all) | 62 | **71** | +9 |
| **Full repo** | green | **1202 passed, 1 xfailed** | all green |

Full repo: `uv run pytest -q` → **1202 passed, 1 xfailed, 4 warnings**
(the 4 warnings + the xfail are pre-existing, unrelated — a deprecated
`HTTP_422_*` constant). `ruff check` clean on every changed file.

**New tests required by §7 — all present and passing:**
- **3-encoding parser** (`test_parser_accepts_three_encodings`) — incl.
  the 7-digit-fraction case that returned `None` before; plus
  empty/unknown → `None`.
- **Candidate B window+refine** (`test_candidate_b_keeps_row_filed_under_wrong_race_date`)
  — a row whose stored `race_date` is wrong by a day but whose
  `scheduled_start` lands on D is **kept**; a decoy running on D+1 is
  **dropped**; plus the empty-`scheduled_start` → `race_date` fallback.
- **DR-034 collapse** (`test_dr034_collapse_resolves_most_complete_fragment`)
  — a market id with two fragments (a **PENDING 0-runner shell** at the
  lowest id + a **15-runner** field): the lookup returns **ONE** logical
  race and `resolve_race` returns the **15-runner** fragment, with the
  canonical venue (`"Emerald"`, not the shell's `"Emerald Downs"`) — never
  the empty shell.
- **Transport down → VPS_UNREACHABLE** (connect-down + 5xx) and **422 →
  raised** `CaptureApiBadRequestError`.

---

## 3. Live smoke (read-only over the 8400 tunnel) + route 503 + drop-counter

**B1 — Duplicate-market resolve returns the most-complete fragment.**
Worked example from the enrichment report (`1.259530858`, Emerald, the
3-fragment group: id 2652588 PENDING/0-runner shell, ids 2674078 &
2677487 SETTLED/15-runner):
```
resolve_race('2026-06-29','Emerald',7)
  → FRESH  market=1.259530858  venue=Emerald  runners=13
```
Resolves fragment **2677487** (most-complete by the ordering below), 13
mappable runners (15 minus 2 null-`betfair_selection_id`) — **not** the
0-runner shell `ORDER BY id` would have returned. ✅

**B2 — A clean single-fragment resolve still works.**
```
resolve_race('2026-06-29','Albury',1)
  → FRESH  market=1.259533736  runners=9  event='Surdex Steel Country Boosted Mdn Hcp'
```

**Tunnel-down → 503 (not 500), at the route.** With
`BETHUB_CAPTURE_API_URL=http://127.0.0.1:9` (a dead port; the operator's
real tunnel was **not** touched), via `TestClient`:
```
503  /api/v1/bets/lookup/meetings
503  /api/v1/bets/lookup/races
503  /api/v1/bets/lookup/race
```
All three lookup routes return **503** — the surface wraps the connect
failure as `VPS_UNREACHABLE` and the (untouched) route bridge maps it to
503. No raw 500. ✅

**§5.2 drop-counter — emits, and surfaces a load-bearing finding.** On two
real dates with known no-market rows:
```
surface=list_meetings race_date=2026-06-28 kept_rows=626 logical_races=90 dropped_no_market=445 dropped_empty_market_groups=8  no_market_fraction=0.7109 above_floor=True
surface=list_meetings race_date=2026-06-29 kept_rows=539 logical_races=59 dropped_no_market=412 dropped_empty_market_groups=10 no_market_fraction=0.7644 above_floor=True
```
The counter emits per call as specified. **However — finding (§5):** the
live no-market fraction is **~71–76%**, not "at/near the ~0.3–1.9% ghost
floor" the brief (§5.2/§8) anticipated. This matches the enrichment
report's own datum (`betfair_win_market_id` non-null on only 149/560 rows
for 2026-06-28 — ~73% null) and reflects the data composition: the list
payload carries every captured race, most of which (greyhound/harness/
non-Betfair meetings) legitimately have no Betfair Win market and are
**correctly** un-loggable (DR-032 §6 / DR-034 stance 3). So `above_floor`
is **structurally True** on every normal date. **Behaviour was not
changed** (the floor constants are left exactly as the brief implies;
this is recorded as a finding, not silently re-tuned). The raw
fraction/counts remain useful as a *relative* regression signal; the
floor constant needs operator recalibration to the true ~70–76% baseline
before `above_floor` carries meaning. Routed to operator-Claude triage.

---

## 4. Launcher-fix confirmations

- **F9 — back-off survives a simulated restart (timer), kill does not.**
  `test_f9_cooloff_survives_restart`: process-1 fails one login → arms the
  30-min cool-off → persists. Process-2 (new provider, same path)
  **restores** `consecutive_failures=1` + the absolute `next_attempt_at`
  and **refuses inside the window without calling login** (0 login calls);
  once the window elapses it attempts again. `test_f9_kill_does_not_survive_restart`:
  driven to killed (5 failures) → a fresh provider on the same path is
  **not killed** and attempts a fresh login. Plus: success clears the
  persisted state; missing/corrupt file → no back-off; the
  `BETHUB_BETFAIR_BACKOFF_PATH` env activates persistence. All passing.
- **F10 — second instance refuses.** Simulated: with a live owner PID in
  the lockfile, a second launch hits the refuse branch (`kill -0` true →
  exit 1); a stale lock (dead PID) is reclaimed so a legitimate relaunch
  proceeds. `bash -n` clean.
- **rebuild-on-source-newer.** The `find … -newer dist/index.html`
  predicate fires when a source file is newer than the built entry point
  (verified with a synthetic newer/older pair); the missing-`dist` branch
  also forces a build. `bash -n` clean.

---

## 5. Self-assessment

**Anchor drift:** none in the four §3 source anchors (all at the stated
lines). One **path** drift recorded: launcher is at repo-root
`BetHub.command`, not `launcher/BetHub.command` (§0).

**Findings surfaced (not silently fixed):**
1. **The list payload's `state` field is the geographic state**
   (`"QLD"`/`""`/`null`), **not** settlement status. `capture_status`
   (SETTLED/PENDING) lives only on the per-race detail route. So the
   brief's §5.2 completeness order — "resolved/`state` precedence
   (settled > pending)" first — is **not implementable from list fields**
   as written. Collapsing from list fields only (no extra per-fragment
   fetch, per §5.2), the ordering used is **`n_runners` → breadth of
   `sources_with_data` → recency (`scheduled_start`, then `id`)**. This
   still satisfies the load-bearing correctness property and the mandatory
   §7 test (the 0-runner PENDING shell carries `n_runners == 0`, so it
   always loses to the 15-runner fragment). The pinned §5.2
   VPS-completeness dependency therefore rests on `n_runners` +
   `sources_with_data` staying present/accurate (not on a settlement-state
   field, which the list does not carry).
2. **Drop-counter floor mismatch** — the live no-market rate (~71–76%) is
   ~40× the brief's stated 0.3–1.9% floor; `above_floor` is structurally
   True. Detailed in §3. Behaviour unchanged; routed to triage.
3. **Runner `scratched`** — the race-detail route exposes `status`
   (`"Active"`/`"Scratched"`), **no `scratched` boolean**; derived
   accordingly.
4. **Results `source` + timestamps** — the results route exposes **no
   `results_source`** field (the old SQL read it for `source_mix`), so
   `source` is inferred from the presence of a Betfair price (BETFAIR_WIN
   if `bf_bsp`/`bf_closing_*` present, else RACING_API); and it exposes no
   finalised/snapshot timestamp, so `finalised_at` is `None` and `as_of`
   is the read time. `bsp` maps from `bf_bsp` (fallback `sp_fixed`).

**Scope adherence:** edits confined to the §5 anchor areas — the
`vps_client/v1` lookup surfaces (`_connection`, new `_lookup_api`,
`race_lookup`, `results`), the launcher, and the auth back-off module.
**Out of scope and untouched:** the route bridge `ui/api/routers/bets.py`
(no route change needed — §5.7), the composition root
`ui/api/dependencies/composition.py` (F9 wired via the launcher env
instead), the other four `vps_client` surfaces (`race_metadata`,
`runner_metadata`, `bracketing`, `starting_price`, `identifier_resolution`
— they stay on the file resolver via the preserved `open_connection`, and
**remain non-operational in the launched app** — a flagged follow-up per
§9), the broken `by-market` route (left in place, unused), and the parked
DR-034 write-side remediation. No settlement/promo/cash-modal/v2/recovery
work, no VPS-side change, no schema/migration, no new auth/credential. The
two UI test re-points (`test_bets_manual_create`, `test_bet_mutation_audit`)
were necessary collateral of the transport change — test fixtures only,
no production behaviour expanded.

**Git hygiene:** tree was clean on `main` at session start (per S198). The
rewrite is committed as **one checkpoint** after tests passed (per §4).
Changed: 6 production files (+1 new) and 4 test files (+1 new helper).

**Anything else odd:** `resolve_race` returns 13 (not 15) runners for the
Emerald example — 2 of the 15 detail runners carry a null
`betfair_selection_id` (e.g. a scratched horse with no Betfair selection)
and are dropped, which is the pre-existing, correct behaviour (an
unstakeable runner). The Candidate-B keep-filter drops a non-empty but
*unparseable* `scheduled_start` rather than applying the `race_date`
fallback (the brief reserves the fallback for *empty* values); with the
new 3-encoding parser this is not expected to occur on live data, but a
genuinely 4th encoding would make such a row vanish from the picker —
noted, not handled (out of spec).

**Bet-safety statement:** CLEAN. This session re-pointed a read-only
race-lookup client to the analytical racing API (DR-033), applied a pure
client-side read-time reconciliation (no cache, no stored copy, no second
integration point — DR-028 clean), and hardened the launcher. No Betfair
settlement, money-movement, lay-placement, or live-betting write path was
read or written; `capture.db` was never opened, copied, or mounted from
the Mac; no VPS file/service/git change was made (read-only GET over the
tunnel for §7 verification only). The F9 change reduces Betfair
login-lockout risk and adds no betting write path.

---

*Report landing complete — operator-Claude can triage: the DR-034
collapse returns the most-complete fragment (live-confirmed); the 503 wrap
holds across all four lookup routes; F9/F10/rebuild verified. Two items
need an operator decision before "live-proven": (a) recalibrate the §5.2
drop-counter floor to the true ~70–76% no-market baseline; (b) the four
non-migrated `vps_client` surfaces remain dead in the launched app.*
