# F-LIVE-1 promo-catalogue cross-thread 500 — fix report (S228)

**Run:** 2026-07-06 (S228), Adelaide-anchored per DR-021.
**Outcome:** FIXED, class-wide, verified. Suite **1346 → 1350 green**. Committed `7d221b7` and pushed to the new GitHub remote (`murra86/bethub-v3`, private) under the S227 git-autonomy guardrails.
**Anchor:** built on bethub-v3 HEAD `ede5ef9` (S227 checkpoint); new HEAD `7d221b7`.
**Bet-safety:** money path untouched (verified by the blast-radius lens — zero changes to settlement, reconciliation, workers, store, orchestrator). Both workers OFF throughout. No DB or secrets in the commit.

---

## 1. What was fixed

**F-LIVE-1** (`b3_liveproof_result.md` §3): during the S227 live-proof, `GET /api/v1/promos/catalogue` threw 500s — `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`. This is **S187/S189 Finding 1** (the per-request `get_db_connection` cross-thread class), which the S189 report §A had assessed as "does not trip live → park post-cutover". It tripped live, so it came off "parked" and was fixed pre-cutover.

## 2. Root cause

FastAPI resolves a sync dependency and the sync endpoint in **separate** anyio threadpool dispatches. A per-request sqlite3 connection created in the dependency's dispatch is then used and closed in the endpoint's dispatch — a different worker thread under concurrent load. sqlite3's default `check_same_thread=True` turns that legitimate sequential cross-thread handoff into a `ProgrammingError` → 500. Under the running app's concurrent polling the dispatch threads diverge often; under sequential test traffic they almost never do — which is exactly why green tests hid it (the S189 sweep had already documented this masking mechanism and left an xfail evidence marker in the suite).

## 3. The fix (one-pass class sweep, per the S223 discipline)

A sweep of every non-test `sqlite3.connect` site found **exactly three providers in the fault class** — connection created in one dispatch, used in another:

| Site | Role |
|---|---|
| `ui/api/routers/promos.py` `get_db_connection` | The live-tripped site (serves the promo endpoints directly — composition does **not** override it) |
| `ui/api/routers/racing.py` `get_db_connection` | Same class via `DbConnDep` (log-context, log-bet endpoints) |
| `ui/api/dependencies/composition.py` `build_db_connection_factory` | The live app's override of the racing dependency |

All three now pass `check_same_thread=False`. Why this is safe: each connection remains **per-request and sequentially used** — created, handed once across the dispatch boundary, used, closed; never touched by two threads at once. Python's sqlite3 runs in serialized threading mode (`threadsafety == 3`, verified on this machine) as a C-level backstop. WAL/locking semantics unchanged.

Why NOT the S187/S188 storage-layer per-method-connection rewrite the S189 report had pencilled in: the W13 promo repositories are shared-connection **by design** (the adapter fans one connection across four repositories), and `credit_in` runs a multi-step write as **one transaction on one connection** — per-method connections would have broken that atomicity. The fault lives at the router/dependency layer, so the fix lands there: minimal collateral, design intent preserved.

Out-of-class `sqlite3.connect` sites (verified same-thread open-use-close, untouched): `ui/api/routers/bets.py` audit fallback factory, `store/repositories/accounts.py` + `bets.py` (the S187 per-method pattern), `scripts/seed_promos.py`, `migrations/`.

## 4. Tests

- **3 new per-provider cross-thread guards** (`tests/ui/api/test_connection_concurrency.py`) — create the connection on one thread, execute+close on another. **Red-before PROVEN**: all three failed pre-fix with the exact live error (run in-session before the fix was applied; independently re-proven by the test-integrity lens via a kwarg-stripping pytest plugin without touching the repo).
- **The S189 xfail evidence marker retired per its own retirement condition** ("if a future fix lands, this xpasses and the finding can be retired") into a hard green guard: 24-way real-dispatch concurrency on `/api/v1/promos/catalogue`, zero 500s, all 200s. Assertion body byte-identical to the xfail version — coverage strictly strengthened. Pre-fix this shows `22×500 / 2×200`.
- Suite **1350 passed** (1346 baseline + 3 new + the retired xfail joining the pass column). Order-dependence and env/cache pollution probed clean.

## 5. Adversarial verification — 3 independent read-only lenses, ALL UPHELD

1. **Correctness** — hunted for any concurrent-use path (workers, background tasks, dependency caching, connection stashing): none. All five consuming endpoints close on their happy paths; workers never touch these providers.
2. **Blast-radius / sweep completeness** — confirmed the three sites are the complete class; diff surgical (4 files); money path untouched; test fixture overrides unaffected.
3. **Test-integrity** — guards exercise the real providers; red-before independently reproduced; xfail flip legitimate; 1350 reconciles exactly; no vacuous-pass path.

## 6. Residuals surfaced by the verify (non-blocking, parked)

- **R-1 (LOW, pre-existing):** `racing.py` `log_bet` — exceptions raised before its `try/finally` block leave the connection to be closed by GC rather than explicitly (money-harmless; close still happens; predates this fix). Candidate hygiene widen of the `try`.
- **R-2 (test-only, pre-existing):** four test-suite fixture factories are themselves in the dispatch-crossing shape with default `check_same_thread=True`; they pass only because sequential TestClient traffic reuses one worker thread. Would flake if those suites ever fired concurrent requests. Not a production gap.
- **R-3 (LOW, pre-existing, out of class):** `SQLiteBetRecordStorage` per-method connections are committed/rolled back by the `with` block but closed only by GC. Never crosses threads live; noting for completeness.
- **R-4 (doc/coverage note):** racing's `DbConnDep` and the composition factory are guarded at unit level; only the promos path has an endpoint-level real-dispatch concurrency guard. The mechanism is identical and proven at dispatch level on the promos path.

## 7. Classification (S189 taxonomy)

**Implemented-not-live.** The fix is proven at real-FastAPI-dispatch level under 24-way concurrency, but the live app has not been relaunched since. First confirmation ride-along: the next live launch (natural candidate: the B4 promo-seed / Safety-Net proof session) — load the promo screen and confirm no 500s. No dedicated launch needed.

<!-- F-LIVE-1 FIXED class-wide (S228) — 3 sites check_same_thread=False; suite 1350; 3-lens UPHELD; commit 7d221b7 pushed; residuals R-1..R-4 parked -->
