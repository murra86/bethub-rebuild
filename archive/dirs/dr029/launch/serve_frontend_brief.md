# Brief — Same-origin frontend serving (v3 serves its own screen)

**Drafted:** 2026-06-17 (Session 157, Adelaide ACST per DR-021)
**Status:** LOCKED on operator approval — single bounded Claude Code session
**Stream:** Launch / packaging (W16 cutover prep — pulls the same-origin
serving slice forward ahead of cutover)
**Governing DRs:** DR-030 (v3 module boundaries), DR-031 (tech stack),
DR-029 §5.6 (composition-root / same-origin deploy story).

---

## 1 — What this brief is and is not

This is a **surgical source change** to the v3 FastAPI app: teach it to
serve the already-built frontend bundle on the **same origin** as the API,
so the whole product runs as a single uvicorn process on a single port.
Today the API (`/api/*`) and the screen are served separately; this change
folds the screen into the API process.

It **is**: one named change to `ui/api/main.py` (plus a small static-serving
helper if Code judges that cleaner), a fresh production build of the
frontend, new automated tests locking the serving behaviour, and empirical
verification that one process serves both the page and the API.

It is **not**: a launcher, a desktop icon, a port-management or
process-shutdown script (that is the next operator-Claude step, built and
tested separately), a CORS rework, a dev-workflow change, a router change, a
schema or DB change, or any edit outside the named anchor. Surprises become
**findings in the report**, not mid-session escalations or scope expansion.

Remediation of anything Code discovers routes to the next operator-Claude
triage session — Code reports, it does not chase.

## 2 — Why this work exists

The operator wants a reliable double-click launch for v3 with clean startup
and clean shutdown, having been bitten repeatedly by v2's two-piece launch
(a separate frontend dev-server that silently fell back to a dead port). The
most reliable fix is to remove the second piece entirely: have FastAPI serve
the built frontend itself, so there is one process, one port, and nothing
left holding a port between launches.

The v3 frontend was already built for this. `ui/web/.env.production` ships
`VITE_API_BASE_URL=` (empty) precisely so the production bundle calls the API
with document-relative URLs and reaches it on the same origin (see
`ui/web/src/api/client.ts`). The DR-029 §5.6 deploy story names same-origin
static serving by FastAPI as the post-DR-029 deploy shape. This brief lands
that shape now, scoped tightly, because it is the reliability foundation the
launcher sits on.


## 3 — Pre-reads

Required, in order:

1. `ui/api/main.py` — the FastAPI app entry point; `create_app()` is the
   anchor. Read it in full before editing.
2. `ui/api/config.py` — `Settings` (note `environment`, `cors_origins`; no
   new config field is required by this brief).
3. `ui/web/src/api/client.ts` — confirms the client uses
   `import.meta.env.VITE_API_BASE_URL` with an empty value in production, so
   a same-origin server satisfies it with no frontend change.
4. `ui/web/.env.production` — confirms the empty API base.
5. `ui/web/src/App.tsx` — confirms `BrowserRouter` (client-side routing),
   which is why the SPA fallback in §5.2 is required.

Reference-only (do not need full reads): `dr029/auto_login/auto_login_report.md`
(precedent for handling untracked files under a dirty tree).

## 4 — System access

- **Mac filesystem, read-write**, limited to the named anchor in §5 plus the
  new test file. Repo root: `/Users/tim/Desktop/Projects/bethub-v3`.
- **Node/npm build**, read-write within `ui/web` (produces `ui/web/dist`).
- **Local process spin-up** for verification: start uvicorn, curl it, stop
  it. No external network calls required; Betfair stays in **mock** mode for
  all verification in this session (this brief does not touch live mode).
- **No database access** required.
- All timestamps in the report in Adelaide local time (ACST/ACDT) per DR-021.

### Dirty-tree discipline (the v3 tree is fully uncommitted)

The v3 working tree is dirty and `ui/api/main.py` is **untracked**. Therefore:

- **No git operations of any kind** — no `add`, `commit`, `stash`, `restore`,
  `checkout`, `reset`. Leave git state exactly as found.
- Because the anchor file is untracked, `git diff` cannot isolate the edit.
  Verify edits by reading the file back and by `grep` for the added symbols,
  the same way the auto-login work verified untracked-file edits.
- Touch only the anchor file and the new test file. No "while we're here"
  edits to adjacent code, imports, or formatting in untouched regions.
- At session end, confirm `git status --short` shows the same tracked-file
  modifications as at start, plus the one new untracked test file — and
  nothing else.


## 5 — Substantive scope

The change lives in `create_app()` in `ui/api/main.py`, added **after** the
routers are included and dependencies configured, so the API surface keeps
precedence and the static serving is the fallthrough. A small private helper
module under `ui/api/` is acceptable if Code judges it cleaner than inlining;
keep it within `ui/api/` to respect DR-030 (UI layer owns its own wiring).

### §5.1 — Mount the built frontend on the same origin

- Resolve the build directory to `ui/web/dist` relative to the repo root
  (derive from `__file__`, do not hard-code an absolute path).
- Serve `dist/assets/*` (hashed JS/CSS) and the other static files in `dist`
  (e.g. `favicon.svg`, `icons.svg`) at their document-relative paths so the
  bundle's own references resolve.
- Serve `dist/index.html` at `GET /`.
- The API keeps full precedence: every existing `/api/*` route, including
  `/api/docs`, `/api/redoc`, `/api/openapi.json`, must behave exactly as it
  does today. The static serving must never shadow or intercept `/api/*`.

### §5.2 — SPA deep-link fallback (required — BrowserRouter)

The frontend uses `BrowserRouter`, so client-side routes like `/racing` or
`/accounts` are not real files on disk. A browser hitting one directly (deep
link, bookmark, or refresh) must receive `index.html` so the React router can
take over.

- Any `GET` request that is **not** under `/api/`, **not** a request for an
  existing static file in `dist`, and accepts HTML → return
  `dist/index.html` with HTTP 200.
- A request under `/api/` that matches no route must still return the normal
  API 404 (JSON), **not** `index.html`. Do not let the fallback swallow API
  misses — this is the most important correctness boundary in the change.
- A request for a genuinely missing static asset (e.g. `/assets/nope.js`)
  returns 404, not `index.html`.

### §5.3 — Guard: only serve when the build exists; never break dev or tests

- Mount the static serving **only when `ui/web/dist/index.html` exists**. If
  the build is absent, the app still starts and the API works normally; log
  one clear WARNING line naming the missing build path. This keeps test runs
  and a fresh checkout from failing.
- The dev workflow (`npm run dev` on Vite + uvicorn cross-origin) must keep
  working unchanged. This change is purely additive — do not remove or narrow
  the CORS middleware or the dev origins.
- The existing pytest suite calls `create_app()`. Adding the mount must not
  break any existing test. If a present `dist` causes any existing test to
  behave differently, that is a finding — surface it; do not paper over it.

### §5.4 — Fresh production build

- Run the frontend production build (`npm run build` in `ui/web`, i.e.
  `tsc -b && vite build`) so the served bundle matches current source rather
  than relying on the existing (older) `dist`. Report the build's exit status
  and confirm `dist/index.html` plus `dist/assets/` are present afterward.
- If the build fails, stop and report it as a blocking finding — do not serve
  a stale bundle to work around a broken build.

### §5.5 — Lock the behaviour with automated tests (reliability requirement)

Add a focused test module (FastAPI `TestClient` against `create_app()`) that
asserts the serving contract, so it cannot silently regress later:

- `GET /` returns 200 and HTML containing the app's root element / bundle
  script reference.
- A client-side route (e.g. `GET /racing`) with an HTML `Accept` header
  returns 200 and the same `index.html` (deep-link fallback works).
- An existing API route (e.g. `GET /api/health`) still returns its JSON,
  unchanged.
- An unknown `/api/*` path returns the API 404 (JSON), **not** `index.html`
  (proves the fallback does not swallow API misses).
- The build-absent path is handled gracefully (the app constructs without
  the mount when `dist/index.html` is absent) — exercise this with a
  temporary/empty build dir or equivalent so the guard in §5.3 is covered.

Tests must be hermetic and require no network and no live Betfair.


## 6 — Sequencing within session

1. Read the §3 pre-reads; confirm the same-origin assumptions (empty
   production API base, BrowserRouter) hold as described. If any does not
   hold, stop and report before editing.
2. Capture baselines (§7) — full suite counts and `git status --short`.
3. Run the fresh production build (§5.4).
4. Make the `ui/api/main.py` change (§5.1–§5.3).
5. Add the tests (§5.5).
6. Run verification (§7) — suites green, curl checks pass.
7. Write the report (§8).

If a cleaner order presents itself, Code may deviate, but the build (step 3)
must precede the curl verification (step 6) since the curl checks serve the
built bundle.

## 7 — Empirical verification (capture before and after)

**Baselines at session start (measure, do not assume):**

- `uv run pytest` — full pass count. Expected ~983 passing at baseline; record
  the actual number.
- `npm run test` (vitest) in `ui/web` — expected ~90 passing; record actual.
- `uv run lint-imports` — expected clean (DR-030 contracts kept).
- `git status --short` — record the dirty file list.

**After the change:**

- `uv run pytest` — equals baseline **plus the new tests**, zero failures.
- `npm run test` (vitest), `tsc -b`, `eslint` — unchanged from baseline
  (this is a Python + build change; note any pre-existing frontend lint
  errors as pre-existing, do not fix them).
- `uv run lint-imports` — still clean.
- **Live single-process curl proof** (Betfair mock mode): start
  `uv run uvicorn ui.api.main:app --port 8000`, then confirm on that one port:
  - `curl -s localhost:8000/` → returns the HTML page.
  - `curl -s localhost:8000/api/health` → returns the health JSON.
  - `curl -s localhost:8000/racing -H "Accept: text/html"` → returns the same
    HTML page (deep-link fallback).
  - `curl -s -o /dev/null -w "%{http_code}" localhost:8000/api/nonexistent`
    → `404`.
  Stop the uvicorn process afterward; confirm the port is free.
- `git status --short` — same as baseline plus only the one new test file.

## 8 — Output spec

Single report file: `dr029/launch/serve_frontend_report.md`.

Sections:

1. **What was built** — the change, the helper (if any), the tests added.
2. **Test results** — baseline vs post table (pytest, vitest, tsc, eslint,
   lint-imports), with the new test count called out.
3. **Anchors touched** — every file + region; grep evidence for the
   untracked-file edits per §4.
4. **Single-process curl proof** — the four curl results verbatim.
5. **Findings** — anything surprising, any deviation from this brief and why,
   any pre-existing debt left untouched.
6. **Self-assessment** — did it fit one session; is the serving contract
   fully covered by the new tests.

Expected length ~120–220 lines. The report contains **no** recommendations
beyond findings, and **no** launcher/icon design (that is the next step).


## 9 — Hard limits (non-negotiable)

Code must **not**:

- Touch any file other than `ui/api/main.py`, an optional new small helper
  module inside `ui/api/`, and the one new test module. No edits elsewhere.
- Perform any git operation (`add`, `commit`, `stash`, `restore`, `checkout`,
  `reset`). Leave the dirty tree exactly as found.
- Change the frontend source, the router, `client.ts`, the env files, or the
  CORS configuration. The frontend is already same-origin-ready; if it were
  not, that would be a finding, not an edit.
- Change any schema, migration, DB, or repository code.
- Touch live Betfair, live mode, credentials, or the network. All
  verification runs in mock mode.
- Build or design the launcher / desktop icon / shutdown logic — explicitly
  out of scope, it is the next operator-Claude step.
- Add a new config field or settings flag (the dist-existence guard in §5.3
  needs none).
- "Fix" pre-existing lint debt (the known frontend eslint errors, any ruff /
  mypy items outside the anchor). Leave them; note them.
- Continue past one bounded session. If the work does not fit, stop and report
  partial-but-coherent progress as a finding.

## 10 — What happens after Code's session

The next operator-Claude (Chat) session reads `serve_frontend_report.md`,
triages it (suites green, curl proof clean, anchors confined, tests lock the
behaviour), and — on a clean report — proceeds to build the **desktop
launcher**: a double-click that builds (if needed), frees any stale port,
starts the single uvicorn process on a pinned port in live mode with the
credentials file, opens the browser when `/api/health` responds, and on close
shuts the process down cleanly and frees the port. The launcher is built and
tested by Chat via Desktop Commander, not by Code, and not in this brief.

If the report surfaces blocking findings (build broken, fallback swallowing
API misses, a test that can't be made hermetic), those become the next
session's triage and a follow-up brief, not a launcher.

## 11 — Cross-references

- **DR-029 §5.6** — composition-root / same-origin deploy story (this brief
  lands that shape ahead of cutover).
- **DR-030** — v3 module boundaries (the static wiring stays inside `ui/`).
- **DR-031** — tech stack (FastAPI / uvicorn / Vite).
- **W16 cutover** — this is the same-origin serving slice of cutover pulled
  forward; the rest of cutover (v2 retirement, data, routing) is unaffected
  and out of scope here.
- **`dr029/auto_login/auto_login_report.md`** — precedent for verifying
  edits to untracked files under a dirty tree.
- **Excluded parking-lot items** — launcher/icon/shutdown (next step),
  vite-8 Fast Refresh dev issue (unrelated; dev-only), on-screen
  "auto-login disabled" banner (separate follow-up).
