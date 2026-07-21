# B6 scope — cutover runbook, gate checklist, and small-builds brief scope

**Drafted:** 2026-07-06, Session 231 (headless runner, first action auto-executed per S230 close).
**Status:** REVIEWED — operator made all held calls in Session 231 (2026-07-06). §4 records
the resolutions: D-2 elective-if-it-occurs; warm-v2 tail ~2 weeks; always-attended confirmed;
worker defaults both-ON. Gate #1 ticks with this review.
**Inputs:** `b6_panel_synthesis.md` (the judge's consolidated verdict — §3 gates, §4 checklist,
§5 blind-spots are this scope's direct source); `b6_panel_pm.md` (Gemini's runbook/checklist
skeleton — merged, with the judge's version winning wherever they differ, per the panel
disposition); `b6_gonogo_panel_pack.md` §6 (the pipeline incl. the operator-locked forensic
money-surface review as the final pre-flip gate).
**Governing DRs:** DR-019 (money derives on read), DR-021 (Adelaide anchors), DR-027/028
(two-database split + boundary).

---

## 0. What this document is, and the pipeline it sits in

The panel ruled unanimous **GO-WITH-CONDITIONS**: the flip is authorised once nine checkable
gates are ticked, and not before. This scope converts that verdict into the three working
artefacts B6 needs:

- **Part 1** — the cutover runbook + rollback plan (panel gate #1, "condition zero").
- **Part 2** — the nine-gate checklist with the judge's tick-off criteria, each gate mapped to
  an owner and its place in the sequence.
- **Part 3** — the scope of ONE Code brief bundling the small builds (r11 worker visibility,
  r2 tripwire test, v3 store backup).

**Pipeline from here** (locked at S230):

1. Operator reviews this scope + makes the two held calls (§4).
2. Code brief drafted from Part 3 → small builds land.
3. Accounts/books reference-data seeding + verification (gate #3).
4. Evidence-gated proving window during normal play — v2 stays system-of-record (gate #9).
5. Forensic money-surface review on the final pre-flip HEAD (pack §6 — the operator-locked
   final gate; the §5 blind-spots routed to it in Part 5 define its scope).
6. W16 flip, executed from Part 1's runbook.

---

## Part 1 — Cutover runbook + rollback plan

### 1.1 Coexistence model (adopted framing)

Per the judge's resolution of D-3: **v3 is already the placement instrument** (the six live
proofs were real v3 placements). The coexistence window's purpose is not "start using v3" —
it is to keep **v2 as the system-of-record and warm rollback target** while evidence accrues,
then transfer record-of-truth at a **quiescent flip**.

**Window duration is evidence-gated, not calendar-gated** (judge's resolution of D-1). The
window stays open until the gate-#9 events are observed:

- ≥1 full clean AU racing day (PM's floor — necessary, not sufficient), AND
- one live interlock-refusal trip (the placement block firing on a real broken stream), AND
- one non-zero settlement beyond the −$4.91 proof.
- A live partial match: **elective-if-it-occurs** (D-2 resolved at S231, §4.1) — a gate only
  if one occurs inside the window; never blocks the flip by its absence.

Each day inside the window ends with the daily money check signed off (§1.5). v2's betting
interfaces stay **closed** during the window to prevent double-entry; its tunnel supervisor
stays running until scripted retirement at flip (r5 log noise tolerated meanwhile). Because
v2 stays closed rather than interactively open, the skeptic's in-tool v2-vs-v3 indicator is
**not included** (judge §4: "include only if v2 stays interactively open" — it doesn't).

### 1.2 Day-one checklist (pre-flip state)

Merged from PM CL-01–06 + the judge's consolidated §4 list. Every line must be true before
the flip minute:

| # | Item | Gate/source | Verify by |
|---|---|---|---|
| DAY-01 | Promo catalogue: 9 rows seeded (done) + operator EV eyeball sign-off | cond. 10 | Sign-off recorded |
| DAY-02 | 10–15 active bookmaker accounts/books registered in v3's store, reviewed complete against one real day's workflow | gate #3 | Operator confirms a real bet can be recorded/tagged against every account in current rotation |
| DAY-03 | Worker always-on defaults decided, recorded, launcher enforces | gate #5 | Decision recorded; launch behaviour matches it |
| DAY-04 | Launcher echoes worker enablement visibly; banner raises on absent expected worker (r11 fixed) | gate #2 | Launch prints SETTLEMENT_WORKER / RECONCILIATION_WORKER state; deliberately-disabled worker produces a visible alert |
| DAY-05 | B5 tunnel healthy; watchdog reports healthy | PM CL-04 | Launcher health gate |
| DAY-06 | Betfair stream subscribed; placement interlock reads SUBSCRIBED | PM CL-05 | In-tool status |
| DAY-07 | Durable log + placement-audit journal active from the first minute — no second "log-birth blind spot" | gate #7 | Log rows exist from launch minute |
| DAY-08 | Daily money check runnable, procedure runbooked (§1.5) | gate #7 | Dry run completes |
| DAY-09 | Clean-state baseline: manual queue empty; the six terminal proof bets confirmed not to pollute the operator's working view | judge §4 (cheap 30-second look) | Visual check of the working view |
| DAY-10 | v3 operational-store backup in place, restore tested once (blind-spot #1) | Part 3.C | Backup file exists; documented restore has succeeded once |
| DAY-11 | Mac local-environment readiness: durable-log directory permissions, port availability, dependencies outside the dev context (blind-spot #2) | judge §5.2 | One pre-flight pass, results noted |
| DAY-12 | r2 tripwire test exists and is green (function still caller-less) | gate #8 | Suite green with the tripwire in it |

### 1.3 The flip — runbook

Executed only when the gate checklist (Part 2) is fully ticked and the forensic money-surface
review has passed. PM's minute-by-minute skeleton, corrected in one place: PM had the r11
launcher fix applied *on flip day* (his step 4) — superseded; r11 lands via the Code brief
**before the proving window** (it is gate #2, ticked before flip day ever arrives).

**F-0. Pre-flight (flip day, before racing / T minus 1 hour).**
Run the daily money check to record the baseline. Confirm the manual review queue is empty.
Confirm the bethub-v3 working tree is clean and matches the approved pushed commit (the same
HEAD the forensic review ran on — if HEAD moved after the review, the review is stale; stop).
Take a fresh v3-store backup (DAY-10 mechanism).

**F-1. Quiesce (minute 0) — the quiescent-flip precondition (gate #4).**
**No open unmatched exchange bets at flip.** Confirm on Betfair's own interface that v3 has
zero in-flight orders. Confirm all bets v2 recorded for the current day are fully settled and
reconciled in v2. Close every v2 browser tab / UI. If any in-flight bet exists: wait for it to
resolve, or apply the orphan-bet procedure (§1.4 step R-2) before proceeding. The flip only
happens from a confirmed-empty in-flight state.

**F-2. Retire v2's tunnel supervisor (minute 5) — scripted, not manual (gate #6).**
Run the retirement step (script/launchctl unload — exact mechanism lands in the Code brief or
runbook finalisation). Verify the supervisor process is gone and v3's B5 watchdog owns the
tunnel port healthily. This also silences r5's auth-log spam permanently.

**F-3. Launch v3 (minute 10).**
Start via the launcher. Watch the terminal echo: SETTLEMENT_WORKER and RECONCILIATION_WORKER
states print per the r11 fix and match the gate-#5 policy. Fault banner silent. Durable log
and placement-audit journal confirmed writing from this minute (DAY-07).

**F-4. Smoke test (minute 15).**
Promo-page picker loads the 9 rows; a race lookup pulls through the tunnel without tripping
the watchdog; the placement interlock reads SUBSCRIBED. No bets placed as part of the smoke
test.

**F-5. Declare record-of-truth transferred (minute 20).**
From this minute v3 is the system-of-record. v2 is retired from operation but kept warm as
the rollback target per the held tail decision (§4.2). The first daily money check of the v3
era runs at end of that day's racing and is signed off.

### 1.4 Rollback plan

**Triggers** (judge §4, merged and deduplicated — any ONE fires an immediate rollback):

1. Any money discrepancy or silent-loss/data mismatch in the daily money check.
2. An unresolvable park that v2 would have handled.
3. Worker stall > 15 minutes during live racing (skeptic's 15–30 and PM's 15 reconciled to 15).
4. Tunnel deadlock > 5 minutes (B5 watchdog fails to self-heal, starving race lookups).
5. Worker-failure masking — the r11 condition recurring in any form (a worker silently off).
6. Operator discomfort. No justification needed.

**Mechanics** (judge §4, incorporating PM's orphan procedure):

- **R-1.** Stop v3: kill the launcher app and all child processes (workers included). This
  frees the tunnel port.
- **R-2. Orphan-bet procedure.** Before opening v2, log into Betfair's native web/app
  interface directly. Manually cancel ALL unmatched pending orders v3 placed (v2 cannot see
  them — v3's store never migrates). For any partially or fully matched v3 bets, write down
  the exact matched stakes and prices from the exchange interface for manual ledger entry.
- **R-3.** Relaunch v2. Its tunnel supervisor reclaims the port and re-establishes lookups.
  v2 drives all NEW bets from this point.
- **R-4.** Manage v3-legacy positions manually from Betfair statements at end of day, via the
  manual queue / hand records — v2 is never asked to represent bets it didn't place.

**Orphan symmetry** (validation seat, judge-endorsed): rollback has the same in-flight-bet
problem as the forward flip — where possible, take the rollback from quiescence too (no open
unmatched v3 orders). When the trigger is urgent and quiescence isn't available, R-2 is what
makes a single orphaned bet survivable; the park-to-manual valve is the backstop.

**Warm-v2 tail:** v2 stays installed-and-runnable for **~2 weeks** after a clean flip
(resolved at S231, §4.2), with no hard deletion until the window's evidence gate is
retrospectively clean.

### 1.5 Daily money check — runbook step (gate #7, closes r10)

Written procedure, run at the end of each racing day — every day of the proving window, and
every day post-flip:

1. `uv run python -m ops.settlement_review` (read-only).
2. Reconcile the day's outcomes against Betfair's own statement/balance movement.
3. Confirm the manual queue is empty or every queued item is understood and in hand.
4. Record the running cross-day tally in a durable place (this is the r10 fix — the tally is
   a written artefact, not session memory).
5. Sign the day off. During the proving window, a signed-off day is what counts toward gate #9.

### 1.6 Backup posture (blind-spot #1 — "run first")

The money store is one SQLite file on the Mac with no stated backup; with no history
migration, a lost/corrupt file post-flip = total operational-state loss. The fix is build
item **C** in the Code brief (Part 3): automated timestamped backups + one tested restore.
Flip-day and proving-window backups then run automatically; DAY-10 verifies.

---

## Part 2 — The nine-gate checklist

Tick-off criteria are the judge's, verbatim (synthesis §3). A gate is ticked only when its
criterion is observably true — no ticking on intention.

| Gate | Substance | Tick when (judge, verbatim) | Owner | Sequence |
|---|---|---|---|---|
| 1 | **B6 authored and reviewed** — written cutover runbook AND rollback procedure exist and reviewed | "the B6 document exists in the repo and covers pre-flight, flip, and rollback steps" | This scope (Part 1) + operator review | NOW — condition zero; ticks when the operator reviews this document |
| 2 | **r11 fixed** — launcher echoes worker state; banner raises on absent expected worker | "a launch visibly prints SETTLEMENT_WORKER / RECONCILIATION_WORKER state, and a deliberately-disabled worker produces a visible alert" | Code brief (Part 3.A) | Before the proving window |
| 3 | **Accounts/books reference data verified** | "operator confirms a real bet can be recorded/tagged against every account in current rotation" | **MET 2026-07-07 (S232 seeding session)** — 4 accounts / 9 books / 13 pairings seeded + day-0 balances ($12,791.73) verified on the live read path (13/13 in the picker, balances exact); operator confirmed balances correct in-app. Evidence: `b6_seeding_pack.md` §6a/§5a. Rider: window day 1 re-confirms in live use per §5.2 | Done (rider rides on proving-window day 1) |
| 4 | **Quiescent-flip precondition written and met** + orphan-bet procedure documented | "the checklist line exists and the flip is executed from a confirmed-empty in-flight state" | Runbook §1.3 F-1 + §1.4 R-2 (written = this doc); met = flip day | Written NOW; met at flip |
| 5 | **Worker always-on defaults decided and recorded**, launcher enforces | "a decision record states the post-cutover worker-start policy and the launcher enforces it" | **DECIDED at S231 (§4.3): both workers ON by default at every launch, opt-out flag for dev only**; enforcement rides in the Code brief with r11 | Decision recorded; enforcement with Part 3.A |
| 6 | **v2 tunnel-supervisor retirement scripted into the cutover** | "the runbook step decommissions v2's supervisor and confirms v3 owns the port healthily" | Runbook §1.3 F-2; scripting with the Code brief or runbook finalisation | Scripted before flip day; executed at flip |
| 7 | **Durable log + daily money check live from first minute, procedure runbooked** | "no second 'log-birth blind spot' exists on cutover day, and the daily-check cadence is a written runbook step" | Built (S229); runbooked at §1.5; live-from-minute-one verified at F-3 | Runbooked NOW; verified at flip |
| 8 | **r2 fenced** — test fails if the unwired placement function gains a caller | "that test exists and is green (i.e., still caller-less)" | Code brief (Part 3.B) | Before the proving window |
| 9 | **Evidence-gated coexistence window completed** — ≥1 full clean AU racing day AND one live interlock-refusal trip AND one non-zero settlement beyond the −$4.91 | "all three observed and each day's money check signed off" (partial match per D-2 — operator-elective) | Proving window, during normal play; operator signs days off | After gates 2/3/5/8 land; before the forensic review |
| 10 | **EV-figure eyeball** (data-quality condition, not a software gate) | "sign-off recorded" | **SIGNED OFF S231** — upgraded from an eyeball to a full validation arc: derivation paper + empirical calibration (163k runners) + adversarial review + external reviews; operator accepted fit-for-purpose with two standing rules (haircut $6–$10 screen EVs ~3 pts; never execute on a ~/⚠-flagged EV as firm). Evidence: `ev_validation_findings.md` | Done |

**Sequencing summary:** gates 1, 4(written), 6(scripted), 7(runbooked) tick with this scope +
its review → gates 2, 5(enforced), 8 + the backup build land via ONE Code brief → gate 3 via
the seeding session → gate 9 via the proving window → forensic money-surface review on the
resulting HEAD → flip executes gates 4(met) and 6(executed).

**Status update (S231, post-build):** the Code brief executed same-session
(`b6_small_builds_brief.md` → `b6_small_builds_report.md`, HEAD `4f98ad5` pushed, suites
1390/132 green). **Gates #2, #5(enforced), #8 are MET; blind-spot #1 (DAY-10) is CLOSED**
(automatic launch+daily backups, retention 30, restore tested for real and documented at
`ops/RESTORE.md`). **Gate #10 SIGNED OFF later in S231** after the EV validation arc
(commission + derivation paper + empirical calibration + adversarial review — see
`ev_validation_findings.md`). Remaining before the flip: **gate #3 (operator seeding) and
gate #9 (proving window)**, then the forensic money-surface review on the pre-flip HEAD.

**Status update (S232):** **Gate #3 MET** — seeding session run 2026-07-07 (see
`b6_seeding_pack.md` §6a/§5a): 4 accounts / 9 books / 13 pairings registered by the operator
through the live Accounts screen; day-0 opening balances written as `day_0_opening` cash
events and verified exact on the live read path; operator confirmed in-app. §5.2's one-real-
day confirmation rides on proving-window day 1. Remaining before the flip: **gate #9 only**,
then the forensic money-surface review on the pre-flip HEAD (now `18177e0`).

---

## Part 3 — Code brief scope: the small-builds bundle (one brief, one bounded session)

One brief, bethub-v3 read-write, bounded single session, suite stays green, no Betfair
contact required, no live-store writes. Brief drafting is the next Chat/governance step after
this scope is reviewed (S231 or S232 per context budget); this Part fixes its scope either way.

**A. r11 — worker visibility (gate #2).**
The launcher echoes each worker's enabled/disabled state at startup, AND the fault banner (or
the launcher itself) raises if an expected worker is not running. Acceptance: a launch
visibly prints SETTLEMENT_WORKER / RECONCILIATION_WORKER state; a deliberately-disabled
expected worker produces a visible alert. **Rider (gate #5):** once the worker-defaults
decision is recorded at scope review, the launcher enforces it — same code territory, same
brief.

**B. r2 — tripwire test (gate #8).**
A test/guard that fails if the unwired stake-invariant-less placement function ever gains a
caller. Acceptance: the test exists and is green while the function remains caller-less; any
future caller turns the suite red. Zero-cost fence on a latent overpay vector.

**C. v3 operational-store backup (blind-spot #1).**
Automated timestamped backup of the v3 operational store — at minimum on every launch plus
daily — to a location that survives loss of the primary file, with a documented restore
procedure **tested once for real**. Acceptance: backups appear automatically; a restore has
been performed successfully and its steps written down. (Design detail — retention count,
destination, SQLite-safe copy method — is the brief's to fix; the acceptance is not.)

Out of scope for this brief: anything touching placement, settlement, reconciliation, or
money logic; the forensic review's blind-spot items (Part 5); accounts/books seeding (that is
operator + data work, not a code build).

---

## Part 4 — Operator decisions (RESOLVED at Session 231 review, 2026-07-06)

Carried per the S230 close as HELD; the operator made all calls at S231 scope review. Each
subsection now records the resolution above the original framing (kept for the record).

### 4.1 D-2 — must a live partial match be observed before the flip?

**RESOLVED — Option B (elective-if-it-occurs).** Operator: a live partial match could take a
long while to eventuate and is not worth holding up cutover. If one occurs inside the window
it becomes a gate (must route cleanly to park/manual); otherwise flip with the
partial-then-lapse guard code-verified-only, failure direction "park safely".

The one condition the panel could not mechanically settle. A partial match may never occur
naturally at $3–$9 stakes within any bounded window; hard-gating on it risks blocking the
flip indefinitely on an event that can't be forced.
- **Option A (validation/skeptic):** hard gate — no flip until a live partial match is
  observed and handled cleanly.
- **Option B (judge's recommendation):** elective-if-it-occurs — if a partial match happens
  inside the window it becomes a gate (must route cleanly to park/manual); if the window
  completes without one, flip anyway with the partial-then-lapse guard code-verified-only, on
  the explicit record that its Betfair size-cancelled assumption is unconfirmed by
  observation and its failure direction is "park safely".

### 4.2 Warm-v2 rollback tail — how long does v2 stay runnable after a clean flip?

**RESOLVED — two weeks.** Operator: v2 works well enough that keeping it runnable is cheap
insurance. v2 stays installed and runnable for ~2 weeks after a clean flip (comfortably above
the judge's one-settlement-cycle floor); no hard deletion until the window's evidence gate is
retrospectively clean.

- **Judge floor (binding minimum):** ≥1 full settlement cycle, no hard deletion until the
  window's evidence gate is retrospectively clean.
- **Validation seat's preference:** 1–2 weeks.
- The call is where between "one settlement cycle" and "a couple of weeks" the tail ends —
  cost is near-zero (v2 just sits installed), so the trade is purely comfort vs tidiness.

### 4.3 One cheap confirm while the operator is here (blind-spot #3)

**RESOLVED — confirmed per recommendation.** v3 runs attended-only; the parked phone alarm
stays parked. If v3 ever starts running unattended, the monitoring scope reopens.

**Also recorded here (gate #5): worker defaults per recommendation — both workers ON by
default at every launch, explicit opt-out flag for dev only.** The Code brief (Part 3.A rider)
makes the launcher enforce it. This paragraph is the gate-#5 decision record.

**Always-attended usage:** confirm that v3 only ever runs while the operator is present and
watching. One question; it validates the entire parked monitoring-scope decision (the parked
phone alarm — "a dead app can't self-report unattended"). If the answer is ever "it runs
unattended", the monitoring scope reopens.

---

## Part 5 — Blind-spot routing map (synthesis §5 → where each lands)

| # | Blind-spot (judge's ranking) | Routed to |
|---|---|---|
| 1 | v3 store backup/restore posture — "run first" | Code brief item C (Part 3) + DAY-10 |
| 2 | Mac local-environment readiness | Day-one checklist DAY-11 (pre-flight pass) |
| 3 | Always-attended-usage confirmation | Operator confirm at scope review (§4.3) |
| 4 | Secrets/credential handling posture | Forensic money-surface review scope (document the posture; launch/config plumbing is already in the review's named surface) |
| 5 | Worker crash-recovery / settlement idempotency mid-cycle | Forensic review scope — test before declaring the window clean |
| 6 | Double-place / concurrency protection | Forensic review scope |
| 7 | Betfair adversarial API failure modes (esp. wrong-signal mis-settle) | Forensic review scope |
| 8 | Exchange exposure/balance-limit handling | Forensic review scope |
| — | Lower priority: UI day-walkthrough; derive-on-read P&L reconstructability; settlement-gate clock/timezone robustness | Forensic review scope candidates (include-list decided when that review is commissioned) |
| — | Scale to 10–15 accounts / performance | Deferred — gates growth, not the flip (judge §5) |

The forensic money-surface review (pack §6) is commissioned after the panel-gated builds land
and the proving window closes; items 4–8 above plus the lower-priority candidates form its
scope input alongside the review's own named surface (placement, reconciliation, settlement,
free-bet crediting, launch/config plumbing) on the final pre-flip HEAD.

---

**Next step (updated at S231 review):** all operator calls are made — D-2 elective (§4.1),
warm-v2 tail ~2 weeks (§4.2), always-attended confirmed + worker defaults both-ON (§4.3).
Gates 1, 4(written), 5(decided), 6(scripted), 7(runbooked) are ticked. Next: draft the Code
brief from Part 3 → small builds land → seeding (gate #3) → proving window (gate #9) →
forensic money-surface review → flip.
