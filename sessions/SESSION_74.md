# Session 74

**Title:** §2.6 (settlement model — race path) brief drafted and locked end-to-end. Five sections written: §1 framing, §2 Betfair Win as canonical settlement source, §3 settlement state machine, §4 edge cases, §5 closure. Brief at 649 lines. §2.6 narrowed Session 74 from the original two-source-agreement framing (Betfair Win + Racing API) to **Betfair-only canonical** for v3 day-one — operator-locked at session open. Three additional design decisions locked: provisional state earns its keep with auto-resolution + manual-escalation paths; past-settlement-window flag is operational visibility surface (not a state); full-market-book read at settlement time captures three count fields (`dead_heat_count`, `removed_runner_count`, `unexpected_state_count`) at no extra API cost. Cluster 1 surgical-fix carry-in dropped from §2.6 scope per Betfair-only narrowing. Sports-side dead-heat handling (AFL ties, NRL equivalents) flagged as `architecture.md` §B.1.4 administrative cleanup carry-forward.
**Opened:** 2026-05-04 10:11 ACST
**Closed:** 2026-05-04 11:44 ACST
**Wall-clock:** ~1h 33m substantive single sitting. Same-workday open relative to Session 73's 09:51 ACST close (~20 minute gap).
**Tool routing:** Claude Chat. No Code routing.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring), DR-019 (derived state on read — load-bearing for §2.6 settlement-state derivation).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 10:11 ACST`.
Mid-session anchor (after §3 written, before §4): same command → `2026-05-04 11:42 ACST` (~91 min in).
Close: same command → `2026-05-04 11:44 ACST`.

Same-workday open relative to Session 73's 09:51 ACST close. ~20 minute gap. Single morning sitting, immediate continuation.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_74_opening_prompt.md` only (Session 73 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 09:51 ACST` matched Session 73 close; `sessions/SESSION_73.md` present (259 lines); `v3_build_picture.md` last-updated `2026-05-04 09:51 ACST` matched Session 73's §2.9 stream-completion update.
- Same-workday recap delivered (tight: Session 73 closed §2.9 brief end-to-end with three strategic calls; Session 74 picks up §2.6 race-path settlement primary candidate per Session 73 forward routing).
- V3 build picture: rendered at open since stream state moved (§2.9 → done, §2.6 → in flight, §2.8 carry-rule drop).
- Open-items delta: skipped silently (no movement since Session 73 close ~20 min prior).

## Session shape

Session 74 was a **brief-drafting session** — drafting §2.6 (settlement model — race path) from scratch per Session 73 forward routing. Five sections landed across nine drafting rounds: §1 framing (5 sub-sections), §2 Betfair Win as canonical settlement source (4 sub-sections), §3 settlement state machine (6 sub-sections), §4 edge cases worth naming (7 sub-sections), §5 closure (5 sub-sections).

The session opened with an **operator-driven scope narrowing** that fundamentally simplified §2.6's design. The locked DR-029 §2.6 scope (per Session 27) specified two-source agreement: Betfair Win market + Racing API result, both consulted, agreement → `finalised`. The operator narrowed at session open: "We're just using Betfair as the canonical source for settlement data for the initial stages... I can't see any instances where Betfair would deviate from the softbook... There may be some edge cases with dead heats or scratchings or things like that, but they will be caught from mismatches in the softbook balances." The narrowing landed cleanly: Betfair-only canonical for v3 day-one, soft-book balance reconciliation as the operational backstop, Racing API result remains in `capture.db` as analytical-layer data (independent of settlement). No revisit-policy forward-pointer to Racing API specifically — held as a general "alternative sources" question if operational divergence eventuates.

Three additional design decisions emerged from operator-Claude exchange during drafting:

**Round 4 (provisional state retention).** Claude drafted §3 with finalised/provisional split per the §2.2 sports-path parallel; operator was 50/50 on whether `provisional` actually earned its keep for race-path settlement. After §3.5 laid out the case for both keeping and collapsing, operator confirmed keep — primary value is in capturing the two real-action triggers (unexpected per-runner state, post-settlement market void), with auto-resolution + manual-escalation paths protecting against operator burden.

**Round 5 (auto-resolution + past-settlement-window reframe).** Operator caught two issues with Claude's initial §3 design: (a) settlement worker should keep reading once a bet enters `provisional` so cases that eventually settle don't sit frozen waiting for operator action; (b) the "settlement past expected window" trigger for `provisional` is wrong — when Betfair itself hasn't settled, there's nothing for the operator to review, so surfacing as burst-review item is noise. Reframed to: (a) auto-resolution path from `provisional` back to terminal states; (b) past-settlement-window flag becomes operational visibility surface (not a state-machine entry), with bets staying in `pending` indefinitely while the worker keeps reading. State machine narrowed from five states with three burst-review triggers to five states with two real triggers + manual escalation.

**Round 6 (manual operator escalation).** Operator voiced "50/50" thought about whether operator should be able to manually escalate a bet to `provisional`. Claude argued for adding it: structurally trivial (one transition), captures operator-side information v3 can't see (external stewards' inquiry signals, soft-book balance discrepancies spotted independently), protects against v3-build-proper failure mode of treating state machine as locked-against-manual-escalation. Operator confirmed.

**Round 7 (full-market-book read generalisation).** Operator asked whether Betfair settlement read could "pull the settlement value for all runners" and flag dead-heat cases (>1 `WINNER`). Claude assessed cost-benefit: Betfair API returns full market book by default, no extra API call cost. Generalised to three count fields populated from the same read — `dead_heat_count` (operator's original suggestion), plus `removed_runner_count` and `unexpected_state_count` as no-cost generalisations. Operator confirmed, also flagged sports-side dead-heat needs equivalent handling (AFL head-to-head ties — real and not rare). Logged as `architecture.md` §B.1.4 administrative cleanup carry-forward.

Round-by-round shape:

**Round 1 (scope read + narrowing).** Operator asked Claude to read `dr029/dr029_scope.md` §2.6 and narrowed scope at session open to Betfair-only canonical. Claude proposed five-section structure (framing, Betfair-as-canonical, state machine, edge cases, closure). Operator confirmed.

**Round 2 (Cluster 1 carry-in question).** Claude asked whether Cluster 1 surgical-fix carry-in (result-population in `runners.finish_position`) stayed in §2.6 scope under Betfair-only design. Operator explored: "We'd be able to reconcile Racing API and Betfair placings in the analytical layer anyway." Cluster 1 dropped from §2.6, moved to analytical-layer prep carry-forward.

**Round 3 (§1 framing drafted, written).** §1 written first (97 lines, 5 sub-sections). Plain-language framing, load-bearing inputs (§2.2, §2.4, §2.8, §2.9) and outputs (§2.7 `betfair_client` contract, settlement state machine, burst-review surfacing) named.

**Round 4 (§2 Betfair Win as canonical settlement source drafted, written).** §2 written (95 lines, 4 sub-sections). Five Betfair API fields named for `betfair_client` exposure. Three deliberate out-of-scope items: cadence/trigger model (§2.4), `betfair_client` outage handling (§2.7), soft-book balance reconciliation implementation (v3 build proper).

**Round 5 (§3 state machine initial draft + provisional question + auto-resolution reframe).** Claude drafted §3 with five-state machine; operator flagged 50/50 on `provisional`. After case-for-both review, operator confirmed keep. Operator then surfaced auto-resolution gap (settlement worker should keep reading) and past-settlement-window reframe (visibility surface, not state). Both folded in.

**Round 6 (manual-escalation question + answer).** Operator voiced 50/50 thought; Claude argued for adding the path. Operator confirmed.

**Round 7 (§3 written with all reframes folded in).** §3 written (183 lines, 6 sub-sections). State machine, transitions (including manual-escalation and post-settlement-void exception), past-settlement-window flag, two automated burst-review triggers, surfacing contract, "why provisional earns its keep" rationale.

**Round 8 (§4 edge cases drafted, full-market-book question + generalisation).** Claude proposed five edge cases (late-scratching identifier shift, dead heats, stewards' protests, abandoned race, Betfair API tier change). Operator surfaced full-market-book read question for dead heats; Claude generalised to three count fields. Operator flagged sports-side dead-heat administrative cleanup carry-forward. §4 written (169 lines, 7 sub-sections).

**Round 9 (§5 closure drafted, written).** §5 covers what §2.6 locks as load-bearing contract, what §2.6 explicitly does not specify, what §2.6 unblocks, what §2.6 carries forward (non-gating), what §2.6 does not unblock. Five sub-sections. §5 written (109 lines).

**Round 10 (close confirmation).** Operator: "As long as we catch the carry forward items at the pertinent work item, you can close out and prepare for next session."

## What was delivered

### 1. §2.6 brief drafted and locked end-to-end

Brief at `dr029/2_6_settlement_race/2_6_settlement_race.md`. 649 lines. Five sections, all locked.

**§1 Framing** (97 lines, 5 sub-sections). What §2.6 specifies (race-path settlement, Betfair-only canonical for v3 day-one). Why Betfair-only works (Betfair Win and soft-book settle on the same race result; soft-book balance reconciliation is the backstop). Revisit policy (locked for v3 day-one, fresh DR if operational divergence eventuates, no Racing API forward-pointer). Load-bearing inputs (§2.2 sports-path parallel, §2.4 Streaming spec for read mechanism, §2.8 bet record contract, §2.9 surface (c) feed). Load-bearing outputs (`betfair_client` settlement-read contract for §2.7, settlement state machine, burst-review surfacing contract).

**§2 Betfair Win as canonical settlement source** (95 lines, 4 sub-sections). What "canonical" means here (single authoritative input, no other source consulted). Two consequences: bet origin doesn't change settlement path; `betfair_selection_id` is canonical runner identity. Five Betfair API fields named for `betfair_client` exposure: market state (`OPEN`/`SUSPENDED`/`CLOSED`), market settlement state (`settledTime`), per-runner settlement status (`WINNER`/`LOSER`/`REMOVED`), market void status, per-runner void status. Settlement read described as five-step idempotent operation. Three deliberate out-of-scope items.

**§3 Settlement state machine** (183 lines, 6 sub-sections). Five states (`pending`, `settled_won`, `settled_lost`, `voided`, `provisional`). Transition rules covering: automated reads from `pending`, auto-resolution from `provisional` to terminal states, manual operator path via burst review, manual operator escalation from any non-`provisional` state, post-settlement-void exception path back from terminal states. Past-settlement-window flag specified as operational visibility surface (not a state) with 30-minute v3-day-one threshold for calibration. Two automated burst-review triggers (unexpected per-runner state, post-settlement market void) plus manual-escalation path. Burst-review surfacing contract names six data items including auto-resolution behaviour. "Why provisional earns its keep" rationale four-bullets.

**§4 Edge cases worth naming** (169 lines, 7 sub-sections). Late-scratching identifier shift (§2.9 §4.4 (b) feed). Dead heats with `dead_heat_count` field specification + sports-side equivalent administrative cleanup carry-forward. Stewards' protest upheld after Betfair settlement (canonical case for §3.4 condition 2). Abandoned race. Multi-runner state captures generalisation (`removed_runner_count` + `unexpected_state_count` from same full-market-book read). Betfair API tier change. Other cases that may emerge.

**§5 What §2.6 closes for DR-029, what's deferred** (109 lines, 5 sub-sections). What §2.6 locks as load-bearing contract (Betfair-only canonical, five-state machine, `betfair_client` settlement-read contract, four count/flag fields, burst-review surfacing contract). What §2.6 explicitly does not specify (cadence/trigger model, `betfair_client` operational concerns, soft-book balance reconciliation implementation). What §2.6 unblocks (§2.7, v3 build proper settlement worker, burst-review queue UI, operational-visibility layer). What §2.6 carries forward non-gating (sports-side dead-heat capture, past-settlement-window threshold calibration, settlement worker periodic verification cadence, operational experience surfacing new edge cases). What §2.6 does not unblock (§2.10 independent; DR-029 itself does not close on §2.6).

### 2. Strategic decisions locked

Five strategic decisions confirmed by operator and locked into the brief:

1. **Betfair-only canonical settlement source for v3 day-one.** Operator-driven scope narrowing at session open from the original two-source-agreement design. Single source, simpler state machine, no Racing API integration in settlement path. Soft-book balance reconciliation is the operational backstop for rare divergence cases.
2. **Provisional state earns its keep with auto-resolution + manual-escalation paths.** Operator was 50/50 at outset; confirmed keep after §3.5 laid out the rationale. Auto-resolution path from `provisional` back to terminal states means low-friction cases self-clear; manual-escalation path from any non-`provisional` state captures operator-side information v3 can't see.
3. **Past-settlement-window is a flag, not a state.** Operator caught the design issue: when Betfair itself hasn't settled, there's nothing for the operator to review. Long-waiters stay in `pending`; the flag is operational visibility surface (badge / count / filterable view) to bring stuck bets to operator attention. Worker keeps reading on normal cadence; auto-transitions when Betfair settles.
4. **Manual operator escalation supported as native state-machine transition.** From any non-`provisional` state → `provisional` on operator decision via burst-review action. Audit-trail entry records operator-supplied free-text reason. Protects against v3-build-proper failure mode of treating state machine as locked-against-escalation.
5. **Full-market-book read at settlement time captures three count fields at no extra cost.** `dead_heat_count`, `removed_runner_count`, `unexpected_state_count` populated from the same Betfair API call the settlement worker performs. `dead_heat_count` originated from operator's question about flagging multi-`WINNER` cases; generalised to the other two as no-cost additions. Sports-side `dead_heat_count` for AFL ties / NRL equivalents flagged as `architecture.md` §B.1.4 administrative cleanup.

### 3. Cluster 1 surgical-fix carry-in dropped from §2.6 scope

Per Session 34 §2.6 scope, Cluster 1 (result-population in `runners.finish_position` over 60-day live-capture window + `racing-metadata-backfill.service` rework) was carried into §2.6 to support the two-source-agreement design. Under Betfair-only canonical settlement, v3 doesn't read `runners.finish_position` for settlement; the field's analytical-layer value remains but no longer gates §2.6 close. Cluster 1 moves to analytical-layer prep carry-forward (non-gating).

### 4. Working-style adherence

Memory edit #16 ("strategic decisions surfaced; technical detail in the artefact") held throughout. Three operator-driven design decisions redirected §2.6 design substantively:

- **Round 1 scope narrowing (Betfair-only).** Operator's reasoning grounded in operational ground-truth ("Betfair must be an accurate canonical source... I can't see any instances where Betfair would deviate from the softbook"). Claude's response was to lay out the option (a) and (b) framing for revisit-policy and let operator pick — landed on (b) with soft hedge.
- **Round 5 auto-resolution + past-settlement-window reframe.** Operator caught two real design issues; Claude reframed both cleanly. Pattern repeats from Session 73's Round 5 reframe: when operator pushback is grounded in operational experience rather than scope/aesthetic preference, the reassessment is substantive.
- **Round 7 full-market-book read generalisation.** Operator's "is it possible to..." question on dead-heat detection was a precision-shaped design question, not a reframe. Claude's job was cost-benefit assessment + generalisation surface area. The three-field generalisation came from "the cost is genuinely tiny" framing — capturing more from the same API call costs nothing.

### 5. One filesystem tool slip caught and corrected

Round 3 (§1 write attempt): Claude used `bash_tool` to create the `2_6_settlement_race/` directory before writing §1. `write_file` then failed with `ENOENT` because `bash_tool` mkdir landed in the sandbox namespace, not the Mac filesystem (Cat 3 names this exact gotcha). Recovered immediately to `Desktop Commander:start_process` for both directory create and file write. No artefact corruption — caught at first write attempt before any committed state was affected. Pattern reinforces Cat 3's "Desktop Commander is the default filesystem and process tool for everything in this project" — when in doubt, the answer is start_process, not bash_tool.

### 6. §2.6 brief now load-bearing input for §2.7

§2.7 (API contract versioning) for `betfair_client` v1.0 contract is now writable per §5.3 — the settlement-read shape (five fields) is specified at the contract level. Combined with §2.9 §6.1 (surface (a) sports-line query, surface (b) `marketTime` read), `betfair_client` v1.0 contract has settlement-read + sports-line-query + scheduled-time-read all writable for §2.7.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021, DR-019 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (tight, ~20 minute gap from Session 73 close).
- **Cat 1 (V3 build picture conditional render)** — rendered at open since stream state moved (§2.9 → done, §2.6 → in flight, §2.8 carry-rule drop). To be updated at this close (§2.6 stream moves from `in flight` to `done`; §2.9 carry-rule one-session post-close drops).
- **Cat 1 (open-items delta)** — skipped silently at open (no movement in 20 min). Will fire at next session open if movement.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Round-by-round cadence with one strategic question per round. No paragraph-stacking, no over-recap.
- **Cat 1 (decision-maker framing)** — held. Each round led with the call or recommendation. The provisional-state question (Round 5) and manual-escalation question (Round 6) explicitly called out as 50/50 operator decisions; Claude provided the case-for analysis at the operator's request.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. When operator handed off route choice, Claude proceeded with the next section immediately.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders. `betfair_client`, `vps_client`, `capture.db`, `betfair_market_id`, `betfair_selection_id`, `dead_heat_count`, `removed_runner_count`, `unexpected_state_count`, `placement_time`, `settledTime` unwound on use.
- **Cat 1 (escalate to detail only when warranted)** — held. §3.5 "why provisional earns its keep" was an explicit operator-choice surface (case for keep + case for collapse) at operator's request; not delivered by default.
- **Cat 1 (line-break rendering for review content)** — held. All §2.6 brief draft sections delivered in fenced code blocks with hard line wraps.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. Mid-session re-anchor at 11:42 ACST (after §3 written, before §4) per Cat 2.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held with one slip caught. `bash_tool` mkdir attempt at Round 3 failed silently into sandbox; immediately recovered to `Desktop Commander:start_process`. No artefact corruption. Reinforces Cat 3 instruction.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python REPL work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; all §2.6 draft content written directly to canonical artefact during the session. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — applies. The §2.6 scope-narrowing at session open (operator-driven Betfair-only narrowing from the locked Session 27 two-source-agreement design) is flagged here as a substantive scope-narrowing event, not a structural-drift-of-an-existing-artefact event. The scope was narrowed in operator-Claude exchange before any artefact was written; the locked DR-029 §2.6 scope in `dr029/dr029_scope.md` is unchanged (the brief itself records the narrowing). If a fresh DR is wanted to formalise the narrowing as part of DR-029 close-out governance, that's an operator call for between-session work.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — minimal engagement. Betfair API behaviour referenced from prior probe + Streaming reference doc work; no fresh API surface investigation needed for §2.6 (the five-field surface is well-understood from §2.4 prior work).
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — n/a; all writes were single-target appends to a fresh file.
- **Cat 3 (write-file vs create_file namespace gotcha)** — applied via the Round 3 `bash_tool` mkdir slip recovery; reinforces "always verify post-write via read_file or list_directory."
- **Cat 4 (DR-027/028 invoked)** — named at open. DR-027 implicit throughout the integration-boundary framing. DR-028 not load-bearing this session.
- **Cat 4 (operational/analytical line discipline)** — engaged throughout. §1.1, §1.2, §2.1, §5.4 anchor on operational-line settlement reads (`betfair_client`) vs analytical-line data (`capture.db`). The Cluster 1 carry-in drop is a direct application of the discipline: `runners.finish_position` is analytical-line data; v3's settlement is operational-line read.
- **Cat 4 (Betfair-as-canonical-source extension)** — load-bearing this session. The Betfair-only narrowing extends "Betfair as canonical source" beyond identity (per §D12 / Session 42 architectural extension) to settlement state itself — every racing bet settles against the Betfair Win market regardless of bet origin.
- **Cat 5 (software questions are Claude's)** — held. Section structure, sub-section design, state machine state enumeration, transition rule enumeration, edge case enumeration, count-field generalisation — all Claude's calls (proposed for confirmation). Operator's three operational-ground-truth pushbacks (Round 1 Betfair-only narrowing, Round 5 auto-resolution + past-window reframe, Round 7 full-market-book read question) involved operational reality Claude does not have, redirecting Claude's software-question proposal to match operator reality. Cat 5 line held cleanly.
- **Cat 5 (operator working-style — memory edit #16)** — held throughout. Strategic questions one per round; technical detail in the artefact. The 50/50 decisions (provisional state in Round 5, manual escalation in Round 6) honoured the working-style preference for explicit case-for analysis on demand without diluting the artefact's technical substance.

## Open items in (carried forward + new)

New from Session 74:

- **§2.6 brief end-to-end** — **CLOSED Session 74.** All 5 sections locked. Brief at `dr029/2_6_settlement_race/2_6_settlement_race.md` (649 lines).
- **Sports-side dead-heat capture in `architecture.md` §B.1.4** — administrative cleanup carry-forward. AFL head-to-head ties, NRL equivalents need `dead_heat_count` capture identical to racing dead heats. Logged for between-session work or DR-029 close.
- **Past-settlement-window threshold calibration** — v3 day-one ships with 30 minutes from race finish; calibrate from operational experience. v3 operational parameter, not §2.6 amendment trigger.
- **Settlement worker periodic verification cadence** — §3.4 condition 2 (post-settlement market voids) requires terminal-state re-reads at some periodic cadence. v3 build proper operational tuning, not §2.6 spec.

Carry-forward (unchanged structure where applicable):

- **§2.6 settlement model — race path** — **CLOSED Session 74.**
- **§2.7 API contract versioning** — unfinished; two module contracts (`vps_client` and `betfair_client`). **Both still writable; `betfair_client` settlement-read shape now specified per §2.6 §5.1.** Recommended Session 75 primary candidate per Session 73's confirmed four-stream order.
- **§2.8 bet-schema reframing** — CLOSED Session 72. Carry post-close window expired Session 73.
- **§2.9 write-side bet-entry coherence** — CLOSED Session 73. Carry post-close window expires this close.
- **§2.10 external analytics scan** — substantially fed by probe; inventory writeup remaining. Independent of §2.6.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records. Reaffirmed throughout §2.6 (settlement extension). Continues as administrative cleanup (`architecture.md` §D12 sub-section update post-DR-029).
- **Complete cascade map** — parked. Best done post-DR-029.
- **CLV as analytical-layer signal** — built post-DR-029.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — operational design downstream. Now also feeds §2.6 burst-review queue UI (v3 build proper).
- **Cluster 1 surgical-fix carry-in (analytical-layer prep)** — `runners.finish_position` backfill + `racing-metadata-backfill.service` rework. **Dropped from §2.6 scope Session 74.** Now non-gating analytical-layer prep work — useful when analytical layer is being built post-DR-029.
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
- **EX_LADDER entitlement question** — operator-side homework. Informs §2.9 §4.4 (e) and §2.6 §4.6 (Betfair API tier change).
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
- **Claude-67 G3** — Racing API ↔ Betfair market identity reconciliation implicit. Now partly covered by §2.9 §4 (surface (c) is the visibility surface) — full reconciliation discipline for race/runner identity remains a Fix 5 concern.
- **Claude-67 G4** — `listCurrentOrders` filter parameter list not in captured reference.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC` betDelay confidence note.

## Open items out

Closed this session:

- **§2.6 §1 framing** — locked.
- **§2.6 §2 Betfair Win as canonical settlement source** — locked.
- **§2.6 §3 settlement state machine** — locked.
- **§2.6 §4 edge cases worth naming** — locked.
- **§2.6 §5 closure** — locked.
- **§2.6 brief end-to-end** — CLOSED Session 74.
- **Betfair-only canonical settlement source strategic question** — locked at session open (operator-driven scope narrowing).
- **Provisional state retention strategic question** — locked keep with auto-resolution + manual-escalation paths.
- **Past-settlement-window state-vs-flag strategic question** — locked flag (operational visibility surface, not state-machine entry).
- **Manual operator escalation strategic question** — locked add as native state-machine transition.
- **Full-market-book read three-field generalisation strategic question** — locked all three count fields (`dead_heat_count`, `removed_runner_count`, `unexpected_state_count`).
- **Cluster 1 surgical-fix carry-in scope question** — locked drop from §2.6 (move to analytical-layer prep carry-forward).
- **§2.9 carry-post-close window** — expires this close per `v3_build_picture.md` carry-rule.

## Session close state

- **Rebuild folder root:** 11 expected `.md` files plus `v3_build_picture.md` (12), `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present. **One new directory created this session:** `dr029/2_6_settlement_race/`.
- **`current_state.md`:** to be updated by close ritual to reflect Session 75 forward routing (§2.7 API contract versioning primary candidate per session-order proposal locked at Session 73 open and confirmed by §2.6 §5.3).
- **`v3_build_picture.md`:** **to be updated this close.** §2.6 stream moves from `in flight` to `done`. §2.7 stream moves from `unfinished` to `in flight` (Session 75 primary candidate). §2.9 (carry-rule one-session post-close) drops.
- **`standing_instructions.md`:** unchanged this session. No new instructions surfaced.
- **`dr029/2_6_settlement_race/2_6_settlement_race.md`:** **created this session.** 649 lines. Status: complete. All 5 sections locked.
- **`dr029/dr029_scope.md`:** unchanged this session. The §2.6 narrowing is recorded in the §2.6 brief itself; whether the scope doc gets a Session 74 amendment note is operator-side judgement (likely not needed — the brief is the authoritative locked artefact).
- **`architecture.md`:** unchanged this session. Sports-side dead-heat capture amendment to §B.1.4 logged as carry-forward.
- **`decisions.md`:** unchanged this session. No new DRs surfaced.
- **`sessions/`:** Session 74 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 74 opening prompt to be removed at close; Session 75 opening prompt to be written.
- **Project knowledge base:** unchanged; no operator-side actions required for Session 75 open.
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** *"As long as we catch the carry forward items at the pertinent work item, you can close out and prepare for next session."* — operator confirmation that all carry-forwards are captured (sports-side dead-heat for `architecture.md` §B.1.4, past-settlement-window threshold calibration, settlement worker periodic verification cadence, Cluster 1 analytical-layer prep) and close-out can proceed.

**Session 75 primary deliverable: §2.7 (API contract versioning) brief drafting.** Per the four-stream order proposed at Session 73 open and confirmed by operator (§2.9 → §2.6 → §2.7 → §2.10 → DR-029 close-out). §2.7 covers two module contracts (`vps_client` and `betfair_client`), both now substantially specified at the contract-shape level by §2.9 (surfaces (a), (b), (c)) and §2.6 (settlement-read five-field shape).

Sequence:

1. **First work:** read `dr029/dr029_scope.md` §2.7 for locked scope reminder; review §2.9 §6.1 (`vps_client` and `betfair_client` v1.0 contracts now writable) and §2.6 §5.1 (`betfair_client` settlement-read contract specification) for the §2.9 + §2.6 handoff.
2. **§2.7 framing** — what API contract versioning needs to specify across both module contracts: versioned endpoint pattern, schema-change discipline, deprecation policy, contract documentation, `vps_client` interface against locked `capture.db` contract, `betfair_client` interface against settlement-read + sports-line-query + `marketTime`-read shape.
3. **Section-by-section per Cat 1 default cadence** — likely cuts: framing, `vps_client` v1.0 contract, `betfair_client` v1.0 contract, schema-evolution policy, deprecation framework, what §2.7 closes.

**Alternative routing if operator prefers:** §2.10 (external analytics scan inventory writeup — independent of §2.6, §2.7, §2.9) is the only other writable Session 75 primary deliverable.

**Out of scope for Session 75:** §2.10 (until §2.7 closes if §2.7 is the chosen route); anything outside the chosen primary deliverable.

**Operator-side actions between sessions:**

1. **(Optional, low priority)** Investigate Betfair API membership tiers — informs EX_LADDER / SP-actual entitlement question and §2.6 §4.6 / §2.9 §4.4 (e) edge case (Betfair API tier change).
2. **(Optional)** Awaiting BetWatch response — no longer gating; informs future operational-soft-book DR.
3. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.
4. **(Optional)** Review §2.6 brief end-to-end at leisure (between-session work; not a Session 75 blocker).
5. **(Optional)** Review §2.9 brief end-to-end at leisure (between-session work; not a Session 75 blocker).
6. **(Optional)** Review §2.8 brief end-to-end at leisure (carry-forward from Session 72).

## Close-out notes

Single morning sitting, ~1h 33m wall-clock — comparable to Session 73 (~1h 27m) for similar fresh-brief drafting work. Session shape was healthy throughout; no split triggers, no fatigue signals.

Three working-style moments worth holding onto:

- **Round 1 operator-driven scope narrowing.** Operator narrowed §2.6 from two-source-agreement to Betfair-only canonical at session open, before any drafting. Pattern: when operator's strategic call simplifies design substantially, lean into the simplification rather than preserving the original scope's complexity. The narrowing also dropped Cluster 1 surgical-fix carry-in cleanly — Cluster 1 was load-bearing only under the two-source design.

- **Round 5 auto-resolution + past-settlement-window reframe.** Operator caught two real design issues in the initial §3 draft: (a) settlement worker should keep reading once a bet enters `provisional`; (b) past-settlement-window for Betfair-not-yet-settled cases is noise, not signal. Pattern: when operator pushback identifies a noise-vs-signal distinction, the reassessment is structural — past-window stops being a state-machine trigger and becomes a visibility flag, which is a cleaner architecture.

- **Round 7 full-market-book read generalisation.** Operator's "is it possible to..." question on dead-heat detection generalised to three count fields at no extra API cost. Pattern: when a precision-shaped question can be generalised cheaply, the generalisation should happen at the design layer rather than the implementation layer — capturing the data at settlement is much cheaper than reconstructing it later. The sports-side dead-heat administrative-cleanup carry-forward came from operator's domain knowledge (AFL ties are real and not rare); naming it at design time prevents v3-build-proper drift.

§2.6 brief is now load-bearing input for §2.7 (`betfair_client` settlement-read shape specified). Session 75 picks up §2.7 API contract versioning across both module contracts.
