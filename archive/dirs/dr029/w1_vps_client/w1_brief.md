# W1 — `vps_client` v1.0 implementation: Code brief

**Status:** Drafted Session 83. Locked at operator sign-off.
**Audience:** Claude Code, single bounded session.
**Output:** `dr029/w1_vps_client/w1_implementation_report.md`.

---

## §1 — What this brief is and is not

This brief commissions Claude Code to implement
`vps_client` v1.0 against the locked contract at
`dr029/2_7_api_contract_versioning/vps_client_contract.md`,
into `bethub-v3/clients/vps_client/v1/` (the empty stub
W0 created).

Scope: implement the typed envelope module (§8 of the
contract), six call surfaces (§9.1 race metadata, §9.2
runner metadata, §9.3 results, §9.4 bracketing, §9.5
BSP/sp_near/sp_far, §9.6 identifier-resolution sanity
check), error-mapping from raw `capture.db` query
exceptions to the closed `UnavailableReason` set, SQL
queries grounded in `capture.db`'s actual schema, and a
local SQLite fixture file under `tests/fixtures/` with
hand-crafted rows covering each envelope status per
surface. Tests run against the fixture; the live VPS is
read once during the session for schema introspection,
not for ongoing test runs.

Out of scope: any change to the contract itself (§2.7
versioning discipline forbids contract edits during
implementation — surfaces as findings if the contract is
ambiguous), `betfair_client` work (W2), the operational
store (W6), any v3 module that consumes `vps_client`
(W4 onwards), CLV reconstruction or other analytical
derivation (§11.4 of the contract — derivation layer,
not `vps_client`).

This is a single bounded Code session. Surprises become
findings in §11 of the report, not blockers — Code does
not pause mid-session for operator-Claude direction.
Remediation of any findings routes to the next
operator-Claude session's triage, not to Code's report
proposing fixes.

---

## §2 — Why this work exists

W1 is the first build session that produces v3 code that
does work. W0 (closed Session 83) initialised the repo
skeleton; every folder, dependency, and toolchain rule
is in place but nothing computes. W1 fills the
`vps_client` v1.0 stub — v3's read interface against the
analytical-line database (`capture.db`) on the VPS.

`vps_client` is the first build target because every
other v3 stream depends on it directly or transitively:
W4 (bet entry) needs identifier-resolution sanity
checks at placement; W5 (settlement worker) needs
results reads; W6 (operational store) needs race
metadata for bet-card display; W7 (burst review) needs
bracketing reads for market-curve display. Implementing
`vps_client` first means the rest of v3 build proper
has a working dependency to build against.

The implementation discipline is structural: per DR-027
(the two-database architecture decision: BetHub owns
operational state, capture.db owns analytical/source
data, no shared tables, integration by reference only)
and DR-028 (the cross-database integration boundary
discipline: no caching, no denormalisation, no second
integration point), `vps_client` is the *only* file in
v3 that knows `capture.db`'s schema. Every SQL query
against `capture.db` lives inside this module; v3
modules import typed return shapes but never see column
names. If `capture.db` changes schema in future, only
`vps_client` touches.

---

## §3 — Pre-reads

Required reads before Code starts:

1. `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/vps_client_contract.md`
   — the locked v1.0 contract Code is implementing
   against. §7 onwards is the developer-readable
   formal specification. Code implements §8 (typed
   envelope) and all six surfaces in §9, plus respects
   §10 (versioning mechanics) and §11 (out-of-scope).

2. `/Users/tim/Desktop/Projects/bethub-rebuild/standing_instructions.md`
   — Category 3 (filesystem and tooling discipline).
   Desktop Commander as default,
   write-script-to-`/tmp` + `start_process` over
   interactive REPL paste, dry-run multi-target
   mechanical edits before write.

3. `/Users/tim/Desktop/Projects/bethub-rebuild/decisions.md`
   — DR-027 (the two-database architecture decision)
   and DR-028 (cross-database integration boundary
   discipline). Read for the structural rationale
   that drives §11 ("no SQL outside `vps_client`").

Reference-only — Code reads on demand, not required
up-front:

- `dr029/2_7_api_contract_versioning/contracts_spec_brief.md`
  and `contracts_spec_report.md` — the Session 77
  Code session that drafted the developer-readable
  spec. Useful if Code wants to understand why
  certain shapes look the way they do.

- `dr029/w0_repo_init/w0_brief.md` and
  `w0_implementation_report.md` — repo skeleton
  context; references for the `import-linter` rules
  Code is now subject to as the first non-stub
  module.

---

## §4 — System access

Filesystem access — read-write:

- `/Users/tim/Desktop/Projects/bethub-v3/` — Code
  populates `clients/vps_client/v1/` (currently
  empty) and adds tests under `tests/`. Code does
  not modify any other folder beyond the named
  paths in §5.

VPS access — read-only, one-shot:

- `root@187.77.183.9` via SSH (operator's standing
  access). Code reads `capture.db`'s schema from
  `/home/racing/racing-data-capture/data/capture.db`
  via `start_process` Python at the canonical path
  per standing instructions Cat 3 (live database
  queries via Desktop Commander start_process with
  Python — never copy the file).

  This is a one-shot read for schema introspection.
  Code does not maintain an SSH tunnel; once the
  schema is captured to a reference doc (§5.1),
  the session continues offline.

  If SSH is unreachable at session start, that is a
  §11 finding and Code halts after §6 step 1 —
  without the schema, the SQL implementation cannot
  ground correctly. Operator confirms SSH is
  expected to be up at session start.

Database access — read-only:

- `capture.db` on VPS, schema introspection only
  (`PRAGMA table_info`, `sqlite_master` queries).
  Code does not read row data from the live DB; row
  data lives in the local fixture (§5.5).

Local toolchain — `uv` per W0. All Python invocations
via `uv run python ...` or `uv run pytest ...`. The
existing `.venv/` from W0 is the runtime; Code does
not create a second venv.

---

## §5 — Substantive scope

Five sub-sections covering the implementation work in
dependency order: schema introspection (informs SQL),
envelope module (foundational), call surfaces (the six
of them), error mapping (cross-cutting), test fixture
+ verification suite (verifies all of the above).

### §5.1 Schema introspection (one-shot VPS read)

Code reads `capture.db`'s schema once at session start
and writes a reference document at
`dr029/w1_vps_client/capture_db_schema.md`. The
document captures:

- Every table the contract's six surfaces reference
  (race metadata, runner metadata, results,
  bracketing, BSP/sp_near/sp_far, identifier
  resolution).
- Column names, types, nullable flags, and primary
  keys for those tables.
- Any `WITHOUT ROWID` declarations or unusual
  configurations.
- Indexes that the SQL queries should plan against.

The reference doc is the bridge between the contract
(which speaks in semantic field names like
`distance_metres`, `track_condition`) and the SQL
implementation (which speaks in `capture.db`'s actual
column names). Where the contract field name and the
column name differ, the doc maps them.

This reference doc lands in the rebuild folder
(`dr029/w1_vps_client/`) — not in the v3 repo. It is
governance material informing W1, not v3 code.

### §5.2 Envelope module (`envelope.py`)

Implement the typed envelope shapes from contract §8
into `bethub-v3/clients/vps_client/v1/envelope.py`:

- `EnvelopeStatus` enum (`fresh`, `stale`,
  `unavailable`).
- `UnavailableReason` enum (the five reasons
  exactly as named in §8.2).
- `FreshEnvelope[T]`, `StaleEnvelope[T]`,
  `UnavailableEnvelope` Pydantic v2 models per §8.3.
- `Envelope` type alias as the discriminated union
  of the three.

All three concrete envelope shapes are generic over
`T: BaseModel` per §8.3. `as_of` timestamps are
Adelaide local per DR-021 (timestamp anchoring,
Adelaide local time) — the module documents this in
its docstring and uses
`zoneinfo.ZoneInfo("Australia/Adelaide")`
consistently.

This module is imported by every surface module
(§5.3) and by tests (§5.5).

### §5.3 Call surfaces (six modules)

Each contract §9 sub-section maps to one module file
under `bethub-v3/clients/vps_client/v1/`:

| Contract § | Module file | Public function |
|---|---|---|
| §9.1 | `race_metadata.py` | `race_metadata(event_id: str) -> Envelope[RaceMetadata]` |
| §9.2 | `runner_metadata.py` | per contract §9.2 signature |
| §9.3 | `results.py` | per contract §9.3 signature |
| §9.4 | `bracketing.py` | per contract §9.4 signature |
| §9.5 | `starting_price.py` | per contract §9.5 signature |
| §9.6 | `identifier_resolution.py` | per contract §9.6 signature |

Each module contains:

- The Pydantic v2 return-shape model exactly as
  named in the contract (`RaceMetadata`,
  `RunnerMetadata`, etc.).
- The SQL query (or queries) against `capture.db`,
  parameterised, no string concatenation of user
  input.
- The public function with the exact signature from
  the contract.
- Mapping from raw DB query results to the typed
  return model (handling nullable fields per
  contract).
- Mapping from query exceptions to envelope
  statuses (cross-cutting; see §5.4).

The `__init__.py` in `clients/vps_client/v1/`
re-exports the six public functions plus the
`Envelope` type so v3 modules import via
`from clients.vps_client.v1 import race_metadata,
Envelope` rather than reaching into module files.

The single shared database connection lives in
`clients/vps_client/v1/_connection.py` — a private
module (leading underscore signals "internal to
this package"). It exposes a context manager that
opens a read-only SQLAlchemy connection to
`capture.db` at the path passed in (real path on
VPS, fixture path in tests; see §5.5). Each surface
uses this to run its SQL.

### §5.4 Error mapping

The cross-cutting discipline that turns raw SQLite
exceptions and connection failures into the closed
`UnavailableReason` set. Implementation lives in
`clients/vps_client/v1/_errors.py` (private module).

Mapping rules:

| Raw condition | Maps to | `retry_after` |
|---|---|---|
| `OperationalError("database is locked")` | `CAPTURE_DB_LOCKED` | 5 seconds |
| `OperationalError` other (file not found, IO) | `VPS_UNREACHABLE` | 60 seconds |
| Query returns zero rows | `GENUINE_ABSENCE` if id resolves cleanly; `NOT_YET_CAPTURED` if within ingestion-lag window; `NOT_IN_CAPTURE_WINDOW` if outside captured range | per the contract §8.3 |
| Query returns row with `as_of` older than freshness target | wraps in `StaleEnvelope` not `UnavailableEnvelope` | n/a |

The "is this within ingestion lag, outside the
capture window, or genuinely absent" distinction is
surface-specific and the contract delegates the
call to the implementation. For W1, Code uses the
simplest defensible heuristic per surface and
documents the heuristic in the module docstring.
Refinement comes in later versions if operational
experience surfaces mis-classification.

### §5.5 Test fixture + verification suite

Local SQLite fixture file at
`bethub-v3/tests/fixtures/capture_db_fixture.sqlite`.
Code generates the fixture from a Python builder
script (`tests/fixtures/build_capture_fixture.py`)
that creates the same tables `capture.db` has (per
§5.1 schema introspection) and inserts hand-crafted
rows covering each envelope status per surface.

Builder script is reproducible: running it from a
clean state produces a byte-identical fixture file.
The fixture file itself is committed (small, stable);
the builder is the source of truth.

Verification suite under
`bethub-v3/tests/clients/vps_client/v1/`:

- `test_envelope.py` — envelope shapes serialise
  correctly, status discrimination works, generic
  type parameter is honoured.
- `test_race_metadata.py` — surface returns
  `fresh` for present-and-current row, `stale` for
  present-but-lagged row, `unavailable` for each of
  the five reasons. One test per envelope status
  per surface.
- ... five more `test_<surface>.py` files, same
  shape.
- `test_error_mapping.py` — the cross-cutting
  mapping rules from §5.4. Mocks the underlying
  connection where needed to simulate
  `OperationalError` etc.

Test count target: roughly 50–70 tests total (8 per
surface × 6 surfaces, plus envelope shape tests,
plus error-mapping tests). Range, not hard line —
Code exceeds with rationale or undershoots with
rationale, flagged in §12 self-assessment.

---

## §6 — Sequencing within session

Code does the work in this order:

1. **Pre-flight: SSH to VPS, run schema
   introspection.** If SSH up, capture schema to
   `dr029/w1_vps_client/capture_db_schema.md` and
   continue to step 2.

   If SSH unreachable, **halt before touching
   `bethub-v3/` at all** — do not create the
   schema doc, do not edit any v3 file, do not
   build the fixture. Write a minimal report
   containing only §1 anchor, §2 pre-flight
   failure detail (what was tried, what failed,
   timestamps), §11 with a single finding naming
   the SSH issue, and §13 anchor. Exit cleanly.
   The operator restores VPS access and re-runs
   W1 against the same locked brief; the v3 repo
   stays in the W0-clean state for the re-run.

2. **Implement `envelope.py`.** Pydantic models
   per §5.2. Smoke test with
   `uv run python -c "..."` to confirm models
   instantiate.

3. **Build the test fixture.** Write
   `tests/fixtures/build_capture_fixture.py`, run
   it, confirm `capture_db_fixture.sqlite` lands.
   Verify schema matches §5.1 introspection.

4. **Implement the six call surfaces in dependency
   order.** Recommended order:
   - `race_metadata.py` (simplest; no joins).
   - `runner_metadata.py` (similar shape).
   - `results.py` (results table joins).
   - `starting_price.py` (single-point reads).
   - `bracketing.py` (time-series window).
   - `identifier_resolution.py` (passive sanity
     check; touches multiple tables).

   For each surface: write the module, write its
   test file, run
   `uv run pytest tests/clients/vps_client/v1/test_<surface>.py`
   green before moving on.

5. **Implement `_errors.py` cross-cutting mapping.**
   Run the error-mapping test file green.

6. **Wire up `__init__.py` re-exports.** Verify
   import path works:
   `uv run python -c "from clients.vps_client.v1
   import race_metadata, Envelope"`.

7. **Final verification sweep:**
   - `uv run ruff check` — exits 0.
   - `uv run mypy .` — exits 0.
   - `uv run lint-imports` — five contracts kept,
     zero broken.
   - `uv run pytest -v` — all tests pass; new
     tests plus the six W0 skeleton tests.
   - `git status` — only intended files changed.

8. **Single git commit** covering everything in
   this session. Commit message: `W1: vps_client
   v1.0 implemented per locked contract (§9.1–§9.6
   + envelope + error mapping + fixture + tests)`.

If the work runs over budget at step 4 (any
surface taking longer than expected), Code finishes
the current surface and surfaces the remainder as
a §11 finding rather than continuing past budget.
Partial implementation with clean coverage on
what's done beats complete-but-untested
everything.

---

## §7 — Empirical verification

Success criteria — every criterion must pass clean
for the report to mark verification as passed:

1. `bethub-v3/clients/vps_client/v1/envelope.py`
   exists; envelope models instantiate without
   error.
2. All six surface modules exist at named paths;
   each exports the public function with the
   signature from the contract.
3. `bethub-v3/tests/fixtures/capture_db_fixture.sqlite`
   exists and is non-empty.
4. `bethub-v3/tests/fixtures/build_capture_fixture.py`
   exists; running it from clean state produces
   the committed fixture.
5. `uv run ruff check` exits 0 with no findings.
6. `uv run mypy .` exits 0 with no findings.
7. `uv run lint-imports` exits 0 with five
   contracts kept, zero broken.
8. `uv run pytest -v` exits 0; six W0 skeleton
   tests still pass; all new W1 tests pass; total
   test count is within the §5.5 target range or
   has a §12 rationale.
9. Schema reference doc exists at
   `dr029/w1_vps_client/capture_db_schema.md`.
10. `git log` shows exactly one commit on the main
    branch with the §6 step 8 message.

---

## §8 — Output spec

Single output file:
`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w1_vps_client/w1_implementation_report.md`.

Section structure:

- §1 — Anchor (session start, Adelaide local).
- §2 — Pre-flight (SSH reachability, VPS state).
- §3 — Schema introspection summary (table counts,
  notable schema shapes).
- §4 — Envelope module summary.
- §5 — Per-surface implementation summary (one
  sub-section per surface; SQL shape, edge cases
  encountered, test coverage).
- §6 — Error mapping summary.
- §7 — Fixture summary (rows per surface, status
  coverage).
- §8 — Final verification (verbatim output of
  every §7 success criterion check).
- §9 — Git state.
- §10 — Pass/fail status table for §7's success
  criteria.
- §11 — Findings (in F1, F2, ... format like W0).
- §12 — Self-assessment (Did Code stay within
  named anchors? Out-of-band actions? Did the
  session fit bounded scope? Anything next
  operator-Claude session should know that the
  report doesn't otherwise capture?).
- §13 — Anchor (session close, Adelaide local).

Length anticipation: ~600–900 lines. Range, not
hard line — exceed with rationale in §12.

The report does NOT contain:

- Recommendations for the next brief.
- Proposed contract edits.
- Speculation about W2+ scope.
- Performance benchmarks or load testing (W1 is
  correctness, not performance).

---

## §9 — Hard limits — what's NOT in scope

Non-negotiable exclusions:

- **No contract edits.** §2.7 versioning discipline
  is immutable during implementation. If the
  contract is genuinely ambiguous, surface as a §11
  finding; Code does not edit
  `vps_client_contract.md` even to fix typos.
- **No `betfair_client` work.** That's W2.
- **No operational-store work, no schema for v3's
  own database.** That's W6.
- **No v3 modules consuming `vps_client`.** Bet
  entry, settlement, burst review — all W4 onwards.
- **No CLV reconstruction or analytics-derived
  fields** per contract §11.4. `vps_client`
  returns raw inputs; derivation is a separate
  layer.
- **No new dependencies beyond what W0 installed.**
  If a new library is genuinely needed, surface as
  §11 finding rather than installing.
- **No global Python state changes** (operator's
  system Python 3.11.9 stays untouched per W0
  Finding F1 substrate). All work via `uv run`.
- **No commits beyond step 8.** Single commit at
  session end. If toolchain checks need
  adjustment, apply them before step 8 — do not
  amend after. Substrate: W0 Finding F5.
- **No write access to `capture.db`.** Read-only,
  schema introspection only.
- **No operator escalation mid-session.** Code
  runs end-to-end, surfaces findings in the
  report, doesn't ping operator-Claude mid-flight
  asking for direction.

---

## §10 — What happens after Code's session

Next operator-Claude session reads
`w1_implementation_report.md` end-to-end, then:

1. **Triage §11 findings** per
   `bethub-brief-drafting` skill §10. Classify
   each finding (cosmetic / blocking /
   scope-question / drift); route to W2
   carry-forward, micro-brief, operator decision,
   or accepted.
2. **Triage §12 self-assessment.** Surface
   anything Code flagged about brief shape or
   session strain.
3. **Confirm W2 has clean foundation.** If yes,
   W2 brief drafting opens (`betfair_client` v1.0
   implementation against the locked contract).
   If no, micro-brief or operator-side correction
   first.

Code does NOT produce the W2 brief. That's
operator-Claude work, drawing on the W1 report
plus the locked `betfair_client_contract.md`.

---

## §11 — Cross-references

- **Contract:**
  `dr029/2_7_api_contract_versioning/vps_client_contract.md`
  (locked Session 75 + Session 77 + Session 78).
  v1.0 immutable; W1 implements against it.
- **DRs invoked:**
  - DR-027 (the two-database architecture
    decision: BetHub owns operational state,
    capture.db owns analytical/source data).
  - DR-028 (the cross-database integration
    boundary discipline decision: no caching,
    no denormalisation, no second integration
    point).
  - DR-019 (derived state on read) —
    load-bearing for §11.4's "no
    analytics-derived fields in `vps_client`"
    exclusion.
  - DR-021 (timestamp anchoring, Adelaide
    local time) — applies to envelope `as_of`
    plus all report timestamps.
  - DR-030 (v3 repo layout) — `vps_client`
    lives in `clients/` per DR-030 layered
    architecture; `import-linter` enforces.
  - DR-031 (v3 tech stack) — Pydantic v2,
    SQLAlchemy 2.0, mypy strict.
- **Prior session record:** `sessions/SESSION_82.md`
  (W0 brief drafting); `sessions/SESSION_83.md`
  (this session — W0 triage + W1 brief drafting).
- **Prior report:**
  `dr029/w0_repo_init/w0_implementation_report.md`
  — W0's foundation that W1 builds on.
- **Parking-lot items excluded from W1 scope:**
  - `betfair_client` v1.0 implementation (W2).
  - Operational store schema (W6).
  - Live pricing / Streaming (W3).
  - Bet entry write surfaces (W4).
  - Settlement worker (W5).
  - Burst review workflow (W7).
  - Cutover (W8).
  - §2.10 bucket-1 backward-compatible
    additions (P1, post-build).
  - Analytical layer scoping (P2,
    post-build).
