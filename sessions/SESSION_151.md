# Session 151 — accounts-setup build brief drafted + locked; v3 codebase probed; auto-login split to next brief

**Opened:** 2026-06-16 15:20 ACST.
**Closed:** 2026-06-16 15:56 ACST.
**Tool routing:** Claude Chat throughout. A pre-flight
read-only probe of the v3 codebase (Desktop Commander)
followed by build-brief drafting into the rebuild
governance folder. No code edits to v2 or v3. No
governance-truth edits beyond close-out.
**Governing DRs invoked:** DR-021 (Adelaide anchors),
DR-022 (book/account/account-at-book vocab — shapes the
accounts model), DR-027/028 (two-DB split + boundary —
accounts-setup is a cutover/cross-DB moment), DR-030
(v3 module boundaries — the ui→store-direct call),
DR-031 (v3 stack).

## Anchor

```
# Session-open:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-06-16 15:20 ACST
# Session-close:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-06-16 15:56 ACST
```

## Pre-flight checks

Open ritual ran per `bethub-session-open`. **One anomaly
surfaced and was resolved:** the operator said "open
session 152", but the last session on disk was 150 and
`current_state.md` pointed forward to 151 — a
session-number mismatch. Surfaced immediately; the
operator confirmed a miscount and we opened **151**.

Drift-check otherwise clean:
- (a) `current_state.md` "Last updated" matched
  `SESSION_150.md` "Closed:" (2026-06-15 12:44 ACST).
- (b) `SESSION_150.md` present, non-empty (218 lines).
- (c) `v3_build_picture.md` updated at S150 close; render
  condition TRUE — build picture rendered at open.
- The `.close_out_backups/SESSION_151_opening_prompt.md`
  was the **expected** backup of this session's opening
  prompt, not a stale artefact (initial flag corrected
  after reading the S150 record's close-state note).

New-workday open (next calendar day after S150) — longer
recap delivered.

## Session shape

A focused Claude Chat session delivering the
accounts-setup build brief — the S151 primary per
`current_state.md`. Ran a v3 codebase pre-flight probe
first (grounding the brief's anchors empirically), then
drafted and locked the brief. One mid-draft operator call
(split auto-login into its own follow-up brief) reshaped
the scope. Clean single-deliverable session, ~36 minutes
wall-clock, no split trigger — full close with budget
intact.

## What was delivered

**1. v3 codebase probe (pre-flight grounding).**
Located v3 at `/Users/tim/Desktop/Projects/bethub-v3`.
Headline finding: **the accounts data layer is already
built** (W11). The three tables (`accounts`, `books`,
`accounts_at_book`, DR-022 vocab) exist with a full
repository — `SQLiteAccountsStorage` with
create/list/archive/register/close plus the
`RegisterResult` envelope (duplicate + missing-referent
handling). The accounts storage is **already wired into
the API composition root** (`get_accounts_storage`
dependency in `ui/api/routers/racing.py`), and a
read-only `GET /v1/racing/accounts` listing already
exists. DR-030 boundary resolved: `.importlinter` puts
`ui` above `store`, so the API talks to the repository
directly — no `workflows/accounts` layer needed.
Frontend: react-router-dom + react-query; routes in
`ui/web/src/routes/`, per-feature API clients in
`ui/web/src/api/`. The v3 git tree is heavily
uncommitted (the whole build untracked).

**2. Accounts-setup build brief drafted + locked.**
`dr029/accounts_setup/accounts_setup_brief.md` — 364
lines, 14,986 bytes, sha256 `f94017d3a17d2aac`. Universal
11-section spine plus 7 sub-sections in §5. Scope: a new
accounts API router exposing the existing repo CRUD; a
frontend setup screen + route/nav managing all three
entities (add/list/deactivate each); a one-line CORS
widen for v2/v3 coexistence; backend + frontend tests
holding the green baselines. Hard limits exclude
auto-login, the lay test, schema changes, v2
import/seed, a workflow layer, other routers/pages, and
all git operations.

**3. Operator call — split auto-login out.** Originally
scoped (S150) to fold auto-login into the accounts build
as one Code session. The probe showed the data layer was
already built, making this brief a tidy
"endpoints + screen" job; folding auto-login in would
bloat the single Code session (Cat 3 S126 timeout risk).
Operator confirmed the split — accounts-setup this brief,
auto-login the next.

**4. Code handoff prompt produced.** A copy-paste prompt
for the out-of-session Claude Code run: points at the
locked brief, requires read-and-confirm before building,
and carries the discipline (named anchors only, no git,
zero Betfair, surprises become findings, report to the
named path).

## Standing-instruction adherence check

- **Cat 1 silent open-ritual** — surfaced the
  session-number mismatch immediately (correct
  anomaly-surfacing, not silence-for-silence's-sake).
  Otherwise a single combined orientation output.
- **Cat 1 calendar-calibrated recap** — new-workday,
  longer recap. Honoured.
- **Cat 1 build-picture conditional render** — rendered
  at open (streams had moved at S150). Honoured.
- **Cat 1 plain language for a non-technical operator** —
  honoured. Probe findings and the "what is auto-login"
  explanation framed in plain operational terms; brief
  calls surfaced operationally.
- **Cat 1 make-software-calls / surface only operator
  calls** — honoured. The probe surfaced no operator
  call; the brief surfaced the genuine calls (split;
  screen does full lifecycle; no pre-seed) and handled
  technical shape autonomously.
- **Cat 1 call-driven surfacing during brief drafting** —
  honoured. Brief written to disk section-by-section;
  only operator-relevant calls surfaced, not section
  text.
- **Cat 2 anchors / reads / pre-flight / drift-check** —
  honoured at open and close.
- **Cat 3 Desktop Commander discipline** — honoured. All
  filesystem/process work via DC; v3 probed read-only;
  brief written in chunks; verify-after-write (wc + grep
  + sha256). No `create_file`.
- **Cat 3 verify-empirically** — honoured. Brief anchors
  grounded in the live v3 codebase, not memory.
- **Bet-safety (hard rule) — honoured.** Zero Betfair
  calls; the brief explicitly excludes all live work.

## Open items in (carry to S152)

Pointer-only — full detail in `current_state.md`.

- **Accounts-setup Code execution (NEW) — S152 primary.**
  The locked brief awaits an out-of-session Code run;
  S152 triages `accounts_setup_report.md`.
- **Auto-login brief** — draft after the Code-report
  triage. Was folded into accounts; now split out.
- **W16 cutover** — accounts-setup is its first
  dependency.
- **$5 lay test** — waits on accounts-setup AND
  auto-login both landing + live deploy.
- **v3 git tree uncommitted (NEW, light)** — operator
  hygiene; worth a commit for a clean restore point.
- VPS follow-ups (out-of-rebuild, SSH): FK-constraint
  warnings; confirm morning snapshot gap.
- Parking-lot carries unchanged (runbook patches; sidebar
  UI; racing-page UI roughness; F4/F6; calculator
  rethink; cross-account spot-check; greyhound op-verify;
  `cascaded_at_settlement_state` enum; §2.4 Fix 4 cadence;
  Betfair API tier).

## Open items out (closed/advanced S151)

- **Accounts-setup build brief — ✅ DRAFTED + LOCKED.**
- **v3 codebase probe — ✅ DONE.**
- **Auto-login fold-vs-split — ✅ RESOLVED (split).**

## Session close state

- **v2 + v3 codebases** — untouched (v3 read-only probe;
  no edits to either).
- **New file on disk:**
  `dr029/accounts_setup/accounts_setup_brief.md`
  (364 lines, locked).
- **`current_state.md`** — rotated to S151 close.
- **`v3_build_picture.md`** — updated (Accounts-setup →
  `awaiting-code-execution`; brief locked).
- **`.close_out_backups/`** —
  `SESSION_152_opening_prompt.md` written; stale
  `SESSION_151_opening_prompt.md` swept.
- **No edits** to `decisions.md`,
  `standing_instructions.md`, `governance.md`, or other
  canonical truth. Accounts-setup remains a
  workstream/routing matter; no DR warranted this
  session.

## Forward routing

**Confirmed with operator** ("Code handoff please", then
"close please"). S152 is a **Claude Chat** triage
session: read the Code report
(`dr029/accounts_setup/accounts_setup_report.md`),
confirm the accounts screen works end-to-end, then draft
the **auto-login** build brief. **Claude Code** builds the
accounts-setup brief out-of-session in between. The $5 lay
test runs once both accounts-setup and auto-login land and
v3 is deployed live with the operator's real Betfair
account registered through the new screen.

## Close-out notes

Clean single-deliverable session. The build brief was
grounded in a live v3 codebase probe — which materially
de-risked it by revealing the data layer was already
built — then drafted and locked at operator confirmation.
Auto-login split out on a session-budget/timeout-risk
call. No split trigger fired; full close with budget
intact.
