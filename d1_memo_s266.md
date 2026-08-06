# D1 NUMBERS MEMO — Call reliability (S266, 4 Aug 2026) — PART 1

Protocol: `d1_preregistration_s266.md`, written and frozen before any
query. Deviations are named as DEVIATIONS below.

**Status: 4 of 6 fits complete.** §1f (bar re-derivation) and §1b-ii
(Harville by field size) are outstanding and are NOT reported here.
Nothing in this memo enters D2 until it has been adversarially
reviewed, per the plan.

**Data.** The frozen 3 Aug capture backup (never the live database —
the collector was mid-card). 313,661 runner-snapshots → 298,954 after
hygiene, over 8,757 Betfair markets, 6 Apr – 3 Aug 2026. Twin rows
deduped by market id (8,978 duplicate rows dropped); 3,311 rows with
no market id excluded; trials, scratched runners, `sp_near =
'Infinity'` strings and ≥900 prices excluded.
Out-of-time split as pre-registered: fit ≤ 30 Jun, all headline
figures reported on 1 Jul – 3 Aug (~36k held-out points per horizon,
far above the 200 minimum).

---

## FINDING 0 — the plan's premise about the incumbent was WRONG

Amendment 1 states the incumbent projection is "the S252-corrected
shrunken tilt `mid × (sp_near/mid)^β`, β ≈ 0.10–0.18".

**It is not. That shrink was recommended in S252 and never shipped.**
`raceWatcher.ts:319` substitutes `sp_near` for best back wholesale:

```ts
bfBack: isLate ? r.bfBack ?? 0 : r.spNear ?? r.bfBack ?? 0
```

There is no exponent anywhere in `ui/web/src/ev/`. So the live tool
runs **β = 1** outside the late window and **β = 0** (no projection)
inside `LATE_WINDOW_MIN`. Amendment 1's "do not remove the
substitution without fixture proof" fence still stands and is
honoured — nothing here removes it; it is shrunk.

Consequence: D1 is not tuning a shrink that exists. It is fitting one
that was specified, agreed, and then never built. Every LEAVE the
tool has ever produced came from a full-strength substitution.

## FINDING 1 (§1c) — β is far below 1 at every horizon

Fit on ≤30 Jun, scored on held-out 1 Jul – 3 Aug. Loss = squared
error in log price vs realised BSP; race-clustered standard errors.

| horizon | β | se | MSE at β | MSE at live setting | improvement |
|---|---|---|---|---|---|
| T−60..30m | **0.382** | 0.008 | 0.2706 | 0.3756 (β=1) | **+27.9%** |
| T−30..10m | **0.393** | 0.008 | 0.2251 | 0.3325 (β=1) | **+32.3%** |
| T−10..3m  | **0.150** | 0.012 | 0.1050 | 0.1604 (β=1) | **+34.5%** |
| T−3..0m   | 0.167 | 0.023 | 0.0630 | 0.0638 (β=0) | +1.3% |

β is stable across the split (0.382→0.397, 0.393→0.405, 0.167→0.146);
only T−10..3m moves materially (0.150→0.208).

Two readings that matter:

1. **Shrinking the tilt cuts projection error by about a third** in
   the three windows where the tool actually projects. This is the
   single largest measured improvement available to the Call.
2. **The late-window rule is already right.** Inside T−3 the tool
   projects nothing, and the best fitted β buys 1.3%. Leave it alone.

The late-window β (0.15–0.17) lands inside S252's 0.10–0.18 range,
which is coherent: S252 fit near the jump.

**Exploratory (declared, not pre-specified — 12 comparisons):** β is
strongly meeting-type dependent. METRO ≈ 0.05–0.10, PROVINCIAL ≈
0.14–0.38, COUNTRY ≈ 0.16–0.43. Out-of-time, a meeting-specific β
beats the horizon-only β by 6–10% MSE on METRO and ~0% elsewhere.
Interpretation is cleaner than the constant: **at metro meetings the
live book is already the best BSP estimate and `sp_near` adds
nothing.** Recommend D2 ships horizon-only β; the metro rule is a
candidate for a later pass, not a blocker.

## FINDING 2 (§1d) — depth imbalance is DEAD once the tilt is shrunk

Pre-registered test: after the fitted β, does size imbalance explain
what the projection misses? Mapping learned on the fit window,
agreement measured out-of-time.

| horizon | n (oot) | corr(residual, imbalance) | directional agreement | base rate |
|---|---|---|---|---|
| T−60..30m | 35,965 | 0.028 | 51.0% | 53.2% |
| T−30..10m | 36,200 | 0.015 | 50.0% | 50.4% |
| T−10..3m  | 35,479 | 0.053 | 52.1% | 51.1% |
| T−3..0m   | 33,713 | 0.057 | 53.0% | 54.9% |

Agreement is **at or below the base rate in three of four horizons**,
and adding an imbalance term changes MSE in the fourth decimal.

The S265 study was not wrong — lay-heavy books do shorten — but the
signal is already inside `sp_near`, and once the tilt is shrunk
properly there is nothing left. **Recommendation: drop the
depth-imbalance input entirely**, including as a veto (amendment 1
provided for veto-only; it does not clear even that bar). This also
closes the pressure-dot question permanently: there is no measured
content to display.

## FINDING 3 (§1e) — a click-time execution gate is not viable

Distributions over the same universe. Spread = (lay − back) / back.

| horizon | n | no lay side | median spread | p90 spread | spread > 10% | best-lay depth < $50 |
|---|---|---|---|---|---|---|
| T−60..30m | 77,532 | 0.1% | 91.5% | 572.7% | 92.1% | 98.2% |
| T−30..10m | 77,556 | 0.1% | 50.0% | 366.7% | 77.7% | 98.0% |
| T−10..3m  | 75,657 | 0.1% | 10.0% | 54.5% | 49.5% | 94.4% |
| T−3..0m   | 69,846 | 0.1% | 5.9% | 25.0% | 27.7% | 87.5% |

By price band (all horizons): median spread 7.8% under 3.0, rising to
36.8% at 30+; over 10% on 46% of sub-3.0 rows and 82% of 30+ rows.

**A gate keyed on click-time spread or depth would fire on 78–92% of
runners outside the last ten minutes.** A gate that fires on almost
everything is not a gate. This is the S252 lesson landing again:
liquidity bites through execution, and the execution path in question
is not click-time at all — Take-SP (`MARKET_ON_CLOSE`) has been the
default since S263, so the hedge fills at SP, not at the ladder you
can see.

**Recommendation, revising amendment 3's shape (not its intent):** do
not build a click-time gate. Model the free-bet conversion leg at
SP-lay economics, which is what actually happens, and keep an
EV floor only for the last-three-minute window where the visible book
is real. Amendment 3's substance — an EV floor, never an automatic
LEAVE — is preserved.

## FINDING 4 (§1a) — the free-bet conversion rate

Re-measured on the current record under read rules R1–R8.

- **Face-weighted conversion: 70.4%**, 95% bootstrap CI **[67.3%,
  72.8%]**, 85 settled deployed free bets, $3,804.50 face consumed.
- Identical excluding book "freebies" (unprompted credits with no
  qualifying bet): 70.4%, CI [67.1%, 72.9%], n=80.
- **The engine's 65.0% is outside the CI.** Amendment 9's 70.2% is
  inside it.

**Recommendation: set `DEFAULT_FB_CONVERSION_RATE` to 0.70.** This
raises every free-bet EV the screen shows; the tool has been
systematically pessimistic on free-bet conversions.

**Reproduction honesty (DEVIATION).** The pre-registration required
reproducing `promo_cycle_analytics_reference_s265.md` §2 exactly.
8 of 11 cells reproduce to the cent. Three do not:

- PointsBet Ins $25 FB 2nd — face $75 vs $50 (new deploys since the
  reference was written).
- CrownBet Ins $50 2+3 — 61.0% vs 56.6% on the same $325–350 face.
- TAB Ins $50 2+3 — 70.9% vs 70.2%.

Plus $260 of face the reference's per-template table does not carry at
all: book **freebie** credits (9 credits with no template, 8 with no
qualifying bet). Those are correctly absent from a per-template table
and correctly present in an engine constant.

The first pass of this measurement produced a 141% Neds cell — the
exact pathology R6 warns about — caused by summing multiple
`free_bet_deployed` events for one bet. Two live cases exist:
`bet-56de667f` (genuine $40 + $22.50 co-funding) and `bet-3b84ec36`
(two $50 credits, one $50 economic face — the R4 void-and-restore
shape). Fix: face = the deployed bet's matched stake, capped by the
draws; draws set apportionment weights only.

**The headline is robust to the unresolved cells** — every variant
tried lands at 70.4–71.6%, and 65% is outside all of them. The three
cells should still be chased before the per-book numbers are quoted
anywhere.

## FINDING 5 (§1b-i) — small-field insurance terms: CLOSED, immaterial

Operator ruling 4 Aug: terms clauses are not implemented (the primary
insurance books pay 2nd and 3rd at any field size); a statistical
error would be. Determination: `position_min_field` is purely a terms
clause (`evEngine.ts:302`), so the terms branch closes.

Bounded exposure check: BetRight is the only book with a known ≤7
exclusion. It has 14 bets on 2+3 templates, and **0 on fields of 7 or
fewer** among those with a recorded field size. Caveat: 10 of the 14
carry no `field_size_at_placement`, so the true count is 0 of 4
known. Immaterial. Not raised again.

§1b-ii (does Harville misprice the 2nd/3rd trigger chance in small
fields?) is the branch the operator asked to be embedded if real. It
is **not yet run** — it needs place BSP from the Data Portal daily
files.

---

## Still outstanding before this memo goes to review

1. **§1b-ii** — Harville trigger-chance error by field-size bucket
   (≤7, 8–10, 11–13, 14+) vs place BSP. Material if any bucket's
   median error > 1.0pt or > $0.50 per $50 promo.
2. **§1f** — EXECUTE_BAR re-derivation, which per amendment 9 and 15
   must run on the CORRECTED stamp (0.70 conversion) and re-banded
   history, not the current one.
3. **§6** — coverage: the 109 ungraded racing-screen cash backs.

## What this implies for D2 (proposals, not decisions)

- Ship the shrunken tilt at the fitted per-horizon β; leave the
  late-window rule untouched.
- Drop depth imbalance entirely; no pressure dot.
- No click-time execution gate; model the conversion leg at SP-lay
  economics.
- `DEFAULT_FB_CONVERSION_RATE` → 0.70 before any threshold tuning.
- Expect the shrink to REDUCE the number of LEAVEs shown: a
  full-strength substitution produces more extreme projected prices
  than the data supports. The LEAVE bar itself must therefore be
  re-derived after the shrink lands, not before.
