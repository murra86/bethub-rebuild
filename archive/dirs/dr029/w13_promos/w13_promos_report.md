# W13 report — Promos / free-bet inventory event log + reference data

**Session anchor (open):** 2026-05-13 08:51:08 +0930 ACST
**Session anchor (close):** 2026-05-13 09:09:55 +0930 ACST
**Brief:** `dr029/w13_promos/w13_promos_brief.md`
**Executor:** Claude Code (single bounded session)

---

## 1 — Pre-amble

**W13 shipped clean.** All four schema tables (`promo_events`,
`promo_template`, `promo`, `warning_catalogue`), 10 indexes, four
row-only repository classes, Pydantic-side discriminated-union event
shapes with FK-nullability and cross-field validators, adapter with
payload-reference validation, and three test files all landed. 129
new tests pass on top of the 624 W14.1-close baseline (753 total).
All five DR-030 contracts kept; mypy and ruff clean on the new code.
End-to-end §7.4 smoke script reports OK through all nine event types
plus reference data CRUD, supersession reads, and payload reference
validation.

Dirty-tree discipline held: HEAD unchanged, no state-mutating git
commands run, only the four named W13 anchors added as new untracked
entries and `store/__init__.py` modified additively.

---

## 2 — Pre-build alignment findings

**7/7 passed; brief assumptions hold against shipped substrate.**

The seven §6.1 checks against W14.1 / W11 / burst_review substrate:

1. **W14.1 adapter shape** — `workflows/cash_flow/v1/cash_flow_store_adapter.py`
   (396 lines) has the class taking `sqlite3.Connection`, public
   Pydantic-typed methods, module-level `_row_to_event` / `_event_to_row`
   / `_row_to_payee` / `_payee_to_row` helpers, `typing.cast` workaround
   at the dispatch parse. Pattern reproduced verbatim for W13.
2. **W14.1 row-only repository** — `store/repositories/cash_flow.py`
   (601 lines) ships row-only with `object`-typed surface and
   `_event_type_value` enum-vs-string helper. No `domain.cash_flow`
   imports. W13's `store/repositories/promos.py` mirrors this exactly
   (and lint-imports confirms 0 `from domain` matches).
3. **W14 domain layer** — `domain/cash_flow/__init__.py` (526 lines)
   has closed enums, `_PayloadBase`, eight `_Payload` subclasses with
   `event_type_payload: Literal[...]` discriminator,
   `_FK_REQUIRED_BY_EVENT_TYPE` + `_check_fk_rules` validator,
   `PAYLOAD_BY_EVENT_TYPE` dispatch. W13 ships the analogue with
   nine event types plus three reference data models.
4. **W14 schema module** — `store/schema/cash_flow.py` (212 lines)
   has DDL constants, indexes, `_add_column_if_missing` helper,
   `apply_migrations(conn)` function. W13's `store/schema/promos.py`
   (282 lines) follows the same shape across four tables + 10 indexes.
5. **W11 tables FK-ready** — `store/schema/accounts.py` defines
   `accounts.account_id`, `books.book_id`,
   `accounts_at_book.account_at_book_id` as PKs. W13's FOREIGN KEY
   declarations on `promo_events` and `promo` point at these
   correctly.
6. **`workflows/burst_review/` is empty** — only the 0-byte
   `__init__.py` present. W13 ships the WRITE surface for cascade
   payload fields (`cascaded_from_bet_id`, `cascaded_at_settlement_state`,
   `cascade_path`) on `FreeBetCreditedPayload` and
   `PromoCashCreditedPayload` so the future burst-review build can
   write cascade-induced credit events without further surgery.
7. **CHECK constraint pattern** — multi-line
   `CHECK (event_type IN ('...', '...'))` syntax confirmed in W14's
   shipped DDL. W13 reproduces the same syntax across five CHECK
   constraints (event_type, source, kind, status, severity).

**Judgement-extension notes (non-halting, surfaced for transparency):**

- **§4 vs §7.3 prose tension on `store/__init__.py` additions.** §4
  prose says "add `Promo*Repository` class names plus error classes".
  §7.3's binding grep check validates only the 4 repository class
  names. The shipped W14 precedent in `store/__init__.py` (42 lines
  pre-W13) re-exported only the 2 repository classes
  (`CashFlowEventRepository`, `PayeeRepository`), not the error
  classes. I followed the W14 precedent for W13 (4 repository class
  re-exports only; error classes remain accessible via
  `store.repositories.promos` direct imports as the test files do).
  The §7.3 grep check returns 8 matches — 4 in the import block + 4
  in `__all__` — both reflecting the same 4 repository classes the
  acceptance test names. Operator-Claude can revise the call in S131
  triage if a different shape is preferred.
- **`warning_type_id` example-vs-type ambiguity.** §5.1.7 of the
  brief shows slug-style example values (`'rapid_turnover'` etc.)
  for `warning_catalogue.warning_type_id` while §5.2.4 / §5.2.8 type
  the Pydantic field as `UUID`. Read the slug examples as
  illustrative of the *operational kind* (per the `(e.g. ...)`
  framing) and the Pydantic type as binding. The SQL column is TEXT
  and accepts either shape; the adapter formats UUIDs via
  `str(uuid)` like every other reference table. Operator seed data
  for `warning_catalogue` should use UUIDs alongside the
  human-readable `label` field where the slug semantics live
  (e.g. `label="Rapid turnover spike"`).

---

## 3 — What Code did

Sequence executed per §6.2 build order, with §6.1 alignment
preceding the build:

1. **Session-open timestamp + pre-baselines (§7.1).** Captured Adelaide-
   local 2026-05-13 08:51:08, git status snapshot (10 modified, 23
   untracked entries — substantial pre-existing dirty tree per §9.7),
   `wc -l` on `store/__init__.py` (42 lines). Confirmed
   `domain/promos`, `store/schema/promos.py`, `store/repositories/promos.py`,
   `workflows/promos/`, `tests/workflows/promos/` did not exist.
   Pre-baseline pytest: 624 passed; lint-imports: 5 kept / 0 broken.

2. **§6.1 alignment check.** Read the four shipped W14 substrate files
   end-to-end, confirmed structural shape. Read W11 `accounts.py` and
   `store/__init__.py` for FK targets and edit pattern. Spot-checked
   the W14 CHECK constraint syntax. Confirmed `workflows/burst_review/`
   empty. All 7 checks green plus two non-halting judgement notes
   (§4 vs §7.3 prose, `warning_type_id` shape) logged here.

3. **Package marker writes (§6.2 step 2).** Created `workflows/promos/`,
   `workflows/promos/v1/`, `tests/workflows/promos/`,
   `tests/workflows/promos/v1/` with one-line or empty `__init__.py`
   files. Read-back confirmed all four landed at the real Mac paths.

4. **`store/schema/promos.py` (§6.2 step 3).** Wrote the 282-line
   DDL module covering four tables in FK-dependency order
   (`warning_catalogue` → `promo_template` → `promo` → `promo_events`),
   10 indexes, five CHECK constraints, all FK declarations, the
   `_add_column_if_missing` helper for future additive use, and the
   `apply_migrations(conn)` public surface. Smoke-tested in isolation
   via a temp-file SQLite — confirmed all four tables and all 10
   indexes created, idempotent on re-run.

5. **`domain/promos/__init__.py` (§6.2 step 4).** Wrote the 837-line
   Pydantic module: twelve closed enums (`PromoEventType` with nine
   values plus `PromoEventSource`, `PromoTemplateKind`, `PromoStatus`,
   `WarningSeverity`, `PromoObservationScope`, `FreeBetCreditSource`,
   `CreditStatus`, `RevocationReason`, `ExpiryReason`, `CascadePath`,
   `JourneyAnnotationConfidence`), `_ensure_adelaide_local` Adelaide-
   tz validator (DR-021), `_PayloadBase`, nine payload subclasses
   with cross-field validators (triggered/freebie pair, cascade
   all-or-nothing, draw-down sum-matches), `PromoEventBase` with
   `_check_event_type_matches_payload` + `_check_fk_rules` validators
   driven by `_FK_REQUIRED_BY_EVENT_TYPE` / `_FK_FORBIDDEN_BY_EVENT_TYPE`
   tables, `PAYLOAD_BY_EVENT_TYPE` dispatch, and three reference data
   models (`PromoTemplate`, `Promo`, `WarningCatalogueEntry`).
   Smoke-tested via `python3 -c` that the discriminated union
   constructs cleanly through to the dispatch table.

6. **`store/repositories/promos.py` (§6.2 step 5).** Wrote the
   1012-line row-only repository module: four `@dataclass(frozen=True)`
   row classes (`PromoEventRow`, `PromoTemplateRow`, `PromoRow`,
   `WarningCatalogueRow`), nine module-level exception types in two
   hierarchies (`PromoEventError` + four subclasses; `PromoReferenceError`
   + two subclasses), the four repository classes with `object`-typed
   surface and CRUD methods, `_promo_event_type_value` and
   `_scalar_value` helpers, and the four `_row_to_*_row` helpers.
   Critical: no `domain.promos` imports — only stdlib + `dataclasses`
   + `store.schema.promos.apply_migrations`. **`lint-imports` run
   immediately after this write: 5/5 contracts kept, 0 broken** —
   DR-030 compliance verified on the spot.

7. **`workflows/promos/v1/promo_store_adapter.py` (§6.2 step 6).**
   Wrote the 785-line adapter module. Initial draft had a small
   walrus-operator artefact in the `_validate_payload_references`
   dispatch chain — caught on smoke-test and cleaned up immediately
   (the `FreeBetDeployedPayload` branch isn't needed because
   deployment events carry no adapter-validated payload references
   per W13 brief §5.4.3). Adapter includes the `PromoStoreAdapter`
   class with full event read/write surface and reference data CRUD
   for all three reference tables, `_validate_payload_references`
   helper covering all six adapter-validated payload references,
   `_require_template` / `_require_promo` / `_require_warning_type`
   / `_require_credit_event` per-reference helpers, eight row ↔
   Pydantic translation helpers, and the
   `PromoReferenceValidationError` adapter-layer exception. Imports
   from `domain.promos` and `store.repositories.promos` — direction
   respects DR-030. Smoke-tested with a small Python script that
   confirmed the bogus-template-reference path raises
   `PromoReferenceValidationError` as designed.

8. **`store/__init__.py` additive edit (§6.2 step 7).** Added a
   six-line import block re-exporting `PromoEventRepository`,
   `PromoRepository`, `PromoTemplateRepository`,
   `WarningCatalogueRepository` plus four entries in `__all__` at
   alphabetical positions. 42 → 52 lines (+10 lines). Verified the
   import works via `python3 -c "from store import ..."`.

9. **`tests/store/repositories/test_promos_schema.py` (§6.2 step 8).**
   Wrote the 812-line schema test file with 19 tests: migration
   table/index creation, idempotency, all five CHECK constraints,
   FK enforcement against W11 (account/book/account_at_book paths),
   self-referential FKs on `parent_event_id` / `supersedes_event_id`,
   `promo` FKs against `promo_template` and `books`, and a documentation-
   test confirming that the closed-vocab `warning_type_id` payload
   reference has no SQL FK (adapter-validated only per W13 brief
   §5.4.3). **Ran `pytest tests/store/repositories/test_promos_schema.py`
   immediately: 19 passed.**

10. **`tests/store/repositories/test_promos_repository.py` (§6.2 step 9).**
    Wrote the 799-line repository test file with 43 tests across the
    four repository classes: parametrised round-trip across all nine
    event types (using JSON payload fixtures sized to satisfy
    Pydantic shape on re-validation), append duplicate, get-not-found,
    FK-violation cases on all three header FKs, list reads by every
    scope plus pagination plus event-type filtering plus correlation,
    supersession LEFT JOIN behaviour plus chain walk plus cycle
    detection plus invalid-scope guard, then standard CRUD for each
    reference repository (templates / promos / warning catalogue).
    **Ran pytest immediately: 43 passed.**

11. **`tests/workflows/promos/v1/test_promo_store_adapter.py` (§6.2 step 10).**
    Wrote the 1608-line adapter test file with 67 tests. Two test
    issues surfaced on first run and were resolved cleanly:
    - **`free_bet_deployed` round-trip equality:** the
      `draw_down_breakdown: list[dict[str, object]]` field does not
      preserve UUID / Decimal types across JSON round-trip (dict values
      typed as `object` survive as strings). Resolved by changing
      the round-trip equality assertion to JSON-equivalence
      (`json.loads(fetched.model_dump_json()) ==
      json.loads(event.model_dump_json())`), which is the
      operationally meaningful invariant. The load-bearing
      `type(fetched.payload) is type(event.payload)` assertion still
      holds. Surfaced as finding §6.2 below for operator review.
    - **W11 unique-constraint on `accounts_at_book(account_id, book_id)`:**
      the `account_at_book_mismatch` test wanted to seed a second
      `account_at_book` under the same account+book; W11's UNIQUE
      constraint disallows this. Resolved by seeding a second book
      and a second account_at_book pointing at that book. The test
      now correctly exercises the cross-scope rejection.
    **Ran pytest after both fixes: 67 passed.** Test coverage:
    discriminated-union round-trip per event type (parametrised, 9
    cases), FK-nullability-per-event-type (9 cases), payload cross-
    field validators (triggered/freebie pair, cascade all-or-nothing
    on both credit payloads, drawdown sum + non-empty + positive
    total), Adelaide-tz validation (naive / non-Adelaide / ACDT),
    Pydantic-typed read paths through all six list methods,
    supersession-aware reads + chain walk + cycle, all eight
    adapter-side payload reference validation paths, reference data
    CRUD round-trips for all three reference surfaces.

12. **Full regression + gate suite (§6.2 steps 11 + 12).**
    `pytest tests/`: **753 passed** (W14.1-close baseline 624 + 129
    new W13). lint-imports: **5 kept / 0 broken**. mypy on the new
    code: **Success: no issues found in 6 source files**. ruff: 3
    import-block sort issues caught (I001 only, auto-fixable) — fixed
    via `ruff check --fix`; re-ran pytest after fix: all 129 W13
    tests still pass. ruff clean afterwards.

13. **§7.4 smoke script.** Wrote `/tmp/w13_smoke.py` per §7.4
    structure (tempfile-backed SQLite, W11+W13 migrations, W11
    seed, all three reference data writes, all nine event types
    appended, scoped list reads, supersession write + supersession-
    excluding read + chain walk, bogus-template payload reference
    validation). First run caught an arithmetic miscount in my
    assertions (I overlooked the two prerequisite credit events the
    revoke + expire targets need) — fixed and re-ran: **reports
    "W13 adapter: 9/9 event types round-trip OK; supersession-
    chain walk OK; latest-non-superseded read OK; payload reference
    validation OK."**

14. **Session-close timestamp + post-baselines (§7.2).** Captured
    Adelaide-local 2026-05-13 09:09:55. Git status diff vs pre-baseline
    shows exactly the expected additive shape: `domain/promos/`,
    `store/schema/promos.py`, `store/repositories/promos.py`,
    `workflows/promos/` all new untracked; `store/__init__.py`
    modified. Tests landed inside the already-untracked
    `tests/store/` and `tests/workflows/` trees, so they show up
    under those existing entries. No pre-existing tracked-modified
    or untracked entries were touched — §9.7 dirty-tree discipline
    held.

Deviation from §6.2 order: none of substance. The adapter draft had
one small first-pass cleanup pass (walrus artefact), and ruff caught
import-order corrections after the test files landed. Both were
caught and fixed in the same session within the §6.2 phase
boundaries; no rework outside the named anchors.

---

## 4 — What landed where

Eleven new files plus one edited file. Sizes via `wc -l`:

**New code (4 files):**

| File | Lines |
|---|---:|
| `domain/promos/__init__.py` | 837 |
| `store/schema/promos.py` | 282 |
| `store/repositories/promos.py` | 1012 |
| `workflows/promos/v1/promo_store_adapter.py` | 785 |

**New tests (3 files):**

| File | Lines |
|---|---:|
| `tests/store/repositories/test_promos_schema.py` | 812 |
| `tests/store/repositories/test_promos_repository.py` | 799 |
| `tests/workflows/promos/v1/test_promo_store_adapter.py` | 1608 |

**New package markers (4 files, all empty or one-line):**

- `workflows/promos/__init__.py`
- `workflows/promos/v1/__init__.py`
- `tests/workflows/promos/__init__.py`
- `tests/workflows/promos/v1/__init__.py`

**Edited file (1):**

- `store/__init__.py` — 42 lines → 52 lines (+10 lines, additive only).

**Total net new code surface:** ~2,916 lines across the four
substantive modules.
**Total net new test surface:** ~3,219 lines across the three test
files.
**Sum vs §7.3 ballparks:** Each individual file lands within or
just outside the brief's stated ballparks (`store/repositories/promos.py`
at 1012 is the only one slightly over the §7.3 ceiling of 1000 —
within the spirit of S120 length-bends-to-required-detail since the
four CRUD surfaces consume the extra ~12 lines without redundancy).

---

## 5 — Test results

Three pytest runs:

1. `pytest tests/store/repositories/test_promos_schema.py -v` —
   **19 passed in 0.13s.**
2. `pytest tests/store/repositories/test_promos_repository.py -v` —
   **43 passed in 0.31s.**
3. `pytest tests/workflows/promos/v1/ -v` — **67 passed in 0.42s.**

**Full suite `pytest tests/ -q`: 753 passed in 2.94s.**
(W14.1-close baseline was 624 passed; W13 adds 129 new.)

---

## 6 — Gate results

- **lint-imports:** 151 files analysed, 379 dependencies.
  **5 kept, 0 broken.** All five DR-030 contracts hold:
  - DR-030 layered architecture: KEPT
  - domain imports nothing in the project: KEPT
  - store imports nothing in the project: KEPT
  - contracts is a leaf package: KEPT
  - workflows cannot import workflows: KEPT
- **mypy** on `domain/promos`, `store/schema/promos.py`,
  `store/repositories/promos.py`, `workflows/promos`:
  **Success: no issues found in 6 source files.**
- **ruff** on the four new code files plus the three new test files:
  3 I001 import-sort issues caught, auto-fixed; **clean afterwards.**

---

## 7 — Spot-check result (§7.4)

End-to-end smoke script at `/tmp/w13_smoke.py` ran successfully:

```
W13 adapter: 9/9 event types round-trip OK; supersession-chain walk
OK; latest-non-superseded read OK; payload reference validation OK.
```

The script:

- Opens a tempfile-backed SQLite connection.
- Applies W11 + W13 migrations.
- Seeds W11 account, book, account_at_book.
- Constructs `PromoStoreAdapter` (which constructs all four
  underlying repositories sharing the connection).
- Creates one `PromoTemplate`, one `Promo`, one
  `WarningCatalogueEntry` via the adapter.
- Appends one event per each of the nine event types, including the
  prerequisite credit events for `free_bet_revoked` / `free_bet_expired`
  and the prerequisite raise event for the round-trip path.
- Reads `list_by_account_at_book` (9 expected: all event types
  except `promo_observed` and `promo_journey_annotation`),
  `list_by_account` (same 9), `list_by_book` (11, all).
- Writes a credit + revoke pair with supersession and confirms
  `latest_non_superseded_by_scope(account_at_book_id=..., event_type=
  PromoEventType.FREE_BET_CREDITED)` excludes the revoked credit and
  includes the still-standing ones.
- Walks the supersession chain backwards from the revoke event,
  confirming chain order [original credit, revoke] earliest-first.
- Attempts an append with a bogus `promo_template_id`; confirms
  `PromoReferenceValidationError` raises.

---

## 8 — Findings

Three findings worth surfacing for S131 triage:

**Finding (a) — `draw_down_breakdown` dict-value type preservation
across JSON round-trip.** The W13 brief §5.2.4 specifies
`FreeBetDeployedPayload.draw_down_breakdown: list[dict[str, object]]`
with the dict shape `{credit_event_id: UUID, amount_drawn: Decimal}`
validated by a custom Pydantic validator. The `object`-typed dict
values don't preserve UUID / Decimal type information across JSON
round-trip — after `model_dump_json()` → `model_validate_json()`, the
dict values come back as strings. The custom validator still
re-validates correctly (the `amount_drawn` string parses to Decimal
for sum-check), and the JSON-level round-trip is canonical (the
serialised form is the same in both directions). But strict Pydantic
object equality (`event.payload == fetched.payload`) fails because
the dict-value types differ. The repository test_promos_repository.py
round-trip passes (it compares rows; the row stores the JSON string
verbatim). The adapter test was updated to use JSON-equivalence for
the parametrised round-trip assertion. **Classification:** (a) per
§10 (brief-spec deviation in the test surface, not in shipped behaviour
— operator-side data round-trip works; the deviation is in how we
write the equality assertion). **Resolution options:** (i) keep
JSON-equivalence assertion as-is; (ii) introduce a structured
`DrawDownEntry` sub-BaseModel so dict values carry typed coercion;
(iii) add a `model_validator(mode="before")` to coerce dict values
into canonical types on construction. Option (i) is shipped. The
operational round-trip works end-to-end either way.

**Finding (b) — Two non-halting brief interpretive choices.** Already
surfaced in §2 above. (i) `store/__init__.py` re-exports the 4
repository classes only (W14 precedent), not the error classes.
(ii) `warning_type_id` typed as `UUID` per the §5.2 spec, with the
§5.1.7 slug example values read as illustrative-of-concept.
**Classification:** (a) per §10 (brief-spec interpretive deviation
— I picked one reading and noted both for the operator). Operator
can override either at S131.

**Finding (c) — `store/repositories/promos.py` at 1012 lines.**
Slightly over the §7.3 stated ballpark of 700–1000. The extra ~12
lines support full CRUD on all four repositories per spec. Per S120
length-bends-to-required-detail standing rule this is acceptable;
no detail elided to fit the ceiling. **Classification:** (c)
informational acknowledgement.

No (b) findings (spec-implied substrate concerns that route to a
follow-on workstream). All architecture / DR substrate stays
unchanged.

---

## 9 — What was deliberately not done

Mirroring W13 brief §1.2 plus what surfaced during build:

- **No cascade-triggering logic** — the `cascaded_from_bet_id`,
  `cascaded_at_settlement_state`, `cascade_path` fields on
  `FreeBetCreditedPayload` and `PromoCashCreditedPayload` are payload-
  level only. The trigger that fires a cascade when a bet's
  settlement state changes is future-burst-review work
  (`workflows/burst_review/` still empty at W13 close).
- **No promo journey derivation function** — `promo_journey_annotation`
  events ship, but the `compute_journey()` derivation reading
  successive `promo_observed` events on the same
  `(promo_template_id, book_id, account_at_book_id)` triple lives in
  W12 or post-W17 work.
- **No FB inventory derivation** — `latest_non_superseded_by_scope`
  + `walk_supersession_chain` ship as the read substrate W12 will
  call against. The actual inventory calculation function isn't W13.
- **No AccountCare warning derivation** — same shape: event types
  + supersession-aware reads ship; the
  `raised − cleared per account_at_book` derivation isn't W13.
- **No reference data seed** — `promo_template`, `promo`,
  `warning_catalogue` tables empty after migration. Operator-driven
  one-off seed work belongs between W13 close and W12 brief
  drafting.
- **No edits to W11 / W14 / W14.1 substrate** — confirmed by
  grep against the four shipped W14 files plus W11 files; none
  modified during W13.
- **No `domain.cash_flow` re-use** — DR-030 spirit holds. `domain/promos`
  defines fresh enums (e.g. `PromoEventSource` is structurally
  identical to `CashFlowEventSource` but defined independently).
- **No Alembic / SQLAlchemy Core** — pre-Alembic `apply_migrations`
  pattern preserved.
- **No bet-record payload-reference validation** —
  `triggering_bet_id`, `deploying_bet_id`, `cascaded_from_bet_id`
  references are NOT validated at adapter write time per W13 brief
  §5.4.3. Those soft-coupled references are W8 burst-review's
  responsibility once that workstream lands.
- **No tests/conftest.py touched** — per W14.1 convention, shared
  test fixtures live per-file rather than global.

---

## 10 — Open questions for triage

**Q1.** Should `store/__init__.py` re-export error classes too? The
brief §4 mentions error classes but §1.1 says "Pattern matches W14"
and W14 doesn't re-export errors. Test files import errors directly
from `store.repositories.promos`; the public `store` re-export pattern
is for the convenience surface only. Current shipping: 4 repository
classes only. If operator-Claude prefers the explicit-errors shape,
the change is a 9-line additive edit.

**Q2.** Should the W13 brief's `warning_type_id` slug examples in
§5.1.7 (`'rapid_turnover'` etc.) replace the Pydantic UUID type at
§5.2 with a `str` or a closed enum? Current shipping: UUID-typed
per §5.2; slug values become illustrative-of-concept (the human-
readable `label` field carries the operationally-readable name).
If the operator's intent was that `warning_type_id` is the slug
itself (memorable, operator-typeable in seed scripts), this would
diverge from the UUID pattern used by every other reference table
PK in v3. Operator-Claude can revise the type if the operational
intent was different.

**Q3.** Should the brief's `cascaded_at_settlement_state: str | None`
type be tightened to a closed enum once W8 burst-review (which writes
cascade events) ships? Today's payload accepts any string; a closed
enum referencing the `domain.settlement` settlement-state values
would be more type-safe but would require either a cross-domain
import (DR-030 violation if `domain.promos` imports from
`domain.settlement`) or a local enum mirror in `domain.promos`. The
S130 Cat 5 software call chose `str | None` to keep the module
standalone — flagging for future-W8 re-evaluation.

**Q4.** Should `draw_down_breakdown` use a structured sub-BaseModel
(`DrawDownEntry`) instead of `list[dict[str, object]]`? See finding
(a). Operationally meaningful round-trip works either way; structured
sub-model would give cleaner Pydantic equality across round-trip but
diverges from the brief's stated type signature.

---

## 11 — What Code thinks should land next

Three plausible forward paths per §10 of the brief, plus a fourth
worth flagging:

**Path A — Seed reference data + W15 brief.** Operator writes
`scripts/seed_promos.py` (or SQL seed) to populate one or two
realistic `promo_template` rows, a small `promo` row set, and the
DR-015 baseline `warning_catalogue` entries. Then operator-Claude
drafts the W15 (`ops_events`) brief reusing the W13 / W14.1 pattern
verbatim. **Argument for:** keeps the per-domain-event-table
workstream rhythm; W15 is structurally well-understood; small
seeding step removes the empty-reference-table footnote from the
operational picture. **Argument against:** delays the read-side
derivation work that gives the operator concrete value.

**Path B — W12 (balances + derivations).** The shipped substrate
post-W13 close is the full set W12 needs:
- Bet records (W4 / W6) for cash stake / cash returns flow.
- Cash flow events (W14 / W14.1) for the balance derivation.
- Promo events (W13) for FB inventory + AccountCare warning state +
  promo journey derivation.
W12 is the first read-side workstream — derives the four operator-
facing surfaces from the event-log substrate. **Argument for:** this
is the workstream that gives the operator concrete value (numbers
on screen). **Argument against:** larger and more design-heavy than
W15.

**Path C — W8 (burst review) including cascade trigger logic.**
Writes the cascade event-write surface W13's `cascaded_*` payload
fields exist to support, plus the operator-explicit cascade UI plus
the auto-cascade trigger. **Argument for:** unlocks the cascade
fields end-to-end. **Argument against:** big workstream; W13's
cascade write surface is dormant-but-ready until this lands, which
is fine — the underlying data shape doesn't need the trigger to be
correct.

**Path D (Code's suggestion) — Path A with a faster ramp.** Operator
seeds 1–3 `promo_template` rows reflecting today's most-used
mechanics (Money back if 2nd / 3rd, Bonus winnings 100%, EW
cashback), one or two `promo` rows for the current cycle, and the
~5 baseline `warning_catalogue` entries. Then operator-Claude drafts
W12 next (not W15), prioritising the read-side surfaces over more
event-log build. W15 (`ops_events`) is structurally identical to
W13 / W14 and can ship later without losing momentum; W12 is the
one that the operator's daily work depends on. **Argument:**
maximises operator-facing value per session; the per-domain event-
log pattern is fully exercised twice over (W14 + W13) and W15 can
slot in once W12 has surfaced any read-side concerns that might
inform the ops_events schema. Operator-Claude's final call at S131.

---

**End of report.**
