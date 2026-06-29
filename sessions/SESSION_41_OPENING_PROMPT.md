Open Session 41 of the v3 rebuild arc. Run `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` via Desktop Commander start_process to anchor on actual current Adelaide local time per DR-021. Pre-flight directory listing of rebuild folder root after named reads, before substantive work.

**FIRST DECISION at session open: has the Saturday probe run yet?**

The probe is scheduled for Saturday morning ACST 2026-05-02. If Session 41 opens before Saturday (e.g., later Friday 2026-05-01), the probe has not run yet — go to Branch X. If Session 41 opens on Saturday afternoon/evening or later, check `dr029/2_1_race_data/` for probe outputs — go to Branch A/B/C.

Check the timestamp anchor against 2026-05-02 ACST and check whether `dr029/2_1_race_data/api_probe_report.md` exists. That tells you which branch.

**Branch X — probe has NOT run yet (Session 41 opens Friday 2026-05-01).** Probe-independent work. **Operator's stated priority: complete the governance work today.** The session operations proposal at `session_operations_proposal.md` was written and accepted in principle in Session 40. Operator wants the documentation parts of Phase 2 done today, not deferred to Session 42-43. Specifically:

- Extract `standing_instructions.md` from WIP — pull the forty-or-so standing instructions out into one organised file, categorised (not chronological). This is operator's control surface for how Claude works with them. Operator wants section-by-section review of this file as it's built — same cadence as the proposal review (one category per round, plain language, decision-shaped).
- Build slim `current_state.md` — the live working state file that replaces the top of WIP.
- WIP itself stays in rebuild folder during the transition as a fallback. Don't delete.
- Deferred to a later dedicated session: Project upload (claude.ai-side), skill authoring.

Other Branch X options if operator surfaces them: Fix 5 brief drafting (venue harmonisation + retroactive race-key merge — independent of probe per WIP §16), or Phase 1 of session operations proposal (create empty `bethub-rebuild` Claude Project). But governance work is the stated priority.

Tool routing: Chat. Anticipated 90-180 min for the governance work.

**Critical context-retention note for Session 41:** Session 40 ended with operator frustration that Claude lost context about doing the governance work today, repeatedly drifted to other topics (Fix 5, taking a break, options menus) when the operator had been clear they wanted governance done today. Do NOT drift. When operator says "do the governance work," do the governance work. Don't propose alternatives. Don't ask if they want a break. Don't run ahead and ask category-structure questions before starting — propose the structure and start writing, bring it for review section by section.

**Branch A — probe ran clean (4 races, both Betfair + Racing API streams captured).** Primary deliverable: triage probe report findings against the five questions; draft Fix 4 brief if cadence findings are clear; sequence Fix 5 brief drafting (independent of probe). Update WIP §1, §13, §17. Tool routing: Chat. Anticipated 60-90 min.

**Branch B — probe ran partially (2-3 races, or one stream failed).** Primary deliverable: triage what's there; decide whether the partial data is enough to inform Fix 4 or whether a follow-up probe is needed; draft follow-up probe brief if so. Anticipated 45-75 min.

**Branch C — probe didn't run as scheduled (VPS down, credentials failed, all metros cancelled, operator-side delay).** Primary deliverable: diagnose why, reschedule, hand back to operator for setup. Brief itself is unchanged and still valid for the rescheduled run. Anticipated 15-30 min.

**Required reads (in order):**

1. `~/Desktop/Projects/bethub-rebuild/work_in_progress.md` — full Session 40 close state.
2. `~/Desktop/Projects/bethub-rebuild/sessions/SESSION_40.md` — Session 40 outcomes (governance + meta).
3. **For Branches A/B/C only:** `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/api_probe_brief.md` (what was specified) and `api_probe_report.md` (what was captured) and `api_probe_data/manifest.json` (execution summary).
4. **For Branch X only:** SESSION_39 record only if Fix 5 brief drafting is the chosen work — covers context the brief draws from.

Reference-only — read on demand:

- `~/Desktop/Projects/bethub-rebuild/session_operations_proposal.md` — for Phase 1 if chosen, or for Phase 2 sequencing context.
- `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/surgical_fix_3_report.md` §6 — empirical surprise that motivated probe; useful interpreting Branch A findings.
- `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/source_review_report.md` §5.3 — inferred-but-empirically-wrong API-shape assumptions probe was designed to resolve.
- `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/inspection_report.md` §F — BSP/SP 0% population baseline.
- `~/Desktop/Projects/bethub-rebuild/dr029/dr029_scope.md` — for forward-routing into §2.4 / §2.6 / §2.10.

**The five questions the probe answers (Branches A/B only):**

1. When (if ever) does `r.sp.actual_sp` populate? Pre-jump? OPEN→SUSPENDED transition? SUSPENDED→CLOSED? Some time after CLOSED? Never?
2. Cross-code response-shape parity — does harness/greyhound differ from thoroughbred?
3. What fields does the API expose that the snapshot writer doesn't capture? — substantial chunk of the §2.10 API-field-inventory deliverable.
4. What's the cadence of meaningful change at 1-second granularity? — informs Fix 4 cadence design grounded in observation.
5. Race and runner identity alignment between Betfair and Racing API (and through Racing API, to bundled Sportsbet and Ladbrokes).

**Forward routing surfaces from probe outcomes (Branches A/B):**

- **Fix 4 (cadence design).** Probe report §3.4 (1s cadence findings) is the load-bearing input.
- **Fix 5 (venue harmonisation + retroactive race-key merge).** Independent of probe; brief draft any session, can land Branch X.
- **§2.10 (API-field-inventory).** Probe report §3.3 substantially feeds this; the §2.10 work item shrinks accordingly.
- **Cross-source join work (future).** Probe report §3.5 surfaces the alignment surface; downstream of Fix 4 + §2.10.

**Standing instructions in WIP. Name DR-027, DR-028, DR-029 in orientation summary.** Filesystem note: Claude.ai session, **Desktop Commander is the default for ALL operations**, no bash sandbox available in this environment (bash_tool tool calls fail with "no such file"). For new files in the rebuild folder, prefer `projects-filesystem:write_file` for fresh artefacts and `projects-filesystem:edit_file` for edits, OR `Desktop Commander:write_file` / `Desktop Commander:edit_block` (cleaner than the generic `create_file` tool which writes to a different namespace and produces misleading "successfully" messages). **REPL discipline:** prefer write-script-to-/tmp + start_process(python3 /tmp/script.py) over interactive REPL paste for any multi-line Python (Session 30 standing).

**Plain-language operational/gambling-framed framing instruction (Session 31 standing) and operational/analytical line discipline drift watch (Session 32 standing) both apply.**

**STANDING INSTRUCTION (locked Session 39, applies all sessions forward) — operator-facing presentation discipline:**
- Short. Plain language. Crucial information only. Not an essay every time. Decision-maker framing.
- Section-by-section walkthrough at one section per round (per Sessions 39-40) is the default for multi-part content.
- This applies to ALL operator-facing conversational responses. Artefact deliverables (briefs, specifications, session records, opening prompts) are exempt — their structured length serves the artefact's purpose.

**State of rebuild folder root at Session 41 open:** seven core canonical .md at root (README, architecture, decisions, governance, v3_data_requirements, vision, work_in_progress) PLUS `session_operations_proposal.md` (8 .md files at root total, until Phase 3 archives WIP). DR-029 artefacts in dr029/: dr029_scope.md (locked); 2_1_race_data/ (api_probe_brief.md plus historical artefacts; probe outputs IF probe has run).

**Open items in:** WIP §1 (Fix 4 + Fix 5 brief drafting — Fix 5 unblocked any session, Fix 4 needs probe); §13 (§2.10 carry — substantially fed by probe §3.3 if probe ran); §16 (VPS in-flight work + metadata-backfill log-permission residual); §17 (Saturday API observation probe).

**Open items out:** none new from Session 40.

**Governing DRs:** DR-029 (active arc; §2.1 closed-with-known-debt-named Sessions 34+37 addendum; §2.2 closed Session 38; Saturday probe drafted Session 39, executed out-of-session post-40 IF SATURDAY+, triaged Session 41); DR-027/028 (cross-DB discipline — probe is read-only, no `capture.db` boundary surface); DR-021 (timestamp).
