# Session 72

**Title:** §2.8 (bet-schema reframing) brief locked end-to-end. §7 reordered to physical position after §6; §8 read-time resolution paths drafted (eleven derived fields plus summary); §9 amendment discipline drafted with universal-amendable model + reconciliation event log + cascade rules per operator's v2-experience direction; §10 closure section drafted naming what §2.8 unblocks (§2.9, §2.7), what lands as load-bearing contract (Session 42 architectural extension, universal-amendable model, cheap-to-capture / expensive-to-reconstruct principle), and four carry-forward items (EX_LADDER entitlement, architecture.md §D12 sub-section update, complete cascade map as parked deliverable, CLV reframed as analytical-layer signal). Brief now 779 lines, all 10 sections locked.
**Opened:** 2026-05-04 07:45 ACST
**Closed:** 2026-05-04 08:06 ACST
**Wall-clock:** ~21 min substantive single sitting. Same-workday open relative to Session 71's 07:36 ACST close (~9 minute gap).
**Tool routing:** Claude Chat. No Code routing.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring), DR-019 (derived state on read — load-bearing for §8), DR-026 (inline snapshot exception on bet records — load-bearing for §9 amendment discipline).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-04 07:45 ACST`.
Close: same command → `2026-05-04 08:06 ACST`.

Same-workday open relative to Session 71's 07:36 ACST close. ~9 minute gap. Single morning sitting, immediate continuation.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 12 `.md` files + `openapi.json` + `external_api_resources.md` + `.DS_Store` + `v3_build_picture.md`. All directories present.
- `.close_out_backups/` contained `SESSION_72_opening_prompt.md` only (Session 71 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-04 07:36 ACST` matched Session 71 close; `sessions/SESSION_71.md` present (202 lines); `v3_build_picture.md` last-updated `2026-05-04 07:36 ACST` matched Session 71's §2.8 detail block update.
- Same-workday recap delivered (tight: Session 71 locked §4/§5/§6; Session 72 closes §2.8 with §8/§9/§10 + §7 reordering).
- V3 build picture: skipped silently per condition (streams did not move between Session 71 close and Session 72 open, ~9 minute gap).
- Open-items delta: skipped silently per condition. Operator flagged at open that `standing_instructions.md` re-upload to project knowledge base was completed — long-standing carry-forward from Session 65 retires this close.

## Session shape

Session 72 was a **brief-completion session** — closing the §2.8 brief end-to-end per Session 71 forward routing. Four pieces of work landed: §7 mechanical reordering (single-edit structural cleanup), §8 read-time resolution paths drafted, §9 amendment discipline drafted, §10 closure section drafted.

Session was tighter than Session 71 (~21 min wall-clock vs ~27 min) because §8/§9/§10 were descriptive sections on mechanisms already established in §1–§7 — no fresh architectural-shape work, just structured naming of behaviours already implicit in earlier sections. The exception was §9, where the operator's v2-experience input redirected the planned strict-amendment approach to a universal-amendable model with cascade rules; that strategic call was load-bearing and changed §9's shape substantially from the pre-draft framing.

Round-by-round shape:

**Round 1 (§7 reordering — recommended at session start, executed immediately).** Operator handed off route choice ("whatever you recommend"). Claude recommended §7 reordering first as a clean mechanical edit before drafting §8/§9/§10, on the rationale that §8 references §7 heavily (cycle attribution, free bet ledger consumption-event traversal) and having §7 sit immediately above §8 in the file makes cross-references read cleanly. Two `Desktop Commander:edit_block` operations: delete §7 + bracketing separators from between §3 and §4 (line 224 → 295 inclusive); append §7 + leading separator at end-of-file after §6.7. Pre-write dry-run summary delivered per Cat 3. Post-write `grep -n "^## "` confirmed clean physical order §1 → §2 → §3 → §4 → §5 → §6 → §7. Line count steady at 521 (no content change, just relocation).

**Round 2 (§8 strategic call — field list).** Claude proposed eleven derived fields drawn from §1–§7 cross-references and DR-019 scope: race classification, runner metadata, finish position, market curve, BSP, field size, settlement payout, cycle attribution, parent linkage, sports event metadata, sports settlement detail. Operator approved the list and asked Claude to do a quick web scan to check for missed fields, anchored on the cheap-to-capture / expensive-to-reconstruct principle.

**Round 3 (web scan + §8 field list refinement).** Two web searches run. First scan (race-data-and-EV-tracking schemas) returned conventional bet-record fields plus heavy form-analysis content (sectional times, sire data, ratings) — all downstream analytical-layer concerns, none operational read-time fields. Second scan (EV tracking + commission/Rule 4) surfaced two genuine candidates: CLV (closing line value — leading analytical signal for value-betting model validation) and Rule 4 / Betfair commission deductions. Claude recommended adding CLV as a 12th derived field, and addressing Rule 4 + commission as captured-implicitly-via-payout-and-pnl (no extra storage; gross/net decomposition lives in capture.db's settlement event capture per analytical-line). Operator approved both.

**Round 4 (§8 drafted and written).** §8 written via single `Desktop Commander:edit_block` append. Twelve sub-sections covering eleven derived fields plus the §8.13 resolution path summary. File grew 521 → 639 lines (+117 — initial draft including §8.12 CLV).

**Round 5 (§9 strategic call — reconciliation event scope).** Claude proposed two options: (A) strict — reconciliation events fire only for settlement-side amendments and Betfair-exchange order-state amendments; (B) generous — universal log including path-(iii) promotions and operator-overrides on any field. Claude recommended (A). Operator pushed back hard with v2-experience direction: "Pretty much any field that's entered at some stage can conceivably be amended later on... As long as we have that capability and everything's flowed through correctly, I'm happy."

This was a load-bearing redirect. Claude reassessed and confirmed the generous-amendment model is operationally correct — v2 reality drove amendments across odds, bookmaker, promotion type, account, and so on, not just settlement-side. The brief's §9 shape changed from option-A-with-strict-fields to universal-amendable-with-cascade-rules. Claude walked through five concrete cascade scenarios from operator's v2 experience (price_taken, account_at_book_id, promo_cycle_id, bet_type/soft_book_id, stake) to validate the cascade-logic-is-key direction.

**Round 6 (§9 drafted and written).** §9 written via single `Desktop Commander:edit_block` append. Six sub-sections: §9.1 amendment principle, §9.2 reconciliation event schema, §9.3 what gets a reconciliation event, §9.4 cascade rules (eight named cascades), §9.5 operator-facing surface, §9.6 what §9 does not cover. File grew 639 → 753 lines (+114).

**Round 7 (operator clarifications on CLV and cascade map).** Operator surfaced two refinements after §9 was written:

- **CLV is fully derivable at the analytical layer** and does not need to be in the operational read-time path. Including §8.12 CLV crossed the line Claude itself drew between operational read-time resolution and analytical-layer signals.
- **Cascade map is incomplete** — §9.4 names the well-understood cases, but the complete map (every conceivable amendment path on every field on every record) is its own piece of work, best done once v3 build is far enough along to test against actual write paths.

Claude agreed on both. CLV reframed as a downstream analytical-layer signal in §10.3 carry-forward; complete cascade map added as parked deliverable in §10.3.

**Round 8 (§8.12 CLV deletion + stale-reference cleanup + §10 drafted and written).** Three edits to land the refinements:

1. `Desktop Commander:edit_block` deletion of §8.12 CLV body, leaving §8.12 (Resolution path summary) renumbered from §8.13 in place.
2. `grep -n "CLV"` scan caught two stale references: §8 framing line 527 and §8.5 BSP failure-mode line 574. Both cleaned via `Desktop Commander:edit_block`.
3. §10 drafted and written via single `Desktop Commander:edit_block` append. Four sub-sections: §10.1 what §2.8 unblocks (§2.9, §2.7), §10.2 what §2.8 lands as load-bearing contract, §10.3 carry-forward items not gating (EX_LADDER, architecture.md §D12 sub-section, complete cascade map, CLV as analytical signal, path-(iii) reconciliation-job UI), §10.4 what §2.8 does not do.

Final state: file at 779 lines. All 10 sections locked. Post-write `grep -n "^## "` confirmed clean structure.

**Round 9 (close confirmation).** Operator confirmed close: "Yes, please close this session up and prepare for next session."

## What was delivered

### 1. §2.8 brief — final three sections + reordering, brief locked end-to-end

Brief at `dr029/2_8_bet_schema/2_8_bet_schema.md` now 779 lines, all 10 sections locked. Session 72 contributions: §7 reordered, §8 drafted (now 11 derived fields + summary), §9 drafted (universal-amendable model), §10 drafted (closure section).

**§7 reordering.** Mechanical structural cleanup. §7 (cycle record + free bet ledger specifications) moved from physical position between §3 and §4 to physical position after §6. Two `Desktop Commander:edit_block` operations. Pre-write dry-run summary delivered. Post-write verification confirmed clean physical order §1 → §2 → §3 → §4 → §5 → §6 → §7. No content change.

**§8 read-time resolution paths.** Eleven sub-sections covering eleven derived fields plus §8.12 resolution path summary. Per DR-019 (derived state on read), every field that can be reconstructed from the analytical line at read time resolves there rather than being stored on the bet record. Per field: which client (`vps_client` against `capture.db` as default; `betfair_client` for live-API fallback), which join key (Betfair canonical identifiers from §2.2), which fallback applies, what the failure mode is. Fields covered: race classification, runner metadata, finish position, market curve, BSP, field size, settlement payout detail (with Rule 4 + commission named as captured-implicitly-via-payout-and-pnl), cycle attribution, parent linkage, sports event metadata, sports settlement detail. CLV originally drafted as §8.12 then dropped per operator clarification (CLV is analytical-layer, not operational read-time path).

**§9 amendment discipline.** Universal-amendable model: every field on every record (bet, cycle, generation, consumption) amendable via reconciliation events with cascade flow-through. Six sub-sections: §9.1 amendment principle (audit trail preserved, cascade rules fire automatically, read-time consumers see current value), §9.2 reconciliation event schema (`reconciliation_id`, `event_type`, `target_record_type`, `target_record_id`, `amended_field`, `old_value`, `new_value`, `reason`, `parent_reconciliation_id`, `operator_initiated`, `audit_timestamp`), §9.3 what gets a reconciliation event, §9.4 cascade rules (eight named cascades — `price_taken`, `stake`, `account_at_book_id`, `bet_type`/`soft_book_id`, `promo_cycle_id`, Betfair canonical identifiers, settlement fields, cycle terms, generation `face_value`, consumption events), §9.5 operator-facing surface, §9.6 what §9 does not cover. Cascade-derived events linked back to triggering amendment via `parent_reconciliation_id`. Ambiguous cascades (would silently delete or invalidate a downstream record) surface flags for operator review rather than auto-resolving.

**§10 what §2.8 closes for DR-029.** Closure section. Four sub-sections: §10.1 what §2.8 unblocks (§2.9 write-side coherence, §2.7 API contract versioning), §10.2 what §2.8 lands as load-bearing contract (Session 42 architectural extension as locked schema, universal-amendable model, cheap-to-capture / expensive-to-reconstruct principle), §10.3 carry-forward items not gating (EX_LADDER / SP-actual entitlement question, architecture.md §D12 sub-section update, complete cascade map as parked deliverable post-DR-029, CLV as downstream analytical-layer signal, path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI), §10.4 what §2.8 does not do (consumer-side UI, soft-book operational layer, atomicity/transaction boundaries on the cascade, settlement source priority and 90-minute fallback machinery).

### 2. Strategic decisions locked

Two strategic decisions confirmed by the operator and locked into the brief:

1. **Universal-amendable model adopted for §9.** Operator's v2 experience (odds, bookmaker, promotion type, account, stake all needed amending in v2 across operational reality) drove the call away from a strict-fields-only reconciliation log to a generous model where every field on every record is amendable. Cascade rules are explicit, with ambiguous cases surfacing operator-review flags rather than auto-resolving.
2. **CLV reframed as analytical-layer signal, not operational read-time field.** §2.8 commits to the operational data layer; CLV is built post-DR-029 alongside the wider analytical layer. Honest scope discipline.

### 3. Working-style adherence

Memory edit #16 ("strategic decisions surfaced; technical detail in the artefact") held throughout. The Round 5 reconciliation-event-scope question was the one place where Claude's recommended option (A strict) didn't survive operator pushback — operator's v2-experience direction was load-bearing and re-shaped §9. The Round 7 CLV and cascade-map clarifications were operator-initiated honest-scope-discipline corrections that Claude agreed with on first pass.

### 4. §2.8 brief now load-bearing input for §2.9 and §2.7

§2.9 (write-side bet-entry coherence) is now writable — §2.8's bet record contract, staging-vs-commit flow, and cascade rules feed §2.9's atomicity work. §2.7 (API contract versioning) on the bet-record-side is also writable. Session 73 forward routing recommends §2.9 as primary candidate; §2.6 (settlement model — race path), §2.7, §2.10 (external analytics scan inventory writeup) all remain in play.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021, DR-019, DR-026 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (tight, ~9 minute gap).
- **Cat 1 (V3 build picture conditional render)** — skipped silently at open per condition. To be updated at this close (§2.8 stream moved from `in flight` to `done`).
- **Cat 1 (open-items delta)** — skipped silently at open per condition. Operator flagged `standing_instructions.md` re-upload completed; that long-standing carry-forward retires at this close.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. Round-by-round cadence with one strategic question per round.
- **Cat 1 (decision-maker framing)** — held. Each round led with the call or recommendation.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. When operator handed off route choice ("whatever you recommend") at session start, Claude recommended §7 reordering first and proceeded immediately rather than re-litigating the choice.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders. EX_LADDER, DSC-0018, FIFO, BSP unwound on use.
- **Cat 1 (escalate to detail only when warranted)** — held. The Round 7 CLV and cascade-map clarifications were operator-initiated and warranted; Claude provided concrete cascade examples (five from operator's v2 experience) at the right depth without escalating beyond that.
- **Cat 1 (line-break rendering for review content)** — n/a; no fenced review blocks delivered this session.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open.
- **Cat 2 (Desktop Commander default)** — held. All file operations via `Desktop Commander:edit_block` (six append/replace operations) and `Desktop Commander:read_file` / `start_process` for verification. One sandbox-namespace gotcha hit early in the session (`view`, `str_replace`, `bash_tool` calls all failed before correctly routing to `Desktop Commander:read_file` and `Desktop Commander:edit_block`). Hit the namespace gotcha *again* at close-out when `create_file` for the session record landed in sandbox; recovered via `projects-filesystem:write_file`. Cat 2 / Cat 3 namespace discipline is the lesson worth holding onto — `create_file` is not the right tool for bethub-rebuild folder writes.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — n/a; no Python REPL work this session.
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; all session content written directly to canonical artefact during the session. No drafts left in chat history.
- **Cat 2 (Surface structural-drift in the session record)** — applies. §7 reordering this session (mechanical edit; no content change) is flagged in the §7 entry above. Two stale CLV references caught and cleaned post-§8.12 deletion via `grep -n "CLV"` scan — flagged here as a small structural-cleanliness item that succeeded.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — n/a this session; no API-shape questions surfaced.
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — applies. The §7 reordering involved two distinct file regions (deletion at lines 225–295 and append at end-of-file). Pre-write dry-run summary delivered per Cat 3 protocol; both edits executed cleanly.
- **Cat 3 (web search for external context)** — engaged. Two web searches run during Round 3 to validate the §8 field list against external EV-tracking conventions. Surfaced CLV and Rule 4 / commission as candidates worth raising; operator approved CLV addition (subsequently dropped per Round 7 honest-scope clarification) and Rule 4 / commission as captured-implicitly-via-payout-and-pnl.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary engaged in §8.13 (resolution path summary) — the bet record's Betfair canonical identifiers are the integration boundary into the analytical layer; the analytical layer joins back on the same identifiers; no caching, no denormalisation, no second integration point. DR-027/028 discipline preserved.
- **Cat 4 (operational/analytical line discipline)** — engaged throughout §8 and §10.3 (CLV reframing). The operational/analytical line distinction was load-bearing in the Round 7 CLV clarification — recognising CLV as analytical-layer signal rather than operational read-time field is direct application of the discipline.
- **Cat 4 (Betfair-as-canonical-source extension)** — load-bearing this session. §8 read-time resolution paths anchor on Betfair canonical identifiers per §2.2 implementation; §10.2 names the Session 42 architectural extension as locked load-bearing contract (no longer flagged as future direction). Position A discipline preserved.
- **Cat 5 (software questions are Claude's)** — held. The §8 field list, the §9 reconciliation event schema, the §10 closure structure — all Claude's calls (proposed for confirmation). Round 5 reconciliation-event-scope was a software-question call that operator's operational-experience input redirected; the redirect was correct (operator's v2 experience is operational ground-truth, which is operator's territory per Cat 5).
- **Cat 5 (operator working-style — memory edit #16)** — held throughout. Strategic questions one per round; technical detail in the artefact. Round 5 reconciliation-event-scope question was framed as a clean A-vs-B choice with Claude's recommendation surfaced for operator confirmation; operator's redirect on the question was the correct outcome.

## Open items in (carried forward + new)

New from Session 72:

- **Complete cascade map** (parked) — every conceivable amendment path on every field on every record, with cascade behaviour and review-flag surfaces enumerated. §9.4 names the well-understood cases; the complete map is its own piece of work, best done post-DR-029 once v3 build is far enough along to test against actual write paths.
- **CLV as analytical-layer signal** (not gating) — built post-DR-029 alongside the wider analytical layer; the operational data layer enables it via Betfair canonical identifiers + `price_taken` + capture.db's BSP and pre-jump price-snapshot tables.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** (not gating) — operational design downstream of v3 build proper.

Carry-forward (unchanged structure, with one retirement):

- **§2.6 settlement model** — unfinished, race path TBD.
- **§2.7 API contract versioning** — unfinished; two module contracts. **Bet-record-side §2.7 work is now writable per §2.8 §10.1.**
- **§2.8 bet-schema reframing** — **CLOSED Session 72.** All 10 sections locked. Brief at `dr029/2_8_bet_schema/2_8_bet_schema.md` (779 lines).
- **§2.9 write-side bet-entry coherence** — unfinished. **Now writable per §2.8 §10.1 — recommended Session 73 primary candidate.** §2.8's bet record contract, staging-vs-commit flow, and cascade rules feed §2.9's atomicity work.
- **§2.10 external analytics scan** — substantially fed by probe; inventory writeup remaining. EX_LADDER entitlement question now formally noted in §2.8 §4.2 carry-forward to §10.3.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records. **Now LOCKED LOAD-BEARING in §2.8 §10.2.** Continues to carry forward as administrative cleanup — `architecture.md` §D12 formal sub-section update post-§2.8 is named as a §10.3 carry-forward item.
- Standard non-gating items: Fix 9, Fix 10, three-row collision triage, low-confidence match review, durable Fix 8 merge tooling, session numbering slip, **EX_LADDER entitlement question** (now formally noted in §2.8 §10.3), drift-check methodology gap, bethub-analytical activation, post-DR-029 monitoring, BSP-fix code findings (c) and (d), BetWatch await (no longer gating per §2.5 deferral), Betfair API tiers, PASSIVE bet-delay handling.
- **`standing_instructions.md` re-upload — RETIRED this close.** Operator flagged at session open that the re-upload was completed. Long-standing carry-forward from Session 65 closes.
- Gaps from earlier reviews logged for awareness: Claude-67 G1–G4, Fresh-Claude E1.

## Open items out

Closed this session:

- **§2.8 §7 (cycle record + free bet ledger) physical reordering** — moved to physical position after §6.
- **§2.8 §8 (read-time resolution paths)** — locked Session 72.
- **§2.8 §9 (amendment discipline + reconciliation events + cascade rules)** — locked Session 72.
- **§2.8 §10 (what this closes for DR-029)** — locked Session 72.
- **§2.8 brief end-to-end** — CLOSED Session 72.
- **Reconciliation-event-scope strategic question** — locked universal-amendable model per operator v2-experience direction.
- **CLV inclusion question** — locked as analytical-layer signal, not operational read-time field; reframed in §10.3 carry-forward.
- **`standing_instructions.md` re-upload (Session 65 carry-forward)** — RETIRED. Operator confirmed completion at session open.

## Session close state

- **Rebuild folder root:** 12 `.md` files + `openapi.json` + `external_api_resources.md` + `.DS_Store` + `v3_build_picture.md`. All directories present. **No new directories created this session.**
- **`current_state.md`:** to be updated by close ritual to reflect Session 73 forward routing (§2.9 primary candidate; §2.6, §2.7, §2.10 also in play).
- **`v3_build_picture.md`:** **to be updated this close.** §2.8 stream moves from `in flight` to `done`. §2.9 detail block updated to reflect now-unblocked status. No prior-session `done` carries to drop this close.
- **`standing_instructions.md`:** unchanged this session.
- **`dr029/2_8_bet_schema/2_8_bet_schema.md`:** **updated this session.** 521 → 779 lines (+258). Status: complete. All 10 sections locked.
- **`dr029/dr029_scope.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session. Will need update post-DR-029 to formalise the Session 42 architectural extension as a sub-section under §D12 (named as §10.3 carry-forward).
- **`decisions.md`:** unchanged this session.
- **`sessions/`:** Session 72 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 72 opening prompt removed at close; Session 73 opening prompt to be written.
- **Project knowledge base:** `standing_instructions.md` re-upload completed by operator at session start (Session 65 carry-forward retires).
- **VPS state:** unchanged this session.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** *"Yes, please close this session up and prepare for next session."* in response to Claude's notice that §2.8 brief is locked end-to-end and Session 73 picks up §2.9 as primary deliverable.

**Session 73 primary deliverable: §2.9 (write-side bet-entry coherence) brief drafting.** §2.9 specifies atomicity guarantees, transaction boundaries, and the integrity-layer flagging surface across the multi-record write paths surfaced in §2.8 — bet record + cycle record (when first-of-cycle) + free bet ledger consumption events (when funding_source = free-bet-pool) + cascade reconciliation events at amendment time. §2.8's bet record contract, staging-vs-commit flow (§3), and cascade rules (§9.4) are the load-bearing inputs.

Sequence:

1. **First work:** read `dr029/2_8_bet_schema/2_8_bet_schema.md` to re-establish the bet-record contract context (especially §3 staging/commit, §7 cycle and ledger, §9 cascade rules); `dr029/dr029_scope.md` §2.9 for scope reminder.
2. **§2.9 framing** — what the write side needs to guarantee: atomicity across the bet/cycle/consumption multi-record write at placement-commit (§3.3 step 3–5); atomicity across cascade-derived multi-record amendments (§9.4); integrity-layer flagging surface for ambiguous cascades. Draft the framing section, walk operator through.
3. **Section-by-section per Cat 1 default cadence** — write-side write paths, cascade execution semantics, integrity-layer flag surface, what §2.9 closes.
4. **Out of scope for Session 73:** §2.6, §2.7, §2.10 (until §2.9 closes); anything outside §2.9.

**Alternative routing if operator prefers:** §2.7 (API contract versioning on bet-record-side) or §2.10 (external analytics scan inventory writeup) are also writable as Session 73 primary deliverables. §2.6 (settlement model — race path) is unfinished and remains in play. Session 73's open ritual will surface the choice; operator's call.

**Operator-side actions between sessions:**

1. **(Optional, low priority)** Investigate Betfair API membership tiers — informs EX_LADDER / SP-actual entitlement question carried forward in §2.8 §10.3.
2. **(Optional)** Awaiting BetWatch response — no longer gating; informs future operational-soft-book DR.
3. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.
4. **(Optional)** Review §2.8 brief end-to-end at leisure (between-session work; not a Session 73 blocker).

## Close-out notes

Single morning sitting, ~21 min wall-clock. §2.8 closed end-to-end across four pieces of work (§7 reordering + §8 + §9 + §10) with two strategic decisions landed (universal-amendable model per operator v2-experience, CLV as analytical-layer signal per honest-scope-discipline reframe).

Two working-style moments worth holding onto:

- **Round 5 reconciliation-event-scope reversal.** Claude recommended option A (strict); operator's v2-experience direction redirected to option B-equivalent (universal-amendable). The redirect was correct — operator's operational reality is ground-truth on what v3 needs to handle, which is operator's territory per Cat 5. Claude reassessed cleanly and reshaped §9 around the cascade-logic-is-key direction. Pattern: when operator's pushback is grounded in operational experience rather than scope or aesthetic preference, the reassessment should be substantive, not cosmetic.
- **Round 7 CLV scope-discipline correction.** Operator caught that §8.12 CLV crossed the operational/analytical line Claude itself drew between operational read-time resolution and analytical-layer signals. Claude agreed cleanly on first pass and reframed CLV in §10.3 carry-forward. Pattern: when operator catches a scope-discipline drift, agree clean and fix; don't dress it up.

§2.8 brief is now load-bearing input for §2.9 and §2.7. Session 73 picks up from here.
