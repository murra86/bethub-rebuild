# Session 114 — Standing-instruction sweep: eight Cat 1 / Cat 2 / Cat 3 / Cat 5 candidates promoted

**Opened:** 2026-05-10 15:27 ACST
**Closed:** 2026-05-10 16:02 ACST
**Tool routing:** Chat (no Code-bound work commissioned this session).
**Governing DRs invoked:** DR-021 (timestamp anchoring). No DR-027 / DR-028 / DR-029 / DR-030 / DR-031 substrate touched this session — pure standing-instruction work.

---

## Anchor

Open command output: `2026-05-10 15:27 ACST`.
Close command output: `2026-05-10 16:02 ACST`.
Wall-clock window 35 min, fully-active session.

## Pre-flight checks

Drift-check at open: clean. `current_state.md` last-updated 2026-05-10 14:47 ACST matched Session 113 close exactly. `sessions/SESSION_113.md` present (87 lines). `v3_build_picture.md` last-updated 2026-05-07 — unchanged correctly (Session 113 was a §2.4 surgical fix, no stream state moved). `.close_out_backups/` held only `SESSION_114_opening_prompt.md` (this session's opener — consumed by open). Operator informed at session open that `governance.md` and `decisions.md` had been re-uploaded to the Claude Project knowledge base, closing both carry-forward operator actions (Session 109's PRIMARY carry on `governance.md`, Session 107's carry on `decisions.md`).

## Session shape

Single-deliverable focused session. Two phases.

**Phase 1 — Forward-routing call.** Operator opened on the leading-candidates framing from `current_state.md`: (1) v3-build-proper re-cut, (2) standing-instruction sweep. Operator picked (2) with framing "do this before v3-build-proper so the build runs against the cleaner ruleset rather than mid-build amendments." Claude agreed; sequencing was sound.

**Phase 2 — Sweep work.** Walked through six candidates queued from prior sessions (`(l)` inventory-first cadence, brief-anchor empirical verification, forward-routing-loose-carry, software-territory call delegation, plain-language cosmetic-routing delegation, write_file-not-create_file vigilance) one at a time per Cat 1 plain-language explainer cadence. Operator added a seventh during the walkthrough — tighten default response register further, framed as cognitive-load-on-operator not response-length-per-se — and an eighth surfaced from Claude self-flagging the Session 114 open's step-by-step narration as a violation of the existing silent-ritual rule (zero-step-narration tightening). All eight wordings drafted, operator confirmed, written to `standing_instructions.md` via `Desktop Commander:edit_block`.

## What was delivered

1. **`standing_instructions.md` — eight edits across Cat 1, Cat 2, Cat 3, Cat 5.** All landed via `Desktop Commander:edit_block`. File grew from 142 to 153 lines. Final hash `410a0cf4babd`.

2. **Cat 1 — three additions/strengthenings:**
   - "Tighten the default response register further" — strengthens the existing brevity defaults with cognitive-load-on-operator framing. Detail-opt-in escape hatch preserved.
   - "Inventory-first cadence on long technical reports" — promotes sweep candidate `(l)` (eleventh concrete use Sessions 99–113) to canonical Cat 1. Classification trigger named explicitly as operational impact, not technical-vs-non-technical. Plain real-world gambling language register baked in (15-year-old-who-knows-gambling baseline).
   - "Silent session-open ritual" + "Silent session-close ritual" tightened with explicit zero-step-narration clause. Caught Session 114 open's violation of the existing rule; tightened wording closes the "low-key narration is fine" interpretation.

3. **Cat 2 — one addition:**
   - "Re-validate queued work-items at execution time" — promotes sweep candidate `(NEW from Session 110) forward-routing-loose-carry` to canonical Cat 2 close-out actions. Pairs with Cat 3 empirical-verification rule.

4. **Cat 3 — two changes:**
   - "`create_file` is banned for filesystem work; verify every write" — strengthens the existing Cat 3 `create_file` vs `write_file` warning from "prefer X over Y" to outright ban with mandatory post-write verification. Substrate: Session 113 close-out partial-state failure caught only by chance at the final sweep step.
   - "Empirical verification before editing governance artefacts" — promotes sweep candidate `brief-anchor empirical verification` (eleven concrete instances Sessions 109–113) to canonical Cat 3.

5. **Cat 5 — two additions:**
   - "Make software calls; don't punt them" — promotes sweep candidate `(operator-delegation) software-territory call delegation` (fourteen exercises) to canonical Cat 5. Strengthens the existing "Software questions are Claude's" first paragraph with the operational discipline of *actually making the call* rather than framing as A-or-B.
   - "Cosmetic calls default to Claude's pick" — promotes sweep candidate `(operator-delegation) plain-language cosmetic-routing delegation` (fifteen concrete instances) to canonical Cat 5. Narrower cousin of the rule above; applies only when "any operational dimension?" lands on a clear no.

6. **Forward routing operator-confirmed: v3-build-proper re-cut as Session 115's primary deliverable.** Multi-session arc; fresh-mind session preferred. Build picture in `v3_build_picture.md` was last cut Session 79; W1–W9 have shipped incrementally since. Re-cut consolidates what's now built vs what's outstanding into a clean current-state stream model for the remaining workstream sequence.

## Standing-instruction adherence check

- **Cat 1 brevity defaults** — honoured *after* operator's #7 surfaced the cognitive-load framing. Earlier in the session (the six-candidate walk-through), responses were marginally too long for what the operator needed; the surfacing of #7 was itself the diagnostic. Lesson logged in the `standing_instructions.md` edit itself.
- **Cat 1 silent session-open ritual (existing)** — **violated at Session 114 open.** Step-by-step headers ("Step 1 —", "Step 2 —", "Step 3 —") appeared in operator-facing text. Caught by operator-Claude conversation when the sweep surfaced #8. Tightened wording landed as part of the sweep — closes the "low-key narration is fine" interpretation.
- **Cat 1 V3 build picture conditional render** — honoured (skip-silent at open). No stream movement Session 113.
- **Cat 1 open-items delta — conditional** — honoured. Two items (`governance.md` and `decisions.md` Project KB re-uploads) closed since last open; surfaced concisely.
- **Cat 1 inventory-first cadence (sweep candidate `(l)`)** — exercised at session-114 open's reading of `current_state.md` open-items section. **Twelfth concrete use** across the active arc, immediately before being promoted to canonical Cat 1.
- **Cat 2 timestamp anchor (DR-021)** — honoured. Open 15:27 ACST and close 16:02 ACST both anchored via `Desktop Commander:start_process`.
- **Cat 2 Desktop Commander default** — honoured. All eight `standing_instructions.md` edits via `Desktop Commander:edit_block`. No `create_file` slip this session.
- **Cat 3 empirical verification before editing (NEW)** — exercised in real time during the sweep. Each `edit_block` was preceded by a `read_file` of the section being edited; old_string was copied verbatim from the read output. **First exercise post-promotion.**
- **Cat 3 `create_file` ban (NEW, strengthened)** — honoured by mechanism (no `create_file` calls made this session). **First session under the strengthened rule.**
- **Cat 5 make software calls don't punt (NEW)** — exercised at sweep candidate #4 itself. Recursive — promoting the rule was an instance of the rule. Promotion read the existing Cat 5 first paragraph and strengthened it inline.
- **Cat 5 cosmetic calls default to Claude's pick (NEW)** — exercised at proposed wording for each of the eight edits (Claude proposed wording, operator confirmed; cosmetic phrasing calls were Claude's). Sixteenth concrete instance.
- **Cat 1 plain real-world gambling-framed explainers** — honoured at the six-candidate walkthrough. Operator confirmed mid-session that the register matched (15-year-old-who-knows-gambling baseline).

## Sweep candidates exercised this session

All sweep candidates this session were the *promotion targets themselves*. Pattern: the sweep work is the canonicalisation event for each candidate. Post-Session 114, the Cat 1 / Cat 2 / Cat 3 / Cat 5 ruleset captures the discipline; sweep candidate tracking compresses to "any new pattern surfaced this session?" (none new this session beyond the eighth which was self-flagged at session 114 open).

Active sweep candidates remaining: none. The queue is empty as of Session 114 close. Future patterns will surface organically and re-build the queue.

## Open items

Pointer to `current_state.md` post-rotation. New items of substance: one — `standing_instructions.md` re-upload to the `bethub-rebuild` Claude Project knowledge base (eight Cat 1 / Cat 2 / Cat 3 / Cat 5 edits added Session 114). Standing operator-side carry-forward.

Carried forward from prior sessions: settings-area cadence follow-up brief; greyhound operational constraint verification; `betfair_adapter.py` mypy cleanup; Betfair API membership tier (BetWatch).

## Open items out (closed Session 114)

- **`governance.md` re-upload to Project KB** — closed (operator-side action completed pre-session-114-open).
- **`decisions.md` re-upload to Project KB** — closed (operator-side action completed pre-session-114-open).
- **Standing-instruction sweep arc** — closed end-to-end. Eight candidates promoted to canonical Cat 1 / Cat 2 / Cat 3 / Cat 5.
- **All sweep candidate tracking** — collapsed (no remaining queue at Session 114 close).
- **Forward routing for Session 115** — confirmed (v3-build-proper re-cut as primary deliverable; multi-session arc; fresh-mind session preferred).

## Session close state

- **Rebuild folder root:** structurally unchanged. `standing_instructions.md` substrate edited (eight edits). `current_state.md` rotated at this close. `sessions/SESSION_114.md` written (this file). `v3_build_picture.md` untouched. `governance.md` untouched. `decisions.md` untouched.
- **`.close_out_backups/`:** `SESSION_114_opening_prompt.md` deleted (consumed at session 114 open). `SESSION_115_opening_prompt.md` written.
- **Project knowledge base:** `standing_instructions.md` re-upload pending (eight Cat 1 / Cat 2 / Cat 3 / Cat 5 edits Session 114). `governance.md` and `decisions.md` were re-uploaded by operator pre-session-114-open; both clear.

## Forward routing

**Confirmed with operator: close session here. Session 115 opens fresh-mind on operator's schedule with v3-build-proper re-cut as primary deliverable.** Multi-session arc — the re-cut is itself scoped over more than one session. Session 115's specific shape: read the existing `v3_build_picture.md`, inventory what's now built (W1–W9 ship state) vs what's outstanding (composition root, remaining workstreams), produce a clean current-state stream model for the remaining workstream sequence. No commitment to specific session count to close the re-cut; the work takes as long as it takes.
