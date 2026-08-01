# SESSION 257 — 28 Jul 2026 (midday sitting)

Operator-directed: TAB odds-lag review → full build ("Proceed. Run an
implementation review after to confirm rigour."). Also session-open
standing checks and the S256 queue items.

## 1. Session open — standing checks

- VPS health: all clear (disk 39%, collector running, 520 races).
- RACING ALERTs (27/28 Jul overnight): false alarms — TAB "frozen"
  window was overnight foreign racing (Gavea) that TAB doesn't carry
  ("last snapshot never" = nothing to snapshot; malformed
  `meetings/R//races/9` URL noted, orchestrator handles it gracefully).
  TAB + TABtouch verified flowing to the minute. Data API timeout at
  23:45 was a one-off; tunnel up. Nothing fixed, nothing needed.

## 2. Credit-gap re-sweep (S256 queue item 2) — CLEARED, nothing owed

Overnight results filled all 11 held-back rows (all Randwick Sat 25
Jul — the trial-flag repair worked; is_trial=0, finish positions
present). Every runner finished 5th or worse — NO 2nd/3rd finishers, so
no credits owed and nothing for the operator to check at the book. The
11 rows dismissed via `record_credit_gap_dismissal` (same reversible
display-layer marker as S256's 24). Credit-gap surface now 0 live rows.

## 3. 1-cent Betfair banner — looked at (2 min), then operator confirmed
the tool now handles it. (Morning money check showed funds-total gap
−$0.01, 0 lines checked; the S256-predicted sub-cent rounding tail
crossing the visible line. Watchdog runs only through the live app's
Betfair client — S248 standing decision, no parallel logins.)

## 4. TAB lag review v2 (report: `tab_lag_review_s257.md`)

Operator added the key fact: lag varies ~10s to OVER A MINUTE.
Measured decomposition (Saturday 25 Jul data: 4,792 UI reads, ~2,900
live fetches, 1,062 real reprices; scripts in
`bethub-analytical/race-price-pressure/cycle3_tab_leadlag/code/s257_lag_review/`):

- Live feed (when active): median display age 4.1s, p99 8.5s, ZERO
  failures/stalls all day. Actual poll cadence 8.3s (designed 7 — the
  clock anchored on fetch completion, adding fetch duration).
- The minute-plus mode: the T-30m live-window gate. Outside it the
  column silently rode the background capture feed — 5-min snapshots
  (~1¾-min inside the final 5m intensive window) — and didn't mark
  "stale" until 10 min. Only mechanism found that produces >1min.
- TAB publishes each reprice 32–40s (p95 ~87s) after its own
  returnWinTime stamp — feed-wide, app included (inference: the
  operator's ~10s observation only adds up on a shared feed). Floor
  nobody outside TAB beats.
- Decodo: bigger subscription buys NOTHING (traffic megabytes/day;
  latency lives elsewhere). Operator told to skip.
- Fill-odds freeze trap found in the morning's f8089df feature: one
  click marked EVERY runner operator-owned → froze the whole card's TAB
  updates AND hid the staleness stamp.

## 5. Build (operator: "Proceed") — all six measures + review fixes

**capture `b7c282f`** (deployed VPS via direct git push — the VPS repo
has no GitHub remote; also pushed to github/master):
- Measure 4: refresher cadence clock anchors at fetch START (8.3→7s).
- Measure 6: two Decodo sessions ("live"/"live-b") rotate → fresh
  pickup every 3.5s final-window. A MODULE-GLOBAL claim registry
  enforces the 7s per-session floor structurally (single gated
  fetch_tab call site): cold-start inline fetches, cooldown expiries,
  multiple open markets can never double-tap a session inside the
  floor. Transport block → bench 900s (burns don't heal in minutes;
  short cooldowns re-run the on-thread hunt every breaker cycle). 404
  (TabRaceNotFound) → clean empty, NEVER a bench (S250 lesson), and
  remembered per-market 120s so a not-on-TAB race stops burning claims.
  Third idle cadence tier (30s at UI gap ≥8s) for all-day polling.
- live_pools_hot 503 → inline serves the refresher's cached copy.

**v3 `8b6a2e8`** (pushed origin; dist rebuilt — next app launch serves it):
- Measure 1: live feed runs whenever the race page is open (gate
  removed; jump distance only picks cadence 1s/5s/15s; early-CLOSED
  market stops it, transient pre-jump SUSPEND doesn't).
- Measure 2: fill-odds owns only the runners it fills; rest released to
  the feed (+ fills join the ownership sweep even if the prices feed
  blinked). Button tooltip updated.
- Measure 3: background stale bound 10min→2min. Review fix: an EMPTY
  live payload no longer asserts freshness (it could pin the stale
  clock to "now" forever for a race TAB doesn't carry).
- Measure 5: 1s final-window screen reads.

## 6. Implementation review (operator-directed) — 2 reviewers + verifier

Round 1 (two independent adversarial agents): 7 capture-side findings
(cold-start double-tap, bench/hunt stall economics, cooldown-expiry
double-tap, per-refresher-only floor, unpinned measure-4 gating, 404
misbench, cache-fresh coupling) + 6 v3-side (empty-live staleness
masking MAJOR, all-day traffic shape MAJOR-operational, fill transient
blank, fill union hole, comment rot, missing cadence pins). ALL
confirmed findings fixed except two consciously accepted: fill-click
transient blank (seconds, cosmetic) and the first-block hunt stall
(inline path now carries the feed during hunts; async hunts out of
scope). Round 2 (verifier with revert-simulation): all prior findings
traced CLOSED; caught the drift-guard test threshold being too lenient
(revert escaped 3/3 — tightened 5→6, now discriminates 7-vs-5 starts)
and the not-on-TAB claim burn (fixed, memo above). Verdict: DEPLOY.
Accepted-as-minor: second-market bootstrap contention (transient,
degrades honestly), bench-on-breaker-fail-fast (masked by all-benched
fallback), 0.25s hot-retry resolve cost, cold-start two-session burst.

## 7. Live proof (Swan Hill R3, T-15m, 28 Jul ~13:15)

22/22 polls at 2s → 200 with 20 runners, real odds. Fetch log spacing
3.5–3.7s effective — sub-7s is only possible with both sessions
rotating (registry refuses otherwise), each at ~7.1s ≥ floor. Post-
deploy VPS health: all clear.

Gates: capture 198 pytest (12 new); v3 459 vitest (8 new), tsc, build.

## 8b. Post-ship operator check: "22s gap" — CONFIRMED AS THE FEED'S CEILING

Operator stopwatched ~22s app→tool on the afternoon session (Swan Hill
R3, new frontend confirmed live — 1–1.5s UI reads, 3.6s fetch cadence).
Measured: 13 real reprices, stamp→our-feed delay median 20.9s (IQR
13.6–29.6), ZERO reprices landed inside a poll gap — faster polling
finds nothing. Edge-TTL probe (S250 lever 3, finally run; production
transport shape, 3 requests): Akamai edge max-age 1–10s only,
cache-buster returns IDENTICAL stamps, ETags regenerate within seconds
while stamps stay old → **the ~21s is TAB's ORIGIN publication pipeline
(internal store lags the desk), not edge cache, not us.** Our chain
share is ~2–3s. On this feed ~15–25s behind the app IS the ceiling.
Only path past it: whatever channel the native app rides — needs a
phone-traffic look (operator-assisted; Pi gateway can mitm), plus a
side-by-side vs tab.com.au WEBSITE (S249: site polls this same API — if
the site lags like us, the app has a privileged channel). Probe script:
VPS /tmp/edge_probe2.py.
**CLOSED same day, operator confirmation:** the tab.com.au WEBSITE race
page lags the same way — fresh prices only appear when the BET SLIP
re-quotes on click. The ~20s display delay is TAB's intentional
anti-scanner design; the public display feed (site, and our tool) is as
fresh as TAB shows anyone, and the slip delivers the real price at
placement. No app-channel pursuit — thread closed. Tool is at the
public-display ceiling: ~2–3s behind the feed, ~20s behind the desk.

## 8c. Second 1-cent Betfair banner — same class, now precisely located

Watchdog today: 1 line checked, sub-cent trued (+0.00 booked), but the
FUNDS gap re-flagged at TWO balances (2644.33, 2117.72), both −0.01 —
a STANDING offset, not drift. Full precision: derived cash 2117.728 =
+0.8c above the cent-precision account. It's the S256 residue class
(pre-fence historical lines' sub-cent leftovers; new lines are trued).
It will keep flashing ±0.01 until either (a) a one-time audited
"ledger residue" alignment event books the 0.8c away + the watchdog
gains the same fence at funds level (auto-book ≤1c residue, R3-named,
books once per crossing — matches the self-serve-fixes feedback), or
(b) we accept the banner. Also noted: derived cash carries float noise
(2117.72799999…) — a Decimal-hygiene pass in the derivation sum path
would make the residue exact. NOT built — proposed to operator.

## 8d. Betfair 1-cent — ROOT-CAUSED, fix BUILT (`9cbc61b`), run pending quiet moment

Operator asked why not reconcile from Betfair's own numbers → answer:
the tool DOES, daily, line-by-line (double-entry is the alarm — the
$23.21/$29.67 precedents); proposed a one-time historical line sweep.
Operator approved subject to a design review. **Review verdict:
APPROPRIATE-WITH-CHANGES and the sweep was aimed at the wrong target:**
the 0.8c residue is TWO STRAY TRUINGS the watchdog itself booked
(+0.004 on 22 + 28 Jul, reproduced to the last digit) — after S256
fenced the balance derivation, `derived_line_gross` stayed unquantized
and "corrected" already-exact lines (active daily bug; a stray booked
at 13:23 today is direct proof). Running my sweep pre-fix would have
booked MORE strays.

Built (`9cbc61b`, 1,912 pytest): (1) `derived_line_gross` now lands on
the same `_cent` fence (regression tests replay the real 79.79 @
7.600000000000001 shape); (2) `ops.reverse_watchdog_truing` —
supervised, append-only, exact-mirror (float tail included → pair nets
zero), idempotent, watchdog-truings-only, dry-run default. The correct
21-Jul truing (−0.01, `8f83ac26…`) is LEFT ALONE; reverse only
`a15119d1-0711-4600-82f0-748318d33e69` and
`9e6419f2-ee57-4210-824d-80c24b49289a`.

**EXECUTED (operator closed app, ~15:0x):** both reversals dry-run then
booked — `4a457fec-d296-4f0c-9795-d66dbf9c4c6d` (−0.004) and
`e21a18a4-9d7e-4e05-a347-c8f8ed8b47ba` (−0.00400000000007979);
idempotency re-proven live (second --execute refused). Derived cash
2117.71999999999983696 → **2117.72 on the cent** (residual −1.6e-13 =
the predicted bet-69054a3f float tail, quantizes to 0.00). Operator
relaunch activates the fenced compare; next money check should read
gap 0.00. Optional proof pass still open: watchdog route
`?dry_run=true` day loop 9 Jul→today after relaunch, expect zero.
Facts for the record: line-truing auto-book cap is 5c (not sub-cent);
markers survive reversal (reversed lines never auto-re-book); float
noise rides stored REAL matched_price — broader Decimal price hygiene
is separate, larger work, not needed for convergence.

## 8e. Afternoon close-out (operator: "proceed with items completable now")

- **Betfair history proof pass RUN (read-only, via the live app):**
  20 days (9–28 Jul), 76 settled lines — 55 exact matches, 20
  unmatched all pre-18-Jul (before the tool's first tracked Betfair
  bet; inside the opening baseline), 1 silently skipped = the
  already-trued 21-Jul line. **Zero corrections needed. Ledger proven
  line-by-line against Betfair.** Operator confirmed balance matches
  in-tool after the reversals + relaunch.
- **Keychron hot buttons:** `keychron_hot_buttons.md` written (VIA
  macros → Ctrl+Opt+Cmd+digit → macOS Shortcuts "Open App"; ~15-min
  operator setup; per-AdsPower-profile keys scoped OUT, offer stands).
- **current_state.md refreshed** (was S245-stale) — S258 required-reads
  updated.
- **BetLog.test.tsx mock hygiene DONE (`3c9434c`):** clearAllMocks
  before defaults — factory vi.fn() implementations leaked across
  tests (restoreAllMocks only touches spies). 46/46 pass unchanged =
  nothing relied on the leakage. Full vitest suite green.
- Subagent review judged unnecessary for these four: read-only pass,
  two docs, and a test-only change gated by the full suite — none can
  reach production behavior.

## 8. Left open / queue

- Operator eyeball next sitting: TAB column side-by-side vs the app
  (expect ~4–6s finals); note any minute-plus sighting (race + time)
  for a one-pull confirm of the background-feed explanation.
- Sat 1 Aug sitting unchanged (live proofs, first live reassign,
  Take-SP stage 0, sweep §4 acceptance, 3 parked panel checks).
- Anytime: current_state.md refresh, BetLog.test.tsx mock hygiene,
  Keychron steps. Operator: BetRight ≥8 template, PF cancel check.
- Known-accepted: fill-click transient blank; first-block hunt stall
  (queue async-hunt if it ever bites); ~0.4c watchdog tail class
  (superseded §8d: class CURED — fence + reversals + proof pass).

## 9. CLOSE (28 Jul 15:27 ACST)

Session closed per `bethub-session-close`. v3 main `3c9434c`; capture
`b7c282f` (VPS + GitHub); suites 1912 pytest / 459 vitest + tsc +
build; nothing uncommitted in either repo. **Sat 1 Aug live batch
DEFERRED — operator away, no betting expected; moves intact to the next
operator race day (likely Sat 8 Aug).** `current_state.md`,
`v3_build_picture.md` (catch-up block S246→S257) and the memory index
all rotated to this close. **S258 first action (operator-confirmed):
high-level overview of recommended next steps — auto-executes, report
only, no edits.** Opening prompt:
`.close_out_backups/SESSION_258_opening_prompt.md`.
