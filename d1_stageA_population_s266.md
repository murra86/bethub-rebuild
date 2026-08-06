# D1 v2 — STAGE A: POPULATION REPORT (S266, 4 Aug 2026)

Deliverable A1 of `d1_preregistration_v2_s266.md`. **No hypothesis
testing.** This answers only: what is in the analysis data, what does the
operator bet, and do they overlap. Stage B (the fits) is blocked until
this clears Review Gate 1.

Source: frozen capture backup `capture_20260803.db` (read-only,
immutable) + the operator's bet record (`bethub.db`, read-only).

---

## A1.1a — Racing-code classifier, validated

`races.racing_code` is stored on only **3,605 of the 9,159** BSP-carrying
races (39%), and on only ~4% of all captured races — so the code must be
inferred. Marker used: **`track_condition` is present iff thoroughbred**
(it is a thoroughbred-only concept; harness and greyhound rows never
carry it). Secondary markers: `venue_normalised` suffixes
(`|greyhound`, `|harness`, `|thoroughbred`).

Validated against the 3,605 labelled races:

| metric | value |
|---|---|
| thoroughbred recall | 512 / 512 = **100.0%** |
| thoroughbred precision | 512 / 517 = **99.0%** |
| false positives | 5 |
| false negatives | 0 |
| **error rate carried into every thoroughbred figure below** | **0.14%** |

Cross-check on the residual: races the classifier calls non-thoroughbred
carry `distance_metres` on **1 of 2,517**, and their venues are Albion
Park (306), Redcliffe (215), Menangle (181), Globe Derby (105), Melton
(104) — harness and greyhound tracks. The residual is not
mis-classified thoroughbred; it is non-thoroughbred whose code was never
stored.

## A1.1b — Composition of the analysis universe

Races carrying a realised BSP, 9,159 total:

| code | METRO | PROVINCIAL | COUNTRY | total | share |
|---|---:|---:|---:|---:|---:|
| **thoroughbred** | **657** | 797 | 2,095 | **3,549** | **38.7%** |
| greyhound | 69 | 266 | 2,035 | 2,370 | 25.9% |
| harness | 0 | 55 | 668 | 723 | 7.9% |
| non-thoroughbred, code unstored | 7 | 319 | 2,191 | 2,517 | 27.5% |

**61.3% of the analysis universe is not thoroughbred.** v1 fitted a
single constant across all of it and recommended it for the operator's
metro thoroughbred betting.

## A1.1c — Composition by window: the v1 "out-of-time test" was not one

| code | fit window (≤30 Jun) | report window (>30 Jun) |
|---|---:|---:|
| thoroughbred | 2,556 (**54.6%**) | 993 (**22.2%**) |
| greyhound | 0 (0.0%) | 2,370 (52.9%) |
| harness | 0 (0.0%) | 723 (16.1%) |
| non-thoroughbred (unstored) | 2,123 (45.4%) | 394 (8.8%) |

Greyhound goes from **0% to 52.9%** across the split; thoroughbred more
than halves. v1's held-out validation therefore measured how a constant
fitted on one sport-mix performs on a different sport-mix. It was a
composition test wearing a time test's clothes. **This is the mechanism
behind the review's B1, now quantified at source.**

## A1.5 — Effective data window

By outcome availability, not column existence:

| month | races with a BSP |
|---|---:|
| 2026-04 | 14 |
| 2026-05 | 2,251 |
| 2026-06 | 2,414 |
| 2026-07 | 3,888 |
| 2026-08 (to 3rd) | 592 |

**Effective window is 1 May – 3 Aug 2026**, not "6 Apr – 3 Aug" as v1
stated. April contributes 14 races.

## A1.4 — Selection mechanism

Funnel, races from 1 May:

| stage | n |
|---|---:|
| races captured | 48,297 |
| with a Betfair win market id | 11,082 |
| with any Betfair snapshot | 15,196 |
| with a final snapshot | 15,105 |
| **with a realised BSP** | **9,159** |

The binding constraint is **Betfair market identity**, not BSP
back-fill: only 23% of captured races ever get a Betfair market, and
~61% of those that do end with a usable BSP. The universe is therefore
"races the collector matched to a Betfair market and saw through to
settlement" — not a random sample of racing. Since Stage B restricts to
thoroughbreds anyway, the relevant question is absolute count per
stratum, answered next.

## A1.2 — The operator's decisions (the target population)

**Sport:** Horse Racing 264 (93.3%), Greyhound Racing 19 (6.7%).
**Venues:** 53 distinct. Top: rosehill 36, eagle farm 34, randwick 33,
doomben 25, caulfield 25, flemington 24, morphettville 11, darwin 7,
sandown 6, pakenham 6.

**Matched price:** n=283, median **4.40**, p95 **12.00**, max 21.00,
**99.6% at or below 20.0**.

**Placement time — the decision weights (amendment 18):**

| window | n | share |
|---|---:|---:|
| before T−60 | 24 | 8.5% |
| T−60..30m | 9 | **3.2%** |
| T−30..10m | 33 | 11.7% |
| T−10..3m | 96 | **33.9%** |
| T−3..0m | 97 | **34.3%** |
| after scheduled jump | 24 | 8.5% |

**68.2% of decisions are made inside the last ten minutes.** v1's two
headline improvements (+28%, +32%) came from windows carrying **14.9%**
of decisions between them.

## A1.3 — Overlap: is the question answerable?

Operator's top ten venues all present in the analysis universe and all
classified thoroughbred. Four of the next six (warrnambool, taree,
rockhampton, q2 parklands) classify greyhound — consistent with the 19
greyhound bets on record.

**Thoroughbred runner-rows available per stratum** (pre-registration
§1 A1.3 threshold: 200 held-out rows or no constant is fitted):

| grade | bucket | fit | report |
|---|---:|---:|---:|
| METRO | T−60..30 / 30..10 / 10..3 / 3..0 | 5,103 / 5,103 / 4,609 / 3,548 | 1,953 / 1,966 / 1,801 / 1,450 |
| PROVINCIAL | " | 5,529 / 5,529 / 5,100 / 4,427 | 2,443 / 2,443 / 2,307 / 1,994 |
| COUNTRY | " | 14,980 / 14,974 / 14,587 / 12,472 | 5,422 / 5,455 / 5,198 / 4,703 |

**Every stratum clears the threshold. Stage B can proceed on the
operator's own population.**

**Caveat that must survive into Stage B:** these are runner-rows.
Clustering is at meeting-day (amendment 21), and metro thoroughbred is
657 races over three months — on the order of 60–90 meeting-days in the
fit window. Effective sample for inference is the cluster count, not the
row count, so metro standard errors will be materially wider than row
counts suggest. Expected resolution on a metro β is roughly ±0.05.

---

## OPEN ITEM BLOCKING §5.3 — the hedge-stake reference is contested

Pre-registration §5.3 sets the lay-depth threshold against the **armed
stake**, referenced to the realised hedge distribution. Two sources
disagree:

| source | n | median | p90 | max |
|---|---:|---:|---:|---:|
| `bets.matched_stake` where side=LAY | 84 | $38.60 | $42.07 | **$79.79** |
| `bet_legs.matched_stake` for LAY bets | 48 | $23.93 | $40.02 | **$48.44** |

`bet_legs` covers only 48 of the 84 lay bets, so it is incomplete; the
S266 money review quoted a third figure again (median $7.21, max
$48.44), which this report could not reproduce from either source.

For reference, lay **liability** (stake × (price−1)) is a different and
much larger quantity: median $289.92, max $861.35. Depth on the exchange
is denominated in backer's stake, so stake — not liability — is the
correct comparator against `best_lay_size`.

**This must be resolved before §5.3 runs.** Provisional position: use
`bets.matched_stake` (the complete source, n=84) and report the
`bet_legs` figures alongside. Not adopted until Gate 1 rules.

## What Stage A does NOT claim

No fit has been run. No constant is proposed. Nothing here supports or
refutes any v1 finding except by describing the population — and the one
v1 finding it does bear on (the composition of the out-of-time split) it
confirms as broken.
