# Report — Streaming transport TLS trust fix (certifi CA bundle)

**Session:** 161 (Code, out-of-session execution)
**Completed:** 2026-06-18 12:15 ACST
**Brief:** `dr029/2_4_betfair_streaming/cert_fix_brief.md`
**Target repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Outcome:** Fix applied, regression test added, suite green
(1002 → 1003 passing, 0 failed). No live Betfair, no git writes.

---

## 1. What changed

All source edits are in one file:
`clients/betfair_client/v1/_stream_transport.py`. Plus the §5.4
regression test and the §5.3 dependency declaration.

### §5.2 — import certifi

Added as its own third-party group, between the stdlib block and the
local `from .` imports:

```python
 from collections.abc import Awaitable, Callable, Iterable
 from typing import Any, Protocol

+import certifi
+
 from . import _clock
```

### §5.1 — give the live TLS context a certifi CA bundle

The bare context now loads certifi's bundle. Per the §5.4 allowance,
the context construction was factored into a tiny same-file helper
(`_build_tls_context`) so the regression test can assert on the exact
context the live connector builds **without opening a socket**. Runtime
behaviour is unchanged — `open_tls_connection` builds the same context
and still calls `asyncio.open_connection(host, port, ssl=context)`.

```python
+def _build_tls_context() -> ssl.SSLContext:
+    """Build the live streaming TLS context with an explicit certifi CA bundle.
+    ... (zero-root default verify paths on this Mac → CERTIFICATE_VERIFY_FAILED;
+    pinning certifi.where() gives the handshake a real CA store) ...
+    Factored out of open_tls_connection so the trust configuration can be
+    asserted without opening a socket (§5.4); runtime behaviour is unchanged.
+    """
+    return ssl.create_default_context(cafile=certifi.where())
+
+
 async def open_tls_connection(
     host: str, port: int
 ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
     """Default live connector — a real TLS socket to Betfair (§3.1). ..."""
-    context = ssl.create_default_context()
+    context = _build_tls_context()
     return await asyncio.open_connection(host, port, ssl=context)
```

The net effect is exactly the §5.1 change — `create_default_context()`
→ `create_default_context(cafile=certifi.where())` — with the call site
moved one indirection back into the helper.

> Note: the source diff does not appear under `git diff` because
> `_stream_transport.py` and `test_stream_transport.py` are **untracked**
> in the dirty tree (`??`), and git diff skips untracked files. The diffs
> above are rendered from the edits as applied; `pyproject.toml` and
> `uv.lock` are tracked and their diffs were inspected directly (see §2).

## 2. certifi dependency status

certifi was **not** a direct project dependency — it was present in the
venv only transitively (pulled by `httpx`). Per §5.3 it has now been
made direct via `uv add certifi`:

```diff
 dependencies = [
     ...
     "httpx",
+    "certifi>=2026.4.22",
 ]
```

`uv.lock` gained the corresponding certifi lock entry (+18 lines).
`pyproject.toml` and `uv.lock` were **already** in the dirty tree
(modified by in-flight v3 work) before this session; my change adds the
single `certifi` line and its lock entry on top — the `pydantic-settings`
line visible in the pyproject diff is pre-existing in-flight work, not
mine.

## 3. Test baseline

| Stage  | `uv run pytest -q`            |
|--------|-------------------------------|
| Before | **1002 passed**, 0 failed, 4 warnings |
| After  | **1003 passed**, 0 failed, 4 warnings |

The +1 is the new §5.4 regression test,
`test_live_tls_context_has_nonempty_ca_store`, placed alongside the
existing streaming-transport tests in
`tests/clients/betfair_client/v1/test_stream_transport.py`. It builds the
exact context the live connector builds (`_build_tls_context()`) and
asserts `cert_store_stats()["x509_ca"] > 0`. No socket, no network — runs
in 0.02s.

**Static proof of the fix** (the §7 `cert_store_stats` numbers, captured
under `uv run` in this environment):

| Context                                              | `x509_ca` |
|------------------------------------------------------|-----------|
| `ssl.create_default_context()` (bare — old behaviour) | **0**     |
| `ssl.create_default_context(cafile=certifi.where())` (new) | **120** |

`certifi.where()` resolves to
`.venv/lib/python3.12/site-packages/certifi/cacert.pem`. The bare context
loads zero trusted roots here — the empirical confirmation of the
brief's root cause — while the certifi-backed context loads 120, so the
streaming handshake now has a real CA store to verify Betfair's chain
against.

**Static checks (after):**
- `ruff check` on both touched files — **All checks passed**.
- `lint-imports` (import-linter) — **5 contracts kept, 0 broken**;
  DR-030 layered architecture intact.

## 4. Hard-limit adherence

- **No live Betfair / no credentials / no network.** Confirmed. The fix
  is static (CA-bundle wiring); the regression test injects nothing live
  and opens no socket. The only network-adjacent command was `uv add
  certifi`, which resolves/locks a package — no Betfair login, no socket
  to `stream-api.betfair.com`.
- **`placement.py` and the SUBSCRIBED interlock untouched.**
  `clients/betfair_client/v1/placement.py` is clean (not in the dirty
  list) and was never opened or edited. The SUBSCRIBED gate is unchanged
  — the existing `test_no_synthesised_ack_when_status_never_succeeds`
  (interlock stays closed without a genuine SUCCESS) still passes.
- **No git writes.** No `add`/`commit`/`stash`/`restore`/`checkout`/
  `reset` of any kind. Only read-only `git status` / `git diff` were run.
- **Dirty-file list unchanged.** The porcelain status at close is
  byte-for-byte the same set as at open: same 13 modified, same untracked
  set. No file appeared or disappeared. The four files I touched were
  already in the dirty tree before this session (`_stream_transport.py`
  and `test_stream_transport.py` untracked; `pyproject.toml` and
  `uv.lock` modified), so editing them did not change the *list*.
- **Edits confined to §5 anchors.** Only the import block, the connector
  function (+ the §5.4 helper seam), the dependency declaration, and the
  one regression test. No adjacent-code drift, no tidy-ups, no F3/F4/F5
  work.

## 5. Findings

**F1 — Brief/file function-name discrepancy (cosmetic, resolved).** The
brief (§3, §5.1) names the target `_default_connector`. No symbol by that
name exists in the file; the function building the bare context at line
160/161 is `open_tls_connection`. Confirmed with the operator before
editing — `_default_connector` was drawn from the function's docstring
description ("Default live connector …"), not its real symbol name. The
correct function was edited. No code impact; flagged so future briefs
cite the real symbol.

**F2 — `_build_tls_context` helper seam used (in-scope per §5.4).** A
clean regression test that asserts on the *connector's actual* context
(not a hand-rebuilt copy) requires a seam, because `open_tls_connection`
otherwise builds the context and immediately opens a socket in the same
breath. The §5.4 allowance for "factoring the context construction into a
helper … only if it does not change runtime behaviour" covers this
exactly. The seam is one private function in the same file; behaviour is
identical. Recorded here for transparency, not as new work.

No other surprises. Nothing discovered that warrants remediation; no
F3/F4/F5 hardening or live-data-loss-warning work was started.

## 6. Self-assessment

The work fit comfortably in one session and matched the brief's §6
sequence exactly: read dirty-tree state, captured the before baseline,
applied import → context → dependency → regression test, captured the
after baseline, wrote this report. The fix is small, the proof is static
and reproducible, and every hard limit held.

**Deferred (correctly out of scope, per brief):** the live proof — the
streaming connection actually reaching `SUBSCRIBED` against real Betfair.
That is the operator's $5-lay re-run (launch `BetHub.command`, watch for
`Betfair streaming reached SUBSCRIBED at startup`, place the lay, confirm
on Betfair), the same Code-proves-plumbing / operator-proves-live split
as the S160 build. The F3 (`keepAlive`) / F4 (operator-visibility +
live-data-loss reconnection warning) / F5 (`INVALID_CLOCK` fresh-image)
hardening brief stays sequenced *after* the lay proves SUBSCRIBED, and is
not written here.
