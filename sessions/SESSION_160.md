# Session 160 — Streaming-transport build: confirm-back triaged (go), build report triaged (whole for the $5 lay); live-data-loss warning requirement locked

**Opened:** 2026-06-18 08:50 ACST
**Closed:** 2026-06-18 09:46 ACST (~56m, single calendar day)
**Tool routing:** Claude Chat + Desktop Commander (orientation
reads, brief/report triage). The build itself ran out-of-session
in Claude Code against the locked brief; this session triaged
Code's confirm-back and Code's build report.
**Governing DRs:** DR-021 (anchors), DR-029 §2.4 (Betfair
Streaming spec — the build's authority), DR-031 (FastAPI/uvicorn
stack), DR-032 (Betfair canonical / auth), DR-030 (v3 module
layout).

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-18 08:50 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-18 09:46 ACST.

## Pre-flight checks (open)

Root clean (12 governance `.md` incl. `v3_build_picture.md` now
in active use + `openapi.json` + `external_api_resources.md` +
benign `.DS_Store`); no phantom files. `.close_out_backups/` held
`SESSION_160_opening_prompt.md` (expected). Drift-check clean:
`current_state.md` stamp (08:39, S159 close) matched
`SESSION_159.md` close; `v3_build_picture.md` stamped at S159
close (Streaming-transport stream surfaced). Silent-open ritual
honoured. Same-workday open (11 min after S159 close) — tight
recap, full build-picture/open-items re-render skipped as
just-reviewed ritual noise.

## Session shape

A two-stage triage session. Code completed the Streaming-transport
build out-of-session faster than expected, so both Flow-3 stages
landed in S160: (1) triaged Code's STEP-2 confirm-back against the
locked brief and advised **go**; (2) triaged Code's build report
once the build completed (~22 min later). The build is **whole for
the $5 lay**. Operator added one forward requirement — an
on-screen live-data-loss / reconnection warning — which maps onto
Code's deferred F4 and folds into the hardening follow-up brief.
Operator will perform the live $5 lay validation between sessions.

## What was delivered

1. **Code confirm-back triaged → GO (Flow 3 stage 1).** Sanity-
   checked Code's STEP-2 confirmation against the locked brief
   (`stream_transport_build_brief.md`, sha 864181fa). All three
   load-bearing limits confirmed held: no live Betfair (fake
   socket only), SUBSCRIBED interlock preserved (genuine acks
   only; `placement.py` untouched), no git writes. Named anchors
   correct. The five spec-vs-brief discrepancies Code surfaced
   (async-task vs I/O-thread; stdlib asyncio TLS vs
   betfairlightweight listener; holding `initialClk`/`clk` in the
   transport; hardcoded production endpoint; racing-first
   subscriptions) were all correctly resolved in Code's own lane —
   none touch bet safety or need an operator call. Issued the go
   with each call explicitly approved + the three non-negotiables
   restated; `__init__.py` re-export guidance given.

2. **Code build report triaged → BUILD WHOLE (Flow 3 stage 2).**
   Read `stream_transport_build_report.md` (173 lines) off disk,
   not the chat summary. Outcome: core bring-up shipped coherent
   and complete (connect → auth → subscribe → read loop → genuine
   `SUBSCRIBED` → clean teardown), plus most of §5.5 (drop
   detection both ways, back-off resubscribe with held tokens,
   one-shot `INVALID_SESSION` recovery). **Bet-safety preserved
   and now explicitly tested** — a dedicated test asserts the gate
   stays closed (client stays `AUTHENTICATING`) without a genuine
   SUCCESS status. Tests 991 → 1002 passed, 0 failed (+11, all
   fake-socket; no network/login/credentials). ruff green, mypy
   clean on Code's modules (lone residual pre-existing in
   untouched `balance_derivation.py`), import-linter 5/5 KEPT
   (DR-030 layering intact). No git writes; dirty list changed by
   exactly two new anchor files. Edits stayed within named
   anchors (`__init__.py` re-export touched as pre-approved at
   confirm-back).

3. **Five named findings classified (inventory-first per Cat 1).**
   None block the $5 lay; classification surfaced to operator in
   plain language:
   - **F1 — test runner is `uv run pytest`, not `python3`**
     (operational/tooling). The `bethub-v3` repo is a `uv` project
     (Python 3.12 venv); system `python3` is 3.11 and lacks
     `httpx`, so `python3 -m pytest` fails at collection. **Durable
     tooling fact — captured in `standing_instructions.md` Cat 3
     this close.** Does NOT change the existing rule about querying
     v2's `bethub.db` with `start_process` + python3 (that's a
     separate context and still correct).
   - **F2 — sports eventTypeIds unverified** — parked; sports sub
     is off by default, off the racing-lay path, sports in-play is
     regulator-blocked. Verify at sports-pages build (W18).
   - **F3 — `keepAlive` scheduling not built** — proactive stay-
     awake ping deferred; the 12-hour token window covers a single
     launch + lay, and `INVALID_SESSION` self-heal is built so a
     mid-session expiry recovers on the next message. Wants wiring
     before sustained all-day live use.
   - **F4 — sustained-failure operator-visibility tier partial** —
     reconnect itself is correct and unbounded; the explicit loud
     "it keeps failing / unavailable" operator alert is not wired.
     **This is exactly the operator's new live-data-loss warning
     requirement (item 4).**
   - **F5 — `INVALID_CLOCK` fresh-image fall-back** relies on
     existing dispatch — low risk for a single launch; hardening
     follow-up.

4. **NEW operator requirement — live-data-loss / reconnection
   warning (LOCKED for the hardening brief).** Operator wants a
   visible on-screen warning in the tool whenever live data is not
   being received and the reconnection protocol is running — so he
   is never looking at stale prices believing they are live. Maps
   directly onto F4 (the deferred operator-visibility tier). Folds
   into the F3/F4/F5 hardening follow-up brief, which is scoped
   **after** the live $5 lay proves SUBSCRIBED — no point hardening
   before the core is proven live.

5. **Routing call — build is whole; harden after the lay.** Per
   brief §10, decided the build does not need a §5.5 hardening
   follow-up before proceeding. Next step is the operator-side
   live $5 lay validation; the F3/F4/F5 + warning hardening brief
   is sequenced after that lands.

## Standing-instruction adherence

- **Cat 1 — silent open ritual: HONOURED.** No step-narration;
  single combined orientation. Same-workday tightness applied.
- **Cat 1 — inventory-first on technical reports: HONOURED.**
  Every finding inventoried + classified by operational/bet-safety
  impact before surfacing; operator-relevant ones in plain
  gambling language, technical detail handled as Claude's
  territory.
- **Cat 1 — build-picture / open-items conditional render:**
  render conditions technically TRUE but suppressed as ritual
  noise (same-workday, 11 min after S159 close — operator just
  reviewed both). Judgment call, operator-serving.
- **Cat 5 — surface decisions, handle detail autonomously:
  HONOURED.** The go/no-go and build-whole calls surfaced; the
  five spec discrepancies + ruff/mypy/import detail handled
  silently as Claude's territory.
- **Cat 5 — make software calls, don't punt: HONOURED.** Go
  issued with each Code call explicitly approved; build-whole +
  harden-after-lay routing decided, not punted.
- **Cat — bet-safety hard rule: CLEAN + STRENGTHENED.** No bet
  placed this session; the interlock is now explicitly test-
  covered (gate stays shut without a genuine connection).
- **Cat 3 — verify empirically: HONOURED.** Report triaged off
  the file on disk, not Code's chat summary.
- **Cat 1 — narrow-wrap review blocks: HONOURED** (Code go-
  message rendered hard-wrapped).
- **Cat 3 — tooling discipline edit: APPLIED** (F1 `uv run`
  note added to `standing_instructions.md` this close).

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in S160:**
- Streaming-transport build brief — Code confirm-back triaged,
  go issued. ✅
- Streaming-transport build — Code report triaged; build whole
  for the $5 lay. ✅

**New / promoted for S161:**
- **Operator-side live $5 lay validation** — now the live front
  edge. Launch `BetHub.command` live, watch for `Betfair
  streaming reached SUBSCRIBED at startup`, place the $5 lay,
  check on Betfair. Steps in build report §5. S161 picks up the
  result.
- **Streaming hardening follow-up brief (F3/F4/F5 + live-data-
  loss warning)** — scoped after the lay validation lands. The
  warning requirement (item 4) is the load-bearing addition;
  F3 (`keepAlive`) and F5 (`INVALID_CLOCK`) ride along.

**Carry-forward (UI tune-ups — operator-flagged S159):**
- Quick-lay single-account auto-pick; quick-lay error-reason
  surfacing; dedicated UI tune-up session. (The live-data-loss
  warning is connection-health, distinct from the lay-attempt
  error surfacing.)

**Carry-forward sensitivity flags:**
- **Bet-safety — CLEAN + now test-covered.** Preserve at every
  future touch of the placement/streaming path.
- **Local-MCP-bridge — WATCH.** S160 ran multi-chunk close writes
  without bridge issues. Keep watching.

**Carry-forward (long-standing):**
- is_self coordinated-removal brief (after validation confirms
  live); optional v3 tree commit (still uncommitted); on-screen
  "auto-login disabled" banner; W16 cutover scoping; runbook
  patches (W17.1 §3); F4 liability-cap; F6 cross-AAB guard;
  calculator rethink; greyhound op-constraint verify;
  `cascaded_at_settlement_state` enum (W8); §2.4 Fix 4 cadence;
  Betfair API tier (awaiting BetWatch); pre-existing frontend lint
  errors; vite-8 dev Fast-Refresh.

## Session close state

- Rebuild root: clean — 12 governance `.md` + `openapi.json` +
  `external_api_resources.md` + benign `.DS_Store`. No phantom
  files. The build report lives under `dr029/2_4_betfair_streaming/`.
- `current_state.md`: rotated to S160 close.
- `v3_build_picture.md`: updated — Streaming-transport stream
  advanced `awaiting-code-execution` → `awaiting-operator-
  validation` (built + triaged whole; F3/F4/F5 + warning named as
  the hardening follow-up); Launch/packaging next-milestone
  updated to point at the live lay.
- `standing_instructions.md`: **edited** — Cat 3 `uv run pytest`
  tooling note added (F1). Needs re-upload to the bethub-rebuild
  Project knowledge base (operator-side, between sessions).
- `.close_out_backups/`: `SESSION_161_opening_prompt.md` written;
  S160 prompt removed.
- `sessions/`: `SESSION_160.md` added.

## Forward routing — confirmed with operator

Operator confirmed: close S160, perform the live $5 lay
validation between sessions. **S161 opens on the result of that
validation** — if SUBSCRIBED reached + lay clears, the arc's
core is proven live and S161 scopes the F3/F4/F5 + live-data-loss
warning hardening brief (Chat → Code). If the live bring-up
misbehaves, S161 triages from the Terminal output (the login
throttle protects against a repeat-fail lockout meanwhile). The
streaming hardening brief is sequenced after the lay, not before.
