# Session 90

**Title:** DR-032 (Betfair as canonical reference layer for all bet records — bet-record / bet-leg schema, immutable logging-time snapshots, no fuzzy-matching at logging time) drafted and locked at `decisions.md`; `architecture.md` §A.10 (Canonical source identifiers — Betfair as the reference layer) drafted and landed alongside as the architectural-principle home that DR-032 cites; phantom-`§D12`-anchor governance gap surfaced and closed (the principle had been cited across ~10 sessions without ever existing as a real heading); cross-reference integrity gap logged as a candidate Cat 2 standing-instruction addition for the next sweep.
**Opened:** 2026-05-06 12:40 ACST
**Closed:** 2026-05-06 14:22 ACST
**Wall-clock:** ~1h42m active session work. Same-workday open relative to Session 89 close (~63 min gap, single-sitting continuation). No pause-and-resume; no day rollover; no split triggers fired.
**Tool routing:** Claude Chat (DR-032 design conversation; §A.10 + DR-032 drafting; close-out). No Claude Code work this session. All file ops via Desktop Commander.
**Governing DRs invoked:** DR-027 (two-database architecture), DR-028 (cross-DB integration boundary), DR-026 (at-log-time market snapshot pattern), DR-022 (account / book / account-at-book vocabulary), DR-019 (derived state on read), DR-030 (v3 repo layout — load-bearing for W4), DR-031 (v3 tech stack), DR-021 (Adelaide local time). Plus Session 42 architectural extension flag — **now formally landed as DR-032.**

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-06 12:40 ACST`.
Close: same command → `2026-05-06 14:22 ACST`.

Same-workday open relative to Session 89 close at 11:37 ACST (~63 min gap, fresh chat continuation after a short break).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, calibrated against Cat 1 silent-ritual instruction:

- Rebuild root: 12 expected `.md` files, `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_90_opening_prompt.md` only (Session 89 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-06 11:37 ACST` matched Session 89 close; `sessions/SESSION_89.md` present (209 lines); `v3_build_picture.md` last-updated `2026-05-06 11:37 ACST` matched Session 89 close.
- Same-workday recap delivered at 63 min gap.
- V3 build picture: skip-silent at open (no streams moved between Session 89 close and Session 90 open).
- Open-items delta: skip-silent at open (no items closed/opened/overdue in the gap).
- Governing DRs named at open: DR-027, DR-028, DR-030, DR-031, DR-021, DR-019, DR-022, plus Session 42 architectural extension flag carried forward.

## Session shape

Session 90 was a **substantive design session** — formalising the Session 42 architectural extension into a numbered decision record. Per Cat 1 call-driven and per current_state.md "What's next", the session ran as a sequence of discrete operator-facing design calls leading to a fully-shaped DR ready for drafting, then drafted both the DR and a companion architecture sub-section to disk.

The session also surfaced a real governance gap mid-design: the `architecture.md §D12` anchor that ~10 prior sessions had cited as load-bearing did not exist as a heading anywhere. The principle had been propagating via shorthand against a phantom anchor. Surfaced honestly, addressed in-session (the principle landed as `architecture.md §A.10` rather than as a fabricated `§D12`), and the cross-reference integrity gap logged as a candidate Cat 2 standing-instruction addition for the next standing-instructions sweep.

Eight design rounds before drafting:

**Round 1 — open + Call 1 routing.** Same-workday open ritual. Call 1: extension lives where? Option A (extend `architecture.md` §D12) vs Option B (fresh DR-032 with own scope and lock). Claude recommended B; operator confirmed B.

**Round 2 — Call 2 identifier shape.** Set A (minimal — just market + selection IDs), Set B (minimal + denormalised display fields), Set C (full Betfair envelope). Claude recommended B; operator confirmed B with framing "BetFair data as the blanket data for all bets so they can all be matched and grouped easily and without fuzzy-ness."

**Round 3 — Call 3 soft-book resolution paths.** Path 1 (operator-driven, racing-screen handles it), Path 2 (fuzzy match at entry, operator confirms), Path 3 (deferred resolution). Operator surfaced two material corrections that reframed the call: (i) soft-book bets don't always have a Betfair hedge — many are standalone — and Betfair identifiers attach for *standardisation*, not because of a hedge; (ii) the racing screen is already Betfair-driven, selections are made through the Betfair API even when no Betfair bet is placed, so identifiers ride along from racing-screen click to modal automatically. Path 1 was correct shape; Claude's framing of it was wrong (described it as if there was something to resolve — there isn't). Reframed: identifiers inherit from entry path, no resolution logic, no fuzzy-match.

**Round 4 — Confirm 1 (entry paths) + Confirm 2 (Betfair-no-market case).** Operator confirmed: racing and sports are the only entry paths in v3 (each defined separately in flow + UI); hard rule that soft-book bets must have a Betfair market available (no fallback path; out-of-scope edge cases stay out of scope).

**Round 5 — Call 4 cross-DB boundary implications.** DR-027 / DR-028 unaffected by DR-032; the canonical-source pattern sits cleanly under both. Set B's denormalised display fields are immutable logging-time snapshots, not refreshable cache (DR-028 holds). Operator confirmed: "the key joiners are always the BetFair market id and selection id. They should link all operational and analytical data where required."

**Round 6 — operator-prompted problem-check.** Operator asked: "do you see any problems with the approach we've designed here?" Claude surfaced three genuine problems: (1) racing screen Betfair-keying assumed but not yet a locked W7 substrate; (2) SGM / multi-leg bets don't fit cleanly into the single-`(marketId, selectionId)` shape; (3) Racing API ↔ Betfair joins not as easy as assumed. Operator corrected each:

- Problem 1 dissolved: Racing API is analytical-line only by architecture; the racing screen for bet placement is Betfair-keyed by architecture, not by W7 design choice.
- Problem 2 — operator confirmed SGMs need multiple `selectionId`s attached, with line-by-line entry. Reframed Claude's earlier recommendation: not v1-scope-down to single-selection, but bet record carries an array of `(marketId, selectionId)` pairs — single-selection bets are arrays of one.
- Problem 3 — operator asked whether matching should be rules-based at logging time vs capture-then-match-later via code. Claude recommended capture-then-match-later (Fix 5's rules-based experience demonstrates rules lag the data; defer matching to where most context is available).

**Round 7 — Call 5 SGM bet-record shape (operator-driven).** Operator asked the right follow-on question: does an SGM produce four rows total (one bet record + three legs)? Yes — bet record owns *bet-as-a-whole* properties (stake, soft-book combined SGM price, account, book-at-account, free-bet flag, strategy tag, settlement outcome), bet legs own *per-leg* properties (`betfair_market_id`, `betfair_selection_id`, denormalised display fields, leg-level Betfair-implied probability for SGM correlation analytics). Plus operator surfaced harness-as-thoroughbred edge case for the matching layer (signals: runner names, runner count, jump time; W1 F2 capture.db code-discriminator remediation tracked separately).

**Round 8 — Call 6 (operator-driven idempotence check).** Operator asked: "does that approach not double count anything? Stake margin, etc.?" Made the ownership split explicit: stake lives only on the bet record (never on legs); soft-book combined price lives only on the bet record (never on legs). Schema enforces idempotence structurally — legs table has no stake column, no combined-price column. Reporting and P&L queries always read against the bet record; legs are read for leg-level analytics only.

**Round 9 — pre-drafting governance check.** Pre-write read of `architecture.md` to find the §D12 anchor surfaced that no §D section exists at all in the file. Then verified across the project: `decisions.md`, `current_state.md`, `project_context.md`, `standing_instructions.md`, `dr029/2_8_bet_schema/`, multiple session records all cite `architecture.md §D12` as if it were a real heading. It isn't. Surfaced honestly to operator: this was a real governance gap, with phantom anchor referenced load-bearingly across ~10 sessions. Three options for resolution: X (write §D12 fresh in `architecture.md`), Y (retarget all references), Z (DR-032 as canonical, leave references). Operator: "wouldn't D12 be in the decision log?" — checked; not there either. Operator confirmed Option X. Claude's chosen placement: §A.10 (under the Reconciliation contract) rather than fabricating a §D section, because §A is the natural home for canonical-source discipline (joins, identifiers, reconciliation) and there's no §C/§D precedent in the file. Legacy `§D12` references will resolve to §A.10's content (a closing note in §A.10 names the legacy citation aging-out).

**Round 10 — drafting + close routing.** Claude drafted §A.10 (22 lines) to `architecture.md` and DR-032 (110 lines) to `decisions.md`, both via `Desktop Commander:edit_block` (§A.10) and `Desktop Commander:write_file` append (DR-032). Per Cat 1 call-driven, no operator-facing line-by-line review surfaced — the locked decisions carried the substance and review-in-chat at this length would be heavy reread. Both files post-write verified via wc -l + grep. Operator confirmed close-and-prepare-next-session.

## What was delivered

This session produced two substantive artefacts (DR-032, architecture.md §A.10) plus closed one ~10-session-old governance carry-forward.

### DR-032 written to disk

Located at `decisions.md` line 1081. 110 lines (including heading and trailing blank). Eight-clause locked stance:

1. Bet records carry Betfair-side identifiers as the canonical join key.
2. Two-table shape: bet record + bet legs.
3. Stake and combined price live exclusively on the bet record. Never on legs.
4. Set B denormalised display fields are immutable logging-time snapshots.
5. No resolution logic at logging time. Identifiers inherit from the entry path.
6. Hard rule: soft-book bets must have a Betfair market available at logging time.
7. Racing API ↔ Betfair joins are not at logging time.
8. Multi-leg correlation analytics fall out for free.

Plus six choices-considered-and-rejected, concrete schema sketch (`bets` and `bet_legs` table column lists), tradeoffs, scope (W4 / W4.1 / W6 implementation; W7 UI ports against the schema), and full cross-references (§A.10, §A.8, DR-027, DR-028, DR-026, DR-022, DR-019, §2.8 brief, Session 42).

### Architecture.md §A.10 (Canonical source identifiers — Betfair as the reference layer) written to disk

Located at `architecture.md` line 563, between §A.9 (Derivation rules) and §B (Operational layer). 22 lines. Five paragraph-shaped sub-clauses: the principle (event-domain authority + bet-record join keys); the rule for soft-book bets (entry-path inheritance, hard rule on Betfair-market availability); the rule for Racing API context (analytical-line only; capture.db-internal resolution); the cross-DB boundary (DR-027 / DR-028 unaffected); the locked schema commitment (cite DR-032). Plus a closing note that legacy `§D12` references resolve to §A.10.

### `architecture.md §D12` phantom-anchor governance gap surfaced and closed

The Session 42 architectural extension had been cited across ~10 sessions as `architecture.md §D12 (Betfair as canonical source)`. The reference appeared in: `architecture.md` line 689, `project_context.md` line 102, `standing_instructions.md` line 130, `current_state.md` (multiple lines), `dr029/2_8_bet_schema/2_8_bet_schema.md` (multiple lines), `dr029/2_10_external_analytics_scan/2_10_external_analytics_scan.md`, `dr029/dr029_scope.md`, `dr029/2_7_api_contract_versioning/contracts_spec_brief.md`, `dr029/w4_bet_entry/hedge_staking_math.md`, `work_in_progress.md`, and ~7 session records. The §2.8 brief's §10.3 carry-forward correctly flagged that `architecture.md §D12 sub-section update` was a known-pending administrative item — but the carry-forward stayed open across Sessions 73–89 because it was tagged "post-DR-029 administrative cleanup" and kept getting deferred.

**Resolution this session:** the principle landed as §A.10 (the natural home under the Reconciliation contract — §A.10 sits alongside §A.8 cross-DB integration and §A.9 derivation rules). DR-032 cites §A.10. Legacy `§D12` references resolve to §A.10's content; will be retargeted at the next documentation sweep without urgency.

**Cross-reference integrity gap logged as a candidate Cat 2 addition.** Surfaced as a candidate `standing_instructions.md` Cat 2 instruction for the next sweep:

> **Cross-reference integrity sweep at session close.** When a session writes new content that references heading-level anchors elsewhere (`architecture.md §X`, `decisions.md DR-N`, named brief sections), verify each reference resolves to an actual heading before close. Surface unresolved references in the session record and either land the missing anchor in-session or log it as a named follow-up with a target session, not as open-ended admin cleanup. Substrate: Session 90 surfaced that §D12 had been cited across ~10 sessions without ever existing as a heading; the gap propagated because the carry-forward discipline tagged it as low-priority admin rather than as an integrity gap.

Not landed this session (substantive sweep work, defer to next standing-instructions sweep). Logged in current_state.md "Pending operator-side actions" as a Claude-side carry-forward.

### Material substrate revisions vs Session 89

None. Session 90 ran against the locked substrates from Session 89 (math review §1–§7) and earlier sessions (Session 42 extension flag, §2.8 brief §10.2/§10.3 substrate). The only revision was the §D12 anchor's location (now §A.10), surfaced this session.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-030, DR-031, DR-021, DR-019, DR-022 named at open. Session 42 architectural extension flag named.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered at 63 min gap. Tight, no over-recap.
- **Cat 1 (V3 build picture conditional render)** — skipped silently at open (no streams moved between Session 89 close and Session 90 open).
- **Cat 1 (open-items delta)** — skipped silently at open (no movement in the gap).
- **Cat 1 (drift-check)** — done at open, all three checks matched.
- **Cat 1 (silent session-open ritual)** — held. Steps 1–5 silent; Steps 6–8 combined into single brief output at end.
- **Cat 1 (silent session-close ritual)** — holding this close. Steps 1–10 silent; Step 11 produces brief verification line.
- **Cat 1 (call-driven surfacing during section-by-section drafting)** — held throughout. Eight discrete operator-facing design calls before drafting, each surfacing only the operator-relevant choice. Drafting itself ran without per-section calls (Cat 1 — call-driven means surfacing only when there's a call, not artificial section ritual).
- **Cat 1 (short responses, plain language)** — held throughout. Some longer responses where operator opted into detail (problem-check round, governance-gap round) — Cat 1 escalate-to-detail-when-warranted permits this.
- **Cat 1 (decision-maker framing)** — held. Each call led with the choice; Claude's recommendation followed; operator's decision went next.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. Operator said "lets go" at session start; Claude proceeded directly to Call 1. Operator confirmations on Calls 2–5 were directly actioned.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders; technical terms (DR-032, §A.10, `betfair_market_id`, `selectionId`, Set A/B/C, Path 1/2/3, Construction A vs B, etc.) unwound where they appeared in operator-facing framing.
- **Cat 1 (escalate to detail only when warranted)** — held. Problem-check round (Round 6) explicitly escalated to detail at operator request; governance-gap round (Round 9) escalated to detail because the gap was genuinely material.
- **Cat 1 (line-break rendering for review content)** — n/a; no review content blocks rendered to chat this session.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout. Some longer rounds were warranted by content (problem-check, governance-gap); brevity default held elsewhere.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. No pause-and-resume.
- **Cat 2 (pre-flight directory listing)** — done at open.
- **Cat 2 (Desktop Commander default)** — held. All file ops via `Desktop Commander:read_file`, `Desktop Commander:start_process` (grep / wc / awk), `Desktop Commander:edit_block` (§A.10 insertion), `Desktop Commander:write_file` (DR-032 append in two writes).
- **Cat 2 (REPL discipline)** — n/a; no REPL work this session. All shell calls were one-shot grep / awk / wc commands.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)** — held. All writes via `Desktop Commander:write_file` or `Desktop Commander:edit_block`.
- **Cat 2 (dry-run multi-target mechanical edits)** — n/a; no scripted multi-target edits this session. §A.10 insertion was a single-target `edit_block` call. DR-032 was an append, not a multi-target edit.
- **Cat 2 (persist drafted artefact content to scratch)** — n/a; both artefacts written to disk in canonical artefact locations during session (`decisions.md`, `architecture.md`), not deferred to scratch.
- **Cat 2 (surface structural-drift in session record)** — flagged. The §A.10 placement (vs the legacy `§D12` shorthand) is structural drift surfaced explicitly in this session record's "What was delivered" section as a governance event.
- **Cat 3 (`bash_tool` non-functional)** — held. All tool routing through Desktop Commander.
- **Cat 3 (external API resources reach-for)** — n/a; no external API research this session. References to Betfair API field shapes (`marketId`, `selectionId`) followed locked substrate without fresh research.
- **Cat 4 (DR-027/028 invoked)** — named at open and re-invoked mid-session at Round 5 (Call 4 cross-DB boundary check). DR-032 sits cleanly underneath both per the locked stance.
- **Cat 4 (operational/analytical line discipline)** — held. DR-032 explicitly names operational line vs analytical line and the canonical join keys for each. Racing API as analytical-line-only is locked language in DR-032 §7.
- **Cat 4 (single-cycle analysis discipline)** — held. SGM bet record as a single bonded entity (one bet, multiple legs, one outcome, one stake) is the architectural shape locked in DR-032 §2/§3.
- **Cat 4 (Betfair as canonical source)** — landed as §A.10 + DR-032. Standing-instruction Cat 4 paragraph re: pending architectural extension can be updated at next standing-instructions sweep to reflect the formal landing.
- **Cat 5 (software questions are Claude's)** — held throughout. Schema design (bet record + bet legs split, ownership of fields, idempotence rules), structural choices (where §A.10 lives, two-table vs flat), drafting (DR-032 text, §A.10 text), tradeoff articulation — all Claude's territory. Operator-facing calls were strategic shape decisions only (where the extension lives, identifier shape, entry-path scope, hard-rule decisions).

## Session-90-specific reflections

- **Operator-driven problem-check round was high-value.** Round 6 surfaced three genuine problems Claude hadn't initially flagged. Two were dissolved by operator corrections (Problem 1 — Racing API analytical-only; Problem 3 — capture-and-match-later approach). One was correctly identified and reshaped (Problem 2 — SGM array-of-pairs shape rather than single-selection v1 scope-down). Pattern: operator-driven problem-checks compound the design's robustness; Claude should surface them more readily on substantive design calls, not wait for operator prompting.

- **Operator-driven idempotence check (Round 8) caught a discipline issue Claude hadn't surfaced.** Asking explicitly about double-counting forced Claude to make the ownership split structural rather than implicit. The schema enforces idempotence (no `stake` column on legs table) rather than relying on developer convention. Pattern: idempotence and double-counting checks belong in the design conversation, not after schema lock.

- **Phantom-anchor governance gap was a real find.** §D12 had been cited load-bearingly across ~10 sessions against an anchor that never existed. Caught only because Claude went looking for §D12 to write the §D12 pointer. The carry-forward discipline correctly flagged the gap (§2.8 brief §10.3) but didn't have a mechanism to force closure. Logged as a candidate Cat 2 addition for the next standing-instructions sweep.

- **§A.10 placement decision (vs fabricating §D12) was a small but real governance call.** Two paths: (i) match the legacy shorthand by writing a fresh §D section just to land the principle there (which would entrench a naming inconsistency and create a §D series with one entry); (ii) place the principle where it architecturally belongs (under §A, the Reconciliation contract, alongside §A.8 cross-DB integration and §A.9 derivation rules) and let legacy references age out. Chose (ii). Closing note in §A.10 names the legacy citation explicitly so future readers don't get confused.

- **Two-write append for DR-032 was deliberate.** First write was the heading + opening "Why" paragraph (9 lines). Second write was the locked stance + concrete + tradeoffs + scope + cross-references (103 lines). Pattern matches Cat 2's "consider chunking files into ≤30 line pieces" advisory. Both writes verified post-hoc via `wc -l` + `grep` for heading presence.

- **DR-032 text intentionally references DR-026 (at-log-time market snapshot pattern) and DR-022 (vocabulary) explicitly.** The cross-reference web is dense — DR-032 sits at the intersection of bet-schema, cross-DB, vocabulary, and snapshot patterns. Naming each load-bearing predecessor in the cross-references section makes future doc sweeps easier (the chain of relationships is explicit, not implicit).

## Open items in (carried forward)

New from Session 90:

- **DR-032 locked.** Bet records carry Betfair `marketId` + `selectionId` as canonical join keys; bet record + bet legs schema; stake and combined price on bet record only; immutable logging-time snapshots on legs; entry-path inheritance from racing/sports screens; hard rule on Betfair-market availability; Racing API joins via capture.db's resolution layer post-hoc.
- **architecture.md §A.10 written.** Architectural-principle home for canonical source identifiers. Cites DR-032 for the schema commitment.
- **Cross-reference integrity gap.** Candidate Cat 2 standing-instruction addition for the next standing-instructions sweep — verify heading-level cross-references resolve at session close. Logged as Claude-side carry-forward; not gating.
- **Legacy `§D12` reference cleanup at next documentation sweep.** ~10 files reference `architecture.md §D12`; these resolve to §A.10's content but should be retargeted explicitly at next sweep. Non-gating; cosmetic.

Carry-forward from Session 89 (status changes):

- **Session 42 architectural extension formalisation** — **closed this session.** Landed as DR-032 + §A.10.
- **W4 brief drafting blocked-on-Session-42-extension** → **unblocked.** W4 brief drafting opens with math review §1–§7 + DR-032 schema commitment as combined substrate.
- **`architecture.md §D12 sub-section update` (§2.8 brief §10.3 carry-forward)** → **closed this session** as §A.10 landing.
- **Hedge-staking math review locked at 1942 lines.** §1–§7 + §8 status close. Substrate for W4 brief drafting (now combined with DR-032 schema).
- **Substrate revision flag for W4 brief drafting** — unchanged. §4 modal mechanics revisions still supersede Session 87 PriceDriftEnvelope when W4 brief drafting opens. Now extended with DR-032 schema commitment.
- **Effective-odds synthesis as racing-screen → modal flow** — unchanged.
- **Default free-bet conversion rate 65%; operator-configurable** — unchanged.
- **Manual stake override as future refinement** — captured in math review §7.5.
- **Multi-rung ladder hedge as future arc** — captured in math review §7.2.
- **`EX_LADDER` operator-side homework parked** — referenced in math review §7.2.
- **W4 substrate decisions captured Session 87** — unchanged.

All other carry-forward items from Session 89 unchanged.

## Open items out (closed this session)

- **Session 42 architectural extension formalisation.** Drafted as DR-032 (`decisions.md` line 1081) + `architecture.md` §A.10. Five-decision locked stance: Set B identifier shape; two-table bet/legs schema; stake/combined-price on bet record only; immutable logging-time snapshots; entry-path inheritance with hard rule on Betfair-market availability. Three workstreams (W4, W4.1, W6) reference DR-032 directly going forward.
- **`architecture.md §D12 sub-section update` (§2.8 brief §10.3 carry-forward).** Landed as §A.10 rather than §D12 (§D shorthand was a misalignment; no §C/§D series in the file). Legacy `§D12` references resolve to §A.10's content.
- **`architecture.md §D12` phantom-anchor governance gap.** Surfaced and closed in-session.
- **W4 brief drafting blocked-on-Session-42-extension.** Now unblocked. W4 brief drafting opens with math review §1–§7 + DR-032 schema commitment as combined substrate.

## Session close state

- **Rebuild folder root:** `decisions.md` updated (1076 → 1186 lines, DR-032 appended). `architecture.md` updated (699 → 721 lines, §A.10 inserted between §A.9 and §B). `current_state.md` updated at close (this skill). `v3_build_picture.md` updated at close — W4 status changes from `blocked-on-Session-42-extension` to `ready-for-brief-drafting`; milestone label updates accordingly.
- **`current_state.md`:** updated at close — "Last updated" → 2026-05-06 14:22 ACST; "Where we are" → DR-032 locked + §A.10 landed; "What's next" → W4 brief drafting opens against math review + DR-032 substrate; required reads adjusted.
- **`v3_build_picture.md`:** updated at close — W4 status moved.
- **`standing_instructions.md`:** unchanged this session. Cat 4 paragraph re: "pending architectural extension (Session 42)" is now stale (the extension landed) — flag for next standing-instructions sweep alongside the cross-reference integrity gap. Operator-side action: re-upload to bethub-rebuild Claude Project knowledge base **not required this session** (no edits to `standing_instructions.md`).
- **Operator-side action — re-upload `decisions.md` and `architecture.md` to Claude Project knowledge base.** Both files materially edited this session. Required for next session's required reads to see DR-032 + §A.10 in the Project knowledge layer.
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** updated this session (§A.10 inserted).
- **`decisions.md`:** updated this session (DR-032 appended).
- **`dr029/w4_bet_entry/hedge_staking_math.md`:** unchanged this session. Math review remains locked at 1942 lines; substrate for W4 brief drafting.
- **`sessions/`:** Session 90 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 90 opening prompt removed at close; Session 91 opening prompt written.
- **Project knowledge base:** `decisions.md` + `architecture.md` need re-uploading by operator. `standing_instructions.md` unchanged from Session 89 close.
- **VPS state:** unchanged this session. No VPS calls.
- **`bethub-v3/`:** unchanged this session. No Code work.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 91 opens fresh chat. Primary deliverable is **W4 brief drafting** — the Betfair hedge-entry workflow brief that commissions Claude Code work for v3's W4 implementation. Math review §1–§7 (1942 lines, locked) plus DR-032 schema commitment (110 lines, locked) plus §A.10 architectural principle (22 lines, locked) form the combined substrate.

**Session 91 shape:**

1. **First work:** read `current_state.md` plus `standing_instructions.md` in full plus `project_context.md` plus `sessions/SESSION_90.md` (this file). Plus DR-032 in `decisions.md` and §A.10 in `architecture.md` as named session-specific reads.

2. **W4 brief drafting opens.** Likely shape: section-by-section call-driven drafting, similar cadence to math review (which produced ~430 lines per session at the heaviest). W4 brief targets Claude Code as recipient — single bounded session, named anchors only, no edits outside scope, hard limits explicit, output spec named, what-happens-after stated. Per `bethub-brief-drafting` skill.

3. **Likely first calls:** scope of W4 brief (which workflow surfaces — hedge entry only, or hedge entry plus modal mechanics?); module placement (per DR-030, `workflow/bet_entry/v1/`); contract substrate (which of math review §1–§7 sections feed which W4 modules; DR-032 schema as the bet-record contract).

**Out of scope for Session 91:** W4.1 soft-book entry path drafting (separate brief); W6 operational store schema brief (separate brief, further downstream); W7 UI brief (downstream); multi-rung ladder hedge implementation.

**Operator-side actions between sessions:**

- **Required:** re-upload `decisions.md` (DR-032 added) and `architecture.md` (§A.10 added) to bethub-rebuild Claude Project knowledge base. Without this, Session 91's Project-knowledge-base reads will see stale versions.
- **Optional:** review §A.10 + DR-032 on disk if desired before Session 91.

## Close-out notes

Session 90 was a clean substantive design session that closed a long-carrying architectural item (Session 42 extension) and surfaced + closed a real governance gap (the §D12 phantom anchor) in the same session. Two artefacts landed: DR-032 (110 lines, eight-clause locked stance) and `architecture.md` §A.10 (22 lines, architectural principle). Both bidirectionally cross-referenced.

Three patterns from Session 90 worth holding onto:

- **Operator-driven problem-checks compound design robustness.** Round 6 surfaced three problems Claude hadn't initially flagged; two were dissolved by operator corrections, one was reshaped from "v1 scope-down" to "schema supports both natively." Pattern: surface problem-checks proactively in substantive design conversations, not just on operator prompting.

- **Idempotence and double-counting checks belong in the design conversation.** Operator's Round 8 question forced Claude to make the ownership split structural (no stake column on legs table) rather than implicit. The schema enforces the rule; developers can't accidentally double-count. Pattern: any multi-table schema with potential aggregation surfaces should explicitly walk the idempotence rules during design.

- **Cross-reference integrity is a real governance discipline.** The §D12 phantom anchor propagated for ~10 sessions because the carry-forward discipline tagged it as "post-DR-029 admin" rather than as an integrity gap. Logged as a Cat 2 candidate for the next sweep.

DR-032 + §A.10 locked. W4 brief drafting blocked-on-Session-42-extension is now unblocked. Session 91 opens against math review §1–§7 + DR-032 + §A.10 as combined substrate.
