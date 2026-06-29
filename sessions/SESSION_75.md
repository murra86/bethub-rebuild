# Session 75

**Title:** §2.7 (API contract versioning) brief drafted and locked end-to-end. Five sections written: §1 framing, §2 `vps_client` v1.0 contract, §3 `betfair_client` v1.0 contract, §4 schema-evolution policy, §5 closure. Brief at 421 lines. §2.7 frames as a versioning-wrapper artefact (not contract-shape re-spec) since the shapes are already locked across §2.6 and §2.9. Single brief covering both module contracts; bet placement included in `betfair_client` v1.0 with write-side surfaces tagged distinctly; path-based versioning under `/v1/...` with per-surface granularity; typed envelope on every return (`fresh`/`stale`/`unavailable` + enumerated reasons); 90-day deprecation window provisional pending operational experience; both-audiences contract documentation shape (operator-readable summary + developer-readable specification) with append-only version history; per-call-site opportunistic migration. Contract documentation files (`vps_client_contract.md` + `betfair_client_contract.md`) carried forward as separate post-§2.7 artefacts — required before v3 build proper but not part of §2.7. Session 76 primary confirmed: §2.10 (external analytics scan inventory writeup).
**Opened:** 2026-05-04 11:56 ACST
**Closed:** 2026-05-04 12:34 ACST
**Wall-clock:** ~38 min substantive single sitting. Same-workday open relative to Session 74's 11:44 ACST close (~12 minute gap).
**Tool routing:** Claude Chat. No Code routing.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline — load-bearing for the one-file boundary protection in both contracts), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 11:56 ACST`.
Close: same command → `2026-05-04 12:34 ACST`.

Same-workday open relative to Session 74's 11:44 ACST close. ~12 minute gap. Single morning sitting, immediate continuation.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_75_opening_prompt.md` only (Session 74 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 11:44 ACST` matched Session 74 close; `sessions/SESSION_74.md` present (267 lines); `v3_build_picture.md` last-updated `2026-05-04 11:44 ACST` matched Session 74's stream-state updates (§2.6 → done, §2.7 → in flight).
- Same-workday recap delivered (tight: Session 74 closed §2.6 race-path settlement brief; Session 75 picks up §2.7 API contract versioning per Session 74 forward routing).
- V3 build picture: rendered at open since stream state moved.
- Open-items delta: skipped silently (no movement in 12 min since Session 74 close).

## Session shape

Session 75 was a **brief-drafting session** — drafting §2.7 (API contract versioning) from scratch per Session 74 forward routing. Five sections landed across five drafting rounds (one round per section). The session's tempo was tighter than Session 74's (~38 min vs ~93 min) because §2.7's wrapper-shape framing made each section more compositional than design-from-first-principles — the contract shapes were already locked across §2.6 and §2.9, so §2.7's job was the policy and discipline layer wrapping them.

Two strategic framing decisions locked at session open shaped the drafting:

**Single brief vs two parallel briefs.** Operator confirmed single brief covering both `vps_client` and `betfair_client` contracts. Shared schema-evolution policy + governance traceability tighter in one artefact. Matches §2.6's shape (race path single brief, sports-side carry-forward separately).

**Versioning-wrapper shape vs re-specifying contract shapes.** Operator confirmed wrapper shape — §2.7 specifies the versioning discipline (path-based versioning, typed envelope, schema evolution policy, deprecation framework, documentation discipline) but does not re-specify the contract shapes themselves. The shapes live in §2.6 §5.1 (`betfair_client` settlement-read) and §2.9 §6.1 (`vps_client` and `betfair_client` v1.0 contracts). §2.7 wraps them in versioning policy.

Operator framing pivot at session open: *"Let's do this review as per the previous reviews. You are the Software/Data Architect Specialist. I just make the strategic operation and execution calls and decisions."* Memory edit #16 stance applied as explicit role assignment for this session — Claude leads architecture, operator makes strategic operation/execution calls. Pattern held cleanly throughout: each round surfaced one to two strategic questions for operator decision (single brief vs two; wrapper vs re-spec; explicit-signal vs simple-null staleness handling; bet placement carved out vs in-contract; deprecation window length; documentation location; documentation audience shape; contract documentation files inside §2.7 vs carried forward) plus the §2.4 cadence-deferral confirmation that opened the session, with technical detail (sub-section structure, sub-section content, path patterns, reason enumerations, evolution-policy specifics, migration discipline) handled inside the artefact rather than surfaced for operator review.

Round-by-round shape:

**Round 1 (scope read + framing decisions).** Operator confirmed single brief covering both contracts and versioning-wrapper shape. Five-section structure proposed and confirmed. §2.4 Streaming-cadence deferral confirmed (cadence is parameters, contract is connection-and-message shape).

**Round 2 (§1 framing drafted, written).** §1 written first (5 sub-sections, 57 lines). What §2.7 specifies (versioning wrapper across two contracts), why versioning matters differently for `vps_client` (BetHub-controlled schema) vs `betfair_client` (Betfair-controlled API), two failure modes guarded against (schema drift propagation; Betfair API churn), load-bearing inputs (§2.6, §2.9, §2.4, DR-027/028), load-bearing outputs (locked v1.0 contracts; schema-evolution policy; deprecation framework; documentation location; substrate for DR-029 close-out governance paragraph).

**Round 3 (§2 `vps_client` v1.0 contract drafted, written).** Strategic question: explicit signal envelope vs simple null + log for staleness handling. Operator confirmed explicit signal. §2 written (5 sub-sections, 79 lines). Six call-surface categories named (race metadata, runner metadata, results, bracketing, BSP / sp_near / sp_far, identifier-resolution); path-based versioning under `/v1/...` with rationale (visibility at call site, mechanically simple parallel running) over header-based; typed envelope with three statuses (`fresh` / `stale` / `unavailable`) and five enumerated unavailability reasons (`vps_unreachable`, `capture_db_locked`, `not_yet_captured`, `not_in_capture_window`, `genuine_absence`); DR-028 one-file boundary; five out-of-scope categories.

**Round 4 (§3 `betfair_client` v1.0 contract drafted, written).** Strategic question: bet placement in `betfair_client` v1.0 vs carved out as separate `betfair_writer` contract. Operator confirmed in-contract — same connection, same auth context, same rate-limit budget; DR-028 protection requires single boundary against the same external API. Write-side surfaces tagged distinctly in documentation and reason enumeration. §3 written (5 sub-sections, 103 lines). Six surface categories (operational live pricing, settlement reads, sports-line query, scheduled-time reads, identifier-resolution checks, Streaming connection) plus three write surfaces (placement, cancellation, replacement); path-based versioning decoupled from Betfair's own API versioning (critical protection — Betfair API churn absorbed inside `betfair_client` for as long as wrapper can absorb it); expanded reason enumeration with Betfair-specific reasons (`betfair_auth_expired`, `betfair_rate_limited`, `betfair_market_suspended`, `betfair_streaming_disconnected`, `betfair_market_not_found`, `betfair_api_unreachable`) plus write-side prefix (`betfair_write_*`); streaming-disconnect-blocks-writes contract behaviour; five out-of-scope categories plus write-side documentation tagging (distinct section in contract documentation, distinct reason prefix, audit-trail requirement on every write-surface call).

**Round 5 (§4 schema-evolution policy drafted, written).** Three strategic questions: deprecation window length (90 days confirmed provisional), documentation location (under `dr029/2_7_api_contract_versioning/` for v1.0, post-DR-029-close relocation to v3 project root confirmed), documentation audience shape (both — operator-readable summary at top + developer-readable specification below). Operator clarification question on §4.1: "Are backward-compatible additions defined yet?" Claude clarified — §4.1 specifies the policy, not pre-enumerated additions. The "make space for later" deferred capabilities (§2.10 inventory outcomes, PASSIVE bet-delay handling, CLV analytical signal, post-DR-029 monitoring, operational soft-book) are capacity in v1.0 not v1.0 content; the §4.1 backward-compat policy is what makes them capacity. Operational soft-book layer flagged as exception — does not land as `vps_client`/`betfair_client` extension; returns as fresh DR with its own contract module. §4 written (5 sub-sections, 116 lines). Backward-compatible additions in-place with deferred capabilities flagged as capacity; breaking changes via new version only with strict-when-in-doubt discipline and per-surface granularity (e.g. `/v2/market/{market_id}/settlement` issues independently of other `betfair_client` surfaces); 90-day deprecation framework with parallel running and end-of-window retirement; contract documentation discipline with both-audiences shape and append-only version history (governance events, not casual changes); per-call-site opportunistic migration over the deprecation window with rollback discipline.

**Round 6 (§5 closure drafted, written).** Strategic question: contract documentation files inside §2.7 vs carried forward as separate post-§2.7 artefacts. Operator confirmed carried forward. Reasons: contract shapes already locked in §2.6 §5.1 and §2.9 §6.1 (mostly transcription against locked specs); drafting both files inside §2.7 would double or triple brief length; developer-readable spec section is properly Code-bound work (likely a brief commissioning Code to draft formal type signatures). §5 written (5 sub-sections, 71 lines). What §2.7 locks (v1.0 of both contracts plus shared schema-evolution policy with capacity for deferred capabilities); six categories of what §2.7 does not specify (cadence parameters, actual call signatures and field-level type definitions, migration friction tolerance, auth flow specifics, rate-limit budget allocation, operational-soft-book contract shape); three things §2.7 unblocks (v3 build proper at contract level, DR-029 close-out governance paragraph substrate, future deferred-capability DR template); five carry-forward items (contract documentation files themselves, post-DR-029-close relocation, 90-day deprecation window revisit, auth flow implementation specification, rate-limit budget allocation tuning, operational experience surfacing new edge cases); six things §2.7 does not unblock (§2.10, DR-029 close itself, v3 build proper start, operational soft-book layer, sports analytical capability, burst-review triage workflow design).

**Round 7 (close confirmation).** Operator: "Please close up and prepare for next session." Forward routing for Session 76 confirmed at close — §2.10 over contract documentation files.

## What was delivered

### 1. §2.7 brief drafted and locked end-to-end

Brief at `dr029/2_7_api_contract_versioning/2_7_api_contract_versioning.md`. 421 lines. Five sections, all locked.

**§1 Framing** (57 lines, 5 sub-sections). What §2.7 specifies (versioning wrapper across two contracts, not contract-shape re-spec). Why versioning matters here (v3 build proper protection from contract churn — different shapes for `vps_client` vs `betfair_client`). Two failure modes guarded against (schema drift propagation; Betfair API churn). Load-bearing inputs (§2.6 §5.1, §2.9 §6.1, §2.4 connection shape, DR-027/028). Load-bearing outputs (locked v1.0 contracts; schema-evolution policy; deprecation framework; named documentation location per contract; substrate for DR-029 close-out governance paragraph).

**§2 `vps_client` v1.0 contract** (79 lines, 5 sub-sections). Six call-surface categories named (race metadata, runner metadata, results, bracketing, BSP / sp_near / sp_far, identifier-resolution). Path-based versioning under `/v1/...` with rationale over header-based. Typed envelope on every return — three statuses (`fresh`/`stale`/`unavailable`), five enumerated unavailability reasons. DR-028 one-file boundary protecting v3 from `capture.db` schema knowledge scatter. Five out-of-scope categories (operational reads, writes to `capture.db`, soft-book operational reads, analytics-derived fields, sports analytical reads).

**§3 `betfair_client` v1.0 contract** (103 lines, 5 sub-sections). Six read surface categories plus three write surfaces tagged distinctly. Path-based versioning under `/v1/...` decoupled from Betfair's own API versioning — critical decoupling that contains Betfair API churn inside `betfair_client` for as long as the wrapper can absorb it. Expanded reason enumeration with six Betfair-specific reasons plus three write-side reasons (`betfair_write_rejected` with Betfair rejection code payload, `betfair_insufficient_funds`, `betfair_bet_placement_in_progress` debounce guard). DR-028 one-file boundary against Betfair API churn — auth handling included inside boundary. Streaming-disconnect-blocks-writes as contract-level behaviour (not v3-side decision). Five out-of-scope categories plus write-side documentation tagging discipline (distinct documentation section, distinct reason prefix `betfair_write_*`, audit-trail requirement on every write-surface call).

**§4 Schema-evolution policy** (116 lines, 5 sub-sections). Backward-compatible additions in-place — five categories enumerated, deferred capabilities flagged as capacity rather than v1.0 content (operational soft-book carved out as future-DR-with-own-contract-module exception). Breaking changes via new version only — eight categories of breaking change enumerated, strict-when-in-doubt discipline, per-surface granularity. 90-day deprecation framework — parallel running of v1 and v2 during window, deprecation warning logging, end-of-window retirement to "retired surfaces" appendix. Contract documentation location and discipline — single source of truth file per contract, both-audiences shape (operator-readable summary at top, developer-readable specification below), append-only version history, edits as governance events. Per-call-site opportunistic migration discipline with rollback path.

**§5 What §2.7 closes for DR-029, what's deferred** (71 lines, 5 sub-sections). What §2.7 locks — v1.0 of both contracts plus shared schema-evolution policy plus capacity for deferred capabilities. Six categories of what §2.7 does not specify. Three things §2.7 unblocks — v3 build proper at contract level, DR-029 close-out governance paragraph substrate, future deferred-capability DR versioning policy template. Five carry-forward items including contract documentation files themselves (required before v3 build proper but separate post-§2.7 work). Six things §2.7 does not unblock.

### 2. Strategic decisions locked

Nine strategic decisions confirmed by operator and locked into the brief:

1. **Single brief covering both contracts** rather than two parallel briefs. Shared schema-evolution policy plus governance traceability cleaner in one artefact.
2. **Versioning-wrapper shape** rather than re-specifying contract shapes. Shapes already locked across §2.6 §5.1 (settlement-read five-field) and §2.9 §6.1 (`vps_client` and `betfair_client` v1.0 contract surfaces); §2.7 wraps them in versioning policy.
3. **Path-based versioning** (`/v1/...`) rather than header-based. Visibility at call site, mechanically simple parallel running, documentation tracks paths cleanly. Applied identically to both contracts.
4. **Typed envelope on every return** (`fresh`/`stale`/`unavailable` + enumerated reasons) rather than simple null + log. v3 modules switch on closed-set states for consistent UX; raw `capture.db` query exceptions and Betfair API errors never reach v3 modules — every exceptional case mapped to typed envelope status by the boundary module.
5. **Bet placement in `betfair_client` v1.0** rather than carved out to separate `betfair_writer` contract. Shared connection, auth context, rate-limit pool; DR-028 protection requires single boundary; write-side surfaces tagged distinctly in documentation, reason enumeration prefix (`betfair_write_*`), and audit-trail requirements.
6. **`betfair_client` versioning decoupled from Betfair's own API versioning.** Critical protection — `betfair_client` v2.0 issues only when v3-facing typed return shape itself changes, not when Betfair API surfaces churn internally. Wrapper absorbs Betfair-driven changes when possible; forces v2.0 only when v3-facing change unavoidable.
7. **90-day deprecation window** as v1.0 default, provisional pending operational experience. Per-call-site opportunistic migration over the window; revisit triggered on first observed migration friction (either too short — pressure-driven migration — or too long — parallel-version overhead accumulating).
8. **Both-audiences contract documentation** — operator-readable summary at top + developer-readable specification below in single file. Append-only version history. Edits as governance events, not casual changes.
9. **Contract documentation files drafted as separate artefacts post-§2.7** rather than inside §2.7. Reasons: shapes already locked in §2.6 / §2.9 (transcription work); drafting inside §2.7 would double brief length; developer-readable spec is properly Code-bound work. Contract documentation files required before v3 build proper but not part of §2.7.

### 3. §2.7 brief now load-bearing input for DR-029 close-out

§2.7's versioning discipline is one of the named pieces in the DR-029 close-out governance paragraph (alongside the three pieces of debt, periodic data-fitness re-verification, operational/analytical line discipline). Survives DR-029 close into v3 build proper as one of the standing disciplines. Provides the versioning policy template that future deferred-capability DRs (operational soft-book, sports analytical, analytics layer formalisation) reuse independently — same shape applied per contract module.

### 4. Working-style adherence

Memory edit #16 stance applied as explicit role assignment for this session per operator framing: *"You are the Software/Data Architect Specialist. I just make the strategic operation and execution calls and decisions."* Pattern held cleanly throughout — each round surfaced one to two strategic questions for operator decision; technical detail (sub-section structure, sub-section content, path patterns, reason enumerations, evolution-policy specifics, migration discipline) handled inside the artefact rather than surfaced for operator review. Operator's one clarification question (Round 5: "Are backward-compatible additions defined yet?") was a precision question on §4.1 framing, resolved cleanly with the policy-not-pre-enumerated framing plus deferred-capabilities-as-capacity flagging.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (tight, ~12 minute gap from Session 74 close).
- **Cat 1 (V3 build picture conditional render)** — rendered at open since stream state moved at Session 74 close (§2.6 → done, §2.7 → in flight). To be updated at this close (§2.7 stream moves from `in flight` to `done`; §2.6 carry-rule one-session post-close drops; §2.10 promoted to `in flight`).
- **Cat 1 (open-items delta)** — skipped silently at open (no movement in 12 min). Will fire at next session open if movement.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Round-by-round cadence with one to two strategic questions per round. No paragraph-stacking.
- **Cat 1 (decision-maker framing)** — held. Each round led with the call or recommendation. Strategic questions explicitly framed as operator decisions with Claude's recommendation flagged for confirmation/pushback.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. When operator confirmed each strategic decision, Claude proceeded directly to the next section.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders. `vps_client`, `betfair_client`, `capture.db`, `betfair_market_id`, `betfair_selection_id`, `placeOrders`, `cancelOrders`, `replaceOrders`, `marketTime`, `settledTime`, `dead_heat_count`, `removed_runner_count`, `unexpected_state_count` unwound on use.
- **Cat 1 (escalate to detail only when warranted)** — held. Operator's clarification question on §4.1 answered with precision-level detail (deferred capabilities as capacity vs content) without escalating beyond the immediate question scope.
- **Cat 1 (line-break rendering for review content)** — held. All §2.7 brief draft sections delivered in fenced markdown rendering inside the canonical artefact rather than chat preview blocks (consistent with §2.6 / §2.9 pattern).
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. No mid-session re-anchor needed; single sitting under 60 minutes.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held. Initial `mkdir` for `2_7_api_contract_versioning/` directory routed through `Desktop Commander:start_process` directly (Session 74 lesson absorbed).
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python REPL work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; all §2.7 draft content written directly to canonical artefact during the session. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — n/a; no structural drift this session. The wrapper-shape framing (§2.7 wraps shapes locked in §2.6 / §2.9) was not a structural change to existing artefacts; §2.7's scope per `dr029/dr029_scope.md` §2.7 was unchanged. All structural decisions surfaced inside the new §2.7 brief.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — minimal engagement. The Betfair API surface was referenced from prior locked §2.6 / §2.9 work; no fresh API surface investigation needed for §2.7's wrapper discipline.
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — n/a; all writes were single-target appends to the §2.7 brief.
- **Cat 3 (write-file vs create_file namespace gotcha)** — n/a; all writes via `Desktop Commander:write_file` directly.
- **Cat 4 (DR-027/028 invoked)** — named at open. DR-028 load-bearing throughout — the one-file boundary protection in both `vps_client` §2.4 and `betfair_client` §3.4 is direct DR-028 application. DR-027 anchoring the operational/analytical line separation (`vps_client` for analytical reads against `capture.db`; `betfair_client` for operational reads against Betfair direct).
- **Cat 4 (operational/analytical line discipline)** — engaged throughout. §2 (`vps_client`) explicitly bounded as analytical-line read surface; §3 (`betfair_client`) explicitly bounded as operational-line read + write surface. The split is the contract architecture, not just a discipline overlay.
- **Cat 4 (Betfair-as-canonical-source extension)** — load-bearing this session at the contract level. Betfair identifiers (`betfair_market_id`, `betfair_selection_id`) are the canonical join keys across both `vps_client` (analytical-side identifier resolution) and `betfair_client` (live-side identifier check). Per Session 42 architectural extension, this carries through to all bet records (Betfair-direct or softbook-typed-price).
- **Cat 5 (software questions are Claude's)** — held cleanly. Operator framed the session at open with explicit role assignment ("Software/Data Architect Specialist" leading architecture; operator making strategic operation/execution calls). Section structure, sub-section design, surface enumeration, reason enumeration, evolution-policy specifics, deprecation framework structure, migration discipline — all Claude's calls (proposed for confirmation). Operator's strategic decisions (single brief vs two; wrapper vs re-spec; explicit signal vs simple null; bet placement in-contract vs carved out; deprecation window length; documentation location; documentation audience shape; contract documentation files inside §2.7 vs carried forward) involved scope and execution choices Claude proposed but operator confirmed. Cat 5 line held cleanly.
- **Cat 5 (operator working-style — memory edit #16)** — held throughout. Strategic questions one to two per round; technical detail in the artefact. Operator's one clarification question (§4.1 backward-compat additions) was a precision question, not a reframe; Claude answered with policy-vs-content distinction without diluting brief substance.

## Open items in (carried forward + new)

New from Session 75:

- **§2.7 brief end-to-end** — **CLOSED Session 75.** All 5 sections locked. Brief at `dr029/2_7_api_contract_versioning/2_7_api_contract_versioning.md` (421 lines).
- **`vps_client_contract.md` documentation file** — required artefact before v3 build proper. Drafted as separate post-§2.7 artefact. Likely Code-bound brief for developer-readable formal spec section against §2.6 / §2.9 locked shapes; operator-readable summary in Chat. Required before v3 build proper but not part of §2.7. **Part of DR-029 critical path.**
- **`betfair_client_contract.md` documentation file** — same shape as above. Required artefact before v3 build proper. **Part of DR-029 critical path.**
- **Post-DR-029-close contract documentation relocation** — both contract documentation files move from `dr029/2_7_api_contract_versioning/` to permanent v3 location (likely `contracts/` folder at v3 project root) as part of DR-029 close-out documentation pass.
- **90-day deprecation window revisit** — provisional v1.0 default; revisit triggered on first observed migration friction. v3 operational parameter, not §2.7 amendment trigger.
- **Auth flow implementation specification** — `betfair_client` v1.0 names auth handling as inside the boundary but does not specify flow shape. Lands inside `betfair_client_contract.md` developer-readable section when that file drafts, not as part of §2.7.
- **Rate-limit budget allocation tuning** — `betfair_client` v1.0 implementation discipline; v3 build proper operational parameter tuning, not contract shape.

Carry-forward (unchanged structure where applicable):

- **§2.6 settlement model — race path** — CLOSED Session 74. Carry post-close window expires this close.
- **§2.7 API contract versioning** — **CLOSED Session 75.**
- **§2.8 bet-schema reframing** — CLOSED Session 72.
- **§2.9 write-side bet-entry coherence** — CLOSED Session 73.
- **§2.10 external analytics scan** — substantially fed by probe; inventory writeup remaining. Independent of §2.6, §2.7, §2.9. **Recommended Session 76 primary candidate per session-order proposal locked at Session 73; confirmed by operator at Session 75 close.**
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records. Reaffirmed throughout §2.7 (Betfair identifiers as canonical join keys across both contract modules). Continues as administrative cleanup (`architecture.md` §D12 sub-section update post-DR-029).
- **Sports-side dead-heat capture in `architecture.md` §B.1.4** — administrative cleanup carry-forward from Session 74. AFL head-to-head ties, NRL equivalents need `dead_heat_count` capture identical to racing dead heats.
- **Past-settlement-window threshold calibration** — v3 day-one ships with 30 minutes from race finish; calibrate from operational experience.
- **Settlement worker periodic verification cadence** — §2.6 §3.4 condition 2 (post-settlement market voids) requires terminal-state re-reads at periodic cadence. v3 build proper operational tuning, not §2.6 spec.
- **Cluster 1 surgical-fix carry-in (analytical-layer prep)** — `runners.finish_position` backfill + `racing-metadata-backfill.service` rework. Dropped from §2.6 scope Session 74. Non-gating analytical-layer prep work.
- **Complete cascade map** — parked. Best done post-DR-029.
- **CLV as analytical-layer signal** — built post-DR-029.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — operational design downstream. Now also feeds §2.6 burst-review queue UI (v3 build proper).
- **`marketTime` mutability empirical question** — folded into Fix 4 cadence brief drafting per §2.9 §3.5.
- **§2.9 §4.4 six edge cases** — documented for burst-review reference, no mitigation built.
- **Fix 4 (Racing API cadence design)** — non-gating. Includes `marketTime` mutability empirical question.
- **Fix 5 (venue harmonisation)** — non-gating.
- **Fix 9 (Racing API re-fetch)** — non-gating.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — non-gating.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — Fix 8 report §8.5 recommendation.
- **Session numbering slip in probe brief** — cosmetic.
- **EX_LADDER entitlement question** — operator-side homework. Informs §2.9 §4.4 (e) and §2.6 §4.6.
- **Drift-check methodology gap** — substrate from Session 64 carry-forward.
- **`bethub-analytical` project awaiting activation** — operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** — parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — non-gating.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — substrate input for analytical scan.
- **BetWatch contacted re: API service and book coverage** — awaiting response. No longer gating per Session 69.
- **Betfair API membership tiers — investigate.** Operator-side homework.
- **PASSIVE bet-delay model handling** — flagged in §2.4 §15.4 as v3.1+ capability.
- **Three pieces of named debt being carried into v3 build** — substrate for DR-029 close-out governance paragraph.

Gaps from earlier reviews logged for awareness:

- **Claude-67 G1** — AU-specific session expiry not on disk.
- **Claude-67 G2** — `listCurrencyRates` API surface silent in captured reference.
- **Claude-67 G3** — Racing API ↔ Betfair market identity reconciliation implicit.
- **Claude-67 G4** — `listCurrentOrders` filter parameter list not in captured reference.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC` betDelay confidence note.

## Open items out

Closed this session:

- **§2.7 §1 framing** — locked.
- **§2.7 §2 `vps_client` v1.0 contract** — locked.
- **§2.7 §3 `betfair_client` v1.0 contract** — locked.
- **§2.7 §4 schema-evolution policy** — locked.
- **§2.7 §5 closure** — locked.
- **§2.7 brief end-to-end** — CLOSED Session 75.
- **Single brief vs two parallel briefs strategic question** — locked single brief.
- **Versioning-wrapper vs re-spec strategic question** — locked wrapper.
- **Path-based vs header-based versioning strategic question** — locked path-based.
- **Explicit signal envelope vs simple null + log strategic question** — locked explicit signal.
- **Bet placement in `betfair_client` v1.0 vs carved out strategic question** — locked in-contract with write-side tagging.
- **Deprecation window length strategic question** — locked 90 days provisional.
- **Documentation location strategic question** — locked under `dr029/2_7_api_contract_versioning/` for v1.0, post-DR-029-close relocation to v3 project root.
- **Documentation audience shape strategic question** — locked both-audiences shape.
- **Contract documentation files inside §2.7 vs carried forward strategic question** — locked carried forward.
- **§2.6 carry-post-close window** — expires this close per `v3_build_picture.md` carry-rule.

## Session close state

- **Rebuild folder root:** 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present. **One new directory created this session:** `dr029/2_7_api_contract_versioning/`.
- **`current_state.md`:** to be updated by close ritual to reflect Session 76 forward routing (§2.10 external analytics scan inventory writeup primary candidate).
- **`v3_build_picture.md`:** **to be updated this close.** §2.7 stream moves from `in flight` to `done`. §2.10 stream moves from `unfinished` to `in flight` (Session 76 primary candidate). §2.6 (carry-rule one-session post-close from Session 74) drops.
- **`standing_instructions.md`:** unchanged this session. No new instructions surfaced.
- **`dr029/2_7_api_contract_versioning/2_7_api_contract_versioning.md`:** **created this session.** 421 lines. Status: complete. All 5 sections locked.
- **`dr029/dr029_scope.md`:** unchanged this session. §2.7 scope per existing locked text unchanged; §2.7 brief assembled within scope.
- **`architecture.md`:** unchanged this session. Sports-side dead-heat capture amendment to §B.1.4 carry-forward from Session 74 still pending.
- **`decisions.md`:** unchanged this session. No new DRs surfaced.
- **`sessions/`:** Session 75 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 75 opening prompt to be removed at close; Session 76 opening prompt to be written.
- **Project knowledge base:** unchanged; no operator-side actions required for Session 76 open.
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** §2.10 (external analytics scan inventory writeup) as Session 76 primary, over contract documentation files. Reasons: §2.10 is the last unwritten DR-029 in-scope deliverable; closing it leaves only contract documentation files plus close-out governance paragraph as DR-029 critical-path items; §2.10 inventory writeup is independent and lands in Chat without Code routing; contract documentation files will likely take Code-bound brief shape (transcription work) and that brief is itself worth drafting in Chat as a deliberate handoff after §2.10 closes (keeps work shapes separated).

**Session 76 primary deliverable: §2.10 (external analytics environmental scan inventory writeup).**

Sequence:

1. **First work:** read `dr029/dr029_scope.md` §2.10 for locked scope reminder; review Saturday API observation probe report (`dr029/2_1_race_data/api_probe_brief.md` and follow-on report) for the substantive feed into the inventory.
2. **§2.10 framing** — what the inventory captures (Betfair API + Racing API fields available but not currently captured), capture-cheap classification (available + currently captured → no action; available + not captured + cheap → capture; available + not captured + expensive OR not available → parked with rationale), no new external API calls beyond what's already authorised, no analytics design (capture-only constraint).
3. **Section-by-section per Cat 1 default cadence** — likely cuts: framing, Betfair API field inventory, Racing API field inventory, capture-cheap classification + bucket assignment, parked-with-rationale items, what §2.10 closes.

**Alternative routing if operator prefers:** contract documentation files (`vps_client_contract.md` and `betfair_client_contract.md`) drafting per §2.7 §5.4 — likely Code-bound brief shape for the developer-readable spec section against §2.6 / §2.9 locked shapes. Two-session work approximately.

**Out of scope for Session 76:** contract documentation files (until §2.10 closes if §2.10 is the chosen route); anything outside the chosen primary deliverable.

**Operator-side actions between sessions:**

1. **(Optional, low priority)** Investigate Betfair API membership tiers — informs EX_LADDER / SP-actual entitlement question.
2. **(Optional)** Awaiting BetWatch response — no longer gating; informs future operational-soft-book DR.
3. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.
4. **(Optional)** Review §2.7 brief end-to-end at leisure (between-session work; not a Session 76 blocker).
5. **(Optional)** Review §2.6 brief end-to-end at leisure (between-session work; not a Session 76 blocker).
6. **(Optional)** Review §2.9 brief end-to-end at leisure (between-session work; not a Session 76 blocker).
7. **(Optional)** Review §2.8 brief end-to-end at leisure (carry-forward from Session 72).

## Close-out notes

Single morning sitting, ~38 min wall-clock — significantly shorter than Sessions 73 (~87 min) and 74 (~93 min) for similar fresh-brief drafting work. The compression is structural — §2.7's wrapper-shape framing made each section more compositional than design-from-first-principles, since the contract shapes were already locked in §2.6 §5.1 and §2.9 §6.1. The session's primary intellectual work was the policy and discipline layer wrapping the locked shapes, plus the eight strategic decisions surfaced in two-question rounds rather than free-running operator-Claude exchange.

Three working-style moments worth holding onto:

- **Round 1 explicit role assignment.** Operator framed the session at open with *"You are the Software/Data Architect Specialist. I just make the strategic operation and execution calls and decisions."* Pattern: when memory edit #16 is applied as explicit role assignment for a specific session shape (rather than implicit working-style preference), the cadence tightens — strategic questions surface explicitly, technical detail goes into the artefact, neither side does the other's job. Worth recognising as an effective session-opening framing for governance/spec work shapes.

- **Round 5 deferred-capabilities-as-capacity clarification.** Operator's *"Are these defined yet?"* clarification on §4.1 backward-compatible additions was a precision question on policy vs content — exactly the question that surfaces the right framing distinction. The deferred capabilities (operational soft-book, §2.10 inventory outcomes, PASSIVE bet-delay, CLV analytical signal, post-DR-029 monitoring) are *capacity* in the v1.0 contracts (the §4.1 policy lets them land as backward-compat additions when they arrive), not v1.0 *content*. The operational soft-book carve-out (returns as fresh DR with own contract module, not as `vps_client`/`betfair_client` extension) is the exception that proves the rule. Pattern: operator's precision-shaped questions on framing produce the cleanest brief sections, even when the answer is "your reading was right; let me make the distinction explicit."

- **Round 6 contract documentation files carved out.** Operator's confirmation on the carved-out shape locked the §2.7 brief at policy-only rather than policy + two formal contract specs. The reasoning chain — shapes locked in §2.6 / §2.9; transcription work; brief length; developer-readable spec is Code-bound — landed cleanly. Pattern: when scope-narrowing is well-supported by structural reasons (work shape, length, tool routing), the operator confirmation lands fast and the brief stays digestible. Comparison point: Session 74's §2.6 was a single-brief-with-everything-in-it shape; §2.7 deliberately carved out the contract documentation files. Both are correct for their respective work shapes — the difference is whether the underlying spec work is design-from-first-principles (§2.6) or transcription-against-locked-shapes (the contract documentation files).

§2.7 brief is now locked. Session 76 picks up §2.10 (external analytics scan inventory writeup) — the last unwritten DR-029 in-scope deliverable.
