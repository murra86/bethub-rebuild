# Session 155 — auto-login report triaged; login-throttle brief drafted and locked

**Opened:** 2026-06-17 08:43 ACST
**Closed:** 2026-06-17 09:24 ACST
**Tool routing:** Claude Chat (auto-login report triage,
throttle co-design with operator, brief drafting + lock,
close). Claude Code executes both locked briefs
out-of-session.
**Governing DRs:** DR-021 (Adelaide timestamps), DR-030 (v3
module boundaries), DR-031 (tech stack), DR-032 (Betfair
canonical).

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → `2026-06-17 08:43 ACST`.
- Close: `TZ=Australia/Adelaide date` → `2026-06-17 09:24 ACST`.

## Pre-flight checks (open)

Drift-check clean: `current_state.md` and `SESSION_154.md`
both stamped `2026-06-17 08:30 ACST` (S154 close);
`v3_build_picture.md` stamped same. Root listing clean — 12
expected `.md` files + the two known API-resource files
(`external_api_resources.md`, `openapi.json`); `.DS_Store`
benign; no phantom files. `.close_out_backups/` held only the
expected `SESSION_155_opening_prompt.md`. Same-workday open
(prior close 08:30, fresh open 08:43 same calendar day).

## Session shape

A focused Claude Chat session in two halves. First half:
triaged Code's auto-login report (the deliverable queued at
S154). Ran the inventory pass — report clean, suites green
(977 pytest, +17 new), only the 5 named files touched, zero
live Betfair calls. Surfaced the operationally-relevant
findings to the operator in plain language. Second half: the
TEMPORARY_BAN finding plus the operator's lived 48-hour
lockout drove a co-design of a login throttle; ran the
`bethub-brief-drafting` ritual end-to-end, grounded on the
just-built provider on disk, drafted + locked the throttle
brief, provided the Code prompt, closed.

## What was delivered

1. **Auto-login report triaged clean.** Read
   `dr029/auto_login/auto_login_report.md`. Inventory pass
   surfaced: provider built + wired (self-refreshing
   `BetfairAuthProvider`), static-token fallback preserved,
   pytest 960→977 (+17, all against a fake login transport),
   vitest/tsc/eslint unchanged. Operator-relevant findings
   surfaced: (a) TEMPORARY_BAN backoff from v2 NOT ported —
   a failing login re-attempts on every request (the seed of
   the throttle work below); (b) first real login is the
   operator's at deploy ($5 lay); (c) 6 pre-existing
   frontend lint errors on live bet-entry surfaces, not from
   this work, parked. Config-to-set already named in the
   report — no new operator config needed beyond it.

2. **Login throttle co-designed with the operator.** The
   TEMPORARY_BAN finding opened a design conversation. The
   operator's ground truth — a past hammering episode locked
   him out of Betfair for ~48 hours and cost money — drove a
   conservative shape beyond v2's ban-only 30-min backoff:
   throttle ALL repeated login failures, one attempt per
   cool-off window, windows escalate 30 min → 1 hr → 2 hr →
   4 hr (cap), and a **hard kill at 5 consecutive failures**
   (operator's call — at 5, something structural is wrong
   that needs review). No auto-recovery: killed state clears
   only on v3 restart, which the operator does *after*
   consulting Claude on remediation. Any successful login
   resets to zero. A timeline visual (cool-off escalation +
   the kill) was rendered inline to confirm the shape.

3. **Throttle brief drafted + LOCKED.** Written to
   `dr029/auto_login/login_throttle_brief.md`. Surgical-fix
   shape (Sessions 35/36 precedent). 11 sections; **374
   lines, 15,094 bytes, SHA256 `3b57f08e021e820f`.** Status
   flipped DRAFT → LOCKED after operator approval.
   Commissions Code to add the throttle to the just-built
   provider — two anchors only (`_auth_betfair.py` + its test
   file), throttle state under the existing lock driven by
   the existing injected clock, tested with a fake login +
   fake clock (zero network, zero real waiting). Python-only;
   no config/env, no frontend, no call-site changes.

4. **Operator calls settled.**
   - **Kill visibility (surfaced) — operator agreed.** The
     killed-state signal this round is a distinct 401 error
     (maps to `betfair_auth_expired`, no call-site change) +
     one ERROR-level log line. A visible on-screen banner was
     kept OUT of scope (frontend work; keeps the result
     Python-only and clean) — noted as a separate small
     follow-up if the operator later wants can't-miss
     on-page alerting.
   - **Software calls (Claude's, surfaced for redirect):**
     throttle lives inside the provider (same lock/clock);
     schedule + threshold are in-code constants not env
     settings; killed state raises the existing 401 type with
     a distinct message; the 4 hr window doubles as a safety
     cap if the threshold were ever raised above the schedule
     length.

5. **Code prompt provided** for the out-of-session run —
   reads the throttle brief + the auto-login brief/report +
   the provider + test file, confirms understanding before
   building (Flow 3 discipline), captures baseline, executes
   §5 in §6 order, hard limits restated, report to
   `login_throttle_report.md`.

## Standing-instruction adherence

- **Cat 1 inventory-first on long reports** — honoured: ran
  the inventory pass on the auto-login report, classified
  each finding by operational impact, surfaced only the
  operator-relevant ones in plain gambling language.
- **Cat 1 brevity / decision-first** — honoured throughout;
  led with the call or the headline, held detail in the
  brief and the report.
- **Cat 1 build-picture render** — rendered at open (streams
  moved at S154).
- **Cat 1 calendar-calibrated open** — same-workday tight
  recap (prior close 08:30, open 08:43).
- **Cat 3 verify-empirically / DR-013** — grounded the
  throttle anchors by reading the just-built provider on disk
  before drafting; did not trust the report's prose alone.
- **Cat 3 `create_file` banned / verify writes** — brief
  written via Desktop Commander, verified post-write (line
  count + section-header grep + byte/SHA).
- **Cat 5 make-software-calls-don't-punt** — the throttle
  shape/homing/constants calls made by Claude; only the
  kill-visibility scoping surfaced (operator agreed).
- **brief-drafting skill** — full ritual: confirm job →
  pre-flight grounding → surgical-fix shape → draft → surface
  calls → operator approval → lock + fingerprint.
- **Session-42 forward-routing rule** — S156 triage shape
  confirmed before close.
- **Visualizer** — timeline rendered inline (diagram module)
  to confirm the cool-off shape; not a file.

## Open items

Pointer-only — full detail in `current_state.md`. New/changed
this session:
- **Login-throttle brief — LOCKED**, awaiting out-of-session
  Code execution. Report lands at
  `dr029/auto_login/login_throttle_report.md`.
- **Auto-login report — TRIAGED clean.** Config-to-set named
  (operator-side); deploy + $5 lay pending operator.
- **is_self coordinated-removal brief** — still queued,
  drafts after auto-login + throttle confirmed live.

## Open items out (closed/advanced)

- Auto-login report triage (S155 primary) — DONE (clean).
- Login-throttle brief drafting — DONE (locked).

## Session close state

- Root: clean, no phantom files.
- New artefact: `dr029/auto_login/login_throttle_brief.md`
  (locked contract). No scratch-promotion needed (the brief
  IS the assembled artefact; nothing left
  drafted-but-unassembled).
- `current_state.md`: rotated to S155 close.
- `v3_build_picture.md`: updated (accounts-setup stream moved
  — auto-login triaged, throttle brief now the
  awaiting-Code item).
- `standing_instructions.md`: not touched (no instruction
  edits this session).
- `.close_out_backups/`: `SESSION_156_opening_prompt.md`
  written; stale `SESSION_155_opening_prompt.md` swept.
- No dev servers stood up (pure Chat triage + drafting).
- Project knowledge base: governance folder auto-syncs.

## Forward routing — CONFIRMED WITH OPERATOR

**Operator runs Code out-of-session** against the locked
throttle brief (Code prompt provided this session).
**Session 156 (Chat)** reads
`dr029/auto_login/login_throttle_report.md`, triages it
(inventory pass), confirms suites green + anchors clean, and
confirms no new operator config beyond the auto-login
report's. With auto-login + throttle both in, the operator
sets credentials, deploys v3 live, and runs the $5 lay test.
The is_self coordinated-removal brief is the remaining
accounts-setup tail after that. Confirmed via Tim's "Lock
it, provide prompt for code, then close please."
