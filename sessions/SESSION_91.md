# Session 91

**Title:** W4 (Betfair hedge-entry workflow) brief drafting opened — 17 design rounds locked all design substrate (scope, module shape, contract substrate, error semantics, reconciliation pass, return contract, hard limits and out-of-scope); brief skeleton plus §1 (scope) and §2 (module shape) drafted to disk at `dr029/w4_bet_entry/w4_bet_entry_brief.md`; comprehensive 17-round substrate captured to `dr029/w4_bet_entry/_drafts/SESSION_91_substrate.md`; remaining sections §3–§14 carry to Session 92 against locked substrate.
**Opened:** 2026-05-06 14:32 ACST
**Closed:** 2026-05-06 15:39 ACST
**Wall-clock:** ~1h7m active session work. Same-workday open relative to Session 90 close (~10 min gap, single-sitting continuation). No pause-and-resume; no day rollover; no split triggers fired.
**Tool routing:** Claude Chat (W4 brief design conversation; brief skeleton + §1/§2 drafting; substrate file authoring; close-out). No Claude Code work this session. All file ops via Desktop Commander.
**Governing DRs invoked:** DR-027 (two-database architecture), DR-028 (cross-DB integration boundary), DR-030 (v3 repo layout — load-bearing for module placement), DR-031 (v3 tech stack — Pydantic v2, Python 3.12+), DR-032 (canonical reference layer for all bet records — load-bearing for bet-record contract), DR-019 (derived state on read — informed Set B snapshot reasoning), DR-026 (at-log-time market snapshot pattern — informed Set B), DR-022 (account/book/account-at-book vocabulary), DR-021 (Adelaide local time).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-06 14:32 ACST`.
Close: same command → `2026-05-06 15:39 ACST`.

Same-workday open relative to Session 90 close at 14:22 ACST (~10 min gap, single-sitting continuation).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, calibrated against Cat 1 silent-ritual instruction:

- Rebuild root: 12 expected `.md` files, `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_91_opening_prompt.md` only (Session 90 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-06 14:22 ACST` matched Session 90 close; `sessions/SESSION_90.md` present (230 lines); `v3_build_picture.md` last-updated `2026-05-06 14:22 ACST` matched Session 90 close (W4 status `in flight`).
- Same-workday recap delivered at 10 min gap.
- V3 build picture: rendered at open (Session 90 close moved W4 to `in flight`).
- Open-items delta: skip-silent at open (no items closed/opened/overdue in 10-min gap).
- Governing DRs named at open: DR-027, DR-028, DR-030, DR-031, DR-032, DR-019, DR-026, DR-022, DR-021.

## Session shape

Session 91 was a **substantive design session** that ran the W4 brief design conversation end-to-end. Per Cat 1 call-driven and the `bethub-brief-drafting` skill's section-by-section default, the session ran as 17 discrete operator-facing design rounds (counted on the substrate file), each surfacing a single decision or clarification before moving on.

Three patterns shaped this session:

1. **Operator clarifications drove substantive design changes**, not just confirmations. Several rounds had Claude propose a recommendation, operator surface an operational reality that reframed the call, and the design adjusted materially. Examples: Round 8 (`strategy_tag` racing-screen inference), Round 9 (Option 2 vs Option 1 for `is_free_bet` — operator's time-sensitivity reasoning was decisive), Round 13 (workflow ordering correction — soft-book first, then hedge, then log), Round 14 (severity reframing of error paths by financial risk vs code-path complexity), Round 15 (pre-flight scope-down and partial-matching schema).

2. **The cadence held to call-driven section-by-section** (Cat 1) throughout. No round bundled multiple decisions; no over-surfacing of technical detail (Cat 5 — software questions are Claude's). Operator-facing calls were strategic shape decisions, sub-call confirmations on operational nuance, or fatigue-aware sequencing checks.

3. **Substrate persistence was the close-out's load-bearing question**, addressed via option (c) (substrate file + brief sections §1/§2 drafted to disk) over option (b) (substrate file only). Operator's stated context-loss concern made option (c) the right risk-managed choice — two independent transcriptions of the locked substrate (substrate file rationale-preserving + brief sections in canonical artefact form) cross-check each other for fidelity.

The 17 design rounds are catalogued in detail at `dr029/w4_bet_entry/_drafts/SESSION_91_substrate.md` (746 lines). Each round captures: the call, the decision, the rationale (including operator-driven corrections preserved verbatim), and the implication for downstream sections.

## What was delivered

This session produced two substantive artefacts on disk plus a fully-locked design substrate covering all sections of the W4 brief.

### W4 brief skeleton + §1 (scope) and §2 (module shape) drafted

Located at `dr029/w4_bet_entry/w4_bet_entry_brief.md`. 321 lines.

**§1 (Scope) — 5 sub-sections:**

- §1.1 What this brief is — names W4 v1 deliverable as the Betfair hedge-entry workflow at `workflow/bet_entry/v1/`.
- §1.2 What this brief is not — 11-item out-of-scope list (UI rendering, modal mechanics, W4.1, W6, W5, W7, Strategy 3 SGM, manual free-bet ledger, multi-rung ladder, page-level balance flag, broader sync reconciliation, streaming dependency).
- §1.3 Strategy coverage in W4 v1 — three strategies actively (Strategy 1 / Strategy 2 sub-shapes (a) and (b) / Strategy 4) plus account-health turnover (NULL `strategy_tag`); Strategy 3 reserved.
- §1.4 Operational workflow — corrected ordering per Round 13: soft-book bet first, Betfair hedge second, soft-book log last.
- §1.5 Why this ordering matters — financial-risk-weighted error semantics framing (set up for §5 drafting Session 92+).

**§2 (Module shape) — 4 sub-sections:**

- §2.1 Four modules at `workflow/bet_entry/v1/` — `orchestrator.py` (impure), `staking.py` (pure, math review §2 free-bet hedge), `pricing.py` (pure, bonus-winnings only — both flavours), `record_builder.py` (pure, DR-032 contract). Module count locked; no additions / splits / merges.
- §2.2 Module boundaries — pure-pure-pure-impure split; Pydantic for cross-module data; no circular imports.
- §2.3 Return contract — three entry-point functions (`pre_flight_check`, `place_hedge`, `log_soft_book_bet`), Pydantic v2 result-type pattern, exceptions reserved for programmer errors.
- §2.4 Module file structure — five files (four modules + `models.py`), `tests/` subdirectory.

§3–§14 carry placeholder headings; Session 92 drafts the rest from substrate.

### Session 91 substrate file written to disk

Located at `dr029/w4_bet_entry/_drafts/SESSION_91_substrate.md`. 746 lines.

Captures the full 17-round design log with rationale per round, plus a Session 92 drafting checklist (12 sections in proposed order), outstanding items not requiring draft inclusion, and a one-screen locked-summary reference.

This file is the **load-bearing handoff to Session 92** alongside the brief skeleton. The brief skeleton holds canonical-form locks for §1/§2; the substrate file holds rationale-preserving locks for the design rounds that feed §3–§14.

### Design substrate locked across the full W4 brief surface

Per the substrate file's locked-summary section:

- **Scope:** hedge entry only; modal mechanics → W7.
- **Modules (4):** orchestrator (impure), staking (pure), pricing (pure, bonus-winnings only — both free-bet and cash flavours), record_builder (pure).
- **Math review reference:** by anchor; not embedded.
- **`strategy_tag`:** four-tag enum + nullable; racing-screen inferred at modal open; modal override allowed; closed enum (no freeform).
- **Set B:** 6 immutable logging-time snapshot fields per leg (`runner_name`, `event_name`, `venue_name`, `market_name`, `scheduled_start_time`, `betfair_implied_probability`).
- **`is_free_bet`:** racing-screen inherited (Option 2); modal override.
- **`free_bet_conversion_rate`:** stored on bet record at logging; default 65% (config); operator-overridable; only consumed by `pricing.py` for free-bet bonus-winnings flavour.
- **`realised_conversion_rate`:** populated by W5 at settlement; based on whichever leg actually won (handles Betfair-price-drift edge case).
- **Pre-flight:** modal-only; market status check + proposed-stake fundedness check; no page-level state-reading.
- **Error framework:** severity-weighted by financial risk; (a) hedge calc fail and (b) Betfair API fail are critical (operator exposed); (c) hedge log fail and (d) soft-book log fail are standard (record-keeping only); retry-with-backoff for retry-safe errors; result-type return pattern.
- **Stake fields generalised:** `requested_stake`, `matched_stake`, `unmatched_stake`, `matched_price`, `match_status` (5-value enum) on all bet records; non-hedge bets have `requested = matched`, `unmatched = 0`.
- **Reconciliation:** Trigger A + B hybrid; 5s post-`placeOrders` window; streaming preferred when available, polling fallback; `provisional_pending` state for stuck cases.
- **Test scope:** unit tests on pure modules + mocked-API integration tests on orchestrator. No real-API integration tests.
- **Hard limits:** 8 items locked. **Out-of-scope:** 11 items named.

### Cross-references locked for Session 92's drafting

The brief draft and substrate file together cite: DR-019, DR-021, DR-022, DR-026, DR-027, DR-028, DR-030, DR-031, DR-032; math review §1–§7 (with §4 carried to W7); `architecture.md` §A.10; `betfair_client_contract.md` v1.0; W4 substrate decisions across Sessions 87, 88, 89, 90.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-030, DR-031, DR-032, DR-019, DR-026, DR-022, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered at 10-min gap.
- **Cat 1 (V3 build picture conditional render)** — rendered at open (Session 90 close moved W4 to `in flight`). Not rendered at close (no further stream movement this session — see Step 6 below).
- **Cat 1 (open-items delta)** — skip-silent at open.
- **Cat 1 (drift-check)** — done at open, all three checks matched.
- **Cat 1 (silent session-open ritual)** — held. Steps 1–5 silent; Steps 6–8 combined into single brief output.
- **Cat 1 (silent session-close ritual)** — holding this close. Steps 1–10 silent; Step 11 produces brief verification line.
- **Cat 1 (call-driven surfacing during section-by-section drafting)** — held throughout. 17 discrete operator-facing design rounds, each with single decision or clarification. No bundling.
- **Cat 1 (short responses, plain language)** — held throughout. Some longer rounds were warranted by content (Round 13 workflow correction, Round 14 severity reframe, Round 15 partial-matching schema design); brevity default held elsewhere.
- **Cat 1 (decision-maker framing)** — held. Each call led with the choice; Claude's recommendation followed; operator's decision went next.
- **Cat 1 (don't drift to alternatives when operator clear)** — held. Operator confirmed option A scope at Round 1; Claude proceeded directly through the 17 rounds without re-litigating scope.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders; technical terms (DR-032 §X, `marketId`, `selectionId`, Pydantic, result-type, Trigger A/B, Set A/B, paths a/b/c/d, etc.) unwound in operator-facing framing.
- **Cat 1 (escalate to detail only when warranted)** — held. Round 14 severity reframe explicitly escalated (operator's framing required engagement); Round 15 partial-matching schema escalated (real schema-shape decision); brevity default held elsewhere.
- **Cat 1 (line-break rendering for review content)** — held. Brief skeleton drafted with hard line wraps at ~70 characters in fenced content; substrate file similar.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. No pause-and-resume.
- **Cat 2 (pre-flight directory listing)** — done at open.
- **Cat 2 (Desktop Commander default)** — held. All file ops via `Desktop Commander:read_file`, `Desktop Commander:list_directory`, `Desktop Commander:start_process` (date / mkdir), `Desktop Commander:write_file` (brief skeleton, substrate file, this session record).
- **Cat 2 (REPL discipline)** — n/a; no REPL work this session. All shell calls one-shot.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)** — held. All writes via `Desktop Commander:write_file`. Both new artefacts verified post-write via tool's success message + line count.
- **Cat 2 (dry-run multi-target mechanical edits)** — n/a; no scripted multi-target edits this session.
- **Cat 2 (persist drafted artefact content to scratch)** — held. Substrate file at `dr029/w4_bet_entry/_drafts/SESSION_91_substrate.md` is the canonical scratch persistence per Cat 2's instruction. Drafted-but-not-assembled material (16 rounds of design substrate not yet folded into brief sections §3–§14) lives in this file for Session 92's consumption.
- **Cat 2 (surface structural-drift in session record)** — n/a this session. No structural drift in governance artefacts (DR-032 unchanged; `architecture.md` §A.10 unchanged from Session 90 close; no schema renumbering).
- **Cat 3 (`bash_tool` non-functional)** — held. All tool routing through Desktop Commander.
- **Cat 3 (external API resources reach-for)** — n/a; no external API research this session. References to Betfair API (`placeOrders`, `listCurrentOrders`, retry-safe vs terminal error categories) drew from prior locked substrate (`betfair_client_contract.md` and prior session work).
- **Cat 4 (DR-027/028 invoked)** — named at open. DR-032 (which sits cleanly under DR-027/028 per Session 90 lock) drove most schema-related rounds (Rounds 5, 6, 7, 9, 15).
- **Cat 4 (operational/analytical line discipline)** — held. W4 is the operational-line workflow engine (Betfair-direct orchestration); analytical-line concerns (capture.db, post-hoc reconciliation across the whole bet history) were explicitly named as W6 territory and excluded.
- **Cat 4 (single-cycle analysis discipline)** — held. Round 9's free-bet field design treats free bets within their cycle context (insurance-trigger cycle, bonus-winnings free-bet cycle) per the standing analysis convention.
- **Cat 4 (Betfair as canonical source)** — DR-032 is the substantive landing of this discipline; W4 is its first writer. Schema reflects DR-032's canonical-identifier-as-join-key principle throughout (Rounds 5, 7, 8, 9, 15).
- **Cat 5 (software questions are Claude's)** — held throughout. Module shape (Round 2), pricing-module scope clarification (Round 3), reference-by-anchor decision (Round 4), Set B field list (Round 7), retry-with-backoff policy (Rounds 12–14), partial-matching schema and `match_status` enum (Round 15), Pydantic + result-type pattern (Round 16), test coverage scope (Round 17 — explicitly delegated by operator as a developer call) — all Claude's territory. Operator-facing calls were strategic shape decisions only (scope, module count, racing-screen inference, severity weighting, partial-matching requirement).

## Session-91-specific reflections

- **Operator clarifications shaped substantive design changes throughout.** Five rounds had operator-driven corrections that materially reframed Claude's recommendation: Round 8 (racing-screen inference for `strategy_tag`), Round 9 (Option 2 for `is_free_bet`), Round 13 (workflow ordering correction), Round 14 (severity reframing by financial risk), Round 15 (partial-matching schema requirement). Pattern: when the operator surfaces an operational reality, the design must accommodate it — Claude's first-pass recommendation is starting substrate, not the locked answer.

- **The Round 13 workflow ordering correction was the highest-leverage moment of the session.** Claude's initial four-failure-path framing assumed an ordering (soft-book log → Betfair hedge → soft-book log later) that didn't match v2's actual flow. Operator surfaced the correct ordering (soft-book bet → Betfair hedge → soft-book log last). The reframe propagated through Rounds 14–15 and reshaped the entire error-semantics section. Pattern: when designing against operational workflows, validate the workflow ordering empirically before locking error semantics. Worth absorbing as a Cat 4 candidate at next standing-instructions sweep ("validate operational workflow ordering empirically before locking semantics that depend on it").

- **The Round 15 partial-matching requirement is operationally important and was nearly missed.** Operator's requirement that historical bet records show *what actually matched and what didn't* (with specific numbers, not just success/failure) shaped the entire `match_status` enum and the generalised stake fields decision. Without operator surfacing this, the schema would have collapsed partial matches to "matched stake" only — losing real analytical value for future EV reconciliation. Pattern: schema decisions for analytical capture should be tested against future-analytics value before locking.

- **Substrate persistence option (c) over (b) was the right risk-managed choice.** Operator's stated concern about context loss between sessions was decisive. Two independent transcriptions of locked substrate (canonical-form brief sections + rationale-preserving substrate file) cross-check each other for fidelity. The 67-minute session's last 30+ minutes drafting both artefacts was time well spent against the failure mode of Session 92 opening with rationale gaps.

- **Brief-drafting cadence is its own thing.** The 17 design rounds were design conversation; the brief drafting itself was section-by-section against a locked substrate. Drafting §1 and §2 ran cleanly because the locks had been made; Session 92's drafting of §3–§14 will be similar shape (most operator-facing calls already settled in this session's substrate; remaining sections are mostly mechanical with a few small calls flagged in the substrate file's checklist).

## Open items in (carried forward)

New from Session 91:

- **W4 brief drafting in flight.** Skeleton + §1 (scope) and §2 (module shape) drafted (321 lines on disk). Sections §3–§14 carry to Session 92. Substrate fully locked at `dr029/w4_bet_entry/_drafts/SESSION_91_substrate.md` (746 lines).
- **Round 13 workflow-ordering-validation pattern as Cat 4 candidate.** Surfaced as a candidate `standing_instructions.md` Cat 4 instruction at next sweep ("validate operational workflow ordering empirically before locking semantics that depend on it"). Logged as Claude-side carry-forward; not gating.
- **Streaming subscription readiness for W4 reconciliation pass.** W2/W3 dependency status check before W4 ships. May surface as a Session 92 question during §6 drafting (reconciliation pass design).

Carry-forward from Session 90 (status):

- **DR-032 locked.** Unchanged. Continues to drive W4 brief schema.
- **`architecture.md` §A.10 written.** Unchanged.
- **Cross-reference integrity gap** (Cat 2 standing-instruction candidate) — unchanged.
- **Legacy `§D12` reference cleanup at next documentation sweep** — unchanged.
- **Cat 4 paragraph re: "pending architectural extension (Session 42)" stale** — unchanged. Flag for next standing-instructions sweep.
- **Hedge-staking math review locked at 1942 lines** — substrate for W4 brief drafting (in flight).
- **Substrate revision flag for W4 brief drafting** — applied this session. §4 modal mechanics carried to W7.
- **Effective-odds synthesis as racing-screen → modal flow** — formalised this session as `pricing.py` two-path scope (Round 10). Carried as W4 brief content.
- **Default free-bet conversion rate 65%; operator-configurable** — formalised this session in §[3 contract substrate, drafting Session 92] design substrate.
- **Manual stake override as future refinement** — captured in §7.5 of math review.
- **Multi-rung ladder hedge as future arc** — captured in §7.2 of math review.
- **`EX_LADDER` operator-side homework parked** — referenced in math review §7.2.
- **W4 substrate decisions captured Session 87** — extended this session by full design substrate.
- **F5 strategy_tag carry forward — operator-facing routing** — formalised this session in Round 5 (four-tag closed enum + nullable for account-health turnover).
- **Streaming envelope vocabulary carry-forward** — unchanged.
- **Deployment-substrate items (F2, F3, F4)** — unchanged.
- **F6 carry-forward to Fix 4 brief + W3+ briefs** — unchanged.
- **§12 self-assessment item 3 — audit-log durable substrate selection** — unchanged.
- **W1 F2 sharpening (Thoroughbred / Harness label conflation)** — unchanged.
- **W1 F1 accepted as v1.0 conflation** — unchanged.
- **W0 F2 brief-language carry** — unchanged.
- **`str_replace` namespace gotcha** — unchanged.
- **DR-030 "18 months" reference correction** — unchanged.
- **`governance.md` §4 deferred-capability reconciliation** — unchanged.
- **Jump-anchor design reframe** — unchanged.
- **Post-DR-029-close contract documentation relocation** — unchanged.
- **Sports-side dead-heat capture in `architecture.md` §B.1.4** — unchanged.
- **Past-settlement-window threshold calibration** — unchanged.
- **Settlement worker periodic verification cadence** — unchanged.
- **Cluster 1 surgical-fix carry-in** — unchanged.
- **Fix 9 / Fix 10 / three-row collision triage / low-confidence match review** — unchanged.
- **Complete cascade map** — unchanged.
- **CLV as analytical-layer signal** — unchanged.
- **Path-(iii) reconciliation-job scheduling and operator-facing flag-queue UI** — unchanged.
- **§2.9 §4.4 six edge cases** — unchanged.
- **All other carry-forward items from Session 90 unchanged.**

## Open items out (closed this session)

None closed this session — Session 91 was substrate-locking and drafting-initiation, not closure of any prior carry-forward item. Items advance to in-flight status:

- **W4 brief drafting** moves from "ready to start" (Session 90 close) to "in flight, §1 and §2 drafted, substrate fully locked, §3–§14 carry to Session 92".

## Session close state

- **Rebuild folder root:** unchanged this session. No edits to root-level governance files.
- **`current_state.md`:** updated at close — "Last updated" → 2026-05-06 15:39 ACST; "Where we are" → W4 brief drafting in flight, §1 and §2 drafted, substrate locked; "What's next" → Session 92 continues drafting §3 onward against substrate file; required reads adjusted.
- **`v3_build_picture.md`:** updated at close — W4 next-milestone label updated to reflect Session 91's progress (continue drafting from §3 against substrate).
- **`standing_instructions.md`:** unchanged this session. Cat 4 paragraph re: "pending architectural extension" remains stale (Session 90 carry-forward); Round 13 candidate addition logged as carry-forward; cross-reference integrity gap (Session 90 carry-forward) remains. All defer to next standing-instructions sweep. Operator-side action: re-upload to bethub-rebuild Claude Project knowledge base **not required this session** (no edits).
- **`governance.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session.
- **`decisions.md`:** unchanged this session.
- **`dr029/w4_bet_entry/`:**
  - `hedge_staking_math.md` — unchanged. Locked at 1942 lines.
  - `w4_bet_entry_brief.md` — **new this session**. 321 lines. Skeleton + §1 + §2.
  - `_drafts/SESSION_91_substrate.md` — **new this session**. 746 lines. Full 17-round design substrate.
- **`sessions/`:** Session 91 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 91 opening prompt removed at close; Session 92 opening prompt written.
- **Project knowledge base:** unchanged. No re-upload required this session (no edits to knowledge-base files).
- **VPS state:** unchanged this session. No VPS calls.
- **`bethub-v3/`:** unchanged this session. No Code work.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 92 opens fresh chat. Primary deliverable is **continuation of W4 brief drafting** against the locked substrate at `dr029/w4_bet_entry/_drafts/SESSION_91_substrate.md` plus the brief skeleton at `dr029/w4_bet_entry/w4_bet_entry_brief.md`.

**Session 92 shape:**

1. **First work:** read `current_state.md` plus `standing_instructions.md` in full plus `project_context.md` plus `sessions/SESSION_91.md` (this file). Plus session-specific reads — substrate file in full + brief skeleton in full.

2. **Drafting opens at §3 (Contract substrate mapping).** Section-by-section call-driven cadence per Cat 1 + the `bethub-brief-drafting` skill. Drafting checklist (12 sections in proposed order) lives in the substrate file's "Session 92 drafting checklist" section.

3. **Likely operator-facing calls during Session 92 drafting:**
   - Sequencing within session (§9) — module build order has alternatives; may surface a call.
   - Length range for report (§11) — estimate may need operator adjustment.
   - Pre-read list (§7) — confirm whether `betfair_client_contract.md` is required-read or reference-only.
   - Possibly: streaming-vs-polling preference for reconciliation pass (§6) if W2/W3 dependency status is unclear.

4. **Estimated session length:** 1.5–2.5 hours active work to complete §3–§14 (~400–600 additional lines of brief content). May need a Session 93 if drafting cadence calls run heavy.

**Out of scope for Session 92:** any new design substrate work (substrate is locked); W4.1 / W6 / W7 brief drafting; streaming-subscription dependency resolution beyond noting it in §6.

**Operator-side actions between sessions:**

- **Optional:** review the brief skeleton + §1/§2 drafted content + substrate file if desired before Session 92.
- **Not required:** no Project knowledge base re-uploads needed (no canonical-truth file edits this session).

## Close-out notes

Session 91 was a clean substantive design session that locked all 17 rounds of W4 brief design substrate, drafted the brief skeleton plus §1 and §2 to disk, and wrote a comprehensive substrate file as the load-bearing handoff to Session 92.

Three patterns from Session 91 worth holding onto:

- **Operator clarifications shape design materially.** Five of 17 rounds had operator-driven corrections that reframed Claude's recommendation (racing-screen inference, Option 2 for `is_free_bet`, workflow ordering, severity reframing, partial-matching schema). The first-pass recommendation is starting substrate; the operator's operational reality is the locking context.

- **Workflow-ordering validation matters before locking dependent semantics.** Round 13's correction propagated through Rounds 14–15 and reshaped the entire error-semantics section. Worth absorbing as a Cat 4 candidate at next standing-instructions sweep.

- **Substrate persistence is non-negotiable on long substrate-heavy sessions.** Two independent transcriptions (canonical-form brief sections + rationale-preserving substrate file) cross-check each other for fidelity. The 67-minute session's drafting overhead was the right risk-managed investment against fresh-Claude context loss in Session 92.

W4 brief drafting in flight. §1 and §2 drafted; §3–§14 carry to Session 92 against locked substrate. No design substrate work remaining; Session 92 is mechanical drafting against locks with a small number of operator-facing calls flagged in the substrate file's checklist.
