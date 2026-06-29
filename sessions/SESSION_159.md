# Session 159 — Live-data confirmed through launcher; lay 503 traced; Streaming-transport build brief locked

**Opened:** 2026-06-18 07:22 ACST
**Closed:** 2026-06-18 08:39 ACST (~1h20m, single calendar day)
**Tool routing:** Claude Chat + Desktop Commander (live-server
probes, code-anchor grounding, brief authoring). The build itself
is dispatched to Claude Code out-of-session against the locked
brief.
**Governing DRs:** DR-021 (anchors), DR-029 §2.4 (Betfair
Streaming spec — the build's authority), DR-031 (FastAPI/uvicorn
stack), DR-032 (Betfair canonical / auth), DR-030 (v3 module
layout).

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-18 07:22 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-18 08:39 ACST.

## Pre-flight checks (open)

Root clean (13 governance `.md` + `openapi.json` +
`external_api_resources.md` + benign `.DS_Store`); no phantom
files. `.close_out_backups/` held only `SESSION_159_opening_prompt.md`
(expected). Drift-check clean: `current_state.md` stamp (21:13,
S158 close) matched `SESSION_158.md` close; `v3_build_picture.md`
stamped at S158 close (launch/packaging moved). Silent-open ritual
honoured this session (the recurring S114/S157/S158 step-narration
miss did **not** recur).

## Session shape

Operator opened to confirm live prices through the launcher. The
session ran in three moves: (1) an accounts-setup wobble that
self-resolved on relaunch (plus a flagged single-account
auto-pick friction in the quick-lay modal); (2) the operator
attempted the `$5` lay and hit `Error: API 503 on POST
/api/v1/racing/lay` — triaged live to root cause; (3) on the
operator's "full build" call, a locked Code brief was authored
to build the missing Betfair Streaming transport. The day's
primary objective (live data through the launcher) was confirmed
in passing during the 503 triage.

## What was delivered

1. **Live data through the launcher — CONFIRMED (primary
   objective).** A direct live read against the running launcher
   (`GET /api/v1/racing/races` on port 8787) returned
   `"status":"fresh"` with real AU markets (Shepparton greyhounds,
   real market IDs, live `total_matched`). Proves the lazy
   auto-login mints a Betfair token and the live REST path returns
   market data end-to-end inside the launched app. The prices the
   operator saw in the quick-lay modal were real.

2. **Lay `503` traced to root cause — Streaming transport
   unbuilt.** The quick-lay `POST /api/v1/racing/lay` returned
   `503`. Confirmed in code across three anchors: the lay route
   maps connectivity-shaped write failures to `503`
   (`racing.py`); the order-placement path refuses while the
   Streaming connection ≠ `SUBSCRIBED`
   (`placement.py:158-159`, reason `betfair_streaming_disconnected`);
   and the Streaming connection is a **state-machine shell only** —
   `streaming.py.connect()` is a pure state transition, the live
   branch of `build_streaming_client` (`composition.py`) hands back
   a `DISCONNECTED` client, and the app `lifespan` hook
   (`main.py:33`) is empty. So the `503` is the system correctly
   refusing to place a bet it cannot watch. **No bet placed —
   bet-safety hard rule CLEAN.**

3. **Build-vs-missing split clarified.** W3 already shipped the
   wire-format **parser** (`_stream_parser.py` §5.1) and W2 the
   dispatch (`streaming.py._handle_message`). Missing is purely
   the **transport** beneath them: the TCP/TLS socket, auth
   handshake, subscriptions, read loop, and reconnection — plus
   the launch wiring. The seam is named by `_stream_parser.py`'s
   own docstring.

4. **Streaming-transport build brief — LOCKED + dispatched.**
   `dr029/2_4_betfair_streaming/stream_transport_build_brief.md`
   (395 lines, 17,767 bytes, sha256 `864181fa26e625b6`).
   Commissions Code to build the live Betfair Streaming transport
   (§2.4 §3–§7) — real TCP/TLS socket, auth handshake, market +
   order subscriptions, read loop reusing the existing parser,
   reconnection — and wire it into the FastAPI `lifespan` so live
   mode brings the connection to `SUBSCRIBED`. Eleven sections,
   surgical-build shape. **Operator chose full build in one go**
   (vs minimal-but-real first). Key encoded calls: bring-up lives
   in the `lifespan` startup hook (not the constructor); **Code
   makes NO live Betfair connection** — fake-socket tests only,
   live proof is operator-side (protects the login throttle); the
   `SUBSCRIBED` interlock is preserved, never weakened or
   synthesised in live mode (`placement.py` untouched); mock mode
   unchanged + default; single bounded session with core+findings
   fallback. Operator approved ("all sounds good/safe — go").

5. **Code dispatch prompt provided.** A complete copy-paste Code
   opening prompt was rendered for the operator (read brief +
   §3 pre-reads → confirm scope/anchors/hard-limits back → STOP
   for go before editing). Verbatim copy archived in the Forward
   routing section below for recoverability.

## Standing-instruction adherence

- **Cat 1 — silent open ritual: HONOURED.** No step-narration in
  operator-facing text; the recurring S114/S157/S158 miss did not
  recur. Single combined orientation delivered.
- **Cat 1 — build-picture conditional render: HONOURED.** Render
  condition TRUE at open (launch/packaging moved at S158); table
  rendered inline.
- **Cat 1 — open-items delta: HONOURED** (two closed / one new
  surfaced).
- **Cat 5 — surface decisions, handle detail autonomously:
  HONOURED.** The streaming-transport finding's *size change* and
  the full-vs-minimal call were surfaced as operator decisions;
  all socket/spec detail kept inside the brief.
- **Cat 5 — make software calls, don't punt: HONOURED with
  surfacing.** The "build lives in lifespan hook," "reuse W3
  parser," and "fake-socket tests" calls were made by Claude; the
  bet-safety-adjacent and budget-shaped calls were surfaced.
- **Cat — bet-safety hard rule: CLEAN.** The 503 was a refusal;
  no order placed. The brief forbids Code live-Betfair access and
  preserves the placement interlock.
- **Cat 3 — verify empirically: HONOURED.** Root cause confirmed
  by live-server probe + code reads, not memory.
- **Cat 1 — narrow-wrap review blocks: HONOURED** (Code prompt
  rendered hard-wrapped).
- **Brief-drafting skill: HONOURED** (grounded anchors pre-draft;
  surfaced the calls; locked on operator approval; fingerprint
  captured).

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in S159:**
- Confirm live data flows through the launched app — CONFIRMED
  (live reads fresh through the launcher). ✅
- Accounts-setup operator-side registration — confirmed working
  (self-resolved on relaunch). ✅

**New / promoted for S160:**
- **Streaming-transport build brief — dispatched to Code,
  awaiting Code's confirm-back.** S160 triages the confirmation
  (advise go), then later triages the build report.

**New parking-lot (UI tune-ups — operator-flagged):**
- **Quick-lay modal single-account friction** — when exactly one
  Betfair account-at-book exists, auto-pick it; show the picker
  only when 2+ exist. Stake/price confirm step untouched. Code
  job; folds into the UI tune-up pass.
- **Quick-lay modal error surfacing** — the modal showed only
  "API 503"; it should surface the underlying reason text (e.g.
  "streaming disconnected") so failures are legible. UI tune-up.
- **Dedicated UI tune-up session** — operator wants a session
  that dwells on each interface (accounts, racing, modal, …) to
  tighten each in turn; operator will keep flagging items as they
  surface.

**Carry-forward (unchanged from S158):**
- Operator-side `$5` lay validation — now sequenced *after* the
  streaming-transport build lands + operator live-launch proves
  `SUBSCRIBED`.
- is_self coordinated-removal brief — after validation confirms
  v3 live.
- Optional: commit the v3 tree (still fully uncommitted).
- On-screen "auto-login disabled" banner; W16 cutover scoping;
  runbook patches (W17.1 §3); F4 liability-cap; F6 cross-AAB
  guard; calculator rethink; greyhound op-constraint verify;
  `cascaded_at_settlement_state` enum (W8); §2.4 Fix 4 cadence;
  Betfair API tier (awaiting BetWatch); pre-existing frontend
  lint errors; vite-8 dev Fast-Refresh (dev-only, sidestepped).

## Session close state

- Rebuild root: clean — 13 governance `.md` + `openapi.json` +
  `external_api_resources.md` + benign `.DS_Store`. No phantom
  files. The new brief lives under `dr029/2_4_betfair_streaming/`.
- `current_state.md`: rotated to S159 close.
- `v3_build_picture.md`: updated — new **Streaming transport**
  stream surfaced (`awaiting-code-execution`); launch/packaging
  live-data milestone met; accounts-setup milestone updated.
- `standing_instructions.md`: untouched (no instruction changes).
- `.close_out_backups/`: `SESSION_160_opening_prompt.md` written;
  S159 prompt removed.
- `sessions/`: `SESSION_159.md` added.

## Forward routing — confirmed with operator

Operator locked the streaming-transport brief and asked for the
Code dispatch prompt, then to close. **S160 (operator + Chat)
triages Code's confirm-back on the brief** (Flow 3 — Claude
sanity-checks Code's confirmation, advises go), then Code builds
out-of-session and produces
`dr029/2_4_betfair_streaming/stream_transport_build_report.md`;
a later Chat session triages that report. Operator-side `$5` lay
validation follows once the build lands and a live launch proves
the connection reaches `SUBSCRIBED`.

**Code dispatch prompt (verbatim, for recoverability):**

```text
BetHub v3 — Claude Code build session.

Working repo: /Users/tim/Desktop/Projects/bethub-v3
(branch: main; the working tree is dirty / largely
uncommitted — that is EXPECTED, it's the accumulated v3
build, not drift).

You are commissioned against a LOCKED brief — it is the
contract, execute as-written:
/Users/tim/Desktop/Projects/bethub-rebuild/dr029/
2_4_betfair_streaming/stream_transport_build_brief.md

The job: build the live Betfair Streaming transport layer
(§2.4 §3–§7) — real TCP/TLS socket, auth handshake, market
+ order subscriptions, read loop, reconnection — and wire
it into app startup so live mode brings the connection to
SUBSCRIBED and the order-placement interlock passes for
real. Reuse the existing W3 parser and W2 dispatch; build
only the transport beneath them.

STEP 1 — Read BEFORE any edit, in order:
  1. The locked brief above.
  2. Its §3 required pre-reads:
     - dr029/2_4_betfair_streaming/2_4_betfair_streaming.md
       (the LOCKED §2.4 spec — the authority)
     - dr029/2_4_betfair_streaming/
       betfair_stream_api_reference.md
     - clients/betfair_client/v1/streaming.py (in full)
     - clients/betfair_client/v1/_stream_parser.py
  NOTE: the two spec docs live in the bethub-rebuild
  planning tree, not in bethub-v3 — read them read-only
  from there.

STEP 2 — Confirm back to me BEFORE building:
  - The job in your own words: what you're building, what
    you're reusing, what you are NOT touching.
  - The named edit anchors (§5) you'll change — and that
    you'll touch nothing else.
  - The hard limits you'll hold (§9), especially:
      * NO live Betfair connection / login / credentials
        use this session — fake-socket tests only.
      * NO git operations of any kind.
      * Do NOT weaken, bypass, or synthesise the SUBSCRIBED
        interlock in live mode; placement.py untouched.
      * Mock mode unchanged and remains the default.
      * Single bounded session — if it won't fit, ship the
        core bring-up coherent + flag the rest as findings.
  - Any discrepancy between the brief and the §2.4 spec
    (the spec wins — surface it).

Then STOP and wait for my go. Do not edit any file until I
confirm.

Output when built (after go):
dr029/2_4_betfair_streaming/stream_transport_build_report.md
per §8. Adelaide local timestamps (DR-021).
```
