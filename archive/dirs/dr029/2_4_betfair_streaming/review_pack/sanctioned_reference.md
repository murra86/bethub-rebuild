# Sanctioned Reference Material — Betfair Exchange API + Racing API

**Purpose:** Single-document reference compendium for the §2.4 Betfair Streaming brief fresh-eyes review. The reviewer reconciles the locked §2.4 brief against the sanctioned material in this document.

**Scope:** All material Betfair officially publishes and sanctions for developer use, captured from the Betfair developer documentation site (Atlassian Confluence — `betfair-developer-docs.atlassian.net`), plus the canonical OpenAPI specification for The Racing API.

**How to use this document:**

1. Read the §2.4 brief first.
2. For each substantive claim, design choice, or assumption in the brief, locate the relevant section of this reference document and verify the brief is consistent with what Betfair (or The Racing API) documents.
3. Findings of inconsistency, missing reference, or design choices that conflict with documented best practice are the primary output of the review.
4. Findings of "the brief makes a claim this reference doesn't cover" are also valuable — flag the gap.

**Cross-reference index:** Section 4 of this document maps §2.4 brief sections to the most relevant parts of this reference material.

**Reference material on-disk capture provenance:**

- Betfair Streaming API reference — captured Session 59 from operator's authenticated browser session, source: Betfair developer docs Streaming API page.
- Betfair Reference Guide pages (`placeOrders`, `cancelOrders`, `replaceOrders`, `best_practice`, `market_data_request_limits`) — captured during §2.4 brief drafting (Sessions 60-64) from operator's authenticated browser session, source: Betfair Reference Guide.
- Betfair Reference Guide pages (`Login & Session Management`, `Betting Enums`, `Betting Exceptions`, `updateOrders`, `Betfair Starting Price Betting`) — captured between Sessions 65 and 66, source: Betfair Reference Guide.
- Racing API — local OpenAPI specification (`openapi.json`, version 1.4.3), summarised here for reviewer accessibility.

**Confluence access note:** the Betfair developer documentation sits behind an anonymous-access wall on Atlassian Confluence. The on-disk captures are produced from the operator's authenticated browser session and are the canonical reference for this review. URLs below are provided for traceability but cannot be fetched anonymously.

---

## Document structure

1. **Betfair Streaming API** — full reference for the Stream API surface (the API that v3 will subscribe to for live market and order updates).
2. **Betfair Exchange REST API — Reference Guide** — endpoint specs, schemas, error handling, rate limits, authentication, enums, best practices for the polling REST surface that complements Streaming.
3. **Racing API** — endpoint catalogue, authentication, plan-tier accessibility, schema overview for the racing metadata API.
4. **Cross-reference index** — maps §2.4 brief sections to the most relevant reference material.

---

# Section 1 — Betfair Streaming API

**Source URL (reference, not anonymously fetchable):** Betfair developer documentation, Streaming API section.

**On-disk source:** `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` (986 lines).

The content of the Streaming API reference follows below in full.

---


# Betfair Exchange Stream API — Reference

**Source:** Betfair Developer Docs, Exchange Stream API page.
**URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687396/Exchange+Stream+API
**Captured:** 2026-05-03 (Session 59) by operator paste from authenticated browser session. Confluence anonymous-access wall blocks `web_fetch`; this is the canonical text as supplied.
**Last updated upstream:** "Updated Feb 20" (per page metadata at capture time).
**Purpose:** On-disk canonical reference for DR-029 §2.4 (Betfair Streaming spec + cadence design) Fix 4 brief drafting, downstream §2.7 (API contract versioning), and operational debugging post-v3-launch. Parallels `openapi.json` for The Racing API.

**Cross-references:**
- `external_api_resources.md` §1 (Betfair) — pointer-doc references this artefact.
- `dr029/dr029_scope.md` §2.4 — scope item being drafted-as-brief in Session 59.
- `dr029/2_3_periodic_api_pattern.md` — operational/analytical carve-out §2.4 sits inside.

**Update protocol:** treat as immutable snapshot. If Betfair updates the upstream doc materially, capture a fresh dated snapshot rather than editing in place.

---

## Page table of contents

Overview | Sample Application - C#, Java & Node.js | Swagger Definition | Typical Interactions with Stream API | Connection | Basic Message Protocol | Connection / ConnectionMessage | Authentication / AuthenticationMessage | Subscription / SubscriptionMessage | MarketDefinition Fields | RunnerDefinition Fields | KeyLineSelection Fields | OrderSubscription Message | Example Output of Order Stream Message on Connection/Re-connection | Heartbeat / HeartbeatMessage | Re-connection / Re-subscription | Performance Considerations | Currency Support | Runner Removals on the Order Stream | Identifying Cancelled BSP Bets | VAR (Video Assistant Referee) Void Bets Handling | Line Markets | Stream API Status - latency | Stream Health | Conflation | Lapse Status Reason Code Possible Values | Offline Documentation | Known Issues

---

## Overview

The Exchange Streaming API provides low latency access to Betfair Exchange market data allowing you to subscribe to and efficiently track changes to market, price, and order data.

The protocol is based on ssl sockets (normal) with a CRLF JSON protocol. We publish a definition of the schema of the JSON messages in the Swagger format.

We maintain sample code in Java, C#, and Node.js here: https://github.com/betfair/stream-api-sample-code

## Sample Application - C#, Java & Node.js

A console-based C#, Java and Node.js sample application is available for the Market & Order Streaming API and is available via https://github.com/betfair/stream-api-sample-code

Users wishing to interact with the Streaming API using one of these languages are strongly advised to make use of this sample code.

## Swagger Definition

For users wishing to use other languages or develop their own implementation, we provide a swagger schema to allow browsing & code generation.

We recommend using Swagger Code Gen (http://swagger.io/swagger-codegen/) for generation.

As a pre-requisite Java version 7 or higher must be installed.

Download both:

- The Swagger Code Gen jar from: https://oss.sonatype.org/content/repositories/releases/io/swagger/swagger-codegen-cli/2.2.1/swagger-codegen-cli-2.2.1.jar
- The Swagger Definition from our GitHub repository: https://github.com/betfair/stream-api-sample-code/blob/master/ESASwaggerSchema.json

Run the following command to view a list of available languages to generate code for: `java -jar swagger-codegen-cli-2.2.1.jar`

Run the following command to generate the code: `java -jar swagger-codegen-cli-2.2.1.jar generate -i ESASwaggerSchema.json -l <LANGUAGE> -o <OUTPUT_DIRECTORY>`

The Swagger editor can also be used to view the domain model. Use File -> Import File and choose the Swagger Definition downloaded from our GitHub repository.

A few points to note with Swagger:

- It's cross-platform and we can't control how it works / behaves — but it does save a lot of error-prone typing.
- Enums and Inheritance are a little flaky:
  - Enums for error codes / filters etc. are defined but are treated as strings in c# (so you will need to copy definitions from the Swagger spec until this is fixed by Swagger).
  - Inheritance is defined but not generated correctly — you will have to manually manipulate the `op=<type>` field.
  - In c# `JsonCreationConverter` is the typical way to model inheritance.
  - In java look at `JsonSubTypes`.
- We are not a REST service — so only the swagger-generated model package is relevant.

## Typical Interactions with Stream API

The typical API interactions are documented below (detail is below this).

- Market Stream
- Order Stream

## Connection

### Protocol

Every message is in json & terminated with a line feed (CRLF):

```
{json message}\r\n
```

### Json Serializer Setup

As the protocol is CRLF delimited don't forget to turn-off JSON pretty printing (C# has this on by default).

### TCP / SSL Connection

Connection is established with an SSL socket to the following address:

**External (SSL):** `stream-api.betfair.com:443`

### Avoiding TIMEOUT on connection

Once you have established a connection you should send a message within 15 seconds to avoid receiving a TIMEOUT error.

### Pre-production (beta) endpoint

For pre-production (beta) releases the following URL should be used for integration testing only.

**Integration Endpoint:** `stream-api-integration.betfair.com`

## Basic Message Protocol

Two base message classes exist:

- **RequestMessage** — These are messages sent to the server.
- **ResponseMessage** — These are messages received from the server.

Every child message type has:

- `id` — A unique counter you should supply on a RequestMessage and which will be supplied back on a ResponseMessage.
- `op` — This identifies the request type and may be used to switch/deserialize correctly.

**Note:** Any fields representing time and having a long type will represent the UNIX Timestamps (See https://currentmillis.com/ for conversions).

### RequestMessage

RequestMessage is the base class for requests from the client; the discriminator is `op=<message type>`.

Key fields:

- `op=authentication` — The AuthenticationMessage — authenticates your connection.
- `op=marketSubscription` — The MarketSubscriptionMessage — subscribes to market changes.
- `op=orderSubscription` — The OrderSubscriptionMessage — subscribes to order changes.
- `op=heartbeat` — The HeartbeatMessage — use if you need to keep a firewall open or want to test connectivity.

**RequestMessages discipline:**

- Remember to set `op=<message type>` — otherwise, we can't decode the request.
- Remember to set `id=<unique sequence>` — this will let you link requests with responses (these should be logged and provided on support calls).
- Every RequestMessage will receive a StatusMessage with the status of the call (linked by the id that you send).
- All errors apart from `SUBSCRIPTION_LIMIT_EXCEEDED` close the connection.

### ResponseMessage

ResponseMessage is the base class for responses back to the client; the discriminator is `op=<message type>`.

Key fields:

- `op=connection` — The ConnectionMessage sent on your connection.
- `op=status` — The StatusMessage (returned in response to every RequestMessage).
- `op=mcm` — The MarketChangeMessage that carries the initial image and updates to markets that you have subscribed to.
- `op=ocm` — The OrderChangeMessage that carries the initial image and updates to orders that you have subscribed to.

**ResponseMessages discipline:**

- As mentioned earlier the `id=<request id>` links your request with your response.
- ChangeMessages carry the id of the original request that established the subscription.

### Status / StatusMessage

Every request receives a status response with a matching id.

Key fields:

- `statusCode` — The status of the request i.e. success/fail
  - `SUCCESS` — Call processed correctly
  - `FAILURE` — Call failed (inspect errorCode and errorMessage for reason)
- `connectionClosed` — Boolean set to true if the connection was closed as a result of a failure
- `errorCode` — The type of error in case of a failure — see the swagger spec/enum.
- `errorMessage` — Additional message in case of a failure
- `connectionsAvailable` — The number of additional connections you can open (populated only in response to authentication requests)

### ErrorCode

This categorizes the various error codes that could be expected (these are subject to change and extension).

**Protocol — General errors not sent with id linking to specific request (as no request context):**

| ErrorCode | Description |
|---|---|
| `INVALID_INPUT` | Failure code returned when an invalid input is provided (could not deserialize the message) |
| `TIMEOUT` | Failure code when a client times out (i.e. too slow sending data) |

**Authentication — Specific to authentication:**

| ErrorCode | Description |
|---|---|
| `NO_APP_KEY` | Failure code returned when an application key is not found in the message |
| `INVALID_APP_KEY` | Failure code returned when an invalid application key is received |
| `NO_SESSION` | Failure code returned when a session token is not found in the message |
| `INVALID_SESSION_INFORMATION` | Failure code returned when an invalid session token is received |
| `NOT_AUTHORIZED` | Failure code returned when the client is not authorized to perform the operation |
| `MAX_CONNECTION_LIMIT_EXCEEDED` | Failure code returned when a client tries to create more connections than allowed to |
| `TOO_MANY_REQUESTS` | Failure code returned when a client makes too many requests within a short time period |

**Subscription — Specific to subscription requests:**

| ErrorCode | Description |
|---|---|
| `SUBSCRIPTION_LIMIT_EXCEEDED` | Thrown when subscribed to more markets than allowed to — set to 200 markets by default |
| `INVALID_CLOCK` | Failure code returned when an invalid clock is provided on re-subscription (check initialClk / clk supplied) |

**General — General errors which may or may not be linked to specific request id:**

| ErrorCode | Description |
|---|---|
| `UNEXPECTED_ERROR` | Failure code returned when an internal error occurred on the server. Slow or unstable internet connectivity on the client side is one of the most common root causes of this issue. See FAQ's for further information |
| `CONNECTION_FAILED` | Failure code used when the client/server connection is terminated |

## Connection / ConnectionMessage

This is received by the client when it successfully opens a connection to the server.

Key fields:

- `connectionId` — This is a unique identifier that you must supply for support.

### Initial ConnectionMessage

On establishing a connection a client receives a ConnectionMessage — the connectionId must be logged & supplied on any support queries:

```
{"op":"connection","connectionId":"002-230915140112-174"}
```

## Authentication / AuthenticationMessage

This message is the first message that the client must send on connecting to the server — you must be authenticated before any other request is processed.

Key fields:

- `op=authentication` — This is the operation type
- `appKey` — This is your application key to identify your application
- `session` — The session token generated from API login.

### Common Authentication Errors

Some common authentication errors that you should handle — are defined on ErrorCodes enum (these will all close your connection):

- `NO_APP_KEY` / `INVALID_APP_KEY` — Check you are using the correct app key
- `NO_SESSION` / `INVALID_SESSION_INFORMATION` — Check the session is current
- `NOT_AUTHORIZED` — Check that you are using the correct Application Key/session and that it has been set up by Betfair Developer Support.
- `MAX_CONNECTION_LIMIT_EXCEEDED` — Check that you are not creating too many connections / are closing connections properly.
- `TOO_MANY_REQUESTS` — Check that you are not creating/closing connections too frequently

## Subscription / SubscriptionMessage

This message changes the client's subscription — there are currently two subscription message types:

- `op=marketSubscription` — MarketSubscriptionMessage which streams:
  - `op=mcm` — MarketChangeMessage — the price changes for a market
- `op=orderSubscription` — OrderSubscriptionMessage which streams:
  - `op=ocm` — OrderChangeMessage — the order changes for a market

On creating a subscription you will receive:

- StatusMessage confirming the status of your request
- A stream of ChangeMessages linked with the id of the request which is composed of:
  - Initial image
  - Deltas to the initial image

It is possible to subscribe multiple times — each replaces the previous (each will send a new initial image and deltas) — they are not additive.

### Key fields on a SubscriptionMessage

- `segmentationEnabled=true`
  - Segmentation breaks up large messages and improves: end to end performance, latency, time to the first and last byte.
  - See the topic on change message segmentation for a full explanation of how this works.
- `conflateMs` — Specifies a forced conflation rate (in milliseconds) — Please note: the field value will be 180000 if you access the Stream API using a Delayed App Key or have an account delay in place when using the Live App Key.
- `heartbeatMs` — Specifies a minimum interval that a client would expect to receive a message (in milliseconds) — bounds are 500 to 5000 milliseconds.
  - If no change is delivered in this interval then an empty change message will be sent with a `ChangeType.HEARTBEAT`.
- `initialClk` & `clk` — these two sequence tokens allow for faster recovery in the event of a disconnection:
  - If supplied (with identical subscription criteria) you will receive a delta to your previous state rather than a full initial image.
  - See the topic on re-subscription for a full explanation of how this works.

### ChangeMessage

This message is the payload that delivers changes (both initial image & updates) to a client — there are currently two change message types:

- `op=mcm` — MarketChangeMessage
- `op=ocm` — OrderChangeMessage

The Order Changes and Market Changes are being produced by 2 independent systems so we can give no guarantee as to the order in which they will be sent.

**Key fields on a ChangeMessage:**

- `ct` / ChangeType — this enumeration is used to identify the type of change:
  - `SUB_IMAGE` — The initial image returned from a subscription. May also happen while the subscription is ongoing and should replace local cache entirely.
  - `RESUB_DELTA` — A patch returned from a resubscribe.
  - `HEARTBEAT` — An empty message published if no data has been sent within heartbeatMs.
    - We send these to maintain the connection to you and detect closed connections.
    - You can use the heartbeatMs to verify that you are still connected.
  - `<null / not set>` — An update message.
- `segmentType` — SegmentType — this enumeration identifies multi-part segmented messages:
  - `SEG_START` — Start of a segmented message.
  - `SEG` — Middle part of a segmented message.
  - `SEG_END` — Last part of a segmented message.
  - `<null / not set>` — A non-segmented message.
- `conflateMs` — the actual conflation being used. This might be different from what you specified — if your account is for instance delayed or your request was out of bounds.
- `status` — Stream status: set to null if the exchange stream data is up to date and 503 if the downstream services are experiencing latency.
- `heartbeatMs` — the actual heartbeat being used. This might be different from what you specified as we bounds check. You can use this to verify your connection is live (as you should receive 1 message within this time period).
- `pt` — publishTime — the time we sent the message.
- `initialClk` & `clk` — these two sequence tokens allow for faster recovery in the event of a disconnection. If we send these then they should be stored. See the topic on re-subscription for a full explanation of how this works.

### Heartbeat ChangeMessages

`heartbeatMs` is a guarantee of how often (even with no changes) you will receive a ChangeMessage; i.e.:

- If `heartbeatMs=500` and your subscription has not changed in 500ms then we will send an empty ChangeMessage with `ct=HEARTBEAT`.
- (this verifies your connection is live and processing data)

### Change Message Segmentation

Typically on changing your subscription, you will want to clear any local cache you maintain.

**Initial Image Handling:**

- How can I detect the start of an initial image & clear my cache? `ct=ChangeType.SUB_IMAGE` and `segmentType=null` or `SegmentType.SEG_START` indicates the start of a new image.
- How can I detect the end of an initial image? `ct=ChangeType.SUB_IMAGE` and `segmentType=null` or `SegmentType.SEG_END` indicates the end of a new image.
- When I change Subscription how do I safely ignore messages for a previous subscription? All ChangeMessages carry `id=<request id>` — this allows safe disposal during subscription change.

### MarketSubscriptionMessage

This subscription type is used to receive price changes for one or more markets; your subscription criteria determine what you see.

**Coarse vs Fine Grain Subscriptions:**

It is preferable to use coarse grain subscriptions (subscribe to a super-set) rather than fine grain (specific market ids).

- If you find yourself frequently changing subscriptions you probably want to find a wider super-set to subscribe to.

A Market Subscription has two types of filter:

- `marketFilter` — MarketFilter — this is a horizontal filter of markets that you require (i.e. rows).
- `marketDataFilter` — MarketDataFilter — this is a vertical filter of fields that you require (i.e. columns).

Limiting the amount of data that you consume will make your initial image much smaller (and faster) & suppress changes that are uninteresting to you.

### Market Filtering / MarketFilter

As with the Betting API users have the ability to filter the market data they get from the Exchange Stream API (ESA).

All subscriptions are evaluated with a few default criteria:

- Standard jurisdictional filtering that restricts visibility (mirroring site behavior).
- Permissions that control:
  - Specific sports that you are entitled to.
  - A maximum consumption limit (exceeding this will result in an error with details of the limit: `ErrorCode.SUBSCRIPTION_LIMIT_EXCEEDED`).

Users can then specify the following filters when they subscribe to ESA:

| Filter name | Type | Mandatory | Description |
|---|---|---|---|
| `marketIds` | Set<String> | No | If no marketIds passed user will be subscribed to all markets |
| `bspMarket` | Boolean | No | Restrict to Bsp markets only, if True or non-bsp markets if False. If not specified then returns both BSP and non-BSP markets |
| `bettingTypes` | Set<BettingType> | No | Restrict to markets that match the betting type of the market (i.e. Odds, Asian Handicap Singles, or Asian Handicap Doubles) |
| `eventTypeIds` | Set<String> | No | Restrict markets by event type associated with the market. (i.e., "1" for Football, "7" for Horse Racing, etc) |
| `eventIds` | Set<String> | No | Restrict markets by the event id associated with the market |
| `turnInPlayEnabled` | Boolean | No | Restrict to markets that will turn in play if True or will not turn in play if false. If not specified, returns both |
| `marketTypes` | Set<String> | No | Restrict to markets that match the type of the market (i.e., MATCH_ODDS, HALF_TIME_SCORE). You should use this instead of relying on the market name as the market type codes are the same in all locales |
| `venues` | Set<String> | No | Restrict markets by the venue associated with the market. Currently, only Horse Racing markets have venues |
| `countryCodes` | Set<String> | No | Restrict to markets that are in the specified country or countries. Please note: default value is 'GB' when the correct country code cannot be determined |
| `raceTypes` | Set<String> | No | Restrict to markets of a specific raceType. Valid values are — Harness, Flat, Hurdle, Chase, Bumper, NH Flat, Steeple (AUS/NZ races), and NO_VALUE (when no valid race type has been mapped) |

For AUS/NZ races, the following definitions apply:

- `Flat` — Used for standard ANZ thoroughbred races.
- `Harness` — Self-explanatory — used for Aus/NZ harness racing events.
- `Steeple` — Used for Aus/NZ steeple chase races.
- `Hurdle` — Used for Aus/NZ hurdle races.

### Example marketSubscription

For example a subscription message with almost all filters enabled will look something like this:

```json
{"op":"marketSubscription","id":2,"marketFilter":{"marketIds":["1.120684740"],"bspMarket":true,"bettingTypes":["ODDS"],"eventTypeIds":["1"],"eventIds":["27540841"],"turnInPlayEnabled":true,"marketTypes":["MATCH_ODDS"],"countryCodes":["ES"]},"marketDataFilter":{}}
```

**Subscriptions with no matching markets:** We don't verify your subscription criteria as you could potentially subscribe to either a wild card (which would include future markets) or a future marketid which we do not have yet but would send on arrival.

### Market data field filtering / MarketDataFilter

A market data filter restricts the fields that you get back (and only if the fields have changed).

Key fields:

- `fields` — A set of field filter flags (see below).
- `ladderLevels` — For depth-based ladders the number of levels to send (1 to 10). 1 is best price to back or lay etc.

**Ladder Levels Behaviour:** When `bdatb` and `bdatl` are sent with an empty array (`"bdatb":[]`), this indicates that there's an update but this has been filtered out due to the `ladderLevels` marketDataFilter — i.e. the update falls outside of the `ladderLevels` specified.

The field filter flags are defined as shown below.

| Filter name | Fields | Type | Description |
|---|---|---|---|
| `EX_BEST_OFFERS_DISP` | `bdatb`, `bdatl` | level, price, size | Best prices including Virtual Bets — depth is controlled by ladderLevels (1 to 10). Virtual price stream is updated ~150 m/s after non-virtual prices. Virtual prices are calculated for all ladder levels |
| `EX_BEST_OFFERS` | `batb`, `batl` | level, price, size | Best prices not including Virtual Bets — depth is controlled by ladderLevels (1 to 10) |
| `EX_ALL_OFFERS` | `atb`, `atl` | price, size | Full available to BACK/LAY ladder |
| `EX_TRADED` | `trd` | price, size | Full traded ladder. This is the amount traded at any price on any selection in the market |
| `EX_TRADED_VOL` | `tv` | size | Market and runner level traded volume |
| `EX_LTP` | `ltp` | price | The "Last Price Matched" on a selection |
| `EX_MARKET_DEF` | `marketDefinition` | MarketDefinition | Send market definitions. To receive updates to any of the MarketDefinition Fields below |
| `SP_TRADED` | `spb`, `spl` | price, size | Starting price ladder |
| `SP_PROJECTED` | `spn`, `spf` | price | Starting price projection prices. To receive any update to the Betfair SP Near and Far price |

### Examples

Multiple field filters may be combined; a subscription message that contains data fields should look like the following:

```json
{"op":"marketSubscription","id":2,"marketFilter":{"marketIds":["1.120684740"]},"marketDataFilter":{"fields":["EX_BEST_OFFERS_DISP","EX_BEST_OFFERS","EX_ALL_OFFERS","EX_TRADED","EX_TRADED_VOL","EX_LTP","EX_MARKET_DEF","SP_TRADED","SP_PROJECTED"]}}
```

The below example shows how to correctly use the `ladderLevels` marketDataFilter:

```json
{"op": "marketSubscription", "id": 1, "marketFilter": { "marketIds": [ "1.134085859" ] }, "marketDataFilter": { "ladderLevels": 2, "fields": [ "EX_MARKET_DEF", "EX_BEST_OFFERS" ] } }
```

**Correctly configuring field filters can help by:**

- Reducing the size (and time) of initial images.
- Reducing the rate of change (as only changes matching your field filter are sent).

### MC / MarketChangeMessage

This is the ChangeMessage stream of data we send back to you once you subscribe to the market stream.

Key fields:

- `<as for ChangeMessage>`
- `mc` / MarketChange — this list of market changes contains the changes in the markets that you have subscribed to.
- `img` / Image — replace existing prices/data with the data supplied: it is not a delta (or null if delta).
- `tv` — The total amount matched across the market. This value is truncated at 2dp (or null if unchanged).
- `marketDefinition` / MarketDefinition — this is sent in full (but only if it has changed).
- `rc` / RunnerChange — this is sent to supply the details of a runner (namely prices).
- `con` / Conflated `= true` — if this is sent then more than one change is combined in this message.

**Values** — Please note: these fields are only included if the field is in your marketSubscription marketDataFilter (e.g. `EX_LTP`), the field changed at ANY POINT since last received clock (`clk`):

- `tv` — Traded Volume on this runner.
- `ltp` — Last Traded Price on this runner.
- `spn` — Starting Price Near.
- `spf` — Starting Price Far.

**Level / Depth Based Ladders (level, price, size — triples — keyed by level):**

- `size=0` — indicates a remove.
- `batb` / `batl` — Best Available To Back / Best Available To Lay (non-virtual).
- `bdatb` / `bdatl` — Best Display Available To Back / Best Display Available To Lay (virtual).

**Price point / full depth Ladders (price, size — tuples — keyed by price):**

- `size=0` — indicates a remove.
- `atb` / `atl` — Available To Back / Available To Lay (these are the raw/full depth non-virtual prices).
- `spb` / `spl` — Starting Price (Available To) Back / Starting Price (Available To) Lay (please be aware that these values are aligned with `atb` / `atl`).
- `trd` — Traded.

### Building a price cache

Most of the change-based data (RunnerChange) is delta based — this means a few rules:

- `img` / Image — if this is set to true then you should replace this item in your cache.
- Values — the values sent are nullable & are not sent if they are not changed (i.e. if `tv` has not changed then there will be no field in the message).

**Level / Depth-Based ladders:**

- `[0, 1.2, 20]` → Insert / Update level 0 (top of book) with price 1.2 and size 20.
- `[0, 1.2, 0]` → Remove level 0 (top of book) i.e. ladder is now empty.

**Price point / full-depth ladders:**

- `[1.2, 20]` → Insert / Update price 1.2 with size 20.
- `[1.2, 0]` → Remove price 1.2 i.e. there is no size at this price.

### Worked examples — ladder updates

You will always receive an update at every position in the ladder that changed so you'll never have to assume anything based on the message you receive.

Seeing `[position,0,0]` means that there's nothing at that position anymore (and hence `[0,0,0]` means there's nothing in the entire ladder anymore).

Placed the first bet on a selection:

```json
"batl":[[0,1.4,2],[1,0,0],[2,0,0],[3,0,0],[4,0,0],[5,0,0],[6,0,0],[7,0,0],[8,0,0],[9,0,0]]
```

Placed a second bet that didn't disturb the first bet's position:

```json
"batl":[[1,1.5,2]]
```

Placed a third bet that bumped the previous two down the ladder:

```json
"batl":[[2,1.5,2],[1,1.4,2],[0,1.3,2]]
```

Cancelled the top position causing the other positions to move up (and the bottom position to become empty):

```json
"batl":[[2,0,0],[1,1.5,2],[0,1.4,2]]
```

Cancelled by market to remove the remaining 2 positions in one go:

```json
"batl":[[1,0,0],[0,0,0]]
```

## MarketDefinition Fields

The following fields are returned within the marketDefinition.

| Field Name | Description | Type |
|---|---|---|
| `Id` | Market Id — the id of the market | string |
| `Venue` | The venue — applies to horse racing and greyhound markets only | string |
| `raceType` | Harness, Flat, Hurdle, Chase, Bumper, NH Flat, Steeple (AUS/NZ races), and NO_VALUE (when no valid race type has been mapped) | string |
| `settledTime` | Market settled time | date-time |
| `timeZone` | This is the timezone in which the event is taking place | string |
| `eachWayDivisor` | The divisor is returned for the marketType EACH_WAY only and refers to the fraction of the win odds at which the place portion of an each way bet is settled | double |
| `bspMarket` | If 'true' the market supports Betfair SP betting | boolean |
| `turnInPlayEnabled` | If 'true' the market is set to turn in-play | boolean |
| `priceLadderDefinition` | Definition of the price ladder type — `CLASSIC`, `FINEST`, `LINE_RANGE` | string |
| `keyLineDefinition` | Definition of a markets key line selection (for valid markets), comprising the selectionId and handicap of the team it is applied to | integer |
| `persistenceEnabled` | If 'true' the market supports 'Keep' bets if the market is to be turned in-play | boolean |
| `marketBaseRate` | The commission rate applicable to the market | double |
| `eventId` | The unique id for the event | string |
| `eventTypeId` | The unique eventTypeId that the event belongs to | string |
| `numberOfWinners` | The number of winners on a market | integer |
| `countryCode` | The events ISO 3166-2 country code | string |
| `lineMaxUnit` | For Handicap and Line markets, the maximum value for the outcome, in market units for this market (eg 100 runs) | double |
| `bettingType` | The market betting type i.e. ODDS, ASIAN_HANDICAP_DOUBLE_LINE, ASIAN_HANDICAP_SINGLE_LINE | string |
| `marketType` | Market base type | string |
| `marketTime` | The market start time | string |
| `suspendTime` | The market suspend time | string |
| `bspReconciled` | True if the market starting price has been reconciled | boolean |
| `complete` | If false, runners may be added to the market | boolean |
| `inPlay` | True if the market is currently in play | boolean |
| `crossMatching` | True if cross-matching is enabled for this market | boolean |
| `runnersVoidable` | True if runners in the market can be voided | boolean |
| `numberOfActiveRunners` | The number of runners that are currently active. An active runner is a selection available for betting | integer |
| `lineMinUnit` | For Handicap and Line markets, the minimum value for the outcome, in market units for this market (eg 0 runs) | double |
| `betDelay` | The number of seconds an order is held until it is submitted into the market. Orders are usually delayed when the market is in-play | integer |
| `status` | The status of the market, for example, OPEN, SUSPENDED, CLOSED (settled), etc | string |
| `regulators` | The market regulators | string |
| `discountAllowed` | Indicate whether or not the users discount rate is taken into account in this market | boolean |
| `openDate` | The scheduled start date and time of the event. This is GMT by default | date |
| `version` | A non-monotonically increasing number indicates market changes | long |
| `suspendReason` | Currently returned only for Soccer markets, when status = SUSPENDED. Possible values are Goal, Third Party Unavailable, Penalty, Red Card, Non In Play Market | string |

**`betDelayModels`** — Indicates which bet delay model/s are applied to a market. PASSIVE, DYNAMIC or both.

- **PASSIVE** — For in-play markets where `betDelay > 0`, orders that are guaranteed not to match immediately are accepted straight away, bypassing the bet delay wait. Order requirements (otherwise bets will be subject to the usual bet delay before being placed):
  - Only plain LIMIT orders are supported.
  - Allowed `persistenceType`: LAPSE.
  - The following attributes are not supported and must be omitted: `timeInForce`, `minFillSize`, `betTargetType`.
- **DYNAMIC** — Indicates market is subject to dynamic in-play bet delays. This means that the in-play `betDelay` will vary while the market is turned in-play.
  - Please note: Currently returned for Tennis markets only. Specifically, every game 3, 5, 7, 9, 11 or game which decides a set (potentially 6, 8, 10, 12) the betDelay is reduced to 1 second.

## RunnerDefinition Fields

The following fields are returned within the runnerDefinition.

| Field Name | Description | Type |
|---|---|---|
| `sortPriority` | Indicates the sort order of the runner on www.betfair.com | integer |
| `removalDate` | The date and time the selection was removed from the market | date-time |
| `name` | The name of the selection | string |
| `Id` | The unique id for the selection | integer |
| `hc` | Handicap — the handicap of the runner (selection) (null if not applicable) | double |
| `adjustmentFactor` | The adjustment factor applicable if the runner is removed from the market | double |
| `bsp` | The Betfair Starting Price of the selection | double |
| `status` | The status of the selection (ACTIVE, WINNER, LOSER, REMOVED, REMOVED_VACANT, HIDDEN, PLACED) | string |

## KeyLineSelection Fields

Description of a markets key line selection, comprising the selectionId and handicap of the team it is applied to.

**Please Note** — The KeyLine selection returned via the Exchange Stream API is based on raw (non virtual prices) only.

| Field name | Description | Type |
|---|---|---|
| `id` | Selection ID of the runner in the key line handicap | integer |
| `hc` | Handicap value of the key line | double |

## OrderSubscription Message

This subscription type is used to receive order changes; the subscription message has one type of filter:

- `orderFilter` (optional)

### OrderFilter

This optional filter already filters by your account, but additional data shaping is supported.

| Filter name | Type | Mandatory | Default | Description |
|---|---|---|---|---|
| `accountIds` | Set<Integer> | No | null | This is for internal use only & should not be set on your filter (your subscription is already locked to your account) |
| `includeOverallPosition` | Boolean | No | true | Returns overall / net position (`OrderRunnerChange.mb` / `OrderRunnerChange.ml`) |
| `customerStrategyRefs` | Set<String> | No | null | Restricts to specified `customerStrategyRefs` (specified in placeOrders); this will filter orders and StrategyMatchChanges accordingly (Note: overall position is not filtered) |
| `partitionMatchedByStrategyRef` | Boolean | No | false | Returns strategy positions (`OrderRunnerChange.smc=Map<customerStrategyRef, StrategyMatchChange>`) — these are sent in delta format as per overall position |

**Example:**

```json
{"op":"orderSubscription","orderFilter":{"includeOverallPosition":false,"customerStrategyRefs":["betstrategy1"],"partitionMatchedByStrategyRef":true},"segmentationEnabled":true}
```

### OCM / OrderChangeMessage

This is the ChangeMessage stream of data we send back to you once you subscribe to the order stream.

Key fields:

- `<as for ChangeMessage>`
- `oc` / OrderAccountChange — the modifications to account's orders (will be null on a heartbeat).
- `closed` — indicates when the market is closed.
- `id` / Market Id — the id of the market the order is on.
- `fullImage` — replace existing data at market level with the data supplied: it is not a delta (or null if delta).
- `orc` / Order Changes — a list of changes to orders on a runner.
- `fullImage` — replace existing data at runner level with the data supplied: it is not a delta (or null if delta).
- `id` / Selection Id — the id of the runner (selection).
- `hc` / Handicap — the handicap of the runner (selection) (null if not applicable).
- `uo` / Unmatched Orders — orders on this runner that are unmatched.

**Order Stream — order field reference.**

Every order change is sent in full; the transient on a change to EXECUTION_COMPLETE is sent (but it would not be sent on the initial image).

- `id` / Bet Id — the id of the order.
- `p` / Price — the original placed price of the order.
- `s` / Size — the original placed size of the order.
- `bsp` / BSP Liability — the BSP liability of the order (null if the order is not a BSP order).
- `side` / Side — the side of the order.
- `status` / Status — the status of the order (`E` = EXECUTABLE, `EC` = EXECUTION_COMPLETE).
- `pt` / Persistence Type — whether the order will persist at in play or not (`L` = LAPSE, `P` = PERSIST, `MOC` = Market On Close).
- `ot` / Order Type — the type of the order (`L` = LIMIT, `MOC` = MARKET_ON_CLOSE, `LOC` = LIMIT_ON_CLOSE).
- `pd` / Placed Date — the date the order was placed.
- `md` / Matched Date — the date the order was matched (null if the order is not matched).
- `cd` / Cancelled Date — the date the order was cancelled (null if the order is not cancelled).
- `ld` / Lapsed Date — the date the order was lapsed (null if the order is not lapsed).
- `lsrc` / Lapse Status Reason Code — the reason that some or all of this order has been lapsed (null if no portion of the order is lapsed).
- `avp` / Average Price Matched — the average price the order was matched at (null if the order is not matched).
- `sm` / Size Matched — the amount of the order that has been matched.
- `sr` / Size Remaining — the amount of the order that is remaining unmatched.
- `sl` / Size Lapsed — the amount of the order that has been lapsed.
- `sc` / Size Cancelled — the amount of the order that has been cancelled.
- `sv` / Size Voided — the amount of the order that has been voided.
- `rac` / Regulator Auth Code — the auth code returned by the regulator.
- `rc` / Regulator Code — the regulator of the order.
- `rfo` / Reference Order — the customer supplied order reference.
- `rfs` / Reference Strategy — the customer-supplied strategy reference used to group orders together — default is "".

**Price point / full depth Ladders (price, size — tuples — keyed by price) of matches:**

- `mb` / Matched Backs — matched amounts by distinct matched price on the Back side for this runner.
- `ml` / Matched Lays — matched amounts by distinct matched price on the Lay side for this runner.

### Building an order cache

An order cache is somewhat simpler as orders are sent in full (on change) and only matches need delta merging.

- `fullImage` — if the market or runner's `fullImage` value is set to true then you should replace this item in your cache. **N.B.** it is possible for the `fullImage` flag to be sent with an empty update for a market/runner which indicates you no longer have any position on that market/runner and it can be removed from your cache completely.
- Orders — replace each order according to order id.

**Price point / full depth ladders:**

- `[1.2, 20]` → Insert / Update price 1.2 with size 20.
- `[1.2, 0]` → Remove price 1.2 i.e. there is no size at this price.
- An empty list of points also means the ladder is now empty.

### Currencies

- **Market subscriptions** — are always in underlying exchange currency — GBP. The default roll-up for GBP is £1 for `batb` / `batl` and `bdatb` / `bdatl`. This means that stakes of less than £1 (or currency equivalent) are rolled up to the next available price on the odds ladder. For `atb` / `atl` there is no roll-up. Available volume is displayed at all prices including those with less than £2 available.
- **Orders subscriptions** — are provided in the currency of the account that the orders are placed in.

### Unmatched Orders

- **New subscriptions:** Will receive an initial image with only `E` — Executable orders (unmatched).
- **Live subscriptions:** Will receive a transient of the order to `EC` — Execution Complete as the order transits into that state (allowing you to remove the order from your cache).

**Please note:** EXECUTION_COMPLETE (fully matched) orders are only returned when transitioning from EXECUTABLE to EXECUTION_COMPLETE. The full details of EXECUTION_COMPLETE orders can only be viewed using `listCurrentOrders` / `listMarketBook` using `orderProjections`.

### Market Level Snapshots

During normal streaming, you may on rare occasions receive a market-level snapshot, in which case you should replace the item in your cache. The update will be a `fullImage`, as shown in the example below:

```json
{"clk": "AIElAJgiAIYjAMAhAOsm", "oc": [{"orc": [{"uo": [{"status": "E", "rfs": "", "sm": 0, "pt": "L", "sr": 2, "rc": "REG_GGC", "sv": 0, "side": "B", "p": 990, "s": 2, "pd": 1603894536000, "sl": 0, "sc": 0, "ot": "L", "rfo": "", "id": "215144775671", "rac": ""}], "id": 30246, "fullImage": true}], "id": "1.174743281", "fullImage": true}], "pt": 1603895058618, "op": "ocm"}
```

## Example Output of Order Stream Message on Connection/Re-connection

Here's an example showing the data provided following a connection/re-connection to the Order Stream API. The example shows matched backs on two separate markets one of which has a size remaining of 0.25.

**Example of Order Stream Output (reconnection) — with size remaining:**

```json
{
    "op": "ocm",
    "id": 6,
    "initialClk": "GpOH0JwBH762w50BHKKomJ0BGpzR5ZoBH5mWsJwB",
    "clk": "AAAAAAAAAAAAAA==",
    "conflateMs": 0,
    "heartbeatMs": 5000,
    "pt": 1468943673782,
    "ct": "SUB_IMAGE",
    "oc": [{
        "id": "1.125657695",
        "orc": [{
            "fullImage": true,
            "id": 48756,
            "mb": [
                [1.4, 2]
            ]
        }]
    }, {
        "id": "1.125657760",
        "orc": [{
            "fullImage": true,
            "id": 151478,
            "uo": [{
                "id": "71352090695",
                "p": 12,
                "s": 5,
                "side": "B",
                "status": "E",
                "pt": "L",
                "ot": "L",
                "pd": 1468919099000,
                "md": 1468933833000,
                "avp": 12,
                "sm": 4.75,
                "sr": 0.25,
                "sl": 0,
                "sc": 0,
                "sv": 0
            }],
            "mb": [
                [12, 4.75]
            ]
        }]
    }]
}
```

**Remaining 0.25 is then matched on marketId 1.125657760:**

```json
{
   "op": "ocm",
   "id": 10,
   "initialClk": "GtD10ZwBH5OJxZ0BHK75mZ0BGsKq6JoBH4THsZwB",
   "clk": "AAAAAAAAAAAAAA==",
   "conflateMs": 0,
   "heartbeatMs": 5000,
   "pt": 1468944647413,
   "ct": "SUB_IMAGE",
   "oc": [{
       "id": "1.125670254",
       "orc": [{
           "fullImage": true,
           "id": 5643663
       }]
   }, {
       "id": "1.125657760",
       "orc": [{
           "fullImage": true,
           "id": 151478,
           "mb": [
               [12, 5]
           ]
       }]
   }, {
       "id": "1.125657695",
       "orc": [{
           "fullImage": true,
           "id": 48756,
           "mb": [
               [1.4, 2]
           ]
       }]
   }]
}
```

## Heartbeat / HeartbeatMessage

This is an explicit heartbeat request (in addition to the server heartbeat interval which is automatic).

This functionality should not normally be necessary unless you need to keep a firewall open.

**Do I need to use HeartbeatMessage?**

No — under normal circumstances the subscription level `ChangeType.HEARTBEAT` is an acceptable guarantee of connection health.

Use the HeartbeatMessage only if you need to keep a firewall open — as it will incur some performance penalty (as a response will block your connection).

## Re-connection / Re-subscription

Although maintaining long-lived connections is actively encouraged (for the Stream API for example), for a number of reasons within & beyond our direct control, we cannot guarantee that keep-alive connection won't be forcibly closed. We, therefore, advise all customers to ensure that they have reconnection logic in place to handle any connection termination scenarios.

If a client is disconnected a client may connect, authenticate and re-subscribe.

**Prerequisite steps:**

1. Store your subscription criteria (re-subscribe will only work correctly with identical subscription criteria).
2. Store `initialClk` (normally only initial image) & `Clk` (normally on every non-segmented message or a SEG_END) on any change message they are sent on.
3. The connection is broken.
4. Connect & Authenticate as normal.
5. Subscribe setting `initialClk` and `Clk` to the last values sent on the subscription.
6. Change message with `ChangeType.RESUB_DELTA` is sent — this will patch your cache.
7. Some markets might have `img=true` set indicating they are either new or can't be patched.

**Easiest way to implement re-subscribe:**

- Store any new subscription message you send as a "pending subscription".
- Store this as an "active subscription" once you get your initial image.
- Update the `initialClk` & `clk` on the subscription message with any non-null values.
- Resend this message after re-connecting.

## Performance Considerations

Here are a few tips on performance which are worth bearing in mind:

**Performance tips:**

- A single market subscription & a subscription to all markets have an identical latency:
  - Cost is identical as the two subscriptions above would evaluate in sequence and thus with the same average latency.
- The initial image is more costly to send than extra updates.
- Limiting data with appropriate filters reduces initial image time.
- Segmented data will always outperform non-segmented data:
  - You will be processing a buffer while another is in-flight and another is being prepared to send.
- Writes to your connection are directly affected by how quickly you consume data & clear your socket's buffer.
- Consuming data slowly is effectively identical to setting conflation.

If you receive `con=true` flag on a market — then you are either:

- consuming data slower than the rate of delivery
- The client subscription message has the `conflateMs` parameter set to a value greater than '0'.
- The Stream API has a slow publishing cycle resulting in multiple updates being pushed in the same message.

## Currency Support

The Exchange Stream API supports GBP currency only.

Those looking to convert data from GBP to a different currency should use `listCurrencyRates` to do so.

**Currencies (restated):**

- **Market subscriptions** — are always in underlying exchange currency — GBP. The default roll-up for GBP is £1 for `batb` / `batl` and `bdatb` / `bdatl`. This means that stakes of less than £1 (or currency equivalent) are rolled up to the next available price on the odds ladder. For `atb` / `atl` there is no roll-up. Available volume is displayed at all prices including those with less than £2 available.
- **Orders subscriptions** — are provided in the currency of the account that the orders are placed in.

## Runner Removals on the Order Stream

When a Rule 4 Runner Removal occurs in a Horse Race the price of matched bets on remaining runners are reduced by a Reduction Factor.

For these matched bets, you will receive on the Order Stream both a `uo` for the affected bet and the relevant updates to `mb` or `ml` (reducing the matched volume at the original matched price and adding volume at the new reduced price).

**Initial bet placement at price 12:**

```json
{"op":"ocm","id":2,"clk":"AK0CAPsBALEC","pt":1467219304831,"oc":[{"id":"1.102151675","orc":[{"fullImage":true,"id":6113662,"uo":[{"id":"10822867886","p":12,"s":2,"side":"B","status":"E","pt":"L","ot":"L","pd":1467219304000,"sm":0,"sr":2,"sl":0,"sc":0,"sv":0,"rac":"","rc":"REG_GGC"}]}]}]}
```

**Bet fully matched at price 12:**

```json
{"op":"ocm","id":2,"clk":"AK0CAPsBALMC","pt":1467219316709,"oc":[{"id":"1.102151675","orc":[{"id":6113662,"uo":[{"id":"10822867886","p":12,"s":2,"side":"B","status":"EC","pt":"L","ot":"L","pd":1467219304000,"md":1467219316000,"avp":12,"sm":2,"sr":0,"sl":0,"sc":0,"sv":0}],"mb":[[12,2]]}]}]}
```

**Runner removed (and so bet was reduced in price to 9.47):**

```json
{"op":"ocm","id":2,"clk":"AK0CAJACALsC","pt":1467219376611,"oc":[{"id":"1.102151675","orc":[{"id":6113662,"uo":[{"id":"10822867886","p":12,"s":2,"side":"B","status":"EC","pt":"L","ot":"L","pd":1467219304000,"md":1467219316000,"avp":9.47,"sm":2,"sr":0,"sl":0,"sc":0,"sv":0}],"mb":[[9.47,2],[12,0]]}]}]}
```

See the `avp` in the `uo` record showing the new price of 9.47 and see the two entries in `mb`, one to remove the previously added size of 2 at a price point 12 and one to add the size of 2 into the new price point of size 9.47.

Bets placed on the actual removed runner will be voided/lapsed (for matched/unmatched bets respectively) and these will also be sent through on the Order Stream.

## Identifying Cancelled BSP Bets

Whilst BSP bets cannot be cancelled in general, in the scenario where a Limit Price applied to the BSP bet is updated this is modelled as a Cancellation of the original bet with the original Limit Price and a Place of a new bet with the new Limit Price.

In this scenario, the cancellation of the original bet can be identified by looking at the "Cancelled Date" field (`cd`) on the "Unmatched Orders" object (`uo`) — N.B. there will be no "Size Cancelled" (`sc`) because a BSP bet does not have any Size before reconciliation.

## VAR (Video Assistant Referee) Void Bets Handling

Here's an example of the Stream API output during a VAR goal cancellation.

**Bets placed after goal scored by home team:**

```json
{"op": "ocm", "clk": "AAAAbwBSAE0AAA==", "status": 503, "pt": 1740062495457, "oc": [{"id": "1.183211193", "orc": [{"id": 55271, "uo": [{"id": "309703551064", "p": 2, "s": 2, "side": "L", "status": "EC", "pt": "L", "ot": "L", "pd": 1740062487000, "md": 1740062495000, "avp": 2, "sm": 2, "sr": 0, "sl": 0, "sc": 0, "sv": 0, "rac": "", "rc": "REG_GGC", "rfo": "", "rfs": ""}], "ml": [[2, 4]], "smc": {"": {"ml": [[2, 4]]}}}]}]}
{"op": "ocm", "clk": "AAAAcgBSAE0AAA==", "status": 503, "pt": 1740062516601, "oc": [{"id": "1.183211193", "orc": [{"id": 44787, "uo": [{"id": "309703551066", "p": 2, "s": 2, "side": "B", "status": "E", "pt": "L", "ot": "L", "pd": 1740062508000, "sm": 0, "sr": 2, "sl": 0, "sc": 0, "sv": 0, "rac": "", "rc": "REG_GGC", "rfo": "", "rfs": ""}]}]}]}
```

**Same bets after goal scored by home team have been cancelled:**

```json
{"id": 55271, "uo": [{"id": "309703551064", "p": 2, "s": 2, "side": "L", "status": "EC", "pt": "L", "ot": "L", "pd": 1740062487000, "md": 1740062495000, "sm": 0, "sr": 0, "sl": 0, "sc": 0, "sv": 2, "rac": "", "rc": "REG_GGC", "rfo": "", "rfs": ""}
{"id": 44787, "uo": [{"id": "309703551066", "p": 2, "s": 2, "side": "B", "status": "EC", "pt": "L", "ot": "L", "pd": 1740062508000, "ld": 1740062723421, "sm": 0, "sr": 0, "sl": 2, "sc": 0, "sv": 0, "rac": "", "rc": "REG_GGC", "rfo": "", "rfs": ""}
```

Key difference being in the values of `sizeMatched` and `sizeRemaining` before the event and `sizeVoided` and `sizeLapsed` after the event.

## Line Markets

Line markets being sent on the Market Stream can be identified by the `bettingType` field of MarketDefinition (with value of "LINE").

The MarketDefinition of Line markets provides some additional fields that will be null for all other types:

- `lineMaxUnit` — maximum value for the outcome, in market units for this market (eg 100 runs).
- `lineMinUnit` — minimum value for the outcome, in market units for this market (eg 0 runs).
- `lineInterval` — the odds ladder on this market will be between the range of `lineMinUnit` and `lineMaxUnit`, in increments of the interval value. e.g. If `lineMinUnit=10 runs`, `lineMaxUnit=20 runs`, `lineInterval=0.5 runs`, then valid odds include 10, 10.5, 11, 11.5 up to 20 runs.

For updates for Orders on Line markets received on the Order Stream be aware of how the following properties behave:

- `price` — line markets operate at even-money odds of 2.0. However, the price for these markets refers to the line positions available as defined by the markets min-max range and interval steps.
- `side` — for Line markets a 'B' bet refers to a SELL line and an 'L' bet refers to a BUY line.
- `averagePriceMatched` — this value is not meaningful for activity on Line markets and is not guaranteed to be returned or maintained for these markets.

## Stream API Status — latency

If any latency occurs, the ChangeMessage for the Order and Market Stream will contain a `status` field which will give an indication of the health of the stream data provided by the service. This feature will be used in addition to the heartbeat mechanism which only gives an indication that the service is up but doesn't provide an indication of the latency of the data provided.

By default, when the stream data is up to date the value is set to null and will be set to 503 when the stream data is unreliable (i.e. not all bets and market changes will be reflected on the stream) due to an increase in push latency. Clients shouldn't disconnect if status 503 is returned; when the stream recovers updates will be sent containing the latest data. The status is sent per subscription on heartbeats and change messages.

**Example of message containing the status field:**

```json
{"op":"ocm","id":3,"clk":"AAAAAAAA","status":503,"pt":1498137379766,"ct":"HEARTBEAT"}

{"op":"mcm","id":2,"clk":"AAAAAAAA","status":503,"pt":1498137381621,"ct":"HEARTBEAT"
```

## Stream Health

In addition to the Stream API status field, we'd recommend the below as best practice for monitoring the health of the Stream API:

- Use heartbeat messages to confirm Stream API is healthy and that you are still connected.
- Messages with `ChangeType.HEARTBEAT` will be sent at the requested interval if no change has occurred.
- If no message of any kind is received for 2 x heartbeat intervals then you may no longer be connected — initiate a fresh connection (use re-subscribe to continue where you left off).
- Re-connect code should contain back-offs to avoid spamming the service if you are unable to connect for a prolonged period for any reason.

## Conflation

Conflation set to true (`con=true`) in the stream message means that multiple stream updates have been pushed in the same cycle.

This can happen due to the following reasons:

- The client socket buffer for the connection needs to be read (cleared) by the client in order for the Stream API to push the next cycle, if not the current update is skipped, and pushed with the next cycle resulting in `con = true`.
- The client subscription message has the `conflateMs` parameter set to a value greater than '0'.
- The Stream API has a slow publishing cycle resulting in multiple updates being pushed in the same message.

## Lapse Status Reason Code Possible Values

This field will now be present in some cases on the Order object of the Order Stream to denote the reason that some or all of the order is lapsed. It will be null if no portion of the order is lapsed or if the order lapsed for some reason other than those listed below.

The full list of currently supported values for this field is:

| Code | Description |
|---|---|
| `MKT_UNKNOWN` | The market was unknown, presumably removed from the matcher (closed) between bet placement and matching |
| `MKT_INVALID` | The market was known about but in an invalid state |
| `RNR_UNKNOWN` | The runner was unknown, presumably removed between bet placement and matching |
| `TIME_ELAPSED` | The bet was waiting in the queue too long, so was lapsed for safety |
| `CURRENCY_UNKNOWN` | The bet's currency ID was not recognised by the matcher |
| `PRICE_INVALID` | The bet's price was invalid, e.g. outside the defined ladder for the market |
| `MKT_SUSPENDED` | The market was suspended at the time the bet came to be matched |
| `MKT_VERSION` | The bet had a maximum market version set, and the market's version on matching was greater than this |
| `LINE_TARGET` | The bet was on a line market, but was requested targeting profit or payout |
| `LINE_SP` | The bet was on a line market, but was either a BSP bet directly or requested to PERSIST_TO_SP |
| `SP_IN_PLAY` | The bet was a BSP bet that had somehow come to be placed after turn-in-play |
| `SMALL_STAKE` | The bet's stake was worth less than half a penny in GBP |
| `PRICE_IMP_TOO_LARGE` | When the bet came to be matched, the price available was better than its best-permitted price, suggesting a significant shift in the market, presumably due to a major incident, which may have rendered the bet unwanted |

## Offline Documentation

An offline version of the Exchange Stream API is available via `ExchangeStreamAPI-March2018.pdf`.

Please note, the full Exchange Stream API specification is available online here.

## Known Issues

**Markets moved under a new eventId** — In certain circumstances, a market may move from one eventId to another due to actions performed by our Exchange Operations team. This will cause the Exchange Stream API to hold two copies of the market in its cache and the initial image of the market provided will therefore contain both copies of the market. In these circumstances, further Stream API updates will only be sent for the latest version of the market. You can identify the latest version of the market using the `version` parameter returned in the initial image and should only store the market with the higher version number.

**Trades with volume = 0 for all traded price points** — e.g. `[{"trd":[[1.75,0],[1.5,0],[1.25,0],[1.32,0],[1.57,0],[2.86,0],[1.82,0],[2.36,0],[1.76,0],[2.48,0],[1.51,0],[2.98,0],[1.26,0]...` — This is an artefact of settlement kicking off that moves the bets away from trading DB into the longer-term store. Any price change notifications triggered during this process will result in attempts to reconstruct the market view based on no bets being available and would result in this kind of notification being sent.

---

# Section 2 — Betfair Exchange REST API (Reference Guide)

**Source URL (reference, not anonymously fetchable):** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687473/Reference+Guide

**On-disk source:** `dr029/2_4_betfair_streaming/reference_guide/` — five captured pages (placeOrders, cancelOrders, replaceOrders, best_practice, market_data_request_limits) plus four pages captured between Sessions 65 and 66 (login_session_management, betting_enums, betting_exceptions, updateOrders).

The Reference Guide is the authoritative reference for the Betfair Exchange polling REST API surface — endpoint specifications, request/response schemas, projection sets, error codes, rate limits, and best practices. It complements the Streaming API reference in Section 1.

The captured pages follow below in turn.

---

## 2.1 — placeOrders

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687509/placeOrders

# placeOrders

**Source:** Betfair Exchange API Documentation — https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687496/placeOrders
**Captured:** 2026-05-03 (Session 60) via web_fetch.
**Last updated upstream:** Jan 07, 2025.

---

## Operation signature

```
PlaceExecutionReport placeOrders(
    String marketId,
    List<PlaceInstruction> instructions,
    String customerRef,
    MarketVersion marketVersion,
    String customerStrategyRef,
    boolean async
) throws APINGException
```

Place new orders into a market. In normal circumstances `placeOrders` is an atomic operation. **PLEASE NOTE:** if the 'Best Execution' feature is switched off, `placeOrders` can return `PROCESSED_WITH_ERRORS` meaning some bets can be rejected and others placed when submitted in the same instruction batch.

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketId` | String | yes | The market id these orders are to be placed on. |
| `instructions` | List<PlaceInstruction> | yes | Place instructions. **Limit: 200 per request for Global Exchange** (50 for Italian Exchange). |
| `customerRef` | String | no | Optional unique string (up to 32 chars) used to **de-dupe mistaken re-submissions**. Allowed chars: upper/lower, digits, `: - . _ + * : ; ~`. **De-duplication window is 60 seconds.** This field does NOT persist into the placeOrders response or Order Stream API — distinct from `customerOrderRef` (which sits inside the PlaceInstruction). |
| `marketVersion` | MarketVersion | no | Optional. Specify which version of the market the orders should be placed on. If the current market version is higher than the one sent, the bet will be lapsed. |
| `customerStrategyRef` | String | no | Reference to specify which strategy sent the order. Returned on order change messages through the stream API. **Limited to 15 characters.** Empty string treated as null. |
| `async` | boolean | no | Defaults to false. If true, orders are placed asynchronously. Track via Stream API or by providing `customerOrderRef`. Order status will be `PENDING` and no bet ID returned in the immediate response. Available for all bet types including Market on Close and Limit on Close. |

Returns: `PlaceExecutionReport`. Throws: `APINGException`.

## Order types and bet shapes

### Standard LIMIT bet

Specify `selectionId`, `side` (BACK/LAY), `orderType: LIMIT`, and a `limitOrder` containing `size`, `price`, `persistenceType`.

`persistenceType` values:
- **`LAPSE`** — unmatched portion cancelled at turn in-play.
- **`PERSIST`** — unmatched portion remains active in-play.
- **`MARKET_ON_CLOSE`** — bet matched at BSP.

### MARKET_ON_CLOSE (BSP)

`orderType: MARKET_ON_CLOSE` with `marketOnCloseOrder.liability` instead of size/price. Matched at Betfair Starting Price.

### LIMIT_ON_CLOSE (BSP with limit)

`orderType: LIMIT_ON_CLOSE` with `limitOnCloseOrder` containing `price` (minimum acceptable BSP) and `liability`. Matched at BSP only if BSP is at or better than the limit.

## Betting enhancements

### Fill or Kill

Set `timeInForce: "FILL_OR_KILL"` on a `limitOrder`. Optionally pass `minFillSize`. Exchange matches the order only if at least `minFillSize` (or whole order if not specified) can be matched. Unmatched portion is immediately cancelled.

**Important matching difference:** the price on a Fill or Kill order represents the **lower limit of the Volume Weighted Average Price** for the entire matched volume, not the lowest price for any fragment. So a FOK order at price 5.4, size 10 might match £2 @ 5.5, £6 @ 5.4, £2 @ 5.3.

### Market version parameter

Pass `marketVersion: { version: <int> }` to lapse the order if the market version has incremented past that point.

The market version is incremented on **any** market change. However, only "material" changes cause version-based rejection:
- Runner removal/addition (under suspension)
- Turn in-play
- Lapsing/voiding bets (e.g. football goal-driven market reformation)

Non-material changes (e.g. start time updates, tennis court time updates) increment the version but do NOT cause material-version rejection. Useful for betting right up to the off without inadvertently betting into in-play.

Rejection example response: `errorCode: BET_TAKEN_OR_LAPSED` inside an instruction report.

### Bet to Payout or Profit/Liability

Set `betTargetType: "PAYOUT"` or `"BACKERS_PROFIT"` and `betTargetSize` on a LimitOrder. Exchange matches to achieve the target payout/profit at the specified price or better. **Not enabled for `.it`, `.es`, `.dk`, `.se` jurisdictions.**

### Lower minimum stakes at larger prices

LIMIT bets below the per-currency Min Bet Size are valid if the payout would be ≥ Min Bet Payout (£10 for GBP). E.g. £1 @ 10, 10p @ 100, 1p @ 1000 are all valid. **LIMIT only.** Not enabled for `.it`, `.es`, `.dk`, `.se`.

### Each Way

Identifiable as `marketType=EACH_WAY` via `listMarketCatalogue`. **Liability is `size × 2`.** Each-way divisor returned via `MARKET_DESCRIPTION` MarketProjection.

Divisor table:

| Race Type | Number of Runners | Number of Places | Each-Way Divisor |
|---|---|---|---|
| Handicap | 16 or more | 4 | 1/4 |
| Handicap | 12 to 15 | 3 | 1/4 |
| Handicap | 8 to 11 | 3 | 1/5 |
| Handicap | 5 to 7 | 2 | 1/4 |
| Non-Handicap | 8 or more | 3 | 1/5 |
| Non-Handicap | 5 to 7 | 2 | 1/4 |

EW markets not offered if ≤ 4 runners at market creation. Number of runners is fixed at market creation time (Betfair Place market style, not Fixed Odds EW).

## Betfair price increments

**Odds Markets:**

| Price range | Increment |
|---|---|
| 1.01 → 2 | 0.01 |
| 2 → 3 | 0.02 |
| 3 → 4 | 0.05 |
| 4 → 6 | 0.1 |
| 6 → 10 | 0.2 |
| 10 → 20 | 0.5 |
| 20 → 30 | 1 |
| 30 → 50 | 2 |
| 50 → 100 | 5 |
| 100 → 1000 | 10 |

**Asian Handicap & Total Goal Markets:** 0.01 increment 1.01 → 1000.

Bet outside these increments → `INVALID_ODDS` error.

## Update protocol

Treat as immutable snapshot. If Betfair updates the upstream doc materially, capture a fresh dated snapshot rather than editing in place.

---

## 2.2 — cancelOrders

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687500/cancelOrders

# cancelOrders

**Source:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687491/cancelOrders
**Captured:** 2026-05-03 (Session 60).
**Last updated upstream:** Jun 04, 2024.

---

## Operation signature

```
CancelExecutionReport cancelOrders(
    String marketId,
    List<CancelInstruction> instructions,
    String customerRef
) throws APINGException
```

Cancel all bets OR cancel all bets on a market OR fully or partially cancel particular orders on a market. **Only LIMIT orders can be cancelled or partially cancelled once placed.**

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketId` | String | no | If `marketId` AND `betId` aren't supplied, **all bets are cancelled**. Concurrent requests to cancel all bets are rejected until the initial request completes. |
| `instructions` | List<CancelInstruction> | no | All instructions must be on the same market. If not supplied, all unmatched bets on the market (if marketId is passed) are fully cancelled. **Limit: 60 cancel instructions per request.** |
| `customerRef` | String | no | Optional unique string (up to 32 chars) for de-duplication of mistaken resubmissions. |

Returns: `CancelExecutionReport`. Throws: `APINGException`.

## Notes

- LIMIT-only — MARKET_ON_CLOSE and LIMIT_ON_CLOSE bets cannot be cancelled once placed.
- Three usage modes:
  1. **No marketId, no betId**: cancel all bets on the account.
  2. **marketId only**: cancel all unmatched bets on the market.
  3. **marketId + instructions**: cancel specific bets (full or partial cancel).
- Partial cancel via `sizeReduction` field on the CancelInstruction.

## Update protocol

Treat as immutable snapshot.

---

## 2.3 — replaceOrders

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687517/replaceOrders

# replaceOrders

**Source:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687487/replaceOrders
**Captured:** 2026-05-03 (Session 60).
**Last updated upstream:** Jun 04, 2024.

---

## Operation signature

```
ReplaceExecutionReport replaceOrders(
    String marketId,
    List<ReplaceInstruction> instructions,
    String customerRef,
    MarketVersion marketVersion,
    boolean async
) throws APINGException
```

**Logically a bulk cancel followed by a bulk place.** Cancel completes first, then new orders are placed.

- The new orders will be placed **atomically** — all or none.
- **If new orders cannot be placed, cancellations will NOT be rolled back.**

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `marketId` | String | yes | Market id these orders are placed on. |
| `instructions` | List<ReplaceInstruction> | yes | Replace instructions. **Limit: 60 per request.** |
| `customerRef` | String | no | Optional unique string (up to 32 chars) for de-duplication. |
| `marketVersion` | MarketVersion | no | Lapses orders if current market version is higher than supplied. |
| `async` | boolean | no | Defaults to false. **Not available for MOC or LOC bets.** Track via Stream API with `customerOrderRef`. |

Returns: `ReplaceExecutionReport`. Throws: `APINGException`.

## Critical semantics

The atomicity gap matters: if you ask to cancel 5 orders and place 5 new ones, and the new placement fails, the 5 cancellations have already happened and stay cancelled. You're left with 5 cancelled bets and no replacement bets. Application code must handle this case explicitly.

## Update protocol

Treat as immutable snapshot.

---

## 2.4 — updateOrders

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687525/updateOrders

**On-disk source:** `dr029/2_4_betfair_streaming/reference_guide/updateOrders.md`
**Captured:** between Sessions 65 and 66 (operator browser session, PDF export from authenticated session)

---

## Page 1

updateOrders
Operation
updateOrders
UpdateExecutionReportupdateOrders#updateOrders(StringmarketId , List<
UpdateInstruction >instructions ,StringcustomerRef )throws APINGException
Update non-exposure changing fields
Parameter
name
Type RequiredDescription
marketId String
 The market id these orders are to be
placed on
instructions List<
UpdateInstruction
>
The number of update instructions.  The
limit of update instructions per request is
60
customerRef String Optional parameter allowing the client to
pass a unique string (up to 32 chars) that
is used to de-dupe mistaken re-
submissions.
Return type Description
UpdateExecutionReport
Throws Description
APINGExceptionGeneric exception that is thrown if this operation fails for any reason.
Since 1.0.0

---

## 2.5 — Login & Session Management

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/ (Login & Session Management page)

**On-disk source:** `dr029/2_4_betfair_streaming/reference_guide/login_session_management.md`
**Captured:** between Sessions 65 and 66 (operator browser session, PDF export from authenticated session)

---

## Page 1

Login & Session Management
Home | API Status | Historical Data | Vendor Program | Developer Forum
Login & Session Management
Login | Login Method Summary | Keep Alive | Logout
Login
The Betfair API offers three login flows for developers, depending on the use case for your
application.
All API requests should be sent as POST.
Non-Interactive login
If you are building an application that will run autonomously, there is a separate login flow to
follow to ensure your account remains secure.
Interactive login
If you are building an application that will be used interactively, then this is the flow for you. This
flow has two variants:
Interactive login - Desktop Application
This login flow makes use of Betfair's login pages and allows your app to gracefully handle all
errors and redirections in the same way as the Betfair website. 
Interactive login - API method
This flow makes use of a JSON API endpoint and is the simplest way to get started if you are
looking to create your own login form.
If you're looking for the quickest way to get started, try the curl example in the Interactive
login - API Method.

## Page 2

Login Request Limits
Login Method Summary
Login
Type
Use Case Method Pros Cons Recommendatio
Non-
interactive
Login
Applications
running
autonomously
(e.g., bots).
Non-
interactive
endpoint
with SSL
certificate.
Secure for
automation.
Recommended
for bots.
Requires
certificate
setup.
✅  Use if your app
runs without user
interaction (e.g.,
bots, scheduled
tasks).
Interactive
Login –
API Login
Applications
needing a
simple
integration
with minimal
development
time.
API login
endpoint
(username
+
password,
or
username
+
password
+ 2FA if
enabled).
Easiest to
implement.
Good for most
apps.
Less flexible
for handling
edge cases
compared to
the
embedded
login page.
✅  Use if you wan
quick setup and
donʼt need T&Cs o
jurisdiction
workflows.
Interactive
Login –
Desktop
App
Applications
used
interactively
by a wide
range of users.
Embedded
Betfair
login
pages.
Handles
workflows like
T&Cs updates
and
jurisdiction
checks. More
flexible for 3rd
party apps.
Requires
embedding
Betfairʼs
login page.
More
development
effort
compared to
API login.
✅  Use if your app
is for many users
and must handle
extra workflows
securely.
Keep Alive
You can use Keep-Alive to extend the session timeout period.


## Page 3

On the international (.com) Exchange the current session expiry time is 12 hours for all
customers (excluding UK & Ireland) and 24 hours for UK & Ireland customers.
The session expiry time is currently 20 minutes on the Italian & Spanish Exchange.
You should request Keep Alive within this time to prevent session expiry. If you don't call Keep
Alive within the specified timeout period, the session will expire.
Session times aren't determined or extended based on API activity.
Please note: You can configure the timeout via My Account > Logout Preferences if required
Headers
Name Description Sample
Accept (mandatory) Header that signals that
the response should be
returned as JSON
application/json
X-Authentication (mandatory) Header that represents
the session token that
needs to be keep alive
Session Token
X-Application (optional) Header the Application
Key used by the
customer to identify the
product.
App Key
The presence of the "Accept: application/json" header will signal that the service should
respond with JSON and not an HTML page
URL Definition (Global)
https://identitysso.betfair.com/api/keepAlive
Other Jurisdictions
Please use the below if your country of residence is in one of the list jurisdictions.
Jurisdiction Endpoint
Australia & New Zealand https://identitysso.betfair.au/api/keepAlive
Italy https://identitysso.betfair.it/api/keepAlive

## Page 4

Spain https://identitysso.betfair.es/api/keepAlive
Romania https://identitysso.betfair.ro/api/keepAlive
Parameters
 The Keep-Alive operation requires no parameters.
Response structure
{
  "token":"<token_passed_as_header>",
  "product":"product_passed_as_header",
  "status":"<status>",
  "error":"<error>"
}
Status values
SUCCESS
FAIL
Error values
INPUT_VALIDATION_ERROR
INTERNAL_ERROR
NO_SESSION
Call sample
Request
curl -k -i -H "Accept: application/json"-H "X-Application: AppKey"-
H "X-Authentication: <token>"https://identitysso.betfair.com/api/keepAlive
Response

## Page 5

curl -k -i -H "Accept: application/json"-H "X-Application: AppKey"-
H "X-Authentication: SESSIONTOKEN"https://identitysso.betfair.com/api/keepAlive
{
  "token":"SESSIONTOKEN",
  "product":"AppKey",
  "status":"SUCCESS",
  "error":""
}
Logout
You can use Logout to terminate your existing session.
URL Definition
The presence of the "Accept: application/json" header will signal that the service should
respond with JSON and not an HTML page
Headers
Name Description Sample
Accept (mandatory) Header that signals that
the response should be
returned as JSON
application/json
X-Authentication (mandatory) Header that represents
the session token
created at login.
Session Token
https://identitysso.betfair.com/api/logout

## Page 6

X-Application (optional) Header the Application
Key used by the
customer to identify the
product.
App Key
Response structure
{
  "token":"<token_passed_as_header>",
  "product":"product_passed_as_header",
  "status":"<status>",
  "error":"<error>"
}
Status values
SUCCESS
FAIL
Error values
INPUT_VALIDATION_ERROR
INTERNAL_ERROR
NO_SESSION
Call sample
# full request
curl -k -i -H "Accept: application/json"-H "X-Application: AppKey"-
H "X-Authentication: <token>"https://identitysso.betfair.com/api/logout
Login | Login Method Summary | Keep Alive | Logout

## Page 7

---

## 2.6 — Betting Enums

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/ (Betting Enums page)

**On-disk source:** `dr029/2_4_betfair_streaming/reference_guide/betting_enums.md`
**Captured:** between Sessions 65 and 66 (operator browser session, PDF export from authenticated session)

---

## Page 1

Betting Enums
Enums
MarketProjection
Value Description
COMPETITION If not selected then the competition will not be returned with
marketCatalogue
EVENT If not selected then the event will not be returned with
marketCatalogue
EVENT_TYPE If not selected then the eventType will not be returned with
marketCatalogue
MARKET_START_TIME If not selected then the start time will not be returned with
marketCatalogue
MARKET_DESCRIPTIONIf not selected then the description will not be returned with
marketCatalogue
RUNNER_DESCRIPTIONIf not selected then the runners will not be returned with
marketCatalogue
RUNNER_METADATA If not selected then the runner metadata will not be returned with
marketCatalogue. If selected then RUNNER_DESCRIPTION will
also be returned regardless of whether it is included as a market
projection.
PriceData
Value Description
SP_AVAILABLE Amount available for the BSP auction.

## Page 2

SP_TRADED Amount traded in the BSP auction.
EX_BEST_OFFERSOnly the best prices available for each runner, to requested price depth.
EX_ALL_OFFERSEX_ALL_OFFERS trumps EX_BEST_OFFERS if both settings are present
EX_TRADED Amount traded on the exchange.
MatchProjection
Value Description
NO_ROLLUP No rollup, return raw fragments
ROLLED_UP_BY_PRICE Rollup matched amounts by distinct matched prices per side.
ROLLED_UP_BY_AVG_PRICERollup matched amounts by average matched price per side
OrderProjection
Value Description
ALL EXECUTABLE and EXECUTION_COMPLETE orders
EXECUTABLE An order that has a remaining unmatched portion. This is either a
fully unmatched or partially matched bet (order)
EXECUTION_COMPLETEAn order that does not have any remaining unmatched portion.
 This is a fully matched bet (order).
MarketStatus
Value Description

## Page 3

INACTIVE The market has been created but isn't yet available.
OPEN The market is open for betting.
SUSPENDED The market is suspended and not available for betting.
CLOSED The market has been settled and is no longer available for betting.
RunnerStatus
Value Description
ACTIVE ACTIVE
WINNER WINNER
LOSER LOSER
PLACED The runner was placed, applies to EACH_WAY marketTypes only.
REMOVED_VACANTREMOVED_VACANT applies to Greyhounds. Greyhound markets
always return a fixed number of runners (traps). If a dog has been
removed, the trap is shown as vacant.
REMOVED REMOVED
HIDDEN The selection is hidden from the market.  This occurs in Horse Racing
markets were runners is hidden when it is doesnʼt hold an official entry
following an entry stage. This could be because the horse was never
entered or because they have been scratched from a race at a
declaration stage. All matched customer bet prices are set to 1.0 even
if there are later supplementary stages. Should it appear likely that a
specific runner may actually be supplemented into the race this
runner will be reinstated with all matched customer bets set back to
the original prices.

## Page 4

TimeGranularity
Value Description
DAYS
HOURS
MINUTES
Side
ValueDescription
BACKTo back a team, horse or outcome is to bet on the selection to win. For LINE
markets a Back bet refers to a SELL line. A SELL line will win if the outcome
is LESS THAN the taken line (price)  
LAYTo lay a team, horse, or outcome is to bet on the selection to lose. For LINE markets
a Lay bet refers to a BUY line. A BUY line will win if the outcome is MORE THAN the
taken line (price) 
OrderStatus
Value Description
PENDING An asynchronous order is yet to be processed. Once the bet has
been processed by the exchange 
(including waiting for any in-play delay), the result will be
reported and available on the 
Exchange Stream API and API NG. 
Not a valid search criteria on MarketFilter
EXECUTION_COMPLETEAn order that does not have any remaining unmatched portion.

## Page 5

EXECUTABLE An order that has a remaining unmatched portion.
EXPIRED The order is no longer available for execution due to its time in
force constraint. 
In the case of FILL_OR_KILL orders, this means the order has
been killed because it could not be filled to your specifications. 
Not a valid search criteria on MarketFilter
OrderBy
Value Description
BY_BET @Deprecated Use BY_PLACE_TIME instead. Order by placed time,
then bet id.
BY_MARKET Order by market id, then placed time, then bet id.
BY_MATCH_TIMEOrder by time of last matched fragment (if any), then placed time, then
bet id. Filters out orders which have no matched date. The dateRange
filter (if specified) is applied to the matched date.
BY_PLACE_TIME Order by placed time, then bet id. This is an alias of to be deprecated
BY_BET. The dateRange filter (if specified) is applied to the placed
date.
BY_SETTLED_TIMEOrder by time of last settled fragment (if any due to partial market
settlement), then by last match time, then placed time, then bet id.
Filters out orders which have not been settled. The dateRange filter (if
specified) is applied to the settled date.
BY_VOID_TIME Order by time of last voided fragment (if any), then by last match time,
then placed time, then bet id. Filters out orders which have not been
voided. The dateRange filter (if specified) is applied to the voided date.

## Page 6

SortDir
Value Description
EARLIEST_TO_LATESTOrder from earliest value to latest e.g. lowest betId is first in the
results.
LATEST_TO_EARLIESTOrder from the latest value to the earliest e.g. highest betId is first
in the results.
OrderType
Value Description
LIMIT A normal exchange limit order for immediate execution
LIMIT_ON_CLOSE Limit order for the auction (SP)
MARKET_ON_CLOSE Market order for the auction (SP)
MarketSort
Value Description
MINIMUM_TRADED Minimum traded volume
MAXIMUM_TRADED Maximum traded volume
MINIMUM_AVAILABLE Minimum available to match
MAXIMUM_AVAILABLE Maximum available to match
FIRST_TO_START The closest markets based on their expected start time
LAST_TO_START The most distant markets based on their expected start time

## Page 7

MarketBettingType
Value Description
ODDS Odds Market - Any market that doesn't fit any any of
the below categories.
LINE Line Market - LINE markets operate at even-money
odds of 2.0. However, price for these markets refers to
the line positions available as defined by the markets
min-max range and interval steps. Customers either
Buy a line (LAY bet, winning if outcome is greater than
the taken line (price)) or Sell a line (BACK bet, winning
if outcome is less than the taken line (price)). If settled
outcome equals the taken line, stake is returned. 
RANGE Range Market - Now Deprecated
ASIAN_HANDICAP_DOUBLE_LINEAsian Handicap Market - A traditional Asian handicap
market. Can be identified by marketType
ASIAN_HANDICAP
ASIAN_HANDICAP_SINGLE_LINEAsian Single Line Market - A market in which there can
be 0 or multiple winners. e,.g marketType
TOTAL_GOALS
FIXED_ODDS Sportsbook Odds Market. This type is deprecated and
will be removed in future releases, when Sportsbook
markets will be represented as ODDS market but with
a different product type
ExecutionReportStatus
Value Description

## Page 8

SUCCESS Order processed successfully
FAILURE Order failed.
PROCESSED_WITH_ERRORSThe order itself has been accepted, but at least one
(possibly all) actions have generated errors. This error only
occurs for replaceOrders, cancelOrders and updateOrders
operations.
In normal circumstances the
/wiki/spaces/BFAPIBETA/pages/1212454 operation will not
return PROCESSED_WITH_ERRORS status as it is an atomic
operation.  PLEASE NOTE: if the 'Best Execution' features is
switched off, placeOrders can return
‘PROCESSED_WITH_ERRORSʼ meaning that some bets can
be rejected and other placed when submitted in the same
PlaceInstruction
TIMEOUT The order timed out & the status of the bet is unknown. If
a TIMEOUT error occurs on
a placeOrders/replaceOrders request, you should
check listCurrentOrders to verify the status of your bets
before placing further orders. Please Note: Timeouts will
occur after 5 seconds of attempting to process the bet but
please allow up to 15 seconds for a timed out order to
appear. After this time any unprocessed bets will
automatically be Lapsed and no longer be available on the
Exchange.
ExecutionReportErrorCode
Value Description
ERROR_IN_MATCHER The matcher is not healthy. Please note: The error
will also be returned is you attempt concurrent

## Page 9

'cancel all' bets requests using cancelOrders which
isn't permitted.
PROCESSED_WITH_ERRORS The order itself has been accepted, but at least one
(possibly all) actions have generated errors
BET_ACTION_ERROR There is an error with an action that has caused the
entire order to be rejected. Check the
instructionReports errorCode for the reason for the
rejection of the order.
INVALID_ACCOUNT_STATE Order rejected due to the account's status
(suspended, inactive, dup cards)
INVALID_WALLET_STATUS Order rejected due to the account's wallet's status
INSUFFICIENT_FUNDS Account has exceeded its exposure limit or available
to bet limit
LOSS_LIMIT_EXCEEDED The account has exceed the self imposed loss limit
MARKET_SUSPENDED Market is suspended
MARKET_NOT_OPEN_FOR_BETTINGMarket is not open for betting. It is either not yet
active, suspended or closed awaiting settlement.
DUPLICATE_TRANSACTION Duplicate customer reference data submitted -
Please note: There is a time window associated with
the de-duplication of duplicate submissions which is
60 second
INVALID_ORDER Order cannot be accepted by the matcher due to the
combination of actions. For example, bets being
edited are not on the same market, or order includes
both edits and placement
INVALID_MARKET_ID Market doesn't exist
PERMISSION_DENIED Business rules do not allow order to be placed. You
are either attempting to place the order using a
Delayed Application Key or from a restricted
jurisdiction (i.e. USA)

## Page 10

DUPLICATE_BETIDS Duplicate bet ids found. For example, you've
included the same betId more than once in a single
cancelOrders request.
NO_ACTION_REQUIRED Order hasn't been passed to matcher as system
detected there will be no state change
SERVICE_UNAVAILABLE The requested service is unavailable
REJECTED_BY_REGULATOR The regulator rejected the order. On the Italian
Exchange this error will occur if more than 50 bets
are sent in a single placeOrders request.
NO_CHASING A specific error code that relates to Spanish
Exchange markets only which indicates that the bet
placed contravenes the Spanish regulatory rules
relating to loss chasing.
REGULATOR_IS_NOT_AVAILABLE The underlying regulator service is not available.
TOO_MANY_INSTRUCTIONS The amount of orders exceeded the maximum
amount allowed to be executed
INVALID_MARKET_VERSION The supplied market version is invalid. Max length
allowed for market version is 12.
INVALID_PROFIT_RATIO The order falls outside the permitted price and size
combination.
NO_CHANGE Trying to update the persistence type to the one it
already has.
PersistenceType
Value Description
LAPSE Lapse (cancel) the order automatically when the market is turned
in play if the bet is unmatched

## Page 11

PERSIST Persist the unmatched order to in-play. The bet will be placed
automatically into the in-play market at the start of the event. 
Once in play, the bet won't be cancelled by Betfair if a material
event takes place and will be available until matched or cancelled
by the user
MARKET_ON_CLOSE Put the order into the auction (SP) at turn-in-play
InstructionReportStatus
Value Description
SUCCESSThe instruction was successful.
FAILUREThe instruction failed.
TIMEOUTThe order timed out & the status of the bet is unknown. If a TIMEOUT error
occurs on a placeOrders/replaceOrders request, you should
check listCurrentOrders to verify the status of your bets before placing further
orders. Please Note: Timeouts will occur after 5 seconds of attempting to
process the bet but please allow up to 15 seconds for a timed out order to
appear. After this time any unprocessed bets will automatically be Lapsed and
no longer be available on the Exchange.
InstructionReportErrorCode
Value Description
INVALID_BET_SIZE bet size is invalid for your currency or yo
INVALID_RUNNER Runner does not exist, includes vacant tr
racing

## Page 12

BET_TAKEN_OR_LAPSED Bet cannot be cancelled or modified as i
taken or has been cancelled/lapsed Incl
cancel/modify market on close BSP bets
on close BSP bets. The error may be retu
placeOrders request if for example a bet
point when a market admin event takes p
turned in-play). 
The error will also be returned if a marke
submitted and a material change has tak
bet was submitted causing the bet to be
BET_IN_PROGRESS No result was received from the matche
configured for the system
RUNNER_REMOVED Runner has been removed from the even
MARKET_NOT_OPEN_FOR_BETTING Attempt to edit a bet on a market that ha
LOSS_LIMIT_EXCEEDED The action has caused the account to ex
imposed loss limit
MARKET_NOT_OPEN_FOR_BSP_BETTING Market now closed to bsp betting. Turne
been reconciled
INVALID_PRICE_EDIT Attempt to edit down the price of a bsp l
or edit up the price of a limit on close ba
INVALID_ODDS Odds not on price ladder - either edit or 
INSUFFICIENT_FUNDS Insufficient funds available to cover the 
exposure limit or available to bet limit wo
INVALID_PERSISTENCE_TYPE Invalid persistence type for this market, 
in-play market or KEEP for markets with 
betDelayModels.
ERROR_IN_MATCHER A problem with the matcher prevented th
completing successfully
INVALID_BACK_LAY_COMBINATION The order contains a back and a lay for t
overlapping prices. This would guarantee
also applies to BSP limit on close bets

## Page 13

ERROR_IN_ORDER The action failed because the parent ord
INVALID_BID_TYPE Bid type is mandatory
INVALID_BET_ID Bet for id supplied has not been found
CANCELLED_NOT_PLACED Bet cancelled but replacement bet was n
RELATED_ACTION_FAILED Action failed due to the failure of a action
action is dependent
NO_ACTION_REQUIRED the action does not result in any state ch
persistence to it's current value
TIME_IN_FORCE_CONFLICT You may only specify a time in force on e
request OR on individual limit order instr
since the implied behaviors are incompa
UNEXPECTED_PERSISTENCE_TYPE You have specified a persistence type fo
order, which is nonsensical because no u
can remain after the order has been plac
INVALID_ORDER_TYPE You have specified a time in force of FIL
have included a non-LIMIT order type.
UNEXPECTED_MIN_FILL_SIZE You have specified a minFillSize on a lim
limit order's time in force is not FILL_OR_
Using minFillSize is not supported where
the request (as opposed to an order) is F
INVALID_CUSTOMER_ORDER_REF The supplied customer order reference i
INVALID_MIN_FILL_SIZE The minFillSize must be greater than zer
equal to the order's size. 
The minFillSize cannot be less than the m
your currency
BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGEYour bet is lapsed. There is better odds t
available in the market, but your 
preferences don't allow the system to m
against better odds. Change your betting
preferences to accept better odds if you
receive this error. Please see

## Page 14

https://support.betfair.com/app/answe
for more details regarding Best Execut
update your settings.
GroupBy
Value Description
EVENT_TYPEA roll up of settled P&L, commission paid and number of bet orders, on a
specified event type
EVENT A roll up of settled P&L, commission paid and number of bet orders, on a
specified event
MARKET A roll up of settled P&L, commission paid and number of bet orders, on a
specified market
SIDE An averaged roll up of settled P&L, and number of bets, on the specified side
of a specified selection within a specified market, that are either settled or
voided
BET The P&L, side and regulatory information etc, about each individual bet order.
BetStatus
Value Description
SETTLED A matched bet that was settled normally

## Page 15

VOIDED A matched bet that was subsequently voided by Betfair, before, during or
after settlement
LAPSED Unmatched bet that was cancelled by Betfair (for example at turn in play).
CANCELLEDUnmatched bet that was cancelled by an explicit customer action.
marketType - Legacy Data
Value Description
A Asian Handicap
L Line market
O Odds market
R Range market.
NOT_APPLICABLE The market does not have an applicable marketType.
TimeInForce
Value Description
FILL_OR_KILLExecute the transaction immediately and completely (filled to size or
between minFillSize and size) or not at all (cancelled).
For LINE markets Volume Weighted Average Price (VWAP) functionality is
disabled
BetTargetType

## Page 16

Value Description
BACKERS_PROFITThe payout requested minus the calculated size at which this
LimitOrder is to be placed. BetTargetType bets are invalid for LINE
markets
PAYOUT The total payout requested on a LimitOrder
PriceLadderType
Value Description
CLASSIC Price ladder increments traditionally used for Odds Markets.
FINEST Price ladder with the finest available increment, traditionally used for 
Asian Handicap markets.
LINE_RANGEPrice ladder used for LINE markets. Refer to MarketLineRangeInfo for more
details.
BetDelayModel
Value Description
PASSIVEFor in-play markets where betDelay > 0, orders that are guaranteed not to
match immediately are accepted straight away, bypassing the bet delay wait.
Order requirements (otherwise bets will be subject to the usual bet delay before
being placed).
Only plain LIMIT orders are supported.
Allowed persistenceType: LAPSE
The following attributes are not supported and must be omitted: timeInForce,
minFillSize, betTargetType

## Page 17

DYNAMICIndicates market is subject to dynamic in-play bet delays. This mean that the
in-play betDelay will vary while the market is turned in-play.
Please note: Currently returned for Tennis markets only. Specifically, every
game 3,5,7,9,11 or game which decides a set (potentially 6,8,10,12) the betDelay
is reduced to 1 second.

---

## 2.7 — Betting Exceptions

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/ (Betting Exceptions page)

**On-disk source:** `dr029/2_4_betfair_streaming/reference_guide/betting_exceptions.md`
**Captured:** between Sessions 65 and 66 (operator browser session, PDF export from authenticated session)

---

## Page 1

Betting Exceptions
Exceptions
APINGException
This exception is thrown when an operation fails
Error code Description
TOO_MUCH_DATA The operation requested too much data, exceeding the Market Data
Request Limits. You must adjust your request parameters to stay with the
documented limits.
INVALID_INPUT_DATA The data input is invalid. A specific description is returned via
errorDetails as shown below.  Please note: if the number of placeOrders,
updateOrders, replaceOrders, or cancelOrders instructions exceeds the
documented limit you will also receive this error.
INVALID_SESSION_INFORMATIONThe session token hasn't been provided, is invalid or has expired. Login
again to create a new session
NO_APP_KEY An application key header ('X-Application') has not been provided in the
request.
NO_SESSION A session token header ('X-Authentication') has not been provided in the
request
UNEXPECTED_ERROR An unexpected internal error occurred that prevented successful request
processing.
INVALID_APP_KEY The application key passed is invalid or is not present
TOO_MANY_REQUESTS There are too many pending (in-flght) requests e.g. a listMarketBook
with Order/Match projections is limited to 3 concurrent requests. The
error also applies to:
listCurrentOrders, listMarketProfitAndLoss and listClearedOrders if
you have 3 or more requests currently in execution.
placeOrders, cancelOrders./wiki/spaces/BFAPIBETA/pages/1212452,
/wiki/spaces/BFAPIBETA/pages/1212456 if the number of transactions
(instructions) submitted exceeds 1000 in a single second.
For more details relating to this error please see FAQ's
SERVICE_BUSY The service is currently too busy to service this request.
TIMEOUT_ERROR The Internal call to downstream service timed out. Please note: If
a TIMEOUT error occurs on a placeOrders/replaceOrders request, you

## Page 2

should check listCurrentOrders to verify the status of your bets before
placing further orders. Please Note: Timeouts will occur after 5 seconds
of attempting to process the bet but please allow up to 15 seconds for a
timed out order to appear. After this time any unprocessed bets will
automatically be Lapsed and no longer be available on the Exchange.
REQUEST_SIZE_EXCEEDS_LIMIT The request exceeds the request size limit. Requests are limited to a total
of 250 betIdʼs/marketIdʼs (or a combination of both).
ACCESS_DENIED The calling client is not permitted to perform the specific action e.g. they
have an App Key restriction in place or attempting to place a bet from a
restricted jurisdiction.
Other
parameters
Type RequiredDescription Values
errorDetails String the stack trace of the
error
"market id passed is invalid"
"locale must use valid iso-639 locale names"
"currency must use valid iso2 currency code
name"
"country code must use valid iso2 country code
name"
"text query has invalid content"
"language must use valid iso language name"
requestUUIDString
Generic JSON-RPC Exceptions
Error
Code
Description
-32700Invalid JSON was received by the server. An error occurred on the server while parsing the JSON
text.
-32601Method not found
-32602Problem parsing the parameters, or a mandatory parameter was not found
-32603Internal JSON-RPC error

---

## 2.8 — Best Practice

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687480/Best+Practice

# Best Practice

**Source:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687730/Best+Practice
**Last upstream update:** Jun 13, 2024
**Captured:** Session 61, 2026-05-03 ACST, via web_fetch

---

## Sections

Development & Testing | Login & Session Management | General Tips | API Status |
Expect: 100 - Continue Header | Enabling HTTP Compression | HTTP Persistent Connection |
Other Performance Tips

---

## Development & Testing

You should use the **Delayed Application Key** for any initial development and functional
testing. Historical data is made available via https://historicdata.betfair.com/#/home
for strategy modelling & analysis.

Only apply for Live Application Key access once you are ready to start transacting on the
Exchange using your Live Application Key.

See the **Personal Betting Access Overview** (Application Keys page) for more details
regarding the difference between Delayed and Live Application Keys.

---

## Login & Session Management

Use **Login** to create a new session and **Keep Alive** to extend the session beyond the
session expiry time. A single session can and should be used across multiple API
calls/threads simultaneously.

Notes:

- Login sessions last up to **24 hours by default** and you can use Keep Alive to extend
  the session beyond the stated session expiry time. **The maximum session length varies
  by country** — further details on the Login & Session Management page.
- A single session can be used across multiple API calls/threads simultaneously. **You
  don't need to make a new login request for every API call.**
- You should ensure that you handle the **INVALID_SESSION_TOKEN** error within your code
  by creating a new session token via the API login method.
- If **login limits** are exceeded, you'll be automatically prevented from making further
  login requests for a period of **20 minutes**. During this time all existing sessions
  will remain valid.

---

## General Tips

- Make the minimal number of transactions/changes possible when transacting. See
  **Transaction Charges** details on the Betfair website.
- Observe the **Market Data Request Limits** when making requests to listMarketCatalogue,
  listRunnerBook, listMarketBook and listMarketProfitandLoss. (See
  `market_data_request_limits.md`.)
- Always prefer leaving an order in place rather than cancelling/re-placing it — stay at
  the front of the queue to be matched.
- **Use the Stream API instead of polling wherever possible**, particularly if you are
  running a high-frequency trading application.
- Log as much as possible to aid queries/problem investigation (especially the
  `connectionId` from the Connection/ConnectionMessage when using the Stream API).
- Make use of the available **betting enhancements** (see placeOrders Betting
  Enhancements section).

---

## API Status

Use the API status page http://status.developer.betfair.com/ to check the health of the
API.

The API Status:

- Measures response latency and error rate against a number of operations every second.
- Automatically toggles the status page if certain thresholds are breached.

Check the API status before contacting Developer Support regarding API problems.

---

## Expect: 100 - Continue Header

Sending this header will result in the error: **"The remote server returned an error:
(417) Expectation Failed."**

If using the .Net Framework, set the relevant property in the ServicePointManager which
prevents the "Expect" header from being added:

```
System.Net.ServicePointManager.Expect100Continue = false;
```

---

## Enabling HTTP Compression

HTTP compression is built into both web servers and web clients to reduce the number of
bytes transmitted in an HTTP response. This makes better use of available bandwidth and
increases performance while reducing download time. When enabled, HTTP protocol data is
compressed before it is sent from the server. Clients capable of receiving compressed
HTTP data announce that they support compression in the HTTP header.

The Betfair API uses HTTP to handle communication between API clients and servers. JSON
messages can be compressed using the same HTTP compression used by web browsers. Custom
API applications may need modification to take advantage of this feature: they need to
send an additional HTTP header to indicate they support receipt of compressed responses
from the API. Some environments require explicit decompression of the response.

**Recommendation:** all Betfair API requests are sent with the
`Accept-Encoding: gzip, deflate` request header.

---

## HTTP Persistent Connection

**Recommendation:** the `Connection: keep-alive` header is set for all requests to
guarantee a persistent connection and reduce latency.

**Idle keep-alive connections to the API endpoints are closed every 3 minutes.**

Although maintaining long-lived connections is actively encouraged (for the Stream API
for example), Betfair cannot guarantee that keep-alive connections won't be forcibly
closed. **All customers must ensure they have reconnection logic in place** to handle any
connection termination scenarios.

---

## Other Performance Tips

Additional advice on optimising HTTPClient performance:
https://httpd.apache.org/docs/2.4/misc/perf-tuning.html

---

## 2.9 — Market Data Request Limits

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/ (operator to confirm exact URL).

# Market Data Request Limits

**Source:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687478/Market+Data+Request+Limits
**Last upstream update:** May 21, 2025
**Captured:** Session 61, 2026-05-03 ACST, via web_fetch

---

## What are Market Data Request Limits?

Although you can request multiple markets from `listMarketBook`, `listRunnerBook`,
`listMarketCatalogue` and `listMarketProfitandLoss`, there are limits on the amount of
data requested **in one request**.

**`sum(Weight) * number market ids` must not exceed 200 points per request.**

The tables below explain the "weighting" of data for each `MarketProjection` or
`PriceProjection`. If the maximum weighting of 200 points is exceeded, the API returns a
**`TOO_MUCH_DATA`** error.

---

## listMarketCatalogue

| MarketProjection      | Weight |
|-----------------------|--------|
| `MARKET_DESCRIPTION`  | 1      |
| `RUNNER_DESCRIPTION`  | 0      |
| `EVENT`               | 0      |
| `EVENT_TYPE`          | 0      |
| `COMPETITION`         | 0      |
| `RUNNER_METADATA`     | 1      |
| `MARKET_START_TIME`   | 0      |

---

## listMarketBook / listRunnerBook

| PriceProjection                  | Weight |
|----------------------------------|--------|
| Null (no PriceProjection set)    | 2      |
| `SP_AVAILABLE`                   | 3      |
| `SP_TRADED`                      | 7      |
| `EX_BEST_OFFERS`                 | 5      |
| `EX_ALL_OFFERS`                  | 17     |
| `EX_TRADED`                      | 17     |

**Combination weights** — specific combinations carry weights that are not the sum of
the individual weights:

| PriceProjection                  | Weight |
|----------------------------------|--------|
| `EX_BEST_OFFERS` + `EX_TRADED`   | 20     |
| `EX_ALL_OFFERS` + `EX_TRADED`    | 32     |

If `exBestOffersOverrides` is used, the weight is calculated by
`weight * (requestedDepth / 3)`.

---

## listMarketProfitandLoss

| PriceProjection   | Weight |
|-------------------|--------|
| Not applicable    | 4      |

---

## Example arithmetic (for §2.4 brief reference)

- 10 markets at `EX_BEST_OFFERS`: `5 * 10 = 50` → within budget.
- 10 markets at `EX_ALL_OFFERS`: `17 * 10 = 170` → within budget.
- 12 markets at `EX_ALL_OFFERS`: `17 * 12 = 204` → exceeds 200 → `TOO_MUCH_DATA`.
- 10 markets at `EX_BEST_OFFERS + EX_TRADED`: `20 * 10 = 200` → at limit.
- 6 markets at `EX_ALL_OFFERS + EX_TRADED`: `32 * 6 = 192` → within budget.
- 7 markets at `EX_ALL_OFFERS + EX_TRADED`: `32 * 7 = 224` → exceeds 200.
- 10 markets at `EX_BEST_OFFERS` with `exBestOffersOverrides` requesting depth 6:
  `5 * (6 / 3) * 10 = 100` → within budget.

---

## 2.10 — Betfair Starting Price Betting (BSP)

**Source URL:** https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/ (Betfair Starting Price Betting page)

**On-disk source:** `dr029/2_4_betfair_streaming/reference_guide/betfair_starting_price_betting.md`
**Captured:** between Sessions 65 and 66 (operator browser session, PDF export from authenticated session)

---

## Page 1

Betfair Starting Price Betting (BSP)
The Betfair Starting Price will be determined by balancing bets from customers who want to
back and lay at Starting Price and matching into the Betfair exchange markets to balance out
any residual demand.
The Betfair Starting Price will be calculated exactly to ensure the fairest and most transparent
odds possible for both backers and layers. The BSP does not need to account for a profit margin
but instead is calculated at the start of an event by looking at the relationship between the
amounts of money requested at SP by opposing betting parties. To give an even more accurate
price, we will use money where possible that is trading on the exchange at the start of the event.
This gives a true reflection of public opinion on a selection.
How is the BSP calculated?
The Near Price is based on money currently on the site at SP as well as unmatched money on
the same selection in the exchange. To understand this properly, you first need to understand
the calculation of the Far Price, which only takes into account the SP bets that have been made.
The Far Price is not as complicated but not as accurate and only accounts for money on the site
at SP.
Excluding money requested at a fixed price on the exchange, if there are £1000 worth of
backers stakes on a selection at SP and £6000 worth of layers liability, we can return an SP at
the start of the event of 6/1 (7.0).
If however there were £6000 worth of backers stakes on the selection and £1000 worth of
layers liability, we would return an SP of 1/6 (1.17). These are calculations of the Far Price.
The calculation of the final starting price occurs when the market is turned in-play. This is when
the market is reconciled. 
Further information and detailed working demonstrating how the Betfair SP price is calculated
can be found via https://promo.betfair.com/betfairsp/FAQs_theBasics.html

---

# Section 3 — Racing API (§2.4-relevant scope)

**Source:** OpenAPI 3.1.0 specification, version 1.4.3, on disk at `/Users/tim/Desktop/Projects/bethub-rebuild/openapi.json`.

**Documentation homepage (browser):** https://api.theracingapi.com/documentation

**Scope of this section.** The Racing API has 58 endpoints covering racecards, results, runner/jockey/trainer/owner/sire/dam/damsire pedigree analysis, plus regional meet endpoints for Australia and North America. This summary is bounded to what the §2.4 Betfair Streaming brief depends on — race/runner identity reconciliation between Betfair and Racing API, plus the BSP timing carry-in logic that uses Racing API data as one of two inputs. The Racing API's broader pedigree-analysis surface is out of scope for this review.

**What the Racing API is, in operator language.** The Racing API is a metadata service for global thoroughbred and harness racing. For Australian racing specifically, it provides race meets, race details, runner fields (horse, jockey, trainer), starting odds, and post-race results — keyed by the Racing API's own internal identifiers (meet_id, race_id, horse_id, etc.). It is the analytical-line counterpart to the Betfair Exchange API for race metadata. Where Betfair owns market and price truth, the Racing API owns runner / race / result truth.

**Authentication.** HTTP Basic auth (RFC 7617). Username and password supplied in the Authorization header per request. Credentials are operator-side configuration; not in scope for this review.

**Rate limits.** Per-endpoint rate limits embedded in the description text of each endpoint. Most endpoints relevant to §2.4 are **5 requests per second** (the Australian meets, races, and results endpoints all sit at this limit). The `/v1/courses/regions` endpoint sits at 1 request per second.

**Plan-tier accessibility.** Endpoints carry plan-tier annotations (Free / Basic / Standard / Pro). The Australian-specific endpoints require the **Australia regional add-on** (£49.99/month) on top of any base plan. Historical access beyond 12 months requires a one-time Australia database historical races add-on (£249).

---

## 3.1 — §2.4-relevant endpoints

The §2.4 brief touches the Racing API at three points: race metadata for the operational layer (when a race is happening, what the runners are, what their starting numbers are), result data for settlement reconciliation, and identity reconciliation against Betfair markets (the brief's §13/§14 BSP timing carry-in and §6 subscription shape both depend on linking a Racing API race to a Betfair market).

The endpoints below are the primary contact points.

### `/v1/australia/meets`

GET. Lists Australian race meets within a date range — up to 12 months in the past and 7 days in the future on the base subscription. Optional `date` query parameter scopes to a specific date.

**Min plan:** Free + Australia regional add-on. **Rate limit:** 5 requests per second.

**Response shape:** array of `Meet` objects with fields: `course` (string), `course_id` (string), `date` (string, ISO date), `meet_id` (string), `races` (array, abbreviated race entries), `state` (string, Australian state).

### `/v1/australia/meets/{meet_id}/races`

GET. Returns all races for a given meet, identified by `meet_id`.

**Min plan:** Free + Australia regional add-on. **Rate limit:** 5 requests per second.

**Response shape:** array of `Race` objects (see §3.2 below for full Race schema).

### `/v1/australia/meets/{meet_id}/races/{race_number}`

GET. Returns a specific race within a meet, identified by `meet_id` plus `race_number`.

**Min plan:** Free + Australia regional add-on. **Rate limit:** 5 requests per second.

**Response shape:** single `Race` object with full runner detail.

**Identity reconciliation note for §2.4 reviewers:** the Racing API identifies a race by `(meet_id, race_number)` as the natural key. Betfair identifies the same race by `marketId` (the Betfair-side market identifier for the WIN market on that race). The brief's §6 subscription shape and §13 BSP timing carry-in implicitly assume a reliable mapping between Racing API race identity and Betfair `marketId`. The reviewer should verify the brief's claims about this mapping are consistent with what both APIs document.

### `/v1/results/{race_id}`

GET. Returns the result for a specific race after running, identified by Racing API `race_id`.

**Min plan:** Standard. **Rate limit:** 5 requests per second.

**Response shape:** `ResultStandard` schema — finishing positions, margins, sectional times where available.

### `/v1/results/today`

GET. Returns all results for the current day across regions.

**Min plan:** Standard. **Rate limit:** 5 requests per second.

### `/v1/odds/{race_id}/{horse_id}`

GET. Returns odds history for a specific runner. Note this is Racing-API-aggregated bookmaker odds, NOT Betfair-direct exchange data.

---

## 3.2 — §2.4-relevant schemas

### `Race` (Australian)

Properties of an Australian race object as returned by the meets/races endpoints:

- `class` — race class (string, nullable).
- `course` — track name (string, nullable). E.g. "Flemington", "Randwick".
- `course_id` — Racing API internal course identifier (string, nullable).
- `date` — race date (string, ISO date, nullable).
- `distance` — race distance (string, nullable). E.g. "1200m".
- `going` — track condition (string, nullable). E.g. "Good", "Soft 5".
- `is_jump_out` — boolean, nullable, default false.
- `is_trial` — boolean, nullable, default false.
- `meet_id` — Racing API internal meet identifier (string).
- `off_time` — scheduled jump time (string, nullable).
- `prize_total` — total prize pool (number, nullable).
- `prizes` — prize breakdown (array, nullable).
- `race_conditions` — race conditions text (string, nullable).
- `race_group` — race group classification (string, nullable).
- `race_name` — race name (string, nullable).
- `race_number` — race number within the meet (integer or string).
- `race_status` — race status (string, nullable).
- `runners` — array of `Runner` objects (see below).
- `state` — Australian state (string, nullable). E.g. "VIC", "NSW".
- `winning_time` — winning time (string, nullable).
- `winning_time_hundredths` — winning time fractional component (string or number, nullable).

### `Runner` (Australian)

Properties of a runner within an Australian race:

- `age` — horse age (integer, nullable).
- `colour` — horse colour (string, nullable).
- `comment` — runner comment (string, nullable).
- `dam` — dam name (string, nullable).
- `dam_id` — Racing API internal dam identifier (string, nullable).
- `draw` — barrier draw (integer, nullable).
- `form` — recent form string (string, nullable).
- `horse` — horse name (string).
- `horse_id` — Racing API internal horse identifier (string).
- `jockey` — jockey name (string, nullable).
- `jockey_claim` — apprentice claim (string or number, nullable).
- `jockey_id` — Racing API internal jockey identifier (string, nullable).
- `margin` — finishing margin (string, nullable, populated post-race).
- `number` — saddle / runner number (integer or string).
- `odds` — odds at time of fetch (object, nullable).
- `owner` — owner name (string, nullable).
- `position` — finishing position (integer, nullable, populated post-race).
- `prize` — prize won (number, nullable, populated post-race).
- `rating` — rating (integer or number, nullable).
- `scratched` — boolean, nullable.
- `sex` — horse sex (string, nullable).
- `silk_url` — silks image URL (string, nullable).
- `sire` — sire name (string, nullable).
- `sire_id` — Racing API internal sire identifier (string, nullable).
- `sp` — starting price (object, nullable, populated post-race). **Note for §2.4 reviewers:** this is Racing-API-aggregated SP, NOT Betfair BSP. The brief's BSP timing carry-in logic in §13/§14 references Betfair BSP via the `r.sp.actual_sp` field on Betfair-side `MarketBook` responses, not this Racing API `sp` field.
- `stats` — runner stats (object, nullable).
- `trainer` — trainer name (string, nullable).
- `trainer_id` — Racing API internal trainer identifier (string, nullable).
- `weight` — assigned weight (string or number, nullable).

### `Meet` (Australian)

Properties of an Australian meet:

- `course` — track name (string, nullable).
- `course_id` — Racing API internal course identifier (string, nullable).
- `date` — meet date (string, ISO date).
- `meet_id` — Racing API internal meet identifier (string).
- `races` — abbreviated array of races at this meet.
- `state` — Australian state (string, nullable).

### `ResultStandard`

Result schema returned by `/v1/results/{race_id}`. Includes finishing positions, margins, sectional times where available, plus runner-level result detail. Full schema in `openapi.json` under `components.schemas.ResultStandard`.

---

## 3.3 — Identity reconciliation — Racing API vs Betfair

The §2.4 brief implicitly depends on reliable mapping between Racing API race identity and Betfair market identity. Reviewers should keep this mapping in mind when reviewing §6 (subscription shape — the brief subscribes by Betfair marketId), §13/§14 (BSP timing carry-in — the BSP belongs to a Betfair market but settlement may need to be reconciled to the Racing API race), and §15 (REST placement — order placement happens against Betfair marketId).

**What's documented:** neither API directly publishes a join key to the other. The mapping is established at v3-implementation level via the venue-and-time-and-race-number combination, with venue normalisation handled separately (per Fix 5 venue harmonisation work, which is out of §2.4 scope).

**What the reviewer should check:** whether the §2.4 brief makes assumptions about this mapping that the brief itself does not explicitly justify. If the brief assumes "we have a `betfair_market_id` for this Racing API race" without specifying how that mapping is acquired or maintained, that's a gap worth flagging — it's load-bearing for §2.4's correctness.



---

# Section 4 — Cross-reference index

This index maps §2.4 brief sections to the most relevant sanctioned reference material. The reviewer is not obliged to follow this mapping — it's a navigation aid for sections of the brief where the relevant reference material may not be obvious. Reviewers should follow their own judgement on what to cross-check where.

| §2.4 brief section | Primary reference | Secondary reference |
|---|---|---|
| §1 Framing | — | — |
| §2 Module shape | — (architectural framing — not directly reference-bound) | — |
| §3 Connection management — Streaming | §1 Streaming API (connection lifecycle, transport, idle handling) | §2.8 Best Practice (HTTP transport defaults, idle keep-alive) |
| §4 Authentication | §2.5 Login & Session Management | §2.8 Best Practice (login rate floors) |
| §5 Subscription patterns — market data | §1 Streaming API (`marketSubscriptionMessage`, `MarketFilter`, `MarketDataFilter`) | §2.6 Betting Enums (market status, projection enums) |
| §6 Subscription patterns — order data | §1 Streaming API (`orderSubscriptionMessage`, order change message shape) | §2.6 Betting Enums (order status, persistence types, order types) |
| §7 Message handling and cache shape | §1 Streaming API (image vs delta semantics, change-message shape, cache reconstruction) | — |
| §8 Reconnection and resubscription | §1 Streaming API (heartbeat, conflate ms, reconnection semantics) | §2.8 Best Practice (idle keep-alive timing) |
| §9 Order placement — REST endpoints | §2.1 placeOrders | §2.6 Betting Enums (PERSIST/LAPSE, MOC), §2.7 Betting Exceptions (placement failure modes) |
| §10 Order state reads — REST endpoints | §2.4 updateOrders, §2.3 replaceOrders | §2.7 Betting Exceptions |
| §11 Rate-limit and data-limit handling | §2.9 Market Data Request Limits | §2.8 Best Practice |
| §12 Cadence design — operational live pricing | §1 Streaming API (`MarketDataFilter` `ladderLevels`, `EX_BEST_OFFERS`, change message cadence) | §2.9 Market Data Request Limits (REST budget for fallback) |
| §13 Cadence design — BSP timing observation carry-in | §2.10 Betfair Starting Price Betting (canonical BSP definition — Near Price, Far Price, reconciliation at in-play); §1 Streaming API (`MarketDataFilter` `EX_MARKET_DEF`, `r.sp.actual_sp`, market lifecycle states OPEN / SUSPENDED / CLOSED) | §3.2 Racing API Race / Runner schemas (race timing context, post-race result reconciliation) |
| §14 Cadence design — placement and cancel | §2.1 placeOrders, §2.2 cancelOrders, §2.4 updateOrders | §2.6 Betting Enums (order persistence semantics) |
| §15 Error handling and stream health | §1 Streaming API (status codes, error semantics) | §2.7 Betting Exceptions (REST error taxonomy) |
| §16 Currency — GBP, AUD, and where the conversion happens | §1 Streaming API (account currency in subscription state) | §2.8 Best Practice |
| §17 What this closes | — (governance / scope framing) | — |

---

**End of sanctioned reference compendium.**

The reviewer should now have everything needed to reconcile the §2.4 brief against the sanctioned material. Findings, gaps, and inconsistencies are the primary output of the review per the orienting prompt.


