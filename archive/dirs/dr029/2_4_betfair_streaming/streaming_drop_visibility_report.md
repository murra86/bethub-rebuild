# Report — Streaming drop visibility (post-startup state-transition logging)

**Executed:** 2026-06-18 ACST (Adelaide-local, DR-021)
**Brief:** `dr029/2_4_betfair_streaming/streaming_drop_visibility_brief.md`
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Type:** Observability / diagnostic-enablement — no behaviour change.

---

## 1. What changed

One source file plus its existing test file. The state machine in
`clients/betfair_client/v1/streaming.py` had **no logger** (confirmed: no
`import logging`, no `getLogger`, zero `logger.` calls) — every transition
moved silently. It now names each transition in the Terminal, with the
drop reason where the payload carries one. Log statements only: no state,
control-flow, timeout, reconnect/back-off, cache, or gate change.

### 1.1 — Module logger (§5.1)

Added `import logging` and a module logger. Its name resolves to
`clients.betfair_client.v1.streaming`, a **child** of the
`clients.betfair_client.v1` namespace the S161 bring-up work surfaced at
INFO — so its records reach the existing Terminal handler by propagation.
**No handler is added here; `logging_setup.py` is untouched** (§2 below
proves the path and the no-double-log).

```python
# child of the API-surfaced namespace → reaches the existing handler by
# propagation; logging_setup.py untouched (§5.1)
logger = logging.getLogger(__name__)
```

### 1.2 — Log every state transition (§5.2, the load-bearing change)

`_handle_message` snapshots **both** `self._state` and the degraded-data
flag `self._status_degraded` before dispatch, then logs exactly one line
if **either** changed. Capturing at the dispatch site — where `op` and
`payload` are in scope — names every transition generically without
touching any handler's logic or signature. The `if/elif` dispatch is
byte-for-byte unchanged; the only additions are the two snapshot lines and
the trailing `_log_transition(...)` call.

```python
prev_state = self._state
prev_degraded = self._status_degraded
# ... unchanged op dispatch ...
self._log_transition(op, payload, prev_state, prev_degraded)
```

```python
def _log_transition(self, op, payload, prev_state, prev_degraded) -> None:
    state_changed = self._state != prev_state
    degraded_changed = self._status_degraded != prev_degraded
    if not state_changed and not degraded_changed:
        return                                   # routine tick → silent (§5.4)
    if state_changed:
        transition = f"{prev_state.value} → {self._state.value}"
    else:
        flag = "degraded" if self._status_degraded else "recovered"
        transition = f"{self._state.value} ({flag})"
    reason = self._drop_reason(op, payload)
    going_degraded = degraded_changed and self._status_degraded
    if (state_changed and self._state in self._DROP_STATES) or going_degraded:
        logger.warning("betfair streaming: %s (op=%s)%s", transition, op, reason)
    else:
        logger.info("betfair streaming: %s (op=%s)%s", transition, op, reason)
```

**Levels (§5.2 + FLAG 3):** a transition into `RECONNECTING`/`DISCONNECTED`,
or the degraded flag going `False→True`, logs at **WARNING**; progress
toward `SUBSCRIBED` and a recovery (degraded `True→False`) logs at **INFO**.

### 1.3 — Drop reason from the real payload (§5.3, FLAGS 1 & 2)

`_drop_reason` renders whatever keys the `status`/`disconnect` payload
actually carries — it does **not** assume the brief's example field names
(`statusCode`/`errorCode`/…), none of which exist in this module's parsed
shape (the only field `_on_status` reads is `status`). An empty
`disconnect` payload yields no reason field — the line names the bare
transition rather than inventing one (FLAG 2). Data-op (`mcm`/`ocm`)
payloads are never rendered (§5.4).

```python
_DIAGNOSTIC_OPS = frozenset({"status", "disconnect"})

def _drop_reason(self, op, payload) -> str:
    if op not in self._DIAGNOSTIC_OPS or not payload:
        return ""
    fields = ", ".join(f"{key}={payload[key]}" for key in sorted(payload))
    return f" reason: {fields}"
```

---

## 2. No-flood proof + propagation/no-double-log

**No-flood (§5.4):** `mcm`/`ocm` touch neither `self._state` nor
`self._status_degraded`, so the change-guard returns early — no line. A
`heartbeat` sets `self._status_degraded = False`; when it is already
`False` (the common case) that is not a change → no line. Only a heartbeat
that *clears* an active degraded flag logs — and that is the §5.4-allowed
recovery transition, not the routine tick. Asserted by
`test_routine_ticks_produce_no_transition_log`.

**Propagation + no `uvicorn.access` duplication** — runtime check after
importing the API app (which runs `configure_logging()` exactly as
production does), emitting a child WARNING through a probe on both parent
and root:

```
child.propagate: True   child.handlers: []
parent has bethub handler: 1   parent.propagate: False
root has bethub handler: 0
child effective level: INFO
times record reached a handler across parent+root: 1  (expect 1 — parent only, not root)
```

The child has no handler; its record propagates **up to the parent**,
fires the parent's `bethub-app-stream` handler once, then stops there
(`parent.propagate=False`). It never reaches root, so there is no
`uvicorn.access` duplication. `logging_setup.py` did not need to change.

---

## 3. Test baseline

| Stage  | Command            | Result                    |
|--------|--------------------|---------------------------|
| Before | `uv run pytest -q` | **1005 passed, 0 failed** |
| After  | `uv run pytest -q` | **1009 passed, 0 failed** |

Delta = 4 new tests in the existing `tests/clients/betfair_client/v1/test_streaming.py`
(added there, not a new file, so the dirty list stays identical — FLAG 4):

- `test_drop_out_of_subscribed_logs_warning` — a post-startup `disconnect`
  logs `subscribed → reconnecting` at WARNING with `op=disconnect`, and
  (empty payload) **no** invented reason field.
- `test_degraded_status_logs_warning_with_payload_reason` — a degraded
  `status` (no `self._state` change) logs at WARNING carrying the **real**
  field `status=503` (FLAG 1 / FLAG 3).
- `test_heartbeat_clearing_degraded_logs_recovery_at_info` — the §5.4
  exception: the heartbeat that clears the flag logs a recovery at INFO;
  the routine heartbeat itself does not.
- `test_routine_ticks_produce_no_transition_log` — `mcm`/`ocm`/`heartbeat`
  that change nothing emit no line (the no-flood guard).

Quality gates on touched files:

- `ruff check clients/betfair_client/v1/streaming.py tests/clients/betfair_client/v1/test_streaming.py` → **All checks passed!**
- `uv run lint-imports` → **5 kept, 0 broken** (DR-030 unchanged).

---

## 4. Hard-limit adherence (§9)

1. **Observability only.** Log statements added; the `_handle_message`
   dispatch, every transition handler, timeouts, reconnect/back-off, cache,
   and heartbeat handling are unchanged. `_log_transition`/`_drop_reason`
   only read state.
2. **`placement.py` and the SUBSCRIBED interlock untouched** — not in the
   edit set; the gate still refuses unless a genuine `SUBSCRIBED`.
3. **No live Betfair / credentials / network / socket.** Tests drive
   `_handle_message` with the existing fake message fixtures; no I/O.
4. **No git writes; dirty list unchanged.** No add/commit/stash/restore/
   checkout/reset. `git status --short` = **56 lines before and after,
   identical**; both edited files were already `M` tracked-modified, so no
   porcelain line appears or disappears. No handler on root — no
   `uvicorn.access` duplication (§2).
5. **No logging on `mcm`/`ocm`/`heartbeat` routine ticks** — transitions
   only (§2, proven by test).

Edits confined to the §5 anchors: `clients/betfair_client/v1/streaming.py`
and its test file. No other source file.

---

## 5. What the operator will now see

**Success shape** (healthy bring-up — progress to SUBSCRIBED, INFO):

```
2026-06-18 13:48:38 INFO  clients.betfair_client.v1.streaming: betfair streaming: connecting → authenticating (op=connection_ack)
2026-06-18 13:48:39 INFO  clients.betfair_client.v1.streaming: betfair streaming: authenticating → subscribed (op=auth_ack)
```

**Drop shape** (the signal this brief exists for — WARNING naming the drop,
plus the payload reason when Betfair sent one):

```
2026-06-18 14:02:11 WARNING clients.betfair_client.v1.streaming: betfair streaming: subscribed (degraded) (op=status) reason: status=503
2026-06-18 14:02:13 WARNING clients.betfair_client.v1.streaming: betfair streaming: subscribed → reconnecting (op=disconnect)
```

A bare disconnect (empty payload) prints `subscribed → reconnecting
(op=disconnect)` with no reason field — honest, not invented. If a future
real disconnect frame carries diagnostics (e.g. `errorCode`/`errorMessage`),
`_drop_reason` renders whatever keys are present automatically. The
recovery path prints at INFO, e.g. `subscribed (recovered) (op=heartbeat)`.

The live drop line was reproduced by the §2 runtime check, which printed:
`2026-06-18 14:27:40 WARNING clients.betfair_client.v1.streaming: betfair
streaming: subscribed -> reconnecting (op=disconnect)`.

---

## 6. Findings + self-assessment

- **F1 — `disconnect` carries no payload into the handler.** `_handle_message`
  dispatches `self._on_disconnect()` with no payload (the handler takes
  none). The reason is therefore logged at the dispatch site, where
  `payload` is in scope — no signature change. Today's fixtures send an
  empty disconnect payload, so a disconnect names the transition with no
  reason. If the real socket path later parses a disconnect reason into the
  payload, it will surface with no further change. Named, not actioned.
- **F2 — degraded `status` is not a `self._state` transition.** It flips
  `self._status_degraded` only; per the approved FLAG 3 reading (and §5.4's
  "heartbeat clears a degraded flag" example), the change-detector watches
  both fields, so a 503 logs at WARNING and its clearance at INFO.
- **F3 — the initial `DISCONNECTED → CONNECTING` move is outside
  `_handle_message`.** It happens in `connect()` (a lifecycle call, not a
  message), which is the transport's socket-open step and already logs
  `betfair stream: socket open …` at INFO. The brief scoped this change to
  `_handle_message`; that initial step is covered by the transport's
  existing line, so it was not duplicated here. Named for completeness.
- **Self-assessment:** All five hard limits held. Brief §6 sequence
  followed end-to-end; 1009/0 green, ruff clean, imports 5/5, dirty list
  56→56 unchanged, no double-logging. The Code-proves-wiring /
  operator-proves-live split is intact: the live Terminal naming the
  *actual* drop reason is the operator's next `BetHub.command` run (§10).
  No connection fix, no keep-alive/clock work, no recommendation on the
  eventual fix — that is the next operator-Claude session's call.
```
