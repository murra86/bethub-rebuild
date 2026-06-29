# BRIEF — Workflow-map integration audit

**Drafted:** Session 189, 2026-06-25 ACST · Chat → Code
(out-of-session)
**Source map:** operator_workflow_map.md (S185, Scope A)

---

## §1 — What this brief is and is not

This is an AUDIT: a classification + provisioning inspection.
It is not a fix, not a measurement battery, not a wiring job.
Single bounded Code session. Surprises become findings in the
report, never blockers, and Code does not chase remediation.
Code does NOT edit any v3 source, does NOT edit the operator
map, does NOT wire or provision anything. Read-only throughout.

## §2 — Why this work exists

The S189 live-validation sweep found that "Log Past Bet" was
built and unit-tested clean at S176, yet has no live data path:
the launcher never sets BETHUB_CAPTURE_DB_PATH and no capture.db
is reachable on the Mac. It read as "done" because its tests
were green against a local fixture. This audit closes that
systemic gap — it classifies every tool-touching activity in
the workflow map by whether it is actually wired AND provisioned
live, so "green-on-fixtures" can never again pass as "done".

## §3 — Pre-reads (Code confirms it has read these before
starting)

Required:
- operator_workflow_map.md (the spine of this audit)
- this brief
- architecture.md (DR-027/028 two-DB line; DR-030 boundaries)
- contracts/vps_client_contract.md (capture.db surfaces)

Reference-only (not required-reads):
- interface_triage/manual_entry_build_report.md (the worked
  example of the exact miss — Log Past Bet)
- current_state.md / sessions/SESSION_188.md (context)

## §4 — System access

- v3 repo /Users/tim/Desktop/Projects/bethub-v3 — READ-ONLY.
- Running v3 app (port 8787) — read-only live inspection
  permitted (curl health/endpoints) to confirm live behaviour.
- Live app process environment — read (ps eww on the running
  uvicorn) to capture launch provisioning.
- BetHub.command launcher — read.
- Operational DB bethub.db — read-only, only if needed to
  confirm a path is live (start_process Python, canonical path,
  never copy the file).
- capture.db / the VPS — NOT required and NOT to be stood up.
  Its unreachability is a finding, not an obstacle to fix.
- Output written to the rebuild folder, NOT the v3 repo.
- All report timestamps Adelaide local (DR-021).

## §5 — The audit, in four passes

### §5.1 Activity inventory
Enumerate every activity and hand-off in the v1 map (Scope A
only): the §3 insurance back-bet loop rows, the §4 conversion
loop rows, the §5 cross-cutting layers (EV column, promo prep,
mark-triggered/settlement, account-health, promo scheduling),
and the §6 named manual re-entry points. Record each activity's
"System underneath" from the map.

### §5.2 Code-wiring (dimension 1)
For each tool-touching activity, trace the real v3 code path
(route → endpoint → workflow → client) and decide whether it
calls a REAL external client or a stub / fixture / TODO.
External systems in scope: Betfair live (betfair_client), VPS
capture (vps_client), operational store (bethub.db). Record the
code anchor (file:line) that proves it.

### §5.3 Launch provisioning (dimension 2 — the one that caught us)
Read BetHub.command and capture the live app's process env. For
each real client found in §5.2, decide whether the live launch
actually supplies what it needs — env vars (e.g.
BETHUB_CAPTURE_DB_PATH, the Betfair credentials path + mode, the
operational DB path), file mounts (capture.db), tunnels (VPS
8400 / SSH), credentials files. Record provisioned / not, and
name the specific missing piece where absent.

### §5.4 Status + drift
Each activity's status is the WORSE of its two dimensions
(code-wiring, provisioning), resolved by the decision table
below. Statuses:

  live-proven          — real client, provisioned, AND an
                         evidenced end-to-end live run (see
                         evidence hierarchy, §5.4a).
  implemented-not-live — feature exists in code but is not
                         operational live. Reason:
                         {fixture-only} and/or {unprovisioned}
                         and/or {evidence-absent}.
  not-wired            — no live path in code (stub / TODO /
                         absent).
  operator-manual      — activity runs outside the tool
                         (AdsPower, soft book, phone); no
                         integration grade applies.

Status decision table (code-wiring × provisioning):

  code-wiring    | provisioning  | status
  ---------------|---------------|---------------------------
  real client    | provisioned   | live-proven IFF evidence
                 |               | clears the bar; else
                 |               | implemented-not-live
                 |               | {evidence-absent}
  real client    | not provided  | implemented-not-live
                 |               | {unprovisioned}
  fixture / stub | provisioned   | implemented-not-live
                 |               | {fixture-only}
  fixture / stub | not provided  | implemented-not-live
                 |               | {fixture-only +
                 |               | unprovisioned}
  no code path   | (n/a)         | not-wired
  outside tool   | (n/a)         | operator-manual

Note the third row: a real-but-stubbed call path that happens to
be provisioned is still implemented-not-live {fixture-only} —
provisioning cannot rescue a path that doesn't call the real
client. "Worse of the two" resolves downward, never up.

Flag any activity where the built code no longer matches the map
(drift), so the map can self-correct.

### §5.4a Evidence hierarchy (what "evidenced end-to-end run"
means)
A live-proven verdict requires evidence that the real external
system was exercised in the live app — not merely that the code
would call it. Accepted evidence, strongest first:

  1. Observed live write/read against the real external system
     — a row written to the live operational DB via the running
     app, or a live Betfair API response captured in app logs /
     network trace at run time. Strongest.
  2. Runtime log line or network request from the running app
     showing the real client round-tripped (request issued +
     non-error response from the real endpoint).
  3. Live endpoint probe through the running app (curl on :8787)
     returning real data sourced from the external system — not
     a fixture, not an empty or error envelope.
  4. Operator-attested live use THIS arc, recorded as such and
     named as operator-attested (weakest standalone; acceptable
     only when 1–3 are impractical to capture, e.g. the phone
     lane).

Static evidence does NOT count: green tests, fixture round-
trips, "the code looks right", or a real client merely being
imported. Where only static evidence exists, the status is
implemented-not-live {evidence-absent}, not live-proven. Code
names which tier (1–4) each live-proven verdict rests on in the
table's hand-off-note column.

## §6 — Sequencing within session
Linear: 5.1 inventory → 5.2 code-wiring → 5.3 provisioning
(needs the client list from 5.2) → 5.4 assignment last. Code may
interleave 5.2/5.3 per activity if cleaner, but 5.4 is last.

## §7 — Success criteria (this is an audit, not a fix)
Done means: every Scope-A activity carries a status with a
proving anchor; every implemented-not-live carries a reason
({fixture-only} / {unprovisioned} / {evidence-absent}); every
real client carries a provisioning verdict; every live-proven
verdict names its evidence tier (1–4); map-drift is flagged.
Known-answer calibration: the audit must independently re-derive
"Log Past Bet" race-lookup as implemented-not-live
{unprovisioned}. If the method does not land that node in that
bucket on its own, the method is flawed and that is the headline
finding.

## §8 — Output spec
Single file: workflow_integration_audit.md (rebuild-folder root).
Structure:
- header: date/anchor, source-map version, one-line method note.
- per-activity table: activity | map ref | system underneath |
  code anchor | code-wiring | provisioning | status | reason |
  hand-off note.
- a "map-drift" section.
- a short "what the method confirmed" note incl. the Log Past
  Bet known-answer check.
Length ~150–300 lines (range, not a hard line; flag if exceeded).
Status vocabulary throughout: live-proven / implemented-not-live
/ not-wired / operator-manual.
Does NOT contain: recommendations, fixes, a remediation plan,
the VPS review, any edit to the operator map, any next brief.

## §9 — Hard limits
- READ-ONLY everywhere. No edit to any v3 source, the operator
  map, or any governance doc.
- No fixes, no wiring, no launcher edits, no env changes, no
  mounts or tunnels stood up. Do NOT stand up capture.db or the
  VPS link "to test" — its absence is the finding.
- No git operations on the v3 dirty tree (no add / commit /
  stash / restore / checkout / reset). Read git status only.
- No scope beyond the v1 map's Scope-A activities. Strategy 2–4,
  sports, the analytics layer — out.
- No remediation proposals — demand side only. The supply-side
  VPS review and any fixes are separate, operator-Claude-routed.
- Single bounded session; if it doesn't fit, deliver partial-
  but-coherent plus a finding, not a continuation.

## §10 — What happens after Code's session
Next operator-Claude session (S190): read
workflow_integration_audit.md, triage it, produce the operator-
friendly digest, and lock the standing rule (a "triaged clean"
verdict must state live-proven / implemented-not-live /
not-wired). Then draft the VPS supply-side review brief,
informed by this demand-side picture. Code does NOT write the
next brief or the friendly version.

## §11 — Cross-references
- Source: operator_workflow_map.md (S185, Scope A).
- Origin: S189 sweep finding (Log Past Bet unprovisioned);
  interface_triage/manual_entry_build_report.md (S176).
- DRs: DR-021 (Adelaide time), DR-027/028 (two-DB line — the
  audit respects the operational/analytical boundary), DR-030
  (module boundary), DR-031 (SQLite WAL).
- Excluded/parked: VPS supply-side review (next); the
  consolidated frontend fix brief (S189 polish items); Strategy
  2–4 workflow mapping.
