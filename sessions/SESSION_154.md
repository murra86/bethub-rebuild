# Session 154 — auto-login brief drafted and locked

**Opened:** 2026-06-17 08:06 ACST
**Closed:** 2026-06-17 08:30 ACST
**Tool routing:** Claude Chat (pre-flight grounding of v2/v3
auth code, brief drafting, operator calls, lock, close).
Claude Code will execute the locked brief out-of-session.
**Governing DRs:** DR-021 (Adelaide timestamps), DR-030 (v3
module boundaries), DR-031 (tech stack), DR-032 (Betfair
canonical).

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → `2026-06-17 08:06 ACST`.
- Close: `TZ=Australia/Adelaide date` → `2026-06-17 08:30 ACST`.

## Pre-flight checks (open)

Drift-check clean: `current_state.md` and `SESSION_153.md`
both stamped `2026-06-16 22:43` (S153 close);
`v3_build_picture.md` stamped same. Root listing clean — 12
expected `.md` files + the two known API-resource files
(`external_api_resources.md`, `openapi.json`); `.DS_Store`
benign; no phantom files. `.close_out_backups/` held only the
expected `SESSION_154_opening_prompt.md`. New-workday open
(prior close 22:43, fresh open 08:06 next calendar day).

## Session shape

A short, focused Claude Chat brief-drafting session. Read the
five orientation reads, rendered the build picture (streams
moved at S153), then ran the `bethub-brief-drafting` ritual for
the auto-login brief. Pre-flight grounded the actual v2 login
source and v3 auth seam on disk before drafting; two operator
calls surfaced (one delegated to Claude, one bet-safety call);
brief drafted end-to-end, surfaced for review, locked. Closed
with the Code prompt provided.

## What was delivered

1. **Pre-flight grounding of the auto-login port (read-only).**
   Located and confirmed on disk the exact port source and
   destination, rather than trusting documented filenames:
   - **Port source (v2):** `src/services/betfair_client.py` —
     `_login()` (username/password POST to
     `identitysso.betfair.com/api/login`), `get_token()`
     (thread-safe cached token, ~4h validity, re-mint at ~3h
     via a lock), `clear_token()`.
   - **Contract (v3):** `clients/betfair_client/v1/_auth.py` —
     the `AuthProvider` Protocol (`session_token()` +
     `app_key()`), with only a static `MockAuthProvider`
     concrete impl. The real provider was explicitly deferred
     at W2 ("lives outside W2 scope... deferred to v3 build
     proper").
   - **Wire point (v3):**
     `ui/api/dependencies/composition.py` —
     `StaticAuthProvider` (reads a token once at startup, never
     refreshes — the docstring names refresh as "the
     operator's responsibility for the first cut") and
     `build_auth_provider()`.
   - **Config add point (v3):** `ui/api/config.py` `Settings`
     (env prefix `BETHUB_`) — has `betfair_mode`, app_key /
     session_token / credentials_path, REST+JSON-RPC URLs, but
     NO username/password (the static provider never logs in).
   - Confirmed the ~12h static-token expiry (composition.py
     docstring) is the real $5-lay blocker, and that the seam
     means zero call-site changes are needed.

2. **Drafted + locked the auto-login brief.** Written to
   `dr029/auto_login/auto_login_brief.md` (own folder, matching
   the per-deliverable convention). Surgical-port shape
   (Sessions 35/36 precedent). 11 sections; **314 lines, 12,520
   bytes, SHA256 `6a3d78413afd0985`.** Status line flipped
   DRAFT → LOCKED after operator approval. The brief commissions
   Code to: add username/password (+ identity URL) to config;
   build a self-refreshing `BetfairAuthProvider` porting v2's
   login+refresh+lock; wire it into `build_auth_provider()` for
   live mode; preserve the static-token path as a fallback. All
   tested against a FAKE login transport.

3. **Two operator calls.**
   - **Verification approach (bet-safety) — Tim delegated to
     Claude's recommendation, then confirmed.** Code builds +
     tests against a fake login, ZERO live Betfair calls; the
     first real login round-trip is the operator's at live
     deploy. Keeps the W17/W17.1 zero-live-call rule intact; the
     refresh logic (the part that carries bugs) is fully
     testable without network.
   - **Fallback preservation — Claude's call, surfaced.** Kept
     the existing paste-a-token path so nothing currently
     working breaks; v3 auto-picks auto-login when
     username/password are set, falls back to static token
     otherwise. No new mode flag.

4. **Code prompt provided** for the out-of-session run — reads
   the brief + §3 pre-reads, confirms understanding before
   building (Flow 3 discipline), executes §5 in §6 order, hard
   limits restated, report to `auto_login_report.md`.

## Standing-instruction adherence

- **Cat 1 brevity / decision-first** — honoured: led with the
  one job and the one real call; held detail in the brief.
- **Cat 1 new-workday recap + build-picture render** — both
  rendered at open (new workday; streams moved at S153).
- **Cat 3 verify-empirically / DR-013** — grounded every named
  anchor on disk before drafting; did not trust documented
  filenames.
- **Cat 5 make-software-calls-don't-punt** — the fallback +
  timing-port + module-shape calls made by Claude; only the
  bet-safety verification call surfaced (and Tim delegated it).
- **brief-drafting skill** — full ritual: confirm job →
  pre-flight grounding → surgical-port shape → draft → surface
  calls → operator review → lock + fingerprint.
- **Session-42 forward-routing rule** — S155 triage shape
  confirmed before close.
- **Write discipline** — brief written via Desktop Commander,
  verified post-write (line count + section-header grep).

## Open items

Pointer-only — full detail in `current_state.md`. New/changed
this session:
- **Auto-login brief — LOCKED**, awaiting out-of-session Code
  execution. Report lands at `dr029/auto_login/`.
- **is_self coordinated-removal brief** — still queued, drafts
  after auto-login confirmed.

## Open items out (closed/advanced)

- Auto-login brief drafting (S154 primary) — DONE (locked).

## Session close state

- Root: clean, no phantom files.
- New artefact: `dr029/auto_login/auto_login_brief.md` (locked
  contract). No scratch-promotion needed (the brief IS the
  assembled artefact; nothing left drafted-but-unassembled).
- `current_state.md`: rotated to S154 close.
- `v3_build_picture.md`: updated (accounts-setup stream moved —
  auto-login brief locked, now awaiting Code).
- `.close_out_backups/`: `SESSION_155_opening_prompt.md`
  written; stale `SESSION_154_opening_prompt.md` swept.
- No dev servers stood up (pure Chat drafting).
- Project knowledge base: governance folder auto-syncs.

## Forward routing — CONFIRMED WITH OPERATOR

**Operator runs Code out-of-session** against the locked brief
(Code prompt provided this session). **Session 155 (Chat)**
reads `dr029/auto_login/auto_login_report.md`, triages it
(inventory pass), confirms suites green + anchors clean, and
surfaces to Tim exactly what config to set for the first live
login. Once that's in and v3 deploys live, the $5 lay test
runs. The is_self coordinated-removal brief is the remaining
accounts-setup tail after that. Confirmed via Tim's "sounds
fine to me" (lock) + "provide the code prompt and close".
