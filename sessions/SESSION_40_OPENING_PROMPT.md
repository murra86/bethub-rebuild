Open Session 40 of the v3 rebuild arc. Run `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` via Desktop Commander start_process to anchor on actual current Adelaide local time per DR-021. Pre-flight directory listing of rebuild folder root after named reads, before substantive work.

**Session purpose: triage Saturday API probe outcomes and route forward.** Tool routing: Chat. Anticipated 30-90 min depending on probe outcome (clean / partial / didn't run).

**Saturday probe ran 2026-05-02 ACST.** Three branches depending on what's at `dr029/2_1_race_data/api_probe_data/` and `api_probe_report.md`:

**Branch A — probe ran clean (4 races, both Betfair + Racing API streams captured).** Primary deliverable: triage probe report findings against the five questions; draft Fix 4 brief if cadence findings are clear; sequence Fix 5 brief drafting (venue harmonisation + retroactive race-key merge — independent of probe but kept paired). Update WIP §1, §13, §17. Anticipated 60-90 min.

**Branch B — probe ran partially (2-3 races, or one stream failed).** Primary deliverable: triage what's there; decide whether the partial data is enough to inform Fix 4 or whether a follow-up probe is needed; draft follow-up probe brief if so. Anticipated 45-75 min.

**Branch C — probe didn't run (VPS down, credentials failed, all metros cancelled, operator-side delay).** Primary deliverable: diagnose why, reschedule, hand back to operator for setup. Brief itself is unchanged and still valid for the rescheduled run. Anticipated 15-30 min.

**Required reads (in order):**

1. `~/Desktop/Projects/bethub-rebuild/work_in_progress.md` — full Session 39 close state.
2. `~/Desktop/Projects/bethub-rebuild/sessions/SESSION_39.md` — Session 39 outcomes.
3. `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/api_probe_brief.md` — what was specified.
4. `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/api_probe_report.md` IF PRESENT — what was captured. If not present, jump to Branch C diagnosis.
5. `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/api_probe_data/manifest.json` IF PRESENT — execution summary, captured race counts, `api_events` log.

Reference-only — read on demand:

- `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/surgical_fix_3_report.md` §6 — the empirical surprise that motivated the probe; useful when interpreting findings against the Fix 3 baseline.
- `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/source_review_report.md` §5.3 — the inferred-but-empirically-wrong API-shape assumptions the probe was designed to resolve.
- `~/Desktop/Projects/bethub-rebuild/dr029/2_1_race_data/inspection_report.md` §F — BSP/SP 0% population baseline.
- `~/Desktop/Projects/bethub-rebuild/dr029/dr029_scope.md` — for forward-routing into §2.4 / §2.6 / §2.10.

**The five questions the probe answered (or attempted to answer):**

1. When (if ever) does `r.sp.actual_sp` populate? Pre-jump? OPEN→SUSPENDED transition? SUSPENDED→CLOSED? Some time after CLOSED? Never?
2. Cross-code response-shape parity — does harness/greyhound differ from thoroughbred?
3. What fields does the API expose that the snapshot writer doesn't capture? — substantial chunk of the §2.10 API-field-inventory deliverable.
4. What's the cadence of meaningful change at 1-second granularity? — informs Fix 4 cadence design grounded in observation.
5. Race and runner identity alignment between Betfair and Racing API (and through Racing API, to bundled Sportsbet and Ladbrokes).

Triage approach for Branch A: read each of §3.1–§3.5 of the probe report against its question; route findings forward (Fix 4 design, §2.10 inventory, future cross-source join work); name anything from §4 ("anything surprising") that warrants its own routing.

**Forward routing surfaces from probe outcomes:**

- **Fix 4 (cadence design).** Probe report §3.4 (1s cadence findings) is the load-bearing input. If the report shows 1s captures meaningful change at INTENSIVE phase but not at STANDARD, Fix 4 design is "tighten INTENSIVE to 1s, leave STANDARD at current cadence." If it shows minimal change at any cadence, Fix 4 may shrink to "log silent-drop branch" only.
- **Fix 5 (venue harmonisation + retroactive race-key merge).** Independent of probe; brief drafted Session 40 or 41. Lifts the Sportsbet sponsor/locality-prefix venue cleaner from the dirty VPS tree (per WIP §16) into `subscription/racing_api.py`'s ingestion path, then runs a retroactive merge across the 60-day live-capture window to close the `with_both` cross-tab gap.
- **§2.10 (API-field-inventory).** Probe report §3.3 substantially feeds this; the §2.10 work item shrinks accordingly. Remaining §2.10 work: any Racing API fields not already covered by probe §3.5; any soft-book scraper fields beyond what's currently captured; the field-by-field inventory deliverable for v3 contract lock.
- **Cross-source join work (future).** Probe report §3.5 surfaces the Betfair ↔ Racing API ↔ Sportsbet/Ladbrokes alignment surface. Designing the join algorithm is downstream — Session 41+ work after Fix 4 + §2.10 land. May warrant its own DR-029 sub-section or fold into §2.5 / §2.7.

**Standing instructions in WIP. Name DR-027, DR-028, DR-029 in orientation summary.** Filesystem note: Claude.ai session, Desktop Commander wired to the Mac filesystem; bash sandbox does not reach the rebuild folder OR the VPS, all rebuild operations route through Desktop Commander or the projects-filesystem MCP server. **For new files in the rebuild folder, prefer `projects-filesystem:write_file` for fresh artefacts and `projects-filesystem:edit_file` for edits to existing files** (cleaner than Desktop Commander's `write_file`/`edit_block` for this workflow). **REPL discipline:** prefer write-script-to-/tmp + start_process(python3 /tmp/script.py) over interactive REPL paste for any multi-line Python (Session 30 standing).

**Plain-language operational/gambling-framed framing instruction (Session 31) and operational/analytical line discipline drift watch (Session 32) both apply.**

**Reinforced Sessions 38-39 — short responses, baby steps, plain operational language. Operator does not do well with long descriptions or lots of content covered in one response. Lead with the one decision or one piece of information the operator needs to react to; defer the rest to the next response. When the work would naturally produce a long response, break it across multiple short rounds rather than batching into one wall of text.** This applies to operator-Claude conversational text, not to artefact deliverables (briefs, specifications, session records) where structured length serves the artefact's purpose. If presenting a triage of multiple findings (e.g., walking through five questions' answers), section-by-section walkthrough at one section per round held cleanly through Session 39's brief review and is the default cadence.

**STANDING INSTRUCTION (locked Session 39, applies all sessions forward) — operator-facing presentation discipline:**
- **Short.** Brevity is not a tradeoff against thoroughness; it is the requirement.
- **Plain language.** Operational/gambling-framed. No essays, no academic register, no hedge-stacking.
- **Crucial information only.** What the operator needs to make a decision or understand the operational shape. Cut everything else.
- **Not an essay every time.** If a topic naturally splits into multiple rounds, split it. Do not batch.
- **Decision-maker framing.** Lead with the call, the choice, or the load-bearing fact. Background and reasoning come after, only if the operator asks.
- This applies to ALL operator-facing conversational responses — triage, walkthroughs, presenting findings, asking for routing calls, summarising progress, anything. Artefact deliverables (briefs, specifications, session records, opening prompts) are exempt because their structured length serves the artefact's purpose.
- Section-by-section walkthrough at one section per round (per Session 39's brief review) is the default for multi-part content.

**State of rebuild folder root at Session 40 open:** seven core canonical .md at root (README, architecture, decisions, governance, v3_data_requirements, vision, work_in_progress). DR-029 artefacts in dr029/: dr029_scope.md (locked, with Session 37 close addendum on §2.1 and Session 38 close addendum on §2.2); 2_1_race_data/{api_probe_brief.md [Session 39], api_probe_data/ [Saturday execution, IF PRESENT], api_probe_report.md [Saturday execution, IF PRESENT], brief.md, inspection_report.md, notes.md, source_review_brief.md, source_review_report.md, surgical_fix_1_2_brief.md, surgical_fix_1_2_report.md, surgical_fix_3_brief.md, surgical_fix_3_report.md, vps_drift_check.md}.

**Open items in:** WIP §1 (Fix 4 + Fix 5 brief drafting now unblocked by probe — depending on findings); §13 (§2.10 carry — substantially fed by probe §3.3); §16 (VPS in-flight work + metadata-backfill log-permission residual; Saturday's tomorrow's-the-test for the chown fix per Session 37 — verify outcome at session open); §17 (Saturday API observation probe — Session 40's primary read).

**Open items out:** none new from Session 39.

**Governing DRs:** DR-029 (active arc; §2.1 closed-with-known-debt-named Sessions 34+37 addendum; §2.2 closed Session 38; Saturday probe drafted Session 39, executed out-of-session post-39, triaged Session 40); DR-027/028 (cross-DB discipline — probe was read-only against Betfair API direct + Racing API direct, no `capture.db` boundary surface); DR-021 (timestamp).
