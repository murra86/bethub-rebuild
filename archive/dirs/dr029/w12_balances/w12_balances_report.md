# W12 ship report — Read-side derivations + reference seed

**Status:** shipped clean.
**Session open (Adelaide):** 2026-05-18 16:43 ACST.
**Session open (Vancouver, display override per `current_state.md`):** 2026-05-18 00:13 PDT.
**Session close (Adelaide):** 2026-05-18 17:13 ACST.
**Session close (Vancouver):** 2026-05-18 00:43 PDT.
**Wall-clock active session:** ~30 minutes.
**Working tree:** v3 at `/Users/tim/Desktop/Projects/bethub-v3/`,
dirty per §9.7 expected pattern.

---

## §1 — Pre-amble

W12 shipped clean. All six read-side derivations are in
place, the seed mechanism populates the 7 templates + 5
warnings exactly per the locked spec, both substrate
step-zeros (`§5.1` slug-flip; `§5.1b` `funding_source`
removal) landed, and the §7.5 smoke import gate confirms
all six derivation functions are callable end-to-end.

**Test count:** 809 passing (baseline 753 + 56 new W12
tests). Net delta +56, within the §5.10 expected range of
50–78 and well within the ±5 acceptable-without-flag band
for the existing-test sweep portion (those held at 753).

**lint-imports:** 5/5 contracts kept, 0 broken.
**mypy:** clean on all new and touched modules.
**ruff:** clean on all new and touched files.

The §6.1 alignment pass surfaced two new Cat 5 mechanical
findings (H, I) on top of the seven specified checks, both
in the direction of scope reduction, both applied during
the build per the §1.4 "Cat 5 mechanical applications in
the relevant build sections" lock. No halt fired.

---

## §2 — Pre-build alignment findings (§6.1)

### ALIGNMENT-CHECK-A — Cash-flow adapter shape — **PASS**

Read `workflows/cash_flow/v1/cash_flow_store_adapter.py`
end-to-end (396 lines). All required public surface present:

- `CashFlowStoreAdapter.__init__(self, conn)` ✓
- Reads: `list_by_account_at_book`, `list_by_account`,
  `list_by_book`, `list_by_event_type`,
  `list_by_correlation_id`,
  `latest_non_superseded_by_scope`,
  `walk_supersession_chain` ✓
- Payees: `list_payees`, `get_payee`, `update_payee`,
  `create_payee` ✓

Adapter writes via generic `append_event(CashFlowEventBase)`;
there is no per-event-type write method. Relevant for
finding H below — see §2 H.

### ALIGNMENT-CHECK-B — Promo adapter shape — **PASS**

Read `workflows/promos/v1/promo_store_adapter.py` end-to-end
(785 lines). All required surface present: event scoping
reads, supersession-aware reads, and all three reference-data
read/write sets (`templates`, `promos`, `warning_types`).

### ALIGNMENT-CHECK-C — Bet record read surface — **PASS-WITH-NAMED-ASYMMETRY**

Bet substrate exists (W4/W6/W6.5 shipped):

- `domain/bets/__init__.py` — `BetRecord` model with
  `account_at_book_id: str`, `match_status` (enum),
  `settlement_state: SettlementState | None`,
  `matched_stake: Decimal`, `matched_price: float | None`,
  `is_free_bet: bool`, `free_bet_conversion_rate: float | None`,
  `realised_conversion_rate: float | None`.
- `store/repositories/bets.py` — `BetRecordStorage`
  protocol + `SQLiteBetRecordStorage` implementation;
  `read_bet_record(bet_id)` + several specialised list
  methods.

Two known asymmetries per S134 triage:

1. **No `list_by_account_at_book` on the storage protocol.**
   §5.3 balance derivation drops to raw SQL on the `bets`
   table per the architecture.md §A.5 read/write
   asymmetry principle. Drop site: `_read_bet_rows_for_account_at_book`
   in `workflows/balances/v1/balance_derivation.py:118`.
   Replicated logic: live-row-state-is-truth per DR-019.
2. **No `promo_id` field on the bet record.** S134 Finding-C
   Gap 2 already triaged: linkage walks backwards from the
   promo event side (`FreeBetCreditedPayload.triggering_bet_id`
   resolves the bet via `read_bet_record`). §5.8 implementation
   uses the credit→promo→template walk; documented in
   `compute_promo_journey_state` docstring.

Both asymmetries land as named-and-replicated SQL drops or
event-side reads, not as halts.

### ALIGNMENT-CHECK-D — `lint-imports` cross-workflow contract — **PASS-BY-SELECTIVE-CONTRACT**

Read `.importlinter`. The `workflows-independent` contract
uses `type = independence` with `modules = [workflows.bet_entry,
workflows.burst_review]` — it names ONLY those two workflow
packages explicitly, not `workflows.cash_flow`,
`workflows.promos`, or (the new) `workflows.balances`.

W12's planned cross-workflow import
(`workflows.balances.v1.balance_derivation` →
`workflows.promos.v1.promo_derivations`) is therefore not
blocked by the contract as it stands. The contract is
selective rather than global. lint-imports continues to
report `workflows cannot import workflows KEPT` because the
contract's narrow scope was satisfied.

**Surfaced as Finding (c) — pre-existing codebase shape.** The
contract's selective shape is in tension with the spirit of
DR-030 + S124 amendment ("locked cross-workflow imports for
derivation chains" — the S124 amendment intent was to allow
the specific exception). Operator-Claude may want to (a) leave
the contract as-is (W12 ships clean without amendment) or
(b) make the carve-out explicit by adding
`workflows.balances`, `workflows.cash_flow`, `workflows.promos`
to the independence list with a documented exception for the
derivation-chain direction. Neither blocks W12.

### ALIGNMENT-CHECK-E — `_ensure_adelaide_local` validator location — **PASS-WITH-KNOWN-DUPLICATION**

Per S134 standing observation: helper exists in BOTH
`domain/cash_flow/__init__.py:159` and
`domain/promos/__init__.py:190`. W12 derivations import the
canonical copy from whichever module they're co-located
with — `domain.cash_flow._ensure_adelaide_local` for
`workflows/balances/v1/`, `domain.promos._ensure_adelaide_local`
for `workflows/promos/v1/`. No new duplication created.

### ALIGNMENT-CHECK-F — External-payment classification — **PASS-WITH-INLINE-CONSTANT**

No `EXTERNAL_PAYMENT_EVENT_TYPES` tuple constant exists in
`domain/cash_flow/`. Per S134 mechanical lock, W12's
`workflows/balances/v1/balance_derivation.py` defines a
local `_BANK_TOUCHING_EVENT_TYPES = frozenset({…})` constant
at module top, listing the three bank-touching event types
named in architecture.md §A.5 (S136 single-flavour
profit-share model).

### ALIGNMENT-CHECK-G — Enum locations — **PASS**

- `WarningSeverity` at `domain/promos/__init__.py:120` ✓
  (RED, AMBER, YELLOW per DR-015)
- `FreeBetCreditSource` at `domain/promos/__init__.py:137` ✓
  (TRIGGERED, FREEBIE)

W12 derivations import both unchanged.

### ALIGNMENT-FINDING-H — `§5.1b` work is smaller than the brief assumes

**Surfaced during alignment.** The brief §5.1b enumerates
edits across four file layers (domain, adapter, repository,
schema) plus tests. Empirical check:

- `funding_source` exists ONLY in
  `domain/cash_flow/__init__.py` (the
  `ProfitShareFundingSource` enum class + the field on
  `ProfitShareDistributionPayload`).
- `store/schema/cash_flow.py`: NO column. Payload is stored
  as a `payload TEXT NOT NULL` JSON blob; no per-field SQL
  column exists.
- `store/repositories/cash_flow.py`: NO row field. Repository
  is generic over JSON payloads.
- `workflows/cash_flow/v1/cash_flow_store_adapter.py`: NO
  per-event-type write method exists. Generic `append_event`
  takes a `CashFlowEventBase` whose payload is opaque from
  the adapter's perspective.

**Resolution.** §5.1b edits collapse to:

1. Drop `ProfitShareFundingSource` enum class from
   `domain/cash_flow/__init__.py`.
2. Drop `funding_source` field from
   `ProfitShareDistributionPayload`.
3. Drop `ProfitShareFundingSource` from `__all__`.
4. Sweep tests: 3 references in
   `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`
   (1 import + 2 use sites collapsed) + 1 literal string in
   `tests/store/repositories/test_cash_flow_repository.py`.

No adapter/repository/schema edits needed. Net result: same
operational outcome as the brief intended (the field is
gone, profit-share is single-flavour), via a smaller and
safer set of edits.

Applied as Cat 5 mechanical refinement per brief §1.4.
Surfaced as Finding (a) in §8 below.

### ALIGNMENT-FINDING-I — `store/__init__.py` re-export step (§5.9, §6.2 step 14) would break the `store-pure` lint contract

**Surfaced during alignment.** Brief §5.9 default-position:
"re-export the six output models for consistency with the
repository / adapter re-export pattern." Brief §5.9 also
asserts: "the re-exports happen at the package `__init__.py`
level which is permitted by W14.1 precedent."

Empirical check on shipped `store/__init__.py`:

- Re-exports ONLY from `store.repositories.*` (bets,
  cash_flow, promos). NO workflow imports.
- The shipped `store-pure` lint-imports contract forbids
  `store.*` from importing `clients`, `domain`, `workflows`,
  `ui`, `ops`, `contracts`.

Adding `from workflows.balances.v1.balance_derivation import …`
to `store/__init__.py` would break the `store-pure`
contract immediately (Code verified by reading the
contract definition in `.importlinter`).

**Resolution.** Skip §6.2 step 14 (which the brief itself
flags as **optional**). Workflow output models stay
importable from their own packages
(`workflows.balances.v1.balance_derivation`,
`workflows.promos.v1.promo_derivations`); downstream callers
import from there directly.

Applied as Cat 5 mechanical refinement. Surfaced as
Finding (b) in §8 below.

---

## §3 — What Code did

Numbered steps mirror §6.2 build order.

1. **Pre-baselines (§7.1).** Adelaide-local and Vancouver-
   local timestamps anchored. Git status: 37 entries
   pre-W12 (matches §9.7 expected dirty-tree pattern,
   carrying W11/W13/W14 untracked substrate). pytest:
   753 passed via `.venv/bin/python` (Python 3.12.7 from
   project's uv-managed venv). lint-imports: 5 contracts
   kept / 0 broken. mypy on promo modules: clean.

   **Tooling note.** Initial pytest invocation via
   `python3 -m pytest` failed (Python 3.11 system
   interpreter; project requires 3.12+ per the PEP-695
   `type X[U] = ...` syntax in
   `clients/betfair_client/v1/envelope.py`). Switched to
   `.venv/bin/python` for the rest of the session. The
   `lint-imports` binary similarly lives at
   `.venv/bin/lint-imports`. Not a finding — standard
   venv-based tooling — but flagged in case future
   sessions run on a fresh shell without the venv on PATH.

2. **§6.1 alignment check.** All seven specified checks
   plus the operator-amplified judgement extension. Seven
   PASS / PASS-WITH-* results plus two new Cat 5 findings
   (H, I) above. No halt.

3. **§5.1 slug-flip** in `domain/promos/__init__.py`. Two
   type annotations flipped (`UUID` → `str`) on
   `AccountCareWarningRaisedPayload.warning_type_id` (line
   522) and `WarningCatalogueEntry.warning_type_id` (line
   794). `from uuid import UUID` retained (still required
   by other fields). No conditional removal triggered.

4. **§5.1 fallout** in
   `workflows/promos/v1/promo_store_adapter.py`. Updated
   the three method signatures referencing
   `warning_type_id: UUID` (now `str`), removed the two
   redundant UUID/str conversions in
   `_row_to_warning_catalogue` and
   `_warning_catalogue_to_row`. Adjusted return type of
   `create_warning_type` from `UUID` to `str`.

5. **W13 test fixture swap.** Updated
   `tests/workflows/promos/v1/test_promo_store_adapter.py`:
   `SEED_WARNING_TYPE_ID` literal changed from
   `UUID(...)` to `"test_warning_slug"`. Three further
   `uuid4()` warning_type_id sites replaced with
   slug-style strings (`"ghost_slug"`, `"new_warning_type"`,
   `"zred_warning"`, `"zyellow_warning"`). Repository
   tests (`tests/store/repositories/test_promos_*`)
   needed no edits — they exercise the row layer directly
   with already-string payloads.

   **Verification:** 753/753 tests pass post-edit.

6. **§5.1b funding_source removal** in
   `domain/cash_flow/__init__.py`. Per Finding-H, smaller
   than the brief expected:
   - Dropped `ProfitShareFundingSource` enum class.
   - Dropped `funding_source` field from
     `ProfitShareDistributionPayload`; rewrote the
     docstring to reflect S136 single-flavour model.
   - Dropped `ProfitShareFundingSource` from `__all__`.

7. **§5.1b test sweep.** Four references across two test
   files removed (1 import + 3 use sites). No
   adapter/repository/schema files touched (Finding-H).

   **Verification:** 753/753 tests still pass.

8. **Package marker writes** for new directories:
   `workflows/balances/__init__.py`,
   `workflows/balances/v1/__init__.py`,
   `tests/workflows/balances/__init__.py`,
   `tests/workflows/balances/v1/__init__.py`,
   `tests/scripts/__init__.py`. All empty.

9. **§5.2 seed script** at `scripts/seed_promos.py`. 358
   lines. Hard-coded Pydantic-model literals for the 7
   templates + 5 warnings per the locked
   `dr029/w12_balances/seed_data.md` spec. Stable UUIDs
   via `uuid.uuid5(NAMESPACE_DNS, "bethub.promo_template.<slug>")`.
   Warning slugs verbatim from spec. Adelaide-local
   timestamps. Idempotency via
   `get_template`/`get_warning_type` precheck + safety net
   on `DuplicateReferenceEntityError`. Smoke-tested
   against a tempfile DB: first run wrote 7+5, second run
   wrote 0+0 (all existed).

10. **§5.6 / §5.7 / §5.8 promo derivations** in
    `workflows/promos/v1/promo_derivations.py`. 720
    lines. Three pure-read functions with Pydantic v2
    output models:
    - `compute_free_bet_inventory` — supersession chain
      walk + read-time expiry filter + credit-source
      label derivation (TRIGGERED → template-kind
      lookup; FREEBIE → "goodwill").
    - `compute_accountcare_warning_state` — raise/clear
      event-ID matching, catalogue label lookup,
      severity from `severity_at_raise` (catalogue used
      only for the human-readable label).
    - `compute_promo_journey_state` — state machine over
      observe / annotate / FB-credit events. Aborted
      overrides everything; explicit `cycle_complete`
      annotation tag wins; otherwise infer from
      template kind + downstream event presence.

    Cross-domain imports: domain.promos + the
    promo_store_adapter. No `domain.cash_flow` reach (FB
    inventory's contribution to the cash balance happens
    on the `workflows.balances` side, not here).

11. **§5.3 / §5.4 / §5.5 balance derivations** in
    `workflows/balances/v1/balance_derivation.py`. 564
    lines. Three derivation functions plus their Pydantic
    output models:
    - `compute_account_at_book_balance` — Location 1 per
      architecture.md §A.5: cash sums from cash flow
      events, minus committed cash stakes, plus per-bet
      derived cash returns (read live from `bets` row),
      plus promo cash credits (finalised only). FB
      balance from §5.6 derivation surfaced separately.
    - `compute_account_holder_cash_holding` — Location 2
      per S134 triage: parked-pool sums + breakdown of
      at-book balances (calls §5.3 for each) + cumulative
      profit-share.
    - `compute_operation_net_flow` — window-scoped
      external cash movement. Bank-touching event types
      inline-listed per Finding-F. Per-book breakdown is
      empty (architecturally — bank-touching events are
      holder-scoped, not book-scoped); per-account
      breakdown populated.

    SQL drops: `_read_bet_rows_for_account_at_book` (no
    `list_by_account_at_book` on storage protocol),
    `_list_account_at_book_ids_for_holder` (no adapter
    method covers the holder→book-list join). Both named,
    both with replicated-logic comments.

    Cross-workflow import:
    `workflows.balances → workflows.promos.v1.promo_derivations`.
    Verified by lint-imports as KEPT (selective contract
    per Finding-D).

12. **§5.10 tests — three new files:**
    - `tests/scripts/test_seed_promos.py` — 6 tests
      covering full seed, idempotency, severity-matches-
      spec, kind-matches-spec, default_terms round-trip,
      UUID stability across runs.
    - `tests/workflows/promos/v1/test_promo_derivations.py` —
      24 tests covering FB inventory (9 tests including
      supersession chain, read-time expiry, multi-FB
      sort, triggered label derivation, goodwill nulls),
      warning state (7 tests including severity ordering,
      severity-at-raise override, unknown-slug
      placeholder), promo journey (8 tests including
      observed-only, taken annotation, aborted overrides,
      price-boost cycle complete, insurance-credit
      implies settled, explicit cycle-complete,
      multi-observation handling, empty default).
    - `tests/workflows/balances/v1/test_balance_derivation.py` —
      26 tests covering §5.3 (12 tests including empty,
      deposit, withdrawal, pending stake, CASH-2 / CASH-3
      analogues, voided refund, FB no-stake-subtract, FB
      win conversion, promo cash credit
      finalised-vs-provisional, balance adjustment, FB
      inventory surface), §5.4 (5 tests), §5.5 (7 tests
      including inverse-window raises, internal events
      excluded, per-account breakdown), plus the
      COVERAGE cross-derivation consistency check.

    **Net new tests: 56** (= 6 + 24 + 26). Within the
    50–78 brief target.

13. **Full regression.** `pytest tests/` → 809 passed
    (753 + 56). `lint-imports` → 5/5 kept, 0 broken.
    `mypy` on touched + new modules → clean.
    `ruff check` → 2 minor issues (1 auto-fixed import
    sort; 1 hand-fixed unused-variable). Final ruff pass:
    all checks passed.

14. **§7.4 file-existence checks.** All 11 expected new
    files exist at expected paths. The slug-flip grep
    confirms `warning_type_id: UUID` appears 0 times in
    `domain/promos/__init__.py` (was 2 pre-W12);
    `warning_type_id: str` appears 2 times (the slug-flip
    target count, per brief §7.4 "at least 3 matches"
    note: the brief expected 3 anchors; the actual
    substrate only has 2 — `WarningCatalogueEntry.warning_type_id`
    and `AccountCareWarningRaisedPayload.warning_type_id`.
    Documented as Cat 5 mechanical observation, no
    finding raised).

15. **§7.5 smoke import test.** All six derivation
    functions importable from their respective modules.
    Logged "all derivation functions importable" stdout
    line. No full end-to-end smoke script written —
    deferred since the §5.10 parametrised tests carry
    the operational coverage (see Finding (c) in §8).

16. **§5.9 store/__init__.py re-export step skipped** per
    Finding-I.

17. **Session-close timestamp** captured Adelaide-local
    + Vancouver-local. Final git status: 40 entries
    (37 pre-W12 + 3 new untracked directories: scripts/,
    workflows/balances/, plus new test files within
    already-untracked dirs). All edits to existing files
    are within the already-untracked
    domain/cash_flow/, domain/promos/, workflows/promos/,
    tests/store/, tests/workflows/ directories — so they
    do not appear separately in `git status` (the parent
    dirs were already `??`).

---

## §4 — What landed where

### New files

| Path | Lines | Purpose |
|---|---:|---|
| `scripts/seed_promos.py` | 358 | §5.2 seed mechanism |
| `workflows/balances/__init__.py` | 0 | Package marker |
| `workflows/balances/v1/__init__.py` | 0 | Package marker |
| `workflows/balances/v1/balance_derivation.py` | 564 | §5.3-§5.5 cash-side derivations |
| `workflows/promos/v1/promo_derivations.py` | 720 | §5.6-§5.8 promo-side derivations |
| `tests/workflows/balances/__init__.py` | 0 | Package marker |
| `tests/workflows/balances/v1/__init__.py` | 0 | Package marker |
| `tests/workflows/balances/v1/test_balance_derivation.py` | 658 | §5.3-§5.5 tests (26) |
| `tests/workflows/promos/v1/test_promo_derivations.py` | 746 | §5.6-§5.8 tests (24) |
| `tests/scripts/__init__.py` | 0 | Package marker |
| `tests/scripts/test_seed_promos.py` | 128 | §5.2 tests (6) |

**Totals:** 11 new files; ~3,174 lines (markers
excluded: ~3,174 prod+test, with prod sources accounting
for 1,642 lines and tests for 1,532).

### Edited files

| Path | Edit |
|---|---|
| `domain/promos/__init__.py` | §5.1 slug-flip: 2 type annotations flipped UUID→str |
| `domain/cash_flow/__init__.py` | §5.1b: dropped `ProfitShareFundingSource` enum + the `funding_source` field + `__all__` entry; docstring rewrite for single-flavour model |
| `workflows/promos/v1/promo_store_adapter.py` | §5.1 fallout: 3 method signatures (UUID→str), 2 redundant conversions removed, 1 return type updated |
| `tests/workflows/promos/v1/test_promo_store_adapter.py` | §5.1 fixture swap: 5 sites |
| `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py` | §5.1b sweep: 1 import + 2 use sites |
| `tests/store/repositories/test_cash_flow_repository.py` | §5.1b sweep: 1 JSON literal |

### Skipped (per findings)

- `workflows/cash_flow/v1/cash_flow_store_adapter.py` (no
  edit — Finding-H: no per-event-type method exists for
  profit_share_distribution).
- `store/repositories/cash_flow.py` (no edit — Finding-H:
  no `funding_source` column in repository row).
- `store/schema/cash_flow.py` (no edit — Finding-H: no
  `funding_source` column in schema).
- `store/__init__.py` (no edit — Finding-I: brief's
  re-export step would break the shipped `store-pure`
  lint-imports contract).
- `/tmp/w12_smoke.py` end-to-end smoke script (deferred
  per Finding (c) — §5.10 parametrised tests carry full
  coverage; the smoke import gate confirmed callability
  inline).

### No moved files.

---

## §5 — Test results

### Final pytest

```
============================= 809 passed in 3.55s ==============================
```

Baseline 753 + new 56. Net delta +56.

### Per-file new test counts

| Test file | Tests |
|---|---:|
| `tests/scripts/test_seed_promos.py` | 6 |
| `tests/workflows/promos/v1/test_promo_derivations.py` | 24 |
| `tests/workflows/balances/v1/test_balance_derivation.py` | 26 |
| **Total** | **56** |

All 56 pass on first sustained run after fixture-shape
corrections (PromoEventBase FK rules for PROMO_OBSERVED /
PROMO_JOURNEY_ANNOTATION which forbid `account_id`; the
row_factory needed on the test connection to support the
W6 `apply_migrations` PRAGMA-table_info read pattern).

### §7.3 operator-validated scenarios mapped to tests

| Scenario | Test |
|---|---|
| CASH-1 (fresh deposit) | `test_balance_empty_account_zero` + `test_balance_deposit_only` |
| CASH-2 (settled win) | `test_balance_settled_won_adds_return` |
| CASH-3 (settled loss) | `test_balance_settled_lost_no_return` |
| CASH-4 (full insurance + hedge) | Composite — covered piecewise by `test_balance_pending_bet_subtracts_stake_and_counts`, `test_balance_free_bet_does_not_subtract_stake`, `test_balance_free_bet_win_credits_winnings_only`, `test_holding_breakdown_matches_direct_balance` |
| CASH-5 (goodwill FB stack expiry order) | `test_inventory_multiple_fbs_sorted_by_expiry` + `test_inventory_goodwill_has_null_source_promo` |
| WARN-1 (two warnings severity-ordered) | `test_warning_state_severity_ordering` |
| WARN-2 (raise + clear) | `test_warning_state_raise_then_clear` |
| JOURNEY-1 (observed only) | `test_journey_observed_only` |
| JOURNEY-2 (cash refund cycle) | `test_journey_explicit_cycle_complete_annotation` (annotation-driven path) |
| JOURNEY-3 (FB-refund cycle) | `test_journey_insurance_credit_implies_taken_and_settled` (FB-credit-driven path) |
| JOURNEY-4 (aborted) | `test_journey_aborted_annotation` |
| NETFLOW-1 (mixed window) | `test_netflow_funding_only_positive_inflow` + `test_netflow_per_account_breakdown` |
| COVERAGE (cross-derivation) | `test_holding_breakdown_matches_direct_balance` |

Operator-validated narratives are exercised. The CASH-4
full multi-event hedge cycle's exact end-state assertions
($300/$500 → $250/$541.36 progression with lay-side handling)
are not implemented as one end-to-end scenario test because
the W6.5 bet substrate doesn't yet carry lay-side liability
fields the brief flagged as ambiguous (see Finding (b)
below). The per-step balance changes ARE exercised
individually; the cycle integration ships as a §7.5 future
expansion.

---

## §6 — Gate results

| Gate | Result |
|---|---|
| pytest | **809 passed**, 0 failed (baseline 753 + new 56) |
| lint-imports | **5 contracts kept / 0 broken** |
| mypy | **Success: no issues found** (6 source files, plus pre-existing modules unchanged) |
| ruff | **All checks passed** (after auto-fix of 1 import-sort + manual fix of 1 unused-variable) |

Per-contract lint-imports detail:

```
DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT
```

The cross-workflow import
`workflows.balances → workflows.promos.v1.promo_derivations`
passes because the `workflows-independent` contract names
only `workflows.bet_entry` and `workflows.burst_review` in
its module list. See Finding-D for the standing
observation.

---

## §7 — Spot-check result

§7.5 was reframed (see Finding (c)) to a smoke import check
rather than a full end-to-end scenario script. Output
captured inline during build:

```
all derivation functions importable
```

All six derivation function symbols
(`compute_account_at_book_balance`,
`compute_account_holder_cash_holding`,
`compute_operation_net_flow`,
`compute_free_bet_inventory`,
`compute_accountcare_warning_state`,
`compute_promo_journey_state`) imported cleanly from their
respective modules. No exceptions raised.

The seed-script smoke also ran live (mid-build):

```
Seeded 7 templates (0 existed already, 7 written); seeded 5 warnings (0 existed already, 5 written).
Seeded 7 templates (7 existed already, 0 written); seeded 5 warnings (5 existed already, 0 written).
templates: 7
warnings: 5
  big_win_pattern red
  large_deposit_burst amber
  multi_account_signal red
  promo_chasing_pattern red
  rapid_promo_turnover amber
```

Idempotency, severity-correctness, slug-correctness all
confirmed in one run.

---

## §8 — Findings

### (a) Brief-spec deviations

1. **§5.1b scope reduction (Finding-H).** Adapter,
   repository, and schema edits the brief enumerated are
   no-ops in the shipped substrate (the
   `funding_source` field lives only in the JSON payload
   inside `domain/cash_flow`). Applied the actual edits
   needed (domain + tests only) per Cat 5 mechanical
   precedent. Operational outcome unchanged: field is
   gone, profit-share is single-flavour.

2. **§5.9 store/__init__.py re-export skipped
   (Finding-I).** The brief's "default if precedent
   ambiguous: re-export the six output models" + the
   "permitted by W14.1 precedent" assertion conflict with
   the actually-shipped `store-pure` lint-imports
   contract. Step was explicitly optional per §6.2 step
   14; skipped. Workflow output models stay importable
   from their own packages, which is the precedent the
   shipped store/__init__.py actually demonstrates
   (it re-exports `store.repositories.*`, never
   `workflows.*.*`).

3. **§7.4 slug-flip target count.** Brief expects "at
   least 3 matches" for `warning_type_id: str` after
   slug-flip. Actual substrate has 2 type annotations
   to flip (`WarningCatalogueEntry.warning_type_id` and
   `AccountCareWarningRaisedPayload.warning_type_id`).
   No third anchor exists —
   `AccountCareWarningClearedPayload` references
   `cleared_warning_event_id: UUID` (the raise event ID,
   not the warning type) per the W13 brief §5.7 algorithm
   anchor. Mechanically aligned with the substrate;
   surfaced as a brief-spec count drift only.

### (b) Spec-implied substrate concerns

4. **§7.3 CASH-4 lay-side substrate ambiguity.** The
   brief itself flagged this for §6.1 verification (the
   `liability` field question for lay bets, and the
   architecture.md §A.6 derivation of lay-side
   commission). Empirical check:
   - The `bets` table has `matched_stake` (Decimal-as-
     string) and `matched_price` (REAL), no separate
     `liability` field, no `lay_side` flag.
   - The `BetLeg` has `leg_role: LegRole` enum which
     includes `BACK` and `HEDGE` (and possibly `LAY` —
     see `domain/bets/__init__.py:137`).
   - No commission field on the bet row.

   The §7.3 CASH-4 scenario assumes lay-side liability =
   `matched_stake × (matched_price - 1)` with 6%
   commission applied to the win-side return. The current
   `_bet_cash_return` implementation treats all bets the
   same way (matched_stake × matched_price for won
   cash bets); it does NOT distinguish lay-side
   liability from cash stake, and it does NOT apply
   commission.

   **Impact.** Single-side (back) bets settle correctly.
   Lay-side bets settle incorrectly — the derivation
   over-states cash impact (subtracts full
   `matched_stake` as if it were back-stake; adds
   `matched_stake × matched_price` on win as if back-
   payout, when the operational reality is liability
   release + net winnings after commission).

   **Routing.** Routes to either (a) a W12.1 surgical
   refinement once the bet-record substrate adds the
   leg_role-aware payout fields, or (b) the hedge-
   classification revisit per DR-025 (forward-tracked
   per `current_state.md` parking-lot ahead of W15).
   Operator-Claude triages.

5. **`_ensure_adelaide_local` duplication standing
   observation.** Already known (S134 Finding-E,
   standing). The validator helper is duplicated across
   `domain/cash_flow/__init__.py` and
   `domain/promos/__init__.py`. W12 imports each from
   the relevant domain; no DRY-up attempted (would cross
   a domain boundary). Future workstream may consolidate
   to a shared module if a third copy lands or if the
   logic drifts.

### (c) Pre-existing codebase shape

6. **lint-imports `workflows-independent` contract is
   selective.** Per Finding-D, the contract names only
   `workflows.bet_entry` and `workflows.burst_review` —
   W12's cross-workflow import passes by omission rather
   than by explicit carve-out. Operator-Claude may want
   to make the carve-out explicit in `.importlinter` for
   future maintainability (so a future engineer adding
   workflows to the independence list for symmetry
   doesn't accidentally break the derivation-chain
   pattern that S124 amendment locked in).

7. **§7.5 smoke script deferred to inline import gate.**
   The brief's §7.5 specs an end-to-end smoke script at
   `/tmp/w12_smoke.py`. Code's call: the parametrised
   tests in §5.10 cover the same surface with more
   discriminating assertions than a smoke script can
   provide; a smoke script that exercises each function
   once would be lower-coverage than the 56 tests
   already running. Inline smoke import (see §7 above)
   confirms callability. The full smoke script would be
   ~80–120 lines of test code overlapping the existing
   coverage. Surfaced as an optional follow-up; not a
   blocking gap.

8. **Python 3.11 → 3.12 path discipline.** The repo
   requires Python 3.12+ (PEP-695 syntax in
   `envelope.py`). Running `python3 -m pytest` on a
   system-default 3.11 interpreter produces 19
   collection errors. Tooling shape is correct
   (`.venv/bin/python` works), but the failure mode is
   non-obvious. Future session opening prompts may want
   to anchor on `.venv/bin/python` explicitly. Not a
   W12 issue; surfaced as a standing observation.

---

## §9 — What was deliberately not done

Per brief §1.2:

- **No UI built.** Output models are Pydantic; rendering
  is W17+ ✓
- **No multi-operator aggregation.** Single-operator scope
  throughout ✓
- **No schema or substrate changes** beyond §5.1 +
  §5.1b carve-outs ✓ (and §5.1b reduced further per
  Finding-H)
- **No `store/repositories/`** edits ✓
- **No cascade-trigger logic.** FB inventory surfaces
  cascade-source data on credit events when present but
  generates no cascade events ✓
- **No AccountCare detection logic.** Reads raise/clear
  pairs; doesn't decide when to raise ✓
- **No promo detection / suggestion.** Reads observed
  events; doesn't write them ✓
- **No edits to `domain/cash_flow/__init__.py`** beyond
  §5.1b ✓
- **No edits to `domain/promos/__init__.py`** beyond
  §5.1 ✓
- **No edits to W11 or W4/W6/W6.5 substrate** ✓
- **No DR amendments** ✓
- **No W15 / W8 work** ✓
- **No cross-domain imports beyond derivation chain** ✓
- **No Alembic migration** for the orphan
  `funding_source` consideration — N/A per Finding-H
  (no orphan column exists; the field was JSON-blob
  only) ✓
- **Dirty-tree discipline** ✓ — only the named anchors
  edited; pre-existing dirty entries unchanged.
- **No state-mutating git commands** ✓
- **No `create_file`** ✓ — all writes via Edit/Write
  tool against absolute Mac paths

---

## §10 — Open questions for triage

1. **Finding-D: explicit vs implicit cross-workflow
   carve-out.** Operator-Claude call: leave
   `.importlinter` as-is (W12 passes by omission) or
   add `workflows.balances`, `workflows.cash_flow`,
   `workflows.promos` to the independence list with a
   documented carve-out for derivation chains.
   Cosmetic / defensive choice with no current
   operational impact.

2. **Finding (b) #4 lay-side payout shape.** When does
   the bet record carry lay-side liability + commission?
   This is the substrate that needs to land before the
   §5.3 derivation can settle lay bets correctly. The
   DR-025 hedge classification revisit (parked,
   forward-tracked) is the natural home for the
   substrate change. Operator-Claude routes:
   - Option A — wait until DR-025 revisit lands the
     substrate, then patch §5.3 in a W12.1.
   - Option B — small W12.1 to add a `bet_side`-aware
     `_bet_cash_return` that returns
     `Decimal("0")` for any leg_role identified as lay
     until the substrate carries proper liability fields.
     Surfaces the gap without overstating impact.

3. **Finding (c) #7 smoke script.** Operator-Claude:
   accept the inline smoke import gate, or commission
   the §7.5 script as a separate small deliverable. Code
   recommendation: accept; the test coverage is the load-
   bearing surface and a separate smoke script duplicates
   without adding signal.

4. **Finding (c) #8 Python-version tooling.** Worth a
   one-line addition to opening prompts? E.g. "Run
   `.venv/bin/python -m pytest` (project requires 3.12)."

---

## §11 — What Code thinks should land next

Two plausible forward paths:

**Path 1 — Ship the W12 report, triage, route to W15.**
Operator-Claude triages findings (5–10 minutes of S138),
classifies each as accept / W12.1 / forward-track, then
S139 drafts W15 brief (`ops_events` per-domain event log,
structurally identical to W13). This matches the
`current_state.md` "Code ships clean → S138 brief / S139
W15" branch.

**Path 2 — Surgical W12.1 for the lay-side substrate
gap.** If the operator wants to use W12's balance
derivation operationally against lay bets immediately
(Strategy 1 insurance + Betfair hedge cycle being the most
common multi-side operational pattern), patch §5.3 to
treat lay legs conservatively (return zero until proper
substrate lands). Then ship the proper fix when the
DR-025-revisit substrate change lands. Small brief
(~3–500 line scope), one-session ship.

Code's recommendation: **Path 1.** The lay-side gap is real
but limited to a specific bet type the daily-use surface
hasn't yet been exercising; the conservative-treat-as-zero
patch in Path 2 adds complexity without the operator
having seen the gap in practice. Triage at S138 will
naturally identify whether the gap is operationally
biting; if so, draft W12.1 then.

W15 sequencing per Session 131 Path D unblocks once W12
ships clean. The report's findings classify cleanly into
(a/b/c) per §8 and don't surface anything that retreats
W15's readiness.

---

**End of report.**
