# Session 78

**Title:** DR-029 closed. Code report triage on the contract documentation files completed cleanly — five Session 77 Code findings triaged, four closed without action, one operator-readable §2 clarifier added to `betfair_client_contract.md` (Streaming surface now names the two-stream nature explicitly). Both contract documentation files locked v1.0 complete. Then drafted the DR-029 close-out governance paragraph end-to-end and wrote it to `governance.md` as the formalised "Final data-layer lock review (DR-029 close-out)" section — six sub-sections covering gate-clearance call, what DR-029 set out to do, what was actually delivered across §§2.1–2.10, the three pieces of named debt being carried forward (no test coverage, no migration framework, monolithic orchestrator file) with named return-triggers each, five deferred capabilities (operational soft-book layer, §2.10 bucket-2 re-evaluation, Fix 4 cadence design, Fix 5 venue harmonisation, periodic data-layer fitness re-verification with 12-month / two-version-bumps-in-180-days / first-irreducible-v3-side-gap triggers), and a closing paragraph signing the artefact off. v3 build proper is now unblocked. Session 79 picks up `v3_build_picture.md` re-cut from DR-029 streams to v3 build workstreams.
**Opened:** 2026-05-04 15:31 ACST
**Closed:** 2026-05-04 16:01 ACST
**Wall-clock:** ~30 min substantive single sitting. Same-workday open relative to Session 77's 15:05 ACST close (~26 minute gap). Same-workday close.
**Tool routing:** Claude Chat. No Code routing required this session — all triage and close-out drafting in-Chat. Operator ran Claude Code between Session 77 and Session 78 against `contracts_spec_brief.md` to produce the report and the developer-readable spec sections.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — **closed this session**), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring), DR-019 (derived state on read — referenced in close-out paragraph as load-bearing for §2.6 settlement-state derivation).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 15:31 ACST`.
Close: same command → `2026-05-04 16:01 ACST`.

Same-workday open relative to Session 77's 15:05 ACST close. ~26 minute gap. Single sitting, immediate continuation. ~30 min wall-clock — short session, well under split-trigger thresholds.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_78_opening_prompt.md` only (Session 77 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 15:05 ACST` matched Session 77 close; `sessions/SESSION_77.md` present (278 lines); `v3_build_picture.md` last-updated `2026-05-04 15:05 ACST` matched Session 77's stream-state updates (contract documentation files stream advanced to "Code session pending between sessions").
- Same-workday recap delivered (tight: Session 77 drafted both contract files' operator-readable summaries plus the Code-bound brief; Session 78 picks up Code report triage).
- V3 build picture: rendered at open since stream state moved at Session 77 close.
- Open-items delta: skipped silently (no movement in 26 min since Session 77 close).

## Session shape

Session 78 was a **two-deliverable session** — Code report triage closing out the contract documentation files arc, then drafting the DR-029 close-out governance paragraph end-to-end. The session's tempo accelerated mid-session — operator opted for "let's keep going" continuation after the contract triage closed cleanly, then "your recommendations" delegation pattern across the close-out paragraph drafting. Six section-by-section confirmations across the close-out paragraph, with operator confirming each before write-to-disk; no redirects requested.

Two structural decisions confirmed at session-mid:

**1. Triage call: clean-lock with one Finding 4 edit.** Code surfaced five findings, all framed as minor / non-blocking. Operator-Claude triage confirmed: F1 (path mismatches in brief §3) cosmetic; F2 (edit-locked §6 vs version history append) Code resolved correctly per natural reading of §2.7 §4.4; F3 (`endpoint_retired` value not in v1.0 enums) correctly absent at v1.0; F4 (order subscription not separately named in operator-readable §2) genuinely improving — one-line clarifier added; F5 (concrete dispatch primitive left as Code's-call) explicitly named as Code's-call by §2.4 §7.9. Both contract documentation files locked v1.0 complete after the F4 edit and version history rows appended.

**2. Close-out paragraph location: append to `governance.md`, not standalone file.** Operator-confirmed at proposal time. Reasoning: `governance.md` line 209 already named "Final data-layer lock review" as a future review pattern "discussed but not yet formalised"; this paragraph is its formalisation. Standalone file would have created one more root file; the close-out hygiene discipline pushes against accumulation.

Round-by-round shape:

**Round 1 (open + Code report receipt).** Session 78 opened via skill. Operator pasted Code's session-complete summary; report received at `dr029/2_7_api_contract_versioning/contracts_spec_report.md`.

**Rounds 2–5 (report read + cross-check).** Read `contracts_spec_report.md` end-to-end (295 lines), then `vps_client_contract.md` (714 lines) end-to-end, then `betfair_client_contract.md` (1172 lines) in three chunks. Substantive coverage verified: every typed shape traces back to a named anchor; envelope shape consistent across files; versioning mechanics parallel; out-of-scope discipline parallel.

**Round 6 (triage proposal + operator confirmation).** Triage call surfaced: clean-lock with Finding 4 edit. Operator confirmed.

**Rounds 7–9 (file edits).** Three `edit_block` calls: F4 clarifier on `betfair_client_contract.md` operator-readable §2 Streaming bullet; Session 78 row appended to `betfair_client_contract.md` §6 version history; Session 78 row appended to `vps_client_contract.md` §6 version history. Both contract documentation files locked v1.0 complete.

**Round 10 (close-out paragraph proposal).** Triage closed; operator opted to keep going. Proposed six-section shape for the close-out governance paragraph, confirmed location as `governance.md` (replacing the "Future review patterns" bullet).

**Rounds 11–17 (section-by-section drafting).** Each section surfaced as draft for review, operator confirmed, written to disk:
- §1 Gate-clearance call (Round 11)
- §2 What DR-029 set out to do (Round 12)
- §3 What was actually delivered (Round 13)
- §4 The three pieces of named debt being carried forward (Round 14)
- §5 What's deferred — and what triggers each returning to scope (Round 15) — collapsed planned §5 and §6 since the periodic re-verification framing fit naturally as deferred capability 5
- §6 Closing (Round 16) — added as a short ribbon-tying paragraph on the recommendation that the artefact needed a structural close mirroring §1's opening

**Round 17 (next-steps brief + close).** Operator requested a brief next-steps trajectory through v3 build proper completion. Delivered as ten-workstream sequence covering pre-build housekeeping (1–2 sessions), v3 build proper (eight workstreams from data layer through cutover), and post-build pre-analytical (bucket-1 §2.10 captures, analytical layer scoping). Close-out follows.

## What was delivered

### 1. Session 77 Code report triage and v1.0 contract documentation files lock

Triaged Code's `contracts_spec_report.md` (295 lines, Code session producing the developer-readable specs in both contract files plus the report). Five findings disposition:

- **F1 (pre-read path mismatches):** trivial cosmetic — brief author's working folder titles drifted from disk-locked folder names. Closed without file edit.
- **F2 (edit-locked §6 vs version history table append-row):** Code resolved correctly per natural reading of §2.7 §4.4 (table is append-only governance log; appending a row is the table's intended growth path, not a §6 edit). Closed without file edit.
- **F3 (`endpoint_retired` reason value not in v1.0 enumeration):** correctly absent at v1.0 because v1.0 ships without any v1-retired surfaces. The future-addition note in §10.5 / §14.6 carries the discipline. Closed without file edit.
- **F4 (order subscription not separately named in operator-readable §2):** genuinely improving — one-line clarifier added to `betfair_client_contract.md` operator-readable §2 Streaming bullet, naming the two-stream nature (market data plus order-state) explicitly so a reader of §2 alone learns the order subscription is part of the Streaming surface rather than a separate write-side surface. Closed with file edit.
- **F5 (concrete dispatch primitive left as Code's-call):** explicitly named as Code's-call by §2.4 §7.9. Closed without file edit.

Two version history rows appended (one row per file) recording Session 78 triage outcome. Both contract documentation files now locked v1.0 complete:
- `vps_client_contract.md` — 716 lines (was 714; +2 from version row only).
- `betfair_client_contract.md` — 1174 lines (was 1172; +2 from F4 clarifier in operator-readable §2 plus version row).

Code's three drift-risk flags from report §8.3 — dispatch primitive reflection-back, `endpoint_retired` belt-and-braces option, identifier-resolution shape distinctness — all visibility-only flags carried forward as v3 build proper concerns rather than v1.0 contract content.

### 2. DR-029 close-out governance paragraph drafted end-to-end

Written to `governance.md` at lines 218–612 as the new top-level section "Final data-layer lock review (DR-029 close-out)". Six sub-sections, ~380 lines total:

- **§1 Gate-clearance call** — anchored at 2026-05-04 ACST, names DR-029 closed, both contracts locked at v1.0, gate cleared, v3 build proper unblocked. Notes the arc ran Sessions 11–78 with active execution from Session 27.
- **§2 What DR-029 set out to do** — recaps the gate's intent: the two named risks from Session 11's lock decision (discipline rot at build time, building against a moving contract), the versioned-contract framing (not feature-complete schema), and the three architectural anchors (DR-027 two-database split, DR-028 cross-DB integration boundary, operational/analytical line discipline).
- **§3 What was actually delivered** — pointer-only summary of all ten in-scope items §§2.1–2.10 with their close sessions, plus the framing closing paragraph naming the contract documentation files as the load-bearing artefacts of gate clearance.
- **§4 The three pieces of named debt being carried forward** — the load-bearing section. Each piece (no test coverage, no migration framework, monolithic orchestrator file) gets a what / why-not-blocking / return-trigger structure. Closing paragraph: "These are not regrets. They are the deliberate choice the gate-clearance call made: clear the gate now, carry the debt forward visibly, return to each piece on a defined trigger rather than letting any of them silently expand."
- **§5 What's deferred — and what triggers each returning to scope** — five deferred capabilities (operational soft-book layer with Strategy 2/3/4 trigger conditions, §2.10 bucket-2 re-evaluation, Fix 4 cadence design, Fix 5 venue harmonisation, periodic data-layer fitness re-verification). Each gets explicit observable triggers. Periodic re-verification trigger conditions: 12 months elapsed (calendar trigger — earliest 2027-05-04 ACST), two or more contract-surface version bumps in 180-day window, or first irreducible v3-side gap.
- **§6 Closing** — short structural close, points at `v3_build_picture.md` re-cutting from DR-029 streams to v3 build workstreams at next session that opens v3-build-proper work, frames the named debt and deferred capability as material the operator and Claude carry into v3 build with eyes open.

The "Future review patterns" section bullet for "Final data-layer lock review" was removed in the same edit — the bullet was the placeholder the section formalises.

### 3. Next-steps trajectory through v3 build proper completion

Delivered as a ten-workstream sequence:

- **Pre-build housekeeping (1–2 sessions):** Session 79 re-cuts `v3_build_picture.md`; Session 80 (optional) drafts Fix 4 + Fix 5 briefs.
- **V3 build proper:** eight workstreams covering data layer (`vps_client` v1.0 implementation), operational core (`betfair_client` v1.0 read surfaces + Streaming connection), live pricing (Streaming cache through to UI), bet entry and write surfaces, settlement worker, operational store + session ops, Burst Review workflow, cutover to v3.
- **Post-build pre-analytical:** bucket-1 §2.10 captures as backward-compatible additions, analytical layer scoping as fresh DR.

No committed session count for v3 build proper. Cutover marks "v3 complete" for the rebuild's purposes; analytical layer is the next arc, not part of v3 build proper.

### 4. Working-style adherence

Memory edit #16 stance applied throughout. Operator engaged "your recommendations" delegation pattern across the close-out paragraph drafting, similar to Session 77's pattern when substrate is fully locked. Section-by-section drafting cadence held — operator confirmed each section before write-to-disk; no redirects.

Memory edit #17 (narrow line wrap, ~60–70 chars per line in fenced review blocks) held throughout. Every fenced draft block fit chat width without horizontal scrolling.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (tight, ~26 minute gap from Session 77 close).
- **Cat 1 (V3 build picture conditional render)** — rendered at open since stream state moved at Session 77 close. To be updated at this close — contract documentation files stream closes (`done`), no other stream movements.
- **Cat 1 (open-items delta)** — skipped silently at open (no movement in 26 min). Will fire at next session open since substantial movement this session.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout.
- **Cat 1 (decision-maker framing)** — held. Each round led with the call or recommendation; routing-question framing at triage and at close-out paragraph drafting was explicit operator-Claude division of work.
- **Cat 1 (don't drift to alternatives when operator clear)** — held.
- **Cat 1 (unwind shorthand)** — held throughout. DRs cited with bracketed reminders. `vps_client`, `betfair_client`, `capture.db`, `betfair_market_id`, `betfair_selection_id`, `EX_LADDER`, `actualSP`, `customerRef`, `EnvelopeStatus` etc. unwound on use.
- **Cat 1 (escalate to detail only when warranted)** — held.
- **Cat 1 (line-break rendering for review content)** — held throughout per memory edit #17.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. No mid-session re-anchor needed; single sitting under 90 minutes.
- **Cat 2 (pre-flight directory listing)** — done at open. Will run at close.
- **Cat 2 (Desktop Commander default)** — held. All file ops via `Desktop Commander:read_file`, `edit_block`, `write_file`, plus one `start_process` for the timestamp anchors.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python REPL work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; all close-out paragraph sections written directly to `governance.md` during the session. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — flagged: §6 of the close-out paragraph was added beyond the original six-section plan. The drift wasn't structural — original §5 + §6 collapsed into one (periodic re-verification fit naturally as deferred capability 5), and a new §6 closing paragraph was added on recommendation. Resulting structure is still six sections; mid-session structural decision was operator-confirmed before write.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default. Operator requested next-steps brief which serves as the substantive closing context.
- **Cat 3 (external API resources reach-for)** — n/a; this session was triage and governance drafting, not data work.
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — n/a; all writes were single-target `edit_block` calls (one specific old_string → one specific new_string per call).
- **Cat 3 (write-file vs create_file namespace gotcha)** — held. All writes via `Desktop Commander:write_file` or `edit_block` directly.
- **Cat 4 (DR-027/028 invoked)** — named at open. Both load-bearing throughout the close-out paragraph (DR-027 anchoring the two-database split framing in §2; DR-028 anchoring the one-file boundary discipline in both contracts and reaffirmed in §2).
- **Cat 4 (operational/analytical line discipline)** — engaged throughout. Close-out paragraph §2 names the line discipline as the third architectural axis.
- **Cat 4 (Betfair-as-canonical-source extension)** — referenced in close-out paragraph §5 deferred capability 1 (carries forward independently per Session 42 architectural extension flag).
- **Cat 5 (software questions are Claude's)** — held cleanly. Triage call shape, close-out paragraph six-section structure, return-trigger specificity, deferral framing — all Claude's calls (proposed for confirmation). Operator's strategic decisions (clean-lock vs other triage shapes, append-to-governance.md vs standalone file, "your recommendations" delegation across drafting) were routing and execution choices Claude proposed but operator confirmed.
- **Cat 5 (operator working-style — memory edit #16)** — held throughout.

## Open items in (carried forward)

New from Session 78:

None. Session 78 was a closing session — its work was triaging open items inward (the contract documentation files locking) and naming the carry-forward shape for v3 build proper (the close-out paragraph). No fresh open items surfaced.

Carry-forward (largely the same shape as Session 77 plus the gate-clearance):

- **Three pieces of named debt** — no test coverage, no migration framework, monolithic orchestrator file. Now formally named in `governance.md` close-out paragraph §4 with explicit return-triggers. Carry forward as governance state, not as session-level open items.
- **Five deferred capabilities** — operational soft-book layer (§2.5), §2.10 bucket-2 re-evaluation, Fix 4 cadence design, Fix 5 venue harmonisation, periodic data-layer fitness re-verification. Now formally named in `governance.md` close-out paragraph §5 with explicit return-triggers.
- **Post-DR-029-close contract documentation relocation** — both files move from `dr029/2_7_api_contract_versioning/` to permanent v3 location (likely `contracts/` folder at v3 project root). Carry forward as v3 build proper administrative cleanup.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records. Continues as administrative cleanup post-DR-029.
- **Sports-side dead-heat capture in `architecture.md` §B.1.4** — administrative cleanup carry-forward (Session 74).
- **Past-settlement-window threshold calibration** — v3 day-one ships with 30 minutes from race finish; calibrate from operational experience.
- **Settlement worker periodic verification cadence** — v3 build proper operational tuning.
- **Cluster 1 surgical-fix carry-in (analytical-layer prep)** — non-gating analytical-layer prep work.
- **Complete cascade map** — parked. Best done post-DR-029.
- **CLV as analytical-layer signal** — built post-DR-029.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — operational design downstream.
- **`marketTime` mutability empirical question** — folded into Fix 4 cadence brief drafting per §2.9 §3.5.
- **§2.9 §4.4 six edge cases** — documented for burst-review reference, no mitigation built.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — Fix 8 report §8.5 recommendation.
- **Session numbering slip in probe brief** — cosmetic.
- **EX_LADDER entitlement question** — operator-side homework.
- **Drift-check methodology gap** — substrate from Session 64 carry-forward.
- **`bethub-analytical` project awaiting activation** — operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** — parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — non-gating.
- **BetWatch contacted re: API service and book coverage** — awaiting response.
- **Betfair API membership tiers — investigate.** Operator-side homework.
- **PASSIVE bet-delay model handling** — flagged in §2.4 §15.4 as v3.1+ capability.
- **Betfair contact re: `EX_LADDER` entitlement and pricing** — operator-side parallel action.
- **Betfair contact re: `EX_TRADED_VOLUME` projection cost and entitlement** — operator-side parallel action.
- **Cluster C capture-routing decision** — deferred.
- **Racing API value assessment** — post-DR-029 strategic decision.
- **Future operational soft-book DR (post-DR-029)** — bundled-bookmaker breadth substrate. Now formally captured in close-out paragraph §5 deferred capability 1 with explicit Strategy 2/3/4 triggers.
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

- **`vps_client_contract.md` v1.0 lock** — operator-readable summary §§1–6 (Session 77) plus developer-readable §§7–11 (Session 77 Code) plus Session 78 triage row appended. v1.0 locked complete.
- **`betfair_client_contract.md` v1.0 lock** — operator-readable summary §§1–6 (Session 77) plus developer-readable §§7–15 (Session 77 Code) plus Session 78 F4 clarifier on operator-readable §2 plus Session 78 triage row appended. v1.0 locked complete.
- **`contracts_spec_brief.md` Code session** — Code session executed cleanly between Sessions 77 and 78; report locked at `contracts_spec_report.md`. Closed.
- **`contracts_spec_report.md` triage** — five findings triaged (1 closed with edit, 4 closed without action). Closed.
- **DR-029 close-out governance paragraph** — drafted end-to-end, written to `governance.md` as new top-level section. Closed.
- **§2.10 carry-rule** — expired this close (was carrying one session post-Session 76 close, now drops).
- **§2.7 carry-rule** — expired Session 76 close, no carry remaining.
- **DR-029 itself** — **CLOSED THIS SESSION.** All ten in-scope items §§2.1–2.10 closed across Sessions 34–78. Both integration-module contracts locked at v1.0. Close-out governance paragraph formalised in `governance.md`. v3 build proper unblocked.

## Session close state

- **Rebuild folder root:** 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present. **Three files modified this session:** `dr029/2_7_api_contract_versioning/vps_client_contract.md`, `dr029/2_7_api_contract_versioning/betfair_client_contract.md`, `governance.md`.
- **`current_state.md`:** to be updated by close ritual to reflect Session 79 forward routing (`v3_build_picture.md` re-cut from DR-029 streams to v3 build workstreams).
- **`v3_build_picture.md`:** **to be updated this close.** Contract documentation files stream advances to `done` (carries one session post-close, then drops). **No other streams in flight** — DR-029 is closed, v3 build proper streams not yet cut. Next session's stream model re-cut is itself the primary deliverable.
- **`standing_instructions.md`:** unchanged this session.
- **`governance.md`:** **modified this session.** Close-out section (lines 218–612, six sub-sections, ~380 lines) added. "Future review patterns" bullet for "Final data-layer lock review" removed in the same edit. **Operator-side action: `governance.md` needs re-uploading to the bethub-rebuild Claude Project knowledge base.**
- **`dr029/2_7_api_contract_versioning/vps_client_contract.md`:** modified this session. 716 lines (was 714). Session 78 triage row appended to §6 version history.
- **`dr029/2_7_api_contract_versioning/betfair_client_contract.md`:** modified this session. 1174 lines (was 1172). F4 clarifier added to operator-readable §2 Streaming bullet; Session 78 triage row appended to §6 version history.
- **`dr029/2_7_api_contract_versioning/contracts_spec_brief.md`:** unchanged this session (Code's source of truth).
- **`dr029/2_7_api_contract_versioning/contracts_spec_report.md`:** Code session output, present at brief-named path. Read this session, not modified.
- **`architecture.md`:** unchanged this session. Sports-side dead-heat capture amendment to §B.1.4 carry-forward from Session 74 still pending; rolls into v3 build proper administrative cleanup.
- **`decisions.md`:** unchanged this session. No new DRs surfaced. DR-029 itself was locked Session 11; the close-out paragraph in `governance.md` records the gate-clearance, which is the procedural complement to the locked DR.
- **`sessions/`:** Session 78 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 78 opening prompt to be removed at close; Session 79 opening prompt to be written.
- **Project knowledge base:** **operator-side action required** — re-upload `governance.md` to bring the close-out section into the Project knowledge base.
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 79 picks up **`v3_build_picture.md` re-cut** from DR-029 streams to v3 build workstreams.

**Session 79 shape:**

1. **First work:** read `current_state.md` plus `governance.md` close-out section (§§1–6) plus the next-steps trajectory recorded in this session's record §3 below.
2. **Re-cut the stream model.** Replace the DR-029-stream cut in `v3_build_picture.md` with v3 build workstream cut. Reference the ten-workstream sequence in this session's "What was delivered" §3 as the substrate.
3. **Surface any pre-build scoping decisions.** Module boundaries, repo layout, build sequence — anything that needs settling before workstream 1 (data layer) opens.
4. **Forward routing for Session 80 onward:** v3 build proper workstream 1 (data layer — `vps_client` v1.0 implementation against the locked contract) OR Fix 4 / Fix 5 brief drafting if operator routes housekeeping first.

**Alternative routing if Session 79 surfaces pre-build scoping issues that need Code-side input:** Session 79 may pivot from build-picture re-cut to a scoping brief commissioning the pre-build investigation; Session 80 then absorbs the build-picture re-cut once scoping settles.

**Out of scope for Session 79:** v3 build proper workstream 1 itself (deferred to Session 80+); Fix 4 / Fix 5 brief drafting (housekeeping; operator decides whether before or alongside build).

**Operator-side actions between sessions:**

1. **(Required for Session 79 productivity)** Re-upload `governance.md` to the bethub-rebuild Claude Project knowledge base. The close-out section is load-bearing for v3 build proper context; without re-upload, fresh chats won't see the section.
2. **(Optional, low priority)** Investigate Betfair API membership tiers — informs §5.4 full-ladder credential upgrade decision + §5.5 EX_LADDER contact action. Carry-forward; non-gating.
3. **(Optional)** Awaiting BetWatch response — no longer gating per Session 69 §2.5 deferral.
4. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.
5. **(Optional)** Contact Betfair re: `EX_LADDER` entitlement and pricing.
6. **(Optional)** Contact Betfair re: `EX_TRADED_VOLUME` projection cost and entitlement.
7. **(Optional)** Review §§2.6, 2.7, 2.8, 2.9, 2.10 briefs end-to-end at leisure.

## Close-out notes

Single sitting, ~30 min wall-clock — short session, well-aligned with operator's preference for Chat efficiency on triage-and-close-out work when substrate is fully locked.

Three working-style moments worth holding onto:

- **Triage-and-extend continuation pattern.** Session opened expecting only Code report triage (anticipated single deliverable). Operator opted for "session's pretty young, let's keep going" continuation after triage closed cleanly, which extended the session into close-out paragraph drafting end-to-end. Pattern: when a session closes its primary deliverable early and substrate for the next deliverable is fully locked (DR-029's substrate was fully captured in `current_state.md` carry-forward + `dr029_scope.md` + `decisions.md` DR-029 entry), continuing into the next deliverable rather than splitting is operator's right call — the cognitive overhead of opening a fresh session for substrate-locked drafting is meaningful when the alternative is direct continuation.

- **Mid-section structural decision (§5/§6 collapse).** During §5 drafting, the planned §5 (deferred capabilities) and planned §6 (periodic re-verification) collapsed naturally — periodic re-verification fit as deferred capability 5. Surfaced to operator at the moment of recognition; operator confirmed via "happy with your recommendation" pattern. New §6 (closing paragraph) added as ribbon-tying rather than substantive sixth section. Resulting structure remained six numbered sections; the structural decision was operator-confirmed before write. Pattern: structural drift during artefact drafting is fine if surfaced and confirmed at the moment of recognition; absorbed silently is the failure mode.

- **DR-029 closure as governance event, not procedural event.** This session closed the longest active arc in the rebuild — DR-029 ran from Session 11 lock to Session 78 close-out across roughly six weeks of operator-Claude work. The closure is recorded in `governance.md` (the close-out paragraph) rather than as an amendment to DR-029 itself in `decisions.md`. Reasoning: DR-029 is the *decision* (locked Session 11); the close-out paragraph is the *gate clearance* (closed Session 78). DRs are immutable once locked per the project's governance discipline; gate clearances are formalised in `governance.md` per its "Final data-layer lock review" framing. The two artefact types are distinct.

DR-029 is closed. v3 build proper is the next arc.
