# Close the account-reference format class — SURGICAL FIX report

**Session:** single bounded Claude Code session, 2026-06-25 ACST.
Start ~08:55 ACST, close ~09:11 ACST.
**Brief:** `interface_triage/account_ref_format_class_fix_brief.md` (LOCKED
S186). **Surface:** `account_ref_surface_review_report.md` (the anchor).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
(HEAD `2329604`, unchanged at close).
**Mode:** READ-WRITE, limited to the §5 named anchors.

---

## Outcome (read first)

The account-reference format-mismatch class is **closed**. The three refs
(`account_id` · `book_id` · `account_at_book_id`) are now typed `str` and
passed through as operational hex verbatim at every reviewed anchor across
the three modules (cash_flow, balance_derivation, racing). The F2-seeded
dashed cross-domain test fixtures are flipped to hex, and three mandatory
FK-on regression guards are in place.

**Success signal met:** the ~10 known F-A read-path test failures are
**green**; the three guards **pass**; the full suite is **1184 passed, 0
failed**; `settlement.py` is **byte-identical**; HEAD and the dirty list
are **unchanged** (all edits land in already-untracked source dirs; no
tracked baseline file touched).

No escalation fired (the §5.0 baseline gate passed clean). No follow-up
brief drafted.

---

## Baseline (§5.0 gate)

| Check | Required | Start | Close |
|---|---|---|---|
| HEAD | `2329604aa8…` | `2329604aa8…` | **`2329604aa8…`** |
| Dirty count (`git status --porcelain \| wc -l`) | 69 | 69 | **69** |
| `settlement.py` SHA-256 | `9e07a75d…40d4a3` | `9e07a75d…40d4a3` | **`9e07a75d…40d4a3`** |
| `racing.py:714` | `account_at_book_id: UUID` | matched | (now `str`) |
| `balance_derivation.py:147` | `(str(account_at_book_id),)` | matched | (param now `str`) |
| `cash_flow_store_adapter.py:344` | `account_id=str(event.account_id)…` | matched | (now passthrough) |

**Gate result: PASS** — no drift. Proceeded.

---

## §A — Changes applied (production)

Uniform treatment per the proven F2 pattern: retype `UUID → str`, drop the
`UUID(...)` read-wrap and the `str(...)` write-wrap, pass operational hex
through verbatim. Spine-owned UUIDs left untouched (see §E).

### C1 — cash_flow

**`domain/cash_flow/__init__.py`** (`CashFlowEventBase`)
| Line | Before → After |
|---|---|
| 409 | `account_id: UUID \| None` → `str \| None` |
| 410 | `book_id: UUID \| None` → `str \| None` |
| 411 | `account_at_book_id: UUID \| None` → `str \| None` |
| 405/412/413/416 | `event_id` / `parent_event_id` / `supersedes_event_id` / `correlation_id` — **left `UUID`** |

**`workflows/cash_flow/v1/cash_flow_store_adapter.py`**
| Line | Before → After |
|---|---|
| 119 | `list_by_account_at_book(account_at_book_id: UUID)` → `str` |
| 136 | `list_by_account(account_id: UUID)` → `str` |
| 153 | `list_by_book(book_id: UUID)` → `str` |
| 195–197 | `latest_non_superseded_by_scope(...)` three refs `UUID \| None` → `str \| None` |
| 312–316 | READ `_row_to_event`: dropped `UUID(row.account_id/book_id/account_at_book_id)` → pass row text through (3 fields collapse to direct passthrough) |
| 344–348 | WRITE `_event_to_row`: dropped `str(event.account_id/book_id/account_at_book_id)` → pass through (the latent F2-class write bug) |
| 182 (`list_by_correlation_id`), 308/319–326/330 (read), 340/352/357/364 (write) | spine-owned ids — **left `UUID`/`str()` as-is** |

**`store/repositories/cash_flow.py`** — **NO change** (the `str()` query
sinks at 224/241/258/336–342 are format-agnostic; they correctly
stringify the hex they now receive). Per §5.1/§9.

### C2 — balance_derivation (`workflows/balances/v1/balance_derivation.py`)

| Line | Before → After |
|---|---|
| 48 | removed now-unused `from uuid import UUID` (consequent to the retype — no remaining `UUID` use in the file; keeps the anchor lint-clean) |
| 112 | `AccountAtBookBalance.account_at_book_id: UUID` → `str` |
| 128 | `_read_bet_rows_for_account_at_book(... account_at_book_id: UUID)` → `str` (the `str()` wrap at 147 left as harmless `str(str)`) |
| 392 | `compute_account_at_book_balance(account_at_book_id: UUID)` → `str` (the hub) |
| 496–497 | `_list_account_at_book_ids_for_holder(account_id: UUID) -> list[UUID]` → `str` / `list[str]` |
| 512 | dropped `UUID(row[0])` re-wrap → `row[0]` (return hex TEXT directly) |
| 517 | `compute_account_holder_cash_holding(account_id: UUID)` → `str` |
| 481 | `AccountHolderCashHolding.account_holder_id: UUID` → `str` |
| 580 | `BookNetFlow.book_id: UUID` → `str` |
| 589 | `AccountNetFlow.account_id: UUID` → `str` |
| 656 | `by_account: dict[UUID, …]` → `dict[str, …]` |
| 431/535 (sinks) | fixed transitively by the param retypes — no separate edit |

### C3 — racing (`ui/api/routers/racing.py`)

| Line | Before → After |
|---|---|
| 714 | `get_log_context(account_at_book_id: UUID)` query param → `str` (**makes the pool display** — frontend sends hex verbatim, review §C) |
| 399 | `LogContextResponse.account_at_book_id: UUID` → `str` (response now hex) |
| 381/386–387/492/833/884 | `credit_event_id` / `source_promo_instance_id` / `source_template_id` / `consumed_credit_event_ids` / idempotency `uuid5`/`UUID(...)` — **left `UUID`** (spine-owned / bet-id); `LogBetRequest.account_at_book_id` (484) already `str` |

---

## §B — Test-seed migration (the coupling consequence)

**How found.** Grepped the test tree for dashed-UUID account-ref seeds
(`rg 'str\(UUID\(' tests`) and for UUID-object ref construction
(`rg '(account_id|book_id|account_at_book_id)\s*=\s*UUID\(' tests`) and
for callers of the retyped functions. This surfaced **three** modules
needing migration (the review named two; the third — the cash_flow adapter
test — seeds the refs as UUID *objects* and breaks directly on the retype).

**Final list (all flipped to operational hex; fixed logical ids preserved
for determinism via `.hex` on the existing fixed UUIDs):**

| File | Sites | Change |
|---|---|---|
| `tests/workflows/balances/v1/test_balance_derivation.py` | 67–73 (7 consts) | `str(UUID("…"))` → `UUID("…").hex`; F2 comment updated to the closed-class state. `PAYEE_ID` left `UUID` (spine-owned). |
| `tests/workflows/balances/v1/test_balance_lay_branch.py` | 57–59 (3 consts) | `str(UUID("…"))` → `UUID("…").hex`; comment updated. |
| `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py` | 64–66 (`SEED_*`) | `UUID("…")` → `UUID("…").hex`; the `str(SEED_*)` DB-seed wraps become harmless no-ops. |

**Decision on `tests/ui/api/test_racing.py` (NOT flipped).** It seeds the
three refs as `UUID` objects rendered dashed via `str()`/f-string. After
the route became `str`-passthrough its tests pass as-is (internally
consistent). Per §5.4's precise scope — "any other **cross-domain
balance/cash_flow** test carrying a dashed account-ref seed" — test_racing
is an API test that writes **no** cash_flow events and cannot re-create
the cash_flow mismatch, so it is **outside** the §5.4 mandate. Flipping
its module consts + helper annotations would exceed the brief (§9 no
drift). Instead, the hex `/log-context` path is pinned explicitly by guard
(b) below, which uses its own `uuid4().hex` seeds. **Observation (not
chased):** test_racing still validates the dashed shape; a future cleanup
could align its seeds to hex — flagged, not in scope here.

---

## §C — Regression guards (the §5.5 mandatory anti-recurrence lever)

All three run with `foreign_keys = ON` against real operational-hex seeds.

| Guard | Location | What it pins | Result |
|---|---|---|---|
| **(a)** cash_flow write | `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py::test_account_ref_format_class_cash_flow_write_holds_fk_and_stores_hex` | A cash_flow write under FK-on against a hex `accounts_at_book` PK **succeeds** and stores the three refs **verbatim dashless hex**; round-trips as `str`; a **dashed** ref **fails** the FK (`CashFlowEventError`) — the bug demonstrated dead. | **PASS** |
| **(b)** racing `/log-context` | `tests/ui/api/test_racing.py::test_account_ref_format_class_log_context_nonempty_for_hex_account` | `/log-context` returns a **non-empty** pool (`fb_count==1`, `free_bet_balance==50.00`) for a `uuid4().hex` account-at-book; the ref round-trips verbatim. | **PASS** |
| **(c)** conversion hinge | `tests/workflows/balances/v1/test_balance_derivation.py::test_account_ref_format_class_credited_free_bet_visible_for_hex_account` | A free-bet credit recorded against a hex account-at-book is **surfaced** by `compute_account_at_book_balance` (`free_bet_count==1`, `free_bet_balance==50`) — the operator's "mark triggered → see the credited free bet" path. | **PASS** |

---

## §D — Pre/post verification

**Pre (captured this session, the F-A battery):**
`uv run pytest` on the balance / cash_flow / racing / composition-root
modules → **10 failed, 100 passed**. The 10:
- `test_balance_derivation` ×7 (`test_holding_*` ×6 + `test_netflow_per_account_breakdown`)
- `test_racing` ×2 (incl. `test_get_log_context_returns_empty_inventory_and_zero_balance`)
- `test_composition_root` ×1 (`test_seven_racing_routes_respond_under_mock_mode`)

Root error captured: `FreeBetInventory.account_at_book_id Input should be a
valid string, input_value=UUID(...)` — the now-`str` promo anchor (F2)
rejecting the UUID its callers passed. `/log-context` against a hex account
did not return a usable pool (the F-A symptom: the route coerced the ref to
`UUID` → dashed downstream).

**Post:**
- Same battery → **110 passed** (all 10 F-A failures green).
- `/log-context` for a hex account-at-book → **non-empty** (guard (b): `fb_count==1`, `free_bet_balance==50.00`).
- Three §5.5 guards → **pass**.
- **Full suite `uv run pytest` → 1184 passed, 0 failed** (pre full-suite per F2 report: 1171 passed + 10 F-A failed; +3 new guards = 1184).
- `settlement.py` SHA-256 → **`9e07a75d…40d4a3` byte-identical**.
- `git status` → **69 entries, unchanged**; HEAD unchanged; no git state-changing op.

---

## §E — What was NOT touched

- **Spine-owned UUIDs — stay UUID** (verified retained): `event_id`,
  `parent_event_id`, `supersedes_event_id`, `correlation_id` (cash_flow);
  `promo_id`, `promo_template_id`, `credit_event_id`,
  `source_promo_instance_id`, `source_template_id`,
  `consumed_credit_event_ids`, idempotency `uuid5`/`UUID(...)` (racing).
  `PAYEE_ID` (balance test) left `UUID`.
- **`settlement.py`** — no contact; SHA byte-identical. No contact with
  `apply_manual_operator_resolution` or the `provisional.py` settlement path.
- **Schema** — no DDL; every PK/FK column was already `TEXT`; hex stored
  verbatim.
- **`store/repositories/cash_flow.py`** — no change (format-agnostic `str()`
  sinks, correct as-is).
- **Promo spine (F2) / operational store** — not re-litigated.
- **Tracked baseline files** — none touched (`.importlinter`, `clients/*`,
  `domain/bets/__init__.py`, `pyproject.toml`, `store/__init__.py`,
  `tests/conftest.py`, `uv.lock` remain the pre-existing `M` set).
- **No git state-changing op** (no add/commit/stash/restore/checkout/reset).

---

## Self-assessment

- **Coverage:** Every §5 anchor applied (C1/C2/C3), the seed flip executed
  as one coupled unit with the cash_flow + balance retypes (no cross-domain
  test ran between them), all three FK-on guards added. The empirical seed
  grep surfaced a third migration site (cash_flow adapter test) beyond the
  two the review named — exactly the "there may be more" the brief
  anticipated.
- **Confidence:** HIGH. The fix is the proven F2 pattern; the 10 F-A
  failures flip to green deterministically, the guards prove the three live
  paths (cash_flow write, `/log-context` display, conversion hinge) against
  real hex under FK-on, and the full suite is clean at 1184.
- **Lint:** my four production files and the three migrated test modules are
  ruff-clean for what I touched (including the consequent `UUID` import
  removal in balance_derivation — no F401). The 37 pre-existing ruff errors
  in `racing.py` / one import in `test_balance_lay_branch.py` are in the
  uncommitted substrate and were **not** introduced by this change; fixing
  them would be drift, so they were left.
- **One in-scope deviation from the literal anchor list, flagged:** removed
  `balance_derivation.py:48` (`from uuid import UUID`), which §5.2 did not
  enumerate — it became dead as a direct consequence of the sanctioned
  retype and is within the named-anchor file. Documented here for the
  record.
- **Honest scope call:** `test_racing.py` seeds left dashed (outside §5.4's
  cross-domain mandate; tests pass via str-passthrough; the hex path is
  covered by guard (b)). Noted as a benign future-cleanup observation, not
  chased.
- **Repo integrity:** HEAD unchanged; dirty list 69 unchanged; settlement
  byte-identical; no schema/DB/persisted-data change; no git state-changing
  op. Adelaide timestamps throughout.

### Routes to the operator-Claude triage (per brief §10)
The class is closed: failing→passing battery green, three FK-on guards in
place, settlement byte-identical, dirty list clean except the named-anchor
(untracked-substrate) files. Forward to the pre-cutover live-validation
sweep and W16 cutover scoping. The shared canonical account-ref type stays
parked (post-cutover hardening, DR-030). No next brief drafted here.

*End of report. READ-WRITE session, 2026-06-25 ~09:11 ACST.*
