# Session 108 — W8 burst-review queue brief drafted and locked (618 → 670 lines)

**Title:** W8 burst-review queue UI brief drafted end-to-end and
locked at `dr029/w4_bet_entry/w8_burst_review_queue_brief.md`.
Eight-anchor initial scope expanded to nine after operator round
folded a minimal top-level navigation surface in (was: out, deferred
to follow-up brief). Read + write + UI all covered in one brief —
operator confirmed Option A (single-bigger-brief) over Option B
(read-side-only-then-write-side-second) on the strength that
splitting would ship a half-built queue. Six operator-call items
walked one-per-round in plain operator language: queue refresh
cadence (locked at 3s with future settings panel noted), confirmation
step before action buttons (locked yes), top-level nav (folded in),
runner-name display (nice-to-have format `selection_id. runner_name`),
audit-trail handling (Code must explicitly confirm path taken),
manual-escalation from terminal (out of scope, future fix between
operator and Claude). Brief locked SHA256 `f26b0fb8...`.

Two new open items surfaced and captured: settings-area cadence
control deferred to follow-up brief; greyhound operational constraint
parked as W6.5-layer needs-verification item. One stale anchor
caught in pre-flight (current_state.md named "§2.9 §4.4" as a §2.6
spec read — §2.9 doesn't exist; corrected to actual §3.1, §3.2,
§3.4, §3.5, §4.4 anchors).

**Opened:** 2026-05-08 11:05 ACST
**Closed:** 2026-05-08 11:32 ACST
**Wall-clock:** ~27 minutes active session work. Same-workday
session relative to Session 107 close (10:51 → 11:05 = 14-min gap
at session-108-open).
**Tool routing:** Claude Chat exclusively. Substrate reads
(current_state, standing_instructions, project_context, SESSION_107),
spec reads (`2_6_settlement_race.md` §3.1, §3.2, §3.4, §3.5, §4.4),
W6.5 substrate inspection (storage.py, settlement.py grep + read),
W7 substrate inspection (`ui/api/`, `ui/web/src/api/client.ts`),
brief authoring + edit_block iteration (1 write + 6 edit_block edits
to renumber and incorporate operator decisions), close-out writes.
**Governing DRs invoked:** DR-021 (Adelaide local time — open and
close anchors plus brief's UI display requirements), DR-027 / DR-028
(cross-database boundary — context only at W8), DR-029 (data-layer
fit-for-purpose review, closed Session 78), DR-030 (v3 repo layout
— load-bearing for `ui/api/routers/` and `ui/web/src/routes/`
placement), DR-031 (v3 tech stack with Session 107 amendment —
load-bearing for FastAPI / React / Vite / TanStack Query usage),
DR-032 (canonical reference layer for bet records — context for
queue display fields), DR-022 (book / account / account-at-book
vocabulary — context for queue display fields), DR-019 (derived
state on read — context for time-in-provisional computation).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
`2026-05-08 11:05 ACST`.
Close: same command → `2026-05-08 11:32 ACST`.

Same-workday session relative to Session 107 close (~14-min gap at
session-108-open).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill. Held silent per
Cat 1 (silent session-open ritual); single combined orientation
output delivered at end of ritual.

- Rebuild root: 11 expected governance `.md` files +
  `v3_build_picture.md` + `openapi.json` +
  `external_api_resources.md` + `.DS_Store` + 6 directories. Clean.
- `.close_out_backups/` contained `SESSION_108_opening_prompt.md`
  only (Session 107 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated
  `2026-05-08 10:51 ACST` matched Session 107 close;
  `sessions/SESSION_107.md` present at 327 lines;
  `v3_build_picture.md` last-updated 2026-05-07 15:52 (predates
  Session 107 close — Session 107 record explicitly noted no stream
  movement, correct not drift).
- Same-workday recap delivered at 14-minute gap (tight,
  one-paragraph framing).
- V3 build picture: skip-silent at open (artefact's last-update
  predates Session 107 close — render condition false per skill
  rule).
- Open-items delta: skip-silent at open (no movement between
  Session 107 close and Session 108 open).
- Governing DRs named at open: DR-030, DR-031, DR-032 load-bearing;
  DR-027/028, DR-019, DR-021, DR-022 context.

**Open ritual deviation worth naming.** None. No `bash_tool` reflex.

**Stale anchor caught at pre-flight.** `current_state.md` "Required
reads for Session 108" named `2_6_settlement_race.md` §2.9 §4.4 as
the write-side coherence read. §2.9 does not exist — the §2.6 file's
top-level numbering tops at §5. The actual write-side coherence
material lives in §3 (state machine — §3.1 states, §3.2 transitions,
§3.4 burst-review trigger conditions, §3.5 surfacing contract) and
§4.4 (abandoned race race-wide voiding via related-bets pointer).
Likely a stale carry from a prior file structure. Corrected mid-
session and worked from the actual sections; flagged in this
record so future briefs don't carry the stale anchor forward.

## Session shape

Session 108 was a substantive brief-drafting session, executed
end-to-end without split-trigger pressure. Three sub-phases:

**Sub-phase A — pre-flight grounding.** Read `2_6_settlement_race.md`
§3.1, §3.2, §3.4, §3.5, §4.4 for the spec substrate. Empirically
verified the W6.5 ship state by grep + read on
`workflows/bet_entry/v1/settlement.py` and `storage.py` —
discovered that `list_provisional_settlement_bets()` and
`ProvisionalSettlementSurfacingPayload` already exist (read-side
substrate for W8 already shipped), but the manual-transition write
path is explicitly deferred at `settlement.py` line 310 ("re-
transition from terminal state: not implemented at v1"). Verified
W7 substrate at `ui/api/routers/` (only `health.py` shipped) and
`ui/web/src/api/client.ts` (only `apiGet` shipped, with comment
explicitly noting POST/PATCH wrappers arrive in W8+). Verified
greyhound carry against W6.5 brief and §2.6 spec — neither names
greyhound explicitly, so carry remains a needs-verification item
not a brief-authoring blocker.

**Sub-phase B — operator scope-shape decision.** Pre-flight surfaced
that W8 needed to commission *both* the read-side queue UI and the
write-side manual-transition path (W6.5's deferral). Two options
walked: Option A (single bigger brief covering all of it) vs Option
B (split into W8a read-side + W8b write-side). Operator confirmed
Option A on the strength that Option B would ship the queue in a
half-built unusable state. Six operator-call items walked one-per-
round in plain operator language:

1. **Queue refresh cadence** — locked at 3 seconds with hard-coded
   constant noting future settings panel.
2. **Confirmation step before action buttons** — locked yes, with
   optional free-text reason captured to audit trail.
3. **Top-level nav menu** — operator pivoted: was scoped out; folded
   into W8 as new §5.8 because invisibility-without-typing-URL
   would suppress operational use. Two entries (Burst review
   primary, Health diagnostic).
4. **Runner-name display** — locked as nice-to-have format
   `selection_id. runner_name` (e.g. `12345. Cornishman`); Code
   ships without if it requires meaningful complexity, surface as
   follow-up brief.
5. **Audit-trail handling** — Code must explicitly confirm in the
   report's §6 (deviations) which path it took — either "audit
   surface found and used" or "no audit surface, transitions
   without audit-trail entry, follow-up brief required."
6. **Manual escalation from terminal back to provisional** —
   deferred to build-proper; operator confirmed this is acceptable
   because operator–Claude can fix any specific case manually
   between sessions.

**Sub-phase C — brief authoring + iteration.** Initial draft
written end-to-end at 618 lines, eight named anchors. Operator
decisions then folded in via 6 surgical `edit_block` edits — adding
new §5.8 (nav surface), renumbering §5.8 → §5.9 (smoke-test),
updating §5 opener "eight" → "nine", reframing §5.6 runner-name
text, strengthening §5.5 audit-trail confirmation requirement,
updating §6 sequencing, §8 output spec, §10 follow-on briefs, §11
parking-lot exclusions. Final file 670 lines, SHA256
`f26b0fb89cafdfaa3b1ba64a9b521c6e45ea2a73ee9faccc7207b64bfb3821cf`.

**Sweep candidates exercised this session:**

- **(s) Plain-language re-explanation on operator request** —
  exercised continuously during operator-call walk in sub-phase B.
  Cat 1 candidate; reinforced.
- **(l) Multi-item-triage inventory-first cadence** — exercised at
  pre-flight when surveying W6.5 substrate (grep → read inventory
  before drafting). Seventh concrete use. Cat 1 candidate; ready for
  canonical encoding.

## What was delivered

1. **W8 burst-review queue UI brief locked** at
   `dr029/w4_bet_entry/w8_burst_review_queue_brief.md`. 670 lines.
   SHA256 `f26b0fb89cafdfaa3b1ba64a9b521c6e45ea2a73ee9faccc7207b64bfb3821cf`.
   Nine named anchors (§5.1–§5.9): apiPost/apiPatch wrappers,
   VITE_API_BASE_URL docs, provisional-bets read endpoint, manual-
   transition write endpoint, manual-transition workflow function,
   queue page, per-bet modal, minimal top-level nav surface,
   smoke-test verification.

2. **Six operator-call decisions encoded into the brief**: 3-second
   refresh cadence with future-settings comment; confirmation step
   with optional reason field; minimal top-level nav (Burst review +
   Health entries); runner-name format `selection_id. runner_name`
   nice-to-have; audit-trail path explicit-confirmation requirement;
   manual-escalation-from-terminal explicitly out of scope.

3. **Two new open items captured**: settings-area cadence control
   deferred to follow-up brief; greyhound operational constraint
   parked as W6.5-layer needs-verification item.

4. **One stale anchor identified and corrected**: `current_state.md`
   named "§2.9 §4.4" as the §2.6 spec read; §2.9 doesn't exist.
   Worked from actual §3.1, §3.2, §3.4, §3.5, §4.4 anchors.

5. **Claude Code prompt produced** for the operator's Code session
   handing off the locked brief, plus context-clearing
   recommendation (clear for fresh context — substantive build
   session, multiple pre-reads, full brief contract.)

## Standing-instruction adherence check

- **Cat 1 brevity / plain-language defaults:** plain operator
  language sustained throughout sub-phase B operator-call walk;
  technical detail kept to the brief itself. One operator-flagged
  reframe in Session 107 carried into this session as default.
- **Cat 1 silent session-open ritual:** held silent per rule; single
  combined orientation output at end.
- **Cat 1 calendar-calibrated session open:** delivered as
  same-workday tight recap (~14-min gap).
- **Cat 1 v3_build_picture.md inline render at open:** skip-silent
  (artefact last-update predates Session 107 close). Correct.
- **Cat 1 open-items delta:** skip-silent (no movement). Correct.
- **Cat 1 hard line wraps in fenced review blocks:** applied to
  the §1 brief draft surfaced for operator review.
- **Cat 1 call-driven surfacing during section-by-section drafting:**
  exercised — full brief drafted under-the-hood per operator
  request, only the 7 operator-call items surfaced for review.
- **Cat 2 timestamp anchor at session open:** anchored 11:05 ACST.
- **Cat 2 required reads in order:** current_state →
  standing_instructions → project_context → SESSION_107.
- **Cat 2 pre-flight directory listing after named reads:** ran.
  Clean.
- **Cat 2 close-out actions:** session record (this file),
  `current_state.md` rotation, opening prompt for Session 109.
  No `v3_build_picture.md` update (no streams moved). No
  `standing_instructions.md` edits.
- **Cat 3 Desktop Commander default:** all filesystem and process
  operations via `Desktop Commander:start_process`, `read_file`,
  `edit_block`, `list_directory`, `write_file`. No `bash_tool`
  reflex.
- **Cat 3 dry-run multi-target mechanical edits:** N/A — six
  `edit_block` calls were single-target each (one specific
  `old_string` → one specific `new_string` in one specific place).
- **Cat 3 verify empirically:** post-write `wc -l` + `shasum`
  confirmed brief integrity at 670 lines, SHA256 `f26b0fb8...`.
- **Cat 4 governance discipline:** brief encodes DR-019, DR-021,
  DR-022, DR-027, DR-028, DR-030, DR-031, DR-032 with bracketed
  plain-language reminders per Cat 1. No new DRs surfaced.
- **Cat 5 software-question / operator-strategic split:** technical
  detail of brief authoring was Claude's territory; six operator-
  facing decisions were operator's calls in plain operator language.
  Clean split.

## Open items in

Pointer-only — full carry-forward list in `current_state.md` "Open
items" section. New items surfaced this session:

- **Session 109 W8 brief dispatch + Code execution + W8 report
  triage** — primary deliverable. Brief locked, ready for hand-off.
- **Settings-area cadence control follow-up brief** — deferred from
  W8 §1. Lands when operational experience surfaces what knobs
  matter; likely co-scoped with other queue-tuning settings as they
  emerge.
- **Greyhound operational constraint verification** — parked as
  W6.5-layer needs-verification. Lands when first real greyhound
  race exercises the settlement worker, OR if a small probe brief is
  scoped before then. Not gating.
- **Stale-anchor finding** — `current_state.md` previously named
  "§2.9 §4.4" for §2.6 reads; corrected this session, captured here
  for record. Future briefs read from the actual §-numbering.
- **Sweep candidate (l) seventh concrete use** — pre-flight
  inventory cadence on W6.5 substrate. Cat 1 candidate; ready for
  canonical encoding.
- **Sweep candidate (s) reinforced** — plain-language operator-call
  walk through six items in sub-phase B. Cat 1 candidate.

## Open items out

- **W8 burst-review queue brief drafting** — closed clean. Brief
  locked at 670 lines, SHA256 `f26b0fb8...`.
- **W7 §7.4 `VITE_API_BASE_URL` carry** — folded into W8 §5.2.
- **Session 100 per-bet modal carry** — folded into W8 §5.7.
- **Session 100 settings-area cadence carry** — deferred to
  follow-up brief, captured as new open item.
- **Session 100 greyhound operational constraint carry** — parked as
  W6.5-layer needs-verification, captured as new open item.

## Session close state

- Rebuild folder root: 11 governance `.md` files +
  `v3_build_picture.md` + `openapi.json` +
  `external_api_resources.md` + `.DS_Store` + 6 directories. Clean.
- WIP: `dr029/w4_bet_entry/w8_burst_review_queue_brief.md` newly
  authored (670 lines). No edits to canonical-truth files this
  session.
- `.close_out_backups/`: stale `SESSION_108_opening_prompt.md` to
  be swept; new `SESSION_109_opening_prompt.md` written by this
  close.
- Sessions folder: `SESSION_108.md` (this file).
- Project knowledge base: `decisions.md` re-upload still pending
  from Session 107 carry. No new uploads required from this
  session (W8 brief lives in `dr029/`, not in the Project
  knowledge base scope).

## Forward routing

**Confirmed with operator:** Session 109 = W8 brief dispatch to
Claude Code (out-of-session), Code execution, then operator-Claude
session reads `w8_burst_review_queue_report.md` and triages findings.
Operator confirmed clear-for-fresh-context for the Code session
(substantive build session needs full brief read without stale
context drift).

**Out of scope for Session 109:**

- Standing-instructions sweep (deferred to dedicated session).
- Settings-area cadence follow-up brief (waits on operational
  experience).
- Greyhound operational constraint verification (waits on first
  real greyhound race or operator-initiated probe).
- Any contract-work briefs unless W8 surfaces a follow-up finding.

**Possible Session 109 outcomes:**

- **W8 report triaged clean** — most plausible: substrate is
  well-understood (W6.5 + W7 ship state), brief is detailed,
  operator decisions encoded. Likely the same shape as Session 107
  triaged W7 (one canonical-truth amendment, three operator-call
  items resolved in plain language).
- **W8 report surfaces an audit-trail follow-up brief** — if
  Code's §5.5 confirms no audit surface in W6.5 ship and the
  operator decides audit-trail is the next priority.
- **W8 report surfaces a runner-name follow-up brief** — if
  Code ships without name display per the nice-to-have carve-out.
- **Deferral-as-deliverable** — if the report surfaces material
  scope reshape, multiple deviations, or unexpected substrate
  findings.
