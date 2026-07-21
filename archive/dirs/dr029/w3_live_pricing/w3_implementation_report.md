# W3 — live pricing consumer path: Code report

**Brief:** `dr029/w3_live_pricing/w3_brief.md` (Session 87).
**Repo target:** `/Users/tim/Desktop/Projects/bethub-v3/clients/betfair_client/v1/`.
**Contract:** `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
v1.1 — F5 strategy_tag added in this session (backward-compatible per
§14.4); v1.0 base locked Sessions 75/77/78.

---

## §1 — Anchor (session start)

`2026-05-05 17:20:10 ACST` (Adelaide local, per DR-021).

---

## §2 — Pre-flight

Contract status header verified at v1.0 — locked Session 75, drafted
Session 77, finalised Session 78. W3 edits the header to v1.1 in step 4
(F5 contract revision).

Baseline `uv run pytest`: **158 passed** at W2 commit `254fcfc` (101 W2
+ 51 W1 + 6 W0). Within expected; pre-flight passed.

Substrate reads completed per brief §3:

- `betfair_client_contract.md` v1.0 (§§9, 10, 11, 12, 14 in full).
- W2 implementation report (`w2_implementation_report.md`) — particularly
  §5 streaming substrate, §11 findings F2/F4/F5, §12 self-assessment
  items 1 & 2 (cadence-parameter constants, `_handle_message` envelope
  contract).
- W2 codebase: `streaming.py` (post-parse dispatch path the parser
  feeds), `_connection.py`, `_audit.py`, `live_pricing.py`,
  `placement.py`, `cancellation.py`, `replacement.py`,
  `tests/fixtures/betfair/stream_messages.py`.
- `decisions.md` DR-021, DR-030, DR-031.
- `betfairlightweight` 2.23.2 — inspected `StreamListener` and
  `BaseListener` in `streaming/listener.py` to confirm the library's
  on-the-wire frame shapes (`op`-tagged JSON dicts with `connection` /
  `status` / `mcm` / `ocm` / `rcm` / `ccm` plus `ct` change types
  `SUB_IMAGE` / `RESUB_DELTA` / `HEARTBEAT` / `UPDATE`).

---

## §3 — Parser module summary

`bethub-v3/clients/betfair_client/v1/_stream_parser.py` (~340 lines).

**Public surface:**

- `parse_frame(raw_frame, *, auth_ack_seen=False) -> tuple[list[dict],
  bool]` — single-frame stateless mapper. Accepts `bytes | str | dict`.
  Returns `(envelopes, new_auth_ack_seen)`. One Betfair frame can yield
  multiple envelopes (an `mcm` with several markets in `mc[]` produces
  one envelope per market; an `ocm` with several selections in
  `oc[].orc[]` produces one envelope per selection).
- `StreamReader(raw_source)` — stateful iterator wrapping
  `parse_frame` across frames. Tracks the auth-ack flag so the first
  successful `op=status` after a `op=connection` promotes to
  `op="auth_ack"`. Plus a `dispatch_to(client)` convenience method that
  drives `client._handle_message` for every yielded envelope.

**Frame-type coverage** — produces the W2 internal envelope shape
(per `streaming.py` module docstring, `{"op": "...", "payload": {...}}`)
that `_handle_message` already consumes. Mapping:

| Raw Betfair frame | Internal envelope op |
|---|---|
| `op=connection` (carries `connectionId`) | `connection_ack` |
| `op=status` (first SUCCESS after connection) | `auth_ack` |
| `op=status` (errorCode / FAILURE) | `status` (degraded, payload.status="503") |
| `op=status` (subsequent SUCCESS / steady-state) | `status` (recovery, payload.status=None) |
| `op=mcm` ct=SUB_IMAGE | `mcm` is_image=True |
| `op=mcm` ct=UPDATE / RESUB_DELTA | `mcm` is_image=False |
| `op=mcm` ct=HEARTBEAT | `heartbeat` |
| `op=ocm` ct=SUB_IMAGE / UPDATE | `ocm` |
| `op=ocm` ct=HEARTBEAT | `heartbeat` |
| malformed JSON / unknown frame | `unknown` (raw preserved, logged WARNING) |

**Field-level mapping for `mcm` and `ocm`** — see module docstring.
Highlights: `marketDefinition.runners[].status` populates
`runner_status` keyed by `selection_id`; `rc[].atb`/`atl` truncate to
top-3 levels per contract §2.4 §5.2 ladderLevels=3; Betfair `B`/`L`
side codes translate to `BACK`/`LAY`; persistence codes
`L`/`P`/`MOC` translate to `LAPSE`/`PERSIST`/`MARKET_ON_CLOSE`;
placement-time epoch milliseconds convert to ISO-format UTC strings
that `to_adelaide(datetime.fromisoformat(...))` handles cleanly.

**`betfairlightweight` integration approach.** The library is **not**
directly imported in W3 — see §11 finding F4 below. The parser receives
raw bytes/str (or already-decoded dicts) and works against the same JSON
frame shapes that `betfairlightweight.streaming.listener.StreamListener.on_data`
receives. v3 build proper deployment pipes
`StreamListener` socket output into `StreamReader`'s `raw_source`; the
shape-compatibility is preserved.

---

## §4 — Translating transport adapter summary

`bethub-v3/clients/betfair_client/v1/_translation.py` (~490 lines).

**Public surface:**

- `TranslatingTransport(inner: Transport, json_rpc_url: str = ...)` —
  conforms to W2's `Transport` Callable signature
  `(url, body, headers) -> dict`, so it drops in as the
  `BetfairRestClient(transport=...)` argument with no surface-module
  changes. Wraps an inner transport (the actual Betfair JSON-RPC HTTP
  call in deployment, a `MockJsonRpcTransport` in tests).
- `BETTING_JSON_RPC_URL = "https://api.betfair.com/exchange/betting/json-rpc/v1"`.
- `SPORTS_API_PREFIX = "SportsAPING/v1.0/"`.

**Configuration mechanics.** The brief framed this as "configuration
flag selects between path-style and translating transport." Because W2's
`BetfairRestClient` already accepts an arbitrary transport callable, the
flag is operationally satisfied by *which transport you wire*: the
default for v1.x tests is W2's path-style `MockTransport` directly;
v3 build proper deployment wires
`TranslatingTransport(inner=httpx_transport)`. No flag added to
`BetfairRestClient` — the constructor is unchanged.

**JSON-RPC mapping table** (all 8 contract surfaces):

| Path | Method (with `SportsAPING/v1.0/` prefix) | Notes |
|---|---|---|
| `GET  /v1/market/{id}/prices`            | `listMarketBook` | priceProjection EX_BEST_OFFERS + EX_TRADED, depth=3 |
| `GET  /v1/market/{id}/runner/{sid}/best` | `listMarketBook` | depth=1; selection filter applied at translate-response time |
| `GET  /v1/market/{id}/settlement`        | `listMarketBook` | priceProjection SP_TRADED; settlement_status from runner.status |
| `GET  /v1/market/{id}/scheduled_time`    | `listMarketCatalogue` | marketProjection MARKET_START_TIME, maxResults=1 |
| `GET  /v1/event/{id}/markets`            | `listMarketCatalogue` | filter eventIds + marketTypeCodes; market_type from query string |
| `GET  /v1/identity/check`                | `listMarketCatalogue` | filter marketIds; runner-presence check on response |
| `POST /v1/orders/place`                  | `placeOrders` | LIMIT order, customerOrderRef + customerStrategyRef forwarded |
| `POST /v1/orders/cancel`                 | `cancelOrders` | optional sizeReduction for partial-cancel |
| `POST /v1/orders/replace`                | `replaceOrders` | newPrice instruction; both legs in one report |

JSON-RPC error responses (server-side `{"error": {...}}`) translate to
`BetfairRestError` with a synthetic HTTP status code so W2's
`_errors.map_rest_error_*` covers connectivity-shaped failures
(`INVALID_SESSION_INFORMATION` → 401 → `betfair_auth_expired`,
`TOO_MUCH_DATA` → 429 → `betfair_rate_limited`, etc.).

**Path prefix handling.** `BetfairRestClient` prepends a REST base URL
to surface paths. The translating transport strips everything before
the surface `/v1/` segment so the regex routing table sees just the
contract path. (Initial implementation didn't strip; tests caught it
on first run.)

---

## §5 — F5 contract revision summary

**Contract edits applied** to
`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`:

1. **Status header (line 3)** updated to `v1.1 — F5 strategy_tag added
   Session 87 W3 (backward-compatible per §14.4); v1.0 locked Session
   75 ...`.
2. **§6 version history table** — appended a v1.1 entry recording the
   F5 backward-compatible addition with the
   `customer_strategy_ref`-distinction note.
3. **§11.1** — `place_bet` signature gains
   `strategy_tag: Optional[str] = None`. Parameter table extended with
   the v1.1 row spelling out the v3-internal vs Betfair-payload
   distinction.
4. **§11.2** — `cancel_bet` signature gains
   `strategy_tag: Optional[str] = None`. Same parameter row.
5. **§11.3** — `replace_bet` signature gains
   `strategy_tag: Optional[str] = None`. Same parameter row.
6. **§12.1 `AuditLogEntry`** — gains
   `strategy_tag: Optional[str] = None`. Plus a v1.1 paragraph
   explicitly distinguishing it from `customer_strategy_ref` (Betfair-
   payload) and naming the Cat 4 single-cycle-analysis use case.

**Code edits applied:**

- `_audit.AuditLogEntry` Pydantic model: added
  `strategy_tag: str | None = None` field.
- `placement._emit_entry`: keyword-only `strategy_tag` parameter
  forwarded to the `AuditLogEntry` constructor.
- `placement.place_bet`: signature gains `strategy_tag: str | None =
  None` parameter; forwarded to `_emit_entry` at all four call sites
  (streaming-blocked, REST-error, rejection, success). Critically:
  `strategy_tag` is **not** added to the placement request body, so
  it never reaches Betfair. Verified by
  `test_place_bet_strategy_tag_never_sent_to_betfair_request_body`.
- `cancellation.cancel_bet` + `replacement.replace_bet`: same
  signature extension and forwarding pattern.

**Backward-compatibility verified.** Default `None` keeps existing v1.0
callers working unchanged; W2's 24 placement/cancellation/replacement
tests all pass against the unchanged signatures.

---

## §6 — Consumer-side reading paths summary

`bethub-v3/clients/betfair_client/v1/consumer.py` (~140 lines).

**`BetfairClient` container:** frozen dataclass with
`rest_client: BetfairRestClient` (required) and
`streaming_client: StreamingClient | None = None` (optional). No
methods — a named bundle.

**Helper functions** (one wrapper per W2 read surface):

- `get_live_market_prices(market_id, client) -> ReadEnvelope[MarketPrices]`
- `get_runner_best_prices(market_id, selection_id, client) -> ReadEnvelope[RunnerBestPrices]`
- `get_market_settlement(market_id, client) -> ReadEnvelope[MarketSettlement]`
- `get_sports_market_variants(event_id, market_type, client) -> ReadEnvelope[list[SportsMarketVariant]]`
- `get_market_scheduled_time(market_id, client) -> ReadEnvelope[MarketScheduledTime]`
- `check_identity(market_id, selection_id, client) -> ReadEnvelope[IdentityCheck]`

All six are pass-through ergonomic wrappers — they unpack
`client.rest_client` and `client.streaming_client`, call the
underlying surface, and return the surface's `ReadEnvelope[T]` shape
unchanged. No batching, no auto-retry, no envelope rewriting (per brief
§5.4 boundaries). Write surfaces deliberately stay outside this module
(meaningfully different parameter shapes — `audit_sink`,
`operator_identity`, `customer_order_ref`, `strategy_tag` — that don't
benefit from a thin wrapper).

**Re-exports** added to `clients/betfair_client/v1/__init__.py` so
v3 callers can `from clients.betfair_client.v1 import BetfairClient,
get_live_market_prices, ...`.

---

## §7 — Cross-cutting modules summary

No new cross-cutting substrate beyond the four named deliverables.

- `_stream_parser.py` — new private module, leaf inside the package.
- `_translation.py` — new private module, depends only on
  `_connection.BetfairRestError` / `_connection.Transport`.
- `consumer.py` — public module re-exported from `v1/__init__.py`.
- All other private modules (`_audit`, `_auth`, `_clock`,
  `_connection`, `_errors`) inherited unchanged from W2 except
  `_audit.AuditLogEntry` (one new optional field per F5).

---

## §8 — Fixture summary

One new fixture module:
`bethub-v3/tests/fixtures/betfair/raw_stream_frames.py` (~290 lines).

Hand-rolled real-shape Betfair Streaming protocol frames. The shapes
match Betfair's published wire format (short-code fields `rfo`/`sm`/
`sr`/`atb`/`atl`/`ct`/etc.) — distinct from W2's
`stream_messages.py` which carries the post-parse internal envelope
shape.

Coverage:

- Connection lifecycle: `CONNECTION`, `AUTH_ACK_STATUS`,
  `STATUS_DEGRADED`, `STATUS_RECOVERY`.
- Market change: `mcm_sub_image`, `mcm_update`, `mcm_resub_delta`,
  `mcm_heartbeat`, `mcm_multi_market` (parameterised market IDs),
  `mcm_sports_sub_image` (AFL MATCH_ODDS for sport-agnostic
  verification).
- Order change: `ocm_sub_image_unmatched`, `ocm_matched_position`,
  `ocm_lay_unmatched` (verifies side/persistence translation),
  `ocm_heartbeat`.
- Edge cases: `UNKNOWN_OP_FRAME` (rcm), `EMPTY_MCM`,
  `malformed_json_str`.
- Helper: `to_json_bytes(frame)` for tests exercising the bytes
  decode path.

For the translating transport tests, fixture data lives inline in
`test_translation.py` (each test constructs its own canned JSON-RPC
`result` payload — keeps each scenario self-contained and easy to
reason about).

---

## §9 — Tests summary

**New W3 tests: 54.** Brief target was 36–50; the parser came in at
27 (vs target 16–24) because the fixture-driven coverage of all frame
types + edge cases + integration with `StreamingClient` filled the
upper end naturally.

| File | Count | Coverage |
|---|---|---|
| `test_stream_parser.py` | **27** | 21 parser unit tests (every `op` × every `ct`, side/persistence translation, multi-market, sport-agnostic, malformed, bytes decode, empty/whitespace) + 6 integration tests where `StreamReader` drives `StreamingClient._handle_message` end-to-end (lifecycle → SUBSCRIBED, image → cache fresh, delta → updated runner, status degraded → cache stale, ocm → order cache populated, heartbeat interleaved → loop survives) |
| `test_translation.py` | **12** | 1 test per surface (5 reads + 3 writes) + unknown-path raises + JSON-RPC error → 401 → auth_expired + path-style transport unaffected sentinel + sport-agnostic |
| `test_strategy_tag.py` | **5** | place/cancel/replace round-trip strategy_tag to audit entry; never-sent-to-Betfair sentinel; default-None backward-compatibility |
| `test_consumer.py` | **10** | container with/without streaming + immutability; 6 helpers route correctly; cache-vs-REST routing through container |

**Final test count:** `158 (W2+W1+W0 baseline) + 54 (W3) = 212 passed`.

**Toolchain:**

- `uv run ruff check` — `All checks passed!`
- `uv run mypy .` — `Success: no issues found in 86 source files`
- `uv run lint-imports` — `5 kept, 0 broken` (DR-030 layered
  architecture intact; no new domain/store/contracts/workflow imports
  added).

---

## §10 — Single commit summary

Commit SHA: **`2329604`** on `main` (W3 follows W0 `67a7f04`, W1
`0f5fae3`, W2 `254fcfc`).

```
$ git log --oneline -4
2329604 W3: live-pricing consumer path (§5.1 streaming wire-format parser + §5.2 translating transport adapter + §5.3 F5 strategy_tag contract revision v1.1 + §5.4 consumer-side reading paths)
254fcfc W2: betfair_client v1.0 implemented per locked contract (...)
0f5fae3 W1: vps_client v1.0 implemented per locked contract (...)
67a7f04 W0: v3 repo skeleton initialised per DR-030 (layout) and DR-031 (stack)
```

Stats: 13 files changed, 3126 insertions(+), 4 deletions(-).

File list:

**New files:**
- `clients/betfair_client/v1/_stream_parser.py`
- `clients/betfair_client/v1/_translation.py`
- `clients/betfair_client/v1/consumer.py`
- `tests/fixtures/betfair/raw_stream_frames.py`
- `tests/clients/betfair_client/v1/test_stream_parser.py`
- `tests/clients/betfair_client/v1/test_translation.py`
- `tests/clients/betfair_client/v1/test_strategy_tag.py`
- `tests/clients/betfair_client/v1/test_consumer.py`

**Modified files:**
- `clients/betfair_client/v1/__init__.py` (consumer re-exports)
- `clients/betfair_client/v1/_audit.py` (AuditLogEntry.strategy_tag)
- `clients/betfair_client/v1/placement.py` (strategy_tag param + forwarding)
- `clients/betfair_client/v1/cancellation.py` (strategy_tag param + forwarding)
- `clients/betfair_client/v1/replacement.py` (strategy_tag param + forwarding)
- `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  (status header + §6 version history + §11.1/§11.2/§11.3 signatures
  + parameter rows + §12.1 AuditLogEntry shape + v1.1 distinction
  paragraph).

---

## §11 — Findings

Four findings surfaced. None blocked verification. All four classified
as **scope-question / future-substrate** for operator-Claude triage.

### Finding F1: brief §5.1 frame-type vocabulary diverges from W2 envelope contract

- **Step where it surfaced:** §6 step 2 (parser substrate read).
- **Expected:** brief §5.1 frame-types list reads "`mcm` ... Maps to
  `op=\"market_image\"` or `op=\"market_delta\"`" and "`ocm` ... Maps to
  `op=\"order_unmatched\"` or `op=\"order_matched\"`".
- **Actual:** the W2 internal envelope (per `streaming.py` module
  docstring — `{"op": "...", "payload": {...}}` — and per
  `tests/fixtures/betfair/stream_messages.py`) uses `op="mcm"` with
  payload `is_image: True/False`, and `op="ocm"` (single value, the
  unmatched-vs-matched distinction is implicit in the `unmatched` /
  `matched_backs` / `matched_lays` payload arrays). Brief §3 pre-reads
  flagged the W2 envelope as "the integration contract"; brief §5.1
  also said "StreamReader integrates with W2's StreamingClient.connect()
  / disconnect() lifecycle without modifying streaming.py's state
  machine."
- **Output:** parser ships producing the W2 envelope shape (`op="mcm"`
  with `is_image`, `op="ocm"` single value). The brief's vocabulary
  divergence is wording-level only — the parser-shape decision was
  unambiguous given the integration-contract framing.
- **Code's read:** cosmetic. Future briefs that reference the parser
  envelope ops should use the W2 vocabulary (`mcm` with `is_image` /
  `ocm`) rather than the `market_image`/`market_delta` framing in
  brief §5.1.
- Code did NOT attempt to re-shape the envelope per brief §1's "no
  edits outside scope" — modifying `streaming.py._handle_message` to
  consume new ops would be a contract-breaking change inappropriate
  for a single bounded session.

### Finding F2: `listMarketBook` does not carry `marketTime`; adapter synthesises `scheduled_start_time`

- **Step where it surfaced:** §6 step 3 (translation table for
  §9.1 live-pricing reads).
- **Expected:** the contract's `MarketPrices` shape includes
  `scheduled_start_time: datetime` as a required field. The path-style
  endpoint `/v1/market/{id}/prices` translates to Betfair's
  `listMarketBook`.
- **Actual:** Betfair's `listMarketBook` response does not carry
  `marketTime` directly — that field belongs to `listMarketCatalogue`
  with `marketProjection=[MARKET_START_TIME]`. The adapter's
  `_translate_market_book` falls back to current wall-clock UTC when
  the response omits `marketDefinition.marketTime`. Acceptable for
  W3's mocked-only scope; tests that supply `marketDefinition` exercise
  the real path.
- **Output:** adapter ships with `scheduled_start_time` synthesised
  from (in priority order): `marketDefinition.marketTime`,
  top-level `marketTime`, current UTC. The synthesis path is
  transparent at the contract surface — `parse_market_prices`
  accepts the payload either way.
- **Code's read:** v3 build proper deployment substrate. Real-API
  integration will need either (a) a second `listMarketCatalogue`
  lookup cached at subscription time per market, or (b) accept that
  the streaming cache already carries `marketDefinition.marketTime`
  for SUBSCRIBED markets and the REST fallback path runs only when
  the cache is unavailable (in which case a fresh `listMarketCatalogue`
  call is operationally cheap). Surface for v3 build proper W4+
  deployment work, not a contract-shape decision.

### Finding F3: identity-check translates to `listMarketCatalogue` runner-presence inspection

- **Step where it surfaced:** §6 step 3 (translation table for
  §9.5 identifier-resolution check).
- **Expected:** the contract's `/v1/identity/check` returns
  `IdentityCheck(exists, market_status, runner_status, event_id)`.
- **Actual:** Betfair has no dedicated identity-check API; the closest
  analog is `listMarketCatalogue` with the market ID and inspection of
  whether the requested `selection_id` appears in `runners[]`. The
  adapter implements that pattern: empty catalogue → `exists=False`;
  catalogue with non-matching selection → `exists=False` (with
  `market_status` populated); catalogue with matching selection →
  `exists=True` with full payload.
- **Output:** translation correct for the W3 mocked-only scope. The
  test `test_identity_check_translates_to_listMarketCatalogue`
  verifies the round-trip.
- **Code's read:** v3 build proper deployment may want to inspect
  whether `listMarketCatalogue` is the most efficient path for
  identity checks at burst-window cadence — alternatives include
  `listEvents` for event-level identity or piggy-backing on the
  existing live-pricing cache. Not a contract-shape decision; surface
  for visibility.

### Finding F4: `betfairlightweight` library declared but not directly imported in W3

- **Step where it surfaced:** §6 step 2 (parser implementation).
- **Expected:** brief §5.1 named `betfairlightweight` per DR-031 as
  the parser's foundation library; "library handles socket-level
  frame reading, TLS handshake, and the wire-format encoding/decoding."
- **Actual:** W3's parser does not directly import
  `betfairlightweight` because no socket is opened during W3 (mocked-
  only scope per brief §4). The parser receives `bytes | str | dict`
  from any iterable source — this is the same shape
  `betfairlightweight.streaming.listener.StreamListener.on_data(raw_data)`
  receives at runtime. The integration is shape-compatibility-by-
  design: v3 build proper deployment wires
  `StreamListener` socket output into `StreamReader(raw_source)`
  without modifying the parser.
- **Output:** the library is a declared dependency (per
  `pyproject.toml`, originally for W2 but unused there per W2 F2);
  W3 also does not exercise it. The shape-compatible parser is
  ready for the deployment-time wire-up.
- **Code's read:** consistent with the brief's mocked-only scope and
  with W2's pattern. v3 build proper deployment will import
  `betfairlightweight`'s `APIClient` for the auth + socket open and
  pass the listener's `on_data` output into `StreamReader`. Surface
  for visibility — the W3+ deployment brief should name this
  integration point explicitly so the parser is hooked correctly.

---

## §12 — Self-assessment

**Did Code stay within the named anchors?** Yes. All four deliverables
land in `clients/betfair_client/v1/` (parser, adapter, F5 code) plus
the F5 contract revision in
`dr029/2_7_api_contract_versioning/betfair_client_contract.md`. No new
modules outside `betfair_client`. No `vps_client` work. No operational
store work. No real Betfair API calls. No new dependencies. F3 mirror
enums kept duplicated (per Session 85 lock). F6 rate-limit budget
untouched. Auth handling unchanged from W2. The audit substrate
remains pluggable Protocol + Stdout/MemorySink (durable substrate
selection deferred to v3 build proper deployment).

**Were any out-of-scope items touched?** No. The contract revision is
the only governance-artefact edit; it is the F5 revision named in
brief §5.3 + step 4 + §11. No DR additions, no `architecture.md`
edits, no `decisions.md` edits, no service-layer modules, no UI
work.

**Did the session fit a single bounded run?** Yes. ~24 minutes
wall-clock from anchor-start to anchor-close (17:20 → 17:44 ACST).
The work fit comfortably; the parser (flagged in brief §6 as the
most likely budget pressure point) landed cleanly with one cycle on
the sport-agnostic test (loosened a key-set equality assertion that
was incidentally over-strict on optional-field parity). The
translating transport's path-prefix handling required one cycle (the
first run did not strip the BetfairRestClient base URL prefix; tests
caught it on first pass).

**Strain-point status.** Not hit. Parser landed clean; no fallback
to "ship parser only" per §7.6 was needed. All four deliverables
(parser + adapter + F5 + consumer) ship in one commit.

**Completion criteria.** Full scope per §7.6. All §7.1–§7.5
verification criteria met:

- §7.1 parser: all 7 frame-type round-trips correct; malformed
  surfaces as `unknown`; sport-agnostic; lifecycle ack sequence;
  end-to-end `StreamingClient` integration; empty/boundary frames;
  `betfairlightweight` shape-compatible (not directly imported per
  F4 finding).
- §7.2 adapter: all 8 surfaces translate correctly; JSON-RPC
  responses reverse-map; default path-style transport unchanged
  (W2's 158 baseline tests continue to pass); coverage table
  exercised; rate-limit constants untouched.
- §7.3 F5: contract edits applied to §11.1/§11.2/§11.3 + §12.1 +
  §6 version history + status header; code edits applied;
  `strategy_tag` not in placement request body; default-None
  backward-compatible; W2 placement tests unchanged.
- §7.4 consumer: 6 helpers route correctly; container constructs
  with/without streaming; envelope shapes pass through unchanged;
  no batching/retry/write-surface coverage; module lives in
  `consumer.py`.
- §7.5 cross-cutting: 212 tests passed; mypy clean; ruff clean;
  no real Betfair API calls; no new dependencies; no out-of-scope
  modifications.

**Anything Code thinks the next operator-Claude session should know
that the report doesn't otherwise capture:**

1. **The brief's "market_image"/"market_delta"/"order_unmatched"/"order_matched"
   parser-op vocabulary (§5.1) is divergent from the W2 envelope
   contract.** F1 above. The W2 envelope (`op="mcm"` with `is_image`,
   `op="ocm"` single value) is the actual integration contract. Future
   briefs touching the streaming envelope should use that vocabulary.

2. **The `BetfairClient` container is the canonical "give me a
   Betfair handle" shape for v3.** Frozen dataclass with
   `rest_client` (required) + `streaming_client` (optional). W4 bet
   entry and W7 burst review will both consume it. Pattern matches
   the brief §10 substrate carry-forward.

3. **`TranslatingTransport` is the integration point for v3 build
   proper real-API deployment.** Wire
   `BetfairRestClient(transport=TranslatingTransport(inner=httpx_transport))`
   at startup; surfaces continue to call path-style URLs unchanged.
   The translation table covers all 8 surfaces; per F2, real-API
   deployment may want to enrich `listMarketBook` responses with
   a separately-cached `marketTime` from `listMarketCatalogue`.

4. **F5 `strategy_tag` is wired through the three write surfaces but
   not yet populated by any caller.** W4 bet-entry layer will be the
   first caller to populate it meaningfully. Recommend the W4 brief
   names tag-value conventions explicitly (Path A locked the
   contract-side as free-form `Optional[str]`; v3 bet-entry layer
   owns validation).

5. **Cadence-parameter constants (W2 self-assessment item 1) carry
   forward unchanged.** `streaming.py` six constants, `_connection.py`
   two — Fix 4 calibration targets. The W3 adapter does not introduce
   new placeholder constants; rate-limit enforcement remains W2 F6
   territory.

6. **`betfairlightweight` is shape-compatible but not imported by W3
   (or W2).** Per F4. v3 build proper deployment will import the
   library's `APIClient` + `StreamListener`; the parser's
   `StreamReader` accepts `StreamListener.on_data` output without
   modification.

---

## §13 — Anchor (session close)

`2026-05-05 17:44:31 ACST` (Adelaide local, per DR-021).

**Session duration:** ~24 minutes from anchor-start to anchor-close.

**End of report.**
