---
name: bethub-session-open
description: Use when the operator says "open session N", "start session N", "let's open session N", "kick off session N", or opens a fresh chat in the bethub-rebuild Claude Project at the start of a working session. Runs the bethub-rebuild session-open ritual — timestamp anchor in Adelaide local time, required reads in order, pre-flight directory listing, drift-check of the previous session's close-out, calendar-calibrated recap and objective, and conditional renders of the v3 build picture and open-items delta. Do not use for non-bethub-rebuild sessions, ad-hoc questions during an already-open session, or when the operator is mid-conversation and pivoting to a new topic. Bethub-rebuild only — other projects are out of scope.
---

# bethub-session-open

This skill runs the open-ritual for a fresh session of the bethub-rebuild project. It encodes Category 2 (Session protocol) of `standing_instructions.md` plus the calendar-calibrated open behaviours added Category 1 in Session 43.

The skill is the procedural layer that makes session-open consistent. It does not replace operator judgement — when something on the checklist surfaces a mismatch or anomaly, surface it to the operator immediately rather than papering over.

## When this skill fires

**Triggers (exhaustive — fire on any of these):**

- Operator says "open session N", "start session N", "let's open session N", "kick off session N", "fresh chat for session N", or any close paraphrase that names a numbered session in the bethub-rebuild context.
- Operator opens a fresh chat in the `bethub-rebuild` Claude Project and the first message is anything that implies starting work.
- Operator pastes an opening prompt artefact (during transition; opening prompts are still load-bearing per `standing_instructions.md` Category 2 until `current_state.md` proves itself).

**Does not fire:**

- Operator is already in an open session and asks an ad-hoc question — that's not a session open.
- Operator pivots to a new topic mid-session — pivoting is not opening.
- Operator opens a chat in any other Claude Project, or a non-Project chat that's not bethub-rebuild work.
- Operator's first message is a one-off question that doesn't imply session work (e.g. "what's the timestamp format we use for session anchors?" — that's a lookup, not an open).

When the trigger is ambiguous, ask the operator directly: "Open Session N proper, or just a quick question?" before running the ritual.

## Open ritual — step by step

Run these steps in order. Do not skip ahead. Each step has an explicit success condition; failure to meet it gets surfaced to the operator immediately, before continuing.

### Step 1 — Timestamp anchor (DR-021)

Run `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` via `Desktop Commander:start_process`. The output is the canonical session-open timestamp. All subsequent timestamps in the session reference this anchor.

**Why:** DR-021 (timestamp anchoring, Adelaide local time) requires anchoring on actual current Adelaide local time, not on conversational pacing. Sessions can run over multiple calendar days; re-anchor on resumption.

**Success condition:** the command returns a current ACST or ACDT timestamp matching wall-clock Adelaide time.

### Step 2 — Required reads in order

Read the files listed in `current_state.md` "Required reads for Session N" — in order. During the Phase 2 transition, the opening prompt artefact also lists them; if both exist, follow `current_state.md` (the post-Phase 2 source of truth).

Standard read list:

1. `current_state.md` — the live working state.
2. `standing_instructions.md` — read in full per Category 2.
3. `project_context.md` — orientation primer.
4. `sessions/SESSION_<N-1>.md` — most recent session record.
5. Any session-specific reads named in `current_state.md` (older session records, scope addenda, governance docs, brief precedents).

Confirm completion before substantive work. If a named read is missing or inaccessible, surface to operator before continuing.

**Why:** Standing instructions live in `standing_instructions.md` and are not held in opening prompts. Skipping the standing-instructions read is the single highest-leverage way to drift on agreed procedure.

### Step 3 — Pre-flight directory listing

Run `Desktop Commander:list_directory` on `/Users/tim/Desktop/Projects/bethub-rebuild` (depth 1). Confirm:

- Expected `.md` files at root present (currently 11: README, architecture, current_state, decisions, governance, project_context, session_operations_proposal, standing_instructions, v3_data_requirements, vision, work_in_progress).
- Once `v3_build_picture.md` is in active use, that's a 12th expected file.
- `.close_out_backups/` is empty (close-out should leave it empty).
- `sessions/`, `dr029/`, `agent_review/`, `diagrams/`, `orchestration_pack/`, `skills/` directories present.

Surface any phantom files, stale backups, or unexpected directory entries immediately.

**Why:** Phantom or leftover files surface immediately rather than mid-session. Pattern of error: a previous session's premature close-out can leave stale opening-prompt artefacts in `.close_out_backups/`. Catching at the next open is the cheapest catch.

### Step 4 — Name governing decision records

In the orientation summary, name the governing DRs by number with bracketed plain-language reminder:

- **DR-029** (the data-layer fit-for-purpose review before v3 build — active arc).
- **DR-027** (the two-database architecture: BetHub owns operational state, capture.db owns analytical/source data).
- **DR-028** (the cross-database integration boundary discipline: no caching, no denormalisation, no second integration point).
- **DR-021** (timestamp anchoring, Adelaide local time — applies every session open).

Re-read trigger: if the session surfaces a cross-database topic, re-read DR-027 and DR-028 mid-session.

**Why:** The operator does not hold DR numbers in working memory per Category 1. Naming the active governors at open prevents drift later when shorthand is invoked.

### Step 5 — Drift-check the previous close-out

Verify three things from the previous session's close:

- (a) `current_state.md` "last updated" timestamp matches `sessions/SESSION_<N-1>.md` close timestamp.
- (b) `sessions/SESSION_<N-1>.md` exists and is non-empty.
- (c) `v3_build_picture.md` was updated last close if streams moved; if it wasn't updated and streams did move, that's a drift. (If streams did not move, the artefact's "last updated" stamp predates the close — that's correct, not drift.)

Surface any mismatch immediately, before substantive work begins. Mismatches are cheap to fix at this point and invisible until the *next* open.

**Why:** Cat 1 instruction added Session 43, directly addressing the Session 42 premature-close-out failure mode. Drift-checks are a 30-second insurance policy against silent close-out gaps.

### Step 6 — Calendar-calibrated recap and objective

Compare the Step 1 anchor against the previous session close timestamp (in `sessions/SESSION_<N-1>.md`). Two cases — see "Calendar-calibrated recap logic" section below for the full rule. Deliver the recap and a 1–2 sentence statement of this session's objective.

### Step 7 — Conditional renders

Two conditional renders, in order:

1. **V3 build picture inline** — render only if stream state moved since previous open. See "Conditional renders" section below for the rule and the rendering shape.
2. **Open-items delta** — render only if there is a meaningful delta in open items since previous open. See "Conditional renders" section below for the rule.

If both conditions are skip-silent, the open ritual ends after Step 6 and the session moves directly to substantive work.

### Step 8 — Confirm orientation complete, hand off to substantive work

A short confirming line — "orientation complete, ready to start on X" where X is the named objective from Step 6. Then wait for the operator's first substantive instruction, or move directly to the first work item if the opening prompt explicitly directed it.

## Calendar-calibrated recap logic

Compare the Step 1 timestamp against the previous session's close timestamp (read from `sessions/SESSION_<N-1>.md` "Closed:" line). Two cases.

### Same-workday

The fresh open is **same-workday** if either:

- The fresh open's calendar date equals the previous session close's calendar date, OR
- The fresh open is between 00:00 and 04:00 ACST/ACDT and the previous close was on the prior calendar date.

The 4am cutoff handles the operator's pattern of occasionally working past midnight — anything before 4am is treated as a continuation of the prior workday, not a new one.

**Recap shape (same-workday):** tight. One or two sentences on what last session did. One or two sentences on what this session does and what it gets the operator. No arc-state recap, no "where we are" framing, no historical context — the operator is in flow and holds the project state.

Example: *Session 43 closed Phase 2 deliverable 4 (`bethub-session-open` frontmatter) plus six standing-instruction edits. Session 44 picks up the four open Phase 2 deliverables — three skill bodies plus `v3_build_picture.md` artefact.*

### New-workday

The fresh open is **new-workday** if it's on a calendar date later than the previous close AND the 4am rule above does not apply.

**Recap shape (new-workday):** longer. Cover four things in plain operator language:

- Where the active arc is (currently DR-029 — the data-layer fit-for-purpose review before v3 build).
- What closed last session.
- What's in flight (carrying forward).
- What this session does and what it gets the operator.

Still front-loaded with the decision or fact the operator needs first. Still plain operator language, no schema or DR jargon (DRs cited with bracketed plain-language reminders per Category 1).

### Sanity check

If the previous-close timestamp can't be located (file missing, malformed, etc.), surface to operator before delivering any recap. Don't guess; the recap calibration depends on a known-good prior anchor.

---

## Conditional renders

Two conditional surfaces, both new-Cat-1 instructions added Session 43. The conditional pattern is deliberate — rendering these unconditionally becomes ritual noise. Render only when there's meaningful state to surface.

### V3 build picture (inline)

**Source:** `v3_build_picture.md` in the rebuild folder root.

**Render condition:** stream state has moved since the previous open. Concretely, the artefact's "Last updated" timestamp is later than the previous session's close timestamp (or, equivalently, the previous session's close-out updated the artefact).

**If render condition is false:** skip silently. Do not surface "no changes" or "build picture unchanged" — that itself is ritual noise.

**Render shape:**

- The full stream table from `v3_build_picture.md` (eleven streams currently — DR-029 §2.1–§2.10 plus session-ops).
- Detail line under the table for **the current session's stream** (1–2 sentences). This is the stream that the session is primarily acting on. Other streams render table-row only.
- **`done` streams carry one session post-close, then drop.** The `bethub-session-close` skill is responsible for dropping them at the appropriate close; this skill renders whatever the artefact contains.

Plain-language operator-facing throughout. DR numbers cited with bracketed plain-language reminders per Category 1. No schema field names.

### Open-items delta

**Source:** `current_state.md` open items section, compared against `sessions/SESSION_<N-1>.md` open items section (or whatever the previous-close snapshot is).

**Render condition:** at least one of the following is true since previous open:

- An open item closed (✅).
- A new open item surfaced.
- An item is now overdue or close to it (e.g. a `waiting-on-<date>` item where the date has passed or is within 24h).

**If render condition is false:** skip silently.

**Render shape:** a short bulleted list under the headers "Closed since last open", "New since last open", "Overdue or close to it". Empty headers omitted. The full open-items list lives in `current_state.md` — the delta is what's worth surfacing in the open ritual, not the full list.

**Order:** v3 build picture renders first, then open-items delta. Both are skipped silently if neither condition fires; in that case the orientation summary closes after Step 6 (calendar-calibrated recap + objective) and the session moves to substantive work.

## Negative scope — what this skill does not do

Explicit non-behaviours, to keep the skill from drifting into adjacent ritual or substituting for operator judgement.

- **Does not summarise or interpret the canonical truth.** The skill reads `standing_instructions.md`, `current_state.md`, `project_context.md`, and the named session record in full. It does not produce a "highlights" digest or a "key points" summary of these — they're read as written, not paraphrased.
- **Does not pre-empt operator decisions.** If the orientation reads surface a routing question, an open question, or anything ambiguous, the skill flags it for the operator and waits for the call. It does not pick a route on the operator's behalf.
- **Does not extend into substantive work.** The skill ends at Step 8 (hand-off). The next instruction comes from the operator (or from an opening prompt artefact if one was pasted). Drifting from open ritual directly into substantive work without the operator's go-ahead is out of scope.
- **Does not skip steps under "obvious" pressure.** "We just opened this morning, no need for a directory listing" is exactly the failure mode this skill prevents. Every step runs every open. The drift-check is cheapest precisely when nothing has gone wrong; skipping it because nothing seems wrong defeats its purpose.
- **Does not author or modify `standing_instructions.md`, `current_state.md`, `v3_build_picture.md`, or any session record.** Those are session-close territory (or substantive-work territory for `standing_instructions.md` edits). The open ritual is read-only on canonical state.
- **Does not suppress the close-out's opening prompt.** During the Phase 2 transition, opening prompts are still load-bearing per `standing_instructions.md` Category 2. If the operator pastes an opening prompt at session start, the skill runs alongside it (the prompt names the session-specific reads; the skill runs the procedural ritual). The two are complementary, not competing.

---

## Reference — canonical truth lives here

The skill implements behaviours specified in `standing_instructions.md`. When the skill and the standing instructions diverge, **the standing instructions win** — the skill is downstream, the instructions are upstream.

Specific cross-references:

- **Step 1 (timestamp anchor)** — Cat 2 "Timestamp anchor at session open, Adelaide local time" + DR-021.
- **Step 2 (required reads)** — Cat 2 "Required reads at session open" + Cat 2 read-`standing_instructions.md`-in-full.
- **Step 3 (pre-flight directory listing)** — Cat 2 "Pre-flight directory listing of rebuild folder root".
- **Step 4 (governing DRs)** — Cat 2 "Name governing decision records in orientation summary".
- **Step 5 (drift-check)** — Cat 1 "Drift-check the previous session's close-out at the start of every fresh open".
- **Step 6 (calendar-calibrated recap)** — Cat 1 "Calendar-calibrated session open" (same-workday vs new-workday with 4am cutoff).
- **Step 7a (v3 build picture)** — Cat 1 "V3 build picture rendered inline at session open — conditional".
- **Step 7b (open-items delta)** — Cat 1 "Open-items delta — conditional".
- **Step 8 (hand-off)** — Cat 1 "Don't drift to alternatives when the operator has been clear about today's work" + the brevity defaults.

When `standing_instructions.md` is updated, this skill is reviewed at the next close-out and updated if any procedural element shifted. The `bethub-session-close` skill catches that review explicitly.
