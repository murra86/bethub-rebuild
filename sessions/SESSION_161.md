# Session 161 — Live $5-lay validation: TLS cert fix shipped + triaged whole; streaming found not reaching SUBSCRIBED; visibility brief locked

**Opened:** 2026-06-18 11:53 ACST
**Closed:** 2026-06-18 13:42 ACST (~1h49m, single calendar day)
**Tool routing:** Claude Chat + Desktop Commander (orientation
reads, two brief drafts, cert-fix triage, three live-error
diagnoses, close). Code ran the cert fix out-of-session against
the locked brief; this session triaged it. A second Code brief
(streaming visibility) was locked but not yet executed.
**Governing DRs:** DR-021 (anchors), DR-029 §2.4 (Betfair
Streaming spec), DR-030 (v3 module layout), DR-031 (FastAPI/
uvicorn stack), DR-032 (Betfair canonical / auth).

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-18 11:53 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-18 13:42 ACST.

## Pre-flight checks (open)

Rebuild root clean: 12 governance `.md` + `openapi.json` +
`external_api_resources.md` + benign `.DS_Store`; no phantom
files. `.close_out_backups/` held `SESSION_161_opening_prompt.md`
(expected). Drift-check clean: `current_state.md` stamp (09:46,
S160 close) matched `SESSION_160.md` close; `v3_build_picture.md`
stamped at S160 close (Streaming-transport stream moved). Silent-
open ritual honoured. Same-workday open (~2h after S160 close) —
tight recap; build picture rendered (streams moved at S160 ⇒
render condition TRUE). Operator confirmed the S160 standing-
instructions re-upload was done (closed that pending action).

## Session shape

An open-then-live-validation triage session. Opened on the S160
hand-off with the operator about to perform the live $5 lay. The
validation surfaced three sequential live issues, each triaged off
the codebase (not guessed): (1) a TLS certificate failure that
blocked the stream entirely; (2) prices-endpoint 503s; (3) a
lay-placement 503. The first was fixed via a Code brief executed
and triaged whole mid-session. The second and third resolved into
a single root finding: the live streaming connection is not
reaching `SUBSCRIBED` on launch, and the app's own bring-up
diagnostics are being swallowed (bare-uvicorn launch, no logging
config). Session closed having locked a visibility brief to make
the cause show itself on the next live run.

Three live launches happened between turns: (a) cert-fail run
(SSL errors, ended); (b) first re-run (prices 200 then 503s on a
near-jump market); (c) full clean-startup run (market open
throughout, no SUBSCRIBED line, lay POST → 503).

## What was delivered

1. **Session opened (silent ritual).** Same-workday tight recap;
   build picture rendered (Streaming-transport had advanced to
   `awaiting-operator-validation` at S160). Operator flagged the
   updated `standing_instructions.md` was re-uploaded to the
   Project KB — pending S160 action closed.

2. **Cert-fix brief drafted + locked.**
   `dr029/2_4_betfair_streaming/cert_fix_brief.md` (241 lines, sha
   `58dccf11`). Surgical fix: the live streaming TLS context built
   a bare `ssl.create_default_context()` (zero trusted roots on
   this Mac — the stdlib default cert path does not exist), so the
   handshake to Betfair's stream endpoint failed
   `CERTIFICATE_VERIFY_FAILED`. Fix: pin certifi's bundle
   (`cafile=certifi.where()`). Grounded empirically before drafting
   (bare context → 0 CA roots; certifi context → 120). REST/reads
   were unaffected (httpx uses certifi) — only the new stdlib-
   asyncio stream used the bare context.

3. **Code confirm-back triaged → GO.** Code restated the change,
   the file list, and the three non-negotiables correctly, and
   flagged a real brief error: the brief named the target function
   `_default_connector` (a docstring phrase) but the actual symbol
   is `open_tls_connection`. Verified against the file (the `def`
   at line 149); approved editing the correct function and logging
   the discrepancy as a finding. Go issued.

4. **Cert fix triaged → WHOLE (verified independently off disk).**
   `cert_fix_report.md`. Confirmed in the live tree, not the chat
   summary: `import certifi` (line 58), a `_build_tls_context`
   helper (the §5.4 seam) returning `create_default_context(
   cafile=certifi.where())`, call site `context =
   _build_tls_context()`. `placement.py` untouched (not in the
   dirty list). Re-ran the **full suite myself**: 1002 → **1003
   passed, 0 failed**. certifi made a direct dependency. Static
   proof reproduced (bare = 0 CA, certifi = 120 CA). Two findings:
   F1 (brief naming slip — cosmetic, resolved), F2 (the helper
   seam — in-scope per §5.4). No git writes; dirty list unchanged
   apart from the four §5 files.

5. **Live-validation triage — the cert fix worked, then two
   503s.** Across the re-runs:
   - **Cert confirmed fixed** — no SSL errors; live prices flowed
     `200 OK`.
   - **Prices 503s** — traced the racing prices endpoint
     (`get_market_prices` → `get_live_market_prices` →
     `live_pricing.market_prices`). Routing rule: serve from the
     stream cache only when `SUBSCRIBED` + heartbeats current,
     else REST fallback. The 503 maps from a family of reasons
     (market-suspended / streaming-disconnected / auth-expired /
     rate-limited / api-unreachable), indistinguishable in the
     Terminal. First hypothesised near-jump market suspension.
   - **Lay 503** — `POST /api/v1/racing/lay` → 503. Traced to the
     **bet-safety gate** in `placement.py` (~L158–161):
     `place_bet` refuses when `streaming_status().state !=
     SUBSCRIBED`, returning `BETFAIR_STREAMING_DISCONNECTED`
     (connectivity-shaped → 503). The gate refused *before* any
     order to Betfair — **no bet placed.** The interlock proven
     under genuine live conditions.

6. **Root finding — stream not reaching SUBSCRIBED + swallowed
   diagnostics.** The full clean-startup Terminal showed the
   market open throughout (prices 200 before *and* after the lay —
   not a suspended market), **no `SUBSCRIBED` line, and no
   transport lines at all.** `ui/api/main.py`
   `_bring_up_live_streaming` logs the outcome (info on success,
   error on timeout/factory-missing), and the transport logs
   connect/auth/subscribe — but the launcher runs bare
   `uv run uvicorn …` with no logging config, so app-logger output
   surfaces only via Python's last-resort handler (WARNING+) and
   unreliably; INFO is dropped and even the bring-up ERROR did not
   show. **Mode-misconfig ruled out** — the launcher correctly
   exports `BETHUB_BETFAIR_MODE=live` (`config.py` defaults to
   `mock`; the launcher overrides). So the app is producing the
   diagnostic we need and it is being swallowed.

7. **Streaming-visibility brief drafted + locked.**
   `dr029/2_4_betfair_streaming/streaming_visibility_brief.md`
   (255 lines, sha `e4f50d76`). **Observability only** — surface
   `ui.api.main` + the `clients.betfair_client.v1` namespace at
   INFO in the Terminal (without duplicating uvicorn's access
   logs), and enrich the bring-up failure line to report the
   actual `streaming_status().state` reached (how far it got).
   No streaming-behaviour change, gate untouched, no live Betfair,
   no git writes. This is the diagnostic foundation the operator's
   F4 (on-screen live-data-loss warning) later builds on; the F4
   UI work stays excluded here. Code confirm-back prompt provided.

## Standing-instruction adherence

- **Cat 1 — silent open ritual: HONOURED.** No step narration;
  single combined orientation; same-workday tightness.
- **Cat 1 — build-picture conditional render: HONOURED** (streams
  moved at S160 ⇒ rendered at open).
- **Cat 1 — inventory-first on technical reports: HONOURED.** Cert
  report triaged off disk; findings classified (F1/F2 cosmetic/
  in-scope, surfaced as one plain line).
- **Cat 1 — short, plain, decision-first: HONOURED.** Each live
  error answered with the plain-language read + the one call/
  question; bet-safety reassurance led every 503 explanation.
- **Cat 1 — narrow-wrap review blocks / paste prompts: HONOURED**
  (both Code prompts fenced + hard-wrapped).
- **Cat 3 — verify empirically: HONOURED, heavily.** Re-ran the
  full suite myself (1003); inspected the actual cert edit, git
  state, and `placement.py` directly; traced every 503 through the
  code; ruled out mode-misconfig by reading `config.py` + the
  launcher — no guessing.
- **Cat 3 — create_file banned / verify writes: HONOURED.** Both
  briefs written via Desktop Commander; verified via wc / sha /
  section grep.
- **Cat 3 — chunked writes: APPLIED** (brief + record in ≤~30-line
  chunks).
- **Cat 5 — make software calls, don't punt: HONOURED.** Cert-fix
  approach decided (code fix over Mac workaround); visibility
  mechanism delegated to Code with a guardrail; scope cuts
  (Terminal-only vs F4 UI) made and named.
- **brief-drafting skill — APPLIED twice** (cert fix; visibility),
  surgical-fix + observability shapes; calls surfaced at hand-off.
- **Bet-safety hard rule — CLEAN + PROVEN LIVE.** No bet placed;
  the gate refused the lay under real conditions; `placement.py`
  untouched across both Code briefs.

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in S161:**
- Cert-fix brief + Code execution — triaged WHOLE; suite 1003. ✅
- TLS certificate handshake failure — fixed (certifi bundle). ✅
- S160 `standing_instructions.md` re-upload to Project KB —
  operator confirmed done. ✅

**New / promoted for S162:**
- **Streaming-visibility brief → Code** (locked, awaiting out-of-
  session execution; confirm-back prompt issued).
- **Stream not reaching SUBSCRIBED on launch** — the live blocker;
  cause to be named by the next live run once visibility lands.

**Carry-forward sensitivity flags:**
- **Bet-safety — CLEAN + proven live.** Preserve at every future
  touch of the placement/streaming path.
- **Local-MCP-bridge — WATCH.** Multi-chunk writes this session
  clean. Keep watching.

## Session close state

- Rebuild root: clean — 12 governance `.md` + `openapi.json` +
  `external_api_resources.md` + benign `.DS_Store`. No phantom
  files. New artefacts live under `dr029/2_4_betfair_streaming/`
  (`cert_fix_brief.md`, `cert_fix_report.md`,
  `streaming_visibility_brief.md`).
- `current_state.md`: rotated to S161 close.
- `v3_build_picture.md`: updated — Streaming-transport next-
  milestone moved from "operator $5 lay" to "stream not reaching
  SUBSCRIBED; visibility brief → Code → name the cause → fix";
  cert-fix sub-step recorded as done.
- `standing_instructions.md`: **not edited** this session.
- `.close_out_backups/`: `SESSION_162_opening_prompt.md` written;
  S161 prompt removed.
- `sessions/`: `SESSION_161.md` added.
- **v3 tree (bethub-v3):** carries the cert fix in the dirty tree
  (certifi import + `_build_tls_context` + the regression test in
  `_stream_transport.py` / `test_stream_transport.py`; `certifi`
  direct in `pyproject.toml` + `uv.lock`). Still fully uncommitted
  by design (optional-commit parking-lot item stands).

## Forward routing — confirmed with operator

Operator confirmed: close S161, continue next session. **S162
opens on the streaming-visibility work.** Sequence: (1) operator
hands `streaming_visibility_brief.md` to Code out-of-session; (2)
S162 triages Code's `streaming_visibility_report.md` (green tests,
no duplicated access logs, gate untouched); (3) operator re-runs
`BetHub.command` live — the Terminal now prints the bring-up story
and **names why the stream will not reach SUBSCRIBED**; (4) S162
(or S163) triages that named cause and scopes the actual
connection fix (Chat → Code). The F3 (`keepAlive`) / F5
(`INVALID_CLOCK`) / F4 (on-screen live-data-loss warning)
hardening brief stays sequenced **after** the lay proves out.
