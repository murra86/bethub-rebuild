# W0 — v3 repo skeleton initialisation brief

**Status:** Locked Session 82.
**Audience:** Claude Code, single bounded session.
**Output:** `dr029/w0_repo_init/w0_implementation_report.md`.

---

## §1 — What this brief is and is not

This brief commissions Claude Code to initialise the v3 repo
skeleton at `/Users/tim/Desktop/Projects/bethub-v3/`, per
DR-030 (v3 repo layout) and DR-031 (v3 tech stack). The
deliverable is an empty but verified foundation that every
subsequent W-stream brief will build into.

Scope: create the folder layout, install the locked
dependencies, configure the toolchain (pytest, ruff,
import-linter, Alembic), populate empty `__init__.py` module
stubs, and write a minimal verification suite that proves the
skeleton works end-to-end.

Out of scope: any business logic, any contract implementation
(`vps_client`, `betfair_client`, repositories, domain modules
all remain empty stubs), any UI work, any migration content
beyond Alembic's initial scaffolding, any external API
connectivity.

This is a single bounded Code session. Surprises become
findings in the report, not blockers — Code does not pause
mid-session for operator-Claude direction. Remediation of any
findings routes to the next operator-Claude session's triage,
not to Code's report proposing fixes.

---

## §2 — Why this work exists

v3 build proper is unblocked post-DR-029 close (Session 78).
DR-030 (v3 repo layout) and DR-031 (v3 tech stack) locked at
Session 79 specify what v3 looks like architecturally; no v3
code exists yet. Every W-stream brief from W1 onward assumes
the repo skeleton is in place — folder layout per DR-030,
import-graph rules enforced, dependencies installed, test
harness operational.

W0 separates "set up the repo" from "build the contract" so
W1 (`vps_client` v1.0 implementation) can run as a focused
single-purpose session against a verified foundation. v2's
structural debt traces partly to absent import-graph
discipline that accumulated quickly because the rules weren't
enforced from day 0; v3 starts with `import-linter` green
from the first commit so the discipline is the floor, not a
goal.

This is the foundational session that every subsequent
W-brief inherits. Getting it right once means W1 through
W-final sit on the same verified skeleton.

---

## §3 — Pre-reads

Required reads before Code starts:

1. `/Users/tim/Desktop/Projects/bethub-rebuild/decisions.md`
   - DR-030 (v3 repo layout) — lines 951–1031.
   - DR-031 (v3 tech stack) — lines 1032–1076.
   These are the architectural specs Code builds against.

2. `/Users/tim/Desktop/Projects/bethub-rebuild/standing_instructions.md`
   - Category 3 (filesystem and tooling discipline). Desktop
     Commander as default, write-script-to-`/tmp` +
     `start_process` over interactive REPL paste, dry-run
     multi-target mechanical edits before write.

Reference-only — Code reads on demand, not required up-front:

- `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/vps_client_contract.md`
  The locked v1.0 contract that W1 will fill into
  `clients/vps_client/`. W0 doesn't implement against it;
  included so Code can verify the empty stub's import path
  matches the contract's expected Python module structure
  (`vps_client.v1.race_metadata`, etc.).

- `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  Same purpose for `clients/betfair_client/` stub.

No pre-flight grounding step before Code starts (the Mac
filesystem is empty at the v3 path; nothing to probe).

---

## §4 — System access

Filesystem access — read-write:

- `/Users/tim/Desktop/Projects/bethub-v3/` — Code creates this
  directory and everything below it. The directory does not
  exist before this session.

Filesystem access — read-only:

- `/Users/tim/Desktop/Projects/bethub-rebuild/` — required
  reads (DR-030, DR-031, standing_instructions.md Cat 3) plus
  reference-only contract files. Code does not modify any
  rebuild folder content.

External system access:

- None. W0 does not connect to `capture.db`, Betfair API, the
  VPS, or any external service. The skeleton being built has
  no external connectivity until W1+ wires in `vps_client`
  and `betfair_client`.

Tooling access — read-write:

- Python 3.12+ environment. Code installs the DR-031 stack
  via `uv` into a v3-local virtual environment at
  `bethub-v3/.venv/`. Global Python state is not modified.
- `git`. Code initialises `bethub-v3/` as a git repo
  (`git init`), configures `.gitignore`, and makes the first
  commit at session end (see §6 sequencing). No pushes, no
  remotes — local repo only at this stage.

Timestamps:

- All timestamps in the implementation report use Adelaide
  local time (ACST/ACDT) per DR-021. Code anchors at session
  start via:
  ```
  TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
  ```

---

## §5 — Substantive scope

### §5.1 — Folder layout per DR-030

Code creates the following directory structure under
`/Users/tim/Desktop/Projects/bethub-v3/`, exactly matching
DR-030's locked layout:

```
bethub-v3/
├── clients/
│   ├── __init__.py
│   ├── vps_client/
│   │   ├── __init__.py
│   │   └── v1/
│   │       └── __init__.py
│   └── betfair_client/
│       ├── __init__.py
│       └── v1/
│           └── __init__.py
├── store/
│   ├── __init__.py
│   ├── schema/
│   │   └── __init__.py
│   └── repositories/
│       └── __init__.py
├── domain/
│   ├── __init__.py
│   ├── bets/
│   │   └── __init__.py
│   ├── settlement/
│   │   └── __init__.py
│   └── pricing/
│       └── __init__.py
├── workflows/
│   ├── __init__.py
│   ├── bet_entry/
│   │   └── __init__.py
│   └── burst_review/
│       └── __init__.py
├── ui/
│   └── (empty — populated in later W-stream)
├── ops/
│   └── __init__.py
├── contracts/
│   └── (empty — locked contract files relocate here at
│         DR-029 close per DR-030 scope; W0 leaves empty)
└── tests/
    ├── __init__.py
    ├── conftest.py            (empty pytest fixture file)
    └── test_skeleton.py       (verification suite — see §5.5)
```

Every Python module folder gets an empty `__init__.py`. `ui/`
and `contracts/` are deliberately empty — `ui/` is populated
by a later frontend-focused W-stream, `contracts/` holds the
locked contract files that relocate from `dr029/` at DR-029
administrative close.

Code does NOT create any other files in these folders. No
placeholder Python modules with TODO comments, no stub
functions, no schema files, no domain logic. The folders are
scaffolding; filling them is W1+ work.

### §5.2 — Dependencies and `pyproject.toml`

Code creates `/Users/tim/Desktop/Projects/bethub-v3/pyproject.toml`
defining the project metadata and the locked DR-031 stack.

Project metadata:

- `name = "bethub"`
- `version = "0.1.0"`
- `requires-python = ">=3.12"`
- `description = "BetHub v3 — Australian bookmaker account
  management platform"`

Runtime dependencies (DR-031 locked stack):

- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server for FastAPI
- `pydantic` — typed return shapes (per `vps_client` contract
  §7 tech-stack assumption)
- `sqlalchemy` — Core query builder, not ORM
- `alembic` — migration framework
- `betfairlightweight` — Betfair Streaming + Exchange API
  (carried forward from v2)
- `httpx` — HTTP client (FastAPI-native, async-friendly)

Dev dependencies (separate group, installed via
`uv sync --all-extras`):

- `pytest`
- `pytest-asyncio`
- `ruff`
- `import-linter`
- `mypy` — static type checking, paired with Pydantic

Code does not pin exact versions in `pyproject.toml` — it
specifies `>=` floors only. `uv.lock` captures exact resolved
versions for reproducibility. `uv.lock` is committed to the
repo.

Code creates a `.python-version` file at the repo root pinning
Python 3.12 for `uv`.

Code does NOT add any dependency not listed above. If a
transitive dependency surfaces as needed during the
verification suite (§5.5), that's a finding for the
implementation report — not an in-session addition.

### §5.3 — Toolchain configuration

Code creates configuration files for the four toolchain
components that run on every commit and on every test run.

**ruff** (lint + format):

- Configuration in `pyproject.toml` under `[tool.ruff]`.
- Line length: 100 (Python community drift away from 88-char
  default; reads better on modern monitors).
- Target Python version: `py312`.
- Default rule set plus E, F, I (imports), B (bugbear), UP
  (pyupgrade), N (naming).
- Format on save assumed (operator's editor config, not
  enforced in repo).

**mypy** (static type checking):

- Configuration in `pyproject.toml` under `[tool.mypy]`.
- Strict mode enabled (`strict = true`) — catches every type
  leak from day 0 rather than retrofitting later.
- Plugin: `pydantic.mypy` (Pydantic v2 model integration).

**pytest** (testing):

- Configuration in `pyproject.toml` under
  `[tool.pytest.ini_options]`.
- `testpaths = ["tests"]`.
- `asyncio_mode = "auto"` (pytest-asyncio handles async tests
  without per-test decorators).
- Minimum verbosity at `-v`.

**import-linter** (DR-030 import-graph enforcement):

- Configuration in `.importlinter` at repo root.
- Defines the eight DR-030 layers (`ui`, `ops`, `workflows`,
  `domain`, `store`, `clients`, `contracts`, `tests`) as a
  directed graph.
- Encodes the four core rules from DR-030:
  1. `domain` imports nothing.
  2. `workflows` cannot import `workflows`.
  3. `store` imports nothing (no domain leak into data
     access).
  4. `contracts` is leaf (imports nothing).
- Plus the down-only direction: `ui`/`ops` → `workflows` →
  `domain`/`store`/`clients` → `contracts`.

Code does not configure pre-commit hooks in W0 — that's
operator-side workflow setup, not part of the build skeleton.
The toolchain runs on demand via `uv run ruff check`,
`uv run mypy`, `uv run pytest`, `uv run lint-imports`.

### §5.4 — `.gitignore` and repo hygiene files

Code creates standard repo hygiene files at the `bethub-v3`
root.

`.gitignore` — covers:

- `.venv/` (virtual environment, never committed)
- `__pycache__/` (Python bytecode cache)
- `*.pyc`, `*.pyo` (compiled Python)
- `.pytest_cache/` (pytest's internal cache)
- `.ruff_cache/` (ruff's internal cache)
- `.mypy_cache/` (mypy's internal cache)
- `*.db`, `*.db-wal`, `*.db-shm` (SQLite operational store;
  never committed regardless of contents)
- `.env`, `.env.local` (environment variables — secrets, API
  keys; never committed)
- `.DS_Store` (macOS filesystem artefact)
- `node_modules/` (frontend dep cache, when `ui/` lands)
- `dist/`, `build/` (frontend build output)

`README.md` — minimal:

- Project name and one-line description.
- Pointer to `/Users/tim/Desktop/Projects/bethub-rebuild/`
  for governance docs, decisions, scope.
- "How to set up locally" — `uv sync`, `uv run pytest`.
- DR-030 layout reference (one-line, not duplicated).

`LICENSE` — not created in W0. Single-operator project, not
public; licence question is parked.

Code does NOT create:

- `.env` or `.env.local` files (no secrets exist yet).
- `CONTRIBUTING.md` (single-operator project).
- `CHANGELOG.md` (versioning is per-contract per DR-030, not
  per-repo).
- GitHub-style files (`.github/`, `ISSUE_TEMPLATE/`, etc.) —
  no remote yet.

### §5.5 — Verification suite

Code creates `tests/test_skeleton.py` — the verification suite
that proves the W0 skeleton actually works. This is the
closest thing W0 has to a "deliverable" beyond folders and
config files: if these tests pass, the foundation is verified.

Six verification tests, each a single pytest function:

1. **`test_python_version_supported`** — confirms
   `sys.version_info >= (3, 12)`. Fails the build if someone
   runs the test suite under an older Python.

2. **`test_all_packages_importable`** — imports every package
   and subpackage created in §5.1:
   ```
   import clients
   import clients.vps_client
   import clients.vps_client.v1
   import clients.betfair_client
   import clients.betfair_client.v1
   import store
   import store.schema
   import store.repositories
   import domain
   import domain.bets
   import domain.settlement
   import domain.pricing
   import workflows
   import workflows.bet_entry
   import workflows.burst_review
   import ops
   ```
   Each import must succeed. This catches missing
   `__init__.py` files and typo'd folder names.

3. **`test_dependencies_importable`** — imports each runtime
   dependency from §5.2:
   ```
   import fastapi
   import uvicorn
   import pydantic
   import sqlalchemy
   import alembic
   import betfairlightweight
   import httpx
   ```
   Confirms `uv sync` actually installed everything.

4. **`test_pydantic_v2`** — confirms `pydantic.VERSION` starts
   with `"2."`. Guards against accidentally pulling Pydantic
   v1 (which has incompatible API; the `vps_client` contract
   spec assumes v2).

5. **`test_sqlalchemy_core_usable`** — constructs a trivial
   `sqlalchemy.Table` and a `select()` query against an
   in-memory SQLite engine. Confirms SQLAlchemy Core (not
   ORM) is wired up and operational.

6. **`test_import_linter_config_present`** — confirms
   `.importlinter` exists at repo root and parses as valid
   INI/TOML. Does NOT run the import-graph rules themselves
   — that runs separately via `uv run lint-imports`.

Code runs all six tests via `uv run pytest -v` as the final
in-session verification. Test output goes into the
implementation report (§8).

Separately, Code runs:

- `uv run ruff check` — must pass clean.
- `uv run mypy .` — must pass clean.
- `uv run lint-imports` — must pass clean (no rule violations
  on the empty skeleton).

Nine total checks (six pytest + three CLI tools). Code runs
all nine as the final verification. Failures surface as
findings, not blockers — the implementation report's job is
to surface them; the next operator-Claude session triages.
This is the discipline pattern from Sessions 35/36 — Code
reports, doesn't chase fixes.

---

## §6 — Sequencing within session

Code does the work in this order. Each step is a checkpoint
— if a step fails, the implementation report captures the
failure and Code does NOT proceed to subsequent steps that
depend on it.

1. **Anchor timestamp.**
   `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` via
   Desktop Commander `start_process`. Captured at the top of
   the implementation report.

2. **Pre-flight check.**
   Confirm `/Users/tim/Desktop/Projects/bethub-v3/` does NOT
   already exist. If it does, halt and surface as a finding
   — W0 assumes a clean slate. This protects against
   accidentally overwriting work that may have started
   out-of-band.

3. **Create folder layout (§5.1).**
   Create `bethub-v3/` root and every subfolder per the
   DR-030 layout. Populate `__init__.py` files. Verify the
   tree structure matches §5.1 exactly via `find` or
   `list_directory` before proceeding.

4. **Initialise uv project.**
   `cd` into `bethub-v3/`, run `uv init --no-readme` (the
   README gets written manually in step 7). Confirm
   `pyproject.toml` created and `.python-version` pinned to
   3.12.

5. **Install dependencies (§5.2).**
   Edit `pyproject.toml` to add the runtime and dev
   dependency groups. Run `uv sync --all-extras`. Confirm
   `uv.lock` created and `.venv/` populated. Verify each
   named dependency is importable via a quick `uv run python
   -c "import X"` sweep.

6. **Configure toolchain (§5.3).**
   Add `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`
   sections to `pyproject.toml`. Create `.importlinter` at
   repo root with the eight DR-030 layers and the four core
   rules. Run each toolchain command on the empty tree to
   confirm each tool is operational:
   - `uv run ruff check` (expect: pass clean)
   - `uv run mypy .` (expect: pass clean — empty tree,
     nothing to check)
   - `uv run lint-imports` (expect: pass clean — no imports
     yet)

7. **Create hygiene files (§5.4).**
   Write `.gitignore` at repo root. Write minimal `README.md`
   per the §5.4 spec.

8. **Write verification suite (§5.5).**
   Create `tests/conftest.py` (empty) and
   `tests/test_skeleton.py` with the six tests from §5.5.
   Run `uv run pytest -v`. Expect all six tests to pass.

9. **Initialise git.**
   `git init` at `bethub-v3/` root. Stage everything except
   `.gitignore`'d files (`git add .`). Verify `git status`
   shows only intended files via `git diff --cached --stat`.
   First commit message:
   `"W0: v3 repo skeleton initialised per DR-030 (layout) and DR-031 (stack)"`.

10. **Final verification sweep.**
    Re-run all nine checks from §5.5 in order, capturing
    output for the implementation report:
    - `uv run ruff check`
    - `uv run mypy .`
    - `uv run lint-imports`
    - `uv run pytest -v` (six tests)

    All nine must pass clean.

11. **Write implementation report (§8).**

**Why this order:** dependencies (step 5) before toolchain
config (step 6) because mypy and ruff need their target
Python environment in place to be configured. Toolchain
config before hygiene files (step 7) because ruff config can
affect what `.gitignore` rules are needed. Verification suite
(step 8) before git init (step 9) so the first commit
captures a verified-passing state.

---

## §7 — Empirical verification

W0 has no "before" state to baseline against — the v3 repo
does not exist before this session. Empirical verification is
single-state: confirm the post-build skeleton meets the named
success criteria.

Success criteria (all nine must hold for the session to
report clean):

1. `/Users/tim/Desktop/Projects/bethub-v3/` exists as a
   directory.
2. The folder structure under it exactly matches §5.1 (every
   named folder present, every named `__init__.py` file
   present, no unnamed extras).
3. `uv sync --all-extras` completed without resolution
   errors.
4. `uv.lock` exists and is non-empty.
5. `uv run ruff check` exits 0 with no findings.
6. `uv run mypy .` exits 0 with no findings.
7. `uv run lint-imports` exits 0 with no rule violations.
8. `uv run pytest -v` exits 0 with six tests passed, zero
   failed, zero skipped.
9. `git log` shows exactly one commit on the main branch
   with the message specified in §6 step 9.

Code captures the output of each verification command
verbatim in the implementation report.

If any criterion fails:

- Code does NOT attempt remediation in-session.
- The failure is captured as a finding in the report with
  full output (command, exit code, stderr/stdout).
- Subsequent dependent steps are skipped per §6.
- The report's overall status is "verification failed — see
  findings", not "verification passed".

W0 has no in-flight or out-of-session verification carve-outs.
Everything is verifiable inside the single Code session
against the local filesystem.

---

## §8 — Output spec

Single output file:

```
/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w0_repo_init/
    w0_implementation_report.md
```

(Code creates the `dr029/w0_repo_init/` directory if it does
not exist. The `dr029/` parent already exists in the rebuild
folder.)

**Note:** this output path lives inside the rebuild folder,
not inside `bethub-v3/` itself. The implementation report is
governance reference material; v3's repo holds only the code
and config. Operator-Claude reads from the rebuild folder in
the next session to triage.

Report structure (numbered §-sections):

- **§1 — Anchor.** Adelaide local timestamp at session start,
  per DR-021.
- **§2 — Pre-flight check.** Result of step 2 (clean-slate
  check). Either "v3 directory did not exist — proceeded" or
  "v3 directory existed — halted; see findings".
- **§3 — Folder layout.** Output of `find` or `tree` against
  `bethub-v3/` post-build. Confirms §5.1 compliance.
- **§4 — uv project initialisation.** Output of `uv init`,
  contents of generated `pyproject.toml` and
  `.python-version`.
- **§5 — Dependencies.** Final `pyproject.toml` dependency
  sections (runtime + dev). Output of `uv sync --all-extras`
  (truncated if very long — first and last 20 lines preserved
  with a `[N lines omitted]` marker). Output of the `uv.lock`
  first-line summary (package count). Output of the
  import-sweep verification.
- **§6 — Toolchain configuration.** Final `[tool.ruff]`,
  `[tool.mypy]`, `[tool.pytest.ini_options]` sections. Final
  `.importlinter` contents. Output of each toolchain
  command's first-run pass.
- **§7 — Hygiene files.** Final `.gitignore` contents. Final
  `README.md` contents.
- **§8 — Verification suite.** Final
  `tests/test_skeleton.py` contents. Output of
  `uv run pytest -v`.
- **§9 — Git initialisation.** Output of `git status`
  post-add, output of `git log` post-commit.
- **§10 — Final verification sweep.** Verbatim output of all
  nine final-sweep commands. Pass/fail status for each.
- **§11 — Findings.** Any deviation from clean execution.
  One sub-section per finding. Format:
  ```
  ### Finding F1: <one-line title>
  - Step where it surfaced: §X
  - Expected: <what should have happened>
  - Actual: <what happened>
  - Output: <verbatim>
  - Code's read: <one-paragraph plain-language assessment>
  - Code did NOT attempt remediation per §7 of brief.
  ```
  If no findings: "No findings — all nine verification checks
  passed clean."
- **§12 — Self-assessment.** Code's brief-adherence assessment:
  - Did Code stay within the named anchors? Yes / No, what
    drifted.
  - Were any out-of-scope items touched? Yes / No, what.
  - Did the session fit a single bounded run? Yes / No, where
    it strained.
  - Anything Code thinks the next operator-Claude session
    should know that the report doesn't otherwise capture.
- **§13 — Anchor.** Adelaide local timestamp at session
  close.

**Length anticipation:** 300–600 lines. Most of the length
will be verbatim command output captured in §§4–10.

The report does NOT contain:

- Recommendations for next steps (next-session triage owns
  that).
- Verdict on whether v3 is "ready to build" (operator-Claude
  judgement, not Code's).
- Comparison with v2 (out of scope).
- Any code modifications discovered "while we were here"
  (out of scope per §9 hard limits).

---

## §9 — Hard limits

Code does NOT do any of the following in this session.
Surfaces or temptations to do them are findings, not
in-session pivots.

**Out of scope — other workstreams:**

- W1 (`vps_client` v1.0 implementation). The
  `clients/vps_client/v1/__init__.py` file is created empty.
  No implementation, no imports from the contract spec, no
  Pydantic models, no endpoint signatures. W1 fills it in
  next.
- W2 onward (every later workstream). All workflow, domain,
  store, and `betfair_client` implementation is out of scope.
- `contracts/` relocation. The locked `vps_client_contract.md`
  and `betfair_client_contract.md` remain in
  `dr029/2_7_api_contract_versioning/` for now. Relocation to
  `bethub-v3/contracts/` is separate administrative cleanup.

**Out of scope — implementation:**

- No business logic in any module. Every `__init__.py` is
  empty.
- No SQL DDL, no migrations beyond Alembic init scaffolding.
- No Pydantic models defined.
- No FastAPI app instantiation.
- No SQLAlchemy engine creation outside the §5.5 verification
  test.
- No environment variable handling, no `.env` files.
- No logging configuration.
- No CLI entry points beyond what `uv init` creates.

**Out of scope — toolchain:**

- No pre-commit hooks. (§5.3 explicit.)
- No CI/CD configuration (`.github/`, GitLab CI, etc.).
- No Docker, no containerisation.
- No deployment scripts.
- No frontend toolchain (Vite, npm, `package.json`) — UI is
  a separate W-stream.
- No Alembic migration content beyond the empty `alembic/`
  scaffolding from `alembic init`. The first real migration
  lands when `store/schema/` is built.

**Out of scope — repo state:**

- No remote git configured. Local repo only.
- No branches beyond `main`. No tags.
- No `LICENSE` file.
- No GitHub-style files.

**Out of scope — the named pieces of debt:**

- Test coverage for v3 modules beyond the §5.5 skeleton
  suite. (Real test coverage lands per-module as W-streams
  build.)
- Migration framework population beyond Alembic scaffolding.
- Monolithic orchestrator file decomposition (this is a v2
  artefact; v3 starts clean).

**Out of scope — git operations:**

- No git commits beyond step 9 in §6.
- No `git push`, `git pull`, `git fetch` — no remote.
- No `git stash`, `git restore`, `git reset`, `git checkout`.
- No rebasing or history rewriting.

**Mid-session escalation:**

- Code does NOT pause mid-session to ping operator-Claude
  for direction. Surprises become findings in §11. The next
  operator-Claude session triages.

---

## §10 — What happens after Code's session

Code's session ends with the implementation report written
to `dr029/w0_repo_init/w0_implementation_report.md`. Code
does not produce the next brief.

**Next operator-Claude session triage:**

1. Read the report end-to-end.
2. Triage §11 (Findings). For each finding:
   - Classify: cosmetic / blocking / scope-question / drift.
   - Route: fixable in W1 (carry forward), needs its own
     micro-brief, needs operator-side decision, or close as
     accepted.
3. Triage §12 (Self-assessment). Surface anything Code
   flagged about brief shape or session strain — feeds back
   into how W1 onward briefs are scoped.
4. Confirm v3 skeleton is ready for W1. The triage's job is
   to answer one question: does W1 (`vps_client` v1.0
   implementation) have a clean foundation to build into?
   - Yes → W1 brief drafting opens.
   - No → fix the gap first (small follow-up brief or
     operator-side correction) before W1.
5. Update governance:
   - `sessions/SESSION_<N>.md` captures the triage outcome.
   - `current_state.md` updated to reflect W0 close, W1
     becoming next active workstream once foundation is
     confirmed.
   - `v3_build_picture.md`: W0 row goes done; W1 row remains
     in flight.
6. Open W1 brief drafting in the same session if foundation
   is clean, or carry forward to the next session if the
   triage runs long.

**Code does NOT:**

- Draft W1's brief.
- Propose what should change in v3 going forward.
- Surface architectural redirections or DR amendments.

---

## §11 — Cross-references

**Scope doc and DR anchors:**

- **DR-030** (v3 repo layout and module-boundary discipline)
  — `decisions.md` lines 951–1031. The locked layout that
  §5.1 builds, the four core import rules that §5.3's
  import-linter config encodes.
- **DR-031** (v3 tech stack — Python 3.12+ / FastAPI /
  SQLite WAL / SQLAlchemy Core / Alembic / React +
  TypeScript + Vite) — `decisions.md` lines 1032–1076. The
  locked dependencies that §5.2 installs.
- **DR-021** (timestamp anchoring, Adelaide local time) —
  propagates to §6 step 1, §8 §1, §13 of the report.
- **DR-027** (two-database architecture: BetHub owns
  operational state, capture.db owns analytical/source data,
  no shared tables, integration by reference only) —
  substrate for the `clients/` folder boundary discipline.
- **DR-028** (cross-database integration boundary discipline:
  no caching, no denormalisation, no second integration
  point) — substrate for `clients/` as the only layer that
  reaches external systems.

**DR-029 close-out debt items addressed in W0:**

- **Debt 2 (no migration framework)** — Alembic scaffolding
  lands in §5.2 / §6, closing the substrate gap from day 0.
  Actual migrations land per-module as W-streams build.
- **Debt 1 (no test coverage)** — substrate landed via
  pytest + pytest-asyncio config in §5.3 and the §5.5
  verification suite. Real per-module coverage lands
  per-module as W-streams build.

**Prior session anchors:**

- **Session 79** — DR-030 and DR-031 locked.
- **Session 81** — Fix 4 closed; W1 transitioned from
  blocked-on-H2 to in flight; this brief (W0) drafted
  Session 82 to separate repo init from W1 implementation.
- **Session 82** — this brief drafted.

**Parking-lot items explicitly excluded (carry-forward, not
in scope for W0):**

- `contracts/` folder relocation (DR-030 administrative
  cleanup post-DR-029-close).
- `bethub-analytical` project activation (operator-side
  decision pending).
- Pre-commit hook configuration (operator-workflow choice,
  parked).
- Remote git configuration (operator preference, parked).
- `LICENSE` file (parked, not load-bearing).
- `governance.md` §4 deferred-capability reconciliation
  (carry-forward from Session 81).
- Jump-anchor design reframe (W4/W5 design substance,
  unrelated to W0).
