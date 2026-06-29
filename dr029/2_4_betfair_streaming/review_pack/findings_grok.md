# §2.4 Betfair Streaming Brief — Detailed Fresh-Eyes Review Report

**Reviewer:** Grok (xAI)  
**Date:** 2026-05-03  
**Review Type:** Single-pass reconciliation against sanctioned reference material  
**Inputs:** Full locked `2_4_betfair_streaming.md` brief + complete `sanctioned_reference.md` (Streaming API, Reference Guide pages, Racing API subset) + orienting prompt.  
**Additional cross-checks:** Betfair Developer Forum threads and official sample code patterns where the sanctioned reference was silent or light on edge cases.

---

## Findings — substantive

**1. SIGNIFICANT (bordering BLOCKING for implementation) — §3.4 Reconnection, §8 Reconnection and resubscription, §7.4–7.5 Cache building**  
The brief correctly describes the core protocol: use stored `initialClk` + `clk` for `RESUB_DELTA` (patch) on reconnect; fallback to full `SUB_IMAGE` on `INVALID_CLOCK`; heartbeat-based drop detection (2× `heartbeatMs`); bounded exponential back-off. This maps directly to the Streaming API reference (Re-connection / Re-subscription, ChangeMessage `ct` field, `initialClk`/`clk` tokens, Heartbeat section).  

However, the brief's assumption of reliable "state-preserving where possible" across sustained outages or process restarts is only partially supported. Forum discussions and sample code show that clocks can invalidate quickly (especially on long drops or subscription changes), and `INVALID_CLOCK` forces a full image. The 60-second post-CLOSED drop discipline (§13.7) and RECONNECTING staleness signalling are good mitigations, but the brief should explicitly call out the performance/cost impact of frequent full images during unstable network periods. This is load-bearing for racing-page and burst-review UX. No outright contradiction, but a notable assumption.

**2. SIGNIFICANT — §14.2 CustomerOrderRef round-trip, §14.3 Single-retry policy, §9 Order placement**  
Excellent coverage of the 60-second de-duplication window for `customerOrderRef` (idempotency). This is explicitly documented in `placeOrders` reference and forum threads. The pattern (generate ref → place → timeout → `listCurrentOrders` lookup by ref → retry once) is sound and follows Betfair's own guidance for handling `TIMEOUT` (which can take 5–15s for the bet to appear).  

The closed-loop latency target (~1s healthy) is realistic. Minor gap: the brief could more strongly emphasise that `customerOrderRef` must be unique per placement attempt within the 60s window (forum users have hit surprises with non-unique refs across bots). Overall very strong.

**3. SIGNIFICANT — §5.1–5.3 Subscription patterns (coarse vs fine, field flags, ladderLevels=3)**  
The preference for coarse subscriptions (racing: eventTypeIds + countryCodes + marketTypes; sports: specific eventTypes + MATCH_ODDS etc.) is **explicitly recommended** in the Streaming API reference. Field filter choices (`EX_BEST_OFFERS_DISP`, `EX_LTP`, `EX_MARKET_DEF`, `SP_PROJECTED`; `ladderLevels=3`) are well-justified for operational use and correctly avoid heavy fields (`EX_ALL_OFFERS`, full traded volume). `segmentationEnabled=true`, `heartbeatMs=5000`, `conflateMs=0` all match documented bounds and best practice.  

Risk note: With AU racing volume + greyhounds, the ~200-market subscription limit (and per-connection throttling) could be approached on busy days. The brief acknowledges this but relies on consumer-side filtering. Solid, but monitor in production.

**4. MINOR — §13 BSP timing observation carry-in & gate**  
The chosen gate (`market_status in (SUSPENDED, CLOSED) AND bsp > 0`) plus phase-aware accessors for near/far/BSP is correct per Streaming API `MarketDefinition` fields (`status`, `bspReconciled`, `actualSP` in runner) and the dedicated BSP Betting page. Differentiation for greyhound (shorter POST_START window) vs thoroughbred is accurate and appropriately pushed to consumer/settlement logic. Good use of `SP_PROJECTED` for operational awareness. No issues.

**5. MINOR — §16 Currency conversion at boundary**  
Fully supported. Market data (ladders, volumes) always GBP; order stream in account currency (AUD); use `listCurrencyRates` for conversion. Roll-up behaviour (£1 GBP default) and AUD-specific minimum stakes are documented. Conversion inside `betfair_client` (never at consumer surfaces) is the correct single-integration-point discipline.

**6. MINOR — Error handling, stream health, staleness (§15, §12.4, §3.4)**  
Three-tier signalling (silent, visible-non-blocking, hard alert), `status=503`, `con=true`, heartbeat loss, `INVALID_SESSION` recovery, etc., all map cleanly to Streaming API (Stream Health, Conflation, StatusMessage, ErrorCode) and Betting Exceptions. Lapse reason codes handling is accurate.

**7. MINOR — Authentication & session lifecycle (§4)**  
Login flow, `keepAlive` cadence (4h proactive), rate-limit floors on login, shared session token across Stream + REST — all align with Login & Session Management and Best Practice pages.

**8. MINOR — Order stream & cache (§6)**  
`includeOverallPosition=true`, `customerOrderRef` round-tripping, unmatched vs matched position (`uo`/`mb`/`ml`), cold-start reconciliation with `listCurrentOrders` — all match the OrderSubscription and OrderChangeMessage sections.

**9. MINOR — REST placement/cancel/replace/update cadence & atomicity (§14, §9–10)**  
Atomicity gap on `replaceOrders` (cancel succeeds but place fails), persistence-only via `updateOrders`, betDelay handling, single-retry policy — all correctly extracted from the respective Reference Guide pages.

---

## Findings — gaps

- **Long-term subscription pressure & 200-market limit (§5.1, §13.7)**: The brief handles dropping CLOSED markets after 60s (good). Sanctioned material confirms the hard limit but provides limited guidance on real-world safe operating numbers during peak AU racing + sports overlap.
- **Racing API ↔ Betfair market identity mapping**: Implicitly required for settlement and runner reconciliation. Neither API publishes a canonical join key; the brief correctly treats this as implementation detail (venue/time/race-number + harmonisation). Worth explicit tracking.
- **PASSIVE betDelayModel handling**: Correctly parked for v3.1. Documented in `MarketDefinition` but real-world usage (especially in-play sports) may require earlier attention.
- **Exact behaviour on very rapid reconnects / subscription churn**: Reference and samples are light on sustained high-frequency reconnect scenarios.

---

## Sections reviewed without findings

- §1 Framing & overall scope
- §2 Module shape, boundaries, parallel clients, versioned contract
- §3 Connection management (lifecycle, 15s auth rule, back-off)
- §7 Message handling, cache shape, delta semantics
- §11 Rate-limit & data-limit awareness
- §12 Operational live pricing cadence
- §17 What this closes (and downstream enablement)

---

## Notes for the operator / Code team

**Overall Assessment:**  
The brief is of high quality — comprehensive, disciplined, and strongly aligned with Betfair’s sanctioned documentation. It follows best practices (coarse subscriptions, streaming-first, clear error categorisation, boundary discipline, idempotency) and provides a solid contract for implementation.

**Strengths:**
- Excellent separation of concerns and staleness signalling.
- Strong emphasis on operational safety (single-retry, customerOrderRef, degradation surfaces, rate-limit enforcement).
- Good BSP and phase-aware handling tailored to Australian racing.

**Watch-outs for implementation:**
1. Reconnection / clock invalidation handling + full-image cost (test under simulated network instability).
2. Placement timeout + reconciliation path under burst conditions.
3. Subscription count monitoring and graceful degradation when approaching limits.
4. Currency rate refresh failure mode (hard alert is correct).
5. Logging of `connectionId`, request UUIDs, and `customerOrderRef` for support calls.

**Recommendation:**  
Proceed to implementation with high confidence. Any minor gaps are operational/edge-case in nature and well within the versioned-contract framework (§2.7). No material changes required to the brief.

---

**End of Detailed Report**  