# Auto-login brief — port v2's self-refreshing Betfair login into v3

**Drafted:** 2026-06-17 (Session 154, Claude Chat)
**Status:** LOCKED — operator-approved Session 154; contract
for Code execution
**Stream:** accounts-setup tail / completes the W2
`_auth.py` deferred seam
**Brief type:** surgical port (Sessions 35/36 surgical-fix
precedent — named additions in dependency order, pre/post
verification, explicit hard limits)
**Governing DRs:** DR-021 (Adelaide timestamps), DR-030 (v3
repo layout / module boundaries), DR-031 (v3 tech stack),
DR-032 (Betfair canonical reference).

---

## §1 — What this brief is and is not

This brief commissions a **single bounded Claude Code session**
to build v3's real, self-refreshing Betfair authentication
provider by porting the login + token-refresh logic that runs
in v2 today.

It **is** a port-and-wire job: add one new concrete
`AuthProvider` implementation, add the credential fields it
needs to config, and wire it into the one composition-root
function that already chooses the live auth provider.

It **is not** a redesign of the auth interface (the Protocol in
`_auth.py` is locked and correct), a change to any Betfair
REST/streaming call site, an order-placement path, or a live
Betfair integration test. Surprises become findings in the
report, not mid-session escalations or scope expansions.

---

## §2 — Why this work exists

When v3 runs in live mode today, it reads a single Betfair
session token from config (an env-var pair or a JSON
credentials file) **once, at app startup**, and never refreshes
it. The composition root says so in its own words: refreshing
the token is "the operator's responsibility for the first cut."
Betfair session tokens are short-lived (~12 hours), so a live
v3 deployment silently loses its Betfair connection mid-day and
every live pricing call and bet placement starts failing.

This is the real blocker on the $5 live lay test: v3 can reach
real Betfair markets (proven Session 149), but it cannot hold a
working session long enough to operate reliably.

v2 solved this from day one. Its `betfair_client.py` logs in
with username + password, caches the token thread-safely, and
re-mints it before it ages out. v3 was deliberately built with
a pluggable auth seam (the `AuthProvider` Protocol, W2) so this
exact implementation could be dropped in later without touching
any call site. This brief is that drop-in.

---

## §3 — Pre-reads

**Required (read before starting):**

1. This brief, end to end.
2. `bethub-v2/src/services/betfair_client.py` — the **port
   source**. The `_login()`, `get_token()`, and `clear_token()`
   methods plus the token-age/locking fields are the logic to
   port. (v2 path:
   `/Users/tim/Desktop/Projects/bethub-v2/src/services/betfair_client.py`.)
3. `bethub-v3/clients/betfair_client/v1/_auth.py` — the
   **contract**. The `AuthProvider` Protocol the new provider
   must satisfy; the `MockAuthProvider` stays untouched for
   tests.
4. `bethub-v3/ui/api/dependencies/composition.py` — the **wire
   point**. `StaticAuthProvider` and `build_auth_provider()`.
5. `bethub-v3/ui/api/config.py` — the **config add point**. The
   `Settings` class (env prefix `BETHUB_`).

**Reference-only (consult if needed, not required):**

- `bethub-v3/clients/betfair_client/v1/_connection.py` — shows
  how `session_token()` / `app_key()` are consumed in REST
  headers. Confirms no call-site change is needed.
- `dr029/w2_betfair_client/w2_brief.md` — the original W2 brief
  that defined the auth seam and deferred this implementation.

---

## §4 — System access

- **Mac filesystem, read-write**, scoped to the v3 tree at
  `/Users/tim/Desktop/Projects/bethub-v3`. Edits limited to the
  named anchors in §5.
- **v2 tree, read-only** — for reading the port source only. No
  edits to v2 under any circumstance (v2 is the live daily
  driver; per project rule it receives no modifications).
- **No live Betfair access.** No network calls to any Betfair
  endpoint during this session — see §9 hard limits. The login
  endpoint URL is wired as a config value and exercised only by
  a fake transport in tests.
- **No database access.** This work does not touch v3's
  operational DB or capture.db.
- Adelaide local timestamps (ACST/ACDT) per DR-021 for every
  time-of-day reference in the report.
- **Git:** the v3 tree is currently uncommitted. Standard
  dirty-tree discipline applies — no `git add`, `commit`,
  `stash`, `restore`, `checkout`, or `reset`. Edit only named
  anchors; confirm with `git diff` after edits that only
  intended changes landed.

---

## §5 — Substantive scope (the port, in dependency order)

### §5.1 — Add credential fields to `Settings`

In `ui/api/config.py`, `Settings` class, add the fields the
self-refreshing login needs (none exist today because the
static provider never logs in):

- `betfair_username: str | None = None`
- `betfair_password: str | None = None`
- `betfair_identity_url: str` defaulting to v2's login endpoint
  (`https://identitysso.betfair.com/api/login`), overridable
  via `BETHUB_BETFAIR_IDENTITY_URL` for the same reason the
  REST URLs are overridable.

Extend `_read_credentials_file()` in `composition.py` so the
JSON credentials file may **optionally** carry `username` and
`password` alongside (or instead of) the existing
`session_token`. Keep the existing app_key/session_token
fields working — they are not removed (see §5.4 fallback).

### §5.2 — Build `BetfairAuthProvider`

Add a new concrete provider that satisfies the `AuthProvider`
Protocol. Home it per DR-030 module boundaries — alongside the
Protocol it implements, in
`clients/betfair_client/v1/` (Code picks the exact filename;
`_auth_betfair.py` or extending `_auth.py` are both fine —
Claude-Code's call on module shape).

Ported behaviour from v2's `betfair_client.py`:

- `app_key()` returns the configured app key.
- `session_token()` returns a valid token, minting one via
  login on first call and re-minting when the cached token is
  older than a conservative max-age. Port v2's values (token
  treated as valid ~4h, refreshed at ~3h) unless Code finds a
  reason to adjust — if so, name it in the report.
- Login posts username + password + app key to the identity
  URL and parses the returned token / error, matching v2's
  `_login()`.
- Thread-safe: a lock guards the cached token so two concurrent
  requests don't both trigger a login (v2's documented v1 bug
  fix — preserve it).
- On refresh failure, **raise** so it surfaces upstream as
  `betfair_auth_expired` per the Protocol docstring — do not
  return a stale or empty token.

The HTTP call goes through an injected transport/callable (same
pattern the rest of the client uses) so tests drive a fake and
no real network call is made. Code chooses the seam shape to
match existing `Transport` conventions.

### §5.3 — Wire it into `build_auth_provider()`

In `composition.py`, `build_auth_provider()`: in **live** mode,
return the new `BetfairAuthProvider` when username + password
are configured (via env pair or credentials file). Mock mode is
unchanged (returns `MockAuthProvider`).

### §5.4 — Preserve the static-token fallback

If live mode is configured with only a static `session_token`
(and no username/password), keep returning today's
`StaticAuthProvider`. This preserves the existing escape hatch
(paste a token manually) and keeps every current test green.
The error raised when **neither** a token nor username/password
is configured stays, reworded to mention both options.

---

## §6 — Sequencing within session

1. §5.1 config fields first — everything downstream references
   them.
2. §5.2 the provider next — the substantive build.
3. §5.3 + §5.4 wiring last — once the provider exists and is
   tested, connect it and preserve the fallback in the same
   pass.

If Code finds a cleaner order, it may deviate and say so in the
report.

---

## §7 — Empirical verification

**Baseline (capture before any edit):** full `pytest` and
`vitest` counts, plus `tsc` + `eslint` clean state. (Last known
green: pytest 960, vitest 90 — confirm at session start, don't
assume.)

**New tests to add for the provider (all against a fake login
transport — no network):**

- First `session_token()` call triggers exactly one login and
  returns the minted token.
- A second call inside the max-age window returns the cached
  token with **no** second login.
- A call after the token has aged past max-age triggers a
  re-mint.
- Concurrent calls trigger only one login (lock holds).
- A login failure raises (surfaces as `betfair_auth_expired`),
  rather than returning a bad token.
- `build_auth_provider()` returns the new provider in live mode
  with username/password configured; returns
  `StaticAuthProvider` with only a static token; returns
  `MockAuthProvider` in mock mode; raises when nothing is
  configured.

**Post:** full `pytest` + `vitest` green (baseline + the new
tests), `tsc` + `eslint` clean. Report both counts so the delta
is visible.

**Out-of-session carve-out:** the real round-trip to Betfair's
login endpoint is **not** verified in this session by design
(bet-safety hard rule). It is first exercised by the operator
at live deploy for the $5 lay test. The report notes this
explicitly as the one behaviour proven only at deploy.

---

## §8 — Output spec

Single report file at:
`dr029/auto_login/auto_login_report.md`

Sections:

1. **What was built** — the config fields, the provider, the
   wiring, the fallback.
2. **Test results** — pytest + vitest before/after counts, new
   tests listed, tsc/eslint state.
3. **Anchors touched** — every file + region edited, with
   `git diff` confirmation that only intended changes landed.
4. **Findings** — anything surprising, any deviation from this
   brief's sequencing or values (e.g. a changed max-age), and
   the named deploy-only behaviour from §7.
5. **What's left for the operator** — exactly what to put in
   config (username, password, app key) and which env-var or
   credentials-file shape to use, so the operator can do the
   first live login cleanly.

Rough length: 150–300 lines. No recommendations beyond §5's
"what's left for the operator"; no scope creep into other
tails (is_self, packaging).

---

## §9 — Hard limits (non-negotiable)

- **Zero live Betfair API calls.** No network to
  `identitysso.betfair.com`, `api.betfair.com`, or any Betfair
  host. The login path is exercised only by a fake transport.
- **Zero order placement.** No bet, no order, no money movement
  of any kind. (Carries the W17/W17.1 bet-safety rule.)
- **No edits to v2.** v2 is read-only port source.
- **No changes to the `AuthProvider` Protocol** or to
  `MockAuthProvider`.
- **No changes to any Betfair call site** (`_connection.py`,
  `streaming.py`, pricing, placement, settlement) — the seam
  means none are needed. If Code believes one is needed, that's
  a finding, not an edit.
- **No database changes**, no schema changes, no migration.
- **No is_self work** — that's a separate queued brief.
- **No packaging / launch / dev-server work** — separate
  cutover deliverable.
- **No git state changes** — dirty-tree discipline per §4.
- **Single bounded session.** If the work doesn't fit, that's a
  finding; partial-but-coherent beats complete-but-lost.

---

## §10 — What happens after Code's session

The next Claude Chat session reads `auto_login_report.md`,
triages it (inventory pass per the report-triage cadence),
confirms the suites are green and the anchors are clean, and
surfaces to the operator exactly what config to set for the
first live login. Code does **not** write the next brief.

Once auto-login is confirmed and v3 is deployed live with real
credentials, the $5 lay test can run. The is_self
coordinated-removal brief is the remaining accounts-setup tail
after that.

---

## §11 — Cross-references

- **Completes:** the W2 `_auth.py` deferred seam (real
  `BetfairAuthProvider`, explicitly deferred in
  `dr029/w2_betfair_client/w2_brief.md`).
- **Unblocks:** the $5 live lay test (W17 racing pages tail);
  W16 cutover readiness.
- **DRs:** DR-021 (Adelaide timestamps), DR-030 (module
  boundaries — provider homing), DR-031 (tech stack), DR-032
  (Betfair canonical).
- **Bet-safety:** W17 / W17.1 §4 zero-live-call rule carries.
- **Excludes (queued separately):** is_self coordinated
  removal; cutover packaging / vite-8 dev-server fix.
