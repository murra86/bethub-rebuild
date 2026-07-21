# Brief — Streaming transport TLS trust fix (certifi CA bundle)

**Drafted:** Session 161, 2026-06-18 ACST
**Type:** Surgical fix to a known issue (Sessions 35/36 precedent).
**Target repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`).
**Governing DRs:** DR-029 §2.4 (Betfair Streaming spec — the
transport's authority), DR-030 (v3 module layout — the transport's
home under `clients/betfair_client/v1/`), DR-032 (Betfair canonical
/ auth), DR-021 (Adelaide-local timestamps in the report).

---

## 1. What this brief is and is not

This is a **single, bounded surgical fix** in one Code session.
Code makes one substantive change — give the live streaming
transport's TLS context an explicit CA-certificate bundle — plus
the minimal supporting edits named below, runs the test suite, and
writes one report.

It is **not** a hardening pass, not a feature build, not a refactor.
Surprises become findings in the report, not new work. Remediation
of anything Code discovers routes back to operator-Claude triage in
the next Chat session — Code does not chase it.

## 2. Why this work exists

At Session 161 the operator launched v3 live to perform the $5 lay
validation. The app started, but the Betfair streaming connection
failed repeatedly at the TLS handshake:

```
betfair stream: connection error: [SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: self-signed certificate in certificate
chain (_ssl.c:1000)
```

Root cause, confirmed empirically this session against the live Mac
environment:

- The live connector builds its TLS context with a bare
  `ssl.create_default_context()` (no explicit CA bundle), at
  `clients/betfair_client/v1/_stream_transport.py` line 160.
- On this machine the stdlib default verify paths resolve to
  `cafile=None`, `capath=None`, and an `openssl_cafile` of
  `/Library/Frameworks/Python.framework/Versions/3.12/etc/openssl/cert.pem`
  — a file that **does not exist**. So the context loads no trusted
  roots and every chain fails to verify.
- `certifi` IS installed in the venv with a valid bundle at
  `.venv/lib/python3.12/site-packages/certifi/cacert.pem`
  (`certifi.where()` resolves under `uv run`).
- The REST/login path is unaffected (live reads were proven at
  S159) because it goes through `httpx`, which uses certifi's bundle
  by default. Only the new stdlib-asyncio streaming transport built
  at S160 uses the bare context, so only streaming fails.

The fix is to point the streaming TLS context at certifi's bundle —
the same trusted list the rest of the tool already uses.

## 3. Pre-reads

Required, in order:

1. This brief.
2. `clients/betfair_client/v1/_stream_transport.py` — the file
   being edited. Read the import block (around lines 50–55) and the
   `_default_connector` function (around lines 150–161).

Reference-only (read on demand, not required):

- `dr029/2_4_betfair_streaming/stream_transport_build_report.md` —
  the S160 build report this fix follows.
- `dr029/2_4_betfair_streaming/stream_transport_build_brief.md` —
  the S160 build brief (precedent + the bet-safety non-negotiables).

## 4. System access

- **Mac filesystem, read-write**, limited to the named anchors in §5.
- **No live Betfair. No real credentials. No network login.** Tests
  run against the fake connector only (see §9). This is a hard limit,
  not a default.
- Test runner is **`uv run pytest`**, never bare `python3` — the
  repo is a `uv` project (Python 3.12 venv); system `python3` is 3.11
  and lacks `httpx`, so it fails at collection. (S160 finding F1.)
- Adelaide-local timestamps (ACST/ACDT) for every time reference in
  the report, per DR-021.

## 5. The fix

All edits live in **one file**:
`clients/betfair_client/v1/_stream_transport.py`. (Exception: §5.3
may touch `pyproject.toml` / `uv.lock` if certifi is not already a
direct dependency.)

### 5.1 — Give the TLS context an explicit CA bundle

At the `_default_connector` function (around line 160), change the
bare context to load certifi's bundle:

```python
# before
context = ssl.create_default_context()

# after
context = ssl.create_default_context(cafile=certifi.where())
```

No other behaviour in that function changes — `asyncio.open_connection(host, port, ssl=context)` stays as-is.

### 5.2 — Import certifi

Add `import certifi` to the import block. It is a third-party import,
so it belongs in its own group after the stdlib block (after
`from typing import Any, Protocol`) and before the local `from .`
imports. Match the file's existing import-grouping style.

### 5.3 — Make certifi a declared dependency

certifi is currently present in the venv transitively (pulled by
`httpx`). Confirm whether it is a **direct** project dependency in
`pyproject.toml`. If it is not, add it explicitly (`uv add certifi`)
so a future dependency change cannot silently remove it. If it is
already direct, make no dependency change and note that in the report.

### 5.4 — Regression test (fake-socket, no network)

Add one small unit test asserting the live connector's TLS context is
built from a non-empty CA store — e.g. construct the context the same
way the connector does and assert
`context.cert_store_stats()["x509_ca"] > 0`, or assert the context is
built with `certifi.where()`. The test must not open any socket or
touch the network. Place it alongside the existing streaming transport
tests. If the cleanest assertion requires a tiny seam (e.g. factoring
the context construction into a helper), that is in scope **only**
within this file and only if it does not change runtime behaviour.

## 6. Sequencing within session

1. Read working-tree state (`git status`) — the tree is dirty with
   in-flight v3 work (see §9); note it, do not touch it.
2. Capture the pre-change test baseline (§7).
3. Apply §5.2 (import), then §5.1 (the context change).
4. Apply §5.3 (dependency check / add).
5. Add §5.4 (regression test).
6. Capture the post-change test baseline (§7).
7. Write the report (§8).

## 7. Empirical verification

**Before:** run `uv run pytest -q` and record the pass count
(expected 1002 passing from S160, 0 failed). Confirm the bare context
loads no roots in this environment — e.g. show that
`ssl.create_default_context().cert_store_stats()` reports zero CA
certs here, while `ssl.create_default_context(cafile=certifi.where()).cert_store_stats()`
reports a non-zero count. This is the static proof of the fix.

**After:** run `uv run pytest -q` and confirm green — the prior count
plus the new §5.4 test, 0 failed. ruff clean on the touched file;
import-linter still passing (DR-030 layering intact).

**Out of scope for Code's verification:** the live connection
actually reaching `SUBSCRIBED`. That requires real Betfair
credentials and a live socket, which §9 forbids. The live proof is
the operator re-running the $5 lay after this fix lands — same
Code-proves-plumbing / operator-proves-live split as the S160 build.

## 8. Output spec

Single report at:
`dr029/2_4_betfair_streaming/cert_fix_report.md`

Sections:

1. What changed — the §5.1/§5.2 diff, shown.
2. certifi dependency status — was it direct already, or added.
3. Test baseline — before/after pass counts, the §5.4 test, the
   `cert_store_stats` before/after numbers.
4. Hard-limit adherence — confirm: no live Betfair / no credentials /
   no network; `placement.py` and the SUBSCRIBED gate untouched; no
   git writes; dirty-file list unchanged; edits confined to §5 anchors.
5. Findings (if any) — anything surprising, as findings not fixes.
6. Self-assessment — did the work fit one session; anything deferred.

Rough length 60–120 lines. The report contains **no** recommendations
beyond the named findings and **no** scope creep into the F3/F4/F5
hardening items.

## 9. Hard limits — what is NOT in scope

Non-negotiable. Code does none of the following:

- **No live Betfair connection, no real credentials, no network
  login.** Fake connector only. This protects the bet-safety story
  and avoids any login activity against Betfair.
- **Do not touch `placement.py` or the SUBSCRIBED interlock.** The
  bet-placing gate is untouched, full stop. It must still pass only on
  a genuine `SUBSCRIBED`.
- **No hardening work.** F3 (`keepAlive`), F4 (operator-visibility /
  the live-data-loss reconnection warning), F5 (`INVALID_CLOCK`
  fresh-image) are a separate post-lay brief. Do not build any of them
  here, even if the file invites it.
- **No git writes.** The tree is dirty with in-flight v3 build work
  (modified tracked files + untracked new files including
  `_stream_transport.py` itself). No `git add`, `commit`, `stash`,
  `restore`, `checkout` (file-targeted), or `reset`. After each edit,
  `git diff <file>` to confirm only intended changes; at close,
  `git status` to confirm the dirty-file list is unchanged apart from
  the edited file(s).
- **Edit only the §5 anchors.** No drift into adjacent code, no
  "while we're here" tidy-ups, no refactors beyond the tiny §5.4 seam
  if needed.
- **No schema changes, no scope creep** into other modules or other
  §2.x items.
- **Files Code may modify:** `_stream_transport.py`; the matching
  test file (§5.4); and `pyproject.toml` + `uv.lock` only if §5.3
  requires `uv add certifi`. Nothing else.

## 10. What happens after Code's session

The operator hands this brief to Code out-of-session; Code produces
`cert_fix_report.md`. The next Chat session triages that report: reads
it off disk, confirms green tests + hard-limit adherence + gate
untouched. If clean, the operator re-runs the live $5 lay (launch
`BetHub.command`, watch the Terminal for `Betfair streaming reached
SUBSCRIBED at startup`, place the lay, check on Betfair). The F3/F4/F5
+ live-data-loss-warning hardening brief stays sequenced **after** the
lay proves SUBSCRIBED. Code does not write that next brief.

## 11. Cross-references

- **DR-029 §2.4** — Betfair Streaming spec (the transport's authority).
- **DR-030** — v3 module layout; the transport's home under
  `clients/betfair_client/v1/`.
- **DR-032** — Betfair canonical / auth.
- **DR-021** — Adelaide-local timestamps in the report.
- **S160 build report + brief** —
  `dr029/2_4_betfair_streaming/stream_transport_build_report.md`,
  `…/stream_transport_build_brief.md`.
- **S160 finding F1** — `uv run pytest` runner (§4).
- **Excluded (parking-lot):** F3/F4/F5 hardening + the live-data-loss
  warning; is_self coordinated-removal; v3 tree commit.
