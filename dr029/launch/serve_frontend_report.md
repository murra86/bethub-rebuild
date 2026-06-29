# Report — Same-origin frontend serving (v3 serves its own screen)

**Executed:** 2026-06-17 (Session 157, Adelaide ACST per DR-021)
**Brief:** `dr029/launch/serve_frontend_brief.md`
**Outcome:** Complete. One bounded session. Suites green, curl proof clean,
anchors confined, serving contract locked by tests. No blocking findings.

---

## 1 — What was built

A surgical, additive change teaching the v3 FastAPI app to serve the built
frontend bundle on the **same origin** as the API, so the whole product runs
as one uvicorn process on one port.

- **New helper** `ui/api/static_serving.py` (`mount_frontend(app, dist_dir=None)`).
  Kept inside `ui/api/` per DR-030. It:
  - Resolves `ui/web/dist` from `__file__` (`parents[2]` repo root → `ui/web/dist`);
    no absolute path hard-coded.
  - Mounts hashed `dist/assets/*` via `StaticFiles` at `/assets`.
  - Serves `dist/index.html` at `GET /` **unconditionally** (so a bare `curl /`
    with no `Accept` header still gets the page).
  - A catch-all `GET /{resource_path:path}` that, in order:
    1. re-raises the normal JSON 404 for any `api`/`api/...` path (the SPA
       fallback must never swallow an API miss — the key correctness boundary);
    2. serves a real top-level static file (`favicon.svg`, `icons.svg`),
       guarded against traversal outside `dist`;
    3. returns `index.html` for HTML navigations (`Accept: text/html`) so the
       `BrowserRouter` deep-links work; otherwise a real 404.
  - **Guard:** mounts nothing and logs one WARNING when `dist/index.html` is
    absent, returning `False` — the app still starts API-only. No new config
    field (per §5.3 / §9).

- **Edit** `ui/api/main.py` — one import and one call to `mount_frontend(app)`
  placed **after** `configure_dependencies(app, settings)` so `/api/*` keeps
  full precedence and static serving is the fallthrough.

- **New test** `tests/ui/api/test_static_serving.py` — 8 tests (below).

- **Fresh production build** of `ui/web` (`tsc -b && vite build`), replacing the
  stale `dist`.

No edits anywhere else. No git operations. Frontend source, router, `client.ts`,
env files, and CORS untouched.

## 2 — Test results (baseline vs post)

| Check | Baseline | Post | Delta |
|---|---|---|---|
| `uv run pytest` | 983 passed | **991 passed** | +8 new (this module), 0 failures |
| `npm run test` (vitest) | 90 passed (13 files) | 90 passed (13 files) | unchanged |
| `tsc -b` (in `npm run build`) | n/a | clean (build exit 0) | clean |
| `npm run lint` (eslint) | 7 problems (6 err, 1 warn) | 7 problems (6 err, 1 warn) | unchanged (pre-existing) |
| `uv run lint-imports` | 5 kept, 0 broken | 5 kept, 0 broken | unchanged |

The 4 pytest `DeprecationWarning`s (`HTTP_422_UNPROCESSABLE_ENTITY`) are
pre-existing and unrelated; left untouched. The 7 eslint problems are
pre-existing `react-hooks/set-state-in-effect` in `Racing.tsx` and a hook
file — pre-existing debt, left untouched per §9.

**New tests (8), mapping to §5.5:**

- `test_root_serves_index_html` — `GET /` → 200 HTML with `id="root"` + `/assets/`.
- `test_client_side_route_falls_back_to_index_html` — `GET /racing` (HTML
  Accept) → 200, byte-identical to `/`.
- `test_top_level_static_file_is_served` — `GET /favicon.svg` → 200 svg (§5.1).
- `test_api_health_unchanged_by_static_mount` — `GET /api/health` → 200 JSON.
- `test_unknown_api_path_returns_json_404_not_index` — `GET /api/nonexistent`
  (even with HTML Accept) → JSON 404, **not** index.html (the boundary).
- `test_missing_static_asset_returns_404_not_index` — `GET /assets/nope.js` → 404.
- `test_build_absent_guard_mounts_nothing` — empty dir → `mount_frontend` returns
  `False`, no `/` or catch-all route added (§5.3 guard).
- `test_build_present_guard_reports_mounted` — complement assertion.

Tests are hermetic (in-process `TestClient`, no network, mock Betfair default).
The serving tests `skipif` the build is absent, with a clear reason.

## 3 — Anchors touched (grep evidence for untracked-file edits)

`ui/api/main.py` is untracked, so edits are verified by read-back + grep per §4
(not `git diff`):

```
$ grep -n "mount_frontend\|static_serving" ui/api/main.py
23:from ui.api.static_serving import mount_frontend
67:    mount_frontend(app)
```

`mount_frontend(app)` sits at line 67, immediately after
`configure_dependencies(app, settings)` (line 61) and before `return app`.

```
$ grep -n "def mount_frontend\|startswith(\"api/\")\|text/html\|StaticFiles" ui/api/static_serving.py
29:from fastapi.staticfiles import StaticFiles
45:def mount_frontend(app: FastAPI, dist_dir: Path | None = None) -> bool:
86:        if resource_path == "api" or resource_path.startswith("api/"):
99:        if "text/html" in request.headers.get("accept", ""):
```

Files:
- `ui/api/main.py` — import (line 23) + call (line 67). Edited region only.
- `ui/api/static_serving.py` — new helper (~110 lines).
- `tests/ui/api/test_static_serving.py` — new test module (8 tests).

**Build artifacts:** `ui/web/dist` rebuilt (JS hash `index-CwPtmkDK.js` →
`index-CKR8ZTYd.js`, confirming the fresh build differs from the stale one;
CSS hash `index-BTYMVci-.css` unchanged). Within `ui/web` per §4 system access.

## 4 — Single-process curl proof (one uvicorn, port 8000, mock mode)

`BETHUB_BETFAIR_MODE=mock uv run uvicorn ui.api.main:app --port 8000`

```
1) GET /
   <!doctype html> ... <title>BetHub v3</title>
   <script type="module" crossorigin src="/assets/index-CKR8ZTYd.js"></script>
   <link rel="stylesheet" crossorigin href="/assets/index-BTYMVci-.css">
   <div id="root"></div> ...            → HTML page ✓

2) GET /api/health
   {"status":"ok","timestamp":"2026-06-17T19:23:58.068769+09:30","version":"0.1.0"}
                                        → health JSON ✓

3) GET /racing  -H "Accept: text/html"
   <!doctype html> ... identical to (1) → deep-link fallback ✓

4) GET /api/nonexistent
   404                                  → API miss not swallowed ✓
```

Both the page and the API answered on the **same single port**. uvicorn stopped
afterward; `lsof tcp:8000` → **PORT 8000 FREE**.

## 5 — Findings

1. **Same-origin baking confirmed empirically.** The brief (§3.3) flagged that
   `client.ts` uses `?? DEFAULT_API_BASE_URL` (`http://localhost:8000`), so
   same-origin only holds if Vite bakes the empty `VITE_API_BASE_URL` as an
   empty string (→ document-relative) rather than dropping it to `undefined`
   (→ localhost fallback). Verified: `grep "localhost:8000" dist/assets/` after
   the fresh build returns **nothing**. The assumption holds. No frontend change
   needed, as the brief expected.

2. **`git status --short` is byte-identical to baseline.** The two new files
   live under `ui/api/` and `tests/ui/` — directories already listed as
   untracked (`?? ui/api/`, `?? tests/ui/`). So no new top-level line appears;
   this is correct, not a missing file. Both files confirmed present on disk.
   No git operation was run; the dirty tree is exactly as found.

3. **A present `dist` did not change any existing test** (§5.3 concern). With
   the build present and the mount active, all 983 prior tests still pass
   identically. The mount is a strict fallthrough behind `/api/*`.

4. **Pre-existing debt left untouched** (per §9): 4 pytest `HTTP_422` deprecation
   warnings; 7 eslint `react-hooks/set-state-in-effect` problems in `Racing.tsx`
   and a hooks file. Noted, not fixed.

5. **No deviations from the brief.** Scope stayed within the named anchor + one
   helper + one test. No CORS/router/schema/env changes. No launcher work.

## 6 — Self-assessment

- **Fit one session:** yes — comfortably, within scope, no partial state.
- **Contract coverage:** the 8 tests cover every §5.5 bullet plus two extras
  (top-level static file; missing-asset 404). The single most important boundary
  — unmatched `/api/*` returns JSON 404, never `index.html`, even under an HTML
  `Accept` header — is asserted directly and re-proven by curl (4). The
  build-absent guard is exercised hermetically with a temp dir.
- **Reliability foundation in place:** one process, one port, page + API
  co-served, port released cleanly on shutdown — the shape the desktop launcher
  (next operator-Claude step) sits on.
- **No recommendations** beyond these findings, and **no launcher/icon design**
  (out of scope per §1 / §9).
