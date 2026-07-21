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
