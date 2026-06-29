# Session 73

**Title:** §2.9 (write-side bet-entry coherence) brief drafted and locked end-to-end. Six sections written: §1 framing, §2 surface (a) sports-line specification, §3 surface (b) placement-time sanity check, §4 surface (c) identifier-resolution sanity check, §5 excluded scope, §6 closure. Brief at 577 lines. §2.9 reframed from atomicity-and-transactions framing to its locked narrow-scope shape (three sanity-check surfaces protecting bet-record identifier resolution) after Claude initial pre-read mis-anchored on cascade atomicity instead of the locked DR-029 §2.9 scope. Two strategic decisions locked: store both operator-typed line and resolved Betfair market_id on every sports bet record (Option A, cheap-to-capture); 30-minute placement-time padding either side of scheduled start, warning-only and never blocking.
**Opened:** 2026-05-04 08:24 ACST
**Closed:** 2026-05-04 09:51 ACST
**Wall-clock:** ~1h 27m substantive single sitting. Same-workday open relative to Session 72's 08:06 ACST close (~18 minute gap).
**Tool routing:** Claude Chat. No Code routing.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline — load-bearing for §4.5), DR-021 (timestamp anchoring), DR-019 (derived state on read — load-bearing for §4 connection to §2.8 §8).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 08:24 ACST`.
Mid-session anchor (after §3 written): same command → `2026-05-04 09:33 ACST` (~69 min into session).
Close: same command → `2026-05-04 09:51 ACST`.

Same-workday open relative to Session 72's 08:06 ACST close. ~18 minute gap. Single morning sitting, immediate continuation.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 12 `.md` files + `openapi.json` + `external_api_resources.md` + `.DS_Store` + `v3_build_picture.md`. All directories present.
- `.close_out_backups/` contained `SESSION_73_opening_prompt.md` only (Session 72 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 08:06 ACST` matched Session 72 close; `sessions/SESSION_72.md` present (209 lines); `v3_build_picture.md` last-updated `2026-05-04 08:06 ACST` matched Session 72's §2.8 stream-completion update.
- Same-workday recap delivered (tight: Session 72 closed §2.8 brief end-to-end with two strategic calls — universal-amendable model and CLV reframed as analytical-layer signal; Session 73 picks up §2.9 as primary deliverable per Session 72 forward routing).
- V3 build picture: rendered at open since stream state moved (§2.8 → done) and since operator's first-task request (project overview + proposed order of work) made the inline render genuinely useful rather than ritual noise.
- Open-items delta: rendered as part of the project overview, since operator asked for state-of-project framing.

## Session shape

Session 73 was a **brief-drafting session** — drafting §2.9 (write-side bet-entry coherence) from scratch per Session 72 forward routing. Six sections landed across nine drafting rounds: §1 framing, §2 sports-line specification (three sub-sections covering branching cases), §3 placement-time sanity check (five sub-sections), §4 identifier-resolution sanity check (five sub-sections including six edge cases), §5 excluded scope (five sub-sections), §6 closure (four sub-sections).

The session opened with a substantial scope-correction pivot. Claude's pre-read of §2.9 framed it on transactional atomicity and cascade-write coherence — substantive concerns, but not what the locked DR-029 §2.9 scope actually specifies. After reading `dr029/dr029_scope.md` §2.9 directly, Claude reframed §2.9 as the integration-boundary contract addition (three sanity-check surfaces) per the locked scope. The corrected framing held throughout the brief. The Claude pre-read miss is itself a Cat 5 software-question pattern: when scope is ambiguous, read the locked scope doc rather than reasoning from memory of adjacent work.

Two operator-driven reframes redirected sub-section design:

**Round 4 (surface (a) reframe).** Claude's initial draft of §2.3 (no-match and edge cases) had the strict reading: "do not silently write a record without a matching market_id, no record without a confirmed market_id at commit." Operator pushed back with operational reality: "I lay a softbook bet which has been accepted but then the market suspends, that means I'm not able to log that softbook bet because there's no Betfair market that is available. I tend to think that I should still be able to log it." The strict reading was wrong — the soft-book bet is the load-bearing reality; v3 records what happened. Reframed §2 around three rare cases (market not yet open, transient API failure, fixture removed) producing a structured `market_id_resolution_pending` flag with surface (c) handling resolution later. Operator-Claude exchange also led to empirical web-search verification that Betfair `market_id` remains available across SUSPENDED state — meaning suspension is not a no-market-id case at all, narrowing the genuinely-pending universe further.

**Round 5–7 (surface (b) reframe).** Operator caught two issues with Claude's initial §3 draft: (a) the "manual timestamp entry" framing was wrong — v3 auto-captures, manual entry is the rare case; (b) the strict pre-scheduled-start rule failed real workflow because race jumps run late and late-second soft-book bets get logged after actual jump. Reframed §3 around 30-minute padding either side of scheduled start (operator's call: symmetric 30/30 minutes, value of the warning is high enough to justify), warning-only never blocking. Empirical question on whether Betfair `marketTime` updates on race delays carried forward as non-gating clarification (web search inconclusive but suggests it does not; design works either way).

Round-by-round shape:

**Round 1 (project overview at session open).** Operator's first message asked for plain-language overview of project state and proposed order of remaining DR-029 work. Claude rendered v3 build picture inline + open-items delta + four-stream order proposal (§2.9 next, then §2.6, then §2.7, then §2.10, then DR-029 close-out). Operator confirmed.

**Round 2 (project progress estimate + §2.9 framing).** Operator asked for percentage-complete estimate (15-20% overall, 75% through DR-029 specifically). Claude proposed initial seven-section structure for §2.9 framed on atomicity and transactions. Operator confirmed framing direction.

**Round 3 (§2.9 scope correction).** Claude read `dr029/dr029_scope.md` §2.9 before drafting framing. Discovered the locked scope is much narrower than the pre-read framing — three specific sanity-check surfaces, not transactional atomicity. Reframed structure to six sections: framing, three surfaces, excluded scope, closure. Operator confirmed.

**Round 4 (§1 framing drafted, written; §2 surface (a) initial draft + reframe via operator).** §1 written first (45 lines). §2 drafted with strict no-record-without-market_id reading; operator surfaced the suspended-market log-bet reality. Claude web-search-verified that Betfair `market_id` remains available across SUSPENDED state; reframed §2 to three rare-case path with `market_id_resolution_pending` flag. §2 written (105 lines including §2.1, §2.2 standard flow, §2.3 cases where market_id resolves later).

**Round 5 (§3 placement-time framing + operator reframe).** Claude initial framing assumed manual timestamp entry. Operator caught: v3 auto-captures, manual is edge case. Operator also caught strict pre-jump rule failure mode (late jumps, late-second soft-book log). Claude proposed asymmetric padding (10 racing / 30 sports); operator overrode to 30/30 symmetric.

**Round 6 (`marketTime` empirical question).** Claude flagged whether Betfair `marketTime` updates on race delays as empirical gap. Web search via developer forum and third-party trading platforms suggests `marketTime` reflects originally-scheduled start and does not update on delays — but unverified against live observation. Folded into Fix 4 cadence brief drafting; design works either way.

**Round 7 (§3 written).** §3 drafted in plain-language layperson style after operator requested explicit plain-language explanation. Five sub-sections: §3.1 what surface does (auto-capture default), §3.2 plausibility window (30/30 racing/sports symmetric, 14 days lower bound), §3.3 behaviour outside window (warning only, never blocking), §3.4 why this matters downstream, §3.5 empirical clarification carried forward. §3 written (108 lines).

**Round 8 (§4 surface (c) drafted with edge-case sub-section).** Claude proposed asymmetric 24h racing / 6h sports escalation thresholds; operator overrode to 12h symmetric and asked Claude to think through unnamed edge cases. Six edge cases surfaced (Betfair market replacement, late-scratching identifier shift, cross-code mismatch, date-boundary edge, Betfair tier change, manual capture.db correction) and added as §4.4 reference list per operator's "document for visibility, design safety measures only when they eventuate" framing. §4 written (149 lines, 5 sub-sections).

**Round 9 (§5 excluded scope drafted, operator requested plain-language summary).** §5 written (92 lines) naming four excluded items: transactional atomicity, cascade-write coherence, integrity-layer flag-queue UI, free bet ledger consumption-event atomicity. Operator requested sharp dot-point plain-language summary before confirming. Confirmed; written.

**Round 10 (§6 closure drafted, operator requested whole-brief summary).** §6ed drafted with four sub-sections: what §2.9 unblocks, what lands as load-bearing contract, carry-forward items, what §2.9 does not unblock. Operator requested three-minute summary of whole document; Claude delivered. Operator confirmed full brief locked. §6 written (84 lines).

**Round 11 (close confirmation).** Operator: "Confirmed. Please finalise this and then, unless there's anything else, close out and prepare for next session."

## What was delivered

### 1. §2.9 brief drafted and locked end-to-end

Brief at `dr029/2_9_write_side/2_9_write_side.md`. 577 lines. Six sections, all locked.

**§1 Framing** (45 lines). §2.9 as integration-boundary contract addition for the leaner bet schema. Three sanity-check surfaces protect identifier resolution. Load-bearing inputs (§2.8 bet record contract, §2.2 Betfair-direct sports operational layer, §2.4 Betfair Streaming spec) and load-bearing output (§2.7 API contract versioning) named. Scope deliberately narrow per locked DR-029 §2.9 — atomicity / cascade-coherence work explicitly outside scope.

**§2 Surface (a) — sports line specification at bet entry** (~105 lines). Three sub-sections. §2.1 what the surface is (operational/analytical-line discipline meets soft-book typed-price path; both operator-typed line and resolved Betfair market_id stored per Option A). §2.2 standard log-time flow (five-step: select fixture, type line, query Betfair variants, pick matching market_id, commit). §2.3 cases where market_id resolves later (three rare cases producing structured `market_id_resolution_pending` flag with reason). Locked: market state at query time (OPEN/SUSPENDED/CLOSED) does not affect flow — Betfair `market_id` is stable across full lifecycle, empirically confirmed via Streaming reference doc.

**§3 Surface (b) — placement-time sanity check** (~108 lines). Five sub-sections. §3.1 what the surface does (auto-capture default, manual entry rare). §3.2 plausibility window (30 minutes either side scheduled start for both racing and sports — operator override of asymmetric proposal; 14 days lower bound). §3.3 behaviour outside window (warning only, never blocking; operator timestamp authoritative). §3.4 why this matters (cycle attribution, settlement matching, CLV reconstruction all fail silently on bad timestamp). §3.5 empirical clarification carried forward (`marketTime` mutability on race delays — folded into Fix 4 brief).

**§4 Surface (c) — identifier-resolution sanity check** (~149 lines). Five sub-sections. §4.1 what the surface does (passive boundary check at first analytical-line read, capture.db ingestion-fault surface). §4.2 resolution-failure handling (passive flag + retry initially, escalate to operator-facing review at 12 hours from `placement_time` — operator override of asymmetric 24h/6h proposal). §4.3 connection to surface (a) `market_id_resolution_pending` (surface (c) is natural recovery path). §4.4 six edge cases worth naming (Betfair-side market replacement, late-scratching identifier shift, cross-code mismatch, date-boundary edge, Betfair tier change, manual capture.db correction — documented for burst-review reference, mitigation only if any eventuate). §4.5 what this surface does not do (active write-time validation against analytical line — DR-028 boundary discipline named explicitly).

**§5 What §2.9 does not do** (~92 lines). Five sub-sections. Names four excluded items with forward pointers to v3 build proper phases: §5.1 transactional atomicity across multi-record writes, §5.2 cascade-write coherence under §2.8 §9 amendment discipline, §5.3 integrity-layer flag surface for ambiguous cascades, §5.4 free bet ledger consumption-event atomicity. §5.5 scope discipline summary names the pattern: §2.9 is contract layer, v3 build proper is implementation layer.

**§6 What §2.9 closes for DR-029** (~84 lines). Four sub-sections parallel to §2.8 §10 shape. §6.1 what §2.9 unblocks (`vps_client` and `betfair_client` v1.0 contracts for §2.7; surface (c) feed into §2.6 race-path settlement). §6.2 what lands as load-bearing contract (integration-boundary contract, soft-book sports-line resolution contract, placement_time plausibility contract). §6.3 carry-forward items not gating (`marketTime` mutability question, four §5 excluded items, six §4.4 edge cases). §6.4 what §2.9 does not unblock (§2.10 independent; §2.6 has its own scope; DR-029 itself does not close on §2.9).

### 2. Strategic decisions locked

Three strategic decisions confirmed by operator and locked into the brief:

1. **Option A on operator-typed-line storage.** Both operator-typed line (e.g. "-6.5") and resolved Betfair market_id are stored on every sports bet record. Audit-trail useful, cheap to capture per §2.8 principle, disambiguates edge cases where typed line and resolved market shift do not exactly align.
2. **30-minute symmetric padding for placement-time window.** Operator override of asymmetric 10-min/30-min proposal. Symmetry chosen because the warning is a single-click acknowledgement, false-positive cost is low, and value of catching obvious errors is high enough to justify symmetric coverage.
3. **12-hour symmetric escalation window for surface (c) resolution failures.** Operator override of asymmetric 24h/6h proposal. Operator's reasoning held: threshold isn't measuring normal ingestion lag, it's measuring gap duration before operator attention is warranted. 12h covers both racing and sports cleanly.

### 3. Working-style adherence

Memory edit #16 ("strategic decisions surfaced; technical detail in the artefact") held throughout. Three operator-driven reframes redirected §2.9 design substantively:

- **§2 reframe (no-record-without-market_id → record-with-pending-flag).** Operator's "I lay a softbook bet, then market suspends, I should still be able to log it" was load-bearing operational ground-truth; Claude's strict reading was wrong on first pass. Empirical web-search verification (Betfair `market_id` stable across SUSPENDED) further narrowed the genuinely-pending universe.
- **§3 reframe (manual-timestamp-entry → auto-capture-default; pre-jump-strict → 30-min-padded).** Operator caught both errors; Claude reassessed both cleanly.
- **§4 framing on edge cases (claude-proposed two → operator-asked-for-comprehensive-list → six landed).** Operator's "document for visibility, design safety measures only when eventuate" framing locked into §4.4 explicitly.

The first reframe (§2) was the most load-bearing. Pattern worth holding onto: when operator's pushback is grounded in operational experience rather than scope or aesthetic preference, the reassessment should be substantive, not cosmetic.

### 4. Web search engaged

Two web searches engaged this session for empirical verification:

- **Round 4 (Betfair market_id availability across SUSPENDED).** Captured locally-stored Streaming reference confirmed `market_id` is stable across full market lifecycle (OPEN → SUSPENDED → CLOSED). Tightened §2.3 case-list significantly.
- **Round 6 (`marketTime` mutability on race delays).** Inconclusive — third-party Betfair-trading-platform forum suggests `marketTime` reflects originally-scheduled start and does not update on delays, but unverified against live observation. Folded into Fix 4 brief drafting; §3 design works either way.

### 5. §2.9 brief now load-bearing input for §2.7 and feeds §2.6

§2.7 (API contract versioning) on `vps_client` and `betfair_client` is now writable per §2.9 §6.1. §2.6 (settlement model — race path) is fed by surface (c)'s late-scratching identifier shift edge case (§4.4 (b)).

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021, DR-019 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (tight, ~18 minute gap from Session 72 close).
- **Cat 1 (V3 build picture conditional render)** — rendered at open since stream state moved (§2.8 → done) and operator's first task request made it useful. To be updated at this close (§2.9 stream moves from `in flight` to `done`; §2.8 carry-rule one-session post-close drops).
- **Cat 1 (open-items delta)** — rendered as part of project overview at operator's request (overview was first task).
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Round-by-round cadence with one strategic question per round. Operator twice requested explicit plain-language framing (Round 5 §3, Round 9 §5 summary, Round 10 whole-brief summary); Claude delivered all three at appropriate brevity.
- **Cat 1 (decision-maker framing)** — held. Each round led with the call or recommendation.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. When operator handed off route choice ("everything looks good"), Claude proceeded with the next section immediately rather than re-litigating.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders. `betfair_client`, `vps_client`, `capture.db`, `marketTime`, `market_id`, `market_id_resolution_pending` unwound on use.
- **Cat 1 (escalate to detail only when warranted)** — held. Round 5 plain-language explanation of §3, Round 6 plain-language `marketTime` empirical writeup, Round 9 §5 plain-language summary, Round 10 whole-brief summary all delivered at appropriate depth without escalating beyond operator request.
- **Cat 1 (line-break rendering for review content)** — held. All §2.9 brief draft sections delivered in fenced code blocks with hard line wraps.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. Mid-session re-anchor at 09:33 ACST (after §3 written) per Cat 2 multi-day session rule pattern.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held. All file operations via `Desktop Commander:write_file` (six append operations to `2_9_write_side.md`), `Desktop Commander:read_file`, `Desktop Commander:start_process` (verification, scope reads, anchor commands, `mkdir`). One bash_tool call early in session failed with "no such file" per the namespace gotcha; recovered immediately to `Desktop Commander:start_process`.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python REPL work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; all §2.9 draft content written directly to canonical artefact during the session. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — applies. The §2.9 scope-correction pivot in Round 3 (Claude's pre-read mis-anchored on transactional atomicity; reframed to locked scope after reading `dr029/dr029_scope.md`) is flagged here as a substantive Round-1-vs-locked-scope reframing event. Not a structural-drift-of-an-existing-artefact event (no renumbering, no schema shift, no file split) — it's a Claude-framing-correction event before any artefact was written. Worth flagging because the pre-read pattern is the worth-noting lesson: when scope is ambiguous, read the locked scope doc rather than reasoning from memory of adjacent work.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — engaged. `external_api_resources.md` consulted for Streaming reference doc location; `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` queried via grep for Betfair market lifecycle behaviour (Round 4) and `marketTime` semantics (Round 6).
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — n/a; all writes were single-target appends to a fresh file.
- **Cat 3 (web search for external context)** — engaged twice. Round 4 verified Betfair `market_id` stability across SUSPENDED. Round 6 attempted `marketTime` mutability verification — inconclusive but folded into Fix 4 carry-forward.
- **Cat 4 (DR-027/028 invoked)** — named at open. DR-028 invoked load-bearing in §4.5 (passive sanity check rationale). DR-027 implicit throughout the integration-boundary framing.
- **Cat 4 (operational/analytical line discipline)** — engaged throughout. §1, §2.1, §4.1, §6.2 all anchor on operational vs analytical line distinction. The §2.9 framing itself is the integration-boundary contract between the two lines.
- **Cat 4 (Betfair-as-canonical-source extension)** — load-bearing this session. The §2.9 brief assumes the Session 42 architectural extension as locked (§2.8 §10.2 baseline). All bet records — racing or sports — carry Betfair canonical identifiers as the join key.
- **Cat 5 (software questions are Claude's)** — held. Section structure proposals, sub-section design, three rare-case enumeration in §2.3, six edge-case enumeration in §4.4, four excluded-item enumeration in §5 — all Claude's calls (proposed for confirmation). Operator's three reframes (§2 strict→pending, §3 manual→auto + strict→padded, padding values 10/30→30/30, escalation 24/6→12/12) all involved operational ground-truth that Claude does not have, redirecting Claude's software-question proposal to match operator reality. Cat 5 line held cleanly.
- **Cat 5 (operator working-style — memory edit #16)** — held throughout. Strategic questions one per round; technical detail in the artefact. Operator-requested plain-language summaries (Round 5, Round 9, Round 10) honoured the working-style preference for explicit plain-language framing on demand without diluting the artefact's technical substance.

## Open items in (carried forward + new)

New from Session 73:

- **§2.9 brief end-to-end** — **CLOSED Session 73.** All 6 sections locked. Brief at `dr029/2_9_write_side/2_9_write_side.md` (577 lines).
- **`marketTime` mutability empirical question** (not gating) — whether Betfair `marketTime` field updates on race delays. Folded into Fix 4 cadence brief drafting per §2.9 §3.5.
- **§2.9 §4.4 six edge cases** (documented for burst-review reference, no mitigation built) — Betfair market replacement, late-scratching identifier shift, cross-code identifier mismatch, time-zone / date-boundary edge, Betfair API tier change, manual data correction in `capture.db`.

Carry-forward (unchanged structure):

- **§2.6 settlement model — race path** — unfinished. **Recommended Session 74 primary candidate** per session order proposed and confirmed at session start.
- **§2.7 API contract versioning** — unfinished; two module contracts (`vps_client` and `betfair_client`). **Both now writable per §2.9 §6.1** — §2.9 surfaces (a), (b), (c) feed v1.0 contract specifications.
- **§2.8 bet-schema reframing** — CLOSED Session 72. Carry post-close window expires this close per `v3_build_picture.md` carry-rule.
- **§2.9 write-side bet-entry coherence** — **CLOSED Session 73.**
- **§2.10 external analytics scan** — substantially fed by probe; inventory writeup remaining. Independent of §2.9.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records. **Locked load-bearing in §2.8 §10.2 and reaffirmed throughout §2.9.** Continues as administrative cleanup (`architecture.md` §D12 sub-section update post-DR-029).
- **Complete cascade map** — parked. Best done post-DR-029. Now also feeds §5.2 forward pointer (cascade-write coherence in v3 build proper).
- **CLV as analytical-layer signal** — built post-DR-029.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — operational design downstream. Now feeds §5.3 forward pointer (integrity-layer flag surface in v3 build proper).
- **Fix 4 (Racing API cadence design)** — non-gating. **Now also includes `marketTime` mutability empirical question per §2.9 §3.5.**
- **Fix 5 (venue harmonisation)** — non-gating.
- **Fix 9 (Racing API re-fetch)** — non-gating.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — non-gating.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — Fix 8 report §8.5 recommendation.
- **Session numbering slip in probe brief** — cosmetic.
- **EX_LADDER entitlement question** — operator-side homework. Now also informs §4.4 edge case (e) (Betfair API tier change).
- **Drift-check methodology gap** — substrate from Session 64 carry-forward.
- **`bethub-analytical` project awaiting activation** — operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** — parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — non-gating.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — substrate input for analytical scan.
- **BetWatch contacted re: API service and book coverage** — awaiting response. No longer gating per Session 69.
- **Betfair API membership tiers — investigate.** Operator-side homework.
- **PASSIVE bet-delay model handling** — flagged in §2.4 §15.4 as v3.1+ capability.
- **Three pieces of named debt being carried into v3 build** — substrate for DR-029 close-out governance paragraph (no test coverage, no migration framework, monolithic orchestrator file).

Gaps from earlier reviews logged for awareness:

- **Claude-67 G1** — AU-specific session expiry not on disk.
- **Claude-67 G2** — `listCurrencyRates` API surface silent in captured reference.
- **Claude-67 G3** — Racing API ↔ Betfair market identity reconciliation implicit. Now partly covered by §2.9 §4 (surface (c) is the visibility surface) — full reconciliation discipline for race/runner identity remains a Fix 5 concern.
- **Claude-67 G4** — `listCurrentOrders` filter parameter list not in captured reference.
- **Fresh-Claude E1** — `PASSIVE` vs `DYNAMIC` betDelay confidence note.

## Open items out

Closed this session:

- **§2.9 §1 framing** — locked.
- **§2.9 §2 surface (a) sports-line specification** — locked.
- **§2.9 §3 surface (b) placement-time sanity check** — locked.
- **§2.9 §4 surface (c) identifier-resolution sanity check** — locked.
- **§2.9 §5 excluded scope** — locked.
- **§2.9 §6 closure** — locked.
- **§2.9 brief end-to-end** — CLOSED Session 73.
- **Operator-typed-line storage strategic question** — locked Option A (store both typed line and resolved Betfair market_id).
- **Placement-time padding strategic question** — locked symmetric 30 minutes either side scheduled start.
- **Surface (c) escalation threshold strategic question** — locked symmetric 12 hours from `placement_time`.
- **§2.9 §4.4 edge-case enumeration** — six edge cases documented for burst-review reference per operator's "document for visibility, mitigate when eventuate" framing.

## Session close state

- **Rebuild folder root:** 12 `.md` files + `openapi.json` + `external_api_resources.md` + `.DS_Store` + `v3_build_picture.md`. All directories present. **One new directory created this session:** `dr029/2_9_write_side/`.
- **`current_state.md`:** to be updated by close ritual to reflect Session 74 forward routing (§2.6 race-path settlement primary candidate per session-order proposal locked at Session 73 open).
- **`v3_build_picture.md`:** **to be updated this close.** §2.9 stream moves from `in flight` to `done`. §2.6 stream moves from `unfinished` to `in flight` (Session 74 primary candidate). §2.8 (carry-rule one-session post-close) drops.
- **`standing_instructions.md`:** unchanged this session. No new instructions surfaced; existing instructions held throughout.
- **`dr029/2_9_write_side/2_9_write_side.md`:** **created this session.** 577 lines. Status: complete. All 6 sections locked.
- **`dr029/dr029_scope.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session. Post-DR-029 §D12 sub-section update remains carry-forward administrative cleanup.
- **`decisions.md`:** unchanged this session. No new DRs surfaced.
- **`sessions/`:** Session 73 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 73 opening prompt to be removed at close; Session 74 opening prompt to be written.
- **Project knowledge base:** unchanged; no operator-side actions required for Session 74 open.
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** *"Confirmed. Please finalise this and then, unless there's anything else, close out and prepare for next session."* in response to Claude's notice that §2.9 brief is locked end-to-end and no decisions are pending.

**Session 74 primary deliverable: §2.6 (settlement model — race path) brief drafting.** Per the four-stream order proposed at Session 73 open and confirmed by operator: §2.9 (this session) → §2.6 → §2.7 → §2.10 → DR-029 close-out. §2.6's race-path specification is its own work; §2.9 §6.1 names the surface (c) feed into §2.6 for late-scratching handling, but §2.6 is independent of §2.9 substantively.

Sequence:

1. **First work:** read `dr029/dr029_scope.md` §2.6 for locked scope reminder; review §2.9 §4.4 (b) (late-scratching identifier shift edge case) and §6.1 (surface (c) feed into §2.6) for the §2.9-side handoff. Settlement model sports-path is already specified per §2.2; race-path is the gap.
2. **§2.6 framing** — what the race-path settlement model needs to specify: VPS race-result via `vps_client` against `capture.db` as canonical source; two-source agreement (Betfair Win + Racing API) → `finalised`; single high-confidence source → `finalised`; low-confidence single-source or divergence → `provisional` surfaced to burst review.
3. **Section-by-section per Cat 1 default cadence** — race-path canonical source, two-source agreement discipline, finalised vs provisional state machine, burst review surfacing, late-scratching handling per §2.9 §4.4 (b), what §2.6 closes.

**Alternative routing if operator prefers:** §2.7 (API contract versioning — both `vps_client` and `betfair_client` contracts now writable) or §2.10 (external analytics scan inventory writeup — independent of §2.9) are also writable as Session 74 primary deliverables.

**Out of scope for Session 74:** §2.7, §2.10 (until §2.6 closes if §2.6 is the chosen route); anything outside the chosen primary deliverable.

**Operator-side actions between sessions:**

1. **(Optional, low priority)** Investigate Betfair API membership tiers — informs EX_LADDER / SP-actual entitlement question and §2.9 §4.4 edge case (e) (Betfair API tier change).
2. **(Optional)** Awaiting BetWatch response — no longer gating; informs future operational-soft-book DR.
3. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.
4. **(Optional)** Review §2.9 brief end-to-end at leisure (between-session work; not a Session 74 blocker).
5. **(Optional)** Review §2.8 brief end-to-end at leisure (carry-forward from Session 72).

## Close-out notes

Single morning sitting, ~1h 27m wall-clock — longer than Session 72 (21 min) and Session 71 (27 min) because §2.9 was a fresh-brief drafting session vs §2.8's three-section completion in Session 72 and §2.8's mid-section drafting in Session 71. Session shape was healthy throughout; no split triggers, no fatigue signals.

Three working-style moments worth holding onto:

- **Round 3 scope-correction pivot.** Claude's pre-read of §2.9 framed it on transactional atomicity and cascade-write coherence — substantive concerns but not the locked DR-029 §2.9 scope. Caught by reading `dr029/dr029_scope.md` §2.9 directly before drafting framing. Pattern: when scope is ambiguous, read the locked scope doc rather than reasoning from memory of adjacent work. The reframe was clean (no artefact written before correction); the broader lesson is to do the locked-scope read upfront on any fresh brief, not after framing has been proposed.

- **Round 4 surface (a) reframe (operator v2-experience override).** Claude's strict no-record-without-market_id reading was wrong on the operational reality. Operator's "I lay a softbook bet, then market suspends, I should still be able to log it" was load-bearing operational ground-truth. Pattern: when operator's pushback is grounded in operational experience rather than scope or aesthetic preference, the reassessment should be substantive, not cosmetic. Same pattern as Session 72's Round 5 reconciliation-event-scope reversal.

- **Round 7-8 operator-driven simplifications.** Operator overrode three of Claude's asymmetric proposals (10/30 racing/sports padding → 30/30; 24h/6h escalation → 12h/12h). Operator's reasoning held in each case: warning value high enough to justify symmetric coverage; threshold isn't measuring normal lag but gap duration before attention. Pattern: Claude's instinct toward asymmetric defaults often over-engineers vs operator's instinct toward simpler symmetric defaults. Worth holding onto for future cadence/threshold-design work.

§2.9 brief is now load-bearing input for §2.7 (both module contracts) and feeds §2.6 (late-scratching handling). Session 74 picks up §2.6 race-path settlement.
