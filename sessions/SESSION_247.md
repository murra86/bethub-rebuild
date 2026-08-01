# Session 247 — Mon 20 Jul (night) → Tue 21 Jul 2026

**Opened** ~20:45 ACST Mon · **Closed** Tue evening (single session
spanning the race-day live-proof). **Focus:** void-gap design lock →
race-day full-stack live-proof (with three live catches) → four-branch
build + single deploy (`a195cf2` → `64ff337`) → audited data
corrections → Betfair reconcile to 3¢ → Wed build plans + review.
**Closed:** yes — S248 FIRST ACTION IS AUTO, see Forward routing.

## What was delivered

- **Mon night:** void-gap design walkthrough LOCKED (D1 attended tap /
  D2 before-after confirm / D3 post-live-proof); design note carries a
  code-verified annex at `a195cf2`. Pakenham coverage fix committed
  with red-before regression test (`53dba6a`, VPS=Mac=GitHub). $13-FB
  memory scrub. bethub-rebuild reorganised (root 200→54; manifest
  `FILING.md`; archive/<topic>/ + router-sim/).
- **Tue morning (pre-racing):** clean-session bet-data review AUDITED —
  both scary flags false alarms (BetRight $0 = documented phantom; TAB
  void re-credit exists via supersession chain); real find = the $13→
  $10 FB face rounding bug (HedgeModal `FB_STAKE_ROUNDING_INCREMENT`).
  Downtime sweep: suites 1618/280 green as-deployed, store forensics
  clean (baselines: S1 stale-legs 23; books total $10,725.64), 2-agent
  code review → 2 HIGH (TAB staleness/override) + 5 MED, all triaged
  (`s247_downtime_review_record.md`). Live-proof proceeded with 7
  briefed disciplines. Re-class door + audit migration live-proven on
  the phantom (forensic verify incl. byte-identical rebuild).
  LPB re-log of the real Tim@TAB bet verified end-to-end (+$325;
  weekend truly ~+$1,220).
- **Tue race-day catches (the live-proof earning its keep):**
  1. TAB burned our TLS fingerprint TWICE (~11:55 "safari", ~13:22
     "safari17_0") — hotfix then MINIMAL ROTATION deployed same day
     (ranked candidates, per-pool pin, burn telemetry; box suite 109
     green; capture repo commits `e215ba1`/`b5ce10d`/`480de45`).
  2. Operator caught the $29.67 Betfair gap → root causes: premature
     FINAL_FULL (Richmond settled on 13.47 vs account's 38.70) +
     commission charged per-bet vs Betfair's per-market-NET.
  3. Beta API price lag vs the TAB website near jump (Azucar/Keen
     Observer) → source-freshness scoping is STEP 1 of Wed's build.
  Also: collector restarted once on a WRONG diagnosis (my clock error
  — 09:23 tick read as 11:23); procedure rule written into memory:
  anchor `date -u` before interpreting log windows; restarts need
  positive evidence. Bounded cost: minutes of dog-race capture.
- **The deploy (operator-approved branch by branch):** four worktree
  branches merged → `64ff337`, gates 1687/301 + dist, app relaunched
  clean. Contents: TAB feed fixes (T1/T2/T3/T5), FB single-source,
  door hardening (B5 unique backstop incl. a found double-SPEND hole;
  B2 include_sibling), recon fixes (FINAL_FULL guard + settlement
  cleared-orders backstop; market-net commission), void re-true
  (attended tap, `BET_RECLASSED source=system`, B4 flag-clearing,
  4th honest outcome `no_account_record`).
- **Audited data corrections (operator-present; backup
  `bethub.db.bak-s247-pre-corrections-20260721-143749`):** Richmond
  matched 13.47→38.70 from a LIVE cleared-orders read; Vesta Bale +
  Spirited Defence relabelled final_partial with honest unmatched;
  4× $0.00 DAY_0_OPENING markers (incl. Tim — the Balances warning
  counts is_self) → all floats seeded, warning gone. Every write has
  a system-sourced bet_edited/adjustment event.
- **Reconcile result: $29.67 → 3¢** (derived 2,428.99 vs real
  2,428.96; residual = Betfair per-line cent rounding from sub-cent
  matched sizes). Operator wants zero → **cent-truing folded into the
  Wed watchdog**: per-line attributable diffs auto-book as audited
  "exchange ledger rounding" adjustments; unattributable diffs FLAG
  ONLY. Guarantee: match to the cent or a named flag, daily.
- **VPS extras:** daily heartbeat staleness now lull-aware
  (`d4f4306`); S245 capture-side work committed after proving
  (`b5ce10d`/`480de45`); Pakenham dup-fragment watch stands.
- **Operator decisions recorded:** partial FB re-credit NO BUILD
  (books don't give change); capture window stays T-60m; promo-bar
  Clear button queued; P&L-after-shares display queued (arithmetic
  confirmed: 1,049.97 − 200 = 849.97); profit disbursements confirmed
  excluded from all cash-on-hand figures (gross P&L is the only
  add-back, by design).

## Still open / unproven

- FB hedge + pairing visibility live test — Wed is a TAB
  bonus-winnings day; single-source fix now live for it.
- Void re-check tap awaits its first real flag. Take-SP Stage 0
  awaits an operator-present race day. Promo template terms (7-day
  TAB expiry etc.) set per template as used.
- Answered-flag-never-re-warns residual (void re-true) on the watch
  list. S1 stale-leg baseline 23. ±3¢ Betfair band until the
  watchdog's first pass books it.

## Forward routing (CONFIRMED with operator)

**S248 FIRST ACTION (AUTO, before anything else after standing
checks): triage the Wed build-plan review** — findings file
`s248_build_plan_review.md` (written at S247 close from the
background reviewer's report). Fold accepted findings into
`tab_transport_hardening_brief.md` + `betfair_recon_fix_brief.md`
item 4, then build in this order:
1. TAB transport hardening — SOURCE-FRESHNESS SCOPING FIRST (the
   website's own endpoint vs api.beta lag), then rotation upkeep,
   per-book NEAR-window alarm, telemetry, cadence-as-config.
2. Betfair account watchdog + cent-truing (books the 3¢ opening act).
3. Operator's FB live test during the day (bonus-winnings promo).
Deploy discipline unchanged: worktrees, gates, app-down swaps outside
racing hours only.
