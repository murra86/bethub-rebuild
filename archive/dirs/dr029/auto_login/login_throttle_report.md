# Login throttle report — escalating cool-off + hard kill on v3's Betfair auto-login

**Executed:** 2026-06-17, ~09:05–09:30 ACST (Adelaide, ACST = UTC+9:30, no
DST in June per DR-021)
**Brief:** `dr029/auto_login/login_throttle_brief.md` (LOCKED, Session 155)
**Hardens:** the `BetfairAuthProvider` from the auto-login session
(`auto_login_report.md`)
**Outcome:** Complete in a single bounded session. The escalating cool-off
throttle and hard kill are built into the provider, tested with a fake
transport + fake clock (zero network, zero real waiting), and all suites are
green. Two anchors touched, no scope creep.

---

## 1 — What was built

A login-retry throttle added entirely inside `_auth_betfair.py`, driven by
the provider's **existing** `self._lock` and injected `self._clock` — no new
infrastructure, no config/env.

**§5.1 — Throttle policy constants** (beside `DEFAULT_TOKEN_MAX_AGE`):

- `LOGIN_COOLOFF_SCHEDULE: tuple[timedelta, ...] = (30 min, 1 hr, 2 hr, 4 hr)`
  — the wait imposed after each consecutive failed login. The final 4 hr
  entry doubles as the cap: if the failure count ever exceeds the schedule
  length, the last window is reused rather than growing.
- `MAX_LOGIN_ATTEMPTS = 5` — after the 5th consecutive failure the provider
  kills itself.
- A `_killed_message(max_attempts)` helper builds the killed-state message;
  with the default 5 it reproduces the brief §5.5 wording verbatim
  ("Betfair auto-login disabled after 5 failed attempts — restart required
  after operator review").
- A module logger (`logging.getLogger(__name__)`) was added, matching the
  package convention in `_stream_parser.py`.

**§5.2 — Throttle state** in `__init__`, guarded by `self._lock` alongside
the token cache: `self._consecutive_failures = 0`,
`self._next_attempt_at: datetime | None = None`, `self._killed = False`.
Two keyword-only constructor params — `cooloff_schedule` and `max_attempts`
— default to the constants so tests can inject a different threshold (§5.1).

**§5.3 — The gate in `session_token()`** (ordered, all under the lock):

1. **Valid cached token** → return it unchanged. The throttle is never
   consulted on the happy path (existing behaviour preserved exactly).
2. **Killed** → raise `BetfairRestError(status_code=401)` with the distinct
   disabled message; `_login()` is never called again.
3. **Inside a cool-off window** (`now < next_attempt_at`) → raise
   `BetfairRestError(status_code=401)` **without** calling `_login()`. This
   is the hammer-stopper.
4. **Otherwise** → attempt `_login()` and account for the outcome.

**§5.4 — Outcome accounting** (helpers `_record_login_success` /
`_record_login_failure`, called under the held lock):

- **Success** → reset failure counter to 0, clear the cool-off gate, clear
  the killed flag, then cache + return the token. Any single success fully
  recovers the provider.
- **Failure** (`_login()` raises `BetfairRestError`) → increment the
  counter; at the threshold set `_killed` (and emit one ERROR log on the
  transition); otherwise arm `next_attempt_at = now + schedule[min(failures
  − 1, len − 1)]` (the cap). The original error is then **re-raised** so the
  caller still sees the auth error this round.

**§5.5 — Killed error + log.** The killed raise keeps `status_code=401` so
existing surfaces still map it to `betfair_auth_expired` with no call-site
change, but carries the distinct disabled message. One ERROR-level log line
with the same message is emitted on the transition into the killed state. No
auto-recovery — only constructing a fresh provider (v3 restart) clears the
killed flag; no timer, retry, or re-enable control was added.

---

## 2 — Test results

All counts measured at session start and end (not assumed).

| Suite        | Baseline            | Post                | Delta |
|--------------|---------------------|---------------------|-------|
| pytest       | 977 passed          | 983 passed          | +6    |
| vitest       | 90 passed           | 90 passed           | 0     |
| tsc -b       | clean (exit 0)      | clean (exit 0)      | 0     |
| eslint       | 7 problems (6 err)  | 7 problems (6 err)  | 0     |

This is a Python-only change; the post eslint output is **byte-identical** to
baseline (verified via `diff`). The 6 eslint errors are pre-existing and
frontend-only — not this work's concern, as the auto-login report already
noted. The existing 17 provider tests pass unchanged.

**New tests** (6) appended to
`tests/clients/betfair_client/v1/test_auth_betfair.py`, all against the fake
login transport + injected fake clock:

1. `test_call_inside_cooloff_does_not_reattempt_login` — after one failure, a
   call inside the 30-min window raises with **no** second transport call.
2. `test_call_after_cooloff_reattempts_login` — once the window elapses
   (clock advanced), the next call does attempt login again.
3. `test_cooloff_windows_escalate_in_order` — windows escalate 30 min → 1 hr
   → 2 hr → 4 hr across consecutive failures (asserted against
   `next_attempt_at`).
4. `test_cooloff_caps_at_final_window` — with the threshold raised to 7 (so
   the cap branch is reachable), windows are 30 m, 1 h, 2 h, 4 h, **4 h, 4 h**
   — capped, not growing.
5. `test_fifth_consecutive_failure_kills_provider` — the 5th failure kills:
   exactly 5 transport calls, then the distinct disabled error on every
   later call (status 401, "disabled"/"restart"), no further transport calls
   even after advancing the clock 999 days; still maps to
   `betfair_auth_expired`.
6. `test_successful_login_resets_throttle` — a success mid-sequence resets
   the counter/gate/killed; a later failure restarts the cool-off at 30 min
   (not 1 hr).

Total provider-test count: **23** (17 existing + 6 new).

**Other hygiene (beyond the brief's named suites):** `ruff` clean on both
anchors; `mypy` clean on the provider; `import-linter` (`lint-imports`) 5
contracts kept, 0 broken (DR-030 boundaries preserved — the throttle stays
inside the provider).

---

## 3 — Anchors touched

Two files, exactly the two named anchors. Both are **untracked** (`??`) in
the dirty v3 tree (created in the prior auto-login session), so `git diff`
has no HEAD baseline to diff against; edits were made as targeted
Edit/append operations and confirmed by `grep`.

1. **`clients/betfair_client/v1/_auth_betfair.py`** — added: `import
   logging` + module logger; the §5.1 constants and `_killed_message`
   helper; the §5.2 state fields and two constructor params; the §5.3 gate +
   §5.4 accounting helpers (`_record_login_success` /
   `_record_login_failure`) inside/around `session_token()`. No other method
   changed — `_login()`, `app_key()`, `clear_token()`, and the happy-path
   cache check are untouched in behaviour.
2. **`tests/clients/betfair_client/v1/test_auth_betfair.py`** — extended the
   `_auth_betfair` import to pull in the two new constants; appended the 6
   throttle tests in a new section. The existing 17 tests are unchanged.

`grep -rln` confirms the throttle symbols (`LOGIN_COOLOFF_SCHEDULE`,
`_record_login_failure`, `_killed_message`) appear in **only** these two
files. No edits to v2, the `AuthProvider` Protocol, `MockAuthProvider`,
`StaticAuthProvider`/fallback, any Betfair call site, config/env, frontend,
the DB, or git state.

---

## 4 — Findings

- **No deviation from the brief's values.** The schedule (30 m / 1 h / 2 h /
  4 h), the cap-at-4-hr reuse, the kill-at-5 threshold, and the §6 sequencing
  were all implemented exactly as specified.

- **Killed message is built from the attempt count** rather than hard-coded
  to "5". With the default `max_attempts=5` it reproduces the brief §5.5
  wording verbatim; building it dynamically keeps it accurate if the
  threshold is ever changed via the constructor param. Minor, in the spirit
  of the brief's "e.g." phrasing.

- **The cap branch needed a raised threshold to exercise.** In the default
  config the provider kills at 5 before the cool-off index can exceed the
  4-entry schedule, so the cap (reuse the last 4 hr window) is unreachable
  by default — exactly as §5.1 anticipates. To prove the cap genuinely
  doesn't grow, `test_cooloff_caps_at_final_window` injects `max_attempts=7`
  and observes the 5th and 6th windows stay at 4 hr.

- **Failure catch is scoped to `BetfairRestError`.** That is what `_login()`
  raises (and what the live login transport raises for HTTP-shape failures),
  so it covers every real and tested failure path. A non-`BetfairRestError`
  exception (an unexpected bug) would propagate unthrottled rather than being
  silently counted — a deliberate choice so the throttle accounts only for
  genuine login failures.

- **Three distinct 401 messages, one mapping.** The plain `_login()` failure,
  the cool-off-window raise, and the killed raise all carry
  `status_code=401` and therefore all map to `betfair_auth_expired` with no
  call-site change; their messages differ so logs distinguish "failed this
  attempt" vs "in cool-off" vs "disabled".

- **Supersedes the auto-login report's §4 TEMPORARY_BAN finding.** That
  report noted v2's TEMPORARY_BAN backoff was not ported and a failing login
  re-attempted on every request. This general escalating throttle + hard
  kill now covers the ban case and every other persistent-failure case, as
  the brief §11 intends.

- **Deploy-only carve-out (unchanged from auto-login).** The real round-trip
  to `identitysso.betfair.com/api/login` is **not** exercised this session.
  The throttle is proven entirely by fake-transport + fake-clock tests; the
  real login boundary is first exercised by the operator at the live $5 lay
  test.

---

## 5 — What's left for the operator

- **No new config or env.** Per §9 the schedule and threshold are in-code
  constants this round — no `Settings` field, no `BETHUB_` var, no
  credentials-file key. The credentials configuration from the auto-login
  report (`BETHUB_BETFAIR_MODE=live` plus the username/password/app-key env
  trio or the JSON credentials file) is unchanged and still the only operator
  config needed for the first live login.

- **Killed-state behaviour to be aware of.** If Betfair login fails
  repeatedly (wrong password, suspended account, endpoint change, network
  fault), the provider first goes quiet — waiting 30 min, then 1 hr, then
  2 hr, then 4 hr between attempts — and after the 5th consecutive failure it
  **disables auto-login entirely**: every token request then returns the
  `betfair_auth_expired` failure with the message "Betfair auto-login
  disabled after 5 failed attempts — restart required after operator
  review", and one ERROR line is written to the logs at that moment. This is
  the safe response to the past 48 h lockout — the provider stops hammering
  Betfair.

- **How to reset it.** There is **no auto-recovery** by design. A v3 restart
  (or toggling live mode off then on) constructs a fresh provider and clears
  the killed state. The restart is the deliberate human checkpoint: consult
  Claude on remediation (why login was failing) **before** bringing it back.
  A single successful login at any earlier point fully resets the throttle on
  its own — only the hard kill requires the restart.

- **Out of scope (noted, not built):** the on-screen "auto-login disabled"
  alert banner (§11) — this round's killed-state signal is the distinct
  error + ERROR log only.
