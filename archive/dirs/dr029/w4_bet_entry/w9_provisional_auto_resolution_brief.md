# W9 — Provisional auto-resolution brief

**Drafted:** 2026-05-10 ACST (Adelaide local per DR-021)
**Source spec:** `dr029/2_6_settlement_race/2_6_settlement_race.md` (§2.6,
§3.2 transitions from `provisional`).
**Predecessors:** W6.5 settlement worker (1316-line brief, 850-line report,
shipped Session 105). W8 burst-review queue (671-line brief, 1340-line
report, shipped Session 109).
**Shape:** surgical extension to the W6.5 settlement worker. Closest
precedent: W6.1 anomaly_reason_code surgical amendment (542-line brief,
shipped Session 105).
**Status at lock:** awaiting operator review.

---

## §1 What this brief is and is not

W9 commissions Code to add a **second pass shape** to the W6.5
settlement worker — a sweep over `PROVISIONAL` bets that re-reads
the Betfair Win market and auto-resolves to terminal settlement
states when the market has settled cleanly. Per §2.6 §3.2, this
is the deferred half of the spec — W6.5 implemented the
`pending → provisional` direction; W9 implements the
`provisional → settled_won / settled_lost / voided` direction.

W9 also adds a **side-effect** on every settlement-worker read
(both PENDING and PROVISIONAL passes): the `MarketSettlement`
payload returned by the read is persisted onto the bet record as
a new column `last_read_market_state`. The W8 burst-review modal
currently renders an explainer ("No persisted market read at v1")
because no such persistence existed; W9 closes that gap so the
modal shows the actual market state Betfair reported on the
worker's last read.

This is a **single bounded Code session**. Code reads this brief
end-to-end, executes against named anchors only, and produces one
report at the named output path. Surprises become §6 deviations or
§7 findings, not blockers. Remediation routes to operator-Claude
triage in the next session, never inside Code's report.

Specifically in scope:

- A new `last_read_market_state: MarketSettlement | None` field on
  `BetRecord`. Default `None` for backward compatibility.
- A new column on the bets table — JSON-serialised
  `MarketSettlement` payload — with idempotent inline DDL
  migration via the existing `_add_column_if_missing` helper.
  Reader (`_row_to_record`) deserialises; INSERT writes; new
  storage method `update_last_read_market_state` writes the
  side-effect.
- A new pass-loop entry point `run_provisional_resolution_pass`
  in `workflows/bet_entry/v1/settlement.py`, structurally
  parallel to `run_settlement_pass` but filtering on
  `(SettlementState.PROVISIONAL,)` and using a parallel resolver
  `_resolve_provisional_for_bet` that handles the
  PROVISIONAL-staying fall-through correctly.
- A new `SettlementProvisionalPassResult` Pydantic model — counter
  shape adjusted for the PROVISIONAL→terminal transitions plus
  the PROVISIONAL-stays carry.
- An extension to `run_settlement_pass` (the existing PENDING
  sweep) and `run_provisional_resolution_pass` (the new sweep)
  that persists `last_read_market_state` via the new storage
  write whenever a Betfair read succeeds — regardless of whether
  the read produces a state transition. This is the side-effect
  that closes the W8 modal visibility gap.
- An update to `_build_surfacing_payload` and the storage's
  `list_provisional_settlement_bets` query so the surfacing
  payload's `last_read_market_state` field is sourced from the
  persisted column rather than passed as `None` unconditionally.
- Tests for all of the above — covers the new pass loop, the
  PROVISIONAL→terminal transitions, the side-effect persistence
  on both pass shapes, the surfacing payload's now-populated
  field, the storage round-trip on the new column, and an
  integration test covering both passes plus the side-effect.

Specifically not in scope (see §9 hard limits for the full list):

- No changes to `clients.betfair_client.v1.settlement`. The
  v1.0 surface is shipped; the worker calls it.
- No changes to W6's reconciliation worker
  (`reconciliation.py`).
- No implementation of §2.6 §3.4 condition 2 (post-settlement
  market voided re-transition from terminal state). W6.5
  deferred this; W9 inherits the deferral. The worker reads bets
  in PENDING and PROVISIONAL only; terminal-state bets are not
  re-read at v1.
- No settlement worker cadence specification. §2.6 §2.4 leaves
  cadence to §2.4 or v3 build proper. W9 ships the
  PROVISIONAL pass-loop primitive at a default cadence (same
  60-second pass interval as the PENDING sweep); the trigger
  model that wraps it is build-proper.
- No burst-review queue UI changes. W8 already renders
  `last_read_market_state` when non-null; W9 only changes how
  the field gets populated upstream. The W8 surface continues
  working as-is.
- No Alembic migration. W9 uses the same `_add_column_if_missing`
  inline DDL pattern W6 / W6.5 established.
- No audit-trail surface for settlement transitions. W8 §7.1
  open question; capability 7 in `governance.md` §4. Manual
  operator transitions still log via worker logger (W8 ship
  state); auto-resolution transitions added by W9 follow the
  same logging pattern. Persisted audit trail is a separate
  brief.
- No `ProvisionalTriggerSource` enum changes. The
  `POST_SETTLEMENT_VOID` value remains defined-but-unused at
  v1; W9 doesn't change that.

This is a **surgical extension brief**, not a substrate-plus-
worker brief. Closest precedent: W6.1 anomaly_reason_code surgical
amendment (Session 105 ship). The §-section spine mirrors
surgical-fix shape (Sessions 35, 36, 105, 109): named anchors in
dependency order, sequencing call, empirical verification pre/post,
hard limits explicit. Length envelope sits between W6.1 (542
lines) and W6.5 (1316 lines) — the side-effect persistence makes
it slightly larger than W6.1 because it touches both pass shapes
and the storage column.

## §2 Why this work exists

§2.6 of `dr029/2_6_settlement_race/2_6_settlement_race.md`
specifies v3's race-path settlement model. §3.2 names the
transitions from `provisional`:

> From `provisional` (auto-resolution path):
> - → `settled_won` if a subsequent settlement read returns clean `WINNER`.
> - → `settled_lost` if a subsequent settlement read returns clean `LOSER`.
> - → `voided` if a subsequent settlement read returns `REMOVED` or market void.

W6.5 explicitly deferred this path. From the W6.5 brief §5.5
Change C ("Note on §2.6 §3.4 condition 2 — post-settlement market
voided"):

> The worker only reads bets in PENDING.

And from the W6.5 report §5 implementation notes:

> The worker only reads bets in PENDING; it does not re-read
> terminal-state bets. Manual operator escalation into PROVISIONAL
> is the v1 substitute.

The deferral was sound at W6.5 — that brief was already 1316 lines
landing the canonical PENDING→terminal path plus the
PROVISIONAL surfacing payload. Adding the PROVISIONAL re-sweep
inside W6.5 would have doubled the brief's envelope.

W8 then shipped the operator-facing surface for PROVISIONAL bets
(W8 §3.5 / §3.6 / §3.7 — burst-review queue, modal, manual
operator resolution). W8's modal renders `last_read_market_state`
when non-null but currently always sees `None` because the W6.5
storage helper passes `last_read=None` unconditionally
(W8 report §6.1 / §6.2 visible at the modal:
"No persisted market read at v1. The settlement worker's last
snapshot is not stored on the bet record yet — see W6.5 report
§5.6 for the carry-forward.").

W9 closes both gaps in one bounded session: the auto-resolution
direction of §2.6 §3.2, plus the persistence side-effect that
makes W8's modal useful.

§2.6 §3.6 (operator note from Session 74 framing) names why
PROVISIONAL earns its keep — the auto-resolution path means
low-friction cases self-clear without operator burden, manual
action remains available for cases that need it. W6.5 + W8
delivered the manual half; W9 delivers the auto-resolution half
that closes the operational loop.

## §3 Pre-reads

Required reads (in order, before drafting any code):

1. `dr029/2_6_settlement_race/2_6_settlement_race.md` §3.2 (the
   transitions from `provisional`), §3.4 (the trigger conditions
   into `provisional`), §3.5 (the burst-review surfacing
   contract), §4.3 (stewards' protest upheld after Betfair
   settlement — the canonical case W9 closes) — read in full.
2. `dr029/w4_bet_entry/w6_5_settlement_worker_brief.md` §5.4–§5.6
   (the constants, helpers, decision logic, surfacing payload that
   W9 extends).
3. `dr029/w4_bet_entry/w6_5_settlement_worker_report.md` §5
   (implementation notes, esp. the §5.6 surfacing-payload notes
   on `last_read=None` at v1).
4. `dr029/w4_bet_entry/w8_burst_review_queue_report.md` §3.5
   (`apply_manual_operator_resolution` shape — the manual
   operator path W9 mirrors structurally), §3.7 (the modal's
   rendering of `last_read_market_state`).
5. `workflows/bet_entry/v1/models.py` (412 lines) — `BetRecord`
   shape, `SettlementState` enum, the W6.5 settlement field
   block (lines 261–272), the `is_past_settlement_window`
   computed property (lines 274–293).
6. `workflows/bet_entry/v1/settlement.py` (878 lines) — the W6.5
   ship state. Read end-to-end. Anchor on:
   - `_resolve_settlement_for_bet` (lines 280–415) — the read-side
     resolver W9's PROVISIONAL resolver mirrors with one branch
     change.
   - `run_settlement_pass` (lines 419–571) — the pass loop W9's
     PROVISIONAL pass mirrors with a different filter and
     different counter shape.
   - `_write_settlement_bookkeeping` (lines 573–595) — the
     bookkeeping helper W9 reuses unchanged.
   - `apply_manual_operator_resolution` (lines 651–732) — the W8
     manual path; structurally similar transition write that W9's
     auto-resolution write mirrors.
   - `__all__` (lines 856–878) — the exports list W9 extends.
7. `workflows/bet_entry/v1/storage.py` (1000 lines) — the storage
   layer. Anchor on:
   - `BetRecordStorage` Protocol (lines 65–186) — three new
     entries needed for W9 (the `last_read_market_state` write,
     possibly an extension to `list_provisional_settlement_bets`).
   - `_BETS_DDL` (lines 195–219) — schema W9 extends with one
     new column.
   - `InMemoryBetRecordStorage.list_provisional_settlement_bets`
     (lines 431–470) and `SQLiteBetRecordStorage.
     list_provisional_settlement_bets` (lines 860–897) — the two
     surfacing-payload query implementations W9 updates so
     `last_read=...` sources from the persisted column.
   - `_row_to_record` (lines 940–989) — the reader W9 extends
     with the new column deserialisation.
8. `tests/workflows/bet_entry/v1/test_settlement.py` (1597 lines)
   — read structure of Block 1–7. W9 adds a Block 8 for
   PROVISIONAL pass tests, plus extends Block 1 / 2 / 5 for the
   side-effect persistence. Look at existing helpers
   (`_make_record`, the `T0_PLUS_300S` Adelaide-local clock pin,
   `MockSettlementReader`, fixture patterns) — W9 reuses these.
9. `clients/betfair_client/v1/settlement.py` (118 lines) — the
   `MarketSettlement` Pydantic model shape. W9 needs to JSON-
   serialise it for storage and deserialise on read; the
   model's existing Pydantic v2 shape supports
   `model_dump_json()` / `model_validate_json()` natively. No
   modification.

Reference-only (consult on demand, not required cover-to-cover):

- `decisions.md` — DR-021 (timestamp anchoring), DR-027
  (two-database architecture), DR-028 (cross-database integration
  boundary discipline), DR-030 (v3 repo layout / module-boundary
  discipline), DR-031 (v3 tech stack: Pydantic v2, SQLite WAL,
  ruff, lint-imports, pytest), DR-032 (canonical-reference-layer
  for all bet records).
- `architecture.md` §A.10 (canonical source identifiers), §B.1.4
  (sports-path settlement model — sibling reference).
- `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  §9.2 (settlement reads — the existing v1.0 surface).
- `dr029/w4_bet_entry/w6_5_settlement_worker_brief.md` §5.7
  (scheduler classes — referenced for stylistic precedent if W9
  needs to wire a second scheduler instance for the PROVISIONAL
  pass; design call in §5 below).
- `governance.md` §4 (capability 7 — audit-trail surface for
  settlement transitions; out of scope for W9 but the worker
  logger pattern W6.5 / W8 established applies to W9's new
  transitions identically).

## §4 System access

- **Filesystem (read-write):** Mac local at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Edit anchors named
  in §5 only.
- **Working tree:** dirty per W6 + W6.1 + W6.5 + W7 + W8 ship
  pattern. Operator's in-flight work has not landed since W8.
  Pre-baseline `git status` capture at session start; post-
  baseline `git status` capture at session close. The dirty-file
  list does not change across the session — W9's edits land
  inside the existing untracked W4 namespace.
- **Python interpreter:** `.venv/bin/python` (3.12.7) per W6.1 /
  W6.5 / W8 precedent. Invoke via the venv interpreter
  explicitly (W6 §8.1 finding mitigation).
- **Database (read-write):** in-process SQLite via the existing
  `SQLiteBetRecordStorage` reference implementation. No external
  database. No live Betfair API calls — all tests use mocked
  adapters per the W6 / W6.5 / W8 pattern.
- **Tests:** `pytest` from the venv. Pre-baseline run at session
  start to establish the count (expected 486 from W8 ship);
  post-baseline run at session end to verify net-new test
  delta.
- **No git operations.** No `git add`, `git commit`, `git stash`,
  `git restore`, `git checkout`, `git reset`. The brief's edit
  anchors land inside already-untracked / already-modified files
  in the `workflows/bet_entry/v1/` namespace plus the existing
  `tests/workflows/bet_entry/v1/` namespace; the dirty-file list
  does not change.
- **Adelaide local timestamps per DR-021.** All session
  timestamps, all test fixtures, all log lines.

## §5 Substantive scope sections

§5 names every change W9 makes. Anchors are file + region. Code
edits only what's named here.

### §5.1 — `BetRecord` field addition

**File:** `workflows/bet_entry/v1/models.py`

**Change A — `last_read_market_state` field.** Add to `BetRecord`
immediately after the W6.5 `unexpected_state_count` field
(line 271 in current ship), before the `legs` tuple. The field
type is `MarketSettlement | None` — the same type the settlement
worker reads from `clients.betfair_client.v1.settlement`. Default
`None` for backward compatibility with pre-W9 records.

```
# W9 — last MarketSettlement read by the settlement worker per
# §2.6 §3.5. Persisted as JSON on the bets row; deserialised on
# read. Populated on every successful settlement-worker read
# (PENDING and PROVISIONAL passes), regardless of whether the
# read produces a state transition. Default None for pre-W9
# records and bets the worker has not yet read.
last_read_market_state: MarketSettlement | None = None
```

**Note on circular import.** `MarketSettlement` lives in
`clients.betfair_client.v1.settlement`. `models.py` does not
currently import from `clients/`. The import lands at the top
of the module per the existing W6.5 pattern in `settlement.py`
(which imports the same type). DR-030 layered architecture
permits W4 internals importing the W3 betfair_client surface;
the W6.5 ship already exercises this path through `settlement.py`
and the lint-imports contracts confirm it stays clean.

### §5.2 — Storage schema migration + DDL + reader/writer extensions

**File:** `workflows/bet_entry/v1/storage.py`

**Change A — `_BETS_DDL` extension.** Add one column to the DDL,
positioned after `unexpected_state_count`:

```
last_read_market_state       TEXT             -- W9 — nullable JSON
```

Position: after `unexpected_state_count` (the last existing W6.5
column), before the closing `)`.

**Change B — `_connect_and_init` migration.** Add one
`_add_column_if_missing` call inside the existing migration block,
immediately after the W6.5 calls. Idempotent and consistent with
the W6 / W6.5 pattern:

```
_add_column_if_missing(conn, "bets", "last_read_market_state", "TEXT")
```

**Change C — `write_bet_record` INSERT extension.** Add one
column to the INSERT column list and the values tuple. Position:
after `unexpected_state_count`. Value follows the JSON-as-text
pattern:

```
(
    record.last_read_market_state.model_dump_json()
    if record.last_read_market_state is not None
    else None
),
```

**Change D — `_row_to_record` extension.** Read the new column
from the bet row and populate it on the `BetRecord` constructor.
Pattern follows the existing optional-typed-field readers:

```
last_read_market_state=(
    MarketSettlement.model_validate_json(
        bet_row["last_read_market_state"]
    )
    if bet_row["last_read_market_state"] is not None
    else None
),
```

`MarketSettlement` import in `storage.py` lands alongside the
existing `BetLeg` / `BetRecord` / etc. imports; the import-graph
addition is a single edge captured in `lint-imports`. DR-030
layered architecture permits W4 storage importing the W3
betfair_client surface for type purposes.

**Change E — `BetRecordStorage` Protocol method:
`update_last_read_market_state`.** Add to the Protocol (and to
both implementations). Signature:

```
def update_last_read_market_state(
    self,
    bet_id: str,
    *,
    last_read_market_state: MarketSettlement | None,
) -> WriteResult:
    """W9 brief §5.2 — side-effect write distinct from
    `update_settlement_state`. Writes the persisted MarketSettlement
    column on a successful settlement-worker read. The worker
    calls this on every successful read (PENDING and PROVISIONAL
    passes), regardless of whether the read produces a state
    transition.

    `last_read_market_state=None` is a valid input — clears the
    column. Reserved for tests / diagnostic use; the worker only
    ever passes a non-None value.
    """
    ...
```

Implementation in `SQLiteBetRecordStorage` mirrors
`update_settlement_state`'s shape: single UPDATE inside the lock,
returns `WriteResult(success=False, error_message="bet_id not
found")` if `cursor.rowcount == 0`. Implementation in
`InMemoryBetRecordStorage` mirrors the same pattern via
`model_copy(update={...})`.

**Change F — `list_provisional_settlement_bets` update.** Both
implementations (`InMemoryBetRecordStorage` and
`SQLiteBetRecordStorage`) currently call
`_build_surfacing_payload(..., last_read=None, ...)`
unconditionally (storage.py lines 463 / 891). Update both to
pass `last_read=bet.last_read_market_state` — sourcing the field
from the bet record's persisted column rather than the
unconditional `None`.

This is a one-line change per implementation. The
`ProvisionalSettlementSurfacingPayload` model already accepts
`MarketSettlement | None` for the field; no payload-shape
changes needed. The W8 modal already renders the persisted-or-
absent paths correctly per W8 report §3.7.

### §5.3 — `settlement.py` — new resolver for PROVISIONAL bets

**File:** `workflows/bet_entry/v1/settlement.py`

**Change A — `_resolve_provisional_for_bet` function.** New pure
read-side resolver, structurally parallel to
`_resolve_settlement_for_bet` (line 280) but with the
fall-through case staying PROVISIONAL rather than transitioning
into it. Six-step logic mirroring the existing resolver:

```
def _resolve_provisional_for_bet(
    *,
    record: BetRecord,
    settlement_reader: SettlementReader,
) -> SettlementDecision:
    """W9 brief §5.3 — given a bet record currently in
    PROVISIONAL and a settlement reader, decide what the bet's
    `settlement_state` should resolve to per §2.6 §3.2's
    auto-resolution path.

    Read steps (in order):

    1. Read the Betfair Win market via `settlement_reader.read(
       market_id=...)` using the leg's `betfair_market_id`.
    2. Read returned ReadUnavailable → no decision; reason
       `read_unavailable_settlement`. Bet stays PROVISIONAL.
    3. `market_status != CLOSED` → no decision; reason
       `market_not_yet_closed`. Bet stays PROVISIONAL.
       (Transient — the bet was put into PROVISIONAL because of
       a prior read; this case implies the market state has
       reverted, which is an unusual edge case but defensively
       handled as "stays PROVISIONAL" rather than transitioning.)
    4. `settled_time is None` (CLOSED but not yet settlement-
       stamped) → no decision; reason `market_not_yet_settled`.
       Bet stays PROVISIONAL.
    5. `market_voided` → `SettlementState.VOIDED` with reason
       `voided_market_voided`. Auto-resolution clears the bet
       cleanly (§2.6 §3.2).
    6. Find the runner matching the leg's `betfair_selection_id`:
       - REMOVED → VOIDED with reason `voided_runner_removed`.
       - WINNER → SETTLED_WON with reason `settled_won`.
       - LOSER → SETTLED_LOST with reason `settled_lost`.
       - None / other → **stays PROVISIONAL** with reason
         `provisional_unexpected_state`. Decision's `new_state`
         is None — the bet is already in PROVISIONAL, no
         transition needed; the worker logs the unexpected
         state for visibility but does not write a state change.

    All terminal-state transitions populate the three count
    fields from the same MarketSettlement response. The fall-
    through (stays-PROVISIONAL) case populates count fields as
    None on the decision — since no transition fires, the
    existing count fields on the bet record are not overwritten.

    Pure read-side — does no writes. The pass-level worker
    (`run_provisional_resolution_pass`) takes the decision and
    applies it to storage.
    """
```

**Key difference from `_resolve_settlement_for_bet`:** the
fall-through case (runner not in market, or unexpected runner
status) returns `new_state=None` rather than
`new_state=SettlementState.PROVISIONAL`. The bet is **already** in
PROVISIONAL; transitioning it back to PROVISIONAL is a no-op and
would pollute the audit log with spurious "transitioned to same
state" entries. Decision's reason code stays
`provisional_unexpected_state` for log visibility; the pass loop
counts these as a "stayed PROVISIONAL" carry rather than as a
transition.

The same applies to step 5 (`market_voided`) and step 6 (clean
WINNER / LOSER / REMOVED) — these are real transitions out of
PROVISIONAL and the resolver returns the appropriate terminal
state.

**§2.6 §3.4 condition 2 (post-settlement market voided
re-transition from terminal state) — out of scope.** W9 reads
PENDING and PROVISIONAL bets only; it does not re-read terminal-
state bets. Carried forward to build-proper per W6.5 brief §5.5
Change C; W9 inherits the deferral.

**Change B — `SettlementProvisionalPassResult` Pydantic model.**
New pass-level summary distinct from `SettlementPassResult` (the
existing PENDING-pass result). Counter shape:

```
class SettlementProvisionalPassResult(BaseModel):
    """W9 brief §5.3 — pass-level summary returned by
    `run_provisional_resolution_pass`. Counters are inclusive
    across the swept population.

    Differs from `SettlementPassResult` in that the
    `provisional_entered` counter does not exist (the population
    is already PROVISIONAL); a `stayed_provisional` carry-counter
    captures bets that the read did not resolve. Otherwise
    structurally parallel.
    """

    model_config = ConfigDict(frozen=True)

    swept_count: int
    settled_won: int
    settled_lost: int
    voided: int
    stayed_provisional_market_not_closed: int
    stayed_provisional_market_not_settled: int
    stayed_provisional_read_unavailable: int
    stayed_provisional_unexpected_state: int
    last_read_persisted_count: int  # W9 §5.4 side-effect counter
    started_at: datetime  # Adelaide local per DR-021
    finished_at: datetime
    pass_id: str  # uuid4 hex for log correlation
```

Eight counter classes. The `last_read_persisted_count` is the
side-effect counter — bumped once per bet whose Betfair read
succeeded (i.e. did not return `ReadUnavailable`), regardless of
whether the read produced a state transition. Useful for
operator-facing observability of "the worker is doing its
side-effect job" distinct from "the worker is transitioning
bets".

**Change C — `run_provisional_resolution_pass` function.** New
pass-loop entry point, structurally parallel to
`run_settlement_pass` (line 419):

```
def run_provisional_resolution_pass(
    *,
    storage: BetRecordStorage,
    settlement_reader: SettlementReader,
    max_results: int = 100,
    now: Callable[[], datetime] | None = None,
) -> SettlementProvisionalPassResult:
    """W9 brief §5.3 — single pass over PROVISIONAL bets.

    Queries unresolved PROVISIONAL bets via
    `storage.list_unsettled_bets(settlement_states=
    (SettlementState.PROVISIONAL,), max_results=...)`, resolves
    each via `_resolve_provisional_for_bet`, writes settlement-
    state updates via `storage.update_settlement_state` for
    transitions, persists `last_read_market_state` via
    `storage.update_last_read_market_state` whenever the read
    succeeded (per §5.4), and writes bookkeeping via
    `storage.update_reconciliation_bookkeeping` per W6's shared
    substrate per W6.5 §5.5 Change G.

    No `older_than_event_start` filter — bets in PROVISIONAL are
    by definition past the race start time (the PENDING pass
    transitioned them based on a Betfair read, which only fires
    once the race is over). The age filter is redundant for this
    population.

    Idempotent across calls. Returns a
    `SettlementProvisionalPassResult`.
    """
```

**Note on age filter omission.** The existing
`run_settlement_pass` uses `age_threshold_seconds` (default 300s)
to skip bets whose race hasn't run yet. PROVISIONAL bets cannot
be in that pre-race state — they reached PROVISIONAL by going
through a Betfair read that returned an unexpected state, which
only happens after the market closed. The PROVISIONAL pass
therefore omits the age filter. The pass still uses `max_results`
to bound per-pass population and Betfair-call budget.

### §5.4 — `last_read_market_state` side-effect persistence

The side-effect closes the W8 modal visibility gap by persisting
the worker's most recent successful Betfair read onto the bet
record.

**Change A — extension to `run_settlement_pass`** (the existing
PENDING pass). After every successful settlement read — i.e.
when the read did **not** return `ReadUnavailable` — call
`storage.update_last_read_market_state(bet_id,
last_read_market_state=settlement)` to persist the
`MarketSettlement` payload. The write happens after the
state-transition write (when applicable) and after the bookkeeping
write, in the same per-bet loop iteration.

Place the persistence call inside the existing pass loop, after
`_write_settlement_bookkeeping`. Failure mode: if the
side-effect write returns `WriteResult(success=False, ...)`,
log a warning (mirroring the bookkeeping-write failure pattern at
`_write_settlement_bookkeeping`) but do not fail the pass — the
state transition (if any) has already been committed; the
side-effect is an operator-visibility additive.

**Change B — `_resolve_settlement_for_bet` decision shape
extension.** The existing resolver returns a `SettlementDecision`
which does not carry the source `MarketSettlement` payload — only
derived fields (the three counts, the reason code, the detail
dict). The PENDING pass needs access to the source payload to
persist it via §5.4 Change A.

Two viable paths:

1. **Extend `SettlementDecision`** with a
   `source_market_settlement: MarketSettlement | None` field —
   populated whenever the read succeeded (i.e. all branches
   except `read_unavailable_settlement`), `None` otherwise.
2. **Restructure the loop** so the read result is captured
   alongside the decision and passed to the write step
   separately, without changing the decision model.

Code's call which lands cleaner. The brief leans toward path 1
(extend the model) — keeps the decision self-contained, no
parallel state-tracking variable in the loop body, and the new
field is straightforwardly testable. Path 2 might keep the
decision model leaner but at the cost of looser pass-loop shape.
If Code picks path 2, flag in §6 deviation.

**Change C — extension to `run_provisional_resolution_pass`.**
Same side-effect persistence as Change A, applied to the new
PROVISIONAL pass. The persistence fires on every successful
Betfair read regardless of whether the read produces a transition
out of PROVISIONAL. The `last_read_persisted_count` counter on
`SettlementProvisionalPassResult` (per §5.3 Change B) tracks how
many bets had the side-effect applied.

The PROVISIONAL pass writing `last_read_market_state` means the
W8 modal's display of "current Betfair Win market state as last
read" stays fresh across multiple worker passes — useful for
PROVISIONAL bets that the worker can't auto-resolve (unexpected
state cases), since the operator's manual decision benefits from
seeing the latest market state Betfair reported.

### §5.5 — `_build_surfacing_payload` — no signature change, called differently

**File:** `workflows/bet_entry/v1/settlement.py`

`_build_surfacing_payload` (line 246) takes
`last_read: MarketSettlement | None` as a keyword argument. The
helper itself does not change — the change is at the call sites.

**Change A — InMemoryBetRecordStorage callers.** Per §5.2
Change F: source `last_read=bet.last_read_market_state` rather
than `last_read=None`.

**Change B — SQLiteBetRecordStorage callers.** Same — source
from the bet record, not unconditional None.

That's the entire §5.5 change. No new function, no model
changes. The persistence side-effect at §5.4 makes the field
populated on the bet record; this section just routes the
populated value through to the surfacing payload that the W8
modal reads.

### §5.6 — Scheduler wiring

**File:** `workflows/bet_entry/v1/settlement.py`

The W6.5 ship has `ManualSettlementScheduler` and
`ThreadingSettlementScheduler` — both currently unwired in
production. Build-proper will compose schedulers around both
pass shapes; W9 does **not** wire schedulers because:

- Production composition lives in build-proper, not in worker
  modules per DR-030 (layered architecture).
- The existing scheduler classes work for either pass shape —
  they take a `Callable[[], None]` and an interval; the
  PROVISIONAL pass is a `Callable[[], None]` once partially
  applied with its storage / reader / etc. arguments.
- Tests for `run_provisional_resolution_pass` exercise the pass
  shape directly via `ManualSettlementScheduler.flush()` per the
  existing scheduler test pattern (test_settlement.py
  scheduler block).

No new scheduler classes. No new `__all__` entries for
schedulers. The `__all__` extension at §5.10 covers the new
public symbols (`_resolve_provisional_for_bet`,
`run_provisional_resolution_pass`,
`SettlementProvisionalPassResult`).

### §5.7 — Update existing logging on W6.5 manual operator path
(consistency only)

**File:** `workflows/bet_entry/v1/settlement.py`

The W8 manual-operator path at `apply_manual_operator_resolution`
(line 651) emits an INFO log line on every transition. The auto-
resolution path W9 ships emits the same shape of log line per
pass-loop transition (mirroring the existing
`run_settlement_pass` LOG.info pattern at line 521). The two log
shapes need to be parallel for operator log triage:

- **Auto path (W9 new)**: `"settlement auto-resolved bet_id=%s:
  provisional -> %s (reason=%s)"` — mirrors the existing PENDING-
  pass log shape.
- **Manual path (W8 existing)**: `"settlement manual operator
  resolution: bet_id=%s, previous_state=provisional,
  new_state=%s, operator_reason=%s, applied_at=%s"` — unchanged
  by W9.

W9 does **not** modify the W8 manual-path log shape. The two
shapes are different by design — the manual path carries the
operator reason, the auto path doesn't have one. Naming this
explicitly so Code doesn't drift toward unifying the two log
formats.

### §5.8 — Tests

**File:** `tests/workflows/bet_entry/v1/test_settlement.py` —
extended.

The test module currently runs ~50 tests across Blocks 1–7 (W6.5
+ W8). W9 adds Block 8 plus extensions to Blocks 1, 2, and 5
for the side-effect.

**Block 1 extension (the existing `_resolve_settlement_for_bet`
block) — tests for `_resolve_provisional_for_bet`:**

1. `test_resolve_provisional_returns_settled_won_on_clean_winner`
2. `test_resolve_provisional_returns_settled_lost_on_clean_loser`
3. `test_resolve_provisional_returns_voided_on_runner_removed`
4. `test_resolve_provisional_returns_voided_on_market_voided`
5. `test_resolve_provisional_stays_provisional_on_runner_not_in_market`
   — fall-through returns `new_state=None`.
6. `test_resolve_provisional_stays_provisional_on_unexpected_runner_status`
   — fall-through returns `new_state=None`.
7. `test_resolve_provisional_stays_provisional_on_market_not_yet_closed`
   — defensive case; bet stays PROVISIONAL.
8. `test_resolve_provisional_stays_provisional_on_market_closed_no_settled_time`
   — bet stays PROVISIONAL.
9. `test_resolve_provisional_stays_provisional_on_settlement_read_unavailable`
   — bet stays PROVISIONAL; carries reason verbatim.

**Block 2 extension (the existing `run_settlement_pass` block) —
tests for `run_provisional_resolution_pass`:**

1. `test_provisional_pass_sweeps_only_provisional_bets` —
   PENDING / terminal-state bets excluded.
2. `test_provisional_pass_increments_settled_won_counter`.
3. `test_provisional_pass_increments_settled_lost_counter`.
4. `test_provisional_pass_increments_voided_counter`.
5. `test_provisional_pass_increments_stayed_provisional_counters_correctly`
   — three bets, three different stays-PROVISIONAL reasons,
   three counters.
6. `test_provisional_pass_writes_bookkeeping_per_bet_per_pass` —
   shared substrate with the PENDING pass per W6.5 §5.5
   Change G.
7. `test_provisional_pass_handles_storage_update_failure_on_state_write`
   — storage UPDATE returns failure → counted as carry, no raise.
8. `test_provisional_pass_handles_storage_update_failure_on_last_read_write`
   — side-effect write returns failure → log warning, do not
   fail pass, transition (if any) committed.
9. `test_provisional_pass_writes_count_fields_on_terminal_transition`
   — counts stamped on disk per state transition.
10. `test_provisional_pass_does_not_overwrite_count_fields_on_no_transition`
    — when bet stays PROVISIONAL, the existing counts on the bet
    record are not overwritten.
11. `test_provisional_pass_uses_adelaide_local_timestamps` —
    DR-021 coverage.
12. `test_provisional_pass_persists_last_read_market_state_on_successful_read`
    — side-effect counter increments per successful read.
13. `test_provisional_pass_does_not_persist_last_read_on_read_unavailable`
    — read failed → no side-effect write.
14. `test_provisional_pass_omits_age_filter` — bet with leg
    event_start very recent (within 60 seconds) is still swept
    when in PROVISIONAL.

**Block 2 further extension (existing `run_settlement_pass` —
side-effect):**

15. `test_settlement_pass_persists_last_read_market_state_on_successful_read`
    — the existing PENDING pass also persists the side-effect
    per §5.4 Change A.
16. `test_settlement_pass_does_not_persist_last_read_on_read_unavailable`
    — read failed → no side-effect write.

**Block 5 extension (the existing storage-layer block):**

17. `test_sqlite_last_read_market_state_round_trip` — write
    BetRecord with non-None field, read back via
    `read_bet_record`, assert `MarketSettlement.model_dump()`
    equality.
18. `test_sqlite_last_read_market_state_round_trip_with_none` —
    write with `last_read_market_state=None`, read back, assert
    None.
19. `test_sqlite_update_last_read_market_state_returns_not_found`
    — missing bet_id → `WriteResult(success=False)`.
20. `test_sqlite_last_read_market_state_column_migration_idempotent`
    — double-init is a no-op on the new ALTER TABLE.

**Block 4 extension (the existing burst-review surfacing
payload block):**

21. `test_surfacing_payload_carries_persisted_last_read_market_state`
    — bet record with non-None `last_read_market_state` →
    payload's field reflects the persisted value.
22. `test_surfacing_payload_last_read_remains_none_when_unpersisted`
    — bet record with `last_read_market_state=None` (e.g. worker
    hasn't run yet) → payload's field is None (the existing
    pre-W9 behaviour for not-yet-read bets).
23. `test_inmemory_list_provisional_settlement_bets_uses_persisted_last_read`
    — the InMemory query implementation surfaces the persisted
    field, not unconditional None.

**Block 8 (new) — Integration test:**

24. `test_end_to_end_pending_then_provisional_then_terminal_with_sqlite_storage`
    — single bet starts PENDING; PENDING pass reads market
    showing unexpected runner state, transitions bet to
    PROVISIONAL; second pass (PROVISIONAL) reads market showing
    clean WINNER, transitions bet to SETTLED_WON. End-to-end
    via SQLite reference store. Asserts on every intermediate
    state including `last_read_market_state` populated after
    both passes.

**Test count delta target: +24 net new tests** (486 → 510).
Acceptable band: 510-518 (+24 to +32) — Code may produce up to
8 additional tests for natural test boundaries surfacing during
write (e.g. additional defensive cases on the side-effect write,
additional fixture-shape coverage). Flag in §6 deviation if
outside the band.

### §5.9 — Smoke verification (post-W8 end-to-end shape)

**Optional, time-permitting.** W8 §5.9 established the full-stack
smoke-test pattern. W9 does not introduce new HTTP endpoints —
the W8 endpoints continue working unchanged — but the visible
behaviour change (W8 modal now showing actual market state when
the worker has read it) is worth verifying end-to-end if the
session has budget.

Smoke probe shape (mirrors W8 §5.9):

1. Spin up FastAPI on port 8765 against a clean DB.
2. Insert a synthetic bet in PROVISIONAL state with
   `last_read_market_state=None` via the W8 §5.9 fixture script
   pattern.
3. `curl GET /api/v1/bets/provisional` — confirms
   `last_read_market_state: null` (pre-W9-pass state).
4. Run `run_provisional_resolution_pass` against the same DB
   with a `MockSettlementReader` returning a clean
   MarketSettlement.
5. `curl GET /api/v1/bets/provisional` — if the bet auto-
   resolved, the queue is empty (clean WINNER); if the bet
   stayed PROVISIONAL (e.g. unexpected state), the queue still
   shows the bet but `last_read_market_state` is now populated.

**Code's call whether to run §5.9.** If pre-baseline tests + §5.1
through §5.8 take most of the session budget, skip §5.9 and flag
in §6 deviation. The unit + integration test coverage at §5.8
covers the worker-side wire shape; §5.9 only adds operator-
facing-surface verification, which is W8's territory and was
already smoke-tested at W8 ship.

### §5.10 — `__all__` exports

**File:** `workflows/bet_entry/v1/settlement.py`

Add to the existing `__all__` list (currently lines 856–878):

- `_resolve_provisional_for_bet`
- `run_provisional_resolution_pass`
- `SettlementProvisionalPassResult`

Position: alphabetically per the existing list shape. The
existing entries (`_resolve_settlement_for_bet`,
`run_settlement_pass`, `SettlementPassResult`) stay in place.

## §6 Sequencing within session

Code's session walks in dependency order:

1. **Models first** (§5.1) — `last_read_market_state` field on
   `BetRecord`. The field's default `None` means existing test
   fixtures stay valid without modification.
2. **Storage substrate** (§5.2) — DDL extension, migration call,
   `_row_to_record` reader, `write_bet_record` INSERT writer,
   new `update_last_read_market_state` Protocol method on both
   implementations, `list_provisional_settlement_bets` callers
   updated.
3. **Worker module — resolver** (§5.3 Change A) — new
   `_resolve_provisional_for_bet`. Pure function; no dependencies
   on any new substrate.
4. **Worker module — pass result model** (§5.3 Change B) —
   `SettlementProvisionalPassResult`.
5. **Worker module — pass loop** (§5.3 Change C) —
   `run_provisional_resolution_pass`. Depends on step 3 (the
   resolver) and step 2 (the storage methods).
6. **Side-effect persistence** (§5.4) — extend
   `_resolve_settlement_for_bet` and `run_settlement_pass` with
   the persistence call; same extension to the new
   `run_provisional_resolution_pass`. Depends on step 2 (the
   storage write method) and step 5 (the new pass loop).
7. **Surfacing payload routing** (§5.5) — already covered by
   §5.2 Change F; flagged here for completeness in case Code
   addresses §5.2 storage and §5.5 routing as separate sub-
   commits.
8. **Logging consistency** (§5.7) — auto-path log line shape;
   no new code, just consistency check during write.
9. **`__all__` exports** (§5.10) — extend the list once new
   public symbols exist.
10. **Tests** (§5.8) — covering all blocks. Run targeted
    before full-suite: `pytest tests/workflows/bet_entry/v1/
    test_settlement.py -v` first, then full-suite.
11. **Verification** (§7) — pre/post baselines on test count,
    ruff, lint-imports.
12. **(Optional) §5.9 smoke** — if budget permits.

The order is intentional. The new pass loop can't run before the
resolver exists; the side-effect persistence can't fire before
the storage write method exists; the surfacing payload's new
shape can't be tested before the storage column round-trips
correctly.

If a different order surfaces during execution as cleaner, Code
may deviate; flag the deviation in §6 of the report with the
reasoning. The dependency order above is the safe default; W6.5
report §6 / W8 report §6 establish that minor sequencing
deviations are routine and not a problem.

## §7 Empirical verification

### §7.1 — Pre-baseline (session open)

Capture all of the following:

- `pytest --collect-only -q | tail -1` — pre-baseline test count.
  Expected: 486 (W8 ship state per W8 report §2.1).
- `pytest -q` — full-suite pass/fail. Expected: 486 passed.
- `ruff check workflows/bet_entry/v1/ tests/workflows/bet_entry/v1/`
  — clean.
- `lint-imports` — 5 contracts kept, 0 broken (W8 ship: 120
  files, 336 dependencies).
- `git status` — capture the dirty-file list. No `git add` /
  `git commit` / `git stash` allowed; the snapshot is for the
  report's §9 self-assessment.
- For the optional smoke (§5.9): `npm run lint`, `npx vitest
  run`, `npm run build` — capture pre-baselines if the §5.9
  probe runs.

### §7.2 — Post-baseline (session close)

Re-run all of §7.1's commands.

Expected post-baseline:

- Test count: ~510 (+24 net new). Acceptable band: 510-518
  (+24 to +32); flag in §6 if outside the band.
- Full-suite pass: all green.
- `ruff check` clean.
- `lint-imports` 5 kept, 0 broken. Files / dependencies
  count may grow modestly (the new MarketSettlement import in
  storage.py adds an edge; the new pass-loop function adds
  imports captured by lint-imports' static analysis).
- `git status` — same dirty-file list at the file-level. No new
  untracked files at the root level. No modifications outside
  the named §5 anchors.

### §7.3 — Functional verification checklist

Code confirms in the report's §9 self-assessment:

- [ ] All `tests/workflows/bet_entry/v1/test_settlement.py` pass
      (existing + Block 1/2/4/5 extensions + Block 8 new).
- [ ] `tests/workflows/bet_entry/v1/test_reconciliation.py` still
      passes (no regressions from W6 / W6.1 substrate).
- [ ] `tests/workflows/bet_entry/v1/test_storage.py` still passes
      (storage extensions are additive).
- [ ] `tests/ui/api/test_provisional.py` still passes (W8
      endpoint tests — `last_read_market_state` field continues
      to surface; the path it takes through the API is unchanged
      from W8's perspective).
- [ ] Full suite passes.
- [ ] `ruff check` clean on the W4 + tests scope.
- [ ] `lint-imports` 5 contracts kept, 0 broken.
- [ ] No live Betfair API calls (mocked-only tests).
- [ ] No edits outside the §5 named anchors.
- [ ] No new untracked files.

### §7.4 — Sample model dumps

The report's §9 captures one full auto-resolution cycle's post-
write state via model dumps:

- A `BetRecord` after PROVISIONAL→SETTLED_WON auto-resolution
  shows `settlement_state="settled_won"`, the three count fields
  preserved from the original PROVISIONAL transition,
  `last_read_market_state` populated from the latest worker read,
  and `last_reconciled_at` / `reconciliation_attempts` stamped
  per pass.
- A `BetRecord` after the PENDING pass with the side-effect
  applied (no transition, just side-effect) shows
  `settlement_state="pending"` (unchanged), all count fields
  None, `last_read_market_state` populated, and
  `reconciliation_attempts=1`.
- A `ProvisionalSettlementSurfacingPayload` for a bet that
  stayed PROVISIONAL after a pass shows the
  `last_read_market_state` field populated with the latest
  market read — confirming the W8 modal will now render actual
  market state rather than the v1 "not stored" explainer.

These confirm the wire shape Session 112's W9 triage will read
against.

## §8 Output spec

**Path:** `dr029/w4_bet_entry/w9_provisional_auto_resolution_report.md`
(absolute: `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/
w4_bet_entry/w9_provisional_auto_resolution_report.md`).

**Length range:** 500-800 lines. The brief is ~700-900 lines;
W6.5 report at 850 lines was inside W6.5's brief envelope (1316
lines), W8 report at 1340 lines was outside W8's brief envelope
(671 lines). W9 sits between W6.1 surgical (305-line report) and
W6.5 substrate-plus-worker (850-line report) in shape — surgical
extension shape, slightly larger than W6.1 because of the side-
effect work touching both pass shapes. Flag in §9 self-assessment
if outside the band.

**Required structure:**

- **§1 Summary** — what shipped end-to-end in one paragraph plus
  the named-anchor checklist (A-G across §5.1–§5.10). Test count
  delta. ruff / lint-imports state.
- **§2 Files changed** — table of pre/post LOC for every file
  touched. No new files (this is a surgical extension to W6.5
  ship; new code lands inside `settlement.py`, `storage.py`,
  `models.py`, and `test_settlement.py`).
- **§3 Test count delta** — exact pre and post numbers, the +N
  delta, any band-flag.
- **§4 New tests added** — listed by block (1/2/4/5/8 per §5.8)
  with one-line description per test. Total test count by block.
- **§5 Implementation notes** — one sub-section per §5.x anchor.
  What landed, any inline decisions taken. The §5.4 Change B
  decision (extend `SettlementDecision` vs restructure the loop)
  is restated explicitly in the implementation note for
  visibility.
- **§6 Deviations from brief** — any deviation from the §5
  anchors, the §6 sequencing, or the test-count band. Expected:
  zero or one (the §5.4 Change B decision direction is the
  most likely deviation surface).
- **§7 Open questions for triage** — anything Code surfaced that
  the next operator-Claude session needs to resolve. Expected:
  zero or one. Audit-trail surface for auto-resolution
  transitions inherits W8 §7.1's open question; W9 doesn't add
  new audit gaps.
- **§8 Findings beyond brief scope** — anything Code noticed
  during execution that wasn't anchored in the brief but warrants
  surfacing. Expected: zero or one.
- **§9 Self-assessment** — pre/post baselines table per §7.1 /
  §7.2; functional verification checklist per §7.3 (10 items
  ticked); `git status` snapshots; length flag; DR-021 timestamp
  confirmation.

**What the report does not contain:**

- No recommendations for what to do next. Forward routing is
  Session 112's call.
- No proposals for fixes outside the brief's scope.
- No design changes from the §5 anchors. Anchor-level changes
  surface as §6 deviations.
- No `git` operations in the implementation notes.

## §9 Hard limits

Non-negotiable. Code does not, under any circumstances:

- **Modify `clients.betfair_client.v1.settlement`.** The v1.0
  surface is shipped. W9 reads it without modification.
- **Modify `clients.betfair_client.v1.envelope`** or any other
  `clients/` module. The brief touches `workflows/` and
  `tests/workflows/` only.
- **Modify W6's reconciliation worker** (`reconciliation.py`).
  W9 sits beside it; W6 substrate is W6 territory.
- **Modify the orchestrator** (`orchestrator.py`). The
  bet-entry write-time population of `settlement_state=PENDING`
  is W7 / build-proper territory.
- **Modify W8's manual operator path**
  (`apply_manual_operator_resolution`). W9's auto-resolution
  path is structurally parallel but separately implemented; do
  not factor common code between them at this brief's level
  (Code may surface a refactoring opportunity as §8 finding,
  but does not execute it).
- **Modify W8's UI surface** (`ui/api/routers/provisional.py`,
  any `ui/web/` files). W9 only changes how
  `last_read_market_state` gets populated upstream; the W8 surface
  continues working as-is.
- **Implement §2.6 §3.4 condition 2** (post-settlement market
  voided re-transition from terminal state). Out of scope per
  W6.5 inheritance; carry-forward to build-proper. The worker
  reads PENDING and PROVISIONAL bets only.
- **Implement settlement worker cadence / trigger model.** Out
  of scope per §1; the pass-loop primitive is shipped; the
  trigger that wraps it is build-proper.
- **Implement an audit-trail table for settlement transitions.**
  W8 §7.1 open question; capability 7 in `governance.md` §4.
  Both auto and manual transitions log via the worker logger
  (W6.5 / W8 ship pattern); W9 follows the same pattern. A
  persisted audit trail is a separate brief.
- **Implement scheduler wiring for the new pass.**
  Build-proper composes schedulers around both pass shapes; W9
  ships the pass-loop primitive only.
- **Implement Alembic migration.** Out of scope per §1; the
  inline DDL pattern from W6 / W6.5 is reused.
- **Edit `decisions.md`, `architecture.md`, `governance.md`,
  `standing_instructions.md`, `current_state.md`, or any
  rebuild-folder governance file.** Code-side governance touches
  are Chat-territory.
- **Run `git add` / `git commit` / `git stash` / `git restore` /
  `git checkout` (file-targeted) / `git reset`.** The dirty-tree
  state is preserved; `git status` is read-only.
- **Make live Betfair API calls.** All tests use mocked
  adapters. Code captures `git status` and the test count via
  `pytest`; nothing else hits a network.
- **Modify pre-W9 fields on `BetRecord` or in storage DDL.**
  The existing fields stay as they are; W9 adds one new field
  / one new column only.

If the brief's anchors and the live codebase diverge — for
example, a §5 anchor file has moved, an existing function shape
has changed, a test fixture is missing — Code surfaces the
mismatch as a §6 deviation in the report and stops at the
affected anchor; the remaining anchors that don't depend on the
affected one continue. The next operator-Claude session resolves
the mismatch.

## §10 What happens after Code's session

The next operator-Claude session (Session 112 by current
sequencing) runs W9 report triage via the inventory-first cadence
pattern (sweep candidate `(l)` — likely tenth concrete use):

1. Read the W9 report end-to-end.
2. Inventory pass — classify §6 deviations, §7 open questions,
   §8 findings as no-call (Code's territory, awareness only) or
   operator-call (warrants routing).
3. Walk operator-call items one-per-round. Resolve each.
4. Forward routing: W9 closes §2.6 §3.2's auto-resolution
   path. Remaining DR-029-adjacent surfaces:
   - **Capability 7** (audit-trail surface for settlement
     transitions) — lodged Session 109; trigger conditions still
     not met.
   - **Capability 6** (race-level consolidated EV) — lodged
     Session 109; trigger conditions still not met.
   - **v3-build-proper re-cut work** — deferred behind W9; now
     unblocked.
   - **Fix 4 cadence brief** — deferred from Session 80; assess
     whether W6.5 + W8 + W9 has subsumed it.
   - **`.env.production` same-origin wire-up** — post-DR-029 ops
     follow-up.
   - **Standing-instruction sweep** — multiple candidates
     accumulated; dedicated fresh-mind session whenever operator
     wants.

Code does not produce the next brief. Forward routing is the
next session's work.

## §11 Cross-references

**Source spec:** `dr029/2_6_settlement_race/2_6_settlement_race.md`
(§2.6, 649 lines). Primary anchor — §3.2 (the transitions from
`provisional`), §3.4 (trigger conditions), §3.5 (surfacing
contract), §4.3 (stewards' protest case the auto-resolution
closes).

**Predecessor briefs:**
- `dr029/w4_bet_entry/w6_5_settlement_worker_brief.md` (1316
  lines, W6.5).
- `dr029/w4_bet_entry/w8_burst_review_queue_brief.md` (671
  lines, W8).

**Predecessor reports:**
- `dr029/w4_bet_entry/w6_5_settlement_worker_report.md` (850
  lines, W6.5 ship — Session 105).
- `dr029/w4_bet_entry/w8_burst_review_queue_report.md` (1340
  lines, W8 ship — Session 109).

**Active governing DRs:**
- DR-021 (timestamp anchoring, Adelaide local time) —
  load-bearing for every test fixture and log timestamp.
- DR-027 (two-database architecture) — context for why
  settlement reads happen on the operational line via
  `betfair_client`, not from `capture.db`.
- DR-028 (cross-database integration boundary discipline) —
  context. W9 reads only operational substrate plus the Betfair
  surface; no capture.db touch.
- DR-030 (v3 repo layout / module-boundary discipline) —
  load-bearing for the `last_read_market_state` field's import
  paths (W4 internals importing W3 betfair_client surface; the
  W6.5 ship already exercises this; lint-imports contracts stay
  clean).
- DR-031 (v3 tech stack) — load-bearing for every code surface.
- DR-032 (canonical-reference-layer for all bet records) —
  load-bearing for the worker's read of leg-0
  `betfair_market_id` / `betfair_selection_id`.
- DR-019 (derived state on read) — context. The
  `last_read_market_state` field is **persisted state**, not
  derived — it captures the worker's last read at the time of
  read. The persistence is justified by §2.6 §3.5's "current
  Betfair Win market state as last read" surfacing requirement;
  derivation-on-read is not viable because the worker's read is
  the operational source of truth, not a downstream derivation.

**Source-spec items left out of scope (called out for clarity):**
- §2.6 §3.4 condition 2 (post-settlement market voided
  re-transition from terminal state). Out per §1; ships
  build-proper.
- §2.6 §1.2 / §5.4 soft-book balance reconciliation. Out per
  §1; ships build-proper.
- §2.6 §5.4 settlement worker periodic verification cadence. Out
  per §1; ships build-proper.
- §2.6 §5.4 sports-side dead-heat capture
  (`architecture.md` §B.1.4 amendment). Out per §1;
  administrative cleanup.
- §2.6 §5.4 past-settlement-window threshold calibration. Out
  per §1; v3 operational tuning.

**Carry-forward items this brief logs:**
- W6.5 §5.6 Change C — `entered_provisional_at` dedicated column
  refinement (proxied via `last_reconciled_at` at v1). Not in
  W9 scope; ships build-proper.
- W6.5 §5.5 Change G shared-bookkeeping decision — W9 inherits
  unchanged.
- W8 §7.1 audit-trail surface — capability 7; W9 inherits the
  worker-logger v1 pattern; persisted audit is a separate brief.
- §2.6 §3.4 condition 2 deferral — W9 inherits W6.5's
  deferral; build-proper territory.
- W6 §8.1 finding — `requires-python = ">=3.12"` venv invocation
  foot-gun. W9 follows the existing mitigation (use the venv
  interpreter explicitly).

---

**End of brief.**
