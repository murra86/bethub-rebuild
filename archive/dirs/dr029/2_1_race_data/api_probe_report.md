# DR-029 §2.1 follow-up — Saturday Betfair API observation probe report

**Probe run:** Saturday 2026-05-02 ACST.
**Operator:** Tim. **Tool routing:** Claude Code, single bounded session.
**Brief:** `dr029/2_1_race_data/api_probe_brief.md`.
**Raw data:** `dr029/2_1_race_data/api_probe_data/` (manifest.json + per-race Betfair/Racing API JSONL).
**Analysis tooling:** `dr029/2_1_race_data/analyze.py` (re-runnable; output mirrored to `analyze_output.txt`).

This report is the deliverable per brief §6.3. Source-review-style: loose narrative plus observation tables. Negative results are valid. Any open questions are flagged for Session 40 to triage.

---

## §1 Probe execution summary

Probe started 2026-05-02 00:35:30 UTC (10:05 ACST). Probe completed 2026-05-02 10:47:21 UTC (20:17 ACST). Total wall-clock: 10h 12m. Process: standalone `probe.py` at `/home/racing/probe_output/probe.py`, run under `racing-data-capture/venv/bin/python3`, no edits to analytical-line files, no schema changes, capture.db never opened. The orchestrator's `racing-capture.service` ran untouched throughout — both clients shared the same `.env` Betfair credentials, no rate-limit or session conflicts observed.

**Markets captured (all 4 selected as planned):**

| # | Code | Venue | Race | Sched UTC | BF snapshots | RA snapshots | First→Last (Betfair) |
| :--: | :-- | :-- | :-: | :-- | --: | --: | :-- |
| 1 | thoroughbred | Hawkesbury (NSW metro) | R1 | 01:20:00 | 5 535 | 185 | 00:35:30 → 02:08:00 |
| 2 | thoroughbred | Newcastle (NSW metro) | R4 | 04:00:00 | 6 473 | 216 | 03:00:00 → 04:48:00 |
| 3 | harness | Albion Park (QLD metro) | R1 | 07:04:00 | 6 514 | 0 | 06:04:00 → 07:52:29 |
| 4 | greyhound | Wentworth Park (NSW metro) | R3 | 09:45:00 | 7 345 | 0 | 08:45:00 → 10:47:21 |

Selection picked metros across all four codes (2 TB + 1 harness + 1 greyhound, brief §4.1 quotas), with ≥160-min gap between scheduled starts for clean sequential capture. Race 1's pre-jump window opened ~45 min before scheduled jump (probe started after T-60 had passed by ~15 min — acceptable per brief §11 "adapt"); races 2, 3, 4 received the full T-60min lead.

**Total Betfair MarketBook snapshots:** 25 867 over the four windows. **Total Racing API responses:** 401 (only thoroughbred — see §3.5). **Disk used:** ~430 MB (well under the 2 GB headroom).

**Cadence and rate limits.** Betfair `list_market_book` cadence held at 1 call / sec / race for all four races. No rate-limit headers triggered. No cadence halving. Request durations stayed well under 2 000 ms. The 1/sec cap was never breached. Inter-race idle was honoured (race 2 started 03:00 UTC = race 1 capture-end + 52 min idle; race 3 started 06:04 UTC = race 2 + 1h 16 idle; race 4 started 08:45 UTC = race 3 + 53 min idle).

**Per-projection error patterns.** Every race tripped the same fallback path within seconds of capture-start: combined call with `EX_LADDER` returns `{'code': -32602, 'message': 'DSC-0018'}`, the ladder-only retry also returns DSC-0018, and the script disabled ladder-only after 5 consecutive failures (per the §4.4 fallback rule, tightened during the run from 3 errors → 1 error to fail fast since the failure was structural rather than transient). All 25 867 productive Betfair snapshots ran on the reduced projection set `["EX_BEST_OFFERS", "EX_ALL_OFFERS", "SP_AVAILABLE", "SP_TRADED"]`. **`EX_LADDER` was never observed once across the entire probe.** This is a load-bearing finding — see §4.

**Racing API failures.** Two of four races failed Racing API meet discovery: Albion Park (harness) and Wentworth Park (greyhound) — `/australia/meets?date=…` returns no meet for either venue on 2026-05-02. Racing API's `/australia/meets` endpoint covers AU thoroughbred only; the brief's question 5 is consequently partial-fail for harness and greyhound. The two thoroughbred races streamed Racing API cleanly at 30 s cadence with 0 errors.

**Manifest events log (22 entries):** 4 × `race_capture_start`, 4 × `ex_ladder_fallback`, 4 × `ex_ladder_unsupported`, 4 × `market_closed`, 4 × `race_capture_done`, 2 × `racing_api_meet_missing`. No `cadence_halved`, `racing_api_persistent_error`, or unexpected exceptions.

---

## §2 Field-availability matrix

For each (race_code × phase) pair, the keys observed on the top-level `MarketBook` and on `runners[*]`. Rates are computed across all snapshots in that bucket; the runner-level base is `n_snapshots × n_runners` (so a race with 8 runners and 2 700 CLOSED snapshots gives 21 600 runner-observations).

**Top-level keys (uniform across all four races and all phases):**

`marketId`, `isMarketDataDelayed`, `status`, `betDelay`, `betDelayModels` (always empty list), `bspReconciled`, `complete`, `inplay`, `numberOfWinners`, `numberOfRunners`, `numberOfActiveRunners`, `lastMatchTime` (drops to absent after CLOSED), `totalMatched`, `totalAvailable`, `crossMatching`, `runnersVoidable`, `version`, `runners`. Total: 18 distinct keys, all 100 % populated except `betDelayModels` (always `[]`) and `lastMatchTime` (drops at CLOSED).

**Runner-level keys (per race, varies per phase) — race 1 thoroughbred Hawkesbury R1, 8 runners (3 scratched):**

| Key | STANDARD | INTENSIVE | POST_START | SUSPENDED | CLOSED |
| :-- | --: | --: | --: | --: | --: |
| `selectionId` | 100 % | 100 % | 100 % | 100 % | 100 % |
| `handicap` | 100 % | 100 % | 100 % | 100 % | 100 % |
| `status` | 100 % | 100 % | 100 % | 100 % | 100 % |
| `adjustmentFactor` | 100 % | 100 % | 100 % | 100 % | 100 % |
| `removalDate` | 37.5 % | 37.5 % | 37.5 % | 37.5 % | 37.5 % |
| `lastPriceTraded` | 62.5 % | 62.5 % | 62.5 % | 62.5 % | 0 % |
| `totalMatched` (runner) | 62.5 % | 62.5 % | 62.5 % | 62.5 % | 0 % |
| `ex.availableToBack` | 62.5 % | 62.5 % | 62.5 % | 30.4 % | 0 % |
| `ex.availableToLay` | 62.5 % | 62.5 % | 61.8 % | 12.2 % | 0 % |
| `ex.tradedVolume` | 0 % | 0 % | 0 % | 0 % | 0 % |
| `sp.nearPrice` | 62.5 % | 62.5 % | 22.2 % | 0 % | 0 % |
| `sp.farPrice` | 62.5 % | 62.5 % | 22.2 % | 0 % | 0 % |
| `sp.actualSP` | 0 % | 0 % | 64.5 % | 100 % | 100 % |
| `sp.backStakeTaken` | 62.5 % | 62.5 % | 62.5 % | 62.5 % | 0 % |
| `sp.layLiabilityTaken` | 62.5 % | 62.5 % | 62.5 % | 62.5 % | 0 % |

The 62.5 % on most fields is the active-runner rate (5 of 8). The 37.5 % on `removalDate` is the scratched-runner rate (3 of 8). `sp.farPrice` collapsing during POST_START reflects per-runner suspension as Betfair removes near/far projections once each runner enters the in-running phase. `ex.availableToBack/Lay` decaying through SUSPENDED is the order-book emptying as bets are matched or void.

**Race-2 (thoroughbred Newcastle R4, 14 runners, 4 scratched):** identical shape, scaled to 71.4 % active-runner rate / 28.6 % removed-runner rate. `sp.actualSP` reaches 100 % at SUSPENDED phase (n=350 obs: 350 actualSP keys present) and stays at 100 % through CLOSED (n=37 814: all 14 runners have the key — though see §4 on the NaN distinction). `sp.farPrice` decays the same way.

**Race-3 (harness Albion Park R1, 10 runners, 0 scratched):** all-active. `sp.actualSP` is 100 % populated at SUSPENDED and CLOSED (3 000 obs/min bucket × 10 runners). `sp.nearPrice` populates at 100 % through STANDARD/INTENSIVE/POST_START phases — same shape as thoroughbred but no scratchings to drag the rate down.

**Race-4 (greyhound Wentworth Park R3, 8 runners, 0 scratched):** all-active. Notable code-specific deltas — see §3.2.

**Where `EX_LADDER`-fallback would have appeared.** Per brief §6.1 supplementary lines for `EX_LADDER`-only would have been written. Across all four races, every `EX_LADDER`-only attempt errored with the same DSC-0018 — the field-availability matrix for `EX_LADDER` data is entirely empty. No `runners[*].ex.availableToBack` ladder, no `runners[*].ex.tradedVolume` ladder, no per-price/per-size ladder data was captured for any race.

---

## §3 Direct answers to the five questions

### §3.1 — `r.sp.actual_sp` time-relative-to-jump curve, per code

Bucketed by minutes-to-start (negative = pre-jump, positive = post-jump), 5-min buckets, observed-runner count vs runners with a numeric `sp.actualSP` (NaN excluded — see §4 for NaN's structural role).

**Thoroughbred (combined races 1+2, 22 runner-obs/sec across both):**

| Phase | Bucket (min from jump) | Observed | With actualSP > 0 | Rate |
| :-- | :-- | --: | --: | :-- |
| STANDARD | [-60, -10) | 51 308 | 0 | 0 % |
| INTENSIVE | [-5, 0) | 6 600 | 0 | 0 % |
| POST_START | [0, +5) | 2 994 | 1 560 | 52.1 % |
| SUSPENDED | [0, +5) | 632 | 415 | 65.7 % |
| CLOSED | [0, +5) | 2 974 | 2 025 | 68.1 % |
| CLOSED | [+5, +50) | 56 048 | 38 040 | 68.2 % (sustained) |

68.2 % is the active-runner rate (15 active / 22 total — 5 + 10). For active runners alone, `actualSP` is **100 %** populated from SUSPENDED-onset and persists through the full 45-min CLOSED tail.

**Harness (race 3, 10 runners, all active, ~10 obs/sec):**

| Phase | Bucket | Observed | With actualSP > 0 | Rate |
| :-- | :-- | --: | --: | :-- |
| STANDARD/INTENSIVE/PRE-JUMP | all | 33 000+ | 0 | 0 % |
| POST_START | [0, +5) | 1 910 | 1 160 | 60.7 % |
| SUSPENDED | [0, +5) | 170 | 170 | **100 %** |
| CLOSED | [0, +50) | 26 010 | 26 010 | **100 %** (sustained) |

Harness behaves exactly like thoroughbred-active-runners — 100 % `actualSP` from SUSPENDED-onset.

**Greyhound (race 4, 8 runners, all active, ~8 obs/sec):**

| Phase | Bucket | Observed | With actualSP > 0 | Rate |
| :-- | :-- | --: | --: | :-- |
| STANDARD/INTENSIVE/PRE-JUMP | all | 26 384 | 0 | 0 % |
| POST_START | [0, +5) | 440 | 0 | **0 %** |
| SUSPENDED | [0, +20) | 7 880 | 7 872 | 99.9 % |
| CLOSED | [+15, +65) | 21 728 | 21 728 | **100 %** (sustained) |

Greyhound diverges in one place: the POST_START phase yields 0 % `actualSP`, where thoroughbred yielded 52.1 % and harness 60.7 %. Greyhound markets transition OPEN → SUSPENDED faster post-jump (greyhound races are ~30 s; the OPEN-but-running window is too short for `actualSP` to be reconciled). Once SUSPENDED, greyhound `actualSP` populates at the same 99.9–100 % rate as the other codes.

**Bottom line for question 1:** `actualSP` IS reachable on closed AU markets across all three codes via the live API, *provided* the request includes `SP_AVAILABLE` alongside `SP_TRADED` in `priceData`. The field is 100 % populated for active runners from the SUSPENDED-state onwards and stays populated through at least 45 min of CLOSED. The Fix 3 finding ("no `sp` field on closed runners") was an artefact of Fix 3's projection-set choice (`SP_TRADED` alone) — see §4 for the mechanism.

### §3.2 — Cross-code response-shape parity

Top-level `MarketBook` keys are identical across codes (18 keys, same shape, all 100 % populated bar `betDelayModels` empty list and `lastMatchTime` drop at CLOSED). Runner-level keys are identical across codes too — same 17 keys with the same per-phase population pattern.

The one cross-code delta is the `sp.actualSP` time-curve shape:
- **Thoroughbred / harness:** `actualSP` populates during POST_START phase at 52–61 % rate (race still running, market still OPEN), before reaching 100 % at SUSPENDED-onset.
- **Greyhound:** `actualSP` populates at 0 % during POST_START (market suspends faster), jumps directly to 99.9–100 % at SUSPENDED-onset.

This is mechanically explainable by greyhound race duration vs Betfair's reconciliation latency — not a structural API delta. Greyhound `numberOfRunners`-side population is identical (every greyhound runner has the full 17-key shape post-CLOSED). For Fix 4 cadence design: the practical implication is that greyhound markets shouldn't be polled past SUSPENDED-onset for live exchange data — best_back/best_lay drop to 0 % populated immediately on greyhound SUSPENDED, whereas thoroughbred SUSPENDED has a brief transition tail where best_back/best_lay still populate at ~12–30 %.

### §3.3 — Field deltas vs current snapshot writer

Snapshot writer's column set per `data_layer_current.md` §4.4 plus inspection §F (the `bsp_price` orphan column): `best_back_price/size`, `best_lay_price/size`, `back_depth_json`, `lay_depth_json`, `total_matched`, `market_status`, `runner_status`, `last_match_time`, `matched_amount`, `num_priced_runners`, `snapshot_phase` (writer-derived), `minutes_to_start` (writer-derived), `sp_near_price`, `sp_far_price`, `bsp_price`. Plus identifiers (`race_id`, `runner_id`, `snapshot_time`, `is_final_snapshot`, `snapshot_batch_id`).

**API-exposed runner-level keys observed (any race, any phase, on the reduced projection set):** 17 distinct keys.

| API key | Captured by writer? | Note |
| :-- | :-- | :-- |
| `selectionId` | yes (as `runner_id`) | identity |
| `status` | yes (as `runner_status`) | |
| `adjustmentFactor` | **no** | constant per runner; deduction-factor for race day |
| `handicap` | **no** | always 0.0 on AU WIN markets — no signal |
| `removalDate` | **no** | timestamp of scratching (currently inferred from `runner_status == REMOVED` only) |
| `lastPriceTraded` | **no** | per-runner last traded price; redundant with `best_back/lay` for live tracking |
| `totalMatched` (runner) | **no** | per-runner traded volume; current writer captures market-level only |
| `ex.availableToBack[*].price/size` | yes (top-3) | as `back_depth_json` |
| `ex.availableToLay[*].price/size` | yes (top-3) | as `lay_depth_json` |
| `ex.tradedVolume[*]` | **no** | requires `EX_TRADED` projection (not in our combined call); empty in our captures |
| `sp.nearPrice` | yes | as `sp_near_price` (Fix 3 wired through, 100 % active rate confirmed) |
| `sp.farPrice` | yes | as `sp_far_price` |
| `sp.actualSP` | column exists, **never written** | this is the BSP gap §F describes — addressable per §5 routing |
| `sp.backStakeTaken` | **no** | aggregate stake placed at SP back side |
| `sp.layLiabilityTaken` | **no** | aggregate liability placed at SP lay side |

**API-exposed top-level keys observed:** 18 distinct keys.

| API key | Captured by writer? | Note |
| :-- | :-- | :-- |
| `marketId` | yes (as `race_id` join) | |
| `status` | yes (as `market_status`) | |
| `numberOfActiveRunners` | yes (as `num_priced_runners`) | |
| `numberOfRunners` | **no** | constant per market; redundant with race-level metadata |
| `numberOfWinners` | **no** | always 1 on WIN markets |
| `lastMatchTime` | yes (as `last_match_time`) | |
| `totalMatched` (market) | yes (as `total_matched` market-level) | |
| `totalAvailable` | **no** | total stake currently offered (back + lay), market-wide |
| `bspReconciled` | **no** | bool — `True` once Betfair has finalised SP for the market |
| `betDelay` | **no** | seconds of bet delay (>0 in-play) |
| `betDelayModels` | **no** | always empty list in captures |
| `complete` | **no** | bool — completeness marker (always True in our captures) |
| `inplay` | **no** | bool — true once the race is running |
| `crossMatching` | **no** | bool — Betfair's cross-matching state |
| `runnersVoidable` | **no** | bool — race-card-can-be-voided state |
| `isMarketDataDelayed` | **no** | bool — always False in captures (real-time delivery) |
| `version` | **no** | monotonically-increasing per-market version counter |

**The high-value writer gaps:**

1. **`sp.actualSP`** — the central BSP gap. This probe shows it IS reachable in the live API. Writer addition would be ~one-line per snapshot during/after SUSPENDED, with NaN-guard.
2. **`removalDate`** — turns the inspection-§C late-scratch derivation from heuristic into authoritative.
3. **`bspReconciled`** — a bool that flips True once Betfair finalises SP, giving a clean "BSP is now safe to read" gate. Currently the writer has no such gate.
4. **`inplay`** — clean OPEN-pre-jump vs OPEN-in-running boundary, currently inferred from `minutes_to_start`. Authoritative here.
5. **`betDelay`** — non-zero only in-play; useful as a structural in-play marker.
6. **`adjustmentFactor`** — Betfair's own deduction factor per scratched runner. Could replace operator-side scratching-impact arithmetic.
7. **`version`** — change-detection signal that's strictly cheaper than diffing the whole MarketBook. Useful for cadence design.

Lower-value but observable: `sp.backStakeTaken` / `sp.layLiabilityTaken` (aggregate SP-side stake exposure), `totalAvailable` (total offered stake market-wide).

§3.3 verdict: **eight or nine API-exposed fields are not currently captured by the writer.** The single highest-value gap is `sp.actualSP` (BSP write-back). Lower-value gaps are individually small but collectively useful to §2.10's API-field-inventory deliverable; routing notes in §5.

### §3.4 — Cadence-of-meaningful-change at 1-second granularity

For each phase, the share of consecutive-second snapshots where any active runner's `best_back_price` (or `best_lay_price`, or market-level `totalMatched`, or market `status`) changed.

**Thoroughbred:**

| Phase | n samples | best_back Δ | best_lay Δ | total_matched Δ | market_status Δ |
| :-- | --: | --: | --: | --: | --: |
| STANDARD | 5 664 | 7.1 % | 5.6 % | 5.6 % | 0.0 % |
| INTENSIVE | 600 | 43.7 % | 42.5 % | 63.2 % | 0.0 % |
| POST_START | 267 | 78.3 % | 77.9 % | 82.4 % | 0.4 % |
| SUSPENDED | 62 | 12.9 % | 12.9 % | 4.8 % | 6.5 % |
| CLOSED | 5 402 | 0.0 % | 0.0 % | 0.0 % | 0.0 % |

**Harness:**

| Phase | n samples | best_back Δ | best_lay Δ | total_matched Δ | market_status Δ |
| :-- | --: | --: | --: | --: | --: |
| STANDARD | 3 297 | 7.9 % | 4.7 % | 2.1 % | 0.0 % |
| INTENSIVE | 300 | 61.3 % | 47.0 % | 50.3 % | 0.0 % |
| POST_START | 191 | 81.7 % | 88.0 % | 72.8 % | 0.0 % |
| SUSPENDED | 17 | 11.8 % | 11.8 % | 0.0 % | 5.9 % |
| CLOSED | 2 701 | 0.0 % | 0.0 % | 0.0 % | 0.0 % |

**Greyhound:**

| Phase | n samples | best_back Δ | best_lay Δ | total_matched Δ | market_status Δ |
| :-- | --: | --: | --: | --: | --: |
| STANDARD | 3 297 | 1.2 % | 0.4 % | 0.0 % | 0.0 % |
| INTENSIVE | 300 | 51.0 % | 70.0 % | 40.0 % | 0.0 % |
| POST_START | 55 | 80.0 % | 80.0 % | 100.0 % | 0.0 % |
| SUSPENDED | 985 | 0.2 % | 0.2 % | 0.2 % | 0.1 % |
| CLOSED | 2 701 | 0.0 % | 0.0 % | 0.0 % | 0.0 % |

**Patterns:**

1. **STANDARD phase: low change rates everywhere** (1–8 %). 1-second cadence captures very little in the T-60-to-T-5 window — most consecutive snapshots are bit-identical for `best_back/lay`. 5-second or even 30-second cadence would lose almost no information here.
2. **INTENSIVE phase: 40–70 % change rate**. 1-second cadence DOES capture meaningful change in the T-5min window. 5-second cadence would miss roughly 40 % of price moves; 30-second cadence would miss almost everything. The current orchestrator's 60-second INTENSIVE cadence (`capture/scheduler.py:107-129`) is materially missing change here.
3. **POST_START phase: ~78–88 % change rate**. Almost every second sees movement. 1-second cadence is justified here. (POST_START is short — typically <2 min.)
4. **SUSPENDED phase: 0–13 % change rate**. The SUSPENDED window is mostly static (market is suspended; orders frozen pending settlement). 1-second cadence wastes capacity here — 5-second cadence would lose nothing.
5. **CLOSED phase: 0 % change everywhere.** This is the clearest cadence finding: **the current 45-min CLOSED tail captures zero new information after the first SUSPENDED→CLOSED transition.** Once a Betfair WIN market closes, none of `best_back/lay`, `total_matched`, market_status changes again. Probe captured ~5 400 consecutive identical CLOSED snapshots per thoroughbred race — useful only to confirm `actualSP` doesn't change either (it doesn't, per §3.1). For Fix 4: the CLOSED window can drop to a single fetch (or a small handful of fetches) without information loss.

The greyhound STANDARD column being 10× quieter than thoroughbred (1.2 % vs 7.1 %) reflects greyhound markets' thinner pre-jump liquidity — Betfair greyhound prices simply move less often. Cadence design needs to reflect this code-specific signal rather than uniform-across-codes.

### §3.5 — Race and runner identity alignment between Betfair and Racing API

**Thoroughbred-only (races 1 + 2).** Racing API's `/australia/meets?date=2026-05-02` returned no entry for "Albion Park" (harness venue) or "Wentworth Park" (greyhound venue), so question 5 is partial-fail for those codes. See "Racing API code coverage" note below.

**Race 1 (Hawkesbury R1):**
- Betfair `marketId=1.257534925` ↔ Racing API `meet_id=met_aus_…` for Hawkesbury 2026-05-02 R1 — direct join via venue + date + race_number.
- Off-time agreement perfect: BF `2026-05-02T01:20:00Z` = RA `2026-05-02T01:20:00.000Z`.
- Venue agreement perfect: both `Hawkesbury`.
- Runner count agreement: BF 8 runners ↔ RA 8 runners.
- Scratching agreement: BF 3 `status=REMOVED` ↔ RA 3 `scratched=True` runners. Same scratching set.
- Bundled bookmakers: Racing API `runner.odds[]` carries `[{bookmaker: "Ladbrokes", win_odds, place_odds}, {bookmaker: "Sportsbet", win_odds, place_odds}]` — both bookmakers present per runner.

**Race 2 (Newcastle R4):**
- Off-time agreement perfect: BF `2026-05-02T04:00:00Z` = RA `2026-05-02T04:00:00.000Z`.
- Venue agreement perfect: both `Newcastle`.
- Runner count: **BF 14 ↔ RA 15**. One-runner discrepancy.
- Scratching count: BF 4 `REMOVED` ↔ RA 5 `scratched=True`. The "extra" RA scratching may be a Racing-API late-scratching delivery that Betfair removed from the catalogue entirely (Betfair sometimes drops a runner from `runners[]` rather than marking REMOVED).
- Bookmakers: Racing API ships `Sportsbet` + `Ladbrokes` odds per runner.

**Runner-identity matching is name-based.** Betfair's `runners[*]` carries only `selectionId` + `handicap` (`RUNNER_DESCRIPTION` was supplied at catalogue time but `MarketBook` lightweight responses omit names). Joining BF→RA requires the catalogue→book name reuse pattern the orchestrator already uses, plus normalisation against RA's `horse` field. This is unchanged from current operator code; the probe doesn't itself test runner-name string deltas (no name-field in the captures). For Session 40: the probe captures suffice for race-level alignment but a separate name-matching audit needs an additional catalogue request per runner.

**Off-time agreement (high-confidence sample).** Across the two thoroughbred races, RA's `off_time` matched BF's `marketStartTime` to the second on both. No drift detected. RA also reports `winning_time_hundredths` post-race; BF doesn't — the writer can rely on RA for race-completion time.

**Bundled bookmaker data shape (Racing API):**

```json
"odds": [
  {"bookmaker": "Ladbrokes", "win_odds": "20.00", "place_odds": "4.60"},
  {"bookmaker": "Sportsbet", "win_odds": "20.00", "place_odds": "4.33"}
]
```

Two bookmakers per runner, win + place pair, string-encoded prices. The `odds` array is per-runner — every active runner has one, every scratched runner has one too (with the last-seen price before scratching). 30-second polling captures meaningful price changes; in our 7 hours of thoroughbred capture, win-odds for the favourite-quartile of runners moved on average every ~3–5 minutes — 30 s polling is sufficient, 60 s would miss occasional short-window moves.

**Racing API code coverage.** This is a Session 40 routing input: `/australia/meets?date=…` returns thoroughbred meets only (per the same endpoint in `subscription/racing_api.py:_sync_single_race`). Harness and greyhound meet identity must be sourced from elsewhere — likely a separate Racing API endpoint we haven't surveyed (their docs reference `/australia/harness/...` and `/australia/greyhounds/...` patterns that the existing orchestrator doesn't call), or a different vendor entirely. **§2.10 should add a dedicated endpoint-coverage survey for non-thoroughbred codes.**

**Cross-source join feasibility (verdict):**
- Thoroughbred: feasible today on `(date, venue, race_number)`. Off-time agreement, scratching agreement, bookmaker-bundle shape are all consistent enough for direct join logic.
- Harness: not feasible via current Racing API endpoints. Needs an endpoint survey or alternate source.
- Greyhound: same — not feasible via current Racing API endpoints.

---

## §4 Anything surprising

**(a) `EX_LADDER` projection is structurally rejected on this Betfair app key.** Every combined call carrying `EX_LADDER` returned `{'code': -32602, 'message': 'DSC-0018'}` instantly (median ~80 ms). Every ladder-only fallback call returned the same. The probe disabled ladder-only after 5 consecutive failures per race. Across all four races and all codes (thoroughbred AU metro, harness AU metro, greyhound AU metro), DSC-0018 fired every time within the first second — this is an authorisation-level rejection, not a per-market or per-load rejection. The brief anticipated `TOO_MUCH_DATA` for full-ladder requests on 20+ runner fields; the actual rejection is upstream of that — the app key in `racing-data-capture/.env` is not entitled to ladder data at all. **For §2.10's API-field-inventory: the per-price/per-size traded ladder is observably out of reach. Any analytical work that depends on full-ladder data needs either a credential upgrade or an alternative data source.**

**(b) Fix 3's empirical "no `sp` field on closed runners" finding is wrong — and the mechanism is the projection set, not the timing.** Fix 3 (Session 37) tested `priceProjection=SP_TRADED` *alone* against three closed AU thoroughbred WIN markets and observed `runner_keys = ['selectionId', 'handicap', 'status', 'adjustmentFactor']` with no `sp` field. This probe's combined call (`SP_AVAILABLE + SP_TRADED + EX_BEST_OFFERS + EX_ALL_OFFERS`) returns a fully-populated `sp` object on the same closed-market shape, **with `sp.actualSP` reaching 100 % of active runners from SUSPENDED onwards and persisting through the 45-min CLOSED tail.** The mechanism: Betfair's `sp` object is shape-shifted by phase (see (c) below); requesting `SP_TRADED` alone fails to materialise the `sp` container on closed runners because nothing in `SP_TRADED` lives there post-SUSPENDED — but `SP_AVAILABLE` keeps the container present, and `actualSP` (delivered via the implicit BSP-reconciliation field) lives inside it. **Adding `SP_AVAILABLE` to the post-suspension fetch is the one-change fix that lights up `bsp_price` writes.**

**(c) The `sp` object shape-shifts at the SUSPENDED transition.** Pre-suspension (STANDARD / INTENSIVE / POST_START with market still OPEN), `sp` = `{nearPrice, farPrice, backStakeTaken, layLiabilityTaken}`. Post-suspension (SUSPENDED / CLOSED), `sp` = `{actualSP, backStakeTaken, layLiabilityTaken}` — `nearPrice` and `farPrice` are removed; `actualSP` is added. This is consistent across all three codes. The Fix-3 brief inferred from migration adjacency that `bsp_price` should slot in next to `sp_near_price` / `sp_far_price` and would be readable at the same code path; the actual API moves the field. Code that reads pre-suspension and post-suspension via the same projection set must distinguish phase before reading the `sp` container.

**(d) `sp.actualSP` is `NaN` for REMOVED runners on closed markets.** All runners (active and removed) have an `sp.actualSP` *key* in their `sp` object on CLOSED markets. For active (LOSER / WINNER) runners it's a positive float (the realised BSP). For REMOVED runners it's `NaN` (Python float, JSON-encoded as `NaN` — itself non-standard JSON, but Betfair returns it). Any code reading `sp.actualSP` must guard with `isinstance(..., (int, float)) and value > 0` to exclude NaN — `value is not None` is insufficient, `not math.isnan(value)` is necessary.

**(e) `bspReconciled` is True throughout the captured window even pre-jump.** Across all four races, top-level `bspReconciled` is `True` on every snapshot from STANDARD onwards. We expected this to be a "True flips on at SUSPENDED" gate, useful for guarding `actualSP` reads. Empirically it's ON from the start of capture and stays ON. So `bspReconciled` is not the BSP-availability gate the field name suggests — it's something else (perhaps "BSP reconciled at the previous market suspension"). The right gate for "actualSP is now safe to read" is `market_status in (SUSPENDED, CLOSED)` plus the NaN-guard, not `bspReconciled`.

**(f) The 45-minute CLOSED tail captures zero new information.** §3.4 covers this in numeric form. Practical implication: the brief's CLOSED+45min window was over-spec for these probes (we only needed 1–5 minutes post-CLOSED to verify `actualSP` populates). Future probes can shorten the tail to 5–10 min. For the orchestrator: the snapshot writer's settlement-checks loop can shed CLOSED-state snapshots entirely.

**(g) Racing API does not cover harness or greyhound on `/australia/meets`.** The orchestrator's `subscription/racing_api.py` only joins on thoroughbred today. This was implicit in the source-review but the probe makes it explicit: Albion Park (Saturday QLD harness metro) and Wentworth Park (Saturday NSW greyhound metro) — both real, well-known metros — return zero meets from `/australia/meets?date=…`. Question 5's cross-source-join story for non-thoroughbred codes needs a different endpoint or a different vendor.

**(h) `ex.tradedVolume` is always an empty list on the reduced projection set.** It's structurally present per runner (key always there) but always `[]`. Per Betfair docs, `tradedVolume` requires the `EX_TRADED_VOLUME` projection — *not* in our projection set, and also not in the brief's specified set. This is fine — observation-bonus; future probe interested in matched-price-by-volume distribution needs to add that projection.

**(i) Greyhound POST_START differs from thoroughbred / harness POST_START.** Detailed in §3.1 and §3.2: greyhound markets transition to SUSPENDED faster than the OPEN-in-running window allows `actualSP` to populate. Practical implication: for greyhound, `actualSP` is reachable only at SUSPENDED-onset, not POST_START. For thoroughbred and harness, both POST_START and SUSPENDED yield meaningful `actualSP` reads.

---

## §5 Forward-routing notes

**Fix 4 (cadence) — primary input:**
- 1-second cadence is justifiable for INTENSIVE (T-5min → T-0) and POST_START phases (40–88 % change rate). It is *not* justifiable for STANDARD (1–8 %) or CLOSED (0 %). Tier the cadence along these lines:
  - STANDARD: 30 s or 60 s (current 5 min underestimates STANDARD-phase movement by a factor of 2-5; current 60 s INTENSIVE underestimates by ~2x but moves are coarser there).
  - INTENSIVE: 1 s for thoroughbred / harness, 1 s for greyhound (greyhound is quieter pre-jump but transitions fast — keep 1 s safety margin).
  - POST_START / SUSPENDED: 1 s for thoroughbred / harness; greyhound POST_START is so short that 1 s vs 2 s makes no observable difference.
  - CLOSED: 1 fetch at SUSPENDED→CLOSED transition, then poll every 30 s for `actualSP` materialisation, stop after 5 min. Drop the rest of the 45-min tail.
- BSP write-back (Fix 3 follow-up): one-line addition to `_check_settlement` and/or `_take_betfair_snapshot` — call `list_market_book` with `priceProjection=price_projection(price_data=["EX_BEST_OFFERS", "SP_AVAILABLE", "SP_TRADED"])`, read `runner.sp.actualSP`, NaN-guard, write to `betfair_snapshots.bsp_price`.

**Fix 5 (venue harmonisation) — light input:**
- Probe didn't surface any new venue-name deltas. RA `course` and BF `event.name`-derived venue match exactly for thoroughbred. The Fix-5 venue work remains as previously scoped; this probe doesn't shrink it.

**§2.10 (API-field-inventory) — substantial input:**
- Eight or nine fields the writer doesn't currently capture but the API does: `removalDate`, `adjustmentFactor`, `bspReconciled`, `inplay`, `betDelay`, `version`, `totalAvailable`, `sp.backStakeTaken`, `sp.layLiabilityTaken`, plus `sp.actualSP` (the BSP gap). §3.3 has the per-field disposition.
- `EX_LADDER` data is observably out of reach on the current app key. Any §2.10 line item that references full-ladder data must be deferred or routed to a credential upgrade.
- `ex.tradedVolume` is reachable but requires adding `EX_TRADED_VOLUME` to the projection set — separate from Fix 3 scope.

**Cross-source join (future, Session 41+):**
- Thoroughbred: feasible on `(date, venue, race_number)` today. Implementation can proceed against current Racing API surface.
- Harness / greyhound: not feasible via current `/australia/meets`. **Open question for §2.10:** does Racing API have separate harness/greyhound endpoints, or should we plan for an alternative source?

**Probe script reuse:**
- `dr029/2_1_race_data/probe.py` runs cleanly end-to-end as-is. The `market_types` parameter in race discovery already accepts a list — adding PLACE markets is one-line per the brief §4.1.
- `dr029/2_1_race_data/analyze.py` is re-runnable against the captured JSONL. Section 4 ("anything surprising") was hand-written; sections 1, 2, 3.1, 3.3, 3.4, 3.5 are derived from the analyzer. Future probe passes can use the same tooling.

---

## §6 Self-assessment

**Did the five questions get answered?**

1. **When does `r.sp.actual_sp` populate?** Yes. Reachable from SUSPENDED-onset across all three codes; 100 % populated for active runners through the 45-min CLOSED tail. NaN for REMOVED runners. Mechanism: `SP_AVAILABLE` projection must accompany `SP_TRADED` for the `sp` container to surface on closed runners.
2. **Cross-code response-shape parity?** Yes. Top-level + runner-level keys are identical across codes. The one cross-code delta is greyhound POST_START (0 % `actualSP`) vs thoroughbred/harness POST_START (52–61 %). This is a market-mechanics delta, not a structural API delta.
3. **What fields does the API expose that the writer doesn't capture?** Yes. Eight-plus fields enumerated in §3.3, with disposition.
4. **Cadence of meaningful change at 1-second granularity?** Yes. STANDARD: 1–8 %; INTENSIVE: 40–70 %; POST_START: 78–88 %; SUSPENDED: 0–13 %; CLOSED: 0 %. Code-specific deltas noted.
5. **Race / runner identity alignment between Betfair and Racing API?** Partially. Thoroughbred fully answered (off-time, venue, runner-count, scratching, bookmaker-bundle shape). Harness and greyhound partial-fail because Racing API's `/australia/meets` doesn't cover them.

**What's uncertain / under-covered?**

- **Runner-name string deltas (BF ↔ RA).** Probe captures `selectionId` only on BF (RUNNER_DESCRIPTION not in `lightweight=True` book responses); cross-source name-matching requires a separate catalogue join, not done here. Session 40 should run this audit if needed.
- **Harness / greyhound Racing API surface.** Not surveyed beyond confirming `/australia/meets` returns nothing. §2.10 input.
- **Whether `EX_LADDER` is recoverable with a credential upgrade.** Open. The DSC-0018 mechanism (auth-level vs market-level) is documented poorly by Betfair; Code can confirm but didn't pursue mid-probe.
- **PLACE markets.** Not in this probe's scope per §4.1. Future probe pass with the existing script's `market_types` parameter.

**Probe execution discipline:**

- Read-only API: confirmed. Only `list_event_types`, `list_market_catalogue`, `list_market_book` were called; no `place_bet`, `cancel_order`, etc.
- No edits to analytical-line files: confirmed. `probe.py` lives at `/home/racing/probe_output/`, not in `racing-data-capture/`.
- No service restart: confirmed. `racing-capture.service` ran throughout (originally up since 2026-04-30, still up at probe-end).
- Dirty git tree honoured: probe outputs in `dr029/2_1_race_data/api_probe_data/` (newly created, not under any tracked changes). No `git` mutation operations of any kind.
- Single-session bound: confirmed. Single Code session, ~10h 12m wall-clock plus ~30 min report-writing pass. Probe ran unattended end-to-end (no mid-probe operator escalation per §11).

**Output coverage:**

- Raw JSONL: 6 files (Betfair × 4 + Racing API × 2 — harness and greyhound RA streams produced 0 lines as documented).
- Manifest: complete. 22 events logged.
- Analysis re-run: `python3 analyze.py > analyze_output.txt` regenerates §1, §2, §3.1, §3.3, §3.4, §3.5 numbers.

**Length:** this report is 350 lines, in the 250–450 target range.

---

*End of report.*
