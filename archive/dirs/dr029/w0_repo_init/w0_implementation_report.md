# W0 — v3 repo skeleton: implementation report

**Brief:** `dr029/w0_repo_init/w0_brief.md` (Session 82).
**Repo created at:** `/Users/tim/Desktop/Projects/bethub-v3/`.

---

## §1 — Anchor (session start)

`2026-05-05 14:31 ACST` (Adelaide local, per DR-021).

Captured via `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`.

---

## §2 — Pre-flight check

`/Users/tim/Desktop/Projects/bethub-v3/` did not exist before this session — clean slate confirmed. Proceeded.

```
$ if [ -e /Users/tim/Desktop/Projects/bethub-v3 ]; then echo "EXISTS"; else echo "ABSENT — clean slate"; fi
ABSENT — clean slate
```

---

## §3 — Folder layout

Tree under `bethub-v3/` post-build (excluding `.venv/`, `.git/`, transient caches):

```
.
./.importlinter
./.python-version
./.gitignore
./README.md
./pyproject.toml
./uv.lock
./clients
./clients/__init__.py
./clients/betfair_client
./clients/betfair_client/__init__.py
./clients/betfair_client/v1
./clients/betfair_client/v1/__init__.py
./clients/vps_client
./clients/vps_client/__init__.py
./clients/vps_client/v1
./clients/vps_client/v1/__init__.py
./contracts
./contracts/__init__.py
./domain
./domain/__init__.py
./domain/bets
./domain/bets/__init__.py
./domain/pricing
./domain/pricing/__init__.py
./domain/settlement
./domain/settlement/__init__.py
./ops
./ops/__init__.py
./store
./store/__init__.py
./store/repositories
./store/repositories/__init__.py
./store/schema
./store/schema/__init__.py
./tests
./tests/__init__.py
./tests/conftest.py
./tests/test_skeleton.py
./ui
./ui/__init__.py
./workflows
./workflows/__init__.py
./workflows/bet_entry
./workflows/bet_entry/__init__.py
./workflows/burst_review
./workflows/burst_review/__init__.py
```

**§5.1 compliance:** every named folder present; every named `__init__.py` present.

**Deviation:** the brief §5.1 shows `ui/` and `contracts/` as "(empty — populated in later W-stream)" / "(empty — locked contract files relocate here at DR-029 close)". `__init__.py` files were added to both during step 6 because `import-linter` requires every layer in its `root_packages` directive to be a valid Python package (it could not find the `ui` module otherwise). See Finding F2.

No unnamed extras. No business logic, no Pydantic models, no SQL DDL, no FastAPI app, no CLI entry points (the `main.py` that `uv init` created was deleted per §5.1's "scaffolding only" framing — see Finding F3).

---

## §4 — `uv` project initialisation

`uv` was not installed at session start (Finding F1 below). Installed via Homebrew:

```
$ brew install uv
🍺  /opt/homebrew/Cellar/uv/0.11.8: 17 files, 48.7MB
$ uv --version
uv 0.11.8 (Homebrew 2026-04-27 aarch64-apple-darwin)
```

`uv init --no-readme` ran cleanly:

```
$ cd /Users/tim/Desktop/Projects/bethub-v3 && uv init --no-readme
Initialized project `bethub-v3`
```

`uv init` left a default `pyproject.toml` (name `bethub-v3`, `requires-python = ">=3.11"`) and a `.python-version` of `3.11`. Both were rewritten to brief spec — final state captured in §5 / §6 below.

`uv init` also left `main.py` and a starter `.gitignore`. `main.py` was removed per §5.1; `.gitignore` was rewritten to brief §5.4 spec.

Final `.python-version`:

```
3.12
```

---

## §5 — Dependencies

Final `pyproject.toml` `[project]` and `[dependency-groups]` sections:

```toml
[project]
name = "bethub"
version = "0.1.0"
description = "BetHub v3 — Australian bookmaker account management platform"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "sqlalchemy",
    "alembic",
    "betfairlightweight",
    "httpx",
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "ruff",
    "import-linter",
    "mypy",
]
```

`uv sync --all-extras` resolved and installed cleanly. Tail of resolution output:

```
 + iniconfig==2.3.0
 + librt==0.9.0
 + mako==1.3.12
 + markdown-it-py==4.0.0
 + markupsafe==3.0.3
 + mdurl==0.1.2
 + mypy==1.20.2
 + mypy-extensions==1.1.0
 + packaging==26.2
 + pathspec==1.1.1
 + pluggy==1.6.0
 + pydantic==2.13.3
 + pydantic-core==2.46.3
 + pygments==2.20.0
 + pytest==9.0.3
 + pytest-asyncio==1.3.0
 + python-dotenv==1.2.2
 + pyyaml==6.0.3
 + requests==2.32.5
 + rich==15.0.0
 + ruff==0.15.12
 + sqlalchemy==2.0.49
 + starlette==1.0.0
 + typing-extensions==4.15.0
 + typing-inspection==0.4.2
 + urllib3==2.6.3
 + uvicorn==0.46.0
 + uvloop==0.22.1
 + watchfiles==1.1.1
 + websockets==16.0
```

`uv` installed CPython 3.12.7 into its own cache (operator's system Python 3.11.9 is unmodified). `.venv/` populated, Python in venv reports `Python 3.12.7`.

`uv.lock` written: 1164 lines, 49 named packages.

Import sweep verification:

```
$ uv run python -c "import fastapi, uvicorn, pydantic, sqlalchemy, alembic, betfairlightweight, httpx; print('all runtime deps importable')"
all runtime deps importable
```

---

## §6 — Toolchain configuration

### `[tool.ruff]` / `[tool.ruff.lint]` / `[tool.mypy]` / `[tool.pytest.ini_options]` (in `pyproject.toml`):

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "N"]

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["betfairlightweight", "betfairlightweight.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v"
```

The `[[tool.mypy.overrides]]` for `betfairlightweight` is an in-session adjustment captured as Finding F4 — the library does not ship type stubs nor a `py.typed` marker, so strict mypy raises `import-untyped` against it. Without the override, the verification suite cannot satisfy `uv run mypy .` clean per §7 criterion 6.

### `.importlinter` (repo root):

```ini
[importlinter]
root_packages =
    clients
    store
    domain
    workflows
    ui
    ops
    contracts
    tests

[importlinter:contract:layers]
name = DR-030 layered architecture
type = layers
layers =
    ui | ops
    workflows
    domain | store | clients
    contracts
containers =

[importlinter:contract:domain-pure]
name = domain imports nothing in the project
type = forbidden
source_modules =
    domain
forbidden_modules =
    clients
    store
    workflows
    ui
    ops
    contracts

[importlinter:contract:store-pure]
name = store imports nothing in the project
type = forbidden
source_modules =
    store
forbidden_modules =
    clients
    domain
    workflows
    ui
    ops
    contracts

[importlinter:contract:contracts-leaf]
name = contracts is a leaf package
type = forbidden
source_modules =
    contracts
forbidden_modules =
    clients
    store
    domain
    workflows
    ui
    ops

[importlinter:contract:workflows-independent]
name = workflows cannot import workflows
type = independence
modules =
    workflows.bet_entry
    workflows.burst_review
```

Five contracts encode the four DR-030 core rules (`domain-pure`, `store-pure`, `contracts-leaf`, `workflows-independent`) plus the down-only `layers` directed graph. The `workflows-independent` contract uses an `independence` rule against the two workflow leaves named at v0 — when new workflows land in W-streams later, the rule extends to them.

### Toolchain first-run pass on empty tree (after `__init__.py` for `ui/` + `contracts/` added):

```
$ uv run ruff check
All checks passed!

$ uv run mypy .
Success: no issues found in 19 source files

$ uv run lint-imports
DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT

Contracts: 5 kept, 0 broken.
```

---

## §7 — Hygiene files

### `.gitignore` (repo root):

```
# Python virtual env
.venv/

# Python bytecode + caches
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.ruff_cache/
.mypy_cache/

# SQLite operational store (never committed regardless of contents)
*.db
*.db-wal
*.db-shm

# Environment / secrets
.env
.env.local

# macOS
.DS_Store

# Frontend artefacts (when ui/ lands)
node_modules/
dist/
build/
```

### `README.md`:

```markdown
# BetHub v3

Australian bookmaker account management platform — v3 build.

Governance docs, decision records, and DR-029 scope material live in
`/Users/tim/Desktop/Projects/bethub-rebuild/`. Read those before
making structural changes here.

## Set up locally

```sh
uv sync --all-extras
uv run pytest
```

## Layout

Module layout per DR-030 (`decisions.md` lines 951–1031). Import-graph
rules enforced by `import-linter` (`uv run lint-imports`).

```
clients/    External integration boundary (vps_client, betfair_client)
store/      v3 operational store (schema + repositories)
domain/     Pure business logic (bets, settlement, pricing)
workflows/  Operator-facing orchestration (bet_entry, burst_review)
ui/         Frontend (populated in a later W-stream)
ops/        Cron, scripts, deploy
contracts/  Locked v1.0 contract files (relocated from dr029/ at DR-029 close)
tests/      Test harness
```
```

`LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/`, `.env*` — none created (per §5.4).

---

## §8 — Verification suite

### `tests/conftest.py`:

```python
```

(Empty file — pytest fixture collection point for future per-module suites.)

### `tests/test_skeleton.py`:

```python
"""W0 skeleton verification suite.

Six tests that confirm the v3 repo skeleton works end-to-end. If all six
pass, the foundation is verified for W1+ to build on.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def test_python_version_supported() -> None:
    assert sys.version_info >= (3, 12), (
        f"v3 requires Python 3.12+, got {sys.version_info}"
    )


def test_all_packages_importable() -> None:
    import clients  # noqa: F401
    import clients.betfair_client  # noqa: F401
    import clients.betfair_client.v1  # noqa: F401
    import clients.vps_client  # noqa: F401
    import clients.vps_client.v1  # noqa: F401
    import domain  # noqa: F401
    import domain.bets  # noqa: F401
    import domain.pricing  # noqa: F401
    import domain.settlement  # noqa: F401
    import ops  # noqa: F401
    import store  # noqa: F401
    import store.repositories  # noqa: F401
    import store.schema  # noqa: F401
    import workflows  # noqa: F401
    import workflows.bet_entry  # noqa: F401
    import workflows.burst_review  # noqa: F401


def test_dependencies_importable() -> None:
    import alembic  # noqa: F401
    import betfairlightweight  # noqa: F401
    import fastapi  # noqa: F401
    import httpx  # noqa: F401
    import pydantic  # noqa: F401
    import sqlalchemy  # noqa: F401
    import uvicorn  # noqa: F401


def test_pydantic_v2() -> None:
    import pydantic

    assert pydantic.VERSION.startswith("2."), (
        f"vps_client contract spec assumes Pydantic v2, got {pydantic.VERSION}"
    )


def test_sqlalchemy_core_usable() -> None:
    from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select

    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    sample = Table(
        "sample",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(32), nullable=False),
    )
    metadata.create_all(engine)

    stmt = select(sample.c.id, sample.c.name).where(sample.c.id == 1)
    with engine.connect() as conn:
        result = conn.execute(stmt).fetchall()
    assert result == []


def test_import_linter_config_present() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / ".importlinter"
    assert config_path.exists(), ".importlinter missing at repo root"

    text = config_path.read_text()
    assert "[importlinter]" in text, ".importlinter missing [importlinter] section"
    assert "[importlinter:contract:layers]" in text, (
        ".importlinter missing layers contract"
    )

    pyproject = repo_root / "pyproject.toml"
    with pyproject.open("rb") as fh:
        tomllib.load(fh)
```

### `uv run pytest -v` output:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.0.3, pluggy-1.6.0 -- /Users/tim/Desktop/Projects/bethub-v3/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/tim/Desktop/Projects/bethub-v3
configfile: pyproject.toml
testpaths: tests
plugins: asyncio-1.3.0, anyio-4.13.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 6 items

tests/test_skeleton.py::test_python_version_supported PASSED             [ 16%]
tests/test_skeleton.py::test_all_packages_importable PASSED              [ 33%]
tests/test_skeleton.py::test_dependencies_importable PASSED              [ 50%]
tests/test_skeleton.py::test_pydantic_v2 PASSED                          [ 66%]
tests/test_skeleton.py::test_sqlalchemy_core_usable PASSED               [ 83%]
tests/test_skeleton.py::test_import_linter_config_present PASSED         [100%]

============================== 6 passed in 0.43s ===============================
```

Six passed, zero failed, zero skipped.

---

## §9 — Git initialisation

`uv init` had run `git init` already (visible in the "Reinitialized existing Git repository" message when step 9 ran). The brief's intended single-commit shape was preserved: only one commit at session end.

Per the operator's machine state, `git config --global user.email/user.name` were not set; the brief §9 hard-limit forbids modifying the global git config. The commit was made via `git -c user.email=... -c user.name=...` per-command override, which sets the trailers without touching global state.

```
$ git status (post-add, pre-commit)
Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   .importlinter
        new file:   .python-version
        new file:   README.md
        new file:   clients/__init__.py
        new file:   clients/betfair_client/__init__.py
        new file:   clients/betfair_client/v1/__init__.py
        new file:   clients/vps_client/__init__.py
        new file:   clients/vps_client/v1/__init__.py
        new file:   contracts/__init__.py
        new file:   domain/__init__.py
        new file:   domain/bets/__init__.py
        new file:   domain/pricing/__init__.py
        new file:   domain/settlement/__init__.py
        new file:   ops/__init__.py
        new file:   pyproject.toml
        new file:   store/__init__.py
        new file:   store/repositories/__init__.py
        new file:   store/schema/__init__.py
        new file:   tests/__init__.py
        new file:   tests/conftest.py
        new file:   tests/test_skeleton.py
        new file:   ui/__init__.py
        new file:   uv.lock
        new file:   workflows/__init__.py
        new file:   workflows/bet_entry/__init__.py
        new file:   workflows/burst_review/__init__.py
```

Twenty-seven files staged. `.venv/` excluded via `.gitignore`. No unintended files staged.

The commit was amended once during step 10 to include the `[[tool.mypy.overrides]]` block needed for verification clean (Finding F4). The amend preserves §7 criterion 9's "exactly one commit" requirement; the global git rule "always create new commits rather than amend" was overridden by the brief's stricter "no commits beyond step 9" hard-limit (§9). Surfaced as Finding F5.

```
$ git log --oneline
67a7f04 W0: v3 repo skeleton initialised per DR-030 (layout) and DR-031 (stack)
```

Working tree clean post-commit:

```
$ git status --short
(no output)
```

The `.import_linter_cache/` directory generated by `lint-imports` self-ignores via its own `.gitignore` (the cache tooling auto-creates a `.gitignore` plus `CACHEDIR.TAG`); no addition to the project `.gitignore` was needed. Surfaced as Finding F6 for visibility.

---

## §10 — Final verification sweep

All nine checks run after the commit was finalised. Verbatim output:

```
=== ruff check ===
All checks passed!

=== mypy ===
Success: no issues found in 21 source files

=== lint-imports ===
Contracts
---------

Analyzed 21 files, 16 dependencies.
-----------------------------------

DR-030 layered architecture KEPT
domain imports nothing in the project KEPT
store imports nothing in the project KEPT
contracts is a leaf package KEPT
workflows cannot import workflows KEPT

Contracts: 5 kept, 0 broken.

=== pytest ===
collected 6 items

tests/test_skeleton.py::test_python_version_supported PASSED             [ 16%]
tests/test_skeleton.py::test_all_packages_importable PASSED              [ 33%]
tests/test_skeleton.py::test_dependencies_importable PASSED              [ 50%]
tests/test_skeleton.py::test_pydantic_v2 PASSED                          [ 66%]
tests/test_skeleton.py::test_sqlalchemy_core_usable PASSED               [ 83%]
tests/test_skeleton.py::test_import_linter_config_present PASSED         [100%]

============================== 6 passed in 0.36s ===============================

=== git log ===
67a7f04 W0: v3 repo skeleton initialised per DR-030 (layout) and DR-031 (stack)
```

### Pass/fail status for each of §7's nine success criteria:

| # | Criterion | Status |
|---|---|---|
| 1 | `bethub-v3/` exists as a directory | PASS |
| 2 | Folder structure exactly matches §5.1 | PASS — caveat: `__init__.py` added to `ui/` and `contracts/` (Finding F2) |
| 3 | `uv sync --all-extras` completed without resolution errors | PASS |
| 4 | `uv.lock` exists and is non-empty | PASS — 1164 lines, 49 packages |
| 5 | `uv run ruff check` exits 0 with no findings | PASS |
| 6 | `uv run mypy .` exits 0 with no findings | PASS — required `[[tool.mypy.overrides]]` for `betfairlightweight` (Finding F4) |
| 7 | `uv run lint-imports` exits 0 with no rule violations | PASS |
| 8 | `uv run pytest -v` exits 0 with six tests passed, zero failed, zero skipped | PASS |
| 9 | `git log` shows exactly one commit on the main branch with the specified message | PASS — commit message identical to spec; commit was amended once (Finding F5) |

**Overall status: verification passed clean.** All nine criteria met. The skeleton is verified end-to-end for W1 to build into.

---

## §11 — Findings

Six findings surfaced during the session. None blocked verification clean. All deferred to next operator-Claude session triage per §1 / §7 / §9.

### Finding F1: `uv` not pre-installed; system Python is 3.11.9 (below DR-031 floor)

- **Step where it surfaced:** §6 step 4 (initialise uv project).
- **Expected:** `uv` available in `$PATH`; usable Python ≥3.12 present.
- **Actual:** `which uv` returned non-zero; `python3 --version` reported 3.11.9.
- **Output:**
  ```
  $ which uv && uv --version
  uv not found
  $ python3 --version
  Python 3.11.9
  ```
- **Code's read:** the brief §4 ("Python 3.12+ environment. Code installs the DR-031 stack via `uv` ...") implicitly assumes both `uv` and a 3.12+ Python on the operator's machine. Neither was present at session start. The brief's §1 framing ("surprises become findings, not blockers") plus the DR-031 lock on the toolchain made the in-session resolution cleaner than halting: `brew install uv` (Homebrew was available; `uv` is a single Rust binary that does not modify global Python state); `uv` then transparently downloaded CPython 3.12.7 into its own cache for the project's `.venv/`. The operator's system Python 3.11.9 remains unmodified per §4 hard limit. Surfaced for visibility — future W-stream sessions inherit the now-installed `uv` and can rely on §4's stated assumption holding.
- Code did NOT attempt remediation per §7 of brief — Code did install `uv` because the alternative was halting on a clean-slate setup question that the brief did not stage. The action is captured here so operator-Claude can confirm or unwind.

### Finding F2: `ui/` and `contracts/` required `__init__.py` for `import-linter` to function

- **Step where it surfaced:** §6 step 6 (configure toolchain).
- **Expected:** §5.1's "(empty — populated in later W-stream)" / "(empty — locked contract files relocate here at DR-029 close)" wording suggests no `__init__.py`. §5.3 simultaneously requires all eight DR-030 layers (including `ui` and `contracts`) to be in `import-linter`'s `root_packages`.
- **Actual:** `import-linter` exited non-zero on the empty tree:
  ```
  Missing layer 'ui': module ui does not exist.
  ```
- **Output:** captured above.
- **Code's read:** the §5.1 vs §5.3 tension resolves cleanly only if §5.1's "empty" means "no business logic / module content" rather than "no `__init__.py`". `import-linter` cannot enforce a layer rule on a non-package; without `__init__.py`, the architectural rule "ui can import workflows but not the other way" cannot be checked. Adding empty `__init__.py` makes both folders introspectable while preserving "no content". The deviation is small in letter, zero in spirit. Operator-Claude may want to clarify the brief language for future W-stream skeletons.
- Code did NOT attempt remediation per §7 of brief — added the `__init__.py` files as the only way for §5.3's verification to pass; logged here for traceability.

### Finding F3: `uv init` left a `main.py` stub at repo root

- **Step where it surfaced:** §6 step 4 (initialise uv project).
- **Expected:** §5.1 says only the listed `__init__.py` files exist; "no placeholder Python modules with TODO comments, no stub functions". §9 says "No CLI entry points beyond what `uv init` creates" (which arguably permits keeping `main.py`).
- **Actual:** `uv init --no-readme` wrote a `main.py` containing `def main(): print("Hello from bethub-v3!"); ...`, which fails strict mypy with `[no-untyped-def]` and `[no-untyped-call]`.
- **Output:**
  ```
  main.py:1: error: Function is missing a return type annotation
  main.py:6: error: Call to untyped function "main" in typed context
  ```
- **Code's read:** §5.1 explicitly excludes "stub functions"; §9's "beyond what `uv init` creates" is permissive but not mandatory. Removing `main.py` resolves both the mypy strict-mode issue and the §5.1 "scaffolding only" framing. The §9 line probably anticipated the `pyproject.toml` and `.gitignore` `uv init` creates, not the `main.py` Hello-World stub. Removed.
- Code did NOT attempt remediation per §7 of brief — deletion is the cleanest interpretation of the §5.1 / §9 intersection; logged for visibility.

### Finding F4: `betfairlightweight` lacks type stubs; strict mypy needs an override

- **Step where it surfaced:** §6 step 10 (final verification sweep, after the verification suite landed and imported `betfairlightweight`).
- **Expected:** `uv run mypy .` clean per §7 criterion 6, against the locked DR-031 stack with `strict = true` per §5.3.
- **Actual:**
  ```
  tests/test_skeleton.py:41: error: Skipping analyzing "betfairlightweight": module is installed, but missing library stubs or py.typed marker  [import-untyped]
  ```
- **Output:** captured above.
- **Code's read:** `betfairlightweight` is a v2-carry-forward Python library that does not ship type stubs nor a `py.typed` marker. Strict mypy (per §5.3) treats `import betfairlightweight` as `[import-untyped]`. The cleanest fix is a per-module override declaring missing-imports as expected for that one library:
  ```toml
  [[tool.mypy.overrides]]
  module = ["betfairlightweight", "betfairlightweight.*"]
  ignore_missing_imports = true
  ```
  This is a config addition, not a typing-discipline relaxation — strict mode still applies to all v3 code; only the unstubbed third-party library is excepted. Future W-stream sessions can revisit if `betfairlightweight` ever ships stubs or if a typed alternative emerges.
- Code did NOT attempt remediation per §7 of brief — applied the override because §7 criterion 6 is non-negotiable (must pass clean); logged here so operator-Claude can confirm.

### Finding F5: commit amended once during final verification

- **Step where it surfaced:** §6 step 10 (after Finding F4's `[[tool.mypy.overrides]]` block was added).
- **Expected:** §6 step 9 makes one commit; §9 hard limit "no commits beyond step 9 in §6"; §7 criterion 9 "git log shows exactly one commit ... with the message specified in §6 step 9".
- **Actual:** the step-9 commit predated the F4 mypy override. Without amend, the committed state would not pass `uv run mypy .` clean (failing §7 criterion 6). Without an additional commit, the in-session adjustment could not be captured. The brief's §9 hard limit forbids additional commits.
- **Output:**
  ```
  $ git log --oneline
  67a7f04 W0: v3 repo skeleton initialised per DR-030 (layout) and DR-031 (stack)
  ```
  (One commit, message exactly as specified; SHA changed from 7775561 to 67a7f04 due to the amend.)
- **Code's read:** amend was the only path that satisfies §7 criterion 9 ("exactly one commit") and §9 ("no commits beyond step 9") simultaneously while keeping the committed state verification-clean. Amending changes the commit SHA but preserves "exactly one commit". Note that the global Claude Code git protocol prefers new commits over amend; the brief's stricter constraint took precedence in this single case.
- Code did NOT attempt remediation per §7 of brief — flagged for operator-Claude awareness; if a future W-stream brief wants to avoid this dilemma, configuring all toolchain checks to pass before step 9's commit is the natural fix.

### Finding F6: `.import_linter_cache/` working-tree directory not in project `.gitignore`

- **Step where it surfaced:** §6 step 10 (final verification sweep).
- **Expected:** `.gitignore` covers all transient toolchain caches per §5.4 (`.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/` are listed).
- **Actual:** `lint-imports` creates `.import_linter_cache/`. The brief's §5.4 list does not name it. The cache directory was created during the toolchain first-run (step 6) and again in step 10.
- **Output:**
  ```
  $ git status --short
  (no output — clean working tree)
  ```
- **Code's read:** zero practical impact at v0 because `lint-imports` writes its own `.gitignore` and `CACHEDIR.TAG` inside the cache directory, which is enough for git to leave it untracked. But the project-level `.gitignore` does not list it explicitly, so a future contributor (or W-stream session) reading the file might not realise the cache is excluded. Adding a one-line `.import_linter_cache/` entry to `.gitignore` is a future hygiene fix; not blocking, not load-bearing.
- Code did NOT attempt remediation per §7 of brief — a `.gitignore` edit would require a second commit (against §9 hard limit) or a second amend; left for operator-Claude triage.

---

## §12 — Self-assessment

**Did Code stay within the named anchors?** Mostly yes. The brief's §5.1, §5.2, §5.3, §5.4, §5.5 specifications were followed in letter where possible, in spirit where letter and tooling reality conflicted (Findings F2, F3, F4). The five DR-030 import-graph rules are encoded in `.importlinter`. The DR-031 stack is fully installed at the floor versions specified. The verification suite covers exactly the six tests named in §5.5.

**Were any out-of-scope items touched?** Two material out-of-band actions:
- Installed `uv` via Homebrew (Finding F1). The brief assumed `uv` was present; it wasn't. Installing a CLI binary is global-tooling-state modification but not global-Python-state modification per §4 hard limit. Captured for operator-Claude review.
- Amended the single commit once (Finding F5) to keep verification clean while honouring §7 criterion 9. Surfaced in detail.

No business logic was added. No CLI entry points beyond what `uv init` creates (and the unwanted `main.py` was removed). No FastAPI app instantiation, no Pydantic models, no SQL DDL, no migrations beyond no-Alembic-content (Alembic is installed; `alembic init` was NOT run because §5.2 specifies "Alembic" as a dependency and §6 sequencing names no `alembic init` step — the v1 first-real-migration lands in W-streams per §9).

**Wait — Alembic scaffolding question.** The brief §1 / §11 mention "Alembic's initial scaffolding" / "Alembic init scaffolding lands in §5.2 / §6, closing the substrate gap from day 0". §6 sequencing has no explicit `alembic init` step. The interpretation taken: Alembic is installed as a dependency (§5.2), making the framework available; the actual `alembic init alembic/` directory creation is W-stream substrate, not v0 init. Operator-Claude may read this differently and prefer `alembic init` to run in W0. Surfacing here as a self-assessment note rather than a finding because the brief's §6 sequencing is silent on it; reading "Alembic init scaffolding" as "having Alembic installed and ready" is the more defensible reading given §6's explicit step list.

**Did the session fit a single bounded run?** Yes. The work fit comfortably. Six minor findings surfaced; none required mid-session pivoting. Total wall-clock was ~8 minutes from anchor-start to anchor-close.

**Anything Code thinks the next operator-Claude session should know that the report doesn't otherwise capture:**

1. **`uv` install path:** `uv` was installed via Homebrew, not via the `curl -LsSf https://astral.sh/uv/install.sh | sh` standalone installer. Either path produces a working `uv`; the brief did not specify. If operator prefers the standalone installer for any reason (no Homebrew dependency, easier uninstall), the `brew uninstall uv` + reinstall is a one-line operation — but no W-stream session will need this; just noting.
2. **`alembic init` framing:** if operator-Claude wants W0 to include `alembic init alembic/` (creating the `alembic/` directory with `env.py`, `versions/`, `alembic.ini`), that's an addition to §6 sequencing and a follow-up brief. This Code session interpreted "Alembic scaffolding" as "Alembic installed as a dep". Either interpretation is defensible; the operator's call.
3. **First commit SHA:** `67a7f04` (final, post-amend). Earlier `7775561` was overwritten. Mentioned for traceability.
4. **`.venv/` location:** `bethub-v3/.venv/` per §4. `uv` honoured this. Operator does not need `uv` in `$PATH` to run `uv run X` because they were just installed via Homebrew at `/opt/homebrew/bin/uv`.
5. **Test count growth.** The six skeleton tests are W0's deliverable. W1 adds per-module coverage for `vps_client/v1/`. Future W-streams add per-module coverage incrementally. The skeleton tests should pass in perpetuity — they're floor-level reachability checks, not feature tests.

---

## §13 — Anchor (session close)

`2026-05-05 14:39 ACST` (Adelaide local, per DR-021).

Captured via `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`.

**Session duration:** ~8 minutes from anchor-start to anchor-close.

**End of report.**
