# Brief — Placement-failure full diagnostic (capture the real Betfair error, end-to-end)

**Drafted:** 2026-06-18 (Session 162, Adelaide-local / DR-021)
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Type:** Diagnostic / observability — **no behaviour change.**
**Serves:** DR-029 §2.4 live validation. The decisive diagnostic: the
prior three visibility briefs localised the lay-503 to the Betfair
order-place call failing with the **catch-all** reason
`betfair_api_unreachable`. This brief makes one live lay surface the
*complete raw cause* so no further diagnosis is needed.

---

## 1. What this brief is and is not

A single, bounded, **diagnostic-only** Code session. It captures the
**complete raw failure detail** of a failed Betfair order-place call — the
exact exception, the HTTP status, Betfair's raw response body, and the
underlying error message — at **every layer where that detail currently
gets collapsed**, and emits it to the Terminal plus a `/tmp` file. The
goal is total certainty: whatever the failure fork, the next live lay
names it unambiguously.

It is **not** a fix. It does not change what any layer raises, returns,
maps, or how the order is built/sent, and it does not touch the bet-safety
gate. It only **adds capture + logging**, then lets the existing flow
proceed unchanged. Surprises become findings; the actual fix is the next
session's brief, scoped off what this run reveals.

## 2. Why this work exists — the collapse chain

The real Betfair error exists in the code at the moment of failure, but
three layers each discard a notch of it before anything is logged:

1. **`_build_live_httpx_transport._transport`** (composition.py) — does
   `client.post(...)`, `response.raise_for_status()`, `response.json()`
   with **no error handling**. A connect failure (`httpx.RequestError`)
   or an HTTP error (`httpx.HTTPStatusError`, carrying the **raw response
   body**) propagates out raw — and is never logged.
2. **`TranslatingTransport` / `_rpc_error_to_rest_error`** (_translation.py)
   — for a Betfair JSON-RPC error (HTTP 200 with an error object), this
   reads `data.APINGException.errorCode`, maps a *small known set* to
   401/429/503, and **collapses everything else to `status_code=None`**.
   The real `errorCode`/message is put on `BetfairRestError.message` —
   then nothing logs `message`.
3. **`place_bet` `except BetfairRestError`** (placement.py) — logs only
   `env.reason.value` (the placement-visibility line), i.e. the **mapped
   catch-all** `betfair_api_unreachable`, discarding `exc.status_code`
   and `exc.message`.

So `betfair_api_unreachable` is the bucket for "any `BetfairRestError`
that isn't 401/403/429" — it can mean a genuine connect failure, a Betfair
HTTP error, OR a Betfair JSON-RPC rejection with an unrecognised
`errorCode`. This brief captures the raw truth at points 1–3 so we know
which, and exactly what Betfair said.

## 3. Pre-reads

Required, in order:

1. This brief.
2. `placement_visibility_brief.md` + `placement_visibility_report.md`
   (same folder) — the prior placement logging this extends; establishes
   the logger and the four outcome lines.
3. The three files edited (§5): `ui/api/dependencies/composition.py`
   (`_build_live_httpx_transport`), `clients/betfair_client/v1/_translation.py`
   (`_rpc_error_to_rest_error` + its caller in `TranslatingTransport`),
   `clients/betfair_client/v1/placement.py` (the `except BetfairRestError`
   branch).

Reference-only: `clients/betfair_client/v1/_errors.py` (the catch-all
mapping — unchanged), `clients/betfair_client/v1/_connection.py`
(`BetfairRestError` carries `.status_code`, `.message`, `.retry_after`).

## 4. System access

- **Mac filesystem, read-write**, confined to the §5 anchors + the `/tmp`
  diagnostic file.
- **No live Betfair. No credentials. No network. No order placed** by
  Code. All forks are exercised with fakes/mocks (§7).
- Test suite under **`uv run pytest`** (uv project; S160 F1). Adelaide
  timestamps per DR-021.
- **Git / dirty-tree:** read working-tree state at start and report the
  delta. `placement.py` is already `M`; `composition.py` and
  `_translation.py` become `M` if currently clean. **No git writes**
  (no add/commit/stash/restore/checkout/reset); no *other* source file
  changes. The `/tmp` diagnostic file is **outside the repo** — it must
  not appear in `git status` at all. Report the exact dirty count.

## 5. Scope — capture the raw failure at all three layers

Add a small diagnostic helper and call it from the three collapse points.
Each call fires **only on a failure path** (never on success), emits a
clearly-tagged block to the Terminal (WARNING/ERROR), and appends one
structured record to a `/tmp` file (recommended:
`/tmp/bethub_placement_failures.jsonl`, JSON-lines, append). Exact helper
shape, file format, and logger choice are Code's call; the requirement is
**completeness and credential-safety** (§9).

### 5.1 — Transport boundary (composition.py `_build_live_httpx_transport`)

Wrap the `client.post(...)` / `raise_for_status()` / `.json()` body so
that on failure it captures, then **re-raises the original exception
unchanged**:

- `httpx.HTTPStatusError` → the **HTTP status code** and the **raw
  response body** (`exc.response.status_code`, `exc.response.text`) — this
  is the full Betfair body for HTTP-error responses.
- `httpx.RequestError` (and subclasses: connect/timeout/SSL) → the
  **exception class name + repr** and the **request URL** — the
  connect-failure fork.
- The **request URL and HTTP method** (already non-secret).

Behaviour is unchanged: capture, then re-raise the *same* exception. Do
not convert, swallow, or alter control flow.

### 5.2 — JSON-RPC error mapping (_translation.py)

At `_rpc_error_to_rest_error` (or the `TranslatingTransport` response-
handling that calls it), capture the **full raw JSON-RPC `error` object**
— `code`, `message`, and the entire `data` (including
`data.APINGException`, which carries the real `errorCode` and often a
per-instruction error) — **before** it is collapsed to a coarse
`status_code`. The mapping itself is unchanged; only a capture call is
added on the error path.

### 5.3 — Placement catch (placement.py `except BetfairRestError`)

In the existing REST-error branch, alongside the current
`env.reason.value` line, also log **`exc.status_code` and `exc.message`**
(the message Betfair/`_translation` put on the exception — likely the
single most direct answer). One line; the branch's logic is otherwise
unchanged (the prior placement-visibility line and the `_emit_entry`/
`return` stay).

### 5.4 — Credential safety (non-negotiable)

The request **headers** carry the Betfair session token
(`X-Authentication`) and app key (`X-Application`). These — and any other
credential — are **NEVER** captured, logged, or written to the `/tmp`
file. Capture URL, method, request *body* (market/selection/side/price/
stake — non-secret), response status, and response *body* only. If the
helper is given headers, it must drop/redact them before any output.

## 6. Sequencing

5.1 (transport raw capture) → 5.2 (JSON-RPC raw capture) → 5.3 (placement
status+message) → 5.4 holds throughout → tests → full-suite baseline. One
pass; the three capture points are independent (no ordering dependency at
runtime — whichever fork fires, its point captures the truth).

## 7. Empirical verification — the "we 100% know" proof

The success criterion is that **every failure fork produces a complete,
distinguishable capture**. Add fake/mock tests (no I/O) covering all four:

- (a) **Connect failure** — inner transport raises `httpx.RequestError`
  (or a stand-in): capture names a transport/connect failure + the URL;
  the original exception still propagates unchanged.
- (b) **HTTP-error response** — inner raises `httpx.HTTPStatusError` with a
  response carrying status (e.g. 400) and a body: capture records the
  status **and the raw body**.
- (c) **JSON-RPC error body** — a HTTP-200 response whose body is a Betfair
  JSON-RPC error with an **unrecognised** `APINGException.errorCode`:
  capture records the **full error object incl. errorCode + message**
  (and the existing mapping still yields `status_code=None`).
- (d) **Placement catch** — `place_bet`'s `except BetfairRestError` logs
  `exc.status_code` + `exc.message` (plus the existing reason line).
- (e) **Credential-safety** — assert the captured Terminal output and the
  `/tmp` record for (a)–(d) contain **no** session token / app key /
  header values (feed a sentinel secret; assert it never appears).

Plus: `ruff` clean on all touched files; `uv run lint-imports` → 5 kept,
0 broken; before/after suite counts; dirty-list delta = exactly the
edited source files, `/tmp` file absent from `git status`; no-double-log
unchanged (reference the prior proof).

## 8. Output spec

Single file: `dr029/2_4_betfair_streaming/placement_failure_diagnostic_report.md`.
Adelaide timestamps. Sections:

1. What changed (the helper + the three capture points; show them).
2. Behaviour-unchanged proof (each point captures then re-raises/returns
   the *same* exception/value; gate + mapping + order build untouched;
   diff is purely additive around them).
3. Credential-safety proof (the redaction + the (e) test).
4. Test baseline (before → after; the five tests named).
5. **What the operator will now see** — sample Terminal block + sample
   `/tmp` record for each of the three forks (connect / HTTP-error /
   JSON-RPC-error), so the operator and next session can read either.
6. Findings + self-assessment.

Length whatever completeness needs (~160–240 lines). No fix proposed.

## 9. Hard limits — non-negotiable

1. **Diagnostic/observability only.** No change to what any layer raises,
   returns, or maps; no change to the order body, the REST call, the
   translation logic, or control flow. Capture, then re-raise/return the
   **same** exception/value. The bet-safety gate + interlock are untouched.
2. **Credentials never captured.** No session token, app key, or request
   headers in any Terminal line or `/tmp` record (§5.4). Proven by test (e).
3. **No live Betfair / credentials / network / order placed** by Code.
   All forks exercised with fakes/mocks.
4. **No git writes.** Edited source files appear `M`; the `/tmp` file is
   outside the repo and must not appear in `git status`. No other source
   file changes. No `uvicorn.access` duplication (reuse the existing
   named-namespace handlers by propagation; no handler on root).
5. **Failure-path only.** Every capture fires only on a failure/error
   path — zero output on a successful placement, zero on the hot read
   paths.

Excluded and named: the actual fix (next session, scoped off this run's
result — whether endpoint/region, a Betfair rejection, or a connect
issue), the in-memory audit-sink durability gap, the 200-market
over-subscription, `cancellation.py` / `replacement.py`, and any change to
`logging_setup.py` or the catch-all mapping in `_errors.py`.

## 10. What happens after Code's session

Next operator-Claude session triages
`placement_failure_diagnostic_report.md` (green tests, behaviour-unchanged,
credential-safety, dirty list clean). Then the operator re-runs
`BetHub.command` live and attempts the $5 lay **once** — the Terminal (and
the `/tmp` file) now carry the **complete raw Betfair failure**: the fork,
the status, the `errorCode`/message, and the body. That fully determines
the root cause, and the **next brief is the fix** — no further diagnosis.

## 11. Cross-references

- **Serves:** DR-029 §2.4 live validation; closes the diagnostic arc the
  three prior visibility briefs opened.
- **Follows:** `placement_visibility_brief.md` / `_report.md` (named the
  catch-all reason); the S162 live runs that localised the 503 to the
  REST place call.
- **DRs:** DR-021 (anchors), DR-030 (module layout — unchanged), DR-032
  (Betfair canonical / auth — the path the result may implicate, fixed
  later, not here).
- **Bet-safety hard rule:** preserved — the placement gate and order flow
  are observed, not modified.
