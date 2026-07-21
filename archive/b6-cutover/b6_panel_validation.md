# B6 panel — VALIDATION seat output

**Seat:** Validation (technical) — fresh Claude Opus, no project context, per `b6_gonogo_panel_pack.md` §2/§4.2.
**Run:** 2026-07-06 (Session 230), in-house isolated instance; input = seat prompt + evidence dossier only.
**Filed verbatim below.**

---

# PANEL RECORD — VALIDATION SEAT ASSESSMENT
## BetHub v3 cutover readiness (compiled from Evidence Dossier 2026-07-06)

## VERDICT: GO-WITH-CONDITIONS

The money path is architecturally sound and its failure direction is genuinely biased toward safety in the ways I can verify from the dossier. But "live-proven" here means *exercised once, at minimal stakes, over two days, on a single market shape.* That is enough to retire the blockers as **built and directionally correct**; it is not enough to call the system *proven across the range of conditions a live fortnight produces.* The gap between those two is exactly what the conditions below are meant to close. None of the conditions require re-architecture — they are gating events, day-one state, and a rollback discipline. B6 (the thing this panel shapes) is unstarted, and B6 is where a cutover is actually won or lost.

I would not flip today. I would flip after the conditions in Q2/Q3/Q4 are met.

---

## Q1 — Is the money path proven enough to cut over?

**Not yet — but the shortfall is sample and observation coverage, not design.**

What the proof trail genuinely establishes, and I credit it:

- **The core loop closed correctly once, end to end, on real money.** PROOF 1 is the load-bearing evidence: an unmatched lay recorded pending at stake 0, reconciled to a true matched stake, held through the race by the settlement gate, then settled at the correct magnitude *and correct sign* (−$4.91 on a lay whose runner won). The derive-on-read rule (DR-019) means settlement stamped state and the money fell out of recorded stake×price — that is the right shape for a payments-adjacent system, and it worked.
- **The safety valve fired for real.** PROOF 2 — a never-matched lay that the system *refused to resolve by assumption* and parked to manual — is the single most reassuring event in the dossier, because it is the failure direction working under uncertainty, observed, not asserted.
- **The team found a real defect by measuring the exchange rather than trusting its own model** (PROOF 3: Betfair files never-matched orders under LAPSED, not SETTLED). Fixing that, re-proving it live, and gating auto-fail on *full*-stake lapse (partials park) is good engineering hygiene.

Why "once" is not "enough":

1. **n=6, all one shape.** Every live bet was a single-leg lay, AU harness/thoroughbred WIN market, $3–$9 stake, across two calendar days (D5.f — the team says this itself). The exchange's messy states — partial matches, partial-then-lapse, multi-runner/place markets, dead-heats, voids/abandonments, late scratchings, price suspensions mid-race — are **not established** as having occurred live. The resolver's partial-then-lapse guard is verified *in code against per-docs assumptions the team admits are unconfirmed by observation* (D5.e). The failure direction if that assumption is wrong is "park safely," which I accept — but I want it *observed*, not reasoned.
2. **Exactly one non-zero settlement.** Five of six proofs were $0 no-bets. The money *magnitude* path — the part that can actually overpay — has been walked once. One correct −$4.91 is a green light to proceed, not a proof of the payout arithmetic across win/lose/void/partial permutations.
3. **The interlock refusal path is unit-tested only** (D5.c) — the thing that blocks placement when the stream is down has never actually blocked a placement live. It's money-safe by direction, but it is a claimed guarantee that has not been exercised against a real stream drop.

**Observable events that would move me from GO-WITH-CONDITIONS toward unconditional GO:**
- A live **partial match** reconciled to its true partial stake and settled at correct magnitude.
- A live **partial-then-lapse** shape parking (or resolving) as the guard intends — confirming the Betfair size-cancelled semantics the team currently only assumes.
- A live **multi-runner or non-WIN market** settled correctly, if any such market is in the operator's real rotation.
- The **interlock refusal actually tripping** on a real stream drop and blocking a place.
- One **full unattended-of-the-worker settlement cycle** with the settlement worker confirmed ON at launch (see r11).

None of these require staged/fake money — they will occur naturally in the operator's normal play. The condition is: **run v3 in shadow/parallel for a defined window until these shapes are observed, before v3 becomes the sole tool.** See Q4.

---

## Q2 — Which residuals gate the flip, which are correctly parked?

**Correctly parked (I concur — ship over these):**
- **r1** (stale matched-stake column, verified nothing on the money path reads it), **r3** (redundant read calls — cost not correctness, bounded by the park valve), **r4** ("$0 at $0" / "Won"/$0 cosmetic display — money-correct under derive-on-read), **r5/r6/r7** (tunnel-supervisor noise, boot-start gap, ~30s half-open window — ops annoyances that self-heal or dissolve at cutover), **r8** (web access lines absent from diary), **r9** (audit journal never rotates — "years to matter"). These are genuinely non-money-path or genuinely cosmetic. Parking them is the right call.

**Gate the flip (I would not ship as-is):**

- **r11 — worker-enablement is an invisible launch condition. This is the one I would hard-block on.** A supervised launch was run with the *settlement worker accidentally OFF*, dropped by a double-click that lost the env flag, and it was caught only by manual process inspection. The team classifies this cosmetic. It is not. In a system whose entire safety story is "workers hold and settle correctly," a silently-disabled settlement worker means bets that should settle simply *don't* — they sit unsettled with no active fault, and the money check (D4.3) reports on decisions that were never made. The failure is silent and it is on the money path's supervision layer. **Condition: the launcher must echo enabled workers at startup and, preferably, the fault banner must raise if an expected worker is not running.** Cheap to fix; disproportionate downside if not.

- **r2 — unwired placement function with no stake-invariant.** Unreachable today because it has no caller. I accept it as non-blocking *only with a written condition*: it must stay uncalled, and the day it acquires a caller it must gain the proposed-vs-recorded-stake invariant *before* that caller ships. This is a latent overpay vector sitting in the codebase with the safety rail removed. Park is acceptable; **leaving it undocumented as a landmine is not.** Add a guard/assert or a test that fails if it ever gains a caller.

- **r10 — cross-day money-check tally is "session discipline, not code."** Not a flip-blocker on its own, but it interacts badly with the fresh-start operating model. If the daily money check depends on the operator running it with the right cadence and it silently misses decisions made before the log's birth (D4.3, the 15:48 blind spot), then the primary money-oversight tool has human-discipline gaps on both ends. **Condition: document the operator's daily-check procedure as an explicit day-one runbook step**, not an assumed habit.

**Not in the register but I treat as residual:** the **B4 EV-figure accuracy** is "eyeball pending, non-gating." Agreed non-gating for *software* readiness — but note it is unverified data in the live store on day one.

---

## Q3 — What must exist in v3 on day one (fresh start, no history migration)?

The fresh-start decision is clean and I like it — no migration means no migration bugs. But "no history" is not "no state." Day one must contain:

1. **Accounts/books reference data, reviewed against a real day.** D7 says this has "not been reviewed for completeness against a real day." With ~10–15 live bookmaker accounts, if the reference data is incomplete the operator cannot record a real bet on day one. **This is a day-one blocker and it is not yet done.** Must be reviewed and confirmed complete before flip.
2. **A defined in-flight-state procedure at the moment of flip.** D7 admits "in-flight state at flip time … has no designed carry procedure yet." Any live unmatched exchange lay open at the instant of cutover — placed from v2 or v3 — has no home. **Condition: flip only from a quiescent state** — i.e., choose a cutover moment with no open unmatched exchange bets, and write that precondition into the cutover checklist. This is the single most likely place to lose or double-count real money during the transition.
3. **Explicit worker-default decision, made and recorded.** D7: workers are OFF between sessions, enabled per-launch by env flags; "always-on defaults are a cutover-time decision." This must be *decided and made visible* (ties to r11). Undecided defaults + invisible enablement = the r11 failure at scale.
4. **The seeded promo catalogue (9 rows) and the six terminal proof bets** are already in the store. The proof bets being present is fine (terminal, money-correct), but confirm they don't pollute the operator's day-one working view (r4's cosmetic confusion could make a settled no-bet read as "Won").
5. **The retirement of v2's tunnel supervisor scripted into the cutover**, not left as a manual "remember to." D4/D7 are explicit that it must be retired *at* flip, and r5 shows it actively misbehaves while both run.
6. **The durable log and money check running from the first minute** — so there is no second "15:48 blind spot" on the day that actually matters.

---

## Q4 — Coexistence + rollback window

The architecture is well-suited to a clean parallel window: v2 is "fully operational and untouched … the fallback" (D7), and v3 stores no shared mutable money state with v2. The only shared physical resource is the VPS tunnel port, and B5 already manages that politely (health-gated, never kills a tunnel it didn't start). This is a good position to roll back from.

Recommended shape:

- **Phase 0 — shadow/parallel (duration = evidence-gated, not calendar-gated).** v2 remains the source of truth for the operator's day. v3 runs alongside and places the real hedge legs (it already does — the six proofs came from real v3 placements), but v2 is the fallback of record. The window stays open until the Q1 observable events have occurred: at least one live partial match, one non-zero settlement beyond the −$4.91, the interlock refusal tripping, and a full session with the settlement worker confirmed ON. I would want **more than two calendar days and more than six bets** before declaring the shape space covered — a realistic minimum is a couple of weeks of real play or ~20–30 real legs including at least one partial and one messy-close, whichever comes first.
- **Phase 1 — flip.** Executed only from a **quiescent state** (no open unmatched exchange bets, Q3.2). At the flip: retire v2's supervisor script, set the decided worker defaults, confirm reference data complete. v2 stays installed and runnable.
- **Rollback window — keep v2 warm for at least one full settlement cycle beyond the flip, ideally 1–2 weeks.** Because no history migrates, rollback is "stop using v3, resume v2" — cheap — *but* any v3-placed bet in flight at rollback has the same orphan problem as forward cutover. So rollback must also be taken from quiescence where possible, and the operator needs a documented manual procedure for reconciling a single orphaned exchange bet by hand (the manual review queue is the natural home for it). The park-to-manual safety valve is what makes rollback survivable; lean on it.
- **Coexistence caveat already flagged:** v2's supervisor redialing every ~5s (r5) is harmless noise but confirms the two tools should not both own the tunnel for long. Keep Phase 0 as short as the evidence allows.

---

## Q5 — What I'd check that the dossier doesn't mention

Base assessment only on the dossier; where silent, "not established." The following are **not established** and I would want answers before or during Phase 0:

1. **Idempotency and crash-recovery of the workers mid-cycle.** The dossier proves the workers produce correct results across passes, but says nothing about what happens if the app *crashes between* recording a matched stake and stamping settlement, or mid-reconciliation. Does a restart double-book, re-place, or double-settle? The placement-audit journal is "crash-safe" (D4) — good — but crash-safety of the *settlement state machine* is not established.
2. **Betfair API failure modes beyond LAPSED/empty.** What does the resolver do on HTTP 5xx, auth-token expiry, rate-limiting, or a *malformed/partial* cleared-orders response (not "no signal" but "wrong signal")? PROOF 2 covers "no conclusive signal → park." Adversarial/garbage responses are not established.
3. **Concurrency / double-place protection.** If the operator double-clicks place (they already double-clicked the launcher, per r11), or the stream reconnects mid-place, is there an idempotency key preventing two real lays? Not established.
4. **Clock/timezone and race-close timing.** Settlement gate "held it while the race ran" — what drives that gate's timing, and is it robust to the missing settled-time field (PROOF 1 notes Betfair's close quirk) across markets, not just the one observed?
5. **Backup/restore of the v3 SQLite store.** It's on the operator's Mac. What is the backup posture of the *operational* money store (as distinct from the GitHub *code* remote)? A lost/corrupted SQLite file on day one with no history migration and no stated backup = total operational-state loss. Not established.
6. **Secrets/credential handling** for Betfair and the bookmaker accounts — not mentioned; a payments-adjacent system should have a stated posture.
7. **The unattended blind spot the team named honestly** (D4.2: "a dead app cannot self-report while unattended"). Accepted as parked for attended use — but I'd confirm the operator's real usage is genuinely always-attended today, because the entire monitoring scope decision rests on that assumption.

---

## SAFETY-POSTURE ASSESSMENT (the panel's core charge)

**The stated failure direction — "hold/park and ask the operator, never fabricate money" — is supported by the evidence for the failure modes actually exercised, and is credible-but-unproven for the rest.**

Supported under failure, observed:
- PROOF 2 parked a never-matched bet under real uncertainty rather than guessing. This is the direction holding *under failure*, live, on real money — the strongest single fact in the dossier.
- PROOF 3's fix only auto-fails on *full*-stake lapse; any partial shape parks. Conservative in the right direction.
- The derive-on-read rule structurally prevents settlement from *writing* a money magnitude — the class of "fabricated stake" bug is designed out, not just tested out.
- The interlock refuses to place without a live stream (direction: refuses = money-safe).

Credible but **not proven under failure**:
- The interlock refusal has never actually tripped live (D5.c) — the safe direction is unit-tested, not observed.
- The fault banner's fault states **have never been triggered by a real fault** (D5.a). The system's ability to *tell the operator* something is wrong is, today, mock-proven only. A safety posture that depends on escalation-to-human has an unproven escalation channel.
- r11 is the counterexample that worries me most: a silent worker-off condition is a failure that does *not* announce itself and was caught only by luck (manual inspection). That is the one place the "always ask the operator" promise demonstrably did *not* hold — the operator was never asked; the worker was simply absent.

**Net:** the money-*movement* direction (never overpay, never fabricate, bias to under-record) is well-founded and partly proven. The money-*supervision* direction (always surface faults/parks to the human) rests on channels (banner, worker-enablement visibility, daily check discipline) that are mock-proven or discipline-dependent. The former is what protects against catastrophic loss and it is in good shape. The latter is what protects against *silent* loss, and it is the softer half. My conditions target that softer half.

---

## CONDITIONS SUMMARY (what GO is contingent on)

**Hard gates before flip:**
1. **r11** — worker enablement made visible at launch; fault banner (or launcher) raises if an expected worker is not running.
2. **Q3.1** — accounts/books reference data reviewed and confirmed complete against a real day.
3. **Q3.2 / Q4** — flip executed only from a quiescent state (no open unmatched exchange bets); documented in-flight/orphan-bet manual procedure exists.
4. **Phase 0 parallel window held open until the Q1 observable events are seen** — at minimum one live partial match, one non-zero settlement beyond −$4.91, and one interlock refusal tripping live.

**Documented conditions (not code-blocking, but written into the cutover):**
5. r2 kept caller-less with a guard/test that fails if it gains a caller.
6. Worker always-on defaults decided and recorded (D7).
7. v2 supervisor retirement and v2-warm rollback window (≥1 full settlement cycle) scripted into cutover.
8. Daily money-check procedure written as a runbook step, not assumed habit (r10, D4.3 blind spot).

The build is honest with itself — the D5 ledger and D6 register are unusually candid, and that candor is itself a positive readiness signal. The engineering is directionally right and the safety bias is real. What's missing is not soundness but *coverage*, plus a genuinely-unstarted B6. Close the four hard gates and hold the parallel window until the exchange shows you its messy states, and this is a defensible flip.

**VALIDATION SEAT: GO-WITH-CONDITIONS.**
