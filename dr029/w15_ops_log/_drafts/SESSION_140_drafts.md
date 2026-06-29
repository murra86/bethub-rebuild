# Session 140 drafts — W15 ops-log grounding (pre-drafting capture)

**Purpose:** W15 (operations log) brief drafting was deferred at
S140 close after a full local-MCP-bridge outage (both Desktop
Commander and projects-filesystem hung 4 min each). The brief was
NOT written. This file captures the grounding done at S140 so S141
drafts the W15 brief without re-grounding. Read this + the W13/W14
briefs at S141.

**Anchor:** 2026-05-27 08:34 PDT / 2026-05-28 01:04 ACST (S140 close).

---

## The job (brief Step 1)

Commission Code to build the **operations log** — an append-only
`ops_events` table plus its store adapter, following the W13
(promo events) / W14 (cash flow) **per-domain event-table
pattern**. Ships the `hedge_state_classification` audit-event
shape (the audit trail for the DR-025 six-state hedge
classification). Output: a Code report.

## Home decision (resolved at S140)

W15 follows the **per-domain pattern**, NOT the top-level `ops/`
package. Authority: `store/schema/cash_flow.py` docstring states
verbatim that the common event-header shape "is the pattern W13
(`promo_events`) and W15 (`ops_events`) will reuse." So W15 builds
across four locations, parallel to cash_flow / promos:

- `domain/ops/__init__.py` (new)
- `store/schema/ops.py` (new)
- `store/repositories/ops.py` (new)
- `workflows/ops/v1/ops_store_adapter.py` (new)

**Note:** a top-level `ops/` package already exists (it's in
`.importlinter` root_packages and sits in the layers contract's top
tier alongside `ui`). The S140 outage hit before I could read its
contents — NOT load-bearing, because W15's per-domain modules
(`domain.ops`, `store`-side `ops`, `workflows.ops`) are distinct
packages from the root `ops`. W15 does NOT build in or modify the
top-level `ops/`. Brief should instruct Code to confirm no
naming/import collision and surface any as a finding.

## The pattern (from cash_flow / promos — grounded S140)

Four layers per event-domain:

1. **Domain** (`domain/<d>/__init__.py`):
   - `<D>EventType(StrEnum)` — closed enum of event types.
   - `<D>EventSource(StrEnum)` — `operator` / `system` /
     `integration`.
   - Per-event payload classes (`_PayloadBase` subclasses, each
     with an `event_type_payload` literal discriminator).
   - `<D>EventBase(BaseModel, frozen=True)` — common event header
     (fields below), with validators: Adelaide-local on
     `recorded_at`/`occurred_at`; event_type↔payload discriminator
     match; per-event-type FK required/forbidden rules.

2. **Schema** (`store/schema/<d>.py`): DDL with the common header +
   CHECK-enforced closed enums (event_type, source), indexes sized
   to read patterns, `apply_migrations(conn)` (enables FK pragma,
   creates tables in FK-dependency order, creates indexes,
   idempotent via IF NOT EXISTS), `_add_column_if_missing` helper.
   `store/` imports stdlib only (DR-030).

3. **Repository** (`store/repositories/<d>.py`): row types + CRUD.

4. **Adapter** (`workflows/<d>/v1/<d>_store_adapter.py`): methods
   mirror cash_flow's adapter — `append_event`, `get_event`,
   `list_by_<scope>` (per scope id), `list_by_event_type`,
   `list_by_correlation_id`, `latest_non_superseded_by_scope`,
   `walk_supersession_chain`, plus `_row_to_event` / `_event_to_row`
   converters.

## Common event-header fields (from `CashFlowEventBase`, replicate)

```
event_id: UUID
event_type: <D>EventType
recorded_at: datetime        # system clock at write (Adelaide local)
occurred_at: datetime        # when the real-world fact happened
<scope FKs>                  # nullable generically; per-type rules
parent_event_id: UUID | None = None
supersedes_event_id: UUID | None = None
payload: <discriminated union>
source: <D>EventSource
correlation_id: UUID | None = None
notes: str | None = None
```
`frozen=True` — append-only; "edit" = new event with
`supersedes_event_id` set.

## W15-specific shape

**Scope FKs for `ops_events`:** a hedge-state classification
attaches to a bet (and its cycle). So scope columns are likely
`bet_id` + `cycle_id` (NOT account/book/account_at_book like cash
flow). Confirm against `domain/bets` (`bets` carries `bet_id`,
`cycle_id`). Decide FK target: `bet_id` → `bets(bet_id)`.

**`OpsEventType` (v1):** one concrete type — `HEDGE_STATE_CLASSIFICATION
= "hedge_state_classification"`. The table is the general ops-log
spine; v1 ships the single type DR-025 / W12 needs. CHECK enum
closed; future types extend via migration + enum edit.

**`HedgeStateClassificationPayload`:** records a classification
event. Fields (proposed — confirm at drafting):
- `from_state: HedgeState | None` (None on first classification)
- `to_state: HedgeState`
- `classifier`: operator-set vs auto (maps to `source`
  operator/system) — or an explicit enum
- `reason` / `trigger`: optional (free text or small enum)
- consider an auto-resolve marker (DR-025 settlement+24h auto-
  resolve) — confirm whether that belongs in the payload or is
  derived

**`HedgeState` enum — DOES NOT EXIST in code yet** (grep-confirmed
S140; zero matches). W15 defines the six DR-025 states:
`hedged`, `hedge_partial`, `hedge_failed`, `unhedged_deliberate`,
`unhedged_oversight`, `unhedged_unclassified`. Decide home:
`domain/ops` (with the payload) or `domain/bets`. Lean `domain/ops`
since it's the ops-log's concern; cross-check it doesn't belong
with the bet record. (DR-025 amendment in decisions.md is the
authority for the six states.)

## Two housekeeping folds (carry from S139)

1. **Import-linter carve-out.** `.importlinter` has an
   `independence` contract `workflows-independent` currently listing
   ONLY `workflows.bet_entry` and `workflows.burst_review`. W15 must
   register `workflows.ops` consistently with the W13/W14 precedent.
   **Observed inconsistency to surface:** `workflows.promos`,
   `workflows.cash_flow`, `workflows.balances` are NOT in that
   contract. So "match precedent" may mean NOT adding ops either, OR
   the contract is under-populated. Brief instructs Code to: add
   `workflows.ops` per precedent, run `lint-imports`, and surface
   the inconsistency as a finding rather than silently
   normalising it.
2. **`.venv/bin/python` 3.12 anchor** in §4 system access (DR-031
   locks Python 3.12+). Same as the W12.1 brief §4.

## Tests — three-way split (W14.1 / W13 convention)

Layout (per cash_flow precedent):
- `tests/store/repositories/test_ops_schema.py`
- `tests/store/repositories/test_ops_repository.py`
- `tests/workflows/ops/v1/test_ops_store_adapter.py`
Cover: schema round-trip, migration idempotency, append + each
`list_by_*`, supersession chain, the event_type↔payload validator,
FK rules, Adelaide-local validator.

## Scope calls to surface at S141 handoff (operator-visible)

- **Single event type at v1** (`hedge_state_classification`), table
  as extensible spine — vs shipping a broader set now. (Lean:
  single, matches the "ships the hedge_state_classification shape"
  framing.)
- **W15 ships the audit LOG, not the classifier engine.** The
  auto-classification flow (what decides a bet's hedge state) is
  separate/later — parallel to how W14 shipped the cash-flow store
  but W12 was the consumer. Exclude in hard limits.

## Brief shape

Universal spine §1–§11 (W13 brief is the template; same structure,
leaner — ops log is simpler than W13's promos+inventory+reference
scope). Dirty-tree discipline (W12 build untracked; same as W12.1
brief §9). Output: `dr029/w15_ops_log/w15_ops_log_report.md`.

## Pre-reads for the S141 drafting session

- This file.
- `dr029/w13_promos/w13_promos_brief.md` (the template; §5.1–§5.6,
  §6, §9 especially).
- `dr029/w14_cash_flow/w14_cash_flow_brief.md` (the append-only
  event-store precedent).
- Live: `store/schema/cash_flow.py`, `domain/cash_flow/__init__.py`,
  `workflows/cash_flow/v1/cash_flow_store_adapter.py` (the exact
  pattern to mirror), `.importlinter` (the carve-out),
  `decisions.md` DR-025 + S139 amendment (the six states).
