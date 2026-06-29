# Session 187 — account-ref triage CLEAN + a cross-thread DB-connection fault found, fixed-brief handed

**Opened:** 2026-06-25 09:08 ACST.
**Closed:** 2026-06-25 10:18 ACST.
**Tool routing:** Claude Chat — report triage + live diagnosis
via Desktop Commander (read-only probes against the v3 repo +
live DB + throwaway mock instances) + fix-brief drafting. Code
commissioned out-of-session (the locked brief + ready-to-paste
prompt handed at close; Code's read-and-confirm gate returned
faithful and was released).
**Governing DRs:** DR-021 (Adelaide time); DR-031 (SQLite WAL
tech stack); DR-030 (module boundary); DR-027/028 (two-database);
settlement byte-identity (`9e07a75d…`).

---

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-25 09:08 ACST.
- Close: same command → 2026-06-25 10:18 ACST.
- Same-workday open (~11 min after the S186 close at 08:57);
  ~70 min active session. No split triggers.

## Pre-flight checks (S187 open)

Clean open, no anomalies. Drift-check passed: current_state,
SESSION_186, and v3_build_picture all carried the expected
S186-close stamps (all at 2026-06-25 08:57). Folder root clean;
`.close_out_backups/` held only SESSION_187_opening_prompt.md
(the Phase-2 carry). Both conditional renders fired (build
picture + open-items delta). S187 opened in a WAIT posture per
the S186 close instruction — held for operator confirmation
before triaging.

## Session shape

A triage-then-validate session that turned into a fault hunt.
Three arcs ran end-to-end: (1) the account-reference format
class triaged CLEAN and CLOSED; (2) a stale frontend bundle was
rebuilt so the new screens actually serve; (3) a live-validation
attempt surfaced a NEW concurrency fault on the Accounts screen,
which was diagnosed to root cause, proven, and handed to Code as
a locked fix brief. No production code was edited in Chat (all
fixes route to Code); the only state Chat changed on the v3 repo
was rebuilding the gitignored frontend bundle.

## What was delivered

**1. Account-ref format-class fix — TRIAGED CLEAN, class
CLOSED.** Read Code's `account_ref_format_class_fix_report.md`
against the locked brief: all ~10 known display-path failures
green, the three FK-on regression guards in, full suite 1184
passing, settlement byte-identical (`9e07a75d…`), dirty tree
unchanged except named anchors. The two Code-flagged items (a
dead-import removal inside a named-anchor file; one racing test
left on the old id-shape, its live path pinned by a hex guard)
were sound dev-lead calls, no operator action. Live free-bet
crediting is now proven written AND visible against real
accounts — the promo-on-bet / credit-in arc is complete.

**2. Stale frontend bundle rebuilt (launcher stale-build
trap).** The launcher (`BetHub.command`) only builds the
frontend if `ui/web/dist/index.html` is MISSING — it never
rebuilds on stale source. The served bundle was built 21 June;
source had moved to 23 June (BetLog, Log Past Bet, PromoBar /
Free Bet button, Log Bet panel, race screen). Ran
`npm run build` in `ui/web`; bundle now current (09:32), tsc
clean, 103 modules, nothing tracked disturbed (dirty 69),
settlement SHA unchanged. The backend always loads fresh on
launch, so today's account-ref fix came for free. This trap
recurs after every frontend change until the launcher gets its
"rebuild-if-source-newer" upgrade (the pending launcher brief).

**3. Cross-thread DB-connection fault — DIAGNOSED, PROVEN,
brief HANDED.** Live-validation of the Accounts screen threw
repeated 500s (add + load, accounts + books). Chat traced it
end-to-end: the on-disk code + live DB serve correctly in
isolation (reads, mapper, writes all proven; live DB writable;
the operator's "Tim" account + "BetFair" book already present),
so the fault was concurrency-only. Root cause: the accounts
storage (`store/repositories/accounts.py` ~125) holds one
long-lived `self._conn` and is wired as a process-wide
`@lru_cache` singleton (`_build_default_accounts_storage` in
racing.py). SQLite forbids cross-thread connection use; the API
serves on a worker-thread pool, so any request off the creating
thread 500s. Proven with a concurrency probe: 30 simultaneous
reads → 26 × 500, 4 × 200. NOT caused by the S186 account-ref
fix (it never touched the wiring); pre-existing latent fault,
invisible to the single-threaded test suite. Same singleton also
backs the racing log-panel account picker — a core-workflow
risk, so it's a genuine pre-cutover must-fix.

**4. The fix brief — DRAFTED + LOCKED + HANDED.**
`interface_triage/db_connection_concurrency_fix_brief.md` (325
lines, 11 sections, sha `d747e6d0…`). A SWEEP + surgical fix:
inventory and PROVE every connection path safe/faulty; fix the
one accounts fault (per-request connection, matching the proven
`get_db_connection` pattern); add red-before/green-after
concurrency guards (≥20 simultaneous requests, must use real
threadpool concurrency, not a sequential TestClient loop) on
every affected endpoint; lock the safe paths in with assertions.
Hard limits: settlement byte-identical, no schema change, no
touch to the safe per-request deps or the bet-storage cache,
dirty-tree discipline, single bounded session, §5.0 baseline
STOP gate. Code's read-and-confirm gate came back faithful
(every anchor, the no-touch list, the settlement rule, the gate
restated; correctly flagged the v2-vs-v3 memory note — answered:
operate on bethub-v3 only, v2 is never modified) and was
RELEASED with the ready-to-paste prompt. Code runs
out-of-session.

**5. Parked — accounts-screen enhancement.** The operator's ask
to remove the "My own account" checkbox and auto-fill cluster +
platform from desktop research is a separate frontend +
research-logic scope. Surfaced, parked, noted in the fix brief's
§11 so it's not lost.

## Standing-instruction adherence check

- **Cat 1 (lead with the call; plain language; escalate-to-
  detail flagged):** honoured — triage verdict led; the
  concurrency diagnosis was flagged "deserves a little detail"
  before the explanation.
- **Cat 1 (don't surface dev-lead calls unless a decision is
  needed):** honoured — the two account-ref flags + the fix
  mechanism noted compactly; the one genuine decision (structural
  guard now vs parked) surfaced as a question.
- **Cat 1 (calls-made list at brief hand-off):** honoured —
  three calls surfaced for redirect.
- **Cat 2 (fenced-block ~60–70 char wraps):** honoured — brief +
  Code prompt hard-wrapped.
- **Cat 2 (always provide ready-to-paste Code prompt):** honoured.
- **Cat 3 (Desktop Commander; verify every write; live-DB via
  start_process Python; never copy the DB; uv run pytest noted in
  brief):** honoured — all probes via start_process; brief
  written chunked + verified on disk; throwaway mock instances
  used temp DBs for write tests so live data was never touched.
- **Cat 4 (brief-drafting skill; ground the surface before
  locking; Code read-and-confirm gate):** honoured — full
  codebase connection-surface scan run before drafting; gate
  enforced before release.
- **Cat 5 (software calls are Claude's, made not punted):**
  honoured — fix shape, mechanism, sweep-vs-review-first all made
  and stated; the rebuild was done, not punted.

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in Session 187:**
- Account-ref format-class fix triage (S187 primary) — CLEAN,
  class CLOSED. ✅
- Stale frontend bundle — rebuilt, current. ✅
- Concurrency fault — diagnosed, proven, fix brief drafted +
  locked + handed, Code gate released. ✅

**New / promoted for Session 188:**
- **S188 primary: auto-triage
  `db_connection_concurrency_fix_report.md` straight after the
  open ritual — NO confirmation required** (operator directive at
  S187 close). Success = §A inventory complete, the accounts
  fault fixed, concurrency guards red-before/green-after,
  settlement byte-identical, dirty list clean except named
  anchors.

**Carried to Session 188:**
- Pre-cutover live-validation sweep (operator-run) — resumes
  after the concurrency fix lands (Accounts → Log Bet panel →
  Log Past Bet → conversion hinge → BetLog → live Betfair lay).
- Launcher brief (F9/F10 + F12 + rebuild-if-source-newer) —
  now extra-motivated by the stale-bundle trap hit this session.
- Accounts-screen enhancement: remove "My own account" +
  auto-fill cluster/platform from desktop research — scope when
  picked up.
- Optional structural anti-recurrence guard (CI lint for any
  future endpoint-facing storage holding a thread-bound
  connection) — parked; fold into a follow-up if wanted.
- Racing-API placings backfill — own parallel brief.
- W16 cutover scoping (after the briefs land).
- Parking-lot (unchanged from S186).

**Carry-forward sensitivity flags:**
- **Bet-safety hard rule — CLEAN.** No code touched in Chat. The
  concurrency fix (when Code runs it) must hold the line —
  settlement byte-identical (`9e07a75d…`), no contact with
  settlement / provisional paths; it's a connection-lifetime fix
  only, no schema change. The brief's §9 enforces this.
- **v2 is never modified** — reaffirmed to Code this session
  (its memory flagged v2; the repo under fix is bethub-v3 only).
- **finish-position gap does NOT touch live settlement.**
- **v2 DB corruption** — confined to regenerable tables;
  jump-start-only to retirement.

## Session close state

- Rebuild folder root: clean, no phantom v2 files. New this
  session: `interface_triage/db_connection_concurrency_fix_brief
  .md` (325 lines, LOCKED, sha `d747e6d0…`).
- v3 repo (`bethub-v3`): no tracked file touched; the only
  change was rebuilding the gitignored `ui/web/dist/` bundle
  (09:32). HEAD `2329604`, dirty 69, settlement `9e07a75d…` —
  all unchanged.
- current_state.md rotated to S187 close (2026-06-25 10:18 ACST).
- v3_build_picture.md UPDATED (interface-refinement stream moved
  — account-ref class CLOSED + concurrency fault found and brief
  handed); stamp bumped to 2026-06-25 10:18 ACST.
- standing_instructions.md unchanged this session (no new/edited
  instruction; the auto-triage directive is session-specific
  forward routing, lives in the opening prompt + current_state).
- .close_out_backups/: stale SESSION_187_opening_prompt.md
  removed; SESSION_188_opening_prompt.md written.

## Forward routing — CONFIRMED WITH OPERATOR

The operator's explicit close instruction: "First action next
session is to triage report (no confirmation required — do
straight after open process completed)." So S188 opens, runs the
open ritual, and then AUTO-TRIAGES
`db_connection_concurrency_fix_report.md` immediately — no wait,
no confirmation prompt (distinct from S187's wait posture). On a
clean triage the cross-thread connection fault class CLOSES, and
the operator re-launches and resumes the pre-cutover
live-validation sweep, clearing toward the launcher brief and
W16 cutover scoping.

---
*Session 187 record. Closed 2026-06-25 10:18 ACST.*
