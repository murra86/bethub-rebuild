# SESSION 256 — 28 Jul 2026 (early morning)

**Scope:** session-open standing checks → the 26/27 Jul "Book frozen"
alerts (root-caused + fixed capture-side) → 0j built+deployed+
live-proven (§3) → quiet sitting: Saturday feedback batch + stake-edit
completion (§6) → LIVE streaming-ladder bug found off an operator flag
and fixed+deployed before racing (§7). Everything on main `dbbc626`.

## 1. Open

- VPS health: all clear (disk 39%, collector running, backups fresh,
  sweep ran attempted=80/walled=25, tunnel up, 377 races captured).
- RACING ALERTs found: "Book frozen" 26 Jul (5 books) + 27 Jul
  (6 books) — investigated below. 25 Jul "Stamped coverage" (Murtoa)
  was already explained in S255 §1.

## 2. Book-frozen alerts → trial-meet contamination (FIXED, capture `3496816`)

**What the operator should know: the two alerts were false alarms — no
capture was lost. But the cause was real and had been quietly damaging
race records since March. It is now fixed.**

- Mechanism: The Racing API lists same-course barrier-trial meetings as
  SEPARATE meets under the SAME course name (27 Jul had two "Albury"
  meets: the real 8-race card + a 1-race "OPEN TRIAL" at 16:35, same
  course_id). capture.db keys races on (race_date, venue_normalised,
  race_number), which cannot tell them apart — so the trial's R1
  upserted ONTO the real Albury R1: scheduled_start / race_name /
  is_trial / winning_time flipped to the trial's, and the trial's
  horses were injected as extra runner rows (the RC-2 guard correctly
  deflected them to S: keys — real results were never overwritten).
- The alerts: the trial's post-card start time kept the liveness NEAR
  window open after the day's real races ended, so 6 books that had
  simply finished their day were flagged frozen. Same shape on 26 Jul
  (Sapphire Coast + Kalgoorlie trial meets, WA evening timing).
- Damage measured (capture.db, 28 Jul): **1,065 book-priced races
  flagged is_trial=1** (invisible to the results backfill — silent
  results-coverage loss), **394 races carrying two interleaved
  fields**, growing 1–4/day since March. Race-1 bias (trial meets are
  mostly 1–3 races).
- Fix (standing capture-fix authority): the subscription sync now
  SKIPS trial/jump-out races outright (`is_trial`/`is_jump_out` are in
  the API payload; nothing downstream consumes subscription trial data
  — every analytical query already excludes trials). Red-before test
  `tests/test_subscription_trial_guard.py`; 149 local + 3-on-VPS tests
  green; deployed `3496816` (VPS + GitHub). Also fixed in passing: two
  latent 2-tuple returns in `_sync_single_race` (callers unpack 3).
- Self-repair: the nightly backfill re-pulls the trailing 14 days, so
  recent contaminated metadata heals from tonight's 20:00 UTC run.
  **Left for the data-reset thread:** pre-14-day metadata (is_trial
  flips, trial start times), the injected S: runner rows, and the
  question of whether trial-runner rows leaked into any calibration
  join (S253 used odds-joined runners, so likely clean — verify).
  NEW TWIN-ROW LEAD: this class sits alongside the S255
  synthetic-suffix lead as a plausible S252 twin-row generator.

## 3. 0j BUILT + DEPLOYED (same sitting — operator returned, tool was
## shut down; merged to main `e5d8e83`, pushed; live-proof in §3b)

Both halves built in the one sitting, red-before tests at every money
surface. Working tree returned to main + dist rebuilt from main, so an
unattended app launch still runs exactly what S255 shipped. Deploy =
check out the branch, `npm run build`, restart, with the operator.

### Other-code bet row
- `bets` gains nullable `bet_code` ('conditioning'/'sports') +
  `event_description` (Alembic `0002_other_code_bets`; racing bets
  carry NULL in both).
- Records are **legless** — no Betfair stamp exists for a free-text
  event, and leglessness keeps them invisible to the settlement
  worker (`list_unsettled_bets` inner-joins legs), lay pairing and
  void-recheck by construction. All `legs[0]` sites audited: guarded.
- `POST /api/v1/bets/other`: AAB checked hard, extra fields rejected,
  BET_CREATED audit as on the manual path. PENDING default → settles
  through the existing BetLog Won/Lost/Void door (no leg guard there);
  terminal-at-entry allowed for backfills.
- Money proven in tests: pending commits the stake; a won settle pays
  stake × (price − 1) to the cent ($40 @ 1.38 → −$40 then +$15.20).
- UI: new **Other Bet** screen (person/book/kind chips, free-text
  event, stake/odds, bet date, Pending/Won/Lost/Void). BetLog names
  legless rows by their event text and shows the kind (Conditioning /
  Sports) where venue+R№ would sit.

### Goodwill/deposit credit door (rider)
- `record_account_credit`: FB or cash credit anchored to the
  ACCOUNT-AT-BOOK with `credit_source='freebie'` — the domain shape
  that existed with validation + the "goodwill" inventory label but no
  writer. Mandatory reason; expiry on FB only; client idempotency key
  (one per opened card) stamped as correlation_id — replay returns 200
  `already_banked` with the original event, fresh key banks again.
- `POST /api/v1/promos/account-credits`; Balances book rows gain a
  **credit** button beside ＋/− opening a MovementCard-style card.
- Gates: 1884 pytest (32 new) · 437 vitest (9 new) · tsc ·
  `npm run build` · no new ruff/mypy findings · import contracts kept.

### 3b. Deploy record (operator present, 28 Jul ~07:25)
1. Branch checked out, dist built, app launched via BetHub.command —
   clean start, both workers ON, VPS race lookup connected, schema
   migrated additively on connect (bets 32/33 = bet_code /
   event_description).
2. Pre-entry DB check (app down): Allbets/Tim held ONE deposit
   ($200) + three settled-lost racing bets ($20/$30/$20) — **no −$40
   adjustment had ever been booked**, so the backfill could not
   double-count. Two Allbets racing bets (26/27 Jul) postdated the
   conditioning log.
3. **$40 AFL bet backfilled** through POST /v1/bets/other
   (`bet-b1fa124b…`, pending): balance moved to $90.00 cash /
   $40 pending — the exact real-money gap the log predicted. Settled
   LOST through the existing door (Collingwood 108–74): pnl −$40.00,
   pending 0, cash $90.00.
4. **$100 FB banked** through POST /v1/promos/account-credits: shows
   in inventory as $100.00, label "goodwill", source freebie, expiry
   22 Aug 2026 23:30. Winnings-only term stays operator-managed (the
   tool doesn't model FB terms).
5. `conditioning_bets_log.md` retired to a conditioning diary.
6. Merged ff to main `e5d8e83`, pushed; feature branch deleted. The
   running app was untouched by the merge (no uvicorn --reload; tree
   ended byte-identical).

**Operator confirm (10 seconds, anytime): Allbets app should show
$90.00 cash + the $100 bonus bet — the tool now claims both.**

## 4. S256 queue remainder (unchanged from S255 close)

- Quiet sitting: Saturday feedback batch + settled-stake-edit button.
- **Sat 1 Aug sitting:** race-day live proofs + first live reassign +
  Take-SP stage 0 + morning-sweep §4 acceptance + 3 parked panel
  checks (additivity, $-at-risk, steadies/concentrates).
- Operator anytime: BetRight ≥8 template (day next used); confirm
  Punting Form cancelled.
- Small: 1-cent Betfair recon banner on Tim (2 min in the next
  money-check sitting).

## 5. Mid-morning operator flags (07:36)

1. **1-cent Betfair banner (queue item 5) — examined, not dismissed.**
   Zero-tolerance funds check, account flat, genuine 1c: Betfair
   charges commission cent-rounded per market; our derivation keeps
   exact fractions — structural penny residue. No bet is wrong.
   QUEUED: quantize derived commission per market as Betfair does
   (money-path change, own tested sitting). Banner is informational
   until then; do not chase the cent by hand.
2. **"No Betfair odds on the race page" — REAL BUG, found + fixed +
   deployed (see §7).** Note for the record: an early theory ("Betfair
   books empty in the morning") was an artifact of two broken probes
   (wrong attrs on betfairlightweight lightweight dicts; wrong field
   names on the app payload) and was retracted — raw listMarketBook
   showed full books throughout. Swan Hill R1 separately has zero
   capture snapshots because it is one of today's trial-contaminated
   rows (§2) — the sweep's identity guard rightly refused it.

## 6. Quiet sitting BUILT (`f8089df`): Saturday feedback batch + stake-edit completion

- **BetLog date filter (item 4):** preset chips Today / 7 days / Month /
  All time + the calendar inputs; NEW whole-window period strip (P&L,
  staked settled, W/L/V, pending $) folded server-side over every row
  the filters match — never a page sum. `BetPeriodStats` on the feed.
- **Settled stake-edit (S254 follow-on):** the door itself had shipped
  in S237 — completed it: UI now moves BOTH stake fields on soft-book
  edits (the requested/matched incoherence is what really forced the
  Sarie script); NEW banked-credit fence on money edits (409 naming the
  credit + revoke door — same cure as reclass; tag-only edits pass);
  three stale PENDING-only docstrings corrected.
- **Race page:** ★ + holder letters on runners with a current bet
  (item 2); "Fill odds from my bets" button (item 6 — wipes entered
  odds, fills bet runners with entered price, averaged; TAB auto-feed
  cannot refill/overwrite); activity board "Unmatched $xx.xx at y.yy"
  from the live current-orders join (item 8).
- Not in batch: promo-flag highlight (blocked on "log promo"), FB CALL
  confidence (needs the 70% definition), TAB ~10s lag (investigation),
  Keychron macros (OS-side, not BetHub).

## 7. LIVE BUG: streaming ladders never parsed — FIXED + DEPLOYED (`dbbc626`)

The operator's 07:36 flag was real: the market subscription requests
EX_BEST_OFFERS_DISP (wire fields bdatb/bdatl, [level,price,size]
triples) but the mcm parser read only atb/atl — every live ladder
parsed EMPTY while ltp flowed, the streaming cache served priceless
markets, and cache eligibility kept REST from being consulted. The
raw-frame test fixtures encoded the same wrong wire contract (27 tests
locked the broken behaviour); streaming bring-up is recent, so this
first met real traffic THIS morning. Fix: parser reads the disp
triples; StreamingClient keeps per-runner level maps (image resets,
size-0 removes, ltp-only preserves) and rewrites ladders from the
merged map before the W2 whole-runner replacement. 6 new tests.

**Deployed 08:14** (merge ff to main `dbbc626`, dist rebuilt, app
restarted with operator present): fresh envelope, full 3-level ladders
matching the raw book to the tick. Momentary
SUBSCRIPTION_LIMIT_EXCEEDED as the old process's stream died →
recovered SUCCESS.

Gates across §6+§7: 1896 pytest (38 new this session) · 449 vitest
(12 new) · tsc · no new ruff/mypy · import contracts kept.

## 8. Settled corrections → burst review (operator-directed, `main`)

Operator: "include any in the burst and/or manual review to ensure they
have been executed properly." Burst review chosen (it IS the
did-everything-execute surface; the manual queue is the settlement
worker's lane).

- `GET /v1/bet-corrections`: last 7 days of settled stake/odds edits
  (before snapshot terminal; tag-only skipped) + outcome reclasses with
  their mandatory reason, newest first, each carrying the bet's CURRENT
  derived P&L — the executed-properly proof, recomputed on read.
- Burst review section (e) "Settled corrections — last 7 days",
  read-only, between banked credits and the watchdog list.
- LIVE FIND on first read: a pre-S237 bet_edited payload carries
  match_status; the strict typed parse 500'd the list. Forensic reads
  now go row-level with tolerant JSON access (+ regression test
  seeding the exact legacy shape).
- Live proof: the section's newest row is the REAL S254 Sarie
  correction ($10→$13 @ TAB, lost, P&L now $0.00 — FB stake, zero cash
  impact, exactly as S254 recorded).
- Deployed with a restart (~08:30); gates 1900 pytest / 451 vitest.

## 9. Clean exit (operator feedback, shipped + live-proven)

"Every time I click the bethub icon, it opens. When I exit it,
everything closes (including the terminal window)."

- Nav gains **Exit** (inline confirm) → `POST /api/shutdown` → the app
  SIGTERMs itself → uvicorn graceful shutdown (workers + stream) → the
  launcher's wait/trap cleanup frees port + money-store lock → the
  launcher closes its OWN Terminal window (tty-matched, Terminal.app
  only; a real failure keeps the window open with the error visible).
  Farewell screen replaces the app.
- Ctrl-C and closing the window remain clean stops and now also close
  the window; a crash (unexpected uvicorn exit code) keeps it open.
- Second click on the icon while BetHub runs: opens the browser to the
  running app and its transient window closes — no more FATAL
  already-running message (F10 one-server rule unchanged).
- Live proof: POST /api/shutdown took the whole launcher down (lock
  freed, port released, all processes gone); relaunched clean.
  Window-close arm is Terminal.app-only so the operator's first real
  double-click → Exit run is the final visual check.

## 10. Review sweep + P&L breakdown (operator-directed)

- Sweep: pending 0 · manual queue 0 · source-pending 0 · unpaired 0.
  Credit gaps 35 → 24 dismissed via the tool's own
  confident-ran-outside rules; 11 held back — race results genuinely
  absent (likely the trial-flag class; tonight's re-pull fills them,
  re-sweep after — any 2nd/3rd finisher is owed a credit).
- P&L breakdown filed: `pl_breakdown_s256.md`. Total +$1,750.32 (293
  settled bets since 18 Jul), reconciles to the cent with
  /v1/cash-flow/pnl (self-check passing). Insurance +$1,425.84 over
  157 cycles ≈ 81% of profit; bonus-winnings +$304.11/15 cycles;
  no-promo +$20.37/37 — the edge is the promo, matching S252/S253.
  Kate @ CrownBet (−$265, 0/9) the only cold line; Betfair −$29.68 =
  hedging cost, netted inside cycles.

## 11. Cent-truth fix — 1-cent banner class CURED (`e3baa43`, live)

Diagnosis refined from §5.1: commission was ALREADY cent-true per
market (0g shares + rebate cancellation). The real leaks were the other
derivation edges carrying 4dp: a lost lay's liability (stake×(price−1))
debited unrounded forever, won-back stake×price products, FB
winnings×conversion. Betfair and the books keep cent ledgers. Fix:
quantize those three edges ROUND_HALF_UP (4 red-first tests;
1905 pytest green; nothing relied on the fractions).

Live proof: pre-deploy read-only recompute moved derived Tim@Betfair
2644.34 → 2644.334 vs real 2644.33; post-restart on-demand watchdog
pass against the REAL account: flags [], gap −0.00, clean true —
banner gone. Residual ~0.4c sits inside per-line rounding-direction
ambiguity; if it ever crosses a cent the watchdog re-flags and R3
names the line. Operator steps required: none (restart done in
sitting).

## 12. CLOSE (28 Jul ~09:30) — S257 queue

S256 shipped, all live on v3 main `e3baa43` (capture `3496816`):
trial-guard, 0j + credit door, Saturday feedback batch, settled
stake-edit completion, stream-ladder fix, corrections review, clean
exit, cent-truth fix. P&L breakdown filed (`pl_breakdown_s256.md`);
review surfaces cleared bar the 11 results-absent gap rows.

**S257 queue (operator-directed at close):**
1. **FIRST ACTION — TAB odds-lag review (feedback item 7, "still lags
   ~10s"): investigation + EXECUTIVE SUMMARY REPORT ONLY. Assess
   possible improvements INCLUDING whether an increased Decodo
   subscription would help. NO EDITS until the operator confirms.**
   (Context: S250 transport work targeted faster; live feed rides the
   VPS Decodo path; cycle-3 lead-lag research in
   race-price-pressure/cycle3_tab_leadlag has the cadence numbers.)
2. Session-open standing checks + re-sweep the 11 credit-gap rows
   (results fill overnight; 2nd/3rd finishers are owed credits —
   operator checks the book, then credit-in).
3. Available anytime: current_state.md refresh; BetLog.test.tsx
   mock-hygiene sweep; Keychron instructions.
4. Sat 1 Aug sitting unchanged (live proofs, first live reassign,
   Take-SP stage 0, sweep §4 acceptance, 3 parked panel checks).
5. Operator: BetRight ≥8 template (day next used); PF cancel check.
