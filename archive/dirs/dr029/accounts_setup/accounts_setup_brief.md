# Accounts-setup build brief (v3)

**Drafted:** 2026-06-16 (Session 151), Claude Chat.
**For:** out-of-session Claude Code, single bounded session.
**Stream:** Accounts-setup (first W16 cutover dependency).
**Target codebase:** `/Users/tim/Desktop/Projects/bethub-v3`.

---

## 1. What this brief is and is not

This is a **build brief** for a new operator-facing capability:
the ability to add and manage betting accounts, bookmakers
(books), and account-at-book registrations inside v3, through a
web screen backed by HTTP endpoints.

- **Is:** a single bounded Code session that (a) exposes the
  already-built accounts data layer through a new API router,
  (b) builds a setup screen + nav route in the v3 frontend,
  (c) widens the CORS allow-list for v2/v3 coexistence.
- **Is not:** auto-login (a separate follow-up brief), the live
  lay test, any Betfair/live-pricing work, any schema change,
  any v2 data import. See §9 hard limits.
- Surprises become **findings in the report**, not mid-session
  pings or scope changes. Remediation routes to the next
  operator-Claude triage session, not Code.

## 2. Why this work exists

v3's racing core talks to live Betfair end-to-end (proven
Session 149). The one thing blocking real daily use and the
final live lay test is that **v3 cannot yet hold the operator's
books and accounts** — the database is empty and there is no
operator-facing way to populate it.

Session 150 scoped this and locked three operator calls:

1. **Fresh start** — no v2 import; clean build on v3's account
   model.
2. **Core earners first** — start lean; the operator adds the
   real earner books, expands over time.
3. **Setup screen** — a reusable in-v3 add/edit page, not a
   one-time seed script.

The Session 151 pre-flight probe (this session) confirmed the
accounts **data layer is already built** (W11): the three
tables and a full repository of safe write methods exist. This
brief therefore commissions the layers *above* that — the API
and the screen — plus the small CORS change for coexistence.

Accounts-setup is the first named dependency of the W16 cutover
(the v2-to-v3 switch).

## 3. Pre-reads

**Required (read before starting):**

- This brief, in full.
- `store/schema/accounts.py` — the three tables
  (`accounts`, `books`, `accounts_at_book`) and their columns.
- `store/repositories/accounts.py` — `SQLiteAccountsStorage`:
  the create/list/archive/register/close methods this brief
  exposes. Note the `RegisterResult` envelope (success + reason).
- `ui/api/main.py` — how routers are registered.
- `ui/api/routers/racing.py` — the established router pattern
  (pydantic request/response models, `Depends(...)`, the
  existing `get_accounts_storage` dependency at ~line 175 and
  `AccountsStorageDep` at ~line 277, and the read-only
  `GET /v1/racing/accounts` listing at ~line 748). Reuse
  `get_accounts_storage` / `AccountsStorageDep`; do not
  duplicate them.
- `ui/api/dependencies/composition.py` — confirms accounts
  storage is already wired (`_accounts_storage`,
  `get_accounts_storage` override). No new wiring needed.
- `ui/api/config.py` — the `cors_origins` setting (§5.7).
- `ui/web/src/App.tsx` — nav + route wiring (react-router-dom).
- `ui/web/src/api/racing.ts`, `client.ts`, `types.ts` — the
  frontend API-client pattern to follow.
- `ui/web/src/routes/Health.tsx` (+ `.module.css`,
  `.test.tsx`) — the simplest route-component precedent.

**Reference-only (consult if needed):**

- `dr029/accounts_setup/_drafts/SESSION_150_drafts.md` — the
  locked scope + earner grounding.
- `.importlinter` — DR-030 layer rules (§5 relies on these).
- `decisions.md` — DR-022, DR-030, DR-031.

## 4. System access

- **Mac filesystem, read-write**, scoped to
  `/Users/tim/Desktop/Projects/bethub-v3` and the named anchors
  only. No edits elsewhere.
- **v3 SQLite DB** at `bethub-v3/data/bethub.db` — touched only
  indirectly, through `SQLiteAccountsStorage` and the running
  app during verification. Do not hand-edit the DB file.
- **No VPS access. No Betfair access. No v2 access.**
- **Git working tree is dirty** (the v3 build is largely
  uncommitted). Treat dirty as the baseline state. Hard git
  limits in §9 — Code makes **no** git operations of any kind.
- **Adelaide local timestamps (ACST/ACDT)** per DR-021 for any
  time-of-day reference in the report.

---

## 5. Substantive scope

Layer order matches DR-030 (the module-boundary rules). Per
`.importlinter`, the `ui` layer may import the `store` layer
directly, so the API talks to `SQLiteAccountsStorage` **without
a workflow layer** — no `workflows/accounts` is built.

### 5.1 — New API router: `ui/api/routers/accounts.py`

A new router exposing the existing repository methods. Declare
routes under `/v1/accounts` (the `/api` prefix is added in
`main.py`). Use `AccountsStorageDep` from `racing.py` (reuse,
do not redefine). Pydantic request/response models follow the
`racing.py` style. Server generates the TEXT primary keys
(`uuid4().hex`) and the `created_at` timestamp — clients never
supply IDs. Follow the existing write path's timestamp
convention.

**Accounts**

- `GET  /v1/accounts` → `list_active_accounts()`.
- `POST /v1/accounts` → `create_account()`. Body:
  `name` (str), `is_self` (bool — "is this one of my own
  accounts" vs a household member's). Returns the created row.
- `POST /v1/accounts/{account_id}/archive` →
  `archive_account()`. Returns 200 if a row was updated, 404 if
  not found.

**Books**

- `GET  /v1/books` → `list_active_books()`.
- `POST /v1/books` → `register_book()`. Body: `name` (str),
  `ownership_cluster` (str, optional), `platform` (str,
  optional). The two optional fields default to null in v1.
- `POST /v1/books/{book_id}/archive` → `archive_book()`.

**Registrations (account-at-book)**

- `GET  /v1/accounts/{account_id}/books` →
  `list_active_accounts_at_book_for_account()`.
- `POST /v1/registrations` → `register_account_at_book()`.
  Body: `account_id`, `book_id`. Map the `RegisterResult`
  envelope to HTTP: success → 201; reason
  `ACCOUNT_ALREADY_REGISTERED_AT_BOOK` → 409;
  `MISSING_REFERENT` → 422. The response body carries a stable
  machine code plus a plain-English message the screen shows.
- `POST /v1/registrations/{account_at_book_id}/close` →
  `close_account_at_book()`. 200 / 404 as above.

PK collisions on insert raise (the repo's documented behaviour);
let them surface as 500 — they indicate a programmer error, not
an operator action.

### 5.2 — Register the router

- Export `accounts_router` from `ui/api/routers/__init__.py`
  alongside the existing router exports.
- In `ui/api/main.py`, add
  `app.include_router(accounts_router, prefix="/api")` next to
  the existing `include_router` calls. No other change to
  `main.py`.

### 5.3 — Frontend API client: `ui/web/src/api/accounts.ts`

Following the `racing.ts` / `provisional.ts` pattern, add a
typed client module wrapping the §5.1 endpoints via the shared
`client.ts` fetch helper. Add the request/response types to
`ui/web/src/api/types.ts` (or a co-located type block, matching
how `racing.ts` does it).

### 5.4 — Setup screen: `ui/web/src/routes/Accounts.tsx`

A new route component (plus `Accounts.module.css` and
`Accounts.test.tsx`) that lets the operator manage all three
entities. Use `@tanstack/react-query` for data (queries for the
three lists; mutations for create/register/archive/close, each
invalidating the relevant query on success). Three working
sections — function over polish (visual refinement is collected
on first real use, not this brief):

- **Accounts** — list active accounts; add-account form (name +
  an "my own account" toggle for `is_self`); archive control
  per row.
- **Books** — list active books; add-book form (name; optional
  cluster/platform); archive control per row.
- **Registrations** — for a selected account, show its
  registered books; a "register at book" control (pick account
  + book); a close control per registration. Surface the 409
  "already registered" and 422 "missing referent" responses as
  plain inline messages.

### 5.5 — Route + nav wiring: `ui/web/src/App.tsx`

Add a `<Route path="/accounts" element={<Accounts />} />` and a
nav `<Link to="/accounts">` (label: "Accounts"). No other
change to `App.tsx`.

### 5.6 — CORS widen: `ui/api/config.py`

The `cors_origins` default currently allows the v3 dev origin
on port 5173 only. v3's frontend auto-bumps to 5174 when v2
holds 5173, so during coexistence the API must accept both.
Widen the default to include both `http://localhost:5173` and
`http://localhost:5174` (and the `127.0.0.1` equivalents if the
existing entry uses that host form). This is the only change to
`config.py`.

### 5.7 — Tests

- **Backend (pytest):** a new test module for the accounts
  router, following the existing `tests/ui/api/` override
  pattern (install `app.dependency_overrides[get_accounts_storage]`
  with an in-memory or temp-file storage). Cover: create + list
  round-trip for each entity; the duplicate-registration 409;
  the missing-referent 422; archive/close happy path + 404.
- **Frontend (vitest):** a test for `Accounts.tsx` following the
  `Health.test.tsx` / `Racing.*.test.tsx` pattern, mocking the
  api client. Cover: the three lists render; an add submits and
  the list refreshes; the duplicate-registration error renders.
- Maintain the existing green baselines. Read the actual
  pre-change pass counts at session start (do not assume a
  number); the report records before and after.

---

## 6. Sequencing within session

1. Backend first: §5.1 router → §5.2 registration → §5.6 CORS.
2. Backend tests (§5.7 pytest); confirm green.
3. Verify the API round-trips (see §7) before touching the
   frontend.
4. Frontend: §5.3 client → §5.4 screen → §5.5 route/nav.
5. Frontend tests (§5.7 vitest); confirm green.
6. Manual smoke per §7.

A different order is fine if it reads cleaner to Code, but the
backend-before-frontend dependency is real (the screen calls
the endpoints).

## 7. Empirical verification

Capture both states so the report shows what moved.

**Pre:**
- Record pytest + vitest pass counts before any change.
- Confirm `GET /v1/accounts` / `/v1/books` return empty on the
  clean DB.

**Post (API round-trip — run against the live app):**
1. `POST /v1/accounts` (create "Test Account", `is_self=true`)
   → appears in `GET /v1/accounts`.
2. `POST /v1/books` (create "Test Book") → appears in
   `GET /v1/books`.
3. `POST /v1/registrations` (the two IDs above) → 201; appears
   in `GET /v1/accounts/{id}/books`.
4. Repeat step 3 → 409 `ACCOUNT_ALREADY_REGISTERED_AT_BOOK`.
5. `POST /v1/registrations` with a bogus `book_id` → 422
   `MISSING_REFERENT`.
6. Archive/close each → drops from the active listings.
7. **Clean up the test rows** so the operator's DB is left
   empty (or note clearly in the report if any test data
   remains).

**Post (screen smoke):** start backend + frontend, open
`/accounts`, add an account + book + registration through the
UI, confirm they persist across a page refresh.

**Post (tests):** pytest + vitest green; record the new counts.

---

## 8. Output spec

Single report at
`dr029/accounts_setup/accounts_setup_report.md`. Roughly
300–600 lines. Sections:

1. What was built (router, screen, CORS, tests) — concise.
2. Endpoint surface as delivered (path, method, repo method,
   status codes).
3. Screen shape as delivered (the three sections; any UI notes).
4. Tests added + baselines before/after.
5. Verification evidence — the §7 round-trip and smoke results.
6. Deviations / findings — anything that differed from this
   brief, any surprise surfaced (not chased).
7. Self-assessment — did it fit one session; was the length
   range right; anything left for follow-up.

The report contains **no** recommendations beyond surfaced
findings, **no** auto-login work, **no** lay-test steps.

## 9. Hard limits — NOT in scope

Code does none of the following:

- **Auto-login** — porting v2's self-refreshing Betfair login
  is the **next** brief. Do not touch the auth/credentials path
  (`StaticAuthProvider`, the credentials-file reader, session-
  token refresh) in this session.
- **The $5 lay test** and any live Betfair / live-pricing /
  order-placement work. This brief makes **zero** Betfair calls.
- **Schema changes** to `accounts` / `books` / `accounts_at_book`,
  including the additive tier/phase columns named in the W11
  brief §5.2. The three tables are taken as built.
- **v2 data import or any seed script.** Fresh start; the
  operator populates books/accounts through the screen. Do not
  pre-seed a book catalogue.
- **A `workflows/accounts` layer.** API → store directly is
  DR-030-legal; adding a workflow layer is out of scope.
- **Other routers/pages.** No edits to the racing, provisional,
  or health routers or their screens, beyond the App.tsx
  nav+route lines (§5.5) and the single CORS line (§5.6).
- **Named debt** (no test framework gaps chased, no orchestrator
  refactors).
- **Git operations of any kind** — no `add`, `commit`, `stash`,
  `restore`, `checkout`, `reset`. The tree is dirty as baseline;
  Code only creates/edits the named files and leaves git alone.
  Run `git status --short` at start and at end; the report notes
  the delta is only the expected new/changed files.

If the work does not fit one Code session, that is a **finding**
(stop at a coherent point and report), not a continuation past
budget.

## 10. What happens after Code's session

The next operator-Claude (Chat) session reads
`accounts_setup_report.md`, triages findings, and confirms the
screen works. Then:

- Claude drafts the **auto-login brief** (the next Code
  commission).
- Once auto-login lands and v3 is deployed in live mode with the
  operator's real Betfair account registered through this
  screen, the **$5 lay test** runs — closing the W17 racing-page
  go-live and clearing the path to the W16 cutover decision.

Code does not write the auto-login brief; that is the next
Chat session's work.

---

## 11. Cross-references

- **Scope:** `dr029/accounts_setup/_drafts/SESSION_150_drafts.md`
  (locked scope + earner grounding).
- **DRs:** DR-022 (book / account / account-at-book vocabulary),
  DR-027 / DR-028 (two-database split + boundary — accounts-setup
  is a cutover/cross-DB moment), DR-030 (v3 module boundaries —
  the ui→store-direct call in §5), DR-031 (v3 stack), DR-021
  (Adelaide timestamps).
- **Builds on:** the W11 accounts data layer
  (`store/schema/accounts.py`, `store/repositories/accounts.py`)
  and the W17 / W17.1 racing-router + composition-root patterns.
- **Excludes (parking-lot):** auto-login; the $5 lay test; the
  racing-page UI roughness; the sidebar empty-vs-error polish;
  W16 cutover scoping proper.
- **Build picture:** the Accounts-setup stream in
  `v3_build_picture.md`.
