# VPS Hardening — Day-3 Deploy Report (S241, Wed 15 Jul 2026, 07:11–07:55 ACST)

Contract: `vps_hardening_brief.md` v3, Day-3 slot (item 8b). Pre-racing constraint honoured
(first real race 11:55 ACST; deploy window closed 07:55).

## What landed

1. **Identity sweep timer ENABLED + first run** (`racing-identity-sweep.timer`,
   05:50/10:20/15:20 ACST, Persistent=true). First run 07:13: 77 WIN / 76 PLACE markets →
   77 race identities, updated=45 inserted=32 twin=0 adopted=0 collisions=0, 799 runners,
   63 scratched, page-cap alarm silent, 8s wall clock.
   **Acceptance verified:** 77/77 today's races carry win market ids, 76/77 place ids
   (one WIN market has no PLACE market on Betfair), 77/77 racing_code stamped, zero
   duplicate market-id fragments, collector keepAlive undisturbed (no session/auth noise).

2. **Collector RESTARTED on W7 code** (`6ea50aa`, PID 667542, 07:14). Immediately visible:
   discovery for **2026-07-15** (venue-local AU day — old code would say 14 Jul at that UTC
   hour), per-event-type pagination, types 7 only (dogs stay OFF until tonight's 22:03 W7c
   swap; `INCLUDE_GREYHOUNDS` absent from .env → default off).
   **30-min watch CLEAN:** 6 samples, active throughout, 0 errors/tracebacks; normal phase
   transitions + half-hour discovery cycle (308 new races, 89 active).

3. **W2 wired** (commits `656264f` + `27442fe`, VPS=Mac=GitHub):
   - **Bookmaker-staleness book-id gate:** staleness only evaluated when ≥1 in-window race
     carries a bookmaker race id. Kills the 14-Jul evening family (8 alerts, night harness,
     zero book ids).
   - **Stamped-coverage check:** every bookmaker-known AU race jumping ≤2h must carry a
     Betfair identity (win market id + ≥1 runner selection id), ANY twin fragment satisfies
     (candidacy — book ids, AU state — is group-level too), collision-valve suffixes
     stripped in grouping, trials excluded by venue list (`lark hill`).
   - Tests: 30 liveness tests (19 old + 11 new) → after refinement 33; full repo suite
     **75 green** on Mac AND on the box.

## Live catch + rule amendment (governance note)

First live run of stamped-coverage flagged 11 "Muswellbrook" races (sportsbet-only ids,
15-min cadence from 09:00 AEST, no class, no Betfair markets). Diagnosis: **barrier-trial
card listed by sportsbet with the trial label stripped by discovery** — is_trial=0 on all
rows (the flag-unreliability the brief §W2 warned about, in the opposite direction).
Left alone: a false alarm every 15 min all trial-morning.

**Amendment to the brief's pinned candidate set:** sportsbet-ONLY races are not coverage
candidates (≥2 books, or a single non-sportsbet book, still are). Evidence: last 30 days,
1,104/1,111 single-book AU rows are sportsbet-only and only 53/1,104 (4.8%) ever gained a
Betfair market. **Accepted residual:** ~2/day genuinely sportsbet-only real races go
unwatched by this one check. Reversal is one HAVING clause.

Post-amendment live run: exit 0, "No candidate races in the coverage window" (trial card
screened; real races enter the 2h window from ~09:55 and are already sweep-stamped).

## S240 watch-item CLOSED: bookmaker snapshots resumed

32 bookmaker snapshots since restart (sportsbet, Muswellbrook card in window). The 14-Jul
evening "stall" was confirmed no-eligible-races lull, not a fetcher fault. Multi-book flow
(ladbrokes/neds/tab…) confirms naturally from ~11:00 ACST real races — 11:23 alert-watch
tick checks this.

## Rollback

`/root/hardening_rollback_day3/`: deployed SHA + pre-restart collector SHA (`90f4810` —
restart on this to revert) + systemd unit tarball. DB backup 05:02 this morning verified
(keep-2 rotation working).

## Follow-ups (named, for Fri close-out)

- `health_check.py` exits 1 after a SUCCESSFUL send when issues detected → unit shows
  "failed" (tripped this morning's open; cosmetic, email arrived fine — 6am heartbeat now
  lands in gmail INBOX per W1).
- `reset_alert_counter()` touches the cooldown file on every healthy run → first alert
  after a healthy run can be suppressed ≤30 min (pre-existing S238 behaviour, cosmetic).
- W2 stamped-coverage acceptance tail: zero-false-alarm soak runs through today
  (alert-watch ticks); red-on-synthetic-gap covered by unit tests
  (`test_missing_market_id_is_red`, catalogue-truncation shape).
- Venue-alias fragmentation ("Albion" vs "Albion Park") remains open (known, pre-reset).

## Post-deploy incident (11:23 tick, RESOLVED 11:57 — 10 min before first jump)

Stamped-coverage alerts 10:30 + 11:15 ACST on Eagle Farm/Balaklava (real meetings). The
tripwire earned its keep on day one — two real defects found and fixed under standing
authority (`a4bf6dd`, 76 tests green, VPS=Mac=GitHub):

1. **10:20 sweep DIED: Betfair `TOO_MUCH_DATA` (ANGX-0001)** on the greyhound catalogue.
   `PAGE_SIZE=200` ignores Betfair's response-WEIGHT cap: RUNNER_METADATA(2) +
   MARKET_DESCRIPTION(1) = 3 points/market vs a 200-point limit → >66 markets/page
   errors. Morning runs passed only because few markets were listed that early. Fix:
   PAGE_SIZE 60, MAX_PAGES 50 (same 3,000-market ceiling). Re-run: SWEEP COMPLETE,
   1,947 runners, twin=45 adopted=97, done 02:26:35 UTC — first race 02:36.
2. **Coverage twin key split UTC twins**: legacy rows store the UTC day, new-code rows
   the venue-local day → date-keyed grouping counted one race as two, inflating the gap
   count. Fix: twin key = (venue, race number) only — cannot collide inside a 2h window.
   Regression test added (`test_utc_twin_with_split_race_date_is_one_race`).

Post-fix liveness: "All 17 candidate races Betfair-stamped", all checks passed. Note the
alert was HALF-true (sweep failure real, count inflated) — exactly the failure class the
check exists to catch; zero-false-alarm soak restarts today.

## 22:03 slot (item 8d): dist live, dogs flag set — dogs capture starts 08:30 Thu

App-idle verified (no processes, zero in-flight bets). The W7c frontend build was already
in the served `ui/web/dist` (built 15:14 while the app was closed — no running-app hazard);
next app launch serves the new picker. Rollback: rebuild from `51b62f7`-era frontend via git.

VPS: `.env` rollback copy staged, `INCLUDE_GREYHOUNDS=1` appended, collector restarted —
and it exited cleanly by DESIGN: "Past stop hour (19:00 Adelaide) and no active races".
The collector is a daily session (start timer 08:30 ACST; runs past 19:00 only while races
are active); a fresh post-19:00 start exits before discovery, so late-evening dog races
can't be picked up tonight (they were never captured pre-flip either — no regression).
**Dogs event type 4339 goes live at Thu 08:30 auto-start** (timer verified NEXT=23:00 UTC);
acceptance check scheduled 08:47 Thu (discovery line includes 4339, dog races gain market
ids + snapshots). Old process was tracking 0 races at restart — nothing dropped.

Learning for the brief: "collector restart" steps scheduled after 19:00 ACST must expect
the stop-hour exit; the flag flip still lands (env read at next start).

## Identity drill (item 8e, Thu 06:05–06:10 ACST) — PASSED

Abort gate: first jump 10:09 ACST, ~4h clear. Collector in designed overnight-off state
(= the drill's "stopped pre-first-race" precondition).

- 05:50 timer sweep green: inserted=34 (early dog listings), adopted=9, collisions=0.
- **Every Betfair-listed race stamped:** 73/73 market-bearing rows for today carry
  win market id + racing_code (39 T + 34 G; harness lists later in the day — code path
  already proven live yesterday, twin=45 Albion Park day). 744 runners stamped.
- **Idempotence + never-overwrite (acceptance #3):** sweep run twice; second run
  inserted=0 adopted=0 twin=0 collision=0; full identity diff over 551 rows
  (15–16 Jul: id|win|place|code) = EMPTY; total races 98,606 unchanged.
- **Fragment audit:** zero duplicate market-id fragments for today. The
  swept-then-collected = ONE fragment half completes naturally after the 08:30 collector
  start — folded into the 08:47 dogs-live check.
- **Red-before note (honest):** the "absent from picker pre-sweep" red state was not
  synthetically re-created (the 05:50 timer beat the drill window by design); it is
  evidenced by yesterday's LIVE red→green cycle instead (10:20 sweep failure → stamped
  10 min pre-jump, stamped-coverage alert red then green). Accepted as satisfied.
- Session proof (#7): collector keepAlive across sweep runs proven Wed (three sweeps
  under a live collector, zero session noise).

## Dogs-live acceptance (Thu 08:47 ACST) — PASSED

1. Collector auto-started 08:30:35 on the daily timer, active, no errors.
2. Discovery line: **"Betfair discovery: 136 WIN, 136 PLACE markets (types 7,4339)"** —
   greyhounds live in the catalogue call; bookmaker discovery normal (430 new races,
   186 active; tabtouch 44 venues).
3. **97 greyhound races for today, 97/97 with win market ids**; zero duplicate
   market-id fragments → the collector did NOT double-insert sweep-stamped races —
   this also completes the identity drill's "swept-then-collected = ONE fragment" half.
   Dog price snapshots 0 at check time — timing-normal: today's first race overall IS a
   greyhound (10:09 ACST); capture window opens ~09:10. 09:23 tick verifies first dog
   snapshots; full §3.5 dog-day proof (prices/BSP/volume/picker latency) at the 10:33
   drill slot and through the day.
4. 05:50 sweep green (drill section above).
   Note: 294 NULL-code rows today = bookmaker-side rows (incl. 44 tabtouch venues, many
   never Betfair-listed); all market-bearing rows are code-stamped — NULLs are the
   expected non-Betfair tail, not a gap.

## Overnight 15→16 Jul: collector operating-window cry-wolf — FIXED (09:23 tick)

9 "Collector process not found" alerts 22:30–08:15 overnight: the liveness watcher
treated the collector's DESIGNED daily-session shutdown (clean stop-hour exit; timer
restart 08:30) as a failure, and W3 burned both self-heal restarts fighting it — each
restart exited cleanly again by design. No capture was lost (nothing left to capture).
Silver lining: the restart-cap "NEEDS HANDS" path (acceptance #2's alert wording)
demonstrated itself live.

Fix (`568239f` + test fix `f47da9b`, VPS=Mac=GitHub, 84 tests green both machines):
collector-alive + data-freshness checks now apply only inside the collector's operating
day (08:25–19:00 Adelaide) OR at any hour when its last exit was NOT clean — an
overnight CRASH still alerts and self-heals; the designed exit no longer does.
Stamped-coverage + API checks stay active around the clock during racing hours (a
pre-08:30 morning card still needs stamps + reads). Live-proven: liveness run exits 0,
"All checks passed". W3 restart budget for today (UTC-keyed) is untouched — the 10:33
kill drill has its full 2-restart allowance.

## Kill drill + cap + page-cap + dog-day (item 8f, Thu 10:33–11:35) — ALL PASSED

**Kill drill (acceptance #1) ✓:** collector stopped 10:34 ACST → liveness detected 10:45
(streak 1; first alert suppressed once by the known cooldown-touch quirk) → 11:00 run:
streak 2 → **W3 auto-restart succeeded** + gmail alert with "AUTO-RESTART #1 attempted
(streak 2)" (26 min from kill — well inside ≤75) → 11:15 **RACING RECOVERED** notice →
snapshots fresh, streak reset 0, `.liveness_restarts` = 2026-07-16 1. Drill cost:
~26 min of price snapshots on a quiet mid-morning card, as budgeted.

**Restart-cap negative test (acceptance #2) ✓ via live evidence:** overnight 15→16 Jul
the cap path ran for real — 2 restarts burned, subsequent failures sent "NEEDS HANDS:
restart cap (2/day) reached", no third restart attempted. Unit tests cover the state
machine; not re-staged mid-racing-day (would cost another hour of capture for a
duplicate proof).

**Page-cap truncation alarm (acceptance #6) ✓ synthetic:** new `tests/test_page_cap.py`
(`751d8c0`) — endless-full-pages source trips `hit_page_cap` at exactly MAX_PAGES;
draining source doesn't. Sweep alarm wiring (capped → truncation alert email) verified
present. 86 tests green Mac + box.

**Dog-day measurements (acceptance #5, first natural dog day):**
- 211 market-bearing races stamped today: **143 greyhound / 39 thoroughbred / 29
  harness** — dogs ≈ 2/3 of the card, matching the brief's 2× volume prediction.
- **Discovery hit 208 WIN markets — past the old 200-market single-call cliff.** The
  pre-W7 unpaginated code would have silently truncated TODAY's card. Concrete live
  justification for pagination + the sweep's 60/page weight fix.
- Dog price snapshots flowing (442 by mid-morning; first race of the day was a dog).
- DB 4,325 MB (+~29 MB over 2 days so far); disk steady 36%. Full-day dog delta reads
  at Friday close-out. Picker latency re-measure: next operator app session.

Follow-up (cosmetic): RECOVERED email body reuses the failure template header.

## State at close

VPS=Mac=GitHub `27442fe`. Timer schedule next: sweep 10:20 + 15:20, W7c build 15:03,
dist swap + dogs-live 22:03 (app-idle-checked). Liveness timer running new code every 15m.
