**Last updated:** 2026-08-01 evening ACST (Session 263 OPEN — post-race-day
cleanup; S260 deploy verified this session).

**Timezone:** DR-021 standard applies — Adelaide anchors, no overrides active.

---

## Where we are

**v3 in steady daily operation; money records proven to the cent; capture
race-identity ENFORCED and the historical twin backlog now CLEARED; the
S260 capture-resilience release is DEPLOYED and verified.** v3 main
`dd7daec` (pushed; dist rebuilt — live at next app open). Capture VPS runs
branch `s260-resilience` @ `cb4e026` (deployed unattended 04:27 ACST
1 Aug, all Saturday-morning checks passed). Both repos backed up on GitHub.

- **Race identity — FIXED PERMANENTLY, and the backlog is now DONE.**
  Enforcement at all three layers since S259 (DR-036). The historical
  repair completed overnight 1 Aug under the new FK indexes: **5,316
  markets merged in 695s (~7.6/s), orphans zero, zero db-lock errors**.
  679 markets remain in scope, all deliberately-refused classes (540
  identity-gate + 139 settled-count audits) = worklist 0m's population.
  Safety timers re-armed nightly: twin repair 05:05 ACST, gap-aware
  collector restart 04:25 ACST. One proof outstanding: rehydration on
  the first in-window restart (tonight 18:55 UTC) — Sunday reads it.
- **Capture resilience — deployed; core objectives adversarially
  verified; three post-deploy defects found (S263 review), one fixed
  live.** Root cause was the missing runner_id FK index (11.7M-row
  scans = the 7.5s lock holds), not lock policy. Rehydration works
  (exercised live 21×; formal proof at tonight's single 04:25 ACST
  restart). The review found: (1) a deploy-script stamp bug caused a
  20-restart storm + 93-min capture blank right after the deploy —
  **live stamp file fixed 1 Aug eve, storm cannot recur tonight**;
  script code fix queued Sunday; (2) ONE post-deploy RACING ALERT
  (playup frozen from 08:54 UTC, then invisible to liveness once it
  left the candidate set — watch tomorrow's AU card; blind-spot fix
  queued); (3) Ubuntu unattended-upgrades force-restarted the
  collector mid-race-day (~2m17s, Doomben R8 pre-jump ticks lost) —
  OS-upgrade policy is an operator decision, queued.
- **Lay matching (0t-A) — SHIPPED S260, LIVE-PROVEN 31 Jul**: first real
  pairing fired in 1.43s (the control had never fired in production;
  root cause was lay-before-back ordering). Replay: 61/61 lays link,
  zero wrong. Remaining: the 34-row historical repair (script not built;
  `lay_matching_brief.md` §3; app quiet + backup first) — takes cycle
  tracking 74.2% → ~99%.
- **Money truth — audits S260: P&L arithmetic ZERO errors** (332 settled
  bets recomputed to the cent; commission exact across 54 markets); FB
  ledger cross-foots exactly; integrity 81% of bets / 74.2% of cycles
  fully coherent (the gap is almost entirely the lay-linking class
  above). P&L since 17 Jul: **+$2,273 as of S258**; 1 Aug settlements
  pending the Bet365 bonus-cash decision.
- **International Phase 1 — BUILT + 4× reviewed, staged for Sunday.**
  Capture `f2fa921` (498 tests) + v3 glue already shipped. The race rail
  is pinned to AU (`BETHUB_RACING_COUNTRIES=AU` in `BetHub.command`) —
  **delete that line when the capture side deploys.** Then verification
  day, then the one-row GB flip.
- **Race day 1 Aug (S262) — operator verdict: successful.** First
  "bet-earlier" strategy day (segment 1 Aug in any timing/EV analysis —
  `strategy_days.md`). Tim-TAB promo mis-pick fixed via the sanctioned
  correction (third instance → worklist 0x "change promo" button). Race
  day UX batch queued as 0y / 0z / 1a. Morning sweep's first Saturday
  ran (formal §4 acceptance report still owed).
- **promo-pilot (satellite, informal S261)** — standalone TAB promo-EV
  page at `~/Desktop/Projects/promo-pilot`, reads BetHub read-only,
  parity-proven engine; morning review issued operator rules; TAB→EV
  live-proven 07:45 (14/14 races). NOTE (found S263): the BET NOW
  strip was REMOVED in code 1 Aug 08:02 (backup
  `page.py.bak-20260801-betnow-strip`) in favour of a per-race hot
  count that suppresses itself once the race jumps — this FIXED the
  morning review's "BET NOW survives the jump" defect; change was
  unrecorded at the time. Operator day-use verdict pending.
- **Analytical standing:** promo-EV indicator VALIDATED (S253); scope
  discipline stands — simple per-runner promo-EV, no rankings, free
  bets/market-edge out. model.db needs a re-extract before parked
  research resumes (race ids pre-date the twin merges).

## What's next

**S263 remainder (operator-directed at S262 close):** feedback batch
walk-through + full worklist review together. Carry-in decisions:
Bet365 bonus-cash uplift % / cap (5 winners, $599.50 profit waiting);
4th/5th cashback promo template (offered, not yet built); Mango deploy
(port-forward + AdsPower profile + F19, pending since S258).

**Sunday 2 Aug queue:** rehydration check (single restart expected
tonight after the stamp fix) → International Phase 1 deploy (delete
the AU pin after) → 34-row lay repair (backup first) → 0w SIM-gateway
hardening (alerting first) → deploy-script + restart-guard code fixes
(0u tail) → morning-sweep §4 report → 0m mini-brief → playup check on
the AU card. Then 0t-B cycle accounting when sequenced.

## Required reads for Session 264

In order:
1. `current_state.md` (this file).
2. `standing_instructions.md` — in full per Cat 2.
3. `sessions/SESSION_262.md` (race day) + `SESSION_260.md` postscript
   (deploy verification).
4. `worklist.md` — statuses reconciled 1 Aug.

## Pending operator-side actions

- Bet365: rate CONFIRMED (25% cash on winnings, balance-verified
  $859.38); credits BANKED 1 Aug 23:07 via the tool's own auto door —
  which computed 4 of 5 a touch high under the hardcoded TAB
  whole-dollar-ceiling rounding rule (NOT operator typing; and
  return_pct=0.25 was already stored, EV already right). **Tool
  overstates Bet365 by $2.12** until the 1b correction lands.
  **Worklist 1b SHIPPED END-TO-END** (`d3583cf` + `bdadb8f` +
  `2daa17a`; 3+ adversarial reviews; correction RUN 2 Aug 06:15,
  $859.38 exact): rounding is a per-template term; the credit box
  computes the bonus; cash credits undoable in-app; **auto-bank on
  Won live at restart** (operator approved all recommendations —
  Burst Review auto-lane + undo as review path); corrections keep
  the original economic date; the BetLog strip now shows "bonus cash
  + all-in" so it reconciles with the Accounts page; the manual
  settle door no longer wipes dead-heat facts. Remaining: operator
  restart, live smoke on today's first bonus win, 0t-B
  cycle-complete number.
- ~~3 money events 16:21–16:24~~ **CONFIRMED by operator S263**
  (Kate withdrawals + profit share = intended end-of-day banking);
  money check re-run clean after.
- Which of the restored race-day live-proof batch items (worklist
  item 5) did 1 Aug actually cover? (panel checks / first reassign /
  TAB eyeball / Take-SP Stage 0.)
- OS-upgrade policy on the capture box: unattended-upgrades restarted
  the collector mid-race-day — recommend pinning service restarts to
  the 04:00–06:00 maintenance window (Sunday build if agreed).
- Mango proxy hookup at the friend's house (then cross-button F19).
- Promo-pilot day-use verdict (keep / change / park) — incl. blessing
  the 1 Aug BET NOW → hot-count change.

## Open items (accepted-as-minor, revisit only if they bite)

- Sarie-Ladbrokes free-bet credits: ALL SIX (the 5×$30 split + a 6th
  $30 triggered 1 Aug) are now fully deployed — zero live, expiry
  loose end moot (corrected S263; the $10 goodwill credit separately
  expired at the book 1 Aug, recorded honestly). The 0v split/undo
  build itself remains queued.
- Fill-odds click: released cells blank a few seconds until the feed
  re-seeds (cosmetic; 0i added the release path).
- First transport-block on a live TAB session stalls the refresher for
  the hunt duration (inline path carries the feed meanwhile).
- Stored `matched_price` is float (REAL) — Decimal hygiene is separate,
  larger work; and 0z(d) will store the true matched average.
- "Kensington Park" (Whangarei NZ) would alias to randwick if a book
  ever emits that spelling — watch item; no book does today.
