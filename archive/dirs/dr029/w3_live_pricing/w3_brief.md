# W3 — Live pricing consumer path: Code brief

**Workstream:** W3 (live pricing — Streaming
cache through to consumer-side reading paths).
**Repo target:**
`/Users/tim/Desktop/Projects/bethub-v3/clients/betfair_client/v1/`
plus contract revision under
`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`.
**Contract:**
`dr029/2_7_api_contract_versioning/betfair_client_contract.md`
v1.0 (locked Sessions 75/77/78), with one
backward-compatible revision in this brief
(F5 `strategy_tag` addition to §12.1).
**Substrate:** W2 implementation report
(`dr029/w2_betfair_client/w2_implementation_report.md`,
Session 84/85).

---

## §1 — What this brief is and is not

This brief commissions Code to ship the
**live-pricing consumer path** for v3 build
proper, scoped to the library/consumer side
only.

### What this brief is

Four substantive deliverables, all landing
inside `bethub-v3/clients/betfair_client/v1/`
(or extending its public surface), plus one
small backward-compatible revision to the
locked Betfair client contract:

1. **Streaming wire-format parser** built on
   `betfairlightweight` per DR-031 (the v3
   tech stack decision). Produces the
   `_handle_message` internal envelope shape
   that `streaming.py` already consumes.
   W2's streaming surface ships the
   post-parse dispatch path; this brief
   ships the pre-parse path that feeds it.
   Surfaced as W2 finding F2 (Session 85
   triage).

2. **Translating transport adapter** for
   path-style ↔ Betfair JSON-RPC translation.
   W2's contract uses path-style endpoints
   (`/v1/market/{market_id}/prices`) as a
   clean abstraction; real Betfair Exchange
   REST uses JSON-RPC over
   `api.betfair.com/exchange/betting/` with
   method names. The adapter sits in
   `_connection.py` or alongside it; tests
   register against the path abstraction;
   adapter does the translation behind the
   curtain. Surfaced as W2 finding F4 with
   Option A locked (Session 85 triage).

3. **F5 contract revision** —
   `strategy_tag: Optional[str] = None` added
   to §12.1 audit-log entry. Backward-compatible
   addition; distinct from Betfair's
   `customer_strategy_ref` (which stays as
   Betfair-payload). Enables clean Strategy
   1/2/3/4 cycle-grouping at audit time.
   Small enough to fold into this brief
   rather than its own arc.

4. **Consumer-side reading paths** — typed
   helper functions inside `betfair_client`
   v1.x that wrap the cache-vs-REST routing
   in higher-level "give me live prices for
   this market" calls. No new modules
   outside `betfair_client`. The shape is a
   public surface that future v3 callers
   (W4 bet entry, W7 burst review, the
   eventual UI service layer) will consume.

### What this brief is not

This brief explicitly excludes:

- **UI substrate.** No React + TypeScript
  + Vite work. The frontend that renders
  live prices to the operator is a separate
  workstream that lands after W3's library
  code is in.
- **Service layer.** No new modules outside
  `betfair_client`. v3's eventual API/service
  layer that wraps library calls in
  v3-shaped operations is a future
  workstream — guessing at its shape now
  would build something W4 and W7 may not
  actually want.
- **Real Betfair API integration.** No real
  socket opening, no real REST calls, no
  real auth flow. W3 stays mocked-only per
  W2's pattern (brief §4). Real-API
  integration is a v3 build proper
  deployment concern, post-W3.
- **Operational store integration.** No
  reads from or writes to v3's operational
  store. W6 owns operational store schema;
  W3 ships library code only.
- **Proactive rate-limit enforcement.**
  Surfaced as W2 finding F6. The
  `_connection.RateLimitBudget` placeholder
  stays as-is; proactive enforcement is
  operationally meaningful only against real
  Betfair API rate-limiting in v3 build
  proper deployment.

### Frame

Library brief, single bounded session, named
anchors only, no edits outside scope. Mocked
tests only. Pattern mirrors W2 brief shape
(eleven sections, §11 verification criteria,
§12 self-assessment). Three v3-build-proper
substrate decisions (F4 Option A, F5
strategy_tag, F3 mirror enums kept) are
inputs, not items to re-litigate.

---
## §2 — Why this work exists

### Operating impact

W3 ships the data substrate that makes
**burst review** possible — the operating
cadence where Strategy 1 (Safety Net,
promo-driven insurance bets, ~95% of current
profit) and Strategy 2 (Price Booster,
top-fluc / best-of-best / bonus-winnings
promos, the remaining ~5%) are actually
placed.

Burst review's shape: the operator scans a
set of races approaching the jump, reads
live prices and recent movement, identifies
runners that match a strategy's promo
criteria, and places bets at the live price
within the burst window (typically the last
few minutes before jump). The data the
operator needs in front of them at that
moment is live Betfair pricing — refreshed
fast enough that the price they're reading
matches the price the bet will be placed
at.

W2 shipped the streaming cache and the
post-parse dispatch path, but the cache is
populated from a `_handle_message` envelope
that doesn't yet have a real wire-format
producer feeding it — so today the cache is
populated only by hand-crafted test fixtures.
W3 closes that gap by shipping the parser,
which produces the envelope from real Betfair
Streaming protocol frames.

W3 also ships the path-style ↔ Betfair
JSON-RPC translation (W2 contract uses path
abstractions, real Betfair API uses JSON-RPC
method calls), which means the REST fallback
paths in `live_pricing.py` will actually
reach Betfair when called against a real
deployment.

In short: W2 made the cache exist; W3 makes
the cache fillable from real data and the
REST fallbacks reachable. Together they form
the live-pricing data layer that burst review
(W7) and bet entry (W4) consume.

The strategic stake is straightforward.
Strategy 1 is 95% of current profit and is
heavily promo-dependent — books recognise
the promo-cycling pattern quickly, and any
operational friction (slow data, missed
windows, settlement delays) compounds into
account-health risk. W3's library code
needs to be clean enough that downstream
consumers don't have to work around it.

Strategy 2 is the smaller share but has the
best account-health profile of the four
(price-uplift bets look like ordinary
punting). Faster live pricing makes Strategy
2's drifter-identification cleaner, which
matters more as Strategy 2's share grows.

Strategies 3 and 4 are aspirational; W3 is
not built around them, but the library
shape needs to be general enough that future
analytical layers can read the same cache.

### Build sequence

W3 closes `betfair_client` to v1.x complete
state for v3 build proper. After W3 lands:

- **W4 (bet entry + write surfaces)
  unblocked.** W4 commissions the v3-side
  bet-entry workflow — placement, sports
  line specification, identifier-resolution
  sanity checks. W4 needs the live-pricing
  read paths W3 ships (a placement-time
  sanity check reads current price before
  placing).
- **W7 (Burst Review workflow) unblocked.**
  W7 is the operator-facing burst review
  surface. It consumes W3's library directly
  for live pricing.
- **W5 and W6 not directly unblocked.** W5
  (settlement worker) is `blocked-on-W4`;
  W6 (operational store + session ops) is
  `blocked-on-W1` (already met).

Three substrate decisions from W2 triage
(Session 85) are inputs to this brief, not
items to re-litigate:

1. **F4 Option A locked** — translating
   transport adapter for path-style ↔
   JSON-RPC. Lives in `_connection.py` or
   alongside it.
2. **F5 strategy_tag locked** —
   backward-compatible addition to §12.1
   audit-log entry, distinct from Betfair's
   `customer_strategy_ref`. Lands as a
   small contract revision in this brief.
3. **F3 mirror enums kept duplicated** —
   `BetSideStr` / `PersistenceTypeStr` stay
   in `_audit.py` for v1.x. Refactor only
   if duplication surfaces elsewhere.

Two further substrate items from W2 carry
forward but are *not* W3's scope (flagged
explicitly in §9 hard limits):

- **F6 proactive rate-limit enforcement** —
  Fix 4 brief / v3 build proper deployment
  territory.
- **§12 self-assessment item 3 — audit-log
  durable substrate selection** — deployment
  configuration, single sink-class swap at
  startup. Not a contract or library shape
  decision.

---
## §3 — Pre-reads

Required reads before Code starts:

1. `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`
   — the locked v1.0 contract. W3 implements
   against §10 (Streaming surface — the parser
   produces the envelope `streaming.py` already
   consumes), §9 (live-pricing read surfaces —
   the consumer reading paths wrap these), and
   §12 (audit-trail discipline — F5 strategy_tag
   revision lands here as a backward-compatible
   addition). Code respects §14 (versioning
   mechanics) when applying the F5 revision.

2. `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w2_betfair_client/w2_implementation_report.md`
   — W2's full implementation report. Particularly
   §5 (streaming surface implementation — the
   `_handle_message` envelope shape, the cache
   helpers, the cadence-parameter placeholders),
   §11 findings F2 / F4 / F5 (the substrate items
   W3 ships against), and §12 self-assessment items
   1 and 2 (the cadence-parameter constants live
   in two modules — `streaming.py` six,
   `_connection.py` two; the `_handle_message`
   envelope is the integration contract).

3. `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w2_betfair_client/w2_brief.md`
   — W2's brief structure as a reference shape.
   W3 is a sibling brief; the shape (§§1–11)
   tracks W2's. Cross-reading W2 surfaces patterns
   Code reuses: error-mapping shape, fixture-driven
   verification, single commit at session end,
   post-write verification sweep, mocked-only test
   discipline.

4. `/Users/tim/Desktop/Projects/bethub-rebuild/standing_instructions.md`
   — full read per Cat 2. Particularly relevant for
   W3: Cat 3 (filesystem and tooling discipline —
   Desktop Commander default, write-script-to-`/tmp`
   + `start_process` over interactive REPL paste,
   dry-run multi-target mechanical edits before
   write); Cat 4 (single-cycle analysis discipline
   — load-bearing for the F5 strategy_tag revision
   rationale); Cat 5 (operator/Claude division of
   labour — software questions are Code's, surfaces
   as findings rather than mid-session pivots).

5. `/Users/tim/Desktop/Projects/bethub-rebuild/decisions.md`
   — DR-030 (v3 repo layout / module-boundary
   discipline) and DR-031 (v3 tech stack —
   `betfairlightweight` named as the Streaming
   wire-format library). Both are load-bearing for
   W3: DR-030 governs where the parser and adapter
   live (inside `betfair_client/v1/`); DR-031
   governs how the parser is built.

6. The W2 codebase itself at
   `/Users/tim/Desktop/Projects/bethub-v3/clients/betfair_client/v1/`,
   single commit `254fcfc`. Code reads
   `streaming.py` (post-parse dispatch path it
   feeds), `_connection.py` (transport callable it
   wraps), `_audit.py` (audit-log entry shape it
   extends), `live_pricing.py` (read surfaces it
   wraps), and the test fixtures at
   `tests/fixtures/betfair/`. The 158 passing
   tests (101 W2 + 51 W1 + 6 W0) are the
   regression substrate.

Reference-only — Code reads on demand, not required
up-front:

- `dr029/2_7_api_contract_versioning/contracts_spec_brief.md`
  and `contracts_spec_report.md` — the Session 77
  Code session that drafted the developer-readable
  contract specifications. Useful if Code wants
  the rationale behind contract shapes.

- `dr029/w1_vps_client/w1_implementation_report.md`
  — W1's report. F3 (PEP-695 type alias substrate)
  and F6 (`_clock.now_utc()` test-patchability)
  re-apply to W3 if any new typed shapes ship.

- `external_api_resources.md` (rebuild root) —
  pointer set for Betfair Exchange REST and
  Streaming API documentation. Code reaches for
  this when verifying real Betfair JSON-RPC method
  shapes (for the F4 translating adapter) or real
  Betfair Streaming protocol frame shapes (for the
  F2 wire-format parser).

- `betfairlightweight` library documentation —
  Code reaches for the library's own documentation
  (Python package, available via `uv add
  betfairlightweight` per DR-031) when implementing
  the parser. The library handles socket-level
  frame reading; Code's job is to map the library's
  output shapes into the `_handle_message` internal
  envelope shape.

---
## §4 — System access

Filesystem access — read-write:

- `/Users/tim/Desktop/Projects/bethub-v3/` — Code
  extends `clients/betfair_client/v1/` (currently
  populated by W2 at single commit `254fcfc`) and
  adds tests under `tests/`. Code does not modify
  any other folder beyond the named paths in §5.

Filesystem access — write to one path outside
the v3 repo:

- `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  — Code applies the F5 strategy_tag revision to
  §12.1 of this file (backward-compatible addition
  per §5.3 below). Code touches no other section
  of the contract; the revision is surgical, with
  the version-history footer updated per the
  contract's §14 versioning mechanics.

Network access — none required:

- W3 runs entirely against mocked HTTP responses
  and mocked Streaming-protocol-frame scenarios,
  same pattern as W2. Code does NOT make real
  Betfair API calls during this session. No SSL
  handshakes to `stream-api.betfair.com`, no
  REST calls to `api.betfair.com`. All HTTP and
  Streaming interactions are mocked using
  hand-rolled Python test fixtures with
  `unittest.mock` and `pytest.monkeypatch` per
  W1/W2 pattern.

  Rationale: real Betfair API calls require
  credentials that are operator-side configuration.
  Putting credentials in the brief, the v3 repo, or
  the Code session is a security failure mode.
  Real-API integration shifts to v3 build proper
  deployment.

- If Code finds a Betfair Streaming protocol
  frame shape or JSON-RPC method shape where the
  real Betfair behaviour is ambiguous and a single
  one-shot real-API read would resolve it, that's
  a §11 finding — not a mid-session escalation.
  Code surfaces the ambiguity in the report;
  operator-Claude triage in the next session
  decides whether to commission a one-off
  reach-out or accept the ambiguity as a v1.x
  carry-forward.

Credentials — none in scope:

- Code does not handle, generate, store, or
  reference any Betfair credentials (session
  token, app key, certificate, password). The
  `AuthProvider` Protocol from W2 is already in
  place at `_auth.py`; W3 reuses it. The real
  auth flow lands in v3 build proper deployment
  when real credentials become available.

Local toolchain — `uv` per W0/W1/W2. All Python
invocations via `uv run python ...` or
`uv run pytest ...`. The existing `.venv/` from W0
is the runtime; Code does not create a second
venv. Dependencies present from W0 + W1 + W2:
`pydantic`, `sqlalchemy`, `betfairlightweight`,
`pytest`, `ruff`, `mypy`, `import-linter`,
`alembic`. `betfairlightweight` is already a
declared dependency per DR-031; W3 uses it
substantively for the first time (W2 declared
the dependency but did not exercise the library
because the parser was deferred). If a new
dependency is genuinely needed, Code surfaces
it as a §11 finding rather than installing.
Mocking remains hand-rolled with stdlib
`unittest.mock` plus `pytest.monkeypatch`.

---
## §5 — Substantive scope

Four deliverables, sequenced substrate-first per
§5.0:

- §5.1 — Streaming wire-format parser
- §5.2 — Translating transport adapter
- §5.3 — F5 contract revision (strategy_tag
  addition to §12.1 audit-log entry)
- §5.4 — Consumer-side reading paths

Each deliverable lands as its own commit-able
unit; Code commits all four together at session
end per W2 pattern.

### §5.1 — Streaming wire-format parser

**What this is.** A new module
`clients/betfair_client/v1/_stream_parser.py`
(name is Code's call) that consumes raw Betfair
Streaming protocol frames and produces the
internal `_handle_message` envelope shape
(`{"op": "...", "payload": {...}}`) that W2's
`streaming.py` already consumes.

**Foundation library.**
`betfairlightweight` per DR-031 (the v3 tech
stack decision). The library handles
socket-level frame reading, TLS handshake, and
the wire-format encoding/decoding. Code's job
is to map the library's output shapes into the
`_handle_message` internal envelope.

**Subscription scope coverage.** Both
`RACING_AU` and `SPORTS_AU` per contract §10.2.
The parser is sport-agnostic at the wire level —
Betfair Streaming uses the same frame shapes
(`mcm`, `ocm`, status, heartbeat) regardless of
sport. Sport-specific consumption logic (e.g.
handicap lines, total-points markets) sits in
the read surfaces (`live_pricing.py`,
`sports_lines.py`), not in the parser. The
parser handles frame shapes, not market
semantics.

**Frame types the parser handles.** Per Betfair
Streaming protocol documentation (reach for
`external_api_resources.md` if shape verification
is needed):

- `mcm` (market change message) — full image
  and delta variants. Maps to `op="market_image"`
  or `op="market_delta"` in the internal
  envelope.
- `ocm` (order change message) — unmatched and
  matched-position variants. Maps to
  `op="order_unmatched"` or
  `op="order_matched"`.
- `status` — connection-level status messages.
  Maps to `op="status"` with status code in the
  payload (e.g. `503` for degraded, recovery
  signals).
- `heartbeat` — keep-alive messages. Maps to
  `op="heartbeat"`.
- `connection` and `auth` ack — initial
  handshake messages. Map to `op="connection_ack"`
  and `op="auth_ack"`.
- `unknown` — defensive catch-all for frame
  shapes the parser doesn't recognise. Maps to
  `op="unknown"` with the raw frame in the
  payload, plus a log warning. Code's call on
  whether to surface as a `streaming.py` error
  or silently drop; recommendation is to log and
  drop for v1.x to avoid breaking the streaming
  loop on unfamiliar frame shapes.

**Public surface.** The parser exposes one
public function: `parse_frame(raw_frame: bytes |
str) -> InternalEnvelope`. Plus a `StreamReader`
class wrapping `betfairlightweight`'s socket
reader, exposing an iterator that yields parsed
internal envelopes for `streaming.py` to dispatch.
The exact class shape is Code's call; the
constraint is that `StreamReader` integrates
with W2's `StreamingClient.connect()` /
`disconnect()` lifecycle without modifying
`streaming.py`'s state machine.

**Tests.** Per the W2 test pattern: hand-rolled
fixtures in
`tests/fixtures/betfair/raw_stream_frames.py`
(name is Code's call) carrying real-shape Betfair
Streaming frames (taken from Betfair Streaming
API documentation samples). Test coverage:

- Each frame type round-trips correctly into
  the internal envelope.
- Malformed frames produce `op="unknown"` with
  raw payload preserved.
- Sport-agnostic frame coverage: a representative
  racing `mcm` and a representative sports `mcm`
  both produce `op="market_image"` correctly.
- Connection lifecycle: `connection` ack →
  `auth_ack` → first `mcm` produce the right
  envelope sequence.
- Empty and minimal frames don't crash the
  parser.

Coverage target: 12–18 tests for the parser
itself, plus 4–6 integration-shaped tests
where the parser feeds W2's existing
`StreamingClient` end-to-end (parsed envelope
arrives at `_handle_message`, cache populates,
freshness arithmetic resolves correctly).

**Substrate carry from W2.** The
`_handle_message` envelope shape documented at
the top of `streaming.py` and in
`tests/fixtures/betfair/stream_messages.py`
is the integration contract. Code reads both
to confirm the envelope shape before writing
the parser.

---
### §5.2 — Translating transport adapter

**What this is.** A translation layer that maps
the contract's path-style endpoint abstraction
into real Betfair Exchange REST JSON-RPC method
calls, sitting between W2's surface modules and
the underlying transport callable. Lives in
`_connection.py` or alongside it (Code's call on
exact module placement; recommendation is to
keep it in `_connection.py` if footprint is
small, or split into `_connection_translation.py`
if it gets large enough to warrant separation).

**Why this exists.** W2's contract uses path-style
endpoints (`/v1/market/{market_id}/prices`,
`/v1/orders/place`, etc.) as a clean abstraction
for surface design. Real Betfair Exchange REST
uses JSON-RPC over
`api.betfair.com/exchange/betting/json-rpc/v1`
with method names (`listMarketBook`, `placeOrders`,
etc.) and a single endpoint per service. The
adapter translates between the two so:

- Surface modules and tests register against the
  contract's clean path abstraction.
- Real-API integration in v3 build proper
  deployment flips a config flag; the adapter
  does the JSON-RPC translation behind the
  curtain.
- The Betfair-shape complexity sits in one place
  where it can be tested in isolation.

**Substrate carry from W2.** F4 Option A locked
Session 85. The path-style abstraction stays
clean; translation lives in one shim.

**Surface coverage.** All 8 surfaces — 5 reads
plus 3 writes:

- §9.1 live-pricing reads
  (`/v1/market/{id}/prices`,
  `/v1/market/{id}/runner/{sel}/best`) →
  `listMarketBook` with the appropriate
  `priceProjection` parameters.
- §9.2 settlement reads
  (`/v1/market/{id}/settlement`) →
  `listMarketBook` with `MARKET_STATE` /
  settled-runner data, or `listClearedOrders` /
  `listMarketCatalogue` as appropriate.
- §9.3 sports-line query
  (`/v1/event/{id}/markets`) →
  `listMarketCatalogue` with `eventIds` filter
  and `marketTypeCodes` filter.
- §9.4 scheduled-time reads
  (`/v1/market/{id}/scheduled-time`) →
  `listMarketBook` or `listMarketCatalogue`
  surface that exposes `marketTime`.
- §9.5 identifier-resolution check
  (`/v1/market/{id}/identity`) →
  `listMarketCatalogue` with selection-level
  data.
- §11.1 placement
  (`POST /v1/orders/place`) → `placeOrders`.
- §11.2 cancellation
  (`POST /v1/orders/cancel`) →
  `cancelOrders`.
- §11.3 replacement
  (`POST /v1/orders/replace`) →
  `replaceOrders`.

The exact JSON-RPC method names and parameter
shapes are Code's call to verify against
Betfair Exchange REST documentation (reach for
`external_api_resources.md` if needed). Some
of the contract's path-shaped endpoints map to
the same JSON-RPC method with different
parameters (e.g. several reads collapse onto
`listMarketBook`); the adapter handles that
mapping internally.

**Public surface.** A configuration flag (e.g.
`use_translating_transport: bool` on
`BetfairRestClient` constructor, or a separate
`BetfairJsonRpcTransport` subclass — Code's
call) selects between path-style direct
transport (W2's existing behaviour, used in
W3's tests) and translating transport (used in
v3 build proper real-API deployment).

When the translating transport is active, calls
land at a single Betfair JSON-RPC endpoint
with the appropriate method name and params
shape; responses are translated back into the
shapes the surface modules expect. When
inactive (default for v1.x tests), calls route
through W2's existing path-shaped transport
unchanged.

**Tests.** Two test surfaces:

- **Translation correctness.** For each of the
  8 surfaces, one test asserts that a call
  through the translating transport produces
  the expected JSON-RPC method name and params
  shape, and that the JSON-RPC response is
  mapped back into the contract's expected
  return shape. Hand-rolled fixtures of real-
  shape Betfair JSON-RPC responses (taken from
  Betfair documentation samples) drive the
  reverse-mapping verification.
- **Path-style transport unchanged.** All W2
  surface tests (already 50+ tests) continue to
  pass against the default path-style transport.
  The adapter does not change W2's existing
  behaviour when inactive.

Coverage target: 8–12 tests for translation
correctness. The full W2 test suite (101 W2 +
51 W1 + 6 W0 = 158 tests) continues to pass
unchanged.

**Cadence-parameter constants.** W2's two
`_connection.py` constants (`max calls per
window`, `window length`) stay placeholder per
F6 — Fix 4 calibration target, no proactive
enforcement in this brief. The adapter does
not touch these.

---
### §5.3 — F5 contract revision (strategy_tag)

**What this is.** A small backward-compatible
revision to the locked Betfair client contract,
adding `strategy_tag: Optional[str] = None` to
the §12.1 audit-log entry shape, plus
matching pass-through parameters on the three
write surfaces (`place_bet`, `cancel_bet`,
`replace_bet`).

**Why this exists.** Surfaced as W2 finding F5
(Session 85 triage). The contract's existing
`customer_strategy_ref` parameter on `place_bet`
is Betfair-side payload (forwarded to Betfair
in the placement request body) and is not
suitable for v3-side analytics joins. The
`strategy_tag` field is v3's analytics-join
key — it lands on the audit entry and enables
clean Strategy 1/2/3/4 cycle-grouping at audit
time without touching Betfair-side fields.

**Why this matters operationally.** Strategy 1
(Safety Net) is ~95% of current profit and is
heavily cycle-shaped — original bet, refund-as-
free-bet trigger, free bet outcome, all
analysed as one cycle (per Cat 4 single-cycle
analysis discipline). Strategy 2 (Price Booster)
has cycle-shaped sub-shapes (bonus-winnings).
Strategy 3 (SGM Correlated Friction) is
cycle-shaped by design. Strategy 4 (Synthetic
Each-Way) is single-leg.

Tagging audit entries with `strategy_tag` at
write time means downstream analytics can
group by strategy without parsing
`customer_order_ref` or joining against
external strategy-attribution tables. Cleanest
join key for cycle-grouping at the audit layer.

**Population semantics — Path A (locked).**
`strategy_tag` is a free-form `Optional[str]`.
The contract does not lock the tag values; v3's
bet-entry layer is responsible for choosing and
validating tag conventions (e.g. `"safety_net"`,
`"price_booster"`, `"sgm_correlated"`,
`"synthetic_each_way"`, or a different naming
scheme as the strategy taxonomy evolves).

Trade-off acknowledged: a typo in a strategy
tag silently lands on the audit entry.
Mitigation is the bet-entry layer's
responsibility, not the contract's. The
loose-string shape future-proofs against
strategy-taxonomy churn (sub-strategies,
variants, renaming) without contract revisions.

**Distinct from `customer_strategy_ref`.**
Worth saying explicitly because the names are
similar:

- `customer_strategy_ref` — Betfair-side
  payload, forwarded to Betfair in the
  placement request body. Betfair stores it
  against the order on Betfair's side. Useful
  for cross-checking Betfair's own reporting,
  not for v3-side analytics joins. Stays as-is
  in §11.1 placement parameters.
- `strategy_tag` — v3-side audit-log field.
  Never sent to Betfair. Used only for
  v3-internal analytics joins. New in this
  revision.

Both fields can carry the same string value if
the operator wants — they're independent.

**Contract changes.** Three surgical edits to
`betfair_client_contract.md`:

1. **§11.1 placement signature.** Add
   `strategy_tag: Optional[str] = None` to the
   `place_bet` parameter list. Document
   alongside `customer_strategy_ref` with the
   distinction made explicit.
2. **§11.2 cancellation signature.** Add
   `strategy_tag: Optional[str] = None` to the
   `cancel_bet` parameter list. Same shape as
   §11.1.
3. **§11.3 replacement signature.** Add
   `strategy_tag: Optional[str] = None` to the
   `replace_bet` parameter list. Same shape as
   §11.1.
4. **§12.1 audit-log entry shape.** Add
   `strategy_tag: Optional[str] = None` to the
   `AuditLogEntry` field list. Document the
   distinction from `customer_strategy_ref`
   (Betfair-payload vs v3-side analytics
   join key).
5. **§14 versioning footer.** Bump the contract
   version note to v1.1 with a one-line entry
   recording the F5 backward-compatible
   addition. Existing v1.0 callers continue to
   work unchanged (the field is optional with
   default `None`).

**Code changes.** Mechanical extensions of
W2's existing code:

- `_audit.AuditLogEntry` Pydantic model gets
  `strategy_tag: Optional[str] = None` added.
- `placement.py` `place_bet` signature gets
  `strategy_tag: Optional[str] = None`
  parameter; the value is forwarded to the
  audit entry constructor. The Betfair request
  body is unchanged (`strategy_tag` is never
  sent to Betfair).
- `cancellation.py` `cancel_bet` and
  `replacement.py` `replace_bet` get the same
  parameter and audit-entry forwarding.

**Tests.** One test per write surface (3 total)
asserting that a `strategy_tag` value passes
through to the audit entry correctly, and one
test asserting that a `None` value (the default)
also lands correctly. 4 tests total.

W2's existing 101 tests continue to pass
unchanged — the addition is backward-compatible
because the parameter has a default.

---
### §5.4 — Consumer-side reading paths

**What this is.** A thin convenience layer on
top of W2's existing read surfaces, exposing
ergonomic helper functions that future v3
callers (W4 bet entry, W7 burst review, the
eventual UI service layer) will consume.

Lives inside `clients/betfair_client/v1/` —
either as a new module
`clients/betfair_client/v1/consumer.py` (Code's
call) or as additions to the existing
read-surface modules. Recommendation is a new
module so the convenience layer is visibly
distinct from the contract surface (W2's read
modules implement the contract; the consumer
module wraps them for ergonomics).

**Why this exists.** W2's read surfaces are
contract-shaped — they accept `rest_client` and
optional `streaming_client` parameters
explicitly, return `ReadEnvelope[T]`
discriminated unions, and require the caller
to handle each envelope status (`fresh` /
`stale` / `unavailable`) per the contract's
§4 envelope contract.

Future callers (W4 bet entry, W7 burst review)
will repeat the same client-passing and
envelope-handling boilerplate at every call
site if there's no convenience layer. The
consumer paths centralise the boilerplate so
callers can write `get_live_market_prices(
market_id)` and get back a typed result with
the right cache routing applied.

This is genuinely small in scope — most of
W3's value sits in the parser (§5.1) and the
adapter (§5.2). The consumer paths are the
smaller of the four deliverables by design.

**Public surface.** A small set of helper
functions, each wrapping one W2 read surface:

- `get_live_market_prices(market_id, client)
  -> ReadEnvelope[MarketPrices]` — wraps
  `live_pricing.market_prices()`, always
  passes `streaming_client` if available on
  the `client` object.
- `get_runner_best_prices(market_id,
  selection_id, client) ->
  ReadEnvelope[RunnerBestPrices]` — wraps
  `live_pricing.runner_best_prices()`.
- `get_market_settlement(market_id, client)
  -> ReadEnvelope[MarketSettlement]` — wraps
  `settlement.market_settlement()`.
- `get_sports_market_variants(event_id,
  market_type, client) ->
  ReadEnvelope[list[SportsMarketVariant]]` —
  wraps `sports_lines.sports_market_variants()`.
- `get_market_scheduled_time(market_id, client)
  -> ReadEnvelope[MarketScheduledTime]` —
  wraps `scheduled_time.market_scheduled_time()`.
- `check_identity(market_id, selection_id,
  client) -> ReadEnvelope[IdentityCheck]` —
  wraps `identity.identity_check()`.

The `client` parameter is a new container
shape — `BetfairClient` (Code's call on exact
class name and shape) — that bundles the
existing `BetfairRestClient` and optional
`StreamingClient` references in one place. The
container is constructed once at v3 startup
and passed to consumer-path calls.

**Container shape.** `BetfairClient` is a small
dataclass or Pydantic model carrying:

- `rest_client: BetfairRestClient` (required).
- `streaming_client: StreamingClient | None`
  (optional; `None` means cache-vs-REST routing
  always falls through to REST).

No methods on the container itself — it's a
named bundle. Consumer paths take the
container and unpack the references they need.

**What the consumer paths do NOT do.**

- They do not batch reads across multiple
  markets. That's W7 burst-review territory.
- They do not attempt automatic retry on
  `unavailable` envelopes. The caller decides
  retry semantics; the convenience layer is
  pass-through.
- They do not rewrite envelope shapes. The
  caller still receives the discriminated
  union and handles each status. The
  convenience is in the call-site
  boilerplate, not in the response shape.
- They do not handle write surfaces. Write
  callers continue to use `placement.py`,
  `cancellation.py`, `replacement.py` directly
  — write surfaces have meaningfully different
  call shapes (audit_sink, operator_identity,
  customer_order_ref) that don't benefit from
  a thin wrapper.

**Tests.** One test per consumer path (6 total)
asserting that the wrapper correctly routes the
call through to the underlying read surface
with the right client references. Plus 2–4
tests covering the `BetfairClient` container
shape (construction with and without streaming,
unpacking, etc.).

Coverage target: 8–10 tests for the consumer
layer.

---

### §5 close — total deliverable footprint

- Parser (§5.1): 1 new module + 1 fixtures
  module + 16–24 tests.
- Adapter (§5.2): 1 module addition (or new
  module) + 8–12 tests.
- F5 contract revision (§5.3): contract edits
  to 4 sections + version footer + minor edits
  to `_audit.py` + 3 placement modules + 4
  tests.
- Consumer paths (§5.4): 1 new module + 1
  small container shape + 8–10 tests.

**Total new tests:** approximately 36–50 (plus
158 existing W2 + W1 + W0 tests continue to
pass unchanged).

**Single commit at session end** per W2 pattern.

---
## §6 — Sequencing within session

Code executes the four deliverables substrate-
first per Order A (locked Session 86):

**Step 1 — Pre-flight.**
- Anchor session start with Adelaide local
  time per DR-021.
- Read the contract, W2 implementation report,
  W2 brief, standing instructions, decisions,
  and the W2 codebase per §3.
- Verify contract version header matches
  expected (v1.0; W3 will edit it to v1.1 in
  step 4).
- Run `uv run pytest` baseline against current
  W2 commit `254fcfc`. Expect 158 passing
  (101 W2 + 51 W1 + 6 W0). If the baseline
  doesn't match, surface as §11 finding before
  proceeding.

**Step 2 — Streaming wire-format parser
(§5.1).**
- Read the `_handle_message` envelope shape
  from W2's `streaming.py` and
  `tests/fixtures/betfair/stream_messages.py`.
- Read `betfairlightweight` library docs to
  confirm the library's frame-reader output
  shapes.
- Build the parser module producing the
  internal envelope from real Betfair
  Streaming protocol frames.
- Build the fixtures module with hand-rolled
  real-shape Betfair Streaming frames (`mcm`,
  `ocm`, status, heartbeat, connection ack,
  auth ack, plus malformed and unknown).
- Build the parser tests (12–18 tests).
- Build the integration tests where the parser
  feeds W2's existing `StreamingClient` end-
  to-end (4–6 tests).
- Run `uv run pytest` — expect 158 + 16–24
  passing.

**Step 3 — Translating transport adapter
(§5.2).**
- Map each of the 8 contract path-shaped
  endpoints to its Betfair JSON-RPC method
  equivalent (verify against
  `external_api_resources.md` and Betfair
  Exchange REST docs as needed).
- Build the adapter module (or extend
  `_connection.py`) with translation logic.
- Add a configuration flag selecting between
  path-style direct transport (default,
  W2's existing behaviour) and translating
  transport (real-API mode).
- Build hand-rolled fixtures of real-shape
  Betfair JSON-RPC responses for each surface.
- Build translation correctness tests (8–12
  tests).
- Run `uv run pytest` — expect previous count
  + 8–12 passing. The full W2 test suite
  continues to pass against the default
  path-style transport.

**Step 4 — F5 contract revision (§5.3).**
- Apply the surgical edits to
  `betfair_client_contract.md`: §11.1, §11.2,
  §11.3 placement signatures get `strategy_tag`
  parameter; §12.1 audit-log entry gets
  `strategy_tag` field; §14 versioning footer
  gets v1.1 entry.
- Update `_audit.AuditLogEntry` to include
  `strategy_tag`.
- Update `placement.py`, `cancellation.py`,
  `replacement.py` to accept and forward
  `strategy_tag` to the audit entry.
- Build the 4 strategy_tag tests.
- Run `uv run pytest` — expect previous count
  + 4 passing. Existing W2 placement tests
  continue to pass (the addition is
  backward-compatible).

**Step 5 — Consumer-side reading paths
(§5.4).**
- Build the `BetfairClient` container shape.
- Build the consumer module wrapping each W2
  read surface.
- Build the consumer-path tests (8–10 tests).
- Run `uv run pytest` — expect final count
  158 + 36–50 = 194–208 passing.

**Step 6 — Final verification.**
- Run `uv run mypy clients/betfair_client/v1/`
  — expect clean (no new type errors
  introduced).
- Run `uv run ruff check
  clients/betfair_client/v1/` — expect clean.
- Run `uv run pytest` final — expect all tests
  passing.
- Anchor session close with Adelaide local
  time per DR-021.

**Step 7 — Single commit.**
- All four deliverables (parser, adapter, F5
  contract revision and code, consumer paths)
  ship in one commit at session end. Per W2
  pattern. Commit message follows W2's shape.

**Strain-point flagging.** The most likely
budget pressure point is the parser (§5.1) —
the envelope mapping has 7 frame types plus
malformed/unknown, and the integration tests
exercise the full state machine end-to-end.
If the parser hits the strain point and Code
has used >70% of session budget by step 2 end,
fall back per §6 of this brief: ship parser
clean as the partial-completion fallback,
defer adapter / F5 / consumer paths to a
follow-up brief. Code surfaces the fallback
in the report explicitly.

Other deliverables are lower-risk: adapter is
mechanical translation; F5 is small surgical
edits; consumer paths are thin wrappers.

---
## §7 — Empirical verification

Code verifies each deliverable lands cleanly
against the criteria below. The full checklist
is the basis of the §11 verification block in
the implementation report.

### §7.1 — Parser (§5.1) verification

1. Each Betfair Streaming protocol frame type
   round-trips correctly into the internal
   envelope: `mcm` → `op="market_image"` or
   `op="market_delta"`; `ocm` →
   `op="order_unmatched"` or
   `op="order_matched"`; `status` →
   `op="status"`; `heartbeat` →
   `op="heartbeat"`; `connection` ack →
   `op="connection_ack"`; `auth` ack →
   `op="auth_ack"`.
2. Malformed frames produce `op="unknown"`
   with the raw payload preserved in the
   envelope; the parser does not crash.
3. Sport-agnostic frame coverage: a
   representative racing `mcm` and a
   representative sports `mcm` both produce
   `op="market_image"` correctly.
4. Connection lifecycle: `connection` ack →
   `auth_ack` → first `mcm` produce the right
   envelope sequence in order.
5. End-to-end integration: parser feeds W2's
   `StreamingClient`; cache populates
   correctly; freshness arithmetic resolves
   against pinned `_clock.now_utc()` reference.
6. Empty / minimal / boundary-condition
   frames don't crash the parser.
7. `betfairlightweight` library is the
   foundation; no hand-rolled socket reading
   in W3.

### §7.2 — Translating transport adapter
(§5.2) verification

1. Each of the 8 contract path-shaped
   endpoints maps correctly to its Betfair
   JSON-RPC method equivalent when the
   translating transport is active.
2. JSON-RPC responses are translated back
   into the contract's expected return shapes
   correctly for each surface.
3. The translating transport activates via a
   configuration flag; when inactive (default
   for v1.x tests), calls route through W2's
   existing path-shaped transport unchanged.
4. All W2 surface tests (the 50+ existing
   read- and write-surface tests) continue to
   pass against the default path-style
   transport.
5. Translation correctness tests cover all 8
   surfaces — 5 reads + 3 writes.
6. Cadence-parameter constants in
   `_connection.py` (max calls per window,
   window length) stay placeholder; the
   adapter does not introduce proactive rate-
   limit enforcement.

### §7.3 — F5 contract revision (§5.3)
verification

1. Contract `betfair_client_contract.md` has
   `strategy_tag: Optional[str] = None` added
   to §11.1 / §11.2 / §11.3 placement
   signatures.
2. Contract §12.1 audit-log entry shape
   includes `strategy_tag: Optional[str] =
   None` with documentation of distinction
   from `customer_strategy_ref`.
3. Contract §14 versioning footer carries a
   v1.1 entry recording the F5 backward-
   compatible addition.
4. `_audit.AuditLogEntry` Pydantic model
   includes `strategy_tag` field with
   `Optional[str] = None` default.
5. `place_bet`, `cancel_bet`, `replace_bet`
   accept `strategy_tag` parameter, default
   `None`, forward to audit entry.
6. `strategy_tag` is never sent to Betfair —
   the placement request body does not include
   it. Verified by inspection of the request
   body shape in placement tests.
7. Existing W2 placement tests continue to
   pass unchanged (the addition is backward-
   compatible because the parameter has a
   default).

### §7.4 — Consumer-side reading paths
(§5.4) verification

1. Each of the 6 consumer helper functions
   correctly routes the call through to the
   underlying W2 read surface with the right
   client references.
2. The `BetfairClient` container shape
   constructs correctly with required
   `rest_client` and optional
   `streaming_client`.
3. Consumer paths return `ReadEnvelope[T]`
   discriminated unions unchanged from the
   underlying surfaces — no rewriting.
4. Consumer paths do not batch reads, do not
   retry on `unavailable`, do not handle write
   surfaces.
5. Consumer paths live in `consumer.py` (or
   equivalent named module) inside
   `clients/betfair_client/v1/`.

### §7.5 — Cross-cutting verification

1. `uv run pytest` final count: 158 (existing
   W2+W1+W0) + 36–50 (W3) = 194–208 tests
   passing. No skipped tests.
2. `uv run mypy clients/betfair_client/v1/`
   clean.
3. `uv run ruff check
   clients/betfair_client/v1/` clean.
4. Single commit at session end carrying all
   deliverables.
5. No real Betfair API calls made during the
   session.
6. No new dependencies added beyond the
   existing W0 + W1 + W2 set.
7. No modifications outside named scope (no
   `vps_client` work, no operational store
   work, no UI work, no service-layer
   modules).

### §7.6 — Completion criteria

**Floor (minimum to consider session
complete):** parser (§5.1) ships clean with
all §7.1 criteria met. The integration tests
where the parser feeds W2's `StreamingClient`
are the load-bearing acceptance signal.

**Full scope:** all four deliverables (parser
+ adapter + F5 revision + consumer paths)
ship in one commit, all §7.1–§7.5 criteria
met.

**Partial-completion fallback.** If Code hits
budget pressure after the parser lands clean
(see §6 strain-point flagging), Code may ship
the parser as the floor and defer adapter /
F5 / consumer paths to a follow-up brief.
Surfaced explicitly in the implementation
report as "deferred to W3.1" or equivalent.

The fallback is intended to reduce session
pressure rather than to fire. W2's pattern
(have a fallback, don't actually need it)
worked cleanly — the fallback's existence
made the session calmer without forcing it
to fire.

---
## §8 — Output spec

Code produces one implementation report at
session end:

`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w3_live_pricing/w3_implementation_report.md`

Report shape mirrors W2's report (§§1–13):

1. **§1 Anchor (session start)** — Adelaide
   local time per DR-021.
2. **§2 Pre-flight** — baseline test count
   verified, contract version verified, W2
   substrate reads complete.
3. **§3 Parser module summary** — module
   shape, public surface, frame-type coverage,
   `betfairlightweight` integration approach.
4. **§4 Translating transport adapter
   summary** — module shape, JSON-RPC
   mapping table per surface, configuration
   flag mechanics.
5. **§5 F5 contract revision summary** —
   contract edits applied, code edits applied,
   backward-compatibility verified.
6. **§6 Consumer-side reading paths
   summary** — `BetfairClient` container,
   helper functions, scope boundaries.
7. **§7 Cross-cutting modules summary** —
   any shared substrate (e.g. shared fixtures,
   shared types) introduced.
8. **§8 Fixture summary** — new fixtures
   modules, frame samples, JSON-RPC response
   samples.
9. **§9 Tests summary** — count per
   deliverable, total count, mypy/ruff status.
10. **§10 Single commit summary** — commit
    SHA, file list, summary message.
11. **§11 Findings (F1–FN)** — anything Code
    surfaces for operator-Claude triage.
    Findings classified as cosmetic / scope-
    question / blocking. Each finding follows
    W2 finding shape: step where it surfaced /
    expected / actual / output / Code's read.
12. **§12 Self-assessment** — did Code stay
    within named anchors? Out-of-scope items
    touched? Session fit a single bounded
    run? Strain-point hit? Completion-floor
    or full-scope? Anything the next
    operator-Claude session needs to know
    that the report doesn't otherwise capture.
13. **§13 Anchor (session close)** — Adelaide
    local time per DR-021.

Report is plain markdown, hard-wrapped at
~70 chars per line for chat-width review.

---

## §9 — Hard limits

What this brief explicitly excludes — Code
does not touch any of these:

- **UI substrate.** No React + TypeScript +
  Vite work. The frontend that renders live
  prices is a separate workstream that lands
  after W3.
- **Service layer.** No new modules outside
  `clients/betfair_client/v1/` (other than
  the contract revision). v3's eventual
  service layer wrapping library calls in
  v3-shaped operations is a future
  workstream.
- **Real Betfair API integration.** No real
  socket opening, no real REST calls, no
  real auth flow. W3 stays mocked-only per
  W2's pattern. Real-API integration is v3
  build proper deployment territory.
- **Operational store integration.** No
  reads from or writes to v3's operational
  store. W6 owns operational store schema.
- **Proactive rate-limit enforcement.** W2
  finding F6 — Fix 4 calibration target.
  `_connection.RateLimitBudget` placeholder
  stays as-is.
- **Audit-log durable substrate selection.**
  W2 §12 self-assessment item 3 — deployment
  configuration, single sink-class swap at
  startup. Not a contract or library shape
  decision.
- **F3 mirror enums refactor.** Locked
  Session 85: kept duplicated for v1.x.
  Refactor only if duplication surfaces
  elsewhere.
- **`vps_client` work.** W1 territory.
- **Cross-database queries.** No reads from
  capture.db, no reads from v3 operational
  store. The library is sealed at the
  Betfair-facing boundary.
- **New dependencies.** Existing W0 + W1 +
  W2 dependency set is the budget. If a new
  dependency is genuinely needed, surface as
  §11 finding rather than installing.
- **Multi-session work.** Single bounded
  Code session. Partial-completion fallback
  per §7.6 if budget runs out — defer to
  follow-up brief, do not extend the
  session.
- **Architecture changes.** Contract
  revision in §5.3 is the only governance-
  artefact edit. No DR additions, no
  `architecture.md` edits, no
  `decisions.md` edits.

---

## §10 — What happens after Code's session

After Code commits and the report lands, the
next operator-Claude session triages.

**Triage shape (mirrors W2 triage in Session
85):**

1. Read the implementation report end-to-end.
2. Classify each §11 finding (cosmetic /
   scope-question / blocking). Route per
   classification — cosmetic accepted as-is,
   scope-questions routed to operator-relevant
   call or v3-build-proper substrate decision,
   blocking surfaced for fix.
3. Verify §11 verification criteria all PASS.
4. Verify foundation clean for downstream
   workstreams.
5. Update `current_state.md` to reflect W3
   close and W4 / W7 unblock.
6. Update `v3_build_picture.md` — W3 →
   `done` (carries one session); W4 + W7
   → unblocked.
7. Lock the F5 contract revision as v1.1 of
   the Betfair client contract — confirm the
   contract version footer reads correctly,
   confirm the contract documentation
   relocation flag (post-DR-029-close
   contract documentation moves to v3's
   `contracts/` folder per DR-030 layout)
   carries forward unchanged.

**What unblocks after W3:**

- **W4 (bet entry + write surfaces)** — the
  live-pricing read paths W3 ships are
  consumed by W4's placement-time sanity
  checks. W4 brief drafting can open
  immediately.
- **W7 (Burst Review workflow)** — the
  consumer-side reading paths and the
  underlying streaming cache are W7's data
  substrate. W7 brief drafting opens after
  W4 (W7's UI shape depends partly on what
  W4's bet-entry surface looks like).

**Substrate carry-forwards from W3 triage to
later workstreams:**

- The `BetfairClient` container shape lands
  in W3 — W4 and W7 both consume it. The
  container is the canonical "give me a
  Betfair handle" shape for v3.
- The translating transport's configuration
  flag is the integration point for real-API
  deployment — flagged for v3 build proper
  deployment work.
- F5 strategy_tag pass-through is wired
  through write surfaces but not yet
  consumed by anything. W4 bet-entry layer
  will be the first caller to populate it
  meaningfully — flagged for W4 brief
  drafting.

**Partial-completion fallback path.** If W3
ships parser-only per §7.6 floor, the
follow-up brief (W3.1 or equivalent)
commissions adapter + F5 + consumer paths in
a smaller bounded session. W4 and W7 stay
`blocked-on-W3` until the follow-up lands.

---

## §11 — Cross-references

**Contract sections this brief touches:**
- §10 (Streaming surface) — parser produces
  envelope `streaming.py` consumes.
- §9 (read surfaces) — consumer paths wrap
  these.
- §11.1 / §11.2 / §11.3 (write surfaces) —
  F5 strategy_tag parameter added.
- §12.1 (audit-log entry shape) — F5
  strategy_tag field added.
- §14 (versioning mechanics) — version
  footer bumped to v1.1.

**Prior briefs and reports:**
- `dr029/w0_repo_init/w0_brief.md` and
  `w0_implementation_report.md` — repo
  skeleton and import-linter contracts.
- `dr029/w1_vps_client/w1_brief.md` and
  `w1_implementation_report.md` — sibling
  client pattern, F3 PEP-695 substrate, F6
  `_clock` test-patchability.
- `dr029/w2_betfair_client/w2_brief.md` and
  `w2_implementation_report.md` — direct
  parent. F2 / F4 / F5 / F6 substrate.

**Governing decision records:**
- **DR-027** (the two-database architecture
  decision: BetHub owns operational state,
  capture.db owns analytical/source data).
- **DR-028** (the cross-database integration
  boundary discipline decision: no caching,
  no denormalisation, no second integration
  point).
- **DR-019** (derived state on read) — load-
  bearing for consumer paths (no analytical
  reads in `betfair_client`; consumer paths
  respect the same exclusion).
- **DR-021** (timestamp anchoring, Adelaide
  local time) — applies to session start /
  close anchors and to envelope `as_of`
  semantics.
- **DR-030** (v3 repo layout / module-
  boundary discipline) — load-bearing for
  parser and adapter module placement.
- **DR-031** (v3 tech stack) —
  `betfairlightweight` named as Streaming
  wire-format library; Pydantic v2 for
  shapes; Python 3.12+ for PEP-695 type
  aliases.

**External resources:**
- `external_api_resources.md` (rebuild root)
  — pointer set for Betfair Exchange REST
  and Streaming API documentation.
- `betfairlightweight` library documentation
  — Python package, foundation for the
  parser.

**Standing instructions and governance:**
- `standing_instructions.md` — full read at
  session start per Cat 2.
- `decisions.md` — DR list.
- `governance.md` — DR-029 close-out section
  (Session 78), three pieces of named debt,
  five deferred capabilities.

---

**End of brief.**
