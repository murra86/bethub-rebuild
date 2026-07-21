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
