# W3 order-state read surface + read-side boundary pass-through report

**Session opened:** 2026-05-07 16:35 ACST
**Session closed:** 2026-05-07 16:50 ACST
**Brief:** `dr029/w4_bet_entry/w3_order_state_brief.md`
**Pre-flight:** `dr029/w4_bet_entry/w3_order_state_preflight.md`
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`
**Code session:** out-of-session, single bounded run

---

## §1 — Summary

All §5 substantive scope sections of the brief shipped end-to-end in
one bounded session.

**Shipped:**

- New W3 read surface `clients/betfair_client/v1/current_orders.py`
  exposing `list_current_orders(rest_client, *, market_id=None,
  bet_id=None) -> ReadEnvelope[OrderStateList]` per brief §5.1, with
  `OrderRecord` and `OrderStateList` Pydantic shapes mirroring the
  account-funds shape precedent (162 lines).
- New W3 surface tests at
  `tests/clients/betfair_client/v1/test_current_orders.py` — 14 tests
  covering fresh empty / single / multi orders, four filter
  combinations, defensive parsing of optional fields, three
  unavailable-reason paths, filter validation, and Adelaide-local
  timestamp discipline (350 lines).
- W4 boundary discriminated-union models `ReadOk[T]`, `ReadUnavailable`,
  `ReadOutcome[T]` added to `workflows/bet_entry/v1/orchestrator.py`
  per brief §5.5; the three `BetfairAdapter` Protocol read methods
  updated to return `ReadOutcome[T]` instead of bare snapshot / `None`.
- `RealBetfairAdapter` rewired in
  `workflows/bet_entry/v1/betfair_adapter.py` per brief §5.6: read-side
  pass-through routing now carries the unavailable-reason verbatim;
  `get_order_state` stub replaced with a real wrap of
  `list_current_orders` (closes the W4 real-adapter report §8.1
  finding); SUSPENDED special case in `get_market_status` dropped per
  the §5.6 behaviour-preserving rewire.
- Orchestrator call sites at `_market_status_check`,
  `_fundedness_check`, `_read_order_state_with_retry`, and the
  Trigger B downstream caller updated per brief §5.7 to switch on
  `ReadOk` / `ReadUnavailable` and preserve the unavailable-reason
  on the `PreFlightFlag.detail` for downstream layers.
- `MockBetfairAdapter` in `test_orchestrator.py` updated per brief §5.8
  to return `ReadOutcome[T]` shapes; `set_market_status_unavailable`
  / `set_account_funds_unavailable` test setters added so future
  tests can pin a specific reason value.
- `test_betfair_adapter.py` restructured per brief §5.10 — three
  read-method tests rewritten for the `ReadOutcome` shape, four new
  `get_order_state` real-path tests added (partial-match, fully-matched-
  in-orders, resolved-out-of-orders, auth-expired pass-through), plus
  pass-through coverage for `betfair_auth_expired` on
  `get_market_status` and `get_account_funds`.
- `__init__.py` re-exports updated per brief §5.2 — `OrderRecord`,
  `OrderStateList`, `list_current_orders` added to imports and
  `__all__` in alphabetical order within the read-surfaces block.
- `_translation.py` extended per brief §5.4 — `/v1/orders/current`
  → `SportsAPING/v1.0/listCurrentOrders` request/response translators
  added (previously not covered; the path-style routing is endpoint-
  specific, not generic).
- Contract spec at
  `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  updated per brief §5.3 — new §9.8 `Order-state reads` block,
  Status line bumped to v1.4, §6 version-history v1.4 row added,
  §15.4 carve-out narrowed further to admit `listCurrentOrders`
  alongside `getAccountFunds`.

**Not shipped:** nothing in scope was deferred. The brief's §1 / §9
out-of-scope list (composition root, modal copy, auth-refresh, schema
changes, etc.) was respected throughout — see §6 deviations and §8
findings for the few judgement calls.

**Test count:** 342 → 361 (+19 net new tests passing).
**ruff:** clean before, clean after.
**import-linter:** 5 contracts kept before, 5 kept after.

---

## §2 — Files changed

| File | Pre lines | Post lines | Δ |
|---|---:|---:|---:|
| `clients/betfair_client/v1/current_orders.py` (new) | 0 | 162 | +162 |
| `clients/betfair_client/v1/__init__.py` | 175 | 183 | +8 |
| `clients/betfair_client/v1/_translation.py` | 664 | 737 | +73 |
| `workflows/bet_entry/v1/orchestrator.py` | 1356 | 1459 | +103 |
| `workflows/bet_entry/v1/betfair_adapter.py` | 345 | 406 | +61 |
| `tests/clients/betfair_client/v1/test_current_orders.py` (new) | 0 | 350 | +350 |
| `tests/workflows/bet_entry/v1/test_betfair_adapter.py` | 614 | 773 | +159 |
| `tests/workflows/bet_entry/v1/test_orchestrator.py` | 1102 | 1196 | +94 |
| `dr029/2_7_api_contract_versioning/betfair_client_contract.md` | 1362 | 1486 | +124 |

Total LOC delta on production code: +407. Total LOC delta on tests:
+603. Total LOC delta on contract spec: +124.

No file outside the brief's named anchors was touched. No git
operations were run.

---

## §3 — Test count delta

**Pre-baseline:**

- 342 tests collected, 342 passed
- ruff: clean
- import-linter: 5 contracts kept, 0 broken
- working tree: pre-Session-101 state — `__init__.py` modified;
  `account_funds.py`, `market_catalogue.py`, the W4 workflow tree,
  the W4 workflow tests, and the `test_account_funds.py` /
  `test_market_catalogue.py` test files all untracked. This matches
  the Session 100 close state per `real_adapter_report.md` §9 plus
  the `dr029/w4_bet_entry/w4_followup_report.md` carry from Session
  97.

**Post-execution:**

- 361 tests collected, 361 passed
- ruff: clean
- import-linter: 5 contracts kept, 0 broken
- working tree: previous untracked + new `current_orders.py` +
  `test_current_orders.py`; `__init__.py` and `_translation.py`
  modified additionally. No unintended drift outside named anchors.

**Net delta:** +19 tests passing.

This exceeds the brief's +6 to +12 guide range by +7. Breakdown:

- `test_current_orders.py` shipped 14 tests covering all §5.9 areas
  (fresh empty / single / multiple, four filter combinations including
  none/either/both, defensive optional-field parsing, three
  unavailable-reason paths, two filter-validation cases, and
  Adelaide-local timestamp). The brief's §5.9 enumerates these areas
  explicitly; 14 fell out from one test per area without bunching.
- `test_betfair_adapter.py` net delta is +5 (was 19, now 24): 1 stub
  test deleted, 4 new `get_order_state` real-path tests, plus 2
  added pass-through reason tests (auth-expired on
  `get_market_status` and `get_account_funds`).

The brief explicitly says `Final count is whatever Code lands; 6-12
is the guide range, not a hard target` so this is named here for
visibility, not flagged as a deviation. The 14 W3 surface tests
each cover a distinct §5.9 area; the +5 adapter-side delta hits
the upper end of the brief's 3-7 guide. Both are within the spirit
of the brief's coverage expectations.

---

## §4 — New tests added

### §4.1 — `tests/clients/betfair_client/v1/test_current_orders.py` (14 tests)

Fresh paths (8):

- `test_list_current_orders_empty_returns_fresh_envelope` — `orders=[]`
  is a valid fresh result.
- `test_list_current_orders_single_order_parses_correctly` — full
  field-by-field parse of an `OrderRecord`.
- `test_list_current_orders_multiple_orders_preserve_order` — list
  ordering preserved.
- `test_list_current_orders_market_filter_passes_through` — `market_id`
  alone in the query string.
- `test_list_current_orders_bet_filter_passes_through` — `bet_id`
  alone.
- `test_list_current_orders_both_filters_pass_through` — both filters
  combined.
- `test_list_current_orders_no_filter_omits_query` — no filter →
  no query string.
- `test_list_current_orders_optional_fields_handle_omission` —
  defensive parsing per account-funds precedent.

Filter validation (2):

- `test_list_current_orders_empty_market_filter_rejected` — empty
  string `market_id` raises `ValueError`.
- `test_list_current_orders_empty_bet_filter_rejected` — empty
  string `bet_id` raises `ValueError`.

Unavailable paths (3):

- `test_list_current_orders_auth_expired_returns_unavailable` (401).
- `test_list_current_orders_api_unreachable_returns_unavailable` (503).
- `test_list_current_orders_rate_limited_returns_unavailable_with_retry_after`
  (429 with `retry_after`).

Adelaide local timestamps per DR-021 (1):

- `test_list_current_orders_cache_as_of_uses_adelaide_local` —
  envelope `as_of` and `data.cache_as_of` both Adelaide-local on the
  pinned-clock fixture.

### §4.2 — `tests/workflows/bet_entry/v1/test_betfair_adapter.py` deltas

Restructured for `ReadOutcome` shape (3):

- `test_get_market_status_open` — asserts `ReadOk` wrapping the
  snapshot.
- `test_get_market_status_suspended_passes_through` (renamed from
  `test_get_market_status_suspended`) — asserts
  `ReadUnavailable(reason="betfair_market_suspended")` per brief
  §5.6 behaviour-preserving rewire.
- `test_get_market_status_api_unreachable_passes_through` (renamed
  from `test_get_market_status_unavailable_returns_inactive`) —
  asserts `ReadUnavailable(reason="betfair_api_unreachable")`.
- `test_get_account_funds_fresh` — asserts `ReadOk` wrapping the
  snapshot.
- `test_get_account_funds_rate_limited_passes_through` (renamed
  from `test_get_account_funds_unavailable_returns_none`) — asserts
  `ReadUnavailable(reason="betfair_rate_limited")`.
- `test_get_account_funds_decimal_precision` — adjusted for the
  unwrap.

New (6):

- `test_get_market_status_auth_expired_passes_through` — pass-through
  coverage for the auth-expired routing per Session 100 §7.1
  fold-in.
- `test_get_account_funds_auth_expired_passes_through` — same for
  account-funds.
- `test_get_order_state_partially_matched` — bet found in current
  orders with partial match → `ReadOk` snapshot reflects matched /
  unmatched split, `found_in_unmatched=True`.
- `test_get_order_state_fully_matched_in_orders` — bet found with
  `size_remaining=0` → `found_in_unmatched=False` despite the bet
  still appearing in the list.
- `test_get_order_state_resolved_out_of_orders` — bet absent from
  current orders → adapter constructs the resolved-out snapshot
  (`matched_size=original_size`, `found_in_unmatched=False`).
- `test_get_order_state_auth_expired_passes_through` — `ReadUnavailable`
  with `reason="betfair_auth_expired"` per the §7.1 fold-in.

Removed (1):

- `test_get_order_state_stub_returns_none` — the stub it tested no
  longer exists.

### §4.3 — `tests/workflows/bet_entry/v1/test_orchestrator.py`

Net delta: 0 tests (still 30). The `MockBetfairAdapter` was reshaped
internally to return `ReadOutcome[T]` and the existing `set_*` /
`queue_order_state` API was preserved (with the historical `None`
sentinel for queue_order_state continuing to mean "unavailable" — it
now routes to `ReadUnavailable(reason="betfair_api_unreachable")`).
All 30 tests pass unchanged.

---

## §5 — Implementation notes

### §5.1 — `_translation.py` answer (brief §5.4)

The brief asked Code to determine whether the new endpoint already
routes via the existing path-style → JSON-RPC translation, or
whether it needed an explicit translation entry.

**Answer: not covered; explicit entry added.** The translation
layer's request/response routing is endpoint-specific (each path has
its own compiled regex matcher and translator function). Added:

- `_ORDERS_CURRENT_RE = re.compile(r"^/?v1/orders/current/?$")` regex.
- `_build_list_current_orders_params(query)` request builder mapping
  `market_id` query → `marketIds` list and `bet_id` query → `betIds`
  list per Betfair's `listCurrentOrders` filter shape.
- `_translate_list_current_orders(result)` response translator
  converting Betfair's `currentOrders` summary list into the v3
  path-style payload that `current_orders._parse` expects.
- Header docstring updated with the new
  `GET /v1/orders/current → listCurrentOrders` line.

The route uses `SportsAPING/v1.0/listCurrentOrders` matching the
existing `placeOrders` / `cancelOrders` / `replaceOrders`
namespacing — Betfair's JSON-RPC namespace is unified, even though
the brief docstring example mentions `BettingAPING/v1.0/...`. See
§6 deviation 4.

### §5.2 — Resolved-out-of-orders treatment in `get_order_state`

Per brief §5.6, when the named `bet_id` does not appear in the W3
`list_current_orders` payload, the adapter constructs a snapshot
expressing "fully resolved" with `matched_size=original_size`,
`unmatched_size=0`, `average_matched_price=None`,
`found_in_unmatched=False`. This is the dominant case at Trigger B
read time (fully matched bets fall out of current orders within
seconds of full match). The brief's sanity-check note about edge
cases where the bet was cancelled / voided / lapsed is preserved as
a finding for Session 102 (§8 below) — settlement-state
reconciliation lives in the post-settlement workflow per the brief
itself.

### §5.3 — `get_market_status` rewire — SUSPENDED routing

The pre-existing `RealBetfairAdapter.get_market_status` carried a
per-reason refinement that converted `BETFAIR_MARKET_SUSPENDED`
back to `MarketStatusSnapshot(status="SUSPENDED")` after the W3
`live_pricing` SUSPENDED-intercept (live_pricing.py:126) had
already converted it to `UnavailableReadEnvelope`. Per brief §5.6
this conversion is dropped; SUSPENDED now reaches the orchestrator
as `ReadUnavailable(reason="betfair_market_suspended")` and
`_market_status_check` reads the reason directly.

The behaviour the operator sees in the pre-flight is preserved —
the same `MARKET_SUSPENDED` warn-severity flag with the same
operator-facing message. The detail dict additionally records
`unavailable_reason: "betfair_market_suspended"` so downstream
layers (modal, logging) can switch on it without parsing the
flag's `code` string.

### §5.4 — Two distinct `BetfairReadUnavailableReason` import sites

After the edit, `betfair_adapter.py` imports
`BetfairReadUnavailableReason` from
`clients.betfair_client.v1.envelope` (a deeper path than the public
package re-export at `clients.betfair_client.v1.__init__`). The
existing public re-export was not removed; the deeper import is
used because the original adapter file already imported from
`clients.betfair_client.v1` at the top level and the structural
split (W3 boundary helper at `envelope.py` vs the surface re-export
graph at `__init__.py`) made a sub-module import the cleaner shape.
This preserves per-file import discipline and matches the existing
import precedent in the file (`current_orders` and `envelope` both
addressed via deeper paths).

### §5.5 — Mock setter API preserved

Per brief §5.8 ("Code's call on whether existing Trigger B test
fixtures need reshape vs whether wrapper helpers on
`MockBetfairAdapter` keep the test-shape stable. Either is fine"),
chose to keep test-shape stable. The 30 existing
`test_orchestrator.py` tests continue to call `set_market_status`,
`set_account_funds`, and `queue_order_state` with the same
arguments as before; the mock wraps in `ReadOk` /
`ReadUnavailable` on the way out. New setters
`set_market_status_unavailable(reason)` and
`set_account_funds_unavailable(reason)` added for future tests
that want to pin a specific reason value;
`queue_order_state` now also accepts `ReadOk` / `ReadUnavailable`
directly.

### §5.6 — `OrderRecord` defensive defaults

The contract spec states `size_lapsed`, `size_cancelled`,
`size_voided` as `Decimal` fields. The Pydantic shape uses
`Decimal("0")` as the default for all three so that payloads
omitting these (most live unmatched orders never lapse / cancel /
void) parse cleanly. The brief named "defensive parsing" as a
test-coverage area; this default-on-omit behaviour is exercised by
`test_list_current_orders_optional_fields_handle_omission`.

---

## §6 — Deviations from brief

The brief requested operator notice on judgement calls. Six items
recorded; none change scope.

### §6.1 — Contract version bumped to v1.4 (not v1.3)

**Brief direction:** `bump contract version to v1.3 per §14.4`
(brief §1 + §5.3 version note `**Added v1.3 (2026-05-07).**`).

**Observed state:** `betfair_client_contract.md` already at v1.3
from Session 96 W4 follow-up Code (REST-fetch fallback
clarification at §13.5; existing §6 row dated 2026-05-07).

**Action taken:** Bumped to **v1.4** and updated the §9.8 version
note + §6 row + Status line accordingly. The brief's directional
intent (`next backward-compatible addition gets a fresh version
bump for audit clarity, per the §6 history pattern`) was preserved;
the literal v1.3 string would have created two distinct §6 rows
both labelled v1.3, contradicting the contract's own append-only
discipline (§6 preamble: "v1.0's text never gets rewritten").

The brief's drafting context (Session 101 brief author) appears to
have anchored on v1.2 as the latest version; the Session 96 v1.3
addition isn't referenced in the brief or pre-flight grounding,
suggesting it post-dated the source material the brief was drafted
against.

### §6.2 — Sequencing: contract spec before final verification

Brief §6 recommended the contract-spec edit at step 12 (after all
code edits + tests). Followed exactly: contract spec was the second-
to-last edit, after tests passed.

### §6.3 — `selection_id` reserved-not-used in `get_order_state`

The W3 `list_current_orders` surface accepts `market_id` and
`bet_id` filters but not `selection_id`. The W4 Protocol method
`get_order_state` keeps `selection_id` in the signature for
forwards compat (per the existing pre-flight discipline at
`pre_flight_check`), with a `del selection_id` line acknowledging
the reservation explicitly. The brief's pseudocode at §5.6 also
elided the `selection_id` filter, so this is consistent with the
brief's own implementation hint.

### §6.4 — `BettingAPING` vs `SportsAPING` namespace

The brief docstring example at §5.1 says:

> Maps to Betfair's ``BettingAPING/v1.0/listCurrentOrders`` per
> §15.4 v1.3 carve-out.

The actual Betfair JSON-RPC namespace is unified — the existing
`_translation.py` uses `SportsAPING/v1.0/...` for `placeOrders`,
`cancelOrders`, `replaceOrders` etc., which in betfairlightweight
are `endpoints.betting.*`. The implementation uses
`SportsAPING/v1.0/listCurrentOrders` matching the existing
`placeOrders` precedent. The contract spec at §9.8 references
`Betfair's listCurrentOrders` without the namespace prefix to
side-step this and stay aligned with the actual API surface.
Module docstring in `current_orders.py` reads
`BettingAPING/v1.0/listCurrentOrders` per the brief's literal
text — left as-is rather than substituted, since the comment is
descriptive (the library-side counterpart is
`betfairlightweight.endpoints.betting.list_current_orders`, where
"betting" is the betfairlightweight package name) rather than the
JSON-RPC method literal which lives in `_translation.py`.

### §6.5 — `set_account_funds(None)` semantics preserved as
       `ReadUnavailable`

Pre-existing test API: `set_account_funds(None)` meant "the next
read returns the historical `None` sentinel" (which the orchestrator
treated as "read failed"). Post-rewire, the orchestrator switches
on `ReadOk` / `ReadUnavailable`. The mock now routes
`set_account_funds(None)` to `ReadUnavailable(reason=
"betfair_api_unreachable")` so the historical test sites
(specifically `test_pre_flight_funds_unavailable_warn` at
test_orchestrator.py:424) continue to exercise the same orchestrator
branch (warn-severity `FUNDS_CHECK_UNAVAILABLE`) without behaviour
change. New tests targeting a specific reason use
`set_account_funds_unavailable(reason)`.

### §6.6 — `betfair_market_suspended` not surfaced from §9.8

The brief §5.1 lists `betfair_market_suspended` among the common
failure modes for `list_current_orders`, but the W3 surface code
does not produce that reason — order-state reads aren't market-
status-gated (the bet exists in the operator's order list
independent of market state; suspension affects the per-market
read at §9.1, not the per-order read here). The contract spec
§9.8 accordingly drops `betfair_market_suspended` from the
failure-mode list and adds an explanatory paragraph naming the
reason. The seven-value `BetfairReadUnavailableReason` enum
remains the closed set the surface can return; the spec just
narrows the practically-applicable subset for §9.8 specifically,
matching the §9.6 / §9.7 precedent of listing only the common
cases per surface.

---

## §7 — Open questions for triage

### §7.1 — Line 187 narrative reference still says "seven read
            surfaces"

Contract §7 "How to read this section" line 187 reads:

> §9 specifies seven read surfaces (§9.1–§9.5 at v1.0; §9.6 + §9.7
> added v1.2)

After this brief's §9.8 addition there are eight read surfaces
(§9.1–§9.5 + §9.6 + §9.7 + §9.8). The brief's "named anchors only"
hard limit named §9.8 + §6 (the version history table); §7's
narrative reference was not named and was not edited. The same
thing happened at Session 96 (v1.3 added §13.5; line 187 stayed at
"seven read surfaces" — accurate since §13.5 isn't a new read
surface). Triage call for Session 102: update line 187 to
"eight read surfaces" via a follow-up housekeeping pass (a single
in-place line edit), or leave it.

### §7.2 — Resolved-out-of-orders settlement-state ambiguity

The brief §5.6 pseudocode treats "bet not in current orders" as
"fully matched" and notes the edge case where the bet was
cancelled / voided / lapsed would also fall out of current orders
without being fully matched. Per brief: real settlement-state
reconciliation lives in the post-settlement workflow (out of scope
here). Triage call for Session 102: confirm that W6 broader-sync
reconciliation (or the post-settlement workflow if separate) is
the right home for differentiating these cases, and that Trigger
B's "fully matched" assumption is an acceptable v1.4 approximation
for the live placement → reconciliation cycle.

### §7.3 — `BetfairReadUnavailableReason` import-sub-module question

`betfair_adapter.py` now imports
`BetfairReadUnavailableReason` from
`clients.betfair_client.v1.envelope` (the deeper path) rather than
from the public `clients.betfair_client.v1` re-export. Both work
identically and import-linter contracts pass. Triage call for
Session 102: prefer one shape consistently across the W4 adapter
imports? The existing `current_orders` import already uses the
deeper path (`from clients.betfair_client.v1.current_orders import
list_current_orders, OrderStateList`) for the new module's
non-`__init__`-resident types, so structural consistency arguably
favours the deeper path. No-call as far as code correctness; a
style consistency call only.

---

## §8 — Findings (beyond brief scope; not actioned)

### §8.1 — `OrderRecord.placed_date` always non-None

The brief §5.1 spec lists `placed_date: datetime` (non-Optional)
because Betfair's `CurrentOrderSummary` always carries a placement
timestamp. The implementation matches the spec. If a future
Betfair-side change ever omits it, the `_parse_order` helper will
raise on the missing key — which is the correct behaviour per the
contract's "fail loud at the boundary" discipline. Naming this so
Session 102 has the visibility if a future field-presence test
ever proves load-bearing.

### §8.2 — `size_requested` derivation chooses `priceSize.size`

In `_translate_list_current_orders`, `size_requested` is taken
from Betfair's `priceSize.size` field (the original placement
size). The W3 contract §9.8 spec fields `size_requested = Decimal`
without ambiguity; the alternative would be
`size_matched + size_remaining + size_lapsed + size_cancelled +
size_voided`, which should equal `priceSize.size` for any
correctly-tracked Betfair order. Choosing `priceSize.size` as the
authoritative source means a Betfair-side accounting drift would
surface as a sanity-check failure inside the adapter rather than
silently shipping. No drift detection is implemented at v1.4.

### §8.3 — Test count delta exceeds brief's guide range

+19 vs guide of +6 to +12. Surfaced in §3 above; named here for
report-structure completeness. Coverage matches the brief's §5.9
explicit areas one-test-per-area, so the upward variance is from
the area enumeration being broader than the brief's
implementation-level guess at the file size; the brief itself
notes this is "not a hard target."

### §8.4 — `betfair_streaming_disconnected` reason absent in §9.8 too

For symmetry with §6.6 (no `betfair_market_suspended` from the
order-state surface), `betfair_streaming_disconnected` also does
not surface from `list_current_orders` because order-state reads
are REST-only — they don't share the streaming connection. The
contract §9.8 failure-modes list omits it accordingly. The
`ReadUnavailable.reason` Literal in `orchestrator.py` keeps the
seven-value enum mirror — not narrowed per surface — because the
W4 boundary's discriminated-union is across all three reads, not
per-read.

---

## §9 — Self-assessment

### §9.1 — Pre/post baselines

| Check | Pre | Post | Δ |
|---|---|---|---|
| `pytest` count passing | 342 | 361 | +19 |
| `ruff check` | clean | clean | — |
| import-linter (5 contracts) | kept | kept | — |
| Working-tree state | matches Session 100 close | named anchors only modified or added | — |

### §9.2 — `git status` snapshot — session open

```
On branch main
Changes not staged for commit:
        modified:   clients/betfair_client/v1/__init__.py

Untracked files:
        clients/betfair_client/v1/account_funds.py
        clients/betfair_client/v1/market_catalogue.py
        tests/clients/betfair_client/v1/test_account_funds.py
        tests/clients/betfair_client/v1/test_market_catalogue.py
        tests/workflows/
        workflows/bet_entry/v1/
```

### §9.3 — `git status` snapshot — session close

```
On branch main
Changes not staged for commit:
        modified:   clients/betfair_client/v1/__init__.py
        modified:   clients/betfair_client/v1/_translation.py

Untracked files:
        clients/betfair_client/v1/account_funds.py
        clients/betfair_client/v1/current_orders.py
        clients/betfair_client/v1/market_catalogue.py
        tests/clients/betfair_client/v1/test_account_funds.py
        tests/clients/betfair_client/v1/test_current_orders.py
        tests/clients/betfair_client/v1/test_market_catalogue.py
        tests/workflows/
        workflows/bet_entry/v1/
```

Net additions to working-tree state from this session:

- `_translation.py` — moved from clean to modified (the new
  `_ORDERS_CURRENT_RE` routing entry).
- `current_orders.py` — new untracked.
- `test_current_orders.py` — new untracked.

The pre-existing untracked / modified files (`__init__.py` modified
plus the W4 workflow tree, account_funds, market_catalogue, and
their tests) reflect prior in-progress work from Sessions 94–100;
this session's edits to `__init__.py` (re-exports) and the
pre-existing W4 files (`orchestrator.py`, `betfair_adapter.py`,
their tests) land on top of that pre-existing state.

No file outside the brief's named anchors was modified or added.

### §9.4 — Functional verification

- All `get_market_status` call sites in the orchestrator
  (`_market_status_check`) handle both `ReadOk` and `ReadUnavailable`
  via `isinstance(outcome, ReadUnavailable)` checks. ✓
- All `get_account_funds` call sites in the orchestrator
  (`_fundedness_check`) handle both branches via the same pattern. ✓
- All `get_order_state` call sites in the orchestrator
  (`_read_order_state_with_retry` plus the Trigger B caller in
  `_run_trigger_b`) handle both `ReadOk` and `ReadUnavailable`. ✓
- SUSPENDED signal verification: the W3-side `live_pricing`
  SUSPENDED-intercept at `live_pricing.py:126` still produces
  `UnavailableReadEnvelope(BETFAIR_MARKET_SUSPENDED)`; the W4
  adapter passes this through as `ReadUnavailable(reason=
  "betfair_market_suspended")`; the orchestrator's
  `_market_status_check` still surfaces a `MARKET_SUSPENDED` warn
  flag with the same operator-facing message. The unavailable-reason
  string is additionally preserved on the flag's `detail` dict.
  Behaviour-preserving rewire confirmed via
  `test_get_market_status_suspended_passes_through` and the
  pre-existing
  `test_pre_flight_market_suspended_returns_warn` in
  `test_orchestrator.py` (continues to pass with the mock's
  `set_market_status("SUSPENDED")` call still working).
- Trigger B reconciliation tests cover the resolved-out-of-orders
  path
  (`test_get_order_state_resolved_out_of_orders` in
  `test_betfair_adapter.py`), the still-in-orders path
  (`test_trigger_b_provisional_pending` continues to pass via the
  mock), and the failure path
  (`test_trigger_b_read_fails_twice_stays_provisional` updated to
  exercise the new `ReadUnavailable` retry semantics — exception
  on attempt 1, exception on attempt 2 → record stays
  `PROVISIONAL` per brief §6.4).

### §9.5 — Mocked REST integration only

No live Betfair calls were made. All `RealBetfairAdapter` tests
exercise the new `get_order_state` real path through `MockTransport`
+ `BetfairRestClient` against the test fixture
`/v1/orders/current` payload shape.

### §9.6 — Length flag

This report sits at ~620 lines (within the brief's 600-900 line
anticipation, well under the 1000-line surface-flag threshold).

### §9.7 — Adelaide local timestamps per DR-021

- Session-open timestamp: 2026-05-07 16:35 ACST.
- Session-close timestamp: 2026-05-07 16:50 ACST.
- All test fixtures generating `cache_as_of` values use the existing
  conftest-pinned `FIXTURE_NOW_UTC = 2026-05-04 04:42:30 UTC`
  (= 14:12:30 ACST) per the precedent in
  `tests/clients/betfair_client/v1/conftest.py`. Adelaide-local
  conversion is exercised by
  `test_list_current_orders_cache_as_of_uses_adelaide_local`.
- Contract §9.8 example timestamps Adelaide-local per the §9.6
  precedent.
- Report timestamps in this file Adelaide-local throughout per
  brief §4.

End of report.
