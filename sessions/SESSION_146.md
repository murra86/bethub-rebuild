# Session 146 — W17 brief + M1 micro-brief both drafted and LOCKED

**Opened:** 2026-06-10 16:06 ACST.
**Closed:** 2026-06-13 09:17 ACST (multi-day session — operator
paused after the open/drafting day; close-out fired on actual
close per Cat 2 multi-day rule).
**Tool routing:** Claude Chat (grounding reads + brief drafting +
locks). No code edits. New artefacts:
`dr029/w17_racing_pages/w17_brief.md` (598 lines, LOCKED) and
`dr029/m1_maintenance/m1_brief.md` (174 lines, LOCKED; new
`dr029/m1_maintenance/` directory). Code execution prompts for
both briefs handed to operator in-chat at close.
**Governing DRs invoked:** DR-021 (Adelaide anchors), DR-030
(module boundaries — racing router + migrations placement),
DR-031 (tech stack — Alembic adoption commissioned via M1),
DR-019 (derive-on-read — lay liability + balance surfaces),
DR-025 + S139 amendment (commission from Betfair MBR — carried
into the EV-engine port spec), DR-032 (canonical bet record),
DR-027/028 (named to exclude analytical-line access from W17).

## Anchor

```
# Session-open:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-06-10 16:06 ACST

# Session-close:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-06-13 09:17 ACST
```

## Pre-flight checks

Open ritual ran silent per `bethub-session-open` (sixth
consecutive clean). Required reads completed (`current_state.md`,
`standing_instructions.md` in full, `project_context.md`,
`SESSION_145.md`, `scope_settlement.md`). Pre-flight directory
listing clean: 13 root `.md` + `openapi.json`, all directories
present, `.close_out_backups/` held only
`SESSION_146_opening_prompt.md` (expected).

**Drift-check (Step 5): clean.**
- (a) `current_state.md` "Last updated" matched `SESSION_145.md`
  "Closed:" (2026-06-10 15:58 ACST).
- (b) `SESSION_145.md` present, non-empty (205 lines).
- (c) `v3_build_picture.md` updated at S145 close; render
  condition TRUE — build picture rendered at open.

Same-workday open (~8 min after S145 close) — tight recap. Open
ritual output: single combined brief (recap + build picture +
open-items delta + hand-off).

## Session shape

Brief-drafting session, exactly the S145-confirmed shape. First
half: remaining W17 grounding reads — v2's `LogBetFromRacePage.jsx`
(735), `HedgeModal.jsx` (628), `evEngine.js` (502),
`promoPresets.js`, `softOddsLadder.js`; v3's workflow read
surfaces (W12 `balance_derivation.py`, W13 `promo_derivations.py`
signatures + key function bodies), betfair_client surfaces
(live_pricing, market_catalogue, scheduled_time signatures),
contract §9 structure, `ui/api` scaffold and `ui/web` source tree.
Second half: W17 brief drafted end-to-end per
`bethub-brief-drafting` with call-driven surfacing (scope was
locked at S145, so per-section operator calls were nil; two
drafting calls surfaced for visibility at hand-off). Operator
locked W17 on the summary without a section walkthrough, then M1
anchors were verified empirically (docstring line numbers, mypy
error count = 15, time-bomb file locations) and the M1 micro-brief
drafted and locked the same way. Code prompts for both briefs
provided at close on operator request.

## What was delivered

**1. W17 brief — drafted, verified, LOCKED.**
`dr029/w17_racing_pages/w17_brief.md`, 598 lines, 11 sections
(§5 carries twelve scope sub-sections). Expands the S145 scope
settlement without re-opening it. Key shape: new
`list_racing_markets` betfair_client read surface + contract §9.9
backward-compatible addition (the client had single-market reads
only — gap found in grounding); racing read routers + log-context
route (W12 balance + W13 FB inventory in one response); bet-log
and lay-placement routes fronting the existing bet_entry workflow;
EV engine ported to TypeScript client-side (v2 parity, regression
fixtures pinning Harville/EV outputs to 6dp); race sidebar, dense
odds/EV table, promo preset machinery, simple price-movement
indicator (5-min tunable window, sparkline + matched-spike flag
both included as the drafting call), log panel with FB
inventory/balance surfacing, ⚡ quick-lay port. Coherent-checkpoint
priority defined (§6) if Code overruns: price-read + bet-log page
first; quick-lay and indicator are the cut line.

**2. Bet-safety posture encoded in W17.** No live Betfair API
calls or order placement during the build — placement path
mock-tested; operator exercises the live ⚡ path at small size
post-delivery. v2's two safety behaviours preserved explicitly:
$50 default stake on bonus-winnings cash, and the
never-profit-target-lay rule (uncapped-liability guard) restated
in §5.4 and §5.11.

**3. M1 micro-brief — drafted, verified, LOCKED.**
`dr029/m1_maintenance/m1_brief.md`, 174 lines, seven items:
FB-test clock-freeze (REF_TIME 2026-05-18; baseline 894/2 →
896/0), two stale `_COMMISSION_TABLE` docstrings
(balance_derivation L153–160, test_balance_lay_branch L291), bets
row-factory normalisation (W15 f#2), `.importlinter` doc note
(W15 f#1), `betfair_adapter.py` mypy cleanup (15 errors verified
live, union-narrowing flavour, no-ignore rule), Alembic adoption
(baseline revision 0 only, empty-diff verification, stamp path
documented for operator — never executed against the live DB).

**4. Code execution prompts** for both briefs handed to the
operator in-chat (M1 first to green the baseline, then W17).
Reproduced in the S147 opening prompt for re-use.

## Standing-instruction adherence check

- **Cat 1 silent open-ritual — CLEAN** (sixth consecutive,
  S141–S146). Single combined output, zero step narration.
- **Cat 1 calendar-calibrated recap** — honoured (same-workday,
  tight).
- **Cat 1 build-picture conditional render** — honoured
  (rendered; streams moved at S145 close). 26 consecutive clean
  S120–S146.
- **Cat 1 open-items delta** — honoured (rendered).
- **Cat 1 plain language** — honoured (drafting calls surfaced in
  gambling-operational terms; Alembic unwound on every mention).
- **Cat 1 call-driven surfacing** — honoured and load-bearing this
  session: scope sections drafted and written to disk without
  per-section walkthroughs; only the two genuine visibility items
  (mock-only Betfair during build; preserved v2 safety defaults)
  surfaced. Operator opted to lock both briefs on summaries.
- **Cat 2 anchors / reads / pre-flight / drift-check** — honoured.
- **Cat 2 multi-day session rule** — exercised: open 2026-06-10,
  close 2026-06-13; close-out fired at actual close, re-anchored.
- **Cat 3 Desktop Commander discipline** — honoured; chunked
  brief writes with verify-after-write (wc -l + header greps);
  one ENOENT on the M1 write caught immediately (missing
  directory), fixed with mkdir and re-verified — no silent loss.
- **Cat 3 empirical verification** — honoured: M1 anchors (line
  numbers, mypy count, time-bomb files) verified against the live
  repo before being named in the brief.
- **Cat 5 make-software-calls-don't-punt** — honoured: EV engine
  port location (client-side TS), new client surface shape,
  router/envelope mapping, sparkline + spike-flag inclusion,
  Alembic placement — all called by Claude, stated for
  visibility where operationally relevant, not punted.
- **Operator-confirmed forward routing** — honoured ("lock it" ×2;
  "provide the Claude Code prompt first, then close out").

## Open items in (carry to S147)

- **W17 — awaiting-code-execution.** Operator runs the W17 Code
  session out-of-session against the locked brief. S147 (or the
  first session after Code runs) triages
  `dr029/w17_racing_pages/w17_report.md`. May arrive as a
  checkpoint report if Code overran — triage routes the remainder.
- **M1 — awaiting-code-execution.** Operator runs the (light) M1
  Code session first. Triage `dr029/m1_maintenance/m1_report.md`;
  on clean close, pytest standing baseline becomes 896/0 and
  Alembic is recorded as adopted against DR-031.
- **Operator first-use validation of the live ⚡ quick-lay path**
  (post-W17 delivery, real race, small size) — bet-safety step
  named in W17 §10.
- Parking-lot carries unchanged: calculator rethink; cross-account
  spot-check view; settings-area cadence follow-up brief;
  greyhound operational constraint verification;
  `cascaded_at_settlement_state` closed-enum revisit (W8);
  §2.4 Fix 4 cadence design dependency; optional live
  `get_account_funds()` probe; Betfair API membership tier
  investigation (awaiting BetWatch).

## Open items out (closed/advanced S146)

- **W17 brief drafting** — ✅ CLOSED (drafted, verified, LOCKED).
- **M1 micro-brief drafting** — ✅ CLOSED (drafted, verified,
  LOCKED; did not slip to S147).
- Betfair-client race-listing gap — found in grounding, resolved
  inside the W17 brief (§5.2 surface + contract §9.9 addition);
  not a carried item.

## Session close state

- **`dr029/w17_racing_pages/`** — `scope_settlement.md` (carried),
  `w17_brief.md` (NEW, 598 lines, LOCKED).
- **`dr029/m1_maintenance/`** — NEW directory; `m1_brief.md`
  (174 lines, LOCKED).
- **v2 + v3 codebases** — untouched (grounding reads + one mypy
  diagnostic run only; v2 read-only per standing rule).
- **`current_state.md`** — rotated to S146 close.
- **`v3_build_picture.md`** — updated (W17 → awaiting-code-
  execution; M1 → awaiting-code-execution; current-session detail
  block rewritten).
- **`.close_out_backups/`** — `SESSION_147_opening_prompt.md`
  written; stale `SESSION_146_opening_prompt.md` swept.
- **No edits** to `decisions.md`, `standing_instructions.md`, or
  other canonical truth.

## Forward routing

**Confirmed with operator** ("provide the Claude Code prompt
first, then close out"). Between sessions: operator runs M1 in
Code, then W17 in Code, using the prompts provided (also carried
in the S147 opening prompt). S147 opens on report triage —
whichever reports exist on disk at open (M1 expected first; W17
possibly a checkpoint report). Claude Chat triages per the
inventory-first cadence; any W17.1 surgical follow-up routes from
there. W16 cutover remains blocked-on-W17.

## Close-out notes

Clean two-deliverable session — the largest brief of the build
plus the maintenance bundle both locked in one session, which the
S145 deferral made room for. Call-driven surfacing earned its keep:
a 598-line brief produced with exactly two operator-facing calls,
both bet-safety/visibility-shaped, and the operator locked on
summary. The one wobble (M1 write ENOENT into a not-yet-created
directory) was caught by the immediate error, not by later
verification — mkdir-then-rewrite, verified clean. Multi-day close
exercised the Cat 2 rule as designed.
