# Login throttle brief — escalating cool-off + hard
# kill on v3's Betfair auto-login

**Drafted:** 2026-06-17 (Session 155, Claude Chat)
**Status:** LOCKED — operator-approved Session 155; contract
for Code execution
**Stream:** accounts-setup tail / hardens the auto-login
provider that completed the W2 `_auth.py` seam
**Brief type:** surgical fix (Sessions 35/36 precedent —
named changes in dependency order, pre/post verification,
explicit hard limits, dirty-tree discipline)
**Governing DRs:** DR-021 (Adelaide timestamps), DR-030 (v3
repo layout / module boundaries), DR-031 (v3 tech stack),
DR-032 (Betfair canonical reference).

---

## §1 — What this brief is and is not

This brief commissions a **single bounded Claude Code
session** to add a login-retry **throttle** to the
self-refreshing `BetfairAuthProvider` that Code built in the
auto-login session (report:
`dr029/auto_login/auto_login_report.md`).

It **is** a surgical addition to one existing provider: when
a login fails, the provider waits an escalating cool-off
window before it will try again, and after five consecutive
failed attempts it stops trying entirely and surfaces a
clear "disabled" error for operator review.

It **is not** a redesign of the provider, a change to the
`AuthProvider` Protocol, a change to any Betfair call site,
an order-placement path, a config/env addition, a frontend
change, or a live Betfair integration test. Surprises become
findings in the report, not mid-session escalations or scope
expansions. Remediation discussion routes to the next
operator-Claude Chat triage, not Code's report.

---

## §2 — Why this work exists

The auto-login provider re-mints the Betfair session token
automatically, which unblocks the live $5 lay test. But as
built, if the login itself starts **failing** (wrong
password, suspended account, Betfair changing the login
endpoint, a network fault), every incoming request that
needs a token calls the login path again — there is no
throttle. Near a jump, in burst-review, that is potentially
many login attempts per second.

The operator has lived the consequence: a past episode of
hammering Betfair with repeated requests triggered a lockout
that lasted almost 48 hours and cost money. The fix is to
make the provider go **quieter** when login is failing, not
louder, and to stop entirely once it is clear something
structural is wrong that only the operator can fix.

This is a separate, additive job from the auto-login brief —
that work is complete and tested; this brief hardens it.

---

## §3 — Pre-reads

**Required (read before starting):**

1. This brief, end to end.
2. `dr029/auto_login/auto_login_brief.md` — the locked brief
   the provider was built against (the contract this one
   extends).
3. `dr029/auto_login/auto_login_report.md` — Code's report
   on what was built (provider shape, the lock, the clock
   injection, the `BetfairRestError(401)` failure raise).
4. `bethub-v3/clients/betfair_client/v1/_auth_betfair.py` —
   the **provider to modify**. The throttle wraps the login
   path inside `session_token()`; the failure raise lives in
   `_login()`. (v3 path:
   `/Users/tim/Desktop/Projects/bethub-v3/clients/betfair_client/v1/_auth_betfair.py`.)
5. `bethub-v3/tests/clients/betfair_client/v1/test_auth_betfair.py`
   — the existing 17-test file; the new throttle tests extend
   it.

**Reference-only (consult if needed, not required):**

- `bethub-v3/clients/betfair_client/v1/_auth.py` — the
  `AuthProvider` Protocol (`session_token()` + `app_key()`),
  unchanged.
- `bethub-v3/clients/betfair_client/v1/_connection.py` —
  where `BetfairRestError` is defined and how
  `session_token()` is consumed in REST headers (confirms no
  call-site change is needed).

---

## §4 — System access

- **Mac filesystem, read-write**, scoped to the v3 tree at
  `/Users/tim/Desktop/Projects/bethub-v3`. Edits limited to
  the two named anchors in §5.
- **No live Betfair access.** No network calls to any Betfair
  endpoint — see §9. The login path is exercised only by a
  fake transport, and time is advanced only by an injected
  fake clock.
- **No database access.** This work touches neither v3's
  operational DB nor capture.db.
- **v2 tree:** not needed (the port already happened). No v2
  reads required; no v2 edits under any circumstance.
- Adelaide local timestamps (ACST/ACDT) per DR-021 for every
  time-of-day reference in the report.
- **Git:** the v3 tree is uncommitted. Standard dirty-tree
  discipline applies — no `git add`, `commit`, `stash`,
  `restore`, `checkout`, or `reset`. Edit only named anchors;
  confirm with `git diff` after edits that only intended
  changes landed.

---

## §5 — Substantive scope (the throttle, in dependency order)

All changes live inside `_auth_betfair.py` and its test
file. The throttle state is guarded by the **existing**
`self._lock` and driven by the **existing** injected
`self._clock`, so it is fully deterministic in tests and
needs no new infrastructure.

### §5.1 — Add the throttle policy constants

Add module-level constants next to the existing
`DEFAULT_TOKEN_MAX_AGE`:

- An **escalating cool-off schedule** — the wait after each
  consecutive failed login, in order: **30 min, 1 hr, 2 hr,
  4 hr**. Express as a tuple of `timedelta`s.
- A **maximum attempt count** — **5**. After the 5th
  consecutive failure the provider is killed (no further
  login attempts).

The 4 hr final entry doubles as the **cap**: if the failure
count ever exceeds the schedule length, the last (4 hr)
window is reused rather than growing further. With the
kill-at-5 threshold and a 4-entry schedule this branch is
not reached in the default config, but the cap makes the
logic safe if the threshold is ever raised. Both values are
constants (operator-set by decision, not env-tuned); a
constructor parameter may default to them so tests can
inject a short schedule + low threshold.

### §5.2 — Add throttle state to the provider

In `__init__`, add state alongside the existing token cache,
all guarded by `self._lock`:

- a **consecutive-failure counter** (starts at 0),
- the **time of the next permitted login attempt** (the
  cool-off gate; `None` when not cooling off),
- a **killed flag** (starts `False`).

### §5.3 — Gate the login path in `session_token()`

Inside `session_token()`, before the existing
mint/refresh branch calls `_login()`:

1. If a **valid cached token** exists (within
   `token_max_age`), return it unchanged — the throttle is
   not consulted on the happy path. (Existing behaviour;
   preserve exactly.)
2. If the provider is **killed**, raise immediately with a
   distinct, clearly-worded error (see §5.5) — never call
   `_login()` again.
3. If the clock is **earlier than the next-permitted-attempt
   time** (inside a cool-off window), raise the standard
   auth-expired error **without** calling `_login()` — this
   is what prevents the hammer. No new login attempt fires
   until the window elapses.
4. Otherwise, attempt the login via the existing `_login()`
   path (still inside the lock).

### §5.4 — Account for the attempt outcome

Wrap the `_login()` call so the throttle records what
happened, still under the lock:

- **On success:** reset the failure counter to 0, clear the
  cool-off gate, clear the killed flag, then cache + return
  the token as today. Any single success fully recovers the
  provider.
- **On failure (`_login()` raises):** increment the failure
  counter; if it has reached the maximum (5), set the killed
  flag; otherwise set the next-permitted-attempt time to
  `now + schedule[failure_index]` (capped at the last
  schedule entry). Re-raise so the caller still sees the
  auth error this round.

### §5.5 — The killed-state error and log

When killed, the provider raises `BetfairRestError` with
`status_code=401` (so existing surfaces still map it to
`betfair_auth_expired` with no call-site change), but with a
**distinct message** naming the cause — e.g. "Betfair
auto-login disabled after 5 failed attempts — restart
required after operator review." On the transition into the
killed state, emit one **ERROR-level log line** with the
same message so it is loud in the logs.

**No auto-recovery.** Nothing clears the killed flag except
constructing a fresh provider — i.e. restarting v3 (or
toggling live mode off/on). This is deliberate: the operator
consults Claude on remediation before bringing it back, so
the restart is the human checkpoint. No timer, no retry, no
re-enable control is added.

---

## §6 — Sequencing within session

1. §5.1 constants first — everything references them.
2. §5.2 state next — the fields the gate and accounting use.
3. §5.3 + §5.4 + §5.5 together — the gate, the
   success/failure accounting, and the killed error/log are
   one coherent change to `session_token()` and are written
   and tested as a unit.

If Code finds a cleaner order, it may deviate and say so in
the report.

---

## §7 — Empirical verification

**Baseline (capture before any edit):** full `pytest` and
`vitest` counts plus `tsc` + `eslint` state. (Last known
green from the auto-login report: pytest 977, vitest 90;
eslint carries 6 pre-existing frontend errors that are not
this work's concern. Confirm at session start, don't
assume.)

**New tests to add (all against a fake login transport and
the injected fake clock — zero network, zero real waiting):**

- After one failed login, a second `session_token()` call
  **inside** the cool-off window raises **without** calling
  the transport again (no second login attempt).
- After the cool-off window elapses (advance the fake
  clock), the next call **does** attempt login again.
- The cool-off windows **escalate** across consecutive
  failures in the right order: 30 min, then 1 hr, then 2 hr,
  then 4 hr.
- The fourth window is 4 hr and the schedule **caps** there
  (does not grow beyond 4 hr).
- The **fifth** consecutive failure kills the provider:
  subsequent calls raise the distinct disabled error and
  **never** call the transport again, even after the clock
  is advanced arbitrarily far (no auto-recovery).
- A **successful** login mid-sequence resets everything: the
  failure counter returns to 0 and a later failure starts
  the cool-off again at 30 min.
- The existing 17 tests still pass unchanged (happy path,
  cache-within-window, re-mint after max-age, concurrent
  single-flight, the existing failure-raises-401 cases).

**Post:** full `pytest` (baseline + new tests) + `vitest`
green; `tsc` + `eslint` unchanged from baseline (Python-only
change). Report both counts so the delta is visible.

**Out-of-session carve-out:** unchanged from the auto-login
brief — the real round-trip to Betfair's login endpoint is
**not** exercised this session. The throttle is proven
entirely by fake-transport + fake-clock tests.

---

## §8 — Output spec

Single report file at:
`dr029/auto_login/login_throttle_report.md`

Sections:

1. **What was built** — the constants, the throttle state,
   the gate, the success/failure accounting, the killed
   error + log.
2. **Test results** — pytest + vitest before/after counts,
   new tests listed, tsc/eslint state.
3. **Anchors touched** — every file + region edited, with
   `git diff` confirmation that only intended changes landed.
4. **Findings** — anything surprising, any deviation from
   this brief's schedule/threshold values or sequencing, and
   the named deploy-only carve-out from §7.
5. **What's left for the operator** — whether any config
   changes from the auto-login report still apply (expected:
   none new — the throttle is automatic), plus a plain
   statement of the killed-state behaviour and that a v3
   restart is what resets it.

Rough length: 120–250 lines. No recommendations beyond §8.5;
no scope creep into other tails (is_self, packaging, the
on-screen alert banner noted in §11).

---

## §9 — Hard limits (non-negotiable)

- **Zero live Betfair API calls.** No network to
  `identitysso.betfair.com`, `api.betfair.com`, or any
  Betfair host. The login path is exercised only by a fake
  transport; time only by the injected fake clock.
- **Zero order placement.** No bet, no order, no money
  movement of any kind. (Carries the W17/W17.1 bet-safety
  rule.)
- **No edits to v2.**
- **No changes to the `AuthProvider` Protocol**, to
  `MockAuthProvider`, or to `StaticAuthProvider` / the
  static-token fallback path.
- **No changes to any Betfair call site**
  (`_connection.py`, `streaming.py`, pricing, placement,
  settlement). If Code believes one is needed, that's a
  finding, not an edit.
- **No config/env additions.** The schedule and threshold
  are in-code constants this round — no `Settings` field, no
  `BETHUB_` env var, no credentials-file key.
- **No frontend / UI changes.** The on-screen alert banner
  is explicitly out of scope (see §11) — the killed-state
  signal this round is the distinct error + ERROR log only.
- **No database changes**, no schema, no migration.
- **No is_self work; no packaging / launch / dev-server
  work** — separate queued deliverables.
- **No git state changes** — dirty-tree discipline per §4.
- **Single bounded session.** If the work doesn't fit,
  that's a finding; partial-but-coherent beats
  complete-but-lost.

---

## §10 — What happens after Code's session

The next Claude Chat session reads
`login_throttle_report.md`, triages it (inventory pass per
the report-triage cadence), confirms the suites are green
and the anchors are clean, and confirms there is no new
operator config beyond what the auto-login report already
named. Code does **not** write the next brief.

With both the auto-login provider and this throttle in
place, v3 is deploy-ready for the first live login: the
operator sets the credentials named in the auto-login
report, deploys v3 live, and runs the $5 lay test. The
is_self coordinated-removal brief is the remaining
accounts-setup tail after that.

---

## §11 — Cross-references

- **Hardens:** the `BetfairAuthProvider` from
  `dr029/auto_login/auto_login_brief.md` /
  `auto_login_report.md` (the auto-login Code session).
- **Addresses:** the auto-login report's §4 finding that
  TEMPORARY_BAN backoff was not ported and a failing login
  re-attempts on every request — superseded here by a
  general escalating throttle plus a hard kill, which covers
  the ban case and every other persistent-failure case.
- **Unblocks (with auto-login):** the $5 live lay test (W17
  racing pages tail); W16 cutover readiness.
- **DRs:** DR-021 (Adelaide timestamps), DR-030 (module
  boundaries — throttle stays inside the provider), DR-031
  (tech stack), DR-032 (Betfair canonical).
- **Bet-safety:** W17 / W17.1 §4 zero-live-call rule carries.
- **Excludes (queued / separate):** the on-screen
  "auto-login disabled" alert banner (a small frontend
  follow-up if the operator wants visible-on-page alerting,
  scoped separately); is_self coordinated removal; cutover
  packaging / vite-8 dev-server fix.
