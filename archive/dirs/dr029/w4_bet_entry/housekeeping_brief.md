# W4 housekeeping brief — testpaths reorganisation, SQLite stub `price_source` column, recovery-key set canonicalisation

**Brief shape:** surgical-fix, three coordinated changes.
**Audience:** Claude Code, single bounded session.
**Source:** Session 97 triage of W4 follow-up report
(`dr029/w4_bet_entry/w4_followup_report.md`) — three findings
(§8.1, §8.2, §8.3) routed by operator-Claude to one combined
housekeeping brief per the standing principle "pay tooling-
hygiene and structural-consistency costs now, while the
project is in build, rather than carry them into live
operations" (locked Session 97).
**Locked:** 2026-05-07 (Adelaide local per DR-021).

---

## §1 — What this brief is and is not

**This brief is** a surgical-fix brief covering three small,
independent housekeeping changes in the v3 codebase:

1. **§5.1** — move W4 module-local tests from
   `workflows/bet_entry/v1/tests/` to
   `tests/workflows/bet_entry/v1/` (matching the existing
   `tests/clients/...` convention).
2. **§5.2** — extend the W4 SQLite stub at
   `workflows/bet_entry/v1/storage.py` to round-trip the
   `price_source` field (DDL + INSERT + SELECT + round-trip
   test).
3. **§5.3** — canonicalise the recovery-key set in
   `_path_b_result` to lower-snake throughout (rename the
   `MARKET_SUSPENDED` constant per the §6.1 canonicalisation
   pattern from the W4 follow-up).

**This brief is not:**

- A new feature or capability addition. Pure tooling and
  consistency work.
- A scope expansion of the W4 follow-up. The follow-up arc
  closed Session 97; this brief addresses three findings
  routed for housekeeping rather than left as carry-forward
  debt.
- The real `BetfairAdapter` implementation brief. That
  brief drafts post-this-housekeeping in Session 98.

Single bounded Code session. Surprises become findings, not
blockers. Remediation routes to operator-Claude triage at
the next chat session, not Code's report.

---

## §2 — Why this work exists

W4 follow-up Code's report (Session 96 build, triaged
Session 97) surfaced three findings that all share the
shape "knowable-bad state in tooling/structure that should
be fixed before live ops rather than carried forward":

- **§8.1** — `pyproject.toml` `testpaths = ["tests"]`
  excludes module-local tests at
  `workflows/bet_entry/v1/tests/`. Default `pytest` reports
  232 baseline; W4's 75 existing + 12 new tests are
  invisible. Future briefs would either need to remember an
  explicit two-path invocation or silently miss W4
  regressions in default verification.
- **§8.2** — W4 SQLite stub at
  `workflows/bet_entry/v1/storage.py` doesn't round-trip
  `price_source`. DDL has 17 columns; new field is the
  18th. Write skips silently; read defaults to None. In-
  memory tests preserve the field; SQLite path drops it.
- **§8.3** — Recovery-key set in `_path_b_result` mixes
  upper-snake (`MARKET_SUSPENDED`, Betfair API style) and
  lower-snake (`betfair_streaming_disconnected`, post-§6.1
  W3 enum style). Two conventions in one set.

Operator-Claude landed the standing principle Session 97 —
fix-now while it's cheap, not carry into live ops. All
three findings fit that principle. Combining them into one
housekeeping brief is more operator-budget-efficient than
three separate ones; the work is small, mechanical, and
non-overlapping.

---

## §3 — Pre-reads

**Required (in order):**

1. This brief in full.
2. `dr029/w4_bet_entry/w4_followup_report.md` — Session 97
   triage source. §8.1, §8.2, §8.3 are the relevant
   findings.
3. `pyproject.toml` (repo root) — current `testpaths`
   configuration.

**Reference-only (read on demand if scope unclear):**

- `dr029/w4_bet_entry/w4_followup_brief.md` — Session 96
  brief that produced the codebase state being modified.
- `decisions.md` DR-030 — v3 repo layout and module-
  boundary discipline (frames why `tests/workflows/...`
  is the consistent shape).
- `decisions.md` DR-031 — v3 tech stack (pytest, ruff,
  import-linter discipline).

---

## §4 — System access

**Read-write on Mac filesystem at**
`/Users/tim/Desktop/Projects/bethub-v3/`.

- All work is local. No VPS access. No network calls.
- No live API calls (Betfair, Racing API, none).
- No live database queries beyond ordinary `pytest` runs
  that exercise SQLite in-test (the stub uses an in-test
  SQLite file or in-memory connection per its existing
  pattern — Code reads the existing test setup to confirm).
- Working tree is currently clean against the W4 follow-up
  build except for whatever Code's previous session left
  modified (`clients/betfair_client/v1/__init__.py`
  modified; `workflows/bet_entry/v1/` untracked tree). Read
  `git status` at session start to confirm; the dirty
  regions from the prior W4 follow-up session are expected
  and not in this brief's edit anchors.

Adelaide local timestamps per DR-021 anywhere time-of-day
appears in the report.

---

## §5 — Substantive scope

### §5.1 — Move W4 tests under `tests/workflows/bet_entry/v1/`

**Anchors:**

- Source directory: `workflows/bet_entry/v1/tests/`.
- Target directory: `tests/workflows/bet_entry/v1/`
  (mirrors `tests/clients/...` convention).

**Steps Code performs:**

1. Create target directory `tests/workflows/bet_entry/v1/`
   plus any required `__init__.py` chain
   (`tests/workflows/__init__.py`,
   `tests/workflows/bet_entry/__init__.py`,
   `tests/workflows/bet_entry/v1/__init__.py` — match
   whatever pattern `tests/clients/...` uses).
2. Move every `*.py` file from
   `workflows/bet_entry/v1/tests/` to
   `tests/workflows/bet_entry/v1/`. Includes test modules
   plus any test-helper modules (`conftest.py`, fixture
   modules) that live in the source directory.
3. Delete the now-empty `workflows/bet_entry/v1/tests/`
   directory.
4. Update import paths in the moved test files. Tests
   currently import from W4 module via relative or
   absolute paths (e.g. `from workflows.bet_entry.v1.models
   import BetRecord`) — those should continue to work
   unchanged because the module under test hasn't moved.
   Cross-test imports (test helpers importing from each
   other) may need updating depending on the original
   pattern; resolve by running `pytest` post-move and
   fixing any `ImportError`.
5. Update `pyproject.toml` if necessary. Default
   `testpaths = ["tests"]` should now pick up the moved
   tests automatically; verify by running default
   `pytest` and confirming the count rises from 232 to
   244 (232 baseline + 12 new W4 tests from the follow-up
   build). If the count is still 232, the move didn't
   reach the configured testpath — fix.

**Hard limit:** no edits to test bodies. Pure file moves
plus import-path repairs only.

### §5.2 — Extend W4 SQLite stub to round-trip `price_source`

**Anchors:**

- File: `workflows/bet_entry/v1/storage.py`.
- DDL block: ~lines 86-105 (per W4 follow-up report §8.2).
- INSERT statement: ~lines 252-282.
- SELECT statement: ~lines 378-405.
- Test: `test_sqlite_round_trip` in the W4 test suite (now
  living at `tests/workflows/bet_entry/v1/...` post-§5.1).

**Steps Code performs:**

1. Add `price_source TEXT` column to the DDL. Position
   adjacent to other operational metadata columns
   (`placed_at`, `book_or_exchange`, `account_at_book_id`)
   to mirror the model layer's grouping per W4 follow-up
   §5.2.
2. Update INSERT statement: add `price_source` to the
   column list and the parameter binding. Bind value is
   the `BetRecord.price_source` enum's `.value` attribute
   (the string form, since the column is `TEXT`); handle
   `None` correctly (bind as SQL NULL).
3. Update SELECT statement: add `price_source` to the
   selected columns and to the row-build that constructs
   the returned `BetRecord`. Read value is parsed back to
   `PriceSource(value)` if non-None, or `None` if NULL.
4. Extend `test_sqlite_round_trip` to assert `price_source`
   round-trips for each of the three `PriceSource` enum
   values (`STREAMING_CACHE`, `REST_FETCH`,
   `OPERATOR_TYPED`) plus the `None` case (default for
   backward compatibility).

**Hard limit:** no other column additions. No table
restructure. No migration framework introduction (still
deferred per DR-029 close-out governance §4).

### §5.3 — Canonicalise recovery-key set on lower-snake

**Anchors:**

- File: `workflows/bet_entry/v1/orchestrator.py`.
- Recovery-key set in `_path_b_result` (~line 1057 per W4
  follow-up report).
- Any matching string compares elsewhere in
  `_path_b_result` or its callers.

**Steps Code performs:**

1. Rename the `MARKET_SUSPENDED` constant — wherever it's
   compared in the recovery-key set or used as a key — to
   lower-snake (`market_suspended`).
2. Update every site where `MARKET_SUSPENDED` is produced
   (the W3 envelope's reason value, the W4 outcome
   literal, anywhere else it appears as a string literal).
   Code performs `grep -rn 'MARKET_SUSPENDED' bethub-v3/`
   from repo root to enumerate all sites and surfaces the
   list before editing.
3. Update tests that reference the old casing.

**Hard limit:** no other recovery-key additions or
deletions. No reshape of `_path_b_result`'s control flow.
Pure constant-rename across all sites.

**If `MARKET_SUSPENDED` is sourced from the actual Betfair
API response shape** (i.e. the API returns it upper-cased
and the orchestrator preserves that), Code does not modify
the API-shape source. Instead, the rename happens at the
W4 boundary where it's translated into a recovery-key
internal to v3. Code surfaces in the report whether the
boundary lives in `_path_b_result` itself or upstream.

---

## §6 — Sequencing within session

Order matters because §5.1 moves test files and §5.2 + §5.3
edit modules whose tests live in those moved files. Do
§5.1 first so the test runs in §5.2 / §5.3 verification
exercise the canonical post-move test layout.

1. **§5.1 first** — file moves + testpath verification.
   Run default `pytest` post-move; confirm 232 → 244
   passing.
2. **§5.2 second** — SQLite stub column. Extend test;
   re-run pytest; confirm 244 → 245 (one new round-trip
   assertion case may add 1–4 sub-tests depending on how
   parametrisation lands).
3. **§5.3 third** — recovery-key canonicalisation. Run
   pytest after; confirm count stable, all green.

If any step's test count is unexpected, surface it in the
report rather than chasing a re-investigation.

---

## §7 — Empirical verification

**Pre-change baseline (run at session start):**

```bash
cd /Users/tim/Desktop/Projects/bethub-v3
git status                              # capture dirty state
.venv/bin/python -m pytest 2>&1 | tail -3
.venv/bin/python -m pytest tests/ workflows/bet_entry/v1/tests/ 2>&1 | tail -3
.venv/bin/python -m ruff check . 2>&1 | tail -3
.venv/bin/lint-imports 2>&1 | tail -10
```

Expected pre-state: default pytest 232 passing;
combined-paths invocation 319 passing; ruff clean;
import-linter 5 contracts kept.

**Post-change verification:**

```bash
git status                              # confirm only intended changes
.venv/bin/python -m pytest 2>&1 | tail -3
.venv/bin/python -m ruff check . 2>&1 | tail -3
.venv/bin/lint-imports 2>&1 | tail -10
```

Expected post-state:
- Default pytest 244+ passing (232 baseline + 12 new W4
  follow-up tests now visible + 1–4 new round-trip sub-
  assertions from §5.2; combined-path invocation no
  longer needed because `tests/workflows/...` is now
  under default `testpaths`).
- Ruff clean.
- Import-linter 5 contracts kept (no contract changes
  expected).
- `git status` shows the moves + edits only.

---

## §8 — Output spec

**Single output file:**
`dr029/w4_bet_entry/housekeeping_report.md`.

**Length anticipation:** 200–300 lines. This is a small
brief; report should not exceed that range without flagging
in self-assessment.

**Section structure:**

1. **§1 — Summary of what shipped** — three changes named,
   test count delta, ruff/import-linter status.
2. **§2 — Files moved / edited** — table or list of every
   file touched, with what changed.
3. **§3 — Tests built / updated** — what's new, what's
   modified, count delta.
4. **§4 — Test results** — pre and post baseline
   commands and outputs.
5. **§5 — Linting + import-linter** — ruff and
   import-linter post-state (subsumed into §4 if both
   clean).
6. **§6 — Deviations from brief** — any case where Code
   diverged from the brief's literal text and why.
7. **§7 — Open questions** — anything Code wants
   operator-Claude to confirm at next triage.
8. **§8 — Findings** — anything Code surfaces as
   noteworthy that isn't an open question (drift,
   unexpected state, related cleanup that earned itself
   a flag).
9. **§9 — Self-assessment** — session-budget fit,
   confidence regions, what operator should look at first.

**Output does not contain:** recommendations for further
work beyond what's named in §7 / §8 (no scope creep into
the real adapter brief or other housekeeping); no overall
verdict; no proposed next briefs (those are the next chat
session's work).

---

## §9 — Hard limits — what is NOT in scope

- **No edits to test bodies** beyond import-path repairs
  in §5.1 and the new round-trip assertion in §5.2.
- **No SQL schema changes beyond the named column
  addition.** No table restructure, no other column
  additions, no migration framework introduction.
- **No edits to `BetRecord`, `PriceSource`, or other W4
  models.** Stub is the only persistence surface in scope.
- **No edits to the orchestrator's `_place_with_retry`,
  `_place_via_rest_fetch`, REST-fetch wiring, or any W4
  control flow.** §5.3 is a pure rename.
- **No edits to W3 (`clients/betfair_client/v1/`).**
  Recovery-key canonicalisation stays inside W4.
- **No new tests beyond the round-trip sub-assertions in
  §5.2.** Other test additions are out of scope.
- **No Protocol or contract changes.** Contracts and
  protocols are W4-follow-up territory, locked.
- **No git operations.** No `git add`, `git commit`,
  `git stash`, `git restore`, `git checkout` (file-
  targeted), `git reset`. Read-only on git via
  `git status` and `git diff` for verification.
- **No mid-session escalation to operator-Claude.** Single
  bounded session; surprises go in the report.
- **No work on §8.4 (W4 → W3 import precedent), §7.1
  (REST-fetch fresh-by-definition contract), §7.2
  (operator manual price override case), §7.3 (modal
  copy)** — these are routed elsewhere per Session 97
  triage.

---

## §10 — What happens after Code's session

The next chat session (Session 98) reads the report
end-to-end. Triage shape:

1. Walk §6 deviations (any unexpected divergence from
   the brief).
2. Walk §7 open questions (one per round per Cat 1
   call-driven discipline).
3. Walk §8 findings (route each: no action / fold into
   existing carry / surface for the real adapter brief
   / new sweep candidate).
4. Lock close-out: housekeeping arc complete; carry-
   forward items into `current_state.md`.

Once housekeeping is closed clean, Session 98 (or the next
session if 98 is consumed by triage) drafts the **real
`BetfairAdapter` implementation brief** as the next major
deliverable. That brief inherits a clean codebase from
this housekeeping work.

---

## §11 — Cross-references

**Source findings (W4 follow-up report, Session 96 build,
Session 97 triage):**

- §8.1 routed → §5.1 of this brief.
- §8.2 routed → §5.2 of this brief.
- §8.3 routed → §5.3 of this brief.

**Other findings from same report, routed elsewhere
(out of scope for this brief):**

- §6.4 — `OPERATOR_TYPED` populated at orchestrator
  boundary — ratified Session 97; no action.
- §6.5 — `_place_with_retry` tuple-return shape change —
  ratified Session 97; no action.
- §7.1 — implicit "REST returns means fresh" contract —
  parking-lot for contract-cleanup sweep.
- §7.2 — operator manual price override case — named
  carry-forward to W7 brief drafting.
- §7.3 — modal copy after REST-fetch failure — generic
  W7 brief carry.
- §8.4 — first W4 → W3 import — standing-instructions
  sweep candidate (k).

**DRs invoked:**

- DR-021 (Adelaide local time) — applies to all
  timestamps in report.
- DR-030 (v3 repo layout and module-boundary discipline)
  — frames why `tests/workflows/...` is the consistent
  shape.
- DR-031 (v3 tech stack — pytest, ruff, import-linter
  discipline) — frames the verification commands.

**Standing principle locked Session 97:** "Pay tooling-
hygiene and structural-consistency costs now, while the
project is in build, rather than carry them into live
operations." This brief is the first execution of the
principle.

---

**End of brief.**
