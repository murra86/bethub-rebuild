# Session 201 — recovery-run brief locked + handed to Code; recovery wired, proven, triaged clean (independently verified); cutover-queue advance + manual-entry data-availability finding

**Opened:** 2026-06-29 17:55 ACST (headless runner, fast-path)
**Closed:** 2026-06-29 19:02 ACST
**Tool routing:** Chat — brief lock, Code prompts, recovery triage,
groundings, governance. Code — recovery build/prove (out-of-session,
completed this session).
**Governing DRs:** DR-033 (placings analytical / settlement
Betfair-only), DR-027/028 (two-database boundary), DR-021 (Adelaide
anchors).

## Anchor
- Open: `2026-06-29 17:55 ACST` (runner fast-path; desktop confirmed
  18:13 ACST).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-29 19:02 ACST`.

## Pre-flight / open
Fast-path open: the headless runner's saved result
(`SESSION_201_opening_prompt_result.md`, run 17:55:03, fresh vs S200
close 17:51) was presented straight, no re-verify. Drift-checks had
passed in the runner. First action (auto-draft recovery-run brief,
then hold) was already done — brief held for operator lock.

## Session shape
Single continuous same-workday arc off the S201 hold. Three strands:
(1) operator signed off the held recovery-run brief → locked + Code
prompts produced; (2) Code ran the recovery out-of-session and the
report was triaged clean with independent VPS verification; (3) two
operator groundings — the timer/quota-window question (R-2) and the
manual-entry data-availability question — plus a parked discussion of
a cycle-harness auto-dispatch extension.

## What was delivered
1. **Recovery-run brief LOCKED** (`recovery_run_brief.md`, DRAFT →
   LOCKED). Operator signed off the three calls as drafted: pacing
   moderate-aggressive/capped, low-touch monitoring, ~80/20
   backlog/recent split. End-line + status flipped; no scope edits
   after lock.
2. **Code hand-off produced (Chat):** the build+prove Code prompt
   (read-and-confirm gate on §3 pre-reads + §11 hard limits), a
   read-only daily check-in prompt, and a bare SSH fallback one-liner.
   Memory advice given: run the build in a FRESH Code session (clean
   conversation context) but keep `CLAUDE.md` project memory.
3. **Cycle-harness auto-dispatch idea — discussed, PARKED** (operator
   call). Lock→dispatch→execute→detect→triage→notify loop is feasible
   as a close/open-style extension; needs its own locked brief, a hard
   safety-class gate (no money/settlement/Betfair/v3 auto-exec), and
   triage-with-independent-spot-check. Not built. Priority stays v3
   cutover.
4. **Recovery report TRIAGED CLEAN** (`recovery_run_report.md`) with
   independent live-VPS verification, not report-trust:
   - Deficit recomputed from `capture.db` (mode=ro): full backlog
     **42,103 / 99 dates**, recoverable (≥2026-03-15) **41,340 / 90** —
     exact match to the report.
   - Burndown line + recovery-state JSON live on VPS as reported;
     timer enabled + active (next 23:30 ACST); dirty tree unchanged
     (HEAD `5f71488`, 15 `M` + 8 `??`); S198 fix logic byte-intact.
   - Scope A (raised ceiling 120 + auto-revert at deficit ≤100) and
     Scope B (burndown log + stall/completion/error alerts via reused
     `send_alert`) both verify; 12/12 deterministic checks; budget-skew
     proven by unit (live pass landed 0 — today's quota exhausted, F-2).
5. **R-1 / R-2 surfaced and grounded.** R-1: deficit far larger than
   briefed → realistic clear ~4–6 weeks, not 1–2. R-2: timer fires
   23:30 ACST = 14:00 UTC, ~14h into the UTC quota day. Grounded the
   actual scheduled Racing-API consumers on the VPS — the
   metadata-backfill job is effectively the only meaningful one; NO
   heavy routine daytime consumer. Today's mid-afternoon exhaustion
   was the **manual S198 verification session** (one-off), not steady
   state. Conclusion: **timer move likely unnecessary — watch real
   nights first.** (Corrected an earlier overconfident "the day drains
   the budget" framing.)
6. **Daily-check cadence agreed:** daily for the next 5 days, then
   ~every 2 days. Real window starts **tomorrow night** — tonight
   (29 Jun) is contaminated by today's manual exhaustion, so expect
   ~0. 1-July first clean check flagged to memory (#20, dated, drop
   after 2026-07-01). Operator declined a calendar reminder.
7. **Manual-entry data-availability grounding (operator-requested).**
   Recent-window coverage (≥2026-06-15, thoroughbred non-trial):
   metadata + runners present on every date; `betfair_selection_id`
   ~60–95%; but `finish_position` **largely absent across recent
   dates** (06-21→06-24 all zero; only 06-20/27/28 well-covered).
   Read: manual-entry *lookup* + *win/lose* are supportable now;
   *placings* (place/each-way auto-confirm) are not — and this is a
   gap in the **recent forward capture**, not only the historical
   backlog the recovery is grinding. Per DR-033 placings settle is a
   manual flag anyway, so it doesn't block manual entry; but it
   reshapes the provisioning brief and surfaces a new open item.

## Standing-instruction adherence
- **Tool routing stated throughout** (Cat — explicit): Chat for
  lock/prompts/triage/groundings; Code for execution. ✓
- **DB reads** via `start_process` + sqlite `mode=ro` against the live
  VPS `capture.db`; never copied (WAL discipline). ✓
- **DR-021** Adelaide anchors throughout. ✓
- **Brief-drafting / architectural** — surfaced only operator-relevant
  calls (the 80/20 split, the timer decision, the data finding);
  technical detail handled in-artefact. ✓
- **Memory** used for the dated 1-July reminder (not a standing
  instruction — correctly routed to memory, not `standing_instructions.md`). ✓
- **Build picture:** left untouched — the recovery is capture-side
  analytical (not a W-stream); the W-streams did not move. current_state
  is authoritative for the queue advance.

## Open items in (new this session)
- **Recent-window finish_position capture reliability.** 0-coverage
  across several recent dates (06-21→06-24, results long published)
  suggests the forward placings capture may be failing or
  quota-starved independent of the historical backlog recovery.
  Investigate as part of / alongside the S202 first action. This is
  the operator's manual-entry data concern, generalised.

## Open items out (closed this session)
- **Recovery-run brief** — locked + handed to Code. ✅
- **Recovery run** — wired, proven, triaged clean; now self-running
  via `racing-metadata-backfill.timer`. Henceforth monitoring-only
  (daily ×5 → ~2-day), not active build work. ✅

## Open items (carried — pointer to current_state.md)
Pre-cutover queue (in order): **launcher capture-data provisioning
(S202 first action)** → cash-modal back-stake blank → settlement-worker
→ promo-seed → W16 cutover scoping. Plus: recovery monitoring cadence;
GitHub off-machine backup of bethub-v3 (pending operator login — the
one backup gap); manage live unmatched lays; v2 jump-start-only to
retirement. Parking-lot per current_state unchanged.

## Session close state
- Rebuild root: 33 `.md` files + dirs intact. `recovery_run_brief.md`
  (LOCKED) and `recovery_run_report.md` present.
- `.close_out_backups/`: stale `SESSION_201_opening_prompt.md` swept;
  `SESSION_202_opening_prompt.md` written.
- `v3_build_picture.md`: untouched (no W-stream movement).
- `standing_instructions.md`: untouched (no new standing instruction).
- Project KB: no re-upload needed this close.

## Forward routing (CONFIRMED with operator)
S202 first action — **two-part grounding, then draft the launcher
capture-data provisioning brief:**
1. Ground the current capture-data link state — is the 8400 tunnel /
   capture.db reachability changed since S189? How does the launcher
   set the app's environment (`BETHUB_CAPTURE_DB_PATH` etc.)?
2. Investigate recent-data availability for manual logged bets
   (extend this session's finding — is the recent-window placings
   capture actually landing, or quota-starved/broken forward?).
Then draft `launcher capture-data provisioning` brief, informed by
both — the brief must account for placings being sparse/manual
(DR-033) and fold in carried launcher risks F9 (back-off reset on
restart) / F10 (double-session) / rebuild-if-source-newer.
Operator confirmed close + this first action explicitly.
