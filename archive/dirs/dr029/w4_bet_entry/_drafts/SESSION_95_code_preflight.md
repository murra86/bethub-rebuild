# Session 95 W4 follow-up — Code preflight investigation

**Date:** 2026-05-07 (Adelaide local)
**Scope:** read-only investigation of `bethub-v3` for the operator-Claude
W4 follow-up brief (W4 report §7.4 streaming-blocked reclassification +
§7.6 `soft_book_combined_price` NULL-for-single-leg).
**No edits, no git, no test runs, no Betfair calls.**

---

## §1 — REST price-fetch surface

**(a)** Yes — REST price-fetch surfaces exist in
`clients/betfair_client/v1/live_pricing.py`. Two functions, both
exported from `__init__.py`. They share one implementation file and
both run cache-first / REST-fallback routing already.

**(b)** Two functions:

- `market_prices(market_id, rest_client, streaming_client=None) -> ReadEnvelope[MarketPrices]`
  — full market book (lines 137–157). When `streaming_client` is
  `None` or the cache misses, calls `_market_prices_via_rest`
  (lines 112–134) hitting `/v1/market/{market_id}/prices`.
- `runner_best_prices(market_id, selection_id, rest_client, streaming_client=None) -> ReadEnvelope[RunnerBestPrices]`
  — single-runner shortcut (lines 160–207). Same routing rule. REST
  path: `/v1/market/{market_id}/runner/{selection_id}/best`.

Consumer-side helpers `get_live_market_prices(market_id, client)` /
`get_runner_best_prices(market_id, selection_id, client)` exported
from `consumer.py` accept the bundled `BetfairClient`
(REST + optional streaming).

**(c)** Pydantic v2 return shapes (all in `live_pricing.py`),
wrapped in `ReadEnvelope[...]` (`FreshEnvelope` / `StaleEnvelope` /
`UnavailableReadEnvelope`). REST path returns `fresh` or
`unavailable`; `stale` is streaming-cache-only.

- `MarketPrices` — `market_id`, `market_status` (OPEN/SUSPENDED/CLOSED
  enum), `in_play`, `bsp_reconciled`, `bet_delay_seconds`,
  `scheduled_start_time`, `total_market_traded_volume`,
  `runners: list[RunnerPrices]`, `cache_as_of`.
- `RunnerPrices` — `selection_id`, `runner_status`,
  `best_back/best_lay: list[PriceLevel]`, `last_traded_price`,
  `sp_near/sp_far`, `total_runner_traded_volume`.
- `RunnerBestPrices` — `market_id`, `selection_id`, `market_status`,
  `best_back/best_lay: PriceLevel | None`, `cache_as_of`. Level-0
  only on this shape.
- `PriceLevel` — `price`, `size` (AUD-equivalent).

**(d)** Single-market fetch only. Both functions take exactly one
`market_id`. No multi-market list surface. (Closest multi-market
shape is `sports_market_variants(event_id, market_type)` per §9.3 —
filter-by-event, not arbitrary multi-market list.)

**Note for the brief.** REST-fallback for streaming-blocked is
implementable today by calling `runner_best_prices(...,
streaming_client=None)` or `_market_prices_via_rest(...)` directly.
No new contract surface or new module needed. The orchestrator's
`BetfairAdapter` Protocol would need a new "fetch fresh price"
read-side method — it currently exposes only `place_hedge_bet`,
`get_market_status`, `get_account_funds`, `get_order_state`
(no live-pricing read).

---

## §2 — Bet-record `price_source` field

**(a)** No `price_source` field exists today. Searched
`bethub-v3/` end-to-end (`grep -rn "price_source\|priceSource"
--include="*.py"` and same on the W4 brief) — zero hits.

**(b)** N/A. Closest existing field is `book_or_exchange: str` on
`BetRecord` (operational metadata — `'betfair'` for hedge leg,
soft-book book name otherwise). That's source-of-the-bet, not
source-of-the-price.

**(c)** N/A.

**Where it would slot in.** `workflows/bet_entry/v1/models.py` —
`BetRecord` (lines 177–222), in the "Operational metadata" block
(lines 212–215, alongside `placed_at` / `book_or_exchange` /
`account_at_book_id`). Natural shape:

```python
class PriceSource(str, Enum):
    STREAMING_CACHE = "streaming_cache"
    REST_FETCH = "rest_fetch"
    OPERATOR_TYPED = "operator_typed"  # soft-book entries

# inside BetRecord
price_source: PriceSource | None = None
```

`BetRecord` is `frozen=True`; adding optional field with default
`None` is backward-compatible at the model layer. There is no SQL
schema yet — `store/schema/`, `store/repositories/`, `domain/bets/`
are empty `__init__.py` placeholders, so no DB-side coordination
required.

**Per-leg vs per-record.** `BetLeg` (lines 128–174) carries Betfair
identifiers + Set B snapshot. A case can be made for `price_source`
on `BetLeg` (future SGM workflows could mix sources per leg), but
W4 v1 ships single-leg only and the brief framing says "flag the
record" — `BetRecord` placement matches. Operator-Claude's call.

---

## §3 — Current streaming-blocked error handling

Classification lives at two layers, with one production site.

**(a) File and line range.** Single production site:
`clients/betfair_client/v1/placement.py:155–186` —
`place_bet`'s streaming-state pre-check at function entry. When
`streaming_status().state != SUBSCRIBED`, `place_bet` short-circuits
with `UnavailableWriteEnvelope(reason=BETFAIR_STREAMING_DISCONNECTED,
retry_after=10, ...)` and emits an audit entry with
`WriteOutcome.STREAMING_DISCONNECTED`. This is the contract §13
"streaming-disconnect-blocks-writes" implementation.

W4 orchestrator carries a parallel classification slot at
`workflows/bet_entry/v1/orchestrator.py:147` —
`PlacementOutcome.outcome: Literal["success", "retry_safe", "terminal", "streaming_blocked"]`.
Handler at `_place_with_retry` (lines 645–685) — line 677 treats
`streaming_blocked` identically to `retry_safe` (back off + retry,
brief §5.3 50/200/500ms). Modal-side recovery hint at
`_path_b_result` (lines 942–946) — when
`outcome.error_code == "BETFAIR_STREAMING_DISCONNECTED"`, recovery
options gain "Wait and retry".

**(b) Current category.** Two layers:

- **W3 (`betfair_client`)**: `UnavailableWriteEnvelope` with
  `reason=BETFAIR_STREAMING_DISCONNECTED` (a read-side reason
  applied to a write outcome per contract §8.3). Audit log records
  `WriteOutcome.STREAMING_DISCONNECTED`.
- **W4 orchestrator**: routed through `streaming_blocked`
  PlacementOutcome value, then collapsed into the retry-safe branch
  behaviourally. Brief §5.3 doesn't list streaming-disconnect
  explicitly; the orchestrator docstring (line 654) names the choice
  as "Streaming-disconnect is treated as retry-safe."

Net: nominally a fourth distinct category at the Protocol shape,
collapsed into retry-safe at runtime.

**(c) Centralised vs scattered.** Centralised. One production site
(W3 `place_bet` pre-check). W4 Protocol carries one slot, one
handler. No real `BetfairAdapter` exists yet — only
`MockBetfairAdapter` in `tests/test_orchestrator.py`, which doesn't
construct `outcome="streaming_blocked"` in any test today. Nothing
in production code path produces this value. The future real
adapter (sequenced Session 96+) will carry the
W3-envelope → W4-PlacementOutcome translation in one place.

A REST-fallback reclassification therefore touches three coordinated
sites:

1. W3 `place_bet` pre-check stays as-is (or gets an opt-in
   REST-fetch parameter).
2. Orchestrator's `_place_with_retry` adds a REST-fetch branch when
   `outcome=="streaming_blocked"` (instead of retry-safe).
3. `BetfairAdapter` Protocol gains a "fetch fresh price" read-side
   method exposing the existing `runner_best_prices` /
   `market_prices` REST path.

No scattered classification to consolidate first — the change is
greenfield wiring of existing W3 capability, not refactor of
existing handling.

---

## §4 — Self-assessment / adjacent observations

- **REST fallback already exists at the W3 layer.** `live_pricing.py`
  cache-first / REST-fallback routing is the default. The brief
  doesn't need a new REST surface — only Protocol extension +
  orchestrator wiring.
- **No real `BetfairAdapter` exists yet.** Today's
  `streaming_blocked` outcome is reachable only through a
  hypothetical adapter. The §7.4 reclassification is effectively a
  Protocol-shape + orchestrator-handler change, not a refactor of
  running code.
- **`PlacementOutcome.raw: dict[str, object]`** (line 155) is a
  Betfair-side detail slot. A REST-fetch fallback could surface the
  fetched-price snapshot there, or add an explicit
  `rest_fetch_price: float | None` field — brief should name which.
- **Modal recovery wiring may go unreachable post-change.**
  `_path_b_result` line 942 special-cases
  `BETFAIR_STREAMING_DISCONNECTED` for recovery messaging. If
  REST-fallback reclassifies to successful-with-flag (not path-b),
  this branch is unreachable; brief should name whether to prune.
- **§7.6 not investigated** per operator scope. Flag only:
  `BetRecord.soft_book_combined_price` is `float | None` today
  (models.py:210); no shape change needed for NULL-for-single-leg.
- **Naming inconsistency across W3/W4 boundary.** W3 reason
  `betfair_streaming_disconnected` (lowercase); W4 outcome
  `"streaming_blocked"` (different word); orchestrator recovery-key
  `BETFAIR_STREAMING_DISCONNECTED` (uppercase). Three surface
  representations of the same concept — worth one brief sentence on
  canonicalisation.
- **`BetRecord.frozen=True`** — adding `price_source` is backward-
  compatible if optional with default `None`; `record_builder.py`
  callers and direct-construction tests need touching only if the
  field is made required.
- **Confidence.** All three answers anchored on direct file reads
  and explicit greps. Only uncertainty: per-record vs per-leg
  placement of `price_source` (flagged in §2).
