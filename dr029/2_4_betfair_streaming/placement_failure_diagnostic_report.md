# Report — Placement-failure full diagnostic (capture the real Betfair error, end-to-end)

**Executed:** 2026-06-18 ACST (Adelaide-local, DR-021)
**Brief:** `dr029/2_4_betfair_streaming/placement_failure_diagnostic_brief.md`
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Type:** Diagnostic / observability — no behaviour change.

---

## 1. What changed

A new diagnostic helper plus capture calls at the three layers where the
real Betfair failure detail is collapsed into the catch-all
`betfair_api_unreachable`. Capture, then re-raise/return the **same**
exception/value — no fix, no gate change, no mapping change.

### 1.0 — Helper (`clients/betfair_client/v1/_failure_diagnostics.py`, new)

`capture_placement_failure(stage, **detail)` → one redacted **WARNING**
line on the Terminal (logger `clients.betfair_client.v1._failure_diagnostics`,
a child of the surfaced namespace) **and** one appended JSON line to
`/tmp/bethub_placement_failures.jsonl`. Lives in `clients/…` (lowest common
layer) so both the clients modules and `ui/…/composition.py` can import it —
the same submodule-import pattern composition already uses for `_translation`.
Never raises (the `/tmp` write is best-effort, `try…except OSError`).

Credential-safety is built in: callers pass only non-secret fields, and
`_redact()` recursively drops any secret-shaped key (`x-authentication`,
`x-application`, `authorization`, `session_token`, `app_key`, `password`, …)
as defence-in-depth, plus an 8 000-char soft cap (truncation marked, never
silent).

### 1.1 — Transport boundary (`composition.py` `_build_live_httpx_transport`, point 1)

Wrapped `client.post` + `raise_for_status()` in `try`; on failure, capture
then **bare `raise`** (the identical exception):

```python
try:
    response = client.post(url, json=body, headers=headers)
    response.raise_for_status()
except httpx.HTTPStatusError as exc:
    capture_placement_failure("transport_http_error", url=url, method="POST",
        request_body=body, response_status=exc.response.status_code,
        response_body=exc.response.text)          # status + RAW body
    raise
except httpx.RequestError as exc:
    capture_placement_failure("transport_request_error", url=url, method="POST",
        request_body=body, error_class=type(exc).__name__, error_repr=repr(exc))
    raise
payload: dict[str, Any] = response.json()         # success path unchanged
return payload
```

`headers` are **never** passed to the capture (§5.4).

### 1.2 — JSON-RPC error mapping (`_translation.py` `TranslatingTransport.__call__`, point 2)

One capture inserted before the unchanged raise — the full raw error object
(`code` / `message` / `data.APINGException.errorCode`) **before** the
collapse to a coarse `status_code`:

```python
if "error" in rpc_response and rpc_response["error"]:
    capture_placement_failure("jsonrpc_error", json_rpc_url=self._url,
                              error=rpc_response["error"])
    raise _rpc_error_to_rest_error(rpc_response["error"])   # unchanged
```

`_rpc_error_to_rest_error` (the mapping) is untouched.

### 1.3 — Placement catch (`placement.py` `except BetfairRestError`, point 3)

Per FLAG 4 ruling — a plain placement-logger line (no helper, no `/tmp`),
beside the existing reason line, before the unchanged `return env`:

```python
logger.warning("betfair placement failed (ref=%s): %s",
               customer_order_ref, env.reason.value)        # existing
logger.warning("betfair placement failed (ref=%s) raw: status_code=%s message=%s",
               customer_order_ref, exc.status_code, exc.message)   # added
return env
```

---

## 2. Behaviour-unchanged proof

Each point captures, then re-raises/returns the **same** value:

- Point 1: `except … as exc: capture(...); raise` — the bare `raise`
  re-raises the **identical** exception; the success path (`json()` →
  `return`) is outside the `try`, untouched. Tests (a)/(b)/(e) assert the
  original `httpx.ConnectError` / `httpx.HTTPStatusError` still propagates.
- Point 2: the `raise _rpc_error_to_rest_error(...)` line is unchanged and
  returns the **same** mapped `BetfairRestError`. Test (c) asserts the
  mapping still yields `status_code=None` for an unrecognised errorCode.
- Point 3: a log line before the unchanged `return env`; the gate,
  `_emit_entry`, mapping, and the existing reason line are untouched.

The bet-safety gate, the order body, the REST call, and the translation
logic are not modified. **Note (finding F3):** `_translation.py` and
`placement.py` were already `M` with pre-existing in-flight v3 work, so a
raw `git diff` against HEAD shows unrelated changes too; the
behaviour-unchanged guarantee rests on **the full suite staying green
(1018, every pre-existing test included)**, not on a clean diff. My
additions are confined to the import + the capture/log calls shown above.

### No `uvicorn.access` duplication (runtime check)

```
child.propagate: True   child.handlers: []
parent (clients.betfair_client.v1) has bethub handler: 1   parent.propagate: False
root has bethub handler: 0
child effective level: INFO
times reached a handler across parent+root: 1  (expect 1 — parent only, not root)
```

The helper's child logger reaches the parent's `bethub-app-stream` handler
once, then stops (parent `propagate=False`) — never root. `logging_setup.py`
untouched.

---

## 3. Credential-safety proof

- **By construction:** point 1 passes URL, method, request *body*, response
  status, response *body* — never `headers` (which carry `X-Authentication`
  / `X-Application`). Points 2/3 carry only Betfair's own error object /
  `exc.message`.
- **Defence-in-depth:** `_redact()` drops secret-shaped keys from any dict
  handed in.
- **Test (e)** feeds a sentinel secret (`SUPER-SECRET-TOKEN-sentinel-XYZ`)
  as the session token through the headers into point 1 **and** straight
  into the helper as a `headers={…}` dict, then asserts the sentinel appears
  in **neither** the captured Terminal output **nor** the `/tmp` record
  (and that `<redacted>` is present). Green.

---

## 4. Test baseline

| Stage  | Command            | Result                    |
|--------|--------------------|---------------------------|
| Before | `uv run pytest -q` | **1013 passed, 0 failed** |
| After  | `uv run pytest -q` | **1018 passed, 0 failed** |

Delta = 5 new tests in `tests/clients/betfair_client/v1/test_placement_failure_diagnostic.py`:

- (a) `test_connect_failure_captured_and_reraised` — `httpx.RequestError`
  fork: capture names the transport failure + URL; original exception
  re-raised.
- (b) `test_http_error_captures_status_and_raw_body` — `httpx.HTTPStatusError`
  fork: `/tmp` record carries status **and the raw body**.
- (c) `test_jsonrpc_error_captures_full_error_object` — HTTP-200 Betfair
  JSON-RPC error with an **unrecognised** `APINGException.errorCode`:
  capture records the full error object incl. `errorCode` + `message`; the
  mapping still yields `status_code=None`.
- (d) `test_placement_catch_logs_status_and_message` — `place_bet`'s
  `except BetfairRestError` logs `exc.status_code` + `exc.message`; no `/tmp`
  write from this point (FLAG 4).
- (e) `test_no_credential_in_capture_or_tmp` — the sentinel-secret proof.

`httpx` 0.28.1 is importable in the test env (FLAG 6 confirmed), so (a)/(b)/(e)
build real `httpx` exceptions via a monkeypatched `httpx.Client` — no socket.

**One prior assertion updated:** last session's
`test_rest_error_logs_warning_with_mapped_reason` asserted *exactly one*
WARNING in the REST-error branch; point 3 adds a second (the raw line), so
the assertion now filters for the mapped-reason line (`"raw:" not in …`).
Same intent, file already `M`.

Quality gates: `ruff check` → **All checks passed!** on all touched files;
`uv run lint-imports` → **5 kept, 0 broken** (DR-030 — the helper sits in
`clients/…`, imported downward by composition, contracts intact).

---

## 5. What the operator will now see

On the next live lay, the Terminal prints a tagged WARNING and the same
record is appended to `/tmp/bethub_placement_failures.jsonl`. The three forks
are distinguishable by `stage`:

**Connect failure** (`transport_request_error`):
```
WARNING …_failure_diagnostics: PLACEMENT FAILURE [transport_request_error] url='…/json-rpc/v1', method='POST', request_body={…placeOrders…}, error_class='ConnectError', error_repr="ConnectError('…')"
/tmp ▸ {"stage":"transport_request_error","url":"…","method":"POST","request_body":{…},"error_class":"ConnectError","error_repr":"…"}
```

**HTTP-error response** (`transport_http_error`):
```
WARNING …_failure_diagnostics: PLACEMENT FAILURE [transport_http_error] url='…', method='POST', request_body={…}, response_status=400, response_body='{"detail":"…","errorCode":"…"}'
/tmp ▸ {"stage":"transport_http_error","response_status":400,"response_body":"{…full Betfair body…}", …}
```

**JSON-RPC error** (`jsonrpc_error`) — the most likely live fork (see F1):
```
WARNING …_failure_diagnostics: PLACEMENT FAILURE [jsonrpc_error] json_rpc_url='…', error={'code':-32099,'message':'ANGX-…','data':{'APINGException':{'errorCode':'PERMISSION_DENIED', …}}}
WARNING …placement: betfair placement failed (ref=…) raw: status_code=None message=PERMISSION_DENIED
/tmp ▸ {"stage":"jsonrpc_error","json_rpc_url":"…","error":{"code":-32099,"message":"…","data":{"APINGException":{"errorCode":"PERMISSION_DENIED"}}}}
```

Whatever the fork, the `errorCode`/message/status/body are now on screen and
in the file — no further diagnosis needed.

---

## 6. Findings + self-assessment

- **F1 — the uncaught-transport gap (name for a later brief; NOT fixed
  here).** `BetfairRestClient.post` has no error handling, and
  `_build_live_httpx_transport` raises **raw** httpx (unlike
  `_build_login_transport`, which converts). So a genuine connect / HTTP-error
  on the order-place POST propagates **uncaught** out of `place_bet` — it
  would surface as a **500, not the observed 503**. The observed
  `betfair_api_unreachable` (a `BetfairRestError` with `status_code` not in
  {401,403,429}) therefore implies the **JSON-RPC-error fork** (point 2 /
  `exc.message`): Betfair returned HTTP 200 with an error object whose
  `errorCode` the small mapping doesn't recognise. Point 1 is captured anyway
  as completeness insurance and re-raises unchanged. The uncaught-transport
  gap is a real robustness issue for a later fix brief.
- **F2 — point 2 is a shared surface.** `TranslatingTransport.__call__`
  handles reads and writes, so the `jsonrpc_error` capture fires on any
  JSON-RPC error, not only placement. It is failure-only (§9.5) and
  stage-tagged, so the `/tmp` file disambiguates; in the live one-lay
  scenario it is the placement error.
- **F3 — pre-existing dirty files.** `_translation.py`, `placement.py`,
  `test_placement.py`, and `test_translation.py` were already `M` with
  in-flight v3 work before this session; my edits are isolated within them.
  Behaviour-unchanged is evidenced by the green suite, not a clean diff.
- **Dirty-tree delta (per FLAG 1 + FLAG 5):** **58 → 61.** New: `??
  clients/betfair_client/v1/_failure_diagnostics.py`, `??
  tests/clients/betfair_client/v1/test_placement_failure_diagnostic.py`, and
  ` M tests/conftest.py` (the FLAG-5 autouse redirect — the +1 beyond FLAG
  1's estimate of 60, required to guarantee no test ever writes the real
  `/tmp` file). The three edited source targets keep their existing status
  (`composition.py` `??`, `_translation.py` `M`, `placement.py` `M`), as does
  `test_placement.py` (`M`). The `/tmp` file is **absent** after the full
  suite and **never** appears in `git status`. No git write commands run.
- **Self-assessment:** all five hard limits held — diagnostic only;
  credentials never captured (test e); no live Betfair / network / order;
  no git writes and the `/tmp` file out of the repo; failure-path only (zero
  on success — the existing success/partial-match placement tests emit no
  capture). The Code-proves-wiring / operator-proves-live split is intact:
  the next `BetHub.command` lay now carries the complete raw cause, and the
  **next brief is the fix** (no further diagnosis). No fix proposed here.
```
