# Session 43 — Phase 2 partial: standing_instructions.md edits for session-open ritual

**Opened:** 2026-05-01 12:59 ACST (Friday afternoon)
**Closed:** 2026-05-01 13:51 ACST (~52 minutes, single calendar day)
**Tool routing:** Claude Chat
**Governing DRs invoked:** DR-029 (active arc — but no DR-029 substantive work this session); DR-027/028 (cross-DB discipline — not invoked, no boundary surface this session); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 12:59 ACST` at open and `2026-05-01 13:51 ACST` at close. Friday — probe scheduled for Saturday 2026-05-02. Branch X (probe-independent) confirmed at open per Session 42's forward-routing.

## Pre-flight checks

- **Rebuild folder root:** 11 .md files, expected. No phantom files at open.
- **VPS metadata-backfill diagnostic (WIP §16):** `racing-metadata-backfill.service` last ran 2026-04-30 14:02 UTC (= 23:32 ACST) — completed cleanly, 5,458 races / 67 runners synced across 60 dates, **no PermissionError**. Fix 2's chown is holding empirically. Note: the opening prompt assumed a 23:30 ACST run; the timer actually fires at 14:00 UTC daily (~23:30 ACST during ACST, ~midnight during ACDT). Next run scheduled tonight 23:30 ACST.
- **Stale phantom:** one `.close_out_backups/SESSION_43_opening_prompt.md` artefact from Session 42's premature close survived its claimed deletion; swept at Session 43 close.

## Session shape

Probe-independent governance work. **Phase 2 deliverable 5 (`bethub-session-open` skill) was opened but not closed.** Session pivoted mid-flight — frontmatter for the skill was drafted in round 1, then the operator surfaced four content additions to `standing_instructions.md` itself rather than to the skill body. The instructions belong upstream of the skill (the skill implements them), so the session re-routed to apply the standing-instruction edits first. Skill bodies (deliverables 5-7) carry forward to Session 44.

## What was delivered

### 1. `bethub-session-open` skill — frontmatter drafted, body deferred

Frontmatter for `bethub-session-open/SKILL.md` drafted and operator-approved. Captures: trigger phrases (open session N, starting session N, let's open session N, kick off session N, fresh chat in the bethub-rebuild Claude Project); behaviours encoded (timestamp anchor with calendar-aware comparison, required reads in order, pre-flight directory listing, naming governing DRs, calendar-calibrated short recap and objective, v3 build picture rendered inline); negative scope (do not use for non-bethub-rebuild sessions or ad-hoc questions during an already-open session). Body drafting deferred to Session 44 so the body can implement the new Cat 1 / Cat 2 standing instructions in lockstep.

### 2. Five new standing instructions applied to `standing_instructions.md`

Six edits in two `Desktop Commander:edit_block` passes (five new Cat 1 instructions, one Cat 2 pointer). All edits operator-approved before application.

**Cat 1 (How Claude communicates with the operator) — five additions:**

- **Default to luddite-analyst-gambler brevity.** Tightens the default register beyond existing brevity instructions. Operator is high-level, wants the call/fact/next move, not the reasoning chain.
- **Escalate to detail only when warranted.** Material decisions, risks if fast-tracked, architectural trade-offs warrant detail — flag explicitly with "this deserves a little detail" before delivering. Operator opts in, doesn't get it by default.
- **Calendar-calibrated session open.** Compare current Adelaide local time against previous session close. Same-workday (same calendar date OR fresh open between 00:00–04:00 ACST and previous close on prior calendar date) → tight 1–2 sentence recap + 1–2 sentence objective. New-workday → longer recap with arc state, what closed, what's in flight, this session's objective.
- **V3 build picture rendered inline at session open — conditional.** Mermaid/table visual of v3 build streams with consistent status indicators (`in flight`, `unfinished`, `blocked-on-<X>`, `waiting-on-<date>`, `parked`, `done`). Source of truth lives in `v3_build_picture.md`. **Render only when stream state has moved since previous open** — skip silently otherwise. Update artefact at session close when streams move.
- **Drift-check the previous session's close-out at the start of every fresh open.** Verify `current_state.md` last-updated timestamp matches previous close, `sessions/SESSION_N.md` exists, `v3_build_picture.md` updated if streams moved. Cheap diagnostic; addresses Session 42 premature-close-out failure mode (mismatches invisible until next open).
- **Open-items delta — conditional.** Surface delta in open items since previous open (closed, newly opened, overdue or close to it). Render only when meaningful delta — skip silently otherwise. Full list lives in `current_state.md`.

**Cat 2 (Session protocol) — one pointer:**

- After orientation summary, deliver the calendar-calibrated recap, drift-check, conditional v3 build picture, and conditional open-items delta per Cat 1. Pointer-only; full text lives in Cat 1.

### 3. Conditional rendering pattern established

Two of the five new Cat 1 instructions (v3 build picture, open-items delta) carry an explicit "render only when state moved, skip silently otherwise" rule. This is a deliberate design choice — the operator-Claude review surfaced that rendering these unconditionally would become ritual noise. The conditional pattern preserves signal when it matters and saves attention when it doesn't. Worth noting as a precedent for any future ritual element.

### 4. Pending operator-side action

Updated `standing_instructions.md` (now 128 lines, was 111) needs to be **re-uploaded to the bethub-rebuild Claude Project knowledge base**, replacing the version uploaded Session 42. Between-session work; not gating Session 44 skill body drafting (the local file is canonical for in-session reads via Desktop Commander).

### 5. V3 build picture artefact — not yet authored

`v3_build_picture.md` referenced as source of truth in the new Cat 1 instruction but **not yet created**. Authoring carries forward — naturally pairs with skill body drafting in Session 44 since the skill renders the picture inline. Stream breakdown is operator-redline; Claude proposes first draft.

## Phase 2 status after Session 43 close

| # | Deliverable | Status |
|---|---|---|
| 1 | `project_context.md` | ✅ Written (Session 42) |
| 2 | Slim `current_state.md` | ⏭️ Skipped (Session 42 — already light) |
| 3 | Upload 8 canonical docs | ✅ Done (Session 42) |
| 4 | Project custom instructions | ✅ Done (Session 42) |
| 4a | **Re-upload `standing_instructions.md` to Project** | ⏳ Operator action between sessions |
| 5 | `bethub-session-open` skill | ⏳ Frontmatter drafted; body Session 44 |
| 6 | `bethub-session-close` skill | ⏳ Session 44 |
| 7 | `bethub-brief-drafting` skill | ⏳ Session 44 |
| 8 | `v3_build_picture.md` artefact | ⏳ Session 44 (paired with skill body) |

Phase 2 close pushed to Session 44. Probe-triage moves to Session 45.

## Standing-instruction adherence check

- DR-021 timestamp anchor at open and close — clean.
- Required reads completed in order — clean (current_state → standing_instructions → project_context → SESSION_42 → §4.3 + §7 of session_operations_proposal).
- Pre-flight directory listing before substantive work — clean.
- DR-029 / DR-027 / DR-028 / DR-021 named in orientation — clean.
- Desktop Commander / projects-filesystem routing — clean.
- Operator-facing presentation discipline (Cat 1) — held. Section-by-section per skill held; pivoted cleanly when operator changed subject mid-flow.
- Don't-drift-to-alternatives — held.
- Multi-day session note (added Session 42) not exercised — single calendar day session.
- **New behaviours not yet exercised:** the five Cat 1 instructions added this session were *authored* this session — they govern Session 44 forward, not Session 43.

## Open items

Pointer-only — items themselves live in `work_in_progress.md` until WIP is archived in Phase 3.

- **Phase 2 deliverables 5-7** — three skill bodies (`bethub-session-open`, `bethub-session-close`, `bethub-brief-drafting`). `bethub-session-open` frontmatter drafted; bodies Session 44.
- **Phase 2 deliverable 8** — `v3_build_picture.md` artefact authoring (Session 44, paired with `bethub-session-open` body).
- **Phase 2 operator-side** — re-upload `standing_instructions.md` to Project knowledge base.
- **WIP §1** — Fix 4 (cadence, needs probe) and Fix 5 (venue harmonisation, unblocked) brief drafting.
- **WIP §13** — §2.10 carry, substantially fed by probe report §3.3.
- **WIP §16** — VPS in-flight work; metadata-backfill log-permission residual closed empirically this session (Fix 2 chown holding; clean run 2026-04-30 23:32 ACST).
- **WIP §17** — Saturday API observation probe runs tomorrow 2026-05-02. Operator setup checklist in WIP. Triage Session 45 (was Session 44 pre-pivot).
- **Pending architectural extension flagged Session 42** — "Betfair as canonical source" extending to all bet records including softbook. Lands in Fix 5 brief drafting and post-DR-029 documentation pass.

## Open items out

None new from Session 43.

## Session close state

- Rebuild folder root: 11 .md unchanged from Session 42 close (`standing_instructions.md` edited in place, 111 → 128 lines).
- WIP unchanged.
- `.close_out_backups/` empty (one stale artefact from Session 42 swept at close).
- Sessions: SESSION_43.md added; opening prompt for Session 44 follows below.
- Probe brief unchanged.
- Claude Project `bethub-rebuild` operational; Project knowledge base needs `standing_instructions.md` re-upload.

## Forward routing — confirmed with operator

Session 44 continues Phase 2: draft `bethub-session-open` body (implementing the five new Cat 1 instructions plus one Cat 2 pointer), author `v3_build_picture.md`, then `bethub-session-close` and `bethub-brief-drafting` per operator's chosen pace.

**Probe-triage (originally Session 44) moves to Session 45** — Saturday afternoon ACST or whenever the operator opens after the probe completes.

Eighteenth consecutive non-early-close session.
