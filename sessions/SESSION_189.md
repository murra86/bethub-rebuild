# Session 189 — live-validation sweep triage; Log Past Bet
# found unprovisioned; workflow-integration audit commissioned

**Opened:** 2026-06-25 12:56 ACST
**Closed:** 2026-06-25 18:16 ACST
**Tool routing:** Claude Chat (triage + diagnosis + brief
drafting + governance). Code commissioned out-of-session for
the workflow-integration audit.
**Governing DRs:** DR-021 (Adelaide time), DR-027/028 (two-DB
operational/analytical line), DR-030 (module boundary), DR-031
(SQLite WAL), DR-033 (data-source roles).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-25 12:56 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-25 18:16 ACST.
- ~5h wall-clock (a gap while the operator was away); past the
  ~3h soft split trigger → the consolidated frontend fix brief
  was deferred to S190 rather than pushed through.

## Pre-flight checks (open ritual)

Clean open. current_state, SESSION_188, and v3_build_picture
all carried the matching 2026-06-25 11:27 ACST S188-close
stamp (no drift). Root folder clean; `.close_out_backups/` held
exactly `SESSION_189_opening_prompt.md` (the expected Phase-2
carry). Same-workday open (~1.5h after S188 close).

## Session shape

A triage-and-pivot session. Opened same-workday on the S188
forward routing — triage the operator's pre-cutover live-
validation sweep. The sweep returned no 500s anywhere, which
settled the Finding-1 question (the per-request
`get_db_connection` cross-thread class did not trip live → it
parks to post-cutover; the accounts fault class stays closed).

The sweep's headline finding reframed the session. "Log Past
Bet" — built and unit-tested clean at S176 — showed empty,
greyed-out cascade dropdowns. Diagnosis traced it past the
frontend to a backend 500 on the race-lookup feed, then to the
root cause: the feature has no live data path at all. The
`vps_client` capture.db surfaces read a local SQLite *file* via
`BETHUB_CAPTURE_DB_PATH`; the launcher never sets that env var,
no capture.db is mounted or reachable on the Mac, and the VPS
tunnel (port 8400 — an API, not a file) is down. It read as
"done" for ~13 sessions purely on green fixture tests.

That exposed a systemic governance gap, which the operator
named: green-on-fixtures passing as "done", with no tracking of
what is actually wired live. The session pivoted to a fix — a
workflow-integration audit (demand side) ahead of the planned
VPS review (supply side) — and locked the governing rule.

## What was delivered

1. **Live-validation sweep — TRIAGED.** No 500s; Finding 1 did
   not trip live and parks to post-cutover. The accounts fault
   class stays closed. The rest of the sweep dump (banner
   freeze, odds-box "1" rejection, Betfair-modal fill-message
   confusion, log-panel close/clear, free-bet amount buttons,
   the delete key, redundant free-bet return-type) is small
   frontend polish — captured for a single consolidated fix
   brief (queued, drafted S190).

2. **Log Past Bet root-caused live.** Health 200; meetings
   lookup 500 on both dates; running app process env confirmed
   carrying the Betfair credentials path + live mode but NOT
   `BETHUB_CAPTURE_DB_PATH`; `BetHub.command` never sets it;
   `mdfind` found no capture.db on the Mac; no sshfs/mount; the
   8400 tunnel unreachable. v2 reaches the VPS via the 8400 API
   (a port-forward of an HTTP API), whereas v3's `vps_client`
   was built to read a local file — so the file-access path was
   never stood up. Verdict: implemented-not-live
   {unprovisioned}. Pre-cutover blocker for manual entry; none
   of v3's "pull from the VPS" features can work live until the
   link is built.

3. **Workflow-integration audit — DRAFTED + LOCKED + HANDED.**
   `workflow_integration_audit_brief.md` (224 lines, 10,285
   bytes, sha `451026087d252c25`). A read-only Code audit that
   classifies every Scope-A workflow-map activity by live-
   integration status across TWO dimensions — code-wiring (real
   client vs stub) AND launch-provisioning (does the launcher
   actually supply the env/mount/tunnel/credentials each client
   needs). Status = the worse of the two. Taxonomy: live-proven
   / implemented-not-live {fixture-only | unprovisioned |
   evidence-absent} / not-wired / operator-manual, resolved by
   a decision table, with a defined evidence hierarchy for
   "live-proven" and a known-answer calibration that must re-
   derive Log Past Bet as implemented-not-live {unprovisioned}.
   Output: companion artefact `workflow_integration_audit.md`
   (operator map left untouched as operator-domain truth). Code
   prompt provided. Closest precedent: S33 source-review brief.

4. **New Cat 4 standing instruction — LOCKED (governance
   event).** "Classify done by live-integration status, not
   green tests." Added to `standing_instructions.md` §4. This
   is the systemic anti-recurrence rule for the miss that
   surfaced this session. Operator-side action: re-upload
   `standing_instructions.md` to the Project KB.

5. **current_state.md + v3_build_picture.md rotated/updated.**
   Build-picture header + interface-refinement row carried to
   S189 (sweep done; Finding-1 park; VPS-wiring finding; audit
   commissioned).

## Standing-instruction adherence check

- **Cat 1 brevity / decision-maker framing** — held. Led with
  the call each turn; flagged "this deserves a little detail"
  before the one long VPS-wiring explanation.
- **Cat 1 plain language / no jargon** — held. Root cause
  explained as "the launcher hands the app your Betfair login
  but not the capture-data path".
- **Cat 1 don't-surface-dev-lead-calls-by-default** — held on
  the audit brief hand-off; surfaced only the four genuine
  design calls (companion-vs-in-place, taxonomy, two-dimension
  audit, scope bound), and only because the operator was
  shaping the governance fix.
- **Cat 2 brief-drafting + always-provide-Code-prompt** — held.
  Brief drafted via the skill (S33 precedent), locked, verified
  on write (line/byte/sha captured), Code prompt provided
  unprompted.
- **Cat 3 empirical verification** — held throughout. Every
  claim about the live state (env, 500s, mounts, tunnel) came
  from Desktop Commander probes, not memory. The map and the
  three governance files were re-read from disk before editing.
- **Cat 3 create_file banned / verify writes** — held. All
  writes via Desktop Commander; brief + record verified.
- **Cat 4 ground "already built" claims (S178)** — directly
  exercised: the sweep grounded a "built clean" claim against
  live behaviour and found it unprovisioned. The new Cat 4 rule
  is the verdict-side complement.
- **NEW Cat 4 rule authored this session** — flagged as a
  governance event (below). Edit applied at close rather than
  mid-session (deferred deliberately, operator-endorsed).

## Open items

Pointer-only — full detail in `current_state.md`.

**New / promoted for S190:**
- Triage Code's `workflow_integration_audit.md`; produce the
  operator-friendly digest.
- Draft the VPS supply-side review brief (informed by the
  audit's demand-side picture).
- Draft the consolidated frontend fix brief (the S189 sweep
  polish dump).

**Carried:** Finding-1 follow-up (now parked post-cutover);
launcher brief (now must also wire capture.db provisioning);
the full parking-lot (unchanged).

## Open items out (closed this session)

- **Live-validation sweep triage (S189 primary)** — DONE. No
  500s; Finding 1 resolved (parks post-cutover); polish dump
  captured; the one blocker (Log Past Bet unprovisioned) root-
  caused and routed to the audit.
- **Finding 1 — live-trip decision** — RESOLVED: did not trip,
  parks to post-cutover cleanup.

## Governance event (structural-drift surfacing rule, Cat 2)

A new standing instruction was authored at close, not during
substantive work — a deliberate, operator-endorsed deferral
("lock it at close"). `standing_instructions.md` §4 gains:
"Classify done by live-integration status, not green tests."
The `bethub-session-open`/`-close` skills do not need a review
trigger (the rule adds a verdict obligation, not a procedural
step). Operator-side action carried: re-upload
`standing_instructions.md` to the bethub-rebuild Project KB.

## Session close state

- `sessions/SESSION_189.md` — this record.
- `current_state.md` — rotated to S189 outcomes; stamp 18:16.
- `v3_build_picture.md` — header + interface-refinement row
  updated; stamp 18:16. (Pre-existing cosmetic staleness — the
  "Streams (Session 171)" heading and the bottom "Current
  session's activity (S171)" block — left as-is; not load-
  bearing for the open render.)
- `standing_instructions.md` — new Cat 4 rule appended.
- `workflow_integration_audit_brief.md` — locked (224 lines).
- `.close_out_backups/` — stale S189 prompt removed; S190
  opening prompt written.

## Forward routing (CONFIRMED with operator)

S190 triages Code's `workflow_integration_audit.md`, produces
the operator-friendly digest, locks the standing rule's
companion check at triage, then drafts the VPS supply-side
review brief (informed by the audit) and the consolidated
frontend fix brief. Then: launcher brief (now incl. capture.db
provisioning) → W16 cutover scoping. The operator runs the
audit Code session between S189 and S190.
