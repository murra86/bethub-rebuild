# Brief — Streaming bring-up visibility (Terminal diagnostic surface)

**Drafted:** Session 161, 2026-06-18 ACST
**Type:** Observability / diagnostic-enablement (no behaviour change).
**Target repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`).
**Governing DRs:** DR-029 §2.4 (Betfair Streaming spec), DR-030 (v3
module layout), DR-031 (FastAPI/uvicorn stack), DR-021 (Adelaide-local
timestamps in the report).

---

## 1. What this brief is and is not

This is a **single, bounded observability change** in one Code session.
Code makes the live streaming bring-up **report its outcome reliably in
the Terminal** when the app is launched via `BetHub.command` — the
resolved Betfair mode, whether bring-up was attempted, and the final
`SUBSCRIBED` / did-NOT-subscribe-because-X result, plus the transport's
own connect/auth/subscribe messages.

It is **observability only**. It changes **no** streaming connection
logic — not connect, auth, subscribe, reconnect, the cache, or the
placement gate. Nothing about *how* the stream behaves changes; only
*what we can see* changes.

It is **not** the in-UI live-data-loss warning (operator requirement F4).
That is a later hardening brief, after the lay proves out. This brief is
Terminal-visibility only — the diagnostic foundation that F4 will later
build a UI surface on top of.

Surprises become findings in the report, not new work.

## 2. Why this work exists

At Session 161 the operator launched v3 live (post-cert-fix) to place the
$5 lay. Observed behaviour, confirmed empirically this session:

- The TLS cert fix works — no SSL errors; live prices flow (`200 OK`) via
  the REST fallback path; the market was open throughout (prices 200
  before and after the lay attempt — not a suspended/near-jump market).
- The lay is refused with HTTP 503. The placement gate
  (`placement.py` lines ~158–161) returns `BETFAIR_STREAMING_DISCONNECTED`
  because `streaming_client.streaming_status().state != SUBSCRIBED` at
  placement time. The gate is working correctly — no bet was placed.
- **The streaming connection is not reaching/holding `SUBSCRIBED`, and we
  cannot see why.** `ui/api/main.py` `_bring_up_live_streaming` already
  logs the outcome — `logger.info("…reached SUBSCRIBED at startup")` on
  success, `logger.error("…did NOT reach SUBSCRIBED…")` on timeout,
  `logger.error("…factory missing…")` if the client factory is absent —
  and the transport (`_stream_transport.py`, logger
  `clients.betfair_client.v1._stream_transport`) logs connect/auth/
  subscribe/reconnect events. **None of these appeared in the operator's
  Terminal this run.**
- The launcher (`BetHub.command` line 81) runs bare
  `uv run uvicorn ui.api.main:app …` with no `--log-config`/`--log-level`,
  and the app configures no logging itself. So app-logger output is
  surfaced only by Python's last-resort handler (WARNING+ to stderr) and
  unreliably — INFO is dropped, and even the bring-up ERROR did not show.
  Mode is correctly `live` (launcher exports `BETHUB_BETFAIR_MODE=live`),
  so this is **not** a mode misconfiguration.

Net: the app is producing the diagnostic we need, but it is being
swallowed. This brief makes it visible so the next live run names the
cause — and gives the operator the streaming-state visibility F4 wants.

## 3. Pre-reads

Required, in order:

1. This brief.
2. `ui/api/main.py` — the `_bring_up_live_streaming` function and the
   `lifespan` hook (lines ~42–97) and `create_app` (lines ~100–135).
3. `ui/api/config.py` — `betfair_mode` resolution (env prefix `BETHUB_`).

Reference-only (read on demand):

- `clients/betfair_client/v1/_stream_transport.py` — the transport logger
  and its connect/auth/subscribe/reconnect log lines (logger name
  `clients.betfair_client.v1._stream_transport`). **Do not edit this
  file** unless §5 explicitly requires a log-line addition there; the
  lines it needs already exist.
- `clients/betfair_client/v1/streaming.py` — `streaming_status()` and
  `StreamingConnectionState` (the state the bring-up reports).
- `BetHub.command` — the launcher (line 81 starts uvicorn).

## 4. System access

- **Mac filesystem, read-write**, limited to the §5 anchors.
- **No live Betfair. No real credentials. No network login.** Tests use
  the existing fake/mock paths only. This is a hard limit (see §9).
- Test runner is **`uv run pytest`**, never bare `python3` (S160 F1).
- Adelaide-local timestamps (ACST/ACDT) in the report, per DR-021.

## 5. Scope — make the streaming bring-up visible

The goal is a reliable Terminal diagnostic. Two parts.

### 5.1 — Configure application logging so app loggers surface at INFO

When the app runs (via `BetHub.command` → bare uvicorn), records from
`ui.api.main` and the `clients.betfair_client.v1` namespace (the
transport especially) must appear in the Terminal at INFO and above,
with timestamps.

**Mechanism is Code's call**, within these constraints:

- **Do not duplicate uvicorn's access logs.** The known pitfall: adding a
  handler to the *root* logger before/after uvicorn's own `dictConfig`
  can cause uvicorn's records to print twice. Prefer configuring the
  specific app-logger namespaces (`ui.api.main`,
  `clients.betfair_client.v1`) with their own handler + appropriate
  `propagate`, OR perform the setup at a point in the lifespan that
  composes cleanly with uvicorn's config. Whatever the mechanism, verify
  no double-printing of the `uvicorn.access` lines.
- **Idempotent.** Repeated `create_app()` calls (the test suite creates
  the app many times) must not stack duplicate handlers. Guard the setup.
- **INFO level** for the two app namespaces; leave uvicorn's own levels
  as they are.
- A small dedicated helper (e.g. a `configure_logging()` in a new
  `ui/api/logging_setup.py`, or equivalent) called once from the
  composition path is the suggested shape — but the exact home is Code's
  call per DR-030 layering.

### 5.2 — Make the bring-up outcome explicit and always-logged

In `_bring_up_live_streaming` / `lifespan` (`ui/api/main.py`), ensure the
following are logged on **every** live launch, at INFO (or ERROR for the
failure path), so the Terminal always tells the whole story:

1. The resolved Betfair mode and that live streaming bring-up is being
   attempted.
2. On success: the existing "reached SUBSCRIBED at startup" line (already
   present).
3. On failure/timeout: enrich the existing error line to include the
   **actual `streaming_status().state`** reached (e.g. CONNECTING,
   AUTHENTICATING, DISCONNECTED) so the Terminal shows *how far* it got,
   not just that it failed.
4. The factory-missing path already logs an error — keep it.

This is additive logging only — **no change to control flow, timeouts,
or the connection sequence.** The 15s bring-up budget, the fail-safe
"app still starts" behaviour, and the gate all stay exactly as they are.

### 5.3 — Transport log lines

The transport's connect/auth/subscribe/reconnect lines already exist
(§3 reference). Once §5.1 surfaces the `clients.betfair_client.v1`
namespace at INFO, they appear. **Only** add a transport log line if a
genuinely load-bearing step in the connect→subscribe path currently logs
nothing at all; if so, add a single INFO line at that step and record it
as a finding. Do not otherwise touch `_stream_transport.py`.

## 6. Sequencing within session

1. Read working-tree state (`git status`) — dirty tree (§9); note, don't
   touch.
2. Capture the pre-change test baseline (§7).
3. Apply §5.1 (logging configuration), then §5.2 (bring-up log enrichment).
4. Add the §7 regression test.
5. Capture the post-change test baseline.
6. Write the report (§8).

## 7. Empirical verification

**Before:** `uv run pytest -q`, record pass count (expected 1003 from the
S161 cert fix, 0 failed).

**After:** `uv run pytest -q` green — prior count plus the new test,
0 failed. ruff clean on touched files; import-linter still 5/5 (DR-030).

**New test (fake, no network):** assert the logging configuration causes
`ui.api.main` and `clients.betfair_client.v1` records at INFO to reach a
handler (e.g. via `caplog` / a captured handler), and assert it is
idempotent (configuring twice does not multiply handlers). No socket, no
live Betfair.

**Out of scope for Code's verification:** the live Terminal actually
showing the streaming reason. That needs a live launch, which §9 forbids
Code from doing. The live confirmation is the operator's next
`BetHub.command` run — same Code-proves-wiring / operator-proves-live
split as the S160 build and the cert fix.

## 8. Output spec

Single report at:
`dr029/2_4_betfair_streaming/streaming_visibility_report.md`

Sections:

1. What changed — the logging setup (mechanism chosen + why) and the
   bring-up log enrichment, with the key diffs shown.
2. Double-log check — evidence that `uvicorn.access` lines are not
   duplicated.
3. Test baseline — before/after counts + the new idempotency/visibility
   test.
4. Hard-limit adherence — no streaming-logic change; `placement.py` and
   the gate untouched; no live Betfair; no git writes; dirty list
   unchanged apart from edited files; edits confined to §5 anchors.
5. What the operator will now see — a short example of the Terminal lines
   the next live launch should print (success and failure shapes).
6. Findings + self-assessment.

Rough length 80–140 lines. No recommendations beyond named findings; no
F4 UI-warning work; no other streaming changes.

## 9. Hard limits — what is NOT in scope

Non-negotiable:

- **No streaming behaviour change.** This is observability only. Do not
  alter connect, authenticate, subscribe, the reconnect/back-off loop,
  the heartbeat handling, the 15s bring-up budget, the cache, or any
  state transition. Only logging/visibility is added.
- **Do not touch `placement.py` or the SUBSCRIBED interlock.** The
  bet-placing gate stays exactly as it is — refuses unless a genuine
  `SUBSCRIBED`.
- **No live Betfair, no real credentials, no network login.** Tests use
  fake/mock paths only.
- **No F4 UI work.** The in-tool / on-screen live-data-loss warning is a
  separate later brief. This brief stops at Terminal visibility.
- **No git writes.** Dirty tree (in-flight v3 build: modified tracked
  files + untracked new files). No `add`/`commit`/`stash`/`restore`/
  `checkout`/`reset`. After each edit, `git diff <file>` to confirm
  intended-only changes; at close, `git status` to confirm the dirty
  list is unchanged apart from the file(s) edited.
- **Edit only the §5 anchors.** Expected files: `ui/api/main.py`; a small
  new logging-setup module if Code chooses that shape; the matching test
  file. `_stream_transport.py` only under the narrow §5.3 condition.
  Nothing else. No refactors, no "while we're here" tidy-ups.
- **No schema changes, no scope creep** into other modules or §2.x items.

## 10. What happens after Code's session

The operator hands this brief to Code out-of-session; Code produces
`streaming_visibility_report.md`. The next Chat session triages it
(green tests, no double-logging, gate untouched). Then the operator
re-runs `BetHub.command` live — and this time the Terminal prints the
streaming bring-up story, naming why it will not `SUBSCRIBED`. The
operator brings that Terminal output to the following Chat session, which
triages the **named cause** and scopes the actual connection fix. The F4
UI live-data-loss warning stays sequenced after the lay proves out. Code
does not write the next brief.

## 11. Cross-references

- **DR-029 §2.4** — Betfair Streaming spec.
- **DR-030** — v3 module layout (where a logging-setup module may live).
- **DR-031** — FastAPI/uvicorn stack (uvicorn logging interaction).
- **DR-021** — Adelaide-local timestamps in the report.
- **S160 build report** — finding **F4** (operator-visibility tier), the
  requirement this brief begins to serve; and **F1** (`uv run pytest`).
- **S161 cert fix** — `dr029/2_4_betfair_streaming/cert_fix_report.md`
  (the prior fix that unblocked TLS, taking the baseline to 1003 tests).
- **Excluded (parking-lot):** F3 (`keepAlive`), F5 (`INVALID_CLOCK`), the
  F4 UI warning, is_self removal, v3 tree commit.
