# Session 88

**Title:** Hedge-staking math review §1–§5 drafted and written to disk at `dr029/w4_bet_entry/hedge_staking_math.md` (1074 lines covering scope, variables, Construction A cash + free-bet derivations, Construction B cash + free-bet derivations, modal mechanics, cycle shapes); §6 worked examples + §7 edge cases deferred to Session 89 per operator's split-trigger call. Material design substrate captured: cash and free-bet hedge formulas locked; Net=0 condition corrected to operator's form `P_bf = P_soft × (1 − c) + c`; commission resolution must be dynamic per Betfair venue-specific listings (ship-blocker named); Construction B (back-against-Betfair-back) restricted to two-outcome markets only; multi-rung ladder hedge math verified and routed to future arc (matching-layer scope, Route C); modal mechanics redesigned around live-price + custom-price tandem with `priceLimit`-protected placement, dissolving the Session 87 PriceDriftEnvelope substrate; Strategy 2 sub-shapes corrected to three (boosted odds; bonus winnings as free bet; bonus winnings as cash); effective-odds synthesis tool-calculated from racing-screen promo fields, not operator-typed; default free-bet conversion rate downgraded from 70% to 65%; manual stake override deferred to future refinement.
**Opened:** 2026-05-05 19:01 ACST
**Closed:** 2026-05-06 11:00 ACST
**Wall-clock:** Session opened 19:01 ACST 2026-05-05; operator paused mid-session and resumed next day (re-anchored on resumption per Cat 2 multi-day rule); active session work substantially less than calendar gap. Day-rollover split trigger fired; operator explicitly named fatigue at §5 close and chose Route B (defer §6/§7 to fresh session) per Cat 1 split-rather-than-push-through discipline.
**Tool routing:** Claude Chat (math review §1–§5 drafting; design substrate calls; close-out). No Claude Code work this session.
**Governing DRs invoked:** DR-027 (two-database architecture), DR-028 (cross-DB integration boundary), DR-021 (Adelaide local time), DR-019 (derived state on read), DR-030 (v3 repo layout — load-bearing for W4 module placement), DR-031 (v3 tech stack). Plus Session 42 architectural extension flag carried forward (cycle-linkage at logging time formalises before W4.1).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-05 19:01 ACST`.
Close: same command → `2026-05-06 11:00 ACST`.

Same-workday open relative to Session 87 close (~14 min gap, single-sitting continuation). Session itself spanned a calendar-day rollover but on operator's pause-and-resume pattern; close timestamp reflects actual close moment per Cat 2.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill, calibrated against Cat 1 silent-ritual instruction:

- Rebuild root: 12 expected `.md` files, `openapi.json`, `external_api_resources.md`, `.DS_Store`. All directories present.
- `.close_out_backups/` contained `SESSION_88_opening_prompt.md` only (Session 87 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-05 18:47 ACST` matched Session 87 close; `sessions/SESSION_87.md` present (228 lines); `v3_build_picture.md` last-updated `2026-05-05 18:47 ACST` matched Session 87 close.
- Same-workday recap delivered (tight: Session 87 closed W3 + opened W4 brief drafting + paused on math review need; Session 88 ships hedge-staking math review).
- V3 build picture: rendered inline at open (artefact updated by Session 87 close; render condition fired).
- Open-items delta: skip-silent (no items closed/opened/overdue between Session 87 close and Session 88 open).
- Governing DRs named at open: DR-027, DR-028, DR-021, DR-019, DR-030, DR-031.

## Session shape

Session 88 was a **single-deliverable design session** — hedge-staking math review §1–§5 drafted call-driven and written to disk at `dr029/w4_bet_entry/hedge_staking_math.md` (1074 lines). §6 (worked numerical examples) and §7 (edge cases / ship-blocker items / future extensions list) deferred to Session 89.

The session was substantively richer than its surface scope because operator clarifications on operational reality reshaped the design at three points — soft-book lay framing dropped (§1), live-price modal mechanism replacing PriceDriftEnvelope (§4), Strategy 2 sub-shape structure corrected to three sub-shapes (§5). Each clarification produced material design refinements that landed in the artefact and tightened the math review's operational accuracy.

The session was call-driven section-by-section per Cat 1. Round structure roughly:

**Round 1 (open + Call 0).** Standard same-workday open ritual. Cycle-equalisation target locked: equalise net dollars-in-pocket across the two Betfair-side outcomes at whatever level current price-and-stake combination supports. No EV assumptions baked into placement-time formulas. No free-bet conversion rate folded in (this assumption was later refined in §5).

**Round 2 (Call 0.1 — formality level).** Locked Route B (semi-formal — explicit variables, derivation steps shown, worked examples).

**Round 3 (§1 first draft + two corrections from operator).** Operator surfaced two corrections: soft-book lay does not exist as a soft-book product (Australian books are back-only); Betfair commission must be applied dynamically per venue-specific listings (Ipswich 4% example vs Queensland 8% statewide). These reshaped §1 materially — soft-book-lay framing dropped entirely; commission resolution flagged as ship-blocker (W4 ports v2's commission-lookup mechanism, which itself may be Route-B-shaped via live Betfair commission endpoint queries).

**Round 4 (Construction A vs Construction B framing locked).** Operator clarified back-against-back hedging is mathematically equivalent to lay-against-back hedging when both legs target the same outcome through different sides of the Betfair book. Construction A (lay on same selection) covers any-outcome markets; Construction B (back on opposing selection) covers two-outcome markets only. Both ship in W4. Multi-leg back-against-back constructions (three-or-more outcome markets) explicitly out of W4 scope.

**Round 5 (§2 derivation + Net=0 correction).** Cash formula derived: `S_bf = (S_soft × P_soft) / (P_bf − c)`. Operator corrected the Net=0 condition to its explicit form: `P_bf = P_soft × (1 − c) + c` (mine had been the implicit inequality form `P_soft × (1 − c) > P_bf − c`). Free-bet formula derived after operator caught my error treating a $100 free bet as a cash bet in the worked example: `S_bf = [S_soft × (P_soft − 1)] / (P_bf − c)`. Sanity check across both formulas; liability calculation surfaced.

**Round 6 (Concern A vs Concern B separation).** Operator's question on the sanity-bound enforcement clarified that I'd conflated two different operational concerns — math edge at extremely low Betfair odds (theoretical, P_bf approaching c) versus high-liability hedges at high Betfair odds (operational, common). Concern A dissolved entirely (Betfair minimum tick is 1.01; math edge is unreachable). Call 2.1 locked as Route B — surface stake/liability/Net + soft warning when liability exceeds configurable threshold (default $1,000).

**Round 7 (multi-rung ladder hedge spec review).** Operator surfaced a separately-developed spec for matching across multiple Betfair price levels (cheapest-first ladder filling with commission-aware closure on the final rung). I verified the math independently — single-rung cash formula is the spec's collapse case; multi-rung formula derived for both cash and free-bet variants. Routing locked at Route C — defer multi-rung to a future arc (matching-layer scope, candidate for own math review and possibly DR-032). Single-rung is W4 v1 scope; multi-rung is future. Spec's four open policy questions (commission rate source, rounding, partial-hedge tolerance, stale-price handling) carry forward to that future arc. Premise correction to operator: the existing entitlement is `EX_BEST_OFFERS` (top-three rungs), not three-best implied by Streaming generally — `EX_LADDER` would lift to ten rungs and is parked operator-side homework.

**Round 8 (§3 Construction B derivation).** Cash formula: `S_bf = (S_soft × P_soft) / [(P_bf − 1) × (1 − c) + 1]`. Free-bet formula: `S_bf = [S_soft × (P_soft − 1)] / [(P_bf − 1) × (1 − c) + 1]`. Different denominator from Construction A — algebraic non-equivalence except at c = 0. Liability for Construction B equals the back stake itself (no separate liability mechanism). §3.6 sub-section names the not-quite-equivalence: real Betfair markets have overround across the two sides, and the formulas use different denominators, so Construction A and Construction B produce slightly different Net values for "equivalent" prices. Cross-construction Net comparison flagged as §7 future-extension item; W4 v1 is operator-selects-construction.

**Round 9 (§4 modal mechanics redesign — material substrate revision).** Operator reshaped the §4 design with two substantive interventions: (a) "hold line" semantics meaning **place the order at original price** (not refresh and don't place) using Betfair's `persistenceType=PERSIST`; (b) live-price modal where displayed price updates with Betfair Streaming and stake auto-recomputes against live price. Combined effect dissolved the Session 87 Round 9 PriceDriftEnvelope substrate entirely — operator sees live numbers continuously and uses `priceLimit`-protected placement to enforce price intent at the API layer. The modal exposes both live-price and custom-price modes in tandem (operator chose two-mode-in-tandem rather than toggle); custom price drives independent recomputation; match-availability indicator surfaces fully-matched / partially-matched / fully-unmatched at placement; persistence type (PERSIST default; LAPSE; MOC) operator-controlled per placement. Calls 4.1, 4.2, 4.3 locked routes through the redesign (live + custom in tandem; MOC always exposed; PERSIST default). §4.8 explicitly names the substrate revision so when W4 brief drafting resumes, the §4 mechanics here are the locked substrate (not the Session 87 envelope shape).

**Round 10 (§5 Strategy structure corrections).** Operator corrected the cycle-shape framing in three substantive ways: (a) Strategy 1 has at most two legs (not three — my hypothetical third-leg downstream-promo scenario doesn't exist operationally); (b) Strategy 2 has three sub-shapes not two — boosted odds (single-leg cash); bonus winnings as free bet (two-leg cycle, free-bet leg = Strategy 1 free-bet leg); bonus winnings as cash (single-leg with adjusted win-state payout); (c) effective-odds synthesis is **tool-calculated** from racing-screen promo fields, not operator-typed. The synthesis math: `P_soft_effective = P_soft_actual + (free_bet_cap × conversion_rate) / S_soft` for sub-shape 2; `P_soft_effective = P_soft_actual + bonus_cash_cap / S_soft` for sub-shape 3. Optimal stake `S_optimal = bonus_cap / (P_soft_actual − 1)` rounded to nearest $5, surfaced both on racing screen and in modal. Default free-bet conversion rate downgraded 70% → 65% based on operator's observed realisation. Strategy 2 sub-shape 1 UX simplification: v3 takes boosted odds directly, no separate original-vs-boosted delta capture. Free-bet conversion analytics is intent-aware (post-DR-029 work; intent-capture substrate from earlier sessions provides the filter).

**Round 11 (manual stake override deferral).** Operator considered manual stake override as a third axis of modal control alongside live-vs-custom price and persistence type, then chose to defer to future refinement. Math review stays clean on equalisation as canonical behavior; §7 will flag manual override as future extension when §7 lands next session.

**Round 12 (close routing).** Operator chose Route B — close session, defer §6 + §7 to fresh session. Day-rollover split trigger fired plus operator-named fatigue; close-out runs full but no §6/§7 push-through.

## What was delivered

This session produced one substantive artefact (math review §1–§5) plus close-out artefacts. The design substrate captured is materially load-bearing for W4 brief drafting when it resumes — multiple Session 87 substrate items revised based on operational clarifications surfaced this session.

### Hedge-staking math review §1–§5 written to disk

Located at `dr029/w4_bet_entry/hedge_staking_math.md`. 1074 lines. Sections covered:

**§1 — Variables and conventions.** Soft-book leg back-only (no soft-book lay). Two Betfair leg constructions named. Variables defined explicitly (S_soft, P_soft, S_bf, P_bf, c). Commission resolution flagged as dynamic per Betfair venue-specific listings (ship-blocker — W4 ports v2's mechanism). Equalisation condition stated.

**§2 — Construction A: lay-against-soft-book-back.** Cash formula derived: `S_bf = (S_soft × P_soft) / (P_bf − c)`. Free-bet formula derived: `S_bf = [S_soft × (P_soft − 1)] / (P_bf − c)`. Equalised outcome value for both. Net=0 condition: `P_bf = P_soft × (1 − c) + c` (operator's form). Three regimes (profit-locked / arb / cycle-cost). Liability and balance impact: `Liability = S_bf × (P_bf − 1)`; soft warning at $1,000 default threshold (operator-configurable). Three sanity checks (zero-commission equal odds; free-bet zero-commission moderate odds; soft-book odds approach 1 — all pass).

**§3 — Construction B: back-against-Betfair-back.** Restricted to two-outcome markets only. Cash formula: `S_bf = (S_soft × P_soft) / [(P_bf − 1) × (1 − c) + 1]`. Free-bet formula: `S_bf = [S_soft × (P_soft − 1)] / [(P_bf − 1) × (1 − c) + 1]`. Different denominator from Construction A — non-equivalent except at c = 0. Liability for Construction B equals back stake itself. §3.6 names Construction A vs B not-quite-equivalence (overround + commission); W4 v1 is operator-selects.

**§4 — Modal mechanics.** Live-price mechanism (Streaming-driven recomputation of P_bf, S_bf, Liability, Net). Custom-price mechanism (operator-typed price; same recomputation). Both run in tandem in same modal. Match-availability surfacing (fully-matched / partially-matched / fully-unmatched at placement). Persistence type (PERSIST default; LAPSE; MOC available all markets). `priceLimit`-protected placement collapses favourable-vs-unfavourable drift handling. Cancel-then-place uses same mechanics on place leg. Sanity-checking via operator visibility (no math-layer bounds). §4.8 explicitly names the substrate revision dissolving Session 87 PriceDriftEnvelope.

**§5 — Refund and free-bet cycle shapes.** Strategy 1 (Safety Net) up to two legs. Strategy 2 sub-shape 1 (boosted odds) single-leg cash with v3 UX simplification. Strategy 2 sub-shape 2 (bonus winnings as free bet) two-leg with effective-odds synthesis: `P_soft_effective = P_soft_actual + (free_bet_cap × conversion_rate) / S_soft`. Strategy 2 sub-shape 3 (bonus winnings as cash) single-leg with cash bonus: `P_soft_effective = P_soft_actual + bonus_cash_cap / S_soft`. Optimal stake `S_optimal = bonus_cap / (P_soft_actual − 1)` rounded to nearest $5. Default conversion rate 65%. Strategy 2 price-uplift deferred. General turnover unchanged. Cycle-linkage at logging time flagged for before W4.1. Free-bet conversion rate as both parameter and analytics — intent-filtered realised rate measured post-cycle in analytical layer.

### Material substrate revisions vs Session 87

When W4 brief drafting resumes, the following substrate items have been revised this session:

1. **§4 modal mechanics replace PriceDriftEnvelope.** Session 87 Round 9 captured a structured PriceDriftEnvelope with two retry routes (hold line / accept drift) as the unfavourable-drift handling mechanism. §4.8 supersedes that mechanism with live-price + custom-price modal in tandem plus `priceLimit`-protected placement. The directional thinking from Session 87 still holds; the mechanism is simpler and operator-visible continuously rather than snapshot-and-prompt.

2. **"Hedge-target spec" framing extended to mode-aware.** Session 87 captured `hedge_target` spec as workflow input. The math review confirms this shape but extends with mode-aware behavior — the modal accepts a `hedge_target` and exposes both live-price and custom-price ways to drive the actual placement against it.

3. **Effective-odds synthesis is tool-calculated, not operator-typed.** When operator places via the racing screen with Strategy 2 sub-shape 2 or 3, the racing screen's promo fields (promo type, free-bet cap, bonus cash cap, conversion rate) drive automatic synthesis of `P_soft_effective` when modal opens. Operator does not type effective odds; they see them displayed alongside actual odds.

4. **Default free-bet conversion rate is 65%, not 70%.** Operator-configurable. Reflects observed realisation rate.

5. **Strategy 1 Safety Net hedging is rare; Strategy 2 bonus-winnings is sometimes hedged.** The math covers all cases for completeness; W4 brief drafting can weight examples accordingly when it resumes.

6. **Manual stake override is future refinement, not v1.** Math review stays clean on equalisation; §7 flags as future extension.

### Material new items captured for §7 (Session 89)

§7 has not yet been drafted but will list:

- **Ship-blocker:** dynamic commission lookup per Betfair venue (Ipswich 4% vs Queensland 8% example). W4 ports v2's mechanism; v2 may use Route-B-shaped live commission endpoint.
- **Multi-bet-per-market commission interaction** — flagged in §1 conventions; named in §7 as edge case.
- **Multi-rung ladder hedge** — feasible extension; formula derived in conversation; routed to future arc (matching-layer scope, candidate DR-032 or later).
- **Cross-construction Net comparison** — Construction A vs B; W4 could surface both Net values; v1 is operator-selects.
- **Operator config layer for `auto_accept_drift`** parameter (residual from §4 framing — but with PriceDriftEnvelope dissolved this may not need separate mention).
- **Strategy 2 price-uplift handling** — deferred to data-source work outside DR-029.
- **Manual stake override** — future refinement.
- **Placement-latency matched-price reporting** — `betfairlightweight` substrate.
- **Free-bet realised-rate analytics** — post-DR-029 analytical layer work.
- **Intent-capture substrate for free-bet analytics filter** — references earlier-sessions work.

### Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-027, DR-028, DR-021, DR-019, DR-030, DR-031 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday recap delivered (~14 min gap qualifies).
- **Cat 1 (V3 build picture conditional render)** — rendered inline at open (artefact updated by Session 87 close).
- **Cat 1 (open-items delta)** — skipped silently at open (no delta between Session 87 close and Session 88 open).
- **Cat 1 (drift-check)** — done at open, all three checks matched.
- **Cat 1 (silent session-open ritual)** — held. Steps 1–5 silent; Steps 6–8 combined into single brief output at end.
- **Cat 1 (silent session-close ritual)** — holding this close. Steps 1–10 silent; Step 11 produces brief verification line.
- **Cat 1 (call-driven surfacing during section-by-section drafting)** — held throughout. Twelve rounds with explicit operator calls per round; cadence held cleanly. Operator surfaced multiple substantive corrections (soft-book lay, dynamic commission, Strategy 1 third-leg, Strategy 2 sub-shapes, effective-odds tool-calculated) which reshaped §1, §4, and §5 materially. Cadence absorbed iteration without losing structure.
- **Cat 1 (short responses, plain language)** — held. Operator's clarifications drove tighter framing on each iteration. Multiple drift-catches by operator on technical-vocabulary slips (e.g. "operator inputs effective odds" → tool-calculates effective odds; "hold line refresh modal" → place limit order at original price).
- **Cat 1 (decision-maker framing)** — held. Each call led with the choice; recommendation followed; reasoning sat behind. Operator role as strategic decision-maker respected throughout — design substrate revisions came from operator clarifications on operational reality, not Claude framings.
- **Cat 1 (don't drift to alternatives when operator clear)** — held.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders; technical terms (`priceLimit`, `persistenceType`, `EX_LADDER`, MOC, `PriceDriftEnvelope`) unwound where they appeared in operator-facing framing.
- **Cat 1 (escalate to detail only when warranted)** — held. The Round 9 modal redesign got dedicated framing because it was material substrate revision; Claude flagged it explicitly as material revision before going deep. Round 10 Strategy 2 sub-shape correction got the same treatment.
- **Cat 1 (line-break rendering for review content)** — held. All review-content blocks rendered at ~60-70 character hard-wrap.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held throughout.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored. Session crossed calendar-day rollover via pause-and-resume; close anchor reflects actual close timestamp per multi-day rule.
- **Cat 2 (pre-flight directory listing)** — done at open.
- **Cat 2 (Desktop Commander default)** — held. All file ops via Desktop Commander.
- **Cat 2 (REPL discipline)** — n/a; no Python REPL work this session.
- **Cat 2 (`create_file` vs `write_file` namespace gotcha)** — held. All writes via `Desktop Commander:write_file`.
- **Cat 2 (dry-run multi-target mechanical edits)** — n/a; no scripted edits this session.
- **Cat 2 (persist drafted artefact content to scratch)** — n/a — math review §1–§5 written to disk in canonical artefact location during session, not deferred. §6/§7 deferred to next session were not drafted in chat (only outlined at high level), so no scratch persistence required.
- **Cat 2 (surface structural-drift in session record)** — flagged. Session 88 Round 9 dissolves Session 87 PriceDriftEnvelope substrate; §4.8 of math review names this explicitly. Session 88 Round 10 corrects Session 87's implicit Strategy 2 sub-shape framing. Both surfaced as substrate revisions in "What was delivered" section.
- **Cat 3 (`bash_tool` non-functional)** — held. All tool routing through Desktop Commander.
- **Cat 3 (external API resources reach-for)** — held implicitly. References to Betfair `priceLimit`, `persistenceType`, `EX_BEST_OFFERS` / `EX_LADDER` entitlement, MARKET_ON_CLOSE all reflected accurate Betfair API behaviour rather than fresh research; operator-side homework on `EX_LADDER` upgrade noted in current_state.md.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-DB topics did not surface mid-session (math review is workflow-internal; cycle-linkage is logging-time architectural concern flagged for W4.1).
- **Cat 4 (operational/analytical line discipline)** — held. Math review's placement-time math is operational-line; free-bet realised-rate analytics is analytical-line and explicitly named as post-DR-029 work.
- **Cat 4 (single-cycle analysis discipline)** — held. §5 cycle-shape framing names cycle membership at logging time; placement-time math is per-leg with cycle aggregation in analytics.
- **Cat 5 (software questions are Claude's)** — held throughout. Mathematical derivations, formula derivations, sanity-check construction, modal mechanics design, edge-case identification all handled by Claude. Operator-facing calls were strategic/operational shape decisions only. The hedge-math review pause from Session 87 (verification work the operator wanted to lock before formulas embedded in tool) was the right Cat 5 boundary call — math is software territory but the operator wanted to verify before locking; this session's structure (semi-formal derivations + operator-clarified inputs) respected that need.

## Session-88-specific reflections

- **Operator clarifications were higher-volume and higher-leverage than typical session.** Roughly six of the twelve rounds involved operator clarifications that reshaped Claude's framing materially (soft-book lay non-existence; dynamic commission; Net=0 explicit form; live-price modal; effective-odds tool-calculated; Strategy 2 three sub-shapes). This is not drift — it's the operator catching framing imprecision and the math review tightening as a result. The artefact is materially better for it.

- **Math review uncovered substrate revisions to Session 87 design.** Session 87 Round 9 framed unfavourable-drift handling as PriceDriftEnvelope with two retry routes; Session 88 Round 9 dissolved that mechanism in favour of live-price-modal-plus-priceLimit. Session 87's directional thinking still holds; mechanism evolved. Worth flagging that math reviews of locked design substrate should be expected to surface revisions — verification work is supposed to test whether design substrate survives contact with the math.

- **Live-price modal is materially better operator UX than Session 87's snapshot-and-prompt design.** v2 had this; v3 should match per operator. The redesign collapses two flows (favourable / unfavourable drift) into one (operator watches live numbers and decides). Cleaner, less friction, less code to ship. Worth recording that Session 87's design wasn't wrong — it was a less-efficient working draft that the math review sharpened.

- **Multi-rung ladder math is feasible but explicitly out-of-scope for W4 v1.** The spec the operator surfaced is mathematically correct; Claude verified independently. Routing to future arc (matching-layer scope) avoided W4 scope creep while preserving the path forward. Pattern likely repeats: substantive design that surfaces during a session but doesn't fit the immediate arc gets routed cleanly to a future arc with the math captured for reference.

- **Operator energy management drove Route B close.** Operator named fatigue at §5 close and chose to defer §6/§7 rather than push through. §6 (worked numerical examples) and §7 (edge cases / future extensions) are mechanical compared to §1–§5 design work. Better to ship them fresh-mind than tired. Cat 1 split-rather-than-push-through discipline working as designed.

## Open items in (carried forward)

New from Session 88:

- **Math review §6 + §7 deferred to Session 89.** §6 ships two worked numerical examples (one cash hedge, one free-bet hedge) demonstrating Construction A formulas operationally with realistic numbers. §7 ships edge-cases and future-extensions list including the items captured in "Material new items captured for §7" above.
- **Substrate revision flag for W4 brief drafting.** When W4 brief drafting resumes after math review locks, the §4 modal mechanics (live + custom price tandem; `priceLimit`-protected; PERSIST default; match-availability surfacing) supersede the Session 87 Round 9 PriceDriftEnvelope substrate. The four substrate decisions from Session 87 (scope, module placement, placement workflow input shape, cancel/replace + adjust) are otherwise unchanged but extended by §4 mechanics.
- **Effective-odds synthesis as racing-screen → modal flow.** Strategy 2 sub-shape 2 and sub-shape 3 trigger automatic `P_soft_effective` synthesis from racing-screen promo fields when modal opens. W4 brief drafting needs to spec this synthesis explicitly — the racing-screen field set, the synthesis formulas, the modal display of both `P_soft_actual` and `P_soft_effective`. Optimal-stake calculation surfaced both on racing screen and in modal.
- **Default free-bet conversion rate 65%; operator-configurable.** Update from 70% folklore. Math review uses 65% in §6 worked examples when Strategy 2 sub-shape 2 appears.
- **Manual stake override as future refinement.** §7 will flag; not v1 scope.
- **Multi-rung ladder hedge as future arc.** Likely matching-layer scope; candidate DR-032 or later. Math derived and verified in Session 88 conversation; carry forward to future arc.
- **`EX_LADDER` operator-side homework parked.** Surfaced as relevant to multi-rung work but not gating; current entitlement `EX_BEST_OFFERS` (top three) is sufficient for W4 v1.

Carry-forward from Session 87 (status changes):

- **W4 brief drafting paused — four substrate decisions captured.** Status changes from "blocked-on-math-review" to "blocked-on-§6+§7-completion" (§1–§5 are the load-bearing math; §6 worked examples and §7 edge cases need to land before W4 brief drafting fully unblocks). Paragraph-level revision: the four substrate decisions from Session 87 are now extended by Session 88's §4 mechanics revisions per "Substrate revision flag" above.
- **W3 closed** — unchanged; one-session carry concludes at this close per `v3_build_picture.md` rule.
- **Session 42 architectural extension formalisation flagged for before W4.1** — unchanged.
- **F5 strategy_tag carry forward** — unchanged.
- **Deployment-substrate items (F2, F3, F4)** — unchanged.
- **F6 carry-forward** — unchanged.
- **W1 F2 sharpening** — unchanged.
- **W1 F1 accepted as v1.0 conflation** — unchanged.
- **Streaming envelope vocabulary carry** — unchanged.
- **`standing_instructions.md` re-upload** — unchanged; still pending.
- **Post-DR-029-close contract documentation relocation** — unchanged.
- **W0 F2 brief-language carry** — unchanged.
- **W0 F4 typed-stub carry** — unchanged (deployment-substrate).
- **`str_replace` namespace gotcha** — unchanged.
- **`governance.md` §4 deferred-capability reconciliation** — unchanged.
- **DR-030 "18 months" reference correction** — unchanged.
- **§12 self-assessment item 3 — audit-log substrate** — unchanged.
- All other items unchanged from Session 87 carry-forward set.

## Open items out (closed this session)

- **Cycle-equalisation target definition (Session 87 implied; locked Session 88 Round 1).** Equalise net dollars-in-pocket across the two Betfair-side outcomes at whatever level current price-and-stake combination supports. No EV assumptions baked into placement-time math. No free-bet conversion rate folded into placement-time formulas (with one nuance: §5.3/§5.4 effective-odds synthesis is *parameter*, not assumption — operator-configurable).
- **Hedge-staking math review §1–§5.** Drafted, locked, written to disk. Foundation for §6 + §7 next session.

## Session close state

- **Rebuild folder root:** unchanged at session level except `current_state.md` and `v3_build_picture.md` updated at close (W3 drops out per one-session carry rule; W4 milestone-label changes; new `dr029/w4_bet_entry/` directory created with `hedge_staking_math.md` artefact at 1074 lines).
- **`current_state.md`:** updated at close to reflect math review §1–§5 landed, §6/§7 deferred to Session 89, substrate revisions to Session 87 design, default conversion rate downgrade.
- **`v3_build_picture.md`:** updated at close — W3 drops from picture (one-session carry concluded); W4 milestone-label updates from "blocked-on-math-review" to "blocked-on-§6+§7-completion"; detail line shifts to reflect §1–§5 landing plus carryforward.
- **`standing_instructions.md`:** unchanged this session. Re-upload to Project knowledge base still flagged in pending operator-side actions.
- **`governance.md`:** unchanged this session. §4 reconciliation still pending.
- **`decisions.md`:** unchanged this session.
- **`architecture.md`:** unchanged this session. Session 42 extension formalisation deferred to before W4.1.
- **`dr029/w4_bet_entry/`:** new folder created this session; `hedge_staking_math.md` at 1074 lines covering §1–§5.
- **`sessions/`:** Session 88 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 88 opening prompt removed at close; Session 89 opening prompt written.
- **Project knowledge base:** `standing_instructions.md` stale until re-uploaded. All other canonical-truth artefacts current.
- **VPS state:** unchanged this session. No VPS calls.
- **`bethub-v3/`:** unchanged this session. No Code work.
- **`/tmp/`:** no scratch scripts written this session.

## Forward routing

**Confirmed with operator at close:** Session 89 opens fresh chat to land §6 + §7 of the math review and lock the artefact. After §6/§7 land, W4 brief drafting opens (the math review is fully locked substrate at that point).

**Session 89 shape:**

1. **First work:** read `current_state.md` plus `standing_instructions.md` in full plus `project_context.md` plus `sessions/SESSION_88.md` (this file). The §1–§5 substrate, design substrate revisions vs Session 87, and the §6/§7 outline are all captured here.

2. **§6 worked numerical examples authoring** — two worked examples demonstrating §2 Construction A formulas operationally. Likely:
   - **Cash hedge example.** General turnover bet at soft-book at moderate odds (e.g. $50 at 3.0, c = 0.05, Betfair lay at 3.10). Compute S_bf, liability, equalised Net. Show favourable-drift recompute (live-price modal mechanism) and custom-price example. Demonstrate sanity check 1 with non-trivial numbers.
   - **Free-bet hedge example.** Strategy 2 sub-shape 2 free-bet leg at moderate odds (e.g. $100 free bet at 4.0, c = 0.05, Betfair lay at 4.20). Compute S_bf, liability, equalised Net. Compare against a placement at the actual `P_soft_effective` synthesis if Strategy 2 framing applied (this is how the math review demonstrates the synthesis flowing through).

3. **§7 edge cases and future extensions list authoring** — consolidating items captured across §1–§5 into a single forward-looking section. Items list captured in "Material new items captured for §7" above. Approximately 10-15 items, mostly one-paragraph each.

4. **Lock the math review at end of §6/§7 land.** Final write to disk; operator confirms; W4 brief drafting fully unblocked.

5. **If budget allows after math review locks:** open Session 42 architectural extension formalisation. Optional. Three workstreams reference it (W4 hedge-target input shape, W4.1 soft-book entry path, W6 operational store schema). Either extends `architecture.md` §D12 or drafts new DR (DR-032 candidate — Betfair as canonical source extends to all bet records; cycle-linkage join-key formalism). Optional; depends on session budget.

**Out of scope for Session 89:** W4 brief drafting itself (post-math-review session); soft-book typed-price entry math (W4.1 territory); UI behaviour around modal mechanics (W7 territory); multi-rung ladder hedge math implementation (future arc).

**Operator-side actions between sessions:** None required. §6/§7 is in-session work.

## Close-out notes

Session 88 was a substantive design session that ran longer than planned scope because operator clarifications surfaced material design refinements that reshaped Session 87 substrate and tightened the math review's operational accuracy. The artefact (1074 lines covering §1–§5) is materially better for the iterations.

The decision to close at §5 and defer §6/§7 to Session 89 respects fatigue (operator-named) and day-rollover split trigger. §6/§7 are mechanical compared to the design work just completed; they ship cleaner fresh-mind.

Three patterns worth holding onto for Session 89 and beyond:

- **Math reviews of locked design substrate should be expected to surface revisions.** Session 87 Round 9 PriceDriftEnvelope dissolved in Session 88 Round 9 because verification work tested whether the design substrate survived contact with the math. The directional thinking was sound; the mechanism evolved. This is what verification is supposed to do.

- **Operator clarifications on operational reality are the leverage point in design sessions.** Six of twelve rounds in Session 88 turned on operator clarifications — soft-book lay non-existence, dynamic commission per venue, Strategy 1 cycle shape, Strategy 2 sub-shape structure, effective-odds tool-calculated, manual stake override deferral. Claude's framing was the working draft; operator's clarifications were the design refinements that made it operational. The cadence respected this by surfacing each refinement as a call rather than absorbing it silently.

- **Substantive substrate revisions during a session need explicit flagging in the session record and the affected artefact.** Session 88 §4.8 explicitly names the PriceDriftEnvelope dissolution; this session record names six substrate revisions vs Session 87 in "Material substrate revisions vs Session 87" section; current_state.md will reflect the W4 substrate updates. Three layers of documentation prevent silent drift between Session 87's substrate framing and the math review's locked formulas.

§1–§5 locked. §6/§7 deferred to Session 89. W4 brief drafting blocked on §6/§7 completion, then unblocked.
