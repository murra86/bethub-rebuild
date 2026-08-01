# SESSION 260 — 30–31 Jul 2026

Opened with the three commissions from S259's close. Standing autonomy: sub-agents for planning and implementation, adversarial review at both ends, return only for decisions.

---

## Session-open checks

- VPS health: all clear (disk 50%, collector running, DB fresh, 502 races captured, backups 13h).
- RACING ALERT: the kensington stamped-coverage spam **stopped** after 29 Jul 06:15, as the S259 fix intended. The only 30 Jul alert was the known Decodo 407 true-positive.
- B6 self-heal live in the sweeps (`twin_merged=47`, 29 Jul evening). The two Wagga mis-stamped markets re-skip at the identity gate every pass, as designed.
- Night-2 twin repair timer verified armed → **fired on schedule 23:45 ACST**; running at ~0.3 markets/s against 6,244 outstanding, so it will deadline-abort again. **Night 3 armed** (`twin-repair-n3.timer`, 31 Jul 14:15 UTC).

---

## Commission 3 — review of every S259 change · CLOSED

Report: `s259_change_review_s260.md`. Three independent read-only reviewers.

**Live data actions: ALL PASS.** Twin merge journal reconciles (2,632 rows; main run exactly the reported 2,530), spot-checks clean, orphans zero, backup intact, Wagga pair correctly unmerged. Sarie cash→FB correction sanctioned end-to-end. Phase 0 migrations as designed.

**v3 money path: CLEAN, zero findings** on the promo-correction commit.

**7 real defects found, all fixed and shipped this session:**
- v3 `fa594c2` (pushed): launcher **startup** carried the same kill-Chrome bug `02442f0` fixed at shutdown; the feed could stomp a half-typed sub-$2 price after 0i made CLEAR release the box; tab-close URL match tightened.
- capture `f50d4b2` (pushed + **deployed**, collector restarted into a verified zero-race gap): **market-adopted rows froze `scheduled_start` and track condition** (stale starts were feeding liveness NEAR windows, the restart gap check and the twin terminal fence); identity sweep bypassed the S259 cross-code refusal; coverage re-probe ran ~48×/day instead of daily; proxy-auth probe alerted on any transient blip. 385→396 tests.

**Open design items:** the gap-aware daily recycle may never find a gap under continuous operation (it gave up at 05:30 today); tonight's repair will hold its slot past both recompute timers, so **tomorrow's `au_suppressed` check must verify the log has real output — absence is not a pass**.

---

## Commission 1 — International Phase 1 · BUILT, NOT DEPLOYED

Brief: `international_phase1_brief.md` (base plan + normative v2 fixes section).

Planning settled **every** open question — zero operator decisions needed. Corrections to the assessment: race-number synthesis not needed (matching is start-time proximity, not `R\d`); no page-size resize; **Decodo delta ≈ 0** (Betfair is unproxied, verified); the flip needs no restart and is one row. Two Phase 0 gaps found: the "countryCode is source 1" wiring read a field that didn't exist, and ordering lock 4 was never implemented.

**Three adversarial reviews: 3× SAFE WITH FIXES, zero UNSAFE.** 14 fixes integrated as normative. Four were blocking, and two reviewers found the first one independently:
- **F1** country must be stamped from the catalogue *request*, fail-closed (Betfair returns tz "GMT" with no countryCode for GB, which re-opened the mis-bind and the date overwrite).
- **F2** the flip widens all event types — GB greyhounds are ~400+ markets/day at AU-shared names, 10× the volume math → per-country event types + a racing-code guard.
- **F3** the identity sweep is a second unguarded writer (a GB market named with `R\d` could adopt a market-less Perth Ascot row).
- **F4** country flaps per-pass → read learned `venue_country` at match time + a daily qualified/unqualified census.

**Built (local only, nothing deployed or flipped):** capture `a9c966e`, `62ed91c`, `03c05c0`, `1b2b45e`, `652014f` — 396→478 tests, with the two mis-bind fixtures **proven red first** against the old matcher (GB Sandown did land on the AU dogs row and flip its racing code; GB Ascot silently vanished beside Perth Ascot). v3 `ddbcc77` — 1949→1962 pytest, 494→499 vitest.

**Implementation adversarial review is the next gate**, then deploy (via the new `deploy_phase1.py`, which refuses while any sweep/repair unit is active), then the verification day, then the one-row GB flip.

Notable implementer deviations to weigh at review: the multi-WIN runner-count tie-break is inert (no field size at match time); the code guard is two rules rather than a blanket ban, to keep AU byte-identical; a small `market_country` audit table was added because nothing recorded which catalogue country a market came from; the AU-invariance corpus is a fixture, not a live export.

**Note for the v3 side:** the sidebar rail is Betfair-direct, so GB markets appear the moment v3 ships — not at the capture flip. `BETHUB_RACING_COUNTRIES=AU` reverts that without a rebuild if a clean rail is wanted until the flip.

---

## Commission 2 — bet-by-bet integrity + P&L · AUDITS DONE

Reports: `bet_integrity_audit_s260.md`, `pl_audit_s260.md`. Both read-only; live DB untouched.

**Integrity: 336 bets, 248 cycles, every one examined. 81% of bets / 74.2% of cycles fully coherent → the 100% bar is NOT met today.**

Passes: insurance journeys 0 broken (59 complete, 135 open-but-coherent, no orphan credits, no double-consumption); **free-bet ledger cross-foots exactly** ($2,853 credited = $2,778 consumed + $75 revoked + $0 available, 8/8 account-books, confirmed against the project's own derivation); corrections integrity 25/25 with no double-supersedes and the rejected-cash filter proven by re-derivation; story shape 0 flags of 336.

**Worst finding — the live lay-pairing door has never fired in production, root cause proven:** the operator places the lay 1–3 seconds *before* logging the free-bet back (31 of 32 cases), and the candidate list only offers pre-existing back bets, so it is empty at lay time. The design assumed back-then-lay. 32 of 61 lays sit alone, each with its hedged free bet on the same market and selection in another cycle; zero lays have paired since 21 Jul. The tool's own 24-hour flag shows only 1 of the 32.

Also: 2 free-bet bets mis-linked by the S253 reassignment (money moved, cycle did not) — a cycle re-point, no money moves. 6 of 248 cycles span more than one date and every date-filtered view splits them.

**P&L: zero arithmetic errors, 7 latent/display defects.** 332 settled bets recomputed from raw fields matched the tool to the cent ($2,225.99 = $2,225.99); commission reconciled exactly across 54 markets and 4 real days, including the 18 Jul mixed-market rebate to the fraction; 12 cycles hand-recomputed with no diffs.

The two-P&Ls divergence is **$0.00 over the last 14 days** — the gap is structurally one term (finalised promo cash) and is zero only because these promos pay bonuses, not cash. Peak ever: $10, for 74 minutes. So the "insurance days look negative" complaint is a *different* problem — an attribution gap, not a missing-credit gap. Recommendation: relabel both figures, don't unify, and build the cycle-complete number as 0t's deliverable.

Highest-value P&L findings: the log-a-past-bet conversion box carries a placeholder that would multiply *realised* free-bet winnings down (zero exposure today, one keystroke from −$157.50 on a single $50 bonus); 4 surfaces omit commission so two real lays differ by ~$3.25 between screens.

**Both audits point at the same repair**, which is 0t's second half and sequenced after international.

---

## Phase 1 implementation review (2nd adversarial gate)

**Verdict: SAFE WITH FIXES.** 478 tests confirmed green independently. The reviewer could not break AU invariance, cross-country binding, or the D8 date rule — the core identity work is sound. Three fixes required before deploy, none needing redesign:

1. **Lock 4 false-alarms on the build's own success case (HIGH).** The flap census fails any base venue appearing under both a qualified and a bare key — but UK Ascot + Perth Ascot is exactly the intended end state, reproduced live by the reviewer. It would have fired nightly from the migration onward, training the operator to ignore the one tripwire that catches a country-stamping escape. The suite missed it because the clean-day test paired `ascot|gb` with `randwick`.
2. **The rekey marker is not enforced before the flip (HIGH — the stop-ship).** The readiness assertion returns early when no foreign country is *enabled*, so the migration marker is never checked pre-flip; but the matcher qualifies keys *unconditionally*. Deploying the code without running the migration would therefore mint a market-less twin per international race per pass — the exact DR-036 class Phase 1 exists to prevent.
3. **The deploy script leaves capture DOWN on failure (MED-HIGH).** Failure paths print instructions and exit with the collector stopped; combined with #2 the liveness self-heal would restart it two cycles later onto new code with old keys.
4. Migration side-table remap is lost on crash-then-rerun (coverage suppression would reset to UNKNOWN permanently), and side tables commit in a separate transaction from the row updates, contrary to §3.3.
5. `--reverse` is partial: skips merged rows, never remaps side tables, never clears the marker.
6. F11's tie-break is fully inert in production and its test is tautological (fixture sets a field production never sets). Not a corruption risk — the code guard and warning hold. Documented as a known limitation rather than fixed; making it real needs a discovery-side change.

**Answers to the three gate questions:** AU behaviour is safe (corpus, bit-identical-day test and an independent trace all hold; the only AU-visible change is the F2 code guard refusing a different-code second market, which is an improvement). The GB flip is safe once fixes 1–3 land and the gates pass. The migration is reversible **for rekeys only** — merges and side tables are not, so rollback means reverting code *and* hand-restoring from the journal pre-images.

Fixes dispatched. Deploy remains blocked until they land and the nightly repair finishes.

---

## ⚠️ LIVE INCIDENT (30 Jul 14:15–14:49 UTC / 31 Jul 23:45–00:19 ACST) — twin repair starved the collector

**A RACING ALERT fired mid-session ("Betfair data, Book frozen, Capture silent"). It was a true positive with a cause nobody had seen before.**

The nightly twin repair holds long write transactions on the capture database. The collector sets **no `busy_timeout` anywhere** (grep: zero hits), so its writes do not wait for the lock — they **fail hard**. From the moment the repair started (14:15:00) the collector began losing writes: **668 lock errors across 488 distinct races** (448 failed race persists + 181 failed bookmaker fetches), and all snapshot capture stopped at 14:16. The liveness self-heal restarted the collector at 14:46, which could not help because the lock was external.

**Why this never appeared on night 1:** the collector was **down** for the entire night-1 repair window — the known 29 Jul outage (collector logged 00:00–12:00, then nothing until 23:00). Last night's repair ran against an idle database. **Tonight was the first time the two ever ran concurrently.** This also exonerates this morning's `f50d4b2` deploy, which was my first suspicion.

**Resolved:** repair stopped at 14:49; the collector recovered immediately (races processing, zero further lock errors). Repair progress is preserved — each merge journals in its own transaction, so the ~206 merges banked tonight stand; ~5,800 of 6,244 markets remain.

**Night 3 has been DISARMED.** Re-arming it unchanged would repeat the damage unattended.

**The real fix (queued, needs review before build):** give the collector a `busy_timeout` so writes wait instead of failing; pace the repair so it cannot monopolise the write lock; and reconsider the overnight-bulk-repair assumption entirely — under continuous operation with international racing there is **no quiet window any more**, which is precisely what the international work institutionalises. A low-priority trickle inside the identity sweep (where B6 self-heal already repairs a 14-day window) may be the better shape than a bulk night job.

**Second, separate finding from the same alert:** the "Betfair data stale" clause is a **known-cause false alarm overnight** — the races running at that hour are all international (Goodwood, Ankara, Vaal, Nottingham, Kocaeli, Galway) and none carry a Betfair market, so no Betfair snapshots can flow. Phase 1 fixes this for GB specifically; the alert should not be silenced before then, because tonight it also carried the true capture-silent signal.

### Incident part 2 — the restart itself drops the in-flight card (corrected diagnosis)

Capture did not resume after the repair was stopped. Chasing that turned up a **second, more important defect, and it partly implicates my own remediation.**

Discovery selects the AU racing day (`orchestrator.py:305`, `local_racing_day(..., "Australia/Sydney")`). When the collector **restarts**, it rebuilds its tracked set from that day only — so any race still running under the **previous** card date is silently abandoned. Tonight the Adelaide date rolled at 14:30 UTC while the UK/IE evening card (Goodwood, Galway, Wolverhampton — all `race_date = 2026-07-30`) was mid-flight. The liveness self-heal restarted the collector at 14:46, and I restarted it again at 15:01; each restart re-anchored it to 31 Jul and dropped 22 in-flight races.

Evidence: every race running at that moment carried `race_date = 2026-07-30`, while the collector logged "Running discovery for 2026-07-31"; zero fetch attempts followed; coverage suppression was not the cause ("coverage-skipped: none" on every pass); the 15:00 UTC hour produced 0 snapshots against 3,217 (28 Jul) and 4,055 (26 Jul) in the same hour.

**Bounded and self-correcting:** 51 races on the 30 Jul card lose capture until roughly 19:00 UTC, after which the later meetings resume automatically because TAB files them under the 31 Jul card (Delaware 19:00, Wolverhampton 19:07, Woodbine 19:10 are all already discovered and tracked). **AU racing is unaffected** — 123 races await on the current card, and the money-critical morning card will capture normally.

**Why this matters far beyond tonight:** the Phase 0 gap-aware daily recycle is scheduled for **04:15–05:30 ACST = 18:45–20:00 UTC — peak UK and US racing**. The capture review already flagged that window as likely to starve (`near_races()` counts every race, so it may never find a gap). Now we know the other side of it: on any day it *does* fire, it would drop the whole in-flight overseas card. Both halves need settling together, and both are squarely inside the international work.

**Lesson recorded:** restarting the collector between the Adelaide midnight rollover and the end of the overseas card is not a safe remedy — it costs the in-flight card. The gap-aware wrapper must also refuse on previous-card-date races in flight, not just on races near their jump.

**Also caught while debugging:** ad-hoc SQL comparing `scheduled_start` against `datetime('now')` is silently wrong — stored stamps carry a `T` separator and `+00:00` offset, so the string compare puts every stored value after `now` and "races near jump" always returns 0. My first gap-check of the night returned a false all-clear because of it. Use `datetime(scheduled_start)` on both sides in any hand query. Worth a sweep of production SQL for the same shape.

---

## Final state of S260 (31 Jul, Friday morning)

### SHIPPED — lay matching (0t-A), v3 `326a181`, pushed
The forward-linker, the widened unpaired-lay flag, the cycle-aware race-screen ⚠,
and the uncapped real-money lines in the money check. **Live at the operator's
next app restart.** 1988 backend / 503 frontend tests, tsc + build green, dist
rebuilt.

The validation that mattered: the reviewer **replayed the new matching rule over
all 336 live bets in time order**, with only the information the tool would have
had at each moment. **61 of 61 lays link correctly, zero wrong, zero ambiguous** —
including reproducing the 29 S246 hand-backfilled pairs exactly. Max real delta
8.2 s against a 30 s window; nothing at all in the 30–180 s band the original
design would have reached into.

Two review catches, both fixed: the money check's 5-line cap was **swallowing the
one real-money signal** (an FB conversion on Cryptonic, settled lost, hedge never
linked) behind 32 backlog lines — the two shapes are now capped separately; and a
link was invisible, so the confirmation now names it ("paired with your Betfair
lay $43.10").

**Also shipped, caught before restart:** the build carries the Phase 1 display
glue, whose rail is Betfair-direct — the first restart would have surfaced GB
meetings with live prices and no capture row behind them. Rail pinned to AU by one
env line in `BetHub.command`; delete it when the capture side deploys.

### STAGED, NOT DEPLOYED — capture resilience, branch `s260-resilience` = `a0cefd4`
Built off `f50d4b2` (what the VPS actually runs), **451 tests green on that base**
— the §6 gate genuinely passed this time rather than being asserted. The
`liveness_check.py` conflict appeared exactly as predicted and was resolved to the
documented recipe; four independent greps confirm **zero Phase 1 leaked**. Pushed
to GitHub and to the VPS **as a ref only** — VPS working tree verified still on
`master`/`f50d4b2`, untouched, collector live.

Deploy window: **04:25–05:45 ACST**, the measured window. Not deployed today —
measured at 09:31 ACST there were 8 races near jump and **all 8 actively
capturing**.

Second review round fixed six things, two of which were gates: a test reached for
a Phase-1-only symbol (so the branch could not be proven green), and §6 still
claimed a clean cherry-pick when the obvious conflict resolution would have
silently imported Phase 1 code onto a non-Phase-1 base. Also: a repair that runs
out of time now reports **INCOMPLETE and exits 75** instead of logging "DONE"; the
deadline moved to 05:38 with `--sleep-between 0.1`, giving ~9 minutes clear of the
05:50 sweep instead of 1–3; and rehydration gained a real double-track guard.
Note the builder found the specified guard key was **vacuous** (a UNIQUE constraint
means those rows can never collide) and implemented the live DR-036 shape instead.

### Still open
- **Both safety timers remain disarmed**; the twin backlog (~5,800 markets) stays
  halted until the resilience deploy.
- **Phase 1** deferred to Sunday: capture `f2fa921` + v3 already shipped behind the
  AU pin. Verification day, then the one-row GB flip.
- **The 34-row lay repair** runs after race day (app quiet, backup first).
- **0v** — split/undo for account-anchored credits, operator-queued, not urgent.
- The five new Sarie/Ladbrokes $30 credits carry **no expiry date**.

### DEPLOY ARMED — `s260-deploy.timer`, 18:55 UTC 31 Jul (04:25 ACST Sat 1 Aug)

Operator took the recommendation to use the window. Script
`scripts/deploy_resilience.sh` on branch `s260-resilience` (tip `cb4e026`),
staged out-of-tree on the VPS at `/root/deploy_resilience.sh`, fired by a
transient timer with `--no-recycle-tonight`.

**The one rule: every exit path leaves the collector RUNNING.** No bare `set -e`;
every failure goes through `fail()` or `rollback()`, both of which bring capture
back up, plus an EXIT trap for anything that escapes. Tested in a sandbox with
real sqlite and the real migration/pacing blobs: **64/64 assertions**, including
migration-prints-SCAN → abort + collector restarted + tree still `master`;
collector-never-starts → checkout rolled back + restarted + timers left unarmed;
and refusals for the window edges, active units, a live repair process,
`hot_races() > 0`, no recent backup, and unverified drift on the branch.

Order (V3-corrected): preflight → stop collector → build indexes (assert
`USING COVERING INDEX`, abort on `SCAN`) → checkout → start + verify
"Orchestrator started" and `db-lock errors: 0` → install units, arm both timers.

Deviations accepted: the pinned-SHA gate now requires `a0cefd4` to be an ancestor
**and** the only differing path to be the deploy script itself (committing the
script necessarily moved the tip); and `--no-recycle-tonight` suppresses the
collector recycle, which would otherwise be eligible to fire within five minutes
of a restart it just performed. The twin repair still fires at 05:05 as designed —
that is the point of the release, and it is protected by the indexes, the lock
guard, the aggregate-rate abort, the WAL abort and INCOMPLETE-with-exit-75.

**Not fail-safe by construction (named, accepted):** if `systemctl start` itself
fails during a rollback, capture stays down — the script logs a CRITICAL line
naming the two recovery commands, but no script can recover a systemd that will
not start a unit.

**Saturday-morning checks:** `logs/deploy_resilience.log` for the SUCCESS banner;
`logs/twin_repair.log` for `DONE` vs `INCOMPLETE` and a rate ≥3 markets/s;
`grep -c "database is locked"` over the collector journal **must be 0**; both
timers showing a concrete NEXT; and that overnight capture actually happened.

---

## POSTSCRIPT (S263, 1 Aug evening) — Saturday checks + 3 adversarial reviews

First written at S263 open, then REVISED the same evening after the
operator directed three independent adversarial reviews. The first draft
of this postscript said "ALL PASSED" — that was too strong. Reviewed
verdict: **the deploy's core objectives all verify; "healthy since" did
not.**

**Core objectives — independently CONFIRMED:**
- `deploy_resilience.log`: **SUCCESS** banner 18:57:49 UTC (04:27 ACST) —
  checkout master → `s260-resilience` @ `cb4e026` (master intact at
  `f50d4b2` as rollback); both FK indexes built, probe-verified
  `USING COVERING INDEX`, no SCAN.
- `twin_repair.log`: **DONE in 695s — 5,316 markets merged (~7.6/s vs the
  ≥3 bar)**; orphan scan all-zero. **The twin backlog is CLEARED** —
  reviewer re-derived the census from the DB: exactly 679 twins remain
  and they are SET-IDENTICAL to the 540 identity-gate + 139
  settled-audit refusals (zero ordinary backlog; the 0m population).
  No new twin minted since 28 Jul. Merges journaled with full donor
  pre-images; 3 spot-checks intact; Wagga pair still correctly refused.
- Lock errors since the deploy: **0** (grep signature positively
  validated against the 668 errors of the 30 Jul incident).
- Rehydration WORKS: exercised live 21× (previous-card races re-tracked
  on every restart, never dropped from tracking).

**What the review found that the first draft missed:**
- **A 20-restart storm, 18:57→20:30 UTC 31 Jul.** The deploy script
  wrote the restart stamp file root-owned (service runs as `racing`) AND
  stamped the UTC date where the check compares Adelaide — so every
  5-min tick of the restart window believed no restart had happened.
  Capture was blank for 93 min post-deploy (overnight dead zone; prior
  Saturday's same hours were ≈0 anyway, so marginal loss small — but
  "no capture hole" is false). **Live stamp file fixed 1 Aug evening
  (chown racing:racing, write-verified)** — tonight's window will
  restart ONCE (= the formal rehydration proof). Deploy-script code fix
  + the oneshot-`activating` guard gap (restarts fired mid-repair;
  repair survived by design) queued for Sunday.
- **One RACING ALERT after the deploy** (not zero): 09:30 UTC 1 Aug,
  playup frozen — playup's last snapshot 08:54 UTC and it then dropped
  out of liveness's candidate set (no NEAR races), so a still-frozen
  book went invisible. Discovery for playup keeps working (9 venues,
  no fetch errors logged). Watch tomorrow's AU card; liveness
  candidate-set blind spot queued.
- **Ubuntu unattended-upgrades SIGKILLed the collector mid-race-day**
  (06:15–06:17 UTC = 15:45 ACST, openssl upgrade; graceful stop hung on
  a proxy-resolve curl). ~2m17s outage while Doomben R8 was INTENSIVE;
  BSP + settlement recovered, final pre-jump ticks 06:16→jump lost.
  OS-upgrade policy (pin restarts to the maintenance window) = operator
  decision, queued.

Filing note: this record was misfiled at the bethub-rebuild root at S260
close; moved to `sessions/` at S263 open.
