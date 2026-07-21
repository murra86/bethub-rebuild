# W2 — `betfair_client` v1.0 implementation: Code brief

**Status:** Drafted Session 84. Locked at operator sign-off.
**Audience:** Claude Code, single bounded session.
**Output:** `dr029/w2_betfair_client/w2_implementation_report.md`.

---

## §1 — What this brief is and is not

This brief commissions Claude Code to implement
`betfair_client` v1.0 against the locked contract at
`dr029/2_7_api_contract_versioning/betfair_client_contract.md`,
into `bethub-v3/clients/betfair_client/v1/` (currently
empty stub from W0).

Scope: implement the typed envelope module (§8 of the
contract) reusing `vps_client`'s envelope shape with
Betfair-specific reason enumerations layered on; five
read surfaces (§9.1 operational live-pricing reads, §9.2
settlement reads, §9.3 sports-line query, §9.4
scheduled-time reads, §9.5 identifier-resolution
checks); one Streaming surface (§10 — connection
lifecycle, subscribe call surfaces, status read, order
cache shape, reconnect/heartbeat/dispatch behaviour);
three write surfaces (§11.1 bet placement, §11.2 bet
cancellation, §11.3 bet replacement); audit-trail
discipline (§12) producing one structured log entry per
write call regardless of outcome; streaming-disconnect-
blocks-writes behaviour (§13); error-mapping from raw
Betfair API exceptions and Streaming protocol errors to
the closed `BetfairReadUnavailableReason` and
`BetfairWriteUnavailableReason` sets; mocked HTTP and
Stream-message test fixtures with hand-crafted scenarios
covering each envelope status and write outcome per
surface.

Out of scope: any change to the contract itself (§2.7
versioning discipline forbids contract edits during
implementation — surfaces as findings if the contract
is ambiguous), real Betfair API calls during the
session (per Option 1: tests use mocked responses, no
live credentials in the brief or the v3 repo), cadence
parameters (Fix 4 — heartbeat threshold, subscribe
interval, reconnect back-off, polling cadence outside
burst windows are operational tuning deferred per §10
of the contract), `vps_client` work (already shipped in
W1), the operational store (W6), any v3 module that
consumes `betfair_client` (W3 onwards for live pricing,
W4 onwards for bet entry, W5 for settlement reads),
analytical reads (route through `vps_client`,
contract §15.1).

This is a single bounded Code session. Surprises become
findings in §11 of the report, not blockers — Code does
not pause mid-session for operator-Claude direction.
Remediation of any findings routes to the next
operator-Claude session's triage, not to Code's report
proposing fixes.

---

## §2 — Why this work exists

W2 is the second build session of v3 that produces
working code. W0 (closed Session 83) initialised the
repo skeleton; W1 (closed Session 84 triage) implemented
`vps_client` v1.0 — v3's read interface against the
analytical-line database. W2 fills the
`betfair_client` v1.0 stub — v3's read-and-write
interface against the operational-line live API.

`betfair_client` is the second build target because it
unblocks every operational-line v3 module: W3 (live
pricing) needs the Streaming connection and the
market-cache snapshot reads; W4 (bet entry) needs the
sports-line query, scheduled-time reads, identifier-
resolution checks, and bet placement; W5 (settlement
worker) needs the settlement reads; the racing page and
sports page UIs need the operational live-pricing
reads. With `vps_client` and `betfair_client` both
shipped, v3 build proper has both data interfaces in
place; downstream workstreams build operational logic
on top of those two boundaries.

The implementation discipline is structural: per DR-028
(the cross-database integration boundary discipline:
no caching, no denormalisation, no second integration
point), `betfair_client` is the *only* file in v3 that
knows Betfair's API shape. HTTP calls, Streaming
protocol parsing, auth handling, rate-limit awareness,
and currency translation all live inside this module.
v3 modules import typed return shapes; they never see
Betfair JSON, Streaming protocol fields, session
tokens, or rate-limit budgets. If Betfair changes
their API in future, only `betfair_client` touches.

W2 is materially more complex than W1 in three ways
worth naming up front. First, the Streaming surface is
new substrate — long-lived connection, subscription
lifecycle, message dispatch, heartbeat handling,
automatic reconnection. None of this had a counterpart
in W1's stateless reads. Second, write surfaces carry
the audit-trail cross-cutting concern — every
placement, cancellation, and replacement produces one
structured log entry regardless of outcome, joined by
`customer_order_ref` for single-cycle analysis per
standing instructions Cat 4. Third, the streaming-
disconnect-blocks-writes behaviour means write calls
inspect Streaming connection state before reaching
Betfair — a contract-level discipline that lives
inside `betfair_client` rather than in v3 modules.

Per Option 1 (operator-confirmed at brief drafting):
the session uses mocked HTTP responses and mocked
Stream-message scenarios for verification. No real
Betfair API calls during W2. Real-API integration
shifts to v3 build proper when downstream workstreams
start consuming `betfair_client`.

## §2 — Why this work exists

W2 is the second build session of v3 that produces
working code. W0 (closed Session 83) initialised the
repo skeleton; W1 (closed Session 84 triage) implemented
`vps_client` v1.0 — v3's read interface against the
analytical-line database. W2 fills the
`betfair_client` v1.0 stub — v3's read-and-write
interface against the operational-line live API.

`betfair_client` is the second build target because it
unblocks every operational-line v3 module: W3 (live
pricing) needs the Streaming connection and the
market-cache snapshot reads; W4 (bet entry) needs the
sports-line query, scheduled-time reads, identifier-
resolution checks, and bet placement; W5 (settlement
worker) needs the settlement reads; the racing page and
sports page UIs need the operational live-pricing
reads. With `vps_client` and `betfair_client` both
shipped, v3 build proper has both data interfaces in
place; downstream workstreams build operational logic
on top of those two boundaries.

The implementation discipline is structural: per DR-028
(the cross-database integration boundary discipline:
no caching, no denormalisation, no second integration
point), `betfair_client` is the *only* file in v3 that
knows Betfair's API shape. HTTP calls, Streaming
protocol parsing, auth handling, rate-limit awareness,
and currency translation all live inside this module.
v3 modules import typed return shapes; they never see
Betfair JSON, Streaming protocol fields, session
tokens, or rate-limit budgets. If Betfair changes
their API in future, only `betfair_client` touches.

W2 is materially more complex than W1 in three ways
worth naming up front. First, the Streaming surface is
new substrate — long-lived connection, subscription
lifecycle, message dispatch, heartbeat handling,
automatic reconnection. None of this had a counterpart
in W1's stateless reads. Second, write surfaces carry
the audit-trail cross-cutting concern — every
placement, cancellation, and replacement produces one
structured log entry regardless of outcome, joined by
`customer_order_ref` for single-cycle analysis per
standing instructions Cat 4. Third, the streaming-
disconnect-blocks-writes behaviour means write calls
inspect Streaming connection state before reaching
Betfair — a contract-level discipline that lives
inside `betfair_client` rather than in v3 modules.

Per Option 1 (operator-confirmed at brief drafting):
the session uses mocked HTTP responses and mocked
Stream-message scenarios for verification. No real
Betfair API calls during W2. Real-API integration
shifts to v3 build proper when downstream workstreams
start consuming `betfair_client`.

---

## §3 — Pre-reads

Required reads before Code starts:

1. `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`
   — the locked v1.0 contract Code is implementing
   against. §7 onwards is the developer-readable
   formal specification. Code implements §8 (typed
   envelope), §9 (five read surfaces), §10 (Streaming
   surface), §11 (three write surfaces), §12 (audit-
   trail discipline), §13 (streaming-disconnect-
   blocks-writes), and respects §14 (versioning
   mechanics) and §15 (out of scope).

2. `/Users/tim/Desktop/Projects/bethub-rebuild/standing_instructions.md`
   — full read per Cat 2. Particularly relevant for
   W2: Cat 3 (filesystem and tooling discipline —
   Desktop Commander default, write-script-to-`/tmp`
   + `start_process` over interactive REPL paste,
   dry-run multi-target mechanical edits before
   write); Cat 4 (single-cycle analysis discipline,
   load-bearing for §12 audit-trail join-key
   semantics); Cat 5 (operator/Claude division of
   labour — software questions are Code's, surfaces
   as findings rather than mid-session pivots).

3. `/Users/tim/Desktop/Projects/bethub-rebuild/decisions.md`
   — DR-027 (the two-database architecture decision:
   BetHub owns operational state, capture.db owns
   analytical/source data) and DR-028 (the cross-
   database integration boundary discipline: no
   caching, no denormalisation, no second integration
   point). Read for the structural rationale that
   drives "no Betfair API calls outside
   `betfair_client`" and the rationale for reads-and-
   writes sharing one module boundary.

4. `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w1_vps_client/w1_implementation_report.md`
   — W1's report, particularly §11 findings F3
   (PEP-695 type alias substrate — re-applies to
   `betfair_client`'s envelope module) and F6
   (`_clock.now_utc()` test-patchability pattern —
   recommended for adoption in W2 and beyond per
   W1 §12 self-assessment item 2).

5. `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w1_vps_client/w1_brief.md`
   — W1's brief structure as a reference shape. W2
   is a sibling brief with extended substrate; the
   shape (§§1–11) tracks W1's. Cross-reading W1
   surfaces patterns Code will reuse: error-mapping
   shape, fixture-driven verification, single
   commit at session end, post-write
   verification sweep.

Reference-only — Code reads on demand, not required
up-front:

- `dr029/2_7_api_contract_versioning/contracts_spec_brief.md`
  and `contracts_spec_report.md` — the Session 77
  Code session that drafted both contracts'
  developer-readable specifications. Useful if
  Code wants to understand why certain shapes look
  the way they do (e.g. the read-side / write-side
  reason enumeration split).

- `dr029/w0_repo_init/w0_implementation_report.md`
  and `dr029/w1_vps_client/capture_db_schema.md` —
  W0 substrate (repo skeleton, import-linter
  contracts) and W1's schema reference for
  cross-comparison if Code wants to see how the
  envelope shape ties to W1's surfaces.

- `external_api_resources.md` (rebuild root) —
  pointer set for Betfair Exchange REST and
  Streaming API documentation. Code reaches for
  this if a contract surface's intended Betfair-
  side endpoint shape needs verification (per
  standing instructions Cat 3, external API
  resources reach-for trigger).

---

## §4 — System access

Filesystem access — read-write:

- `/Users/tim/Desktop/Projects/bethub-v3/` — Code
  populates `clients/betfair_client/v1/` (currently
  empty) and adds tests under `tests/`. Code does
  not modify any other folder beyond the named
  paths in §5.

Network access — none required:

- W2 runs entirely against mocked HTTP responses
  and mocked Stream-message scenarios per Option 1.
  Code does NOT make real Betfair API calls during
  this session. No SSL handshakes to
  `stream-api.betfair.com`, no REST calls to
  `api.betfair.com`. All HTTP and Stream
  interactions are mocked using hand-rolled Python
  test fixtures with `unittest.mock` and
  `pytest.monkeypatch` (per §5.5 below) — same
  shape as W1's mocking pattern.

  Rationale: real Betfair API calls require
  credentials (session token, app key) that are
  operator-side configuration. Putting credentials
  in the brief, the v3 repo, or the Code session
  is a security failure mode. Real-API integration
  shifts to v3 build proper when downstream
  workstreams (W3 onwards) start consuming
  `betfair_client`.

- If Code finds a contract surface where the
  Betfair API shape is ambiguous and a single
  one-shot read against real Betfair would resolve
  it, that's a §11 finding — not a mid-session
  escalation. Code surfaces the ambiguity in the
  report; operator-Claude triage in the next
  session decides whether to commission a one-off
  reach-out or accept the ambiguity as a v1.0
  carry-forward.

Credentials — none in scope:

- Code does not handle, generate, store, or
  reference any Betfair credentials (session token,
  app key, certificate, password). Auth handling
  is implemented as a pluggable interface
  (`AuthProvider` Protocol or similar — Code's
  call at implementation per the contract's §7
  boundary discipline) so v3 build proper
  deployment can inject the real auth flow without
  modifying `betfair_client`. The interface stub
  plus a test-time `MockAuthProvider` are the
  v1.0 deliverables; the real auth flow lands in
  v3 build proper when real credentials become
  available.

Local toolchain — `uv` per W0 + W1. All Python
invocations via `uv run python ...` or
`uv run pytest ...`. The existing `.venv/` from W0
is the runtime; Code does not create a second venv.
Dependencies present from W0 + W1: `pydantic`,
`sqlalchemy`, `betfairlightweight`, `pytest`,
`ruff`, `mypy`, `import-linter`, `alembic`. If a
new dependency is genuinely needed, Code surfaces
it as a §11 finding rather than installing — the
v3 dependency budget is operator-visible per §9
hard limits. Mocking is hand-rolled with stdlib
`unittest.mock` plus `pytest.monkeypatch` per the
W1 pattern; no mocking library dependency required.

---

## §5 — Substantive scope

Six sub-sections covering the implementation work in
dependency order: envelope module (foundational), read
surfaces (five of them), Streaming surface (one, with
internal connection management), write surfaces (three
of them), audit-trail discipline (cross-cutting), test
fixture + verification suite (verifies all of the
above).

### §5.1 Envelope module (`envelope.py`)

Implement the typed envelope shapes from contract §8
into `bethub-v3/clients/betfair_client/v1/envelope.py`.
The shape mirrors `vps_client/v1/envelope.py` (W1
shipped) but with Betfair-specific reason enumerations:

- `EnvelopeStatus` enum (`fresh` / `stale` /
  `unavailable`) — same as `vps_client`.
- `BetfairReadUnavailableReason` enum (six values
  per contract §8.2: `genuine_absence`,
  `betfair_auth_expired`, `betfair_rate_limited`,
  `betfair_market_suspended`,
  `betfair_streaming_disconnected`,
  `betfair_market_not_found`,
  `betfair_api_unreachable`).
- `BetfairWriteUnavailableReason` enum (three values
  per contract §8.3: `betfair_write_rejected`,
  `betfair_insufficient_funds`,
  `betfair_bet_placement_in_progress`).
- `FreshEnvelope[T]`, `StaleEnvelope[T]` Pydantic v2
  generic models per contract §8.4.
- `UnavailableReadEnvelope` (carrying
  `BetfairReadUnavailableReason` + optional
  `retry_after`) per contract §8.4.
- `UnavailableWriteEnvelope` (carrying union of
  read and write reasons + optional `retry_after`,
  `rejection_code`, `rejection_detail`) per
  contract §8.4.
- `ReadEnvelope[T]` and `WriteEnvelope[T]` PEP-695
  type aliases per W1 F3 substrate (contract
  phrasing uses `typing.Union[...]` which doesn't
  survive runtime subscripting on Python 3.12+;
  PEP-695 syntax `type ReadEnvelope[U] = ...`
  resolves this — same fix W1 applied).

`as_of` timestamps are Adelaide local per DR-021. The
module exposes `now_adelaide()` and `to_adelaide()`
helpers consistent with W1's `vps_client/v1/envelope.py`.

**Implementation choice:** the envelope module is
local to `betfair_client/v1/`, not imported from
`vps_client/v1/`. The two modules contain equivalent
shapes for the shared parts but diverge on the
unavailable-reason enumerations. Per DR-030 layered
architecture, `betfair_client` does not depend on
`vps_client` — they're sibling clients, not a
dependency chain. Code duplicates the shared envelope
shape in `betfair_client/v1/envelope.py`.

This module is imported by every surface module
(§5.2–§5.4) and by tests (§5.6).

### §5.2 Read surfaces (five modules)

Each contract §9 sub-section maps to one module file
under `bethub-v3/clients/betfair_client/v1/`:

| Contract § | Module file | Public function(s) |
|---|---|---|
| §9.1 | `live_pricing.py` | `market_prices(market_id)`, `runner_best_prices(market_id, selection_id)` |
| §9.2 | `settlement.py` | `market_settlement(market_id)` |
| §9.3 | `sports_lines.py` | `sports_market_variants(event_id, market_type)` |
| §9.4 | `scheduled_time.py` | `market_scheduled_time(market_id)` |
| §9.5 | `identity.py` | `identity_check(market_id, selection_id)` |

Each module contains:

- The Pydantic v2 return-shape models exactly as
  named in the contract (`MarketPrices`,
  `RunnerBestPrices`, `MarketSettlement`,
  `SportsMarketVariant`, `MarketScheduledTime`,
  `IdentityCheck`, plus supporting models like
  `RunnerPrices`, `RunnerSettlement`, `PriceLevel`).
- The HTTP-call shape against Betfair's API — what
  endpoint, what request payload, how to parse the
  response.
- The public function with the exact signature
  from the contract.
- Mapping from raw Betfair JSON responses to the
  typed return model (handling nullable fields,
  enum coercion, currency translation per contract
  §2.4 §16 — AUD as account currency).
- Mapping from HTTP exceptions and Betfair error
  responses to envelope statuses (cross-cutting;
  see §5.5 below for the error-mapping module).

The §9.1 live-pricing reads have a special property:
per contract §10, they are satisfied from the
Streaming cache when the connection is healthy and
from REST polling when not. The public function
shape is the same; the implementation routes
internally based on Streaming connection state.
Other read surfaces (§9.2–§9.5) are REST-only.

### §5.3 Streaming surface (one module + helpers)

Implement the Streaming surface from contract §10
into `bethub-v3/clients/betfair_client/v1/streaming.py`,
with internal helper modules as needed.

The Streaming surface has three external behaviours
exposed upward:

- `streaming_status() -> StreamingStatus` — read
  current connection state, subscription state,
  heartbeat freshness.
- `market_cache_snapshot(market_id)` — same payload
  shape as `market_prices` in §9.1, satisfied from
  the Streaming cache when connection healthy.
- `order_cache_snapshot(market_id, selection_id)` —
  read current unmatched-and-matched position from
  the order cache.

Plus subscribe-registration call surfaces per
contract §10.6:

- `on_market_update(callback)` — register a callback
  invoked on each market update.
- `on_order_update(callback)` — register a callback
  invoked on each order update.

The Streaming surface owns and manages the long-lived
TCP/SSL connection to Betfair, the authentication
flow against the auth provider interface (§4 above),
the subscription lifecycle (subscribe / resubscribe
on reconnect / per-subscription independence per
contract §10.5), the heartbeat-loss detection, and
the automatic reconnection behaviour (back-off
between attempts; threshold for sustained-failure
unavailable signal). All of this is internal to
`betfair_client`; consumers see only typed envelopes
on reads and typed events on subscriptions.

**Cadence parameters not specified.** Per contract
§10 and Fix 4 deferral: heartbeat threshold, subscribe
interval, reconnect back-off cadence, and polling
cadence outside burst windows are operational tuning
deferred to v3 build proper. W2 implements the
*shape* (state machine, message-loop scaffolding,
reconnection-trigger logic) with placeholder
constants for the timing parameters that will be
calibrated post-Fix-4. The placeholders are
documented in module docstrings as "Fix 4
calibration target."

**Connection state machine.** Five connection states
per contract §10.1: `DISCONNECTED`, `CONNECTING`,
`AUTHENTICATING`, `SUBSCRIBED`, `RECONNECTING`. The
state machine and its transitions live in
`streaming.py`'s internal class (`StreamingClient`
or similar — Code's call at implementation). The
external `StreamingConnectionState` enum exposed via
`streaming_status()` mirrors the internal state.

**Mocking discipline for tests.** Tests use
hand-rolled Stream-message fixtures (per §5.6
below) with mocked socket I/O. The state machine
runs against the fixtures deterministically; no
real socket is opened during W2.

### §5.4 Write surfaces (three modules)

Each contract §11 sub-section maps to one module file:

| Contract § | Module file | Public function |
|---|---|---|
| §11.1 | `placement.py` | `place_bet(...)` |
| §11.2 | `cancellation.py` | `cancel_bet(...)` |
| §11.3 | `replacement.py` | `replace_bet(...)` |

Each module contains:

- The Pydantic v2 return-shape model
  (`BetPlacementResult`, `BetCancellationResult`,
  `BetReplacementResult`).
- The supporting enums (`BetSide`,
  `PersistenceType`).
- The HTTP-call shape against Betfair's
  `placeOrders` / `cancelOrders` /
  `replaceOrders` operations.
- The public function with the exact signature
  from the contract.
- Mapping from raw Betfair responses to the typed
  return model (echoing `customer_order_ref`,
  capturing `bet_id`, etc.).
- Mapping from rejection codes and HTTP exceptions
  to `BetfairWriteUnavailableReason` values per
  contract §8.3.
- Pre-call check against Streaming connection state
  for the §13 streaming-disconnect-blocks-writes
  behaviour (§11.1 only — placement is blocked;
  cancellation and replacement are not, per
  contract §13.4).
- Audit-log entry emission per contract §12 — every
  call produces exactly one entry regardless of
  outcome, before the call returns.

### §5.5 Cross-cutting modules (`_auth.py`, `_audit.py`,
       `_clock.py`, `_connection.py`, `_errors.py`)

Five private modules (leading underscore signals
"internal to this package") covering cross-cutting
concerns:

**`_auth.py`** — defines the `AuthProvider` Protocol
interface (Python `typing.Protocol` per Pydantic v2
+ DR-031 typing discipline) plus a `MockAuthProvider`
class for test-time use. Real `BetfairAuthProvider`
implementation is out of scope for W2; the Protocol
shape lets v3 build proper inject the real auth
without modifying `betfair_client`.

**`_audit.py`** — implements the `AuditLogEntry`
shape per contract §12.1 plus the audit-log writer.
The writer's substrate is a pluggable
`AuditLogSink` Protocol; W2 ships a
`StdoutAuditLogSink` (writes JSON-lines to stdout)
plus a `MemoryAuditLogSink` (collects entries in a
list, used by tests). Real durable substrate
(file path, log aggregator, database table) is v3
build proper deployment configuration per contract
§12.2; W2's interface lets that swap in cleanly.

**`_clock.py`** — exposes `now_utc()` as a module
attribute so tests can `monkeypatch.setattr(_clock,
"now_utc", ...)` for deterministic-clock tests
(W1 F6 substrate). All surfaces import via
`from . import _clock` and call `_clock.now_utc()`
or `_clock.now_adelaide()`.

**`_connection.py`** — REST connection management
(connection pool, rate-limit budget tracking, retry
discipline). Wraps the HTTP library
(`httpx` or `requests` — Code's call at
implementation; the contract is shape-only).
Streaming connection management lives in
`streaming.py`, not here.

**`_errors.py`** — central error-mapping module
covering both read and write surfaces. Maps raw
HTTP exceptions, Betfair rejection codes, and
Streaming protocol errors to envelope statuses
and reason values. Per-surface heuristics for
read-side row-shape reasons
(`betfair_market_not_found`, `genuine_absence`,
etc.) live in surface modules; this module
covers the cross-cutting exception-shaped
mappings and the rejection-code translation
table for write surfaces.

### §5.6 Test fixture + verification suite

Mocked HTTP responses and mocked Stream-message
scenarios under
`bethub-v3/tests/fixtures/betfair/`:

- `rest_responses.py` — Python module exposing
  hand-crafted Betfair JSON response strings (or
  Python-dict equivalents) per call surface,
  covering each envelope status outcome. Plus
  helper functions to wrap responses in mocked
  HTTP-client return shapes.
- `stream_messages.py` — Python module exposing
  hand-crafted Streaming protocol message
  sequences per scenario (clean connect, market
  data updates, order updates, heartbeat
  sequences, disconnect-and-reconnect
  scenarios, sustained-failure scenarios).

Verification suite under
`bethub-v3/tests/clients/betfair_client/v1/`:

- `test_envelope.py` — envelope shapes serialise
  correctly, status discrimination works, generic
  type parameter is honoured for both
  `ReadEnvelope` and `WriteEnvelope`.
- One `test_<surface>.py` file per read surface
  (five files): each surface returns `fresh` for
  clean response, `stale` where applicable
  (live-pricing reads), `unavailable` for each
  applicable reason.
- `test_streaming.py` — connection state machine
  transitions under each scenario; subscription
  lifecycle; heartbeat-loss detection;
  reconnection back-off; per-subscription
  independence; sustained-failure unavailable
  signalling.
- One `test_<surface>.py` file per write surface
  (three files): each surface returns `fresh` for
  successful placement / cancel / replace,
  `unavailable` for each applicable write
  rejection reason, and audit-log entries are
  emitted correctly per outcome.
- `test_audit.py` — audit-log entry shape;
  one-entry-per-write discipline; outcome
  mapping per write outcome; `customer_order_ref`
  join-key correctness for retry-cycle
  reconstruction.
- `test_streaming_blocks_writes.py` — placement
  is blocked when streaming state is non-
  `SUBSCRIBED`; cancellation and replacement are
  not blocked; the blocked envelope carries the
  expected reason and `retry_after` shape.
- `test_error_mapping.py` — cross-cutting mapping
  rules from `_errors.py`. Mocks HTTP exceptions
  and Betfair rejection codes; confirms each maps
  to the expected envelope status / reason.

Test count target: roughly 90–130 tests total. Each
read surface lands in the 8–15 range (similar to W1,
plus extra coverage for the streaming-cache-vs-REST-
fallback behaviour on §9.1); each write surface
8–12 (placement / cancel / replace per outcome,
plus audit-log emission); streaming module 15–25
(state machine transitions, multiple scenarios);
audit module 5–10; cross-cutting 5–10. Range, not
hard line — Code exceeds with rationale or
undershoots with rationale, flagged in §12 self-
assessment.

The test conftest pins `_clock.now_utc()` to a
fixture-stable reference per W1 F6 pattern. Without
the pin, freshness arithmetic against fixture
timestamps would flake as wall-clock advances.

---

## §6 — Sequencing within session

Code does the work in this order:

1. **Pre-flight: read the contract end-to-end plus
   the W1 implementation report.** Confirm the
   contract is at v1.0 locked status (header line)
   and that no carry-forward findings from W1
   apply to envelope shape beyond F3 (PEP-695)
   and F6 (`_clock.now_utc()`). If the contract
   shows any `**Status:** drafting` or unlocked
   markers, halt before touching `bethub-v3/` —
   write a minimal report containing only §1
   anchor, §2 pre-flight failure detail, §11 with
   a single finding naming the contract-not-locked
   issue, and §13 anchor. Exit cleanly.

2. **Implement `envelope.py`.** Pydantic models
   per §5.1, PEP-695 type aliases per W1 F3
   substrate. Smoke test with `uv run python -c
   "..."` to confirm models instantiate and
   `ReadEnvelope[X]`, `WriteEnvelope[X]` are
   runtime-subscriptable.

3. **Implement cross-cutting modules in
   dependency order:**
   - `_clock.py` (no dependencies; stand-alone).
   - `_auth.py` (`AuthProvider` Protocol +
     `MockAuthProvider` shipped class per §5.5).
   - `_audit.py` (`AuditLogEntry` model +
     `AuditLogSink` Protocol +
     `StdoutAuditLogSink` default +
     `MemoryAuditLogSink` for tests).
   - `_connection.py` (REST connection wrapper
     + rate-limit budget tracking; HTTP library
     choice is Code's call at implementation).
   - `_errors.py` (cross-cutting exception →
     envelope mapping; rejection-code translation
     table for write surfaces).

4. **Implement read surfaces in dependency
   order:**
   - `live_pricing.py` (§9.1 — most complex due
     to streaming-cache-vs-REST-fallback;
     deferred until streaming module exists).
     **Skip for now; revisit at step 6.**
   - `settlement.py` (§9.2).
   - `sports_lines.py` (§9.3).
   - `scheduled_time.py` (§9.4).
   - `identity.py` (§9.5).

   For each surface: write the module, write its
   test file, run `uv run pytest
   tests/clients/betfair_client/v1/test_<surface>.py`
   green before moving on.

5. **Implement Streaming surface (`streaming.py`).**
   Connection state machine per contract §10.1
   (five states); subscribe call surfaces per
   §10.2; status read per §10.3; order cache
   shape per §10.4; reconnect / heartbeat /
   dispatch logic per §10.5; subscribe / dispatch
   upward per §10.6. Hand-rolled Stream-message
   fixtures in `tests/fixtures/betfair/stream_
   messages.py`; tests cover state machine
   transitions, subscription lifecycle, heartbeat
   loss, reconnection back-off, per-subscription
   independence, sustained-failure unavailable
   signalling. Cadence parameters use placeholder
   constants documented as "Fix 4 calibration
   target." Run `uv run pytest
   tests/clients/betfair_client/v1/test_
   streaming.py` green before moving on.

6. **Return to `live_pricing.py` (§9.1).**
   Implement against the now-existing Streaming
   cache. Routing logic: when streaming state is
   `SUBSCRIBED` and heartbeats current, satisfy
   from cache; otherwise fall through to REST.
   Tests cover both paths.

7. **Implement write surfaces in dependency
   order:**
   - `placement.py` (§11.1 — most complex due to
     streaming-disconnect-blocks-writes pre-check).
   - `cancellation.py` (§11.2).
   - `replacement.py` (§11.3).

   For each surface: write the module, write its
   test file (covering each write outcome plus
   audit-log emission verification), run green
   before moving on. Plus
   `test_streaming_blocks_writes.py` and
   `test_audit.py` runs against the now-complete
   audit and streaming substrates.

8. **Wire up `__init__.py` re-exports.** v3
   modules import via `from clients.betfair_
   client.v1 import market_prices, place_bet,
   ReadEnvelope, ...` — flat surface, not
   reaching into module files.

9. **Final verification sweep:**
   - `uv run ruff check` — exits 0.
   - `uv run mypy .` — exits 0.
   - `uv run lint-imports` — five contracts
     kept, zero broken (W0 substrate plus the
     new `betfair_client` paths covered by the
     existing layered-architecture contract).
   - `uv run pytest -v` — all tests pass; W0
     skeleton tests plus W1 tests plus new W2
     tests.
   - `git status` — only intended files changed.

10. **Single git commit** covering everything in
    this session. Commit message: `W2:
    betfair_client v1.0 implemented per locked
    contract (§9.1–§9.5 + §10 streaming + §11.1–
    §11.3 + §12 audit + §13 streaming-disconnect
    + envelope + error mapping + fixtures +
    tests)`.

If the work runs over budget at any step (any
surface or the streaming module taking longer than
expected), Code finishes the current module and
surfaces the remainder as a §11 finding rather
than continuing past budget. Partial implementation
with clean coverage on what's done beats complete-
but-untested everything. The streaming module
specifically (step 5) is the most likely point of
budget pressure given W2's complexity differential
over W1; if step 5 strains, finishing steps 1–4
plus streaming-state-machine-only (no
reconnection/heartbeat behaviour) is a defensible
partial outcome — surface in §11 as a scope-
adjustment finding so the next operator-Claude
session can commission a W2.1 follow-up.

---

## §7 — Empirical verification

Success criteria — every criterion must pass clean
for the report to mark verification as passed:

1. `bethub-v3/clients/betfair_client/v1/envelope.py`
   exists; envelope models instantiate without
   error; `ReadEnvelope[X]` and `WriteEnvelope[X]`
   are runtime-subscriptable.

2. All five read-surface modules
   (`live_pricing.py`, `settlement.py`,
   `sports_lines.py`, `scheduled_time.py`,
   `identity.py`) exist at named paths; each
   exports the public function(s) with the
   signature(s) from contract §9.

3. `streaming.py` exists; the connection state
   machine implements all five states from
   contract §10.1 with valid transitions; subscribe
   call surfaces, status read, order cache shape,
   reconnect/heartbeat/dispatch logic implemented
   per contract §10.

4. All three write-surface modules
   (`placement.py`, `cancellation.py`,
   `replacement.py`) exist at named paths; each
   exports the public function with the signature
   from contract §11; each emits exactly one
   audit-log entry per call regardless of outcome.

5. Cross-cutting modules (`_auth.py`, `_audit.py`,
   `_clock.py`, `_connection.py`, `_errors.py`)
   exist; `AuthProvider` Protocol + `MockAuthProvider`
   shipped; `AuditLogSink` Protocol +
   `StdoutAuditLogSink` default + `MemoryAuditLogSink`
   for tests.

6. `bethub-v3/tests/fixtures/betfair/rest_responses.py`
   and `bethub-v3/tests/fixtures/betfair/stream_messages.py`
   exist and provide the hand-crafted mock
   scenarios per §5.6.

7. `uv run ruff check` exits 0 with no findings.

8. `uv run mypy .` exits 0 with no findings.

9. `uv run lint-imports` exits 0 with five
   contracts kept, zero broken.

10. `uv run pytest -v` exits 0; W0 skeleton tests
    still pass; W1 tests still pass; all new W2
    tests pass; total test count is within the
    §5.6 target range or has a §12 rationale.

11. The streaming-disconnect-blocks-writes
    behaviour (contract §13) is verified by
    `test_streaming_blocks_writes.py` — placement
    blocked when state is non-`SUBSCRIBED`;
    cancellation and replacement not blocked;
    blocked envelope carries the expected reason
    and `retry_after`.

12. The audit-trail discipline (contract §12) is
    verified by `test_audit.py` — one entry per
    write call regardless of outcome;
    `customer_order_ref` join-key is correctly
    populated for retry-cycle reconstruction.

13. `git log` shows exactly one new commit on the
    main branch with the §6 step 10 message.

---

## §8 — Output spec

Single output file:
`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w2_betfair_client/w2_implementation_report.md`.

Section structure:

- §1 — Anchor (session start, Adelaide local).
- §2 — Pre-flight (contract status verified;
  any halt conditions encountered).
- §3 — Envelope module summary (shapes, PEP-695
  application, smoke-test result).
- §4 — Per-read-surface implementation summary
  (one sub-section per surface; HTTP shape,
  edge cases encountered, test coverage).
- §5 — Streaming surface implementation summary
  (state machine shape, subscription handling,
  reconnection behaviour, fixtures used).
- §6 — Per-write-surface implementation summary
  (one sub-section per surface; HTTP shape,
  rejection-code handling, audit-log emission,
  streaming-disconnect pre-check for placement).
- §7 — Cross-cutting modules summary (`_auth`,
  `_audit`, `_clock`, `_connection`, `_errors`).
- §8 — Fixture summary (REST responses per
  surface, Stream-message scenarios, status
  coverage).
- §9 — Final verification (verbatim output of
  every §7 success criterion check).
- §10 — Git state.
- §11 — Findings (in F1, F2, ... format like W0
  and W1).
- §12 — Self-assessment (Did Code stay within
  named anchors? Out-of-band actions? Did the
  session fit bounded scope? Was the streaming
  module strain point hit? Anything next
  operator-Claude session should know that the
  report doesn't otherwise capture?).
- §13 — Anchor (session close, Adelaide local).

Length anticipation: ~800–1200 lines. Range, not
hard line — exceed with rationale in §12. W2 is
materially more work than W1; report length should
reflect that.

The report does NOT contain:

- Recommendations for the next brief (W3+).
- Proposed contract edits.
- Speculation about W3+ scope.
- Performance benchmarks or load testing (W2 is
  correctness, not performance — Streaming
  message-loop performance is a v3 build proper
  concern when real Betfair traffic is in scope).
- Real Betfair API call attempts or results.

---

## §9 — Hard limits — what's NOT in scope

Non-negotiable exclusions:

- **No contract edits.** §2.7 versioning discipline
  is immutable during implementation. If the
  contract is genuinely ambiguous, surface as a §11
  finding; Code does not edit
  `betfair_client_contract.md` even to fix typos.
- **No real Betfair API calls.** Per Option 1 and §4
  network-access discipline. No SSL handshakes to
  `stream-api.betfair.com`, no REST calls to
  `api.betfair.com`. All HTTP and Stream
  interactions are mocked.
- **No credentials handled.** No session tokens, no
  app keys, no certificates, no passwords. Auth
  is implemented as a pluggable interface with a
  shipped `MockAuthProvider`; the real
  implementation is out of scope.
- **No `vps_client` work.** That shipped in W1.
- **No operational-store work, no schema for v3's
  own database.** That's W6.
- **No v3 modules consuming `betfair_client`.** Live
  pricing UI, bet entry, settlement worker — all
  W3 onwards.
- **No new dependencies beyond what W0 + W1
  installed.** If a new library is genuinely
  needed, surface as §11 finding rather than
  installing. Hand-rolled mocking is the established
  pattern (W1 substrate); no mocking library
  required.
- **No global Python state changes.** All work
  via `uv run`.
- **No commits beyond step 10.** Single commit at
  session end. If toolchain checks need
  adjustment, apply them before step 10 — do not
  amend after. Substrate: W0 Finding F5, encoded
  into W1 §9, re-encoded here.
- **No operator escalation mid-session.** Code
  runs end-to-end, surfaces findings in the
  report, doesn't ping operator-Claude mid-flight
  asking for direction.
- **No Streaming protocol parsing in v3 modules.**
  All Streaming protocol fields, message shapes,
  and protocol-level error handling stay inside
  `streaming.py` (or its internal helpers).
  Consumers see typed events only.
- **No raw Betfair JSON in v3 modules.** All
  Betfair JSON parsing stays inside
  `betfair_client/v1/`. Consumers see Pydantic
  models only. If a Betfair field is genuinely
  needed but not yet in the contract, surface
  as a §11 finding (backward-compatible-addition
  candidate per contract §14.4).
- **No analytical-store writes.** `betfair_client`
  does not write to `capture.db` or any
  analytical store. Per contract §15.3.
- **No account-management surfaces.** Fund
  transfers, deposits, withdrawals, account
  settings, statement queries are out of scope
  per contract §15.4. No `account_*` methods at
  v1.0.
- **No generic market-discovery surfaces beyond
  the contract.** `listMarketCatalogue`-style
  arbitrary-filter discovery is out of scope per
  contract §15.5. Only the contract's specific
  discovery surfaces (§9.3 sports-line query, the
  racing/sports market subscription scopes in
  §10.2) are exposed.

---

## §10 — What happens after Code's session

Next operator-Claude session reads
`w2_implementation_report.md` end-to-end, then:

1. **Triage §11 findings** per
   `bethub-brief-drafting` skill §10. Classify
   each finding (cosmetic / blocking /
   scope-question / drift); route to W3
   carry-forward, micro-brief, operator decision,
   or accepted.

2. **Triage §12 self-assessment.** Surface
   anything Code flagged about brief shape or
   session strain. The streaming module is the
   most likely strain point — if Code hit a
   partial-completion fallback per §6, the
   triage routes the remainder to a W2.1
   follow-up brief drafted in the next session.

3. **Confirm W3 has clean foundation.** If yes,
   W3 brief drafting opens (live pricing
   workstream — Streaming cache through to UI).
   If no, micro-brief or operator-side correction
   first.

Code does NOT produce the W3 brief or any W2.1
follow-up brief. Brief drafting is operator-Claude
work, drawing on the W2 report plus the locked
contracts and any DRs needed for the next
workstream's structural rationale.

---

## §11 — Cross-references

- **Contract:**
  `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  (locked Session 75 + Session 77 + Session 78).
  v1.0 immutable; W2 implements against it.
- **DRs invoked:**
  - DR-027 (the two-database architecture
    decision: BetHub owns operational state,
    capture.db owns analytical/source data).
  - DR-028 (the cross-database integration
    boundary discipline decision: no caching,
    no denormalisation, no second integration
    point) — load-bearing for "no Betfair API
    calls outside `betfair_client`" and for
    reads-and-writes-share-the-module rationale.
  - DR-019 (derived state on read) —
    load-bearing for the contract's exclusion
    of CLV reconstruction and other analytics-
    derived fields.
  - DR-021 (timestamp anchoring, Adelaide
    local time) — applies to envelope `as_of`,
    audit-log entry timestamps, and all report
    timestamps.
  - DR-030 (v3 repo layout) — `betfair_client`
    lives in `clients/` per layered architecture;
    `import-linter` enforces.
  - DR-031 (v3 tech stack) — Pydantic v2,
    Python 3.12+, mypy strict, Protocol-based
    interfaces.
- **Prior session records:**
  - `sessions/SESSION_82.md` — W0 brief drafting.
  - `sessions/SESSION_83.md` — W0 triage + W1
    brief drafting.
  - `sessions/SESSION_84.md` — W1 triage + W2
    brief drafting (this session).
- **Prior reports:**
  - `dr029/w0_repo_init/w0_implementation_report.md`
    — W0 foundation.
  - `dr029/w1_vps_client/w1_implementation_report.md`
    — W1 sibling-client substrate; F3 (PEP-695)
    and F6 (`_clock.now_utc()`) substrate carried
    forward into W2.
- **Sibling artefacts:**
  - `dr029/w1_vps_client/w1_brief.md` — W1's
    brief structure as a reference shape; W2
    tracks the same §§1–11 shape with extended
    substrate.
  - `dr029/w1_vps_client/capture_db_schema.md` —
    W1's schema reference; not load-bearing for
    W2 but cross-comparable for envelope shape.
- **Carry-forward operator-side context for W2
  triage at next session:**
  - W1 F1 (event_id ↔ market_id conflation) —
    accepted as v1.0 default, no W2 implication.
  - W1 F2 sharpening (Thoroughbred label includes
    harness undifferentiated) — capture.db side;
    no W2 implication for Betfair-side data.
  - W1 F3 (PEP-695 type alias) — applied to W2
    envelope per §5.1.
  - W1 F4 (StewardsStatus default OFFICIAL) —
    capture.db side; no W2 implication.
  - W1 F5 (sectional_times_seconds always None) —
    capture.db side; no W2 implication.
  - W1 F6 (`_clock.now_utc()` test pattern) —
    applied to W2 per §5.5.
- **Parking-lot items excluded from W2 scope:**
  - Operational store schema (W6).
  - Live pricing UI / consumer paths (W3).
  - Bet entry write-call sites (W4).
  - Settlement worker reconciliation (W5).
  - Burst review workflow (W7).
  - Cutover (W8).
  - §2.10 bucket-1 backward-compatible
    additions (P1, post-build).
  - Analytical layer scoping (P2, post-build).
  - Real Betfair API integration (deferred to
    v3 build proper W3+).
  - Real auth flow implementation (deferred to
    v3 build proper W3+).
  - Audit-log durable substrate selection
    (deferred to v3 build proper deployment
    configuration).
  - PASSIVE bet-delay model handling (§2.4
    §15.4 v3.1+ capability).
