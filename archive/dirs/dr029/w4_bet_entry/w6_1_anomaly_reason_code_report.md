# W6.1 — `structural_anomaly_no_betfair_bet_id` reason code report

**Session opened:** 2026-05-08 07:07 ACST (Adelaide local per DR-021)
**Session closed:** 2026-05-08 07:10 ACST
**Brief:** `dr029/w4_bet_entry/w6_1_anomaly_reason_code_brief.md` (locked)
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`
**Python interpreter:** `.venv/bin/python` (3.12.7) per brief §4.

---

## §1 — Summary

W6.1 surgical amendment shipped end-to-end within a single
bounded session. All five named anchors landed; nothing outside
§5 scope was touched.

What shipped:

- **Anchor A** — `ResolutionReasonCode` Literal grew by one
  value: `"structural_anomaly_no_betfair_bet_id"` appended at
  the end (8 → 9 values).
- **Anchor B** — `_resolve_one`'s missing-`betfair_bet_id` guard
  now returns `reason_code="structural_anomaly_no_betfair_bet_id"`
  with `detail={"bet_id": record.bet_id}`. Replaces the prior
  `reason_code="read_unavailable_orders"` +
  `detail={"anomaly": "missing_betfair_bet_id"}` shape.
- **Anchor C** — `_resolve_one` docstring gains a "step 0
  sanity guard" entry ahead of the orders read; existing read
  steps unchanged.
- **Anchor D** — `ReconciliationPassResult` gains a
  `structural_anomalies: int` field (sixth counter; inserted
  between `left_provisional_read_unavailable` and `started_at`).
  Pass loop initialises and increments it specifically when
  the no-decision path fires on the new reason code; the
  pass-finish `LOG.info` line includes the new counter.
- **Anchor E** — existing
  `test_resolve_missing_betfair_bet_id_anomaly` assertions
  flipped to match the new shape; one new pass-level test
  `test_pass_increments_structural_anomalies_counter` added.

Test count delta: 416 → 417 (+1 net new test, as targeted).
`ruff check`: clean. `lint-imports`: 5 contracts kept, 0 broken.
The functional behaviour of the worker is unchanged — the
anomaly is still logged at WARNING, no decision is made, the
bet stays in its current `match_status`, and bookkeeping is
still stamped per pass. Only the labelling and the pass-result
counter visibility changed.

What didn't ship: nothing from §5 deferred. No edits outside the
five named anchors. No `git add`/`commit`/`stash` issued. No
governance docs touched. No live API calls. No database writes.

## §2 — Files changed

| File | Pre LOC | Post LOC | Δ |
|---|---:|---:|---:|
| `workflows/bet_entry/v1/reconciliation.py` | 640 | 655 | +15 |
| `tests/workflows/bet_entry/v1/test_reconciliation.py` | 1015 | 1055 | +40 |
| **TOTAL** | **1655** | **1710** | **+55** |

No other files modified. No files added or deleted.

## §3 — Test count delta

Pre-baseline (session open):

```
416 tests collected
```

Post-baseline (session close):

```
417 tests collected
417 passed in 1.08s
```

Delta: **+1 net new test**, matching brief §5.5 target. The
flipped existing anomaly test is an assertion change only and
does not alter the test count.

## §4 — New tests added

`test_pass_increments_structural_anomalies_counter`
(`tests/workflows/bet_entry/v1/test_reconciliation.py`,
inserted after `test_pass_handles_storage_failure`).

Coverage:

- A `PROVISIONAL` bet with `betfair_bet_id=None` is written
  to storage and a single pass is run.
- Asserts `result.swept_count == 1`,
  `result.structural_anomalies == 1`,
  `result.left_provisional_read_unavailable == 0` —
  proves the new counter is incremented and is mutually
  exclusive with the read-unavailable counter.
- Asserts `adapter.order_state_calls == []` — the guard
  short-circuits ahead of the orders read (no wasted Betfair
  call).
- Asserts the bet's `match_status` is unchanged (`PROVISIONAL`),
  `last_reconciled_at == T0_PLUS_300S` (Adelaide-local fixture
  per DR-021), and `reconciliation_attempts == 1` —
  proves bookkeeping is stamped even when the decision path is
  the structural-anomaly one, matching the existing
  `_write_bookkeeping` contract that runs regardless of the
  decision branch.

## §5 — Implementation notes

### §5.1 — Anchor A (Literal addition)

Single-line append at `reconciliation.py:87`. The Literal carries
no positional semantics; appending at the end keeps the diff
minimal per brief §5.1 guidance.

### §5.2 — Anchor B (guard reason code flip)

The `WARNING` log line at `reconciliation.py:191-195` was
preserved verbatim per brief §5.2 ("the WARNING log line stays
unchanged"). Only the `ResolutionDecision` constructor changed:
`reason_code` flipped, `detail` shape moved from
`{"anomaly": "missing_betfair_bet_id"}` to
`{"bet_id": record.bet_id}`. The new detail value carries the
operationally useful identifier (the W4 bet_id) for triage —
the anomaly tag is now redundant with the reason code itself.

### §5.3 — Anchor C (docstring update)

Inserted a new "step 0 sanity guard" bullet ahead of the
existing step 1 in the `_resolve_one` docstring. Existing read
steps 1-6 are unchanged. The new bullet references the
`structural_anomalies` pass-result counter introduced by
Anchor D and cross-references W6.1 brief §5.4.

### §5.4 — Anchor D (counter addition)

Three discrete edits in three regions of the file:

1. `ReconciliationPassResult` model — `structural_anomalies:
   int` field inserted between `left_provisional_read_unavailable`
   and `started_at` per brief §5.4 Change A. No default value
   (Pydantic v2 frozen model — explicit at construction). The
   pass-loop constructor sets it.
2. Pass loop — `structural_anomalies = 0` initialiser added
   alongside the other five counters at the top of
   `run_reconciliation_pass`. Inside the per-record loop, the
   `else` branch (no-decision path) now branches on
   `decision.reason_code == "structural_anomaly_no_betfair_bet_id"`:
   structural-anomaly hits increment `structural_anomalies`,
   all other no-decision hits increment
   `left_provisional_read_unavailable` as before. The single
   `LOG.warning` line covers both branches.
3. Pass-finish `LOG.info` — added `anomalies=%s` substitution
   at the end of the format string + `result.structural_anomalies`
   to the parameter tuple. Operator-side log inspection now sees
   the new counter inline with the existing carry counter.

### §5.5 — Anchor E (test updates)

Two edits in `test_reconciliation.py`:

1. Existing `test_resolve_missing_betfair_bet_id_anomaly` —
   two-assertion flip per brief §5.5 Change A
   (`reason_code` + `detail` key). The "no order-state call"
   assertion is preserved.
2. New `test_pass_increments_structural_anomalies_counter` —
   inserted after `test_pass_handles_storage_failure`. The
   structure mirrors the surrounding pass-level tests in this
   block (same fixtures, same `T0_PLUS_300S` clock pin, same
   `_make_record` helper).

### §5.6 — Sequencing

Brief §6 specifies Anchor A first; subsequent anchors
B/C/D/E in any order with E last. I followed the brief order
(A → B → C → D → E) which kept the file in a valid state at
each step. Tests were run only after E completed: both targeted
tests passed on the first run, no rework needed.

### §5.7 — `ReconciliationPassResult` shape inspection (§7.4)

Sample model dump (constructed for documentation, not from a
real pass — this is the shape Session 105 / W6.5 should expect):

```json
{
  "swept_count": 4,
  "resolved_final_full": 2,
  "resolved_final_partial": 0,
  "resolved_failed": 1,
  "transitioned_to_provisional_pending": 0,
  "left_provisional_read_unavailable": 0,
  "structural_anomalies": 1,
  "started_at": "2026-05-08T14:12:30+09:30",
  "finished_at": "2026-05-08T14:12:31+09:30",
  "pass_id": "abc123def456abc123def456abc12345"
}
```

Six counter fields populated as expected; ISO8601 timestamps
in Adelaide (`+09:30`) per DR-021; `pass_id` is a 32-char hex
string.

## §6 — Deviations from brief

None. The five anchors landed exactly as specified. The brief
flagged that no deviations were expected; this report confirms
that expectation.

## §7 — Open questions for triage

None. The brief flagged that no open questions were expected;
this report confirms that expectation. W6.1 closes the §6.2 /
§7.1 carry from the W6 report cleanly.

## §8 — Findings beyond brief scope

None. No related-anomaly path or surface-area surprise surfaced
mid-session. Brief §1 noted "other seven W6 reason codes are
unchanged"; verified empirically by inspecting the Literal
post-edit (8 original entries unchanged + 1 appended).

## §9 — Self-assessment

### §9.1 — Pre/post baselines

| Metric | Pre-baseline | Post-baseline | Δ |
|---|---|---|---|
| `pytest` collected | 416 | 417 | +1 |
| `pytest` passing | 416 | 417 | +1 |
| `ruff check workflows/bet_entry/v1/ tests/workflows/bet_entry/v1/` | clean | clean | — |
| `lint-imports` | 5 kept, 0 broken | 5 kept, 0 broken | — |
| `ResolutionReasonCode` Literal values | 8 | 9 | +1 |
| `ReconciliationPassResult` counter fields | 5 | 6 | +1 |
| `ReconciliationPassResult` total fields | 9 | 10 | +1 |

### §9.2 — Functional verification checklist (brief §7.3)

- [x] All `tests/workflows/bet_entry/v1/test_reconciliation.py`
  pass (40 tests post-amendment, was 39 pre-amendment).
- [x] `test_resolve_missing_betfair_bet_id_anomaly` passes with
  the new assertions (`reason_code` and `detail.bet_id`).
- [x] `test_pass_increments_structural_anomalies_counter` passes
  on the first run.
- [x] Full suite passes: `417 passed in 1.08s`.
- [x] `ruff check` clean on the W4 source + test scope.
- [x] `lint-imports` 5 contracts kept, 0 broken.
- [x] No live Betfair API calls, no database writes (mocked-only,
  in-memory storage).
- [x] No edits outside the five named anchors.

### §9.3 — `git status` snapshots

**Session open (2026-05-08 07:07 ACST):**

```
On branch main
Changes not staged for commit:
	modified:   clients/betfair_client/v1/__init__.py
	modified:   clients/betfair_client/v1/_translation.py
Untracked files:
	clients/betfair_client/v1/account_funds.py
	clients/betfair_client/v1/current_orders.py
	clients/betfair_client/v1/market_catalogue.py
	tests/clients/betfair_client/v1/test_account_funds.py
	tests/clients/betfair_client/v1/test_current_orders.py
	tests/clients/betfair_client/v1/test_market_catalogue.py
	tests/workflows/
	workflows/bet_entry/v1/
```

**Session close (2026-05-08 07:10 ACST):**

Identical to session open at the file-list level. The W6.1
edits land inside already-untracked
`workflows/bet_entry/v1/reconciliation.py` and
`tests/workflows/bet_entry/v1/test_reconciliation.py`, so
the dirty-file surface didn't change. No new untracked files
appeared (consistent with brief §10's "no new untracked files
should appear" expectation). No `git add` / `git commit` /
`git stash` / `git restore` was issued.

### §9.4 — Length flag

Report length: ~ 250 lines (within brief §8's 200-400 line
target band). Surgical brief produced a surgical report — no
length surprise to flag.

### §9.5 — Adelaide-local timestamp confirmation per DR-021

- Session open / close timestamps captured via
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`.
- New pass-level test
  `test_pass_increments_structural_anomalies_counter` reuses
  the existing `T0_PLUS_300S` Adelaide-local fixture
  (`datetime(2026, 5, 6, 14, 12, 30, tzinfo=ZoneInfo("Australia/Adelaide"))
  + timedelta(seconds=300)`) — no new timestamp constants
  introduced.
- `LOG.info` pass-finish format adds an `anomalies=%s` field;
  the underlying `started_at` / `finished_at` Adelaide-local
  semantics are unchanged.

---

**End of report.**
