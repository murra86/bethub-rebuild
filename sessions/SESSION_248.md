# Session 248 — Tue 21 Jul 2026 (afternoon → evening)

**Opened** ~15:00 ACST (a day earlier than the planned Wed open —
operator opened Tuesday afternoon) · **Closed** Tue ~20:00.
**Focus:** review-triage fold → balances full review + $165 fix →
BANKROLL MODEL established (operator idea) + display build → TAB
transport hardening built + deployed a day early → account-watchdog
core built (R1–R5). **Closed:** yes — S249 first action is AUTO, see
Forward routing.

## Session-open checks

- VPS health: all clear (disk 37%, sweep ran, 559 races captured).
- RACING ALERT: Sun 20 Jul Pakenham "Stamped coverage" storm (9
  emails) verified already root-caused+fixed at S247 (`53dba6a`,
  ' synthetic' twin-key strip); no data lost (full T-60 capture all
  day); no alerts since. Nothing actioned.
- Date note: operator said "Tue 19 Jul"; actual date Tue 21 Jul.

## What was delivered

1. **AUTO triage done:** all `s248_build_plan_review.md` findings
   accepted + folded — R1–R6 into `betfair_recon_fix_brief.md` item 4
   amendments; T1–T7 inline into `tab_transport_hardening_brief.md`.
2. **Balances full review (operator-flagged):** operation cash was
   inflated by EXACTLY $165 — the UpYaGo withdrawal parked in Tim's
   HIDDEN self-float (UI hides the row assuming the money lives in
   the bank tile; backend counts it in floats). UpYaGo internals were
   perfect (book $0.00, bets net +$5.00). Fix: $165 remittance
   `30b289c3` (backup `bethub-pre-s248-remit-fix-20260721.db`).
   "Moved to your bank" −$11,250.17 decoded: dominated by the day-0
   seed ($10,684.67) booked as funding.
3. **BANKROLL MODEL (operator-commissioned, the day's structural
   win):** dedicated UBank account = the operation's homebase = Tim's
   float, tracked to the cent. Seeded $3,000.00 (incl. the returning
   $165) as ONE funding event `93513c7b` (backup
   `bethub-pre-s248-bankroll-seed-20260721.db`). Op cash 14,940.14 =
   true working capital; P&L 1,054.97 untouched; self-check green.
   STANDING DAILY CHECK: bankroll row == bank app.
4. **Money-page display build (`404a928`, frontend-only, 301 vitest
   green, tsc+build verified):** self float SHOWN as "Bankroll" row +
   counted in card total; Bankroll tile replaces "Moved to your bank"
   (netFlow endpoint kept, unconsumed); "At risk right now" →
   "Current exposure"; deposit source defaults from-float for ALL
   holders; door reads "Tim — bankroll". **Implemented-not-live:
   goes live on the operator's next BetHub restart** (launcher
   rebuilds dist app-down automatically).
5. **TAB transport hardening BUILT + DEPLOYED a day early**
   (capture `625c650`; box suite 125 green, 16 new red-before
   tests; collector+racing-api restarted in the no-race window;
   per-book check live-proven clean first run): T3 full-list hunt
   budget + 120s shared breaker (pins still serve); T7 import-time
   fingerprint validation; per-book frozen-book alarm (check 8, all
   T4 cry-wolf gates, T5 index-scoped); transport counters at
   GET /health/tab-transport + live-poll changed=Y/N lines. Item 4
   cadence config DEFERRED behind the T1 IP-axis gate. **Deploy flow
   established: Mac→VPS git push (`receive.denyCurrentBranch=
   updateInstead` set on the box); github = mirror. curl_cffi 0.14.0
   now installed on the Mac (full capture suite runs locally).**
6. **Account watchdog (recon brief item 4): R4 client extension
   (`9e9dd0c` — settledDateRange, paging, moreAvailable surfaced) +
   CORE MODULE (`f410a6c` — `workflows/balances/v1/account_watchdog.py`,
   13 tests): gross line compare (R1), [watchdog:bet_id] idempotency
   (R2, cent books exactly once — proven), amount = real − derived
   with the sign round-tripped through the REAL derivation both
   directions (R3), paged pull w/ loud truncation (R4), funds compare
   w/ flat-ness caveat (R5), $0.05 ceiling, flag-never-book above it
   (Richmond shape tested). Suite 1704 green.
7. **Ops docs for the operator:** `bank_transfer_playbook.md` (10
   scenarios) + `bank_transfer_quickref.html` (one-screen card,
   opened in browser). Worklist rewritten (items 0/0b/0c/0d/0e).

## Decisions / lessons

- **Bankroll model** kills the is_self special case — a Tim
  book-withdrawal parking in his float is now CORRECT; the morning's
  auto-remit pairing idea was cancelled as superseded.
- Bankroll↔intermediary transfers have NO single ledger event yet —
  interim recipe is the remittance+funding pair (playbook #5/#8);
  one-tap door = worklist 0d (priority raised, labels confused the
  operator live).
- Watchdog surfaces (route/daily/banner) deliberately NOT wired
  tonight: a standalone ops CLI would open a parallel Betfair login
  beside the running app — wrong integration. In-app wiring at S249
  with the supervised first pass (books the standing 3¢).
- "Tile decided": bank tile slot = **Bankroll** (operator call,
  same evening).

## Forward routing (S249 — first action AUTO)

1. **AUTO first:** wire the account watchdog through the LIVE app
   (on-demand route + daily trigger + fault banner), then
   operator-supervised first pass — expect it to book the standing
   3¢ and go clean.
2. Source-freshness probe (transport brief item 5): site-XHR
   endpoint discovery + probe script; tomorrow's cards supply the
   near-jump head-to-head. Cadence stays 8s.
3. Operator restart of BetHub → bankroll screen live; walk the
   quick-ref card on first real transfer.
4. Read the day's first transport telemetry
   (GET /health/tab-transport + live-poll lines + per-book alarms).
5. Glance: `racing-health-check.service` failed state on the VPS
   (pre-existing 6AM email unit, untouched tonight).
6. Standing: worklist 0d (transfer door) queued; 0c holdings
   quantisation; 0e UBank API (LOW, when commissioned).

## State at close

- v3 `f410a6c` pushed (suites 1704 / 301); capture `625c650`
  deployed VPS=Mac=GitHub (box suite 125); both VPS services active,
  liveness all-checks-passed post-deploy.
- Money: P&L +$1,054.97 · op cash $14,940.14 (books 10,270.34 /
  Sarie float 1,669.80 / bankroll 3,000.00) · self-check green ·
  manual queue untouched tonight.
- Backups taken this session: pre-remit-fix, pre-bankroll-seed
  (both under ~/.bethub/backups/).
