# Brief — Streaming drop visibility (post-startup state-transition logging)

**Drafted:** 2026-06-18 (Session 162, Adelaide-local / DR-021)
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Type:** Observability / diagnostic-enablement — **no behaviour change.**
**Serves:** DR-029 §2.4 (Betfair Streaming spec) — live-validation
diagnostics. Direct follow-on to `streaming_visibility_brief.md`
(bring-up visibility, executed clean S161→S162).

---

## 1. What this brief is and is not

This is a single, bounded, **observability-only** Code session. It adds
logging to the streaming **state machine** so that when the live stream
leaves `SUBSCRIBED` *after* a healthy startup, the Terminal names it —
with the reason Betfair gave, where one is present.

It is **not** a fix to the connection. It does not add keep-alive, does
not touch clock handling, does not change any streaming behaviour, state,
control flow, timeout, cache, or the placement gate. Nothing about how
the stream connects, stays connected, or reconnects changes. Only log
statements are added.

Surprises are recorded as findings in the report, not chased. Any
remediation routes to the next operator-Claude triage session, not into
this Code run.

---

## 2. Why this work exists

At S162 the operator launched live after the bring-up visibility brief
landed. The Terminal showed the stream reaching `SUBSCRIBED at startup`
(13:48:39) — the S161 "won't subscribe" blocker is cleared at launch.
The operator then attempted the $5 lay; it was refused `503`.

Triaged off the codebase: the lay route delegates to `place_bet`, whose
bet-safety gate refuses unless `streaming_status().state == SUBSCRIBED`.
So by lay-time the stream had left `SUBSCRIBED`. Prices kept returning
`200` because the price path falls back to one-shot REST when the stream
is not eligible — masking the drop on screen.

The blind spot: `clients/betfair_client/v1/streaming.py` — the module
that owns `self._state` — has **no logger** (confirmed: no `import
logging`, no `getLogger`, zero `logger.` calls). Its transition handlers
(`_on_disconnect` → `RECONNECTING`, `_on_status` → degraded, the
connect/auth/subscribe transitions) move state **silently**. The
transport file (`_stream_transport.py`) logs its socket-level steps, but
a Betfair-initiated drop that arrives as a `status`/`disconnect` message
flips state with no line printed. So the screen goes quiet, then the lay
`503`s with no on-screen reason.

This brief lights up those transitions so the next live run names the
drop (e.g. an `errorCode`, a degraded `status`, or a bare disconnect),
which tells the next session whether the real fix is keep-alive,
clock-sync, or something else — before any connection code is written.

## 3. Pre-reads

Required, in order:

1. This brief.
2. `streaming_visibility_brief.md` (same folder) — the bring-up
   visibility brief this follows; establishes the logging conventions
   already in place and the four non-negotiables.
3. `streaming_visibility_report.md` (same folder) — Code's own report on
   that work; §1.1 documents the named-namespace handler already wired
   for `clients.betfair_client.v1` at INFO.

Reference-only (read on demand): `cert_fix_report.md`,
`stream_transport_build_report.md` (S160 §4 findings F3 keep-alive / F5
INVALID_CLOCK — the suspected real causes this brief is designed to
confirm or rule out).

## 4. System access

- **Mac filesystem, read-write**, confined to the named anchors in §5.
- **No live Betfair. No credentials. No network login. No streaming
  socket opened.** Verification is via the existing fake/driven message
  path only (`_handle_message` is test-driven per its own docstring).
- The `bethub-v3` tree is fully uncommitted by design. **No git writes**
  (no `add`/`commit`/`stash`/`restore`/`checkout`/`reset`). The edit
  anchor sits inside the already-untracked tree; the porcelain dirty list
  must read identical before and after.
- Test suite runs under **`uv run pytest`** (the repo is a `uv` project;
  system `python3` is 3.11 and lacks `httpx` — S160 finding F1). Quote
  the baseline with `uv run pytest -q`.
- Adelaide local timestamps (ACST/ACDT) for every time reference in the
  report, per DR-021.

## 5. Scope — what to add

One file: `clients/betfair_client/v1/streaming.py`. Plus its test file.
No other source file is touched. **`logging_setup.py` is NOT touched** —
this module's logger name will be `clients.betfair_client.v1.streaming`,
a child of the `clients.betfair_client.v1` namespace already surfaced at
INFO (S161 work), so its records reach the existing Terminal handler by
normal propagation. Confirm this rather than assume it.

### 5.1 — Module logger

Add a module logger in the same form the transport already uses
(`logger = logging.getLogger(__name__)`). No other structural change.

### 5.2 — Log every state transition (the load-bearing change)

Make `_handle_message` (or the transition handlers it calls) emit one log
line **whenever `self._state` actually changes**, naming the transition
`<from> → <to>` and the triggering `op`. The recommended mechanism is to
capture `self._state` before dispatch and compare after, logging only on
change — this catches every transition generically (connect, auth,
subscribe, **disconnect → RECONNECTING**, and any recovery back to
SUBSCRIBED) without enumerating handlers or altering their logic. Exact
form is Code's call; the requirement is that no state change is silent.

Recommended levels: a drop (`SUBSCRIBED`/`AUTHENTICATING` →
`RECONNECTING`/`DISCONNECTED`) logs at **WARNING** so it stands out in
the Terminal; healthy transitions (toward `SUBSCRIBED`) log at **INFO**.

### 5.3 — Surface the drop reason from the message payload

For the connection-lifecycle ops that carry diagnostics — `status` and
`disconnect` — include the diagnostic fields the payload actually carries
(e.g. `statusCode` / `errorCode` / `errorMessage` / `connectionClosed`,
whichever are present in this codebase's parsed message shape) in the log
line. This is the field that names keep-alive timeout vs invalid-clock vs
subscription-limit vs a clean close. Inspect the real payload shape in
the wire-message path and log what's there; do not invent field names.

### 5.4 — Do NOT log the high-frequency data ops

`mcm` (market change) and `ocm` (order change) fire on every price/position
tick; `heartbeat` fires on the heartbeat cadence. **None of these get a
log line** — logging them would flood the Terminal and bury the signal.
The single allowed exception: if a `heartbeat` or `mcm`/`ocm` is the thing
that flips state (e.g. clears a degraded flag), that *state change* is
logged per §5.2, but the routine tick itself is not. Transitions only.

## 6. Sequencing

5.1 (logger) → 5.2 (transition logging) → 5.3 (payload reason) → 5.4 is a
constraint that holds throughout. Then the test (§7), then the full-suite
baseline. One pass; no dependency that forces another order.

## 7. Empirical verification

- **Before:** `uv run pytest -q` — record the pass/fail count.
- **After:** `uv run pytest -q` — record it again; the only delta is the
  new test(s).
- **New test(s)** (fake/driven, no socket): drive a `SUBSCRIBED` state,
  then feed a `disconnect` (and/or a degraded `status`) message; assert
  (a) the state transition is logged at WARNING, (b) the log record
  carries the transition and any payload diagnostic field, and (c) a
  routine `mcm`/`ocm`/`heartbeat` produces **no** transition log line
  (the no-flood guard).
- **Quality gates on touched files:** `ruff check` clean; `uv run
  lint-imports` → 5 kept, 0 broken (DR-030 unchanged).
- **Dirty-list proof:** `git status --short` line count identical before
  and after.

## 8. Output spec

Single file: `dr029/2_4_betfair_streaming/streaming_drop_visibility_report.md`.
Adelaide-local timestamps. Sections:

1. What changed (the logger + the transition/payload logging; show the
   added lines).
2. No-flood proof (the data ops produce no transition lines).
3. Test baseline (before → after counts; the new test named).
4. Hard-limit adherence (the five non-negotiables in §9, each addressed).
5. What the operator will now see — the **success** shape (transitions
   to SUBSCRIBED) and, more importantly, the **drop** shape (a WARNING
   naming `SUBSCRIBED → RECONNECTING` plus the payload reason), as
   sample Terminal lines.
6. Findings + self-assessment.

Rough length 120–200 lines. The report contains **no** connection fix, no
keep-alive/clock work, no recommendation on the eventual fix — that is the
next operator-Claude session's call.

## 9. Hard limits — non-negotiable

1. **Observability only.** No change to state, control flow, timeouts,
   reconnect/back-off, cache, heartbeat handling, or any streaming
   behaviour. Log statements only.
2. **`placement.py` and the SUBSCRIBED interlock untouched.** Not in the
   edit set. The gate still refuses unless a genuine `SUBSCRIBED`.
3. **No live Betfair / credentials / network / socket.** Fake-driven
   tests only.
4. **No git writes; dirty list unchanged.** No duplication of
   `uvicorn.access` (do not add handlers to the root logger; this module
   reuses the existing named-namespace handler by propagation).
5. **No logging on `mcm` / `ocm` / `heartbeat` routine ticks.**
   Transitions only (§5.4).

Excluded and named: the keep-alive fix (S160 F3), the clock-sync fix
(S160 F5), the F4 on-screen live-data-loss warning, the in-memory
audit-sink durability gap (parking-lot), and any change to
`logging_setup.py`. None are in scope here.

## 10. What happens after Code's session

The next operator-Claude session triages
`streaming_drop_visibility_report.md` (green tests, no-flood proof, gate
untouched, dirty list unchanged). Then the operator re-runs
`BetHub.command` live and lets it sit until the stream drops — the
Terminal now **names the drop and its reason**. That named reason
(keep-alive timeout vs invalid-clock vs other) drives the scoping of the
actual connection-fix brief (Chat → Code). Code does not write that
brief; this run ends at the report.

## 11. Cross-references

- **Serves:** DR-029 §2.4 (Betfair Streaming spec) live validation.
- **Follows:** `streaming_visibility_brief.md` / `_report.md` (bring-up
  visibility), `cert_fix_report.md` (S161), S160
  `stream_transport_build_report.md` §4 (F3/F5).
- **DRs:** DR-021 (Adelaide anchors), DR-030 (module layout — unchanged),
  DR-031 (FastAPI/uvicorn logging interaction — the existing handler is
  reused, not modified).
- **Bet-safety hard rule:** preserved — the placement/streaming gate is
  not touched; this run only observes the streaming path.
