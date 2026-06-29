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
