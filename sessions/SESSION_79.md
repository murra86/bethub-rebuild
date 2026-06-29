# Session 79

**Title:** V3 build picture re-cut from DR-029 scope items to v3 build workstreams (twelve workstreams across three bands — pre-build housekeeping, eight v3 build proper workstreams, post-build pre-analytical), then pre-build scoping pass settling three load-bearing architectural calls — repo layout (single repo), build sequence (Route A: H2 first then W1), and module boundaries (top-level layout, import-graph rules as strict directed graph, tech stack as Python 3.12+ / FastAPI / SQLite WAL / SQLAlchemy Core / Alembic / React + TypeScript + Vite). Closed Session 79 with two new DRs locked: DR-030 (v3 repo layout and module-boundary discipline, covering top-level layout + import-graph rules) and DR-031 (v3 tech stack). v3 build proper substrate now fully scoped; Session 80 picks up H2 (Fix 4 + Fix 5 brief drafting) per operator's Route A routing.
**Opened:** 2026-05-04 16:15 ACST
**Closed:** 2026-05-04 17:17 ACST
**Wall-clock:** ~1 hr 02 min single sitting. Same-workday open relative to Session 78's 16:01 ACST close (~14 minute gap). Same-workday close.
**Tool routing:** Claude Chat. No Code routing required this session — re-cut, scoping pass, and DR drafting all in-Chat. Operator delegated technical-side leadership explicitly mid-session ("you are the Software and Data Architect Specialist") and held the strategic-side input role for operating-gambling routing decisions.
**Governing DRs invoked:** DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline — load-bearing for DR-030's `clients/` boundary framing), DR-029 (data-layer fit-for-purpose review — closed Session 78, referenced this session for substrate), DR-021 (timestamp anchoring), DR-019 (derived state on read — referenced for DR-030's `domain/` purity rationale). **Two new DRs locked this session:** DR-030 (v3 repo layout and module-boundary discipline) and DR-031 (v3 tech stack).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 16:15 ACST`.
Close: same command → `2026-05-04 17:17 ACST`.

Same-workday open relative to Session 78's 16:01 ACST close. ~14 minute gap. Single sitting, immediate continuation. ~1 hr 02 min wall-clock — well under split-trigger thresholds.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_79_opening_prompt.md` only (Session 78 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 16:01 ACST` matched Session 78 close; `sessions/SESSION_78.md` present (256 lines); `v3_build_picture.md` last-updated `2026-05-04 16:01 ACST` matched Session 78 close.
- Same-workday recap delivered (tight: Session 78 closed DR-029, drafted close-out paragraph; Session 79 picks up `v3_build_picture.md` re-cut).
- V3 build picture: rendered at open since stream state moved at Session 78 close (both DR-029 close-out streams `done`, carrying one session).
- Open-items delta: rendered at open — DR-029 itself closed plus six other items closed Session 78.
- Operator-side action surfaced: re-upload `governance.md` to bethub-rebuild Claude Project knowledge base. Operator confirmed re-upload mid-session.

## Session shape

Session 79 was a **two-deliverable session plus close-out DR drafting** — primary deliverable was the `v3_build_picture.md` re-cut, which landed in one round after operator-confirmed three framing calls (workstream count, dependency model, H2 status). Session then extended into a pre-build scoping pass after operator routing — "this is a pretty new session, let's keep going" — covering three architectural questions section by section per the locked Cat 1 walkthrough cadence. Operator's mid-session declaration that Claude is "Software and Data Architect Specialist" with operator only providing strategic operating-gambling input set the engagement model for the rest of the session: Claude proposed, operator confirmed (or redirected) on operating-side and routing-side calls only.

Three structural decisions confirmed across the scoping pass:

**1. Repo layout — single repo.** Software call. Operator confirmed without operating-side input ("I don't even know what a repo is, so sounds good"). DR-028 enforcement is at the code-review and contract-file level, not the repo level; splitting adds release-cycle friction without adding boundary protection. Day-0 fresh-start advantage; no cross-team coordination concerns.

**2. Build sequence — Route A (H2 before W1).** Operator strategic call. Two routes proposed: Route A (H2 housekeeping first — Fix 4 + Fix 5 brief drafting before v3 build proper starts), Route B (W1 alongside or before H2 — v3 build proper starts immediately, Fix 4 lands when convenient). Operator chose Route A — *"we're in no hurry to get this developed, and extra due diligence can never hurt"*. Saturday probe substrate (2026-05-02) is fresh enough to be captured into Fix 4 brief now.

**3. Module boundaries — three sub-questions, all confirmed.**
- *Sub-question 3a (top-level layout):* eight folders — `clients/`, `store/`, `domain/`, `workflows/`, `ui/`, `ops/`, `contracts/`, `tests/`. Pure software call.
- *Sub-question 3b (import-graph rules):* strict directed graph, arrows go down only. `domain/` and `store/` are pure leaves; `workflows/` cannot import `workflows/`. `import-linter` enforces. Pure software call.
- *Sub-question 3c (tech stack):* Python 3.12+ / FastAPI / SQLite WAL / SQLAlchemy Core / Alembic / React + TypeScript + Vite / `betfairlightweight` / `pytest` / `ruff` / `import-linter`. Two operator-side strategic questions explicitly framed (FastAPI replacing Flask, SQLite vs Postgres) — operator confirmed both with no redirects.

Round-by-round shape:

**Round 1 (open via skill).** Standard open ritual. Operator confirmed governance.md re-upload status at hand-off.

**Round 2 (operator confirms re-upload, requests proposal).** Operator: "You propose."

**Rounds 3–5 (re-cut proposal + operator confirmation + write).** Three framing calls surfaced: workstream count (12 — eight build-proper plus pre-build housekeeping plus post-build pre-analytical), dependency model (`blocked-on-<workstream>` for build sequence visibility), H2 status (`parked` not `unfinished`). Operator confirmed all three. Re-cut written to `v3_build_picture.md` as full rewrite (95 lines, was 85). `Desktop Commander:write_file` (rewrite mode, single artefact-level edit cleaner than five `edit_block` calls). Verified post-write.

**Rounds 6–7 (continuation routing + role declaration).** Operator opted for continuation: pre-build scoping pass now while context is fresh. Critically, operator declared technical-side leadership delegation — *"you are the Software and Data Architect Specialist. I'm only making strategic decisions related to operations and execution"*. Engagement model locked for rest of session.

**Round 8 (Question 1 — repo layout).** Single proposal (single repo) with reasoning + rejected alternatives. Operator confirmed.

**Round 9 (Question 2 — build sequence).** Two routes (A vs B) with strategic question framed for operator's operating-side input. Operator chose Route A.

**Rounds 10–12 (Question 3 — module boundaries, three sub-questions section by section).** Sub-question 3a (top-level layout) — confirmed. Sub-question 3b (import-graph rules) — confirmed. Sub-question 3c (tech stack) — confirmed including both operator-side strategic questions (FastAPI, SQLite).

**Round 13 (close routing).** Three pre-build scoping decisions settled. Recommended writing two DRs at close (DR-030 covering 3a+3b together; DR-031 covering 3c). Two routing questions surfaced: DR drafting at close (vs section-by-section now) and what's left this session (close vs start H2 now). Operator: "Close it up. Prepare for next session. Write the DRs."

**Rounds 14+ (close ritual).** DR-030 + DR-031 drafted and appended to `decisions.md`. Close ritual proper running.

## What was delivered

### 1. `v3_build_picture.md` re-cut from DR-029 scope to v3 build workstreams

Full rewrite of `v3_build_picture.md` (95 lines, was 85). Replaced the DR-029-stream cut with v3 build workstream cut. Three bands:

- **H — Pre-build housekeeping (2 items):** H1 (this re-cut, `in flight` Session 79), H2 (Fix 4 + Fix 5 brief drafting, `parked` until operator routes — now sequenced before W1 per Route A).
- **W — V3 build proper (8 workstreams):** W1 data layer (`vps_client` v1.0 implementation), W2 operational core (`betfair_client` v1.0 read + Streaming), W3 live pricing, W4 bet entry + write surfaces, W5 settlement worker, W6 operational store + session ops, W7 Burst Review workflow, W8 cutover. All `blocked-on-<workstream>` per the dependency graph.
- **P — Post-build pre-analytical (2 items):** P1 (§2.10 bucket-1 backward-compatible additions), P2 (analytical layer scoping as fresh DR). Both `parked` until v3 build proper completes.

Status indicator vocabulary unchanged from Session 43 lock. Render rules unchanged. Operator-redline notes refreshed for the new cut.

H2 status note: not yet updated to reflect Route A sequencing in the artefact's row text — currently reads "parked until operator routes". Updated to "next-up after Session 79 close" or equivalent at this close. **Flagged as a small structural-drift correction below.**

### 2. Pre-build scoping pass — three architectural calls settled

Three architectural questions worked through section by section across rounds 8–12:

**Q1 — Repo layout.** Single repo for v3. Software call.
**Q2 — Build sequence.** Route A (H2 housekeeping first, then v3 build proper). Operator strategic call.
**Q3 — Module boundaries.** Three sub-questions, all confirmed:
- *3a Top-level layout:* `clients/`, `store/`, `domain/`, `workflows/`, `ui/`, `ops/`, `contracts/`, `tests/`.
- *3b Import-graph rules:* strict directed graph; `domain/` + `store/` are pure leaves; `workflows/` cannot import `workflows/`; `import-linter` enforces.
- *3c Tech stack:* Python 3.12+ / FastAPI / SQLite WAL / SQLAlchemy Core / Alembic / React + TypeScript + Vite / `betfairlightweight` / `pytest` / `ruff` / `import-linter`.

Substantive scope is captured in DR-030 + DR-031 below.

### 3. DR-030 + DR-031 drafted and appended to `decisions.md`

Both DRs drafted at close per operator confirmation (route: at-close write, not section-by-section now — substance was fully locked in chat; writing was mechanical).

**DR-030 — V3 repo layout and module-boundary discipline.** Lines 951–1031 of `decisions.md`. Covers Q3 sub-questions 3a + 3b together (same architectural decision viewed two ways). Top-level layout, import-graph rules as strict directed graph, the two load-bearing rules (`domain/` imports nothing; `workflows/` cannot import `workflows/`), enforcement via `import-linter`. Names DR-028 as the upstream architectural anchor; names DR-029 close-out debt 1 (no test coverage) as the substrate `import-linter` extends. Layouts considered and rejected (flat, DDD bounded contexts, MVC).

**DR-031 — V3 tech stack.** Lines 1032–1076 of `decisions.md`. Covers Q3 sub-question 3c. Stack table per layer with rationale. Three explicitly-flagged calls (FastAPI over Flask, SQLAlchemy Core over ORM, Alembic from day 0). Names DR-029 close-out debt 2 (no migration framework) as substrate Alembic closes from day 0. Choices considered and rejected (Postgres, keep Flask, pure ORM, alternative test framework).

No build-sequence DR — Route A is a session-level routing call, captured in `current_state.md` and this session record. Not architectural enough for a DR.

`decisions.md` total: 1076 lines (was 946, +130).

### 4. Working-style adherence

Memory edit #16 stance applied throughout. Operator's explicit role declaration mid-session ("you are the Software and Data Architect Specialist") tightened the engagement model — Claude proposed software-side answers without punting back to operator on technical detail; operator's role narrowed to operating-side strategic input and routing decisions. Pattern held cleanly through Q1 (no operator input needed), Q2 (operator strategic call), Q3 (sub-questions 3a/3b no operator input needed; 3c two strategic questions explicitly framed).

Memory edit #17 (narrow line wrap, ~60–70 chars per line in fenced review blocks) held throughout. Every fenced block (proposed table, layout sketch, import-graph rules, stack table) fit chat width without horizontal scrolling.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021, DR-019 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered at open (tight, ~14 minute gap from Session 78 close).
- **Cat 1 (V3 build picture conditional render)** — rendered at open since stream state moved at Session 78 close. To be updated at this close — re-cut writes new workstream model, both DR-029 close-out streams drop, H1 closes (`done`, carries one session).
- **Cat 1 (open-items delta)** — rendered at open (substantial movement Session 78). To be evaluated at close — see below.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Every round led with the call or recommendation; reasoning followed.
- **Cat 1 (decision-maker framing)** — held cleanly. Operator's explicit role declaration mid-session reinforced this — strategic-input framing was sharper for Q2 (operator call) than Q1 / Q3 sub-3a / Q3 sub-3b (Claude calls).
- **Cat 1 (don't drift to alternatives when operator clear)** — held.
- **Cat 1 (unwind shorthand)** — held throughout. DRs cited with bracketed reminders. Technical terms (repo, FastAPI, SQLAlchemy Core, ORM, Alembic, Vite, `import-linter`, lint rule) unwound in plain language on use. Specific instance: "repo" unwound at first appearance ("Repo = repository = the folder/codebase where all v3's code lives, version-controlled with git") after operator surfaced unfamiliarity.
- **Cat 1 (escalate to detail only when warranted)** — held. Q3 sub-3c (tech stack) escalated with explicit "this is where I'd want a small piece of strategic input" framing.
- **Cat 1 (line-break rendering for review content)** — held throughout per memory edit #17.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. No mid-session re-anchor needed; single sitting under 90 minutes.
- **Cat 2 (pre-flight directory listing)** — done at open. To be re-run at close as part of post-close verification.
- **Cat 2 (Desktop Commander default)** — held. All file ops via `Desktop Commander:write_file` (rewrite mode for re-cut; append mode for DR additions), `read_file`, plus `start_process` for timestamp anchors and one `wc -l` verification call. **One drift moment surfaced and self-corrected:** initial `wc -l` was attempted via `bash_tool`, which failed (per Cat 3 — `bash_tool` is non-functional in this environment). Self-corrected immediately to `Desktop Commander:start_process`. No operational impact.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python REPL work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; both DRs drafted directly into `decisions.md` at close. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — flagged: H2 status row in `v3_build_picture.md` was written at re-cut time as "parked until operator routes". Operator subsequently confirmed Route A which sequences H2 before W1. The row text was not updated mid-session; updated at close. This is minor textual drift, not structural — the workstream model itself is unchanged. Surfaced here per the Cat 2 instruction.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — n/a; this session was scoping and DR drafting, not data work.
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — n/a; all writes were single-target (one full rewrite of `v3_build_picture.md`; one append to `decisions.md`).
- **Cat 3 (`bash_tool` non-functional)** — surfaced and self-corrected once mid-session. See Cat 2 above.
- **Cat 3 (write-file vs create_file namespace gotcha)** — held. All writes via `Desktop Commander:write_file`. Verified post-write.
- **Cat 4 (DR-027/028 invoked)** — named at open. DR-028 explicitly load-bearing in DR-030 — the `clients/` folder boundary is DR-028 made structural at the folder level. Cited by number with bracketed reminder.
- **Cat 4 (operational/analytical line discipline)** — engaged in DR-030 (the operational/analytical line cuts orthogonally to MVC, named in the rejected-MVC reasoning).
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a this session.
- **Cat 5 (software questions are Claude's)** — held cleanly throughout, sharpened by operator's mid-session role declaration. Q1 (repo layout), Q3 sub-3a (top-level layout), Q3 sub-3b (import-graph rules) — pure Claude calls. Q3 sub-3c (tech stack) — Claude call with two strategic questions framed for operator. Q2 (build sequence) — strategic call framed for operator with Claude's architectural read.
- **Cat 5 (operator working-style — memory edit #16)** — held throughout, sharpened by mid-session role declaration.

## Open items in (carried forward)

New from Session 79:

- **DR-030 + DR-031 effective post-upload** — operator-side action: re-upload `decisions.md` to the bethub-rebuild Claude Project knowledge base for fresh chats to see the new DRs. Until re-upload, fresh chats won't see DR-030 or DR-031. Same shape as Session 78's `governance.md` re-upload requirement.

Carry-forward (largely the same shape as Session 78):

- **Three pieces of named debt** — no test coverage, no migration framework, monolithic orchestrator file. Two have substrate-shifts this session: (a) test coverage debt now has `import-linter` per DR-030 as the first regression-protected surface; (b) migration framework debt has Alembic per DR-031 as substrate landing from day 0. Both still carry forward as `governance.md` close-out paragraph §4 named debt with their original return-triggers — the substrate shifts don't close the debt items, they just give v3 a head start on closing them.
- **Five deferred capabilities** — operational soft-book layer (§2.5), §2.10 bucket-2 re-evaluation, Fix 4 cadence design, Fix 5 venue harmonisation, periodic data-layer fitness re-verification. Now formally named in `governance.md` close-out paragraph §5.
- **Post-DR-029-close contract documentation relocation** — both files move from `dr029/2_7_api_contract_versioning/` to v3's `contracts/` folder per DR-030 layout. Carry forward as v3 build proper administrative cleanup.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records.
- **Sports-side dead-heat capture in `architecture.md` §B.1.4** — administrative cleanup carry-forward.
- **Past-settlement-window threshold calibration** — v3 day-one ships with 30 minutes from race finish.
- **Settlement worker periodic verification cadence** — v3 build proper operational tuning.
- **Cluster 1 surgical-fix carry-in (analytical-layer prep)** — non-gating analytical-layer prep work.
- **Complete cascade map** — parked. Best done post-DR-029.
- **CLV as analytical-layer signal** — built post-DR-029.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — operational design downstream.
- **`marketTime` mutability empirical question** — folded into Fix 4 cadence brief drafting per §2.9 §3.5.
- **§2.9 §4.4 six edge cases** — documented for burst-review reference.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — Fix 8 report §8.5 recommendation.
- **Session numbering slip in probe brief** — cosmetic.
- **EX_LADDER entitlement question** — operator-side homework.
- **Drift-check methodology gap** — substrate from Session 64 carry-forward.
- **`bethub-analytical` project awaiting activation** — operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** — parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — non-gating.
- **BetWatch contacted re: API service and book coverage** — awaiting response (no longer gating).
- **Betfair API membership tiers — investigate.** Operator-side homework.
- **PASSIVE bet-delay model handling** — flagged in §2.4 §15.4 as v3.1+ capability.
- **Betfair contact re: `EX_LADDER` entitlement and pricing** — operator-side parallel action.
- **Betfair contact re: `EX_TRADED_VOLUME` projection cost and entitlement** — operator-side parallel action.
- **Cluster C capture-routing decision** — deferred.
- **Racing API value assessment** — post-DR-029 strategic decision.
- **v3 build-proper UI candidates** — three surfaces logged §5.2 of §2.10 brief.
- **Betfair SP-projection accuracy study** — post-DR-029 analytical capability candidate.
- **Racing EV model recalibration with §2.10 bucket-1 captures** — post-DR-029 analytical work.
- **WIP §16** — VPS in-flight work. Unchanged.

Gaps from earlier reviews (logged for awareness):
- **Claude-67 G1** — AU-specific session expiry not on disk.
- **Claude-67 G2** — `listCurrencyRates` API surface silent in captured reference.
- **Claude-67 G3** — Racing API ↔ Betfair market identity reconciliation implicit.
- **Claude-67 G4** — `listCurrentOrders` filter parameter list not in captured reference.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC` betDelay confidence note. Partly addressed Session 76.

## Open items out (closed this session)

- **`v3_build_picture.md` re-cut from DR-029 scope to v3 build workstreams** — re-written this session as a full rewrite. New cut is by build workstream across three bands (H/W/P).
- **Both DR-029 close-out streams from Session 78** (Contract documentation files; DR-029 close-out governance paragraph) — dropped per one-session carry rule. Removed from the workstream cut.
- **Pre-build scoping pass — three architectural questions** — settled this session: repo layout (single repo), build sequence (Route A), module boundaries (8 folders + import-graph rules + tech stack).
- **DR-030 — V3 repo layout and module-boundary discipline** — locked this session. Lines 951–1031 of `decisions.md`.
- **DR-031 — V3 tech stack** — locked this session. Lines 1032–1076 of `decisions.md`.

## Session close state

- **Rebuild folder root:** 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present. **Two files modified this session:** `v3_build_picture.md` (full rewrite, 95 lines, was 85), `decisions.md` (DR-030 + DR-031 appended; 1076 lines, was 946).
- **`current_state.md`:** to be updated by close ritual to reflect Session 80 forward routing (H2 — Fix 4 + Fix 5 brief drafting). New required reads to add: DR-030 + DR-031 reference for any future session that needs to re-anchor on the v3 architectural shape.
- **`v3_build_picture.md`:** **modified this session — full rewrite.** New cut by build workstream. To be touched at close for two reasons: (a) update H1 status to `done` (carries one session), and (b) update H2 row text to reflect Route A sequencing ("next-up after Session 79 close" or equivalent). "Last updated" timestamp updates to close timestamp.
- **`standing_instructions.md`:** unchanged this session.
- **`governance.md`:** unchanged this session. **Operator-side action complete:** operator confirmed re-upload of `governance.md` to bethub-rebuild Claude Project knowledge base mid-session.
- **`decisions.md`:** **modified this session.** DR-030 (lines 951–1031) and DR-031 (lines 1032–1076) appended. Total 1076 lines, +130 from Session 78. **Operator-side action: `decisions.md` needs re-uploading to bethub-rebuild Claude Project knowledge base.**
- **`architecture.md`:** unchanged this session. Sports-side dead-heat capture amendment to §B.1.4 carry-forward from Session 74 still pending.
- **`dr029/`:** unchanged this session.
- **`sessions/`:** Session 79 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 79 opening prompt to be removed at close; Session 80 opening prompt to be written.
- **Project knowledge base:** **operator-side action required** — re-upload `decisions.md` to bring DR-030 + DR-031 into the Project knowledge base. `governance.md` re-upload completed mid-session.
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 80 picks up **H2 — Fix 4 + Fix 5 brief drafting**, per Route A sequencing locked Round 9 of this session.

**Session 80 shape:**

1. **First work:** read `current_state.md` plus `standing_instructions.md` in full plus `project_context.md` plus `sessions/SESSION_79.md` (this file) plus `decisions.md` DR-030 + DR-031 entries (lines 951–1076).
2. **H2 brief drafting.** Fix 4 (cadence brief) draws on Saturday 2026-05-02 API observation probe substrate plus the `betfair_client_contract.md` v1.0 §2.4 Streaming spec (cadence parameters explicitly deferred from contract to Fix 4). Fix 5 (venue harmonisation) is independent of the probe; can land in same session or split.
3. **Forward routing for Session 81 onward:** v3 build proper W1 (data layer — `vps_client` v1.0 implementation Code-bound brief).

**Alternative routing if Session 80 surfaces that Fix 4 + Fix 5 is too much for one session:** split. Fix 4 first (probe substrate is fresh), Fix 5 second.

**Out of scope for Session 80:** v3 build proper W1 itself (deferred to Session 81+); any reshape of the workstream cut from Session 79 unless operator surfaces redline edits in advance.

**Operator-side actions between sessions:**

1. **(Required for Session 80 productivity)** Re-upload `decisions.md` to the bethub-rebuild Claude Project knowledge base. DR-030 + DR-031 are load-bearing for v3 build proper context; without re-upload, fresh chats won't see them.
2. **(Optional, low priority)** Investigate Betfair API membership tiers — informs §5.4 full-ladder credential upgrade decision + §5.5 EX_LADDER contact action. Carry-forward; non-gating.
3. **(Optional)** Awaiting BetWatch response — no longer gating per Session 69 §2.5 deferral.
4. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.
5. **(Optional)** Contact Betfair re: `EX_LADDER` entitlement and pricing.
6. **(Optional)** Contact Betfair re: `EX_TRADED_VOLUME` projection cost and entitlement.
7. **(Optional)** Review §§2.6, 2.7, 2.8, 2.9, 2.10 briefs end-to-end at leisure.

## Close-out notes

Single sitting, ~1 hr 02 min wall-clock. Three working-style moments worth holding onto:

- **Mid-session operator-Claude role declaration.** Operator declared technical-side leadership delegation explicitly mid-session: "you are the Software and Data Architect Specialist. I'm only making strategic decisions related to operations and execution". Pattern: when the work is architectural and the operator doesn't have the technical foundation to second-guess proposals, explicit role declaration sharpens the engagement model. Claude's framing of strategic-input questions tightens (Q2 build sequence framed sharply on operating side; Q3 sub-3c tech stack framed two questions explicitly with strategic-side hooks). Worth carrying forward as a pattern: if Claude is leading on a stretch of architectural work, the framing of "strategic input I'd want from you" calls is more important than usual to keep operator-side calls visible without drowning operator in software-side detail.

- **DR drafting at close vs section-by-section.** Operator chose at-close drafting ("Close it up... Write the DRs"). The choice was correct — the substantive content was fully locked in chat across rounds 8–12 (eight architectural confirmations across three questions). The writing was mechanical: assembling locked content into the DR template format, naming upstream DRs (DR-027 / DR-028 for DR-030; DR-029 close-out debt for DR-030 + DR-031 substrate). At-close DR drafting is a valid pattern when (a) substance is fully locked in the substantive-work portion of the session, (b) the writing is template-following rather than synthesis, and (c) close-out has budget for it. Fails as a pattern if any of those three fail — substance not fully locked produces last-minute redirects, synthesis-shaped writing requires operator review per section, and tight close-out budget produces partial writes.

- **Mid-session `bash_tool` self-correction.** Initial `wc -l` attempt routed via `bash_tool` (which is non-functional in this environment per Cat 3) failed with "no such file." Self-corrected immediately to `Desktop Commander:start_process`. Pattern reinforces the standing-instruction discipline — `bash_tool` failures are diagnostic, not a problem to debug. Switch tools and continue.

DR-030 + DR-031 are now load-bearing for v3 build proper. Session 80 carries them forward as required reading.
