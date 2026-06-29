# Review Findings: Betfair Streaming Spec §2.4

**Date:** 2026-05-03
**Document:** 2_4_betfair_streaming.md
**Status:** Thorough Review Completed

## 1. Executive Summary
The proposed spec for `betfair_client` is exceptionally well-structured and aligns with Betfair's "Best Practice" recommendations. The use of a dedicated I/O thread for the Stream API and the clear separation of the analytical vs. operational lines are key strengths.

## 2. Key Findings & Corrections

### 2.1 The "BSP is Safe to Read" Gate (Section 13.2)
* **Spec Logic:** Relies on `market_status` and `bsp > 0`.
* **Official Recommendation:** In the Stream API `MarketDefinition` object, the `bspReconciled` flag is the canonical signal. While your probe found it unreliable, I recommend using it as a secondary check: `(status in ['SUSPENDED', 'CLOSED']) AND bspReconciled == True AND bsp > 0`. This prevents reading "Near Price" projections that sometimes appear in the BSP field during the transition.

### 2.2 Currency Conversion (Section 16)
* **Verification:** Confirmed. Betfair Stream ladders are **always in GBP**. Your implementation of a conversion layer within `betfair_client` using `listCurrencyRates` is the correct way to maintain DR-028 discipline.

### 2.3 Idempotency and de-dup (Section 14.2)
* **Verification:** The distinction between `customerRef` (60s request de-dup) and `customerOrderRef` (instruction identity) is correct.
* **Note:** Ensure `customerRef` is unique per application key. If the operator uses multiple instances of v3 with the same key, a global unique prefix is needed.

### 2.4 Reconnection Token Discipline (Section 8)
* **Verification:** Your 2-token discipline (`initialClk` and `clk`) is the textbook implementation for "patching" a stream after a disconnect. This will save significant bandwidth and latency during standard operational drops.

## 3. Potential Inconsistencies
* **Section 11.2 Weights:** You correctly identify the 200-point ceiling. Be aware that `EX_BEST_OFFERS` with virtual price depth (LadderLevels=3) increases the weight. Your chunking strategy (10 markets per request) is a safe and appropriate buffer.

## 4. Final Verdict
The spec is **Build-Ready**. The error handling (Section 15) and staleness signaling (Section 7.8) are robust enough to handle the volatility of live racing markets.