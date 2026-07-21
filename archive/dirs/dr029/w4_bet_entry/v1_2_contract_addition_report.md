# `betfair_client` v1.2 contract addition — session report

**Session:** 94 Code (single bounded session)
**Date:** 2026-05-07 (Adelaide local)
**Brief:** `dr029/w4_bet_entry/v1_2_contract_addition_brief.md`
**Status:** complete

---

## §1 — Summary

Closed W4 report §8.1 (`get_account_funds`) and §8.2
(`get_market_catalogue`) by amending `betfair_client_contract.md` to
v1.2 per the §14.4 backward-compatible-additions mechanism, and
implementing the corresponding `clients/betfair_client/v1/` modules
with mocked-transport tests.

| Item | Result |
|---|---|
| Contract version after amendment | v1.2 (no surface-level version bump) |
| Surfaces added | §9.6 `get_account_funds`, §9.7 `get_market_catalogue` |
| Existing surfaces touched | None — purely additive |
| New source files | 2 (`account_funds.py`, `market_catalogue.py`) |
| New test files | 2 (`test_account_funds.py`, `test_market_catalogue.py`) |
| Modified source files | 1 (`__init__.py` exports only) |
| New tests | 20 (8 + 12) |
| Pytest | 232 passed (baseline 212 → +20; zero regression) |
| Ruff | clean |
| Import-linter | 5 of 5 contracts kept |
| Fresh-invocation import | OK |
| Deviations from brief | 1 (W3-pattern vs library-call internals — §7) |
| Findings | 4 (§9) |
| Open questions | 0 |

All seven expected files modified or created. No edits outside named
anchors of brief §4 / §5 / §6 / §7. No git operations. No real Betfair
API calls. Phase 1 lock landed cleanly; Phase 2 ran against a locked
contract.

---

## §2 — Contract amendment landed

Five edit anchors per brief §5; all five executed in Phase 1. Document
grew from 1199 to 1357 lines (+158). Below the brief's rough +200–280
estimate because the inserted §9.6 / §9.7 surfaces are tighter than
§9.1 / §9.2 (no streaming-cache routing prose, no settlement-state
enumeration).

### §2.1 — §9.6 `get_account_funds`

Anchor: brief §5.1. Position: lines 660–725 (66 lines). Inserted
between former line-657 close of §9.5 and former §10 header. Spec
coverage: anchor heading; v1.2-added marker; source-spec anchor (§2.9
§6.1 surface (d)); endpoint path; call signature; parameter spec
table; return-shape Pydantic model; failure-modes listing;
stale-not-applicable note; example call/response (fresh + unavailable).
Reads coherently against §9.5 (closest existing surface).

### §2.2 — §9.7 `get_market_catalogue`

Anchor: brief §5.2. Position: lines 727–813 (87 lines). Inserted
immediately after the new §9.6. Spec coverage: anchor heading;
v1.2-added marker; decision anchor (DR-032 §4); endpoint path; call
signature; parameter spec table; return-shape Pydantic models
(`RunnerCatalogue` + `MarketCatalogue`); single-market-scope note;
failure-modes listing; stale-not-applicable note; example
call/response. Nested shape mirrors `MarketPrices` × `RunnerPrices`
precedent.

### §2.3 — §15.4 narrowing

Anchor: brief §5.3. Position: lines 1347–1351. Existing paragraph
replaced with brief's exact replacement language: account-management
exclusion preserved; v1.2 carve-out for `get_account_funds` named;
remaining `AccountAPING` endpoints (`transferFunds`,
`getAccountStatement`, `getAccountDetails`, `listCurrencyRates`)
explicitly listed as still out of scope.

### §2.4 — §6 version history append

Anchor: brief §5.4. Position: new line 169 (one new row in the version
history table, immediately below the Session 87 W3 v1.1 row). Date
2026-05-07, Session 94 Code. Carries the brief's exact entry text.

### §2.5 — §5.5 cross-reference housekeeping

Anchor: brief §5.5.

| Site | Edit | Position |
|---|---|---|
| §14.4 list of "first wave of backward-compatible additions" | Append "Plus the v1.2 endpoints added in §9.6 and §9.7." | line 1319 |
| §3 "Account management" bullet | Heading edited to acknowledge §9.6 carve-out; trailing sentence added to spell out the v1.2 narrow carve-out. | line 70 |
| §7 ToC enumeration ("§9 specifies five read surfaces") | Updated to "§9 specifies seven read surfaces (§9.1–§9.5 at v1.0; §9.6 + §9.7 added v1.2)." | line 185 |

The brief's verbatim §3 replacement language ("No account-management
surfaces") didn't match the document state — the actual §3 has bullet
structure. Recorded as Finding 1.

### §2.6 — End-to-end coherence self-check

Phase 1 step 8 self-check ran after all five anchors landed:
§9.6/§9.7 read coherently against §9.1–§9.5; §15.4 carve-out
unambiguous; v1.2 history row dated and complete; cross-references
land at §14.4 / §3 / §7; no broken Markdown (code fences and tables
intact); pre-existing §9.1–§9.5 / §10 / §11 / §12 / §13 untouched.
Lock point reached at Phase 1 close.

---

## §3 — Implementation landed

Two new source files in `bethub-v3/clients/betfair_client/v1/`.
Both mirror the W3 v1.0 surface pattern (`BetfairRestClient` injection,
path-style endpoint abstraction, exception-mapped envelope per contract
§8) — see §7 for the brief-vs-pattern call.

### §3.1 — `account_funds.py` (92 lines)

Module docstring names contract anchor §9.6 + source-spec §2.9 §6.1
surface (d) + library-side `betfairlightweight.endpoints.account.get_account_funds`
counterpart. `AccountFunds(BaseModel)` matches contract §9.6 return
shape exactly: required `available_to_bet_balance`, `exposure`,
`cache_as_of`; optional `exposure_limit`, `retained_commission`,
`points_balance`, `discount_rate`, `wallet`. Public function
`get_account_funds(rest_client, wallet=None) -> ReadEnvelope[AccountFunds]`
— wallet validated non-empty when supplied (raises `ValueError`),
forwarded as `?wallet=X` query string. Adelaide-local timestamping
via `_clock.now_utc()` → `to_adelaide(...)` for both envelope `as_of`
and data `cache_as_of` (same instant). Failure mapping via
`_errors.map_rest_error_read` — covers auth-expired / rate-limited /
api-unreachable. No new error paths — existing `_errors` mapping
sufficient.

### §3.2 — `market_catalogue.py` (135 lines)

Module docstring names contract anchor §9.7 + DR-032 §4 +
library-side `betfairlightweight.endpoints.betting.list_market_catalogue`
with the brief's projection list. `RunnerCatalogue(BaseModel)` and
`MarketCatalogue(BaseModel)` match contract §9.7 return shapes
exactly. `_parse_runner` performs explicit `int → str` coercion on
`selection_id` per the brief's note. `_parse` flat-maps market-shape
fields, iterates runner sub-shapes, and converts `market_start_time`
to Adelaide local via `to_adelaide(datetime.fromisoformat(...))`.
Public `get_market_catalogue(market_id, rest_client) -> ReadEnvelope[MarketCatalogue]`.
Empty-payload branch — `payload is None or payload == {} or
payload.get("market_id") is None` → `BETFAIR_MARKET_NOT_FOUND` —
covers both library-side empty-list semantics and any REST-shape
empty-dict semantic the translation layer may produce. 404 from
transport maps directly to `BETFAIR_MARKET_NOT_FOUND` per the
`live_pricing.py` precedent. The contract's `RunnerCatalogue`
deliberately omits `metadata`; the parser ignores any `metadata` key
on the wire.

### §3.3 — `__init__.py` (modified)

Two new `from .account_funds import ...` and `from .market_catalogue
import ...` lines added to the existing import block (alphabetically
sorted). `__all__` extended with five new public names (`AccountFunds`,
`MarketCatalogue`, `RunnerCatalogue`, `get_account_funds`,
`get_market_catalogue`) within the existing read-surfaces block. No
edits to existing exports.

### §3.4 — Library re-verification

Per brief §6.4, library import-check ran in the v3 venv at session
start: `library version: 2.23.2`. All `AccountFunds` /
`MarketCatalogue` / `RunnerCatalogue` / `Event` / `EventType` resource
classes importable. Inspected source for each; field shapes match the
brief's `available_to_bet_balance` / `event.id` / `event.country_code`
(library-renamed from `countryCode`) / `event.time_zone`
(library-renamed from `timezone`) / `selection_id` (int) / etc. No
library-version drift between brief drafting and Code execution.

---

## §4 — Tests built

Two new test files mirroring the source-file naming. Mocked
`BetfairRestClient` transport per the W3 W2-test pattern; no real
library calls (see §7).

### §4.1 — `test_account_funds.py` (204 lines, 8 tests)

| # | Test | Brief |
|---|---|---|
| 1 | `test_get_account_funds_returns_fresh_envelope_with_full_funds_data` | §7.1 c.1 |
| 2 | `test_get_account_funds_with_explicit_wallet_passes_through` | §7.1 c.2 |
| 3 | `test_get_account_funds_with_default_wallet_omits_parameter` | §7.1 c.3 |
| 4 | `test_get_account_funds_optional_fields_handle_none` | §7.1 c.4 |
| 5 | `test_get_account_funds_auth_expired_returns_unavailable` | §7.1 c.5 |
| 6 | `test_get_account_funds_api_unreachable_returns_unavailable` | §7.1 c.6 |
| 7 | `test_get_account_funds_rate_limited_returns_unavailable_with_retry_after` | §7.1 c.7 |
| 8 | `test_get_account_funds_cache_as_of_uses_adelaide_local` | §7.1 c.8 |

All 8 brief-mandated cases covered; none added beyond the minimum.
Wallet pass-through and default tests use a `_capturing_responder`
helper that records the request URL — needed since the W3 pattern
generates the wallet via query-string.

### §4.2 — `test_market_catalogue.py` (344 lines, 12 tests)

| # | Test | Brief |
|---|---|---|
| 1 | `test_get_market_catalogue_returns_fresh_envelope_with_full_data` | §7.2 c.1 |
| 2 | `test_get_market_catalogue_passes_correct_market_id_in_path` | §7.2 c.2 (adapted) |
| 3 | `test_get_market_catalogue_empty_payload_returns_market_not_found` | §7.2 c.3 |
| 4 | `test_get_market_catalogue_selection_id_coerced_to_str` | §7.2 c.4 |
| 5 | `test_get_market_catalogue_optional_event_fields_handle_none` | §7.2 c.5 |
| 6 | `test_get_market_catalogue_runner_metadata_not_surfaced` | §7.2 c.6 |
| 7 | `test_get_market_catalogue_handicap_handles_racing_none_and_sports_value` | §7.2 c.7 |
| 8 | `test_get_market_catalogue_market_not_found_via_exception` | §7.2 c.8 |
| 9 | `test_get_market_catalogue_auth_expired_returns_unavailable` | §7.2 c.9 |
| 10 | `test_get_market_catalogue_api_unreachable_returns_unavailable` | §7.2 c.10 |
| 11 | `test_get_market_catalogue_market_start_time_is_adelaide_local` | §7.2 c.11 |
| 12 | `test_get_market_catalogue_cache_as_of_uses_adelaide_local` | §7.2 c.12 |

Case 2 was adapted from "passes correct filter and projection" to
"passes correct market_id in path" — the W3 path-style pattern carries
no `filter` / `market_projection` / `max_results` kwargs; library-shape
translation lives at `_translation.py` (off limits per brief §11). At
this surface layer the relevant assertion is that the market_id reaches
the transport correctly. See §7 for the underlying mismatch.

### §4.3 — Test count delta

Brief-stated baseline: 287. Actual baseline: 212 (Finding 4). New
tests: 20. Total post-amendment: 232. Brief-mandated +20 delta hit
exactly.

---

## §5 — Test results

Full pytest from `bethub-v3/`: `232 passed in 0.52s`. Per-suite:

| Suite | Pass / total |
|---|---|
| `test_account_funds.py` | 8 / 8 |
| `test_market_catalogue.py` | 12 / 12 |
| Other v1 betfair tests (155) | 155 / 155 |
| `vps_client/v1/...` | unchanged: all pass |
| `tests/test_skeleton.py` | unchanged: all pass |

Zero regression. No flaky cases — single-pass green.

---

## §6 — Linting + import-linter

**Ruff:** `ruff check .` — `All checks passed!`. Both new source files
and both new test files lint clean under the existing `pyproject.toml`
config (E/F/I/B/UP/N selected; UP042/UP046 ignored).

**Import-linter:** `lint-imports` — analysed 98 files / 271
dependencies; all 5 contracts kept (DR-030 layered architecture; domain
imports nothing; store imports nothing; contracts is leaf; workflows
cannot import workflows). New modules sit at the `clients` layer;
imports only from sibling private modules within `clients/betfair_client/v1/`
and from `pydantic` — no cross-layer imports introduced.

---

## §7 — Deviations from brief

One material deviation.

### §7.1 — W3 path-style implementation rather than library-call internals

**Anchor:** brief §6.1 + §6.2 + §7 (test mocking guidance).

**Tension.** Brief §6.1 prescribed "Internal: call
`client.account.get_account_funds(wallet=wallet)` via the library;
map the returned `betfairlightweight.resources.AccountFunds` resource
…". Brief §6.2 similarly prescribed `client.betting.list_market_catalogue(...)`
with explicit `filter` / `market_projection` / `max_results`
library-shape kwargs. Brief §7 referenced "Mocked `betfairlightweight`
calls."

But brief §1 framed the implementation as "mirroring the W3 v1.0
surface pattern"; brief §3 named `live_pricing.py` as the "reference
implementation pattern." The W3 surfaces inject `BetfairRestClient`
(path-style HTTP-shape transport wrapper, with v1-path → JSON-RPC
translation held at `_translation.py` per W2 finding F4) — not
`betfairlightweight.APIClient`. No existing v1 surface calls
`betfairlightweight` library methods directly. Brief §11 forbade edits
to `_connection.py` / `_translation.py` / other private modules.

**Decision.** Code mirrored the W3 v1.0 surface pattern faithfully:
both new functions take `rest_client: BetfairRestClient`; endpoints
are path-style (`/v1/account/funds`, `/v1/market/{id}/catalogue`)
matching the contract's existing endpoint convention; tests use
`MockTransport.register_static` / `register_error` per the existing
`test_live_pricing.py` / `test_identity.py` precedent.

**Why this preserves brief intent.** The contract spec (§5.1 + §5.2)
is unambiguous about the public surface shape — Pydantic return shape +
envelope wrapping + endpoint-path convention. None of those depend on
whether the surface module's internal call is REST or library. The
brief's library-shape field-mapping tables remain authoritative for
deployment-time wiring at `_translation.py` — adding the v1 → JSON-RPC
translation entries for the new surfaces is a follow-up (Finding 3),
out of scope here per §11.

**No other deviations.** All edits remained within named §4–§7
anchors. No edits to existing surface code, existing tests,
`vps_client/`, `_translation.py`, `_errors.py`, or any other private
module.

---

## §8 — Open questions

None. The brief was substantively specified; the single tension at
§7.1 was resolved by the brief's own "mirror W3 pattern" framing plus
the §11 hard-limit prohibition on editing private modules. Follow-up
items (translation-layer entries, consumer-side helpers) are next-
session decisions, not Code-session questions.

---

## §9 — Findings

Numbered, anchored, no-recommendations.

### Finding 1 — Brief-text mismatch at §3 cross-reference site

**Anchor:** brief §5.5 second bullet ("§3 third paragraph — currently
begins 'No account-management surfaces.'").

**Summary:** the brief quoted the §3 site as "currently begins 'No
account-management surfaces.'", but the actual §3 has bullet structure
(5 bullets); the relevant bullet was "Account management." (line 70).
No paragraph in §3 begins "No account-management surfaces."

**Implication:** Code preserved intent (acknowledge §9.6 carve-out
within §3) by editing the bullet's heading and trailing sentence. The
substantive change matches intent; the verbatim replacement language
was not applicable.

### Finding 2 — §2 surface count not updated

**Anchor:** brief §5.5 ("No other cross-reference edits.") + line 26 +
line 1297 (§14.2).

**Summary:** §2 opens "`betfair_client` v1.0 exposes nine surfaces —
five read surfaces, one streaming surface, three write surfaces."
After v1.2 the count is eleven / seven / one / three. §14.2 ("nine
v1.0 surfaces (§9 ×5...)") is similarly stale.

**Implication:** brief §5.5 explicitly bounded cross-reference
housekeeping. Code respected the bound and did not update §2 or §14.2.
Both sites carry stale surface counts; readers reaching §6 history or
§7 ToC see the v1.2 count.

### Finding 3 — Translation-layer entries pending for new surfaces

**Anchor:** `bethub-v3/clients/betfair_client/v1/_translation.py`
(read-only this session per brief §11).

**Summary:** the new path-style endpoints `/v1/account/funds` and
`/v1/market/{id}/catalogue` have no translation entries at
`_translation.py`. The two surfaces work end-to-end against
`MockTransport`; against a real httpx-backed transport via
`TranslatingTransport`, calls would fail at "unknown path" today.

**Implication:** real-API operability requires `_translation.py` to
add JSON-RPC mappings (`getAccountFunds` for funds; `listMarketCatalogue`
for catalogue with the brief §6.2 projections). Known follow-up — not
a session deviation, since §11 forbade editing `_translation.py`.

### Finding 4 — Brief-stated baseline test count vs actual

**Anchor:** brief §7 ("Existing W3 + W4 test count is 287") + §9 Gate
2 ("All existing 287 tests continue to pass").

**Summary:** actual baseline at session start was 212 collected by
pytest. The brief's 287 may have counted tests across the
bethub-rebuild scaffolding plus v3, or was an over-estimate from a
different point in time.

**Implication:** "zero regression" target is satisfied against the
actual baseline — 212 → 232 with the +20 new tests. The 287 figure is
informational; no regression introduced.

---

## §10 — Self-assessment

**Did the work fit budget?** Yes — single bounded session, three
phases completed in sequence. Phase 1 (contract amendment) ran
cleanly; Phase 1 self-check passed without revision. Phase 2
(implementation + tests + lint + import-linter + full pytest) ran in
one pass. Phase 3 (this report) lands within target after compression.

**Where less confident:**

- **Deviation §7.1** is a real fork in the brief's specification. The
  Phase-1 contract amendment is unaffected (the contract spec is
  implementation-agnostic at the contract level), but the Phase-2
  implementation choice is visible in the source-file shape and test
  pattern. Operator review of §7.1 is the right first stop.
- **Wallet validation discipline.** `account_funds.py` raises
  `ValueError` on empty-string wallet at function-entry. Existing
  surfaces (e.g. `identity.py`) don't validate parameters at function
  entry; they trust the path-style URL construction. ValueError is
  more defensive but adds a code path the contract doesn't explicitly
  require.
- **Empty-payload semantics for catalogue.** The empty-payload branch
  in `market_catalogue.py` checks three conditions
  (`payload is None or payload == {} or payload.get("market_id") is
  None`). Defensive — superset of the contract's "empty list" spec.
  Could be tightened.

**What should the operator look at first?**

1. The contract amendment (§9.6 + §9.7) — canonical artefact.
2. Deviation §7.1 — confirm W3-pattern interpretation or surface a
   follow-up.
3. Findings 2 + 3 — known follow-ups; operator decides whether they
   roll into the Session 96+ real-adapter brief or land separately.

**Length-range overrun:** none. Report at ~470 lines (within 300–500
target after compression pass).

**Acceptance work for the operator:**

- (Required) read the contract amendment for content fit.
- (Optional) read `account_funds.py` and `market_catalogue.py` for
  implementation review.
- (Optional) read the new test files to confirm test-shape adherence.
- (Optional) run a real `get_account_funds()` call against the live
  Betfair API at low risk — funds reads are read-only, no exposure;
  validates library mapping end-to-end. Requires `_translation.py`
  translation entry first (Finding 3).

---

**End of report.** Locked at Session 94 close. Operator-Claude triage
session reads next.
