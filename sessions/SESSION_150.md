# Session 150 — VPS alert-flood fixed at source; accounts-setup scoped (fresh / core-earners / setup-screen); build brief deferred to S151

**Opened:** 2026-06-15 09:24 ACST.
**Closed:** 2026-06-15 12:44 ACST.
**Tool routing:** Claude Chat throughout. Two distinct
arcs: (1) an out-of-scope VPS ops task (racing data-
capture health check + alert-email fix) handled directly
over SSH via Desktop Commander; (2) the bethub-rebuild
work — a Chat scoping session for the new accounts-setup
workstream. Heavy Desktop Commander use (SSH to the
capture VPS; read-only queries against v2 bethub.db; one
scratch artefact written). No code edits to v2/v3. No
governance-truth edits beyond close-out.
**Governing DRs invoked:** DR-021 (Adelaide anchors),
DR-022 (book/account/account-at-book vocab — shapes
accounts-setup), DR-027/028 (two-DB split + boundary —
accounts-setup is a cutover/cross-DB moment), DR-030
(v3 module boundaries), DR-031 (v3 stack).

## Anchor

```
# Session-open:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-06-15 09:24 ACST
# Session-close:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-06-15 12:44 ACST
```

## Pre-flight checks

Open ritual ran silent per `bethub-session-open` (tenth
consecutive clean). Required reads completed
(`current_state.md`, `standing_instructions.md` in full,
`project_context.md`, `SESSION_149.md`). Pre-flight
listing clean: 13 root `.md` + `openapi.json`, all dirs
present, `.close_out_backups/` held only
`SESSION_150_opening_prompt.md` (expected).

**Drift-check: clean.**
- (a) `current_state.md` "Last updated" matched
  `SESSION_149.md` "Closed:" (2026-06-14 08:23 ACST).
- (b) `SESSION_149.md` present, non-empty (273 lines).
- (c) `v3_build_picture.md` updated at S149 close; render
  condition TRUE — build picture rendered at open.

New-workday open (next calendar day, after 4am) — longer
recap delivered before the operator's VPS request.

## Session shape

Two arcs. The operator opened S150 but front-loaded an
out-of-scope request: a health check on the racing
data-capture VPS plus shutting down a flood of alert
emails. That was handled first (see "What was delivered"
#1), then the session ran its intended shape — a Claude
Chat scoping session for the new accounts-setup
workstream (the S150 primary per `current_state.md`).
Scoping settled three operator calls, grounded them in
the operator's real v2 footprint, and pinned the outcome
to scratch. The build brief itself was deferred to a
focused S151 on a budget call (>3h wall-clock by close;
direct W12-precedent for giving a build brief its own
session).

## What was delivered

**1. VPS alert-flood fixed at source (out-of-scope ops).**
Health-checked the racing data-capture VPS
(`root@187.77.183.9`). Both core services healthy
(`racing-capture` collector + `racing-api`, 4-day
uptime); discovery cycling across Betfair + all
bookmakers incl. TABtouch. Diagnosed the "million emails"
flood: the liveness check's 30-min cooldown was broken —
its cooldown file (`.last_liveness_alert`) was owned by
`root` while the check runs as `racing`, so every run
errored on the cooldown write and the frozen timestamp
defeated suppression → an alert every 15 min whenever the
Betfair-freshness check tripped. That check's 4h
staleness threshold also failed to cover the ~13h
overnight racing gap, so it false-tripped every morning.
Fix: `chown racing:racing` the cooldown file (restores
suppression) + raised `BETFAIR_STALE_MINUTES` 240 → 840
in `scripts/liveness_check.py`; `.bak` saved; py_compile
clean; manual run as `racing` now exits 0, all checks
pass, no email. Two follow-ups parked (operator-flagged):
recurring `FOREIGN KEY` warnings dropping the odd Betfair
race; and confirming the morning snapshot gap is just the
overnight lull. Routed as future VPS-ops (SSH), not Code.

**2. Accounts-setup scoping — three calls locked.**
- Call 1 — **fresh start in v3**, no v2 import (clean
  build on v3's account model, no v2 vocab debt).
- Call 2 — **core earners first** (lean start, expand
  later; not the full 34-book footprint).
- Call 3 — **setup screen** (reusable in-v3 add/edit
  accounts page, not a one-time seed).

**3. Grounded in the operator's real v2 footprint.**
Read-only queries against v2 `bethub.db`: 49 accounts
across 5 players (Tim, Kate, Jordan, Caroleena, Sarie)
at 34 books; 22 active, 9 promo_excluded. Top books by
real bet activity (1,931 bets): Betfair (exchange/lay
side), TAB, TABTouch, PointsBet, HotBet, BossBet, Betr
as earners; StarSports high-churn/account-health. Used
to confirm v3's catalogue covers the earners and the
screen surfaces them first (Claude's territory — no
operator call).

**4. Scope pinned to scratch.** Wrote
`dr029/accounts_setup/_drafts/SESSION_150_drafts.md`
(109 lines) — locked scope, earner grounding, v3 known
structure (from S149), S151 pre-flight TODO, brief shape
+ governing DRs, routing. S151 opens ready to draft.

## Standing-instruction adherence check

- **Cat 1 silent open-ritual — CLEAN** (tenth
  consecutive). Single combined output at orientation;
  zero step narration.
- **Cat 1 calendar-calibrated recap** — honoured
  (new-workday, longer recap).
- **Cat 1 build-picture conditional render** — honoured
  (rendered at open; streams had moved at S149 close).
- **Cat 1 plain language for a non-technical operator** —
  honoured. VPS diagnosis (cooldown/permissions, stale
  threshold) and accounts-setup calls all framed in
  plain operational terms.
- **Cat 1 make-software-calls / surface only operator
  calls** — honoured. Catalogue contents + screen
  ordering taken as Claude's call; only the three genuine
  operator calls (import?/which books/screen-vs-seed) and
  the session-shape routing call were surfaced.
- **Cat 2 anchors / reads / pre-flight / drift-check** —
  honoured at open and close.
- **Cat 3 Desktop Commander discipline** — honoured. All
  filesystem/process work via Desktop Commander; live v2
  DB queried in place (never copied); write-script-to-
  `/tmp` for the query scripts; no `create_file`;
  verify-after-write on the scratch doc.
- **Cat 3 verify-empirically** — honoured. Accounts-setup
  grounded in live v2 data, not memory; VPS diagnosis
  confirmed against live logs/journal/service state.
- **Bet-safety (hard rule) — honoured.** No live Betfair
  order placed; VPS work was capture-side only.

## Open items in (carry to S151)

Pointer-only — full detail in `current_state.md`.

- **Accounts-setup build brief (NEW) — S151 primary.**
  Draft the Code build brief against the locked scope in
  the scratch doc. Pre-flight: probe v3 codebase first.
- **W16 cutover** — next major routing decision;
  accounts-setup is its first dependency.
- **v3 auto-login (Code)** — folds into the accounts
  build.
- VPS follow-ups (out-of-rebuild, SSH-ops): FK-constraint
  warnings; confirm morning snapshot gap is overnight
  lull.
- Parking-lot carries unchanged: runbook patches (W17.1
  §3); v3 dev CORS default; sidebar empty-vs-error UI;
  live racing-page UI roughness; F4 liability-cap; F6
  cross-AAB FB-deploy guard; calculator rethink; cross-
  account spot-check; greyhound op-constraint verify;
  `cascaded_at_settlement_state` enum (W8); §2.4 Fix 4
  cadence; Betfair API tier (awaiting BetWatch).

## Open items out (closed/advanced S150)

- **Accounts-setup scoping — ✅ DONE.** Three calls locked
  + grounded; scope pinned to scratch.
- **VPS alert flood — ✅ FIXED** (out-of-rebuild).

## Session close state

- **v2 + v3 codebases** — untouched (read-only on v2;
  no v3 edits).
- **VPS** — `scripts/liveness_check.py` edited
  (threshold 240→840) + cooldown file chowned; `.bak`
  saved on the box. Capture services healthy.
- **New file on disk:**
  `dr029/accounts_setup/_drafts/SESSION_150_drafts.md`.
  Throwaway: `/tmp/v2_*.py` query scripts.
- **`current_state.md`** — rotated to S150 close.
- **`v3_build_picture.md`** — updated (Accounts-setup →
  scoped, brief-drafting next; current-session detail
  rewritten).
- **`.close_out_backups/`** —
  `SESSION_151_opening_prompt.md` written; stale
  `SESSION_150_opening_prompt.md` swept.
- **No edits** to `decisions.md`,
  `standing_instructions.md`, `governance.md`, or other
  canonical truth. Accounts-setup is a workstream/routing
  decision (current_state + this record + build picture);
  a DR is a S151 scoping call if warranted.

## Forward routing

**Confirmed with operator** ("close please", after
agreeing to defer the brief to its own session). S151 is
a **Claude Chat** brief-drafting session: probe the v3
codebase, then draft the accounts-setup build brief
section-by-section against the locked scope. A **Claude
Code** session then builds against the locked brief; v3
auto-login folds in; the $5 lay test runs against the
operator's real Betfair account once registered.

## Close-out notes

Productive split-shape session: an unplanned VPS ops fix
up front, then the intended accounts-setup scoping.
Three clean operator calls, grounded in real v2 data,
pinned to scratch; brief deferred to S151 on a budget
call (>3h wall-clock; W12 precedent). No split trigger
forced a minimal close — close-out ran full with budget
intact.
