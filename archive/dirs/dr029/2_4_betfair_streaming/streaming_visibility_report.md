# Report — Streaming bring-up visibility (Terminal diagnostic surface)

**Executed:** 2026-06-18 ACST (Adelaide-local, DR-021)
**Brief:** `dr029/2_4_betfair_streaming/streaming_visibility_brief.md`
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Type:** Observability / diagnostic-enablement — no behaviour change.

---

## 1. What changed

Two additive changes plus one new helper module and its test. No
streaming logic, control flow, timeouts, or the placement gate were
touched.

### 1.1 — Logging configuration (§5.1)

New module **`ui/api/logging_setup.py`** with `configure_logging()`,
called once from `create_app()`.

**Mechanism chosen — named-namespace handlers, `propagate=False`, root
untouched.** It attaches one tagged stderr handler (INFO, timestamped)
to exactly the two app namespaces — `ui.api.main` and
`clients.betfair_client.v1` — and sets `propagate=False` on them. This
is the deliberate anti-double-log choice (§5.1 pitfall): the known way
to duplicate `uvicorn.access` is to add a handler to the **root** logger
around uvicorn's own `dictConfig`. By configuring only the named app
loggers and stopping their propagation, their records print exactly once
via our handler and never reach whatever uvicorn installs on root.
uvicorn's own loggers and levels are left as-is.

```python
# ui/api/logging_setup.py (core)
_APP_LOGGER_NAMESPACES = ("ui.api.main", "clients.betfair_client.v1")
_HANDLER_NAME = "bethub-app-stream"

def configure_logging() -> None:
    for namespace in _APP_LOGGER_NAMESPACES:
        target = logging.getLogger(namespace)
        target.setLevel(logging.INFO)
        target.propagate = False          # root-safe: no uvicorn.access dup
        if not _already_configured(target):   # idempotent: tagged-handler guard
            target.addHandler(_build_handler())
```

```python
# ui/api/main.py — create_app()
def create_app() -> FastAPI:
    configure_logging()        # surface app namespaces at INFO (brief §5.1)
    settings = get_settings()
    ...
```

**Idempotency:** the handler is tagged `bethub-app-stream`; re-attachment
is skipped if a handler of that name is already present. The suite builds
the app many times and `create_app()` runs `configure_logging()` at
import — handler count per namespace stays 1 (verified §2, §3).

### 1.2 — Bring-up outcome made explicit (§5.2)

In `ui/api/main.py`, additive log statements only — no change to the
15s budget, the await/timeout, the fail-safe startup, or teardown.

```python
# lifespan() — item 1: resolved mode + attempt
if settings.betfair_mode == "live":
    logger.info(
        "Betfair mode resolved to 'live'; attempting live streaming "
        "bring-up (budget %ss).", LIVE_STREAMING_BRINGUP_TIMEOUT_SECONDS,
    )
```

```python
# _bring_up_live_streaming() — item 3: enrich failure with furthest state
else:
    reached_state = client.streaming_status().state.value
    logger.error(
        "Betfair streaming did NOT reach SUBSCRIBED within %ss at "
        "startup; furthest state reached: %s. ...",
        LIVE_STREAMING_BRINGUP_TIMEOUT_SECONDS, reached_state,
    )
```

- Item 2 (success "reached SUBSCRIBED at startup") — unchanged.
- Item 4 (factory-missing ERROR) — kept as-is.

### 1.3 — Transport log lines (§5.3)

**`_stream_transport.py` not touched.** Every load-bearing step in the
connect→subscribe path already logs at INFO: `socket open to host:port`
(line 360) and each outbound op via `_send` — `→ authentication`,
`→ marketSubscription`, `→ orderSubscription` (line 588) — plus
reconnect-wait (326), connection-error (340), and session-error (484/491)
lines. No step logs nothing, so the §5.3 condition for adding a line is
not met. Recorded as finding F1.

---

## 2. Double-log check

Structural proof that `uvicorn.access` records have **no path** to our
handler (runtime inspection after `configure_logging()` ran twice):

```
root has bethub handler: 0
uvicorn.access has bethub handler: 0
uvicorn.access.propagate: True (uvicorn-owned, untouched)
ui.api.main:                  bethub-handler-count=1 level=INFO propagate=False
clients.betfair_client.v1:    bethub-handler-count=1 level=INFO propagate=False
paths from uvicorn.access to bethub handler: 0
```

Our handler lives only on the two app namespaces, and those do not
propagate. `uvicorn.access` reaches our handler only via root
propagation; root carries no bethub handler. Therefore zero duplication
paths. Count stays 1 after a second `configure_logging()` (idempotent).

---

## 3. Test baseline

| Stage  | Command            | Result                  |
|--------|--------------------|-------------------------|
| Before | `uv run pytest -q` | **1003 passed, 0 failed** |
| After  | `uv run pytest -q` | **1005 passed, 0 failed** |

Delta = the 2 new tests in `tests/ui/api/test_logging_setup.py`:

- `test_app_namespaces_surface_at_info` — for each namespace: the tagged
  handler is attached, level is INFO, `propagate is False`; and an INFO
  record emitted on the namespace reaches a captured handler (a record
  below effective level would be dropped before any handler, so a
  captured INFO record proves the INFO wiring). Fake, no socket.
- `test_configure_logging_is_idempotent` — three `configure_logging()`
  calls leave exactly one tagged handler per namespace.

Quality gates on touched files:

- `ruff check ui/api/main.py ui/api/logging_setup.py tests/ui/api/test_logging_setup.py` → **All checks passed!**
- `uv run lint-imports` → **5 kept, 0 broken** (DR-030 unchanged).

---

## 4. Hard-limit adherence

- **No streaming-logic change.** Only log statements added; connect,
  auth, subscribe, reconnect, heartbeat, the 15s bring-up budget, the
  cache, and every state transition are byte-for-byte unchanged.
- **`placement.py` and the SUBSCRIBED interlock untouched** — not in the
  edit set; the gate still refuses unless a genuine `SUBSCRIBED`.
- **No live Betfair / credentials / network login.** Tests use the
  fake/mock paths only; the new test does no I/O beyond in-memory logging.
- **No git writes.** No add/commit/stash/restore/checkout/reset.
  `git status --short` = **56 lines before and after, identical.** Edits
  land under the already-untracked `ui/api/` and `tests/ui/` dirs (and
  `main.py` is itself within untracked `ui/api/`), so the porcelain dirty
  list does not change.
- **No `uvicorn.access` duplication** — proven in §2.
- **Edits confined to §5 anchors:** `ui/api/main.py`,
  `ui/api/logging_setup.py` (new helper), `tests/ui/api/test_logging_setup.py`.
  No other files. No refactors, no schema changes, no F4 UI work.

---

## 5. What the operator will now see

Next live `BetHub.command` run, the Terminal prints the bring-up story
(timestamped, INFO+). Success shape:

```
2026-06-18 21:14:02 INFO ui.api.main: Betfair mode resolved to 'live'; attempting live streaming bring-up (budget 15.0s).
2026-06-18 21:14:02 INFO clients.betfair_client.v1._stream_transport: betfair stream: socket open to <host>:<port>
2026-06-18 21:14:02 INFO clients.betfair_client.v1._stream_transport: betfair stream: → authentication (id=...)
2026-06-18 21:14:02 INFO clients.betfair_client.v1._stream_transport: betfair stream: → marketSubscription (id=...)
2026-06-18 21:14:03 INFO ui.api.main: Betfair streaming reached SUBSCRIBED at startup.
```

Failure shape (now names how far it got):

```
2026-06-18 21:14:02 INFO  ui.api.main: Betfair mode resolved to 'live'; attempting live streaming bring-up (budget 15.0s).
2026-06-18 21:14:02 INFO  clients.betfair_client.v1._stream_transport: betfair stream: socket open to <host>:<port>
2026-06-18 21:14:02 INFO  clients.betfair_client.v1._stream_transport: betfair stream: → authentication (id=...)
2026-06-18 21:14:17 ERROR ui.api.main: Betfair streaming did NOT reach SUBSCRIBED within 15.0s at startup; furthest state reached: authenticating. ...
```

The `furthest state reached: <state>` plus the presence/absence of the
`→ marketSubscription` line together name the stall point (e.g. stuck in
AUTHENTICATING — auth sent, no ack — versus never leaving CONNECTING).

---

## 6. Findings + self-assessment

- **F1 — transport already fully instrumented.** Every load-bearing
  connect→subscribe step logs at INFO; §5.3's add-a-line condition was
  not met, so `_stream_transport.py` was left untouched. Surfacing the
  `clients.betfair_client.v1` namespace at INFO is sufficient to make
  those existing lines appear.
- **F2 — `propagate=False` is the deliberate trade-off.** App-namespace
  records bypass root entirely. This is what guarantees no
  `uvicorn.access` duplication, and it is correct here because nothing
  else in the app relies on these records reaching root handlers. If a
  future structured-logging/root-aggregation requirement lands, that
  decision should be revisited — flagged, not actioned (out of scope).
- **Self-assessment:** All four non-negotiables held. Brief §6 sequence
  followed end-to-end; 1005/0 green, ruff clean, imports 5/5, dirty list
  unchanged apart from the edited anchors. The Code-proves-wiring /
  operator-proves-live split is intact: the live Terminal confirmation is
  the operator's next `BetHub.command` run (§8), not verified here.
