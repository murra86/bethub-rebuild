# W4 follow-up Code report — REST-fetch fallback + price_source field + naming canonicalisation

**Status:** delivered Session 96 (single bounded Code session).
**Brief:** `dr029/w4_bet_entry/w4_followup_brief.md` (locked Session 96).
**Date:** 2026-05-07 (Adelaide local per DR-021).
**Audience:** operator-Claude triage, Session 97.

---

## §1 — Summary of what shipped

Six coordinated changes landed in one bounded Code session:

1. **§5.1 — `BetfairAdapter` Protocol extension.** New
   `fetch_fresh_runner_price` read-side method exposing the
   existing W3 `live_pricing` REST capability through the
   orchestrator's adapter boundary. `MockBetfairAdapter` gained a
   matching `queue_fresh_runner_price` test hook.
2. **§5.2 — `PriceSource` enum + `BetRecord.price_source`.** New
   optional field at the operational metadata block; default
   `None`; backward-compatible per Pydantic optional default.
   Threaded through `record_builder.py` inputs to the resulting
   `BetRecord`.
3. **§5.3 — Orchestrator REST-fetch branch.** When
   `_place_with_retry` receives a `betfair_streaming_disconnected`
   outcome (renamed per §5.6), the new `_place_via_rest_fetch`
   helper fetches a fresh REST price per the existing 50/200/500ms
   backoff schedule and places at that price; bet record carries
   `price_source=REST_FETCH`. Fall-through to the existing modal
   recovery wiring when REST is also unreachable; one-line
   comment names why the branch is retained per Session 96
   operator lock.
4. **§5.4 — `record_builder.py` NULL handling.**
   `build_soft_book_bet_record` now sets
   `soft_book_combined_price=None` unconditionally (single-leg
   territory in W4 v1; SGM_CORRELATED raises before reaching this
   code). Honest semantic per Session 95 operator decision.
5. **§5.6 — Naming canonicalisation.** Code chose **Option A —
   align on W3** (collapse three names to one canonical form
   `betfair_streaming_disconnected` lowercase across the W3/W4
   boundary). See §6.1 for rationale.
6. **§5.5 — §13 contract clarification paragraph.** New §13.5
   added; status header bumped from v1.1 to v1.3 (v1.2 amendment
   note also threaded into header to fix a stale-status bug
   surfaced during the edit — see §6.3); §6 history-row entry
   appended.

**Test delta.** +12 new tests (right at the brief's upper bound
of 8-12). Counts:

- Default `pytest` invocation (`tests/` only per
  `pyproject.toml` `testpaths`): 232 → 232 (no change at this
  testpath — see §8.1).
- `workflows/bet_entry/v1/tests/` (W4 module-local): 75 → 87.
- Combined coverage when run as
  `pytest tests/ workflows/bet_entry/v1/tests/`: 307 → 319.

Ruff clean across project; import-linter all 5 contracts kept;
zero regression.

---

## §2 — Modules edited

### §2.1 — `workflows/bet_entry/v1/models.py`

| Region | Change |
|---|---|
| Enum block (~line 123) | Added `PriceSource(str, Enum)` with three values: `STREAMING_CACHE`, `REST_FETCH`, `OPERATOR_TYPED`. Docstring anchors brief §5.2. |
| `BetRecord` operational metadata block (~line 230) | Added `price_source: PriceSource \| None = None` alongside `placed_at` / `book_or_exchange` / `account_at_book_id`. |

### §2.2 — `workflows/bet_entry/v1/__init__.py`

Added `PriceSource` to the models-import block and to the
alphabetically-sorted `__all__` models section.

### §2.3 — `workflows/bet_entry/v1/orchestrator.py`

| Region | Change |
|---|---|
| Imports (~line 43) | Added `from clients.betfair_client.v1.live_pricing import RunnerBestPrices`; added `PriceSource` to the models import. First W4 → W3 import (see §8.4). |
| `PlacementOutcome.outcome` Literal (~line 150) | Renamed `"streaming_blocked"` → `"betfair_streaming_disconnected"` per §5.6 Option A. Docstring updated. |
| `BetfairAdapter` Protocol (~line 195) | Added `fetch_fresh_runner_price(market_id, selection_id) -> RunnerBestPrices \| None`. |
| `_place_with_retry` (~line 675) | Return type changed from `PlacementOutcome` to `tuple[PlacementOutcome, PriceSource]`. New branch: `betfair_streaming_disconnected` outcome triggers `_place_via_rest_fetch`; cache-fresh path returns `STREAMING_CACHE`; REST-fetch path returns `REST_FETCH`. |
| `_place_via_rest_fetch` (new, ~line 745) | Calls `adapter.fetch_fresh_runner_price` retried per the existing 50/200/500ms backoff; reads the relevant side (`best_back` for BACK, `best_lay` for LAY); places via `place_hedge_bet` reusing the same `customer_order_ref` per contract §11.1 idempotency-key discipline. Returns `None` when REST returns None across all retries OR when the relevant side has no liquidity. |
| `place_hedge` body (~line 580) | Tuple-unpacks the new `_place_with_retry` return; passes `price_source` into `_hedge_inputs_from`. |
| `_hedge_inputs_from` / `_soft_book_inputs_from` | Now thread `price_source` through. Soft-book helper hard-wires `PriceSource.OPERATOR_TYPED` (see §6.4). |
| `_path_b_result` recovery wiring (~line 1057) | Recovery key check `"BETFAIR_STREAMING_DISCONNECTED"` → `"betfair_streaming_disconnected"` per §5.6. Added comment naming why the branch stays intact (Session 96 operator lock). |

### §2.4 — `workflows/bet_entry/v1/record_builder.py`

| Region | Change |
|---|---|
| Imports | Added `PriceSource` from models. |
| `HedgeRecordInputs` / `SoftBookRecordInputs` | Added `price_source: PriceSource \| None = None` to operational metadata block on both. |
| `build_hedge_bet_record` | Threads `inputs.price_source` into the resulting `BetRecord`. |
| `build_soft_book_bet_record` | (a) Threads `inputs.price_source` through. (b) `soft_book_combined_price=None` unconditionally per W4 follow-up §5.4 (single-leg has no combined price; SGM_CORRELATED raises in `_validate_strategy_tag` before reaching this code today). Comment names the discriminator and the future SGM hook. |

### §2.5 — `workflows/bet_entry/v1/tests/test_orchestrator.py`

Imports extended (`PriceLevel` / `RunnerBestPrices` from W3
live_pricing, `MarketStatus` from W3 settlement, `PriceSource`
from W4 models). `MockBetfairAdapter` extended with
`_fresh_price_responses` queue, `fresh_price_calls` recorder,
`queue_fresh_runner_price(...)` test hook, and
`fetch_fresh_runner_price(...)` Protocol implementation.
Helper `_runner_best_prices(...)` added; `_success_placement`
gained an optional `price` parameter. Seven new test cases
added — see §3.1.

### §2.6 — `workflows/bet_entry/v1/tests/test_record_builder.py`

Imports extended (`PriceSource`). Five new test cases added —
see §3.2.

### §2.7 — `dr029/2_7_api_contract_versioning/betfair_client_contract.md`

| Region | Change |
|---|---|
| Status header (line 3) | `v1.1 — F5 strategy_tag ...` → `v1.3 — §13 REST-fetch fallback clarification ...` with v1.2 amendment note also rolled in (see §6.3). |
| §6 history table (~line 169) | Appended one row dated 2026-05-07 attributing v1.3 backward-compatible clarification to Session 96 W4 follow-up Code; closes brief §5.5. |
| §13.5 (new, after §13.4) | New subsection "REST-fetch fallback at placement time" per the brief's suggested wording. Spells out: rule applies to streaming-cache placements; fresh-REST-price placements preserve the rule's intent; `betfair_client` block at §11.1 operates on streaming state alone; v3 carries `price_source=REST_FETCH` for transparency. |

---

## §3 — Tests built

**Total new tests:** 12. Zero regression on the 75 existing W4
tests or the 232 baseline `tests/` collection.

### §3.1 — `test_orchestrator.py` (7 new)

| Test | Coverage |
|---|---|
| `test_betfair_adapter_protocol_has_fetch_fresh_runner_price` | Protocol method exists with expected signature; `MockBetfairAdapter` implements it; default-no-queue returns `None`; queued response returns through. |
| `test_streaming_blocked_rest_fetch_succeeds` | Streaming-blocked → REST returns price → second placement at fresh price → bet record carries `price_source=REST_FETCH`. Asserts orchestrator placed at fresh price (4.30), not the operator-typed price (4.20). |
| `test_streaming_blocked_rest_fetch_reuses_customer_order_ref` | Per contract §11.1: same `customer_order_ref` reused across both placement attempts. |
| `test_streaming_blocked_rest_fetch_fails_modal_recovery` | REST returns `None` across all 3 retries → falls through to existing modal recovery; modal surfaces "Wait and retry". 1 placement attempt + 3 REST-fetch retries; no second placement. |
| `test_streaming_blocked_rest_fetch_no_liquidity_fails` | REST fetch returns valid `RunnerBestPrices` but with `best_lay=None` for a LAY bet. Treated as if REST fetch had failed; falls through to modal recovery. |
| `test_happy_path_carries_streaming_cache_source` | Cache-fresh happy path: bet record carries `price_source=STREAMING_CACHE`. |
| `test_streaming_blocked_back_side_uses_best_back` | Side discrimination: BACK bets read `best_back`; LAY bets read `best_lay`. |

### §3.2 — `test_record_builder.py` (5 new)

| Test | Coverage |
|---|---|
| `test_single_leg_soft_book_combined_price_is_null` | Soft-book inputs carry `soft_book_combined_price=4.00`; output `BetRecord` carries `None` (single-leg discriminator collapses to "always NULL"). |
| `test_single_leg_hedge_record_carries_price_source_streaming_cache` | Round-trip: hedge inputs `STREAMING_CACHE` → output `STREAMING_CACHE`. |
| `test_single_leg_hedge_record_carries_price_source_rest_fetch` | Round-trip: hedge inputs `REST_FETCH` → output `REST_FETCH`. |
| `test_single_leg_soft_book_record_carries_operator_typed_source` | Round-trip: soft-book inputs `OPERATOR_TYPED` → output `OPERATOR_TYPED`. |
| `test_price_source_defaults_to_none_when_unset` | Backward-compatibility: hedge record built without `price_source` carries `None`. |

---

## §4 — Test results

```
$ .venv/bin/python -m pytest 2>&1 | tail -10
============================= 232 passed in 0.37s ==============================

$ .venv/bin/python -m pytest tests/ workflows/bet_entry/v1/tests/ 2>&1 | tail -5
============================= 319 passed in 0.42s ==============================

$ .venv/bin/python -m pytest workflows/bet_entry/v1/tests/ 2>&1 | tail -5
============================== 87 passed in 0.11s ==============================

$ .venv/bin/python -m ruff check . 2>&1 | tail -5
All checks passed!

$ .venv/bin/lint-imports 2>&1 | tail -10
DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT
Contracts: 5 kept, 0 broken.
```

Default `pytest` (232 baseline) shows zero regression but no
new tests visible — testpath config excludes
`workflows/bet_entry/v1/tests/`. See §8.1.

Manual spot-check confirmed `BetRecord.price_source` lands at
`models.py:230`, adjacent to `placed_at` / `book_or_exchange`
/ `account_at_book_id` per brief §5.2 anchor.

---

## §5 — Linting + import-linter

Already covered in §4. The new W4 → W3 import
(`RunnerBestPrices`) is permitted by the DR-030 layered-
architecture contract (`workflows` → `clients` is a top-down
dependency). No additional contract edits required.

---

## §6 — Deviations from brief

### §6.1 — §5.6 canonicalisation: Code chose **Option A — align on W3**

Brief §5.6 invited Code's call between aligning on W3
(`betfair_streaming_disconnected` everywhere) or aligning on W4
short form (`streaming_blocked` everywhere).

**Code's choice: Option A.** Rationale:

1. **True canonicalisation collapses to one name.** The brief's
   stated goal was "collapse to one canonical form." Option A
   produces one name across the W3/W4 boundary; Option B keeps
   two (W3 `betfair_streaming_disconnected` + W4
   `streaming_blocked`).
2. **Future real-adapter translation is trivial.** Under Option
   A the W3 envelope `reason` value flows through to the W4
   outcome literal unchanged (no string mapping); under Option
   B the adapter would carry an explicit translation.
3. **Trade-off accepted.** Option A's downside is the longer
   routing-tag string compared to peers (`success`,
   `retry_safe`, `terminal`); Code judged the canonicalisation
   win to outweigh the cosmetic asymmetry.

Tests, code references, and contract anchors all use the new
canonical form.

### §6.2 — Modal recovery wiring comment wording

Brief §5.3 said: "Code names the branch with a one-line comment
… explaining why it's retained as a rare-path fallback."
Comment landed at `_path_b_result` (~line 1052):

```python
# Error-code-keyed extra recovery actions per brief §5.3.
# The streaming-disconnected branch is retained as a rare-
# path fallback for the Betfair-fully-down edge case (REST
# also unreachable per W4 follow-up §5.3 fallback chain
# step 3); operator-locked Session 96.
```

No logic changes to the branch itself — just the case-rename
in the recovery-key set per §6.1.

### §6.3 — Contract status header: stale `v1.1` → fresh `v1.3` (with v1.2 also rolled in)

Brief said update header from `v1.1` to `v1.3`. The header was
indeed `v1.1` even though §6 history already had a v1.2 entry
from Session 94. Code rolled in both v1.2 (Session 94) and v1.3
(this brief) amendment notes into the status header in a single
update — preserving the brief's intent while fixing a stale-
status-text bug.

### §6.4 — `price_source=OPERATOR_TYPED` populated at orchestrator boundary

Brief §5.2 named three `PriceSource` values without explicitly
directing where `OPERATOR_TYPED` is populated. Code populates it
at `_soft_book_inputs_from` (the orchestrator-side helper that
converts a `SoftBookLogRequest` into `SoftBookRecordInputs`)
because soft-book legs are always operator-typed by definition
(no v3-side price feed for soft-book bookmakers per math review
§1). One-site placement; uniform soft-book records carry the
flag.

### §6.5 — `_place_with_retry` tuple-return shape change

Brief §5.3 named the REST-fetch wiring without specifying how
`price_source` flows from the placement layer to the bet-record
build path. Code chose `tuple[PlacementOutcome, PriceSource]`
return rather than (a) adding `price_source` to
`PlacementOutcome` (rejected: per-attempt vs per-bet-overall
concept conflation) or (b) thread-local state (rejected:
violates pure-call discipline). The tuple ripples cleanly to
one call site (`place_hedge`), which already tuple-unpacks.

---

## §7 — Open questions

### §7.1 — REST-fetch implicit "non-None means fresh" contract

The Protocol method returns `RunnerBestPrices` directly (the
`FreshEnvelope` wrapping is unwrapped by the future real
adapter). The implicit contract is "if `fetch_fresh_runner_price`
returns non-None, the price IS fresh" — REST guarantees freshness
per W3 contract §4. Worth confirming this is sufficient or whether
the future adapter should set `price_source=STREAMING_CACHE` on
some edge-case "stale REST" outcome. Probably nothing.

### §7.2 — `OPERATOR_TYPED` for hedge bets where the operator manually overrode the price

The orchestrator wires `STREAMING_CACHE` for cache-fresh and
`REST_FETCH` for REST-fallback. If the operator manually
overrides `request.proposed_price` at modal-confirm time (W7's
UI behaviour), the bet record's `price_source` will be
`STREAMING_CACHE` even though the price was operator-typed.
Whether the override case warrants a fourth source value —
or is captured elsewhere on the operator-input shape — is W7-
adjacent and out of this brief's scope.

### §7.3 — Modal recovery copy after REST-fetch failure

When REST also fails, modal surfaces "Wait and retry" — the
same recovery option as `MARKET_SUSPENDED`. Whether the
operator-facing message should distinguish "streaming
disconnected, REST also unreachable" from
"streaming disconnected (try the cache again)" is W7
modal-copy territory.

---

## §8 — Findings

### §8.1 — `pyproject.toml` `testpaths = ["tests"]` excludes W4 module-local tests from default pytest

The brief expected `pytest 240-244 passing` from the default
invocation. Actual count under default invocation is `232 → 232`
because `pyproject.toml` line 45 sets `testpaths = ["tests"]`
and the W4 tests live module-local at
`workflows/bet_entry/v1/tests/`. 75 existing + 12 new W4 tests
are invisible to the default invocation.

Two possible operator-Claude routes:

1. **Move W4 tests under `tests/`** (e.g.,
   `tests/workflows/bet_entry/v1/`) to bring them under the
   configured testpath. Aligns with `tests/clients/...`
   convention.
2. **Extend `testpaths`** to include
   `workflows/bet_entry/v1/tests/` (and presumably future
   workflow test dirs by glob). Single-line config change.

Either route is config-housekeeping outside this brief's scope.

### §8.2 — SQLite stub at `storage.py` doesn't round-trip `price_source`

The `workflows/bet_entry/v1/storage.py` SQLite reference
implementation has DDL for the `bets` table at lines ~86-105
listing 17 columns; INSERT/SELECT statements at lines ~252-282
and ~378-405 don't touch `price_source`. SQLite write skips
the field; read defaults to None.

Effect on this brief's test scope: none. `test_record_builder.py`
exercises the in-memory model; `test_orchestrator.py` uses
`InMemoryBetRecordStorage` which preserves all Pydantic fields.
Existing `test_sqlite_round_trip` doesn't assert on `price_source`.

The brief's hard limit "No SQL schema changes" was rationalised
by Code preflight noting `store/schema/`, `store/repositories/`,
`domain/bets/` are empty — but the W4 v1 SQLite stub at
`workflows/bet_entry/v1/storage.py` does have DDL. Code
honoured the hard limit literally; the discrepancy between
brief premise and reality matters for sequencing the next
session's work.

Routing options:

1. **Add the column in the next session** (small DDL change
   alongside whatever future store work picks up).
2. **Leave the stub as-is** — store-proper work in
   `store/schema/` will model `price_source` correctly when it
   lands; the W4 stub is throwaway.

Operator-Claude call.

### §8.3 — Recovery-key set mixes naming conventions

After §5.6 canonicalisation, the `_path_b_result` set looks
like `{"MARKET_SUSPENDED", "betfair_streaming_disconnected"}` —
upper-snake-case (Betfair API status code style) and lower-
snake-case (W3 reason-enum-value style) coexisting. Out of
brief scope to standardise.

### §8.4 — `RunnerBestPrices` import is the first W4 → W3 dependency

Pre-brief: `orchestrator.py` had no imports from `clients/` —
the Protocol abstracted the W3 boundary by defining W4-side
types. Post-brief: orchestrator imports `RunnerBestPrices`
from W3 directly per brief §5.1. Operationally fine
(`RunnerBestPrices` is a small, stable shape) but worth flagging
as the first crack in the W3/W4-types-fully-decoupled
discipline. If a future Protocol extension also returns a W3
type, the pattern is established.

---

## §9 — Self-assessment

### §9.1 — Session-budget fit

All six locked items shipped in one bounded session: §5.1
Protocol extension + §5.2 enum + field + §5.3 orchestrator
REST-fetch wiring + §5.4 record_builder NULL handling + §5.5
contract paragraph + §5.6 naming canonicalisation. 12 new tests
landed (right at the brief's upper bound). Zero regression;
ruff clean; import-linter clean. Report sits within the
300-450 line target.

### §9.2 — Confidence regions

**High confidence:**

- §5.1 Protocol extension shape + return type + mock test hook.
- §5.2 enum + field placement + backward-compat at the model
  layer.
- §5.3 wiring logic + side-discrimination + customer_order_ref
  reuse + fall-through-on-no-liquidity (all four scenarios have
  explicit test cases).
- §5.4 NULL handling + future-SGM hook.
- §5.5 contract paragraph + history row + status header roll-
  forward.
- §5.6 canonicalisation Option A: argued in §6.1.

**Lower confidence (flagged in §7 / §8):**

- Whether `pyproject.toml` testpaths should be widened (§8.1).
- Whether SQLite stub gets `price_source` column added in next
  session vs left to store-proper (§8.2).
- Whether the implicit "REST returns means fresh by definition"
  contract needs explicit assertion (§7.1).

### §9.3 — What the operator should look at first

In rough priority order:

1. **§6.1 (canonicalisation Option A choice)** — Code picked
   one of two reasonable options the brief invited; ripples
   into the future real-adapter brief.
2. **§8.1 (testpaths exclude W4 module-local tests)** —
   affects future-brief verification arithmetic; future briefs
   should use the explicit two-testpath invocation OR a config
   widening.
3. **§8.2 (SQLite stub doesn't round-trip price_source)** —
   want a routing decision before the real-adapter brief lands
   and exercises the SQLite path.
4. **§6.3 (status header v1.1 → v1.3 stale-fix)** — minor
   bookkeeping; mention only because it deviates from the
   brief's literal text.
5. **§6.5 (`_place_with_retry` tuple-return shape change)** —
   the brief didn't specify how `price_source` flows from the
   placement layer to the bet-record build; tuple return is
   Code's call.

The rest of §6/§7/§8 entries are smaller flags routing through
Cat 1 / Cat 2 / Cat 3 of operator-Claude's framework without
much weight.

---

**End of report.**
