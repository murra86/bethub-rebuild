# SESSION 267 — 5 Aug 2026 (data day: the import, and the Phase 1 blocker)

**One-line summary:** The Betfair historical import was rebuilt so it
cannot lapse silently again, run into the live database and scheduled;
and the 342 rows blocking the Phase 1 deploy turned out to be Australian
races wearing a wrong country stamp, which was corrected at the root.
The Phase 1 disjointness count is now zero.

Operator scoped the session to **data work**. The Betfair ADVANCED/PRO
paid-tier quote is **explicitly left alone** — do not re-raise unprompted.

## Standing checks (open)

VPS health all clear — collector running, capture fresh, backups 3h,
overnight sweep ran (attempted 113, walled 39), disk 44%. The RACING
ALERT burst of 4 Aug 19:30–21:15 UTC was the failed Phase 1 deploy and
its recovery; nothing new since 21:15 UTC.

## 1. Betfair historical import — fixed, run, scheduled, alarm proven

Commit `3a9a142` on `s266-snapshot-enrichment`. Note `origin` IS the VPS.

**The lapse had TWO hardcoded ceilings, not one.** `DOWNLOAD_FILES`
stopped at 2026-02 **and** `--to-date` defaulted to 2026-03-31. Neither
could ever raise: a month that is never requested is indistinguishable
from a month with no data, and a 404 was only a warning. Both are now
derived from the calendar and the file list extends itself.

`check_coverage()` interrogates the **database** — which months hold rows
— rather than the download, so it catches a lapse however it happened.
A required month with zero rows emails via `liveness_check.send_alert`
and exits non-zero. The current month is exempt (Betfair publishes after
month end), which is why the timer fires three times a month.

**Both paths proven live, not asserted:**
- gap path — two months removed in a scratch copy → exit 1 and
  "RACING ALERT (Betfair history): 2 month(s) missing" delivered 08:44;
- clean path — `systemctl start racing-betfair-import.service` → exit 0,
  "No gaps", no email.

**Result in the live DB:** 17 unbroken months, Mar 2025 – Jul 2026,
**232,980 rows** (+69,171). Place BSP on 99.8%, actual off time on
99.99%. The new months match far better than the old — 91.9% on
market_id against 0%, unmatched 1.6% against 14.9% — because the 2026
CSVs carry the win market id and our races now hold it too.

Schedule: `racing-betfair-import.timer`, 5th/12th/19th 04:45 Adelaide,
`Persistent=true`, IO-idle, ~90s per run. Import is append-only into
`betfair_historical` with INSERT OR IGNORE on (market_id, selection_id),
so a re-run is a no-op and a killed run costs nothing.

**Trap recorded for whoever joins these tables next:**
`races.betfair_win_market_id` is the API form (`1.254584358`);
`betfair_historical.bf_win_market_id` is the CSV form (`240124447`).
They never join — 0 of 16,863. The link is race_id/runner_id from the
matcher. Any market-id join between the two is meaningless.

## 2. The Phase 1 blocker was a data bug — and the guard was RIGHT

Commit `af18787`.

0p Phase 1's rekey refused on its §3.3 disjointness proof: 342 non-AU
rows carried a Betfair market id. **Every one was an AUSTRALIAN race
with a wrong country stamp.** Had the guard not held, the rekey would
have written `bathurst|gb` onto NSW country and harness races and
`canterbury|us` onto Sydney metro races — into the venue **identity
key**, which is the expensive kind to undo.

**Evidence (independent re-derivation, per the S266 process lesson):**

- **Bathurst** — 396 rows, all stamped GB. No British racecourse of that
  name exists. 114 carry state NSW, 46 carry racing_code harness, 271
  are meeting_type COUNTRY. Jumps run 13:00–21:00 Sydney; the Doncaster
  GB control runs 22:00–03:00. Nothing resembles a British card.
- **Canterbury** — a REAL collision. `normalise_venue` strips "Park", so
  Sydney's Canterbury and Minnesota's Canterbury Park share the key
  `canterbury`, and the venue genuinely is both. The Minnesota races
  jump 04:00–07:00 Sydney. 187 rows carry NSW state AND an 11:00–17:00
  jump, matching the 7 correctly-stamped AU rows and the Flemington
  control — two independent signals agreeing.

**Root cause, two mechanisms combining:**
1. every country write is fill-if-null, so the first value to land is
   permanent and nothing downstream ever revisits it;
2. `recompute_venue_country` learns a venue only when its rows AGREE,
   which cannot distinguish uniformly-wrong from uniformly-right —
   Bathurst was 396-for-396 wrong, was learned, and was then backfilled
   across the venue.

**Fix.** All three write paths — `fill_country_if_null`,
`recompute_venue_country`, `backfill_country_from_venue_table` — now
refuse a non-AU country on a row carrying an Australian state code.
Both cannot be true and the combination is free to detect. Contradictions
leave the column NULL, which the §5.1 order already reads as "not known
yet" rather than as an answer. `liveness_check` gains a 7-day
contradiction check for a route we have not thought of.

`scripts/correct_country_stamps.py` corrected 396 + 187 = 583 rows,
journalled with pre-images in `country_stamp_fixes`, with `--reverse`.
Bathurst wholesale; Canterbury only where two signals agree. **143 rows
carrying NSW-with-US were deliberately NOT corrected** — nothing resolves
them, and the code's own rule is that a wrong country is worse than none.
All are historical; zero in the last 7 days, so the new check passes.

**RESULT: the Phase 1 disjointness count is ZERO. The deploy unblocks
with no change to the safety guard.**

Suite 501 green (was 460): +19 coverage tests, +22 contradiction tests.

## 3. Correction to an S266 belief — "wait for repair-zero" was unreachable

S266 owed "drive the 342 to zero before re-attempting" and framed it as
waiting for the twin repair. **Repair-zero was never going to arrive.**
The 679 remaining twin markets ARE the permanently-refused 0m population
(540 identity-gate + 139 settled-audit), unchanged since 31 Jul; the
nightly repair now completes in ~4s against 54s on the night it cleared
the backlog. Phase 1 was not waiting on a queue to drain — it was waiting
on a data bug, which is now fixed.

## 4. The Call column — checked, no change made

Operator asked, before racing, that the Call be working as well as
possible given S266's findings. Checked; **no live bug**. S266's review
corrected the memo's DESCRIPTION of the code, not the code: the
projection has always been a geometric blend of `sp_near` with the live
lay (`evEngine.ts` `estimateTrueOdds`), and `LATE_WINDOW_MIN` has always
been 2. `raceWatcher` tests 10/10; served build current (08:08, no
source newer, no unmerged branches).

Two findings worth keeping:

1. **The grade is display-only.** STRONG and MOD render as different
   pills and nothing else — no stake, no action, no code path. With the
   S266 decision that they carry the same stake, the entire trust gate is
   currently money-inert. The only Call output that changes a decision is
   LEAVE, and LEAVE exists solely because the projection moves the
   number (`evNow ≥ bar AND evProjected < bar`).
2. **On the operator's own population the Call structurally cannot say
   STRONG about 60% of the time.** Measured over 30 days of AU metro
   thoroughbreds, 135 races with a snapshot inside the 15-minute window:
   market formation passes 98.5%, pool coherence 81.5%, but the $50k
   volume floor passes only **44.4%**; all three 40.0%. So MOD-not-STRONG
   usually means "thin pool", not "weaker bet".

**Nothing changed.** The only lever that moves FIRE vs LEAVE is the
projection, which was rejected twice and is timeboxed to one dedicated
sitting; tuning the volume floor would change a word on screen and no
money. Operator was offered a FIRE/LEAVE display collapse and a
"MOD · thin pool" reason chip, and chose to **leave the display exactly
as is** before racing.

**The D1 unlock:** D1 failed because the fit universe was ~61% greyhound
and harness while the operator bets 93% thoroughbred and 71% metro —
there was no way to test the projection on his own population. Today's
import removes that: settled BSP for every AU thoroughbred race across 17
months means the next sitting can ask the question directly on metro
thoroughbreds instead of on a proxy.

## HANDOFF — S268

1. **Phase 1 deploy.** Blocker cleared; nothing in the data refuses it
   now. Confirm disjointness is still zero at deploy time, then
   Gate B → drop `BETHUB_RACING_COUNTRIES=AU` → Gate C (operator GB
   promo bet). Note the loop-arming defect S266 owed is still open: the
   deploy loop must refuse to ARM at a time its own guard forbids.
2. **SP-pool live proof** — the last piece of the S266 capture
   extension. Depth is PROVEN (7–10 levels against the old cap of 3) and
   `adjustment_factor` fills 607/607, but `sp_back_stake_taken` /
   `sp_lay_liability` were 0/607 because the nearest snapshot sat 194
   minutes from the jump and an SP pool is empty that far out. Check on a
   near-jump snapshot.
3. **Stage A REBUILD** on the imported foundation, then Gate 1, Stage B,
   Gate 2.
4. **D1's one remaining sitting** — now answerable on the operator's own
   population. If metro does not clear its own adoption bar, take the
   cheap version and move on.
5. **S265 live proofs still outstanding**: first settle-up batch to the
   cent, strip/Results eyeball, auto-bank first bonus win, Take-SP first
   fill.
6. **0m** — the 679 refused twins; nothing else will clear them.

---

# S267 AFTERNOON — race-day work (5 Aug)

## 5. Places on the day — SHIPPED AND PROVEN

**Cause found:** finishing positions come from The Racing API on a job
that ran ONCE A NIGHT (20:00 UTC / 05:30 Adelaide). Betfair gave the
winner near-live; everything else waited for the overnight sync. That is
the whole reason the Results page showed places the next morning.

`racing-intraday-results.timer` — 15:00/19:00/22:30 Adelaide, `--days 1`
(RECENT path only; the heavy backlog trickle stays gated on the argless
invocation). Three passes not ten: the provider tightened rate limits
~29 Jun and each pass re-fetches the full card.

**PROVEN LIVE 15:01:** today went from **0 finishing positions** to
**214, with 44 runners marked PLACED**. Covers thoroughbred meetings only
(the feed's scope); dogs/harness still wait for the overnight pass.

## 6. Betfair place market — BUILT, NOT DEPLOYED (`s267-place-only`)

`_check_settlement` only ever polled the WIN market, so `PLACED` could
only come from the subscription. In a Betfair PLACE market the
place-getters settle as WINNER — same call, market id we already hold.
No new provider, no scraping.

**Measured settlement lag, live, 4 races:** Bendigo win 2.4 min / place
2.4; Doomben 3.1 / 5.4; Q1 Lakeside 1.7 / **14.8**. So places land 2–15
min after the jump — fast enough for insurance triggering, and no
external site would beat it. **Known limit, documented in code:** the
read is one-shot, so a race whose place market lags past its win
settlement gets no places here and falls back to the intraday pass.

## 7. Exacta ordering — BUILT THEN REVERTED (adversarial review)

Operator's idea, and it decodes correctly: an EXACTA runner is named by
saddlecloth pair ("6 - 3" = 6 first, 3 second). Verified live at Hobart
against the win and place markets. Betfair AU runs EXACTA (39) and
QUINELLA (39) but **no trifecta or first-four**; "4 TBP" four-place
markets exist. Coverage looked like 2nd/3rd on 60%, 4th on 55%.

**KILLED by review, and it was right.** `get_sibling_markets` resolved
siblings by `event_ids`, but **a Betfair event is a MEETING, not a
race** — this repo already knows it (`race_matcher.py:396` buckets place
markets by event, `:530` disambiguates by `start_time`). On a multi-race
meeting every exacta collapsed onto one dict key, so it could resolve to
another race's result. The cross-check only validated the WINNER, so
when two races shared a winning saddlecloth it would write a wrong 2nd —
and `finish_position` is COALESCE-guarded, so **the error could never be
corrected**, not even by the overnight feed.

Second blocker: the retry loop leaned on `has_timed_out()`, which
measures from SCHEDULED START, not from when the wait began — a race
with a future start time and a closed market would poll indefinitely
(~1,400 calls). Third: eight of my own tests passed for the wrong reason
(bare `mock.Mock()` made `win_settled` truthy, so the guarded path never
ran).

**Do not re-attempt** without: sibling resolution by `market_start_time`
keyed per market id, a wait-scoped deadline, and jitter on
`should_check_settlement`.

## 8. Race-screen rework — BUILT (`s267-race-row`, 9 commits, UNMERGED)

The S265 mock's three approved answers had never been built; operator
noticed nothing was on screen. Four columns removed (Matched, Raw EV,
BF Close, Trend) with their jobs moved to hovers; lay-health tint;
trend reduced to one glyph on a ≥2% move. S250's TAB drift-since-open
PRESERVED on the arrow's hover.

Live-screen fixes after operator screenshots: **column misalignment**
(headers left behind when cells were removed — Actions rendered under
BF CLOSE, my error, live mid-race-day); lay tint firing on EVERY row
(top-of-book depth is not available money — ratio only now); single-line
rows; number/marker in separate fixed slots so columns align; roomier
rows; LOG + ⚡ side by side; **Promo EV shows the straight number** with
the ⚠ retained (relaxes S231's band); **raw EV shown when no promo is
armed**, header renames; **scratchings sort to the bottom**.

## 9. Betting analysis (operator asked: "am I doing anything wrong?")

**No.** 1–5 Aug, 158 back bets: **38 wins against 37.8 expected** —
exactly on the prices. Saturday +1.4 sd (lucky), 2–5 Aug −1.8 sd
(unlucky), combined level. Stake per bet flat, volume DOWN after the bad
run — no chasing.

Money: Sat **+$1,575.76**, since **−$1,388.31**, five days **+$187.45**.

**Structural cause of the swing:** insurance pays on 2nd/3rd, winnings-
bonus pays only on a win. 67 insurance bets Saturday → 0 on the 3rd and
4th. Free bets earned: Sat $1,109 face, since $275/$0/$43/$82. Without
insurance every loss is a total loss and variance roughly doubles.

**FREE-BET CONVERSION MEASURED FOR THE FIRST TIME: 0.947** across 88
settled free-bet placements ($3,868 face → $3,662 returned), CI
[0.40, 1.59]. The engine assumes **0.65**. So every promo EV on screen
is UNDERSTATED. `realised_conversion_rate` is NULL on every row — the
tool never records this; it had to be reconstructed.

**TAB 25% winnings bonus:** 57 bets, −$883.61, but the 95% CI on return
is **[−65%, +5%] of stake** and wins are 1.5 sd light. Verdict: keep
taking them; the data cannot distinguish a bad promo from a cold run.

## 10. Calibration by racing code — the answer to "should I bet dogs?"

30,000 runners, 3,758 settled races, price inside 5 min of the jump,
de-vigged, vs actual winners:

| code | runners | predicted | actual | bias |
|---|---|---|---|---|
| thoroughbred | 5,021 | 500.0 | 500 | +0.00 pts |
| **greyhound** | 17,660 | 2,478.0 | 2,478 | **+0.00 pts** |
| harness | 6,888 | 763.0 | 763 | +0.00 pts |

**Greyhounds are the best-calibrated of the three** (tightest CI, holds
across every decile). **My earlier advice to cut dogs was WRONG** — it
rested on a thin-market argument that S253 had already disproved on
52,101 runners (liquidity interaction −0.001). Harness has one soft
spot: **44.5% predicted → 32.9% actual on 161 runners** — be wary under
about $2.50.

## 11. Other findings

- **SP pool: NOT our bug.** Direct probe — Betfair returns
  `back_stake_taken=[]` while sending valid near/far prices. Four of the
  five S266 capture fields work (last traded price, adjustment factor,
  removal date, 10-level depth); the SP pool is simply not served.
- **Take-SP:** operator confirms it works. **Cannot be corroborated** —
  the persistence type (MARKET_ON_CLOSE vs limit) is stored NOWHERE.
  One-column fix, worth doing so the next proof is checkable.
- **$14.21 exchange recheck:** Betfair flat at $1,697.05, zero exposure,
  but the tool still had 1 bet pending — reconcile when it clears.

## HANDOFF — S268 (supersedes the earlier list)

1. **04:40 deploy** (armed, 19:10 UTC 5 Aug). Confirm it landed, capture
   healthy → Gate B → drop `BETHUB_RACING_COUNTRIES=AU` → Gate C.
2. **Merge/deploy `s267-place-only`** AFTER Phase 1 is verified.
3. **Merge `s267-race-row`** (9 commits) — operator is running it from a
   local build, so a rebuild from main would lose it. Ask whether to keep.
4. **`s267-0m-prep`** — `--reverse` + `--report` built and tested; the
   evidence run says only **11 of 369** clears rest on the disqualified
   s3-only signal. Cleanup on a quiet weekday, in batches.
5. Stage A rebuild; deploy-scheduler fix or retirement.
6. **Record `realised_conversion_rate`** and the lay persistence type —
   two small gaps that make live proofs unanswerable after the fact.
