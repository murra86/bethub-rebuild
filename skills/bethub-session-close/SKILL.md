---
name: bethub-session-close
description: Use when the operator says "close session N", "close out", "wrap session N", "end session N", "let's close out", or signals the working session is wrapping up in the bethub-rebuild project. Runs the bethub-rebuild session-close ritual — final timestamp anchor, pre-close checklist, session record write, current_state.md rotation, conditional v3_build_picture.md update, conditional standing_instructions.md sweep, opening prompt generation for the next session, and post-close verification. Do not use for non-bethub-rebuild sessions, mid-session pauses, or when the operator is just stepping away briefly. Bethub-rebuild only — other projects are out of scope. The skill enforces the Session 11 lesson (split rather than push through) and the Session 42 lesson (operator-confirmed forward routing before close-out completes).
---

# bethub-session-close

This skill runs the close-ritual for an active session of the bethub-rebuild project. It encodes Category 2 (Session protocol) close-out actions from `standing_instructions.md` plus the close-out protocol from `governance.md`.

The skill is the procedural layer that makes session-close consistent. It does not substitute for operator confirmation on forward routing — when the next session's shape is ambiguous, the skill stops and asks rather than guessing.

## When this skill fires

**Triggers (exhaustive — fire on any of these):**

- Operator says "close session N", "close out", "close out session N", "wrap session N", "end session N", "let's close out", or any close paraphrase that signals the session is ending.
- Operator signals the session is wrapping (e.g. "I think we're done for today", "let's call it") in a bethub-rebuild context.

**Does not fire:**

- Operator pauses mid-session and intends to resume (e.g. "stepping away for an hour", "I need a break"). Pauses are not closes — re-anchor timestamp on resumption per Cat 2 multi-day session rule, but no close-out fires.
- Operator pivots between substantive tasks within the same session.
- Operator asks "should we close out?" — that's a question, not a trigger. Answer the question; the close-out triggers on a subsequent confirmation.

**Critical sanity check before firing:** confirm the operator actually intends to close. The Session 42 lesson: a premature close-out — closing while load-bearing forward routing is still ambiguous — is the failure mode. If the next session's shape isn't clear from the current session's outcomes, **ask the operator directly** before firing. "Ready to close, or should we settle [forward-routing question] first?" is the cheap insurance.

## Close ritual — step by step

Run these steps in order. Do not skip ahead. Each step has an explicit success condition.

### Step 1 — Re-anchor timestamp (DR-021)

Run `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` via `Desktop Commander:start_process`. This is the canonical session-close timestamp. Used in:

- The session record's "Closed:" line.
- The `current_state.md` "Last updated" line.
- The next session's opening prompt as the previous-close anchor (used by `bethub-session-open`'s drift-check and calendar-calibrated recap).

**Why re-anchor at close even if recently anchored:** sessions can run over multiple calendar days. The close timestamp is what `bethub-session-open` calibrates against next session — it must reflect actual close time, not pause time or session-open time.

**Success condition:** the command returns a current ACST or ACDT timestamp matching wall-clock Adelaide time.

### Step 2 — Pre-close checklist (governance.md §close-out protocol)

Verify before any close-out work begins:

- [ ] **First-action gate (hard — operator instruction, S200).** Close-out does **not** complete until the **next session's first action is confirmed with the operator** — unless the operator has **explicitly** said there is no first action, in which case record that the next session opens with no defined first action and proceed. This is stronger than generic forward-routing confirmation: the runner launched at Step 12 drives the opening prompt's first action automatically, so an unconfirmed first action means an automated run against an unconfirmed target. If the first action isn't confirmed and hasn't been explicitly waived, **stop and ask** before continuing — do not guess. The Session 42 lesson (closing while forward routing was ambiguous left Session 43's opening prompt mis-targeted) is the weaker precedent this gate hardens.
- [ ] All in-flight tool calls completed; nothing in pending state.
- [ ] Pre-flight directory listing run (`Desktop Commander:list_directory` on rebuild folder root, depth 1). Surface any phantom or stale files.
- [ ] No phantom files in scope — `system_snapshot.md`, `context_index.md`, `STATUS.md`, `CLAUDE.md` are v2 conventions and must not be created (governance.md §1).
- [ ] Open items list compiled — what carries to which future session.
- [ ] If any artefacts produced this session need operator-side action between sessions (e.g. uploading to Project knowledge base), note them for the close.
- [ ] Draft mental dry-run of files that will be modified — Should match what's actually changed during the session.

If any item is uncertain, surface the uncertainty. Don't proceed with mixed state.

### Step 3 — Hard split-trigger check (governance.md §2)

Before proceeding, check for split triggers:

- Wall-clock duration above ~3 hours of active session work.
- Day-rollover during the session (crossed local midnight ACST).
- Substantive scope change mid-session (new DRs, amendments to prior locked work, new governance files).
- Operator fatigue signal — explicit notes of tiredness or wanting to wrap.
- Claude detects context budget tightening.

**On any trigger, the response is to split-and-defer rather than push-through.** This skill still runs (close-out happens now, with full context budget for it), but any in-flight non-essential work — additional artefacts, optional sweeps, polish edits — defers to the next session rather than being layered on top of close-out.

If close-out itself looks like it might be expensive (multiple files to update, scratch promotion, new DR drafting), **and** any of the trigger signals fired, recommend a "minimal close" — write the session record, update `current_state.md`, generate the opening prompt, defer the rest to next session's open.

### Step 4 — Write the session record

Write `sessions/SESSION_<N>.md` with the standard structure:

- Header: session number, title (one-line summary of what landed), opened/closed timestamps, tool routing, governing DRs invoked.
- **Anchor** section: the open and close timestamp commands and outputs.
- **Pre-flight checks** section: what the open-ritual surfaced.
- **Session shape** section: 1–2 paragraphs describing what the session was — was it focused on a single deliverable, did it pivot, was it probe-triage, was it meta-work, etc.
- **What was delivered** section: numbered list of concrete outputs (artefacts written, files edited, decisions confirmed). Each item gets a short paragraph.
- **Standing-instruction adherence check**: explicit per-instruction tick on whether each Cat 1 / Cat 2 instruction was honoured. Flag any that were authored this session but not exercised.
- **Open items** section: pointer-only to `current_state.md` items, with any new items called out explicitly.
- **Open items out** section: items closed this session.
- **Session close state** section: state of rebuild folder root, WIP, `.close_out_backups/`, sessions folder, project knowledge base.
- **Forward routing** section: what next session does. **Confirmed with operator** is the load-bearing word — Session 42's premature close failed here.

Length target: 6–12K. Long enough to be a durable record, short enough to read in full at next session open.

**Success condition:** file written, non-empty, structure matches above.

### Step 5 — Update `current_state.md`

Rotate session-N content in. Specifically:

- "Last updated" timestamp → Step 1's close timestamp.
- "Where we are" → reflects session-N outcomes. Old "Where we are" content rotates *out* — into the just-written `SESSION_<N>.md`, not appended.
- "What's next" → reflects what session-(N+1) will do.
- "Required reads" → updated for next session if changes (e.g. new artefact authored this session that needs reading next session).
- Open items → updated to reflect closed/opened items this session.
- Active governing DRs → rarely changes; update only if a new DR was locked this session.

**Target file size:** ~10–20 KB. If `current_state.md` is growing session over session, that's drift — historical content should be rotating into session records, not accumulating in `current_state.md`.

### Step 6 — Conditional `v3_build_picture.md` update

**Update condition:** at least one stream's state moved during the session. Concretely:

- A stream's status changed (e.g. `blocked-on-probe` → `in flight`).
- A stream's next-milestone label changed.
- A new stream surfaced (rare; would imply DR-029 scope expansion or v3 build proper started).
- A stream closed (`done`).
- A previously-`done` stream is past its one-session carry window and needs to be dropped.

**If condition fires:** edit `v3_build_picture.md` in-place. Update the "Last updated" timestamp at the top to Step 1's close timestamp. Apply the stream-state changes.

**If condition doesn't fire:** leave the artefact untouched. Do not bump the timestamp; the timestamp reflects last actual update, not last session that checked.

### Step 7 — Conditional `standing_instructions.md` sweep

**Sweep condition:** any new standing instruction surfaced during the session, OR any existing instruction was edited.

**If condition fires:** the edits should already have been applied during the session itself (standing-instruction edits are substantive work, not close-out work). At close, verify:

- The file's line count is what was expected after edits.
- No partial edits, no leftover scratch text.
- Operator-side action flagged: standing_instructions.md needs re-uploading to the bethub-rebuild Claude Project knowledge base.

**If condition doesn't fire:** skip silently.

**Skill review trigger:** if Cat 1 or Cat 2 instructions changed, flag `bethub-session-open` and `bethub-session-close` skills for review at next session open. The skills implement those instructions; divergence is drift.

### Step 8 — Generate the next session's opening prompt

Write the opening prompt to `.close_out_backups/SESSION_<N+1>_opening_prompt.md`. Format per Session 43's working pattern (which itself follows governance.md "Open and close-out economy"):

- Drafted-at timestamp + handoff note (the runner launched at close Step 12 consumes this prompt and runs its defined first action — no manual paste; per the Cat 2 auto-runner amendment).
- One-paragraph orientation: re-run timestamp anchor per DR-021, pre-flight directory listing after named reads.
- **Calendar-calibrated open directive** (Cat 1): compare current ACST against this close's timestamp.
- **Drift-check directive** (Cat 1): verify (a) `current_state.md` last-updated matches this close's timestamp; (b) `sessions/SESSION_<N>.md` exists; (c) `v3_build_picture.md` updated if streams moved.
- **Primary deliverable** for the session.
- **Required reads** in order — `current_state.md` first, then `standing_instructions.md` in full, then `project_context.md`, then `sessions/SESSION_<N>.md`, then any session-specific reads.
- **Reference-only reads** — read on demand.
- **Pre-flight verification** — session-specific.
- **Pending operator-side actions** — what the operator does between sessions.
- **Open items in / Open items out** — what carries forward, what closed.
- **Filesystem note** — Desktop Commander default, REPL discipline, write-script-to-`/tmp` pattern.
- **Expected state of rebuild folder root** at next open.
- **Governing DRs** — typically DR-029, DR-027/028 if cross-DB, DR-021 always.

Target length: ~150–250 words for the body, plus the structured sections. Pointer document, not a summary.

**Why generate at every close on a multi-session arc:** standing instruction Cat 2 — operator does not need to ask. The opening prompt is the load-bearing handoff today and remains so until `current_state.md` proves itself.

### Step 9 — Sweep `.close_out_backups/`

Verify:

- The just-written `SESSION_<N+1>_opening_prompt.md` is present.
- No stale opening prompts from previous sessions are present (Session 42 left a stale `SESSION_43_opening_prompt.md` artefact that survived its claimed deletion — caught at Session 43 open; this skill prevents that recurrence at *its* close).
- No other stray files.

If stale files present, delete them. Re-run `Desktop Commander:list_directory` on `.close_out_backups/` to confirm clean state.

### Step 10 — Closing summary to operator

A short, high-level closing summary per Cat 2: what was done, what state things are in, what's next. Same brevity cadence as session conversation. Not an essay.

**If the opening prompt is being produced** (which it always is on multi-session arcs), Cat 2 says omit the closing summary — the opening prompt is canonical because the next session consumes it; the closing summary is read once. Default behaviour: omit. Operator may request explicitly; otherwise skip.

**One exception worth surfacing:** if the session produced something the operator needs to know *between* sessions (a flagged operator-side action, a discovered drift, a routing change), surface that explicitly even when omitting a full summary. One line, not a paragraph.

### Step 11 — Post-close verification

Re-run `Desktop Commander:list_directory` on the rebuild folder root and `sessions/`. Confirm:

- `sessions/SESSION_<N>.md` exists, expected size.
- `current_state.md` "Last updated" stamp matches close timestamp.
- `v3_build_picture.md` updated if streams moved (timestamp matches close); untouched otherwise.
- `standing_instructions.md` reflects any session edits, line count matches.
- `.close_out_backups/SESSION_<N+1>_opening_prompt.md` exists.
- No phantom files at root.

**Why post-verify:** Cat 2 — "After any long-running script call, re-run a state-snapshot read to verify canonical state matches expected. Do not trust absence of an error message as success when filesystem state changes." Close-out is the canonical state-changing moment of a session; verification is mandatory, not optional.

If verification fails on any item, surface to operator immediately. Do not declare close-out complete until state matches.

### Step 12 — Launch the headless session runner (strictly last)

The **final** action of close-out. Fires once, and only once **every** Step 1–11 verification has passed. Launch the out-of-session runner via `Desktop Commander:start_process`:

```
nohup /Users/tim/.bethub-cycle/session_cycle.sh "/Users/tim/Desktop/Projects/bethub-rebuild/.close_out_backups/SESSION_<N+1>_opening_prompt.md" >/dev/null 2>&1 & disown
```

Substitute `<N+1>` with the next session number — the same number used in Step 8's opening-prompt filename. The runner opens session N+1, runs the `bethub-session-open` ritual, executes the opening prompt's defined first action (honouring any `hold` / no-gate marker), then notifies the operator's laptop and phone.

**Strictly last — non-negotiable.** This is the only step that spawns work outside the current session, so it runs after everything else is verified clean. If *any* Step 1–11 check failed — write failure, verification mismatch, missing opening prompt, phantom file, partial state — **do not launch.** Surface the failure and stop. Launching on top of a failed close-out would open the next session against a broken handoff; withholding the launch is the guarantee that **the next session never opens before this one's close-out is fully complete.**

**Success condition:** `start_process` returns (the runner is detached and running). The close's one-line operator output (per Step 10 / Step 11) notes the launch — e.g. "close complete, Session N+1 runner launched." On any prior-step failure this step is skipped and the failure is what surfaces.

**Why detached (`nohup … & disown`):** the runner outlives this chat session, so the current session can end without killing it. Output is discarded (`>/dev/null 2>&1`) because the runner reports to the operator through its own laptop/phone notification, not through this session's transcript.

## Negative scope — what this skill does not do

- **Does not push through split triggers.** Step 3 explicitly recommends a minimal close on any split trigger. Pushing through is the Session 11 / Session 42 failure mode and is what this skill structurally prevents.
- **Does not close without the next session's first action confirmed or explicitly waived.** Step 2's first-action gate (hard, S200) stops close-out until the operator has confirmed the next session's first action — or explicitly said there is none. Step 8 names "Confirmed with operator" as load-bearing in the session record. Because the Step 12 runner drives that first action automatically, closing on an unconfirmed first action means an unattended run against an unconfirmed target; the skill does not do that.
- **Does not author a closing summary by default.** Cat 2 says omit when an opening prompt is produced. The skill defaults to omit; the operator can request explicitly.
- **Does not modify canonical truth that wasn't substantively changed during the session.** `architecture.md`, `decisions.md`, `governance.md`, `vision.md`, `v3_data_requirements.md`, `dr029/dr029_scope.md`, `project_context.md` — these are session-substantive-work territory if they need editing, not close-out territory. Close-out updates `current_state.md`, `sessions/SESSION_<N>.md`, conditionally `v3_build_picture.md` and `standing_instructions.md`, and writes the opening prompt. Anything else means substantive work didn't get committed properly during the session.
- **Does not silently degrade.** If something fails — file write, verification mismatch, anything — surface immediately. "Almost worked" is the same as "didn't work" for governance state.
- **Does not delete session records.** Session records are immutable historical truth. If a session record is wrong, the correction is a new note, not a rewrite. The skill never overwrites or deletes `sessions/SESSION_<N>.md` for any N.

---

## Recovery from partial-state failure

Per `governance.md` §close-out protocol §4 (recovery procedure for partial-state failures).

If close-out fails mid-run — script crash, verification mismatch, operator interrupt — the recovery flow is:

1. **Establish actual state.** Single `start_process` call: list rebuild folder root, list `sessions/`, list `.close_out_backups/`. For each governance file in scope, report last-modified timestamp and current line count. Output is a state snapshot. Do not modify anything yet.
2. **Decide direction.** Complete forward (most work done, remaining changes well-defined) or roll back (state unclear, multiple files mixed). When in doubt, roll back. Rolling back is cheap.
3. **Execute, then verify.** Re-run state snapshot post-execution. Confirm world matches expectations. If still mixed, escalate to operator.
4. **Document briefly.** Add a short "Close-out notes" section to the just-archived session log. One paragraph, what failed and what recovery direction was taken. Not a post-mortem.

Recovery is rare by design — Steps 1–11 above are structured to prevent partial state. But the recovery path exists for the cases the structure misses.

---

## Reference — canonical truth lives here

The skill implements behaviours specified in `standing_instructions.md` and `governance.md`. When the skill and either source diverge, **the upstream source wins** — the skill is downstream.

Specific cross-references:

- **Step 1 (timestamp anchor)** — Cat 2 + DR-021.
- **Step 2 (pre-close checklist)** — `governance.md` §close-out protocol pre-close-out checklist.
- **Step 3 (split-trigger check)** — `governance.md` §close-out protocol §2 (hard session-length signals).
- **Step 4 (session record)** — Cat 2 close-out actions + `governance.md` close-out protocol.
- **Step 5 (`current_state.md` update)** — Cat 2 close-out actions.
- **Step 6 (`v3_build_picture.md` update)** — Cat 1 "V3 build picture rendered inline at session open — conditional" (the close-side update is what enables the open-side render).
- **Step 7 (`standing_instructions.md` sweep)** — Cat 2 + the implicit rule that instruction edits happen during substantive work, not close-out.
- **Step 8 (opening prompt generation)** — Cat 2 "Operator workflow: copy-paste opening prompts, current" + `governance.md` "Open and close-out economy."
- **Step 9 (sweep `.close_out_backups/`)** — pattern established Session 43 (Session 42's stale artefact caught at Session 43 open).
- **Step 10 (closing summary)** — Cat 2 "Closing summary to operator: short, high-level, crucial detail only" + `governance.md` "Closing summary — when to omit."
- **Step 11 (post-close verification)** — Cat 2 "After any long-running script call, re-run a state-snapshot read to verify canonical state matches expected."
- **Step 12 (launch headless runner)** — Cat 2 (Session 198 opening-prompt auto-runner amendment) + operator instruction Session 199; the action-half that consumes the Step 8 opening prompt. Strictly last, all-verification-passed gate.

When `standing_instructions.md` or `governance.md` is updated, this skill is reviewed at the next session open and updated if any procedural element shifted. The `bethub-session-open` skill catches that review explicitly via the drift-check.

---

## Notes on the standing-instruction–skill–artefact triangle

Three layers of governance interact at session-close:

1. **`standing_instructions.md`** — the operator's control surface. Authoritative. Read in full at every session open.
2. **`bethub-session-open` and `bethub-session-close` skills** — the procedural implementations of the standing instructions. Authored to match; reviewed when instructions change.
3. **`current_state.md`, `sessions/SESSION_<N>.md`, `v3_build_picture.md`** — the artefacts the skills read from and write to.

The skills are *upstream of the artefacts* (skills modify artefacts) but *downstream of the instructions* (instructions specify what the skills do). Editing a skill does not change a standing instruction. Editing an instruction triggers a skill review.

This triangle is what protects against the Session 11 lesson (split rather than push through), the Session 42 lesson (operator-confirmed forward routing before close-out), and the Session 43 lesson (mid-session pivots applied to standing instructions, not absorbed silently into skill bodies).
