# M1 Brief — Maintenance micro-bundle

**Drafted:** Session 146, 2026-06-10 ACST.
**Status:** LOCKED — operator-confirmed Session 146. Ready for
out-of-session Code execution.
**Shape:** one light Code session, independent of W17. Runs
whenever convenient; no ordering dependency against the W17 brief.

---

## §1 — What this brief is and is not

A **surgical maintenance brief**: seven small, independent items —
five accumulated maintenance fixes plus a single-file mypy cleanup
plus Alembic adoption (the DR-031 deferral now closing per the
S145 timing call). No feature work, no behaviour change except
where an item names one. Single bounded Code session; surprises
are findings; remediation routes to Chat triage.

## §2 — Why this work exists

Items 1–5 accumulated across W12–W15 triage sessions as
known-but-not-urgent debt. Item 6 keeps the bet-entry Betfair
adapter type-clean. Item 7 closes the DR-031 migration-framework
deferral before cutover-era schema changes start arriving.

## §3 — Pre-reads

1. This brief end to end.
2. `decisions.md` DR-031 (tech stack — Alembic deferral note).
3. Per-item anchors named in §5.

## §4 — System access

Mac filesystem, v3 repo read-write at
`/Users/tim/Desktop/Projects/bethub-v3/`. No v2 access, no VPS, no
capture.db, no live Betfair. Adelaide timestamps per DR-021.

## §5 — The seven items

### Item 1 — FB-inventory test time-bomb (clock freeze)

S144 diagnosis: two promo test files construct free-bet expiry
fixtures relative to a hardcoded reference date; the suite began
failing as wall-clock time passed it. Fix: freeze the clock — pin
a REF_TIME of 2026-05-18 (Adelaide) in both files and derive every
fixture timestamp and the derivation's "now" from it (monkeypatch
the `_now()` seam in `promo_derivations.py`), so the tests are
deterministic forever.

Anchors: `tests/workflows/promos/v1/test_promo_derivations.py`,
`tests/workflows/promos/v1/test_promo_store_adapter.py`.
Expected effect: pytest baseline moves 894/2 → 896/0.

### Item 2 — Stale docstring, balance derivation

`workflows/balances/v1/balance_derivation.py` L153–160: the
`_DEFAULT_COMMISSION` docstring says commission-source population
"is the separate next brief". That brief (W12.2) has since landed.
Rewrite the docstring to present tense: commission is populated at
write time from Betfair MBR; the 0.08 constant remains the
read-side fallback for NULL commission on legacy/edge rows. No
code change.

### Item 3 — Stale docstring, lay-branch test

`tests/workflows/balances/v1/test_balance_lay_branch.py` L291:
same stale `_COMMISSION_TABLE` framing. Align wording with Item
2's rewrite. No assertion changes.

### Item 4 — Bets row-factory asymmetry (W15 finding #2)

Per the W15 report finding #2: row-factory handling is asymmetric
across the bets storage read paths (one path sets
`conn.row_factory = sqlite3.Row` at `store/repositories/bets.py`
~L475; others set it per-cursor or assume it). Normalise to one
documented convention (per-cursor preferred — no caller-visible
connection mutation), matching whichever pattern the W15 report
recommended. Read the W15 report finding before editing.
Behaviour-neutral; full test suite is the guard.

### Item 5 — `.importlinter` documentation note (W15 finding #1)

Per the W15 report finding #1: add the short explanatory note to
`.importlinter` (comment header) documenting the contract layout
and the reason for the layering, per the report's wording. No
contract changes — comment/documentation only.

### Item 6 — `betfair_adapter.py` single-file mypy cleanup

`.venv/bin/mypy workflows/bet_entry/v1/betfair_adapter.py`
currently reports 15 errors, predominantly union-attr narrowing on
read/write envelope unions (e.g. accessing `.reason`/`.data`
without narrowing `FreshEnvelope | StaleEnvelope |
UnavailableReadEnvelope`). Fix by proper narrowing (isinstance /
status checks or typed helper guards), NOT by `# type: ignore` and
NOT by changing envelope models. Zero errors on the file at close;
no behaviour change; full suite green.

### Item 7 — Alembic adoption (DR-031 deferral closes)

Adopt Alembic as the migration framework for v3's operational
store:

- `alembic init` wired to the repo layout (alembic.ini +
  `migrations/` directory placed per DR-030 module boundaries —
  store-adjacent, importable config from `store/`).
- One baseline migration capturing the CURRENT schema as revision
  0 (autogenerate against the live model/DDL, then hand-verify the
  emitted DDL matches `store/schema/` exactly — the baseline must
  be a no-op against an existing database).
- A documented stamp path for the operator's existing local DB
  (`alembic stamp head`) recorded in the report and in a short
  README note under the migrations directory.
- Developer flow note: future schema changes ship as Alembic
  revisions; `store/schema/` remains the readable source of truth.
- NO schema changes ride along. Baseline only.

## §6 — Sequencing

1 (unblocks clean baseline) → 2 → 3 → 4 → 5 → 6 → 7. Items 2–6
are order-free; Alembic last so the suite is fully green before
the framework lands.

## §7 — Empirical verification

- Pytest at start: record baseline (expected 894/2). After Item 1:
  896/0. At close: 896/0 (or better), zero new failures.
- Item 6: mypy on the named file → 0 errors, before/after output
  captured in the report.
- Item 7: `alembic upgrade head` on a fresh empty DB produces a
  schema identical to the current DDL (Code diffs `sqlite_master`
  SQL between a fresh-DDL DB and a fresh-Alembic DB and includes
  the result — expected: empty diff); `alembic stamp head` against
  a copy of a seeded fixture DB succeeds. Never against the
  operator's live DB — the stamp path is documented for the
  operator, not executed by Code.
- `lint-imports` clean at close (Item 5 must not alter contracts).

## §8 — Output spec

Single report: `dr029/m1_maintenance/m1_report.md`. Sections:
per-item delivery note (one short block each), verification
results (pytest/mypy/alembic diffs), findings, self-assessment.
Length anticipation: 120–250 lines. No recommendations, no scope
creep beyond findings.

## §9 — Hard limits

- No W17 work of any kind, even where files sit adjacent.
- No schema changes (Item 7 is baseline-capture only).
- No mypy work outside `betfair_adapter.py`.
- No edits to envelope models, contracts, or `.importlinter`
  contract definitions (Item 5 is comments only).
- No v2, VPS, capture.db, or live Betfair access.
- No `# type: ignore` suppressions for Item 6.
- No Alembic operations against the operator's live database.
- Named anchors only; no drive-by refactors.
- No operator escalation mid-session; findings go in the report.

## §10 — What happens after

Next Chat session reads `m1_report.md`, confirms the 896/0
baseline becomes the new standing pytest expectation in
`current_state.md`, and notes Alembic as adopted against DR-031.

## §11 — Cross-references

DR-031 (tech stack; migration-framework deferral), DR-030 (module
boundaries — migrations placement), DR-021 (timestamps). W15
report findings #1/#2 (`dr029/w15_ops_log/`). S144 session record
(time-bomb diagnosis). S145 scope settlement §7 (bundling call).
Excluded: W17 brief (`dr029/w17_racing_pages/w17_brief.md`).
