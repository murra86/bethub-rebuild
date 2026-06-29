# §2.6 — Settlement model (race path)

**DR-029 stream:** §2.6 (settlement model — race path).
**Scope status:** Locked Session 27, narrowed Session 74 (Betfair-only canonical
for v3 day-one).
**Drafted:** Session 74 (2026-05-04 ACST).

---

## §1 Framing

### §1.1 What §2.6 specifies

§2.6 specifies how v3 settles a racing bet — what source v3 reads to determine
whether a bet won, lost, or placed, and how v3 marks the bet record once that
determination is made. Race-path only; the sports-path equivalent was specified
in §2.2 (Session 38) and lives in `architecture.md` §B.1.4.

The locked v3 day-one design is **Betfair-only canonical**: v3 reads the
Betfair Win market result via `betfair_client` to settle every racing bet,
regardless of whether the bet was placed on Betfair directly or on a soft book.
There is no Racing API cross-check in the settlement path. There is no
two-source agreement state machine. Soft-book balance reconciliation in v3's
operational layer is the safety net for the rare cases where Betfair's result
might be wrong (dead heats, late protests, stewards' adjustments) — that
reconciliation work lives in v3 build proper, not in §2.6.

### §1.2 Why Betfair-only works

Two operational facts make the single-source design sound:

1. **Betfair Win settlement and soft-book settlement track the same race
   result.** Both pay out against the official finishing order set by the
   racing authority. There is no structural mechanism for Betfair to settle a
   different winner than Sportsbet, Ladbrokes, PointsBet, or any other
   Australian book. Edge cases (dead heats, protests upheld after initial
   settlement, stewards' decisions reversed) can produce divergence, but those
   are rare-and-edge events, not systemic risk.

2. **Soft-book balance reconciliation in the tool is the backstop.** Every
   soft-book bet's settlement is verifiable against the actual cash movement
   in the soft-book account. If Betfair settled a bet "won" but the soft book
   settled it "lost" (or vice versa), the discrepancy surfaces in balance
   reconciliation regardless of what §2.6's settlement state machine recorded.
   The reconciliation work is operational hygiene v3 will do anyway; it
   doesn't need to be replicated inside §2.6.

The Racing API result remains available in `capture.db` as analytical-layer
data — useful for model calibration, CLV reconstruction, and post-hoc
strategy review — but it is not part of v3's settlement state machine at
day-one.

### §1.3 Revisit policy

The Betfair-only design is locked for v3 day-one. If operational experience
surfaces material divergence cases — Betfair settlements consistently wrong
on a class of races, settlement delays past operational tolerance, edge-case
classes that balance reconciliation doesn't catch cleanly — the policy is
revisited as a fresh decision (likely a fresh DR). No forward pointer to
Racing API specifically; the cross-check question is held open as a general
"alternative sources" question, not a pre-committed integration spec.

### §1.4 Load-bearing inputs

§2.6 depends on:

- **§2.2 (Session 38) — sports-path settlement model.** Race-path settlement
  follows the same finalised / provisional / burst-review discipline shape as
  sports-path, adjusted for racing's source asymmetry (Betfair-only vs sports'
  Betfair-with-public-archive-fallback).
- **§2.4 (in flight) — Betfair Streaming spec.** Race settlement reads happen
  via `betfair_client`. Whether those reads are streaming-driven or polling-
  driven is a §2.4 decision; §2.6 specifies the shape of the read, not the
  cadence.
- **§2.8 (Session 72) — bet record contract.** Every racing bet record carries
  `betfair_market_id` and `betfair_selection_id` as canonical identifiers,
  populated at bet entry per §2.9 surface (a). §2.6 reads those identifiers
  to query Betfair for the settlement result.
- **§2.9 (Session 73) — write-side bet-entry coherence.** Surface (c)
  identifier-resolution sanity check feeds §2.6 for the late-scratching
  identifier-shift edge case (§2.9 §4.4 (b)).

### §1.5 Load-bearing outputs

§2.6 produces:

- **`betfair_client` settlement-read contract** for §2.7 (API contract
  versioning). What §2.6 needs `betfair_client` to expose for settlement
  reads — market state, settlement state, runner-level winner/placed flags,
  void status. Specified at §2.6's level of detail; §2.7 takes the spec and
  versions it as part of `betfair_client` v1.0.
- **Settlement state machine** that the bet record's `settlement_state` field
  (per §2.8 §6.4) transitions through. §2.8 specified the shape of the field;
  §2.6 specifies the transitions for racing bets.
- **Burst-review surfacing contract** — what §2.6 surfaces to the operator's
  burst-review queue when a bet can't be cleanly auto-settled. Specifies the
  shape; the burst-review UI itself is downstream v3 build proper work.

## §2 Betfair Win as canonical settlement source

### §2.1 What "canonical" means here

For v3 day-one, "canonical" means: the Betfair Win market's settlement state
is the single authoritative input that drives every racing bet's settlement
state in v3. No other source is consulted. Racing API results are not read.
Soft-book results are not read. The bet record's settlement state transitions
are determined entirely by what `betfair_client` reports back from the Betfair
Win market identified by the bet record's `betfair_market_id`.

Two consequences worth naming:

1. **Bet origin doesn't change the settlement path.** A bet placed on Betfair
   directly, a bet placed on Sportsbet, a bet placed on Ladbrokes — all
   settle the same way. v3 reads the Betfair Win market the bet was logged
   against (per the `betfair_market_id` recorded at bet entry per §2.9
   surface (a)) and applies the result. The soft-book identity of the bet is
   irrelevant to the settlement read.

2. **The bet record's `betfair_selection_id` is the canonical runner
   identity.** v3 doesn't ask "did Runner X win" against the racing
   authority's official result; it asks "did the Betfair selection
   identified by `betfair_selection_id` settle as the winner of the Betfair
   Win market identified by `betfair_market_id`." This is structurally
   equivalent for all non-edge-case races, and the rare divergence cases are
   caught by soft-book balance reconciliation downstream.

### §2.2 What the Betfair Win market exposes at settlement time

When a Betfair Win market closes and settles, the market state transitions
through the Betfair API. v3's settlement read needs the following fields
exposed by `betfair_client`:

- **Market state** — `OPEN`, `SUSPENDED`, `CLOSED`. Settlement reads only
  meaningful results once the market is `CLOSED`.
- **Market settlement state** — whether Betfair has actually settled the
  market (`settledTime` field on the market book). A market can be `CLOSED`
  but not yet `settledTime`-stamped during the gap between race finish and
  Betfair-side settlement processing.
- **Per-runner settlement status** — for each `selection_id` in the market,
  Betfair reports `WINNER`, `LOSER`, or `REMOVED` (for late scratchings).
  This is the settlement-state field per runner.
- **Market void status** — whether the market itself has been voided (rare,
  but real — abandoned races, race result reversed by stewards' decision past
  Betfair's settlement window).
- **Per-runner void status** — whether a specific runner has been voided
  (also rare — late-scratching identifier shift cases per §2.9 §4.4 (b)).

§2.6 specifies what `betfair_client` exposes at the API contract level; the
exact field names and call signatures are §2.7's job. §2.6 names the
information shape, §2.7 versions the surface.

### §2.3 The settlement read

For each unsettled racing bet on the bet record, v3's settlement worker
performs a single read:

1. Read the Betfair Win market identified by `betfair_market_id` via
   `betfair_client`.
2. If the market is not yet `CLOSED`, take no settlement action; the bet
   remains in its pre-settlement state.
3. If the market is `CLOSED` but not yet settled (no `settledTime`), take no
   settlement action; the bet remains pre-settlement. (Burst-review
   surfacing if this state persists past expected — see §3 state machine.)
4. If the market is `CLOSED` and settled, read the per-runner settlement
   status for the bet's `betfair_selection_id`. Apply to the bet record per
   the state machine in §3.
5. If the market is voided or the runner is voided, apply the void path per
   the state machine in §3.

The read is idempotent — calling it multiple times produces the same result
once the market is settled. The settlement worker's cadence (how often it
sweeps unsettled bets, how it backs off, how it handles transient errors) is
operational implementation detail in v3 build proper, not §2.6's spec.

### §2.4 What §2.6 does not specify about the read

Three things §2.6 deliberately leaves to other streams:

- **Cadence and trigger model.** Whether the settlement worker is
  streaming-driven (subscribed to market state changes), polling-driven
  (sweep every N seconds for unsettled bets), or hybrid is a §2.4 decision.
  §2.6's state machine works against any read cadence.
- **Failure handling for `betfair_client` outages.** Transient API failures,
  authentication expiry, rate-limit responses — all operational concerns
  handled at the `betfair_client` layer, not in the settlement state
  machine. §2.6 assumes the read either succeeds or doesn't; "doesn't
  succeed" means the bet stays unsettled until the next read.
- **Soft-book balance reconciliation.** The operational backstop named in
  §1.2. Implementation lives in v3 build proper alongside the operational
  account-balance tracking layer. §2.6 names it as the safety net but does
  not specify it.

## §3 Settlement state machine

### §3.1 The states

§2.8 §6.4 specified `settlement_state` as a field on the bet record without
naming racing-side transitions. §2.6 names them. Five states for racing bets
under the Betfair-only canonical design:

- **`pending`** — bet placed, race not yet settled. Default state at bet
  entry. The settlement worker has not yet seen a `CLOSED`+settled Betfair
  Win market for this bet's `betfair_market_id`. Bets stay in `pending`
  indefinitely while the worker keeps reading; long-waiters are surfaced
  via an operational-visibility flag (see §3.3) rather than a separate
  state.
- **`settled_won`** — Betfair Win market `CLOSED`, settled, and the bet's
  `betfair_selection_id` reported as `WINNER`. Terminal state.
- **`settled_lost`** — Betfair Win market `CLOSED`, settled, and the bet's
  `betfair_selection_id` reported as `LOSER`. Terminal state.
- **`voided`** — bet's `betfair_selection_id` reported as `REMOVED` (late
  scratching), or the Betfair Win market itself voided (abandoned race,
  stewards' reversal). Terminal state in v3's settlement layer; downstream
  bet-cycle handling (refund / free-bet trigger / etc.) is operational
  implementation in v3 build proper.
- **`provisional`** — bet's settlement read produced a state v3 cannot map
  to the four above without operator input, or the operator manually
  escalated the bet for review. Surfaced to burst review. Settlement
  worker keeps re-reading the market on its normal cadence; if a clean
  settlement state subsequently arrives, the bet auto-resolves to the
  appropriate terminal state without operator action.

### §3.2 The transitions

From `pending`:

- → `settled_won` on Betfair Win market `CLOSED`+settled, runner `WINNER`.
- → `settled_lost` on Betfair Win market `CLOSED`+settled, runner `LOSER`.
- → `voided` on Betfair Win market voided OR runner `REMOVED`.
- → `provisional` on burst-review-trigger condition (see §3.4).

From `provisional` (auto-resolution path):

- → `settled_won` if a subsequent settlement read returns clean `WINNER`.
- → `settled_lost` if a subsequent settlement read returns clean `LOSER`.
- → `voided` if a subsequent settlement read returns `REMOVED` or market
  void.

From `provisional` (manual operator path via burst review):

- → `settled_won` / `settled_lost` / `voided` on operator decision.

If auto-resolution and operator action arrive concurrently (rare race
condition), the operator action wins. Audit-trail entry on the bet record
records both the settlement-read result and the operator override.

**Manual operator escalation.** From any non-`provisional` state →
`provisional` on operator decision via burst-review action. Audit-trail
entry records the escalation reason as operator-supplied free-text. This
covers cases where the operator notices something the tool can't —
external information about a stewards' inquiry, a soft-book balance
discrepancy spotted independently, a race result observed on another feed
before Betfair processes it.

`settled_won`, `settled_lost`, and `voided` are terminal under normal
operation — the settlement worker does not re-read once a bet is in one of
these states. Exception: if Betfair voids the market after initial
settlement (rare; stewards' decision past Betfair's settlement window),
the bet transitions from terminal state back to `provisional`. This is
the only auto-transition back from a terminal state in the state machine;
it requires a separate trigger path on the settlement worker's read cycle
(see §3.4 condition 2). Manual operator escalation can also transition a
bet from a terminal state to `provisional`.

### §3.3 Past-settlement-window flag (not a state)

If a bet remains in `pending` past an expected post-jump settlement
window, v3 surfaces a "past settlement window" flag on the bet record for
operational visibility. The flag is not a state — the settlement worker
continues reading exactly as it does for any other `pending` bet, and the
bet auto-transitions to a terminal state once Betfair settles the market.
The flag exists only to give the operator a visibility surface for
long-waiters (a badge, a count indicator, a filterable view) so stuck
settlements aren't invisible.

Threshold for v3 day-one: **30 minutes from race finish**. Calibrate from
operational experience — if 30 minutes is too tight (most-bets-are-flagged
noise) or too loose (real stuck bets sitting too long unflagged), adjust.
The threshold is a v3 operational parameter, not an architectural lock.

The flag is deliberately a visibility surface rather than a `provisional`
trigger because there is nothing for the operator to review when Betfair
itself hasn't settled — the bet is waiting on Betfair, not on a v3
decision. Surfacing it as a burst-review item would just create noise the
operator clears with no action. If the operator does spot something
material about a flagged long-waiter (e.g. an external signal that the
race result is being disputed), the manual-escalation path in §3.2 is
the route — the flag itself is just the visibility surface that brings
the bet to operator attention.

### §3.4 Burst-review trigger conditions

Two automated conditions transition a bet from a non-`provisional` state
into `provisional`:

1. **Settlement read returned an unexpected state.** Per-runner settlement
   status returned a value that isn't `WINNER`, `LOSER`, or `REMOVED`. The
   Betfair API is documented as returning these three values; an
   unexpected state means either an API change or an edge case Betfair has
   not documented. Either way, surface for operator inspection.
2. **Market voided after initial settlement.** Bet was already in a
   terminal state (`settled_won`, `settled_lost`, or `voided`), the
   settlement worker re-reads the market for an unrelated reason or
   periodic verification, and the market is now voided where it
   previously settled cleanly. Stewards' decision past Betfair's
   settlement window is the canonical case. Bet transitions from terminal
   back to `provisional` for operator decision on what should happen with
   the bet's downstream consequences (refund, free-bet trigger reversal,
   manual override).

Plus the manual-escalation path per §3.2 — operator decision from any
non-`provisional` state.

The two automated conditions reflect "v3 noticed something it can't
decide on its own" — the operator has something material to act on, not
just a delay to wait out. The manual-escalation path covers the inverse:
"operator noticed something v3 can't see."

### §3.5 Burst-review surfacing contract

When a bet enters `provisional`, §2.6 specifies what gets surfaced to the
burst-review queue. The queue itself is v3 build proper UI work; §2.6
specifies the data the queue receives:

- The bet record (full record, including `betfair_market_id`,
  `betfair_selection_id`, soft-book identity, line value if applicable).
- The trigger source — which of the two §3.4 automated conditions fired,
  or "manual operator escalation" with the operator-supplied reason.
- The current Betfair Win market state as last read (market state,
  settlement state, runner-level statuses).
- The `placement_time` and the time the bet entered `provisional`, so the
  operator can see how long the bet has been waiting.
- A pointer to any related bets in the same race (for batch operator
  decisions if a race-wide condition is the cause — e.g. abandoned race
  voiding a whole card).

Two surfacing behaviours worth naming explicitly:

- **Auto-resolution clears items from the queue.** If a bet in
  `provisional` auto-resolves (subsequent settlement read returns a clean
  state), the burst-review item disappears from the queue without
  operator action. An audit-trail entry on the bet record records the
  auto-resolution. The operator's queue should handle item disappearance
  gracefully — items can vanish between page loads.
- **Operator action records on the bet record.** Manual `provisional` →
  terminal-state transitions are audit-trailed alongside whatever the
  settlement-read state was at the time of operator action, so post-hoc
  review can reconstruct what the operator saw and what they decided.

### §3.6 Why provisional earns its keep

Operator note from Session 74 framing: confirmed `provisional` is worth
keeping. The case:

- **The two automated trigger conditions are real.** Unexpected-state
  responses and post-settlement market voids both happen in operational
  reality and both require operator input — neither resolves on its own
  and neither is caught cleanly by soft-book balance reconciliation alone
  (balance recon catches that something is wrong, but not what to do
  about it).
- **The manual-escalation path captures operator-side information v3
  can't see.** External signals about stewards' inquiries, race-result
  observations from other feeds, soft-book balance discrepancies spotted
  independently — all cases where the operator notices something material
  before v3 does. The state machine supports the escalation natively.
- **The state captures "something needs operator attention" cleanly.**
  The auto-resolution path means low-friction cases self-clear without
  operator burden; manual action remains available for cases that need
  it.
- **It costs little to specify.** One non-terminal state, two automated
  trigger conditions, a manual-escalation path, an auto-resolution path
  that overlaps with v3's normal settlement-worker cycle, a surfacing
  contract that v3 needs anyway.

## §4 Edge cases worth naming

Following the §2.9 §4.4 pattern: document for burst-review visibility,
design safety measures only when any eventuate. The list is not exhaustive;
operational experience with v3 will surface cases not anticipated here, and
those get added to the list as they emerge.

### §4.1 Late-scratching identifier shift

Feeds in from §2.9 §4.4 (b). Runner is scratched after the Betfair Win
market closes for that runner but before the market settles. Betfair
handles the case via the per-runner `REMOVED` status — the runner's
selection in the market book transitions to `REMOVED`, and the settlement
read returns `REMOVED` for that `selection_id`.

§2.6 handling: bet transitions `pending` → `voided` per §3.2. No special
case in the state machine — the `REMOVED` path is the same path used for
any voided runner. Surface (c) in §2.9 catches the analytical-line side
of identifier shift if `capture.db` ingestion lags; §2.6 itself reads
operationally direct via `betfair_client` and isn't affected by
analytical-line timing.

### §4.2 Dead heats

Two or more runners finish in a tie for the win. Betfair's per-runner
settlement returns `WINNER` for each of the tied runners. The bet record's
`betfair_selection_id` matches one of them, the settlement read returns
`WINNER`, and the bet transitions `pending` → `settled_won` per §3.2.

**v3 captures the dead-heat fact at settlement time.** The settlement
worker's read pulls the full Betfair Win market book (which the API
returns by default — same call, same response payload, no extra cost).
The worker counts the number of per-runner statuses that returned
`WINNER`; if greater than 1, the bet record's `dead_heat_count` field is
set to the count alongside the `settled_won` transition.

Field shape:

- `dead_heat_count` — integer, nullable. Null means clean settlement
  (single `WINNER`). 2 means two-way dead heat. 3 means three-way (rare
  but real). Stored on the bet record as part of the settlement
  transition.

Why it matters: downstream cycle handling in v3 build proper (soft-book
balance reconciliation, expected-payout calculation, free-bet trigger
behaviour) reads the `dead_heat_count` flag and applies the correct
expected-payout shape. Soft books typically pay half-stake at full odds
on a two-way dead heat; capturing the dead-heat fact at settlement time
means v3's expected payout already accounts for it, and balance
reconciliation only fires for genuine discrepancies rather than for
known-cause dead-heat half-payouts.

Capturing the fact at settlement is also much cheaper than reconstructing
it from soft-book records later — the data is operationally useful for
CLV reconstruction, EV measurement on insurance cycles, and any future
analytics work that cares about dead-heat-prone race types or events.

**Sports-side equivalent — administrative cleanup carry-forward.** Sports
markets can also produce dead-heat-shaped settlements — AFL head-to-head
markets settle as ties when matches end in a draw (real and not rare in
home-and-away matches), NRL equivalents on draw-permitting markets, and
similar cases in other sports. Betfair handles these identically to
racing dead heats: per-team `WINNER` status for each tied side. The
sports-path settlement model in `architecture.md` §B.1.4 (specified
Session 38 per §2.2) needs an amendment to specify the same
`dead_heat_count` capture for sports bets. This is administrative
cleanup, not a §2.6 deliverable; logged for between-session work or
DR-029 close.

### §4.3 Stewards' protest upheld after Betfair settlement

Canonical case for the §3.4 condition 2 trigger (market voided after
initial settlement). The Betfair Win market settles cleanly, the bet
transitions to a terminal state, and then a stewards' protest is upheld
past Betfair's settlement window — Betfair voids the market.

§2.6 handling: settlement worker re-reads the market on its normal cadence
(or at periodic verification cadence; specifics are §2.4 / v3 build
proper); the void status surfaces; bet transitions terminal →
`provisional` per §3.2. Burst-review surfaces the void with the prior
terminal state, the new void state, and any related bets in the same
race for batch operator decision.

This is the load-bearing case for `provisional` — without the state, a
post-settlement void leaves the bet stuck at a wrong terminal state with
the operator only discovering the discrepancy via soft-book balance
reconciliation later.

### §4.4 Abandoned race

Whole race is abandoned (weather, track conditions, late-cancellation
events). Betfair voids the market in full; all per-runner statuses
return as voided or the market itself returns voided.

§2.6 handling: every bet on the abandoned race transitions to `voided`
per §3.2. Race-wide condition surfaces in burst review via the §3.5
"pointer to any related bets in the same race" mechanism — the operator
sees a single race-wide event rather than multiple individual bet
surfacings, and can act on the cluster as a batch.

Downstream cycle handling for abandoned races (refunds, free-bet trigger
behaviour, promo eligibility implications) is operational implementation
in v3 build proper. §2.6's job ends at recording the bet as `voided`.

### §4.5 Multi-runner state captures (generalisation of §4.2)

§4.2's full-market-book read is cheap — the Betfair API returns all
runners by default in a single market book call. The same read pattern
captures two additional operationally-useful signals at no extra cost:

- **`removed_runner_count`** — integer, nullable. Counts per-runner
  statuses that returned `REMOVED`. Populated alongside any settlement
  transition where the count is greater than zero. Signals late-scratching
  events at race level; useful operational visibility for burst review,
  for cases where multiple late scratchings shift the practical race shape
  (relevant for §4.1-style cases at scale, and for any future analytics
  on race-shape integrity).

- **`unexpected_state_count`** — integer, nullable. Counts per-runner
  statuses that aren't `WINNER`/`LOSER`/`REMOVED`. Populated alongside
  the §3.4 condition 1 `provisional` trigger when an unexpected state
  fires; gives the operator a triage signal at the burst-review surface
  (one runner with unexpected state is one kind of edge case; multiple
  runners with unexpected state is a different kind, likely an API change
  or a Betfair-side incident).

All three counts (`dead_heat_count`, `removed_runner_count`,
`unexpected_state_count`) are populated from the single market book read
the settlement worker is already performing. No extra API call, no extra
latency, no rate-limit implication — just additional fields populated
from the response data.

### §4.6 Betfair API tier change affecting settlement read fields

Feeds in from §2.9 §4.4 (e). Betfair changes the API tier required to
access certain market book fields, or deprecates fields v3 relies on for
settlement reads. The settlement read returns either an unexpected state
(triggering §3.4 condition 1, `provisional`) or fails entirely (settlement
worker retries, bet stays `pending` and surfaces as past-window per §3.3
flag).

§2.6 handling: no design specification — this is an operational cleanup
concern that lives in `betfair_client` versioning per §2.7 and in the
operator-side homework on Betfair API tiers (carry-forward item).
Surfaced in §4 only because the failure mode would route through §2.6's
state machine if it eventuated.

### §4.7 Other cases that may emerge

Operational experience with v3 will surface cases not anticipated here.
The pattern is:

- New edge case observed during operations.
- Operator decides whether the case warrants design-time handling or
  documentation-only.
- Documentation-only cases get added to this list (or its v3-build-proper
  equivalent).
- Design-time cases trigger a §2.6 amendment via fresh DR or scope
  revision.

Examples of cases that might emerge but aren't anticipated now: Betfair
introducing a new per-runner status value beyond `WINNER`/`LOSER`/`REMOVED`
(would currently route to `provisional` per §3.4 condition 1 with
`unexpected_state_count` populated, which is the right shape); race
postponement to a different day with the same Betfair market identifier
preserved; partial settlement of a market where some runners settle and
others don't.

## §5 What §2.6 closes for DR-029, what's deferred

### §5.1 What §2.6 locks as load-bearing contract

§2.6 closes the race-path settlement model for DR-029 with the following
load-bearing contracts:

- **Betfair-only canonical settlement source for v3 day-one.** Every
  racing bet — Betfair direct, soft-book, or any future bet origin —
  settles against the Betfair Win market identified by the bet record's
  `betfair_market_id`. No other source is consulted in the settlement
  state machine.
- **Five-state settlement state machine** for racing bets: `pending`,
  `settled_won`, `settled_lost`, `voided`, `provisional`. Transitions
  specified in §3.2 covering automated reads, auto-resolution from
  `provisional`, manual operator escalation, and the post-settlement
  void exception path back from terminal states.
- **`betfair_client` settlement-read contract.** What `betfair_client`
  exposes for settlement reads — market state, market settlement state
  (`settledTime`), per-runner settlement status, market void status,
  per-runner void status. Specification feeds §2.7 (`betfair_client`
  v1.0 contract versioning).
- **Bet-record settlement fields.** Three count fields populated from
  the same full-market-book read the settlement worker performs —
  `dead_heat_count`, `removed_runner_count`, `unexpected_state_count`.
  Plus the past-settlement-window flag (operational visibility surface,
  not a state).
- **Burst-review surfacing contract.** What data the burst-review queue
  receives when a bet enters `provisional` — bet record, trigger source,
  current Betfair market state as last read, timestamps, race-wide
  pointer to related bets. Surface itself is v3 build proper UI work;
  the data contract is locked here.

### §5.2 What §2.6 explicitly does not specify

Three categories of work named explicitly as out of scope for §2.6:

- **Settlement worker cadence and trigger model.** Whether reads are
  streaming-driven, polling-driven, or hybrid is a §2.4 decision. §2.6's
  state machine works against any read cadence.
- **`betfair_client` operational concerns.** Authentication, rate-limit
  handling, transient API failures, reconnection — all live in
  `betfair_client` itself and in §2.7 contract versioning. §2.6 assumes
  the read either succeeds or doesn't.
- **Soft-book balance reconciliation.** The operational backstop for
  rare divergence cases (§1.2). Implementation lives in v3 build proper
  alongside operational account-balance tracking. §2.6 names it as the
  safety net but does not specify it.

### §5.3 What §2.6 unblocks

§2.6 unblocks downstream DR-029 streams and v3 build proper work:

- **§2.7 (API contract versioning) for `betfair_client`.** §2.6 names
  what `betfair_client` must expose for settlement reads; §2.7 takes
  that specification and versions it as part of `betfair_client` v1.0
  contract. The settlement-read shape is now writable for §2.7
  alongside the surface (a) sports-line query and surface (b)
  `marketTime` read already named in §2.9 §6.1.
- **v3 build proper settlement worker implementation.** The state
  machine, transitions, trigger conditions, and read shape are
  specified at the contract level. v3 build proper implements the
  worker against the contract.
- **v3 build proper burst-review queue UI.** The data contract is
  specified; the UI surface implements against it.
- **v3 build proper operational-visibility layer for past-settlement-
  window flagging.** The flag is named; the surface is implemented
  in v3 build proper.

### §5.4 What §2.6 carries forward (non-gating)

Items surfaced during §2.6 drafting that are not gating for DR-029
close but need attention as administrative cleanup or future
operational calibration:

- **Sports-side dead-heat capture.** `architecture.md` §B.1.4 needs an
  amendment to specify `dead_heat_count` capture for sports bets
  (head-to-head AFL ties, NRL equivalents, similar cases). Identical
  shape to racing dead heats; administrative cleanup, not a §2.6
  deliverable.
- **Past-settlement-window threshold calibration.** v3 day-one ships
  with 30 minutes from race finish; calibrate from operational
  experience. Not a §2.6 amendment trigger — it's a v3 operational
  parameter.
- **Settlement worker periodic verification cadence.** §3.4 condition
  2 (post-settlement market voids) requires the worker to re-read
  terminal-state bets at some periodic verification cadence. The
  cadence itself is v3 build proper operational tuning, not a §2.6
  spec.
- **Operational experience surfacing new edge cases.** Per §4.7,
  cases not anticipated now will emerge from v3 operations and either
  get added to documentation or trigger §2.6 amendments via fresh DR.

### §5.5 What §2.6 does not unblock

§2.6 does not unblock §2.10 (external analytics scan inventory
writeup), which is independent of settlement model. §2.10 remains
writable as an alternative Session 75+ deliverable per Session 73's
session-order proposal.

§2.6 also does not close DR-029 itself. Remaining DR-029 work after
§2.6: §2.7 (API contract versioning across both module contracts), §2.10
(external analytics scan inventory), Fix 4 (Racing API cadence design
including `marketTime` mutability question), Fix 5 (venue
harmonisation), and the DR-029 close-out governance paragraph covering
periodic data-fitness re-verification and the three pieces of named
debt.
