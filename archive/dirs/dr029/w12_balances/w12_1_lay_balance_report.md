# W12.1 — Lay-balance fix (Code report)

**Brief:** `dr029/w12_balances/w12_1_lay_balance_brief.md` (Session 140, locked).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/`.
**Session timestamp:** 2026-06-10, Adelaide local.
**Pre-reads consulted:** brief; `workflows/balances/v1/balance_derivation.py`;
`store/schema/bets.py`; `domain/bets/__init__.py`. Reference-only pre-reads
(`store/repositories/bets.py`, `workflows/bet_entry/v1/record_builder.py`,
`workflows/bet_entry/v1/staking.py`) consulted on demand. The boundary
adapter `workflows/bet_entry/v1/bet_store_adapter.py` was also touched —
see Findings §1 below.

---

## §1 — Summary

W12.1 lands the locked Betfair lay substrate (`side` + `commission` on
the bet record) and the read-side lay branch in the balance derivation
per brief §5.1–§5.6. Liability is derived on read per DR-019
(`L = matched_stake × (matched_price − 1)`); commission population
remains a separate next brief — `commission` stays `None` at write time
and the read path applies an 8% fallback when NULL.

**Net-effect identities (brief §5.5, confirmed by §5.6 tests):**

- Lay win:  `−L + (L + S × (1 − c))` = `+ S × (1 − c)`
- Lay loss: `−L + 0` = `− L`
- Lay void: `−L + L` = `0`

**Suite status:**

- Balances workstream tests: **26 → 39 collected; 38 passed, 1
  pre-existing failure** (delta `+13` new lay-branch tests, all green;
  the single failure is `test_balance_free_bet_inventory_surfaces` and
  pre-dates W12.1).
- Full repo suite: **822 collected, 820 passed, 2 failed**. Both
  failures (`test_balance_free_bet_inventory_surfaces`,
  `test_inventory_single_freebie_available`) pre-date W12.1 and concern
  `compute_free_bet_inventory` (an untouched module).

**Headline:** the lay branch is functionally correct; the §7 cross-check
against the domain authority matches.

---

## §2 — Per-anchor outcome

### §5.1 — Schema (`store/schema/bets.py`)

Added two nullable columns to `_BETS_DDL` and two
`_add_column_if_missing` calls in `apply_migrations`, both tagged
`W12.1`, placed after the W9 call as the brief named:

```sql
side       TEXT   -- W12.1 — 'BACK'/'LAY'; NULL = back
commission REAL   -- W12.1 — Betfair commission rate; NULL → 8% fallback on read
```

No other column, index, or table touched.

### §5.2 — Domain (`domain/bets/__init__.py`)

Added two backward-compatible optional fields to `BetRecord`,
defaulting to `None`:

```python
side: BetSideTag | None = None
commission: float | None = None
```

`BetSideTag` and `Construction` were already present at L149–L173 (W139
substrate lock); imports unchanged.

### §5.3 — Repository (`store/repositories/bets.py`)

Added two fields to the `BetRow` dataclass (str + float, both
defaulting to `None`). Extended `write_bet_record`'s `INSERT INTO bets`
to include the `side, commission` columns and bound parameters
(`row.side`, `row.commission`). Extended `_row_to_bet_row` to map both
columns back onto the dataclass.

The brief's `row.side.value if row.side is not None else None`
construction actually belongs at the `BetRecord ↔ BetRow` adapter
boundary (`workflows/bet_entry/v1/bet_store_adapter.py`), since the
repository works against the primitive `BetRow`. Adapter pass-through
recorded as Finding §1 below.

### §5.4 — Bet entry (`workflows/bet_entry/v1/record_builder.py`)

Added an optional `construction: Construction | None = None` field to
`HedgeRecordInputs` (inside the named anchor, backward-compatible).
`build_hedge_bet_record` now derives `side` from this input:

- `Construction.LAY_AGAINST_BACK`  → `BetSideTag.LAY`
- `Construction.BACK_AGAINST_BACK` → `BetSideTag.BACK`
- `None` (today's orchestrator) → `None` (read as BACK on the balance
  side — preserves existing behaviour)

`commission` stays `None` at write time per brief §9.

Soft-book builder (`build_soft_book_bet_record`) untouched — the
soft-book leg's `side` remains the default `None` (read as BACK), per
math review §1.

Orchestrator-side plumbing required to populate `construction` is
recorded as Finding §2.

### §5.5 — Balances (`workflows/balances/v1/balance_derivation.py`)

Four edits, dependency-ordered as named:

**(a) `_read_bet_rows_for_account_at_book`** — added `side, commission`
to the SELECT column list. No other change to the query.

**(b) `_bet_cash_return`** — added a lay branch ahead of the existing
back-bet logic. Lay branch:

- `is_free_bet=True` + `side=LAY` → conservative `0` + finding (guard
  #2).
- `settled_won` → `L + S × (1 − c)` (with `c = 0.08` fallback when
  `commission` NULL).
- `settled_lost` → `0`.
- `voided` → `L`.
- pending / provisional / None → `0`.

`Decimal(str(commission))` matches the existing `matched_price`
handling.

**(c) `_bet_cash_stake_committed`** — added a lay branch returning
`L` (cash committed at placement = liability for a lay). Back-bet and
free-bet branches unchanged.

**(d) `_bet_pending_cash_stake`** — added a lay branch returning `L`
for any lay row in a pending state. Back-bet branch unchanged.

The `compute_account_at_book_balance` loop is **unchanged**; the
committed/return split makes the net come out right without
double-counting.

Three small private helpers were added alongside the existing
`_bet_cash_return` / `_bet_cash_stake_committed` /
`_bet_pending_cash_stake` family: `_is_lay(row)`, `_lay_liability(row)`,
and a module-level `_DEFAULT_COMMISSION = Decimal("0.08")` constant.
These are new code for the lay branch (not a refactor of existing
code); each lay-branch site references them rather than triplicating
the liability formula.

### §5.6 — Tests (`tests/workflows/balances/v1/test_balance_lay_branch.py`)

New file, 13 tests, all green:

| Test | Asserts |
| --- | --- |
| `test_lay_win_credits_stake_net_of_commission` | Lay $10 @ 3.0, c=0.08 → cash 100 → 109.20 (`+S(1−c)`). |
| `test_lay_loss_subtracts_liability` | Lay $10 @ 3.0 settled_lost → 100 → 80 (`−L = −20`). |
| `test_lay_void_zero_net_effect` | Lay $10 @ 3.0 voided → 100 → 100 (net 0). |
| `test_lay_pending_reserves_liability_not_stake` | Pending lay: cash drops by L, `pending_bet_stake_total == L`, count=1. |
| `test_lay_win_commission_zero_eight` | Explicit c=0.08 reproduces the worked example. |
| `test_lay_win_commission_zero_four` | Lay $20 @ 4.0, c=0.04 → +19.20 net. |
| `test_lay_win_null_commission_falls_back_to_eight_percent` | NULL commission ⇒ 8% fallback. |
| `test_null_side_back_settled_won_unchanged` | **NULL-side regression guard.** Back $50 @ 2.5 settled_won → 200 → 275. |
| `test_explicit_back_side_settled_won_matches_null_side` | `side='BACK'` and `side=NULL` yield identical balances. |
| `test_free_bet_lay_contradiction_no_cash_effect` | Free-bet + lay (contradiction) → 0 cash effect; no lay maths applied. |
| `test_schema_round_trip_lay_side_and_commission` | BetRecord(side=LAY, commission=0.05) round-trips intact via repository + adapter. |
| `test_schema_round_trip_null_side_null_commission` | NULL/NULL round-trips intact (backward-compat). |
| `test_apply_migrations_is_idempotent` | `apply_migrations` run twice is a clean no-op; columns present. |

---

## §3 — Verification (per brief §7)

**Pre-fix baseline:**

- `grep -nE "side|commission" store/schema/bets.py` returned a single
  docstring match (the word "inside" on L4) — zero functional matches.
- Balances suite: `25 passed, 1 failed` (the FB-inventory failure).

**Post-fix verification:**

- Balances suite: `38 passed, 1 failed` (same single pre-existing
  failure; delta `+13` new tests, all green).
- Full repo suite: `820 passed, 2 failed`. Both failures
  (`test_balance_free_bet_inventory_surfaces`,
  `test_inventory_single_freebie_available`) pre-date W12.1; they
  concern `compute_free_bet_inventory` which W12.1 did not touch.
- Net-effect identities (`+S(1−c)` / `−L` / `0`): confirmed in the four
  named tests.
- NULL-side regression guard: confirmed via
  `test_null_side_back_settled_won_unchanged`
  and `test_explicit_back_side_settled_won_matches_null_side`.
- Schema round-trip (BetRecord → DB → BetRecord): confirmed for both
  `side=LAY` + commission, and NULL/NULL.
- Migration idempotency: confirmed.
- `git status` at close: matches session start. The W12.1 edits sit
  inside the already-untracked W12 build region (per §9; full status
  appended in §6).

---

## §4 — Cross-check (brief §7 — implementation vs `domain/bets` authority)

The brief calls out two checks against the domain / math-review
authority:

1. **Construction A liability formula.** `domain/bets/__init__.py`
   `Construction.LAY_AGAINST_BACK` (Construction A) maps to the math
   review §1 / §3 formula `liability = s_bf × (p_bf − 1)` (also cited
   in brief §3 reference-only pre-read for `staking.py`'s
   `liability = s_bf × (p_bf − 1)` for Construction A).
   Implementation: `_lay_liability(row)` computes
   `Decimal(matched_stake) × (Decimal(str(matched_price)) − 1)` —
   **matches**.

2. **Lay-win net cash identity.** Brief §5.5 states the lay-win net
   cash = `+S × (1 − c)`. Implementation:
   - `_bet_cash_stake_committed` for lay = `L`
   - `_bet_cash_return` for `settled_won` lay = `L + S × (1 − c)`
   - Loop computes `cash += return − committed = +S × (1 − c)` —
     **matches**.

The void and loss identities are derived from the same committed /
return split and likewise match.

**Result: implementation matches the domain authority.** No mismatch
to triage.

---

## §5 — Findings

### Finding §5.1 — `bet_store_adapter.py` touched outside the §5.3 named anchor

**Files touched:** `workflows/bet_entry/v1/bet_store_adapter.py` —
added `BetSideTag` import (1 line); added `side` / `commission`
pass-through in `to_rows` (3 lines) and `from_rows` (3 lines).

**Why it matters:** `workflows.bet_entry.v1.bet_store_adapter` is the
`domain.bets.BetRecord` ↔ `store.repositories.bets.BetRow` boundary
(W10 lift). The §5.3 named anchor (`store/repositories/bets.py`) works
against primitive `BetRow`; the field translation
(`record.side.value if record.side is not None else None`) belongs at
the adapter, not the repository. Without these pass-through lines:

- The §5.4 `BetRecord.side` populated by `build_hedge_bet_record` never
  reaches the `BetRow.side` field, so the DB column always stays NULL.
- The §5.6 schema round-trip test (`persist a BetRecord with
  side=LAY ... read it back via the repository`) cannot succeed
  end-to-end.

**Recommendation for operator-Claude triage:** treat the adapter
pass-through as either (a) absorbed into §5.3 scope post-hoc (since
the brief's own §5.6 demands the end-to-end round-trip), or (b) split
out as a one-line W12.2 follow-up. The edit is minimal (`record.side.value
if record.side is not None else None`, plus the symmetric `BetSideTag(row.side)`
on read) and additive.

### Finding §5.2 — `construction` not plumbed through the orchestrator (§5.4 deferral)

**File touched:** `workflows/bet_entry/v1/record_builder.py` — added
`construction: Construction | None = None` to `HedgeRecordInputs` (a
new optional field, backward-compatible).

**Why it matters:** the brief §5.4 explicitly anticipated this: "If
the construction is not cleanly available at the construction site
without reaching outside the named anchor, stop, leave `side`
defaulting to `None`, and record this as a finding — do not thread
new plumbing through other modules to obtain it."

The caller of `build_hedge_bet_record` is
`workflows/bet_entry/v1/orchestrator.py` (NOT in named scope). The
orchestrator does not currently pass `construction` into
`HedgeRecordInputs`; consequently `inputs.construction is None`,
`side` defaults to `None`, and the balance derivation reads it as
BACK. **Today's behaviour is preserved exactly** for all
newly-written hedge records until orchestrator-side plumbing lands.

**Recommendation:** a small follow-up brief (W12.2 candidate) to wire
`orchestrator.py` so it forwards the `Construction` already produced
by the staking calculator (`workflows/bet_entry/v1/staking.py` resolves
this) into `HedgeRecordInputs.construction`. The W12.1 substrate is
ready to accept it — no further `record_builder` change needed.

### Finding §5.3 — `is_free_bet` + `side=LAY` guard implemented; no row encountered in tests

The brief §5.5 guard #2 ("cannot lay with a free bet") is implemented
in `_bet_cash_return` as a conservative-zero short-circuit ahead of
any lay maths. No production-shaped row exercises this case; the unit
test `test_free_bet_lay_contradiction_no_cash_effect` confirms the
short-circuit behaviour. No further action needed.

### Finding §5.4 — `settlement_state` perspective confirmed as the bet's own

The brief §5.5 guard #1 asked Code to confirm whether `settled_won`
records the lay bet's own perspective or the backed selection's
perspective. **Confirmation:** the existing back-bet logic in
`_bet_cash_return` interprets `settled_won` as the **bet's own**
perspective (it returns `matched_stake × matched_price`, which is the
back bet winning). The new lay branch reuses the same interpretation
(`settled_won` = the lay bet itself won, i.e. the backed selection
lost). Sign-inversion would be required only if the settlement worker
recorded from the backed-selection's perspective, which it does not.
No further action needed.

### Finding §5.5 — Two pre-existing test failures (not introduced by W12.1)

`test_balance_free_bet_inventory_surfaces` and
`test_inventory_single_freebie_available` both failed in the pre-fix
baseline and continue to fail post-fix. They concern
`compute_free_bet_inventory` (in `workflows/promos/v1/`), which W12.1
did not touch. Recorded for operator-Claude awareness; the wiring
issue is upstream of W12.1.

### Finding §5.6 — Self-assessment

Work fit one bounded session comfortably. Each anchor landed cleanly
on the first edit pass; the two surfaces requiring extension beyond
the strictly-named scope (`bet_store_adapter` pass-through and
`HedgeRecordInputs.construction` field) are both small, additive, and
match the brief's anticipated "boundary, finding, no silent
expansion" pattern. No anchor ran larger than expected. Report
length is within the brief's 150–350-line target.

---

## §6 — Final `git status`

```
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
?? domain/promos/
?? scripts/
?? store/repositories/accounts.py
?? store/repositories/bets.py
?? store/repositories/cash_flow.py
?? store/repositories/promos.py
?? store/schema/accounts.py
?? store/schema/bets.py
?? store/schema/cash_flow.py
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
?? workflows/promos/
```

The post-session `git status` is **byte-identical** to the session-start
state — the W12.1 edits land entirely inside the already-untracked W12
build region (and the already-modified `domain/bets/__init__.py`),
exactly as the brief §9 anticipated. No `git add`, `commit`, `stash`,
`restore`, `checkout`, or `reset` was issued at any point during the
session.

**End of report.**
