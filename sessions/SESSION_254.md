# Session 254 — Sun 26 Jul 2026 (deploy window) — CLOSED Sun eve

**Close-out:** wrong-account error class SOLVED end-to-end (detection
sweeps + BetLog reassign button + guided correction tool; 4 commits
`b230eab`/`cf2c691`/`31d6c66`/`0169dd4`; migration run on live; acceptance
= real incident replayed to the cent; executive summary
`reassign_build_executive_summary.md`). Also this session: S253 audit
findings all resolved ($208 dismissed as non-triggered, Sarie stake
corrected, Kate/Leigh closed as already-corrected double-draw, FB expiry
dropped by operator); worklist 0k (morning odds sweep) added.
**DISPLACED from this window, carried to S255: worklist 0j (other-code
bet row + credit door, commissioned S251) and the 6 queued panel fixes —
the reassign build took the window.** Panel itself still uncommitted
awaiting operator review. S255 open: standing checks, then the
prioritization below (§5).

## 1. Standing checks (session open)
- `ops.vps_health`: **all clear** — disk 38%, collector running, capture db
  fresh (0.0h), 2 backups (newest 8h), overnight sweep ran (attempted 80,
  walled 25). 8400 tunnel not answering — normal, app closed operator-side.
- RACING ALERTs: two new self-cleared batches since S253 closed —
  **Canberra 24 Jul** (8 alerts, 01:30–06:00 UTC) and **Murtoa 25 Jul**
  (1 alert), both the known no-Betfair-identity category (Murtoa is a picnic
  track with no Betfair market). Nothing since 25 Jul 00:45 UTC. No capture
  fix needed.
- First action honoured: `SESSION_253.md` read in full before anything else.

## 2. Position at open
- Leigh/Tim wrong-account fix: EXECUTED + verified on live 26 Jul 11:09
  (S253 §6). Closed. Reassign-account door remains a planned build.
- Race EV + variance panel: built, adversarially reviewed, green
  (`npm run build` clean, 412/412) but **uncommitted on disk**. Effectively
  live already (dist served from disk, S253 §4i) — operator hard-refresh
  applies.

## 3. Queue for this window (from S253 §5 / §4j / §4l)
1. Operator live-review of the panel + confirm 2 flagged choices
   (small-field-3rd clause divergence; pending-bets-only read) → commit.
2. Six queued fixes: `bonus_pct` NaN guard; over-cap variance read;
   scratched-runner reason text; FB `mbr=null`→8% default; verdict dedup;
   live-browser acceptance pass.
3. Day-1 feedback items (8, S253 §4l).
4. Reassign-account door (endpoint + BetLog UI + `bet_reassigned` audit;
   needs CHECK-rebuild migration; this morning's script is the tested core).
5. Operator-owned: enter real `position_min_field` terms on the 12 templates.

## 5. Close: open queue + proposed prioritization (for S255 open)
1. **Monday (deploy window closes):** operator panel review + 2 display
   choices → commit panel → 6 queued panel fixes → 0j build.
2. **Before Sat 1 Aug:** morning odds sweep (0k) on the VPS — every
   Saturday missed is study data lost.
3. **Saturday:** race-day live proofs (watchdog funds-gap, Take-SP
   stage 0, big live-proof list); first live reassign together if one
   arises.
4. **Next quiet sitting:** Saturday-feedback batch (BetLog date filter +
   period P&L, star runners with bets, odds-populate button, unmatched
   visibility); settled-bet stake-edit button.
5. **Operator quick actions, anytime:** enter `position_min_field`
   insurance terms (biggest EV error on screen); BetRight ≥8-runner
   template term; confirm Punting Form subscription actually cancelled.
6. **Later/parked:** TAB lag investigation, FB CALL confidence (needs
   definition), promo-flag highlight (blocked on log-promo), AccountCare
   sequence, `current_state.md` refresh, remainder of parked list.

## 4. Work log

### 4a. S253 auto-action 1 — independent review of the Leigh/Tim fix: CLEAN
Fresh post-hoc verification, independent of the exec-day verifier: raw-SQL
structural checks written from scratch + the app's own derivations, run on a
WAL-consistent copy of the live store (script
`scratchpad/review_leightim_s254.py`). **42/43 checks pass** — every intended
edit is in place and correct: qualifier on Leigh; credit on Leigh, consumed
by the new deploy grouping The Creator; So Rebellious deploy re-sourced to
Tim's real spare credit, bet + $300 untouched on Tim; Tim 2732.20 / Leigh
1957.80 by the app's own derivation; FB in-hand 0/0; no orphans; audit
present; integrity/FK clean; all 141 promo payloads parse.

### 4b. The 1 failing check = a NEW, PRE-EXISTING wrong-account instance
Store-wide S243 sweep (deploy account == deploying bet's account — exec-day
checks only asserted the two touched deploys) found **Kate/Leigh, 18 Jul**:
$50 free bet @ 9.5 settled_lost on **Leigh@TAB** (`bet-3b84ec36…`) funded by
a **Kate@CrownBet** credit (deploy `031bbd8e`, credit `5fb003c4`). Present
byte-identical in the pre-fix backup ⇒ NOT caused by the 26 Jul fix;
predates the S243 write-time guard by ~a day. No cash misstatement (FB loss
returns nothing either way) — inventory/turnover attribution only.
**Operator truth needed:** who really placed it?

### 4b2. Worklist addition (operator-directed, mid-session)
**0k — morning odds sweep** added to `worklist.md` from
`morning_odds_sweep_brief.md` (planned in an informal session 26 Jul;
capture-side, Saturdays-only v1, executor-ready brief). Unblocks the
early-placement study + the S252 morning-market edge. Note: to catch next
Saturday (1 Aug) it must be built on the VPS before then.

### 4c. S253 auto-action 2 — permanent-fix plan WRITTEN (v1 — superseded by 4e)
`bet_reassignment_door_plan.md` — Tier 1 clean-chain reassign door
(endpoint + BetLog UI + faithful `bet_reassigned` audit; prerequisite
CHECK-rebuild migration ⇒ deploy-window); Tier 2 (consumed-credit
re-source, the Leigh/Tim shape) stays script-based, door refuses it loudly.
Plus: add the two store-wide sweeps that caught Kate/Leigh to the daily
money check. 3 operator decisions listed at the end of the plan.

### 4d. COMPREHENSIVE 20-AGENT REVIEW (operator-commissioned) — results
Workflow `wf_b6b2cf3e-6ba` (6 data auditors × 175 checks + adversarial
verify of every significant finding + 2 fix reviewers + 2 plan reviewers;
1.35M tokens, all agents completed; raw results in the workflow journal).

**THE 26 JUL FIX IS 100% SOUND — definitively closed.**
- Byte-diff reviewer: complete row-level diff of ALL 12 tables, pre-fix
  backup vs live — EXACTLY the five intended operations, nothing else;
  inserted rows field-perfect vs design §4.
- Gap-hunt reviewer: 79 read-surface keys computed pre/post — 10 diffs,
  every one intended; all HTTP surfaces render the touched rows correctly;
  the late-timestamped deploy breaks nothing (all consumers are orderless);
  bet_legs/cash_flow/reconciliation all clean. Verdict: no further
  verification needed. (One pre-existing store-wide latency: journey state
  never sees triggered credits — promo table has 0 rows so the template
  lookup always misses; display-only, predates the fix.)

**DATA AUDIT — store is fundamentally sound (cash to the cent, all chains
coherent, all 141 events re-hydrate); 5 confirmed findings, 5 refuted by
adversarial verify, 16 minor. Confirmed:**
1. [MED, REAL MONEY] **6 uncredited insurance qualifiers, 21–22 Jul, up to
   $208 owed** (5× Tim@UpYaGo $158; 1× Tim@BetRight $50) — no credit, no
   dismissal, 4–5 days stale while everything around them was processed.
   Tim@UpYaGo's promo layer has NEVER been processed (0 promo events vs 7
   settled safety-net bets). DB can't tell "book owes us" from "runners
   missed the places" — OPERATOR TRUTH NEEDED per bet.
2. [MED] **4 no-op `bet_edited` audit events** (empty diff, no notes; 18–25
   Jul) — what changed is unrecoverable; the S236 edit door allows account
   moves that produce exactly this signature. One suspicious: `3ba73fab`
   edits Tim@TAB's Tengun Tommy bet 2 min after an identical Leigh@TAB bet
   on the same runner. Operator may remember.
3. [MED] **FB expiry structurally untracked** — `fb_expiry_days` NULL on
   all 12 templates ⇒ all 60 credits carry NULL expiry ⇒ the read-time
   expiry filter is inert store-wide. Strengthens the standing operator
   action (set TAB=7d etc.).
4. [LOW] **Sarie@TAB $3 FB face unaccounted** — deploy `54d557bc` drew the
   full $13 credit onto a $10 bet; stake typo vs forfeit vs $3 residual
   still at TAB — operator check.
5. [MED, dup of 2 from second finder] — same no-op-audit issue.
   Minor items of note: float-contaminated amount string in cent-truing
   cash event `8f83ac26`; Tim@Betfair sub-cent residue (displays fine);
   fat-finger census: 2 same-market/same-stake cross-account pairs.

**KATE/LEIGH REFRAMED:** it was ALREADY 80% corrected on 19 Jul via the
restore door (`774a6af1` "S243: cross-account draw" → re-deploy on Kate).
The naive S243 sweep re-flags the superseded wrong deploy — sweeps must
ignore superseded deploys. Remaining: Leigh's FB bet `3b84ec36` is an
unfunded orphan. Operator truth still needed; small composition either way.

### 4d2. Operator decisions (mid-session)
- **FB expiry: DROPPED.** Operator manages expiries manually; the input is
  complication without value. Worklist item 2 updated; expiry machinery
  stays deliberately inert. Do not re-raise.
- $208 qualifiers, Kate/Leigh bet, Sarie $3: operator gathering account
  context — detail tables provided (see chat).

### 4f. AUDIT FINDINGS RESOLVED (operator truth received; writes executed)
1. **$208 credit-gaps → DISMISSED (all non-triggered).** Operator: all 5
   Tim@UpYaGo (21 Jul) + Tim@BetRight Enchanted Miss (22 Jul) finished
   outside the insured positions — no free bets due. Recorded 6 dismissals
   via the app's own writer (`record_credit_gap_dismissal`, endpoint
   pattern), app down, backup
   `bethub-PRE-s254-dismissals-20260726-143303.db` (444). Verified:
   live gaps list 41 → 35, exactly the six. Script
   `scratchpad/dismiss_s254.py`; event ids in output.
2. **Leigh/Kate SOLVED — NO FIX NEEDED (my "orphan" claim was wrong).**
   Full timeline of both pairings 18–19 Jul shows: at 12:50:54 the Leigh
   Tempt The Gods FB bet got TWO simultaneous deploys — Leigh's own credit
   `6e98446e` via deploy `6202dcc6` (CORRECT, still live) AND Kate's
   `5fb003c4` via `031bbd8e` (spurious cross-account DOUBLE-DRAW; Kate's
   own same-runner bet followed at 12:53 funded by her other credit). The
   19 Jul S243 correction restored Kate's credit and re-deployed it on her
   real 8246cc19. Verified now: nothing supersedes `6202dcc6`, zero
   orphans store-wide. Current data CORRECT; the only artifact is that a
   naive S243 sweep re-flags the superseded deploy (plan v2's sweeps are
   superseded-aware). No operator decision needed after all.
3. **Sarie $13/$10 → ROW CORRECTED.** Context found: S247
   `fb_face_single_source_fix_brief.md` — modal rounded the $13 face to a
   $10 prefill; real TAB ticket was $13; code fixed S247 (`64ff337`) but
   the brief chose "rows stand as logged". Operator S254: should have been
   addressed. Executed: stake 10.00→13.00 both fields, faithful
   `bet_edited` audit (before/after snapshots + full story in notes,
   event `e0e0ffcc`), UPDATE+audit committed atomically, backup
   `bethub-PRE-s254-sarie13-20260726-143650.db` (444). Verified: row
   13.00; audit parses; Sarie@TAB cash unchanged 1168.00 (FB stake,
   settled_lost — zero cash impact). App edit door couldn't do it
   (stake edits fenced to PENDING) — scripted with app models.

### 4g. FB expiry decision + v2 review commissioned
Operator: proceed with the v2 plan process. Adversarial design review
workflow `wf_98e2cb0f-397` launched (4 agents: composition mechanics,
migration/domain/endpoint plumbing, failure modes + verification
sufficiency, and END-TO-END SIMULATION of both real incidents using the
actual writers on private copies).

### 4h. v2 REVIEW LANDED — 3× UNSOUND + 1× SOUND_WITH_ISSUES → PLAN v3
The round caught build-stoppers; v3 written (same file, review record §8):
- **Re-credit step unbuildable**: fb_credit's LOCKED once-per-qualifier
  guard counts revoked credits as credited → composition needs a NEW
  chain-terminal-aware correction-credit writer (operator decision — it
  amends a locked contract).
- **Serviceability PROVEN by execution**: the composed sequence on a copy
  of the real pre-fix Leigh/Tim state reproduced the known-correct end
  state TO THE CENT (with guard bypass) — architecture direction right.
- **v2's Kate/Leigh prescription would have double-funded** a $50 bet with
  $100 face, silently through every guard (executed in sim) → mandatory
  pre-flight: refuse live-drawn-face > stake.
- **LIVE DEFECT found in the current app**: S236 `PATCH /v1/bets/{id}`
  move door refuses Betfair as SOURCE but not TARGET — a soft-book bet can
  be moved into the exchange lane today (Tim@BetFair active). Patch queued
  as pre-door fix §4a, this deploy window.
- Also: S236 door bypasses all planned safeguards (fold into one path);
  spendable-phantom crash window → composition journal table + adjacent
  atomic restore+revoke; `list_source_pending_spends` counts superseded
  deploys as funding (pre-existing blindness — fix before door); sweeps
  extended to (a)–(e) with chain-terminal-aware (c); CAS from-triplet;
  audit row raw-inserted in-txn via adapter serializer; same-book-only v1
  (cross-book stamps poison S253 calibration); reassign-preview GET;
  `_FK_REQUIRED_BY_EVENT_TYPE` landmine.
- Build order FLIPPED: pre-door fixes → composed-correction module (the
  real fixer; both real incidents were promo-spine shapes) → endpoint+
  migration (future clean shape).
**4 operator decisions in plan §7. Next gate: focused re-review of v3
deltas before build.**

### 4i. Decisions resolved + FINAL REVIEW PASSED → plan v3.1 BUILD-READY
Operator resolved all decisions (no locked-rule exceptions → sibling
correction verb; same-book-only v1; settled bets movable; freebie out of
scope). Operator workflow priority recorded: self-serve in-tool fixes
(memory `feedback_selfserve_intool_fixes`). Operator's settlement-order
thought reviewed: complementary, not a substitute (prevents tangles, not
the entry-time mistake). Final focused review `wf_8ddc30b9-2b8` (3 agents):
ALL SOUND_WITH_ISSUES — spec pins only, no redesigns. Headline pins: the
correction credit must be a NEW ROOT event (fb_restore-literal shape
vanishes face cross-account), correlation stamped to the qualifier, guard
under BEGIN IMMEDIATE checking ALL the qualifier's chains; §3.0 concrete
step sequence added; journal DDL + in-step updates + pre-generated event
ids; void exemptions for the superseded-aware readers (bet-a5f3cfb2);
PAYLOAD_BY_EVENT_TYPE registration + read-back test; closure/CAS on the
txn connection; foreign_keys-before-BEGIN; settlement-state CAS.
Realistic estimate 3–5 sittings (not 1–2); A ships first, own deploy.
**All pins applied → `bet_reassignment_door_plan.md` v3.1, BUILD-READY.
Reviewer confidence ~85–90% rigorous permanent fix with pins applied.**

### 4j. SITTING A BUILT + COMMITTED (`b230eab`) — red-before, 1747 green
1. **Betfair-target hole PATCHED** (`ui/api/routers/bets.py`): PATCH move
   arm now refuses a Betfair TARGET (422) — red test first, confirmed the
   hole, then fix; 30/30 endpoint tests green.
2. **`list_source_pending_spends` fixed** (`burst_review.py`): superseded
   deploys no longer count as funding; voided FB bets exempt (a5f3cfb2
   shape). New test file, 5 tests, red-before. On the live store the
   fixed reader still reads clean (every real FB bet funded or voided).
3. **LEDGER COHERENCE SWEEPS in the daily money check**
   (`ops.settlement_review`, new section after CYCLE PAIRING WATCH):
   five superseded-aware sweeps (deploy-vs-bet account / chain coherence /
   live-credit-vs-qualifier / book-lane match / unfunded FB). Goldens
   pre-computed on the audit copy BEFORE implementation: (a) naive=1
   (the corrected Kate deploy — proving superseded-awareness matters)
   aware=0; (b) 0; (c) 0 of 59; (d) 0/290; (e) 0. Seeded-violation +
   corrected-state tests for each, 6 tests. **Live store: 0 flags.**
Full suite 1747 passed (was ~1734). Backend-only — live on next app
start, no dist rebuild, no migration. Panel work remains uncommitted,
untouched, awaiting operator review.
NEXT: sitting B (correction verb + journal + composition module), then
C (bet_reassigned migration + reassign endpoint + BetLog door).

### 4k. SITTING B round 1 (workflow `wf_01a2a5ec-e70`) — verifier FAILED it
Built (3 agents, disjoint new files, red-before): `fb_correction.py`
(§3a verb, 15 tests, all 4 pins, golden-chain real-data dry-run clean);
`composition_journal.py` (17 tests, non-committing helpers proven by
rollback); `ops/correct_promo_chain.py` (16 tests). 54 new tests green,
no existing file touched, fb_credit/restore/deployment byte-untouched.
**Independent verifier: FAIL — the acceptance replay (real Leigh/Tim
incident on the pre-fix backup) was REFUSED at plan time**: the builder
scoped v1 to funded-bet-already-on-target, excluding consumed-deploy
re-sourcing (the So Rebellious spare-credit sub-shape) that plan §1.6/§3.0
requires. Zero writes on refusal (fail-safe held). Also: guard-lock,
in-step §3b re-run, and in-step S243 assert exist in code but NO test pins
them (mutation probes stayed green); plan-time TOCTOU on the
second-composition check; settlement re-check outside the verb's txn;
sweep (f) not yet wired. Fix round `wf_5b07b293-994` launched: re-sourcing
branch (operator names the spare credit — no auto-discovery), the missing
pin tests, TOCTOU + settlement-guard closures, sweep (f), nits. Re-verify
gates on the replay matching the executed fix's money surfaces to the
cent. Operator-notified (non-blocking): correction credit copies
face_value_expiry verbatim (v1; moot for consumed shapes).

### 4l. SITTING B COMMITTED (`cf2c691`) — fix round PASSED re-verify
Fix round `wf_5b07b293-994`: all 7 findings fixed. Re-sourcing shape
lands in ONE atomic txn (restore + spare-re-fund + revoke-of-corrective —
chosen because the split form leaves a settled bet unfunded at a commit
point); operator names the spare (`--spare-credit`), grouping target
auto-discovered iff EXACTLY one orphan on the target (else refuse); the
3 previously-unpinned safety checks now mutation-pinned; plan-TOCTOU +
settlement-in-verb-txn closed; sweep (f) live. **Independent re-verify:
PASS — the real Leigh/Tim incident replayed on the pre-fix backup,
straight AND crash-resumed, matches the executed fix's money surfaces to
the cent (Tim 2732.20 / Leigh 1957.80 / FB 0-0 / orphans none / sweeps
silent / global cash conserved), PURELY APPEND-ONLY (5 events appended,
zero pre-existing promo rows changed — vs the one-off's 2 in-place
UPDATEs).** Full suite 1813 green; my gate re-ran it + spot-checked txn
discipline; committed (8 files, +5781).
Non-blocking v1 policies for operator awareness: 2+ orphans on target →
refuse (name-the-bet flag possible later); grouping deploy correlation =
funded bet's cycle (executed-fix convention); under-faced spares allowed
without warning (operator-knowledge territory).

### 4m. SITTING C BUILT + COMMITTED (`31d6c66`) + MIGRATION RUN ON LIVE
Workflow `wf_66ef3e01-12c` (migration+domain → endpoint ∥ BetLog UI →
verify): all pins verified implemented; 4 mutation probes each killed the
right test; migration rehearsed on scratch then RUN ON LIVE 17:32 (backup
`bethub-PRE-s254-reassign-migration-20260726-173221.db` 444; 16 audit
rows preserved, CHECK admits bet_reassigned, integrity/FK ok).
Verify verdict PASS_WITH_ISSUES → I fixed the one real defect inline
(red-before, 3 new tests): **the closure walk over-blocked
corrected-away funding whose credit lived on elsewhere** (the real
Kate-chain shape) — deploy refs now bind only while LIVE; credit refs
bind until their chain dies. Real-data verdicts now exact: `3b84ec36`
refused naming ONLY its live funding `6202dcc6` (correct — composed
tool's territory; the plan's original "ALLOWED" pin predated the
double-draw discovery and is corrected in the plan); qualifier
`bcd524f8` refused naming `60b175eb`. Also: preview busy_timeout, TS
nullable widenings. PATCH account-move arm fully stripped (grep-verified
single path). Endpoint 30 tests; BetLog 39/39; backend suite **1850**;
`npm run build` clean; panel work byte-untouched (git-verified).
**Deployed: backend live at next app start; dist already rebuilt;
migration done. The wrong-account build (plan v3.1 A+B+C) is COMPLETE.**
Non-blocking notes: UI renders a fixed 409 line (server detail not
echoed); pnl_delta orientation trusts server from/to names (correct per
contract); vitest mock-hygiene sweep of BetLog.test.tsx → worklist.

### 4n. FINAL WHOLE-SYSTEM REVIEW (operator-commissioned) + polish `0169dd4`
Workflow `wf_d9d51b50-6d9`, 4 reviewers on the finished state:
- **Acceptance: CONFIRMED_SOUND** — all proofs re-run at HEAD with exact
  numbers: CLI replay + crash-resume to the cent; a REAL button
  move-and-reverse on a live-store copy (bet-2b90b99e, $40 P&L shifted
  and restored byte-identically, audit rows read back); real-bet
  refusals zero-write (sha256-verified).
- **Money safety: SOUND_WITH_NOTES — no wrong-money path** across commit
  points, decimal discipline, race interleavings, error paths. Noted
  transients are the design-accepted, journal-visible ones.
- **Coherence: DEFECT_FOUND (operability, fail-closed)** — circular
  refusal handoff (endpoint↔CLI) for the spend-bet shape; the plan-§5
  daily-check schema assertion dropped between sittings; expired-terminal
  divergence (deliberate v1 scoping, but message dead-ended).
- **Completeness: SOUND_WITH_NOTES** — spare-credit ids undiscoverable
  (HIGH); sweep (f) truncated id unusable for resume; tool absent from
  operator docs; plan doc lacked a BUILT stamp; CLI polish.
**All fixed same-day (`0169dd4`):** refusals now list candidate credit
ids (smoke-proven on the real incident data: it prints exactly
`5e32f0d7…`); new `credits` + `list` subcommands; paste-ready full-id
resume line; sweep (g) pre-migration-store detector (+2 tests, 10/10);
routing messages fixed both directions incl. qualifier auto-naming;
busy_timeout + friendly errors + help texts; honest panel copy;
`operator_workflow_map.md` §7 written; plan stamped BUILT & SHIPPED.
Gates: backend 1852, build clean, BetLog 39/39.
**Deliverable: `reassign_build_executive_summary.md`.**
Accepted-as-noted (documented, no action): funded-bet settlement flip
window in the correction-credit step (caught by the next step's in-txn
check before money lands); endpoint doesn't consult the journal (both
outcomes loud); post-commit response re-read can 404 after a landed move
(retry 409s with the truth); `current_state.md` 6 sessions stale
(pre-existing → worklist).

### 4e. DOOR PLAN REWRITTEN v2 — reassign-by-COMPOSITION
Plan review verdicts: attack SOUND_WITH_ISSUES (4 significant defects);
alternatives reviewer REFUTED v1's core premise — append-only re-anchoring
is NOT blocked (chains extend through the DEPLOY; `fb_restore` is the
shipped verb; the 19 Jul Kate correction is production proof), and v1's
Tier-1 door would have refused BOTH real incidents. v2 (same file):
bets-row UPDATE + `bet_reassigned` migration (now incl. domain enum +
payload union + EXPLICIT migration run — the precedent is lazy) + promo
corrections composed from existing validating writers, ordered so every
prefix is money-coherent; target-relative closure eligibility; delta
asserts; 3 superseded-aware standing sweeps; extended test list.
Kate/Leigh fix decoupled from the migration.
