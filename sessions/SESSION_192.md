# Session 192 — placings-backfill report auto-triaged; backlog
# quota-wall surfaced; placings-trickle brief locked + Code released

**Opened:** 2026-06-25 22:14 ACST
**Closed:** 2026-06-25 22:43 ACST
**Tool routing:** Claude Chat (report triage + operator digest +
routing + brief drafting). Code commissioned out-of-session once: the
placings-trickle brief locked + read-back confirmed + released this
session (execution carries to S193).
**Governing DRs:** DR-021 (Adelaide time), DR-033 (data-source roles
— the reason placings recovery is analytical/background, not
live-urgent), DR-027/028 (operational/analytical boundary —
untouched; the trickle is all capture-side).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-25 22:14 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-25 22:43 ACST.
- ~29 min wall-clock; well under the ~3h soft split trigger.
  Same-workday open (~19 min after S191 close). No day rollover.
  No split trigger fired.

## Pre-flight checks (open ritual)

Clean open. current_state, SESSION_191, and v3_build_picture all
carried the matching 2026-06-25 21:55 ACST S191-close stamp (no
drift). Root folder clean (extra `.md` files all live reference
artefacts, no phantoms). `.close_out_backups/` held exactly the
expected `SESSION_192_opening_prompt.md`. Directory listing settled
the routing immediately: `placings_backfill_report.md` was present —
the operator ran the Code session between sessions — so the S192
primary (auto-triage) was GO. Same-workday tight open; the full
build-picture table was held (operator saw it 19 min prior at S191
close — re-rendering would be ritual noise), the one genuine delta
(report landed → primary executable) folded into the triage.

## Session shape

A triage-then-commission session, single clean arc. Auto-triaged
Code's `placings_backfill_report.md` straight off the open ritual (no
confirmation gate, per the S191 forward routing). The triage surfaced
that the forward fix landed but the historical backlog did NOT
recover — quota-blocked, not fix-failed — and that the real bug was
deeper than the brief assumed. Delivered the operator digest in plain
gambling terms, then worked the routing decision through three
options with the operator. The operator chose the automated
backlog-trickle (recover off leftover daily quota, recent data always
first, self-stopping), explicitly framing reliability over speed and
"use what I already pay for, just extract it properly." Drafted +
locked the trickle brief via the brief-drafting skill, triaged Code's
read-back (faithful + grounded), and released. Closed on the standing
auto-triage forward route.

## What was delivered

1. **`placings_backfill_report.md` — AUTO-TRIAGED + digest produced.**
   Report read in full. Verdict: the forward fix LANDED and is
   mechanism-verified (the nightly job now selects recent dates
   first, bounded to ~15 days), but **the bug was deeper than the
   brief assumed** — not "stamp-drop-out" (dates leaving the sync set
   once stamped) but **quota-starvation-by-ordering**: the Racing API
   has a daily request quota (~13–14 date-fills/day), and the old
   unbounded, oldest-first `IS NULL` set burned that quota on
   already-complete March dates, starving the recent dates at the
   tail (last night: 14 filled / 101 zeroed). Code chose the
   brief-permitted alternative (bounded recent-first window) over the
   literal union recipe — the union would have added 0 dates and
   fixed nothing — a sound, flagged deviation. **Recovery was
   quota-blocked**: 2 of 117 dates recovered (2026-06-20 fully;
   2026-06-25 partial/today), ~114 leftover (2026-03-01 → 2026-06-24
   minus 06-20), purely quota-gated, `sync_day` proven to fill (June
   20: 0 → 1,384 finishing positions). Digest delivered in plain
   terms, leading with the call (fix sound going forward; historical
   gap still empty and won't self-heal; bet-safety clean).

2. **Routing decision — automated backlog-trickle CHOSEN.** Worked
   three options with the operator: let-it-ride / slow-manual-recovery
   / look-at-the-feed-tier. Operator's reasoning: wants the data,
   won't pay more (the data is all inside the current subscription —
   it just needs extracting properly), doesn't mind how long it takes
   within reason (analytics is a way off). Landed on the **automated
   trickle**: the nightly job spends its *leftover* daily quota on the
   oldest missing dates after the recent window is filled — hands-off,
   self-healing, self-stopping. Confirmed reliability-over-speed as
   the design priority. Expected closure ~2 weeks of nightly runs
   (~10 backlog dates/night against the shared quota); the report's
   per-night log makes the true rate readable after 2–3 nights.

3. **Placings-trickle brief — DRAFTED + LOCKED + Code read-back
   confirmed + RELEASED.** `placings_trickle_brief.md` (rebuild root,
   234 lines, 11 sections). A surgical standing change to one VPS
   anchor (`scripts/backfill_race_metadata.py`): a new backlog
   selector (oldest-first, thoroughbred-incompleteness keyed — NOT
   `subscription_synced_at IS NULL`, which F2 proved permanently
   unbounded; floored at 2026-03-01) + a backlog pass wired into the
   argless nightly path after the recent pass (leftover-only,
   stop-on-quota-wall, idempotent via `sync_day`, self-healing,
   self-stopping, don't-retry-dead-dates guard) + per-night logging
   (`BACKLOG PASS: … remaining_backlog_dates=K` → `BACKLOG COMPLETE`).
   §5.0 baseline STOP gate confirms the post-S192 substrate before
   building. Recent-first is a structural §9 hard rule. Capture-side /
   analytical only; auto-settle/v3/settlement/money-path
   named-and-excluded; bet-safety clean by construction; dirty-tree
   discipline carries the S192 forward-fix edit as intended substrate.
   Four operator-relevant calls surfaced at hand-off; the one real
   decision (older-month ~20% residual — fold in or exclude) resolved
   as EXCLUDE when the operator read the read-back against the brief
   as written. Code's read-and-confirm gate came back FAITHFUL and
   GROUNDED (bet-safety reasoned from DR-033 + the DR-027/028 boundary,
   not parroted; correctly reconciled oldest-first-within-backlog vs
   recent-first-priority). RELEASED with the go-line. Code runs
   out-of-session.

## Standing-instruction adherence check

- **Cat 1 brevity / decision-maker framing** — held. Led with the
  call each turn; flagged "this deserves a little detail" before the
  triage digest.
- **Cat 1 plain language / no jargon** — held. Digest used real-world
  terms ("the feed company caps how many days you can pull per day";
  "the recent days got starved at the back of the queue").
- **Cat 1 silent open/close ritual** — held. Open produced one
  combined orientation/triage block; close ran silent to this record +
  opening prompt. (Minor: a couple of light framing lines appeared at
  open — within tolerance, no step-by-step headers.)
- **Cat 1 same-workday calibration** — held. Tight open; full
  build-picture table held back as ritual noise (operator saw it 19
  min prior).
- **Cat 1 don't-surface-dev-lead-calls-by-default** — held. Surfaced
  the four operator-relevant brief calls + the one real decision;
  held detection-mechanism / persistence detail as Claude's.
- **Cat 2 brief-drafting skill** — held. Surgical-fix shape; calls
  surfaced at hand-off; brief verified on write; Code prompt +
  read-and-confirm gate provided unprompted; read-back triaged before
  release.
- **Cat 2 always-provide-Code-prompt** — held. Provided at hand-off +
  the release go-line after the faithful read-back.
- **Cat 3 empirical verification** — held. Drafted against the freshly
  triaged report's grounded anchors (HEAD, dirty-tree state, function
  signature, service config); no stale-anchor assumptions.
- **Cat 3 create_file banned / verify writes** — held. Brief written
  via Desktop Commander; verified on write (234 lines, header
  spot-checked).
- **Cat 5 make-the-call** — held. Made the brief's software calls
  (backlog detection latitude, stop-on-wall, logging shape) and
  surfaced the operator-relevant ones; recommended exclude on the
  residual call with reasoning.
- **Bet-safety hard rule — CLEAN.** No code touched in Chat. The brief
  is capture-side / analytical by construction; settlement and
  placement untouched. No contact with any money path.

## Open items

Pointer-only — full detail in `current_state.md`.

**New / promoted for S193:**
- Triage Code's `placings_trickle_report.md` (S193 primary, auto on
  open).

**Carried to S193:**
- Consolidated frontend fix brief (independent parallel start).
- Launcher brief (capture-data provisioning + F9/F10/F12 +
  rebuild-if-source-newer).
- Settlement-worker brief — standalone.
- Promo-seed item — standalone, small.
- W16 cutover scoping.
- Parking-lot (unchanged — incl. now the older-month ~20%
  finish-position residual top-up, excluded from the trickle brief).

## Open items out (closed this session)

- **Triage `placings_backfill_report.md` + operator digest (S192
  primary)** — DONE. Forward fix sound (mechanism-verified); backlog
  recovery quota-blocked (2/117, ~114 leftover); bug reframed as
  quota-starvation-by-ordering; bet-safety clean. ✅
- **Leftover-backfill routing** — DONE. Automated backlog-trickle
  chosen over manual recovery / paying for more quota. ✅
- **Placings-trickle brief** — DRAFTED + LOCKED + read-back confirmed
  + RELEASED. ✅ (Execution + triage carry to S193.)

## Session close state

- `sessions/SESSION_192.md` — this record.
- `current_state.md` — rotated to S192 outcomes; stamp 22:43.
- `v3_build_picture.md` — header + interface-refinement row updated
  (report triaged; trickle brief locked + released); stamp 22:43.
- `placings_trickle_brief.md` — LOCKED (234 lines).
- `standing_instructions.md` — untouched (no new instruction this
  session).
- `decisions.md` — untouched this session (still carries the S191
  DR-029 amendment + S180 DR-032 amendment; KB re-upload still
  pending from S191).
- `.close_out_backups/` — stale S192 prompt removed; S193 opening
  prompt written.

## Pending operator-side actions

- **Run the placings-trickle Code session** — paste the released
  go-line; Code executes `placings_trickle_brief.md` end-to-end and
  produces `placings_trickle_report.md`. **Run from the logged-in Mac
  session** (the ssh-agent must be available — the VPS key is
  passphrase-protected).
- **Re-upload `decisions.md`** to the bethub-rebuild Project KB —
  carries the S191 DR-029 amendment AND the S180 DR-032 amendment. KB
  copy stale. (Carryover from S191.)
- **Re-upload `standing_instructions.md`** to the Project KB
  (carryover — includes the S189 §4 live-integration rule).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** jump-start-only on request (to retirement).

## Forward routing (CONFIRMED with operator)

The operator confirmed: "close with auto triage next session." S193
**auto-triages** `placings_trickle_report.md` straight off the open
ritual (no confirmation gate, consistent with the established
pattern). On a clean triage → confirm the mechanism (recent-first,
leftover-only, self-stopping) + that the first in-session increment
behaved → then it's hands-off background (the operator lets the
nightly runs trickle the backlog closed over ~2 weeks; a later
session spot-checks the log rate, `remaining_backlog_dates` trending
to 0). Then back to the pre-cutover queue: consolidated frontend fix
brief (independent parallel start) / launcher capture-data
provisioning → settlement-worker brief → promo-seed item → W16
cutover. The operator runs the trickle Code session between S192 and
S193.
