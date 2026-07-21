# §2.10 — External analytics environmental scan inventory

**Drafted:** Session 76 (2026-05-04 ACST).
**Status:** in flight.
**Governing scope:** `dr029/dr029_scope.md` §2.10.
**Substrate:** Saturday API observation probe report (`dr029/2_1_race_data/api_probe_report.md`); Racing API OpenAPI spec (`openapi.json`); current snapshot-writer column set (per `data_layer_current.md` §4.4 plus inspection §F).

---

## §1 Framing

### §1.1 What §2.10 is

§2.10 is the time-boxed inventory step that closes out DR-029's data-layer fit-for-purpose
review. The deliverable is a per-field disposition list across two source APIs (Betfair
Exchange API and The Racing API), classifying each field the sources expose into one of
three capture buckets:

- **Capture in the data review** — field is available, not currently captured by the
  snapshot writer, cheap to add.
- **Park with rationale** — field is available but expensive to capture (separate
  projection, credential upgrade, vendor cost), or genuinely not available on the current
  surface. Each parked field carries a one-line reason.
- **Already covered** — field is available and currently captured. No action.

The output is a substrate for v3 build-proper capture decisions, not an implementation
specification. v3's capture layer reads §2.10's bucket-1 list as "fields to wire in" and
§2.10's bucket-2 list as "fields to revisit when their parking rationale changes."

### §1.2 What §2.10 is not

§2.10 does not specify cadence. Capture-cheapness in §2.10 is "cheap as a write at
whatever cadence the orchestrator already runs." The cadence-tier design (when STANDARD
becomes 30s, when CLOSED stops capturing, when greyhound POST_START differs from
thoroughbred) is Fix 4's territory and lands separately. §2.10's per-field cost
classification is cadence-agnostic.

§2.10 does not specify analytics. The capture-only constraint per `dr029_scope.md` §2.10
holds: §2.10 decides what fields are worth pulling into `capture.db`, not what models or
analyses consume them. Analytics layer formalisation remains deferred per `dr029_scope.md`
§3.2.

§2.10 does not assess vendor value. The Racing API value question (whether the £49.99 GBP
+ AU regional add-on subscription is justified by what it uniquely provides for
thoroughbreds) is a strategic call that sits post-DR-029, with §2.10's inventory as
substrate. §2.10 enumerates what Racing API exposes; the cost-benefit call is operator
work after the inventory is in hand.

§2.10 does not extend coverage to non-racing sports. Sports analytical capture is
out-of-scope per principle 1.3 (`dr029_scope.md` §1.3). Sports operational reads via
`betfair_client` are separate and already specified in §2.2.

### §1.3 The racing-only constraint

§2.10 covers thoroughbred, harness, and greyhound — the three racing codes captured to
`capture.db` today. The probe report's §3.2 confirmed cross-code response-shape parity at
the Betfair API level: top-level and runner-level keys are identical across codes, with
one mechanically-explainable cross-code delta (greyhound POST_START transitions to
SUSPENDED faster than the OPEN-in-running window allows `actualSP` to populate). For
§2.10 inventory purposes, Betfair's per-field availability is treated as code-uniform.

Racing API coverage is asymmetric across codes. The OpenAPI spec inventory (60 endpoints
under `/v1/...`) is thoroughbred-only by product design — sires, dams, damsires,
racecards, horses, jockey/trainer analysis. Zero endpoints for harness or greyhound. The
probe report's empirical finding (Albion Park harness and Wentworth Park greyhound
returned no meets from `/australia/meets`) is consistent: it's not a missing endpoint, it
is a thoroughbred-only product. §2.10 §3 frames Racing API value with that asymmetry as a
structural product limit, not a gap.

### §1.4 What feeds §2.10

Three load-bearing inputs:

- **Probe report** (`dr029/2_1_race_data/api_probe_report.md`). The substantive feed.
  Probe captured 25 867 Betfair MarketBook snapshots and 401 Racing API responses across
  four races (2 thoroughbred, 1 harness, 1 greyhound) on 2026-05-02. §3.3 of the report
  enumerates eight-plus Betfair API fields the writer doesn't currently capture; §3.5
  documents Racing API surface for thoroughbred. §2.10 §2 and §3 build directly on
  these.
- **Racing API OpenAPI spec** (`openapi.json` at rebuild root). Endpoint inventory plus
  per-endpoint schemas. Confirms thoroughbred-only coverage and surfaces the
  breeding/connections/analysis endpoints not yet touched by the orchestrator
  (`subscription/racing_api.py`).
- **Current snapshot-writer column set.** Per `data_layer_current.md` §4.4 plus the
  `bsp_price` orphan-column finding from inspection §F. Defines the "currently captured"
  baseline against which the inventory's bucket-3 classifications are decided.

### §1.5 What §2.10 produces

Three load-bearing outputs:

- **Bucket-1 list** — fields to wire into the snapshot writer. Read by v3 build-proper
  capture work. Each entry carries field name, source API, capture-cheapness rationale,
  and value rationale.
- **Bucket-2 list** — fields parked with rationale. Read at v3 capture decisions where
  the rationale might have changed (credential upgrade, vendor change, cadence shift
  enabling new capture paths).
- **Forward-routing and carry-forward inputs.** Three named handoffs: (i) Fix 4 cadence
  brief substrate (CLOSED-stop marker, INTENSIVE-tier segmentation candidates, greyhound
  POST_START cadence delta — all called out in probe report §5 and routed forward, not
  re-specified here); (ii) post-DR-029 Racing API value assessment (with thoroughbred-only
  scope clarified); (iii) post-DR-029 full-ladder credential upgrade question
  (`EX_LADDER` is observably out of reach on current Betfair app key per probe finding
  (a)).

The combined outputs feed into the DR-029 close-out governance paragraph as one of the
named pieces alongside the three pieces of v3-carried debt, periodic data-fitness
re-verification, operational/analytical line discipline, and §2.7's versioning
discipline.

---

## §2 Betfair API field inventory

### §2.1 Inventory baseline

This section enumerates Betfair Exchange API fields that the snapshot writer either
captures, doesn't capture but could cheaply, or doesn't capture and shouldn't (or can't).
Source: probe report §3.3 (per-field availability matrix) plus probe report §4
(surprises), both built on 25 867 MarketBook snapshots across all three racing codes.

The baseline against which the inventory is judged: the current snapshot writer's column
set per `data_layer_current.md` §4.4. That set covers identifiers (`race_id`, `runner_id`,
`snapshot_time`, `is_final_snapshot`, `snapshot_batch_id`), market state (`market_status`,
`runner_status`, `last_match_time`, `total_matched`), exchange ladder snapshot
(`best_back_price/size`, `best_lay_price/size`, top-3 depth in `back_depth_json` /
`lay_depth_json`), SP projection fields (`sp_near_price`, `sp_far_price`, `bsp_price` —
the orphan column), plus writer-derived fields (`snapshot_phase`, `minutes_to_start`,
`matched_amount`, `num_priced_runners`).

Field disposition follows §2.10's three-bucket framing per §1.1: **capture** (available,
not captured, cheap), **park** (available but expensive, or not available), **already
covered** (no action). One field per row, one disposition per field.

### §2.2 High-value capture candidates

Five fields where the gap between "what the API exposes" and "what the writer captures"
maps to clear operational or analytical value. All are cheap — single-key reads from the
existing projection set, no extra API calls, no extra projections.

**`sp.actualSP` — runner-level. Bucket: capture.**

**Note:** `sp.actualSP` is Betfair's internal API name for the **Betfair Starting Price
(BSP)** — the realised SP value once the market reconciles at jump. They are the same
field. The `bsp_price` column already exists in `betfair_snapshots` (the orphan column
from inspection §F); this capture populates it. This is one capture, not two.

Probe report §3.1 confirms 100% population for active runners from SUSPENDED-onset across
all three codes, persisting through the 45-min CLOSED tail. NaN for REMOVED runners.
Capture mechanism per probe report §4(b): ensure `SP_AVAILABLE` is in the projection set
alongside `SP_TRADED`; the `sp` container then surfaces on closed runners and `actualSP`
is reachable. NaN-guard required (`isinstance(value, (int, float)) and value > 0` —
`value is not None` is insufficient because Betfair returns Python `NaN` not `null`).

Operational value: BSP is the canonical settlement reference for any Strategy 1 cycle
that runs through Betfair Win markets. Currently inferred indirectly post-settlement.
Direct capture closes the loop. Analytical value: BSP is the calibration anchor for the
racing EV model's Harville exponents (γ=0.77, δ=0.62, ε=0.48 per the racing EV model
project's calibrated state); model-recalibration on fresh capture data needs BSP per row.
BSP is also the comparison anchor for the SP-projection accuracy study flagged in §5
(predicted-vs-realised study uses already-captured `sp.nearPrice`/`sp.farPrice` plus
`actualSP`).

**`removalDate` — runner-level. Bucket: capture.**

Timestamp at which a runner was scratched. Currently the writer infers scratch state from
`runner_status == REMOVED` only; the timestamp is unknown. `removalDate` makes
late-scratch handling authoritative rather than heuristic. Probe report §3.3 lists this
as a high-value writer gap.

Operational value: late scratches affect promo eligibility (insurance refunds, free-bet
triggers) and operator-side decision context at the burst window. Knowing precisely
*when* a scratch happened against the operator's bet timestamp is the difference between
"bet placed before scratch" and "bet placed after scratch but during ingestion lag."
Edge case: soft-book bet logged just before a Betfair-side scratch fires is handled by
existing burst-review workflow per `architecture.md` §D12 (Betfair as canonical runner
identity); `removalDate` provides the authoritative timestamp for operator triage in that
case.

**`adjustmentFactor` — runner-level. Bucket: capture.**

Betfair's own deduction factor applied to remaining runners when a runner is scratched.
Currently the operator's downstream code computes deduction effects manually.
`adjustmentFactor` is the API's own canonical value for Betfair-settled bets.

Note: industry-standard deduction-factor rule applies, but exact deduction factors per
scratch can differ between Betfair and soft books because the calculation is sensitive to
the scratched runner's price relative to the field at scratch-time, and Betfair vs
soft-book prices may diverge slightly at that moment. Capture provides Betfair's
canonical value; soft-book deductions still need their own handling. Operational value:
cleaner Betfair-side settlement reconciliation when scratchings occur during a race-card.
Analytical value: removes a category of computation drift between operator code and
Betfair's actual market-clearing.

**`inplay` — top-level (market-level). Bucket: capture.**

Bool, true once the race is running. Currently the writer derives in-play state from
`minutes_to_start` (writer-derived from `marketTime`). `inplay` is the authoritative
market-level signal — clean OPEN-pre-jump vs OPEN-in-running boundary.

Operational value: phase-classification accuracy. The writer's `snapshot_phase` field
currently uses `minutes_to_start` thresholds, which drift relative to actual race state
(early/late jumps). Authoritative `inplay` replaces inference. Direct UI value: v3's
racing and sports pages can surface "race jumped" / "event started" markers from
authoritative `inplay` rather than time-threshold inference.

**`betDelay` — top-level (market-level). Bucket: capture.**

Seconds of bet delay applied to in-play orders. Per Betfair's canonical definition, "the
number of seconds an order is held until it is submitted into the market. Orders are
usually delayed when the market is in-play." Pre-jump value is 0; flips to a positive
small integer (typically 1–5) once the race goes in-play.

AU regulation context: Australian regulations prohibit live online betting on most events
(call-in requirement). v3's day-to-day operational value of `betDelay` is consequently
low — in-play bet entry from the platform isn't a near-term capability. Capture justified
on two grounds: (i) cheap (single int per snapshot); (ii) historical signal substrate for
PASSIVE bet-delay model handling (parked as v3.1+ capability per `current_state.md` open
items). When v3.1+ work activates against historical data, the signal needs to have been
captured at the time. Cost of capture-now is trivial; cost of retrospective capture is
infinite (Betfair doesn't backfill historical `betDelay` values).

### §2.3 Lower-value but cheap capture candidates

Four fields where capture is mechanically cheap but operational value is more limited.
Recommend capture for inventory completeness — the cost is one extra column read per
snapshot — but flagged as lower-priority than §2.2.

**`version` — top-level. Bucket: capture.**

Per Betfair's canonical definition: "The version of the market. The version increments
whenever the market status changes, for example, turning in-play, or suspended when a
goal is scored." This is a **state-change signal**, not a tick-level change-detection
signal. The version increments on structural transitions (OPEN → SUSPENDED → CLOSED,
in-play turning, market-suspension events) rather than on every price move.

Capture value: structural state-transition detection without parsing `market_status`
strings. Useful for cadence-tier design (Fix 4 may consume `version` deltas as the "this
snapshot crossed a state boundary" signal that authorises a deeper inspection or write).
Not the deduplication signal for tick-level skip-writes — for that, content hashing or
`lastMatchTime` comparison are the right shape. The CLOSED-stop marker (operator-flagged)
is the right mechanism for the CLOSED-tail capture-waste problem.

**`totalAvailable` — top-level. Bucket: capture.**

Per Betfair's canonical definition: "The total amount of orders that remain unmatched."
Complement to existing `total_matched`: where `total_matched` is liquidity that's already
been used (bets with counterparties), `totalAvailable` is unmatched liquidity sitting in
the order book waiting to be matched.

Strategy 4 (Synthetic Each-Way) is the natural consumer when it activates — thin-margin
value betting needs to know the actual matchable size at a given price level, which the
top-3 depth in `back_depth_json` / `lay_depth_json` doesn't capture in aggregate. Capture
now means data is in place when Strategy 4 activates.

**`sp.backStakeTaken` / `sp.layLiabilityTaken` — runner-level. Bucket: capture (pair).**

Per-runner SP-pool exposure. `sp.backStakeTaken` is the aggregate stake committed to the
SP back side for the runner (people backing at SP); `sp.layLiabilityTaken` is the
aggregate liability committed to the SP lay side (maximum loss exposure to SP layers).
Together they describe the SP-pool composition that feeds Betfair's SP reconciliation
algorithm at jump-time.

Important framing: these fields are the **underlying inputs** to Betfair's own SP
projection (`sp.nearPrice` / `sp.farPrice`, already captured per §2.7 below). The
projection itself is what tells you "where will the SP land"; `backStakeTaken` /
`layLiabilityTaken` tell you "what's the SP-pool composition behind that projection." Use
case is interrogating *why* a projection is what it is, or building divergent projection
logic that diverges from Betfair's own.

The v3 build-proper UI candidate logged in §5 covers the dual surface: headline
`sp.farPrice` projection (already captured) plus optional SP-pool interrogation panel
using `backStakeTaken`/`layLiabilityTaken` for composition analysis.

### §2.4 Park with rationale — credential gap

**`EX_LADDER` projection (per-price/per-size traded ladder). Bucket: park.**

The single largest capture gap, parked rather than captured. Probe report §4(a):
`EX_LADDER` is **structurally rejected** on the current Betfair app key. Every combined
call carrying `EX_LADDER` returned `{'code': -32602, 'message': 'DSC-0018'}` instantly
(median ~80 ms response). Every ladder-only fallback returned the same. The rejection
fired uniformly across all four races and all three codes within the first second — this
is an authorisation-level rejection, not a per-market or transient rejection. The current
app key is not entitled to ladder data at all.

Parking rationale: capture requires either a Betfair credential upgrade (entitlement
change against the current app key) or an alternative data source. Both are non-trivial
strategic decisions sitting outside DR-029's scope.

Routed forward as a **post-DR-029 follow-on item**: full-ladder credential upgrade
question — assess what tier or product change unlocks `EX_LADDER`, what it costs, and
what analytical work it would enable that the bucket-1 captures don't. Operator-side
parallel action: contact Betfair to confirm entitlement gating and pricing for
`EX_LADDER` access.

### §2.5 Park with rationale — extra projection cost

**`ex.tradedVolume` (per-runner traded-volume distribution by price level). Bucket: park,
with re-evaluation trigger.**

Per-runner traded volume across the order book, broken down by price level. Probe report
§4(h): structurally present per runner in the API response (key always there) but always
empty `[]` on the reduced projection set. Per Betfair documentation, populating
`ex.tradedVolume` requires adding the `EX_TRADED_VOLUME` projection to the request.

Note: separate from runner-level aggregate `runners[*].totalMatched` (per-runner traded
volume aggregate), which is reachable on the existing projection set per probe report
§3.3 and sits in bucket-1 as the runner-level total-matched capture. `ex.tradedVolume` is
the per-price breakdown of that aggregate — a strictly larger payload.

Parking rationale: not free. Adding `EX_TRADED_VOLUME` to every snapshot increases
per-call payload size and may push the orchestrator's per-second call budget into
rate-limit territory at INTENSIVE/POST_START cadence. The cost-vs-benefit assessment
needs Fix 4's cadence-tier design to be settled first — once cadence is known, the
incremental cost of `EX_TRADED_VOLUME` is calculable.

Re-evaluation trigger: after Fix 4 closes. If Fix 4's cadence design has headroom,
`ex.tradedVolume` returns to bucket-1 candidacy. Logged in §5 as a Fix-4-dependent
re-evaluation item, not a permanent park. Operator-side parallel action: contact Betfair
to confirm whether `EX_TRADED_VOLUME` projection is entitlement-gated separately or
purely a payload-cost question.

### §2.6 Park with rationale — low operational value

**`bspReconciled` — top-level bool. Bucket: park, low value.**

Per Betfair's canonical definition: "True if the market starting price has been
reconciled." Probe report §4(e) surprise: `bspReconciled` was True throughout the
captured window even pre-jump (~45–60 minutes before scheduled jump). The flag flipped
True at some point earlier than the expected SUSPENDED→CLOSED transition. Two possible
mechanisms: (a) Betfair reconciles a pre-race "indicative SP" early in the pre-jump
window and flips the flag at that point (consistent with how `sp.nearPrice`/`sp.farPrice`
operate as pre-jump SP projections); or (b) the flag is sticky from the prior race-day's
reconciliation and isn't a meaningful per-market signal. The canonical definition doesn't
disambiguate between these.

Parking rationale: the flag is not the BSP-availability gate the field name suggests.
The actual operational gate for "actualSP is now safe to read" is `market_status in
(SUSPENDED, CLOSED)` plus the NaN-guard, both of which the writer already has access to.
Capturing `bspReconciled` adds a column with no clear consumer. Cost is trivial (one bool
per snapshot) but no benefit identified. Park unless a downstream consumer surfaces.

### §2.7 Already covered — no action

The probe report §2 enumerated 17 distinct runner-level keys and 18 distinct top-level
keys. The fields the writer already captures (per §2.1's baseline list) are the
identifier surface (`selectionId` → `runner_id`, `marketId` → `race_id` join), market
state (`status`, `numberOfActiveRunners`, `lastMatchTime`, `totalMatched`), exchange
ladder snapshot (top-3 of `ex.availableToBack` / `ex.availableToLay`, surfaced as
`back_depth_json` / `lay_depth_json`), and the SP projection pair (`sp.nearPrice`,
`sp.farPrice`, wired through cleanly per Fix 3 §3.1 with 100%/95% INTENSIVE/STANDARD
population post-restart).

**Note on `sp.nearPrice` / `sp.farPrice` value.** These are Betfair's own predicted SP
values, calculated and updated continuously through the pre-jump window. `nearPrice` is
the projected SP using the current SP pool plus available exchange orders; `farPrice` is
the projected SP using only the SP-pool money (back stakes vs lay liabilities), generally
considered the better forward-looking indicator because it's based on money committed to
SP reconciliation rather than money sitting in unmatched exchange orders. Both populate
through STANDARD/INTENSIVE/POST_START, drop at SUSPENDED-onset when the `sp` container
shape-shifts (per probe report §2). Both are dual-use:

- **Operational use** — direct value-identification signal on race and sports pages. When
  `farPrice` materially diverges from current best back/lay, that's drift-direction
  substrate for Strategy 2 (Price Booster) and value identification more generally. v3
  build-proper UI candidate logged in §5.
- **Analytical use** — substrate for Betfair-SP-projection accuracy study (predicted SP
  vs realised SP by minutes-to-jump, segmented by code/venue/field-size/liquidity). The
  capability lands automatically once `sp.actualSP` capture wires in (bucket-1 above);
  no new capture work needed. Logged in §5 as a post-DR-029 analytical capability
  candidate.

**Three runner-level fields are excluded from any bucket** because they carry no signal
on AU WIN markets:

- `handicap` — always 0.0 on AU WIN markets. Probe report §3.3.
- `numberOfRunners` (top-level) — constant per market; redundant with race-level metadata
  the writer already carries.
- `numberOfWinners` (top-level) — always 1 on WIN markets.

`runnersVoidable`, `crossMatching`, `complete`, `isMarketDataDelayed` are top-level bools
captured by the probe but with no observable variation across the captured window
(complete=True, crossMatching=True, isMarketDataDelayed=False, runnersVoidable=False on
every snapshot). Park-equivalent: not formally bucketed because their operational value
is contingent on observing variation, which the probe didn't surface. Re-evaluate if a
multi-day probe ever runs.

### §2.8 Summary

**Bucket 1 (capture):** `sp.actualSP` (= BSP, populates the existing orphan `bsp_price`
column), `removalDate`, `adjustmentFactor`, `inplay`, `betDelay`, `version`,
`totalAvailable`, `sp.backStakeTaken`, `sp.layLiabilityTaken`. Nine fields. All cheap,
all reachable on the existing projection set.

**Bucket 2 (park with rationale):** `EX_LADDER` (credential gap, post-DR-029 follow-on);
`ex.tradedVolume` (extra-projection cost, Fix-4-dependent re-evaluation); `bspReconciled`
(probe-vs-definition mismatch, no consumer identified).

**Bucket 3 (already covered):** identifier surface, market state, exchange ladder
snapshot, SP projection pair (`sp.nearPrice` / `sp.farPrice`). The SP projection pair
carries dual operational + analytical value flagged forward to §5.


---

## §3 Racing API field inventory

### §3.1 Inventory baseline

This section enumerates The Racing API endpoints and per-endpoint fields against the
current orchestrator's consumption pattern. Source: `openapi.json` (60 endpoints across
`/v1/...`); probe report §3.5 (Racing API observed shape on the two thoroughbred races);
current orchestrator code path (`subscription/racing_api.py:_sync_single_race`).

**Structural framing:** Racing API is thoroughbred-only by product design. The endpoint
inventory contains zero harness or greyhound endpoints; the vocabulary itself (sires,
dams, damsires, racecards, horses, jockey/trainer analysis) is thoroughbred-specific.
This is a product limit, not a capture decision. §3.3 logs the harness/greyhound
non-availability formally; §3.2's per-field disposition decisions apply to thoroughbred
data only.

**Currently captured baseline.** Per `subscription/racing_api.py`, the orchestrator
currently calls one endpoint pattern: `/v1/australia/meets?date=YYYY-MM-DD` followed by
per-race meta sync via `/v1/australia/meets/{meet_id}/races/{race_number}` (probe
report §3.5 confirms shape). Fields landing in `capture.db` today:

- Race-level: `meet_id`, `course`, `race_number`, `off_time` (scheduled jump), basic race
  metadata (distance, surface, class where surfaced).
- Runner-level: `horse` (name), `horse_id`, `barrier`, `weight`, `jockey`, `trainer`,
  basic form indicators, `scratched` flag.
- Bundled bookmaker odds: `runner.odds[]` array carrying `{bookmaker, win_odds,
  place_odds}` pairs for Sportsbet and Ladbrokes per active runner. 30-second cadence.

Bucket-3 (already covered) for §3 is bounded to that subset. Everything else Racing API
exposes — breeding lineage, jockey/trainer/owner analysis, course-level statistics,
results-with-time-detail — sits outside current capture.

### §3.2 Available + not currently captured

Three field clusters where Racing API exposes data the orchestrator doesn't currently
pull. Per-cluster disposition.

**Cluster A — Result enrichment from `/v1/results/{race_id}`. Bucket: capture.**

Probe report §3.5 surfaced two thoroughbred-side fields available post-race that the
writer doesn't capture:

- **`winning_time_hundredths`** — race-completion time at hundredths-of-second precision.
  Betfair doesn't expose this; Racing API does. Operational value modest (post-race
  reference); analytical value direct (sectional-time-style features for racing EV model
  calibration where they're available, plus race-pace classification when `going` /
  `surface` / class are factored in).
- **Off-time confirmation** — Racing API publishes confirmed actual off-time post-race,
  distinct from scheduled `off_time`. Probe found perfect agreement with Betfair's
  `marketStartTime` on the two thoroughbred races, but capturing the Racing API
  confirmation gives a cross-source check for any case where the two diverge (early/late
  jumps where Betfair's `inplay` flip-time doesn't match Racing API's recorded off).
  Pairs cleanly with the bucket-1 `inplay` capture from §2.

Capture cost: low. The `/v1/results/{race_id}` endpoint is one call per race
post-completion, on the existing thoroughbred path. No incremental rate-limit pressure.

**Cluster B — Bundled-bookmaker breadth. Bucket: capture (with caveat).**

Racing API's `runner.odds[]` array currently surfaces Sportsbet and Ladbrokes per the
orchestrator's observed shape. Whether the array can carry more bookmakers depends on
Racing API's plan tier and add-on structure, which is not surfaced cleanly in
`openapi.json`'s schema (per §3 of `external_api_resources.md`, rate limits and tier
gating are embedded in description HTML rather than schema fields).

Disposition note: marginal value today (current promo-exploitation operations don't
consume bundled-bookmaker odds operationally), but Sportsbet and Ladbrokes are
operationally relevant books for promo coverage. The current bundled feed becomes a
candidate substrate for the future operational soft-book layer (deferred Session 69 per
`dr029_scope.md` §3.11) when that layer activates as a fresh DR. For §2.10's purpose:
log "Racing API bundled-bookmaker breadth needs verification at value-assessment time"
and flag the substrate to §5 for the future operational soft-book DR. Capture the
existing two bookmakers as the orchestrator already does (bucket-3); the breadth question
returns when the consumer activates.

**Cluster C — Breeding lineage, connections analysis, course-level statistics. Bucket:
capture-routing-deferred.**

Racing API exposes a substantial set of endpoints the orchestrator doesn't currently
call:

- **Breeding lineage:** `/v1/sires/...`, `/v1/dams/...`, `/v1/damsires/...` — pedigree
  tree, progeny analysis by class, by distance, results history.
- **Connections analysis:** `/v1/jockeys/{id}/analysis/...`,
  `/v1/trainers/{id}/analysis/...`, `/v1/owners/{id}/analysis/...` — historical
  performance segmented by course, distance, owner-trainer pair, jockey-trainer pair,
  horse age.
- **Horse-level analysis:** `/v1/horses/{id}/analysis/distance-times`,
  `/v1/horses/{id}/results`, plus standard/pro racecard variants.
- **Course-level statistics** via the various `analysis/courses` sub-paths.

Operational value to v3: low to none. None of these fields drives bet-entry, settlement,
or burst-window decision support — they're all backward-looking analytical surfaces.
Operationally overkill for promo exploitation (Strategy 1 / Strategy 2, currently 100%
of operator profit).

Analytical value: substantial, but for `bethub-analytical/` not `capture.db`, and only
when deep market analysis on runner/horse fundamentals activates. Future-state
substrate for Strategy 4 (Synthetic Each-Way) place-market modelling and any forward
Harville recalibration with breeding/connections features. The
`bethub-analytical/racing_ev_calibration/` activation (currently sequenced second after
AFL SGM per `external_api_resources.md` §3) is the natural consumer.

Disposition: **capture-routing-deferred.** §2.10 logs availability and analytical
suitability; routing decision (capture into `capture.db` for joint operational/analytical
use vs capture into `bethub-analytical/` directly via on-demand pulls) is deferred to
whichever project activates first and can answer it from concrete need. Trigger
condition for re-activation: a strategy or analytical project surfaces concrete
requirement for breeding/connections/course-analysis features. Recorded in §5 as a
forward-routing item to the relevant analytical activation.

### §3.3 Park with rationale — non-thoroughbred coverage gap

**Harness racing endpoints. Bucket: park, structural product limit.**

Racing API has zero endpoints for harness racing. The OpenAPI spec inventory (60
endpoints under `/v1/...`) contains no harness-specific paths; vocabulary scan against
"harness", "trot", "standardbred" returns zero matches. The probe report's empirical
finding (Albion Park harness Saturday metro returned no meets from `/australia/meets`) is
consistent with this: it's not a missing endpoint, it's a thoroughbred-only product.

Parking rationale: structural product limit, not addressable through configuration,
credential, or endpoint changes against current Racing API. Routes to vendor-alternative
question if harness analytical capability ever becomes operationally needed. No current
Strategy directly requires harness analytical data; harness racing today is operational
on Strategy 1 (insurance) and Strategy 2 (price boosters), neither of which needs the
analytical-capture surfaces Racing API would provide for thoroughbreds.

**Greyhound racing endpoints. Bucket: park, structural product limit.**

Same shape as harness. Zero Racing API endpoints; probe-empirical confirmation
(Wentworth Park greyhound Saturday metro returned no meets); thoroughbred-only product
by design.

Parking rationale identical: structural, not addressable. Cross-source join for greyhound
race identity reconciliation (probe report §5 question) requires either an alternative
vendor or remains a "Betfair-only" identity surface for greyhound. Logged to §5 for
post-DR-029 review if greyhound analytical work ever surfaces requirements.

### §3.4 Already covered — no action

Per §3.1 baseline: the meets-and-races thoroughbred endpoint pattern, race-level metadata
(course, off_time, distance, class), runner-level metadata (horse, barrier, weight,
jockey, trainer, scratched flag), and the bundled two-bookmaker odds array (Sportsbet +
Ladbrokes win/place pairs). All currently captured by `subscription/racing_api.py` at
30-second cadence.

### §3.5 Summary

**Bucket 1 (capture):** Cluster A result enrichment — `winning_time_hundredths` and
confirmed off-time from `/v1/results/{race_id}`. One incremental endpoint per
thoroughbred race post-completion. Two fields.

**Bucket 1 with routing deferred:** Cluster C breeding lineage / connections analysis /
course-level statistics. Substantial available surface; routing between `capture.db` and
`bethub-analytical/` deferred to whichever analytical project activates first against
concrete deep-market-analysis requirement. Logged forward to §5.

**Bucket 2 (park with rationale):** Harness endpoints (structural product limit);
greyhound endpoints (structural product limit). Bundled-bookmaker breadth flagged to §5
as future operational soft-book DR substrate.

**Bucket 3 (already covered):** Meets-and-races thoroughbred endpoint pattern; race and
runner metadata; bundled two-bookmaker odds (Sportsbet + Ladbrokes).

**Cross-Racing-API-and-Betfair note:** §2 (Betfair) and §3 (Racing API) together resolve
the cross-source-join question for thoroughbred (feasible today on `(date, venue,
race_number)` per probe report §3.5) and for harness/greyhound (not feasible via Racing
API; remains Betfair-only identity surface per §3.3 above). §4 carries the bucket
classifications forward into a single combined disposition table.


---

## §4 Combined disposition table

### §4.1 Bucket-1 capture list — combined

The consolidated capture list across both APIs. Eleven fields total (nine Betfair,
two Racing API), plus one routing-deferred cluster. Tier labels per §2.10 framing
(high-value / lower-value / result-enrichment / capture-routing-deferred) preserve
section-level context without imposing artificial cross-API numeric ordering. Read by
v3 build-proper capture work as the primary "fields to wire in" input.

| Field | Source | Tier | Capture mechanism | Value summary |
| :-- | :-- | :-- | :-- | :-- |
| `sp.actualSP` | Betfair | high-value | Add `SP_AVAILABLE` to projection set; read post-SUSPENDED with NaN-guard; write to existing `bsp_price` orphan column | BSP — canonical settlement reference for Strategy 1 cycles; calibration anchor for Harville model; comparison anchor for SP-projection accuracy study |
| `removalDate` | Betfair | high-value | Single-key read on runner; available across all phases | Authoritative scratch timestamp; replaces `runner_status == REMOVED` heuristic; pairs with bet-vs-scratch timing reconciliation |
| `adjustmentFactor` | Betfair | high-value | Single-key read on runner | Betfair's canonical deduction factor for Betfair-side settlement reconciliation |
| `inplay` | Betfair | high-value | Single-key read at top-level | Authoritative race-jumped / event-started signal; replaces `minutes_to_start` threshold inference; UI flip-marker on race/sports pages |
| `betDelay` | Betfair | high-value | Single-key read at top-level | Historical signal substrate for v3.1+ PASSIVE bet-delay model handling; AU regs limit current operational use |
| `sp.backStakeTaken` | Betfair | high-value | Single-key read on runner | SP-pool back composition; substrate for lead-indicator price-direction signals on v3 race/sports pages — paired with already-captured `sp.nearPrice`/`sp.farPrice`, gives operational read on where the market is heading before standard exchange prices catch up. Direct Strategy 2 (Price Booster) profit-line input |
| `sp.layLiabilityTaken` | Betfair | high-value | Single-key read on runner | SP-pool lay composition; pairs with `backStakeTaken` for lead-indicator price-direction reads. Same operational framing — Strategy 2 lead-indicator substrate, not analytical-only |
| `version` | Betfair | lower-value | Single-key read at top-level | State-change signal (status transitions); not tick-level skip-write |
| `totalAvailable` | Betfair | lower-value | Single-key read at top-level | Total unmatched liquidity market-wide; complement to existing `total_matched`; substrate for Strategy 4 when activated |
| `winning_time_hundredths` | Racing API | result-enrichment | Add `/v1/results/{race_id}` call post-race-completion on existing thoroughbred path | Race-completion time at hundredths precision; not exposed by Betfair; sectional-pace analytical substrate |
| Confirmed off-time | Racing API | result-enrichment | Same call as above; `off_time` field on result response | Cross-source check vs Betfair `marketStartTime`; pairs with bucket-1 `inplay` for jump-time reconciliation |

**Routing-deferred cluster (logged but not assigned to bucket-1 today):**

- **Racing API breeding / connections / course analysis** — Cluster C from §3.2.
  Substantial endpoint surface (sires, dams, damsires, jockey/trainer/owner analysis,
  course-level statistics, horse-level analysis). Operational value to v3 low to none;
  analytical value substantial but for `bethub-analytical/`, not `capture.db`.
  Capture-routing decision deferred to whichever analytical project activates first
  against concrete deep-market-analysis requirement. Logged in §5 forward-routing.

### §4.2 Bucket-2 park list — combined

Five parked items across both APIs. Each carries parking rationale and re-evaluation
trigger; some have operator-side parallel actions logged forward to §5.

| Item | Source | Park reason | Re-evaluation trigger |
| :-- | :-- | :-- | :-- |
| `EX_LADDER` per-price/per-size traded ladder | Betfair | Authorisation-level rejection on current app key (DSC-0018 across all probe markets); credential entitlement gap | Post-DR-029 credential upgrade decision; operator-side Betfair contact for entitlement and pricing |
| `ex.tradedVolume` per-runner traded-volume distribution by price level | Betfair | Requires extra `EX_TRADED_VOLUME` projection; payload-size cost not free at INTENSIVE/POST_START cadence | After Fix 4 cadence design closes — incremental cost calculable once cadence-tier headroom known |
| `bspReconciled` top-level bool | Betfair | Probe-vs-canonical-definition mismatch; flag isn't the BSP-availability gate the name suggests; no consumer identified | Downstream consumer surfaces (none currently anticipated) |
| Racing API harness endpoints | Racing API | Structural product limit — Racing API is thoroughbred-only by product design; zero harness endpoints exist | Vendor-alternative search if harness analytical capability ever becomes operationally required |
| Racing API greyhound endpoints | Racing API | Same structural product limit as harness | Vendor-alternative search if greyhound analytical work surfaces requirements |

**Flagged-but-not-parked items:**

- **Racing API bundled-bookmaker breadth.** The current Sportsbet + Ladbrokes pair is
  captured (bucket-3); whether more bookmakers are available depends on Racing API
  plan-tier and add-on structure. Flagged forward to §5 as substrate for the future
  operational soft-book DR — when that DR activates, the breadth question feeds the
  consumer-surface design.

### §4.3 Cadence-dependence callout

§2.10's "capture-cheap" classification is judged at the cadence the orchestrator
currently runs (5-minute STANDARD, 60-second INTENSIVE per `capture/scheduler.py`,
1-second on the probe's measurement window). Cadence design is Fix 4's territory; if
Fix 4 shifts cadence materially, two effects on §4 become possible:

- **Bucket-1 entries may shift to bucket-2.** A field that's cheap at 60-second
  INTENSIVE may become expensive at 1-second INTENSIVE — payload size compounds linearly
  with cadence. None of the bucket-1 entries in §4.1 are obvious candidates for shifting
  (all are single-key reads on existing projection-set responses, not new projections).
  But the assessment is cadence-conditional and revisable.
- **Bucket-2 entries may shift to bucket-1.** The single explicit case is
  `ex.tradedVolume` (§4.2): the parking rationale is payload-size cost at
  INTENSIVE/POST_START cadence; if Fix 4's cadence design has headroom, the field
  returns to bucket-1 candidacy. This is the single documented Fix-4-dependent
  re-evaluation trigger.

**Forward-routing implication.** §5 carries the explicit re-evaluation triggers (Fix 4
close → `ex.tradedVolume` re-eval; post-DR-029 credential decision → `EX_LADDER`
re-eval; future operational soft-book DR → bundled-bookmaker breadth re-eval; analytical
project activation → Cluster C routing decision). No re-evaluation is automatic; each
trigger surfaces a concrete decision point with §2.10 inventory as substrate.

### §4.4 Combined-table summary

**Bucket 1 (capture):** 11 fields plus 1 routing-deferred cluster.

- 7 Betfair high-value fields driving operational and settlement clarity (BSP,
  authoritative scratch timestamp, deduction factor, in-play marker, bet-delay
  historical signal, SP-pool composition pair as Strategy 2 lead-indicator substrate).
- 2 Betfair lower-value fields filling out structural state-change detection (version)
  and market-wide unmatched liquidity (totalAvailable).
- 2 Racing API result-enrichment fields on the existing thoroughbred path
  (winning_time_hundredths, confirmed off-time).
- 1 Racing API routing-deferred cluster (breeding / connections / course analysis)
  pending analytical project activation.

**Bucket 2 (park with rationale):** 5 items.

- 1 credential-gated Betfair item (EX_LADDER) with operator-side parallel action.
- 1 cadence-dependent Betfair item (ex.tradedVolume) with Fix 4 re-evaluation trigger.
- 1 low-consumer-value Betfair item (bspReconciled) with no anticipated re-evaluation.
- 2 structural Racing API gaps (harness, greyhound endpoints) with vendor-alternative
  re-evaluation trigger if analytical capability needed.

**Bucket 3 (already covered):** identifier surfaces, market state, exchange ladder
top-3 depth, SP projection pair (`sp.nearPrice` / `sp.farPrice` — both dual-use
operational + analytical per §2.7), Racing API meets-and-races thoroughbred pattern
plus bundled two-bookmaker odds.

The combined disposition feeds §5 forward-routing and §6 close-out summary.


---

## §5 Forward-routing and carry-forward items

### §5.1 Fix 4 cadence brief substrate

Fix 4 (Racing API and Betfair Streaming cadence design) consumes §2.10's bucket-1
captures alongside probe report §3.4's cadence-of-meaningful-change numbers. Substrate
flagged forward:

- **CLOSED-stop marker (operator-flagged Session 76).** Probe report §3.4 confirms 0%
  change rate across the full 45-min CLOSED tail. Fix 4 should specify a stop-capture
  marker on SUSPENDED→CLOSED transition with a small post-CLOSED window for
  `actualSP`-availability verification (probe report §5 suggests 5 minutes), then
  capture stops for that race. Eliminates wasted API calls and `capture.db` writes on
  static CLOSED markets.
- **INTENSIVE-tier segmentation candidates.** Probe report §3.4 shows 40–70% change rate
  across INTENSIVE phase. Operator flagged Session 76 that segmentation within INTENSIVE
  may be warranted (different cadence at T-5min vs T-1min). Fix 4 design substrate, not
  §2.10 specification.
- **Greyhound POST_START cadence delta.** Probe report §3.1 shows greyhound markets
  transition OPEN → SUSPENDED faster than thoroughbred/harness; greyhound POST_START
  yields 0% `actualSP` populate where thoroughbred yields 52% and harness 60%. Fix 4
  should specify code-specific POST_START cadence rather than uniform-across-codes.
- **`ex.tradedVolume` re-evaluation trigger (§4.2).** After Fix 4 cadence design closes,
  re-assess whether `EX_TRADED_VOLUME` projection cost is bearable. If Fix 4's cadence
  design has headroom, `ex.tradedVolume` returns to bucket-1 candidacy. If not, parking
  rationale stands.

Fix 4 brief drafting itself is a separate non-gating quality work item per
`current_state.md` open items, expected post-DR-029-close. §2.10 hands the substrate
forward; Fix 4 owns the cadence specification.

### §5.2 v3 build-proper UI candidates

Three operational UI surfaces where §2.10 captures feed v3 build-proper UI design.
Logged for v3 build-proper, not specified inside §2.10:

- **Headline SP projection on race and sports pages.** Surface `sp.farPrice` (Betfair's
  own forward projection of where SP will land) alongside current best back/lay on the
  race/sports page row for each runner. Direct value-identification signal — when
  `farPrice` materially diverges from current best back, that's drift-direction
  substrate for Strategy 2 (Price Booster) and value identification more generally.
  Substrate already captured (`sp_near_price` / `sp_far_price` per Fix 3); UI work only.
- **SP-pool interrogation panel.** Optional drilldown surfacing
  `sp.backStakeTaken`/`sp.layLiabilityTaken` for the runner the operator is inspecting.
  Shows the SP-pool composition behind `farPrice` — useful when `farPrice` looks
  suspicious or operator wants to build divergent projection logic. Substrate lands via
  bucket-1 capture.
- **Race-jumped / event-started UI marker.** Surface authoritative `inplay` flip on
  race/sports pages so the operator sees the moment a race goes in-play rather than
  inferring from `minutes_to_start` thresholds. Substrate lands via bucket-1 capture.

All three are UI work against captured substrate, not new capture work. v3 build-proper
design owns the UI shape.

### §5.3 Post-DR-029 analytical capability candidates

Two analytical capabilities where the substrate is in place (or will be once bucket-1
lands) and the analytical work is downstream of DR-029 close. Logged for the analytical
project that consumes them:

- **Betfair SP-projection accuracy study.** Substrate: `sp.nearPrice` and `sp.farPrice`
  (already captured) paired with `sp.actualSP` (bucket-1 capture). Study shape:
  predicted SP vs realised SP as a function of minutes-to-jump, segmented by code,
  venue, field-size, liquidity. Validates Betfair's own SP projection accuracy and
  surfaces conditions where the projection is reliable vs unreliable. Builds against
  existing data layer once `actualSP` capture wires in; no additional capture work
  needed.
- **Racing EV model recalibration with §2.10 bucket-1 captures.** Harville exponents
  (γ=0.77, δ=0.62, ε=0.48 per the racing EV model project's calibrated state) were
  fit against an earlier capture state. Recalibration against fresh data including
  bucket-1 fields (`actualSP`, `removalDate`, `adjustmentFactor`,
  `winning_time_hundredths`) is a candidate for the racing EV calibration work in
  `bethub-analytical/racing_ev_calibration/` when that project activates (currently
  sequenced second after AFL SGM).

Both candidates are post-DR-029, downstream of v3 build-proper. §2.10 logs the substrate
availability; analytical work owns the study design.

### §5.4 Post-DR-029 strategic decisions

Four decisions deferred to post-DR-029 review, each with §2.10 inventory as substrate:

- **Racing API value assessment.** Whether Racing API's £49.99 GBP + AU regional
  add-on subscription is justified by what it uniquely provides for thoroughbreds.
  Substrate: §3 inventory (bundled-bookmaker odds, `winning_time_hundredths`, off-time
  confirmation, breeding/connections/analysis surfaces); thoroughbred-only scope
  clarified by §3.3 (zero harness or greyhound coverage by product design).
  Cost-benefit decision belongs to operator; §2.10 provides the inventory.
- **Full-ladder credential upgrade question (`EX_LADDER`).** Whether to pursue Betfair
  credential entitlement upgrade or alternative data source for full per-price
  per-size traded ladder data. Substrate: §4.2 parked-with-rationale entry plus
  operator-side Betfair contact response (§5.5). Decision triggers if/when ladder data
  becomes operationally or analytically required for a concrete strategy.
- **Future operational soft-book DR (bundled-bookmaker breadth).** Racing API's
  `runner.odds[]` array currently surfaces Sportsbet + Ladbrokes; whether more
  bookmakers are available depends on plan-tier and add-on structure. Substrate feeds
  the future operational soft-book DR (deferred Session 69 per `dr029_scope.md` §3.11)
  when that DR activates. Sportsbet and Ladbrokes are operationally relevant books for
  promo coverage; the bundled feed is candidate substrate for the consumer-surface
  design when concrete strategy requirements surface.
- **Cluster C routing decision (`capture.db` vs `bethub-analytical/`).** Racing API
  breeding lineage, connections analysis, course-level statistics are substantial
  analytical surface but operationally low-value for v3. Routing decision deferred to
  whichever analytical project activates first against concrete deep-market-analysis
  requirement. Trigger condition: a strategy or analytical project surfaces concrete
  requirement for breeding/connections/course-analysis features. Most likely triggers:
  Strategy 4 (Synthetic Each-Way) place-market modelling activation; forward Harville
  recalibration with breeding/connections features.

All four decisions are post-DR-029. §2.10 closes with the substrate in place; operator
makes the calls when triggers surface.

### §5.5 Operator-side parallel actions

Two operator-side actions running parallel to v3 build-proper, not gating any DR-029
deliverable:

- **Contact Betfair re: `EX_LADDER` entitlement and pricing.** Confirm whether
  full-ladder access is gated behind a credential tier upgrade, what tier or product
  change unlocks it, and what it costs. Response feeds §5.4 full-ladder credential
  upgrade decision. Operator-side homework; not Claude work.
- **Contact Betfair re: `EX_TRADED_VOLUME` projection cost and entitlement.** Confirm
  whether the projection is entitlement-gated separately or purely a payload-cost
  question. If purely payload-cost, response feeds Fix 4 cadence-design substrate
  (§5.1). If entitlement-gated, treats analogously to `EX_LADDER`. Operator-side
  homework; not Claude work.

Both flagged as operator-side actions in `current_state.md` open items at session
close.

### §5.6 Carry-forward into DR-029 close-out governance paragraph

§2.10's contribution to the DR-029 close-out governance paragraph alongside the
existing named pieces:

- The three pieces of v3-carried debt (no test coverage, no migration framework,
  monolithic orchestrator file).
- Periodic data-fitness re-verification cadence.
- Operational/analytical line discipline (Session 32 standing instruction).
- §2.7's API contract versioning discipline (Session 75 brief output).

§2.10 adds: **bucket-2 re-evaluation trigger discipline.** The five parked items in
§4.2 each carry an explicit re-evaluation trigger; v3 governance carries the trigger
discipline forward so parked items return to active scope when their conditions are
met (rather than being forgotten). Specifically: Fix 4 close triggers `ex.tradedVolume`
re-eval; post-DR-029 credential decision triggers `EX_LADDER` re-eval; future
operational soft-book DR triggers bundled-bookmaker breadth re-eval; analytical project
activation triggers Cluster C routing decision.

Substrate: §4.2 park list with re-evaluation triggers + §5.4 strategic-decision
framing.


---

## §6 What §2.10 closes for DR-029

### §6.1 What §2.10 locks

§2.10 locks the per-field disposition list across both APIs (Betfair Exchange API and
The Racing API), classified into three buckets per §1.1's framing:

- **Bucket-1 capture list (§4.1)** — 11 fields plus one routing-deferred cluster.
  Seven Betfair high-value fields (`sp.actualSP`, `removalDate`, `adjustmentFactor`,
  `inplay`, `betDelay`, `sp.backStakeTaken`, `sp.layLiabilityTaken`); two Betfair
  lower-value fields (`version`, `totalAvailable`); two Racing API result-enrichment
  fields (`winning_time_hundredths`, confirmed off-time); one routing-deferred Racing
  API cluster (Cluster C — breeding lineage, connections analysis, course-level
  statistics). Read by v3 build-proper capture work as the primary "fields to wire in"
  input.

- **Bucket-2 park list (§4.2)** — five items with explicit parking rationale and
  re-evaluation triggers. One credential-gated Betfair item (`EX_LADDER`); one
  cadence-dependent Betfair item (`ex.tradedVolume`); one low-consumer-value Betfair
  item (`bspReconciled`); two structural Racing API gaps (harness, greyhound endpoint
  coverage). Plus one flagged-but-not-parked item (Racing API bundled-bookmaker
  breadth) as future operational soft-book DR substrate.

- **Bucket-3 already-covered surfaces (§4.4)** — identifier surfaces, market state,
  exchange ladder top-3 depth, SP projection pair (`sp.nearPrice`/`sp.farPrice` —
  both dual-use operational + analytical per §2.7 with forward-routing flags to §5.2
  and §5.3), Racing API meets-and-races thoroughbred pattern, bundled two-bookmaker
  odds (Sportsbet + Ladbrokes).

- **Forward-routing matrix (§5)** — six handoffs across three time horizons. Fix 4
  cadence brief substrate (§5.1); v3 build-proper UI candidates (§5.2); post-DR-029
  analytical capability candidates (§5.3); post-DR-029 strategic decisions (§5.4);
  operator-side parallel actions (§5.5); DR-029 close-out governance contribution
  (§5.6).

- **Bucket-2 re-evaluation trigger discipline** as §2.10's contribution to the DR-029
  close-out governance paragraph. Each parked item carries an explicit re-evaluation
  trigger so parked items return to active scope when conditions are met rather than
  being forgotten.

### §6.2 What §2.10 unblocks

§2.10 is the last unwritten in-scope DR-029 deliverable per `dr029_scope.md` §2's
ten in-scope items. Closing §2.10 leaves two DR-029 critical-path items remaining
before v3 build proper:

- **Contract documentation files (`vps_client_contract.md` + `betfair_client_contract.md`)
  drafting** per §2.7 §5.4. Likely Code-bound brief shape for the developer-readable
  formal-spec section against §2.6 / §2.9 locked shapes; operator-readable summary in
  Chat. Required artefact before v3 build proper but not part of §2.7 itself. Approximately
  two-session work.

- **Close-out governance paragraph drafting.** Covers the named pieces: three pieces
  of v3-carried debt (no test coverage, no migration framework, monolithic orchestrator
  file); periodic data-fitness re-verification cadence; operational/analytical line
  discipline (Session 32 standing instruction); §2.7's API contract versioning
  discipline (Session 75 brief output); §2.10's bucket-2 re-evaluation trigger
  discipline (§5.6 above). Substrate is in place across the relevant artefacts; the
  drafting work is consolidating the framing.

After both items land, DR-029 closes and v3 build proper begins.

### §6.3 What §2.10 does not unblock

Six items remain explicitly out of §2.10's scope or downstream of DR-029 close:

- **v3 build proper.** Still gated on contract documentation files and close-out
  governance paragraph (per §6.2). §2.10 contributes the data-layer capture substrate
  but doesn't itself authorise v3 build start.

- **Fix 4 cadence brief drafting.** Non-gating quality work per `current_state.md`
  open items, expected post-DR-029-close. §2.10 hands cadence substrate forward (§5.1);
  Fix 4 owns the cadence specification itself. CLOSED-stop marker, INTENSIVE-tier
  segmentation, greyhound POST_START code-specific cadence, and `ex.tradedVolume`
  re-evaluation all wait on Fix 4.

- **Operational soft-book layer.** Deferred per `dr029_scope.md` §3.11. Returns as a
  fresh DR when strategy work surfaces concrete consumer-surface requirements.
  Bundled-bookmaker breadth question (§5.4) is substrate for that future DR, not
  unblocking §2.10 work.

- **Sports analytical capability.** Asymmetric architecture per principle 1.3
  (`dr029_scope.md` §1.3) — sports operational reads via `betfair_client` direct, no
  analytical capture in `capture.db`. §2.10's racing-only constraint (§1.3) holds;
  sports analytical work, if ever scoped, sources from public archives separately.

- **Analytics layer formalisation.** Deferred per `dr029_scope.md` §3.2. The
  capture-only constraint per `dr029_scope.md` §2.10 holds throughout this brief;
  §2.10 decides what fields are worth pulling, not what models or analyses consume
  them. Analytics layer is downstream of DR-029 close and downstream of the relevant
  analytical project activations.

- **Burst-review triage workflow design.** Downstream per `dr029_scope.md` §3.10.
  v3-build-proper work; §2.10's bucket-1 captures (specifically `removalDate`,
  authoritative `inplay`, the SP-pool composition pair) feed into burst-review surface
  design but don't specify it.

- **The four post-DR-029 strategic decisions** logged in §5.4 (Racing API value
  assessment; full-ladder credential upgrade; future operational soft-book DR;
  Cluster C routing decision). Each carries its own trigger condition; §2.10
  provides substrate, not decisions.

### §6.4 §2.10 brief close

§2.10 brief drafted Session 76 against the locked scope at `dr029/dr029_scope.md`
§2.10. Substrate: Saturday 2026-05-02 API observation probe report (`dr029/2_1_race_data/api_probe_report.md`);
Racing API OpenAPI specification (`openapi.json`); current snapshot-writer column set
(per `data_layer_current.md` §4.4 plus inspection §F).

§2.10 closes the last unwritten DR-029 in-scope deliverable. DR-029 critical path now
runs through contract documentation files and close-out governance paragraph
(§6.2) before v3 build proper begins.
