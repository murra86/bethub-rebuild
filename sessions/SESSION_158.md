# Session 158 — Desktop launcher built + open/close process finalised

**Opened:** 2026-06-17 19:12 ACST
**Closed:** 2026-06-17 21:13 ACST (~2 hours, single calendar day)
**Tool routing:** Claude Chat + Desktop Commander (report triage,
launcher build/test). The serve-frontend source change was executed
out-of-session by Claude Code (prior), triaged here.
**Governing DRs:** DR-021 (anchors), DR-029 §5.6 (same-origin deploy
shape), DR-030 (v3 layout — launcher at repo root, serving inside
`ui/`), DR-031 (FastAPI/uvicorn/Vite), DR-032 (Betfair canonical /
auto-login).

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-17 19:12 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-17 21:13 ACST.

## Pre-flight checks (open)

Root clean (13 governance `.md` + `openapi.json` +
`external_api_resources.md` + benign `.DS_Store`); no phantom files.
Drift-check clean: `current_state.md` stamp (19:02, S157 close)
matched `SESSION_157.md` close; build picture stamped at S157 close
(launch/packaging stream added). **Anomaly surfaced at open:**
`dr029/launch/serve_frontend_report.md` was absent — Code had not yet
run the brief, so the S158 primary (triage) could not start until the
operator dispatched Code.

## Session shape

Three phases. (1) Triaged Code's brief-confirmation (Flow 3) and
advised go. (2) Triaged Code's completed serve-frontend report —
clean. (3) Built and tested the desktop launcher in the `bethub-v3`
repo, then finalised the open/close UX in response to two operator
questions (Terminal-window lifecycle; overnight-running safety). A
single focused deliverable — the launcher — bracketed by the report
triage that unblocked it.

## What was delivered

1. **Serve-frontend confirmation triaged → go.** Code read the brief
   and confirmed back. Flagged a path wobble (brief lives in the
   planning tree `bethub-rebuild`; code lives in `bethub-v3`) and
   resolved it read-only — `ui/api/main.py` present in `bethub-v3`
   per §4. Confirmation was faithful: optional helper in-scope, the
   API-404-not-`index.html` correctness boundary surfaced unprompted,
   bet-safety fenced (mock only). Advised proceed.

2. **Serve-frontend report triaged → clean.**
   `dr029/launch/serve_frontend_report.md` (173 lines). pytest
   983→991 (+8, 0 fail), vitest 90→90, tsc clean, eslint 7→7
   (pre-existing), lint-imports unchanged. Single-process curl proof
   on :8000 (page + API on one port, port freed on stop). Key
   boundary held: unmatched `/api/*` returns JSON 404, never
   `index.html`, even under an HTML Accept header — asserted by test
   and re-proven by curl. Same-origin baking confirmed empirically
   (no `localhost:8000` in `dist/assets`). No deviations, no git ops,
   mock-only. **Closes the serve-frontend brief.**

3. **Desktop launcher built —**
   `/Users/tim/Desktop/Projects/bethub-v3/BetHub.command`. A
   double-click `.command` (opens in Terminal so status is visible —
   deliberate, given v2's silent-failure history). Behaviour: `cd`
   repo root → clear any stale process on the pinned port → build the
   frontend only if `ui/web/dist/index.html` is missing → start one
   `uv run uvicorn ui.api.main:app` on **port 8787**, `MODE=live` by
   default (exports `BETHUB_BETFAIR_MODE=live` +
   `BETHUB_BETFAIR_CREDENTIALS_PATH` → the secrets file) → poll
   `/api/health` (40s budget, bail if uvicorn dies) → `open` the
   browser on 200 → hold the foreground → on stop, clean shutdown
   that frees the port. Test overrides: `BETHUB_BETFAIR_MODE=mock`,
   `BETHUB_LAUNCH_NO_BROWSER=1`, `BETHUB_LAUNCH_PORT`.

4. **Launcher tested (mock) — all mechanics green.** Pre-seeded
   stale port cleared; health 200 (~1s); page served at `/`;
   `/api/nope`→404; clean shutdown freed the port on SIGTERM.

5. **Open/close UX finalised (three hardenings, each tested).**
   (a) A deliberate stop now exits **code 0** while a real error
   keeps its non-zero code (FATAL paths preserved), so a tidy
   Terminal auto-closes on clean exit but stays open to show errors.
   (b) **Relaunch-race hardening** — `_shutdown` reaps only the
   listener PIDs *this* instance owns (`OWNED_PORT_PIDS`), so an
   orphaned old window cannot clobber a freshly-relaunched instance
   (tested: A leftover + B relaunch on the same port → B stays
   healthy, A exits clean, port frees on B stop). (c) De-duplicated
   the shutdown message (trap disarms itself first). Terminal-setting
   guidance given (close-on-clean-exit + prompt-before-closing);
   **operator chose to leave "prompt before closing" ON** as a safety
   check.

6. **Overnight-running question answered (verified against
   `clients/betfair_client/v1/_auth_betfair.py`).** Auto-login is
   **lazy, not timer-driven**: `session_token()` re-mints only when
   called AND the cached token is >3h old (`DEFAULT_TOKEN_MAX_AGE`,
   refresh at 3h against a ~4h Betfair TTL). Idle overnight ⇒ **zero**
   Betfair login calls; under steady use ≤1 re-login per ~3h. Throttle
   confirmed: escalating cool-off 30m→1h→2h→4h refusing attempts
   during each window, hard-kill at 5 consecutive failures, no
   auto-recovery, any single success fully resets. Conclusion:
   leaving it running overnight is harmless on all three axes —
   next-day launch (port self-heals + relaunch hardened), data (an
   idle server does not write), throttle (idle = no calls; failures
   back off and cannot recreate the 48h lockout).

## Operator action this session

The operator **double-clicked the launcher live** ("it works",
browser opened). Note: a browser-open only proves the server started
and served the page (health needs no auth); because the live login is
lazy, whether live **prices** loaded end-to-end is **unconfirmed** —
that is the S159 confirmation. No bet placed; bet-safety hard rule
CLEAN.

## Standing-instruction adherence

- **Cat 1 — silent open ritual: MISS (recurring).** S158 open again
  carried step-style headers in operator-facing text ("Step 1 —",
  "Step 2 —"), the S114/S157 pattern. Third recurrence. Carry forward
  firmly: S159 open must run **genuinely silent** — tool calls only,
  no step narration; the sole operator-facing output is the combined
  orientation plus any anomaly.
- **Cat 1 — build-picture conditional render: HONOURED.** Render
  condition was TRUE at S158 open (launch/packaging moved at S157);
  the build picture was rendered inline at open.
- **Cat — tool-routing recommendations: HONOURED.** Launcher → Chat +
  Desktop Commander (stated); live run + $5 lay → operator-side
  (stated).
- **Cat — surface decisions, handle detail autonomously: HONOURED.**
  Port / launcher form / live-default surfaced as brief operator
  calls; shell internals kept inside the artefact.
- **Cat — bet-safety hard rule: CLEAN.** Launcher mechanics tested
  mock-only; the operator's live launch placed no order.
- **Cat 2 — opening prompt at close: HONOURED** (produced for S159).
- **Cat — DB read discipline / narrow-wrap review blocks:** N/A this
  session.

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in S158:**
- Serve-frontend brief — report triaged clean. ✅
- Build + test the desktop launcher — built, mock-tested, hardened. ✅

**New / promoted for S159:**
- **Confirm live data flows through the launched app** — the first
  end-to-end live auto-login proof (live prices visible on the racing
  page via the launcher). S159 primary.
- Then operator-side **$5 lay validation**, then the **is_self
  coordinated-removal brief**.

## Session close state

- Rebuild root: clean — 13 governance `.md` + `openapi.json` +
  `external_api_resources.md` + benign `.DS_Store`. No phantom files.
  (The launcher and all code work live in the `bethub-v3` repo, not
  in this planning tree.)
- `current_state.md`: rotated to S158 close.
- `v3_build_picture.md`: updated — launch/packaging stream moved
  (serve-frontend done; launcher built + mock-tested).
- `standing_instructions.md`: untouched (no instruction changes this
  session).
- `.close_out_backups/`: `SESSION_159_opening_prompt.md` written;
  S158 prompt removed.
- `sessions/`: `SESSION_158.md` added.

## Forward routing — confirmed with operator

Operator said "close" after being asked whether to do the live run
now or park it ⇒ **parked**. S159 (operator + Chat) confirms v3 shows
**live prices** through the launched app (proving the lazy auto-login
works end-to-end inside the launcher), then proceeds to the
operator-side **$5 lay validation**, then the **is_self
coordinated-removal brief**. The launcher itself is built, tested,
hardened, and in the operator's hands.
