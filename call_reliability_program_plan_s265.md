# The Call as THE decision indicator — program plan (S265, 4 Aug 2026)

**Operator commission (verbatim intent):** "I would like to make the
CALL item as reliable a data point as possible to advise whether I
should execute a trade or not — ideally a single indicator that all my
decision making is made on." Also: "I will respect the call from now
on" (post-audit).

**Starting evidence (S265 audit, on the operator's own 279 graded
bets + 638-race pressure study):**
- LEAVE is directionally VALIDATED: 24 overrides lost $619 (−53% ROI,
  12.5% win vs 27% implied) while MOD/STRONG ran ~+20%; the drift
  projection behind it works.
- STRONG vs MOD is UNPROVEN separation (statistically
  indistinguishable at n=28 STRONG).
- Thresholds are admitted first-cut constants (three July-16
  anecdotes); the R1 grade backtest (worklist 0h) never ran.
- Back-vs-lay depth imbalance is a real, replicated drift signal
  (638 races, clustered t≈5; lay-heavy shortens, back-heavy drifts)
  but small standalone (~54% vs 52% directional) — an INPUT, not a
  display.
- The grade ignores: order-book pressure, lay-side usability (hedge
  execution reality), place-market prices for insurance triggers.

---

## A. What "reliable single indicator" must mean (the contract)

The Call answers ONE question: **"should I fire this trade at this
stake, right now?"** — combining edge (promo EV), durability (will the
edge survive to the jump), and executability (can the hedge actually
be placed at the assumed price). Its tiers must carry calibrated,
operator-meaningful semantics:

- **STRONG** — fire at full stake; historically ≥X% ROI band.
- **MOD** — fire; standard stake.
- **LEAVE** — do not fire (now validated); if overridden, half stake
  maximum (operator's own rule, 4 Aug).

Reliability = each tier's FORWARD outcomes match its band, measured
monthly on the logged record (the store already stamps grade_at_log on
every bet — the feedback loop exists).

## B. The four inputs to fold in (ranked by evidence)

1. **Lay-side usability → execution gate (HIGH evidence, S252).**
   A promo EV that assumes a hedge near best-back is fiction when the
   lay side is unusable. Gate: lay/back spread ratio, best-lay depth
   vs the armed hedge stake, empty-ladder detection. Effect on Call:
   caps the tier (a STRONG with an unusable hedge is at best MOD for
   cash promos, LEAVE for free-bet conversions where the lay IS the
   trade). First-cut thresholds from the S252 distributions
   (spread >8–10%, depth < stake), tuned in D.
2. **Depth-imbalance pressure → drift projection input (HIGH evidence
   the signal exists, S265 study).** Today drift-vs-firm comes from
   sp_near (BF Close) — the S252 benchmark showed sp_near is WORSE
   than the live book at every horizon. Replace/augment: projected
   price = live book adjusted by the imbalance tercile (direction
   only, magnitude capped at the observed ~3-point differential).
   Expected effect: better LEAVE/not-LEAVE boundary — the tier the
   audit proved carries money.
3. **Grade backtest / band calibration (worklist 0h — the debt).**
   Replay the grade over the capture store's snapshot history for
   every historical logged bet (and a no-bet control sample):
   calibration curves per tier, per code, per time-to-jump bucket.
   Output: tuned thresholds for the STRONG/MOD boundary, verified
   LEAVE bar, trust-gate constants re-derived from data instead of
   the three anecdotes.
4. **Place-market prices for insurance triggers (MEDIUM —
   scoped-only).** Insurance EV rides the 2nd/3rd trigger chance;
   Betfair PLACE markets price exactly that. The capture store holds
   place market ids but never reads them. Scope in D; build only if
   the backtest shows trigger-chance error is a material EV error
   source.

## C. What the Call explicitly will NOT do

- No new columns; the pill (and its hover reasons) stays the whole
  surface. Pressure gets at most the ◂/▸ dot (operator to confirm).
- No auto-execution; the Call advises, the operator fires (standing
  friction rule: warn, never block).
- No overclaiming: tiers display "~" until the calibration in D has
  ≥ agreed sample sizes per tier per code.

## D. Delivery stages

- **D1 — Analysis sitting (offline, capture store + bet record).**
  (i) Re-derive trust-gate + band constants via the 0h backtest
  design; (ii) fit the imbalance adjustment (tercile → drift delta,
  by code); (iii) lay-usability distributions → gate thresholds;
  (iv) quantify trigger-chance error vs place-market implied (sample
  of races where place odds are recoverable) → decide input 4.
  Deliverable: a numbers memo with proposed constants + expected
  tier-ROI bands. ADVERSARIALLY REVIEWED before any code.
- **D2 — Build (red-before, display-only paths).** raceWatcher.ts:
  execution gate + pressure-adjusted projection + tuned constants;
  hover explains WHY (gate reasons named); ◂/▸ dot if approved.
  Suite + the S253-style parity tests against the memo's fixtures.
- **D3 — Live validation window.** 2 race weeks respecting the Call;
  weekly scorecard (per-tier n / win rate / ROI vs band) added to the
  daily money check output so reliability is WATCHED, not assumed.
  Bands adjust only via a repeat of D1's method, never ad hoc.

Sequencing: after the current deploy/0y landing settles; D1 is one
focused sitting; D2 one more; D3 is passive.

## E. Risks / honesty

- n is small in the tails (24 LEAVE, 28 STRONG): bands stay wide and
  hedged until D3 accumulates; the scorecard prints n.
- The pressure effect may shrink under regime change (winter→spring
  carnivals); D3's scorecard catches decay because it re-measures.
- Single-indicator concentration risk: the Call inherits every
  upstream data fault (soft-odds staleness, twin rows). Mitigation:
  the trust gate already caps on data-quality signals; 0y (fresh TAB)
  and the venue/0m work reduce the fault surface independently.
- Place-market capture (input 4) touches the collector — anything
  there rides the standard deploy discipline, and only enters if D1
  proves materiality.

---

## S265 ADVERSARIAL REVIEW — AMENDMENTS (NORMATIVE; D1 must honor these)

Verdict AMEND-FIRST. Blocking: 1–3. All six land here verbatim.

1. **(§B2 rewrite)** The incumbent projection is the S252-corrected
   shrunken tilt: `mid × (sp_near/mid)^β`, β ≈ 0.10–0.18 (validated
   out-of-time on 613k decision points, SESSION_252 §4d — the "drop
   sp_near" reading was RETRACTED there; removing the substitution
   kills LEAVE, proven on the real fixture). D1 fits β per horizon and
   adopts it. Depth-imbalance enters first as a VETO/trust input only
   (direction contradicting the projection → trust cap; signals never
   raise a tier). A magnitude adjustment ships only if D1 beats the
   shrunken-tilt incumbent out-of-time; any cap's units defined
   explicitly. The sp_near substitution is never removed/replaced
   without fixture proof the documented trap cases still grade LEAVE.
2. **(D3 rework)** LEAVE counterfactual ledger (display-only): every
   LEAVE shown at jump logs runner/soft price/projected close and
   settles against BSP — respected LEAVEs still generate outcome data
   (compliance would otherwise destroy LEAVE's feedback). Rolling
   scorecard with per-tier n targets before any "calibrated" claim:
   MOD ≥200 (~2wk), STRONG ≥100 (~7–9wk at 11–17/wk), LEAVE ≥50 via
   the ledger; prints n, per promo kind, and coverage share.
3. **(§B1 rescope)** The execution gate applies ONLY to trades whose
   EV assumes a hedge leg (free-bet conversions), and its effect is an
   EV FLOOR, not a tier cap: lay unusable → EV recomputed at
   unhedged-conversion economics (fbConversionRate floor), tier
   follows THAT EV — never automatic LEAVE (no-hedge-ack precedent
   stands). The gate models the ACTUAL execution path — Take-SP
   MARKET_ON_CLOSE default since S263 (SP-lay liability, not
   click-time depth alone). For cash promos (never hedged — operator
   strategy on record), lay spread/depth feeds the TRUST gate only.
4. **(§B3 honesty tiers)** Every backtest row classified: (a) bet-time
   truth (stored soft_book_combined_price + nearest snapshot,
   staleness noted — ~4.5min cadence mid-window, ~20s inside T-3);
   (b) feed-approximated series (8 captured bookmakers, ~88% of
   graded bets); (c) assumed-promo control rows (arming never
   persisted — assumption declared). Non-feed books (Bet365, BetRight,
   AllBets, CrownBet, UpYaGo) and typed boosted prices excluded from
   series replay or flagged. Mandatory: twin-row dedupe by market id;
   scheduled-vs-actual jump caveat on all time buckets. Place-market
   materiality via place BSP in the Data Portal daily files (jump-time
   truth — adequate for the materiality question only).
5. **(§A contract additions)** Reliability includes COVERAGE: D1
   characterises the 109 ungraded racing-screen cash backs; the
   scorecard reports the share of fired bets carrying a Call. NONE
   stamps distinctly from NULL (display-only tweak). The Call's EV
   basis (qualifying stake = max_stake ?? 100) is stated in the
   contract; stake-band semantics for STRONG vs MOD deferred until D3
   proves the separation. The one-global-bar decision (S245) stands
   unless the operator re-decides; D1 may only report per-kind
   evidence (LEAVE rate differs: bonus 24% vs insurance 8%).
6. **(§A flag)** "STRONG = full stake" is a PROPOSAL pending operator
   lock, not an existing rule; the only operator-owned stake rule is
   LEAVE-override ≤ half stake (4 Aug). Also noted: the S252 fence on
   market-edge modelling stays — the imbalance fit exists solely to
   serve the Call's LEAVE boundary, never an SP model.
