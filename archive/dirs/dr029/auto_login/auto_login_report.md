# Auto-login report — v2's self-refreshing Betfair login, ported into v3

**Executed:** 2026-06-17, ~08:30–08:45 ACST (Adelaide, ACST = UTC+9:30, no
DST in June per DR-021)
**Brief:** `dr029/auto_login/auto_login_brief.md` (LOCKED, Session 154)
**Outcome:** Complete in a single bounded session. The self-refreshing
`BetfairAuthProvider` is built, wired, and tested; the static-token
fallback is preserved; all suites green.

---

## 1 — What was built

A drop-in for the W2 `_auth.py` deferred seam: one new concrete
`AuthProvider`, the config fields it needs, and the wiring that selects it
in live mode — with the static-token escape hatch intact.

**§5.1 — Config fields (`ui/api/config.py`, `Settings`).** Added three
fields, all env-overridable under the `BETHUB_` prefix:

- `betfair_username: str | None = None`
- `betfair_password: str | None = None`
- `betfair_identity_url: str = "https://identitysso.betfair.com/api/login"`
  (ported from v2's `LOGIN_URL`; overridable via
  `BETHUB_BETFAIR_IDENTITY_URL` for the same reason the REST URLs are).

**§5.2 — The provider (`clients/betfair_client/v1/_auth_betfair.py`, new).**
`BetfairAuthProvider` satisfies the `AuthProvider` Protocol and ports v2's
`_login()` / `get_token()` / `clear_token()` plus its token-age and locking
fields:

- `app_key()` returns the configured app key.
- `session_token()` mints a token via login on first call and re-mints once
  the cached token ages past `token_max_age` (ported verbatim from v2:
  refresh at 3h, token treated valid ~4h — `DEFAULT_TOKEN_MAX_AGE =
  timedelta(hours=3)`).
- `_login()` posts username + password + app key to the identity URL via an
  **injected transport callable** (the existing `Transport` shape) and
  parses the returned token / error, matching v2's response handling
  (`status == "SUCCESS"` → token; `TEMPORARY_BAN` and all other failures →
  raise).
- Thread-safe: a `threading.Lock` guards the cache so concurrent callers
  don't both log in.
- On any refresh failure it **raises** `BetfairRestError(status_code=401)`,
  which the surfaces already map to `betfair_auth_expired` via
  `_errors.map_rest_error_read` — never a stale or empty token.
- An injectable `clock` makes token aging deterministic in tests.

Homed beside the Protocol it implements per DR-030, and re-exported from the
package surface (`clients/betfair_client/v1/__init__.py`) per the flat
re-export convention.

**§5.3 / §5.4 — Wiring + fallback (`ui/api/dependencies/composition.py`).**

- `_read_credentials_file()` now returns a `_FileCredentials` dataclass that
  may carry `app_key`, `session_token`, `username`, and `password` — any
  subset, all optional (each validated as a string when present). The
  static `app_key` + `session_token` shape keeps working unchanged.
- `build_auth_provider()` resolves credentials from the env fields, then
  merges in the credentials file (env wins on conflict), then chooses in
  precedence order:
  1. **Self-refreshing login** — `username` + `password` present →
     `BetfairAuthProvider` (raises a clear error if `app_key` is missing).
  2. **Static-token fallback** — only `app_key` + `session_token` →
     today's `StaticAuthProvider` (paste-a-token escape hatch, unchanged).
  3. Neither → raises, reworded to name both options (still contains the
     word "credentials" the existing safety test asserts on).
- `_build_login_transport()` added: the live `httpx` form-post transport for
  the identity endpoint (lazy `httpx` import, no network call at
  construction). HTTP-shape failures are converted to `BetfairRestError` so
  login failures map through the same `betfair_auth_expired` /
  `betfair_api_unreachable` path as the REST transport. **Never invoked in
  this session** — tests drive a fake.
- Mock mode is untouched (still `MockAuthProvider`).

---

## 2 — Test results

All counts measured at session start and end (not assumed).

| Suite        | Baseline            | Post                | Delta |
|--------------|---------------------|---------------------|-------|
| pytest       | 960 passed          | 977 passed          | +17   |
| vitest       | 90 passed           | 90 passed           | 0     |
| tsc -b       | clean (exit 0)      | clean (exit 0)      | 0     |
| eslint       | 7 problems (6 err)  | 7 problems (6 err)  | 0     |

vitest / tsc / eslint are unchanged because this is a Python-only change —
the post eslint output is **byte-identical** to baseline (verified via
`diff`). The 6 eslint errors are pre-existing and frontend-only (see
Findings).

**New tests** (17, all against a FAKE login transport — zero network),
`tests/clients/betfair_client/v1/test_auth_betfair.py`:

Provider behaviour (§7):
1. `test_first_call_triggers_exactly_one_login_and_returns_token` — first
   `session_token()` does exactly one login, returns the minted token, posts
   the right URL/body/headers.
2. `test_app_key_returns_configured_value`.
3. `test_second_call_in_window_returns_cache_without_relogin` — cached
   token, no second login.
4. `test_call_after_max_age_triggers_remint` — re-mint past max-age.
5. `test_concurrent_calls_trigger_only_one_login` — 10 threads, one login
   (lock holds).
6. `test_login_failure_raises_and_maps_to_auth_expired` — raises
   `BetfairRestError(401)` → `betfair_auth_expired`.
7. `test_temporary_ban_raises_as_auth_failure` — TEMPORARY_BAN surfaces as a
   401 auth failure (see Findings on backoff).
8. `test_success_without_token_raises`.
9. `test_clear_token_forces_relogin`.

Wiring (§5.3 / §5.4):
10. `test_live_with_username_password_returns_betfair_provider`.
11. `test_live_self_refresh_takes_precedence_over_static_token`.
12. `test_live_with_only_static_token_returns_static_provider`.
13. `test_mock_mode_returns_mock_provider`.
14. `test_live_without_any_credentials_raises`.
15. `test_live_username_password_without_app_key_raises`.
16. `test_credentials_file_username_password_builds_betfair_provider`.
17. `test_credentials_file_static_token_still_builds_static_provider`.

**Other hygiene (beyond the brief's named suites):**
- `ruff` — clean on all four files I authored/edited; one fix auto-applied
  to my own test file (import sort). composition.py retains two pre-existing
  ruff issues left untouched (Findings).
- `mypy` — clean on my three changed `.py` files (one pre-existing error in
  the transitively-imported `balance_derivation.py`, untouched).
- `import-linter` (`lint-imports`) — 5 contracts kept, 0 broken; DR-030
  layered architecture preserved.

---

## 3 — Anchors touched

Five files, each only at the named region. The v3 tree was already dirty at
baseline, so `git diff` (HEAD→worktree) cannot cleanly isolate edits to
**untracked** files; edits were made as surgical string replacements and are
itemised below.

1. **`ui/api/config.py`** *(untracked at baseline)* — three credential
   fields added to `Settings` (§5.1). No other region changed.
2. **`clients/betfair_client/v1/_auth_betfair.py`** — **new file**, the
   `BetfairAuthProvider` (§5.2).
3. **`clients/betfair_client/v1/__init__.py`** *(already `M` at baseline)* —
   exactly two added lines: `from ._auth_betfair import BetfairAuthProvider`
   and `"BetfairAuthProvider",` in `__all__`. `git diff` on this tracked
   file shows my two lines plus a large body of **pre-existing** dirty
   content (account_funds / current_orders / market_catalogue /
   racing_catalogue re-exports) that predates this session — confirmed by
   the baseline `git status` already listing `__init__.py` as modified and
   those sibling modules as untracked. `grep -c` confirms each of my two
   additions appears exactly once.
4. **`ui/api/dependencies/composition.py`** *(untracked at baseline)* —
   import of `BetfairAuthProvider` + `BetfairRestError`; `_FileCredentials`
   dataclass; rewritten `_read_credentials_file()`; new
   `_build_login_transport()`; rewritten `build_auth_provider()` (§5.3/§5.4).
5. **`tests/clients/betfair_client/v1/test_auth_betfair.py`** — **new
   file**, the 17 tests above.

`git status` confirms only these five paths changed. No edits to v2, the
`AuthProvider` Protocol, `MockAuthProvider`, any Betfair call site, the DB,
schema, or git state.

---

## 4 — Findings

- **Deploy-only behaviour (per §7 carve-out).** The real round-trip to
  `identitysso.betfair.com/api/login` is **not** exercised this session by
  design (zero-live-call hard rule). It is first exercised by the operator
  at live deploy for the $5 lay test. Everything up to the network boundary
  is proven by the fake-transport tests; the boundary itself is the one
  behaviour proven only at deploy.

- **Locking tightened vs v2 (deviation, intentional).** v2 logs in
  **outside** its lock (releases the lock, does network I/O, re-acquires to
  store), so two concurrent cache-misses in v2 could both trigger a login.
  The brief §5.2 explicitly requires "two concurrent requests don't both
  trigger a login," so this port holds the lock **across** the login,
  single-flighting it. Holding a lock over a short auth call is acceptable
  and keeps the cache invariant simple. Test #5 asserts the single-flight.

- **TEMPORARY_BAN backoff NOT ported (deviation, in-scope discipline).**
  v2 sets a 30-minute stateful backoff on a `TEMPORARY_BAN` login response.
  That stateful backoff is not in the brief §5.2 named behaviour list, so it
  is deliberately **not** ported. The ban is still surfaced — it raises a
  401 (`betfair_auth_expired`) like any other login failure rather than
  being swallowed — but there is no automatic backoff window. Operator
  consequence: under a TEMPORARY_BAN the next request will re-attempt login
  immediately. If repeated bans become an issue in live operation, porting
  v2's backoff is a small, well-scoped follow-up.

- **max-age unchanged.** v2's values were ported verbatim (refresh at 3h,
  token treated valid ~4h). No reason was found to adjust them.

- **eslint was NOT clean at baseline** — contradicts the brief §7
  assumption of "eslint clean state." Baseline eslint reports 7 problems (6
  errors, 1 warning), all pre-existing and entirely in frontend TSX/TS
  (`HedgeModal.tsx`, `LogBetPanel.tsx`, `RaceListSidebar.tsx`,
  `usePriceMemory.ts`, `Racing.tsx` — `react-hooks` rules). This work is
  Python-only and touches no frontend file; post eslint is byte-identical
  to baseline. Flagged as a pre-existing condition, not addressed (out of
  scope).

- **Pre-existing Python-lint debt left untouched (dirty-tree discipline).**
  `composition.py` (untracked) carries two pre-existing issues unrelated to
  this work: `F401` (`import os` unused) and `I001` (a stray blank line in
  the import block). `ruff --diff` confirms the only fixes would be to
  remove that `import os` and one blank line — both in regions I never
  edited. Removing them would surface as unintended changes, so they are
  left as-is. Likewise the pre-existing `mypy` error in
  `balance_derivation.py` is untouched. None of these are in this brief's
  named anchors or verification list.

- **No Betfair call site needed changing** — confirmed. The seam works as
  designed: `_connection._headers()` already calls `auth.session_token()`,
  and the surfaces already catch `BetfairRestError`, so the provider's raise
  flows straight to `betfair_auth_expired` with no call-site edit.

- **Login transport encoding.** The live login transport posts
  form-encoded data (`httpx ... data=body`), matching v2's
  `application/x-www-form-urlencoded` login, and converts httpx HTTP errors
  to `BetfairRestError` so they map cleanly. This differs from the REST
  transport (which posts JSON) — login is form-encoded by Betfair's
  identity API. The provider itself is transport-agnostic (it just calls the
  injected callable), so this detail lives only in the deploy-only builder.

---

## 5 — What's left for the operator

To perform the first live login, set Betfair to live mode and supply
credentials by **one** of the two shapes below. With username + password
present, v3 builds the self-refreshing `BetfairAuthProvider` automatically;
the static-token path remains as a fallback.

**Always required:**

```
BETHUB_BETFAIR_MODE=live
```

**Option A — env vars (self-refreshing login, recommended):**

```
BETHUB_BETFAIR_APP_KEY=<your Betfair application key>
BETHUB_BETFAIR_USERNAME=<your Betfair username>
BETHUB_BETFAIR_PASSWORD=<your Betfair password>
```

**Option B — credentials file (self-refreshing login):**

```
BETHUB_BETFAIR_CREDENTIALS_PATH=/path/outside/repo/betfair.json
```

with the file containing:

```json
{
  "app_key": "<your Betfair application key>",
  "username": "<your Betfair username>",
  "password": "<your Betfair password>"
}
```

**Fallback — static token (no auto-refresh, the old behaviour):** supply
`BETHUB_BETFAIR_APP_KEY` + `BETHUB_BETFAIR_SESSION_TOKEN` (env), or
`{"app_key": "...", "session_token": "..."}` in the credentials file. v3
returns `StaticAuthProvider` and the operator owns refreshing the token.

**Notes for the operator:**

- Precedence: if both `username`/`password` **and** a static `session_token`
  are configured, the self-refreshing provider wins.
- `BETHUB_BETFAIR_IDENTITY_URL` defaults to v2's login endpoint
  (`https://identitysso.betfair.com/api/login`); override only if Betfair
  changes the URL or for staging.
- Never commit credentials (env or file) to the repo.
- The first live `session_token()` call (on the first real request in live
  mode) is the moment the real Betfair login fires for the first time — this
  is the deploy-only behaviour noted in §4. The $5 lay test is the intended
  first live exercise.
- Under a Betfair `TEMPORARY_BAN`, the provider surfaces an auth error and
  re-attempts on the next request (no automatic backoff — see §4).
