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
