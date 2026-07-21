# W11.1 — accounts test files surgical rename

**Source:** `dr029/w11_accounts/w11_accounts_report.md`
Finding §4.1.
**Brief locked:** 2026-05-11 20:49 ACST (Session 121).
**Anchor:** `/Users/tim/Desktop/Projects/bethub-v3/`.

---

## §1. What this is and is not

This is a **surgical rename** of the two W11 accounts test files
to align with the existing `tests/store/repositories/`
sub-directory layout. Single bounded Code session. Two file
moves — no code changes, no imports edited, no schema or
behaviour change. Verification: pytest stays green at 549
passing; lint-imports stays at 5 contracts kept, 0 broken; the
old paths are gone and the new paths are present.

It is **not** a rewrite of any test logic, a refactor of the
repository or schema modules, an edit of the locked
`w11_accounts_brief.md` (the brief stays locked per the
brief-locking convention — this W11.1 brief and its report are
the canonical record that the test paths moved), or work on any
other W11 report finding. Specifically out of scope:

- §4.2 (executescript vs execute divergence) — behavioural
  equivalent, accepted as-shipped per Session 121 triage.
- §4.3 (FK pragma real and tested) — verification confirmation,
  no action needed.
- §4.4 (`_add_column_if_missing` lands unused) —
  brief-specified future substrate, accepted as-shipped.
- §4.5 (`close()` method added beyond brief's named list) —
  held-connection lifecycle handle, accepted as-shipped.
- §4.6 (test bug caught and fixed pre-pytest) — already
  resolved by Code in-session.
- §5.1 deviations (`close()` method, symmetric bool returns,
  `ConfigDict(frozen=True)`) — all match project patterns,
  accepted as-shipped.

Surprises become findings in the report. Remediation routes to
operator-Claude triage, not Code's report.

## §2. Why this work exists

W11 shipped two new test files at `tests/store/`:

- `tests/store/test_accounts_schema.py`
- `tests/store/test_accounts_repository.py`

These paths follow the W11 brief's §5.5 and §7.3 explicit
specifications. However, the existing bets-tests precedent that
the brief cited at §5.5 actually lives at
`tests/store/repositories/test_bets.py` — the brief's prose
named the wrong precedent path (`tests/store/test_bets_*.py`).
Code correctly followed the brief's explicit paths and surfaced
the divergence as Finding §4.1.

The asymmetric layout that results would propagate forward
unless corrected: W12 (balances), W13 (promos), W14
(transactions), and W15 (operations log) briefs will each need
to pick a canonical test path. The cleaner go-forward state is
a single `tests/store/repositories/` convention matching the
bets-tests reality. Operator-Claude Session 121 triage routed
this as a surgical rename before W12 brief drafting locks the
future convention.

## §3. Pre-reads

Required-reads before starting (in order):

1. `dr029/w11_accounts/w11_accounts_brief.md` — the W11 brief.
   Establishes the scope, anchor files, and lint / pytest
   baselines. Stays locked; this W11.1 brief supersedes the
   §7.3 file-existence paths only.
2. `dr029/w11_accounts/w11_accounts_report.md` — the W11
   report. Finding §4.1 is the named work; all other findings
   are out-of-scope here and must not be touched.
3. `decisions.md` §DR-030 — the v3 repo layout and
   module-boundary discipline DR. Context only; this brief does
   not alter any import contract.

Reference-only (do not read unless a finding warrants):

- `tests/store/repositories/test_bets.py` — the precedent the
  W11 paths are aligning to. Untouched by W11.1.
- `tests/store/repositories/__init__.py` — confirm presence
  before the move. Should already exist (the bets-tests
  precedent requires it for pytest discovery).

## §4. System access

Mac filesystem **read-write** to
`/Users/tim/Desktop/Projects/bethub-v3/tests/store/`. No DB
access. No external API access. No git operations (no add,
commit, stash, restore, reset; the working tree is dirty from
W11 and earlier work).

All timestamps in the report use Adelaide local time per DR-021
(timestamp anchoring, Adelaide local time).

## §5. Substantive scope

### §5.1 — Verify the destination directory shape

Before moving anything, confirm:

- `tests/store/repositories/` exists as a directory.
- `tests/store/repositories/__init__.py` is present (pytest
  discovery dependency).
- `tests/store/repositories/test_bets.py` is present (precedent
  marker).

If any of these are missing, surface as a finding in §4 of the
report before proceeding. Do not create `__init__.py` from
scratch unless the absence is the actual current state and you
are confident it should be present — that's an
operator-Claude routing call, not a Code freelance.

### §5.2 — Move the two W11 test files

Move both files from `tests/store/` to
`tests/store/repositories/`:

- `tests/store/test_accounts_schema.py` →
  `tests/store/repositories/test_accounts_schema.py`
- `tests/store/test_accounts_repository.py` →
  `tests/store/repositories/test_accounts_repository.py`

Use plain `mv` via Desktop Commander start_process (not
`git mv` — no git operations per §9.5). The files are untracked
under the already-untracked `tests/store/` top-level entry, so
the move has no git-tracking implications.

### §5.3 — Verify imports still resolve

Test files import from `domain.accounts`, `store.schema.accounts`,
and `store.repositories.accounts` via absolute paths from the
project root. These imports do not depend on the test file's
own location and need no edits.

Confirm by running pytest collection (`uv run pytest --collect-only`
or equivalent) and verifying both test modules are discovered
from the new paths before running the full test suite.

If any import does not resolve from the new location, surface
as a finding rather than chasing the failure beyond the named
anchors.

## §6. Sequencing within session

In dependency order:

1. Capture pre-baselines per §7 (lint-imports, pytest,
   git status, file existence at old paths).
2. §5.1 (verify destination directory shape). If any
   precondition fails, stop and surface as a finding.
3. §5.2 (move both files).
4. §5.3 (verify imports resolve and pytest collection
   discovers tests at new paths).
5. Capture post-baselines per §7. Lint-imports must show 5
   contracts kept, 0 broken; pytest must show 549 passed;
   the two new paths present and the two old paths gone.

If a verification gate fails at step 5, surface as a finding in
§4 of the report rather than chasing the failure beyond the
named anchors.

## §7. Empirical verification

**Pre-baseline (capture at session start):**

- `uv run lint-imports` — full output. Expected: 5 contracts
  kept, 0 broken.
- `uv run pytest -x -q` — exit status + summary line.
  Expected: 549 passed.
- `git status --short` — full output. Captures the dirty-tree
  state going in.
- File-existence check:
  - `tests/store/test_accounts_schema.py` — present.
  - `tests/store/test_accounts_repository.py` — present.
  - `tests/store/repositories/test_accounts_schema.py` —
    absent.
  - `tests/store/repositories/test_accounts_repository.py` —
    absent.

**Post-baseline (capture at session close, before report
write):**

- `uv run lint-imports` — full output. Expected: 5 contracts
  kept, 0 broken (unchanged from pre-baseline).
- `uv run pytest -x -q` — exit status + summary line.
  Expected: 549 passed (unchanged from pre-baseline).
- `git status --short` — full output. Should differ from pre
  only on the two named file paths (old paths gone, new paths
  added).
- File-existence check:
  - `tests/store/test_accounts_schema.py` — absent.
  - `tests/store/test_accounts_repository.py` — absent.
  - `tests/store/repositories/test_accounts_schema.py` —
    present.
  - `tests/store/repositories/test_accounts_repository.py` —
    present.

**Pytest collection check (capture in the report):**

- `uv run pytest tests/store/repositories/test_accounts_schema.py --collect-only -q`
  — expected: 5 tests collected.
- `uv run pytest tests/store/repositories/test_accounts_repository.py --collect-only -q`
  — expected: 17 tests collected.

## §8. Output spec

**Single output file:** `dr029/w11_accounts/w11_1_report.md`.

**Section structure:**

1. Pre-session state — pre-baselines from §7; file existence
   at old paths.
2. Changes made — one §-sub-section per substantive change
   (§5.1 destination verification, §5.2 file moves,
   §5.3 import resolution). Move-command outputs inline.
3. Post-session state — post-baselines from §7; file existence
   at new paths; pytest collection counts.
4. Findings / surprises — flag anything that deviated,
   surprised, or didn't fit the brief. Per §9.1, observe and
   report — no freelance fixes.
5. Self-assessment — deviations from brief (if any); hard
   limits adherence; anything in scope that couldn't be done
   cleanly; report length flag.

**Length range:** 100–200 lines. This is a smaller scope than
W10.1 (no code changes), so the report should be shorter.
Length-over-target is acceptable when substantive detail earns
it (per Cat 5 length-over-target preference); ritual padding is
not.

**Output does NOT contain:** recommendations for next steps;
suggested follow-up briefs; routing calls; any work outside the
named anchors.

## §9. Hard limits — non-negotiable

### §9.1 Operating principle

Code observes and reports; the next operator-Claude session
decides what to do about surprises. If a finding arises that
isn't covered by the brief's named scope, Code does not
freelance a fix — Code surfaces the finding in §4 of the
report and the next session routes it.

### §9.2 Behaviour and schema preserved

- Schema unchanged. No DDL changes anywhere.
- Behaviour unchanged. No source-code edits anywhere. No
  changes to test logic — only test-file locations change.
- Test counts unchanged. Pytest stays at 549 passing.
- Lint contracts unchanged. Lint-imports stays at 5 kept,
  0 broken.

### §9.3 No adjacent workstreams or findings

- No work on W11 report findings §4.2, §4.3, §4.4, §4.5, §4.6,
  or any §5.1 deviation — all accepted as-shipped per
  Session 121 triage.
- No work on W12 (balances), W13 (promos), W14 (transactions),
  W15 (operations log), W17 (racing market pages), or any
  other workstream.
- No edits to the W11 brief at `w11_accounts_brief.md`
  (locking convention preserved). The §7.3 file-existence
  paths in the W11 brief become a stale historical reference
  after this rename; W11.1's brief and report are the
  canonical go-forward record.
- No new test files, no new schema, no new repository methods,
  no new domain models.

### §9.4 No Alembic adoption, no debt-fixing

- No Alembic adoption (carried per W10 brief §10.2).
- No work on the named pieces of v3 debt (monolithic
  orchestrator file; no migration framework; no test coverage
  gaps).

### §9.5 Operational guardrails

- No git operations (no add, commit, stash, restore, reset,
  `git mv`). The working tree is dirty from W11 and earlier
  work; Code reads but does not modify the dirty state outside
  the named anchors. The W11 test files are untracked under
  the already-untracked `tests/store/` entry, so plain `mv` is
  the correct mechanism.
- No DB access.
- No external API calls.
- No mid-session escalation. Code runs end-to-end, surfaces
  findings in the report, does not ping operator-Claude
  mid-flight for direction.

## §10. What happens after Code's session

1. Operator-Claude Session 122 (or wherever the next session
   lands) reads `dr029/w11_accounts/w11_1_report.md`, runs the
   inventory-first cadence on any findings, and routes each.
2. If verification gates pass (5 contracts kept, 0 broken;
   549 pytest passes; old paths gone and new paths present;
   pytest collection finds 5 + 17 tests at new paths), close
   W11.1, update `v3_build_picture.md` if needed (W11 already
   marked `done` at Session 121 close per the one-session
   carry rule — W11.1 closes silently in the same band), and
   proceed to W12 brief drafting.
3. If verification gates fail (any), routing decision:
   follow-up surgical brief, escalate to a broader re-shape, or
   accept the residual state with operator confirmation.

## §11. Cross-references

- **W11 brief:** `dr029/w11_accounts/w11_accounts_brief.md` —
  the parent brief whose §4.1 finding this rename closes.
  Locked; not edited.
- **W11 report:** `dr029/w11_accounts/w11_accounts_report.md`
  — Finding §4.1 names the path divergence.
- **W10.1 brief:** `dr029/w10_storage_lift/w10_1_brief.md` —
  precedent shape for surgical follow-up to a closed
  parent W-stream.
- **DR-030** (v3 repo layout and module-boundary discipline) —
  context. No contract changes from this brief.
- **DR-021** (timestamp anchoring, Adelaide local time) — all
  timestamps in the report.
- **W11 brief §9.1** operating principle — verbatim carry to
  §9.1 here.
- **Cat 5 length-over-target preference** (standing instruction,
  Session 120 close) — report length range named with
  load-bearing detail prioritised over hitting target.

---

**End of brief.**
