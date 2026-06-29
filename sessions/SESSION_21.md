# Session 21 log

**Date:** 2026-04-29 (Adelaide local, ACST)
**Open:** 12:55 ACST
**Close:** ~15:30 ACST (approximate; close-out script run time)
**Duration:** ~2.5 hours substantive work; first session under new open-and-close-out economy directive

---

## Scope going in

Per the Session 20 closing prompt:

(1) Lock the two remaining structural choices for the assessment-agent prompts — Question A (open-questions agent runs in parallel with the three assessors, sees only the four documents, never their assessments) and Question B (judge synthesis sees the four original documents plus the four agent outputs).

(2) Draft the three assessment-agent prompts (software-developer, project manager, skeptic) plus the open-questions agent prompt, with the software-dev prompt drafted first as a worked example for the operator to react to. Operator does higher-level review of each prompt at end of session.

Suggested approach: software-dev prompt first as worked example for operator to react to; PM and skeptic prompts will be near-clones with only the role-brief paragraph swapped.

Carry-out triggers: context tightening, operator fatigue, scope larger than session bandwidth. Bias toward closing early.

## Scope completed

**(1) Question A and Question B locked.** Operator confirmed both with operator-Claude leans intact. Reasoning recorded in operator-Claude conversation:

- **Question A — yes, parallel.** The open-questions agent has a different brief (surfacing what hasn't been asked, what's been assumed without defence, what's been backgrounded that should be foregrounded) — that's an upstream job, not a downstream one, and operates on the same input the assessors operate on, not on their outputs. Two reasons to keep parallel: (a) anchoring protection — running the open-questions agent serially after the assessors would pre-shape its surface of "what's been backgrounded" by what the assessors already foregrounded, defeating its purpose; (b) the judge benefits more from genuinely independent inputs than from staged ones.
- **Question B — yes, documents plus outputs.** The judge synthesises rather than chooses; to do that well, the judge needs ground truth to verify assessor claims against. Without source documents, the judge is reduced to proxy signals (confidence, reasoning-chain length) rather than substantive calls. Secondary benefit: if agents misread the documents, the judge can catch it.

**(2) Software-developer assessment-agent prompt drafted** as `orchestration_pack/prompt_software_dev.md` (132 lines, ~2,200 words excluding inline-paste markers for the four documents). Per Session 20's locked structural choices: inline document paste markers for all four documents (decision-under-review, v3-data-requirements, architecture-current, data-layer-current); grouped question structure with three sets (Set 1 — four B.7 questions; Set 2 — two v3-stakes questions from Sessions 18–19; Set 3 — DUR §6 secondary asks as framing lenses); tight prompt with role-brief paragraph specifying the how-it's-built lens (with explicit guard-rails against straying into PM or skeptic territory); hybrid output format with bookending sections (lead coherence-of-framing assessment, closing open-questions-you-would-want-answered); lead-paragraph operator-background calibration framing; pairing weighting between Question 1.1 (bet schema) and Question 1.5 (periodic-only API) given its own labelled section after each individual answer; Question 1.4 visible as struck-through with no response expected for source-document numbering match; AccountCare-DB future-shape pushback as its own labelled output section.

**Operator higher-level review of the prompt deferred to Session 22** per operator's session-end choice, after a mid-session digression on tote-pool captures (see Operator-discoveries below). Six specific points flagged for operator attention in Session 22 (recorded in WIP open-questions): prompt length (~2,200 words pre-paste, ~8–10k post-paste), Set 3 framing-lenses placement, Question 2.2 sub-section depth, pairing-weighting placement, AccountCare-DB pushback ask placement, skeptic role-brief design for Grok stylistic-disposition handling.

**The PM and skeptic prompts (~95% identical clones with only role-brief swap) and the open-questions agent prompt are now Session 22 work**, alongside finalising the software-dev prompt after operator review. Judge synthesis prompt template likely Session 22 or 23.

## Operator-discoveries / corrections during session

**Tote-pool capture extension drafted into `v3_data_requirements.md` then fully reverted.** Mid-session, operator surfaced an idea to add Australian tote pool capture (the three TAB pools: NSW TAB, SuperTAB, UTAB; plus TABtouch as the WA pool) to the data layer, motivated by bookmaker promo classes that pay out at tote-derived values (Top Fluc, Midi Div, Top Tote, Top Tote Plus, "best of three TABs"). Operator-Claude conversation worked through the four-pool inventory, source paths (TAB Studio API for NSW TAB and SuperTAB pending Tabcorp/Racing Australia approval; Adelaide-IP native serving for UTAB; existing VPS scraper for TABtouch), capture shape (time-series + final dividends + pre-computed derived summaries), and architectural shape (folds into existing capture.db with no DR-027/DR-028 disturbance). Sportsbet promo definitions (Top Tote Plus, Top Fluc metro-only, Midi Div, Tote) supplied by operator and integrated.

The expansion was drafted into `v3_data_requirements.md` as a new section B.2.7, with change-log note at the top, B.1 in-scope and out-of-scope list extensions, and a "what this expansion does to DR-029 scope" framing. Operator then reconsidered: "let's leave this out for now. I think it complicates things too much. This can be a separate VPS edition later on." All edits fully reverted; document is byte-identical to Session 19 close state (202 lines, 12,820 bytes verified post-revert against pre-edit reading). Not lost — the conversation captured pool inventory, source paths, derived summary definitions, and operator's "could be revived as a future capture.db extension" stance, all of which now sits in WIP open-questions item 5 for future revival.

The mid-session digression-then-revert is the right outcome of the new operator pace ("one or two max three sessions per scope item") combined with operator instinct: the expansion was honest scope-expansion and would have made the multi-agent review's scope-rightness assessment messier than it needed to be at this stage.

**Governance directive applied: open-and-close-out economy.** New section added to `governance.md` by the operator at session open ("Open and close-out economy (added 29-April by Tim)"). Session 21 is the first session to apply it. Implications observed during the session: closing summary omitted in favour of the opening prompt for Session 22; mid-session narration tightened (single-line edit-pass announcements rather than per-edit commentary); state-snapshot diagnoses limited to two sentences. The directive worked cleanly — close-out reduced to mechanical scripted-promotion plus opening-prompt-as-pointer.

## Tools used

- bash (TZ command for Adelaide local time anchoring at session open and close).
- Desktop Commander: read_multiple_files, list_directory, edit_block, write_file, start_process — primary tools for filesystem operations (bash sandbox does not reach the rebuild folder).
- tool_search (loaded Desktop Commander start_process / interact_with_process / read_process_output mid-session).

## Files touched

**Created:**
- `sessions/SESSION_21.md` (this file).
- `orchestration_pack/` directory (new at session, holds prompt drafts).
- `orchestration_pack/prompt_software_dev.md` (132 lines, ~2,200 words pre-paste).

**Edited:**
- `work_in_progress.md` (Session 21 close update — table row, Where-we-are section, open-questions list renumbered Session 22, close-out tracking line, filesystem discipline note).

**Edited and fully reverted (net zero):**
- `v3_data_requirements.md` (tote-capture B.2.7 drafted then fully reverted; document byte-identical to Session 19 close state).

**Backups cleaned at session open:**
- `.close_out_backups/SESSION_20_20260429T122814/` (per Session 20 opening prompt directive; verified canonical files intact before cleanup).

**Backups created at close:**
- `.close_out_backups/SESSION_21_<timestamp>/` (containing pre-close-out copy of `work_in_progress.md` only; `SESSION_21.md` is new, no pre-state to back up).

**Pre-existed and not edited this session (no net change):**
- `decision_under_review.md`
- `decisions.md`
- `architecture_current.md`
- `data_layer_current.md`
- `governance.md`
- `vision.md`
- `README.md`
- `architecture.md`

## Lessons applied / discipline maintained

- **DR-021:** Adelaide local time anchored at session open (12:55 ACST) and re-anchored at close-out.
- **DR-028 orientation discipline:** named DR-027 and DR-028 explicitly in orientation summary at session open.
- **Pre-flight directory listing:** ran at session open per standing instruction.
- **Standing instruction on shorthand:** applied throughout operator-facing conversational text (technical labels preserved in the assessment-agent prompt artefact since assessors need them for cross-document navigation).
- **Silent-close-out-failure mitigation (Session 20 standing instruction):** state-snapshot read after each Desktop Commander long-running script call; pre-close-out state-snapshot performed; post-close-out state-snapshot will verify canonical state matches expected.
- **Open-and-close-out economy directive (Session 21 governance addition):** opening prompt for Session 22 produced as pointer document; closing summary omitted; mid-session narration tightened; state-snapshot diagnoses limited.
- **Bias toward closing early:** session closed when operator chose to defer software-dev prompt review to Session 22, rather than pushing through to draft the PM and skeptic clones in the same session.

## Open items going into Session 22

**Session 22 first priority:** operator higher-level review of the software-dev assessment-agent prompt draft (`orchestration_pack/prompt_software_dev.md`). Six specific points flagged for operator attention (see WIP open-questions item 1).

**Session 22 second priority:** draft the PM and skeptic assessment-agent prompts as near-clones of the software-dev template with only the role-brief paragraph swapped.

**Session 22 third priority:** draft the open-questions agent prompt (independent brief; runs in parallel per Question A; reads only the four documents).

**Session 22 fourth priority (likely carries to Session 23):** draft the judge synthesis prompt template (sees the four original documents plus the four agent outputs per Question B; synthesises rather than chooses).

**Session 23+ (provisional):** finalise all prompts; package doc suite for hand-off; operator runs assessments in separate sessions between sessions; subsequent session is judge synthesis run plus operator-Claude analysis of findings.

**Operator pre-decision-homework, separate from orchestration sessions:**
- Vendor scan for third-party odds-feed vendors (Question 2 sub-question 6b Option D — see `data_layer_current.md` §5.4).
- VPS tunnel restart (~/Library/LaunchAgents/com.bethub.vps-tunnel.plist; tunnel down for 8+ days now).
- Tote-pool capture extension revival (parked Session 21, see WIP open-questions item 5).

**Parked separately:**
- Operator-Claude context-retention concern from Session 17.
