# Session 58

**Title:** §2.3 (periodic-only API pattern reframe on operational/analytical axis) locked. DR-029 stream count drops from nine to eight. Two minor governance corrections surfaced (operator already holds Betfair API documentation; BetWatch contacted as soft-book vendor candidate). One Cat 1 edit to standing instructions (line-break rendering for review content).
**Opened:** 2026-05-03 12:09 ACST
**Closed:** 2026-05-03 13:57 ACST
**Wall-clock:** 1h 48min (single sitting, single workday — same-workday continuation of Session 57's 12:01 close, 8 min gap).
**Tool routing:** Claude Chat. No Code routing this session — §2.3 is documentation/specification work, no empirical probe, no file edits to executable code.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-DB integration boundary discipline), DR-021 (timestamp anchoring), DR-019 (derived state on read — referenced in §2.3 artefact).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-03 12:09 ACST`.
Close: same command → `2026-05-03 13:57 ACST`.

Sunday early afternoon, same-workday continuation of Session 57's 12:01 close (8 min gap; same-workday per Cat 1).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- 13 `.md` files at rebuild root + `openapi.json` (matched expected count at Session 57 close).
- All directories present.
- `.close_out_backups/` contained `SESSION_58_opening_prompt.md` only (Session 57 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-03 12:01 ACST` matched Session 57 close; `sessions/SESSION_57.md` present and non-empty (196 lines); `v3_build_picture.md` last-updated `2026-05-03 12:01 ACST` matched (artefact moved at Session 57 close — §2.1 stream from `in flight` to `done`).
- Governing DRs named in orientation summary.
- Same-workday calendar-calibrated recap delivered (tight).
- V3 build picture: rendered (stream state moved at Session 57 close).
- Open-items delta: rendered (§2.1 closed; §2.1 BSP timing observation surfaced as new).

## Session shape

Session 58 was a **single-deliverable documentation session** with one substantive thread plus two governance corrections that surfaced naturally during section-by-section review.

The substantive thread was authoring `dr029/2_3_periodic_api_pattern.md` — the DR-029 §2.3 reframe of the periodic-only API pattern on the operational/analytical axis. Documentation work, not new design — the two-direct-lines architecture was already committed in `dr029/dr029_scope.md` §1.2; §2.3 makes the consequence for `vps_client`'s contract explicit so v3 build does not drift back toward dual-purpose reads.

Six sections drafted section-by-section (header, framing, analytical reads, operational reads, bracketing-doesn't-transfer, what-this-closes), one section per round per Cat 1, operator-confirmed each section before moving on. Two operator interventions during review: (a) confirmation that analytical has no input to operational data flow — folded into Section 4's "no analytical input to the operational flow" block; (b) operator flagged that Betfair and Racing API documentation are already in hand from Session 55 (`external_api_resources.md`), correcting Section 6's "held lightly until operator collects Betfair API documentation" framing to "documentation in hand"; (c) operator flagged BetWatch contacted as soft-book vendor candidate — confirmed §2.3 unchanged (vendor selection is §1.4 / §3.5 territory, not §2.3 territory), logged for `current_state.md` open items.

Substantively closed: DR-029 §2.3 stream. Forward routing confirmed: Session 59 picks up §2.4 Fix 4 cadence brief drafting. Session closed via `bethub-session-close` skill.

## What was delivered

### 1. `dr029/2_3_periodic_api_pattern.md` — DR-029 §2.3 locked

88-line artefact at `dr029/2_3_periodic_api_pattern.md`. Six sections:

- **Header.** Status (locked, closes DR-029 §2.3), authored Session 58, governing DRs (DR-027 / DR-028 / DR-029), source recommendations (multi-agent review Recommendations 1 and 5), cross-references (`dr029/dr029_scope.md` §1.2 / §2.4 / §2.5; `architecture.md` §B).
- **§1 Framing.** What the periodic-only pattern is, what the multi-agent review surfaced (the pattern was being asked to do double duty for analytical and operational consumers), what §2.3 does about it (reframe on operational/analytical axis), and the closing line that this is making an existing commitment explicit rather than introducing new architecture.
- **§2 Analytical reads — periodic-only reaffirmed.** Analytical line definition (`vps_client` → `capture.db`, backward-looking work per DR-019), no on-demand fresh-now endpoint, the bracketing argument (analytical questions are about market movement around a moment, not a single point), cadence as `capture.db`-internal, staleness signalling per v1.0 lock.
- **§3 Operational reads — separate concern.** Operational line definition (`betfair_client` / `softbook_client` direct), what operational reads serve (live decision support — racing page, sports page, burst-review, bet entry), no analytical input to operational flow, no on-demand fresh-now from `vps_client`, the two lines query the same Betfair API consistent-by-construction modulo cadence lag.
- **§4 The bracketing argument does not transfer to operational reads.** Why bracketing works analytically (analytical questions are time-insensitive, surrounding-interval snapshots beat single fresh-now), why bracketing fails operationally (cadence lag is the dominant fitness criterion for operational reads), the named drift pattern from Cluster-3 Session 31 / Cluster-2 Session 32 with `standing_instructions.md` Cat 4 reference, two-question test for which line a question is on, plus how to handle questions that split across both lines (stitched at v3 consumer surface, not inside the clients).
- **§5 What this closes.** §2.3 locked, DR-029 stream count drops from nine to eight, what changed vs. pre-reframe scope (split by line), what this enables (§2.4 and §2.5 specify operational-line behaviour without analytical-line constraints), open items routed forward (§2.4 Fix 4 brief drafting now fully unblocked given documentation already in hand; §2.5 soft-book interface contract picks up Racing API OpenAPI spec as canonical reference plus BetWatch vendor candidate as parallel-track input). No new debt surfaced.

The reframe does not change `vps_client`'s contract — `vps_client` was already periodic-only by intent. It changes how the project talks about the pattern: the pattern is not a universal property of v3's data reads, it is a property of analytical reads specifically.

### 2. Standing-instruction Cat 1 edit — line-break rendering for review content

Mid-session operator request: when providing content to review, render with line breaks so it fits chat width without horizontal scrolling. Applied for the remainder of Session 58 (Sections 3–6 of the §2.3 artefact were rendered with hard line wraps in the review fenced blocks). To be folded into `standing_instructions.md` Cat 1 at this close.

Drift signal addition: long unwrapped lines forcing horizontal scroll on review content.

### 3. Two governance corrections surfaced

**(a) Betfair / Racing API documentation already in hand.** Session 57's open-items list and `current_state.md` carried the framing "operator continuing to collect Betfair API documentation between sessions." Operator flagged during §2.3 Section 6 review that this had landed Session 55 — `external_api_resources.md` documents all four Betfair entry points (Reference Guide, Sample Code, API Tools Demo, Streaming API note) plus the Racing API OpenAPI spec sitting locally at `openapi.json`. Correction folded into §2.3 Section 6's "open items routed forward" block. To clear from `current_state.md` pending operator-side actions at this close.

**(b) BetWatch contacted as soft-book vendor candidate.** Operator flagged BetWatch has been contacted re: their book coverage, and they have an API service that may address the soft-book operational source need. Confirmed §2.3 unchanged — per `dr029/dr029_scope.md` §1.4 (soft-book operational layer source-flexible) and §3.5 (vendor selection out of scope), §2.5 specifies the interface contract; vendor selection is v3.1 territory. To log as new open item in `current_state.md`: "BetWatch contacted re: API service and book coverage; awaiting response. Candidate soft-book operational source for v3.1 implementation per §1.4 / §3.5."

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered (8 min between close and open).
- **Cat 1 (V3 build picture conditional render)** — rendered (stream state moved Session 57 — §2.1 to `done`).
- **Cat 1 (open-items delta)** — rendered (§2.1 closed, BSP timing observation new).
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Section-by-section review at one section per round was the explicit shape.
- **Cat 1 (decision-maker framing)** — held. Each section ended with operator confirmation gate before moving forward.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. When operator said "yep" to start drafting, started drafting; when operator said "yep" to lock each section, locked it.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders; "§2.3", "§2.4", "§2.5", "vps_client", "betfair_client", "softbook_client", "BSP", "bracketing argument" all unwound on use throughout review.
- **Cat 1 (line-break rendering for review content)** — *new instruction, surfaced this session.* Honoured for Sections 3–6 review after operator request mid-Section-3.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open and close. Same 13 `.md` + `openapi.json` at root both checks; clean.
- **Cat 2 (Desktop Commander default)** — held throughout. All file operations via `Desktop Commander:write_file` / `read_file` / `list_directory` / `start_process`. `tool_search` called once for `start_process` parameter schema (deferred-tool pattern — expected).
- **Cat 2 (no-DB-file-copy)** — n/a this session; no DB queries.
- **Cat 2 (operational/analytical line discipline)** — n/a this session in any reasoning sense; the §2.3 artefact itself is the formalisation of this discipline.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 2 (write_file vs create_file gotcha)** — held. §2.3 artefact written via `Desktop Commander:write_file` to canonical Mac path; verified post-write via wc/head.
- **Cat 3 (external API resources reach-for)** — surfaced via operator correction (governance correction (a) above). `external_api_resources.md` is the canonical pointer for Betfair docs in hand and Racing API OpenAPI spec.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary held cleanly throughout — §2.3 artefact is the explicit articulation of the boundary on the analytical/operational axis.
- **Cat 4 (operator review of artefacts is between-session work)** — n/a; the §2.3 artefact was reviewed inline section-by-section.
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a this session; carries forward.
- **Cat 5 (software questions are Claude's)** — held. Artefact structure proposal, section content, cross-reference choices were Claude's calls; operator confirmed direction.

**One process win:** operator's two corrections (Betfair docs already in hand, BetWatch contacted) caught at exactly the right moment — Section 6 review — before the artefact locked. Both surfaced from operator-side context Claude didn't have. Section-by-section review shape is what made this catchable.

**No new standing instructions surfaced this session beyond the line-break rendering Cat 1 edit above.**

## Open items in (carried forward)

All non-closed items from Session 57 carry forward to Session 59. Status updates:

- **§2.3 periodic-only API pattern reframe** — **CLOSED THIS SESSION.** See "Open items out".
- **§2.4 Fix 4 cadence design** — **fully unblocked this session.** Documentation in hand (`external_api_resources.md` §1) per governance correction (a). Session 59 primary deliverable.
- **§2.5 soft-book interface contract** — partial input from probe Q5 (harness/greyhound Racing API gap); BetWatch vendor candidate added as parallel-track input (governance correction (b)).
- **§2.10 external analytics scan** — unchanged. Inventory write-up is the remaining work.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — unchanged. Post-DR-029 documentation pass.
- **Fix 9 (Racing API re-fetch)** — unchanged. Non-gating quality work.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — unchanged. Non-gating quality work.
- **Three-row collision per-row triage** — unchanged. Non-gating.
- **Low-confidence match review** — unchanged. Non-gating.
- **Durable Fix 8 merge tooling** — unchanged. Non-gating.
- **Session numbering slip in probe brief** — unchanged. Cosmetic.
- **EX_LADDER entitlement question** — unchanged. Operator-side homework.
- **Drift-check methodology gap** — unchanged. Light-touch; folds into next pre-flight pattern naturally.
- **`bethub-analytical` project awaiting activation** — unchanged. Out-of-rebuild-project work.
- **Post-DR-029 monitoring layer (smaller scope)** — unchanged. Parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — unchanged. Non-gating.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — unchanged. Substrate input for Fix 4 / §2.5.
- **§2.1 BSP timing observation — open-but-post-jump BSP reachability** — unchanged. Forward-reference input for Fix 4 cadence design.

**New (Session 58):**

- **BetWatch contacted re: API service and book coverage** — awaiting response. Candidate soft-book operational source for v3.1 implementation per `dr029/dr029_scope.md` §1.4 (soft-book operational layer source-flexible) and §3.5 (vendor selection out of DR-029 scope). Forward-reference input for §2.5 interface contract design — concretely: what API shape exists in the wild, what books BetWatch covers, what cadence they offer.

**Closed (Session 58 — clearing from operator-side pending):**

- ✅ Continue collecting Betfair API documentation — landed Session 55 in `external_api_resources.md`. Cleared from `current_state.md` pending operator-side actions.
- ✅ Re-upload `standing_instructions.md` to bethub-rebuild Claude Project knowledge base — operator flagged at Session 58 open as completed. Cleared.

## Open items out

- **§2.3 periodic-only API pattern reframe — CLOSED.** Locked artefact at `dr029/2_3_periodic_api_pattern.md` (88 lines). Per `dr029/dr029_scope.md` §2.3, the work was: reaffirm periodic-only for analytical reads, carve out operational consumers, clarify the bracketing argument does not transfer. All three landed. The DR-029 close addendum at `dr029/dr029_scope.md` §2.3 will need updating with the close detail at DR-029 close-out time (not this session). DR-029 stream count drops from nine to eight.

## Session close state

- **Rebuild folder root:** 13 `.md` files + `openapi.json` (unchanged from Session 57 close). No phantom files. All directories present.
- **`current_state.md`:** updated by close ritual to reflect §2.3 closure, BetWatch new open item, two cleared operator-side actions, Session 59 forward routing on §2.4 Fix 4 cadence brief drafting.
- **`v3_build_picture.md`:** §2.3 stream moves from `in flight` to `done` (carry-rule applies — drops at Session 60 render). §2.1 drops at this render per carry-rule (closed Session 57, carry expired). Other streams unchanged. Artefact updated; "Last updated" stamp moves to this close timestamp.
- **`standing_instructions.md`:** Cat 1 edit applied — line-break rendering for review content. Re-upload to Project knowledge base completed Session 58 open (operator-side action cleared). Net session edit: +1 instruction line in Cat 1.
- **`dr029/`:** new artefact at `2_3_periodic_api_pattern.md` (88 lines).
- **`sessions/`:** Session 58 record written by close ritual.
- **`.close_out_backups/`:** Session 58 opening prompt removed at close; Session 59 opening prompt to be written by close ritual.
- **Project knowledge base:** `standing_instructions.md` re-upload completed by operator Session 58 open. Operator-side re-upload needed again at this close given Cat 1 edit landed this session.
- **VPS state:** healthy (Session 57 confirmed; no operational checks this session).
- **`bethub-analytical/`:** unchanged.

## Forward routing

**Confirmed with operator at close:** "Whatever you recommend." → Claude recommendation: close Session 58, open Session 59 on §2.4 Fix 4 cadence brief drafting. Operator: "Yes."

Session 59 primary deliverable: **§2.4 Fix 4 cadence brief drafting (Betfair Streaming spec + cadence design).**

Per `dr029/dr029_scope.md` §2.4, the work is brief drafting — `betfair_client` module shape parallel to `vps_client`, single integration point for Betfair Streaming API, connection management, authentication, subscription patterns, reconnection behaviour, message handling, rate-limit handling. Documentation in hand: `external_api_resources.md` §1 (Reference Guide, Sample Code, API Tools Demo, Streaming API note). The §2.1 BSP timing observation from Session 57 (open-but-post-jump BSP reachability — `actualSP` populating 1–2 min post-jump while `market_status` is still `OPEN`) is forward-reference input for cadence design.

Bigger shape than §2.3 — properly multi-section work. Recommended approach: read into the Betfair Reference Guide first, then propose brief structure for operator review, then draft section-by-section. Likely a longer session than Session 58 but should still close in single sitting.

**Out of scope for Session 59:** §2.5 soft-book interface contract (separate session; awaits BetWatch response and is contract-spec rather than brief-spec); §2.6 / §2.7 / §2.8 / §2.9 / §2.10 (sequenced after §2.4 + §2.5).

**Operator-side actions between sessions:**

1. Re-upload `standing_instructions.md` to bethub-rebuild Claude Project knowledge base — Cat 1 line-break rendering edit landed this session.
2. (Optional) Awaiting BetWatch response on book coverage and API access — when it lands, the response feeds §2.5 forward.
3. (Optional) Review `bethub-analytical/README.md` and decide on activation timing.
4. Open Session 59 with the standard "open session 59" trigger.
