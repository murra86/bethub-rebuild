# Accounts-setup revision report (v3)

**Session:** out-of-session Claude Code, single bounded session.
**Date:** 2026-06-16 (Adelaide local, ACST per DR-021).
**Brief:** `dr029/accounts_setup/accounts_setup_revision_brief.md` (locked).
**Option source of truth:** `dr029/accounts_setup/cluster_platform_signoff.md`.
**Builds on:** `dr029/accounts_setup/accounts_setup_report.md`.
**Target codebase:** `/Users/tim/Desktop/Projects/bethub-v3`.
**Outcome:** **One of the two changes built; one halted as a finding.**
§5.2 (constrained dropdowns) is complete and verified. §5.1 (`is_self`
removal) was **stopped at the discipline gate** — `is_self` is consumed
outside the accounts-setup surface (the racing log-panel account picker,
plus the shared domain/schema/repository and ~10 other test suites), so
removing it would break a downstream reader. Surfaced as a finding per
the brief's §5.1 STOP rule rather than chased. No git operations. No
schema changes. Zero Betfair/live calls.

---

## 1. Pre-reads confirmed (Flow 3 steps 2–3)

Read and confirmed in order before any edit:

1. `accounts_setup_revision_brief.md` — the locked spec (two changes;
   surprises → findings; edit only named anchors; no git; no schema
   change beyond dropping `is_self`; both fields stay optional TEXT).
2. `cluster_platform_signoff.md` — the locked option lists (9 clusters,
   7 platforms) used verbatim as the backend source of truth.
3. `accounts_setup_report.md` — the original build (router, client,
   screen, two test suites; baselines 956 / 89).

---

## 2. Decision gate: `is_self` removal (§5.1) — STOPPED, surfaced as a finding

The brief's §5.1 discipline rule is explicit:

> grep the whole repo for `is_self` at session start. If any consumer
> **outside** the accounts-setup surface depends on it (racing page,
> balances, reference layer), STOP and surface as a finding — do not
> silently break a downstream reader.

The session-start grep (`is_self`, repo-wide, excluding
`node_modules`/`.git`/`dist`) returned **38 hits across 25 files**. They
fall into three groups:

**(a) The accounts-setup surface (the brief's expected, removable set):**

- `ui/api/routers/accounts.py` — `CreateAccountRequest.is_self`,
  `AccountResponse.is_self`, the mapper, the `create_account` insert.
- `ui/web/src/api/accounts.ts` — `Account.is_self`,
  `CreateAccountBody.is_self`.
- `ui/web/src/routes/Accounts.tsx` — the checkbox + the "mine/household"
  tag.
- `tests/ui/api/test_accounts.py` — create/listing assertions.
- `ui/web/src/routes/Accounts.test.tsx` — fixture + payload assertion.

**(b) Live downstream consumers OUTSIDE the accounts surface — the STOP trigger:**

- `ui/api/routers/racing.py:415` — `AccountItem.is_self` is a field on
  the racing log-panel's account-picker response model.
- `ui/api/routers/racing.py:769` — the listing endpoint **reads
  `a.is_self`** off the domain account and surfaces it:
  `AccountItem(account_id=a.account_id, name=a.name, is_self=a.is_self)`.
  This is the brief-named "racing page" dependency, live (not dead
  pass-through).
- `ui/web/src/api/racing.ts:176` — the frontend `AccountItem` type
  carries `is_self: boolean`.
- `ui/web/src/routes/Racing.picker.test.tsx` (3 hits) and
  `ui/web/src/components/LogBetPanel.test.tsx` (1 hit) — racing-side
  tests assert on it.

**(c) Shared persistence layer (also outside the accounts surface):**

- `store/schema/accounts.py:39` — `is_self INTEGER NOT NULL` column.
- `store/repositories/accounts.py` — `AccountRow.is_self` dataclass
  field, the INSERT column list, and the row→object read.
- `domain/accounts/__init__.py` — the `Account` dataclass field +
  docstring.
- ~10 other test suites INSERT `is_self` into the `accounts` table
  because the column is `NOT NULL`:
  `tests/store/repositories/test_accounts_schema.py`,
  `test_accounts_repository.py`, `test_promos_schema.py`,
  `test_promos_repository.py`, `test_cash_flow_schema.py`,
  `test_cash_flow_repository.py`, `tests/ui/api/test_racing.py`,
  `tests/workflows/balances/v1/*`, `tests/workflows/cash_flow/v1/*`,
  `tests/workflows/promos/v1/*`.

**Conclusion.** The brief anticipated `is_self` being confined to the
accounts-setup surface ("If it is confined … remove cleanly"). It is
not: the field is load-bearing for the racing page and the shared
domain/schema/repository, and the schema column is `NOT NULL` so a clean
end-to-end removal would also touch a dozen downstream test suites and a
schema column. Every one of those lies outside the brief's named anchors
and outside its "no schema changes beyond dropping `is_self`" allowance
once the racing/domain coupling is in scope.

Per the STOP rule, I did **not** remove `is_self` — neither end-to-end
(would break racing + break the `NOT NULL` insert in many suites) nor
partially from the accounts surface alone (would leave an inconsistent
half-removed field and a divergent `create_account` default while racing
still renders mine/household — a silent, confusing state). The clean,
contract-faithful action is to leave `is_self` fully intact and route
the removal to operator-Claude triage, which can decide a coordinated
cross-surface change (racing picker + domain + schema migration + the
downstream suites) as its own scoped piece of work.

`is_self` is therefore **untouched** in this session. The accounts-setup
`is_self` assertions in the two test files were intentionally retained
(dropping them is part of the halted §5.1, not §5.2).

---

## 3. What was built (§5.2 — constrained dropdowns)

Cluster + platform are now constrained dropdowns backed by one backend
source of truth, with a shared options endpoint feeding both the
frontend `<select>`s and the POST validation. Both fields remain
**optional** (explicit empty option) and stored as **TEXT** (no DB enum).

### 3.1 Backend — `ui/api/routers/accounts.py`

- **Source-of-truth constants.** Two module-level tuples,
  `OWNERSHIP_CLUSTERS` (9 values) and `PLATFORMS` (7 values), copied
  verbatim from `cluster_platform_signoff.md`:
  - Clusters: `Entain`, `Flutter`, `Tabcorp`, `bet365`,
    `betr / BlueBet`, `Crown / Blackstone`, `PlayUp`, `PointsBet`,
    `Independent`.
  - Platforms: `BetMakers`, `GenerationWeb`, `Punterstech`, `BetCloud`,
    `ApolloTech`, `BetEngine`, `Custom`.
  These are the single source — both the endpoint and the validator read
  them, so the dropdowns and the server cannot drift.
- **Options endpoint.** `GET /v1/books/options` → new
  `BookOptionsResponse` model `{ ownership_clusters: [...],
  platforms: [...] }`. Placed before the `POST /v1/books` route; no
  path collision with `GET /v1/books` or the `{book_id}` param routes
  (confirmed by the green suite).
- **POST validation.** New `_validate_book_option(...)` helper called in
  `register_book` for each field. A non-empty value off the locked list
  raises **422** with the existing `{code, message}` envelope —
  `UNKNOWN_OWNERSHIP_CLUSTER` / `UNKNOWN_PLATFORM`. Empty / null is
  always allowed (a book may be uncategorised). Validation runs **before
  the insert**, so a rejected book never reaches storage.
- `__all__` extended with `OWNERSHIP_CLUSTERS`, `PLATFORMS`,
  `BookOptionsResponse`.

Schema, model, repository: **untouched** — the fields were already TEXT
nullable, exactly as the brief requires.

### 3.2 Frontend client — `ui/web/src/api/accounts.ts`

- New `BookOptions` interface (`ownership_clusters: string[]`,
  `platforms: string[]`).
- New `fetchBookOptions()` → `GET /api/v1/books/options`.

### 3.3 Screen — `ui/web/src/routes/Accounts.tsx`

- New `book-options` query (`fetchBookOptions`, `staleTime: Infinity` —
  the list is effectively static within a session).
- The two free-text book inputs (Cluster, Platform) are now `<select>`
  dropdowns fed by the options query. Each carries an explicit
  `<option value="">Uncategorised</option>` empty option so the field
  stays optional. The submit logic is unchanged (`value || null`), so a
  blank selection still POSTs `null`.
- No other section touched. The Accounts section (and its `is_self`
  checkbox) is unchanged — see §2.

---

## 4. Tests updated (§5.3)

### Backend — `tests/ui/api/test_accounts.py` (14 → 18 cases)

- **Fixed** `test_create_book_round_trips_with_optional_fields`: the
  original used off-list values (`ownership_cluster="cluster-a"`,
  `platform="entain"`) which the new validation correctly rejects.
  Updated to listed values (`"Entain"` / `"BetMakers"`).
- **Added** `test_book_options_returns_both_locked_lists` — the endpoint
  mirrors `OWNERSHIP_CLUSTERS` / `PLATFORMS` exactly (and the 9 / 7
  locked counts).
- **Added** `test_create_book_accepts_listed_values` — a listed
  cluster + platform → 201.
- **Added** `test_create_book_rejects_unknown_cluster_with_422` — off-list
  cluster → 422 `UNKNOWN_OWNERSHIP_CLUSTER`, and asserts the book was
  **not** inserted.
- **Added** `test_create_book_rejects_unknown_platform_with_422` —
  off-list platform → 422 `UNKNOWN_PLATFORM`.
- Imports `OWNERSHIP_CLUSTERS, PLATFORMS` from the router so the test and
  the endpoint share one source.

### Frontend — `ui/web/src/routes/Accounts.test.tsx` (3 → 4 cases)

- **Added** `BOOK_OPTIONS` fixture and mocked `fetchBookOptions` in
  `beforeEach` (the Books section now queries it on mount).
- **Added** `renders the cluster + platform dropdowns from the options
  endpoint` — asserts the fields are `<select>`s populated from the
  options endpoint (incl. the empty "Uncategorised" option) and that
  selecting listed values POSTs them in the create-book payload.

No existing test changed behaviour. The deltas are exactly the new/fixed
cases (+4 backend, +1 frontend).

---

## 5. Verification (§7)

### Pre / post pass counts (read, not assumed)

| Suite | Command | Before | After |
|---|---|---|---|
| Backend | `uv run pytest -q` | **956 passed** | **960 passed** |
| Frontend | `npx vitest run` | **89 passed** (13 files) | **90 passed** (13 files) |

Both suites were fully green at session start (no pre-existing failures).
The two pre-existing `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings
remain (now 4, since the new validator uses the same alias as the racing
router — kept for codebase consistency; switching it project-wide is the
out-of-scope cleanup already noted in the original report's finding 3).

Typecheck + lint: `npx tsc --noEmit` clean; `eslint` clean on all three
changed frontend files.

### Live surface (real ASGI app via `TestClient`, temp DB, no network)

Exercised the mounted app directly (same ASGI app the suite uses;
zero external calls, throwaway temp DB deleted after):

- `GET /v1/books/options` → **200**, returns both locked lists in order
  (9 clusters, 7 platforms).
- `POST /v1/books` with a listed platform (`Custom`) + cluster
  (`Entain`) → **201**.
- `POST /v1/books` with an off-list platform (`"Nope"`) → **422**, code
  `UNKNOWN_PLATFORM`.

The screen renders the two `<select>`s from the options endpoint and a
categorised book round-trips through the create payload (vitest
component test). A literal human browser click-through remains the one
residual manual check (no headless browser installed — same posture and
hand-off as the original report's finding 4); the brief's §10 already
assigns the built-app `:5173` click-through to operator-Claude triage.

### Real v3 DB — empty and untouched (read-only, DR-013)

Opened the canonical `data/bethub.db` **read-only** (`file:…?mode=ro`)
via a `uv run python` process and counted:

```
accounts          0
books             0
accounts_at_book  0
```

The canonical `data/bethub.db` file is unchanged (mtime `16 Jun 16:21`,
pre-session; `-wal` still 0 bytes). The `-shm` sidecar's mtime ticked to
session time — a benign side effect of mapping the WAL index for a
read-only open; **no data was written** (content verified empty above,
and the main DB file is byte-unchanged). Never copied; never written.

---

## 6. Files changed (complete delta)

**Edited (5 — all named anchors):**

- `ui/api/routers/accounts.py` — option constants, `BookOptionsResponse`,
  `GET /v1/books/options`, `_validate_book_option`, validation call in
  `register_book`, `__all__`.
- `ui/web/src/api/accounts.ts` — `BookOptions` type, `fetchBookOptions`.
- `ui/web/src/routes/Accounts.tsx` — options query + query key, two
  `<select>` dropdowns (was two text inputs), imports.
- `tests/ui/api/test_accounts.py` — fixed 1 test, added 4, added import.
- `ui/web/src/routes/Accounts.test.tsx` — `BookOptions` fixture + mock,
  added 1 test, imports.

**Not touched (despite §5.1 listing them):** `store/schema/accounts.py`,
`store/repositories/accounts.py`, `domain/accounts/__init__.py`,
`ui/api/routers/racing.py`, `ui/web/src/api/racing.ts`, and the
`is_self` lines inside `accounts.py` / `accounts.ts` / `Accounts.tsx` /
the two accounts test files — all because §5.1 is halted (§2).

No git operations of any kind. No schema changes. No files outside the
named anchors. No "while we're here" cleanup.

---

## 7. Findings (surfaced, not chased)

1. **`is_self` is load-bearing outside the accounts surface — §5.1
   removal halted.** (See §2 for the full dependency map.) The racing
   log-panel account picker reads it live (`racing.py:769`,
   `racing.ts:176`, two racing test files), and it is a `NOT NULL`
   schema column inserted by ~10 downstream test suites and carried by
   the shared domain/repository. Removing it cleanly is a coordinated
   cross-surface change (racing picker behaviour + domain + a schema
   migration + downstream suites), all outside this brief's anchors and
   its "no schema changes beyond dropping `is_self`" allowance.
   **Routes to operator-Claude triage** to decide scope: whether the
   racing picker still needs a mine/household distinction at all, and if
   not, a single coordinated removal brief (including a column-drop
   migration, since v3 data is empty so no backfill is needed).

2. **`HTTP_422_UNPROCESSABLE_ENTITY` deprecation (unchanged posture).**
   The new validator uses the same deprecated status alias as the
   existing racing/accounts routers, adding two more identical
   `DeprecationWarning`s (4 total). Kept for consistency; a project-wide
   alias migration remains the separate, out-of-scope cleanup the
   original report already flagged.

No other deviations. No auto-login work, no lay-test, no seed script, no
new workstreams, no W16 routing — all per §9.

---

## 8. Self-assessment

- **Fit one session?** Yes. §5.2 is built, verified, and green; §5.1 was
  resolved at the discipline gate (halt + finding) rather than expanded
  into an out-of-scope cross-surface change.
- **Was the STOP the right call?** Yes — the brief names "racing page" as
  the exact trigger, and the grep found a live racing dependency plus a
  `NOT NULL` schema coupling. Proceeding would have either broken a
  downstream reader or left a half-removed field; both violate the
  contract.
- **Loose ends (all outside this brief):** the coordinated `is_self`
  removal (finding 1), the human browser click-through (brief §10), and
  the project-wide 422 alias migration (finding 2). Nothing in the §5.2
  locked scope was deferred.
