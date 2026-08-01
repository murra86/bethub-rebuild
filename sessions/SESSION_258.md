# SESSION 258 — 28 Jul 2026 (afternoon) + 29 Jul continuation — CLOSED 29 Jul eve

**S259 OPENING DIRECTIVE (operator): open with a summary of pending
action items, a short memory refresher for each, and recommended next
steps.**

## Scope
Session-open standing checks → root-caused and fixed the false "Data API"
RACING ALERTs (capture-side). 29 Jul continuation: two operator drops
recorded, runner display-order fix shipped (v3 `7b4c7bf`, §5).

## 1. Standing checks
- **VPS health:** all clear (disk 39%, collector running, DB fresh, backups
  healthy, overnight sweep ran 81 attempted / 24 walled). 8400 tunnel down =
  app closed, normal.
- **RACING ALERT sweep (2 days):** six alerts. The overnight/morning
  book-frozen ones match the known foreign-racing false-alarm pattern S257
  already triaged (TAB transport self-rotated a burned fingerprint at 03:58
  UTC and recovered on its own). The two **"Data API: timed out"** alerts
  (27 Jul 23:45 UTC, 28 Jul 04:16 UTC) were new — investigated below.

## 2. False "Data API" alerts — root cause
The API was never down. During both failure windows racing-api was serving
soft-odds requests at 1.5s cadence; the liveness probe's `/health` request
never even reached uvicorn's log.

Cause: `/health` (and the liveness checker's own global freshness check)
computed `MAX(snapshot_time)` over `betfair_snapshots` (4.0M rows) and
`bookmaker_snapshots` (7.4M rows). Neither table has a plain
`snapshot_time` index, so SQLite walked the full covering index of the
4.8 GB DB — **measured 30s / 35s per table on the live box**. The probe's
timeout is 5s → false alarm whenever racing-hour write load slowed the
scan. The same scans also explain the 20–45s the liveness pass itself took
every 15 minutes.

Handler runs in FastAPI's threadpool, so the event loop stayed free —
which is exactly why every other endpoint kept working while `/health`
timed out.

## 3. Fix (capture `00a76ac`, deployed + live-proven)
Replaced both `MAX(snapshot_time)` reads with newest-row-by-rowid reads
(`ORDER BY rowid DESC LIMIT 1`, liveness variant keeps the S255
non-MORNING filter and stops at the first live row). Valid because the
collector appends in time order. No new index — a `CREATE INDEX` on a
4.8 GB table would have blocked collector writes mid-card.

- Files: `api/routes/health.py`, `scripts/liveness_check.py`.
- Gates: 198/198 pytest.
- **Live equivalence proof:** old vs new query on the production DB —
  identical values, 30s→9ms (betfair) and 35s→20ms (bookmaker).
- Deployed: push to VPS + GitHub, racing-api restarted (app was closed).
- **Live-proven:** `/health` 200 in 59ms (was timing out); two manual
  liveness passes all-green in ~0.15s (was 45–65s); 06:15 UTC scheduled
  run confirmed clean.

## 4. Collector restart at 06:07 UTC — not ours, benign
racing-capture restarted during the deploy window. Traced to Ubuntu's
daily `apt-daily-upgrade` (systemd package upgrade restarted cron,
fail2ban, racing-capture, etc.). Graceful shutdown, back in 13s, all
freshness checks green after. No action.

## 5. Runner display order fix (29 Jul, v3 `7b4c7bf`)
Operator sighting: Eagle Farm R1 runners rendering 4, 3, 9, 6, 10, 8…
Cause: the S256 streaming cutover serves `prices.runners` in first-image
arrival order (arbitrary); the old REST path happened to arrive
card-ordered, so nothing in the chain ever sorted and the page inherited
the scramble. Display-only defect — all money paths key runners by
selection_id / object identity.

Fix in OddsTable only: a sorted display COPY ordered by the runner-name
cloth-number prefix (same regex family as the # column), catalogue
`sort_priority` fallback, unresolvable runners last in stable feed
order. `prices.runners` itself untouched — activeRunners/fieldProbs/EV
indexing unaffected. Red-before tests (2, failed pre-fix); gates
461/461 vitest + tsc + scratch-dir build (served dist deliberately NOT
rebuilt — app was open; S232 rule). **LIVE at next app start** (launcher
rebuilds dist app-down).

## 6. Operator decisions recorded (29 Jul)
- BetRight ≥8-runners template term DROPPED permanently (no promos from
  BetRight; only book needing it). Worklist item 2 closed.
- UBank bankroll automation DROPPED (stays manual). Worklist 0e closed.
- Mango proxy deploy at the friend's house happening 29 Jul; operator
  will ask for live assistance completing the connection.

## 7. Post-restart confirmations (29 Jul, operator)
- Runner order LIVE-CONFIRMED (saddlecloth order on screen).
- Money check gap 0.00 — S257 watchdog-truing thread fully closed
  (optional dry-run day-loop proof not needed).
- Transfer-control walkthrough (0d) delivered; remaining: first real
  transfer at the next float move.

## 8. Keychron hot buttons COMPLETE (29 Jul, operator-confirmed)
Circle→Sarie, triangle→Kate, square→Mads — one press opens/focuses that
AdsPower profile browser (launcher `~/bin/adspower_hotkey.sh` via the
AdsPower local API; Automator Quick Actions + Services keybinds;
triangle/square remapped to F17/F18 in VIA — factory F14/F15 collide
with macOS brightness). Cross reserved for the Mango profile (F19 +
one Quick Action when it exists). Full as-built in
`keychron_hot_buttons.md`. Transfer walkthrough (0d) also confirmed
complete this morning — only its first real use remains.

## 9. Randwick TAB column blank — twin-row instance, fix DEFERRED to 0l
Operator sighting 29 Jul: no TAB odds on Randwick races. Root cause:
Kensington-track meeting split into three venue variants — "randwick"
(7 races, betfair market ids + 8/8 selection stamps, NO tab data),
"randwick kensington" (same market ids, tab_race_id RKE/n + full TAB/
book/Betfair snapshots, ZERO selection stamps), "kensington" (empty
shell). Both soft-odds endpoints resolve the TAB fragment (correct per
DR-034 ordering), key by betfair_selection_id, find none → `runners:
[]` → blank column. Confirmed live against both endpoints on market
1.260470533. Day-wide sweep: Randwick's 7 races were the ONLY affected
markets on 29 Jul. Capture unaffected (odds landing on the twin).
Operator decision: NO patch — permanent class fix commissioned as
worklist 0l (join hardening + de-twinning at creation + historical
repair; ties to S252 63% twin-attachment finding and the S256
data-reset thread).

## 10. 0f BUILT — hide/restore book rows + pairing review (v3 `b42820d`)
Operator commissioned the sitting after closing PF + transfer items.
Deep review first (S249 conduct rule): explorer mapped bet-entry
validation (3 of 4 write paths accept ANY pairing string — no FK, no
active/balance checks; Other Bet = existence-only 422), the `active`
flag's blast radius (pickers, BetLog labels/filters, PnL totals +
self-check, account watchdog, reassign/FB/promo-chain correction gates
— disqualifying it), and the burst-review machinery (NO flag store;
every section a live derivation).

Built, additive-only: display-only `accounts_at_book.hidden` column
(idempotent _add_column_if_missing migration, runs at next app start);
repo setter + hide/unhide endpoints (un-hide first-class — no one-way
door, unlike close, which 409s on re-register); listing passthrough
(pickers deliberately unchanged — hidden pairings stay selectable);
Balances: hide button per row, S237-style inline confirm naming
outstanding balance/pending/FBs (warns, never blocks), hidden rows
keep their cash in card totals, per-card fold-out with restore.
Permissive-entry half: write paths untouched (already permissive);
new derived read GET /v1/bets/pairing-review (7-day window, no stored
state) surfaces bets at hidden AND phantom pairings — the phantom case
also closes the long-standing silent-accept visibility hole — rendered
as a Burst review section with repair pointers (restore from Balances /
reassign from BetLog). v1 exclusion per conduct rule: no
balance-at-log-time flagging (not recorded anywhere; retroactive
derivation would mislabel normally-settling books).

Red-before tests at every layer. Gates: 1926 pytest / 465 vitest /
tsc / scratch build (served dist untouched — app open). LIVE at next
app start; walkthrough owed then.

## 11. 0f live-confirmed + refinement (v3 `5c389e9`)
Operator restarted, hid inactive books, confirmed working. Refinement
same sitting (operator-directed): hidden pairings excluded from the
race screen book chips (TopBar only; Log Past Bet unchanged so history
at hidden books stays recordable; burst-review section still catches).
Red-before test; 466 vitest. Live at next app start.

## 12. Early-bet jump watch + race-rail pending dot (v3 `048bf96`)
Operator placed 4 early positive-EV bets (~10:30 ACST, aware of risk):
Leigh-TAB Randwick R1 #6 Crown Of Fire @3.40 + Sandown R5 #9 Foire De
Trone @4.20; Tim-AllBets Randwick R1 #6 @3.68 + Eagle Farm R2 #8
Exceed The Sale @3.52 (all $50). Jump watch armed (Monitor →
scratchpad jump_watch.sh): waits per race (EF R2 12:03 / RW R1 12:20 /
SD R5 14:15 ACST), polls market_status past scheduled time, reports
final TAB + Betfair back vs taken. AllBets not in capture's book set —
TAB/Betfair are the stated reference for those two. Randwick reads ride
BOTH twin rows (3406592 + 3395587) so the twin bug can't blank them.
First reading at arm time: EF #8 already 3.52→3.10 (shortened, EV
positive so far).

Race-rail pending dot SHIPPED same ask: small amber dot after venue on
races carrying pending bets (feed read state=pending/500/30s in Racing
→ Set of leg market ids → optional sidebar prop). Red-before; 468
vitest. LIVE-CONFIRMED by operator post-restart same sitting.

## 13. Settlement-worker queue item — stale, CLOSED (29 Jul)
Operator challenged the standing "supervised live run pending, flag
OFF" item ("Betfair bets are already auto-settled" — correct). Code
verification: launcher has defaulted `BETHUB_SETTLEMENT_WORKER=true`
(+ reconciliation worker) in live since 6 Jul (`4f98ad5`, r11/gate 2+5
work) — the worker has been live for three weeks; the queue item and
its memory were overtaken and never updated. Closed. Recorded facts:
worker settles BETFAIR bets only (copies the exchange's settled
record); soft-book bets remain operator-settled via Won/Lost/Void —
boundary enforced BOTH directions in the settle endpoints (Betfair
bets refuse manual settle; worker never touches soft books).
Acceptance evidence in lieu of the never-run supervised session: all
of July's daily to-the-cent money checks + S257's 76-line ledger
proof. Memory `settlement_worker_liveproof_blocked.md` marked CLOSED.
Also this sitting: Randwick R3 #8 Eviction Notice @2.40 (Tim-TAB,
$50) added to the jump watch (6 bets / 5 races).

## 14. Race-day corrections pass (29 Jul afternoon — all four operator
items closed)
(1) Leigh-TAB EF R1 Benefit Of Doubt: loss→VOID reclass verified
(bet_reclassed 13:59, reason "Late scratching") — flowed correctly.
(2) Leigh-TAB SD R5 Foire De Trone late-scratching deduction: operator
self-fixed price 4.20→4.116 via the settled-edit door (3 audited edit
events, final 4.116, payout 205.80 == TAB real) — verified; balances
reconcile. (3) FB credits banked+verified: $25 Sarie/Exceed The Sale +
$30 Leigh/Crown Of Fire (auto) + $40 Leigh/Foire De Trone (MANUAL
door — TAB credited on pre-deduction 4.20 odds; ordering trap
documented: price-edit BEFORE banking, manual amount because auto
would compute 38.95). (4) **HAND-FIX (operator-confirmed, app
closed): two Tim-AllBets winners were mislogged under "TAB Bonus
Winnings 25% to $50 (FB)" but were boosted-odds bets. Swapped
promo_template_id 87878499→31cb9535 ("Boosted Odds", price_boost) on
bet-ee415adb-4dc5-518e-8005-628db2acb4d2 + bet-ee4fb0ff-33f8-594f-
8bbc-c738e6de003e (2 rows, quick_check ok). Backup:
data/bethub.db.bak-s258-pre-promoswap-20260729-145104.** In-store
audit event NOT written — BetSnapshot (extra=forbid) has no promo
field, a faithful diff is unrepresentable; this record + backup IS
the trail (S222 precedent). Effect: the two false "bonus landed"
suggestions (~$31.50/$33.50 never-owed credits) disappear; promo
attribution correct. Follow-up idea (NOT commissioned): in-tool
"change promo" control on BetLog if this error class recurs.

## 15. Corrections-pass verifications + promo-name display (v3 `b1d683a`)
Operator eye-verified the template swap via the raw id prefix
(31cb9535) — both sides confirmed. Corrected record: day tally was
5 won / 5 lost / 1 void (my "3 won" miscount corrected by operator);
pending excluded: Sarie's deployed $25 FB on 3. Swag + its $20.39
Betfair lay. Shipped on the back of the verification gap: BetLog
expanded detail now shows the promo NAME (raw template id on hover) —
shared catalogue query, red-before, 470 vitest. LIVE at next app
start.

## 16. P&L/EV evaluation + FULL EV-calculation audit + fix (v3 `e63e7d3`)
Operator asked for P&L + EV-vs-real ("I think we're running hot").
Findings: +\$2,273.07 since 17 Jul day-zero (self-check green) vs
+\$1,828 EV logged on the backs → +\$445 raw luck (~24% hot), FB
conversion realizing 70.1% vs 65% assumed (+\$140 of the gap); with
the standing S231 ~3pt screen-EV haircut, true heat ≈ +\$850 — still
inside one SD of variance over ~240 backs. Verdict: hot but normal;
plan on \$6–8/qualifier.

Operator screenshot (Randwick R6 Rantan: column −2.4% vs panel
+\$0.36) → full audit commissioned. Report:
`bethub-rebuild/ev_calc_audit_s258.md`. ALL formulas sound (probs
S253-validated; insurance/free-bet/boosted/raw checked by hand; panel
EV analytic and correct). ONE defect (D1, exact reproduction:
\$50→+0.664%, \$100→−2.411%): bonus-winnings presets leave max_stake
null by design, but five consumers valued at `max_stake ?? 100` — the
\$50 bonus cap falsely binds from odds 3.0, understating boost bets
odds 3.0–5.0 on the column, ConfirmCard, Call grades, panel candidate
default, and STAMPED promo_ev_at_log (→ the 25 settled
bonus-winnings bets' logged EV understated ~\$30–40; fortnight luck
≈ +\$410 not +\$445). Display/analytics only — no money path reads
these. Fix `e63e7d3`: shared DEFAULT_HYPOTHETICAL_STAKE=50 replaces
every ??100; both log doors stamp at the bet's REAL typed stake via
snapshot.promoEvForStake. Red-before at all three surfaces; 474
vitest. LIVE at next app start. Deferred: historical
bonus_winnings promo_ev_at_log recompute (approximate only — full
field not stored); the S231 haircut stays out of code.

## Carry-forward (unchanged)
- Operator eyeballs TAB column vs app (~4–6s finals expected).
- Sat 1 Aug sitting DEFERRED (operator away) → live-proof batch moves to
  next attended race day (likely Sat 8 Aug).
- Operator: BetRight ≥8 template, PF cancel check, Keychron setup.
