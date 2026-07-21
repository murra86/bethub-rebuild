# B6 panel — SYNTHESIS (judge) output

**Seat:** Synthesis / judge — fresh Claude Opus, no project context, per `b6_gonogo_panel_pack.md` §2/§4.4.
**Run:** 2026-07-06 (Session 230), in-house isolated instance; input = judge prompt + evidence dossier + the three labelled assessments (`b6_panel_skeptic.md`, `b6_panel_validation.md`, `b6_panel_pm.md`).
**Filed verbatim below.**

---

# PANEL RECORD — BetHub v3 Cutover Go/No-Go — Consolidated Synthesis (Judge)

## CONSOLIDATED VERDICT: GO-WITH-CONDITIONS

All three seats independently reached the same verdict: **GO-WITH-CONDITIONS**. There is no dissent on direction — the disagreement is entirely about *how many* conditions and *how long* the coexistence window runs, not about whether the system can eventually flip. That unanimity is itself the strongest signal in the record: three different lenses, given the same dossier, all landed on "the architecture is money-safe, the proof is real but thin, and the cutover mechanics (B6) that actually decide success are unwritten."

The load-bearing facts they all credit: the derive-on-read money rule (DR-019) structurally designs out the "fabricated stake / overpay" bug class; PROOF 1 closed the full loop once on real money at correct magnitude *and sign* (−$4.91); and PROOF 2 showed the park-to-manual safety valve firing under real uncertainty. The load-bearing gap they all name: B6 is NOT STARTED, and B6 is where a cutover is won or lost.

**The flip is authorised once the numbered conditions in §3 are met. It is not authorised today**, principally because B6 does not yet exist, one silent-failure residual (r11) is unfixed, and day-one reference data is unverified.

---

## 1. WHERE THE ASSESSORS AGREE (treat as settled)

1. **Verdict and its basis.** GO-WITH-CONDITIONS, on the ground that money-*movement* safety (never overpay, never fabricate, bias to under-record) is well-founded and partly proven, while money-*supervision* safety (surfacing faults/parks to the human) rests on channels that are mock-proven or discipline-dependent.
2. **r11 is a hard gate, not cosmetic.** All three reject the team's "cosmetic" classification of the invisible worker-enablement condition. A silently-disabled settlement worker is a silent money-supervision failure that already occurred once and was caught only by luck. This is the single most agreed-upon correction to the team's own view.
3. **The live sample is too narrow to call the *class* proven.** n=6, single-leg lays, AU harness/thoroughbred WIN, $3–$9, two days, one non-zero settlement. Enough to retire B1–B3 as *built and directionally correct*; not enough to call the shape-space covered.
4. **Accounts/books reference data is a day-one blocker.** D7 admits it is unreviewed against a real day; with 10–15 live accounts the operator cannot record a real bet if it is incomplete.
5. **In-flight/quiescent flip must be designed.** No carry procedure exists for an open unmatched exchange bet at the flip instant; this is the most likely place to lose or double-count real money.
6. **The residual park-list is largely correct.** All three concur that r1, r3, r4, r5, r6, r7, r8, r9 are correctly parked (money-harmless, cosmetic, or self-dissolving at cutover).
7. **v2 is a clean rollback target** because no mutable money state is shared; the only shared physical resource (VPS tunnel port) is already managed politely by B5, and v2's supervisor must be retired *at* flip, scripted, not left as a manual "remember to."
8. **The daily money check has discipline-dependent gaps on both ends** (the 15:48 log-birth blind spot; cross-day tally is session discipline) and must be written as a runbook step.

---

## 2. WHERE THEY DISAGREE — CLASSIFIED AND RESOLVED

**D-1 (SUBSTANTIVE — the real open question): Coexistence window — calendar-gated or evidence-gated?**
- PM: 24 hours / one full AU racing day, terminated by one clean end-of-day money check.
- SKEPTIC: minimum 3–5 full race days, evidence-gated toward ~weeks.
- VALIDATION: evidence-gated, ~2 weeks or ~20–30 real legs *including at least one partial match and one messy close*, whichever first.

This is not a misread; it is a genuine methodological split. PM gates on *time-clean* (a day with no errors), SKEPTIC/VALIDATION gate on *shape-coverage* (specific unobserved money paths actually occurring). **Resolution: evidence-gating is correct, because the named gaps — a live partial match, a second non-zero settlement, and a live interlock refusal — are concrete money paths that a 24-hour clean run does not guarantee to exercise.** A quiet day proves nothing about partials. The panel adopts an evidence-gated window (§3 cond. 9). The *floor* PM identifies (at least one full clean racing day) is a necessary-but-not-sufficient sub-condition, folded in.

**D-2 (SUBSTANTIVE, escalate to operator judgment): Must a live *partial match* be observed before the flip?**
- VALIDATION makes it a hard Phase-0 gate; SKEPTIC wants it; PM lists partial-then-lapse only as an *invalidating* event, not a required precondition.

A partial match may not occur naturally within any bounded window at $3–$9 stakes. Making it a hard gate risks blocking the flip indefinitely on an event the operator cannot force. **Resolution: this is the one condition the panel cannot mechanically settle — it is a real risk-vs-schedule trade the operator must decide.** Recommended: require the partial-match observation as a gate *if* it occurs within the window; if the window otherwise completes without a partial ever appearing, permit flip with the partial-then-lapse guard remaining code-verified-only, on the explicit record that its Betfair size-cancelled assumption (D5.e) is unconfirmed-by-observation and its failure direction is "park safely." Flagged as a surfaced substantive residual, not resolved.

**D-3 (LENS-BASED): Severity framing of the coexistence model.** PM = near-hard flip, v2 "completely dormant but configured," ready in minutes. SKEPTIC = true multi-day parallel where v2 still handles ongoing/settling bets. VALIDATION = shadow/parallel where v3 already places the real legs (correct: the six proofs *were* real v3 placements). Different risk tolerance, not a factual conflict. **Resolution: adopt VALIDATION's framing — v3 is already the placement instrument; the window's purpose is to keep v2 as system-of-record and warm rollback target until evidence accrues, then transfer record-of-truth at a quiescent flip.**

**D-4 (LENS-BASED, near-factual): EV-figure accuracy as a gate.** SKEPTIC wants operator EV sign-off as a day-one item; VALIDATION and the dossier call it non-gating for *software* readiness but flag it as unverified live data; PM makes it CL-01 eyeball. No factual conflict — the dossier explicitly marks it non-gating. **Resolution: not a software gate, but a cheap day-one data-quality step; include as a low-cost condition (§3 cond. 10).**

**D-5 (LENS-BASED): r2 and r10 severity.** VALIDATION elevates r2 (unwired stake-invariant-less placement fn) and r10 (cross-day tally) to *documented conditions*; SKEPTIC and PM leave them parked. Not a misread — VALIDATION simply wants the latent overpay vector fenced with a test and the discipline gap runbooked. **Resolution: adopt VALIDATION's cheap fences (§3 cond. 8 and cond. 7) — zero cost, removes a latent landmine and a discipline dependency.**

No **factual misreads** were found — all three seats read the dossier consistently. Every divergence is lens-based (risk tolerance) or substantive (D-1, D-2).

---

## 3. CONSOLIDATED CONDITIONS (each stated as a checkable event/artefact)

**Hard gates — flip is not authorised until all are ticked:**

1. **B6 authored and reviewed.** A written cutover runbook AND a written rollback procedure/script exist and have been reviewed. *Tick when: the B6 document exists in the repo and covers pre-flight, flip, and rollback steps.* (This is the panel's own deliverable domain and is currently NOT STARTED — it is condition zero.)
2. **r11 fixed.** The launcher echoes each worker's enabled/disabled state at startup, AND the fault banner (or launcher) raises if an expected worker is not running. *Tick when: a launch visibly prints SETTLEMENT_WORKER / RECONCILIATION_WORKER state, and a deliberately-disabled worker produces a visible alert.*
3. **Accounts/books reference data verified.** The 10–15 active bookmaker accounts are registered in v3's store and reviewed complete against one real day's workflow. *Tick when: operator confirms a real bet can be recorded/tagged against every account in current rotation.*
4. **Quiescent-flip precondition written and met.** Cutover checklist states "no open unmatched exchange bets at flip," AND a documented manual orphan-bet reconciliation procedure exists. *Tick when: the checklist line exists and the flip is executed from a confirmed-empty in-flight state.*
5. **Worker always-on defaults decided and recorded.** *Tick when: a decision record states the post-cutover worker-start policy and the launcher enforces it.*
6. **v2 tunnel-supervisor retirement scripted into the cutover** (not manual). *Tick when: the runbook step decommissions v2's supervisor and confirms v3 owns the port healthily.*
7. **Durable log + daily money check live from first minute, procedure runbooked.** *Tick when: no second "log-birth blind spot" exists on cutover day, and the daily-check cadence is a written runbook step (closes r10 / D4.3).*
8. **r2 fenced.** A test/guard fails if the unwired placement function ever gains a caller. *Tick when: that test exists and is green (i.e., still caller-less).*
9. **Evidence-gated coexistence window completed** (see §4). At minimum: ≥1 full clean AU racing day AND one live interlock-refusal trip AND one non-zero settlement beyond the −$4.91. *Tick when: all three observed and each day's money check signed off.* (Partial-match observation per D-2 — operator-elective gate.)

**Low-cost data-quality condition (not a software gate):**

10. **EV-figure eyeball.** Operator signs off the 9 seeded promo rows for EV accuracy. *Tick when: sign-off recorded.*

---

## 4. CONSOLIDATED DAY-ONE + COEXISTENCE + ROLLBACK CHECKLIST (deduplicated)

**DAY-ONE STATE (v3 at flip):**
- [ ] Promo catalogue: 9 rows seeded (done) + EV eyeball sign-off (cond. 10).
- [ ] Bookmaker accounts/books reference data registered and reviewed complete (cond. 3). *[all three]*
- [ ] Launcher starts tunnel + required workers with *visible* worker-enablement confirmation (cond. 2).
- [ ] Durable log + placement-audit journal active from first minute (cond. 7).
- [ ] Daily money check runnable, procedure documented (cond. 7).
- [ ] Clean-state baseline: manual queue empty (currently true); the six terminal proof bets confirmed not to pollute the operator's working view (r4 confusion). *[VALIDATION single-source on the pollution check — worth a 30-second look, cheap.]*
- [ ] In-tool v2-vs-v3 indicator to prevent double-entry confusion. *[SKEPTIC single-source — scrutinise: useful if both UIs are open, but if the coexistence model keeps v2 dormant/closed (PM), lower value. Include only if v2 stays interactively open during the window.]*

**COEXISTENCE WINDOW:**
- Model: v3 places all real hedge legs (already the case); **v2 remains the warm rollback target and system-of-record until the evidence gate closes**, then record-of-truth transfers at a quiescent flip.
- Duration: **evidence-gated, not calendar-gated** — held open until cond. 9 events observed; PM's "one full clean racing day" is the floor, not the finish line.
- Shared tunnel: B5 manages the port; v2 supervisor stays until scripted retirement at flip (r5 noise is tolerated meanwhile).
- Daily: run v3 money check and reconcile key outcomes against Betfair statements each day. *[SKEPTIC adds cross-check against v2's view — include only for bets both tools can see; single-source.]*

**ROLLBACK:**
- Trigger (merged, deduplicated): any money discrepancy or silent-loss/data mismatch in the daily check; an unresolvable park v2 would have handled; worker stall >15 min during live racing; tunnel deadlock >5 min; worker-failure masking (the r11 condition); or operator discomfort. *(SKEPTIC's >15–30 min and PM's >15 min reconciled to >15 min.)*
- Mechanics: stop v3 + workers → **manually cancel v3's unmatched exchange orders on Betfair's native interface and hand-record matched stakes/prices** → relaunch v2 (its supervisor reclaims the port) → manage v3-legacy positions from Betfair statements via the manual queue → v2 drives new bets.
- **Orphan symmetry (VALIDATION single-source, but sound):** rollback has the *same* in-flight-bet problem as forward cutover — take rollback from quiescence where possible; the park-to-manual valve is what makes a single orphaned bet survivable. Worth including — it closes a real gap the other two under-weighted.
- Keep v2 warm for **≥1 full settlement cycle** beyond flip (PM: minutes-ready; VALIDATION: 1–2 weeks). Adopt: v2 stays installed and runnable for at least one full settlement cycle, with no hard deletion until the window's evidence gate is retrospectively clean.

*Single-source items flagged for scrutiny above: v2/v3 UI indicator (SKEPTIC), proof-bet view-pollution check (VALIDATION), v2-side money cross-check (SKEPTIC), rollback-orphan symmetry (VALIDATION). The last is substantive and recommended; the first is conditional on the coexistence model; the middle two are cheap and worth doing.*

---

## 5. BLIND-SPOT CHECKS TO ACTUALLY RUN — ranked by cost-to-check vs risk-if-real

1. **Operational SQLite store backup/restore posture** (VALIDATION). *Cheapest to check, highest downside.* Code is on GitHub; the *money store* is on the operator's Mac with no stated backup. With no history migration, a lost/corrupt file on day one = total operational-state loss. Check: confirm a backup exists and a restore has been tried. **Run first.**
2. **Mac local-environment readiness** (PM): durable-log directory permissions, local port availability, dependencies outside the dev context. Cheap; a failure blocks launch or silently kills logging on cutover day. **Run before flip.**
3. **Always-attended-usage confirmation** (VALIDATION #7). One question to the operator; validates the *entire* parked monitoring-scope decision (the parked phone alarm, "a dead app can't self-report unattended"). Cheap, medium risk. **Confirm explicitly.**
4. **Secrets/credential handling** for Betfair + bookmaker accounts (VALIDATION, PM). Low-medium cost; a payments-adjacent tool needs a stated posture. **Document.**
5. **Worker crash-recovery / settlement-state idempotency mid-cycle** (VALIDATION #1). What happens on a crash *between* recording a matched stake and stamping settlement, or mid-reconciliation — double-settle/double-book? Placement-audit journal is crash-safe; the settlement state machine's crash-safety is not established. Medium cost, high risk. **Test before declaring the window clean.**
6. **Double-place / concurrency protection** (SKEPTIC, VALIDATION #3). Is there an idempotency key against a double-clicked place or a reconnect-mid-place? The operator already double-clicked the launcher (r11), so double-input is demonstrated behaviour. Medium cost, high risk.
7. **Betfair adversarial API failure modes** (VALIDATION #2, SKEPTIC): 5xx, auth-token expiry, rate-limit, and especially a *malformed/wrong* cleared-orders response (not "no signal → park," but "wrong signal → mis-settle"). Medium cost, medium-high risk.
8. **Exchange exposure/balance-limit handling during a live session** (PM). Medium cost, medium risk.

Lower priority (medium cost, contained risk): full end-to-end operator UI day-walkthrough (SKEPTIC); derive-on-read P&L reconstructability without in-memory state (SKEPTIC); settlement-gate clock/timezone robustness given Betfair's missing settled-time field across market types (VALIDATION #4). Scale-to-10–15-accounts/performance (SKEPTIC) is deferred — cutover is at current scale, so it gates *growth*, not the flip.

---

**PANEL DISPOSITION:** GO-WITH-CONDITIONS. The build is a genuinely money-safe foundation with real (if thin) live proof; it is not a lab prototype, but neither is it a proven daily driver. Author B6, close the nine hard gates — chief among them the unwritten cutover mechanics, the r11 silent-worker fix, and verified reference data — run the evidence-gated parallel window, and flip from quiescence. The two items the panel deliberately leaves to the operator: whether to hard-gate on observing a live partial match (D-2), and the exact length of the warm-v2 rollback tail.
