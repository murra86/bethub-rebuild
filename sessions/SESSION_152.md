# Session 152 — accounts-setup built, validated end-to-end, and revision-scoped

**Opened:** 2026-06-16 16:05 ACST
**Closed:** 2026-06-16 21:51 ACST
**Tool routing:** Claude Chat (triage, live click-through validation
via Desktop Commander, research, brief drafting, governance). Claude
Code executed the original accounts-setup build out-of-session; a
revision is now commissioned for the next Code run.
**Governing DRs:** DR-021, DR-022, DR-027/028, DR-030, DR-031, DR-032,
DR-013.

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → `2026-06-16 16:05 ACST`.
- Close: `TZ=Australia/Adelaide date` → `2026-06-16 21:51 ACST`.

## Pre-flight checks (open)

Drift-check clean: `current_state.md`, `SESSION_151.md`, and
`v3_build_picture.md` all stamped `2026-06-16 15:56` (S151 close).
Root listing clean — no phantom files. Same-workday open (9 minutes
after S151 close). `.close_out_backups/` held the expected
`SESSION_152_opening_prompt.md` only.

## Session shape

A long, multi-phase Chat session. It opened by clearing Code's
pre-flight confirmation to proceed with the accounts-setup build, then
triaged Code's completed report (clean — all scope, all green, real DB
untouched). The substantive middle was a live, hands-on click-through
validation of the built screen via Desktop Commander, which surfaced
and resolved a chain of run-the-app problems before the screen would
render and function. It closed on two operator design calls
(remove `is_self`; cluster/platform as dropdowns), the desktop research
to define those lists, a documented account-health/extraction strategy
framework, and a locked revision brief.

## What was delivered

1. **Cleared Code to build, then triaged the report.** Code's
   pre-flight confirmation was a faithful read of the locked brief
   (all 9 endpoints, status codes, files, hard limits) — cleared.
   Its completed report triaged clean: full scope built, pytest
   942→956 (+14), vitest 86→89 (+3), all green, prod build succeeds,
   only the 10 named files touched, git untouched, zero Betfair. Real
   v3 DB independently confirmed empty (0/0/0) and never written.

2. **End-to-end click-through validation (the residual §7 check).**
   Stood up the v3 backend (uvicorn on a throwaway DB) + frontend and
   drove the screen in the browser. Confirmed the three sections,
   add/list/archive/close, the 409 "already registered" path, and
   cross-origin persistence all work. The original build was sound;
   the friction was all in *running* it.

3. **Resolved a chain of launch blockers** (all real findings):
   - **White screen** — the v3 dev server (`npm run dev`) ships
     component code referencing `$RefreshSig$` without the React
     Fast Refresh preamble: a vite-8 / `@vitejs/plugin-react`
     incompatibility. Worked around by running the **production
     build via `vite preview`** (no Fast Refresh).
   - **404 on loads, then on adds** — the production build uses the
     `.env.production` API base, which is **empty by design**
     (same-origin deploy story). Rebuilt with
     `VITE_API_BASE_URL=http://localhost:8000` so the built app
     reaches the local backend cross-origin; CORS (widened to
     :5173/:5174 in the build) already permits it. Verified preflight
     + POST both 200/201 with correct ACAO headers.

4. **Two operator design calls (→ the revision):**
   - Remove the `is_self` "my own account" field entirely.
   - Book `ownership_cluster` + `platform` become constrained
     dropdowns. Operator defined "platform" as the shared white-label
     interface (and, as research confirmed, the shared **risk
     engine**).

5. **Desktop research → locked option lists.** Six white-label
   platforms (BetMakers, GenerationWeb, Punterstech, BetCloud,
   ApolloTech, BetEngine) + "Custom"; major-owner clusters. Full
   book→platform map captured. Operator declined to review the lists
   ("trust your judgement") — locked as drafted with PlayUp/NextBet
   and PointsBet flagged "verify owner" inside the sheet. Cadence
   rule (operator-confirmed): **no periodic review; research a
   genuinely unknown book at registration time** to confirm
   relatedness.

6. **Account-health / extraction strategy framework — DOCUMENTED.**
   The protect-vs-harvest framework (separate registration timing
   from exploitation intensity; open related accounts early while the
   identity is clean; stagger exploitation; major-owner pairs =
   protect/keepers, small same-platform books = harvest/disposable).
   Written to `dr029/accounts_setup/account_health_strategy_note.md`
   and added as a memory trigger to resurface when the account-health
   workstream opens.

7. **Artefacts produced:**
   - `dr029/accounts_setup/account_health_strategy_note.md`
   - `dr029/accounts_setup/cluster_platform_signoff.md` (locked lists)
   - `dr029/accounts_setup/accounts_setup_revision_brief.md` (LOCKED;
     drop `is_self`, cluster/platform dropdowns via a shared options
     endpoint, both stay optional TEXT, unknown values → 422)
   - A Code handoff prompt for the revision (provided at close).

## Standing-instruction adherence

- **Cat 1 build-picture render** — streams moved at S152 (accounts
  built + validated; revision locked) ⇒ render TRUE at S153 open.
- **Cat 1 tone/formatting** — honoured; surfaced operator decisions,
  detail held in artefacts.
- **Cat 3 verify-empirically** — heavily exercised (DB state, CORS
  preflight, served bundle base, route registration all confirmed by
  direct probe, not assumption). Also caught a close-out write-target
  slip (see below).
- **Cat 3 DB read discipline (DR-013)** — real DB read-only via
  `start_process` Python; never copied.
- **Cat 5 division of labour** — technical detail (build mechanics,
  validation constants, endpoint shape) handled autonomously; only
  the two design calls + cadence surfaced to operator.
- **Bet-safety hard rule** — CLEAN. Zero live orders; all
  click-through on a throwaway DB; real DB untouched.
- **No standing-instruction file edits** this session (new rules
  captured as open items / opening-prompt; promote to
  `standing_instructions.md` at S153 if operator wants them formal).

## Close-out note — write-target slip (recovered)

At close, the session record and the three `dr029/accounts_setup/`
artefacts were first written with the generic `create_file` tool,
which targets the container filesystem, not the Mac — so they were
absent from the project. Step 11 post-close verification caught it
(the `ls` showed them missing). All four were re-written via Desktop
Commander to the Mac and re-verified present. **Lesson for future
sessions:** use Desktop Commander (`write_file` / `edit_block`) for
all `/Users/tim/...` writes; the generic `create_file` / `str_replace`
/ `view` tools operate on the container, not the Mac. Captured in the
S153 opening prompt's filesystem note.

## Open items

Pointer-only — full detail in `current_state.md`. New this session:
accounts-setup REVISION (Code) + triage; the vite-8 dev-server finding
and same-origin launch model (carry-forward); the unknown-book
research rule; the launch/packaging deliverable; the bet-time
same-owner/same-platform warning enhancement.

## Open items out (closed/advanced)

- Accounts-setup build — BUILT + CLICK-THROUGH VALIDATED.
- `is_self` removal + cluster/platform dropdowns — design locked;
  revision brief locked.
- Account-health/extraction framework — documented + memory-triggered.

## Session close state

- Root: clean, no phantom files. Three new artefacts under
  `dr029/accounts_setup/` (re-written to the Mac after the slip).
- Dev servers: **stood down**; throwaway DB + `/tmp` scratch removed;
  ports :8000/:5173 clear.
- `current_state.md`: rotated to S152 close (Desktop Commander).
- `v3_build_picture.md`: updated (accounts-setup stream moved).
- `.close_out_backups/`: `SESSION_153_opening_prompt.md` written;
  stale `SESSION_152_opening_prompt.md` swept.
- Project knowledge base: governance folder auto-syncs (no operator
  action needed).

## Forward routing — CONFIRMED WITH OPERATOR

Operator runs the accounts-setup **revision** in an out-of-session
Claude Code session (handoff prompt provided at close). **Session 153**
(Chat) triages `accounts_setup_revision_report.md`, re-runs the
built-app click-through, closes the accounts-setup workstream, then
drafts the **auto-login** brief. The $5 lay test runs once both
accounts-setup and auto-login land and v3 is deployed. Confirmed via
operator's "good to proceed" + "I just need the prompt for code and we
can close."
