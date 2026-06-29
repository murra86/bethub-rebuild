# Accounts-Setup Revision Brief (for Claude Code)

**Drafted:** Session 152 (2026-06-16, Adelaide).
**Builds on:** `dr029/accounts_setup/accounts_setup_report.md`
(the just-completed build) and the operator design calls in
Session 152.
**Sign-off required before hand-off.**

---

## 1. What this brief is and is not

A **surgical revision** of the just-built accounts-setup capability,
in a single bounded Code session. Two changes only: (a) remove the
account `is_self` field end-to-end; (b) convert book `ownership_cluster`
and `platform` from free-text inputs to constrained dropdowns sourced
from a locked option list. Surprises become findings, not blockers.
Remediation of anything outside these two changes routes to
operator-Claude triage, not Code's report. Zero Betfair/live calls.

## 2. Why this work exists

The Session 152 click-through validated the screen end-to-end. The
operator then made two design calls: the "my own account" flag is not
needed, and cluster/platform must be pick-lists (not free text) to
serve as the two correlated-flag axes for account-health strategy
(see `account_health_strategy_note.md`).

## 3. Pre-reads

- `dr029/accounts_setup/accounts_setup_report.md` (what exists now)
- `dr029/accounts_setup/cluster_platform_signoff.md` (the **locked
  option lists** — source of truth for allowed values)
- The files created/edited by the original build (router, data layer,
  schema, `accounts.ts`, `Accounts.tsx`, the two test files)

## 4. System access

Mac filesystem, read-write, limited to the named anchors. Live v3
operational DB is **read-only** for verification (canonical path; never
copy — `start_process` Python per DR-013). v3 data is empty (confirmed
0/0/0 in Session 152), so schema-definition edits need no migration or
backfill. Adelaide local timestamps per DR-021.

## 5. Scope

### 5.1 Remove `is_self` (account ownership flag)

Drop the field everywhere it appears: the accounts table definition,
the `Account` model/dataclass, `create_account` (signature + insert),
any serialisation, the API request/response shapes in
`ui/api/routers/accounts.py`, the typed client in `accounts.ts`, the
checkbox + "mine/household" tag in `Accounts.tsx`, and both test files.

**Discipline:** grep the whole repo for `is_self` at session start.
If any consumer **outside** the accounts-setup surface depends on it
(racing page, balances, reference layer), STOP and surface as a
finding — do not silently break a downstream reader. If it is confined
to the accounts-setup surface (expected), remove cleanly.

### 5.2 Cluster + platform as constrained dropdowns

Both stay **optional** (a book may be uncategorised); the dropdown
carries an explicit empty option. Both stay **TEXT** in the schema
(no hard DB enum — the lists are mutable). Implementation:

- A single backend source-of-truth constant for the allowed cluster
  and platform values, populated from `cluster_platform_signoff.md`.
- A small read endpoint (e.g. `GET /v1/books/options`) returning both
  lists, so the frontend dropdowns and the backend validation share
  one source and cannot drift.
- `POST /v1/books` validates `ownership_cluster` and `platform`
  against the lists; unknown non-empty values → **422** with the
  existing `{code, message}` envelope.
- `Accounts.tsx` Books section renders the two free-text inputs as
  `<select>` dropdowns fed by the options endpoint.

Module shape, exact constant location, endpoint naming, and validation
wiring are Code's call within DR-030 boundaries.

### 5.3 Tests

Update `tests/ui/api/test_accounts.py` and `Accounts.test.tsx` to
match: drop all `is_self` assertions; add coverage for the options
endpoint, valid-value acceptance, and unknown-value 422. Keep the
existing suites green.

## 6. Sequencing

Backend first (schema/model → constant + options endpoint →
validation), then frontend (client → dropdowns), then tests. `is_self`
removal (5.1) and the dropdown work (5.2) are independent; do 5.1
first to keep the model change isolated.

## 7. Verification

- Pre: record current `pytest` / `vitest` pass counts (don't assume).
- Post: full suites green; `GET /v1/books/options` returns both lists;
  a book POST with a listed platform succeeds (201); a book POST with
  an off-list platform returns 422; the screen renders dropdowns and
  persists a categorised book across refresh.
- Confirm the operator's real v3 DB is still empty and untouched at
  end (read-only check).

## 8. Output spec

Single report at `dr029/accounts_setup/accounts_setup_revision_report.md`,
~200–400 lines: what changed (per file), before/after pass counts,
verification results, `is_self` grep findings, and any surprises.
No recommendations, no scope creep.

## 9. Hard limits — NOT in scope

- No auto-login work (its own brief, next).
- No schema changes beyond dropping `is_self` (cluster/platform stay
  TEXT).
- No Betfair/live calls, no real-money paths, no lay test.
- No git operations (my files sit in already-untracked v3 dirs).
- No edits outside the named anchors; no "while we're here" cleanup.
- No new workstreams; no W16 cutover routing.

## 10. What happens after Code's session

Operator-Claude triages `accounts_setup_revision_report.md`: confirm
green + dropdowns working, re-run the browser click-through (built app
on :5173, as established in Session 152), then close the accounts-setup
workstream and move to the **auto-login** brief.

## 11. Cross-references

- Locked option lists: `cluster_platform_signoff.md`
- Strategy rationale: `account_health_strategy_note.md`
- Prior build: `accounts_setup_report.md`
- DRs: DR-021 (timestamps), DR-027 (two-DB), DR-030 (module
  boundaries), DR-013 (DB read discipline)
- Parking-lot (excluded): bet-time same-owner/same-platform warning
  (future enhancement); the dev-server vite-8 Fast Refresh
  incompatibility (separate finding from Session 152).
