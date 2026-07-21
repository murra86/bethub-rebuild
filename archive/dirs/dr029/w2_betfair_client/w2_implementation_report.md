# W2 — `betfair_client` v1.0 implementation: Code report

**Brief:** `dr029/w2_betfair_client/w2_brief.md` (Session 84).
**Repo target:** `/Users/tim/Desktop/Projects/bethub-v3/clients/betfair_client/v1/`.
**Contract:** `dr029/2_7_api_contract_versioning/betfair_client_contract.md` v1.0 (locked Sessions 75/77/78).

---

## §1 — Anchor (session start)

`2026-05-05 16:06 ACST` (Adelaide local, per DR-021).

---

## §2 — Pre-flight

Contract status header verified at v1.0 — locked Session 75, drafted
Session 77, finalised Session 78. No `**Status:** drafting` markers
present. No carry-forward findings from W1 apply to envelope shape beyond
F3 (PEP-695 type alias substrate — re-applied here per §3) and F6
(`_clock.now_utc()` test-patchability pattern — re-applied here per §7).

Baseline `uv run pytest` against W0 + W1 substrate: **57 passed** before
W2 work began. No drift detected; pre-flight passed and Code proceeded
to step 2.

---

## §3 — Envelope module summary

`bethub-v3/clients/betfair_client/v1/envelope.py` (~110 lines).

Shapes shipped per contract §8:

- `EnvelopeStatus` (`fresh` / `stale` / `unavailable`) — same shape as
  `vps_client/v1/envelope.py`.
- `BetfairReadUnavailableReason` — seven values exactly matching
  contract §8.2: `genuine_absence`, `betfair_auth_expired`,
  `betfair_rate_limited`, `betfair_market_suspended`,
  `betfair_streaming_disconnected`, `betfair_market_not_found`,
  `betfair_api_unreachable`.
- `BetfairWriteUnavailableReason` — three values exactly matching
  contract §8.3: `betfair_write_rejected`, `betfair_insufficient_funds`,
  `betfair_bet_placement_in_progress`.
- `FreshEnvelope[T]`, `StaleEnvelope[T]` — Pydantic v2 generic models
  per contract §8.4. Both declare
  `model_config = {"arbitrary_types_allowed": True}` so the discriminated
  union accepts list payloads where the contract calls for them (e.g.
  `ReadEnvelope[list[SportsMarketVariant]]` from §9.3).
- `UnavailableReadEnvelope` — carries
  `BetfairReadUnavailableReason` + optional `retry_after`.
- `UnavailableWriteEnvelope` — carries union of
  `BetfairWriteUnavailableReason | BetfairReadUnavailableReason` (the
  contract §8.4 union for connectivity-shaped failures during a write
  call) + optional `retry_after`, `rejection_code`, `rejection_detail`.
- `ReadEnvelope[U]`, `WriteEnvelope[U]` — PEP-695 generic type aliases
  per W1 finding F3 substrate. The contract's `typing.Union[...]`
  phrasing does not survive runtime subscripting on Python 3.12+; the
  `type X[U] = ...` form gives the same typing surface plus runtime
  support. → Finding F1 (re-application of W1 F3 to W2; flagged for
  visibility only).

`as_of` timestamps are Adelaide local per DR-021. Helpers
`now_adelaide()` and `to_adelaide()` exposed alongside the shapes,
mirroring `vps_client/v1/envelope.py`.

**Implementation choice — local envelope, not imported from
`vps_client`.** Per DR-030 layered architecture, `betfair_client` and
`vps_client` are sibling clients, not a dependency chain. The shared
shape is duplicated locally; the unavailable-reason enumerations diverge
between the two modules.

Smoke test (`uv run python -c "from clients.betfair_client.v1.envelope
import ..."`) confirmed:
- All seven read-side reason values present.
- All three write-side reason values present.
- `ReadEnvelope[Demo]` and `WriteEnvelope[Demo]` runtime-subscriptable
  with concrete Pydantic models.
- Both envelopes accept the connectivity-cross-over (write envelope with
  read-side reason).

---

## §4 — Per-read-surface implementation summary

Five read surfaces under `clients/betfair_client/v1/`. Each surface
exposes the exact public function signature from contract §9 and parses
mocked Betfair JSON returns via the `BetfairRestClient` transport
abstraction.

### §4.1 §9.1 live-pricing — `live_pricing.py`

- Public functions: `market_prices(market_id, rest_client,
  streaming_client=None)`, `runner_best_prices(market_id, selection_id,
  rest_client, streaming_client=None)`.
- Pydantic shapes: `MarketPrices`, `RunnerBestPrices`, `RunnerPrices`,
  `PriceLevel`. Plus `parse_market_prices()` and `parse_runner_prices()`
  helpers re-used by `streaming.py` for cache population.
- Routing per contract §10: when a `streaming_client` is supplied, the
  cache is consulted first via `cached_market_prices()` /
  `cached_runner_best_prices()`; on miss or non-`SUBSCRIBED` state the
  call falls through to REST.
- REST path: `GET /v1/market/{market_id}/prices` and
  `GET /v1/market/{market_id}/runner/{selection_id}/best`. Suspended
  markets surface as `unavailable` with reason
  `betfair_market_suspended`. 404 → `betfair_market_not_found`. Other
  HTTP-shape failures route through `_errors.map_rest_error_read`.
- Per contract §4: REST returns `fresh` by definition (live API). The
  `stale` envelope is a streaming-cache concept only — it surfaces from
  the cache wrap helpers in `streaming.py`.
- Tests: 9 covering REST-only path (suspended, market-not-found,
  cache-miss-fallback), cache path (image populates, runner-best
  short-circuit), and the unknown-selection-falls-through-to-REST shape.

### §4.2 §9.2 settlement reads — `settlement.py`

- Public function: `market_settlement(market_id, rest_client)`.
- Pydantic shapes: `MarketSettlement`, `RunnerSettlement`,
  `RunnerSettlementStatus`, `MarketStatus`.
- Five anchor fields per §2.6 §5.1 plus three count fields
  (`dead_heat_count`, `removed_runner_count`, `unexpected_state_count`)
  per contract §9.2 generalisation.
- `market_status=CLOSED` with `settled_time=None` returns a `fresh`
  envelope per contract §9.2 — distinct from `unavailable` because v3's
  settlement worker reads it as "wait and retry." Verified by
  `test_fresh_closed_pending_settlement`.
- Failure modes: 404 → `betfair_market_not_found`; other HTTP-shape
  failures route through `_errors`.
- Tests: 6 covering fresh-settled, fresh-closed-pending, market-not-found,
  api-unreachable (503), auth-expired (401), rate-limited (429).

### §4.3 §9.3 sports-line query — `sports_lines.py`

- Public function: `sports_market_variants(event_id, market_type,
  rest_client)`.
- Pydantic shapes: `SportsMarketType` (MATCH_ODDS / HANDICAP / TOTAL),
  `SportsMarketVariant`, plus re-used `RunnerPrices` from
  `live_pricing.py`.
- Empty `variants` array on a 200 response → `genuine_absence` (event
  resolves but Betfair offers no markets of that type). 404 →
  `betfair_market_not_found` (event itself unknown).
- Tests: 4 covering fresh handicap variants, no-variants, event-not-found,
  match-odds-shape.

### §4.4 §9.4 scheduled-time reads — `scheduled_time.py`

- Public function: `market_scheduled_time(market_id, rest_client)`.
- Pydantic shape: `MarketScheduledTime`.
- Empirical caveat per contract §9.4 (whether Betfair `marketTime`
  updates on material delay) propagated as a module docstring; the
  surface returns whatever Betfair currently reports.
- Tests: 3 covering fresh, market-not-found, api-unreachable (502).

### §4.5 §9.5 identifier-resolution check — `identity.py`

- Public function: `identity_check(market_id, selection_id, rest_client)`.
- Pydantic shape: `IdentityCheck` with `exists: bool` plus optional
  `market_status`, `runner_status`, `event_id`.
- Distinction per contract §9.5: `betfair_market_not_found` (404) is
  distinct from "market resolved cleanly but selection not in market"
  (`exists=False` with `market_status` populated). Verified by
  `test_identity_selection_missing_in_known_market`.
- Tests: 3 covering exists-true, exists-false-with-market-known,
  market-not-found.

---

## §5 — Streaming surface implementation summary

`clients/betfair_client/v1/streaming.py` (~470 lines), with internal
state machine, per-market and per-(market, selection) caches,
subscription tracking, and dispatch primitives upward.

**Public types per contract §10.**

- `StreamingConnectionState` — five states per §10.1: DISCONNECTED,
  CONNECTING, AUTHENTICATING, SUBSCRIBED, RECONNECTING.
- `MarketSubscriptionScope` — RACING_AU, SPORTS_AU per §10.2 + §2.4 §5.1.
- `StreamingStatus` — state, market_subscriptions list,
  order_subscription_active, last_message_time, last_market_image_time,
  consecutive_reconnect_failures.
- `UnmatchedOrder`, `MatchedPositionLevel`, `OrderPosition` — order
  cache shape per §10.4.
- `MarketUpdate`, `OrderUpdate` — typed dispatch events per §10.6.

**`StreamingClient` class.**

- Lifecycle: `connect()` triggers DISCONNECTED → CONNECTING; the
  subsequent `connection_ack` message in `_handle_message` advances to
  AUTHENTICATING; `auth_ack` advances to SUBSCRIBED. Subscription
  registration (`subscribe_markets(scope)`, `subscribe_orders()`)
  records intent before auth completes; the SUBSCRIBED state activates
  whatever subscriptions are registered. Idle SUBSCRIBED with no
  registered subscriptions is legal (verified by
  `test_idle_subscribed_with_no_subs_is_legal`).
- Cache: market cache keyed by `market_id`; order cache keyed by
  `(market_id, selection_id)`. Both populated via image and delta
  messages dispatched through `_handle_message`. Caches survive
  disconnect per contract §10.5 + §2.4 §8.8 per-subscription
  independence — verified by
  `test_per_subscription_independence_caches_survive_disconnect`.
- Cache-vs-REST routing helpers: `cached_market_prices()` and
  `cached_runner_best_prices()` return `None` when the cache path is
  ineligible (state ≠ SUBSCRIBED, no cached image), so
  `live_pricing.market_prices()` falls through to REST cleanly.
- Wrap helpers (`_wrap_cached_market`, `_wrap_cached_order`,
  `_wrap_runner_best`) implement the freshness logic centrally:
  `fresh` when state = SUBSCRIBED AND heartbeat current AND not
  status-degraded AND age within `CACHE_STALE_THRESHOLD_SECONDS` (30s
  placeholder); `stale` otherwise (with `lag_seconds = age`).
- Reconnection: `_on_disconnect` transitions to RECONNECTING and
  increments `consecutive_reconnect_failures`. The
  `SUSTAINED_RECONNECT_FAILURE_THRESHOLD` placeholder is 5 attempts;
  threshold-tripping is observable via the streaming status field
  (verified by `test_sustained_failure_threshold_marker`). Caches are
  not cleared on disconnect — the helper `disconnect(reset_caches=True)`
  exists for explicit operator-driven teardown.
- Heartbeats: `HEARTBEAT_LOSS_THRESHOLD_SECONDS = 10` placeholder. When
  the wall-clock advances past the threshold without a fresh message,
  `_heartbeat_overdue()` returns `True` and cached payloads surface as
  `stale`. Verified by `test_heartbeat_loss_marks_cache_stale` which
  monkeypatches `_clock.now_utc()` 60s into the future.
- `status=503` handling per §10.5 + §2.4 §8.5: degraded-data, not a
  connection signal. The internal `_status_degraded` flag flips on; the
  state stays SUBSCRIBED; reads return `stale`. Cleared on next
  `status_ok` or heartbeat. Verified by `test_status_503_marks_cache_stale`
  and `test_status_recovery_clears_degraded_flag`.
- Callback registration: `on_market_update(callback)` and
  `on_order_update(callback)` per §10.6. The dispatch primitive is a
  simple synchronous list — Code's call at implementation per the
  contract's "Code finalises the dispatch primitive" framing. The
  shape upward is the typed `MarketUpdate` / `OrderUpdate` event;
  consumers never see Streaming protocol fields.

**Cadence parameters as Fix 4 placeholders.** Six constants tagged at
the top of `streaming.py` with the comment "Fix 4 calibration target":
`HEARTBEAT_LOSS_THRESHOLD_SECONDS = 10`,
`RECONNECT_BACKOFF_INITIAL_SECONDS = 1`,
`RECONNECT_BACKOFF_MAX_SECONDS = 30`,
`SUSTAINED_RECONNECT_FAILURE_THRESHOLD = 5`,
`CACHE_FRESHNESS_TARGET_SECONDS = 5`,
`CACHE_STALE_THRESHOLD_SECONDS = 30`.

**Mocking discipline.** Tests drive `_handle_message` directly with
hand-crafted scenarios from
`tests/fixtures/betfair/stream_messages.py`. No real socket is opened
during W2. The actual socket-reading loop is v3 build proper
substrate — `betfairlightweight` integration sits inside the message
parser that calls `_handle_message`. → Finding F2 (the wire-format
parser is the v3 build proper integration point; W2 ships the
post-parse dispatch path; surfaced for visibility, not as a defect).

**Tests: 26.** Coverage: connection state transitions; market image
and delta dispatch; order unmatched and matched dispatch; callback
registration and firing; cache emptiness vs subscription state; sustained
reconnection failure tracking; status-503 stale propagation; status
recovery; heartbeat-loss stale assertion; market suspended in cache;
per-subscription independence (caches survive disconnect); subscribe
call surfaces; idle SUBSCRIBED legality; status fields; cache reset on
explicit disconnect; multi-market cache isolation; cache age past
freshness window; runner-best cache helper; runner-best returns None
when not subscribed.

---

## §6 — Per-write-surface implementation summary

Three write surfaces. Each emits exactly one structured audit-log entry
per call regardless of outcome (contract §12), via the shared `_emit_entry`
helper in `placement.py`.

### §6.1 §11.1 placement — `placement.py`

- Public function: `place_bet(market_id, selection_id, side, price, stake,
  customer_order_ref, rest_client, streaming_client, audit_sink,
  operator_identity, customer_strategy_ref=None,
  persistence_type=PersistenceType.PERSIST)`.
- Pydantic shape: `BetPlacementResult` with `bet_id`,
  `customer_order_ref` (echoed), `placed_at`, `initial_size_matched`,
  `size_remaining`, `average_price_matched`.
- Endpoint: POST `/v1/orders/place` with the typed body.
- **Streaming-disconnect-blocks-writes pre-check per §13.1.** Before any
  REST call, the streaming state is read; if not SUBSCRIBED, the call
  returns `UnavailableWriteEnvelope(reason=BETFAIR_STREAMING_DISCONNECTED,
  retry_after=10, rejection_detail="Streaming connection unavailable;
  placement queue paused.")` and the audit entry records
  outcome=`STREAMING_DISCONNECTED`. Verified across all four
  non-SUBSCRIBED states by `test_streaming_blocks_writes.py`.
- Mapping from rejection codes: `INSUFFICIENT_FUNDS` →
  `betfair_insufficient_funds`; `BET_IN_PROGRESS` /
  `DUPLICATE_BETIDS` → `betfair_bet_placement_in_progress`; everything
  else → `betfair_write_rejected` (echoes the rejection code in the
  envelope).
- Tests: 6 covering successful placement, partial-match success, reject
  market-not-open, reject insufficient-funds, blocked-when-disconnected,
  auth-expired connectivity failure during write.

### §6.2 §11.2 cancellation — `cancellation.py`

- Public function: `cancel_bet(market_id, bet_id, rest_client, audit_sink,
  operator_identity, size_to_cancel=None)`.
- Pydantic shape: `BetCancellationResult` with `bet_id`, `cancelled_at`,
  `size_cancelled`, `size_remaining`.
- Endpoint: POST `/v1/orders/cancel`.
- **Not subject to streaming-disconnect pre-check** per §13.4 — verified
  by `test_cancellation_not_blocked_when_disconnected`.
- Tests: 4 covering full success, partial success, rejection
  (`BET_TAKEN_OR_LAPSED` — folds to `betfair_write_rejected`), 503 →
  `api_unreachable`.

### §6.3 §11.3 replacement — `replacement.py`

- Public function: `replace_bet(market_id, bet_id, new_price, rest_client,
  audit_sink, operator_identity)`.
- Pydantic shape: `BetReplacementResult` with `cancelled_bet_id`,
  `new_bet_id`, `replaced_at`, `new_price`, `size_carried`.
- Endpoint: POST `/v1/orders/replace`.
- Atomicity caveat per §2.4 §14.6 propagated as a module docstring.
- **Not subject to streaming-disconnect pre-check** per §13.4 — verified
  by `test_replacement_not_blocked_when_disconnected`.
- Tests: 3 covering success, rejection (`PRICE_INVALID` — folds to
  `betfair_write_rejected`), 429 → `rate_limited` with retry_after.

---

## §7 — Cross-cutting modules summary

Five private modules under `clients/betfair_client/v1/`:

**`_clock.py`** (~15 lines). Exposes `now_utc()` as a module attribute
per W1 F6 substrate. All surfaces import via `from . import _clock`
and call `_clock.now_utc()`. Tests
`monkeypatch.setattr(_clock, "now_utc", lambda: FIXTURE_NOW_UTC)` in
the conftest autouse fixture; freshness arithmetic resolves
deterministically against the pinned reference (2026-05-04 04:42:30
UTC = 14:12:30 ACST).

**`_auth.py`** (~50 lines). Defines `AuthProvider` Protocol with
`session_token()` and `app_key()` methods. Ships `MockAuthProvider`
returning fixed values for tests. The real `BetfairAuthProvider` is
deferred to v3 build proper deployment per brief §4 — no real
credentials handled.

**`_audit.py`** (~120 lines). Contract §12 substrate.
- `AuditLogEntry` Pydantic model carrying all fields per §12.1
  (entry_id, operator_identity, timestamp, operation, market_id,
  selection_id, bet_id, side, price, stake, customer_order_ref,
  persistence_type, outcome, rejection_code, rejection_detail,
  betfair_bet_id_returned, elapsed_ms).
- `WriteOperation` enum (PLACE / CANCEL / REPLACE).
- `WriteOutcome` enum (SUCCESS / REJECTED / INSUFFICIENT_FUNDS /
  PLACEMENT_IN_PROGRESS / STREAMING_DISCONNECTED / AUTH_EXPIRED /
  RATE_LIMITED / API_UNREACHABLE / OTHER_FAILURE).
- `BetSideStr` and `PersistenceTypeStr` mirror enums duplicated locally
  to avoid an `_audit` → `placement` import cycle (`_audit` is a leaf
  inside the package). → Finding F3 (mirror-enum pattern flagged for
  visibility — operator-Claude triage may decide whether to consolidate
  in a future refactor).
- `AuditLogSink` Protocol with one method `write(entry)`.
  `StdoutAuditLogSink` writes JSON-lines to stdout (default for local
  dev); `MemoryAuditLogSink` collects entries in `.entries` for tests.
  Real durable substrate is v3 build proper deployment configuration.

**`_connection.py`** (~95 lines). REST connection wrapper around an
injected transport callable. `BetfairRestClient` exposes `get(path)`
and `post(path, body)`; the transport signature is
`(url, json_body, headers) -> dict`. `RateLimitBudget` dataclass
tracks call timestamps in a sliding window — the placeholder defaults
(200 calls / 60s) are Fix 4 calibration targets. `BetfairRestError`
exception carries `status_code`, `message`, `retry_after` for
`_errors` to map.

**`_errors.py`** (~85 lines). Two mapping functions:
`map_rest_error_read(exc)` → `UnavailableReadEnvelope`;
`map_rest_error_write(exc)` → `UnavailableWriteEnvelope` (re-uses the
read-side mapping for connectivity-shaped failures, then wraps in the
write envelope shape). Plus `write_reason_for_rejection_code(code)`
table mapping known Betfair rejection codes
(`INSUFFICIENT_FUNDS` → funds, `BET_IN_PROGRESS` / `DUPLICATE_BETIDS`
→ in-progress; everything else → write-rejected) and
`write_envelope_for_rejection(code, detail)` builder.

---

## §8 — Fixture summary

Two fixture modules under `tests/fixtures/betfair/`:

### `rest_responses.py`

Hand-crafted Betfair JSON responses per surface, plus a `MockTransport`
class that routes by URL substring match. Tests register per-path
responders (`register_static`, `register_error`) and pass the transport
to a `BetfairRestClient`.

Status coverage per surface:
- §9.1 live-pricing: fresh full, fresh runner-best, suspended-market,
  market-not-found (via 404), api-unreachable (via 5xx), auth-expired
  (via 401), rate-limited (via 429).
- §9.2 settlement: fresh-settled, fresh-closed-pending, fresh-open-no-data,
  market-not-found, api-unreachable, auth-expired, rate-limited.
- §9.3 sports-line: fresh handicap variants, no-variants
  (`genuine_absence`), event-not-found.
- §9.4 scheduled-time: fresh, market-not-found, api-unreachable.
- §9.5 identity: exists-true, exists-false-with-market, market-not-found.
- §11 writes: place success, place partial-match, place rejected
  market-suspended, place rejected insufficient-funds, cancel success,
  cancel partial success, cancel rejected, replace success, replace
  rejected, replace rate-limited.

### `stream_messages.py`

Internal-envelope message scenarios for the state machine. Each scenario
is a `{"op": "...", "payload": {...}}` dict matching the shape
`StreamingClient._handle_message` consumes. Builders for parameterised
scenarios (`market_image(market_id)`, `market_delta(market_id, price)`,
`market_suspended(market_id)`, `order_unmatched(...)`,
`order_matched(...)`) plus the static lifecycle messages
(`CONNECTION_ACK`, `AUTH_ACK`, `HEARTBEAT`, `STATUS_DEGRADED`,
`STATUS_OK`, `DISCONNECT`).

The conftest autouse fixture pins `_clock.now_utc()` to
`2026-05-04 04:42:30 UTC` (= 14:12:30 ACST) so freshness arithmetic
against fixture timestamps (which fall in the 14:11–14:30 ACST window)
resolves deterministically per W1 F6 substrate.

---

## §9 — Final verification (verbatim output)

### `uv run ruff check`

```
All checks passed!
```

### `uv run mypy .`

```
Success: no issues found in 78 source files
```

### `uv run lint-imports`

```
Analyzed 74 files, 190 dependencies.
------------------------------------

DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT

Contracts: 5 kept, 0 broken.
```

### `uv run pytest -v` (truncated to summary)

```
collected 158 items

tests/clients/betfair_client/v1/test_audit.py ...... [7 passed]
tests/clients/betfair_client/v1/test_cancellation.py ... [4 passed]
tests/clients/betfair_client/v1/test_envelope.py ... [12 passed]
tests/clients/betfair_client/v1/test_error_mapping.py ... [10 passed]
tests/clients/betfair_client/v1/test_identity.py ... [3 passed]
tests/clients/betfair_client/v1/test_live_pricing.py ... [9 passed]
tests/clients/betfair_client/v1/test_placement.py ...... [6 passed]
tests/clients/betfair_client/v1/test_replacement.py ... [3 passed]
tests/clients/betfair_client/v1/test_scheduled_time.py ... [3 passed]
tests/clients/betfair_client/v1/test_settlement.py ...... [6 passed]
tests/clients/betfair_client/v1/test_sports_lines.py ... [4 passed]
tests/clients/betfair_client/v1/test_streaming.py ........ [26 passed]
tests/clients/betfair_client/v1/test_streaming_blocks_writes.py ... [8 passed]
tests/clients/vps_client/v1/* ... [51 passed — W1 substrate]
tests/test_skeleton.py ... [6 passed — W0 substrate]

============================= 158 passed in 0.45s ==============================
```

Per §5.6 brief target, total W2 test count is **101** (target range
90–130). Within the named range.

---

## §10 — Git state

```
$ git log --oneline
254fcfc W2: betfair_client v1.0 implemented per locked contract (§9.1–§9.5 + §10 streaming + §11.1–§11.3 + §12 audit + §13 streaming-disconnect + envelope + error mapping + fixtures + tests)
0f5fae3 W1: vps_client v1.0 implemented per locked contract (§9.1–§9.6 + envelope + error mapping + fixture + tests)
67a7f04 W0: v3 repo skeleton initialised per DR-030 (layout) and DR-031 (stack)
```

Three commits on `main`: W0 skeleton, W1 vps_client, this session's
single W2 commit. Working tree clean post-commit. Per the brief's hard
limit "no commits beyond step 10," no amend was needed; toolchain
checks passed clean before the commit landed.

---

## §11 — Pass/fail status table

| # | Criterion | Status |
|---|---|---|
| 1 | `envelope.py` exists; envelope models instantiate without error; `ReadEnvelope[X]` and `WriteEnvelope[X]` runtime-subscriptable | PASS |
| 2 | All five read-surface modules (`live_pricing`, `settlement`, `sports_lines`, `scheduled_time`, `identity`) exist with public functions matching contract signatures | PASS |
| 3 | `streaming.py` exists; five-state state machine with valid transitions; subscribe call surfaces, status read, order cache shape, reconnect/heartbeat/dispatch logic | PASS |
| 4 | All three write-surface modules exist; each emits exactly one audit-log entry per call regardless of outcome | PASS |
| 5 | Cross-cutting modules (`_auth`, `_audit`, `_clock`, `_connection`, `_errors`) exist; `AuthProvider` Protocol + `MockAuthProvider`; `AuditLogSink` Protocol + `StdoutAuditLogSink` + `MemoryAuditLogSink` | PASS |
| 6 | `tests/fixtures/betfair/rest_responses.py` and `stream_messages.py` exist; status coverage per §5.6 | PASS |
| 7 | `uv run ruff check` exits 0 with no findings | PASS |
| 8 | `uv run mypy .` exits 0 with no findings | PASS — 78 source files |
| 9 | `uv run lint-imports` exits 0 with five contracts kept, zero broken | PASS |
| 10 | `uv run pytest -v` exits 0; W0 + W1 tests still pass; total = 158, of which 101 are new W2 | PASS |
| 11 | Streaming-disconnect-blocks-writes verified by `test_streaming_blocks_writes.py` | PASS — placement blocked across all four non-SUBSCRIBED states; cancel+replace not blocked; envelope carries reason + retry_after |
| 12 | Audit-trail discipline verified by `test_audit.py` | PASS — one entry per call; `customer_order_ref` join-key correctly populated for retry-cycle reconstruction |
| 13 | `git log` shows exactly one new commit on main with §6 step 10 message | PASS |

**Overall status: verification passed clean.** All 13 criteria met.

---

## §11.findings — Findings

Six findings surfaced. None blocked verification clean. All deferred to
next operator-Claude session triage per brief §10 routing.

### Finding F1: PEP-695 type alias re-applied per W1 F3 substrate

- **Step where it surfaced:** §6 step 2 (envelope smoke test).
- **Expected:** contract §8.4 shows `ReadEnvelope = FreshEnvelope[T] |
  StaleEnvelope[T] | UnavailableReadEnvelope` and `WriteEnvelope =
  FreshEnvelope[T] | UnavailableWriteEnvelope` as non-PEP-695 union
  aliases.
- **Actual:** that form is not runtime-subscriptable on Python 3.12+.
  Switched to `type ReadEnvelope[U] = ...` and
  `type WriteEnvelope[U] = ...` (PEP-695 generic type alias).
- **Code's read:** identical to W1 F3 — the contract phrasing is a
  typing-level alias (mypy understands) but doesn't survive runtime
  subscripting; PEP-695 syntax gives the same typing surface plus
  runtime support. Local to `envelope.py`; contract surface upward
  unchanged. Future contract revisions might want to update the example
  phrasing for accuracy under DR-031 (Python 3.12+).
- Code did NOT attempt remediation per §1 of brief — flagged for
  consistency with W1 F3.

### Finding F2: real Streaming wire-format parser is v3 build proper substrate

- **Step where it surfaced:** §6 step 5 (streaming module
  implementation).
- **Expected:** the contract §10 describes the upward shape — connection
  states, subscriptions, dispatch — without specifying the wire format
  (left to `betfairlightweight` library integration per DR-031).
- **Actual:** W2 ships the post-parse dispatch path. The
  `_handle_message(message)` method consumes a simplified internal
  envelope (`{"op": "...", "payload": {...}}`) which a v3 build proper
  parser will produce from raw Betfair Streaming protocol frames
  (`mcm`, `ocm`, status, heartbeat, etc.).
- **Output:** the `streaming.py` module docstring documents the
  internal envelope shape and the integration point. Tests drive the
  state machine directly via this envelope; no real socket is opened
  during W2.
- **Code's read:** this is the natural break point given the brief's
  Option 1 (mocked-only, no real Betfair calls). The wire-format parser
  belongs alongside the real socket integration in v3 build proper.
  Operator-Claude triage may want to flag this in the v3 build proper
  brief drafting so the parser is named explicitly as a W3+ deliverable.
- Code did NOT attempt remediation per §1 of brief — flagged for
  visibility.

### Finding F3: `_audit.BetSideStr` / `PersistenceTypeStr` mirror enums

- **Step where it surfaced:** §6 step 7 (write-surface implementation).
- **Expected:** the contract §12.1 audit-log entry references the
  same `BetSide` / `PersistenceType` enums used in §11.1 placement.
- **Actual:** importing `BetSide` from `placement.py` into `_audit.py`
  would create an import cycle (`_audit ↔ placement`). Since `_audit`
  is a leaf inside the package by design, the enums were duplicated
  locally as `BetSideStr` and `PersistenceTypeStr` (same values, same
  shape) and `placement.py` casts via `BetSideStr(side.value)` when
  constructing the audit entry.
- **Output:** mypy + ruff both clean. The duplication is invisible to
  consumers — the public surface re-exports `BetSide` and
  `PersistenceType` from `placement.py`; `BetSideStr` /
  `PersistenceTypeStr` only appear inside `_audit.AuditLogEntry`.
- **Code's read:** acceptable for v1.0. An alternative refactor would
  consolidate the enums into a fourth shared `_types.py` module —
  small change, but unnecessary unless the duplication starts to
  surface elsewhere. Operator-Claude triage may decide.
- Code did NOT attempt remediation per §1 of brief — flagged for
  visibility.

### Finding F4: contract endpoint paths are abstract; real Betfair API uses different shapes

- **Step where it surfaced:** §6 step 4 (read-surface implementation).
- **Expected:** the contract §9–§11 specify endpoint paths like
  `/v1/market/{market_id}/prices`, `/v1/orders/place`, etc. — clearly
  marked as the contract's internal abstraction since real Betfair
  Exchange REST uses JSON-RPC over `api.betfair.com/exchange/betting/`
  with method names (`listMarketBook`, `placeOrders`, ...) rather than
  REST-style paths.
- **Actual:** W2 implements against the contract's path-style abstraction
  (W2 ships mocked tests only, so the URL never reaches a real server).
  Real-API integration in v3 build proper W3+ will need a transport
  adapter that translates the path-style calls to Betfair's actual
  JSON-RPC shape — or alternatively, the contract may want to revise
  the path examples in a future update to match Betfair's real API
  shape.
- **Output:** all surfaces' transport calls match the contract's path
  pattern; tests register mock responders against those paths.
- **Code's read:** the path-vs-JSON-RPC question is a real-API
  integration concern — out of scope for W2 per brief §4 (no real
  Betfair calls). The transport callable in `_connection.py` is shaped
  to receive arbitrary URLs, so v3 build proper can either keep the
  contract's path abstraction with a translating transport, or rewrite
  the surfaces to call Betfair JSON-RPC directly. Either is
  defensible.
- Code did NOT attempt remediation per §1 of brief — surfaced as a
  v3 build proper deliverable framing question.

### Finding F5: `customer_strategy_ref` parameter accepted but unused on placement

- **Step where it surfaced:** §6 step 7 (placement implementation).
- **Expected:** contract §11.1 specifies `customer_strategy_ref:
  Optional[str] = None` as a parameter on `place_bet`.
- **Actual:** the parameter is accepted by `place_bet`, forwarded into
  the request body as `customer_strategy_ref`, but not surfaced on
  the audit-log entry's `AuditLogEntry` shape (contract §12.1 doesn't
  list `customer_strategy_ref` among the audit fields).
- **Output:** `place_bet(..., customer_strategy_ref="2", ...)` works
  correctly; the field round-trips to Betfair via the request body.
- **Code's read:** consistent with the contract — §12.1 audit entry
  doesn't include `customer_strategy_ref` because the strategy tag is
  Betfair-side payload, not v3-side analytics-join key. v3-side analytics
  would join via `customer_order_ref`. If the operator wants strategy
  tags in audit entries for cycle-grouping, that's a backward-compatible
  addition to §12.1 in a future contract revision.
- Code did NOT attempt remediation per §1 of brief — flagged so the
  operator-Claude triage notices the gap if/when strategy-tag analytics
  become a v3 use case.

### Finding F6: rate-limit budget is placeholder; not enforced in W2

- **Step where it surfaced:** §6 step 3 (`_connection.py` design).
- **Expected:** contract §7 names rate-limit awareness as a concern that
  lives inside `betfair_client`. The contract doesn't specify enforcement
  mechanics (calls per window, soft-vs-hard limit handling, etc.) —
  Fix 4 calibration target.
- **Actual:** `_connection.RateLimitBudget` dataclass tracks call
  timestamps in a sliding window with placeholder defaults (200 calls /
  60s) but is not actually wired into the REST client request path. A
  rate-limited Betfair response (HTTP 429) is mapped to the
  `betfair_rate_limited` reason via the existing `_errors` path — that
  works. What's missing is *proactive* rate-limit enforcement (e.g.
  back-off before sending a request when the budget is exhausted).
- **Output:** all tests pass; runtime behaviour is identical to "no
  budget tracking at all" because the budget is never queried.
- **Code's read:** appropriate for v1.0 mocked-only scope. Proactive
  enforcement is operationally meaningful only against real Betfair API
  rate-limiting in v3 build proper. Surfacing now because the v3 build
  proper W3+ briefs will need to wire this in (or replace it).
- Code did NOT attempt remediation per §1 of brief — flagged for v3
  build proper triage.

---

## §12 — Self-assessment

**Did Code stay within the named anchors?** Yes. Every typed return shape
traces back to contract §8 / §9 / §10 / §11; every reason value is from
the §8.2 / §8.3 closed sets; the envelope shape matches §8.4; surface
signatures match contract §9 and §11 exactly. The streaming surface
implements all five states from §10.1 with the typed events and
subscription tracking from §10.2 / §10.6. The audit-trail entries match
§12.1. The streaming-disconnect-blocks-writes pre-check operates per §13.

**Were any out-of-scope items touched?** No. No `vps_client` work (W1).
No operational store work (W6). No v3 module consuming `betfair_client`.
No real Betfair API calls. No new dependencies beyond what W0+W1
installed (mocking is hand-rolled per W1 pattern). Auth handling is the
Protocol + `MockAuthProvider` shape only — real auth flow deferred. The
audit substrate is `StdoutAuditLogSink` + `MemoryAuditLogSink` — durable
substrate deferred.

**Did the session fit a single bounded run?** Yes. Approximately 20
minutes wall-clock from anchor-start to anchor-close. The work fit
comfortably; the streaming module — flagged in brief §6 as the most
likely budget pressure point — landed cleanly in one pass with one
iteration cycle on cache-survives-disconnect semantics (the
`market_cache_snapshot` returning `stale` rather than `unavailable`
during RECONNECTING). The fix tightened the contract interpretation
rather than scope-cutting; no partial-completion fallback per the
brief's W2.1-follow-up framing was needed.

**Was the streaming module strain point hit?** Briefly — the
RECONNECTING-state cache-snapshot semantics were ambiguous between
"unavailable because connection is down" and "stale because per-subscription
independence keeps the cache" interpretations; the contract §10.5 +
§2.4 §8.8 per-subscription-independence rule resolved it cleanly to
the "stale" shape.

**Anything Code thinks the next operator-Claude session should know
that the report doesn't otherwise capture:**

1. **Cadence-parameter placeholder constants live in two modules.**
   `streaming.py` carries six (heartbeat, reconnect, sustained-failure,
   freshness target, stale threshold); `_connection.py` carries two (max
   calls per window, window length). All are tagged "Fix 4 calibration
   target" via comments. When Fix 4 lands, operator-Claude will need to
   touch both modules — surfacing now so the Fix 4 brief drafting
   anticipates.

2. **The `streaming.py` `_handle_message` envelope shape is the v3 build
   proper integration contract.** The wire-format parser (built on
   `betfairlightweight` per DR-031) needs to produce this internal
   envelope. The shape is documented at the top of `streaming.py` and
   in the `tests/fixtures/betfair/stream_messages.py` module docstring.
   Worth naming this in the W3+ brief for live-pricing so the parser is
   commissioned alongside the consumer code.

3. **Audit-log durable substrate selection is genuinely deployment
   work.** `_audit.AuditLogSink` is a Protocol with `write(entry)`;
   `StdoutAuditLogSink` is the default. Plausible v3 build proper
   substrates: append-only file in v3's `data/` dir, structured logs
   into the operational store's audit table, or a syslog/journald sink.
   The choice doesn't affect the contract — it's a single sink-class
   swap at startup.

4. **101 tests vs 90–130 target.** Toward the lower end. Coverage
   pattern is one passing test per envelope status per surface, plus
   shape verification (envelope, error mapping, audit shape) and the
   cross-cutting streaming-blocks-writes + audit-cycle scenarios.
   Adding more would be redundant against the heuristic-driven coverage
   already in place. Self-assessed as adequate for W2 v1.0 verification
   scope; W3+ consumers will exercise more paths via integration tests.

5. **Live-pricing types live in `live_pricing.py`, imported by
   `streaming.py`.** A clean alternative would have been a shared
   `_market_data.py` module. Per W2 brief §6 step 5/6 sequencing,
   `streaming.py` was built before the full `live_pricing.py`
   functions, but the data shapes were defined in `live_pricing.py`
   first to avoid duplication. The arrangement works cleanly; flagging
   in case future operator-Claude refactors want a shared types module.

---

## §13 — Anchor (session close)

`2026-05-05 16:26 ACST` (Adelaide local, per DR-021).

**Session duration:** ~20 minutes from anchor-start to anchor-close.

**End of report.**
