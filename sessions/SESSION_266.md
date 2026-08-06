# SESSION 266 — 4 Aug 2026 (Call program D1: run, rejected, rebuilt)

**One-line summary:** D1 ran, was rejected by three independent reviews,
was rebuilt, and its rebuild failed its own mid-point gate. Zero analysis
shipped. What DID ship: a capture extension recovering five discarded
Betfair fields, a latent schema bug fixed, and five months of Betfair
BSP/jump-time/place data recovered from a lapsed import.

## Standing checks (open)

VPS health all clear (collector running, capture fresh, backups 12h,
527 races). SIM gateway lane 3001 (Kate) dropped 09:16, self-recovered,
healthcheck clean on re-run. 3 Aug Betfair-stale alerts cleared.

## Operator decisions taken (do not re-litigate)

1. **STRONG and MOD carry the SAME stake.** Tiers collapse to FIRE/LEAVE
   for staking. Rationale: operator bets promo maximum anyway, and the
   record cannot separate the tiers at feasible n. LEAVE-override ≤ half
   stake remains the only stake rule.
2. **Race-row mock: all three answers accepted as recommended** — row
   order kept (verdict adjacent to the controls); lay-health tint on the
   row, reason in words at arming, not per-row; trend arrow kept but only
   on a material move.
3. **Pressure dot: OUT.** (Evidence base later weakened — see D1 review
   B3 — but the recommendation stands on the separate ground that a tail
   signal belongs in the engine, not on screen.)
4. **`DEFAULT_FB_CONVERSION_RATE` STAYS AT 0.65.** Operator: prefers a
   slightly conservative figure. Binding consequence: §1f must fit the
   bar against 0.65, the same value the screen uses.
5. **Small-field TERMS clause: closed permanently.** It is a book-terms
   matter and the primary insurance books pay 2nd/3rd at any field size.
   The STATISTICAL branch (Harville by field size) stays open and is now
   unblocked by the place-BSP import.

## D1 v1 — RUN AND REJECTED

Pre-registration `d1_preregistration_s266.md` written before any query.
Memo `d1_memo_s266.md`. Both retained as the record of what failed.

Findings claimed: β ≈ 0.38/0.39/0.15/0.17 with 28–35% MSE improvement;
depth imbalance dead; click-time lay gate not viable; FB conversion
70.4%; small-field immaterial.

**Three adversarial reviews, three separate serious failures, none
overlapping:**

- **Code & data truth — PARTIAL.** The historical claim survived (the
  S252 shrink was never built; one commit to `raceWatcher.ts`, never
  modified). But the memo's description of the live path was WRONG:
  `evEngine.ts:196` applies `Math.sqrt(bfBack * bfLay)`, so the
  projection is a geometric blend of `sp_near` with the LIVE lay —
  effectively β≈0.5 in log space — firing on 62–97% of rows. `β = 1`
  was a straw incumbent. Also `LATE_WINDOW_MIN = 2`, not 3.
  **Caught a real forward bug:** shipping `mid × (sp_near/mid)^β` as
  specified would have compounded TWO shrinks.
  Re-measured against the true path the recommendation still holds at
  +22–31%.
- **Statistician — REJECT.** The fit universe was ~61% greyhound and
  harness; the operator bets 93% thoroughbred, 71% metro. On the
  operator's metro tracks the recommended β is **worse than no
  projection** (−6.6% MSE in both mid-windows). The "out-of-time" split
  was a composition change (greyhound 0% → 52.9%), not a time test. The
  imbalance kill inverts under a clustered test (t = 4.3–5.3 on
  thoroughbreds; none was ever run) and used top-of-book where ladder
  depth existed. The lay-usability kill collapses on the real decision
  set. 13 undeclared protocol deviations. Amendments 17–28 issued.
- **Money & consequence — AMEND-FIRST.** Arithmetic reproduced exactly;
  the QUANTITY was wrong. The engine constant multiplies expected
  CREDITED face; the memo measured cash per dollar DEPLOYED, excluding
  expiry/revocation/never-placed leakage. Corrected ≈ 67.4%
  [63.4, 70.7] — **0.65 is inside that CI.** Also: the proposed package
  would dissolve **67–92% of LEAVE**, and every dissolved LEAVE becomes
  a FIRE (LEAVE requires `evNow ≥ bar AND evProjected < bar`; shrinking
  β collapses that band). Exposure −$65 to −$130/wk. Also found the S265
  reference table itself double-counts a restored credit.

**Adjudication of the one disagreement:** statistician said ship 0.70,
money review said 0.65 is inside the CI. Money review wins — it checked
what was being measured, not just whether the sum was right. Moot in any
case: operator has fixed the constant at 0.65.

## D1 v2 — REBUILT, GATE 1 FAILED

`d1_preregistration_v2_s266.md`. Adds STAGING (Stage A population →
Gate 1 → Stage B fits → Gate 2), a contradiction-escalation rule (v1's
own metro estimate contradicted its recommendation and was filed as
future work), and a review mandate that **re-running the analyst's
scripts is not verification — headlines must be independently
re-derived**. That distinction is exactly what separated the review that
found the real error from the one that confirmed everything.

Stage A: `d1_stageA_population_s266.md`. **Gate 1 verdict: FAIL**, 12
conditions. Key catches:

- The `track_condition` thoroughbred classifier was validated on a label
  set that is **0% of the fit window** — `racing_code` is populated on
  no race before 1 July. Circular.
- Sufficiency counted runner-snapshots. In the registered unit (decision
  points) **metro fails: 196 held-out races < 200**; at meeting-day
  level, 32.
- A1.4's repair clause was skipped: **464 metro thoroughbred races
  (+71%) and 43 meeting-days were recoverable** and the protocol
  required doing that BEFORE fitting.
- Universe not restricted to Australia — **35 "metro" races are in
  Minnesota** (Canterbury Park conflated with Canterbury, Sydney).
- Within metro the composition mismatch REPEATS: Perth is 22% of the
  data and 1.5% of the operator's betting; Randwick + Caulfield are 29%
  of his metro decisions and hold 2 held-out meeting-days.
- The A1.4 funnel mixed two date filters and was non-monotonic.
- Hedge-stake item RESOLVED (not open): the disputed $7.21 is
  `bet_legs.matched_stake` **including 38 zero rows** — a bug artefact.
  `bet_legs.matched_stake` is a stale denormalised copy (62 of 86
  disagree with the bet row) and must not be used. **Better instrument
  found: 86 real hedge attempts — 79 full, 5 partial, 2 failed (8.1%
  non-fill).** Observed, bet-time truth; replaces the whole click-time
  depth threshold exercise.

## OPERATOR CHALLENGE → DATA RECOVERED

Operator challenged the five-month window ("we've been capturing for
months and have a racing API with 12 months"). Correct challenge.

Found: **`betfair_historical`, 163,809 rows, Mar 2025 – Feb 2026** —
Betfair's monthly `ANZ_Thoroughbreds_YYYY_MM.csv` files, already
imported, with BSP, place BSP, **actual off times** and race class.
**The import had lapsed since February.**

Ran it for **2026-03 → 2026-07** (August not yet published) via
`scripts/import_betfair_historical.py` into a WORKING COPY
(`/root/d1/work.db`), not the live DB — race day, deploy armed.
Result: **7,140 thoroughbred markets, ~69,200 BSP rows**, 96.6% matched.

Three problems it solves at once: definitive thoroughbred identity (kills
the circular classifier), actual jump times (the reviewer called these
unavailable anywhere), and place BSP (unblocks §1b-ii).

Metro usable sample 657 → **715 races / 90 meeting-days**. Modest,
because the binding constraint is NOT BSP — **345 of 1,060 metro
thoroughbred races have a settled price but no `sp_near` capture from
us.**

**Hard ceiling, recorded:** `sp_near` capture begins April 2026. It is a
live-only figure and is NOT in the free BSP files. Nothing recovers the
run-up before then.

**Betfair paid data:** BASIC free = 1-min intervals, last traded price
only, no volume, no ladder → almost certainly insufficient. ADVANCED =
1s + top-3 ladder + volume; PRO = 50ms + full ladder. **No published
pricing for AU customers** — quote via automation@betfair.com.au. Not
contacted (operator's name, operator's call).

## SHIPPED — capture extension (built, tested, NOT deployed)

Five fields arriving in the `EX_ALL_OFFERS` + `SP_AVAILABLE` responses we
already pay for, discarded at parse time:

- **`sp_back_stake_taken` / `sp_lay_liability`** — the SP pool. `sp_near`
  is DERIVED from this money. Without it there is no way to distinguish a
  projection standing on $40k from one on $200 — the explanatory variable
  for the entire β question, never recorded.
- **`last_price_traded`** — the time of the last trade was kept, the
  price was not.
- **`adjustment_factor` / `removal_date`** — the late-scratching
  deduction Betfair applies to bets ALREADY PLACED. Real money off the
  operator's bets, never captured.
- **Order book 3 → 10 levels.** `EX_ALL_OFFERS` returns the full ladder
  at no extra weight; the parser kept three rungs. Both S266 reviews
  wanted ladder depth and had to use top-of-book.

Files: `betfair/models.py`, `betfair/client.py` (+`DEPTH_LEVELS`,
`_sum_price_sizes`, `_iso`), `storage/database.py`,
`storage/racing_day.py` (`ensure_snapshot_enrichment_schema` — additive,
nullable, O(1), safe with the collector writing), `capture/orchestrator.py`,
`scripts/morning_sweep.py` (second writer — updated AND now ensures schema
itself, per the codebase's own both-writers convention).
Tests: `tests/test_snapshot_enrichment.py` (9 new). **576 pass.**

**Latent bug found and fixed:** `bsp_price` was never in the schema of
record — it existed only via an `ALTER TABLE` inside
`import_betfair_historical.py`. A database built fresh by `init_db`
lacked it and the first snapshot write raised "no such column".
Invisible in production only because the live DB went through that
import. `tests/test_twin_merge.py` carried a hand-written workaround
adding the column, with a comment saying the schema lacked it — someone
hit this before and patched around it. Workaround removed.

**SHIPPED 5 Aug 07:48 ACST — see below. (Originally held back deliberately:)** Phase 1 deploy loop 8 fires 22:55 4 Aug
(fallback 04:35 proven). Two changes in one deploy makes a failure
ambiguous, and Phase 1 has already burned seven attempts. Working tree
uncommitted; ready to commit + ship once Phase 1 lands healthy.

## STRATEGIC POSITION (agreed with operator)

The Call program's own ceiling: a PERFECT jump-time Call ≈ 2–3% of
turnover vs the ~21% the promos deliver. Against that, D1 has consumed a
full session and four review rounds with every quantitative claim
retracted.

**Agreed: finish D1 properly but TIMEBOX it to one sitting on the new
data foundation.** If it does not produce a metro number that clears its
own adoption bar, take the cheap version — stamp honesty, full coverage
(every fired bet carries a Call), respect LEAVE, stop tuning the
projection — and move to higher-value worklist items.

Likely outcome flagged in advance: metro may be unanswerable, in which
case the honest answer is **"at metro meetings the market is already
right; the Call should not project at all"** — simpler than any constant
and free to implement.

## INCIDENT — deploy loop 9 failed mid-flight, collector down 2h16m

**Timeline (ACST):**
- 22:55 4 Aug — loop 8 fires. **Attempt 1 refused: "too close to the
  top/bottom of the hour (22:55) — deploy between :10 and :45".** The
  loop was scheduled at a minute its own guard forbids. From 23:45 the
  overnight repair/backup window blocked everything else. Exhausted at
  01:55 with **249 refusals across all loops and zero successes ever.**
- 01:40 5 Aug — armed loop 9 at **04:35** (the S265-proven slot: after
  the 04:30 window, at :35 past the hour, no AU racing).
- 04:35 — **dry run CLEARED for the first time ever.** Real deploy ran:
  `git checkout master` (→ 9d86480) succeeded, then
  `migrate_intl_venue_keys.py --force-preflight` **REFUSED at
  preflight**: *"342 non-AU row(s) carry a Betfair market id — the
  rekey set must be disjoint from the twin repair's market-keyed merge
  set. STOP and wait for repair-zero."*
- Collector restarted into the NEW code with no rekey marker → refused
  to boot by design (lock 2, `racing_day.py:782`). **DOWN 04:35–06:51.**

**Diagnosis before acting:** the migration refused at PREFLIGHT, before
moving any key. Its only writes were two additive nullable columns
(`jurisdiction_config.betfair_event_types`, `venue_country.is_alias`) —
harmless and ignored by the old code. `schema_meta` carries no rekey
marker. **No half-moved state existed**, so no reverse migration was
needed or run.

**Resolution:** rolled the code back rather than forcing past the guard.
The refusal protects against re-minting the DR-036 twin class that took
multiple sessions to clear — forcing it was the wrong trade.
`git checkout s260-resilience` (cb4e026, the commit running since
31 Jul; its `assert_identity_ready` returns early when only AU is
enabled, so it boots). Collector active, discovery running for 5 Aug,
bookmaker snapshots writing within a minute, `ops.vps_health` all clear,
no deploy timer left armed.

**THE REAL FINDING — Phase 1 is blocked on DATA, not on deploy timing.**
Eight loops chased a scheduling problem. The first time a dry run
cleared, the deploy revealed the actual blocker: **342 non-AU rows carry
a Betfair market id and overlap the twin repair's merge set.** Phase 1
cannot land until that set is repaired to zero. No amount of
rescheduling would ever have worked.

**Two fixes owed:**
1. The loop must refuse to ARM at a time its own guard would reject
   (22:55 violates the :10–:45 rule). Eight loops, eight days, one
   two-line preflight.
2. Drive the 342 non-AU market-id rows to zero (0m / twin-repair family)
   before re-attempting Phase 1.

## SHIPPED — capture extension LIVE 5 Aug 07:48 ACST

Could not ride Phase 1 (Phase 1 is blocked on data, not timing), so it
shipped standalone — correctly, since it is independent and additive.

**Critical deploy detail:** local `master` carries all the 0p Phase 1
international commits, i.e. exactly the code that took the collector
down at 04:35. Deploying from master would have re-broken it. The change
was therefore cherry-picked onto **`s260-resilience`** (cb4e026, the
running code) as branch **`s266-snapshot-enrichment`** (`939cb78`),
tested on THAT base (**460 pass**), pushed to `origin` (which is the VPS
itself — `ssh://root@187.77.183.9/home/racing/racing-data-capture`),
checked out, collector restarted 07:48.

Verified: migration ran (`added betfair_snapshots.removal_date` et al),
all six columns present (`last_price_traded`, `sp_back_stake_taken`,
`sp_lay_liability`, `adjustment_factor`, `removal_date`, `bsp_price`),
collector booted clean, discovery running for 5 Aug, 71 WIN markets.

**LIVE PROOF STILL OWED.** Zero Betfair snapshots had been written since
the restart when the session closed (exchange capture starts near the
jump; first AU race ~10:00). The fields are deployed and unit-tested but
**not yet proven to populate with real values**. First job next session:
confirm `sp_back_stake_taken` / `last_price_traded` are non-null on real
rows and that `back_depth_json` now carries more than 3 levels.

**Master still holds the same commit (`1601707`) for whenever Phase 1
lands** — the two branches must be reconciled at that point, not before.

## HANDOFF — S267 does these FIRST

1. **Deploy**: confirm loop 8 landed (22:55 4 Aug; fallback 04:35 5 Aug;
   count-based watcher — FAILED marker carries NO timestamp). Then push
   capture master → ff VPS → merge `s265-1a-phase0` + `s265-0y`
   (racing-api restart only) → Gate B → GB flip → drop
   `BETHUB_RACING_COUNTRIES=AU` → Gate C (operator GB promo bet).
2. **Ship the capture extension** immediately after Phase 1 is healthy —
   every day undeployed is SP-pool data that cannot be recovered.
   Uncommitted in `racing-data-capture` working tree; 576 tests green.
3. **Merge the historical import into the live DB** in a quiet window
   (`/root/d1/work.db` proves it; re-run against `capture.db`), and put
   the monthly import on a schedule so it cannot lapse again.
4. **Stage A REBUILD** on the imported foundation — rebuilt, not patched:
   4–5 of Gate 1's 12 conditions disappear when Betfair's own
   thoroughbred file is the authority. Then Gate 1 again, then Stage B,
   then the full Gate 2 round.
5. **Live proofs still outstanding** from S265: first settle-up batch to
   the cent, strip/Results eyeball, auto-bank first bonus win, Take-SP
   first fill.

Operator actions pending: app bounce (Phase 3 + 0y wiring on screen),
Gate C bet, $14.21 exchange recheck when flat, decision on whether to
request a Betfair ADVANCED/PRO quote.
