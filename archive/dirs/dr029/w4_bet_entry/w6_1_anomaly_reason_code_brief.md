# W6.1 — `structural_anomaly_no_betfair_bet_id` reason code amendment

**Status:** locked, single-write
**Anchored on:** Session 104 triage of W6 broader-sync report
§6.2 / §7.1 — operator-confirmed promotion of the missing-
`betfair_bet_id` anomaly to its own reason code with a dedicated
pass-result counter for visibility.
**Brief shape:** surgical fix, mirrors Sessions 35/36 surgical-fix
precedent.

---

## §1 — What this brief is and is not

**Is:** a small surgical change to the W6 reconciliation worker
that promotes the missing-`betfair_bet_id` structural anomaly
from a buried `detail.anomaly` discriminator (current v1 ship)
to a first-class reason code with its own pass-result counter.
Single bounded Code session.

**Is not:**

- Not a re-architecture of the reason-code surface. Other seven
  W6 reason codes are unchanged.
- Not a touch on the W6 functional behaviour. The guard at
  `reconciliation.py:190` already does the right thing
  operationally (logs WARNING, returns no-decision, leaves the
  bet untouched). This brief changes how the anomaly is
  *labelled and counted*, not how it's handled.
- Not scope for any other §6 deviation or §7 open question from
  the W6 report. §7.2 (composite voided/removed) and §7.3
  (still-pending sub-counter) were operator-resolved in Session
  104 as no-change.
- Not a contract change. `betfair_client_contract.md` v1.4 is
  not touched. The `BetfairReadUnavailableReason` client-side
  enum at `clients/betfair_client/v1/envelope.py` is not
  touched — the new code is a `ResolutionReasonCode` Literal
  value, which is reconciliation-module-internal vocabulary.
- Not governance-doc edits. No edits to `decisions.md`,
  `architecture.md`, `governance.md`, `current_state.md`,
  `standing_instructions.md`, `vision.md`,
  `v3_data_requirements.md`, `project_context.md`.
- Surprises become findings in the report, not blockers and
  not mid-session escalations.

---

## §2 — Why this work exists

W6 v1 shipped the missing-`betfair_bet_id` defensive guard at
`reconciliation.py:190-203`. The guard returns a
`ResolutionDecision` with `reason_code="read_unavailable_orders"`
and `detail={"anomaly": "missing_betfair_bet_id"}`. This conflates
two structurally different paths:

- A genuine read failure (Betfair API unreachable, auth expired,
  etc.) — the worker should retry on a future pass.
- A structural anomaly (a `PROVISIONAL` bet has no
  `betfair_bet_id`, which is unreachable except via a software
  bug elsewhere) — the worker should never expect this to
  resolve and should make the anomaly loudly visible.

Operator decision Session 104: the structural anomaly should
have its own reason code and its own pass-result counter so it
shows up at the pass-summary level rather than being buried in
log detail.

This is consistent with operator-Claude division of labour per
`standing_instructions.md` Cat 5 — software-shaped surface
decisions are Claude's territory; the operator confirmed the
visibility direction.

---

## §3 — Pre-reads

Required:

- `dr029/w4_bet_entry/w6_broader_sync_report.md` — Session 104
  triage substrate (especially §6.2, §7.1, §4.1 test 12).
- `dr029/w4_bet_entry/w6_broader_sync_brief.md` — locked W6
  brief (this amendment is consistent with brief intent;
  brief itself is not edited).
- `workflows/bet_entry/v1/reconciliation.py` — current file
  state (640 LOC; the changes land at lines 78-87, 170-180,
  187-203, and 415-460 — see §5).
- `tests/workflows/bet_entry/v1/test_reconciliation.py` — the
  existing test_resolve_missing_betfair_bet_id_anomaly at
  line 495-510 needs the assertion updated.

Reference-only:

- `clients/betfair_client/v1/envelope.py` — confirms
  `BetfairReadUnavailableReason` is the *client-side* enum and
  not touched by this brief.
- `decisions.md` — DR-021 (Adelaide local timestamps), DR-031
  (Pydantic v2, ruff, import-linter discipline), DR-032
  (canonical reference layer — `betfair_bet_id` semantics).

---

## §4 — System access

- **Filesystem:** read-write on the v3 working tree at
  `/Users/tim/Desktop/Projects/bethub-v3/`.
- **Database:** none. This brief is a pure code/test change.
- **Betfair API / VPS:** not touched. No live calls.
- **Timestamps:** Adelaide local per DR-021 for any new
  test fixtures or log assertions; existing fixtures unchanged.
- **Python interpreter:** `.venv/bin/python` (3.12.7) per
  W6 report §8.1 (system `python3` is 3.11.9 and rejects
  PEP-695 `type` aliases). Use the venv interpreter
  consistently.

---

## §5 — Substantive scope

Five named anchors, in dependency order. Each anchor is
surgical — a small, specific edit, not a rewrite.

### §5.1 — Anchor A: `ResolutionReasonCode` Literal addition

**File:** `workflows/bet_entry/v1/reconciliation.py`
**Line range:** 78-87 (the `ResolutionReasonCode` Literal block).

**Change:** add one new value to the Literal:

```python
ResolutionReasonCode = Literal[
    "fully_matched_via_orders",
    "still_pending_in_orders",
    "absent_resolved_pre_settlement_full",
    "absent_resolved_pre_settlement_failed",
    "absent_resolved_post_settlement_terminal",
    "absent_resolved_void_or_removed",
    "read_unavailable_orders",
    "read_unavailable_settlement",
    "structural_anomaly_no_betfair_bet_id",  # NEW
]
```

The new code is the last entry in the Literal. Order is not
load-bearing (it's a `str | Literal`, no positional semantics);
appending at the end keeps the diff minimal.

### §5.2 — Anchor B: `_resolve_one` guard reason code

**File:** `workflows/bet_entry/v1/reconciliation.py`
**Line range:** 187-203 (the missing-`betfair_bet_id` guard).

**Change:** flip the `reason_code` and remove the now-redundant
`detail.anomaly` key. The WARNING log line stays unchanged.

Before (line 198-203):

```python
return ResolutionDecision(
    new_status=None,
    matched_stake=None,
    unmatched_stake=None,
    matched_price=None,
    reason_code="read_unavailable_orders",
    detail={"anomaly": "missing_betfair_bet_id"},
)
```

After:

```python
return ResolutionDecision(
    new_status=None,
    matched_stake=None,
    unmatched_stake=None,
    matched_price=None,
    reason_code="structural_anomaly_no_betfair_bet_id",
    detail={"bet_id": record.bet_id},
)
```

Rationale: the new reason code carries the structural-anomaly
semantics directly; `detail` shifts to carrying the operationally
useful identifier (the bet_id that triggered the anomaly), not
the redundant anomaly tag.

### §5.3 — Anchor C: `_resolve_one` docstring update

**File:** `workflows/bet_entry/v1/reconciliation.py`
**Line range:** 170-180 (the `_resolve_one` docstring read
steps).

**Change:** add a step describing the structural-anomaly guard
ahead of step 1 (the orders read). Suggested wording:

```text
0. Sanity guard: a record with no `betfair_bet_id` is
   structurally unreconcilable — log WARNING and return no
   decision with reason `structural_anomaly_no_betfair_bet_id`.
   Pass loop treats this distinctly from read-unavailable
   failures via the dedicated pass-result counter (§5.4 below).
```

Then renumber the existing read steps (current step 1 stays
step 1; the addition is a step 0 prefix). The downstream step
numbering is unchanged.

### §5.4 — Anchor D: `ReconciliationPassResult` counter addition

**File:** `workflows/bet_entry/v1/reconciliation.py`
**Line range:** the `ReconciliationPassResult` Pydantic model
(~lines 116-135 per pre-W6.1 layout) plus the pass loop
counter accumulation (~lines 415-460).

**Change A (model):** add a sixth counter field:

```python
class ReconciliationPassResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    swept_count: int
    resolved_final_full: int
    resolved_final_partial: int
    resolved_failed: int
    transitioned_to_provisional_pending: int
    left_provisional_read_unavailable: int
    structural_anomalies: int  # NEW
    started_at: datetime
    finished_at: datetime
    pass_id: str
```

Field order: insert after `left_provisional_read_unavailable`
and before `started_at`. Default value not set (Pydantic v2
requires explicit value at construction); the pass-loop
constructor must include it.

**Change B (pass loop):** initialise the counter at the top of
`run_reconciliation_pass` alongside the other five counters,
and increment it specifically when the no-decision path fires
on `reason_code == "structural_anomaly_no_betfair_bet_id"`.

Pseudo-shape (current pass-loop logic at lines 415-460):

```python
# Initialisation alongside other counters:
structural_anomalies = 0

# Inside the per-record loop, in the `else` branch when
# decision.new_status is None:
else:
    if decision.reason_code == "structural_anomaly_no_betfair_bet_id":
        structural_anomalies += 1
    else:
        left_provisional_read_unavailable += 1
    LOG.warning(
        "reconciliation left provisional bet_id=%s "
        "(reason=%s, detail=%s)",
        record.bet_id,
        decision.reason_code,
        decision.detail,
    )
```

**Change C (`ReconciliationPassResult` constructor at end of
pass):** include `structural_anomalies=structural_anomalies` in
the `ReconciliationPassResult(...)` call. Update the
pass-finish LOG.info line to include the new counter so
operator-side log inspection shows it.

### §5.5 — Anchor E: test updates

**File:** `tests/workflows/bet_entry/v1/test_reconciliation.py`

**Change A — existing anomaly test
(`test_resolve_missing_betfair_bet_id_anomaly` at line 495-510):**
update the two assertions to match the new shape:

Before:

```python
assert decision.reason_code == "read_unavailable_orders"
assert decision.detail["anomaly"] == "missing_betfair_bet_id"
```

After:

```python
assert decision.reason_code == "structural_anomaly_no_betfair_bet_id"
assert decision.detail["bet_id"] == record.bet_id
```

**Change B — pass-level coverage:** add one new pass-level test
exercising the `structural_anomalies` counter:

```python
def test_pass_increments_structural_anomalies_counter(...) -> None:
    """A bet with no betfair_bet_id increments the
    structural_anomalies counter, not
    left_provisional_read_unavailable."""
    # Construct an unreconciled bet record with betfair_bet_id=None
    # via _make_record(betfair_bet_id=None). Run a single pass.
    # Assert: result.structural_anomalies == 1
    # Assert: result.left_provisional_read_unavailable == 0
    # Assert: bookkeeping fields stamped (last_reconciled_at set,
    # reconciliation_attempts incremented).
```

The bookkeeping assertion is important: structural anomalies
are still swept (the bet should appear in next-pass candidates
unchanged in match-status, but with bookkeeping stamped so
attempts counter increments). This matches the existing
behaviour of `_write_bookkeeping` being called regardless of
the decision branch.

**Change C — existing pass-level coverage:** verify the existing
`test_pass_handles_storage_failure` and other counter
assertions don't accidentally need a `structural_anomalies=0`
assertion added. If a test asserts the full
`ReconciliationPassResult` shape (e.g. via `result.model_dump()`
comparison), it needs the new field added; otherwise no change.

Test count delta target: **+1** (the new pass-level test). The
existing anomaly test count is unchanged (assertion change only,
not a new test). Total post-amendment test count: 416 → 417.

---

## §6 — Sequencing within session

Order of operations:

1. **Anchor A first** (Literal addition) — without this, every
   subsequent step would fail type-check (the new value
   wouldn't be a valid `ResolutionReasonCode`).
2. **Anchor B** (guard reason code flip) — after A, this is a
   single substitution.
3. **Anchor C** (docstring update) — independent of B; can
   land before or after.
4. **Anchor D** (counter addition) — after A. The Pydantic model
   change must precede the pass-loop logic change to avoid
   intermediate broken state.
5. **Anchor E** (test updates) — last. After A-D land, run
   `pytest tests/workflows/bet_entry/v1/test_reconciliation.py`
   and the existing anomaly test should fail (assertion
   mismatch); update assertions per §5.5 Change A; then add
   the new pass-level test per §5.5 Change B.

If natural ordering during the session fits better (e.g.
docstring before guard flip), Code may deviate — the
load-bearing constraint is A before the others.

---

## §7 — Empirical verification

### §7.1 — Pre-baseline (session open)

Capture three states:

```bash
# Test count
.venv/bin/python -m pytest --collect-only -q | tail -1
# Expected: 416 tests collected

# Static checks
.venv/bin/python -m ruff check workflows/bet_entry/v1/ tests/workflows/bet_entry/v1/
.venv/bin/python -m lint_imports
# Both expected: clean / 5 contracts kept
```

### §7.2 — Post-baseline (session close)

Same three commands. Expected:

```
417 tests collected
ruff check: clean
lint-imports: 5 contracts kept, 0 broken
```

### §7.3 — Targeted functional verification

```bash
# All reconciliation tests pass
.venv/bin/python -m pytest tests/workflows/bet_entry/v1/test_reconciliation.py -v

# Existing anomaly test passes with new assertions
.venv/bin/python -m pytest \
    tests/workflows/bet_entry/v1/test_reconciliation.py::test_resolve_missing_betfair_bet_id_anomaly -v

# New pass-level test passes
.venv/bin/python -m pytest \
    tests/workflows/bet_entry/v1/test_reconciliation.py::test_pass_increments_structural_anomalies_counter -v
```

All three must pass before close.

### §7.4 — Pass-result counter shape inspection

After tests pass, capture (in the report) a sample
`ReconciliationPassResult` model dump showing the six counter
fields populated. This documents the new shape for the next
operator-Claude session.

---

## §8 — Output spec

**Report path:** `dr029/w4_bet_entry/w6_1_anomaly_reason_code_report.md`

**Section structure:**

1. Summary — what shipped, what didn't.
2. Files changed — table with pre/post LOC.
3. Test count delta — pre/post pytest collection counts.
4. New tests added — names + brief descriptions.
5. Implementation notes — anchor-by-anchor commentary.
6. Deviations from brief — if any (none expected; flag any
   surprise).
7. Open questions for triage — if any (none expected).
8. Findings beyond brief scope — if any (e.g. a related
   anomaly path discovered mid-session). Not actioned by
   this brief.
9. Self-assessment — pre/post baselines table, functional
   verification checklist, `git status` snapshots, length
   flag, Adelaide-local timestamp confirmation.

**Length anticipation:** 200-400 lines. This is a small surgical
brief; the report should reflect that. If the report exceeds
400 lines, flag it in §9 self-assessment as a length surprise
and explain why.

**What the report does not contain:**

- No recommendations on what to do next (operator-Claude
  triage territory).
- No re-architecture proposals (the change is the change;
  scope creep into other reason-code surface adjustments is
  forbidden per §9).
- No edits to governance docs.
- No live API call evidence (none made).

---

## §9 — Hard limits

Code does not:

- Edit any file outside the five named anchors:
  - `workflows/bet_entry/v1/reconciliation.py` (anchors A, B,
    C, D).
  - `tests/workflows/bet_entry/v1/test_reconciliation.py`
    (anchor E).
- Edit `betfair_client_contract.md` (the contract is at v1.4
  and not touched by this work).
- Edit `clients/betfair_client/v1/envelope.py` or any other
  client-side module — the new reason code is
  reconciliation-module-internal vocabulary, not a client-side
  enum value.
- Add reason codes beyond the one named in this brief.
- Touch other W6 deviations (§6.3, §6.4, §6.5, §6.6, §6.7) —
  all operator-confirmed acceptable in Session 104.
- Touch other W6 open questions (§7.2, §7.3, §7.4, §7.5) —
  all operator-resolved in Session 104.
- Add `git add`, `git commit`, `git stash`, `git restore`,
  `git checkout` (file-targeted), or `git reset` operations.
  Working tree stays as Code finds it.
- Run live Betfair API calls of any shape.
- Write to any database (no schema change, no data writes).
- Refactor adjacent code "while we're here" — surgical
  discipline applies.
- Mid-session escalate to operator-Claude. Surprises become
  findings in §6 / §7 / §8 of the report.

If Code finds the work won't fit a single bounded session
(unlikely given scope), that's a finding for the report, not a
continuation past budget.

---

## §10 — Working tree state at session open

Per W6 report §8.2 / §9.3, the working tree carries pre-existing
dirty regions from Session 101 onwards:

- Modified: `clients/betfair_client/v1/__init__.py`,
  `clients/betfair_client/v1/_translation.py`.
- Untracked: `clients/betfair_client/v1/account_funds.py`,
  `current_orders.py`, `market_catalogue.py`, their tests,
  the entire `tests/workflows/` and `workflows/bet_entry/v1/`
  trees.

W6.1's named anchors are inside the already-untracked
`workflows/bet_entry/v1/` and `tests/workflows/` trees — no
intersection with the modified files. No new untracked files
should appear; this brief only edits existing ones.

Code captures `git status` at session open and session close in
the report's §9.3.

---

## §11 — What happens after Code's session

Session 105 (operator-Claude triage):

1. Read the W6.1 report via inventory-first cadence (sweep
   candidate `l`, fourth concrete use).
2. Walk any deviations / open questions / findings — expected
   to be near-empty given scope.
3. Acknowledge close; operator-Claude moves to W6.5
   settlement-state worker brief drafting per Session 104
   forward routing.

W6.1 closes the §6.2 / §7.1 carry from the W6 report. No new
arcs opened by this brief.

---

## §12 — Cross-references

- **Source:** Session 104 triage of `w6_broader_sync_report.md`
  §6.2 + §7.1 (operator-confirmed promotion).
- **Builds on:** W6 broader-sync brief
  (`w6_broader_sync_brief.md`); W6 report
  (`w6_broader_sync_report.md`); Session 103 brief drafting;
  Session 104 triage (this session).
- **DRs invoked:** DR-021 (Adelaide local timestamps for any
  new test fixtures); DR-031 (Pydantic v2 `frozen=True`,
  ruff, lint-imports discipline); DR-032 (`betfair_bet_id`
  semantics).
- **Out of scope (explicit):** all other W6 deviations and
  open questions; W6.5 settlement-state worker (separate
  brief, sequenced after this); W7 burst-review (separate
  brief, sequenced after W6.5).
- **Parking-lot items unaffected:** §8.1 venv invocation
  foot-gun; §8.5 COALESCE migration back-fill (W6.5
  territory).

---

**End of brief.**
