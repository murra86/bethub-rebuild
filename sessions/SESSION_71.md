# Session 71

**Title:** §2.8 (bet-schema reframing) brief drafting continued — §4 Betfair exchange bet records, §5 soft-book racing bet records, §6 soft-book sports bet records all locked. Three strategic calls landed: `customer_ref` not stored on bet record (transient retry-safety scaffolding only), bet record floor snapshot only with EX_LADDER carried forward as non-gating entitlement question, soft-book identity simplified to `soft_book_id` only (no operator-supplied bet receipt), and `operator_line_side` captured at placement-commit (not re-derived at read time) to protect against head-to-head price drift between placement and event-start. Brief now 521 lines, 7 of 10 sections locked. §8/§9/§10 deferred to Session 72.
**Opened:** 2026-05-04 07:09 ACST
**Closed:** 2026-05-04 07:36 ACST
**Wall-clock:** ~27 min substantive single sitting. New-workday open relative to Session 70's 00:21 ACST close (~7 hours gap, post-4am-cutoff).
**Tool routing:** Claude Chat. No Code routing.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring), DR-019 (derived state on read — load-bearing for §2.8), DR-026 (inline snapshot exception on bet records — load-bearing for §2.8).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 07:09 ACST`.
Close: same command → `2026-05-04 07:36 ACST`.

New-workday open relative to Session 70's 00:21 ACST close. ~7 hour gap, post-4am-cutoff. Single morning sitting.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 12 `.md` files + `openapi.json` + `external_api_resources.md` + `.DS_Store` + `v3_build_picture.md`. All directories present.
- `.close_out_backups/` contained `SESSION_71_opening_prompt.md` only (Session 70 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 00:21 ACST` matched Session 70 close; `sessions/SESSION_70.md` present (191 lines); `v3_build_picture.md` last-updated `2026-05-04 00:21 ACST` matched Session 70's `done` carry drop + §2.8 detail block update.
- New-workday recap delivered (active arc DR-029, what closed Session 70, what's in flight, what Session 71 does).
- V3 build picture: rendered (streams moved at Session 70 close).
- Open-items delta: skipped silently per condition (~7 hours gap, no operator action between close and open).

## Session shape

Session 71 was a **brief-drafting session** — continuing §2.8 (bet-schema reframing) per Session 70 forward routing. The session walked the brief section-by-section per Cat 1 default cadence, surfacing strategic decisions one at a time and absorbing technical detail into the artefact rather than into chat per the working-style memory edit (memory #16).

Three strategic rounds delivered three locked sections (§4 Betfair exchange, §5 soft-book racing, §6 soft-book sports). Round shape was tighter than Session 70 — strategic decisions were narrower (mechanical application of architectural commitments locked Session 70 across three bet types) so each section landed in roughly one strategic-question round plus one drafting round.

Round-by-round shape:

**Round 1 (§4 Betfair exchange — two strategic calls).** Re-established context from open ritual reads, plus pulled §2.4 §14 cross-references for placeOrders linkage detail. Two strategic calls surfaced together: (a) `customer_ref` retention on the bet record — Claude recommended transient-only (held in working state for the 60-second retry window, discarded thereafter); (b) at-placement snapshot scope — Claude recommended floor-only (best back / best back size / best lay / best lay size / total matched; no virtual ladder). Operator confirmed the customer_ref recommendation directly. Operator pushed back on the snapshot recommendation conditional on analytical-line coverage of depth.

**Round 2 (analytical-line ladder coverage verification).** Operator's hinge-condition: snapshot floor-only on the bet record is fine **if** the analytical line carries depth. Claude verified by inspecting the Saturday API observation probe report (`dr029/2_1_race_data/api_probe_report.md`):
- ✅ EX_BEST_OFFERS (3 best back / 3 best lay) and EX_ALL_OFFERS — captured periodically by VPS.
- ✅ Total matched, BSP, SP projections — captured.
- ❌ EX_LADDER (full per-price ladder with traded volume) — NOT captured. Authorisation-level rejection (DSC-0018) on current Betfair app key. Already an open item in `current_state.md` — "EX_LADDER entitlement question — operator-side homework; possible DR."

Three options offered: (A) lock recommendation A unchanged with no escalation; (B) lock A but escalate the EX_LADDER entitlement question in §2.8's "what this closes" section as not-gating; (C) defer §4 drafting until EX_LADDER question resolves. Claude recommended B. Operator confirmed: 3-deep view sufficient for currently-known audit needs, full ladder not needed, EX_LADDER as not-gating entitlement question is good framing — "we'll discover more when we actually get stuck into the analytical side of things, but that's a little bit down the track."

**Round 3 (§4 drafted and written).** §4 written via `Desktop Commander:edit_block`. Replaced the placeholder line "## Sections 4, 5, 6, 8 — to be drafted in subsequent sessions" with the full §4 content (seven sub-sections). File grew from 300 → 363 lines (+63).

**Round 4 (§5 soft-book racing — one strategic call).** Strategic call: soft-book identity field set. Three options offered: (A) `soft_book_id` only; (B) `soft_book_id` + optional `soft_book_bet_reference` (operator-supplied bookmaker bet receipt); (C) B + structured ticket-data block. Claude recommended B at first.

Operator pushed back: didn't understand the operational mechanics of the bet receipt reference. Asked for a simple scenario. Claude walked through the only intended use case: future CSV-import-from-bookmaker-transactions feature (parked) needing a clean join key from imported transaction rows back to v3 bet records. Honest reassessment — the future feature isn't on the v3 day-one roadmap, the field's value is gated entirely on a future feature, typing per-book bet receipt numbers is high friction, and inconsistent population would force fuzzy-matching anyway. Claude reversed recommendation to A.

Operator confirmed A directly: "Ultimately, if we do a CSV capability, there will be the capacity to do some fuzzy matching to get the right bets... In reality, I'm not going to input the bet receipt on bets that I take, so I think A is the way to go."

Lesson worth flagging: Claude's first-pass framing of B as "costs nothing if skipped" was wrong — operator effort is non-zero, and the field's value is gated on a not-yet-scoped feature. Honest reassessment after operator pushback was the corrective move.

**Round 5 (§5 drafted and written).** §5 written via `Desktop Commander:edit_block`. Seven sub-sections covering soft-book identity, operator-typed price, Betfair-side reference snapshot for EV-context, at-placement field set summary, retrospective entry adjustments, path (iii) placeholder, settlement state. File grew from 363 → 448 lines (+85).

**Round 6 (§6 soft-book sports — one strategic call + clarifying question).** Strategic call: how to handle the operator-specified line value on the bet record. Two options: (A) unsigned line only, side recoverable at read time from `betfair_market_id` plus §B.1.3 favourite-inference; (B) unsigned line plus resolved side captured at placement-commit. Claude recommended B because head-to-head prices shift between placement and event-start, and re-deriving the side at read time may draw the inference toward a different team than was true at click time. Operator confirmed B directly: "B negates that problem, so good call."

Operator then surfaced a clarifying question about whether the bet record captures the specific promo applicable at the time of the bet (e.g. "Sportsbet 4-place insurance, $50 cap, 2.0 floor, second-only refund"). Claude walked through the answer: the data is captured, but at the cycle layer (§7.1 `promo_terms` block) not duplicated on every bet record. One join from bet record via `promo_cycle_id` → cycle record → full promo specifics. Reasoning: avoids duplicating promo terms across every bet under the same cycle; matches the standing analysis convention that any bet whose outcome drives downstream behaviour is analysed as a single cycle. Operator confirmed: "Oh, that sounds great. Thanks."

**Round 7 (§6 drafted and written).** §6 written via `Desktop Commander:edit_block`. Seven sub-sections covering market-type discriminator, operator-specified line value (with `operator_line_side` decision-context captured at placement-commit), line-resolution-to-Betfair-market-id pattern (five-step staging sequence), at-placement field set summary, retrospective entry adjustments, path (iii) placeholder, settlement state. File grew from 448 → 521 lines (+73).

**Round 8 (close).** Section state summary delivered (7 of 10 sections locked, §8/§9/§10 deferred to Session 72). Two structural items flagged for awareness (§7 sits between §3 and §4 in the file due to Session 70 write order — clean physical ordering deferred to single mechanical edit at end-of-§2.8 close; `architecture.md` Session 42 architectural-extension formal sub-section update remains administrative cleanup, not gating). Operator confirmed close: "Yep, let's close up and set up the next session."

## What was delivered

### 1. §2.8 brief — three sections drafted, written to disk

Brief at `dr029/2_8_bet_schema/2_8_bet_schema.md` now 521 lines (300 at Session 70 close → +63 §4 → +85 §5 → +73 §6). Three sections locked this session:

**§4 Betfair exchange bet records.** Seven sub-sections: §4.1 exchange-specific identity (`customer_order_ref` permanent, `betfair_bet_id` permanent, `customer_ref` transient working state only — not on bet record); §4.2 at-placement snapshot type-specific fields (best back / best back size / best lay / best lay size / total matched, with EX_LADDER entitlement question carried forward to §10 as not-gating); §4.3 retrospective entry adjustments; §4.4 path (iii) placeholder; §4.5 order-state lifecycle (four amendable fields tracking through Betfair matching states); §4.6 order-state-to-settlement handoff at terminal order state; §4.7 failure modes captured on the bet record (`placement_state` field with three values: `clean`, `recovered-from-uncertain`, `placeholder-promoted`).

**§5 Soft-book racing bet records.** Seven sub-sections: §5.1 soft-book identity (`soft_book_id` only — no operator-supplied bet receipt); §5.2 operator-typed price (`price_taken` is the load-bearing decision-context fact; `snapshot_source = typed`); §5.3 Betfair-side reference snapshot for EV-context (same five fields as §4.2, but role is EV-comparison reference not the bet's own decision context, with EV-use cases named for Strategies 1, 2, and 4); §5.4 at-placement field set summary; §5.5 retrospective entry adjustments; §5.6 path (iii) placeholder with `typed → retrospective` snapshot_source flip on promotion; §5.7 settlement state (Betfair-canonical settlement; payout calc applies `price_taken` not the Betfair reference price).

**§6 Soft-book sports bet records.** Seven sub-sections: §6.1 market-type discriminator (`sports_market_type` ∈ {match, line, total}); §6.2 operator-specified line value (`operator_line_value` unsigned numeric, `operator_line_side` ∈ {favourite, underdog, over, under}, both mandatory for line and total markets, null for match — side captured at placement-commit, not re-derived at read time, protects against head-to-head price drift); §6.3 line-resolution-to-Betfair-market-id pattern (five-step staging sequence per `architecture.md` §B.1.2; `betfair_market_id` resolved at staging not at commit); §6.4 at-placement field set summary; §6.5 retrospective entry adjustments; §6.6 path (iii) placeholder; §6.7 settlement state (Betfair-direct auto-settlement per architecture §B.1.4; payout calc on `price_taken`).

### 2. Strategic decisions locked

Three strategic decisions confirmed by the operator and locked into the brief:

1. **`customer_ref` not stored on the bet record.** Held in transient working state on the in-flight record for the 60-second retry window per §2.4 §14.2, discarded thereafter. No read-time consumer post-window. `customer_order_ref` (the round-trip key, permanent identifier across Betfair-side state reads) is the load-bearing identifier and is stored permanently. `betfair_bet_id` also stored permanently. Three Betfair-side identifiers participate in placement; only two land on the bet record.

2. **Bet record carries floor snapshot only.** Five fields: best back, best back size, best lay, best lay size, total matched. No virtual ladder on the bet record. The 3-deep periodic view captured by VPS scrape into `capture.db` provides sufficient depth picture for currently-known audit needs. EX_LADDER (full per-price traded ladder) is not captured anywhere — Betfair returns DSC-0018 (authorisation-level rejection) on the current API credential. Carried forward as not-gating entitlement question to be revisited when analytical work surfaces concrete need.

3. **Soft-book identity is `soft_book_id` only.** No operator-supplied bookmaker bet receipt field. Operational reality: typing per-book bet receipt numbers on every placement is high friction across Strategy 1 volume; inconsistent population would force fuzzy-matching anyway. Future CSV-import-from-bookmaker-transactions feature (parked) can fuzzy-match on amount + timestamp + selection where it lands.

4. **`operator_line_side` captured at placement-commit, not re-derived at read time.** Decision-context per DR-026 (inline snapshot exception). Protects against head-to-head price drift between placement and event-start. Same field-shape across handicap and total markets (uniform schema; the discriminator is per-market-type validation rules).

### 3. Working-style adherence

Memory edit #16 ("strategic decisions surfaced; technical detail in the artefact") held throughout. Strategic questions surfaced one per round; technical detail (field lists, schema shapes, staging sequence steps, failure-mode handling) absorbed into the artefact body. The Round 4 reversal on §5's soft-book identity (B → A after operator pushback) demonstrated honest reassessment of a first-pass recommendation — flagged in Round 4 narrative above as a lesson worth holding onto.

### 4. §8–§10 deferred to Session 72

Three sections remaining in the §2.8 brief: §8 read-time resolution paths, §9 immutability discipline + reconciliation events, §10 what this closes for DR-029. Estimated single Session 72 to close §2.8 entirely. Plus one mechanical edit at end-of-§2.8 close: move §7 (cycle record + free bet ledger) to physical-file order after §6 for clean numerical layout (currently sits between §3 and §4 due to Session 70 write order; ordering doesn't affect content, only readability).

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021, DR-019, DR-026 named at open.
- **Cat 1 (calendar-calibrated recap)** — new-workday recap delivered.
- **Cat 1 (V3 build picture conditional render)** — rendered at open per condition (streams moved at Session 70 close).
- **Cat 1 (open-items delta)** — skipped silently at open per condition.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Section-by-section cadence with one strategic question per round; technical detail in the artefact, not in chat.
- **Cat 1 (decision-maker framing)** — held. Each round led with the call or recommendation; rationale followed only when warranted.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. Operator's confirmations on each strategic call were locked immediately; no further re-litigation.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders. EX_LADDER and DSC-0018 unwound on use.
- **Cat 1 (escalate to detail only when warranted)** — held. The analytical-line ladder coverage verification in Round 2 was explicitly flagged as warranting detail; operator opted in via the hinge-condition framing. The promo-on-cycle-record clarification in Round 6 was operator-initiated; Claude delivered the answer at appropriate detail and stopped.
- **Cat 1 (line-break rendering for review content)** — held; the strategic-call review blocks used hard line wraps.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open.
- **Cat 2 (Desktop Commander default)** — held. All file operations via `Desktop Commander:edit_block` (three append operations to `2_8_bet_schema.md`) and `Desktop Commander:read_file` / `start_process` for verification.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; all session content written directly to canonical artefact during the session. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — applies. Two structural items flagged in Round 8 close summary: §7 sits between §3 and §4 in physical file order (deferred mechanical edit to end-of-§2.8 close); `architecture.md` Session 42 architectural-extension formal sub-section update remains administrative cleanup, not gating.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — engaged. The Round 2 verification of analytical-line ladder coverage referenced the Saturday API observation probe report (`dr029/2_1_race_data/api_probe_report.md`) directly per Cat 3 protocol.
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — applies. Three `Desktop Commander:edit_block` operations were single-target append operations (replacing one specific placeholder line or extending one specific section). No multi-target pattern matching. No dry-run needed.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary engaged in §4.2 (analytical-line depth coverage via `vps_client` reads against `capture.db`), §5.3 (Betfair-side reference snapshot via `betfair_client` for soft-book bets), §5.6 + §6.6 (path iii reconciliation paths). DR-027/028 discipline preserved; the bet record's Betfair canonical identifiers remain the join key into the analytical layer at read time.
- **Cat 4 (operational/analytical line discipline)** — engaged throughout. Round 2 analytical-line ladder verification was a direct application of the discipline — naming the line first, reasoning about coverage on that line, not conflating with operational-line capture.
- **Cat 4 (Betfair-as-canonical-source extension)** — load-bearing this session. §4 §4.1 (Betfair-exchange canonical identifiers), §5 §5.4 (soft-book racing canonical identifiers populated at commit via `betfair_client` resolution), §6 §6.3 (line-resolution to Betfair market-id pattern at staging) all directly implement the Session 42 architectural extension. Position A discipline preserved.
- **Cat 5 (software questions are Claude's)** — held. The §4/§5/§6 schema shapes, the customer_ref transient-vs-permanent call, the snapshot floor scope, the operator_line_side decision-context capture — all Claude's calls (proposed for confirmation). Operator confirmed direction; technical detail handled inside the artefact.
- **Cat 5 (operator working-style — memory edit #16)** — held throughout. Strategic questions one per round; technical detail in the artefact. Round 4 reversal demonstrated reassessment-on-pushback rather than dressing a marginal recommendation as no-cost.

## Open items in (carried forward + new)

New from Session 71: **§2.8 §8/§9/§10 unfinished** — read-time resolution paths, immutability + reconciliation events, what this closes. Plus one structural carry-forward: §7 physical-file ordering moves to after §6 at end-of-§2.8 close (Session 72 mechanical edit).

Carry-forward (unchanged structure):

- **§2.6 settlement model** — unfinished, race path TBD.
- **§2.7 API contract versioning** — unfinished; two module contracts.
- **§2.8 bet-schema reframing** — **§1, §2, §3, §4, §5, §6, §7 locked. §8/§9/§10 to draft Session 72.** Brief at `dr029/2_8_bet_schema/2_8_bet_schema.md` (521 lines).
- **§2.9 write-side bet-entry coherence** — unfinished. §3 + §4 + §5 + §6 in §2.8 substantially feed §2.9; staging-vs-commit model is shared.
- **§2.10 external analytics scan** — substantially fed by probe; inventory writeup remaining. EX_LADDER entitlement question now formally noted in §2.8 §4.2 carry-forward to §10.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records. **Now load-bearing in §2.8 §2.2, §4.1, §5.4, §6.3.** Continues to carry forward — `architecture.md` formal sub-section update post-§2.8 close is administrative cleanup, not gating.
- Standard non-gating items: Fix 9, Fix 10, three-row collision triage, low-confidence match review, durable Fix 8 merge tooling, session numbering slip, **EX_LADDER entitlement question** (now formally referenced in §2.8 §4.2), drift-check methodology gap, bethub-analytical activation, post-DR-029 monitoring, BSP-fix code findings (c) and (d), BetWatch await (no longer gating per §2.5 deferral), Betfair API tiers, PASSIVE bet-delay handling, standing_instructions.md re-upload.
- Gaps from earlier reviews logged for awareness: Claude-67 G1–G4, Fresh-Claude E1.

## Open items out

Closed this session:

- **§2.8 §4 (Betfair exchange bet records)** — locked Session 71.
- **§2.8 §5 (soft-book racing bet records)** — locked Session 71.
- **§2.8 §6 (soft-book sports bet records)** — locked Session 71.
- **§4 customer_ref retention question** — locked transient-only, not on bet record.
- **§4 at-placement snapshot scope question** — locked floor-only, with EX_LADDER carried forward to §10 as not-gating.
- **§5 soft-book identity field-set question** — locked `soft_book_id` only.
- **§6 operator_line_side capture-vs-derive question** — locked captured-at-placement-commit.
- **Promo specificity capture clarification** — confirmed the cycle record's `promo_terms` block is the canonical store; bet record reference is one join away.

## Session close state

- **Rebuild folder root:** 12 `.md` files + `openapi.json` + `external_api_resources.md` + `.DS_Store` + `v3_build_picture.md`. All directories present. **No new directories created this session.**
- **`current_state.md`:** updated by close ritual to reflect Session 72 forward routing (§8/§9/§10 anchor).
- **`v3_build_picture.md`:** **updated this close.** §2.8 detail block updated to reflect §4/§5/§6 locked Session 71. No `done` carries to drop this close (no streams moved to `done` Session 70 or 71).
- **`standing_instructions.md`:** unchanged this session.
- **`dr029/2_8_bet_schema/2_8_bet_schema.md`:** **updated this session.** 300 → 521 lines. Status: drafting; §1, §2, §3, §4, §5, §6, §7 locked; §8/§9/§10 to draft Session 72.
- **`dr029/dr029_scope.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session. Will need update post-§2.8 close to formalise the Session 42 architectural extension as a sub-section under §D12.
- **`decisions.md`:** unchanged this session.
- **`sessions/`:** Session 71 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 71 opening prompt removed at close; Session 72 opening prompt to be written.
- **Project knowledge base:** unchanged this session. Carry-forward action: `standing_instructions.md` re-upload from Session 65.
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** *"Yep, let's close up and set up the next session."* in response to Claude's recommendation that 7 of 10 sections are locked, the brief is mechanically ~70% complete, and §8/§9/§10 are mechanical descriptions of mechanisms already established in §1–§7 fitting comfortably in a single follow-up session.

**Session 72 primary deliverable: complete §2.8 brief — §8 read-time resolution paths, §9 immutability discipline + reconciliation events, §10 what this closes for DR-029. Plus mechanical reordering of §7 to sit physically after §6 in the file.**

Sequence:

1. **First work:** read `dr029/2_8_bet_schema/2_8_bet_schema.md` to re-establish §1–§7 context (especially the cycle record + free bet ledger spec in §7 because §8 read-time resolution paths reference cycle attribution and consumption-event traversal); `dr029/dr029_scope.md` §2.8 for scope reminder.
2. **§7 physical reordering** — move §7 from its current position (between §3 and §4) to after §6. Single mechanical edit. Could happen at session start or as part of the close-out write at end-of-§2.8.
3. **§8 read-time resolution paths** — for each derivable field (race classification, runner metadata, finish position, market curve, BSP, field size, settlement payout, cycle attribution, parent linkage), name the read-time resolution path: which client (`vps_client`, `betfair_client`), which join key, what fallback applies. Per DR-019 (derived state on read). The bet-record-to-cycle-to-promo-terms join is one of the more load-bearing examples; the bet-record-to-free-bet-ledger consumption-event traversal for parent attribution is another.
4. **§9 immutability discipline + reconciliation events** — append-only fields enumerated; amendable fields enumerated; reconciliation event shape specified (event_type, target_bet_id, amended_field, old_value, new_value, reason, audit_timestamp); operator-override path through reconciliation events with audit trail.
5. **§10 what this closes for DR-029** — closure section. What §2.8 unblocks (§2.9 write-side coherence, §2.7 API contract versioning on the bet-record shape). EX_LADDER entitlement question carried forward as not-gating. Session 42 architectural extension formally landed as load-bearing contract. Post-§2.8 administrative cleanup items (architecture.md §D12 sub-section update, §7 physical reordering) named.
6. **Section-by-section per Cat 1 default cadence.** Likely covers all three sections plus §7 reordering Session 72.
7. **Out of scope for Session 72:** §2.6, §2.7, §2.9, §2.10 (until §2.8 closes); anything outside §2.8.

**Operator-side actions between sessions:**

1. **(Carry-forward)** Re-upload `standing_instructions.md` to the bethub-rebuild Claude Project knowledge base if not yet done from Session 65.
2. **(Optional, low priority)** Investigate Betfair API membership tiers.
3. **(Optional)** Awaiting BetWatch response — no longer gating; informs future operational-soft-book DR.
4. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.

## Close-out notes

Single morning sitting, ~27 min wall-clock. Three sections locked across three strategic-call rounds — tighter cadence than Session 70 because the strategic shape locked Session 70 made §4/§5/§6 mechanical applications across three bet types rather than fresh architectural-shape work.

Three strategic calls landed cleanly with one notable working-style moment: the Round 4 reversal on §5's soft-book identity (B → A after operator pushback). Claude initially framed `soft_book_bet_reference` as "costs nothing if skipped" — not the honest assessment. Operator effort to type per-book bet receipts is non-zero; the field's value was gated on a not-yet-scoped feature; inconsistent population would force fuzzy-matching anyway. Operator's pushback ("can you just give a simple scenario or two...") forced the honest reassessment that produced the correct recommendation. Worth holding onto: when a field's day-one value is "future feature might use this", scrutinise the operator-effort cost before recommending.

The §2.8 brief is now 7 of 10 sections locked. §8/§9/§10 are descriptive sections on mechanisms already established in §1–§7 — read-time resolution describes the read-side of the operational/analytical split already structured into §2/§4/§5/§6; immutability + reconciliation describes the write-side discipline already established in §2.5 + §3.3; "what this closes" is the closure summary. Single Session 72 should close §2.8 entirely.
