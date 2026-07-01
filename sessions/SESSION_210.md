# Session 210 — Cash-modal back-stake blank fix (shipped)

**Opened:** 2026-06-30 15:21 ACST (runner fast-path open; operator engaged live 2026-07-01 ~09:23 ACST)
**Closed:** 2026-07-01 09:55 ACST
**Tool routing:** Chat (diligence, brief authoring, NO-GO triage, close) + Claude Code (out-of-session Phase A review + Phase B execution against the locked brief).
**Governing DRs:** DR-021 (timestamp anchoring, Adelaide local). Bet-safety CLEAN — frontend screen-only; the lay-sizing formula, lay price, persistence, commission, and the liability guard were all named-excluded and left untouched.

---

## Anchor

- **Open:** runner fast-path presented `SESSION_210_opening_prompt_result.md` (ran 2026-06-30 15:21:40 ACST, fresh vs the S209 close 15:14) — the cash-modal overview held for operator confirmation. Operator engaged live 2026-07-01 morning.
- **Close:** `TZ="Australia/Adelaide" date` → **2026-07-01 09:55 ACST**.
- Note: runner-open (06-30) → close (07-01) crosses local midnight, but the live operator session was a single ~30-minute block on 07-01; treated as one workday's work, no split needed (nothing in-flight to defer).

## Pre-flight checks

Rebuild root clean at open and close — expected `.md` set present plus the two new S210 artefacts (`cash_lay_stake_prefill_fix_brief.md`, `…report.md`); no phantom files (`system_snapshot.md` / `context_index.md` / `STATUS.md` / `CLAUDE.md` absent per governance §1); `.close_out_backups/` held only the S210 prompt at open. `bethub-v3` working tree clean on `main` @ `b0f05b0` throughout diligence.

## Session shape

A single-deliverable session: ship the cash-modal (HedgeModal) back-stake blank fix — the next build item after Log Past Bet. It ran the full Chat→Code loop with a diligence-first posture the operator explicitly asked for ("no surprises — be sure the fix is real and won't cause other issues"). Chat grounded the defect in the live code before committing to a fix shape, drafted a two-anchor surgical brief with a review-first gate, handled a correct NO-GO from Code's Phase-A review via an Addendum-A test-scope widening, and verified the committed result independently.

## What was delivered

1. **Root-cause diligence (Chat, live code).** Traced the reported cash-lay under-sizing to two anchors: `routes/Racing.tsx` pipes `manualOdds[selection_id]` (the operator's soft PRICE, a `Record<string,number>`) into the `initialBackStake` stake-named prop; `components/HedgeModal.tsx` plain-cash branch seeds the back-stake box from that prop. Confirmed blank-is-safe (empty box → `Number('')=0` → `laySize` null → `attemptPlace`/`runPlacement` bail + button disabled), and that the two OTHER cash sub-paths are isolated: bonus-winnings cash ($50 `BONUS_WINNINGS_CASH_DEFAULT_STAKE`, a preserved v2 safety default) and free-bet face-value seeding. The lay PRICE is live-polled from Betfair and unaffected.

2. **Locked brief (`cash_lay_stake_prefill_fix_brief.md`).** Surgical two-anchor fix (Sessions 35/36 shape) with a review-first GO/NO-GO gate: B1 Racing.tsx cash branch → `0`; B2 HedgeModal plain-cash `return 0` + initialiser `… : initialMode === 'cash' ? '' : '0.00'`. Hard limits named-and-excluded lay sizing / price / liability guard / FB path / BW-$50. Commit-on-green tagged S210; NO-GO handback on any unnamed impact. Operator signed off (blank-it confirmed; commit-on-green + S210 tag confirmed).

3. **Code Phase-A review → NO-GO (correct).** Code independently CONFIRMED the diagnosis (A1–A3, A5) and no production consumer breaks, but A4 surfaced an unbudgeted impact: five pre-existing plain-cash placement tests in `HedgeModal.test.tsx` seed the box via `initialBackStake` and click Place, so they fail once the box blanks. Repairing five pre-existing tests exceeded the brief's §9 test authorisation, so Code stopped, wrote the finding, left the tree clean/uncommitted, and handed back — exactly the gate's design.

4. **Addendum A — test-scope widening (operator-Claude triage).** Confirmed the fix is correct and the five tests merely encode the OLD buggy pre-fill. Authorised repairing exactly those five by typing the stake each already passed as `initialBackStake` (50/100) before its existing Place click — no assertion loosened, deleted, or reordered — plus the one new cash-blank test. Updated the §7 bar accordingly. Everything else in the locked brief held. Re-issued (Phase A not repeated).

5. **Code Phase-B execution → green, committed `e2638fa`.** Racing.tsx cash→`0` (stale comment corrected); HedgeModal plain-cash `return 0` + cash-only blank initialiser; five tests funded faithfully + one new cash-blank test. `tsc -b` clean; targeted 13→14; full `ui/web` suite 124→125; tree clean on `main` @ `e2638fa` (parent `b0f05b0`). Independently verified in Chat: git state + both production diffs match spec exactly; BW-$50 and FB seeding untouched.

6. **Two findings parked to `current_state.md`.** (a) Pre-existing `Racing.tsx` lint debt (`react-hooks/set-state-in-effect` on the race-switch `setManualOdds({})` effect, ~lines 117–118) — not introduced by the fix. (b) A blank cash box shows only a disabled Place button, no inline "enter a stake" prompt (FB mode has one) — optional cosmetic parity.

## Standing-instruction adherence check

- **DR-021 timestamps** — open + close anchored Adelaide local. ✅
- **Diligence-before-commission** (Flow 3 / operator's explicit ask) — fix grounded in live code before the brief locked; brief carried a review-first gate. ✅
- **Brief discipline** (Cat 4 / brief-drafting skill) — single bounded session, named anchors, hard limits, output spec, what-happens-after, commit-on-green. ✅
- **NO-GO / surprises-become-findings** — honoured on both sides: Code handed back rather than improvising a 5-test rewrite; Chat widened scope explicitly via a recorded addendum, not silently. ✅
- **Bet-safety** — screen-only; liability guard / lay sizing / lay price / settlement all untouched. CLEAN. ✅
- **classify-done-by-live-integration (Cat 4)** — the fix is committed + suite-green; live operator confirmation of the blank-box behaviour is the remaining eyeball, not a blocker.

## Open items — pointer

Full list in `current_state.md`. Cash-modal blank fix CLOSED this session. Next build item = settlement-worker brief (IOU + manual-match-to-lay).

## Open items out (closed this session)

- **Cash-modal back-stake blank fix** — SHIPPED, committed `e2638fa`, suite green. ✅

## Session close state

- `bethub-v3`: clean on `main` @ `e2638fa` (3 files: Racing.tsx, HedgeModal.tsx, HedgeModal.test.tsx; +50/−7).
- `bethub-rebuild`: `cash_lay_stake_prefill_fix_brief.md` (+ Addendum A) and `…report.md` at root; two findings added to `current_state.md` parking-lot.
- `.close_out_backups/`: S211 opening prompt written (see Forward routing).
- Project knowledge base: no re-upload needed (no standing_instructions / governance edit this session).

## Forward routing — CONFIRMED with operator

**S211 first action (AUTO, NO gate):** run the placings-recovery **daily check** — 1 July is the first clean data point after the 29 June quota exhaustion; report the burndown and eyeball whether the per-night `BACKLOG_MAX_ATTEMPTS = 20` cap is the throughput choke (assess whether the 23:30 ACST nightly timer wants a post-quota-reset slot). Then the next build item = **settlement-worker brief** (IOU + manual-match-to-lay) → promo-seed → W16 cutover. Data Foundation harvest parallel, not gating.
