# §2.9 — Write-side bet-entry coherence

DR-029 in-scope item §2.9. Integration-boundary contract addition that protects the leaner bet schema landed in §2.8. Three sanity-check surfaces at write time, plus an explicit excluded-scope section naming the transactional/cascade-atomicity work that sits downstream of DR-029 in v3 build operational design.

**Status:** in flight (Session 73). §1 locked.
**Load-bearing inputs:** §2.8 (bet record contract), §2.2 (Betfair-direct sports operational layer), §2.4 (Betfair Streaming spec).
**Load-bearing output:** §2.7 (API contract versioning — surface (c) is part of the `vps_client` contract).

---

## §1. Framing

§2.9 is the integration-boundary contract addition that protects the leaner bet
schema landed in §2.8. §2.8 specified what a bet record looks like — eleven
derived fields resolved at read time against the analytical line, Betfair
canonical identifiers as the join key, universal-amendable model with cascade
rules. §2.9 specifies the three sanity-check surfaces at write time that protect
those identifiers' later read-time resolution.

§2.9's scope is deliberately narrow. The leaner schema's correctness depends on
identifiers written at bet-entry time resolving cleanly later when the read-time
resolution paths fire. Three surfaces protect that contract:

- Sports line specification at bet entry, where the operator's typed soft-book
  line and the corresponding Betfair market_id must be matched at write time
  rather than reconciled later (§2).
- Placement-time plausibility, a trivial guard against backdating and
  clock-drift errors that would compromise downstream cycle attribution and
  settlement timing (§3).
- Identifier-resolution as a passive boundary check at first analytical read,
  framed as a capture.db ingestion-fault surface rather than a write-time
  validation step (§4).

These three surfaces close the integration-boundary contract for the leaner
schema. They are not transactional atomicity, not cascade-write coherence, not
multi-record-write semantics — those concerns are real but sit downstream of
DR-029 in v3 build operational-design work. §5 names that excluded scope with
forward pointers so it does not get lost.

§2.9's load-bearing inputs are §2.8 (the bet record contract being protected),
§2.2 (Betfair-direct sports operational layer that surface (a) queries against),
and §2.4 (Betfair Streaming spec underpinning the operational direct line).
§2.9's load-bearing output is §2.7's API contract versioning — surface (c)'s
passive boundary check is part of the `vps_client` contract that §2.7 versions.

---

## §2. Surface (a) — sports line specification at bet entry

### §2.1 What this surface is

When the operator places a sports bet on a handicap or total market at a soft
book, the line they bet (e.g. "Port -6.5", "total points over 215.5") must be
matched to a specific Betfair market_id at log time. Race runner identity
resolves cleanly through Betfair canonical identifiers because both sides of
the boundary (operational and analytical) source from the same Betfair API,
so the join key is structurally stable. Sports lines are different: Betfair
exposes many market variants per fixture (handicap at -5.5, -6.0, -6.5, -7.0;
totals at 215.5, 216.5, 217.5; and so on), and the operator's soft-book line
might match any one of them, a different one across books, or none at all.
Picking the right market_id is a log-time decision; once committed, the
market_id is the canonical join key for everything downstream.

This is the surface where the operational/analytical-line discipline meets
the soft-book typed-price path. The operator types the soft-book price at
bet entry per the §2.5 deferral; v3 takes that typed price as authoritative
for the soft-book leg. The line itself — the handicap or total at which the
bet was struck — must be resolved against Betfair's market structure to give
the bet record a valid join key. Surface (a) is that resolution step.

The operator's typed line is also retained on the bet record alongside the
resolved Betfair market_id, per the §2.8 cheap-to-capture / expensive-to-
reconstruct principle. The typed line is the operator's view of what they bet;
the market_id is Betfair's canonical identity for the matching market. Both
are useful — the typed line for audit and operator memory, the market_id for
read-time resolution and analytics. Storing both is cheap and disambiguates
edge cases where the typed line and the resolved market shift do not exactly
align (e.g. soft book offered -6.5, Betfair only has -6.0 and -7.0 variants).

### §2.2 Standard log-time flow

Five-step flow for sports bets on handicap or total markets:

1. Operator selects fixture in burst UI. v3 has the Betfair `event_id` from
   §2.2's Betfair-direct sports operational layer.
2. Operator types the line they took at the soft book (e.g. "-6.5" for
   handicap, "215.5 over" for total) and the price (e.g. 1.91).
3. v3 queries Betfair direct via `betfair_client` for all market variants for
   the fixture and market type (handicap or total). Result is a list of
   `market_id` values with their Betfair handicap or total values.
4. v3 surfaces matching candidates to the operator. Two cases for the standard
   flow:
   - Exact match on the operator-typed line: v3 pre-selects the matching
     market_id. Operator confirms.
   - No exact match: v3 surfaces a candidate ladder (the matching market type
     for the fixture, with the operator-typed line as the anchor). Operator
     picks the variant they consider closest to the soft-book line they took,
     acknowledging the line-shift.
5. Operator confirms. v3 writes the bet record with:
   - The confirmed Betfair `market_id` as the canonical join key.
   - The operator-typed line as `operator_typed_line` (free-text, e.g. "-6.5").
   - The operator-typed soft-book price as `price_taken`.

The market state at query time (OPEN, SUSPENDED, CLOSED) does not affect this
flow. Betfair's `market_id` is stable across the full market lifecycle —
SUSPENDED is a transient trading-state on a known market, not a no-identifier
state. v3 attaches the market_id either way.

The candidate-ladder selection surface — including the operator-typed-line
anchor and the variants surfaced above and below for cross-soft-book
comparison — lives in burst UI design, downstream of DR-029. The contract
specified here is the data-layer behaviour: v3 must record a confirmed Betfair
market_id (or, in the rare cases below, a structured pending flag) and the
operator-typed line on every sports bet record.

### §2.3 Cases where market_id resolves later

Three rare cases where v3 cannot resolve a Betfair market_id at log time:

- **Market not yet open on Betfair.** The fixture exists at the soft book but
  Betfair has not opened the corresponding market yet. Rare, since the operator
  typically bets markets already trading; possible for early-listed soft-book
  markets.
- **Transient `betfair_client` API failure.** Network failure, authentication
  failure, rate-limit cap, or other API-side unavailability at the moment v3
  attempts the query. Not a market-state issue — the market_id exists, v3 just
  cannot reach Betfair to retrieve it.
- **Fixture removed from Betfair entirely.** Race or fixture scratched on
  Betfair's side and removed from the market catalogue. Different from
  SUSPENDED, where the market_id remains queryable.

In all three cases, v3 still records the bet. The bet record commits with:
- The operator-typed line as `operator_typed_line`.
- The operator-typed price as `price_taken`.
- A structured pending flag: `market_id_resolution_pending` with `reason` taking
  one of `not_yet_open` / `api_failure` / `fixture_removed`.

Surface (c) — identifier-resolution sanity check (§4) — catches resolution at
first analytical-line read against `capture.db`. When the analytical line
catches up (Betfair opens the market, API recovers, fixture state stabilises),
the market_id resolves and attaches to the bet record via the §9 amendment
discipline locked in §2.8. The pending flag clears.

The general principle: surface (a) protects the integration-boundary contract
without blocking the operator's log-time workflow. The soft-book bet is the
load-bearing reality — v3 records what happened. The Betfair market_id is the
canonical join key, attached whenever it can be resolved (typically log time;
occasionally later via surface (c)).

---

## §3. Surface (b) — placement-time sanity check

A trivial guard, specified explicitly because it protects downstream cycle
attribution and settlement timing.

### §3.1 What this surface does

When the operator commits a bet record, v3 captures `placement_time`
automatically from the system clock. Manual timestamp entry is the edge case —
backfilling a missed log, batch-logging from yesterday, or correcting via the
§9 amendment discipline locked in §2.8. In normal operations the timestamp is
auto-captured and the operator never sees this surface.

The auto-captured (or manually-entered) timestamp is checked against the
scheduled start time of the fixture, sourced from Betfair via `betfair_client`
(the `marketTime` field on the market). The check is: is `placement_time`
within a plausibility window relative to the scheduled start.

### §3.2 Plausibility window

The plausibility window is sport-specific:

- **Racing** (thoroughbred, harness, greyhound): `placement_time` must be no
  later than scheduled start plus 30 minutes, and no earlier than scheduled
  start minus 14 days.
- **Sports** (AFL, NRL, and other team sports): same — no later than scheduled
  start plus 30 minutes, no earlier than scheduled start minus 14 days.

The 30-minute upper bound on log-after-scheduled-start absorbs typical
operational cases: racing late-second soft-book bets logged after the actual
jump (commonly 0–5 minutes post-jump); sports first-quarter live-betting
loggings; brief delays where the operator pauses between placing at the soft
book and switching to v3 to log.

The 14-day lower bound on log-before-scheduled-start catches obvious wrong-
fixture errors (operator pasting a future fixture's market for a past bet,
selecting the wrong week's AFL round, etc.) without false-warning on legitimate
futures bets.

### §3.3 Behaviour outside the window

If `placement_time` falls outside the plausibility window:

- v3 surfaces a warning on commit, naming the mismatch ("placement_time is X
  minutes after scheduled start" or "placement_time is X days before scheduled
  start").
- The operator confirms the timestamp.
- v3 commits the bet record with the operator's timestamp authoritative.

The check is warning-only, never blocking. The operator's typed (or auto-
captured-then-confirmed) timestamp is always authoritative. Legitimate edge
cases exist — race postponements past the 30-minute bound, futures bets, late
batch-logging — and friction-free operator override is the right design.
v3's job is to surface obvious errors at the moment the bet is committed,
not to second-guess operator judgement.

The warning and the operator's confirmation are logged in the operations
event log for audit, with `placement_time_warning_acknowledged` flag on the
bet record.

### §3.4 Why this matters for downstream resolution

A backdated or otherwise-wrong `placement_time` quietly breaks three
downstream resolution paths:

- **Cycle attribution** (§2.8 §7) joins bets to cycles via `placement_time`
  ordering relative to cycle window boundaries. A wrong timestamp can group a
  bet into the wrong cycle, distorting Strategy 1 (Safety Net) cycle EV.
- **Settlement matching** (§2.8 §8.7) joins bets to race results via
  `placement_time` against race-result timestamps. A bet timestamped after the
  race finish would look like an impossible bet.
- **CLV reconstruction** (the analytical-layer signal flagged in §2.8 §10.3)
  requires `placement_time` to fall within the pre-jump price-snapshot window.
  A backdated timestamp would silently fail the analytical lookup.

Surface (b) catches the obvious cases at write time. The check is cheap (a
single comparison against `marketTime`) and high-value because the failure
modes downstream are silent.

### §3.5 Empirical clarification carried forward

It is not yet empirically confirmed whether Betfair's `marketTime` field
updates when a race is materially delayed (e.g. stewards' delay of 30+
minutes). External evidence (third-party Betfair-trading-platform forums)
suggests `marketTime` reflects originally-scheduled start and does not update
on delays, but this has not been verified against a delayed-race observation.

The §3 design works either way:

- If `marketTime` does not update: a race delayed 35 minutes past schedule
  will warn-on-log when the operator logs immediately after the actual jump.
  The warning is a single-click acknowledgement and the operator already
  knows the race was delayed. False-positive on legitimate-delay cases is
  tolerable.
- If `marketTime` does update: the warning would only fire on bets logged
  more than 30 minutes past the *updated* scheduled start, which is a tighter
  and more sensitive check.

The empirical question is folded into Fix 4 cadence brief drafting (which
naturally touches `marketTime` semantics). If `marketTime` is confirmed to
update on delays, no §3 design change is needed; if confirmed not to update,
no §3 design change is needed either (the 30-minute padding already absorbs
the false-positive cost). The clarification is logged for completeness, not
because it gates anything.

---

## §4. Surface (c) — identifier-resolution sanity check

A passive boundary check at first analytical-line read, framed as a
`capture.db` ingestion-fault surface rather than a write-time validation step.

### §4.1 What this surface does

When the bet record is logged, its identifiers come from the operational
direct line — `betfair_client` for racing-page or sports-page selections.
Those identifiers (Betfair `market_id`, Betfair `selection_id`, Betfair
`event_id`) are the canonical join keys per §2.8 §1.

Later, when read-time resolution fires (§2.8 §8 — read-time resolution paths),
v3 joins the bet record's identifiers against `capture.db` via `vps_client`
to resolve the eleven derived fields (race classification, BSP, finish
position, and so on). This join should always succeed because both the
operational line (`betfair_client`) and the analytical line (`vps_client`
against `capture.db`) source from the same Betfair API. The identifiers are
structurally stable across the boundary.

If the join fails on the first attempt — the bet record's identifiers don't
match any record in `capture.db` — the failure is not a bet-record-side
problem. The bet record is correct; the analytical-line ingestion has not
caught up yet, or has gapped. Surface (c) frames this as a `capture.db`
ingestion-fault surface, not a write-time error.

### §4.2 Resolution-failure handling

When read-time resolution fails on the first attempt:

- v3 does not raise a write-time error. The bet record's identifiers are
  correct; the analytical line has not caught up.
- v3 surfaces the failure in the operations event log as a `capture.db`
  ingestion-fault flag, with the bet record id and the missing analytical-line
  identifier(s) named. No operator-facing surface yet — this is a passive
  flag, retried on each subsequent read-time pass.
- v3 retries resolution on each subsequent read-time pass. When the analytical
  line catches up (typical case: `capture.db` ingestion lag, normally minutes,
  occasionally hours), the resolution succeeds and the flag clears.
- If resolution still fails after 12 hours from the bet's `placement_time`,
  the flag escalates to operator-facing review (burst review or its
  equivalent — the burst-review workflow design itself sits downstream of
  DR-029 in `dr029_scope.md` §3.10). 12 hours is long enough that normal
  ingestion lag never trips it; short enough that real gaps surface within an
  operationally useful timeframe.

The general principle: surface (c) preserves the integration-boundary contract
without putting write-time pressure on the analytical line. The bet record
commits cleanly at log time; resolution is best-effort at read time; failure
is framed as an ingestion-fault surface for analytical-line investigation,
with operator-facing escalation only after the 12-hour window.

### §4.3 Connection to surface (a) market_id pending flag

When surface (a) (§2) leaves a bet record with `market_id_resolution_pending`
flagged (the rare cases — market not yet open, transient API failure, fixture
removed from Betfair), surface (c) is the natural resolution path. The bet
record is logged with operator-typed line and price as fallback identity; the
market_id slot is empty.

When the analytical line catches up — Betfair opens the market, API recovers,
fixture state stabilises — surface (c)'s read-time resolution attempt finds
the matching market and attaches the canonical `market_id` via the §9
amendment discipline locked in §2.8. The pending flag clears.

This is the standard recovery path for surface (a)'s rare cases. No special
machinery required — surface (c) handles the resolution as a matter of course
on its first successful pass.

### §4.4 Edge cases worth naming

Surface (c) is the visibility surface for any structural identifier mismatch
between the operational and analytical lines. Most cases fall under normal
ingestion lag or surface (a)'s rare pending cases. Six edge cases are worth
documenting explicitly so burst review has a reference list of avenues to
investigate when surface (c) flags fire. These are documented for visibility
only — no dedicated mitigation machinery is built for any of them today. If
any eventuate in real operations, a safety measure can be designed at that
point.

- **(a) Betfair-side market replacement.** Betfair occasionally voids a
  market and reissues a replacement with a different `market_id` for what is
  operationally the same race or fixture. Triggers include stewards'
  inquiries leading to re-runs and market-rules amendments. The bet record
  carries the original (now-voided) `market_id`; `capture.db` may have
  ingested under the new `market_id`. Resolution fails because the join key
  no longer exists in the current Betfair catalogue. Expected frequency:
  rare, perhaps a handful per year.

- **(b) Late-scratching identifier shift.** A runner scratched after the
  operator logs the bet but before `capture.db` ingests the race results.
  Whether this triggers a resolution failure depends on how `capture.db`
  represents removed runners — if scratched runners stay in the table with a
  `removed` flag, resolution succeeds and the bet is settled per Rule 4 /
  refund logic. If scratched runners drop from the table, resolution fails.
  Touches §2.6 (settlement model) territory. Expected frequency: scratchings
  themselves are common; resolution failures from this cause depend on
  `capture.db` schema choices yet to be locked.

- **(c) Cross-code identifier mismatch.** Bet entered carrying identifiers
  from one racing code (thoroughbred, harness, greyhound) joining against a
  `capture.db` record from a different code. Should be impossible if
  `betfair_client` and the burst UI are correctly scoped, but a code-
  inference bug at bet-entry time could produce this. Surface (c) is the
  visibility surface; the underlying cause would be an implementation bug.

- **(d) Time-zone or date-boundary edge.** A late-Friday-night Australian
  race crossing the GMT date boundary at Betfair's side. Should be
  eliminated by joining on `market_id` rather than date+venue, but worth
  naming because v2 had drift here historically.

- **(e) Betfair API tier or app-key change.** If the Betfair account moves
  between Live and Delayed app keys, or hits a tier issue, `betfair_client`
  might return data under a different identifier scheme than `vps_client`
  (configured separately on the VPS). Tier question already flagged as an
  open item elsewhere (EX_LADDER entitlement, §2.8 §10.3 carry-forward).

- **(f) Manual data correction in `capture.db`.** Operator or admin runs a
  backfill or correction script against `capture.db` that re-IDs records.
  Bet records logged before the correction point to the old id. Operational
  hygiene issue; surface (c)'s 12-hour escalation would catch this.

When burst review encounters a surface (c) flag, this list is the reference
set for diagnosis. Most flags will be normal ingestion lag (Class 1) or
surface (a) pending cases (Class 2). When neither applies, this list of edge
cases is where to look next.

### §4.5 What this surface does not do

Surface (c) is not an active validation step at write time. v3 does not
attempt analytical-line resolution at log time. The reasons:

- The operational line is the source of truth at log time. The bet record's
  identifiers are valid because `betfair_client` returned them.
- The analytical line has expected ingestion lag. Forcing a write-time check
  against `capture.db` would either fail spuriously (lag has not caught up
  yet) or block the operator's log-time workflow waiting on a backend system.
- The integration-boundary contract (DR-028 — no caching, no denormalisation,
  no second integration point) is preserved by keeping the read-time path
  the only resolution surface.

Surface (c) is therefore deliberately passive: a flag-and-retry mechanism on
the read-time path, not a validation gate on the write-time path. This
matches the locked scope framing in DR-029 §2.9(c): "passive sanity check on
the integration boundary, not an active validation step."

---

## §5. What §2.9 does not do

§2.9's scope is the integration-boundary contract addition — three sanity-check
surfaces protecting the leaner bet schema's identifier resolution. Several
adjacent concerns are real but deliberately excluded from §2.9 because they
sit downstream of DR-029 in v3 build operational design. This section names
them with forward pointers so they do not get lost.

### §5.1 Transactional atomicity across multi-record writes

When a bet is committed at log time, multiple records may be written together:
the bet record itself, a cycle record (when first-of-cycle per §2.8 §7), and
free bet ledger consumption events (when `funding_source = free-bet-pool` per
§2.8 §7). These writes need to be atomic — either all succeed or none do — to
avoid half-written states where a bet record exists but its cycle record is
missing, or a free bet ledger consumption event fired without a corresponding
bet record.

§2.9 does not specify the transactional boundaries, isolation levels, or
rollback semantics for these multi-record writes. That is operational-design
work for v3 build proper, where the database choice (still TBD per
`project_context.md` §4) and the ORM or query-builder layer determine the
concrete transaction shape.

Forward pointer: v3 build's data-layer construction phase. Carry-forward in
`current_state.md` open items.

### §5.2 Cascade-write coherence under §2.8 §9 amendment discipline

§2.8 §9 locked the universal-amendable model: every field on every record is
amendable via reconciliation events with cascade flow-through. §9.4 named
eight cascade rules for the well-understood cases. The execution semantics of
those cascades — atomicity across cascade-derived multi-record amendments,
ordering guarantees, conflict resolution when two cascade paths target the
same field, rollback when a cascade fails partway — are not specified here.

§2.9 does not specify cascade execution semantics. That is operational-design
work for v3 build proper, downstream of the data-layer construction in §5.1.

Forward pointer: v3 build's amendment-pipeline construction phase. The
"complete cascade map" parked deliverable (per §2.8 §10.3 carry-forward) feeds
this work.

### §5.3 Integrity-layer flag surface for ambiguous cascades

§2.8 §9.4 named that ambiguous cascades surface flags for operator review
rather than auto-resolving. The integrity-layer machinery that produces those
flags — what triggers a flag, how flags are queued, the operator-facing flag-
queue UI, the resolution workflow — is not specified here.

§2.9 does not specify the integrity-layer flag surface. That is operational-
design work for v3 build proper, alongside the cascade execution semantics in
§5.2.

Forward pointer: v3 build's integrity-layer construction phase. The "path-
(iii) reconciliation-job scheduling and operator-facing flag-queue UI" item
(per §2.8 §10.3 carry-forward) is the same body of work.

### §5.4 Free bet ledger consumption-event atomicity

§2.8 §7 locked the free bet ledger schema (free_bets table, free_bet_deployments
table, atomic service layer). The atomicity requirements for ledger consumption
events at bet-placement time — single ledger entry per consumption, no double-
deduction on retry, no orphan deployments when the parent bet write fails —
are real but specified at the v3 build operational layer, not here.

§2.9 does not specify free bet ledger consumption-event atomicity. The §2.8
§7 schema lock is the contract; §2.9 protects the bet-record-side identifier
resolution; the consumption-event atomicity sits in v3 build operational
design.

Forward pointer: v3 build's free bet ledger construction phase. v2's existing
atomic service layer is operational substrate that informs the v3 design but
does not constrain it.

### §5.5 Scope discipline summary

The pattern across §5.1–§5.4 is the same: §2.9 protects the integration-
boundary contract for the leaner bet schema; the operational-design work that
implements multi-record writes, cascade pipelines, integrity-layer flag
surfaces, and ledger atomicity sits in v3 build proper. DR-029's job is to
lock the data-layer fitness contract before v3 build begins, not to specify
v3 build's own operational design.

Each excluded item has a forward pointer to the v3 build phase that will
specify it. The forward pointers are deliberately coarse — v3 build's phase
structure is itself TBD until DR-029 closes — but they ensure the excluded
scope is named, not lost.

---

## §6. What §2.9 closes for DR-029

### §6.1 What §2.9 unblocks

§2.9 unblocks the bet-record-side of §2.7 (API contract versioning) for
final formalisation. Specifically:

- **`vps_client` contract.** Surface (c)'s passive boundary check at first
  analytical-line read is part of the `vps_client` contract — the contract
  must specify that resolution failures are flagged as ingestion-fault
  surfaces, not raised as write-time errors, with the 12-hour escalation
  window to operator-facing review. §2.7 versions this behaviour as part of
  v1.0 of the contract.
- **`betfair_client` contract.** Surface (a)'s sports-line query pattern (the
  five-step flow in §2.2) and surface (b)'s `marketTime` read are part of the
  `betfair_client` contract. §2.7 versions both behaviours as part of v1.0 of
  the contract.

§2.9 also feeds §2.6 (settlement model — race path) by clarifying surface (c)'s
treatment of late-scratching identifier shifts (§4.4 edge case (b)). The
settlement model needs to specify how `capture.db` represents removed runners,
which determines whether late scratchings produce surface (c) flag fires or
resolve cleanly via Rule 4 settlement.

### §6.2 What §2.9 lands as load-bearing contract

Three load-bearing contracts land with §2.9, all preserved as v3 build proper
proceeds:

- **The integration-boundary contract for the leaner bet schema.** Three
  sanity-check surfaces (a, b, c) protect identifier resolution between the
  operational and analytical lines. Per DR-028 (no caching, no
  denormalisation, no second integration point), surface (c) is deliberately
  passive — write-time validation against the analytical line is not a
  pattern v3 adopts.
- **The soft-book sports-line resolution contract.** Operator types the
  soft-book line; v3 queries Betfair for market variants; operator picks the
  matching market_id; v3 records both the operator-typed line and the
  resolved market_id (per §2 of this brief). This contract holds for the
  typed-price path absorbed into §2.8 / §2.9 from the deferred §2.5.
- **The placement_time plausibility contract.** 30-minute window either side
  of scheduled start, warning-only and never blocking, operator timestamp
  always authoritative (per §3 of this brief). Cycle attribution, settlement
  matching, and CLV reconstruction depend on this timestamp being roughly
  right.

### §6.3 Carry-forward items not gating

Three items carry forward beyond §2.9 close, none gating DR-029:

- **`marketTime` mutability empirical question** (per §3.5). Whether Betfair's
  `marketTime` field updates on race delays. Folded into Fix 4 cadence brief
  drafting (which naturally touches `marketTime` semantics). The §3 design
  works either way; this is logged for completeness, not because it gates
  anything.
- **The four excluded items per §5.** Transactional atomicity across multi-
  record writes (§5.1), cascade-write coherence (§5.2), integrity-layer flag
  surface (§5.3), free bet ledger consumption-event atomicity (§5.4). All
  forward-pointed to v3 build proper phases.
- **Surface (c) edge-case reference list** (per §4.4). Six edge cases
  documented for burst-review diagnosis: Betfair-side market replacement,
  late-scratching identifier shift, cross-code identifier mismatch, time-zone
  / date-boundary edge, Betfair API tier change, manual data correction in
  `capture.db`. Documented for visibility only; safety measures designed if
  any eventuate.

### §6.4 What §2.9 does not unblock

§2.9 does not unblock §2.10 (external analytics scan inventory writeup) —
§2.10 is independent and writable already. §2.9 does not unblock §2.6
(settlement model — race path) directly; §2.6's race-path specification is
its own work, though §2.9 §6.1 names the surface (c) feed into §2.6 for
late-scratching handling.

§2.9 does not close DR-029 itself. Remaining DR-029 in-scope items after
§2.9 close: §2.6 (race-path settlement), §2.7 (API contract versioning final
formalisation), §2.10 (external analytics scan inventory writeup), plus the
§2.1 surgical-fix arc tail (Fix 4 cadence brief, Fix 5 venue harmonisation).
DR-029 closes once all those land plus the close-out governance paragraph
(naming the three pieces of named debt being carried into v3 build).
