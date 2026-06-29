# Session 162 — Live $5-lay root cause found: stream ruled out, the 503 driven to a named Betfair error (customerRef > 32-char limit). Three diagnostic briefs executed + triaged clean.

**Opened:** 2026-06-18 13:53 ACST
**Closed:** 2026-06-18 15:43 ACST (~1h50m, single calendar day)
**Tool routing:** Claude Chat + Desktop Commander (orientation
reads, three brief drafts, three report triages each with an
independent `uv run pytest` re-run, deep read-only code tracing
across the placement/streaming/transport/translation path, close).
Code executed the three briefs out-of-session against the locked
specs.
**Governing DRs:** DR-021 (anchors), DR-029 §2.4 (Betfair
Streaming spec), DR-030 (module layout), DR-031 (FastAPI/uvicorn
logging), DR-032 (Betfair canonical / auto-login).

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-18 13:53 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-18 15:43 ACST.

## Pre-flight checks (open)

Root clean: 12 governance `.md` + `openapi.json` +
`external_api_resources.md` + benign `.DS_Store`; no phantom
files. `.close_out_backups/` held `SESSION_162_opening_prompt.md`
(expected). Drift-check clean: `current_state.md` stamp (13:42,
S161 close) matched `SESSION_161.md` close; `v3_build_picture.md`
stamped at S161 close (streams moved). Silent-open ritual
honoured. Same-workday open (~11 min after S161 close) — tight
recap; build picture rendered (streams moved at S161 ⇒ render
TRUE).

## Session shape

An open-then-root-cause session. Opened on the S161 streaming-
visibility hand-off; Code had executed the **bring-up visibility**
brief between sessions (suite 1003→1005), and the operator's first
live run showed the stream now reaching SUBSCRIBED at startup —
yet the $5 lay still returned 503. The session became a disciplined,
layer-by-layer root-cause hunt on that persistent 503: each step a
small **diagnostic-only** Code brief that made the next hidden layer
name itself, with a strict no-guessing rule (every hypothesis traced
against the live codebase before acting). It ended by driving the
503 to a single, definitive Betfair error. No fix was applied this
session — by design; the fix is S163's first work.

Five live `BetHub.command` runs happened across the session
(14:37–15:41), each adding a layer of on-screen visibility until the
real cause was named.

## What was delivered

1. **Session opened (silent ritual).** Same-workday tight recap;
   build picture rendered. Triaged the bring-up visibility report
   (S161 brief, Code-run): clean — `logging_setup.py` surfaces
   `ui.api.main` + `clients.betfair_client.v1` at INFO by named-
   namespace handler, `propagate=False`, no `uvicorn.access`
   duplication; suite 1003→1005.

2. **Key reframe #1 — the stream is fine at startup.** The first
   live run (post-visibility) showed `SUBSCRIBED at startup`; the
   lay 503 traced (off the code) to the bet-safety gate, but the
   gate's own refusal writes only to the in-memory audit sink, not
   the Terminal — so the lay-time reason was still dark. Drafted
   **`streaming_drop_visibility_brief.md`** (observability-only:
   give `streaming.py`'s state machine a logger; log every
   `self._state`/degraded-flag transition; no-flood on mcm/ocm/
   heartbeat). Code confirm-back caught FLAG 3 (log on either
   state OR degraded change) — approved. Triaged WHOLE: purely
   additive, suite re-run 1009, gate untouched.

3. **Key reframe #2 — the stream STAYS subscribed; it's not the
   gate.** With drop-logging live, the next run showed the stream
   holding SUBSCRIBED from startup through to the lay (no drop
   line) — so the gate *passed*. The 503 was therefore downstream,
   in the REST order-place call. Also surfaced (and grounded
   against the on-disk Betfair Stream API reference): the recurring
   startup `SUBSCRIPTION_LIMIT_EXCEEDED` (degraded→recovered) =
   the racing page subscribing to >200 markets (Betfair's per-
   subscription cap); non-fatal (the one error that does NOT close
   the connection), so NOT the lay blocker. Parked as real cleanup.

4. **Placement visibility — name the Betfair refusal.** Drafted
   **`placement_visibility_brief.md`** (observability-only: a
   logger on `placement.py`; one outcome line per `place_bet`
   branch — 3 failures WARNING with reason, success INFO with
   bet_id; gate byte-for-byte unchanged). Code confirm-back FLAGS
   A/B accepted (preserve the real local-variable gate form;
   emit→log→return on all four branches). Triaged WHOLE: diff
   purely additive (zero `-` lines), gate intact, suite 1013,
   dirty list 56→58 (placement.py + test, both newly `M`).

5. **The catch-all unmasked.** Next live lay named
   `betfair_api_unreachable` — but tracing showed that is the
   *catch-all* reason (anything not 401/403/429). Deeper trace:
   the write path IS correctly wired (`BetfairRestClient` →
   `TranslatingTransport` → httpx → the real Betfair betting
   JSON-RPC URL; base URLs correct in `config.py`). The real
   Betfair error sits on `BetfairRestError.message` but was never
   logged — every layer collapsed it (httpx → translation
   `_rpc_error_to_rest_error` maps a small known set, else
   `status_code=None` → catch-all → `api_unreachable`).

6. **The decisive diagnostic (operator asked for thoroughness).**
   Drafted **`placement_failure_diagnostic_brief.md`** — capture
   the COMPLETE raw failure at all three collapse layers (transport
   raw body/exception; translation full JSON-RPC error object;
   placement `exc.status_code`+`exc.message`), Terminal + a `/tmp`
   JSON-lines file, hard credential-redaction, tests for every
   fork. Code confirm-back was excellent: FLAG 2 narrowed it (a
   true connect failure would 500, not 503 → the live failure is
   the JSON-RPC-error fork); FLAGS 4/5 tightened (point-3 plain
   line; autouse conftest keeps the real `/tmp` file pristine).
   Triaged WHOLE: gate intact, credential-safety proven (sentinel
   test), `/tmp` clean, suite 1018, dirty list 58→61 (helper +
   test `??`, conftest `M`).

7. **ROOT CAUSE NAMED (live).** The next lay printed it outright:
   `APINGException errorCode=INVALID_INPUT_DATA — "The customerRef
   for this transaction contains invalid characters or is too long
   (32 character limit)"`. The app sends `customer_order_ref =
   "bet-record-" + uuid4()` = **47 chars**; Betfair caps the
   reference at **32**. Betfair rejects the order outright. Not the
   stream, not auth, not the connection, not a closed market — a
   reference string 15 characters too long.

## Standing-instruction adherence

- **Cat 1 — silent open/close ritual: HONOURED.** No step
  narration; single combined orientation at open; close running
  silent with one-line end.
- **Cat 1 — build-picture conditional render: HONOURED** (rendered
  at open; streams moved at S161).
- **Cat 1 — short, plain, decision-first: HONOURED.** Each live
  503 answered with the plain-language read + bet-safety
  reassurance led; technical detail kept inside the briefs.
- **Cat 1 — inventory-first on technical reports: HONOURED.** All
  three reports triaged off disk, findings classified, only
  operator-relevant calls surfaced.
- **Cat 3 — verify empirically: HONOURED, heavily.** Re-ran the
  full suite independently after each brief (1009 / 1013 / 1018);
  traced every 503 through the live code; confirmed the gate
  byte-for-byte and the diffs additive; grounded the Betfair
  error-code meaning against the on-disk Stream API reference.
- **Cat 3 — create_file banned / verify writes: HONOURED.** All
  briefs written via Desktop Commander; verified via wc/sha/grep.
- **Cat 3 — chunked writes + pre-exec risk: HONOURED.**
- **Cat 5 — make software calls, don't punt: HONOURED.** Brief
  shapes, capture mechanisms, scope cuts decided and named; only
  genuine operator calls (confirm-first vs combined; instant peek
  vs durable brief; close vs push on) surfaced.
- **brief-drafting skill — APPLIED three times** (drop-visibility,
  placement-visibility, placement-failure-diagnostic); calls
  surfaced at each hand-off; confirm-back prompts provided.
- **Bet-safety hard rule — CLEAN + PROVEN LIVE again.** No bet
  placed across five live runs; the gate refused every lay under
  real conditions; `placement.py`'s gate condition + envelope
  byte-for-byte unchanged across all three briefs.
- **`standing_instructions.md` — NOT edited this session.**

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in S162:**
- Bring-up streaming-visibility brief (S161) — triaged clean. ✅
- "Stream not reaching SUBSCRIBED" blocker — RESOLVED; stream
  subscribes at startup and holds. ✅
- Drop-visibility + placement-visibility + placement-failure
  diagnostic briefs — all executed + triaged WHOLE. ✅
- Lay-503 root cause — NAMED: customerRef exceeds Betfair's
  32-char limit. ✅

**New / promoted for S163:**
- **THE FIX (S163 primary):** make `customer_order_ref` Betfair-
  compliant (≤32 chars) while staying unique and still tying each
  Betfair order back to its v3 bet record. Design choice is
  Claude's (shorten the ref format, or send Betfair a compliant
  short ref distinct from the internal bet id) — surface only the
  shape, handle detail in the brief. Chat → Code brief.

**Carry-forward (real, named, not blocking the fix):**
- **F1 uncaught-transport gap** — a genuine connect/HTTP-error on
  the order POST would surface as a 500, not a clean 503
  (`_build_live_httpx_transport` raises raw httpx; place_bet only
  catches `BetfairRestError`). Robustness fix, later brief.
- **200-market over-subscription** — racing page subscribes to
  >200 markets ⇒ recurring startup `SUBSCRIPTION_LIMIT_EXCEEDED`
  (non-fatal); affected markets fall to REST. Cleanup brief.
- **In-memory audit-sink durability** — placements logged only to
  an in-memory sink; no on-disk record of bets/refusals yet.
- Streaming hardening follow-up (F3 keepAlive / F5 INVALID_CLOCK /
  F4 on-screen live-data-loss warning) — note: stream proven
  stable through bet-time this session, so this is lower urgency
  than thought, but still carried.
- is_self coordinated-removal brief; optional v3 tree commit;
  quick-lay modal error-reason surfacing (the 503 reason now logs
  to Terminal but the UI modal still shows generic); W16 cutover
  scoping; the long-standing parking-lot set from S161.

## Session close state

- Rebuild root: clean — 12 governance `.md` + `openapi.json` +
  `external_api_resources.md` + `.DS_Store`. No phantom files.
  Three new briefs + three new reports added under
  `dr029/2_4_betfair_streaming/`.
- `current_state.md`: rotated to S162 close.
- `v3_build_picture.md`: updated — Streaming-transport milestone
  moved (stream now subscribes + holds; lay-503 root cause named);
  a new "Placement / live-lay" thread captured.
- `standing_instructions.md`: **not edited** this session.
- `.close_out_backups/`: `SESSION_163_opening_prompt.md` written;
  S162 prompt removed.
- `sessions/`: `SESSION_162.md` added.
- **v3 tree (bethub-v3):** carries this session's diagnostic
  additions (streaming.py drop-logging; placement.py outcome
  lines + raw line; composition.py + _translation.py capture
  calls; new `_failure_diagnostics.py`; new tests; conftest
  redirect). Suite at 1018. Still fully uncommitted by design.

## Forward routing — confirmed with operator

Operator confirmed: close S162, finish next session. **S163 opens
on THE FIX** — scope and commission the `customer_order_ref`
≤32-char fix (Chat → Code), then the operator re-runs the live $5
lay, which should now place. The three carry-forward robustness/
cleanup items (uncaught-transport gap, 200-market over-
subscription, audit-sink durability) sequence after the lay
proves out.
