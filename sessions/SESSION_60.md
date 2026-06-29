# Session 60

**Title:** §2.4 Fix 4 brief drafting — Sections 1–11 of 18 locked covering front matter, framing, module shape, Streaming connection, authentication, market subscription, order subscription, message handling, reconnection, REST placement, REST order state reads. Three Betfair Reference Guide pages captured to `reference_guide/` (placeOrders, cancelOrders, replaceOrders) per Path A on-demand fetch. Close at Section 11 on context-budget split-trigger; Section 12 (rate-limits) onwards defers to Session 61.
**Opened:** 2026-05-03 14:35 ACST
**Closed:** 2026-05-03 16:57 ACST
**Wall-clock:** 2h 22m (single sitting, single workday — same-workday continuation of Session 59's 14:29 close, 6 min gap).
**Tool routing:** Claude Chat. No Code routing — section-by-section brief drafting + on-demand documentation fetch + persistence + pointer-doc edit.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-03 14:35 ACST`.
Close: same command → `2026-05-03 16:57 ACST`.

Sunday afternoon, same-workday continuation of Session 59's 14:29 close (6 min gap; same-workday per Cat 1).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- 13 `.md` files at rebuild root + `openapi.json` (matched expected count from Session 59 close).
- All directories present.
- `.close_out_backups/` contained `SESSION_60_opening_prompt.md` only (Session 59 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-03 14:29 ACST` matched Session 59 close; `sessions/SESSION_59.md` present and non-empty (143 lines); `v3_build_picture.md` last-updated `2026-05-03 13:57 ACST` matched (Session 59 was documentation-only, no stream state moved).
- Governing DRs named in orientation summary.
- Same-workday calendar-calibrated recap delivered (tight, 6 min gap).
- V3 build picture: skipped silently per condition (no stream movement Session 59).
- Open-items delta: skipped silently per condition (no movement in 6 min gap).

## Session shape

Session 60 was a **section-by-section brief-drafting session** with two material expansions of the working surface mid-session: (a) confirming Path A on-demand fetch is viable now that the Confluence anonymous-access wall has loosened, and (b) confirming `betfair_client` scope covers Streaming pricing reads + REST placement + REST order state reads (one module, one integration point per DR-028).

Session opened against Session 59's deferred Fix 4 brief drafting; standard session-open ritual, governing DRs named, drift-check passed. Operator flagged the standing-instructions re-upload from Session 58 close was already done — cleared from open items.

The first substantive move was a documentation audit before drafting began: confirmed the Stream API canonical reference (986 lines, captured Session 59) covers the Streaming side; the Reference Guide (REST surface) covers the placement and order-state side. Operator uploaded a partial Betting API endpoint summary PDF; operator confirmed the upload wasn't sufficient for full brief drafting. Path A vs Path B vs hybrid options surfaced; Path A confirmed (on-demand fetch during drafting, no bulk capture upfront).

A web_fetch test against `listMarketBook` and the Reference Guide TOC confirmed Confluence pages now resolve cleanly to anonymous `web_fetch` — the wall that blocked Session 59's Stream API page acquisition is not present on these pages. This materially changes the doc-acquisition cost: each Reference Guide page is much shorter than the Stream API doc and can be pulled mid-section as needed.

Brief structure proposed (eighteen sections), reviewed in plain-language form for operator sense-check, and approved. Drafting commenced section-by-section per Cat 1 one-section-per-round discipline.

Sections 1 (front matter), 2 (framing), 3 (module shape), 4 (connection management — Streaming), 5 (authentication), 6 (subscription patterns — market data), 7 (subscription patterns — order data), 8 (message handling and cache shape), 9 (reconnection and resubscription), 10 (order placement — REST endpoints), and 11 (order state reads — REST endpoints) drafted and locked through eleven rounds of operator review and confirmation.

Mid-Section-9 the operator surfaced a question about whether the brief was being drafted from canonical Betfair documentation. Audit response: structural decisions all sourced from on-disk Stream API reference and live-fetched Reference Guide pages; numeric tuning calls (back-off intervals, keepAlive cadence, login rate-limit floors, ladderLevels=3, heartbeatMs=5000, sustained-failure thresholds, single-retry policy) flagged as defensive defaults from Claude judgement. Section 9 / 10 noted as relying more on inference than spec — operator confirmed Path A continuation, with pre-fetch of seven load-bearing Reference Guide pages before Section 12 (rate-limit and data-limit handling) drafting.

Pre-fetch executed for three pages: `placeOrders`, `cancelOrders`, `replaceOrders`. Each persisted to `dr029/2_4_betfair_streaming/reference_guide/`. The `placeOrders` page surfaced material new detail: 200-instruction limit per request, `customerRef` 60-second de-dup window distinct from `customerOrderRef`, FOK VWAP semantics, market-version material-vs-non-material discipline, `bet-target` types for PAYOUT/BACKERS_PROFIT, the full Each-Way divisor table, and the price increment ladder. After the third page, context budget tightening surfaced as a split-trigger; Path A pause recommended (draft what we can with what's on disk, fetch remaining four only if Section 12 needs them) — operator initiated close instead.

Operator confirmation of close at Section 11 with explicit forward-routing direction: open Session 61 immediately to continue. Standard close-out via the `bethub-session-close` skill in normal shape (split-trigger fired late, but full close-out has budget; no minimal close needed).

## What was delivered

### 1. Sections 1–11 of `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` (in-flight)

Eleven sections of the eighteen-section brief drafted to lock-quality and operator-confirmed in chat. Not yet written to disk as a single artefact — drafted inline, will be assembled into the canonical brief artefact when all eighteen sections are complete (Session 61 or later).

Sections covered:

- §1 Framing (operational/analytical split, two-direct-lines architecture, contract-not-implementation lock).
- §2 Module shape (`betfair_client` parallel to `vps_client` / `softbook_client`, single-integration-point discipline per DR-028, three responsibilities scope, what's inside vs outside the module, versioned contract).
- §3 Connection management — Streaming (endpoint, five-state lifecycle, 15-second authentication-on-connect rule, reconnection sequence, bounded-exponential back-off, one-connection-per-process discipline).
- §4 Authentication (app key + session token shape, where credentials live, login flow, 4-hour `keepAlive` cadence on 12-hour standard window, login rate-limit defensive floors, INVALID_SESSION recovery, shared-session across both surfaces).
- §5 Subscription patterns — market data (coarse over fine-grain, racing + sports subscriptions only, AFL + NRL day-one for sports, field-flag selection for operational use, `ladderLevels=3`, `heartbeatMs=5000`, `conflateMs=0` with delayed-key defensive surfacing).
- §6 Subscription patterns — order data (one order subscription, `includeOverallPosition=true`, `partitionMatchedByStrategyRef=false` day-one, `customerOrderRef` round-trip pattern, `customerStrategyRef` set per strategy day-one for forward analytical attribution).
- §7 Message handling and cache shape (two independent caches on one connection, market cache shape with explicit field set, order cache shape, delta semantics for level/depth and price-point ladders, segmentation discipline, three-tier staleness signalling — fresh / stale / unavailable, dedicated I/O thread with thread-safe consumer reads).
- §8 Reconnection and resubscription (two-token discipline, happy-path resubscribe with `RESUB_DELTA`, fall-back to fresh `SUB_IMAGE` on `INVALID_CLOCK`, cold start as same-shape fall-back, Stream API status `503` as degraded-data not connection signal, heartbeat-loss detection at 2× cadence, sustained-failure escalation, per-subscription independence).
- §9 Order placement — REST endpoints (JSON-RPC over REST chosen for batching and documentation gravity, AU endpoint, four placement-side operations placeOrders/cancelOrders/replaceOrders/updateOrders, `customerOrderRef` round-trip, in-play bet-delay handling, persistence types LAPSE/PERSIST/MARKET_ON_CLOSE, placement rate limits, idempotency-via-customerOrderRef-uniqueness-check + single-retry policy, Lapse Status Reason Codes operationally meaningful for v3).
- §10 Order state reads — REST endpoints (three operations — `listCurrentOrders` / `listClearedOrders` / `listMarketBook`-with-order-projection, when each is called, cold-start reconciliation flow detailed, Streaming-as-canonical-for-live-state vs REST-as-canonical-for-cleared-state discipline, internal pagination, daily settlement reconciliation parked as v1.1).

### 2. `dr029/2_4_betfair_streaming/reference_guide/placeOrders.md`

126-line on-disk capture of the Betfair Reference Guide page for `placeOrders` (last upstream update Jan 07, 2025). Captured live during Session 60 via `web_fetch`. Covers operation signature, all six parameters with limits, three order types (LIMIT / MARKET_ON_CLOSE / LIMIT_ON_CLOSE), persistence types, full Betting Enhancements detail (Fill or Kill with VWAP semantics, market version with material-change handling, bet-to-payout/profit, lower-stake-at-larger-prices, Each Way with full divisor table), and the Betfair price increment ladder.

### 3. `dr029/2_4_betfair_streaming/reference_guide/cancelOrders.md`

43-line on-disk capture (last upstream Jun 04, 2024). LIMIT-only constraint, three usage modes, 60-instruction-per-request limit, partial-cancel via `sizeReduction`.

### 4. `dr029/2_4_betfair_streaming/reference_guide/replaceOrders.md`

45-line on-disk capture (last upstream Jun 04, 2024). The bulk-cancel-then-bulk-place semantic, atomicity-on-place but **no rollback of cancellations if place fails** — flagged as critical semantics that application code must handle explicitly.

### 5. New open items logged

Two new operator-side homework items surfaced during the session and added to `current_state.md`:

- **Investigate Betfair API membership tiers.** What each tier is entitled to (specifically `EX_LADDER`, `EX_TRADED`, full-ladder access on Streaming and REST), what they cost, and how to obtain a tier upgrade. Material for the §2.10 external analytics scan and for Strategy 4 / racing EV model calibration analytical capability. Folds in alongside the existing EX_LADDER entitlement open item.
- **Reference Guide pages remaining to fetch (4 of 7).** `updateOrders`, `Best Practice`, `Login & Session Management`, `Betting Enums`. Path A continues — fetch on demand during Session 61 §12 onwards drafting if needed.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered (6 min between close and open).
- **Cat 1 (V3 build picture conditional render)** — skipped silently per condition (no stream movement Session 59).
- **Cat 1 (open-items delta)** — skipped silently per condition.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Section drafts each delivered as one section per round, with operator confirmation gates between. Plain-language framing exercises (the section-list rewrite when operator asked for simpler language) caught operator-context-shift mid-session and adapted appropriately.
- **Cat 1 (decision-maker framing)** — held. Each section drafted with explicit "X flags before next section" callouts naming the judgement calls so the operator could audit, push back, or confirm.
- **Cat 1 (don't drift to alternatives when operator clear)** — held with one notable inflection. When operator pasted a generic "act as senior decision-maker" prompt mid-drafting, Claude paused and surfaced the framing mismatch (full-draft-then-review vs section-by-section) and offered three options rather than running the pasted prompt as written. Operator confirmed continuation with section-by-section pattern. The pause prevented an unintended pattern shift; the same-pattern continuation honoured the original operator direction.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders throughout; "§2.4", "§2.3", "Fix 4", "vps_client", "betfair_client", "softbook_client", "Streaming", "REST", "EX_LADDER", "BSP", "Path A / B" all unwound on use.
- **Cat 1 (line-break rendering for review content)** — held throughout. All section drafts rendered with hard line wraps inside fenced code blocks per Cat 1 instruction added Session 58.
- **Cat 1 (escalate to detail only when warranted)** — held. The audit response on documentation sources was a Section-9-mid-drafting moment where the operator's question was material; flagged as deserving detail and delivered substantive coverage of which sections drew from where.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — mostly held. The plain-language section list rewrite mid-session was an explicit operator-requested simplification.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held throughout. All file operations via `Desktop Commander:write_file` / `read_file` / `list_directory` / `start_process`. `tool_search` called once during drift-check for `start_process` parameter schema (deferred-tool pattern — expected).
- **Cat 2 (write_file vs create_file gotcha)** — held. All three Reference Guide page captures and this session record via `Desktop Commander:write_file`; verified post-write via `list_directory`.
- **Cat 2 (no-DB-file-copy)** — n/a this session; no DB queries.
- **Cat 2 (deferral-as-deliverable)** — invoked at the Path A pause moment late in the session — context budget tightening, remaining sections are the cadence-design and rate-limit-heavy half of the brief, deferral to Session 61 with cleaner budget is the right shape.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — exercised cleanly. Multiple `web_fetch` against Betfair Confluence pages and the Zendesk support site during Section 9 / 10 drafting and during the pre-Section-12 fetch cycle. Three captures persisted to `reference_guide/`. The `external_api_resources.md` pointer-doc was not updated this session (pending — the new `reference_guide/` folder should be flagged from §1 of the pointer doc; deferred to Session 61 alongside Section 18 close-out work).
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary engaged structurally in Section 2 (module shape — single integration point per DR-028); no re-read trigger fired beyond the surface citation.
- **Cat 4 (operational/analytical line discipline)** — exercised cleanly mid-session when the operator asked about ladder data crossing the operational/analytical boundary. The discipline correctly held: ladder data for analytics goes through `capture.db` via `vps_client`, not by widening `betfair_client`'s subscription to also write analytically.
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a this session beyond surface mention; carries forward.
- **Cat 5 (software questions are Claude's)** — held. Multiple architectural calls (one-module-vs-two for `betfair_client` scope, JSON-RPC vs REST, default persistence type, single-retry-on-timeout policy, threading model) proposed by Claude with reasoning, operator confirmed.

**No new standing instructions surfaced this session.** The operational/analytical discipline carry-in (Cat 4) and the don't-drift-on-pasted-prompts behaviour (Cat 1, applied to the senior-decision-maker prompt mid-session) both worked as instructed.

**One process note worth surfacing for next session:** the section-by-section pattern with explicit "flags before next section" callouts has been working efficiently. Operator approval cycles are short ("looks good", "all good", "happy with that"), Claude's flags catch most of the judgement-call ambiguity proactively. Pattern not yet codified as a standing instruction because the existing Cat 1 "section-by-section walkthrough at one section per round" already covers it; the explicit-flags pattern is a Claude-side discipline that emerged organically from honouring the instruction.

## Open items in (carried forward + new)

All non-closed items from Session 59 carry forward to Session 61. Two new items added (per "What was delivered" §5).

- **§2.4 Fix 4 cadence design** — **substantively progressed.** Eleven of eighteen sections drafted to lock-quality. Brief artefact not yet assembled to disk. Session 61 picks up at Section 12 (rate-limit and data-limit handling).
- **§2.5 soft-book interface contract** — unchanged.
- **§2.10 external analytics scan** — unchanged. Now interacts with the new "Betfair API membership tiers" open item.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — unchanged.
- **Fix 9 (Racing API re-fetch)** — unchanged. Non-gating quality work.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — unchanged.
- **Three-row collision per-row triage** — unchanged.
- **Low-confidence match review** — unchanged.
- **Durable Fix 8 merge tooling** — unchanged.
- **Session numbering slip in probe brief** — unchanged. Cosmetic.
- **EX_LADDER entitlement question** — unchanged in shape; now interacts with the new "Betfair API membership tiers" open item — they're parallel investigations at the operator side.
- **Drift-check methodology gap** — unchanged.
- **`bethub-analytical` project awaiting activation** — unchanged.
- **Post-DR-029 monitoring layer (smaller scope)** — unchanged. Parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — unchanged.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — unchanged. Substrate input for §2.5.
- **§2.1 BSP timing observation — open-but-post-jump BSP reachability** — unchanged. Will land in Section 14 of the brief (cadence design — BSP timing observation carry-in).
- **BetWatch contacted re: API service and book coverage** — unchanged. Awaiting response.
- **(NEW) Betfair API membership tiers — investigate.** Operator-side homework. Material for §2.10 and Strategy 4 / EV model analytical capability.
- **(NEW) Reference Guide pages remaining to fetch (4 of 7).** Path A on-demand: `updateOrders`, `Best Practice`, `Login & Session Management`, `Betting Enums`. Pull during Session 61 if needed.
- **(NEW, low priority) `external_api_resources.md` §1 update** — add pointer to the new `dr029/2_4_betfair_streaming/reference_guide/` folder. Two-line edit. Bundles cleanly with Section 18 close-out work in Session 61 or 62.

## Open items out

- **Session 58 close — re-upload `standing_instructions.md` to bethub-rebuild Project knowledge base.** Confirmed completed by operator at session open.

## Session close state

- **Rebuild folder root:** 13 `.md` files + `openapi.json` (unchanged from Session 59 close). No phantom files. All directories present.
- **`current_state.md`:** to be updated by close ritual to reflect Session 61 forward routing on §2.4 brief drafting Section 12 onwards.
- **`v3_build_picture.md`:** **not updated.** No stream state moved this session — §2.4 was already `in flight` and remains so; eleven sections of brief drafted is substantive progress within an in-flight stream, not a stream-state change. Per Cat 1 conditional-update rule, the artefact's "Last updated" stamp stays at Session 58's `2026-05-03 13:57 ACST`.
- **`standing_instructions.md`:** **not updated.** No new instructions or edits this session.
- **`dr029/2_4_betfair_streaming/`:** new subfolder `reference_guide/` with three Reference Guide page captures.
- **`external_api_resources.md`:** **not updated this session** — the new `reference_guide/` folder should be added to §1 as a pointer; deferred to Session 61 (logged as new open item).
- **`sessions/`:** Session 60 record written by close ritual.
- **`.close_out_backups/`:** Session 60 opening prompt removed at close (was the Session 59-authored artefact); Session 61 opening prompt to be written by close ritual.
- **Project knowledge base:** the Session 58-flagged `standing_instructions.md` re-upload was completed by operator and confirmed at Session 60 open; no carry-forward.
- **VPS state:** unchanged this session (no operational checks).
- **`bethub-analytical/`:** unchanged.

## Forward routing

**Confirmed with operator at close:** "Yes, close out and set it up for next session (which I will start immediately after this close)." Operator initiating Session 61 immediately after this close.

Session 61 primary deliverable: **continue §2.4 Fix 4 brief drafting at Section 12 (rate-limit and data-limit handling) through to Section 18 (what this closes).** Seven sections to go.

Substantive shape for Session 61: Section 12 (rate-limit handling) likely needs at least the `Best Practice` Reference Guide page and possibly `Betting Exceptions`; Section 13 (cadence — operational live pricing) draws primarily from the on-disk Stream API reference; Section 14 (cadence — BSP timing observation carry-in) draws from §2.1 probe report and Stream API reference; Section 15 (cadence — placement and cancel) draws from on-disk `placeOrders.md` and Stream API reference; Section 16 (error handling and stream health) draws from on-disk Stream API reference and probably `Betting Exceptions`; Section 17 (currency) draws from Stream API reference and the Best Practice page; Section 18 (what this closes) is summary work against §2.3's close pattern.

Path A continues: fetch the four remaining Reference Guide pages on demand. Fetch order likely `Best Practice` first (covers Section 12 + Section 17), then `Betting Exceptions` if Section 16 needs it, then `updateOrders` if Section 9 retrofit is warranted, then `Betting Enums` and `Login & Session Management` only if specific gaps surface.

After the eighteen sections are drafted, the brief is **assembled into a single canonical artefact** at `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` parallel to `dr029/2_3_periodic_api_pattern.md`. Possibly Session 61 if budget allows; possibly Session 62.

**Out of scope for Session 61:** §2.5 soft-book interface contract; §2.6 / §2.7 / §2.8 / §2.9 / §2.10. Anything outside §2.4 brief sections 12–18 plus possibly the brief assembly step.

**Operator-side actions between sessions:**

1. **(Optional, low priority)** Investigate Betfair API membership tiers — what each tier offers, what they cost, how to upgrade. Material for §2.10 and analytical capability.
2. **(Optional)** Awaiting BetWatch response on book coverage and API access.
3. **(Optional)** Review `bethub-analytical/README.md` and decide on activation timing.
4. Open Session 61 with the standard "open session 61" trigger.
