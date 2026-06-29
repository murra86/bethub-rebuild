# W12.2 — Commission source + construction plumbing (Code report)

**Session:** 143 Code (W12.2 build) — 2026-06-10 ACST per DR-021.
**Brief:** `dr029/w12_balances/w12_2_commission_construction_brief.md`
(SHA-256 `2928122d…`, 487 lines, gate-verified).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/` @ dirty W10–W15
build region (expected per §9). Python `.venv/bin/python` (3.12).

---

## §1 — Pre-baselines (§7.1)

```text
.venv/bin/pytest -q
=> 881 passed, 2 failed in 4.12s
   - tests/workflows/balances/v1/test_balance_derivation.py
       ::test_balance_free_bet_inventory_surfaces
   - tests/workflows/promos/v1/test_promo_derivations.py
       ::test_inventory_single_freebie_available

.venv/bin/lint-imports
=> 5 kept, 0 broken
```

`git status --short` showed the expected W10–W15 dirty state (full
output at §7 — character-for-character identical pre- and
post-session). The two failures are the pre-existing FB-inventory
pair carried since before W12.1; out of W12.2 scope per §9.

Gates 1 and 2 both passed: brief SHA `2928122d…` matched and 487
lines confirmed; the §3 pre-reads were read end-to-end in order
(brief, `staking.py`, `orchestrator.py`, `record_builder.py`,
`market_catalogue.py`, contract §9.7 + §14.4, DR-025 S139 amendment).

---

## §2 — Pre-build alignment

DR-025 S139 amendment (decisions.md L741) ruled commission is
Betfair's per-market `marketBaseRate`, snapshotted at hedge entry, 8%
fallback when unreadable. The W12.1 F§5.2 plumbing gap surfaced that
`_hedge_inputs_from` never forwarded `construction`, so new hedges
landed with `side=NULL` and the W12.1 lay maths never bit on new bets.

Both pieces touch `workflows/bet_entry/v1/` and were combined into one
bounded session per the Session 35 combine-related-fixes precedent.
Sequencing followed §6 verbatim: client surface → contract → staking
retirement → record builder → orchestrator → tests → verification.

Grep confirmed zero production callers of the retired symbols outside
the W4 package + its `__init__.py` re-exports. Two docstring
references survive in W12.1 territory (f#3, f#4); left untouched per
§9 hard limits.

---

## §3 — What was built

### §3.1 — `clients/betfair_client/v1/market_catalogue.py` (§5.1)

`MarketCatalogue` gained `market_base_rate: float | None = None`,
documented as a decimal fraction matching `BetRecord.commission` and
`HedgeStakeInput.commission_rate` (no downstream conversion). `_parse`
reads `payload.get("market_base_rate")` tolerantly; absence → `None`,
not an error. ÷100 normalisation lives at the translation boundary,
not at parse, per the brief's one-place-normalisation rule. Additive
per contract §14.4.

### §3.2 — `contracts/betfair_client_contract.md` (§5.2)

§9.7's return-shape block gained the `market_base_rate` field with
its unit; a new "v1.5 — `MARKET_DESCRIPTION` projection note"
paragraph records the projection-list extension. §6 history gained
a row dated 2026-06-10 Session 143 W12.2 as a **v1.5
backward-compatible addition** — driver DR-025 S139 amendment. v1.5
(not v1.3 as the brief named) preserves monotonic version ordering;
see f#1.

### §3.3 — `clients/betfair_client/v1/_translation.py` (§5.1 minimal equivalent)

The §9.7 catalogue path was not wired in the translation layer at
all pre-session; calling through the real `TranslatingTransport`
would have raised "unrecognised path". The brief permits the
minimal equivalent. Added: `_MARKET_CATALOGUE_RE`; request mapping
to `listMarketCatalogue` with five projections (`EVENT`,
`EVENT_TYPE`, `RUNNER_DESCRIPTION`, `MARKET_START_TIME`,
`MARKET_DESCRIPTION`); `_translate_market_catalogue` response
handler that performs the ÷100 normalisation on
`description.marketBaseRate` with a try/except guard against
non-numeric values. See f#2.

### §3.4 — `workflows/bet_entry/v1/staking.py` (§5.3)

Retired: `_COMMISSION_TABLE`, `_SportFamily`, `CommissionLookupKey`,
`resolve_commission`, `_classify_sport`, `commission_lookup`. Added:
`DEFAULT_COMMISSION_RATE: float = 0.08` and
`commission_from_market_base_rate(rate: float | None) -> float`
returning `rate` when not `None` and in `[0.0, 1.0)`, else
`DEFAULT_COMMISSION_RATE`. Out-of-range values fall back rather than
raising — bet entry must not hard-fail on a bad metadata field. Zero
is a valid Betfair rate (promotion window) and is passed through.
Module docstring rewritten in DR-025 S139 terms with the
table-drift lesson recorded. `HedgeStakeInput`, `compute_hedge_stake`,
`breakeven_betfair_price`, and the math review §6 worked examples
are untouched.

### §3.5 — `workflows/bet_entry/v1/__init__.py` (§5.3 re-exports)

`resolve_commission` removed from imports and `__all__`;
`DEFAULT_COMMISSION_RATE` and `commission_from_market_base_rate`
added in their place.

### §3.6 — `workflows/bet_entry/v1/record_builder.py` (§5.5)

W12.1 had added `construction` to `HedgeRecordInputs` but NOT
`commission` (the write site hardcoded `commission=None`). W12.2
adds `commission: float | None = None` (optional + default `None`,
backward compatible) and the hedge build path writes
`commission=inputs.commission`. The W12.1 deferred-next-brief
comment at the write site now names W12.2 as landed. The soft-book
builder is untouched (commission is a Betfair-leg concept). The
W12.1 side-derivation block is untouched.

### §3.7 — `workflows/bet_entry/v1/orchestrator.py` (§5.4)

`HedgeEntryRequest` gained `commission_rate: float | None = None`
(NULL preserves we-did-not-know; no coercion to 0.08 at write time)
and `construction: Construction | None = None`. A
`@model_validator(mode="after")` enforces side ⇔ construction
agreement; mismatch raises at request construction — programmer
error per the brief's exceptions carve-out.

`_hedge_inputs_from` now forwards both: `commission` verbatim;
`construction` from the request when supplied, else derived from
`side` (`"LAY"` → `LAY_AGAINST_BACK`, `"BACK"` →
`BACK_AGAINST_BACK`). The derivation is total — `side` is required —
so every new hedge gets a populated construction and therefore a
populated `side` tag via the W12.1 builder block. **This closes
W12.1 F§5.2 operationally.** `_modal_data_snapshot` carries the
two new fields (error-path data preservation parity). `Construction`
+ `model_validator` were added to the existing imports; no new
cross-boundary imports. Retry policy, Trigger A/B, pre-flight all
untouched.

### §3.8 — Tests (§5.6)

- **Staking** — four table-lookup tests removed; four
  `commission_from_market_base_rate` tests added (passthrough,
  `None` → 0.08, out-of-range → 0.08, zero-is-valid). All
  `compute_hedge_stake` math tests untouched.
- **Catalogue** — two new tests: `market_base_rate` present (0.08
  passthrough at parse boundary) and absent → `None`.
- **Orchestrator** — eight new tests in a W12.2 block at the
  end of the file: commission forwarded verbatim; commission `None`
  flows unchanged; construction derived from `side` both ways;
  explicit construction honoured; side↔construction mismatch raises
  `ValidationError`; `_modal_data_snapshot` carries the new fields
  on a path (b) error; end-to-end propagation through the record
  builder.
- **Record builder** — three new tests: commission lands;
  defaults to `None`; soft-book commission stays `None`.

Test-count delta: 4 removed + 17 added = **+13 net**.

---

## §4 — Post-baselines (§7.2) + spot-check (§7.3)

### §4.1 — Post-baselines

```text
.venv/bin/pytest -q
=> 894 passed, 2 failed in 4.09s
   - the same two pre-existing FB-inventory failures; no new ones.
   - delta: +13 net new passing tests (881 → 894), matching §5.6.

.venv/bin/lint-imports
=> 5 kept, 0 broken
```

`git status --short` is character-for-character identical to §7.1.
No new files added or removed; W12.2 edits landed inside the
already-tracked-modified `_translation.py` and inside already-
untracked W10–W15 build-region directories.

### §4.2 — End-to-end spot-check transcript

Through `HedgeEntryRequest` + `_hedge_inputs_from` +
`build_hedge_bet_record` with a deterministic in-process
`PlacementOutcome`. Two hedges:

```text
========================================================================
Bet 1 — LAY hedge | commission_rate=0.05 | no explicit construction
========================================================================
  request.commission_rate = 0.05
  request.construction    = None
  request.side            = 'LAY'
  forwarding → inputs.commission   = 0.05
  forwarding → inputs.construction = Construction.LAY_AGAINST_BACK
  bet_record.commission     = 0.05
  bet_record.side           = BetSideTag.LAY
  bet_record.matched_stake  = 72.82
  bet_record.matched_price  = 4.2

  Read-side W12.1 lay-branch derivation (c = stored 0.05):
    liability = stake*(price-1)        = 233.0240
    return if lay wins  = stake*(1-c)  =  69.1790
    return if lay loses = -liability   = -233.0240

========================================================================
Bet 2 — BACK hedge | commission_rate=None | implicit Construction B
========================================================================
  request.commission_rate = None
  request.construction    = None
  request.side            = 'BACK'
  forwarding → inputs.commission   = None
  forwarding → inputs.construction = Construction.BACK_AGAINST_BACK
  bet_record.commission     = None       (NULL preserved)
  bet_record.side           = BetSideTag.BACK
  bet_record.matched_stake  = 49.67
  bet_record.matched_price  = 3.1

  Read-side derivation (back branch, 8% read-side fallback):
    c (W12.1 read-side fallback)               = 0.08
    return if back wins = stake*(price-1)*(1-c) = 95.9624
    return if back loses = -stake               = -49.6700
```

Bet 1 demonstrates the load-bearing chain: a LAY hedge with the
modal-supplied per-market commission (`0.05`) lands as
`commission=0.05` + `side=LAY`, and the W12.1 lay branch uses the
stored `c=0.05`, not the 8% fallback. Bet 2 demonstrates
NULL-preservation: an unresolved commission flows through as `NULL`
and the read-side 8% fallback applies at derivation. Both records
carry their `side` tag — the W12.1 maths bites on new bets end-to-end,
closing F§5.2.

---

## §5 — Findings

### f#1 — Contract version label landed as v1.5, not v1.3

**Observed.** Brief §5.2 specifies "the changelog table gains a
v1.3 row". The contract already records v1.3 (Session 96 — §13.5
clarification) and v1.4 (Session 101 — §9.8 addition). The new row
landed as v1.5 to preserve monotonic version ordering; otherwise
identical to the brief (date 2026-06-10, Session 143 W12.2 Code,
DR-025 S139 amendment driver).

**Why it matters.** The brief's named version label was authored
against an outdated view of the running contract version. Surfacing
so the next operator-Claude triage can decide whether the brief
warrants a note or §6 introductory text should be tightened.

### f#2 — §9.7 catalogue path had no translation entry pre-session

**Observed.** `_translation.py` covered the other v1.x surfaces
but lacked `_MARKET_CATALOGUE_RE`, the `/v1/market/{id}/catalogue`
request mapping, and the response handler entirely. Calling
`get_market_catalogue` through the real `TranslatingTransport`
would have raised `BetfairRestError("unrecognised path …")`. The
catalogue surface had only been exercised against direct
path-style mocks. Per the brief's "minimal equivalent" permission,
W12.2 added the catalogue translation (regex + five projections +
÷100 boundary).

**Why it matters.** Without this, the §5.1 field would have been
unreachable end-to-end. Surfacing so the next session can decide
whether the wider §9.x translation surface warrants a sweep —
other surfaces wired correctly, only §9.7 was missing.

### f#3 — Docstring in `workflows/balances/v1/balance_derivation.py` references retired `_COMMISSION_TABLE`

**Observed.** Line 159 contains "mirrors `staking.py`'s
`_COMMISSION_TABLE` default." `_COMMISSION_TABLE` was retired in
§5.3. Left untouched per §9 hard limits.

**Why it matters.** Substantive read-side fallback behaviour
(matching 8%) remains correct; only the docstring reference dangles.
One-line edit is the entire remediation; flagged for a later tidy-up
brief or co-landing with adjacent balance-derivation work.

### f#4 — Docstring in `tests/workflows/balances/v1/test_balance_lay_branch.py` similarly references `_COMMISSION_TABLE`

**Observed.** Line 291 contains "(`staking.py` `_COMMISSION_TABLE`
default) per brief §5.5". Same nature as f#3, in the W12.1 test
suite. Left untouched per §9.

**Why it matters.** Same as f#3 — substantive behaviour correct;
only the docstring is stale. The W12.1 test still passes.

### f#5 — `_translation.py` diff includes pre-existing W3 §9.8 wiring

**Observed.** `git diff clients/betfair_client/v1/_translation.py`
returns a hunk that includes both W12.2 catalogue work AND
pre-existing W3 §9.8 work (`_ORDERS_CURRENT_RE`,
`_build_list_current_orders_params`,
`_translate_list_current_orders`). The §9.8 entries are W3 work
that landed pre-session and were visible in the §7.1 status as the
file's already-modified hunk; my W12.2 footprint is exclusively the
catalogue doc-line, `_MARKET_CATALOGUE_RE`, the two catalogue match
blocks, and the new `_translate_market_catalogue` function (~90
lines).

**Why it matters.** No remediation needed; recorded so a diff-based
review of W12.2's footprint does not double-count W3-era work.

---

## §6 — Self-assessment

Both pieces landed inside one bounded session. Commission sourcing
pivoted from the W4 static table onto `marketBaseRate` with the §9.7
surface extension and the catalogue translation backfill it implied.
The orchestrator now forwards both `commission_rate` and
`construction` so the W12.1 side-derivation block sees a populated
`Construction` on every new hedge — the `side` tag lands on the
record and the W12.1 lay maths bites end-to-end. The W12.1
"preserved-but-wrong-for-lays" state is gone for new bets; existing
rows are untouched per §9.

Tests: +13 net new with edge coverage on the sourcing function
(None, out-of-range, zero) and the side↔construction validator (both
directions). 894 / 2 baseline maintained. Lint-imports stayed 5 / 0
(no new cross-boundary imports). Spot-check confirms data flow with
concrete numbers.

Surprises (v1.5-vs-v1.3 label conflict; missing catalogue
translation) became findings rather than blockers. The
minimal-equivalent translation addition stayed inside §5.1 anchor
scope. §9 hard limits respected throughout — no edits to
`balance_derivation.py`, no W15 / ops-log, no `hedge_state`, no
backfill, no Alembic, no refactors in passing, no dirty-tree git ops.

---

## §7 — Final `git status --short`

```text
 M .importlinter
 M clients/betfair_client/v1/__init__.py
 M clients/betfair_client/v1/_connection.py
 M clients/betfair_client/v1/_translation.py
 M clients/betfair_client/v1/live_pricing.py
 M clients/betfair_client/v1/streaming.py
 M domain/bets/__init__.py
 M pyproject.toml
 M store/__init__.py
 M tests/clients/betfair_client/v1/test_streaming.py
 M uv.lock
?? clients/betfair_client/v1/account_funds.py
?? clients/betfair_client/v1/current_orders.py
?? clients/betfair_client/v1/market_catalogue.py
?? contracts/betfair_client_contract.md
?? contracts/vps_client_contract.md
?? domain/accounts/
?? domain/cash_flow/
?? domain/ops/
?? domain/promos/
?? scripts/
?? store/repositories/accounts.py
?? store/repositories/bets.py
?? store/repositories/cash_flow.py
?? store/repositories/ops.py
?? store/repositories/promos.py
?? store/schema/accounts.py
?? store/schema/bets.py
?? store/schema/cash_flow.py
?? store/schema/ops.py
?? store/schema/promos.py
?? tests/clients/betfair_client/v1/test_account_funds.py
?? tests/clients/betfair_client/v1/test_current_orders.py
?? tests/clients/betfair_client/v1/test_market_catalogue.py
?? tests/scripts/
?? tests/store/
?? tests/ui/
?? tests/workflows/
?? ui/api/
?? ui/web/
?? workflows/balances/
?? workflows/bet_entry/v1/
?? workflows/cash_flow/
?? workflows/ops/
?? workflows/promos/
```

Identical to the §7.1 pre-baseline. W12.2 edits land within the
already-tracked-modified `_translation.py` and within already-
untracked W10–W15 directories; no git operations performed.

**End of report.**
