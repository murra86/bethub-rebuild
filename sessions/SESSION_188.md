# Session 188 — concurrency fix TRIAGED CLEAN, accounts
# fault class CLOSED; a second same-class fault (Finding 1)
# surfaced and routed to the live sweep

**Opened:** 2026-06-25 10:50 ACST.
**Closed:** 2026-06-25 11:27 ACST.
**Tool routing:** Claude Chat — open ritual + auto-triage of
Code's out-of-session fix report against the locked brief. No
code edited in Chat; no artefact authored (a triage session).
Code's concurrency fix ran out-of-session before this open.
**Governing DRs:** DR-021 (Adelaide time); DR-031 (SQLite WAL
tech stack — the connection fix sits on it); DR-030 (module
boundary); DR-027/028 (two-database); settlement byte-identity
(`9e07a75d…`).

---

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-25 10:50 ACST.
- Close: same command → 2026-06-25 11:27 ACST.
- Same-workday open (~32 min after the S187 close at 10:18);
  ~37 min active session. No split triggers.

## Pre-flight checks (S188 open)

Clean open, no anomalies. Drift-check passed: current_state,
SESSION_187, and v3_build_picture all carried the matching
S187-close stamp (2026-06-25 10:18 ACST). Folder root clean;
`.close_out_backups/` held only SESSION_188_opening_prompt.md
(the expected Phase-2 carry; the stale S187 prompt was removed
at the S187 close as recorded). Both conditional renders fired
(build picture + open-items delta). Per the S187 operator
directive, S188 AUTO-TRIAGED the fix report straight after the
open ritual — no wait, no confirmation prompt.

## Session shape

A single-arc triage session. The open ritual ran, then S188
auto-triaged Code's `db_connection_concurrency_fix_report.md`
against the locked `db_connection_concurrency_fix_brief.md`.
The triage came back CLEAN — every gate the brief set held —
and surfaced one material new finding (a second, separate
expression of the same fault class on a different set of
screens) that was out of scope to fix and is routed to the
operator's pre-cutover live-validation sweep. No production
code was edited in Chat; no brief or scope artefact was
authored. The session closed with the operator going to
re-launch v3 and run the usability sweep, bringing results to
S189.

## What was delivered

**1. Concurrency fix report — TRIAGED CLEAN, accounts fault
class CLOSED.** Read Code's report against the locked brief.
Every gate held:

- **Baseline gate passed** — HEAD `2329604`, dirty 69,
  settlement SHA `9e07a75d…40d4a3`, both fault anchors present
  as stated. No drift; proceeded. (Code also disambiguated a
  second `settlement.py` in `clients/betfair_client/v1/` — a
  different file, SHA `73f0561b…`, correctly left untouched.)
- **The sweep (§A) is complete and PROVEN, not asserted** —
  every connection path enumerated and empirically classified.
- **The accounts fault is fixed** — proven on two independent
  harnesses (in-process TestClient threadpool + a live uvicorn
  server with 24 concurrent httpx clients). The three screens
  that threw 500s — `/api/v1/accounts`, `/api/v1/books`,
  `/api/v1/racing/accounts` — now return 24×200 clean under
  concurrency, pre-fix 9–23×500.
- **Regression guard red-before / green-after** — the new
  `tests/ui/api/test_connection_concurrency.py` fires 24
  simultaneous requests through the real providers (no
  dependency overrides — genuine threadpool fan-out, the thing
  a sequential TestClient loop can't reproduce and the reason
  the 1184-suite missed the class). Shown failing on the
  unmodified code (62×500 of 72) then green after the fix.
- **Bet-safe** — settlement byte-identical pre/post
  (`9e07a75d…40d4a3`), no schema change, no contact with the
  settlement / provisional paths.
- **Full suite green** — `uv run pytest` → 1188 passed, 1
  xfailed, 0 failed (baseline 1184 → +4 passed, +1 xfailed).
- **Dirty tree clean** — count 69 unchanged, porcelain
  byte-identical; both anchor files fall inside already-
  untracked entries. No git state-changing command.

The racing log-panel account picker — the core-workflow risk
that made this a pre-cutover must-fix — is one of the three
screens now proven clean.

**2. The fix mechanism — a sound, well-reasoned deviation
from the brief's literal default (Claude's territory, recorded
for the file).** Code fixed at the storage layer
(`store/repositories/accounts.py`, a named §5 anchor) — a
per-method connection mirroring the proven-safe bet storage —
rather than the brief's literal default (drop racing.py's
`@lru_cache` + a per-request generator dependency). Two stated,
proven reasons, both inside the brief's §5.2 latitude clause:
(a) the running app actually wires the accounts storage via
`composition.py`'s singleton, not racing.py's `@lru_cache`
(**Finding 2**) — and composition.py is not a §5 anchor, so
fixing the storage class is the only lever that reaches the
production path from within the allowed anchors; (b) a
per-request connection created in a FastAPI dependency is
*itself* cross-thread-unsafe (**Finding 1** — see below), so
the brief's default would have inherited that defect. Fixing at
the storage layer neutralises every wrapper at once, so
racing.py was intentionally left untouched (now safe by virtue
of the storage fix). No operator call — sound dev-lead
reasoning, latitude was granted, both conditions met.

**3. Finding 1 — a second, separate expression of the same
fault class, OUT OF SCOPE, routed to the live sweep (the one
operator-facing surface this session).** The sweep disproved
the brief's "safe" pre-classification of the per-request
`get_db_connection` path: FastAPI resolves the connection in
one worker thread (dependency resolution) and uses/closes it in
another (the endpoint body), so under concurrency it hits the
same cross-thread 500. Proven on the live server. It's the same
fault class as the accounts singleton, expressed per-request
rather than process-wide. It affects any screen firing
concurrent reads through `get_db_connection` — the promos
catalogue, the racing log-context, and the W12/W13 derivation
screens. Code correctly flagged-not-chased it (§5.2 scoped the
fix to the accounts path; §9 forbade touching the safe-path
providers) and left an `xfail` test carrying the full finding —
executable evidence that flips to passing the day it's fixed.

**Operator decision surfaced and made:** fix-now-via-follow-up-
Code-brief vs run-the-sweep-and-see-what-trips. Operator chose
the sweep first (cheaper; which live screens fire enough
concurrent reads to trip it in practice is exactly what the
sweep answers). If a screen trips, we draft the follow-up brief
then with the real symptom in hand; if nothing trips, it's
post-cutover cleanup.

**4. Live-validation sweep posture set.** The operator goes to
re-launch v3 and walk the full workflow as a usability run —
Accounts → Log Bet panel → Log Past Bet → conversion hinge →
BetLog → live Betfair lay. Brief tightenings agreed: the
Accounts screen + log-panel picker are already fixed (a repeat
failure there is a *different* problem and gets flagged as
such); flag anything off, not only load errors (the
connection bug's tell is a screen erroring on first open);
collect issues and triage at the end rather than stopping the
sweep each time.

## Standing-instruction adherence check

- **Cat 1 (lead with the call; plain language; escalate-to-
  detail flagged):** honoured — the triage verdict (class
  closes, clean) led; Finding 1 was flagged "deserves a little
  detail" before the explanation.
- **Cat 1 (inventory-first cadence on long technical reports):**
  honoured — the report was inventory-triaged gate-by-gate
  (baseline, sweep, fix, guards, verification, no-touch), then
  classified by operational impact: Finding 1 surfaced (affects
  the live sweep), Finding 2 + the mechanism deviation handled
  silently as Claude's territory.
- **Cat 1 (don't surface dev-lead calls unless a decision is
  needed):** honoured — the storage-layer mechanism deviation
  (Finding 2) was noted compactly as "why the fix is robust,"
  not enumerated for review; the one genuine decision (sweep-
  first vs follow-up-brief-now) was surfaced and made.
- **Cat 1 (silent open ritual; combined brief output):**
  honoured — Steps 1–5 ran silently; the recap + both
  conditional renders + the triage came as one output.
- **Cat 1 (calendar-calibrated open):** honoured — same-workday
  tight recap (32 min after S187 close).
- **Cat 2 (auto-triage straight after open, no confirmation):**
  honoured — the S187 directive followed exactly.
- **Cat 3 (Desktop Commander; verify every write; uv run pytest
  noted in the triage):** honoured — all reads + the close-out
  writes via Desktop Commander, chunked, verified on disk.
- **Cat 5 (software calls are Claude's, made not punted):**
  honoured — the mechanism-deviation verdict and the Finding 1
  routing recommendation were made, not punted; only the one
  consequence-bearing decision went to the operator.

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in Session 188:**
- Concurrency fix report auto-triage (S188 primary) — CLEAN;
  the cross-thread accounts-connection fault class CLOSED. ✅

**New / promoted for Session 189:**
- **Finding 1 — the `get_db_connection` cross-thread class** (a
  second, per-request expression of the same fault on the
  promos-catalogue / racing-log-context / W12–W13 derivation
  screens). Routed to the live-validation sweep: observe-which-
  trips → follow-up Code brief only if a live screen trips.
  Carries an `xfail` evidence test in the suite.
- **S189 primary: triage the operator's live-validation sweep
  results** — the operator runs the sweep between sessions and
  brings the findings to S189 open.

**Carried to Session 189:**
- Pre-cutover live-validation sweep — operator-run between
  sessions (Accounts → Log Bet panel → Log Past Bet →
  conversion hinge → BetLog → live Betfair lay).
- Launcher brief (F9/F10 + F12 + rebuild-if-source-newer) —
  still queued; the stale-bundle trap (S187) is the extra
  motivation.
- Accounts-screen enhancement (remove "My own account" +
  auto-fill cluster/platform) — scope when picked up.
- Racing-API placings backfill + nightly results-sync fix —
  own parallel brief.
- W16 cutover scoping (after the briefs land).
- Parking-lot (unchanged from S187).

**Carry-forward sensitivity flags:**
- **Bet-safety hard rule — CLEAN.** No code touched in Chat
  this session. The fix Code ran held the line — settlement
  byte-identical (`9e07a75d…`), no schema change, a
  connection-lifetime fix only, no contact with settlement /
  `apply_manual_operator_resolution` / `provisional.py`.
- **Finding 1 is NOT a settlement risk** — it's a connection-
  lifetime fault on read endpoints; if it trips, the symptom is
  a screen erroring on load, never a wrong settlement.
- **v2 is never modified** — the repo under fix is bethub-v3
  only.
- **finish-position gap does NOT touch live settlement** —
  confirmed S174, re-confirmed S179.
- **v2 DB corruption** — confined to regenerable tables;
  betting data intact; jump-start-only to retirement.

## Session close state

- Rebuild folder root: clean, no phantom v2 files. No new
  artefact authored this session (a triage session — the fix
  report Code produced out-of-session already lived at
  `interface_triage/db_connection_concurrency_fix_report.md`).
- v3 repo (`bethub-v3`): unchanged by Chat this session. Code's
  out-of-session fix changed `store/repositories/accounts.py`
  (per-method connection) + added
  `tests/ui/api/test_connection_concurrency.py`; HEAD
  `2329604`, dirty 69, settlement `9e07a75d…` all unchanged
  (both anchor files sit inside already-untracked entries).
- current_state.md rotated to S188 close (2026-06-25 11:27
  ACST).
- v3_build_picture.md UPDATED (interface-refinement stream
  moved — accounts concurrency fault class CLOSED + Finding 1
  surfaced and routed to the live sweep); stamp bumped to
  2026-06-25 11:27 ACST.
- standing_instructions.md unchanged this session (no new or
  edited instruction).
- .close_out_backups/: stale SESSION_188_opening_prompt.md
  removed; SESSION_189_opening_prompt.md written.

## Forward routing — CONFIRMED WITH OPERATOR

The operator's explicit close instruction: "Close it up and I
will commence next session with the test results." So S188
closes now; the operator re-launches v3 between sessions and
runs the pre-cutover live-validation usability sweep; S189
opens on triaging those sweep results. If a screen tripped the
Finding-1 connection fault, S189 drafts the follow-up Code
brief against the real symptom; otherwise Finding 1 parks to
post-cutover cleanup. The launcher brief and W16 cutover
scoping remain queued behind the sweep.

---
*Session 188 record. Closed 2026-06-25 11:27 ACST.*
