# Session 42 — Branch X: Phase 1 Project creation + Phase 2 governance work (docs, uploads, instructions)

**Opened:** 2026-05-01 11:07 ACST (Friday)
**Closed:** 2026-05-01 12:51 ACST (~104 minutes, single calendar day)
**Tool routing:** Claude Chat
**Governing DRs invoked:** DR-029 (active arc — but no DR-029 substantive work this session); DR-027/028 (cross-DB discipline — not invoked, no boundary surface this session); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 11:07 ACST` at open and `2026-05-01 12:51 ACST` at close. Friday — probe scheduled for Saturday 2026-05-02. **Branch X confirmed at open** (probe not yet run; opening prompt's Branch X fallback applied).

## Session shape

Probe-independent governance work. Two probe-independent tracks ran in series:

1. **Phase 1 of session operations proposal** — operator-side: created empty `bethub-rebuild` Claude Project via claude.ai sidebar.
2. **Phase 2 of session operations proposal** — Chat-side: docs, uploads, Project custom instructions. Skills (deliverables 5-7) deferred to Session 43 per operator-chosen pace; **operator subsequently re-routed Session 43 to also be governance/skills work, with probe-triage moved to Session 44** (probe runs Saturday).

In the middle of Phase 2's section 2 mid-walkthrough, the operator surfaced four standing-instruction edits which were addressed before continuing — see "Standing instructions edits" below.

## What was delivered

### 1. Empty `bethub-rebuild` Claude Project created (Phase 1)

Operator-side via claude.ai sidebar. Project description: "Data capture/analytic and operational/execution tool for EV driven betting." Empty knowledge base, empty instructions, no files.

### 2. Four standing-instruction edits applied to `standing_instructions.md`

- **Edit 1 (Category 2 timestamp anchor):** appended note that sessions can run over multiple calendar days — operator may pause mid-session and resume the next day; re-anchor on resumption; close-out actions only fire when operator actually closes.
- **Edit 2 (Category 2 close-out actions, directory cleanup sweep):** appended explicit "keep the rebuild folder structure clean" point — tidy beats messy, but historical records (session logs, locked DRs, scope addenda, agent review artefacts, locked briefs and reports) are not clutter, they are governance and reference material.
- **Edit 3 (Category 4 governance discipline, bet-cycle analysis):** generalised the "insurance bets and free bets are always analysed as a cycle" instruction to **any bet whose outcome drives downstream behaviour** — examples: insurance + free bet, bonus-back-on-winnings, any future promo class with the same shape (cashback-on-loss, multi-bet-bonuses, refund-if-fav-wins, etc.).
- **Edit 4 (Category 4 governance discipline, Betfair as canonical source):** flag-only — operator surfaced intent to extend "Betfair as canonical source" to *all* bet records (including manually-logged softbook bets carrying Betfair-side identifiers as canonical join key). Recognised mid-walkthrough as load-bearing enough to belong in `architecture.md` and possibly a new DR. Logged as pending architectural extension; surfaced as input to Fix 5 brief drafting and to the post-DR-029 documentation pass.

All four edits applied via `Desktop Commander:edit_block` with full pre-read verification.

### 3. `project_context.md` written at rebuild root

Created at `/Users/tim/Desktop/Projects/bethub-rebuild/project_context.md`. ~27 KB, ~2,800 words, six sections, drafted via section-by-section walkthrough one section per round per Category 1 standing instruction. Voice: third-person ("Tim is..."). Substantive operator-driven content additions throughout:

1. **What this project is** — bethub-rebuild as v3 architectural rebuild; design target ~30+ AU bookmaker accounts (current ~10-15 actively in rotation, larger footprint aspirational); built from lessons learned in v2; v3 architectural goals (coherent design from locked decisions, improved operating/execution efficiency, basis for analytical capability later).
2. **Who the operator is** — Tim, Adelaide, business/governance background, full-time professional sports/racing trading goal; decade of operational experience predominantly sign-up-bonus and deposit-bonus based; EV-driven betting relatively new direction; account hygiene mostly intuition-driven (browsing-activity / per-account router/SIM / AdsPower fingerprint isolation as new territory); mathematical and probability foundation actively being learned (Bayes, CLT, binomial, PDFs studied; still early); analytical layer deliberately deferred until both data layer and mathematical foundation are ready.
3. **The four racing strategies** — operational reality (Strategy 1 = ~95% of profit today, Strategy 2 = ~5%, Strategies 3-4 produce no profit today — aspirational growth); Strategy 1 detailed three-outcome breakdown (runner wins is profit, target 2:1-8:1 odds with optimal-band-discovery as analytical project for later; runner outside placings is pure loss; runner inside placings triggers refund typically as free bet converting ~70% of face value, loss mitigation not break-even); Strategy 2 two sub-shapes including bonus-winnings; Strategy 3 SGM bonus-back scoped not built; Strategy 4 — operator does not yet have working understanding of execution mechanics, to learn later; standing analysis convention.
4. **Key vocabulary** — account/book/account-at-book per DR-022 (operator chose to keep "account-at-book" rather than rename); operational vs analytical line; three databases; Betfair as canonical source with pending architectural extension flagged; Decision Records.
5. **Active arc — DR-029** — what DR-029 is, ten in-scope items, where the arc is right now, what gates v3 build.
6. **Tooling and environment** — Claude Chat vs Claude Code division of labour, Desktop Commander as default, Project knowledge base + skills approach (Phase 2 forward), live database queries, operator workflow, multi-agent review for material strategic decisions (operator-validated approach with rationale on different model failure modes).

### 4. `current_state.md` slimming skipped

Already at 60 lines / ~3.5 KB — well under proposal target. No work needed; will evolve naturally as session-close skill gets written in Session 43.

### 5. Eight canonical docs uploaded to Project knowledge base

Operator-side via Project Files area:

| # | File | Lines |
|---|---|---|
| 1 | project_context.md | 210 |
| 2 | standing_instructions.md | 111 |
| 3 | dr029_scope.md | 259 |
| 4 | v3_data_requirements.md | 203 |
| 5 | governance.md | 250 |
| 6 | decisions.md | 947 |
| 7 | architecture.md | 684 |
| 8 | vision.md | 36 |

Total ~2,700 lines, ~256 KB, 4% of project capacity used. Indexing started at upload.

### 6. Project custom instructions written and saved

~180 words pasted into Project Instructions field. Points at three orientation reads in order; names standing-instruction categories at high level; reaffirms operator-facing presentation discipline; reaffirms Tim as strategic decision-maker / Claude as software decision-maker.

### 7. Premature close-out + reopen lesson

First close-out attempt at 12:40 ACST produced a Session 42 record + Session 43 opening prompt shaped for probe triage. Operator clarified the actual intent: finish governance work *today* in a fresh Session 43, with probe-triage moving to Session 44 (Saturday). Premature close artefacts deleted (`sessions/SESSION_42.md` and `.close_out_backups/SESSION_43_opening_prompt.md`); session reopened; close-out redone with the corrected forward-routing. **Lesson:** when "close session" is invoked, default-routing the next session to the next-anticipated-substantive-work-arc (probe triage in this case) is wrong if the operator actually wants the next session to continue an in-flight workstream (Phase 2 skills). Ask the operator at close-out time which work-arc Session N+1 should open against, especially when multiple in-flight arcs are live.

## Phase 2 status after Session 42 close

| # | Deliverable | Status |
|---|---|---|
| 1 | `project_context.md` | ✅ Written |
| 2 | Slim `current_state.md` | ⏭️ Skipped (already light) |
| 3 | Upload 8 canonical docs | ✅ Done |
| 4 | Project custom instructions | ✅ Done |
| 5 | `bethub-session-open` skill | ⏳ Session 43 (today) |
| 6 | `bethub-session-close` skill | ⏳ Session 43 (today) |
| 7 | `bethub-brief-drafting` skill | ⏳ Session 43 (today) |

Phase 2 finishes in Session 43 (skills); probe triage routes to Session 44 (Saturday).

## Standing-instruction adherence check

- DR-021 timestamp anchor at open and both close attempts — clean.
- Required reads completed in order — clean.
- Pre-flight directory listing before substantive work — clean.
- DR-029 / DR-027 / DR-028 / DR-021 named in orientation — clean.
- Desktop Commander / projects-filesystem routing — clean (one tool_search reload mid-session for `start_process`, one for `write_file`; recovered cleanly).
- Operator-facing presentation discipline (Category 1) — held cleanly. Section-by-section walkthrough applied throughout project_context.md drafting.
- Don't-drift-to-alternatives — held cleanly during Phase 2 execution.
- Multi-day session note (new edit this session) not exercised — single calendar day session.
- **New lesson surfaced:** close-out next-session-routing should be operator-confirmed when multiple in-flight arcs are live (see Section 7 above).

## Open items

**No new substantive open items.** Carrying forward:

- WIP §16 (VPS in-flight work + metadata-backfill log-permission residual). Tomorrow's scheduled `racing-metadata-backfill.service` run at 2026-05-01 23:30 ACST is the diagnostic for whether Fix 2's chown held.
- WIP §17 (Saturday API observation probe — runs tomorrow 2026-05-02).
- WIP §13 (§2.10 carry — to be substantially fed by probe report).
- **Phase 2 deliverables 5-7** (three skills) — Session 43 today.
- Pending architectural extension flagged Session 42 — "Betfair as canonical source" extending to all bet records including softbook. Lands in Fix 5 brief drafting and post-DR-029 documentation pass.

## Session close state

- Rebuild folder root: 7 canonical .md + `current_state.md` + `standing_instructions.md` + `session_operations_proposal.md` + `project_context.md` = **11 .md files at root**, plus 6 subdirectories.
- WIP unchanged this session — stays in place during Phase 2 transition as fallback per Session 40 plan.
- `.close_out_backups/` empty (premature opening prompt deleted at reopen).
- One `.DS_Store` swept at first close attempt (verified zero remaining).
- Probe brief unchanged.
- Claude Project `bethub-rebuild` operational with knowledge base loaded, indexing finishing in background, custom instructions in place.

## Forward to Session 43

Session 43 today (Friday afternoon ACST), Phase 2 finish — three custom skills authored. Probe runs Saturday; Session 44 triages probe outcomes. Seventeenth consecutive non-early-close session.
