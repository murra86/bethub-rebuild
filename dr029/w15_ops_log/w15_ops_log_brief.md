# W15 — Operations log (Code brief)

**Status:** Locked, Session 142 (2026-06-10 ACST).
**Type:** Build workstream. Single bounded Code session.
**Workstream:** W15 (operations log — `ops_events`).
**Precedent shape:** W13 (promos) / W14 (cash flow) per-domain
event-table briefs. Third instance of the pattern; this brief is
deliberately leaner because the pattern is established and the
shipped W14 code is the authoritative template.
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/`

---

## §1 — What this brief is and is not

This brief commissions the **operations log**: an append-only
`ops_events` table, its domain models, repository, and store
adapter — the third instance of the per-domain event-table
pattern established by W14 (`cash_flow_events`) and reused by
W13 (`promo_events`).

v1 ships **one concrete event type**:
`hedge_state_classification` — the audit-trail record for the
DR-025 six-state hedge classification model. Every time a bet's
hedge state is classified (or re-classified), an event is
appended recording the transition, who/what made it, and why.
Events are never edited or deleted; corrections supersede.

The table and its surrounding code are built as the **general
ops-log spine** — the closed event-type enum and CHECK
constraint extend via migration when future operational event
types are commissioned. v1 does not speculate about what those
types are.

**This brief is not:**

- The hedge-classification **engine**. Nothing in W15 decides
  what a bet's hedge state is. The auto-classification flow
  (Betfair-data-derived states), the settlement+24h auto-resolve
  timer, and the operator classification surface (Burst Review,
  W8) are all later work per the DR-025 S139 amendment
  sequencing. W15 ships the place those decisions get recorded.
- A `hedge_state` column on the `bets` table. That column lands
  with the classifier engine, not with the log.
- Any change to W12 / W12.1 balance code, bet-entry code, or
  any other shipped workstream.

Surprises become **findings** in the report, not blockers and
not silent scope expansion. If the pattern-mirroring surfaces
something the named anchors don't cover, Code stops at the
boundary, implements what is named, and records the surface as
a finding for operator-Claude triage.

---

## §2 — Why this work exists

DR-025 (hedge classification — five terminal states plus one
transient) requires that "every classification event goes into
the operations log with the path indicator: operator-classified
vs auto-resolved," so that v4 analytics can distinguish
operator-confirmed states from auto-resolved ones. The S139
amendment confirmed the six-state model unchanged and locked the
sequencing: (b) "W15 — the operations log ships the
`hedge_state_classification` audit-event shape only."

W14 shipped the first per-domain event log (`cash_flow_events`)
and its docstring states the common event-header shape "is the
pattern W13 (`promo_events`) and W15 (`ops_events`) will reuse."
W13 shipped the second instance. W15 is the third and completes
the operational-store event-log set currently scoped.

W15 was fully grounded at Session 140
(`dr029/w15_ops_log/_drafts/SESSION_140_drafts.md`); this brief
executes that grounding. Two operator scope calls were confirmed
at Session 141: (1) single event type at v1, spine extensible;
(2) W15 ships the logbook, not the classifier engine.

---
## §3 — Pre-reads

Required, in order:

1. This brief.
2. `store/schema/cash_flow.py` — the schema template. Its module
   docstring is the pattern authority; `ops.py` mirrors its
   shape (DDL constants, indexes, `_add_column_if_missing`,
   `apply_migrations`).
3. `domain/cash_flow/__init__.py` — the domain template: the
   StrEnums, `_PayloadBase` discriminator pattern, the frozen
   `CashFlowEventBase` header model and its validators
   (Adelaide-local datetimes, event_type↔payload match,
   per-type FK required/forbidden rules).
4. `workflows/cash_flow/v1/cash_flow_store_adapter.py` — the
   adapter template: method surface and the
   `_row_to_event` / `_event_to_row` converters.
5. `decisions.md` (rebuild folder) DR-025 **including the
   2026-05-22 Session 139 amendment** — the six states, the
   path-indicator requirement, and the sequencing that bounds
   this brief.

Reference-only (read on demand, not required up front):

- `store/repositories/cash_flow.py` — repository template.
- `store/schema/bets.py` — the `bets` DDL (`bet_id` PK,
  `cycle_id` column) that `ops_events` references.
- `domain/bets/__init__.py` — `BetRecord` (`bet_id: str`,
  `cycle_id: str`) for scope-field typing.
- `store/schema/promos.py` / `domain/promos/__init__.py` — the
  second pattern instance, if a tie-breaker is needed where
  cash_flow and promos diverge (they should not materially).
- `.importlinter` — the §5.6 edit target.
- `dr029/w14_cash_flow/w14_cash_flow_brief.md` §5 — the fuller
  prose behind the pattern, if the shipped code leaves a
  question open.

---

## §4 — System access

- **Mac filesystem, read-write**, limited to the named anchors
  in §5. Everything else read-only.
- **Python:** `.venv/bin/python` at the repo root — Python 3.12
  per DR-031 (tech stack). All `pytest` / `lint-imports` runs go
  through the venv binaries (`.venv/bin/pytest`,
  `.venv/bin/lint-imports`).
- **No live databases.** All DB work is against temp/in-memory
  SQLite in tests. v2's `bethub.db` and the VPS `capture.db` are
  out of scope entirely.
- **No network access needed.** No Betfair API calls.
- **Timestamps:** Adelaide local (ACST/ACDT) for every
  time-of-day reference in the report, per DR-021.

---
## §5 — Substantive scope

Four new modules + one additive edit to `store/__init__.py` +
one `.importlinter` edit + three test files. All four modules
are **new files** — nothing existing is modified except the two
named edits. Mirror the cash_flow instance throughout; where
this brief is silent, the shipped cash_flow code is the
authority.

### §5.1 — Domain models (`domain/ops/__init__.py`) — NEW

Module docstring follows the cash_flow shape: what the module
is, the DR-025 anchor, the W15 brief reference, DR-030
placement note (domain imports nothing in the project).

**`OpsEventType(StrEnum)`** — closed enum, one member at v1:

- `HEDGE_STATE_CLASSIFICATION = "hedge_state_classification"`

**`OpsEventSource(StrEnum)`** — mirror cash_flow exactly:
`OPERATOR = "operator"`, `SYSTEM = "system"`,
`INTEGRATION = "integration"`.

**`HedgeState(StrEnum)`** — the six DR-025 states, values
verbatim from the DR:

- `HEDGED = "hedged"`
- `HEDGE_PARTIAL = "hedge_partial"`
- `HEDGE_FAILED = "hedge_failed"`
- `UNHEDGED_DELIBERATE = "unhedged_deliberate"`
- `UNHEDGED_OVERSIGHT = "unhedged_oversight"`
- `UNHEDGED_UNCLASSIFIED = "unhedged_unclassified"`

Home decision (made at drafting): `HedgeState` lives in
`domain/ops` with the payload that carries it. It is the ops
log's vocabulary today; nothing in `domain/bets` consumes it
(grep-confirmed zero matches in the codebase at S140/S141).
When the classifier engine and the `hedge_state` column land
later, relocation to `domain/bets` is a candidate — Code notes
this in the module docstring but does NOT pre-emptively place
it in `domain/bets` now.

**`ClassificationPath(StrEnum)`** — the DR-025 path indicator,
recording HOW a classification happened:

- `OPERATOR = "operator"` — operator-set (Burst Review or
  equivalent surface, later).
- `AUTO_BETFAIR = "auto_betfair"` — derived from Betfair match
  data (the hedged / hedge_partial / hedge_failed auto states).
- `AUTO_RESOLVE = "auto_resolve"` — the settlement+24h timer
  resolving `unhedged_unclassified` → `unhedged_deliberate`.
- `SYSTEM_DEFAULT = "system_default"` — the log-time default
  assignment of `unhedged_unclassified` when a bet has no
  linked Betfair order (DR-025 flow step 5). Distinct from
  `AUTO_BETFAIR` (which derives a state FROM match data) and
  from `AUTO_RESOLVE` (the timer).

**`_PayloadBase(BaseModel)`** — mirror cash_flow: frozen,
`event_type_payload` literal discriminator pattern.

**`HedgeStateClassificationPayload(_PayloadBase)`**:

- `event_type_payload: Literal["hedge_state_classification"]`
- `from_state: HedgeState | None` — `None` on the first
  classification of a bet; the prior state on re-classification
  or supersession.
- `to_state: HedgeState` — required.
- `path: ClassificationPath` — required. The DR-025 path
  indicator.
- `reason: str | None = None` — optional free text (e.g. the
  operator's note on an `unhedged_oversight` flag).

Payload validator: `from_state` and `to_state` must differ when
`from_state` is not `None` (a classification event records a
transition; a no-op re-assertion is not an event).

Consistency validator (model-level on `OpsEventBase`, see
below): `path == OPERATOR` requires header
`source == OPERATOR`; `path` in
(`AUTO_BETFAIR`, `AUTO_RESOLVE`, `SYSTEM_DEFAULT`) requires
`source == SYSTEM`. Keeps the generic header and the
DR-025-specific payload from contradicting each other.

**`OpsEventBase(BaseModel, frozen=True)`** — the common event
header, mirroring `CashFlowEventBase` field-for-field with the
scope FKs swapped to the bet axis:

```
event_id: UUID
event_type: OpsEventType
recorded_at: datetime        # system clock at write, Adelaide
occurred_at: datetime        # when the real-world fact happened
bet_id: str | None = None    # scope FK (str — bets PK is TEXT)
cycle_id: str | None = None  # scope (plain column, no FK table)
parent_event_id: UUID | None = None
supersedes_event_id: UUID | None = None
payload: <discriminated union of payload classes>
source: OpsEventSource
correlation_id: UUID | None = None
notes: str | None = None
```

Validators, mirroring cash_flow's: (a) Adelaide-local timezone
required on `recorded_at` / `occurred_at`; (b) event_type ↔
payload discriminator match; (c) per-event-type FK rules — for
`hedge_state_classification`, `bet_id` AND `cycle_id` are both
REQUIRED (a classification always attaches to a bet, and every
bet carries a cycle per DR-032 / the `bets` DDL where
`cycle_id` is NOT NULL); (d) the path↔source consistency rule
above.

Scope-field typing note: `bet_id` / `cycle_id` are `str`, not
`UUID` — the `bets` table keys are TEXT and `BetRecord` carries
them as `str`. Do not "normalise" them to UUID.

### §5.2 — Schema (`store/schema/ops.py`) — NEW

Mirror `store/schema/cash_flow.py` (DDL constants, indexes,
`_add_column_if_missing`, `apply_migrations(conn)`; stdlib
imports only per DR-030).

**`ops_events` DDL** — common header columns with the scope
swapped to the bet axis:

```sql
CREATE TABLE IF NOT EXISTS ops_events (
    event_id            TEXT PRIMARY KEY NOT NULL,
    event_type          TEXT NOT NULL
        CHECK (event_type IN (
            'hedge_state_classification'
        )),
    recorded_at         TEXT NOT NULL,
    occurred_at         TEXT NOT NULL,
    bet_id              TEXT,
    cycle_id            TEXT,
    parent_event_id     TEXT
        REFERENCES ops_events(event_id),
    supersedes_event_id TEXT
        REFERENCES ops_events(event_id),
    payload             TEXT NOT NULL,
    source              TEXT NOT NULL
        CHECK (source IN (
            'operator', 'system', 'integration')),
    correlation_id      TEXT,
    notes               TEXT,
    FOREIGN KEY (bet_id) REFERENCES bets(bet_id)
);
```

`cycle_id` carries no FOREIGN KEY — cycles have no table of
their own; `cycle_id` is a plain column on `bets` (DR-032). The
column is indexed for the read pattern, not FK-enforced.

Scope columns are nullable at the DDL layer (generic header
shape, matching cash_flow's nullable scope columns); the
per-event-type REQUIRED rule is enforced in the domain
validator. Defence-in-depth split identical to cash_flow.

**Indexes** (four, sized to read patterns):

- `idx_ops_events_bet ON ops_events(bet_id, recorded_at)`
- `idx_ops_events_cycle ON ops_events(cycle_id, recorded_at)`
- `idx_ops_events_event_type
   ON ops_events(event_type, recorded_at)`
- `idx_ops_events_correlation ON ops_events(correlation_id)`

**`apply_migrations(conn)`** — enables the FK pragma, creates
`ops_events`, creates the indexes; idempotent via IF NOT
EXISTS. Dependency note in the docstring: `ops_events` FKs to
`bets(bet_id)` — callers (and tests) must apply the bets schema
migrations first, exactly as `cash_flow` documents its
dependency on the W11 accounts tables. Mirror that handling;
do not invent a new cross-schema bootstrap mechanism.

### §5.3 — Repository (`store/repositories/ops.py`) — NEW

Mirror `store/repositories/cash_flow.py`: an `OpsEventRow`
row type and CRUD over `ops_events`. Repository `__init__`
invokes `apply_migrations` per the cash_flow precedent. Read
methods cover the same surface the adapter needs (§5.4): by
event_id, by bet_id, by cycle_id, by event_type, by
correlation_id, supersession lookups. Append-only — no UPDATE
or DELETE on `ops_events` rows anywhere in the module. stdlib
imports only per DR-030.

### §5.4 — Adapter (`workflows/ops/v1/ops_store_adapter.py`) — NEW

Plus the package files `workflows/ops/__init__.py` and
`workflows/ops/v1/__init__.py`.

`OpsStoreAdapter` mirrors `CashFlowStoreAdapter`'s method
surface with the scope methods swapped to the bet axis:

- `append_event(event: OpsEventBase) -> UUID`
- `get_event(event_id: UUID) -> OpsEventBase`
- `list_by_bet(bet_id, ...)`
- `list_by_cycle(cycle_id, ...)`
- `list_by_event_type(event_type, ...)`
- `list_by_correlation_id(correlation_id, ...)`
- `latest_non_superseded_by_scope(...)` — scope = bet: the
  latest non-superseded event for a bet_id. This is the read
  the future classifier surface uses to answer "what is this
  bet's current classification per the log".
- `walk_supersession_chain(event_id, ...)`
- `_row_to_event` / `_event_to_row` converters (payload JSON
  round-trip through the discriminated union, exactly as
  cash_flow's converters do).

Pagination/ordering parameters: copy cash_flow's signatures.

### §5.5 — `store/__init__.py` — ADDITIVE EDIT

Add the ops repository re-exports alongside the existing
cash_flow and promos blocks (W14 §5.4 precedent). Additive
only — no reordering, no removal, no reformatting of existing
exports.

### §5.6 — `.importlinter` — ADDITIVE EDIT

Add `workflows.ops` to the `workflows-independent` independence
contract's modules list (currently `workflows.bet_entry`,
`workflows.burst_review`).

**Finding to surface (do not silently normalise):** the
contract does NOT list `workflows.promos`,
`workflows.cash_flow`, or `workflows.balances`, despite those
packages existing. Either the contract is under-populated or
the omission is deliberate. Code adds `workflows.ops`, runs
`lint-imports`, and records the inconsistency as a report
finding for operator-Claude triage. Code does NOT add the
other three packages to the contract in this session.

### §5.7 — Naming-collision check (top-level `ops/`)

A top-level `ops/` package exists at the repo root (currently
an empty placeholder `__init__.py`; it sits in the
`ui | ops` layer of the `.importlinter` layers contract). W15's
modules (`domain.ops`, `store.schema.ops`,
`store.repositories.ops`, `workflows.ops`) are distinct module
paths and do not collide with root `ops`. Code confirms at
session start that no import shadowing or resolution surprise
arises (a quick `python -c "import ops; import domain.ops;
import workflows.ops"` after the modules exist suffices) and
surfaces any anomaly as a finding. Code does NOT modify, build
in, or remove the top-level `ops/` package.

### §5.8 — Tests — NEW (three files)

Three-way split per the W13/W14 convention:

- `tests/store/repositories/test_ops_schema.py`
- `tests/store/repositories/test_ops_repository.py`
- `tests/workflows/ops/v1/test_ops_store_adapter.py`
  (plus the test package `__init__.py` files mirroring the
  cash_flow test tree)

Coverage, mirroring the cash_flow test suites:

- Schema: DDL round-trip, migration idempotency (double
  `apply_migrations` clean), CHECK enforcement (bad event_type
  / bad source rejected), FK enforcement (`bet_id` must exist
  in `bets`; tests apply bets schema migrations first per the
  §5.2 dependency note).
- Repository: insert + each read path, append-only surface.
- Adapter: `append_event` + `get_event` round-trip through the
  payload union; each `list_by_*`; supersession chain append +
  walk; `latest_non_superseded_by_scope` with and without
  supersession.
- Domain validators: Adelaide-local datetime rejection of naive
  / wrong-tz datetimes; event_type↔payload mismatch rejection;
  missing `bet_id` / `cycle_id` rejection for
  `hedge_state_classification`; `from_state == to_state`
  rejection; path↔source consistency rejection; all six
  `HedgeState` values accepted in `to_state`.

---

## §6 — Sequencing within session

1. **Pre-build alignment check.** Read working-tree state
   (`git status`), read the cash_flow pattern files, run the
   §5.7 collision check on the existing root `ops/`, capture
   the §7.1 pre-baselines.
2. `domain/ops/__init__.py` (no dependencies).
3. `store/schema/ops.py` (no project imports).
4. `store/repositories/ops.py` (imports schema).
5. `workflows/ops/v1/ops_store_adapter.py` (imports domain +
   repository).
6. `store/__init__.py` additive edit.
7. `.importlinter` edit + `lint-imports` run.
8. Tests (all three files), full `pytest` run.
9. §7.2 post-baselines + report.

If a different order is operationally cleaner mid-session, Code
may deviate with the reasoning recorded in the report.

---

## §7 — Empirical verification

### §7.1 — Pre-baselines (capture at session open)

- `git status --short` — full dirty-tree snapshot.
- Confirm none of the §5 new-file paths exist yet.
- `.venv/bin/lint-imports` — baseline result (expected: pass).
- `.venv/bin/pytest` — baseline run; record pass/fail counts.
  (If the W12.1 surgical fix has executed before this session,
  its test file is part of the baseline — see §9 dirty-tree.)

### §7.2 — Post-baselines (capture at session close)

- `.venv/bin/pytest` — full run green, including the three new
  test files; record counts.
- `.venv/bin/lint-imports` — green with `workflows.ops`
  registered.
- `git status --short` — delta vs §7.1 is EXACTLY: the new
  files named in §5 (+ test package `__init__.py` files) as
  untracked additions, plus modifications to
  `store/__init__.py` and `.importlinter`. Nothing else moved.

### §7.3 — End-to-end spot-check

In a temp SQLite DB (bets schema applied first, one stub bets
row inserted), run the canonical DR-025 lifecycle through the
adapter:

1. Append event 1 — the log-time default:
   `from_state=None`, `to_state=UNHEDGED_UNCLASSIFIED`,
   `path=SYSTEM_DEFAULT`, `source=SYSTEM`.
2. Append event 2 superseding event 1 — the auto-resolve:
   `from_state=UNHEDGED_UNCLASSIFIED`,
   `to_state=UNHEDGED_DELIBERATE`, `path=AUTO_RESOLVE`,
   `source=SYSTEM`, `supersedes_event_id=<event 1>`.
3. Append event 3 superseding event 2 — the retrospective
   operator flag: `from_state=UNHEDGED_DELIBERATE`,
   `to_state=UNHEDGED_OVERSIGHT`, `path=OPERATOR`,
   `source=OPERATOR`, with a `reason`,
   `supersedes_event_id=<event 2>`.
4. Verify: `latest_non_superseded_by_scope` returns event 3;
   `walk_supersession_chain` from event 3 yields 3→2→1;
   `list_by_bet` returns all three in `recorded_at` order;
   payloads round-trip intact through JSON.

Record the spot-check transcript in the report.

Also update the §5.8 domain-validator test coverage to include
the `path`↔`source` consistency rule across all four
`ClassificationPath` values.

---

## §8 — Output spec

Single report file:

`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w15_ops_log/
w15_ops_log_report.md`

(one path — wrapped here for display width only).

Section structure:

1. Session header — Adelaide-local open/close timestamps
   (DR-021), venv/Python check result, §7.1 pre-baselines.
2. Pre-build alignment check — working-tree snapshot, the §5.7
   collision-check result, pattern-file confirmation.
3. What was built, per §5 sub-section — concise; the code is
   the artefact, the report describes deltas and choices.
4. §7.2 post-baselines + §7.3 spot-check transcript.
5. Findings — numbered (f#1, f#2, ...), each with what was
   observed, why it matters, and NO remediation design (triage
   is the next Chat session's work). The §5.6 import-linter
   inconsistency lands here.
6. Self-assessment — anything that didn't fit, deviations from
   sequencing, length-overrun flags.
7. Final `git status --short` output.

Length anticipation: 200–400 lines. The report does NOT
contain: recommendations, next-brief proposals, redesign
suggestions, or commentary on other workstreams.

---

## §9 — Hard limits (non-negotiable)

**Not in scope — do not build, do not touch:**

- The hedge-classification ENGINE: no auto-classification flow,
  no settlement+24h timer, no Burst Review / operator surface,
  no wiring into settlement or bet-entry code paths. Nothing
  outside the log writes events in this session except tests.
- A `hedge_state` column on `bets` — explicitly excluded; lands
  with the engine later per the DR-025 S139 amendment.
- W12.1 / W12.2 territory: no edits to balance derivation,
  staking, record_builder, bets schema, or commission handling.
- Additional ops event types beyond
  `hedge_state_classification`.
- The top-level root `ops/` package — no edits, no contents, no
  removal.
- `.importlinter` beyond the single §5.6 modules addition — do
  NOT add promos/cash_flow/balances to the independence
  contract; surface as a finding only.
- Alembic / migration framework (DR-031 defers it); use the
  inline `apply_migrations` pattern.
- Named debt (test-coverage gaps elsewhere, monolithic files):
  not this brief's problem.
- Refactors / tidy-ups in passing, including in the cash_flow /
  promos modules being mirrored.

**Single bounded session.** If the work does not fit one
session, stop at a coherent boundary and record it as a
finding — partial-but-coherent beats complete-but-lost.

**No mid-session operator escalation.** Surprises become report
findings; Code runs end-to-end.

**Dirty-tree git discipline** (load-bearing — the entire W12+
build region is untracked/modified; this is expected state, not
drift):

- No `git add`, `git commit`, `git stash`, `git restore`,
  `git checkout` (file-targeted), `git reset`.
- Read working-tree state at session start (§7.1).
- The tree as of S141 drafting: ~10 modified + ~30 untracked
  paths (the W10–W14 build + W12 region). **The W12.1 surgical
  fix may have executed before this session runs** — if so,
  additional expected modifications exist on
  `store/schema/bets.py`, `domain/bets/__init__.py`,
  `store/repositories/bets.py`,
  `workflows/bet_entry/v1/record_builder.py`,
  `workflows/balances/v1/balance_derivation.py`, plus a new
  W12.1 test file. All expected; not drift; not W15's concern.
  W15's anchors are disjoint from all of them.
- Edit only the §5 anchors. After each edit to the two existing
  files (`store/__init__.py`, `.importlinter`), run
  `git diff <file>` to confirm only intended changes landed.
- At session close, `git status --short` per §7.2 — delta is
  exactly the named new files + the two named edits.

**Module boundaries (DR-030):** `domain/` and `store/` import
stdlib only (no project imports); `workflows/` may import
`domain` and `store`. The new modules introduce no
cross-boundary imports beyond that. `lint-imports` green is the
mechanical check.

---

## §10 — What happens after Code's session

The next operator-Claude Chat session reads
`w15_ops_log_report.md` and triages:

- Green and clean → W15 closes. The operations log exists and
  is ready for its first real writer.
- Findings (the import-linter inconsistency is expected; the
  §5.7 collision check, payload-shape strain, or anything
  else) → triage; decide whether a W15.1 follow-up is
  warranted.
- The **classifier engine** (auto-classification flow,
  settlement+24h auto-resolve, `hedge_state` column, Burst
  Review surface) lands later with the racing / burst-review
  screens per the DR-025 S139 amendment sequencing point (c).
  Code does NOT write that brief.
- The **W12.2 commission-source reconciliation** is a separate
  tracked brief, unrelated to W15's output.

---

## §11 — Cross-references

- **Scope / decision:** DR-025 (hedge classification, six-state
  model) + its 2026-05-22 Session 139 amendment in
  `decisions.md` — the states, the path-indicator requirement
  ("operations log captures the path to terminal state"), and
  the sequencing that bounds W15 to the audit-event shape only.
- **DRs invoked:** DR-030 (repo layout / module boundaries —
  the per-domain pattern home and the import-linter contracts),
  DR-031 (tech stack; Python 3.12+; Alembic deferred), DR-032
  (canonical bet record — `bet_id` / `cycle_id` scope), DR-019
  (derive-on-read — context for why the log stores
  classifications as events, not as mutable state), DR-021
  (Adelaide-local timestamps).
- **Architecture:** §A.2 (per-domain event log spine + common
  event header), §A.6 (hedge-state deferred block).
- **Pattern authority:** the shipped W14 code
  (`store/schema/cash_flow.py` docstring names W15 explicitly)
  and the W13 second instance.
- **Prior artefacts:**
  `dr029/w15_ops_log/_drafts/SESSION_140_drafts.md` (the
  grounding this brief executes);
  `dr029/w14_cash_flow/w14_cash_flow_brief.md` and
  `dr029/w13_promos/w13_promos_brief.md` (precedent briefs);
  `sessions/SESSION_140.md` (grounding session record).
- **Excluded items (tracked elsewhere):** the classifier engine
  + `hedge_state` column (DR-025 sequencing point (c), lands
  with W8/W17 surfaces); W12.2 commission-source
  reconciliation (own brief); Alembic adoption (sequenced after
  W12 + W15); the import-linter under-population question
  (finding → triage).

**End of brief.**
