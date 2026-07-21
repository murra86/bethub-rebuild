# W7 — Web layer skeleton brief

**Drafted:** 2026-05-08 (Adelaide local per DR-021)
**Source spec:** DR-031 (v3 tech stack — locked Session 79),
DR-030 (v3 repo layout — locked Session 79),
`dr029/2_6_settlement_race/2_6_settlement_race.md` §3.5
(burst-review surfacing contract — the consumer downstream of W7
that motivates the skeleton's shape).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`
**Python interpreter:** `.venv/bin/python` (3.12.7)
**Status:** Locked, ready for Code dispatch.

---

## §1 What this brief is and is not

**This brief is.** A substrate brief that stands up the v3 web
layer skeleton — the FastAPI HTTP application under `ui/api/`,
the React + TypeScript + Vite frontend under `ui/web/`, and the
integration shape between them. The skeleton ships a working
end-to-end smoke-test page that proves the stack works: a frontend
page hits a FastAPI endpoint, gets a real response, renders it.
The skeleton is the substrate W8 (burst-review queue pages) builds
on.

**This brief is not.** Not the burst-review queue UI itself —
that's W8 territory and stays out of scope here. Not a full app
shell with navigation, authentication, or styling — those are
build-proper concerns and earn their place when there's more
than one page to navigate between. Not a deployment story — the
skeleton runs in dev mode locally; production-deploy lives under
`ops/` and is post-DR-029 work. Not a state-management
architecture decision beyond the defaults named in §5.5.

**Surprises become findings, not blockers.** If Code hits a
package-version conflict, a build-chain quirk, or a structural
question the brief didn't anticipate, the response is: capture it
as a finding in §8 of the report, make a defensible choice
inline, continue. Operator-Claude triage at W7 report review
routes the finding — Code does not pause mid-session for
direction.

---

## §2 Why this work exists

W4-W6.5 has been building the Python-side substrate the
burst-review feature needs (bet records, reconciliation worker,
settlement worker, the `ProvisionalSettlementSurfacingPayload`
data shape). All of it is library code with no HTTP surface and
no operator-facing UI.

Session 100's three carry items (settings-area cadence control,
per-bet modal override, greyhound operational constraint) were
originally tagged for "W7 burst-review brief drafting." Session
106 reshaped that scope: the burst-review queue UI is W8;
the carry items move to W8 where they have a UI surface to attach
to.

W7 stands up the web layer that everything operator-facing rides
on — first the burst-review queue (W8), then in time the bet-entry
surface, the AccountCare surface, the racing/sports screens, the
settings area. Doing it as a dedicated substrate brief lets the
structural decisions (FastAPI app shape, frontend tooling,
integration shape) be made carefully without being tangled up
inside a feature brief. Every downstream UI brief inherits the
shape locked here.

DR-030 already locks `ui/` as a top-level layer that imports
workflows/domain/store/clients but is not imported by them.
DR-031 locks the tech stack (FastAPI + React + TypeScript +
Vite). W7's job is to translate those locked decisions into a
working skeleton.

---

## §3 Pre-reads

**Required (read before starting):**

- This brief, end-to-end.
- `decisions.md` §DR-030 (repo layout + import-graph rules) and
  §DR-031 (tech stack).
- `.importlinter` (rebuild folder root has the canonical, the v3
  copy at `bethub-v3/.importlinter` is what's enforced) — confirm
  the locked layering before adding `ui/api/` and `ui/web/`
  imports.
- `pyproject.toml` — current dependency state and tooling config.

**Reference-only (consult on demand, not required-reads):**

- `dr029/2_6_settlement_race/2_6_settlement_race.md` §3.5
  (burst-review surfacing contract) — context for what shape the
  W8 queue pages will eventually need from the API. W7 doesn't
  build queue endpoints; it builds the skeleton W8 attaches to.
- `dr029/2_9_write_side/2_9_write_side.md` — the broader
  bet-entry write-side picture; reference for understanding what
  other workflows the API will eventually expose.
- `decisions.md` §DR-008 (Smart Betfair view), §DR-022
  (vocabulary — book/account/account-at-book) — context for
  future operator-facing surfaces, not load-bearing for skeleton.
- `architecture.md` — orientation primer if Code needs the
  broader v3 picture.
- `dr029/w4_bet_entry/w6_5_settlement_worker_brief.md` and
  `w6_5_settlement_worker_report.md` — most recent precedent for
  brief shape and report cadence.

---

## §4 System access

**Read-write on:** `bethub-v3/` working tree only. Specifically:

- New directories: `ui/api/`, `ui/web/`.
- Modifications: `pyproject.toml` (add FastAPI + uvicorn already
  present; potentially add httpx or other support libraries if
  needed for testing the skeleton); `.importlinter` if
  `ui/api/` and `ui/web/` need to be split into separate
  importable packages (note: `ui/web/` is TypeScript/JavaScript,
  not Python — won't appear in `import-linter` graph).
- New files: skeleton code, configuration files, build-chain
  config, test files, smoke-test page.

**Read-only on:**

- All other directories under `bethub-v3/` (workflows/, clients/,
  store/, domain/, contracts/, tests/, ops/).
- The rebuild folder governance docs (this brief, the spec docs,
  decision records).

**No access required:** No live Betfair API, no VPS, no
`capture.db`, no v2 codebase. The skeleton ships with a smoke-test
page that hits an in-process FastAPI endpoint returning canned
data — no external dependencies.

**Adelaide local timestamps per DR-021** for any time-of-day
references in the report (start/end timestamps,
`pytest --collect-only` snapshots, etc.).

---

## §5 Substantive scope

Nine sub-sections, each carrying named anchors and structural
decisions. Code implements against §5.1-§5.9 in dependency order
per §6.

### §5.1 — Repo layout under `ui/`

Two new sibling directories under `ui/`:

- **`ui/api/`** — FastAPI Python application. Treated as a
  standard Python package (has `__init__.py`, importable from
  tests, lints against `import-linter`). All Python source for
  the HTTP layer lives here.
- **`ui/web/`** — React + TypeScript + Vite frontend.
  TypeScript/JavaScript code, build output, package.json,
  tsconfig, etc. Not a Python package — `import-linter` does not
  see it.

The existing empty `ui/__init__.py` stays (keeps `ui` as a
Python namespace per the import-linter `root_packages` list).

**Subdirectories under `ui/api/`** (proposed structure; Code
adapts if a cleaner shape surfaces):

```
ui/api/
├── __init__.py
├── main.py              # FastAPI app instance, lifecycle wiring
├── routers/             # Route modules grouped by feature
│   ├── __init__.py
│   └── health.py        # /api/health smoke-test endpoint (W7 lands)
├── dependencies/        # FastAPI dependency-injection helpers
│   └── __init__.py
├── middleware/          # Middleware (CORS, error handling, logging)
│   └── __init__.py
└── config.py            # App configuration (env vars, settings)
```

**Subdirectories under `ui/web/`** (Vite default scaffold,
TypeScript variant):

```
ui/web/
├── package.json
├── package-lock.json    # or pnpm-lock.yaml — Code's call
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── index.html
├── public/
└── src/
    ├── main.tsx         # React app entry
    ├── App.tsx          # Root component
    ├── routes/          # Page components (W7: smoke-test page)
    │   └── Health.tsx
    ├── api/             # API client code (OpenAPI-generated)
    │   └── (generated)
    └── styles/          # CSS modules
```

### §5.2 — FastAPI app skeleton (`ui/api/`)

**`ui/api/main.py`.** Creates the `FastAPI` app instance with:

- `title="BetHub v3"`, `version="0.1.0"`.
- OpenAPI docs at `/api/docs` (Swagger UI) and `/api/redoc`.
- OpenAPI JSON spec at `/api/openapi.json` — load-bearing for
  §5.6 (OpenAPI client generation).
- Lifecycle hooks (`startup` / `shutdown`) wired empty for now;
  W8+ will attach the settlement-worker scheduler and other
  background tasks here.
- Router includes for everything in `ui/api/routers/`.

**`ui/api/routers/health.py`.** One endpoint:
`GET /api/health` returning `{"status": "ok",
"timestamp": <Adelaide-local ISO8601>, "version": "0.1.0"}`.
Pydantic v2 response model named `HealthResponse`.

**`ui/api/middleware/`.** Empty package at v1; no middleware
land in W7. Comment-only `__init__.py` reserves the namespace
for W8+.

**`ui/api/dependencies/`.** Empty package at v1; same comment.

**`ui/api/config.py`.** A `Settings` Pydantic model with:

- `app_name: str = "BetHub v3"`
- `cors_origins: list[str] = ["http://localhost:5173"]` —
  the Vite dev-server origin.
- `environment: Literal["dev", "prod"] = "dev"`.
- Read from environment variables via `pydantic-settings`
  (add to `pyproject.toml` if not already present — verify
  pre-flight).

**Note on `pydantic-settings`.** If not in deps, add to
`pyproject.toml` `dependencies` list. Code's call on whether to
use it or hand-roll env-var reading; `pydantic-settings` is the
idiomatic pattern.

### §5.3 — CORS and dev-server integration

The Vite dev-server runs on `http://localhost:5173` by default.
The FastAPI app runs on `http://localhost:8000` by default. In
dev, the frontend hits the API cross-origin — CORS middleware on
the FastAPI side allows the Vite origin.

**`ui/api/main.py` registers the CORS middleware:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

In production (later, post-DR-029), the frontend's built static
assets will be served by FastAPI itself (same origin, no CORS
needed). The `environment: Literal["dev", "prod"]` switch in
`config.py` is the seam where production-static-serving lands
later. W7 ships dev-mode only.

### §5.4 — React + Vite + TypeScript skeleton (`ui/web/`)

**Bootstrap via `npm create vite@latest ui/web/ -- --template
react-ts`** (or pnpm equivalent — Code's call). The default
scaffold is the starting point; the brief specifies adaptations
below.

**Routing — React Router v6.** Add `react-router-dom@^6` to
`package.json`. `App.tsx` wraps the routes in `<BrowserRouter>`;
W7 ships one route: `/health` rendering the `<Health>` component.
W8+ adds more routes.

**State / data fetching — TanStack Query.** Add
`@tanstack/react-query` to `package.json`. `App.tsx` wraps the
app in `<QueryClientProvider>`. The smoke-test page uses
`useQuery` to fetch `/api/health` and render the response.

**Styling — plain CSS modules.** Vite's React-TS template
supports CSS modules out of the box. The smoke-test page has a
companion `Health.module.css` showing the pattern. No Tailwind,
no styled-components, no CSS-in-JS.

**Strict TypeScript.** `tsconfig.json` enables `strict: true`,
`noUnusedLocals: true`, `noUnusedParameters: true`. Vite's
default React-TS template ships strict-mode-friendly already;
W7 confirms the settings.

**Linting — ESLint default from Vite scaffold.** The Vite
template ships with ESLint configured for React + TypeScript.
W7 keeps the defaults; no custom rules.

### §5.5 — OpenAPI client generation

The FastAPI app auto-generates an OpenAPI 3 spec at
`/api/openapi.json`. The frontend uses `openapi-typescript` (or
equivalent) to generate TypeScript types from this spec, giving
the frontend type-safe access to API endpoints.

**Tooling.** Add `openapi-typescript` as a `devDependency` in
`ui/web/package.json`. Add a script:

```json
"scripts": {
  "generate-api-types": "openapi-typescript http://localhost:8000/api/openapi.json -o src/api/types.ts"
}
```

**Workflow.** Developer runs FastAPI in dev mode, runs
`npm run generate-api-types`, the resulting `src/api/types.ts`
provides typed paths/methods/responses. The smoke-test page
demonstrates this: it imports `HealthResponse` type from the
generated file and uses it in the `useQuery` call.

**Note.** The generated file is committed to source control,
not gitignored. Regeneration is manual — when the API surface
changes, the developer regenerates and reviews the diff. This is
the simplest workable shape; CI auto-regen is a future
enhancement.

**Minimal API client wrapper.** A thin `ui/web/src/api/client.ts`
module exposes a typed `fetch` wrapper using the generated types.
Shape:

```typescript
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`http://localhost:8000${path}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json() as Promise<T>;
}
```

W7 ships only `apiGet`; `apiPost`, `apiPatch`, etc. land in W8+
when they're actually needed. Keep the surface minimal.

### §5.6 — Smoke-test page

**Purpose.** Prove the full stack works end-to-end: FastAPI
serves a request, the OpenAPI spec generates types, the frontend
imports the types, TanStack Query fetches the endpoint,
React renders the response.

**`ui/web/src/routes/Health.tsx`.** A React component that:

- Uses `useQuery({ queryKey: ['health'], queryFn: () =>
  apiGet<HealthResponse>('/api/health') })`.
- Shows a loading state while fetching.
- Shows an error state if the fetch fails.
- Shows the response on success: status, timestamp, version.
- Has minimal CSS via `Health.module.css` to make the page
  visually navigable (not styled — just laid out).

**Wired in `App.tsx`** as the route for `/` (root path) and
`/health` (both paths render the same component at v1; W8 will
introduce a real router shape).

### §5.7 — Tests

Three layers of tests; all run as part of the existing pytest
suite where applicable, or via the new frontend test runner.

**Backend tests — `tests/ui/api/`** (new directory,
parallel to `tests/clients/`, `tests/workflows/`).

- `tests/ui/api/__init__.py` (empty package marker).
- `tests/ui/api/test_health.py` — pytest tests using FastAPI's
  `TestClient`:
  - `test_health_endpoint_returns_ok_status` — GET /api/health
    returns 200 with `{"status": "ok", ...}`.
  - `test_health_endpoint_returns_adelaide_timestamp` — confirms
    the timestamp is Adelaide-local (parses, checks tzinfo).
  - `test_health_endpoint_returns_correct_version` — version
    matches `pyproject.toml` value.
  - `test_app_includes_cors_middleware` — confirms
    `CORSMiddleware` is in the app's middleware stack.
  - `test_app_exposes_openapi_spec` — GET /api/openapi.json
    returns 200 with valid OpenAPI 3 JSON.

**Frontend tests — `ui/web/src/`** (Vite scaffold ships with
Vitest).

- `ui/web/src/routes/Health.test.tsx` — Vitest + React Testing
  Library:
  - Component renders loading state initially.
  - Component renders response on successful fetch (mocked).
  - Component renders error state on fetch failure.

The Vite scaffold's default test setup is sufficient; no
additional libraries beyond what `npm create vite` ships.

**Smoke-test (manual, documented in README).** A
`ui/web/README.md` documents how to run the full stack:

1. Terminal 1: `cd /path/to/bethub-v3 && uvicorn ui.api.main:app
   --reload --port 8000`.
2. Terminal 2: `cd ui/web && npm run dev`.
3. Browser: `http://localhost:5173/health` shows the smoke-test
   page rendering live API response.

This isn't an automated test; it's a documented validation
procedure for operator-Claude review at the report stage.

### §5.8 — `import-linter` configuration

Verify `.importlinter` already lists `ui` as a `root_package` —
it does (line 7 of the current config).

`ui.api` will appear in the import graph as a sub-module of
`ui`. The existing `[importlinter:contract:layers]` already has
`ui | ops` at the top layer with arrows down to `workflows |
domain | store | clients`. **No `.importlinter` changes needed**
unless Code surfaces an unexpected import that breaks the
existing rules — flag as a finding if so.

`ui/web/` is TypeScript/JavaScript and is invisible to
`import-linter` (it scans Python only).

### §5.9 — `__init__.py` exports and module-level conventions

**`ui/__init__.py`** — empty, namespace marker only.

**`ui/api/__init__.py`** — exports the `app` instance:

```python
from ui.api.main import app

__all__ = ["app"]
```

This lets `uvicorn ui.api:app` work as an alternative to the
explicit `uvicorn ui.api.main:app`. Convention-only; both forms
work.

**`ui/api/routers/__init__.py`** — exports each router for
inclusion in `main.py`:

```python
from ui.api.routers.health import router as health_router

__all__ = ["health_router"]
```

W8+ adds more routers; the `__all__` list grows then.

---

## §6 Sequencing within session

Order of work, with dependency reasoning. Code can deviate where
a different order is operationally cleaner, but the dependencies
must hold.

1. **Pre-flight reads** — pyproject.toml, .importlinter,
   existing ui/__init__.py to confirm empty state.
2. **§5.1 — Repo layout.** Create `ui/api/` and `ui/web/`
   directories with their initial structure. Empty
   `__init__.py`s, empty placeholder dirs. Smallest possible
   first commit-equivalent step.
3. **§5.2 — FastAPI app skeleton.** Land `main.py`,
   `config.py`, `routers/health.py`. Verify with
   `python -c "from ui.api.main import app; print(app.title)"`.
4. **§5.3 — CORS middleware.** Wire CORS into `main.py`.
5. **§5.7 — Backend tests first** (before frontend, so the
   FastAPI app is verified before the frontend depends on it).
   `pytest tests/ui/api/` should be green before moving on.
6. **§5.4 — Frontend scaffold.** Run `npm create vite@latest`
   in `ui/web/`. Adapt scaffold per §5.4 (add React Router,
   TanStack Query, openapi-typescript).
7. **§5.5 — OpenAPI client generation.** With FastAPI running,
   regenerate types. Verify the generated `types.ts` file.
8. **§5.6 — Smoke-test page.** Build `Health.tsx` and the route.
   Verify manually per §5.7's smoke-test procedure.
9. **§5.7 — Frontend tests.** Vitest tests for `Health.tsx`.
10. **§5.9 — Cleanup.** Verify `__init__.py` exports, run full
    pytest suite, run `ruff check`, run `lint-imports`, run
    frontend tests.

**The §5.5 → §5.6 boundary is the integration moment.** If
something is going to break, it breaks here — the OpenAPI
generation step requires both halves to be talking. Code spends
more attention here than elsewhere.

---

## §7 Empirical verification

### §7.1 — Pre-baseline (capture at session start)

```bash
cd /Users/tim/Desktop/Projects/bethub-v3
.venv/bin/pytest --collect-only -q | tail -5
.venv/bin/ruff check
.venv/bin/lint-imports
git status
ls -la ui/
```

Expected pre-state:

- `pytest --collect-only -q` shows 458 tests (W6.5 ship state).
- `ruff check` clean.
- `lint-imports` 5 contracts kept, 0 broken.
- `git status` matches W6.5 ship state (modified
  `clients/betfair_client/v1/__init__.py` and
  `_translation.py`; untracked dirs as before).
- `ls -la ui/` shows only `__init__.py` (empty).

### §7.2 — Post-baseline (capture at session end)

Same commands. Expected post-state:

- `pytest --collect-only -q` shows 458 + N tests, where N is the
  count of new backend tests added in §5.7. Estimate: 5 backend
  tests, so ~463 total.
- `ruff check` clean (including the new `ui/api/` files).
- `lint-imports` still 5 contracts kept, 0 broken (or 6 if
  Code adds a new contract for `ui.api` specifically — flag in
  report if so).
- `git status` shows the new `ui/api/`, `ui/web/`, `tests/ui/`
  directories untracked. Existing untracked / modified entries
  unchanged.
- `ls -la ui/` shows `__init__.py`, `api/`, `web/`.

### §7.3 — Smoke-test verification

Manual procedure per §5.7. Code documents in the report whether
the smoke-test ran successfully and includes a screenshot
description (text only — Code can't actually screenshot, but
describes what the smoke-test page renders when working).

### §7.4 — Frontend test run

```bash
cd ui/web
npm install     # idempotent on second run
npm run test    # Vitest
npm run build   # confirm production build succeeds
```

The build step is a sanity check that the TypeScript compiles
end-to-end (Vite's build does TypeScript checking). Capture
output in the report.

### §7.5 — Test count delta

Capture pre and post test counts for both backend (pytest) and
frontend (vitest). Report shows the delta clearly.

Acceptable band: backend +4 to +8; frontend +3 to +6. Outside
either band → flag in §6 deviations.

---

## §8 Output spec

Single named file: `dr029/w4_bet_entry/w7_web_layer_skeleton_report.md`.

**Section structure mirrors W6.5's report shape, adapted for
substrate:**

- §1 Summary — what landed; named-anchor checklist.
- §2 Files changed — table with pre/post LOC per file, status,
  status. Includes both Python and TypeScript files.
- §3 Test count delta — pre/post for both pytest and vitest.
- §4 New tests added — listed by name, organised by §5.x
  anchor.
- §5 Implementation notes — one subsection per §5.x anchor,
  capturing what landed and any in-session decisions.
- §6 Deviations from brief — if any. Empty list is fine.
- §7 Open questions for triage — for operator-Claude routing in
  the next session.
- §8 Findings beyond brief scope — anything Code surfaced that
  wasn't in scope but seemed worth recording.
- §9 Self-assessment — pre/post baselines table; functional
  verification checklist; `git status` snapshots; length flag;
  DR-021 timestamp confirmation; smoke-test verification.

**Length anticipation:** 800-1200 lines. Substrate brief with
two new technology stacks coming in (FastAPI structurally, full
React/Vite frontend) — bigger than W6.5's 850 lines. Outside
the band → flag in §9.4 of the report; not a deviation.

**The report does not contain:**

- Recommendations on burst-review queue UX (W8 territory).
- Recommendations on production deployment (post-DR-029
  territory).
- Architectural alternatives to the locked DR-031 stack.
- Performance benchmarks (premature for substrate).

---

## §9 Hard limits — what's NOT in scope

Code is forbidden from doing any of the following. If any of
these surface as "I should probably also..." mid-execution, the
answer is: surface as a finding, don't do it.

- **No burst-review queue UI.** W8 territory.
- **No bet-entry UI.** Future W-stream territory.
- **No authentication / login.** Single-operator local app at
  v1; auth lands later if it lands at all.
- **No state-management library beyond TanStack Query and React
  hooks.** No Redux, Zustand, Jotai, MobX, etc.
- **No styling library beyond CSS modules.** No Tailwind,
  styled-components, Emotion, MUI, etc.
- **No animation library** (Framer Motion etc.).
- **No production deployment configuration.** No Dockerfile, no
  CI config, no nginx config. Dev-mode only.
- **No database integration in the API.** The smoke-test
  endpoint returns canned data. W8+ wires the API to the store
  layer.
- **No background task scheduling.** The settlement-worker /
  reconciliation-worker schedulers stay where they are
  (instantiable but not running). W8+ wires them into the
  FastAPI lifespan.
- **No edits to `workflows/`, `clients/`, `domain/`, `store/`,
  `contracts/`, `ops/`, or any other existing top-level
  directory.** W7 only adds files under `ui/api/`, `ui/web/`,
  and `tests/ui/`.
- **No `.importlinter` changes** unless a new contract is
  genuinely needed (flag as a finding with reasoning).
- **No `pyproject.toml` modifications beyond adding required
  dependencies** (`pydantic-settings` if not present; verify
  pre-flight). Do not bump existing dep versions.
- **No git mutations.** No `add`, `commit`, `stash`, `restore`,
  `checkout`, `reset`. Code reads `git status` as part of the
  empirical-verification baseline; that's the only git command
  it runs.
- **No live API calls.** No Betfair, no VPS, nothing external.
- **No edits to canonical-truth files in the rebuild folder**
  (`decisions.md`, `architecture.md`, `governance.md`,
  `standing_instructions.md`, `vision.md`, `v3_data_requirements.md`,
  `project_context.md`, `current_state.md`).
- **No CI/CD or pre-commit hook setup.** Out of scope.
- **No `ops/` work.** Cron scripts, deployment scripts —
  post-DR-029.

If a hard limit conflicts with what Code thinks is needed to
ship the brief, surface as a finding in §6 of the report and
ship without crossing the limit. Operator-Claude triage routes
the conflict.

---

## §10 What happens after Code's session

The next operator-Claude session reads this report end-to-end via
inventory-first cadence (the established triage pattern from
sweep candidate `(l)` — sixth concrete use likely, on the
running tally). The session walks §6 deviations, §7 open
questions, §8 findings beyond scope; classifies each as no-call
(Code's territory) or operator-call (warrants routing); walks
operator-call items one per round.

If W7 ships clean, the session sequences directly into W8 brief
drafting (the burst-review queue pages on top of the now-working
skeleton). The Session 100 carry items (settings-area cadence
control, per-bet modal override, greyhound operational
constraint) are folded into W8.

If W7 ships with named-debt or follow-up questions, the next
session drafts a follow-up brief picking up the debt before W8.

Code does not produce W8's brief. That's the next session's
work.

---

## §11 Cross-references

**Decision records invoked:**

- DR-021 (timestamp anchoring, Adelaide local time) — applies
  to every timestamp in the report and in the `/api/health`
  endpoint response.
- DR-027 (two-database architecture) — context only; W7 doesn't
  touch databases.
- DR-028 (cross-database boundary discipline) — context only.
- DR-030 (v3 repo layout + import-graph rules) — load-bearing.
  `ui/api/` and `ui/web/` placement under `ui/` follows the
  locked layering.
- DR-031 (v3 tech stack) — load-bearing. FastAPI, React,
  TypeScript, Vite all sourced from this DR.

**Spec docs:**

- `dr029/2_6_settlement_race/2_6_settlement_race.md` §3.5 —
  the burst-review surfacing contract that motivates W7's
  existence (W8's queue pages will consume this).
- `dr029/2_9_write_side/2_9_write_side.md` — the write-side
  picture; future API endpoints land here.

**Prior reports / briefs:**

- `dr029/w4_bet_entry/w6_5_settlement_worker_brief.md` /
  `_report.md` — most recent precedent for brief and report
  shape.
- `dr029/w4_bet_entry/w6_broader_sync_brief.md` — broader-sync
  precedent for substrate-shape briefs.
- `dr029/w4_bet_entry/w4_bet_entry_brief.md` — W4 substrate
  brief precedent.

**Items explicitly out of scope, parked for later:**

- Burst-review queue UI (W8).
- Settings-area cadence control (W8 carry from Session 100).
- Per-bet modal override (W8 carry from Session 100).
- Greyhound operational constraint (W8 carry from Session 100).
- Bet-entry UI (future W-stream).
- AccountCare UI surface (future W-stream).
- Production deployment (post-DR-029).
- Background-task scheduling integration (W8+).

---

**End of brief.**
