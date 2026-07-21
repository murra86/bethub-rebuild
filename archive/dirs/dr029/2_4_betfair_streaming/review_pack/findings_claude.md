# Fresh-eyes review — §2.4 Betfair Streaming brief

**Reviewer:** Claude (fresh session)
**Pack:** locked §2.4 brief (2,629 lines, dated Sessions 60/61/64), `sanctioned_reference.md` (2,567 lines, Sections 1–4), and the orienting prompt.
**Pass:** single, no iteration.
**Method:** every substantive design choice in the brief reconciled against the consolidated reference document; cross-checks against the Betfair Developer Forum and Betfair GitHub samples where the consolidated reference was silent. Two such cross-checks were performed (customerRef de-dupe semantics; greyhound eventTypeId).

---

## Findings — substantive

### Finding 1 — BLOCKING: §14.2 misattributes the 60-second de-duplication window to `customerOrderRef`. The window applies to `customerRef`.

**Brief §14.2** ("The customerOrderRef round trip"): *"Per the on-disk `placeOrders.md` reference's customerRef section, **Betfair de-duplicates against customerOrderRef for 60 seconds.** A retry of `placeOrders` with the same customerOrderRef inside that window will not double-place. This gives v3 a clean idempotency boundary."*

**Sanctioned reference, Section 2.1 — placeOrders, Parameters table:** *"`customerRef` (String, no) — Optional unique string (up to 32 chars) used to **de-dupe mistaken re-submissions**. ... **De-duplication window is 60 seconds.** This field does NOT persist into the placeOrders response or Order Stream API — distinct from `customerOrderRef` (which sits inside the PlaceInstruction)."* The same Section then describes `customerStrategyRef` and (inside the PlaceInstruction) `customerOrderRef` as separate concepts with no de-dup semantics attached.

**Sanctioned reference, Section 2.6 — Betting Enums, ExecutionReportErrorCode:** `DUPLICATE_TRANSACTION` — *"Duplicate customer reference data submitted ... There is a time window associated with the de-duplication of duplicate submissions which is 60 second"*. This is the error returned when `customerRef` is reused inside the window — confirming `customerRef`, not `customerOrderRef`, is the de-dup key.

**Cross-reference (Betfair Developer Forum, "Customer Ref in placeOrders" thread, forum.developer.betfair.com/forum/sports-exchange-api/exchange-api/3209):** the same 60-second window is described against `customerRef`. The thread also clarifies `customerRef` is NOT returned in `listCurrentOrders` or any subsequent response, which aligns with the captured Section 2.1 statement.

**Why this is BLOCKING.** The brief makes `customerOrderRef` carry two roles simultaneously: (a) the v3-bet-record join key on the order stream (per §6.3 and §9.4 — this role is correct, `customerOrderRef` does round-trip via the `rfo` field), and (b) the de-dup key for placement-retry safety (per §14.2 — this role is wrong; the de-dup key is `customerRef`). The retry-safety design at §14.3 ("On timeout: v3 reads `listCurrentOrders` filtered by customerOrderRef ... If not found: retry placeOrders with the same customerOrderRef. Idempotency guarantee from §14.2 holds.") relies on the wrong field carrying the idempotency property.

If implemented as written, a retry of `placeOrders` with the same `customerOrderRef` but no `customerRef` (or with a different `customerRef` because v3 re-generated one) would NOT be de-duplicated by Betfair, and would create a duplicate bet. The "single-retry policy + idempotency guarantee" is not actually safe under the brief's design as drafted.

**Implication for §6.3, §9.4, §14.2, §14.3.** The brief needs to set BOTH refs on every placement: `customerOrderRef` (per-instruction, used for stream round-tripping into the v3 bet record — this is what the brief already names) AND `customerRef` (request-level, used for the 60-second de-dup window — this is what §14.2 should name). On a retry, the SAME `customerRef` value must be sent, otherwise the de-dup window doesn't engage. The `listCurrentOrders` lookup-before-retry still happens, but the `customerRef` is the ultimate safety net inside the 60-second window (since the lookup itself can race the timed-out request).

A secondary concern: `customerRef` is NOT returned in `listCurrentOrders` (per the captured page text and the forum thread), so the lookup at §14.3 has to be on `customerOrderRef`, which IS returned. This means the design needs both: lookup keyed on `customerOrderRef`, de-dup safety net keyed on `customerRef`.

---

### Finding 2 — BLOCKING: §14.3 sets the placement-call timeout threshold to 3000 ms, below Betfair's own 5-second matcher timeout. This creates a race window where a v3 timeout fires while the bet is still in-flight at Betfair, and `listCurrentOrders` may not yet show it.

**Brief §14.3** ("Single-retry policy on timeout"): *"Timeout threshold: 3000ms. Healthy `placeOrders` calls return well under 1s; a 3-second wait is a defensive ceiling, not an expected wait. On timeout: v3 reads `listCurrentOrders` filtered by customerOrderRef to check whether the placement actually landed before the timeout fired."*

**Sanctioned reference, Section 2.6 — Betting Enums, ExecutionReportStatus.TIMEOUT:** *"The order timed out & the status of the bet is unknown. If a TIMEOUT error occurs on a placeOrders/replaceOrders request, you should check listCurrentOrders to verify the status of your bets before placing further orders. Please Note: **Timeouts will occur after 5 seconds of attempting to process the bet but please allow up to 15 seconds for a timed out order to appear.** After this time any unprocessed bets will automatically be Lapsed and no longer be available on the Exchange."*

The same text appears verbatim in Section 2.6 (InstructionReportStatus.TIMEOUT) and in Section 2.7 (Betting Exceptions — TIMEOUT_ERROR).

**Why this is BLOCKING.** v3's 3-second client-side timeout fires before Betfair's own 5-second matcher timeout, AND before the up-to-15-second window in which a timed-out order may still appear on `listCurrentOrders`. The §14.3 sequence becomes:

1. v3 issues placement at click + 0ms.
2. v3's 3-second timeout fires at click + 3000ms — but Betfair's matcher hasn't yet decided the bet is dead (5-second window).
3. v3 calls `listCurrentOrders` filtered on `customerOrderRef`.
4. The bet is not yet returned (Betfair's documentation says "allow up to 15 seconds for a timed out order to appear").
5. v3 retries `placeOrders`. If the original lands a few hundred ms later, v3 has now placed two bets.

Finding 1's `customerRef` 60-second window IS the protection here — but only if §14.2 is corrected per Finding 1. Without it, the 3-second timeout is unsafe by Betfair's own published timing.

The straightforward remediation is either (a) raise the v3 timeout to ≥ 15 seconds (matching Betfair's "allow up to 15 seconds" guidance), or (b) keep the 3-second timeout but lock the `customerRef` discipline from Finding 1 as the actual idempotency mechanism, with the `listCurrentOrders` lookup as a soft check rather than the primary safety. Either is workable; the brief picks the operator-latency-friendly tight timeout but doesn't engage the only mechanism that makes it safe.

---

### Finding 3 — SIGNIFICANT: §3.5 and §15.3 specify different reconnect back-off caps (30 s vs 16 s). One of the two is wrong; the brief is internally inconsistent.

**Brief §3.5** ("Back-off discipline"): *"Reconnection back-off is bounded-exponential: 1 second, 2 seconds, 4 seconds, 8 seconds, **capped at 30 seconds**, then constant 30-second intervals indefinitely."*

**Brief §15.3** ("Reconnection back-off and escalation"): *"Per Section 8, Streaming reconnect uses bounded exponential back-off — first attempt immediate, then 1s, 2s, 4s, 8s, **capped at 16s**."*

Section 8.7 itself (which both reference) uses 30 seconds.

**Sanctioned reference, Section 1 — Stream API, "Stream Health":** *"Re-connect code should contain back-offs to avoid spamming the service if you are unable to connect for a prolonged period for any reason."* The reference does not specify a cap value — both 16 s and 30 s are inside what Betfair sanctions. So this is an internal-consistency finding, not a sanctioned-material conflict, but the brief's two sections give a downstream implementer two different numbers to follow. Operator decision needed before implementation.

**Why SIGNIFICANT not MINOR.** §3.5 is the section §15.3 cites ("per Section 8"); §15.3 then states a different number. A Code-side implementer reading §15.3 first would build to 16 s; reading §3.5 first would build to 30 s. The brief cannot lock contract shape if two of its own sections disagree on a load-bearing number.

---

### Finding 4 — SIGNIFICANT: §4.5 and §11.4 specify different login-attempt floor cadences (1/sec vs 1/60 sec). Both can't be right.

**Brief §4.5** ("Login rate limit discipline"): *"betfair_client's login path enforces this with a hard floor: **no more than one login attempt per second** from a single betfair_client instance, and no more than 10 login attempts in any rolling 5-minute window."*

**Brief §11.4** ("REST-side login-rate limit"): *"betfair_client rate-limits authentication-attempt frequency **to one per 60 seconds at floor** (defensive default), and escalates to operator-visible alert if a third attempt is required within 10 minutes."*

**Sanctioned reference, Section 2.8 — Best Practice:** *"If login limits are exceeded, you'll be automatically prevented from making further login requests for a period of 20 minutes. During this time all existing sessions will remain valid."* The reference does not publish the actual login limit threshold (per the brief's own note in §4.5). Both floors (1/sec, 1/60sec) are well inside whatever the unpublished ceiling is — so neither violates Betfair's sanctioned material directly. The conflict is internal.

**Why SIGNIFICANT.** A 60× difference between the two stated floors — a Code-side implementer cannot pick a single defensible number from the brief as drafted. Operator decision needed.

A note alongside: the brief at §4.5 says "no more than 10 login attempts in any rolling 5-minute window" — a rate of 2/min average, ~1 per 30 seconds — which sits between the two floors and may have been the intended discipline. But the brief states three different rates across two sections.

---

### Finding 5 — SIGNIFICANT: §16 refreshes the GBP→AUD rate "daily", but Betfair's `listCurrencyRates` is not specified by the consolidated reference; the brief's daily-refresh choice is an operator-side default that is not sanctioned-material-derived.

**Brief §16** ("Currency"): *"`listCurrencyRates` is the conversion source. Per the Stream API reference's Currency Support section, v3 calls `listCurrencyRates` (REST) at startup and refreshes daily to get the GBP-to-AUD rate."*

**Sanctioned reference, Section 1 — Stream API, "Currency Support":** *"The Exchange Stream API supports GBP currency only. Those looking to convert data from GBP to a different currency should use `listCurrencyRates` to do so."* — exactly two sentences. The Stream API reference points to `listCurrencyRates` as the conversion source. Nothing in the captured material specifies refresh cadence, response shape, rate-limit cost, or staleness tolerance for `listCurrencyRates` itself.

**Why SIGNIFICANT not MINOR.** The brief frames daily refresh as if it follows from sanctioned material ("Per the Stream API reference's Currency Support section"), but the sanctioned material is silent on cadence — it only names the endpoint. The operator can defend "daily" as a reasonable choice on FX-volatility grounds (per the brief's own justification), but the citation as drafted is misleading. A reviewer or downstream implementer reading "Per the Stream API reference's Currency Support section, v3 calls listCurrencyRates (REST) at startup and refreshes daily" will reasonably believe the daily cadence is documented; it is not.

The remediation is to reword the citation: the endpoint name comes from the sanctioned material, the daily cadence is an operator-policy choice. Both are defensible; the citation just needs to be honest about which is which.

---

### Finding 6 — MINOR: §9.6 names "Day-one default is PERSIST". Both PERSIST and LAPSE are legitimate Betfair persistence types; the choice is an operator decision, but the brief's framing is muddled by §6.3's separate claim that `customerStrategyRef` is set to "1", "2", "3", "4" per strategy.

**Brief §9.6:** *"Day-one default is PERSIST unless the operator explicitly selects LAPSE or MARKET_ON_CLOSE. The default may be revisited as operational evidence accumulates across the four strategies (Session 64 operator decision)."*

**Sanctioned reference, Section 2.6 — Betting Enums, PersistenceType:**

- `LAPSE` — *"Lapse (cancel) the order automatically when the market is turned in play if the bet is unmatched"*.
- `PERSIST` — *"Persist the unmatched order to in-play. The bet will be placed automatically into the in-play market at the start of the event. **Once in play, the bet won't be cancelled by Betfair if a material event takes place** and will be available until matched or cancelled by the user"*.
- `MARKET_ON_CLOSE` — *"Put the order into the auction (SP) at turn-in-play"*.

PERSIST has a non-trivial in-play exposure characteristic ("won't be cancelled by Betfair if a material event takes place") that the brief does not mention. LAPSE is the conservative pre-jump-only default in most retail betting code. The brief's choice of PERSIST as default is defensible — the brief flags it as a Session 64 operator decision — but the rationale shown is weak ("default may be revisited as operational evidence accumulates"), and the sanctioned material's own warning about PERSIST's in-play behaviour is not discussed in the brief.

**Why MINOR.** This is the operator's decision to make. The brief acknowledges it as Session 64 operator-decided. Flagging it because the persistence-type choice is the kind of decision that can pass review unchecked and surface as a surprise after the first in-play race during an OPEN-pre-jump bet that was placed PERSIST and then survived into in-play.

---

### Finding 7 — MINOR: §3.1 names `stream-api-integration.betfair.com` as the pre-production endpoint without port, but production is `stream-api.betfair.com:443`. The integration endpoint also takes :443 per the sanctioned reference, but the brief's naming asymmetry could mislead Code at implementation.

**Brief §3.1:** *"Production: `stream-api.betfair.com:443`. ... A pre-production integration endpoint exists (`stream-api-integration.betfair.com`) for testing."*

**Sanctioned reference, Section 1 — Stream API, "Connection":**
- *"External (SSL): `stream-api.betfair.com:443`"*
- *"Integration Endpoint: `stream-api-integration.betfair.com`"* (no port)

The reference itself omits the port from the integration endpoint, so the brief is consistent with the source. But both endpoints take :443 SSL — this is a Stream API reference page omission that Code may want clarified at implementation time. Cosmetic; v3 does not use the integration endpoint operationally per the brief.

---

### Finding 8 — MINOR: §6.2 sets `partitionMatchedByStrategyRef=false`, citing it as the default. The sanctioned reference confirms this is the default — but the brief's other order-filter parameters need a quick consistency check.

**Brief §6.2:** *"`includeOverallPosition=true`", "`partitionMatchedByStrategyRef=false`", "`customerStrategyRefs` — not set", "`segmentationEnabled=true`*"

**Sanctioned reference, Section 1 — Stream API, OrderFilter table:**
- `includeOverallPosition` — default `true`. ✓ (brief sets explicitly to true, redundant but harmless.)
- `partitionMatchedByStrategyRef` — default `false`. ✓
- `customerStrategyRefs` — default `null`. ✓ (brief leaves unset.)
- `accountIds` — *"This is for internal use only & should not be set on your filter"*. The brief does not mention this; correct, since it's not to be set.

`segmentationEnabled` is a property of the SubscriptionMessage (not the OrderFilter). The brief at §6.2 places it inside the order-filter list rather than as a separate subscription parameter. Cosmetic structural confusion in the brief; semantically correct (segmentation on the order subscription is sanctioned).

---

### Finding 9 — MINOR: §9.5 states `betDelayModels.PASSIVE` "applies broadly to in-play markets". The sanctioned reference is more specific — PASSIVE has explicit constraints on order shape (LIMIT only, LAPSE only, no timeInForce/minFillSize/betTargetType).

**Brief §9.5:** *"PASSIVE — `betDelay > 0` but orders that won't match immediately bypass the delay. **Applies broadly to in-play markets.** No special handling — `betfair_client` sends the order, Betfair decides whether to apply the delay."*

**Sanctioned reference, Section 1 — Stream API, MarketDefinition Fields:** *"PASSIVE — For in-play markets where `betDelay > 0`, orders that are guaranteed not to match immediately are accepted straight away, bypassing the bet delay wait. **Order requirements (otherwise bets will be subject to the usual bet delay before being placed):**
- Only plain LIMIT orders are supported.
- Allowed `persistenceType`: LAPSE.
- The following attributes are not supported and must be omitted: `timeInForce`, `minFillSize`, `betTargetType`."*

**Sanctioned reference, Section 2.6 — Betting Enums, BetDelayModel:** same wording, same constraints.

The brief's characterisation ("no special handling — Betfair decides whether to apply the delay") is correct in the limit case where v3 doesn't try to use PASSIVE deliberately. But v3 day-one places PERSIST (per §9.6) in many cases — PERSIST orders never get the PASSIVE bypass because the bypass requires `persistenceType: LAPSE`. So v3's day-one in-play placements are always subject to the full bet delay, which the brief's §14.4 acknowledges. Internally consistent; the §9.5 wording is slightly looser than the sanctioned material.

**Why MINOR.** The brief's design is correct in its conclusion ("v3 day-one does not use the PASSIVE model"); the description of PASSIVE itself just lacks the order-shape constraints from the sanctioned material. Cosmetic.

---

## Findings — gaps

### Gap 1 — Australian-specific session expiry is not documented in the consolidated reference; the brief's 4-hour `keepAlive` cadence at §4.4 is defended by reference to the 12-hour international and 20-minute Italian/Spanish windows, but the AU window itself is not on disk.

**Brief §4.4:** *"A Betfair session token expires after 12 hours of no API use, or 20 minutes of no use for some account types (per Betfair's session management documentation). ... `betfair_client` calls `keepAlive` proactively on a 4-hour cadence while the session is active. The 4-hour cadence is well inside the shortest documented expiry window (with margin) and well inside the 12-hour standard window."*

**Sanctioned reference, Section 2.5 — Login & Session Management, Page 3:** *"On the international (.com) Exchange the current session expiry time is **12 hours** for all customers (excluding UK & Ireland) and **24 hours** for UK & Ireland customers. The session expiry time is currently **20 minutes** on the Italian & Spanish Exchange."* 

The reference also lists separate `keepAlive` endpoints by jurisdiction (Page 3): `https://identitysso.betfair.au/api/keepAlive` for Australia & New Zealand, but says nothing about the AU session expiry. The Best Practice page (Section 2.8) says *"Login sessions last up to 24 hours by default and you can use Keep Alive to extend the session beyond the stated session expiry time. The maximum session length varies by country — further details on the Login & Session Management page."* — which then doesn't itself specify AU.

**Why this is a gap not a finding.** v3's operational account is Australian; the brief's 4-hour cadence is comfortably inside any plausible AU expiry (at the worst case it would be the 12-hour international default). The brief's reasoning holds even with the AU-specific number unknown. But the brief at §17.3 itself flags this as an open item: *"Specific session-length details by country (per `best_practice.md`'s reference) are not on disk. Pull on demand if authentication discipline needs retrofit."* So the brief authors are aware. The gap is that the operator may want to confirm AU's number before locking the cadence — though even if AU is 20 min (matching IT/ES), the 4-hour cadence is still inside it as long as a single missed keepAlive doesn't happen. The cadence-vs-floor margin worth a sanity check.

---

### Gap 2 — `listCurrencyRates` API surface is silent in the captured reference, but the brief at §16 builds non-trivial design on top of it.

**Brief §16:** v3 calls `listCurrencyRates` (REST) at startup, refreshes daily, caches, applies to every market-data display.

**Sanctioned reference, Section 1 — Stream API, "Currency Support":** names `listCurrencyRates` as the conversion source. No detail on the call shape, response, rate-limit budget, error modes.

**Why this is a gap.** The brief asserts a refresh cadence, a placement-blocking behaviour ("Currency-conversion errors do not block placement"), and a cache discipline — all without citing where the `listCurrencyRates` operational characteristics come from. They almost certainly come from the operator's working knowledge of the endpoint, but the consolidated reference doesn't include them. A future drift scan against `listCurrencyRates`'s actual documentation may find the brief's assumptions are wrong (for example, if the endpoint has its own rate limit pool that the brief should be respecting). Worth pulling the reference page on demand before locking §16 hard.

---

### Gap 3 — The brief's identity-reconciliation between Racing API races and Betfair markets is implicit; the consolidated reference (Section 3.3) explicitly flags this as something the reviewer should check.

**Brief §6.3, §13, §14:** assumes v3 has a `betfair_market_id` for every race v3 cares about. The brief does not specify how that mapping is established or maintained.

**Sanctioned reference, Section 3.3 — Identity reconciliation:** *"The §2.4 brief implicitly depends on reliable mapping between Racing API race identity and Betfair market identity. ... neither API directly publishes a join key to the other. The mapping is established at v3-implementation level via the venue-and-time-and-race-number combination, with venue normalisation handled separately (per Fix 5 venue harmonisation work, which is out of §2.4 scope). ... If the brief assumes 'we have a betfair_market_id for this Racing API race' without specifying how that mapping is acquired or maintained, that's a gap worth flagging — it's load-bearing for §2.4's correctness."*

**Why this is a gap.** §2.4 doesn't need to specify Fix 5's venue harmonisation work — that's correctly out of scope per the brief's own framing (§2.4 is contract-shape work, not joining infrastructure). But the brief is silent on the contract assumption that drives several of its design choices: that `betfair_market_id` is reliably available on every v3 race entity at the moment the operator wants to subscribe to it. If Fix 5 ever fails to populate a market id for some race the operator cares about, §2.4's coarse-subscription discipline (subscribe by event-type-and-country, not by marketId) carries that race regardless — but anything that needs to act on a specific market (placement at §9, settlement reads at §10, BSP gates at §13) breaks silently.

The brief should at least note that this is a precondition assumed from elsewhere, so a downstream review of Fix 5 against §2.4 is on the operator's radar.

---

### Gap 4 — `listCurrentOrders` filtering by `customerOrderRef` is assumed at §9.8, §14.3, §10.2; the consolidated reference (Section 2.1) confirms `customerOrderRef` exists as a per-instruction field but the captured material does not explicitly spec the filter.

**Brief §9.8, §14.3, §10.2:** *"`betfair_client` calls `listCurrentOrders` filtered on the `customerOrderRef` of the failed call"* etc.

**Sanctioned reference, Section 2:** does not include the captured `listCurrentOrders` page. Section 2.6's `OrderProjection` enum names `EXECUTABLE` / `EXECUTION_COMPLETE` / `ALL`, but the filter parameter set on `listCurrentOrders` itself is not enumerated.

**Why this is a gap.** The brief assumes `customerOrderRefs` is a valid filter parameter on `listCurrentOrders`. This is correct per the live Betfair API (the operator's working knowledge confirms it) but the consolidated reference doesn't include the `listCurrentOrders` Reference Guide page that would prove it. Pull `listCurrentOrders.md` on demand before locking the cold-start reconciliation flow at §10.5 hard — a Code-side implementer needs the parameter list, not just the brief's narrative description.

---

## Sections reviewed without findings

- §1 Framing
- §2 Module shape (architectural framing — not directly reference-bound)
- §2.1 Parallel module structure
- §2.2 Boundaries betfair_client owns
- §2.3 Versioned contract
- §3.2 Connection lifecycle (state machine — internal to brief)
- §3.3 The 15-second authentication rule (consistent with sanctioned reference)
- §3.4 Reconnection on drop (consistent with sanctioned reference's re-subscription protocol)
- §3.6 Connection per process (consistent with `MAX_CONNECTION_LIMIT_EXCEEDED` semantics)
- §4.1 What authentication consists of
- §4.2 Where credentials live
- §4.3 Login flow
- §4.6 INVALID_SESSION recovery (consistent with sanctioned reference error semantics)
- §4.7 Streaming and REST share one session (consistent with Best Practice section)
- §5.1 Coarse over fine-grain (directly cites sanctioned guidance correctly)
- §5.2 Data filter — the field flags (field flags consistent with sanctioned MarketDataFilter table; greyhound eventTypeId 4339 verified via cross-check)
- §5.3 Subscription parameters (segmentationEnabled, heartbeatMs, conflateMs all consistent with sanctioned bounds)
- §5.4 Subscription lifecycle
- §6.1 Why order streaming, not REST polling (rate-limit pool composition correct per Section 2.7)
- §6.2 Subscription shape (see Finding 8 for minor structural note; substantive content correct)
- §6.4 What the order stream cache holds (consistent with sanctioned `uo`/`mb`/`ml` semantics)
- §6.5 What the order stream cache exposes upward
- §6.6 Reconciliation pattern with REST
- §7.1 Two caches, one connection
- §7.2 Market cache shape (consistent with MarketDefinition + RunnerDefinition fields)
- §7.3 Order cache shape
- §7.4 Building the market cache from messages (`SUB_IMAGE` / `RESUB_DELTA` / update semantics correct)
- §7.5 Delta semantics — ladders (level/depth and price-point semantics consistent with sanctioned reference)
- §7.6 Building the order cache from messages (`fullImage` semantics consistent including the empty-update market-removal case)
- §7.7 What consumers see
- §7.8 Staleness signalling — explicit, not inferred
- §7.9 Concurrency and threading
- §8.1 The two-token discipline (consistent with sanctioned `initialClk` / `clk` semantics)
- §8.2 Resubscribe with stored tokens — the happy path
- §8.3 Fall back to fresh image — the unhappy path (consistent with `INVALID_CLOCK` semantics)
- §8.4 Cold start
- §8.5 Stream API status field — `503` vs disconnect (sanctioned guidance to not disconnect on 503 correctly cited)
- §8.6 Heartbeat-loss detection (2× heartbeatMs rule consistent with sanctioned Stream Health section)
- §8.7 Sustained reconnection failure (substance correct; back-off cap inconsistency flagged at Finding 3)
- §8.8 Per-subscription independence
- §9.1 REST endpoint and surface (`api.betfair.com.au` correctly noted; JSON-RPC vs REST surfaces correctly differentiated)
- §9.2 The four placement-side operations
- §9.3 Place, cancel, replace, update — call shape
- §9.4 The customerOrderRef round-trip (the round-trip mechanism is correct; see Finding 1 for the de-dup misattribution)
- §9.7 The placement rate limits (1000-tps and 3-concurrent ceilings correctly cited per Section 2.7)
- §9.9 Order placement failures — Lapse Status Reason Codes (codes consistent with sanctioned Section 1 list)
- §10.1 The three REST read operations
- §10.3 When `listClearedOrders` is called (independent rate-limit pool consistent with sanctioned material)
- §10.4 When `listMarketBook` with order projection is used
- §10.5 Cold-start reconciliation flow
- §10.6 What the REST read methods expose upward
- §10.7 Pagination and partial returns
- §10.8 Streaming-vs-REST consistency
- §11.1 Streaming-side limits (`MAX_CONNECTION_LIMIT_EXCEEDED`, `SUBSCRIPTION_LIMIT_EXCEEDED`, `connectionsAvailable` discipline all consistent)
- §11.2 REST-side data-weight limit (200-point ceiling, weight tables correctly cited per Section 2.9)
- §11.3 REST-side instruction-count limits (200/60/60 consistent across sanctioned reference)
- §11.5 REST-side transaction-charge consideration
- §11.6 HTTP transport defaults (gzip + keep-alive + no Expect:100-Continue + 3-min idle close all consistent with Best Practice)
- §11.7 Streaming-side slow-consumer behaviour (`con=true` semantics consistent with sanctioned Performance Considerations and Conflation sections)
- §11.8 Aggregate discipline
- §12.1 Publisher cadence
- §12.2 Heartbeat cadence (heartbeatMs bounds 500–5000 consistent with sanctioned material)
- §12.3 Consumer cadence
- §12.4 The cadence the burst UI sees
- §12.5 Cadence floor for operational fitness
- §12.6 What this section does not cover
- §13.1 The BSP-reachability finding (Stream-side BSP via `SP_TRADED` + runner-definition `bsp` consistent with sanctioned reference)
- §13.2 The "BSP is now safe to read" gate (probe-derived rather than reference-derived; consistent with sanctioned market-status enum)
- §13.3 The OPEN-but-post-jump window
- §13.4 The `sp` container shape-shift (Stream-side handling via separate field flags consistent with sanctioned material)
- §13.5 Per-phase change rates and Streaming subscription cadence
- §13.6 Greyhound POST_START asymmetry
- §13.7 The 45-minute CLOSED tail finding
- §13.8 What this closes
- §14.1 Latency budget for a single placement
- §14.4 In-play bet-delay timing
- §14.5 Cancel pacing (LIMIT-only cancellation consistent with sanctioned cancelOrders notes; 60-instruction limit correctly cited)
- §14.6 Replace pacing — the atomicity gap (the replace-without-rollback semantics correctly cited and the `replaced_ok` / `cancelled_no_replace` / `failed` discriminated return is a load-bearing safety design)
- §14.7 Update pacing — the persistence-flag-only path (sanctioned updateOrders signature confirms persistence-only update without price/size change)
- §14.8 Closed-loop latency target
- §14.9 What this section does not cover
- §15.1 The three error categories
- §15.2 Streaming connection health
- §15.4 REST error handling (error catalogue consistent with sanctioned Section 2.7 Betting Exceptions)
- §15.5 Lapse-status-reason codes (full code list consistent with sanctioned reference)
- §15.6 Operator-visible failure surfaces
- §15.7 What this section does not cover
- §16.1 What this section does not cover
- §17 What this closes (governance / scope framing)

---

## Notes for the operator

**Note A — Finding 1 cascades into the placement test design.** When Finding 1 is remediated (set both `customerRef` and `customerOrderRef` on every placement; lookup-on-retry uses `customerOrderRef`; de-dup safety net uses `customerRef`), the placement-test surface changes too. A retry-safety test that depends on the 60-second window needs to reuse the SAME `customerRef` value across the original-call and retry-call, which the brief's Code-side implementer needs to know explicitly. Worth flagging in the §2.4-derived implementation brief that follows this review.

**Note B — Finding 2 may interact with Finding 1.** If the operator chooses to keep the 3-second timeout (per brief §14.3) and rely on `customerRef` rather than the `listCurrentOrders` lookup as the primary safety, this works inside the 60-second window. If the operator chooses to widen the timeout to 15 seconds (matching Betfair's "allow up to 15 seconds for a timed-out order to appear"), the design is unchanged in shape but the closed-loop latency target at §14.8 is no longer 1 second — it becomes "1 second on the happy path; up to 15 seconds on the timeout-then-recover path." Both options are workable; the operator's call.

**Note C — `customerStrategyRef` 15-character limit.** The brief at §6.3 sets `customerStrategyRef` to "1", "2", "3", "4". The sanctioned reference (Section 2.1 placeOrders parameters table) confirms the field is "Limited to 15 characters". Single-digit values fit comfortably. No issue. Flagging because if Strategy 5+ ever lands and the operator decides to use richer strategy refs ("strategy_1_v2_in_play"), the 15-character ceiling will bite. Worth noting in any future strategy-attribution work.

**Note D — `listCurrentOrders` and `customerRef` retrievability.** Per the cross-checked Betfair Developer Forum thread (forum.developer.betfair.com/forum/sports-exchange-api/exchange-api/3209), `customerRef` (the request-level field) is NOT returned in `listCurrentOrders` response. So if Finding 1 is remediated by adding `customerRef`, the lookup-on-retry mechanism still has to query by `customerOrderRef`, not `customerRef`. The brief's fundamental approach (use `customerOrderRef` for round-tripping) is correct; the brief just needs to add `customerRef` as an additional safety net specifically for the de-dup window.

**Note E — The two captured pages on `updateOrders` and Betting Enums (Sections 2.4, 2.6 of the consolidated reference) appear to be PDF-export artefacts** — the formatting is degraded relative to the cleanly-captured `placeOrders.md`/`cancelOrders.md`/`replaceOrders.md`/`best_practice.md`/`market_data_request_limits.md` pages. The substance is still extractable but worth re-capturing cleanly via web_fetch when the Confluence anonymous-access wall ever comes down (or via re-paste from authenticated browser session). Not a finding against the brief — purely a reference-pack hygiene note.

**Note F — Finding 3 (the back-off cap inconsistency) and Finding 4 (the login-floor inconsistency) both stem from the brief being authored across three sessions (60, 61, 64).** A pre-lock cross-section consistency sweep would have caught both. Worth adding to the brief-drafting close-out checklist for future briefs of comparable length.

**Note G — Persistence default at §9.6 (Finding 6) is the kind of decision that benefits from a deliberate operator paragraph in the brief itself rather than leaving it as "Session 64 operator decision".** A reviewer (or a future operator returning to the brief in six months) will not have the Session 64 transcript available; the rationale would be helpful inline. Not a finding — just a documentation observation.

**Note H — The brief makes effective use of the reference material throughout.** The cadence design at §13 (BSP timing observation carry-in) is a particularly well-grounded section — it cites the §2.1 probe report directly, names the empirical gate (`market_status in (SUSPENDED, CLOSED) and bsp > 0`), names the NaN guard as non-optional, and folds the per-phase change rates into Streaming subscription discipline. This is the kind of section where reference-grounded reasoning shows. The findings above are concentrated in §14 (placement and cancel timing), where the brief's design layers on top of `customerOrderRef` semantics that turn out to be partially misattributed.

---

**End of review.**