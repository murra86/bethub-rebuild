# W10.1 — `BetRecord.last_read_market_state` type demotion

**Source:** `dr029/w10_storage_lift/w10_report.md` Finding B.
**Brief locked:** 2026-05-11 17:28 ACST (Session 119).
**Anchor:** `/Users/tim/Desktop/Projects/bethub-v3/`.

---

## §1. What this is and is not

This is a **surgical fix** to the single import edge surfaced in
W10 Finding B. Single bounded Code session. Single change to a
type annotation on `BetRecord`, with the conversion pushed into
the existing adapter and the typed-access consumers updated.
Verification: lint-imports comes back fully green (5 contracts
kept, 0 broken); pytest stays green (527 passing, same as W10
close baseline); no behaviour or schema change.

It is **not** a refactor of the settlement-snapshot surface, a
re-shape of the boundary adapter, a broader DR-030 enforcement
pass, or work on findings A, C, D, E, F, or G from the W10 report
(all of which are accepted as-shipped per Session 119 triage).

Surprises become findings in the report. Remediation routes to
operator-Claude triage, not Code's report.

## §2. Why this work exists

W10 lifted the bet vocabulary into `domain/bets/`. After the lift,
`BetRecord.last_read_market_state: MarketSettlement | None` forces
the import `domain.bets -> clients.betfair_client.v1.settlement`
at module load. This breaks the `domain-pure` and `DR-030 layered
architecture` lint contracts. The `store-pure` contract (W10's
primary failure signal) is green — but the broader DR-030 picture
isn't.

Operator-Claude Session 119 triage routed this as Path (a) from
W10 Finding B: demote the field type to `dict[str, object] | None`
and have the consumers convert to/from `MarketSettlement` at the
specific sites that need typed access. The underlying storage
column is already a JSON string
(`BetRow.last_read_market_state: str | None`), so the dict shape
matches the on-disk shape directly. The conversion cost is one
`.model_dump()` / `.model_validate()` call at each consumer.

## §3. Pre-reads

Required-reads before starting (in order):

1. `dr029/w10_storage_lift/w10_brief.md` — the W10 brief.
   Establishes the layering rules, the adapter pattern, and the
   primary-vs-secondary failure-signal framing.
2. `dr029/w10_storage_lift/w10_report.md` — the W10 report.
   Finding B is the named work; Findings A, C, D, E, F, G are
   out-of-scope here and must not be touched.
3. `decisions.md` §DR-030 — the v3 repo layout and module-boundary
   discipline DR. Load-bearing for the verification gate.
4. `bethub-v3/.importlinter` — the five lint contracts. The two
   currently failing contracts (`domain-pure`,
   `DR-030 layered architecture`) are what must go green.

Reference-only (do not read unless a finding warrants):

- `domain/bets/__init__.py` — owns `BetRecord` and its
  `last_read_market_state` field.
- `workflows/bet_entry/v1/bet_store_adapter.py` — owns boundary
  conversion (`to_rows` / `from_rows`) and payload construction
  (`to_provisional_payload`).
- `clients/betfair_client/v1/settlement.py` — defines
  `MarketSettlement`.
- `workflows/bet_entry/v1/settlement.py` — owns
  `_persist_last_read_market_state` (the writer).
- `ui/api/routers/provisional.py` — the read-side consumer that
  constructs provisional payloads.

## §4. System access

Mac filesystem **read-write** to
`/Users/tim/Desktop/Projects/bethub-v3/`. No DB access. No
external API access. No git operations (no add, commit, stash,
restore, reset; the working tree is dirty from W10).

All timestamps in the report use Adelaide local time per DR-021
(timestamp anchoring, Adelaide local time).

## §5. Substantive scope

### §5.1 — `BetRecord` field type demotion

In `domain/bets/__init__.py`:

- Change `BetRecord.last_read_market_state` field annotation from
  `MarketSettlement | None` to `dict[str, object] | None`.
- Remove the import of `MarketSettlement` from
  `clients.betfair_client.v1.settlement`. After this change, no
  module under `domain/` should import from `clients/`.
- Update the field's docstring (if present) to reflect the new
  shape: the field holds the most recent settlement snapshot as a
  JSON-shaped dict; workflow-side consumers parse into
  `MarketSettlement` when typed access is needed.

### §5.2 — Adapter boundary conversion

In `workflows/bet_entry/v1/bet_store_adapter.py`:

- `to_rows(record)`: when serialising
  `record.last_read_market_state` (now a dict) to
  `BetRow.last_read_market_state` (a JSON string column), use
  `json.dumps(record.last_read_market_state)` if not-None, else
  None.
- `from_rows(row, legs)`: when constructing the `BetRecord`,
  parse `row.last_read_market_state` (JSON string) with
  `json.loads(row.last_read_market_state)` if not-None, else None
  for the dict-typed field.

`MarketSettlement` model-level (de)serialisation moves out of the
adapter's `to_rows` / `from_rows` boundary — these functions now
handle plain dict ↔ JSON-string conversion, not model ↔ JSON.
Model-level (de)serialisation now happens only at the specific
consumer sites that need typed access (see §5.3).

### §5.3 — Caller updates

Anchor sweep before edits to confirm all consumers are identified:

```
grep -rn "last_read_market_state" \
  --include="*.py" \
  /Users/tim/Desktop/Projects/bethub-v3/
```

Two named anchor sites worth verifying directly (from the W10
report):

- **`workflows/bet_entry/v1/settlement.py:_persist_last_read_market_state`**
  — currently calls `market_state.model_dump_json()` before
  passing the JSON string to
  `storage.update_last_read_market_state(...)`. The storage write
  call shape is unchanged. The in-memory `BetRecord` field is now
  dict; where the settlement worker assigns to
  `record.last_read_market_state`, it now calls
  `market_state.model_dump()` (returning a dict) rather than
  holding the typed `MarketSettlement` on the record.
- **The provisional-router payload construction**
  (`workflows/bet_entry/v1/bet_store_adapter.py:to_provisional_payload`
  + its caller in `ui/api/routers/provisional.py`) — the function
  currently takes `market_settlement: MarketSettlement` as a
  separate parameter. The router call site now parses the dict
  back to `MarketSettlement` before calling the payload builder:

  ```
  market_settlement = (
      MarketSettlement.model_validate(record.last_read_market_state)
      if record.last_read_market_state is not None
      else None
  )
  ```

  `to_provisional_payload`'s signature is unchanged; only the
  caller-side parse is added.

General rule for any other consumers the grep surfaces:

- **Assigning a `MarketSettlement` to `record.last_read_market_state`**
  → convert via `value.model_dump()` first.
- **Reading `record.last_read_market_state` for typed access**
  → convert via
  `MarketSettlement.model_validate(record.last_read_market_state)`,
  guarding for None.

Test files that previously constructed `BetRecord` with a typed
`MarketSettlement` for `last_read_market_state` now construct with
`.model_dump()` dicts. The W10 test helpers (`_write_record`,
`_read_record`, `_provisional_payloads` — Finding F) are
untouched in shape; only the field-construction values within
test cases change.

## §6. Sequencing within session

In dependency order:

1. Capture pre-baselines per §7 (lint-imports, pytest, git
   status).
2. §5.1 (field type demotion + `MarketSettlement` import
   removal). Verify file parses; do not run pytest yet.
3. §5.2 (adapter `to_rows` / `from_rows` updated to plain
   JSON ↔ dict).
4. §5.3 (caller sweep + anchor-site updates + any consumer
   parses).
5. Capture post-baselines per §7. Lint-imports must show 5
   contracts kept, 0 broken; pytest must show 527 passed.

If a verification gate fails at step 5, surface as a finding in
§4 of the report rather than chasing the failure beyond the named
anchors.

## §7. Empirical verification

**Pre-baseline (capture at session start):**

- `uv run lint-imports` — full output. Expected: 3 contracts
  kept, 2 broken on the
  `domain.bets -> clients.betfair_client.v1.settlement` edge.
- `uv run pytest -x -q` — exit status + summary line. Expected:
  527 passed.
- `git status --short` — full output. Captures the dirty-tree
  state going in.

**Post-baseline (capture at session close, before report write):**

- `uv run lint-imports` — full output. Expected: 5 contracts
  kept, 0 broken.
- `uv run pytest -x -q` — exit status + summary line. Expected:
  527 passed.
- `git status --short` — full output. Should differ from pre only
  on the named anchors.

**Anchor diffs (capture in the report):**

For each modified file, run `git diff <file>` at session close
and include the diff in the report as a quote-block under §2
(Changes made).

## §8. Output spec

**Single output file:** `dr029/w10_storage_lift/w10_1_report.md`.

**Section structure:**

1. Pre-session state — line counts of anchors; pre-baselines from
   §7.
2. Changes made — one §-sub-section per substantive change (§5.1
   through §5.3). Anchor diffs inline.
3. Post-session state — post-baselines from §7.
4. Findings / surprises — flag anything that deviated, surprised,
   or didn't fit the brief. Per §9.1, observe and report — no
   freelance fixes.
5. Self-assessment — deviations from brief (if any); hard limits
   adherence; anything in scope that couldn't be done cleanly;
   report length flag.

**Length range:** 150–300 lines.

**Output does NOT contain:** recommendations for next steps;
suggested follow-up briefs; routing calls; any work outside the
named anchors.

## §9. Hard limits — non-negotiable

### §9.1 Operating principle

Code observes and reports; the next operator-Claude session
decides what to do about surprises. If a finding arises that
isn't covered by the brief's named scope, Code does not freelance
a fix — Code surfaces the finding in §4 of the report and the
next session routes it.

### §9.2 Behaviour and schema preserved

- Schema unchanged. No new tables, no new columns, no modified
  columns, no DDL changes. `BetRow.last_read_market_state: str |
  None` keeps its existing JSON-string shape.
- Behaviour unchanged. The in-memory representation on
  `BetRecord.last_read_market_state` changes type (dict vs typed
  model), but every observable outcome (persisted JSON string in
  the column, payload contents for the provisional router, the
  `is_past_settlement_window` computed-field result) is preserved.

### §9.3 No adjacent workstreams or findings

- No work on W10 Findings A, C, D, E, F, G — all accepted
  as-shipped per Session 119 triage.
- No work on W11–W15 (accounts, balances, promos, transactions,
  ops log) or W17 (racing market pages) scaffolding.
- No new module boundaries; no new `domain/` subdirectories; no
  re-shape of `bet_store_adapter.py` beyond the conversion
  changes in §5.2.

### §9.4 No Alembic adoption, no debt-fixing

- No Alembic adoption (carried per W10 brief §10.2).
- No work on the named pieces of v3 debt (monolithic
  orchestrator file; no migration framework; no test coverage
  gaps).

### §9.5 Operational guardrails

- No git operations (no add, commit, stash, restore, reset). The
  working tree is dirty from W10; Code reads but does not modify
  the dirty state outside the named anchors.
- No DB access. Tests use `tmp_path`-scoped SQLite per existing
  pattern.
- No external API calls.
- No mid-session escalation. Code runs end-to-end, surfaces
  findings in the report, does not ping operator-Claude
  mid-flight for direction.

## §10. What happens after Code's session

1. Operator-Claude Session 120 (or wherever the next session
   lands) reads `dr029/w10_storage_lift/w10_1_report.md`, runs
   the inventory-first cadence on any findings, and routes each.
2. If verification gates pass (5 contracts kept, 0 broken; 527
   pytest passes; anchor diffs clean), close W10.1 and update
   `v3_build_picture.md` to mark W10 fully complete and unblock
   W11–W15.
3. If verification gates fail (any), routing decision: follow-up
   surgical brief, escalate to a broader re-shape, or accept the
   residual contract break with operator confirmation.

## §11. Cross-references

- **W10 brief:** `dr029/w10_storage_lift/w10_brief.md` — the
  parent brief whose Finding B this fix closes.
- **W10 report:** `dr029/w10_storage_lift/w10_report.md` — Finding
  B at §4.B.
- **DR-030** (v3 repo layout and module-boundary discipline) —
  the load-bearing structural rule whose two contracts
  (`domain-pure` + `DR-030 layered architecture`) this brief
  restores to green.
- **DR-031** (v3 tech stack) — Alembic locked but deferred per
  W10 brief §10.2; this brief honours that carry.
- **DR-021** (timestamp anchoring, Adelaide local time) — all
  timestamps in the report.
- **W10 brief §9.1** operating principle — verbatim carry to §9.1
  here.

---

**End of brief.**
