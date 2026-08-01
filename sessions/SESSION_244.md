# Session 244 — Sun 19 Jul 2026 (eve) → Mon 20 Jul (morning close)

**Title:** Weekend feedback closed to zero — winnings-credit triage, EV
cap fix, ledger hops corrected, and the whole B1 "honest money reads"
build designed → grounded → built → LIVE in one session.
**Opened:** 2026-07-19 17:58 ACST (cold manual open; the headless
runner's result landed simultaneously — reviewed, agreed with the live
re-checks on every material point). **Closed:** 2026-07-20 09:10 ACST
(overnight pause; operator resumed for the morning bounce + close).
**Tool routing:** single Claude Code session throughout; one 6-agent
grounding workflow; one background build agent (own context window).
**Governing DRs invoked:** DR-027/DR-028 (two-database split + boundary
— capture-side placings read by reference through the 8400 tunnel,
no caching), DR-021 (Adelaide anchors), DR-019 (derive-on-read — all
board corrections were spine events, never balance edits).

## Anchor

Open `TZ=Australia/Adelaide date` → 2026-07-19 17:58 ACST.
Close same command → 2026-07-20 09:10 ACST.

## Pre-flight / open checks

VPS health all clear (disk 36%, capture fresh, sweep ran). W5 mailbox:
no new alerts since the handled 17-Jul one; 6am heartbeat healthy;
off-box backup 9h old. Alert-watch cron re-armed (2-hourly; dies with
the session). App found running pre-restart code — restart pending
noted, not touched. Drift-check: `SESSION_243.md` lacked a "Closed:"
stamp (corrected this close — stamp note added, no content rewrite);
`v3_build_picture.md` one close behind (caught up this close). Vocus
lane 3003: operator confirmed router fine — pending item CLEARED.

## Session shape

Operator-driven triage → build → live-proof arc, in five movements:
(1) the weekend feedback summary the runner's open was meant to lead
with; (2) deep triage of item 7/#10 (the missing bonus-winnings
credits) which root-caused a promo-terms error, an EV mis-wiring, and
a door/detector blind spot; (3) the 23-row credit-gaps sweep against
real race placings; (4) ledger-hop corrections ($400 Tim funding
written; $300 Sarie funding reversed after the operator corrected the
real-world story); (5) B1 commissioned ("plan up build 1, use
sub-agents"), grounded by a 6-agent workflow, built end-to-end by a
background agent, triaged, and live-proven across two app bounces.
Day rolled past midnight mid-session (operator pause, morning resume).

## What was delivered

1. **Sarie $13 + Leigh $33 winnings credits written** through the spine
   machinery with audit notes (events `3db8aba1`/`af0add59`), Leigh's
   spend paired to Lets Go Brother (`1d7fd7e2`, same cycle). Board =
   real world exactly: Sarie–TAB $13 the only unspent FB anywhere.
   Real TAB variant established from the actual credits: **25% of
   winnings, rounded up to the dollar, cap $100** (operator-confirmed
   terms).
2. **Catalogue corrected in place**: template `0f6456d4` renamed "TAB
   Bonus Winnings 25% to $100 (FB)", return 0.25, cap $100, correction
   note recorded. Live in the picker immediately (per-request read).
   Historical promo_ev_at_log stamps left as logged (honest record).
3. **EV cap mis-wiring found and fixed** (`99eb6f3` + test literal
   `53a8585`): the catalogue cap was routed to max-STAKE for winnings
   promos, so the EV engine priced the bonus uncapped and the stake
   box prefilled the cap. Config gained `bonus_cap`; both EV call
   sites pass it; TopBar cap dial edits the right knob per kind;
   insurance untouched. 6 new tests.
4. **Sunday-evening bounce (operator-run, dist rebuilt app-down)**
   activated: 60s match-status sweep, deployment-corrections +
   credit-revocations doors, the EV fix. All live-verified (doors
   answer 422-validation; new bundle served). Lesson: wrong-method
   GET probes return 404 on this app — probe with POST.
5. **Credit-gaps swept 23 → 0.** Every entry classified against real
   finish positions (capture.db over SSH, one query): all 23 ran 4th
   or worse — zero money owed. Dismissed through the door (23 × 201).
   Root insight recorded: the detector is placings-blind but the
   capture side isn't → became B1 item 8.
6. **Ledger hops corrected, both through doors.** Tim's $400 BetRight
   deposit: funding hop written (`6bbf0738`) — float view +$400, P&L
   unchanged (never wrong). Then the operator corrected Sarie's story:
   her $300 CrownBet deposit came from PointsBet/StarSports
   withdrawals (now logged, $1,559.80), NOT bank money → the 18-Jul
   $300 funding event REVERSED via the reverse door (`6dae51bc`).
   Proof: Sarie's holder pool derives to exactly $1,259.80
   (1,559.80 − 300). **Standing operator rule captured: any deposit
   to a Tim account-at-book is bank money, always.**
7. **B1 "honest money reads" brief** written to
   `honest_money_reads_build_brief.md` after a 6-agent read-only
   grounding workflow re-anchored every claim at HEAD `53a8585` (the
   review report was 5 commits stale; three findings materially
   changed the plan — indexed correlation path for the fuse; zero
   omitted-limit consumers remain so no fetch-all API; the per-bet
   race-result endpoint already existed for item 8).
8. **B1 BUILT by a background agent** (fresh context, brief-driven):
   7 commits `eae7c11`→`2e9abd3` pushed; backend 1481→**1511** green,
   frontend 215→**220** green, tsc clean; red-before/green-after on
   items 1/5/6/7/8.1; report
   `honest_money_reads_build_report.md` (inventory-first). Triage:
   D1 gate change verified safe against the live catalogue; dist
   byte-untouched (S232 held); Q3 stuck-sweep-slot backlog checked by
   this session = **0 rows** (nothing to drain).
9. **Monday-morning bounce + full live-proof.** Dist rebuilt app-down,
   operator relaunched. Verified live: credit-gaps **[]** (neither
   banked bonus bet re-lists — the fuse fix's dedupe holding on real
   data); credit-in on Leigh's real WON bonus bet → **"already
   credited — $33"** through the NEW kind-aware gate (old gate would
   have 422'd the shape); race-result reports Davida
   `selection_position: 8` (the outside-top-4 case); movements
   envelope `{items, total: 25}`; new bundle `index-DjNgUcf9.js`
   serving. **B1 = live-proven on the money paths, live-serving on the
   screens; only race-day UI moments remain to observe.**
10. **W5 ticks clean ×2** during the session (no new alerts).

## Operator decisions this session

- Whole-dollar ROUND_HALF_UP on winnings-shape credits (matches TAB's
  observed $13/$33) — ratified; other books' rounding is a terms
  observation to make per book.
- Tim-deposit rule (above) → B2 will encode as the deposit-door
  default ("fresh bank money" for Tim, "from float" for others) with a
  non-blocking negative-float tripwire + daily-check line.
- TAB free bets expire in ONE WEEK (operator fact) → **use Sarie's
  $13 by ~Fri 25 Jul**; expiry-stamping at credit time queued for B2.
- Dead-heat bonus wins have no in-app hand-credit path (B1 report F2)
  → B2 candidate accepted (manual-amount credit door).
- Build delegation pattern ratified: background agent with own context
  window = the "separate Code session", preferred.

## Standing-instruction adherence

Silent open/close rituals held (single combined briefs). All money
writes via doors/spine machinery with reasons — zero raw SQL writes.
DR-028 held: placings read by reference (SSH one-off for the sweep;
the built feature uses the 8400-tunnel client). S232 held twice (both
dist rebuilds app-down, verified). Git autonomy exercised: 10 commits
pushed total this session (EV fix ×2, B1 ×7, plus the agent's), all
green-tree. Inventory-first triage on the B1 report. UX-lead shape on
item 8 (verdict chips, one-tap sweep, fail-safe unknowns). Cat-4
promo-terms lesson extended (25%-variant + 1-week expiry →
`bethub_promo_terms_lessons` memory).

## Open items out (closed this session)

Weekend items 3 (restart live), 7 (Sarie credited + gaps zero), 8
rider ($400 second hop), 12 tail (all hops true); EV cap trap; the B1
HIGH fuse + entire truncation-review batch; Vocus 3003 confirm.

## Open items (pointer-only)

`s242_s243_feedback_workplan.md` remains the queue: **A (Mon,
committed): TAB API build (A1 Decodo spike) + race-watcher §6
walkthrough → Tier-1 commission** · C UI pass #3 · B2 (now: void/
delete door, auto-restore-on-void, small-field insurance honesty,
deposit-source door + float tripwire, FB expiry stamping, dead-heat
manual credit door, void-detector wiring) · E operator actions (Sarie
$13 by ~25 Jul; spot-check one verdict chip first race day; BetRight
field-size habit) · F parked unchanged. Burst-review note at close:
operator reports only the two banked FBs visible as items — consistent
with a clean board; detector live and empty.

## Session close state

Rebuild root: no phantom files; `.close_out_backups/` holds only
`SESSION_245_opening_prompt.md`. `SESSION_243.md` given its missing
"Closed:" stamp as a flagged correction note. `v3_build_picture.md`
caught up (S243+S244). bethub-v3 HEAD `2e9abd3` pushed, tree clean,
suites 1511/220 green, app UP on current code.

## Forward routing (CONFIRMED with operator)

S245 opens Monday morning 20 Jul — operator: "It's Monday morning, so
I'll be opening it as soon as the auto agent is complete." First
action: standing checks (auto) → present the Monday A queue → HOLD
(both A items operator-gated). Runner launched at this close.
