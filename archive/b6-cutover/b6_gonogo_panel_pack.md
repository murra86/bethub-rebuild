# B6 go/no-go panel pack — the multi-agent cutover-readiness review commission

**Drafted:** 2026-07-06 17:15 ACST (Session 230), per the S229-confirmed first action.
**Status: DRAFT — operator review required before any seat runs. Nothing has been sent
to any external service. This document only becomes a review when the operator pastes
its parts into the outside models.**
**Pattern source:** `governance.md` — multi-agent governance review pattern (Sessions
20–26 established it; this is its second full use).
**Subject:** the pre-W16 cutover go/no-go — is BetHub v3's money path proven enough to
retire v2 and run the day on v3, and what must the flip itself contain.

---

## 0. How to use this pack (operator guide)

The pack has five parts. You only handle three of them:

1. **§2 Seat design** — confirm (or change) which outside model sits in which seat.
2. **§4 Per-seat prompts** — one paste-ready prompt per seat. Each prompt tells the
   model its role and its questions.
3. **§5 Evidence dossier** — one self-contained document every seat gets. Paste it
   into the same message as (or immediately after) the seat prompt.

**Run order:** the three assessment seats (§4.1–§4.3) run independently, in any order,
in fresh chats with no shared history. The judge (§4.4) runs **last**, and gets the
three assessments plus the dossier.

**Where outputs land:** save each seat's full response verbatim into the rebuild folder
root as:

- `b6_panel_skeptic.md`
- `b6_panel_validation.md`
- `b6_panel_pm.md`
- `b6_panel_synthesis.md` (the judge)

Copy-paste the model's answer into a text file with that name (or hand each response to
the next Chat/governance session and it will file them). Once all four exist, the next
governance session triages the synthesis and shapes B6 scoping from the verdict.

**Privacy note (one-time confirm):** everything pasted into an outside model leaves the
machine and lands on that provider's servers. The dossier contains real Betfair bet IDs,
real (small) money figures, and a description of the operation's Strategy-1 shape. It
contains **no** account names, credentials, bookmaker account identities, or personal
details. Confirm you're comfortable with that content going to the seat providers before
running.

---

## 1. The question set — what the panel answers

Five questions, asked of every assessment seat (each seat weighs them through its own
lens):

- **Q1 — Go/no-go on the evidence.** Based on the dossier, is the money path proven
  enough to cut over from v2 to v3? If no: what specific additional proof would change
  the answer, stated as observable events (not "more testing").
- **Q2 — Residual risk.** Of the named residuals and honest classifications in the
  dossier (§5.5, §5.6), which — if any — should gate the flip, and why? Which are
  correctly parked?
- **Q3 — Day-one state.** v3 starts fresh (no transaction history carried from v2, by
  locked decision). What must exist in v3 at the moment of go-live for the operator to
  run a normal day? Enumerate concretely.
- **Q4 — Coexistence and rollback.** What should the v2↔v3 coexistence window look
  like — length, what stays live in v2, the trigger conditions for falling back, and
  what "fallback" mechanically means once real bets exist in v3?
- **Q5 — Blind spots.** What would you check before this cutover that the evidence
  dossier does not mention? Assume the authors are anchored; hunt for the unasked
  question.

---

## 2. Seat design (proposed — operator confirms)

Per the `governance.md` pattern: mix model families, because same-family sessions share
priors and converge. Each seat is stacked against a specific failure mode of this
decision.

| Seat | Proposed model | Why this model / what failure mode it covers |
|---|---|---|
| **Skeptic** | **Grok** (fresh chat) | Pushes hardest on coherence; willing to call the whole framing wrong. Covers: "the evidence pack is self-congratulatory and the real risk is unstated." |
| **Validation (technical)** | **Claude Opus** (fresh chat, NO project context, not this account's Project) | Software-developer read: is the proof chain technically sound, do the live-proofs actually demonstrate what they claim. Fresh-session Claude is deliberately outside the 200+-session anchoring. |
| **Structuring / PM** | **Gemini** (fresh chat) | Sequencing, dependency, and risk-management framing — strongest on Q3/Q4 (day-one checklist, rollback design). |
| **Synthesis (judge)** | **Claude Opus** (fresh chat, no project context) | Synthesise rather than choose: where the three agree, where they disagree and why, and the recommendation set that emerges. Runs last. |

**ChatGPT — proposed EXCLUDED, flag per the pattern.** ChatGPT was excluded from the
Sessions 20–26 review over its gambling-content safety posture. This review is more
gambling-loaded than that one (live lay placement, settlement, real money on a betting
exchange), so the same constraint applies with more force. If the operator wants a
fourth assessment seat anyway, ChatGPT could take a narrowed, mechanics-only brief
(Q3/Q4 only — day-one state and rollback, no betting-strategy content), but the default
proposal is three assessment seats + judge, no ChatGPT.

**Operator decisions — CONFIRMED S230 (2026-07-06):**
1. Seat/model assignments confirmed as proposed above.
2. ChatGPT confirmed OUT.
3. Dossier content confirmed as-is (real bet IDs + money figures stay; privacy note
   accepted).
4. Run mechanics amendment: the two Claude seats (validation §4.2, judge §4.4) run
   in-house as fresh isolated Claude Opus instances receiving only the seat prompt +
   dossier — same fresh-eyes guarantee, less operator effort. Operator runs Grok
   (skeptic §4.1) and Gemini (PM §4.3) only.

---

## 3. Run mechanics

1. **Seat runs are independent.** Open a fresh chat per seat (no project attachments,
   no prior history). Paste the seat prompt (§4.x), then the full evidence dossier (§5).
   If the interface has a length limit, send the prompt first, then the dossier in a
   second message — the prompts tell the model to wait for the dossier.
2. **Take the response verbatim.** No follow-up coaching beyond clarifying questions
   the model itself asks (answer factually from the dossier; if the answer isn't in the
   dossier, say "not established — treat as unknown"). If a model refuses on
   gambling-content grounds, stop that seat and note it — don't re-prompt around a
   refusal.
3. **File each output** under the §0 filenames.
4. **Judge runs last:** paste §4.4, then the dossier, then all three assessments
   (labelled SKEPTIC / VALIDATION / PM).
5. **Synthesis session:** the next governance session reads `b6_panel_synthesis.md`
   (plus the three assessments), triages the verdict with the operator, and turns it
   into the B6 scope — cutover mechanics, day-one checklist, coexistence/rollback plan,
   and the v2 tunnel-supervisor retirement.

Expected operator effort: roughly 30–45 minutes across the four chats, at leisure —
seats can run on different days; the dossier is stable until code changes.

---

## 4. Per-seat prompts (paste-ready)

### 4.1 Skeptic seat (proposed: Grok)

```
You are the SKEPTIC seat on a go/no-go review panel for a software cutover.

Context in one paragraph: a solo operator runs a betting operation on ~10-15
Australian bookmaker accounts. His main strategy places promoted "insurance"
bets at bookmakers and hedges ("lays") on the Betfair exchange. His current
tool (v2) is being replaced by a ground-up rebuild (v3). The v3 team believes
the money path is now proven end-to-end on real money and wants to schedule
the cutover. You are here to attack that belief.

You will next receive an EVIDENCE DOSSIER written by the v3 team. Treat it as
a document written by people who want the answer to be "go". Your job:

1. Answer Q1-Q5 below, leading with your overall verdict (GO / NO-GO /
   GO-WITH-CONDITIONS) and your confidence in it.
2. Attack the proof chain: what do the live-proofs actually demonstrate vs
   what the dossier claims they demonstrate? Where is one observed instance
   being treated as a proven class?
3. Name the single most likely way this cutover goes wrong in the first two
   weeks, concretely.
4. Be willing to say the framing itself is wrong (e.g. "the question isn't
   whether the money path works, it's X").

The five panel questions:
Q1 Is the money path proven enough to cut over? If no, what observable
   events would change your answer?
Q2 Which named residuals should gate the flip? Which are correctly parked?
Q3 What must exist in v3 on day one (fresh start, no history migration)?
Q4 What should the v2/v3 coexistence + rollback window look like?
Q5 What would you check that the dossier doesn't mention?

Constraints: base your assessment only on the dossier; where it is silent,
say "not established" rather than assuming. Do not advise on betting
strategy, staking, or how to avoid bookmaker detection - this review is
strictly about whether the SOFTWARE is ready. Wait for the dossier before
answering.
```

### 4.2 Validation seat (proposed: fresh Claude Opus, no project context)

```
You are the VALIDATION seat on a go/no-go review panel for a software
cutover. You are a senior software engineer with settlement/payments-adjacent
experience, seeing this project for the first time.

Context in one paragraph: a solo operator runs a betting operation on ~10-15
Australian bookmaker accounts. His main strategy places promoted "insurance"
bets at bookmakers and hedges ("lays") on the Betfair exchange. His current
tool (v2, Flask/SQLite/React) is being replaced by a ground-up rebuild (v3,
FastAPI/SQLite/React). The v3 team reports the money path live-proven on real
money and asks whether it is technically sound to cut over.

You will next receive an EVIDENCE DOSSIER. Assess it as an engineer:

1. Answer Q1-Q5 below, leading with your verdict (GO / NO-GO /
   GO-WITH-CONDITIONS).
2. Judge the proof chain's technical soundness: do the described live-proofs,
   test counts, and adversarial-verification passes actually support the
   claimed status of each component? Distinguish "exercised once live" from
   "proven under the range of conditions a live fortnight will produce".
3. Pay particular attention to the honest-classification ledger (things the
   team itself marks as mock-proven or unit-tested-only) and the residual
   register: which entries would YOU refuse to ship over?
4. Assess the safety posture: the system's stated failure direction is
   "hold/park and ask the operator, never fabricate money". Does the evidence
   support that this direction holds under failure, not just under success?

The five panel questions:
Q1 Is the money path proven enough to cut over? If no, what observable
   events would change your answer?
Q2 Which named residuals should gate the flip? Which are correctly parked?
Q3 What must exist in v3 on day one (fresh start, no history migration)?
Q4 What should the v2/v3 coexistence + rollback window look like?
Q5 What would you check that the dossier doesn't mention?

Constraints: base your assessment only on the dossier; where it is silent,
say "not established". Software readiness only - no betting-strategy advice.
Wait for the dossier before answering.
```

### 4.3 Structuring / PM seat (proposed: Gemini)

```
You are the PROJECT-MANAGEMENT seat on a go/no-go review panel for a software
cutover. Your lens: sequencing, dependencies, operational readiness, and
rollback design - not code.

Context in one paragraph: a solo operator runs a betting operation on ~10-15
Australian bookmaker accounts; his main strategy places promoted "insurance"
bets at bookmakers and hedges ("lays") on the Betfair exchange. His current
tool (v2) keeps running until the rebuilt tool (v3) takes over. v3 starts
with an empty database by locked decision - no history is migrated. The team
reports the money path proven and wants to plan the flip.

You will next receive an EVIDENCE DOSSIER. Your deliverables:

1. Answers to Q1-Q5 below, leading with your verdict (GO / NO-GO /
   GO-WITH-CONDITIONS).
2. A concrete DAY-ONE CHECKLIST: every piece of reference data, configuration,
   environment state, and operator knowledge that must exist at go-live for a
   normal working day to succeed on v3. Mark each item seed-once vs ongoing.
3. A COEXISTENCE/ROLLBACK PLAN skeleton: recommended window length, what
   stays live in v2 during it, explicit fallback trigger conditions, and what
   falling back mechanically requires once v3 holds real bets that v2 has
   never seen. Include the in-flight-bet problem: what happens to a live
   unmatched exchange bet placed from v3 if the operator falls back mid-day?
4. The cutover-day runbook shape: the ordered steps of the flip itself,
   including retiring v2's separate tunnel-supervisor script (named in the
   dossier) without breaking v2 while it's still the fallback.

The five panel questions:
Q1 Is the money path proven enough to cut over? If no, what observable
   events would change your answer?
Q2 Which named residuals should gate the flip? Which are correctly parked?
Q3 What must exist in v3 on day one?
Q4 What should the coexistence + rollback window look like?
Q5 What would you check that the dossier doesn't mention?

Constraints: base your assessment only on the dossier; where it is silent,
say "not established". Software/operational readiness only - no betting-
strategy advice. Wait for the dossier before answering.
```

### 4.4 Synthesis / judge seat (proposed: fresh Claude Opus, no project context)

```
You are the JUDGE on a go/no-go review panel for a software cutover. Three
independent assessors (SKEPTIC, VALIDATION, PM) have each reviewed the same
evidence dossier for a betting-management tool's v2-to-v3 cutover. You will
receive: (1) the evidence dossier, (2) the three assessments, labelled.

Your job is to SYNTHESISE, not to re-review and not to pick a winner:

1. Where do the three assessors AGREE? (These points are close to settled.)
2. Where do they DISAGREE, and is the disagreement factual (one misread the
   dossier), lens-based (different risk tolerance), or substantive (a real
   open question)? Resolve factual ones; surface substantive ones.
3. Produce the CONSOLIDATED VERDICT: GO / NO-GO / GO-WITH-CONDITIONS. If
   conditions: a numbered, checkable list - each condition stated as an
   observable event or artefact, so the team can tick it off unambiguously.
4. Produce the CONSOLIDATED DAY-ONE + ROLLBACK requirements: merge the
   assessors' Q3/Q4 answers into one deduplicated checklist, flagging any
   item only one assessor raised (single-source items deserve scrutiny, not
   automatic inclusion).
5. List the top blind-spot checks from the assessors' Q5 answers that the
   team should actually run, ranked by cost-to-check vs risk-if-real.

Lead with the consolidated verdict. Wait for the dossier and the three
assessments before answering.
```

---

## 5. Evidence dossier (paste-ready — every seat gets this, verbatim)

```
=== EVIDENCE DOSSIER: BetHub v3 cutover-readiness (compiled 2026-07-06) ===

Read this as the factual record. It was compiled by the build team; the
honest-classification ledger (D5) and residual register (D6) list everything
the team itself knows to be unproven or imperfect.

--- D1. THE SYSTEM AND THE DECISION ---

BetHub v2: Flask/SQLite/React betting-management tool, built Mar-Apr 2026,
runs the operator's day today. Frozen (bug fixes only) during the rebuild.

BetHub v3: ground-up rebuild (FastAPI/SQLite/React on the operator's Mac),
governed by numbered locked decision records. Two-database architecture:
v3's own operational store (bets, promos, settlement state) is separate from
an analytical capture database on a remote VPS, integrated by reference only.
Key money rule (DR-019): money is DERIVED ON READ from the recorded matched
stake and price - settlement stamps state, it never writes money magnitudes.
Design failure-direction: when the system cannot conclusively determine an
outcome it HOLDS or PARKS the bet to a manual review queue; it never guesses,
never fabricates a stake, and biases to under-record rather than overpay.

Cutover scope (operator-locked): Strategy-1 parity is sufficient to flip.
Strategy 1 ("Safety Net"): place a promoted insurance bet at a bookmaker,
optionally hedge by LAYING the runner on Betfair exchange through the tool.
The Betfair leg of v3's workflow is lay-only by design (the hedge tool);
placing BACK bets on Betfair through v3 is not part of cutover scope.
v3 starts fresh at cutover: NO bet/transaction history migrates from v2
(locked decision). v2 keeps running in parallel until the flip completes.
Scale: ~10-15 bookmaker accounts in rotation today; design target ~30.

The decision under review: is v3 ready to become the daily tool (cutover),
and what must the flip contain (day-one state, coexistence window, rollback)?

--- D2. THE BLOCKER MAP AND ITS STATUS ---

The team tracked 7 cutover blockers (B1-B7). Current status:

B1 Lay placement live-proving ............ CLEARED (evidence in D3)
B2 Auto-settlement worker live-proving ... CLEARED (evidence in D3)
B3 Match-reconciliation live-proving ..... CLEARED (evidence in D3)
B4 Promo catalogue seeded ................ CLEARED (9 promo rows seeded to
   the live store, operator-confirmed visible in the race-page picker;
   EV-figure accuracy eyeball by the operator still pending, non-gating)
B5 VPS tunnel auto-start + health ........ CLEARED (built + live-tested, D4)
B7 Monitoring/observability .............. CLEARED (built, D4)
B6 Cutover mechanics / day-one / rollback  NOT STARTED - it is what this
   panel's verdict shapes.

Code state: test suite 1383 passing, frontend suite 130 passing, working
tree clean, pushed to a private GitHub remote. All money-path fixes were
built with red-before-green tests and independent adversarial verification
passes (3 review lenses attacking each fix; findings fixed before merge).

--- D3. THE MONEY-PATH PROOF TRAIL (all real Betfair, real money, operator-
supervised) ---

Six real lay bets were placed through v3 against live Betfair across three
supervised sessions (2026-07-05/06). Every proof below is an observed event
in the running app against the real exchange, not a test fixture.

PROOF 1 - matched lay, true money end-to-end. LAY $3.15 at Shepparton
(Betfair bet 434257406420). Placed unmatched -> store recorded it pending
with matched stake 0. It matched on Betfair -> the reconciliation worker
wrote the TRUE matched stake ($3.15 @ 2.56). The settlement gate held it
while the race ran. Race closed; the layed runner WON; the settlement worker
booked the LAY-side loss: -$4.91 (= 3.15 x (2.56-1)) - real magnitude,
correct direction, correct value. Betfair's own market close had a quirk
(no settled-time field) and the worker resolved correctly anyway.

PROOF 2 - never-matched lay, the safety valve. LAY $8.33 left to lapse at
the jump (bet 434257942837). Reconciliation swept it 3 times over ~10 min,
got no conclusive "never matched" signal from Betfair's cleared-orders API,
and REFUSED TO GUESS: it parked the bet to the manual review queue with $0
money and no settlement. This is the load-bearing safety behaviour observed
on real money: uncertainty escalates to the operator, it is never resolved
by assumption.

PROOF 3 - the lapse gap found, fixed, and re-proven live. Investigating why
PROOF 2 parked instead of auto-resolving, the team MEASURED real Betfair
behaviour (a read-only watcher over 5 real lapsing lays): Betfair files a
never-matched order under cleared-orders status LAPSED within ~2 minutes of
the jump - never under SETTLED, the only status the resolver queried. Fix:
the resolver now also checks LAPSED (and CANCELLED), and only auto-fails a
bet when the lapsed-back size equals the FULL requested stake - any partial
shape still parks to the manual queue. 8 new tests red-before-green; 3
adversarial lenses tried to make it mis-fail a matched bet and found no
reachable path. LIVE-PROOF same day: on the next app launch the first sweep
auto-resolved all four measurement lays to FAILED/$0 in one pass.

PROOF 4 - settlement stamps terminal, ledger untouched. A supervised
settlement window (2026-07-06): the settlement worker's first pass stamped
all four $0 no-bet lays from PROOF 3 terminal (settled, $0 money), and the
cash-flow ledger was confirmed untouched (zero money rows - correct, since
money derives on read and these were no-bets). BONUS: PROOF 2's parked bet
self-resolved during this window - under the PROOF 3 fix, reconciliation
finally got its conclusive lapse signal and the bet was stamped
failed/$0/voided. The manual queue is now EMPTY.

PROOF 5 - the placement interlock held throughout. All six lays went through
a genuinely SUBSCRIBED live price stream (placement is interlocked: the tool
refuses to place when the stream isn't live). A real stream defect found on
first live launch (a 64KiB read-buffer overflow on the full-country racing
image causing a reconnect loop) was fixed, adversarially verified, and the
stream then held SUBSCRIBED through two full sessions including a restart.

Money summary across all proofs: one real settled loss of -$4.91 (correct),
five $0 no-bets (all correctly terminal), zero fabricated values, zero
overpays, manual queue empty.

--- D4. OPERABILITY BUILDS (supporting, all landed 2026-07-06) ---

B5 tunnel: v3's race-lookup for late bet entry rides an SSH tunnel to the
VPS. The launcher now auto-starts it and runs a health-gated watchdog
(redials only when the port is actually dead; coexists with v2's own
tunnel-supervisor script, which v2 still needs until cutover - v3 reuses a
healthy tunnel and never kills one it didn't start). Live-tested 4-case
matrix: cold start / kill-and-respawn ~15s / worst-case teardown / v2
coexistence and handback. NOTE for Q3/Q4: v2's separate supervisor script
must be retired AT cutover, not before.

B7 observability, three pieces:
 1. Durable app log: all app activity to a daily-rotating file, retained
    permanently (operator call), plus a placement-audit journal - one JSON
    line per real place/cancel/replace, crash-safe, with a no-silent-loss
    fallback. Closes the prior gap where audit records lived in memory only.
 2. In-tool fault banner: both workers report health; a banner (silent when
    healthy) shows plain-words alerts on worker stall/error, price-feed
    drop, or lost contact with the backend. OPERATOR SCOPE CALL: a phone/
    push alarm for unattended running was deliberately PARKED - faults only
    matter in use today; the money path degrades hold-not-overpay; revisit
    at unattended/30-account scale. Named accepted caveat: a dead app cannot
    self-report while unattended.
 3. Daily money check: a one-command read-only review that pulls a day's
    settlement/reconciliation decisions from the durable log, joins money
    and bet-cycles from the store read-only, and flags every full-payout
    decision and every park for human eyes. Live-run clean. Known one-off:
    decisions made before the log's birth (15:48 on 2026-07-06) are
    invisible to it.

--- D5. HONEST-CLASSIFICATION LEDGER (the team's own not-fully-proven list) ---

The team classifies every feature as live-proven (exercised against the real
system in the running app) / implemented-mock-proven (built + tested, not yet
observed live) / unit-tested-only. Items NOT at live-proven:

 a. B7 piece 1 (durable logs) and piece 2 (fault banner): implemented +
    mock-proven. Passive live confirm expected at the next real launch
    (diary grows; banner stays silent). The banner's fault states have never
    been triggered by a real fault.
 b. B5 in-app ride-along: tunnel mechanics live-proven (real SSH, real VPS,
    real kills), but a full live day of race lookups through the launcher-
    owned tunnel hasn't happened yet.
 c. The placement interlock's REFUSAL path (blocking placement when the
    stream is down): unit-tested only, never tripped live. Failure direction
    is money-safe (refuses to place).
 d. BACK-bet settlement on Betfair: implemented + unit-tested, no live path
    until a back-entry UI exists. Out of cutover scope (lay-only tool).
 e. Partial-match-then-lapse on Betfair: the resolver's guard for it is
    adversarially verified in code, but the shape has never occurred live;
    the guard's assumption about Betfair's size-cancelled semantics on
    partials is per-docs, unconfirmed by observation (parks safely if wrong).
 f. Six real bets is the entire live sample. All at minimal stakes ($3-$9),
    all AU harness/thoroughbred WIN markets, all single-leg lays, two
    calendar days.

--- D6. RESIDUAL REGISTER (named, parked, non-blocking per the team) ---

Money-adjacent:
 r1. A bet-leg table column keeps a stale matched-stake copy after post-
     placement reconciliation; verified money-harmless (nothing on the money
     path reads it); hardening parked.
 r2. An unwired internal placement function has no invariant tying proposed
     stake to recorded stake; unreachable today (no caller).
 r3. Carried-forward reconciliation retries re-pay 3 Betfair read calls per
     sweep until the park valve bounds them (cost, not correctness).
Display-only:
 r4. Bet log shows "$0 at $0" for unmatched pending bets, no requested-stake
     detail; a settled no-bet shows badge "Won"/$0 (market outcome vs $0
     money) - cosmetically confusing, money-correct per derive-on-read.
Ops:
 r5. v2's tunnel supervisor uselessly redials every ~5s while v3 owns the
     tunnel port (auth-log noise on the VPS; self-heals; dissolves when the
     supervisor is retired at cutover).
 r6. Nothing starts the tunnel at machine boot if the operator goes straight
     to v2 (v3 launch covers the common case).
 r7. A half-open tunnel can serve errors for up to ~30s before the watchdog
     redials.
 r8. Web-server access lines aren't in the durable diary (app records only).
 r9. The placement-audit journal never rotates (one line per real placement;
     years to matter).
 r10. The daily money check's cross-day tally is session discipline, not
     code.
 r11. The launcher doesn't echo which workers are enabled at startup; one
     supervised launch was run with the settlement worker accidentally OFF
     (double-click launch dropped the env flag) and was caught by manual
     process inspection. (Team classifies cosmetic; note the operational
     angle: worker-enablement is currently an invisible launch condition.)

--- D7. KNOWNS FOR DAY-ONE / COEXISTENCE (input to Q3/Q4, not yet designed) ---

 - v3 store already holds: the seeded promo catalogue (9 rows), the six
   proof bets in terminal states. No accounts/books reference data has been
   reviewed for completeness against a real day.
 - v2 remains fully operational and untouched; it is the fallback.
 - v2 and v3 share one physical resource: the VPS tunnel port (managed
   politely by B5, see D4). v2's supervisor script must be retired at flip.
 - The operator's workers (settlement, reconciliation) are currently OFF
   between sessions and enabled per-launch by environment flags; always-on
   defaults are a cutover-time decision.
 - No bet history migrates. In-flight state at flip time (any live unmatched
   exchange bet placed from v2 or v3) has no designed carry procedure yet.
 - Cutover marks "v3 complete" for the rebuild; the analytical layer is a
   separate later arc.

=== END OF DOSSIER ===
```

---

## 6. What happens after the panel

1. Operator files the four outputs (§0 filenames).
2. Next governance session: triage `b6_panel_synthesis.md` with the operator — accept /
   contest each condition, then convert the verdict into the **B6 scope**: the cutover
   runbook, day-one checklist, coexistence window + fallback triggers, and the v2
   tunnel-supervisor retirement step.
3. B6 executes — panel conditions built, day-one state prepared.
4. **Final forensic money-surface review (operator-locked S230) — the last gate before
   the flip.** One comprehensive adversarial review of the whole money surface as a
   single unit — placement, reconciliation, settlement, free-bet crediting, and the
   launch/config plumbing that arms them — plus any code the panel conditions changed.
   Deliberately sequenced AFTER the panel and after B6's builds land, so it reviews the
   final tree that will actually cut over, not code about to change. Read-only,
   multi-lens (the S223 one-pass-sweep pattern); its findings are the last fix batch.
   Scoped and commissioned as part of B6; runs on the pre-flip HEAD.
5. Forensic review clean (or its findings fixed + re-verified) → W16 cutover.

<!-- B6 GO/NO-GO PANEL PACK drafted S230 — operator to confirm seat assignments +
dossier content before any seat runs; outputs land as b6_panel_*.md -->
