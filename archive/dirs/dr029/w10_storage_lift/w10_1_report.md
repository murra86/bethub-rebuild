# W10.1 — `BetRecord.last_read_market_state` type demotion report

**Source brief:** `dr029/w10_storage_lift/w10_1_brief.md` (locked
2026-05-11 17:28 ACST, Session 119).
**Session window:** 2026-05-11 17:32:56 → 17:37:33 ACST (Adelaide local
per DR-021).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`.
**Scope:** single named edge from W10 Finding B — demote
`BetRecord.last_read_market_state` from `MarketSettlement | None` to
`dict[str, object] | None`; restore the two broken lint contracts
without behaviour or schema change.

---

## 1. Pre-session state

**Anchor line counts (at session open, post-W10):**

- `domain/bets/__init__.py` — 370 lines.
- `workflows/bet_entry/v1/bet_store_adapter.py` — 195 lines.
- `tests/workflows/bet_entry/v1/test_settlement.py` — 2728 lines.

**Pre-baselines per §7:**

`uv run lint-imports` — 3 contracts kept, 2 broken:

```
DR-030 layered architecture
    domain.bets -> clients.betfair_client.v1.settlement (l.36)
domain imports nothing in the project
    domain.bets -> clients.betfair_client.v1.settlement (l.36)
```

`uv run pytest -x -q` — `527 passed in 1.45s` (W10 close baseline).

`git status --short` — 10 modified, 14 untracked (post-W10 dirty
state). No git operations performed during the session; the dirty-tree
contents are unchanged across the session apart from the W10.1 anchors.

---

## 2. Changes made

### §5.1 — `domain/bets/__init__.py` field type demotion

Removed the `MarketSettlement` import (previously at line 36) along
with the explanatory block comment that documented the W10 Finding B
problem. Updated the module docstring to reflect the new field shape
and the workflow-side parse pattern. Changed
`BetRecord.last_read_market_state`'s annotation from
`MarketSettlement | None` to `dict[str, object] | None`, with the
field's neighbouring comment rewritten to flag the W10.1 demotion and
the consumer-side parse rule.

After this change, the module's imports are stdlib + `pydantic` only.
No `clients/`, no `workflows/`, no `store/`, no `ui/`. The seven
remaining `MarketSettlement` strings in the file are docstring /
comment references — no live import.

Targeted before/after for the field:

```diff
-    last_read_market_state: MarketSettlement | None = None
+    last_read_market_state: dict[str, object] | None = None
```

Targeted before/after for the import block (lines 27–36 pre-edit):

```diff
-# `MarketSettlement` is a clients-side Pydantic model carried on
-# `BetRecord.last_read_market_state` (W9 brief §5.2). This makes
-# `domain.bets` import `clients.betfair_client.v1.settlement`, breaking
-# DR-030's `domain-pure` contract. ...
-# Flagged in the report findings for triage.
-from clients.betfair_client.v1.settlement import MarketSettlement
```

(Block deleted; nothing replaces it. The module docstring picks up the
context.)

### §5.2 — `workflows/bet_entry/v1/bet_store_adapter.py` conversion swap

Added `import json` at module top. Replaced
`MarketSettlement`-model-level (de)serialisation inside `to_rows` /
`from_rows` with plain JSON-string ↔ dict conversion via the stdlib
`json` module. The `MarketSettlement` import stays — it is used by the
`to_provisional_payload(market_settlement: MarketSettlement | None)`
parameter, which remains the typed surface for payload construction.
Updated the module docstring to describe the new boundary semantic.

Targeted before/after for `to_rows`:

```diff
         last_read_market_state=(
-            record.last_read_market_state.model_dump_json()
+            json.dumps(record.last_read_market_state)
             if record.last_read_market_state is not None
             else None
         ),
```

Targeted before/after for `from_rows`:

```diff
         last_read_market_state=(
-            MarketSettlement.model_validate_json(row.last_read_market_state)
+            json.loads(row.last_read_market_state)
             if row.last_read_market_state is not None
             else None
         ),
```

### §5.3 — Caller sweep + anchor updates

Anchor sweep via:

```
grep -rn "last_read_market_state" --include="*.py" \
  /Users/tim/Desktop/Projects/bethub-v3/
```

98 hits across 9 files. Classifying by call shape:

- **Store-side (`BetRow`, `store/repositories/bets.py`,
  `store/schema/bets.py`):** `last_read_market_state: str | None`
  throughout (JSON string). Unchanged — W10.1 doesn't touch the row /
  schema column shape.
- **Worker write path
  (`workflows/bet_entry/v1/settlement.py:_persist_last_read_market_state`):**
  takes `last_read_market_state: MarketSettlement`, calls
  `model_dump_json()` to produce a JSON string, passes the string to
  `storage.update_last_read_market_state(...)`. The store signature
  already takes `str | None` and the worker's `MarketSettlement →
  JSON string` flow does not touch any `BetRecord` field. Unchanged.
- **Provisional router payload construction
  (`ui/api/routers/provisional.py`):** already reads
  `bet_row.last_read_market_state` (a JSON string from the BetRow
  store-side type) and parses via
  `MarketSettlement.model_validate_json(...)` before calling
  `to_provisional_payload`. The dict-typed `BetRecord` field is not
  read on this path. Unchanged.
- **`ProvisionalSettlementSurfacingPayload.last_read_market_state`
  (workflow-side payload field, `settlement.py:281`):** stays typed
  `MarketSettlement | None`. The brief carries this surface unchanged
  (workflow-side typed access is intended). Unchanged.

The only consumer-side updates required by the demotion landed in
`tests/workflows/bet_entry/v1/test_settlement.py` — five sites
asserting `fetched.last_read_market_state.model_dump() ==
snapshot.model_dump()` and three sites constructing a `BetRecord` with
a typed `MarketSettlement` value. Updates:

```diff
- assert fetched.last_read_market_state.model_dump() == snapshot.model_dump()
+ assert (
+     MarketSettlement.model_validate(fetched.last_read_market_state).model_dump()
+     == snapshot.model_dump()
+ )
```

```diff
-     update={"last_read_market_state": snapshot}
+     update={"last_read_market_state": snapshot.model_dump(mode="json")}
```

`MarketSettlement` is already imported at the top of
`tests/workflows/bet_entry/v1/test_settlement.py` (line 31, alongside
the other clients-side enums). No new imports added.

Two specific test-side sites worth noting (covered by the same
substitutions):

- The end-to-end SQLite round-trip test
  (`test_end_to_end_pending_then_provisional_then_terminal_with_sqlite_storage`)
  reads `fetched_after_pending` / `fetched_final` after worker passes
  write through `storage.update_last_read_market_state(...)`. Both
  assertion blocks now wrap `MarketSettlement.model_validate(...)`
  around the dict.
- The `test_surfacing_payload_carries_persisted_last_read_market_state`
  and sibling tests assert against `payload.last_read_market_state`
  (the payload's own field, still `MarketSettlement | None`) — those
  did not need substitution. The substitution applied only to the
  `BetRecord`-side accessors.

---

## 3. Post-session state

**Anchor line counts (at session close):**

- `domain/bets/__init__.py` — 371 lines (+1 net; net of −10 lines for
  the deleted import block / comment and +11 lines for the docstring
  expansion + the field comment rewrite).
- `workflows/bet_entry/v1/bet_store_adapter.py` — 202 lines (+7 net;
  the `import json` addition plus the docstring rewrite, partially
  offset by the conversion-line swap which is the same line count
  before and after).
- `tests/workflows/bet_entry/v1/test_settlement.py` — 2736 lines
  (+8 net; the five `MarketSettlement.model_validate(...)` wrappers
  expand each one-line assertion into a four-line `assert (...)` block
  for readability).

**Post-baselines per §7:**

`uv run lint-imports` — **5 contracts kept, 0 broken.** Analysed 124
files, 352 dependencies. Specifically:

```
DR-030 layered architecture           KEPT
domain imports nothing in the project KEPT
store imports nothing in the project  KEPT
contracts is a leaf package           KEPT
workflows cannot import workflows     KEPT
```

`uv run pytest -x -q` — `527 passed in 1.52s`. Same count as the
pre-baseline; no regressions, no new tests added.

`git status --short` — identical file-set to pre-baseline. The 10
modified files and 14 untracked entries are unchanged at the path
level. The W10.1 edits land inside three already-modified files
(`domain/bets/__init__.py`, plus `workflows/bet_entry/v1/` and
`tests/workflows/bet_entry/v1/test_settlement.py` which are already in
the untracked W10 trees).

---

## 4. Findings / surprises

One observation surfaced during the caller sweep, flagged here for
visibility (no fix attempted per §9.1):

**Finding W10.1-α — `model_dump()` vs `model_dump(mode="json")`
distinction.**

The brief §5.3 "General rule" said: "Assigning a `MarketSettlement`
to `record.last_read_market_state` → convert via `value.model_dump()`
first." For `MarketSettlement` (which has a `datetime` field
`settled_time` and a tuple of `RunnerSettlement` sub-models), plain
`.model_dump()` returns a dict with native `datetime` objects and
inner `RunnerSettlementStatus` enum instances — values that `json.dumps`
in the adapter's `to_rows` cannot serialise.

Used `.model_dump(mode="json")` instead at the three test-side
construction sites — this returns a fully-JSON-primitive dict (ISO
strings for datetimes, string values for enums) which round-trips
cleanly through `json.dumps` → SQLite TEXT → `json.loads` → the
`BetRecord` dict field. The brief's "General rule" text reads as
needing the `mode="json"` qualifier for the JSON-string column path
the brief itself chose; documenting here so the next session can
decide whether to update the brief's prose for any future caller.

No source-side `BetRecord` construction with a typed `MarketSettlement`
exists in the workflow code today — the worker writes via storage,
never assigns to a `BetRecord` field. The mode='json' qualifier is
currently a test-side detail only.

---

## 5. Self-assessment

### Deviations from brief

- **None on the main scope.** Field type demoted, adapter conversion
  swapped, callers updated, verification gates green.
- **One minor consumer-rule clarification** — used `.model_dump(mode="json")`
  rather than the brief's literal `.model_dump()` at three test-side
  `BetRecord` construction sites, for the reason stated under Finding
  W10.1-α.

### Hard-limit adherence (§9.2 – §9.5)

- **§9.2 — Behaviour and schema preserved.** Schema: untouched.
  `BetRow.last_read_market_state: str | None` keeps its JSON-string
  shape; DDL and migration block are unmodified. Behaviour: the
  observable outcomes — persisted JSON content in the column, payload
  field contents (`payload.last_read_market_state` still typed
  `MarketSettlement | None`), `is_past_settlement_window` results — are
  all preserved. The change is a Python-side type narrowing on one
  field of one domain model.
- **§9.3 — No adjacent workstreams or findings.** No work on W10
  Findings A, C, D, E, F, G; no W11–W15 or W17 scaffolding; no new
  module boundaries; no `domain/` subdirectories; no `bet_store_adapter`
  re-shape beyond the §5.2 conversion swap.
- **§9.4 — No Alembic, no debt-fixing.** Untouched.
- **§9.5 — Operational guardrails.** No git operations (no add,
  commit, stash, restore, reset). No DB access (tests use existing
  `tmp_path`-scoped SQLite per pre-W10 pattern). No external API
  calls. Session ran end-to-end with no mid-session escalation; this
  report is the only artefact.

### Length flag

This report is ~250 lines. Within the 150–300 line target per §8.

---

**End of report.**
