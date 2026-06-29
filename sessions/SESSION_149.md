# Session 149 — go-live validation: live data path PROVEN; real ⚡ lay blocked on v3 accounts setup (Option B locked)

**Opened:** 2026-06-14 06:38 ACST.
**Closed:** 2026-06-14 08:23 ACST.
**Tool routing:** Claude Chat throughout, but atypical — this was
a live-environment triage session, not a planning/brief session.
Heavy Desktop Commander use against the live v2 + v3 codebases and
running dev servers (read-only inspection: lsof, curl, grep, code
reads; one operator-run token-mint script). No governance artefacts
authored beyond close-out. No code edits by Chat.
**Governing DRs invoked:** DR-021 (Adelaide anchors), DR-031 (v3
tech stack — credentials/config env model), DR-027/028 (two-DB
split — relevant as accounts setup becomes a cutover dependency).

## Anchor

```
# Session-open:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-06-14 06:38 ACST

# Session-close:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-06-14 08:23 ACST
```

## Pre-flight checks

Open ritual ran silent per `bethub-session-open` (ninth
consecutive clean). Required reads completed (`current_state.md`,
`standing_instructions.md` in full, `project_context.md`,
`SESSION_148.md`). Pre-flight directory listing clean: 13 root
`.md` + `openapi.json`, all directories present,
`.close_out_backups/` held only `SESSION_149_opening_prompt.md`
(expected).

**Drift-check: clean.**
- (a) `current_state.md` "Last updated" matched `SESSION_148.md`
  "Closed:" (2026-06-13 17:21 ACST).
- (b) `SESSION_148.md` present, non-empty (195 lines).
- (c) `v3_build_picture.md` updated at S148 close; render
  condition TRUE — build picture rendered at open.

New-workday open (next calendar day, after 4am) — longer recap.
Operator opened mid-task with a live snag, so orientation was
kept tight and the session moved straight into triage.

## Session shape

Live go-live validation triage — the shape `current_state.md`
flagged as the S149 branch ("if the operator hit snags during
go-live, S149 triages those first"). The operator started the
W17.1 §3 runbook between sessions, hit the mock dry run showing
v2, and opened S149 on that. The session became a step-by-step
walk through the runbook against the live environment, surfacing
and clearing a chain of environment/wiring issues, reaching a
genuine milestone (live Betfair data flowing into the v3 racing
page), then hitting a hard blocker (no accounts in v3) that
turned the session into a routing decision. Closed on a locked
decision (Option B) and a clean stopping point.

## What was delivered

**1. Mock dry run snag diagnosed — port collision (not a bug).**
The runbook's "open localhost:5173" landed on v2 because v2's
own dev server already held 5173; v3's Vite frontend had
auto-bumped to 5174. v3 backend (uvicorn) was up on 8000 as
specified. Fix: open localhost:5174. Confirmed via lsof + cwd
inspection (5173 → bethub-v2/frontend; 5174 → bethub-v3/ui/web).

**2. Mock-mode scope clarified — log panel needs a selected
race.** Operator saw "no bet logging panel" in mock mode. Read
the racing page code (`routes/Racing.tsx`): the log panel,
odds table, and ⚡ are all gated on a selected market, and mock
mode deliberately serves no races. So mock mode can only prove
the page renders + the empty-state placeholder ("Pick a race
from the sidebar to start") — it cannot exercise the log panel,
account picker, or quick-lay. Runbook §3.2's "you should see the
account picker / quick-lay" list is not reachable in mock mode
as built.

**3. Live credentials seeded by reusing v2's login.** Live mode
needs a Betfair session token. Established empirically that v2
authenticates via username + password against
`identitysso.betfair.com/api/login` (interactive, no cert),
minting and caching its own token — which is why v2 "just always
works" and why there is no stored token to copy. v3, by
contrast, reads a static `app_key` + `session_token` from a JSON
file and has no auto-login. Resolved for today by a one-off
script (`/tmp/bethub_mint_token.py`) that imports v2's own
`BetfairClient.get_token()`, reuses the v2 app key, and writes
`~/.config/bethub/betfair_credentials.json` (chmod 600). Operator
ran it; nothing sensitive printed. Verified file present, both
fields set.

**4. Live "no markets" diagnosed — CORS block (real find).**
After switching to live mode the page showed "no markets", then
"Failed to fetch". Backend was confirmed serving today's real AU
races on :8000 (Healesville greyhounds, Devonport thoroughbreds,
real market IDs, ~10:39 first jumps). Root cause: v3 backend's
CORS allow-list defaults to `http://localhost:5173` only
(`ui/api/config.py`), so the browser on :5174 was blocked — and
this also masked itself in mock mode (a blocked fetch renders
identically to "no races" in the sidebar). Fixed by
`export BETHUB_CORS_ORIGINS='["http://localhost:5173","http://localhost:5174"]'`
+ backend restart (env_prefix `BETHUB_`, pydantic-settings JSON
list parse).

**5. MILESTONE — live Betfair data flowing into the v3 racing
page.** After the CORS fix, races populated and prices ticked
live. This is the first time v3's racing operational core — the
home of ~95% of the operation's profit — has talked to live
Betfair markets. The core technical unknown of the racing build
(does the live data path work end to end) is now answered: yes.
Some cosmetic UI roughness noted; triaged as polish, not a gate.

**6. BLOCKER — v3 has no accounts, and no way to add them.**
The real ⚡ lay (§3.4) could not proceed: `/api/v1/racing/accounts`
returned 0 books / 0 accounts / 0 accounts-at-book. v3's DB is
empty (expected — clean start, no v2 backfill). Confirmed there
is no operator-facing path to register books/accounts in v3:
frontend routes are only Racing / Health / Provisional, no
account-creation POST endpoints exist, and the only seed script
is `seed_promos.py`. So standing v3 up for real use needs an
accounts-setup capability that is not built.

**7. DECISION — Option B locked.** Accounts setup becomes the
next workstream and the first concrete dependency of W16 cutover
(v3 cannot be used daily until it can hold the operator's books
and accounts). The $5 lay test folds into that work, run against
the operator's real Betfair account once registered. Option A
(minimal one-account seed just to finish the lay test now) was
declined — the data-path validation already de-risked the build,
so there is no pressure to force the lay test ahead of proper
accounts setup.

## Standing-instruction adherence check

- **Cat 1 silent open-ritual — CLEAN** (ninth consecutive,
  S141–S149). Single combined output, zero step narration. (Some
  light orientation framing appeared while pivoting to the live
  snag, but no step headers.)
- **Cat 1 calendar-calibrated recap** — honoured (new-workday;
  kept tight because the operator opened mid-task on a snag).
- **Cat 1 build-picture conditional render** — honoured
  (rendered at open; streams had moved at S148 close). 29
  consecutive clean S120–S149.
- **Cat 1 plain language for a non-technical operator** —
  honoured throughout the triage. Port collision, CORS, token
  auth, and the accounts blocker were all framed in real-world
  terms (doors/ports, "v2 just always works", empty picker), no
  unexplained jargon.
- **Cat 1 make-software-calls-don't-punt / surface only
  operator calls** — honoured. All diagnosis (lsof, code reads,
  curl, CORS env fix, mint script) was handled as Claude's
  territory; only the genuinely operator-facing call (Option A
  vs B — a cutover-shaping routing decision) was surfaced.
- **Cat 2 anchors / reads / pre-flight / drift-check** —
  honoured at open and close.
- **Cat 3 Desktop Commander discipline** — honoured. All work
  via Desktop Commander (the only filesystem/process tool here);
  write-script-to-/tmp pattern used for the mint script; no
  `create_file`; verify-after-write on the credentials file and
  session record.
- **Cat 3 verify-empirically** — honoured heavily and load-
  bearing this session: every diagnosis was confirmed against
  the live environment (process cwd, raw API responses, CORS
  header presence, accounts counts) rather than inferred.
- **Bet-safety (hard rule) — honoured.** No live order placed.
  The session stopped at read-only; the real ⚡ lay was deferred,
  not executed. Claude placed nothing and triggered no Betfair
  order path.
- **Credential-handling discipline** — honoured. Claude did not
  print, echo, or enter any secret values; the operator ran the
  mint script himself; verification used booleans/counts only.

## Open items in (carry to S150)

Pointer-only — full detail in `current_state.md`.

- **Accounts-setup workstream (NEW) — S150 primary.** Scope the
  way books/accounts get into v3 and draft the build brief. The
  first real W16 cutover dependency. Operator calls needed at
  scoping: pull accounts across from v2 vs set up fresh; which
  books to bring; setup screen vs one-time seed.
- **W16 cutover** — still the next major routing decision, now
  with accounts-setup named as its first dependency.
- **v3 auto-login (Code item)** — give v3 v2's self-refreshing
  username+password login so tokens stop expiring every ~12h.
  Folds into the accounts/settings build. Until then, live mode
  needs a fresh token (re-run `/tmp/bethub_mint_token.py`).
- **Runbook patches (W17.1 §3)** — three, carried for whoever
  next edits the runbook: (i) §3.2 note that v2 holding :5173
  bumps v3 to :5174 (read the terminal for the real URL); (ii)
  §3.2 "you should see account picker / quick-lay" is not
  reachable in mock mode as built; (iii) live steps need the
  CORS origin widened to the bumped port.
- **v3 dev CORS default (Code item)** — defaults to :5173 only,
  so v3 breaks the moment it runs alongside v2 (which is exactly
  the cutover situation). Widen dev CORS or pin ports. Part of
  the broader "v3 must expect coexistence with v2" theme.
- **Sidebar empty-vs-error (UI polish)** — a blocked/failed
  fetch renders identically to a legitimate "no races"; worth a
  distinct error state so a wiring failure can't masquerade as
  an empty card list.
- **UI roughness on the live racing page** — cosmetic bugs noted
  during live smoke; collect on first real-use feedback, fold
  into the settings-area / polish cadence.
- Parking-lot carries unchanged: F4 liability-cap UI + default;
  F6 cross-AAB FB-deploy guard; calculator rethink (Excel-shaped);
  cross-account spot-check view; greyhound operational constraint
  verification; `cascaded_at_settlement_state` closed-enum
  revisit (W8); §2.4 Fix 4 cadence dependency; Betfair API
  membership tier (awaiting BetWatch).

## Open items out (closed/advanced S149)

- **W17 live data-path validation — ✅ DONE.** Live Betfair
  markets + ticking prices confirmed in the v3 racing page. The
  core racing-build unknown is resolved.
- **W17.1** — dropped from the build picture this close per the
  one-session carry rule (closed clean S148).
- **Go-live debrief (the S149 primary)** — ✅ complete: the
  debrief surfaced the validation outcome (data path good, lay
  blocked) and produced the Option B routing decision.

## Session close state

- **v2 + v3 codebases** — untouched by Chat (read-only triage).
- **Running processes (operator-side, between-sessions note):**
  v3 backend was left running on :8000 in **live** mode holding
  a Betfair session, v3 frontend on :5174, v2 still up. Operator
  may Ctrl+C the v3 dev servers when done; nothing depends on
  them staying up.
- **New file on disk:** `~/.config/bethub/betfair_credentials.json`
  (outside the repo, chmod 600, token good ~12h then harmlessly
  stale). Throwaway one-off: `/tmp/bethub_mint_token.py`.
- **`current_state.md`** — rotated to S149 close.
- **`v3_build_picture.md`** — updated (W17.1 dropped; W17 →
  data-path-validated, real-lay-pending-accounts; new
  Accounts-setup stream added as next-up and first W16
  dependency; current-session detail rewritten).
- **`.close_out_backups/`** — `SESSION_150_opening_prompt.md`
  written; stale `SESSION_149_opening_prompt.md` swept.
- **No edits** to `decisions.md`, `standing_instructions.md`,
  `governance.md`, or other canonical truth. Option B is recorded
  as a workstream/routing decision (current_state + this record +
  build picture), not a new DR; if accounts setup warrants a DR,
  that is a scoping-session call at S150.

## Forward routing

**Confirmed with operator** ("Close here"; Option B chosen
explicitly). S150 is a **Claude Chat** scoping session: settle
the accounts-setup workstream (v2-pull vs fresh, which books,
screen vs seed) and draft the build brief. A **Claude Code**
session then builds against the locked brief; the v3 auto-login
fix folds in. The $5 lay test runs as a natural part of that
work, against the operator's real Betfair account once it is
registered in v3.

## Close-out notes

Clean, productive triage session with a real milestone and a
clean stop. The chain — port collision → mock-mode scope →
credential reuse → CORS → live data → accounts blocker — was
worked end to end in plain language, every step confirmed against
the live environment. The headline is that v3's racing core now
talks to live Betfair; the honest second headline is that v3
can't be used for real until it can hold accounts, which is now
the named front edge of cutover. No split trigger fired
(~1h45m, no day-rollover, no fatigue, context fine); normal
close.
