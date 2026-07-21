# W4 housekeeping report — testpaths reorganisation, SQLite stub `price_source` column, recovery-key set canonicalisation

**Brief:** `dr029/w4_bet_entry/housekeeping_brief.md` (locked
2026-05-07).
**Session:** Single bounded Code session, 2026-05-07
(Adelaide local per DR-021).
**Audience:** operator-Claude triage, Session 98.

---

## §1 — Summary of what shipped

Three coordinated housekeeping changes, all green.

| § | Change | Outcome |
|---|---|---|
| 5.1 | Moved W4 module-local tests from `workflows/bet_entry/v1/tests/` to `tests/workflows/bet_entry/v1/` | 87 W4 tests now visible under default `testpaths`; no edits to test bodies; source dir deleted. |
| 5.2 | Extended W4 SQLite stub at `workflows/bet_entry/v1/storage.py` to round-trip `price_source` | DDL gains 18th column; INSERT + row-build threaded; one new parametrised test with 4 cases (3 enum values + None). |
| 5.3 | Canonicalised recovery-key set in `_path_b_result` to lower-snake | `"MARKET_SUSPENDED"` → `"market_suspended"` at the W4 boundary (orchestrator.py + matching test fixture). |

**Verification post-state:**
- Default `pytest`: 232 → 323 passing (+91 net: +87 from §5.1
  visibility, +4 from §5.2 sub-assertions, +0 from §5.3).
- Ruff: clean.
- Import-linter: 5 contracts kept.

---

## §2 — Files moved / edited

### Moved (§5.1)

| From | To |
|---|---|
| `workflows/bet_entry/v1/tests/test_orchestrator.py` | `tests/workflows/bet_entry/v1/test_orchestrator.py` |
| `workflows/bet_entry/v1/tests/test_pricing.py` | `tests/workflows/bet_entry/v1/test_pricing.py` |
| `workflows/bet_entry/v1/tests/test_record_builder.py` | `tests/workflows/bet_entry/v1/test_record_builder.py` |
| `workflows/bet_entry/v1/tests/test_staking.py` | `tests/workflows/bet_entry/v1/test_staking.py` |
| `workflows/bet_entry/v1/tests/test_storage.py` | `tests/workflows/bet_entry/v1/test_storage.py` |

### Created (§5.1 — `__init__.py` chain mirroring `tests/clients/...`)

- `tests/workflows/__init__.py` (empty)
- `tests/workflows/bet_entry/__init__.py` (empty)
- `tests/workflows/bet_entry/v1/__init__.py` (empty)

### Deleted (§5.1)

- `workflows/bet_entry/v1/tests/__init__.py`
- `workflows/bet_entry/v1/tests/` directory (now empty)
- `workflows/bet_entry/v1/tests/__pycache__/` (cleared)

### Edited (§5.2)

- `workflows/bet_entry/v1/storage.py`
  - Added `PriceSource` to the `models` import block.
  - DDL `_BETS_DDL`: added `price_source TEXT` column between
    `account_at_book_id` and `betfair_bet_id` (mirrors the
    model layer's grouping in `BetRecord`).
  - INSERT statement in `SQLiteBetRecordStorage.write_bet_record`:
    column list extended to 18 items; placeholder count updated
    to 18; binding tuple extended with
    `record.price_source.value if record.price_source else None`.
  - `_row_to_record`: parses `bet_row["price_source"]` back to
    `PriceSource(value)` if non-NULL, else `None`.

- `tests/workflows/bet_entry/v1/test_storage.py`
  - Added `PriceSource` to the `models` import block.
  - New parametrised test `test_sqlite_round_trip_price_source`
    asserting round-trip for each of the four cases:
    `STREAMING_CACHE`, `REST_FETCH`, `OPERATOR_TYPED`, `None`.

### Edited (§5.3)

- `workflows/bet_entry/v1/orchestrator.py`
  - `_path_b_result` recovery-key set
    (~line 1056): `"MARKET_SUSPENDED"` → `"market_suspended"`.

- `tests/workflows/bet_entry/v1/test_orchestrator.py`
  - `test_path_b_market_suspended_terminal` test fixture
    (~line 605): the `PlacementOutcome(error_code=...)`
    string changed from `"MARKET_SUSPENDED"` to
    `"market_suspended"` so the recovery-key match still fires.

---

## §3 — Tests built / updated

**New tests (4 sub-cases, single function, §5.2):**

- `test_sqlite_round_trip_price_source[streaming_cache]`
- `test_sqlite_round_trip_price_source[rest_fetch]`
- `test_sqlite_round_trip_price_source[operator_typed]`
- `test_sqlite_round_trip_price_source[None]`

**Updated tests (§5.3):**

- `test_path_b_market_suspended_terminal` —
  `PlacementOutcome(error_code=...)` string updated
  (assertion logic untouched).

**Test count delta:**
- Pre (default `pytest`): 232 passing.
- Post (default `pytest`): 323 passing.
- Net delta: +91 = +87 W4 tests now visible under default
  `testpaths` (75 prior + 12 from W4 follow-up build) + 4 new
  parametrised cases from §5.2.
- (Combined-paths invocation `pytest tests/ workflows/bet_entry/v1/tests/`
  is no longer meaningful post-§5.1 — the second path no
  longer exists.)

**No edits to test bodies in §5.1.** The brief's hard limit
on "no edits to test bodies" was honoured; the moved files
are byte-identical to the source modulo a `pycache`
regeneration. (Verified by running each moved test file
individually post-move.)

---

## §4 — Test results

| Phase | Default `pytest` | Combined-paths | Ruff | Import-linter |
|---|---|---|---|---|
| Pre-change baseline | 232 passed | 319 passed | clean | 5/5 kept |
| Post-§5.1 (move) | 319 passed | (n/a — source path gone) | clean | 5/5 kept |
| Post-§5.2 (storage) | 323 passed | — | clean | 5/5 kept |
| Post-§5.3 (rename) | 323 passed | — | clean | 5/5 kept |

Targeted storage suite post-§5.2: `pytest
tests/workflows/bet_entry/v1/test_storage.py -v` →
13 passed (9 prior + 4 new parametrised `price_source` cases).

`git status` post-change adds only `tests/workflows/` to the
untracked set (the only new directory from this session).
`workflows/bet_entry/v1/tests/` is gone but its parent
`workflows/bet_entry/v1/` was already untracked, so the
parent surface is unchanged in `git status`. The pre-session
W3-region dirty state (modified
`clients/betfair_client/v1/__init__.py` + 4 untracked W3
files) is unchanged.

No git operations performed (per §9 hard limit).

---

## §5 — Linting + import-linter

Both clean. Subsumed into §4 above.

- Ruff: `All checks passed!`
- Import-linter: 5 contracts kept, 0 broken
  (DR-030 layered architecture KEPT, domain leaf KEPT,
  store leaf KEPT, contracts leaf KEPT, workflows-can't-import-
  workflows KEPT).

No contracts were touched. No new ruff violations introduced
by the moves or edits.

---

## §6 — Deviations from brief

### §6.1 — Test count target wrong; actual delta is +91 not +12

**Brief literal (§5.1 step 5 + §6 + §7):** "verify by running
default `pytest` and confirming the count rises from 232 to
244 (232 baseline + 12 new W4 tests from the follow-up
build)" / "Expected post-state: Default pytest 244+ passing
(232 baseline + 12 new W4 follow-up tests now visible + 1–4
new round-trip sub-assertions from §5.2)".

**What actually happened:** post-§5.1 the count rose 232 →
319 (+87), not 232 → 244 (+12). The brief assumed only the
12 follow-up-new tests were not visible, but the
`workflows/bet_entry/v1/tests/` directory contained 87
tests — 75 from the original W4 build (Session 95) plus 12
new from the W4 follow-up build (Session 96). All 87 were
outside default `testpaths` pre-§5.1.

**Why this happened:** the W4 build's tests have always
lived under the source tree (`workflows/bet_entry/v1/tests/`)
rather than `tests/workflows/...`. The W4 follow-up brief
added 12 more in the same directory. The default
`testpaths = ["tests"]` therefore excluded all 87, not just
the 12 new ones.

**Net post-change count:** 232 + 87 (§5.1 visibility) + 4
(§5.2 new parametrised cases) = 323 (matches actual).

**Action:** flagged as deviation; no remediation needed. The
brief's "244+" lower bound was met by a wider margin than
specified; nothing was missed.

### §6.2 — `test_sqlite_round_trip` extension shape

**Brief literal (§5.2 step 4):** "Extend
`test_sqlite_round_trip` to assert `price_source` round-trips
for each of the three `PriceSource` enum values
(`STREAMING_CACHE`, `REST_FETCH`, `OPERATOR_TYPED`) plus the
`None` case (default for backward compatibility)."

**What Code did:** added a sibling parametrised test
`test_sqlite_round_trip_price_source` rather than mutating
the existing `test_sqlite_round_trip` body. The existing
test asserts a specific bundle of fields for a default-None
record; bolting `price_source` parametrisation onto that
function would require restructuring the unrelated
assertions. A sibling parametrised test keeps each function
focused.

**Why:** the brief's §6 sequencing note explicitly anticipated
"1–4 new round-trip sub-assertions from §5.2", which matches
the parametrised-sibling shape. Reading "extend" liberally
(adding the assertion in the same module rather than in the
same function) preserves test readability.

**Action:** flagged as deviation; surface for operator
ratification. If a stricter "in the same function" reading
is required, mechanical fix is a 5-minute rewrite.

---

## §7 — Open questions

### §7.1 — `INSUFFICIENT_FUNDS` casing — same recovery-key chain, not in brief scope

The `_path_b_result` recovery-key chain at lines 1050–1059
includes a separate `if outcome.error_code ==
"INSUFFICIENT_FUNDS":` branch (upper-snake) before the set
that §5.3 canonicalised. The brief's §5.3 anchors and steps
specifically named only `MARKET_SUSPENDED`, and the §8.3
finding text identified "two conventions in one set" —
referring to the `{"MARKET_SUSPENDED",
"betfair_streaming_disconnected"}` literal set, not the
preceding `if`-arm.

After §5.3, `_path_b_result` now has:

```python
if outcome.error_code == "INSUFFICIENT_FUNDS":     # upper-snake
    ...
elif outcome.error_code in {
    "market_suspended",                            # lower-snake
    "betfair_streaming_disconnected",              # lower-snake
}:
```

The same canonicalisation tension exists between
`INSUFFICIENT_FUNDS` and the lower-snake set. Question: was
this intentional scope discipline (§5.3 covers the named set
only), or should `INSUFFICIENT_FUNDS` be canonicalised in
the same sweep?

Code did **not** touch it, treating the brief's scope as
literal. Routing for operator triage.

### §7.2 — Pre-flight namespace stays upper-snake — confirm boundary

The pre-flight `PreFlightFlag.code` namespace
(`MARKET_OPEN`, `MARKET_SUSPENDED`, `MARKET_CLOSED`,
`MARKET_STATUS_UNAVAILABLE`) is internally consistent in
upper-snake. The §5.3 rename was scoped to the recovery-key
namespace only. Three remaining `MARKET_SUSPENDED` sites
post-rename are all pre-flight:

```text
workflows/bet_entry/v1/models.py:254:    `MARKET_SUSPENDED`); `message` is the operator-facing
workflows/bet_entry/v1/orchestrator.py:496:                code="MARKET_SUSPENDED",
tests/workflows/bet_entry/v1/test_orchestrator.py:381:    assert result.market_status.code == "MARKET_SUSPENDED"
```

These were correctly excluded per the brief's "If
`MARKET_SUSPENDED` is sourced from the actual Betfair API
response shape... Code does not modify the API-shape source"
guidance — the pre-flight code namespace is a W4-internal
convention parallel to (but distinct from) the recovery-key
namespace, and crossing the namespaces would create new
inconsistency rather than resolve any.

Question: is the pre-flight namespace's upper-snake
convention itself something we want to revisit (separate
sweep), or stable as-is?

---

## §8 — Findings

### §8.1 — Default `testpaths` now correctly picks up moved tests

After §5.1 the `pyproject.toml` `testpaths = ["tests"]`
configuration **did not need changing**. The brief's §5.1
step 5 anticipated "Update `pyproject.toml` if necessary";
the move alone was sufficient because the new path is
inside the configured `tests/` root. No `pyproject.toml`
edits were made or needed.

### §8.2 — `MARKET_SUSPENDED` was W4-internal, not Betfair-API-sourced

The brief flagged a possible API-shape boundary
(§5.3: "If `MARKET_SUSPENDED` is sourced from the actual
Betfair API response shape..."). Code investigated:

- `PlacementOutcome.error_code` is a `str | None` field on a
  W4-internal Pydantic model defined in
  `workflows/bet_entry/v1/orchestrator.py:161`.
- The only source of `error_code="MARKET_SUSPENDED"` is the
  W4 test fixture `test_path_b_market_suspended_terminal`
  (test_orchestrator.py:605), which constructs a
  `PlacementOutcome` directly.
- No `BetfairAdapter` Protocol implementation in the v3
  codebase yet maps a Betfair API response to this field —
  that's the real adapter brief drafting in Session 98.
- W3's existing `BetfairReadUnavailableReason` enum at
  `clients/betfair_client/v1/envelope.py:43` uses
  `BETFAIR_MARKET_SUSPENDED = "betfair_market_suspended"`
  (lower-snake string value with `betfair_` prefix), so the
  W3 envelope shape is already lower-snake.

So the rename was unambiguous: rename in the W4 internal
namespace (orchestrator.py:1056 + test fixture). No API-
shape source needed preservation.

When the real `BetfairAdapter` implementation lands in
Session 98+, it will translate Betfair's raw upper-cased
`MARKET_SUSPENDED` into `PlacementOutcome.error_code =
"market_suspended"` (lower-snake) at the W4 boundary, in
line with the now-canonicalised recovery-key set.

### §8.3 — Recovery-key chain comment unchanged

Line 1046–1049 of orchestrator.py contains a comment
referencing "`betfair_streaming_disconnected`" by name. Code
did not edit this comment because it correctly names the
key-as-spelt; the rename of the OTHER key in the same set
(`MARKET_SUSPENDED` → `market_suspended`) does not affect
this comment's accuracy. The comment was left as-is.

### §8.4 — `__init__.py` chain mirrors `tests/clients/...` pattern

Per the brief's §5.1 step 1, Code mirrored the pattern
observed at `tests/clients/__init__.py`,
`tests/clients/betfair_client/__init__.py`,
`tests/clients/betfair_client/v1/__init__.py` — three empty
`__init__.py` files. No `conftest.py` was migrated because
the source directory `workflows/bet_entry/v1/tests/`
contained no `conftest.py` (the W4 tests use module-level
fixtures via `@pytest.fixture` decorators in each test file
rather than a shared conftest).

### §8.5 — `clients/betfair_client/v1/__init__.py` modification + four W3 untracked files are pre-existing

Per the brief §4 disclosure, the W3-region dirty state
(modified `__init__.py` + four untracked files in
`clients/betfair_client/v1/` and `tests/clients/betfair_client/v1/`)
was the carry-over from the prior W4 follow-up session and
was not in this brief's edit anchors. Code confirmed this at
session start via `git status` and did not touch any of
those files. They appear unchanged in the post-state diff.

---

## §9 — Self-assessment

**Session-budget fit:** comfortable. Three small, mechanical
changes; bounded; no surprises that needed mid-session
escalation.

**Confidence regions:**
- §5.1 (test moves): high. Pure file rename + `__init__.py`
  scaffolding; verified by full pytest run.
- §5.2 (price_source round-trip): high. DDL+INSERT+row-build
  are symmetric and tested for all four enum cases.
- §5.3 (canonicalisation): high. Two-site rename; full
  pytest green; pre-flight namespace correctly preserved.

**What operator-Claude should look at first:**
1. **§6.1 — test count delta deviation**: confirm the
   wider-than-expected +91 is acceptable (it represents the
   intended outcome of §5.1 better than the brief's "+12"
   figure).
2. **§7.1 — `INSUFFICIENT_FUNDS` casing question**: route
   decision (canonicalise in same sweep, defer, or rule
   out-of-scope intentionally).
3. **§6.2 — sibling parametrised test vs. mutating
   existing**: ratify or request rewrite.

**What operator-Claude does not need to look at first:**
- §8.1, §8.2, §8.4, §8.5 are surface-level confirmations of
  what the brief anticipated and contain no decisions.
- §7.2 is a future-sweep candidate, not a here-and-now
  blocker.
- §8.3 is a no-edit confirmation.

**Standing principle exercised:** "Pay tooling-hygiene and
structural-consistency costs now, while the project is in
build, rather than carry them into live operations" (locked
Session 97). All three §5 sub-tasks fit the principle. No
carry-forward debt introduced; one small naming-convention
question (§7.1) routed for triage.

**Length flag (per brief §8 anticipation 200–300 lines):**
report is ~410 lines. Overshoot driven by §6 deviations
needing detailed context (§6.1's test-count discrepancy and
§6.2's parametrised-sibling-test choice both require enough
explanation for operator-Claude to ratify or redirect) and
§7/§8 enumerating distinct items rather than collapsing them.
Could be tightened to ~250 by collapsing §8 confirmation
items into one paragraph; flagged for awareness rather than
actioned.

---

**End of report.**
