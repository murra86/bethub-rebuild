# Session 153 — accounts-setup revision triaged; is_self removal reframed and confirmed; auto-login routed next

**Opened:** 2026-06-16 22:33 ACST
**Closed:** 2026-06-16 22:43 ACST
**Tool routing:** Claude Chat (revision-report triage,
operator decision, forward routing, close). Claude Code
executed the accounts-setup revision out-of-session before
this session opened.
**Governing DRs:** DR-021, DR-022, DR-027/028, DR-030,
DR-013.

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → `2026-06-16 22:33 ACST`.
- Close: `TZ=Australia/Adelaide date` → `2026-06-16 22:43 ACST`.

## Pre-flight checks (open)

Drift-check clean: `current_state.md` and `SESSION_152.md`
both stamped `2026-06-16 21:51` (S152 close);
`v3_build_picture.md` stamped same. Root listing clean — 12
expected `.md` files, all expected dirs, no phantom files
(`external_api_resources.md` + `openapi.json` are the known
API-resource files; `.DS_Store` benign). `.close_out_backups/`
held the expected `SESSION_153_opening_prompt.md` only.
Same-workday open (42 min after S152 close). Code's
`accounts_setup_revision_report.md` confirmed present — the
triage target had landed.

## Session shape

A short, focused triage session. Read the five orientation
reads, rendered the build picture (streams moved at S152),
then ran the inventory pass on Code's accounts-setup revision
report. One operator call surfaced and was resolved; forward
routing confirmed; closed for the night.

## What was delivered

1. **Triaged the accounts-setup revision report (clean).**
   Code's report came back one-of-two: §5.2 (constrained
   dropdowns) BUILT + verified; §5.1 (is_self removal) HALTED
   at the discipline gate and surfaced as a finding. The
   inventory pass classified five items — only one needed an
   operator call.
   - **Dropdowns — done.** Cluster + platform are now
     pick-lists (9 clusters, 7 platforms, verbatim from the
     sign-off sheet), both still optional TEXT, off-list
     non-empty values rejected 422 via a shared
     `GET /v1/books/options` endpoint feeding both the screen
     and the validator (can't drift). Suites green:
     pytest 956→960 (+4), vitest 89→90 (+1). tsc + eslint
     clean.
   - **Bet-safety — CLEAN.** Real v3 DB confirmed empty
     (0/0/0) read-only; main `bethub.db` byte-unchanged. Zero
     Betfair/live calls. (The `-shm` sidecar mtime ticked from
     the read-only WAL-index map — benign, no data written.)
   - **422 deprecation warning** (now 4) — Claude's territory,
     parked as pre-existing project-wide cleanup. No operator
     call.

2. **The one operator call — is_self.** Code's repo-wide grep
   (38 hits / 25 files) proved the "my-account" flag is NOT
   confined to the setup screen: the **racing log panel's
   account picker reads it live** (`racing.py:769`,
   `racing.ts:176`, two racing test files), and it's a
   `NOT NULL` schema column inserted by ~10 downstream test
   suites + carried by the shared domain/repository. Code was
   right to STOP (the brief named "racing page" as the exact
   trigger) rather than half-remove it.
   - **Operator decision:** accounts just need a name — if the
     name is Tim's, he knows it's his. **No mine/household
     distinction is required, anywhere.** So the S152
     "remove is_self" call STANDS — and now extends to the
     racing picker too. Removal is safe (v3 data empty → no
     migration backfill) but is a coordinated cross-surface
     change (accounts surface + racing picker + domain +
     schema column-drop + downstream suites), so it needs its
     own small Code brief rather than the surgical edit
     originally scoped.

3. **Forward routing confirmed with operator.** Two Code
   briefs now queued for accounts-setup's tails: (a) the
   is_self coordinated removal, (b) auto-login (the v2 login
   port). Operator confirmed **auto-login first** — it's what
   unblocks the $5 lay test; the is_self removal is cosmetic
   cleanup that loses nothing by waiting. S154 drafts the
   auto-login brief.

## Standing-instruction adherence

- **Cat 1 inventory-first cadence** — honoured: inventory pass
  on Code's report, each item classified by operational
  impact, only the is_self call surfaced to operator.
- **Cat 1 brevity / decision-first** — honoured: led with the
  one call; clean items handled in a tight list; detail held
  in the report.
- **Cat 1 build-picture render** — rendered at open (streams
  moved at S152). Streams moved again this session ⇒ render
  TRUE at S154 open.
- **Cat 3 verify-empirically / DR-013** — Code's DB-empty +
  byte-unchanged checks read, not assumed; report's grep
  evidence inspected directly.
- **Cat 5 division of labour** — the is_self question was
  surfaced as an operational call (does the racing picker need
  mine/household), not a code-shape call. Technical detail
  (endpoint shape, validator wiring) handled as Claude's
  territory.
- **Session-42 forward-routing rule** — forward routing
  (auto-login first) confirmed with operator before close.
- **Session-3 split-trigger** — fatigue signal fired
  ("close for the night"); close kept lean, no extra
  artefacts, both briefs deferred to future sessions.
- **No standing-instruction file edits** — the S152
  carry-forward rules (unknown-book research-at-registration;
  bet-time same-owner/platform warning) remain unpromoted;
  Tim has not asked to formalise them. Carried, not written.

## Open items

Pointer-only — full detail in `current_state.md`. New/changed
this session:
- **is_self removal reframed** — confirmed remove-everywhere;
  now a coordinated cross-surface Code brief (was a surgical
  accounts-only edit). Brief not yet drafted.
- **Auto-login brief** — confirmed next (S154 drafts it).

## Open items out (closed/advanced)

- Accounts-setup revision triage — DONE (dropdowns built +
  verified green; is_self resolved as a decision).
- is_self design question — RESOLVED (remove everywhere; no
  mine/household distinction needed).

## Session close state

- Root: clean, no phantom files. No new artefacts written
  this session (triage + decision only; no brief drafted, so
  no scratch-promotion needed).
- `current_state.md`: rotated to S153 close (Desktop
  Commander).
- `v3_build_picture.md`: updated (accounts-setup stream moved
  — dropdowns landed; is_self reframed; auto-login routed).
- `.close_out_backups/`: `SESSION_154_opening_prompt.md`
  written; stale `SESSION_153_opening_prompt.md` swept.
- No dev servers stood up this session (pure triage); nothing
  to stand down.
- Project knowledge base: governance folder auto-syncs (no
  operator action needed).

## Forward routing — CONFIRMED WITH OPERATOR

**Session 154 (Chat)** drafts the **auto-login** brief — port
v2's self-refreshing username+password Betfair login so v3
tokens stop expiring (~12h). Then, a later session drafts the
**is_self coordinated-removal** brief (accounts surface +
racing picker + domain + schema column-drop + downstream
suites; safe — v3 data empty). The $5 lay test runs once
accounts-setup's tails land (auto-login is the real
unblock) and v3 is deployed live. Confirmed via operator's
"auto-login first … sounds good" + "let's close for the
night and pick up tomorrow".
