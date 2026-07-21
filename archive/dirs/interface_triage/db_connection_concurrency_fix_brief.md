# BRIEF — Close the cross-thread DB-connection fault class
#         (SWEEP + SURGICAL FIX, READ-WRITE)

**File:** `interface_triage/db_connection_concurrency_fix_brief.md`
**Drafted:** S187 · 2026-06-25 ACST · LOCKED on operator approval.
**Repo under fix:** `/Users/tim/Desktop/Projects/bethub-v3`
@ `main` (HEAD `2329604`, 69 dirty entries — baseline confirmed
S187 10:08 ACST).
**Builds on:** the S187 live-validation finding — the Accounts
screen threw repeated 500s; Chat traced it to a shared,
thread-bound SQLite connection and proved it with a concurrency
probe (30 concurrent reads → 26 × 500, 4 × 200).

---

## §1 — What this brief is and is not

A SWEEP plus a SURGICAL FIX, in a single bounded Claude Code
session, READ-WRITE but limited to the anchors named in §5. Two
jobs:

1. **Sweep** — inventory EVERY database-connection path the API
   exposes and classify each as cross-thread-safe or not, by the
   one criterion in §5.1. Prove each verdict; do not assert it.
2. **Fix** — eliminate the one confirmed fault (the accounts
   storage), then add concurrency regression guards so the whole
   class cannot silently return.

Code applies ONLY the named changes. No drift into adjacent
code "while we're here". Surprises become findings in the
report, not edits and not mid-session pings — with ONE
exception: the §5.0 baseline-drift stop gate. Code does NOT
re-platform the storage layer, does NOT touch settlement, and
does NOT draft any follow-up brief.

## §2 — Why this work exists

The Accounts-setup screen returned 500s on load and on every
add (accounts and books) during the S187 live-validation sweep.
The data and the on-disk request code were proven correct in
isolation, so the fault was concurrency-only. Root cause:

- The accounts storage object is built once and cached
  process-wide (`@lru_cache`), and it holds a single SQLite
  connection for its whole lifetime.
- SQLite forbids using one connection from a thread other than
  the one that created it. The API serves each request on a
  pool of worker threads.
- So any request that lands on a thread other than the
  connection's creating thread raises and returns 500. The page
  fires several requests at once on load, so the failures are
  immediate and racy — which is also why it passed the test
  suite (those run single-threaded) and seemed to work under
  light, one-at-a-time use earlier in the build.

This is NOT caused by the S186 account-reference fix — that
change never touched the connection wiring. It is a pre-existing
latent fault, exposed now under real browser concurrency. The
operator has asked for the whole class addressed, not just the
one screen, so recurrence is designed out.

## §3 — Pre-reads (in order)

Required (read and confirm understanding before any edit):

- `ui/api/routers/racing.py` — the dependency providers block
  (~§140–200): `_build_default_accounts_storage` (the
  `@lru_cache` singleton, the fault) and `get_db_connection`
  (the per-request pattern, the proven-safe template to follow).
  Also the `list_accounts` endpoint (~759) — the racing log
  panel's account/book picker, a second consumer of the faulty
  storage.
- `ui/api/routers/accounts.py` — the Accounts-setup router; all
  its endpoints consume the faulty storage via `AccountsStorageDep`.
- `store/repositories/accounts.py` — `SQLiteAccountsStorage`
  (~line 125: `self._conn = sqlite3.connect(...)`, the
  long-lived connection; no `check_same_thread`).

Reference-only (consult to confirm the safe paths, not to edit):

- `ui/api/routers/promos.py` (~71) + `ui/api/dependencies/
  composition.py` (~437) — per-request `get_db_connection`.
- `store/repositories/bets.py` (~538) — per-method connection
  (opened and closed inside each call).
- `ui/api/routers/bets.py` (~259) — per-emit audit connection.
- Governing DRs: DR-031 (tech stack — SQLite WAL), DR-030
  (module boundary), DR-021 (Adelaide time), settlement
  byte-identity.

## §4 — System access

- Mac filesystem, direct. Repo
  `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
  (HEAD `2329604`).
- READ-WRITE, limited to the named anchors in §5. Every other
  file is read-only.
- Dirty working tree is expected (~69 git entries). Code runs NO
  git state-changing command (no add/commit/stash/restore/
  checkout/reset). At close, the dirty list is unchanged EXCEPT
  the named-anchor files. Confirm via `git status` start + close.
- Tests run under **`uv run pytest`** (Cat 3 — bare `python3`
  fails at collection).
- `settlement.py` (SHA `9e07a75d…40d4a3`) is NOT touched —
  byte identity confirmed pre and post.
- Adelaide local timestamps (ACST/ACDT) per DR-021 in the report.

## §5 — Substantive scope

### §5.0 — Baseline confirmation gate (STOP condition)

Before any edit, confirm the repo is where the brief left it:

- `git rev-parse --short HEAD` == `2329604`
- `git status --porcelain | wc -l` == `69`
- `settlement.py` SHA-256 begins `9e07a75d`
- the fault anchor still reads as stated:
  `store/repositories/accounts.py` ~125
  (`self._conn = sqlite3.connect(` with no `check_same_thread`),
  and `racing.py` `_build_default_accounts_storage` is still
  `@lru_cache(maxsize=1)`.

If ANY has drifted, **STOP** — report it (anchors stale) and do
not fix against a moved tree. This is the one sanctioned stop.

### §5.1 — The sweep: inventory and classify every connection path

Enumerate every place the running API obtains a SQLite
connection — dependency providers, cached storage factories, and
storage-class constructors. For EACH, classify against the one
criterion that defines this fault class:

> **Faulty** = a connection object that (a) is created once and
> reused across more than one request, AND (b) can be touched by
> a thread other than the one that created it. In practice: a
> process-wide/singleton object that holds a connection for its
> lifetime and is consumed by the threadpool-served endpoints.
>
> **Safe** = a connection created and closed within a single
> request (or a single method call) on the thread that serves
> it — even if the *storage object* around it is cached.

Known starting inventory (Code confirms, extends, and PROVES
each — do not take this list as complete or as gospel):

- `SQLiteAccountsStorage` (`store/repositories/accounts.py`) —
  holds `self._conn`, wired `@lru_cache` singleton in racing.py
  → **FAULTY** (the confirmed fault). Consumed by accounts.py
  (all endpoints) and racing.py `list_accounts`.
- `SQLiteBetRecordStorage` (`store/repositories/bets.py`) —
  cached singleton, BUT opens a fresh connection per method →
  expected **SAFE**. Prove it (no `self._conn`; every method
  opens+closes its own).
- `get_db_connection` in racing.py / promos.py /
  composition.py — per-request, closed in the endpoint →
  expected **SAFE**. Prove it (created per request, closed).
- bets.py per-emit audit connection (~259) → expected **SAFE**.

Output of this step is the §A inventory table in the report:
every path, its verdict, and the one-line proof.

### §5.2 — Fix the accounts storage (the confirmed fault)

Eliminate the cross-thread sharing. The required OUTCOME: the
accounts endpoints must serve unlimited concurrent requests with
zero connection-layer 500s, with each request using a connection
created, used, and released on its own serving thread.

Preferred mechanism (matches the proven `get_db_connection`
pattern already in this codebase): give each request its own
accounts-storage connection rather than sharing one process-wide
— i.e. drop the `@lru_cache` singleton on the accounts-storage
provider and supply a per-request storage whose connection is
closed when the request ends (a FastAPI dependency that yields
then closes in a `finally`). Keep `apply_migrations` idempotent
behaviour intact.

Code's latitude on mechanism: if Code has a strong, stated
reason to prefer another approach (e.g. `check_same_thread`
handling, a per-request connection injected into the storage, or
a per-method-connection refactor mirroring bets.py), it may take
it — PROVIDED the §7 concurrency guard passes and no shared
mutable connection survives. Per-request is the default; deviate
only with the reason recorded in the report.

Do NOT change the bet-storage cache or the per-request
`get_db_connection` providers — they are safe (§5.1). The fix is
the accounts path only.

### §5.3 — Concurrency regression guards (MANDATORY)

The anti-recurrence lever — this is what "avoid future
instances" means in practice. Add an automated guard that
exercises real threadpool concurrency (a plain sequential
TestClient loop will NOT catch this class — that is exactly why
1184 tests missed it). The harness is Code's call (e.g. run the
app under a live server and fire concurrent requests, or drive
the threadpool directly), but it MUST:

- Fire many simultaneous requests (≥20) at each endpoint that
  reads the accounts storage — `/api/v1/accounts`,
  `/api/v1/books`, `/api/v1/racing/accounts` — and assert EVERY
  response is 200 (zero connection-layer 500s).
- Be wired so it would FAIL against the pre-fix code (Code
  confirms it reproduces the fault before the fix, passes after).

### §5.4 — Confirm the safe paths stay safe

For the bet-write path and the per-request connection deps
(§5.1 "safe"), add or extend at least one concurrency assertion
that a representative read endpoint on each safe path also holds
zero 500s under concurrent load. This locks the safe verdict in
as a test, not just a claim. No production change to those paths.

## §6 — Sequencing within session

1. **§5.0 baseline gate** — confirm HEAD / dirty / settlement
   SHA / fault anchor. STOP if drifted.
2. **§5.1 sweep** — inventory + classify + prove every path
   before touching anything. This bounds the fix.
3. **§5.3 guard first (red)** — write the concurrency guard and
   confirm it FAILS against the current accounts code (proves it
   catches the fault).
4. **§5.2 fix** — apply the accounts-storage fix; the guard goes
   green.
5. **§5.4 safe-path guards** — lock the safe verdicts in.
6. **Full suite** — `uv run pytest`; the new guards pass and
   nothing else regresses.

Guard-before-fix (step 3 before 4) is load-bearing: it proves
the guard actually reproduces the fault rather than passing
vacuously.

## §7 — Empirical verification (pre and post)

Capture BOTH states so the report shows what moved:

- **Pre:** the §5.3 concurrency guard run against current code —
  show the 500s (the fault reproduced). Cite counts.
- **Post:** the same guard green (zero 500s across all three
  accounts endpoints); the §5.4 safe-path guards green; full
  `uv run pytest` with no new failures (cite the count delta).
- **settlement.py** SHA-256 byte-identical pre and post
  (`9e07a75d…40d4a3`).
- **`git status`** dirty list unchanged except the named-anchor
  files (the accounts storage, its provider in racing.py, and
  the new/extended test modules).

## §8 — Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/interface_triage/db_connection_concurrency_fix_report.md`

Sections:
- **Baseline** — HEAD, dirty count, settlement SHA (pre/post),
  §5.0 gate result.
- **§A — Connection-surface inventory** — every path, verdict
  (faulty/safe), one-line proof. The sweep deliverable.
- **§B — The fix** — what changed in the accounts path,
  file:line, mechanism used, and why (if not the default).
- **§C — Regression guards** — the concurrency guard(s) added,
  the red-before / green-after evidence, file:line.
- **§D — Pre/post verification** — the fault reproduced then
  cleared; safe-path guards; full-suite delta; settlement SHA.
- **§E — What was NOT touched** — settlement, schema, the safe
  connection paths, the bet-storage cache.
- **Self-assessment** — coverage, any path whose verdict was
  uncertain, confidence, anything not provable in one session.

Anticipated ~200–350 lines. No scope creep into other fixes, no
next-brief draft, no schema change.

## §9 — Hard limits (non-negotiable)

- READ-WRITE only at the §5 anchors (the accounts storage, its
  provider in racing.py, and the test modules). No drift into
  adjacent code, no opportunistic refactor.
- `settlement.py` byte-identical (SHA `9e07a75d…40d4a3`). No
  contact with `settlement.py`,
  `apply_manual_operator_resolution`, or the `provisional.py`
  settlement path.
- **Do NOT change the safe paths** — the per-request
  `get_db_connection` providers and the bet-storage cache stay
  as they are. Confirm them (§5.1, §5.4); do not rewrite them.
- **NO schema change** — this is a connection-lifetime fix only;
  zero DDL.
- **NO git state-changing ops** (add/commit/stash/restore/
  checkout/reset). Dirty list unchanged except the named anchors.
- The concurrency guard MUST exercise real threadpool
  concurrency — a sequential TestClient loop does not satisfy
  §5.3.
- Single bounded session. Over-budget = a finding, not a
  continuation.
- No mid-session escalation EXCEPT the §5.0 baseline STOP.
- `uv run pytest`, never bare `python3` (Cat 3).

## §10 — What happens after Code's session

The next operator-Claude session reads
`db_connection_concurrency_fix_report.md`, confirms the class is
closed — the §A inventory complete, the accounts fault fixed,
the concurrency guards red-before/green-after, settlement
byte-identical, dirty list clean except named anchors — and the
operator re-launches and resumes the live-validation sweep
(Accounts → Log Bet panel → Log Past Bet → conversion hinge →
BetLog → live Betfair lay). Code does NOT draft the next brief.

## §11 — Cross-references

- Origin: the S187 live-validation finding + the Chat
  concurrency probe (30 concurrent → 26 × 500).
- DRs: DR-031 (SQLite WAL tech stack), DR-030 (module boundary),
  DR-021 (Adelaide time), settlement byte-identity.
- Arc: interface-refinement / pre-cutover — clears the Accounts
  screen and the log-panel account picker before W16 cutover
  scoping.
- Adjacent (NOT in this brief): the "remove My own account box +
  auto-fill cluster/platform from desktop research" enhancement
  — a separate frontend + research-logic scope, parked.
- Parking-lot: a structural lint/guard that fails CI if a future
  endpoint-facing storage holds a thread-bound connection
  (broader anti-recurrence; optional hardening, not pulled into
  this fix).

---
*End of brief. LOCKED S187 2026-06-25 ACST.*
