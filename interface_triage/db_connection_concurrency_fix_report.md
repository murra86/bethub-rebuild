# REPORT — Close the cross-thread DB-connection fault class

**Brief:** `interface_triage/db_connection_concurrency_fix_brief.md`
(LOCKED S187 2026-06-25 ACST).
**Repo under fix:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
(HEAD `2329604`).
**Session:** S187 · 2026-06-25 ACST · single bounded session, READ-WRITE
limited to the §5 anchors.
**Outcome:** Accounts fault fixed at the storage layer; concurrency
guards added red-before / green-after; full suite green; settlement
byte-identical. **Two material findings** surfaced (the brief's "safe"
`get_db_connection` path is in fact faulty; the running app's accounts
provider is composition.py's singleton, not racing.py's `@lru_cache`) —
both handled per §1 as findings, not scope creep.

---

## Baseline (§5.0 gate)

| Check | Expected | Observed | Result |
|---|---|---|---|
| `git rev-parse --short HEAD` | `2329604` | `2329604` | ✓ |
| `git status --porcelain \| wc -l` | `69` | `69` | ✓ |
| `settlement.py` SHA-256 | begins `9e07a75d` | `9e07a75d…40d4a3` | ✓ |
| `accounts.py` ~125 fault anchor | `self._conn = sqlite3.connect(`, no `check_same_thread` | present as stated | ✓ |
| `racing.py` accounts provider | `@lru_cache(maxsize=1)` | present as stated | ✓ |

`settlement.py` resolves to **`workflows/bet_entry/v1/settlement.py`**
(SHA `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3`).
A second `clients/betfair_client/v1/settlement.py` exists (SHA
`73f0561b…`) — a different file, not the protected one; left untouched.

**Gate result: PASS — proceeded.** No drift; no STOP triggered.

---

## §A — Connection-surface inventory (the sweep)

Criterion (§5.1): **Faulty** = a connection created once and reused
across requests AND reachable from a thread other than its creator.
**Safe** = a connection created, used, and closed within one request /
method call on the thread that serves it.

| # | Path | Wiring | Verdict | Proof (empirical) |
|---|---|---|---|---|
| 1 | `SQLiteAccountsStorage` (`store/repositories/accounts.py`) | held `self._conn` for instance lifetime | **FAULTY** (the confirmed fault) | Long-lived connection bound to its creating thread; reused cross-thread by the threadpool. Reproduced: `/accounts`,`/books`,`/racing/accounts` → ~20–23 × 500 of 24 (TestClient) and 9–23 × 500 (live uvicorn). |
| 1a | …consumed via racing.py `_build_default_accounts_storage` `@lru_cache(maxsize=1)` | process-wide singleton | **FAULTY** (default path) | Singleton holds the thread-bound connection process-wide. |
| 1b | …**actually wired in the running app** via `composition.py` `_accounts_storage` (`configure_dependencies`, line 552) | process-wide singleton cached in `state["accounts_storage"]`, built by `build_storages` (line 422) | **FAULTY** (production path) | `create_app()` (main.py:148) installs this override, which **shadows** 1a. This is the singleton the operator's browser actually hit. See **Finding 2**. |
| 2 | `SQLiteBetRecordStorage` (`store/repositories/bets.py`) | `@lru_cache` singleton, but opens+closes a fresh connection per method under a `Lock` | **SAFE** | No `self._conn`; `_connect()` per method (bets.py:537–542). `/api/v1/bets/provisional` → 24 × 200 under 24-way concurrency, pre- and post-fix. Locked in by `test_safe_bet_storage_path_holds_under_concurrency`. |
| 2a | …also cached in `provisional.py` `_build_default_storage` `@lru_cache` | singleton over the same per-method storage | **SAFE** | Same class as #2; the cache wraps a connection-less storage. |
| 3 | `get_db_connection` per-request dep (`racing.py:186`, `promos.py:65`, `composition.py:436`) | fresh connection per request, closed in the endpoint | **FAULTY** (reclassified — brief said safe) | The connection is created during FastAPI **dependency** resolution (one anyio worker thread) and used/closed in the **endpoint body** (a *different* worker thread). Under concurrency these are different OS threads → `ProgrammingError`. `/api/v1/promos/catalogue` → 22–23 × 500 (TestClient), 6–9 × 500 (live uvicorn). See **Finding 1**. |
| 4 | Conn-receiving repos: `promos.py`, `cash_flow.py`, `ops.py`, `bet_mutations.py` | constructor takes `conn` arg (`self._conn = conn`), built per request around #3 | **SAFE as written, but inherit #3's defect** | They never *create* a connection (constructor `(self, conn)`); lifetime is the per-request #3 connection. Safe in isolation; exposed to #3's cross-thread hop when reached through `get_db_connection`. |
| 5 | bets.py per-emit audit connection (`ui/api/routers/bets.py:258–269`) | opened via factory, used, `conn.close()` in `finally`, all inside one call | **SAFE** | Created/used/closed in a single synchronous call on one thread (bets.py:265–269). |

**Sweep coverage:** every `sqlite3.connect` call site in `store/`,
`ui/`, `workflows/`, `clients/` (non-test) was enumerated and every
endpoint-facing storage/provider classified. The only process-wide
connection-holder reachable by endpoints was the accounts storage
(#1/#1a/#1b). Finding 1 (#3) is a distinct, per-request expression of
the same fault class.

---

## §B — The fix

**File changed:** `store/repositories/accounts.py` (a named §5 anchor).
**Mechanism:** per-method connection, mirroring the proven-safe
`SQLiteBetRecordStorage` — explicitly within the §5.2 latitude clause
("a per-method-connection refactor mirroring bets.py … PROVIDED the §7
guard passes and no shared mutable connection survives").

What changed:

- `__init__` (line 135) no longer opens a long-lived `self._conn`. It
  records `self._db_path`, creates a process-wide `self._lock`, and runs
  `apply_migrations` **once** through a transient connection. Idempotent
  migration behaviour intact (`store/schema/accounts.py` ends with
  `conn.commit()`).
- New `_connect()` (line 141) — opens a fresh connection configured the
  W11 way (`PRAGMA foreign_keys = ON`, `sqlite3.Row`).
- New `_connection()` context manager (line 154) — yields a per-call
  connection created, used, and closed on the **calling** thread, under
  `self._lock`. This is the heart of the fix: the connection never
  outlives the method and is never handed to another thread.
- All 14 CRUD methods (lines 193–403) now run their statements inside
  `with self._connection() as conn:` instead of `self._conn`. Signatures,
  return types, SQL, commit semantics, and the
  `register_account_at_book` IntegrityError classification are unchanged.
- `close()` (line 173) is now a documented no-op (retained for API /
  test-fixture compatibility; there is no longer a long-lived connection
  to close).

**Why not the brief's literal default** (drop racing.py's `@lru_cache`
+ a per-request generator dependency):

1. **It would not fix the running app.** `create_app()` →
   `configure_dependencies` overrides `get_accounts_storage` with
   composition.py's own singleton (Finding 2). Changing racing.py's
   default provider has no effect on the deployed path; composition.py
   is **not** a §5 anchor and is forbidden to edit (§9). Fixing the
   shared object's *class* — the storage — is the only lever that
   reaches the production singleton from within the allowed anchors.
2. **A per-request connection created in a dependency is itself
   cross-thread-unsafe** (Finding 1, proven). The brief's default
   mechanism would have inherited that defect.

Fixing at the storage layer neutralises **every** wrapper at once — the
racing.py `@lru_cache`, the composition.py singleton, and the racing
`list_accounts` consumer — because none of them now holds a connection.
Consequently **racing.py was intentionally left unchanged**: its
`@lru_cache(maxsize=1)` provider is now exactly as safe as the blessed
`_build_default_bet_storage` (a cache over a connection-less storage).
Editing it would be an unnecessary, non-surgical change (§9).

---

## §C — Regression guards

**File added:** `tests/ui/api/test_connection_concurrency.py` (a named
§5 anchor — test module). Harness: `ThreadPoolExecutor` firing
`CONCURRENCY = 24` (≥20, §5.3) simultaneous requests through
`TestClient(app, raise_server_exceptions=False)` against the **real**
providers (no `dependency_overrides`) on a tempfile DB via
`BETHUB_DB_PATH`. This drives genuine anyio worker-thread fan-out — the
condition a sequential `TestClient` loop cannot create, and the reason
the prior 1184-test suite missed the class (every accounts test
overrides the provider with a per-request factory; see
`test_accounts.py:44–47`).

| Test | Endpoint(s) | Pre-fix | Post-fix |
|---|---|---|---|
| `test_accounts_endpoint_holds_zero_500s_under_concurrency[/api/v1/accounts]` | `/api/v1/accounts` | FAIL — 23 × 500 | **PASS — 24 × 200** |
| `…[/api/v1/books]` | `/api/v1/books` | FAIL — 21 × 500 | **PASS — 24 × 200** |
| `…[/api/v1/racing/accounts]` | `/api/v1/racing/accounts` | FAIL — 22 × 500 | **PASS — 24 × 200** |
| `test_safe_bet_storage_path_holds_under_concurrency` (§5.4) | `/api/v1/bets/provisional` | PASS — 24 × 200 | **PASS — 24 × 200** |
| `test_get_db_connection_path_is_also_cross_thread_unsafe` (§5.4 → evidence) | `/api/v1/promos/catalogue` | (fault) | **XFAIL** — documents Finding 1 |

Guard-before-fix (§6 step 3) was honoured: the accounts tests were run
RED against the unmodified singleton **before** any edit (62 × 500 of 72
across the three endpoints) and confirmed to reproduce the fault, so the
guard cannot pass vacuously.

The §5.4 get_db_connection guard could not be a green "safe-path
lock-in" because the sweep disproved that verdict. Rather than assert a
falsehood (or leave a hard failure that would breach §7), it is an
`xfail` carrying the full finding text — executable evidence in the
suite that xpasses the day Finding 1 is fixed.

---

## §D — Pre/post verification

**Fault reproduced then cleared** — two independent harnesses:

- *TestClient (anyio threadpool):* accounts endpoints 20–23 × 500 →
  **0 × 500 (24 × 200)** after fix.
- *Live `uvicorn` server (production ASGI stack), 24 concurrent `httpx`
  clients:*

  | Endpoint | Pre-fix | Post-fix |
  |---|---|---|
  | `/api/v1/accounts` | 9 × 500 | **24 × 200** |
  | `/api/v1/books` | 23 × 500 | **24 × 200** |
  | `/api/v1/racing/accounts` | 23 × 500 | **24 × 200** |
  | `/api/v1/bets/provisional` (safe) | 24 × 200 | 24 × 200 |
  | `/api/v1/promos/catalogue` (Finding 1) | 9 × 500 | 6 × 500 (out of scope) |

  The pre-fix accounts numbers match the brief's browser probe (26 × 500
  / 4 × 200 of 30) in character — the few 200s are requests that land on
  the connection's creating thread.

- **Safe-path guards:** bet-storage path 24 × 200 (locked in green).

- **Full suite:** `uv run pytest` →
  **1188 passed, 1 xfailed, 0 failed** (7.76 s). Baseline was 1184
  passed; delta = **+4 passed** (3 accounts param-variants + 1
  bet-storage safe-path) **+1 xfailed** (the Finding-1 evidence test).
  **No new failures; no pre-existing failure observed.**

- **settlement.py:** SHA-256 `9e07a75d…40d4a3` **identical pre and
  post** — byte-identical, no contact.

- **`git status`:** dirty count **69, unchanged**; the porcelain list is
  byte-identical to the pre-session snapshot. Both anchor files fall
  inside already-untracked entries — `?? store/repositories/accounts.py`
  (already an untracked file; its content changed, its porcelain line did
  not) and `?? tests/ui/` (the new test file is absorbed into this
  pre-existing untracked-subtree entry). No git state-changing command
  was run.

---

## §E — What was NOT touched

- **`settlement.py`** (`workflows/bet_entry/v1/`) — byte-identical
  (`9e07a75d…40d4a3`). No contact with it,
  `apply_manual_operator_resolution`, or the `provisional.py` settlement
  path.
- **The safe connection paths' production code** — `get_db_connection`
  providers (racing/promos/composition), `SQLiteBetRecordStorage`, the
  bets.py audit emit. (Finding 1 notwithstanding, these were not edited —
  out of scope per §5.2/§9; recorded for follow-up.)
- **The bet-storage cache** — untouched.
- **`racing.py`** — the accounts provider was left unchanged
  (intentional; see §B). No drift into adjacent code.
- **`composition.py`** — not a §5 anchor; read-only. Its accounts
  singleton is now safe by virtue of the storage-layer fix.
- **Schema / DDL** — zero changes. Connection-lifetime fix only.
- **No git state-changing ops.** No follow-up brief drafted.

---

## Self-assessment

- **Coverage.** Every endpoint-facing connection path was enumerated and
  empirically classified (not asserted). The confirmed accounts fault is
  fixed and proven cleared on both TestClient and a live server. The fix
  reaches the *production* wiring (composition.py's singleton), not just
  racing.py's default.
- **Confidence: high** on the accounts fix. It mirrors the codebase's
  own proven-safe pattern (`bets.py`, independently re-verified at 24 ×
  200 here), holds no shared mutable connection, and passes red-before /
  green-after on two harnesses plus the full 1188-test suite.

**Finding 1 — `get_db_connection` is not cross-thread-safe (brief said
"safe").** FastAPI resolves a sync dependency and its sync endpoint in
separate anyio worker-thread dispatches; under concurrency the
per-request connection is created on one thread and used/closed on
another → `sqlite3.ProgrammingError` → 500. Reproduced on the live
server (traceback at `promos.py:136 conn.close()`). This is the same
fault class as the accounts singleton, expressed per-request rather than
process-wide. **Out of scope** here (§5.2 scopes the fix to the accounts
path; §9 forbids touching the safe-path providers). It is latent for any
screen that fires concurrent reads through `get_db_connection`
(promos catalogue, racing log-context, and the W12/W13 derivations).
Recommend a follow-up brief: either give those endpoints a per-method /
thread-confined connection, or open the connection inside the endpoint
body rather than the dependency. Captured as the `xfail` evidence test.

**Finding 2 — the running app's accounts provider is composition.py's
singleton, not racing.py's `@lru_cache`.** `create_app()` →
`configure_dependencies` (main.py:148) overrides `get_accounts_storage`
with `_accounts_storage`, a process-wide `SQLiteAccountsStorage` cached
in `state` (composition.py:519–527, built by `build_storages` at line
422). The brief's §5.0/§3 fault anchor (racing.py's `@lru_cache`) is
shadowed in production. This is why the fix had to land at the storage
layer to be effective; it is also why no racing.py edit was necessary.

- **Uncertain verdicts:** none left uncertain. The one path the brief
  pre-classified that I could not confirm as stated — `get_db_connection`
  — was disproved with direct evidence (Finding 1), not left ambiguous.
- **Not provable in one session:** the production impact radius of
  Finding 1 (which live screens fire enough concurrent `get_db_connection`
  reads to trip it in the browser) — that belongs to the resumed
  live-validation sweep, not this bounded fix.
- **Residual:** the `xfail` test will `xpass` if Finding 1 is later
  fixed, prompting retirement of the marker.

---
*End of report. S187 2026-06-25 ACST.*
