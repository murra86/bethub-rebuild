# Build report — Betfair Streaming transport (§2.4 §3–§7)

**Brief:** `dr029/2_4_betfair_streaming/stream_transport_build_brief.md` (LOCKED, Session 159).
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`), branch `main`, baseline commit `2329604`.
**Outcome:** Core bring-up shipped **coherent and complete** — connect → authenticate → subscribe → read loop → genuine `SUBSCRIBED` → clean teardown, plus reconnection (socket + heartbeat-loss) with token-preserving resubscribe and one-shot `INVALID_SESSION` recovery. One §5.5 item (`keepAlive` scheduling) deferred as a named finding. Fit one session.

---

## 1. Session anchor + baselines

- **Session start:** 2026-06-18 ~08:50 ACST (Adelaide local, DR-021).
- **Report written:** 2026-06-18 09:19 ACST.
- **Test runner:** `uv run pytest` (Python 3.12 venv). **Finding F1:** the memory note "`python3` on this machine" is wrong for `bethub-v3` — the system `python3` is 3.11 and lacks `httpx`, so `python3 -m pytest` fails at collection (`starlette.testclient requires httpx`). The repo is a `uv` project (`.venv`, `.python-version=3.12`); the correct runner is **`uv run pytest`**. Captured the real baseline under `uv`.

### Baselines captured before any edit

| Baseline | Value |
|---|---|
| `git status --short` | 54 entries (dirty v3 tree, as expected) — snapshot at `/tmp/baseline_git_status.txt` |
| Full suite (`uv run pytest -q`) | **991 passed**, 0 failed, 4 warnings (matches the brief's ~991 expectation) |
| ruff / mypy / import-linter | pre-existing items noted in §4 |

---

## 2. What was built (per §5)

The seam was exactly as the brief framed it: the W3 parser (`_stream_parser.parse_frame` / `StreamReader`) and the W2 state machine + caches + dispatch (`streaming.StreamingClient._handle_message`) were **reused unchanged**; only the transport beneath them was built.

### 2.1 Streaming transport — the socket (§5.1, spec §3.1/§3.2/§3.6)

**New module:** `clients/betfair_client/v1/_stream_transport.py` (`BetfairStreamTransport`).

- Opens a long-lived TLS socket to `stream-api.betfair.com:443` (§3.1, hardcoded module constant — production exclusively; integration endpoint parked). The real connector (`open_tls_connection`, `asyncio.open_connection(..., ssl=...)`) exists as a reviewable code path but is **invoked only via the injected `connector` seam** — never in tests or this session.
- Runs as a background **asyncio task** (`asyncio.create_task`), not a thread (Code-side call, approved — FastAPI/uvicorn stack per DR-031; spec §1/§2 defers threading model to Code). The read loop does only read → parse → dispatch and never blocks on consumer work, satisfying the §7.9/§12.3 I/O-isolation intent.
- Drives the §3.2 lifecycle (`DISCONNECTED → CONNECTING → AUTHENTICATING → SUBSCRIBED`, `RECONNECTING`) from **real** socket events — the transport never sets state directly; it feeds parsed envelopes (and one internal `disconnect` signal on drop) into the existing `_handle_message`.

### 2.2 Authentication handshake (§5.2, spec §3.3/§4.1/§4.7)

- On receiving the genuine `connection` frame (→ `AUTHENTICATING`), the transport **immediately** writes the authentication message (§3.3 15-second rule; no lazy auth).
- The message is built from the injected `AuthProvider`: `appKey` = `auth.app_key()`, `session` = `auth.session_token()` (§4.1). The same provider serves REST (§4.7) — no second login is minted. Credentials are never logged (the auth message op/id are logged; the token is not — §4.2).
- `SUBSCRIBED` is reached **only** on a genuine success `status` parsed off the socket (W3 promotes the first post-`connection` SUCCESS to `auth_ack`; W2 `_on_auth_ack` promotes to `SUBSCRIBED`). **No synthesised acks in live mode.**

### 2.3 Subscriptions (§5.3, spec §5 market / §6 order / §13 BSP flags)

Sent immediately after auth success (§5.4), independently on the one connection:

- **Racing market subscription** (`marketSubscription`, id=1): `marketFilter` = `eventTypeIds:["7","4339"]`, `countryCodes:["AU"]`, `marketTypes:["WIN","PLACE"]` (coarse, §5.1 — race-type scoping deferred to the consumer surface). `marketDataFilter.fields` = `EX_BEST_OFFERS_DISP, EX_LTP, EX_MARKET_DEF, SP_PROJECTED, SP_TRADED` (§5.2 + the §13.1 BSP-reachability flags), `ladderLevels=3`, `heartbeatMs=5000`, `conflateMs=0`, `segmentationEnabled=true`.
- **Order subscription** (`orderSubscription`, id=2): `orderFilter` = `includeOverallPosition:true`, `partitionMatchedByStrategyRef:false`; `segmentationEnabled:true` (§6.2). This is the subscription the placement interlock depends on.
- **Sports market subscription** (id=3) is wired behind the `SPORTS_AU` scope flag (off by default in live composition); see Finding F2 on the unverified eventTypeIds.

### 2.4 Read loop → existing parser → existing dispatch (§5.4, spec §7)

- The loop reads CRLF frames with `asyncio.wait_for(reader.readline(), timeout=heartbeat_loss_seconds)`, hands each to the **existing** `parse_frame()`, and feeds the resulting envelope(s) to the **existing** `_handle_message()`. Parsing and dispatch are not reimplemented.
- **`initialClk` / `clk` held in the transport** (Code-side call, approved): the W3 parser does not surface the resubscribe tokens (they are recovery concerns, not cache-shape concerns), so the transport reads them off the raw frame itself, keyed per subscription request `id` (§8.1/§8.8). The parser is untouched.
- Heartbeat / back-off **constants are reused** from `streaming.py` (`HEARTBEAT_LOSS_THRESHOLD_SECONDS`, `RECONNECT_BACKOFF_INITIAL_SECONDS`, `RECONNECT_BACKOFF_MAX_SECONDS`) — not redefined.

### 2.5 Reconnection / session recovery (§5.5, spec §3.4/§3.5/§4.6/§8)

- **Drop detection, both paths (§3.4):** socket error / EOF (`readline()` returns `b""`) **and** heartbeat-loss (no frame for `2× heartbeatMs`, via the read `wait_for` timeout).
- On drop the transport feeds the internal `disconnect` op (→ `RECONNECTING`, failure counters per §8.7), then reconnects with the **§3.5 back-off** (first attempt immediate, then 1/2/4/8/16s capped at 30s; reset to immediate on a successful `SUBSCRIBED`).
- **Resubscribe carries the held `initialClk`/`clk`** (§8.2) so Betfair sends a `RESUB_DELTA`; cold start / token-absent sends a fresh image (§8.3/§8.4).
- **`INVALID_SESSION` recovery (§4.6):** the transport inspects the parsed `status` envelope's `error_code` (which W2's `_on_status` ignores) and on `INVALID_SESSION_INFORMATION`/`NO_SESSION` forces exactly one re-login via the provider's `clear_token()` (subject to the provider's own §4.5 login-rate floors), letting the socket drop so reconnect re-authenticates with the fresh token. One attempt per episode; reset on clean `SUBSCRIBED`.

### 2.6 Composition + lifespan wiring (§5.6)

- **`ui/api/dependencies/composition.py` → `build_streaming_client`:** live mode now builds a `BetfairStreamTransport` (racing market + order) and **attaches** it to the client, but does **not** start it — the client is returned still `DISCONNECTED`. Constructing the transport opens no socket (only `start()` does), so composing/importing the app never touches Betfair. **Mock mode is byte-for-byte unchanged** (same `subscribe_markets` + `connect` + synthesised `connection_ack`/`auth_ack`).
- **`ui/api/main.py` → `lifespan`:** in live mode only, starts the background transport task and waits up to a bounded budget (`LIVE_STREAMING_BRINGUP_TIMEOUT_SECONDS = 15.0`) for a **genuine** `SUBSCRIBED`, then tears the socket down on shutdown. **Fails loud and safe:** any error is logged and swallowed, the client is left not-`SUBSCRIBED`, and the app still starts serving reads — the placement interlock then keeps refusing lays (the correct safe state). Mock mode: the hook is a no-op.
- **Seam:** a thin lifecycle surface was added to `StreamingClient` (`attach_transport`, `has_transport`, `start_streaming`, `stop_streaming`, `await_subscribed`), held **duck-typed** so `streaming.py` imports nothing from the transport (no `transport → streaming → transport` cycle). This is the "invoked from `streaming.py`" seam the brief §5.1 names.

### 2.7 Placement interlock — preserved (§5.7)

`clients/betfair_client/v1/placement.py` is **not modified.** The `SUBSCRIBED` gate at `placement.py:158-159` is untouched. In live mode the gate now passes only because the stream **genuinely** reaches `SUBSCRIBED` — never via a loosened, short-circuited, or synthesised state. A dedicated test asserts that without a genuine SUCCESS status the client stays `AUTHENTICATING` and the gate stays closed.

---

## 3. Test results

| Metric | Pre | Post |
|---|---|---|
| Full suite (`uv run pytest -q`) | **991 passed** | **1002 passed**, 0 failed |
| New tests added | — | **+11** (8 transport + 3 composition/lifespan) |
| Streaming-related subset | — | 62 passed (transport + composition + W2 streaming + blocks-writes) |

### Fake-socket scenarios added (`tests/clients/betfair_client/v1/test_stream_transport.py`, 8 tests)

All drive an in-memory `FakeConnection` via the `connector` seam — **no network, no login, no credentials.** A guard asserts `host=="fake"`; the production endpoint constants are asserted but `open_tls_connection` is never called.

1. Scripted `connection → status SUCCESS → market SUB_IMAGE → order SUB_IMAGE` drives the **genuine** state machine to `SUBSCRIBED` and populates the market **and** order caches via the existing `_handle_message` path.
2. Authentication is the **first** client message and is built from the injected provider (`appKey`/`session`); subscriptions follow, after auth.
3. The market subscription carries the spec filters (`eventTypeIds 7/4339`, AU, WIN/PLACE, `ladderLevels=3`, `SP_TRADED` present, `heartbeatMs=5000`, `conflateMs=0`); the order subscription carries `includeOverallPosition=true` / `partitionMatchedByStrategyRef=false`.
4. **Bet-safety:** with no SUCCESS status the client never reaches `SUBSCRIBED` (stays `AUTHENTICATING`) — the interlock stays closed.
5. Socket close triggers `RECONNECTING` and a resubscribe carrying the held `clk` (§8.2).
6. Heartbeat-loss (no frame within the threshold) triggers reconnect (fresh authentication on the new connection).
7. `INVALID_SESSION_INFORMATION` triggers exactly **one** re-login (`clear_token` called once) then a clean reconnect.
8. The real connector targets the §3.1 production endpoint (static assertion; never invoked).

### Mock-mode-unchanged proof

- The pre-existing `test_streaming_client_in_mock_mode_is_subscribed` (mock → `SUBSCRIBED` with `RACING_AU` registered) **still passes** — the mock branch of `build_streaming_client` was not altered.
- All pre-existing W2 streaming tests (`test_streaming.py`) and the interlock test (`test_streaming_blocks_writes.py`) pass unchanged.
- New `test_lifespan_mock_mode_is_noop_and_unchanged` confirms the lifespan hook does nothing in mock mode.
- New `test_live_mode_attaches_transport_but_stays_disconnected` and `test_lifespan_brings_up_subscribed_via_fake_socket` confirm the live path: attached-but-DISCONNECTED at composition, genuine `SUBSCRIBED` after the lifespan bring-up (fake socket), `DISCONNECTED` after clean teardown.

### Lint / type / imports

- **ruff:** all checks pass on the touched files. `ruff --fix` also removed 4 **pre-existing** unused imports it found in two anchor files it was already reformatting (`os` in `composition.py`; `sys`, `build_betfair_client`, `build_storages` in `test_composition_root.py`) — these are within named anchors, flagged here for transparency.
- **mypy:** my four source modules are clean. One residual error — `workflows/balances/v1/balance_derivation.py:167 [no-any-return]` — is **pre-existing baseline** (transitively imported; that file is not in my change set, confirmed via `git status`).
- **import-linter (`lint-imports`):** all 5 contracts **KEPT** (DR-030 layering intact — the new transport sits in the `clients` layer and imports only stdlib + sibling modules).

---

## 4. Deferred items — named findings

- **F1 — Test runner is `uv run`, not `python3`.** (Operational, not a build defect.) See §1. Worth correcting in the project memory note so future sessions capture baselines correctly.
- **F2 — Sports eventTypeIds unverified.** `SPORTS_MARKET_FILTER` uses the commonly-cited AU values (AFL `61420`, NRL `1477`) but these were **not** verified live this session (no live calls permitted). Operator confirms via `listEventTypes` at launch. Low impact: the sports subscription is off by default in live composition and is not on the `$5`-lay (racing) path; sports placement is regulator-blocked in-play (§9.5.1).
- **F3 — `keepAlive` scheduling not built (§4.4 / §5.5).** The proactive 4-hour `keepAlive` REST call is **deferred**. It is a REST-surface concern (the transport holds no REST client), and the session token's 12-hour absolute window comfortably covers a single operator launch + the `$5`-lay validation. Scope for a follow-up: wire a 4-hour `keepAlive` task (REST `keepAlive`, fall back to fresh login on failure per §4.4) alongside the transport, sharing the one session. `INVALID_SESSION` recovery (§4.6) **is** built, so a mid-session expiry still self-heals on the next message — `keepAlive` is the proactive optimisation, not the safety net.
- **F4 — Sustained-failure operator escalation is partial (§3.5 / §8.7 / §15.6).** The state machine counts consecutive failures and the time-based window (existing W2 `_on_disconnect`), and the transport logs each reconnect, but the explicit "5 consecutive / 60-second → hard operator alert + unavailability surface" escalation tier (§8.7/§15.3) is not separately wired in the transport. Reconnect itself is correct and unbounded; this is the operator-visibility layer. Scope for the same follow-up as F3.
- **F5 — `RESUB_DELTA` vs `INVALID_CLOCK` fall-back (§8.3) relies on existing dispatch.** The transport resubscribes with tokens and the parser maps `RESUB_DELTA` to a delta; an `INVALID_CLOCK` status would currently surface as a degraded `status` and the connection would continue. The explicit "on `INVALID_CLOCK`, drop tokens and resubscribe fresh" branch (§8.3) is not specially handled. Low risk for a single launch (tokens are seconds-fresh); named for the hardening follow-up.

None of these block the `$5`-lay validation: the core bring-up reaches genuine `SUBSCRIBED`, the order subscription is active, and the interlock passes for real.

---

## 5. Operator-side verification carve-out (Session-36-style)

**What Code verified (in-session, fake socket):** the state machine reaches `SUBSCRIBED` from genuine acks; caches populate; reconnection + token-resubscribe + one-shot re-login fire; mock mode unchanged; the interlock stays closed without a genuine ack.

**What Code CANNOT verify (operator-side, by design — no live connection this session):** the real socket reaching `SUBSCRIBED` against live Betfair, and a real lay clearing the interlock.

**What Tim does at launch to close it:**
1. Ensure live credentials are in place (`BETHUB_BETFAIR_CREDENTIALS_PATH` → `app_key` + `username`/`password` for self-refreshing login, or `app_key` + `session_token`), set `BETHUB_BETFAIR_MODE=live`.
2. Launch `BetHub.command` live. Watch the Terminal: the lifespan hook logs `socket open to stream-api.betfair.com:443`, the `→ authentication` / `→ marketSubscription` / `→ orderSubscription` sends, and finally **`Betfair streaming reached SUBSCRIBED at startup.`** (If instead it logs the "did NOT reach SUBSCRIBED within 15s" error, the app still starts; triage from the Terminal output in the next Chat session — the login throttle protects against a repeat-fail lockout meanwhile.)
3. Open the racing page, place the **`$5` lay**, and confirm it on Betfair. The interlock now passes because the stream genuinely reached `SUBSCRIBED` — not because anything was loosened.

---

## 6. Edits stayed within named anchors

**Dirty file list changed by exactly two entries vs the captured baseline** (`comm` of `/tmp/baseline_git_status.txt` vs post):

```
+ ?? clients/betfair_client/v1/_stream_transport.py     (new transport module — §5.1 anchor)
+ ?? tests/clients/betfair_client/v1/test_stream_transport.py  (new test — anchor's test)
(no entries removed)
```

The other anchors were already in the dirty tree (so they add no new status line):

| Anchor | Git state | Change |
|---|---|---|
| `clients/betfair_client/v1/_stream_transport.py` | `??` (new) | the transport (≈600 lines incl. docstrings) |
| `clients/betfair_client/v1/streaming.py` | `M` (already) | +transport lifecycle seam (`attach_transport`/`start_streaming`/`stop_streaming`/`await_subscribed`/`has_transport`) + `_transport` attr. `+~110` lines; **`_handle_message` dispatch untouched** |
| `clients/betfair_client/v1/__init__.py` | `M` (already) | re-export `BetfairStreamTransport`, `open_tls_connection` (wiring imports required it — kept to the re-export + `__all__` lines, flagged per brief) |
| `ui/api/dependencies/composition.py` | `??` dir (already) | live branch of `build_streaming_client` + `app.state` stash + import; mock branch unchanged |
| `ui/api/main.py` | `??` dir (already) | `lifespan` live bring-up + teardown |
| `tests/ui/api/test_composition_root.py` | `??` dir (already) | +3 §5.6 tests |
| `tests/clients/betfair_client/v1/test_stream_transport.py` | `??` (new) | 8 fake-socket tests |

No edits to `placement.py`, `_stream_parser.py`, `consumer.py`, `live_pricing.py`, `_connection.py`, the auth providers, schemas, DB, or migrations. **No git writes** were performed (no add/commit/stash/restore/checkout/reset/clean). Verified throughout with read-only `git status` / `git diff`.

---

## 7. Self-assessment

- **Fit one session?** Yes. Core bring-up (§5.1–§5.4 + §5.6) shipped coherent, plus most of §5.5 (drop detection both ways, back-off resubscribe with held tokens, one-shot `INVALID_SESSION` recovery). Only `keepAlive` scheduling (F3) and the explicit sustained-failure operator-escalation tier (F4) and the `INVALID_CLOCK` fresh-image fall-back (F5) are deferred — all named with enough detail to scope a single follow-up. Partial-but-coherent was not needed; the result is whole for the `$5`-lay arc.
- **Spec discrepancies surfaced (spec wins):**
  - *Threading model.* Spec §7.9/§12.3 says "dedicated I/O thread"; built as an asyncio task. **Not a true conflict** — spec §1/§2 explicitly defers threading model to Code, and the app is asyncio/uvicorn (DR-031). Resolved in favour of the brief's "async task", which the operator pre-approved.
  - *Library.* `betfairlightweight` 2.23.1 is installed and the parser docstring cites it as "foundation", but the brief mandates reusing the W3 `parse_frame`/`StreamReader` seam — so a thin asyncio TLS socket feeds the parser rather than routing through bfl's listener (which would bypass the parser). Code-side call per spec §2, pre-approved.
  - *Token surfacing.* The W3 parser does not emit `initialClk`/`clk`; the transport reads them off the raw frame (integration seam, not a parser bug). Pre-approved.
  - *Two market subscriptions vs one.* Spec §5.1 defines racing **and** sports market subs; the `$5`-lay path is racing-only, so racing market + order is the load-bearing bring-up and sports is wired behind its scope flag (off by default). Scope judgment, noted (F2).
- **Build-vs-spec on `SUBSCRIBED` timing:** the existing W2 contract promotes to `SUBSCRIBED` on `auth_ack` (subscriptions registered) rather than on the first `SUB_IMAGE`. This matches spec §3.2 ("authenticated, subscriptions active") and the existing mock behaviour; the caches then populate as images arrive a beat later. Left as-is (not modified) — the interlock correctly keys on `SUBSCRIBED` = authenticated + subscribed.

**Bottom line:** the missing transport is built and genuinely reaches `SUBSCRIBED` against a fake socket; the placement interlock is preserved and now passes for real once the operator brings the live socket up. The `503 betfair_streaming_disconnected` on `POST /api/v1/racing/lay` is unblocked pending the operator-side live proof.
