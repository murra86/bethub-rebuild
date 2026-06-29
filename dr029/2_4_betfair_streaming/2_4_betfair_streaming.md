# §2.4 — Betfair Streaming spec and `betfair_client` contract

**Status:** Locked. Closes DR-029 §2.4.
**Authored:** Sessions 60, 61, 64 (2026-05-03 ACST).
**Governing DRs:** DR-027 (two-database architecture: BetHub owns operational state, capture.db owns analytical/source data), DR-028 (cross-database integration boundary discipline: no caching, no denormalisation, no second integration point), DR-029 (data-layer fit-for-purpose review before v3 build).
**Source recommendations:** multi-agent review Recommendation 2 (`agent_review/Judge/judge_synthesis.md`) — the operational-line Streaming spec was previously implicit in v3 architecture, now named.
**Cross-references:** `dr029/dr029_scope.md` §1.2 (two direct lines into Betfair), §2.3 (periodic-only API pattern, analytical line), §2.5 (soft-book interface contract, parallel operational module); `architecture.md` §B (operational layer); `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` (Stream API canonical reference, captured Session 59); `dr029/2_4_betfair_streaming/reference_guide/` (REST surface page captures); `external_api_resources.md` §1 (Betfair Reference Guide pointer-set).

---

## 1. Framing

The two direct lines into Betfair (§1.2 of the scope document) split
v3's Betfair integration cleanly: the analytical line runs through
`vps_client` against `capture.db` for backward-looking work
(post-hoc bet review, model calibration, BSP archive, market-curve
analysis); the operational line runs `betfair_client` direct from
v3 for live decision support (racing page, sports page, burst-review
workflow, bet entry, bet management, settlement reads).

§2.3 locked the analytical line as periodic-only and carved out the
operational line as a separate concern. §2.4 specifies the
operational line: the `betfair_client` module contract — what it
connects to, what it exposes upward to v3's UI and bet-entry code,
what it accepts going down to Betfair, and what discipline applies
at the edges.

The Stream API canonical reference (`dr029/2_4_betfair_streaming/
betfair_stream_api_reference.md`) is the primary input for the
streaming side of `betfair_client`. The Betfair Reference Guide
(REST surface) is the primary input for the order placement and
order state side; relevant pages are fetched on demand during this
brief drafting per Path A discipline (the Confluence anonymous-access
wall is not blocking these pages).

This is contract work, not implementation. The brief locks call
signatures, data shapes, staleness and unavailability signals,
error semantics, and cadence targets. It does not lock module file
structure, internal class hierarchy, library choices, or threading
model — those are Code's calls when the brief executes. The
versioned-contract framing from §1.1 of the scope document applies:
v1.0 is contract shape and discipline locked, not feature-complete
field set; backward-compatible additions land via §2.7's API
contract versioning discipline.

`betfair_client` carries three responsibilities in scope for v1.0:

- **Streaming pricing reads** — subscribe to Betfair's Stream API
  for live exchange data (prices, market depth, traded volumes,
  market state, BSP reconciliation). Feeds the racing page, sports
  page, and burst-review live displays.
- **REST order placement** — place, cancel, replace, and update
  orders on the Betfair Exchange. Called by v3's bet-entry flow.
- **REST order state reads** — read current and cleared orders for
  reconciliation, settlement, and position tracking. Called by v3's
  settlement flow and Burst Review.

Out of scope for v1.0: any soft-book equivalent (that's `softbook_
client` per §2.5); bet record schema fields stored at placement
(§2.8); settlement triggers and Burst Review surfacing (§2.6 racing
path, §B.1.4 sports path); analytical reads of any kind (those go
through `vps_client`).


## 2. Module shape

`betfair_client` is v3's single integration point with the Betfair
Exchange. One module, one connection surface to Betfair, one place
where Betfair-side concerns live in the codebase.

The single-integration-point discipline is direct from DR-028 (the
cross-database integration boundary discipline decision: no caching,
no denormalisation, no second integration point). DR-028 was
authored for the cross-database boundary between `capture.db` and
v3's operational store, but the underlying principle — one place
owns each external surface — applies equally to v3's connection to
Betfair. There is no parallel client elsewhere in v3 that talks to
Betfair directly. Code that needs Betfair data goes through
`betfair_client`.

### 2.1 Parallel module structure

`betfair_client` sits alongside two siblings, each owning a
different external surface:

- **`vps_client`** — v3's interface to the analytical layer
  (`capture.db` on the VPS). Periodic-only reads per §2.3.
  Backward-looking analytical work.
- **`betfair_client`** — v3's interface to Betfair. Streaming
  pricing reads, REST order placement, REST order state reads.
  Live decision support.
- **`softbook_client`** — v3's interface to the soft-book
  operational layer per §2.5. Source-flexible (manual entry day-one,
  vendor implementation later). Live soft-book pricing and bet
  entry.

The three clients are independent. They do not call each other.
They expose data upward to v3's consumer code (racing page, sports
page, burst-review workflow, bet-entry flow, settlement flow), which
stitches the three sources at the v3 consumer surface, not inside
any client.

### 2.2 Boundaries `betfair_client` owns

Inside `betfair_client`:

- The TCP/SSL Stream API connection, its authentication, its
  subscription state, its reconnection logic.
- The internal cache that holds the live market and order state
  (built from initial images plus deltas per the Stream API
  protocol).
- The HTTP REST connection to Betfair's Betting API endpoints
  (placement, cancel, replace, update, current orders, cleared
  orders, market book reads with order projections).
- Authentication session lifecycle (login, keepAlive, INVALID_
  SESSION recovery).
- Rate-limit and data-limit awareness — the module enforces Betfair's
  call-rate ceilings and request-weight ceilings before sending,
  surfacing back-pressure to consumers rather than blindly
  forwarding.
- Currency translation between Stream API GBP and account-currency
  AUD where needed (per §16 of this brief).
- Error mapping — translating Betfair's error codes into v3-side
  signals (recoverable vs surface-to-operator vs reconnect vs fail).

Outside `betfair_client`:

- v3's own bet record (lives in v3's operational store; bet record
  shape is §2.8's concern).
- Settlement decisions (live in v3's settlement flow, which calls
  `betfair_client` for order state but owns the finalised vs
  provisional logic per §2.6).
- The racing page and sports page UI rendering (consume
  `betfair_client`'s outputs but render in v3's frontend).
- Account selection, persona routing, soft-book parallel — none
  pass through `betfair_client`.

### 2.3 Versioned contract

Per §1.1 of the scope document, `betfair_client`'s contract is
versioned. v1.0 locks call signatures, returned data shapes,
staleness and unavailability signals, and error semantics for the
three responsibilities named above. Backward-compatible additions
(new fields on returned shapes, new optional parameters on calls,
new methods that don't break existing ones) land in-place against
v1.0. Breaking changes — any change that would break a current
consumer — only land via a new version (v1.1, v2.0 per §2.7's
discipline).

The contract documentation lives with `betfair_client`, not
scattered across v3's consumer modules. Schema-drift surfaces in
one file when Betfair changes something upstream — not across v3's
codebase.


## 3. Connection management — Streaming

The Streaming connection is a long-lived authenticated TCP/SSL
socket to Betfair, kept open across the v3 session lifetime.
Reconnection on drop is automatic, transparent to consumers, and
state-preserving where possible.

### 3.1 Endpoint

Production: `stream-api.betfair.com:443`.

The Australian Betting API REST endpoint (`api.betfair.com.au`)
applies to the REST surface only. The Stream API endpoint is the
same global address regardless of account jurisdiction.

A pre-production integration endpoint exists
(`stream-api-integration.betfair.com`) for testing. v3 uses
production exclusively in operational deployment; integration
endpoint use is a Code-side concern only if test infrastructure is
ever added (currently parked per the named-debt list at DR-029
close).

### 3.2 Connection lifecycle

Five states `betfair_client` tracks for the Streaming connection:

- **DISCONNECTED** — no socket open, no authentication, no
  subscription. Initial state on module startup.
- **CONNECTING** — TCP/SSL handshake in progress.
- **AUTHENTICATING** — connection open, authentication message sent,
  awaiting StatusMessage. Per the Stream API protocol, the first
  message after connect must be authentication; if no message is
  sent within 15 seconds, Betfair closes with TIMEOUT.
- **SUBSCRIBED** — connection open, authenticated, subscriptions
  active, receiving change messages and heartbeats. The steady-state
  operational mode.
- **RECONNECTING** — connection lost, awaiting back-off interval
  before retry. State-preservation tokens (`initialClk`, `clk`) held
  for the resubscribe attempt.

State transitions are internal to `betfair_client`. Consumers see
either "data available" (current cache state) or "data unavailable"
(staleness signal) — they don't see the underlying connection state
machine.

### 3.3 The 15-second authentication rule

Betfair closes the connection with `TIMEOUT` if no message is sent
within 15 seconds of connect. `betfair_client`'s connect path sends
authentication immediately on socket open — no waiting for consumer
calls, no lazy authentication. This is non-negotiable; the rule
exists at Betfair's side and bypassing it would mean every fresh
connection drops itself.

### 3.4 Reconnection on drop

When the Streaming connection drops (which it will — Betfair's docs
explicitly state long-lived connections cannot be guaranteed),
`betfair_client` follows this sequence:

1. Detect the drop. Two detection paths: (a) socket-level error or
   close, (b) heartbeat-loss — no message of any kind received for
   2× the negotiated `heartbeatMs` interval (per the Stream API
   reference's stream-health guidance).
2. Mark the connection RECONNECTING. Surface staleness to consumers
   immediately — current cache contents are now stale-as-of the
   drop time, not stale-as-of-now.
3. Wait the back-off interval (see §3.5).
4. Open a fresh TCP/SSL connection.
5. Authenticate (as per §3.3).
6. Resubscribe with the stored `initialClk` and `clk` tokens, using
   identical subscription criteria to the previous subscription.
   This is what triggers Betfair to send `RESUB_DELTA` (a patch to
   bring the cache forward) rather than a fresh `SUB_IMAGE` (a full
   replacement).
7. Apply the `RESUB_DELTA` to the cache. Mark connection SUBSCRIBED.
   Clear the staleness signal.

If resubscribe fails (e.g. `INVALID_CLOCK` because the stored tokens
are stale, or subscription criteria are no longer valid),
`betfair_client` falls back to a fresh `SUB_IMAGE` — full cache
replacement — rather than retrying the resubscribe.

### 3.5 Back-off discipline

Reconnection back-off is bounded-exponential: 1 second, 2 seconds,
4 seconds, 8 seconds, capped at 30 seconds, then constant 30-second
intervals indefinitely. Reset to 1 second on successful reconnect.

The cap exists because indefinite exponential growth would mean
hours-long gaps after sustained outage, which is operationally
unacceptable; the floor (1 second initial) avoids hammering Betfair
on transient drops.

Sustained reconnection failure (e.g. five or more consecutive
failed reconnects, or any single reconnect attempt that fails with
an authentication or authorisation error) surfaces to v3's
operator-facing logs immediately, not silently. Operator may need
to act (renew session token, check Betfair API status page,
investigate network).

### 3.6 Connection per process

One Streaming connection per v3 process. v3's Streaming-consuming
code (racing page, sports page, burst-review workflow) reads from
`betfair_client`'s in-process cache, not from a fresh connection.
Multiple subscriptions on a single connection are supported by the
Stream API; multiple connections from a single account are
discouraged (per `MAX_CONNECTION_LIMIT_EXCEEDED` semantics) and
unnecessary for v3's operational scale.

If v3 ever splits into multiple processes that each need Betfair
streaming data, the canonical fix is one connection per process
with its own `betfair_client` instance — not multiplexing one
connection across processes. Out of scope for v1.0.


## 4. Authentication

`betfair_client` holds one authenticated session at a time, used
across both the Streaming connection and the REST surface. The
session is created via Betfair's login API, refreshed proactively
via `keepAlive`, and recovered automatically on
`INVALID_SESSION_INFORMATION`.

### 4.1 What authentication consists of

Two pieces of credential material are required for every Betfair
API call (Streaming or REST):

- **Application key** — identifies the application (v3) to Betfair.
  Static, set by operator via developer console once per
  application. Lives in operator-side configuration.
- **Session token** — identifies the logged-in account session.
  Dynamic, generated via the login API, expires 12 hours after
  issue on `.com.au` accounts (Italian/Spanish jurisdictions:
  20 minutes after issue, not applicable to v3). Session expiry is
  on absolute timeout — API activity does **not** extend the
  session. Only `keepAlive` resets the timer.

Both are required on every request. The application key is sent
directly; the session token is sent in the `X-Authentication`
header (REST) or in the AuthenticationMessage (Streaming).

### 4.2 Where credentials live

Credentials live in operator-side configuration outside the
codebase. v3 reads them at startup from a local config source
(file, environment variable, secrets manager — Code's call when
the brief executes). Credentials are never logged, never written
to disk inside `betfair_client`, never exposed in error messages,
never returned to consumers.

The brief does not specify which config source to use; that's an
operator decision in the deployment environment. The brief locks
that credentials are read once at startup, held in `betfair_client`'s
memory only, and refreshed in memory only.

### 4.3 Login flow

`betfair_client` performs login once at startup:

1. Call Betfair's login endpoint with username, password, and
   application key.
2. Receive a session token.
3. Store the token in memory.
4. Mark the session active.

Login uses the certificate-based interactive login endpoint where
operator credentials require it (per Betfair's documented login
options). The brief does not lock which login flow (interactive
vs non-interactive) to use; that's a Code-side call based on the
operator's account configuration.

### 4.4 Session lifecycle and `keepAlive`

A Betfair session token expires 12 hours after issue on `.com` /
`.com.au` accounts (20 minutes on Italian/Spanish jurisdictions —
not applicable to v3's AU operation). Session time is **not**
extended by ordinary API activity; only `keepAlive` resets the
timer. This is the corrected framing — earlier Betfair documentation
described expiry as "12 hours of inactivity" which referred to a
now-deprecated codepath. v3 reasons about `keepAlive` cadence
against absolute-timeout semantics.

`betfair_client` calls `keepAlive` proactively on a 4-hour cadence
while the session is active. The 4-hour cadence is well inside the
12-hour absolute-timeout window with substantial margin, so a single
missed `keepAlive` round (e.g. transient network failure) does not
risk session expiry. `keepAlive` is cheap — a single REST call with
no body — so the cost of being proactive is trivial against the
cost of mid-session expiry.

If `keepAlive` fails (returns an error, or the session is reported
expired), `betfair_client` falls back to a fresh login per §4.3.

### 4.5 Login rate limit discipline

Betfair limits successful logins to 100 per minute per account; on
breach, the account is locked out for 20 minutes. `betfair_client`'s
login path enforces this with a hard floor: no more than one login
attempt per second from a single `betfair_client` instance, and no
more than 10 login attempts in any rolling 5-minute window. These
floors are well inside Betfair's ceilings — the goal is to make it
structurally impossible for `betfair_client` to trigger the
lockout, not to optimise login speed.

If the floors are hit, `betfair_client` waits before retrying. If
the lockout is somehow triggered (e.g. operator running multiple
v3 processes, or a credential misconfiguration triggering rapid
login failures), `betfair_client` surfaces the lockout to
operator-facing logs immediately and stops attempting login until
the 20-minute window passes. The error code Betfair returns on
lockout is `TEMPORARY_BAN_TOO_MANY_REQUESTS`.

**Existing sessions are unaffected by the lockout.** Per Betfair's
session management documentation, the 20-minute window blocks fresh
login attempts only — any session token issued before the lockout
remains valid for the rest of its 12-hour absolute window. A v3
process whose initial login was successful continues operating
normally even if a separate process triggers the lockout. This
matters operationally: a misconfigured restart loop in one v3
process does not take down a sibling v3 process holding a valid
session.

### 4.6 INVALID_SESSION recovery

If any API call (Streaming or REST) returns `INVALID_SESSION_
INFORMATION` or `NO_SESSION`, `betfair_client` treats this as a
session-expired condition:

1. Mark the current session expired.
2. Trigger a fresh login per §4.3 (subject to the rate-limit
   floors in §4.5).
3. On successful login, retry the failed call once with the new
   token.
4. If the retry also fails with a session error, surface to
   operator-facing logs and stop — this indicates a deeper problem
   (credentials wrong, account suspended, etc.) that won't resolve
   via retry.

This recovery path is invisible to consumers in the success case
— they see the call complete, slightly slower than usual but
correctly. In the failure case, they see a structured error
("authentication failed, operator action required") rather than a
raw Betfair error code.

### 4.7 Streaming and REST share one session

The same session token is used for both surfaces. When `betfair_
client` refreshes its session (proactive `keepAlive` or recovery
from `INVALID_SESSION`), the new token applies to both surfaces.
Streaming reconnects after a session refresh use the new token in
their AuthenticationMessage; REST calls use it in the next
request's header.

There is no design that would have separate sessions for the two
surfaces. One session, one source of truth for "is `betfair_client`
authenticated right now."

## 5. Subscription patterns — market data

`betfair_client` subscribes to the Stream API to receive live
market data — prices, depth, traded volumes, market state — for
the markets v3 cares about. Subscription shape determines what
v3 sees and at what cost.

### 5.1 Coarse over fine-grain

Betfair's documented best practice is to prefer coarse-grain
subscriptions (subscribe to a super-set of markets you care about)
over fine-grain (subscribe to specific market IDs). The reasoning:
fine-grain subscriptions force frequent subscription changes as
markets are added or removed from the operator's view, and each
subscription change re-sends the initial image, which is the
expensive part of the protocol.

`betfair_client` subscribes coarse. Two market subscriptions in
total, both maintained for the v3 process lifetime:

- **Racing subscription.** All Australian thoroughbred, harness, and
  greyhound WIN and PLACE markets, filtered by `eventTypeIds=["7"]`
  (Horse Racing) plus `eventTypeIds=["4339"]` (Greyhound Racing),
  `countryCodes=["AU"]`, `marketTypes=["WIN","PLACE"]`. Race-type
  scoping (Flat, Harness, Steeple, Hurdle) is not applied at
  subscription time — Betfair's `raceTypes` filter is available, but
  applying it at subscription locks out late-listed markets where
  race-type metadata hasn't yet been written. v3 filters by race
  type at the consumer surface using `MarketDefinition.raceType`
  instead.
- **Sports subscription.** AFL and NRL fixtures, filtered by
  `eventTypeIds` covering those competitions. Specific eventTypeId
  lookup is Code's call at execution (Betfair's `listEventTypes`
  REST call returns the canonical list). Market scope: at minimum
  `MATCH_ODDS`, plus the handicap and total markets v3's sports
  page uses for line-typed bet entry. Sub-markets (player props,
  SGM) are out of scope per §B.1.6 of `architecture.md` (specialist
  markets parked for v3.1+). Sports subscription scope is read-only
  for in-play markets — placement on in-play sport is prohibited
  under AU regulation (see §9.5.1).

### 5.2 Data filter — the field flags

The Stream API's market data filter controls which fields the
subscription receives, with each flag adding cost (initial image
size, message rate, message payload size). `betfair_client`'s
subscription enables only the flags v3 actively consumes.

For racing:

- **`EX_BEST_OFFERS_DISP`** — best back/lay prices including virtual
  bets, depth controlled by `ladderLevels`. Virtual bets matter
  because they reflect what a bet at advertised odds would actually
  match against (per Betfair's cross-matching). v3's racing page
  shows top-of-book prices; this is the load-bearing flag for that
  display.
- **`EX_LTP`** — last traded price. Useful as a sanity check against
  the best back/lay (large gap = thin market, late drift, or
  similar) and for the Top Fluc / Best of Best price-uplift logic
  in Strategy 2.
- **`EX_MARKET_DEF`** — market definition (status, in-play flag,
  BSP-reconciled flag, race type, venue, country, regulators,
  number of active runners, scheduled start time, etc.). Required
  for v3 to know whether a market is OPEN, SUSPENDED, or CLOSED,
  whether BSP has reconciled, and the race-level metadata v3
  filters on at the consumer surface.
- **`SP_PROJECTED`** — Betfair SP near and far projections.
  Operationally relevant for the racing page's "where SP is heading"
  display and for analytical hand-off (the BSP value before
  reconciliation).

`ladderLevels` is set to **3** for racing — top three prices on
each side. Three is enough for the racing page's display
(operationally, only the top price matters for bet entry; the
second and third give visual context on market depth) and keeps
the initial image small.

For sports:

- **`EX_BEST_OFFERS_DISP`** — same rationale as racing.
- **`EX_LTP`** — same rationale as racing.
- **`EX_MARKET_DEF`** — same rationale as racing, plus sports-
  specific fields (in-play status, bet delay, key-line definition
  for handicap markets).

Sports `ladderLevels` also **3**.

Flags v3 does *not* enable at subscription time:

- **`EX_ALL_OFFERS`** — full ladder. Heavy. v3 doesn't need it for
  operational decisions; analytical needs go through `capture.db`,
  not the operational stream. EX_LADDER entitlement is a separate
  open question (per `external_api_resources.md` §1.5); even if
  entitlement is granted, full ladder is not enabled by default.
- **`EX_TRADED`** / **`EX_TRADED_VOL`** — full traded ladder and
  market/runner traded volume. Analytical territory. Not enabled
  operationally.
- **`SP_TRADED`** — starting price ladder. Same — analytical, not
  operational.
- **`EX_BEST_OFFERS`** (non-virtual) — `_DISP` (with virtual) is
  what matches actual operator-facing prices, so non-virtual is
  not enabled.

### 5.3 Subscription parameters

`segmentationEnabled=true`. Always. Segmented messages outperform
non-segmented for initial images, which is the dominant cost in the
protocol. Cost is zero, benefit is non-zero, no reason not to.

`heartbeatMs=5000` — 5-second heartbeat. Betfair bounds-checks to
500–5000ms; 5000ms is the upper bound and the conservative choice
(fewer heartbeats means less message volume; the 5-second window is
short enough that a stale connection is detected within ~10 seconds
per the 2× rule in §3.4). If `betfair_client`'s heartbeat-loss
detection ever needs to fire faster (e.g. burst-window scenarios
where 10-second detection is too slow), the cadence can be tightened
in a backward-compatible v1.1 — for v1.0, 5000ms is correct.

`conflateMs=0` — no conflation requested. v3 wants every change as
it happens; conflation deliberately drops or merges updates, which
trades latency for bandwidth in a way that doesn't fit operational
live pricing. Note that Betfair may force conflation if v3's
account is on a Delayed App Key (the field returns 180000 in that
case per the Stream API reference) — `betfair_client` reads the
returned `conflateMs` value on subscription confirmation and surfaces
it to operator-facing logs if non-zero, since that indicates a
delayed-app-key configuration that may not be intended.

`marketIds` is not set on either subscription — coarse-grain via
the filters above is the whole point.

### 5.4 Subscription lifecycle

Subscriptions are sent immediately after authentication completes
on each fresh connection. Both subscriptions (racing and sports)
are sent in parallel — the Stream API supports multiple
subscriptions on a single connection, and they run independently.

Each subscription has its own `id` (a unique sequence per
RequestMessage per the Stream API protocol) and its own
`initialClk`/`clk` token pair. `betfair_client` stores the tokens
per-subscription; reconnection resubscribes both with their
respective tokens.

Subscription criteria are constant for the v3 process lifetime —
v3 does not dynamically change which races or sports it cares
about. Late-listed markets (per the §2.1 finding that 71 Betfair
WIN markets vs 106 active races at one point) are caught by the
coarse filter automatically; markets that disappear (scratched,
abandoned) generate `MarketDefinition` updates with status changes
that consumers see through the cache.


## 6. Subscription patterns — order data

`betfair_client` subscribes to the Stream API's order stream as
well as the market stream, with the same authenticated connection.
The order stream pushes updates whenever any of v3's bets change
state — placement confirmations, partial matches, full matches,
cancellations, lapses, voids, and reductions from runner removals.

### 6.1 Why order streaming, not REST polling

v3 could in principle poll `listCurrentOrders` periodically for the
same information. Order streaming is preferred because:

- **Latency.** Order streaming pushes state changes within
  sub-second of the event. Polling at safe intervals (per Betfair's
  rate limits) is multi-second. For burst-window decisions where
  the operator needs to know whether a bet just matched before
  placing a follow-up, push beats poll.
- **Rate-limit cost.** `listCurrentOrders` shares a 3-concurrent-
  request rate-limit pool with `listMarketBook`-with-order-projection
  and `listMarketProfitAndLoss`. Polling order state would consume
  that budget against the same operator's bet placement and
  settlement reads.
- **Coverage.** Order streaming sends transient `EXECUTION_COMPLETE`
  states when a bet transitions from EXECUTABLE to EC, which polling
  can miss if the transition happens between polls.

REST `listCurrentOrders` and `listClearedOrders` are used by
`betfair_client` for reconciliation and settlement reads (§7), not
for live state tracking. The two surfaces are complementary, not
redundant.

### 6.2 Subscription shape

One order subscription per `betfair_client` instance, established
immediately after authentication and after the market subscriptions
(§5.4).

The order subscription's `orderFilter` parameters:

- **`includeOverallPosition=true`** — return the net matched
  position per runner (`OrderRunnerChange.mb` and `.ml` — matched
  backs and lays at distinct price points). This is the
  position-tracking data v3 uses for settlement reconciliation and
  for the burst-review workflow's "what's my live exposure on this
  runner" display.
- **`partitionMatchedByStrategyRef=false`** — v3 day-one does not
  use `customerStrategyRef` to partition position views per
  strategy. The four racing strategies are operator-side concepts;
  Betfair-side strategy partitioning would be useful for analytical
  attribution (which strategy generated which P&L) but is downstream
  of v3 day-one. Backward-compatible v1.1 addition if needed.
- **`customerStrategyRefs`** — not set. Day-one. Pairs with the
  partitioning flag above.
- **`segmentationEnabled=true`** — same rationale as market
  subscriptions. Always on.

### 6.3 What v3 stores on bets and what `customerOrderRef` carries

Per §2.8 (bet-schema reframing), v3's bet record carries the Betfair
identifiers needed to find the bet on Betfair's side:
`betfair_market_id`, `betfair_selection_id`, and the Betfair-side
bet ID returned at placement.

`betfair_client` sets `customerOrderRef` on every placement to v3's
internal bet record ID. This is v3's identifier round-tripping
through Betfair — when the order stream sends an update on that
bet, the `rfo` field on the unmatched-order record carries v3's bet
record ID, and `betfair_client` matches it back to v3's bet without
needing to look up by Betfair bet ID first.

`betfair_client` also sets `customerRef` (the request-level
parameter, distinct from `customerOrderRef` — see §14.2) on every
`placeOrders` call to a v3-generated value. The `customerRef` is
the load-bearing field for Betfair's 60-second placement de-dup
window and is the actual safety net for retry-on-timeout. v3
caches the `customerRef` alongside the in-flight bet record at
click time so the same value can be reused on retry; full reuse
discipline is in §14.2.

`customerStrategyRef` is set to the racing strategy number ("1",
"2", "3", "4") at placement, even though v3 day-one doesn't filter
or partition on it. Setting it costs nothing at placement time and
makes future analytical work (per-strategy P&L from Betfair-side
data) backward-compatible without re-quering historical bets.

### 6.4 What the order stream cache holds

`betfair_client`'s order-stream cache is keyed by
(`market_id`, `selection_id`) and holds:

- **Unmatched orders (`uo`)** — every EXECUTABLE order on the
  runner with its current price, original size, size matched, size
  remaining, side, persistence type, placement timestamp,
  `customerOrderRef`, `customerStrategyRef`.
- **Matched position (`mb` and `ml`)** — net matched position by
  distinct price point on each side. This is the rolled-up view
  across all the operator's matched orders on the runner.

When an order transitions from EXECUTABLE to EXECUTION_COMPLETE,
Betfair sends the transient EC state once and then the order
disappears from `uo`. `betfair_client` removes it from the
unmatched cache on receipt of the EC state and updates the matched
position from the `mb`/`ml` deltas in the same message.

EXECUTION_COMPLETE orders are not held in the streaming cache
beyond that transient — for full-detail reads on completed orders
(e.g. settlement reconciliation), `betfair_client` calls REST
`listCurrentOrders` or `listClearedOrders` (per §7).

### 6.5 What the order stream cache exposes upward

Three reads `betfair_client` exposes to v3 consumers based on the
order-stream cache:

- **Get unmatched orders for a runner** — used by the racing page
  and sports page to show "you have an open back at $4.20 for $50"
  alongside the live market.
- **Get net matched position for a runner** — used by the
  burst-review workflow's exposure display and by the bet-entry
  flow's "you already have $X matched on this runner" sanity
  check before placing a follow-up.
- **Get all unmatched orders across all markets** — used by the
  open-orders view (operator's overall live exposure) and by the
  stale-order detection logic (any unmatched orders on markets
  that have moved to SUSPENDED or CLOSED).

All three reads return what's in the cache as of the most recent
update. Staleness signalling (§3.4) applies — if the connection is
in RECONNECTING state, the cache is marked stale and consumers see
the staleness alongside the data.

### 6.6 Reconciliation pattern with REST

The order stream is the live state. REST `listCurrentOrders` is the
reconciliation source.

On v3 startup, before opening the Streaming connection,
`betfair_client` calls `listCurrentOrders` once to get the current
EXECUTABLE order state. This is the cold-start image. Once
Streaming is connected and the order subscription returns its
`SUB_IMAGE`, `betfair_client` reconciles the two — the Streaming
image is canonical (it's what Betfair considers current right now),
the REST cold-start image is checked against it for any drift.

Drift between the two on cold start indicates an edge case (e.g. an
order changed state between the REST call and the Stream subscription
landing). Surface to operator-facing logs but proceed with the
Streaming image as truth.

During steady-state operation, REST `listCurrentOrders` is not
called. Streaming is the source of live state. REST is used only
for cold start and for `listClearedOrders` reads against settled
orders (§7).


## 7. Message handling and cache shape

`betfair_client` maintains an in-process cache of live market and
order state, populated by the Streaming connection's initial images
and updated by deltas. The cache is what v3's consumers read from
— consumers do not see raw Stream API messages, do not parse JSON,
do not track sequence tokens.

### 7.1 Two caches, one connection

The Streaming connection carries two independent message streams:

- **Market stream** (`op=mcm`) — feeds the **market cache**,
  populated by the racing and sports market subscriptions (§5).
- **Order stream** (`op=ocm`) — feeds the **order cache**, populated
  by the order subscription (§6).

The two caches are independent. Market changes don't trigger order
cache updates and vice versa. They share connection state (one
connection, one authentication, one heartbeat) but maintain
separate data and separate `initialClk` / `clk` token pairs.

### 7.2 Market cache shape

Keyed by `marketId`. For each market, the cache holds:

- **Market definition** — status (OPEN / SUSPENDED / CLOSED),
  in-play flag, BSP-reconciled flag, race type, venue, country,
  market type, scheduled start time, betDelay, regulators, number
  of active runners, complete flag, all the fields from Stream
  API's `MarketDefinition`.
- **Per-runner data**, keyed by `selectionId`:
  - **Runner definition** — status (ACTIVE / WINNER / LOSER /
    REMOVED / etc.), name, sortPriority, handicap, BSP, removal
    date and adjustment factor (if removed).
  - **Best back/lay ladder** — top 3 prices on each side from
    `EX_BEST_OFFERS_DISP` (per §5.2), keyed by level (0, 1, 2),
    each level holding price and size.
  - **Last traded price** — single price from `EX_LTP`.
  - **SP near/far projections** — single price each from
    `SP_PROJECTED`.
  - **Total runner traded volume** — single number from runner-level
    `tv`.
- **Total market traded volume** — single number from market-level
  `tv`.

Fields that aren't subscribed to (full ladder, traded ladder, SP
ladder) are simply absent from the cache. Consumers that ask for
them get a clear "not available" signal rather than null or zero.

### 7.3 Order cache shape

Keyed by (`marketId`, `selectionId`). For each runner the operator
has any position on, the cache holds:

- **Unmatched orders** — list of EXECUTABLE orders, each with order
  ID, price, original size, size matched, size remaining, side,
  persistence type, order type, placement timestamp,
  `customerOrderRef`, `customerStrategyRef`. Full per-order detail.
- **Matched backs** (`mb`) — keyed by price, size matched at that
  price (rolled up across all matched orders on the back side at
  that price).
- **Matched lays** (`ml`) — same shape, lay side.

### 7.4 Building the market cache from messages

Three message types update the market cache:

- **`SUB_IMAGE`** — initial image. On receipt, `betfair_client`
  replaces the entire market cache with the contents of the image.
  Triggered on subscription, on resubscribe with stale tokens, or
  on rare market-level snapshot during steady-state operation
  (where the message carries `img=true` per market or runner).
- **`RESUB_DELTA`** — patch on resubscribe. Apply as deltas against
  the existing cache. Markets in the patch with `img=true` are
  replaced wholesale; otherwise individual fields update per the
  delta semantics in §7.5.
- **Update messages (no `ct` set)** — steady-state deltas. Apply
  per §7.5.

The market cache is multi-segment safe. Segmented messages
(`SEG_START`, `SEG`, `SEG_END`) are accumulated until the segment
chain completes; cache application happens on segment-end, not
per-segment. This avoids consumers seeing half-applied images
during the segmentation window.

### 7.5 Delta semantics — ladders

Level / depth-based ladders (`bdatb`, `bdatl`, `batb`, `batl`)
arrive as `[level, price, size]` triples:

- `[0, 1.20, 50]` — set level 0 (top of book) to price 1.20 with
  size 50. Replaces whatever was previously at level 0.
- `[1, 1.21, 30]` — set level 1 to 1.21 with size 30.
- `[0, 1.20, 0]` — remove level 0 (the size went to zero).
  Subsequent levels shift up by Betfair's send convention; the
  message will include explicit updates to the new level
  positions.

`betfair_client` applies these as direct level replacements. It
does not infer what should happen at unstated levels — Betfair
sends explicit updates at every level that changed (per the Stream
API reference's "you'll never have to assume").

Price-point ladders (`atb`, `atl`, `trd`, `spb`, `spl`) arrive as
`[price, size]` tuples and follow the same insert / update / remove
semantics keyed by price rather than level. `betfair_client` does
not subscribe to these for v1.0 (per §5.2's field-flag selection),
so the cache shape doesn't include them — but the protocol handling
is named here for completeness.

Single-value fields (`ltp`, `tv`, `spn`, `spf`) arrive as direct
replacements. If the field is null in the message, the field hasn't
changed — the cached value is preserved, not cleared. Per the Stream
API's "values sent are nullable & are not sent if they are not
changed."

### 7.6 Building the order cache from messages

Two message-level concepts apply to the order cache:

- **`fullImage=true` at market level** — replace the cache entry
  for that market wholesale. Used on cold-start and on rare order-
  cache snapshots.
- **`fullImage=true` at runner level** — replace the cache entry
  for that (market, runner) wholesale. Used when Betfair re-syncs
  a single runner.

Without `fullImage`, the message is a delta:

- **Unmatched order changes (`uo`)** — each order in the delta is
  replaced wholesale (orders are sent in full on change, not as
  partial deltas). Order ID is the key. Orders not in the delta
  are unchanged in the cache. Orders that have transitioned to
  EXECUTION_COMPLETE arrive in the delta with their EC state, and
  `betfair_client` removes them from the unmatched cache after
  applying any final size updates.
- **Matched changes (`mb`, `ml`)** — same `[price, size]` semantics
  as market-cache price-point ladders. `size=0` removes the price
  point from the matched view.

When a market's `fullImage=true` arrives with an empty body (no
orders, no matched), this signals v3 has no remaining position on
that market — the cache entry for the market is removed.

### 7.7 What consumers see

`betfair_client` exposes typed read methods upward, not raw cache
access. The methods follow the pattern: "tell me the current state
of X." Consumers do not see Stream API field names. They do not
need to know about deltas, segments, or sequence tokens.

Read methods include (illustrative — Code finalises signatures
when implementing):

- **Market state by `marketId`** — returns market definition fields
  in v3-side vocabulary (status as enum, in-play boolean, BSP
  reconciled boolean, scheduled start time as datetime, etc.) plus
  a staleness flag and a last-update timestamp.
- **Runner state by `(marketId, selectionId)`** — returns runner
  definition fields, top-of-book back/lay prices and sizes, last
  traded price, SP near/far projections.
- **Best back / best lay shortcut by `(marketId, selectionId)`** —
  the most-frequent operational read. Returns just the level-0
  back price, level-0 back size, level-0 lay price, level-0 lay
  size. Convenience over the full runner-state read.
- **My unmatched orders by `(marketId, selectionId)`** — returns
  the list of unmatched orders from the order cache, with v3-side
  field names.
- **My net matched position by `(marketId, selectionId)`** —
  returns matched-back ladder and matched-lay ladder.
- **My all-unmatched-orders** — across all markets, returns the
  unmatched view from the order cache.

Each read returns data plus a staleness signal. Staleness is set
when the connection is in RECONNECTING state, when the most recent
heartbeat is overdue, or when the consumer-supplied tolerance (an
optional argument like `max_age_ms`) is breached.

### 7.8 Staleness signalling — explicit, not inferred

When the connection drops or heartbeats stop arriving,
`betfair_client` does not return last-known cache contents
silently. The staleness signal is structured:

- **Fresh** — connection SUBSCRIBED, heartbeats current, cache
  applied to the last received message. Consumer-supplied
  `max_age_ms` not breached.
- **Stale** — connection RECONNECTING, or heartbeats overdue (no
  message of any kind for 2× `heartbeatMs`), or `max_age_ms`
  breached. Cache contents returned alongside the stale flag.
  Consumer decides whether stale data is acceptable for the
  decision at hand.
- **Unavailable** — connection sustainedly failed (e.g. five
  consecutive failed reconnects per §3.5), or never connected.
  No cache contents returned. Consumer must decide what to do.

The three states are explicit. There is no silent fallback from
fresh to stale — consumers always know which they're getting. This
matches §2.3's "explicit staleness or unavailability signals — not
silent fallbacks, not stale data dressed up as fresh."

### 7.9 Concurrency and threading

The Streaming connection runs on a dedicated I/O thread inside
`betfair_client`. Cache updates happen on that thread. Consumer
reads happen on whichever thread v3's calling code lives on
(racing page rendering, bet-entry flow, etc.).

The cache is read-many, write-one — many consumers can read at
once, only the I/O thread writes. Read-write coordination is via
read-write locks or copy-on-write structures (Code's call when the
brief executes). The contract upward is that read methods are
thread-safe; consumers can call them from any thread without
coordination.

`betfair_client` does not expose the I/O thread upward. Consumers
do not interact with it.



## 8. Reconnection and resubscription

The Streaming connection drops periodically — Betfair's
documentation explicitly does not guarantee long-lived connections,
and operational reality across v2 confirms drops happen on the
order of a few times per day. `betfair_client`'s reconnection
behaviour is the difference between "drops are invisible to the
operator" and "drops cause cascading data gaps that surface in bet
entry."

This section specifies the full reconnection flow. The connection
state machine itself is in §3 (CONNECTING / AUTHENTICATING /
SUBSCRIBED / RECONNECTING / DISCONNECTED). What's specified here:
the resubscription protocol, the token discipline, and the failure-
mode behaviours.

### 8.1 The two-token discipline

The Stream API gives `betfair_client` two sequence tokens for each
subscription:

- **`initialClk`** — sent once on the initial image. Marks the
  position of the initial cache state.
- **`clk`** — sent on every non-heartbeat message after the initial
  image (or on every SEG_END for segmented messages). Marks the
  position of each delta.

`betfair_client` stores both tokens per-subscription (one pair for
the racing market subscription, one pair for the sports market
subscription, one pair for the order subscription). On every
non-null `clk` received, the stored value updates to the new one.
`initialClk` updates only when a fresh `SUB_IMAGE` arrives.

The tokens are opaque to `betfair_client` — they're not parsed or
decoded, just stored and replayed. Their job is to let Betfair
work out how far the client got and patch from there on resubscribe.

### 8.2 Resubscribe with stored tokens — the happy path

When the connection drops and reconnection succeeds (per §3
sequence: detect drop → mark RECONNECTING → wait back-off → fresh
TCP/SSL → authenticate), `betfair_client` resubscribes:

1. For each subscription (racing market, sports market, order),
   send the SubscriptionMessage with the stored `initialClk` and
   `clk` tokens, using **identical** subscription criteria to the
   original subscription. The Stream API requires identical
   criteria for resubscribe — different criteria gets treated as a
   fresh subscription.
2. Receive a `RESUB_DELTA` from Betfair — the patch needed to bring
   the local cache forward from where the tokens say it was to
   where the live state actually is.
3. Apply the `RESUB_DELTA` to the cache. Some markets in the patch
   may carry `img=true` indicating they're either new since the
   drop or can't be patched cleanly — for those, replace the cache
   entry wholesale per the §7.4 image-handling rules.
4. Receive new `initialClk` (if the resubscribe response carried
   one) and start receiving `clk` updates as steady-state messages
   resume.
5. Mark the connection SUBSCRIBED. Clear the staleness flag from
   read methods.

Steady-state operation resumes. Consumers see continuous data with
a brief stale window during the drop and reconnect.

### 8.3 Fall back to fresh image — the unhappy path

Resubscribe with stored tokens can fail in two ways:

- **`INVALID_CLOCK`** — Betfair's StatusMessage rejection. Tokens
  are too stale (typical when reconnect takes more than a few
  minutes) or otherwise invalid.
- **Subscription criteria mismatch** — vanishingly unlikely in
  v3's design (criteria are constant for the process lifetime),
  but possible if v3's configuration changes between drop and
  reconnect.

On either failure, `betfair_client` falls back to a fresh
subscription: send the SubscriptionMessage **without** `initialClk`
and `clk`. Betfair responds with a fresh `SUB_IMAGE`. Apply per
§7.4 — wholesale cache replacement.

The fall-back is not graceful for consumers — there's a window
where the cache is empty between the failed resubscribe and the
applied SUB_IMAGE. But it's correct: stale data dressed up as
fresh would be operationally worse than a brief unavailability
window. The staleness signal stays asserted through the fall-back
window.

### 8.4 Cold start

When v3 starts up, `betfair_client` opens its connection, authenti-
cates, and subscribes from scratch — no stored tokens, fresh
SUB_IMAGE for each subscription. Cold start is the same path as
the post-`INVALID_CLOCK` fall-back: subscribe without tokens,
receive fresh image, apply.

The order subscription cold start is paired with a REST
`listCurrentOrders` reconciliation per §6.6. Market subscription
cold starts have no equivalent reconciliation — Streaming is the
only source for live market state.

### 8.5 Stream API status field — `503` vs disconnect

The Stream API includes a `status` field on every change message
and heartbeat. Two values:

- **`null` / not present** — stream data is up to date.
- **`503`** — downstream Betfair services are experiencing
  latency. Stream data may be incomplete or delayed but the
  connection itself is healthy and messages are still arriving.

Per the Stream API reference's explicit guidance: clients should
**not** disconnect on `503`. The connection is fine; the data is
degraded. When Betfair recovers, updates resume containing the
latest data.

`betfair_client` treats `503` as a degraded-data signal, not a
connection signal:

- Cache continues to apply incoming messages (they're still
  meaningful, just possibly behind real-time).
- Staleness signalling is asserted on read methods — consumers see
  "data is degraded, possibly stale by an unknown amount" rather
  than fresh.
- Logs the `503` to operator-facing logs on first occurrence within
  a session and on transition back to `null`. Avoids log-flooding
  during sustained `503` periods (a single sustained 503 would
  produce many messages).
- Does not trigger reconnection. The connection is fine.

When `503` clears (next message arrives with `status=null`), the
staleness flag clears and consumers see fresh again.

### 8.6 Heartbeat-loss detection

Heartbeats are the connection's health signal. With `heartbeatMs=
5000` (per §5.3), `betfair_client` expects at least one message —
either a heartbeat or a real change message — every 5 seconds per
subscription.

Detection rule (per the Stream API reference): if no message of any
kind arrives for **2× `heartbeatMs`** (10 seconds at the configured
cadence), the connection is presumed dead. `betfair_client` closes
the socket and enters RECONNECTING per §3.4.

This catches connection deaths that don't surface as TCP errors
(e.g. silent network partitions, NAT timeouts, intermediary firewall
drops). Without the heartbeat-loss check, those conditions would
leave `betfair_client` holding a dead socket indefinitely.

The 2× rule is a margin for jitter — a single missed heartbeat
might be transient network delay; two consecutive misses signals
something's structurally wrong.

### 8.7 Sustained reconnection failure

Most reconnects succeed within seconds. When they don't,
`betfair_client` escalates:

- **5 consecutive failed reconnect attempts** — the connection has
  been failing for at least ~30 seconds (per the back-off cap of 30
  seconds at the upper bound). `betfair_client` logs a
  sustained-failure event to operator-facing logs and continues
  retrying at the 30-second cap indefinitely. Read methods surface
  unavailability (not just staleness) at this point — cache
  contents are too old to be useful.
- **Authentication failure during reconnect** — e.g. session
  expired and re-login also failed (per §4.6's session recovery
  failing through). `betfair_client` stops attempting reconnect,
  surfaces "authentication failed, operator action required" to
  operator-facing logs, and waits for operator intervention. The
  cache is marked unavailable; v3 cannot use Betfair-direct data
  until the operator resolves the auth issue.

Both escalation paths surface to operator-facing logs visibly —
this is the kind of failure that needs operator awareness, not
silent retries that bury the symptom.

### 8.8 Per-subscription independence

The three subscriptions (racing market, sports market, order) each
maintain their own `initialClk` / `clk` token pair. On reconnect,
they resubscribe independently — racing might successfully resume
with `RESUB_DELTA` while sports falls back to fresh SUB_IMAGE if
sports tokens are stale (unlikely but possible).

Cache state for each subscription is independent. Failure on one
subscription does not invalidate the other two's caches.
Reconnection happens at the connection level (one connection serves
all three subscriptions); subscription-level resubscribe happens
per-subscription within the reconnected connection.


## 9. Order placement — REST endpoints

`betfair_client` places, cancels, replaces, and updates orders via
Betfair's REST Betting API. The Streaming connection (§5–§8) is
read-only — it pushes state changes from Betfair to v3, but does
not accept order instructions. Placement and management always
goes through REST.

### 9.1 REST endpoint and surface

Australian-account endpoint: `https://api.betfair.com.au/exchange/
betting/`. Two interfaces are available — JSON-RPC at
`/exchange/betting/json-rpc/v1` (note hyphen) and JSON REST at
`/exchange/betting/rest/v1.0/`.

`betfair_client` uses **JSON-RPC** for all calls. Two reasons:

- JSON-RPC supports batched calls in a single HTTP request (multiple
  `<method>` calls in one array). REST requires one HTTP request
  per call. Batching is operationally useful for placing multiple
  bets in a single round-trip.
- JSON-RPC is the more commonly-documented surface in Betfair's
  reference material and sample code. Drift risk is lower.

The JSON-RPC method prefix is `SportsAPING/v1.0/<method>` for
Betting API operations, `AccountAPING/v1.0/<method>` for the
Accounts API.

Headers on every request:

- `X-Application: <appKey>` — the application key from §4.
- `X-Authentication: <sessionToken>` — the current session token.
- `Accept-Encoding: gzip, deflate` — per Betfair's best-practice
  guidance for response compression.
- `Connection: keep-alive` — persistent connection, reducing
  per-request handshake latency. Note: idle keep-alive connections
  are closed by Betfair every 3 minutes per the Best Practice page,
  so `betfair_client` does not assume the connection lives forever
  — TCP-level reconnection is automatic per the HTTP client used.
- `Content-Type: application/json`.

### 9.2 The four placement-side operations

`betfair_client` exposes four placement-side calls upward, each
mapping to a Betfair REST operation:

- **Place** — `placeOrders`. Submit one or more new orders to a
  market. Each order specifies side (BACK / LAY), size, price,
  order type (LIMIT / LIMIT_ON_CLOSE / MARKET_ON_CLOSE),
  persistence type (LAPSE / PERSIST / MARKET_ON_CLOSE),
  `customerOrderRef` (set per §6.3), `customerStrategyRef` (set per
  §6.3).
- **Cancel** — `cancelOrders`. Cancel one or more unmatched orders
  on a market. Each instruction specifies the bet ID and optionally
  a size to cancel (partial cancel). Bets that are fully matched
  cannot be cancelled.
- **Replace** — `replaceOrders`. Cancel an existing unmatched order
  and immediately place a new order at a different price, in a
  single atomic operation. Used when the operator wants to move a
  pending bet to a different price without losing queue position
  to a separate-cancel-then-place sequence.
- **Update** — `updateOrders`. Change the persistence type of an
  unmatched order (LAPSE → PERSIST or vice versa). Does not change
  price or size — just whether the order survives turn-in-play.

Each operation accepts a list of instructions in a single call
against a single `marketId`. Multiple markets in one call requires
multiple calls (or one batched JSON-RPC request with multiple
operations).

### 9.3 Place, cancel, replace, update — call shape

For each of the four operations, `betfair_client` exposes a typed
method upward. Consumers pass v3-side concepts (a bet record, a
runner reference, a price, a size); `betfair_client` translates to
Betfair JSON-RPC shape, sends the request, parses the response,
maps Betfair-side identifiers and statuses back to v3-side return
shapes.

The contract:

- Consumer passes v3-side data — never raw Betfair JSON.
- Method returns a v3-side result shape — never raw Betfair
  response. Includes the Betfair bet ID for successful placements
  (so v3 can store it on the bet record per §2.8), the
  `customerOrderRef` echo (so v3 can confirm round-trip), and the
  per-instruction status.
- On any failure (network error, Betfair API error, partial
  success), the method returns a structured result with the
  per-instruction outcome. Successful instructions are not rolled
  back if other instructions in the same call fail — Betfair's
  semantics are per-instruction.

### 9.4 The `customerOrderRef` round-trip

Per §6.3, every placement carries `customerOrderRef` set to v3's
internal bet record ID. The round-trip:

1. v3's bet-entry flow creates a bet record locally with a unique
   ID, marks it as "pending placement."
2. `betfair_client` sends `placeOrders` with `customerOrderRef`
   set to the v3 bet record ID.
3. Betfair returns the placement response with the Betfair bet ID
   and the `customerOrderRef` echoed back.
4. v3 stores the Betfair bet ID on the bet record. The bet record
   moves to "placed" state.
5. The order subscription's stream message for the bet (when
   matched, partially matched, cancelled, etc.) carries
   `customerOrderRef` = v3 bet record ID, so `betfair_client` can
   route the stream update to the right v3 bet without needing to
   look up by Betfair bet ID first.

This means v3's bet record ID is the join key between v3's
operational store and Betfair-side state, even before the Betfair
bet ID lands. Failure modes (placement timeout where v3 doesn't
know if Betfair received the order) are handled by reconciliation
— v3 calls `listCurrentOrders` filtered on the `customerOrderRef`
to discover whether the placement landed.

Note that every `placeOrders` call also carries `customerRef` —
the request-level de-dup parameter, distinct from
`customerOrderRef`. See §14.2 for the de-dup mechanics and the
retry-safety discipline; this section covers only the round-trip
identity role of `customerOrderRef`.

### 9.5 In-play bet delay handling

Markets that turn in-play apply a `betDelay` (in seconds) to
incoming orders. The order is held by Betfair for `betDelay`
seconds before being submitted into the matcher. The delay is
visible on `MarketDefinition.betDelay` once the market is in-play.

`betfair_client` does not impose any v3-side timing on top of
Betfair's bet delay. The placement call sends the order;
Betfair handles the delay; the order stream surfaces the order's
state once it's matched, lapsed, or cancelled. v3's bet-entry
flow sees a slight delay between placement and confirmation when
in-play, which matches the user-facing timing operators are used
to.

The `betDelayModels` field (PASSIVE / DYNAMIC) per the Stream API
reference's MarketDefinition documentation:

- **PASSIVE** — `betDelay > 0` but orders that won't match
  immediately bypass the delay. Applies broadly to in-play markets.
  No special handling — `betfair_client` sends the order, Betfair
  decides whether to apply the delay.
- **DYNAMIC** — Tennis markets only currently. Delay varies by game
  state. Sports v1.0 day-one is AFL and NRL (per §5.1), so DYNAMIC
  doesn't apply. Backward-compatible v1.1 if tennis is added.

### 9.5.1 Australian regulatory constraint on in-play sport placement

Australian regulation (Interactive Gambling Act 2001) prohibits online in-play
sport bet placement via any channel except telephone. Per Betfair's developer
support documentation: *"Australian customers cannot place in-play bets on sport
via any channel, including the API, except by telephone."* The constraint applies
to AFL, NRL, and all sports other than racing. **Racing in-play placement
(thoroughbred, harness, greyhound) remains permitted via the API for AU accounts**
— the §9.5 bet-delay logic above continues to apply unchanged for racing.

The operator's current strategy mix does not engage in-play sports placement —
Strategy 3 (Correlated Friction, AFL/NRL SGM bonus-back) is pre-jump only, and
Strategies 1, 2, 4 are racing-focused. This constraint is therefore preventive
rather than active for v3 day-one. It is locked here so v3-side bet-entry holds
the discipline regardless of future code paths or strategy evolution.

**v3-side discipline:**

- Sports-page bet-entry disables placement once the cached
  `MarketDefinition.inplay` flag flips to `true` for any sports market. The flag
  is the canonical signal; v3 reads it from the market cache rather than
  inferring from `betDelay > 0`.
- Sports subscription scope (MATCH_ODDS plus handicap/total per §5.1) remains
  unchanged — read-only display of in-play sports markets is permitted, only
  placement is restricted.
- The §9.5 PASSIVE/DYNAMIC `betDelay` discussion remains relevant only for
  racing day-one. Reads of in-play sports markets continue to surface `betDelay`
  values; v3 displays them but does not act on them for sports placement.

**Failure mode if discipline breaks:** a placement attempted in-play on sport
would be regulator-rejected by Betfair, not by `betfair_client`. The rejection
class is regulatory, not ordinary lapse — handled at §15.4's error surface as a
hard rejection that should not auto-retry. Defence-in-depth: even if `betfair_
client` issued such a call, Betfair's rejection prevents the placement from
landing.

**Future-state opening:** the operator has not ruled out in-play sport placement
permanently — a phone-channel route exists, and regulatory landscape can shift.
If in-play sport placement enters scope in v3.1+, this constraint relaxes via
explicit DR rather than silent discipline drift. Today's v3 holds the line.

### 9.6 Persistence types

The `persistenceType` field on an order controls what happens at
turn-in-play:

- **LAPSE** — the unmatched portion is cancelled when the market
  goes in-play. Used when the operator does not want pre-jump
  price exposure to survive into in-play markets (which reprice on
  race events the pre-jump model didn't anticipate).
- **PERSIST** — the unmatched portion remains active in-play.
  Per the on-disk Betting Enums reference: *"Once in play, the
  bet won't be cancelled by Betfair if a material event takes
  place."* This is non-trivial in-play exposure — a bet placed
  PERSIST that survives into in-play is subject to Betfair's
  bet-delay (per §9.5) and remains live regardless of how the race
  unfolds during the unmatched portion's lifetime.
- **MARKET_ON_CLOSE** (`MOC`) — bet is matched at BSP regardless
  of pre-jump matching. The price field is ignored; size acts as
  a stake. Used for BSP-targeted bets.

`betfair_client` exposes persistence type as a typed parameter on
the placement method. v3's bet-entry flow chooses based on the
operator's intent.

**Day-one default is PERSIST.** The operator's day-one Betfair
flow is dominated by free-bet matching cycles where pre-jump price
exposure surviving into in-play is operationally desirable — the
free bet's value is realised when the unmatched portion eventually
matches, even if that's after turn-in-play. The bet-entry surface
exposes LAPSE as a per-bet override at logging time so the
operator can flip on a per-bet basis when intent differs. The
default may be revisited as the strategy mix shifts away from
free-bet-matching dominance and other persistence shapes (LAPSE
for clean pre-jump-only exposure on Strategy 1/2/4; MARKET_ON_CLOSE
for explicit BSP targeting) become more common.

### 9.7 The placement rate limits

Three rate limits apply to placement-side operations:

- **1000 transactions per second per account** — across `placeOrders`,
  `cancelOrders`, `replaceOrders`, `updateOrders` combined, counting
  individual instructions (not requests). A `placeOrders` call with
  10 instructions counts as 10 transactions. Exceeding this returns
  TOO_MANY_REQUESTS. v3's operational scale (single-operator manual
  bet entry plus modest automated flows) is many orders of magnitude
  below this — not a concern for v1.0 but `betfair_client` enforces
  awareness defensively per §11.
- **3 concurrent requests** for `listMarketBook` with order/match
  projection, `listCurrentOrders`, `listMarketProfitAndLoss` —
  applies to read-side operations, not placement. Covered in §11.
- **General TOO_MANY_REQUESTS** for sustained burst patterns —
  `betfair_client`'s rate-limit awareness (§11) applies a soft
  ceiling well below Betfair's hard ceiling.

### 9.8 Idempotency and placement retry semantics

Placement is **not** idempotent at the network layer. If a placement
request times out and `betfair_client` retries, the retry is a
fresh placement — Betfair has no concept of "this is the same order
I tried to send before."

Two protections against duplicate placement:

- **`customerOrderRef` uniqueness check.** Before retrying a timed-
  out placement, `betfair_client` calls `listCurrentOrders` filtered
  on the `customerOrderRef` of the failed call. If an order with
  that ref exists, the original placement landed — no retry. If no
  order with that ref exists, the placement did not land — retry is
  safe.
- **Single-retry policy.** `betfair_client` retries a timed-out
  placement at most once. After that, the placement is surfaced as
  failed to v3's bet-entry flow; the operator decides whether to
  re-attempt manually. Repeated automated retries on placement are
  high-risk — they risk duplicate bets — and aren't worth the
  operational saving.

Cancel, replace, and update operations are idempotent at the bet-ID
level — they reference an existing bet ID, and "cancel an order
that's already cancelled" is a no-op rather than a duplicate
action. Retry semantics for those operations are simpler — a single
retry on timeout is safe.

### 9.9 Order placement failures — Lapse Status Reason Codes

When an order lapses (gets removed by Betfair without matching),
the order stream message carries a Lapse Status Reason Code (`lsrc`
field). The full catalogue is in the Stream API reference (§7.5
Lapse codes); the operationally-meaningful ones for v3:

- **`MKT_SUSPENDED`** — market was suspended at the time the bet
  came to be matched. Common at jump time.
- **`MKT_UNKNOWN`** — market was removed between bet placement and
  matching. Rare; typically means the market closed/abandoned.
- **`RNR_UNKNOWN`** — runner was removed between bet placement and
  matching. Common when a horse is scratched after the bet but
  before the off.
- **`PRICE_INVALID`** — bet price outside the defined ladder. Should
  not happen in v3 — `betfair_client`'s placement method validates
  prices against the ladder client-side before sending.
- **`TIME_ELAPSED`** — bet waited too long in queue, lapsed for
  safety. Edge case.
- **`PRICE_IMP_TOO_LARGE`** — when matched, the available price was
  better than the bet's best-permitted price (suggests a major
  market movement). Edge case.

`betfair_client` surfaces lapse codes upward to v3's bet-entry
flow with v3-side semantics — "your bet on Greeks Princess at
$4.20 lapsed because the market suspended" — not raw Betfair
codes. Operator-facing messages are constructed from the lapse
code plus the bet record context.


## 10. Order state reads — REST endpoints

The order stream (§6) is `betfair_client`'s primary source for live
order state. REST order-state reads are the secondary source, used
where Streaming doesn't fit — cold-start reconciliation, historical
settlement reads, full-detail lookups on completed orders.

This section specifies what REST reads `betfair_client` makes,
when, and how the results combine with the streaming cache.

### 10.1 The three REST read operations

`betfair_client` uses three Betting API operations for order state:

- **`listCurrentOrders`** — returns currently active orders
  (EXECUTABLE) and recently completed orders (EXECUTION_COMPLETE
  within the last few hours). Used for cold-start reconciliation
  (§6.6) and for `customerOrderRef` round-trip recovery (§9.8).
- **`listClearedOrders`** — returns settled orders from the cleared
  history. Settled means the market has closed and the order has
  resolved (won, lost, voided, lapsed). Used for settlement reads
  and historical position reconstruction.
- **`listMarketBook` with order projections** — returns market
  state plus the operator's matched/unmatched position on the
  market in a single call. Used in narrow cases where v3 needs
  market data and order data atomically together; otherwise the
  Streaming caches handle this without REST.

### 10.2 When `listCurrentOrders` is called

Three operational cases:

- **Cold start.** `betfair_client` calls `listCurrentOrders` once
  at startup, before opening the Streaming connection (per §6.6).
  Returns the current EXECUTABLE order set. The result populates a
  cold-start cache that's reconciled against the Streaming
  SUB_IMAGE when it arrives. Filter: no filter — the operator's
  full account scope.
- **`customerOrderRef` round-trip recovery.** When a placement
  request times out (per §9.8), `betfair_client` calls
  `listCurrentOrders` filtered on the `customerOrderRef` of the
  failed placement to discover whether the order landed. Filter:
  `customerOrderRefs=[<ref>]`.
- **Operator-initiated reconciliation.** Burst Review or a manual
  reconciliation flow may request a fresh REST read against the
  current order state to compare with the streaming cache. Surfaces
  drift if any. Operator-side trigger, not automatic.

In all three cases, REST is the source of truth at the moment of
the call, but steady-state operations continue to read from the
streaming cache. REST is not used for routine reads.

### 10.3 When `listClearedOrders` is called

Settlement-side reads. After a market closes:

- **Per-market settlement read.** When v3's settlement flow needs to
  finalise a bet record, `betfair_client` calls `listClearedOrders`
  filtered on the bet's market ID and the operator's account scope.
  Returns the settled order detail: matched price, matched size,
  profit/loss, settlement timestamp.
- **Daily settlement reconciliation (optional, post-DR-029).** A
  daily sweep that pulls the prior day's cleared orders for cross-
  checking against v3's local bet records. Useful as a defensive
  reconciliation but not gating for v1.0. Backward-compatible v1.1
  addition.

`listClearedOrders` has an independent rate-limit pool (per the
Stream API reference's TOO_MANY_REQUESTS notes — `listClearedOrders`
does not contend with `listCurrentOrders` / `listMarketBook` /
`listMarketProfitAndLoss`). Settlement reads can run alongside
operational reads without rate-limit contention.

### 10.4 When `listMarketBook` with order projection is used

Narrowly. Most read use cases are served by either the streaming
market cache (live prices) or the streaming order cache (live
position) without REST. `listMarketBook` with `orderProjection` is
useful in two specific cases:

- **Pre-Streaming sanity reads.** Before subscribing to a market
  (e.g. when adding a market to v3's watch set ad-hoc), one REST
  call returns market state plus position state in a single round-
  trip. Faster than waiting for the subscription's SUB_IMAGE.
- **Atomic snapshot for Burst Review.** When the burst-review
  workflow needs a single moment-in-time consistent view of market
  + own position, one REST call beats two cache reads that might
  apply at slightly different times.

Both cases are bounded — not high-frequency. `betfair_client`
defaults to the streaming cache; the REST path is the exception
not the rule.

The rate-limit cost is significant (per §11) — `listMarketBook` with
order or match projection counts against the 3-concurrent rate-
limit pool. `betfair_client`'s rate-limit awareness (§11) applies.

### 10.5 Cold-start reconciliation flow

The cold-start reconciliation pattern, complete:

1. v3 startup begins.
2. `betfair_client` initialises. Authentication completes.
3. `betfair_client` calls `listCurrentOrders` — returns current
   EXECUTABLE order set. Stored as the cold-start image.
4. `betfair_client` opens the Streaming connection. Authenticates.
5. Subscribes to the market and order streams. SUB_IMAGE messages
   arrive.
6. The order stream's SUB_IMAGE is canonical for live state.
   `betfair_client` reconciles cold-start image against
   SUB_IMAGE:
   - Orders in both — match. Streaming wins on any field
     differences (Streaming is more recent).
   - Orders in cold-start image only, not in SUB_IMAGE — likely
     transitioned to EXECUTION_COMPLETE between the REST call and
     the Stream subscription. Surface to operator-facing logs (mild
     diagnostic). Drop from cache (the Streaming view is canonical).
   - Orders in SUB_IMAGE only, not in cold-start image — placed
     between the REST call and Stream subscription. Add to cache.
     Surface to operator-facing logs (mild diagnostic).
7. The streaming cache is now the source of truth. Cold-start
   image is discarded.
8. v3's cold-start sequence completes; the racing page and sports
   page can begin reading from `betfair_client`.

The cold-start window between steps 3 and 6 is small (typically
under a second). Reconciliation is defensive — most cold starts
will see zero drift between the two images.

### 10.6 What the REST read methods expose upward

`betfair_client` exposes typed methods, not raw REST responses.
Same pattern as the streaming cache reads (§7.7):

- **Get current orders** (across all markets, or filtered by market
  / runner / `customerOrderRef`). Returns a list of orders in v3-
  side shape with v3-side field names.
- **Get cleared orders for a market** — returns settled order
  detail in v3-side shape. Used by settlement.
- **Get atomic market + position snapshot** — returns a combined
  view of market state and own position. Used narrowly per §10.4.

Each method internally handles the REST call shape, error mapping,
rate-limit waiting (per §11), and response parsing. Consumers see
v3-side data only.

### 10.7 Pagination and partial returns

`listCurrentOrders` and `listClearedOrders` paginate via `fromRecord`
/ `recordCount` parameters when result sets exceed a single page
(default 1000 records per page). `betfair_client` handles
pagination internally — calls `listClearedOrders` repeatedly with
incremented `fromRecord` until all pages are returned, then
returns the full result list to the consumer.

Default page size is 1000 (Betfair's documented maximum). The
operational scale of v3's settlement reads is well within a single
page for routine cases — pagination matters only for large-window
historical reads.

### 10.8 Streaming-vs-REST consistency

The streaming and REST surfaces show the same underlying order
state from Betfair's side, but there's a small consistency window
between when an event happens and when each surface reflects it.

`betfair_client`'s discipline:

- **Streaming is canonical for live state.** Routine reads always
  go through the streaming cache, never REST.
- **REST is canonical for closed/settled state** (via
  `listClearedOrders`). Streaming carries transient EC notifications
  but doesn't retain settled order detail.
- **When the two disagree on a live order**, Streaming wins —
  Streaming is push-based and reflects the most recent event.

Drift between the two on the same live order is rare — both
surfaces feed from the same Betfair backend. When it surfaces, the
discipline above resolves it without consumer involvement.

## 11. Rate-limit and data-limit handling

Two surfaces carry rate and data limits: REST and Streaming. They are independent and
have different failure modes. v3 must handle both inside `betfair_client` so consumer
code (the racing page, sports page, burst-review surface, settlement reconciliation)
never has to reason about Betfair quotas directly.

This section names the limits, names the failure response v3 takes for each, and locks
the discipline that keeps v3 below the quotas without over-engineering.

### 11.1 Streaming-side limits

The Streaming connection carries three limit shapes.

**Connection count.** Each app key has a maximum allowed simultaneous connection count.
Exceeding it returns `MAX_CONNECTION_LIMIT_EXCEEDED` on the authentication response and
closes the connection. v3 runs one connection per process (per Section 3 — connection
management); the design carries no risk of breaching this on its own, but session
restarts with stale connections still counted are a real failure mode. Mitigation: on
authentication, the response carries `connectionsAvailable` (the number of *additional*
connections the account can open). v3 logs this on every authentication, and surfaces a
warning when it drops to zero on a fresh authentication — that's the signature of stale
connections from a previous run that didn't close cleanly.

**Market subscription count.** A single subscription can name up to 200 markets by
default. Exceeding it returns `SUBSCRIPTION_LIMIT_EXCEEDED`. Notably, this is the only
error that does *not* close the connection — the connection stays up and v3 can re-send
a smaller subscription. v3's market-subscription pattern (per Section 5 — coarse over
fine-grain) subscribes by event-type and country code rather than by market id, so the
200-market limit is enforced server-side by the filter rather than approached by v3
listing market ids one at a time. The headline risk is a marketFilter that resolves to
more than 200 markets — e.g. AU thoroughbred + harness + greyhound on a heavy Saturday
afternoon. Mitigation: `betfair_client` catches `SUBSCRIPTION_LIMIT_EXCEEDED`, logs the
filter that triggered it, and falls back to a tighter filter (per-code subscriptions
instead of all-codes, or per-state subscriptions instead of country-wide) deterministically
rather than failing. The fallback shape is fixed in code, not negotiated at runtime.

**Connection-rate / authentication-rate.** Repeatedly opening connections or
re-authenticating in rapid succession returns `TOO_MANY_REQUESTS`. Connection-level
back-off (per Section 3) handles this — v3's bounded exponential back-off on reconnect
already prevents the loop that would trigger it. Named here for completeness.

### 11.2 REST-side data-weight limit (`listMarketBook` / `listRunnerBook` /
        `listMarketCatalogue` / `listMarketProfitandLoss`)

The REST market-data endpoints enforce a **data-weight budget per request**:
sum(weight) * number_of_market_ids must not exceed 200 points

Exceeding it returns `TOO_MUCH_DATA`. The weights are documented in the
`market_data_request_limits.md` reference page on disk; the load-bearing numbers for v3:

- `EX_BEST_OFFERS` weight 5 → 40 markets per request maximum.
- `EX_ALL_OFFERS` weight 17 → 11 markets per request maximum.
- `EX_BEST_OFFERS + EX_TRADED` weight 20 (combination is *not* the sum of individuals)
  → 10 markets per request maximum.
- `EX_ALL_OFFERS + EX_TRADED` weight 32 → 6 markets per request maximum.
- `SP_TRADED` weight 7 → 28 markets per request maximum.
- `SP_AVAILABLE` weight 3 → 66 markets per request maximum.
- `EX_BEST_OFFERS` with `exBestOffersOverrides` requesting depth 6 → weight becomes
  `5 * (6/3) = 10` → 20 markets per request.

v3's REST market-data calls happen in three places (per Section 10 — order state reads —
and the per-market reachability checks): cold-start order reconciliation,
reconciliation-after-Streaming-gap, and operational ad-hoc market lookups. None of these
naturally batch beyond 5–10 markets, so the 200-point ceiling is not a binding constraint
in normal operation. **The discipline is to never let consumer code pass an unbounded
market-id list straight through to a REST call.** `betfair_client` enforces a hard
ceiling per call (10 markets at `EX_BEST_OFFERS + EX_TRADED`, 6 at `EX_ALL_OFFERS +
EX_TRADED`) and chunks the request internally if the consumer hands it more.

### 11.3 REST-side instruction-count limits (placement / cancel / replace)

Per the on-disk `placeOrders.md`, `cancelOrders.md`, and `replaceOrders.md` reference
pages:

- `placeOrders` — maximum **200 instructions per request**.
- `cancelOrders` — maximum **60 instructions per request**.
- `replaceOrders` — maximum **60 instructions per request** (matches cancel).

v3 day-one places one bet at a time from the racing-page / sports-page entry surface, so
the 200-instruction limit on `placeOrders` is not a binding constraint operationally.
The 60-instruction limit on `cancelOrders` becomes relevant only if v3 ever supports
mass-cancel (e.g. "cancel all my unmatched on this market") — which is not day-one
scope. `betfair_client` enforces the limits as a defensive ceiling regardless, so a
future caller can't accidentally violate them.

### 11.4 REST-side login-rate limit

Per the on-disk `best_practice.md` reference page: **if login limits are exceeded, the
account is automatically prevented from making further login requests for 20 minutes.
Existing sessions remain valid during the lockout.** The exact threshold is not
published. v3's login pattern (per Section 4 — authentication) is one login per process
start, with `keepAlive` calls every 4 hours to extend the 24-hour window — login rate is
structurally low. The risk surface is restart loops or process-supervisor misconfiguration
that re-authenticates on every error. Mitigation: the canonical login-attempt floors
are locked in §4.5 (no more than one attempt per second from a single `betfair_client`
instance, and no more than 10 attempts in any rolling 5-minute window). On top of those
floors, `betfair_client` escalates to operator-visible alert if a third login attempt
is required within 10 minutes — that pattern signals a restart-loop or credential
problem rather than ordinary session expiry, and surfaces the issue before it
approaches the 5-minute floor.

### 11.5 REST-side transaction-charge consideration

Betfair charges customers for transactions above a threshold per market settlement
(documented on the operator-side Betfair Charges page, not in the developer docs). v3
does not pay transaction charges in normal operation — promotional and value-betting
flow stays well below the threshold. Named here because it interacts with placement
discipline:

- **Prefer leaving an order in place rather than cancelling and re-placing.** This is
  documented Betfair Best Practice — staying in queue position matters for matching
  speed, and cancel-and-replace inflates the transaction count toward the charging
  threshold. v3's placement code path follows this; `replaceOrders` is preferred over
  `cancelOrders` followed by `placeOrders` for price corrections, and `updateOrders` is
  preferred for persistence-flag corrections (per Section 9). Transaction charges are an
  operator concern at the account level, not a `betfair_client` concern.

### 11.6 HTTP transport defaults

Per the on-disk `best_practice.md` reference page, three transport defaults reduce
latency and avoid known failure modes:

- **`Accept-Encoding: gzip, deflate`** — REST responses can be many KB; compression is
  recommended on every request.
- **`Connection: keep-alive`** — persistent connection reduces per-request setup
  latency. Note: idle keep-alive connections are closed every 3 minutes by Betfair; v3's
  HTTP client must handle silent connection close and re-establish on the next request.
- **No `Expect: 100-Continue` header** — sending it returns HTTP 417 from Betfair. v3's
  HTTP client explicitly suppresses this header. This is a known .NET-environment
  default that doesn't apply directly to a Python client, but the suppression discipline
  is the same — never send the header, regardless of platform.

### 11.7 Streaming-side slow-consumer behaviour (cousin of rate-limiting)

Streaming does not throttle the publisher to match the consumer. If v3 reads from the
socket buffer slower than Betfair publishes, Betfair *conflates* updates — multiple
ChangeMessages collapsed into one, with `con=true` set on the resulting message.

This is not a rate-limit error; it's a graceful degradation. But it is a fitness signal
for the operational line: a `con=true` ChangeMessage means v3 is not consuming fast
enough, and the operational cadence promised by the Streaming subscription is degraded.

**Discipline:**

- The dedicated I/O thread (per Section 7 — message handling) reads the socket buffer
  on a tight loop; consumer reads are off the cache (thread-safe), not off the socket
  directly.
- `betfair_client` exposes `con=true` as an operational fitness signal alongside
  `status: 503` and heartbeat-loss (per Section 8 — reconnection and resubscription, and
  Section 15 — error handling and stream health). Sustained `con=true` is logged and
  surfaced; it is a v3-side performance defect, not a Betfair-side issue.
- `conflateMs` on the subscription stays at `0` (no forced conflation requested) per
  Section 5 — operational use needs the publisher's natural cadence, not artificially
  slowed cadence. The Delayed App Key forces `conflateMs=180000` regardless; v3 runs on
  the Live App Key for operational reads.

### 11.8 Aggregate discipline

Six discipline points, locked:

1. Every `betfair_client` REST call computes the data-weight against the 200-point
   ceiling and chunks the request if needed. No call is allowed to exceed the ceiling
   even if a consumer hands it an oversized id list.
2. Every `betfair_client` REST placement / cancel / replace call respects the
   per-operation instruction-count ceiling (200 / 60 / 60). Defensive ceiling regardless
   of caller.
3. Authentication frequency is rate-limited at `betfair_client` to the floors locked
   in §4.5 (one attempt per second, max 10 in any rolling 5-minute window), with
   operator-visible escalation on repeated attempts within 10 minutes (per §11.4).
4. Streaming subscriptions stay below 200 markets via filter discipline (event-type +
   country code, never raw market-id lists). `SUBSCRIPTION_LIMIT_EXCEEDED` triggers
   deterministic per-code or per-state fallback.
5. HTTP transport defaults: gzip compression on every request, keep-alive on every
   request, no Expect: 100-Continue, idle-close-after-3-minutes handled silently.
6. `con=true` on a ChangeMessage is treated as a v3-side fitness signal and surfaced
   alongside status:503 and heartbeat-loss; it is not a Betfair-side error.


## 12. Cadence design — operational live pricing

This section locks the cadence v3 expects from the Streaming subscription for operational
live pricing — racing-page burst-window decisions, sports-page bet entry, and any other
surface where v3 is asking "what is the price right now" on behalf of the operator's
next action.

Cadence here means three things, named separately because they fail separately:

- **Publisher cadence** — how often Betfair sends a ChangeMessage when something has
  changed.
- **Heartbeat cadence** — how often Betfair sends an empty ChangeMessage when nothing
  has changed (proves the connection is live).
- **Consumer cadence** — how fast v3 reads the socket buffer and updates its in-process
  cache.

The three together produce the cadence the burst UI sees. If any one degrades, the
operational fitness of the line degrades — but for different reasons that need different
responses.

### 12.1 Publisher cadence — what Betfair gives us

Betfair's Stream API publishes ChangeMessages on its own internal cycle. The cadence is
not documented as a fixed number; it's "as fast as the publisher's cycle produces
material change, subject to the consumer keeping up." For AU thoroughbred WIN markets
near jump, this is observed at sub-second to ~1-second cadence on v2 today.

`conflateMs=0` on the subscription requests no forced conflation — v3 receives the
publisher's natural cadence (per Section 5 — market subscription, and §11.7). This is
the right call for operational use; the alternative (any positive conflateMs) artificially
slows the cadence in exchange for fewer wakeups, which trades operational fitness for
something v3 doesn't need.

The Delayed Application Key forces `conflateMs=180000` (3 minutes) regardless of what
the subscription requests. v3 runs operational on the Live App Key for this reason.
Dev / functional testing uses the Delayed key per Best Practice; the cadence on that key
is unfit for operational decision support and is not used for any v3 code path that
serves the burst UI.

### 12.2 Heartbeat cadence — what v3 requests

`heartbeatMs` on the subscription requests a minimum interval at which v3 receives a
ChangeMessage even if nothing has changed. The valid range is 500 to 5000 milliseconds.

v3 sets `heartbeatMs=5000` (per Section 5). Rationale:

- 5000ms is the lightest end of the heartbeat range — it minimises empty-message traffic
  on the connection while still bounding the silence period.
- Heartbeat is a connection-health signal, not a freshness signal. The freshness signal
  is the Stream API status field on every ChangeMessage (`status: 503` when downstream
  services are degraded; null when fresh). v3 reads freshness from `status`, not from
  heartbeat cadence.
- Going tighter (e.g. heartbeatMs=500) buys nothing operationally — actual price changes
  during the burst window arrive on their own cadence, faster than 5000ms. The 5000ms
  ceiling exists to bound *connection death detection*, not to bound *freshness*.

The actual heartbeat cadence used is returned on every ChangeMessage as `heartbeatMs`.
v3 logs the actual cadence at subscription start to confirm Betfair honoured the
request.

### 12.3 Consumer cadence — what v3 controls

This is the cadence v3 owns and the one that breaks first under load.

Per Section 7 (message handling), v3's `betfair_client` runs a dedicated I/O thread that
reads the SSL socket on a tight loop. The thread does three things and only three
things:

1. Read CRLF-delimited JSON message from the socket.
2. Deserialise and apply to the in-process cache (market cache or order cache,
   depending on `op`).
3. Update freshness metadata on the cache (last-message timestamp, status field, conflation
   flag).

Consumer reads from v3's racing page, sports page, or burst-review surface go against
the cache, not against the socket. The cache is updated synchronously inside the I/O
thread; reads are thread-safe and lock-free for the common case (per Section 7).

The discipline is: nothing else runs on the I/O thread. Logging, metrics, persistence,
and any other side effect that could block — all happen off-thread, fed from a
non-blocking queue. If the I/O thread blocks, the socket buffer fills, Betfair conflates
on the publisher side (`con=true`), and the operational cadence degrades.

### 12.4 The cadence the burst UI sees

The burst UI reads the cache. The freshness it sees on any read is:

- **Last-message timestamp** — when the cache was last updated for the market in
  question. Sub-second under healthy operation.
- **Status flag** — `fresh` if the most recent ChangeMessage carried `status=null`,
  `degraded` if the most recent message carried `status=503`, `stale` if no message has
  been received within 2× heartbeatMs.
- **Conflation flag** — true if the most recent ChangeMessage carried `con=true`.

The UI consumes these directly per Section 7's three-tier staleness signalling. The
cache does not extrapolate, does not interpolate, does not re-fetch from REST when stale
— it surfaces the freshness state to the UI and the UI decides what to display
(e.g. greying out the price ladder when status is degraded).

### 12.5 Cadence floor for operational fitness

Two guarantees, not one.

**Movement-cadence guarantee.** When a market is changing materially (price, depth,
total matched), v3 expects ChangeMessages to arrive sub-second on the burst window for
AU thoroughbred WIN markets. This matches v2-today behaviour. Stable markets correctly
produce no movement messages — silence is not degradation.

**Connection-liveness guarantee.** Regardless of market activity, v3 expects a
ChangeMessage of some kind (movement or heartbeat) within heartbeatMs (5000ms). Two
consecutive missed heartbeats (10s of total silence) means the connection is dead;
initiate reconnect per Section 8.

Neither guarantee is a contract Betfair publishes — both are fitness expectations.
Sustained breach is investigated; transient breach is logged and ignored.

**Sustained-degradation surfaces (unchanged from prior draft):**

- `con=true` arriving repeatedly on a single market over a 30-second window — v3-side
  consumer cadence is too slow; investigate I/O-thread contention.
- `status: 503` arriving repeatedly across multiple markets over a 30-second window —
  Betfair downstream services are degraded; surface to operator and continue.
- 10 seconds of total silence — connection is dead; reconnect.

### 12.6 What this section does not cover

Cadence near specific market state transitions (jump-time SUSPENDED → CLOSED, BSP
reconciliation, in-play turn) is the subject of Section 13 (BSP timing observation
carry-in). Cadence for placement and cancel operations (REST-side, not Streaming) is
the subject of Section 14. Error-driven cadence interruption (reconnection back-off,
heartbeat-loss escalation) is the subject of Section 15.

This section locks the *steady-state operational live pricing* cadence only.


## 13. Cadence design — BSP timing observation carry-in

This section folds the §2.1 Saturday API observation probe findings into the §2.4
Streaming spec. The probe ran REST-side polling at 1-second cadence for ten hours
across two AU thoroughbred, one harness, and one greyhound metro race (probe report at
`dr029/2_1_race_data/api_probe_report.md`). The findings transfer to Streaming because
both surfaces sit on the same publisher cycle and the same market state machine — the
probe's per-phase change rates and BSP-reconciliation timing apply to Streaming
cadence too.

What this section locks: how v3's `betfair_client` reads BSP via Streaming, when it
reads it, what gates "BSP is now safe to read", and how the per-phase cadence picture
shapes Streaming subscription discipline.

### 13.1 The BSP-reachability finding

Per probe §3.1 and §4(b), BSP (`runners[*].sp.actualSP`) is reachable on closed AU
markets across all three codes via the live API, **provided** the request includes
`SP_AVAILABLE` alongside `SP_TRADED` in the price-data projection.

Streaming-side equivalent: the Stream API's market-data filter exposes BSP via two
field flags (per the on-disk Stream API reference, Market Data Field Filtering section):

- `SP_PROJECTED` — pre-suspension projection prices (`spn` near, `spf` far).
- `SP_TRADED` — Starting Price ladder (`spb`, `spl`).

The Stream API does not have a separate `SP_AVAILABLE` flag — the equivalent shape is
delivered via `SP_TRADED`'s payload combined with the runner-definition `bsp` field
(per the RunnerDefinition Fields table). The mechanics differ from REST but the
reachability is the same: subscribe to `SP_TRADED` and `SP_PROJECTED` on the market
subscription (per Section 5), and BSP becomes available via the runner-definition's
`bsp` field once the market reconciles.

**The load-bearing point:** v3's market subscription includes `SP_TRADED` and
`SP_PROJECTED` from day one. This is locked in Section 5 already; restated here
because the probe-driven justification for why is BSP reachability.

### 13.2 The "BSP is now safe to read" gate

Per probe §4(e), `bspReconciled` (top-level MarketBook field) is **not** the BSP-
availability gate the field name suggests. It is `True` from the start of capture
through pre-jump on every snapshot — apparently signalling "BSP reconciled at the
previous market suspension" rather than "BSP is now safe to read for this market".

The empirical gate v3 uses instead:
market_status in (SUSPENDED, CLOSED) and bsp is not None and not isnan(bsp)

Streaming-side, this translates to: the market-cache's `marketDefinition.status` field
is `SUSPENDED` or `CLOSED`, and the runner-definition's `bsp` field is a positive
finite float.

**The NaN guard is not optional.** Per probe §4(d), removed runners on closed markets
carry an `sp.actualSP` *key* whose value is `NaN` (Python float, JSON-encoded as the
non-standard token `NaN` — Betfair returns it as-is). Any code reading BSP must guard
with `isinstance(value, (int, float)) and value > 0`; `value is not None` alone is
insufficient.

`betfair_client` exposes BSP through a typed accessor on the cache that applies the
gate and the NaN guard before returning. Consumer code (settlement reconciliation,
analytical write-back, racing-page display) calls the accessor; the gate is never
re-implemented at the consumer surface.

**`bspReconciled` is not used even as a secondary check.** A defensible-sounding
suggestion is to add `bspReconciled == True` as a belt-and-braces gate alongside the
empirical `market_status` + `bsp > 0` condition above. v3 declines this. The probe
established that `bspReconciled` is `True` from the start of capture through pre-jump
on every snapshot for AU thoroughbred WIN markets — using it as a secondary check
would either be a no-op (when True, which is always) or introduce a false-negative
path (if the field ever stuck False post-jump, valid BSP reads would be suppressed).
The empirical `market_status in (SUSPENDED, CLOSED) AND bsp > 0 AND not isnan(bsp)`
gate is the correct defensive pattern for AU racing and the only gate v3 implements.

### 13.3 The OPEN-but-post-jump window

The open item flagged in `current_state.md` — "open-but-post-jump BSP reachability —
`actualSP` populates 1–2 min post-jump while `market_status` still `OPEN`" — sits in
the POST_START phase. Per probe §3.1:

- **Thoroughbred POST_START** (`status=OPEN`, race running, T+0 to T+5 min): `actualSP`
  populates at 52% rate for active runners.
- **Harness POST_START**: `actualSP` populates at 61% rate for active runners.
- **Greyhound POST_START**: `actualSP` populates at **0%** — greyhound markets
  transition OPEN → SUSPENDED faster than reconciliation can complete (greyhound races
  are ~30 seconds, the OPEN-but-running window is too short).

The implication for Streaming cadence: between SUSPENDED-onset and 1–2 min before
SUSPENDED-onset (the POST_START window for thoroughbred / harness), BSP is *partially*
reachable but not gate-passing under §13.2's strict rule. v3 does not act on
partial-reconciliation BSP — settlement reconciliation, analytical write-back, and
display all wait for the full SUSPENDED gate.

This is correct rather than restrictive. The cost of acting on a partial-reconciliation
BSP value is reading a number that may still move; the cost of waiting another 1–2 min
is operationally trivial because settlement-driven actions don't compete on that
timescale.

### 13.4 The `sp` container shape-shift

Per probe §4(c), the `sp` object in API responses has different field sets pre- and
post-suspension:

- **Pre-suspension** (STANDARD / INTENSIVE / POST_START with market still OPEN):
  `sp = {nearPrice, farPrice, backStakeTaken, layLiabilityTaken}`.
- **Post-suspension** (SUSPENDED / CLOSED): `sp = {actualSP, backStakeTaken,
  layLiabilityTaken}` — `nearPrice` and `farPrice` are removed; `actualSP` is added.

Streaming-side, the field-flag separation handles this naturally: `SP_PROJECTED`
delivers `spn` / `spf` pre-suspension; `SP_TRADED` delivers `spb` / `spl` ladders
when present; the `bsp` field on the runner-definition delivers the realised BSP
post-suspension.

**v3's market cache must distinguish phase before reading the `sp`-equivalent fields.**
The cache surfaces this through three separate accessors:

- `near_price(market_id, runner_id)` — returns `spn` if pre-suspension, None
  otherwise.
- `far_price(market_id, runner_id)` — returns `spf` if pre-suspension, None
  otherwise.
- `bsp(market_id, runner_id)` — returns realised BSP if post-suspension and gate-
  passing per §13.2, None otherwise.

No single accessor returns "the SP value" without phase context; the consumer code
asks the question that matches the cache state, and the cache returns None when the
field is structurally not present.

### 13.5 Per-phase change rates and Streaming subscription cadence

Per probe §3.4, change rates per phase on REST-side 1-second polling:

| Phase       | thoroughbred | harness  | greyhound | implication for Streaming    |
|-------------|--------------|----------|-----------|------------------------------|
| STANDARD    | 1–8 %        | 2–8 %    | 0–1 %     | low publisher cadence        |
| INTENSIVE   | 40–63 %      | 47–61 %  | 40–70 %   | high publisher cadence       |
| POST_START  | 78–82 %      | 73–88 %  | 80–100 %  | very high publisher cadence  |
| SUSPENDED   | 0–13 %       | 0–12 %   | 0–1 %     | mostly silent                |
| CLOSED      | 0 %          | 0 %      | 0 %       | fully silent                 |

These rates measure how often consecutive 1-second REST snapshots differed. They are
*proxies* for Streaming cadence — a 7% change rate on REST-1s polling means the
publisher's natural cycle produced a material change in roughly 7% of 1-second
windows, so Streaming will deliver ChangeMessages at roughly that rate too.

**Implications for Streaming subscription discipline:**

- **STANDARD phase (T-60min to T-5min)** — publisher cadence is naturally low. v3's
  Streaming subscription delivers the publisher's natural rate; no cadence tuning
  needed. If `con=true` arrives during STANDARD, that's a hard v3-side signal — there's
  almost no underlying change to conflate, so any conflation is consumer-side
  back-pressure.
- **INTENSIVE phase (T-5min to T-0)** — publisher cadence is high. v3's Streaming
  subscription delivers heavy traffic. The I/O thread (per Section 7 / Section 12) must
  keep up; this is the load-bearing window for consumer-cadence fitness.
- **POST_START phase (T+0 to ~T+2min, race running)** — publisher cadence is very
  high; almost every second sees movement. `betDelay > 0` per the MarketDefinition's
  in-play marker. Streaming continues delivering through the in-play window until
  SUSPENDED-onset.
- **SUSPENDED phase (post-race, pre-settlement, ~5 min)** — publisher cadence drops to
  near-zero. Heartbeats dominate. BSP becomes gate-passing for settlement
  reconciliation per §13.2.
- **CLOSED phase (post-settlement)** — publisher cadence is zero. Heartbeats
  dominate. The market-cache entry can be evicted shortly after CLOSED-onset; v3 keeps
  it for 60 seconds post-CLOSED to allow settlement-reconciliation reads, then drops
  it.

### 13.6 Greyhound POST_START asymmetry

Per probe §3.2 and §4(i), greyhound markets transition OPEN → SUSPENDED faster than
the reconciliation window allows BSP to populate during POST_START — greyhound races
are ~30 seconds, the OPEN-but-running window is too short.

**Practical implication for Streaming:** for greyhound markets, BSP becomes gate-
passing only at SUSPENDED-onset, not in the POST_START window. v3's settlement
reconciliation timing for greyhound is consequently tighter to SUSPENDED-onset than for
thoroughbred / harness, where partial POST_START reconciliation is observable but
not gate-passing.

This is a code-specific cadence delta, not a structural Streaming difference. v3's
Streaming subscription does not differentiate by code — the same subscription delivers
all three. The differentiation happens at the consumer surface (settlement
reconciliation logic) where code-specific timing expectations are encoded.

### 13.7 The 45-minute CLOSED tail finding

v3's Streaming subscription delivers ChangeMessages throughout the full market
lifecycle — OPEN pre-jump (STANDARD + INTENSIVE phases), OPEN in-running (POST_START
phase, `inplay=true`), and SUSPENDED post-race pre-settlement. All of this is captured
into the operational cache and is available to consumer code for as long as the market
is subscribed.

Per probe §3.4 and §4(f), only the **CLOSED** phase produces zero new information
across all codes. Once a market enters CLOSED (settlement complete), `best_back/lay`,
`total_matched`, `market_status`, and even `actualSP` are immutable.

**Streaming implication:** v3 unsubscribes from a market shortly after CLOSED-onset.
The lifecycle:

1. Market subscribed when it appears in the day's race programme (typically T-60min
   or earlier, depending on subscription filter scope).
2. Subscription delivers through OPEN pre-jump → OPEN in-running → SUSPENDED. Cache
   is updated continuously.
3. CLOSED-onset detected (MarketDefinition status → `CLOSED`).
4. v3 reads BSP and any other settlement-relevant fields from the cache (per §13.2
   gate).
5. v3 holds the market in cache for 60 seconds to allow late settlement-
   reconciliation reads from consumer code.
6. After 60 seconds, the market is dropped from the active subscription's
   marketFilter — Streaming stops delivering updates for it.

This is consumer-side discipline; the Streaming subscription itself is at-most-200-
markets per Section 5, so dropping closed markets keeps the subscription fresh for
new ones to take their place across the day's race programme.

### 13.8 What this closes

Section 13 locks four design points specific to BSP timing and per-phase Streaming
cadence:

1. v3 subscribes to `SP_TRADED` and `SP_PROJECTED` on the market subscription (already
   locked in Section 5; this section gives the probe-driven justification).
2. The "BSP is safe to read" gate is `market_status in (SUSPENDED, CLOSED) AND bsp >
   0`, applied in `betfair_client`'s typed accessor; never re-implemented at consumer
   surfaces.
3. The market-cache exposes phase-aware accessors for `near_price`, `far_price`, and
   `bsp` separately — no single accessor returns "the SP value" without phase context.
4. CLOSED markets drop from the active subscription 60 seconds post-CLOSED, freeing
   subscription slots for new markets in the day's race programme.

**Open item carry-forward:** the §2.1 BSP timing observation open item ("open-but-post-
jump BSP reachability") is now substantively addressed in this section. v3 does not
act on partial POST_START reconciliation; it waits for the SUSPENDED gate. The open
item can move from `current_state.md` to "addressed in §2.4 Section 13" at brief-
assembly time.


## 14. Cadence design — placement and cancel

Placement and cancel are REST-side operations on `betfair_client`. Per Section 9 they
go through `placeOrders` / `cancelOrders` / `replaceOrders` / `updateOrders` JSON-RPC.
Per Section 10 their post-call state is observable via the Streaming order subscription
and via REST `listCurrentOrders` / `listClearedOrders`.

This section locks the timing layer between those two surfaces: how fast v3 expects a
placement to settle, what cadence the retry policy operates on, what timing constraints
in-play bet-delay imposes, and how the operator-click-to-confirmed-match closed loop
fits within the operational fitness target.

### 14.1 Latency budget for a single placement

The operator clicks "place bet" on the racing page or sports page. Between that click
and the bet appearing matched (or unmatched in queue) on the cache, v3 traverses:

1. **Pre-flight checks** (v3-internal, sub-millisecond): selection valid, price within
   ladder per the on-disk `placeOrders.md` price increment table, stake within
   minimums per currency.
2. **`placeOrders` REST call** (network + Betfair-side): typical 200–500ms in healthy
   conditions for a single instruction. The on-disk Best Practice page recommends
   gzip + keep-alive (per §11.6) which keeps this end of the range.
3. **Response parsing**: `instructionReports[0].status` is `SUCCESS` / `FAILURE`,
   `betId` returned on success, `placedDate` returned, lapse-status-reason-code
   returned if any portion lapsed.
4. **Order cache update via Streaming**: the order subscription (per Section 6)
   delivers an `OCM` message reflecting the new bet. Typical sub-second from REST
   acknowledgement.
5. **Match confirmation** (if matched immediately): order transitions
   `EXECUTABLE → EXECUTION_COMPLETE`, delivered as an order-stream transient per the
   on-disk Stream API reference's "Unmatched Orders" section. Sub-second again in
   normal market conditions.

**End-to-end budget under healthy conditions: ~1 second from click to fully matched
display, dominated by the REST round trip plus the Streaming acknowledgement.**

This is the v2-today benchmark. v3 inherits it; the architecture does not aim to beat
it materially because the REST round trip is the floor and Betfair owns it.

### 14.2 The two refs: customerOrderRef round-trip + customerRef de-dup window

Per the on-disk `placeOrders.md` reference, `placeOrders` exposes two distinct
client-supplied identifiers with different roles:

- **`customerOrderRef`** — a per-instruction field inside `PlaceInstruction`. Betfair
  echoes it back on the placement response and on every subsequent order-state read
  via `listCurrentOrders` and the order stream's `rfo` field. v3 generates one per
  placement and uses it as the load-bearing identifier for matching v3's local in-
  flight record to Betfair's bet record before `betId` is known. Limited to typical
  UUID-shaped strings.

- **`customerRef`** — a request-level top-level parameter on `placeOrders` itself
  (not inside the PlaceInstruction). Per the reference's parameters table:
  *"Optional unique string (up to 32 chars) used to de-dupe mistaken re-submissions
  ... De-duplication window is 60 seconds. This field does NOT persist into the
  placeOrders response or Order Stream API — distinct from `customerOrderRef`."*
  This is the only field with documented de-dup semantics; the corresponding error
  is `DUPLICATE_TRANSACTION` per the on-disk Betting Enums (Section 2.6).

**v3 sets BOTH on every placement.** They serve different purposes and are not
interchangeable.

**Cadence implication:** the customerOrderRef is the round-trip key for state
reconciliation; the customerRef is the idempotency safety net for retry.

- v3 generates the customerOrderRef AND a customerRef at click time and writes a
  local in-flight record keyed on the customerOrderRef.
- v3 issues `placeOrders` with both refs set.
- If the response arrives cleanly, v3 reads `betId` and links it to the in-flight
  record. The customerRef is discarded (it served its de-dup role and does not
  return).
- If the response is lost (network timeout, 502 from Betfair, etc.), v3 retries
  `placeOrders` with the **same customerOrderRef AND the same customerRef** as the
  original call. Inside Betfair's 60-second window, the customerRef de-dup engages:
  if the original landed, the retry returns `DUPLICATE_TRANSACTION` and v3 falls
  through to a `listCurrentOrders` lookup keyed on customerOrderRef to recover the
  betId. If the original didn't land, the retry places cleanly. Either way, exactly
  one bet exists at Betfair.

**The customerRef is the actual idempotency mechanism.** The `listCurrentOrders`
lookup is a soft check — useful for state reconciliation but not load-bearing for
double-place protection, because the lookup itself can race the timed-out original
(per Betfair's own "allow up to 15 seconds for a timed-out order to appear"
guidance — see §14.3).

**Crucial reuse discipline for retry safety:** the customerRef value sent on the
retry call must be byte-identical to the customerRef sent on the original call.
A re-generated customerRef on retry breaks the de-dup window and risks double-place.
v3 caches the customerRef alongside the in-flight record at click time and reuses
it on retry; the customerRef is discarded after the 60-second window closes.

This gives v3 a clean idempotency boundary: the 60-second window is the retry
window; beyond it, retry is no longer safe and v3 escalates to operator review
rather than automatic retry.

**Multi-instance precondition.** The 60-second de-dup window is keyed on the
combination of application key plus `customerRef`. v3 day-one runs as a single
process per account, so customerRef collision is impossible by construction. If a
future v3 deployment ever runs multiple processes against the same Betfair
application key (e.g. parallel v3 instances per persona, sharded operational
workloads), every customerRef value must carry an instance-unique prefix to
prevent a customerRef from one instance accidentally de-duping a legitimate
placement from another. The prefix discipline is Code's call at execution time
when multi-instance shape is locked; today it is a deferred precondition, not an
active constraint.

### 14.3 Single-retry policy on timeout

Per Section 9's "single-retry policy", v3's `betfair_client` retries a placement
exactly once on timeout, never more. The pacing:

- **Initial call** issued at click+0ms.
- **Timeout threshold**: 3000ms. Healthy `placeOrders` calls return well under 1s;
  a 3-second wait is a defensive ceiling, not an expected wait. The 3-second
  threshold sits inside Betfair's own matcher-timeout window (5 seconds, per the
  on-disk Betting Enums and Betting Exceptions reference) and inside the up-to-15-
  second window in which a timed-out order may still appear on `listCurrentOrders`.
  This means a v3-side timeout can fire while the original call is still in-flight
  at Betfair. The customerRef de-dup window (per §14.2) is what makes this safe —
  a retry inside the 60-second customerRef window cannot double-place regardless
  of whether the original eventually landed.
- **On timeout**: v3 reads `listCurrentOrders` filtered by customerOrderRef as a
  soft check to surface state earlier where possible.
  - If found: link `betId` and treat as success. No retry needed.
  - If not found: retry `placeOrders` with the same customerOrderRef AND the same
    customerRef. The customerRef de-dup window from §14.2 is the safety net; if the
    original placement does eventually land at Betfair, the retry returns
    `DUPLICATE_TRANSACTION` and v3 falls through to a second `listCurrentOrders`
    read to recover the betId.
- **On second timeout**: surface to operator as in-flight-uncertain. Do not retry
  again. The customerOrderRef is logged as in-flight; manual reconciliation via
  `listCurrentOrders` / `listClearedOrders` is the recovery path.

The 3-second timeout plus single retry plus order-state check gives a worst-case
latency budget of roughly 7 seconds (3s timeout + 1s state check + 3s retry).
Operationally this is well outside the burst window — if v3 hits this path during
INTENSIVE-phase pricing, the bet's edge has likely evaporated. The retry exists to
protect against transient network failures, not to recover bet entries when the market
has moved.

### 14.4 In-play bet-delay timing

Per the on-disk Stream API reference's MarketDefinition Fields table, in-play markets
carry a `betDelay` field — the number of seconds an order is held by Betfair before it
is submitted to the matcher. AU thoroughbred WIN markets typically run `betDelay=0`
through the OPEN-pre-jump window and `betDelay=5` once `inplay=true` flips per Section
14.5.

**Cadence implication:**

- A placement issued at `betDelay=5` does not enter the order book for 5 seconds. v3's
  cache reflects this — `EXECUTABLE` status with `placedDate` set, `matchedDate` not
  yet set, `sizeMatched=0`.
- If the market suspends (race ends, void, etc.) during the 5-second delay, the order
  may lapse with `lsrc=MKT_SUSPENDED` per Section 9's Lapse Status Reason Codes.
- v3 surfaces the bet-delay state to the racing page / sports page so the operator
  knows the bet is held: "queued, will enter market in N seconds" rather than "live
  now". This is consumer-side display logic, not `betfair_client` discipline.

The PASSIVE bet-delay model (per the Stream API reference's MarketDefinition table)
allows specific LIMIT-order shapes to bypass the wait if they're guaranteed not to match
immediately. v3 day-one does not use the PASSIVE model; placements during in-play go
through standard bet-delay. PASSIVE handling is a v3.1+ capability if Strategy 2 in-play
placements ever justify it.

**Sports placements are pre-jump only per §9.5.1.** The bet-delay mechanics described
in this section apply to racing in-play placement (permitted under AU regulation) and
do not apply to sports — sports bet-entry is disabled v3-side once `inplay=true`.

### 14.5 Cancel pacing

Per the on-disk `cancelOrders.md` reference, `cancelOrders`:

- Maximum **60 instructions per request** (per §11.3).
- Two cancel shapes: (a) **cancel-all-on-market** — instructions list omitted,
  `marketId` supplied, every unmatched bet on the market is cancelled in full;
  (b) **targeted** — instructions list specifies one or more `betId`s, each
  optionally with `sizeReduction` for partial cancel.
- **`betId` is the natural idempotency key** for cancels. `cancelOrders` does
  accept a request-level `customerRef` for de-dup with the same 60-second
  window as `placeOrders`, but v3's cancel discipline does not need it —
  `betId` is unique and already known at the time v3 issues a cancel. v3 does
  not retry cancels on timeout: if a cancel didn't land, the bet remains live;
  v3 reads `listCurrentOrders` to confirm and re-issues the cancel as a fresh
  call (not a structural retry). Setting `customerRef` on cancels is therefore
  optional in v3 day-one and is parked as a low-value backward-compatible v1.1
  hardening.

**Cadence:** cancel calls have similar latency to place calls (200–500ms healthy).

The discipline locked in §11.5 applies here: **prefer leaving an order in place rather
than cancelling and re-placing.** Cancels happen when the operator decides the bet
should not be matched (price has moved, decision changed) or when settlement-time cleanup
removes lapsed-but-still-EXECUTABLE leftovers. Routine price-adjustment goes through
`replaceOrders` (per §14.6), not cancel-then-place.

### 14.6 Replace pacing — the atomicity gap

Per the on-disk `replaceOrders.md` reference, `replaceOrders` is **bulk-cancel-then-
bulk-place**, with one critical semantic that application code must handle:

> Atomicity holds for the place phase, but **there is no rollback of cancellations if
> the place phase fails.**

If v3 issues `replaceOrders` to cancel an old order at price X and place a new one at
price Y, and the cancel succeeds but the place fails (e.g. price Y is no longer
available, market suspended, etc.), v3 ends up with **the old order cancelled and no
new order placed.**

**Cadence implication:** v3's `replaceOrders` handler must read the response carefully:

- `instructionReports[0].cancelInstructionReport.status` — did the cancel land?
- `instructionReports[0].placeInstructionReport.status` — did the place land?
- If cancel-success and place-failure, v3 logs the gap and surfaces to the operator
  immediately. Do not auto-retry the place; the price has moved, and silently
  re-attempting may match at a worse price than the operator intended.

This is the load-bearing gotcha of `replaceOrders`. The on-disk reference flags it
explicitly. v3's `betfair_client` exposes a `replace()` method that returns a
discriminated result type (`replaced_ok` / `cancelled_no_replace` / `failed`) so
consumer code cannot accidentally treat the cancel-success-place-failure case as
success.

### 14.7 Update pacing — the persistence-flag-only path

Per Section 9 and the implicit `updateOrders` semantics, `updateOrders` changes the
persistence flag (`LAPSE` → `PERSIST` → `MARKET_ON_CLOSE`) on an existing
`EXECUTABLE` order **without changing its price or size**. This is structurally
distinct from `replaceOrders` and avoids the atomicity gap entirely — there is no
cancel phase to fail-without-rollback.

**Cadence:** `updateOrders` calls have similar latency to place / cancel (200–500ms).
The use case is narrow: typically a placement where the operator decides post-
placement to convert `PERSIST` (default) to `LAPSE` so the order is cancelled
rather than ridden into in-play if not matched pre-jump, or the inverse where a
LAPSE-at-placement override needs flipping back to PERSIST.

v3's `betfair_client` exposes `update_persistence()` as a separate method from
`replace()`. Calling `replace()` to change persistence-only is structurally wrong — the
cancel-place atomicity gap doesn't apply but the failure surfaces are wider; routing
through `update_persistence()` is correct.

### 14.8 Closed-loop latency target

End-to-end target for the operator's click-to-confirmed-match path under healthy
conditions:

| Path                                              | Target          |
|---------------------------------------------------|-----------------|
| Click → REST acknowledgement                      | < 500 ms        |
| REST acknowledgement → Streaming order-cache update | < 500 ms        |
| Streaming order-cache update → match (if immediate) | sub-second      |
| **Total click → fully-matched display**           | **~1 second**   |

In INTENSIVE-phase pricing (T-5min to T-0), this latency target is load-bearing —
edges evaporate inside seconds. v3 does not aim to beat 1 second materially because
the REST round-trip floor is Betfair-owned, but v3 must not slip on the v3-side
contributions:

- Pre-flight checks must stay sub-millisecond.
- HTTP transport must use keep-alive (per §11.6) — connection-establishment latency
  on every placement would blow the budget.
- gzip compression must be enabled on requests and responses.
- The Streaming I/O thread must not block (per Section 7) — if it does, the
  REST-acknowledgement-to-cache-update gap balloons.

If the closed-loop latency exceeds 2 seconds sustainably under healthy conditions,
that's a v3-side performance defect. Investigation surfaces are the same as Section
13.5's degradation surfaces.

### 14.9 What this section does not cover

Order-stream cache shape (matched / unmatched / cancelled / lapsed transitions) is
covered in Section 7. REST endpoint specifics (request shape, response shape, error
codes) are covered in Section 9. Order-state reads (`listCurrentOrders` /
`listClearedOrders`) are covered in Section 10. Error handling and stream health
(reconnection, heartbeat-loss escalation) is covered in Section 15.

This section locks the *placement and cancel timing layer* only.


## 15. Error handling and stream health

There are three failure surfaces v3's `betfair_client` has to handle: errors that come
back on a single REST call, errors that come back on the Streaming connection, and
silent degradation where nothing has technically failed but the operational fitness has
dropped below acceptable. Each has its own recovery shape, and each surfaces to the
operator differently — most failures are handled silently inside `betfair_client` and
the operator never sees them; some surface as visible-but-non-blocking warnings; a small
number block placement entirely until resolved.

### 15.1 The three error categories

**Transient errors** are network blips, brief Betfair-side latency spikes, idle
keep-alive disconnects (per §11.6's three-minute idle-close), and similar. They resolve
on a retry or a reconnect. v3 handles these silently — retry the call, reconnect the
stream, log the event for post-hoc review, and never bother the operator. The single-
retry policy on placement (per §14.3) sits in this category. Streaming reconnect with
exponential backoff (per Section 8) sits here too.

**Structural errors** are bad inputs, bad credentials, or hitting a hard limit. They
won't resolve on retry — retrying just produces the same error. Examples: `INVALID_ODDS`
on a placement (the operator typed a price not on the ladder), `TOO_MUCH_DATA` on a
REST market-data call (per §11.2 weight budget), `NO_APP_KEY` / `INVALID_APP_KEY` /
`INVALID_SESSION_INFORMATION` on authentication. v3 handles these by logging,
surfacing a clear operator-facing error (in the case of placement, the form rejects
the bet with the Betfair reason), and in some cases by automatic recovery
(`INVALID_SESSION_INFORMATION` triggers a fresh login per §11.1).

**Authoritative errors** are Betfair-side state changes that v3 must respect — a market
suspends, a runner is removed, BSP reconciliation completes, etc. These aren't errors
in the failure sense; they're state transitions delivered through the same channels
errors come through. Examples: `MKT_SUSPENDED` lapse-status-reason-code on a placement
(per §14.4), Rule 4 deductions on matched bets (per the Stream API reference's "Runner
Removals on the Order Stream" section), VAR void handling on football. v3 reads these
into the cache as state changes, surfaces them to the relevant UI, and the operator
sees them as part of the normal market lifecycle rather than as failures.

### 15.2 Streaming connection health

The Streaming connection has three independent health signals. v3 monitors all three;
each has a different recovery path.

**The `status` field on every ChangeMessage** signals downstream-service health on the
Betfair side. `null` means stream data is up to date; `503` means stream data is stale
(latency in Betfair's downstream services). Per the on-disk Stream API reference's
"Stream API Status — latency" section, v3 should not disconnect on `503` — when the
stream recovers, updates with the latest data are sent automatically. v3 surfaces the
`503` state to the racing-page / sports-page UI as a "data degraded" indicator (per
Section 12.4's three-tier staleness signalling) and continues operating; placement is
still possible but the operator knows the displayed prices may be stale.

**The heartbeat cadence** signals connection liveness independent of data flow. If no
ChangeMessage of any kind arrives within `2 × heartbeatMs` (per §12.5's connection-
liveness guarantee — 10 seconds at the default 5-second heartbeat), v3 treats the
connection as dead and initiates reconnect per Section 8. This catches the case where
the underlying TCP connection has dropped silently (firewall close, network blip)
without Betfair sending a `CONNECTION_FAILED` status.

**The `con=true` flag on a ChangeMessage** signals that v3 is the bottleneck — Betfair
has conflated multiple updates into one because v3's I/O thread isn't reading the socket
fast enough (per §11.7). This is a v3-side performance defect, not a Betfair issue.
Sustained `con=true` triggers an internal investigation surface (logged, alert raised
to operator log); transient `con=true` is logged silently. The recovery path is v3-
side optimisation, not retry — there's nothing to retry.

### 15.3 Reconnection back-off and escalation

Per Section 8, Streaming reconnect uses bounded exponential back-off — first attempt
immediate, then 1s, 2s, 4s, 8s, capped at 30s (per §3.5 and §8.7). The cap exists
because Betfair's
`TOO_MANY_REQUESTS` error fires on connection-rate abuse (per §11.1); the back-off
keeps v3 well below that ceiling.

**Sustained-failure escalation:** if Streaming has not successfully reconnected within
60 seconds of the first failure, v3 surfaces a hard operator-facing alert. The racing
page and sports page show a connection-down state — placement is disabled until the
stream is healthy, because v3 cannot trust its in-cache prices once the feed is
degraded for that long. The operator can override placement-disable manually if there's
a critical bet to enter (rare, but the path exists), with explicit confirmation that
prices may be stale.

**Recovery on reconnect:** v3 re-authenticates, re-subscribes with the stored
`initialClk` / `clk` tokens (per Section 8's two-token discipline), and the
`ChangeType.RESUB_DELTA` patches the cache forward from where it left off. If
`INVALID_CLOCK` returns, v3 falls back to a fresh `SUB_IMAGE` and the cache is replaced
wholesale — the markets and orders that were live before the disconnect re-arrive in
full.

**Full-image cost on unstable networks:** repeated `INVALID_CLOCK` returns on a flaky
connection mean v3 keeps falling back to fresh `SUB_IMAGE` rather than getting clean
`RESUB_DELTA` patches. Each fresh image is a full re-send of all subscribed market
state, which can be several MB on a busy AU racing afternoon. v3's I/O thread handles
this without consumer-visible degradation in normal cases, but on a sustained-flaky
network the bandwidth cost compounds and the racing page sees `RECONNECTING` /
`SUBSCRIBED` cycle visibly. The 60-second sustained-failure escalation above is the
backstop — beyond that, v3 surfaces the connection state as degraded and the operator
investigates the underlying network rather than continuing to absorb churn.

### 15.4 REST error handling

REST errors come back as either an HTTP-level error (timeout, 502, 503) or as a JSON-
RPC-level error in the response body (`status: FAILURE`, `errorCode`, `errorMessage`).
v3 treats these uniformly — the recovery path depends on the error category (§15.1),
not on which layer the error came through.

**Most common operational errors and their paths:**

- **`TIMEOUT`** (HTTP-level, no response within v3's threshold) — transient, retry per
  §14.3 single-retry policy with order-state lookup in between for placements; for
  reads, retry once and surface to caller as failed if second attempt also times out.
- **`INVALID_SESSION_INFORMATION`** (JSON-RPC-level on any call) — structural-but-
  recoverable. v3 issues a fresh login, retries the original call once with the new
  session token. If the second call also fails with the same error, escalate to
  operator-visible (something's wrong with credentials).
- **`INVALID_APP_KEY`** / **`NO_APP_KEY`** — structural and not recoverable in-session.
  Hard operator alert; placement and reads disabled until resolved.
- **`TOO_MUCH_DATA`** (REST market-data) — structural; v3's chunking discipline (per
  §11.2) should prevent this from ever firing. If it does, the bug is in
  `betfair_client`, not in the call site. Logged as defect-level alert.
- **`TOO_MANY_REQUESTS`** — v3 is hitting Betfair's rate limit somewhere. Back off
  immediately (10-second pause) and log; if it persists, hard operator alert because
  v3's rate-limit discipline (per §11) has a defect.
- **`TEMPORARY_BAN_TOO_MANY_REQUESTS`** — login lockout per §4.5 (100 successful
  logins per minute breached, 20-minute account-side block on fresh login attempts).
  Existing valid sessions continue operating. Surface to operator-visible logs
  immediately; `betfair_client` stops attempting fresh logins until the 20-minute
  window passes.
- **`INVALID_ODDS`** / **`INVALID_BET_SIZE`** — structural, on placement only.
  Surfaced to the operator as a placement rejection with the specific reason; bet form
  remains open for correction.
- **`MARKET_NOT_OPEN_FOR_BETTING`** — authoritative; the market suspended between
  display and click. Surfaced as placement rejection; the operator sees the market is
  no longer accepting bets.

### 15.5 Lapse-status-reason codes

Per the on-disk Stream API reference's "Lapse Status Reason Code Possible Values"
section, when an order lapses (in part or in full), Betfair returns one of thirteen
reason codes on the order-stream `lsrc` field. The operationally meaningful ones for
v3:

- **`MKT_SUSPENDED`** — market suspended while the bet was in the matching queue.
  Common for in-play placements crossing into a SUSPENDED state. Surface to operator;
  the bet didn't match.
- **`MKT_VERSION`** — the bet was placed with a market-version constraint and the
  market changed before matching. v3 day-one does not use market-version constraints
  (per Section 9), so this should not fire; if it does, the call site has a defect.
- **`PRICE_INVALID`** / **`PRICE_IMP_TOO_LARGE`** — the price was outside Betfair's
  permitted range or had moved materially before matching. Surface to operator.
- **`TIME_ELAPSED`** — bet sat in the matching queue too long. Should be rare on AU
  markets; surface to operator if it fires.
- **`SP_IN_PLAY`** — a Betfair SP bet was placed after turn-in-play (which is a
  structural error). Surface as a defect — v3's placement code path should prevent
  this.
- **`MKT_UNKNOWN`** / **`RNR_UNKNOWN`** — market or runner removed between placement
  and matching. Surface as authoritative state change; not a v3 defect.

The remaining codes (`MKT_INVALID`, `CURRENCY_UNKNOWN`, `LINE_TARGET`, `LINE_SP`,
`SMALL_STAKE`) are either v3-defect-level (currency, line semantics) or
operator-error-level (small stake) and surface accordingly.

### 15.6 Operator-visible failure surfaces

Three tiers, distinct and load-bearing:

**Silent / log-only** — transient errors handled inside `betfair_client`. Network
blips, idle-close reconnects, single-retry-success path, transient `con=true`. Logged
for post-hoc review; operator sees nothing.

**Visible-but-non-blocking** — degradation that v3 is operating through, but the
operator should know about. `503` stream-status (data degraded), `con=true` sustained
(v3-side performance defect), placement-rejection on `INVALID_ODDS` / `MKT_SUSPENDED`
(bet didn't go through, but everything else still works). Surfaced via UI state change
(degraded indicator, error toast on placement form, etc.) without blocking the
operator's workflow.

**Hard alert / placement-disabled** — v3 cannot operate safely. Streaming
disconnected for over 60 seconds, repeated `INVALID_SESSION_INFORMATION`,
`INVALID_APP_KEY`, sustained `TOO_MANY_REQUESTS`, repeated REST timeouts across
multiple endpoints. The racing page and sports page disable placement until resolved;
operator sees a hard alert with the specific failure mode and the suggested next step
(restart `betfair_client`, check credentials, contact Betfair support, etc.).

### 15.7 What this section does not cover

Reconnection protocol mechanics (token discipline, RESUB_DELTA vs SUB_IMAGE,
heartbeat-loss escalation timing) are covered in Section 8. Rate-limit and data-limit
specifics (200-point weight budget, instruction counts, login rate floors) are covered
in Section 11. Per-call retry pacing for placements is covered in Section 14.

This section locks the *error categorisation, stream health monitoring, and
operator-visible failure surface* layer.


## 16. Currency — GBP, AUD, and where the conversion happens

- **Betfair's exchange runs on GBP under the hood.** Per the on-disk Stream API
  reference's Currency Support section, market subscriptions on Streaming are *always*
  delivered in GBP — `batb` / `batl` ladders, `bdatb` / `bdatl` virtual ladders,
  `tradedVolume`, `totalMatched` — all GBP, regardless of what currency the operator's
  account holds.

- **v3's account is AUD.** Order subscriptions on Streaming are delivered in the
  account's currency, so the operator's bets show as AUD on the order stream. But the
  market data — the prices and liquidity v3 displays on the racing page and sports page
  — comes through as GBP and must be converted before display.

- **`listCurrencyRates` is the conversion source.** Per the Stream API reference's
  Currency Support section, `listCurrencyRates` is the documented endpoint for
  GBP-to-other-currency conversion (the reference names the endpoint but is silent
  on call cadence, response shape, or rate-limit cost). v3 calls `listCurrencyRates`
  (REST) at startup and refreshes daily as an operator-policy choice — daily
  refresh is well inside intra-day GBP/AUD volatility (typically <1% per day) and
  costs one REST call per process per day. The rate is cached in `betfair_client`
  and applied to every market-data display.

- **The conversion happens at `betfair_client`, never at the consumer surface.** The
  racing page, sports page, and burst-review surface receive prices and liquidity in
  AUD as if Betfair delivered them that way. The consumer code never reasons about GBP.
  This is a single-integration-point discipline (per DR-028 — the cross-database
  integration boundary discipline) extended to currency: no AUD-vs-GBP confusion at
  any layer above `betfair_client`.

- **Roll-up matters at small stakes.** Per the Stream API reference, the default
  GBP roll-up for `batb` / `batl` and `bdatb` / `bdatl` is £1 — stakes under £1 are
  rolled up to the next available price on the odds ladder. For `atb` / `atl` (full
  raw depth) there is no roll-up. Operationally this means the displayed best-back /
  best-lay prices on Streaming are aggregated; the full ladder is the place to read
  if v3 ever needs to know exact small-stake liquidity.

- **Minimum stake is currency-specific.** Per the on-disk `placeOrders.md` reference's
  Additional Information / Currency Parameters section, AUD minimum bet sizes are
  different from GBP minimums. v3's pre-flight placement check (per §14.1) reads the
  AUD minimums table and rejects bets below the minimum before sending the placement
  to Betfair. Trying to place under-minimum returns `INVALID_BET_SIZE` (per §15.4); v3
  catches it before the round trip.

- **BSP liability minimum is also currency-specific.** Same reference, same table —
  AUD minimum BSP liability for LAY bets is its own number. v3's pre-flight check on
  BSP LAY placements reads the AUD value, not the GBP value.

- **Rate staleness is bounded.** The cached GBP-to-AUD rate is refreshed daily (a
  fresh `listCurrencyRates` call at session start, plus once per 24 hours if v3 runs
  through midnight). Intra-day FX moves on the GBP/AUD pair are typically well under
  1% — small enough that bet-entry decisions aren't materially distorted by stale-by-
  hours rate caching. If the daily refresh fails, v3 keeps using the previous rate
  and logs a warning; placement continues.

- **Currency-conversion errors do not block placement.** If the rate cache is empty
  (first-ever startup, refresh failed and no fallback), v3 surfaces a hard alert and
  placement is disabled — placement on un-converted prices is a defect-level state.
  But under normal operation, currency handling is invisible: AUD displayed, AUD
  bet, AUD settled, AUD shown in account state.

### 16.1 What this section does not cover

Account-balance display and reconciliation between v3 and Betfair (where currency also
matters) is covered in Section 6 of `architecture.md` and the v3-build settlement work
post-DR-029. Cross-currency promo handling (free bets denominated in AUD vs GBP-side
bonus calculations) is operator-strategy territory, not a `betfair_client` concern.

This section locks the *currency conversion at the integration boundary* layer only.


## 17. What this closes

§2.4 is locked. The DR-029 stream count drops from eight to seven.

### 17.1 What changed in v3's design picture

The pre-§2.4 position was that v3 needed "an operational line for Betfair pricing" but
the line's shape was unspecified — connection management, subscription patterns, error
handling, cadence, placement protocol all sat as open design questions. §2.4 locks
all of these into a single `betfair_client` module with a versioned contract:

- **Module shape (Section 2)** — `betfair_client` parallel to `vps_client` and
  `softbook_client`, single integration point per DR-028 (the cross-database
  integration boundary discipline), three responsibilities (Streaming pricing,
  REST placement, REST order state), versioned contract.
- **Streaming surface (Sections 3–8)** — connection management, authentication,
  market subscription, order subscription, message handling, reconnection. Two-token
  resub discipline, 5000ms heartbeat, coarse-over-fine subscription, three-tier
  staleness signalling, dedicated I/O thread.
- **REST surface (Sections 9–10)** — JSON-RPC over REST for placement, customerOrderRef
  round-trip, single-retry policy, three placement-side and three order-state
  operations, cold-start reconciliation flow.
- **Operational discipline (Sections 11–16)** — rate-limit handling, per-phase cadence
  expectations, BSP timing gates, placement closed-loop latency budget, error
  categorisation, currency conversion at the boundary.

### 17.2 What this enables downstream

- **§2.5 (soft-book interface contract)** can specify `softbook_client`'s shape against
  the now-locked `betfair_client` reference. The two operational clients are designed
  to look the same from the consumer surface — staleness signalling, three-tier
  freshness states, contract versioning — so the burst-review and racing/sports page
  code reads the same shape from both.
- **§2.6 (settlement model — sports path)** can read live exchange data via
  `betfair_client` for sports auto-settlement per the architecture work locked in
  §2.2 close. The Streaming subscription for sports markets follows the same shape as
  racing per Section 5.
- **§2.7 (API contract versioning)** has its first concrete consumer contract to
  version. `betfair_client` v1.0 contract is the reference shape for `vps_client` and
  `softbook_client` to follow.
- **§2.8 (bet-schema reframing)** now has the operational source shape locked. The
  at-placement decision-context fields v3 stores on bet records (price taken, best
  back / best lay at placement, total matched, snapshot timestamp) come from
  `betfair_client`'s in-process cache.
- **v3 build (post-DR-029)** — racing page and sports page bet-entry surfaces have a
  defined operational data source. The placement closed-loop (§14.8) is the latency
  contract v3's UI is built against.

### 17.3 Open items routed forward

- **`updateOrders` Reference Guide page fetch** — drawn on for §14.7 (update-
  persistence-only path) but inferred from `placeOrders` and `replaceOrders` rather
  than read directly. Pull on demand if Section 14 needs retrofit. Path A continues.
- **`Login & Session Management` Reference Guide page fetch** — drawn on for §4
  (authentication) and §11.4 (login rate floors). Specific session-length details by
  country (per `best_practice.md`'s reference) are not on disk. Pull on demand if
  authentication discipline needs retrofit.
- **`Betting Enums` Reference Guide page fetch** — covers the projection enums and
  status enums used throughout. Inferred from cross-references; pull if specific enum
  semantics need verifying.
- **`Betting Exceptions` Reference Guide page fetch** — covers REST error code
  semantics. §15.4 inferred most of these from context; pull if error-handling
  retrofit needed.
- **`external_api_resources.md` §1 update** — add pointer to the `dr029/2_4_betfair_
  streaming/reference_guide/` folder. Five Reference Guide pages now on disk
  (placeOrders, cancelOrders, replaceOrders, best_practice, market_data_request_limits).
  Two-line edit. Bundles with brief assembly.
- **EX_LADDER entitlement question** — restated. §2.4 does not depend on full-ladder
  data for v3 day-one operational reads. Strategy 4 (synthetic each-way value betting)
  and racing-EV-model calibration analytical capability may eventually need it.
  Operator-side investigation of Betfair API membership tiers carries forward.
- **§2.1 BSP timing observation open item** — substantively addressed in Section 13
  (BSP timing observation carry-in). The "open-but-post-jump BSP reachability" finding
  is now folded into the §13.2 gate (`market_status in (SUSPENDED, CLOSED) AND bsp >
  0`). Open item closes at brief assembly time.
- **PASSIVE bet-delay model handling** — flagged in §14.4 as v3.1+ capability. Not in
  v3 day-one scope; would be revisited if Strategy 2 in-play placements ever justify
  it.
- **Cross-eventId market migration edge case** — per the Stream API reference, Betfair
  Operations occasionally re-parents a market to a new `eventId` mid-life, causing
  the Stream cache to hold two copies of the market and the SUB_IMAGE to carry both.
  Operationally rare; not in v1.0 scope. Cache de-dup logic, if it ever fires, lives
  at consumer surfaces (racing page, sports page) rather than inside `betfair_client`.

### 17.4 What this does not change

The §2.3 (periodic-only API pattern) operational/analytical carve-out is unchanged.
`vps_client` against `capture.db` remains periodic-only for analytical reads;
`betfair_client` is the operational line; the two are independent by construction per
DR-027 (the two-database architecture decision: BetHub owns operational state,
capture.db owns analytical/source data).

The `softbook_client` shape (§2.5) is not yet specified beyond Position (2) locked
Session 27 — source-flexible interface contract, manual entry day-one, vendor
implementation as v3.1 backward-compatible addition.

The asymmetric architecture (racing has both analytical and operational lines; sports
has operational-only) per principle 1.3 of the DR-029 scope is unchanged.

### 17.5 No new debt surfaced

§2.4 closes cleanly without adding to the three pieces of named debt (no test
coverage, no migration framework, monolithic orchestrator file) carried at DR-029
close-out time.