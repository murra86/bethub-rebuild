# Brief — Betfair Streaming transport build (§2.4 §3–§7)

**Status:** LOCKED (operator-approved Session 159,
2026-06-18 ACST). Contract — Code executes against this as-written.
**Type:** Build (single bounded Claude Code session).
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`).
**Drafted:** Session 159, 2026-06-18 ACST.
**Serves:** the operator-side `$5` lay validation — currently
blocked because the live order-placement path refuses with
`betfair_streaming_disconnected` (HTTP 503).

---

## 1. What this brief is and is not

This is a **build** brief. Claude Code implements the live
Betfair Streaming **transport layer** — the real TCP/SSL socket,
the authentication handshake, the market + order subscriptions,
the read loop, and reconnection — against the **locked** §2.4
spec, then wires it into the app's startup so live mode brings
the connection up to `SUBSCRIBED`.

It is executed in a **single bounded Code session**. If the full
build cannot complete coherently in one session, Code ships the
**core bring-up** (connect → authenticate → subscribe → read loop
→ `SUBSCRIBED` → clean teardown, with tests) as a coherent unit
and surfaces the remaining hardening (reconnection edge cases,
`keepAlive`, `INVALID_SESSION` recovery) as **named findings**
for a follow-up brief. Partial-but-coherent beats
complete-but-lost-coherence.

Surprises are **findings in the report**, not blockers and not
mid-session pings to the operator. Remediation of anything Code
discovers routes to the next operator-Claude triage session, not
into this Code run.

**This brief does not authorise any live Betfair connection
during Code's session.** Code builds and unit-tests against a
**fake in-memory socket** only. The genuine end-to-end proof
(the socket actually reaching `SUBSCRIBED` against real Betfair)
is **operator-side**, performed by Tim at launch after this brief
lands. See §4 and §9.

---

## 2. Why this work exists

Session 159 traced a live `503` on `POST /api/v1/racing/lay`.
Root cause, confirmed in code: the order-placement path is gated
by a deliberate safety interlock that refuses to place any bet
while the Betfair Streaming connection is not `SUBSCRIBED`
(`clients/betfair_client/v1/placement.py:158-159`). The price
**read** path uses REST and works; the Streaming connection —
which exists to let the app *watch* an order's fate in real time
— was shipped as a **state-machine shell only**. The real socket
transport was always marked "v3 build proper" and has not been
built (`streaming.py` `connect()` is a pure state transition; the
live branch of `build_streaming_client` hands back a
`DISCONNECTED` client; the app `lifespan` hook is empty).

So the `503` is the system correctly refusing to place a bet it
cannot watch. This brief builds the missing transport so the
interlock passes **for real**, unblocking the `$5` lay.

The W3 commit already built the **pre-parse** layer
(`_stream_parser.py` §5.1 — `parse_frame()` decodes wire frames
into the envelope shape `streaming.py._handle_message()` already
consumes). What is missing is the **transport beneath it**: the
socket I/O, the auth/subscribe message sending, the read loop
that feeds the parser, and reconnection. The seam is clean and
named by `_stream_parser.py`'s own docstring (it explicitly
excludes "socket-level frame reading, TLS handshake, and
on-the-wire JSON decoding").

---

## 3. Pre-reads

**Required, in order:**

1. `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` — the
   **locked** §2.4 spec. The authority for this build. §3
   (connection management), §4 (authentication), §5 (market
   subscriptions), §6 (order subscriptions), §7 (message handling
   + cache shape) are the load-bearing sections. Where this brief
   and the spec appear to differ, **the spec wins** — surface the
   discrepancy as a finding.
2. `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` —
   canonical Stream API wire-protocol reference (auth message,
   subscription messages, `mcm`/`ocm`, `clk`/`initialClk`,
   heartbeat). 986 lines; the on-the-wire detail the transport
   must speak.
3. `clients/betfair_client/v1/streaming.py` — the existing state
   machine, caches, and `_handle_message` dispatch the transport
   must drive. **Read in full** — the transport plugs into the
   seam this file defines.
4. `clients/betfair_client/v1/_stream_parser.py` — the existing
   W3 wire-format parser (`parse_frame`, `StreamReader`). The
   transport's read loop **reuses** this; it is not rebuilt.

**Reference-only (read on demand):**

- `clients/betfair_client/v1/_auth_betfair.py` and `_auth.py` —
  the `AuthProvider` (exposes `app_key()` + `session_token()`,
  which the auth handshake consumes; Streaming and REST share one
  session per §4.7).
- `clients/betfair_client/v1/_connection.py` — the REST transport
  (`BetfairRestClient`), as the precedent for transport shape /
  error types; **not modified by this brief**.
- `ui/api/dependencies/composition.py` `build_streaming_client`
  (~line 308) — the live-vs-mock construction seam.
- `ui/api/main.py` `lifespan` (line 33) — the empty startup hook.
- `clients/betfair_client/v1/placement.py` (~line 158) — the
  `SUBSCRIBED` interlock. **Read to preserve, not to change.**

---

## 4. System access

- **Mac filesystem, read-write**, confined to the named anchors
  in §5 and their test files. No edits outside those anchors.
- **No live Betfair connection.** Code must not open a socket to
  `stream-api.betfair.com`, must not perform a live Betfair
  login, and must not read or use the operator's credentials file
  (`/Users/tim/Desktop/Projects/bethub-secrets/betfair.json`).
  All Code-side testing is against a **fake/in-memory socket**
  (frames injected, no network). This protects the login throttle
  (a real prior lockout lasted ~48h) and keeps the live proof
  operator-side.
- **No databases** are read or written by this brief.
- **Git working tree is dirty** (the accumulated, largely
  uncommitted v3 build on branch `main`, one commit). Dirty-tree
  discipline in §9 applies. Code captures `git status` at session
  start as its own baseline.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every
  time-of-day reference in the report.

---

## 5. Build scope

The build implements §2.4 §3–§7. Sub-sections below name the
anchors and the spec sections each must satisfy. The spec is the
detailed authority; this brief names *what* and *where*, the spec
names *exactly how on the wire*.

### 5.1 Streaming transport — the socket

**Anchor:** new transport module in
`clients/betfair_client/v1/` (Code names it, e.g.
`_stream_transport.py`), invoked from `streaming.py`.

- Open a long-lived TCP/**TLS** socket to the §3.1 endpoint
  (`stream-api.betfair.com:443` — production; the integration
  endpoint is parked, do not use).
- Drive the §3.2 connection lifecycle states already defined in
  `streaming.py` (`DISCONNECTED → CONNECTING → AUTHENTICATING →
  SUBSCRIBED`, plus `RECONNECTING`) from **real** socket events —
  not the test-only injected acks.
- Run as a background async task so the read loop (§5.4) does not
  block the FastAPI event loop.

### 5.2 Authentication handshake (§3.3, §4)

- On socket open, send the authentication message **immediately**
  (§3.3 — the 15-second rule; Betfair drops the connection with
  `TIMEOUT` if the first message is late). No lazy auth.
- Build the auth message from the injected `AuthProvider`:
  `app_key()` + `session_token()` (§4.1). Streaming and REST
  share the one session (§4.7) — use the same provider, do not
  mint a second login.
- Transition to `SUBSCRIBED` only on a **genuine** success status
  from Betfair (`connection_ack` then `auth_ack`/status per the
  wire reference). Never synthesise these in live mode.

### 5.3 Subscriptions (§5 market, §6 order)

- Send the market subscription (§5 — coarse scope, the field
  filter per §5.2/§5.3) and the **order** subscription (§6 —
  order streaming is how the app watches an order's fate; this is
  what the placement interlock depends on).
- Hold the §3.4 state-preservation tokens (`initialClk`, `clk`)
  for resubscribe-on-reconnect.

### 5.4 Read loop → existing parser → existing dispatch

- Read frames off the socket, hand each to the **existing**
  `_stream_parser.parse_frame()`, and feed the resulting envelope
  to the **existing** `streaming.py._handle_message()`. Do **not**
  reimplement parsing or dispatch — only the transport that drives
  them. Reuse `_stream_parser.StreamReader` where it fits.
- Heartbeat tracking per §7 / §3.4: the existing constants in
  `streaming.py` (heartbeat-death window, back-off sequence) are
  the source of truth — reuse them, do not redefine.

### 5.5 Reconnection, keepAlive, session recovery (§3.4–§3.5, §4.4, §4.6)

- Detect drops two ways (§3.4): socket-level error/close, and
  heartbeat-loss (no message for 2× negotiated `heartbeatMs`).
- Reconnect with the §3.5 back-off discipline (first retry
  immediate, then the defined escalating sequence), resubscribing
  with held `clk`/`initialClk`.
- `keepAlive` (§4.4) and `INVALID_SESSION` recovery (§4.6 — on
  `INVALID_SESSION`, trigger one fresh login via the auth
  provider, subject to the §4.5 rate-limit floors). These are the
  parts most likely to overflow a single session — if so, ship
  §5.1–§5.4 + §5.6 coherent and surface these as named findings.

### 5.6 Composition + lifespan wiring (live-mode bring-up)

**Anchors:** `ui/api/dependencies/composition.py`
`build_streaming_client` (~line 308); `ui/api/main.py` `lifespan`
(line 33).

- Live mode must bring the connection up to `SUBSCRIBED` at app
  startup. Per the spec's connection-per-process shape (§3.6) and
  the existing composition comment ("scheduled by a lifespan
  startup hook"), the bring-up belongs in the **`lifespan`
  startup hook**, not buried in the constructor. `lifespan`
  starts the background transport task (live mode only), waits for
  `SUBSCRIBED` within a bounded budget, and tears the socket down
  cleanly on shutdown.
- **Mock mode is unchanged.** The existing mock path (injected
  `connection_ack`/`auth_ack`, faked `SUBSCRIBED`) stays exactly
  as-is and remains the default. Live bring-up fires **only** when
  `settings.betfair_mode == "live"`.
- If live bring-up fails (no socket, auth fail, timeout), it must
  fail **loudly and safely**: log clearly, leave the streaming
  client **not** `SUBSCRIBED`, and let the app still start serving
  reads. The placement interlock then keeps refusing lays (the
  correct safe state) rather than the app placing blind.

### 5.7 Preserve the placement interlock — do not weaken

`clients/betfair_client/v1/placement.py` is **not modified**. The
`SUBSCRIBED` gate at ~line 158 is the bet-safety property this
whole build serves: a bet is only placeable when the app can
watch it over a live order stream. Success of this brief is that
the gate now passes because the stream **genuinely** reaches
`SUBSCRIBED` — never because the gate was loosened, short-circuited,
or fed a synthesised state in live mode.

---

## 6. Sequencing within session

1. Capture baselines (§7): `git status`, full test run.
2. §5.1 socket transport + §5.2 auth handshake (reach
   `AUTHENTICATING` → `SUBSCRIBED` against the fake socket).
3. §5.3 subscriptions + §5.4 read-loop wiring to the existing
   parser/dispatch.
4. §5.5 reconnection / keepAlive / session recovery.
5. §5.6 composition + lifespan wiring; confirm mock unchanged.
6. Tests throughout (§7); re-run full suite at the end.

A cleaner order Code discovers is fine — say so in the report.

---

## 7. Empirical verification

**Baselines captured at session start** (report both pre and
post):

- `git status --short` — the dirty file list before any edit.
- Full test suite — capture the starting counts. (Expected
  starting point ~`991` pytest passing as of Session 158; capture
  the **actual** number, do not trust this figure.)

**What Code verifies in-session (against a fake socket):**

- Feeding a scripted frame sequence (connection_ack → auth_ack →
  market sub image → order sub image → heartbeats) drives the
  state machine to `SUBSCRIBED` and populates the market + order
  caches via the existing `_handle_message` path.
- A simulated drop (socket close, and separately heartbeat-loss)
  triggers `RECONNECTING` and a resubscribe with held
  `clk`/`initialClk`.
- `INVALID_SESSION` on the fake stream triggers exactly one
  re-login via a stubbed auth provider (within §4.5 floors).
- **Mock mode is byte-for-byte unchanged**: the existing
  streaming tests still pass; mock launch still reaches a faked
  `SUBSCRIBED` and serves.
- Lint / import-linter / type-check all green (or unchanged from
  baseline if pre-existing items exist).

**What Code CANNOT verify (operator-side carve-out):** the real
socket reaching `SUBSCRIBED` against live Betfair, and a real lay
clearing the interlock, can only be confirmed by Tim launching
`BetHub.command` live. This is the Session 36-style
in-session-vs-out-of-session carve-out — name it explicitly in
the report; do not attempt a live connection to close it.

---

## 8. Output spec

Single report file:
`dr029/2_4_betfair_streaming/stream_transport_build_report.md`.

Structure:

1. Session anchor (Adelaide local), baselines (git + tests).
2. What was built, per §5 sub-section, with the files/regions
   touched and the spec sections satisfied.
3. Test results: pre/post counts; the fake-socket scenarios
   added; mock-mode-unchanged proof.
4. Anything deferred as a **finding** (esp. §5.5 hardening) with
   enough detail to scope a follow-up.
5. The operator-side verification carve-out, stated plainly:
   exactly what Tim does at launch to prove `SUBSCRIBED` and then
   place the `$5` lay.
6. `git status` + per-file `git diff` summary confirming edits
   stayed within named anchors.
7. Self-assessment: did it fit one session; any spec
   discrepancies surfaced.

Rough length 250–500 lines. Over-run is fine if it is load-bearing
build detail; flag it in the self-assessment. The report contains
**no** recommendations beyond scoping deferred findings, and **no**
scope creep into other §2.x items.

---

## 9. Hard limits — what's NOT in scope

Non-negotiable:

- **No live Betfair connection during Code's session.** No socket
  to `stream-api.betfair.com`, no live login, no use of the
  credentials file. Fake-socket testing only. (Protects the login
  throttle and the operator-side proof.)
- **Do not weaken, bypass, short-circuit, or synthesise the
  `SUBSCRIBED` interlock in live mode.** `placement.py` is not
  modified. Faked acks remain mock-only.
- **No git operations:** no `add`, `commit`, `stash`, `restore`,
  `checkout` (file-targeted), `reset`, `clean`. Read working-tree
  state at start; after each edit run `git diff <file>` to confirm
  only intended changes; at close run `git status` to confirm the
  dirty file list changed **only** by the named anchors + their
  tests.
- **Named anchors only.** Edits confined to: the new transport
  module, `streaming.py` (wiring the transport in), `composition.py`
  (`build_streaming_client`), `main.py` (`lifespan`), and the
  corresponding test files. No "while we're here" edits to the REST
  read path (`consumer.py`, `live_pricing.py`, `_connection.py`),
  the parser (`_stream_parser.py` — reused, not edited unless a
  genuine bug blocks reuse, which is a finding), or anything else.
- **No schema changes**, no migrations, no DB access.
- **Mock mode unchanged** and remains the default.
- **No scope creep** into other §2.x items (settlement §2.6,
  bet-schema §2.8, soft-book §2.5, etc.).
- **No mid-session operator escalation.** Run end-to-end; surface
  everything in the report.
- **Single bounded session** — if it won't fit, ship core +
  findings (§1), don't continue past a coherent stopping point.

---

## 10. What happens after Code's session

1. **Next operator-Claude (Chat) session triages the report** —
   reads `stream_transport_build_report.md`, classifies any
   findings by operational / bet-safety impact, decides whether a
   §5.5 hardening follow-up brief is needed or the build is whole.
2. **Operator-side live proof (Tim):** launch `BetHub.command`
   live, confirm the connection reaches `SUBSCRIBED` (watch the
   Terminal), open the racing page, then place the **`$5` lay** and
   check it on Betfair. This is the validation the whole arc has
   been sequencing toward.
3. If live bring-up misbehaves, triage from the Terminal output in
   the following Chat session — the throttle protects against any
   repeat-fail lockout meanwhile.

Code does **not** write the follow-up brief; that is the next
Chat session's call.

---

## 11. Cross-references

- **Scope:** DR-029 §2.4 (Betfair Streaming spec) — this brief
  builds the transport the locked §2.4 contract specifies.
- **Spec authority:** `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`
  §3–§7; wire reference `betfair_stream_api_reference.md`.
- **DRs:** DR-021 (Adelaide timestamps), DR-031 (FastAPI/uvicorn
  stack), DR-032 (Betfair canonical / auth), DR-030 (v3 layout —
  new module homes under `clients/betfair_client/v1/`).
- **Prior work reused:** W3 commit (`_stream_parser.py` §5.1
  parser; `streaming.py` W2 state machine + `_handle_message`).
- **Finding origin:** Session 159 live `503` triage on
  `POST /api/v1/racing/lay`.
- **Excluded parking-lot:** integration-endpoint test infra
  (named-debt, parked at DR-029 close); reconnection hardening may
  defer to a follow-up per §1/§5.5.
