# W12 brief — Read-side derivations + reference data seed (balances, FB inventory, AccountCare warning state, promo journey)

**Status:** locked Session 133.
**Lock anchor:** 2026-05-13 ACST (Adelaide local per DR-021;
exact lock timestamp captured in `sessions/SESSION_133.md` at
close).
**Workstream:** W12 (the first read-side workstream in v3 —
turns the event-log substrate shipped across W4 / W6 / W11 /
W14 / W14.1 / W13 into operator-facing numbers).
**Recipient:** Claude Code, single bounded session.
**Brief location:**
`dr029/w12_balances/w12_balances_brief.md`.
**Triages:** the read-side derivation gap identified across
DR-019 + S124 amendment (derived state on read; the
materialised-view-on-entity-row asymmetry). W13's close-out
identified that ship was substrate-only; this brief commissions
the surfaces operator-Claude work has been pointing at since
the earliest v3 sketches.

---

## §1 — What this brief is and is not

### §1.1 — What this brief is

This brief commissions Code to **ship the six read-side
derivations that turn the v3 event substrate into operator-
facing numbers**, plus two small substrate prerequisite
edits (a slug-flip on the W13-shipped warning surface and
the removal of a now-vestigial `funding_source` field on
the W14-shipped profit-share event), plus the seed
mechanism that populates the W13-shipped reference tables
from the locked content spec at
`dr029/w12_balances/seed_data.md`.

The six derivations:

- **Per-account-at-book balance (Location 1)** — for each
  active `account_at_book`, what is the current cash position
  given the W14 cash-flow event log plus the W4 / W6 / W6.5
  bet record state. This is "how much have I got at Sportsbet
  in Tim's account right now."
- **Per-custodian cash holding (Location 2)** — for each
  bookmaker, the total cash held across all of the operator's
  accounts at that bookmaker. Cross-account aggregation of
  Location 1.
- **Operation-net-flow informational view** — the operator's
  total net inflow vs outflow over a chosen window (deposits
  in, withdrawals out, net per book / per account / overall).
  Informational only; not a balance derivation.
- **Free-bet inventory state** — for each `account_at_book`,
  what free bets are currently held, of what face value, with
  what expiry, and from which originating promo. Derived from
  the `promo_events` flow with supersession-aware reads.
- **AccountCare warning state** — for each `account_at_book`,
  which warnings are currently active and at what severity.
  Derived from `accountcare_warning_raised` minus
  `accountcare_warning_cleared` event pairs.
- **Promo journey state** — for each
  `(promo_template_id, book_id, account_at_book_id)` triple,
  where the operator is in the cycle (observed-but-not-taken
  / taken-leg-active / leg-settled / cycle-complete /
  cycle-aborted). Derived from `promo_observed` plus
  `promo_journey_annotation` events.

Plus three non-derivation pieces:

- **Step zero — slug-flip (§5.1)** — the
  `warning_type_id` slug-flip edit in
  `domain/promos/__init__.py` (UUID → str). 3–5 model
  lines, no schema change (the SQL column is already
  TEXT), test-fixture swap.
- **Step zero — funding_source drop (§5.1b)** —
  removal of the now-vestigial `funding_source` field
  on `ProfitShareDistributionPayload` in
  `domain/cash_flow/__init__.py`, plus adapter and
  repository updates, plus test-fixture sweep. Per
  the S136 profit-share model clarification (holder's
  bank IS the parked pool — see §5.4 / §5.5
  semantics). Underlying schema column may remain
  orphan; Alembic migration out of scope.
- **Seed mechanism (§5.2)** — code that consumes the
  locked seed spec at
  `dr029/w12_balances/seed_data.md` and writes the
  seven `promo_template` rows + five
  `warning_catalogue` entries via the W13-shipped
  `PromoStoreAdapter`.

The work ships as roughly twelve to fourteen new files
plus three edited files (the §5.1 slug-flip edit on
`domain/promos/__init__.py`, the §5.1b
`funding_source` drop across `domain/cash_flow/__init__.py`
+ adapter + repository, and the additive
`store/__init__.py` re-export of the derivation surface)
— exact list landed in §5 below.

### §1.2 — What this brief is not

W12 explicitly does **not**:

- **Build any UI.** Derivations return Pydantic models or
  structured dataclasses. The web surface that renders them
  to the operator is downstream work (W17 / W18 / similar).
- **Build any aggregation across operators.** Single-operator
  scope only — Tim's accounts and books. Multi-operator
  aggregation is out of v3 scope entirely.
- **Touch any shipped schema.** No new columns, no new
  indexes, no new CHECK constraints, no DDL changes. W14 +
  W13 substrate is read-only for W12.
- **Touch `store/repositories/`.** Row-only repositories are
  W14 / W13 territory. W12's derivations live workflow-side
  and call into the existing adapter surface.
- **Build the cascade-trigger logic on W13's payload cascade
  fields.** Those fields ship from W13 and stay dormant until
  W8 burst-review lands. W12 may surface a free bet's
  cascade-source in the inventory state if the payload data
  is present, but does not generate cascade events.
- **Build any AccountCare detection logic.** W12 derives the
  *state* (which warnings are currently active per
  account_at_book) from raise/clear event pairs. *When* a
  warning fires (the threshold-detection logic) is downstream
  AccountCare workstream territory — that work writes the
  raise events; W12 reads them.
- **Build any promo-detection or promo-suggestion logic.**
  W12 derives the *state* of a promo cycle in flight. The
  upstream observation logic (what scrapes the bookmaker's
  promo surface, what creates the `promo_observed` event) is
  W17 (operational layer) / capture-side / future work.
- **Touch `domain/cash_flow/__init__.py`,
  `store/schema/cash_flow.py`, `store/repositories/cash_flow.py`,
  or the cash-flow adapter.** The W14 / W14.1 substrate is
  read-only for W12.
- **Touch `domain/promos/__init__.py` beyond the slug-flip
  step zero.** Reference data models, payload subclasses,
  event types, validators all stay as W13 shipped them.
- **Touch `store/schema/promos.py`,
  `store/repositories/promos.py`, or
  `workflows/promos/v1/promo_store_adapter.py` beyond the
  test-fixture swap for the slug-flip.** W13's substrate is
  read-only for W12 derivations (the seed mechanism uses
  the public adapter surface, doesn't modify it).
- **Touch the bet record substrate.** W4 / W6 row schemas,
  repositories, and adapter (if any) all stay read-only.
- **Amend any DR.** No `decisions.md` edit. The derivations
  implement DR-019 + S124 amendment; the slug-flip is the
  Session 131 call that lands as a brief task, not a DR
  amendment.
- **Build W15 (`ops_events`).** W15 is structurally identical
  to W13 / W14 and is sequenced after W12 per the Session
  131 Path D call.
- **Build W8 (burst review) cascade trigger.** Already named
  above; included here for symmetry.
- **Touch any other v3 module** — no `clients/`, no
  `contracts/`, no `ui/`, no `ops/`, no other workflows /
  their tests, no scripts beyond the seed script if that's
  the chosen seed mechanism, no build config / pyproject.


### §1.3 — Why W12 has the scope it does

Six software calls were made during brief drafting (Session
133); naming them for visibility per `standing_instructions.md`
Cat 5. None of these affect operation, account hygiene, or
strategy directly — they're internal-shape choices made by
Claude.

- **Where derivations live in the module tree.** Two new
  workflow packages — `workflows/balances/v1/` for the
  cash-side derivations (Location 1 balance, Location 2
  custodian holding, operation-net-flow) and an extension of
  the existing `workflows/promos/v1/` package for the
  promo-side derivations (FB inventory, AccountCare warning
  state, promo journey). Alternative considered: a single
  `workflows/derivations/v1/` umbrella package. Rejected
  because the cash-side and promo-side derivations read from
  different adapters and have no shared dependency surface —
  bundling them produces a module that knows about both
  domains for no upside. The split keeps each derivation
  close to its substrate adapter.

- **Derivations are read-only computations, not persisted
  state.** Each derivation function takes a `sqlite3.Connection`
  (W14.1 pattern) or an already-constructed adapter and
  returns a Pydantic model. Nothing gets written; the
  derivation is recomputed on every call. This is DR-019 +
  S124 amendment exactly. Caching is downstream operational
  concern (request-level memoisation in the web surface, not
  at the derivation layer).

- **Derivation outputs are Pydantic v2 models.** Same
  convention as the rest of v3. Closed enums where the value
  set is fixed (e.g. `WarningSeverity` already exists in
  `domain.promos`; W12 imports it rather than redefining).
  Decimal for cash amounts. Adelaide-local timestamps via
  the existing `_ensure_adelaide_local` validator pattern
  (the validator itself stays in `domain.promos` /
  `domain.cash_flow`; W12 models with timestamps re-validate
  on construction).

- **Seed mechanism: Pydantic-via-adapter.** The seed script
  reads `dr029/w12_balances/seed_data.md`, parses the seven
  templates and five warnings into `PromoTemplate` and
  `WarningCatalogueEntry` Pydantic models, and writes them
  via the W13-shipped `PromoStoreAdapter`. Alternative
  considered: raw SQL INSERT statements. Rejected because
  the adapter path gives type safety, validates the seed
  data against the shipped schema as a side effect, and
  matches the operational ledger pattern for any future
  re-seed. Raw SQL would shortcut the validation layer that
  exists to catch exactly the kind of drift seed scripts
  introduce.

- **Operation-net-flow takes an explicit time window.**
  No default. Caller passes a start and end Adelaide-local
  datetime; the derivation aggregates external payment events
  in that window. Alternative considered: default to
  "all-time" or "last 30 days." Rejected because the
  operator's natural framing of "how did I go last month vs
  this month" requires explicit windows, and a hidden
  default invites silent misreads when the window doesn't
  match what the operator expected.

- **Derivations expose pure functions, not classes.** Each
  derivation is a function like
  `compute_account_at_book_balance(conn, account_at_book_id)
  -> AccountAtBookBalance`. Alternative considered: class-
  based derivation services with state. Rejected because
  there is no state to hold — each call is fresh against
  the substrate. Functions read cleaner and test cleaner.

Operator can override any of these at any time before Code
lock.

### §1.4 — Triage context from Session 134

W12 was first commissioned at S133 against a brief that
assumed several substrate shapes that didn't match what
W4 / W6 / W11 / W13 / W14 had actually shipped. Code
halted at §6.1 alignment per the halt rule; the W12
report at `dr029/w12_balances/w12_balances_report.md`
surfaced 15 findings across 7 brief-spec deviations
and 7 load-bearing alignment misses.

S134 triaged the findings and locked the following
decisions. Each is referenced at the relevant build
section; named here in one place so the rationale is
discoverable without re-reading the report.

**Balance algorithm follows architecture.md §A.5 / §A.6
verbatim** (Finding-H). Cash returns from bet
settlements compute on read from the bet row
(`matched_stake × matched_price` against settlement
state), not from cash flow events. No `bet_won` /
`bet_lost` event type exists or will be added; bet
settlement remains a derived-on-read consequence of the
bet row's settlement state per DR-019.

**Read-side derivations may read directly from
`store.repositories.*` SQL paths** where the typed
workflow adapter exposes no matching read method
(Finding-C). Write paths always go through the typed
adapter surface. The asymmetry is intentional: adapters
exist to enforce payload contracts and supersession
discipline on the write side; read derivations under
DR-019 optimise differently and frequently read at the
SQL layer. Each W12 derivation that drops to SQL names
the read path and reason inline. Architecture.md §A.5
carries this as a design principle (added alongside
this brief revision).

**Location 2 is per account-holder, not per
custodian-as-bookmaker** (Finding-M). The W12 output
returns the holder's parked-pool balance, the list of
that holder's per-account-at-book balances (existing
Location 1 derivation filtered to this holder), the
total cash with the holder, and the cumulative
profit-share distributed to the holder. Aggregating
across account-holders at the same book is not the
core Location 2 derivation — those are separate
operational positions sharing only a bookmaker — but
the view is surfaceable as a separate informational
read for occasional spot-checks of single-book
concentration across personas. The informational read
is not part of the W12 scope; flagged as a possible
W12.1 or later refinement.

**FB inventory surfaces an enriched credit-source
label** (Finding-G). The shipped `FreeBetCreditSource`
enum is binary (`TRIGGERED` / `FREEBIE`); W12 keeps
that import unchanged and additionally derives a
`credit_source_label` field on the output model by
walking from the FB credit event's
`triggering_promo_instance_id` to the source promo's
template kind. Operationally rich labels (insurance
trigger, bonus-winnings trigger, goodwill) surface
without mutating the shipped enum or duplicating
linkage onto the FB credit event payload.

**Warning state walks raise-event-id linkages, not
warning-type tallies** (Finding-J + Finding-K).
`AccountCareWarningClearedPayload` references the
specific raise event ID it cancels, not the warning
type. The algorithm walks each raise and checks for a
clear event referencing its event ID. Severity comes
from `severity_at_raise` on every raise (the field is
mandatory; no catalogue-fallback path).

**Promo→bet linkage reads backwards via the promo
event log** (Finding-C Gap 2). The bet record does not
carry a `promo_template_id` field; the linkage exists
on the promo event side
(`FreeBetCreditedPayload.triggering_bet_id`,
`FreeBetDeployedPayload.deploying_bet_id`). The promo
journey derivation reads from this direction. No
substrate change to the bet record.

The remaining findings (B method names, F external-
payment classification, I net-flow window framing, L
FB expiry field rename, N slug-flip target count, O
slug semantics clarification, E `_ensure_adelaide_local`
duplication standing observation) land as Cat 5
mechanical applications in the relevant build sections.

---

## §2 — Why this work exists

W12 is the first read-side workstream in v3. Until W12, the
v3 build has shipped substrate only — schemas, event-log
tables, repositories, adapters. Operationally, nothing yet
turns the substrate into numbers the operator can act on.

The governing DR is **DR-019 + S124 amendment** (derived
state on read; the materialised-view-on-entity-row asymmetry
that applies to bet records but NOT to `promo_events`). The
amendment is load-bearing for W12 — it says that the
`promo_events`-derived surfaces (FB inventory, AccountCare
warning state, promo journey) are pure read-derived from the
event flow, while the bet-record-derived balance derivation
reads from the materialised view on the bet record row.

The substrate W12 reads from:

- **Cash flow events** (W14 / W14.1 — shipped Session 128):
  the `cash_flow_events` table, eight event types covering
  deposits, withdrawals, refunds, adjustments, bonuses, and
  external transfers, plus the `payees` reference table.
  The `CashFlowStoreAdapter` exposes the read surface.
- **Bet records** (W4 / W6 / W6.5 — shipped earlier in v3):
  bet record rows with settlement state. Stake, return, and
  settlement-state shape feed the balance derivation.
- **Promo events** (W13 — shipped Session 130 / triaged
  Session 131): the `promo_events` table with nine event
  types covering FB credit / deploy / revoke / expire, cash
  credit, promo observation, journey annotation, and
  AccountCare warning raise / clear. Plus three reference
  tables (`promo_template`, `promo`, `warning_catalogue`).
  The `PromoStoreAdapter` exposes the read surface.

These three substrates are now stable. W12 turns them into
operator-facing numbers.

The wider design rationale: v3's architectural goals
(`vision.md`) are tighter operational efficiency and a
cleaner basis for analytical capability layered on top. The
operational efficiency goal requires the operator to see
their position at any book at any time — what's the cash
balance, what FBs are available, what warnings are active,
where each promo is in its cycle. W12 delivers all four.

The DR-029 close-out arc is now complete substrate-wise. The
remaining v3 build work (W12 read-side, W15 ops_events, W8
burst review, W17 operational web layer, W18 analytical UI)
all consume the substrate W12 makes legible.

---

## §3 — Pre-reads

### §3.1 — Read/write asymmetry (design principle)

Write paths go through the typed workflow adapter
(`workflows/<domain>/v1/<domain>_store_adapter.py`).
Read paths default to the adapter as well — DR-019
allows derivations to drop directly to the SQL layer
(`store/repositories/<domain>.py`) where the adapter
exposes no matching read method, but each drop is a
named exception, not the path of least resistance.

The asymmetry is intentional. Adapters enforce
payload contracts and supersession discipline on the
write side and replicate that discipline on adapter-
routed reads. A SQL drop bypasses the adapter but
does not bypass the need for the logic. Each W12 read
that drops to SQL must:

1. **Name the path and reason inline.** State which
   table is read and why no adapter method fits.
2. **Replicate any relevant adapter-side business
   logic explicitly.** For event tables this means
   supersession filtering and latest-event-per-scope
   selection. For entity tables (`bets`,
   `accounts_at_book`) this means honouring DR-019
   state-on-row semantics — e.g. reading the bet
   row's settlement-state field as the source of
   truth, not reconstructing it from event history.
   The replicated logic is named in a code comment at
   the drop site.
3. **Surface verification in the ship report.**
   Enumerate every SQL drop, name the replicated
   logic, and demonstrate correctness via unit test
   or worked example.

Recorded as a project-level principle in
architecture.md §A.5: adapter-first is the default
for future workstreams. Where an adapter method is
missing, the first-choice response is to add the
adapter method, not drop to SQL.

### §3.2 — Required reads (read before starting)

In recommended order:

1. **This brief (`dr029/w12_balances/w12_balances_brief.md`)
   end-to-end.** Skim, then read substantively from §5 forward
   for the build itself.

2. **Locked seed content spec
   (`dr029/w12_balances/seed_data.md`).** 391 lines. The
   seven template rows and five warning entries are the seed
   content; the spec also documents the per-template
   `default_terms` JSON shapes and the operational notes that
   anchor the FB inventory and AccountCare warning state
   derivations downstream. The seed script in §5.2 consumes
   this spec content.

3. **W13 ship report
   (`dr029/w13_promos/w13_promos_report.md`).** 578 lines. The
   as-built shape of the promo substrate. Section §3 ("What
   Code did") and §4 ("What landed where") are most
   load-bearing; §10 Q2 covers the slug-flip background that
   makes §5.1 a coherent step zero.

4. **W14.1 adapter brief
   (`dr029/w14_cash_flow/w14_1_adapter_brief.md`).** 1,586
   lines. The v3 workflow-side adapter convention W12's
   `workflows/balances/v1/` and the `workflows/promos/v1/`
   derivation extension both follow. Read §1.1 (what is
   shipped), §1.3 (Cat 5 calls + rationale), §5.1 (adapter
   shape), §5.2 (repository-row interface) — these define
   the convention W12 derivations call against. Reference-
   only beyond those sections.

5. **W13 brief
   (`dr029/w13_promos/w13_promos_brief.md`) — targeted
   sections only.** 3,249 lines; full re-read deferred per
   the pre-execution risk advisory (Cat 3 standing
   instruction). Route on-demand to specific sections if
   needed:
   - §A.4 event-type closed set — the nine `promo_events`
     event types named exactly.
   - §5.2 payload shapes — what fields each event type's
     payload carries (relevant for FB inventory derivation
     payload extraction).
   - §5.4.3 adapter-validated reference pattern — how
     payload references to template / promo / warning_type
     are validated; W12 derivations join on the same shape.
   These references are by section number; Code uses them as
   look-ups, not as full re-reads.

6. **Shipped code, end-to-end:**
   - `domain/cash_flow/__init__.py` (526 lines) — the
     cash-flow domain layer. Read the event payload subclasses
     and `PAYLOAD_BY_EVENT_TYPE` dispatch — the balance
     derivation reads these payloads. Read-only for W12.
   - `domain/promos/__init__.py` (837 lines) — the promo
     domain layer. Read the event payload subclasses,
     `PAYLOAD_BY_EVENT_TYPE` dispatch, and the three
     reference data models. W12's slug-flip step zero edits
     this file at one location (`warning_type_id` type
     annotation); rest is read-only.
   - `workflows/cash_flow/v1/cash_flow_store_adapter.py`
     (396 lines) — the cash-flow read surface. Methods like
     `list_by_account_at_book`,
     `latest_non_superseded_by_scope` are the substrate the
     balance derivation calls. Read-only.
   - `workflows/promos/v1/promo_store_adapter.py` (785
     lines) — the promo read surface. Same methods on the
     promo substrate; W12 extends this package with
     derivation functions but does not modify the existing
     adapter class. Read-only on existing class.
   - `store/repositories/cash_flow.py` (601 lines) and
     `store/repositories/promos.py` (1,012 lines) —
     reference for SQL-level read shape if a derivation needs
     to drop below the adapter for performance (it shouldn't
     for the first ship; flagged here as a fallback only).

7. **Architecture and decisions:**
   - `architecture.md` §A.4 (promo event substrate, event-
     type semantics).
   - `architecture.md` §D12 (Betfair as canonical source —
     relevant background only for W12; no direct dependency).
   - `decisions.md` DR-019 + Session 124 amendment (derived
     state on read; the materialised-view-on-entity-row
     asymmetry).
   - `decisions.md` DR-022 (book / account / account-at-book
     vocabulary — the unit at which Location 1 balance lives).
   - `decisions.md` DR-027 + Session 124 amendment (two-
     database architecture; per-domain event-table internal
     shape).
   - `decisions.md` DR-030 + Session 124 amendment (v3
     repo layout and module-boundary discipline).
   - `decisions.md` DR-032 (canonical-reference-layer / two-
     table bet record — the balance derivation crosses bet
     records).
   - `decisions.md` DR-015 (three-tier AccountCare warning
     severity scheme — calibrates how the warning state
     derivation orders / surfaces warnings).

8. **Standing instructions
   (`standing_instructions.md`).** Read in full per the
   project convention. Category 3 (filesystem / tooling
   discipline) and Category 5 (operator–Claude division of
   labour) are most load-bearing during execution.

### §3.3 — Reference-only (read on demand)

Read only if a specific question surfaces during build:

- `current_state.md` (rebuild folder root) — live working
  state; refer if context on prior session decisions is
  needed.
- `sessions/SESSION_130.md`, `sessions/SESSION_131.md`,
  `sessions/SESSION_132.md` — recent session records covering
  W13 brief drafting, W13 triage, and the seed spec lock.
- `governance.md` — multi-agent review pattern, close-out
  protocol. Relevant only if a finding routes to operator-
  Claude triage requiring governance escalation (unlikely
  for W12).
- `dr029/w14_cash_flow/w14_cash_flow_brief.md` (the
  original W14 brief, pre-W14.1) — reference for the
  cash-flow event payload semantics if a balance derivation
  edge case needs grounding.
- `architecture.md` §D1-§D11 — operational and analytical
  line context; relevant only if a derivation question
  about "what data is W12 actually reading from" surfaces.

---

## §4 — System access

**Mac filesystem (read-write at named anchors only).** All
W12 build work happens on the operator's local Mac at
`/Users/tim/Desktop/Projects/bethub-v3-build/` (or
equivalent v3 working tree — confirm path at session open
via `pwd` or `git status` in the v3 repo root). New files
and edits land at the anchors named in §5. No file edits
outside the named anchors.

**Desktop Commander as the primary filesystem tool.** Per
the project's standing instructions Category 3. The
`bash_tool` is non-functional in this environment;
`projects-filesystem` MCP is an acceptable alternative for
fresh writes and edits. `create_file` is banned (per the
Session 113 / Session 114 strengthened rule). Every write
to a build artefact gets verified via `Desktop Commander:
read_file` or `Desktop Commander:list_directory`
immediately after.

**v3 dev SQLite databases (read-write via in-memory or
tempfile only).** All test runs use ephemeral SQLite
(tempfile-backed via the W13 / W14 pattern). No persistent
v3 dev database touched. No interaction with the live v2
`bethub.db` at
`/Users/tim/Desktop/Projects/bethub-v2/data/bethub.db`
(read-only forbidden too; v2 is fully out of scope for
W12).

**No VPS access required.** W12 is BetHub-side only. The
analytical layer at `capture.db` on the VPS is not touched.
DR-027 + DR-028 cross-database boundary discipline holds —
W12 reads from BetHub's operational store only.

**Adelaide local timestamps per DR-021.** Session open and
close anchors via
`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`. All
timestamps in the report use Adelaide local time
(ACST/ACDT). Adelaide-local validation in derivation
outputs uses the existing `_ensure_adelaide_local`
validator imported from `domain.cash_flow` or
`domain.promos`.

**Git working tree (read-only on dirty regions, additive
for new files).** If the v3 working tree is dirty at
session open, dirty-tree discipline applies (§9.7) — read
state at start, edit only named anchors, no
state-mutating git commands.

---

## §5 — Substantive scope

### §5.1 — Step zero: `warning_type_id` slug-flip

The W13-shipped `domain/promos/__init__.py` types
`warning_type_id` as `UUID` on the `WarningCatalogueEntry`
model and on the `AccountCareWarningRaisedPayload` event
payload. (`AccountCareWarningClearedPayload` does not carry
`warning_type_id` — clear events reference the specific
raise event they cancel via `cleared_warning_event_id`, per
the §5.7 derivation walk.) The Session 131 call locked the
slug-flip: warning identifiers are slugs
(operator-typeable, human-readable strings like
`rapid_promo_turnover`), not UUIDs.

Edit anchors in `domain/promos/__init__.py`:

- **`WarningCatalogueEntry.warning_type_id`** — flip
  `warning_type_id: UUID` to `warning_type_id: str`. Drop
  the `from uuid import UUID` line if no other field still
  uses UUID (check before removing).
- **`AccountCareWarningRaisedPayload.warning_type_id`** —
  same flip, `UUID` → `str`.

The SQL column on `warning_catalogue.warning_type_id` (in
`store/schema/promos.py`) is already TEXT and accepts both
shapes — no schema change required. Existing CHECK
constraints don't reference `warning_type_id` directly.

The W13 `PromoStoreAdapter` formats UUIDs via `str(uuid)` in
the row-conversion helpers; once the type is `str`, that
formatting step becomes a no-op. Check
`workflows/promos/v1/promo_store_adapter.py` for any
`UUID(...)` or `str(...)` conversions on `warning_type_id`
specifically; remove the now-unnecessary conversion (the
field is already a string both sides). This is a small edit
inside the adapter, expected at one or two locations.

**Test-fixture impact.** The W13 test files seed warning
catalogue entries with `uuid.uuid4()` values. Swap to
slug strings — pick slugs from the seed spec (`W1 —
rapid_promo_turnover`, `W2 — large_deposit_burst`, etc.) for
realism; tests don't need to use seed-spec slugs literally
but the slug strings should look like real slugs (snake_case,
descriptive). Files touched:

- `tests/store/repositories/test_promos_schema.py` — fixture
  generator for warning catalogue rows.
- `tests/store/repositories/test_promos_repository.py` — same.
- `tests/workflows/promos/v1/test_promo_store_adapter.py` —
  same.

**Verification:** after the slug-flip edits, `pytest tests/`
must still pass at the W13-close baseline of 753 tests. No
test count change from this edit.

**Lint-imports compliance:** unchanged. No new imports, no
removed imports beyond the conditional `from uuid import
UUID` removal.

**Hard limit on §5.1:** the slug-flip is the only edit to
`domain/promos/__init__.py`. No other type signatures
change, no validator changes, no enum changes. If the
`UUID` import is still required by another field (check
`promo_template_id`, `promo_id`, `bet_id` references), leave
the import in place.

### §5.1b — Step zero (continued): drop `funding_source` from `profit_share_distribution`

**Why.** Session 136 clarified the profit-share model
operationally. The holder's bank account IS the parked
pool — they are literally the same physical money. A
`profit_share_distribution` event records a ledger
reallocation: dollars already sitting in the holder's
bank get marked as the holder's own funds rather than
operational capital. No physical movement happens. Tim's
bank is never touched by a profit-share event.

The W14-shipped substrate carries a `funding_source`
field on the `ProfitShareDistributionPayload` model with
two values: `tim_direct` (profit-share funded directly
from Tim's bank) and `account_holder_cash_holding`
(profit-share funded from the holder's existing parked-
pool). Under the clarified S136 model, only the
`account_holder_cash_holding` variant corresponds to
operational reality; `tim_direct` describes a path that
does not exist. The field is now vestigial.

Cleanup happens as a W12 substrate step before the
read-side build proper, alongside the §5.1 slug-flip.
Same shape of work, same session, no separate W14.x
amendment session required.

**Edit anchors:**

- `domain/cash_flow/__init__.py` —
  `ProfitShareDistributionPayload` model: drop the
  `funding_source: ProfitShareFundingSource` field.
  Drop the `ProfitShareFundingSource` enum class
  entirely if no other model references it (check
  before removing).
- `domain/cash_flow/__init__.py` —
  `ProfitShareFundingSource` enum class: delete if
  unreferenced. If any other code imports the symbol,
  pause and surface as an ALIGNMENT-FINDING; do not
  delete.
- `workflows/cash_flow/v1/cash_flow_store_adapter.py`
  — `create_profit_share_distribution` method (or
  equivalent): drop the `funding_source` parameter
  from the method signature and from the SQL INSERT
  parameters. Check whether the method's docstring
  references the field; update if so.
- `store/repositories/cash_flow.py` — the row-
  conversion helpers and any SQL that reads the
  `funding_source` column: drop column references.
  The underlying schema column may remain in the
  table (it's a TEXT column accepting NULL); leaving
  it as an orphan column is acceptable for this pass.
  Adding an Alembic migration to drop the column is
  out of scope for W12 per §9.4.
- `store/schema/cash_flow.py` — the schema definition
  may carry the column for completeness. Leave the
  schema as-is unless its presence causes a lint or
  test failure; the column is now ignored by all
  read and write paths.

**Test-fixture impact.** Any W14 test that constructs
`ProfitShareDistributionPayload(...)` with a
`funding_source=` kwarg needs the kwarg removed. Test
files likely touched:

- `tests/store/repositories/test_cash_flow_schema.py`
- `tests/store/repositories/test_cash_flow_repository.py`
- `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`

Any test that asserted behaviour conditional on
`funding_source` (e.g. parked-pool subtraction only for
the `account_holder_cash_holding` variant) needs the
condition collapsed — under the new model, every
profit-share is the equivalent of the old
`account_holder_cash_holding` flavour.

**Verification.** After this step, `pytest tests/`
must still pass at the W13-close baseline of 753 tests.
The expected count change: test count may decrease
slightly if a test was specifically parameterised over
the two `funding_source` variants and the redundant
parameterisation collapses. Code reports the new count
in the ship report; any net change beyond ±5 surfaces
as a finding for operator review.

**Lint-imports compliance:** unchanged. No new imports.
One removed import (`ProfitShareFundingSource`) if the
enum gets deleted.

**Hard limit on §5.1b:** the `funding_source` field
removal is the only edit to `domain/cash_flow` for this
step. No other field changes, no validator changes, no
other enum changes. The schema column may remain
orphan in the table (per the "leave as-is" note above);
explicit column-drop via Alembic is out of scope.

**Cross-references updated by this step.** The
following architecture document is amended as part of
the Session 136 W12 commission (separately from the
Code session, by the operator/Chat ahead of Code's
work):

- `architecture.md` §A.5 — operation-net-flow formula,
  bank-touching event table, and profit-share
  semantics paragraph updated to reflect the
  single-flavour model.

Code does not edit `architecture.md`. The architecture
doc revision is already in effect when Code reads it
as part of the §3.2 required reads.

### §5.2 — Seed mechanism for `promo_template` +
`warning_catalogue`

A small seed script at `scripts/seed_promos.py` (new file)
consumes the locked seed content spec at
`dr029/w12_balances/seed_data.md` and writes the seven
promo templates and five warning catalogue entries via the
W13-shipped `PromoStoreAdapter`.

**Script shape:**

- Top-level constants holding the seven template definitions
  and the five warning definitions, parsed once at module-
  load from hard-coded Pydantic-model literals. Why hard-
  coded literals rather than parsing the markdown spec at
  runtime: the spec is content, not a config file; the
  script's load-bearing job is to instantiate validated
  Pydantic models and write them through the adapter, not
  to be a markdown parser. The seed spec is the document of
  record; the script's constants are the operational
  expression of the spec.
- A `main()` function that opens the v3 dev DB (path passed
  via argv, no hard-coded path), constructs
  `PromoStoreAdapter(conn)`, and iterates the constants
  writing each template via
  `adapter.create_template(template)` and each
  warning via `adapter.create_warning_type(entry)`.
- Idempotency: before each write, check if the row already
  exists via `adapter.get_template(template_id)` for
  templates and `adapter.get_warning_type(warning_type_id)`
  for warnings. If yes, skip (don't overwrite). The seed is
  intended as a one-off initial population; re-runs should
  be safe no-ops if the rows are already present.
- Adelaide-local timestamps on any timestamp fields per
  DR-021.
- A short summary printout at end of run: "Seeded X
  templates (Y existed already, Z written); seeded P
  warnings (Q existed already, R written)."

**Template ID convention.** Each template gets a stable
slug-style UUID (e.g. `uuid.uuid5(uuid.NAMESPACE_DNS,
'bethub.promo_template.cash_refund_if_2nd')`) so that
re-runs against a fresh DB regenerate the same UUIDs.
Alternative considered: random `uuid4()` per run. Rejected
because re-runs should produce a consistent ID space —
operator-facing diagnostics and tests both benefit from
stable identity.

**Warning ID convention.** Warning slugs from the seed spec
(`rapid_promo_turnover`, `large_deposit_burst`,
`big_win_pattern`, `multi_account_signal`,
`promo_chasing_pattern`) used verbatim as the
`warning_type_id` values. These are the canonical operator-
facing slugs; the seed script is the moment they enter the
system.

**Cross-references in template / warning fields.** The
seven templates carry `default_terms` as JSON values; the
script writes the JSON exactly as the seed spec defines
them. The five warnings carry `severity` per the seed spec
(`amber` for W1, W2; `red` for W3, W4, W5). Severity values
use the `WarningSeverity` enum imported from
`domain.promos`.

**No `promo` rows seeded by this script.** `promo` rows
represent specific live offerings at a book (e.g. "Sportsbet
Cash refund if 2nd, valid 2026-05-13 to 2026-05-31"); those
are operationally created when the operator observes a
promo in the wild and the operational layer writes a
`promo_observed` event with a fresh `promo_id`. The seed
script only seeds the template catalogue + warning catalogue.

**File anchor:**
- New file: `scripts/seed_promos.py` (~80-120 lines).
- No edits to `domain.promos`, `store.repositories.promos`,
  or the adapter beyond the §5.1 slug-flip.

**Verification:** after running the seed against a fresh
tempfile DB, the adapter's `list_templates()` returns
7 templates and `list_warning_types()` returns
5 entries with the expected slug IDs and severities.

---

### §5.3 — Per-account-at-book balance derivation (Location 1)

**What it computes.** For a given `account_at_book_id`,
returns the current cash position plus the free-bet face-
value total at that book.

**Substrate read.**

- `CashFlowStoreAdapter.list_by_account_at_book(
  account_at_book_id)` — all cash flow events for the
  account-at-book. The shipped event-type taxonomy
  carries no bet-settlement event; this read returns
  deposits, withdrawals, balance adjustments, and the
  account-at-book scoped subset of any external
  payment events. Per architecture.md §A.5, this is
  one of three reads feeding the cash balance.
- **Bet records for the account-at-book** — read
  directly via raw SQL against the `bets` table
  (`SELECT * FROM bets WHERE account_at_book_id = ?`).
  The W6/W6.5 bet storage class exposes no
  `list_by_account_at_book` method; per §3.1 the
  read-side may drop to `store/repositories/bets.py`
  patterns. The bet rows feed the cash stake
  subtraction and the computed cash return per
  architecture.md §A.6.
- `promo_cash_credited` events from
  `PromoStoreAdapter.list_by_account_at_book(
  account_at_book_id,
  event_type=PromoEventType.PROMO_CASH_CREDITED)` —
  the third leg of architecture.md §A.5. Only events
  with payload status `finalised` count.
- FB inventory (the §5.6 derivation, called
  internally) — for the separate `free_bet_balance`
  output field, not the cash balance.

**Algorithm (plain language).**

Per architecture.md §A.5, the per-account-at-book
cash balance is:

  + sum of `account_at_book_deposit` event amounts
  − sum of `account_at_book_withdrawal` event amounts
  ± sum of `account_at_book_balance_adjustment` signed amounts
  − sum of `bets.matched_stake` for rows where
    `is_free_bet = False` and the bet has been placed
    (any settlement state; the stake left the account
    at placement)
  + sum of computed cash return per bet row (see §A.6
    derivation: `matched_stake × matched_price` for won
    bets; zero for lost bets; refunded stake for
    pushed / scratched bets — the substrate's
    settlement-state field drives this)
  + sum of `promo_cash_credited` event amounts where
    payload status is `finalised`

Free-bet stakes (`is_free_bet = True`) do not subtract
from cash — the FB's face value was never cash to
begin with. Free-bet returns to a cash bet still
compute as cash (the FB conversion rate, if any, is
applied per the bet row's `free_bet_conversion_rate`
field).

**Pending-bet stake separation.** For the operator-
facing `pending_bet_stake_total` field on the output,
sum `matched_stake` only for cash bets in the
"placed-and-not-yet-settled" state (substrate's
settlement-state enum is the source of truth for
"placed"; check the live bet row, not the historical
state per DR-019).

Free bet balance = the §5.6 inventory derivation's
total face value across all available FBs.

**Pydantic output model.**

```python
class AccountAtBookBalance(BaseModel):
    account_at_book_id: UUID
    cash_balance: Decimal
    free_bet_balance: Decimal
    pending_bet_stake_total: Decimal
    bet_count_pending: int
    free_bet_count: int
    currency: str  # 'AUD' for current operator scope
    computed_at: datetime  # Adelaide-local per DR-021

    @field_validator('computed_at')
    @classmethod
    def _validate_adelaide_local(cls, v: datetime) -> datetime:
        return _ensure_adelaide_local(v)
```

Cash and FB balances are separated for operational
clarity. The `pending_bet_stake_total` and
`bet_count_pending` fields surface the "committed cash"
deduction transparently — so the operator can see how
much is in flight and how it's split.

**Edge cases.**

- **Account-at-book with no events.** Returns zero
  balance, empty FB inventory. Not an error.
- **Account-at-book closed at the book.** Same shape;
  the closure event (typically a `account_closed`
  cash flow event in the future, or a settlement
  refund) is just another event in the sum. Balance
  may be zero or non-zero depending on what's
  outstanding.
- **Currency drift.** Hard-coded to AUD at this build;
  multi-currency is out of v3 scope per
  `project_context.md` (Australian-market focus). If
  any event carries a non-AUD currency, the derivation
  raises `BalanceCurrencyMismatchError`.
- **Decimal precision.** Cash amounts use 2 decimal
  places (AUD cents). FB face values typically integer
  AUD but use Decimal for consistency. Sums use full
  Decimal precision; round only at display layer
  (which is downstream, not W12).
- **Negative balance.** Surfaces if outflows exceed
  inflows. Not an error — the derivation reports what
  the events say. Operationally this is normally a
  data-flow issue (a deposit event not yet written
  while a withdrawal is) but the derivation does not
  judge.

**Pending-bet stake — supersession-aware.** If a bet's
settlement state is updated via a row update (DR-019 +
S124 amendment: bet records are materialised-view-on-
entity-row), the balance derivation reads the current
row state, not the historical state. Pending stake is
read from the live row's `status == PLACED` (or
equivalent v3 placed-and-not-settled state).

**File anchor:**
- New module: `workflows/balances/v1/balance_derivation.py`
  (~150-220 lines).
- Function: `compute_account_at_book_balance(conn:
  sqlite3.Connection, account_at_book_id: UUID)
  -> AccountAtBookBalance`.

**lint-imports compliance.** The function imports:
- `domain.cash_flow` (event types, adapter Pydantic
  models).
- `domain.promos` (FB-related event types and reference
  data — via the §5.6 inventory derivation it calls).
- `workflows.cash_flow.v1` (the cash flow adapter).
- `workflows.promos.v1` (the promo adapter — but ONLY
  via the §5.6 derivation function, not the adapter
  directly).
- Whatever the v3 bet-record read surface exposes
  (confirm at §6.1).
- stdlib (`sqlite3`, `uuid`, `decimal`, `datetime`).

DR-030: this module sits in `workflows/`. It can import
from `domain` and from other `workflows.*.v1.*` modules
following the cross-workflow rule (DR-030 + S124
amendment locked workflow-to-workflow imports for
derivation chains). Code confirms the cross-workflow
import shape at §6.1 alignment.

---

### §5.4 — Per-account-holder cash holding (Location 2)

**What it computes.** For a given `account_id` (the
account-holder, e.g. Sarie, Tim-self, partner-persona),
returns the total cash sitting with that holder across
the operation: parked-pool balance not yet deployed
to any book, plus per-account-at-book balances at each
book the holder holds an account at, plus the
cumulative profit share distributed to the holder
to date.

Aggregating cash across multiple holders at the same
book is not part of the core W12 Location 2 derivation —
those are separate operational positions sharing only
a bookmaker — but a per-bookmaker cross-account view
is surfaceable as a separate informational read when
the operator wants to spot-check single-book
concentration. Flagged as a possible W12.1 or later
refinement; not in W12 scope.

**Substrate read.**

- `CashFlowStoreAdapter.list_by_account(account_id)`
  — all cash flow events scoped to the
  account-holder. Feeds the parked-pool calculation.
- The §5.3 balance derivation, called once per
  account-at-book the holder holds. For the list of
  account-at-book IDs at the holder, raw SQL against
  the `accounts_at_book` table
  (`SELECT account_at_book_id, book_id FROM
  accounts_at_book WHERE account_id = ?`) per the
  §3.1 read-side asymmetry pattern.

**Algorithm (plain language).**

Parked-pool balance — cash sitting with the
account-holder but not deployed to any book — sums:

  + sum of `account_holder_funding` event amounts
    (inflow from Tim's bank to the holder)
  − sum of `account_holder_remittance` event amounts
    (outflow from the holder back to Tim's bank)
  − sum of `account_at_book_deposit` event amounts
    (outflow from the holder to a book)
  + sum of `account_at_book_withdrawal` event amounts
    (inflow from a book back to the holder)
  − sum of `profit_share_distribution` event amounts
    (the holder's bank IS the parked pool; a
    profit-share is pure ledger reallocation marking
    money already in the holder's bank as the
    holder's own funds rather than operational
    capital; the dollar amount no longer counts as
    cash with the operation)
  ± sum of `account_holder_balance_adjustment` signed
    amounts (model-side corrections)

Per-account-at-book breakdown — for each of the
holder's account-at-book IDs, call
`compute_account_at_book_balance(conn,
account_at_book_id)` from §5.3. The breakdown is the
existing Location 1 derivation filtered to this
holder.

Total cash with holder = parked-pool balance + sum of
breakdown cash balances. This is the headline number.

Cumulative profit share distributed = sum of
`profit_share_distribution` event amounts at the
holder. Not subtracted from the headline total (those
amounts have been reallocated to the holder's own
funds; they're informational at this holder view,
separately from the parked-pool calculation that
already subtracts them).

**Pydantic output model.**

```python
class AccountHolderCashHolding(BaseModel):
    account_holder_id: UUID  # accounts.account_id
    parked_pool: Decimal
    at_book_balances: list[AccountAtBookBalance]
    total_with_holder: Decimal  # parked_pool + sum of breakdown cash
    total_profit_share_distributed: Decimal
    currency: str  # 'AUD'
    computed_at: datetime

    @field_validator('computed_at')
    @classmethod
    def _validate_adelaide_local(cls, v: datetime) -> datetime:
        return _ensure_adelaide_local(v)
```

**Edge cases.**

- **Holder with no events ever.** Returns zero
  parked-pool, empty breakdown, zero total, zero
  profit-share. Not an error.
- **Holder with parked cash but no book accounts.**
  Funding has landed but nothing's been deposited
  out yet. Breakdown is empty; total equals the
  parked-pool balance. Valid intermediate state.
- **Negative parked-pool.** Surfaces if withdrawals
  from books outpace deposits to books plus funding.
  Not an error — the derivation reports what events
  say. Operationally typically a data-flow issue.
- **Multi-currency.** AUD only at current scope per
  DR-022.
- **Profit-share semantics.** The holder's bank
  account IS the parked-pool — they are literally
  the same physical money. A
  `profit_share_distribution` event is pure ledger
  reallocation marking the named dollar amount as
  the holder's own funds rather than operational
  capital; no physical movement happens. The event
  reduces parked-pool (the operation's claim on the
  money) and does not touch Tim's bank (the money
  never passed through Tim's bank — it has been in
  the holder's bank since funding). See §5.5 for
  the operation-net-flow treatment (profit-share
  is not a bank-touching event in this model).

**File anchor:**
- Same module as §5.3:
  `workflows/balances/v1/balance_derivation.py`.
- Function: `compute_account_holder_cash_holding(conn:
  sqlite3.Connection, account_id: UUID)
  -> AccountHolderCashHolding`.

**lint-imports compliance.** Same as §5.3 — domain.cash_flow,
workflows.cash_flow.v1, plus raw SQL access via the shared
sqlite3.Connection per §3.1 read-side asymmetry.

### §5.5 — Operation-net-flow informational view

**What it computes.** For a given Adelaide-local window
(`start_at`, `end_at`), returns the operator's external
cash movement **within the named window** — inflow from
Tim's bank into the operation, outflow from the operation
back to Tim's bank, and outflow from the operation as
profit-share distributions. Window-scoped, not cumulative
since day zero; the caller selects the window (last 30
days, last quarter, year-to-date) at the call site. Plus
per-book and per-account breakdowns; per-book is
expected to be empty or sparse for the external-payment
classification (the relevant events are holder-scoped,
not book-scoped) and is retained for symmetry with other
balance views, with refinement deferred to a possible
W12.1 pass once the reads run operationally.

**Substrate read.**

`CashFlowStoreAdapter.list_by_account_at_book` /
`list_by_account` filtered by external-payment event
types. The classification of external vs internal is
event-type-based, not by an `is_external_payment` field
on the row.

External-payment event types (counted in operation
net-flow):

- `account_holder_funding` — inflow from Tim's bank to
  the operation. (Per the §5.4 model the funded
  dollars land directly in the holder's bank, but
  from Tim's-bank perspective the dollars left
  Tim's bank — so the event is bank-touching.)
- `account_holder_remittance` — outflow from the
  operation to Tim's bank.
- `external_payment` — outflow from Tim's bank to an
  external (non-holder) payee. Per the operator's
  S136 framing this is a COGS-equivalent expense
  category (tax, infrastructure, data subs); kept
  separate from holder-flow in the breakdowns but
  counted in the headline net-flow total.

Internal-only event types (NOT counted in operation
net-flow):

- `account_at_book_deposit`,
  `account_at_book_withdrawal` — intra-operation flow
  between holder parked-pool and book accounts.
- `account_holder_balance_adjustment`,
  `account_at_book_balance_adjustment` — model
  corrections, not flow.
- `profit_share_distribution` — pure ledger
  reallocation per §5.4. The holder's bank IS the
  parked pool; profit-share marks dollars already
  in the holder's bank as the holder's own funds
  rather than operational capital. No physical
  movement, no Tim's-bank touch.

**Algorithm.**

For each cash flow event in the window matching one of
the bank-touching event types:

- `account_holder_funding` events: add the amount to
  `total_inflow`.
- `account_holder_remittance` events: add the amount
  to `total_outflow`.
- `external_payment` events: add the amount to
  `total_outflow`.
- Net = inflow − outflow.

Per-account-holder breakdown: same aggregation grouped
by `account_id` (the holder who funded or received).
External-payment events have no `account_id` scope and
do not appear in the per-holder breakdown; they appear
in their own `external_payments_total` field on the
output model below.

Per-book breakdown: bank-touching events are holder-
scoped or non-scoped, not book-scoped; the per-book
breakdown is expected to be empty in this view (see
opening note).

**Pydantic output model.**

```python
class OperationNetFlow(BaseModel):
    window_start: datetime
    window_end: datetime
    total_inflow: Decimal
    total_outflow: Decimal
    external_payments_total: Decimal  # subset of
        # total_outflow attributable to
        # `external_payment` events specifically;
        # surfaced separately for COGS-equivalent
        # categorisation per S136 operator framing
    net: Decimal
    by_book: list[BookNetFlow]
    by_account: list[AccountNetFlow]
    currency: str  # 'AUD'
    computed_at: datetime

class BookNetFlow(BaseModel):
    book_id: UUID
    inflow: Decimal
    outflow: Decimal
    net: Decimal

class AccountNetFlow(BaseModel):
    account_id: UUID
    inflow: Decimal
    outflow: Decimal
    net: Decimal
```

**Edge cases.**

- **Empty window.** Returns all zeros. Not an error.
- **Window crossing daylight-saving transition.** The
  window bounds use Adelaide local time; events use
  Adelaide local time; the comparison is timezone-aware
  via the `_ensure_adelaide_local` validator. DST
  transitions are handled by the underlying datetime
  library.
- **Inverse-direction window (`end_at` before
  `start_at`).** Raises `InvalidWindowError`. The
  derivation does not silently swap.
- **Open-ended window.** Not supported. Both bounds
  required. (The operator's framing of "last month"
  or "this quarter" maps to explicit
  start/end at the call site.)

**File anchor:**
- Same module:
  `workflows/balances/v1/balance_derivation.py`.
- Function: `compute_operation_net_flow(conn:
  sqlite3.Connection, window_start: datetime,
  window_end: datetime) -> OperationNetFlow`.

---

### §5.6 — Free-bet inventory state

**What it computes.** For a given `account_at_book_id`,
returns the list of free bets currently available at
that account — those credited and not yet deployed, not
revoked, not expired. Each FB carries its face value,
expiry, originating promo template, and credit source.

**Substrate read.**

- `PromoStoreAdapter.list_by_account_at_book(
  account_at_book_id, event_type=PromoEventType
  .FREE_BET_CREDITED)` — all FB credit events for the
  account-at-book.
- For each credit, query the supersession chain to
  determine current state: `walk_supersession_chain(
  credit_event_id)` returns the chain of subsequent
  events that supersede this credit.

**Algorithm (supersession-aware).**

For each `free_bet_credited` event at the account-at-book:

1. Walk its supersession chain forward. The latest
   event in the chain is the FB's current state:
   - **No subsequent events:** FB is fresh-credited
     and untouched. **Available.**
   - **Latest is another `free_bet_credited`:** the
     original was superseded by a fresh credit (used
     for partial-draw or correction patterns). The
     latest credit is the current FB; check ITS
     supersession chain forward (the algorithm
     recurses naturally through the chain walk).
   - **Latest is `free_bet_deployed`:** FB was used
     in a bet. **Not available.**
   - **Latest is `free_bet_revoked`:** FB was
     withdrawn by the book. **Not available.**
   - **Latest is `free_bet_expired`:** FB hit its
     expiry. **Not available.**

2. For each FB whose latest state is "available," read
   the credit event's payload to extract:
   - Face value (the `amount` payload field).
   - Expiry timestamp (the `face_value_expiry` payload
     field — name matches the W13 shipped payload, not
     the brief's earlier `expires_at`).
   - Triggering promo instance ID (the
     `triggering_promo_instance_id` payload field if
     present — null for goodwill FBs).
   - Credit source (the `credit_source` payload field
     — the W13 shipped binary enum: `TRIGGERED` or
     `FREEBIE`).

   For each FB with a non-null
   `triggering_promo_instance_id`, walk to the source
   promo via
   `PromoStoreAdapter.get_promo(triggering_promo_instance_id)`,
   then walk to the promo's template via
   `PromoStoreAdapter.get_template(promo.template_id)`,
   then read `template.kind` to derive the rich
   `credit_source_label`:
   - `INSURANCE` → `"insurance trigger"`
   - `BONUS_WINNINGS` → `"bonus-winnings trigger"`
   - `PRICE_BOOST` → `"price-boost trigger"`
   - `EW_CASHBACK` → `"each-way cashback trigger"`
   - `OTHER` → `"other trigger"`

   For FBs with a null
   `triggering_promo_instance_id` (i.e. `credit_source
   = FREEBIE`), `credit_source_label = "goodwill"`.

3. Sort by expiry ascending (earliest expiry first) so
   the operator sees the about-to-expire FBs at the top
   of the list.

**Filter for expiry at read time.** If a credit's
payload has an `expires_at` in the past at the
`computed_at` time of the derivation, the FB is treated
as expired even if no `free_bet_expired` event has been
written yet. (The expiry event is normally written by
a background job; the read-time filter ensures the
state is correct even with operational lag.)

**Pydantic output model.**

```python
class AvailableFreeBet(BaseModel):
    credit_event_id: UUID
    face_value: Decimal
    currency: str  # 'AUD'
    credited_at: datetime
    face_value_expiry: datetime | None
    source_promo_instance_id: UUID | None
    source_template_id: UUID | None
    credit_source: FreeBetCreditSource  # W13 binary enum
    credit_source_label: str  # derived per algorithm step 2

class FreeBetInventory(BaseModel):
    account_at_book_id: UUID
    free_bets: list[AvailableFreeBet]
    total_face_value: Decimal
    fb_count: int
    computed_at: datetime
```

**Edge cases.**

- **No FB credits ever for this account_at_book.**
  Returns empty inventory. Not an error.
- **Partially-drawn FB via supersession.** Captured by
  the chain walk — the latest non-superseded credit's
  remaining face value is what shows. If the credit
  rewriting wasn't done (legacy data), the FB shows
  with its original face value (per the credit event).
- **FB credited then immediately revoked by book.**
  Chain shows credit → revoke; latest is revoke; FB
  filtered out. Not available.
- **Expiry timestamp in past but no expiry event yet.**
  FB filtered out per the read-time expiry check. The
  background-job lag does not show stale "available"
  FBs.
- **Credit event with malformed payload.** Pydantic
  validation at adapter-read time will already have
  raised; this derivation does not need to defensively
  parse. If a malformed payload somehow reaches the
  derivation, raise `InventoryParseError`.

**File anchor:**
- New function in the existing
  `workflows/promos/v1/` package, in a new module to
  keep the adapter file untouched:
  `workflows/promos/v1/promo_derivations.py`
  (~140-200 lines).
- Function: `compute_free_bet_inventory(conn:
  sqlite3.Connection, account_at_book_id: UUID)
  -> FreeBetInventory`.

**lint-imports compliance.** The function imports:
- `domain.promos` (event types, enums, reference data
  models).
- `workflows.promos.v1.promo_store_adapter` (the
  shipped adapter — read-only).
- stdlib.

No `domain.cash_flow` import — FB inventory is purely
promo-substrate work. The §5.3 balance derivation calls
this function and combines its `total_face_value` into
the `free_bet_balance` field; the cross-domain
combination happens in `workflows.balances`, not in
`workflows.promos`.

---

### §5.7 — AccountCare warning state

**What it computes.** For a given `account_at_book_id`,
returns the list of currently-active warnings (raised
but not yet cleared), each with its label and severity.
Active warnings sorted by descending severity (red →
amber → yellow), then by most-recent within severity.

**Substrate read.**

- `PromoStoreAdapter.list_by_account_at_book(
  account_at_book_id, event_type=PromoEventType
  .ACCOUNTCARE_WARNING_RAISED)` — all raise events.
- `PromoStoreAdapter.list_by_account_at_book(
  account_at_book_id, event_type=PromoEventType
  .ACCOUNTCARE_WARNING_CLEARED)` — all clear events.
- `PromoStoreAdapter.list_warning_types()`
  — the warning catalogue (for label + baseline
  severity).

**Algorithm.**

For each `accountcare_warning_raised` event at the
account_at_book (ordered by event timestamp ascending):

1. Check whether any subsequent
   `accountcare_warning_cleared` event has
   `cleared_warning_event_id == this raise event's
   event_id`.
2. If yes — this raise has been cleared. Skip.
3. If no — this raise is active.

Group active raises by `warning_type_id` (the field on
the raise payload). If a single warning type has
multiple unmatched raises (raised twice before any
clear), the most-recent active raise per warning_type
is the "current" raise for that type.

For each current active raise, build an
`ActiveWarning` model:

- `warning_type_id` (the slug; from the raise event's
  payload, which is the only payload carrying the
  field — clear events reference the raise event ID,
  not the warning type).
- `label` (from the catalogue lookup at
  `PromoStoreAdapter.get_warning_type(warning_type_id)`).
- `severity`: the `severity_at_raise` field on the
  raise event. The field is mandatory on the shipped
  W13 payload (not nullable); every raise carries an
  explicit severity. The catalogue's baseline
  `severity` is informational only at the warning-
  type-display layer and is not consulted by the
  active-warning derivation.
- `raised_at`: the timestamp of the raise.
- `raise_event_id`: the raise event's ID.

Sort: severity descending (`red` first, then `amber`,
then `yellow` per DR-015), then `raised_at`
descending within severity.

**Cleared-warnings handling.** Cleared warnings are NOT
in the active state output. A future "warning history"
derivation would surface them; the current state
surface is active-only by design.

**Multiple raises before clear.** If a warning type is
raised twice before either raise is cleared, both
raises are active until matched by their own clear
event. The clear events reference specific raise
event IDs (not the warning type), so one clear
cancels exactly one raise. The "current" active
raise displayed per warning type is the most recent
of the unmatched raises.

**Pydantic output model.**

```python
class ActiveWarning(BaseModel):
    warning_type_id: str  # slug per S131 + §5.1 flip
    label: str  # from catalogue
    severity: WarningSeverity  # red / amber / yellow
    raised_at: datetime
    raise_event_id: UUID

class AccountCareWarningState(BaseModel):
    account_at_book_id: UUID
    active_warnings: list[ActiveWarning]
    red_count: int
    amber_count: int
    yellow_count: int
    computed_at: datetime
```

The per-severity counts surface alongside the list so
the operator can see "I have 2 reds at this book" at a
glance without iterating the list.

**Edge cases.**

- **No raise events ever.** Returns empty active
  warnings, all counts zero. Not an error.
- **Warning_type referenced in raise event but not in
  catalogue.** Adapter-side validation at W13 write
  time should have caught this; if it reaches the
  derivation, the warning is included with `label =
  "(unknown warning type)"` and the original severity
  from the raise event. No error raised — this is a
  data-quality flag visible at read time rather than
  an exception.
- **Severity always from raise event.** The raise
  event's `severity_at_raise` is the operationally-
  binding severity. Catalogue severity exists for
  display-time defaulting at the warning-type label
  layer (out of W12 scope), not for active-warning
  derivation.
- **Raised and cleared in same instant (same
  timestamp).** Both count toward their tallies; if
  counts equal, warning is not active. Order between
  same-timestamp events follows event ID ordering
  (UUIDs are sortable).

**File anchor:**
- Same module as §5.6:
  `workflows/promos/v1/promo_derivations.py`.
- Function: `compute_accountcare_warning_state(conn:
  sqlite3.Connection, account_at_book_id: UUID)
  -> AccountCareWarningState`.

### §5.8 — Promo journey state

**What it computes.** For a given
`(promo_template_id, book_id, account_at_book_id)`
triple, returns the current state of the operator's
journey through that promo offering at that account-
at-book. The journey state describes where the
operator is in the promo cycle.

**Journey states (closed enum).**

- `OBSERVED_NOT_TAKEN` — the promo was observed (a
  `promo_observed` event landed) but no bet has been
  placed against it yet.
- `TAKEN_LEG_ACTIVE` — a bet has been placed against
  the promo (linked by `promo_id` on the bet record or
  by an explicit `promo_journey_annotation` event
  with `taken` tag) and is pending settlement.
- `LEG_SETTLED_AWAITING_DOWNSTREAM` — the bet has
  settled but downstream events are still expected
  (e.g. an insurance promo: bet settled in a
  non-winning placing, FB credit expected but not yet
  written; or FB credited, FB deployed, FB-bet
  pending).
- `CYCLE_COMPLETE` — all expected downstream outcomes
  have resolved. For a cash-refund insurance promo:
  bet settled and any cash refund credited. For an
  FB insurance promo: original bet settled, any
  triggered FB credited, deployed, and its bet
  settled. For a price-boost: bet settled (no
  downstream events). For a bonus-winnings-FB: bet
  settled, any triggered FB credited, deployed, and
  its bet settled. For a goodwill FB: FB deployed and
  its bet settled.
- `CYCLE_ABORTED` — operator-driven via an explicit
  `promo_journey_annotation` event with `aborted`
  tag. Cycle treated as ended early; no further
  downstream events expected.

**Substrate read.**

- `PromoStoreAdapter.list_by_account_at_book(
  account_at_book_id, event_type=PromoEventType
  .PROMO_OBSERVED)` — all observed events at the
  account-at-book; filter to those whose payload
  carries the queried `promo_template_id` and the
  observation scope matches the queried `book_id`.
- `PromoStoreAdapter.list_by_account_at_book(
  account_at_book_id, event_type=PromoEventType
  .PROMO_JOURNEY_ANNOTATION)` — annotation events at
  the account-at-book; filter to those for the
  queried promo_template_id.
- Bet records linked to the promo — read by walking
  the promo event log backwards. Specifically, the
  `FreeBetCreditedPayload.triggering_bet_id` field
  (on FB credit events at the account_at_book) and
  the `FreeBetDeployedPayload.deploying_bet_id` field
  (on FB deploy events at the account_at_book) carry
  bet IDs. To find bets linked to a given promo
  template, filter promo events for the
  `account_at_book_id` and read the bet IDs from
  matching credit / deploy event payloads. The bet
  record itself does not carry a forward
  `promo_template_id` field; the linkage exists only
  in the reverse direction on the promo event side.
- Bet records read by ID — once the bet IDs are
  collected from promo events, fetch each bet row
  directly via the bet storage class's
  `read_bet_record(bet_id)` method (this surface
  exists; only `list_by_account_at_book` is missing
  per Finding-C Gap 1).
- The downstream FB events (credited / deployed /
  expired / revoked) and their derived bet records,
  via the `parent_event_id` chain back to the original
  bet.
- The W14 cash flow events for cash refunds linked to
  the promo (via correlation_id or parent_event_id).

**Algorithm (state machine, evaluated at read time).**

The journey progresses through states based on the
event flow. Read all events for the triple, build the
state by checking:

1. Most recent `promo_journey_annotation` with
   `aborted` → state is `CYCLE_ABORTED`. Stop.
2. No bet placed against the promo — walk the promo
   event log for the account_at_book. If no
   `free_bet_credited` event references a bet_id via
   `triggering_bet_id` and no
   `promo_journey_annotation` event with `taken` tag
   exists for the promo_template_id, state is
   `OBSERVED_NOT_TAKEN`. Stop.
3. Bet placed but not settled → state is
   `TAKEN_LEG_ACTIVE`. Stop.
4. Bet settled. Inspect the template's mechanic
   (looked up from the template catalogue):
   - **`PRICE_BOOST` / `BONUS_WINNINGS` cash-only:**
     no downstream events expected. State is
     `CYCLE_COMPLETE`. Stop.
   - **`INSURANCE` (cash refund):** if bet settled in
     a place position that should trigger the refund,
     check for a cash refund event linked to this bet;
     if present, `CYCLE_COMPLETE`; if not yet, state
     is `LEG_SETTLED_AWAITING_DOWNSTREAM`. If bet
     settled outside refund-eligible positions,
     `CYCLE_COMPLETE`.
   - **`INSURANCE` (FB refund) / `BONUS_WINNINGS`
     FB / `OTHER` (goodwill):** check whether the
     downstream FB has been credited, deployed, and
     its derived bet settled. Each step that's still
     pending keeps the state at
     `LEG_SETTLED_AWAITING_DOWNSTREAM`. Once the FB
     leg is fully resolved (settled or expired),
     `CYCLE_COMPLETE`.

**Pydantic output model.**

```python
class PromoJourneyState(BaseModel):
    promo_template_id: UUID
    book_id: UUID
    account_at_book_id: UUID
    state: JourneyState  # the closed enum above
    observed_at: datetime | None
    taken_at: datetime | None
    leg_settled_at: datetime | None
    cycle_resolved_at: datetime | None
    abort_reason: str | None
    triggering_bet_id: UUID | None
    downstream_event_ids: list[UUID]
    computed_at: datetime
```

The timestamp fields are populated as the journey
progresses; they're null until the relevant event has
fired. `downstream_event_ids` lists every event in
the cycle (observed, annotation, credit, deploy,
settlement, refund) for traceability.

**Edge cases.**

- **Multiple observations of same triple before
  taking.** Reflects the operator seeing the promo
  multiple times. The journey state shows the
  earliest observation as `observed_at`; subsequent
  observations are in `downstream_event_ids`.
- **Observation but no bet record link.** State is
  `OBSERVED_NOT_TAKEN` indefinitely — the operator
  saw the promo but never placed against it. After
  the promo's natural expiry (typically a few days),
  this becomes operationally stale; W12 does not
  auto-expire to `CYCLE_ABORTED` (that's annotation-
  driven only). A future "journey grooming" workstream
  may revisit.
- **Bet placed against the promo but the link is
  ambiguous** (e.g. bet record's `promo_id` is null
  but a journey annotation says "taken"). Annotation
  wins — explicit operator-driven event overrides
  inference. State is `TAKEN_LEG_ACTIVE` or further.
- **Downstream FB credited but never deployed
  (operator chose not to use it; it expired).** Once
  the FB expires (via `free_bet_expired` event or
  read-time expiry filter), the cycle resolves to
  `CYCLE_COMPLETE`. Operationally the operator may
  prefer to label this `CYCLE_ABORTED` — that's an
  operator-driven annotation at the time, not an
  automatic state inference.

**File anchor:**
- Same module:
  `workflows/promos/v1/promo_derivations.py`.
- Function: `compute_promo_journey_state(conn:
  sqlite3.Connection, promo_template_id: UUID,
  book_id: UUID, account_at_book_id: UUID)
  -> PromoJourneyState`.

---

### §5.9 — Module structure and lint-imports compliance

**New modules and files.**

```
workflows/balances/
├── __init__.py                              # empty marker
└── v1/
    ├── __init__.py                          # empty marker
    └── balance_derivation.py                # §5.3, §5.4, §5.5

workflows/promos/
└── v1/
    └── promo_derivations.py                 # §5.6, §5.7, §5.8
                                             # (NEW — separate from
                                             # promo_store_adapter.py)

scripts/
└── seed_promos.py                           # §5.2

tests/workflows/balances/
├── __init__.py                              # empty marker
└── v1/
    ├── __init__.py                          # empty marker
    └── test_balance_derivation.py           # tests for §5.3-§5.5

tests/workflows/promos/v1/
└── test_promo_derivations.py                # tests for §5.6-§5.8
                                             # (NEW — separate from
                                             # test_promo_store_adapter.py)

tests/scripts/
├── __init__.py                              # empty marker
└── test_seed_promos.py                      # tests for §5.2
```

Plus edited files:

- `domain/promos/__init__.py` — §5.1 slug-flip (3 type
  annotations).
- `workflows/promos/v1/promo_store_adapter.py` — §5.1
  fallout cleanup of `UUID(...)`/`str(...)`
  conversions on `warning_type_id` (1-2 locations).
- `domain/cash_flow/__init__.py` — §5.1b
  `funding_source` field removal from
  `ProfitShareDistributionPayload`; conditional
  removal of `ProfitShareFundingSource` enum class.
- `workflows/cash_flow/v1/cash_flow_store_adapter.py`
  — §5.1b adapter method signature + SQL parameter
  cleanup for `funding_source`.
- `store/repositories/cash_flow.py` — §5.1b row-
  conversion helper cleanup.
- `store/__init__.py` — additive re-exports of the
  derivation output models (`AccountAtBookBalance`,
  `BookCashHolding`, `OperationNetFlow`,
  `FreeBetInventory`, `AccountCareWarningState`,
  `PromoJourneyState`) if these surface gets adopted as
  the public re-export convention. Check W14.1 + W13
  precedent at §6.1 for whether output models are
  re-exported. **Default if precedent is ambiguous:
  re-export the six output models for consistency with
  the repository / adapter re-export pattern.**

**lint-imports contracts that must hold post-W12.**

All five existing DR-030 contracts continue to pass:

1. **DR-030 layered architecture** — KEPT.
   `workflows.*.v1.*` may import from `domain.*` and
   from `store.*` (the existing W14.1 pattern). W12's
   derivation modules follow this.
2. **`domain` imports nothing in the project** — KEPT.
   §5.1 slug-flip changes types within `domain.promos`
   but adds no new project-internal imports (may even
   remove `from uuid import UUID` if unused after the
   flip). §5.1b removes a field and possibly an enum
   class from `domain.cash_flow`; same shape — no new
   imports introduced, one possibly removed.
3. **`store` imports nothing in the project** — KEPT.
   The §5.1b edit to `store/repositories/cash_flow.py`
   is local row-conversion cleanup (removing column
   references that no longer exist on the domain
   model); no new project-internal imports added.
   The additive `store/__init__.py` re-export of
   output models is `from workflows...` and therefore
   not a `store`-side project import; the re-exports
   happen at the package `__init__.py` level which is
   permitted by W14.1 precedent).
4. **`contracts` is a leaf package** — KEPT. W12 does
   not touch `contracts.*`.
5. **`workflows` cannot import `workflows`** — **this
   contract needs verification at §6.1.** W12's §5.3
   balance derivation needs to call the §5.6 FB
   inventory derivation, which is a cross-workflow
   import (`workflows.balances` imports from
   `workflows.promos.v1.promo_derivations`). The S124
   amendment to DR-030 locked cross-workflow imports for
   derivation chains explicitly — confirm the exact
   `lint-imports` contract shape at §6.1; if the
   contract is currently "workflows cannot import
   workflows," it needs amendment to allow the
   derivation-chain pattern. If amendment is needed,
   surface as ALIGNMENT-FINDING and halt; do not amend
   the contract unilaterally. If the contract already
   accommodates the S124 amendment, proceed.

**Confirm at §6.1 alignment check.** Read
`pyproject.toml` (or wherever the `lint-imports`
contracts live) and verify the cross-workflow rule
shape before drafting any code that crosses workflow
boundaries.

### §5.10 — Tests

**Test file layout — three new test files plus marker
package files** per the W14.1 / W13 convention.

**`tests/workflows/balances/v1/test_balance_derivation.py`** — covers §5.3, §5.4, §5.5.

Test groups:

- **§5.3 balance derivation** — 14-18 tests:
  - Empty account: zero balance, empty FB inventory.
  - Deposit only: balance reflects deposit.
  - Deposit + withdrawal: balance reflects net.
  - Deposit + placed bet: balance reflects deposit
    minus pending stake; `pending_bet_stake_total`
    matches.
  - Deposit + placed bet + bet settled win: balance
    reflects deposit minus stake plus return (the
    return arrives via cash flow event).
  - Deposit + placed bet + bet settled loss: balance
    reflects deposit minus stake; no return credited.
  - FB credit only: cash balance unchanged;
    `free_bet_balance` reflects the FB face value.
  - FB credit + deploy: FB drops out; cash balance
    unchanged (deploy doesn't move cash).
  - FB credit + deploy + FB-bet win: cash balance
    increases by the FB-bet return.
  - Multiple FBs credited: `free_bet_balance` is the
    sum.
  - Currency mismatch raises `BalanceCurrencyMismatch
    Error`.
  - Adelaide-local timestamp on `computed_at` validates.
  - Decimal precision preserved (no float drift).
  - Supersession-aware pending-bet reads (bet placed
    then bet record updated to a non-PLACED state →
    pending stake adjusts).
- **§5.4 cash holding** — 4-6 tests:
  - Empty book: zero total, empty breakdown.
  - Single account at book: total matches breakdown's
    single entry.
  - Multiple accounts at book: total sums breakdown.
  - Breakdown order: by account_at_book_id ascending
    (deterministic).
- **§5.5 net-flow** — 6-9 tests:
  - Empty window: zero inflow, zero outflow, zero net.
  - Deposits only: inflow positive, outflow zero, net
    positive.
  - Withdrawals only: outflow positive, inflow zero,
    net negative.
  - Mixed: inflow and outflow both positive, net is
    inflow minus outflow.
  - Per-book breakdown matches grouping.
  - Per-account breakdown matches grouping.
  - Inverse window raises `InvalidWindowError`.
  - Window crossing DST boundary: events on correct
    side of boundary counted correctly.
  - Internal-only events (refunds, adjustments,
    bonuses) excluded from external-flow.

**`tests/workflows/promos/v1/test_promo_derivations.py`** — covers §5.6, §5.7, §5.8.

Test groups:

- **§5.6 FB inventory** — 8-12 tests:
  - Empty account: empty inventory.
  - FB credit only: 1 FB available.
  - Credit + deploy: empty.
  - Credit + revoke: empty.
  - Credit + expire event: empty.
  - Credit with expiry in past + no expire event:
    empty (read-time expiry filter).
  - Credit + supersession by partial-draw credit: latest
    credit shows with remaining face value.
  - Multiple FBs: ordered by expiry ascending.
  - Goodwill FB (no promo_template_id): inventory entry
    has null `source_promo_template_id`.
- **§5.7 warning state** — 8-12 tests:
  - Empty account: no active warnings.
  - Raise only: warning active, severity from catalogue.
  - Raise + clear: warning not active.
  - Raise + raise + clear: warning active (count 2 > 1).
  - Severity override via `severity_at_raise` on raise
    event.
  - Catalogue severity change after raise: derivation
    uses catalogue current severity when
    `severity_at_raise` is null.
  - Multiple warning types: ordered red → amber →
    yellow.
  - Within same severity: most-recent first.
  - Per-severity counts match active list.
- **§5.8 promo journey** — 10-15 tests:
  - Observed only: state OBSERVED_NOT_TAKEN.
  - Observed + bet pending: TAKEN_LEG_ACTIVE.
  - Observed + bet settled win (price boost template):
    CYCLE_COMPLETE.
  - Observed + bet settled, insurance cash refund
    triggered: LEG_SETTLED_AWAITING_DOWNSTREAM until
    refund credits, then CYCLE_COMPLETE.
  - Observed + bet settled, FB insurance triggered: full
    cycle through credit → deploy → FB-bet settle =
    CYCLE_COMPLETE.
  - Each intermediate stage reports the correct state.
  - Operator annotation with `aborted`: CYCLE_ABORTED
    regardless of other events.
  - Multiple observations: earliest `observed_at`, all
    in `downstream_event_ids`.
  - Goodwill FB journey (no upstream observation, just
    credit + deploy + settle): CYCLE_COMPLETE on bet
    settle.
  - Bonus-winnings-FB: full cycle through original bet
    win + FB credit + FB deploy + FB-bet settle =
    CYCLE_COMPLETE.

**`tests/scripts/test_seed_promos.py`** — covers §5.2.

Test groups (4-6 tests):

- Fresh DB, full seed: 7 templates and 5 warnings
  exist after run.
- Re-run on already-seeded DB: idempotent, no
  duplicates, summary reports correctly.
- Adelaide-local timestamps on all seeded rows.
- Severity values match seed spec (W1/W2 amber;
  W3/W4/W5 red).
- Default-terms JSON parses cleanly and matches seed
  spec.
- Goodwill template's `default_terms.common_sources`
  list survives round-trip.

**Total net new tests:** 50-78 across the three test
files. The total is wide because each derivation has
several edge cases — Code calibrates the final count
based on what's covered cleanly per parametrisation
versus what needs distinct tests.

**Total test suite baseline post-W13:** 753 tests.
**Post-W12 expected total:** 803-831 tests.

**Test isolation.** Per W14.1 / W13 convention, every
test seeds its own substrate (W11 account / book /
account_at_book; relevant cash flow and promo events;
relevant bet records via the v3 bet substrate). No
shared `conftest.py` fixtures — per-file fixtures only.

---

## §6 — Sequencing within session

### §6.1 — Pre-build codebase alignment check

Before any edits, Code runs the following empirical
checks against the shipped W14.1 / W13 / W11 / W4-W6
substrate. Surface any divergence as an
`ALIGNMENT-FINDING` (A, B, C, ...) and halt before
substantive edits. The brief is anchored on what's
shipped; if shipped reality has drifted, the brief's
spec needs adjustment before code lands.

The seven specified checks (each names a specific file
or shape Code reads and what's confirmed by reading it):

**ALIGNMENT-CHECK-A — W14.1 adapter shape.** Read
`workflows/cash_flow/v1/cash_flow_store_adapter.py`
end-to-end. Confirm:
- Class `CashFlowStoreAdapter` exists with
  `__init__(self, conn: sqlite3.Connection)`.
- Public read methods include
  `list_by_account_at_book`, `list_by_account`,
  `list_by_book`, `list_by_event_type`,
  `list_by_correlation_id`,
  `latest_non_superseded_by_scope`,
  `walk_supersession_chain`.
- Public payee surface includes `list_payees`,
  `get_payee`, `update_payee`, `create_payee`.

**ALIGNMENT-CHECK-B — W13 promo adapter shape.** Read
`workflows/promos/v1/promo_store_adapter.py` end-to-
end. Confirm:
- Class `PromoStoreAdapter` exists with
  `__init__(self, conn: sqlite3.Connection)`.
- Public read methods include
  `list_by_account_at_book`, `list_by_account`,
  `list_by_book`,
  `latest_non_superseded_by_scope`,
  `walk_supersession_chain`.
- Reference-data read methods include
  `list_templates`, `list_promos`,
  `list_warning_types`,
  `get_template`, `get_promo`,
  `get_warning_type`.

**ALIGNMENT-CHECK-C — bet record read surface.** Look
for the v3 bet-record read surface — the workflow-side
adapter (if one exists) or the repository directly.
Likely paths:
- `workflows/bets/v1/bet_store_adapter.py` if exists.
- `store/repositories/bets.py` directly.
- `domain/bets/__init__.py` for the bet record model.

Confirm:
- A method exists for listing bets by
  `account_at_book_id` (whatever its exact name).
- Each bet record carries a `status` field with a
  closed set including "placed-and-not-yet-settled"
  (whatever its exact enum value).
- A field exists carrying the bet's stake amount as
  Decimal.
- A field exists or path exists linking a bet to its
  triggering promo (the `promo_id` linkage W13's
  cascade payload references; if no such field on the
  bet record, surface as ALIGNMENT-FINDING-C and
  describe the join shape Code thinks fits).

If the bet-record substrate doesn't exist yet (the
W4/W6 workstreams haven't shipped), surface as a
HARD STOP — W12 cannot ship without the bet
substrate. Verify by checking the workstream status
in `v3_build_picture.md`.

**ALIGNMENT-CHECK-D — `lint-imports` cross-workflow
contract.** Read `pyproject.toml` (or wherever
`lint-imports` contracts are declared). Find the
contract that governs workflow-to-workflow imports.

The §5.3 balance derivation imports from
`workflows.promos.v1.promo_derivations` (the §5.6
FB inventory function). Confirm the contract permits
this. The DR-030 + S124 amendment locked cross-
workflow imports for derivation chains; the contract
should reflect this.

If the contract is currently "workflows cannot import
workflows" without a derivation-chain carve-out,
surface as ALIGNMENT-FINDING-D and halt. The fix is
an additive contract amendment in `pyproject.toml`
to allow `workflows.balances.v1.*` to import from
`workflows.promos.v1.*` (or to remove the contract
entirely, depending on the intent of the S124
amendment). Operator-Claude triages.

**ALIGNMENT-CHECK-E — `_ensure_adelaide_local`
validator location.** Confirm the helper exists at
either `domain/cash_flow/__init__.py`,
`domain/promos/__init__.py`, or a shared location.
W12 derivation output models import this helper for
their `computed_at` validator.

If the helper exists in two locations (one per
domain), pick whichever is canonical — confirm at
this check whether both are identical. If they
differ, surface as ALIGNMENT-FINDING-E for operator-
Claude resolution.

**ALIGNMENT-CHECK-F — `is_external_payment`
classification.** Confirm the cash flow event types
that qualify as "external payment" (deposits,
withdrawals, external transfers in/out) are
identifiable from the `CashFlowEventType` enum or
from a classification helper.

Most likely shape: a tuple constant in
`domain.cash_flow` like
`EXTERNAL_PAYMENT_EVENT_TYPES = (CashFlowEventType
.DEPOSIT, CashFlowEventType.WITHDRAWAL, ...)`. If
no such constant exists, identify the event types
directly via inspection and surface as ALIGNMENT-
FINDING-F so operator-Claude can decide whether a
constant should be added (one-line edit in
`domain/cash_flow`, but DR-030-respectful) or
W12 lists them inline.

**ALIGNMENT-CHECK-G — `WarningSeverity` and
`FreeBetCreditSource` enum locations.** Confirm both
enums are in `domain/promos/__init__.py` and are
importable. The W12 derivation output models use
them.

`WarningSeverity` is the three-tier scheme per
DR-015 (red, amber, yellow).
`FreeBetCreditSource` is a binary enum on the
shipped substrate (`TRIGGERED` / `FREEBIE`); the
richer operator-facing label (`"insurance
trigger"`, `"bonus winnings trigger"`, `"goodwill"`,
etc.) is derived at read time per the §5.6
algorithm by walking from
`triggering_promo_instance_id` to the source
promo's template kind.

**Operator-amplified judgement extension.** Per the
W13 §6.1 precedent (operator amplified at S130 close:
Code applies its own judgement beyond the seven
specified checks). Code surfaces ANY concern noticed
during alignment — spec mismatch, future-builds
risk, pattern drift, missing precedent, unclear
reference — as ALIGNMENT-FINDING-H or beyond. The
seven specified checks are the floor; broader
judgement is welcome and expected.

**Halting rule.** Any ALIGNMENT-FINDING halts
substantive edits. Code surfaces all findings in the
report (§3 in the output spec template); operator-
Claude triages in the next session. Code does NOT
unilaterally amend specs, contracts, or DRs to
resolve findings.

### §6.2 — Build order

Execute in this order. Each step has a verification
gate before moving to the next.

1. **Session-open timestamp + pre-baselines (§7.1
   below).** Adelaide-local timestamp via the
   project's standing command. Git status snapshot.
   Pre-baseline `pytest` and `lint-imports` runs.
2. **§6.1 alignment check.** All seven checks plus
   judgement extension. Halt on any finding.
3. **§5.1 slug-flip edit on
   `domain/promos/__init__.py`.** Three type
   annotations + conditional `from uuid import UUID`
   removal. Verify via `pytest tests/store/` and
   `pytest tests/workflows/promos/v1/` —
   tests should pass (the W13 tests use UUID
   fixtures that get re-typed when the slug-flip is
   applied; until the W13 fixtures are updated, tests
   may fail with `ValidationError` on the warning
   type field).
4. **W13 test fixture swap.** Update the W13 test
   files to use slug strings instead of UUIDs for
   `warning_type_id`. Run `pytest tests/` —
   confirm all 753 tests still pass. Hold here if
   any fail; do not proceed to §5.2 until the W13
   test suite is green.
5. **§5.1 fallout in
   `workflows/promos/v1/promo_store_adapter.py`.**
   Remove the now-unnecessary UUID / str conversions
   on `warning_type_id`. Verify via `pytest tests/
   workflows/promos/v1/` and the full `pytest
   tests/` again.
5a. **§5.1b `funding_source` field removal in
    `domain/cash_flow/__init__.py`.** Drop the field
    from `ProfitShareDistributionPayload`; drop the
    `ProfitShareFundingSource` enum class if
    unreferenced (otherwise pause and surface). Verify
    via `pytest tests/store/` and `pytest
    tests/workflows/cash_flow/v1/` — tests will fail
    on any W14 fixture or adapter call still passing
    `funding_source=`; that's expected and resolves at
    step 5b.
5b. **§5.1b fallout in adapter + repository + W14 test
    fixtures.** Update
    `workflows/cash_flow/v1/cash_flow_store_adapter.py`
    method signature and SQL; update
    `store/repositories/cash_flow.py` row-conversion
    helpers; sweep all W14 test files referencing
    `funding_source` (kwarg in payload construction,
    test parameterisations over the two variants).
    Schema file (`store/schema/cash_flow.py`) likely
    needs no edit (orphan column tolerated per §5.1b).
    Run `pytest tests/` — confirm tests still pass.
    Net test count change reported in ship report
    §3; ±5 acceptable, anything beyond surfaces as a
    finding.
6. **Package marker writes** for new
   directories: `workflows/balances/__init__.py`,
   `workflows/balances/v1/__init__.py`,
   `tests/workflows/balances/__init__.py`,
   `tests/workflows/balances/v1/__init__.py`,
   `tests/scripts/__init__.py`.
7. **§5.2 seed script** at
   `scripts/seed_promos.py`. Write the script;
   smoke-test against a tempfile DB; confirm 7
   templates and 5 warnings land.
8. **§5.6 FB inventory derivation** in
   `workflows/promos/v1/promo_derivations.py`. Write
   the function plus the `FreeBetInventory` and
   `AvailableFreeBet` Pydantic models. Smoke-test
   in isolation against the seeded DB before tests.
9. **§5.7 warning state derivation** in the same
   module. Function plus `AccountCareWarningState`
   and `ActiveWarning` models. Smoke-test.
10. **§5.8 promo journey derivation** in the same
    module. Function plus `PromoJourneyState`
    Pydantic model + the closed `JourneyState`
    enum. Smoke-test through one cycle end-to-end.
11. **§5.3 / §5.4 / §5.5 balance derivations** in
    `workflows/balances/v1/balance_derivation.py`.
    Three functions plus the output models.
    `compute_account_at_book_balance` calls
    `compute_free_bet_inventory` for the FB balance
    field; cross-workflow import landed here.
    Smoke-test each derivation through a basic
    scenario.
12. **Tests:** write the three test files in the
    order §5.10 names. Run after each file lands;
    confirm tests pass before moving to the next.
13. **§5.2 seed-script tests** at
    `tests/scripts/test_seed_promos.py`. Write and
    run.
14. **Optional additive `store/__init__.py`
    re-exports** of the six output models (if
    §6.1 confirms the precedent). Verify via a
    `python3 -c "from store import ..."` import
    smoke-test.
15. **Full regression** — `pytest tests/`,
    `lint-imports`, `mypy` on the new code, `ruff`
    on the new files. All gates pass.
16. **§7 verification gates** — capture post-
    baselines per §7.2. Run §7.4 file-existence
    checks. Run §7.5 spot-check smoke script.
17. **Session-close timestamp.** Adelaide-local.
    Final `git status` confirms only the named
    anchors in the dirty / untracked entries.
18. **Write report** per §8 output spec.

Deviations from this order are expected to be small
(e.g. test file order may shuffle if a later test
exposes a bug in an earlier derivation that needs
re-work). Significant deviations surface in the
report's §3 sequencing-deviations section.

---

## §7 — Empirical verification

### §7.1 — Pre-baselines (capture at session open)

Run and capture in the report's §3 ("What Code did")
opening section.

```bash
# Adelaide-local session anchor.
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %Z"

# Git working-tree snapshot.
git status --short | wc -l
git status

# Test baseline.
pytest tests/ --tb=no -q 2>&1 | tail -5

# Lint-imports baseline.
lint-imports 2>&1 | tail -10

# mypy baseline on the existing touched modules.
mypy domain/promos workflows/promos store/repositories/promos.py 2>&1 | tail -5

# File-existence checks for not-yet-created anchors.
ls -la workflows/balances/ 2>&1 || echo "(does not exist — expected)"
ls -la workflows/promos/v1/promo_derivations.py 2>&1 || echo "(does not exist — expected)"
ls -la scripts/seed_promos.py 2>&1 || echo "(does not exist — expected)"
ls -la tests/workflows/balances/ 2>&1 || echo "(does not exist — expected)"

# Capture lint-imports contract shape for ALIGNMENT-CHECK-D.
grep -A 30 "lint-imports" pyproject.toml 2>&1 || \
  grep -A 30 "lint-imports" .importlinter 2>&1 || \
  cat importlinter.toml 2>&1
```

Expected pre-baselines per the post-W13 state:
- **pytest:** 753 tests passing.
- **lint-imports:** 5 contracts kept / 0 broken.
- **mypy:** clean on the touched promo modules.

Any divergence at pre-baseline halts substantive
edits — investigate before proceeding.

### §7.2 — Post-baselines (capture at session close)

Same commands run again at close. Capture and report
in the report's §6 (Gate results).

Expected post-baselines:
- **pytest:** 803-831 tests passing (753 pre-baseline +
  50-78 new W12 tests).
- **lint-imports:** 5 contracts kept / 0 broken (or
  6 contracts kept / 0 broken if the cross-workflow
  contract surfaced as an additive contract amendment
  at §6.1 / ALIGNMENT-FINDING-D).
- **mypy:** clean across all touched and new modules
  (`domain/promos`, `workflows/promos/v1/`,
  `workflows/balances/v1/`, `scripts/seed_promos.py`).
- **ruff:** clean (auto-fix import sort if it surfaces,
  per the W13 precedent at S130).

Also capture:

```bash
# File-size sanity check.
wc -l workflows/balances/v1/balance_derivation.py
wc -l workflows/promos/v1/promo_derivations.py
wc -l scripts/seed_promos.py
wc -l tests/workflows/balances/v1/test_balance_derivation.py
wc -l tests/workflows/promos/v1/test_promo_derivations.py
wc -l tests/scripts/test_seed_promos.py

# Git working-tree final state.
git status

# Session-close anchor.
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %Z"
```

**File-size rough guides** (not hard limits per the
S120 length-bends-to-required-detail rule):
- `balance_derivation.py`: 350-550 lines (three
  derivations + three output models + helpers).
- `promo_derivations.py`: 350-550 lines (three
  derivations + several output models + helpers).
- `seed_promos.py`: 80-150 lines.
- Test files combined: ~1800-2800 lines (each test
  file roughly 600-900 lines per the W13 / W14.1
  precedent shape).

---

### §7.3 — Formula-test scenarios (operator-validated)

These scenarios are the load-bearing test shape for W12.
Each one encodes a real-world operational narrative with
expected derivation outputs at each step. The operator
validated these scenarios at brief lock (Session 133);
Code implements them as parametrised tests that assert
the derivation outputs match the expected numbers.

**Test pattern.** Each scenario is a Python function or
parametrised case in the relevant test file. The scenario:
1. Seeds W11 account / book / account_at_book.
2. Writes the named events in order (cash flow, bet
   record, promo events).
3. Calls the relevant derivation function at each named
   inspection point.
4. Asserts the derivation output matches the expected
   numbers.

The operator-validated narratives plus their expected
derivation outputs follow.

---

**Scenario CASH-1 — Fresh deposit, no bets.**

Setup: account-at-book at Sportsbet, fresh.

Events:
- Cash flow: deposit $200.

Inspection: `compute_account_at_book_balance(conn,
account_at_book_id)`.

Expected:
```
cash_balance              = $200.00
free_bet_balance          = $0.00
pending_bet_stake_total   = $0.00
bet_count_pending         = 0
free_bet_count            = 0
currency                  = 'AUD'
```

---

**Scenario CASH-2 — Bet placed and settles as win.**

Setup: deposit $200 at Sportsbet.

Events:
- Cash flow: deposit $200.
- Bet record: $50 cash bet at $3.00 on Runner X
  (status: placed).
- Bet record updated: status → won, settlement_state
  → settled, matched_price → 3.00 (after the runner
  wins). The cash return derives on read from the bet
  row per architecture.md §A.6:
  `matched_stake × matched_price = $50 × 3.00 = $150`.
  No bet-settlement cash flow event is written.

Inspection points:
- After bet placement, before settlement: cash $200 -
  $50 pending = $150 cash effective, $50 pending stake.
- After settlement: cash $200 - $50 + $150 = $300
  (the $150 return derives on read, not as a logged
  cash flow event).

Expected at final inspection:
```
cash_balance              = $300.00
pending_bet_stake_total   = $0.00
bet_count_pending         = 0
```

---

**Scenario CASH-3 — Bet placed and settles as loss.**

Setup: deposit $200 at Sportsbet.

Events:
- Cash flow: deposit $200.
- Bet record: $50 cash bet (status: placed).
- Bet record updated: status → lost (no return).

Expected at final inspection:
```
cash_balance              = $150.00
pending_bet_stake_total   = $0.00
```

---

**Scenario CASH-4 — Full insurance + hedge cycle.**

This is the load-bearing complex scenario — the full
insurance cycle the operator described at brief lock.
Tests that the balance derivation tracks each event
across both books correctly through a complete
operational cycle.

Setup: Sportsbet account-at-book with $300 cash;
Betfair account-at-book with $500 cash. Seven promo
templates and five warning catalogue entries seeded
(via §5.2). The relevant template is **T3 — Free bet
if 2nd or 3rd** (`INSURANCE`, FB payout, default cap
$50).

Events in order with inspection points:

**Step 1 — Place original insurance bet at Sportsbet.**
- Promo observed event at Sportsbet for T3 (Runner A
  race, default terms with cap $50 and places [2,3]).
- Bet record: $50 cash bet at $5.00 on Runner A, linked
  to the observed promo via `promo_id` (status:
  placed).

Inspection at Sportsbet:
```
cash_balance              = $250.00
pending_bet_stake_total   = $50.00
bet_count_pending         = 1
free_bet_balance          = $0.00
```
Betfair unchanged: cash $500, no pending.

**Step 2 — Runner A finishes 2nd. Original bet
loses; FB insurance triggers.**

- Bet record updated: status → lost (original $50 stake
  gone, no cash return since the cash side of the
  insurance promo is the FB payout, not a cash refund).
- Cash flow event: no cash credit for the original bet.
- Promo event: `free_bet_credited` at Sportsbet, $50
  face value, `credit_source = TRIGGERED`,
  `triggering_bet_id` set to the original bet,
  `triggering_promo_instance_id` set to the T3 promo
  observed at step 1. Derived `credit_source_label
  = "insurance trigger"` per §5.6 algorithm.
- Promo event: `promo_journey_annotation` (optional
  — taken-leg-settled).

Inspection at Sportsbet:
```
cash_balance              = $250.00
free_bet_balance          = $50.00
free_bet_count            = 1
pending_bet_stake_total   = $0.00
bet_count_pending         = 0
```

**Step 3 — Deploy FB at Sportsbet on Runner B at
$8.50, hedge at Betfair.**

- Promo event: `free_bet_deployed` at Sportsbet,
  drawing $50 down from the credit event. Linked to a
  new FB-bet record.
- Bet record at Sportsbet: $50 FB stake at $8.50 on
  Runner B (status: placed; flagged as FB-funded so
  the balance derivation doesn't double-count it as
  pending cash).
- Bet record at Betfair: lay Runner B at $8.60 with
  6% commission, lay stake $L (the operator-determined
  hedge amount; for this scenario $L = $44, liability
  $7.60 × $44 = $334.40, status: placed).
- No bet-placement cash flow event is written for the
  lay. The $334.40 liability is captured on the bet
  row; Betfair's cash position derives on read via the
  §5.3 algorithm's stake-out term per architecture.md
  §A.6. (Code: verify how the W6/W6.5 bet record
  represents lay-side liability — most likely
  `matched_stake` interpreted as the liability for lay
  bets, or a dedicated `liability` field. Surface at
  §6.1 alignment-check if the substrate shape is
  ambiguous.)

Inspection at Sportsbet:
```
cash_balance              = $250.00
free_bet_balance          = $0.00       # FB deployed
free_bet_count            = 0
pending_bet_stake_total   = $0.00       # FB-bet stake
                                        # not counted
                                        # as pending
                                        # CASH stake
bet_count_pending         = 1           # the FB-bet
                                        # itself
```
Inspection at Betfair:
```
cash_balance              = $165.60     # $500 - $334.40
pending_bet_stake_total   = $334.40     # lay liability
bet_count_pending         = 1
```

**Step 4 — Runner B loses (Betfair hedge wins).**

- Bet record at Sportsbet (FB-bet): status → lost.
  No cash return (FB-funded bets don't refund stake or
  pay if they lose; the FB was already drawn down).
- Bet record at Betfair: status → won, settlement_state
  → settled (lay won because Runner B lost).
- No bet-settlement cash flow event is written.
  Betfair's cash position derives on read from the bet
  row per §5.3 algorithm + architecture.md §A.6. The
  operational math: lay liability released $334.40 +
  net winnings after commission ($44 × 0.94 = $41.36
  after 6% Betfair commission) = $375.76 total return.
  (Code: verify §A.6 derivation handles lay-side
  returns and commission; surface at §6.1 alignment-
  check if the architecture doc's §A.6 doesn't
  explicitly cover lay settlement.)

Inspection at Sportsbet:
```
cash_balance              = $250.00
free_bet_balance          = $0.00
pending_bet_stake_total   = $0.00
bet_count_pending         = 0
```
Inspection at Betfair:
```
cash_balance              = $541.36     # $165.60 +
                                        # $375.76
pending_bet_stake_total   = $0.00
bet_count_pending         = 0
```

**Cycle summary.** Starting total: $800 ($300 + $500).
Ending total: $791.36 ($250 + $541.36). Net cycle:
-$8.64.

The cycle outcome (-$8.64) is the small residual loss
typical of an insurance + FB-hedge cycle when the
back side loses — the original insurance bet's cash
stake was lost, partially offset by the FB-hedge
return. The W12 derivation is correctly tracking each
event regardless of the cycle's economic outcome.

**Note on lay stake.** $L = $44 is the scenario
parameter chosen for the test. The scenario is about
verifying the balance derivation tracks events
correctly, not about validating the hedge math itself.
Other lay stakes (e.g. $43.91 for equal-outcome lock-
in, or higher stakes for positive EV on the hedge leg)
produce different cycle outcomes but exercise the same
derivation event flow.

---

**Scenario CASH-5 — Goodwill FB stack with expiry
ordering.**

Setup: account-at-book with $100 cash. Two goodwill FBs
credited at different times with different expiries.

Events:
- Cash flow: deposit $100.
- Promo event: `free_bet_credited` $25 with
  `credit_source = FREEBIE`,
  `triggering_promo_instance_id = null`, expires in
  7 days. Derived `credit_source_label = "goodwill"`
  per §5.6 algorithm.
- Promo event: `free_bet_credited` $50 with
  `credit_source = FREEBIE`,
  `triggering_promo_instance_id = null`, expires in
  30 days. Derived `credit_source_label = "goodwill"`.

Inspection: `compute_free_bet_inventory(conn,
account_at_book_id)`.

Expected:
```
free_bets               = [
    {face_value: $25.00, expires_at: T+7d,  ...},
    {face_value: $50.00, expires_at: T+30d, ...},
]
total_face_value        = $75.00
fb_count                = 2
```

Order: earliest-expiry first.

Balance inspection same account:
```
cash_balance              = $100.00
free_bet_balance          = $75.00
free_bet_count            = 2
```

---

**Scenario WARN-1 — Two warnings active, severity-
ordered.**

Setup: account-at-book at Sportsbet, warning catalogue
seeded.

Events:
- Promo event: `accountcare_warning_raised` for
  `rapid_promo_turnover` (catalogue severity: amber).
- Promo event: `accountcare_warning_raised` for
  `big_win_pattern` (catalogue severity: red).

Inspection:
`compute_accountcare_warning_state(conn,
account_at_book_id)`.

Expected:
```
active_warnings  = [
    {warning_type_id: 'big_win_pattern',
     label: 'Big win pattern',
     severity: WarningSeverity.RED,
     raised_at: ...},
    {warning_type_id: 'rapid_promo_turnover',
     label: 'Rapid promo turnover',
     severity: WarningSeverity.AMBER,
     raised_at: ...},
]
red_count        = 1
amber_count      = 1
yellow_count     = 0
```

Red first (most-urgent), then amber.

---

**Scenario WARN-2 — Warning raised then cleared.**

Setup: account-at-book at Sportsbet.

Events:
- Promo event: `accountcare_warning_raised` for
  `large_deposit_burst` (catalogue severity: amber).
- Promo event: `accountcare_warning_cleared` for
  `large_deposit_burst`.

Inspection:
`compute_accountcare_warning_state(conn,
account_at_book_id)`.

Expected:
```
active_warnings  = []
red_count        = 0
amber_count      = 0
yellow_count     = 0
```

Cleared warning is not in active state.

---

**Scenario JOURNEY-1 — Observed but never taken.**

Setup: account-at-book at Sportsbet, T1 template
(Cash refund if 2nd) seeded.

Events:
- Promo event: `promo_observed` for T1 at Sportsbet
  (Runner Y race).
- No bet record placed against this observed promo.

Inspection: `compute_promo_journey_state(conn,
template_id=T1, book_id=Sportsbet,
account_at_book_id)`.

Expected:
```
state               = JourneyState.OBSERVED_NOT_TAKEN
observed_at         = T0
taken_at            = None
leg_settled_at      = None
cycle_resolved_at   = None
```

---

**Scenario JOURNEY-2 — Complete cash-refund cycle.**

Setup: account-at-book at Sportsbet with $100 cash, T1
template seeded.

Events:
- Promo event: `promo_observed` for T1 (Runner Y race).
- Bet record: $50 cash bet on Runner Y at $5.00,
  linked to T1 via `promo_id` (status: placed).
- Bet record updated: status → settled-2nd (Runner Y
  finished 2nd).
- Promo event: `promo_cash_credited` — cash refund of
  $25 (default cap) linked to the bet via
  `triggering_bet_id`.
- Cash flow event: cash refund credited $25.

Inspection: `compute_promo_journey_state(conn,
template_id=T1, ...)`.

Expected:
```
state               = JourneyState.CYCLE_COMPLETE
observed_at         = T0
taken_at            = T1
leg_settled_at      = T2
cycle_resolved_at   = T3
```

Balance after cycle:
```
cash_balance        = $100 - $50 + $25 = $75.00
```

---

**Scenario JOURNEY-3 — Complete FB-refund cycle.**

Setup: account-at-book at Sportsbet, T2 template
seeded.

Events:
- `promo_observed` for T2 (Runner Z race).
- Bet record: $50 cash bet on Runner Z at $5.00,
  linked to T2 (placed).
- Bet settled: 2nd place.
- `free_bet_credited` $50 (T2 trigger), linked to bet
  via `triggering_bet_id`.
- `free_bet_deployed` — FB used on a follow-on bet
  Runner Q at $4.00.
- Bet record (FB-bet): placed.
- FB-bet settled: lost.

Inspection:
- At observation: OBSERVED_NOT_TAKEN.
- After bet placement: TAKEN_LEG_ACTIVE.
- After 2nd-place settlement: LEG_SETTLED_AWAITING_
  DOWNSTREAM (FB credited, not yet fully resolved).
- After FB deploy: still LEG_SETTLED_AWAITING_
  DOWNSTREAM (FB-bet pending).
- After FB-bet settlement: CYCLE_COMPLETE.

Expected final state:
```
state               = JourneyState.CYCLE_COMPLETE
cycle_resolved_at   = (FB-bet settlement timestamp)
```

---

**Scenario JOURNEY-4 — Aborted cycle.**

Setup: any account-at-book with any template,
mid-cycle.

Events:
- `promo_observed`, bet placement (TAKEN_LEG_ACTIVE
  state).
- `promo_journey_annotation` with `aborted` tag and
  optional `abort_reason` string.

Inspection: `compute_promo_journey_state(...)`.

Expected:
```
state               = JourneyState.CYCLE_ABORTED
abort_reason        = (the operator-supplied reason)
cycle_resolved_at   = (the annotation timestamp)
```

Aborted overrides any other event flow — even if
downstream events (FB credit, FB deploy, etc.)
subsequently land, the journey stays
`CYCLE_ABORTED` until a new observation event starts a
fresh cycle for the same triple.

---

**Scenario NETFLOW-1 — Mixed-window net flow.**

Setup: two accounts at one book, plus one account at a
second book. Window: 30 days.

Events in window:
- Account A at Sportsbet: deposit $200, deposit $100,
  withdrawal $50.
- Account B at Sportsbet: deposit $300, no
  withdrawals.
- Account A at Ladbrokes: deposit $150, withdrawal
  $100.

Inspection:
`compute_operation_net_flow(conn, window_start,
window_end)`.

Expected:
```
total_inflow        = $750.00  ($200+$100+$300+$150)
total_outflow       = $150.00  ($50+$100)
net                 = $600.00
by_book = [
    {book_id: Sportsbet, inflow: $600,
     outflow: $50, net: $550},
    {book_id: Ladbrokes, inflow: $150,
     outflow: $100, net: $50},
]
by_account = [
    {account_id: A, inflow: $450,
     outflow: $150, net: $300},
    {account_id: B, inflow: $300,
     outflow: $0,   net: $300},
]
```

---

**Scenario COVERAGE — Cross-derivation consistency.**

Setup: any non-trivial multi-event scenario above
(CASH-4 is the canonical case).

Inspection: at the final state, run BOTH:
- `compute_account_at_book_balance` for Sportsbet's
  account-at-book.
- `compute_book_cash_holding(conn, book_id=Sportsbet)`.

Assert: the Location 2 holding's `breakdown` list
contains the same `AccountAtBookBalance` model that
the direct call returned (or at least the same field
values; Decimal equality on cash_balance, etc.).

The cross-derivation consistency check ensures Location
1 and Location 2 produce coherent numbers.

---

**Operator-validation lock anchor.** Scenarios CASH-1
through NETFLOW-1 confirmed at Session 133 brief lock.
COVERAGE scenario is the consistency check Claude
added at brief lock. The operator's load-bearing
requirement: each scenario's expected numbers match
what the operator would see on a daily-use dashboard
if the events fired as described. Any divergence
between derivation output and these numbers is a W12
bug, not an operator-misunderstanding.

---

### §7.4 — File-existence and content checks

At session close, verify the following files exist
with expected content shape via `Desktop Commander:
read_file` or `Desktop Commander:list_directory`.

```bash
# New files exist.
test -f workflows/balances/__init__.py
test -f workflows/balances/v1/__init__.py
test -f workflows/balances/v1/balance_derivation.py
test -f workflows/promos/v1/promo_derivations.py
test -f scripts/seed_promos.py
test -f tests/workflows/balances/__init__.py
test -f tests/workflows/balances/v1/__init__.py
test -f tests/workflows/balances/v1/test_balance_derivation.py
test -f tests/workflows/promos/v1/test_promo_derivations.py
test -f tests/scripts/__init__.py
test -f tests/scripts/test_seed_promos.py

# Edited file: slug-flip applied.
grep -nE "warning_type_id:\s*str" domain/promos/__init__.py | wc -l
# Expected: at least 3 matches (3 type annotations
# flipped from UUID to str).

grep -cE "warning_type_id:\s*UUID" domain/promos/__init__.py
# Expected: 0 (slug-flip complete).

# Edited file: store/__init__.py if W14 precedent for
# output-model re-export adopted.
grep -nE "AccountAtBookBalance|FreeBetInventory" store/__init__.py
# Expected: matches if precedent adopted; otherwise no
# matches and the §6.1 alignment confirmed no
# re-export pattern.
```

Each file landed at expected Mac path (not in a
Claude-container sandbox per the Cat 3 `create_file`
ban). Spot-check by reading a few lines from each.

**Cross-derivation function signatures.** Verify each
derivation function's signature exists and is callable:

```python
# Smoke import test.
python3 -c "
from workflows.balances.v1.balance_derivation import (
    compute_account_at_book_balance,
    compute_book_cash_holding,
    compute_operation_net_flow,
)
from workflows.promos.v1.promo_derivations import (
    compute_free_bet_inventory,
    compute_accountcare_warning_state,
    compute_promo_journey_state,
)
print('all derivation functions importable')
"
```

If any import fails, that's a hard stop.

### §7.5 — Spot-check end-to-end smoke script

A small Python script that exercises all six derivations
plus the seed script in one end-to-end run. Write to
`/tmp/w12_smoke.py` (NOT a build artefact — it's a
verification tool).

Script shape:

```python
"""W12 smoke: seed + six derivations end-to-end."""
import sqlite3, tempfile, sys
from decimal import Decimal
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ADL = ZoneInfo("Australia/Adelaide")
now_adl = lambda: datetime.now(tz=ADL)

# 1. Create a tempfile-backed SQLite, apply all
#    migrations.
# 2. Seed W11 (one account, one book, one
#    account_at_book).
# 3. Run the seed script (or import + call seed
#    main) to populate the catalogue.
# 4. Write a small set of events:
#    - Cash flow deposit.
#    - Bet record placed + settled (one cycle).
#    - Promo observed + free_bet_credited +
#      free_bet_deployed.
#    - AccountCare warning_raised.
#    - Promo journey annotation.
# 5. Call each of the six derivations.
# 6. Assert each returns a sensible-shaped Pydantic
#    output (right model class, no exceptions).
# 7. Print summary: "W12 smoke OK — 6/6 derivations
#    callable + seed populated 7 templates and 5
#    warnings."

# Implementation: ~80-120 lines following the W13 /
# W14.1 smoke script pattern. Code uses its judgement
# for the exact event sequence; the load-bearing
# assertion is that each derivation returns its
# Pydantic output without raising.
```

The smoke script is NOT part of the test suite —
it's a final-verification artefact that confirms the
shipped surface is callable end-to-end. The
parametrised tests in §5.10 carry the real coverage;
the smoke script is the "is this thing alive?"
gate.

Run output expected:
```
W12 smoke: seed populated 7 templates, 5 warnings.
Balance derivation: AccountAtBookBalance OK.
Cash holding derivation: BookCashHolding OK.
Net-flow derivation: OperationNetFlow OK.
FB inventory derivation: FreeBetInventory OK.
Warning state derivation: AccountCareWarningState OK.
Promo journey derivation: PromoJourneyState OK.
W12 smoke: 6/6 derivations callable end-to-end.
```

---

## §8 — Output spec

Code writes a single report file at:
**`dr029/w12_balances/w12_balances_report.md`**

Structure (mirroring the W13 / W14.1 report shape):

- **§1 — Pre-amble.** One paragraph: did W12 ship
  clean, what's the test count, what gates passed.
- **§2 — Pre-build alignment findings.** All seven
  ALIGNMENT-CHECKs from §6.1 with results. Each gets a
  pass/find/halt. Operator-amplified judgement findings
  (H, I, ...) listed if any.
- **§3 — What Code did.** Numbered steps matching §6.2
  build order with brief commentary on each. Sequencing
  deviations called out explicitly.
- **§4 — What landed where.** Tables of new files
  (with line counts), edited files (with line delta),
  and moved files if any.
- **§5 — Test results.** pytest run output (final
  count + baseline delta). Per-file run summary if
  helpful.
- **§6 — Gate results.** `lint-imports` count
  (kept/broken). `mypy` summary. `ruff` summary.
- **§7 — Spot-check result.** §7.5 smoke script
  output verbatim.
- **§8 — Findings.** Three classification buckets per
  the W13 / W14.1 pattern:
  - **(a) brief-spec deviation:** anywhere Code's
    implementation differs from the brief.
  - **(b) spec-implied substrate concern:** anything
    Code discovered about W4/W6/W11/W13/W14 substrate
    that the brief didn't anticipate.
  - **(c) pre-existing codebase shape:** anything
    Code noticed that's a standing observation rather
    than a W12 issue.
- **§9 — What was deliberately not done.** Mirroring
  the brief's §1.2; confirm each excluded item stayed
  excluded.
- **§10 — Open questions for triage.** Anything Code
  thinks operator-Claude should decide at the next
  session.
- **§11 — What Code thinks should land next.** One or
  two plausible forward paths post-W12.

**Expected report length.** 500-800 lines. The W13
report was 578 lines; W12 has six derivations vs W13's
nine event types, but each derivation has more
algorithm content than each event type. Same order of
magnitude.

**Report does NOT contain:**

- The W12 brief itself paraphrased back. Cross-reference
  by path; don't restate.
- Full code listings. Reference by file path + line
  range only.
- The full test list. Summarise per-file count; the
  test files speak for themselves.
- Operator-Claude triage. That's the next session's
  work; Code surfaces findings, doesn't resolve them.

---

## §9 — Hard limits

### §9.1 — Operating principle

W12 ships read-side derivations on top of stable
substrate. Hard limits exist so that Code stays on
brief and surfaces surprises as findings rather than
chasing them into adjacent workstreams.

The operating principle: every choice Code makes
during this session, when faced with a "should I also
do X" question, defaults to NO unless X is explicitly
in the brief. Surprises become findings (§3 of the
report). Findings get triaged by operator-Claude in
the next session.

### §9.2 — No schema or substrate changes

Hard limits on schema and the W4/W6/W11/W13/W14
substrate:

- **No new columns, indexes, CHECK constraints, or
  tables.** W12 reads from existing tables only. If a
  derivation needs data that the schema doesn't carry,
  that's a HALT — surface as a finding (probably (b)
  spec-implied substrate concern), do not amend the
  schema.
- **No edits to `store/schema/*.py`.** Read-only.
  (Note: §5.1b leaves an orphan `funding_source`
  column in `cash_flow_events` — schema file may
  remain unchanged with the column declaration in
  place; the column is now ignored by all read and
  write paths. Alembic column-drop migration is out
  of scope per §9.4.)
- **No edits to `store/repositories/*.py` beyond
  §5.1b cleanup of `cash_flow.py` row-conversion
  helpers.** Read-only otherwise. The §5.1b edit
  removes column references to the now-vestigial
  `funding_source` field; no logic changes, no new
  imports.
- **No edits to `domain/cash_flow/__init__.py`
  beyond §5.1b `funding_source` removal.** The
  field-and-possibly-enum drop is the ONLY change to
  this file. No new payload subclasses, no new
  validators, no other enum changes.
- **No edits to `domain/promos/__init__.py` beyond
  the §5.1 slug-flip.** The slug-flip is the ONLY
  change to this file. No new payload subclasses, no
  new validators, no new enums.
- **No edits to existing adapters beyond §5.1 and
  §5.1b fallout.** The cash-flow adapter is read-
  only except for the §5.1b
  `funding_source`-removal cleanup (method
  signature + SQL parameter list). The promo adapter
  is read-only beyond the §5.1 fallout cleanup
  (removing the now-unnecessary UUID conversions).
- **No edits to W11 (`store/schema/accounts.py`,
  `store/repositories/accounts.py`,
  `domain/accounts/`, or whatever W11 actually
  shipped).** Read-only.
- **No edits to W4/W6/W6.5 bet substrate.** Read-only.

### §9.3 — No adjacent workstreams

- **No W15 (ops_events) work.** W15 is sequenced
  after W12 per Session 131 Path D.
- **No W8 (burst review) cascade-trigger logic.** The
  W13-shipped cascade payload fields stay dormant
  until W8 ships. W12 may surface the cascade-source
  payload data if it's present on an FB credit event
  (informational), but does not write cascade events.
- **No W17 (operational web layer) UI.** W12 derivation
  outputs are Pydantic models; rendering them is W17.
- **No W18 (analytical UI) surfaces.** Distinct
  workstream.
- **No AccountCare detection logic.** W12 reads
  AccountCare raise/clear events; the threshold
  detection that decides when to raise a warning is
  downstream.
- **No promo-detection logic.** W12 reads
  `promo_observed` events; what writes them is
  upstream (W17 / capture-side).

### §9.4 — No Alembic, no SQLAlchemy Core migration

Pre-Alembic `apply_migrations(conn)` pattern persists.
W12 does not write new migrations; it reads from the
existing schema.

DR-031 locks Alembic as the v3 migration tool; the
adoption work is deferred sequenced after W12 + W15.

### §9.5 — No cross-domain imports beyond derivation
chain

DR-030 + S124 amendment:

- `domain.balances` (if it existed; it doesn't —
  derivations live in `workflows.balances`) does NOT
  import from any other domain.
- `workflows.balances.v1.balance_derivation` imports
  from `domain.cash_flow`, `domain.promos`,
  `workflows.cash_flow.v1`, `workflows.promos.v1`, and
  stdlib — the cross-workflow import for derivation
  chains is the only departure from W14.1's pattern,
  and only because the S124 amendment locked it.
- `workflows.promos.v1.promo_derivations` imports
  from `domain.promos`, `workflows.promos.v1.
  promo_store_adapter`, and stdlib. No `domain.cash_
  flow` or `workflows.cash_flow` imports.
- No imports of `clients.*`, `contracts.*`, or
  `ui.*`.

### §9.6 — Operational guardrails

- **Single bounded Code session.** If the work doesn't
  fit, that's a finding via §9.1 partial-ship
  discipline below, not a continuation. Partial-but-
  coherent ship beats complete-but-lost-coherence.
- **Adelaide local timestamps throughout** per DR-021.
  Pre-baselines, post-baselines, report timestamps,
  derivation output `computed_at` — all Adelaide
  local.
- **No `create_file`.** Per Cat 3. Every file write
  uses `Desktop Commander:write_file` or
  `projects-filesystem:write_file`.
- **Verify every write.** Per Cat 3. After each file
  write, confirm via `Desktop Commander:read_file` or
  `list_directory` that the file landed at the
  expected Mac path.
- **Pre-execution risk advisory (Cat 3).** For
  multi-line writes via `write_file mode='append'`,
  chunks of 60-180 lines reliably land per the S130
  empirical observation; larger chunks may surface
  "performance tip" advisories but the writes
  complete. For `edit_block` edits, the empirical
  ceiling is ~30 lines per the S124-S125 observation;
  split larger edits.
- **No state-mutating git commands.** No `git add`,
  `git commit`, `git stash`, `git restore`,
  `git checkout` (file-targeted), `git reset`. Read
  state via `git status` only.

### §9.7 — Dirty-tree handling

The v3 working tree may carry pre-existing dirty
regions at W12 session open. Discipline:

- Read working-tree state at session start via
  `git status`. Capture in pre-baseline.
- Edit only the named anchors in §5.
- After each edit, run `git diff <file>` to confirm
  only intended changes landed.
- At session close, run `git status` again. Confirm:
  - All W12 anchors are in the diff or untracked.
  - All pre-existing dirty entries are unchanged.
  - No state-mutating git commands were run.

If a dirty region overlaps a W12 edit anchor, halt
immediately and surface as a finding — the operator
needs to resolve the overlap before W12 can proceed
at that anchor.

### §9.8 — Partial-ship discipline

If Code reaches a session-budget wall mid-build:

- Halt at the next coherent boundary (e.g. one
  derivation fully shipped + tested, rather than
  mid-derivation).
- Capture state in the report's §3 with explicit
  named partial-ship boundary.
- Surface which derivations are shipped, which are
  partially-shipped, which are not started.
- Operator-Claude triages partial ship at the next
  session — re-routes scope or drafts a W12.1
  follow-up brief for the residual.

The session-budget wall is a finding, not a failure.
The earliest coherent halt point beats the latest
non-coherent push.

---

## §10 — What happens after Code's session

Code ships the W12 report at the path named in §8.
Operator-Claude opens the next session, reads the
report, runs `bethub-session-open` ritual, triages
findings.

**Expected triage path:**

1. **§2 alignment findings.** If any halted, the next
   session resolves before substantive work continues
   (most likely scenario: ALIGNMENT-FINDING-D on
   cross-workflow imports needs the contract
   amendment).
2. **§8 findings.** Each (a) / (b) / (c) gets
   classified and routed:
   - **(a) brief-spec deviation:** operator-Claude
     reviews each; either accepts the deviation as
     reasonable judgement or commissions a small fix.
   - **(b) spec-implied substrate concern:** routes
     to a follow-up workstream brief or to a DR
     amendment if the substrate needs to change.
   - **(c) pre-existing codebase shape:** logged for
     sweep at later workstreams; no immediate action.
3. **§10 open questions.** Each gets an explicit
   operator-Claude call.
4. **§11 forward routing.** Operator picks the next
   workstream. Default per Session 131 Path D:
   **W15** (`ops_events` per-domain event log,
   structurally identical to W13). Alternative paths
   surface based on what W12 reveals.

**Forward-tracked items that may surface mid-W12.**

- **Hedge classification (DR-025, Finding #8 from
  Session 123).** Currently scoped to revisit before
  W15 brief drafting. W12's balance derivation
  crosses bet records and may surface hedge-payoff
  modelling questions (especially in the CASH-4
  scenario). If the question surfaces in W12 review,
  it routes back into the DR-025 revisit ahead of
  W15.
- **`cascaded_at_settlement_state` closed-enum
  revisit** (Session 131 Q3). Forward-tracked for
  W8. May surface in W12 if the FB inventory
  derivation reads cascade-source data on credit
  events.

**W12.1 surgical-fix scope (if needed).** If the W12
report surfaces a clean small fix that needs to land
before W15 — equivalent to W14 → W14.1's
DR-030 break repair — operator-Claude drafts a W12.1
brief in the next session. Default expectation: W12
ships clean and no W12.1 is needed.

---

## §11 — Cross-references

### §11.1 — Architecture and decisions

- `architecture.md` §A.4 — promo event substrate
  (defines the nine `promo_events` event types and
  their semantic roles).
- `architecture.md` §D12 — Betfair as canonical
  source (context for the W12 hedge-cycle scenario
  CASH-4).
- `decisions.md` **DR-019 + Session 124 amendment**
  — derived state on read; the materialised-view-
  on-entity-row asymmetry that drives W12's algorithm
  shape.
- `decisions.md` **DR-022** — book / account /
  account-at-book vocabulary; the unit at which
  Location 1 balance lives.
- `decisions.md` **DR-027 + Session 124 amendment**
  — two-database architecture and per-domain event-
  table internal shape; substrate W12 reads from.
- `decisions.md` **DR-028** — cross-database
  integration boundary discipline; W12 stays
  BetHub-side throughout.
- `decisions.md` **DR-030 + Session 124 amendment**
  — v3 repo layout and module-boundary discipline;
  W12's workflow-side derivation placement follows
  this.
- `decisions.md` **DR-031** — v3 tech stack (Pydantic
  v2, Python 3.12+, etc.).
- `decisions.md` **DR-032** — canonical-reference-
  layer / two-table bet record; relevant to the
  balance derivation's bet-record reads.
- `decisions.md` **DR-015** — three-tier AccountCare
  warning severity scheme (red / amber / yellow);
  calibrates the warning state derivation's ordering.
- `decisions.md` **DR-021** — timestamp anchoring,
  Adelaide local time.

### §11.2 — Prior briefs and reports

- `dr029/w12_balances/seed_data.md` — the locked
  content spec consumed by §5.2.
- `dr029/w13_promos/w13_promos_brief.md` — the W13
  spec; sections §A.4, §5.2, §5.4.3 referenced on-
  demand.
- `dr029/w13_promos/w13_promos_report.md` — the W13
  ship report; the as-built substrate W12 reads from.
- `dr029/w14_cash_flow/w14_1_adapter_brief.md` — the
  v3 workflow-side adapter convention; W12's
  derivation modules follow the same module placement
  pattern.

### §11.3 — Standing instructions and governance

- `standing_instructions.md` — read in full per Cat 2.
  Categories 1 (operator communication), 3 (filesystem
  / tooling), 5 (operator-Claude division of labour)
  most load-bearing during execution.
- `governance.md` — multi-agent review pattern;
  relevant only if a finding routes to operator-Claude
  triage requiring governance escalation.

### §11.4 — Parking-lot items the brief excludes

- Cascade-trigger logic on W13's payload cascade
  fields (W8 territory).
- AccountCare detection / threshold logic (downstream
  AccountCare workstream).
- Promo-detection / promo-suggestion logic (W17
  operational layer / capture-side).
- Hedge-payoff modelling (DR-025 revisit ahead of
  W15).
- `cascaded_at_settlement_state` closed-enum tightening
  (W8 revisit).
- Multi-currency support (out of v3 scope per
  `project_context.md`).
- Multi-operator aggregation (out of v3 scope).
- The web UI surface that renders W12 outputs (W17).
- The analytical UI surface (W18).
- Alembic adoption (sequenced after W12 + W15).

### §11.5 — Build picture context

After W12 ships clean, the build picture updates:
- W12 transitions from `in flight` → `done` (one
  session carry per the v3_build_picture.md rule).
- W15 transitions from `blocked-on-W12` → `unfinished`
  (ready to start; brief drafting next session per
  Path D).
- Other streams unchanged.

If W12 ships with a residual W12.1 fix needed, W12
status becomes `done-with-known-debt-named` and W12.1
becomes the next session's deliverable. W15 stays
blocked.

---

**End of W12 brief.**
