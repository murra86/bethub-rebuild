# Session 87

**Title:** W3 implementation report triaged clean (212 tests, mypy/ruff/lint-imports clean, four findings all classified scope-question/future-substrate, F5 contract revision locked at v1.1, foundation clean for W4 + W7 unblock); W4 brief drafting opened call-driven and surfaced four substrate decisions before pausing for hedge-staking math review (W4 scope = Betfair-side bet-entry orchestration with soft-book typed-price entry deferred to W4.1; module placement at `workflow/bet_entry/v1/` per DR-030 layered architecture; placement workflow takes hedge-target spec as input with directional drift handling auto-recomputing stake on favourable drift and surfacing two-route warning on unfavourable drift; cancel/replace primitive-only with combined `adjust_hedge` workflow shipping atomic-from-operator-perspective stake-and-price submission). W4 brief drafting paused; Session 88 ships hedge-staking math review artefact as standalone deliverable, then W4 brief drafting resumes with locked math as substrate.
**Opened:** 2026-05-05 17:54 ACST
**Closed:** 2026-05-05 18:47 ACST
**Wall-clock:** ~53 min. Single sitting, well under split-trigger threshold.
**Tool routing:** Claude Chat (W3 triage; W4 brief drafting partial; close-out). Claude Code (out-of-session, between Session 86 and Session 87 — executed the locked W3 brief and produced the implementation report at commit `2329604`).
**Governing DRs invoked:** DR-027 (two-database architecture), DR-028 (cross-DB integration boundary), DR-021 (Adelaide local time anchoring), DR-019 (derived state on read), DR-030 (v3 repo layout — load-bearing for W4 module placement at `workflow/bet_entry/v1/`), DR-031 (v3 tech stack), plus Session 42 architectural extension flag invoked mid-session (Betfair as canonical source extending to all bet records — formalisation deferred to before W4.1, not before W4).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-05 17:54 ACST`.
Close: same command → `2026-05-05 18:47 ACST`.

Same-workday open relative to Session 86's 17:11 ACST close (~43 min gap, single-sitting continuation for W3 triage).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, calibrated against Cat 1 silent-ritual instruction:

- Rebuild root: 12 expected `.md` files (11 + `v3_build_picture.md`), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_87_opening_prompt.md` only (Session 86 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-05 17:11 ACST` matched Session 86 close; `sessions/SESSION_86.md` present (225 lines); `v3_build_picture.md` last-updated `2026-05-05 17:11 ACST` matched Session 86 close.
- Same-workday recap delivered (tight: W3 brief locked + Code prompt issued Session 86; Code executed out-of-session; Session 87 triages).
- V3 build picture: rendered inline at open (artefact updated by Session 86 close; render condition fires).
- Open-items delta: skip-silent (no items closed/opened/overdue between Sessions 86 close and 87 open beyond Code's out-of-session work which is what 87 triaged).
- Governing DRs named at open: DR-027, DR-028, DR-021, DR-019, DR-030, DR-031.

## Session shape

Session 87 was a **two-arc session** — W3 triage in the first arc (call-driven per Cat 1; classify findings, verify §7 criteria, lock F5 at v1.1, confirm forward routing) followed by **W4 brief drafting opening** in the second arc (also call-driven per Cat 1; surfaced four substrate decisions before reaching the hedge-staking math piece, where the operator surfaced a v2 history of math errors and wanted dedicated math review before embedding the formulas).

Triage arc closed cleanly with all findings classified as scope-question/future-substrate (none blocking), §7 criteria all PASS, F5 contract revision locked at v1.1, and forward routing confirmed (W4 next, W7 after W4). W3 closed; foundation clean for W4 + W7 unblock.

W4 brief drafting arc opened call-driven and ran four substrate calls before reaching the math-review pause. The four calls captured genuinely meaningful design decisions — scope boundary, module placement, placement workflow shape (which evolved through three operator-driven refinements into directional-drift handling with stake-equalisation logic), and cancel/replace shape with combined `adjust_hedge` workflow. The pause was operator-driven: the hedge-staking math behind the directional-drift logic deserves dedicated review given v2's history of math errors.

Round-by-round shape:

**Round 1 (open via skill).** Standard same-workday open ritual. Session 86 close timestamp matched all three drift-check anchors. V3 build picture rendered (state moved at Session 86 close); open-items delta skipped silently.

**Round 2 (triage arc — F1 finding).** Surfaced two routes for the brief §5.1 vocabulary divergence (parser shipped W2's actual envelope contract `op="mcm"` with `is_image` rather than the brief's `market_image`/`market_delta` framing). Locked Route A — accept divergence as brief-side wording drift; future-brief carry-forward logged for streaming-envelope vocabulary.

**Round 3 (triage arc — F2/F3 silent routing).** F2 (`listMarketBook` synthesised `scheduled_start_time`) and F3 (identity-check via `listMarketCatalogue` runner-presence inspection) both classified as deployment-substrate carry-forwards against v3 build proper Betfair deployment work. No operator call needed; routed silently in summary.

**Round 4 (triage arc — F4 finding).** Surfaced two routes for the W0 F4 typed-stub carry-forward (originally "revisit if `betfairlightweight` ships stubs"; W3 didn't substantively exercise the library either, so the carry can't fire until deployment wires it). Locked Route A — re-park W0 F4 to v3 build proper deployment.

**Round 5 (triage arc — F5 contract lock-in).** Verified empirically. Status header reads "v1.1 — F5 strategy_tag added Session 87 W3 (backward-compatible per §14.4); v1.0 locked Session 75 ...". F5 contract revision locked at v1.1.

**Round 6 (triage arc — forward routing call).** Surfaced three routes (W4 next; W7 next; defer call). Locked Route A — W4 next, W7 after W4 (W7's UI shape depends partly on what W4's bet-entry surface looks like; W4 has next concrete unblocked dependencies for W5 + W6).

**Round 7 (W4 brief drafting opens — Call 1).** Surfaced three routes for W4 scope boundary (narrow library scope; wider with soft-book typed-price entry; narrow first then soft-book in W4.1). Locked Route C — Betfair-side orchestration only; soft-book typed-price entry deferred to W4.1 between W4 and W7.

**Round 8 (W4 — Call 2).** Surfaced two routes for module placement (new `workflow/bet_entry/v1/` package per DR-030 vs extending `clients/betfair_client/v1/`). Locked Route A — `workflow/bet_entry/v1/` per DR-030 layered architecture. Sets pattern for W7 (`workflow/burst_review/v1/`).

**Round 9 (W4 — Call 3, evolved across multiple sub-rounds).** Surfaced three routes for placement-time sanity check shape (advisory only; strict block; configurable per-check fail-closed default). Initial recommendation Route C — fail-closed-with-explicit-override. Operator clarified scope (Betfair-side bet placement, not soft-book UI surface), then surfaced two-way explicit choice on mismatch (hold line vs accept drift) which sharpened Route C to "Route C-sharpened" — structured `PriceDriftEnvelope` returned on mismatch with both retry routes available. Operator further refined to favourable-vs-unfavourable directional handling: favourable-drift auto-accepts with stake adjustment, unfavourable-drift surfaces warning with two-route choice. Two further questions surfaced (stake-adjustment definition and "favourable" definition) that the operator answered through hedge-math operational framing — Betfair use is almost entirely lay bets matching against soft-book bets, so stake adjusts to equalise cycle outcomes, "favourable" means strictly better directional move (lay-down or back-up). This surfaced the Session 42 architectural extension flag (Betfair as canonical source extends to all bet records including soft-book hedges) — initially recommended Route B (pre-W4 architectural session) but operator clarification on the operational order (soft-book bet placed first; tool input is interim state until logged; modal opens with already-locked soft-book parameters) reshaped the call: workflow takes hedge-target spec as input rather than referencing persisted soft-book record, so cycle-linkage formalisation defers to before W4.1 (when soft-book entry actually establishes the linkage at logging time), not before W4. Locked Route A — proceed with W4 drafting using hedge-target spec as input shape.

**Round 10 (W4 — Call 4).** Surfaced two routes for cancellation/replacement workflow shape (symmetric with placement vs primitive-only). Locked Route B — primitive only; cycle-management logic layered above. Operator added two refinements: warning configurability (per-call override + operator config), symmetric directional logic across lay (against soft-book back) and back (against soft-book lay). Then surfaced atomic stake-and-price submission requirement (Betfair API limitation forces sequential cancel-then-place; ideally tool sends as one operator action). Surfaced three routes for combined workflow (single-confirm atomic-from-operator-perspective; explicit two-step with synchronous chaining; separate primitives only). Locked Route A — ship `adjust_hedge` workflow function as part of W4 (operator perceives one action; library executes cancel+place sequentially with named failure modes for partial completion).

**Round 11 (W4 pause — math review routing).** Operator surfaced v2 history of math errors and wanted hedge-staking math review before formulas embedded in tool. Surfaced two routes (math review in this session; math review as standalone pre-W4 deliverable). Locked Route B — math review as standalone artefact next session at `dr029/w4_bet_entry/hedge_staking_math.md`. Operator confirmed `adjust_hedge` execution shape (Betfair API two-call sequence rendered as single operator action; named failure modes; ~50–200ms uncovered window acknowledged).

**Round 12 (close).** Operator confirmed close-out. Session-close ritual fires.

## What was delivered

This session produced two substantive outputs (one closed deliverable, one opened-then-paused) plus standard close-out artefacts.

### W3 implementation report triage

W3 closed cleanly. Triage classified all four findings (F1 cosmetic with future-brief vocabulary carry; F2/F3 deployment substrate; F4 deployment substrate with W0 F4 re-parked). §7 verification criteria all PASS — 212 tests passing (158 W2+W1+W0 baseline + 54 W3), mypy clean (86 source files), ruff clean, lint-imports 5 kept 0 broken (DR-030 layered architecture intact). F5 contract revision locked at v1.1 (status header verified empirically: "v1.1 — F5 strategy_tag added Session 87 W3 (backward-compatible per §14.4)").

Substrate carry-forwards inherited from W3 to W4 + W7:
- `BetfairClient` container shape (frozen dataclass with `rest_client` required + `streaming_client` optional) is the canonical "give me a Betfair handle" shape for v3.
- `TranslatingTransport` is the integration point for v3 build proper real-API deployment (wire `BetfairRestClient(transport=TranslatingTransport(inner=httpx_transport))` at startup).
- F5 `strategy_tag` is wired through write surfaces but not yet populated by any caller — W4 bet-entry layer will be the first caller to populate it meaningfully.
- Cadence-parameter constants (W2 §12 self-assessment item 1) carry forward unchanged — Fix 4 calibration territory.
- `betfairlightweight` is shape-compatible but not imported by W2 or W3; v3 build proper deployment imports `APIClient` + `StreamListener` and pipes output into `StreamReader.raw_source`.

Deployment-substrate items routed silently to v3 build proper Betfair deployment work (paired with `TranslatingTransport` integration):
- F2: `listMarketBook` `scheduled_start_time` synthesis — deployment may want a separately-cached `listMarketCatalogue` lookup at subscription time per market, or accept that streaming cache carries `marketDefinition.marketTime` for SUBSCRIBED markets and REST fallback runs only when cache is unavailable.
- F3: identity-check via `listMarketCatalogue` runner-presence — deployment may want to inspect whether `listMarketCatalogue` is most efficient at burst-window cadence (alternatives: `listEvents`, piggy-backing on live-pricing cache).
- F4: `betfairlightweight` shape-compatible but not directly imported — deployment will import `APIClient` + `StreamListener`; the W3+ deployment brief should name this integration point explicitly. W0 F4 typed-stub carry re-parked to deployment (was an open carry; can't fire until library is actually imported).

### W4 brief drafting (paused — substrate captured for resumption)

Four design substrate decisions captured for W4 brief §5 substantive scope when drafting resumes after math review:

1. **Scope:** Betfair-side bet entry orchestration + placement-time sanity checks. Soft-book typed-price entry deferred to W4.1 (small follow-up brief between W4 and W7). UI deferred to W7. Service layer deferred to v3 build proper.
2. **Module placement:** new `workflow/bet_entry/v1/` package per DR-030 layered architecture. Pattern carries forward to W7 (`workflow/burst_review/v1/`). `import-linter` enforces layer boundaries.
3. **Placement workflow input:** `hedge_target` spec (typed parameter object — soft-book price, soft-book stake, market_id, selection_id, plus cycle metadata for stake derivation). Workflow derives Betfair lay/back parameters from spec; favourable-drift auto-recomputes stake to maintain cycle equalisation; unfavourable-drift surfaces structured `PriceDriftEnvelope` with two retry routes (hold line / accept drift). Symmetric across lay (against soft-book back) and back (against soft-book lay). Warning configurability via per-call override (`auto_accept_drift: bool = False`) plus operator config layer (read by caller, passed through to workflow).
4. **Cancel/replace + adjust:** Cancellation and replacement primitive-only (no hedge-target machinery). Combined `adjust_hedge` workflow function ships atomic-from-operator-perspective stake-and-price submission — internally executes cancel-then-place as two Betfair API calls; named failure modes (`cancel_succeeded_place_failed` etc.); operator perceives one action with one result envelope. ~50–200ms uncovered window acknowledged as Betfair-API constraint.

Architectural carry: Session 42 Betfair-as-canonical-source extension formalises **before W4.1** (when cycle-linkage is actually established at logging time), not before W4. W4's hedge-target input shape doesn't require persisted soft-book bet records — operator's operational order places the soft-book bet before opening the modal, so the modal's input is effectively final hedge-target parameters not a record reference.

### Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-021, DR-019, DR-030, DR-031 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (~43 min gap qualifies).
- **Cat 1 (V3 build picture conditional render)** — rendered inline at open (artefact updated by Session 86 close).
- **Cat 1 (open-items delta)** — skipped silently at open (no delta between Session 86 close and Session 87 open beyond Code's out-of-session work).
- **Cat 1 (drift-check)** — done at open, all three checks matched.
- **Cat 1 (silent session-open ritual)** — held. Steps 1–5 silent; Steps 6–8 combined into single brief output at end.
- **Cat 1 (silent session-close ritual)** — holding this close. Steps 1–10 silent; Step 11 produces brief verification line.
- **Cat 1 (call-driven surfacing during section-by-section drafting)** — held throughout both arcs. Triage surfaced 3 operator-relevant calls (F1, F4, forward routing) with F2/F3/§7 silent. W4 brief drafting surfaced 4 operator-relevant calls (scope, module, placement workflow, cancel/replace + adjust) with multiple operator-driven refinements on Call 3 producing the directional-drift handling shape. Cadence held cleanly without operator pull-ups on over-surfacing or under-surfacing.
- **Cat 1 (short responses, plain language)** — held throughout. Calls framed in plain operator/gambling language with operating impact. Operator's question on Call 3 (whether the sanity check was for soft-book modal log-time) caught a framing drift — Claude clarified the W4 placement is Betfair-side library code (not UI), with the soft-book log-time comparison sitting in W4.1. Drift caught; cadence resumed.
- **Cat 1 (decision-maker framing)** — held. Each call led with the choice; recommendation followed; reasoning sat behind. Operator's role as strategic decision-maker was respected — the directional-drift refinement and the hedge-math operational framing both came from operator clarifications on operational reality, not Claude framings.
- **Cat 1 (don't drift to alternatives when operator clear)** — held.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders; technical terms (`TranslatingTransport`, `PriceDriftEnvelope`, `adjust_hedge`, `listMarketBook` vs `listMarketCatalogue`, JSON-RPC, etc.) unwound where they appeared in operator-facing framing.
- **Cat 1 (escalate to detail only when warranted)** — held. The Round 9 architectural extension flag (Session 42 — Betfair as canonical source extending to all bet records) got a detailed framing because it was material; Claude flagged it explicitly before going deep. The operator's clarification then *deflated* the architectural ask correctly — Route B (pre-W4 architectural session) was over-pricing the call given the operational reality of soft-book-placed-first.
- **Cat 1 (line-break rendering for review content)** — n/a; no review-content blocks rendered this session.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open.
- **Cat 2 (Desktop Commander default)** — held. All file ops via Desktop Commander.
- **Cat 2 (REPL discipline)** — n/a; no Python REPL work this session.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)** — held. No file writes mid-session beyond the close-out artefact writes themselves.
- **Cat 2 (dry-run multi-target mechanical edits)** — n/a; no scripted edits this session.
- **Cat 2 (persist drafted artefact content to scratch)** — n/a for this session — W4 brief drafting was paused before any section text was written to disk; substrate captured in this session record (above) for resumption next session. Decision substrate IS the artefact this session produced; persistence to scratch would duplicate.
- **Cat 2 (surface structural-drift in session record)** — n/a; no structural drift in governance artefacts this session. Note: F5 contract revision was applied by Code, not by this session — Session 86 commissioned it, Code shipped it, Session 87 verified it.
- **Cat 3 (`bash_tool` non-functional)** — held. Cat 3 surfaced briefly at open when bash_tool returned "no such file" for the Mac filesystem; routed correctly to Desktop Commander tool_search and read_multiple_files.
- **Cat 3 (external API resources reach-for)** — n/a this session; W3 triage and W4 substrate both worked from W3's report and W2 substrate, not fresh Betfair API research.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-DB topics did not surface mid-session (W3 is library-internal; W4's hedge-target spec is workflow-internal).
- **Cat 4 (operational/analytical line discipline)** — held. The W4 placement workflow is strictly operational-line (Betfair-direct via the W3 read paths and write surfaces); analytical-line (capture.db) does not appear in W4's scope.
- **Cat 4 (single-cycle analysis discipline)** — held. The directional-drift handling is explicitly cycle-shaped — stake equalises cycle outcomes against the soft-book bet's parameters, not against an abstract Betfair position. This is the discipline at work in real architectural design.
- **Cat 5 (software questions are Claude's)** — held throughout. Technical detail (parser shape carry from W3, `TranslatingTransport` substrate, `BetfairClient` container shape, module placement, parameter shapes, failure-mode naming) handled by Claude. Operator-facing calls were strategic/operational shape decisions only. The hedge-math review pause is a Cat 5 boundary moment — math is software territory but math errors have operational consequences and the operator wants to verify before locking; correct routing.

## Session-87-specific reflections

- **Operator-driven design refinements on Round 9 produced sharper architecture than Claude's initial framing.** Claude's initial Route C was generic fail-closed-with-override. Three successive operator clarifications — directional handling, stake equalisation against soft-book parameters, soft-book-placed-first operational order — reshaped the design into something materially better. The cadence held: Claude framed each iteration as an operator call with my recommendation, operator's clarification became substrate for the next iteration. This is the call-driven discipline working as designed.

- **Session 42 architectural extension flag is overdue for formalisation.** Three workstreams now reference it (W4, W4.1, W6). Recommended deferring formalisation to before W4.1 — but worth flagging that if the math review session has remaining budget after the math artefact lands, the operator may want to use it for the formalisation. Carry-forward into Session 88 opening prompt.

- **Math review as standalone artefact is the right pattern for verification-style work.** The hedge-staking math behind the directional-drift handling is the kind of thing where v2 errors matter and the operator wants to read carefully. Treating it as a dedicated session deliverable rather than a sub-round of W4 brief drafting respects the verification work. Pattern likely repeats for any future "math the operator needs to verify" moments.

- **Triage cadence is now self-sustaining across both triage and brief drafting.** Triage surfaced 3 calls in 5 rounds; brief drafting surfaced 4 calls in 4 rounds (plus Round 9's multi-step refinement). No operator pull-ups on cadence either way. Cat 1 call-driven discipline is operationally stable now.

## Open items in (carried forward)

New from Session 87:

- **W3 closed** — implementation report triaged clean; substrate carry-forwards captured above; foundation clean for W4 + W7 unblock.
- **W4 brief drafting paused — four substrate decisions captured.** Resumes after Session 88 math review locks the hedge-staking formulas. Substrate documented in "What was delivered" section above.
- **Session 88 deliverable: hedge-staking math review.** Standalone artefact at `dr029/w4_bet_entry/hedge_staking_math.md` — lay-against-soft-book-back math (common case), back-against-soft-book-lay math (sports case), worked examples for favourable + unfavourable drift on both, stake-only-change vs combined stake-and-price-change examples, Betfair commission section.
- **Session 42 architectural extension formalisation flagged for before W4.1.** Three workstreams now reference it (W4 hedge-target input shape, W4.1 soft-book entry path, W6 operational store schema). Belongs in `architecture.md` extension to §D12 or new DR (DR-032 candidate). May surface in Session 88 if math-review budget allows.
- **F5 strategy_tag carry forward — operator-facing routing.** W4 bet-entry layer will be first caller to populate `strategy_tag` meaningfully. Recommend W4 brief names tag-value conventions explicitly (e.g. `safety_net`, `price_booster`, `sgm_correlated`, `synthetic_each_way`); contract-side stays Path A free-form per Session 86 lock.
- **Deployment-substrate items (F2, F3, F4)** — paired with `TranslatingTransport` integration as v3 build proper Betfair deployment carry-forwards. Surface naturally when real-API deployment work opens post-W7.

Carry-forward from Session 86 (status changes):

- **F2 / F4 / F5 substrate carries from W2 → all closed by W3 implementation.** Removed from open-items.
- **F6 carry-forward to Fix 4 brief + W3+ briefs** — unchanged; flagged in W3 brief §9 hard limits as out-of-scope; carry-forward intact for Fix 4 brief and v3 build proper deployment.
- **§12 self-assessment item 3 — audit-log durable substrate** — unchanged.
- **W1 F1 accepted as v1.0 conflation** — unchanged.
- **W1 F2 sharpening (capture.db Thoroughbred label)** — unchanged. Worth flagging at W6 brief drafting.
- **`standing_instructions.md` re-upload to Project knowledge base** — unchanged; still pending.
- **Post-DR-029-close contract documentation relocation** — unchanged. Contract is now v1.1 when it relocates per the F5 revision.
- **W0 F2 brief-language carry** — unchanged.
- **W0 F4 typed-stub carry** — re-parked this session to v3 build proper deployment per F4 routing.
- **`str_replace` namespace gotcha** — unchanged; pending Cat 3 sweep at next standing-instructions edit.
- **`governance.md` §4 deferred-capability reconciliation** — unchanged; substantive doc edit deferred to natural fresh-mind session.
- **DR-030 "18 months" reference correction** — unchanged.
- **Streaming envelope vocabulary carry** — new this session per F1; future briefs touching streaming envelope use W2's vocabulary (`op="mcm"` with `is_image` / `op="ocm"` single value), not the brief §5.1 framing.
- All other items unchanged from Session 86 carry-forward set.

## Open items out (closed this session)

- **W3 implementation report triage** — closed. All findings classified; §7 criteria PASS; F5 contract revision locked at v1.1; W4 + W7 unblocked.
- **F2 substrate carry from W2** — closed by W3 implementation (parser shipped at `_stream_parser.py`).
- **F4 Option A substrate carry from W2** — closed by W3 implementation (`TranslatingTransport` shipped at `_translation.py`).
- **F5 strategy_tag substrate carry from W2** — closed by W3 contract revision + code edits; field is wired through write surfaces awaiting first caller.
- **W0 F4 typed-stub carry-forward** — re-parked from "open carry" to "deployment substrate" per F4 finding.

## Session close state

- **Rebuild folder root:** unchanged at session level except `current_state.md` and `v3_build_picture.md` updated at close (W3 status flips from `awaiting-code-execution` to `done` and carries one session per drop rule; W4 status flips from `blocked-on-W3` to `blocked-on-math-review`; W7 status flips from `blocked-on-W3` to `unblocked` available; new milestone labels).
- **`current_state.md`:** updated at close to reflect W3 closed, W4 paused-pending-math, Session 88 ships math review artefact, then W4 brief drafting resumes.
- **`v3_build_picture.md`:** updated at close — W3 → `done` (carries one session); W4 → `blocked-on-math-review`; W7 → `unblocked` (available; sequenced behind W4 per forward routing); detail line shifts to math review.
- **`standing_instructions.md`:** unchanged this session. Re-upload to Project knowledge base still flagged in pending operator-side actions (covers Sessions 83 + 84 edits).
- **`governance.md`:** unchanged this session. §4 reconciliation still pending.
- **`decisions.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session. Session 42 extension formalisation deferred to before W4.1 (could surface in Session 88 if budget allows).
- **`dr029/`:** new folder `w4_bet_entry/` will be created Session 88 when math review artefact lands. No new files this session.
- **`sessions/`:** Session 87 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 87 opening prompt removed at close; Session 88 opening prompt written.
- **Project knowledge base:** `standing_instructions.md` stale until re-uploaded. All other canonical-truth artefacts current.
- **VPS state:** unchanged this session. No VPS calls.
- **`bethub-v3/`:** updated by Code's W3 execution between Sessions 86 and 87 — commit `2329604` shipped 13 files, +3126/-4. No further changes this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 88 opens fresh chat to ship the hedge-staking math review artefact as a standalone deliverable. After math review locks, W4 brief drafting resumes from the four substrate decisions captured in this session record.

**Session 88 shape:**

1. **First work:** read `current_state.md` plus `standing_instructions.md` in full plus `project_context.md` plus `sessions/SESSION_87.md` (this file). The four W4 substrate decisions are captured in this session record's "What was delivered" section — they are the substrate the math review serves and the substrate W4 brief drafting resumes from.

2. **Hedge-staking math review artefact authoring** at `dr029/w4_bet_entry/hedge_staking_math.md`. Single-deliverable session. Shape:
   - Lay-against-soft-book-back math (common case — Strategy 1 Safety Net, ~95% profit). Worked examples: favourable Betfair lay drift (lay-down) recomputing stake; unfavourable lay drift (lay-up) surfacing two-route choice. Both stake-only and combined stake+price examples.
   - Back-against-soft-book-lay math (sports case — less time-sensitive). Symmetric directional handling: favourable back drift (back-up) recomputing stake; unfavourable back drift (back-down) surfacing two-route choice.
   - Cycle-equalisation derivation: starting from the soft-book bet's outcome parameters (win-state payout, loss-state outcome), derive the Betfair hedge stake that makes the operator's net outcome equal across both states. Show the algebra.
   - Betfair commission section: how the 5% (or operator-account-specific) commission affects lay-side equalisation. v2's potential math errors may live here.
   - Worked numerical examples with realistic values for at least Strategy 1 (Safety Net) and Strategy 2 (Price Booster bonus-winnings sub-shape).

3. **Lock the math at end of session.** Write to disk; operator confirms the formulas; carry forward to W4 brief §5 substantive scope.

4. **If budget allows after math review:** open Session 42 architectural extension formalisation. Either extend `architecture.md` §D12 directly or draft a new DR (DR-032 candidate — Betfair as canonical source extends to all bet records; cycle-linkage join-key formalism). Optional; depends on session budget.

**Out of scope for Session 88:** W4 brief drafting itself (post-math-review session); soft-book typed-price entry math (W4.1 territory); UI behaviour around the directional-drift handling (W7 territory).

**Operator-side actions between sessions:** None required. Math review is in-session work.

## Close-out notes

Session 87 was a clean two-arc session — W3 triage closed cleanly with all findings routed and F5 locked at v1.1, then W4 brief drafting opened call-driven and surfaced four substrate decisions before pausing at the hedge-staking math review need.

The W4 pause is a substantive design decision, not a fatigue split. Operator has explicit history of math errors in v2 and wants dedicated review before formulas embed in tool. Session 88 ships the math review as a standalone artefact; W4 brief drafting resumes after with the locked math as substrate.

Three patterns worth holding onto:

- **Operator-driven design refinements through call iteration.** Round 9's directional-drift handling shape came from three successive operator clarifications, each re-shaping Claude's initial Route C into something materially better. The call-driven cadence absorbed the iteration cleanly without losing structure.

- **Architectural-extension formalisation timing matters.** The Session 42 flag could have been formalised before any of W4 / W4.1 / W6 — but its actual operational shape only became clear in this session through the operator's hedge-target operational framing. Formalising too early would have shipped a less-grounded extension; formalising before W4.1 (when the cycle-linkage actually lands) is the right timing.

- **Math review as standalone artefact is the right shape for verification work.** Treating verification-style deliverables as their own sessions respects the operator's review need and produces durable reference artefacts (the math doc lives in version control, gets referenced by W4, W4.1, W7 briefs).

W3 closed; W4 substrate captured; Session 88 math review next; W4 brief drafting resumes after.
