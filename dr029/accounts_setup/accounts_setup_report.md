# Accounts-setup build report (v3)

**Session:** out-of-session Claude Code, single bounded session.
**Date:** 2026-06-16 (Adelaide local, ACST per DR-021).
**Brief:** `dr029/accounts_setup/accounts_setup_brief.md`.
**Target codebase:** `/Users/tim/Desktop/Projects/bethub-v3`.
**Outcome:** Complete. All §5 scope built, all baselines green, §7
verification passed. No git operations performed.

---

## 1. What was built

The accounts-setup capability — the operator-facing add/edit surface
for accounts, books, and account-at-book registrations — was built in
full across the three layers the brief commissioned (the W11 data layer
was already present and was not touched):

- **API router** (`ui/api/routers/accounts.py`) — a new thin HTTP
  adapter over `SQLiteAccountsStorage`, exposing nine routes under
  `/v1/accounts`, `/v1/books`, `/v1/registrations`. No `workflows`
  layer (DR-030 permits `ui → store` directly). Registered in
  `main.py` via `app.include_router(accounts_router, prefix="/api")`
  and exported from `ui/api/routers/__init__.py`.
- **CORS widen** (`ui/api/config.py`) — the `cors_origins` default now
  includes both `http://localhost:5173` and `http://localhost:5174`
  so the API accepts v3's frontend whether or not v2 is holding 5173.
- **Frontend API client** (`ui/web/src/api/accounts.ts`) — a typed
  module wrapping the nine endpoints via the shared `client.ts` fetch
  helper, with co-located types.
- **Setup screen** (`ui/web/src/routes/Accounts.tsx` +
  `.module.css`) — a three-section React page (Accounts, Books,
  Registrations) using `@tanstack/react-query` for queries and
  mutations, with inline error surfacing for the 409/422 registration
  cases.
- **Route + nav** (`ui/web/src/App.tsx`) — `/accounts` route and an
  "Accounts" nav link.
- **Tests** — `tests/ui/api/test_accounts.py` (14 backend cases) and
  `ui/web/src/routes/Accounts.test.tsx` (3 frontend cases).

Zero Betfair / live calls were made. All DB interaction during
verification ran against throwaway temp DBs via the documented
`BETHUB_DB_PATH` override; the operator's `data/bethub.db` was read
once (read-only, to confirm it was empty) and never written.

---

## 2. Endpoint surface as delivered

All paths carry the `/api` prefix added in `main.py` (so the live
paths are `/api/v1/...`). The server generates the TEXT primary keys
(`uuid4().hex`) and the `created_at` timestamp (Adelaide-local,
`datetime.now(ZoneInfo("Australia/Adelaide"))` — matching the racing
router's timestamp convention); clients never supply IDs.

| Method | Path | Repo method | Status codes |
|---|---|---|---|
| GET  | `/v1/accounts` | `list_active_accounts()` | 200 |
| POST | `/v1/accounts` | `create_account()` | 201 |
| POST | `/v1/accounts/{account_id}/archive` | `archive_account()` | 200 / 404 |
| GET  | `/v1/books` | `list_active_books()` | 200 |
| POST | `/v1/books` | `register_book()` | 201 |
| POST | `/v1/books/{book_id}/archive` | `archive_book()` | 200 / 404 |
| GET  | `/v1/accounts/{account_id}/books` | `list_active_accounts_at_book_for_account()` | 200 |
| POST | `/v1/registrations` | `register_account_at_book()` | 201 / 409 / 422 |
| POST | `/v1/registrations/{account_at_book_id}/close` | `close_account_at_book()` | 200 / 404 |

**Request bodies:**

- `POST /v1/accounts` — `{ "name": str, "is_self": bool }`.
- `POST /v1/books` — `{ "name": str, "ownership_cluster": str|null,
  "platform": str|null }` (the two optional fields default to null).
- `POST /v1/registrations` — `{ "account_id": str, "book_id": str }`.

**Registration envelope mapping** (from `RegisterResult`):

- success → **201**, returns the created registration row.
- reason `ACCOUNT_ALREADY_REGISTERED_AT_BOOK` → **409**.
- reason `MISSING_REFERENT` → **422**.

The 409/422 body is
`{"detail": {"code": "<machine code>", "message": "<plain English>"}}`
— the screen renders the `message` inline. The machine `code` is the
exact `RegisterResult.reason` string, so the surface is stable for any
future consumer.

**Archive / close** return `{"changed": true}` on 200 (a stable JSON
shape rather than an empty body) and 404 when no active row matched.

**PK collisions** on insert raise from the repository and surface as
500 — per the brief, a programmer error rather than an operator
action. These are not caught.

---

## 3. Screen shape as delivered

Route `/accounts`, reached from the new "Accounts" nav link (placed
between "Burst review" and "Health"). One page, three sections, each
with a list + add-form + soft-delete control. Function over polish,
per the brief — minimal CSS, no visual refinement beyond legibility.

- **Accounts** — lists active accounts; add-account form (name input +
  a "My own account" checkbox bound to `is_self`, default on); an
  "Archive" button per row. Empty / loading / error states surface
  explicitly.
- **Books** — lists active books; add-book form (name + optional
  cluster + optional platform; blank optional fields submit as null);
  cluster/platform shown as small tags when present; "Archive" per row.
- **Registrations** — an account `<select>` drives the section. Once an
  account is picked, the page shows that account's active registrations
  and a "register at book" form (a book `<select>` + "Register at
  book"). A "Close" button per registration row. The 409 "already
  registered" and 422 "missing referent" responses render as a plain
  inline `role="alert"` message (the server's plain-English `message`).

Data flow: one `useQuery` per list (`['accounts']`, `['books']`,
`['registrations', accountId]`); one `useMutation` per write, each
invalidating the list(s) it touches on success, so the lists refresh
without a manual reload. The registrations query is `enabled` only
when an account is selected.

**UI notes:**

- Entity names appear both in their list and in the section
  `<select>` controls — expected, since the registration section needs
  to pick an account/book by name.
- The screen reuses the existing `apiGet` / `apiPost` helpers and the
  `ApiError` type; the registration error path reads `ApiError.detail`
  to pull out the server's `message`.

---

## 4. Tests added + baselines

### Baselines (read at session start, before any change)

| Suite | Command | Before | After |
|---|---|---|---|
| Backend | `uv run pytest -q` | **942 passed** | **956 passed** |
| Frontend | `npx vitest run` | **86 passed** (12 files) | **89 passed** (13 files) |

No pre-existing failures in either suite at session start (the brief
said to read the actual numbers rather than assume; both suites were
fully green). The deltas are exactly the new tests (+14 backend, +3
frontend); no existing test changed behaviour.

> **Environment note (finding, see §6):** the suites must be run
> through the project's `uv` environment (`uv run pytest`,
> `npx vitest`). The machine's bare `python3` lacks `httpx`, so a
> plain `python3 -m pytest` fails at collection on every
> `TestClient`-based module. This is an environment-invocation detail,
> not a code issue.

### Backend tests — `tests/ui/api/test_accounts.py` (14 cases)

Follows the existing `tests/ui/api/test_racing.py` override pattern:
`app.dependency_overrides[get_accounts_storage]` is installed with a
per-request factory that opens `SQLiteAccountsStorage` against a
`tmp_path` SQLite file (per-request because the TestClient runs the
route in a worker thread and SQLite forbids cross-thread connection
sharing; `apply_migrations` is idempotent so re-open is safe).

Coverage:

- create + list round-trip for accounts, books, and registrations;
- empty-listing on a clean DB (accounts + books);
- book optional fields persist when supplied and default to null when
  omitted;
- duplicate registration → 409 with `code ==
  ACCOUNT_ALREADY_REGISTERED_AT_BOOK`;
- missing-referent registration → 422 with `code == MISSING_REFERENT`;
- archive account / archive book / close registration happy paths
  (row drops from the active listing) + their 404s.

### Frontend tests — `ui/web/src/routes/Accounts.test.tsx` (3 cases)

Follows the `Health.test.tsx` pattern, mocking the `../api/accounts`
client module (`vi.mock`) and rendering under a fresh `QueryClient`:

- the three lists render (accounts, books, and — after selecting an
  account — registrations);
- an add-account form submits with the right payload and the list
  refreshes to show the new row;
- the duplicate-registration error renders inline (an `ApiError` with
  the 409 `{code, message}` detail → the plain message appears).

---

## 5. Verification evidence (§7)

### Pre

- `GET /v1/accounts` and `/v1/books` both returned `[]` on a clean DB.
- The operator's real `data/bethub.db` was confirmed empty
  (read-only): `accounts 0`, `books 0`, `accounts_at_book 0`.

### Post — API round-trip (live app, `uvicorn` on a temp DB)

Ran against `uvicorn ui.api.main:app` with
`BETHUB_DB_PATH=/tmp/dr029_roundtrip.db`. Results matched the brief
step-for-step:

1. `POST /v1/accounts` ("Test Account", `is_self=true`) → 201; row
   appeared in `GET /v1/accounts`.
2. `POST /v1/books` ("Test Book") → 201; row appeared in
   `GET /v1/books` (optional fields null).
3. `POST /v1/registrations` (the two IDs) → **201**; appeared in
   `GET /v1/accounts/{id}/books`.
4. Repeat of step 3 → **409**, body
   `{"code":"ACCOUNT_ALREADY_REGISTERED_AT_BOOK","message":"This
   account is already registered at this book."}`.
5. `POST /v1/registrations` with a bogus `book_id` → **422**, body
   `{"code":"MISSING_REFERENT","message":"The selected account or book
   no longer exists."}`.
6. Close registration → 200; account's book listing → `[]`. Archive
   account → 200; accounts listing → `[]`. Archive book → 200; books
   listing → `[]`.
7. 404 checks: archive unknown account → 404; close unknown
   registration → 404.

**Test-data cleanup:** the round-trip ran entirely against a throwaway
temp DB (`/tmp/dr029_roundtrip.db`), which was deleted at session end.
The operator's `data/bethub.db` was never written and remains empty
(re-confirmed `0 / 0 / 0` at session end). No test rows persist
anywhere.

### Post — screen smoke

Started the backend on `:8000` (temp DB `/tmp/dr029_smoke.db`) and the
Vite dev server on `:5173`:

- The SPA serves the `/accounts` route (returns the app
  `index.html` with the React root + `main.tsx` entry — client-side
  routing then renders the screen).
- **CORS coexistence confirmed:** a preflight from origin
  `http://localhost:5174` returned `200` with
  `access-control-allow-origin: http://localhost:5174`, and an actual
  GET from `http://localhost:5173` returned the matching allow-origin.
  Both dev origins are now accepted (the §5.6 change, verified live).
- **Persistence across refresh:** exercised the exact endpoints the
  mounted screen calls (`POST` account/book/registration, then the
  three `GET` lists the screen re-runs on mount) against `:8000`; the
  created rows were returned by the re-fetch, i.e. they survive the
  remount a browser page-refresh performs.
- **Production build:** `npm run build` (`tsc -b && vite build`)
  succeeded with the new screen included (97 modules transformed).
- **Typecheck + lint:** `npx tsc --noEmit` clean; `eslint` clean on
  all new/changed frontend files.

The one verification step not performed literally is a *human browser
click-through* of the page — no headless browser (Playwright/Puppeteer)
is installed in the project, and the discipline rule (zero external
calls) ruled out triggering a browser download. The screen's behaviour
is instead evidenced by: the vitest component test (renders + submit +
error-render), the live API round-trip against the same endpoints, the
served-route check, the CORS check, and the green production build.
See §6.

### Git delta (start vs end)

`git status --short` at session end is **byte-identical** to the
start-of-session baseline. All files created/edited by this session
live inside directories that were already untracked at baseline
(`ui/api/`, `ui/web/`, `tests/ui/`) — git collapses those to the
directory name, so no new top-level entry appears, and the tracked
modified (` M`) list is unchanged. Confirmed at the file level with
`git status --short -uall` that the four *edited* files
(`ui/api/main.py`, `ui/api/config.py`, `ui/api/routers/__init__.py`,
`ui/web/src/App.tsx`) are untracked (`??`) — i.e. no committed file
was modified. **No git operations of any kind were run.**

Files created/edited (the complete delta):

- **Created:** `ui/api/routers/accounts.py`,
  `tests/ui/api/test_accounts.py`, `ui/web/src/api/accounts.ts`,
  `ui/web/src/routes/Accounts.tsx`,
  `ui/web/src/routes/Accounts.module.css`,
  `ui/web/src/routes/Accounts.test.tsx`.
- **Edited:** `ui/api/routers/__init__.py` (export `accounts_router`),
  `ui/api/main.py` (import + `include_router`), `ui/api/config.py`
  (CORS widen), `ui/web/src/App.tsx` (route + nav link).

Every one of these is a file the brief named in §5. No adjacent code
was touched.

---

## 6. Deviations / findings

Nothing in the brief's scope was changed. The items below are
surface-level surprises surfaced (not chased), per the discipline
rule.

1. **`types.ts` is auto-generated; co-located types used instead.**
   `ui/web/src/api/types.ts` carries a "Do not make direct changes"
   banner (it is produced by `openapi-typescript` via
   `npm run generate-api-types`). The brief explicitly permitted "a
   co-located type block, matching how `racing.ts` does it", so
   `accounts.ts` defines its own types and does **not** edit
   `types.ts`. Consequence: the generated `types.ts` does not yet
   describe the new endpoints. Re-running `npm run generate-api-types`
   against a running server (out of scope here) would add them; the
   hand-rolled types match the router exactly in the meantime. This is
   the same posture `provisional.ts` already takes.

2. **Test environment must be `uv` / project `node_modules`.** As
   noted in §4: the bare system `python3` lacks `httpx`, so
   `python3 -m pytest` fails at collection. The working invocations are
   `uv run pytest` and (from `ui/web`) `npx vitest`. This is a runner
   detail for whoever re-runs the suites, not a code change.

3. **`HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning.** The router
   uses `status.HTTP_422_UNPROCESSABLE_ENTITY`, matching the existing
   `racing.py`. The installed Starlette version deprecates that alias
   in favour of `HTTP_422_UNPROCESSABLE_CONTENT`, emitting one
   `DeprecationWarning` (the same warning the racing suite already
   emits at baseline). Kept the existing spelling for codebase
   consistency; switching the alias project-wide is a separate,
   out-of-scope cleanup.

4. **No headless browser for a literal UI click-through.** The
   project has no Playwright/Puppeteer installed. Rather than trigger a
   browser download (which would breach the zero-external-calls rule),
   the screen smoke was completed at the HTTP layer plus the vitest
   component test (see §5). A human browser click-through remains the
   one residual manual check — flagged for the next operator-Claude
   triage session, which the brief (§10) already assigns to "confirm
   the screen works".

No schema changes, no auto-login work, no lay-test steps, no seed
script, no `workflows/accounts` layer, no edits to other
routers/pages beyond the App.tsx and config.py lines the brief named.

---

## 7. Self-assessment

- **Did it fit one session?** Yes, comfortably and at a coherent
  stopping point. The full §5.1–§5.7 scope is built, both baselines
  are green with the new tests added, and the §7 verification ran end
  to end.
- **Was the length range right?** The 300–600-line report range fits;
  this report sits within it. The build itself was right-sized for one
  bounded session — the data layer being pre-built (W11) is what made
  the API + screen + tests achievable in a single pass.
- **Anything left for follow-up** (surfaced, not actioned):
  - Re-run `npm run generate-api-types` so `types.ts` covers the new
    endpoints, if the project wants the generated types in sync
    (finding 1).
  - A human browser click-through of `/accounts` during the next
    triage session (finding 4).
  - Optional, project-wide: migrate the deprecated `422` status alias
    (finding 3) — affects the existing racing router too, so it is not
    an accounts-setup concern.
- These are the only loose ends, and all three are explicitly outside
  this brief's scope. Nothing in the locked scope was deferred.
