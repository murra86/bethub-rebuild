# Session 20 log

**Date:** 2026-04-29 (Adelaide local, ACST)
**Open:** 11:33 ACST
**Close:** ~12:26 ACST (close-out completion; substantive work concluded earlier in session)
**Duration:** ~50 minutes substantive work; close-out ran twice (first attempt failed silently after 20–25 minutes of attempted scripted close-out; recovery completed forward at 12:26)

---

## Scope going in

(1) Multi-agent governance review orchestration. Three independent assessment agents — software dev (fresh Claude session), PM (GPT-5 or Gemini), skeptic (whichever non-Claude wasn't used for PM). Plus `open_questions.md` agent and judge synthesis (fresh Claude). Operator-Claude work for Session 20 primarily orchestration: prepare assessment-agent prompts, package the doc suite, prepare open_questions agent prompt, prepare judge synthesis prompt.

Suggested sequence in opening prompt: pin model assignments, draft assessment-agent prompt template, draft open_questions prompt, draft judge synthesis prompt, hand off for operator to run assessments in separate sessions, judge synthesis lands Session 21+.

(2) Judge synthesis if capacity permitted (realistically Session 21+).

Carry-out triggers: context tightening, operator fatigue, scope larger than session bandwidth. Bias toward closing early.

## Scope completed

Operator opened the session by reframing pace: "I want to spend a bit of time confirming both the approach, and the specific approach to executing the multi-agent review. I think we should only take one or two (max three) sessions per scope item." This shifted Session 20 from "draft prompts" to "lock the structural choices that govern prompt-drafting before drafting begins." Operator acceptance of slower deliberate orchestration — closer to the multi-agent review's stakes — was the right call.

**Locked across this session:**

1. **Model assignments.**
   - Software developer: fresh Claude Opus session.
   - PM: Gemini.
   - Skeptic: Grok.
   - Judge: fresh Claude Opus session.
   - Open-questions agent: independent — fresh Claude session or Gemini, decided when drafting the prompt.

   ChatGPT was excluded from the PM / skeptic seats because of its conservative gambling-content safety posture (operator's experience, confirmed against general public reports). Half-engagement on substantive gambling content was identified as worse than no engagement for a stress-test review. Grok was selected for skeptic over alternatives (DeepSeek; two-Gemini-prompts; drop-to-two-agents) because its stylistic disposition matches the skeptic brief. Caveat noted: Grok's prompt design matters more than other agents' — explicit framing on "stress-test means substantive critique not rhetorical performance" needs to land in the prompt itself.

2. **Structural choice 1 — Doc suite packaging: inline paste.** Each assessor receives the full text of `decision_under_review.md`, `v3_data_requirements.md`, `architecture_current.md`, `data_layer_current.md` pasted inline in the prompt in that order, with brief framing between documents. Costs prompt length, buys robustness against any "did the agent actually read the file" risk.

3. **Structural choice 2 — Question structure: grouped, not flat.** Three groups presented to the assessor:
   - **Group 1 — The four B.7 questions** from `v3_data_requirements.md` Section B.7. (#1 bet schema simplification, #2 data-layer-first sequencing, #3 data review scope rightness, #4 struck through and visible as such, #5 periodic-only API pattern with analytical bracketing).
   - **Group 2 — The two Session 18–19 v3-stakes questions** from `data_layer_current.md` §8. (Q1 reachability and continuous-fitness discipline; Q2 operational live pricing splitting into 6a Betfair / 6b soft-book A/B/C/D).
   - **Group 3 — DUR §6 secondary asks as framing/lens** (primary stress-test framing, coherence-of-framing ask, AccountCare-DB pushback ask, B.7 #1+#5 pairing ask, operator-background calibration framing). These are not standalone questions; they're how the assessor is meant to approach Groups 1 and 2.

4. **Structural choice 3 — Tight prompt with role-brief paragraph differentiating.** All three assessment-agent prompts are 95% identical. Only the role-brief paragraph differs:
   - Software-dev: technical and architectural soundness, integration risks, design alternatives a sharp engineer would push back with. *How* the thing is built.
   - PM: sequencing, scope, dependency, risk-management, delivery realism. *Whether the plan delivers.*
   - Skeptic: challenge framing itself; find the load-bearing assumption that breaks the argument; refuse to engage on stated terms when framing is shaky; locate failure rather than propose alternatives. *Where this falls apart.*

   Reasoning: tight prompts make judge synthesis tractable — when the three outputs disagree, the disagreement is substantive (about the question) rather than artifactual (about prompt shape).

5. **Structural choice 4 — Hybrid output format with bookending sections.**
   - **Lead section: coherence-of-framing assessment** (per DUR §6 secondary ask).
   - **Six question headers in the middle**, each with prose response below covering failure-mode framing (where it could break, conditions for failure, what failure looks like). No rigid sub-headings forcing checklist-shape output.
   - **B.7 Q4 visible as strikethrough**, no response expected, transparency-preserving.
   - **B.7 #1 and #5 each get individual headers, plus an explicit "B.7 #1 + #5 paired weighting" section** honouring DUR §6 pairing ask without losing per-question granularity.
   - **Closing section: open questions you'd want answered before finalising.** Catches insights that don't fit any single question.

6. **Structural choice 5 — Lead-paragraph operator-background calibration framing.** First paragraph of every prompt names: operator is not a data architect; wants real expert critique not validation; will absorb sharp pushback; soften nothing. Reasoning: this matters most for Gemini (defaults toward courteous engagement); reinforces Grok's natural disposition without overriding; sits cleanly with Claude.

**Not locked, carrying to Session 21:**

- **Question A** — does the open-questions agent run in parallel with the three assessors (sees only the four documents, never their assessments)? Operator-Claude lean: yes, in parallel — preserves diversity, prevents anchoring.
- **Question B** — does the judge see the four documents *plus* the four agent outputs (three assessments + open_questions), or just the four outputs? Operator-Claude lean: documents *plus* outputs — judge needs ground truth to verify assessor claims.

These two are the last remaining structural choices before prompt-drafting begins.

## Operator-discoveries / corrections during session

**Operator correction on shorthand language.** Mid-session, operator noted: *"Please just assume I don't remember things like the four B7 questions or DR001. Can you provide me with more detail of all these shorthand terms you use (in all responses)?"* Standing instruction added (now in operator-instructions section of work_in_progress.md): in operator-Claude sessions, terms like "B.7", "DR-027", "DUR §6", "Slice 6", and any other internal shorthand should be unwound to plain language on use. The operator does not hold these in working memory and shouldn't have to. Applied for the rest of the session and forward.

**Pace re-set on the orchestration arc.** Original Session 20 estimate was "covers preparation through to prompt drafts ready." Operator re-set to "one or two (max three) sessions per scope item," which expanded the orchestration arc to: Session 20 = lock structural choices + model assignments (done); Session 21 = finish locking remaining two choices + draft three assessment prompts and open_questions prompt for higher-level operator review; Session 22 = draft judge synthesis prompt + doc-suite packaging, hand off ready for operator to run assessments between sessions; subsequent session = judge synthesis run + analysis of findings. The slower-and-deliberate trade was operator's explicit call.

## Tools used

- bash (TZ command for Adelaide local time anchoring at session open and at close-out).
- Desktop Commander: list_directory, read_file, start_process — primary tools for filesystem operations (bash sandbox does not reach the rebuild folder).
- tool_search (loaded Desktop Commander start_process / interact_with_process / read_process_output mid-session).

## Files touched

**Created:**
- `sessions/SESSION_20.md` (this file).

**Edited:**
- `work_in_progress.md` (Session 20 close update).

**Backups cleaned at close:**
- `.close_out_backups/SESSION_19_20260429T110214/` (per Session 20 opening prompt directive; verified recoverable from canonical files before cleanup).
- `.close_out_backups/SESSION_20_20260429T115902/` (empty folder created by the failed first close-out attempt; removed since nothing was backed up — no canonical state was modified during the failure).

**Backups created at close:**
- `.close_out_backups/SESSION_20_<timestamp>/` (containing pre-close-out copy of `work_in_progress.md` only; `SESSION_20.md` is new, no pre-state to back up).

**Pre-existed and not edited this session:**
- `decision_under_review.md`
- `decisions.md`
- `architecture_current.md`
- `data_layer_current.md`
- `v3_data_requirements.md`
- `governance.md`
- `vision.md`
- `README.md`
- `architecture.md`

## Lessons applied / discipline maintained

- **DR-021:** Adelaide local time anchored at session open (11:33 ACST) and re-anchored at close-out (12:26 ACST).
- **DR-028 orientation discipline:** named DR-027 and DR-028 explicitly in orientation summary at session open.
- **Pre-flight directory listing:** ran at session open per standing instruction; ran again at close-out recovery per governance.md §4 Step 1.
- **Standing instruction on shorthand:** applied from mid-session forward; carried into work_in_progress.md operator-instructions for future sessions.
- **Bias toward closing early:** session closed when Question A and Question B were the only structural choices remaining, rather than pushing through to draft-the-first-prompt as the original opening prompt allowed.

## Close-out failure and recovery

**First attempt failed silently after 20–25 minutes.** Operator reported the failure; Claude had not detected it. Likely cause: a Desktop Commander `start_process` long-running script call that timed out client-side while completing partially server-side, with the partial-completion not visible in the conversation. State snapshot at recovery showed:

- `.close_out_backups/SESSION_20_20260429T115902/` existed but was empty (folder created, no files copied in).
- `session_log.md` did not exist (consistent with this being an orchestration session that produced no in-session active log).
- `sessions/SESSION_20.md` did not exist (archive step never ran).
- `work_in_progress.md` mtime unchanged from Session 19 close (no canonical-file modification had been applied).

**Recovery direction: complete forward.** Per governance.md §4 Step 2 — state was *clear* (no partial application to canonical files), not mixed. Roll-back was unnecessary. Forward path: write `SESSION_20.md` fresh, update `work_in_progress.md`, clean Session 19 backup, remove empty Session 20 backup folder, create new Session 20 backup of pre-close-out work_in_progress.md.

**Lesson — surfaces beyond the Sessions 15/16/19 close-out lessons.** The Session 15/16/19 lessons addressed close-out script reliability under operator-visible failure modes (visible "FILES MOVED? VERIFIED." print, verified pre-condition polarities, cleanup verification in script's closing manifest). This session's failure mode is structurally different — silent client-side timeout on a server-side-completing operation, with Claude not detecting that the close-out had failed at all. Mitigation for future sessions: at any close-out involving a Desktop Commander long-running script call, immediately re-run a state-snapshot read after the script call returns (or appears to return), to verify canonical state matches expected state. Do not trust the absence of an error message as success when the operation involves filesystem state changes. Add to operator-instructions in work_in_progress.md.

## Open items going into Session 21

**Session 21 first priority:** lock the two remaining structural choices.
- **Question A** — open-questions agent runs in parallel with three assessors, reads only the four documents, never sees their assessments. Confirm or push back.
- **Question B** — judge sees the four original documents *plus* the four agent outputs. Confirm or push back.

**Session 21 second priority:** draft the three assessment-agent prompts (software-dev, PM, skeptic) and the open-questions agent prompt. Operator does higher-level review of each draft.

**Session 22+ (per operator's session-arc plan):** finalise prompts after operator review; draft judge synthesis prompt; package doc suite for hand-off; operator runs assessments between sessions.

**Session 23+ (provisional):** judge synthesis run; analysis of findings; whatever the synthesis surfaces feeds into the build-strategy decision and DR-029 data review scoping.

**Operator pre-decision-homework, separate from orchestration sessions:**
- Vendor scan for third-party odds-feed vendors (Question 2 sub-question 6b Option D — see `data_layer_current.md` §5.4). Whether suitable commercial odds aggregators cover v3's specific day-one book list at acceptable cost. Informs whether 6b has four real architectural options or three.
- VPS tunnel restart (`~/Library/LaunchAgents/com.bethub.vps-tunnel.plist` exists but isn't running; tunnel down for 7+ days now). Doesn't block orchestration sessions; worth restoring before any v3 build session that exercises the integration.

**Parked separately:**
- Operator-Claude context-retention concern from Session 17 (folded into DUR Section 6 as secondary assessor ask; meta-governance fix is separate).
