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
