# Session 156 — Login-throttle report triaged CLEAN;
# validation runbook scoped; v2 relaunch fixed

**Opened:** 2026-06-17 09:34 ACST
**Closed:** 2026-06-17 13:16 ACST
**Tool routing:** Claude Chat (triage, planning, ops
support, governance). Desktop Commander for all
filesystem/process work. No Code session this session.
**Governing DRs:** DR-021 (timestamp anchoring), DR-029
(accounts-setup arc), DR-030 (provider homing), DR-032
(Betfair canonical). DR-027/028 noted (cutover not yet
scoped).

## State at open (rotated from current_state.md)

Entered with auto-login built + triaged clean (S155) and
the login-throttle brief LOCKED (374 lines, SHA
`3b57f08e`), awaiting out-of-session Code execution. S156's
job was to triage Code's throttle report once it landed.

## Anchor

- Open: 2026-06-17 09:34 ACST
- Close: 2026-06-17 13:16 ACST
- Elapsed 3h42m wall-clock, but the middle was an operator
  betting break (v2 daily-driver use); active session work
  well under the 3h split trigger. No day rollover, no
  scope change — full close.

## Pre-flight checks (open ritual)

Drift-check clean: `current_state.md`, `SESSION_155.md`,
and `v3_build_picture.md` all stamped 2026-06-17 09:24 ACST
(S155 close); accounts-setup had moved at S155 ⇒
build-picture render condition TRUE at open. Root clean — 12
expected `.md` files + the two API-resource files + benign
`.DS_Store`; `.close_out_backups/` held only the S156
opening prompt. Code's `login_throttle_report.md` confirmed
present ⇒ S156 ran as a real triage, not a hold.

## Session shape

A focused Chat session with one primary deliverable (triage
Code's throttle report) plus operator-facing planning and a
short operational interlude. Three movements: (1) triaged
the throttle report CLEAN, grounding the verdict with
independent filesystem checks rather than the report's prose
alone; (2) rendered the v3 build plan and scoped the
operator-side validation runbook, detailing step 1
(credentials); (3) diagnosed and fixed a v2 daily-driver
relaunch failure so the operator could place real bets, then
shut v2 down cleanly at close. No Code commissioned; no
governance truth changed beyond close-out artefacts.

## What was delivered

1. **Login-throttle report triaged — CLEAN (primary).**
   Code's `dr029/auto_login/login_throttle_report.md` passed
   all three triage gates. Suites green: pytest 977→983 (+6
   throttle tests on a fake login + fake clock, zero
   network); vitest/tsc/eslint byte-unchanged;
   ruff/mypy/import-linter clean (throttle stayed inside the
   provider per DR-030). Anchors clean: only
   `_auth_betfair.py` + its test file touched —
   independently grep-verified across the v3 tree (throttle
   symbols confined to the two files; no leak to config,
   call sites, DB, frontend). No new operator config: the
   credentials trio named in `auto_login_report.md` §5 is
   still the only operator setup. Headline values
   independently confirmed in the actual code, not just the
   report: cool-off 30m → 1h → 2h → 4h, `MAX_LOGIN_ATTEMPTS
   = 5`, killed message verbatim to the brief, token max-age
   unchanged at 3h.

2. **Findings surfaced (operator-relevant).** The
   TEMPORARY_BAN gap that started this work is now closed —
   the throttle covers the ban case and every
   repeated-failure case. Killed-state behaviour confirmed:
   escalating cool-off, hard kill at 5, distinct
   auth-expired error + one ERROR log line, restart-only
   recovery (operator+Claude review), single-success reset.
   Scope note: the throttle counts genuine login failures
   (`BetfairRestError`); an unexpected different exception
   type surfaces loudly rather than being throttled —
   deliberate, and it doesn't reopen the lockout vector (the
   failures that cause lockouts all run the throttled path).
   On-screen banner remains out of scope (parking-lot).

3. **V3 build plan rendered + validation runbook scoped.**
   Showed the path to cutover inline: accounts-setup code is
   now effectively complete (registration + auto-login +
   throttle all in and triaged); remaining sequence is
   operator validation (deploy + $5 lay) → is_self
   coordinated-removal brief → W16 cutover → v3 complete;
   P1/P2 parked post-cutover. Scoped the operator-side
   validation as a 6-step runbook (login → launch v3 →
   confirm live odds → $5 lay → check Betfair → login
   safeguards). Detailed step 1: same credential values as
   v2 (same Betfair account) placed in v3's fields —
   `BETHUB_BETFAIR_MODE=live` + the app-key/username/
   password trio (env) or the JSON credentials file.
   Confirmed v3 has no EV calcs yet (analytical layer is P2,
   parked) ⇒ v2 stays the daily driver through validation.

4. **v2 relaunch failure diagnosed + fixed (operational).**
   The BetHub.app launcher wasn't reopening. Root cause: the
   previous run's Vite found 5173 busy and silently fell
   back to 5174, so Chrome opened to a dead 5173. Confirmed
   v2 fully down (no listeners on 5000/5173/8400, no stale
   procs); backend had last logged healthy the prior day.
   Brought v2 up cleanly — Flask :5000, Vite pinned to :5173
   (`--strictPort`), SSH tunnel attempted — verified both
   services listening + dashboard serving (200), opened
   Chrome. Operator placed real bets on v2. At close, shut
   v2 down gracefully (TERM to Flask/Vite/node child; tunnel
   had already exited) and verified all ports clear + no
   lingering processes.

## Standing-instruction adherence check

- **Cat 1 inventory-first cadence on long technical
  reports** — honoured. Throttle report triaged via
  inventory pass; each finding classified; operator-relevant
  ones surfaced in plain gambling language; technical detail
  handled silently.
- **Cat 3 verify-empirically** — honoured + exceeded.
  Verdict grounded in independent grep + code reads
  (anchors, schedule, kill threshold, killed message), not
  prose alone.
- **Cat 1 build-picture inline render** — honoured at open
  (render condition fired; full table + accounts-setup
  detail).
- **Cat 1 brevity / plain-language / narrow fenced wraps** —
  honoured.
- **Bet-safety hard rule** — CLEAN. No live orders by
  Claude; operator's real bets placed by operator through
  v2; v3 validation ($5 lay) deferred to S157.
- **Tool routing stated** — honoured (Chat vs Code vs
  operator-side named throughout).
- **No standing-instruction file edits** this session.

## Open items

Pointer-only — full detail in `current_state.md`.

**New / promoted for Session 157:**
- Run the operator-side validation (deploy v3 live + $5
  lay) — S157 primary, gated on operator setting v3
  credentials.
- is_self coordinated-removal brief — drafts once validation
  confirms v3 live.

## Open items out (closed this session)

- Login-throttle report triage — ✅ DONE (clean; all three
  gates passed; headline values independently verified).
- v2 relaunch failure — ✅ RESOLVED (port-pin fix; cleanly
  shut down at close).

## Session close state

- Rebuild folder root: clean — 12 `.md` + 2 API-resource
  files; no phantom files.
- WIP: none open.
- `.close_out_backups/`: stale `SESSION_156_opening_prompt.md`
  removed; `SESSION_157_opening_prompt.md` written.
- `sessions/`: `SESSION_156.md` written (this file).
- v3 build picture: updated (accounts-setup stream moved).
- v2 runtime: fully shut down (operator-confirmed).

## Forward routing

**Confirmed with operator.** Session 157 runs the
validation: operator sets v3 credentials (step 1), launches
v3 live, confirms live odds, places the real $5 lay, checks
Betfair. Deferred to S157 at operator's explicit direction
("we will run validation next session"). If validation
passes, S157 proceeds to the is_self coordinated-removal
brief; if it surfaces issues, those become S157's triage. v2
was stopped at operator's request and is no longer running.
