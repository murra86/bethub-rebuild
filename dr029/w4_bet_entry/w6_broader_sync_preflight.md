# W6 broader-sync reconciliation pre-flight grounding

**Captured:** 2026-05-07 (Session 103)
**Source:** empirical inspection of post-Session-101 codebase + governance docs
**Purpose:** anchor scope decisions for `w6_broader_sync_brief.md`
  drafting

---

## §1 — Codebase state, post-Session-101 ship

### §1.1 — W4 module layout

`bethub-v3/workflows/bet_entry/v1/`:

- `__init__.py` — 119 lines.
- `betfair_adapter.py` — 406 lines (post-Session-101: real wraps for
  three reads + `get_order_state` real wrap closing the W4 §8.1
  finding).
- `models.py` — 355 lines (Pydantic shapes; `MatchStatus` enum at
  line 42; `BetRecord` / `BetLeg` at 142 / 191).
- `orchestrator.py` — 1459 lines (post-Session-101: +103 LOC from
  `ReadOk` / `ReadUnavailable` / `ReadOutcome[T]` discriminated
  union plus call-site updates).
- `pricing.py` — 194 lines.
- `record_builder.py` — 375 lines.
- `staking.py` — 400 lines.
- `storage.py` — 440 lines (the W4 v1 stub Protocol +
  in-memory + SQLite reference impls).

### §1.2 — `MatchStatus` enum (the W6-relevant states)

`models.py:42-56` defines five values:

- `FINAL_FULL` — Trigger B confirmed full match. Terminal.
- `FINAL_PARTIAL` — Trigger B confirmed partial match (some matched,
  some unmatched at jump or cancelled by jump). Terminal.
- `PROVISIONAL` — Trigger B's read failed (`ReadUnavailable`); we
  don't yet know what matched. **W6 sweeps these.**
- `PROVISIONAL_PENDING` — Trigger B's read returned but bet still
  has unmatched stake at Trigger B time (5s post-placement); a
  state W6 must distinguish from `PROVISIONAL` because
  `PROVISIONAL_PENDING` is "we know there's unmatched still
  pending" whereas `PROVISIONAL` is "we don't know the state".
  **W6 sweeps these too** (resolves them once the unmatched
  resolves at Betfair-side).
- `FAILED` — Terminal exchange rejection (placement failed
  outright). Terminal.

### §1.3 — Orchestrator's own reference to W6

`orchestrator.py:962-985` — `_run_trigger_b` docstring reads:

> Failure handling per §6.4: single retry at +10s if the
> read fails, then leave `provisional` for W6's broader
> sync reconciliation to pick up later (out of W4 scope).

And the failure log message:

> "Trigger B read unavailable for bet_id=%s (reason=%s); record
> stays provisional (W6 sync reconciliation will pick up)."

This is the orchestrator's own contract for what W6 is for: pick
up `MatchStatus.PROVISIONAL` and resolve to terminal.

### §1.4 — `BetRecord` / `BetLeg` schema (DR-032)

`models.py:142-225`:

- `BetRecord` carries `match_status: MatchStatus`,
  `matched_stake / unmatched_stake / requested_stake`,
  `matched_price`, `betfair_bet_id` (nullable; populated for
  hedge legs).
- `BetLeg` (per-leg, hedge-side carries the canonical
  `betfair_market_id` + `betfair_selection_id` per DR-032 §1).
- **No `last_reconciled_at` field, no `reconciliation_attempts`
  field** — W6 must add them (or omit, see §4 scope decisions).

### §1.5 — Storage Protocol (`BetRecordStorage`)

`storage.py:60-78` defines three methods:

- `write_bet_record(record: BetRecord) -> WriteResult`
- `update_match_status(bet_id, status, matched_stake,
  unmatched_stake, matched_price) -> WriteResult`
- `read_bet_record(bet_id: str) -> BetRecord | None`

**No query method that returns "all `PROVISIONAL` bets" or any
filtered set.** W6 needs at minimum:
`list_unreconciled_bets(...) -> list[BetRecord]` (or equivalent
filter shape).

### §1.6 — Reference SQLite schema (`storage.py:90-127`)

`bets` table: bet-as-a-whole columns including `match_status` (TEXT)
plus `betfair_bet_id` (TEXT, nullable).
`bet_legs` table: per-leg with `betfair_market_id`,
`betfair_selection_id`, six Set B fields per DR-032.

**Implication for W6's query strategy:** the join for "what
markets do unreconciled bets cover?" is
`bets ⋈ bet_legs WHERE bets.match_status IN
('provisional', 'provisional_pending')`.

---

## §2 — Betfair-side settlement read surfaces

### §2.1 — Existing W3 surfaces (post-Session-101 contract v1.4)

Eight read surfaces in `betfair_client_contract.md` (line 187 still
reads "seven" — Session 102 housekeeping carry):

- §9.1 — operational live-pricing reads (streaming-cached or REST
  fetch).
- §9.2 — settlement reads (market-scoped: `market_settlement(market_id)`).
  **Not bet-scoped.** Per `settlement.py:79-118`, returns
  `MarketSettlement` with `market_id`, `market_status`,
  `settled_time`, per-runner `RunnerSettlement` records (`WINNER`
  / `LOSER` / `REMOVED` plus `bsp` plus `voided`),
  `market_voided`, plus three count fields (`dead_heat_count`,
  `removed_runner_count`, `unexpected_state_count`).
- §9.3 — sports-line query.
- §9.4 — scheduled-time reads.
- §9.5 — identifier-resolution checks.
- §9.6 — account funds (v1.2 carve-out).
- §9.7 — market catalogue read.
- §9.8 — order-state reads (`list_current_orders`, v1.4 carve-out;
  Trigger B's surface).

### §2.2 — `listClearedOrders` is OUT OF SCOPE in v1.4 contract

Contract §15.4 (line 1480):

> Carve-out (v1.4): `list_current_orders` is in scope per §9.8
> ... `listClearedOrders` (post-settlement archival query) ...
> remain out of scope.

**Implication for W6:** if W6 reads Betfair's archive of
cleared orders to resolve `MatchStatus.PROVISIONAL` bets, the
brief must spec a **new W3 surface (§9.x addition)** plus an
**API tier verification step** (per §15.4 the contract carved
out only what existing surfaces require; cleared-orders may be
on a different membership tier — per current_state.md
"Betfair API membership tiers — investigate"
operator-side homework, still pending).

### §2.3 — `market_settlement(market_id)` is the §2.6 surface

§2.6 (settlement model — race path) names `market_settlement` as
the load-bearing read for the **settlement state machine** (the
`pending` → `settled_won` / `settled_lost` / `voided` /
`provisional` transitions). This surface already exists in W3 at
`settlement.py` and is in the v1.4 contract at §9.2.

### §2.4 — Sweep candidate (p) check

Contract §6 version-history rows (per `betfair_client_contract.md`
header/Status line at line 3):

- v1.0 — Session 75 lock + Session 77 draft.
- v1.1 — Session 87 (F5 strategy_tag).
- v1.2 — Session 94 (`get_account_funds` + `get_market_catalogue`).
- v1.3 — Session 96 (REST-fetch fallback clarification).
- v1.4 — Session 101 (§9.8 `list_current_orders`).

**Latest version: v1.4. Five rows.** W6 brief must assume v1.4 and
plan v1.5 if a new surface is added. Sweep candidate (p) satisfied:
brief's pre-flight grounding has explicitly verified contract
version + history row count.

---

## §3 — Two reconciliation surfaces, not one — the scope question

### §3.1 — The mismatch

Two separate streams reach into "W6":

- **W6a (match-state reconciliation, Session 102 §7.2 carry).**
  Sweep `MatchStatus.PROVISIONAL` / `PROVISIONAL_PENDING` bets and
  resolve to terminal `MatchStatus`. The orchestrator's own
  contract says W6 picks these up. The §7.2 settlement-state
  ambiguity (cancelled / voided / lapsed bets vs fully matched)
  was Option-A-locked into "W6's territory" last session.

- **W6b (settlement-state reconciliation, §2.6 spec).** Sweep
  bets where `MatchStatus` is terminal (`FINAL_FULL` /
  `FINAL_PARTIAL`) but the Betfair Win market hasn't settled yet.
  Transition `settlement_state` (a field that doesn't yet exist on
  `BetRecord` — §2.8 §6.4 specified it but W4 didn't ship it)
  through `pending` → `settled_won` / `settled_lost` / `voided` /
  `provisional`. Surface to burst-review queue when triggered.

### §3.2 — Why the two are distinct

- W6a operates on **match status** (did the bet take effect at
  Betfair?) and reads `listCurrentOrders` (W3 §9.8) plus
  potentially `listClearedOrders` (new W3 surface). Time-frame:
  seconds-to-minutes post-placement.
- W6b operates on **settlement state** (did the race finish, and
  did our runner win?) and reads `market_settlement` (W3 §9.2).
  Time-frame: minutes-to-hours post-race-jump.

A bet can be in any combination of (W6a state × W6b state):
match-resolved + race-not-yet-jumped (most common); match-resolved +
race-settled (terminal); match-still-provisional + race-already-
jumped (rare; suggests a longer Trigger B failure window than
expected).

### §3.3 — Both scopes have load-bearing carry items

W6a load-bearing carries:

- §7.2 settlement-state differentiation (cancelled / voided /
  lapsed vs fully matched).
- §8.6 broader-sync reconciliation carry.
- Storage-interface query method extensions.
- F5 strategy_tag carry (W6 reads tagged strategy info — only
  load-bearing if W6 emits per-strategy reconciliation metrics
  or filters; otherwise informational).

W6b load-bearing carries:

- §2.6 entire spec (five-state machine, three count fields,
  past-window flag, burst-review surfacing contract).
- Past-settlement-window threshold calibration (30-minute v3
  day-one default).
- Settlement worker periodic verification cadence (§3.4
  condition 2 — re-read terminal-state bets to catch
  post-settlement voids).
- §2.9 §4.4 six edge cases (analytical-line side; awareness, no
  mitigation built).

### §3.4 — Brief shape implication

If W6 covers both surfaces, the brief is large — likely 1500+
lines drawing on §2.6 spec (~640 lines), the storage-interface
extensions, the new W3 §9.x for `listClearedOrders` (if needed),
the schema additions for `settlement_state` field, and two
worker implementations. Sequencing within the same Code session
is tight.

If W6 covers W6a only, brief is W3-precedent-shaped (~1200 lines
estimated), W6b sequenced as a follow-up (W6.5 or "W6b" or
absorbed into v3 build proper post-DR-029-close).

If W6 covers W6b only, the §7.2 carry from Session 102 doesn't
get addressed in W6 — it carries forward to a later brief.

---

## §4 — Other scope decisions surfaced

### §4.1 — Storage Protocol additions needed (W6a)

At minimum:

- `list_unreconciled_bets(*, statuses: tuple[MatchStatus, ...] |
  None = None, older_than: datetime | None = None) ->
  list[BetRecord]` — query filter by status + age.
- `update_reconciliation(bet_id: str, *, last_reconciled_at:
  datetime, attempts: int) -> WriteResult` — bookkeeping write.
- New schema columns: `last_reconciled_at TEXT`,
  `reconciliation_attempts INTEGER DEFAULT 0`.

### §4.2 — Schema migration framework (the named debt)

`governance.md` §4 names "no migration framework" as one of the
three pieces of DR-029 named debt. W6's schema additions
(`last_reconciled_at`, `reconciliation_attempts` for W6a;
`settlement_state` plus three count fields for W6b) are the
first place that debt becomes load-bearing — adding columns to
existing tables in the SQLite reference impl needs an explicit
migration path even at v1 storage.

DR-031 (v3 tech stack) names Alembic for migrations. W6 brief
either spec's lightweight DDL-only migrations inline (single
ALTER TABLE per column, idempotent at startup) or names Alembic
adoption as a precondition. Recommend inline — Alembic adoption
is post-DR-029 work; W6 needs to ship without blocking on it.

### §4.3 — Worker substrate (APScheduler vs threading vs asyncio)

`orchestrator.py:286-385` already defines `TriggerBScheduler`
Protocol with two impls (`ManualTriggerBScheduler`,
`ThreadingTriggerBScheduler`). W6's worker can mirror this —
Protocol + threading reference + manual stub for tests.

DR-031 names FastAPI / asyncio in v3 build proper. W6's worker
sits behind a Protocol so the substrate is swappable at
composition root.

### §4.4 — Cadence (a v3 operational parameter, not architectural)

W6a worker cadence: every N minutes sweep `PROVISIONAL` bets
older than M seconds. v3 day-one defaults TBD; calibrate from
operational experience. Suggest brief leaves as v1 placeholder
constants (5-minute sweep, 60-second age threshold) and names
calibration as v3-build-proper operational tuning.

W6b worker cadence: §2.6 §5.4 names this as v3-build-proper
operational tuning, not §2.6 (or W6) spec.

### §4.5 — Past-settlement-window threshold (W6b only)

§2.6 §3.3 names 30 minutes from race finish for v3 day-one,
calibrate from operational experience. W6b brief either takes
this as the literal default or proposes a different
v3-day-one number. Recommend the literal §2.6 default; matches
the operator's own framing language.

### §4.6 — Audit-trail substrate (the named debt)

`governance.md` §4 second piece of debt: "no audit-log durable
substrate selected". W6's auto-resolution writes (`provisional` →
terminal) per §2.6 §3.5 require audit-trail entries. W6 brief
either ships v1 audit-trail-as-DB-column (e.g.
`audit_log: JSON | None` on the bets table, append-only
JSON entries) or names the durable-substrate selection as a
W6 dependency to land first.

Recommend v1 audit-trail-as-JSON-column inside the bets row
for W6 v1; durable substrate selection deferred.

---

## §5 — Anchors for brief drafting

If W6a-only:

- Universal twelve-section spine per W3 brief precedent.
- §5 substantive scope sub-sections likely:
  - §5.1 New W3 module `cleared_orders.py` (or extension to
    `current_orders.py`) for `listClearedOrders` if needed.
  - §5.2 Contract §9.x addition (v1.5).
  - §5.3 `BetRecordStorage` Protocol extensions (new query
    methods + bookkeeping write).
  - §5.4 SQLite reference impl extensions (new columns,
    inline DDL migration).
  - §5.5 New W6 module `bet_entry/v1/reconciliation.py` (or
    `broader_sync.py`) — worker module.
  - §5.6 Worker scheduler Protocol mirroring
    `TriggerBScheduler`.
  - §5.7 Adapter extension for `listClearedOrders` reads.
  - §5.8 `MockBetfairAdapter` updates.
  - §5.9 Worker tests.
  - §5.10 Adapter tests for new read.
  - §5.11 Storage tests.
  - §5.12 Schema-migration test (idempotency).
- Test count delta target: +20 to +30.
- Output report at
  `dr029/w4_bet_entry/w6_broader_sync_report.md`.
- Length anticipation: 800-1200 lines.

If W6 covers both surfaces:

- Larger brief (~1500-1800 lines).
- Two worker modules, two cadences, two state machines.
- Risk of single-Code-session over-budget per W6 brief
  precedent (W3 brief shipped within budget at 1156 lines;
  W6 dual-surface would push into riskier territory).

---

## §6 — Summary call

Three calls surface for the operator before brief drafting
proceeds:

- **Call A — W6 scope width.** W6a only (match-state
  reconciliation, `MatchStatus.PROVISIONAL` sweep, closes §7.2
  settlement-state ambiguity), W6b only (settlement-state
  reconciliation, §2.6 worker), or both?
- **Call B — `listClearedOrders` decision.** If W6a: does it
  read `listClearedOrders` (new W3 surface, contract v1.5,
  potentially API-tier-gated) or just `listCurrentOrders` plus
  Betfair's settlement-time stamping (best-effort
  match-resolution from absence-from-current-orders + market
  settlement)?
- **Call C — Schema migration framework.** Inline DDL-only
  migrations (single ALTER TABLE per column, idempotent at
  startup) shipping with W6, or Alembic adoption as a
  precondition before W6?

Recommended path: **W6a only, with read strategy that combines
`listCurrentOrders` (already in v1.4) + `market_settlement`
(already in v1.4 §9.2) — no new W3 surface. Inline DDL
migrations. W6b deferred to a follow-up brief (W6.5 or
sequenced after W7) that specifically lifts §2.6 into v3
operational substrate.**

This keeps the W6 brief within W3-precedent shape, closes the
§7.2 carry, and defers the §2.6 worker work to a separate
session that can do justice to its scope.
