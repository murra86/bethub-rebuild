# Session 91 substrate — W4 brief drafting

**Purpose:** Captures all locked decisions from Session 91's W4 brief
design conversation in durable form on disk. Session 92's drafting
reads this file plus `w4_bet_entry_brief.md` (sections §1 and §2
already drafted) plus the canonical substrate (math review §1–§7,
DR-032, `architecture.md` §A.10) and continues drafting from §3
onward.

**Locked at:** 2026-05-06 ~16:30 ACST (Session 91).
**Next session reads:** this file as primary substrate; brief skeleton
on disk; Session 91 record; standard required reads.
**Failure mode this protects against:** Sessions 60→61→62 (drafts
living only in chat history, unrecoverable on fresh chat open).

---

## Round-by-round design log (17 rounds)

### Round 1 — Scope decision

**Call:** W4 brief = hedge entry only (Option A) vs hedge entry plus
modal mechanics (Option B).

**Decision: Option A — hedge entry only.** Modal mechanics carried to
W7. Math review §4 stays locked on disk; doesn't go stale by waiting.

**Rationale:**
1. Single-session bounded execution — Code briefs work best when one
   Code session can ship the whole thing end-to-end. Hedge entry plus
   modal mechanics is a bigger surface and risks the brief becoming
   two Code sessions stitched together.
2. DR-032's bet-record / bet-leg schema is the stable contract.
   Hedge entry writes against that schema; modal mechanics is a UI-
   coupled behavioural layer above the engine. Splitting at that
   seam respects DR-030's module boundaries (orchestration vs UI).
3. W4 → W7 sequencing already implied. W7 has a complete behavioural
   spec to port against, not a half-locked one.

**Trade-off accepted:** §4 modal mechanics carries forward to W7 as
locked-but-not-yet-shipped substrate.

### Round 2 — Module shape

**Call:** Module count and split for `workflow/bet_entry/v1/`.

**Decision: four modules.**
- `orchestrator.py` (impure)
- `staking.py` (pure)
- `pricing.py` (pure)
- `record_builder.py` (pure)

**Rationale:**
- Single-responsibility per module makes brief easier to write (one
  section per module) and Code easier to ship without modules
  drifting into each other.
- `orchestrator.py` is the only impure module — all I/O centralised.
- `staking.py` and `pricing.py` are split because they answer
  different questions (stake math vs effective-odds synthesis).
- `record_builder.py` is its own module because DR-032's schema is
  the W4 contract; one module's job is "build a DR-032-compliant
  bet record from entry-path inputs".
- No `commission.py` — dynamic commission lookup is thin enough to
  live inside `staking.py` or `orchestrator.py`.

**Operator added:** segmented modules make bug isolation easier
later — confirmed alignment with the design intent.

### Round 3 — `pricing.py` scope clarification

**Operator clarification:** `pricing.py` synthesises effective odds
**only for bonus-winnings-style promos** (Strategy 2 sub-shape (b)).
Insurance promos (Strategy 1) and clean turnover (Strategy 4) do not
run through `pricing.py` at all — Strategy 1's stake math handles
the refund layer in `staking.py`; Strategy 4 has no price-uplift
layer.

**Decision: `pricing.py`'s scope is bonus-winnings only.** The brief
must explicitly name which strategies it serves and which it
deliberately doesn't.

**Implication for racing-screen → modal flow:** `pricing.py` only
fires when the operator clicks a selection where the racing screen
has bonus-winnings promo fields populated. Insurance and clean-
turnover paths skip the pricing module entirely.

### Round 4 — Math review reference style

**Call:** Embed math review section text in the brief, or
reference-by-anchor?

**Decision: reference-by-anchor.** Brief names math review sections
as required reads; Code loads both files into context before
starting.

**Rationale:**
1. Math review is locked at 1942 lines on disk. Embedding duplicates
   locked content; future clarifications would drift.
2. Code reads both files anyway (named anchors = required reads).
   Embedding adds context cost without adding information.
3. Brief stays leaner and W4-focused (module shape, schema, error
   semantics, what-Code-must-do). Math is the math.

**Trade-off accepted:** anyone reading the brief in isolation has to
also open the math review. Acceptable — Code's workflow is to read
all named anchors before starting.

### Round 5 — `strategy_tag` enum

**Call:** `strategy_tag` value vocabulary on bet record.

**Decision: four-tag enum, closed (not freeform):**
- `safety_net` — Strategy 1 (insurance / refund promos).
- `price_booster` — Strategy 2 (top fluc, BOB, bonus winnings).
- `sgm_correlated` — Strategy 3 (SGM correlated friction).
- `synthetic_each_way` — Strategy 4 (clean turnover with EV thesis).

**W4 v1 actively populates three** (`safety_net`, `price_booster`,
`synthetic_each_way`). `sgm_correlated` reserved for W4.1 / W7.

**Tag set is closed.** Future strategies need a DR amendment or new
tag added explicitly. Protects against tag drift (operator typos,
downstream code matching on partial strings).

### Round 6 — `strategy_tag` nullability

**Operator clarification:** Some bets carry no strategy. They are
**deliberate non-EV bets placed for account-pattern hygiene** —
mixing the bet shapes books see, keeping accounts looking like
ordinary punting, diluting the promo-hunting signal.

**Decision: `strategy_tag` is nullable.** Account-health turnover
bets land with `strategy_tag = NULL`.

**Important distinction from Strategy 4:**
- **Strategy 4 (`synthetic_each_way`):** deliberate clean turnover
  *with* EV thesis. Thin margins but value-betting.
- **Account-health turnover (`NULL`):** deliberate turnover *without*
  EV thesis. Bet pattern itself is the point, not expected return.

The analytics layer later will want to tell them apart cleanly.

**Modal must surface "no strategy" as an explicit operator choice**,
not an unfilled-field default. `strategy_tag` is always either an
explicit value or an explicit `NULL`, never an accidental empty.

### Round 7 — Set B denormalised display fields

**Call:** Which fields are populated as immutable logging-time
snapshots on bet legs (per DR-032 §2 / §4)?

**Decision: six fields per leg.**
1. `runner_name` — e.g. "Winx".
2. `event_name` — e.g. "Race 5 Randwick".
3. `venue_name` — e.g. "Randwick" (Betfair-canonical).
4. `market_name` — e.g. "WIN" / "PLACE" / specific SGM market.
5. `scheduled_start_time` — race / event start time at logging.
6. `betfair_implied_probability` — per-leg Betfair-implied
   probability at logging (1 / Betfair back price).

All six are **immutable logging-time snapshots**. Never refreshed.
Not cache.

**Rationale for `betfair_implied_probability` as snapshot vs
derived:** DR-019 (derived state on read) wants derivation done at
read, not store, *unless* the derivation depends on time-of-logging
context that won't be reproducible later. Betfair-implied probability
at logging *is* time-of-logging context — the price moves,
reconstructing it later means going to capture.db. Snapshot is
correct.

**Rationale for `scheduled_start_time` as snapshot:** the time at
logging matters for "did I bet 30 seconds before jump or 30 minutes
before" analytics.

**Rationale for six fields total (not fewer):** Set B's purpose is
to make bet display readable without ever joining to capture.db.
Cutting the set down breaks that property.

### Round 8 — `strategy_tag` inference from racing-screen promo

**Operator surfaced operational flow detail:** On the racing page,
the operator pre-populates the promo type before the bet logs. The
modal already knows the promo when it opens.

**Decision: `strategy_tag` is inferred from racing-screen promo
selection at modal open.** Not operator-typed at the modal.

**Inference rules:**
- Promo = insurance → `strategy_tag = safety_net`.
- Promo = bonus-winnings (free-bet or cash) → `strategy_tag =
  price_booster`.
- No promo selected → `strategy_tag = NULL` by default (account-
  health turnover).

**Strategy 3 (SGM) and Strategy 4 (synthetic each-way) are NOT
racing-screen-driven.** Neither is time-sensitive in the same way as
the racing-page EV-trigger flow. Operator sets those tags manually
at the modal when those workflows exist (Strategy 3 → W4.1 / W7;
Strategy 4 → later workflow).

**Modal allows override.** Racing page is suggestion; modal is the
lock. Override semantics: changing the tag at the modal is a normal
operation, not an exception. **No audit trail needed for tag
overrides at v1.**

**Fits cleanly with DR-032's entry-path inheritance pattern.** The
racing screen already drives Betfair `marketId` + `selectionId` into
the modal via DR-032; now also drives `strategy_tag`. Same flow,
one more field.

### Round 9 — Free-bet field design

**Free bets can come from anywhere:**
- Triggered from prior insurance bet (Strategy 1 cycle).
- Triggered from prior bonus-winnings free-bet payout (Strategy 2
  sub-shape (b) free-bet flavour).
- **Promotional / random / unsolicited from books** — operator
  flagged these explicitly. Need manual ledger entry path eventually.

**`is_free_bet` field source — Option 2 (racing-screen inference).**

**Decision: `is_free_bet` inherited from racing-screen promo
selection.** Modal opens with `is_free_bet` pre-populated when the
racing-screen promo type is free-bet-stake. Modal allows override
(rare, but pattern matches `strategy_tag`).

**Operator's reasoning (decisive):** free-bet hedging is time-
sensitive. Parameters need to be locked before the modal opens. The
racing-screen → modal flow is already the inheritance pattern for
`strategy_tag` and Betfair identifiers per DR-032. `is_free_bet`
riding the same flow is consistent and operationally efficient. v2's
design is the pattern v3 inherits.

**`free_bet_conversion_rate`:**
- **Stored on bet record at logging time.**
- **Default 65%** per math review §6.2 (66.99% realised at moderate
  odds, 83.56% at long odds).
- **Operator-overridable at modal.**
- **Default lives in a config constant** (not hardcoded into
  `staking.py`). Future tuning is a config edit, not a code edit.

**Conversion rate scope — only consumed by `pricing.py` for
Strategy 2 sub-shape (b) free-bet flavour.** Walking through the
strategies:
- **Strategy 1:** triggered free bet runs through its own cycle
  later. Conversion rate isn't relevant to staking the original
  insurance bet itself.
- **Strategy 2 sub-shape (a) price-uplift:** no free bet. Not
  relevant.
- **Strategy 2 sub-shape (b) bonus-winnings free-bet flavour:**
  conversion rate folds into `pricing.py`'s effective-odds
  synthesis. **This is the only place conversion rate impacts
  pricing math.**
- **Strategy 4:** no free bets. Not relevant.
- **Account-health (NULL):** no free bets. Not relevant.

**`realised_conversion_rate` — populated by W5 at settlement.** W4
leaves NULL at logging.

**Calculation rule (operator-specified):** realised conversion rate
is based on *whichever bet actually won*, not on theoretical
equalised outcome.

**Rationale:** Betfair-price-drift edge case is real. When the hedge
stake doesn't precisely equalise outcomes (because Betfair moved
between operator clicking and bet matching), one leg pays slightly
more than the other on a settled cycle. The realised conversion rate
reflects whichever leg actually won, not theoretical equalisation.
Rare but the math has to handle it cleanly.

**Schema implication:** `free_bet_conversion_rate` field exists on
bet record at logging time (assumed rate); `realised_conversion_rate`
field exists on bet record but is W5's territory at settlement.
Brief notes this as W5 forward-routing item.

**Manual free-bet ledger entry: out of W4 scope.** Free bets from
promotional / random / unsolicited sources need manual ledger entry;
that workflow lives in W6+ / future workflow brief, not W4.

### Round 10 — Strategy 2 sub-shape (b) two-flavour split

**Operator clarification:** Strategy 2 sub-shape (b) bonus-winnings
has **two flavours**:
- **Free-bet bonus-winnings** — bonus comes as free bet, runs
  through future cycle, ~65% conversion. Uses `free_bet_conversion_
  rate` in `pricing.py`.
- **Cash bonus-winnings** — bonus is cash, no future cycle, no
  conversion-rate question. Effective odds calculation is simpler:
  `original_odds × (1 + cash_bonus_rate)` on win.

**Decision: `pricing.py` handles two distinct effective-odds paths.**
Both are Strategy 2 sub-shape (b) but mathematically distinct.

**Tightened `pricing.py` scope (full):**
- **Insurance promos (Strategy 1):** no `pricing.py` involvement.
- **Price-uplift Strategy 2 sub-shape (a):** no `pricing.py`
  involvement (price uplift paid at settlement, not logging — bet
  is staked at advertised odds).
- **Free-bet bonus-winnings:** `pricing.py` synthesises with
  conversion rate.
- **Cash bonus-winnings:** `pricing.py` synthesises with cash bonus
  rate.
- **Strategy 4 / clean turnover / NULL:** no `pricing.py` involvement.

**Racing-screen contract implication:** the racing-screen promo
selector must distinguish free-bet vs cash bonus-winnings as
separate promo types. That selection drives which `pricing.py` path
fires. Flagged in brief as W4 dependency on W7's racing-screen
contract.

**Free-bet stake calculation uses math review §2 (free-bet hedge
math), not standard cash-stake hedge formula.** The two are
materially different — free bets pay winnings only, no stake return.
Brief references math review §2 explicitly as the formula source.

### Round 11 — Stale-price flag at modal level

**Call:** Modal behaviour when Betfair API is slow / returns stale
data / unreachable at modal-open time.

**Decision: Option 2 — modal opens with last-known prices, stale
flagged.**

**Stale threshold:** 2 seconds, configurable. Matches the ~1-second
cadence of v2's Betfair direct line.

**Stale-price display additions (operator-added):** on top of binary
staleness flag, modal displays elapsed time since last update ("last
updated X seconds ago"). W4's data contract includes the price
source timestamp so W7 can render the elapsed time.

**Rationale:**
- Hedge entry is time-sensitive. Blocking the modal (Option 1) costs
  the operator the bet entirely if Betfair has a hiccup.
- Operator is strategic decision-maker — flagging stale prices and
  letting operator decide is consistent with operator-Claude
  division of labour.
- "Stale" threshold is configurable; v1 ships at 2 seconds.
- **No system-side prevention of placing against stale prices** —
  operator judgement call.

### Round 12 — Bet-record write failure handling (initial draft)

**Call:** What does W4 do when bet-record write fails at logging
time?

**Initial decision: Option 3 — automatic retry with backoff (50ms,
200ms, 500ms), then fail loud if persistent.** Modal preserves
entry data on persistent failure.

**[Reframed in Round 13 after operator surfaced workflow ordering
correction.]**

### Round 13 — Workflow ordering correction and four-failure-path framework

**Operator correction (load-bearing):** the actual workflow ordering
in v2 differs from Claude's initial assumption.

**Corrected workflow:**
1. Operator selects soft-book bet on racing page, picks promo,
   enters odds.
2. Operator waits for EV trigger. **Operator places bet at soft
   book** (real-money exposure 1 of 2).
3. Operator opens **Betfair hedge modal in BetHub.** Modal pre-
   populates from racing-page data. Modal calculates and surfaces
   hedge stake.
4. Operator confirms hedge → **Betfair API order placed** (real-
   money exposure 2 of 2). Hedge bet record written automatically
   on API success.
5. **Log-bet screen comes up.** Operator enters details of soft-book
   bet. **Soft-book bet record logged in BetHub.**

**Critical ordering: soft-book bet placed first; Betfair hedge
placed second; soft-book log happens last (after both legs are
placed at books / exchange).** This is time-sensitive; hedge has to
go in fast after soft-book placement.

**Operator note:** Strategy 1 is rarely hedged. Hedging matters
mostly for Strategy 2 (boosted odds, bonus winnings). Strategy 1's
EV comes from refund layer; hedging would forfeit it.

**Four failure paths reframed against corrected ordering:**

- **(a) Betfair hedge stake calculation fails (modal step 3 prep).**
  Soft-book bet already placed; no Betfair exposure yet. **Operator
  exposed on soft-book side.** Critical financial-risk path.
- **(b) Betfair API order placement fails (step 4).** Soft-book bet
  placed; Betfair order rejected by exchange. **Operator exposed on
  soft-book side only.** Critical financial-risk path.
- **(c) Betfair hedge log write fails (step 4 success path, BetHub
  local DB write).** Both legs placed; BetHub failed to log hedge
  record. **Position is closed (no monetary risk).** Standard
  record-keeping path.
- **(d) Soft-book log write fails (step 5).** Both legs placed;
  Betfair hedge logged; soft-book log fails. **Position is closed
  (no monetary risk).** Standard record-keeping path.

### Round 14 — Severity-weighted error framework (operator-driven)

**Operator reframe (decisive):** failure-mode severity is by
**financial risk**, not by code-path complexity.

- **Paths (a) and (b) are critical** — operator has unhedged
  exposure. Real money at risk. Priority is minimising time-to-
  recovery.
- **Paths (c) and (d) are standard** — record-keeping failures only.
  Position is closed; no monetary risk. Operator confirmed bug
  experience: D very occasionally happens; lower severity because
  position has been closed; manual recovery is acceptable.

**Locked: severity-weighted error framework.**

**Path (a) — hedge calculation failure:**
- Critical, fail-loud-fast, no retry.
- Surface message: "Soft-book bet placed at book; Betfair hedge
  calculation failed. You are exposed on the soft-book side.
  Recovery options: retry calculation, manually hedge through
  Betfair directly, or accept unhedged position."

**Path (b) — Betfair API order failure:**
- Critical with retry-safe error categorisation.
- **Retry-safe errors** (transient network, rate limit, exchange
  busy): auto-retry, 3 attempts, exponential backoff (50ms, 200ms,
  500ms).
- **Terminal errors** (insufficient funds, market closed, market
  suspended, invalid stake): fail-loud-fast, no retry.
- Surface message names the specific exchange error and recovery
  options.
- **Most terminal errors prevented by pre-flight checks** (Round
  15) — terminal errors at API time become exceptions, not the
  common case.

**Path (c) — Betfair hedge log write failure:**
- Standard.
- Retry-with-backoff (3 attempts, 50ms / 200ms / 500ms).
- Persistent failure surfaces non-urgently. Manual ledger entry is
  known-good fallback.
- Modal preserves entry data indefinitely (exposure-on-both-sides
  case; data must not be lost even though severity is standard).

**Path (d) — soft-book log write failure:**
- Standard.
- Retry-with-backoff.
- Persistent failure surfaces non-urgently. Manual entry recovery.
- Modal preserves entry data.

**Brief framing:** error semantics structured under financial-risk
lens. Critical-path messages designed for fast operator action;
W7 UI prominence reflects this. Standard-path messages designed for
record-keeping cleanup; W7 lower prominence acceptable.

### Round 15 — Pre-flight checks scoped down + partial-matching schema

**Pre-flight checks final scope (operator simplification):**

**Dropped:** page-level Betfair balance threshold flag. Operator
generally aware of balance; not high-value for the complexity it
adds (racing/sports pages would need to read Betfair state).

**Kept (modal-level only):**
- **Market status check** (closed / suspended) — Betfair API call
  modal makes for pricing anyway; data on hand. Surfaces "Market
  closed" / "Market currently suspended — wait for resumption" at
  modal.
- **Proposed-stake fundedness check** — Betfair balance read once at
  modal-open for this single check. Surfaces "Insufficient Betfair
  funds for proposed hedge of $X" at modal before confirm click.

**`orchestrator.py` exposes:**
```
pre_flight_check(market_id, selection_id, proposed_stake) ->
  PreFlightResult
```
returning market status + proposed-stake fundedness + operator-
actionable flags. No racing/sports page state-reading.

**UI rendering by W7.** Data contract is W4's.

**Partial matching on Betfair hedge orders:**

**Operator requirement (decisive):** historical bet records must
show *what actually matched and what didn't*. If $73 of a $100
order matched at 2.40 and $27 lapsed unmatched, both numbers must
be in the bet record permanently. Useful for analysis later.

**Schema implication: generalised stake fields across all bet
records (Option A).**

Every bet record carries:
- `requested_stake` — what the operator submitted ($100 in example).
- `matched_stake` — what actually matched ($73).
- `unmatched_stake` — what didn't match and lapsed ($27).
  Calculable from the other two but stored explicitly for
  analytical clarity.
- `matched_price` — the price at which the matched portion filled.
- `match_status` — five-value enum, see below.

**For non-hedge bets:** `requested_stake = matched_stake` always;
`unmatched_stake = 0`. Schema uniformity (Option A) chosen over
Option B (hedge-only fields) because:
1. DR-032 favours uniformity (single-leg bets are bets-with-one-leg).
2. Soft-book bets can also partially match in unusual cases (some
   books offer best-available pricing; some have minimum-stake
   adjustments at confirmation). Generalising handles future cases.
3. Analytical queries simpler — "show me all bets where matched <
   requested" works across all bet types.

**`match_status` five-value enum:**
- `final_full` — order fully matched at requested or better price.
- `final_partial` — order partially matched, remainder lapsed at
  race start / market close.
- `provisional` — order placed, reconciliation pass not yet
  completed (transient state, normally exists for ~5 seconds).
- `provisional_pending` — order partially matched, reconciliation
  pass completed but unmatched portion still pending in market
  (rare; flagged for operator review).
- `failed` — order rejected by exchange, no matching occurred.

**Hybrid Trigger A + Trigger B for hedge record writes:**

**Trigger A (immediate):** `placeOrders` API success → write
provisional hedge record using API response data. Mark
`match_status = 'provisional'`. Guarantees immediate logging even
if operator's session ends right after.

**Trigger B (reconciliation pass):** 5 seconds after order placement
(configurable), `orchestrator.py` calls `listCurrentOrders` for the
placed order ID. Updates the hedge record with finalised match
data. Marks `match_status = 'final_full'` or `'final_partial'`.

**Streaming subscription preferred when available:** if Betfair
streaming subscription is up at W4-shipping time (W2/W3 dependency),
reconciliation pass uses the order stream. Polling fallback
otherwise. Brief specifies both paths; doesn't require streaming.

**Final fallback for unusual cases:** if reconciliation can't
establish a final state within reasonable window (e.g. 30 seconds),
record stays `provisional_pending`. Surfaces to operator for manual
review at Betfair directly.

**Trigger B as broader sync-based reconciliation safety net** (catch
missed Trigger A writes from path (c) failures) is **W6 territory**,
not W4. W4 ships per-order reconciliation only.

**DR-032 schema clarification:** `match_status` and the generalised
stake fields fit within DR-032 as **operational state**, not
principle change. **No DR-032 amendment needed.** Brief specifies
the fields. Brief notes population logic per bet type.

### Round 16 — Return contract pattern

**Call:** Pydantic models vs dicts vs tuples; exceptions vs result-
type.

**Decision: Pydantic v2 models for return shapes; result-type for
operational errors.** Per DR-031 (the v3 tech stack decision).

**`orchestrator.py` exposes three main entry-point functions:**
- `pre_flight_check(...) -> PreFlightResult`
- `place_hedge(...) -> HedgePlacementResult`
- `log_soft_book_bet(...) -> SoftBookLogResult`

**Result-type pattern carries the four-error-path framework
explicitly** in the result instance: `error_path` ∈ {a, b, c, d},
`severity` ∈ {critical, standard}, `recovery_options`,
`error_detail`. Caller (W7) checks `result.success`; doesn't wrap
in try/except for normal operational paths.

**Exceptions reserved for programmer errors** — invalid input types,
schema violations, bugs.

**Operator confirmed:** technical-shape call inside Cat 5 (software
questions are Claude's). Locked.

### Round 17 — Hard limits and out-of-scope

**Hard limits — what Code must not exceed:**
1. Single bounded session.
2. Module set fixed at four (no additional modules, no splits, no
   merges).
3. DR-032 schema is the bet-record contract; no schema changes mid-
   session. Schema gaps surface as findings, not silent additions.
4. No edits outside `workflow/bet_entry/v1/`.
5. Pre-flight check stays modal-only (no page-level state-reading).
6. No UI rendering work (W7 territory).
7. Reconciliation pass scope is per-order only (W6 owns broader
   sync-based reconciliation).
8. Test coverage: unit tests for pure modules + mocked-API
   integration tests for `orchestrator.py`. No real-API integration
   tests.

**Test coverage scope (operator delegated to Claude as developer
call):** tighter scope. Reasoning:
- W4 is first v3 build workstream; test-environment plumbing is a
  separate workstream of its own.
- Operational use is the strongest integration test signal —
  manual-first / fix-as-needed pattern from v2.
- Real Betfair API behaviour mismatch with mock is unlikely (mock
  built against locked `betfair_client_contract.md` v1.0).

**Explicitly out of scope (named to prevent drift):**
1. W4.1 (soft-book typed-price entry path).
2. W6 (operational store schema). Bet record / bet leg tables get
   *defined* in this brief but *table creation, migration, broader
   schema* lives in W6.
3. W7 (UI / modal rendering).
4. Strategy 3 (SGM) implementation.
5. Manual free-bet ledger entry workflow.
6. Modal mechanics from math review §4 (carried to W7).
7. Multi-rung ladder hedge (math review §7.2 future arc).
8. Page-level Betfair balance threshold flag (dropped at
   simplification).
9. Settlement worker logic (W5 territory).
10. Broader reconciliation safety net (W6 territory).
11. Streaming subscription dependency (W4 uses if available;
    polling fallback if not).

---

## Drafting checkpoint

**On disk Session 91:**
- Brief skeleton at `dr029/w4_bet_entry/w4_bet_entry_brief.md`
  (321 lines).
- Sections §1 (scope) and §2 (module shape) drafted.
- Sections §3 onward have placeholder headings; Session 92 drafts
  the rest.

**Substrate this file captures (Session 92 reads):**
- 17 design rounds locked in detail above.
- Each call's rationale preserved.
- Operator-driven corrections preserved verbatim where they
  reframe Claude's initial position.
- Cross-references to math review sections, DR-032 clauses, and
  prior session decisions.

---

## Session 92 drafting checklist (proposed)

**Sections to draft (in order):**
1. **§3 Contract substrate mapping** — DR-032 fields per module,
   field population sources, generalised stake fields, `match_
   status` semantics, Set B six-field list, `strategy_tag` enum,
   `is_free_bet` inheritance, `free_bet_conversion_rate` defaults.
2. **§4 Pre-flight checks** — `pre_flight_check()` data contract,
   market status check, proposed-stake fundedness check, modal-only
   scope.
3. **§5 Error semantics** — four-error-path framework with
   severity weighting, retry-with-backoff policy, retry-safe vs
   terminal Betfair API error categorisation, surface messages per
   path, modal data preservation rules.
4. **§6 Reconciliation pass design** — Trigger A + B hybrid, 5-
   second window, streaming-vs-polling logic, `match_status` state
   transitions, fallback for stuck-pending orders.
5. **§7 Pre-reads** — files Code reads before starting (math
   review §1–§7 minus §4, DR-032, `architecture.md` §A.10, DR-027,
   DR-028, DR-030, DR-031, `betfair_client_contract.md`).
6. **§8 System access** — Betfair API (read-write for orders), v3
   operational store (read-write for bet records), no VPS, no
   capture.db. Adelaide local timestamps per DR-021.
7. **§9 Sequencing within session** — module build order
   (`record_builder.py` first, `pricing.py` and `staking.py`
   parallel, `orchestrator.py` last as composition layer; tests
   alongside each).
8. **§10 Empirical verification and acceptance** — pytest pass on
   pure-module tests; mocked-orchestrator tests pass; manual
   acceptance is operator-side post-brief (single test bet through
   the full flow against a small Betfair stake).
9. **§11 Output spec** — single named file at
   `dr029/w4_bet_entry/w4_bet_entry_report.md`. Section structure
   (modules built / tests passing / open questions / deviations
   from brief). Length range 300–500 lines.
10. **§12 Hard limits** — eight items above, named explicitly.
11. **§13 What happens after Code's session** — operator-Claude
    triage session reads report, surfaces findings, routes to
    next workstream (W4.1 brief, W7 brief, or fix follow-up).
    Code does not produce next brief.
12. **§14 Cross-references** — DR-027, DR-028, DR-030, DR-031,
    DR-032, DR-019, DR-026, DR-022, DR-021; math review §1–§7;
    architecture.md §A.10; W4 substrate decisions Session 87, 88,
    89, 90.

**Estimated length when complete:** ~700–900 lines total brief.
Drafting cadence per Cat 1 (call-driven, section-by-section).

**Likely operator-facing calls during Session 92 drafting:**
- Sequencing within session — module build order has alternatives;
  may surface a call.
- Length range for report — estimate may need operator adjustment.
- Pre-read list — confirm whether `betfair_client_contract.md`
  should be required-read or reference-only.
- Possibly: streaming-vs-polling preference for reconciliation
  pass if W2/W3 dependency status is unclear.

Most other sections are mechanical from the substrate.

---

## Outstanding items not requiring draft inclusion

These are surfaced from Session 91 but live in carry-forward
streams, not in W4 brief:

- **Manual free-bet ledger entry workflow** — W6+ / future workflow
  brief. Captured in `current_state.md` open items.
- **Page-level Betfair balance flag** — explicitly dropped from W4
  v1; not a parked item (operator chose simplicity).
- **Streaming subscription readiness** — W2/W3 dependency status
  check before W4 ships. May surface as a Session 92 question
  during §6 drafting.
- **Real-Betfair test environment** — out of W4 scope; future
  workstream of its own.

---

## Locked summary (one-screen reference)

- **Scope:** hedge entry only; modal mechanics → W7.
- **Modules (4 at `workflow/bet_entry/v1/`):** orchestrator (impure),
  staking (pure, math review §2 free-bet hedge), pricing (pure,
  bonus-winnings only — both flavours), record_builder (pure, DR-032
  contract).
- **Math review reference:** by anchor; not embedded.
- **`strategy_tag`:** four-tag enum + nullable; racing-screen
  inferred; modal override allowed.
- **Set B:** 6 immutable logging-time fields per leg.
- **`is_free_bet`:** racing-screen inherited; modal override.
- **`free_bet_conversion_rate`:** stored on bet record; default 65%
  (config); only consumed by `pricing.py` for free-bet bonus-winnings.
- **`realised_conversion_rate`:** W5 populates at settlement;
  whichever leg actually won.
- **Pre-flight:** modal-only; market status + stake fundedness.
- **Error framework:** severity-weighted; (a)/(b) critical, (c)/(d)
  standard; retry-with-backoff for retry-safe errors; result-type
  return pattern.
- **Stake fields generalised:** `requested_stake`, `matched_stake`,
  `unmatched_stake`, `matched_price`, `match_status` (5-value enum)
  on all bet records.
- **Reconciliation:** Trigger A + B hybrid; 5s window; streaming if
  available, polling fallback.
- **Test scope:** unit tests pure modules + mocked-API tests
  orchestrator. No real-API integration tests.
- **Hard limits:** 8 items locked. **Out-of-scope:** 11 items named.
