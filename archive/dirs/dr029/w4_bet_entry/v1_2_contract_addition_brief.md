# `betfair_client` v1.2 contract addition brief

**Session:** 94 (drafted Session 94, locked at session close)
**Status:** drafting
**Closes:** §8.1 (`get_account_funds` contract gap) + §8.2 (`get_market_catalogue` contract gap) from `dr029/w4_bet_entry/w4_bet_entry_report.md`.
**Mechanism:** §14.4 backward-compatible additions of `betfair_client_contract.md` v1.0 — new endpoints alongside existing ones, no version bump for v3-side consumers, opt-in adoption.

---

## §1 — What this brief is and is not

This brief is a **mini-build commission with paired contract amendment**. The Code session it commissions runs end-to-end as a single bounded session and produces three things:

1. An in-place amendment to `betfair_client_contract.md` adding two read surfaces (`get_account_funds` and `get_market_catalogue`) per the §14.4 backward-compatible-additions mechanism.
2. The corresponding client-side implementation in `clients/betfair_client/v1/` — two new files, with envelope handling, error mapping, and Adelaide-local timestamping mirroring the W3 v1.0 surface pattern.
3. Tests covering the new methods, mocked against `betfairlightweight`'s API per the W4 mocked-library testing pattern. No real-API calls during the Code session.

A short report at session close names what shipped, deviations from this brief, findings (if any), and any open questions for operator-Claude triage.

**What this brief is not:**

- **Not a relocation of the contract document.** The contract amendment lands in place at `dr029/2_7_api_contract_versioning/betfair_client_contract.md`. Relocating contract `.md` files to v3's `contracts/` directory per DR-030 (the v3 repo layout decision) is a separate carry-forward and stays deferred.
- **Not a wholesale account-management surface.** Only `get_account_funds` lands. `transfer_funds`, `get_account_statement`, `get_account_details`, `list_currency_rates` all stay outside v1.2 — `betfairlightweight` exposes them but v3 day-one has no consumers. Contract §15.4 (account management out of scope) gets narrowed at §5.3 to name the carve-out, not removed wholesale.
- **Not a wholesale market-discovery surface.** Only `get_market_catalogue` lands, scoped to single-market-ID lookup for Set B field population (per DR-032 §4 — the canonical-reference-layer-for-all-bet-records decision). Generic catalogue browsing (multi-event, filter-driven discovery) stays out per contract §15.5.
- **Not a real-adapter implementation.** The W4 v1 `BetfairAdapter` Protocol mock-population continues; replacing the mock with a real adapter is sequenced for Session 96+ and is out of scope here.
- **Not a v1.1 re-spec or other contract surface revision.** Existing v1.0 / v1.1 surfaces (§9.1–§9.5, §10, §11, §12, §13) are unchanged. The amendment is purely additive.
- **Not a version bump.** Per §14.4, new endpoints alongside existing ones do not bump the contract version. v3-side consumers who don't use the new surfaces are unaffected.

**Surprises become findings, not blockers.** If the Code session uncovers a contract gap mid-implementation (e.g. the `betfairlightweight` library shape diverges from what the contract spec expects), Code stops the implementation phase and surfaces to operator-Claude rather than silently revising the contract. The contract spec produced in Phase 1 of the session (per §8 sequencing) is treated as canonical truth for the rest of the session — same discipline a freshly-locked contract carries between sessions.

---

## §2 — Why this work exists

Session 93 closed the W4 v1 triage (bet entry + write surfaces, the v3 build proper workstream that ships at `bethub-v3/workflows/bet_entry/v1/`). Code shipped clean against the W4 brief — 287 tests pass, ruff clean, all 5 import-linter contracts kept. Two of nine Findings surfaced as substantive contract gaps:

- **§8.1 — `getAccountFunds` not exposed.** W4 brief §4.3 specifies a fundedness pre-flight check at bet entry. Contract §15.4 explicitly excludes account management. Code's orchestrator preserves brief §4.3's "API failure handling" by surfacing `WARN funds_check_unavailable` rather than `BLOCK INSUFFICIENT_FUNDS`, but the check ships permanently as advisory until contract surfaces add `get_account_funds`. Operationally useful — insufficient-funds rejection at exchange is a real failure mode v2 has hit; not gating because the exchange rejects at placement time per contract §11.1 if truly unfunded.

- **§8.2 — `marketCatalogue` not exposed.** DR-032 §4 (the canonical-reference-layer decision) requires every bet record to carry six immutable per-leg snapshot fields populated from Betfair `marketCatalogue`: runner name, event name, event venue, sport, scheduled start time, plus the canonical Betfair identifiers themselves. Contract v1.0's `MarketPrices` / `RunnerPrices` shapes (§9.1) don't expose these. Code's W4 mock pre-populates the Set B fields; the real adapter genuinely cannot ship until contract surfaces them. Same surface is needed by W4.1 (soft-book typed-price entry) and W7 (burst-review modal pre-population) — not unique to W4.

Both gaps close in one v1.2 amendment per the §14.4 backward-compatible-additions mechanism: new endpoints alongside existing ones, no version bump, no consumer migration required. The amendment unblocks the real `BetfairAdapter` implementation (sequenced Session 96+) and three downstream workstreams (W4 acceptance, W4.1, W7).

The §8.1 piece is opportunistic; the §8.2 piece is the gating concern. Pairing them in one brief is the cheap unlock for everything downstream.

---

## §3 — Pre-reads

Required reads, in order:

1. **`dr029/2_7_api_contract_versioning/betfair_client_contract.md`** — the contract being amended. Critical sections:
   - §9.1 (operational live-pricing reads — `MarketPrices` / `RunnerPrices` shape; the new market-catalogue surface mirrors this read-side pattern).
   - §9.5 (identifier-resolution checks — closest existing surface to `get_market_catalogue` shape-wise; useful precedent).
   - §11.1 (bet placement — for `customer_strategy_ref` discipline carry-through, not for write-side mechanics).
   - §14.4 (backward-compatible additions mechanism — the version-discipline anchor).
   - §15.4 (account management out of scope — the exclusion being narrowed at §5.3).
   - §6 (version history — appended at §5.4).

2. **`dr029/w4_bet_entry/w4_bet_entry_report.md`** §8.1 + §8.2 only — the gap descriptions that motivate this brief.

3. **`bethub-v3/clients/betfair_client/v1/live_pricing.py`** — reference implementation pattern for the new module files. Module docstring with contract anchor; Pydantic v2 `BaseModel` return shape; `BetfairRestClient` for REST calls; `_errors.map_rest_error_read` for failure mapping; `ReadEnvelope[...]` envelope; `_clock.to_adelaide` for timestamping.

4. **`bethub-v3/clients/betfair_client/v1/identity.py`** — the closest existing surface shape-wise to `get_market_catalogue` (single-market lookup, returns a typed shape with multiple fields). Worth reading for the call-pattern precedent.

5. **`bethub-v3/tests/clients/betfair_client/v1/test_live_pricing.py`** — reference test pattern. Mocked `betfairlightweight` calls, parametrised cases, envelope-shape assertions, error-mapping coverage.

Reference-only — read on demand:

- **`bethub-v3/clients/betfair_client/v1/_errors.py`** — error-mapping module. New `betfairlightweight` exception types may need adding here if the new endpoints raise something `_errors` doesn't already handle (likely fine; same auth and connectivity exception surface as existing endpoints).
- **`bethub-v3/clients/betfair_client/v1/envelope.py`** — `ReadEnvelope`, `BetfairReadUnavailableReason` enum.
- **`bethub-v3/.importlinter`** — the 5 layered-architecture contracts. New methods inside `clients/betfair_client/v1/` are at the `clients` layer; the contracts allow `clients` to import from itself and from `contracts` (leaf). Verified at brief-drafting time.
- **`dr029/w4_bet_entry/w4_bet_entry_brief.md`** §3.5 — DR-032 Set B field reference. Read only if Set B field shape questions surface during contract drafting.
- **`decisions.md`** — DR-032 (canonical reference layer for all bet records — informs Set B requirements); DR-030 (v3 repo layout); DR-031 (v3 tech stack — Pydantic v2 / SQLAlchemy / FastAPI / pytest).
- **`betfairlightweight` library source** — installed in `bethub-v3/.venv/`. Specifically `betfairlightweight/endpoints/account.py` (`get_account_funds`) and `betfairlightweight/endpoints/betting.py` (`list_market_catalogue`); plus the resource shapes at `betfairlightweight/resources/accountresources.py` (`AccountFunds`) and `betfairlightweight/resources/bettingresources.py` (`MarketCatalogue`, `RunnerCatalogue`, `Event`, `EventType`). Brief-drafting session verified the surface; Code can re-verify if any Pydantic shape decision needs grounding.

---

## §4 — System access

**Read-write on:**

- `dr029/2_7_api_contract_versioning/betfair_client_contract.md` — in-place amendment per §5 below. Single file; named anchors only (new §9.6, new §9.7, narrowed §15.4, appended §6 history). No edits outside named anchors.
- `bethub-v3/clients/betfair_client/v1/account_funds.py` — new file (does not exist today).
- `bethub-v3/clients/betfair_client/v1/market_catalogue.py` — new file (does not exist today).
- `bethub-v3/clients/betfair_client/v1/__init__.py` — append-only export additions for the new modules. No edits to existing exports.
- `bethub-v3/tests/clients/betfair_client/v1/test_account_funds.py` — new file.
- `bethub-v3/tests/clients/betfair_client/v1/test_market_catalogue.py` — new file.

**Read-only on everything else.** Specifically off-limits without explicit operator approval mid-session: any other contract `.md` file (`vps_client_contract.md`, the §2.7 versioning brief itself); any other `clients/betfair_client/v1/` source file (existing surfaces unchanged); any `workflows/`, `domain/`, `store/`, `ui/`, `ops/`, `contracts/` directories.

**No real Betfair API access.** All testing mocks `betfairlightweight` — same pattern as existing W3 tests at `tests/clients/betfair_client/v1/test_live_pricing.py`. No live credentials, no SSH tunnels, no `capture.db` queries.

**No git operations.** No `git add`, `git commit`, `git stash`, `git restore`, `git checkout`, `git reset`. The v3 repo working tree is the operator's territory; Code edits files in place and surfaces what was changed in the report. Operator handles staging and commits between sessions.

**Adelaide local timestamps per DR-021 (the timestamp anchoring decision: Adelaide local time).** All timestamps in new code use `_clock.to_adelaide` (existing helper in `clients/betfair_client/v1/_clock.py`). All timestamps in the report use Adelaide local time.

**Python environment.** Use the venv at `bethub-v3/.venv/`. Python 3.12+. Existing tooling: `pytest`, `ruff`, `import-linter` (config at `bethub-v3/.importlinter`). All commands run from `bethub-v3/` as working directory.

---

## §5 — Contract amendment scope

Five sub-anchors. The amendment lands in place at `dr029/2_7_api_contract_versioning/betfair_client_contract.md`. Surgical-fix discipline: edits only at the named anchors below.

### §5.1 — New §9.6 read surface: `get_account_funds`

Insert immediately after §9.5 (identifier-resolution checks), before the §10 streaming surface header. Anchor heading: `### §9.6 Account funds read`.

**Anchor.** §2.9 §6.1 surface (d) — fundedness pre-flight at bet entry. Per W4 brief §4.3.

**Endpoint path.** `/v1/account/funds`.

**Call signature.**

```python
def get_account_funds(
    wallet: Optional[str] = None,
) -> ReadEnvelope[AccountFunds]: ...
```

**Parameter spec.** Single optional parameter table:

| Name | Type | Semantics | Validation | Default |
|---|---|---|---|---|
| `wallet` | `Optional[str]` | Betfair wallet identifier. AU operator default is `None` — Betfair routes to the operator's primary AUD wallet. | When supplied, non-empty. | `None` |

**Return shape.**

```python
class AccountFunds(BaseModel):
    available_to_bet_balance: float       # AUD available for placement; primary fundedness signal
    exposure: float                       # currently-staked unmatched + matched-not-yet-settled
    exposure_limit: Optional[float]       # operator-set exposure cap if any; None = no cap configured
    retained_commission: Optional[float]  # commission accrued not yet deducted; advisory
    points_balance: Optional[float]       # Betfair Rewards points; advisory, never used for placement
    discount_rate: Optional[float]        # operator commission-discount rate; advisory
    wallet: Optional[str]                 # echo of which wallet was queried
    cache_as_of: datetime                 # query timestamp; Adelaide local
```

**Failure modes.** `BetfairReadUnavailableReason` set applies. Common cases:

- `betfair_auth_expired` — session token lapsed. Surfaces; v3-side recovery routes through existing W3 auth refresh per `_auth.py`.
- `betfair_api_unreachable` — connectivity failure. Treated as transient; v3 caller can retry.
- `betfair_rate_limited` — endpoint shares Betfair's account-API rate budget. `retry_after` populated per the `_errors` mapping.

`stale` envelope is **not** applicable here — funds reads are non-cached, non-streamed, every call is direct REST. Returned envelope is always `fresh` on success or `unavailable` on failure.

**Example call and response.**

```python
result = betfair_client.get_account_funds()

# fresh:
FreshEnvelope(status="fresh", as_of=datetime(2026,5,7,8,5,30),
              data=AccountFunds(
                  available_to_bet_balance=1247.83,
                  exposure=320.50,
                  exposure_limit=None,
                  retained_commission=12.40,
                  points_balance=None,
                  discount_rate=0.0,
                  wallet=None,
                  cache_as_of=datetime(2026,5,7,8,5,30)))

# unavailable, auth expired:
UnavailableReadEnvelope(status="unavailable",
                        reason=BetfairReadUnavailableReason.BETFAIR_AUTH_EXPIRED,
                        retry_after=None)
```

### §5.2 — New §9.7 read surface: `get_market_catalogue`

Insert immediately after the new §9.6 (so §9.6 then §9.7), before §10. Anchor heading: `### §9.7 Market catalogue read`.

**Anchor.** DR-032 §4 (the canonical-reference-layer-for-all-bet-records decision) — Set B six immutable per-leg snapshot fields populated at bet logging time.

**Endpoint path.** `/v1/market/{market_id}/catalogue`.

**Call signature.**

```python
def get_market_catalogue(
    market_id: str,
) -> ReadEnvelope[MarketCatalogue]: ...
```

**Parameter spec.**

| Name | Type | Semantics | Validation | Default |
|---|---|---|---|---|
| `market_id` | `str` | Betfair `market_id`. | Non-empty; format `^\d+\.\d+$` per Betfair convention. | required |

**Return shape.**

```python
class RunnerCatalogue(BaseModel):
    selection_id: str
    runner_name: str
    sort_priority: Optional[int]      # display ordering hint from Betfair
    handicap: Optional[float]         # for line-based sports markets; None for racing WIN/PLACE

class MarketCatalogue(BaseModel):
    market_id: str
    market_name: str                  # e.g. "R1 1200m Mdn-SW", "Match Odds"
    event_id: str                     # Betfair event_id; canonical join key per DR-032
    event_name: str                   # e.g. "Flemington 7th May", "Hawthorn v Geelong"
    event_venue: Optional[str]        # populated for racing; sometimes None for sports
    event_country_code: Optional[str] # ISO; e.g. "AU"
    event_time_zone: Optional[str]    # IANA tz name; e.g. "Australia/Melbourne"
    event_type_id: str                # Betfair sport identifier; "7" thoroughbred, "4339" greyhound, etc.
    event_type_name: str              # e.g. "Horse Racing", "Australian Rules"
    market_start_time: datetime       # scheduled start, Adelaide local
    runners: list[RunnerCatalogue]
    cache_as_of: datetime             # query timestamp; Adelaide local
```

**Single-market scope at v1.2.** This surface returns the catalogue for one named `market_id`. Multi-market discovery (filter-driven catalogue browsing) stays out per contract §15.5; if v3 ever needs it, a separate surface lands at v1.3+.

**Failure modes.** `BetfairReadUnavailableReason` set applies:

- `betfair_market_not_found` — `market_id` aged out of current Betfair catalogue window or never existed.
- `betfair_auth_expired`, `betfair_api_unreachable`, `betfair_rate_limited` — connectivity-shaped failures.

`stale` not applicable — catalogue data is reference-shape (slow-changing per Betfair's own definition); every call is direct REST.

**Example call and response.**

```python
result = betfair_client.get_market_catalogue("1.234567890")

# fresh:
FreshEnvelope(status="fresh", as_of=datetime(2026,5,7,8,15,2),
              data=MarketCatalogue(
                  market_id="1.234567890",
                  market_name="R3 1200m Mdn-SW",
                  event_id="31876421",
                  event_name="Flemington 7th May",
                  event_venue="Flemington",
                  event_country_code="AU",
                  event_time_zone="Australia/Melbourne",
                  event_type_id="7",
                  event_type_name="Horse Racing",
                  market_start_time=datetime(2026,5,7,14,15,0),
                  runners=[
                    RunnerCatalogue(selection_id="47291834",
                                    runner_name="Express Magic",
                                    sort_priority=1,
                                    handicap=None),
                    # ...
                  ],
                  cache_as_of=datetime(2026,5,7,8,15,2)))

# unavailable:
UnavailableReadEnvelope(status="unavailable",
                        reason=BetfairReadUnavailableReason.BETFAIR_MARKET_NOT_FOUND,
                        retry_after=None)
```

### §5.3 — Narrow §15.4 (account management out of scope)

Edit §15.4 to name the carve-out. Existing language excludes the entire `AccountAPING` surface; the amendment narrows the exclusion to keep `get_account_funds` in scope while leaving the rest out.

**Edit anchor.** §15.4 paragraph beginning "Fund transfers, deposits, withdrawals, account settings, statement queries."

**New language (replaces existing paragraph):**

> Fund transfers, deposits, withdrawals, account settings, statement queries, account-detail metadata, currency-rate lookups. Betfair's `AccountAPING/v1.0/...` surface exposes these but v3 day-one doesn't use them; account hygiene work is operator-side via Betfair's web UI. Returns to scope only if a future workflow surfaces a concrete need.
>
> **Carve-out (v1.2):** `get_account_funds` is in scope per §9.6 — fundedness pre-flight at bet entry needs a real funds read. The carve-out is narrow: only the `getAccountFunds` endpoint surfaces; `transferFunds`, `getAccountStatement`, `getAccountDetails`, and `listCurrencyRates` remain out of scope.

### §5.4 — Append §6 version history entry

Edit anchor: §6 heading "Version history". Append a new entry below the existing v1.0 / v1.1 entries.

**New entry text:**

> **v1.2 (2026-05-07).** Two new read surfaces added per §14.4 backward-compatible-additions mechanism: §9.6 `get_account_funds` (closes W4 report §8.1; fundedness pre-flight at bet entry); §9.7 `get_market_catalogue` (closes W4 report §8.2; canonical Set B field population per DR-032 §4). §15.4 narrowed to carve out `get_account_funds` while keeping the rest of `AccountAPING` out of scope. No existing surfaces changed. No version bump for v3-side consumers; existing call sites are unaffected.

### §5.5 — Cross-reference housekeeping

Two cross-reference sites updated for completeness:

- **§14.4 list of "first wave of backward-compatible additions"** — currently lists §2.10 inventory items (`actualSP`, `removalDate`, etc.). Append: "Plus the v1.2 endpoints added in §9.6 and §9.7."
- **§3 ("What it does not do") third paragraph** — currently begins "No account-management surfaces." Edit to: "No account-management surfaces beyond §9.6 (`get_account_funds`)."

No other cross-reference edits. The ToC at §7 (Overview) regenerates implicitly when the new §9.6 and §9.7 land — leave the §7 list as-is; if the existing language enumerates surfaces by number, Code adds the two new entries to the list at §7's enumeration site only.

---

## §6 — Implementation scope

Two new files in `bethub-v3/clients/betfair_client/v1/`, plus exports added to `__init__.py`. Each file follows the existing one-file-per-surface pattern (precedent: `live_pricing.py`, `identity.py`, `settlement.py`, etc.).

### §6.1 — `account_funds.py`

New file at `bethub-v3/clients/betfair_client/v1/account_funds.py`.

**Module shape:**

- Module docstring naming the contract anchor (§9.6) and the `betfairlightweight` mapping (`account.get_account_funds`).
- Pydantic v2 `AccountFunds(BaseModel)` matching the contract §5.1 return shape exactly.
- Public function `get_account_funds(client, wallet=None) -> ReadEnvelope[AccountFunds]` where `client` is the v1 module's existing `BetfairRestClient` (or whatever the existing W3 surfaces inject — Code's call to mirror existing pattern).
- Internal: call `client.account.get_account_funds(wallet=wallet)` via the library; map the returned `betfairlightweight.resources.AccountFunds` resource to the contract's Pydantic shape; wrap in `FreshEnvelope`; map exceptions via `_errors.map_rest_error_read`.
- Adelaide local timestamping via `_clock.to_adelaide` for `cache_as_of` (set to `datetime.now()` at function-call time, then converted).

**Field mapping (library → contract):**

| Library attr | Contract field | Notes |
|---|---|---|
| `available_to_bet_balance` | `available_to_bet_balance` | direct |
| `exposure` | `exposure` | direct |
| `exposure_limit` | `exposure_limit` | direct; Optional |
| `retained_commission` | `retained_commission` | direct; Optional |
| `points_balance` | `points_balance` | direct; Optional |
| `discount_rate` | `discount_rate` | direct; Optional |
| `wallet` | `wallet` | direct echo |
| n/a | `cache_as_of` | populated client-side via `_clock` |

**Wallet default.** Per the operator note: `wallet=None` is the AU operator's default — Betfair routes to the primary wallet without explicit specification. Code's signature accepts `wallet` as `Optional[str]`; passing `None` to `betfairlightweight` omits the parameter from the API request.

### §6.2 — `market_catalogue.py`

New file at `bethub-v3/clients/betfair_client/v1/market_catalogue.py`.

**Module shape:**

- Module docstring naming the contract anchor (§9.7) and the `betfairlightweight` mapping (`betting.list_market_catalogue` with `marketProjection` to surface event / runner / event-type detail).
- Pydantic v2 `RunnerCatalogue(BaseModel)` and `MarketCatalogue(BaseModel)` matching contract §5.2 return shapes exactly.
- Public function `get_market_catalogue(client, market_id) -> ReadEnvelope[MarketCatalogue]`.
- Internal: call `client.betting.list_market_catalogue(...)` with the filter and projection naming below; receive `list[betfairlightweight.resources.MarketCatalogue]`; assert the list contains exactly one element (or zero — surface as `betfair_market_not_found`); map the resource to the contract's Pydantic shape; wrap in `FreshEnvelope`.

**`list_market_catalogue` call shape:**

```python
client.betting.list_market_catalogue(
    filter={"marketIds": [market_id]},
    market_projection=[
        "EVENT",            # populates Event(id, name, venue, countryCode, timezone, openDate)
        "EVENT_TYPE",       # populates EventType(id, name)
        "RUNNER_DESCRIPTION",  # populates RunnerCatalogue.runner_name + sort_priority + handicap + metadata
        "MARKET_START_TIME",   # populates market_start_time
    ],
    max_results=1,
)
```

**`max_results=1` default.** The library defaults `max_results` to 1; Code sets it explicitly anyway for readability and to make the single-market scope visible in the call site.

**Empty-list handling.** `list_market_catalogue` returns an empty list when the `market_id` doesn't resolve. Code returns `UnavailableReadEnvelope(reason=BetfairReadUnavailableReason.BETFAIR_MARKET_NOT_FOUND, retry_after=None)` in that case — no exception is raised by the library for the empty case, so error mapping doesn't pick it up; the empty-list branch is explicit.

**Field mapping (library → contract):**

| Library path | Contract field | Notes |
|---|---|---|
| `mc.market_id` | `market_id` | direct |
| `mc.market_name` | `market_name` | direct |
| `mc.event.id` | `event_id` | nested; per DR-032 canonical join key |
| `mc.event.name` | `event_name` | nested |
| `mc.event.venue` | `event_venue` | nested; Optional (often `None` for sports) |
| `mc.event.country_code` | `event_country_code` | nested; Optional |
| `mc.event.time_zone` | `event_time_zone` | nested; Optional; passthrough of library's `time_zone` rename of Betfair's native `timezone` |
| `mc.event_type.id` | `event_type_id` | nested |
| `mc.event_type.name` | `event_type_name` | nested |
| `mc.market_start_time` | `market_start_time` | direct; library returns `datetime`; convert to Adelaide via `_clock.to_adelaide` |
| `mc.runners[i].selection_id` | `runners[i].selection_id` | per-runner; convert int→str if library returns int |
| `mc.runners[i].runner_name` | `runners[i].runner_name` | per-runner |
| `mc.runners[i].sort_priority` | `runners[i].sort_priority` | per-runner; Optional |
| `mc.runners[i].handicap` | `runners[i].handicap` | per-runner; Optional |
| n/a | `cache_as_of` | populated client-side via `_clock` |

**`selection_id` type coercion.** `betfairlightweight.RunnerCatalogue.selection_id` is `int` (Betfair returns it as integer); the contract specifies `str` for consistency with all other identifier fields across `betfair_client` v1.0. Code converts via `str(...)` at mapping time. The contract spec at §5.2 keeps `selection_id: str`.

**Metadata not surfaced.** `RunnerCatalogue.metadata` (jockey name, weight, age, etc. for racing) is omitted from the Pydantic shape at v1.2 — DR-032 Set B doesn't require it, and surfacing it pulls in a chunk of typing work for variable-shape sport-specific dicts. Stays out; future v1.3 addition if a workflow surfaces a need.

### §6.3 — `__init__.py` exports

Append to `bethub-v3/clients/betfair_client/v1/__init__.py`:

```python
from .account_funds import AccountFunds, get_account_funds
from .market_catalogue import MarketCatalogue, RunnerCatalogue, get_market_catalogue
```

Insert after the existing import block; preserve existing export ordering. No edits to existing exports.

### §6.4 — Re-verification of `betfairlightweight` surface

Code verifies the library surface at session start by running a one-shot import check in the v3 venv:

```python
import betfairlightweight
from betfairlightweight import APIClient
from betfairlightweight.resources.accountresources import AccountFunds as LibAccountFunds
from betfairlightweight.resources.bettingresources import (
    MarketCatalogue as LibMarketCatalogue,
    RunnerCatalogue as LibRunnerCatalogue,
)
print("library version:", betfairlightweight.__version__)
```

If any import fails, that's a finding (library version drift between brief-drafting and Code execution); Code stops the implementation phase and surfaces.

---

## §7 — Test scope

Two new test files in `bethub-v3/tests/clients/betfair_client/v1/`, mirroring the source-file naming. Mocked `betfairlightweight` per the W4 + existing W3 pattern; no real-API calls.

### §7.1 — `test_account_funds.py`

New file at `bethub-v3/tests/clients/betfair_client/v1/test_account_funds.py`.

**Reference precedent.** `tests/clients/betfair_client/v1/test_live_pricing.py` for fixture setup, mocking pattern, envelope assertion shape.

**Minimum case list:**

1. **`test_get_account_funds_returns_fresh_envelope_with_full_funds_data`** — mock returns full `LibAccountFunds` resource; assert `FreshEnvelope` + every contract field maps correctly.
2. **`test_get_account_funds_with_explicit_wallet_passes_through`** — call with `wallet="UK"`; assert library was called with `wallet="UK"`.
3. **`test_get_account_funds_with_default_wallet_omits_parameter`** — call with no wallet; assert library was called with `wallet=None`.
4. **`test_get_account_funds_optional_fields_handle_none`** — mock returns resource with `points_balance=None`, `exposure_limit=None`, `discount_rate=None`; assert envelope's `data` carries `None` for those fields.
5. **`test_get_account_funds_auth_expired_returns_unavailable`** — mock raises `betfairlightweight.exceptions.SessionTokenError` (or whichever exception the existing `_errors.map_rest_error_read` maps to `BETFAIR_AUTH_EXPIRED`); assert `UnavailableReadEnvelope` with the right reason.
6. **`test_get_account_funds_api_unreachable_returns_unavailable`** — mock raises a connectivity-shaped exception (mirror existing test's pattern); assert correct reason mapping.
7. **`test_get_account_funds_rate_limited_returns_unavailable_with_retry_after`** — mock raises rate-limit exception; assert `retry_after` populated.
8. **`test_get_account_funds_cache_as_of_uses_adelaide_local`** — assert `cache_as_of` is timezone-aware Adelaide local (mirror existing tz-handling assertions in `test_live_pricing.py`).

### §7.2 — `test_market_catalogue.py`

New file at `bethub-v3/tests/clients/betfair_client/v1/test_market_catalogue.py`.

**Reference precedent.** Same as §7.1 plus `test_identity.py` for the single-market lookup pattern.

**Minimum case list:**

1. **`test_get_market_catalogue_returns_fresh_envelope_with_full_data`** — mock returns single-element list with full `LibMarketCatalogue` (event, event_type, runners populated); assert every contract field maps correctly.
2. **`test_get_market_catalogue_passes_correct_filter_and_projection`** — assert library called with `filter={"marketIds": [market_id]}` and `market_projection=["EVENT", "EVENT_TYPE", "RUNNER_DESCRIPTION", "MARKET_START_TIME"]` and `max_results=1`.
3. **`test_get_market_catalogue_empty_list_returns_market_not_found`** — mock returns `[]`; assert `UnavailableReadEnvelope` with `BETFAIR_MARKET_NOT_FOUND`.
4. **`test_get_market_catalogue_selection_id_coerced_to_str`** — mock returns runner with `selection_id=47291834` (int); assert contract shape carries `selection_id="47291834"`.
5. **`test_get_market_catalogue_optional_event_fields_handle_none`** — mock returns event with `venue=None`, `country_code=None`, `time_zone=None`; assert contract shape carries `None` for those fields.
6. **`test_get_market_catalogue_runner_metadata_not_surfaced`** — mock returns runner with `metadata={"WEIGHT_VALUE": "57.0", "JOCKEY_NAME": "..."}`; assert contract `RunnerCatalogue` does not expose metadata.
7. **`test_get_market_catalogue_handicap_handles_none_for_racing`** — racing-shape mock has runner `handicap=None`; sports-shape mock has `handicap=-5.5`; both mapped correctly.
8. **`test_get_market_catalogue_market_not_found_via_exception`** — covers the case where library raises rather than returns empty list (defensive; the library mostly returns empty, but if it raises a 404-like exception, error mapping handles it).
9. **`test_get_market_catalogue_auth_expired_returns_unavailable`** — auth failure mapping.
10. **`test_get_market_catalogue_api_unreachable_returns_unavailable`** — connectivity failure mapping.
11. **`test_get_market_catalogue_market_start_time_is_adelaide_local`** — assert `market_start_time` returned as Adelaide local; mirror existing tz tests.
12. **`test_get_market_catalogue_cache_as_of_uses_adelaide_local`** — same shape as §7.1 case 8.

**Test count target.** 8 + 12 = 20 new test cases. Existing W3 + W4 test count is 287; new total target is ~307. Code reports actual count in §3 of the report.

---

## §8 — Sequencing within session

Work runs in two phases. Phase boundary is the lock point: contract drafted and verified clean, then implementation against the contract.

**Phase 1 — Contract amendment.**

1. Read all required pre-reads per §3.
2. Verify `betfairlightweight` library surface per §6.4 (one-shot import check).
3. Edit `betfair_client_contract.md` per §5.1 — insert §9.6 with full surface spec.
4. Edit per §5.2 — insert §9.7 with full surface spec.
5. Edit per §5.3 — narrow §15.4 with the carve-out language.
6. Edit per §5.4 — append v1.2 entry to §6 version history.
7. Edit per §5.5 — cross-reference housekeeping at §14.4 list and §3 paragraph (and §7 ToC if it enumerates surfaces).
8. Re-read amended contract end-to-end. Self-check: §9.6 and §9.7 read coherently against §9.1–§9.5; §15.4 carve-out language is unambiguous; version-history entry is dated and complete; cross-references land cleanly.

**Phase 1 lock point.** At this point the contract is canonical truth for the rest of the session. If implementation in Phase 2 surfaces a contract gap (a return-shape discrepancy, an unhandled failure mode, a missing parameter), Code stops the implementation phase and surfaces to operator-Claude rather than silently revising the contract. See §11 hard limit.

**Phase 2 — Implementation.**

9. Create `bethub-v3/clients/betfair_client/v1/account_funds.py` per §6.1.
10. Create `bethub-v3/clients/betfair_client/v1/market_catalogue.py` per §6.2.
11. Append exports to `bethub-v3/clients/betfair_client/v1/__init__.py` per §6.3.
12. Create `bethub-v3/tests/clients/betfair_client/v1/test_account_funds.py` per §7.1.
13. Create `bethub-v3/tests/clients/betfair_client/v1/test_market_catalogue.py` per §7.2.
14. Run `ruff check .` from `bethub-v3/`; fix any issues in new files only (do not touch existing files for ruff issues).
15. Run `import-linter --config .importlinter` from `bethub-v3/`; expect all 5 contracts kept.
16. Run `pytest tests/clients/betfair_client/v1/test_account_funds.py tests/clients/betfair_client/v1/test_market_catalogue.py -v`; expect all new tests pass.
17. Run full `pytest` suite from `bethub-v3/`; expect existing 287 tests still pass plus the new ~20 cases pass.

**Phase 3 — Report.**

18. Write the report at the path named in §10.

**Sequencing rationale.** Contract before implementation because the contract is the spec the implementation satisfies. Tests before lint/import-linter because tests are more diagnostic; lint/import-linter are mechanical sweeps. Full-suite pytest last to confirm no regression in existing surfaces.

**Deviation rule.** Code may deviate from the within-step ordering above when a different ordering produces equivalent results more cleanly (e.g. writing the test file alongside its source file, then running tests for that one surface before moving to the next). Phase boundaries (Phase 1 lock, Phase 2 lock, Phase 3 start) are not deviation points — Phase 1 finishes before Phase 2 starts.

---

## §9 — Empirical verification

Two verification gates plus one final state check.

**Gate 1 — Contract amendment lands cleanly.** After Phase 1 step 8 (re-read end-to-end), Code confirms:

- All five edit anchors (§5.1, §5.2, §5.3, §5.4, §5.5) executed without errors.
- Document line count grew by approximately 200–280 lines (rough range; current contract is 1199 lines, post-amendment expected ~1400–1480 lines).
- Existing §9.1–§9.5 unchanged (spot-check by line-grepping for unchanged anchor headings).
- Existing §11–§13 unchanged.
- Markdown rendering not visibly broken (no unclosed code fences, no malformed table rows).

If any of those check fails, Code surfaces as a finding before starting Phase 2.

**Gate 2 — Implementation lands cleanly.** After Phase 2 step 17 (full pytest suite):

- All new tests (~20 cases) pass.
- All existing 287 tests continue to pass — zero regression.
- `ruff check .` clean across the project.
- `import-linter --config .importlinter` reports all 5 contracts kept.
- Both new source files import without error in a fresh Python invocation: `python -c "from clients.betfair_client.v1 import get_account_funds, get_market_catalogue, AccountFunds, MarketCatalogue"`.

If any check fails, Code surfaces as a finding in the report — does not push through to Phase 3 with a known failure.

**Final state check.** No edits outside the named anchors of §4 and §5–§7. Specifically:

- `vps_client_contract.md`: untouched.
- `2_7_api_contract_versioning.md`: untouched (the brief that frames the contract — separate from the contract itself).
- Any other `clients/`, `workflows/`, `domain/`, `store/`, `ui/`, `ops/`, `contracts/` source file: untouched unless explicitly named in §4.
- Existing tests: untouched.

`git status` (run by Code at session close, no commit) should show only the seven expected files modified or created:

```
modified:   dr029/2_7_api_contract_versioning/betfair_client_contract.md
new file:   bethub-v3/clients/betfair_client/v1/account_funds.py
new file:   bethub-v3/clients/betfair_client/v1/market_catalogue.py
modified:   bethub-v3/clients/betfair_client/v1/__init__.py
new file:   bethub-v3/tests/clients/betfair_client/v1/test_account_funds.py
new file:   bethub-v3/tests/clients/betfair_client/v1/test_market_catalogue.py
new file:   dr029/w4_bet_entry/v1_2_contract_addition_report.md
```

Any additional changed files in `git status` is a finding.

---

## §10 — Output spec

**Single output file.** `dr029/w4_bet_entry/v1_2_contract_addition_report.md`.

**Length range.** 300–500 lines. Substantially smaller than W4's 837-line report — this is a smaller-scope mini-build with paired contract amendment, not a full workstream. Report flags overrun if it lands above 500 lines per the W4 brief §11.4 self-flagging discipline.

**Section structure (numbered).**

1. **Header / summary of what shipped** — contract version (v1.2), what new surfaces, file inventory, test count delta, lint/import-linter state.
2. **Contract amendment landed** — per §5 edit anchors. One subsection per edit (§9.6, §9.7, §15.4 narrowing, §6 history, §5.5 cross-references). Each subsection: anchor, edit shape, post-edit line range. Spot-check: contract reads coherently end-to-end.
3. **Implementation landed** — per §6. One subsection per file. Each: line count, key implementation choices, library-mapping decisions made, anything that diverged from the brief's mapping table (with reasoning).
4. **Tests built** — per §7. Test count per file, total new test count, mapping of test cases to brief case list (note any cases added beyond the brief's minimum set, with reasoning).
5. **Test results** — pytest output summary; new test count, full-suite count, pass/fail, any flaky cases.
6. **Linting + import-linter results** — `ruff check` summary; `import-linter` per-contract status.
7. **Deviations from brief** — anything Code did differently from the brief's spec, with reasoning. Brief expects this section to often be empty or near-empty; non-empty deviations are scoped to library-API discoveries or pattern adherence.
8. **Open questions** — items needing operator-Claude triage. Expected to be small (the brief is substantially specified); list zero or more.
9. **Findings** — observations from the implementation that warrant operator-Claude awareness. Same shape as W4 report §8: numbered, each with anchor, summary, implication, no recommendation. Likely small.
10. **Self-assessment** — did the work fit budget, where less confident, what should operator look at first, length-range overrun if any, acceptance work the operator runs next.

**What the report does not contain:**

- No proposals for the next brief. Forward routing is the next operator-Claude session's call.
- No recommendations on contract design beyond noting findings. The contract is canonical post-Phase-1.
- No performance benchmarking against the live Betfair API. Mocked-only.
- No relocation of the contract document. That carry-forward stays parked.
- No multi-market or filter-driven `list_market_catalogue` extension. Single-market scope only at v1.2.
- No `transferFunds`, `getAccountStatement`, `getAccountDetails`, or `listCurrencyRates` surfaces. Per §15.4 narrowing, only `get_account_funds` lands.

**Adelaide local timestamps throughout the report per DR-021.**

---

## §11 — Hard limits

Non-negotiable. Code is forbidden from doing any of the following without explicit operator approval surfaced via the next operator-Claude session.

**Contract content beyond §5 anchors.**

- No edits to existing surfaces (§9.1–§9.5, §10, §11, §12, §13, §14).
- No edits to `vps_client_contract.md`.
- No edits to `2_7_api_contract_versioning.md` (the §2.7 framing brief, separate from the contract itself).
- No new contract surfaces beyond §9.6 and §9.7. Examples explicitly excluded: `list_currency_rates` (per §15.4 narrowing), `get_account_statement`, `get_account_details`, `transfer_funds`, multi-market `list_market_catalogue`, `list_event_types`, `list_market_book` (already covered by §9.1).

**Implementation scope beyond §6 anchors.**

- No edits to existing `clients/betfair_client/v1/` source files except the named append to `__init__.py`.
- No new helper modules in `clients/betfair_client/v1/` beyond the two files named in §6.1 and §6.2.
- No edits to `_errors.py`, `_auth.py`, `_clock.py`, `_connection.py`, `envelope.py`, or any other private module. New error mappings, if needed, surface as findings — Code does not silently extend the existing error-mapping table.
- No edits to `vps_client/` source. Contract amendment touches only `betfair_client_contract.md`; implementation touches only `betfair_client` source.
- No edits anywhere in `workflows/`, `domain/`, `store/`, `ui/`, `ops/`, or `contracts/` directories.

**Contract-as-canonical-mid-session.** This is the discipline rule named in §1 and referenced in §8. After Phase 1 lock:

- If implementation in Phase 2 surfaces a contract gap (return-shape discrepancy, unhandled failure mode, missing parameter, library API divergence), Code stops the implementation phase and surfaces to operator-Claude as a finding. The contract is not silently revised mid-session.
- The exception: if Phase 1's self-check at step 8 catches a contract issue before lock (the contract didn't read coherently, an edit anchor missed), Code may revise within Phase 1. The lock is the boundary.
- Cosmetic Phase 1 issues found in Phase 2 (a typo, a Markdown rendering glitch) may be fixed in place — these are not contract-content changes. Anything that affects the surface spec, the field shapes, the failure modes, or the parameter table is content and stops at Phase 2.

**Test scope beyond §7 anchors.**

- No edits to existing test files.
- No new test fixtures in `conftest.py` (existing fixtures are sufficient; if not, surface as a finding).
- No real-API tests. All `betfairlightweight` calls in the new test files use mocks — same pattern as `test_live_pricing.py`.

**Git operations.** No `git add`, `git commit`, `git stash`, `git restore`, `git checkout`, `git reset`. Operator manages staging and commits between sessions. Code may run `git status` at session close as a state-confirmation read — read-only.

**Pieces of named debt.** No attempts to address the three pieces of named debt from DR-029 (no test coverage, no migration framework, monolithic orchestrator). Existing tests are extended for the new surfaces only; nothing else.

**Single bounded session.** This is one Code session. If the work doesn't fit the budget, that's a finding — Code surfaces "needs to continue in a follow-up session" rather than half-completing across multiple sessions or compressing the test-case list silently.

**No cross-session continuation.** If Code stops mid-Phase-2 due to budget exhaustion or a Phase-1-locked contract gap surfacing, the report names the stop point, what landed, what didn't, and what the next session needs to pick up. Code does not anticipate or specify the follow-up brief — that's operator-Claude's call.

---

## §12 — What happens after Code's session

The Code session produces the artefacts named in §9 (modified contract, four new source/test files, modified `__init__.py`) plus the report at §10. Operator handles staging and commits between sessions.

The next operator-Claude session reads the report and triages — same shape as Session 93's W4 report triage. Read order:

1. Contract amendment summary (report §2) — confirm v1.2 surfaces landed with the spec'd shape.
2. Test results + lint/import-linter state (report §5 + §6) — confirm no regression.
3. Deviations (report §7) — operator-Claude decides whether each deviation needs to be reverted, locked, or surfaces a follow-up.
4. Open questions (report §8) — walk one decision per round per Cat 1.
5. Findings (report §9) — batch no-action items per operator preference; surface substantive ones.
6. Self-assessment (report §10) — operator-side acceptance shape.

**Forward-routing decisions the next session likely makes:**

- Whether to commission the real `BetfairAdapter` implementation brief (sequenced Session 96+ per Session 93 close) — now substantively unblocked by v1.2.
- Whether the W4 brief amendment sweep (cosmetic Session-93-batched items) lands now or stays parked.
- Whether the W4 follow-up Code brief (§7.4 + §7.6 narrow changes from W4 report) pairs with anything else or runs solo.
- Whether the v3 composition-root structural decision (fresh DR or DR-030 addendum, sequenced Session 95) moves up given v1.2 lands cleanly.

These routing decisions are out of scope for the Code session and out of scope for this brief. The brief commissions the v1.2 amendment + implementation; the next session decides what to do with it.

**Operator-side actions between sessions:**

- (Required) review the contract amendment for content fit. The amendment is the canonical spec going forward; the operator's between-session read is the right time to catch anything that didn't land cleanly.
- (Optional) review the implementation files if curious about the shipped code.
- (Optional) run a real `get_account_funds()` call against the live Betfair API at low risk — funds reads are read-only, no exposure. Validates the library-mapping is correct end-to-end. Operator's call whether to bother; not gating.
- (Optional) review the report end-to-end before the triage session.

---

## §13 — Cross-references

**Scope-doc anchor.** `dr029/dr029_scope.md` §2.7 (API contract versioning, the active arc this brief sits within). DR-029 is closed (Session 78); v1.2 amendment work is post-DR-029-close adjustment via the §14.4 mechanism that DR-029 explicitly preserved as a forward path.

**Decision Records invoked:**

- **DR-021** (timestamp anchoring, Adelaide local time) — applies to all new code's timestamping; applies to the report's timestamps; applies to the contract's `cache_as_of` and `market_start_time` field semantics.
- **DR-027** (the two-database architecture decision: BetHub owns operational state, capture.db owns analytical/source data) — frames why `betfair_client` is operational-line-only; new surfaces stay on the operational line.
- **DR-028** (the cross-database integration boundary discipline: no caching, no denormalisation, no second integration point) — applies to v3-side consumers of the new surfaces; not directly load-bearing for this brief but cited because the new surfaces will feed v3-side bet record creation per DR-032.
- **DR-030** (v3 repo layout and module-boundary discipline) — frames the file locations (`clients/betfair_client/v1/...`); the import-linter contracts in `.importlinter` enforce this.
- **DR-031** (v3 tech stack) — Pydantic v2 for return shapes; Python 3.12+; pytest; ruff; import-linter. All used per existing W3 + W4 patterns.
- **DR-032** (canonical reference layer for all bet records) — load-bearing for §5.2 / §6.2 / §7.2. Set B six-field requirement is the reason `get_market_catalogue` lands.

**Prior reports / sessions this brief builds on:**

- **Session 93 — W4 v1 triage** (forward-routing source). Located both contract gaps; locked v1.2 brief drafting as Session 94's primary deliverable.
- **`dr029/w4_bet_entry/w4_bet_entry_report.md` §8.1 + §8.2** (gap descriptions).
- **`dr029/w4_bet_entry/w4_bet_entry_brief.md` §3.5 + §4.3** (the W4 spec that surfaces the need for the two new contract surfaces).
- **Session 78 — DR-029 close** (post-close governance shape; v1.2 mechanism is the §14.4 path explicitly preserved at close).

**Parking-lot items this brief excludes:**

- **Contract document relocation** — `betfair_client_contract.md` and `vps_client_contract.md` move from `dr029/2_7_api_contract_versioning/` to `bethub-v3/contracts/` per DR-030. Carry-forward, deferred. The empty `bethub-v3/contracts/` directory exists today but holds no files yet.
- **Real `BetfairAdapter` implementation brief** — sequenced Session 96+ per Session 93 close. Substantively unblocked by v1.2 but is its own brief.
- **v3 composition-root structural decision** (fresh DR or DR-030 addendum) — sequenced Session 95 per Session 93 close. Names where composition-root code lives, owns adapter implementations.
- **W4 brief amendment sweep** — cosmetic / clarifying amendments accumulated through W4 Sessions 87–93. Bundle for next-time-we-touch-the-brief.
- **W4 follow-up Code brief** (§7.4 `streaming_blocked` reclassification + §7.6 `soft_book_combined_price` NULL-for-single-leg) — narrow scope; sequenced Session 94 if budget allows alongside this brief, else Session 95+.
- **W6 broader sync reconciliation** (`listClearedOrders` or similar) — W4 report §8.6 carry. Routes to W6 brief drafting.
- **Math review §6 arithmetic-step explicit update** — cosmetic; defer to next math review touch.
- **Multi-market or filter-driven `list_market_catalogue`** — explicitly out of scope at v1.2 per §1 + §15.5 of contract. Surfaces only when a v3 workflow needs it.
- **`AccountAPING` surfaces beyond `get_account_funds`** — `transferFunds`, `getAccountStatement`, `getAccountDetails`, `listCurrencyRates`. Per §15.4 narrowing in §5.3, all stay out.

---

**End of brief.** Locked at Session 94 close. Code reads start-to-end before commencing Phase 1.
