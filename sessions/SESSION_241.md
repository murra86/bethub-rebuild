# Session 241 — Tue 14 Jul 18:02 → Fri 17 Jul ~22:00 ACST (4-day continuous session)

## Headline deliverables

1. **VPS hardening Days 3–5 executed and build CLOSED** (`vps_hardening_acceptance_report.md`:
   11 PASS / 2 deferred measurements / 0 FAIL). Day-3 deploy (sweep timer live, collector
   on W7 code, W2 wired), identity + kill + reboot drills all passed, dead-man proven from
   a rebooted box, dogs live (143-race first day, discovery past the old 200-market cliff).
   FOUR cry-wolf families found+fixed live: evening book-id gate, sportsbet-only trials,
   collector operating-window, trailing-window→NEAR-window (17 Jul, pre-empts Saturday's
   gallops→dogs transition). Two REAL catches by the new tripwires: sweep TOO_MUCH_DATA
   death (fixed 10 min pre-jump) + the weight-cap page size. Repos synced throughout
   (racing-data-capture latest `3d6c3b8`).
2. **W7c tool companion** (`w7c_companion_build_report.md`, v3 `3c56ebf`): honest T/H/G
   codes through API→vps_client→picker, wrong-species guard (resolve code pin + 409
   backstop), match-confidence caution, contract §10.3 amendments.
3. **UI pass 12/12** (`ui_pass_jul16_build_report.md`, v3 `34b0e87`+`4bd215c`): runner
   scroll+locked columns+BF Close, EV bands, black-sheet theme, BetLog rework + settle-door
   RESULTS (first consumer of §9.x results surface), dup warning, FB auto-select,
   persist/lapse tags, modal live-conversion + cleanup. Operator live-caught the BF Close
   SP_AVAILABLE request gap within the hour → fixed + regression-pinned. Suites 1464/207.
4. **v3 DATA RESET executed Fri ~16:30, operator-present, ALL GATES PASSED**
   (`v3_data_reset_runbook.md`): backup `bethub-pre-reset-20260717-162916.db`; scoped wipe;
   11 balances seeded via the cash-flow door + 3 day-0 funding events (all capital
   confirmed Tim's; floats 0.00) — **all 14 pairings exact to the cent, total $10,684.67**.
   Runbook lessons: seed BOTH hops (funding+deposits); hand the app back to the operator
   after Claude-launched steps (port-conflict confusion).
5. **Race watcher designed + deep-researched** (`race_watcher_design_note.md` v2,
   `race_watcher_research_report.md` — 103 agents, 25/25 claims verified): EV-at-jump
   engine, TRUST CAPS THE GRADE (operator requirement, research-backed), no CERTAIN tier,
   nearPrice demoted (cached ~60s, live best back beats it late), movement never raises
   tiers, calibration recipe pinned (isotonic ≥1k/bucket, BSP target, ECE/MCE). §6 open
   questions await operator walkthrough.
6. **TAB API scoped** (`tab_api_scoping_brief.md`): 403 root cause = edge bot-protection
   (datacenter IP + TLS fingerprint, live-probed); fix = curl_cffi + residential egress
   (A1 Decodo spike Mon; A2 Pi home-IP relay fallback — never betting SIM lanes); TAB
   already fully wired in capture (one-line re-enable); NO promo data in any API tier;
   integration = selection_id-keyed odds → operational route → Soft Odds auto-fill.
   Studio application NOT recommended (promo-account scrutiny risk) — operator concurred.
7. **BF Close operator masterclass** (Pinjarra/Kilmore/Albion/Rays Redemption live case
   studies) → the trust-gate rules; thin-pool skew both directions; stale-pool-vs-steam.
8. **Aged Care settled**: partial filled IN FULL via persist, $37.91 — first live
   queue-filled case; take-SP analysis updated (give-back side now quantified).
9. **Pi gateway check** (operator-requested): Kate+Sarie lanes healthy; **Vocus lane down
   since Mon eve — needs operator physical power-cycle; UNCONFIRMED at session close.**
   Gap named: Pi lane-down alerts are journal-only (no email) — offered to wire, no
   decision yet.

## Operator decisions this session

Results-retention deferred to post-reset build (then to weekend — reset ran late).
Watcher+TAB = HIGH priority (`priority_flags_s241.md`); TAB build Mon; no Studio
application; strategy shift stated: concentrate EV per promo selectively (spray-cost
pre-build analysis flagged); insurance bets never layed (memory'd).

## Next session (fresh, Sat 18 Jul = BIG BET DAY)

- **Sat: NO new code.** Standing checks at open (vps_health, RACING ALERT in:sent,
  dead-man arrival, off-box freshness); alert watch 2-hourly 09:23–21:23; on-call
  between races. **Hardening runner schedule is RETIRED** (build closed) — only the
  standing items remain.
- **Ask operator: Vocus router power-cycled?** Verify lane 3003 if yes.
- Weekend/Mon queue: results-retention build; watcher walkthrough (§6) → Tier-1 build;
  TAB API build (Mon, per brief); take-SP brief v2 sign-off still pending; theme
  revision verdict; spray-cost analysis; deferred: calendar diff, picker latency,
  W6 fault banner.
