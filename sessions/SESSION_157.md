# Session 157 — v3 Betfair credentials set up;
# same-origin serving brief drafted + locked for Code

**Opened:** 2026-06-17 13:32 ACST
**Closed:** 2026-06-17 19:02 ACST
**Tool routing:** Claude Chat (operator-side setup support,
launch-approach decision, brief drafting, governance).
Desktop Commander for all filesystem/process work. No Code
session this session — the serve-frontend brief is locked
for out-of-session Code.
**Governing DRs:** DR-021 (timestamp anchoring), DR-030 (v3
module boundaries), DR-031 (tech stack), DR-029 §5.6
(same-origin deploy story). DR-027/028 noted (W16 cutover
adjacent).

## State at open (rotated from current_state.md)

Entered with the accounts-setup code tail effectively
complete (registration + auto-login + login-throttle all
triaged clean) and S157 framed for the operator-side live
validation (deploy v3 + $5 lay). The session pivoted to
credentials setup and the launch foundation instead — the
validation needs a clean way to launch v3, which surfaced
the launcher as the real next dependency.

## Anchor

- Open: 2026-06-17 13:32 ACST
- Close: 2026-06-17 19:02 ACST
- ~5h30m wall-clock, but the middle was operator-away time;
  active session work (orientation, credentials walk-through,
  launch decision, brief drafting) well under the 3h active
  split trigger. No day rollover, no scope change — full
  close.

## Pre-flight checks (open ritual)

Drift-check clean: `current_state.md`, `SESSION_156.md`, and
`v3_build_picture.md` all stamped 2026-06-17 13:16 ACST (S156
close); accounts-setup had moved at S156 ⇒ build-picture
render fired at open. Root clean — 12 `.md` + 2 API-resource
files + benign `.DS_Store`; `.close_out_backups/` held only
the S157 opening prompt. (Minor: the open-ritual response
carried step-style headers in operator-facing text — the
S114 silent-ritual pattern; noted under adherence.)


## Session shape

An operator-support + brief-drafting session that pivoted
off the planned validation. Three movements: (1) located v2's
Betfair login and set up v3's own credentials file, walked
the operator through it terminal-first (files were hidden, so
terminal was the cleaner route); (2) took the launch-approach
decision — v3 has no launcher today, and the operator wants a
reliable double-click that starts and stops cleanly, having
been bitten by v2's two-piece launch; chose the single-program
same-origin model for reliability (operator delegated the
call); (3) drafted and locked the serve-frontend brief for
Code. No live orders, no governance truth changed beyond
close-out artefacts.

## What was delivered

1. **v3 Betfair credentials set up (operator-side, DONE).**
   Located v2's login at `/Users/tim/Desktop/Projects/
   bethub-v2/.env` (three values: `BETFAIR_USERNAME`,
   `BETFAIR_PASSWORD`, `BETFAIR_APP_KEY`). Created v3's own
   credentials file at `/Users/tim/Desktop/Projects/
   bethub-secrets/betfair.json` (outside the repo, empty
   skeleton written by Claude). Operator populated it via a
   terminal one-liner that copied the three values straight
   from v2's `.env` into the JSON — values moved Mac-to-Mac,
   never through chat, never written by Claude. Operator
   confirmed the result good. This is the credential shape
   v3's auto-login provider consumes (`auto_login_report.md`
   §5: live mode + app key + username + password).

2. **Launch-approach decision — single-program, same-origin
   (reliability call).** v3 currently runs as two pieces (the
   FastAPI engine on `/api/*` and the frontend served
   separately) — the same two-piece fragility that made v2's
   launch flaky. Decided to make FastAPI serve the built
   frontend itself, so v3 runs as one uvicorn process on one
   port. The frontend is already built for this
   (`.env.production` ships an empty API base ⇒ document-
   relative calls ⇒ same-origin), and it is the DR-029 §5.6
   deploy shape pulled forward from W16 cutover. Operator
   delegated the technical call, priority = reliability.

3. **Serve-frontend brief drafted + LOCKED for Code.**
   `dr029/launch/serve_frontend_brief.md` — 291 lines, SHA
   `e6d6dec1e63d`, 11-section spine. Commissions one surgical
   change to `ui/api/main.py` (serve the built frontend
   same-origin with an SPA deep-link fallback, guarded on
   dist-existence so dev/tests are unaffected), a fresh prod
   build, and new automated tests locking the serving
   contract (the "bit more work for reliability" the operator
   okayed). Hard limits: one file + one test module only, no
   git ops (v3 tree fully uncommitted, `main.py` untracked),
   no live Betfair (all verification in mock mode), no
   launcher/icon (that's the next Chat step). Grounded
   empirically before drafting — app object, router type,
   prod API-base, and git tree all read live.


## Standing-instruction adherence check

- **Cat 5 make-the-call / developer-lead** — honoured. Made
  the same-origin reliability call rather than punting the
  technical choice back; surfaced only the operational/
  sequencing dimension (pulling cutover serving forward).
- **Cat 3 verify-empirically** — honoured. Brief anchors
  grounded in live reads (app object in `main.py`, BrowserRouter
  in `App.tsx`, empty prod API base, dirty git tree) before
  drafting, not from memory.
- **bethub-brief-drafting skill** — honoured. Pre-flight
  grounding, 11-section spine, dirty-tree git-hands-off
  discipline, single-file anchor, output spec + hard limits,
  locked + verified post-write.
- **Cat 1 brevity / plain-language / no-jargon-to-operator** —
  honoured. Credentials + launch framing kept in plain terms;
  technical detail held inside the brief artefact.
- **Bet-safety hard rule** — CLEAN. No live orders by Claude.
  Credentials file created but used for nothing this session;
  the brief keeps Code in mock mode end-to-end.
- **Secret-handling** — Claude wrote only an empty skeleton;
  the operator moved the real values Mac-to-Mac himself. No
  secret ever entered chat or was written by Claude.
- **`create_file` banned / verify writes** — honoured.
  Desktop Commander `write_file` throughout; credentials file
  and brief both read back / verified.
- **Tool routing stated** — honoured (Chat vs Code vs
  operator-side named throughout).
- **Cat 1 silent open ritual — MINOR DRIFT.** The open
  response carried "Step 1 / Step 2"-style headers in
  operator-facing text, the same pattern flagged at S114.
  Orientation otherwise combined correctly at the end. Watch
  next open.
- **No standing-instruction file edits** this session.

## Open items

Pointer-only — full detail in `current_state.md`.

**New / promoted for Session 158:**
- Triage Code's `serve_frontend_report.md` (same-origin
  serving change) — S158 primary, gated on Code having run
  the brief out-of-session.
- Build + test the desktop launcher (Chat + Desktop
  Commander) — once the serving change triages clean.

**Carried:**
- Operator-side $5 lay validation — now sensibly sequenced
  *after* the launcher (clean launch → validate live).
- is_self coordinated-removal brief — still pending, drafts
  after validation confirms v3 live.

## Open items out (closed this session)

- v3 Betfair credentials setup — ✅ DONE (file created +
  populated by operator, confirmed good).

## Session close state

- Rebuild folder root: clean — 12 `.md` + 2 API-resource
  files; no phantom files.
- New artefact dir: `dr029/launch/` (holds the locked
  serve-frontend brief; will hold its report + launcher
  notes).
- WIP: none open.
- `.close_out_backups/`: stale `SESSION_157_opening_prompt.md`
  removed; `SESSION_158_opening_prompt.md` written.
- `sessions/`: `SESSION_157.md` written (this file).
- v3 build picture: updated (launch/packaging stream added).
- Operator-side: v3 credentials file now live at
  `/Users/tim/Desktop/Projects/bethub-secrets/betfair.json`.

## Forward routing

**Confirmed with operator.** Session 158 opens by triaging
Code's `serve_frontend_report.md` (the same-origin serving
change). On a clean report, S158 proceeds to build and test
the desktop launcher with the operator (single uvicorn
process, pinned port, live mode + credentials file, clean
startup/shutdown, browser-open on health-check). The $5 lay
validation follows the launcher. If the report surfaces
blocking findings, those become S158's triage and a follow-up
brief. The serve-frontend brief is locked and handed to Code
out-of-session by the operator between sessions.
