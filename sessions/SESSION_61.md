# Session 61

**Title:** §2.4 Fix 4 brief drafting — Sections 12–18 of 18 locked covering rate-limit and data-limit handling, three cadence-design sections (operational live pricing, BSP timing observation carry-in, placement and cancel), error handling and stream health, currency / GBP / AUD handling, what this closes. All eighteen sections now drafted-and-locked-in-chat across Sessions 60 + 61. Two new Reference Guide pages captured (`best_practice.md`, `market_data_request_limits.md`). Brief assembly to canonical artefact deferred to Session 62. Fresh-eyes review against full Betfair documentation suite logged as new open item.
**Opened:** 2026-05-03 17:05 ACST
**Closed:** 2026-05-03 17:51 ACST
**Wall-clock:** 46 min (single sitting, single workday — same-workday continuation of Session 60's 16:57 close, 8 min gap).
**Tool routing:** Claude Chat. No Code routing — section-by-section brief drafting + on-demand documentation fetch + persistence.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-03 17:05 ACST`.
Close: same command → `2026-05-03 17:51 ACST`.

Sunday afternoon, same-workday continuation of Session 60's 16:57 close (8 min gap; same-workday per Cat 1).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- 13 `.md` files at rebuild root + `openapi.json` (matched expected count from Session 60 close).
- All directories present.
- `.close_out_backups/` contained `SESSION_61_opening_prompt.md` only (Session 60 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-03 16:57 ACST` matched Session 60 close; `sessions/SESSION_60.md` present and non-empty (185 lines); `v3_build_picture.md` last-updated stamp older than Session 60 close (Session 60 was section-drafting only, no stream state moved).
- Governing DRs named in orientation summary.
- Same-workday calendar-calibrated recap delivered (tight, 8 min gap).
- V3 build picture: skipped silently per condition (no stream movement Session 60).
- Open-items delta: skipped silently per condition (no movement in 8 min gap).

## Session shape

Session 61 was a **continuation section-by-section brief-drafting session** — directly resumed Session 60's eighteen-section §2.4 Fix 4 brief drafting at Section 12, working through to Section 18.

Session opened against Session 60's deferred state. Operator confirmed first call: fetch `Best Practice` Reference Guide page before drafting Section 12. Path A on-demand fetch executed cleanly — `web_fetch` returned both `Best Practice` and `Market Data Request Limits` pages (the latter linked from Best Practice General Tips and load-bearing for §12.2 weight-budget arithmetic).

Sections 12 through 18 drafted in seven rounds of operator review and confirmation. Pattern continued from Session 60: section drafted → flag callouts → operator decides → lock → next section. Two notable mid-section operator-driven changes:

- **§13.5 cadence floor rewording.** Operator asked whether tightening the cadence floor to 0.5 seconds was risky or overkill. The pause produced a recognition that the original wording muddled two distinct guarantees — movement-cadence (sub-second when market moves) vs connection-liveness (heartbeat within bounds) — and the rewording separated them cleanly.
- **§14.7 in-race capture clarification.** Operator asked whether v3 captures data through the in-race window. The question surfaced that the original §14.7 wording read like the only capture window was post-CLOSED, when in fact v3's Streaming subscription delivers throughout OPEN-pre-jump → OPEN-in-running → SUSPENDED → CLOSED. Reworded to make the lifecycle explicit.
- **§15 persistence default.** Operator confirmed v2's standing pattern is per-bet operator choice with PERSIST as the UI default-select. Locked accordingly with the option for operator to flip per-bet via the placement form, plus post-placement persistence flips via the `updateOrders` path.
- **§16.6 hard-alert override behaviour.** Operator chose option (b) — confirmation modal — over one-click or typed-reason alternatives. Reviewable.
- **§17 currency decisions.** Two decisions surfaced and resolved: (1) daily refresh cadence (vs hourly) — Claude recommended daily, operator confirmed; (2) empty-cache hard alert (vs hardcoded fallback rate) — Claude recommended hard alert, operator confirmed.

After Section 18 lock, operator asked Claude's recommendation on whether to assemble the brief to disk this session or defer. Claude recommended deferral (context-budget honesty, formatting-drift risk, fresh-eyes review benefits from clean assembly). Operator confirmed. Standard close-out via the `bethub-session-close` skill in normal shape.

## What was delivered

### 1. Sections 12–18 of `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` (in-flight)

Seven sections of the eighteen-section brief drafted to lock-quality and operator-confirmed in chat. Combined with Sessions 60's eleven sections, **all eighteen sections are now drafted-and-locked-in-chat**. Brief artefact still not yet written to disk — drafted inline, will be assembled into the canonical brief artefact in Session 62.

Sections covered Session 61:

- §12 Rate-limit and data-limit handling (Streaming connection / subscription / auth-rate limits, REST data-weight 200-point budget with arithmetic, REST instruction-count limits, login rate floors, transport defaults, slow-consumer behaviour, aggregate discipline).
- §13 Cadence design — operational live pricing (publisher / heartbeat / consumer cadence triplet, what the burst UI sees, per-§13.5 movement-cadence and connection-liveness as two separate guarantees, sustained-degradation surfaces).
- §14 Cadence design — BSP timing observation carry-in (probe-driven justification for `SP_TRADED + SP_PROJECTED` subscription, the `bspReconciled` non-gate finding from probe §4(e), the `market_status in (SUSPENDED, CLOSED) AND bsp > 0` gate, NaN guard, sp container shape-shift, OPEN-but-post-jump partial-reconciliation handling, greyhound POST_START asymmetry, full lifecycle subscription including in-race + 60s post-CLOSED hold).
- §15 Cadence design — placement and cancel (latency budget — ~1s click-to-matched, customerOrderRef 60s de-dup window, single-retry policy on 3s timeout, in-play bet-delay handling, cancel pacing, replaceOrders atomicity gap with discriminated result type, updateOrders persistence-flag-only path, persistence default = PERSIST with operator per-bet override, closed-loop latency targets).
- §16 Error handling and stream health (three error categories — transient / structural / authoritative, three Streaming health signals — `status: 503` / heartbeat-loss / `con=true`, reconnection back-off with 60s sustained-failure escalation, REST error catalogue, lapse-status-reason codes, three-tier operator-visible failure surface — silent / visible-non-blocking / hard-alert-placement-disabled, override path = confirmation modal).
- §17 Currency — GBP, AUD, and where the conversion happens (Betfair GBP under-the-hood, AUD on order side, `listCurrencyRates` daily refresh, conversion at `betfair_client` boundary, AUD-specific minimum stake / BSP-liability tables, rate-staleness handling, empty-cache hard alert).
- §18 What this closes (DR-029 stream count drops 8 → 7, what changed in v3's design picture, what this enables downstream — §2.5 / §2.6 / §2.7 / §2.8 / v3 build, open items routed forward, no new debt).

### 2. `dr029/2_4_betfair_streaming/reference_guide/best_practice.md`

135-line on-disk capture of the Betfair Best Practice page (last upstream Jun 13, 2024). Captured live during Session 61 via `web_fetch`. Covers Development & Testing (Delayed vs Live App Key), Login & Session Management (24h default, country-specific limits, INVALID_SESSION_TOKEN handling, 20-min lockout on login-rate breach), General Tips (transaction charges, market-data limits pointer, prefer-leave-orders-in-place, Stream API over polling, log connectionId, betting enhancements), API Status, Expect: 100-Continue header avoidance, HTTP compression, persistent connection (3-min idle close), other performance pointers.

### 3. `dr029/2_4_betfair_streaming/reference_guide/market_data_request_limits.md`

79-line on-disk capture (last upstream May 21, 2025). Load-bearing reference for §12.2 brief content — the 200-point weight budget formula, per-PriceProjection weights table (`SP_AVAILABLE` 3, `SP_TRADED` 7, `EX_BEST_OFFERS` 5, `EX_ALL_OFFERS` 17, `EX_TRADED` 17, combinations explicitly non-additive), `exBestOffersOverrides` weight formula, plus worked examples written in for §2.4 brief reference (10 markets at `EX_BEST_OFFERS` = 50 weight, 7 markets at `EX_ALL_OFFERS + EX_TRADED` = 224 → exceeds, etc.).

### 4. New open items logged

Two new operator-side homework items surfaced this session and added to `current_state.md`:

- **(NEW) §2.4 Fix 4 brief — fresh-eyes review against full Betfair documentation suite.** Triggers after brief assembly (Session 62 or later). Candidate agents: fresh Claude session, or Grok via the multi-agent review pattern in `governance.md` (different model family for the skeptic seat). Goal: catch inferred-where-I-should-have-fetched gaps that section-by-section drafting may have missed. Operator-flagged Session 61.
- **(NEW) §2.4 Fix 4 brief assembly to canonical artefact.** Deferred from Session 61 close to Session 62. Output: `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` parallel to `dr029/2_3_periodic_api_pattern.md`. Plus the two-line `external_api_resources.md` §1 update to add the `reference_guide/` folder pointer.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered (8 min between close and open).
- **Cat 1 (V3 build picture conditional render)** — skipped silently per condition (no stream movement Session 60).
- **Cat 1 (open-items delta)** — skipped silently per condition.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Section drafts each delivered as one section per round, with operator confirmation gates. Mid-section flagged decisions were surfaced before lock.
- **Cat 1 (decision-maker framing)** — held. Each section locked with explicit "X flags before next section" callouts. Operator's "give me sharp dot points plain/gambler languaged" requests for §16 and §17 caught a register-shift mid-session and Claude adapted appropriately.
- **Cat 1 (don't drift to alternatives when operator clear)** — held with one inflection. Operator's "what's your rec?" mid-session asked Claude to make the call between assemble-now vs defer; Claude provided the recommendation rather than punting back to operator.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders throughout; "§2.4", "Fix 4", "vps_client", "betfair_client", "softbook_client", "Streaming", "REST", "EX_LADDER", "BSP", "Path A" all unwound on use.
- **Cat 1 (line-break rendering for review content)** — held throughout. All section drafts rendered with hard line wraps inside fenced code blocks per Cat 1 instruction added Session 58.
- **Cat 1 (escalate to detail only when warranted)** — held. The §16 and §17 sharp-dot-points reformatting was an operator-requested register shift; the detail-explain on §16.6 override modes was operator-prompted detail.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held in operator-language reformats. Section drafts themselves are necessarily detailed (artefact register, not conversational), but the conversational layer between sections held the brevity default.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held throughout. All file operations via `Desktop Commander:write_file` / `read_file` / `list_directory` / `start_process`. `tool_search` called once during open ritual for `start_process` parameter schema (deferred-tool pattern — expected).
- **Cat 2 (write_file vs create_file gotcha)** — held. Both Reference Guide page captures and this session record via `Desktop Commander:write_file`; verified post-write via `list_directory`.
- **Cat 2 (no-DB-file-copy)** — n/a this session; no DB queries.
- **Cat 2 (deferral-as-deliverable)** — invoked at the brief-assembly decision point near session end. Claude recommended deferral; operator confirmed. The session shape stays a clean drafting session without becoming a drafting + assembly hybrid.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — exercised cleanly. `web_fetch` against Betfair Confluence Best Practice and Market Data Request Limits pages, both succeeded under anonymous access. Both captures persisted to `reference_guide/`. The `external_api_resources.md` pointer-doc still not updated this session (logged as carry-forward open item, bundles cleanly with brief assembly in Session 62).
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary engaged structurally throughout the brief-drafting (Section 17 currency conversion at the integration boundary explicitly invoked DR-028's no-second-integration-point discipline).
- **Cat 4 (operational/analytical line discipline)** — exercised cleanly. Section 13 cadence design framed entirely on the operational line; Section 14 BSP timing observation carry-in correctly inherited the operational/analytical carve-out from §2.3 without re-litigating it.
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a this session beyond surface mention.
- **Cat 5 (software questions are Claude's)** — held. Multiple architectural calls proposed by Claude with reasoning, operator confirmed: §13 cadence-floor rewording (Claude recommended split into two guarantees, operator confirmed), §14.7 in-race capture rewording (Claude proposed clearer lifecycle framing, operator confirmed), §15 placement persistence default (Claude proposed PERSIST default with operator per-bet override, operator confirmed with the framing the operator wanted), §16.6 hard-alert override behaviour (Claude offered three options, operator chose), §17 currency decisions (Claude recommended both, operator confirmed both).

**No new standing instructions surfaced this session.** The "give me sharp dot points plain/gambler languaged" mid-session register-shift requests for §16 and §17 are already covered by Cat 1's "default to luddite-analyst-gambler brevity" — Claude's first drafts were artefact-register (necessarily detailed), operator's request shifted to operator-conversation register; the existing instruction's range covers both.

**One process note worth surfacing for next session:** the section-by-section pattern with explicit "flags before next section" callouts has continued working efficiently across both Session 60 (eleven sections) and Session 61 (seven sections). Eighteen sections drafted in roughly 3h 8m total wall-clock across the two sessions. No drift in the pattern; no need to codify further.

## Open items in (carried forward + new)

All non-closed items from Session 60 carry forward to Session 62. Two new items added (per "What was delivered" §4).

- **§2.4 Fix 4 cadence design** — **drafting complete in chat.** All eighteen sections drafted-and-locked. Brief artefact assembly to disk deferred to Session 62 — see new open item.
- **(NEW) §2.4 Fix 4 brief assembly to canonical artefact.** Session 62 primary deliverable. Output: `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`, parallel to `dr029/2_3_periodic_api_pattern.md`. Plus the two-line `external_api_resources.md` §1 update folding in cleanly.
- **(NEW) §2.4 Fix 4 brief — fresh-eyes review against full Betfair documentation suite.** Triggers after brief assembly. Candidate agents: fresh Claude session, or Grok via multi-agent review pattern.
- **§2.5 soft-book interface contract** — unchanged.
- **§2.10 external analytics scan** — unchanged. Now interacts with the Betfair API membership tiers item.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — unchanged.
- **Fix 9 (Racing API re-fetch)** — unchanged. Non-gating quality work.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — unchanged.
- **Three-row collision per-row triage** — unchanged.
- **Low-confidence match review** — unchanged.
- **Durable Fix 8 merge tooling** — unchanged.
- **Session numbering slip in probe brief** — unchanged. Cosmetic.
- **EX_LADDER entitlement question** — unchanged. Restated in §18.3 as routed-forward; v3 day-one operational reads do not depend on full-ladder data, so this remains parallel to §2.4 close.
- **Drift-check methodology gap** — unchanged.
- **`bethub-analytical` project awaiting activation** — unchanged.
- **Post-DR-029 monitoring layer (smaller scope)** — unchanged. Parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — unchanged.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — unchanged. Substrate input for §2.5.
- **§2.1 BSP timing observation — open-but-post-jump BSP reachability** — **substantively addressed in §2.4 Section 14**, will close at brief assembly time.
- **BetWatch contacted re: API service and book coverage** — unchanged. Awaiting response.
- **Betfair API membership tiers — investigate.** Unchanged. Operator-side homework.
- **Reference Guide pages remaining to fetch (now 2 of 4 remaining).** `updateOrders`, `Login & Session Management`, `Betting Enums`, `Betting Exceptions` — four pages were on the list at Session 60 close; this session captured `Best Practice` and `Market Data Request Limits` (the latter wasn't on the list but is load-bearing). The four originally-listed pages remain pending. Path A on-demand: pull during Session 62 if brief assembly or fresh-eyes review needs them. Re-stated in §18.3.
- **`external_api_resources.md` §1 update** — bundles with Session 62 brief assembly.
- **PASSIVE bet-delay model handling** — flagged in §15.4 as v3.1+ capability. Not in v3 day-one scope. Logged for completeness; revisit if Strategy 2 in-play placements ever justify it.

## Open items out

None this session. (Brief drafting Sections 12–18 closed; carries forward as the brief-assembly task.)

## Session close state

- **Rebuild folder root:** 13 `.md` files + `openapi.json` (unchanged from Session 60 close). No phantom files. All directories present.
- **`current_state.md`:** to be updated by close ritual to reflect Session 62 forward routing on brief assembly + pointer-doc update + fresh-eyes review setup.
- **`v3_build_picture.md`:** **not updated.** No stream state moved this session — §2.4 was already `in flight` and remains so; eighteen sections of brief drafted is substantive progress within an in-flight stream, not a stream-state change. Brief assembly in Session 62 will be the moment §2.4 stream state moves (in flight → done) once the artefact lands and §2.3-style close governance applies.
- **`standing_instructions.md`:** **not updated.** No new instructions or edits this session.
- **`dr029/2_4_betfair_streaming/`:** subfolder `reference_guide/` now contains five Reference Guide page captures — `placeOrders`, `cancelOrders`, `replaceOrders` (Session 60), `best_practice`, `market_data_request_limits` (Session 61). Brief artefact still pending assembly.
- **`external_api_resources.md`:** **not updated this session** — the new `reference_guide/` folder pointer still pending Session 62.
- **`sessions/`:** Session 61 record written by close ritual.
- **`.close_out_backups/`:** Session 61 opening prompt removed at close (was the Session 60-authored artefact); Session 62 opening prompt to be written by close ritual.
- **Project knowledge base:** unchanged. No Project upload action needed this session.
- **VPS state:** unchanged this session (no operational checks).
- **`bethub-analytical/`:** unchanged.

## Forward routing

**Confirmed with operator at close:** "b" (defer brief assembly to Session 62), with prior confirmation that Session 62's primary deliverable is brief assembly to disk + the `external_api_resources.md` pointer-doc update + fresh-eyes review setup.

Session 62 primary deliverable: **assemble the eighteen drafted sections into the canonical §2.4 artefact** at `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`. Strip the inline review-formatting (flag callouts, hard line wraps inside fenced code blocks) and unify the structure to match `2_3_periodic_api_pattern.md`. Write the two-line `external_api_resources.md` §1 update folding in the `reference_guide/` folder pointer. After assembly, set up the fresh-eyes review per the operator's flagged direction — either a fresh Claude session or Grok via the multi-agent review pattern in `governance.md`.

Section sources for assembly: Sections 1–11 in `sessions/SESSION_60.md` "What was delivered" + section-detail in chat history of Session 60; Sections 12–18 in `sessions/SESSION_61.md` (this file) "What was delivered" + section-detail in chat history of Session 61. The full inline drafts are in chat — assembly is read-and-paste-with-cleanup, not redrafting.

**Out of scope for Session 62:** §2.5 soft-book interface contract; §2.6 / §2.7 / §2.8 / §2.9 / §2.10. Anything outside brief assembly + pointer-doc update + fresh-eyes review setup.

After Session 62 closes the §2.4 stream (brief assembled, fresh-eyes review setup), the next active stream is **§2.5 soft-book interface contract** unless operator-side input from BetWatch lands first and changes routing.

**Operator-side actions between sessions:**

1. **(Optional, low priority)** Investigate Betfair API membership tiers — what each tier offers, what they cost, how to upgrade. Material for §2.10 and analytical capability.
2. **(Optional)** Awaiting BetWatch response on book coverage and API access.
3. **(Optional)** Review `bethub-analytical/README.md` and decide on activation timing.
4. Open Session 62 with the standard "open session 62" trigger.
